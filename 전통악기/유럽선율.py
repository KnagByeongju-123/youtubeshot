"""유럽 선율 배경음 — 하프시코드 같은 건반(뜯는 소리)이 가락을 치고, 현악(활로 켜는 소리)이 길게 받쳐 주는 3/4 미뉴에트풍
2026-11-05 (나폴레옹 암호 편): 배경음은 선율이 있는 연주로 (CLAUDE.md 4장) → 18~19세기 유럽 편 가락 배경음.
레 단조(레 미 파 솔 라 시♭ 도)로 새로 지은 가락 — 기존 곡을 옮긴 것이 아님. 비밀 편지·암호처럼 조용히 긴장되는 느낌, 느린 템포.
악기 소리는 공통.py 로 컴퓨터가 직접 합성 → 녹음 음원·편곡을 쓰지 않아 저작권 걱정 없음

  - song(n, rng): n 샘플 길이 (가락 A A' B A 한 바퀴 → 쉬어 가는 마디 → 되풀이, 둘째 바퀴부터 현악이 가락을 함께)
혼자 시험: python -X utf8 전통악기/유럽선율.py <결과.wav> [초]
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import 공통 as K  # noqa: E402

SR = K.SR
MINOR = [0, 2, 3, 5, 7, 8, 10]   # 레 단조 (으뜸음 D)
ROOT = 62                        # D4
E4 = 60 / 72                     # 3/4: 4분음표 72 → 4분음표 길이(초)

# 가락: (음 자리, 4분음표 개수) — 마디마다 3박. 자리 0 = 레, 7 = 한 옥타브 위 레, 음수 = 아래
A1 = [(4, 1), (2, 1), (4, 1), (5, 2), (4, 1), (3, 1), (2, 1), (1, 1), (2, 3),
      (2, 1), (3, 1), (4, 1), (5, 1), (4, 1), (3, 1), (2, 1), (1, 1), (-1, 1), (0, 3)]
A2 = [(4, 1), (2, 1), (4, 1), (5, 2), (4, 1), (3, 1), (2, 1), (1, 1), (2, 3),
      (7, 1), (6, 1), (5, 1), (4, 2), (2, 1), (3, 1), (1, 1), (-1, 1), (0, 3)]
B1 = [(5, 2), (6, 1), (7, 2), (6, 1), (5, 1), (4, 1), (3, 1), (4, 3),
      (3, 2), (4, 1), (5, 1), (4, 1), (3, 1), (2, 1), (1, 1), (2, 1), (4, 3)]
FORM = [A1, A2, B1, A1]
BASS = {0: [0, 7], 3: [-2, 5], 4: [-3, 4], 5: [-4, 3]}   # 마디 바탕음(자리 → 낮은 두 음, 반음)


def deg_midi(d):
    o, k = divmod(d, 7)
    return ROOT + 12 * o + MINOR[k]


def harpsichord(f, d, rng):
    return K.pluck(f, d, damp=0.988, bright=0.85, buzz=0.05, rng=rng)


def strings(f, d):
    return K.bowed(f, d, band=(300, 2600), vib_rate=5.0, vib=0.006, attack=0.5, nasal=0.5)


def bars_of(mel):
    return sum(k for _, k in mel) // 3


def accompany(buf, t0, bars, rng, roots, gain=1.0):
    """왼손: 마디 첫 박 낮은 음 + 둘째·셋째 박 화음 (쿵-짝-짝)"""
    for b in range(bars):
        tb = t0 + b * 3 * E4
        lo = BASS[roots[b % len(roots)]]
        K.place(buf, harpsichord(K.hz(ROOT - 12 + lo[0]), 1.2, rng), tb, 0.26 * gain, pan=-0.25)
        for j in (1, 2):
            K.place(buf, harpsichord(K.hz(ROOT - 12 + lo[1]), 0.6, rng), tb + j * E4, 0.12 * gain, pan=-0.15)
        K.place(buf, strings(K.hz(ROOT - 24 + lo[0]), 3 * E4 + 0.3), tb, 0.10 * gain, pan=0.0)


def phrase(buf, t, mel, rng, with_strings):
    t0 = t
    for deg, k in mel:
        d = k * E4
        f = K.hz(deg_midi(deg))
        K.place(buf, harpsichord(f, max(0.9, d + 0.3), rng), t, 0.40, pan=0.15)
        if with_strings and k >= 2:
            K.place(buf, strings(f, d + 0.2), t, 0.13, pan=-0.1)
        t += d
    accompany(buf, t0, bars_of(mel), rng, [0, 3, 0, 4, 5, 3, 4, 0])
    return t


def rest_bars(buf, t, rng, bars=2):
    accompany(buf, t, bars, rng, [0, 4], gain=0.8)
    return t + bars * 3 * E4


def song(n, rng, mode=None):
    buf = np.zeros((n + int(4 * SR), 2), np.float32)
    t, rnd = 0.6, 0
    while t < n / SR:
        for mel in FORM:
            t = phrase(buf, t, mel, rng, with_strings=rnd % 2 == 1)
        t = rest_bars(buf, t, rng)
        rnd += 1
    return K.reverb(buf[:n], rng, sec=2.2, wet=0.3)


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "유럽선율.wav"
    sec = float(sys.argv[2]) if len(sys.argv) > 2 else 45
    K.write_wav(out, song(int(sec * SR), np.random.default_rng(7)))
    print(out)
