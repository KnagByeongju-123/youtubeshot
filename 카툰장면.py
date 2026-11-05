"""카툰 장면 영상 — 코드로 그린 배경 + 움직이는 카툰 인물 (GPU 없이)
python 카툰장면.py <장면.json> <결과.mp4> [--초 5] [--fps 24] [--미리보기 결과.png]
  장면.json = {"bg": "kitchen" | "sea_lighthouse" | "white", "chars": [{"who": "<등장인물_카툰.json 의 name>",
               "x": 960, "scale": 0.9, "view": "front|back|right|left",
               "act": ["blink", "breath", "talk", "stir", "wave", "walk"], "dx": 0}], "cast": "<등장인물_카툰.json 경로>"}
  - blink 눈 깜빡임, breath 숨쉬기, talk 입 움직임, stir 냄비 젓기(팔), wave 손 흔들기, walk 걷기(dx = 초당 이동 px)
  - 같은 인물 설정이면 어느 장면에서든 똑같은 얼굴 (카툰캐릭터.py)
"""
import importlib.util
import json
import math
import os
import subprocess
import sys

import cairosvg

HERE = os.path.dirname(os.path.abspath(__file__))
_sp = importlib.util.spec_from_file_location("kchar", os.path.join(HERE, "카툰캐릭터.py"))
K = importlib.util.module_from_spec(_sp)
_sp.loader.exec_module(K)
W, H = 1920, 1080
OUT = K.OUT


def R(x, y, w, h, fill, sw=4, extra=""):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" stroke="{OUT}" stroke-width="{sw}" {extra}/>'


# ───────────────────────── 배경 ─────────────────────────
def bg_kitchen(t, cold=False, mood="storm", stopped=False):
    """1900년 등대 숙소 부엌: 돌벽, 나무 바닥, 무쇠 난로(불꽃), 창밖 폭풍 바다, 벽시계(추가 흔들림), 식탁"""
    s = '<defs><linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#5d6b7a"/><stop offset="1" stop-color="#9aa6b0"/></linearGradient></defs>'
    s += R(0, 0, W, H, "#cdbf9f", 0)
    for r in range(9):   # 돌벽 줄눈
        y = 40 + r * 82
        s += f'<line x1="0" y1="{y}" x2="{W}" y2="{y}" stroke="#b3a482" stroke-width="3"/>'
        for k in range(14):
            x = (k * 150 + (75 if r % 2 else 0)) % (W + 150)
            s += f'<line x1="{x}" y1="{y}" x2="{x}" y2="{y + 82}" stroke="#b3a482" stroke-width="3"/>'
    s += R(0, 800, W, 280, "#8a6141", 0) + f'<line x1="0" y1="800" x2="{W}" y2="800" stroke="{OUT}" stroke-width="5"/>'
    for k in range(12):
        s += f'<line x1="{k * 170}" y1="800" x2="{k * 170 - 120}" y2="{H}" stroke="#6f4c32" stroke-width="3"/>'
    # 창문 + 바깥 바다
    wx, wy, ww, wh = 760, 150, 400, 300
    s += R(wx - 18, wy - 18, ww + 36, wh + 36, "#6b4a30", 5)
    s += R(wx, wy, ww, wh, "url(#sky)", 4)
    for i in range(5):
        yy = wy + 190 + i * 22
        ph = t * 2.2 + i
        d = f"M{wx},{yy} " + " ".join(f"Q{wx + 20 + 40 * j},{yy - 10 * math.sin(ph + j)} {wx + 40 + 40 * j},{yy}" for j in range(10))
        s += f'<path d="{d}" fill="none" stroke="#e8eef2" stroke-width="3" opacity="0.8"/>'
    s += f'<rect x="{wx}" y="{wy + 185}" width="{ww}" height="{wh - 185}" fill="#3f5566" opacity="0.6"/>'
    s += f'<line x1="{wx + ww / 2}" y1="{wy}" x2="{wx + ww / 2}" y2="{wy + wh}" stroke="#6b4a30" stroke-width="12"/>'
    s += f'<line x1="{wx}" y1="{wy + wh / 2}" x2="{wx + ww}" y2="{wy + wh / 2}" stroke="#6b4a30" stroke-width="12"/>'
    # 벽시계 (추가 흔들림)
    cx, cy = 1450, 230
    s += R(cx - 55, cy - 70, 110, 260, "#7a5232", 5) + K.E(cx, cy, 44, 44, "#f6efdc", 5)
    for h_ in range(12):
        a = h_ * math.pi / 6
        s += f'<line x1="{cx + 34 * math.sin(a):.1f}" y1="{cy - 34 * math.cos(a):.1f}" x2="{cx + 39 * math.sin(a):.1f}" y2="{cy - 39 * math.cos(a):.1f}" stroke="{OUT}" stroke-width="3"/>'
    s += f'<line x1="{cx}" y1="{cy}" x2="{cx + 20}" y2="{cy - 18}" stroke="{OUT}" stroke-width="5" stroke-linecap="round"/>'
    s += f'<line x1="{cx}" y1="{cy}" x2="{cx - 4}" y2="{cy - 32}" stroke="{OUT}" stroke-width="3" stroke-linecap="round"/>'
    pa = 0.0 if stopped else 0.35 * math.sin(t * math.pi * 2 / 1.6)
    px, py = cx + 85 * math.sin(pa), cy + 60 + 85 * math.cos(pa)
    s += f'<line x1="{cx}" y1="{cy + 60}" x2="{px:.1f}" y2="{py:.1f}" stroke="#c9a227" stroke-width="4"/>' + K.E(px, py, 14, 14, "#c9a227", 4)
    # 무쇠 난로 + 냄비 + 김
    sx, sy = 260, 560
    s += R(sx, sy, 300, 240, "#2f2f33", 6, 'rx="10"') + R(sx - 20, sy - 30, 340, 34, "#3d3d42", 6, 'rx="6"')
    s += R(sx + 260 - 10, 0, 40, sy - 30, "#3d3d42", 5)
    fl = 0.0 if cold else 0.75 + 0.25 * math.sin(t * 17) * math.sin(t * 7.3)
    s += R(sx + 60, sy + 90, 180, 110, "#1a1a1a", 5, 'rx="8"')
    if not cold:
        s += K.P(f"M{sx + 80},{sy + 195} Q{sx + 110},{sy + 195 - 70 * fl} {sx + 150},{sy + 150} Q{sx + 175},{sy + 195 - 85 * fl} {sx + 220},{sy + 195} Z", "#f39c32", 3)
        s += K.P(f"M{sx + 115},{sy + 195} Q{sx + 140},{sy + 195 - 40 * fl} {sx + 185},{sy + 195} Z", "#ffd76a", 0)
    s += R(sx + 60, sy - 110, 170, 85, "#5a5f66", 5, 'rx="12"')
    for i in range(0 if cold else 3):   # 김
        ph = (t * 0.6 + i / 3) % 1
        yy = sy - 120 - ph * 160
        xx = sx + 110 + i * 30 + 14 * math.sin(t * 3 + i)
        s += f'<ellipse cx="{xx:.1f}" cy="{yy:.1f}" rx="{20 + ph * 20:.1f}" ry="{12 + ph * 10:.1f}" fill="#ffffff" opacity="{0.55 * (1 - ph):.2f}"/>'
    return s


