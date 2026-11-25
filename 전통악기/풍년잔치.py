"""풍년 잔치 — 새로 지은 굿거리 가락 (사용자 요청 2026-11-25: 풍년가 악보를 구할 수 없어 같은 장단·음계로 새 곡)
  장단: 굿거리(12/8, 한 장단 12칸) · 음계: 솔·라·도·레·미 다섯 음(풍년가와 같은 평조풍, 솔로 맺음)
  1절 = 태평소 가락 + 장구·꽹과리·북 굿거리 + 징 / 2절 = 아쟁이 한 옥타브 아래에서 같이, 북이 네 장단마다 몰아침 → 끝에 덩·갱·쿵·징
  소리: 태평소·아쟁·장구·꽹과리·북·징 모두 이 저장소의 직접 합성 소리 (저작권 걱정 없음)

사용: python -X utf8 전통악기/풍년잔치.py [결과.mp3] [--칸 0.2] [--절 2]
"""
import argparse
import importlib.util
import os
import subprocess
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import 공통 as K  # noqa: E402

SR = K.SR
# 음 이름 → MIDI (솔 = G4). ' 는 한 옥타브 위
NOTE = {"솔": 67, "라": 69, "도": 72, "레": 74, "미": 76, "솔'": 79, "라'": 81, "도'": 84}
# 가락: 한 줄 = 한 장단(12칸), '음:칸', 쉼은 '-:칸'
MELODY = """
도:3 레:2 미:1 솔':3 미:3
레:2 미:1 레:2 도:1 라:6
도:3 도:2 레:1 미:2 레:1 도:2 레:1
솔:6 솔:3 -:3
솔':3 라':2 솔':1 미:3 솔':3
미:2 레:1 도:2 레:1 미:6
레:2 미:1 레:2 도:1 라:2 도:1 레:3
도:9 -:3
솔':6 솔':3 라':3
솔':2 미:1 레:2 미:1 솔':6
라':3 솔':2 미:1 레:3 도:3
레:9 -:3
미:3 솔':2 미:1 레:3 도:3
라:2 도:1 레:2 미:1 레:6
도:3 레:2 도:1 라:3 도:2 라:1
솔:9 -:3
"""


def parse(text):
    out = []
    for line in text.strip().splitlines():
        cells = 0
        for tok in line.split():
            name, n = tok.rsplit(":", 1)
            out.append((None if name == "-" else NOTE[name], int(n)))
            cells += int(n)
        assert cells == 12, f"한 장단이 12칸이 아님: {line} ({cells})"
    return out


def load(name):
    spec = importlib.util.spec_from_file_location("m_" + name, os.path.join(HERE, name + ".py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def play(aj, notes, p, unit, t, rng, up=0):
    """가락을 쉼마다 끊어 한 숨(한 활)씩 연주 → [(소리, 시작 초)]"""
    out, phrase, t0 = [], [], t
    for m, d in notes + [(None, 0)]:
        if m is None:
            if phrase:
                ns = []
                for k, (mm, dd) in enumerate(phrase):
                    last = k == len(phrase) - 1
                    role = "shake" if (dd >= 3 * unit or last) else ("push" if k == 0 and dd >= 2 * unit else "plain")
                    ns.append((mm + up, dd, role))
                semis, amp = aj.phrase_contour(ns, p, rng)
                out.append((aj.ajaeng_tone(semis, amp, p, rng), t0))
            t += d * unit
            phrase, t0 = [], t
            continue
        phrase.append((m, d * unit))
        t += d * unit
    return out


def render(unit=0.2, verses=2, seed=5):
    aj = load("아쟁")
    rng = np.random.default_rng(seed)
    notes = parse(MELODY)
    bars = len(MELODY.strip().splitlines())
    bar = 12 * unit
    taep = dict(aj.PRESETS_REAL["5_실측_느린배경"], timbre="태평소", depth=30, rate=4.8, slow=0.0, vib_start=0.4,
                glide=0.04, fade=(0.03, 0.22), breath=0.07, bright_amp=0.02, push_st=(0.6, 1.0))
    ajg = dict(aj.PRESETS_REAL["5_실측_느린배경"], depth=40, glide=0.06, fade=(0.05, 0.3), vib_start=0.3)
    lead = bar                                                               # 첫 장단은 타악만
    total = lead + verses * bars * bar + 4.0
    buf = np.zeros((int(total * SR), 2), np.float32)

    def add(part, t0, gain):
        i0 = int(t0 * SR)
        k = min(len(part), len(buf) - i0)
        if k > 0:
            buf[i0:i0 + k] += part[:k] / (np.abs(part).max() + 1e-6) * gain

    cyc = 1 + verses * bars
    add(K.janggu_rhythm("굿거리", cyc, rng, end=False, unit=unit), 0.0, 0.42)
    add(K.kkwaenggwari_rhythm("굿거리", cyc, rng, unit=unit, end=False), 0.0, 0.6)
    first = 1 + bars                                                         # 북 가락: 1절은 그대로, 2절은 네 장단마다 끝을 몰아침
    add(K.buk_rhythm("굿거리", first, rng, unit=unit), 0.0, 0.9)
    add(K.buk_rhythm("굿거리", cyc - first, rng, unit=unit, fill_every=4), first * bar, 0.95)
    for c in range(cyc):                                                     # 징: 네 장단마다(2절은 두 장단마다)
        b = c * bar
        if c % (2 if c > bars else 4) == 0:
            K.place(buf, K.gong(110, 3.0, bend=0.02, rng=rng), b, 0.2, 0.0)
    for v in range(verses):
        t = lead + v * bars * bar
        for snd, t0 in play(aj, notes, taep, unit, t, rng):
            K.place(buf, snd, t0, 0.62, 0.1)
        if v >= 1:                                                           # 2절: 아쟁이 한 옥타브 아래에서 같이
            for snd, t0 in play(aj, notes, ajg, unit, t, rng, up=-12):
                K.place(buf, snd, t0, 0.42, -0.15)
    end = lead + verses * bars * bar
    for snd, g, pan in ((K.janggu("덩", rng), 0.55, 0.0), (K.kkwaenggwari("갱", rng), 0.45, 0.3),
                        (K.big_drum(62 * K.BUK_LOW, 2.0, rng), 0.5, -0.35), (K.gong(110, 3.5, bend=0.02, rng=rng), 0.4, 0.0)):
        K.place(buf, snd, end, g, pan)
    return K.reverb(buf, rng, sec=1.8, wet=0.2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out", nargs="?", default=os.path.join(os.path.dirname(HERE), "역사", "배경음샘플", "한국", "풍년잔치.mp3"))
    ap.add_argument("--칸", type=float, default=0.2)
    ap.add_argument("--절", type=int, default=2)
    a = ap.parse_args()
    x = render(a.칸, a.절)
    wp = a.out[:-4] + ".wav"
    K.write_wav(wp, x)
    try:
        import imageio_ffmpeg
        ff = imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        ff = "ffmpeg"
    subprocess.run([ff, "-y", "-loglevel", "error", "-i", wp, "-b:a", "160k", a.out], check=True)
    os.remove(wp)
    print("OK", a.out, f"{len(x) / SR:.1f}초")
    return 0


if __name__ == "__main__":
    sys.exit(main())
