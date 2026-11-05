"""블록 장난감 모양 캐릭터 — 카툰캐릭터.py 의 인물 설정을 그대로 받아 네모난 블록 인형으로 그림 (사용자 결정 2026-11-05)
  - 특정 회사 장난감 모양을 따라 하지 않은 오리지널 블록 인형: 네모 머리·상자 몸통·막대 팔다리·네모 손, 플라스틱 광택
  - 같은 설정 = 같은 모습. 자세(pose)도 카툰과 같음 (깜빡임·말·팔 각도·걷기·숨)
  - 인물 설정에 "style": "block" 이 있거나, 카툰캐릭터.STYLE = "block" 이면 카툰캐릭터.figure()·시트가 이 모양으로 그림"""
import math

OUT = "#26221f"
LW = 5
VW, G = 400, 860


def shade(hexc, f):
    hexc = hexc.lstrip("#")
    r, g, b = (int(hexc[i:i + 2], 16) for i in (0, 2, 4))
    if f < 1:
        r, g, b = (int(c * f) for c in (r, g, b))
    else:
        r, g, b = (int(c + (255 - c) * (f - 1)) for c in (r, g, b))
    return "#%02x%02x%02x" % (r, g, b)


def RB(x, y, w, h, fill, rx=6, sw=LW, extra=""):
    """외곽선 있는 둥근 모서리 상자 (블록 한 조각)"""
    if w < 0:
        x, w = x + w, -w
    return f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx}" fill="{fill}" stroke="{OUT}" stroke-width="{sw}" {extra}/>'


def SHINE(x, y, w, h, op=0.28):
    """플라스틱 광택 (왼쪽 위 흰 띠)"""
    return f'<rect x="{x + w * 0.1:.1f}" y="{y + h * 0.08:.1f}" width="{w * 0.18:.1f}" height="{h * 0.5:.1f}" rx="4" fill="#ffffff" opacity="{op}"/>'


def SIDE(x, y, w, h, op=0.16):
    """오른쪽 그늘"""
    return f'<rect x="{x + w * 0.78:.1f}" y="{y + 3:.1f}" width="{w * 0.2:.1f}" height="{h - 6:.1f}" rx="3" fill="#000" opacity="{op}"/>'


def P(d, fill, sw=LW, extra=""):
    st = "" if 'stroke="' in extra else f'stroke="{OUT}"'
    return f'<path d="{d}" fill="{fill}" {st} stroke-width="{sw}" stroke-linejoin="round" stroke-linecap="round" {extra}/>'


def ROT(cx, cy, deg, inner):
    return f'<g transform="rotate({deg:.2f} {cx:.1f} {cy:.1f})">{inner}</g>' if deg else inner


class B:
    """몸 치수"""
    def __init__(s, c):
        s.c = c
        H = c["height"]
        # 장난감 비율: 큰 네모 머리, 넓은 상자 몸통, 짧고 굵은 다리 (키·배 차이는 그대로 남겨 인물마다 다르게)
        s.hs = H * c["head"] * 1.32                       # 머리 높이
        s.hw = s.hs * c["head_w"] / 0.86 * 0.53           # 머리 반폭
        s.top = G - H
        s.hy0, s.hy1 = s.top, s.top + s.hs
        s.ty0 = s.hy1 + s.hs * 0.08                       # 몸통 위
        s.ty1 = s.ty0 + H * c["torso"] * 1.05             # 몸통 아래
        s.cx = VW / 2
        s.sw = max(c["shoulder"] * 1.12, s.hw * 1.1)
        s.bw = max(max(c["waist"], c["hip"]) * 1.12, s.sw * 0.88)
        s.lw = s.bw * 0.92                                # 다리 굵기 (두 다리가 거의 붙음)
        s.aw = c["arm_w"] * 1.65
        s.alen = (s.ty1 - s.ty0) * 1.02


