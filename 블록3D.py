"""입체 블록 세상 그리기 — GPU 없이 파이썬으로 그리는 작은 3D 블록 엔진 (사용자 결정 2026-11-05: 마인크래프트처럼 입체 블록, 단 그림·인물은 모두 오리지널)
  - 모든 것이 상자(블록): 배경은 1칸짜리 블록을 쌓은 '복셀', 인물은 머리·몸·팔·다리 상자 (인물 설정 = 카툰캐릭터와 같은 등장인물 json)
  - 원근 카메라 + 화가 알고리즘(먼 면부터 그림) + 빛 방향 음영 + 블록마다 살짝 다른 색(질감)
  - python 블록3D.py 부엌 <결과.png|mp4> [--초 6]
"""
import math
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw

W, H = 1920, 1080
SS = 1.5           # 계단 현상 줄이기: 1.5배로 그린 뒤 줄임
LIGHT = np.array([-0.45, 0.85, 0.55])
LIGHT = LIGHT / np.linalg.norm(LIGHT)


def hexrgb(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], float)


def jitter(rgb, key, amt=10):
    """블록마다 색을 살짝 다르게 (같은 자리면 언제나 같은 값)"""
    r = (hash(key) % 1000) / 1000.0 - 0.5
    return np.clip(rgb + r * amt * 2, 0, 255)


# ───────────────────────── 상자 ─────────────────────────
CUBE = np.array([[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0], [0, 0, 1], [1, 0, 1], [1, 1, 1], [0, 1, 1]], float)
FACES = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 4, 7, 3), (1, 2, 6, 5), (3, 7, 6, 2), (0, 1, 5, 4)]   # -z +z -x +x +y -y
FACE_DIR = [(0, 0, -1), (0, 0, 1), (-1, 0, 0), (1, 0, 0), (0, 1, 0), (0, -1, 0)]


def rot(axis, deg):
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    if axis == "x":
        return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])
    if axis == "y":
        return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


class Box:
    """x0,y0,z0 = 가장 작은 꼭짓점, size = (w,h,d). rots = [(pivot(3), axis, deg), ...] 차례로 적용. emit = 스스로 빛남(음영 없음)"""
    __slots__ = ("p", "s", "col", "rots", "emit", "skip", "edge", "bias")

    def __init__(s, p, size, col, rots=None, emit=False, skip=(), edge=True, bias=None):
        s.p, s.s = np.array(p, float), np.array(size, float)
        s.col = hexrgb(col) if isinstance(col, str) else np.array(col, float)
        s.rots, s.emit, s.skip, s.edge = rots or [], emit, skip, edge
        s.bias = bias if bias is not None else (0.3 if not edge else 0.0)   # 얼굴 위 작은 조각(눈·입)은 늘 붙은 면보다 앞에

    def corners(s):
        v = s.p + CUBE * s.s
        for pv, ax, deg in s.rots:
            if deg:
                v = (v - pv) @ rot(ax, deg).T + pv
        return v


class Camera:
    def __init__(s, pos, target, fov=40, ortho=None):
        s.ortho = ortho            # 숫자면 원근 없는 평면 그림 (화면 높이에 들어갈 블록 수)
        s.pos = np.array(pos, float)
        f = np.array(target, float) - s.pos
        s.f = f / np.linalg.norm(f)
        r = np.cross(s.f, [0, 1, 0])
        s.r = r / np.linalg.norm(r)
        s.u = np.cross(s.r, s.f)
        s.focal = (H * SS / 2) / math.tan(math.radians(fov / 2))

    def project(s, pts):
        v = pts - s.pos
        x, y, z = v @ s.r, v @ s.u, v @ s.f
        if s.ortho:
            k = H * SS / s.ortho
            return np.stack([W * SS / 2 + k * x, H * SS / 2 - k * y], 1), z
        z0 = z
        z = np.maximum(z, 0.05)
        return np.stack([W * SS / 2 + s.focal * x / z, H * SS / 2 - s.focal * y / z], 1), z0


