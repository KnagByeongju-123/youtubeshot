"""블록 바다 생물·물건 — 《고래가 남긴 마지막 선물》 등장

크기 단위: 장면 1 = 1미터. scale = 블록 한 칸의 실제 크기.
몸이 긴 생물은 마디(seg0, seg1 …)로 나눠 마디를 돌리면 헤엄침 (고래 = 위아래, 물고기·상어·먹장어 = 좌우).
앞(머리)은 -y 쪽.
"""
import math

from 블록 import Model


def _ellipse_body(part_of, L, a_fn, b_fn, col_fn, c_fn=lambda t: 0.0, top_cap=None):
    """머리(-y 쪽, y=0)에서 꼬리(y=L-1)까지, 단면이 타원인 몸통. part_of(y) → 그 y 의 부위"""
    for y in range(L):
        t = y / (L - 1)
        a, b, c = a_fn(t), b_fn(t), c_fn(t)
        R = int(math.ceil(max(a, b))) + 1
        for x in range(-R, R + 1):
            for z in range(-R + int(c) - 1, R + int(c) + 2):
                if (x / max(a, 0.5)) ** 2 + ((z - c) / max(b, 0.5)) ** 2 <= 1.0:
                    if top_cap and z > top_cap(t, c, b):
                        continue
                    part_of(y).set(x, y, z, col_fn(x, y, z, t, a, b, c))


def _segments(m, L, cuts, parent0=None):
    """y 로 나눈 마디 부위들. cuts = 마디가 시작하는 y 목록(첫 값 0). 돌려주는 것: part_of(y)"""
    segs = []
    for i, y0 in enumerate(cuts):
        segs.append(m.part(f"seg{i}", (0, y0 - 0.5 if i else 0, 0), f"seg{i - 1}" if i else parent0))

    def part_of(y):
        k = 0
        for i, y0 in enumerate(cuts):
            if y >= y0:
                k = i
        return segs[k]
    return part_of, segs


def _top_z(part_lookup, x, y):
    zs = [k[2] for k in part_lookup if k[0] == x and k[1] == y]
    return max(zs) if zs else None


