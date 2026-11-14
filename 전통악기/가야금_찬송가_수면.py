"""가야금·해금·장구 찬송가 연주 — 수면용 긴 연주곡 (30분 넘게)
악보: 찬송가/악보/*.abc (Open Hymnal, 공개 저작물 — 4성부 그대로: 소프라노=멜로디, 알토·테너=가운데 화음, 베이스=낮은 줄)
악기 소리: 컴퓨터로 직접 합성 (가야금_찬송가.py 의 가야금·장구, 공통.py 의 해금) → 녹음 음원 없음

한 곡을 여러 번 돌며 악기 역할을 바꿈 (지루하지 않게, 소리는 점점 잔잔하게)
  가야금 : 가야금이 노래(꾸밈: 농현·꺾는 음·꾸밈음), 낮은 가야금 줄이 베이스
  해금   : 해금이 노래, 가야금은 펼침화음(베이스-테너-알토-테너) 반주, 장구 아주 작게(첫 박 덩, 가운데 덕)
  함께   : 가야금 노래 + 해금이 뒤따라 은은히, 가야금 베이스, 장구
1부 = 그 편의 곡 × (가야금·해금·함께), 2부 = 같은 곡 × (가야금·해금) 조금 더 느리고 작게, 마지막 곡은 장구 없이 → 끝 30초 서서히 작아짐

사용법: python -X utf8 전통악기/가야금_찬송가_수면.py [결과 폴더] [--편 1|2]   (편마다 곡 묶음이 다름, 기본 1편)   → 연주곡.mp3 + 곡순서(유튜브 챕터).txt
"""
import os
import subprocess
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import 공통 as K  # noqa: E402
import 찬송가_악보 as A  # noqa: E402
from 가야금_찬송가 import gayageum, jango  # noqa: E402

SR = K.SR
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# (악보 파일, 한국어 제목, 통일찬송가 장, 4분음표 빠르기) — 수면용으로 느리게
ALBUMS = {   # 편마다 따로 만듦. 장 번호를 확인하지 못한 곡은 None (제목만 표시)
    "1": [   # 1편 (35분)
        ("Amazing_Grace", "나 같은 죄인 살리신", 405, 64),
        ("It_Is_Well_With_My_Soul", "내 평생에 가는 길", 470, 58),
        ("Nearer_My_God_To_Thee", "내 주를 가까이 하게 함은", 364, 80),
        ("What_A_Friend_We_Have_In_Jesus", "죄짐 맡은 우리 구주", 487, 60),
        ("Blessed_Assurance", "예수를 나의 구주 삼고", 204, 78),
        ("Under_His_Wings", "주 날개 밑 내가 편안히 쉬네", 478, 84),
    ],
    "2": [   # 2편 — 마지막은 저녁 노래로 잠들기 좋게
        ("Holy_Holy_Holy", "거룩 거룩 거룩", None, 70),
        ("Jesus_Loves_Me", "예수 사랑하심은", None, 70),
        ("I_Need_Thee_Every_Hour", "주 음성 외에는", None, 78),
        ("Rock_Of_Ages", "만세 반석 열리니", None, 82),
        ("More_Love_To_Thee", "내 구주 예수를 더욱 사랑", None, 64),
        ("Pass_Me_Not", "인애하신 구세주여", None, 70),
        ("When_I_Survey", "주 달려 죽은 십자가", None, 72),
        ("Abide_With_Me", "때 저물어서 날이 어두니", None, 58),
    ],
}


def sounding(notes, t):
    """t 박에 울리고 있는 음 (없으면 None)"""
    for st, d, m in notes:
        if st <= t + 1e-6 < st + d:
            return m
    return None


def fit(m, lo, hi):
    while m < lo:
        m += 12
    while m > hi:
        m -= 12
    return m


def haegeum(freq, dur, long_note):
    """해금 한 음: 활로 켜는 콧소리 + 긴 음은 깊은 떨림"""
    return K.bowed(freq, dur, band=(650, 3400), vib_rate=4.6, vib=0.013 if long_note else 0.005, attack=0.14, nasal=1.0)


