"""입체 블록 동물 (오리지널 모양 — 상자 몇 개로 만든 동물, 사용자 참고 2026-11-06: 블록 게임 동물처럼 단순·귀엽게)

animal(kind, pos, face=0, t=0, act="stand", scale=1.0) → 상자 목록 (블록3D.Box)
  kind: ox(소)·donkey(당나귀)·cat(고양이)·ibis(따오기)·croc(악어)·hippo(하마)·goat(염소)·dog(개)
  pos = 발 가운데 (x, y, z), face = 보는 방향(도, 0 = +z, 90 = +x) — 사람(person)과 같음
  act: stand(서서 꼬리·머리만 살짝) · walk(네 다리 번갈아) · eat(고개 숙여 풀 먹기) · sit(앉기, 고양이) · open(입 벌리기, 악어·하마)
키 비율: 사람 키 ≈ 5.3 블록 → 소 어깨 ≈ 3.3, 당나귀 ≈ 2.8, 고양이 ≈ 0.9, 하마 ≈ 3.0
얼굴은 네모 머리 앞면에 눈(검은 네모 + 흰 반짝)·코·뿔을 작은 조각으로 붙임 (글자·무늬 그림 없음)
"""
import math
import os
import importlib.util

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
_sp = importlib.util.spec_from_file_location("blk3d_e", os.path.join(HERE, "블록3D.py"))
E = importlib.util.module_from_spec(_sp)
_sp.loader.exec_module(E)
Box = E.Box

# 몸 크기(가로 w, 높이 h, 길이 d), 다리 길이 leg·굵기 lw, 머리 크기 hd, 색
SPEC = {
    "ox":     dict(w=2.2, h=1.7, d=3.6, leg=1.6, lw=0.55, hd=(1.4, 1.3, 1.2), col="#8a5a3a", belly="#e9dcc8", spot="#f1e8da", horn="#efe6cf", nose="#d9a08a", tail=1.3),
    "donkey": dict(w=1.5, h=1.3, d=2.6, leg=1.5, lw=0.4, hd=(1.0, 1.0, 1.4), col="#8d8a86", belly="#d9d4cc", nose="#e6e0d6", ear=0.9, mane="#4a4440", tail=1.1),
    "goat":   dict(w=1.1, h=1.0, d=1.9, leg=1.1, lw=0.3, hd=(0.8, 0.8, 0.9), col="#e9e3d6", belly="#d6cfc0", nose="#c9a58a", horn="#8a7a62", beard="#cfc6b4", tail=0.4),
    "dog":    dict(w=0.9, h=0.85, d=1.7, leg=0.9, lw=0.28, hd=(0.85, 0.8, 0.85), col="#c8964f", belly="#ecd6ad", nose="#2b2320", ear=0.45, tail=0.8),
    "cat":    dict(w=0.55, h=0.5, d=1.15, leg=0.45, lw=0.18, hd=(0.6, 0.55, 0.5), col="#c9a46a", belly="#efe1c2", spot="#8a6a3c", nose="#e58a8a", ear=0.25, tail=0.9),
    "hippo":  dict(w=2.6, h=2.0, d=3.8, leg=0.9, lw=0.8, hd=(2.0, 1.4, 1.8), col="#8f7a86", belly="#c9a8a8", nose="#b38c8c", ear=0.25, tail=0.4),
}


def _rot_all(out, piv, face):
    if face:
        for b in out:
            b.rots.append((np.array(piv, float), "y", face))
    return out


def _eyes(B, fx, y, z, hw, sz):
    for sg in (-1, 1):
        B((fx + sg * hw - (sz if sg > 0 else 0), y, z), (sz, sz, 0.03), "#1d1a18", edge=False)
        B((fx + sg * hw - (sz * 0.45 if sg > 0 else -sz * 0.1) , y + sz * 0.55, z + 0.02), (sz * 0.35, sz * 0.35, 0.02), "#ffffff", edge=False)


