"""나스카 도표 → 사진/c11.jpg(AI 찾기 과정), 사진/c15.jpg(두 종류의 그림)  (python 도표_만들기.py — 사진 찾기가 끝난 뒤)
숫자: Sakai 외, PNAS 121(40) e2407652121 (2024) — 후보 47,410 → 유망 1,309 → 확인 303 (2022.9~2023.2), 36곳 중 1곳, 사진 확인 1,200시간·현장 1,440시간
 선 그림 평균 90m·50개·야생 동물 64%·의식용 직선망에서 평균 34m / 부조 그림 평균 9m·사람과 사람이 다룬 것 81.6%·오솔길에서 평균 43m"""
import json, os
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 1920, 1080
FB = "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf"
FR = "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"
GOLD, WHITE, GREY, SAND, BLUE = (255, 214, 140), (240, 240, 240), (175, 165, 150), (210, 150, 100), (120, 190, 255)
F = lambda s, f=FB: ImageFont.truetype(f, s)


def base(title):
    im = Image.new("RGB", (W, H), (40, 28, 22)); d = ImageDraw.Draw(im)
    d.text((110, 80), title, font=F(62), fill=GOLD)
    return im, d


def save(im, name):
    os.makedirs(os.path.join(HERE, "사진"), exist_ok=True)
    im.save(os.path.join(HERE, "사진", name + ".jpg"), quality=92)


# c11 AI 찾기 과정 (깔때기)
im, d = base("인공지능과 사람이 함께 찾은 303개")
steps = [(1500, "47,410곳", "인공지능이 고른 후보"), (1280, "1,309곳", "사람이 사진으로 추림 (1,200시간)"), (1060, "303개", "걸어서 확인한 새 그림 (1,440시간)")]
y = 230
for w, n, t in steps:
    x0 = (W - w) // 2
    d.rounded_rectangle((x0, y, x0 + w, y + 170), 20, fill=(90, 60, 45), outline=SAND, width=5)
    d.text((x0 + 40, y + 30), n, font=F(72), fill=WHITE)
    d.text((x0 + 40 + int(F(72).getlength(n)) + 40, y + 60), t, font=F(38, FR), fill=GOLD)
    y += 230
d.text((110, 960), "평균 36곳을 봐야 1곳의 유망 후보 · 2022년 9월~2023년 2월 · Sakai 외, PNAS (2024)", font=F(32, FR), fill=GREY)
save(im, "c11")

# c15 두 종류의 그림
im, d = base("나스카 그림은 두 종류")
cols = [(110, "거대한 선 그림", ["평균 길이 90m", "주로 야생 동물 (64%)", "의식용 직선 길에서 평균 34m", "→ 공동체가 함께 치른 의식"], BLUE),
        (1000, "작은 부조 그림", ["평균 크기 9m", "사람·가축·잘린 머리 (81.6%)", "구불구불한 오솔길에서 평균 43m", "→ 길 가는 사람·작은 무리가 봄"], SAND)]
for x, t, rows, c in cols:
    d.rounded_rectangle((x, 210, x + 810, 900), 30, outline=c, width=6, fill=(55, 38, 30))
    d.text((x + 50, 250), t, font=F(56), fill=c)
    for i, r in enumerate(rows):
        d.text((x + 50, 380 + i * 120), r, font=F(42, FR if i < 3 else FB), fill=WHITE)
d.text((110, 960), "Sakai 외, PNAS (2024) — 새로 찾은 그림까지 모아 처음으로 비교", font=F(32, FR), fill=GREY)
save(im, "c15")

mp = os.path.join(HERE, "사진후보", "후보.json")
meta = json.load(open(mp, encoding="utf-8")) if os.path.exists(mp) else {}
for k in ["c11", "c15"]:
    meta[k + "_도표"] = {"title": "도표: " + k, "artist": "설명 도표 (Sakai 외 2024 수치)", "license": "—", "page": "", "source": "설명 도표", "file": k + ".jpg"}
json.dump(meta, open(mp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("ok")
