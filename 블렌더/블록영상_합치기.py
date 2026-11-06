"""블록 영상 합치기: 장면 그림(JPG) + 나레이션·배경음(소리.wav) + 한 줄 자막 → 1920×1080 H.264 (블록영상.md)
python -X utf8 블렌더/블록영상_합치기.py <작업 폴더(시간표.json·장면계획.json·소리.wav)> <장면 그림 폴더> <결과.mp4> [--제목 "…"]
  - 장면마다 애니메이션(그린 장 수) 뒤 남은 시간은 마지막 장을 아주 천천히 확대해 이어 감
  - 자막: 문단을 문장·쉼표로 나눠 한 줄씩(글자 수 비율로 시간), 맨 앞 제목 카드(첫 문단 시작 전)"""
import json
import os
import re
import subprocess
import sys

work, frames, out = sys.argv[1], sys.argv[2], sys.argv[3]
title = sys.argv[sys.argv.index("--제목") + 1] if "--제목" in sys.argv else ""
tt = json.load(open(os.path.join(work, "시간표.json"), encoding="utf-8"))
plan = json.load(open(os.path.join(work, "장면계획.json"), encoding="utf-8"))
tmp = os.path.join(work, "_조각")
os.makedirs(tmp, exist_ok=True)
FPS = 24
parts = []
for p in plan:
    sc, dur, n = p["scene"], p["dur"], p["anim"]
    a = os.path.join(tmp, f"{sc:02d}_a.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", str(FPS), "-i", os.path.join(frames, f"s{sc:02d}_%04d.jpg"),
                    "-vf", "scale=1920:1080:flags=lanczos,format=yuv420p", "-c:v", "libx264", "-crf", "18", "-preset", "medium", a], check=True)
    parts.append(a)
    rest = dur - n / FPS
    if rest > 0.05:                                  # 마지막 장을 천천히 확대하며 머무름 (1.00 → 1.06)
        nf = int(round(rest * FPS))
        last = os.path.join(frames, f"s{sc:02d}_{n:04d}.jpg")
        b = os.path.join(tmp, f"{sc:02d}_b.mp4")
        z = f"zoompan=z='1+0.06*on/{max(1, nf)}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={nf}:s=1920x1080:fps={FPS}"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-loop", "1", "-i", last, "-vf", "scale=3840:2160:flags=lanczos," + z + ",format=yuv420p",
                        "-frames:v", str(nf), "-c:v", "libx264", "-crf", "18", "-preset", "medium", b], check=True)
        parts.append(b)
lst = os.path.join(tmp, "목록.txt")
open(lst, "w").write("".join(f"file '{x}'\n" for x in parts))
video = os.path.join(tmp, "영상만.mp4")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", video], check=True)


def ts(t):
    h, r = divmod(max(0, t), 3600)
    m, s = divmod(r, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


ass = ["[Script Info]", "ScriptType: v4.00+", "PlayResX: 1920", "PlayResY: 1080", "", "[V4+ Styles]",
       "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
       "Style: 자막,NanumSquare_ac,58,&H00FFFFFF,&H00FFFFFF,&H00101010,&H80000000,-1,0,0,0,100,100,0,0,1,4,1,2,80,80,70,1",
       "Style: 제목,NanumSquare_ac,96,&H00FFFFFF,&H00FFFFFF,&H00202020,&H90000000,-1,0,0,0,100,100,0,0,1,6,2,5,80,80,0,1",
       "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
segs = tt["segs"]
if title and segs and segs[0]["t0"] > 0.5:
    ass.append(f"Dialogue: 0,{ts(0.2)},{ts(segs[0]['t0'] - 0.1)},제목,,0,0,0,,{{\\fad(400,300)}}{title}")
for sg in segs:
    if sg["kind"] != "text":
        continue
    pieces = [x.strip() for x in re.split(r"(?<=[.?!])\s+|(?<=,)\s+", sg["text"]) if x.strip()]
    merged = []
    for x in pieces:                                   # 너무 짧은 조각은 앞 조각과 합침
        if merged and len(merged[-1]) + len(x) < 24:
            merged[-1] += " " + x
        else:
            merged.append(x)
    total = sum(len(x) for x in merged) or 1
    t, span = sg["t0"], sg["t1"] - sg["t0"]
    for x in merged:
        d = span * len(x) / total
        ass.append(f"Dialogue: 0,{ts(t)},{ts(t + d - 0.05)},자막,,0,0,0,,{x.rstrip(',')}")
        t += d
ass_p = os.path.join(tmp, "자막.ass")
open(ass_p, "w", encoding="utf-8").write("\n".join(ass) + "\n")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", video, "-i", os.path.join(work, "소리.wav"), "-vf", f"ass={ass_p}",
                "-c:v", "libx264", "-crf", "20", "-preset", "medium", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
                "-shortest", "-movflags", "+faststart", out], check=True)
print("OK", out)