def quad(kind, pos, face=0.0, t=0.0, act="stand", scale=1.0):
    s = SPEC[kind]
    k = scale
    x0, y0, z0 = pos
    out = []

    def B(p, size, col, rots=(), **kw):
        out.append(Box((x0 + p[0] * 1, y0 + p[1], z0 + p[2]), size, col, list(rots), **kw))

    w, h, d, leg, lw = s["w"] * k, s["h"] * k, s["d"] * k, s["leg"] * k, s["lw"] * k
    sitting = act == "sit"
    by = leg if not sitting else leg * 0.35
    # 몸통 (+z 가 앞)
    tilt = [(np.array([x0, y0 + by, z0 - d / 2]), "x", -28)] if sitting else []
    B((-w / 2, by, -d / 2), (w, h, d), s["col"], tilt)
    if s.get("spot"):   # 무늬 조각 (옆구리)
        for sg in (-1, 1):
            B((sg * w / 2 - (0.03 if sg < 0 else 0), by + h * 0.45, -d * 0.15), (0.03, h * 0.35, d * 0.28), s["spot"], tilt, edge=False)
            B((sg * w / 2 - (0.03 if sg < 0 else 0), by + h * 0.2, d * 0.18), (0.03, h * 0.25, d * 0.18), s["spot"], tilt, edge=False)
    # 다리 4개 (걷기: 대각선 다리가 같이)
    sw = math.sin(t * 2 * math.pi / 0.9) * (24 if act == "walk" else 0)
    for i, (sx, sz) in enumerate(((-1, 1), (1, 1), (-1, -1), (1, -1))):
        lx = sx * (w / 2 - lw * 0.55) - lw / 2
        lz = sz * (d / 2 - lw * 0.7) - lw / 2
        ph = sw if (i in (0, 3)) else -sw
        if sitting and sz < 0:      # 앉으면 뒷다리는 접어 바닥에
            B((lx, 0, lz - lw * 0.5), (lw, leg * 0.35, lw * 2), s["col"])
            continue
        piv = np.array([x0 + lx + lw / 2, y0 + by, z0 + lz + lw / 2])
        B((lx, 0, lz), (lw, by if not sitting else leg, lw), s["col"], [(piv, "x", ph)])
        B((lx - 0.01, 0, lz - 0.01), (lw + 0.02, min(0.22 * k, leg * 0.2), lw + 0.02), "#3b2c22" if kind in ("ox", "donkey", "goat", "hippo") else s.get("belly", s["col"]), [(piv, "x", ph)])
    # 머리
    hw_, hh, hdp = (v * k for v in s["hd"])
    eat = act == "eat"
    hy = by + h * (0.55 if not sitting else 1.05)
    hz = d / 2 - hdp * 0.25 + (0 if not sitting else -0.15 * k)
    bobh = math.sin(t * 2 * math.pi / 2.6) * 0.04 * k
    hrot = [(np.array([x0, y0 + hy, z0 + d / 2]), "x", 55 + 8 * math.sin(t * 2.2) if eat else 4 * math.sin(t * 1.3))]
    if kind == "hippo":
        hy, hz = by + h * 0.2, d / 2 - hdp * 0.2
    head = []

    def HB(p, size, col, **kw):
        head.append(Box((x0 + p[0], y0 + p[1] + bobh, z0 + p[2]), size, col, list(hrot), **kw))

    HB((-hw_ / 2, hy, hz), (hw_, hh, hdp), s["col"])
    fz = hz + hdp
    # 주둥이 + 콧구멍
    mo = 0.0
    if act == "open":
        mo = (0.5 + 0.5 * math.sin(t * 2 * math.pi / 1.6)) * hh * 0.35
    snw = hw_ * {"cat": 0.32, "dog": 0.5}.get(kind, 0.75)
    snh = hh * {"cat": 0.22, "dog": 0.32}.get(kind, 0.45)
    HB((-snw / 2, hy + 0.02 * k - mo * 0.0, fz - 0.02), (snw, snh, (0.35 if kind not in ("cat",) else 0.12) * k * (1.6 if kind == "hippo" else 1)), s["nose"])
    if mo:
        HB((-snw / 2, hy - mo, fz - 0.02), (snw, mo, 0.3 * k * (1.6 if kind == "hippo" else 1)), "#7a2a2a", edge=False)
    nz = fz - 0.02 + (0.35 if kind != "cat" else 0.12) * k * (1.6 if kind == "hippo" else 1)
    for sg in (-1, 1):
        HB((sg * snw * 0.22 - 0.05 * k, hy + snh * 0.55, nz), (0.1 * k, 0.1 * k, 0.02), "#3a2622", edge=False)
    _eyes(HB, 0, hy + hh * 0.6, fz + 0.005, hw_ * 0.32, 0.17 * k if kind not in ("hippo", "ox") else 0.2 * k)
    # 귀·뿔
    if s.get("ear"):
        el = s["ear"] * k
        for sg in (-1, 1):
            if kind in ("cat", "dog", "hippo"):
                HB((sg * hw_ * 0.3 - 0.1 * k, hy + hh, hz + hdp * 0.35), (0.2 * k, el * (0.8 if kind == "dog" else 1), 0.16 * k), s["col"])
            else:   # 당나귀: 긴 귀
                HB((sg * hw_ * 0.3 - 0.11 * k, hy + hh, hz + hdp * 0.15), (0.22 * k, el, 0.14 * k), s["col"])
                HB((sg * hw_ * 0.3 - 0.07 * k, hy + hh + 0.05, hz + hdp * 0.15 + 0.13 * k), (0.14 * k, el * 0.8, 0.02), "#4a4440", edge=False)
    if s.get("horn"):
        for sg in (-1, 1):
            if kind == "ox":
                HB((sg * (hw_ / 2) - (0.45 * k if sg < 0 else 0), hy + hh * 0.85, hz + hdp * 0.4), (0.45 * k, 0.18 * k, 0.18 * k), s["horn"])
                HB((sg * (hw_ / 2 + 0.3 * k) - 0.09 * k, hy + hh * 0.85, hz + hdp * 0.4), (0.18 * k, 0.45 * k, 0.18 * k), s["horn"])
            else:
                HB((sg * hw_ * 0.25 - 0.08 * k, hy + hh, hz + hdp * 0.2), (0.16 * k, 0.45 * k, 0.16 * k), s["horn"])
    if s.get("beard"):
        HB((-0.1 * k, hy - 0.3 * k, fz - 0.05), (0.2 * k, 0.32 * k, 0.12 * k), s["beard"])
    if s.get("mane"):
        HB((-0.12 * k, hy + hh * 0.7, hz - 0.02), (0.24 * k, 0.25 * k, hdp * 0.8), s["mane"])
        B((-0.12 * k, by + h, d / 2 - 0.6 * k), (0.24 * k, 0.22 * k, 0.6 * k), s["mane"])
    out += head
    # 꼬리 (살랑)
    tl = s.get("tail", 0.5) * k
    tw = 14 * math.sin(t * 2 * math.pi / 1.3)
    tp = np.array([x0, y0 + by + h * 0.85, z0 - d / 2])
    if kind == "cat":
        B((-0.07 * k, by + h * 0.7, -d / 2 - tl * 0.15), (0.14 * k, tl, 0.14 * k), s["col"], [(tp, "x", -25), (tp, "z", tw)])
    else:
        B((-0.07 * k, by + h * 0.85 - tl, -d / 2 - 0.08 * k), (0.14 * k, tl, 0.14 * k), s["col"], [(tp, "z", tw)])
        B((-0.1 * k, by + h * 0.85 - tl - 0.2 * k, -d / 2 - 0.1 * k), (0.2 * k, 0.28 * k, 0.2 * k), s.get("mane", "#3b2c22"), [(tp, "z", tw)])
    return _rot_all(out, (x0, y0, z0), face)


