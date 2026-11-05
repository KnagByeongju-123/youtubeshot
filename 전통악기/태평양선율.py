"""태평양 선율 배경음 — 폴리네시아 섬 느낌: 코피리(입이 아닌 코로 부는 대나무 피리, 하와이 '오헤 하노 이후') 같은 부드러운 피리 가락,
줄을 느슨하게 맨 기타처럼 뜯는 현의 화음, 큰북 '파후'와 박 북 '이푸'가 아주 작게 받침.
2026-11-05 (이스터섬→하와이 항해 편): 배경음은 선율이 있는 연주로 (CLAUDE.md 4장) → 태평양·폴리네시아 편 가락 배경음.
솔 장조 오음계로 새로 지은 가락 — 전통 노래·유명 곡을 옮긴 것이 아님. 넓은 바다를 천천히 건너는 느낌, 느린 템포.
악기 소리는 공통.py 로 컴퓨터가 직접 합성 → 녹음 음원·편곡을 쓰지 않아 저작권 걱정 없음

  - song(n, rng): n 샘플 길이 (가락 A A' B A 한 바퀴 → 현과 북만 남는 쉼 → 되풀이, 둘째 바퀴부터 뜯는 현이 가락을 함께)
혼자 시험: python -X utf8 전통악기/태평양선율.py <결과.wav> [초]
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import 공통 as K  # noqa: E402

SR = K.SR
PENTA = [0, 2, 4, 7, 9]       # 솔 장조 오음계 (솔 라 시 레 미)
ROOT = 67                     # G4
Q = 60 / 56                   # 4분음표 56 (느리게)

# 가락: (음 자리, 4분음표 개수) — 마디마다 4박. 자리 0 = 솔, 5 = 한 옥타브 위 솔
A1 = [(2, 2), (3, 1), (4, 1), (3, 3), (2, 1), (1, 2), (2, 1), (1, 1), (0, 4)]
A2 = [(2, 2), (3, 1), (4, 1), (5, 3), (4, 1), (3, 2), (2, 1), (1, 1), (2, 4)]
B1 = [(5, 2), (4, 1), (3, 1), (4, 3), (3, 1), (2, 2), (1, 1), (2, 1), (3, 4)]
FORM = [A1, A2, B1, A1]
CHORD = {0: [-12, -5, 0, 4], 1: [-7, 0, 5, 9], 2: [-10, -3, 2, 5], 3: [-8, -1, 4, 7]}   # 솔·도·레·미 단조 (반음)
PROG = [0, 1, 0, 2, 3, 1, 2, 0]


def deg_midi(d):
    o, k = divmod(d, 5)
    return ROOT + 12 * o + PENTA[k]


def nose_flute(f, d, rng):
    """코피리: 숨소리가 많고 부드러운 피리, 긴 음은 천천히 떨림"""
    return K.flute(f, d, breath=0.22, vib=0.006, slide=0.02, rng=rng, vib_rate=4.2)


def slack_string(f, d, rng):
    """줄을 느슨하게 맨 기타처럼 뜯는 현 (따뜻하고 길게 울림)"""
    return K.pluck(f, max(1.4, d + 0.8), damp=0.995, bright=0.35, rng=rng)


def bars_of(mel):
    return sum(k for _, k in mel) // 4


def accompany(buf, t0, bars, rng, gain=1.0):
    for b in range(bars):
        tb = t0 + b * 4 * Q
        ch = CHORD[PROG[b % len(PROG)]]
        for j, st in enumerate(ch):          # 화음을 한 줄씩 천천히 뜯음 (파도처럼)
            K.place(buf, slack_string(K.hz(ROOT - 12 + st), 2.4, rng), tb + j * Q * 0.5, 0.08 * gain, pan=-0.25)
        for j, st in enumerate(ch[1:]):
            K.place(buf, slack_string(K.hz(ROOT - 12 + st), 1.6, rng), tb + 2 * Q + j * Q * 0.5, 0.05 * gain, pan=-0.2)
        if b % 2 == 0:                       # 큰북 파후: 두 마디에 한 번, 아주 작게
            K.place(buf, K.big_drum(62, 2.0, rng), tb, 0.06 * gain, pan=0.0)
        K.place(buf, K.frame_drum(0.5, False, rng), tb + 2 * Q, 0.025 * gain, pan=0.3)   # 박 북 이푸: 셋째 박에 살짝


def phrase(buf, t, mel, rng, second):
    t0 = t
    for deg, k in mel:
        d = k * Q
        f = K.hz(deg_midi(deg))
        K.place(buf, nose_flute(f, d + 0.25, rng), t, 0.30, pan=0.12)
        if second:
            K.place(buf, slack_string(f / 2, d, rng), t, 0.12, pan=-0.1)
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
    return K.reverb(buf[:n], rng, sec=2.8, wet=0.38)


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "태평양선율.wav"
    sec = float(sys.argv[2]) if len(sys.argv) > 2 else 45
    K.write_wav(out, song(int(sec * SR), np.random.default_rng(7)))
    print(out)
