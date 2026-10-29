"""번호 붙인 컷 모음표 — 사용자가 전체 그림을 한 번에 보고 고칠 컷 번호를 직접 지시하도록 (영상 합치기 전에 보냄)
python 컷_모음표.py <컷폴더> <저장폴더> [한 장에 몇 컷=24]
  - 컷폴더의 c001.png … 를 번호 순서대로 4줄×6칸(기본)에 크게 놓고, 칸마다 왼쪽 위에 큰 번호(c001)를 적음
  - 결과: <저장폴더>/모음_01.jpg, 모음_02.jpg … (한 장 1920×1080, 폰에서 확대해 보기 좋게)"""
import glob
import os
import sys

from PIL import Image, ImageDraw, ImageFont

FONT = "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf"


def main(a):
    if len(a) < 2:
        print(__doc__)
        return 2
    src, out = a[0], a[1]
    per = int(a[2]) if len(a) > 2 else 24
    cols = 6 if per > 12 else 4
    rows = (per + cols - 1) // cols
    W, H = 1920, 1080
    cw, ch = W // cols, H // rows
    fs = sorted(f for f in glob.glob(os.path.join(src, "c*.png")) if os.path.basename(f)[1:4].isdigit())
    os.makedirs(out, exist_ok=True)
    font = ImageFont.truetype(FONT, max(22, ch // 7))
    for p in range(0, len(fs), per):
        sheet = Image.new("RGB", (W, H), "black")
        d = ImageDraw.Draw(sheet)
        for k, f in enumerate(fs[p:p + per]):
            im = Image.open(f).convert("RGB")
            im.thumbnail((cw - 4, ch - 4))
            x, y = (k % cols) * cw + 2, (k // cols) * ch + 2
            sheet.paste(im, (x, y))
            label = os.path.splitext(os.path.basename(f))[0]
            l, t, r, b = d.textbbox((0, 0), label, font=font)
            d.rectangle([x, y, x + r + 12, y + b + 8], fill=(200, 30, 30))
            d.text((x + 6, y + 2), label, font=font, fill="white")
        name = os.path.join(out, f"모음_{p // per + 1:02d}.jpg")
        sheet.save(name, quality=90)
        print(name)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
