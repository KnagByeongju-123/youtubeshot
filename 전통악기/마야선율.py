"""메소아메리카(마야) 선율 배경음 — 흙으로 빚은 피리(오카리나 같은 흙피리) 가락, 통나무 북(툰쿨) 낮은 두 음, 거북 등딱지 북(작고 마른 소리),
뜯는 현 대신 나무 막대 실로폰처럼 짧게 울리는 화음(아주 작게).
2026-11-06 (마야 천문학자 삭 탄 와아스 편): 배경음은 선율이 있는 연주로 (CLAUDE.md 4장) → 마야·메소아메리카 편 가락 배경음.
레 단조 오음계(레 파 솔 라 도)로 새로 지은 가락 — 전통 곡·유명 곡을 옮긴 것이 아님. 별을 오래 바라보는 듯 차분하고 신비로운 느낌, 느린 템포.
악기 소리는 공통.py 로 컴퓨터가 직접 합성 → 녹음 음원·편곡을 쓰지 않아 저작권 걱정 없음

  - song(n, rng): n 샘플 길이 (가락 A A' B A 한 바퀴 → 북만 남는 쉼 → 되풀이, 둘째 바퀴부터 두 번째 흙피리가 5도 아래로 따라 붊)
혼자 시험: python -X utf8 전통악기/마야선율.py <결과.wav> [초]
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import 공통 as K  # noqa: E402

SR = K.SR
PENTA = [0, 3, 5, 7, 10]      # 레 단조 오음계 (레 파 솔 라 도)
ROOT = 62                     # D4
Q = 60 / 52                   # 4분음표 52 (느리게)

A1 = [(4, 2), (3, 1), (2, 1), (3, 3), (1, 1), (2, 2), (1, 1), (0, 1), (0, 4)]
A2 = [(4, 2), (5, 1), (4, 1), (3, 3), (2, 1), (1, 2), (2, 1), (3, 1), (2, 4)]
B1 = [(5, 3), (6, 1), (5, 2), (4, 2), (3, 2), (4, 1), (3, 1), (1, 4)]
FORM = [A1, A2, B1, A1]
CHORD = {0: [-12, -5, 0, 3], 1: [-9, -2, 3, 7], 2: [-7, 0, 5, 8], 3: [-14, -7, -2, 2]}   # 레 단조·파·솔 단조·도 (반음)
PROG = [0, 0, 1, 2, 0, 3, 2, 0]


def deg_midi(d):
    o, k = divmod(d, 5)
    return ROOT + 12 * o + PENTA[k]


def clay_flute(f, d, rng):
    """흙피리: 둥글고 숨소리 많은 소리, 긴 음은 천천히 떨림"""
    return K.flute(f, d, breath=0.18, vib=0.005, slide=0.03, rng=rng, vib_rate=4.6)


def wood_bar(f, d, rng):
    """나무 막대를 치는 짧고 마른 소리"""
    return K.pluck(f, max(0.6, d), damp=0.985, bright=0.3, rng=rng)


def bars_of(mel):
    return sum(k for _, k in mel) // 4


def accompany(buf, t0, bars, rng, gain=1.0):
    for b in range(bars):
        tb = t0 + b * 4 * Q
        ch = CHORD[PROG[b % len(PROG)]]
        K.place(buf, K.big_drum(70, 1.8, rng), tb, 0.07 * gain, pan=-0.1)               # 통나무 북 툰쿨: 낮은 음
        K.place(buf, K.big_drum(94, 1.2, rng), tb + 2.5 * Q, 0.04 * gain, pan=0.1)       # 높은 음
        K.place(buf, K.frame_drum(0.4, False, rng), tb + 1 * Q, 0.025 * gain, pan=0.35)  # 거북 등딱지 북
        K.place(buf, K.frame_drum(0.4, False, rng), tb + 3 * Q, 0.02 * gain, pan=0.35)
        for j, st in enumerate(ch):
            K.place(buf, wood_bar(K.hz(ROOT + st), 1.0, rng), tb + j * Q * 0.5, 0.05 * gain, pan=-0.3)


def phrase(buf, t, mel, rng, second):
    t0 = t
    for deg, k in mel:
        d = k * Q
        f = K.hz(deg_midi(deg))
        K.place(buf, clay_flute(f, d + 0.25, rng), t, 0.30, pan=0.1)
        if second:
            K.place(buf, clay_flute(f * 2 ** (-7 / 12), d + 0.25, rng), t, 0.12, pan=-0.2)
        t += d
    accompany(buf, t0, bars_of(mel), rng)
    return t


def rest_bars(buf, t, rng, bars=2):
    accompany(buf, t, bars, rng, gain=0.8)
    return t + bars * 4 * Q


def song(n, rng, mode=None):
    buf = np.zeros((n + int(5 * SR), 2), np.float32)
    t, rnd = 0.6, 0
    while t < n / SR:
        for mel in FORM:
            t = phrase(buf, t, mel, rng, second=rnd % 2 == 1)
        t = rest_bars(buf, t, rng)
        rnd += 1
    return K.reverb(buf[:n], rng, sec=3.0, wet=0.4)


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "마야선율.wav"
    sec = float(sys.argv[2]) if len(sys.argv) > 2 else 45
    K.write_wav(out, song(int(sec * SR), np.random.default_rng(7)))
    print(out)
