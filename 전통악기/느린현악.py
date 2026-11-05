"""느린 현악 배경음 — 바이올린 가락 + 비올라 화음 + 첼로 바탕음, 활로 길게 이어 켜는 아주 느린 연주
사용자 결정 2026-11-05 (잉카 미라 편): "현악 매우 느리게, 굳이 잉카 음악 필요 없어" → 지역 악기 대신 차분하고 애잔한 현악.
라 단조로 새로 지은 가락 — 기존 곡을 옮긴 것이 아님. 슬프고 조용한 주제(희생·죽음·잃어버린 것)에 두루 씀.
악기 소리는 공통.py 로 컴퓨터가 직접 합성 → 녹음 음원·편곡을 쓰지 않아 저작권 걱정 없음

  - song(n, rng): n 샘플 길이 (가락 A A' B A 한 바퀴 → 첼로만 남는 쉼 → 되풀이, 둘째 바퀴부터 두 번째 바이올린이 3도 아래로 함께)
혼자 시험: python -X utf8 전통악기/느린현악.py <결과.wav> [초]
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import 공통 as K  # noqa: E402

SR = K.SR
MINOR = [0, 2, 3, 5, 7, 8, 10]   # 라 단조
ROOT = 69                        # A4 (바이올린)
Q = 60 / 30                      # 4분음표 30 → 한 박 2초 (매우 느리게)

# 가락: (음 자리, 박 수) — 마디마다 4박. 자리 0 = 라, 7 = 한 옥타브 위, 음수 = 아래
A1 = [(4, 2), (3, 1), (2, 1), (2, 3), (1, 1), (0, 2), (1, 1), (2, 1), (1, 4)]
A2 = [(4, 2), (5, 1), (4, 1), (3, 3), (2, 1), (1, 2), (-1, 1), (1, 1), (0, 4)]
B1 = [(5, 2), (6, 1), (7, 1), (6, 3), (5, 1), (4, 2), (3, 1), (4, 1), (2, 4)]
FORM = [A1, A2, B1, A1]
# 마디 화음(첼로 바탕음, 비올라 두 음) 반음 — 라 단조 · 레 단조 · 파 장조 · 미 단조
CHORDS = [(-24, (-9, -5)), (-19, (-7, -4)), (-28, (-9, -4)), (-29, (-10, -5))]
PROG = [0, 1, 2, 3]


def deg_midi(d):
    o, k = divmod(d, 7)
    return ROOT + 12 * o + MINOR[k]


def violin(f, d):
    return K.bowed(f, d, band=(450, 3600), vib_rate=4.6, vib=0.010, attack=0.9, nasal=0.55)


def viola(f, d):
    return K.bowed(f, d, band=(250, 2400), vib_rate=4.4, vib=0.007, attack=1.4, nasal=0.45)


def cello(f, d):
    return K.bowed(f, d, band=(80, 1400), vib_rate=4.2, vib=0.006, attack=1.6, nasal=0.4)


def bars_of(mel):
    return sum(k for _, k in mel) // 4


def accompany(buf, t0, bars, gain=1.0):
    for b in range(bars):
        tb = t0 + b * 4 * Q
        lo, (v1, v2) = CHORDS[PROG[b % len(PROG)]]
        K.place(buf, cello(K.hz(ROOT + lo), 4 * Q + 0.8), tb, 0.20 * gain, pan=-0.3)
        for st, pan in ((v1, 0.25), (v2, 0.35)):
            K.place(buf, viola(K.hz(ROOT + st), 4 * Q + 0.8), tb, 0.08 * gain, pan=pan)


def phrase(buf, t, mel, second):
    t0 = t
    for deg, k in mel:
        d = k * Q
        K.place(buf, violin(K.hz(deg_midi(deg)), d + 0.6), t, 0.30, pan=0.05)
        if second:
            K.place(buf, violin(K.hz(deg_midi(deg - 2)), d + 0.6), t, 0.12, pan=-0.15)
        t += d
    accompany(buf, t0, bars_of(mel))
    return t


def rest_bars(buf, t, bars=2):
    for b in range(bars):
        K.place(buf, cello(K.hz(ROOT - 24), 4 * Q + 0.8), t + b * 4 * Q, 0.16, pan=-0.3)
    return t + bars * 4 * Q


def song(n, rng, mode=None):
    buf = np.zeros((n + int(12 * SR), 2), np.float32)
    t, rnd = 0.8, 0
    while t < n / SR:
        for mel in FORM:
            t = phrase(buf, t, mel, second=rnd % 2 == 1)
        t = rest_bars(buf, t)
        rnd += 1
    return K.reverb(buf[:n], rng, sec=3.2, wet=0.4)


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "느린현악.wav"
    sec = float(sys.argv[2]) if len(sys.argv) > 2 else 45
    K.write_wav(out, song(int(sec * SR), np.random.default_rng(7)))
    print(out)
