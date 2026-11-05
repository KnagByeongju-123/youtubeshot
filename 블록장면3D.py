"""입체 블록 장면 — 장면 설정(json, "engine": "3d") → 그 순간의 그림 (블록3D.py 엔진, GPU 없이)
  장면 json: {"engine": "3d", "cast": "../등장인물_카툰.json", "set": "island|stairs|kitchen|hook|rocks|plain|...", "opt": {...},
             "cam": {"pos": [x,y,z], "look": [x,y,z], "fov": 40, "move": [dx,dy,dz]},   # move = 장면 동안 카메라가 움직이는 거리
             "chars": [{"who": 이름, "at": [x,z], "to": [x,z], "face": 도, "act": [...], "y": 높이, "scale": 1}], "fx": ["rain", "fade_in", "dark"]}
  - act: blink breath talk stir wave point reach pat wipe walk run shout closed shiver
  - 영상 프로그램(shorts_novel_maker)이 그림 옆 <그림>.json 이 "engine": "3d" 이면 이 파일로 그림
  python 블록장면3D.py <장면.json> <결과.png> [--t 1.0]"""
import importlib.util
import json
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
_sp = importlib.util.spec_from_file_location("b3d", os.path.join(HERE, "블록3D.py"))
E = importlib.util.module_from_spec(_sp)
_sp.loader.exec_module(E)
Box, Voxels, Camera, person = E.Box, E.Voxels, E.Camera, E.person

MOOD = {   # 하늘 위·아래, 바다, 빛 세기, 색 덧씌움
    "day": ((120, 165, 205), (205, 225, 235), "#3f7fa6", 1.0, None),
    "grey": ((110, 125, 138), (180, 190, 196), "#4a6878", 0.9, None),
    "storm": ((45, 52, 62), (100, 112, 124), "#2c4252", 0.75, (40, 50, 70, 0.18)),
    "dusk": ((70, 72, 120), (235, 160, 110), "#3c5272", 0.85, (255, 150, 90, 0.08)),
    "night": ((10, 18, 45), (40, 55, 90), "#14243c", 0.55, (20, 30, 80, 0.3)),
    "fog": ((160, 166, 170), (205, 208, 210), "#6d7d88", 0.85, (220, 224, 226, 0.25)),
}
_STATIC = {}


def _static(key, fn):
    """움직이지 않는 블록은 한 번만 만들어 둠"""
    if key not in _STATIC:
        _STATIC[key] = fn()
    return _STATIC[key]


# ───────────────────────── 장소 ─────────────────────────
def sea_tiles(t, mood, x0=-40, x1=60, z0=-50, z1=30, step=2, rough=1.0):
    col = E.hexrgb(MOOD[mood][2])
    out = []
    for x in range(x0, x1, step):
        for z in range(z0, z1, step):
            h = 0.25 * rough * math.sin(t * 1.3 + x * 0.35 + z * 0.22) + 0.15 * rough * math.sin(t * 0.9 - x * 0.2 + z * 0.4)
            c = col * (1.0 + 0.06 * math.sin(x * 1.7 + z * 0.9)) + (25 if h > 0.25 * rough else 0)
            out.append(Box((x, -1 + h, z), (step, 1, step), np.clip(c, 0, 255), skip=(0, 2, 3, 5), edge=False))
    return out


def island_vox(present=False):
    vx = Voxels()
    cx, cz, R = 8, -14, 10
    for x in range(cx - R - 2, cx + R + 3):
        for z in range(cz - R + 2, cz + R - 1):
            d = math.hypot((x - cx) / R, (z - cz) / (R * 0.75))
            if d > 1.05:
                continue
            h = int(1 + 7 * max(0.0, 1 - d) ** 0.6 + (1 if (x * 7 + z * 3) % 5 == 0 else 0))
            for y in range(-1, h):
                vx.put(x, y, z, "#6f6a62" if y < h - 1 else "#5f8a4a", j=14)
    top = 8
    for y in range(top, top + 9):                                 # 등대 탑 (흰 블록 2×2)
        for x in (cx, cx + 1):
            for z in (cz - 1, cz):
                vx.put(x, y, z, "#f1efe8", j=6)
    for x in range(cx - 1, cx + 3):
        for z in range(cz - 2, cz + 2):
            vx.put(x, top + 9, z, "#2f2f33", j=4)                 # 꼭대기 받침
            vx.put(x, top + 11, z, "#2f2f33", j=4)                # 지붕
    for x in range(cx - 7, cx - 2):                               # 숙소
        for z in range(cz - 3, cz + 1):
            for y in range(top - 1, top + 2):
                vx.put(x, y, z, "#e9e4d8", j=8)
            vx.put(x, top + 2, z, "#5a5f66", j=6)
    return vx.boxes()