def bg_table(t):
    """앞쪽 식탁 (인물 앞에 그림)"""
    return (R(1180, 760, 640, 40, "#9b6b43", 6, 'rx="6"') + R(1210, 800, 30, 220, "#7a5232", 5) + R(1760, 800, 30, 220, "#7a5232", 5)
            + K.E(1330, 752, 60, 14, "#f1ede2", 4) + K.E(1600, 752, 60, 14, "#f1ede2", 4)
            + R(1450, 700, 90, 52, "#d8b27a", 4, 'rx="20"'))



# ───────────────────────── 하늘·바다·섬 (여러 배경이 같이 씀) ─────────────────────────
SKY = {   # 분위기별 하늘 위·아래 색, 바다 색, 어둡게
    "day": ("#8fb3cc", "#d6e4ea", "#4f7c96"), "grey": ("#7d8a95", "#b9c2c8", "#4a6070"),
    "storm": ("#3b4450", "#6d7884", "#2c3e4c"), "dusk": ("#4a4e7a", "#e7a36b", "#3c4f6e"),
    "night": ("#0d1630", "#2a3a5e", "#16233d"), "fog": ("#a7adb2", "#d3d6d8", "#6d7d88"),
}


def sky(mood, horizon=640):
    a, b, _ = SKY.get(mood, SKY["day"])
    s = (f'<defs><linearGradient id="sk_{mood}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{a}"/>'
         f'<stop offset="1" stop-color="{b}"/></linearGradient></defs><rect width="{W}" height="{horizon + 2}" fill="url(#sk_{mood})"/>')
    if mood == "night":
        for i in range(60):
            x, y = (i * 397) % W, (i * 211) % (horizon - 80)
            s += f'<circle cx="{x}" cy="{y}" r="{1.2 + (i % 3) * 0.6}" fill="#ffffff" opacity="0.7"/>'
    if mood in ("storm", "grey", "fog", "dusk"):
        for i in range(5):
            cx, cy = (i * 470 + 120) % (W + 200) - 100, 90 + (i % 3) * 70
            col = "#2a313a" if mood == "storm" else ("#8a8fa0" if mood == "dusk" else "#9aa3aa")
            s += f'<ellipse cx="{cx}" cy="{cy}" rx="260" ry="60" fill="{col}" opacity="0.6"/>'
    return s


def sea(mood, t, horizon=640, rough=1.0):
    _, _, c = SKY.get(mood, SKY["day"])
    s = f'<rect y="{horizon}" width="{W}" height="{H - horizon}" fill="{c}"/>'
    for i in range(9):
        yy = horizon + 18 + i * (i + 3) * 6
        amp = (4 + i * 2) * rough
        ph = t * (1.2 + 0.25 * i) + i * 1.7
        seg = 60 + i * 18
        d = f"M-40,{yy} " + " ".join(f"Q{-40 + seg * j + seg / 2:.0f},{yy - amp * math.sin(ph + j * 0.9):.1f} {-40 + seg * (j + 1):.0f},{yy}" for j in range(int(W / seg) + 3))
        s += f'<path d="{d}" fill="none" stroke="#ffffff" stroke-width="{2 + i * 0.4:.1f}" opacity="{0.25 + 0.04 * i:.2f}"/>'
    return s


