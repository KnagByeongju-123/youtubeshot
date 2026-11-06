"""「피라미드는 어떻게 쌓았을까」 입체 블록 장면 — 영화처럼 컷을 나눈 카메라 (사용자 결정 2026-11-06)
python 연재/피라미드/장면3D_설정.py [c01,c02]   (검수: python 입체애니_검수.py 연재/피라미드/장면3D)
cam.shots = [{컷 1, "to": 0.5}, {컷 2, "to": 1.0}] — 컷마다 dolly(밀고 들어가기)·crane(솟아오르기)·track(인물 따라가기)·orbit(돌기), fov→fov1 줌"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
H, T, P = "안내자 하람 (14)", "타티 (10)", "하푸 반장 (40대)"
WB, WG, WR, S = "일꾼 파랑", "일꾼 초록", "일꾼 빨강", "과학자"
LIVE = ["blink", "breath"]
PYR = {"pyr": [0, -60], "n": 24}
HALF = {**PYR, "built": 13, "ramp": True}


def ch(who, at, face=0, act=None, **k):
    d = {"who": who, "at": at, "face": face, "act": act or LIVE}
    d.update(k)
    return d


def dolly(pos, look, pos1, look1, fov=50, fov1=None, to=1.0, **k):
    d = {"mode": "dolly", "pos": pos, "look": look, "pos1": pos1, "look1": look1, "fov": fov, "fov1": fov1 or fov, "to": to}
    d.update(k)
    return d


def shots(*s):
    return {"shots": list(s), "hand": 0.06}


# 썰매 끄는 줄 (일꾼들이 썰매 앞에서 끔): 썰매 x=-10, 진행에 따라 +dx
SLED = {"sledges": [[-10, 0, 0, 10]], "ropes": [[[-8, 1.0, -0.8], [6, 2.2, -2.5]], [[-8, 1.0, 0.8], [6, 2.2, 2.5]]]}
TEAM = [ch(WB, [7, -2.5], 90, ["pull"], to=[17, -2.5]), ch(WG, [9.5, -2.5], 90, ["pull"], to=[19.5, -2.5]),
        ch(WR, [7, 2.5], 90, ["pull"], to=[17, 2.5]), ch(WB, [9.5, 2.5], 90, ["pull"], to=[19.5, 2.5])]

S_ = {
 "c01": {"set": "desert", "opt": {**PYR, "cap": True, "small_pyr": True}, "fx": ["fade_in"],
         "cam": shots(dolly([0, 90, 260], [0, 20, -60], [0, 30, 120], [0, 30, -60], 40, 44))},
 "c02": {"set": "desert", "opt": {**PYR, "cap": True}, "chars": [ch(WB, [4, 20], 180), ch(WG, [-3, 22], 170)],
         "cam": shots(dolly([2, 1.5, 40], [0, 6, 0], [2, 2.0, 32], [0, 70, -60], 60, 66))},   # 아래에서 꼭대기로 올려다봄 (크기)
 "c03": {"set": "desert", "opt": {**PYR}, "cam": shots(dolly([-40, 10, 20], [-20, 6, -10], [-10, 16, 8], [0, 14, -20], 46))},
 "c04": {"set": "desert", "opt": {**PYR, "built": 4, "blocks": [[-4, 10], [3, 12], [9, 9]]},
         "cam": shots(dolly([-18, 3, 30], [0, 1.5, 10], [10, 3, 28], [2, 1.5, 10], 48))},
 "c05": {"set": "plain", "opt": {"c1": [40, 30, 20], "c2": [230, 190, 120]}, "chars": [ch(H, [0, 0], 0, ["closed", "breath"])], "fx": ["glow"],
         "cam": shots(dolly([0, 4.4, 9], [0, 4.0, 0], [0, 4.4, 5.5], [0, 4.2, 0], 42))},
 "c06": {"set": "desert", "opt": {**HALF, "sledges": [[-6, 30, 0], [8, 36, 0]]}, "chars": [ch(H, [0, 70], 180, LIVE), ch(WB, [-2, 32], 90), ch(WR, [10, 38], 90)],
         "cam": shots(dolly([3, 9, 82], [0, 6, 70], [3, 9, 82], [0, 6, 70], 50, to=0.35), dolly([3, 9, 82], [0, 6, 60], [6, 14, 90], [0, 14, -20], 50, 56))},   # 하람 뒷모습 → 아래 펼쳐진 공사장
 "c07": {"set": "desert", "opt": {**HALF}, "chars": [ch(T, [-1.5, 40], 30, ["blink", "talk"]), ch(H, [1.8, 40.5], -70)],
         "cam": shots(dolly([7, 5.0, 48], [0.5, 3.6, 40], [4, 4.2, 45], [-0.5, 3.4, 40], 46, to=0.55), dolly([-3, 4.4, 46], [1.2, 4.0, 40.5], [-2.5, 4.4, 45.5], [1.2, 4.2, 40.5], 44))},   # 어깨 너머 → 반대쪽
 "c08": {"set": "desert", "opt": {**HALF, "sledges": [[0, 30, 0]]}, "chars": [ch(P, [-4, 33], 60, ["blink", "talk", "point"]), ch(T, [-6, 35], 40)],
         "cam": shots(dolly([-12, 4, 44], [-4, 4, 33], [-8, 5, 40], [0, 3, 30], 46))},
 "c09": {"set": "desert", "opt": {**HALF, "sledges": [[0, 30, 0]]}, "chars": [ch(H, [-3.6, 30], 90, ["push", "blink"])],
         "cam": shots(dolly([-1, 3, 38], [-2.5, 2.5, 30], [-1.5, 2.8, 36], [-2.5, 2.6, 30], 44))},
 "c10": {"set": "desert", "opt": {**HALF}, "chars": [ch(T, [-1.4, 40], 20, ["blink", "talk", "flap"]), ch(P, [1.8, 40], -30, ["blink", "laugh"])],
         "cam": shots(dolly([0, 5, 50], [0, 4, 40], [0, 4.5, 47], [0, 4.2, 40], 46))},
 "c11": {"set": "desert", "opt": {**HALF, **SLED}, "chars": TEAM,
         "cam": {"shots": [{"mode": "track", "who": WR, "off": [-6, 3, 14], "off1": [4, 3, 13], "aim": [-6, 2, -2], "fov": 52}], "hand": 0.08}},
 "c12": {"set": "desert", "opt": {**HALF, **SLED, "wet": True, "pour": True}, "chars": TEAM + [ch(WG, [-6.0, -2.2], 90, ["blink", "reach"], hold="#b8743a", to=[4, -2.2])],
         "cam": shots(dolly([-3, 3.2, 10], [-5, 2.2, -2], [4, 3.2, 9], [3, 2.2, -2], 52))},   # 물 붓는 손 가까이 따라감
 "c13": {"set": "desert", "opt": {**HALF}, "chars": [ch(H, [0, 40], 0, ["blink", "breath", "talk"])],
         "cam": shots(dolly([0, 4.6, 46], [0, 4.4, 40], [0, 4.6, 44.5], [0, 4.4, 40], 42))},
 "c14": {"set": "desert", "opt": {**HALF, **SLED, "wet": True, "pour": True}, "chars": TEAM + [ch(WG, [-6.0, -2.2], 90, ["reach"], hold="#b8743a", to=[4, -2.2])],
         "cam": shots(dolly([-30, 1.0, 0], [0, 1, 0], [-24, 1.4, 4], [8, 1.2, 0], 40, to=0.5), {"mode": "orbit", "target": [4, 2, 0], "a0": -25, "a1": 25, "r0": 22, "h0": 6, "h1": 10, "fov": 50, "to": 1.0})},
 "c15": {"set": "desert", "opt": {**HALF, "sledges": [[-6, 0, 0, 22]], "wet": True, "pour": True}, "chars": [ch(H, [-3.0, -2.2], 90, ["reach", "laugh"], hold="#b8743a", to=[10, -2.2])],
         "cam": {"shots": [{"mode": "track", "who": H, "off": [-2, 3, 10], "off1": [6, 3, 10], "aim": [3, 1.5, 0], "fov": 52}], "hand": 0.1}},
 "c16": {"set": "desert", "opt": {**HALF, "wet": True}, "chars": [ch(H, [0, 0], 30, ["laugh", "sit"]), ch(WB, [-4, -3], 60, ["laugh"]), ch(WR, [4, -3], -60, ["laugh"]), ch(T, [2, 3], -30, ["laugh"])],
         "cam": shots(dolly([0, 6, 14], [0, 1.5, 0], [0, 3, 8], [0, 1.6, 0], 50, bump=0.05))},
 "c17": {"set": "desert", "opt": {**HALF, "wet": True}, "chars": [ch(P, [1.8, 0.5], -70, ["blink", "talk", "reach"]), ch(H, [-0.6, 0], 60, ["laugh", "sit"])],
         "cam": shots(dolly([-8, 3, 8], [0.5, 2.5, 0], [-6, 3.5, 7], [0.5, 3, 0], 46))},
 "c18": {"set": "desert", "opt": {**HALF}, "chars": [ch(T, [1.2, 40], 90, ["walk", "talk"], to=[8, 40]), ch(H, [-1.2, 40], 90, ["walk"], to=[5.6, 40])],
         "cam": {"shots": [{"mode": "track", "who": T, "off": [-3, 3, 9], "off1": [3, 3, 9], "aim": [0, 2.5, 0], "fov": 48}], "hand": 0.1}},
 "c19": {"set": "village", "chars": [ch(T, [-1, 7], 30, ["blink", "talk"]), ch(H, [1.5, 7.5], 10, ["blink", "laugh"]), ch(WB, [4, 6], 200), ch(WG, [-4, 6], 160)],
         "cam": shots(dolly([18, 12, 30], [0, 2, 0], [6, 4.5, 16], [1, 2.5, 4], 50))},   # 위에서 마을로 내려오며
 "c20": {"set": "desert", "opt": {**HALF, "sledges": [[0, 34, 0]]}, "chars": [ch(H, [6, 60], 160, LIVE)],
         "cam": shots(dolly([9, 3.0, 72], [6, 4, 60], [10, 4, 76], [20, 26, -40], 52, 60))},   # 하람 등 뒤에서 위로 틸트
 "c21": {"set": "desert", "opt": {**HALF, "mood": "desert_dusk"}, "chars": [ch(H, [0, 40], 0, ["blink", "talk"]), ch(T, [-2.4, 41], 30, ["blink", "wave"]), ch(P, [2.6, 41], -30)], "fx": ["glow"],
         "cam": shots(dolly([0, 4.6, 51], [0, 3.8, 40.5], [0, 4.5, 48.5], [0, 4.0, 40.5], 48))},
 "c22": {"set": "desert", "opt": {**PYR, "cap": False, "small_pyr": True}, "chars": [ch(H, [0, 40], 180, LIVE)],
         "cam": shots(dolly([0, 3, 48], [0, 4, 40], [0, 18, 70], [0, 24, -60], 50, 46))},   # 하람 뒤에서 크레인으로 솟아 피라미드
 "c23": {"set": "frieze", "chars": [ch(w, [4 - k * 2.4, 0], 90, ["pull"]) for k, w in enumerate([WB, WG, WR, WB, WG, WR, WB, WG])],
         "cam": shots(dolly([-2, 3, 30], [-2, 3, 0], [12, 3, 30], [12, 3, 0], 42))},
 "c24": {"set": "lab", "chars": [ch(S, [-10.5, 2], 60, ["blink", "talk", "point"])], "cam": shots(dolly([-2, 7, 18], [-3, 3, 0], [0, 6.5, 15], [-1.5, 2.8, 0], 52))},
 "c25": {"set": "nile", "cam": {"shots": [{"mode": "orbit", "target": [0, 1, 3], "a0": -40, "a1": 10, "r0": 34, "r1": 26, "h0": 10, "h1": 6, "fov": 50}], "hand": 0.05}},
 "c26": {"set": "village", "opt": {"ruin": True}, "cam": shots(dolly([-20, 14, 24], [0, 0, -6], [10, 10, 20], [0, 0, -6], 50))},
 "c27": {"set": "desert", "opt": {**PYR, "built": 16, "spiral": True}, "cam": {"shots": [{"mode": "orbit", "target": [0, 16, -60], "a0": 10, "a1": 80, "r0": 120, "h0": 50, "h1": 40, "fov": 48}], "hand": 0.05}},
 "c28": {"set": "desert", "opt": {**PYR, "cap": True, "mood": "desert_dusk"}, "chars": [ch(w, [-8 + k * 2.2, 30 + (k % 2)], 180) for k, w in enumerate([WB, WG, P, T, WR, WB, WG])],
         "cam": shots(dolly([0, 2.5, 46], [0, 3, 30], [0, 10, 70], [0, 26, -60], 52, 46))},
 "c29": {"set": "desert", "opt": {**PYR, "cap": True, "mood": "desert_dusk"}, "chars": [ch(H, [-4, 40], 90, ["walk"], to=[12, 40], exit=True)],
         "cam": shots(dolly([-14, 3, 52], [-4, 3, 40], [4, 4, 56], [10, 8, 20], 50))},
}

if __name__ == "__main__":
    import importlib.util
    sp = importlib.util.spec_from_file_location("bs3", os.path.join(ROOT, "블록장면3D.py"))
    B3 = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(B3)
    d = os.path.join(HERE, "장면3D")
    os.makedirs(d, exist_ok=True)
    only = sys.argv[1].split(",") if len(sys.argv) > 1 else None
    for cid, sc in S_.items():
        if only and cid not in only:
            continue
        sc = {"engine": "3d", "cast": "../등장인물.json", **sc}
        p = os.path.join(d, cid + ".json")
        new = json.dumps(sc, ensure_ascii=False, indent=1)
        if not os.path.exists(p) or open(p, encoding="utf-8").read() != new:
            open(p, "w", encoding="utf-8").write(new)
        scene, cast = B3.load(p)
        B3.frame(scene, cast, 3.0, 8).save(os.path.join(d, cid + ".png"))
        print(cid, end=" ", flush=True)
    print("\n장면 저장")
