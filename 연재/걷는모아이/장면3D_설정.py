"""「모아이는 어떻게 걸었을까」 입체 블록 장면 설정 → 장면3D/cNN.json + 멈춘 그림 cNN.png (블록장면3D.py)
python 연재/걷는모아이/장면3D_설정.py [c01,c02]   (검수: python 입체애니_검수.py 연재/걷는모아이/장면3D)"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
H, T, A = "안내자 하람 (14)", "조각가 토키 할아버지 (70대)", "아리 (10)"
R, Bl, G, S = "섬 사람 빨강 팀", "섬 사람 파랑 팀", "섬 사람 초록 팀", "과학자"
LIVE = ["blink", "breath"]
SCI = {"left": [S, S, S], "right": [S, S, S], "back": [S, S]}
TEAMS = {"left": [R, R, R], "right": [Bl, Bl, Bl], "back": [G, G]}


def ch(who, at, face=0, act=None, **k):
    d = {"who": who, "at": at, "face": face, "act": act or LIVE}
    d.update(k)
    return d


WALK = {"start": -14, "end": 0, "mz": 0, "msc": 2.0}   # 모아이 높이 약 16 = 어른 세 명보다 큼
S_ = {
 "c01": {"set": "rapanui", "cam": {"pos": [0, 40, 110], "look": [0, 0, 0], "fov": 40, "move": [0, -14, -45]}, "fx": ["fade_in"]},
 "c02": {"set": "ahu", "cam": {"pos": [-4, 5, 22], "look": [0, 4, -3], "fov": 50, "move": [6, 0, -2]}},
 "c03": {"set": "rapanui", "opt": {"road": True}, "cam": {"pos": [-10, 46, 52], "look": [4, 2, 0], "fov": 46, "move": [6, -4, -8]}},
 "c04": {"set": "field", "opt": {"fallen": [[2, 2, 40]]}, "cam": {"pos": [-8, 5, 16], "look": [2, 1.5, 0], "fov": 48, "move": [4, 0, -2]}},
 "c05": {"set": "plain", "opt": {"c1": [18, 15, 42], "c2": [70, 66, 140]}, "cam": {"pos": [0, 4.4, 6.5], "look": [0, 4.0, 0], "fov": 42}, "chars": [ch(H, [0, 0], 0, ["closed", "breath"])], "fx": ["glow"]},
 "c06": {"set": "quarry", "cam": {"pos": [0, 9, 16], "look": [0, 5, -10], "fov": 52, "move": [0, -1, -3]}, "chars": [ch(H, [0, 6], 180, LIVE)]},
 "c07": {"set": "quarry", "cam": {"pos": [0, 4.5, 14], "look": [0, 3.3, 4], "fov": 46}, "chars": [ch(A, [-1.4, 5], 40, ["blink", "breath", "talk"]), ch(H, [1.6, 5.5], -60, LIVE)]},
 "c08": {"set": "quarry", "opt": {"carving": []}, "extra": {"moai": [[-4, 6, 90, 2.0, True]]}, "cam": {"pos": [6, 7, 20], "look": [-3, 2, 4], "fov": 50},
         "chars": [ch(T, [-0.6, 3.0], -100, ["blink", "breath", "wipe"], hold="#6b6b6b"), ch(A, [2.6, 6.0], -80, LIVE)]},
 "c09": {"set": "field", "cam": {"pos": [10, 7, 22], "look": [0, 6, 0], "fov": 50}, "extra": {"moai": [[-2, -3, 0, 2.0]]},
         "chars": [ch(T, [2.6, 2.0], -40, ["blink", "breath", "talk", "reach"])]},
 "c10": {"set": "field", "cam": {"pos": [9, 2.2, 18], "look": [-1, 8, 0], "fov": 60}, "extra": {"moai": [[-1, -3, 0, 2.0]]}, "chars": [ch(H, [2.5, 4.5], 200, LIVE)]},
 "c11": {"set": "field", "cam": {"pos": [0, 7.5, 21], "look": [-2, 6.5, 0], "fov": 56}, "extra": {"moai": [[-8, -8, 20, 2.0]]},
         "chars": [ch(A, [-1.2, 1.5], 20, ["blink", "talk", "wave"]), ch(T, [1.6, 1.0], -30, ["blink", "breath", "talk"])]},
 "c12": {"set": "walk", "opt": {**WALK, "walk": False, "teams": TEAMS}, "cam": {"pos": [10, 14, 40], "look": [-10, 6, 0], "fov": 52}, "chars": [ch(T, [-7, 9.0], 40, ["blink", "talk", "point"])]},
 "c13": {"set": "walk", "opt": {**WALK, "walk": False, "pulls": ()}, "cam": {"pos": [-26, 8, 20], "look": [-12, 6, 0], "fov": 50}, "chars": [ch(T, [-11.5, 6.0], -100, ["blink", "talk", "point"])]},
 "c14": {"set": "walk", "opt": {**WALK, "teams": TEAMS, "period": 3.2}, "cam": {"pos": [-4, 12, 40], "look": [-8, 6, 0], "fov": 52}},
 "c15": {"set": "walk", "opt": {**WALK, "teams": TEAMS, "period": 3.2}, "cam": {"pos": [-34, 12, 26], "look": [-6, 6, 0], "fov": 52}},
 "c16": {"set": "walk", "opt": {**WALK, "teams": TEAMS}, "cam": {"pos": [16, 8, 30], "look": [-6, 6, 0], "fov": 52},
         "chars": [ch(H, [-5, 16], 20, ["blink", "talk", "wave"]), ch(A, [-2.5, 15.5], 10, ["blink", "talk", "wave"])]},
 "c17": {"set": "walk", "opt": {**WALK, "teams": TEAMS, "sing": True}, "cam": {"pos": [20, 9, 12], "look": [-6, 6, -6], "fov": 54}},
 "c18": {"set": "walk", "opt": {**WALK, "teams": {"left": [H, R, R], "right": [Bl, Bl, Bl], "back": [G, G]}}, "cam": {"pos": [12, 6, 2], "look": [-6, 6, -10], "fov": 60}},
 "c19": {"set": "walk", "opt": {**WALK, "road": True, "teams": TEAMS, "start": -22, "end": -4}, "cam": {"pos": [-40, 12, 20], "look": [-12, 4, 0], "fov": 50, "move": [10, 0, 0]}},
 "c20": {"set": "ahu", "opt": {"mood": "dusk"}, "cam": {"pos": [2, 5, 20], "look": [0, 4, -3], "fov": 52, "move": [-2, 0, -2]},
         "chars": [ch(R, [-4, 5], 200), ch(Bl, [-1, 6], 180), ch(G, [3, 5.5], 160), ch(T, [6, 6], 200)]},
 "c21": {"set": "ahu", "opt": {"mood": "dusk"}, "cam": {"pos": [1.5, 4.6, 13], "look": [0, 3.4, 3.6], "fov": 46},
         "chars": [ch(T, [-1.0, 3.5], 60, ["blink", "talk", "pat"]), ch(H, [0.9, 3.8], -70, LIVE)]},
 "c22": {"set": "ahu", "opt": {"mood": "dusk"}, "cam": {"pos": [0, 4.4, 12], "look": [0, 3.3, 3], "fov": 46},
         "chars": [ch(H, [0, 4], 0, ["blink", "talk"]), ch(A, [-2.4, 5], 40, ["blink", "wave"]), ch(T, [2.6, 4.6], -30, LIVE)], "fx": ["glow"]},
 "c23": {"set": "ahu", "opt": {"mood": "day"}, "cam": {"pos": [0, 4.0, 16], "look": [0, 4.5, -3], "fov": 50, "move": [0, 0, -2]}, "chars": [ch(H, [0, 6], 180, LIVE)]},
 "c24": {"set": "walk", "opt": {**WALK, "walk": False, "teams": SCI, "msc": 1.0}, "cam": {"pos": [6, 8, 24], "look": [-10, 3, 0], "fov": 52}},
 "c25": {"set": "walk", "opt": {**WALK, "teams": SCI, "msc": 1.0, "period": 3.0}, "cam": {"pos": [-6, 8, 24], "look": [-8, 3, 0], "fov": 52}},
 "c26": {"set": "walk", "opt": {**WALK, "teams": {"left": [S] * 7, "right": [S] * 7, "back": [S] * 4}, "msc": 1.0}, "cam": {"pos": [0, 16, 34], "look": [-8, 1, 0], "fov": 56}},
 "c27": {"set": "field", "opt": {"road": True, "fallen": [[-6, 4, 80], [9, -5, 100]]}, "cam": {"pos": [-18, 6, 8], "look": [4, 0, 0], "fov": 48, "move": [8, 0, 0]}},
 "c28": {"set": "ahu", "opt": {"mood": "dusk"}, "cam": {"pos": [0.1, 5.6, 3.5], "look": [0.1, 5.2, -3], "fov": 40, "move": [0, 0, -0.8]}},
 "c29": {"set": "walk", "opt": {**WALK, "mood": "dusk", "teams": TEAMS}, "cam": {"pos": [-8, 6, 40], "look": [-8, 6, 0], "fov": 50}, "fx": ["past"]},
 "c30": {"set": "ahu", "opt": {"mood": "dusk"}, "cam": {"pos": [-14, 5, 14], "look": [4, 3, 2], "fov": 50},
         "chars": [ch(H, [-6, 6], 100, ["walk"], to=[12, 6], speed=1.0, exit=True)]},
 "c31": {"set": "field", "extra": {"moai": [[-3, -1, 90, 1.6, True]]}, "cam": {"pos": [5, 4, 12], "look": [-1, 2.5, 0], "fov": 48},
         "chars": [ch(H, [2.5, 2.5], -40, ["blink", "breath", "talk"])]},
 "c32": {"set": "field", "extra": {"moai": [[-8, -8, 20, 2.0]]}, "cam": {"pos": [0, 7.5, 21], "look": [-2, 6.5, 0], "fov": 56},
         "chars": [ch(A, [-1.6, 1.5], 25, ["blink", "talk", "flap"]), ch(H, [1.8, 1.2], -30, ["blink", "laugh"])]},
 "c33": {"set": "walk", "opt": {**WALK, "teams": TEAMS, "stumble": True, "period": 3.0}, "cam": {"pos": [-6, 10, 34], "look": [-7, 6, 0], "fov": 52}},
 "c34": {"set": "walk", "opt": {**WALK, "walk": False, "teams": TEAMS}, "cam": {"pos": [8, 4.5, -1], "look": [-3, 2, -8], "fov": 54},
         "chars": [ch(H, [-2.0, -6.0], 63, ["blink", "laugh", "sit"])]},
}


# ── 카메라 움직임 (사용자 결정 2026-11-05: 블록은 원래 크기, 카메라는 역동적으로) ──
# orbit = 대상 둘레를 a0→a1 도 돌기(r 거리, h 높이: 0→1 로 바뀌면 크레인), follow = 걷는 모아이를 따라 돌기, shake = 걸음마다 쿵, hand = 손 카메라
def orbit(tx, ty, tz, a0, a1, r0, r1=None, h0=6, h1=None, fov=50, mode="orbit", shake=0, hand=0.1):
    c = {"mode": mode, "target": [tx, ty, tz], "a0": a0, "a1": a1, "r0": r0, "r1": r1 if r1 is not None else r0,
         "h0": h0, "h1": h1 if h1 is not None else h0, "fov": fov, "hand": hand}
    if shake:
        c["shake"] = shake
    return c


CAM = {
 "c01": orbit(0, 2, 0, -25, 10, 115, 72, 46, 24, 40),
 "c02": orbit(0, 4, -3, -35, 30, 24, 22, 5, 7, 50),
 "c03": orbit(4, 2, 0, 5, 40, 62, 52, 46, 38, 46),
 "c06": orbit(0, 5, -6, -15, 15, 24, 22, 6, 12, 52),
 "c08": orbit(-2, 2, 4, 15, 50, 19, 17, 6, 8, 50),
 "c09": orbit(-2, 8, -3, 30, 10, 24, 22, 3, 12, 52),
 "c10": orbit(-1, 9, -3, 25, -20, 19, 17, 1.6, 3, 60),
 "c12": orbit(-10, 5, 0, 10, 40, 44, 40, 14, 18, 52),
 "c13": orbit(-12, 7, 0, -60, -30, 20, 18, 7, 8, 50),
 "c14": orbit(0, 7, 0, -60, 20, 34, 28, 5, 12, 50, "follow", 0.35),
 "c15": orbit(0, 7, 0, -140, -95, 36, 32, 8, 12, 52, "follow", 0.35),
 "c16": orbit(0, 7, 0, 25, 60, 36, 34, 7, 9, 52, "follow", 0.3),
 "c17": orbit(-6, 3, -9, 60, 100, 17, 16, 5, 6, 54, shake=0),
 "c33": orbit(0, 7, 0, -20, 10, 36, 30, 8, 9, 52, "follow", 0.6),
 "c31": orbit(-1, 2.5, 0, 30, 0, 12, 10, 4, 3.5, 48),
 "c19": orbit(0, 6, 0, -95, -60, 32, 30, 9, 11, 50, "follow", 0.3),
 "c20": orbit(0, 5, -3, -20, 20, 25, 23, 6, 7, 52),
 "c23": orbit(0, 6, -3, 0, 0, 20, 19, 3, 9, 50),
 "c24": orbit(-10, 3, 0, 20, 50, 25, 23, 8, 9, 52),
 "c25": orbit(0, 4, 0, -50, 0, 26, 24, 6, 9, 52, "follow", 0.2),
 "c26": orbit(-8, 1, 0, 0, 30, 36, 32, 12, 22, 56),
 "c29": orbit(0, 7, 0, -10, 20, 38, 34, 6, 8, 50, "follow", 0.3),
}
for k_, c_ in CAM.items():
    S_[k_]["cam"] = c_
for k_ in ("c32", "c34", "c04", "c05", "c07", "c11", "c18", "c21", "c22", "c27", "c28", "c30"):   # 나머지는 손 카메라로 살짝
    S_[k_]["cam"]["hand"] = 0.12 if k_ not in ("c05", "c28") else 0.04
S_["c18"]["cam"]["shake"] = 0.3
for k_ in S_:
    S_[k_].pop("style", None)      # 흐림 효과는 쓰지 않음 (사용자 결정 2026-11-05: 느려짐), 블록도 잘게 나누지 않음

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
        B3.frame(scene, cast, 1.5, 8).save(os.path.join(d, cid + ".png"))
        print(cid, end=" ", flush=True)
    print("\n장면 저장")
