# -*- coding: utf-8 -*-
"""옛날 오락실 게임 같은 8비트 효과음·배경음을 직접 합성(남의 음원 없음 → 저작권 걱정 없음).

블록애니.py 가 장면 영상에 자동으로 넣음. 따로 들어 보기:
  python 레트로소리.py 견본 <폴더>      # 효과음마다 wav + 배경음 wav

효과음 이름: 착지 놀람 활 맞음 광선 점프 쓰러짐 승리 동전 주먹 윙윙 데굴데굴 부서짐 휘익 삐 심장 아야
배경음 곡: 레트로전투
"""
import math
import sys
import wave

import numpy as np

SR = 44100


def _t(sec):
    return np.arange(int(sec * SR)) / SR


def square(freq, sec, duty=0.5):
    """네모 파형(8비트 소리의 기본). freq 는 숫자 또는 시간마다 바뀌는 배열."""
    n = int(sec * SR)
    f = np.full(n, freq, dtype=float) if np.isscalar(freq) else np.asarray(freq, dtype=float)[:n]
    ph = np.cumsum(f) / SR
    return np.where((ph % 1.0) < duty, 1.0, -1.0)


def triangle(freq, sec):
    n = int(sec * SR)
    f = np.full(n, freq, dtype=float) if np.isscalar(freq) else np.asarray(freq, dtype=float)[:n]
    ph = np.cumsum(f) / SR
    return 2 * np.abs(2 * (ph % 1.0) - 1) - 1