# ───────────────────────── 머리 ─────────────────────────
def hair_block(b, x, view):
    """(머리 뒤에 그릴 것, 머리 위에 그릴 것)"""
    c, hw, hs, y0 = b.c, b.hw, b.hs, b.hy0
    st, col = c["hair_style"], c["hair"]
    side = view in ("right",)
    back = view == "back"
    bh, fr = "", ""
    w = hw * 2 if not side else hw * 1.7
    xl = x - w / 2
    if st == "bald":
        for k in ([-1, 1] if not side else [-1]):
            xx = x + k * (w / 2) - (8 if k > 0 else -8) * 0 + (0 if k > 0 else 0)
            fr += RB(xx - (hs * 0.12 if k < 0 else 0) - (0 if k < 0 else hs * 0.0), y0 + hs * 0.3, hs * 0.12, hs * 0.3, col, 4, 4)
        if back:
            fr += RB(xl - 4, y0 + hs * 0.42, w + 8, hs * 0.22, col, 6, 4)
        fr += f'<ellipse cx="{x - w * 0.15:.1f}" cy="{y0 + hs * 0.1:.1f}" rx="{w * 0.16:.1f}" ry="{hs * 0.04:.1f}" fill="#fff" opacity="0.5"/>'
        return bh, fr
    cap_h = {"crew": 0.24, "spiky": 0.26, "slick": 0.2, "bob": 0.3, "long": 0.3, "perm": 0.3, "bun": 0.24}.get(st, 0.24)
    if back:
        cap_h = {"bob": 0.9, "long": 0.95}.get(st, 0.8)
    fr += RB(xl - 6, y0 - hs * 0.06, w + 12, hs * (cap_h + 0.06), col, 10)
    fr += SHINE(xl - 6, y0 - hs * 0.06, w + 12, hs * (cap_h + 0.06), 0.22)
    if side:   # 옆머리: 뒤통수 쪽 덩어리
        fr += RB(xl - 8, y0, w * 0.42, hs * (0.62 if st not in ("bob", "long") else 0.85), col, 8)
    if st in ("bob", "long") and not back:
        for k in ([-1, 1] if not side else []):
            fr += RB(x + k * (w / 2) - (0 if k > 0 else hs * 0.16) + (-6 if k > 0 else 6), y0 + hs * 0.1, hs * 0.16, hs * 0.75, col, 6)
    if st == "long":
        bh += RB(xl - 6, y0 + hs * 0.4, w + 12, hs * 1.05, col, 8)
    if st == "spiky":   # 삐죽삐죽: 위·옆으로 세모 블록
        n = 6
        for i in range(n):
            px = xl - 6 + (w + 12) * (i + 0.5) / n
            ht = hs * (0.2 + 0.07 * ((i * 3) % 3))
            fr = P(f"M{px - (w + 12) / n * 0.55:.1f},{y0 + 2:.1f} L{px + (w + 12) / n * 0.1:.1f},{y0 - ht:.1f} L{px + (w + 12) / n * 0.55:.1f},{y0 + 2:.1f} Z", col, 4) + fr
        for k in ([-1, 1] if not side else [-1]):
            ex = x + k * (w / 2 + 6)
            fr = P(f"M{ex:.1f},{y0 + hs * 0.05:.1f} L{ex + k * hs * 0.22:.1f},{y0 + hs * 0.14:.1f} L{ex:.1f},{y0 + hs * 0.28:.1f} Z", col, 4) + fr
        if not back and not side:   # 앞머리 톱니
            for i in range(4):
                px = xl + w * (i + 0.5) / 4
                fr += P(f"M{px - w / 8:.1f},{y0 + hs * cap_h - 2:.1f} L{px:.1f},{y0 + hs * (cap_h + 0.1):.1f} L{px + w / 8:.1f},{y0 + hs * cap_h - 2:.1f} Z", col, 3)
    if st == "perm":   # 뽀글: 둥근 블록 송이
        for i in range(7):
            px = xl - 8 + (w + 16) * i / 6
            fr = RB(px - hs * 0.1, y0 - hs * 0.14, hs * 0.2, hs * 0.2, col, 10, 4) + fr
        for k in ([-1, 1] if not side else [-1]):
            fr += RB(x + k * (w / 2) - hs * 0.1, y0 + hs * 0.15, hs * 0.2, hs * 0.22, col, 10, 4)
    if st == "slick":
        fr += f'<line x1="{x - w * 0.15:.1f}" y1="{y0 + 4:.1f}" x2="{x + w * 0.3:.1f}" y2="{y0 + hs * 0.12:.1f}" stroke="{shade(col, 1.7)}" stroke-width="4"/>'
    return bh, fr


