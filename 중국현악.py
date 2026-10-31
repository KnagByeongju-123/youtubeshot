"""중국 현악 배경음 — 고쟁(뜯는 현) + 얼후(활로 켜는 현)를 컴퓨터로 직접 합성 (녹음 음원을 쓰지 않아 저작권 걱정 없음)
역사 채널(삼국지·중국 배경) 다큐용. 중국 오음계의 다섯 갈래(MODES: 궁조·상조·각조·치조·우조) 중 하나로 연주
(같은 다섯 음이라도 어느 음을 으뜸음으로 삼느냐에 따라 밝음·차분·신비·활기·슬픔으로 느낌이 달라짐)

  - guzheng(freq, dur): 고쟁 한 음 (Karplus-Strong 현 + 누르는 음(살짝 올렸다 내림))
  - erhu(freq, dur): 얼후 한 음 (톱니파 + 떨림 + 몸통 울림)
  - interlude(rng, sec, mode): 나레이션 사이에 넣을 고쟁 한 소절 (훑어 내림 + 짧은 선율, 마지막은 으뜸음)
  - bed(n, rng, mode): 나레이션 아래 깔리는 잔잔한 배경 (드문 고쟁 + 긴 얼후)
혼자 시험: python -X utf8 중국현악.py <결과.wav> [초] [음계]
음계 샘플 다섯 개: python -X utf8 중국현악.py --샘플 <폴더>  (각 30초 mp3, 역사/배경음샘플/ 에 들어 있음)
"""
import sys

import numpy as np

SR = 44100
PENTA = [0, 2, 4, 7, 9]          # 궁조 오음계 (도 레 미 솔 라)
ROOT = 50                        # D3 (MIDI)
MODES = {                        # 음계 이름: (으뜸음에서 잰 음 간격, 으뜸음 MIDI, 느낌) — 사용자 결정 2026-10-31: 편마다 골라 씀
    "궁조": ([0, 2, 4, 7, 9], 50, "밝고 당당 (건국·즉위·승리)"),
    "상조": ([0, 2, 5, 7, 10], 52, "차분하고 소박 (학자·행정·기록)"),
    "각조": ([0, 3, 5, 8, 10], 54, "어둡고 신비 (의문의 죽음·수수께끼)"),
    "치조": ([0, 2, 5, 7, 9], 55, "밝고 힘참 (전투·출정)"),
    "우조": ([0, 3, 5, 7, 10], 57, "슬프고 애잔 (비극적 최후)"),
}


def mode_of(mode):
    """음계 이름 → (음 간격, 으뜸음). 모르는 이름이면 궁조"""
    pen, root, _ = MODES.get(str(mode or "").strip(), MODES["궁조"])
    return pen, root


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def scale_notes(lo=ROOT, hi=ROOT + 31, pen=None, root=None):
    """lo~hi 사이의 음계 음 (MIDI). pen·root 를 주면 그 음계, 안 주면 궁조"""
    pen, root = (pen or PENTA), (ROOT if root is None else root)
    return [o * 12 + p + root for o in range(-2, 5) for p in pen if lo <= o * 12 + p + root <= hi]


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


def interlude(rng, sec=4.0, mode="궁조"):
    """나레이션 사이 고쟁 한 소절: 위에서 아래로 훑기(글리산도) → 짧은 선율 3~5음 → 마지막 음은 으뜸음, 누르는 음으로 길게"""
    pen, root = mode_of(mode)
    buf = np.zeros((int((sec + 2.5) * SR), 2), np.float32)
    notes = scale_notes(root + 12, root + 36, pen, root)
    t = 0.0
    for m in reversed(notes[-7:]):                                 # 훑어 내림
        _place(buf, guzheng(hz(m), 1.6, rng=rng), t, 0.32, pan=0.3)
        t += 0.055
    t += 0.35
    mel = scale_notes(root + 7, root + 24, pen, root)
    k = int(rng.integers(2, len(mel) - 2))
    steps = int(rng.integers(3, 6))
    for j in range(steps):
        k = int(np.clip(k + rng.choice([-2, -1, 1, 2]), 0, len(mel) - 1))
        last = j == steps - 1
        if last:                                                   # 끝음은 으뜸음 → 음계 느낌이 또렷하게
            k = mel.index(root + 12)
        _place(buf, guzheng(hz(mel[k]), 2.6 if last else 1.8, bend=0.03 if last else 0.0, rng=rng), t, 0.7 if last else 0.55)
        t += 0.42 if not last else 0
    return _reverb(buf, rng)


def bed(n, rng, mode="궁조"):
    """나레이션 아래 깔리는 배경: 긴 얼후 음(가끔) + 드문 고쟁 음 + 낮은 고쟁 저음 (저음은 으뜸음을 자주)"""
    pen, root = mode_of(mode)
    buf = np.zeros((n, 2), np.float32)
    low = scale_notes(root - 12, root, pen, root) + [root - 12, root]
    mid = scale_notes(root + 7, root + 26, pen, root)
    t = 0.5
    while t < n / SR - 2:
        _place(buf, guzheng(hz(rng.choice(low)), 3.0, rng=rng), t, 0.35, pan=-0.2)
        for _ in range(int(rng.integers(1, 4))):
            _place(buf, guzheng(hz(rng.choice(mid)), 2.0, rng=rng), t + rng.uniform(0.6, 3.2), 0.28, pan=0.25)
        if rng.random() < 0.45:
            _place(buf, erhu(hz(rng.choice(mid)), rng.uniform(3, 5)), t + rng.uniform(0.5, 2), 0.16, pan=-0.1)
        t += rng.uniform(3.5, 5.5)
    return _reverb(buf, rng, wet=0.4)


def write_wav(path, x):
    import wave
    x = np.clip(x / (np.abs(x).max() + 1e-6) * 0.8, -1, 1)
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((x * 32767).astype(np.int16).tobytes())


def sample(mode, sec=30, seed=11):
    """음계 샘플: 고쟁 한 소절(챕터 제목 때) + 잔잔한 배경(나레이션 아래)"""
    rng = np.random.default_rng(seed)
    it = interlude(rng, mode=mode)
    return np.concatenate([it, bed(int(max(5, sec - len(it) / SR) * SR), rng, mode)])


def main(a):
    if not a:
        print(__doc__)
        return 2
    if a[0] == "--샘플":                       # 음계 다섯 개 샘플 mp3
        import os
        import subprocess
        out = a[1] if len(a) > 1 else "."
        os.makedirs(out, exist_ok=True)
        for i, (nm, (_, _, feel)) in enumerate(MODES.items(), 1):
            wp = os.path.join(out, f"{i}_{nm}_{feel.split(' (')[0].replace(' ', '')}.wav")
            write_wav(wp, sample(nm))
            try:
                import imageio_ffmpeg
                ff = imageio_ffmpeg.get_ffmpeg_exe()
            except Exception:
                ff = "ffmpeg"
            subprocess.run([ff, "-y", "-loglevel", "error", "-i", wp, "-b:a", "160k", wp[:-4] + ".mp3"], check=True)
            os.remove(wp)
            print("OK", wp[:-4] + ".mp3")
        return 0
    sec = float(a[1]) if len(a) > 1 else 20
    write_wav(a[0], sample(a[2] if len(a) > 2 else "궁조", sec, seed=7))
    print("OK", a[0])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
