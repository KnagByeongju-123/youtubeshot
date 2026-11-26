"""짧은 모음 연습('아. 에. 이. 오. 우.')처럼 받아쓰기가 글자를 못 맞출 때 — 소리 크기로 소리 나는 마디를 찾아 음절마다 [음절, 시작, 끝]
   (사용자 2026-11-26 '아, 에, 이, 오, 우 집중연습': 발음시각.py 가 10개 중 3개만 맞춤 → 소리 마디로 다시 잡음)
   마디 수가 음절보다 적으면 가장 긴 마디를 둘로 나눔(이어 읽은 '오우'), 많으면 가장 짧은 마디를 버림
   사용: .supertonic_venv/bin/python 실사3D/소리마디_시각.py <나레이션.mp3|wav> "아에이오우" <결과.json> [--문턱 0.08]
   → 애니3D/입모양_프레임.py <결과.json> ... 로 입 모양"""
import json
import subprocess
import sys
import numpy as np

a = sys.argv[1:]; src, text, dst = a[0], a[1], a[2]
TH = float(a[a.index("--문턱") + 1]) if "--문턱" in a else 0.08
syl = [c for c in text if "가" <= c <= "힣"]
raw = subprocess.run(["ffmpeg", "-v", "error", "-i", src, "-ac", "1", "-ar", "16000", "-f", "s16le", "-"], capture_output=True).stdout
x = np.frombuffer(raw, np.int16).astype(np.float32) / 32768; h = 160                    # 0.01초 칸
e = np.sqrt(np.convolve(x ** 2, np.ones(h) / h, "valid")[::h])
on = e > e.max() * TH; segs = []; s = None
for i, v in enumerate(list(on) + [False]):
    if v and s is None: s = i
    if not v and s is not None:
        if i - s > 3: segs.append([s / 100, i / 100])
        s = None
while len(segs) < len(syl) and segs:                                                   # 이어 읽은 마디 나누기(가운데 가장 조용한 곳)
    k = max(range(len(segs)), key=lambda j: segs[j][1] - segs[j][0]); t0, t1 = segs[k]
    i0, i1 = int((t0 + (t1 - t0) * 0.3) * 100), int((t0 + (t1 - t0) * 0.7) * 100)
    cut = (i0 + int(np.argmin(e[i0:i1]))) / 100 if i1 > i0 else (t0 + t1) / 2
    segs[k:k + 1] = [[t0, cut], [cut, t1]]
while len(segs) > len(syl):
    segs.pop(min(range(len(segs)), key=lambda j: segs[j][1] - segs[j][0]))
out = [[c, round(t0, 3), round(t1, 3)] for c, (t0, t1) in zip(syl, segs)]
json.dump(out, open(dst, "w", encoding="utf-8"), ensure_ascii=False)
print("음절", len(syl), "개 ↔ 소리 마디", len(segs), "개 →", dst)
for r in out: print(" ", r)
