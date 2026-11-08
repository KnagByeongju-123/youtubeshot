# -*- coding: utf-8 -*-
"""떨어지는 돌을 좌우로 피하는 장면 — 단계마다 어려워짐(하나씩 → 둘씩 → 돌 비 → 거대 바위).
돌이 떨어질 곳·시각과 전사가 움직일 길만 적으면: 빨간 '!' 경고, 점점 빨라지는 낙하, 부서지는 조각,
점수, 거대 바위의 화면 흔들림을 자동으로 넣음. 전사가 돌에 맞는 자리에 있으면 경고를 띄움.

  python 블록애니/돌_단계_만들기.py 블록애니/장면_돌.json
  xvfb-run -a .blender_venv/bin/python 블록애니.py 장면 블록애니/장면_돌.json 결과.mp4
"""
import json
import random
import sys

TOP = 9.5  # 돌이 나타나는 높이
START_X = 0.0
# 단계: (제목, 제목 시각, 떨어지는 시간(초), 점수, [(땅에 닿는 초, x), ...])
WAVES = [
    ("1단계", 0.3, 1.3, 100, [(2.4, 0.0), (3.8, -2.5), (5.0, 1.5)]),
    ("2단계", 5.8, 1.0, 200, [(7.6, 3.5), (7.6, 0.5), (8.8, -2.5), (8.8, -5.0)]),
    ("3단계", 9.6, 0.8, 300, [(11.2, 2.0), (11.6, -1.0), (12.0, 4.5), (12.4, -4.0), (12.8, 3.2), (13.2, -1.8)]),
]
ROCK_R = 0.5
# 전사 움직임: (출발 초, 도착 초, 도착 x, 자세)
MOVES = [(1.3, 2.0, -2.5, "걷기"), (2.8, 3.4, 1.5, "걷기"), (4.0, 4.6, 3.5, "걷기"),
         (6.6, 7.2, -2.5, "달리기"), (7.9, 8.5, 2.0, "달리기"),
         (10.4, 10.9, 3.2, "달리기"), (12.2, 12.65, 0.5, "달리기"), (14.8, 15.6, -6.5, "달리기")]
SURPRISE = [(12.66, 13.1)]  # (시작, 끝) 아슬아슬해서 놀라는 때
BIG = {"제목": ("거대 바위!", 13.6), "x": 0.5, "닿는초": 16.0, "떨어지는시간": 1.3, "반지름": 1.6, "점수": 1000}
CLEAR = 17.2
TOTAL = 20.5
rng = random.Random(3)


def fall_keys(x, t_hit, dur, r, n=10):
    """점점 빨라지며 떨어짐(높이 = 위 - 거리 × u²)."""
    out = []
    for k in range(n + 1):
        u = k / n
        out.append({"초": round(t_hit - dur + dur * u, 3), "위치": [x, 0, round(TOP - (TOP - r) * u * u, 3)]})
    return out


def debris(x, t, count=5, stay=0.5, big=False):
    """땅에 닿은 곳에서 튀는 조각들."""
    out = []
    for k in range(count):
        dx = rng.uniform(0.6, 2.2 if not big else 3.5) * (1 if k % 2 else -1)
        peak = rng.uniform(0.5, 1.3 if not big else 2.2)
        d = 0.45 if not big else 0.7
        keys = []
        for j in range(7):
            u = j / 6
            keys.append({"초": round(t + d * u, 3),
                         "위치": [round(x + dx * u, 3), -0.2, round(0.25 + 4 * peak * u * (1 - u) - 0.13 * u, 3)]})
        keys.append({"초": round(t + d + stay, 3), "위치": keys[-1]["위치"]})
        out.append({"모양": "조각", "반지름": 0.12 if not big else 0.22, "등속": True, "동작": keys})
    return out


def player_x(t):
    x = START_X
    for t0, t1, xt, _ in MOVES:
        if t >= t1:
            x = xt
        elif t0 <= t < t1:
            u = (t - t0) / (t1 - t0)
            u = u * u * (3 - 2 * u)
            return x + (xt - x) * u
    return x


