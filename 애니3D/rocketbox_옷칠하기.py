"""Rocketbox 인물 그림 다시 칠하기 — 평상복을 아나운서 차림으로 (사용자 2026-11-26 Female_Adult_12 를 아나운서로, 1번 '옷만 정장처럼 칠하기')
   몸 그림: 피부(손·다리·목)는 그대로, 옷은 모두 짙은 남색(원래 주름·결은 밝기로 살림, 초록·보라 무늬·체크도 남색), 신발 칸은 검정
   머리 그림: 파란 눈동자 → 갈색, --지우기 칸의 어두운 무늬(목 옆 별 문신 등)는 주변 피부로 메움(cv2.inpaint)
   사용: .supertonic_venv/bin/python 애니3D/rocketbox_옷칠하기.py <Textures 폴더> <출력 폴더> [--색 22,30,58]
         [--신발 x0,y0,x1,y1;…] [--눈 x0,y0,x1,y1] [--지우기 x0,y0,x1,y1;…]   (칸은 그림 비율 0~1, 위가 0)"""
import os, shutil, sys
import numpy as np
import cv2
from PIL import Image
def rd(p): a_ = np.asarray(Image.open(p).convert('RGB')); return np.ascontiguousarray(a_[..., ::-1])          # TGA 는 cv2 가 못 읽음 → PIL, BGR 로
def wr(p, b): Image.fromarray(np.ascontiguousarray(b[..., :3][..., ::-1])).save(p)

a = sys.argv[1:]; src, dst = a[0], a[1]; os.makedirs(dst, exist_ok=True)
def opt(k, d): return a[a.index(k) + 1] if k in a else d
def boxes(s): return [tuple(float(v) for v in b.split(",")) for b in s.split(";") if b]
NAVY = np.array([float(v) for v in opt("--색", "13,17,32").split(",")])[::-1]            # cv2 는 BGR
SHOES = boxes(opt("--신발", "0.15,0.0,0.33,0.30;0.66,0.0,0.84,0.30"))
EYE = boxes(opt("--눈", "0.20,0.85,0.31,0.995"))
ERASE = boxes(opt("--지우기", "0.165,0.36,0.235,0.46;0.765,0.36,0.835,0.46"))
for f in os.listdir(src):
    if not os.path.exists(os.path.join(dst, f)): shutil.copy(os.path.join(src, f), os.path.join(dst, f))
def px(b, W, H): return int(b[0] * W), int(b[1] * H), int(b[2] * W), int(b[3] * H)
body = next(f for f in os.listdir(src) if f.endswith("_body_color.tga"))
im = rd(os.path.join(src, body)).copy(); H, W = im.shape[:2]; bgr = im[..., :3].astype(np.float32)
hsv = cv2.cvtColor(im[..., :3], cv2.COLOR_BGR2HSV).astype(np.float32); hh, ss, vv = hsv[..., 0] * 2, hsv[..., 1] / 255, hsv[..., 2] / 255
skin = (hh >= 5) & (hh <= 32) & (ss > 0.18) & (ss < 0.75) & (vv > 0.32)
skin = cv2.morphologyEx(skin.astype(np.uint8), cv2.MORPH_OPEN, np.ones((5, 5), np.uint8)).astype(bool)
empty = bgr.sum(2) < 6                                           # 쓰지 않는 검은 바탕
cloth = ~skin & ~empty
lum = bgr.mean(2) / 255
loud = (ss > 0.35) & ~skin                                        # 초록·보라·체크 같은 진한 무늬
base = float(np.median(lum[cloth & ~loud])) if (cloth & ~loud).any() else 0.12
l = np.where(loud, base, np.clip(lum, 0, base * 2.5))
l = cv2.GaussianBlur(l.astype(np.float32), (0, 0), 0.8)
fac = (0.55 + 0.9 * l / max(base, 1e-3) * 0.5)[..., None]
navy = np.clip(NAVY * fac, 0, 255)
shoe = np.zeros_like(cloth)
for b in SHOES:
    x0, y0, x1, y1 = px(b, W, H); shoe[y0:y1, x0:x1] = True
black = np.clip(np.array([18, 18, 20.0]) * fac * 1.1, 0, 255)
out = bgr.copy(); out[cloth] = navy[cloth]; out[cloth & shoe] = black[cloth & shoe]
im[..., :3] = out.astype(np.uint8); wr(os.path.join(dst, body), im)
print("몸 그림: 옷 칸", round(cloth.mean() * 100, 1), "%, 피부", round(skin.mean() * 100, 1), "%, 옷 기본 밝기", round(base, 3))
head = next(f for f in os.listdir(src) if f.endswith("_head_color.tga"))
im = rd(os.path.join(src, head)).copy(); H, W = im.shape[:2]; c = im[..., :3].astype(np.float32)
for b in EYE:                                                     # 파란 눈동자 → 갈색 (밝기 결 그대로)
    x0, y0, x1, y1 = px(b, W, H); r = c[y0:y1, x0:x1]
    blue = (r[..., 0] > r[..., 2] + 12) & (r[..., 0] > 50)
    lm = r.mean(2, keepdims=True) / 255
    brown = np.clip(np.array([28, 52, 92.0]) * (0.5 + 1.4 * lm), 0, 255)
    r[blue] = brown[blue]; c[y0:y1, x0:x1] = r
    print("눈동자 바꾼 점", int(blue.sum()))
m = np.zeros((H, W), np.uint8)
for b in ERASE:                                                   # 문신처럼 주변보다 어두운 무늬만 골라 메움
    x0, y0, x1, y1 = px(b, W, H); r = c[y0:y1, x0:x1].mean(2)
    med = cv2.medianBlur(r.astype(np.uint8), 31).astype(np.float32)
    m[y0:y1, x0:x1] = ((med - r) > 18).astype(np.uint8) * 255
m = cv2.dilate(m, np.ones((5, 5), np.uint8))
c = cv2.inpaint(c.astype(np.uint8), m, 6, cv2.INPAINT_TELEA)
im[..., :3] = c; wr(os.path.join(dst, head), im)
print("머리 그림: 지운 점", int((m > 0).sum()), "→", dst)
