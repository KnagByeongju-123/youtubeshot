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
def bg_kitchen(t):
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
    pa = 0.35 * math.sin(t * math.pi * 2 / 1.6)
    px, py = cx + 85 * math.sin(pa), cy + 60 + 85 * math.cos(pa)
    s += f'<line x1="{cx}" y1="{cy + 60}" x2="{px:.1f}" y2="{py:.1f}" stroke="#c9a227" stroke-width="4"/>' + K.E(px, py, 14, 14, "#c9a227", 4)
    # 무쇠 난로 + 냄비 + 김
    sx, sy = 260, 560
    s += R(sx, sy, 300, 240, "#2f2f33", 6, 'rx="10"') + R(sx - 20, sy - 30, 340, 34, "#3d3d42", 6, 'rx="6"')
    s += R(sx + 260 - 10, 0, 40, sy - 30, "#3d3d42", 5)
    fl = 0.75 + 0.25 * math.sin(t * 17) * math.sin(t * 7.3)
    s += R(sx + 60, sy + 90, 180, 110, "#1a1a1a", 5, 'rx="8"')
    s += K.P(f"M{sx + 80},{sy + 195} Q{sx + 110},{sy + 195 - 70 * fl} {sx + 150},{sy + 150} Q{sx + 175},{sy + 195 - 85 * fl} {sx + 220},{sy + 195} Z", "#f39c32", 3)
    s += K.P(f"M{sx + 115},{sy + 195} Q{sx + 140},{sy + 195 - 40 * fl} {sx + 185},{sy + 195} Z", "#ffd76a", 0)
    s += R(sx + 60, sy - 110, 170, 85, "#5a5f66", 5, 'rx="12"')
    for i in range(3):   # 김
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


BGS = {"kitchen": bg_kitchen, "white": lambda t: R(0, 0, W, H, "#ffffff", 0)}
FRONT = {"kitchen": bg_table}


# ───────────────────────── 움직임 ─────────────────────────
def pose_at(acts, t, seed):
    p = {}
    if "breath" in acts:
        p["breath"] = 0.008 * math.sin(t * 2 * math.pi / 3.6 + seed)
    if "blink" in acts:   # 3~4초마다 0.12초
        per = 3.2 + (seed % 3) * 0.4
        p["blink"] = (t + seed * 0.7) % per < 0.12
    if "talk" in acts:
        v = abs(math.sin(t * 11 + seed)) * (0.5 + 0.5 * math.sin(t * 3.1))
        p["talk"] = v
    if "stir" in acts:
        p["arm"] = 90 + 9 * math.sin(t * 2 * math.pi / 1.4)
        p["arm_l"] = 0
    if "wave" in acts:
        p["arm_r"] = 140 + 18 * math.sin(t * 2 * math.pi / 0.6)
    if "walk" in acts:
        p["walk"] = t * 2 * math.pi / 0.9
        p["bob"] = -6 * abs(math.sin(t * 2 * math.pi / 0.9))
    return p


def frame_svg(scene, cast, t):
    bg = scene.get("bg", "white")
    s = BGS[bg](t)
    for i, ch in enumerate(scene["chars"]):
        c = cast[ch["who"]]
        sc = ch.get("scale", 0.9)
        x = ch.get("x", 960) + ch.get("dx", 0) * t
        foot = ch.get("y", 1000)
        acts = ch.get("act", ["blink", "breath"])
        g = K.figure(c, ch.get("view", "front"), pose_at(acts, t, i * 1.7 + 0.3))
        s += f'<g transform="translate({x - 200 * sc:.1f},{foot - K.G * sc:.1f}) scale({sc})">{g}</g>'
        if ch.get("prop") == "ladle":   # 국자 (젓는 손)
            pass
    if bg in FRONT:
        s += FRONT[bg](t)
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