def render(boxes, cam, bg=(150, 180, 205), sky=None):
    """상자 목록 → PIL 그림"""
    img = Image.new("RGB", (int(W * SS), int(H * SS)), tuple(int(c) for c in bg))
    dr = ImageDraw.Draw(img)
    if sky is not None:   # 위→아래 하늘 색
        a, b = np.array(sky[0], float), np.array(sky[1], float)
        for k in range(0, int(H * SS), 6):
            q = k / (H * SS)
            dr.rectangle([0, k, W * SS, k + 6], fill=tuple(int(v) for v in a + (b - a) * q))
    polys = []
    for b in boxes:
        v = b.corners()
        scr, depth = cam.project(v)
        for fi, f in enumerate(FACES):
            if fi in b.skip:
                continue
            if not cam.ortho and min(depth[i] for i in f) < 0.12:
                continue                      # 카메라 뒤·바로 앞에 걸친 면은 안 그림 (화면 전체를 덮지 않게)
            p = v[list(f)]
            n = np.cross(p[1] - p[0], p[3] - p[0])
            nn = np.linalg.norm(n)
            if nn < 1e-9:
                continue
            n = n / nn
            c = p.mean(0)
            if np.dot(n, cam.pos - c) <= 0:
                continue                      # 뒤쪽 면은 안 그림
            d = np.linalg.norm(c - cam.pos) - b.bias
            if b.emit:
                col = b.col
            else:
                lum = 0.55 + 0.45 * max(0.0, float(np.dot(n, LIGHT)))
                col = b.col * lum
            polys.append((d, [tuple(scr[i]) for i in f], tuple(int(x) for x in np.clip(col, 0, 255)), b.edge))
    polys.sort(key=lambda t: -t[0])
    for d, pts, col, edge in polys:
        oc = tuple(int(x * 0.72) for x in col) if edge else None
        dr.polygon(pts, fill=col, outline=oc)
    return img.resize((W, H), Image.LANCZOS)


# ───────────────────────── 복셀(배경 블록) ─────────────────────────
class Voxels:
    """1칸 블록 격자. 붙어 있는 면은 안 그려서 빠름"""
    def __init__(s):
        s.v = {}

    def put(s, x, y, z, col, emit=False, j=10):
        s.v[(x, y, z)] = (col, emit, j)

    def fill(s, x0, x1, y0, y1, z0, z1, col, j=10, emit=False):
        for x in range(x0, x1):
            for y in range(y0, y1):
                for z in range(z0, z1):
                    s.put(x, y, z, col, emit, j)

    def boxes(s):
        out = []
        nb = [(0, 0, -1), (0, 0, 1), (-1, 0, 0), (1, 0, 0), (0, 1, 0), (0, -1, 0)]
        for (x, y, z), (col, emit, j) in s.v.items():
            skip = tuple(i for i, (dx, dy, dz) in enumerate(nb) if (x + dx, y + dy, z + dz) in s.v and not s.v[(x + dx, y + dy, z + dz)][1] == emit is False)
            skip = tuple(i for i, (dx, dy, dz) in enumerate(nb) if (x + dx, y + dy, z + dz) in s.v)
            if len(skip) == 6:
                continue
            out.append(Box((x, y, z), (1, 1, 1), jitter(hexrgb(col), (x, y, z), j), emit=emit, skip=skip))
        return out


