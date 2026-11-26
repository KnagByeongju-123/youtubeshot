"""그림(텍스처)에서 한 가지 색 계열의 옷만 다른 색으로 — 주름·그림자(밝기 결)는 살림 (사용자 2026-11-26 '상의는 검은색으로')
   사용: .supertonic_venv/bin/python 애니3D/옷색바꾸기.py <그림> [<출력>] [--색상 190,260] [--채도 0.12] [--새색 26,26,30] [--대비 1.0]
     --색상 : 바꿀 색의 색상 범위(도, 파랑 = 190~260), --채도 : 이보다 진한 것만, --새색 : 바꿀 색(sRGB 0~255, 기본 검정에 가까운 짙은 회색)
     밝기 결: 새 색 × (원래 밝기 ÷ 그 옷의 중간 밝기)^대비 → 검게 칠해도 주름이 보임"""
import sys
import numpy as np
import cv2
from PIL import Image

a = sys.argv[1:]; src = a[0]; dst = a[1] if len(a) > 1 and not a[1].startswith("--") else src
def opt(k, d): return a[a.index(k) + 1] if k in a else d
H0, H1 = (float(v) for v in opt("--색상", "190,260").split(","))
SMIN = float(opt("--채도", "0.12")); NEW = np.array([float(v) for v in opt("--새색", "26,26,30").split(",")])
CON = float(opt("--대비", "1.0"))
rgb = np.asarray(Image.open(src).convert("RGB")).astype(np.float32)
hsv = cv2.cvtColor(rgb.astype(np.uint8), cv2.COLOR_RGB2HSV).astype(np.float32)
h, s, v = hsv[..., 0] * 2, hsv[..., 1] / 255, hsv[..., 2] / 255
m = ((h >= H0) & (h <= H1) & (s > SMIN) & (v > 0.03)).astype(np.float32)
m = cv2.GaussianBlur(cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8)), (0, 0), 1.0)
lum = rgb.mean(2); med = float(np.median(lum[m > 0.5])) if (m > 0.5).any() else 128.0
fac = np.clip((lum / max(med, 1.0)) ** CON, 0.3, 2.5)[..., None]
new = np.clip(NEW * fac, 0, 255)
out = rgb * (1 - m[..., None]) + new * m[..., None]
Image.fromarray(out.astype(np.uint8)).save(dst)
print("바꾼 칸", round(float((m > 0.5).mean()) * 100, 1), "% →", dst)
