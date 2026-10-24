"""성우 목소리 샘플 — 후보 목소리마다 같은 문장을 읽혀 mp3 로 저장 (들어 보고 고르는 용도)
python 성우_샘플.py <저장폴더> "<읽을 문장>" 이름=성우[,속도%[,톤반음]] ...
  예) python 성우_샘플.py 샘플 "엄마가 떠나시고 처음 맞은 생신이었습니다." 1번=F5,-6 2번=F1,-8,-1 3번=M2
  - 성우 = Supertonic M1~M5 · F1~F5, 속도 = 빠르기 % (-10 = 10% 느리게), 톤 = 반음 (-2 = 두 반음 낮게, 빠르기는 그대로)
  - 결과: <저장폴더>/<이름>_<성우>_속도<..>_톤<..>.mp3 + 모두 이어 붙인 전체듣기.mp3 (후보 사이 1초 쉼)
고른 목소리는 등장인물.json 의 voice ({"code", "rate", "semis"}) 에 저장"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PY = os.path.join(HERE, ".supertonic_venv", "Scripts" if os.name == "nt" else "bin", "python.exe" if os.name == "nt" else "python")


def parse(arg):
    name, _, spec = arg.partition("=")
    p = [x.strip() for x in spec.split(",")]
    return name, p[0].upper(), float(p[1]) if len(p) > 1 and p[1] else 0.0, float(p[2]) if len(p) > 2 and p[2] else 0.0


def main():
    out_dir, text, cands = sys.argv[1], sys.argv[2], [parse(a) for a in sys.argv[3:]]
    os.makedirs(out_dir, exist_ok=True)
    env = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
    w = subprocess.Popen([PY, "-X", "utf8", "-u", os.path.join(HERE, "supertonic_local_worker.py"),
                          "--model-dir", os.path.join(HERE, "supertonic_assets")],
                         stdin=subprocess.PIPE, stdout=subprocess.PIPE, encoding="utf-8", bufsize=1, env=env)
    json.loads(w.stdout.readline())              # ready
    made = []
    for name, code, rate, semis in cands:
        base = os.path.join(out_dir, f"{name}_{code}_속도{rate:+.0f}_톤{semis:+.0f}")
        wav = base + "_raw.wav"
        w.stdin.write(json.dumps({"text": text, "voice": code, "speed": max(.7, min(2.0, 1 + rate / 100)),
                                  "steps": 5, "lang": "ko", "out": os.path.abspath(wav)}, ensure_ascii=False) + "\n")
        r = json.loads(w.stdout.readline())
        if not r.get("ok"):
            print("ERR", name, r)
            continue
        sr = int(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=sample_rate", "-of", "csv=p=0", wav],
                                capture_output=True, text=True).stdout.strip() or 44100)
        k = 2 ** (semis / 12)
        af = f"asetrate={int(sr * k)},aresample={sr},atempo={1 / k:.6f}," if semis else ""
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", wav, "-af", af + "aresample=44100,apad=pad_dur=1",
                        "-ac", "1", "-b:a", "128k", base + ".mp3"], check=True)
        os.remove(wav)
        made.append(base + ".mp3")
        print("OK", base + ".mp3")
    w.stdin.close()
    lst = os.path.join(out_dir, "_목록.txt")
    with open(lst, "w", encoding="utf-8") as f:
        f.writelines(f"file '{os.path.abspath(m)}'\n" for m in made)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy",
                    os.path.join(out_dir, "전체듣기.mp3")], check=True)
    os.remove(lst)


if __name__ == "__main__":
    main()
