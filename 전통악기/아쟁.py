"""아쟁 — 활(송진 바른 개나리 막대)로 줄을 긁어 켜는 낮은 현악기. 직접 합성 (녹음 음원을 쓰지 않아 저작권 걱정 없음)

해금(공통.bowed)과 다른 점
  - 낮은 음역 (첼로쯤): 으뜸음 MIDI 40~50
  - 농현(떠는 음): 처음엔 곧게 내다가 뒤로 갈수록 크고 느리게 출렁임 (깊이 = 센트, 100센트 = 반음)
  - 퇴성(꺾는 음): 음 끝을 아래로 끌어내림 / 추성(밀어 올림): 아래에서 밀어 올리며 시작
  - 음과 음 사이를 미끄러지듯 이어 감 (한 활로 이어지는 소리)
  - 거친 활 소리: 막대가 줄에 걸렸다 미끄러지며 나는 떨림(rough) + 긁는 잡음(scrape)
  - 몸통 울림: 낮은 쪽이 두껍게

사용: python -X utf8 전통악기/아쟁.py [결과폴더]   → 후보 3개(30초 mp3) + 전체듣기.mp3
"""
import os
import subprocess
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import 공통 as K  # noqa: E402

SR = K.SR
GYEMYEON = [0, 3, 5, 7, 10]     # 계면조 (슬프고 애절)
PYEONG = [0, 2, 5, 7, 9]        # 평조 (차분)

# 후보 프리셋 — root: 으뜸음 MIDI, span: 가락이 올라가는 폭(반음), depth: 농현 깊이(센트), rate: 농현 빠르기(1초에 몇 번),
# fall: 퇴성 비율, push: 추성 비율, rough: 활 걸림 떨림, scrape: 긁는 잡음, bright: 밝기(Hz), grit: 소리 찢김(포화),
# note: 한 음 길이 범위(초), glide: 음 사이 미끄러짐(초)
PRESETS = {
    "1_은은한아쟁": dict(root=50, span=19, depth=45, rate=4.8, fall=0.15, push=0.10, rough=0.12, scrape=0.03,
                    bright=1900, grit=0.4, note=(1.6, 3.0), glide=0.10, mode=GYEMYEON),
    "2_산조풍아쟁": dict(root=45, span=22, depth=110, rate=4.2, fall=0.35, push=0.25, rough=0.28, scrape=0.07,
                    bright=2600, grit=0.9, note=(1.4, 3.6), glide=0.16, mode=GYEMYEON),
    "3_거친저음아쟁": dict(root=40, span=19, depth=85, rate=3.6, fall=0.40, push=0.20, rough=0.48, scrape=0.13,
                     bright=3200, grit=1.6, note=(1.8, 4.2), glide=0.20, mode=GYEMYEON),
}


def _lp_noise(rng, n, cutoff):
    """천천히 출렁이는 잡음 (-1~1 쯤)"""
    from scipy.signal import butter, lfilter
    x = lfilter(*butter(2, cutoff / (SR / 2)), rng.standard_normal(n))
    return (x / (np.abs(x).max() + 1e-6)).astype(np.float32)


