"""잔잔한 피아노 연주곡 (직접 합성한 오리지널 — 저작권 걱정 없음, 사용자 결정 2026-11-25: 교육 영상 배경음 '잔잔한 피아노 연주곡')
   - 왼손: 화음을 펼쳐 치는 8분음표 반주(베이스 + 5도 + 10도), 오른손: 화음 음을 따라 걷는 느린 멜로디(마디 끝은 길게)
   - 구성: A(멜로디) → A'(한 옥타브 위 변주) → 쉼(반주만, 조용히) → B(다른 화음 진행) … 길이만큼 이어 감, 4마디마다 셈여림이 부풀었다 가라앉음
   - 소리: 배음이 조금씩 어긋난 피아노 줄(높은 배음이 먼저 사라짐) + 해머 소리 + 페달로 길게 울림 + 공간 울림(잔향 2.2초)
   사용: python 교육/피아노연주곡.py <결과.wav> [--길이 600] [--박자 66] [--씨앗 7] [--조 0(C)~11]"""
import sys
import wave

import numpy as np
from scipy.signal import fftconvolve

a = sys.argv[1:]; out = a[0]
def opt(k, d): return float(a[a.index(k) + 1]) if k in a else d
DUR, BPM, SEED, KEY = opt("--길이", 600.0), opt("--박자", 66.0), int(opt("--씨앗", 7)), int(opt("--조", 0))
SR = 44100; rng = np.random.default_rng(SEED)
N = int(SR * (DUR + 4)); L = np.zeros(N, np.float32); R = np.zeros(N, np.float32)
beat = 60.0 / BPM; bar = 4 * beat
hz = lambda m: 440.0 * 2 ** ((m - 69) / 12)

cache = {}
def note(m, vel=0.6, dur=None):
    """피아노 한 음: 배음이 조금씩 높아지는(줄의 굳기) 소리, 높은 배음이 먼저 사라짐, 낮은 음일수록 오래 울림"""
    key = (m, round(vel, 2))
    if key in cache: return cache[key]
    f0 = hz(m); ring = 2.2 + 2.8 * np.clip((72 - m) / 36, 0, 1)          # 울림 길이(초)
    t = np.arange(int(SR * (ring + 0.3))) / SR
    B = 0.00035; s = np.zeros_like(t)
    for n in range(1, 9):
        fn = n * f0 * np.sqrt(1 + B * n * n)
        if fn > 9000: break
        amp = (1.0 / n ** 1.25) * (0.55 + 0.45 * vel) ** (n - 1)
        dec = ring / (1 + 0.55 * (n - 1))
        s += amp * np.sin(2 * np.pi * fn * t + rng.uniform(0, 6.28)) * np.exp(-t / dec)
    s += 0.35 * np.sin(2 * np.pi * f0 * 1.003 * t) * np.exp(-t / ring)   # 줄 두 가닥이 살짝 어긋나 맥놀이
    ham = rng.standard_normal(int(SR * 0.012)) * np.exp(-np.arange(int(SR * 0.012)) / (SR * 0.002)) * 0.08
    s[:len(ham)] += ham
    s *= np.minimum(1, t / 0.004) * np.minimum(1, (t[-1] - t) / 0.25)
    s = (s / np.max(np.abs(s)) * vel).astype(np.float32)
    cache[key] = s; return s

def put(m, t0, vel):
    s = note(m, vel); i = int(t0 * SR); j = min(N, i + len(s))
    if i >= N: return
    p = np.clip((m - 60) / 30, -0.6, 0.6)                          # 낮은 음 왼쪽, 높은 음 오른쪽 조금
    L[i:j] += s[:j - i] * (0.5 - 0.35 * p); R[i:j] += s[:j - i] * (0.5 + 0.35 * p)

