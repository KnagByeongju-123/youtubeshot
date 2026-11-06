"""입체 블록 애니 — 장면 검수 규칙 + 자동 검사 (사용자 결정 2026-11-05: 장면을 확대 검수하고 고친 뒤에 영상)
python 입체애니_검수.py <장면3D 폴더 또는 장면.json ...> [--결과 <폴더>] [--이름 c18,c19] [--규칙]
  - 장면마다 처음·가운데·끝 3순간을 그려 <결과>/<장면>_<순간>.png, 인물마다 확대 조각 <장면>_<순간>_<인물>.png (640px 이상)
  - 아래 '자동 검사'로 잡을 수 있는 것은 자동으로 찾아 <결과>/_입체검수.txt 에 적음 → 걸린 장면부터 크게 열어 봄
  - 자동 검사가 '통과'여도 사람 눈 검수(RULES)는 꼭 함: 자동 검사는 숫자로 잴 수 있는 것만 봄
  - --규칙 : 검수 규칙만 화면에 보여 줌
  결과 폴더 기본: output/점검3D/<장면 폴더 이름>/

작업 순서(필수):
  1) 장면 설정(장면3D_설정.py) → 2) 이 검수(자동 + 확대 사람 눈) → 3) 고침 → 2)로 다시, 걸린 것이 없을 때까지
  → 4) 2분 구간 하나만 영상으로 만들고 멈춤(render_project + 구간 멈춤) → 5) 다 만든 영상에서 몇 장면을 꺼내 고친 곳이 들어갔는지 확인
  → 6) 나레이션을 붙여 사용자에게 보내고, 확인을 받은 뒤 다음 구간
  · 인물·블록 그리는 코드(블록3D.py)를 고치면 이미 만든 구간도 다시 그림 (구간마다 인물 모습이 달라지지 않게)
  · 장면 설정 파일 날짜가 바뀌면 영상 프로그램이 모든 구간을 새로 그림 — 그리기 코드만 바꿨으면 그 구간 파일(seg_*)을 지워서 다시 그리게 함
"""
import importlib.util
import json
import math
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
_sp = importlib.util.spec_from_file_location("bs3d", os.path.join(HERE, "블록장면3D.py"))
S3 = importlib.util.module_from_spec(_sp)
_sp.loader.exec_module(S3)
E = S3.E
W, H = E.W, E.H

# ───────────────────────── 사람 눈 검수 규칙 ─────────────────────────
RULES = """[입체 블록 장면 검수 규칙] — 장면마다 처음·가운데·끝 3순간을 크게(1920px) 열고, 인물·사물마다 확대해서 하나씩 확인
 ■ 인물
  1. 발이 땅에 붙었는지: 떠 있음·땅(계단·바위)에 묻힘·바다 위를 걸음 (창밖 멀리 걷는 사람은 그 아래 땅이 있어야 함)
  2. 얼굴: 말하는 사람이 카메라에 뒤통수만 보이지 않는지, 얼굴을 가리는 조각(귀 덮개·수염·뒷머리 덩어리)이 없는지
  3. 머리·모자: 모자 밖으로 삐져나온 머리 점, 이마의 검은 점, 수염이 머리 옆 전체를 덮지 않는지 (수염은 턱 앞쪽만)
  4. 소품이 대본대로인지: 젓는 사람 손의 국자는 냄비 안, 건네는 빵은 손에, 걸린 외투·빈 침대처럼 대본에 나온 물건이 보이는지
  5. 크기: 멀리 있는 사람이 너무 작아 안 보이거나 창틀·기둥에 가리지 않는지
  6. 캐릭터 설정과 같은지: 옷 색·대표 색·모자·고글·멜빵 (방수 외투로 갈아입어도 모자 같은 상징은 남김)
 ■ 사물·배경
  7. 떠 있는 건물: 등대·숙소가 땅 위에 떠 있지 않은지 (건물 자리는 평평한 땅)
  8. 물건 모양이 그 물건으로 읽히는지: 외투(깃·소매·단추), 배(뱃머리·선실), 렌즈(빛나는 유리 + 놋쇠 테), 계단(한 칸씩), 난간(가는 막대)
  9. 빛: 등대 빛줄기가 방 안 사람을 뚫고 지나가지 않는지 (빛줄기는 유리창 밖부터), 꺼진 난로엔 불꽃·수프·김이 없는지
 10. 대본의 상태와 맞는지: 멈춘 시계, 꺼진 난로, 불 꺼진 등대, 비·폭풍·해 질 녘
 ■ 화면
 11. 잘림: 조명탄·파도 꼭대기·인물 머리가 화면 밖으로 나가지 않는지
 12. 빈 곳: 방 밖·땅 끝·바다 끝 같은 빈 공간이 보이지 않는지 (카메라는 방 안에, 땅·바다는 화면보다 넓게)
 13. 화면이 한 색으로 덮이지 않는지 (카메라 바로 앞 물체), 문짝·기둥이 화면을 크게 가리지 않는지
 14. 줄무늬·울타리처럼 보이는 것: 물결 언덕은 한 색으로 이어지게
 15. 움직임: 처음과 끝 순간도 봄 — 파도가 끝에서 사라지거나, 사람이 목표 자리를 지나치거나, 물건이 화면 밖으로 날아가지 않는지
"""


