"""그림 점검표 — 사용자가 직접 점검하도록 그림을 40장씩 번호를 붙여 한 장으로 모음 (사용자 결정 2026-10-31)
python 그림_점검표.py <프로젝트.json 또는 그림 폴더> [--장수 40]
  - 프로젝트면 대본에 나오는 순서대로, 폴더면 파일 이름 순서대로
  - 결과: output/점검/<이름>_점검_1.jpg, _2.jpg … (8칸×5줄, 칸마다 번호 · 나오는 시각 순서) + <이름>_점검_목록.txt (번호 → 그림 파일)
  - 사용자가 번호로 고칠 그림을 알려 주면 그 그림만 다시 그림"""
import glob
import json
import os
import re
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
a = sys.argv[1:]
src = os.path.abspath(a[0])
per = int(a[a.index("--장수") + 1]) if "--장수" in a else 40
if src.endswith(".json"):
    story = json.load(open(src, encoding="utf-8")).get("story", "")
    paths = []
    for line in story.split("\n"):
        mm = re.match(r"\s*\[(?:사진|그림|이미지)\s*[:：]\s*([^|\]]+)", line)
        if mm:
            p = mm.group(1).strip()
            paths.append(p if os.path.isabs(p) else os.path.join(HERE, p))
    name = os.path.basename(src)[:-5].replace("_프로젝트", "")
else:
    paths = sorted(glob.glob(os.path.join(src, "*.png")) + glob.glob(os.path.join(src, "*.jpg")))
    name = os.path.basename(src.rstrip("/"))
paths = [p for p in paths if os.path.exists(p)]
out_dir = os.path.join(HERE, "output", "점검")
os.makedirs(out_dir, exist_ok=True)
font = ImageFont.truetype(glob.glob("/usr/share/fonts/**/NanumGothicBold.ttf", recursive=True)[0], 34)
COLS, TW, TH = 8, 400, 225
made = []
for b in range(0, len(paths), per):
    chunk = paths[b:b + per]
    rows = (len(chunk) + COLS - 1) // COLS
    sheet = Image.new("RGB", (COLS * (TW + 8) + 8, rows * (TH + 8) + 8), (30, 30, 30))
    d = ImageDraw.Draw(sheet)
    for i, p in enumerate(chunk):
        x, y = 8 + (i % COLS) * (TW + 8), 8 + (i // COLS) * (TH + 8)
        sheet.paste(Image.open(p).convert("RGB").resize((TW, TH)), (x, y))
        d.rectangle((x, y, x + 70, y + 42), fill=(0, 0, 0))
        d.text((x + 6, y + 2), str(b + i + 1), fill=(255, 220, 0), font=font)
    f = os.path.join(out_dir, f"{name[:40]}_점검_{b // per + 1}.jpg")
    sheet.save(f, quality=88)
    made.append(f)
open(os.path.join(out_dir, f"{name[:40]}_점검_목록.txt"), "w", encoding="utf-8").write("\n".join(f"{i + 1}\t{p}" for i, p in enumerate(paths)))
print(f"그림 {len(paths)}장 → 점검표 {len(made)}장")
for f in made:
    print(f)
