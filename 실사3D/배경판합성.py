"""투명 배경으로 찍은 인물 장면(png, --투명)을 사진 한 장(배경판) 위에 얹기 — 카메라가 고정된 장면용 (사용자 2026-11-25: 직접 찍은 에펠탑 사진을 배경으로)
   배경판은 장면 크기에 꽉 차게 잘라 맞추고(--중심 x,y 로 자를 자리), 살짝 흐리게(--흐림, 배경이 멀어 보이게), 인물 그림자도 함께 얹힘(shadow catcher 알파)
   사용: python 실사3D/배경판합성.py <장면 폴더> <배경 사진> <결과 폴더> [--중심 0.5,0.5] [--흐림 1.5] [--색 1.0,1.0,1.0]"""
import glob, os, sys
from PIL import Image, ImageFilter, ImageOps
a = sys.argv[1:]; src, plate, dst = a[:3]
cx, cy = (float(v) for v in (a[a.index("--중심") + 1] if "--중심" in a else "0.5,0.5").split(","))
blur = float(a[a.index("--흐림") + 1]) if "--흐림" in a else 1.5
fs = sorted(glob.glob(os.path.join(src, "*.png"))); os.makedirs(dst, exist_ok=True)
W, H = Image.open(fs[0]).size
im = ImageOps.exif_transpose(Image.open(plate)).convert("RGB"); pw, ph = im.size; s = max(W / pw, H / ph)   # 휴대폰 사진은 돌림 정보(EXIF)대로 바로 세움
im = im.resize((int(pw * s + 0.5), int(ph * s + 0.5)), Image.LANCZOS); pw, ph = im.size
x0 = int(min(max(cx * pw - W / 2, 0), pw - W)); y0 = int(min(max(cy * ph - H / 2, 0), ph - H))
bg = im.crop((x0, y0, x0 + W, y0 + H))
if blur > 0: bg = bg.filter(ImageFilter.GaussianBlur(blur))
bg = bg.convert("RGBA")
for f in fs:
    o = bg.copy(); o.alpha_composite(Image.open(f).convert("RGBA")); o.convert("RGB").save(os.path.join(dst, os.path.basename(f)))
print("합성:", len(fs), "장 →", dst)
