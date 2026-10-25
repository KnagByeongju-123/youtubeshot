"""레이어 움직임 준비 — 고른 컷마다 누끼(인물·사물) + 빈자리 채운 배경 + <컷>.layers.json 을 한 번에 (애니메이션 연재 전용)

  python 레이어_준비.py <그림폴더> c01=날아감:0.24,-0.2,0.5 c33=솟아오름 c34=다가옴 ...
  python 레이어_준비.py <그림폴더> --마무리      (그림 AI 배경 채우기가 끝난 뒤 layers.json 쓰기)

1) 누끼: rembg(isnet) — 반투명이면 알파를 단단히, 가장 큰 덩어리만 → <그림폴더>/레이어/<컷>_obj.png
2) 빈자리: 누끼 둘레를 넓혀 cv2.inpaint 로 대충 채움 → klein fixes(refs 없이, '물체 없음' 설명)로 그 칸을 다시 그림
   (작업_이어하기 줄에 넣어 그림 → 서버가 바뀌어도 이어 그림) → <그림폴더>/레이어/<컷>_bg.png
3) --마무리: 배경이 다 그려진 컷마다 <그림폴더>/<컷>.layers.json 을 씀 → 영상 만들기(render_project)가 그 장면을 레이어 움직임으로 그림
- 움직임 이름은 레이어_움직임.py 와 같음 (날아감·다가옴·떨어짐·솟아오름·확대·흔들림·둥실, '이름:dx,dy,크기')
- 규칙: 한 회차에서 장면의 30~50%만, 움직임이 대본 내용과 맞는 컷만 고름. 누끼가 이상하면(배경 조각이 붙음·반쪽만) 그 컷은 빼고 다시"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PY = os.path.join(HERE, ".supertonic_venv", "bin", "python")
SDPY = os.path.join(HERE, ".sd_venv", "bin", "python")


def cut_one(src, out_obj, out_hole, out_rough):
    import cv2
    import numpy as np
    from PIL import Image, ImageFilter
    from rembg import new_session, remove
    im = Image.open(src).convert("RGB")
    a = np.asarray(remove(im, session=new_session("isnet-general-use")))[:, :, 3]
    m = (a > 100).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(m)
    if n < 2:
        return None
    k = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
    m = (lab == k).astype(np.uint8) * 255
    cover = float((m > 0).mean())
    obj = im.copy()
    obj.putalpha(Image.fromarray(m).filter(ImageFilter.GaussianBlur(1.2)))
    obj.save(out_obj)
    hole = cv2.dilate(m, np.ones((17, 17), np.uint8))
    Image.fromarray(hole).save(out_hole)
    rough = cv2.inpaint(cv2.cvtColor(np.asarray(im), cv2.COLOR_RGB2BGR), hole, 9, cv2.INPAINT_TELEA)
    cv2.imwrite(out_rough, rough)
    ys, xs = np.nonzero(hole)
    return cover, [int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1]


def main():
    a = sys.argv[1:]
    if not a:
        sys.exit(__doc__)
    folder = os.path.abspath(a[0])
    lay = os.path.join(folder, "레이어")
    os.makedirs(lay, exist_ok=True)
    plan_p = os.path.join(lay, "계획.json")
    plan = json.load(open(plan_p, encoding="utf-8")) if os.path.exists(plan_p) else {}
    if "--마무리" in a:
        n = 0
        for c, mv in plan.items():
            bg = os.path.join(lay, f"{c}_bg.png")
            if os.path.exists(bg):
                json.dump({"bg": f"레이어/{c}_bg.png", "layers": [{"png": f"레이어/{c}_obj.png", "move": mv}]},
                          open(os.path.join(folder, f"{c}.layers.json"), "w", encoding="utf-8"), ensure_ascii=False)
                n += 1
            else:
                print("배경이 아직 없음:", c)
        print(f"layers.json {n}개 씀")
        return
    fixes = []
    for arg in a[1:]:
        c, _, mv = arg.partition("=")
        src = next((os.path.join(folder, c + e) for e in (".png", ".jpg") if os.path.exists(os.path.join(folder, c + e))), None)
        if not src:
            print("그림 없음:", c)
            continue
        r = cut_one(src, os.path.join(lay, f"{c}_obj.png"), os.path.join(lay, f"{c}_hole.png"), os.path.join(lay, f"{c}_rough.png"))
        if not r:
            print("누끼 실패:", c)
            continue
        cover, box = r
        print(f"  {c}: 누끼 {cover * 100:.0f}% · 빈자리 {box} · 움직임 {mv or '확대'}")
        if cover > 0.6:
            print(f"    ⚠ {c}: 누끼가 그림의 60%를 넘음 (배경까지 잡힌 듯) — 빼는 것을 권함")
        plan[c] = mv or "확대"
        fixes.append({"id": f"{c}_bg", "image": os.path.join(lay, f"{c}_rough.png"), "out": os.path.join(lay, f"{c}_bg.png"), "box": box,
                      "prompt": "the same scene background continuing naturally, same art style and lighting, clean empty background "
                                "with absolutely no people, no characters, no robots, no ship, no objects in this area",
                      "refs": [], "seed": 11})
    json.dump(plan, open(plan_p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    if fixes:
        jp = os.path.join(lay, "배경채우기.json")
        json.dump({"fixes": fixes}, open(jp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        name = "레이어배경_" + os.path.basename(os.path.dirname(folder)) + "_" + os.path.basename(folder)
        subprocess.run([PY, os.path.join(HERE, "작업_이어하기.py"), "add", name, "--", SDPY, os.path.join(HERE, "klein_worker.py"),
                        os.path.join(HERE, "models", "FLUX2_klein_4B"), jp, os.path.join(lay, "_klein")], check=True)
        subprocess.Popen([PY, os.path.join(HERE, "작업_이어하기.py"), "run"], cwd=HERE, stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL, start_new_session=True)
        print("배경 채우기를 줄에 넣음 →", name, "/ 끝나면: python 레이어_준비.py", a[0], "--마무리")


if __name__ == "__main__":
    main()