def face_block(b, x, pose, side=False):
    c, hw, hs, y0 = b.c, b.hw, b.hs, b.hy0
    s = ""
    e = "closed" if pose.get("blink") else c["eyes"]
    ey = y0 + hs * 0.5
    xs = [x + hw * 0.55] if side else [x - hw * 0.42, x + hw * 0.42]
    for px in xs:
        if e == "closed":
            s += f'<rect x="{px - hs * 0.08:.1f}" y="{ey:.1f}" width="{hs * 0.16:.1f}" height="4" fill="{OUT}"/>'
        elif e == "anime":
            s += RB(px - hs * 0.1, ey - hs * 0.11, hs * 0.2, hs * 0.22, "#ffffff", 4, 3)
            s += f'<rect x="{px - hs * 0.06 + (hs * 0.03 if side else 0):.1f}" y="{ey - hs * 0.07:.1f}" width="{hs * 0.12:.1f}" height="{hs * 0.16:.1f}" rx="3" fill="{c.get("iris", "#3a2a1a")}"/>'
            s += f'<rect x="{px - hs * 0.045:.1f}" y="{ey - hs * 0.06:.1f}" width="{hs * 0.04:.1f}" height="{hs * 0.04:.1f}" fill="#fff"/>'
        elif e == "smile":
            s += P(f"M{px - hs * 0.08},{ey + 2} L{px},{ey - hs * 0.05} L{px + hs * 0.08},{ey + 2}", "none", 4)
        elif e == "sharp":
            s += P(f"M{px - hs * 0.08},{ey + hs * 0.02} L{px + hs * 0.08},{ey - hs * 0.03} L{px + hs * 0.08},{ey + hs * 0.04} L{px - hs * 0.08},{ey + hs * 0.05} Z", OUT, 2)
        elif e == "tired":
            s += f'<rect x="{px - hs * 0.06:.1f}" y="{ey:.1f}" width="{hs * 0.12:.1f}" height="{hs * 0.06:.1f}" rx="2" fill="{OUT}"/>'
        else:
            s += f'<rect x="{px - hs * 0.05:.1f}" y="{ey - hs * 0.06:.1f}" width="{hs * 0.1:.1f}" height="{hs * 0.12:.1f}" rx="3" fill="{OUT}"/>'
            s += f'<rect x="{px - hs * 0.025:.1f}" y="{ey - hs * 0.045:.1f}" width="{hs * 0.03:.1f}" height="{hs * 0.03:.1f}" fill="#fff"/>'
        bw = 4 * c["brows"]
        by = ey - hs * (0.17 if e == "anime" else 0.13)
        tilt = {"sharp": 0.04, "anime": 0.03, "tired": -0.03}.get(e, 0)
        sg = 1 if px > x or side else -1
        s += f'<line x1="{px - hs * 0.1:.1f}" y1="{by + (tilt * hs if sg < 0 else -tilt * hs) * -1:.1f}" x2="{px + hs * 0.1:.1f}" y2="{by + (tilt * hs if sg > 0 else -tilt * hs):.1f}" stroke="{OUT}" stroke-width="{bw:.1f}" stroke-linecap="square"/>'
        if c["blush"]:
            s += f'<rect x="{px - hs * 0.08 + (hs * 0.04 if px > x else -hs * 0.04):.1f}" y="{ey + hs * 0.12:.1f}" width="{hs * 0.14:.1f}" height="{hs * 0.05:.1f}" rx="3" fill="#f08a7a" opacity="0.5"/>'
    mx = x + hw * 0.5 if side else x
    my = y0 + hs * 0.8
    if c["beard"]:
        bc = c["beard"] if isinstance(c["beard"], str) else c["hair"]
        if side:
            s += RB(x - hw * 0.2, y0 + hs * 0.62, hw * 1.0, hs * 0.42, bc, 6)
        else:
            s += RB(x - hw - 2, y0 + hs * 0.6, hw * 2 + 4, hs * 0.44, bc, 8)
            s += f'<rect x="{x - hs * 0.12:.1f}" y="{my - hs * 0.04:.1f}" width="{hs * 0.24:.1f}" height="{hs * 0.08:.1f}" rx="3" fill="{c["skin"]}"/>'
    if c["mustache"]:
        mc = c["hair"] if c["hair_style"] != "bald" else "#9a9a9a"
        s += RB(mx - hs * (0.1 if side else 0.17), my - hs * 0.1, hs * (0.2 if side else 0.34), hs * 0.07, mc, 3, 3)
    talk = pose.get("talk", 0)
    if talk > 0.15:
        s += RB(mx - hs * 0.07, my - hs * 0.02, hs * 0.14, hs * (0.04 + 0.08 * talk), "#6b2a24", 3, 3)
    elif c["mouth"] == "smile":
        s += P(f"M{mx - hs * 0.12},{my - 2} L{mx - hs * 0.08},{my + hs * 0.05} L{mx + hs * 0.08},{my + hs * 0.05} L{mx + hs * 0.12},{my - 2} Z", "#8c3b32", 3)
    elif c["mouth"] == "frown":
        s += P(f"M{mx - hs * 0.09},{my + hs * 0.03} L{mx - hs * 0.05},{my} L{mx + hs * 0.05},{my} L{mx + hs * 0.09},{my + hs * 0.03}", "none", 4)
    elif c["mouth"] == "smirk":
        s += f'<line x1="{mx - hs * 0.08:.1f}" y1="{my + 2:.1f}" x2="{mx + hs * 0.1:.1f}" y2="{my - hs * 0.03:.1f}" stroke="{OUT}" stroke-width="4"/>'
    else:
        s += f'<rect x="{mx - hs * 0.08:.1f}" y="{my - 2:.1f}" width="{hs * 0.16:.1f}" height="4" fill="{OUT}"/>'
    if c["glasses"]:
        gc = c.get("glasses_col", OUT)
        for px in xs:
            s += f'<rect x="{px - hs * 0.13:.1f}" y="{ey - hs * 0.1:.1f}" width="{hs * 0.26:.1f}" height="{hs * 0.2:.1f}" rx="3" fill="#fff" fill-opacity="0.2" stroke="{gc}" stroke-width="4"/>'
        if not side:
            s += f'<line x1="{xs[0] + hs * 0.13:.1f}" y1="{ey - hs * 0.03:.1f}" x2="{xs[1] - hs * 0.13:.1f}" y2="{ey - hs * 0.03:.1f}" stroke="{gc}" stroke-width="4"/>'
    return s


