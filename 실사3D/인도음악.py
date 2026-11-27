"""인도풍 춤 배경음(직접 합성, 저작권 걱정 없음): 탄푸라 드론(Sa·Pa) + 타블라 느낌 북(다·딘·나, 8박) + 시타르 느낌 뜯는 현 선율(라가 음계)
   사용: python 실사3D/인도음악.py <출력.wav> [--초 14] [--빠르기 100]  (사용자 2026-11-27 인도춤 시험)"""
import sys, wave
import numpy as np

a = sys.argv[1:]; out = a[0]
SEC = float(a[a.index("--초") + 1]) if "--초" in a else 14.0
BPM = float(a[a.index("--빠르기") + 1]) if "--빠르기" in a else 100.0
SR = 44100; n = int(SR * SEC); y = np.zeros(n); rng = np.random.default_rng(7)
beat = 60.0 / BPM
def put(sig, t):
    i = int(t * SR); j = min(n, i + len(sig))
    if i < n: y[i:j] += sig[:j - i]
def tabla(kind, amp):
    t = np.arange(int(SR * 0.6)) / SR
    if kind == "다":      # 낮은 바얀 + 높은 다얀
        s = 0.9 * np.sin(2 * np.pi * (70 * t + 40 * (1 - np.exp(-t * 8)) / 8)) * np.exp(-t * 6) + 0.5 * np.sin(2 * np.pi * 420 * t) * np.exp(-t * 18)
    elif kind == "딘":
        s = 0.7 * np.sin(2 * np.pi * 440 * t) * np.exp(-t * 10) + 0.3 * np.sin(2 * np.pi * 880 * t) * np.exp(-t * 20)
    else:                 # 나
        s = 0.6 * np.sin(2 * np.pi * 520 * t) * np.exp(-t * 25) + 0.2 * rng.standard_normal(len(t)) * np.exp(-t * 80)
    return amp * s
def pluck(f, amp, dur=1.2):
    N = int(SR / f); buf = rng.uniform(-1, 1, N); L = int(SR * dur); o = np.zeros(L)
    for k in range(L): o[k] = buf[k % N]; buf[k % N] = 0.5 * (buf[k % N] + buf[(k + 1) % N]) * 0.997
    sym = np.sin(2 * np.pi * f * 2.0 * np.arange(L) / SR) * np.exp(-np.arange(L) / SR * 3) * 0.15   # 시타르의 반짝이는 공명
    return amp * (o + sym)
SA = 261.63                                         # 도(Sa)
scale = [0, 1, 4, 5, 7, 8, 11, 12]                  # 바이라브 라가 느낌
def note(d): return SA * 2 ** (scale[d % 8] / 12 + (d // 8))
# 드론
t = np.arange(n) / SR
dr = sum(np.sin(2 * np.pi * f * t) * w for f, w in ((SA / 2, 0.5), (SA * 0.75, 0.35), (SA, 0.3), (SA * 1.5, 0.15)))
y += 0.07 * dr * (1 + 0.15 * np.sin(2 * np.pi * 0.25 * t))
# 타블라 8박 (다 딘 딘 다 | 다 딘 나 나)
pat = ["다", "딘", "딘", "다", "다", "딘", "나", "나"]
k = 0; tt = 0.0
while tt < SEC:
    put(tabla(pat[k % 8], 0.35 if pat[k % 8] == "다" else 0.25), tt)
    if k % 2 == 1: put(tabla("나", 0.12), tt + beat / 2)
    k += 1; tt += beat
# 선율 (2박마다, 위아래로 굽이침)
mel = [0, 2, 3, 4, 3, 2, 1, 0, 4, 5, 6, 7, 6, 4, 3, 2]
tt = beat * 2; k = 0
while tt < SEC - 1:
    put(pluck(note(mel[k % len(mel)] + 8), 0.22), tt); k += 1; tt += beat * (1 if k % 4 else 2)
y = y / (np.abs(y).max() + 1e-9) * 0.8
fade = int(SR * 0.6); y[-fade:] *= np.linspace(1, 0, fade); y[:int(SR * 0.3)] *= np.linspace(0, 1, int(SR * 0.3))
with wave.open(out, "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((y * 32767).astype(np.int16).tobytes())
print("→", out, SEC, "초")