# ---------------------------------------------------------------- 혹등고래
def humpback(name="보름이", L=48, scale=0.31, crescent=3, dark="#232b35", pale="#d6dadd", groove="#aeb5ba"):
    pal = {"dark": dark, "dark2": "#2d3743", "pale": pale, "groove": groove, "eye": "#0b0d10",
           "knob": "#1a2028", "moon": "#f4f2ea", "fin": "#cfd4d6", "finedge": "#3a434d"}
    m = Model(name, pal, scale)
    cuts = [0, int(L * 0.22), int(L * 0.38), int(L * 0.53), int(L * 0.67), int(L * 0.79), int(L * 0.87)]
    part_of, segs = _segments(m, L, cuts)
    amax = L * 0.125
    bmax = L * 0.12

    def f(t):
        if t < 0.32:
            return 0.22 + 0.78 * math.sin(math.pi / 2 * t / 0.32) ** 0.8
        return max(0.13, math.cos(math.pi / 2 * (t - 0.32) / 0.6) ** 1.3)

    def g(t):
        if t < 0.32:
            return 0.45 + 0.55 * math.sin(math.pi / 2 * t / 0.32)
        return max(0.30, f(t)) if t > 0.6 else f(t)

    def col(x, y, z, t, a, b, c):
        rel = (z - c) / max(b, 0.5)
        if rel < -0.35 and t < 0.55:                       # 배의 주름(세로 줄무늬)
            return "pale" if x % 2 == 0 else "groove"
        if rel < -0.55 and t < 0.8:
            return "pale"
        return "dark" if (x + y) % 5 else "dark2"
    _ellipse_body(part_of, int(L * 0.9), lambda t: amax * f(t * 0.9), lambda t: bmax * g(t * 0.9), col,
                  c_fn=lambda t: -0.08 * bmax * math.sin(math.pi * min(1, t / 0.6)),
                  top_cap=lambda t, c, b: c + b * 0.72 if t < 0.2 else 1e9)
    allv = {}
    for s in segs:
        allv.update(s.vox)
    # 입선: 머리 옆에 어두운 줄
    for y in range(1, int(L * 0.2)):
        t = y / (L - 1)
        a, c = amax * f(t), -0.08 * bmax * math.sin(math.pi * min(1, t / 0.6))
        z = int(round(c - bmax * f(t) * 0.12))
        for x in (-int(round(a * 0.98)), int(round(a * 0.98))):
            if (x, y, z) in allv:
                part_of(y).set(x, y, z, "eye")
    # 눈
    ye = int(L * 0.2)
    ae = amax * f(ye / (L - 1))
    for sx in (-1, 1):
        x = sx * int(round(ae))
        z = int(round(-bmax * 0.1))
        part_of(ye).set(x, ye, z, "eye")
        part_of(ye).set(x + sx, ye, z, "eye")
    # 머리 위 혹(결절)
    for y in range(1, int(L * 0.19), 3):
        for x in (-2, 0, 2):
            zt = _top_z(part_of(y).vox, x, y)
            if zt is not None:
                part_of(y).set(x, y, zt + 1, "knob")
    # 숨구멍
    yb = int(L * 0.21)
    for x in (-1, 1):
        zt = _top_z(part_of(yb).vox, x, yb)
        if zt is not None:
            part_of(yb).set(x, yb, zt, "eye")
    # 하얀 반달 무늬 (머리 위, 숨구멍 앞)
    if crescent:
        y0 = int(L * 0.12)
        for k in range(0, 181, 12):
            ang = math.radians(k)
            x = int(round(crescent * math.cos(ang)))
            y = int(round(y0 - crescent * 0.8 * math.sin(ang)))
            for yy in (y, y + 1):
                zt = _top_z(part_of(yy).vox, x, yy)
                if zt is not None:
                    part_of(yy).set(x, yy, zt, "moon")
    # 등지느러미(작은 혹 + 지느러미)
    yd = int(L * 0.66)
    for i, y in enumerate(range(yd - 2, yd + 3)):
        zt = _top_z(part_of(y).vox, 0, y)
        if zt is not None:
            h = [1, 2, 3, 2, 1][i]
            for dz in range(1, h + 1):
                part_of(y).set(0, y, zt + dz, "dark")
    # 가슴지느러미 (몸길이의 1/3, 하얗고 앞쪽 가장자리에 혹)
    yf = int(L * 0.27)
    af = amax * f(yf / (L - 1))
    zf = -bmax * 0.35
    flen = int(L * 0.32)
    for sx, nm in ((-1, "fin_l"), (1, "fin_r")):
        root = (sx * (af - 0.5), yf, zf)
        fp = m.part(nm, root, f"seg{1 if yf >= cuts[1] else 0}")
        for i in range(flen):
            x = int(round(sx * (af + i * 0.78)))
            yc = yf + i * 0.55
            z = int(round(zf - i * 0.32))
            w = 3 if i < flen * 0.5 else (2 if i < flen * 0.85 else 1)
            for dy in range(w):
                y = int(round(yc)) + dy
                fp.set(x, y, z, "fin" if dy else ("finedge" if i % 3 == 1 else "fin"))
    # 꼬리지느러미 (마지막 마디)
    ft = part_of(L - 1)
    yt = int(L * 0.88)
    span = int(L * 0.18)
    ct = 0
    for x in range(-span, span + 1):
        ax = abs(x)
        lead = yt + ax * 0.42
        trail = lead + max(1.0, 4.0 - ax * 0.28) - (1.5 if ax <= 1 else 0)
        for y in range(int(round(lead)), int(round(trail)) + 1):
            serr = (ax > 2 and (x + y) % 3 == 0 and y == int(round(trail)))
            if serr:
                continue
            ft.set(x, y, ct, "dark")
            if ax < span - 1:
                ft.set(x, y, ct - 1, "pale" if (x * 7 + y) % 9 else "dark")
    # 꼬리자루(몸통 끝 ~ 꼬리지느러미 사이)를 이어 줌
    for y in range(int(L * 0.76), yt + 2):
        for z in range(-1, 2):
            part_of(y).set(0, y, z, "dark")
    return m