def phrase_contour(notes, p, rng):
    """notes = [(MIDI, 길이초, 역할)] → (음높이 곡선(반음), 세기 곡선). 역할: 'shake' 떠는 음, 'fall' 꺾는 음, 'push' 밀어 올림, 'plain'"""
    from scipy.signal import fftconvolve
    total = int(sum(d for _, d, _ in notes) * SR)
    base = np.zeros(total, np.float32)       # 음 계단 (나중에 부드럽게 이어 붙임)
    orn = np.zeros(total, np.float32)        # 꾸밈 (농현·퇴성·추성) — 부드럽게 하지 않음
    amp = np.zeros(total, np.float32)
    i0 = 0
    for k, (m, d, role) in enumerate(notes):
        n = int(d * SR) if k < len(notes) - 1 else total - i0
        t = np.arange(n) / SR
        base[i0:i0 + n] = m
        u = t / d
        # 농현: 음의 15% 지점부터 커짐, 끝으로 갈수록 깊고 살짝 느려짐
        grow = np.clip((u - 0.15) / 0.45, 0, 1) ** 1.2
        depth = p["depth"] / 100 * (1.0 if role == "shake" else 0.4)
        rate = p["rate"] * (1 - 0.18 * u) * rng.uniform(0.92, 1.08)
        ph = np.cumsum(2 * np.pi * rate / SR)
        o = depth * grow * np.sin(ph)
        if role == "fall":                   # 퇴성: 60% 지점부터 1~2 반음 아래로
            o = o * 0.4 - rng.uniform(1.0, 2.0) * np.clip((u - 0.6) / 0.35, 0, 1) ** 1.6
        if role == "push":                   # 추성: 아래에서 밀어 올리며 시작
            o = o - rng.uniform(1.0, 2.0) * np.exp(-t / 0.18)
        orn[i0:i0 + n] = o
        # 세기: 활을 바꿀 때 살짝 줄고, 음 가운데쯤에서 부풀었다 끝에 줄어듦 (산조의 밀고 당김)
        sw = 0.55 + 0.45 * np.sin(np.pi * np.clip(u * 0.9 + 0.05, 0, 1)) ** 0.8
        dip = 1 - 0.55 * np.exp(-t / 0.07)
        amp[i0:i0 + n] = sw * dip
        i0 += n
    w = max(3, int(p["glide"] * SR))
    pad = np.concatenate([np.full(w, base[0]), base, np.full(w, base[-1])])
    base = fftconvolve(pad, np.ones(w) / w, "same")[w:w + total].astype(np.float32)
    fade = np.clip(np.arange(total) / (0.35 * SR), 0, 1) * np.clip((total - np.arange(total)) / (0.9 * SR), 0, 1)
    return base + orn, amp * fade


def ajaeng_tone(semis, amp, p, rng):
    """음높이 곡선(MIDI 반음) → 아쟁 소리 (모노)"""
    from scipy.signal import butter, lfilter
    n = len(semis)
    jitter = _lp_noise(rng, n, 18) * 0.004 * (0.5 + p["rough"])            # 활이 걸렸다 미끄러지며 음이 살짝 흔들림
    f = 440.0 * 2 ** ((semis - 69) / 12) * (1 + jitter)
    ph = np.cumsum(f / SR) % 1
    saw = (2 * ph - 1).astype(np.float32)
    pulse = np.where(ph < 0.32, 1.0, -0.47).astype(np.float32)               # 활에 걸린 좁은 펄스 (거친 결)
    y = saw * (1 - 0.35 * p["rough"]) + pulse * 0.35 * p["rough"]
    rough_am = 1 + p["rough"] * 0.6 * _lp_noise(rng, n, 55)                  # 걸림 떨림 (빠르게 거칠거칠)
    y = y * rough_am
    # 몸통 울림: 낮은 울림 두 곳 + 가운데 + 밝기
    body = (lfilter(*butter(2, [110 / (SR / 2), 260 / (SR / 2)], "band"), y) * 1.3
            + lfilter(*butter(2, [300 / (SR / 2), 620 / (SR / 2)], "band"), y) * 0.9
            + lfilter(*butter(2, [900 / (SR / 2), 1500 / (SR / 2)], "band"), y) * 0.45)
    y = lfilter(*butter(2, p["bright"] / (SR / 2)), y) * 0.55 + body
    y = np.tanh(y * (1 + p["grit"])) / np.tanh(1 + p["grit"])                 # 소리가 살짝 찢어지는 거친 맛
    # 긁는 잡음: 소리 높이에 맞춰 박자가 붙은 잡음 (송진 막대가 줄을 긁는 소리)
    nz = rng.standard_normal(n).astype(np.float32) * (0.4 + 0.6 * (ph < 0.25))
    nz = lfilter(*butter(2, [1400 / (SR / 2), 5200 / (SR / 2)], "band"), nz)
    nz = nz / (np.abs(nz).max() + 1e-6)
    y = y / (np.abs(y).max() + 1e-6) + nz * p["scrape"] * 3.0
    y = lfilter(*butter(1, 40 / (SR / 2), "high"), y)
    y = y * amp
    return (y / (np.abs(y).max() + 1e-6)).astype(np.float32)