def lighthouse(x, base, h, lamp="on", t=0.0, ruin=False):
    """등대(흰 탑 + 검은 꼭대기) + 옆 숙소. lamp: on / off / beam(돌아가는 빛)"""
    w0, w1 = h * 0.16, h * 0.11
    s = ""
    hx = x - h * 0.55   # 숙소
    s += R(hx - h * 0.3, base - h * 0.28, h * 0.62, h * 0.28, "#e9e4d8", 4) + K.P(f"M{hx - h * 0.34},{base - h * 0.28} L{hx},{base - h * 0.42} L{hx + h * 0.36},{base - h * 0.28} Z", "#5a5f66", 4)
    for k in range(3):
        s += R(hx - h * 0.22 + k * h * 0.17, base - h * 0.2, h * 0.08, h * 0.08, "#ffd76a" if lamp != "off" and k == 1 else "#4a5560", 3)
    s += K.P(f"M{x - w0},{base} L{x - w1},{base - h * 0.78} L{x + w1},{base - h * 0.78} L{x + w0},{base} Z", "#f4f1ea", 4)
    s += R(x - w1 - 8, base - h * 0.8, (w1 + 8) * 2, 12, "#2f2f33", 4)
    glow = lamp != "off"
    s += R(x - w1 * 0.75, base - h * 0.93, w1 * 1.5, h * 0.13, "#ffe9a0" if glow else "#3a4552", 4)
    s += K.P(f"M{x - w1 * 0.9},{base - h * 0.93} Q{x},{base - h * 1.04} {x + w1 * 0.9},{base - h * 0.93} Z", "#2f2f33", 4)
    if lamp == "beam":
        a = (t * 0.9) % 2.0
        side = 1 if a < 1 else -1
        op = 0.55 * math.sin(math.pi * (a % 1))
        ly = base - h * 0.865
        s += f'<path d="M{x},{ly} L{x + side * 1400},{ly - 120} L{x + side * 1400},{ly + 160} Z" fill="#fff4c2" opacity="{op:.2f}"/>'
    if glow:
        s += f'<circle cx="{x}" cy="{base - h * 0.865}" r="{h * 0.14}" fill="#fff4c2" opacity="0.35"/>'
    return s


def island(mood, t, lamp="on", present=False, ship=None, flare=False, fog=False, far=False, p=0.0):
    s = sky(mood) + sea(mood, t)
    cx = 1100 if not far else 1250
    sc = 1.0 if not far else 0.6
    s += K.P(f"M{cx - 520 * sc},{660} L{cx - 430 * sc},{660 - 260 * sc} L{cx - 250 * sc},{660 - 330 * sc} L{cx + 120 * sc},{660 - 350 * sc} "
             f"L{cx + 380 * sc},{660 - 300 * sc} L{cx + 560 * sc},{660 - 180 * sc} L{cx + 640 * sc},{660} Z", "#4f5a46" if mood != "night" else "#1f2a24", 5)
    s += K.P(f"M{cx - 430 * sc},{660 - 260 * sc} L{cx - 250 * sc},{660 - 330 * sc} L{cx + 120 * sc},{660 - 350 * sc} L{cx + 380 * sc},{660 - 300 * sc} "
             f"L{cx + 360 * sc},{660 - 270 * sc} L{cx - 300 * sc},{660 - 290 * sc} Z", "#6f8a56" if mood != "night" else "#2d3d2f", 0)
    s += lighthouse(cx + 60 * sc, 660 - 345 * sc, 250 * sc, lamp if not present else "beam", t)
    if ship:   # ship = [시작 x, 멈출 x]: 장면 앞 55% 동안 섬 쪽으로 다가와 멈춤
        q = min(1.0, p / 0.55)
        q = 0.5 - 0.5 * math.cos(math.pi * q)
        sx = ship[0] + (ship[1] - ship[0]) * q
        s += boat(sx, 690, 0.8)
        if flare and p > 0.55:   # 배가 멈춘 뒤 그 배에서 조명탄을 쏘아 올림
            ph = min(1.0, (p - 0.55) / 0.35)
            fx_, fy = sx + 40 + 60 * ph, 610 - 470 * math.sin(ph * math.pi / 2)
            s += f'<line x1="{sx + 40:.0f}" y1="610" x2="{fx_:.0f}" y2="{fy:.0f}" stroke="#ffb38a" stroke-width="3" opacity="0.5"/>'
            s += f'<circle cx="{fx_:.0f}" cy="{fy:.0f}" r="{9 + 26 * ph:.0f}" fill="#ff5a3c" opacity="{0.95 - 0.3 * ph:.2f}"/>'
            s += f'<circle cx="{fx_:.0f}" cy="{fy:.0f}" r="{40 + 90 * ph:.0f}" fill="#ff8a5c" opacity="{0.25 * (1 - ph) + 0.08:.2f}"/>'
    if fog or mood == "fog":
        s += f'<rect width="{W}" height="{H}" fill="#e6e9eb" opacity="0.35"/>'
    return s