def set_island(t, p, o):
    mood = o.get("mood", "grey")
    b = sea_tiles(t, mood) + _static(("island", o.get("present", False)), island_vox)
    cx, cz, top = 8, -14, 8
    lamp = o.get("lamp", "on")
    on = lamp != "off"
    b.append(Box((cx - 0.5, top + 10, cz - 1.5), (3, 1, 3), "#fff1a8" if on else "#3a4552", emit=on, edge=False))
    if lamp == "beam" or (on and mood in ("night", "dusk", "storm")):
        a = t * 40
        piv = np.array([cx + 1, top + 10.5, cz])
        b.append(Box((cx + 1, top + 10.2, cz - 0.3), (40, 0.6, 0.6), (255, 244, 194), [(piv, "y", a)], emit=True, edge=False))
    if o.get("ship"):
        s0, s1 = o["ship"]
        q = min(1.0, p / 0.55)
        q = 0.5 - 0.5 * math.cos(math.pi * q)
        sx = s0 + (s1 - s0) * q
        bob = 0.15 * math.sin(t * 1.6)
        b += [Box((sx, -0.6 + bob, 4), (7, 1.4, 2.6), "#2e2b2a"), Box((sx + 1.5, 0.8 + bob, 4.4), (3.5, 1.4, 1.8), "#d9d2c3"),
              Box((sx + 2.6, 2.2 + bob, 4.9), (0.9, 2.2, 0.9), "#a83232"), Box((sx + 6, 0.8 + bob, 5.1), (0.2, 3.5, 0.2), "#2b2b2b")]
        if o.get("flare") and p > 0.55:
            ph = min(1.0, (p - 0.55) / 0.35)
            fy = 1 + 16 * math.sin(ph * math.pi / 2)
            for k in range(6):   # 연기 꼬리
                b.append(Box((sx + 3 + ph * 2 - k * 0.08, fy - k * 1.2 * ph, 5.0), (0.25, 0.25, 0.25), (255, 200, 170), emit=True, edge=False))
            b.append(Box((sx + 2.6 + ph * 2, fy, 4.8), (0.9 + ph, 0.9 + ph, 0.9 + ph), (255, 90, 60), emit=True, edge=False))
    return b, mood


def set_stairs(t, p, o):
    mood = o.get("mood", "grey")
    def build():
        vx = Voxels()
        for x in range(-6, 30):
            for z in range(-12, 4):
                h = int(max(0, (x + 4) * 0.45))
                for y in range(-1, min(h, 12)):
                    vx.put(x, y, z, "#6f6a62" if y < h - 1 else "#5f8a4a", j=12)
        for k in range(10):   # 돌계단 (왼쪽 아래 → 오른쪽 위)
            for z in (1, 2):
                vx.put(20 - k * 2, 9 - k + 0, z, "#9a9c9e", j=8)
                vx.put(19 - k * 2, 9 - k + 0, z, "#9a9c9e", j=8)
        return vx.boxes()
    return sea_tiles(t, mood, -40, 10, -10, 40) + _static("stairs", build), mood


def set_kitchen(t, p, o):
    b = E.kitchen(t if not o.get("stopped") else 0.0)
    if o.get("cold"):   # 꺼진 난로: 불꽃·김을 뺌 (emit 상자 중 주황·흰 것)
        b = [x for x in b if not (x.emit and (x.col[0] > 200 and x.col[2] < 120 or x.col.min() > 230))]
    if o.get("stopped"):
        pass
    return b, o.get("mood", "indoor")