def noise(sec, step=1):
    """옛날 게임기 잡음(같은 값을 step 번 반복 → 낮을수록 거친 소리)."""
    n = int(sec * SR)
    v = np.random.default_rng(7).uniform(-1, 1, n // step + 1)
    return np.repeat(v, step)[:n]


def env(n, attack=0.005, decay=None, sec=None):
    sec = sec or n / SR
    t = np.arange(n) / SR
    e = np.minimum(1.0, t / max(attack, 1e-4))
    if decay:
        e = e * np.exp(-t / decay)
    else:
        e = e * np.clip(1 - t / sec, 0, 1)
    return e


def sweep(f0, f1, sec, curve="exp"):
    t = _t(sec) / sec
    if curve == "exp":
        return f0 * (f1 / f0) ** t
    return f0 + (f1 - f0) * t


# ───────────── 효과음 ─────────────
def sfx(name):
    if name == "활":  # 시위 튕김 '퉁' + 바람 '슉'
        a = square(sweep(900, 260, 0.12), 0.12, 0.25) * env(int(0.12 * SR), decay=0.05)
        b = noise(0.18, 3) * env(int(0.18 * SR), decay=0.06) * 0.35
        out = np.zeros(int(0.18 * SR)); out[:len(a)] += a * 0.6; out += b
        return out
    if name == "맞음":  # '퍽'
        a = noise(0.16, 6) * env(int(0.16 * SR), decay=0.045)
        b = square(sweep(220, 70, 0.16), 0.16) * env(int(0.16 * SR), decay=0.06) * 0.5
        return a * 0.8 + b
    if name == "윙윙":  # 벌 날갯소리(떨리는 낮은 소리)
        sec = 0.9
        t = _t(sec)
        f = 190 + 12 * np.sin(2 * math.pi * 6 * t)
        a = square(f, sec, 0.3) * (0.6 + 0.4 * np.sin(2 * math.pi * 28 * t)) * env(int(sec * SR), attack=0.08)
        return a
    if name == "데굴데굴":  # 통나무 구르는 소리: 낮게 '두르륵'
        sec = 1.0
        t = _t(sec)
        a = triangle(70 + 10 * np.sin(2 * math.pi * 3 * t), sec) * (0.55 + 0.45 * (np.sin(2 * math.pi * 9 * t) > 0))
        b = noise(sec, 40) * 0.35 * (0.5 + 0.5 * np.sin(2 * math.pi * 9 * t))
        return (a + b) * env(int(sec * SR), attack=0.05)
    if name == "부서짐":  # 돌이 깨지는 '와장'
        sec = 0.35
        a = noise(sec, 2) * env(int(sec * SR), decay=0.07)
        b = noise(sec, 9) * env(int(sec * SR), decay=0.12) * 0.6
        return a * 0.7 + b
    if name == "휘익":  # 큰 것이 떨어지는 '휘이이익'(높은 데서 낮게)
        sec = 1.3
        f = sweep(1400, 300, sec)
        return square(f, sec, 0.5) * env(int(sec * SR), attack=0.2) * 0.5 + triangle(f / 2, sec) * 0.3
    if name == "삐":  # 남은 시간 경고
        return square(1760, 0.12, 0.5) * env(int(0.12 * SR), attack=0.002) * 0.6
    if name == "심장":  # 쿵-쾅
        def thump(sec, f0):
            return np.sin(2 * math.pi * np.cumsum(sweep(f0, 40, sec)) / SR) * env(int(sec * SR), decay=0.05)
        return np.concatenate([thump(0.14, 90), np.zeros(int(0.06 * SR)), thump(0.18, 75) * 0.8])
    if name == "아야":  # 맞았을 때 '뾰로롱↓'
        sec = 0.4
        return square(sweep(900, 150, sec), sec, 0.5) * (0.6 + 0.4 * np.sign(np.sin(2 * math.pi * 25 * _t(sec)))) \
            * env(int(sec * SR)) * 0.7
    if name == "주먹":
        return sfx("맞음")
    if name == "광선":  # '퓨웅~' 떨리며 내려감
        sec = 0.55
        f = sweep(1600, 180, sec) * (1 + 0.08 * np.sin(2 * math.pi * 30 * _t(sec)))
        return square(f, sec, 0.25) * env(int(sec * SR), attack=0.01) * 0.7
    if name == "착지":  # '쿵'
        sec = 0.4
        a = np.sin(2 * math.pi * np.cumsum(sweep(110, 40, sec)) / SR) * env(int(sec * SR), decay=0.12)
        b = noise(sec, 12) * env(int(sec * SR), decay=0.05) * 0.6
        return a + b
    if name == "점프":  # '뾰옹'
        sec = 0.2
        return square(sweep(280, 950, sec), sec, 0.25) * env(int(sec * SR), attack=0.005) * 0.6
    if name == "놀람":  # '삐빅'
        a = square(1320, 0.07, 0.5) * 0.5
        gap = np.zeros(int(0.03 * SR))
        b = square(1760, 0.09, 0.5) * env(int(0.09 * SR)) * 0.5
        return np.concatenate([a, gap, b])
    if name == "쓰러짐":  # 뚜루루루↓
        notes = [784, 659, 523, 440, 349, 262, 196]
        parts = [square(f, 0.075, 0.5) * env(int(0.075 * SR)) for f in notes]
        tail = triangle(98, 0.35) * env(int(0.35 * SR))
        return np.concatenate(parts + [tail]) * 0.55
    if name == "동전":
        return np.concatenate([square(988, 0.07, 0.5), square(1319, 0.3, 0.5) * env(int(0.3 * SR))]) * 0.45
    if name == "승리":  # 짧은 팡파레(직접 만든 가락)
        seq = [(523, .12), (659, .12), (784, .12), (1047, .28), (0, .06), (880, .12), (1047, .5)]
        out = []
        for f, d in seq:
            if f == 0:
                out.append(np.zeros(int(d * SR)))
                continue
            lead = square(f, d, 0.25) * env(int(d * SR), attack=0.005, decay=d * 1.2)
            bass = triangle(f / 4, d) * 0.6
            out.append(lead * 0.55 + bass * 0.5)
        return np.concatenate(out)
    raise ValueError(f"모르는 효과음: {name}")


# ───────────── 배경음 ─────────────
NOTE = {n: i for i, n in enumerate(["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"])}


def hz(s):  # "A4" → 440
    if s in ("-", "."):
        return 0.0
    name, octv = s[:-1], int(s[-1])
    return 440.0 * 2 ** ((NOTE[name] + (octv - 4) * 12 - 9) / 12)


def bgm(sec, song="레트로전투", bpm=150):
    """직접 만든 8비트 전투 곡(라단조, 기본 150 BPM). sec 길이만큼 반복."""
    step = 60 / bpm / 2  # 8분음표
    # 가락(8분음표 한 칸씩, 4마디 = 32칸) — Am F G E 진행
    lead = ("A4 - C5 E5 A5 - G5 E5  F5 - E5 C5 A4 - C5 -  "
            "G4 - B4 D5 G5 - F5 D5  E5 - G#4 B4 E5 - D5 B4").split()
    bass_roots = ["A2", "F2", "G2", "E2"]
    one_loop = []
    n_step = int(step * SR)
    for i in range(32):
        bar = i // 8
        f = hz(lead[i])
        l = square(f, step, 0.25) * env(n_step, attack=0.003, decay=step * 0.9) * 0.32 if f else np.zeros(n_step)
        root = hz(bass_roots[bar])
        bf = root * (2 if i % 2 else 1)  # 옥타브로 통통 튀는 베이스
        b = triangle(bf, step) * 0.55
        h = noise(step, 1) * env(n_step, decay=0.012) * (0.22 if i % 2 else 0.1)  # 하이햇
        k = np.zeros(n_step)
        if i % 4 == 0:  # 북
            k = np.sin(2 * math.pi * np.cumsum(sweep(140, 45, step)) / SR) * env(n_step, decay=0.06) * 0.6
        one_loop.append(l + b + h + k)
    loop = np.concatenate(one_loop)
    reps = int(math.ceil(sec * SR / len(loop)))
    return np.tile(loop, reps)[: int(sec * SR)]


# ───────────── 섞기 ─────────────
SFX_VOL = {"윙윙": 0.4, "동전": 0.7, "데굴데굴": 0.6, "부서짐": 0.6, "휘익": 0.5, "삐": 0.6, "심장": 0.9}  # 효과음마다 크기 배율
def bgm_tempo(sec, song, tempo):
    """tempo = [(초, BPM), ...] — 구간마다 빠르기를 바꿔 이어 붙임(점점 빨라지는 음악)."""
    tempo = sorted(tempo) or [(0, 150)]
    if tempo[0][0] > 0:
        tempo = [(0, 150)] + tempo
    parts = []
    for k, (t0, b) in enumerate(tempo):
        t1 = tempo[k + 1][0] if k + 1 < len(tempo) else sec
        if t1 > t0:
            parts.append(bgm(t1 - t0, song, b))
    m = np.concatenate(parts)
    n = int(sec * SR)
    return np.pad(m, (0, max(0, n - len(m))))[:n]


def mix(total_sec, events, music=None, music_vol=0.35, music_end=None, sfx_vol=0.9, tempo=None):
    """events = [(초, 효과음이름), ...]. 배경음은 music_end 초에 0.4초 동안 줄어들며 끝남.
    배경음 최고 크기 music_vol(설정 bgm_peak 와 같은 뜻)."""
    n = int(total_sec * SR)
    out = np.zeros(n)
    if music:
        m = bgm_tempo(total_sec, music, tempo) if tempo else bgm(total_sec, music)
        m = m / (np.max(np.abs(m)) + 1e-9) * music_vol
        if music_end is not None:
            e0, e1 = int(music_end * SR), int((music_end + 0.4) * SR)
            fade = np.ones(n)
            fade[e0:e1] = np.linspace(1, 0, max(0, min(e1, n) - e0))[: max(0, min(e1, n) - e0)]
            fade[e1:] = 0
            m = m * fade
        out += m
    for t, name in events:
        s = sfx(name)
        s = s / (np.max(np.abs(s)) + 1e-9) * sfx_vol * SFX_VOL.get(name, 1.0)
        i = int(t * SR)
        if i >= n:
            continue
        j = min(n, i + len(s))
        out[i:j] += s[: j - i]
    peak = np.max(np.abs(out))
    if peak > 0.98:  # 겹쳐서 넘치면 전체를 살짝 줄임(찢어지는 소리 막기)
        out = out / peak * 0.98
    return out


def write_wav(path, x):
    x = np.clip(x, -1, 1)
    data = (x * 32767).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(data.tobytes())


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "견본":
        import os
        d = sys.argv[2]
        os.makedirs(d, exist_ok=True)
        for nm in ["착지", "놀람", "활", "맞음", "광선", "점프", "쓰러짐", "승리", "동전"]:
            write_wav(os.path.join(d, f"{nm}.wav"), sfx(nm) * 0.8)
        write_wav(os.path.join(d, "배경음_레트로전투.wav"), bgm(13) * 0.5)
        print("저장:", d)
    else:
        print(__doc__)
