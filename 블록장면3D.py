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
            if cx - 8 <= x <= cx + 3 and cz - 4 <= z <= cz + 2:   # 건물이 서는 꼭대기는 평평하게 (떠 보이지 않게)
                h = 8
            for y in range(-1, h):
                vx.put(x, y, z, "#6f6a62" if y < h - 1 else "#5f8a4a", j=14)
    top = 8
    for y in range(top, top + 9):                                 # 등대 탑 (흰 블록 3×3)
        for x in (cx - 1, cx, cx + 1):
            for z in (cz - 2, cz - 1, cz):
                vx.put(x, y, z, "#f1efe8", j=6)
    for x in range(cx - 2, cx + 3):
        for z in range(cz - 3, cz + 2):
            vx.put(x, top + 9, z, "#2f2f33", j=4)                 # 꼭대기 받침(난간)
    for x in range(cx - 1, cx + 2):
        for z in range(cz - 2, cz + 1):
            vx.put(x, top + 11, z, "#2f2f33", j=4)                # 지붕
    vx.put(cx, top + 12, cz - 1, "#2f2f33", j=4)
    for x in range(cx - 7, cx - 2):                               # 숙소 (땅에 붙음)
        for z in range(cz - 3, cz + 1):
            for y in range(top, top + 3):
                vx.put(x, y, z, "#e9e4d8", j=8)
            vx.put(x, top + 3, z, "#5a5f66", j=6)
    for x in (cx - 6, cx - 4):                                    # 숙소 창문
        vx.put(x, top + 1, cz + 1, "#3a4552", j=4)
    return vx.boxes()


def set_island(t, p, o):
    mood = o.get("mood", "grey")
    b = sea_tiles(t, mood) + _static(("island", o.get("present", False)), island_vox)
    cx, cz, top = 8, -14, 8
    lamp = o.get("lamp", "on")
    on = lamp != "off"
    b.append(Box((cx - 1, top + 10, cz - 2), (3, 1, 3), "#fff1a8" if on else "#3a4552", emit=on, edge=False))   # 등불 방 유리
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
        b += [Box((sx, -0.6 + bob, 4), (7, 1.4, 2.6), "#2e2b2a"), Box((sx + 7, -0.3 + bob, 4.4), (1.2, 1.1, 1.8), "#2e2b2a"), Box((sx + 8.2, 0.0 + bob, 4.8), (0.8, 0.8, 1.0), "#2e2b2a"),
              Box((sx + 1.5, 0.8 + bob, 4.4), (3.5, 1.4, 1.8), "#d9d2c3"), Box((sx + 2.0, 1.5 + bob, 6.21), (2.5, 0.4, 0.02), "#3a4552", edge=False),
              Box((sx + 2.6, 2.2 + bob, 4.9), (0.9, 2.2, 0.9), "#a83232"), Box((sx + 6, 0.8 + bob, 5.1), (0.2, 3.5, 0.2), "#2b2b2b")]
        if o.get("flare") and p > 0.55:
            ph = min(1.0, (p - 0.55) / 0.35)
            fy = 1 + 11 * math.sin(ph * math.pi / 2)
            for k in range(6):   # 연기 꼬리
                b.append(Box((sx + 3 + ph * 2 - k * 0.08, fy - k * 1.2 * ph, 5.0), (0.25, 0.25, 0.25), (255, 200, 170), emit=True, edge=False))
            b.append(Box((sx + 2.6 + ph * 2, fy, 4.8), (0.9 + ph, 0.9 + ph, 0.9 + ph), (255, 90, 60), emit=True, edge=False))
    return b, mood


