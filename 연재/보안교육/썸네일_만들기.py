# 정보보안 교육 영상 썸네일 글씨 얹기 (그림 왼쪽 빈자리에 글씨, 오른쪽에 인물)
# python 연재/보안교육/썸네일_만들기.py <그림> <결과.jpg> "<띠 글>" "<큰 글씨 1줄>" "<큰 글씨 2줄>" <빨갛게 강조할 낱말>
#   글꼴: 나눔스퀘어 ExtraBold (서버에 기본으로 있음)
import sys
from PIL import Image, ImageDraw, ImageEnhance, ImageFont

src, out, badge, l1, l2, hi = sys.argv[1:7]
F = "/usr/share/fonts/truetype/nanum/NanumSquareEB.ttf"
W, H = 1280, 720
NAVY, RED, WHITE = (18, 42, 96), (220, 38, 38), (255, 255, 255)
im = Image.open(src).convert("RGB").resize((W, H), Image.LANCZOS)
im = ImageEnhance.Color(ImageEnhance.Contrast(im).enhance(1.08)).enhance(1.1)
d = ImageDraw.Draw(im)
X = 60


def fit(text, size, max_w):
    while size > 40:
        f = ImageFont.truetype(F, size)
        if d.textlength(text, font=f) <= max_w:
            return f
        size -= 4
    return ImageFont.truetype(F, size)


def line(y, text, f):
    """강조 낱말만 빨갛게, 나머지는 남색. 흰 테두리로 그림 위에서도 잘 보이게"""
    x = X
    parts = text.split(hi) if hi and hi in text else [text]
    for k, p in enumerate(parts):
        for seg, col in ((p, NAVY), (hi if k < len(parts) - 1 else "", RED)):
            if seg:
                d.text((x, y), seg, font=f, fill=col, stroke_width=10, stroke_fill=WHITE)
                x += d.textlength(seg, font=f)


fb = ImageFont.truetype(F, 46)                       # 위쪽 빨간 띠
bw = d.textlength(badge, font=fb)
d.rounded_rectangle((X, 150, X + bw + 48, 150 + 76), radius=38, fill=RED)
d.text((X + 24, 150 + 12), badge, font=fb, fill=WHITE)
max_w = int(W * 0.47) - X
f1 = fit(l1, 130, max_w)
f2 = fit(l2, 150, max_w)
f = f1 if f1.size < f2.size else f2                  # 두 줄 같은 크기로
line(260, l1, f)
line(260 + f.size + 30, l2, f)
im.save(out, quality=93)
print(out)