def 보름이():
    return humpback("보름이")


def 어린고래():
    return humpback("어린고래", L=40, scale=0.17, crescent=2, dark="#38424e", pale="#dfe2e4", groove="#bcc2c6")


# ---------------------------------------------------------------- 고래 뼈 (살이 사라진 뒤)
def 고래뼈(L=48, scale=0.31):
    pal = {"bone": "#e9e3d1", "bone2": "#d3cbb4", "dark": "#8f8670"}
    m = Model("고래뼈", pal, scale)
    sk = m.part("skull", (0, 0, 0))
    # 머리뼈: 앞이 좁고 뒤가 넓은 납작한 쐐기
    for y in range(0, int(L * 0.24)):
        w = int(1 + (y / (L * 0.24)) * 5)
        sk.box(-w, w, y, y, 0, 1, "bone")
        if y > L * 0.12:
            sk.box(-w + 1, w - 1, y, y, 2, 2, "bone2")
    # 아래턱뼈 두 개 (바깥으로 휜 활 모양)
    for sx in (-1, 1):
        for y in range(0, int(L * 0.25)):
            x = sx * int(round(2 + 5 * math.sin(math.pi * y / (L * 0.25)) + y * 0.08))
            sk.set(x, y, -2, "bone2")
    sp = m.part("spine", (0, int(L * 0.24), 0), "skull")
    for y in range(int(L * 0.24), int(L * 0.95)):
        sp.box(-1, 1, y, y, 1, 2, "bone" if y % 2 else "bone2")
        if y % 2 == 0 and y < L * 0.8:
            sp.set(0, y, 3, "bone")                   # 등뼈 돌기
            sp.set(0, y, 4, "bone2")
    # 갈비뼈 (반원으로 휘어 내려옴, 일부는 무너져 바닥에)
    for i, y in enumerate(range(int(L * 0.27), int(L * 0.5), 2)):
        rr = 6 - abs(i - 4) * 0.4
        for sx in (-1, 1):
            for k in range(0, 100, 8):
                ang = math.radians(k)
                x = sx * int(round(1 + rr * math.sin(ang)))
                z = int(round(1 - rr * (1 - math.cos(ang))))
                if z < -6:
                    continue
                sp.set(x, y, z, "bone")
    # 가슴지느러미 뼈 (손가락처럼 갈라짐)
    for sx in (-1, 1):
        for i in range(12):
            x = sx * (6 + i)
            y = int(L * 0.3) + i // 2
            sp.set(x, y, -5, "bone")
            if i > 6:
                sp.set(x, y + 2, -5, "bone2")
    return m


# ---------------------------------------------------------------- 먹장어 (긴 몸, 좌우로 헤엄)
def 먹장어(L=30, scale=0.02):
    pal = {"skin": "#b68a80", "belly": "#d6b3a8", "dark": "#5a3c38", "barbel": "#e5c7bd"}
    m = Model("먹장어", pal, scale)
    part_of, segs = _segments(m, L, [0, 5, 10, 15, 20, 25])

    def col(x, y, z, t, a, b, c):
        if z < c - b * 0.4:
            return "belly"
        if abs(x) >= a - 0.6 and z < c and y % 3 == 0 and 4 < y < 10:
            return "dark"                           # 아가미 구멍 줄
        return "skin"
    _ellipse_body(part_of, L, lambda t: 1.6 * (0.8 if t < 0.05 else (1 if t < 0.8 else max(0.4, 1 - (t - 0.8) * 3))),
                  lambda t: 1.6 * (0.8 if t < 0.05 else 1.0), col)
    hd = segs[0]
    for x in (-1, 1):                               # 입가의 수염
        hd.set(x, -1, -1, "barbel")
        hd.set(x, -2, -1, "barbel")
        hd.set(x * 2, -1, 0, "barbel")
    # 꼬리 지느러미 테두리 (위아래로 납작)
    tl = segs[-1]
    for y in range(L - 7, L):
        for z in (2, -2):
            tl.set(0, y, z, "skin")
    return m


