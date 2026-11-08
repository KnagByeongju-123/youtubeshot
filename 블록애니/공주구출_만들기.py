# -*- coding: utf-8 -*-
"""공주 구출 — 땅에서 출발해 기울어진 층과 사다리를 올라 꼭대기 감옥의 공주를 구함.

- 2·3·4층 바닥은 층마다 반대로 기울어짐. 전사는 늘 오르막으로 올라가고, 통나무는 내리막으로 굴러옴.
- 통나무는 왼쪽 위 하늘에서 4층으로 떨어져 기울기를 따라 구르다가, 끊어진 바닥·사다리 구멍을 만나면
  아래층으로 떨어지고 그 층의 기울기를 따라 반대로 구름(4층 → 3층 → 2층 → 땅 → 화면 밖).
- 전사와 통나무가 만나는 순간을 모두 찾아 자동으로 점프. 끊어진 바닥도 점프로 건넘.
- 2층: 벌 2마리(한 번 쏘여 목숨 -1), 3층: 하늘에서 돌이 떨어짐(아슬아슬), 꼭대기: 괴물 우주인(광선·화살 3발)
- 긴장 장치: 맨 앞 미리보기, 남은 시간(5초부터 빨강+삐), 목숨 하트, 아슬아슬할 때 잠깐 확대,
  층마다 빨라지는 음악, 보스 앞 심장 소리.

  python 블록애니/공주구출_만들기.py 블록애니/장면_공주구출.json
  xvfb-run -a .blender_venv/bin/python 블록애니.py 장면 블록애니/장면_공주구출.json 결과.mp4
"""
import json
import math
import sys

BASE = [0.0, 3.2, 6.4, 9.6, 12.8]  # 층 높이(가운데 기준): 땅, 2층, 3층, 4층, 꼭대기
DOWN = [-1, 1, -1, 1, 0]  # 내리막 방향(+1 = 오른쪽이 낮음). 땅은 평평하지만 통나무는 왼쪽으로 굴러감
SLOPE = 0.9 / 22  # 기울기(22m 에 0.9m)
LADDERS = [8.0, -8.0, 8.0, -3.0]  # i 번째 사다리: i층 → i+1층
EDGE = 11.0
TOP_X0 = LADDERS[3] + 0.6  # 꼭대기 층은 사다리 오른쪽부터(왼쪽 위는 하늘 — 통나무가 떨어지는 곳)
HOLES = {1: (-3.4, -1.8), 2: (5.6, 7.2), 3: (2.8, 4.4)}  # 끊어진 바닥
GAP = 0.6  # 사다리가 올라오는 곳의 구멍(반 너비)
RUN, CLIMB = 5.0, 3.2  # m/초
JUMP = (0.65, 1.8)  # 통나무 넘기(길이 초, 높이 m)
HOLE_JUMP = (0.6, 1.4)
LOG_R, LOG_V = 0.6, 5.0
LOG_DROP_X, SKY = -9.0, 18.0
LOG_EVERY = 2.6
FRONT = -1.0  # 인물·감옥·돌은 벽돌 바닥보다 앞줄 → 겹쳐도 가려지지 않음
BASE_CAM = {"위치": [0, -40, 8.3], "보는곳": [0, 0, 8.3], "직교": 32}


def fz(k, x):
    """k 층 바닥의 x 에서 높이."""
    if k in (1, 2, 3):
        return BASE[k] - DOWN[k] * SLOPE * x
    return BASE[k]


def cuts(k):
    """k 층의 구멍들(사다리 구멍 + 끊어진 바닥)."""
    c = []
    if k >= 1:
        c.append((LADDERS[k - 1] - GAP, LADDERS[k - 1] + GAP))
    if k in HOLES:
        c.append(HOLES[k])
    return sorted(c)