def ibis(pos, face=0.0, t=0.0, act="stand", scale=1.0):
    """따오기(나일강의 흰 새): 흰 몸 + 검은 머리·목 + 길게 휜 부리 + 가는 다리"""
    k = scale
    x0, y0, z0 = pos
    out = []

    def B(p, size, col, rots=(), **kw):
        out.append(Box((x0 + p[0], y0 + p[1], z0 + p[2]), size, col, list(rots), **kw))

    ly = 1.0 * k
    step = math.sin(t * 2 * math.pi / 0.8) * (20 if act == "walk" else 0)
    for sg in (-1, 1):
        piv = np.array([x0 + sg * 0.15 * k, y0 + ly, z0])
        B((sg * 0.15 * k - 0.04 * k, 0, -0.04 * k), (0.08 * k, ly, 0.08 * k), "#2b2b2b", [(piv, "x", step * sg)])
        B((sg * 0.15 * k - 0.08 * k, 0, -0.02 * k), (0.16 * k, 0.04 * k, 0.3 * k), "#2b2b2b", [(piv, "x", step * sg)])
    B((-0.35 * k, ly, -0.6 * k), (0.7 * k, 0.6 * k, 1.1 * k), "#f4f1ea")
    B((-0.36 * k, ly + 0.05 * k, -0.85 * k), (0.72 * k, 0.35 * k, 0.35 * k), "#2b2b2b")   # 검은 꽁지
    peck = act == "eat"
    nr = [(np.array([x0, y0 + ly + 0.5 * k, z0 + 0.4 * k]), "x", 70 + 10 * math.sin(t * 3) if peck else 5 * math.sin(t * 1.5))]
    B((-0.1 * k, ly + 0.45 * k, 0.3 * k), (0.2 * k, 0.7 * k, 0.2 * k), "#2b2b2b", nr)          # 목
    B((-0.16 * k, ly + 1.05 * k, 0.22 * k), (0.32 * k, 0.3 * k, 0.4 * k), "#2b2b2b", nr)       # 머리
    for sg in (-1, 1):
        B((sg * 0.16 * k - (0.03 * k if sg > 0 else 0), ly + 1.2 * k, 0.48 * k), (0.03 * k, 0.07 * k, 0.07 * k), "#ffffff", nr, edge=False)
    bp = [(np.array([x0, y0 + ly + 1.12 * k, z0 + 0.6 * k]), "x", 28)] + nr   # 길게 아래로 휜 부리 (한 조각, 머리 앞에서 시작)
    B((-0.04 * k, ly + 1.08 * k, 0.58 * k), (0.08 * k, 0.08 * k, 0.75 * k), "#2b2b2b", bp)
    return _rot_all(out, (x0, y0, z0), face)


