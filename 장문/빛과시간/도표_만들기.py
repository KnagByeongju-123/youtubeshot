"""빛과 시간 설명 도표 → 사진/<컷>.jpg  (python 도표_만들기.py)
숫자: 달 약 1.3초, 태양 약 8분 20초, 베텔게우스 약 500~700광년, 안드로메다 약 250만 광년, JADES-GS-z14-0 약 135억 년(빛이 달려온 시간)
우주 나이 약 138억 년, 관측 가능한 우주 반지름 약 465억 광년(Planck 2018), 눈→뇌 약 0.1초 안팎"""
import json, os, random
from PIL import Image, ImageDraw, ImageFont, ImageFilter
HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 1920, 1080
FB = "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf"
FR = "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"
GOLD, WHITE, GREY, BLUE, RED = (255, 222, 150), (240, 240, 240), (165, 165, 175), (120, 190, 255), (255, 110, 90)


def F(size, f=FB):
    return ImageFont.truetype(f, size)


def space():
    """별이 뿌려진 어두운 바탕"""
    random.seed(7)
    im = Image.new("RGB", (W, H), (8, 10, 22))
    d = ImageDraw.Draw(im)
    for _ in range(900):
        x, y, r = random.randrange(W), random.randrange(H), random.choice([0, 0, 0, 1, 1, 2])
        c = random.randint(90, 230)
        d.ellipse((x - r, y - r, x + r, y + r), fill=(c, c, min(255, c + 20)))
    return im, ImageDraw.Draw(im)


def save(im, name):
    os.makedirs(os.path.join(HERE, "사진"), exist_ok=True)
    im.save(os.path.join(HERE, "사진", name + ".jpg"), quality=92)


# c07 빛이 걸리는 시간
im, d = space()
d.text((150, 110), "지금 보는 빛은 언제 떠났을까", font=F(64), fill=GOLD)
rows = [("달", "약 1.3초 전"), ("태양", "약 8분 20초 전"), ("베텔게우스", "약 500~700년 전"), ("안드로메다은하", "약 250만 년 전"), ("가장 먼 은하 (JADES-GS-z14-0)", "약 135억 년 전")]
y = 270
for i, (a, b) in enumerate(rows):
    d.ellipse((150, y + 12, 186, y + 48), fill=(255, 210 - i * 30, 120 + i * 25))
    d.text((220, y), a, font=F(50, FR), fill=WHITE)
    d.text((1200, y), b, font=F(52), fill=BLUE)
    y += 120
d.text((150, 900), "밤하늘 = 서로 다른 시간에 떠난 빛이 한 화면에 겹친 것", font=F(40, FR), fill=GREY)
save(im, "c07")

# c10 138억 년인데 465억 광년
im, d = space()
d.text((150, 110), "우주 나이는 138억 년인데", font=F(64), fill=GOLD)
cx, cy = 1350, 560
for r, col, lab in [(420, BLUE, "볼 수 있는 우주의 끝 · 약 465억 광년 (지금 거리)"), (125, RED, "빛이 달린 시간 · 약 138억 년")]:
    d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=col, width=5)
d.ellipse((cx - 14, cy - 14, cx + 14, cy + 14), fill=(120, 200, 255))
d.text((cx - 40, cy + 22), "지구", font=F(32), fill=WHITE)
d.text((150, 300), "빛이 오는 동안에도", font=F(50, FR), fill=WHITE)
d.text((150, 380), "공간이 계속 늘어나", font=F(50, FR), fill=WHITE)
d.text((150, 460), "빛이 출발한 곳은", font=F(50, FR), fill=WHITE)
d.text((150, 540), "훨씬 멀어졌다", font=F(50), fill=GOLD)
d.text((150, 700), "━  약 465억 광년 (지금 거리)", font=F(36), fill=BLUE)
d.text((150, 760), "━  약 138억 년 (빛이 달린 시간)", font=F(36), fill=RED)
save(im, "c10")

# c16 눈에서 뇌까지
im, d = space()
d.text((150, 110), "보는 데도 시간이 걸린다", font=F(64), fill=GOLD)
boxes = [("빛", "눈에 닿음"), ("눈", "빛 → 신호"), ("신경", "신호를 뇌로"), ("뇌", "장면을 만듦")]
x = 150
for i, (a, b) in enumerate(boxes):
    d.rounded_rectangle((x, 380, x + 330, 620), 24, outline=BLUE, width=4, fill=(18, 26, 50))
    d.text((x + 40, 410), a, font=F(70), fill=WHITE)
    d.text((x + 40, 520), b, font=F(38, FR), fill=GREY)
    if i < 3:
        d.text((x + 345, 455), "→", font=F(70), fill=GOLD)
    x += 430
d.text((150, 720), "모두 합쳐 약 0.1초 안팎", font=F(60), fill=GOLD)
d.text((150, 820), "그래서 뇌는 움직이는 것의 위치를 조금 앞당겨 예측한다 (Nijhawan, Nature 1994)", font=F(34, FR), fill=GREY)
save(im, "c16")

