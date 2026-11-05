"""카툰 캐릭터 시트 — AI 없이 코드로 그리는 인물 (앞·옆·옆·뒤 4장, 전신, 흰 배경)
python 카툰캐릭터.py <인물.json> <결과폴더> [--이름 A,B]
  - 인물.json = {"chars": [{name, height, build..., colors...}, ...]} (설정 이름은 아래 DEFAULT 참고)
  - 같은 설정이면 언제나 똑같은 모습 → 장면마다 얼굴이 바뀌지 않음
  - 특징 만들기: ① 몸 모양(키·어깨·배) ② 대표 색 하나(sig) ③ 머리 모양 ④ 소품(모자·안경·앞치마·넥타이·목도리)
  - 결과: <결과폴더>/<name>.png (1600×900), 그리고 _모두.png (여러 명을 한 장에)
"""
import json
import math
import os
import sys

import cairosvg

OUT = "#2a2522"      # 외곽선 색
LW = 5               # 외곽선 굵기
VW, VH = 400, 900    # 한 방향 그림 칸
G = 860              # 땅 높이

DEFAULT = {
    "height": 720,        # 전체 키(px, 칸 높이 900)
    "head": 0.22,         # 키에 대한 머리 높이 비율 (클수록 귀여움)
    "head_w": 0.86,       # 머리 너비 / 높이
    "shoulder": 70,       # 어깨 반폭
    "waist": 58,          # 허리(배) 반폭 — 어깨보다 크면 배가 나옴
    "hip": 56,            # 엉덩이 반폭
    "torso": 0.33,        # 키에 대한 몸통 길이
    "leg_w": 30, "arm_w": 24,
    "skin": "#f2c9a5", "hair": "#2b2b2b", "hair_style": "crew",
    "top": "#3d5a80", "top_type": "jacket", "bottom": "#55565b", "shoes": "#3a2a22",
    "sig": None,          # 대표 색 (넥타이·목도리·앞치마·모자 등 소품 색)
    "eyes": "dot", "brows": 1.0, "mouth": "flat",
    "wrinkles": False, "mustache": False, "glasses": False, "blush": False,
    "cap": False, "aviator": False, "coat_len": 0, "beard": False, "braces": False, "double": False, "tie": False, "apron": False, "scarf": False, "lanyard": False,
}


def shade(hexc, f):
    """색을 어둡게(f<1)·밝게(f>1)"""
    hexc = hexc.lstrip("#")
    r, g, b = (int(hexc[i:i + 2], 16) for i in (0, 2, 4))
    if f < 1:
        r, g, b = (int(c * f) for c in (r, g, b))
    else:
        r, g, b = (int(c + (255 - c) * (f - 1)) for c in (r, g, b))
    return "#%02x%02x%02x" % (r, g, b)


def P(d, fill, sw=LW, extra=""):
    st = "" if 'stroke="' in extra else f'stroke="{OUT}"'
    return f'<path d="{d}" fill="{fill}" {st} stroke-width="{sw}" stroke-linejoin="round" stroke-linecap="round" {extra}/>'


def E(cx, cy, rx, ry, fill, sw=LW, extra=""):
    st = "" if 'stroke="' in extra else f'stroke="{OUT}"'
    return f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{rx:.1f}" ry="{ry:.1f}" fill="{fill}" {st} stroke-width="{sw}" {extra}/>'


