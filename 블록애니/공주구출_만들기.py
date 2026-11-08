# -*- coding: utf-8 -*-
"""공주 구출 — 판(스테이지)마다 땅에서 출발해 기울어진 층과 사다리를 올라 꼭대기 감옥의 공주를 구함.
판이 끝나면 다음 판이 이어지고(점수도 이어짐), 판마다 영상을 만든 뒤 하나로 합침.

- 2·3·4층 바닥은 층마다 반대로 기울어짐. 전사는 늘 오르막, 통나무는 내리막으로 굴러옴.
- 통나무는 위 하늘에서 4층으로 떨어져 구르다가, 끊어진 바닥·사다리 구멍을 만나면 아래층으로 떨어지고
  그 층의 기울기를 따라 반대로 구름(4층 → 3층 → 2층 → 땅 → 화면 밖). 만나는 순간 전사가 자동으로 점프.
- 층마다 할 일(STAGES 의 "층"): "벌" = 날아오는 벌을 활로, "돌" = 하늘에서 떨어지는 돌을 멈췄다 피함, None = 그냥 지나감
- 꼭대기: 괴물 우주인(광선을 점프로 피하고 화살 N발) → 감옥이 열리고 하트 → 구출 성공!
- "거울": true 인 판은 좌우를 뒤집음(통나무가 반대쪽에서, 공주가 반대쪽에).

  python 블록애니/공주구출_만들기.py 블록애니/장면_공주구출        → 장면_공주구출_1판.json, _2판.json …
  xvfb-run -a .blender_venv/bin/python 블록애니.py 장면 블록애니/장면_공주구출_1판.json 1판.mp4   (판마다)
  .blender_venv/bin/python 블록애니.py 합치기 전체.mp4 1판.mp4 2판.mp4
"""
import json
import math
import sys

STAGES = [
    {"판": 1, "제목": "공주를 구하라!", "층": {1: ("벌", 2), 2: ("돌", 2), 3: (None, 0)},
     "통나무_간격": 2.6, "통나무_빠르기": 5.0, "보스_화살": 3, "거울": False},
    {"판": 2, "제목": "더 빨라진 통나무!", "층": {1: ("돌", 3), 2: ("벌", 3), 3: ("벌", 2)},
     "통나무_간격": 2.0, "통나무_빠르기": 6.0, "보스_화살": 4, "거울": True},
]

BASE = [0.0, 3.2, 6.4, 9.6, 12.8]  # 층 높이(가운데 기준): 땅, 2층, 3층, 4층, 꼭대기
DOWN = [-1, 1, -1, 1, 0]  # 내리막 방향(+1 = 오른쪽이 낮음). 땅은 평평하지만 통나무는 왼쪽으로 굴러감
SLOPE = 0.9 / 22
LADDERS = [8.0, -8.0, 8.0, -3.0]  # i 번째 사다리: i층 → i+1층
EDGE = 11.0
TOP_X0 = LADDERS[3] + 0.6  # 꼭대기 층은 사다리 오른쪽부터(왼쪽 위는 하늘 — 통나무가 떨어지는 곳)
HOLES = {1: (-3.4, -1.8), 2: (5.6, 7.2), 3: (2.8, 4.4)}  # 끊어진 바닥
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
        P.move(target)

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
        P.move(target)

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
        kind, n = cfg["층"].get(k, (None, 0))
        if kind == "벌":
            bees(n)
        elif kind == "돌":
            rocks(n)
        else:
            P.move(LADDERS[k])
        P.climb()

    # ── 꼭대기: 괴물 우주인
    z = BASE[4]
    alien_x = 1.5
    t_top = P.t
    P.turn(60)
    P.wait(0.3)
    t_laser = P.t
    objs.append({"모양": "광선", "색": "#7CFF4F", "동작": [{"초": round(t_laser, 2), "위치": [alien_x - 1.0, 0, z + 1.6]},
                                                         {"초": round(t_laser + 0.9, 2), "위치": [-14.5, 0, z + 1.0]}]})
    P.jump_here(2.4, 0.75)
    P.pose("활쏘기")
    hits = []
    for k in range(cfg["보스_화살"]):
        th = P.t + 0.55 + k * 0.7
        arrow(P.x + 0.9, z + 1.45, alien_x - 0.6, z + 1.6, th)
        hits.append(th)
    P.wait(hits[-1] - P.t + 0.3, "활쏘기")
    t_fall = hits[-1]
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
    text(f"{cfg['판']}판 클리어!", t_clear, t_clear + 3.2, 0, 7.2, "#ffe14d", 1.8)
    P.wait(3.3, "만세")
    total = round(t_clear + 3.2, 2)

    # ── 통나무: 하늘에서 계속 떨어짐 → 만나는 순간 자동 점프(+100)
    t_d = 1.2
    while t_d < t_top - 2:
        lk, thuds = log_path(t_d, LOG_DROP_X, cfg["통나무_빠르기"])
        objs.append({"모양": "통나무", "반지름": LOG_R, "쿵": thuds, "동작": lk})
        last, t = -9, lk[0]["초"]
        while t < lk[-1]["초"]:
            lp = interp(lk, t)
            px, pz, pk = P.pos(t)
            if lp and not P.climbing(t) and abs(lp[2] - LOG_R - pz) < 0.35 and abs(lp[0] - px) < 0.3 and t - last > 1.0:
                P.jumps.append((t, *JUMP))
                add_score(t + 0.3, 100, px, pz)
                last = t
            t += 0.01
        t_d += cfg["통나무_간격"]

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
                 {"이름": "괴물우주인", "위치": [alien_x, FRONT, z], "방향": -60, "바꿈": {"키": 1.0}, "동작": alien_acts},
                 {"이름": "공주", "위치": [cage_x, FRONT + 0.2, z], "방향": 0, "동작": princess_acts}],
        "물체": objs,
        "효과음": sfx + [{"초": round(t_clear, 2), "소리": "승리"}],
        "배경음": {"곡": "레트로전투", "크기": 0.35, "끝": round(t_clear - 0.1, 2)},
        "카메라": CAM,
    }
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
