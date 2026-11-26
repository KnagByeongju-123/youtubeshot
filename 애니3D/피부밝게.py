"""그림(텍스처)의 피부만 밝고 덜 붉게 — 동양인 피부 톤 쪽으로 (사용자 2026-11-26 '얼굴색만 조금 밝게 해서 동양인처럼')
   피부 = 색상 6~35°, 채도 0.12~0.80, 밝기 0.30 이상 (머리카락(어두움)·입술(붉음)·눈은 빠짐). 경계는 부드럽게 섞음
   --입술 x0,y0,x1,y1 (그림 비율): 입술 칸은 피부 고르기에서 빼고 칸 전체를 같은 비율로만 조금 밝게(색·채도 그대로)
     — 아랫입술의 연한 분홍 일부가 피부로 잡혀 하얗게 지워진 듯 얼룩졌음(사용자 2026-11-26 '아랫입술 색이 지워진 부분')
   사용: .supertonic_venv/bin/python 애니3D/피부밝게.py <그림.tga|png> [<출력>] [--밝기 1.16] [--채도 0.78] [--입술 0.44,0.375,0.56,0.435]"""
import sys
import numpy as np
import cv2
from PIL import Image

a = sys.argv[1:]; src = a[0]; dst = a[1] if len(a) > 1 and not a[1].startswith("--") else src
BR = float(a[a.index("--밝기") + 1]) if "--밝기" in a else 1.16
SA = float(a[a.index("--채도") + 1]) if "--채도" in a else 0.78
rgb = np.asarray(Image.open(src).convert("RGB"))
hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV).astype(np.float32)
h, s, v = hsv[..., 0] * 2, hsv[..., 1] / 255, hsv[..., 2] / 255
m = ((h >= 6) & (h <= 35) & (s > 0.12) & (s < 0.80) & (v > 0.30)).astype(np.float32)
m = cv2.GaussianBlur(cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8)), (0, 0), 2.0)
lipm = np.zeros_like(m)
if "--입술" in a:
    x0, y0, x1, y1 = (float(t) for t in a[a.index("--입술") + 1].split(",")); H_, W_ = m.shape
    lipm[int(y0 * H_):int(y1 * H_), int(x0 * W_):int(x1 * W_)] = 1.0
    lipm = cv2.GaussianBlur(lipm, (0, 0), 6.0)
    lipcore = cv2.GaussianBlur((((h < 15) | (h > 340)) & (s > 0.30)).astype(np.float32) * lipm, (0, 0), 1.5)   # 입술 색(색상 15° 아래, 피부는 20° 이상)
    lipm = np.clip(lipm * 1.0, 0, 1)
    m = m * (1 - np.clip(lipcore * 2, 0, 1))                                                          # 입술 둘레는 피부 처리 빼기
v_l = v * (1 + (BR - 1) * 0.5 * np.clip(lipcore * 2, 0, 1)) if "--입술" in a else v                     # 입술은 반만 고르게 밝게
v2 = np.clip(v_l * (1 + (BR - 1) * m), 0, 1); s2 = s * (1 + (SA - 1) * m)
h2 = h + 3.0 * m                                               # 주황 → 아주 살짝 노란 쪽
out = cv2.cvtColor(np.stack([h2 / 2, s2 * 255, v2 * 255], -1).clip(0, 255).astype(np.uint8), cv2.COLOR_HSV2RGB)
Image.fromarray(out).save(dst)
print("피부 칸", round(float((m > 0.5).mean()) * 100, 1), "% 밝게 →", dst)
