# -*- coding: utf-8 -*-
"""공주 구출 — 땅에서 출발해 사다리로 4층을 올라 꼭대기 감옥의 공주를 구함.
층마다 장애물: 1층 통나무(점프) → 2층 벌(한 번 쏘임, 목숨 -1)·끊어진 바닥 → 3층 천장 돌(아슬아슬)·끊어진 바닥
→ 4층 끊어진 바닥·뒤에서 오는 통나무 → 꼭대기 괴물 우주인(광선 점프로 피하고 화살 3발) → 감옥이 열리고 하트 → 구출 성공!
긴장 장치: 맨 앞 미리보기, 남은 시간(5초부터 빨강+삐), 목숨 하트, 아슬아슬한 순간 슬로모션+확대,
층마다 빨라지는 음악, 보스 앞 심장 소리.

전사의 길(달리기·점프·오르기)을 순서대로 적으면 위치·자세·방향 키를 자동으로 만들고,
통나무·벌·돌이 전사와 만나는 시각을 계산해 점프·화살을 맞춤.

  python 블록애니/공주구출_만들기.py 블록애니/장면_공주구출.json
  xvfb-run -a .blender_venv/bin/python 블록애니.py 장면 블록애니/장면_공주구출.json 결과.mp4
"""
import json
import math
import sys

FLOORS = [0.0, 3.2, 6.4, 9.6, 12.8]  # 땅, 2층, 3층, 4층, 꼭대기
JUMP_H = 1.8
LOG_R = 0.6
FRONT = -1.0  # 인물·감옥은 벽돌 바닥(앞뒤 ±0.5m)보다 앞에 섬 → 점프해서 위층 바닥과 겹쳐도 몸이 보임
LADDERS = [8.0, -8.0, 8.0, -8.0]  # i 번째 사다리: FLOORS[i] → FLOORS[i+1]
EDGE = 11.0
RUN, WALK, CLIMB = 5.0, 3.0, 3.2  # m/초
GAP = 0.6  # 사다리가 올라오는 곳의 바닥 구멍(반 너비)
HOLES = {1: (-3.4, -1.8), 2: (5.6, 7.2), 3: (2.8, 4.4)}  # 층 번호 → 끊어진 바닥(점프로 건넘)
HOLE_JUMP = (0.6, 1.4)  # 구멍 점프 길이(초)·높이(m)
BASE_CAM = {"위치": [0, -40, 8.3], "보는곳": [0, 0, 8.3], "직교": 32}


