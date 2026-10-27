"""로미토 도표 → 사진/c09·c11·c15·c17.jpg  (python 도표_만들기.py — 사진 찾기가 끝난 뒤)
숫자: Fernandes 외, NEJM 394(5): 513 (2026) — 로미토 1 약 145cm·로미토 2 약 110cm, 둘 다 여자·1촌(엄마와 딸이 가장 그럴듯),
 로미토 2 NPR2 변이 두 벌(마로토형), 로미토 1 한 벌 / 아빠 한 벌은 추정"""
import json, os
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 1920, 1080
FB = "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf"
FR = "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"
GOLD, WHITE, GREY, ROSE, TEAL, RED = (255, 214, 140), (240, 240, 240), (175, 165, 160), (240, 150, 160), (120, 200, 190), (235, 110, 100)
BG = (34, 26, 24)
F = lambda s, f=FB: ImageFont.truetype(f, s)


def base(title):
    im = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(im)
    d.text((110, 80), title, font=F(62), fill=GOLD)
    return im, d


def note(d, t):
    d.text((110, 960), t, font=F(32, FR), fill=GREY)


def save(im, name):
    os.makedirs(os.path.join(HERE, "사진"), exist_ok=True)
    im.save(os.path.join(HERE, "사진", name + ".jpg"), quality=92)


def person(d, x, h, c, short=False):                       # 단순한 사람 모양 (발끝 y=880, h cm → 픽셀)
    px = h * 3.6; top = 880 - px; head = px * 0.13
    d.ellipse((x - head / 2, top, x + head / 2, top + head), fill=c)
    leg = px * (0.32 if short else 0.47); arm = px * (0.22 if short else 0.36)
    body_top, body_bot = top + head + 6, 880 - leg
    d.rounded_rectangle((x - px * 0.11, body_top, x + px * 0.11, body_bot), 18, fill=c)
    d.line([(x - px * 0.11, body_top + 14), (x - px * 0.2, body_top + 14 + arm)], fill=c, width=16)
    d.line([(x + px * 0.11, body_top + 14), (x + px * 0.2, body_top + 14 + arm)], fill=c, width=16)
    d.line([(x - px * 0.05, body_bot), (x - px * 0.07, 880)], fill=c, width=18)
    d.line([(x + px * 0.05, body_bot), (x + px * 0.07, 880)], fill=c, width=18)


# c09 두 사람
im, d = base("함께 묻힌 두 사람")
person(d, 620, 145, TEAL); person(d, 1240, 110, ROSE, short=True)
d.line([(300, 882), (1620, 882)], fill=WHITE, width=3)
d.text((620, 900), "로미토 1 · 약 145cm", font=F(44), fill=TEAL, anchor="ma")
d.text((1240, 900), "로미토 2 · 약 110cm", font=F(44), fill=ROSE, anchor="ma")
d.text((1420, 560), "팔다리가\n유난히 짧음", font=F(40), fill=WHITE)
note(d, "1963년 이탈리아 남부 로미토 동굴 · 키는 뼈로 추정한 값 · 사람 모양은 설명용")
save(im, "c09")

# c11 수수께끼
im, d = base("60년 동안 풀리지 않은 질문")
for i, t in enumerate(["로미토 2는 남자일까, 여자일까?", "두 사람은 어떤 사이였을까?", "둘 다 작았던 까닭은 같을까?", "어떤 병이었을까? — 뼈만으로는 알 수 없음"]):
    y = 230 + i * 165
    d.rounded_rectangle((110, y, 1810, y + 130), 22, fill=(58, 44, 40), outline=GOLD if i < 3 else RED, width=4)
    d.text((160, y + 40), t, font=F(52), fill=WHITE)
save(im, "c11")

# c15 DNA가 밝힌 답
im, d = base("DNA가 밝힌 답")
ans = [("둘 다 여자", "남자로 알려졌던 로미토 2는 소녀"), ("1촌 가족", "엄마와 딸일 가능성이 가장 큼"), ("같은 유전자 NPR2", "딸은 변이 두 벌, 엄마는 한 벌")]
for i, (a, b) in enumerate(ans):
    y = 230 + i * 220
    d.rounded_rectangle((110, y, 1810, y + 180), 26, fill=(58, 44, 40), outline=TEAL, width=5)
    d.text((170, y + 30), a, font=F(64), fill=WHITE); d.text((170, y + 112), b, font=F(42, FR), fill=GOLD)
note(d, "Fernandes 외, New England Journal of Medicine (2026) — 귀 안쪽 뼈에서 뽑은 고대 DNA")
save(im, "c15")

# c17 유전
im, d = base("변이 두 벌과 한 벌")
def box(x, y, t, s, c):
    d.rounded_rectangle((x, y, x + 520, y + 220), 26, fill=(58, 44, 40), outline=c, width=5)
    d.text((x + 260, y + 60), t, font=F(54), fill=WHITE, anchor="mm"); d.text((x + 260, y + 150), s, font=F(40, FR), fill=c, anchor="mm")
box(220, 220, "엄마 (로미토 1)", "변이 한 벌 → 조금 작은 키", TEAL)
box(1180, 220, "아빠 (추정)", "변이 한 벌을 가졌을 것", GREY)
box(700, 600, "딸 (로미토 2)", "변이 두 벌 → 마로토형", ROSE)
d.line([(480, 440), (900, 600)], fill=WHITE, width=5); d.line([(1440, 440), (1020, 600)], fill=WHITE, width=5)
note(d, "유전자는 엄마에게서 한 벌, 아빠에게서 한 벌씩 받음 · 아빠는 유전 원리로 본 추정")
save(im, "c17")

mp = os.path.join(HERE, "사진후보", "후보.json")
meta = json.load(open(mp, encoding="utf-8")) if os.path.exists(mp) else {}
for k in ["c09", "c11", "c15", "c17"]:
    meta[k + "_도표"] = {"title": "도표: " + k, "artist": "설명 도표 (Fernandes 외 2026)", "license": "—", "page": "", "source": "설명 도표", "file": k + ".jpg"}
os.makedirs(os.path.dirname(mp), exist_ok=True)
json.dump(meta, open(mp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("ok")