# 화음 진행 (근음, 장/단) — 조 C 기준 반음
PROG_A = [(0, 'M'), (7, 'M'), (9, 'm'), (4, 'm'), (5, 'M'), (0, 'M'), (2, 'm'), (7, 'M')]
PROG_B = [(5, 'M'), (7, 'M'), (4, 'm'), (9, 'm'), (2, 'm'), (7, 'M'), (0, 'M'), (0, 'M')]
SCALE = [0, 2, 4, 5, 7, 9, 11]
def chord_tones(r, q): return [r, r + (4 if q == 'M' else 3), r + 7]

sections = ['A', "A'", 'rest', 'B', 'A', 'rest', "B'", "A'"]
t = 1.0; si = 0; prev = 72 + KEY
while t < DUR - 2:
    sec = sections[si % len(sections)]; si += 1
    prog = PROG_B if sec.startswith('B') else PROG_A
    up = 12 if sec.endswith("'") else 0
    for b, (r, q) in enumerate(prog):
        if t >= DUR - 2: break
        bt = t + b * bar
        swell = 0.75 + 0.25 * np.sin(np.pi * ((b % 4) + 0.5) / 4)       # 4마디마다 부풀었다 가라앉음
        root = 48 + KEY + r; ct = chord_tones(r, q)
        # 왼손: 베이스(두 박 울림) + 펼친 화음 8분음표
        put(root - 12 if r > 5 else root, bt, 0.42 * swell)
        arp = [root, root + 7, root + 12 + (ct[1] - r), root + 7, root + 12, root + 7, root + 12 + (ct[1] - r), root + 19]
        for k, m in enumerate(arp):
            put(m, bt + k * beat / 2 + rng.uniform(-0.008, 0.008), (0.22 if k % 2 else 0.28) * swell)
        if sec == 'rest': continue
        # 오른손: 화음 음을 중심으로 한 걸음씩 걷는 멜로디 (2분·4분음표), 마디 끝은 화음 음
        pos = 0.0
        rhythm = [2, 1, 1] if rng.random() < 0.5 else [1, 1, 2]
        if b % 4 == 3: rhythm = [3, 1] if rng.random() < 0.5 else [4]
        for dur in rhythm:
            cands = [72 + KEY + up + s + o for s in SCALE for o in (-12, 0, 12)]
            cands = [c for c in cands if 64 + up <= c <= 84 + up]
            chordish = [c for c in cands if (c - KEY) % 12 in [x % 12 for x in ct]]
            pool = chordish if (pos == 0 or dur >= 2) else cands
            m = min(pool, key=lambda c: abs(c - prev) + rng.uniform(0, 3.5))
            put(m, bt + pos * beat + rng.uniform(-0.01, 0.01), (0.5 + 0.1 * rng.random()) * swell)
            prev = m; pos += dur
    t += len(prog) * bar

# 공간 울림(잔향): 지수로 줄어드는 소음 응답, 왼·오 다르게
irn = int(SR * 2.2); it = np.arange(irn) / SR
irL = rng.standard_normal(irn) * np.exp(-it / 0.55); irR = rng.standard_normal(irn) * np.exp(-it / 0.55)
irL[:int(SR * 0.012)] = 0; irR[:int(SR * 0.017)] = 0
wetL = fftconvolve(L, irL)[:N]; wetR = fftconvolve(R, irR)[:N]
wetL /= np.max(np.abs(wetL)) + 1e-9; wetR /= np.max(np.abs(wetR)) + 1e-9
dry = max(np.max(np.abs(L)), np.max(np.abs(R))) + 1e-9
mixL = L / dry * 0.8 + wetL * 0.28; mixR = R / dry * 0.8 + wetR * 0.28
fade = np.ones(N); fi = int(SR * 2); fade[:fi] = np.linspace(0, 1, fi); fade[-int(SR * 4):] = np.linspace(1, 0, int(SR * 4))
st = np.stack([mixL * fade, mixR * fade], 1)[:int(SR * DUR)]
st = st / (np.max(np.abs(st)) + 1e-9) * 0.89
with wave.open(out, 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((st * 32767).astype(np.int16).tobytes())
print('피아노 연주곡:', out, f'{DUR:.0f}초, 박자 {BPM:.0f}, 씨앗 {SEED}')