def croc(pos, face=0.0, t=0.0, act="stand", scale=1.0):
    """악어: 낮고 긴 몸 + 등의 돌기 + 긴 주둥이(입 벌리기) + 짧은 다리 + 긴 꼬리"""
    k = scale
    x0, y0, z0 = pos
    out = []

    def B(p, size, col, rots=(), **kw):
        out.append(Box((x0 + p[0], y0 + p[1], z0 + p[2]), size, col, list(rots), **kw))

    G, G2, BL = "#5c7a3a", "#3f5a28", "#d8d2a2"
    B((-0.8 * k, 0.35 * k, -1.6 * k), (1.6 * k, 0.6 * k, 3.2 * k), G)
    B((-0.75 * k, 0.33 * k, -1.5 * k), (1.5 * k, 0.05 * k, 3.0 * k), BL, edge=False)
    for i in range(6):   # 등 돌기
        B((-0.45 * k, 0.95 * k, -1.4 * k + i * 0.5 * k), (0.25 * k, 0.15 * k, 0.3 * k), G2)
        B((0.2 * k, 0.95 * k, -1.2 * k + i * 0.5 * k), (0.25 * k, 0.15 * k, 0.3 * k), G2)
    sw = math.sin(t * 2 * math.pi / 1.0) * (25 if act == "walk" else 0)
    for i, (sx, sz) in enumerate(((-1, 1), (1, 1), (-1, -1), (1, -1))):
        piv = np.array([x0 + sx * 0.85 * k, y0 + 0.4 * k, z0 + sz * 1.0 * k])
        B((sx * 0.85 * k - 0.2 * k, 0, sz * 1.0 * k - 0.2 * k), (0.4 * k, 0.45 * k, 0.4 * k), G, [(piv, "y", (sw if i in (0, 3) else -sw))])
    wag = 10 * math.sin(t * 2 * math.pi / 2.0)
    tp = np.array([x0, y0, z0 - 1.6 * k])
    B((-0.5 * k, 0.4 * k, -3.0 * k), (1.0 * k, 0.45 * k, 1.4 * k), G, [(tp, "y", wag)])
    B((-0.3 * k, 0.4 * k, -4.2 * k), (0.6 * k, 0.32 * k, 1.2 * k), G, [(tp, "y", wag * 1.6)])
    # 머리: 위턱 + 아래턱(입 벌리기)
    mo = (0.5 + 0.5 * math.sin(t * 2 * math.pi / 2.2)) * 22 if act == "open" else 2
    jp = np.array([x0, y0 + 0.5 * k, z0 + 1.6 * k])
    B((-0.65 * k, 0.5 * k, 1.6 * k), (1.3 * k, 0.45 * k, 0.6 * k), G)
    B((-0.45 * k, 0.55 * k, 2.2 * k), (0.9 * k, 0.32 * k, 1.5 * k), G, [(jp, "x", -mo)])
    B((-0.42 * k, 0.35 * k, 2.2 * k), (0.84 * k, 0.2 * k, 1.45 * k), G2, [(jp, "x", mo * 0.4)])
    for i in range(5):   # 이빨 (흰 작은 조각)
        B((-0.42 * k, 0.52 * k, 2.3 * k + i * 0.28 * k), (0.06 * k, 0.07 * k, 0.08 * k), "#ffffff", [(jp, "x", -mo)], edge=False)
        B((0.36 * k, 0.52 * k, 2.3 * k + i * 0.28 * k), (0.06 * k, 0.07 * k, 0.08 * k), "#ffffff", [(jp, "x", -mo)], edge=False)
    for sg in (-1, 1):   # 툭 튀어나온 눈
        B((sg * 0.38 * k - 0.15 * k, 0.95 * k, 1.75 * k), (0.3 * k, 0.22 * k, 0.3 * k), G)
        B((sg * 0.38 * k - 0.07 * k, 1.0 * k, 2.04 * k), (0.14 * k, 0.14 * k, 0.03), "#e8c13a", edge=False)
        B((sg * 0.38 * k - 0.02 * k, 1.0 * k, 2.06 * k), (0.05 * k, 0.14 * k, 0.02), "#1d1a18", edge=False)
    return _rot_all(out, (x0, y0, z0), face)


