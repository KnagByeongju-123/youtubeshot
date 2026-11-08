r"""사진 앞층 오려 내기 (사용자 결정 2026-11-08) — 무료 rembg(MIT, isnet-general-use 모델)로 사진 앞쪽 주인공(사람·인형·성·유물…)을 저절로 오려 내고,
배경의 빈자리는 둘레 색으로 메움(OpenCV inpaint). Blender(블렌더_사진3D.py)가 앞층을 배경 앞에 세워 카메라가 움직일 때 앞·뒤가 다른 속도로 움직이게 함.

사용: python 사진_앞층.py <저장폴더> <사진1> <사진2> ...
  사진마다 <저장폴더>/<키>_fg.png (앞층, 투명 배경) · <키>_bg.png (빈자리를 메운 배경) · <키>_mask.png 를 만들고
  'OK 사진 fg bg' / 'NOFG 사진 (이유)' 한 줄씩 출력. 앞층이 너무 작거나(2% 미만) 너무 크면(60% 넘음) 앞층 없이(NOFG) — 풍경·도표 사진
모델은 models/rembg/ 에 (처음 한 번 약 180MB 내려받음)
"""
import os
import sys
import hashlib
import numpy as np
from PIL import Image, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
os.environ.setdefault("U2NET_HOME", os.path.join(HERE, "models", "rembg"))


def key_for(path):
    st = os.stat(path)
    return hashlib.md5(f"{os.path.abspath(path)}|{st.st_size}|{int(st.st_mtime)}".encode("utf-8")).hexdigest()[:20]


def split(path, out_dir, session):
    import cv2
    from rembg import remove
    k = key_for(path)
    fg_p, bg_p, mk_p = (os.path.join(out_dir, f"{k}_{n}.png") for n in ("fg", "bg", "mask"))
    if os.path.exists(fg_p) and os.path.exists(bg_p):
        return "OK", fg_p, bg_p
    if os.path.exists(os.path.join(out_dir, f"{k}_nofg.txt")):
        return "NOFG", open(os.path.join(out_dir, f"{k}_nofg.txt"), encoding="utf-8").read(), ""
    im = Image.open(path).convert("RGB")
    small = im.copy()
    small.thumbnail((1024, 1024))
    m = np.asarray(remove(small, session=session, only_mask=True), np.float32) / 255.0
    area = float((m > 0.5).mean())
    if area < 0.02 or area > 0.60:
        why = f"앞층 {area * 100:.0f}% (2~60% 밖)"
        open(os.path.join(out_dir, f"{k}_nofg.txt"), "w", encoding="utf-8").write(why)
        return "NOFG", why, ""
    m = cv2.resize(m, im.size, interpolation=cv2.INTER_LINEAR)
    a = np.clip((m - 0.35) / 0.3, 0, 1)                                   # 가장자리 부드럽게
    rgb = np.asarray(im)
    Image.fromarray(np.dstack([rgb, (a * 255).astype(np.uint8)])).save(fg_p)
    Image.fromarray((a * 255).astype(np.uint8)).save(mk_p)
    # 배경: 앞층 자리(조금 넓게)를 둘레 색으로 메움 — 작게 줄여 메운 뒤 키워서 그 자리에만 얹음
    hole = (a > 0.05).astype(np.uint8) * 255
    hole = cv2.dilate(hole, np.ones((3, 3), np.uint8), iterations=max(2, im.size[0] // 160))
    sc = 640 / max(im.size)
    sw, sh = max(8, int(im.size[0] * sc)), max(8, int(im.size[1] * sc))
    s_rgb = cv2.resize(rgb, (sw, sh), interpolation=cv2.INTER_AREA)
    s_hole = cv2.resize(hole, (sw, sh), interpolation=cv2.INTER_NEAREST)
    filled = cv2.inpaint(s_rgb, s_hole, 9, cv2.INPAINT_TELEA)
    filled = cv2.GaussianBlur(filled, (0, 0), 2.0)
    big = cv2.resize(filled, im.size, interpolation=cv2.INTER_CUBIC).astype(np.float32)
    w = cv2.GaussianBlur(hole.astype(np.float32) / 255.0, (0, 0), max(2, im.size[0] / 300))[..., None]
    bg = rgb.astype(np.float32) * (1 - w) + big * w
    Image.fromarray(bg.clip(0, 255).astype(np.uint8)).save(bg_p)
    return "OK", fg_p, bg_p


def main():
    out_dir, paths = sys.argv[1], sys.argv[2:]
    os.makedirs(out_dir, exist_ok=True)
    from rembg import new_session
    session = new_session("isnet-general-use")
    for p in paths:
        try:
            r = split(p, out_dir, session)
            print(r[0], p, r[1], r[2], flush=True)
        except Exception as e:
            print("ERR", p, str(e)[:200], flush=True)


if __name__ == "__main__":
    main()
