"""조지아풍 춤 배경음(직접 합성, 저작권 걱정 없음): 6/8 박자 돌리(북) + 판두리(뜯는 3줄 현) 아르페지오 + 낮은 드론
   사용: python 실사3D/조지아음악.py <출력.wav> [--초 10] [--빠르기 120]  (빠르기 = 6/8 의 점4분음표 기준 한 마디 2박)"""
import sys, wave
import numpy as np

a = sys.argv[1:]; out = a[0]
SEC = float(a[a.index("--초") + 1]) if "--초" in a else 10.0
BPM = float(a[a.index("--빠르기") + 1]) if "--빠르기" in a else 120.0
SR = 44100; n = int(SR * SEC); y = np.zeros(n)
e8 = 60.0 / BPM / 3                                   # 8분음표 길이 (점4분 = 3개)
def put(sig, t):
    i = int(t * SR); j = min(n, i + len(sig))
    if i < n: y[i:j] += sig[:j - i]
def drum(f0, dec, amp):
    t = np.arange(int(SR * 0.5)) / SR
    return amp * np.sin(2 * np.pi * (f0 * t + 30 * (1 - np.exp(-t * 30)) / 30)) * np.exp(-t * dec) + amp * 0.3 * np.random.randn(len(t)) * np.exp(-t * 60)
def pluck(f, amp, dur=0.9):
    N = int(SR / f); buf = np.random.uniform(-1, 1, N); L = int(SR * dur); o = np.zeros(L)
    for k in range(L): o[k] = buf[k % N]; buf[k % N] = 0.5 * (buf[k % N] + buf[(k + 1) % N]) * 0.996
    return amp * o
A3 = 220.0; scale = [0, 2, 3, 5, 7, 9, 10, 12]      # 도리안
def note(d): return A3 * 2 ** (scale[d % 8] / 12 + (d // 8))
mel = [0, 2, 4, 4, 3, 2, 1, 2, 3, 2, 1, 0, 4, 5, 6, 5, 4, 2, 3, 2, 1, 0, 0, 0]
t = 0.0; k = 0
while t < SEC:
    pos = k % 6
    put(drum(90, 9, 0.55) if pos == 0 else drum(180, 18, 0.30) if pos == 3 else drum(320, 30, 0.12), t)
    put(pluck(note(mel[k % len(mel)] + 7), 0.22), t)
    if pos in (0, 3): put(pluck(note(mel[k % len(mel)]) , 0.12, 1.4), t)
    t += e8; k += 1
tt = np.arange(n) / SR
y += 0.05 * np.sin(2 * np.pi * A3 / 2 * tt) * (1 - np.exp(-tt * 2))   # 낮은 드론
fade = np.minimum(1, np.minimum(tt / 0.4, (SEC - tt) / 1.2)); y *= fade
y = y / (np.abs(y).max() + 1e-9) * 0.8
with wave.open(out, "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((y * 32767).astype(np.int16).tobytes())
print("→", out, SEC, "초")
