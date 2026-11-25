"""장구 소리 샘플 만들기 (소리 만드는 법은 공통.py 의 janggu · janggu_rhythm · JANGGU_RHYTHMS)
→ 역사/배경음샘플/타악/장구/ : 0_소리하나씩.mp3 (덩·쿵·덕·기덕·더러러러) + 장단별(굿거리·자진모리·휘모리·세마치) + 장구_전체듣기.mp3
사용: python -X utf8 전통악기/장구.py [결과폴더]"""
import os
import subprocess
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import 공통 as K  # noqa: E402


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
    rng = np.random.default_rng(5)
    kinds = ["덩", "쿵", "덕", "기덕", "더러러러"]
    one = np.zeros((int(len(kinds) * 1.0 * K.SR + K.SR), 2), np.float32)
    for i, k in enumerate(kinds):                       # 하나씩 1초 간격
        K.place(one, K.janggu(k, rng), 0.3 + i * 1.0, 1.0)
    files = [os.path.join(out, "0_소리하나씩.mp3")]
    save(one, files[0])
    for i, name in enumerate(K.JANGGU_RHYTHMS, 1):
        unit, cells, _ = K.JANGGU_RHYTHMS[name]
        cyc = max(3, int(np.ceil(8 / (unit * cells))))   # 8초쯤
        f = os.path.join(out, f"{i}_{name}.mp3")
        save(K.janggu_rhythm(name, cyc, rng), f)
        files.append(f)
    lst = os.path.join(out, "_목록.txt")
    with open(lst, "w", encoding="utf-8") as fp:
        fp.writelines(f"file '{os.path.abspath(m)}'\n" for m in files)
    subprocess.run([ffmpeg(), "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-b:a", "160k",
                    os.path.join(out, "장구_전체듣기.mp3")], check=True)
    os.remove(lst)
    return 0


if __name__ == "__main__":
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(here, "역사", "배경음샘플", "타악", "장구")))
