"""파리 분위기 짧은 배경음 (직접 합성한 오리지널 '샹송풍' 왈츠 — 저작권 걱정 없음, 사용자 2026-11-25 '배경음 샹송')
   아코디언(두 리드를 살짝 어긋나게 해 떨리는 '뮈제트' 소리) 멜로디 + 쿵-짝-짝 3박자 반주(베이스 + 화음), 가을 느낌 단조(A단조↔C장조)
   사용: python 실사3D/샹송음악.py <결과.wav> [--길이 8] [--박자 150]"""
import sys, wave
import numpy as np

a = sys.argv[1:]; out = a[0]
def opt(k, d): return float(a[a.index(k) + 1]) if k in a else d
DUR, BPM = opt("--길이", 8.0), opt("--박자", 150)
SR = 44100; N = int(SR * DUR); mix = np.zeros(N); beat = 60 / BPM
f = lambda m: 440 * 2 ** ((m - 69) / 12)


def add(sig, at):
    i = int(at * SR)
    if i >= N: return
    n = min(len(sig), N - i); mix[i:i + n] += sig[:n]


def accordion(m, dur, vol, bright=1.0):
    n = int(dur * SR); t = np.arange(n) / SR
    vib = 1 + 0.004 * np.sin(2 * np.pi * 5.5 * t)
    s = 0
    for det in (0.0, 0.0045, -0.003):                                   # 뮈제트: 리드 셋을 살짝 다르게
        ph = 2 * np.pi * np.cumsum(f(m) * (1 + det) * vib) / SR
        for k in range(1, 7): s = s + np.sin(k * ph) * (bright ** (k - 1)) / k ** 1.1
    env = np.minimum(1, t / 0.04) * np.minimum(1, (dur - t) / 0.06).clip(0, 1)
    return s * env * vol / 3


def bass(m, dur, vol):
    n = int(dur * SR); t = np.arange(n) / SR
    return (np.sin(2 * np.pi * f(m) * t) + 0.3 * np.sin(4 * np.pi * f(m) * t)) * np.exp(-t / 0.35) * np.minimum(1, t / 0.01) * vol


# 화음 진행 (마디마다): Am Dm G C F Dm E Am
prog = [(45, [57, 60, 64]), (50, [57, 62, 65]), (43, [55, 59, 62]), (48, [55, 60, 64]),
        (41, [57, 60, 65]), (50, [57, 62, 65]), (40, [56, 59, 64]), (45, [57, 60, 64])]
# 멜로디 (음, 박): 직접 지은 짧은 선율
mel = [(76, 1), (74, 0.5), (72, 0.5), (71, 1), (72, 3),
       (77, 1), (76, 0.5), (74, 0.5), (72, 1), (74, 3),
       (74, 1), (72, 0.5), (71, 0.5), (69, 1), (71, 2), (67, 1),
       (72, 1.5), (71, 0.5), (69, 1), (68, 1.5), (71, 0.5), (69, 3)]
nbar = int(DUR / (3 * beat)) + 1
for b in range(nbar):
    t0 = b * 3 * beat; root, ch = prog[b % len(prog)]
    add(bass(root, beat * 0.9, 0.55), t0)                               # 쿵
    for k in (1, 2):                                                    # 짝 짝
        for m in ch: add(accordion(m, beat * 0.55, 0.10, 0.55), t0 + k * beat)
t = 0.0
for m, d in mel * 2:
    if t > DUR: break
    add(accordion(m, d * beat * 0.95, 0.30, 0.7), t); t += d * beat
fade = int(1.2 * SR); mix[-fade:] *= np.linspace(1, 0, fade); mix[:int(0.05 * SR)] *= np.linspace(0, 1, int(0.05 * SR))
# 작은 방 울림
rev = np.zeros_like(mix)
for dl, g in ((0.031, 0.25), (0.053, 0.18), (0.089, 0.12), (0.137, 0.08)):
    k = int(dl * SR); rev[k:] += mix[:-k] * g
mix = mix + rev; mix /= np.abs(mix).max() / 0.85
st = np.stack([mix, np.roll(mix, int(0.009 * SR))], 1)
with wave.open(out, "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((st * 32767).astype(np.int16).tobytes())
print("→", out, f"({DUR}s, {BPM} BPM 왈츠)")