# c19 우주의 '지금' 지도
im, d = space()
d.text((150, 110), "우주의 '지금' 지도", font=F(64), fill=GOLD)
ex, ey = 360, 620
d.ellipse((ex - 16, ey - 16, ex + 16, ey + 16), fill=(120, 200, 255)); d.text((ex - 40, ey + 26), "지구", font=F(32), fill=WHITE)
g1, g2 = (900, 620), (1600, 620)
d.ellipse((g1[0] - 22, g1[1] - 22, g1[0] + 22, g1[1] + 22), outline=RED, width=4)
d.ellipse((g2[0] - 26, g2[1] - 26, g2[0] + 26, g2[1] + 26), fill=GOLD)
d.line((ex + 30, ey, g1[0] - 30, g1[1]), fill=RED, width=4)
d.line((g1[0] + 30, g1[1], g2[0] - 34, g2[1]), fill=GOLD, width=4)
d.text((g1[0] - 180, g1[1] - 120), "보이는 모습", font=F(40), fill=RED)
d.text((g1[0] - 220, g1[1] + 50), "빛이 떠날 때의 위치·모습", font=F(32, FR), fill=GREY)
d.text((g2[0] - 170, g2[1] - 120), "계산한 '지금'", font=F(40), fill=GOLD)
d.text((g2[0] - 250, g2[1] + 50), "그동안 우주가 늘어난 만큼", font=F(32, FR), fill=GREY)
d.text((150, 300), "기준: 우주배경복사로 정한 '우주 시간'", font=F(44, FR), fill=WHITE)
d.text((150, 860), "'지금' 지도는 눈으로 볼 수 없고, 관측한 빛을 거꾸로 계산해야 그릴 수 있다", font=F(36, FR), fill=GREY)
save(im, "c19")

# c30 GPS 위성 시계 (상대성 이론)
im, d = space()
d.text((150, 110), "GPS 위성의 시계는 더 빨리 간다", font=F(64), fill=GOLD)
d.ellipse((1250, 520, 1650, 920), fill=(30, 80, 160)); d.text((1380, 690), "지구", font=F(48), fill=WHITE)
d.rectangle((1500, 220, 1580, 270), fill=(200, 200, 210)); d.rectangle((1420, 232, 1500, 258), fill=(80, 120, 200)); d.rectangle((1580, 232, 1660, 258), fill=(80, 120, 200))
d.text((1440, 290), "GPS 위성 · 약 2만 km 위", font=F(32, FR), fill=WHITE)
d.text((150, 300), "· 빠르게 돌아서 → 하루 약 7마이크로초 느려짐", font=F(42, FR), fill=WHITE)
d.text((150, 380), "· 중력이 약해서 → 하루 약 45마이크로초 빨라짐", font=F(42, FR), fill=WHITE)
d.text((150, 490), "합쳐서 하루 약 38마이크로초 빠름", font=F(56), fill=BLUE)
d.text((150, 600), "바로잡지 않으면 위치가 하루 약 10km 어긋남", font=F(48), fill=RED)
d.text((150, 720), "→ 위성 시계를 처음부터 이만큼 늦춰 맞춰 둠", font=F(40, FR), fill=GREY)
save(im, "c30")

# c34 눈에 보이는 빛은 아주 일부
im, d = space()
d.text((150, 110), "우리 눈에 보이는 빛은 아주 일부", font=F(64), fill=GOLD)
bands = [("전파", (90, 90, 120)), ("마이크로파", (100, 90, 130)), ("적외선", (150, 60, 60)), ("", None), ("자외선", (110, 70, 170)), ("엑스선", (80, 80, 150)), ("감마선", (70, 70, 120))]
x = 150
for name, col in bands:
    w_ = 210 if name else 200
    if col is None:
        for k in range(w_):
            h = k / w_
            r, g, b = [int(255 * max(0, min(1, v))) for v in (1.5 - abs(h * 4 - 0.5) if h < 0.4 else 1.5 - abs(h * 4 - 4), 1.5 - abs(h * 4 - 2), 1.5 - abs(h * 4 - 3.5))]
            d.line((x + k, 420, x + k, 560), fill=(r, g, b))
        d.text((x + 10, 590), "눈에 보이는 빛", font=F(36), fill=WHITE)
    else:
        d.rectangle((x, 420, x + w_, 560), fill=col)
        d.text((x + 15, 470), name, font=F(34, FR), fill=WHITE)
    x += w_ + 10
d.text((150, 720), "제임스 웹 망원경은 멀리서 붉게 늘어난 빛을 '적외선'으로 본다", font=F(40, FR), fill=GREY)
save(im, "c34")

meta_p = os.path.join(HERE, "사진후보", "후보.json")
meta = json.load(open(meta_p, encoding="utf-8")) if os.path.exists(meta_p) else {}
for k in ["c07", "c10", "c16", "c19", "c30", "c34"]:
    meta[k + "_도표"] = {"title": "도표: " + k, "artist": "설명 도표", "license": "—", "page": "", "source": "설명 도표", "file": k + ".jpg"}
json.dump(meta, open(meta_p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("ok")
