"""태평소(호적) 샘플 — 실제 호적 산조 녹음(1969년 LP, 인터넷 아카이브)을 연주분석.py 로 잰 값으로 맞춤 (녹음은 숫자만 재는 데 씀)
  음역 MIDI 70~86 · 긴 음은 거의 곧게, 떨림 1초 4.7번·작게(±20센트쯤) · 아래에서 밀어 올리며 들어가는 음 · 가끔 크게 출렁이는 꾸밈
  음색 = 공통.TAEP_HARM_DB(잰 배음 세기) + 서가 떠는 거친 결 + 숨소리 (공통.wind_tone)
가락 짜기·꾸밈(농현·퇴성·추성·꾸밈음)은 아쟁.py 의 것을 그대로 쓰고 소리만 태평소로 (timbre='태평소')

사용: python -X utf8 전통악기/태평소.py [결과폴더]
  → 1_태평소_독주.mp3 · 2_태평소_풍물자진모리.mp3(장구·북·징·꽹과리) · 3_태평소_아리랑.mp3(장구 세마치) · 태평소_전체듣기.mp3
"""
import importlib.util
import os
import subprocess
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import 공통 as K  # noqa: E402

SR = K.SR


def load(name):
    spec = importlib.util.spec_from_file_location("m_" + name, os.path.join(HERE, name + ".py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


AJ = load("아쟁")
GYEMYEON, PYEONG = AJ.GYEMYEON, AJ.PYEONG
BASE = dict(timbre="태평소", depth=32, rate=4.7, slow=0.0, vib_start=0.45, rough=0.3, scrape=0.0, drone=(0.0, 0.0),
            breath=0.07, buzz=0.18, bright_amp=0.02)
PRESETS = {
    "1_태평소_독주": dict(BASE, root=75, span=12, fall=0.15, push=0.30, note=(0.7, 2.6), glide=0.06, mode=GYEMYEON,
                      fade=(0.05, 0.3)),
    "2_태평소_풍물자진모리": dict(BASE, root=74, span=12, depth=24, fall=0.10, push=0.15, grace=0.25, glide=0.03, mode=PYEONG,
                          unit=0.15, beats=[1, 1, 2, 2, 3], steps=(6, 11), rest=(1, 3), janggu="자진모리", fade=(0.02, 0.2)),
}


def pungmul_drums(buf, unit, start, rng):
    """풍물 받침: 장단 첫 칸마다 북, 두 장단마다 징, 꽹과리 자진모리 (장구는 아쟁.bed 가 자진모리로 침)"""
    bar = 12 * unit
    c, t = 0, start
    while t < len(buf) / SR - 1.0:
        K.place(buf, K.big_drum(62 * K.BUK_LOW, 1.2, rng), t, 0.45, pan=-0.2)
        K.place(buf, K.big_drum(62 * K.BUK_LOW, 0.8, rng), t + 6 * unit, 0.3, pan=-0.2)
        if c % 2 == 0:
            K.place(buf, K.gong(110, 3.0, bend=0.02, rng=rng), t, 0.22, pan=0.25)
        kk = K.kkwaenggwari_rhythm("자진모리", 1, rng, unit=unit, end=False)              # 꽹과리 (2026-11-25)
        K.place(buf, kk[:, 0] + kk[:, 1], t, 0.55, pan=0.35)
        c += 1
        t += bar


def ffmpeg():
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return "ffmpeg"


def save(x, mp3):
    wp = mp3[:-4] + ".wav"
    K.write_wav(wp, x)
    subprocess.run([ffmpeg(), "-y", "-loglevel", "error", "-i", wp, "-b:a", "160k", mp3], check=True)
    os.remove(wp)
    print("OK", mp3)


def main(out):
    os.makedirs(out, exist_ok=True)
    files = []
    for name, p in PRESETS.items():
        x = AJ.bed(30, p, seed=11)
        if "janggu" in p:
            x = x / (np.abs(x).max() + 1e-6)
            pungmul_drums(x, p["unit"], 0.4, np.random.default_rng(4))
        f = os.path.join(out, name + ".mp3")
        save(x, f)
        files.append(f)
    ar = load("아리랑")
    f = os.path.join(out, "3_태평소_아리랑.mp3")
    save(ar.render(2, 0.2, inst="태평소"), f)
    files.append(f)
    lst = os.path.join(out, "_목록.txt")
    with open(lst, "w", encoding="utf-8") as fp:
        fp.writelines(f"file '{os.path.abspath(m)}'\n" for m in files)
    subprocess.run([ffmpeg(), "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-b:a", "160k",
                    os.path.join(out, "태평소_전체듣기.mp3")], check=True)
    os.remove(lst)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(HERE), "역사", "배경음샘플", "한국", "태평소")))