# ───────────────────────── 인물 (블록 사람) ─────────────────────────
def person(c, pos, face=0.0, pose=None, scale=1.0):
    """등장인물 설정(c) → 상자 목록. pos = 발 가운데 (x,y,z), face = 몸이 보는 방향(도, 0 = 카메라 쪽 +z, 90 = +x 쪽)"""
    pose = pose or {}
    D = {"height": 720, "head": 0.22, "head_w": 0.86, "shoulder": 70, "waist": 58, "hip": 56, "torso": 0.33, "leg_w": 30, "arm_w": 24,
         "skin": "#f2c9a5", "hair": "#2b2b2b", "hair_style": "crew", "top": "#3d5a80", "top_type": "jacket", "bottom": "#55565b",
         "shoes": "#3a2a22", "sig": None, "eyes": "dot", "mouth": "flat", "cap": False, "aviator": False, "coat_len": 0, "beard": False,
         "braces": False, "double": False, "tie": False, "apron": False, "scarf": False, "mustache": False, "glasses": False, "blush": False}
    c = {**D, **c}
    scale = scale * 1.6                                # 방 블록에 비해 사람이 너무 작지 않게
    k = c["height"] / 720 * 3.3 * scale                # 전체 키(블록 단위)
    hs = k * c["head"] * 1.25                          # 머리 한 변
    hwid = hs * c["head_w"] / 0.86
    leg = k * 0.36
    tor = k * c["torso"] * 0.95
    sw = c["shoulder"] / 70 * 0.62 * scale             # 어깨 반폭
    bw = max(c["waist"], c["hip"]) / 70 * 0.62 * scale
    bw = max(bw, sw * 0.9)
    dep = 0.42 * scale + max(0, c["waist"] - c["shoulder"]) / 70 * 0.3
    aw = c["arm_w"] / 24 * 0.3 * scale
    x0, y0, z0 = pos
    bob = pose.get("bob", 0) + pose.get("breath", 0) * 4
    if pose.get("sit"):   # 바닥에 주저앉음: 몸 전체를 내려 엉덩이가 바닥에 닿게 (다리는 아래에서 앞으로 뻗음)
        bob -= k * 0.36 - 0.42
    out = []

    layer = {"b": 0.0}

    def B(p, s, col, rots=(), **kw):
        kw.setdefault("bias", layer["b"] if kw.get("edge", True) else 0.3 + layer["b"])
        out.append(Box((x0 + p[0], y0 + p[1] + bob, z0 + p[2]), s, col, list(rots), **kw))

    wp = pose.get("walk")
    swing = math.degrees(math.sin(wp)) * 0.5 if wp is not None else 0
    # 다리
    lw = bw * 0.95
    for sg in (-1, 1):
        lx = -lw if sg < 0 else 0
        piv = np.array([x0 + lx + lw / 2, y0 + leg + bob, z0])
        r = [(piv, "x", swing * sg)] if not pose.get("sit") else [(piv, "x", -86 + 6 * sg)]
        B((lx + 0.01, 0.16, -dep / 2 + 0.02), (lw - 0.02, leg - 0.16, dep - 0.04), c["bottom"], r)
        B((lx - 0.02, 0, -dep / 2 - 0.02), (lw + 0.0, 0.18, dep + 0.12), c["shoes"], r)
    # 코트 자락
    if c["coat_len"]:
        cl = leg * c["coat_len"] * 1.2
        B((-bw - 0.05, leg - cl, -dep / 2 - 0.04), (bw * 2 + 0.1, cl, dep + 0.08), c["top"])
    # 몸통
    ty = leg
    B((-bw, ty, -dep / 2), (bw * 2, tor * 0.25, dep), c["bottom"] if not c["coat_len"] else c["top"])        # 허리
    B((-sw, ty + tor * 0.22, -dep / 2), (sw * 2, tor * 0.8, dep), c["top"])
    fz = dep / 2                                                                      # 앞면 z
    if c["top_type"] in ("jacket", "uniform", "cardigan"):
        B((-hwid * 0.2, ty + tor * 0.62, fz), (hwid * 0.4, tor * 0.4, 0.02), c.get("shirt", "#f4f1ea"), edge=False)
        if c["tie"]:
            B((-0.06, ty + tor * 0.45, fz + 0.02), (0.12, tor * 0.5, 0.02), c["sig"] or "#b23a3a", edge=False)
        for i in range(3):
            for sx in ((-0.14, 0.1) if c["double"] else (0.06,)):
                B((sx, ty + tor * (0.3 + 0.15 * i), fz), (0.06, 0.06, 0.03), c.get("button", "#d9c27a"), edge=False)
    if c["braces"]:
        for sx in (-sw * 0.6, sw * 0.6 - 0.08):
            B((sx, ty + tor * 0.2, fz), (0.08, tor * 0.82, 0.02), c["sig"] or "#a83232", edge=False)
            B((sx, ty + tor * 0.2, -fz - 0.02), (0.08, tor * 0.82, 0.02), c["sig"] or "#a83232", edge=False)
    if c["apron"]:
        B((-bw * 0.75, ty - leg * 0.4, fz), (bw * 1.5, tor * 0.9 + leg * 0.4, 0.04), c["sig"] or "#c0392b")
    # 팔: 어깨를 축으로 (arm_r/arm_l = 옆으로 들기, arm = 앞으로 들기)
    sy = ty + tor * 1.0
    alen = tor * 0.95
    for sg in (-1, 1):
        ax = sg * sw + (0 if sg > 0 else -aw)
        piv = np.array([x0 + sg * sw + sg * aw / 2 * 0, y0 + sy + bob, z0])
        side = pose.get("arm_r" if sg > 0 else "arm_l", 0)
        fwd = pose.get("arm", 0) if sg > 0 else pose.get("arm2", 0)
        r = [(piv, "x", -(fwd) - swing * sg), (piv, "z", side * sg)]
        B((ax, sy - alen, -aw / 2), (aw, alen, aw), c["top"], r)
        B((ax + 0.01, sy - alen - aw * 0.9, -aw / 2 + 0.01), (aw - 0.02, aw * 0.9, aw - 0.02), c["skin"], r)
        if sg > 0 and pose.get("ladle"):   # 국자: 손에서 아래로 긴 자루 + 끝의 오목한 머리
            hp = np.array([x0 + ax + aw / 2, y0 + bob + sy - alen - aw * 0.5, z0])   # 손 자리: 국자를 팔과 직각으로 꺾어 냄비 안으로
            lr = [(hp, "x", pose.get("ladle_deg", 95))] + r
            B((ax + aw * 0.35, sy - alen - aw * 0.9 - 0.45, -0.04), (0.08, 0.55, 0.08), "#8a8f96", lr)   # 짧은 자루 (끝은 수프 속)
        if sg > 0 and pose.get("hold"):    # 손에 든 물건 (빵 반쪽 등)
            B((ax - 0.05, sy - alen - aw * 1.3, -aw * 0.9), (aw + 0.1, aw * 0.7, aw * 1.4), pose["hold"], r)
    # 목·머리
    hy = sy + 0.05
    B((-hwid * 0.2, sy - 0.05, -0.12), (hwid * 0.4, 0.12, 0.24), c["skin"])
    B((-hwid / 2, hy, -hs / 2), (hwid, hs, hs), c["skin"])
    fz = hs / 2 + 0.005
    ex, ey = hwid * 0.22, hy + hs * 0.48
    eh = 0.03 if pose.get("blink") else hs * 0.16
    for sg in (-1, 1):
        if c["eyes"] == "anime" and not pose.get("blink"):
            B((sg * ex - hs * 0.1, ey - hs * 0.08, fz), (hs * 0.2, hs * 0.22, 0.02), "#ffffff", edge=False)
            B((sg * ex - hs * 0.05, ey - hs * 0.06, fz + 0.01), (hs * 0.1, hs * 0.16, 0.02), c.get("iris", "#3a2a1a"), edge=False)
        else:
            col = "#26221f"
            B((sg * ex - hs * 0.06, ey - (0 if pose.get("blink") else hs * 0.06), fz), (hs * 0.12, eh if not c["eyes"] in ("tired",) else hs * 0.07, 0.02), col, edge=False)
        B((sg * ex - hs * 0.1, ey + hs * 0.16, fz), (hs * 0.2, hs * 0.05 * (1.5 if c["eyes"] in ("sharp", "anime") else 1), 0.02), shade_hex(c["hair"], 0.8) if c["hair_style"] != "bald" else "#26221f", edge=False)
        if c["blush"]:
            B((sg * ex - hs * 0.08 + sg * hs * 0.05, ey - hs * 0.2, fz), (hs * 0.16, hs * 0.07, 0.015), "#f08a7a", edge=False)
    my = hy + hs * 0.18
    layer["b"] = 0.2
    if c["beard"]:
        bc = c["beard"] if isinstance(c["beard"], str) else c["hair"]
        B((-hwid / 2 - 0.02, hy - 0.04, fz - 0.06), (hwid + 0.04, hs * 0.36, 0.1), bc)
        B((-hwid / 2 - 0.02, hy - 0.04, -hs * 0.05), (0.08, hs * 0.42, hs * 0.57), bc)   # 옆 수염은 턱 앞쪽만
        B((hwid / 2 - 0.06, hy - 0.04, -hs * 0.05), (0.08, hs * 0.42, hs * 0.57), bc)
    if c["mustache"]:
        B((-hs * 0.2, my + hs * 0.06, fz + 0.02), (hs * 0.4, hs * 0.07, 0.03), c["hair"] if c["hair_style"] != "bald" else "#9a9a9a", edge=False)
    talk = pose.get("talk", 0)
    mh = hs * (0.05 + 0.12 * talk) if talk > 0.15 else hs * 0.04
    mw = hs * (0.3 if c["mouth"] == "smile" else 0.22)
    B((-mw / 2, my - mh / 2, fz + (0.07 if c["beard"] else 0.01)), (mw, mh, 0.02), "#6b2a24" if talk > 0.15 or c["mouth"] == "smile" else "#26221f", edge=False)
    # 머리카락
    hc, st = c["hair"], c["hair_style"]
    t = hy + hs
    if st == "bald":
        for sg in (-1, 1):
            B((sg * (hwid / 2) - (0.08 if sg < 0 else 0) + (0 if sg < 0 else -0.0), hy + hs * 0.35, -hs / 2), (0.08, hs * 0.35, hs * 0.8), hc)
    else:
        top_h = hs * (0.24 if st != "perm" else 0.3)
        B((-hwid / 2 - 0.04, t - top_h + 0.06, -hs / 2 - 0.04), (hwid + 0.08, top_h, hs + 0.08), hc)
        back_h = hs * (0.9 if st in ("bob", "long") else 0.75)
        if c["aviator"]:   # 비행 모자 밑 머리는 짧게 (뒷머리가 검은 덩어리로 얼굴을 덮지 않게)
            back_h = hs * 0.45
        B((-hwid / 2 - 0.04, t - back_h, -hs / 2 - 0.04), (hwid + 0.08, back_h, 0.12), hc)
        sl = hs * (0.8 if st in ("bob", "long") else 0.45) * (0.6 if c["aviator"] else 1.0)
        for sg in (-1, 1):
            B((sg * hwid / 2 - (0.06 if sg < 0 else -0.02) - (0 if sg < 0 else 0.04), t - sl, -hs / 2 - 0.04), (0.08, sl, hs * (0.75 if st not in ("bob", "long") else 0.95)), hc)
        if st == "long":
            B((-hwid / 2 - 0.04, t - hs * 1.6, -hs / 2 - 0.06), (hwid + 0.08, hs * 0.8, 0.14), hc)
        if st == "spiky" and not c["aviator"]:
            for i in range(5):
                for j in range(3):
                    px = -hwid / 2 + hwid * (i + 0.5) / 5 - 0.07
                    pz = -hs / 2 + hs * (j + 0.5) / 3 - 0.07
                    hh_ = 0.1 + 0.08 * ((i * 7 + j * 3) % 3)
                    B((px, t + 0.06, pz), (0.14, hh_, 0.14), hc)
            for i in range(4):
                B((-hwid / 2 + hwid * (i + 0.5) / 4 - 0.07, t - top_h - 0.06, fz - 0.06), (0.14, 0.14, 0.1), hc)
        if st == "perm":
            for i in range(5):
                for j in range(4):
                    B((-hwid / 2 - 0.08 + (hwid + 0.16) * i / 4 - 0.08, t + 0.02, -hs / 2 + hs * j / 3 - 0.08), (0.18, 0.12, 0.18), hc)
    # 모자
    if c["cap"]:
        cc = c["cap"] if isinstance(c["cap"], str) else (c["sig"] or "#333a55")
        B((-hwid / 2 - 0.06, t - 0.02, -hs / 2 - 0.06), (hwid + 0.12, hs * 0.3, hs + 0.12), cc)
        B((-hwid / 2 - 0.02, t - 0.06, hs / 2), (hwid + 0.04, 0.06, hs * 0.35), shade_hex(cc, 0.5))
        B((-0.06, t + 0.06, hs / 2 + 0.06), (0.12, 0.1, 0.02), "#e3b341", edge=False)
    if c["aviator"]:
        ac = c["aviator"] if isinstance(c["aviator"], str) else "#8a5a32"
        B((-hwid / 2 - 0.06, t - hs * 0.22, -hs / 2 - 0.06), (hwid + 0.12, hs * 0.34, hs + 0.12), ac)
        for sg in (-1, 1):
            B((sg * hwid / 2 - (0.08 if sg < 0 else 0) , hy + hs * 0.5, -hs * 0.36), (0.08, hs * 0.3, hs * 0.3), ac)   # 귀 덮개 (모자에 붙은 위쪽 뒤편, 모자와 같은 색)
        B((-hwid / 2 - 0.08, t - hs * 0.08, -hs / 2 - 0.08), (hwid + 0.16, 0.07, hs + 0.16), "#3b3b3b")
        for sg in (-1, 1):
            B((sg * ex - hs * 0.13, t - hs * 0.12, hs / 2 + 0.06), (hs * 0.26, hs * 0.2, 0.06), "#c9a227")
            B((sg * ex - hs * 0.08, t - hs * 0.08, hs / 2 + 0.12), (hs * 0.16, hs * 0.12, 0.02), "#7fc8d8", edge=False)
    if c["scarf"]:
        sc = c["sig"] or "#c0392b"
        B((-hwid * 0.42, sy - 0.12, -0.2), (hwid * 0.84, 0.16, 0.42), sc)
        B((hwid * 0.08, sy - 0.62, dep / 2 + 0.02), (0.16, 0.5, 0.06), shade_hex(sc, 0.85))
    if c["glasses"]:
        for sg in (-1, 1):
            B((sg * ex - hs * 0.14, ey - hs * 0.1, fz + 0.02), (hs * 0.28, hs * 0.22, 0.01), c.get("glasses_col", "#26221f"), edge=False)
    # 몸 방향
    if face:
        piv = np.array([x0, y0, z0])
        for b in out:
            b.rots.append((piv, "y", face))
    return out


