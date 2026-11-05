"""플래넌 등대 편 51개 장면 설정 → 장면/cNN.json (카툰장면.py 가 읽음)
python 연재/플래넌등대/장면_설정.py  (다시 돌리면 덮어씀)"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
D, M, A, J, H = "등대장 제임스 두캣 (43)", "부등대지기 토머스 마셜 (40)", "임시 등대지기 도널드 맥아더 (28)", "교대 등대지기 조지프 무어", "안내자 하람 (14)"
LIVE = ["blink", "breath"]
OIL = {"top": "#2e3b4f", "top_type": "jacket", "coat_len": 0.62, "shirt": "#3a3a3a", "scarf": False}   # 검은 방수 외투
PALE = {"skin": "#ead8cb"}


def ch(who, x, view="front", act=None, scale=0.9, y=1000, **k):
    d = {"who": who, "x": x, "view": view, "act": act or LIVE, "scale": scale, "y": y}
    d.update(k)
    return d


def close(who, x=960, view="front", act=None, sc=2.4, eye_y=470):
    """얼굴 가까이: 눈 높이가 eye_y 가 되게 발 위치를 계산"""
    hgt = {H: 640, A: 790, D: 770, M: 690, J: 720}[who]
    head = {H: 0.25, A: 0.2, D: 0.2, M: 0.22, J: 0.21}[who]
    return ch(who, x, view, act, sc, y=round(eye_y + (hgt - hgt * head * 0.55) * sc))


S = {
 "c01": {"bg": "sea", "opt": {"mood": "storm", "lamp": "off"}, "chars": [], "fx": ["fade_in"]},
 "c02": {"bg": "sea", "opt": {"mood": "grey", "lamp": "off", "far": True, "ship": [-150, 560], "flare": True}, "chars": []},
 "c03": {"bg": "landing", "opt": {"mood": "grey"}, "chars": []},
 "c04": {"bg": "stairs", "chars": [ch(J, 1350, "left", ["run", "blink"], 0.75, y=1010, x_to=620, y_to=440, speed=1.1)]},
 "c05": {"bg": "kitchen", "opt": {"cold": True, "stopped": True, "mood": "grey"}, "chars": [ch(J, 1100, "front", ["blink", "shiver"])]},
 "c06": {"bg": "hook", "opt": {"coat": True}, "chars": []},
 "c07": {"bg": "sea", "opt": {"mood": "fog", "lamp": "off", "far": True}, "chars": [], "fx": ["dark"]},
 "c08": {"bg": "rocks", "opt": {"mood": "day"}, "chars": [ch(H, 960, "front", ["blink", "breath", "talk"], 1.0, y=1040)]},
 "c09": {"bg": "plain", "opt": {"c1": "#2b3a52", "c2": "#7a8fa8"}, "chars": [close(H, act=["blink", "breath", "talk"])]},
 "c10": {"bg": "vortex", "chars": [close(H, act=["closed", "breath"], sc=1.6, eye_y=420)]},
 "c11": {"bg": "rocks", "opt": {"mood": "storm"}, "chars": [ch(H, 820, "right", ["blink", "breath", "shiver"], 0.95, y=1020)], "fx": ["rain"]},
 "c12": {"bg": "rocks", "opt": {"mood": "night"}, "chars": [ch(H, 650, "right", LIVE, 0.9, y=1020), ch(D, 1750, "left", ["walk", "blink", "talk"], 0.95, y=1030, x_to=1180)], "fx": ["rain"]},
 "c13": {"bg": "kitchen", "opt": {"table": True}, "chars": [ch(M, 640, "left", ["blink", "breath", "stir", "talk"], 0.9, y=1010), ch(D, 1700, "front", LIVE, 0.95, y=1040), ch(H, 1320, "front", LIVE, 0.95, y=1050)]},
 "c14": {"bg": "kitchen", "opt": {"table": True}, "chars": [ch(A, 1560, "left", ["blink", "breath", "reach"], 0.95, y=1040), ch(H, 1180, "right", LIVE, 0.95, y=1050)]},
 "c15": {"bg": "kitchen", "opt": {"notice": True}, "chars": [ch(D, 900, "left", ["blink", "breath", "point", "talk"], 0.95, y=1030)]},
 "c16": {"bg": "kitchen", "opt": {"table": True}, "chars": [ch(M, 1450, "front", ["blink", "breath", "talk", "wave"], 0.95, y=1040), ch(H, 1120, "front", ["blink", "breath", "talk"], 0.95, y=1050)]},
 "c17": {"bg": "lantern", "opt": {"mood": "night"}, "chars": [ch(A, 1480, "left", LIVE, 0.85, y=1060), ch(H, 470, "right", LIVE, 0.85, y=1070)]},
 "c18": {"bg": "lantern", "opt": {"mood": "night", "lx": 1450}, "chars": [close(A, 650, "right", ["blink", "breath", "talk"], 2.0, 430)]},
 "c19": {"bg": "lantern", "opt": {"mood": "night", "light": "flicker", "console": True}, "chars": [ch(A, 620, "right", ["blink", "breath", "reach", "talk"], 0.9, y=1060), ch(H, 1320, "left", LIVE, 0.85, y=1070)]},
 "c20": {"bg": "rocks", "opt": {"mood": "day"}, "chars": [ch(M, 760, "right", ["blink", "breath", "reach", "talk"], 0.9, y=1030), ch(H, 1160, "left", ["blink", "breath", "reach"], 0.9, y=1040)]},
 "c21": {"bg": "lantern", "opt": {"mood": "day", "light": "off", "lx": 1080, "wipe": True}, "chars": [ch(D, 700, "right", ["blink", "breath", "wipe", "talk"], 0.9, y=1060)]},
 "c22": {"bg": "kitchen", "opt": {"night": True, "table": True}, "chars": [ch(M, 560, "right", LIVE, 0.9, y=1010), ch(A, 1100, "front", LIVE, 0.9, y=1020), ch(D, 1650, "front", LIVE, 0.95, y=1040)]},
 "c23": {"bg": "kitchen", "opt": {"night": True}, "chars": [ch(M, 620, "front", ["blink", "breath", "talk", "wipe"], 0.9, y=1010), ch(D, 1150, "front", LIVE, 0.95, y=1030), ch(A, 1600, "left", LIVE, 0.9, y=1020)]},
 "c24": {"bg": "sea", "opt": {"mood": "storm", "lamp": "beam"}, "chars": [], "fx": ["rain", "dark"]},
 "c25": {"bg": "bedroom", "chars": [ch(H, 1000, "right", ["blink", "breath"], 0.85, y=1040)]},
 "c26": {"bg": "kitchen", "opt": {"mood": "grey"}, "chars": [ch(D, 700, "right", ["blink", "breath", "talk"], 0.95, y=1030)]},
 "c27": {"bg": "kitchen", "opt": {"door": "open", "mood": "grey"}, "chars": [ch(D, 420, "front", ["blink", "breath", "talk"], 0.95, y=1030, over=OIL), ch(M, 700, "front", LIVE, 0.9, y=1020, over=OIL), ch(A, 1400, "left", LIVE, 0.9, y=1020)]},
 "c28": {"bg": "kitchen", "opt": {"door": "open", "mood": "grey"}, "chars": [ch(M, 900, "right", ["blink", "breath", "pat"], 0.95, y=1020, over=OIL), ch(H, 1120, "left", ["blink", "breath"], 0.85, y=1040)]},
 "c29": {"bg": "lantern", "opt": {"mood": "dusk", "light": "off", "lx": 260, "land": True}, "chars": [ch(D, 1450, "right", ["walk"], 0.18, y=790, x_to=1800, over=OIL), ch(M, 1400, "right", ["walk"], 0.17, y=788, x_to=1750, over=OIL), ch(A, 900, "right", LIVE, 0.9, y=1060), ch(H, 560, "right", LIVE, 0.85, y=1070)]},
 "c30": {"bg": "sea", "opt": {"mood": "dusk", "lamp": "off", "far": True, "swell": True}, "chars": []},
 "c31": {"bg": "lantern", "opt": {"mood": "dusk", "light": "off", "lx": 1600}, "chars": [close(A, 800, "front", ["blink", "shiver", "talk"], 1.8, 440)]},
 "c32": {"bg": "kitchen", "opt": {"door": "open", "hook": "coat", "mood": "storm"}, "chars": [ch(A, 1350, "left", ["run", "talk"], 0.95, y=1030, x_to=160, speed=1.3)]},
 "c33": {"bg": "lantern", "opt": {"mood": "storm", "light": "on", "lx": 1650, "land": True}, "chars": [ch(A, 950, "right", ["run"], 0.2, y=765, x_to=1450, y_to=800), ch(H, 650, "right", ["shout", "blink"], 1.0, y=1080)], "fx": ["rain"]},
 "c34": {"bg": "wave", "chars": []},
 "c35": {"bg": "wave", "opt": {"silhouette": True}, "chars": []},
 "c36": {"bg": "landing", "opt": {"mood": "storm", "bent": True, "wet": True, "flagpole": False}, "chars": []},
 "c37": {"bg": "lantern", "opt": {"mood": "storm", "light": "flicker", "console": True}, "chars": [ch(H, 960, "front", ["blink", "shiver"], 0.95, y=1260)]},
 "c38": {"bg": "lantern", "opt": {"mood": "storm", "light": "flicker", "console": True}, "chars": [ch(H, 960, "front", ["blink", "breath", "talk"], 1.0, y=1200)], "fx": ["glow"]},
 "c39": {"bg": "lantern", "opt": {"mood": "night", "light": "dim"}, "chars": [ch(H, 960, "front", ["closed", "breath"], 1.0, y=1100, opacity=0.85)], "fx": ["glow"]},
 "c40": {"bg": "sea", "opt": {"mood": "night", "lamp": "off", "far": True, "ship": [-200, 900]}, "chars": []},
 "c41": {"bg": "sea", "opt": {"mood": "day", "present": True}, "chars": [ch(H, 380, "back", LIVE, 0.95, y=1120)]},
 "c42": {"bg": "ring", "chars": [ch(H, 1500, "left", ["blink", "breath"], 1.0, y=1100)]},
 "c43": {"bg": "crevice", "chars": []},
 "c44": {"bg": "papers", "chars": []},
 "c45": {"bg": "desk", "chars": []},
 "c46": {"bg": "rocks", "opt": {"mood": "storm"}, "chars": [ch(A, 250, "right", ["run"], 0.95, y=1030, x_to=1750)], "fx": ["rain", "past"]},
 "c47": {"bg": "hook", "opt": {"ruin": True}, "chars": [ch(H, 960, "back", LIVE, 1.1, y=1250)]},
 "c48": {"bg": "hook", "opt": {"ruin": True, "hand": True}, "chars": []},
 "c49": {"bg": "sea", "opt": {"mood": "dusk", "present": True}, "chars": []},
 "c50": {"bg": "sea", "opt": {"mood": "night", "present": True, "far": True}, "chars": []},
 "c51": {"bg": "rocks", "opt": {"mood": "dusk"}, "chars": [ch(H, 800, "right", ["walk"], 0.95, y=1030, x_to=1700)]},
}

if __name__ == "__main__":
    d = os.path.join(HERE, "장면")
    os.makedirs(d, exist_ok=True)
    for cid, sc in S.items():
        sc = {"cast": "../등장인물_카툰.json", **sc}
        json.dump(sc, open(os.path.join(d, cid + ".json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(len(S), "장면 설정 저장")