def boat(x, y, sc=1.0):
    """작은 증기선 (1900년)"""
    g = (K.P(f"M{-170},{0} L{170},{0} L{130},{55} L{-140},{55} Z", "#2e2b2a", 5) + R(-90, -55, 170, 55, "#d9d2c3", 4)
         + R(-30, -130, 36, 78, "#a83232", 4) + R(-30, -130, 36, 14, "#1d1d1d", 3)
         + f'<line x1="120" y1="0" x2="120" y2="-120" stroke="{OUT}" stroke-width="5"/>')
    return f'<g transform="translate({x:.0f},{y}) scale({sc})">{g}</g>'


# ───────────────────────── 장소 배경 ─────────────────────────
def bg_sea(t, p, o):
    s = island(o.get("mood", "grey"), t, o.get("lamp", "on"), o.get("present", False), o.get("ship"), o.get("flare", False), far=o.get("far", False), p=p)
    if o.get("swell"):   # 먼바다 수평선이 부풀어 오름
        h = 30 + 170 * p
        s += K.P(f"M0,642 Q500,{642 - h * 0.3:.0f} 900,{642 - h:.0f} Q1300,{642 - h * 0.3:.0f} 1920,642 Z", "#3c4f6e", 4)
        s += K.P(f"M600,{642 - h * 0.75:.0f} Q900,{642 - h * 1.05:.0f} 1200,{642 - h * 0.75:.0f}", "none", 8, 'stroke="#ffffff" opacity="0.7"')
    return s


def bg_landing(t, p, o):
    """돌 선착장 가까이: 젖은 돌계단, 쇠 난간, 빈 깃대, 부서지는 파도"""
    mood = o.get("mood", "grey")
    s = sky(mood, 520) + sea(mood, t, 520, 1.6)
    s += K.P("M0,620 L760,560 L980,600 L1920,640 L1920,1080 L0,1080 Z", "#5b5e60", 5)
    for k in range(7):
        y = 620 + k * 62
        s += K.P(f"M{120 + k * 40},{y} L{760 + k * 30},{y - 20} L{760 + k * 30},{y + 26} L{120 + k * 40},{y + 46} Z", "#7b7e80", 4)
    bent = o.get("bent", False)
    for k in range(6):
        x0 = 860 + k * 160
        top = 470 if not (bent and k >= 2) else 470 + (k - 1) * 30
        lean = (k - 1) * 40 if bent and k >= 2 else 0
        s += f'<line x1="{x0}" y1="640" x2="{x0 + lean}" y2="{top}" stroke="#4a4a4f" stroke-width="12" stroke-linecap="round"/>'
    pts = []
    for k in range(6):
        x0 = 860 + k * 160
        lean = (k - 1) * 40 if bent and k >= 2 else 0
        top = 470 if not (bent and k >= 2) else 470 + (k - 1) * 30
        pts.append(f"{x0 + lean},{top}")
    s += f'<polyline points="{" ".join(pts)}" fill="none" stroke="#4a4a4f" stroke-width="12" stroke-linecap="round"/>'
    if o.get("flagpole", True):
        s += f'<line x1="300" y1="610" x2="300" y2="200" stroke="{OUT}" stroke-width="9"/>' + K.E(300, 196, 10, 10, "#c9a227", 4)
    if o.get("wet", False):
        s += f'<rect width="{W}" height="{H}" fill="#9fb4c4" opacity="0.12"/>'
    return s


def bg_stairs(t, p, o):
    s = sky("grey", 400) + sea("grey", t, 400)
    s += K.P("M0,1080 L0,380 L700,300 L1920,250 L1920,1080 Z", "#5e6b52", 5)
    for k in range(10):   # 가파른 돌계단
        x = 1300 - k * 95
        y = 1080 - k * 78
        s += R(x - 140, y - 60, 280, 60, "#8b8d8f", 4)
    s += f'<polyline points="{" ".join(f"{1460 - k * 95},{1000 - k * 78 - 60}" for k in range(10))}" fill="none" stroke="{OUT}" stroke-width="7"/>'
    s += lighthouse(420, 330, 260, o.get("lamp", "off"), t)
    return s


def bg_kitchen_full(t, p, o):
    s = bg_kitchen(t, cold=o.get("cold", False), mood=o.get("mood", "storm"), stopped=o.get("stopped", False))
    if o.get("night"):
        s += f'<rect width="{W}" height="{H}" fill="#0b1430" opacity="0.38"/>'
        s += f'<circle cx="1500" cy="640" r="380" fill="#ffcf6a" opacity="0.10"/>'
    if o.get("notice"):   # 벽에 붙은 규칙 종이 (글자 대신 줄)
        s += R(560, 330, 150, 190, "#f1e6c8", 4)
        for j in range(6):
            s += f'<line x1="580" y1="{360 + j * 26}" x2="{690 - (j % 2) * 30}" y2="{360 + j * 26}" stroke="#9a8f7a" stroke-width="5"/>'
    if o.get("hook"):     # 문 옆 옷걸이 + 걸린 방수 외투
        s += R(1600, 300, 220, 26, "#6b4a30", 5)
        if o["hook"] == "coat":
            s += K.P("M1680,326 L1760,326 L1810,700 L1720,716 L1630,700 Z", "#2e3b4f", 5)
    if o.get("door"):
        s += R(60, 300, 230, 500, "#6b4a30", 6) + R(80, 320, 190, 460, "#cfd6dc" if o["door"] == "open" else "#7a5232", 4)
    return s