class Path:
    """전사의 움직임을 차례로 쌓음. 위치는 촘촘한 키로, 자세·방향은 바뀌는 때에만."""

    def __init__(self, x, z, face):
        self.t, self.x, self.z, self.face = 0.0, x, z, face
        self.keys = [{"초": 0, "위치": [x, 0, z], "방향": face, "자세": "서기"}]
        self.jumps = []  # (가운데 초, 길이, 높이) — 이동 중 점프

    def _pos(self, t0, x0, x1, z0, dur, t):
        u = (t - t0) / dur
        x = x0 + (x1 - x0) * u
        z = z0
        for tm, d, h in self.jumps:
            if tm - d / 2 <= t <= tm + d / 2:
                v = (t - (tm - d / 2)) / d
                z = z0 + 4 * h * v * (1 - v)
        return x, z

    def pose(self, p, t=None):
        self.keys.append({"초": round(self.t if t is None else t, 3), "자세": p})

    def turn(self, face):
        if face != self.face:
            self.keys.append({"초": round(self.t, 3), "방향": self.face})
            self.keys.append({"초": round(self.t + 0.15, 3), "방향": face})
            self.face = face

    def wait(self, dur, p="서기"):
        self.pose(p)
        self.keys.append({"초": round(self.t, 3), "위치": [self.x, 0, self.z]})
        self.t += dur
        self.keys.append({"초": round(self.t, 3), "위치": [self.x, 0, self.z]})

    def move(self, x1, speed=RUN, p="달리기", jump_at=()):
        """x1 까지 달림. jump_at = [(가운데 초, 길이, 높이)] 그 사이 점프."""
        self.turn(60 if x1 > self.x else -60)
        dur = abs(x1 - self.x) / speed
        t0, x0 = self.t, self.x
        self.jumps = list(jump_at)
        self.pose(p)
        n = max(2, int(dur * 12))
        for k in range(n + 1):
            t = t0 + dur * k / n
            x, z = self._pos(t0, x0, x1, self.z, dur, t)
            self.keys.append({"초": round(t, 3), "위치": [round(x, 3), 0, round(z, 3)]})
        for tm, d, h in jump_at:
            self.keys.append({"초": round(tm - d / 2, 3), "자세": "점프"})
            self.keys.append({"초": round(tm + d / 2, 3), "자세": p})
            for k in range(9):  # 점프 구간은 더 촘촘히
                t = tm - d / 2 + d * k / 8
                x, z = self._pos(t0, x0, x1, self.z, dur, t)
                self.keys.append({"초": round(t, 3), "위치": [round(x, 3), 0, round(z, 3)]})
        self.jumps = []
        self.t, self.x = t0 + dur, x1
        self.pose("서기")

    def x_at(self, t0, x0, x1, speed, t):
        return x0 + (x1 - x0) * (t - t0) / (abs(x1 - x0) / speed)

    def climb(self, z1):
        self.turn(180)  # 사다리에서는 등을 보임
        dur = (z1 - self.z) / CLIMB
        self.pose("오르기")
        self.keys.append({"초": round(self.t, 3), "위치": [self.x, 0, self.z]})
        self.t += dur
        self.keys.append({"초": round(self.t, 3), "위치": [self.x, 0, z1]})
        self.z = z1
        self.t += 0.05
        self.keys.append({"초": round(self.t, 3), "위치": [self.x, 0, z1]})
        self.pose("서기")

    def knock(self, dx, dur=0.5):
        """맞아서 뒤로 밀림."""
        self.pose("맞음")
        self.keys.append({"초": round(self.t, 3), "위치": [self.x, 0, self.z]})
        self.t += dur
        self.x += dx
        self.keys.append({"초": round(self.t, 3), "위치": [self.x, 0, self.z]})
        self.pose("서기")

    def jump_here(self, h=2.4, d=0.7):
        t0 = self.t
        self.pose("점프")
        for k in range(9):
            u = k / 8
            self.keys.append({"초": round(t0 + d * u, 3), "위치": [self.x, 0, round(self.z + 4 * h * u * (1 - u), 3)]})
        self.t += d
        self.pose("서기")


def meet(px0, pv, pt0, ox0, ov, ot0):
    """전사(px0 에서 pt0 에 출발, 빠르기 pv)와 물체가 만나는 시각."""
    # px0 + pv(t-pt0) = ox0 + ov(t-ot0)
    return (ox0 - ov * ot0 - px0 + pv * pt0) / (pv - ov)