class Route:
    """전사의 길. 모든 구간이 직선(시간에 따라 x·z 가 고르게 변함) → 나중에 점프를 얹음."""

    def __init__(self, x, k, face):
        self.t, self.x, self.k, self.face = 0.0, x, k, face
        self.seg = []  # (t0, t1, x0, x1, z0, z1, 층)
        self.poses = [(0.0, "서기")]
        self.faces = [(0.0, face)]
        self.climbs = []
        self.jumps = []  # (가운데 초, 길이, 높이)

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
        z = fz(self.k, self.x)
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

    def knock(self, dx, dur=0.45):
        self.pose("맞음")
        self._seg(dur, self.x + dx, fz(self.k, self.x), fz(self.k, self.x + dx))
        self.pose("서기")

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
        merged = []  # 겹치는 점프는 하나로 합침
        for a, b, h in js:
            if merged and a <= merged[-1][1]:
                merged[-1] = (merged[-1][0], max(b, merged[-1][1]), max(h, merged[-1][2]))
            else:
                merged.append((a, b, h))
        self.jump_windows = merged
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


def log_path(t0, x0):
    """하늘에서 떨어져 층마다 구르다 구멍으로 떨어지는 통나무의 키(같은 빠르기)."""
    keys, thuds = [], []
    k = 3
    zl = fz(k, x0) + LOG_R
    for i in range(7):  # 하늘에서 떨어짐(점점 빨라짐)
        u = i / 6
        keys.append({"초": round(t0 + 0.7 * u, 3), "위치": [x0, 0, round(SKY - (SKY - zl) * u * u, 3)]})
    t, x = t0 + 0.7, x0
    thuds.append(round(t, 2))
    while True:
        d = DOWN[k]
        if k == 0:
            t += abs(-15 - x) / LOG_V
            keys.append({"초": round(t, 3), "위치": [-15.0, 0, LOG_R]})
            break
        ahead = [(a + b) / 2 for a, b in cuts(k) if ((a + b) / 2 - x) * d > 0]
        nx = min(ahead, key=lambda c: abs(c - x)) if ahead else d * (EDGE + 0.3)
        t += abs(nx - x) / LOG_V
        keys.append({"초": round(t, 3), "위치": [round(nx, 3), 0, round(fz(k, nx) + LOG_R, 3)]})
        lx = nx + 0.4 * d
        land = fz(k - 1, lx) + LOG_R
        top = fz(k, nx) + LOG_R
        for i in range(1, 7):  # 구멍으로 떨어짐
            u = i / 6
            keys.append({"초": round(t + 0.5 * u, 3), "위치": [round(nx + 0.4 * d * u, 3), 0, round(top - (top - land) * u * u, 3)]})
        t += 0.5
        x = lx
        k -= 1
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