def animal(kind, pos, face=0.0, t=0.0, act="stand", scale=1.0):
    if kind == "ibis":
        return ibis(pos, face, t, act, scale)
    if kind == "croc":
        return croc(pos, face, t, act, scale)
    return quad(kind, pos, face, t, act, scale)


if __name__ == "__main__":   # 동물 모음 시트: python 블록동물.py <결과.png>
    import sys
    from PIL import Image, ImageDraw, ImageFont
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "output", "블록동물_모음.png")
    kinds = ["ox", "donkey", "goat", "dog", "cat", "hippo", "ibis", "croc"]
    names = {"ox": "소", "donkey": "당나귀", "goat": "염소", "dog": "개", "cat": "고양이", "hippo": "하마", "ibis": "따오기", "croc": "악어"}
    E.W, E.H = 480, 400
    tiles = []
    for kd in kinds:
        bx = animal(kd, (0, 0, 0), face=90, t=0.3, act="stand")
        allv = np.concatenate([b.corners() for b in bx])
        c = (allv.min(0) + allv.max(0)) / 2
        r = float(np.linalg.norm(allv.max(0) - allv.min(0)))
        cam = E.Camera((c[0] + r * 0.75, c[1] + r * 0.45, c[2] + r * 1.15), tuple(c), 40)
        im = E.render(bx, cam, bg=(236, 240, 232)).resize((480, 400))
        ImageDraw.Draw(im).text((14, 10), names[kd], fill=(40, 40, 40), font=ImageFont.truetype("/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf", 30))
        tiles.append(im)
    sheet = Image.new("RGB", (480 * 4, 400 * 2), "white")
    for i, im in enumerate(tiles):
        sheet.paste(im, ((i % 4) * 480, (i // 4) * 400))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    sheet.save(out)
    print(out)
