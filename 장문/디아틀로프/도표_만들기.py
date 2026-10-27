"""디아틀로프 도표 → 사진/c15.jpg(그날 밤의 위치), c17.jpg(수많은 가설), c20.jpg(눈판 눈사태 과정)  (사진 찾기가 끝난 뒤)
내용: 텐트(홀라트샤흘 비탈) → 약 1.5km 아래 숲 가장자리 삼나무(2명) / 비탈(3명) / 계곡 눈 아래(4명, 5월 4일)
 Gaume·Puzrin 2021: 비탈 깎기 → 활강풍이 위쪽에 눈 쌓음 → 적어도 9시간 뒤 금·무너짐 → 약 5m 눈판이 스키 깐 텐트 바닥 위로"""
import json, os
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 1920, 1080
FB = "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf"
FR = "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"
GOLD, WHITE, GREY, BLUE, RED = (255, 214, 140), (240, 240, 240), (170, 175, 185), (140, 190, 255), (255, 120, 100)
F = lambda s, f=FB: ImageFont.truetype(f, s)


def base(t):
    im = Image.new("RGB", (W, H), (22, 28, 40)); d = ImageDraw.Draw(im)
    d.text((110, 80), t, font=F(62), fill=GOLD)
    return im, d


def save(im, n):
    os.makedirs(os.path.join(HERE, "사진"), exist_ok=True); im.save(os.path.join(HERE, "사진", n + ".jpg"), quality=92)


im, d = base("그날 밤의 위치")
d.polygon([(110, 300), (1810, 900), (110, 900)], fill=(220, 228, 240))           # 비탈
d.rectangle((260, 330, 360, 380), fill=(120, 100, 80)); d.text((200, 230), "텐트 (안쪽에서 찢김)", font=F(36), fill=WHITE)
for x in range(380, 1420, 70):
    d.ellipse((x, 380 + (x - 380) * 0.33, x + 14, 394 + (x - 380) * 0.33), fill=(90, 90, 110))   # 발자국
d.text((620, 470), "발자국 · 약 1.5km 아래로", font=F(34), fill=(40, 40, 60))
d.polygon([(1500, 640), (1460, 760), (1540, 760)], fill=(40, 110, 60)); d.rectangle((1494, 760, 1506, 800), fill=(90, 60, 30))
d.text((1380, 560), "삼나무 · 모닥불 (2명)", font=F(36), fill=WHITE)
d.text((700, 610), "비탈 (3명)", font=F(36), fill=RED)
d.text((1560, 850), "계곡 눈 아래 (4명, 5월)", font=F(34), fill=RED)
d.text((110, 960), "북부 우랄 홀라트샤흘산, 1959년 2월 1~2일 밤", font=F(32, FR), fill=GREY)
save(im, "c15")

im, d = base("60년 동안 나온 가설들")
for i, (a, b, c) in enumerate([("군사 무기 실험", "증거 없음", GREY), ("귀에 안 들리는 낮은 소리(초저주파)", "증거 없음", GREY), ("설인·외계인", "증거 없음", GREY), ("거센 바람(활강풍)", "일부 설명", BLUE), ("눈사태", "가장 유력하지만 의문점이 남음", GOLD)]):
    y = 230 + i * 140
    d.text((150, y), "· " + a, font=F(46, FR), fill=WHITE); d.text((1180, y + 4), b, font=F(42), fill=c)
save(im, "c17")

im, d = base("작은 눈판 눈사태 (가우메·푸즈린 2021)")
steps = [("① 텐트 자리 깎기", "비탈의 눈을 깎아 평평하게"), ("② 바람이 눈을 쌓음", "활강풍이 위쪽에 눈을 실어 옴"), ("③ 금이 감", "적어도 9시간쯤 뒤"), ("④ 눈판이 무너짐", "약 5m 크기, 흔적이 적음")]
x = 110
for i, (a, b) in enumerate(steps):
    d.rounded_rectangle((x, 300, x + 390, 640), 26, outline=BLUE, width=5, fill=(34, 44, 64))
    d.text((x + 28, 340), a, font=F(42), fill=WHITE)
    d.text((x + 28, 450), b, font=F(32, FR), fill=GOLD)
    if i < 3:
        d.text((x + 400, 430), "→", font=F(56), fill=BLUE)
    x += 450
d.text((110, 760), "스키를 깔고 누운 사람 위로 단단한 눈판 → 겉 상처 없이 가슴·머리 부상 (모의실험)", font=F(38, FR), fill=WHITE)
d.text((110, 900), "연구팀도 '사건을 다 풀었다고 하지 않는다'", font=F(34, FR), fill=GREY)
save(im, "c20")

mp = os.path.join(HERE, "사진후보", "후보.json")
meta = json.load(open(mp, encoding="utf-8")) if os.path.exists(mp) else {}
for k in ["c15", "c17", "c20"]:
    meta[k + "_도표"] = {"title": "도표: " + k, "artist": "설명 도표", "license": "—", "page": "", "source": "설명 도표", "file": k + ".jpg"}
json.dump(meta, open(mp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("ok")
