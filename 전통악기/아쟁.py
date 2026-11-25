"""아쟁 — 활(송진 바른 개나리 막대)로 줄을 긁어 켜는 낮은 현악기. 직접 합성 (녹음 음원을 쓰지 않아 저작권 걱정 없음)

해금(공통.bowed)과 다른 점
  - 낮은 음역 (첼로쯤): 으뜸음 MIDI 40~50
  - 농현(떠는 음): 처음엔 곧게 내다가 뒤로 갈수록 크고 느리게 출렁임 (깊이 = 센트, 100센트 = 반음)
  - 퇴성(꺾는 음): 음 끝을 아래로 끌어내림 / 추성(밀어 올림): 아래에서 밀어 올리며 시작
  - 음과 음 사이를 미끄러지듯 이어 감 (한 활로 이어지는 소리)
  - 거친 활 소리: 막대가 줄에 걸렸다 미끄러지며 나는 떨림(rough) + 긁는 잡음(scrape)
  - 몸통 울림: 낮은 쪽이 두껍게

사용: python -X utf8 전통악기/아쟁.py [결과폴더] [--실측]   → 후보 3개(30초 mp3) + 전체듣기.mp3
  --경쾌: 높은 음·빠르고 경쾌한 후보 7~9번 (평조, 박자에 맞춘 짧은 음, 장구 반주: 자진모리·휘모리·굿거리)
  --실측: 실제 아쟁 산조 녹음을 잰 값(PRESETS_REAL, 음색은 잰 배음 세기 그대로)으로 만든 후보 4~6번
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

# 실제 아쟁 산조 녹음(1969년 LP, 인터넷 아카이브)을 `연주분석.py` 로 잰 값 (2026-11-25) — 녹음은 숫자만 재는 데 쓰고 가락은 베끼지 않음
#   음역 MIDI 54~73(가운데 65.5) · 농현 1초에 약 5.3번, 위아래 ±40~50센트(그래프로 확인), 음 앞은 곧게 → 뒤에서 떨림
#   퇴성·추성은 반음 하나쯤 · 배음 세기(dB, 1~12번째) 아래 REAL_HARM_DB · 배음 사이 잡음 0.028 · 세기 빠른떨림 0.076
REAL_HARM_DB = [0.0, -6.0, -13.0, -16.2, -18.4, -19.1, -24.9, -30.8, -33.8, -34.8, -37.1, -38.5]
# 실측 프리셋: timbre='실측' = 위 배음 세기로 직접 쌓아 만든 음색, vib_start: 떨림이 시작되는 지점(음 길이 비율),
# fall_st·push_st: 꺾는 폭(반음)
PRESETS_REAL = {      # 1차로 만든 뒤 다시 재서 맞춤: 떨림 더 빠르고 고르게(slow 작게, vib_start 앞당김), 거친 결·잡음 늘림, 받침음 작게
    "4_실측_산조그대로": dict(root=52, span=19, depth=50, rate=5.8, slow=0.06, fall=0.25, push=0.25, rough=0.42, scrape=0.09,
                        note=(0.5, 1.5), glide=0.12, mode=GYEMYEON, timbre="실측", vib_start=0.15, fall_st=(0.8, 1.2),
                        push_st=(0.7, 1.1), drone=(0.3, 0.12)),
    "5_실측_느린배경": dict(root=52, span=17, depth=45, rate=5.5, slow=0.06, fall=0.20, push=0.15, rough=0.36, scrape=0.08,
                       note=(1.1, 2.2), glide=0.14, mode=GYEMYEON, timbre="실측", vib_start=0.2, fall_st=(0.8, 1.2),
                       push_st=(0.7, 1.0), drone=(0.3, 0.12)),
    "6_실측_낮고애절": dict(root=50, span=19, depth=55, rate=5.2, slow=0.08, fall=0.35, push=0.20, rough=0.42, scrape=0.10,
                       note=(1.0, 2.0), glide=0.16, mode=GYEMYEON, timbre="실측", vib_start=0.2, fall_st=(1.0, 1.5),
                       push_st=(0.8, 1.2), drone=(0.3, 0.12)),
}


# 빠르고 경쾌한 후보 (사용자 요청 2026-11-25): 높은 음 · 밝은 평조 · 박자에 맞춘 짧은 음 · 장구 반주 · 꾸밈음(grace: 위에서 톡 떨어지며 시작)
#   unit: 장단 한 칸(초, 12칸 = 한 장단), beats: 한 음이 차지하는 칸 수 후보, steps: 한 마디 음 수, rest: 마디 사이 쉬는 칸 수,
#   janggu: 장구 장단 이름 (JANGGU), grace: 꾸밈음 비율, fade: 마디 시작·끝 부드럽게(초)
PRESETS_FAST = {
    "7_경쾌_자진모리": dict(root=62, span=19, depth=30, rate=6.2, slow=0.0, fall=0.10, push=0.10, grace=0.20, rough=0.35,
                        scrape=0.08, glide=0.04, mode=PYEONG, timbre="실측", vib_start=0.3, fall_st=(0.6, 1.0),
                        push_st=(0.5, 0.9), drone=(0.0, 0.0), unit=0.17, beats=[1, 1, 2, 2, 2, 3], steps=(6, 10),
                        rest=(2, 5), janggu="자진모리", fade=(0.03, 0.25)),
    "8_신나는_휘모리": dict(root=64, span=17, depth=22, rate=6.8, slow=0.0, fall=0.08, push=0.08, grace=0.25, rough=0.38,
                       scrape=0.09, glide=0.03, mode=PYEONG, timbre="실측", vib_start=0.3, fall_st=(0.5, 0.9),
                       push_st=(0.5, 0.8), drone=(0.0, 0.0), unit=0.13, beats=[1, 1, 1, 2, 2], steps=(8, 13),
                       rest=(2, 4), janggu="휘모리", fade=(0.02, 0.2)),
    "9_흥겨운_굿거리": dict(root=60, span=19, depth=35, rate=5.8, slow=0.0, fall=0.12, push=0.15, grace=0.15, rough=0.32,
                       scrape=0.07, glide=0.05, mode=PYEONG, timbre="실측", vib_start=0.3, fall_st=(0.6, 1.0),
                       push_st=(0.5, 0.9), drone=(0.0, 0.0), unit=0.2, beats=[1, 2, 2, 3, 3], steps=(5, 8),
                       rest=(3, 6), janggu="굿거리", fade=(0.03, 0.3)),
}
# 장구 장단 12칸: 덩(양손) · 쿵(북편, 낮게) · 덕(채편, 딱) · 기(채편 작게) · 르(굴림)
JANGGU = {
    "자진모리": {0: "덩", 3: "덕", 6: "쿵", 8: "덕", 10: "덕"},
    "휘모리": {0: "덩", 3: "덕", 6: "쿵", 9: "덕"},
    "굿거리": {0: "덩", 2: "기", 3: "덕", 4: "쿵", 6: "르", 9: "쿵", 11: "덕"},
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
        vs = p.get("vib_start", 0.15) * (1.0 if d > 0.9 else 0.4)      # 짧은 음은 일찍 떨기 시작
        grow = np.clip((u - vs) / 0.45, 0, 1) ** 1.2
        depth = p["depth"] / 100 * (1.0 if role == "shake" else 0.4)
        rate = p["rate"] * (1 - p.get("slow", 0.18) * u) * rng.uniform(0.92, 1.08)
        ph = np.cumsum(2 * np.pi * rate / SR)
        o = depth * grow * np.sin(ph)
        if role == "fall":                   # 퇴성: 60% 지점부터 1~2 반음 아래로
            o = o * 0.4 - rng.uniform(*p.get("fall_st", (1.0, 2.0))) * np.clip((u - 0.6) / 0.35, 0, 1) ** 1.6
        if role == "push":                   # 추성: 아래에서 밀어 올리며 시작
            o = o - rng.uniform(*p.get("push_st", (1.0, 2.0))) * np.exp(-t / 0.18)
        if role == "grace":                  # 꾸밈음: 2반음 위에서 톡 떨어지며 시작 (빠른 가락의 경쾌함)
            o = o + 2.0 * (t < 0.045) * np.clip(1 - t / 0.06, 0, 1)
        orn[i0:i0 + n] = o
        # 세기: 활을 바꿀 때 살짝 줄고, 음 가운데쯤에서 부풀었다 끝에 줄어듦 (산조의 밀고 당김)
        sw = 0.55 + 0.45 * np.sin(np.pi * np.clip(u * 0.9 + 0.05, 0, 1)) ** 0.8
        dip = 1 - 0.55 * np.exp(-t / 0.07)
        amp[i0:i0 + n] = sw * dip
        i0 += n
    w = max(3, int(p["glide"] * SR))
    pad = np.concatenate([np.full(w, base[0]), base, np.full(w, base[-1])])
    base = fftconvolve(pad, np.ones(w) / w, "same")[w:w + total].astype(np.float32)
    fi, fo = p.get("fade", (0.35, 0.9))
    fade = np.clip(np.arange(total) / (fi * SR), 0, 1) * np.clip((total - np.arange(total)) / (fo * SR), 0, 1)
    return base + orn, amp * fade


def real_tone(semis, amp, p, rng):
    """실측 음색: 진짜 연주에서 잰 배음 세기(REAL_HARM_DB)대로 배음을 쌓음. 세게 켤수록 높은 배음이 살아남(밝아짐),
    활 걸림 떨림(rough) · 배음마다 조금씩 다른 흔들림 · 소리 높이에 맞춰 박자가 붙은 긁는 잡음(scrape)"""
    from scipy.signal import butter, lfilter
    n = len(semis)
    jitter = _lp_noise(rng, n, 18) * 0.003 * (0.5 + p["rough"])
    f = 440.0 * 2 ** ((semis - 69) / 12) * (1 + jitter)
    ph = np.cumsum(f / SR)
    nh = int(min(40, 9000 / max(60.0, float(f.min()))))
    a_norm = amp / (amp.max() + 1e-6)
    y = np.zeros(n, np.float32)
    for h in range(1, nh + 1):
        db = REAL_HARM_DB[h - 1] if h <= len(REAL_HARM_DB) else REAL_HARM_DB[-1] - 2.5 * (h - len(REAL_HARM_DB))
        g = 10 ** (db / 20) * (0.35 + 0.65 * a_norm) ** (0.08 * (h - 1))    # 약하게 켜면 높은 배음이 줄어 어두워짐
        wob = 1 + 0.25 * _lp_noise(rng, n, 6) if h > 2 else 1               # 배음마다 세기가 조금씩 출렁임 (살아 있는 소리)
        y += (g * wob * np.sin(2 * np.pi * h * ph + rng.uniform(0, 6.28))).astype(np.float32)
    y = y * (1 + p["rough"] * 0.35 * _lp_noise(rng, n, 60))                 # 활이 걸렸다 미끄러지는 거친 결
    pp = ph % 1
    nz = rng.standard_normal(n).astype(np.float32) * (0.3 + 0.7 * (pp < 0.2))
    nz = lfilter(*butter(2, [1200 / (SR / 2), 6000 / (SR / 2)], "band"), nz)
    y = y / (np.abs(y).max() + 1e-6) + nz / (np.abs(nz).max() + 1e-6) * p["scrape"] * 2.2
    y = lfilter(*butter(1, 50 / (SR / 2), "high"), y) * amp
    return (y / (np.abs(y).max() + 1e-6)).astype(np.float32)


def ajaeng_tone(semis, amp, p, rng):
    """음높이 곡선(MIDI 반음) → 아쟁 소리 (모노)"""
    from scipy.signal import butter, lfilter
    if p.get("timbre") == "실측":
        return real_tone(semis, amp, p, rng)
    if p.get("timbre") == "태평소":                       # 같은 가락 짜기·꾸밈을 태평소 소리로 (태평소.py)
        return K.wind_tone(semis, amp, K.TAEP_HARM_DB, rng, breath=p.get("breath", 0.05), buzz=p.get("buzz", 0.18), bright_amp=p.get("bright_amp", 0.06))
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


def make_phrase_fast(p, rng, mel, k):
    """박자에 맞춘 빠른 마디: 칸 수(beats)로 음 길이, 같은 음 되풀이·뛰는 음 섞음, 끝은 으뜸음이나 5도에서 떨며 맺음"""
    notes = []
    steps = int(rng.integers(*p["steps"]))
    for j in range(steps):
        mv = int(rng.choice([-3, -2, -1, -1, 0, 1, 1, 2, 3]))                 # 오르내림 고르게 (위로만 쏠리지 않게)
        if k + mv < 0 or k + mv > len(mel) - 1:
            mv = -mv
        k = int(np.clip(k + mv, 0, len(mel) - 1))
        last = j == steps - 1
        d = p["unit"] * (max(p["beats"]) + 1 if last else int(rng.choice(p["beats"])))
        r = rng.random()
        if last:
            root = p["root"]
            k = min(range(len(mel)), key=lambda i: min(abs(mel[i] - root - 12), abs(mel[i] - root - 7)) + 0.3 * abs(i - k))
            role = "fall" if rng.random() < p["fall"] * 2 else "shake"
        elif r < p.get("grace", 0):
            role = "grace"
        elif r < p.get("grace", 0) + p["push"]:
            role = "push"
        elif r < p.get("grace", 0) + p["push"] + p["fall"]:
            role = "fall"
        elif d >= 2 * p["unit"]:
            role = "shake"
        else:
            role = "plain"
        notes.append((mel[k], d, role))
    return notes, k


def janggu_hit(kind, rng):
    """장구 한 번 — 공통.py 의 janggu (사용자가 확인한 장구 소리, 2026-11-25). 르 = 채 굴림(더러러러)"""
    return K.janggu({"르": "더러러러"}.get(kind, kind), rng)


def bed(sec, p, seed=7):
    """잔잔하게 깔리는 아쟁 독주 (스테레오) + 가끔 아주 낮은 개방현이 길게 받쳐 줌"""
    rng = np.random.default_rng(seed)
    n = int(sec * SR)
    buf = np.zeros((n, 2), np.float32)
    root = p["root"]
    mel = [root + o * 12 + s for o in range(0, 3) for s in p["mode"] if root + o * 12 + s <= root + p["span"]]
    k = mel.index(root + 7) if root + 7 in mel else len(mel) // 2
    t = 0.4
    fast = "unit" in p
    if fast and p.get("janggu"):                                              # 장구 반주 (처음 한 장단은 장구만)
        pat, u = JANGGU[p["janggu"]], p["unit"]
        c = 0
        while 0.4 + c * u < sec - 0.5:
            kind = pat.get(c % 12)
            if kind:
                K.place(buf, janggu_hit(kind, rng), 0.4 + c * u, 0.6 if kind != "기" else 0.32, pan=-0.12)
            c += 1
        t = 0.4 + 12 * u
    while t < sec - 3:
        notes, k = (make_phrase_fast if fast else make_phrase)(p, rng, mel, k)
        semis, amp = phrase_contour(notes, p, rng)
        tone = ajaeng_tone(semis, amp, p, rng)
        K.place(buf, tone, t, 0.62, pan=0.12)
        dp, dg = p.get("drone", (0.55, 0.22))                                 # 받침음이 나올 확률, 크기
        if rng.random() < dp:                                                 # 낮은 받침음 (개방현)
            ln = len(tone) / SR
            low = [(root - 12 if rng.random() < 0.5 else root, ln, "plain")]
            s2, a2 = phrase_contour(low, dict(p, depth=p["depth"] * 0.5), rng)
            K.place(buf, ajaeng_tone(s2, a2 * 0.8, dict(p, scrape=p["scrape"] * 0.5), rng), t + 0.2, dg, pan=-0.25)
        if fast:                                                              # 박자 칸에 맞춰 쉼
            t += round(len(tone) / SR / p["unit"]) * p["unit"] + int(rng.integers(*p["rest"])) * p["unit"]
        else:
            t += len(tone) / SR + rng.uniform(0.6, 2.0)                       # 숨 쉬듯 쉼
    return K.reverb(buf, rng, sec=1.6 if fast else 2.6, wet=0.22 if fast else 0.33)


def ffmpeg():
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return "ffmpeg"


def main(out, presets=None, listen="아쟁_전체듣기.mp3"):
    os.makedirs(out, exist_ok=True)
    mp3s = []
    for name, p in (presets or PRESETS).items():
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
                    os.path.join(out, listen)], check=True)
    os.remove(lst)
    return 0


if __name__ == "__main__":
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    args = [a for a in sys.argv[1:] if a not in ("--실측", "--경쾌")]
    out = args[0] if args else os.path.join(here, "역사", "배경음샘플", "한국", "아쟁")
    if "--경쾌" in sys.argv:          # 높은 음 · 빠르고 경쾌한 후보 7~9번 (장구 반주)
        sys.exit(main(out, PRESETS_FAST, "아쟁_경쾌_전체듣기.mp3"))
    if "--실측" in sys.argv:          # 실제 연주를 잰 값으로 만든 후보 4~6번
        sys.exit(main(out, PRESETS_REAL, "아쟁_실측_전체듣기.mp3"))
    sys.exit(main(out))