def set_hook(t, p, o):
    def build():
        vx = Voxels()
        vx.fill(-2, 14, 0, 10, -1, 0, "#c9bb98", 16)
        vx.fill(-2, 14, -1, 0, -1, 6, "#8a6141", 14)
        return vx.boxes()
    b = list(_static("hookwall", build))
    b.append(Box((2, 7, 0), (8, 0.5, 0.6), "#6b4a30"))
    for k in range(3):
        b.append(Box((3.2 + k * 2.6, 6.3, 0.2), (0.3, 0.8, 0.5), "#3b3b3b"))
    if o.get("coat", True):
        sway = 3 * math.sin(t * 1.3)
        piv = np.array([5.95, 6.6, 0.4])
        b += [Box((4.7, 1.6, 0.3), (2.5, 5.0, 0.7), "#2e3b4f", [(piv, "z", sway)]), Box((5.3, 5.6, 0.95), (1.3, 1.0, 0.1), "#26303f", [(piv, "z", sway)]),
              Box((4.4, 3.8, 0.35), (0.5, 2.8, 0.6), "#26303f", [(piv, "z", sway)]), Box((7.0, 3.8, 0.35), (0.5, 2.8, 0.6), "#26303f", [(piv, "z", sway)])]
    return b, "indoor"


def set_rocks(t, p, o):
    mood = o.get("mood", "grey")
    def build():
        vx = Voxels()
        for x in range(-20, 30):
            for z in range(-2, 12):
                h = rock_height(x, z)
                for y in range(-1, max(0, h)):
                    vx.put(x, y, z, "#4c4f52" if y < h - 1 else "#5a5d60", j=16)
        return vx.boxes()
    return sea_tiles(t, mood, -40, 50, -40, 0, rough=1.6 if mood == "storm" else 1.0) + _static("rocks", build), mood


def rock_height(x, z):
    """바위 해안 높이: 뒤(바다 쪽, z<3)는 울퉁불퉁, 인물이 서는 가운데(3~8)는 평평한 1, 카메라 쪽(z>8)은 낮게"""
    if z > 8:
        return 0
    if z >= 3:
        return 1
    return max(1, int(1.6 + 1.5 * math.sin(x * 0.4) * math.cos(z * 0.7)))


def set_plain(t, p, o):
    return [], o.get("mood", "plain")


SETS = {"island": set_island, "stairs": set_stairs, "kitchen": set_kitchen, "hook": set_hook, "rocks": set_rocks, "plain": set_plain}


# ───────────────────────── 움직임 ─────────────────────────
def pose3d(acts, t, seed):
    p = {}
    if "breath" in acts:
        p["breath"] = 0.004 * math.sin(t * 2 * math.pi / 3.6 + seed)
    if "blink" in acts:
        p["blink"] = (t + seed * 0.7) % (3.2 + (seed % 3) * 0.4) < 0.12
    if "closed" in acts:
        p["blink"] = True
    if "talk" in acts:
        p["talk"] = abs(math.sin(t * 11 + seed)) * (0.5 + 0.5 * math.sin(t * 3.1))
    if "shout" in acts:
        p["talk"] = 0.8 + 0.2 * abs(math.sin(t * 6))
        p["arm"] = 60 + 20 * math.sin(t * 5)
        p["arm2"] = 60 + 20 * math.sin(t * 5 + 1)
    if "stir" in acts:
        p["arm"] = 70 + 12 * math.sin(t * 2 * math.pi / 1.4)
    if "wave" in acts:
        p["arm_r"] = 150 + 18 * math.sin(t * 2 * math.pi / 0.6)
    if "point" in acts or "reach" in acts:
        p["arm"] = 85 + 4 * math.sin(t * 2)
    if "pat" in acts:
        p["arm"] = 120 + 8 * math.sin(t * 2 * math.pi / 0.8)
    if "wipe" in acts:
        p["arm"] = 95 + 14 * math.sin(t * 3)
    if "walk" in acts:
        p["walk"] = t * 2 * math.pi / 0.9
        p["bob"] = -0.06 * abs(math.sin(t * 2 * math.pi / 0.9))
    if "run" in acts:
        p["walk"] = t * 2 * math.pi / 0.5
        p["bob"] = 0.12 * abs(math.sin(t * 2 * math.pi / 0.5))
        p["walk_amp"] = 1.6
    if "shiver" in acts:
        p["bob"] = 0.015 * math.sin(t * 40)
    return p


