"""한국 선율 배경음 — 가야금이 노래 가락을 뜯고(긴 음은 농현으로 줄을 흔듦), 되풀이 때 해금이 함께, 장구가 굿거리(12/8) 장단
사용자 결정 2026-11-04 (태안 마도 편): 배경음은 선율이 있는 연주로 (CLAUDE.md 4장) → 한국 편 가락 배경음.
평조(라 시 레 미 파# 처럼 반음 없는 다섯 음)로 새로 지은 가락 — 민요·국악곡을 옮긴 것이 아님.
악기 소리는 공통.py 로 컴퓨터가 직접 합성 → 녹음 음원·편곡을 쓰지 않아 저작권 걱정 없음

  - song(n, rng): n 샘플 길이 (가락 A A' B A 한 바퀴 약 43초 → 쉬어 가는 장단 → 되풀이, 둘째 바퀴부터 해금)
혼자 시험: python -X utf8 전통악기/한국선율.py <결과.wav> [초]
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import 공통 as K  # noqa: E402

SR = K.SR
PYEONG = [0, 2, 5, 7, 9]      # 평조 다섯 음 (으뜸음 E)
ROOT = 64                     # E4
E8 = 60 / 66 / 3              # 굿거리: 점4분음표 66 → 8분음표 길이(초)

# 가락: (음 자리, 8분음표 개수) — 마디마다 12칸(12/8). 자리 0 = 으뜸음, 5 = 한 옥타브 위, 음수 = 아래
A1 = [(5, 3), (4, 2), (3, 1), (2, 3), (3, 3), (4, 2), (3, 1), (2, 2), (1, 1), (2, 6),
      (2, 3), (3, 2), (4, 1), (5, 3), (4, 3), (3, 2), (2, 1), (1, 3), (0, 6)]
A2 = [(5, 3), (4, 2), (3, 1), (2, 3), (3, 3), (4, 2), (3, 1), (2, 2), (1, 1), (2, 6),
      (5, 3), (6, 2), (5, 1), (4, 3), (3, 3), (2, 2), (3, 1), (1, 3), (2, 6)]
B1 = [(7, 6), (6, 3), (5, 3), (6, 2), (5, 1), (4, 3), (5, 6),
      (4, 3), (3, 2), (2, 1), (3, 3), (4, 3), (3, 2), (2, 1), (1, 3), (2, 6)]
FORM = [A1, A2, B1, A1]
BASS = [[0, -2, 0, 0], [0, -2, 0, -3], [2, 0, -2, -3], [0, -2, 0, 0]]   # 마디 첫 박 낮은 가야금


def deg_midi(d):
    o, k = divmod(d, 5)
    return ROOT + 12 * o + PYEONG[k]


def gayageum(f, d, rng, nong=False):
    return K.pluck(f, d, damp=0.994, bright=0.35, bend=0.03 if nong else 0.0, vib=0.014 if nong else 0.003, rng=rng)


def haegeum(f, d):
    return K.bowed(f, d, band=(700, 3600), vib_rate=4.5, vib=0.013, nasal=1.0, attack=0.25)


def janggu(buf, t0, bars, rng, gain=0.13):
    """굿거리 장단(12/8) 줄인 것: 덩(낮은+높은) · 기덕 · 쿵 · 덕"""
    hits = [(0, "덩"), (3, "기"), (4, "덕"), (6, "쿵"), (9, "덕"), (10, "기")]
    for b in range(bars):
        tb = t0 + b * 12 * E8
        for i, kind in hits:
            t = tb + i * E8
            if kind in ("덩", "쿵"):
                K.place(buf, K.frame_drum(0.5, True, rng), t, gain, pan=-0.2)
            if kind in ("덩", "덕", "기"):
                K.place(buf, K.frame_drum(0.22, False, rng), t, gain * (0.7 if kind != "기" else 0.4), pan=0.2)


def phrase(buf, t, mel, bass, rng, with_haegeum):
    t0 = t
    for deg, k in mel:
        d = k * E8
        f = K.hz(deg_midi(deg))
        K.place(buf, gayageum(f, max(1.2, d + 0.6), rng, nong=k >= 3), t, 0.45, pan=0.15)
        if with_haegeum and k >= 2:
            K.place(buf, haegeum(f, d + 0.2), t, 0.12, pan=-0.15)
        t += d
    for b, deg in enumerate(bass):
        K.place(buf, gayageum(K.hz(deg_midi(deg) - 12), 2.4, rng), t0 + b * 12 * E8, 0.28, pan=-0.2)
    janggu(buf, t0, len(bass), rng)
    return t


def rest_bars(buf, t, rng, bars=2):
    for b in range(bars):
        K.place(buf, gayageum(K.hz(ROOT - 12), 2.6, rng, nong=True), t + b * 12 * E8, 0.26, pan=-0.2)
        K.place(buf, gayageum(K.hz(deg_midi(2) - 12), 1.6, rng), t + b * 12 * E8 + 6 * E8, 0.16, pan=0.2)
    janggu(buf, t, bars, rng, gain=0.1)
    return t + bars * 12 * E8


def song(n, rng, mode=None):
    buf = np.zeros((n + int(4 * SR), 2), np.float32)
    t, rnd = 0.6, 0
    while t < n / SR:
        for mel, bass in zip(FORM, BASS):
            t = phrase(buf, t, mel, bass, rng, with_haegeum=rnd % 2 == 1)
        t = rest_bars(buf, t, rng)
        rnd += 1
    return K.reverb(buf[:n], rng, sec=2.4, wet=0.33)


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "한국선율.wav"
    sec = float(sys.argv[2]) if len(sys.argv) > 2 else 45
    K.write_wav(out, song(int(sec * SR), np.random.default_rng(7)))
    print(out)
