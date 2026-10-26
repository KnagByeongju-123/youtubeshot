"""조세르 물 승강기 설명 도표 + 논문 그림 16:9 맞추기 → 사진/<컷>.jpg  (python 도표_만들기.py)
도표 내용은 Landreau 외, PLOS ONE 2024 (e0306690) 의 가설 그대로: 사방댐(기스르 엘 무디르) → 깊은 도랑(침전·저류·정수) → 수직 통로 → 물에 뜬 받침
논문 그림(CC BY 4.0)은 잘리지 않게 어두운 바탕 가운데에 놓음 (영상은 화면을 꽉 채우므로 넓은 그림은 잘림)"""
import json, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter
HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 1920, 1080
FB = "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf"
FR = "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"
GOLD, WHITE, GREY, BLUE, SAND, STONE = (255, 214, 140), (240, 240, 240), (170, 165, 155), (110, 180, 245), (196, 160, 105), (215, 200, 170)


def F(size, f=FB):
    return ImageFont.truetype(f, size)


def base():
    im = Image.new("RGB", (W, H), (28, 22, 18))
    return im, ImageDraw.Draw(im)


def save(im, name):
    os.makedirs(os.path.join(HERE, "사진"), exist_ok=True)
    im.save(os.path.join(HERE, "사진", name + ".jpg"), quality=92)


# c16 물의 길 (정리)
im, d = base()
d.text((120, 90), "물의 길 (연구팀 가설)", font=F(64), fill=GOLD)
steps = [("① 사방댐", "기스르 엘 무디르", "홍수와 흙을 가둠"), ("② 정수 시설", "깊은 도랑의 칸들", "가라앉히고·모으고·거름"),
         ("③ 수직 통로", "피라미드 아래 약 28m", "맑은 물이 차오름"), ("④ 물 승강기", "물에 뜬 받침", "돌을 위로 올림")]
x = 110
for i, (a, b, c) in enumerate(steps):
    d.rounded_rectangle((x, 330, x + 380, 640), 26, outline=BLUE, width=5, fill=(34, 44, 60))
    d.text((x + 30, 360), a, font=F(52), fill=WHITE)
    d.text((x + 30, 460), b, font=F(36, FR), fill=GOLD)
    d.text((x + 30, 540), c, font=F(32, FR), fill=GREY)
    if i < 3:
        d.text((x + 392, 450), "→", font=F(64), fill=BLUE)
    x += 450
d.text((120, 760), "흙탕물 → 맑은 물 → 부력", font=F(56), fill=BLUE)
d.text((120, 880), "Landreau 외, PLOS ONE (2024) — 아직 증명되지 않은 가설", font=F(34, FR), fill=GREY)
save(im, "c16")

# c14 물로 돌을 들어 올리는 원리
im, d = base()
d.text((120, 90), "물로 돌을 들어 올리는 원리", font=F(64), fill=GOLD)
for k, (lvl, lab) in enumerate([(820, "① 돌을 받침에 올림"), (560, "② 물을 채우면 받침이 떠오름"), (300, "③ 위에서 돌을 옮겨 쌓음")]):
    x0 = 160 + k * 560
    d.rectangle((x0, 260, x0 + 300, 900), outline=SAND, width=8)                       # 통로 벽
    d.rectangle((x0 + 8, lvl, x0 + 292, 892), fill=(60, 120, 190))                        # 물
    d.rectangle((x0 + 30, lvl - 40, x0 + 270, lvl), fill=(150, 110, 70))                  # 받침
    d.rectangle((x0 + 90, lvl - 130, x0 + 210, lvl - 40), fill=STONE, outline=(120, 110, 90), width=3)   # 돌
    d.text((x0 - 10, 940), lab, font=F(36), fill=WHITE)
d.text((1300, 120), "물을 빼고 다시 채우기를 되풀이", font=F(34, FR), fill=GREY)
save(im, "c14")

# 논문 그림 → 16:9 어두운 바탕 가운데 (CC BY 4.0)
FIG = {"c06": ("plos_g011.png", None), "c07": ("plos_g004.png", (0, 0, 0.5, 1)), "c08": ("plos_g003.png", None), "c09": ("plos_g008.png", None),
       "c11": ("plos_g001.png", None), "c12": ("plos_g004.png", (0.5, 0, 1, 1)), "c13": ("plos_g010.png", None),
       "c15": ("plos_g013.png", None), "c27": ("plos_g009.png", None), "c23": ("ahr_1.png", None)}
for cid, (fn, box) in FIG.items():
    src = Image.open(os.path.join(HERE, "사진후보", fn)).convert("RGB")
    if box:
        w, h = src.size
        src = src.crop((int(box[0] * w), int(box[1] * h), int(box[2] * w), int(box[3] * h)))
    bg = src.resize((W, H)).filter(ImageFilter.GaussianBlur(40)).point(lambda v: v * 0.35)
    s = src.copy()
    s.thumbnail((W - 120, H - 80), Image.LANCZOS)
    if s.width < W - 120 and s.height < H - 80:                                         # 작은 그림은 키움
        r = min((W - 120) / s.width, (H - 80) / s.height)
        s = src.resize((int(s.width * r), int(s.height * r)), Image.LANCZOS)
    bg.paste(s, ((W - s.width) // 2, (H - s.height) // 2))
    save(bg, cid)

meta_p = os.path.join(HERE, "사진후보", "후보.json")
meta = json.load(open(meta_p, encoding="utf-8")) if os.path.exists(meta_p) else {}
for k in ["c16", "c14"]:
    meta[k + "_도표"] = {"title": "도표: " + k, "artist": "설명 도표 (Landreau 외 2024 가설)", "license": "—", "page": "", "source": "설명 도표", "file": k + ".jpg"}
for k in FIG:
    ahr = FIG[k][0].startswith("ahr")
    meta[k + "_논문"] = {"title": "논문 그림: " + k, "artist": "Ghoneim 외 2024" if ahr else "Landreau 외 2024",
                         "license": "CC BY 4.0", "page": "https://doi.org/10.1038/s43247-024-01379-7" if ahr else "https://doi.org/10.1371/journal.pone.0306690",
                         "source": "Communications Earth & Environment" if ahr else "PLOS ONE", "file": k + ".jpg"}
json.dump(meta, open(meta_p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("ok")
