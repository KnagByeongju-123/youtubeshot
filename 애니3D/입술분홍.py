"""얼굴 그림의 입술을 자연스러운 분홍으로 (사용자 2026-11-28 '입술 색 자연스러운 분홍으로' — 윗입술이 회보라, 입술 사이 줄이 청회색이었음)
   입술 칸 = 타원(--가운데 x,y · --반지름 rx,ry, 그림 픽셀), 가장자리 부드럽게. 밝기 결은 두고 색(Lab a·b)을 목표 분홍으로 옮김,
   입술 사이 어두운 줄은 짙은 장밋빛으로. 밝기는 --밝기 배
   사용: python 애니3D/입술분홍.py <head_color.tga> <출력.tga> [--가운데 1023,823] [--반지름 105,42] [--색 158,146] [--세기 0.85] [--밝기 1.0]"""
import sys
import numpy as np, cv2
from PIL import Image

a = sys.argv[1:]; src, dst = a[0], a[1]
def opt(k, d): return [float(v) for v in (a[a.index(k) + 1] if k in a else d).split(",")]
cx, cy = opt("--가운데", "1023,823"); rx, ry = opt("--반지름", "105,42")
ta, tb = opt("--색", "158,146"); K = opt("--세기", "0.85")[0]; BR = opt("--밝기", "1.0")[0]
im = np.array(Image.open(src)); rgb = np.ascontiguousarray(im[..., :3])
lab = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB).astype(np.float32)
H, W = rgb.shape[:2]; yy, xx = np.mgrid[0:H, 0:W]
d = ((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2
m = np.clip((1.15 - d) / 0.35, 0, 1).astype(np.float32)
m = cv2.GaussianBlur(m, (0, 0), 3)
L = lab[..., 0]
gap = np.clip((175 - L) / 40, 0, 1) * m                         # 입술 사이·입꼬리 어두운 곳
lab[..., 1] = lab[..., 1] * (1 - m * K) + (ta * (1 - gap) + 150 * gap) * m * K
lab[..., 2] = lab[..., 2] * (1 - m * K) + (tb * (1 - gap) + 140 * gap) * m * K
lab[..., 0] = L * (1 + (BR - 1) * m)
out = cv2.cvtColor(np.clip(lab, 0, 255).astype(np.uint8), cv2.COLOR_LAB2RGB)
im[..., :3] = out; Image.fromarray(im).save(dst)
print("입술 분홍 →", dst)