# ───────────────────────── 자동 검사 ─────────────────────────
def ground_at(scene, x, z):
    """그 자리 땅 높이 (모르면 None)"""
    st = scene.get("set")
    o = scene.get("opt", {})
    if st == "rocks":
        if -20 <= x < 30 and -2 <= z < 12:
            return S3.rock_height(int(math.floor(x)), int(math.floor(z)))
        return "sea"
    if st == "stairs":
        return S3.stair_h(int(round(x)))
    if st in ("kitchen", "hook"):
        return 0
    if st == "lantern":
        if -8 <= x < 8 and -8 <= z < 8:
            return 0
        if o.get("land") and x >= 8:
            gx = 8 + int((x - 8) // 4) * 4
            return -10 - (gx - 8) * 0.18
        return "sea"
    if st == "quarry":
        return S3.quarry_h(x, z)
    if st in ("field", "walk"):
        if o.get("road") and -1 <= z < 1:
            return -0.5
        if o.get("road") and -2 <= z < 2:
            return -0.25
        return 0
    if st == "ahu":
        return 2 if (-14 <= x < 14 and -6 <= z < -1) else 0
    if st == "landing":
        return 3 if x < 8 else 3 + (int(x) - 8) // 2
    return None


def inside_box(pt, b):
    v = b.corners()
    lo, hi = v.min(0), v.max(0)
    return bool(np.all(pt > lo + 1e-3) and np.all(pt < hi - 1e-3))


def recolor(boxes, i0, i1, col=(255, 0, 255)):
    out = []
    for k, b in enumerate(boxes):
        if i0 <= k < i1:
            nb = E.Box(b.p, b.s, col, b.rots, emit=True, skip=b.skip, edge=False, bias=b.bias)
            out.append(nb)
        else:
            out.append(b)
    return out


def magenta_mask(img):
    a = np.asarray(img).astype(int)
    return (a[..., 0] > 200) & (a[..., 1] < 70) & (a[..., 2] > 200)


def check_scene(path, outdir, times=(0.3, 4.0, 7.7), dur=8.0):
    scene, cast = S3.load(path)
    cid = os.path.splitext(os.path.basename(path))[0]
    probs = []
    for k, t in enumerate(times):
        B = S3.build(scene, cast, t, dur)
        img = S3.frame(scene, cast, t, dur)
        img.save(os.path.join(outdir, f"{cid}_{k}.png"))
        arr = np.asarray(img).astype(int)
        # 화면이 거의 한 색 (카메라 바로 앞 물체가 화면을 덮음)
        if arr.std() < 8 and not ("fade_in" in scene.get("fx", []) and t < 1.2):   # 서서히 밝아지는 첫 순간은 빼고
            probs.append(f"{cid} {t:.1f}초: 화면이 거의 한 색 (카메라가 물체 안·바로 앞)")
        # 방 밖 빈 곳 (실내 장면 배경색이 보임)
        if B["mood"] not in S3.MOOD and B["mood"] != "plain":
            bg = np.all(np.abs(arr - np.array([40, 36, 34])) < 6, axis=2).mean()
            if bg > 0.03:
                probs.append(f"{cid} {t:.1f}초: 방 밖 빈 곳이 화면의 {bg * 100:.0f}% 보임 (카메라를 방 안으로)")
        # 카메라가 상자 안
        cpos = B["cam"].pos
        for b in B["boxes"]:
            if not b.emit and b.s.max() < 30 and inside_box(cpos, b):
                probs.append(f"{cid} {t:.1f}초: 카메라가 물체 안에 있음")
                break
        for ch in B["chars"]:
            who = ch["who"].split(" (")[0]
            if ch.get("exit") and t > dur * 0.6:   # 화면 밖으로 나가는 인물(장면 설정 "exit": true)은 끝부분 검사를 뺌
                continue
            team = "team" in ch["acts"] or "pull" in ch["acts"]            # 줄을 선 팀 사람: 서로 가리고 화면 밖으로도 이어지는 게 정상 → 발 높이만 봄
            x, y, z = ch["pos"]
            g = ground_at(scene, x, z)
            if g == "sea":
                probs.append(f"{cid} {t:.1f}초: {who} 가 바다 위에 서 있음 (발밑에 땅이 없음)")
            elif g is not None and abs(y - g) > 0.35:
                probs.append(f"{cid} {t:.1f}초: {who} 발 높이 {y:.1f} ≠ 땅 {g:.1f} ({'떠 있음' if y > g else '땅에 묻힘'})")
            # 말하는데 뒤돌아 있음
            talking = any(a in ch["acts"] for a in ("talk", "shout")) and not any(a in ch["acts"] for a in ("run", "walk"))   # 뛰어나가며 외치는 뒷모습은 괜찮음
            f = math.radians(ch["face"])
            fv = np.array([math.sin(f), 0, math.cos(f)])
            to_cam = cpos - np.array([x, y, z])
            to_cam[1] = 0
            nrm = np.linalg.norm(to_cam)
            if talking and nrm > 1e-6 and float(np.dot(fv, to_cam / nrm)) < -0.35:   # 옆얼굴(0 근처)까지는 괜찮음
                probs.append(f"{cid} {t:.1f}초: {who} 가 말하는데 카메라에 등을 보임")
            if team:
                continue
            # 보이는 정도·크기·잘림 (이 인물만 분홍으로 칠해 그려 봄)
            seen = magenta_mask(E.render(recolor(B["boxes"], ch["i0"], ch["i1"]), B["cam"], bg=(0, 0, 0)))
            alone = magenta_mask(E.render(recolor(B["boxes"][ch["i0"]:ch["i1"]], 0, 10 ** 6), B["cam"], bg=(0, 0, 0)))
            na, ns = alone.sum(), seen.sum()
            if na == 0:
                probs.append(f"{cid} {t:.1f}초: {who} 가 화면에 없음 (화면 밖·카메라 뒤)")
                continue
            if ns / na < 0.35:
                probs.append(f"{cid} {t:.1f}초: {who} 의 {100 - ns / na * 100:.0f}% 가 다른 물체에 가려짐")
            ys, xs = np.nonzero(alone)
            if xs.min() <= 0 or xs.max() >= W - 1 or ys.min() <= 0:
                if (ys.max() - ys.min()) < H * 0.9:   # 얼굴 가까이 찍은 장면(화면을 꽉 채움)은 빼고
                    probs.append(f"{cid} {t:.1f}초: {who} 가 화면 끝에 걸려 잘림")
            if (ys.max() - ys.min()) < 60:
                probs.append(f"{cid} {t:.1f}초: {who} 가 너무 작음 (키 {ys.max() - ys.min()}px)")
            # 확대 조각 (사람 눈 검수용, 640px 이상)
            ys2, xs2 = np.nonzero(seen if ns > 0 else alone)
            pad = 40
            box = (max(0, xs2.min() - pad), max(0, ys2.min() - pad), min(W, xs2.max() + pad), min(H, ys2.max() + pad))
            crop = img.crop(box)
            sc = max(1.0, 640 / max(1, crop.height))
            crop.resize((int(crop.width * sc), int(crop.height * sc)), Image.NEAREST).save(os.path.join(outdir, f"{cid}_{k}_{who}.png"))
    return probs


def main():
    a = sys.argv[1:]
    if "--규칙" in a:
        print(RULES)
        return
    only = set(a[a.index("--이름") + 1].split(",")) if "--이름" in a else None
    paths = []
    for x in [x for x in a if not x.startswith("--") and (a.index(x) == 0 or a[a.index(x) - 1] not in ("--결과", "--이름"))]:
        if os.path.isdir(x):
            paths += sorted(os.path.join(x, f) for f in os.listdir(x) if f.endswith(".json"))
        elif x.endswith(".json"):
            paths.append(x)
    paths = [p for p in paths if (not only or os.path.splitext(os.path.basename(p))[0] in only)
             and json.load(open(p, encoding="utf-8")).get("engine") == "3d"]
    if not paths:
        print("검사할 입체 장면이 없음")
        return
    out = a[a.index("--결과") + 1] if "--결과" in a else os.path.join(HERE, "output", "점검3D", os.path.basename(os.path.dirname(os.path.abspath(paths[0]))))
    os.makedirs(out, exist_ok=True)
    allp = []
    for p in paths:
        pr = check_scene(p, out)
        allp += pr
        print(os.path.basename(p), "→", "통과" if not pr else f"{len(pr)}건")
    rep = os.path.join(out, "_입체검수.txt")
    with open(rep, "w", encoding="utf-8") as f:
        f.write(f"자동 검사: 장면 {len(paths)}개, 걸린 것 {len(allp)}건\n\n" + ("\n".join(allp) if allp else "(자동 검사로 걸린 것 없음)") + "\n\n" + RULES)
    print("결과:", rep, f"({len(allp)}건)")
    print("※ 자동 검사가 통과여도 그림을 크게 열어 규칙대로 사람 눈 검수를 함")


if __name__ == "__main__":
    main()
