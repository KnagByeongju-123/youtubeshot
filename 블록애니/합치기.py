"""블록 애니 마무리: 장면 영상들을 타이밍대로 이어 붙이고(1080p), 프로그램이 만든 '초록 화면 + 자막 + 나레이션·배경음' 영상을 위에 얹음
python3 블록애니/합치기.py <작품폴더> <초록자막영상.mp4> <결과.mp4>
  초록자막영상 = render_project.py 로 만든 영상 (그림 자리가 모두 순수한 초록 → colorkey 로 빼면 자막·제목 카드만 남음)"""
import json, os, subprocess, sys
W, fg, out = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2]), os.path.abspath(sys.argv[3])
tm = json.load(open(os.path.join(W, "타이밍.json"), encoding="utf-8"))
vd = os.path.join(W, "장면영상"); tmp = os.path.join(vd, "_합치기"); os.makedirs(tmp, exist_ok=True)
lst = []
for i, sh in enumerate(tm["shots"]):
    d = sh["t1"] - sh["t0"]
    o = os.path.join(tmp, f"c{i:02d}.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", os.path.join(vd, f"s{i:02d}.mp4"), "-t", f"{d:.3f}", "-vf", "scale=1920:1080:flags=neighbor,fps=24,setsar=1",
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-an", o], check=True)
    lst.append(f"file '{o}'")
open(os.path.join(tmp, "list.txt"), "w").write("\n".join(lst))
bg = os.path.join(tmp, "bg.mp4")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", os.path.join(tmp, "list.txt"), "-c", "copy", bg], check=True)
# 끝이 모자라면 마지막 장면을 늘림
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", bg, "-i", fg,
                "-filter_complex", "[1:v]colorkey=0x00FF00:0.30:0.08[k];[0:v]tpad=stop_mode=clone:stop_duration=5[b];[b][k]overlay=0:0:shortest=1[v]",
                "-map", "[v]", "-map", "1:a", "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out], check=True)
print("OK", out)