def main(out):
    objs, score_changes, sfx = [], [[0, "점수 0"]], []
    score = 0

    def title(txt, t0, dur=1.6, color="#ffffff", size=1.0):
        objs.append({"모양": "글자", "내용": txt, "글자크기": size, "색": color,
                     "동작": [{"초": t0, "위치": [0, -1, 5.4]}, {"초": t0 + dur, "위치": [0, -1, 5.6]}]})

    def dodged(t, pts):
        nonlocal score
        px = player_x(t)
        objs.append({"모양": "글자", "내용": f"+{pts}", "글자크기": 0.85, "동작": [
            {"초": t + 0.1, "위치": [px, -0.8, 3.3]}, {"초": t + 0.8, "위치": [px, -0.8, 4.1]}]})
        score += pts
        score_changes.append([round(t + 0.1, 2), f"점수 {score}"])
        sfx.append({"초": round(t + 0.12, 2), "소리": "동전"})

    def check(t, x, r):
        px = player_x(t)
        if abs(px - x) < r + 0.45:
            print(f"  !! 경고: {t}초에 x={x} 돌이 떨어지는데 전사가 x={px:.2f} 에 있음(맞음)")

    for name, t0, dur, pts, rocks in WAVES:
        title(name, t0)
        for th, x in rocks:
            objs.append({"모양": "글자", "내용": "!", "글자크기": 0.9, "색": "#ff3030", "동작": [
                {"초": round(th - dur - 0.4, 2), "위치": [x, -1.2, 0.3]}, {"초": round(th - 0.05, 2), "위치": [x, -1.2, 0.3]}]})
            objs.append({"모양": "돌", "반지름": ROCK_R, "쿵": [th], "등속": True, "동작": fall_keys(x, th, dur, ROCK_R)})
            objs += debris(x, th)
            check(th, x, ROCK_R)
            dodged(th, pts)

    # 거대 바위: 떨어져서 그대로 남음 + 화면 흔들림
    b = BIG
    title(b["제목"][0], b["제목"][1], 1.0, "#ff5a5a", 1.1)  # 바위가 떨어지기 전에 사라짐
    th, x, r = b["닿는초"], b["x"], b["반지름"]
    objs.append({"모양": "글자", "내용": "!!", "글자크기": 1.3, "색": "#ff3030", "동작": [
        {"초": round(th - b["떨어지는시간"] - 0.6, 2), "위치": [x, -2.2, 0.4]}, {"초": round(th - 0.05, 2), "위치": [x, -2.2, 0.4]}]})
    keys = fall_keys(x, th, b["떨어지는시간"], r * 0.95, n=14)  # 아래 덩어리까지 땅 위에
    keys.append({"초": TOTAL, "위치": keys[-1]["위치"]})
    objs.append({"모양": "돌", "반지름": r, "쿵": [th], "휘익": True, "등속": True, "돌기": 3.0, "동작": keys})
    objs += debris(x, th, count=8, stay=TOTAL - th, big=True)
    check(th, x, r)
    dodged(th, b["점수"])

    title("클리어!", CLEAR, TOTAL - CLEAR, "#ffe14d", 1.3)
    objs.append({"모양": "글자", "내용": "점수 0", "글자크기": 0.55, "색": "#ffffff", "바뀜": score_changes,
                 "동작": [{"초": 0, "위치": [5.6, -1, 7.3]}, {"초": TOTAL, "위치": [5.6, -1, 7.3]}]})

    # 전사: 움직일 때 그쪽을 바라보고 걷기·달리기, 멈추면 서기
    acts = [{"초": 0, "자세": "서기", "위치": [START_X, 0, 0], "방향": 60}, {"초": 0.9, "자세": "놀람"}, {"초": 1.25, "자세": "서기"}]
    x, face = START_X, 60
    for t0, t1, xt, pose in MOVES:
        nf = 60 if xt > x else -60
        acts += [{"초": t0, "자세": pose, "위치": [x, 0, 0], "방향": face},
                 {"초": round(t0 + 0.15, 3), "방향": nf},
                 {"초": t1, "자세": "서기", "위치": [xt, 0, 0]}]
        x, face = xt, nf
    for a, z in SURPRISE:
        acts += [{"초": a, "자세": "놀람"}, {"초": z, "자세": "서기"}]
    acts += [{"초": th, "자세": "놀람"}, {"초": th + 0.8, "자세": "서기"},
             {"초": CLEAR, "자세": "만세", "방향": face}, {"초": CLEAR + 0.3, "방향": 0}]
    acts.sort(key=lambda k: k["초"])

    # 카메라: 거대 바위가 닿을 때 흔들림(점점 약해짐)
    cams = [{"초": 0, "위치": [0, -30, 3.6], "보는곳": [0, 0, 3.6], "직교": 16}]
    for k in range(13):
        t = th + k * 0.05
        amp = 0.35 * (1 - k / 12)
        dx = amp * (1 if k % 2 else -1)
        dz = amp * 0.6 * (1 if k % 3 else -1)
        cams.append({"초": round(t, 3), "위치": [dx, -30, 3.6 + dz], "보는곳": [dx, 0, 3.6 + dz], "직교": 16})
    cams.append({"초": th + 0.7, "위치": [0, -30, 3.6], "보는곳": [0, 0, 3.6], "직교": 16})
    cams.insert(1, {"초": th - 0.01, "위치": [0, -30, 3.6], "보는곳": [0, 0, 3.6], "직교": 16})

    scene = {
        "캐릭터": "캐릭터.json", "초": TOTAL, "fps": 24, "크기": [1920, 1080], "픽셀": 6, "꼬마": 1.5,
        "배경": "레트로",
        "무대": {"바닥": [-9, 9], "발판": [[-9, -5, 4.8], [5.5, 9, 6.0]], "사다리": [[-5.6, 0, 4.8]]},
        "인물": [{"이름": "전사", "위치": [START_X, 0, 0], "방향": 60, "동작": acts}],
        "물체": objs,
        "효과음": sfx + [{"초": CLEAR, "소리": "승리"}],
        "배경음": {"곡": "레트로전투", "크기": 0.35, "끝": CLEAR - 0.1},
        "카메라": cams,
    }
    json.dump(scene, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("저장:", out, "| 최종 점수", score, "| 돌", sum(len(w[4]) for w in WAVES) + 1, "개")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "블록애니/장면_돌.json")
