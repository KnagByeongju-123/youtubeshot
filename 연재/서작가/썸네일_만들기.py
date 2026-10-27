# 《엄마의 텃밭》 썸네일 글씨 얹기 (두번째새벽/썸네일_만들기.py 를 에세이에 맞게: 따뜻한 강조색·부드러운 띠·글씨 왼쪽 자리)
# python 연재/서작가/썸네일_만들기.py <그림> <결과.jpg> <큰 글씨 1줄> <큰 글씨 2줄|""> <강조할 낱말> <left|top|bottom> [회차 띠 글] [sans|serif]
#   left = 왼쪽 가운데(그림 오른쪽에 인물), top/bottom = 위·아래. sans = 검은고딕(BlackHanSans), serif = 나눔명조 ExtraBold(잔잔한 느낌)
#   글꼴이 없으면: fonts/BlackHanSans-Regular.ttf ← https://raw.githubusercontent.com/google/fonts/main/ofl/blackhansans/BlackHanSans-Regular.ttf
import os
import sys
from PIL import Image, ImageDraw, ImageEnhance, ImageFont


def outlined(im, xy, text, font, fill, edge, width, shadow=None):
    """글씨 + 테두리(+그림자). 테두리는 글자 모양을 넓혀서 그림 — PIL stroke_width 는 이 글꼴에서 'ㄱ' 윗변 테두리가 빠지는 일이 있음"""
    from PIL import ImageFilter
    w, h = int(font.getlength(text)) + 4 * width + 40, int(font.size * 1.6) + 4 * width
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).text((2 * width, 2 * width), text, font=font, fill=255)
    ring = m.filter(ImageFilter.MaxFilter(2 * width + 1))
    x, y = int(round(xy[0])) - 2 * width, int(round(xy[1])) - 2 * width
    if shadow:
        sw, (dx, dy) = shadow
        im.paste((0, 0, 0), (x + dx, y + dy), m.filter(ImageFilter.MaxFilter(2 * sw + 1)))
    im.paste(edge, (x, y), ring)
    im.paste(fill, (x, y), m)

src, out, l1, l2, hi, pos = sys.argv[1:7]
badge = sys.argv[7] if len(sys.argv) > 7 else "엄마의 텃밭 1화"
kind = sys.argv[8] if len(sys.argv) > 8 else "sans"
HERE = os.path.dirname(os.path.abspath(__file__))
F = (os.path.join(HERE, "..", "..", "fonts", "BlackHanSans-Regular.ttf") if kind == "sans"
     else "/usr/share/fonts/truetype/nanum/NanumMyeongjoExtraBold.ttf")
W, H = 1280, 720
HI, BADGE = (255, 196, 90), (176, 92, 52)          # 불빛 같은 주황 강조, 흙빛 띠
im = Image.open(src).convert("RGB").resize((W, H), Image.LANCZOS)
im = ImageEnhance.Contrast(im).enhance(1.1)
im = ImageEnhance.Color(im).enhance(1.12)
grad = Image.new("L", (W, H))                        # 글씨 쪽을 어둡게 (글씨가 잘 보이게)
gp = grad.load()
for y in range(H):
    for x in range(0, W, 4):
        t = (1 - x / W) if pos == "left" else (y / H) if pos == "bottom" else (1 - y / H)
        v = int(max(0, (t - 0.42) / 0.58) * 190)
        for dx in range(4):
            if x + dx < W:
                gp[x + dx, y] = v
im = Image.composite(Image.new("RGB", (W, H), (20, 10, 5)), im, grad)
d = ImageDraw.Draw(im)
lines = [x for x in (l1, l2) if x]
size = 132 if max(len(x) for x in lines) <= 7 else 112 if max(len(x) for x in lines) <= 9 else 96
f = ImageFont.truetype(F, size)
lh = int(size * 1.18)
if pos == "left":
    y0 = (H - lh * len(lines)) // 2 - 20
elif pos == "bottom":
    y0 = H - 50 - lh * len(lines)
else:
    y0 = 70
for k, ln in enumerate(lines):
    y, x = y0 + k * lh, 56
    for word in ln.split(" "):
        col = HI if hi and hi in word else (255, 255, 255)
        w = d.textlength(word, font=f)
        outlined(im, (x, y), word, f, col, (25, 12, 6), 6, shadow=(11, (5, 7)))    # 테두리 + 그림자
        x += w + size * 0.26
fb = ImageFont.truetype(os.path.join(HERE, "..", "..", "fonts", "BlackHanSans-Regular.ttf"), 44)   # 회차 띠
bw = d.textlength(badge, font=fb) + 48
by = 34 if pos in ("bottom", "left") else H - 98
d.rounded_rectangle([34, by, 34 + bw, by + 62], radius=14, fill=BADGE)
d.text((58, by + 7), badge, font=fb, fill=(255, 245, 230))
im.save(out, "JPEG", quality=92)
print(out)
