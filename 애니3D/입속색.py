"""Rocketbox 얼굴 그림의 입 안(잇몸·입천장·혀 칸)을 밝은 짙은 선홍색으로 — 입 안이 그늘져 영상에서 거의 검게 보였음 (사용자 2026-11-26 '입 속이 너무 검은색, 짙은 선홍색이 나을 듯')
   칸(기본: 그림 왼쪽 아래 x 0~0.22, y 0.61~1.0) 안에서 이(밝고 채도 낮음)는 그대로, 나머지는 색상 350°·채도 ≥0.6·밝기 ×--밝기
   사용: .supertonic_venv/bin/python 애니3D/입속색.py <그림> [<출력>] [--칸 0,0.61,0.22,1.0] [--밝기 1.9]"""
import sys
import numpy as np
import cv2
from PIL import Image

a = sys.argv[1:]; src = a[0]; dst = a[1] if len(a) > 1 and not a[1].startswith("--") else src
x0, y0, x1, y1 = (float(t) for t in (a[a.index("--칸") + 1] if "--칸" in a else "0,0.61,0.22,1.0").split(","))
BR = float(a[a.index("--밝기") + 1]) if "--밝기" in a else 1.9
rgb = np.asarray(Image.open(src).convert("RGB")); H, W = rgb.shape[:2]
hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV).astype(np.float32); h, s, v = hsv[..., 0] * 2, hsv[..., 1] / 255, hsv[..., 2] / 255
box = np.zeros((H, W), np.float32); box[int(H * y0):int(H * y1), int(W * x0):int(W * x1)] = 1
teeth = (v > 0.55) & (s < 0.35)
m = box * (~teeth) * (v > 0.02)
m = cv2.GaussianBlur(m.astype(np.float32), (0, 0), 1.2)
h2 = h * (1 - m) + 350 * m; s2 = s * (1 - m) + np.maximum(s, 0.62) * m; v2 = np.clip(v * (1 + (BR - 1) * m) + 0.04 * m, 0, 1)
out = cv2.cvtColor(np.stack([h2 / 2, s2 * 255, v2 * 255], -1).clip(0, 255).astype(np.uint8), cv2.COLOR_HSV2RGB)
Image.fromarray(out).save(dst); print("입 안 칠한 점", int((m > 0.5).sum()), "→", dst)
