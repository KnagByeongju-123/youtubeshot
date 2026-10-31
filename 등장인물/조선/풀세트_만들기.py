"""조선 기본 캐릭터 시트 12장(기본_<역할>.png)을 한 장 풀세트로: python 등장인물/조선/풀세트_만들기.py"""
import glob
import os
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
SECTIONS = [("궁궐 사람들", ["왕", "왕비", "문관", "상궁", "내관", "무관"]),
            ("그 외 일반인들", ["사대부", "상인", "백정", "기생", "농민", "아낙네"])]
W, H, COLS, GAP, LAB, HEAD = 1024, 576, 3, 24, 64, 90
font = lambda s: ImageFont.truetype(glob.glob("/usr/share/fonts/**/NanumGothicBold.ttf", recursive=True)[0], s)
rows = sum((len(n) + COLS - 1) // COLS for _, n in SECTIONS)
out = Image.new("RGB", (COLS * W + (COLS + 1) * GAP, 150 + len(SECTIONS) * HEAD + rows * (H + LAB + GAP)), (250, 247, 240))
d = ImageDraw.Draw(out)
d.text((GAP, 35), "조선시대 인물 캐릭터 시트 (수묵 담채 · 앞 / 옆 / 뒤)", fill=(30, 30, 30), font=font(72))
y = 150
for title, names in SECTIONS:
    d.text((GAP, y + 15), "■ " + title, fill=(120, 40, 30), font=font(56))
    y += HEAD
    for i, n in enumerate(names):
        x = GAP + (i % COLS) * (W + GAP)
        if i and i % COLS == 0:
            y += H + LAB + GAP
        d.text((x + 10, y), n, fill=(20, 20, 20), font=font(52))
        p = os.path.join(HERE, f"기본_{n}.png")
        if os.path.exists(p):
            out.paste(Image.open(p).convert("RGB").resize((W, H)), (x, y + LAB))
    y += H + LAB + GAP
out.save(os.path.join(HERE, "조선_인물_풀세트.jpg"), quality=90)
print("저장:", os.path.join(HERE, "조선_인물_풀세트.jpg"), out.size)
