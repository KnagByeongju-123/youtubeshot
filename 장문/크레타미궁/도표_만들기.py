"""크레타 파푸라 원형 구조물 도표 → 사진/c15.jpg  (python 도표_만들기.py)
수치: 그리스 문화부 발표(2024-06-12) — 지름 약 48m, 넓이 약 1,800㎡, 돌 고리 8겹(평균 두께 1.4m, 남은 높이 최대 1.7m), 가운데 원형 건물 지름 약 15m(네 칸)"""
import json, math, os
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 1920, 1080
FB = "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf"
FR = "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"
GOLD, WHITE, GREY, STONE = (255, 214, 140), (240, 240, 240), (170, 165, 155), (205, 190, 160)
im = Image.new("RGB", (W, H), (30, 26, 22)); d = ImageDraw.Draw(im)
F = lambda s, f=FB: ImageFont.truetype(f, s)
d.text((110, 90), "파푸라 언덕의 원형 구조물", font=F(64), fill=GOLD)
cx, cy, R = 1380, 570, 420
for k in range(8):                                   # 돌 고리 8겹
    r = R - k * 34
    d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=STONE, width=12)
rc = R - 8 * 34 + 10
for a in range(0, 360, 30):                          # 바퀴살 벽
    t = math.radians(a + 15)
    d.line((cx + rc * math.cos(t), cy + rc * math.sin(t), cx + R * math.cos(t), cy + R * math.sin(t)), fill=STONE, width=8)
d.ellipse((cx - 130, cy - 130, cx + 130, cy + 130), fill=(90, 75, 60), outline=GOLD, width=8)    # 가운데 건물
d.line((cx - 130, cy, cx + 130, cy), fill=GOLD, width=6); d.line((cx, cy - 130, cx, cy + 130), fill=GOLD, width=6)
d.line((cx - R, cy + R + 40, cx + R, cy + R + 40), fill=WHITE, width=4)
d.text((cx - 90, cy + R + 50), "지름 약 48m", font=F(36), fill=WHITE)
for i, t in enumerate(["· 돌 고리 8겹 (벽 두께 평균 1.4m)", "· 가운데 둥근 건물 지름 약 15m, 네 칸", "· 바퀴살 같은 벽이 작은 방으로 나눔", "· 좁은 틈으로만 이어진 방들", "· 기원전 2000~1700년 무렵"]):
    d.text((110, 260 + i * 105), t, font=F(42, FR), fill=WHITE)
d.text((110, 900), "그리스 문화부 발표 (2024) — 원래 높이·지붕 모양은 아직 모름", font=F(32, FR), fill=GREY)
os.makedirs(os.path.join(HERE, "사진"), exist_ok=True)
im.save(os.path.join(HERE, "사진", "c15.jpg"), quality=92)
mp = os.path.join(HERE, "사진후보", "후보.json")
meta = json.load(open(mp, encoding="utf-8")) if os.path.exists(mp) else {}
meta["c15_도표"] = {"title": "도표: c15", "artist": "설명 도표 (그리스 문화부 발표 수치)", "license": "—", "page": "", "source": "설명 도표", "file": "c15.jpg"}
json.dump(meta, open(mp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("ok")