def frame(scene, cast, t, dur=None):
    """장면의 t 초 그림 (PIL, 1920×1080)"""
    dur = dur or scene.get("dur", 8.0)
    pr = min(1.0, max(0.0, t / max(0.1, dur)))
    o = scene.get("opt", {})
    boxes, mood = SETS[scene.get("set", "plain")](t, pr, o)
    boxes = list(boxes)
    for i, ch in enumerate(scene.get("chars", [])):
        c = {**cast[ch["who"]], **ch.get("over", {})}
        ax, az = ch.get("at", [0, 0])
        acts = list(ch.get("act", ["blink", "breath"]))
        face = ch.get("face", 0)
        if "to" in ch:
            q = min(1.0, pr * ch.get("speed", 1.0))
            bx, bz = ch["to"]
            ax, az = ax + (bx - ax) * q, az + (bz - az) * q
            if q >= 1.0:
                acts = [a for a in acts if a not in ("walk", "run")]
        y = ch.get("y")
        if y is None:
            y = rock_height(int(ax), int(az)) if scene.get("set") == "rocks" else 0
        if ch.get("y_to") is not None:
            y = y + (ch["y_to"] - y) * min(1.0, pr * ch.get("speed", 1.0))
        boxes += person(c, (ax, y, az), face=face, pose=pose3d(acts, t, i * 1.7 + 0.3), scale=ch.get("scale", 1.0))
    fx = scene.get("fx", [])
    if "rain" in fx:
        cp = scene["cam"]["pos"]
        for k in range(90):
            rx = cp[0] - 14 + (k * 37 % 28)
            rz = cp[2] - 22 + (k * 53 % 18)
            ry = 14 - ((t * 18 + k * 1.37) % 16)
            boxes.append(Box((rx, ry, rz), (0.05, 0.7, 0.05), (200, 214, 228), emit=True, edge=False))
    cm = scene.get("cam", {"pos": [12, 6, 24], "look": [12, 3, 0]})
    mv = np.array(cm.get("move", [0, 0, 0]), float) * (0.5 - 0.5 * math.cos(math.pi * pr))
    cam = Camera(np.array(cm["pos"], float) + mv, np.array(cm["look"], float) + mv * cm.get("look_follow", 1.0), fov=cm.get("fov", 40))
    md = MOOD.get(mood)
    if md:
        img = E.render(boxes, cam, sky=(md[0], md[1]))
    elif mood == "plain":
        a, b = o.get("c1", (43, 58, 82)), o.get("c2", (122, 143, 168))
        img = E.render(boxes, cam, sky=(b, a))
    else:
        img = E.render(boxes, cam, bg=(40, 36, 34))
    tint = md[4] if md else None
    if o.get("night"):
        tint = (20, 30, 80, 0.35)
    if tint:
        img = Image.blend(img, Image.new("RGB", img.size, tint[:3]), tint[3])
    if "dark" in fx:
        img = Image.blend(img, Image.new("RGB", img.size, (5, 7, 15)), 0.35)
    if "past" in fx:
        img = Image.blend(img, Image.new("RGB", img.size, (200, 168, 120)), 0.25)
    if "glow" in fx:
        img = Image.blend(img, Image.new("RGB", img.size, (255, 246, 208)), min(0.9, pr ** 2 * 1.1))
    if "fade_in" in fx and t < 1.2:
        img = Image.blend(Image.new("RGB", img.size, (0, 0, 0)), img, t / 1.2)
    return img


def load(scene_path):
    scene = json.load(open(scene_path, encoding="utf-8"))
    cp = scene["cast"] if os.path.isabs(scene["cast"]) else os.path.join(os.path.dirname(scene_path), scene["cast"])
    cast = {c["name"]: c for c in json.load(open(cp, encoding="utf-8"))["chars"]}
    return scene, cast


if __name__ == "__main__":
    a = sys.argv[1:]
    sc, cast = load(a[0])
    t = float(a[a.index("--t") + 1]) if "--t" in a else 1.0
    frame(sc, cast, t, sc.get("dur", 8)).save(a[1])
