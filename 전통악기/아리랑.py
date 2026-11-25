"""아리랑(본조 아리랑, 작자 미상 전통 민요 — 저작권 없음)을 아쟁이 연주하고 장구가 세마치 장단(9/8)으로 반주
가락: 위키백과 'Arirang' 문서의 악보(9/8, 바장조)를 그대로 옮김 (아래 SCORE, 렐러티브 표기)
아쟁 소리는 아쟁.py 의 실측 음색(실제 아쟁 산조를 잰 값), 장구는 공통.py 의 janggu (사용자 확인 2026-11-25)

사용: python -X utf8 전통악기/아리랑.py [결과.mp3] [--절 2] [--칸 0.2] [--악기 아쟁|태평소]
  --절: 몇 번 되풀이 (1절 약 29초), --칸: 8분음표 한 칸 초 (작을수록 빠름)
"""
import argparse
import importlib.util
import os
import re
import subprocess
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import 공통 as K  # noqa: E402

SR = K.SR
# 9/8, \\relative f' (첫 음은 f' 근처), 4. = 3칸, 4 = 2칸, 8 = 1칸, ~ = 붙임줄, ( ) = 이음줄(한 활로), r = 쉼
SCORE = """
c4. ~ c4 d8 c4 ( d8 ) | f4. ~ f4 g8 f4 ( g8 ) | a4. g8( a g) f4 ( d8 ) | c4. ~ ( c4 d8 c d ) r8 |
f4. ~ f4 g8 f4 ( g8 ) | a4 ( g8 ) f4 ( d8 ) c4 ( d8 ) | f4. ~ f4 g8 f4.| f4. ~ f4. r4. |
c'4. ~ c c | c4. a4. g4. | a4. g4 a8 f4 ( d8 ) | c4. ~ ( c4 d8 c d ) r8 |
f4. ~ f4 g8 f4 ( g8 ) | a4 ( g8 ) f4 ( d8 ) c4 ( d8 ) | f4. ~ f4 g8 f4.| f4. ~ f4. r4.
"""
STEP = {"c": 0, "d": 2, "e": 4, "f": 5, "g": 7, "a": 9, "b": 11}


def parse(score, start=65):
    """렐러티브 표기 → [(MIDI 또는 None(쉼), 칸 수)] (붙임줄은 합침)"""
    toks = re.findall(r"([a-gr])([',]*)(\d*)(\.?)|(~)", score.replace("(", " ").replace(")", " "))
    out, prev, dur, tie = [], start, 2, False
    for name, octs, d, dot, tilde in toks:
        if tilde:
            tie = True
            continue
        if d:
            dur = {"4": 2, "8": 1, "2": 4}[d] * (1.5 if dot else 1)
        elif dot:
            dur = dur * 1.5
        if name == "r":
            out.append((None, dur))
            tie = False
            continue
        cands = [o * 12 + STEP[name] for o in range(2, 9)]
        m = min(cands, key=lambda x: abs(x - prev))          # 앞 음과 가장 가까운 옥타브
        m += 12 * octs.count("'") - 12 * octs.count(",")
        prev = m
        if tie and out and out[-1][0] == m:
            out[-1] = (m, out[-1][1] + dur)
        else:
            out.append((m, dur))
        tie = False
    return out


def load_ajaeng():
    spec = importlib.util.spec_from_file_location("ajaeng", os.path.join(HERE, "아쟁.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def render(verses=2, unit=0.2, seed=3, inst="아쟁"):
    """inst: '아쟁' 또는 '태평소'(한 옥타브 올려 연주, 떨림 작게 — 실제 호적 산조를 잰 값)"""
    aj = load_ajaeng()
    p = dict(aj.PRESETS_REAL["5_실측_느린배경"], glide=0.07, fade=(0.06, 0.35), depth=40, vib_start=0.3, rough=0.32, scrape=0.07)
    up = 0
    if inst == "태평소":
        p = dict(p, timbre="태평소", depth=32, breath=0.07, bright_amp=0.02, rate=4.7, slow=0.0, vib_start=0.45, glide=0.05, fade=(0.03, 0.25))
        up = 12
    rng = np.random.default_rng(seed)
    notes = [(m + up if m is not None else None, d) for m, d in parse(SCORE)]
    bar = 9 * unit
    lead = bar                                                   # 첫 장단은 장구만
    total = lead + verses * 16 * bar + 3.0
    buf = np.zeros((int(total * SR), 2), np.float32)
    jg = K.janggu_rhythm("세마치", 1 + verses * 16, rng, end=True, unit=unit)
    k = min(len(jg), len(buf))
    buf[:k] += jg[:k] / (np.abs(jg).max() + 1e-6) * 0.42             # 장구 (아쟁보다 작게 받침)
    for v in range(verses):
        t = lead + v * 16 * bar
        phrase, t0 = [], t
        for m, d in notes + [(None, 0)]:
            if m is None:                                        # 쉼 = 한 숨(한 활)이 끝남 → 지금까지를 이어서 연주
                if phrase:
                    ns = []
                    for k, (mm, dd) in enumerate(phrase):
                        last = k == len(phrase) - 1
                        role = "shake" if (dd >= 3 * unit or last) else "plain"
                        ns.append((mm, dd, role))
                    semis, amp = aj.phrase_contour(ns, p, rng)
                    K.place(buf, aj.ajaeng_tone(semis, amp, p, rng), t0, 0.62, pan=0.12)
                t = t + d * unit if d else t
                phrase, t0 = [], t
                continue
            phrase.append((m, d * unit))
            t += d * unit
    return K.reverb(buf, rng, sec=2.0, wet=0.25)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out", nargs="?", default=os.path.join(os.path.dirname(HERE), "역사", "배경음샘플", "한국", "아쟁", "아리랑_아쟁장구.mp3"))
    ap.add_argument("--절", type=int, default=2)
    ap.add_argument("--칸", type=float, default=0.2)
    ap.add_argument("--악기", default="아쟁", choices=["아쟁", "태평소"])
    a = ap.parse_args()
    x = render(a.절, a.칸, inst=a.악기)
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
