"""코피알레 해독 설명 도표 (실제 암호 책 사진 위·옆에 글자 카드) → 사진/<컷>.jpg
  python 도표_만들기.py   (사진후보/c02_1.jpg = Copiale-cipher09s.png, Public domain)
내용은 Knight·Megyesi·Schaefer 'The Copiale Cipher'(2011) 논문 4~6장·부록 A 그대로"""
import json, os
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 1920, 1080
FB = "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf"
FR = "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"
FM = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
BG = (24, 22, 19)
GOLD, WHITE, GREY, RED, GREEN, BLUE = (255, 222, 150), (238, 238, 238), (150, 150, 150), (255, 95, 80), (120, 220, 130), (110, 180, 255)
page = Image.open(os.path.join(HERE, "사진후보", "c02_1.jpg")).convert("RGB")


def F(size, f=FB):
    return ImageFont.truetype(f, size)


def canvas():
    im = Image.new("RGB", (W, H), BG)
    return im, ImageDraw.Draw(im)


def lines(d, x, y, rows, size, color, font=FR, gap=1.5):
    for r in rows:
        d.text((x, y), r, font=F(size, font), fill=color)
        y += int(size * gap)
    return y


def left_page(im, crop=None, h=900):
    p = page.crop(crop) if crop else page
    p = p.resize((int(p.width * h / p.height), h), Image.LANCZOS)
    im.paste(p, (90, (H - h) // 2))
    return 90 + p.width


def chip(d, x, y, t, fill, fg=(20, 20, 20), size=58, font=FM, pad=14):
    f = F(size, font)
    b = d.textbbox((0, 0), t, font=f)
    a = d.textbbox((0, 0), "Ag", font=f)
    w, h = max(b[2] - b[0], int(size * 0.6)) + pad * 2, a[3] - a[1] + pad * 2
    d.rounded_rectangle((x, y, x + w, y + h), 10, fill=fill)
    d.text((x + (w - (b[2] - b[0])) // 2 - b[0], y + pad - a[1]), t, font=f, fill=fg)
    return x + w


def save(im, name):
    im.save(os.path.join(HERE, "사진", name + ".jpg"), quality=92)


os.makedirs(os.path.join(HERE, "사진"), exist_ok=True)

# c05 책의 특징
im, d = canvas()
x = left_page(im, (0, 0, 660, 890), 900) + 90
lines(d, x, 190, ["코피알레 암호 책"], 66, GOLD, FB)
lines(d, x, 320, ["· 모두 105쪽", "· 손으로 쓴 글자 약 7만 5천 개", "· 기호 약 90가지", "· 띄어쓰기 없음, 고친 자국 거의 없음"], 46, WHITE)
lines(d, x, 680, ["암호가 아닌 글자는 딱 두 곳"], 44, GOLD, FB)
lines(d, x, 760, ["“Philipp 1866”   ·   “Copiales 3”"], 46, WHITE)
save(im, "c05")

# c08 첫 번째 생각
im, d = canvas()
x = left_page(im, (690, 380, 1080, 860), 900) + 80
lines(d, x, 200, ["첫 번째 생각"], 66, GOLD, FB)
y = 330
chip(d, x, y, "a b c ... z", (255, 214, 90), size=50); d.text((x + 380, y + 12), "로마자 = 진짜 내용?", font=F(48), fill=WHITE)
y += 150
chip(d, x, y, "△ ∴ ‡ ◇ ...", (90, 90, 90), WHITE, size=50, font=FB); d.text((x + 380, y + 12), "나머지 기호 = 가짜?", font=F(48), fill=WHITE)
lines(d, x, 650, ["컴퓨터가 비슷하게 쓰이는 기호끼리 묶자", "로마자들이 한 무리로 뭉쳤기 때문"], 40, GREY)
save(im, "c08")

# c09 40개가 넘는 언어로 시험
im, d = canvas()
lines(d, 140, 110, ["로마자만 뽑아 여러 언어로 풀어 보기"], 62, GOLD, FB)
langs = ["독일어", "영어", "라틴어", "프랑스어", "이탈리아어", "스페인어", "네덜란드어", "스웨덴어", "폴란드어", "그리스어", "헝가리어", "핀란드어", "터키어", "아랍어", "히브리어"]
for i, t in enumerate(langs):
    cx, cy = 130 + (i % 5) * 340, 270 + (i // 5) * 150
    d.rounded_rectangle((cx, cy, cx + 320, cy + 110), 14, outline=(110, 110, 110), width=3)
    d.text((cx + 28, cy + 30), t, font=F(44), fill=WHITE)
    d.text((cx + 262, cy + 22), "✗", font=F(60, "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"), fill=RED)
lines(d, 140, 760, ["… 모두 40개가 넘는 언어 → 전부 뜻 없는 글자", "한 글자를 여러 기호로 쓰는 방식으로 다시 풀어도 실패"], 46, WHITE)
d.text((140, 960), "※ 논문에 나온 것은 독일어·영어·라틴어 + 40여 개 언어 (나머지 칸은 예)", font=F(30, FR), fill=GREY)
save(im, "c09")

# c10 왜 독일어였을까
im, d = canvas()
lines(d, 140, 120, ["왜 독일어에 걸었을까"], 66, GOLD, FB)
cards = [("1", "책이 있던 곳", "독일"), ("2", "컴퓨터 계산", "독일어가 아주 조금 더 그럴듯"), ("3", "책에 적힌 이름", "Philipp — p 를 두 번 (독일식)")]
for i, (n, a, b) in enumerate(cards):
    y = 300 + i * 220
    d.ellipse((140, y, 260, y + 120), fill=(255, 214, 90)); d.text((180, y + 22), n, font=F(66), fill=(20, 20, 20))
    d.text((310, y + 4), a, font=F(42, FR), fill=GREY); d.text((310, y + 58), b, font=F(54), fill=WHITE)
save(im, "c10")

# c11 C 뒤에는 H
im, d = canvas()
lines(d, 140, 110, ["가장 먼저 찾은 짝: C 와 H"], 64, GOLD, FB)
d.text((140, 280), "독일어", font=F(44, FR), fill=GREY)
x = chip(d, 140, 350, "C", (255, 214, 90), size=90); d.text((x + 30, 375), "→", font=F(80), fill=WHITE); chip(d, x + 150, 350, "H", (255, 214, 90), size=90)
d.text((900, 380), "C 뒤에는 거의 언제나 H  (ich, nicht, auch …)", font=F(44, FR), fill=WHITE)
d.text((140, 590), "암호", font=F(44, FR), fill=GREY)
x = chip(d, 140, 660, "?", (90, 90, 90), WHITE, size=90); d.text((x + 30, 685), "→", font=F(80), fill=WHITE); chip(d, x + 150, 660, "–", (90, 90, 90), WHITE, size=90)
d.text((900, 690), "늘 붙어 다니는 두 기호 → C 와 H 로 놓음", font=F(44, FR), fill=WHITE)
d.text((140, 800), "※ 암호 기호는 연구팀이 옮겨 적은 모양 (? 와 –)", font=F(30, FR), fill=GREY)
lines(d, 140, 880, ["독일어에 흔한 글자 묶음과 맞으면 남기고, 안 맞으면 버림"], 42, GREEN)
save(im, "c11")

# c12 로마자는 띄어쓰기
im, d = canvas()
lines(d, 140, 110, ["그때 떠오른 두 낱말"], 64, GOLD, FB)
x = 140
for t, sp in [("CEREMONIE", False), ("b", True), ("DER", False), ("k", True), ("AUFNAHME", False)]:
    x = chip(d, x, 330, t, (110, 180, 255) if sp else (255, 214, 90), size=74) + 26
d.text((140, 500), "= 체레모니 데어 아우프나메 (입회 의식)", font=F(54), fill=WHITE)
lines(d, 140, 660, ["파란 칸의 로마자는 띄어쓰기였다", "진짜 내용은 기묘한 기호들 쪽에 있었음 (처음 생각과 정반대)"], 46, WHITE)
d.text((140, 900), "※ 파란 칸의 로마자는 설명을 위해 고른 예", font=F(32, FR), fill=GREY)
save(im, "c12")

# c13 쌍점 · SCH
im, d = canvas()
lines(d, 140, 110, ["남은 수수께끼 두 가지"], 64, GOLD, FB)
x = chip(d, 140, 290, "ABSCHNIT", (255, 214, 90), size=66); x = chip(d, x + 8, 290, ":", (255, 95, 80), size=66)
d.text((x + 40, 296), "→  ABSCHNITT", font=F(66, FM), fill=GREEN)
d.text((140, 420), "쌍점(:) = 앞 자음을 한 번 더  ('절'이라는 뜻)", font=F(46, FR), fill=WHITE)
x = chip(d, 140, 590, "GESELL", (255, 214, 90), size=66); x = chip(d, x + 8, 590, "◆", (255, 95, 80), size=66, font="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"); x = chip(d, x + 8, 590, "AFT", (255, 214, 90), size=66)
d.text((x + 40, 596), "→  GESELLSCHAFT", font=F(66, FM), fill=GREEN)
d.text((140, 720), "기호 하나 = 세 글자 SCH  ('모임'이라는 뜻)", font=F(46, FR), fill=WHITE)
save(im, "c13")

# c14 풀려난 첫 문장 (부록 A)
im, d = canvas()
x = left_page(im, (0, 0, 660, 890), 900) + 80
lines(d, x, 120, ["책 첫머리, 풀려난 글"], 60, GOLD, FB)
rows = [("Gesetz Buchs …", "법전"), ("geheimer Theil.", "비밀 부분"), ("erster Abschnitt", "첫째 절"),
        ("geheimer Unterricht vor die Gesellen.", "수습생을 위한 비밀 가르침"), ("Ceremonien der Aufnahme.", "입회 의식")]
y = 260
for de, ko in rows:
    d.text((x, y), de, font=F(40, FR), fill=GREY); d.text((x, y + 54), ko, font=F(50), fill=WHITE); y += 140
d.text((x, 990), "출처: Knight·Megyesi·Schaefer (2011) 부록 A", font=F(28, FR), fill=GREY)
save(im, "c14")

meta_p = os.path.join(HERE, "사진후보", "후보.json"); meta = json.load(open(meta_p, encoding="utf-8"))
base = meta["c02_1"]
for k in ["c05", "c08", "c09", "c10", "c11", "c12", "c13", "c14"]:
    meta[k + "_도표"] = {"title": "도표: " + k, "artist": "코피알레 암호 원본(18세기) 위에 그린 설명 도표", "license": "Public domain", "page": base["page"], "source": "Wikimedia Commons"}
json.dump(meta, open(meta_p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("ok")