def bg_hook(t, p, o):
    """벽의 옷걸이 가까이 (외투가 걸려 있음 / 없음 / 지금의 폐허)"""
    ruin = o.get("ruin", False)
    s = R(0, 0, W, H, "#cdbf9f" if not ruin else "#9a9283", 0)
    for r in range(14):
        y = r * 82
        s += f'<line x1="0" y1="{y}" x2="{W}" y2="{y}" stroke="#b3a482" stroke-width="3"/>'
    s += R(560, 220, 800, 46, "#6b4a30", 6, 'rx="8"')
    for k in range(3):
        hx = 720 + k * 240
        s += K.P(f"M{hx},{266} q0,40 30,50", "none", 9, 'stroke="#3b3b3b"')
    if o.get("coat", True) and not ruin:
        sway = 4 * math.sin(t * 1.3)
        s += f'<g transform="rotate({sway:.2f} 960 300)">' + K.P("M900,300 L1020,300 L1110,880 L960,910 L810,880 Z", "#2e3b4f", 6) \
             + K.P("M900,300 L960,420 L1020,300", "none", 5) + R(940, 520, 40, 260, "#26303f", 3) + '</g>'
    if ruin:
        s += f'<rect width="{W}" height="{H}" fill="#556b7a" opacity="0.18"/>'
        s += K.P("M0,0 L700,0 L560,140 L0,200 Z", "#9fb6c6", 0)   # 무너진 지붕 틈 하늘
    if o.get("wick"):
        s += R(870, 196, 90, 18, "#f1e6c8", 3, 'rx="6"')
    if o.get("hand"):
        y = 120 + 80 * min(1, p * 3)
        s += K.E(915, y, 46, 34, "#f6d3b3", 5) + R(870, y - 10 - 0, 90, 18, "#f1e6c8", 3, 'rx="6"')
    return s


def bg_lantern(t, p, o):
    """등대 꼭대기 렌즈실: 유리창 밖 바다, 가운데 커다란 계단식 유리 렌즈(빛이 돎)"""
    mood = o.get("mood", "night")
    s = sky(mood, 700) + sea(mood, t, 700)
    if o.get("land"):   # 창밖 아래로 보이는 섬 비탈 (멀리 걷는 사람이 바다 위가 아니라 땅 위에 있게)
        g = "#4f5a46" if mood not in ("night", "storm") else "#3a4436"
        s += K.P("M0,690 Q500,660 900,700 Q1300,740 1920,720 L1920,880 L0,880 Z", g, 4)
        s += K.P("M700,700 Q1100,760 1500,790 L1920,800", "none", 6, 'stroke="#8b8d8f" opacity="0.8"')   # 서쪽으로 내려가는 길
    for k in range(7):   # 유리창 틀
        x = k * 320
        s += f'<line x1="{x}" y1="0" x2="{x}" y2="1080" stroke="#2a2a2e" stroke-width="16"/>'
    s += f'<line x1="0" y1="140" x2="{W}" y2="140" stroke="#2a2a2e" stroke-width="16"/>'
    s += R(0, 860, W, 220, "#3b3b40", 6)
    on = o.get("light", "on")
    dim = 1.0
    if on == "dim":   # 점점 꺼짐
        dim = max(0.0, 1 - p * 1.1)
    if on == "flicker":
        dim = 0.6 + 0.4 * abs(math.sin(t * 9)) * (0.5 + 0.5 * math.sin(t * 2.3))
    lx, ly = o.get("lx", 960), 520
    s += R(lx - 150, 760, 300, 110, "#6b4a30", 5) + R(lx - 180, 740, 360, 26, "#8a6141", 5)
    s += K.E(lx, ly, 170, 230, "#d5e8ec", 6)
    for k in range(6):
        s += K.E(lx, ly, 170 - k * 26, 230 - k * 36, "none", 3, f'stroke="#9fbcc4"')
    if on != "off":
        s += f'<ellipse cx="{lx}" cy="{ly}" rx="{150 * dim + 10:.0f}" ry="{200 * dim + 10:.0f}" fill="#fff1a8" opacity="{0.75 * dim:.2f}"/>'
        s += K.E(lx, ly, 40 * dim + 4, 50 * dim + 4, "#ffffff", 0, f'opacity="{0.9 * dim:.2f}"')
        if mood in ("night", "dusk", "storm"):
            a = (t * 0.35) % 1
            op = 0.45 * dim * math.sin(math.pi * a)
            s += f'<path d="M{lx},{ly} L{W + 200},{ly - 260 + 520 * a} L{W + 200},{ly - 120 + 520 * a} Z" fill="#fff4c2" opacity="{op:.2f}"/>'
    if o.get("wipe"):
        s += K.E(lx - 60 + 50 * math.sin(t * 3), ly + 20 * math.cos(t * 3), 50, 30, "#ffffff", 3, 'opacity="0.8"')
    return s


