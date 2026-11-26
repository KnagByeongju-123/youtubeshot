"""얼굴 그림(텍스처)의 입술만 선홍색 쪽으로 (사용자 2026-11-26 '루즈 색상은 조금 더 선홍색으로')
   입술 = 입술 칸 안에서 색상 15° 아래·340° 위, 채도 0.25 이상. 색상을 354° 쪽으로 80%, 채도 ×1.35, 밝기 ×1.12 → 원래와 --섞기(기본 0.55) 만큼 섞음
   사용: .supertonic_venv/bin/python 애니3D/입술색.py <그림> [<출력>] [--입술 0.44,0.375,0.56,0.435] [--섞기 0.55] [--색상 354]"""
import sys
import numpy as np
import cv2
from PIL import Image

a = sys.argv[1:]; src = a[0]; dst = a[1] if len(a) > 1 and not a[1].startswith("--") else src
x0, y0, x1, y1 = (float(t) for t in (a[a.index("--입술") + 1] if "--입술" in a else "0.44,0.375,0.56,0.435").split(","))
MIX = float(a[a.index("--섞기") + 1]) if "--섞기" in a else 0.55
TGT = float(a[a.index("--색상") + 1]) if "--색상" in a else 354.0
rgb = np.asarray(Image.open(src).convert("RGB")); H, W = rgb.shape[:2]
hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV).astype(np.float32); h, s, v = hsv[..., 0] * 2, hsv[..., 1] / 255, hsv[..., 2] / 255
box = np.zeros((H, W), np.float32); box[int(H * y0):int(H * y1), int(W * x0):int(W * x1)] = 1; box = cv2.GaussianBlur(box, (0, 0), 6)
lip = ((((h < 15) | (h > 340)) & (s > 0.25)).astype(np.float32)) * box
lip = cv2.GaussianBlur(cv2.morphologyEx(lip, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8)), (0, 0), 1.5)
hh = np.where(h > 180, h - 360, h); t = TGT - 360 if TGT > 180 else TGT
h2 = hh + (t - hh) * 0.8 * lip; h2 = np.where(h2 < 0, h2 + 360, h2)
s2 = np.clip(s * (1 + 0.35 * lip), 0, 1); v2 = np.clip(v * (1 + 0.12 * lip), 0, 1)
out = cv2.cvtColor(np.stack([h2 / 2, s2 * 255, v2 * 255], -1).clip(0, 255).astype(np.uint8), cv2.COLOR_HSV2RGB).astype(np.float32)
out = rgb * (1 - MIX) + out * MIX
Image.fromarray(out.clip(0, 255).astype(np.uint8)).save(dst); print("입술 점", int((lip > 0.5).sum()), "→", dst)
