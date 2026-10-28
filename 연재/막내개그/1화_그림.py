"""막내 1화 컷 합성 — AI 배경·소품(klein) 위에 Open Peeps 인물(표정)과 효과를 얹어 1920×1080 컷 8장
python 연재/막내개그/1화_그림.py 인물 <소재폴더>          → 컷에 나오는 인물·표정 PNG (투명 배경) 받기
python 연재/막내개그/1화_그림.py 합성 <소재폴더> <컷폴더>  → p1.png … p8.png + 모음.jpg
  소재폴더: bg_사무실.png · bg_순댓국식탁.png · prop_초밥/파스타/고기/순댓국.png (klein, 흰 배경) + peeps/
  효과(박수·반짝이·땀방울·생각 풍선)는 그림 도구로 직접 그림 (굵은 검은 선, Open Peeps 와 같은 느낌)"""
import math
import os
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import importlib  # noqa: E402

EP = importlib.import_module("1화_회식메뉴")
W, H = 1920, 1080
X = {"왼": 430, "가운데": 960, "오른": 1490}
FONT = "/usr/share/fonts/truetype/nanum/NanumSquareRoundB.ttf"
BG = {"사무실": "bg_사무실.png", "순댓국 식탁": "bg_순댓국식탁.png"}


def peeps(src):
    import 오픈핍스_인물 as OP
    d = os.path.join(src, "peeps")
    os.makedirs(d, exist_ok=True)
    todo = []
    for _, _, who, _, _ in EP.PANELS:
        for name, face, _ in who:
            f = os.path.join(d, f"{name}_{face}.svg")
            if not os.path.exists(f[:-4] + ".png"):   # 받는 PNG 는 256px 까지라 흐림 → SVG 를 1024px 로 바꿈
                open(f, "wb").write(OP.get(name, face, 256, "svg", scale=88, translateY=6))   # 머리 위가 잘리지 않게 여백
                todo.append(f)
    if todo:
        subprocess.run(["node", os.path.join(HERE, "svg2png.js")] + todo, check=True, env=dict(os.environ, SIZE="1024"))
        print(len(todo), "장")


def cut_white(im, tol=28):
    """흰 바탕을 가장자리에서부터 지워 투명하게 (소품 그림)"""
    im = im.convert("RGBA")
    w, h = im.size
    mask = Image.new("L", (w, h), 0)
    rgb = im.convert("RGB")
    for xy in [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1), (w // 2, 0), (w // 2, h - 1), (0, h // 2), (w - 1, h // 2)]:
        ImageDraw.floodfill(rgb, xy, (255, 0, 255), thresh=tol)
    px = rgb.load()
    mp = mask.load()
    for y in range(h):
        for x in range(w):
            if px[x, y] != (255, 0, 255):
                mp[x, y] = 255
    mask = mask.filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(1))
    im.putalpha(mask)
    return im.crop(mask.getbbox())


def outlined_text(d, xy, s, size, fill, stroke=8):
    """글자 모양을 넓혀 테두리 (stroke_width 대신, 썸네일 규칙과 같게)"""
    f = ImageFont.truetype(FONT, size)
    l, t, r, b = d.textbbox((0, 0), s, font=f)
    m = Image.new("L", (r + stroke * 2 + 4, b + stroke * 2 + 4), 0)
    ImageDraw.Draw(m).text((stroke + 2, stroke + 2), s, font=f, fill=255)
    big = m.filter(ImageFilter.MaxFilter(stroke * 2 + 1))
    base = d._image
    x, y = xy
    base.paste((20, 20, 20), (x, y), big)
    base.paste(fill, (x, y), m)


def star(d, cx, cy, r, fill=(255, 214, 40)):
    pts = []
    for k in range(8):
        a = math.pi / 4 * k - math.pi / 2
        rr = r if k % 2 == 0 else r * 0.32
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    d.polygon(pts, fill=fill, outline=(20, 20, 20), width=6)


def drop(d, cx, cy, r):
    pts = [(cx, cy - r * 1.9)]
    for k in range(0, 181, 10):
        a = math.radians(k)
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    d.polygon(pts, fill=(120, 200, 255), outline=(20, 20, 20), width=6)
    d.ellipse([cx - r * .45, cy - r * .2, cx - r * .1, cy + r * .3], fill="white")