def bg_rocks(t, p, o):
    mood = o.get("mood", "grey")
    s = sky(mood, 560) + sea(mood, t, 560, 1.8)
    s += K.P("M0,760 Q300,640 640,700 Q980,760 1300,660 Q1650,600 1920,700 L1920,1080 L0,1080 Z", "#4c4f52", 5)
    s += K.P("M0,860 Q500,780 900,840 Q1400,900 1920,820 L1920,1080 L0,1080 Z", "#3a3d40", 4)
    return s


def bg_bedroom(t, p, o):
    s = R(0, 0, W, H, "#7d7466", 0) + R(0, 820, W, 260, "#5a4230", 0)
    s += R(1180, 180, 420, 340, "#6b4a30", 6) + R(1200, 200, 380, 300, "#1d2740", 4)
    if (t % 5.0) < 0.12:   # 번개
        s += R(1200, 200, 380, 300, "#dfe8ff", 0)
    for k in range(18):
        y = (t * 600 + k * 53) % 300
        s += f'<line x1="{1210 + k * 21}" y1="{200 + y:.0f}" x2="{1200 + k * 21}" y2="{225 + y:.0f}" stroke="#9fb0d0" stroke-width="2" opacity="0.7"/>'
    s += R(200, 620, 760, 220, "#8a6141", 6) + R(220, 560, 720, 90, "#e9e1cf", 5, 'rx="14"') + R(200, 520, 40, 320, "#6b4a30", 5)
    s += f'<rect width="{W}" height="{H}" fill="#0b1430" opacity="0.35"/>'
    s += f'<circle cx="300" cy="300" r="220" fill="#ffcf6a" opacity="0.08"/>'
    return s


def bg_wave(t, p, o):
    """서쪽 절벽에 부딪쳐 솟구치는 거대한 파도 (p: 0→1 동안 솟았다가 덮침)"""
    s = sky("storm", 700) + sea("storm", t, 700, 2.5)
    s += K.P("M1200,1080 L1260,520 L1420,430 L1700,460 L1920,420 L1920,1080 Z", "#3a4036", 6)
    h = 900 * math.sin(math.pi * min(1.0, p * 1.15)) if not o.get("silhouette") else 760
    s += K.P(f"M0,1080 L0,{1080 - h * 0.6:.0f} Q500,{1080 - h * 1.05:.0f} 1150,{1080 - h:.0f} Q1300,{1080 - h * 0.85:.0f} 1350,{1080 - h * 0.55:.0f} L1350,1080 Z", "#5f8aa3", 6)
    s += K.P(f"M500,{1080 - h * 0.98:.0f} Q850,{1080 - h * 1.12:.0f} 1150,{1080 - h:.0f} Q1260,{1080 - h * 0.9:.0f} 1300,{1080 - h * 0.7:.0f}", "none", 14, 'stroke="#ffffff" opacity="0.8"')
    for k in range(14):
        a = (t * 0.8 + k / 14) % 1
        x = 1150 + 300 * math.cos(k * 2.1) * a
        y = 1080 - h - 200 * a + 40 * math.sin(k)
        s += f'<line x1="{x:.0f}" y1="{y:.0f}" x2="{x + 60 * math.cos(k * 2.1):.0f}" y2="{y - 50 - 40 * a:.0f}" stroke="#ffffff" stroke-width="{10 - 6 * a:.1f}" stroke-linecap="round" opacity="{0.75 * (1 - a):.2f}"/>'
    if o.get("silhouette"):
        for k in range(3):
            x = 1440 + k * 60
            s += K.E(x, 395, 16, 18, "#111", 0) + R(x - 16, 410, 32, 70, "#111", 0, 'rx="10"')
        s += f'<line x1="1440" y1="430" x2="1560" y2="430" stroke="#111" stroke-width="12" stroke-linecap="round"/>'
    return s


def bg_plain(t, p, o):
    a, b = o.get("c1", "#2b3a52"), o.get("c2", "#5a6f8a")
    return (f'<defs><radialGradient id="pl" cx="0.5" cy="0.4" r="0.8"><stop offset="0" stop-color="{b}"/><stop offset="1" stop-color="{a}"/></radialGradient></defs>'
            f'<rect width="{W}" height="{H}" fill="url(#pl)"/>')


def bg_papers(t, p, o):
    s = R(0, 0, W, H, "#3a3230", 0)
    for k in range(5):
        x, y, r_ = 200 + k * 330, 160 + (k % 2) * 140, -8 + k * 4
        g = R(0, 0, 420, 560, "#efe6cf", 5)
        for j in range(14):
            g += f'<line x1="30" y1="{90 + j * 30}" x2="{390 - (j % 3) * 40}" y2="{90 + j * 30}" stroke="#9a8f7a" stroke-width="6"/>'
        g += R(30, 30, 360, 36, "#6a5f4a", 0)
        s += f'<g transform="translate({x},{y}) rotate({r_})">{g}</g>'
    a = 0.5 + 0.5 * math.sin(t * 0.8)
    s += K.P(f"M1200,1080 Q1300,{700 - 40 * a:.0f} 1420,{760 - 40 * a:.0f} Q1500,{620 - 40 * a:.0f} 1600,{700 - 40 * a:.0f} Q1700,{760 - 40 * a:.0f} 1800,1080 Z", "#101418", 0, 'opacity="0.55"')
    return s


