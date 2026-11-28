"""Rocketbox Business_Female_03(베이지 치마 정장) 몸 그림을 남색 정장 + 흰 셔츠 + 검은 구두로 칠함 (사용자 2026-11-27 사진 '이 모습': 남색 재킷·무릎 치마·흰 셔츠·검은 하이힐)
   - 그림 칸(1024 기준 좌표, f016_body_color): 손(위 양쪽 끝)·다리(아래, y>735)는 그대로, 구두(위쪽 x 180~330·690~840, y<210), 셔츠(가운데 x 430~600, y 430~690, 목 살색 V 는 그대로)
   - 정장 = 채도 낮은 베이지(S<100, V<175) → 남색 × (원래 밝기 ÷ 중간 밝기)^대비 : 주름·그림자 결 유지
   사용: python 애니3D/rocketbox_정장칠하기.py <f016_body_color.tga> <출력.tga> [--남색 26,32,58] [--셔츠 236,236,240] [--구두 22,22,26] [--대비 1.0]"""
import sys
import numpy as np, cv2
from PIL import Image

a = sys.argv[1:]; src, dst = a[0], a[1]
def opt(k, d): return a[a.index(k) + 1] if k in a else d
NAVY = np.array([float(v) for v in opt("--남색", "26,32,58").split(",")])
SHIRT = np.array([float(v) for v in opt("--셔츠", "236,236,240").split(",")])
SHOE = np.array([float(v) for v in opt("--구두", "22,22,26").split(",")])
CON = float(opt("--대비", "1.0"))
rgb = np.array(Image.open(src).convert("RGB")).astype(np.float32)
H, W = rgb.shape[:2]; k = W / 1024
hsv = cv2.cvtColor(rgb.astype(np.uint8), cv2.COLOR_RGB2HSV_FULL).astype(np.float32)
h, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]
yy, xx = np.mgrid[0:H, 0:W] / k
def box(x0, x1, y0, y1): return (xx >= x0) & (xx < x1) & (yy >= y0) & (yy < y1)
shoe_box = box(180, 330, 0, 210) | box(690, 840, 0, 210)
shirt_box = box(430, 600, 430, 690)
legs = (yy > 735) & ((xx < 320) | (xx > 710))       # 다리(살색 스타킹) — 가운데 아래는 재킷 밑단
hands = box(0, 190, 0, 280) | box(830, 1024, 0, 280) | box(150, 300, 140, 280) | box(720, 880, 140, 280)
skin = (s > 100) & (v > 125)                     # 목·손 살색 (정장보다 진하고 밝음)
shirt = shirt_box & ~skin & ((s > 95) | (h > 180)) & (v < 140)   # 안쪽 갈색 블라우스(진하고 어두움)만 — 재킷 깃은 정장
shirt = cv2.morphologyEx(shirt.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8)).astype(bool) & ~skin
suit = (s < 140) & (v < 175) & ((h < 45) | (h > 245)) & ~shoe_box & ~shirt & ~legs & ~hands & ~(skin & shirt_box)
shoe = shoe_box & (v < 150) & ~(skin & (v > 170))
out = rgb.copy()
def paint(m, col, con):
    if not m.any(): return
    med = np.median(v[m]); f = np.clip((v / med) ** con, 0, 2.2)[..., None]
    soft = cv2.GaussianBlur(m.astype(np.float32), (0, 0), 1.2)[..., None]
    new = np.clip(col * f, 0, 255)
    out[:] = out * (1 - soft) + new * soft
paint(suit, NAVY, CON)
paint(shirt, SHIRT, 0.35)                      # 흰 셔츠: 그림자 결은 약하게
paint(shoe, SHOE, 0.8)
# 셔츠 깃 안쪽·가장자리의 검은 칸(원래 그림의 짙은 갈색 깃 안쪽 — 칠한 뒤 검게 남아 목 옆 셔츠에 검은 얼룩, 2026-11-28 '검게 물든 곳')을 셔츠 흰색(그늘 조금)으로
o8 = out.astype(np.uint8); hv = cv2.cvtColor(o8, cv2.COLOR_RGB2HSV_FULL)
blk = box(420, 600, 420, 565) & (hv[..., 2] < 32) & ~skin
blk = cv2.morphologyEx(blk.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
blk = cv2.dilate(blk, np.ones((3, 3), np.uint8)).astype(bool) & ~skin & (hv[..., 2] < 50)
out[blk] = SHIRT * 0.82
o8 = out.astype(np.uint8); hv2 = cv2.cvtColor(o8, cv2.COLOR_RGB2HSV_FULL)
edge = box(420, 600, 420, 565) & (hv2[..., 1] < 60) & (hv2[..., 2] > 40) & (hv2[..., 2] < 200) & ~skin   # 깃 가장자리 회색 테두리 → 셔츠색
edge = cv2.dilate(edge.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool) & ~skin & (hv2[..., 1] < 70)
out[edge] = SHIRT * 0.9
print("셔츠 검은 칸 → 흰색: %.2f%%" % (blk.mean() * 100))
Image.fromarray(out.astype(np.uint8)).save(dst)
print("정장 %.0f%% 셔츠 %.1f%% 구두 %.1f%% →" % (suit.mean() * 100, shirt.mean() * 100, shoe.mean() * 100), dst)
