"""꽹과리 샘플 + 사물놀이(꽹과리·장구·북·징) — 소리 만드는 법은 공통.py 의 kkwaenggwari · kkwaenggwari_rhythm
→ 역사/배경음샘플/타악/꽹과리/ : 0_소리하나씩.mp3(갱·깨·깻·지·갠지갱, 이어서 갱·깻을 약하게→세게) · 1_꽹과리_휘모리.mp3 · 2_사물놀이.mp3(자진모리 → 휘모리로 빨라짐) · 꽹과리_전체듣기.mp3
사용: python -X utf8 전통악기/꽹과리.py [결과폴더]"""
import os
import subprocess
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import 공통 as K  # noqa: E402

SR = K.SR


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


def mix(buf, part, t0, gain):
    i0 = int(t0 * SR)
    k = min(len(part), len(buf) - i0)
    if k > 0:
        buf[i0:i0 + k] += part[:k] / (np.abs(part).max() + 1e-6) * gain


def samulnori(rng, sec_jajin=10.0, sec_hwi=10.0):
    """사물놀이: 징 한 번으로 열고 → 자진모리(한 칸 0.15초) → 휘모리(한 칸 0.12초) → 다 같이 '덩·갱·쿵·징'으로 맺음
    꽹과리(오른쪽)·장구(가운데)·북(왼쪽)·징(장단 첫 칸, 두 장단마다)"""
    parts = [("자진모리", 0.15, sec_jajin), ("휘모리", 0.12, sec_hwi)]
    total = 1.2 + sum(p[2] for p in parts) + 4.0
    buf = np.zeros((int(total * SR), 2), np.float32)
    K.place(buf, K.gong(110, 3.0, bend=0.02, rng=rng), 0.0, 0.5, 0.0)
    t = 1.2
    for name, unit, sec in parts:
        cyc = int(round(sec / (12 * unit)))
        mix(buf, K.kkwaenggwari_rhythm(name, cyc, rng, unit=unit, end=False), t, 1.5)
        mix(buf, K.janggu_rhythm(name, cyc, rng, end=False, unit=unit), t, 0.55)
        mix(buf, K.buk_rhythm(name, cyc, rng, unit=unit, fill_every=4), t, 0.95)
        for c in range(cyc):
            b = t + c * 12 * unit
            if c % 2 == 0:
                K.place(buf, K.gong(110, 2.5, bend=0.02, rng=rng), b, 0.22, 0.0)
        t += cyc * 12 * unit
    for snd, g, pan in ((K.janggu("덩", rng), 0.6, 0.0), (K.kkwaenggwari("갱", rng), 0.85, 0.3),
                        (K.big_drum(62 * K.BUK_LOW, 2.0, rng), 0.6, -0.35), (K.gong(110, 3.5, bend=0.02, rng=rng), 0.45, 0.0)):
        K.place(buf, snd, t, g, pan)
    return buf


def main(out):
    os.makedirs(out, exist_ok=True)
    rng = np.random.default_rng(7)
    kinds = [("갱", 1.0), ("깨", 1.0), ("깻", 1.0), ("지", 1.0), ("갠지갱", 1.0),     # 소리 종류
             ("갱", 0.4), ("갱", 0.7), ("갱", 1.1), ("깻", 0.4), ("깻", 0.7), ("깻", 1.1)]   # 같은 소리를 약하게 → 세게
    one = np.zeros((int((len(kinds) + 1) * 0.8 * SR), 2), np.float32)
    for i, (k, f) in enumerate(kinds):
        K.place(one, K.kkwaenggwari(k, rng, force=f), 0.3 + i * 0.8, 1.0)
    files = [os.path.join(out, "0_소리하나씩.mp3")]
    save(one, files[0])
    f = os.path.join(out, "1_꽹과리_휘모리.mp3")
    save(K.kkwaenggwari_rhythm("휘모리", 5, rng, unit=0.12), f)
    files.append(f)
    f = os.path.join(out, "2_사물놀이.mp3")
    save(samulnori(rng), f)
    files.append(f)
    lst = os.path.join(out, "_목록.txt")
    with open(lst, "w", encoding="utf-8") as fp:
        fp.writelines(f"file '{os.path.abspath(m)}'\n" for m in files)
    subprocess.run([ffmpeg(), "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-b:a", "160k",
                    os.path.join(out, "꽹과리_전체듣기.mp3")], check=True)
    os.remove(lst)
    return 0


if __name__ == "__main__":
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(here, "역사", "배경음샘플", "타악", "꽹과리")))
