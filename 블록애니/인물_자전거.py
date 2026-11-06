"""《아버지의 자전거》 인물과 자전거 (블록)

사람: 아버지(최만석, 78), 젊은아버지(35년 전), 은비(42), 어린은비(7), 준호(8)
자전거: 빨간자전거(아이용, 아버지가 만듦), 아버지자전거(낡은 검은 짐자전거, 앞 바구니·뒤 짐받이)
자전거 부위: frame(뿌리) → fork(핸들, 좌우로 돌림), wheel_f·wheel_r(바퀴, x 축으로 돌림), crank(페달, x 축으로 돌림)
자전거는 앞이 -y. 바닥 z=0 에 바퀴가 닿음. 블록 크기는 사람과 같음(0.062m)
"""
import math

from 블록 import Model
import 사람

SKIN_OLD = "#d8a985"


def 아버지():
    pal = {"skin": SKIN_OLD, "hair": "#d9d6d0", "top": "#5b6650", "pants": "#5a5650", "shoes": "#2a2522", "eye": "#1b1b1b",
           "mouth": "#a06a58", "apron": "#7a5a3c", "apron2": "#5e4430", "glass": "#c9c9c9", "brow": "#e4e1db", "belt": "#5a5650"}
    return 사람.person("아버지", pal, hair="gray_short", apron=True, brows="brow")


def 젊은아버지():
    pal = {"skin": "#dca47c", "hair": "#1d1a18", "top": "#62724f", "pants": "#4b4a46", "shoes": "#2a2522", "eye": "#1b1b1b",
           "mouth": "#a06a58", "apron": "#86613f", "apron2": "#664a32", "glass": "#c9c9c9", "brow": "#1d1a18", "belt": "#4b4a46"}
    return 사람.person("젊은아버지", pal, hair="short", apron=True, brows="brow")


def 은비():
    pal = {"skin": "#e9bb98", "hair": "#3a2a22", "top": "#e79a8e", "inner": "#f6f3ee", "pants": "#41618c", "shoes": "#f1f1f1",
           "eye": "#1b1b1b", "mouth": "#c0705f", "glass": "#f6f3ee", "belt": "#41618c"}
    return 사람.person("은비", pal, hair="medium", cardigan=True)


def 어린은비():
    pal = {"skin": "#f0c3a0", "hair": "#2a1f1a", "top": "#f2cf3f", "top2": "#fbf6e6", "pants": "#f2cf3f", "shoes": "#c7362f",
           "sock": "#ffffff", "eye": "#1b1b1b", "mouth": "#d06a5c", "tie": "#c7362f", "cheek": "#f0a090"}
    return 사람.kid("어린은비", pal, hair="pigtails", dress=True)


def 준호():
    pal = {"skin": "#eebd99", "hair": "#1e1a18", "top": "#7fb6dd", "pants": "#2f3e5c", "shoes": "#ffffff",
           "eye": "#1b1b1b", "mouth": "#c27060", "cheek": "#eea38e"}
    return 사람.kid("준호", pal, hair="short", shorts=True)


# ---------------------------------------------------------------- 자전거
def _line(part, p0, p1, col):
    n = int(max(abs(p1[i] - p0[i]) for i in range(3))) + 1
    for k in range(n + 1):
        t = k / max(n, 1)
        part.set(*(int(round(p0[i] + (p1[i] - p0[i]) * t)) for i in range(3)), col)


def _wheel(part, cy, cz, r, tire, rim, spoke, hub):
    for y in range(int(cy - r - 1), int(cy + r + 2)):
        for z in range(int(cz - r - 1), int(cz + r + 2)):
            d = math.hypot(y - cy, z - cz)
            if r - 0.6 <= d <= r + 0.45:
                part.set(0, y, z, tire)
            elif r - 1.4 <= d < r - 0.6:
                part.set(0, y, z, rim)
    for k in range(0, 360, 45):                       # 살(바큇살) — 돌아가는 게 보이게
        a = math.radians(k)
        for i in range(1, int(r - 1)):
            part.set(0, int(round(cy + i * math.cos(a))), int(round(cz + i * math.sin(a))), spoke)
    part.box(-1, 1, int(cy), int(cy), int(cz), int(cz), hub)


