"""가야금으로 찬송가 연주 — 악보(멜로디 글자)를 가야금 소리로 직접 합성 (녹음 음원 없음, 저작권 끝난 곡만)

  멜로디 적는 법: 'D4:1 G4:2 B4:0.5 …' (음이름+옥타브:박자, 쉼표는 R:1) — 쇼츠 메이커의 노래 멜로디와 같은 형식
  화음: 마디마다 'G G C G …' (첫 마디 = 못갖춘마디(시작 음) 다음 마디부터)

  가야금다운 소리:
   - 긴 음(2박 이상)은 농현(줄을 눌렀다 놓았다 하며 흔드는 떨림)
   - 한 음 아래에서 올라오는 음은 밀어 올리는 소리(꺾는 음)
   - 시작은 훑기(줄을 위에서 아래로 쓸어내림), 아래에는 낮은 가야금 줄로 반주(뿌리음-5도-옥타브)
  판: A = 가야금 독주(반주 포함), B = 가야금 + 해금(멜로디를 은은하게 같이) + 장구(세마치 느낌, 아주 작게)

  사용법: python -X utf8 전통악기/가야금_찬송가.py <결과 폴더> [곡이름 …]   (곡이름 없으면 전부)
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import 공통 as K  # noqa: E402

SR = K.SR
NOTE_BASE = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
CHORD_ROOT = {"C": 48, "D": 50, "E": 52, "F": 53, "G": 43, "A": 45, "B": 47}   # 반주 뿌리음 (낮은 줄)

# 저작권이 끝난 찬송가 (작곡가 세상 떠난 해 1955년 이전)
SONGS = {
    "나같은죄인살리신": {   # Amazing Grace, 미국 민요 (1829), 3/4박자, 사장조
        "beats": 3, "bpm": 66, "tonic": "G",
        "pickup": 1,   # 못갖춘마디: 첫 음이 1박
        "melody": ("D4:1 "
                   "G4:2 B4:0.5 G4:0.5 B4:2 A4:1 G4:2 E4:1 D4:2 D4:1 "
                   "G4:2 B4:0.5 G4:0.5 B4:2 A4:1 D5:5 B4:1 "
                   "D5:1.5 B4:0.5 D5:0.5 B4:0.5 G4:2 D4:1 E4:1.5 G4:0.5 G4:0.5 E4:0.5 D4:2 D4:1 "
                   "G4:2 B4:0.5 G4:0.5 B4:2 A4:1 G4:6"),
        "chords": "G G C G G G D D G G C G G D G G",
    },
}


def midi_of(name):
    acc = 1 if "#" in name else (-1 if name[1:2] == "b" else 0)
    return 12 * (int(name[-1]) + 1) + NOTE_BASE[name[0].upper()] + acc


def parse(text):
    out = []
    for tok in text.split():
        n, _, b = tok.partition(":")
        out.append((None if n.upper() == "R" else midi_of(n), float(b or 1)))
    return out


def gayageum(freq, dur, rng, nong=0.0, push=0.0, bright=0.4, damp=0.9965):
    """가야금 한 음: 명주실 줄을 뜯은 소리 + 농현(nong: 떨림 깊이) + 밀어 올림(push: 아래에서 올라오는 정도)"""
    from scipy.signal import butter, lfilter
    n = int(dur * SR)
    y = K.pluck(freq, dur + 0.3, damp=damp, bright=bright, rng=rng)
    t = np.arange(len(y)) / SR
    ratio = np.ones_like(t)
    if push:   # 줄을 눌러 음을 끌어올림 (꺾는 소리)
        ratio *= 1 - push * np.exp(-t / 0.09)
    if nong:   # 농현: 조금 기다렸다가 천천히 깊게 흔듦
        ramp = np.clip((t - 0.35) / 0.6, 0, 1)
        ratio *= 1 + nong * ramp * np.sin(2 * np.pi * 3.6 * np.clip(t - 0.35, 0, None))
    pos = np.clip(np.cumsum(ratio) - ratio[0], 0, len(y) - 1)
    y = np.interp(pos, np.arange(len(y)), y)[:n]
    # 명주실·오동나무 울림: 높은 쇳소리를 깎고 몸통 울림(250~900Hz)을 살짝 더함
    y = lfilter(*butter(2, 3800 / (SR / 2)), y)
    y = y + 0.35 * lfilter(*butter(2, [250 / (SR / 2), 900 / (SR / 2)], "band"), y)
    # 술대 소리처럼 뜯는 순간의 짧은 '틱'
    tick = rng.standard_normal(int(0.012 * SR)) * np.exp(-np.arange(int(0.012 * SR)) / (0.002 * SR))
    y[:len(tick)] += 0.08 * lfilter(*butter(2, [1500 / (SR / 2), 5000 / (SR / 2)], "band"), tick)
    env = np.clip((dur - np.arange(n) / SR) / 0.25, 0, 1)   # 다음 음 전에 살짝 손으로 막음
    y = y * env
    return (y / (np.abs(y).max() + 1e-6)).astype(np.float32)


def jango(kind, rng):
    """장구 한 번: '덩'(양손: 북편 쿵 + 채편 딱), '쿵'(북편), '덕'(채편)"""
    if kind == "쿵":
        return K.frame_drum(0.7, True, rng)
    if kind == "덕":
        return K.frame_drum(0.25, False, rng) * 0.8
    return K.frame_drum(0.7, True, rng) + 0.6 * np.pad(K.frame_drum(0.25, False, rng), (0, int(0.45 * SR)))[: int(0.7 * SR)]


def render(song, version, seed=7):
    rng = np.random.default_rng(seed)
    beat = 60.0 / song["bpm"]
    bar = beat * song["beats"]
    notes = parse(song["melody"])
    chords = song["chords"].split()
    pentatonic = [0, 2, 4, 7, 9]   # 훑기·꾸밈에 쓰는 오음
    tonic = NOTE_BASE[song["tonic"]]

    intro = 1.2 + bar            # 훑기 + 반주 한 마디
    t_mel0 = intro + bar - song["pickup"] * beat   # 첫 음(못갖춘마디)은 둘째 반주 마디 끝에
    body_len = sum(b for _, b in notes) * beat
    total = t_mel0 + body_len + 4.5
    buf = np.zeros((int(total * SR), 2), np.float32)

    # 1) 훑기: 높은 줄에서 낮은 줄로 쓸어내림
    sweep = [m for m in range(86, 54, -1) if (m - tonic) % 12 in pentatonic]
    for i, m in enumerate(sweep):
        K.place(buf, gayageum(K.hz(m), 2.5, rng, bright=0.5), 0.05 + i * 0.07, 0.35 - i * 0.012, pan=0.3 - i * 0.04)
    K.place(buf, gayageum(K.hz(CHORD_ROOT[song['tonic']]), 3.0, rng, nong=0.012), 0.05 + len(sweep) * 0.07, 0.5, pan=-0.2)

    # 2) 반주: 마디마다 뿌리음 - 5도 - 옥타브 (낮은 줄, 작게). 앞에 반주 두 마디(전주) + 곡 마디들
    bar_starts = [intro - bar + bar * k for k in range(1, 3)]
    bar_chords = [chords[0], chords[0]]
    first_full = t_mel0 + song["pickup"] * beat
    for k, c in enumerate(chords):
        bar_starts.append(first_full + k * bar)
        bar_chords.append(c)
    for t0, c in zip(bar_starts, bar_chords):
        r = CHORD_ROOT[c[0]]
        for j, (iv, g) in enumerate([(0, 0.42), (7, 0.26), (12, 0.24)][: song["beats"]]):
            K.place(buf, gayageum(K.hz(r + iv), beat * (2.2 if j == 0 else 1.2), rng, bright=0.25, nong=0.006 if j == 0 else 0),
                    t0 + j * beat + rng.uniform(0, 0.015), g, pan=-0.35)
        if version == "B":   # 장구: 첫 박 덩, 셋째 박 덕 (아주 작게)
            K.place(buf, jango("덩", rng), t0, 0.16, pan=0.15)
            K.place(buf, jango("덕", rng), t0 + 2 * beat, 0.09, pan=0.15)

    # 3) 멜로디: 가야금 (꾸밈: 긴 음 농현, 아래에서 올라오는 음은 밀어 올림, 가끔 위 꾸밈음)
    t, prev = t_mel0, None
    for i, (m, b) in enumerate(notes):
        dur = b * beat
        if m is not None:
            long_note = b >= 2
            push = 0.035 if (prev is not None and 0 < m - prev <= 3 and b >= 1) else 0.0
            nong = 0.022 if long_note else (0.008 if b >= 1 else 0.0)
            if long_note and rng.random() < 0.35:   # 위 이웃음에서 짧게 떨어지는 꾸밈음
                K.place(buf, gayageum(K.hz(m + 2), 0.2, rng, bright=0.5), t - 0.09, 0.3, pan=0.1)
            K.place(buf, gayageum(K.hz(m), dur + 0.6, rng, nong=nong, push=push, bright=0.45), t + rng.uniform(0, 0.02), 0.85, pan=0.1)
            if version == "B" and t > t_mel0 + body_len / 2 - 1:   # 해금: 후반부에 멜로디를 같은 높이로 은은하게
                hg = K.bowed(K.hz(m), dur * 1.05, band=(700, 3600), vib_rate=4.5, vib=0.012 if long_note else 0.005, attack=0.12, nasal=1.0)
                K.place(buf, hg, t + 0.04, 0.16, pan=-0.15)
            prev = m
        t += dur

    # 4) 끝맺음: 으뜸음을 한 옥타브 위에서 한 번 더, 낮은 줄 한 번
    K.place(buf, gayageum(K.hz(CHORD_ROOT[song['tonic']] + 24), 3.5, rng, nong=0.015, bright=0.35), t + 0.3, 0.4, pan=0.25)
    K.place(buf, gayageum(K.hz(CHORD_ROOT[song['tonic']]), 4.0, rng, bright=0.25), t + 0.3, 0.35, pan=-0.3)

    fade = np.clip((total - np.arange(len(buf)) / SR) / 2.0, 0, 1)[:, None]
    return K.reverb(buf * fade, rng, sec=2.4, wet=0.22)


def main(argv):
    out_dir = argv[0] if argv else "찬송가/가야금샘플"
    names = argv[1:] or list(SONGS)
    os.makedirs(out_dir, exist_ok=True)
    import subprocess
    for name in names:
        for ver, label in [("A", "가야금독주"), ("B", "가야금_해금_장구")]:
            wav = os.path.join(out_dir, f"{name}_{ver}_{label}.wav")
            K.write_wav(wav, render(SONGS[name], ver))
            mp3 = wav[:-4] + ".mp3"
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", wav, "-b:a", "192k", mp3], check=True)
            os.remove(wav)
            print("만듦:", mp3)


if __name__ == "__main__":
    main(sys.argv[1:])
