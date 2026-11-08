# -*- coding: utf-8 -*-
"""공주 구출 — 판(스테이지)마다 땅에서 출발해 기울어진 층과 사다리를 올라 꼭대기 감옥의 공주를 구함.
판이 끝나면 다음 판이 이어지고(점수도 이어짐), 판마다 영상을 만든 뒤 하나로 합침.

- 2·3·4층 바닥은 층마다 반대로 기울어짐. 전사는 늘 오르막, 통나무는 내리막으로 굴러옴.
- 통나무는 위 하늘에서 4층으로 떨어져 구르다가, 끊어진 바닥·사다리 구멍을 만나면 아래층으로 떨어지고
  그 층의 기울기를 따라 반대로 구름(4층 → 3층 → 2층 → 땅 → 화면 밖). 만나는 순간 전사가 자동으로 점프.
- 층마다 할 일(STAGES 의 "층", 여러 개 가능): "벌" = 날아오는 벌을 활로, "돌" = 하늘에서 떨어지는 돌을 멈췄다 피함
- 판마다 더할 것: "불덩이_섞기"(N 번째마다 통통 튀는 불덩이), "순찰"(층을 왔다 갔다 하는 딱정벌레 — 만나면 점프)
- "운석": 하늘에서 불꼬리 운석이 전사가 있는 층의 바로 앞·뒤에 떨어져 폭발, "무대": 벽돌·사다리 색, 별, 행성(우주 배경)
- 꼭대기 보스("보스"): "우주인"(광선 N번("보스_광선")을 점프로 피하고 화살 N발) 또는 "여왕벌"(날아다니며 침 두 번, 화살 N발)
  → 감옥이 열리고 하트 → N판 클리어!
- "거울": true 인 판은 좌우를 뒤집음(통나무가 반대쪽에서, 공주가 반대쪽에).

  python 블록애니/공주구출_만들기.py 블록애니/장면_공주구출        → 장면_공주구출_1판.json, _2판.json …
  xvfb-run -a .blender_venv/bin/python 블록애니.py 장면 블록애니/장면_공주구출_1판.json 1판.mp4   (판마다)
  .blender_venv/bin/python 블록애니.py 합치기 전체.mp4 1판.mp4 2판.mp4
"""
import json
import math
import random
import sys

STAGES = [
    {"판": 1, "제목": "공주를 구하라!", "층": {1: ("벌", 2), 2: ("돌", 2), 3: (None, 0)},
     "통나무_간격": 2.6, "통나무_빠르기": 5.0, "보스_화살": 3, "거울": False},
    {"판": 2, "제목": "여왕벌의 탑!", "층": {1: [("돌", 2)], 2: [("벌", 3)], 3: [("돌", 1)]},
     "통나무_간격": 1.9, "통나무_빠르기": 6.2, "불덩이_섞기": 3,  # 세 번째마다 통나무 대신 불덩이
     "순찰": [(1, -1.2, 7.0, 1.6), (3, -10.0, 2.2, 1.8)],  # (층, 왼끝, 오른끝, 빠르기) 딱정벌레
     "보스": "여왕벌", "보스_화살": 4, "거울": True},
    {"판": 3, "제목": "거품이 올라온다!", "층": {1: [("벌", 2), ("거품", 0)], 2: [("돌", 1)]},
     "구멍": {1: (-3.4, -1.8), 2: (5.6, 7.2), 3: (-2.0, 2.0)},  # 4층 가운데 4m 끊김 → 징검다리
     "징검다리": {"층": 3, "빠르기": 1.2},
     "거품": {"간격": 0.8},  # 땅에서 계속 올라오는 거품(전사는 피함)
     "통나무_간격": 2.2, "통나무_빠르기": 5.6,
     "순찰": [(1, -1.2, 7.0, 1.5, 5.0)],  # 다섯째 값 = 거품에 갇혀 날아가는 때
     "보스": "우주인", "보스_화살": 4, "보스_광선": 2, "거울": True,
     "하늘색": "#0b2a4a", "무대": {"벽돌색": "#2f8f9d", "벽돌색2": "#256f7a", "사다리색": "#ffffff"}},
    {"판": 5, "제목": "우주에서 운석이 떨어진다!", "층": {1: [("벌", 3)], 3: [("벌", 2)]},
     "통나무_간격": 1.9, "통나무_빠르기": 6.2, "불덩이_섞기": 4,
     "운석": {"간격": 1.4},  # 전사가 있는 층의 바로 앞·뒤에 떨어짐
     "보스": "우주인", "보스_화살": 5, "보스_광선": 2, "거울": False,
     "무대": {"벽돌색": "#7d8aa3", "벽돌색2": "#5f6b85", "사다리색": "#ffd21f", "별": 160,
            "행성": [-14.0, 9.0, 1.6, "#5b6ee1"]}},
]

