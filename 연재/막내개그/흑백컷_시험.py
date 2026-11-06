"""막내 개그 만화 — 흑백 웹툰 한 컷 시험 (1화 p5 '고기는요?')
python -X utf8 연재/막내개그/흑백컷_시험.py <인물 PNG 폴더> <결과.png>
  - 인물: Open Peeps(CC0) 그림을 흑백으로 (색 → 흰색, 선·머리 → 검정, 머리카락만 망점 회색)
  - 배경: 코드로 그린 사무실 선화(책상·모니터·창문) + 망점(스크린톤), 말풍선 2개, 효과선"""
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

SRC, OUT = sys.argv[1], sys.argv[2]
W, H = 1920, 1080
FONT = "/usr/share/fonts/truetype/nanum/NanumSquare_acEB.ttf"
INK = 15


def bw_peep(path, size):
    """색 칠한 인물 → 흑백: 어두운 곳(선·머리)은 검정, 나머지는 흰색"""
    im = Image.open(path).convert("RGBA").resize((size, size), Image.LANCZOS)
    a = np.asarray(im).astype(np.float32)
    lum = a[..., :3] @ np.array([0.299, 0.587, 0.114])
    rgb = np.where(lum[..., None] < 90, INK, 255).astype(np.uint8).repeat(3, -1)
    out = np.dstack([rgb, a[..., 3].astype(np.uint8)])
    return Image.fromarray(out, "RGBA")


def tone(size, step=9, r=1.6):
    """망점(스크린톤) 무늬 한 장"""
    t = Image.new("L", size, 255)
    d = ImageDraw.Draw(t)
    for y in range(0, size[1], step):
        for x in range((y // step % 2) * step // 2, size[0], step):
            d.ellipse((x - r, y - r, x + r, y + r), fill=INK)
    return t


def bubble(d, box, text, tail, font):
    x0, y0, x1, y1 = box
    d.ellipse(box, fill=255, outline=INK, width=6)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    tx, ty = tail
    ang = math.atan2(ty - cy, tx - cx)
    bx, by = cx + (x1 - x0) / 2 * 0.85 * math.cos(ang), cy + (y1 - y0) / 2 * 0.85 * math.sin(ang)
    p = [(bx + 26 * math.cos(ang + 1.57), by + 26 * math.sin(ang + 1.57)), (tx, ty), (bx + 26 * math.cos(ang - 1.57), by + 26 * math.sin(ang - 1.57))]
    d.polygon(p, fill=255)
    d.line([p[0], p[1], p[2]], fill=INK, width=6)
    lines = text.split("\n")
    lh = font.size * 1.25
    for i, ln in enumerate(lines):
        d.text((cx, cy + (i - (len(lines) - 1) / 2) * lh), ln, font=font, fill=INK, anchor="mm")


canvas = Image.new("L", (W, H), 255)
d = ImageDraw.Draw(canvas)
# 사무실 배경 선화: 창문(망점 하늘)·벽 선·책상·모니터
win = (1180, 90, 1820, 470)
canvas.paste(tone((win[2] - win[0], win[3] - win[1]), 11, 1.4), win[:2])
d.rectangle(win, outline=INK, width=6)
d.line([((win[0] + win[2]) // 2, win[1]), ((win[0] + win[2]) // 2, win[3])], fill=INK, width=5)
d.line([(win[0], (win[1] + win[3]) // 2), (win[2], (win[1] + win[3]) // 2)], fill=INK, width=5)
d.line([(0, 640), (W, 640)], fill=INK, width=4)                       # 벽과 바닥 경계
d.rectangle((120, 700, 1800, 760), fill=255, outline=INK, width=6)    # 책상 윗면
d.line([(160, 760), (160, 1080)], fill=INK, width=6)
d.line([(1760, 760), (1760, 1080)], fill=INK, width=6)
for mx in (330, 1450):                                                # 모니터 두 대
    d.rectangle((mx - 150, 470, mx + 150, 660), fill=255, outline=INK, width=6)
    d.rectangle((mx - 128, 492, mx + 128, 638), outline=INK, width=3)
    d.rectangle((mx - 20, 660, mx + 20, 700), fill=INK)
# 인물: 왼쪽 막내(당황), 오른쪽 이대리(얄밉게)
for name, face, x, flip in (("막내", "hectic", 230, False), ("이대리", "contempt", 1150, True)):
    p = bw_peep(os.path.join(SRC, f"{name}_{face}.png"), 640)
    if flip:
        p = p.transpose(Image.FLIP_LEFT_RIGHT)
    canvas.paste(p.convert("L"), (x, 1080 - 640 + 30), p.split()[3])
# 막내 쪽 당황 효과: 땀방울·떨림 선
for (sx, sy) in ((740, 330), (770, 410)):
    d.ellipse((sx - 14, sy - 22, sx + 14, sy + 22), fill=255, outline=INK, width=5)
for k in range(5):
    d.line([(170 - k * 10, 520 + k * 40), (120 - k * 10, 540 + k * 40)], fill=INK, width=5)
# 이대리 쪽 집중선 몇 개
for a in range(-40, 41, 16):
    r = math.radians(a + 90)
    d.line([(1470 + 620 * math.cos(r), 40 + 0 * math.sin(r)), (1470 + 520 * math.cos(r), 120)], fill=INK, width=3)
f1, f2 = ImageFont.truetype(FONT, 54), ImageFont.truetype(FONT, 50)
bubble(d, (90, 60, 760, 330), "그, 그럼…\n고기는요?", (420, 430), f1)
bubble(d, (900, 140, 1560, 400), "부장님 어제\n고기 드셨어.", (1380, 500), f2)
# 컷 테두리
d.rectangle((0, 0, W - 1, H - 1), outline=INK, width=14)
canvas = canvas.filter(ImageFilter.SMOOTH)
canvas.convert("RGB").save(OUT, quality=95)
print("OK", OUT)
