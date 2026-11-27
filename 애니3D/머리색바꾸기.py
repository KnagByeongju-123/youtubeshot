"""머리카락 그림(opacity_color, 투명도 유지)과 얼굴 그림의 머리 부분을 검은 머리로 (사용자 2026-11-27 '이 모습' — 금속 끄기 뒤 Rocketbox 머리카락 그림의 푸른 기가 드러나 청록색으로 보였음)
   새 색 = 목표색 × (원래 밝기 ÷ 머리 중간 밝기)^대비 → 결은 살림. 얼굴 그림(head_color)은 어두운 곳(L<--어두움)만 바꿈 → 피부·눈썹 결 그대로
   사용: python 애니3D/머리색바꾸기.py <그림.tga> <출력.tga> [--색 24,20,20] [--대비 1.0] [--어두움 0] (얼굴 그림이면 --어두움 70)"""
import sys
import numpy as np, cv2
from PIL import Image
a = sys.argv[1:]; src, dst = a[0], a[1]
def opt(k, d): return a[a.index(k) + 1] if k in a else d
COL = np.array([float(v) for v in opt("--색", "24,20,20").split(",")]); CON = float(opt("--대비", "1.0")); DARK = float(opt("--어두움", "0"))
im = np.array(Image.open(src)); rgb = im[..., :3].astype(np.float32)
L = cv2.cvtColor(im[..., :3], cv2.COLOR_RGB2LAB)[..., 0].astype(np.float32)
cool = ((rgb[..., 1] + rgb[..., 2]) / 2 - rgb[..., 0]) if DARK > 0 else None   # 푸른 기(초록·파랑 > 빨강): 피부엔 없음 → 머리카락
m = np.ones(L.shape, bool) if DARK <= 0 else ((L < DARK) | ((cool > 4) & (L < 130))) & (rgb[..., 0] - rgb[..., 1] < 12)   # 붉은 입속·잇몸은 빼고 (입 벌리면 회색으로 보였음)
if im.shape[2] == 4 and DARK > 0: m &= im[..., 3] > 8          # 머리카락 그림(DARK=0)은 투명한 곳 색도 바꿈 — 가장자리에 옛 색(밝은 색)이 비쳐 흰 줄이 보였음
med = np.median(L[m & (im[..., 3] > 8)] if im.shape[2] == 4 else L[m]) + 1e-6
new = np.clip(COL * np.clip((L / med) ** CON, 0, 4)[..., None], 0, 255)
w = m.astype(np.float32) if DARK <= 0 else np.maximum(np.clip((DARK - L) / 20, 0, 1), np.clip((cool - 4) / 8, 0, 1) * (L < 130)) * m
w = w[..., None]
im[..., :3] = (rgb * (1 - w) + new * w).astype(np.uint8)
Image.fromarray(im).save(dst); print("머리색 바꿈 %.0f%% →" % (m.mean() * 100), dst)