# ---------------------------------------------------------------- 잠꾸러기 상어 (느린 깊은 바다 상어)
def 상어(L=40, scale=0.1):
    pal = {"skin": "#4d4a45", "skin2": "#57534d", "belly": "#68645d", "eye": "#9fd4c8", "dark": "#22211f"}
    m = Model("상어", pal, scale)
    part_of, segs = _segments(m, L, [0, 8, 15, 22, 28, 33])

    def f(t):
        if t < 0.25:
            return 0.62 + 0.38 * math.sin(math.pi / 2 * t / 0.25)
        return max(0.14, math.cos(math.pi / 2 * (t - 0.25) / 0.78))

    def col(x, y, z, t, a, b, c):
        if z < c - b * 0.45:
            return "belly"
        return "skin" if (x * 3 + y + z) % 4 else "skin2"
    _ellipse_body(part_of, int(L * 0.86), lambda t: 4.0 * f(t * 0.86), lambda t: 4.2 * f(t * 0.86), col)
    a7 = 4.0 * f(7 / (L - 1))
    for sx in (-1, 1):
        part_of(5).set(sx * int(round(4.0 * f(5 / (L - 1)) - 0.3)), 5, 1, "eye")
        for k in range(5):                           # 아가미 틈 다섯 개
            y = 8 + k
            for z in (-1, 0, 1):
                part_of(y).set(sx * int(round(a7)), y, z, "dark")
        for i in range(5):                           # 가슴지느러미(작음)
            part_of(10).set(sx * (int(a7) + 1 + i), 10 + i // 2, -2 - i // 2, "skin")
    for y in range(1, 6):                            # 입(머리 아래)
        part_of(y).set(0, y + 1, -3, "dark")
        part_of(y).set(-1, y + 1, -3, "dark")
        part_of(y).set(1, y + 1, -3, "dark")
    for y0, h in ((int(L * 0.5), 2), (int(L * 0.66), 2)):   # 낮은 등지느러미 둘
        for i in range(4):
            zt = _top_z(part_of(y0 + i).vox, 0, y0 + i)
            if zt is not None:
                for dz in range(1, (h if 0 < i < 3 else 1) + 1):
                    part_of(y0 + i).set(0, y0 + i, zt + dz, "skin")
    tl = segs[-1]                                    # 꼬리: 위쪽이 더 긴 지느러미
    for i in range(9):
        y = int(L * 0.84) + i
        tl.set(0, y, 1 + i // 1 if i < 7 else 7, "skin")
        for z in range(1, min(8, 1 + i)):
            if y + (7 - z) // 3 < L + 2:
                tl.set(0, y, z, "skin")
        for z in range(-min(4, i // 2), 1):
            tl.set(0, y, z, "skin")
    return m


# ---------------------------------------------------------------- 게 (다리 8개 + 집게 2개, 옆으로 걸음)
def 게(scale=0.03):
    pal = {"shell": "#c4472f", "shell2": "#a83a26", "under": "#e4a27c", "eye": "#141414", "claw": "#d55538", "tip": "#2b1a14"}
    m = Model("게", pal, scale)
    b = m.part("body", (0, 0, 4))
    b.box(-3, 3, -3, 2, 3, 4, "shell")
    b.box(-2, 2, -2, 1, 5, 5, "shell2")
    b.box(-3, 3, -3, 2, 3, 3, "under")
    b.box(-4, 4, -2, 1, 4, 4, "shell")
    for x in (-1, 1):                                # 눈자루
        b.set(x, -4, 5, "shell")
        b.set(x, -4, 6, "eye")
    for sx in (-1, 1):                               # 집게 (앞쪽)
        side = "r" if sx > 0 else "l"
        c = m.part(f"claw_{side}", (sx * 3, -3, 4), "body")
        c.set(sx * 3, -4, 4, "claw")
        c.set(sx * 3, -5, 4, "claw")
        c.box(sx * 3, sx * 4, -7, -6, 4, 5, "claw")
        c.set(sx * 3, -8, 5, "tip")
        c.set(sx * 4, -8, 4, "tip")
        for i, y in enumerate((-2, 0, 1, 2)):         # 다리 4쌍 (밖으로 뻗었다가 아래로)
            lg = m.part(f"leg_{side}{i}", (sx * 4, y, 4), "body")
            lg.set(sx * 5, y, 4, "shell")
            lg.set(sx * 6, y, 4, "shell")
            lg.set(sx * 7, y, 3, "shell")
            lg.set(sx * 7, y, 2, "shell")
            lg.set(sx * 8, y, 1, "under")
            lg.set(sx * 8, y, 0, "tip")
    return m


# ---------------------------------------------------------------- 옆새우 (쌀알만 한 작은 새우, 떼로 나옴)
def 새우(scale=0.0015):
    pal = {"body": "#ecc0ad", "body2": "#d9a08c", "eye": "#202020", "leg": "#f3d6c9"}
    m = Model("새우", pal, scale)
    b = m.part("body", (0, 0, 4))
    n = 16
    for i in range(n):                               # 활처럼 굽은 몸 (마디마다 색이 번갈아)
        t = i / (n - 1)
        zc = 4 + 3.5 * math.sin(math.pi * t)
        r = 2.2 * (1 - abs(t - 0.4) * 0.9)
        for x in range(-2, 3):
            for z in range(int(zc - r), int(zc + r) + 1):
                if (x / 2.2) ** 2 + ((z - zc) / max(r, 0.8)) ** 2 <= 1:
                    b.set(x, i, z, "body" if (i // 2) % 2 else "body2")
    for x in (-2, 2):
        b.set(x, 1, 6, "eye")
    for i in range(7):                               # 더듬이 두 쌍
        for x in (-1, 1):
            b.set(x, -1 - i, 6 + i // 2, "leg")
    for i in range(2, 13, 2):                        # 다리
        zc = int(4 + 3.5 * math.sin(math.pi * i / (n - 1)) - 2)
        for x in (-2, 2):
            for dz in range(1, 4):
                b.set(x, i, zc - dz, "leg")
    for x in (-1, 0, 1):                             # 꼬리 끝
        b.set(x, n, 3, "body2")
        b.set(x, n + 1, 2, "body2")
    return m


# ---------------------------------------------------------------- 오세닥스 (뼈를 먹는 벌레) — 뼈 조각 위에 여러 마리
def 오세닥스(scale=0.004):
    pal = {"bone": "#e9e3d1", "bone2": "#d3cbb4", "trunk": "#f4f0e6", "plume": "#cf2b3c", "plume2": "#ec6a76", "root": "#7fae6a"}
    m = Model("오세닥스", pal, scale)
    b = m.part("bone", (0, 0, 0))
    b.box(-8, 8, -3, 3, -3, 0, "bone")
    for x in range(-8, 9, 3):
        b.set(x, 0, -3, "bone2")
    spots = [(-6, -1), (-3, 1), (0, -2), (2, 1), (5, -1), (7, 2), (-1, 2)]
    for k, (x, y) in enumerate(spots):
        w = m.part(f"worm{k}", (x, y, 1), "bone")
        h = 3 + k % 2
        for z in range(1, h + 1):
            w.set(x, y, z, "trunk")
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):   # 깃털 네 갈래
            for i in range(1, 4):
                w.set(x + dx * (1 if i < 3 else 2), y + dy * (1 if i < 3 else 2), h + i, "plume" if i < 3 else "plume2")
        w.set(x, y, h + 1, "plume")
    return m


# ---------------------------------------------------------------- 조개들 (홍합·대합·삿갓조개 + 하얀 세균 이불)
def 조개(scale=0.01):
    pal = {"mussel": "#1f2533", "mussel2": "#3a3a44", "clam": "#e6ddc8", "clam2": "#bfb39a", "limpet": "#b59468", "limpet2": "#8d6f4b",
           "mat": "#f6f6f2", "mat2": "#e2e4dc", "bone": "#e9e3d1"}
    m = Model("조개들", pal, scale)
    b = m.part("bed", (0, 0, 0))
    b.box(-10, 10, -5, 5, -2, -1, "bone")
    import random
    rnd = random.Random(3)
    for x in range(-10, 11):                          # 세균 이불(울퉁불퉁)
        for y in range(-5, 6):
            if rnd.random() < 0.7:
                b.set(x, y, 0, "mat" if rnd.random() < 0.7 else "mat2")
                if rnd.random() < 0.25:
                    b.set(x, y, 1, "mat")
    for k, (x, y) in enumerate([(-8, -3), (-6, -2), (-7, 0), (-5, 1)]):   # 홍합(길쭉, 검푸름)
        mp = m.part(f"mussel{k}", (x, y, 1), "bed")
        mp.box(x, x + 1, y, y + 3, 1, 2, "mussel")
        mp.set(x, y + 3, 2, "mussel2")
    for k, (x, y) in enumerate([(0, -3), (3, 1)]):                         # 대합(둥글고 하얗게)
        cp = m.part(f"clam{k}", (x, y, 1), "bed")
        cp.box(x - 1, x + 1, y - 1, y + 1, 1, 2, "clam")
        cp.box(x - 2, x + 2, y, y, 1, 1, "clam")
        cp.box(x - 1, x + 1, y, y, 2, 2, "clam2")
    for k, (x, y) in enumerate([(7, -3), (8, 2), (5, 3)]):                 # 삿갓조개(작은 원뿔)
        lp = m.part(f"limpet{k}", (x, y, 1), "bed")
        lp.box(x - 1, x + 1, y - 1, y + 1, 1, 1, "limpet")
        lp.set(x, y, 2, "limpet2")
    return m


# ---------------------------------------------------------------- 해파리·발광 물고기 (스스로 빛남)
def 해파리(scale=0.03):
    pal = {"bell": "#7fe3ff", "rim": "#c6f4ff", "core": "#ff8fd8", "tent": "#a8ecff"}
    m = Model("해파리", pal, scale)
    m.glow = {"bell", "rim", "core", "tent"}
    b = m.part("bell", (0, 0, 8))
    for z in range(0, 4):
        r = int(round(math.sqrt(max(0, 16 - (z * 1.3) ** 2))))
        for x in range(-r, r + 1):
            for y in range(-r, r + 1):
                if x * x + y * y <= r * r + 1:
                    b.set(x, y, 8 + z, "bell" if z else "rim")
    b.box(-1, 1, -1, 1, 9, 10, "core")
    for k in range(8):
        ang = k * math.pi / 4
        x0, y0 = int(round(3 * math.cos(ang))), int(round(3 * math.sin(ang)))
        tp = m.part(f"tent{k}", (x0, y0, 8), "bell")
        for z in range(0, 8):
            tp.set(x0 + (1 if z % 4 == 1 else 0), y0, 7 - z, "tent")
    return m


def 발광물고기(scale=0.01):
    pal = {"body": "#3c4552", "belly": "#9aa6b2", "dot": "#6fe8ff", "eye": "#e8eef2", "pupil": "#0d0f12"}
    m = Model("발광물고기", pal, scale)
    m.glow = {"dot"}
    part_of, segs = _segments(m, 14, [0, 5, 9])

    def col(x, y, z, t, a, b, c):
        if z < c - b * 0.3:
            return "dot" if (y % 2 == 0 and abs(x) >= a - 0.7 and 2 < y < 12) else "belly"
        return "body"
    _ellipse_body(part_of, 12, lambda t: 1.3 * (0.8 + 0.2 * math.sin(math.pi * t)) * (1 if t < 0.7 else 1 - (t - 0.7) * 2),
                  lambda t: 2.2 * (0.7 + 0.3 * math.sin(math.pi * t)) * (1 if t < 0.7 else 1 - (t - 0.7) * 2), col)
    for sx in (-1, 1):
        part_of(2).set(sx * 1, 1, 1, "eye")
        part_of(2).set(sx * 2, 1, 1, "pupil")
    tl = segs[-1]
    for z in range(-2, 3):
        tl.set(0, 12, z, "body")
        tl.set(0, 13, z * 1 if abs(z) > 0 else 0, "body")
    return m


# ---------------------------------------------------------------- 연구선
def 연구선(scale=0.5):
    pal = {"white": "#f1f2f0", "hull": "#1f3c66", "red": "#a8352d", "win": "#20262e", "crane": "#e07a26", "deck": "#9a9b93", "mast": "#d8dad6"}
    m = Model("연구선", pal, scale)
    h = m.part("hull", (0, 0, 0))
    L = 60
    for y in range(L):
        t = y / (L - 1)
        w = int(round(7 * (math.sin(math.pi / 2 * min(1, t / 0.25)) if t < 0.25 else 1.0)))   # 뱃머리는 좁게
        w = max(1, w)
        bottom = -4 + int(t < 0.15)
        for x in range(-w, w + 1):
            for z in range(bottom, 3):
                if abs(x) == w or z <= bottom or z == 2:
                    h.set(x, y, z, "red" if z <= -3 else ("hull" if z < 1 else "white"))
            h.set(x, y, 2, "deck" if abs(x) < w else "white")
    for y in range(int(L * 0.18), int(L * 0.48)):      # 선실 2층
        h.box(-5, 5, y, y, 3, 6, "white")
        h.box(-4, 4, y, y, 7, 9, "white") if y < int(L * 0.4) else None
    for y in range(int(L * 0.19), int(L * 0.46), 2):    # 창문
        for x in (-5, 5):
            h.set(x, y, 5, "win")
    h.box(-4, 4, int(L * 0.18), int(L * 0.18), 8, 8, "win")   # 조타실 앞창
    h.box(0, 0, int(L * 0.3), int(L * 0.3), 10, 17, "mast")   # 돛대
    h.box(-2, 2, int(L * 0.3), int(L * 0.3), 15, 15, "mast")
    for x in (-5, 5):                                  # 뒤쪽 크레인(A자 틀) — 탐사 장치를 내림
        for z in range(3, 13):
            h.set(x, L - 3 + (z - 3) // 4, z, "crane")
    h.box(-5, 5, L - 1, L - 1, 13, 13, "crane")
    return m


# ---------------------------------------------------------------- 무인 탐사 장치 (카메라·조명 달린 쇠틀)
def 탐사장치(scale=0.12):
    pal = {"frame": "#e8c11f", "frame2": "#c9a414", "cam": "#1c1e22", "lens": "#3d6fa8", "light": "#fffbe6", "float": "#e5582a", "cable": "#2a2a2a"}
    m = Model("탐사장치", pal, scale)
    m.glow = {"light"}
    f = m.part("frame", (0, 0, 0))
    for x in (-4, 4):
        for y in (-4, 4):
            f.box(x, x, y, y, 0, 8, "frame")
    for z in (0, 8):
        f.box(-4, 4, -4, -4, z, z, "frame2")
        f.box(-4, 4, 4, 4, z, z, "frame2")
        f.box(-4, -4, -4, 4, z, z, "frame2")
        f.box(4, 4, -4, 4, z, z, "frame2")
    f.box(-3, 3, -3, 3, 9, 10, "float")                # 위의 부력통(주황)
    f.box(-1, 1, -5, 0, 3, 5, "cam")                   # 카메라
    f.set(0, -6, 4, "lens")
    for x in (-3, 3):                                  # 조명 둘
        f.box(x, x, -5, -5, 6, 7, "light")
    f.box(0, 0, 0, 0, 11, 16, "cable")                 # 줄
    return m


MODELS = {"보름이": 보름이, "어린고래": 어린고래, "고래뼈": 고래뼈, "먹장어": 먹장어, "상어": 상어, "게": 게, "새우": 새우,
          "오세닥스": 오세닥스, "조개": 조개, "해파리": 해파리, "발광물고기": 발광물고기, "연구선": 연구선, "탐사장치": 탐사장치}
