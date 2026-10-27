"""일식709 도표 → 사진/c08·c10·c13·c17.jpg  (python 도표_만들기.py — 사진 찾기가 끝난 뒤)
숫자: Hayakawa 외, ApJL 995(1) (2025) — 기원전 709년 7월 17일, 곡부 좌표 바로잡음(약 8km, N35°36′ E116°59′),
 ΔT 20,264~21,204초, 호메로스(신아시리아) 극소기 기원전 808~717년, 709년 태양 활동 11년 주기 꼭대기 근처"""
import json, os
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 1920, 1080
FB = "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf"
FR = "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"
GOLD, WHITE, GREY, BLUE, RED, SUN = (255, 214, 140), (240, 240, 240), (170, 175, 185), (120, 180, 255), (235, 110, 100), (255, 190, 80)
BG = (16, 20, 34)
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


# c06 일식 원리
im, d = base("해가 달에 꼭 맞게 가려지는 까닭")
d.polygon([(320, 340), (1700, 528), (1700, 552), (320, 740)], fill=(40, 46, 70))
d.ellipse((120, 340, 520, 740), fill=SUN); d.text((320, 780), "해", font=F(48), fill=SUN, anchor="ma")
d.text((1255, 600), "달", font=F(44), fill=WHITE, anchor="ma"); d.text((1670, 600), "지구", font=F(44), fill=BLUE, anchor="ma")
d.ellipse((1240, 525, 1270, 555), fill=(200, 200, 210)); d.ellipse((1640, 510, 1700, 570), fill=BLUE)
d.text((160, 230), "해는 달보다 약 400배 크고, 약 400배 멀리 있다 → 하늘에서 크기가 거의 같다", font=F(42), fill=WHITE)
note(d, "크기와 거리는 실제 비율이 아닌 설명 그림")
save(im, "c06")

# c08 개기일식 띠
im, d = base("개기일식은 좁은 띠 안에서만 보인다")
d.polygon([(100, 820), (1820, 300), (1820, 420), (100, 940)], fill=(40, 46, 80))
d.polygon([(100, 860), (1820, 340), (1820, 380), (100, 900)], fill=(70, 80, 140))
d.text((1250, 470), "개기일식이 보이는 띠", font=F(42), fill=WHITE)
for x, y, t, c in [(760, 640, "기록이 맞다면 여기", SUN), (760, 380, "띠 밖 = 부분일식만", GREY)]:
    d.ellipse((x - 18, y - 18, x + 18, y + 18), fill=c); d.text((x + 40, y - 26), t, font=F(42), fill=c)
note(d, "띠에서 조금만 벗어나도 해가 다 가려지지 않음")
save(im, "c08")

# c10 곡부 좌표
im, d = base("곡부의 위치를 바로잡자 기록이 맞았다")
d.rectangle((300, 260, 1620, 860), outline=(60, 70, 100), width=3)
d.ellipse((520, 480, 560, 520), fill=GREY); d.text((470, 540), "예전 연구가 쓴 좌표", font=F(40), fill=GREY)
d.ellipse((1180, 430, 1240, 490), fill=SUN); d.text((1100, 300), "발굴로 찾은 옛 곡부 궁정", font=F(42), fill=SUN)
d.text((1100, 360), "북위 35°36′ · 동경 116°59′", font=F(36, FR), fill=WHITE)
d.line([(560, 500), (1180, 460)], fill=WHITE, width=4)
d.text((780, 410), "약 8km", font=F(48), fill=WHITE)
note(d, "Hayakawa 외, The Astrophysical Journal Letters (2025) — 고고학 발굴 보고서로 좌표를 바로잡음")
save(im, "c10")

# c13 ΔT
im, d = base("지구의 시계가 늦어진 만큼, 델타 티(ΔT)")
d.text((W // 2, 330), "20,264 ~ 21,204초", font=F(110), fill=WHITE, anchor="mm")
d.text((W // 2, 470), "약 5시간 40분 ~ 5시간 50분", font=F(60), fill=GOLD, anchor="mm")
rows = ["지구가 늘 지금 속도로 돌았다고 하면 → 일식 장소가 수천 km 어긋남", "밀물·썰물의 마찰이 자전을 조금씩 늦춤 (100년에 약 1천분의 2초)",
        "→ 2,700년 전 지구는 지금보다 조금 더 빨리 돌았다"]
for i, t in enumerate(rows):
    d.text((160, 600 + i * 90), t, font=F(42, FR if i < 2 else FB), fill=WHITE if i < 2 else SUN)
note(d, "기원전 709년 7월 17일 일식 · Hayakawa 외 (2025)")
save(im, "c13")

# c17 태양 주기
im, d = base("태양은 잠에서 깨어나고 있었다")
import math
pts = []
for x in range(160, 1780, 4):
    yr = -840 + (x - 160) / 1620 * 180                       # 기원전 840 ~ 660년
    amp = 0.15 if -808 <= yr <= -717 else 1.0
    pts.append((x, 700 - amp * 230 * (0.5 + 0.5 * math.sin((yr + 840) / 11 * 2 * math.pi))))
x0 = 160 + int((-808 + 840) / 180 * 1620); x1 = 160 + int((-717 + 840) / 180 * 1620)
d.rectangle((x0, 300, x1, 760), fill=(34, 40, 66)); d.text((x0 + 30, 310), "호메로스 극소기 (기원전 808~717년)", font=F(40), fill=BLUE)
d.line(pts, fill=SUN, width=6)
xe = 160 + int((-709 + 840) / 180 * 1620)
d.line([(xe, 280), (xe, 780)], fill=RED, width=5); d.text((xe + 15, 230), "기원전 709년 일식", font=F(42), fill=RED)
d.line([(160, 760), (1780, 760)], fill=WHITE, width=3)
d.text((160, 780), "기원전 840년", font=F(34, FR), fill=GREY); d.text((1780, 780), "기원전 660년", font=F(34, FR), fill=GREY, anchor="ra")
note(d, "곡선은 모양을 보여 주는 설명 그림 · 나이테 방사성탄소 복원과 맞음 (Hayakawa 외 2025)")
save(im, "c17")

mp = os.path.join(HERE, "사진후보", "후보.json")
meta = json.load(open(mp, encoding="utf-8")) if os.path.exists(mp) else {}
for k in ["c06", "c08", "c10", "c13", "c17"]:
    meta[k + "_도표"] = {"title": "도표: " + k, "artist": "설명 도표 (Hayakawa 외 2025)", "license": "—", "page": "", "source": "설명 도표", "file": k + ".jpg"}
json.dump(meta, open(mp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("ok")