BASE = [0.0, 3.2, 6.4, 9.6, 12.8]  # 층 높이(가운데 기준): 땅, 2층, 3층, 4층, 꼭대기
DOWN = [-1, 1, -1, 1, 0]  # 내리막 방향(+1 = 오른쪽이 낮음). 땅은 평평하지만 통나무는 왼쪽으로 굴러감
SLOPE = 0.9 / 22
LADDERS = [8.0, -8.0, 8.0, -3.0]  # i 번째 사다리: i층 → i+1층
EDGE = 11.0
TOP_X0 = LADDERS[3] + 0.6  # 꼭대기 층은 사다리 오른쪽부터(왼쪽 위는 하늘 — 통나무가 떨어지는 곳)
DEFAULT_HOLES = {1: (-3.4, -1.8), 2: (5.6, 7.2), 3: (2.8, 4.4)}  # 끊어진 바닥(판마다 "구멍"으로 바꿀 수 있음)
HOLES = dict(DEFAULT_HOLES)
GAP = 0.6
RUN, CLIMB = 5.0, 3.2
JUMP = (0.65, 1.8)
HOLE_JUMP = (0.6, 1.4)
LOG_R = 0.6
LOG_DROP_X, SKY = -9.0, 18.0
FRONT = -1.0  # 인물·감옥·돌은 벽돌 바닥보다 앞줄 → 겹쳐도 가려지지 않음
CAM = [{"초": 0, "위치": [0, -40, 8.3], "보는곳": [0, 0, 8.3], "직교": 32}]


def fz(k, x):
    if k in (1, 2, 3):
        return BASE[k] - DOWN[k] * SLOPE * x
    return BASE[k]


def cuts(k):
    c = []
    if k >= 1:
        c.append((LADDERS[k - 1] - GAP, LADDERS[k - 1] + GAP))
    if k in HOLES:
        c.append(HOLES[k])
    return sorted(c)


def in_cut(k, x, margin=0.9):
    return any(a - margin < x < b + margin for a, b in cuts(k))


class Route:
    """전사의 길. 모든 구간이 직선 → 나중에 점프를 얹음."""

    def __init__(self, x, k, face):
        self.t, self.x, self.k, self.face = 0.0, x, k, face
        self.seg, self.poses, self.faces, self.climbs, self.jumps = [], [(0.0, "서기")], [(0.0, face)], [], []
        self.riding = False

    def pose(self, p, t=None):
        self.poses.append((self.t if t is None else t, p))

    def turn(self, face):
        if face != self.face:
            self.faces += [(self.t, self.face), (self.t + 0.15, face)]
            self.face = face

    def _seg(self, dur, x1, z0, z1):
        self.seg.append((self.t, self.t + dur, self.x, x1, z0, z1, self.k))
        self.t += dur
        self.x = x1

    def wait(self, dur, p="서기"):
        self.pose(p)
        z = self.zc() if self.riding else fz(self.k, self.x)
        self._seg(dur, self.x, z, z)

    def move(self, x1, speed=RUN, p="달리기"):
        self.turn(60 if x1 > self.x else -60)
        dur = abs(x1 - self.x) / speed
        if self.k in HOLES:  # 끊어진 바닥을 지나면 점프
            hc = sum(HOLES[self.k]) / 2
            if min(self.x, x1) < hc < max(self.x, x1):
                self.jumps.append((self.t + abs(hc - self.x) / speed, *HOLE_JUMP))
        self.pose(p)
        self._seg(dur, x1, fz(self.k, self.x), fz(self.k, x1))
        self.pose("서기")

    def climb(self):
        self.turn(180)
        z0, z1 = fz(self.k, self.x), fz(self.k + 1, self.x)
        dur = (z1 - z0) / CLIMB
        self.pose("오르기")
        self.climbs.append((self.t, self.t + dur))
        self._seg(dur, self.x, z0, z1)
        self.k += 1
        self.pose("서기")

    def zc(self):
        return self.seg[-1][5] if self.seg else fz(self.k, self.x)

    def seg_to(self, x1, z1, dur, p=None):
        """정해진 높이로 직선 이동(징검다리·거품)."""
        if p:
            self.pose(p)
        self.seg.append((self.t, self.t + dur, self.x, x1, self.zc(), z1, self.k))
        self.t += dur
        self.x = x1

    def jump_here(self, h, d):
        self.jumps.append((self.t + d / 2, d, h))
        self.wait(d)

    def pos(self, t):
        for t0, t1, x0, x1, z0, z1, k in self.seg:
            if t0 <= t <= t1:
                u = 0 if t1 == t0 else (t - t0) / (t1 - t0)
                return x0 + (x1 - x0) * u, z0 + (z1 - z0) * u, k
        last = self.seg[-1]
        return (last[3], last[5], last[6]) if t > last[1] else (self.seg[0][2], self.seg[0][4], self.seg[0][6])

    def climbing(self, t):
        return any(a <= t <= b for a, b in self.climbs)

    def keys(self, total):
        js = sorted((tc - d / 2, tc + d / 2, h) for tc, d, h in self.jumps)
        merged = []  # 겹치는 점프는 하나로
        for a, b, h in js:
            if merged and a <= merged[-1][1]:
                merged[-1] = (merged[-1][0], max(b, merged[-1][1]), max(h, merged[-1][2]))
            else:
                merged.append((a, b, h))
        out = []
        for i in range(int(total * 24) + 1):
            t = i / 24
            x, z, _ = self.pos(t)
            for a, b, h in merged:
                if a <= t <= b:
                    u = (t - a) / (b - a)
                    z += 4 * h * u * (1 - u)
            out.append({"초": round(t, 3), "위치": [round(x, 3), FRONT, round(z, 3)]})
        ordered = sorted(self.poses, key=lambda e: e[0])

        def pose_at(t):
            cur = "서기"
            for tt, p in ordered:
                if tt <= t:
                    cur = p
            return cur
        for tt, p in self.poses:
            out.append({"초": round(tt, 3), "자세": p})
        for a, b, h in merged:
            out.append({"초": round(a, 3), "자세": "점프"})
            out.append({"초": round(b + 0.001, 3), "자세": pose_at(b + 0.001)})
        for tt, f in self.faces:
            out.append({"초": round(tt, 3), "방향": f})
        out.sort(key=lambda k: k["초"])
        return out


