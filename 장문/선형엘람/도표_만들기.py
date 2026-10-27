"""선형 엘람 문자 도표 → 사진/c15.jpg(글이 너무 적다), c17.jpg(은잔 속 이름 맞추기), c19.jpg(기호 72개)  (사진 찾기가 끝난 뒤)
숫자: 원시 엘람 점토판 1,600개 넘게(아직 해독 못 함) / 선형 엘람 글 약 50개(마더 2021: 51) / 사자 판으로 읽은 기호 약 9개 /
 데세 외 2022: 기호 72개 소리, 알려진 기호의 96% 넘게 / 이름: 실하하·에바라트(왕), 나피리샤(신)"""
import json, os
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 1920, 1080
FB = "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf"
FR = "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"
GOLD, WHITE, GREY, SILVER, RED = (255, 214, 140), (240, 240, 240), (170, 165, 155), (200, 205, 215), (255, 120, 100)
F = lambda s, f=FB: ImageFont.truetype(f, s)


def base(t):
    im = Image.new("RGB", (W, H), (34, 28, 24)); d = ImageDraw.Draw(im)
    d.text((110, 80), t, font=F(62), fill=GOLD)
    return im, d


def save(im, n):
    os.makedirs(os.path.join(HERE, "사진"), exist_ok=True); im.save(os.path.join(HERE, "사진", n + ".jpg"), quality=92)


im, d = base("남아 있는 글의 수")
rows = [("원시 엘람 문자 (기원전 3000년 무렵)", 1600, "1,600개 넘게 · 아직 해독 못 함"), ("선형 엘람 문자 (기원전 2300~1880년)", 50, "약 50개")]
for i, (a, n, b) in enumerate(rows):
    y = 260 + i * 280
    d.text((110, y), a, font=F(44, FR), fill=WHITE)
    d.rectangle((110, y + 80, 110 + int(1600 * n / 1600), y + 150), fill=SILVER if i == 0 else RED)
    d.text((110, y + 165), b, font=F(40), fill=GOLD)
d.text((110, 880), "단서가 너무 적어 '영원히 못 읽을 것'이라는 말까지 나왔던 문자", font=F(38, FR), fill=GREY)
save(im, "c15")

im, d = base("은잔 속 이름 맞추기 (샹폴리옹의 방법)")
for i, (cu, nm) in enumerate([("쐐기문자로 쓴 왕의 이름", "실하하"), ("쐐기문자로 쓴 왕의 이름", "에바라트"), ("쐐기문자로 쓴 신의 이름", "나피리샤")]):
    y = 260 + i * 200
    d.rounded_rectangle((110, y, 760, y + 150), 20, outline=SILVER, width=4, fill=(50, 44, 40))
    d.text((140, y + 20), cu, font=F(32, FR), fill=GREY); d.text((140, y + 70), nm, font=F(52), fill=WHITE)
    d.text((800, y + 45), "→", font=F(70), fill=GOLD)
    d.rounded_rectangle((920, y, 1800, y + 150), 20, outline=GOLD, width=4, fill=(60, 48, 34))
    d.text((950, y + 50), "같은 소리가 될 선형 엘람 기호 묶음", font=F(40, FR), fill=GOLD)
d.text((110, 900), "이름에서 얻은 소리 → 다른 글에 넣어 보기 → '주었다'·'만들었다' 같은 낱말이 읽힘", font=F(36, FR), fill=WHITE)
save(im, "c17")

im, d = base("100년 만의 해독")
d.text((110, 260), "1900년대 초 (사자 판)", font=F(48, FR), fill=WHITE); d.text((1150, 250), "기호 약 9개", font=F(64), fill=SILVER)
d.text((110, 450), "2022년 (데세 연구팀)", font=F(48, FR), fill=WHITE); d.text((1150, 440), "기호 72개", font=F(80), fill=GOLD)
d.text((110, 640), "→ 알려진 기호의 96% 넘게 소리를 읽음", font=F(50), fill=RED)
d.text((110, 880), "Desset 외, 아시리아학 잡지 112권 (2022) — 뜻까지 완전한 번역은 아직", font=F(34, FR), fill=GREY)
save(im, "c19")

mp = os.path.join(HERE, "사진후보", "후보.json")
meta = json.load(open(mp, encoding="utf-8")) if os.path.exists(mp) else {}
for k in ["c15", "c17", "c19"]:
    meta[k + "_도표"] = {"title": "도표: " + k, "artist": "설명 도표 (Desset 외 2022)", "license": "—", "page": "", "source": "설명 도표", "file": k + ".jpg"}
json.dump(meta, open(mp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("ok")
