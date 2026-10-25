# 썸네일 글씨 얹기: python make_thumb.py <그림> <결과.jpg> <큰 글씨 1줄> <큰 글씨 2줄|""> <강조할 낱말> <위치 top|bottom> [회차 띠 글] [글씨 크기]
# (글씨 크기: 얼굴이 크게 나온 그림에서 글씨가 얼굴을 가리면 줄임. 안 쓰면 글자 수로 150/120)
import sys
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter

src, out, l1, l2, hi, pos = sys.argv[1:7]
badge = sys.argv[7] if len(sys.argv) > 7 else "두 번째 새벽 1화"
F = "/home/user/youtubeshot/fonts/BlackHanSans-Regular.ttf"
W, H = 1280, 720
im = Image.open(src).convert("RGB").resize((W, H), Image.LANCZOS)
im = ImageEnhance.Contrast(im).enhance(1.12)
im = ImageEnhance.Color(im).enhance(1.15)
# 글씨 쪽을 어둡게 (글씨가 잘 보이게)
grad = Image.new("L", (1, H))
for y in range(H):
    t = (y / H) if pos == "bottom" else (1 - y / H)
    grad.putpixel((0, y), int(max(0, (t - 0.45) / 0.55) * 200))
im = Image.composite(Image.new("RGB", (W, H), (0, 0, 0)), im, grad.resize((W, H)))
d = ImageDraw.Draw(im)
lines = [x for x in (l1, l2) if x]
size = int(sys.argv[8]) if len(sys.argv) > 8 else (150 if max(len(x) for x in lines) <= 7 else 120)
f = ImageFont.truetype(F, size)
lh = int(size * 1.12)
y0 = (H - 30 - lh * len(lines)) if pos == "bottom" else 95
for k, ln in enumerate(lines):
    y = y0 + k * lh
    x = 50
    for word in ln.split(" "):
        col = (90, 220, 255) if hi and hi in word else (255, 255, 255)
        w = d.textlength(word, font=f)
        for r in (14, 9):    # 두꺼운 검은 테두리 + 그림자
            d.text((x + 6, y + 8), word, font=f, fill=(0, 0, 0), stroke_width=r, stroke_fill=(0, 0, 0))
        d.text((x, y), word, font=f, fill=col, stroke_width=6, stroke_fill=(0, 0, 0))
        x += w + size * 0.28
# 회차 띠
fb = ImageFont.truetype(F, 46)
bw = d.textlength(badge, font=fb) + 50
by = 30 if pos == "bottom" else H - 95
d.polygon([(30, by), (30 + bw + 20, by), (30 + bw, by + 64), (30, by + 64)], fill=(200, 40, 30))
d.text((52, by + 7), badge, font=fb, fill=(255, 255, 255))
im.save(out, "JPEG", quality=92)
print(out)
