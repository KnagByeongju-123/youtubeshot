"""트로이 9개 층 도표 → 사진/c10.jpg  (python 도표_만들기.py)
연대(대략, 위키백과 Troy·유네스코): 1층 기원전 3000년 무렵 ~ 9층 서기 500년 무렵, 2층 = '프리아모스의 보물'(약 기원전 2500~2300년),
6층 = 기원전 1750~1300년 무렵(높은 돌 성벽), 7층 = 기원전 1300~950년 무렵(7a 기원전 1180년 무렵 불탐), 8층 그리스 일리온, 9층 로마 일리움"""
import json, os
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 1920, 1080
FB = "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf"
FR = "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"
GOLD, WHITE, GREY, RED = (255, 214, 140), (240, 240, 240), (170, 165, 155), (255, 120, 100)
F = lambda s, f=FB: ImageFont.truetype(f, s)
im = Image.new("RGB", (W, H), (30, 26, 22)); d = ImageDraw.Draw(im)
d.text((110, 70), "트로이 언덕 속 아홉 겹의 도시", font=F(60), fill=GOLD)
rows = [("9층", "로마의 일리움", "서기 500년 무렵까지"), ("8층", "그리스의 일리온", ""), ("7층", "불에 탄 도시 (7a)", "기원전 1180년 무렵"),
        ("6층", "높은 돌 성벽의 강한 도시", "기원전 13세기 무렵"), ("5층", "", ""), ("4층", "", ""), ("3층", "", ""),
        ("2층", "'프리아모스의 보물'", "기원전 2500~2300년 무렵"), ("1층", "가장 오래된 마을", "기원전 3000년 무렵")]
y = 180
for i, (n, a, b) in enumerate(rows):
    hot = n in ("6층", "7층")
    col = (120 + i * 8, 95 + i * 6, 70 + i * 4)
    d.rectangle((110, y, 1050, y + 86), fill=col, outline=RED if hot else (60, 50, 40), width=6 if hot else 2)
    d.text((140, y + 18), n, font=F(44), fill=WHITE)
    d.text((300, y + 22), a, font=F(36, FR), fill=WHITE)
    d.text((1090, y + 22), b, font=F(34, FR), fill=RED if hot else GREY)
    y += 92
d.text((1090, 140), "← 트로이 전쟁 시대 후보 = 6·7층", font=F(36), fill=RED)
d.text((110, 1020), "층 번호는 아래(오래된 것)부터 · 연대는 대략", font=F(28, FR), fill=GREY)
os.makedirs(os.path.join(HERE, "사진"), exist_ok=True)
im.save(os.path.join(HERE, "사진", "c10.jpg"), quality=92)
mp = os.path.join(HERE, "사진후보", "후보.json")
meta = json.load(open(mp, encoding="utf-8")) if os.path.exists(mp) else {}
meta["c10_도표"] = {"title": "도표: c10", "artist": "설명 도표 (트로이 층 연대)", "license": "—", "page": "", "source": "설명 도표", "file": "c10.jpg"}
json.dump(meta, open(mp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("ok")
