"""안데스 선율 배경음 — 케나(갈대 피리)가 가락을 불고, 차랑고(작은 현악기)가 화음을 긁고, 봄보(큰북)가 와이노 장단(2/4)
사용자 결정 2026-11-05 (잉카 미라 편): 배경음은 선율이 있는 연주로 (CLAUDE.md 4장) → 안데스·잉카 편 가락 배경음.
라 단조 오음계(라 도 레 미 솔)로 새로 지은 가락 — 민요·유명 곡을 옮긴 것이 아님. 아이들이 산을 오르는 차분하고 애잔한 느낌.
악기 소리는 공통.py 로 컴퓨터가 직접 합성 → 녹음 음원·편곡을 쓰지 않아 저작권 걱정 없음

  - song(n, rng): n 샘플 길이 (가락 A A' B A 한 바퀴 → 쉬어 가는 장단 → 되풀이, 둘째 바퀴부터 두 번째 케나가 3도 아래로 따라 붊)
혼자 시험: python -X utf8 전통악기/안데스선율.py <결과.wav> [초]
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import 공통 as K  # noqa: E402

SR = K.SR
PENTA = [0, 3, 5, 7, 10]      # 라 단조 오음계 (라 도 레 미 솔)
ROOT = 69                     # A4
E8 = 60 / 60 / 2              # 와이노 2/4: 4분음표 60 → 8분음표 길이(초). 처음 84 → 주제가 무거워 느리게 (사용자 결정 2026-11-05)

# 가락: (음 자리, 8분음표 개수) — 마디마다 4칸(2/4). 자리 0 = 라, 5 = 한 옥타브 위 라
A1 = [(4, 1), (3, 1), (2, 2), (3, 1), (2, 1), (1, 2), (2, 1), (1, 1), (0, 1), (1, 1), (0, 4),
      (2, 1), (3, 1), (4, 2), (3, 1), (2, 1), (1, 2), (0, 1), (1, 1), (2, 2), (0, 4)]
A2 = [(4, 1), (3, 1), (2, 2), (3, 1), (2, 1), (1, 2), (2, 1), (1, 1), (0, 1), (1, 1), (0, 4),
      (5, 1), (4, 1), (3, 2), (4, 1), (3, 1), (2, 2), (1, 1), (2, 1), (1, 1), (-1, 1), (0, 4)]
B1 = [(5, 2), (6, 2), (5, 1), (4, 1), (3, 2), (4, 1), (3, 1), (2, 2), (3, 4),
      (2, 2), (3, 2), (4, 1), (3, 1), (2, 2), (1, 1), (2, 1), (1, 1), (0, 1), (1, 4)]
FORM = [A1, A2, B1, A1]
CHORD = {0: [0, 7, 12, 15], 1: [3, 10, 15, 19], 2: [-4, 3, 8, 12], 4: [-2, 5, 10, 14]}   # 마디 화음(라 단조·도 장조·파 장조·솔 장조) 반음


def deg_midi(d):
    o, k = divmod(d, 5)
    return ROOT + 12 * o + PENTA[k]


def quena(f, d, rng, accent=False):
    return K.flute(f, d, breath=0.32, vib=0.01 if d > 0.5 else 0.004, vib_rate=5.5, slide=0.025 if accent else 0.0, rng=rng)


def charango(buf, t, chord, rng, gain=0.09):
    """차랑고 긁기: 화음 네 줄을 빠르게 훑어 내림"""
    for i, st in enumerate(chord):
        K.place(buf, K.pluck(K.hz(ROOT - 12 + st), 0.7, damp=0.99, bright=0.7, rng=rng), t + i * 0.012, gain, pan=0.3)


def bars_of(mel):
    return sum(k for _, k in mel) // 4


def accompany(buf, t0, bars, rng, chords, gain=1.0):
    """와이노 장단: 봄보(큰북) 길게-짧게-짧게 + 차랑고 두 번 긁기"""
    for b in range(bars):
        tb = t0 + b * 4 * E8
        ch = CHORD[chords[b % len(chords)]]
        K.place(buf, K.frame_drum(0.6, True, rng), tb, 0.16 * gain, pan=-0.2)
        K.place(buf, K.frame_drum(0.4, True, rng), tb + 3 * E8, 0.09 * gain, pan=-0.2)
        K.place(buf, K.frame_drum(0.2, False, rng), tb + 2 * E8, 0.05 * gain, pan=-0.1)
        charango(buf, tb + 1 * E8, ch, rng, 0.08 * gain)
        charango(buf, tb + 3 * E8, ch, rng, 0.06 * gain)


def phrase(buf, t, mel, rng, second):
    t0 = t
    for deg, k in mel:
        d = k * E8
        K.place(buf, quena(K.hz(deg_midi(deg)), d + 0.08, rng, accent=k >= 2), t, 0.34, pan=0.1)
        if second:
            K.place(buf, quena(K.hz(deg_midi(deg - 1)), d + 0.08, rng), t, 0.16, pan=-0.25)   # 두 번째 케나: 한 자리 아래
        t += d
    accompany(buf, t0, bars_of(mel), rng, [0, 0, 1, 0, 4, 2, 4, 0])
    return t


def rest_bars(buf, t, rng, bars=4):
    accompany(buf, t, bars, rng, [0, 4, 2, 0], gain=0.8)
    return t + bars * 4 * E8


def song(n, rng, mode=None):
    buf = np.zeros((n + int(3 * SR), 2), np.float32)
    t, rnd = 0.6, 0
    while t < n / SR:
        for mel in FORM:
            t = phrase(buf, t, mel, rng, second=rnd % 2 == 1)
        t = rest_bars(buf, t, rng)
        rnd += 1
    return K.reverb(buf[:n], rng, sec=2.6, wet=0.35)


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "안데스선율.wav"
    sec = float(sys.argv[2]) if len(sys.argv) > 2 else 45
    K.write_wav(out, song(int(sec * SR), np.random.default_rng(7)))
    print(out)
