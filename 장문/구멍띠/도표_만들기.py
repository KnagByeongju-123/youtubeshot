"""구멍 띠 도표 → 사진/c05.jpg(크기), 사진/c06.jpg(쏟아진 가설) + 논문 그림 정보(후보.json)  (python 도표_만들기.py — 사진 찾기가 끝난 뒤)
숫자: Bongers 외, Antiquity 100(409) (2026, 온라인 2025-11) — 길이 약 1.5km, 폭 14~22m(평균 약 19m), 구멍 약 5,200개, 지름 1~2m, 깊이 0.5~1m, 구역 60개 이상"""
import json, os
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 1920, 1080
FB = "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf"
FR = "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"
GOLD, WHITE, GREY, SAND, RED = (255, 214, 140), (240, 240, 240), (175, 165, 150), (210, 150, 100), (235, 110, 100)
F = lambda s, f=FB: ImageFont.truetype(f, s)


def base(title):
    im = Image.new("RGB", (W, H), (40, 28, 22)); d = ImageDraw.Draw(im)
    d.text((110, 80), title, font=F(62), fill=GOLD)
    return im, d


def save(im, name):
    os.makedirs(os.path.join(HERE, "사진"), exist_ok=True)
    im.save(os.path.join(HERE, "사진", name + ".jpg"), quality=92)


# c05 구멍 띠의 크기
im, d = base("숫자로 본 구멍 띠")
rows = [("약 5,200개", "구멍의 수"), ("약 1.5km", "띠의 길이 (골짜기 바닥 → 언덕 위)"), ("평균 약 19m", "띠의 폭 (14~22m)"),
        ("1~2m · 0.5~1m", "구멍 하나의 지름 · 깊이"), ("60개 이상", "빈 틈으로 나뉜 구역")]
for i, (n, t) in enumerate(rows):
    y = 210 + i * 140
    d.rounded_rectangle((110, y, 1810, y + 115), 20, fill=(90, 60, 45), outline=SAND, width=4)
    d.text((150, y + 22), n, font=F(64), fill=WHITE)
    d.text((820, y + 38), t, font=F(42, FR), fill=GOLD)
d.text((110, 960), "페루 피스코 계곡 몬테 시에르페 · Bongers 외, Antiquity (2025)", font=F(32, FR), fill=GREY)
save(im, "c05")

# c06 쏟아진 가설
im, d = base("구멍 띠의 정체, 쏟아진 가설")
hy = ["적을 막는 방어 시설", "물·안개를 모으던 곳", "무덤", "광산", "작은 텃밭", "땅에 그린 그림(지상화)", "곡식 창고 (1984)", "회계·임시 보관 (2015)", "외계인의 흔적?"]
for i, t in enumerate(hy):
    c, r = divmod(i, 5)
    x, y = 110 + c * 870, 220 + r * 140
    col = RED if "외계인" in t else (GOLD if "회계" in t else WHITE)
    d.rounded_rectangle((x, y, x + 800, y + 112), 20, fill=(70, 48, 38), outline=col, width=4)
    d.text((x + 40, y + 30), t, font=F(46), fill=col)
d.text((110, 960), "논문은 외계인설을 분명히 부정 · 방어·물 모으기·무덤·광산은 증거가 약함", font=F(32, FR), fill=GREY)
save(im, "c06")

mp = os.path.join(HERE, "사진후보", "후보.json")
meta = json.load(open(mp, encoding="utf-8")) if os.path.exists(mp) else {}
for k in ["c05", "c06"]:
    meta[k + "_도표"] = {"title": "도표: " + k, "artist": "설명 도표 (Bongers 외 2025 수치)", "license": "—", "page": "", "source": "설명 도표", "file": k + ".jpg"}
pg = "https://doi.org/10.15184/aqy.2025.10237"
for k, who in [("p2", "J.L. Bongers"), ("p3a", "J.L. Bongers"), ("p3b", "J.L. Bongers"), ("p3c", "J.L. Bongers"), ("p3d", "C. Stanish"),
               ("p5", "Bongers 외"), ("p6", "Bongers 외"), ("p8", "C. Kiahtipes")]:
    meta[k] = {"title": "논문 그림", "artist": f"{who} (Bongers 외, Antiquity 2025)", "license": "CC BY 4.0", "page": pg, "source": "Antiquity", "file": k + ".jpg"}
json.dump(meta, open(mp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("ok")
