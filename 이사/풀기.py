"""새 서버에서 「경비실의 김 씨」 작업 자료 풀기 (repo 루트에서): python 이사/풀기.py
- 컷 그림 169장·시트·썸네일 → output/사이다/
- 나레이션 녹음(flac) → output/tts_cache/*.npy (영상 만들 때 그대로 재사용, 다시 녹음 안 함)"""
import glob, io, os, sys, tarfile
import numpy as np, soundfile as sf
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
parts = sorted(glob.glob(os.path.join(R, "이사", "data.tar.part*")))
buf = io.BytesIO(b"".join(open(p, "rb").read() for p in parts))
os.makedirs(os.path.join(R, "output", "사이다"), exist_ok=True)
os.makedirs(os.path.join(R, "output", "tts_cache"), exist_ok=True)
n = m = 0
with tarfile.open(fileobj=buf) as t:
    for mem in t.getmembers():
        if not mem.isfile():
            continue
        data = t.extractfile(mem).read()
        if mem.name.startswith("tts/"):
            a, _ = sf.read(io.BytesIO(data), dtype="float32")
            np.save(os.path.join(R, "output", "tts_cache", os.path.basename(mem.name)[:-5] + ".npy"), a)
            m += 1
        else:
            dst = os.path.join(R, "output", "사이다", mem.name)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            open(dst, "wb").write(data)
            n += 1
print("그림·시트", n, "개, 녹음", m, "개 풀었음")