def hats_block(b, x, view):
    c, hw, hs, y0 = b.c, b.hw, b.hs, b.hy0
    s = ""
    side = view == "right"
    w = hw * 2 if not side else hw * 1.7
    xl = x - w / 2
    if c["cap"]:   # 챙 모자
        col = c["cap"] if isinstance(c["cap"], str) else (c["sig"] or "#333a55")
        s += RB(xl - 8, y0 - hs * 0.2, w + 16, hs * 0.3, col, 8)
        s += SHINE(xl - 8, y0 - hs * 0.2, w + 16, hs * 0.3, 0.2)
        s += RB(xl - 10, y0 + hs * 0.06, w + 20, hs * 0.08, shade(col, 0.6), 3)
        if side:
            s += RB(x + w / 2 - 4, y0 + hs * 0.08, hs * 0.3, hs * 0.06, shade(col, 0.45), 3, 4)
        elif view != "back":
            s += RB(xl, y0 + hs * 0.12, w, hs * 0.06, shade(col, 0.45), 3, 4)
            s += RB(x - hs * 0.06, y0 - hs * 0.12, hs * 0.12, hs * 0.1, "#e3b341", 3, 3)
    if c["aviator"]:   # 비행 모자 + 고글
        col = c["aviator"] if isinstance(c["aviator"], str) else "#8a5a32"
        s += RB(xl - 8, y0 - hs * 0.12, w + 16, hs * 0.4, col, 12)
        s += SHINE(xl - 8, y0 - hs * 0.12, w + 16, hs * 0.4, 0.2)
        flaps = [-1, 1] if not side else [-1]
        for k in flaps:
            fx = (x + k * (w / 2 + 2) - (hs * 0.18 if k < 0 else 0)) if not side else x - w * 0.15
            s += RB(fx, y0 + hs * 0.25, hs * 0.18, hs * 0.38, col, 6)
        s += RB(xl - 10, y0 + hs * 0.04, w + 20, hs * 0.08, "#3b3b3b", 3, 4)
        if view != "back":
            gx = [x - hw * 0.42, x + hw * 0.42] if not side else [x + hw * 0.55]
            for g_ in gx:
                s += RB(g_ - hs * 0.11, y0 - hs * 0.02, hs * 0.22, hs * 0.18, "#c9a227", 5, 4)
                s += RB(g_ - hs * 0.07, y0 + hs * 0.01, hs * 0.14, hs * 0.11, "#7fc8d8", 3, 2)
    return s