def render_round(score, bpm, style, rng, gain=1.0, use_jango=True, sweep=False):
    """악보 한 바퀴 → (스테레오 소리, 길이 초)"""
    beat = 60.0 / bpm
    num, den = score["meter"]
    bar_q = num * 4 / den
    v = score["voices"]
    mel, alto, ten, bass = v["S1V1"], v["S1V2"], v["S2V1"], v["S2V2"]
    total_q = mel[-1][0] + mel[-1][1]
    lead = 2.2 if sweep else 0.0
    sec = lead + total_q * beat + 3.0
    buf = np.zeros((int(sec * SR) + SR, 2), np.float32)
    T = lambda q: lead + q * beat
    tonic = A.BASE[score["key"][0]] + (-1 if score["key"][1:] == "b" else 0)

    if sweep:   # 곡 시작: 훑기 (작게)
        pent = [0, 2, 4, 7, 9]
        run = [m for m in range(84, 57, -1) if (m - tonic) % 12 in pent]
        for i, m in enumerate(run):
            K.place(buf, gayageum(K.hz(m), 2.2, rng, bright=0.45), 0.05 + i * 0.075, (0.26 - i * 0.01) * gain, pan=0.3 - i * 0.04)

    # 베이스 (가야금 낮은 줄) — 가야금·함께
    if style in ("가야금", "함께"):
        for st, d, m in bass:
            K.place(buf, gayageum(K.hz(fit(m, 38, 55)), min(d * beat + 0.5, 4.5), rng, bright=0.22, nong=0.006 if d >= 2 else 0),
                    T(st) + rng.uniform(0, 0.012), 0.36 * gain, pan=-0.35)

    # 펼침화음 반주 — 해금 판 (베이스-테너-알토-테너를 박마다 차례로)
    if style == "해금":
        pulse = 1.5 if den == 8 else 1.0
        q, k = 0.0, 0
        while q < total_q - 0.01:
            order = [bass, ten, alto, ten]
            m = sounding(order[k % 4], q) or sounding(bass, q)
            if m is not None:
                lo, hi = [(38, 55), (50, 64), (55, 69), (50, 64)][k % 4]
                K.place(buf, gayageum(K.hz(fit(m, lo, hi)), pulse * beat * 2.2, rng, bright=0.25),
                        T(q) + rng.uniform(0, 0.012), (0.34 if k % 4 == 0 else 0.22) * gain, pan=-0.3)
            q += pulse
            k += 1

    # 장구 — 첫 박 덩, 마디 가운데 덕 (아주 작게)
    if use_jango and style in ("해금", "함께"):
        first_bar = score["bars"][0] - bar_q
        b = first_bar
        while b < total_q - 0.01:
            if b >= 0:
                K.place(buf, jango("덩", rng), T(b), 0.11 * gain, pan=0.15)
            mid = b + (bar_q / 3 * 2 if num in (3, 9) else bar_q / 2)
            if 0 <= mid < total_q:
                K.place(buf, jango("덕", rng), T(mid), 0.06 * gain, pan=0.15)
            b += bar_q

    # 멜로디
    prev = None
    for i, (st, d, m) in enumerate(mel):
        dur = d * beat
        long_note = d >= 2
        if style in ("가야금", "함께"):
            push = 0.035 if (prev is not None and 0 < m - prev <= 3 and d >= 1) else 0.0
            nong = 0.022 if long_note else (0.008 if d >= 1 else 0.0)
            if long_note and rng.random() < 0.3:   # 위 이웃음에서 떨어지는 짧은 꾸밈음
                K.place(buf, gayageum(K.hz(m + 2), 0.2, rng, bright=0.45), max(0.0, T(st) - 0.09), 0.25 * gain, pan=0.1)
            K.place(buf, gayageum(K.hz(m), dur + 0.6, rng, nong=nong, push=push, bright=0.42), T(st) + rng.uniform(0, 0.02), 0.8 * gain, pan=0.1)
        if style == "해금":
            K.place(buf, haegeum(K.hz(m), dur * 1.06 + 0.05, long_note), T(st), 0.42 * gain, pan=0.05)
        if style == "함께":
            K.place(buf, haegeum(K.hz(m), dur * 1.06 + 0.05, long_note), T(st) + 0.05, 0.15 * gain, pan=-0.15)
        prev = m
    end = T(total_q) + 0.6   # 다음 바퀴는 마지막 음이 울린 뒤
    return buf, end


