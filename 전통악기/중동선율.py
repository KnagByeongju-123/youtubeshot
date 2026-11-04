"""중동 선율 배경음 — 우드(뜯는 현)가 노래 가락을 연주하고, 되풀이 때 네이(갈대 피리)가 함께, 다르부카(손북)가 2/4 박자
사용자 결정 2026-11-04 (히타이트 편): '중동 악기 연주, 위스퀴다르 가는 길(Üsküdar'a Gider İken) 정도로' →
그 노래를 옮긴 것이 아니라, 같은 느낌(쿠르디 음계 = 미 파 솔 라 시♭ 도 레 처럼 반음이 앞에 오는 단조, 흔들리듯 걷는 2/4)으로 새로 지은 가락.
악기 소리는 공통.py 로 컴퓨터가 직접 합성 → 녹음 음원·편곡을 쓰지 않아 저작권 걱정 없음

  - song(n, rng): n 샘플 길이의 배경음 (가락 A A' B B' 20초 한 바퀴 → 쉬어 가는 마디 → 되풀이, 둘째 바퀴부터 네이)
혼자 시험: python -X utf8 전통악기/중동선율.py <결과.wav> [초]
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import 공통 as K  # noqa: E402

SR = K.SR
KURDI = [0, 1, 3, 5, 7, 8, 10]   # 쿠르디 음계 (으뜸음 D)
ROOT = 62                         # D4
BPM = 92
E8 = 60 / BPM / 2                 # 8분음표 길이(초)

# 가락: (음계 자리, 8분음표 개수). 자리 0 = 으뜸음 D4, 7 = 한 옥타브 위 D5, 음수 = 아래
A1 = [(4, 2), (5, 1), (4, 1), (3, 1), (2, 1), (3, 1), (4, 1), (2, 1), (1, 1), (2, 1), (3, 1), (1, 2), (0, 2)]
A2 = [(4, 2), (5, 1), (4, 1), (3, 1), (2, 1), (3, 1), (4, 1), (5, 1), (4, 1), (3, 1), (2, 1), (1, 1), (2, 1), (0, 2)]
B1 = [(7, 2), (6, 1), (5, 1), (6, 1), (5, 1), (4, 2), (5, 1), (4, 1), (3, 1), (4, 1), (5, 2), (4, 2)]
B2 = [(7, 1), (7, 1), (6, 1), (5, 1), (6, 1), (5, 1), (4, 1), (3, 1), (4, 1), (3, 1), (2, 1), (1, 1), (1, 2), (0, 2)]
FORM = [A1, A2, B1, B2]
# 마디마다 낮은 우드가 짚는 바탕음 (자리): A1 A2 B1 B2 각 4마디
BASS = [[0, 3, 0, 0], [0, 3, 4, 0], [3, 3, 4, 4], [3, 4, 0, 0]]


def midi(deg):
    o, k = divmod(deg, 7)
    return ROOT + 12 * o + KURDI[k]


def oud(f, d, rng, accent=False):
    return K.pluck(f, d, damp=0.993, bright=0.55 if accent else 0.45, buzz=0.12, rng=rng)


def ney(f, d, rng):
    return K.flute(f, d, breath=0.38, vib=0.008, slide=0.02, rng=rng)


def darbuka(buf, t0, bars, rng, gain=0.16):
    """2/4 손북: 둠(낮은 소리) · 테크(높은 소리) · 테크 테크 — 마디당 8분음표 4칸"""
    for b in range(bars):
        tb = t0 + b * 4 * E8
        for i, kind in enumerate(["D", ".", "T", "T"] if b % 2 == 0 else ["D", "T", ".", "T"]):
            if kind == ".":
                continue
            low = kind == "D"
            K.place(buf, K.frame_drum(0.45 if low else 0.25, low, rng), tb + i * E8, gain * (1.0 if low else 0.6), pan=-0.25)


def phrase(buf, t, mel, bass, rng, with_ney):
    t0 = t
    for deg, k in mel:
        d = k * E8
        f = K.hz(midi(deg))
        if k >= 2:                                  # 긴 음은 우드 트레몰로(잘게 되뜯기)
            for j in range(int(k * 2)):
                K.place(buf, oud(f, 0.6, rng, j == 0), t + j * E8 / 2, 0.42 if j == 0 else 0.22, pan=0.15)
        else:
            K.place(buf, oud(f, 0.9, rng, True), t, 0.45, pan=0.15)
        if with_ney:
            K.place(buf, ney(K.hz(midi(deg) - 12 + 12), d + 0.15, rng), t, 0.17, pan=-0.15)
        t += d
    for b, deg in enumerate(bass):                  # 마디 첫 박 낮은 우드
        K.place(buf, oud(K.hz(midi(deg) - 24), 1.6, rng), t0 + b * 4 * E8, 0.30, pan=-0.2)
    darbuka(buf, t0, len(bass), rng)
    return t


def rest_bars(buf, t, rng, bars=4):
    """쉬어 가는 마디: 낮은 으뜸음 우드와 다르부카만"""
    for b in range(bars):
        K.place(buf, oud(K.hz(ROOT - 24), 1.8, rng), t + b * 4 * E8, 0.28, pan=-0.2)
        if b % 2 == 1:
            K.place(buf, oud(K.hz(midi(4) - 12), 1.0, rng), t + b * 4 * E8 + 2 * E8, 0.18, pan=0.2)
    darbuka(buf, t, bars, rng, gain=0.12)
    return t + bars * 4 * E8


def song(n, rng, mode=None):
    buf = np.zeros((n + int(3 * SR), 2), np.float32)
    t, rnd = 0.6, 0
    while t < n / SR:
        for mel, bass in zip(FORM, BASS):
            t = phrase(buf, t, mel, bass, rng, with_ney=rnd % 2 == 1)
        t = rest_bars(buf, t, rng)
        rnd += 1
    return K.reverb(buf[:n], rng, sec=2.0, wet=0.3)


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "중동선율.wav"
    sec = float(sys.argv[2]) if len(sys.argv) > 2 else 45
    K.write_wav(out, song(int(sec * SR), np.random.default_rng(7)))
    print(out)