def shade_hex(h, f):
    c = hexrgb(h) * f
    return "#%02x%02x%02x" % tuple(int(x) for x in np.clip(c, 0, 255))


# ───────────────────────── 부엌 (1900년 등대 숙소) ─────────────────────────
def kitchen(t):
    vx = Voxels()
    X, Z, HH = 26, 26, 9                                          # 방은 카메라 뒤(z 24)까지 (방 밖 빈 곳이 보이지 않게)
    vx.fill(0, X, -1, 0, 0, Z, "#8a6141", 14)                    # 나무 바닥
    vx.fill(0, X, 0, HH, -1, 0, "#c9bb98", 16)                   # 뒤 돌벽
    vx.fill(-1, 0, 0, HH, -1, Z, "#bfb08c", 16)                  # 왼쪽 벽
    vx.fill(X, X + 1, 0, HH, -1, Z, "#bfb08c", 16)               # 오른쪽 벽
    for x in range(10, 16):                                       # 창문 (구멍 + 창틀)
        for y in range(3, 7):
            vx.v.pop((x, y, -1), None)
    for x in range(9, 17):
        vx.put(x, 2, -1, "#6b4a30", j=6)
        vx.put(x, 7, -1, "#6b4a30", j=6)
    for y in range(2, 8):
        vx.put(9, y, -1, "#6b4a30", j=6)
        vx.put(16, y, -1, "#6b4a30", j=6)
    vx.fill(-1, X + 1, HH, HH + 1, -1, Z, "#5a4030", 10)        # 나무 천장
    for z in range(1, Z, 4):                                      # 천장 들보
        vx.fill(0, X, HH - 1, HH, z, z + 1, "#4a3424", 6)
    # 무쇠 난로 + 굴뚝
    vx.fill(1, 5, 0, 3, 1, 4, "#2f2f33", 8)
    for x in range(2, 4):
        vx.v.pop((x, 0, 3), None)
        vx.v.pop((x, 1, 3), None)
    vx.fill(3, 4, 3, HH, 1, 2, "#3d3d42", 6)
    # 식탁
    vx.fill(14, 23, 2, 3, 8, 11, "#9b6b43", 10)
    for (x, z) in ((14, 8), (22, 8), (14, 10), (22, 10)):
        vx.fill(x, x + 1, 0, 2, z, z + 1, "#7a5232", 8)
    # 벽시계 몸통
    vx.fill(20, 22, 4, 8, 0, 1, "#7a5232", 8)
    bx = vx.boxes()
    # 창밖 바다 (빛나는 평판)
    bx.append(Box((10, 3, -1.6), (6, 2, 0.1), "#9fb0bc", emit=True, edge=False))
    for i in range(3):
        ph = math.sin(t * 2 + i)
        bx.append(Box((10, 3 + 0.3 * i + 0.05 * ph, -1.5), (6, 0.12, 0.05), "#e8eef2", emit=True, edge=False))
    bx.append(Box((10, 5, -1.6), (6, 2, 0.1), "#7f8f9c", emit=True, edge=False))
    # 불꽃 (깜빡임)
    fl = 0.6 + 0.4 * abs(math.sin(t * 9) * math.sin(t * 3.7))
    bx.append(Box((2.1, 0.1, 3.0), (1.8, 0.5 + 0.9 * fl, 0.3), "#f39c32", emit=True, edge=False))
    bx.append(Box((2.5, 0.1, 3.1), (1.0, 0.3 + 0.5 * fl, 0.3), "#ffd76a", emit=True, edge=False))
    # 냄비 + 김
    bx.append(Box((3.2, 3, 2.2), (1.7, 0.9, 1.6), "#5a5f66"))   # 냄비: 난로 위 앞쪽 (마셜 손이 닿는 곳)
    bx.append(Box((3.35, 3.85, 2.35), (1.4, 0.06, 1.3), "#c9b48a", emit=True, edge=False))   # 수프
    for i in range(3):
        ph = (t * 0.6 + i / 3) % 1
        sz = 0.25 + 0.3 * ph
        bx.append(Box((3.8 + 0.2 * math.sin(t * 3 + i), 4.1 + ph * 2.2, 2.8), (sz, sz, sz), "#f4f6f8", emit=True, edge=False))
    # 시계: 문자판 + 추
    bx.append(Box((20.15, 6.4, 1.0), (1.7, 1.4, 0.06), "#f6efdc"))
    pa = 25 * math.sin(t * math.pi * 2 / 1.6)
    piv = np.array([21, 6.2, 1.1])
    bx.append(Box((20.95, 4.4, 1.05), (0.1, 1.8, 0.05), "#c9a227", [(piv, "z", pa)], edge=False))
    bx.append(Box((20.7, 4.2, 1.05), (0.6, 0.5, 0.08), "#c9a227", [(piv, "z", pa)]))
    # 식탁 위 접시·빵
    bx.append(Box((15.2, 3, 8.2), (1.4, 0.12, 1.4), "#f1ede2"))
    bx.append(Box((20.2, 3, 8.2), (1.4, 0.12, 1.4), "#f1ede2"))
    bx.append(Box((17.6, 3, 8.4), (1.5, 0.7, 0.9), "#d8b27a"))
    return bx


