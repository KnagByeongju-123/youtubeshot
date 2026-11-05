"""플래넌 등대 편 — 입체 블록 장면 설정 → 장면3D/cNN.json + 멈춘 그림 cNN.png (블록장면3D.py)
python 연재/플래넌등대/장면3D_설정.py   (아직 입체로 안 만든 장면은 영상에서 예전 카툰 장면을 씀)"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
D, M, A, J, H = "등대장 제임스 두캣 (43)", "부등대지기 토머스 마셜 (40)", "임시 등대지기 도널드 맥아더 (28)", "교대 등대지기 조지프 무어", "안내자 하람 (14)"
LIVE = ["blink", "breath"]
OIL = {"top": "#2e3b4f", "top_type": "jacket", "coat_len": 0.62, "shirt": "#3a3a3a", "scarf": False}   # 검은 방수 외투 (모자는 그대로)
PALE = {"skin": "#ead8cb"}
KCAM = {"pos": [13, 8.0, 24], "look": [13, 3.6, 4], "fov": 44, "move": [0.6, -0.5, -1.8]}


def ch(who, at, face=0, act=None, **k):
    d = {"who": who, "at": at, "face": face, "act": act or LIVE}
    d.update(k)
    return d


S = {
 # ── 1구간 (0~2분) ──
 "c01": {"set": "island", "opt": {"mood": "storm", "lamp": "off"}, "cam": {"pos": [8, 10, 34], "look": [8, 7, -14], "fov": 44, "move": [-3, -1, -6]}, "fx": ["fade_in"]},
 "c02": {"set": "island", "opt": {"mood": "grey", "lamp": "off", "ship": [-34, -6], "flare": True}, "cam": {"pos": [-2, 7, 30], "look": [0, 6, -6], "fov": 52, "move": [2, 0, -2]}},
 "c04": {"set": "stairs", "opt": {"mood": "grey"}, "cam": {"pos": [6, 9, 24], "look": [10, 6, 0], "fov": 48, "move": [10, 4, 0]},
         "chars": [ch(J, [2.5, 1.5], 90, ["run", "blink"], to=[20.5, 1.5], y_to=0, speed=1.1)]},
 "c05": {"set": "kitchen", "opt": {"cold": True, "stopped": True, "bed": True}, "cam": KCAM, "chars": [ch(J, [12, 7], 0, ["blink", "shiver"])]},
 "c06": {"set": "hook", "cam": {"pos": [6, 4.5, 11], "look": [6, 4.2, 0], "fov": 42, "move": [0, 0, -2]}},
 "c07": {"set": "island", "opt": {"mood": "fog", "lamp": "off"}, "cam": {"pos": [8, 9, 48], "look": [8, 8, -14], "fov": 40, "move": [0, 0, -4]}, "fx": ["dark"]},
 "c08": {"set": "rocks", "opt": {"mood": "day"}, "cam": {"pos": [5, 6, 19], "look": [5, 4, 4], "fov": 44, "move": [0, -0.5, -2]}, "chars": [ch(H, [5, 6], 0, ["blink", "breath", "talk"])]},
 "c09": {"set": "plain", "cam": {"pos": [0, 4.4, 5.2], "look": [0, 4.2, 0], "fov": 40, "move": [0, 0, -0.6]}, "chars": [ch(H, [0, 0], 0, ["blink", "breath", "talk"])]},
 "c11": {"set": "rocks", "opt": {"mood": "storm"}, "cam": {"pos": [2, 6, 17], "look": [5, 3, 3], "fov": 46, "move": [1, 0, -2]}, "chars": [ch(H, [5, 5], 55, ["blink", "breath", "shiver"])], "fx": ["rain"]},
 "c12": {"set": "rocks", "opt": {"mood": "night"}, "cam": {"pos": [7, 6, 20], "look": [7, 3, 4], "fov": 46},
         "chars": [ch(H, [3, 6], 80), ch(D, [15, 6], -90, ["walk", "blink", "talk"], to=[7, 6])], "fx": ["rain"]},
 "c13": {"set": "kitchen", "cam": KCAM, "chars": [ch(M, [6.1, 2.9], -80, ["blink", "breath", "stir", "talk"]), ch(D, [21.0, 5.6], -15), ch(H, [17.2, 5.4], 10)]},
 "c14": {"set": "kitchen", "cam": KCAM, "chars": [ch(A, [20.0, 5.6], -50, ["blink", "breath", "reach"], hold="#d8b27a"), ch(H, [16.6, 5.4], 40)]},
 # ── 2구간 (2~4분) ──
 "c18": {"set": "lantern", "opt": {"mood": "night"}, "cam": {"pos": [6.5, 4.6, 5.5], "look": [2, 4.3, -1], "fov": 40, "move": [-0.5, 0, -0.5]},
         "chars": [ch(A, [3.4, -0.3], 40, ["blink", "breath", "talk"])]},
 "c19": {"set": "lantern", "opt": {"mood": "night", "light": "flicker"}, "cam": {"pos": [0, 5.5, 13], "look": [0, 3.2, 0], "fov": 46, "move": [1, -0.3, -1.5]},
         "chars": [ch(A, [-3.3, 1.2], 70, ["blink", "breath", "reach", "talk"]), ch(H, [3.4, 1.6], -60)]},
 "c26": {"set": "kitchen", "opt": {"mood": "grey"}, "cam": {"pos": [21.5, 5.4, 8.5], "look": [12.5, 4.0, 1.0], "fov": 46, "move": [-1, 0, -0.5]},
         "chars": [ch(D, [13, 2.2], 150, ["blink", "breath", "talk"])]},
 "c27": {"set": "kitchen", "opt": {"door": "open", "hook": "empty"}, "cam": {"pos": [11, 6.0, 13.5], "look": [3, 3.4, 7.5], "fov": 58},
         "chars": [ch(D, [1.6, 9.5], 60, ["blink", "breath", "talk"], over=OIL), ch(M, [3.6, 8.0], 40, LIVE, over=OIL), ch(A, [8.0, 5.8], -60)]},
 "c30": {"set": "island", "opt": {"mood": "dusk", "lamp": "off", "swell": True}, "cam": {"pos": [8, 12, 44], "look": [8, 6, -30], "fov": 44, "move": [0, 0, -3]}},
 "c31": {"set": "lantern", "opt": {"mood": "dusk", "light": "off"}, "cam": {"pos": [2.0, 5.4, 6.0], "look": [2.0, 5.1, 0], "fov": 40, "move": [0, 0, -0.6]},
         "chars": [ch(A, [2.0, 1.0], 0, ["blink", "shiver", "talk"], over=PALE)]},
 "c32": {"set": "kitchen", "opt": {"door": "open", "hook": "coat", "mood": "storm"}, "cam": {"pos": [12, 6.0, 13.5], "look": [2, 3.4, 6.5], "fov": 60},
         "chars": [ch(A, [10, 8.5], -100, ["run", "talk"], to=[-3.5, 9.5], speed=1.1, exit=True)]},
 "c33": {"set": "lantern", "opt": {"mood": "storm", "light": "on", "land": True}, "cam": {"pos": [1.5, 5.6, 11.5], "look": [15, -3.5, -2], "fov": 60},
         "chars": [ch(H, [5.2, 4.2], 60, ["shout", "blink"]), ch(A, [16, 4], 75, ["run"], y=-10 - (12 - 8) * 0.18, y_to=-10 - (28 - 8) * 0.18, to=[28, 7.5], speed=1.0)], "fx": ["rain"]},
 "c34": {"set": "wave", "cam": {"pos": [-10, 12, 44], "look": [2, 9, 0], "fov": 52}},
 "c35": {"set": "wave", "opt": {"silhouette": True}, "cam": {"pos": [19, 19, 9], "look": [5, 12.5, -0.5], "fov": 50, "move": [-2, 0, -1]}},
 "c36": {"set": "landing", "opt": {"mood": "storm", "bent": True, "wet": True}, "cam": {"pos": [-6, 9, 22], "look": [4, 3, 2], "fov": 48, "move": [2, -1, -2]}},
 # ── 3구간 (4분~끝) ──
 "c37": {"set": "lantern", "opt": {"mood": "storm", "light": "flicker"}, "cam": {"pos": [3.5, 3.6, 10], "look": [0.5, 2.0, 0], "fov": 48, "move": [-0.5, 0, -1]},
         "chars": [ch(H, [1.5, 3.0], -20, ["blink", "shiver", "sit"])], "fx": ["rain"]},
 "c38": {"set": "lantern", "opt": {"mood": "storm", "light": "flicker"}, "cam": {"pos": [3.8, 5.0, 9.5], "look": [0.8, 4.0, 0], "fov": 44, "move": [-0.4, 0, -1.2]},
         "chars": [ch(H, [1.8, 3.0], -15, ["blink", "breath", "talk", "reach"], hold="#f1e6c8")], "fx": ["glow"]},
 "c39": {"set": "lantern", "opt": {"mood": "night", "light": "dim"}, "cam": {"pos": [0, 5.0, 12], "look": [0, 3.8, 0], "fov": 46, "move": [0, 0, -2]},
         "chars": [ch(H, [0, 3.5], 0, ["closed", "breath"])], "fx": ["glow"]},
 "c40": {"set": "island", "opt": {"mood": "night", "lamp": "off", "ship": [-60, 30]}, "cam": {"pos": [0, 7, 40], "look": [6, 6, -10], "fov": 50}},
 "c41": {"set": "rocks", "opt": {"mood": "day", "island": True}, "cam": {"pos": [3, 6.5, 17], "look": [8, 5, -30], "fov": 50, "move": [1, 0, -2]},
         "chars": [ch(H, [5, 5.5], 180, LIVE)]},
 "c46": {"set": "rocks", "opt": {"mood": "storm"}, "cam": {"pos": [6, 6, 20], "look": [6, 3, 3], "fov": 52},
         "chars": [ch(A, [-6, 5], 90, ["run"], to=[20, 5], speed=1.0, exit=True)], "fx": ["rain", "past"]},
 "c48": {"set": "hook", "opt": {"ruin": True, "hand": True}, "cam": {"pos": [6, 6.5, 8], "look": [6, 6.6, 0], "fov": 42, "move": [0, 0, -1]}},
 "c50": {"set": "island", "opt": {"mood": "night", "present": True, "lamp": "beam"}, "cam": {"pos": [8, 9, 52], "look": [8, 9, -14], "fov": 40, "move": [0, 0, -3]}},
 "c51": {"set": "rocks", "opt": {"mood": "dusk", "island": True}, "cam": {"pos": [-2, 6, 16], "look": [10, 3.5, 2], "fov": 50},
         "chars": [ch(H, [2, 6], 100, ["walk"], to=[16, 4.5], speed=1.0)]},
}

if __name__ == "__main__":
    sys.path.insert(0, ROOT)
    import importlib.util
    sp = importlib.util.spec_from_file_location("bs3", os.path.join(ROOT, "블록장면3D.py"))
    B3 = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(B3)
    d = os.path.join(HERE, "장면3D")
    os.makedirs(d, exist_ok=True)
    only = sys.argv[1].split(",") if len(sys.argv) > 1 else None
    for cid, sc in S.items():
        if only and cid not in only:
            continue
        sc = {"engine": "3d", "cast": "../등장인물_카툰.json", **sc}
        p = os.path.join(d, cid + ".json")
        old = open(p, encoding="utf-8").read() if os.path.exists(p) else None
        new = json.dumps(sc, ensure_ascii=False, indent=1)
        if old != new:   # 안 바뀐 장면은 파일 날짜를 그대로 (영상 구간 캐시 유지)
            open(p, "w", encoding="utf-8").write(new)
        scene, cast = B3.load(p)
        B3.frame(scene, cast, 1.5, 8).save(os.path.join(d, cid + ".png"))
        print(cid, end=" ", flush=True)
    print("\n장면 저장")
