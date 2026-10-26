"""카라한 테페 '가장 오래된 입체 이야기' 도표 → 사진/c17.jpg  (python 도표_만들기.py)
내용: 카룰 인터뷰(The Collector 2025)·아키올로지 매거진 — 큰 돌그릇 안 작은 그릇, 그 안 동물 조각 3개(멧돼지·독수리·여우, 각 약 4cm), 머리를 돌 고리에 넣음"""
import json, os
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 1920, 1080
FB = "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf"
FR = "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"
GOLD, WHITE, GREY, STONE, DARK = (255, 214, 140), (240, 240, 240), (170, 165, 155), (190, 180, 160), (60, 52, 44)
F = lambda s, f=FB: ImageFont.truetype(f, s)
im = Image.new("RGB", (W, H), (30, 26, 22)); d = ImageDraw.Draw(im)
d.text((110, 80), "가장 오래된 입체 이야기 (2025년 발견)", font=F(60), fill=GOLD)
d.pieslice((360, 260, 1560, 860), 0, 180, fill=DARK, outline=STONE, width=10)          # 큰 돌그릇
d.text((1590, 540), "큰 돌그릇", font=F(36), fill=STONE)
d.pieslice((520, 380, 1400, 780), 0, 180, fill=(80, 70, 58), outline=STONE, width=8)     # 작은 그릇
d.text((1590, 640), "작은 돌그릇", font=F(32), fill=STONE)
for i, name in enumerate(["멧돼지", "독수리", "여우"]):
    x = 620 + i * 260
    d.ellipse((x, 470, x + 160, 630), fill=(150, 140, 120), outline=WHITE, width=3)        # 조각 몸
    d.ellipse((x + 40, 410, x + 120, 490), outline=GOLD, width=12)                          # 돌 고리
    d.text((x + 20, 650), name, font=F(40), fill=WHITE)
d.text((110, 900), "· 조각 높이 약 4cm · 세 동물 모두 머리를 돌 고리에 넣은 채 놓임 · 순서를 정해 배치", font=F(34, FR), fill=WHITE)
d.text((110, 960), "카룰 교수 발표 (2025) — 그림은 배치를 설명하는 도표", font=F(30, FR), fill=GREY)
os.makedirs(os.path.join(HERE, "사진"), exist_ok=True)
im.save(os.path.join(HERE, "사진", "c17.jpg"), quality=92)
mp = os.path.join(HERE, "사진후보", "후보.json")
meta = json.load(open(mp, encoding="utf-8"))
meta["c17_도표"] = {"title": "도표: c17", "artist": "설명 도표 (카룰 교수 발표 내용)", "license": "—", "page": "", "source": "설명 도표", "file": "c17.jpg"}
json.dump(meta, open(mp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("ok")
