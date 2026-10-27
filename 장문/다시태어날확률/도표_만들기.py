"""다시 태어날 확률 도표 → 사진/c05.jpg(몸의 원자), c09.jpg(같은 배열이 다시 나올 확률), c16.jpg(뇌 속의 숫자)  (사진 찾기가 끝난 뒤 실행)
숫자: 몸의 원자 약 7×10^27 / 신경세포 약 860억(Azevedo 2009) / 초파리 뇌 약 14만 신경세포·5천만 연결(FlyWire, Nature 2024)
 / 사람 대뇌 1㎣ 세포 약 5만 7천·연결 약 1억 5천만·1.4페타바이트(Shapson-Coe, Science 2024)"""
import json, os, random
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 1920, 1080
FB = "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf"
FR = "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"
GOLD, WHITE, GREY, BLUE, PINK = (255, 214, 140), (240, 240, 240), (165, 165, 180), (120, 190, 255), (255, 150, 190)
F = lambda s, f=FB: ImageFont.truetype(f, s)


def space(title):
    random.seed(11)
    im = Image.new("RGB", (W, H), (10, 12, 26)); d = ImageDraw.Draw(im)
    for _ in range(700):
        x, y, r = random.randrange(W), random.randrange(H), random.choice([0, 0, 1, 1, 2])
        c = random.randint(70, 200); d.ellipse((x - r, y - r, x + r, y + r), fill=(c, c, min(255, c + 25)))
    d.text((120, 90), title, font=F(62), fill=GOLD)
    return im, d


def save(im, name):
    os.makedirs(os.path.join(HERE, "사진"), exist_ok=True)
    im.save(os.path.join(HERE, "사진", name + ".jpg"), quality=92)


im, d = space("우리 몸을 이루는 원자")
d.text((120, 260), "약 7,000,000,000,000,000,000,000,000,000개", font=F(56), fill=WHITE)
d.text((120, 350), "= 7 뒤에 0이 27개 (7천 자)", font=F(46, FR), fill=BLUE)
for i, (a, b) in enumerate([("수소", "우주가 처음 생길 때 (빅뱅)"), ("탄소·산소·질소", "별의 뜨거운 속"), ("칼슘·철", "별의 속과 별의 폭발")]):
    d.text((160, 520 + i * 110), "· " + a, font=F(46), fill=WHITE)
    d.text((780, 524 + i * 110), b, font=F(42, FR), fill=GOLD)
d.text((120, 920), "숨 쉬고 먹을 때마다 들어오고 나가며, 죽은 뒤엔 흙·물·공기로 돌아감", font=F(36, FR), fill=GREY)
save(im, "c05")

im, d = space("같은 배열이 다시 나올 확률")
rows = [("동전 10개가 모두 앞면", "1,024번에 1번"), ("주사위 10개가 모두 6", "약 6천만 번에 1번"), ("원자 7천 자 개가 같은 자리로", "우주 나이로도 닿지 않음")]
for i, (a, b) in enumerate(rows):
    y = 280 + i * 170
    d.text((140, y), a, font=F(48, FR), fill=WHITE)
    d.text((1150, y), b, font=F(48), fill=PINK if i == 2 else BLUE)
d.text((140, 820), "0은 아니지만, 사실상 0", font=F(64), fill=GOLD)
d.text((140, 930), "푸앵카레 재귀(1890): 갇힌 입자들은 아주 오래 기다리면 처음과 거의 같은 배열로 돌아옴", font=F(32, FR), fill=GREY)
save(im, "c09")

im, d = space("뇌 속의 숫자")
boxes = [("사람의 뇌", "신경세포 약 860억 개"), ("초파리 뇌 (2024)", "신경세포 약 14만 개 · 연결 5천만 개 이상"), ("사람 대뇌 1㎣ (2024)", "세포 약 5만 7천 개 · 연결 약 1억 5천만 개 · 자료 1.4페타바이트")]
for i, (a, b) in enumerate(boxes):
    y = 240 + i * 210
    d.rounded_rectangle((120, y, 1800, y + 170), 24, outline=BLUE, width=4, fill=(20, 26, 50))
    d.text((160, y + 30), a, font=F(48), fill=GOLD)
    d.text((160, y + 100), b, font=F(38, FR), fill=WHITE)
d.text((120, 920), "나를 만드는 것 = 재료가 아니라 연결의 무늬 (커넥톰)", font=F(44), fill=PINK)
save(im, "c16")

mp = os.path.join(HERE, "사진후보", "후보.json")
meta = json.load(open(mp, encoding="utf-8")) if os.path.exists(mp) else {}
for k in ["c05", "c09", "c16"]:
    meta[k + "_도표"] = {"title": "도표: " + k, "artist": "설명 도표", "license": "—", "page": "", "source": "설명 도표", "file": k + ".jpg"}
json.dump(meta, open(mp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("ok")