def log_path(t0, x0, v):
    """하늘에서 떨어져 층마다 구르다 구멍으로 떨어지는 통나무의 키(같은 빠르기)."""
    keys, thuds = [], []
    k = 3
    zl = fz(k, x0) + LOG_R
    for i in range(7):
        u = i / 6
        keys.append({"초": round(t0 + 0.7 * u, 3), "위치": [x0, 0, round(SKY - (SKY - zl) * u * u, 3)]})
    t, x = t0 + 0.7, x0
    thuds.append(round(t, 2))
    while True:
        d = DOWN[k]
        if k == 0:
            t += abs(-15 - x) / v
            keys.append({"초": round(t, 3), "위치": [-15.0, 0, LOG_R]})
            break
        ahead = [(a + b) / 2 for a, b in cuts(k) if ((a + b) / 2 - x) * d > 0]
        nx = min(ahead, key=lambda c: abs(c - x)) if ahead else d * (EDGE + 0.3)
        t += abs(nx - x) / v
        keys.append({"초": round(t, 3), "위치": [round(nx, 3), 0, round(fz(k, nx) + LOG_R, 3)]})
        lx = nx + 0.4 * d
        land, top = fz(k - 1, lx) + LOG_R, fz(k, nx) + LOG_R
        for i in range(1, 7):
            u = i / 6
            keys.append({"초": round(t + 0.5 * u, 3), "위치": [round(nx + 0.4 * d * u, 3), 0, round(top - (top - land) * u * u, 3)]})
        t += 0.5
        x, k = lx, k - 1
        thuds.append(round(t, 2))
    return keys, thuds


def interp(keys, t):
    if t < keys[0]["초"] or t > keys[-1]["초"]:
        return None
    for a, b in zip(keys, keys[1:]):
        if a["초"] <= t <= b["초"]:
            u = 0 if b["초"] == a["초"] else (t - a["초"]) / (b["초"] - a["초"])
            return [p + (q - p) * u for p, q in zip(a["위치"], b["위치"])]
    return keys[-1]["위치"]


