"""교육 영상용 슬라이드(그림판) 만들기 — 왼쪽에 제목·시대 연표·핵심어 카드, 오른쪽은 아나운서 자리 (사용자 2026-11-25 '교육자료에 등장해서 나레이션')
   슬라이드 내용은 JSON: {"제목": "...", "연표": ["구석기","신석기","청동기"], "장면": [{"연표": 0, "소제목": "...", "카드": ["...","..."], "주석": "..."} ...]}
   사용: python 실사3D/교육슬라이드.py <내용.json> <결과 폴더> [--크기 1280x720]"""
import json, os, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter
a = sys.argv[1:]; spec = json.load(open(a[0], encoding="utf-8")); out = a[1]
W, H = (int(v) for v in (a[a.index("--크기") + 1] if "--크기" in a else "1280x720").split("x"))
os.makedirs(out, exist_ok=True)
FB = "/usr/share/fonts/truetype/nanum/NanumBarunGothicBold.ttf"; FR = "/usr/share/fonts/truetype/nanum/NanumBarunGothic.ttf"
if not os.path.exists(FB): FB = FR = "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"
F = lambda p, s: ImageFont.truetype(p, int(s * H / 720))
S = lambda v: int(v * H / 720)
BG1, BG2 = (243, 236, 222), (226, 214, 190)          # 흙·종이 느낌 (원시 시대)
ACC = (176, 96, 52); INK = (52, 40, 30); SUB = (120, 100, 80)


def base():
    im = Image.new("RGB", (W, H)); d = ImageDraw.Draw(im)
    for y in range(H):
        t = y / H; d.line([(0, y), (W, y)], fill=tuple(int(BG1[k] * (1 - t) + BG2[k] * t) for k in range(3)))
    return im


for k, sc in enumerate(spec["장면"]):
    im = base(); d = ImageDraw.Draw(im)
    L = S(56); R = int(W * 0.60)                                  # 왼쪽 60% 가 내용, 오른쪽은 아나운서
    d.text((L, S(40)), spec["제목"], font=F(FB, 22), fill=SUB)
    d.text((L, S(74)), sc["소제목"], font=F(FB, 46), fill=INK)
    d.rectangle([L, S(140), L + S(70), S(146)], fill=ACC)
    # 연표
    eras = spec["연표"]; y0 = S(200); x0, x1 = L, R - S(20); n = len(eras)
    d.line([(x0, y0), (x1, y0)], fill=(170, 150, 125), width=S(6))
    for i, e in enumerate(eras):
        cx = x0 + (x1 - x0) * (i + 0.5) / n; on = sc.get("연표") == i
        r = S(16) if on else S(10)
        d.ellipse([cx - r, y0 - r, cx + r, y0 + r], fill=ACC if on else (190, 172, 148), outline=(255, 255, 255), width=S(3))
        f = F(FB if on else FR, 26 if on else 22); tw = d.textlength(e, font=f)
        d.text((cx - tw / 2, y0 + S(24)), e, font=f, fill=INK if on else SUB)
        if sc.get("연표때") and on:
            f2 = F(FR, 18); t2 = sc["연표때"]; d.text((cx - d.textlength(t2, font=f2) / 2, y0 - S(48)), t2, font=f2, fill=ACC)
    # 카드
    cards = sc.get("카드", []); cy = S(300)
    for c in cards:
        sh = Image.new("RGBA", (W, H), (0, 0, 0, 0)); sd = ImageDraw.Draw(sh)
        sd.rounded_rectangle([L + S(4), cy + S(6), R - S(16), cy + S(84)], radius=S(14), fill=(0, 0, 0, 40))
        im.paste(sh.filter(ImageFilter.GaussianBlur(S(6))), (0, 0), sh.filter(ImageFilter.GaussianBlur(S(6))))
        d = ImageDraw.Draw(im)
        d.rounded_rectangle([L, cy, R - S(20), cy + S(78)], radius=S(14), fill=(255, 252, 246))
        d.rounded_rectangle([L, cy, L + S(10), cy + S(78)], radius=S(4), fill=ACC)
        d.text((L + S(30), cy + S(20)), c, font=F(FB, 30), fill=INK)
        cy += S(98)
    if sc.get("주석"): d.text((L, H - S(60)), sc["주석"], font=F(FR, 18), fill=SUB)
    im.save(os.path.join(out, f"slide_{k:02d}.png"))
print("슬라이드", len(spec["장면"]), "장 →", out)
