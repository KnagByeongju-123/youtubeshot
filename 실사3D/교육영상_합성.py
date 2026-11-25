"""교육 영상 합성: 슬라이드(문장마다) + 투명 배경 아나운서 장면 + 한 줄 자막 → 장면 png (그다음 ffmpeg 로 나레이션과 묶음)
   문장 시각은 '시각표.json' = [[시작초, 끝초, "문장"], ...] (영상 기준, 나레이션 시작 지연 포함). 문장 k 가 시작하면 슬라이드 k.
   자막은 문장을 쉼표에서 나눠 글자 수 비율로 시간을 나눔 (한 줄씩, 사용자 결정)
   사용: python 실사3D/교육영상_합성.py <슬라이드 폴더> <아나운서 장면 폴더> <시각표.json> <결과 폴더> [--자리 0.6]"""
import glob, json, os, sys
from PIL import Image, ImageDraw, ImageFont
a = sys.argv[1:]; sdir, pdir, tfile, out = a[:4]
os.makedirs(out, exist_ok=True)
slides = [Image.open(f).convert("RGBA") for f in sorted(glob.glob(os.path.join(sdir, "slide_*.png")))]
W, H = slides[0].size
tl = json.load(open(tfile, encoding="utf-8"))
subs = []
for s0, s1, txt in tl:
    parts = [p.strip() for p in txt.replace(".", ".|").replace(",", ",|").split("|") if p.strip()]
    tot = sum(len(p) for p in parts); t = s0
    for p in parts:
        d = (s1 - s0) * len(p) / tot; subs.append((t, t + d, p.rstrip(","))); t += d
font = ImageFont.truetype("/usr/share/fonts/truetype/nanum/NanumBarunGothicBold.ttf", int(30 * H / 720))
fs = sorted(glob.glob(os.path.join(pdir, "*.png")))
for i, f in enumerate(fs):
    t = i / 24.0
    k = max([j for j, (s0, _, _) in enumerate(tl) if s0 <= t] or [0]); k = min(k, len(slides) - 1)
    im = slides[k].copy()
    p = Image.open(f).convert("RGBA"); pw, ph = p.size
    al = p.getchannel("A").point(lambda v: 0 if v < 12 else v); p.putalpha(al)      # 바닥(그림자 받는 판)의 아주 옅은 알파가 사각형 자국으로 보였음
    im.alpha_composite(p, (W - pw - int(W * 0.03), H - ph))
    sub = next((x for x in subs if x[0] <= t < x[1]), None)
    if sub:
        d = ImageDraw.Draw(im); tw = d.textlength(sub[2], font=font); y = H - int(78 * H / 720)
        box = Image.new("RGBA", im.size, (0, 0, 0, 0)); bd = ImageDraw.Draw(box)
        bd.rounded_rectangle([(W - tw) / 2 - 22, y - 12, (W + tw) / 2 + 22, y + font.size + 14], radius=10, fill=(20, 16, 12, 170))
        im.alpha_composite(box); ImageDraw.Draw(im).text(((W - tw) / 2, y), sub[2], font=font, fill=(255, 255, 255))
    im.convert("RGB").save(os.path.join(out, os.path.basename(f)))
print("합성:", len(fs), "장 →", out)
