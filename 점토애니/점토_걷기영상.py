# -*- coding: utf-8 -*-
"""걷기 장면(투명 배경 frame_*.png, 한 주기)을 흰 배경에 얹어 24fps mp4 로.
한 장을 두 번씩 보여 줘 점토 애니(스톱모션) 느낌. 주기를 여러 번 반복.
쓰는 법: python 점토애니/점토_걷기영상.py <폴더> <결과.mp4> [반복수=5]
"""
import sys, os, glob, subprocess, tempfile
from PIL import Image

src, out = sys.argv[1], sys.argv[2]
rep = int(sys.argv[3]) if len(sys.argv) > 3 else 5
frames = sorted(glob.glob(os.path.join(src, "frame_*.png")))
tmp = tempfile.mkdtemp()
k = 0
for _ in range(rep):
    for f in frames:
        im = Image.open(f).convert("RGBA")
        bg = Image.new("RGB", im.size, "white")
        bg.paste(im, (0, 0), im)
        w, h = bg.size
        bg = bg.crop((0, 0, w - w % 2, h - h % 2))
        for _ in range(2):
            bg.save(os.path.join(tmp, f"{k:05d}.png"))
            k += 1
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", "24", "-i", os.path.join(tmp, "%05d.png"),
                "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", out], check=True)
print("영상:", out, k, "장")