def bg_desk(t, p, o):
    s = R(0, 0, W, H, "#2c2522", 0) + R(1250, 160, 460, 420, "#1a2a44", 6)
    s += sea("night", t, 900, 0.4).replace(f'<rect y="900"', '<rect y="900" opacity="0"')
    s += R(0, 760, W, 320, "#5a3e2a", 0)
    s += K.P("M520,760 L960,700 L1400,760 L960,800 Z", "#efe6cf", 5) + f'<line x1="960" y1="700" x2="960" y2="800" stroke="{OUT}" stroke-width="4"/>'
    for j in range(5):
        s += f'<line x1="{600 + j * 4}" y1="{740 - j * 6}" x2="{900}" y2="{715 - j * 6}" stroke="#9a8f7a" stroke-width="4"/>'
        s += f'<line x1="{1020}" y1="{715 - j * 6}" x2="{1320 - j * 4}" y2="{740 - j * 6}" stroke="#9a8f7a" stroke-width="4"/>'
    fl = 0.8 + 0.2 * math.sin(t * 13) * math.sin(t * 5)
    s += R(380, 600, 50, 160, "#f1e6c8", 4) + K.P(f"M405,600 Q{390},{570 - 20 * fl:.0f} 405,{530 - 30 * fl:.0f} Q{420},{570 - 20 * fl:.0f} 405,600 Z", "#ffcf4a", 3)
    s += f'<circle cx="405" cy="560" r="{260 * fl:.0f}" fill="#ffcf6a" opacity="0.12"/>'
    return s


def bg_ring(t, p, o):
    s = bg_rocks(t, p, {"mood": "day"})
    s += K.E(960, 900, 160, 40, "#4a3a2e", 6) + K.E(960, 820, 120, 90, "none", 22, 'stroke="#8a4a2a"') + K.E(960, 820, 120, 90, "none", 6, f'stroke="{OUT}"')
    return s


def bg_crevice(t, p, o):
    s = sky("grey", 300) + sea("grey", t, 300, 1.2)
    s += K.P("M0,1080 L0,420 L700,380 L780,560 L1100,560 L1180,360 L1920,330 L1920,1080 Z", "#4d5052", 6)
    s += K.P("M780,560 L1100,560 L1060,760 L820,760 Z", "#24272a", 5)
    s += f'<rect width="{W}" height="{H}" fill="#9fb4c4" opacity="0.1"/>'
    return s


def bg_vortex(t, p, o):
    """시간을 건너는 빛 소용돌이"""
    s = bg_plain(t, p, {"c1": "#120f2a", "c2": "#3d3a7a"})
    for k in range(9):
        r = (k * 120 + t * 260) % 1100
        s += f'<circle cx="960" cy="540" r="{r:.0f}" fill="none" stroke="{["#7fc8d8", "#f3c969", "#c0392b"][k % 3]}" stroke-width="{6 + k % 3 * 4}" opacity="{max(0, 0.8 - r / 1300):.2f}"/>'
    for k in range(24):
        a = k * 0.26 + t * 1.6
        r = 200 + (k * 37) % 500
        s += f'<line x1="{960 + r * math.cos(a):.0f}" y1="{540 + r * math.sin(a):.0f}" x2="{960 + (r + 90) * math.cos(a + 0.3):.0f}" y2="{540 + (r + 90) * math.sin(a + 0.3):.0f}" stroke="#ffffff" stroke-width="3" opacity="0.5"/>'
    return s


BGS = {"kitchen": bg_kitchen_full, "white": lambda t, p, o: R(0, 0, W, H, "#ffffff", 0), "sea": bg_sea, "landing": bg_landing,
       "stairs": bg_stairs, "hook": bg_hook, "lantern": bg_lantern, "rocks": bg_rocks, "bedroom": bg_bedroom, "wave": bg_wave,
       "plain": bg_plain, "papers": bg_papers, "desk": bg_desk, "ring": bg_ring, "crevice": bg_crevice, "vortex": bg_vortex}


def front_table(t, p, o):
    return bg_table(t) if o.get("table") else ""


def front_lens(t, p, o):
    return ""


def front_console(t, p, o):
    return (R(960 - 180 - 200, 760, 760, 26, "#8a6141", 5) + R(960 - 150 - 200, 786, 700, 300, "#6b4a30", 5)) if o.get("console") else ""


FRONT = {"kitchen": front_table, "lantern": front_console}