def song_block(name, bpm, styles, rng, gain, use_jango, last=False):
    score = A.read(os.path.join(ROOT, "찬송가", "악보", name + ".abc"))
    pieces, t = [], 0.0
    for i, st in enumerate(styles):
        b, end = render_round(score, bpm, st, rng, gain=gain, use_jango=use_jango, sweep=(i == 0))
        pieces.append((t, b))
        t += end
    total = t + 3.5
    out = np.zeros((int(total * SR) + 2 * SR, 2), np.float32)
    for t0, b in pieces:
        i0 = int(t0 * SR)
        n = min(len(b), len(out) - i0)
        out[i0:i0 + n] += b[:n]
    out = out[: int(total * SR)]
    out = K.reverb(out, rng, sec=2.6, wet=0.24)
    # 소리 크기: 곡마다 평균 크기를 맞추고(gain 반영) 끝은 부드럽게
    rms = np.sqrt(np.mean(out ** 2)) + 1e-9
    out = out * (0.08 * gain / rms)
    tail = np.clip((total - np.arange(len(out)) / SR) / (30.0 if last else 2.5), 0, 1)[:, None]
    return np.clip(out * tail, -0.95, 0.95), total


def write_wav(path, x):
    import wave
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((np.clip(x, -1, 1) * 32767).astype(np.int16).tobytes())


def main(argv):
    album = argv[argv.index("--편") + 1] if "--편" in argv else "1"
    if "--편" in argv:
        i = argv.index("--편")
        argv = argv[:i] + argv[i + 2:]
    SONGS = ALBUMS[album]
    out_dir = argv[0] if argv else os.path.join(ROOT, "찬송가", "가야금_수면" + ("" if album == "1" else album))
    os.makedirs(out_dir, exist_ok=True)
    rng = np.random.default_rng(2026)
    plan = [(s, ["가야금", "해금", "함께"], 1.0, 1.0, True) for s in SONGS]                          # 1부
    plan += [(s, ["가야금", "해금"], 0.92, 0.8, s is not SONGS[-1]) for s in SONGS]                  # 2부: 느리고 작게
    parts, chapters, t = [], [], 0.0
    for k, ((name, ko, no, bpm), styles, slow, gain, jg) in enumerate(plan):
        last = k == len(plan) - 1
        x, sec = song_block(name, bpm * slow, styles, rng, gain, jg, last=last)
        p = os.path.join(out_dir, f"_{k:02d}.wav")
        write_wav(p, x)
        parts.append(p)
        chapters.append((t, f"{ko} (통일찬송가 {no}장)" if no else ko))
        print(f"{k + 1:2d}/{len(plan)} {ko}  {sec / 60:.1f}분", flush=True)
        t += sec
    lst = os.path.join(out_dir, "_목록.txt")
    with open(lst, "w", encoding="utf-8") as f:
        f.writelines(f"file '{os.path.abspath(p)}'\n" for p in parts)
    mp3 = os.path.join(out_dir, "가야금_찬송가_연주곡.mp3")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-b:a", "192k", mp3], check=True)
    for p in parts + [lst]:
        os.remove(p)
    with open(os.path.join(out_dir, "곡순서_유튜브챕터.txt"), "w", encoding="utf-8") as f:
        for i, (s, title) in enumerate(chapters):
            f.write(f"{int(s // 3600)}:{int(s % 3600 // 60):02d}:{int(s % 60):02d} {title}{'  (2부)' if i >= len(SONGS) else ''}\n")
    print(f"완성: {mp3}  전체 {t / 60:.1f}분")


if __name__ == "__main__":
    main(sys.argv[1:])