def bicycle(name, pal, r, base, basket=False, rack=False):
    """r = 바퀴 반지름(칸), base = 앞뒤 바퀴 사이(칸)"""
    m = Model(name, pal, 0.062)
    yf, yr, cz = -base / 2, base / 2, r                # 앞바퀴 y, 뒷바퀴 y, 바퀴 중심 높이
    fr = m.part("frame", (0, 0, 0))
    seat = (0, yr - r * 0.55, cz + r * 1.35)           # 안장 기둥 위
    bb = (0, (yf + yr) / 2 + r * 0.25, cz - r * 0.05)  # 페달 축
    head = (0, yf + r * 0.45, cz + r * 1.2)            # 핸들 기둥 아래
    _line(fr, (0, yr, cz), bb, "frame")               # 체인 받침
    _line(fr, (0, yr, cz), seat, "frame")             # 뒤 받침
    _line(fr, bb, seat, "frame")                       # 안장 기둥
    _line(fr, bb, head, "frame")                       # 아래 대
    _line(fr, seat, head, "frame")                     # 위 대
    fr.box(-1, 1, int(round(seat[1])) - 1, int(round(seat[1])) + 1, int(round(seat[2])) + 1, int(round(seat[2])) + 1, "saddle")
    fr.box(0, 0, int(round(seat[1])) + 2, int(round(seat[1])) + 2, int(round(seat[2])) + 1, int(round(seat[2])) + 1, "saddle")
    _line(fr, (0, yr - 1, cz + 1), (0, bb[1] + 1, cz), "chain")   # 체인
    if rack:                                           # 뒤 짐받이
        fr.box(-1, 1, int(yr - 1), int(yr + r * 0.7), int(cz + r + 1), int(cz + r + 1), "rack")
        _line(fr, (0, yr + r * 0.7, cz + r + 1), (0, yr, cz), "rack")
    fk = m.part("fork", (0, head[1], head[2]), "frame")
    _line(fk, head, (0, yf, cz), "frame")             # 앞 포크
    top = (0, head[1] + 1, head[2] + r * 0.45)
    _line(fk, head, top, "frame")
    fk.box(-4, 4, int(round(top[1])), int(round(top[1])), int(round(top[2])), int(round(top[2])), "bar")  # 핸들
    fk.box(-4, -3, int(round(top[1])), int(round(top[1])), int(round(top[2])), int(round(top[2])), "grip")
    fk.box(3, 4, int(round(top[1])), int(round(top[1])), int(round(top[2])), int(round(top[2])), "grip")
    if basket:                                         # 앞 바구니
        by = int(round(head[1])) - 2
        bz = int(round(head[2]))
        for x in range(-3, 4):
            for y in range(by - 4, by + 1):
                fk.set(x, y, bz - 1, "basket")
                if x in (-3, 3) or y in (by - 4, by):
                    for z in range(bz, bz + 3):
                        if (x + y + z) % 2 == 0 or z == bz + 2:
                            fk.set(x, y, z, "basket")
    wf = m.part("wheel_f", (0, yf, cz), "fork")
    _wheel(wf, yf, cz, r, "tire", "rim", "spoke", "hub")
    wr = m.part("wheel_r", (0, yr, cz), "frame")
    _wheel(wr, yr, cz, r, "tire", "rim", "spoke", "hub")
    ck = m.part("crank", bb, "frame")                 # 페달(앞뒤로 마주 보게)
    ck.box(-1, 1, int(round(bb[1])), int(round(bb[1])), int(round(bb[2])), int(round(bb[2])), "chain")
    for sx, dz in ((-2, 2), (2, -2)):
        _line(ck, (sx, bb[1], bb[2]), (sx, bb[1], bb[2] + dz), "chain")
        ck.box(sx - (1 if sx < 0 else 0), sx + (1 if sx > 0 else 0), int(round(bb[1])) - 1, int(round(bb[1])) + 1,
               int(round(bb[2] + dz)), int(round(bb[2] + dz)), "pedal")
    return m


def 빨간자전거():
    pal = {"frame": "#cf3a32", "saddle": "#f4efe6", "tire": "#232323", "rim": "#c9ccce", "spoke": "#b8bbbd", "hub": "#8a8d90",
           "chain": "#4b4b4b", "bar": "#c9ccce", "grip": "#f4efe6", "pedal": "#2c2c2c"}
    return bicycle("빨간자전거", pal, r=4, base=13)


def 아버지자전거():
    pal = {"frame": "#1f2224", "saddle": "#5b3f2c", "tire": "#1b1b1b", "rim": "#a9acae", "spoke": "#9b9ea0", "hub": "#77797b",
           "chain": "#3d3d3d", "bar": "#a9acae", "grip": "#3b2a20", "pedal": "#2c2c2c", "rack": "#6a6d70", "basket": "#8a6a44"}
    return bicycle("아버지자전거", pal, r=6, base=19, basket=True, rack=True)


MODELS = {"아버지": 아버지, "젊은아버지": 젊은아버지, "은비": 은비, "어린은비": 어린은비, "준호": 준호,
          "빨간자전거": 빨간자전거, "아버지자전거": 아버지자전거}