def build(cfg, start_score=0):
    HOLES.clear()
    HOLES.update(cfg.get("구멍", DEFAULT_HOLES))
    objs, sfx = [], []
    score_ev = []

    def text(txt, t0, t1, x, z, color="#ffffff", size=1.2, y=-3):
        objs.append({"모양": "글자", "내용": txt, "글자크기": size, "색": color,
                     "동작": [{"초": round(t0, 2), "위치": [x, y, z]}, {"초": round(t1, 2), "위치": [x, y, z + 0.15]}]})

    def add_score(t, pts, x, z):
        score_ev.append((round(t, 2), pts))
        text(f"+{pts}", t, t + 0.9, x, z + 2.8, "#ffe14d", 0.9, -2)
        sfx.append({"초": round(t + 0.03, 2), "소리": "동전"})

    def arrow(x0, z0, x1, z1, t_hit, speed=16.0):
        d = math.hypot(x1 - x0, z1 - z0)
        t_fire = t_hit - d / speed * 1.4
        objs.append({"모양": "화살", "동작": [{"초": round(t_fire, 2), "위치": [x0, 0, z0]}, {"초": round(t_hit, 2), "위치": [x1, 0, z1]}]})

    def bees(n):
        """사다리 끝에 서서 날아오는 벌 n 마리를 쏨."""
        target = LADDERS[P.k]
        d = 1 if target > P.x else -1
        P.turn(60 * d)
        P.wait(0.2)
        P.pose("활쏘기")
        t_last = P.t
        for i in range(n):
            th = P.t + 1.4 + 0.9 * i
            xh = P.x + d * (5.0 - 0.9 * i)
            zh = fz(P.k, xh) + (1.6 if i % 2 == 0 else 2.1)
            xs = d * (EDGE + 1)
            ts = th - abs(xh - xs) / 7.0
            objs.append({"모양": "벌", "크기": 1.6, "맞은초": round(th, 2), "동작": [
                {"초": round(ts, 2), "위치": [xs, 0, zh + 0.5]}, {"초": round(th, 2), "위치": [round(xh, 2), 0, round(zh, 2)]},
                {"초": round(th + 0.6, 2), "위치": [round(xh - d * 0.4, 2), 0, round(fz(P.k, xh) + 0.15, 2)]}]})
            arrow(P.x + d * 0.9, fz(P.k, P.x) + 1.45, xh - d * 0.4, zh, th)
            add_score(th, 200, xh, fz(P.k, xh))
            t_last = th
        P.wait(t_last - P.t + 0.4, "활쏘기")

    def rocks(n):
        """사다리까지 가는 길에 하늘에서 돌 n 개 — 멈추면 바로 앞에 떨어지고, 떨어진 뒤 지나감."""
        target = LADDERS[P.k]
        x0 = P.x
        d = 1 if target > x0 else -1
        for i in range(n):
            stop = x0 + (target - x0) * (i + 0.7) / (n + 0.6)
            while in_cut(P.k, stop):
                stop -= d * 0.5
            rx = stop + d * 1.3
            while in_cut(P.k, rx, 0.7):
                rx += d * 0.5
            P.move(stop)
            th = P.t + 0.6
            zg = fz(P.k, rx)
            objs.append({"모양": "글자", "내용": "!", "글자크기": 0.9, "색": "#ff3030", "동작": [
                {"초": round(th - 1.4, 2), "위치": [round(rx, 2), -1.6, zg + 0.3]}, {"초": round(th - 0.05, 2), "위치": [round(rx, 2), -1.6, zg + 0.3]}]})
            ks = [{"초": round(th - 1.0 + u / 10, 3), "위치": [round(rx, 2), FRONT - 0.3, round(SKY - (SKY - (zg + 0.5)) * (u / 10) ** 2, 3)]}
                  for u in range(11)]
            objs.append({"모양": "돌", "반지름": 0.5, "쿵": [round(th, 2)], "등속": True, "동작": ks})
            for k in range(5):
                dx = (0.5 + 0.35 * k) * (1 if k % 2 else -1)
                pk = [{"초": round(th + 0.45 * j / 6, 3), "위치": [round(rx + dx * j / 6, 3), FRONT - 0.3,
                                                                round(zg + 0.25 + 4 * 0.8 * (j / 6) * (1 - j / 6) - 0.13 * j / 6, 3)]}
                      for j in range(7)]
                pk.append({"초": round(th + 0.9, 3), "위치": pk[-1]["위치"]})
                objs.append({"모양": "조각", "반지름": 0.12, "등속": True, "동작": pk})
            add_score(th, 100, rx, zg)
            P.wait(0.35)
            P.pose("놀람")
            P.wait(0.6, "놀람")

    def bubble_capture():
        """거품에 갇혀 위층 높이까지 떠올랐다가 '뽁' 터져 위층에 내려섬(사다리 없이 지름길)."""
        k = P.k
        target = LADDERS[k]
        d = 1 if target > P.x else -1
        xc = P.x + d * 3.0
        while in_cut(k, xc, 0.8) or in_cut(k + 1, xc - d * 0.8, 1.0):
            xc += d * 0.5
        P.move(xc, 3.0, "걷기")
        t_c = P.t + 0.3
        P.wait(0.3)
        z0 = fz(k, xc)
        R = 1.45
        # 아래(땅)에서 올라오는 거품 → 전사를 감쌈 → 함께 떠오름 → 터짐
        rise = []
        zb = -1.0
        t_start = t_c - (z0 + 1.2 - zb) / 2.2
        for j in range(9):
            u = j / 8
            rise.append({"초": round(t_start + (t_c - t_start) * u, 3), "위치": [round(xc, 2), FRONT - 0.5, round(zb + (z0 + 1.2 - zb) * u, 3)]})
        x1 = xc - d * 0.8
        z1 = fz(k + 1, x1) + 0.9
        dur = 1.8
        P.climbs.append((t_c, t_c + dur + 0.4))
        P.pose("놀람")
        n = 12
        for j in range(1, n + 1):
            u = j / n
            xx = xc + (x1 - xc) * u + 0.25 * math.sin(u * 2 * math.pi)
            P.seg_to(round(xx, 3), round(z0 + (z1 - z0) * u, 3), dur / n)
            rise.append({"초": round(P.t, 3), "위치": [round(xx, 3), FRONT - 0.5, round(P.zc() + 1.2, 3)]})
        objs.append({"모양": "거품", "반지름": R, "갇힘": True, "갇힘초": round(t_c, 2), "등속": True, "동작": rise})
        text("뽀글!", t_c, t_c + 1.0, xc, z0 + 3.0, "#9fe8ff", 1.0, -2.5)
        P.seg_to(x1, fz(k + 1, x1), 0.35, "점프")
        P.k = k + 1
        P.pose("서기")
        add_score(P.t, 500, x1, fz(k + 1, x1))
        text("지름길!", P.t, P.t + 1.0, x1, fz(k + 1, x1) + 3.6, "#9fe8ff", 0.9, -2)

    plat = cfg.get("징검다리")
    plat_keys = None

    def ride_platform():
        """끊긴 바닥 앞에서 징검다리를 기다렸다가 올라타고 건넘."""
        nonlocal plat_keys
        k = P.k
        a, b = HOLES[k]
        target = LADDERS[k]
        d = 1 if target > P.x else -1
        w = 1.6
        xa, xb = a + w / 2, b - w / 2
        v = plat["빠르기"]
        Tp = (xb - xa) / v
        ztop = round((fz(k, a) + fz(k, b)) / 2, 3)
        near_edge, far_edge = (b + 0.4, a - 0.4) if d < 0 else (a - 0.4, b + 0.4)
        near_c, far_c = (xb, xa) if d < 0 else (xa, xb)
        P.move(near_edge)
        # 발판이 가까운 끝(near_c)에 오는 때: 왼끝은 2nTp, 오른끝은 (2n+1)Tp
        off = Tp if near_c == xb else 0.0
        nn = 0
        while off + 2 * nn * Tp < P.t + 0.6:
            nn += 1
        t_on = off + 2 * nn * Tp
        P.wait(t_on - 0.45 - P.t)
        P.jumps.append((t_on - 0.2, 0.45, 1.0))
        P.seg_to(near_c, ztop, 0.45, "점프")
        P.riding = True
        P.seg_to(far_c, ztop, Tp, "서기")
        P.riding = False
        P.jumps.append((P.t + 0.2, 0.45, 1.0))
        P.seg_to(far_edge, fz(k, far_edge), 0.45, "점프")
        P.pose("서기")
        plat_keys = (xa, xb, Tp, ztop)

    P = Route(-9.0, 0, 60)
    text(f"{cfg['판']}판", 0.2, 2.2, 0, 8.6, "#ffffff", 2.0)
    text(cfg["제목"], 0.2, 2.2, 0, 6.6, "#ffe14d", 1.4)
    text("도와주세요!", 0.5, 2.8, 7.5, 16.0, "#ff9ad5", 1.0, -2)
    P.wait(1.8)

    # ── 땅 → 사다리
    P.move(LADDERS[0])
    P.climb()
    # ── 2층 · 3층 · 4층
    for k in (1, 2, 3):
        if P.k > k:  # 거품 지름길로 이미 올라옴
            continue
        tasks = cfg["층"].get(k, [])
        if isinstance(tasks, tuple):
            tasks = [tasks]
        for kind, n in tasks:
            if kind == "벌":
                bees(n)
            elif kind == "돌":
                rocks(n)
            elif kind == "거품":
                bubble_capture()
        if P.k > k:
            continue
        if plat and plat["층"] == k:
            ride_platform()
        P.move(LADDERS[k])
        P.climb()

    # ── 꼭대기 보스
    z = BASE[4]
    alien_x = 1.5
    t_top = P.t
    P.turn(60)
    P.wait(0.3)
    t_laser = P.t
    alien_acts = None
    if cfg.get("보스", "우주인") == "여왕벌":
        T = P.t
        W = {"s1": (5.0, z + 2.4), "h1": (4.0, z + 2.9), "h2": (5.5, z + 2.0), "s2": (3.5, z + 2.6), "h3": (5.0, z + 3.1), "h4": (4.2, z + 2.2)}
        n_hit = cfg.get("보스_화살", 4)
        hit_t = [T + 1.6, T + 2.3, T + 4.6, T + 5.3][:n_hit]
        hit_w = [W["h1"], W["h2"], W["h3"], W["h4"]][:n_hit]
        qk = [{"초": 0, "위치": [6.0, 0, z + 2.8]}, {"초": round(T - 1.5, 2), "위치": [5.5, 0, z + 3.1]},
              {"초": round(T, 2), "위치": [W["s1"][0], 0, W["s1"][1]]}, {"초": round(T + 0.8, 2), "위치": [3.0, 0, z + 2.8]},
              {"초": round(T + 3.0, 2), "위치": [W["s2"][0], 0, W["s2"][1]]}, {"초": round(T + 3.8, 2), "위치": [6.0, 0, z + 2.5]}]
        qk += [{"초": round(t, 2), "위치": [w[0], 0, w[1]]} for t, w in zip(hit_t, hit_w)]
        qk.sort(key=lambda k: k["초"])
        t_fall = hit_t[-1]
        fx, fzz = hit_w[-1]
        qk = [k for k in qk if k["초"] <= t_fall]
        for k in range(1, 7):  # 빙글 돌며 아래로
            u = k / 6
            qk.append({"초": round(t_fall + 1.2 * u, 3), "위치": [round(fx + 0.6 * u, 3), 0, round(fzz - (fzz + 4) * u * u, 3)]})
        objs.append({"모양": "벌", "크기": 3.2, "색": "#ffa41f", "왕관": True, "눈색": "#ff2020", "맞은초": round(t_fall, 2), "동작": qk})
        for ts, w in ((T, W["s1"]), (T + 3.0, W["s2"])):  # 침 두 번 → 점프로 피함
            objs.append({"모양": "광선", "색": "#ffd21f", "동작": [{"초": round(ts, 2), "위치": [w[0] - 1.2, 0, w[1] - 0.3]},
                                                                {"초": round(ts + 1.0, 2), "위치": [-14.5, 0, z + 0.3]}]})
        P.wait(0.1)
        P.jump_here(2.2, 0.75)
        P.pose("위로쏘기")
        for t, w in zip(hit_t, hit_w):
            if t > T + 3.0 and P.t < T + 3.1:
                P.wait(T + 3.1 - P.t, "위로쏘기")
                P.jump_here(2.2, 0.75)
                P.pose("위로쏘기")
            arrow(P.x + 0.9, z + 2.0, w[0] - 0.8, w[1], t)
        P.wait(t_fall - P.t + 0.3, "위로쏘기")
        add_score(t_fall, 1000, fx, z)
        sfx.append({"초": round(t_fall + 0.1, 2), "소리": "휘익"})
    else:
        n_l, n_a = cfg.get("보스_광선", 1), cfg["보스_화살"]
        per = math.ceil(n_a / n_l)
        hits, lasers = [], []
        for li in range(n_l):  # 광선 → 점프로 피함 → 화살 몇 발, 되풀이
            tl = P.t if li == 0 else P.t + 0.2
            if li:
                P.wait(0.2, "서기")
            lasers.append(tl)
            objs.append({"모양": "광선", "색": "#7CFF4F", "동작": [{"초": round(tl, 2), "위치": [alien_x - 1.0, 0, z + 1.6]},
                                                                 {"초": round(tl + 0.9, 2), "위치": [-14.5, 0, z + 1.0]}]})
            P.jump_here(2.4, 0.75)
            P.pose("활쏘기")
            for k in range(min(per, n_a - len(hits))):
                th = P.t + 0.55 + k * 0.7
                arrow(P.x + 0.9, z + 1.45, alien_x - 0.6, z + 1.6, th)
                hits.append(th)
            P.wait(hits[-1] - P.t + 0.3, "활쏘기")
        t_fall = hits[-1]
        add_score(t_fall, 1000, alien_x, z)
        alien_acts = [{"초": 0, "자세": "서기", "위치": [alien_x, FRONT, z]}]
        for tl in lasers:
            alien_acts += [{"초": round(tl - 0.4, 2), "자세": "광선"}, {"초": round(tl + 0.5, 2), "자세": "서기"}]
        for th in hits[:-1]:
            alien_acts += [{"초": round(th, 2), "자세": "맞음"}, {"초": round(th + 0.35, 2), "자세": "서기"}]
        alien_acts += [{"초": round(t_fall, 2), "자세": "쓰러짐", "위치": [alien_x, FRONT, z]}]
        for k in range(1, 9):  # 튕겨 올랐다가 아래로 떨어져 사라짐
            u = k / 8
            alien_acts.append({"초": round(t_fall + 1.0 * u, 3),
                               "위치": [round(alien_x + 1.5 * u, 3), FRONT - 1.0, round(z + 4 * 1.2 * u * (1 - u) - (z + 4) * u * u, 3)]})
        sfx.append({"초": round(t_fall + 0.1, 2), "소리": "휘익"})

    cage_x = 7.5
    P.move(cage_x - 1.6)
    t_open = P.t + 0.2
    P.wait(0.6)
    objs.append({"모양": "감옥", "동작": [{"초": 0, "위치": [cage_x, FRONT, z]}, {"초": round(t_open, 2), "위치": [cage_x, FRONT, z]},
                                        {"초": round(t_open + 0.8, 2), "위치": [cage_x, FRONT, z + 3.5]}]})
    sfx.append({"초": round(t_open, 2), "소리": "점프"})
    t_meet = t_open + 0.9
    objs.append({"모양": "하트", "크기": 0.2, "동작": [{"초": round(t_meet, 2), "위치": [cage_x - 0.8, -2.2, z + 2.6]},
                                                    {"초": round(t_meet + 1.6, 2), "위치": [cage_x - 0.8, -2.2, z + 3.4]}]})
    princess_acts = [{"초": 0, "자세": "놀람", "위치": [cage_x, FRONT + 0.2, z], "방향": 0},
                     {"초": round(t_open, 2), "자세": "서기"},
                     {"초": round(t_open + 0.3, 2), "방향": -60}, {"초": round(t_meet, 2), "자세": "만세"}]
    add_score(t_meet, 5000, cage_x - 1.5, z)
    P.pose("만세", t_meet)
    t_clear = t_meet + 0.3
    text(f"{cfg['판']}판 클리어!", t_clear, t_clear + 3.2, 0, 7.2, "#ffe14d", 1.8)
    P.wait(3.3, "만세")
    total = round(t_clear + 3.2, 2)

    # ── 통나무(·불덩이): 하늘에서 계속 떨어짐 → 만나는 순간 자동 점프(+100)
    def meets(floor_keys, lift, jump):
        """floor_keys = 바닥 높이 기준 길. 전사와 만나는 순간 점프."""
        last, t = -9, floor_keys[0]["초"]
        while t < floor_keys[-1]["초"]:
            lp = interp(floor_keys, t)
            px, pz, pk = P.pos(t)
            if lp and not P.climbing(t) and abs(lp[2] - lift - pz) < 0.35 and abs(lp[0] - px) < 0.35 and t - last > 1.0:
                P.jumps.append((t, *jump))
                add_score(t + 0.3, 100, px, pz)
                last = t
            t += 0.01
    t_d, n_drop = 1.2, 0
    mix_n = cfg.get("불덩이_섞기", 0)
    while t_d < t_top - 2:
        n_drop += 1
        lk, thuds = log_path(t_d, LOG_DROP_X, cfg["통나무_빠르기"])
        if mix_n and n_drop % mix_n == 0:  # 불덩이: 통통 튀며 내려옴
            fk = []
            t = lk[0]["초"]
            while t <= lk[-1]["초"]:
                q = interp(lk, t)
                bounce = 0.5 * abs(math.sin((t - lk[0]["초"]) * math.pi / 0.42))
                fk.append({"초": round(t, 3), "위치": [round(q[0], 3), 0, round(q[2] - LOG_R + 0.45 + bounce, 3)]})
                t += 1 / 24
            objs.append({"모양": "불덩이", "반지름": 0.45, "등속": True, "동작": fk})
        else:
            objs.append({"모양": "통나무", "반지름": LOG_R, "쿵": thuds, "동작": lk})
        meets(lk, LOG_R, JUMP)
        t_d += cfg["통나무_간격"]
    # ── 운석: 전사가 있는 층의 바로 앞·뒤에 불꼬리 운석이 떨어져 폭발
    if cfg.get("운석"):
        rg = random.Random(cfg["판"])
        t = 2.4
        while t < t_top - 0.5:
            px, pz, pk = P.pos(t)
            if P.climbing(t) or pk >= 4:
                t += 0.4
                continue
            xl = None
            for _ in range(12):
                c = px + rg.choice([-1, 1]) * rg.uniform(1.5, 3.2)
                if -10.3 < c < 10.3 and not in_cut(pk, c, 0.5):
                    xl = c
                    break
            if xl is None:
                t += 0.4
                continue
            zg = fz(pk, xl)
            dx = rg.choice([-1, 1])
            objs.append({"모양": "글자", "내용": "!", "글자크기": 0.9, "색": "#ff3030", "동작": [
                {"초": round(t - 0.9, 2), "위치": [round(xl, 2), -1.6, round(zg + 0.3, 2)]},
                {"초": round(t - 0.05, 2), "위치": [round(xl, 2), -1.6, round(zg + 0.3, 2)]}]})
            objs.append({"모양": "운석", "쿵": [round(t, 2)], "등속": True, "동작": [
                {"초": round(t - 0.9, 3), "위치": [round(xl - dx * 6, 2), FRONT - 0.3, SKY + 1]},
                {"초": round(t, 3), "위치": [round(xl, 2), FRONT - 0.3, round(zg + 0.45, 2)]}]})
            for k in range(6):
                ddx = (0.5 + 0.4 * k) * (1 if k % 2 else -1)
                pk_ = [{"초": round(t + 0.5 * j / 6, 3), "위치": [round(xl + ddx * j / 6, 3), FRONT - 0.3,
                                                              round(zg + 0.25 + 4 * 1.0 * (j / 6) * (1 - j / 6) - 0.13 * j / 6, 3)]}
                       for j in range(7)]
                pk_.append({"초": round(t + 0.8, 3), "위치": pk_[-1]["위치"]})
                objs.append({"모양": "조각", "반지름": 0.13, "색": "#ff7a1f" if k % 2 else "#6b4a3a", "등속": True, "동작": pk_})
            t += cfg["운석"]["간격"] * rg.uniform(0.8, 1.25)
    # ── 딱정벌레 순찰: 층 위를 왔다 갔다(만나면 점프)
    for pt in cfg.get("순찰", []):
        k, xa, xb, v = pt[:4]
        t_cap = pt[4] if len(pt) > 4 else None
        bk, t, x, d = [], 0.0, (xa + xb) / 2, 1
        while t < total + 0.5:
            bk.append({"초": round(t, 3), "위치": [round(x, 3), FRONT + 0.6, round(fz(k, x), 3)]})
            nx = xb if d > 0 else xa
            t += abs(nx - x) / v
            x, d = nx, -d
        bk.append({"초": round(t, 3), "위치": [round(x, 3), FRONT + 0.6, round(fz(k, x), 3)]})
        if t_cap:  # 거품에 갇혀 하늘로 날아감
            q = interp(bk, t_cap)
            bk = [b for b in bk if b["초"] < t_cap] + [{"초": t_cap, "위치": [round(q[0], 3), q[1], round(q[2], 3)]}]
            up = [{"초": round(t_cap + 3.0 * j / 6, 3), "위치": [round(q[0] + 0.3 * math.sin(j), 3), q[1], round(q[2] + (SKY + 2 - q[2]) * j / 6, 3)]}
                  for j in range(1, 7)]
            bub = [{"초": round(t_cap - 1.2, 3), "위치": [round(q[0], 3), FRONT - 0.3, round(q[2] + 0.5 - 2.6, 3)]},
                   {"초": t_cap, "위치": [round(q[0], 3), FRONT - 0.3, round(q[2] + 0.5, 3)]}]
            bub += [{"초": u["초"], "위치": [u["위치"][0], FRONT - 0.3, round(u["위치"][2] + 0.5, 3)]} for u in up]
            objs.append({"모양": "거품", "반지름": 0.9, "갇힘": True, "갇힘초": t_cap, "등속": True, "동작": bub})
            objs.append({"모양": "딱정벌레", "크기": 2.0, "등속": True, "동작": bk + up})
        else:
            objs.append({"모양": "딱정벌레", "크기": 2.0, "등속": True, "동작": bk})
        meets([dict(b, 위치=[b["위치"][0], 0, b["위치"][2]]) for b in bk], 0.0, (0.6, 1.4))

    # ── 계속 올라오는 거품(전사는 피함)
    if cfg.get("거품"):
        rg = random.Random(cfg["판"] * 7)
        t = 0.3
        while t < total - 1:
            r_ = rg.uniform(0.45, 0.85)
            vz = rg.uniform(1.8, 2.6)
            for _ in range(15):
                bx = rg.uniform(-10.5, 10.5)
                ok = True
                tt = t
                while tt < t + (SKY + 2) / vz:
                    bz = -1 + vz * (tt - t)
                    px, pz, pk = P.pos(tt)
                    if abs(bx - px) < 1.4 and pz - 1.0 < bz < pz + 3.2:
                        ok = False
                        break
                    tt += 0.1
                if ok:
                    break
            if ok:
                ks = [{"초": round(t + j * 0.5, 3), "위치": [round(bx + 0.3 * math.sin(j * 1.3), 3), FRONT - 0.6, round(-1 + vz * j * 0.5, 3)]}
                      for j in range(int((SKY + 2) / vz / 0.5) + 2)]
                objs.append({"모양": "거품", "반지름": round(r_, 2), "동작": ks})
            t += cfg["거품"]["간격"] * rg.uniform(0.7, 1.3)
    # ── 징검다리 발판(왔다 갔다)
    if plat_keys:
        xa, xb, Tp, ztop = plat_keys
        pk_, t, x = [], 0.0, xa
        while t < total + Tp:
            pk_.append({"초": round(t, 3), "위치": [round(x, 3), 0, ztop]})
            x = xb if x == xa else xa
            t += Tp
        objs.append({"모양": "징검돌", "너비": 1.6, "등속": True, "동작": pk_})
    # ── 점수판(앞 판 점수에 이어서)
    acc = start_score
    scores = [[0, f"점수 {acc}"]]
    for t_, p_ in sorted(score_ev):
        acc += p_
        scores.append([t_, f"점수 {acc}"])
    objs.append({"모양": "글자", "내용": scores[0][1], "글자크기": 0.8, "색": "#ffffff", "바뀜": scores,
                 "동작": [{"초": 0, "위치": [12.5, -3, 16.3]}, {"초": total, "위치": [12.5, -3, 16.3]}]})

    acts = P.keys(total)
    stage = {"바닥": [-14, 14], "발판": [], "사다리": []}
    stage.update(cfg.get("무대", {}))
    for k in (1, 2, 3, 4):
        x = -EDGE if k < 4 else TOP_X0
        for a, b in cuts(k):
            if b <= x:
                continue
            stage["발판"].append([x, a, round(fz(k, x), 3), round(fz(k, a), 3)])
            x = b
        stage["발판"].append([x, EDGE, round(fz(k, x), 3), round(fz(k, EDGE), 3)])
    for i, lx in enumerate(LADDERS):
        stage["사다리"].append([lx, round(fz(i, lx), 3), round(fz(i + 1, lx), 3)])
    scene = {
        "캐릭터": "캐릭터.json", "초": total, "fps": 24, "크기": [1920, 1080], "픽셀": 4, "꼬마": 1.5,
        "배경": "레트로", "무대": stage,
        "인물": [{"이름": "전사", "위치": [-9.0, FRONT, 0], "방향": 60, "동작": acts},
                 {"이름": "공주", "위치": [cage_x, FRONT + 0.2, z], "방향": 0, "동작": princess_acts}]
                + ([{"이름": "괴물우주인", "위치": [alien_x, FRONT, z], "방향": -60, "바꿈": {"키": 1.0}, "동작": alien_acts}]
                   if alien_acts else []),
        "물체": objs,
        "효과음": sfx + [{"초": round(t_clear, 2), "소리": "승리"}],
        "배경음": {"곡": "레트로전투", "크기": 0.35, "끝": round(t_clear - 0.1, 2)},
        "카메라": CAM,
    }
    if cfg.get("하늘색"):
        scene["하늘색"] = cfg["하늘색"]
    if cfg.get("거울"):
        mirror(scene)
    return scene, acc


