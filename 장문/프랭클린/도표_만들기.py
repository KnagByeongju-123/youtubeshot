"""프랭클린 원정대 설명 도표 → 사진/<컷>.jpg
  python 도표_만들기.py
c10: 빅토리 포인트 쪽지 내용 (실제 쪽지 사진이 자유 이용 자료에 없어서 그 장소 옛 그림 위에 내용을 적음 — 사진후보/c10_1.jpg, 없으면 어두운 바탕)
c17: 납 수치 막대 (Beattie 1981: 선원 뼈 226ppm, 이누이트 26~36ppm — Wikipedia 'Franklin's lost expedition')"""
import json, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 1920, 1080
FB = "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf"
FR = "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"
GOLD, WHITE, GREY, RED, BLUE = (255, 222, 150), (240, 240, 240), (160, 160, 160), (255, 95, 80), (110, 180, 255)


def F(size, f=FB):
    return ImageFont.truetype(f, size)


def save(im, name):
    im.save(os.path.join(HERE, "사진", name + ".jpg"), quality=92)


os.makedirs(os.path.join(HERE, "사진"), exist_ok=True)
meta_p = os.path.join(HERE, "사진후보", "후보.json")
meta = json.load(open(meta_p, encoding="utf-8"))

# c10 빅토리 포인트 쪽지 내용
bgp = os.path.join(HERE, "사진후보", "c10_1.jpg")
if os.path.exists(bgp) and os.path.getsize(bgp) > 10000:
    bg = Image.open(bgp).convert("RGB")
    r = max(W / bg.width, H / bg.height)
    bg = bg.resize((int(bg.width * r) + 1, int(bg.height * r) + 1), Image.LANCZOS)
    bg = bg.crop(((bg.width - W) // 2, (bg.height - H) // 2, (bg.width - W) // 2 + W, (bg.height - H) // 2 + H))
    bg = ImageEnhance.Brightness(bg.filter(ImageFilter.GaussianBlur(2))).enhance(0.35)
    src = meta.get("c10_1")
else:
    bg, src = Image.new("RGB", (W, H), (24, 22, 20)), None
d = ImageDraw.Draw(bg)
d.text((150, 120), "빅토리 포인트 쪽지에 적힌 내용", font=F(64), fill=GOLD)
d.rounded_rectangle((150, 250, 1770, 470), 18, fill=(245, 236, 210))
d.text((190, 280), "1847년 5월 28일", font=F(44), fill=(90, 60, 30))
d.text((190, 350), "“모두 무사함” — 겨울을 나고, 일행 일부가 섬을 살피러 떠남", font=F(42, FR), fill=(40, 30, 20))
d.rounded_rectangle((150, 510, 1770, 860), 18, fill=(245, 236, 210))
d.text((190, 540), "1848년 4월 25일, 가장자리에 덧붙인 글", font=F(44), fill=(150, 40, 30))
y = 615
for t in ["· 존 프랭클린 경, 1847년 6월 11일 숨짐", "· 지금까지 장교 9명, 선원 15명 숨짐", "· 1848년 4월 22일 배를 버림 — 105명, 남쪽 강으로 출발"]:
    d.text((190, y), t, font=F(42, FR), fill=(40, 30, 20)); y += 72
d.text((150, 880), "※ 내용을 우리말로 옮겨 적은 설명 그림 (쪽지 원본 사진이 아님)", font=F(30, FR), fill=GREY)
save(bg, "c10")
meta["c10_도표"] = {"title": "도표: c10", "artist": ("빅토리 포인트 옛 그림 위에 쪽지 내용을 적은 설명 도표" if src else "쪽지 내용을 적은 설명 도표"),
                   "license": (src or {}).get("license", "—"), "page": (src or {}).get("page", ""), "source": "Wikimedia Commons" if src else "설명 도표", "file": "c10.jpg"}

# c17 납 수치 막대
im = Image.new("RGB", (W, H), (24, 22, 20)); d = ImageDraw.Draw(im)
d.text((150, 110), "뼈 속 납의 양 (1981년 조사)", font=F(64), fill=GOLD)
base, top = 900, 300
scale = (base - top) / 240
bars = [("원정대 선원의 뼈", 226, RED, "226 ppm"), ("같은 지역 이누이트의 뼈", 36, BLUE, "26~36 ppm")]
for i, (lab, v, col, txt) in enumerate(bars):
    x = 300 + i * 650
    d.rectangle((x, base - v * scale, x + 300, base), fill=col)
    d.text((x, base - v * scale - 80), txt, font=F(56), fill=WHITE)
    d.text((x - 20, base + 25), lab, font=F(42, FR), fill=WHITE)
d.line((220, base, 1700, base), fill=(200, 200, 200), width=3)
d.text((1100, 330), "약 10배", font=F(80), fill=RED)
d.text((150, 210), "출처: Beattie 연구팀(1981) — Wikipedia 'Franklin's lost expedition'", font=F(28, FR), fill=GREY)
save(im, "c17")
meta["c17_도표"] = {"title": "도표: c17", "artist": "설명 도표 (Beattie 1981 수치)", "license": "—", "page": "https://en.wikipedia.org/wiki/Franklin%27s_lost_expedition", "source": "설명 도표", "file": "c17.jpg"}
json.dump(meta, open(meta_p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("ok")