def main(out):
    objs, sfx, scores = [], [], [[0, "점수 0"]]
    score = 0

    def text(txt, t0, t1, x, z, color="#ffffff", size=1.2, y=-3):
        objs.append({"모양": "글자", "내용": txt, "글자크기": size, "색": color,
                     "동작": [{"초": round(t0, 2), "위치": [x, y, z]}, {"초": round(t1, 2), "위치": [x, y, z + 0.15]}]})

    def add_score(t, pts, x, z):
        nonlocal score
        score += pts
        scores.append([round(t, 2), f"점수 {score}"])
        text(f"+{pts}", t, t + 0.9, x, z + 2.8, "#ffe14d", 0.9, -2)
        sfx.append({"초": round(t + 0.03, 2), "소리": "동전"})

    def arrow(x0, z0, x1, z1, t_hit, speed=16.0):
        d = math.hypot(x1 - x0, z1 - z0)
        t_fire = t_hit - d / speed * 1.4
        objs.append({"모양": "화살", "동작": [{"초": round(t_fire, 2), "위치": [x0, 0, z0]}, {"초": round(t_hit, 2), "위치": [x1, 0, z1]}]})
        return t_fire

    P = Path(-9.0, 0.0, 60)
    slow, flashes, cams, tempo = [], [], [dict(BASE_CAM, 초=0)], [(0, 140)]

    def zoom(tc, x, zc, before=0.5, after=0.6):
        """tc 무렵 전사 쪽으로 확대했다가 돌아옴."""
        z_ = {"위치": [x, -40, zc], "보는곳": [x, 0, zc], "직교": 13}
        cams.extend([dict(BASE_CAM, 초=round(tc - before, 3)), dict(z_, 초=round(tc - before + 0.25, 3)),
                     dict(z_, 초=round(tc + after - 0.25, 3)), dict(BASE_CAM, 초=round(tc + after, 3))])

    def hole_jump(floor, x_from):
        """x_from 에서 달리기 시작하면 구멍 가운데를 지나는 때 점프."""
        a_, b_ = HOLES[floor]
        hc = (a_ + b_) / 2
        return (P.t + abs(hc - x_from) / RUN, HOLE_JUMP[0], HOLE_JUMP[1])
    text("공주를 구하라!", 0.2, 2.2, 0, 7.2, "#ffe14d", 1.6)
    text("도와주세요!", 0.5, 2.8, 5.0, 16.0, "#ff9ad5", 1.0, -2)
    P.wait(0.9)
    P.pose("놀람", 0.9)
    P.wait(0.9)

    # ── 1층: 오른쪽에서 굴러오는 통나무를 달리며 점프
    z = FLOORS[0]
    t0, x0 = P.t, P.x
    log_t0, log_v, r = t0 + 0.4, 6.0, LOG_R
    tm = meet(x0, RUN, t0, EDGE + 0.5, -log_v, log_t0)
    P.move(LADDERS[0], RUN, jump_at=[(tm, 0.65, JUMP_H)])
    objs.append({"모양": "통나무", "반지름": r, "동작": [{"초": round(log_t0, 3), "위치": [EDGE + 0.5, 0, z + r]},
                                                    {"초": round(log_t0 + (2 * EDGE + 1) / log_v, 3), "위치": [-EDGE - 0.5, 0, z + r]}]})
    add_score(tm + 0.3, 100, P.x_at(t0, x0, LADDERS[0], RUN, tm), z)
    P.climb(FLOORS[1])

    # ── 2층: 벌 2마리. 둘째 벌에 첫 화살이 빗나가 한 번 쏘임(목숨 -1) → 다시 쏴서 맞힘 → 구멍 건너기
    z = FLOORS[1]
    tempo.append((P.t, 155))
    P.turn(-60)
    P.wait(0.2)
    P.pose("활쏘기")
    bx, bz = P.x - 0.9, z + 1.45
    ts1, th1 = P.t - 0.2, P.t + 1.4
    objs.append({"모양": "벌", "크기": 1.6, "맞은초": round(th1, 2), "동작": [
        {"초": round(ts1, 2), "위치": [-EDGE - 1, 0, z + 1.8]}, {"초": round(th1, 2), "위치": [3.0, 0, z + 1.6]},
        {"초": round(th1 + 0.6, 2), "위치": [2.6, 0, z + 0.15]}]})
    arrow(bx, bz, 3.4, z + 1.6, th1)
    add_score(th1, 200, 3.0, z)
    # 둘째 벌: 화살이 머리 위로 빗나감(벌이 아래로 쑥 내려감)
    t_m = th1 + 0.9
    t_sting = t_m + 0.45
    t_hit2 = t_sting + 1.2
    objs.append({"모양": "벌", "크기": 1.6, "맞은초": round(t_hit2, 2), "동작": [
        {"초": round(th1 - 0.6, 2), "위치": [-EDGE - 1, 0, z + 2.6]}, {"초": round(t_m - 0.25, 2), "위치": [0.6, 0, z + 2.6]},
        {"초": round(t_m, 2), "위치": [2.4, 0, z + 1.5]}, {"초": round(t_sting, 2), "위치": [P.x - 1.0, 0, z + 1.5]},
        {"초": round(t_sting + 0.5, 2), "위치": [5.0, 0, z + 2.2]}, {"초": round(t_hit2, 2), "위치": [4.0, 0, z + 1.8]},
        {"초": round(t_hit2 + 0.6, 2), "위치": [3.6, 0, z + 0.15]}]})
    t_fire_miss = t_m - (bx - 2.4) / 16.0
    objs.append({"모양": "화살", "등속": True, "동작": [{"초": round(t_fire_miss, 2), "위치": [bx, 0, bz + 0.2]},
                                                     {"초": round(t_fire_miss + (bx + 12) / 16.0, 2), "위치": [-12, 0, bz + 1.3]}]})
    P.wait(t_sting - P.t, "활쏘기")
    # 쏘임: 빨간 번쩍 + 아야 + 하트 하나 잃음 + 조금 느리게
    flashes.append([round(t_sting, 2), 0.25, "#8a0000"])
    sfx.append({"초": round(t_sting, 2), "소리": "아야"})
    text("아야!", t_sting, t_sting + 0.9, P.x + 0.3, z + 2.9, "#ff5050", 1.0, -2)
    slow.append([round(t_sting - 0.25, 2), round(t_sting + 0.35, 2), 0.4])
    P.knock(0.6, 0.45)
    P.pose("활쏘기")
    arrow(P.x - 0.9, bz, 4.4, z + 1.8, t_hit2)
    add_score(t_hit2, 200, 4.0, z)
    P.wait(t_hit2 - P.t + 0.4, "활쏘기")
    P.move(LADDERS[1], RUN, jump_at=[hole_jump(1, P.x)])
    P.climb(FLOORS[2])

    # ── 3층: 천장에서 돌 — 첫 돌은 코앞(아슬아슬, 느리게+확대) → 둘째 돌 → 구멍 건너기
    z = FLOORS[2]
    tempo.append((P.t, 165))
    ceil = FLOORS[3] - 0.6
    rocks = []
    P.move(-3.0, RUN)
    t_rock1 = P.t + 0.5
    rocks.append((t_rock1, -1.8))
    slow.append([round(t_rock1 - 0.35, 2), round(t_rock1 + 0.25, 2), 0.3])
    zoom(t_rock1, -2.4, z + 1.4, 0.55, 0.55)
    text("아슬아슬!", t_rock1 + 0.05, t_rock1 + 1.0, -2.4, z + 3.0, "#ff9a3c", 1.0, -2)
    P.wait(0.25)
    P.pose("놀람")
    P.wait(0.75, "놀람")
    P.move(2.0, RUN)
    t_rock2 = P.t + 0.6
    rocks.append((t_rock2, 4.0))
    P.wait(0.9)
    P.move(LADDERS[2], RUN, jump_at=[hole_jump(2, P.x)])
    for th, x in rocks:
        dur = 0.55
        objs.append({"모양": "글자", "내용": "!", "글자크기": 0.9, "색": "#ff3030", "동작": [
            {"초": round(th - dur - 0.6, 2), "위치": [x, -1.5, z + 0.3]}, {"초": round(th - 0.05, 2), "위치": [x, -1.5, z + 0.3]}]})
        ks = []
        for k in range(9):
            u = k / 8
            ks.append({"초": round(th - dur + dur * u, 3), "위치": [x, 0, round(ceil - (ceil - (z + 0.5)) * u * u, 3)]})
        objs.append({"모양": "돌", "반지름": 0.5, "쿵": [round(th, 2)], "등속": True, "동작": ks})
        for k in range(5):
            dx = (0.5 + 0.35 * k) * (1 if k % 2 else -1)
            pk = []
            for j in range(7):
                u = j / 6
                pk.append({"초": round(th + 0.45 * u, 3), "위치": [round(x + dx * u, 3), -0.2, round(z + 0.25 + 4 * 0.8 * u * (1 - u) - 0.13 * u, 3)]})
            pk.append({"초": round(th + 0.9, 3), "위치": pk[-1]["위치"]})
            objs.append({"모양": "조각", "반지름": 0.12, "등속": True, "동작": pk})
        add_score(th, 100, x, z)
    P.climb(FLOORS[3])

    # ── 4층: 구멍 건너기 → 뒤에서 굴러오는 통나무를 점프(느리게+확대). 통나무는 구멍으로 아래층에 떨어짐
    z = FLOORS[3]
    tempo.append((P.t, 175))
    t0, x0 = P.t, P.x
    log_t0, log_v = t0 + 0.3, 6.5
    log_x0 = -EDGE - 0.5
    tm = meet(x0, -RUN, t0, log_x0, log_v, log_t0)
    hj = hole_jump(3, x0)
    P.move(LADDERS[3], RUN, jump_at=[hj, (tm, 0.65, JUMP_H)])
    xm = P.x_at(t0, x0, LADDERS[3], RUN, tm)
    slow.append([round(tm - 0.3, 2), round(tm + 0.3, 2), 0.3])
    zoom(tm, xm, z + 1.6, 0.6, 0.6)
    # 통나무 길: 구멍마다 아래층으로 떨어짐
    lk = [{"초": round(log_t0, 3), "위치": [log_x0, 0, z + r]}]
    t_c, x_c, fl, thuds = log_t0, log_x0, 3, []
    while True:
        drop = None
        if fl in HOLES and HOLES[fl][0] > x_c:
            drop = sum(HOLES[fl]) / 2
        if drop is None:
            t_c += (EDGE + 0.5 - x_c) / log_v
            lk.append({"초": round(t_c, 3), "위치": [EDGE + 0.5, 0, FLOORS[fl] + r]})
            break
        t_c += (drop - x_c) / log_v
        lk.append({"초": round(t_c, 3), "위치": [drop, 0, FLOORS[fl] + r]})
        for k in range(1, 7):
            u = k / 6
            lk.append({"초": round(t_c + 0.45 * u, 3), "위치": [round(drop + 0.4 * u, 3), 0,
                                                              round(FLOORS[fl] + r - (FLOORS[fl] - FLOORS[fl - 1]) * u * u, 3)]})
        t_c += 0.45
        x_c = drop + 0.4
        fl -= 1
        thuds.append(round(t_c, 2))
    objs.append({"모양": "통나무", "반지름": r, "쿵": thuds, "동작": lk})
    add_score(tm + 0.3, 300, xm, z)
    P.climb(FLOORS[4])

    # ── 꼭대기: 괴물 우주인 — 심장 소리, 광선을 점프로 피함(느리게+확대), 화살 3발
    z = FLOORS[4]
    tempo.append((P.t, 185))
    alien_x = -1.0
    t_top = P.t
    P.turn(60)
    P.wait(0.3)
    t_laser = P.t
    objs.append({"모양": "광선", "색": "#7CFF4F", "동작": [{"초": round(t_laser, 2), "위치": [alien_x - 1.0, 0, z + 1.6]},
                                                         {"초": round(t_laser + 0.9, 2), "위치": [-14.5, 0, z + 1.0]}]})
    slow.append([round(t_laser + 0.15, 2), round(t_laser + 0.75, 2), 0.3])
    zoom(t_laser + 0.45, P.x + 1.8, z + 1.8, 0.7, 0.6)
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
    alien_acts = [{"초": 0, "자세": "서기", "위치": [alien_x, 0, z]}, {"초": round(t_laser - 0.4, 2), "자세": "광선"},
                  {"초": round(t_laser + 0.5, 2), "자세": "서기"}]
    for th in hits[:-1]:
        alien_acts += [{"초": round(th, 2), "자세": "맞음"}, {"초": round(th + 0.35, 2), "자세": "서기"}]
    alien_acts += [{"초": round(t_fall, 2), "자세": "쓰러짐", "위치": [alien_x, 0, z]}]
    for k in range(1, 9):  # 튕겨 올랐다가 아래로 떨어져 사라짐
        u = k / 8
        alien_acts.append({"초": round(t_fall + 1.0 * u, 3),
                           "위치": [round(alien_x + 1.5 * u, 3), -1.0, round(z + 4 * 1.2 * u * (1 - u) - (z + 4) * u * u, 3)]})
    sfx.append({"초": round(t_fall + 0.1, 2), "소리": "휘익"})

    # 감옥으로 가서 문 열기
    cage_x = 5.0
    P.move(cage_x - 1.6, RUN)
    t_open = P.t + 0.2
    P.wait(0.6)
    objs.append({"모양": "감옥", "동작": [{"초": 0, "위치": [cage_x, 0, z]}, {"초": round(t_open, 2), "위치": [cage_x, 0, z]},
                                        {"초": round(t_open + 0.8, 2), "위치": [cage_x, 0, z + 3.5]}]})
    sfx.append({"초": round(t_open, 2), "소리": "점프"})
    t_meet = t_open + 0.9
    objs.append({"모양": "하트", "크기": 0.2, "동작": [{"초": round(t_meet, 2), "위치": [cage_x - 0.8, -1.2, z + 2.6]},
                                                    {"초": round(t_meet + 1.6, 2), "위치": [cage_x - 0.8, -1.2, z + 3.4]}]})
    princess_acts = [{"초": 0, "자세": "놀람", "위치": [cage_x, 0.2, z], "방향": 0},
                     {"초": round(t_open, 2), "자세": "서기"},
                     {"초": round(t_open + 0.3, 2), "방향": -60}, {"초": round(t_meet, 2), "자세": "만세"}]
    add_score(t_meet, 5000, cage_x - 1.5, z)
    P.pose("만세", t_meet)
    t_clear = t_meet + 0.3
    text("구출 성공!", t_clear, t_clear + 3.5, 0, 7.2, "#ffe14d", 1.8)
    total = round(t_clear + 3.5, 2)

    # ── 화면 위 정보: 점수(오른쪽), 남은 시간(가운데, 5초부터 빨강+삐), 목숨 하트(왼쪽)
    objs.append({"모양": "글자", "내용": "점수 0", "글자크기": 0.8, "색": "#ffffff", "바뀜": scores, "화면고정": True,
                 "동작": [{"초": 0, "위치": [12.5, -3, 16.3]}, {"초": total, "위치": [12.5, -3, 16.3]}]})
    TL = math.ceil(t_meet) + 2  # 구출할 때 2초 남음
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
        if k < 2:
            wins = [(0, total)]
        else:  # 쏘였을 때 깜빡이다 사라짐
            wins = [(0, t_sting), (t_sting + 0.15, t_sting + 0.3), (t_sting + 0.45, t_sting + 0.6)]
        for a_, b_ in wins:
            objs.append({"모양": "하트", "크기": 0.13, "화면고정": True, "동작": [{"초": round(a_, 2), "위치": [hx, -3, 15.75]},
                                                             {"초": round(b_, 2), "위치": [hx, -3, 15.75]}]})

    acts = sorted(P.keys, key=lambda k: k["초"])
    # 인물·감옥을 앞줄(FRONT)로: 벽돌 바닥보다 앞이라 겹쳐도 가려지지 않음
    def front(keys):
        for k in keys:
            if "위치" in k:
                k["위치"][1] = round(k["위치"][1] + FRONT, 3)
        return keys
    front(acts)
    front(alien_acts)
    front(princess_acts)
    for o in objs:
        if o["모양"] == "감옥":
            front(o["동작"])
    stage = {"바닥": [-14, 14], "발판": [], "사다리": []}
    for i, zt in enumerate(FLOORS[1:]):  # 사다리가 올라오는 곳 + 끊어진 바닥에 구멍
        fl = i + 1
        cuts = sorted([(LADDERS[i] - GAP, LADDERS[i] + GAP)] + ([HOLES[fl]] if fl in HOLES else []))
        x = -EDGE
        for a_, b_ in cuts:
            stage["발판"].append([x, a_, zt])
            x = b_
        stage["발판"].append([x, EDGE, zt])
        stage["사다리"].append([LADDERS[i], FLOORS[i], zt])
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
        "카메라": cams,
        "슬로": slow, "번쩍": flashes,
        "미리보기": {"초": [round(t_laser - 0.4, 2), round(t_laser + 1.0, 2)], "글자": "과연 공주를 구할 수 있을까?"},
    }
    json.dump(scene, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("저장:", out, "| 장면 길이", total, "초 | 점수", score, "| 남은 시간", TL - math.ceil(t_meet), "초 정도")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "블록애니/장면_공주구출.json")