def mirror(scene):
    """좌우 뒤집기: x → -x, 바라보는 방향 반대(뒤·앞은 그대로). 글자 위치도 뒤집되 글자 자체는 그대로."""
    def flip_keys(keys):
        for k in keys:
            if "위치" in k:
                k["위치"][0] = -k["위치"][0]
            if "보는곳" in k:
                k["보는곳"][0] = -k["보는곳"][0]
            if "방향" in k and abs(k["방향"]) not in (0, 180):
                k["방향"] = -k["방향"]
    for a in scene["인물"]:
        a["위치"][0] = -a["위치"][0]
        if abs(a.get("방향", 0)) not in (0, 180):
            a["방향"] = -a["방향"]
        flip_keys(a["동작"])
    for o in scene["물체"]:
        flip_keys(o["동작"])
    st = scene["무대"]
    st["발판"] = [[-f[1], -f[0], f[3], f[2]] for f in st["발판"]]
    st["사다리"] = [[-l[0], l[1], l[2]] for l in st["사다리"]]
    for o in scene["물체"]:  # 점수판은 오른쪽 위 그대로
        if o.get("바뀜"):
            flip_keys(o["동작"])


def main(prefix):
    score = 0
    for cfg in STAGES:
        scene, score = build(cfg, score)
        out = f"{prefix}_{cfg['판']}판.json"
        json.dump(scene, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("저장:", out, "| 길이", scene["초"], "초 | 누적 점수", score)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "블록애니/장면_공주구출")