# ───────────────────────── 움직임 ─────────────────────────
def pose_at(acts, t, seed):
    p = {}
    if "breath" in acts:
        p["breath"] = 0.008 * math.sin(t * 2 * math.pi / 3.6 + seed)
    if "blink" in acts:   # 3~4초마다 0.12초
        per = 3.2 + (seed % 3) * 0.4
        p["blink"] = (t + seed * 0.7) % per < 0.12
    if "closed" in acts:
        p["blink"] = True
    if "talk" in acts:
        p["talk"] = abs(math.sin(t * 11 + seed)) * (0.5 + 0.5 * math.sin(t * 3.1))
    if "shout" in acts:
        p["talk"] = 0.7 + 0.3 * abs(math.sin(t * 6))
        p["arm_r"] = 25 + 10 * math.sin(t * 5)
        p["arm_l"] = 25 + 10 * math.sin(t * 5)
    if "stir" in acts:
        p["arm"] = 90 + 9 * math.sin(t * 2 * math.pi / 1.4)
    if "wave" in acts:
        p["arm_r"] = 140 + 18 * math.sin(t * 2 * math.pi / 0.6)
    if "point" in acts:
        p["arm_r"] = 95
        p["arm"] = 95
    if "reach" in acts:
        p["arm"] = 70 + 6 * math.sin(t * 2)
    if "pat" in acts:
        p["arm"] = 120 + 8 * math.sin(t * 2 * math.pi / 0.8)
    if "wipe" in acts:
        p["arm"] = 100 + 14 * math.sin(t * 3)
    if "walk" in acts:
        p["walk"] = t * 2 * math.pi / 0.9
        p["bob"] = -6 * abs(math.sin(t * 2 * math.pi / 0.9))
    if "run" in acts:
        p["walk"] = t * 2 * math.pi / 0.5
        p["bob"] = -14 * abs(math.sin(t * 2 * math.pi / 0.5))
    if "shiver" in acts:
        p["bob"] = 1.5 * math.sin(t * 40)
    return p


def frame_svg(scene, cast, t, dur=None):
    """장면의 t 초 모습 SVG. dur(장면 길이)를 알면 x_to(이동 끝 자리)·p(진행 0~1)에 씀"""
    K.STYLE = scene.get("style", "cartoon")   # "block" = 블록 인형 모양 인물
    dur = dur or scene.get("dur", 8.0)
    pr = min(1.0, max(0.0, t / max(0.1, dur)))
    bg = scene.get("bg", "white")
    o = scene.get("opt", {})
    s = BGS[bg](t, pr, o)
    for i, ch in enumerate(scene["chars"]):
        c = {**cast[ch["who"]], **ch.get("over", {})}   # over: 이 장면만 옷 바꾸기(방수 외투 등)
        sc = ch.get("scale", 0.9)
        x = ch.get("x", 960)
        foot = ch.get("y", 1000)
        q = min(1.0, pr * ch.get("speed", 1.0))
        if "x_to" in ch:
            x = x + (ch["x_to"] - x) * q
        if "y_to" in ch:
            foot = foot + (ch["y_to"] - foot) * q
        x += ch.get("dx", 0) * t
        acts = ch.get("act", ["blink", "breath"])
        if "x_to" in ch and min(1.0, pr * ch.get("speed", 1.0)) >= 1.0:
            acts = [a for a in acts if a not in ("walk", "run")]
        g = K.figure(c, ch.get("view", "front"), pose_at(acts, t, i * 1.7 + 0.3))
        op = ch.get("opacity", 1)
        s += f'<g opacity="{op}" transform="translate({x - 200 * sc:.1f},{foot - K.G * sc:.1f}) scale({sc})">{g}</g>'
    if bg in FRONT:
        s += FRONT[bg](t, pr, o)
    fx = scene.get("fx", [])
    if "rain" in fx:
        for k in range(70):
            x = (k * 137 + t * 300) % (W + 200) - 100
            y = (k * 89 + t * 1400) % H
            s += f'<line x1="{x:.0f}" y1="{y:.0f}" x2="{x - 14:.0f}" y2="{y + 40:.0f}" stroke="#c8d6e4" stroke-width="3" opacity="0.6"/>'
    if "glow" in fx:   # 고글 빛 → 화면이 하얗게 (p 끝으로 갈수록)
        s += f'<rect width="{W}" height="{H}" fill="#fff6d0" opacity="{min(0.9, pr ** 2 * 1.1):.2f}"/>'
    if "past" in fx:   # 회상: 바랜 색
        s += f'<rect width="{W}" height="{H}" fill="#c8a878" opacity="0.28"/>'
    if "dark" in fx:
        s += f'<rect width="{W}" height="{H}" fill="#05070f" opacity="0.35"/>'
    if "fade_in" in fx:
        s += f'<rect width="{W}" height="{H}" fill="#000" opacity="{max(0, 1 - t / 1.2):.2f}"/>'
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">{s}</svg>'


def main():
    a = sys.argv[1:]
    scene = json.load(open(a[0], encoding="utf-8"))
    out = a[1]
    sec = float(a[a.index("--초") + 1]) if "--초" in a else 5.0
    fps = int(a[a.index("--fps") + 1]) if "--fps" in a else 24
    cast_path = scene.get("cast")
    if cast_path and not os.path.isabs(cast_path):
        cast_path = os.path.join(os.path.dirname(os.path.abspath(a[0])), cast_path)
    cast = {c["name"]: c for c in json.load(open(cast_path, encoding="utf-8"))["chars"]}
    if "--미리보기" in a:
        cairosvg.svg2png(bytestring=frame_svg(scene, cast, 0.5).encode(), write_to=a[a.index("--미리보기") + 1])
        return
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", str(fps), "-i", "-",
                           "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", out], stdin=subprocess.PIPE)
    n = int(sec * fps)
    for k in range(n):
        ff.stdin.write(cairosvg.svg2png(bytestring=frame_svg(scene, cast, k / fps).encode()))
    ff.stdin.close()
    ff.wait()
    print("만듦:", out, f"({n}장)")


if __name__ == "__main__":
    main()
