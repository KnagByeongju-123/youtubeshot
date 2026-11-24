"""춤 영상용 짧은 배경음 만들기 (직접 합성한 오리지널 비트 — 저작권 걱정 없음)
   킥(1·2·3·4박) + 스네어·손뼉(2·4박) + 하이햇(8분) + 베이스·화음(4박마다 바뀜), 박자는 춤과 같은 BPM.
   첫 박이 --시작 초에 오게 해 춤 박자(야외_오르빗.py --춤, 춤 시작 0.4초)와 맞춤
   사용: python 실사3D/춤음악.py <결과.wav> [--박자 112] [--길이 9.5] [--시작 0.4]"""
import sys, wave
import numpy as np

a = sys.argv[1:]
out = a[0]
def opt(k, d): return float(a[a.index(k) + 1]) if k in a else d
BPM, DUR, T0 = opt("--박자", 112), opt("--길이", 9.5), opt("--시작", 0.4)
SR = 44100; N = int(SR * DUR); t = np.arange(N) / SR; mix = np.zeros(N)
beat = 60.0 / BPM
rng = np.random.default_rng(7)
def add(sig, at):
    i = int(at * SR)
    if i >= N or i < 0: return
    n = min(len(sig), N - i); mix[i:i + n] += sig[:n]
def env(n, a_=0.002, d=0.2):
    x = np.arange(n) / SR; return np.minimum(1, x / a_) * np.exp(-x / d)
L = int(0.5 * SR); x = np.arange(L) / SR
kick = np.sin(2 * np.pi * (50 + 90 * np.exp(-x / 0.03)) * x) * env(L, 0.001, 0.16) * 0.9
snare = (rng.standard_normal(L) * 0.5 + np.sin(2 * np.pi * 190 * x) * 0.4) * env(L, 0.001, 0.09) * 0.45
clap = rng.standard_normal(L) * env(L, 0.001, 0.05) * 0.35
hat = rng.standard_normal(int(0.08 * SR)); hat = np.diff(np.r_[0, hat]) * env(len(hat), 0.0005, 0.02) * 0.18
chords = [[57, 60, 64], [53, 57, 60], [55, 59, 62], [52, 55, 59]]        # Am F G Em
bassn = [45, 41, 43, 40]
f = lambda m: 440 * 2 ** ((m - 69) / 12)
nb = int((DUR - T0) / beat) + 1
for b in range(nb):
    tb = T0 + b * beat
    add(kick, tb)
    if b % 2 == 1: add(snare, tb); add(clap, tb + 0.005)
    add(hat, tb + beat / 2); add(hat * 0.6, tb)
    bar = (b // 4) % 4
    # 베이스: 8분 음표로 통통
    for h in (0, 0.5):
        n = int(beat * 0.45 * SR); xx = np.arange(n) / SR
        add(np.sign(np.sin(2 * np.pi * f(bassn[bar]) * xx)) * 0.12 * env(n, 0.003, 0.12), tb + h * beat)
    if b % 4 == 0:                                                          # 화음 (부드러운 톱니파 + 저역 필터 대신 배음 줄임)
        n = int(beat * 4 * SR); xx = np.arange(n) / SR; c = np.zeros(n)
        for m in chords[bar]:
            for k in range(1, 5): c += np.sin(2 * np.pi * f(m + 12) * k * xx) / (k * k)
        add(c * 0.05 * np.minimum(1, xx / 0.05) * np.exp(-xx / 2.0), tb)
mix[:int(T0 * SR)] *= np.linspace(0, 1, int(T0 * SR)) if T0 > 0 else 1
fade = int(0.8 * SR); mix[-fade:] *= np.linspace(1, 0, fade)
mix /= max(1e-9, np.abs(mix).max()) / 0.85
st = np.stack([mix, np.roll(mix, int(0.012 * SR)) * 0.9 + mix * 0.1], 1)   # 살짝 넓게
with wave.open(out, "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((st * 32767).astype(np.int16).tobytes())
print(f"→ {out}  ({DUR}s, {BPM} BPM, 첫 박 {T0}s)")
