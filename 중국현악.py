"""중국 현악 배경음 — 고쟁(뜯는 현) + 얼후(활로 켜는 현)를 컴퓨터로 직접 합성 (녹음 음원을 쓰지 않아 저작권 걱정 없음)
역사 채널(삼국지·중국 배경) 다큐용. 오음계(궁조: 도 레 미 솔 라)

  - guzheng(freq, dur): 고쟁 한 음 (Karplus-Strong 현 + 누르는 음(살짝 올렸다 내림))
  - erhu(freq, dur): 얼후 한 음 (톱니파 + 떨림 + 몸통 울림)
  - interlude(rng, sec): 나레이션 사이에 넣을 고쟁 한 소절 (훑어 내림 + 짧은 선율)
  - bed(n, rng): 나레이션 아래 깔리는 잔잔한 배경 (드문 고쟁 + 긴 얼후)
혼자 시험: python -X utf8 중국현악.py <결과.wav> [초]
"""
import sys

import numpy as np

SR = 44100
PENTA = [0, 2, 4, 7, 9]          # 궁조 오음계 (도 레 미 솔 라)
ROOT = 50                        # D3 (MIDI)


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def scale_notes(lo=ROOT, hi=ROOT + 31):
    return [o * 12 + p + lo for o in range(4) for p in PENTA if lo <= o * 12 + p + lo <= hi]


def guzheng(freq, dur=2.2, bend=0.0, rng=None):
    """고쟁 한 음: 지연선 현(Karplus-Strong) — 밝은 첫소리, 천천히 사라짐. bend>0 이면 뜯은 뒤 살짝 눌러 올렸다 내림"""
    from scipy.signal import lfilter
    rng = rng or np.random.default_rng()
    n = int(dur * SR)
    N = max(2, int(SR / freq))
    exc = np.zeros(n, np.float32)
    burst = rng.uniform(-1, 1, N).astype(np.float32)
    burst = np.convolve(burst, [0.5, 0.5], "same")                 # 손톱(가조각) 소리: 조금만 부드럽게
    exc[:N] = burst
    damp = 0.996 if freq < 300 else 0.993
    a = np.zeros(N + 2, np.float32)
    a[0], a[N], a[N + 1] = 1.0, -0.5 * damp, -0.5 * damp
    y = lfilter([1.0], a, exc).astype(np.float32)
    if bend:                                                       # 누르는 음: 음높이를 시간에 따라 살짝 바꿈 (다시 읽기)
        t = np.arange(n) / SR
        ratio = 1 + bend * np.clip((t - 0.25) / 0.25, 0, 1) * np.clip((1.2 - t) / 0.4, 0, 1)
        pos = np.cumsum(ratio)
        pos = pos / pos[-1] * (n - 1)
        y = np.interp(pos, np.arange(n), y).astype(np.float32)
    env = np.minimum(1, np.arange(n) / (0.002 * SR))
    return (y * env / (np.abs(y).max() + 1e-6)).astype(np.float32)


def erhu(freq, dur=3.0):
    """얼후 한 음: 톱니파에 떨림(비브라토) + 몸통 울림(띠 필터) + 천천히 켜고 끝냄"""
    from scipy.signal import butter, lfilter
    n = int(dur * SR)
    t = np.arange(n) / SR
    vib = 1 + 0.006 * np.sin(2 * np.pi * 5.3 * t) * np.clip(t / 0.6, 0, 1)
    ph = np.cumsum(2 * np.pi * freq * vib / SR)
    saw = (2 * ((ph / (2 * np.pi)) % 1) - 1).astype(np.float32)
    b, a = butter(2, [600 / (SR / 2), 3200 / (SR / 2)], "band")
    y = lfilter(b, a, saw) * 0.8 + lfilter(*butter(1, 900 / (SR / 2)), saw) * 0.35
    env = np.clip(t / 0.35, 0, 1) * np.clip((dur - t) / 0.6, 0, 1)
    y = y * env
    return (y / (np.abs(y).max() + 1e-6)).astype(np.float32)


def _place(buf, snd, t0, gain, pan=0.0):
    i0 = int(t0 * SR)
    if i0 >= len(buf):
        return
    seg = snd[: len(buf) - i0] * gain
    buf[i0:i0 + len(seg), 0] += seg * (1 - max(0, pan))
    buf[i0:i0 + len(seg), 1] += seg * (1 + min(0, pan))


def _reverb(x, rng, sec=2.2, wet=0.35):
    from scipy.signal import fftconvolve
    n = int(sec * SR)
    ir = rng.standard_normal((n, 2)).astype(np.float32) * np.exp(-np.arange(n) / (0.35 * SR))[:, None]
    ir[: int(0.02 * SR)] = 0
    out = np.stack([fftconvolve(x[:, c], ir[:, c])[: len(x)] for c in range(2)], 1)
    out /= np.abs(out).max() + 1e-6
    return (x * (1 - wet) + out * wet * np.abs(x).max()).astype(np.float32)


def interlude(rng, sec=4.0):
    """나레이션 사이 고쟁 한 소절: 위에서 아래로 훑기(글리산도) → 짧은 선율 3~5음 → 마지막 음은 누르는 음으로 길게"""
    buf = np.zeros((int((sec + 2.5) * SR), 2), np.float32)
    notes = scale_notes(ROOT + 12, ROOT + 36)
    t = 0.0
    for m in reversed(notes[-7:]):                                 # 훑어 내림
        _place(buf, guzheng(hz(m), 1.6, rng=rng), t, 0.32, pan=0.3)
        t += 0.055
    t += 0.35
    mel = scale_notes(ROOT + 7, ROOT + 24)
    k = int(rng.integers(2, len(mel) - 2))
    steps = int(rng.integers(3, 6))
    for j in range(steps):
        k = int(np.clip(k + rng.choice([-2, -1, 1, 2]), 0, len(mel) - 1))
        last = j == steps - 1
        _place(buf, guzheng(hz(mel[k]), 2.6 if last else 1.8, bend=0.03 if last else 0.0, rng=rng), t, 0.7 if last else 0.55)
        t += 0.42 if not last else 0
    return _reverb(buf, rng)


def bed(n, rng):
    """나레이션 아래 깔리는 배경: 긴 얼후 음(가끔) + 드문 고쟁 음 + 낮은 고쟁 저음"""
    buf = np.zeros((n, 2), np.float32)
    low = scale_notes(ROOT - 12, ROOT)
    mid = scale_notes(ROOT + 7, ROOT + 26)
    t = 0.5
    while t < n / SR - 2:
        _place(buf, guzheng(hz(rng.choice(low)), 3.0, rng=rng), t, 0.35, pan=-0.2)
        for _ in range(int(rng.integers(1, 4))):
            _place(buf, guzheng(hz(rng.choice(mid)), 2.0, rng=rng), t + rng.uniform(0.6, 3.2), 0.28, pan=0.25)
        if rng.random() < 0.45:
            _place(buf, erhu(hz(rng.choice(mid)), rng.uniform(3, 5)), t + rng.uniform(0.5, 2), 0.16, pan=-0.1)
        t += rng.uniform(3.5, 5.5)
    return _reverb(buf, rng, wet=0.4)


def main(a):
    if not a:
        print(__doc__)
        return 2
    import wave
    sec = float(a[1]) if len(a) > 1 else 20
    rng = np.random.default_rng(7)
    out = np.concatenate([interlude(rng), bed(int(sec * SR), rng)])
    out = np.clip(out / (np.abs(out).max() + 1e-6) * 0.8, -1, 1)
    with wave.open(a[0], "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((out * 32767).astype(np.int16).tobytes())
    print("OK", a[0])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