def demo_kitchen(t, cast, flat=False):
    def pose_live(t, seed, extra=None):
        p = {"breath": 0.004 * math.sin(t * 2 * math.pi / 3.6 + seed), "blink": (t + seed) % 3.4 < 0.12}
        p.update(extra or {})
        return p
    bx = kitchen(t)
    M, D, Hm = cast["부등대지기 토머스 마셜 (40)"], cast["등대장 제임스 두캣 (43)"], cast["안내자 하람 (14)"]
    bx += person(M, (7.4, 0, 2.6), face=-90, pose=pose_live(t, 0.3, {"arm": 70 + 12 * math.sin(t * 2 * math.pi / 1.4), "talk": abs(math.sin(t * 9)) * 0.8}))
    bx += person(D, (21.0, 0, 5.6), face=-15, pose=pose_live(t, 1.7))
    bx += person(Hm, (17.2, 0, 5.4), face=10, pose=pose_live(t, 2.9, {"talk": 0}))
    # 카메라: 앞쪽 위에서 비스듬히, 아주 천천히 다가감
    if flat:   # 평면 블록: 정면에서 똑바로, 원근 없이 (천천히 옆으로 흐름)
        cam = Camera((12.2 + 0.12 * t, 4.5, 40), (12.2 + 0.12 * t, 4.5, 0), ortho=11.0)
    else:
        cam = Camera((13 + 0.8 * math.sin(t * 0.2), 8.0 - 0.1 * t, 24 - 0.3 * t), (13, 3.6, 4), fov=44)
    return render(bx, cam, bg=(40, 36, 34))


if __name__ == "__main__":
    import json
    a = sys.argv[1:]
    HERE = os.path.dirname(os.path.abspath(__file__))
    cast = {c["name"]: c for c in json.load(open(os.path.join(HERE, "연재/플래넌등대/등장인물_카툰.json"), encoding="utf-8"))["chars"]}
    out = a[1]
    flat = "--평면" in a
    if out.endswith(".png"):
        demo_kitchen(float(a[a.index("--t") + 1]) if "--t" in a else 0.5, cast, flat).save(out)
    else:
        sec = float(a[a.index("--초") + 1]) if "--초" in a else 6
        fps = 24
        ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(fps), "-i", "-",
                               "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", out], stdin=subprocess.PIPE)
        for k in range(int(sec * fps)):
            ff.stdin.write(demo_kitchen(k / fps, cast, flat).tobytes())
        ff.stdin.close()
        ff.wait()
        print("만듦:", out)