def bubble(d, box, tail=None):
    """생각 풍선: 흰 타원 + 작은 동그라미 꼬리 (tail = 말하는 사람 머리 쪽 점)"""
    d.ellipse(box, fill="white", outline=(20, 20, 20), width=8)
    if tail:
        x0, y0 = (box[0] + box[2]) / 2, box[3]
        for k, r in enumerate((26, 18, 12)):
            t = (k + 1) / 4
            cx, cy = x0 + (tail[0] - x0) * t, y0 + (tail[1] - y0) * t
            d.ellipse([cx - r, cy - r, cx + r, cy + r], fill="white", outline=(20, 20, 20), width=6)


def put(base, im, cx, cy, h):
    s = h / im.height
    im = im.resize((int(im.width * s), int(h)), Image.LANCZOS)
    base.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))


def panel(src, cid, bg, who, prop, props):
    base = Image.open(os.path.join(src, BG[bg])).convert("RGB").resize((W, H), Image.LANCZOS).convert("RGBA")
    if bg == "사무실":     # 배경을 살짝 흐리고 옅게 → 인물이 앞에 또렷하게
        base = Image.blend(base.filter(ImageFilter.GaussianBlur(2)), Image.new("RGBA", (W, H), (255, 255, 255, 255)), 0.15)
    n = len(who)
    ph = 700 if n >= 3 else 780
    xs = dict(X)
    if bg == "순댓국 식탁":   # 식탁의 순댓국이 가운데 보이게 인물을 양옆으로 작게
        ph, xs = 680, {"왼": 330, "오른": 1580}
    heads = {}
    for name, face, pos in sorted(who, key=lambda w: w[2] == "가운데"):   # 가운데 인물이 맨 앞
        im = Image.open(os.path.join(src, "peeps", f"{name}_{face}.png")).convert("RGBA")
        bb = im.getbbox()
        im = im.crop(bb)
        s = ph / im.height
        im = im.resize((int(im.width * s), ph), Image.LANCZOS)
        x = xs[pos]
        base.alpha_composite(im, (int(x - im.width / 2), H - ph + 40))
        heads[pos] = (x, H - ph + 40)
    d = ImageDraw.Draw(base)
    if "박수" in prop:
        outlined_text(d, (90, 70), "짝짝짝!", 120, (255, 120, 60))
        outlined_text(d, (1440, 110), "짝짝!", 110, (255, 190, 40))
    if "반짝이" in prop:
        for cx, cy, r in [(640, 260, 70), (1290, 210, 90), (1380, 470, 50), (560, 520, 45), (960, 120, 55)]:
            star(d, cx, cy, r)
    if "땀방울" in prop:
        hx, hy = heads["가운데"]
        for cx, cy, r in [(hx + 290, hy + 150, 42), (hx - 300, hy + 230, 32), (hx + 340, hy + 320, 28)]:
            drop(d, cx, cy, r)
    food = {"초밥": "초밥", "파스타": "파스타", "고기": "고기", "순댓국": "순댓국"}
    for k, v in food.items():
        if k in prop and "생각" not in prop:
            if cid == "p7":   # 부장님 머리 위로 크게
                bubble(d, (560, 10, 1360, 360))
                put(base, props[v], 960, 185, 300)
                star(d, 560, 120, 50)
                star(d, 1360, 100, 60)
            else:              # 막내(왼) 생각 풍선
                hx, hy = heads["왼"]
                bubble(d, (700, 40, 1220, 380), tail=(hx + 120, hy + 60))
                put(base, props[v], 960, 210, 270)
    if "생각 풍선" in prop:
        hx, hy = heads["왼"]
        bubble(d, (620, 40, 1180, 360), tail=(hx + 120, hy + 80))
        outlined_text(d, (835, 95), "?", 190, (255, 90, 90), stroke=7)
    return base.convert("RGB")


def main(a):
    if a[0] == "인물":
        peeps(a[1])
        return 0
    src, out = a[1], a[2]
    os.makedirs(out, exist_ok=True)
    props = {k: cut_white(Image.open(os.path.join(src, f"prop_{k}.png"))) for k in ("초밥", "파스타", "고기", "순댓국")}
    sheet = Image.new("RGB", (480 * 4, 270 * 2), "black")
    for k, (cid, bg, who, prop, cap) in enumerate(EP.PANELS):
        im = panel(src, cid, bg, who, prop, props)
        im.save(os.path.join(out, cid + ".png"))
        sheet.paste(im.resize((480, 270)), ((k % 4) * 480, (k // 4) * 270))
        print(cid, cap)
    sheet.save(os.path.join(out, "모음.jpg"), quality=88)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
