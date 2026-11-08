# -*- coding: utf-8 -*-
"""굴러오는 통나무를 점프로 피하는 장면 — 단계마다 어려워짐(1개 → 2개 빠르게 → 3개 연달아 → 큰 통나무).
통나무마다 출발 시각·빠르기만 적으면, 전사 앞을 지나는 시각을 계산해 그 순간에 맞춰 포물선 점프·점수를 넣음.

  python 블록애니/통나무_단계_만들기.py 블록애니/장면_통나무.json
  xvfb-run -a .blender_venv/bin/python 블록애니.py 장면 블록애니/장면_통나무.json 결과.mp4
"""
import json
import sys

PX = -3.0  # 전사 자리
START_X, END_X = 9.8, -10.8

# 단계: (제목, 제목 시각, [(출발 초, 빠르기 m/초, 반지름 m, 점수, 점프 길이 초, 점프 높이 m), ...])
WAVES = [
    ("1단계", 0.3, [(1.2, 4.0, 0.6, 100, 0.7, 1.7)]),
    ("2단계", 6.0, [(6.8, 5.5, 0.6, 200, 0.6, 1.7), (7.9, 5.5, 0.6, 200, 0.6, 1.7)]),
    ("3단계", 11.0, [(11.8, 7.0, 0.6, 300, 0.5, 1.6), (12.6, 7.0, 0.6, 300, 0.5, 1.6), (13.2, 7.0, 0.6, 300, 0.5, 1.6)]),
]
# 큰 통나무: 오른쪽 위 발판(높이 6m)에서 굴러 떨어져 한 번 튕긴 뒤 굴러옴
BIG = {"제목": ("큰 통나무!", 16.0), "반지름": 1.0, "출발": 16.6, "빠르기": 6.0, "점수": 1000}
CLEAR = 20.8
TOTAL = 24.0


def arc(t0, t1, x0, x1, z0, z1, peak, n=8):
    """t0→t1 동안 (x0,z0)→(x1,z1) 포물선(peak = 가운데에서 더 오르는 높이). 키 목록."""
    out = []
    for k in range(n + 1):
        u = k / n
        z = z0 + (z1 - z0) * u + 4 * peak * u * (1 - u)
        out.append({"초": round(t0 + (t1 - t0) * u, 3), "위치": [round(x0 + (x1 - x0) * u, 3), 0, round(z, 3)]})
    return out


def main(out):
    objs, jumps, score_changes, extra_sfx = [], [], [[0, "점수 0"]], []
    score = 0

    def title(txt, t0, dur=1.6, color="#ffffff", size=1.0):
        objs.append({"모양": "글자", "내용": txt, "글자크기": size, "색": color,
                     "동작": [{"초": t0, "위치": [0, -1, 5.4]}, {"초": t0 + dur, "위치": [0, -1, 5.6]}]})

    def passed(tp, pts):
        nonlocal score
        objs.append({"모양": "글자", "내용": f"+{pts}", "동작": [
            {"초": tp + 0.15, "위치": [PX, -0.8, 3.3]}, {"초": tp + 1.05, "위치": [PX, -0.8, 4.3]}]})
        score += pts
        score_changes.append([round(tp + 0.15, 2), f"점수 {score}"])
        extra_sfx.append({"초": round(tp + 0.15, 2), "소리": "동전"})

    for name, t0, logs in WAVES:
        title(name, t0)
        for ts, v, r, pts, jd, jh in logs:
            t_end = ts + (START_X - END_X) / v
            tp = ts + (START_X - PX) / v
            objs.append({"모양": "통나무", "반지름": r, "동작": [
                {"초": ts, "위치": [START_X, 0, r]}, {"초": round(t_end, 3), "위치": [END_X, 0, r]}]})
            jumps.append((tp, jd, jh))
            passed(tp, pts)

    # 큰 통나무
    b = BIG
    r, v = b["반지름"], b["빠르기"]
    title(b["제목"][0], b["제목"][1], 1.6, "#ff5a5a", 1.1)
    plat_z = 6.0
    ks = [{"초": b["출발"], "위치": [8.0, 0, plat_z + r]}, {"초": b["출발"] + 0.5, "위치": [5.5, 0, plat_z + r]}]
    t_land1 = b["출발"] + 1.0
    ks += arc(b["출발"] + 0.5, t_land1, 5.5, 4.0, plat_z + r, r, 0.4)[1:]  # 떨어짐
    t_land2 = t_land1 + 0.6
    ks += arc(t_land1, t_land2, 4.0, 1.2, r, r, 1.3)[1:]  # 한 번 튕김
    t_end = t_land2 + (1.2 - END_X) / v
    ks.append({"초": round(t_end, 3), "위치": [END_X, 0, r]})
    objs.append({"모양": "통나무", "반지름": r, "색": "#6a3d1a", "쿵": [t_land1, t_land2], "동작": ks})
    tp = t_land2 + (1.2 - PX) / v
    jumps.append((tp, 0.9, 3.1))
    passed(tp, b["점수"])
    surprise = t_land1

    title("클리어!", CLEAR, TOTAL - CLEAR, "#ffe14d", 1.3)
    objs.append({"모양": "글자", "내용": "점수 0", "글자크기": 0.55, "색": "#ffffff", "바뀜": score_changes,
                 "동작": [{"초": 0, "위치": [5.6, -1, 7.3]}, {"초": TOTAL, "위치": [5.6, -1, 7.3]}]})

    # 전사: 지나가는 순간이 점프 한가운데가 되게
    acts = [{"초": 0, "자세": "서기", "위치": [PX, 0, 0]}, {"초": 1.0, "자세": "놀람"}, {"초": 1.6, "자세": "서기"},
            {"초": surprise, "자세": "놀람"}, {"초": surprise + 0.5, "자세": "서기"}]
    for tp, d, h in jumps:
        t0, t1 = tp - d / 2, tp + d / 2
        acts.append({"초": round(t0, 3), "자세": "점프"})
        acts += arc(t0, t1, PX, PX, 0, 0, h)
        acts.append({"초": round(t1 + 0.001, 3), "자세": "서기"})
    acts.append({"초": CLEAR, "자세": "만세"})
    acts.sort(key=lambda k: k["초"])

    scene = {
        "캐릭터": "캐릭터.json", "초": TOTAL, "fps": 24, "크기": [1920, 1080], "픽셀": 6, "꼬마": 1.5,
        "배경": "레트로",
        "무대": {"바닥": [-9, 9], "발판": [[-9, -5, 4.8], [5.5, 9, 6.0]], "사다리": [[-5.6, 0, 4.8]]},
        "인물": [{"이름": "전사", "위치": [PX, 0, 0], "방향": 60, "동작": acts}],
        "물체": objs,
        "효과음": extra_sfx + [{"초": CLEAR, "소리": "승리"}],
        "배경음": {"곡": "레트로전투", "크기": 0.35, "끝": CLEAR - 0.1},
        "카메라": [{"초": 0, "위치": [0, -30, 3.6], "보는곳": [0, 0, 3.6], "직교": 16}],
    }
    json.dump(scene, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("저장:", out, "| 최종 점수", score, "| 점프", len(jumps), "번")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "블록애니/장면_통나무.json")