# ───────────────────────── 몸 ─────────────────────────
def view_block(c, view="front", pose=None):
    pose = pose or {}
    b = B(c)
    x = b.cx
    s = ""
    side = view == "right"
    back = view == "back"
    hs = b.hs
    legtop = b.ty1 - 6
    # 다리 (걷기: 엉덩이를 축으로 흔듦)
    wp = pose.get("walk")
    swing = math.degrees(math.sin(wp)) * 0.45 if wp is not None else 0.0
    if side:
        d = b.sw * 0.55
        for k, col in ((-1, shade(c["bottom"], 0.8)), (1, c["bottom"])):
            leg = RB(x - b.lw * 0.35, legtop, b.lw * 0.7, G - 30 - legtop, col, 5) + RB(x - b.lw * 0.35 - 4, G - 34, b.lw * 1.0 + 8, 34, shade(c["shoes"], 0.85 if k < 0 else 1), 6)
            s += ROT(x, legtop, -swing * k, leg)
    else:
        for k in (-1, 1):
            lx = x + k * (b.bw * 0.5) - b.lw / 2
            s += RB(lx, legtop, b.lw, G - 30 - legtop, c["bottom"], 5) + SIDE(lx, legtop, b.lw, G - 30 - legtop, 0.12)
            s += RB(lx - 6, G - 34, b.lw + 12, 34, c["shoes"], 6)
    hb, hf = hair_block(b, x, "right" if side else view)
    s += hb
    # 코트 자락
    if c["coat_len"]:
        ky = b.ty1 + (G - b.ty1) * c["coat_len"]
        if side:
            s += RB(x - b.sw * 0.6, b.ty1 - 20, b.sw * 1.3, ky - b.ty1 + 20, c["top"], 6)
        else:
            s += RB(x - b.bw - 8, b.ty1 - 20, b.bw * 2 + 16, ky - b.ty1 + 20, c["top"], 6) + SIDE(x - b.bw - 8, b.ty1 - 20, b.bw * 2 + 16, ky - b.ty1 + 20)
            if not back:
                s += f'<rect x="{x - 10:.1f}" y="{b.ty1:.1f}" width="20" height="{ky - b.ty1 - 4:.1f}" fill="{shade(c["bottom"], 0.9)}"/>'
    # 뒤쪽 팔 (옆모습)
    arm_side = pose.get("arm", 0)
    if side:
        s += ROT(x, b.ty0 + 10, -(arm_side * 0.3) + swing, RB(x - b.aw / 2, b.ty0 + 4, b.aw, b.alen, shade(c["top"], 0.7), 6))
    # 목·몸통
    s += f'<rect x="{x - hs * 0.15:.1f}" y="{b.hy1 - 4:.1f}" width="{hs * 0.3:.1f}" height="{b.ty0 - b.hy1 + 10:.1f}" fill="{c["skin"]}" stroke="{OUT}" stroke-width="4"/>'
    if side:
        d = b.sw * 0.6 + max(0, c["waist"] - c["shoulder"]) * 0.8
        s += RB(x - b.sw * 0.6, b.ty0, b.sw * 0.6 + d, b.ty1 - b.ty0, c["top"], 8) + SHINE(x - b.sw * 0.6, b.ty0, b.sw * 0.6 + d, b.ty1 - b.ty0, 0.18)
    else:
        sw, bw = b.sw, b.bw
        s += P(f"M{x - sw},{b.ty0 + 8} Q{x - sw},{b.ty0} {x - sw + 10},{b.ty0} L{x + sw - 10},{b.ty0} Q{x + sw},{b.ty0} {x + sw},{b.ty0 + 8} "
               f"L{x + bw},{b.ty1} L{x - bw},{b.ty1} Z", c["top"])
        s += SHINE(x - sw, b.ty0, sw * 2, b.ty1 - b.ty0, 0.16) + SIDE(x - bw, b.ty0, bw * 2, b.ty1 - b.ty0, 0.13)
        s += RB(x - bw - 2, b.ty1 - 10, bw * 2 + 4, hs * 0.22, c["bottom"], 4)   # 허리 블록
    tt = c["top_type"]
    if not back and not side:
        if tt in ("jacket", "uniform", "cardigan"):
            vy = b.ty0 + (b.ty1 - b.ty0) * 0.42
            s += P(f"M{x - hs * 0.22},{b.ty0} L{x},{vy} L{x + hs * 0.22},{b.ty0} Z", c.get("shirt", "#f4f1ea"), 4)
            if c["tie"]:
                s += P(f"M{x - 7},{b.ty0 + 4} L{x + 7},{b.ty0 + 4} L{x + 10},{vy - 6} L{x},{vy + 10} L{x - 10},{vy - 6} Z", c["sig"] or "#b23a3a", 3)
            s += f'<line x1="{x}" y1="{vy:.1f}" x2="{x}" y2="{b.ty1 - 8:.1f}" stroke="{OUT}" stroke-width="3"/>'
            for i in range(3 if c["double"] else 2):
                for k in ((-1, 1) if c["double"] else (1,)):
                    s += f'<rect x="{x + k * 14 - 4:.1f}" y="{vy + 14 + i * 30:.1f}" width="8" height="8" fill="{c.get("button", "#d9c27a")}" stroke="{OUT}" stroke-width="2"/>'
            if tt == "uniform":
                s += RB(x - b.sw * 0.62, b.ty0 + 40, 30, 22, shade(c["top"], 0.8), 3, 3) + RB(x + b.sw * 0.62 - 30, b.ty0 + 40, 30, 22, shade(c["top"], 0.8), 3, 3)
        else:
            s += f'<rect x="{x - hs * 0.2:.1f}" y="{b.ty0 - 2:.1f}" width="{hs * 0.4:.1f}" height="10" rx="4" fill="{shade(c["top"], 0.85)}" stroke="{OUT}" stroke-width="3"/>'
    if c["braces"] and not side:
        bc = c["sig"] or "#a83232"
        for k in (-1, 1):
            s += f'<rect x="{x + k * b.sw * 0.42 - 4:.1f}" y="{b.ty0:.1f}" width="8" height="{b.ty1 - b.ty0:.1f}" fill="{bc}" stroke="{OUT}" stroke-width="2"/>'
    if c["apron"] and not side and not back:
        s += RB(x - b.bw * 0.75, b.ty0 + 30, b.bw * 1.5, (b.ty1 - b.ty0) + 110, c["sig"] or "#c0392b", 5)
    if c["scarf"]:
        sc = c["sig"] or "#c0392b"
        if side:
            s += RB(x - b.sw * 0.6 - 4, b.ty0 - 12, b.sw * 1.2 + 8, 24, sc, 6) + RB(x - b.sw * 0.6 - 10, b.ty0 + 6, 20, 70, shade(sc, 0.85), 4)
        else:
            s += RB(x - hs * 0.42, b.ty0 - 14, hs * 0.84, 26, sc, 8)
            if not back:
                s += RB(x + hs * 0.08, b.ty0 + 8, 22, 80, shade(sc, 0.85), 4)
    # 앞쪽 팔
    if side:
        s += ROT(x, b.ty0 + 10, -arm_side - swing, RB(x - b.aw / 2, b.ty0 + 4, b.aw, b.alen, shade(c["top"], 0.92), 6)
                 + RB(x - b.aw * 0.45, b.ty0 + b.alen, b.aw * 0.9, b.aw * 0.8, c["skin"], 5))
    else:
        for k in (-1, 1):
            ang = pose.get("arm_r" if k > 0 else "arm_l", 0)
            ax = x + k * (b.sw - b.aw * 0.1)
            arm = RB(ax - b.aw / 2, b.ty0 + 2, b.aw, b.alen, c["top"], 6) + SHINE(ax - b.aw / 2, b.ty0 + 2, b.aw, b.alen, 0.14)
            arm += RB(ax - b.aw * 0.45, b.ty0 + b.alen - 2, b.aw * 0.9, b.aw * 0.85, c["skin"], 5)
            s += ROT(ax, b.ty0 + 12, -k * (5 + ang), arm)
    # 머리
    w = b.hw * 2 if not side else b.hw * 1.7
    s += RB(x - w / 2, b.hy0, w, hs, c["skin"], 12) + SHINE(x - w / 2, b.hy0, w, hs, 0.25) + SIDE(x - w / 2, b.hy0, w, hs, 0.1)
    if side:
        s += RB(x - w * 0.12, b.hy0 + hs * 0.42, hs * 0.14, hs * 0.2, shade(c["skin"], 0.92), 4, 3)   # 귀
        s += RB(x + w / 2 - 4, b.hy0 + hs * 0.55, hs * 0.1, hs * 0.12, c["skin"], 3, 3)   # 코
    elif not back:
        for k in (-1, 1):
            s += RB(x + k * (w / 2) - (hs * 0.1 if k < 0 else 0), b.hy0 + hs * 0.42, hs * 0.1, hs * 0.2, shade(c["skin"], 0.92), 3, 3)
    if not back:
        s += face_block(b, x, pose, side)
    s += hf + hats_block(b, x, "right" if side else view)
    return s
