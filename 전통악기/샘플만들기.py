"""권역별 전통악기 배경음 샘플(30초 mp3)을 만듦 → 역사/배경음샘플/<권역>/<번호>_<음계>_<느낌>.mp3
사용: python -X utf8 전통악기/샘플만들기.py [권역 ...]   (권역을 안 쓰면 전부)"""
import importlib.util
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(HERE), "역사", "배경음샘플")
REGIONS = ["중국", "한국", "일본", "중동", "인도", "몽골", "중세유럽"]


def load(region):
    spec = importlib.util.spec_from_file_location("trad_" + region, os.path.join(HERE, region + ".py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.REGION


def ffmpeg():
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return "ffmpeg"


def main(names):
    sys.path.insert(0, HERE)
    import 공통 as K
    for rg in names or REGIONS:
        R = load(rg)
        d = os.path.join(OUT, rg)
        os.makedirs(d, exist_ok=True)
        for i, (md, (_, _, feel)) in enumerate(R.modes.items(), 1):
            wp = os.path.join(d, f"{i}_{md}_{feel.split(' (')[0].replace(' ', '')}.wav")
            K.write_wav(wp, R.sample(md))
            subprocess.run([ffmpeg(), "-y", "-loglevel", "error", "-i", wp, "-b:a", "160k", wp[:-4] + ".mp3"], check=True)
            os.remove(wp)
            print("OK", os.path.relpath(wp[:-4] + ".mp3", os.path.dirname(HERE)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