def stair_h(x):
    """돌계단 언덕 높이: 2칸마다 한 계단씩 (x 1 → 1층, x 22 → 11층)"""
    return max(1, min(12, 1 + (x - 1) // 2)) if x >= 1 else 0   # 23 이후는 꼭대기 평지


def set_stairs(t, p, o):
    mood = o.get("mood", "grey")
    def build():
        vx = Voxels()
        for x in range(-6, 44):
            for z in range(-16, 4):
                h = stair_h(x)
                path = 0 <= z <= 2 and 1 <= x <= 22
                for y in range(-1, h):
                    top_ = y == h - 1
                    vx.put(x, y, z, ("#a3a5a7" if path else "#5f8a4a") if top_ else ("#8e9092" if path else "#6f6a62"), j=10)
        for y in range(stair_h(24), stair_h(24) + 7):   # 언덕 위 등대
            for x in (24, 25):
                for z in (-3, -2):
                    vx.put(x, y, z, "#f1efe8", j=6)
        for x in (23, 24, 25, 26):
            for z in (-4, -3, -2, -1):
                vx.put(x, stair_h(24) + 7, z, "#2f2f33", j=4)
        return vx.boxes()
    posts = []
    for x in range(2, 23, 3):   # 돌길 옆 가는 쇠 난간 (기둥 + 가로대)
        posts.append(Box((x + 0.4, stair_h(x), 3.1), (0.15, 1.3, 0.15), "#3b3b3b", edge=False))
        posts.append(Box((x + 0.4, stair_h(x) + 1.15, 3.1), (3.36, 0.1, 0.1), "#3b3b3b", [(np.array([x + 0.4, stair_h(x) + 1.2, 3.15]), "z", 26.5)], edge=False))
    return sea_tiles(t, mood, -40, 10, -10, 40) + _static("stairs", build) + posts, mood


def set_kitchen(t, p, o):
    b = E.kitchen(t if not o.get("stopped") else 0.0)
    if o.get("bed"):    # 빈 침대 (오른쪽 벽 앞)
        b += [Box((6.2, 0, 0.6), (3.0, 1.0, 4.6), "#7a5232"), Box((6.3, 1.0, 0.7), (2.8, 0.4, 4.4), "#e9e1cf"),
              Box((6.5, 1.4, 0.8), (2.4, 0.3, 1.0), "#f4f1ea"), Box((6.1, 0, 0.3), (3.2, 2.4, 0.3), "#6b4a30")]
    if o.get("door"):   # 왼쪽 벽의 문 (열리면 밖의 흐린 하늘빛)
        b = [x for x in b if not (x.p[0] == -1 and 0 <= x.p[1] <= 4 and 8 <= x.p[2] <= 10)]
        b += [Box((-1.05, 0, 7.8), (0.3, 5.2, 0.25), "#6b4a30"), Box((-1.05, 0, 11.0), (0.3, 5.2, 0.25), "#6b4a30"), Box((-1.05, 5.0, 7.8), (0.3, 0.3, 3.45), "#6b4a30")]
        if o["door"] == "open":
            b += [Box((-1.6, 0, 8.05), (0.1, 5.0, 2.95), (200, 210, 218), emit=True, edge=False),
                  Box((-0.95, 0, 11.0), (0.15, 5.0, 2.9), "#7a5232", [(np.array([-0.95, 0, 11.0]), "y", 110)])]   # 문짝은 바깥쪽으로 열림
        else:
            b.append(Box((-1.0, 0, 8.05), (0.15, 5.0, 2.95), "#7a5232"))
    if o.get("hook"):   # 문 옆 옷걸이 (+ 걸린 방수 외투)
        b += [Box((-0.95, 5.6, 3.0), (0.3, 0.3, 3.2), "#6b4a30"), Box((-0.7, 5.2, 4.4), (0.3, 0.5, 0.2), "#3b3b3b")]
        if o["hook"] == "coat":
            sway = 2 * math.sin(t * 1.3)
            pv = np.array([-0.5, 5.5, 4.5])
            R_ = [(pv, "x", sway)]
            b += [Box((-0.8, 1.6, 3.3), (0.6, 3.8, 2.4), "#3c4c66", R_), Box((-0.8, 4.5, 3.0), (0.6, 0.9, 3.0), "#3c4c66", R_),
                  Box((-0.78, 2.3, 2.7), (0.55, 2.8, 0.5), "#33425a", R_), Box((-0.78, 2.3, 5.75), (0.55, 2.8, 0.5), "#33425a", R_)]
            for k in range(3):
                b.append(Box((-0.22, 4.2 - k * 0.9, 4.45), (0.05, 0.16, 0.16), "#c9b25a", R_, edge=False))
    if o.get("cold"):   # 꺼진 난로: 불꽃·김을 뺌 (emit 상자 중 주황·흰 것)
        b = [x for x in b if not (x.emit and (x.col[0] > x.col[2] + 20 or x.col.min() > 230))]   # 불꽃·수프·김 (따뜻한 색 빛) 빼기
    if o.get("stopped"):
        pass
    return b, o.get("mood", "indoor")


def set_hook(t, p, o):
    def build():
        vx = Voxels()
        vx.fill(-2, 14, 0, 10, -1, 0, "#c9bb98", 16)
        vx.fill(-2, 14, -1, 0, -1, 6, "#8a6141", 14)
        return vx.boxes()
    if o.get("ruin"):   # 지금의 숙소 터: 빛바랜 돌벽, 위는 무너져 하늘이 보임
        def build_r():
            vx = Voxels()
            for x in range(-2, 14):
                top = 10 - (abs(x - 3) % 4) - (3 if x > 8 else 0)
                for y in range(0, top):
                    vx.put(x, y, -1, "#9a9283", j=18)
            vx.fill(-2, 14, -1, 0, -1, 6, "#6f6a62", 14)
            return vx.boxes()
        b = list(_static("hookruin", build_r))
        b.append(Box((2, 7, 0), (8, 0.5, 0.6), "#5a4a3a"))
        for k in range(3):
            b.append(Box((3.2 + k * 2.6, 6.3, 0.2), (0.3, 0.8, 0.5), "#5a4636"))
        if o.get("hand"):   # 위에서 내려온 손이 심지를 옷걸이 위에 올려놓음
            q = min(1.0, p * 2.2)
            y = 9.5 - 2.0 * q
            b += [Box((5.5, y + 0.4, 0.5), (0.9, 2.0, 0.7), "#4e5b3a"), Box((5.55, y - 0.2, 0.55), (0.8, 0.65, 0.6), "#f6d3b3"),
                  Box((5.35, y - 0.45, 0.55), (1.2, 0.25, 0.3), "#f1e6c8")]
        elif o.get("wick"):
            b.append(Box((5.35, 7.5, 0.55), (1.2, 0.25, 0.3), "#f1e6c8"))
        return b, o.get("mood", "grey")
    b = list(_static("hookwall", build))
    b.append(Box((2, 7, 0), (8, 0.5, 0.6), "#6b4a30"))
    for k in range(3):
        b.append(Box((3.2 + k * 2.6, 6.3, 0.2), (0.3, 0.8, 0.5), "#3b3b3b"))
    if o.get("coat", True):
        sway = 3 * math.sin(t * 1.3)
        piv = np.array([5.95, 6.6, 0.4])
        R_ = [(piv, "z", sway)]
        b += [Box((4.75, 1.4, 0.3), (2.4, 4.6, 0.6), "#2e3b4f", R_),                       # 몸판
              Box((4.4, 5.3, 0.3), (3.1, 0.8, 0.6), "#2e3b4f", R_),                         # 어깨
              Box((4.1, 2.6, 0.32), (0.55, 3.2, 0.55), "#283447", R_), Box((7.35, 2.6, 0.32), (0.55, 3.2, 0.55), "#283447", R_),   # 늘어진 소매
              Box((5.35, 5.5, 0.92), (0.6, 0.7, 0.06), "#1e2836", R_), Box((6.05, 5.5, 0.92), (0.6, 0.7, 0.06), "#1e2836", R_),   # 깃
              Box((5.93, 1.5, 0.91), (0.06, 4.0, 0.03), "#1a2230", R_, edge=False)]                                           # 여밈선
        for k in range(4):
            b.append(Box((6.15, 4.6 - k * 0.9, 0.92), (0.16, 0.16, 0.05), "#c9b25a", R_, edge=False))                          # 단추
        b.append(Box((5.85, 6.0, 0.4), (0.3, 0.5, 0.3), "#2e3b4f", R_))                                                        # 걸이 고리
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
    b = sea_tiles(t, mood, -40, 50, -40, 0, rough=1.6 if mood == "storm" else 1.0) + list(_static("rocks", build))
    if o.get("island"):   # 먼바다의 섬 (섬 블록을 바다 저편으로 옮겨 놓음)
        off = np.array(o.get("island_at", [0, 0, -46]), float)
        def far():
            return [Box(x.p + off, x.s, x.col, x.rots, x.emit, x.skip, x.edge) for x in island_vox()]
        b += _static(("farisland", tuple(off)), far)
        cx, cz, top = 8 + off[0], -14 + off[2], 8
        if o.get("lamp", "beam") != "off":
            b.append(Box((cx - 1, top + 10, cz - 2), (3, 1, 3), "#fff1a8", emit=True, edge=False))
            if o.get("lamp", "beam") == "beam":
                piv = np.array([cx, top + 10.5, cz - 0.5])
                b.append(Box((cx + 1.6, top + 10.2, cz - 0.8), (60, 0.6, 0.6), (255, 244, 194), [(piv, "y", t * 40)], emit=True, edge=False))
    return b, mood


def rock_height(x, z):
    """바위 해안 높이: 뒤(바다 쪽, z<3)는 울퉁불퉁, 인물이 서는 가운데(3~8)는 평평한 1, 카메라 쪽(z>8)은 낮게"""
    if z > 8:
        return 0
    if z >= 3:
        return 1
    return max(1, int(1.6 + 1.5 * math.sin(x * 0.4) * math.cos(z * 0.7)))


def set_plain(t, p, o):
    return [], o.get("mood", "plain")




# ───────────────────────── 등대 꼭대기 렌즈실 ─────────────────────────
def lens_boxes(t, p, light):
    """가운데 받침 + 겹겹의 유리 렌즈(빛) + 돌아가는 빛줄기"""
    dim = 1.0
    if light == "dim":
        dim = max(0.0, 1 - p * 1.1)
    elif light == "flicker":
        dim = 0.55 + 0.45 * abs(math.sin(t * 9)) * (0.5 + 0.5 * math.sin(t * 2.3))
    elif light == "off":
        dim = 0.0
    b = [Box((-1.4, 0, -1.4), (2.8, 1.6, 2.8), "#6b4a30"), Box((-1.7, 1.6, -1.7), (3.4, 0.25, 3.4), "#b08d3a")]
    glass = np.array([150, 200, 212], float)
    glow = np.array([255, 241, 168], float)
    for k in range(7):   # 아래·위로 갈수록 좁아지는 유리 고리 + 고리 사이 놋쇠 테
        y = 1.85 + k * 0.55
        w = 2.6 - abs(k - 3) * 0.35
        col = glass * (1 - 0.85 * dim) + glow * 0.85 * dim
        b.append(Box((-w / 2, y, -w / 2), (w, 0.44, w), np.clip(col, 0, 255), emit=dim > 0.05, edge=True))
        b.append(Box((-w / 2 - 0.04, y + 0.44, -w / 2 - 0.04), (w + 0.08, 0.1, w + 0.08), "#b08d3a"))
    b.append(Box((-0.9, 5.7, -0.9), (1.8, 0.5, 1.8), "#b08d3a"))   # 렌즈 꼭대기 놋쇠 뚜껑
    if dim > 0.05:
        b.append(Box((-0.5, 3.2, -0.5), (1.0, 1.0, 1.0), (255, 255, 235), emit=True, edge=False))
        a = t * 35
        piv = np.array([0, 3.7, 0])
        b.append(Box((8.6, 3.45, -0.25), (60, 0.5 * dim + 0.1, 0.5), (255, 244, 194), [(piv, "y", a)], emit=True, edge=False))   # 빛줄기는 유리창 밖부터
    return b


def set_lantern(t, p, o):
    mood = o.get("mood", "night")
    def build():
        vx = Voxels()
        vx.fill(-8, 8, -1, 0, -8, 8, "#3a3b40", 8)              # 쇠 바닥
        for x in range(-8, 8):                                   # 낮은 둘레 벽 (뒤·옆)
            vx.put(x, 0, -8, "#2f3034", j=4)
        for z in range(-8, 8):
            vx.put(-8, 0, z, "#2f3034", j=4)
            vx.put(7, 0, z, "#2f3034", j=4)
        vx.fill(-8, 8, 8, 9, -8, 8, "#2a2b2f", 6)               # 지붕
        return vx.boxes()
    b = list(_static("lantern", build))
    for (x, z) in [(-8, -8), (-2.7, -8), (2.6, -8), (7.7, -8), (-8, -2.7), (-8, 2.6), (7.7, -2.7), (7.7, 2.6), (-8, 7.7), (7.7, 7.7)]:
        b.append(Box((x, 1, z), (0.3, 7, 0.3), "#24252a"))       # 유리창 틀 기둥
    for y in (1.0, 7.6):
        b += [Box((-8, y, -8), (16, 0.25, 0.25), "#24252a"), Box((-8, y, -8), (0.25, 0.25, 16), "#24252a"), Box((7.75, y, -8), (0.25, 0.25, 16), "#24252a")]
    b += sea_tiles(t, mood, -160, 160, -160, 160, step=10)
    for x in b[-1:]:
        pass
    sea = [x for x in b if x.s[0] == 10]
    for x in sea:          # 바다는 저 아래 (등대 높이)
        x.p[1] -= 30
    if o.get("land"):      # 창밖 아래로 보이는 섬 비탈 (서쪽 +x 로 내려감)
        for x in range(8, 70, 4):
            for z in range(-24, 24, 4):
                h = -10 - (x - 8) * 0.18
                b.append(Box((x, h - 4, z), (4, 4, 4), E.jitter(E.hexrgb("#5f8a4a"), (x, z), 14), skip=(0, 2, 5)))
        for x in range(8, 70, 2):
            b.append(Box((x, -10 - (x - 8) * 0.18 + 0.02, -1), (2, 0.1, 2), "#9a9c9e", edge=False))   # 서쪽 선착장으로 가는 길
    b += lens_boxes(t, p, o.get("light", "on"))
    if o.get("wick"):      # 맥아더 손의 새 심지
        pass
    return b, mood


def set_wave(t, p, o):
    """서쪽 절벽에 부딪쳐 솟구치는 거대한 파도 (p 0→1: 솟아올라 덮침)"""
    mood = "storm"
    def build():
        vx = Voxels()
        for x in range(6, 40):
            for z in range(-30, 30):
                h = 10 + int(2 * math.sin(z * 0.5) + (x - 6) * 0.15)
                for y in range(-1, h):
                    vx.put(x, y, z, "#3f453c" if y < h - 1 else "#4f5a46", j=12)
        return vx.boxes()
    b = sea_tiles(t, mood, -80, 6, -60, 60, rough=2.2) + list(_static("wavecliff", build))
    q = min(1.0, p * 1.15)
    H = (22 * math.sin(math.pi * q) if q < 0.5 else 22 * (1 - 0.45 * (q - 0.5) / 0.5)) if not o.get("silhouette") else 18   # 솟았다가 절벽을 덮친 채로
    front = -24 + 30 * min(1.0, q * 1.2)
    col = E.hexrgb("#4f7d97")
    for z in range(-14, 14, 2):
        for k in range(8):   # 파도 앞면에서 뒤로 갈수록 낮아지는 물기둥
            x = front - k * 3
            hh = max(0.5, H * (1 - k / 8) * (0.85 + 0.15 * math.sin(z * 0.7 + t)))
            b.append(Box((x, -1, z), (3, hh + 1, 2), np.clip(col * (0.9 + 0.08 * k), 0, 255), skip=(2, 5)))
        b.append(Box((front - 1, H * (0.85 + 0.15 * math.sin(z * 0.7 + t)) - 0.5, z), (3.5, 1.2, 2), (235, 242, 246), edge=False))   # 흰 물마루
    if q > 0.45 and not o.get("silhouette"):   # 절벽에 부딪쳐 튀는 물보라
        for k in range(40):
            a = ((t * 0.9 + k * 0.137) % 1)
            sx = 5 - 8 * a * math.cos(k)
            sy = 8 + 20 * a + 3 * math.sin(k * 3)
            sz = -12 + (k * 7 % 24)
            sz_ = 0.6 + 1.4 * (1 - a)
            b.append(Box((sx, sy, sz), (sz_, sz_, sz_), (240, 246, 250), emit=True, edge=False))
    if o.get("silhouette"):   # 바위 끝, 서로 팔을 붙잡은 세 사람의 그림자
        for k in range(3):   # 절벽 끝에 선 세 사람 (얼굴 없는 검은 그림자, 사람 키 크기)
            z0 = -1.8 + k * 1.5
            zi = int(math.floor(z0 + 0.35))
            top = 10 + int(2 * math.sin(zi * 0.5) + (7 - 6) * 0.15)   # 그 사람이 선 칸의 땅 높이 (떠 있지 않게)
            b += [Box((7.2, top + 0.0, z0), (0.9, 2.2, 0.7), (14, 14, 18), edge=False), Box((7.25, top + 2.2, z0 + 0.05), (0.8, 0.8, 0.6), (14, 14, 18), edge=False),
                  Box((7.3, top + 1.5, z0 + 0.6), (0.6, 0.25, 1.0), (14, 14, 18), edge=False)]   # 옆 사람 팔을 붙잡은 팔
    return b, mood


def set_landing(t, p, o):
    """서쪽 선착장: 젖은 돌 계단·둑, 쇠 난간(bent 면 휘어짐), 거친 바다"""
    mood = o.get("mood", "storm")
    def build():
        vx = Voxels()
        for x in range(-4, 20):
            for z in range(-6, 8):
                h = 3 if x < 8 else 3 + (x - 8) // 2
                for y in range(-1, min(h, 9)):
                    vx.put(x, y, z, "#7b7e80" if y == h - 1 else "#5b5e60", j=12)
        return vx.boxes()
    b = sea_tiles(t, mood, -80, -4, -60, 40, rough=2.0) + list(_static("landing", build))
    for k in range(6):
        x = -2 + k * 2
        lean = (k - 1) * 12 if o.get("bent") and k >= 2 else 0
        piv = np.array([x, 3, 6.5])
        b.append(Box((x, 3, 6.4), (0.25, 2.2, 0.25), "#3b3b3b", [(piv, "z", lean)]))
        if k < 5:
            ang = 0 if not (o.get("bent") and k >= 1) else -10 - k * 6
            b.append(Box((x, 4.9, 6.45), (2.1, 0.18, 0.18), "#3b3b3b", [(np.array([x, 5.0, 6.5]), "z", ang)]))
    if o.get("wet"):
        for k in range(12):
            b.append(Box((-3 + k * 1.7, 3.02, -5 + (k * 5 % 12)), (1.2, 0.03, 0.8), (150, 170, 185), emit=True, edge=False))   # 물웅덩이
    return b, mood


def set_island_swell(t, p, o):
    b, mood = set_island(t, p, o)
    if o.get("swell"):   # 먼바다 수평선이 부풀어 오름
        h = 1 + 9 * p
        sea_c = E.hexrgb(MOOD[mood][2])
        for x in range(-70, 80, 2):   # 둥글게 이어진 물결 언덕 (가운데가 가장 높음, 양 끝은 활처럼 앞으로 휨)
            hh = h * math.exp(-((x - 5) / 38) ** 2)
            z = -72
            b.append(Box((x, -1, z), (2.05, hh + 1, 8), sea_c * 1.05, skip=(2, 3, 5), edge=False))   # 한 색으로 이어진 물결 언덕
    return b, mood


SETS = {"island": set_island_swell, "stairs": set_stairs, "kitchen": set_kitchen, "hook": set_hook, "rocks": set_rocks, "plain": set_plain,
        "lantern": set_lantern, "wave": set_wave, "landing": set_landing}


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
    if "stir" in acts:   # 팔을 냄비 높이로 들고 국자를 휘휘
        p["arm"] = 108 + 8 * math.sin(t * 2 * math.pi / 1.4)
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
    if "sit" in acts:
        p["sit"] = True
    return p


def build(scene, cast, t, dur=None):
    """장면의 t 초 모습을 상자 목록·카메라로 (검수 프로그램 입체애니_검수.py 도 씀)
    돌려줌: {"boxes", "cam", "mood", "o", "fx", "pr", "chars": [{"who", "pos": (x, y, z), "face", "acts", "i0", "i1", "talk"}]}"""
    dur = dur or scene.get("dur", 8.0)
    pr = min(1.0, max(0.0, t / max(0.1, dur)))
    o = scene.get("opt", {})
    boxes, mood = SETS[scene.get("set", "plain")](t, pr, o)
    boxes = list(boxes)
    info = []
    for m_ in scene.get("extra", {}).get("moai", []):   # 장면에 더 둘 모아이 [x, z, 얼굴 방향, 크기, 누움]
        boxes += moai(m_[0], m_[1], yaw=m_[2], sc=m_[3], lying=len(m_) > 4 and m_[4])
    if scene.get("set") in ("walk", "walk_dio"):   # 줄 끝에 팀 사람들 (모아이 쪽 반대로 몸을 젖히고 당김)
        ends, tilt = o["_ends"], o.get("_tilt", 0)
        for side, whos in o.get("teams", {}).items():
            e = ends[side]
            away = e - np.array([o.get("start", -6) + (o.get("end", 6) - o.get("start", -6)) * (pr if o.get("walk", True) else 0), e[1], o.get("mz", 0)])
            away[1] = 0
            away = away / (np.linalg.norm(away) + 1e-9)
            face = math.degrees(math.atan2(-away[0], -away[2]))   # 모아이를 마주 봄 (줄다리기)
            pulling = (side == "left" and tilt > 2) or (side == "right" and tilt < -2) or side == "back"
            for k, who in enumerate(whos):
                pos = e + away * (0.9 + k * 1.5) + np.array([0.6 * (k % 2) - 0.3, 0, 0])
                ps = pose3d(["blink", "breath", "talk" if o.get("sing") else "breath"], t, k * 1.3 + len(side))
                ps["arm"] = 62 if pulling else 75             # 줄을 쥔 두 팔은 앞(모아이 쪽)으로, 당길 때 몸쪽으로 끌어당김
                ps["arm2"] = ps["arm"]
                ps["bob"] = -0.15 if pulling else 0.0         # 당길 때 몸을 낮춤
                c = cast[who]
                i0 = len(boxes)
                boxes += person(c, (pos[0], 0, pos[2]), face=face, pose=ps)
                info.append({"who": who, "pos": (pos[0], 0, pos[2]), "face": face, "acts": ["team"], "i0": i0, "i1": len(boxes), "scale": 1.0, "exit": False})
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
        if y is None or (scene.get("set") == "stairs" and "y_to" in ch):
            st_ = scene.get("set")
            y = (rock_height(int(ax), int(az)) if st_ == "rocks" else stair_h(int(round(ax))) if st_ == "stairs"
                 else quarry_h(ax, az) if st_ == "quarry" else 0)
            ch = {k_: v_ for k_, v_ in ch.items() if k_ != "y_to"}
        if ch.get("y_to") is not None:
            y = y + (ch["y_to"] - y) * min(1.0, pr * ch.get("speed", 1.0))
        if scene.get("set") == "lantern" and o.get("land") and ax >= 8:   # 창밖 비탈: 그 자리 땅 높이에 (묻히거나 뜨지 않게)
            y = -10 - (8 + int((ax - 8) // 4) * 4 - 8) * 0.18
        ps = pose3d(acts, t, i * 1.7 + 0.3)
        if "stir" in acts:
            ps["ladle"] = True
        if ch.get("hold"):
            ps["hold"] = ch["hold"]
        i0 = len(boxes)
        boxes += person(c, (ax, y, az), face=face, pose=ps, scale=ch.get("scale", 1.0))
        info.append({"who": ch["who"], "pos": (ax, y, az), "face": face, "acts": acts, "i0": i0, "i1": len(boxes), "scale": ch.get("scale", 1.0), "exit": ch.get("exit", False)})
    fx = scene.get("fx", [])
    if "rain" in fx:
        cp = scene["cam"]["pos"]
        for k in range(90):
            rx = cp[0] - 14 + (k * 37 % 28)
            rz = cp[2] - 22 + (k * 53 % 18)
            ry = 14 - ((t * 18 + k * 1.37) % 16)
            boxes.append(Box((rx, ry, rz), (0.05, 0.7, 0.05), (200, 214, 228), emit=True, edge=False))
    cm = scene.get("cam", {"pos": [12, 6, 24], "look": [12, 3, 0]})
    ease = 0.5 - 0.5 * math.cos(math.pi * pr)
    mv = np.array(cm.get("move", [0, 0, 0]), float) * ease
    cpos, clook = np.array(cm.get("pos", [0, 6, 20]), float) + mv, np.array(cm.get("look", cm.get("target", [0, 3, 0])), float) + mv * cm.get("look_follow", 1.0)
    if cm.get("mode") in ("orbit", "follow"):
        # orbit: 대상 둘레를 a0→a1 도 돌며 촬영 / follow: 걷는 모아이(o["_mx"])를 따라가며 돌기
        tgt = np.array(cm.get("target", clook), float)
        if cm["mode"] == "follow" and "_mx" in o:
            tgt = np.array([o["_mx"], tgt[1], o.get("mz", 0)], float)
        ang = math.radians(cm.get("a0", 0) + (cm.get("a1", 40) - cm.get("a0", 0)) * ease)
        rad = cm.get("r0", 20) + (cm.get("r1", cm.get("r0", 20)) - cm.get("r0", 20)) * ease
        hgt = cm.get("h0", 6) + (cm.get("h1", cm.get("h0", 6)) - cm.get("h0", 6)) * ease   # 크레인: 높이가 바뀜
        cpos = tgt + np.array([rad * math.sin(ang), hgt - tgt[1], rad * math.cos(ang)])
        clook = tgt
    if cm.get("hand"):   # 손에 든 카메라처럼 아주 약하게 흔들림
        a_ = cm["hand"]
        cpos = cpos + a_ * np.array([math.sin(t * 1.3), 0.6 * math.sin(t * 1.7 + 1), 0.5 * math.sin(t * 0.9 + 2)])
    if cm.get("shake") and "_tilt" in o and o.get("walk", True):   # 모아이가 한 걸음 디딜 때마다 쿵
        per = o.get("period", 2.4) / 2
        dt_ = t % per
        sh_ = cm["shake"] * math.exp(-dt_ * 7) * math.sin(dt_ * 45)
        cpos = cpos + np.array([0, sh_, 0])
        clook = clook + np.array([0, sh_ * 0.6, 0])
    cam = Camera(cpos, clook, fov=cm.get("fov", 40))
    return {"boxes": boxes, "cam": cam, "mood": mood, "o": o, "fx": fx, "pr": pr, "chars": info}


def frame(scene, cast, t, dur=None):
    """장면의 t 초 그림 (PIL, 1920×1080)"""
    B_ = build(scene, cast, t, dur)
    boxes, cam, mood, o, fx, pr = B_["boxes"], B_["cam"], B_["mood"], B_["o"], B_["fx"], B_["pr"]
    md = MOOD.get(mood)
    tex = scene.get("tex", 0.0)
    if md:
        img = E.render(boxes, cam, sky=(md[0], md[1]), tex=tex)
    elif mood == "plain":
        a, b = o.get("c1", (43, 58, 82)), o.get("c2", (122, 143, 168))
        img = E.render(boxes, cam, sky=(b, a), tex=tex)
    else:
        img = E.render(boxes, cam, bg=(40, 36, 34), tex=tex)
    if scene.get("style") == "diorama":
        img = diorama(img, scene.get("focus", 0.55))
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


def diorama(img, focus=0.55):
    """작은 모형 세상처럼: 위·아래를 살짝 흐리게(초점은 focus 높이의 가로 띠), 색을 조금 더 또렷하게, 가장자리를 살짝 어둡게"""
    from PIL import ImageEnhance, ImageFilter
    blur = img.filter(ImageFilter.GaussianBlur(4))
    h = img.height
    ys = np.arange(h) / h
    m = np.clip((np.abs(ys - focus) - 0.18) / 0.3, 0, 1) ** 1.3
    mask = Image.fromarray((np.repeat(m[:, None], img.width, 1) * 255).astype(np.uint8))
    out = Image.composite(blur, img, mask)
    out = ImageEnhance.Color(out).enhance(1.18)
    out = ImageEnhance.Contrast(out).enhance(1.05)
    xs = (np.arange(img.width) / img.width - 0.5) * 2
    vig = 1 - 0.18 * np.clip(((ys - 0.5) * 2)[:, None] ** 2 + xs[None, :] ** 2 - 0.4, 0, 1)
    arr = np.asarray(out).astype(np.float32) * vig[..., None]
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


def load(scene_path):
    scene = json.load(open(scene_path, encoding="utf-8"))
    cp = scene["cast"] if os.path.isabs(scene["cast"]) else os.path.join(os.path.dirname(scene_path), scene["cast"])
    cast = {c["name"]: c for c in json.load(open(cp, encoding="utf-8"))["chars"]}
    return scene, cast




# ═════════════════════ 모아이 편 (온 가족, 2026-11-05) ═════════════════════
TUFF = "#8c8170"


def rope(a, b, col="#c8a46a", w=0.09):
    """두 점을 잇는 밧줄 (얇은 상자를 방향에 맞게 돌림)"""
    a, b = np.array(a, float), np.array(b, float)
    d = b - a
    L = float(np.linalg.norm(d))
    if L < 1e-6:
        return []
    hz = math.hypot(d[0], d[2])
    el = math.degrees(math.atan2(d[1], hz))
    yaw = math.degrees(math.atan2(-d[2], d[0]))
    return [Box((a[0], a[1] - w / 2, a[2] - w / 2), (L, w, w), col, [(a, "z", el), (a, "y", yaw)], edge=False)]


def moai(x, z, yaw=0.0, sc=1.0, tilt=0.0, lying=False, pukao=False, col=TUFF, unfinished=False):
    """블록 모아이 (발 가운데 = x,z, 높이 약 8·sc). yaw = 얼굴 방향(0 = +z), tilt = 좌우로 기운 각도(+ = 왼쪽으로, 아래 모서리를 축으로)"""
    parts = []
    def P(px, py, pz, w, h, d, c=None):
        parts.append(((px * sc, py * sc, pz * sc), (w * sc, h * sc, d * sc), c or col))
    P(-1.2, 0, -0.8, 2.4, 3.6, 1.6)                 # 몸통
    P(-1.1, 0.3, 0.8, 2.2, 1.6, 0.35)               # 둥근 배 (앞으로 볼록)
    P(-1.05, 3.6, -0.75, 2.1, 3.2, 1.7)             # 머리 (앞으로 살짝)
    P(-1.1, 5.9, -0.75, 2.2, 0.45, 2.05)            # 튀어나온 이마
    P(-0.25, 4.3, 0.95, 0.5, 1.7, 0.45)             # 긴 코
    P(-0.55, 3.9, 0.9, 1.1, 0.3, 0.25)              # 입술
    P(-1.0, 3.5, 0.6, 2.0, 0.4, 0.4)                # 턱
    for sg in (-1, 1):
        P(sg * 1.05 - (0.25 if sg < 0 else 0), 3.9, -0.3, 0.25, 2.3, 0.6)      # 긴 귀
        P(sg * 0.55 - 0.25, 5.2, 0.9, 0.5, 0.55, 0.12, "#4a443b")               # 이마 밑 그늘진 눈
        P(sg * 0.75 - 0.2, 0.9, 0.85, 0.4, 0.25, 0.4)                            # 배 위 손 (손가락이 배꼽 쪽으로)
        P(sg * 0.35 - 0.3 + (0.2 if sg < 0 else -0.1), 0.85, 1.12, 0.5, 0.15, 0.12)
    if pukao:
        P(-0.9, 6.8, -0.6, 1.8, 1.0, 1.6, "#9b4a35")   # 붉은 돌 모자 (푸카오)
    out = []
    base = np.array([x, 0, z], float)
    for (p, s_, c) in parts:
        jit = E.jitter(E.hexrgb(c), (round(p[0], 2), round(p[1], 2), x, z), 8)
        rots = []
        if lying:   # 등을 대고 누움 (얼굴이 하늘)
            rots.append((base, "x", -90))
        if tilt:
            piv = base + np.array([(-1.2 if tilt > 0 else 1.2) * sc, 0, 0])
            rots.append((piv, "z", tilt))
        if yaw:
            rots.append((base, "y", yaw))
        out.append(Box(base + np.array(p), s_, jit if not unfinished else jit * 0.92, rots, skip=()))
    return out


def grass_field(key, x0=-40, x1=50, z0=-40, z1=30, h=lambda x, z: 0, step=2, col="#6f9a4e", side="#6f6a62"):
    def build():
        out = []
        for x in range(x0, x1, step):
            for z in range(z0, z1, step):
                hh = h(x, z)
                out.append(Box((x, hh - step, z), (step, step, step), E.jitter(E.hexrgb(col), (x, z), 14), skip=(5,)))
        return out
    return list(_static(key, build))


def set_rapanui(t, p, o):
    """섬 전체: 바다 한가운데 초록 섬, 화산 분화구(채석장), 바닷가의 작은 모아이 줄"""
    mood = o.get("mood", "day")
    def build():
        vx = Voxels()
        for x in range(-34, 36):
            for z in range(-26, 26):
                d = math.hypot(x / 32, z / 22)
                if d > 1:
                    continue
                h = int(2 + 3 * (1 - d) + 2 * math.sin(x * 0.2) * math.cos(z * 0.25))
                vd = math.hypot((x - 18) / 8, (z + 8) / 8)            # 화산 (라노 라라쿠, 돌 비탈)
                if vd < 1:
                    h += int(13 * (1 - vd))
                    if vd < 0.35:
                        h -= 3                                        # 분화구
                for y in range(-1, max(1, h)):
                    vx.put(x, y, z, ("#5f8a4a" if vd >= 0.75 else TUFF) if y == max(1, h) - 1 else "#6f6a62", j=12)
        return vx.boxes()
    sea = [x for x in sea_tiles(t, mood, -120, 120, -100, 80, step=6) if math.hypot((x.p[0] + 3) / 38, (x.p[2] + 3) / 28) > 1]
    b = sea + list(_static("rapanui", build))
    for k in range(7):   # 바닷가의 모아이 줄 (작게)
        b += moai(-20 + k * 1.6, 15, yaw=180, sc=0.25, pukao=k % 2 == 0)
    if o.get("road"):
        for k in range(40):
            q = k / 39
            x, z = 18 - 38 * q, -8 + 23 * q + 3 * math.sin(q * 6)
            b.append(Box((x, 3.05 + 2 * (1 - q), z), (1.2, 0.06, 1.2), "#b8a888", edge=False))
    return b, mood


def set_ahu(t, p, o):
    """바닷가 돌 단(아후) 위에 바다를 등지고 선 모아이들"""
    mood = o.get("mood", "day")
    b = sea_tiles(t, mood, -80, 80, -80, -8, rough=0.8) + grass_field("ahu_grass", -60, 60, -8, 40)
    def plat():
        vx = Voxels()
        vx.fill(-14, 14, 0, 2, -6, -1, "#7d776c", 12)
        return vx.boxes()
    b += list(_static("ahu", plat))
    n = o.get("n", 7)
    for k in range(n):
        if o.get("missing") == k:
            continue
        b += moai(-12 + k * 4, -3.5, yaw=0, sc=o.get("sc", 0.9), pukao=k % 2 == 0)
    for bb in b[-n * 20:]:
        pass
    return [x if x.p[1] >= 0 or x.s[0] > 3 else x for x in b], mood


def set_field(t, p, o):
    """나무 없는 풀밭 + 누워 있는(쓰러진) 모아이, 가운데 오목한 옛길(road)"""
    mood = o.get("mood", "day")
    road = o.get("road", False)
    def h(x, z):
        if road and -2 <= z < 2:
            return -0.5 if -1 <= z < 1 else -0.25
        return 0
    b = sea_tiles(t, mood, -120, 120, -120, -40, step=6) + grass_field(("field", road), -60, 60, -40, 30, h=h, step=1 if road else 2)
    if road:
        for x in range(-60, 60, 1):
            b.append(Box((x, -0.49, -1), (1, 0.02, 2), E.jitter(E.hexrgb("#b8a888"), (x, 9), 10), edge=False))
    for (x, z, yw) in o.get("fallen", []):
        b += [bx for bx in moai(x, z, yaw=yw, sc=0.8, lying=True)]
    return b, mood


def quarry_h(x, z):
    """채석장 땅 높이 (블록 윗면)"""
    return max(1, int((-math.floor(z)) * 0.55 + 1.5 * math.sin(math.floor(x) * 0.3)))


def set_quarry(t, p, o):
    """화산 채석장: 회갈색 돌 비탈에 깎다 만 모아이들이 누워 있음"""
    mood = o.get("mood", "day")
    def build():
        vx = Voxels()
        for x in range(-30, 30):
            for z in range(-30, 12):
                h = quarry_h(x, z)
                for y in range(-1, h):
                    top = y == h - 1
                    vx.put(x, y, z, ("#5f8a4a" if (x * 5 + z * 3) % 4 == 0 or z > 4 else TUFF) if top else TUFF, j=14)
        return vx.boxes()
    b = sea_tiles(t, mood, -100, 100, 12, 80, step=6) + list(_static("quarry", build))
    for (x, z) in o.get("carving", [(-12, -14), (6, -18), (16, -10)]):   # 비탈에 누운 깎는 중인 모아이
        hh = quarry_h(x, z)
        b += [Box(bx.p + np.array([0, hh + 0.1, 0]), bx.s, bx.col, [(np.array([x, hh + 0.1, z]), "x", -70)], skip=()) for bx in moai(x, z, sc=0.9, unfinished=True)]
    return b, mood


def walking_moai(t, p, o):
    """걷는 모아이 + 줄 세 개 + 당기는 팀 (o: start, end, sc, teams, road)"""
    x0, x1 = o.get("start", -6), o.get("end", 6)
    z = o.get("mz", 0)
    sc = o.get("msc", 0.9)
    per = o.get("period", 2.4)          # 왼쪽·오른쪽 한 번씩 = 두 걸음
    ph = 2 * math.pi * t / per
    tilt = 9 * math.sin(ph)
    q = p if o.get("walk", True) else 0.0
    mx = x0 + (x1 - x0) * q
    yaw = 90 + 7 * math.cos(ph)         # 걸음마다 살짝 돌아감 (+x 쪽을 봄)
    b = moai(mx, z, yaw=yaw, sc=sc, tilt=tilt if o.get("walk", True) else 0)
    head = np.array([mx, 6.0 * sc, z])
    pulls = o.get("pulls", ("left", "right", "back"))
    hand_y = 2.3                         # 사람 손 높이
    ends = {"left": np.array([mx + 1.5 * sc, hand_y, z - 4.5 * sc]), "right": np.array([mx + 1.5 * sc, hand_y, z + 4.5 * sc]), "back": np.array([mx - 6 * sc, hand_y, z])}
    cols = {"left": "#c0392b", "right": "#2f6fb0", "back": "#2f8a4f"}
    for k_ in pulls:
        tight = ((k_ == "left" and tilt > 2) or (k_ == "right" and tilt < -2) or k_ == "back")
        e = ends[k_] + (np.array([0, 0.3, 0]) if not tight else 0)
        b += rope(head + np.array([0, 0, -0.8 * sc if k_ == "left" else (0.8 * sc if k_ == "right" else 0)]), e, cols[k_] if o.get("team_rope_col") else "#c8a46a")
    return b, ends, mx, tilt


def set_walk(t, p, o):
    """걷는 모아이 장면: 들판(또는 오목한 옛길·바닷가) 위 + 모아이 + 줄 (팀 사람들은 build 가 줄 끝에 세움)"""
    base_set = o.get("base", "field")
    b, mood = (set_field if base_set == "field" else set_ahu)(t, p, o)
    mb, ends, mx, tilt = walking_moai(t, p, o)
    o["_ends"], o["_tilt"], o["_mx"] = ends, tilt, mx
    return b + mb, mood


SETS.update({"rapanui": set_rapanui, "ahu": set_ahu, "field": set_field, "quarry": set_quarry, "walk": set_walk})



def diorama_base(key, x0, x1, z0, z1, depth=5, water=None, road=False):
    """디오라마 땅 조각: 네모나게 자른 땅 (위 풀, 옆으로 흙·돌 층이 보임). water=(x0,x1,z0,z1) 은 그 안을 물로"""
    def build():
        vx = Voxels()
        for x in range(x0, x1):
            for z in range(z0, z1):
                wet = water and water[0] <= x < water[1] and water[2] <= z < water[3]
                top = -1 if wet else 0
                for y in range(-depth, top):
                    col = ("#6f9a4e" if y == top - 1 else "#8a6141" if y >= -2 else "#6f6a62")
                    if wet:
                        col = "#c9b98f" if y == top - 1 else "#8a6141" if y >= -2 else "#6f6a62"   # 물 아래 모래
                    vx.put(x, y, z, col, j=12)
                if road and -1 <= z < 1 and not wet:
                    vx.v.pop((x, -1, z), None)
                    vx.put(x, -2, z, "#b8a888", j=8)
        return vx.boxes()
    b = list(_static(("diorama", key), build))
    if water:
        b.append(Box((water[0], -1.35, water[2]), (water[1] - water[0], 0.3, water[3] - water[2]), (70, 140, 190), emit=False, edge=False))
    return b


def set_walk_dio(t, p, o):
    """디오라마풍 걷는 모아이: 네모난 땅 조각 위 (한쪽 끝은 바닷물)"""
    b = diorama_base("walk", -30, 22, -16, 16, water=(-30, 22, -16, -11), road=o.get("road", False))
    mb, ends, mx, tilt = walking_moai(t, p, o)
    o["_ends"], o["_tilt"], o["_mx"] = ends, tilt, mx
    return b + mb, o.get("mood", "diorama")


SETS.update({"walk_dio": set_walk_dio})
MOOD["diorama"] = ((206, 222, 232), (246, 238, 222), "#4f86a8", 1.0, None)   # 밝은 작업대 위 같은 하늘색 → 크림색 배경

if __name__ == "__main__":
    a = sys.argv[1:]
    sc, cast = load(a[0])
    t = float(a[a.index("--t") + 1]) if "--t" in a else 1.0
    frame(sc, cast, t, sc.get("dur", 8)).save(a[1])
