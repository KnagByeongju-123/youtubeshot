"""모아이 도표 → 사진/c08·c11·c13·c16·c18.jpg  (python 도표_만들기.py — 사진 찾기가 끝난 뒤)
숫자: Lipo·Hunt, Journal of Archaeological Science 183: 106383 (2025) — 석상 962개·길가 62개, D자 밑면, 앞으로 6~15도,
 4.35톤 복제·18명·100m·40분, 길 폭 약 4.5m·오목, 출발 15~60명·계속 5~25명, 버려진 석상 절반 넘게(51.6%) 채석장 2km 안"""
import json, os
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 1920, 1080
FB = "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf"
FR = "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"
GOLD, WHITE, GREY, STONE, RED, GREEN = (255, 214, 140), (240, 240, 240), (170, 175, 180), (140, 150, 160), (235, 110, 100), (120, 200, 140)
BG = (24, 32, 40)
F = lambda s, f=FB: ImageFont.truetype(f, s)


def base(title):
    im = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(im)
    d.text((110, 80), title, font=F(62), fill=GOLD)
    return im, d


def save(im, name):
    os.makedirs(os.path.join(HERE, "사진"), exist_ok=True)
    im.save(os.path.join(HERE, "사진", name + ".jpg"), quality=92)


def note(d, t):
    d.text((110, 960), t, font=F(32, FR), fill=GREY)


# c08 쏟아진 가설
im, d = base("모아이를 어떻게 옮겼을까?")
hy = [("눕혀서 통나무로 굴렸다", WHITE), ("나무 썰매에 실어 끌었다", WHITE), ("외계인이 옮겼다?", RED), ("섬사람들의 옛이야기: '걸어서 갔다'", GREEN)]
for i, (t, c) in enumerate(hy):
    y = 220 + i * 165
    d.rounded_rectangle((110, y, 1810, y + 130), 22, fill=(38, 50, 62), outline=c, width=5)
    d.text((160, y + 38), t, font=F(54), fill=c)
save(im, "c08")

# c11 길가 모아이의 비밀 (옆모습 그림)
im, d = base("길가에 쓰러진 모아이 62개의 공통점")
d.polygon([(330, 860), (600, 860), (560, 330), (470, 250), (380, 300)], fill=STONE)          # 앞으로 기운 몸 (옆모습)
d.line([(300, 862), (640, 862)], fill=WHITE, width=6)
d.line([(465, 860), (465, 260)], fill=GREY, width=3)
d.line([(465, 860), (420, 260)], fill=GOLD, width=5)
d.text((250, 200), "앞으로 6~15도", font=F(44), fill=GOLD)
cols = [("밑면이 넓은 D자", "세운 채로 좌우로 흔들 수 있음"), ("앞으로 기운 몸", "흔들 때마다 한 발씩 앞으로"), ("제단 석상과 다른 모양", "제단에 세운 뒤 밑면을 다시 깎음")]
for i, (a, b) in enumerate(cols):
    y = 260 + i * 210
    d.rounded_rectangle((820, y, 1810, y + 170), 22, fill=(38, 50, 62), outline=STONE, width=4)
    d.text((870, y + 28), a, font=F(54), fill=WHITE)
    d.text((870, y + 102), b, font=F(38, FR), fill=GOLD)
note(d, "석상 962개 조사 · Lipo·Hunt, Journal of Archaeological Science (2025)")
save(im, "c11")

# c13 실험
im, d = base("4.35톤 복제 모아이 실험")
nums = [("4.35톤", "복제 석상 무게"), ("18명", "밧줄을 잡은 사람"), ("100m", "옮긴 거리"), ("40분", "걸린 시간")]
for i, (n, t) in enumerate(nums):
    x = 110 + i * 435
    d.rounded_rectangle((x, 260, x + 395, 620), 26, fill=(38, 50, 62), outline=GOLD, width=5)
    d.text((x + 197, 400), n, font=F(92), fill=WHITE, anchor="mm")
    d.text((x + 197, 530), t, font=F(40, FR), fill=GOLD, anchor="mm")
d.text((110, 700), "통나무 없이, 밧줄 세 가닥으로 좌우로 흔들며 지그재그로", font=F(48), fill=WHITE)
note(d, "Lipo·Hunt (2012년 실험, 2025년 논문에 정리)")
save(im, "c13")

# c16 길
im, d = base("모아이가 걸은 길")
d.chord((360, 450, 1560, 750), 0, 180, fill=(70, 80, 90))                                  # 오목한 길 단면 (가운데가 깊음)
d.line([(240, 600), (360, 600)], fill=STONE, width=10); d.line([(1560, 600), (1680, 600)], fill=STONE, width=10)
d.polygon([(900, 748), (1020, 748), (1040, 470), (960, 380), (880, 470)], fill=GOLD)
d.line([(360, 590), (1560, 590)], fill=WHITE, width=3)
d.text((1300, 550), "폭 약 4.5m", font=F(48), fill=WHITE, anchor="mm")
d.text((960, 850), "가운데가 오목 → 흔들려도 옆으로 쓰러지지 않음", font=F(44), fill=GOLD, anchor="mm")
d.text((110, 1010), "출발 15~60명, 걷기 시작하면 5~25명 · 길은 석상이 나아가는 대로 새로 닦음", font=F(32, FR), fill=GREY)
save(im, "c16")

# c18 채석장 가까이 몰린 석상
im, d = base("버려진 석상은 어디에 쓰러졌나")
d.rounded_rectangle((110, 260, 1810, 420), 22, fill=(38, 50, 62))
d.rounded_rectangle((110, 260, 110 + int(1700 * 0.516), 420), 22, fill=RED)
d.text((150, 340), "51.6%  — 채석장에서 2km 안", font=F(56), fill=WHITE, anchor="lm")
for i, (x, h) in enumerate([(200, 300), (420, 210), (640, 150), (860, 105), (1080, 75), (1300, 52), (1520, 36)]):
    d.rectangle((x, 860 - h, x + 150, 860), fill=STONE)
d.line([(160, 862), (1740, 862)], fill=WHITE, width=4)
d.text((160, 880), "채석장 가까이", font=F(36, FR), fill=GREY); d.text((1740, 880), "멀리", font=F(36, FR), fill=GREY, anchor="ra")
d.text((1000, 520), "출발 직후에 많이 넘어지고, 멀수록 줄어듦", font=F(44), fill=GOLD)
note(d, "막대는 줄어드는 모습을 보여 주는 설명 그림 · Lipo·Hunt, Journal of Archaeological Science (2025)")
save(im, "c18")

mp = os.path.join(HERE, "사진후보", "후보.json")
meta = json.load(open(mp, encoding="utf-8")) if os.path.exists(mp) else {}
for k in ["c08", "c11", "c13", "c16", "c18"]:
    meta[k + "_도표"] = {"title": "도표: " + k, "artist": "설명 도표 (Lipo·Hunt 2025 수치)", "license": "—", "page": "", "source": "설명 도표", "file": k + ".jpg"}
json.dump(meta, open(mp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("ok")