def make_phrase(p, rng, mel, last_k):
    """가락 한 마디: 3~5음, 계단처럼 오르내리고 끝은 떨거나 꺾음"""
    k = last_k
    notes = []
    steps = int(rng.integers(3, 6))
    for j in range(steps):
        k = int(np.clip(k + rng.choice([-2, -1, -1, 1, 1, 2]), 0, len(mel) - 1))
        d = rng.uniform(*p["note"])
        last = j == steps - 1
        r = rng.random()
        if last:
            role = "fall" if rng.random() < p["fall"] * 1.6 else "shake"
            d *= 1.4
        elif r < p["push"]:
            role = "push"
        elif r < p["push"] + p["fall"] * 0.5:
            role = "fall"
        elif r < 0.85:
            role = "shake"
        else:
            role = "plain"
        notes.append((mel[k], d, role))
    return notes, k


def bed(sec, p, seed=7):
    """잔잔하게 깔리는 아쟁 독주 (스테레오) + 가끔 아주 낮은 개방현이 길게 받쳐 줌"""
    rng = np.random.default_rng(seed)
    n = int(sec * SR)
    buf = np.zeros((n, 2), np.float32)
    root = p["root"]
    mel = [root + o * 12 + s for o in range(0, 3) for s in p["mode"] if root + o * 12 + s <= root + p["span"]]
    k = mel.index(root + 7) if root + 7 in mel else len(mel) // 2
    t = 0.4
    while t < sec - 3:
        notes, k = make_phrase(p, rng, mel, k)
        semis, amp = phrase_contour(notes, p, rng)
        tone = ajaeng_tone(semis, amp, p, rng)
        K.place(buf, tone, t, 0.62, pan=0.12)
        if rng.random() < 0.55:                                               # 낮은 받침음 (개방현)
            ln = len(tone) / SR
            low = [(root - 12 if rng.random() < 0.5 else root, ln, "plain")]
            s2, a2 = phrase_contour(low, dict(p, depth=p["depth"] * 0.5), rng)
            K.place(buf, ajaeng_tone(s2, a2 * 0.8, dict(p, scrape=p["scrape"] * 0.5), rng), t + 0.2, 0.22, pan=-0.25)
        t += len(tone) / SR + rng.uniform(0.6, 2.0)                           # 숨 쉬듯 쉼
    return K.reverb(buf, rng, sec=2.6, wet=0.33)


def ffmpeg():
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return "ffmpeg"


def main(out):
    os.makedirs(out, exist_ok=True)
    mp3s = []
    for name, p in PRESETS.items():
        wp = os.path.join(out, name + ".wav")
        K.write_wav(wp, bed(30, p))
        mp = wp[:-4] + ".mp3"
        subprocess.run([ffmpeg(), "-y", "-loglevel", "error", "-i", wp, "-b:a", "160k", mp], check=True)
        os.remove(wp)
        mp3s.append(mp)
        print("OK", mp)
    lst = os.path.join(out, "_목록.txt")
    with open(lst, "w", encoding="utf-8") as f:
        f.writelines(f"file '{os.path.abspath(m)}'\n" for m in mp3s)
    subprocess.run([ffmpeg(), "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-b:a", "160k",
                    os.path.join(out, "아쟁_전체듣기.mp3")], check=True)
    os.remove(lst)
    return 0


if __name__ == "__main__":
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(here, "역사", "배경음샘플", "한국", "아쟁")))