def main(out):
    objs, sfx, scores, cams, tempo, flashes = [], [], [[0, "점수 0"]], [dict(BASE_CAM, 초=0)], [(0, 140)], []
    score = 0

    def text(txt, t0, t1, x, z, color="#ffffff", size=1.2, y=-3):
        objs.append({"모양": "글자", "내용": txt, "글자크기": size, "색": color,
                     "동작": [{"초": round(t0, 2), "위치": [x, y, z]}, {"초": round(t1, 2), "위치": [x, y, z + 0.15]}]})

    score_ev = []

    def add_score(t, pts, x, z):
        nonlocal score
        score += pts
        score_ev.append((round(t, 2), pts))
        text(f"+{pts}", t, t + 0.9, x, z + 2.8, "#ffe14d", 0.9, -2)
        sfx.append({"초": round(t + 0.03, 2), "소리": "동전"})

    def arrow(x0, z0, x1, z1, t_hit, speed=16.0):
        d = math.hypot(x1 - x0, z1 - z0)
        t_fire = t_hit - d / speed * 1.4
        objs.append({"모양": "화살", "동작": [{"초": round(t_fire, 2), "위치": [x0, 0, z0]}, {"초": round(t_hit, 2), "위치": [x1, 0, z1]}]})

    def zoom(tc, x, zc, before=0.5, after=0.6):
        """아슬아슬한 순간 잠깐 확대."""
        z_ = {"위치": [x, -40, zc], "보는곳": [x, 0, zc], "직교": 14}
        cams.extend([dict(BASE_CAM, 초=round(tc - before, 3)), dict(z_, 초=round(tc - before + 0.25, 3)),
                     dict(z_, 초=round(tc + after - 0.25, 3)), dict(BASE_CAM, 초=round(tc + after, 3))])

    P = Route(-9.0, 0, 60)
    text("공주를 구하라!", 0.2, 2.2, 0, 7.2, "#ffe14d", 1.6)
    text("도와주세요!", 0.5, 2.8, 7.5, 16.0, "#ff9ad5", 1.0, -2)
    P.wait(0.9)
    P.pose("놀람", 0.9)
    P.wait(0.9)

    # ── 1층(땅): 사다리까지 달림(통나무는 자동으로 점프)
    P.move(LADDERS[0])
    P.climb()

    # ── 2층: 벌 2마리 — 둘째 벌에 화살이 빗나가 한 번 쏘임(목숨 -1) → 다시 쏴서 맞힘
    tempo.append((P.t, 155))
    P.turn(-60)
    P.wait(0.2)
    P.pose("활쏘기")
    zf = fz(1, P.x)
    bx, bz = P.x - 0.9, zf + 1.45
    th1 = P.t + 1.4
    objs.append({"모양": "벌", "크기": 1.6, "맞은초": round(th1, 2), "동작": [
        {"초": round(P.t - 0.2, 2), "위치": [-EDGE - 1, 0, fz(1, 0) + 1.8]}, {"초": round(th1, 2), "위치": [3.0, 0, fz(1, 3) + 1.6]},
        {"초": round(th1 + 0.6, 2), "위치": [2.6, 0, fz(1, 2.6) + 0.15]}]})
    arrow(bx, bz, 3.4, fz(1, 3) + 1.6, th1)
    add_score(th1, 200, 3.0, fz(1, 3))
    t_m = th1 + 0.9
    t_sting = t_m + 0.45
    t_hit2 = t_sting + 1.2
    objs.append({"모양": "벌", "크기": 1.6, "맞은초": round(t_hit2, 2), "동작": [
        {"초": round(th1 - 0.6, 2), "위치": [-EDGE - 1, 0, zf + 2.6]}, {"초": round(t_m - 0.25, 2), "위치": [0.6, 0, zf + 2.6]},
        {"초": round(t_m, 2), "위치": [2.4, 0, zf + 1.5]}, {"초": round(t_sting, 2), "위치": [P.x - 1.0, 0, zf + 1.5]},
        {"초": round(t_sting + 0.5, 2), "위치": [5.0, 0, zf + 2.2]}, {"초": round(t_hit2, 2), "위치": [4.0, 0, zf + 1.8]},
        {"초": round(t_hit2 + 0.6, 2), "위치": [3.6, 0, fz(1, 3.6) + 0.15]}]})
    t_fire_miss = t_m - (bx - 2.4) / 16.0
    objs.append({"모양": "화살", "등속": True, "동작": [{"초": round(t_fire_miss, 2), "위치": [bx, 0, bz + 0.2]},
                                                     {"초": round(t_fire_miss + (bx + 12) / 16.0, 2), "위치": [-12, 0, bz + 1.3]}]})
    P.wait(t_sting - P.t, "활쏘기")
    flashes.append([round(t_sting, 2), 0.25, "#8a0000"])
    sfx.append({"초": round(t_sting, 2), "소리": "아야"})
    text("아야!", t_sting, t_sting + 0.9, P.x + 0.3, zf + 2.9, "#ff5050", 1.0, -2)
    P.knock(0.6)
    P.pose("활쏘기")
    arrow(P.x - 0.9, bz, 4.4, zf + 1.8, t_hit2)
    add_score(t_hit2, 200, 4.0, zf)
    P.wait(t_hit2 - P.t + 0.4, "활쏘기")
    P.move(LADDERS[1])
    P.climb()

    # ── 3층: 하늘에서 돌이 떨어짐(앞줄로 떨어져 위층을 지나는 게 보임) — 첫 돌은 코앞
    tempo.append((P.t, 165))
    rocks = []
    P.move(-3.0)
    t_rock1 = P.t + 0.6
    rocks.append((t_rock1, -1.8))
    zoom(t_rock1, -2.4, fz(2, -2.4) + 1.4, 0.5, 0.5)
    text("아슬아슬!", t_rock1 + 0.05, t_rock1 + 1.0, -2.4, fz(2, -2.4) + 3.0, "#ff9a3c", 1.0, -2)
    P.wait(0.35)
    P.pose("놀람")
    P.wait(0.8, "놀람")
    P.move(2.0)
    t_rock2 = P.t + 0.7
    rocks.append((t_rock2, 4.0))
    P.wait(1.0)
    P.move(LADDERS[2])
    for th, x in rocks:
        zg = fz(2, x)
        dur = 1.0
        objs.append({"모양": "글자", "내용": "!", "글자크기": 0.9, "색": "#ff3030", "동작": [
            {"초": round(th - dur - 0.4, 2), "위치": [x, -1.6, zg + 0.3]}, {"초": round(th - 0.05, 2), "위치": [x, -1.6, zg + 0.3]}]})
        ks = []
        for k in range(11):
            u = k / 10
            ks.append({"초": round(th - dur + dur * u, 3), "위치": [x, FRONT - 0.3, round(SKY - (SKY - (zg + 0.5)) * u * u, 3)]})
        objs.append({"모양": "돌", "반지름": 0.5, "쿵": [round(th, 2)], "등속": True, "동작": ks})
        for k in range(5):
            dx = (0.5 + 0.35 * k) * (1 if k % 2 else -1)
            pk = []
            for j in range(7):
                u = j / 6
                pk.append({"초": round(th + 0.45 * u, 3), "위치": [round(x + dx * u, 3), FRONT - 0.3,
                                                                  round(zg + 0.25 + 4 * 0.8 * u * (1 - u) - 0.13 * u, 3)]})
            pk.append({"초": round(th + 0.9, 3), "위치": pk[-1]["위치"]})
            objs.append({"모양": "조각", "반지름": 0.12, "등속": True, "동작": pk})
        add_score(th, 100, x, zg)
    P.climb()

    # ── 4층: 오르막으로 사다리까지(통나무는 자동 점프, 끊어진 바닥도 점프)
    tempo.append((P.t, 175))
    P.move(LADDERS[3])
    P.climb()

    # ── 꼭대기: 괴물 우주인
    tempo.append((P.t, 185))
    z = BASE[4]
    alien_x = 1.5
    t_top = P.t
    P.turn(60)
    P.wait(0.3)
    t_laser = P.t
    objs.append({"모양": "광선", "색": "#7CFF4F", "동작": [{"초": round(t_laser, 2), "위치": [alien_x - 1.0, 0, z + 1.6]},
                                                         {"초": round(t_laser + 0.9, 2), "위치": [-14.5, 0, z + 1.0]}]})
    zoom(t_laser + 0.4, P.x + 1.8, z + 1.8, 0.6, 0.5)
    P.jump_here(2.4, 0.75)
    P.pose("활쏘기")
    hits = []
    for k in range(3):
        th = P.t + 0.55 + k * 0.7
        arrow(P.x + 0.9, z + 1.45, alien_x - 0.6, z + 1.6, th)
        hits.append(th)
    P.wait(hits[-1] - P.t + 0.3, "활쏘기")
    t_fall = hits[-1]
    tt = t_top
    while tt < t_fall:  # 보스와 싸우는 동안 심장 소리
        sfx.append({"초": round(tt, 2), "소리": "심장"})
        tt += 0.75
    add_score(t_fall, 1000, alien_x, z)
    alien_acts = [{"초": 0, "자세": "서기", "위치": [alien_x, FRONT, z]}, {"초": round(t_laser - 0.4, 2), "자세": "광선"},
                  {"초": round(t_laser + 0.5, 2), "자세": "서기"}]
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
    text("구출 성공!", t_clear, t_clear + 3.5, 0, 7.2, "#ffe14d", 1.8)
    P.wait(3.6, "만세")
    total = round(t_clear + 3.5, 2)

    # ── 통나무: 하늘에서 계속 떨어짐 → 전사와 만나는 순간 자동 점프(+100)
    t_d = 1.2
    n_jump = 0
    while t_d < t_top - 2:
        lk, thuds = log_path(t_d, LOG_DROP_X)
        objs.append({"모양": "통나무", "반지름": LOG_R, "쿵": thuds, "동작": lk})
        last = -9
        t = lk[0]["초"]
        while t < lk[-1]["초"]:
            lp = interp(lk, t)
            px, pz, pk = P.pos(t)
            if lp and not P.climbing(t) and abs(lp[2] - LOG_R - pz) < 0.35 and abs(lp[0] - px) < 0.3 and t - last > 1.0:
                P.jumps.append((t, *JUMP))
                add_score(t + 0.3, 100, px, pz)
                last = t
                n_jump += 1
            t += 0.01
        t_d += LOG_EVERY

    acc = 0  # 점수판: 시간 순서대로 더함(통나무 점수는 나중에 계산되므로)
    for t_, p_ in sorted(score_ev):
        acc += p_
        scores.append([t_, f"점수 {acc}"])
    # ── 화면 위 정보(화면 고정): 점수, 남은 시간(5초부터 빨강+삐), 목숨 하트
    objs.append({"모양": "글자", "내용": "점수 0", "글자크기": 0.8, "색": "#ffffff", "바뀜": scores, "화면고정": True,
                 "동작": [{"초": 0, "위치": [12.5, -3, 16.3]}, {"초": total, "위치": [12.5, -3, 16.3]}]})
    TL = math.ceil(t_meet) + 2
    white, red = [], []
    k = 0
    while k <= t_meet:
        left = TL - k
        (red if left <= 5 else white).append([k, f"시간 {left}"])
        if left <= 5:
            sfx.append({"초": k, "소리": "삐"})
        k += 1
    t_red = red[0][0]
    objs.append({"모양": "글자", "내용": white[0][1], "글자크기": 0.9, "색": "#ffffff", "바뀜": white, "화면고정": True,
                 "동작": [{"초": 0, "위치": [0, -3, 16.3]}, {"초": t_red - 0.01, "위치": [0, -3, 16.3]}]})
    objs.append({"모양": "글자", "내용": red[0][1], "글자크기": 1.0, "색": "#ff3030", "바뀜": red, "화면고정": True,
                 "동작": [{"초": t_red, "위치": [0, -3, 16.25]}, {"초": total, "위치": [0, -3, 16.25]}]})
    for k, hx in enumerate((-15.0, -13.9, -12.8)):
        wins = [(0, total)] if k < 2 else [(0, t_sting), (t_sting + 0.15, t_sting + 0.3), (t_sting + 0.45, t_sting + 0.6)]
        for a_, b_ in wins:
            objs.append({"모양": "하트", "크기": 0.13, "화면고정": True, "동작": [{"초": round(a_, 2), "위치": [hx, -3, 15.75]},
                                                                             {"초": round(b_, 2), "위치": [hx, -3, 15.75]}]})

    acts = P.keys(total)
    # 무대: 기울어진 바닥(구멍 사이사이), 사다리
    stage = {"바닥": [-14, 14], "발판": [], "사다리": []}
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
    cams.sort(key=lambda c: c["초"])
    scene = {
        "캐릭터": "캐릭터.json", "초": total, "fps": 24, "크기": [1920, 1080], "픽셀": 4, "꼬마": 1.5,
        "배경": "레트로", "무대": stage,
        "인물": [{"이름": "전사", "위치": [-9.0, FRONT, 0], "방향": 60, "동작": acts},
                 {"이름": "괴물우주인", "위치": [alien_x, FRONT, z], "방향": -60, "바꿈": {"키": 1.0}, "동작": alien_acts},
                 {"이름": "공주", "위치": [cage_x, FRONT + 0.2, z], "방향": 0, "동작": princess_acts}],
        "물체": objs,
        "효과음": sfx + [{"초": round(t_clear, 2), "소리": "승리"}],
        "배경음": {"곡": "레트로전투", "크기": 0.35, "끝": round(t_clear - 0.1, 2), "빠르기": tempo},
        "카메라": cams, "번쩍": flashes,
        "미리보기": {"초": [round(t_laser - 0.4, 2), round(t_laser + 1.0, 2)], "글자": "과연 공주를 구할 수 있을까?"},
    }
    json.dump(scene, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("저장:", out, "| 장면 길이", total, "초 | 점수", score, "| 통나무 점프", n_jump, "번 | 점프 구간",
          [(round(a, 1), round(b, 1)) for a, b, h in P.jump_windows])


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "블록애니/장면_공주구출.json")