def LIMB(x1, y1, x2, y2, w, fill):
    """외곽선 있는 굵은 팔·다리 (어두운 굵은 선 위에 색 선)"""
    return (f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{OUT}" stroke-width="{w + 2 * LW}" stroke-linecap="round"/>'
            f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{fill}" stroke-width="{w}" stroke-linecap="round"/>')


def LINE(x1, y1, x2, y2, sw=LW * 0.8, col=OUT):
    return f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{col}" stroke-width="{sw}" stroke-linecap="round"/>'


class Body:
    def __init__(s, c):
        s.c = c
        H = c["height"]
        s.hh = H * c["head"]
        s.hw = s.hh * c["head_w"] / 2      # 머리 반폭
        s.top = G - H
        s.hcy = s.top + s.hh / 2           # 머리 가운데
        s.sy = s.top + s.hh * 1.04         # 어깨 높이
        s.hy = s.sy + H * c["torso"]       # 엉덩이 높이
        s.handy = s.sy + H * 0.37          # 손 높이
        s.cx = VW / 2



def anime_eye(px, ey, rx, ry, iris, side=False):
    """레트로 애니 눈: 큰 흰자 + 진한 눈동자 + 반짝이 + 굵은 윗눈썹선"""
    s = E(px, ey, rx, ry, "#ffffff", LW * 0.7)
    ix = px + (rx * 0.35 if side else 0)
    s += E(ix, ey + ry * 0.12, rx * (0.55 if side else 0.68), ry * 0.78, iris, 0)
    s += E(ix, ey + ry * 0.18, rx * 0.3, ry * 0.4, "#111111", 0)
    s += E(ix - rx * 0.22, ey - ry * 0.25, rx * 0.2, ry * 0.18, "#ffffff", 0)
    s += E(ix + rx * 0.2, ey + ry * 0.4, rx * 0.09, ry * 0.08, "#ffffff", 0)
    s += P(f"M{px - rx * 1.1},{ey - ry * 0.2} Q{px},{ey - ry * 1.35} {px + rx * 1.15},{ey - ry * 0.35}", "none", LW * 1.4)
    return s


def spikes(cx, cy, rx, ry, a0, a1, n, length, col, base=0.22):
    """머리 둘레(타원)에 바깥으로 삐친 머리카락 송곳 n개 (각도 a0→a1, 도)"""
    s = ""
    for i in range(n):
        a = math.radians(a0 + (a1 - a0) * (i + 0.5) / n)
        da = math.radians((a1 - a0) / n) * base * 2.2
        p1 = (cx + math.cos(a - da) * rx, cy + math.sin(a - da) * ry)
        p2 = (cx + math.cos(a + da) * rx, cy + math.sin(a + da) * ry)
        L = length * (0.8 + 0.4 * ((i * 37) % 5) / 4)
        tip = (cx + math.cos(a + da * 0.6) * (rx + L), cy + math.sin(a + da * 0.6) * (ry + L))
        s += P(f"M{p1[0]:.1f},{p1[1]:.1f} L{tip[0]:.1f},{tip[1]:.1f} L{p2[0]:.1f},{p2[1]:.1f} Z", col, LW * 0.8)
    return s


def fringe(x, t, hw, hh, col, n=5, depth=0.36):
    """이마로 내려온 뾰족 앞머리"""
    s = ""
    for i in range(n):
        x0 = x - hw * 0.95 + i * hw * 1.9 / n
        x1 = x0 + hw * 1.9 / n
        tx = x0 + (x1 - x0) * (0.3 if i < n / 2 else 0.7)
        d = depth * (0.85 + 0.3 * ((i * 3) % 4) / 3)
        s += P(f"M{x0 - 4:.1f},{t + hh * 0.12:.1f} L{tx:.1f},{t + hh * d:.1f} L{x1 + 4:.1f},{t + hh * 0.12:.1f} Z", col, LW * 0.8)
    return s


def aviator_front(b, x, back=False):
    """가죽 비행 모자 + 귀 덮개 + 이마 위 고글"""
    c, hw, hh, cy = b.c, b.hw, b.hh, b.hcy
    t = cy - hh / 2
    col = c["aviator"] if isinstance(c["aviator"], str) else "#8a5a32"
    s = ""
    for sgn in (-1, 1):   # 귀 덮개
        s += P(f"M{x + sgn * hw * 0.8},{cy - hh * 0.15} Q{x + sgn * hw * 1.18},{cy - hh * 0.1} {x + sgn * hw * 1.12},{cy + hh * 0.22} "
               f"Q{x + sgn * hw * 1.05},{cy + hh * 0.33} {x + sgn * hw * 0.86},{cy + hh * 0.3} Z", col)
        s += LINE(x + sgn * hw * 1.0, cy + hh * 0.3, x + sgn * hw * 0.9, cy + hh * 0.5, 4, shade(col, 0.6))
    s += P(f"M{x - hw * 1.08},{cy - hh * 0.02} C{x - hw * 1.12},{t - hh * 0.2} {x + hw * 1.12},{t - hh * 0.2} {x + hw * 1.08},{cy - hh * 0.02} "
           f"Q{x},{t + hh * (0.2 if not back else 0.5)} {x - hw * 1.08},{cy - hh * 0.02} Z", col)
    s += P(f"M{x - hw * 0.1},{t - hh * 0.05} Q{x},{t + hh * 0.1} {x + hw * 0.1},{t + hh * 0.22}", "none", 3, f'stroke="{shade(col, 0.6)}"')
    by = t + hh * 0.13
    s += P(f"M{x - hw * 1.06},{by + hh * 0.06} Q{x},{by - hh * 0.06} {x + hw * 1.06},{by + hh * 0.06}", "none", 11, f'stroke="{OUT}"')
    s += P(f"M{x - hw * 1.06},{by + hh * 0.06} Q{x},{by - hh * 0.06} {x + hw * 1.06},{by + hh * 0.06}", "none", 6, 'stroke="#3b3b3b"')
    if not back:
        for sgn in (-1, 1):
            gx = x + sgn * hw * 0.36
            s += E(gx, by, hw * 0.3, hh * 0.1, "#c9a227", LW * 0.9)
            s += E(gx, by, hw * 0.21, hh * 0.07, "#7fc8d8", 3)
            s += E(gx - hw * 0.07, by - hh * 0.025, hw * 0.06, hh * 0.02, "#ffffff", 0)
    return s


def coat_skirt_front(b, x, back=False):
    c = b.c
    ky = b.hy + (G - b.hy) * c["coat_len"]
    hp = max(c["hip"], c["waist"]) + 6
    s = P(f"M{x - hp},{b.hy - 30} L{x + hp},{b.hy - 30} L{x + hp + 26},{ky} Q{x},{ky + 10} {x - hp - 26},{ky} Z", c["top"])
    s += P(f"M{x + hp * 0.3},{b.hy - 20} L{x + hp + 22},{ky - 4} L{x + hp + 26},{ky} L{x + hp},{b.hy - 30} Z", "#000000", 0, 'opacity="0.14"')
    if back:
        s += LINE(x, b.hy + 20, x, ky + 4, 3.5)
    else:
        s += P(f"M{x - 4},{b.hy - 30} L{x - 16},{ky + 6} L{x + 16},{ky + 6} L{x + 4},{b.hy - 30} Z", shade(c["bottom"], 0.9), 3)
    return s


def coat_skirt_side(b, x, d, belly):
    c = b.c
    ky = b.hy + (G - b.hy) * c["coat_len"]
    return P(f"M{x - d - 2},{b.hy - 30} L{x + d + belly * 0.5},{b.hy - 30} L{x + d + 22},{ky} L{x - d - 30},{ky + 4} Z", c["top"]) + \
        LINE(x - d - 4, b.hy + 10, x - d - 22, ky, 3, shade(c["top"], 0.6))


# ───────────────────────── 앞·뒤 ─────────────────────────
def torso_front(b, x):
    c = b.c
    sw, ww, hp, sy, hy = c["shoulder"], c["waist"], c["hip"], b.sy, b.hy
    my = (sy + hy) / 2 + 10
    return (f"M{x - sw + 14},{sy} L{x + sw - 14},{sy} Q{x + sw + 2},{sy} {x + sw},{sy + 22} "
            f"C{x + sw + 2},{sy + 60} {x + ww + 4},{my - 30} {x + ww},{my} "
            f"C{x + ww - 2},{my + 40} {x + hp + 2},{hy - 20} {x + hp},{hy} "
            f"L{x - hp},{hy} C{x - hp - 2},{hy - 20} {x - ww + 2},{my + 40} {x - ww},{my} "
            f"C{x - ww - 4},{my - 30} {x - sw - 2},{sy + 60} {x - sw},{sy + 22} Q{x - sw - 2},{sy} {x - sw + 14},{sy} Z")


def hair_front(b, x, back=False):
    """머리카락: (뒤에 그릴 것, 앞에 그릴 것) SVG"""
    c, hw, hh, cy = b.c, b.hw, b.hh, b.hcy
    st, col = c["hair_style"], c["hair"]
    t = cy - hh / 2
    behind, front = "", ""
    if st == "perm":   # 뽀글 파마: 동그라미 송이
        dots = []
        for i in range(11):
            a = math.pi * (0.95 + i * 1.1 / 10)
            dots.append((x + math.cos(a) * hw * 1.0, cy + math.sin(a) * hh * 0.5 - hh * 0.05))
        for i in range(5):
            dots.append((x - hw * 0.55 + i * hw * 0.275, t + hh * 0.06))
        if back:
            r0 = hw * 0.3
            fill = E(x, cy - hh * 0.02, hw * 1.08, hh * 0.47, col, LW * 0.8)
            for i in range(4):
                dots.append((x - hw * 0.5 + i * hw * 0.33, cy - hh * 0.12))
            for i in range(3):
                dots.append((x - hw * 0.35 + i * hw * 0.35, cy + hh * 0.12))
            front = fill
        r = hw * 0.3
        front = (front if back else "") + "".join(E(px, py, r, r * 0.92, col, LW * 0.8) for px, py in dots)
        front += "".join(E(px - r * 0.25, py - r * 0.3, r * 0.25, r * 0.15, shade(col, 1.35), 0) for px, py in dots[::2])
        behind = E(x, cy - hh * 0.1, hw * 1.15, hh * 0.5, col, LW * 0.8)
        return behind, front
    if st == "bald":   # 대머리 + 옆머리
        for sgn in (-1, 1):
            front += P(f"M{x + sgn * hw * 0.98},{cy - hh * 0.12} Q{x + sgn * hw * 1.12},{cy + hh * 0.05} {x + sgn * hw * 0.92},{cy + hh * 0.2} "
                       f"Q{x + sgn * hw * 0.85},{cy} {x + sgn * hw * 0.98},{cy - hh * 0.12} Z", col, LW * 0.8)
        if back:
            front += P(f"M{x - hw * 0.98},{cy - hh * 0.05} Q{x},{cy + hh * 0.12} {x + hw * 0.98},{cy - hh * 0.05} "
                       f"Q{x + hw * 0.9},{cy + hh * 0.25} {x},{cy + hh * 0.3} Q{x - hw * 0.9},{cy + hh * 0.25} {x - hw * 0.98},{cy - hh * 0.05} Z", col, LW * 0.8)
        front += E(x - hw * 0.3, t + hh * 0.14, hw * 0.22, hh * 0.05, "#ffffff", 0, 'opacity="0.55"')  # 반짝
        return behind, front
    if st == "spiky":   # 삐죽삐죽 머리 (레트로 애니 소년)
        behind = spikes(x, cy - hh * 0.08, hw * 0.95, hh * 0.45, 150, 390, 9, hh * 0.22, col)
        if back:
            behind += spikes(x, cy + hh * 0.05, hw * 0.8, hh * 0.38, 40, 140, 4, hh * 0.15, col)
            front = P(f"M{x - hw * 1.05},{cy + hh * 0.15} C{x - hw * 1.12},{t - hh * 0.14} {x + hw * 1.12},{t - hh * 0.14} {x + hw * 1.05},{cy + hh * 0.15} "
                      f"L{x + hw * 0.6},{cy + hh * 0.42} L{x + hw * 0.3},{cy + hh * 0.3} L{x},{cy + hh * 0.45} L{x - hw * 0.3},{cy + hh * 0.3} L{x - hw * 0.6},{cy + hh * 0.42} Z", col)
        else:
            front = P(f"M{x - hw * 1.05},{cy + hh * 0.05} C{x - hw * 1.12},{t - hh * 0.14} {x + hw * 1.12},{t - hh * 0.14} {x + hw * 1.05},{cy + hh * 0.05} "
                      f"L{x + hw * 0.9},{t + hh * 0.2} L{x - hw * 0.9},{t + hh * 0.2} Z", col)
            front += fringe(x, t, hw, hh, col)
            for sgn in (-1, 1):   # 구레나룻
                front += P(f"M{x + sgn * hw * 1.05},{cy - hh * 0.12} L{x + sgn * hw * 1.0},{cy + hh * 0.2} L{x + sgn * hw * 0.86},{cy - hh * 0.05} Z", col, LW * 0.8)
        return behind, front
    fr = {"crew": 0.18, "slick": 0.12, "bob": 0.3, "bun": 0.16, "long": 0.28}.get(st, 0.2)
    if back:
        front = P(f"M{x - hw * 1.04},{cy + hh * (0.1 if st != 'crew' else -0.05)} C{x - hw * 1.12},{t - hh * 0.12} {x + hw * 1.12},{t - hh * 0.12} "
                  f"{x + hw * 1.04},{cy + hh * (0.1 if st != 'crew' else -0.05)} Q{x},{cy + hh * 0.32} {x - hw * 1.04},{cy + hh * (0.1 if st != 'crew' else -0.05)} Z", col)
    else:
        lift = hh * 0.02
        if st == "slick":   # 올백 + 가르마
            front = P(f"M{x - hw * 1.03},{cy - hh * 0.02} C{x - hw * 1.1},{t - hh * 0.14} {x + hw * 1.1},{t - hh * 0.14} {x + hw * 1.03},{cy - hh * 0.02} "
                      f"Q{x + hw * 0.7},{t + hh * 0.2} {x + hw * 0.2},{t + hh * 0.16} Q{x - hw * 0.6},{t + hh * 0.13} {x - hw * 1.03},{cy - hh * 0.02} Z", col)
            front += P(f"M{x - hw * 0.35},{t + hh * 0.03} Q{x - hw * 0.1},{t - hh * 0.01} {x + hw * 0.5},{t + hh * 0.06}", "none", LW * 0.6,
                       f'stroke="{shade(col, 1.6)}"')
        else:
            front = P(f"M{x - hw * 1.04},{cy + lift} C{x - hw * 1.12},{t - hh * 0.12} {x + hw * 1.12},{t - hh * 0.12} {x + hw * 1.04},{cy + lift} "
                      f"Q{x + hw * 0.8},{t + hh * (fr + 0.05)} {x + hw * 0.3},{t + hh * fr} Q{x - hw * 0.1},{t + hh * (fr + 0.08)} {x - hw * 0.45},{t + hh * fr} "
                      f"Q{x - hw * 0.85},{t + hh * (fr + 0.05)} {x - hw * 1.04},{cy + lift} Z", col)
    if st == "bob":
        for sgn in (-1, 1):
            behind += P(f"M{x + sgn * hw * 1.02},{cy - hh * 0.1} Q{x + sgn * hw * 1.2},{cy + hh * 0.3} {x + sgn * hw * 0.95},{cy + hh * 0.48} "
                        f"L{x + sgn * hw * 0.5},{cy + hh * 0.45} Z", col)
        if back:
            front = P(f"M{x - hw * 1.08},{cy + hh * 0.1} C{x - hw * 1.14},{t - hh * 0.14} {x + hw * 1.14},{t - hh * 0.14} {x + hw * 1.08},{cy + hh * 0.1} "
                      f"L{x + hw * 1.0},{cy + hh * 0.5} L{x - hw * 1.0},{cy + hh * 0.5} Z", col)
    if st == "bun":
        behind += E(x, t - hh * 0.02, hw * 0.38, hh * 0.15, col)
    if st == "long":
        behind += P(f"M{x - hw * 1.05},{cy - hh * 0.2} L{x - hw * 1.2},{b.sy + 80} L{x + hw * 1.2},{b.sy + 80} L{x + hw * 1.05},{cy - hh * 0.2} Z", col)
    return behind, front


def face_front(b, x, pose=None):
    pose = pose or {}
    c, hw, hh, cy = b.c, b.hw, b.hh, b.hcy
    s = ""
    c = {**c, "eyes": "closed"} if pose.get("blink") else c
    ey = cy + hh * 0.05
    ex = hw * 0.38
    for sgn in (-1, 1):
        px = x + sgn * ex
        if c["eyes"] == "closed":   # 눈 감음 (깜빡임)
            s += P(f"M{px - hw * 0.13},{ey} Q{px},{ey + hh * 0.04} {px + hw * 0.13},{ey}", "none", LW * 0.9)
        elif c["eyes"] == "anime":
            s += anime_eye(px, ey, hw * 0.2, hh * 0.12, c.get("iris", "#5a3a22"))
        elif c["eyes"] == "dot":
            s += E(px, ey, hw * 0.08, hh * 0.055, OUT, 0)
            s += E(px + hw * 0.03, ey - hh * 0.02, hw * 0.025, hw * 0.025, "#ffffff", 0)
        elif c["eyes"] == "smile":   # 웃는 눈 (반달)
            s += P(f"M{px - hw * 0.12},{ey + hh * 0.01} Q{px},{ey - hh * 0.06} {px + hw * 0.12},{ey + hh * 0.01}", "none", LW * 0.9)
        elif c["eyes"] == "sharp":   # 날카로운 눈 (가늘고 올라감)
            s += P(f"M{px - sgn * hw * 0.13},{ey + hh * 0.02} L{px + sgn * hw * 0.13},{ey - hh * 0.03} L{px + sgn * hw * 0.02},{ey + hh * 0.03} Z", OUT, 2)
        elif c["eyes"] == "tired":   # 처진 눈
            s += P(f"M{px - hw * 0.11},{ey - hh * 0.01} Q{px},{ey + hh * 0.04} {px + hw * 0.11},{ey - hh * 0.01}", "none", LW * 0.9)
            s += E(px, ey + hh * 0.008, hw * 0.05, hh * 0.025, OUT, 0)
        # 눈썹
        bw = LW * 1.1 * c["brows"]
        by = ey - hh * (0.11 if c["eyes"] != "anime" else 0.2)
        if c["eyes"] == "anime":
            s += P(f"M{px - sgn * hw * 0.2},{by + hh * 0.03} L{px + sgn * hw * 0.22},{by - hh * 0.03} L{px + sgn * hw * 0.24},{by + hh * 0.0} L{px - sgn * hw * 0.18},{by + hh * 0.055} Z", OUT, 2)
        elif c["eyes"] == "sharp":
            s += LINE(px - sgn * hw * 0.16, by - hh * 0.03, px + sgn * hw * 0.14, by + hh * 0.02, bw)
        elif c["eyes"] == "tired":
            s += LINE(px - sgn * hw * 0.15, by + hh * 0.02, px + sgn * hw * 0.14, by - hh * 0.02, bw)
        else:
            s += P(f"M{px - hw * 0.15},{by + hh * 0.01} Q{px},{by - hh * 0.03} {px + hw * 0.15},{by + hh * 0.01}", "none", bw,
                   f'stroke="{shade(c["hair"], 0.8) if c["hair_style"] != "bald" else OUT}"')
        if c["blush"]:
            s += E(px + sgn * hw * 0.05, ey + hh * 0.13, hw * 0.13, hh * 0.04, "#f08a7a", 0, 'opacity="0.45"')
        if c["wrinkles"]:
            s += LINE(px + sgn * hw * 0.17, ey - hh * 0.01, px + sgn * hw * 0.25, ey + hh * 0.03, 2.5)
            s += LINE(px + sgn * hw * 0.17, ey + hh * 0.025, px + sgn * hw * 0.24, ey + hh * 0.06, 2.5)
    if c["wrinkles"]:
        s += LINE(x - hw * 0.25, cy - hh * 0.17, x + hw * 0.25, cy - hh * 0.17, 2.5)
        s += P(f"M{x - hw * 0.4},{cy + hh * 0.18} Q{x - hw * 0.45},{cy + hh * 0.27} {x - hw * 0.33},{cy + hh * 0.33}", "none", 2.5)
        s += P(f"M{x + hw * 0.4},{cy + hh * 0.18} Q{x + hw * 0.45},{cy + hh * 0.27} {x + hw * 0.33},{cy + hh * 0.33}", "none", 2.5)
    # 코
    s += P(f"M{x - hw * 0.02},{cy + hh * 0.1} Q{x + hw * 0.1},{cy + hh * 0.2} {x - hw * 0.05},{cy + hh * 0.22}", "none", LW * 0.7)
    my = cy + hh * 0.31
    if c["beard"]:
        bc = c["beard"] if isinstance(c["beard"], str) else c["hair"]
        s += P(f"M{x - hw * 0.98},{cy + hh * 0.02} Q{x - hw * 0.95},{cy + hh * 0.42} {x - hw * 0.45},{cy + hh * 0.58} Q{x},{cy + hh * 0.72} {x + hw * 0.45},{cy + hh * 0.58} "
               f"Q{x + hw * 0.95},{cy + hh * 0.42} {x + hw * 0.98},{cy + hh * 0.02} Q{x + hw * 0.7},{cy + hh * 0.22} {x + hw * 0.35},{my - hh * 0.04} "
               f"Q{x},{my - hh * 0.09} {x - hw * 0.35},{my - hh * 0.04} Q{x - hw * 0.7},{cy + hh * 0.22} {x - hw * 0.98},{cy + hh * 0.02} Z", bc)
        s += E(x, my + hh * 0.005, hw * 0.2, hh * 0.045, c["skin"], 0)
    if c["mustache"]:
        s += P(f"M{x},{my - hh * 0.05} C{x - hw * 0.15},{my - hh * 0.09} {x - hw * 0.38},{my - hh * 0.06} {x - hw * 0.4},{my + hh * 0.01} "
               f"Q{x - hw * 0.2},{my - hh * 0.01} {x},{my - hh * 0.02} Q{x + hw * 0.2},{my - hh * 0.01} {x + hw * 0.4},{my + hh * 0.01} "
               f"C{x + hw * 0.38},{my - hh * 0.06} {x + hw * 0.15},{my - hh * 0.09} {x},{my - hh * 0.05} Z", c["hair"] if c["hair_style"] != "bald" else "#9a9a9a", 3)
        my += hh * 0.035
    m = c["mouth"]
    if pose.get("talk", 0) > 0.15:   # 말하는 입 (열림 정도 0~1)
        o = pose["talk"]
        s += E(x, my + hh * 0.01, hw * (0.12 + 0.06 * o), hh * (0.02 + 0.05 * o), "#6b2a24", LW * 0.7)
    elif m == "smile":
        s += P(f"M{x - hw * 0.22},{my - hh * 0.02} Q{x},{my + hh * 0.09} {x + hw * 0.22},{my - hh * 0.02} Q{x},{my + hh * 0.02} {x - hw * 0.22},{my - hh * 0.02} Z", "#8c3b32", 3)
    elif m == "frown":
        s += P(f"M{x - hw * 0.18},{my + hh * 0.03} Q{x},{my - hh * 0.04} {x + hw * 0.18},{my + hh * 0.03}", "none", LW * 0.8)
    elif m == "smirk":
        s += P(f"M{x - hw * 0.18},{my + hh * 0.01} Q{x + hw * 0.05},{my + hh * 0.02} {x + hw * 0.22},{my - hh * 0.04}", "none", LW * 0.8)
    else:
        s += LINE(x - hw * 0.15, my, x + hw * 0.15, my, LW * 0.8)
    if c["glasses"]:
        gy = ey
        for sgn in (-1, 1):
            s += f'<rect x="{x + sgn * ex - hw * 0.22:.1f}" y="{gy - hh * 0.08:.1f}" width="{hw * 0.44:.1f}" height="{hh * 0.15:.1f}" rx="6" fill="#ffffff" fill-opacity="0.25" stroke="{c.get("glasses_col", OUT)}" stroke-width="{LW * 0.8}"/>'
        s += LINE(x - ex + hw * 0.22, gy - hh * 0.02, x + ex - hw * 0.22, gy - hh * 0.02, LW * 0.8, c.get("glasses_col", OUT))
    return s


def cap_front(b, x, back=False):
    c, hw, hh, cy = b.c, b.hw, b.hh, b.hcy
    t = cy - hh / 2
    col = c["cap"] if isinstance(c["cap"], str) else c["sig"] or "#333a55"
    s = P(f"M{x - hw * 1.05},{t + hh * 0.22} C{x - hw * 1.05},{t - hh * 0.18} {x + hw * 1.05},{t - hh * 0.18} {x + hw * 1.05},{t + hh * 0.22} Z", col)
    s += f'<rect x="{x - hw * 1.08:.1f}" y="{t + hh * 0.14:.1f}" width="{hw * 2.16:.1f}" height="{hh * 0.1:.1f}" rx="5" fill="{shade(col, 0.6)}" stroke="{OUT}" stroke-width="{LW}"/>'
    if not back:
        s += P(f"M{x - hw * 0.95},{t + hh * 0.24} Q{x},{t + hh * 0.38} {x + hw * 0.95},{t + hh * 0.24} Z", shade(col, 0.45))
        s += E(x, t + hh * 0.06, hw * 0.14, hh * 0.06, "#e3b341", 3)   # 모자 휘장
    return s


def view_front(c, back=False, pose=None):
    pose = pose or {}
    b = Body(c)
    x = b.cx
    s = ""
    hw, hh = b.hw, b.hh
    # 다리
    lx = c["hip"] * 0.5
    for sgn in (-1, 1):
        s += LIMB(x + sgn * lx, b.hy - 14, x + sgn * lx * 1.05, G - 22, c["leg_w"], c["bottom"])
    s += f'<rect x="{x - c["hip"] * 0.5 - c["leg_w"] / 2:.1f}" y="{b.hy - 20:.1f}" width="{c["hip"] + c["leg_w"]:.1f}" height="40" fill="{c["bottom"]}"/>'
    # 신발
    for sgn in (-1, 1):
        s += P(f"M{x + sgn * lx * 1.05 - c['leg_w'] * 0.75},{G - 6} Q{x + sgn * lx * 1.05 - c['leg_w'] * 0.75},{G - 30} {x + sgn * lx * 1.05},{G - 30} "
               f"Q{x + sgn * lx * 1.05 + c['leg_w'] * 0.8},{G - 30} {x + sgn * lx * 1.05 + c['leg_w'] * 0.8},{G - 6} Z", c["shoes"])
    if c["coat_len"]:
        s += coat_skirt_front(b, x, back)
    hb, hf = hair_front(b, x, back)
    if back:
        s += hb if c["hair_style"] != "long" else ""
    else:
        s += hb
    # 팔(몸통 뒤쪽 어깨에서)
    arms = ""
    for sgn in (-1, 1):
        ax = x + sgn * (c["shoulder"] - c["arm_w"] * 0.35)
        hx = x + sgn * (max(c["shoulder"], c["waist"]) + c["arm_w"] * 0.3)
        hy_ = b.handy - 8
        ang = pose.get("arm_r" if sgn > 0 else "arm_l", 0)   # 팔 올림 각도(도, 바깥쪽으로)
        if ang:
            vx, vy = hx - ax, hy_ - (b.sy + 16)
            r_ = -math.radians(ang) * sgn
            vx, vy = vx * math.cos(r_) - vy * math.sin(r_), vx * math.sin(r_) + vy * math.cos(r_)
            hx, hy_ = ax + vx, b.sy + 16 + vy
        arms += LIMB(ax, b.sy + 16, hx, hy_, c["arm_w"], c["top"])
        arms += E(hx, hy_ + 12, c["arm_w"] * 0.55, c["arm_w"] * 0.62, c["skin"])
    # 목
    s += LIMB(x, b.sy - 30, x, b.sy + 4, hw * 0.55, c["skin"])
    # 몸통
    s += P(torso_front(b, x), c["top"])
    # 그늘(오른쪽)
    s += P(f"M{x + c['shoulder'] * 0.55},{b.sy + 4} Q{x + max(c['waist'], c['shoulder']) * 1.02},{(b.sy + b.hy) / 2} {x + c['hip'] * 0.7},{b.hy - 3} "
           f"L{x + c['hip'] - 4},{b.hy - 3} Q{x + max(c['waist'], c['shoulder']) + 2},{(b.sy + b.hy) / 2} {x + c['shoulder'] - 4},{b.sy + 8} Z",
           "#000000", 0, 'opacity="0.14"')
    s += f'<line x1="{x - c["hip"]}" y1="{b.hy - 2}" x2="{x + c["hip"]}" y2="{b.hy - 2}" stroke="{OUT}" stroke-width="{LW}"/>'
    tt = c["top_type"]
    if not back:
        if tt in ("jacket", "cardigan", "uniform"):
            vy = b.sy + (b.hy - b.sy) * (0.42 if tt != "cardigan" else 0.5)
            s += P(f"M{x - hw * 0.42},{b.sy} L{x},{vy} L{x + hw * 0.42},{b.sy} Z", c.get("shirt", "#f4f1ea"), LW * 0.8)
            if c["tie"]:
                tc = c["sig"] or "#b23a3a"
                s += P(f"M{x - 8},{b.sy + 4} L{x + 8},{b.sy + 4} L{x + 5},{b.sy + 18} L{x + 13},{vy - 4} L{x},{vy + 10} L{x - 13},{vy - 4} L{x - 5},{b.sy + 18} Z", tc, 3)
            s += P(f"M{x - hw * 0.42},{b.sy} L{x - 16},{vy - 6} L{x - 30},{b.sy + 40} Z", shade(c["top"], 0.75), 3)
            s += P(f"M{x + hw * 0.42},{b.sy} L{x + 16},{vy - 6} L{x + 30},{b.sy + 40} Z", shade(c["top"], 0.75), 3)
            s += LINE(x, vy, x, b.hy - 4, 3)
            for i in range(2 if tt != "cardigan" else 3):
                s += E(x + 8, vy + 18 + i * 32, 4, 4, c.get("button", "#d9c27a"), 2)
            if tt == "uniform":   # 경비복: 가슴 주머니 + 어깨 견장
                for sgn in (-1, 1):
                    s += f'<rect x="{x + sgn * c["shoulder"] * 0.55 - 15:.1f}" y="{b.sy + 52:.1f}" width="30" height="24" rx="3" fill="{shade(c["top"], 0.8)}" stroke="{OUT}" stroke-width="3"/>'
                s += f'<rect x="{x - c["shoulder"] * 0.55 - 11:.1f}" y="{b.sy + 42:.1f}" width="22" height="7" fill="#e3b341" stroke="{OUT}" stroke-width="2"/>'
        else:   # 셔츠·티: 동그란 깃
            s += P(f"M{x - hw * 0.45},{b.sy + 1} Q{x},{b.sy + 34} {x + hw * 0.45},{b.sy + 1}", "none", LW * 0.8)
    else:
        s += P(f"M{x - hw * 0.5},{b.sy + 2} Q{x},{b.sy + 14} {x + hw * 0.5},{b.sy + 2}", "none", LW * 0.8)
        s += LINE(x, b.sy + 60, x, b.hy - 6, 2.5, shade(c["top"], 0.6))
    if c["apron"]:
        ac = c["sig"] or "#c0392b"
        if not back:
            s += P(f"M{x - c['waist'] * 0.72},{b.sy + 30} L{x + c['waist'] * 0.72},{b.sy + 30} L{x + c['hip'] * 0.95},{b.hy + 120} "
                   f"Q{x},{b.hy + 132} {x - c['hip'] * 0.95},{b.hy + 120} Z", ac)
            s += LINE(x - c["waist"] * 0.6, b.sy + 30, x - hw * 0.3, b.sy - 2, 6, OUT)
            s += LINE(x + c["waist"] * 0.6, b.sy + 30, x + hw * 0.3, b.sy - 2, 6, OUT)
            s += f'<rect x="{x - 26:.1f}" y="{b.hy + 10:.1f}" width="52" height="34" rx="4" fill="{shade(ac, 0.8)}" stroke="{OUT}" stroke-width="3"/>'
        else:
            wy = (b.sy + b.hy) / 2 + 20
            s += LINE(x - c["waist"] - 2, wy, x + c["waist"] + 2, wy, 9, ac)
            s += P(f"M{x},{wy} q-22,-16 -28,4 q16,6 28,-4 q22,-16 28,4 q-16,6 -28,-4 Z", ac, 3)
            s += LINE(x - 4, wy + 4, x - 12, wy + 46, 7, ac) + LINE(x + 4, wy + 4, x + 12, wy + 46, 7, ac)
            s += LINE(x - hw * 0.5, b.sy + 8, x + hw * 0.5, b.sy + 8, 6, ac)
    if c["braces"]:
        bc = c["sig"] or "#a83232"
        for sgn in (-1, 1):
            if back:
                s += LINE(x + sgn * c["shoulder"] * 0.45, b.sy + 2, x + sgn * 6, b.sy + 70, 7, bc) + LINE(x + sgn * 6, b.sy + 70, x + sgn * 10, b.hy - 4, 7, bc)
            else:
                s += LINE(x + sgn * c["shoulder"] * 0.45, b.sy + 2, x + sgn * c["waist"] * 0.4, b.hy - 4, 7, bc)
                s += E(x + sgn * c["waist"] * 0.4, b.hy - 8, 5, 5, "#d9c27a", 2)
    if c["double"] and not back:
        for i in range(3):
            for sgn in (-1, 1):
                s += E(x + sgn * 16, b.sy + 70 + i * 34, 4.5, 4.5, c.get("button", "#d9c27a"), 2)
    if c["lanyard"] and not back:
        s += P(f"M{x - hw * 0.45},{b.sy} L{x - 6},{b.sy + 85} M{x + hw * 0.45},{b.sy} L{x + 6},{b.sy + 85}", "none", 5, f'stroke="{c["sig"] or "#2d6cdf"}"')
        s += f'<rect x="{x - 17:.1f}" y="{b.sy + 82:.1f}" width="34" height="44" rx="4" fill="#ffffff" stroke="{OUT}" stroke-width="3"/>'
        s += f'<rect x="{x - 10:.1f}" y="{b.sy + 89:.1f}" width="20" height="16" fill="{c["sig"] or "#2d6cdf"}"/>'
    s += arms
    # 머리
    if not back:
        for sgn in (-1, 1):   # 귀
            s += E(x + sgn * hw * 0.98, b.hcy + hh * 0.06, hw * 0.16, hh * 0.1, c["skin"])
    s += E(x, b.hcy, hw, hh / 2, c["skin"])
    if not back:
        s += face_front(b, x, pose)
    if back and c["hair_style"] == "long":
        s += hb
    s += hf
    if c["scarf"]:
        sc = c["sig"] or "#c0392b"
        s += P(f"M{x - hw * 0.62},{b.sy - 18} Q{x},{b.sy + 8} {x + hw * 0.62},{b.sy - 18} L{x + hw * 0.7},{b.sy + 6} Q{x},{b.sy + 30} {x - hw * 0.7},{b.sy + 6} Z", sc)
        if not back:
            s += P(f"M{x + hw * 0.2},{b.sy + 10} L{x + hw * 0.45},{b.sy + 90} L{x + hw * 0.05},{b.sy + 92} Z", shade(sc, 0.85))
    if c["cap"]:
        s += cap_front(b, x, back)
    if c["aviator"]:
        s += aviator_front(b, x, back)
    return s


# ───────────────────────── 옆(오른쪽을 봄) ─────────────────────────
def view_side(c, pose=None):
    pose = pose or {}
    b = Body(c)
    wp = pose.get("walk")          # 걷기 위상(라디안), None 이면 서 있음
    sw_ = math.sin(wp) if wp is not None else 0.0
    x = b.cx
    s = ""
    hw, hh = b.hw, b.hh
    d = c["shoulder"] * 0.55              # 몸 두께 반
    belly = max(0, c["waist"] - c["shoulder"]) * 1.3
    # 다리 (뒤쪽 다리 조금 어둡게)
    for off, col in ((-8, shade(c["bottom"], 0.8)), (8, c["bottom"])):
        stride = (c["height"] * 0.07) * sw_ * (1 if off > 0 else -1)
        lift = max(0.0, -sw_ if off > 0 else sw_) * 10 if wp is not None else 0
        s += LIMB(x + off * 0.6, b.hy - 14, x + off * 0.6 + stride, G - 22 - lift, c["leg_w"], col)
        sx = x + off * 0.6 + stride
        G_ = G
        s += f'<g transform="translate(0,{-lift:.1f})">'
        s += P(f"M{sx - c['leg_w'] * 0.7},{G - 6} Q{sx - c['leg_w'] * 0.7},{G - 30} {sx},{G - 30} Q{sx + c['leg_w'] * 0.6},{G - 30} "
               f"{sx + c['leg_w'] * 1.0},{G - 20} Q{sx + c['leg_w'] * 1.5},{G - 14} {sx + c['leg_w'] * 1.4},{G - 6} Z", shade(c["shoes"], 0.85 if off < 0 else 1)) + "</g>"
    if c["coat_len"]:
        s += coat_skirt_side(b, x, d, belly)
    hb, hf = hair_side(b, x)
    s += hb
    s += LIMB(x - 4, b.sy - 30, x + 2, b.sy + 4, hw * 0.55, c["skin"])
    sy, hy = b.sy, b.hy
    my = (sy + hy) / 2 + 10
    body = (f"M{x - d + 6},{sy} Q{x - d - 4},{sy + 6} {x - d - 2},{sy + 40} C{x - d - 6},{my} {x - d - 4},{hy - 30} {x - d},{hy} "
            f"L{x + d - 2},{hy} C{x + d + belly * 0.6},{hy - 30} {x + d + belly},{my + 20} {x + d + belly * 0.7},{my - 20} "
            f"C{x + d + belly * 0.3},{sy + 50} {x + d + 6},{sy + 30} {x + d - 4},{sy} Z")
    s += P(body, c["top"])
    s += f'<line x1="{x - d}" y1="{hy - 2}" x2="{x + d - 2}" y2="{hy - 2}" stroke="{OUT}" stroke-width="{LW}"/>'
    if c["apron"]:
        ac = c["sig"] or "#c0392b"
        s += P(f"M{x + d + belly * 0.5 - 4},{sy + 30} C{x + d + belly + 8},{my} {x + d + belly * 0.7 + 10},{hy} {x + d + 10},{hy + 120} "
               f"L{x + d - 8},{hy + 120} L{x + d - 6},{sy + 34} Z", ac)
        wy = (sy + hy) / 2 + 20
        s += LINE(x - d - 2, wy, x + d + belly * 0.7, wy, 8, ac)
        s += P(f"M{x - d},{wy} q-20,-14 -26,4 q14,6 26,-4 Z", ac, 3)
    if c["tie"] and c["top_type"] in ("jacket", "uniform", "cardigan"):
        s += P(f"M{x + d - 6},{sy + 4} L{x + d + 2},{sy + 4} L{x + d + belly * 0.55 + 6},{sy + 70} L{x + d + belly * 0.55 - 2},{sy + 76} Z", c["sig"] or "#b23a3a", 3)
    if c["top_type"] in ("jacket", "uniform", "cardigan"):
        s += P(f"M{x + d - 6},{sy + 2} L{x + d - 22},{sy + 60}", "none", 3)
    if c["scarf"]:
        sc = c["sig"] or "#c0392b"
        s += P(f"M{x - hw * 0.5},{sy - 20} L{x + hw * 0.45},{sy - 16} L{x + hw * 0.5},{sy + 10} L{x - hw * 0.55},{sy + 6} Z", sc)
        s += P(f"M{x - hw * 0.45},{sy + 2} L{x - hw * 0.75},{sy + 80} L{x - hw * 0.4},{sy + 84} Z", shade(sc, 0.85))
    if c["lanyard"]:
        s += LINE(x + d - 4, sy + 2, x + d + belly * 0.4 + 4, sy + 82, 5, c["sig"] or "#2d6cdf")
        s += f'<rect x="{x + d + belly * 0.4 - 4:.1f}" y="{sy + 80:.1f}" width="10" height="42" rx="2" fill="#ffffff" stroke="{OUT}" stroke-width="3"/>'
    # 팔
    hx = x + 6 - sw_ * c["height"] * 0.06
    hy_ = b.handy - 8 - abs(sw_) * 6
    ang = pose.get("arm", 0)       # 앞으로 팔 들기(도)
    if ang:
        L = math.hypot(hx - (x - 4), hy_ - (sy + 18))
        r_ = math.radians(ang)
        hx, hy_ = x - 4 + L * math.sin(r_), sy + 18 + L * math.cos(r_)
    s += LIMB(x - 4, sy + 18, hx, hy_, c["arm_w"], shade(c["top"], 0.92))
    s += E(hx + 2, hy_ + 12, c["arm_w"] * 0.5, c["arm_w"] * 0.62, c["skin"])
    # 머리
    cy = b.hcy
    s += E(x, cy, hw * 0.95, hh / 2, c["skin"])
    # 코·턱
    s += P(f"M{x + hw * 0.88},{cy - hh * 0.02} Q{x + hw * 1.12},{cy + hh * 0.12} {x + hw * 0.9},{cy + hh * 0.18}", c["skin"], LW * 0.9)
    s += E(x - hw * 0.1, cy + hh * 0.06, hw * 0.15, hh * 0.1, c["skin"])   # 귀
    s += P(f"M{x - hw * 0.12},{cy + hh * 0.02} q{hw * 0.08},{hh * 0.04} 0,{hh * 0.08}", "none", 2.5)
    ex = x + hw * 0.55
    ey = cy + hh * 0.05
    e = "closed" if pose.get("blink") else c["eyes"]
    if e == "closed":
        s += P(f"M{ex - hw * 0.09},{ey} Q{ex},{ey + hh * 0.035} {ex + hw * 0.09},{ey}", "none", LW * 0.9)
    elif e == "anime":
        s += anime_eye(ex + hw * 0.05, ey, hw * 0.12, hh * 0.12, c.get("iris", "#5a3a22"), side=True)
    elif e == "dot":
        s += E(ex, ey, hw * 0.06, hh * 0.055, OUT, 0)
    elif e == "smile":
        s += P(f"M{ex - hw * 0.09},{ey + hh * 0.01} Q{ex},{ey - hh * 0.06} {ex + hw * 0.09},{ey + hh * 0.01}", "none", LW * 0.9)
    elif e == "sharp":
        s += P(f"M{ex - hw * 0.08},{ey - hh * 0.02} L{ex + hw * 0.1},{ey - hh * 0.03} L{ex + hw * 0.04},{ey + hh * 0.03} Z", OUT, 2)
    else:
        s += P(f"M{ex - hw * 0.08},{ey - hh * 0.01} Q{ex},{ey + hh * 0.04} {ex + hw * 0.09},{ey - hh * 0.01}", "none", LW * 0.9)
    bw = LW * 1.1 * c["brows"]
    if e == "anime":
        ey -= hh * 0.09
    s += LINE(ex - hw * 0.1, ey - hh * 0.11 + (hh * 0.02 if e == "sharp" else 0), ex + hw * 0.12, ey - hh * 0.12 - (hh * 0.02 if e == "sharp" else 0), bw)
    if c["wrinkles"]:
        s += LINE(ex - hw * 0.15, ey, ex - hw * 0.24, ey + hh * 0.04, 2.5)
        s += P(f"M{x + hw * 0.55},{cy + hh * 0.2} q{-hw * 0.06},{hh * 0.08} 0,{hh * 0.14}", "none", 2.5)
    my = cy + hh * 0.31
    if c["beard"]:
        bc = c["beard"] if isinstance(c["beard"], str) else c["hair"]
        s += P(f"M{x - hw * 0.25},{cy + hh * 0.05} Q{x - hw * 0.3},{cy + hh * 0.45} {x + hw * 0.2},{cy + hh * 0.62} Q{x + hw * 0.8},{cy + hh * 0.62} {x + hw * 0.92},{my - hh * 0.02} "
               f"L{x + hw * 0.6},{my - hh * 0.05} Q{x + hw * 0.3},{cy + hh * 0.15} {x - hw * 0.25},{cy + hh * 0.05} Z", bc)
    if c["mustache"]:
        s += P(f"M{x + hw * 0.92},{my - hh * 0.05} Q{x + hw * 0.7},{my - hh * 0.08} {x + hw * 0.55},{my} Q{x + hw * 0.75},{my - hh * 0.01} {x + hw * 0.92},{my - hh * 0.02} Z",
               c["hair"] if c["hair_style"] != "bald" else "#9a9a9a", 3)
        my += hh * 0.035
    m = c["mouth"]
    if pose.get("talk", 0) > 0.15:
        o = pose["talk"]
        s += E(x + hw * 0.74, my + hh * 0.01, hw * (0.08 + 0.04 * o), hh * (0.02 + 0.05 * o), "#6b2a24", LW * 0.7)
    elif m == "smile":
        s += P(f"M{x + hw * 0.62},{my - hh * 0.01} Q{x + hw * 0.75},{my + hh * 0.05} {x + hw * 0.87},{my - hh * 0.02}", "none", LW * 0.8)
    elif m == "frown":
        s += P(f"M{x + hw * 0.62},{my + hh * 0.02} Q{x + hw * 0.75},{my - hh * 0.02} {x + hw * 0.87},{my}", "none", LW * 0.8)
    else:
        s += LINE(x + hw * 0.64, my, x + hw * 0.87, my - hh * 0.01, LW * 0.8)
    if c["glasses"]:
        gc = c.get("glasses_col", OUT)
        s += f'<rect x="{ex - hw * 0.14:.1f}" y="{ey - hh * 0.08:.1f}" width="{hw * 0.3:.1f}" height="{hh * 0.15:.1f}" rx="5" fill="#ffffff" fill-opacity="0.25" stroke="{gc}" stroke-width="{LW * 0.8}"/>'
        s += LINE(ex - hw * 0.14, ey - hh * 0.03, x - hw * 0.05, ey - hh * 0.0, LW * 0.7, gc)
    if c["blush"]:
        s += E(x + hw * 0.5, ey + hh * 0.13, hw * 0.12, hh * 0.04, "#f08a7a", 0, 'opacity="0.45"')
    s += hf
    if c["aviator"]:
        t = cy - hh / 2
        col = c["aviator"] if isinstance(c["aviator"], str) else "#8a5a32"
        s += P(f"M{x - hw * 0.35},{cy - hh * 0.12} Q{x - hw * 0.05},{cy - hh * 0.1} {x + hw * 0.05},{cy + hh * 0.2} "
               f"Q{x - hw * 0.1},{cy + hh * 0.34} {x - hw * 0.35},{cy + hh * 0.3} Z", col)
        s += LINE(x - hw * 0.1, cy + hh * 0.32, x + hw * 0.0, cy + hh * 0.5, 4, shade(col, 0.6))
        s += P(f"M{x - hw * 1.02},{cy + hh * 0.02} C{x - hw * 1.1},{t - hh * 0.2} {x + hw * 0.95},{t - hh * 0.22} {x + hw * 0.98},{t + hh * 0.26} "
               f"Q{x + hw * 0.3},{t + hh * 0.2} {x - hw * 0.2},{cy - hh * 0.1} Q{x - hw * 0.7},{cy - hh * 0.05} {x - hw * 1.02},{cy + hh * 0.02} Z", col)
        by = t + hh * 0.14
        s += LINE(x - hw * 1.0, by + hh * 0.08, x + hw * 0.92, by, 11, OUT) + LINE(x - hw * 1.0, by + hh * 0.08, x + hw * 0.92, by, 6, "#3b3b3b")
        s += E(x + hw * 0.62, by - hh * 0.01, hw * 0.16, hh * 0.1, "#c9a227", LW * 0.9)
        s += E(x + hw * 0.66, by - hh * 0.01, hw * 0.1, hh * 0.07, "#7fc8d8", 3)
    if c["cap"]:
        t = cy - hh / 2
        col = c["cap"] if isinstance(c["cap"], str) else c["sig"] or "#333a55"
        s += P(f"M{x - hw * 1.0},{t + hh * 0.22} C{x - hw * 1.0},{t - hh * 0.18} {x + hw * 1.0},{t - hh * 0.18} {x + hw * 1.0},{t + hh * 0.22} Z", col)
        s += f'<rect x="{x - hw * 1.02:.1f}" y="{t + hh * 0.14:.1f}" width="{hw * 2.04:.1f}" height="{hh * 0.1:.1f}" rx="5" fill="{shade(col, 0.6)}" stroke="{OUT}" stroke-width="{LW}"/>'
        s += P(f"M{x + hw * 0.9},{t + hh * 0.2} Q{x + hw * 1.45},{t + hh * 0.22} {x + hw * 1.5},{t + hh * 0.3} L{x + hw * 0.9},{t + hh * 0.27} Z", shade(col, 0.45))
    return s


def hair_side(b, x):
    c, hw, hh, cy = b.c, b.hw, b.hh, b.hcy
    st, col = c["hair_style"], c["hair"]
    t = cy - hh / 2
    behind, front = "", ""
    if st == "perm":
        r = hw * 0.3
        dots = [(x + math.cos(a) * hw * 0.95, cy + math.sin(a) * hh * 0.5 - hh * 0.05)
                for a in [math.pi * (0.55 + i * 0.13) for i in range(9)]]
        dots += [(x - hw * 0.4, cy - hh * 0.05), (x - hw * 0.1, t + hh * 0.12), (x + hw * 0.3, t + hh * 0.05)]
        behind = E(x - hw * 0.1, cy - hh * 0.1, hw * 1.1, hh * 0.5, col, LW * 0.8)
        front = "".join(E(px, py, r, r * 0.92, col, LW * 0.8) for px, py in dots)
        front += "".join(E(px - r * 0.25, py - r * 0.3, r * 0.25, r * 0.15, shade(col, 1.35), 0) for px, py in dots[::2])
        return behind, front
    if st == "bald":
        front = P(f"M{x - hw * 0.92},{cy - hh * 0.15} Q{x - hw * 1.05},{cy + hh * 0.15} {x - hw * 0.7},{cy + hh * 0.3} "
                  f"Q{x - hw * 0.35},{cy + hh * 0.2} {x - hw * 0.3},{cy - hh * 0.05} Q{x - hw * 0.6},{cy - hh * 0.12} {x - hw * 0.92},{cy - hh * 0.15} Z", col, LW * 0.8)
        front += E(x + hw * 0.05, t + hh * 0.12, hw * 0.25, hh * 0.05, "#ffffff", 0, 'opacity="0.55"')
        return behind, front
    if st == "spiky":
        behind = spikes(x - hw * 0.15, cy - hh * 0.05, hw * 0.85, hh * 0.45, 100, 280, 7, hh * 0.24, col)
        front = P(f"M{x + hw * 0.85},{t + hh * 0.3} L{x + hw * 0.95},{t + hh * 0.08} C{x + hw * 0.6},{t - hh * 0.16} {x - hw * 0.5},{t - hh * 0.16} {x - hw * 0.98},{cy - hh * 0.05} "
                  f"L{x - hw * 0.9},{cy + hh * 0.3} L{x - hw * 0.55},{cy + hh * 0.12} L{x - hw * 0.3},{cy + hh * 0.2} L{x - hw * 0.22},{cy - hh * 0.06} "
                  f"L{x + hw * 0.25},{t + hh * 0.22} L{x + hw * 0.5},{t + hh * 0.36} L{x + hw * 0.6},{t + hh * 0.22} Z", col)
        return behind, front
    fy = {"crew": 0.2, "slick": 0.14, "bob": 0.26, "bun": 0.18, "long": 0.26}.get(st, 0.2)
    front = P(f"M{x + hw * 0.75},{t + hh * fy} C{x + hw * 0.9},{t - hh * 0.05} {x - hw * 0.4},{t - hh * 0.16} {x - hw * 0.95},{cy - hh * 0.1} "
              f"Q{x - hw * 1.05},{cy + hh * (0.25 if st != 'crew' else 0.12)} {x - hw * 0.6},{cy + hh * (0.32 if st != 'crew' else 0.18)} "
              f"Q{x - hw * 0.3},{cy + hh * 0.05} {x - hw * 0.25},{cy - hh * 0.08} Q{x + hw * 0.2},{t + hh * (fy + 0.06)} {x + hw * 0.75},{t + hh * fy} Z", col)
    if st == "slick":
        front += P(f"M{x + hw * 0.5},{t + hh * 0.04} Q{x},{t - hh * 0.04} {x - hw * 0.6},{t + hh * 0.12}", "none", LW * 0.6, f'stroke="{shade(col, 1.6)}"')
    if st == "bob":
        front += P(f"M{x - hw * 0.95},{cy - hh * 0.05} Q{x - hw * 1.1},{cy + hh * 0.35} {x - hw * 0.8},{cy + hh * 0.48} L{x - hw * 0.2},{cy + hh * 0.42} "
                   f"Q{x - hw * 0.2},{cy + hh * 0.1} {x - hw * 0.3},{cy - hh * 0.05} Z", col)
    if st == "bun":
        behind += E(x - hw * 0.85, cy - hh * 0.2, hw * 0.32, hh * 0.15, col)
    if st == "long":
        behind += P(f"M{x - hw * 0.95},{cy - hh * 0.2} L{x - hw * 1.1},{b.sy + 80} L{x - hw * 0.2},{b.sy + 80} L{x},{cy} Z", col)
    return behind, front


def figure(c, view="front", pose=None):
    """장면용 인물 한 명 SVG 조각 (칸 400×900 기준, 발 = (200, 860)). view: front·back·right·left"""
    c = {**DEFAULT, **c}
    pose = pose or {}
    if view == "front":
        g = view_front(c, pose=pose)
    elif view == "back":
        g = view_front(c, back=True, pose=pose)
    elif view == "right":
        g = view_side(c, pose)
    else:
        g = f'<g transform="translate({VW},0) scale(-1,1)">{view_side(c, pose)}</g>'
    br = pose.get("breath", 0.0)   # 숨쉬기: 발을 기준으로 아주 살짝 늘었다 줄었다
    bob = pose.get("bob", 0.0)
    return f'<g transform="translate(0,{bob:.2f}) translate({VW / 2},{G}) scale(1,{1 + br:.4f}) translate({-VW / 2},{-G})">{g}</g>'


def svg_sheet(c, label=True):
    c = {**DEFAULT, **c}
    W = VW * 4
    parts = [
        view_front(c),
        view_side(c),
        f'<g transform="translate({VW * 2},0) scale(-1,1) translate({-VW * 2},0)">{view_side(c)}</g>',
        view_front(c, back=True),
    ]
    g = ""
    for i, p in enumerate(parts):
        dx = 0 if i == 2 else VW * i
        if i == 2:
            # 왼쪽을 보는 옆모습: 칸 2 자리(800~1200)에 좌우를 뒤집어 그림
            g += f'<g transform="translate({VW * 3},0) scale(-1,1)">{view_side(c)}</g>'
            continue
        g += f'<ellipse cx="{dx + VW / 2}" cy="{G}" rx="90" ry="12" fill="#000" opacity="0.08"/>' if i == 0 else ""
        g += f'<g transform="translate({dx},0)">{p}</g>'
    shadows = "".join(f'<ellipse cx="{VW * i + VW / 2}" cy="{G - 2}" rx="95" ry="13" fill="#000" opacity="0.09"/>' for i in range(4))
    lab = ""
    if label:
        lab = f'<text x="24" y="52" font-family="NanumGothic, Noto Sans CJK KR, sans-serif" font-size="34" font-weight="bold" fill="#333">{c["name"]}</text>'
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{VH}" viewBox="0 0 {W} {VH}">'
            f'<rect width="{W}" height="{VH}" fill="#ffffff"/>{shadows}{g}{lab}</svg>')


def render(c, path, label=True):
    cairosvg.svg2png(bytestring=svg_sheet(c, label).encode("utf-8"), write_to=path)


if __name__ == "__main__":
    a = sys.argv[1:]
    data = json.load(open(a[0], encoding="utf-8"))
    out = a[1]
    only = set(a[a.index("--이름") + 1].split(",")) if "--이름" in a else None
    os.makedirs(out, exist_ok=True)
    made = []
    for ch in data["chars"]:
        if only and ch["name"] not in only:
            continue
        p = os.path.join(out, ch["name"] + ".png")
        render(ch, p)
        made.append(p)
        print("만듦:", p)
    if len(made) > 1:
        from PIL import Image
        ims = [Image.open(p).convert("RGB") for p in made]
        tot = Image.new("RGB", (ims[0].width, sum(i.height for i in ims)), "white")
        y = 0
        for im in ims:
            tot.paste(im, (0, y))
            y += im.height
        tot.save(os.path.join(out, "_모두.png"))
        print("모음:", os.path.join(out, "_모두.png"))
