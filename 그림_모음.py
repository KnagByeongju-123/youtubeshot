"""그림 점검용 모음 — 프로젝트 대본의 그림을 나오는 순서대로 번호를 붙여 40장씩 한 장의 모음 그림으로 (사용자 결정 2026-10-31: 40장씩 점검)

  python -X utf8 그림_모음.py <프로젝트.json> [--장수 40] [--열 2]
  → 프로젝트 폴더에 _그림점검_1.jpg, _그림점검_2.jpg … (번호 = 영상에 나오는 순서, 옆에 나오는 시각 대신 그림 설명)
  폰에서 위아래로 넘겨 보기 좋게 2열, 한 칸 640×360
"""
import json
import os
import re
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
MEDIA_RE = re.compile(r"^\[(?:사진|그림|이미지)\s*[:：]\s*([^|\]]+)(?:\|\s*([^|\]]*))?")


def font(size):
    for p in ("/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf", "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
              "C:/Windows/Fonts/malgunbd.ttf"):
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def main(a):
    if not a:
        print(__doc__)
        return 2
    proj = os.path.abspath(a[0])
    per = int(a[a.index("--장수") + 1]) if "--장수" in a else 40
    cols = int(a[a.index("--열") + 1]) if "--열" in a else 2
    story = json.load(open(proj, encoding="utf-8")).get("story", "")
    pics = []
    for line in story.split("\n"):
        mm = MEDIA_RE.match(line.strip())
        if mm:
            p = mm.group(1).strip()
            pics.append((p if os.path.isabs(p) else os.path.join(HERE, p), (mm.group(2) or "").replace("AI 상상도 · ", "").strip()))
    cw, ch, cap = 640, 360, 34
    f_num, f_cap = font(30), font(22)
    out = []
    for g in range(0, len(pics), per):
        part = pics[g:g + per]
        rows = -(-len(part) // cols)
        sheet = Image.new("RGB", (cw * cols, (ch + cap) * rows), "white")
        d = ImageDraw.Draw(sheet)
        for i, (p, c) in enumerate(part):
            x, y = (i % cols) * cw, (i // cols) * (ch + cap)
            try:
                im = Image.open(p).convert("RGB").resize((cw - 6, ch - 6))
            except Exception:
                im = Image.new("RGB", (cw - 6, ch - 6), "grey")
            sheet.paste(im, (x + 3, y + 3))
            n = str(g + i + 1)
            d.rectangle([x + 3, y + 3, x + 18 + 18 * len(n), y + 42], fill="red")
            d.text((x + 10, y + 6), n, fill="white", font=f_num)
            d.text((x + 6, y + ch + 2), c[:28], fill="black", font=f_cap)
        dst = os.path.join(os.path.dirname(proj), f"_그림점검_{g // per + 1}.jpg")
        sheet.save(dst, quality=85)
        out.append(dst)
    print(f"그림 {len(pics)}장 → 모음 {len(out)}장")
    for p in out:
        print(p)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
