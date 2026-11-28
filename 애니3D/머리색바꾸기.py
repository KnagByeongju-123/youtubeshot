"""머리카락 그림(opacity_color, 투명도 유지)과 얼굴 그림의 머리 부분을 검은 머리로 (사용자 2026-11-27 '이 모습' — 금속 끄기 뒤 Rocketbox 머리카락 그림의 푸른 기가 드러나 청록색으로 보였음)
   새 색 = 목표색 × (원래 밝기 ÷ 머리 중간 밝기)^대비 → 결은 살림. 얼굴 그림(head_color)은 어두운 곳(L<--어두움)만 바꿈 → 피부·눈썹 결 그대로
   사용: python 애니3D/머리색바꾸기.py <그림.tga> <출력.tga> [--색 24,20,20] [--대비 1.0] [--어두움 0] (얼굴 그림이면 --어두움 70) [--밝은줄 61] [--넓게] [--칸 x0,y0,x1,y1] [--칸어둡게 x0,y0,x1,y1]"""
import sys
import numpy as np, cv2
from PIL import Image
a = sys.argv[1:]; src, dst = a[0], a[1]
def opt(k, d): return a[a.index(k) + 1] if k in a else d
COL = np.array([float(v) for v in opt("--색", "24,20,20").split(",")]); CON = float(opt("--대비", "1.0")); DARK = float(opt("--어두움", "0"))
im = np.array(Image.open(src)); rgb = im[..., :3].astype(np.float32)
L = cv2.cvtColor(im[..., :3], cv2.COLOR_RGB2LAB)[..., 0].astype(np.float32)
cool = ((rgb[..., 1] + rgb[..., 2]) / 2 - rgb[..., 0]) if DARK > 0 else None   # 푸른 기(초록·파랑 > 빨강): 피부엔 없음 → 머리카락
LABf = cv2.cvtColor(im[..., :3], cv2.COLOR_RGB2LAB).astype(np.float32)
WIDE = "--넓게" in a        # 가르마 작업 때 넓힌 규칙(색 없는 회색·밝은 푸른 기도 머리) — 사용자 '머리카락 지저분해짐 원상복귀'로 기본은 예전 규칙
grey = ((np.abs(LABf[..., 1] - 128) < 6) & (np.abs(LABf[..., 2] - 128) < 7) & (L < 140)) if WIDE else np.zeros(L.shape, bool)
CT, CL = (3, 165) if WIDE else (4, 130)   # 색이 없는 회색: 피부엔 없음 → 머리카락 (이마 옆 회색 얼룩)
m = np.ones(L.shape, bool) if DARK <= 0 else grey | ((L < DARK) | ((cool > CT) & (L < CL))) & (rgb[..., 0] - rgb[..., 1] < 12)   # 붉은 입속·잇몸은 빼고 (입 벌리면 회색으로 보였음)
if im.shape[2] == 4 and DARK > 0: m &= im[..., 3] > 8          # 머리카락 그림(DARK=0)은 투명한 곳 색도 바꿈 — 가장자리에 옛 색(밝은 색)이 비쳐 흰 줄이 보였음
med = np.median(L[m & (im[..., 3] > 8)] if im.shape[2] == 4 else L[m]) + 1e-6
new = np.clip(COL * np.clip((L / med) ** CON, 0, 4)[..., None], 0, 255)
w = m.astype(np.float32) if DARK <= 0 else np.maximum(np.maximum(grey.astype(np.float32), np.clip((DARK - L) / 20, 0, 1)), (np.clip((cool - 3) / 5, 0, 1) if WIDE else np.clip((cool - 4) / 8, 0, 1)) * (L < CL)) * m
w = w[..., None]
im[..., :3] = (rgb * (1 - w) + new * w).astype(np.uint8)
if "--밝은줄" in a:   # 머리카락 칸 안의 밝은 점·줄(원래 그림의 옆 가르마 두피 등)을 둘레 머리색으로 — 둘레 대부분이 머리카락인 곳만 (2026-11-27 '가르마')
    k = int(opt("--밝은줄", "61")) | 1
    L2 = cv2.cvtColor(im[..., :3], cv2.COLOR_RGB2LAB)[..., 0].astype(np.float32)
    dark = (L2 < 55).astype(np.float32)
    frac = cv2.blur(dark, (k, k))
    line = (frac > float(opt("--둘레", "0.6"))) & (L2 >= 55)
    if "--칸" in a:     # 이 네모(그림 픽셀 x0,y0,x1,y1) 안만, 둘레 조건 없이 밝은 점 모두 (2026-11-28 '여기 부분 조금 메워줘' — 옆 가르마 두피 끝)
        x0, y0, x1, y1 = (int(v) for v in opt("--칸", "0,0,0,0").split(","))
        boxm = np.zeros(L2.shape, bool); boxm[y0:y1, x0:x1] = True
        line = boxm & (L2 >= 45)
    line = cv2.dilate(line.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool) & ((frac > float(opt("--둘레", "0.6")) - 0.1) | ("--칸" in a))
    den = cv2.blur(dark, (k, k)) + 1e-6
    fill = np.stack([cv2.blur(im[..., c].astype(np.float32) * dark, (k, k)) / den for c in range(3)], -1)
    if "--칸" in a:   # 칸 안은 평평한 색 대신 옆(왼쪽 --결옮김 px)의 머리카락 결을 옮겨 붙이고 경계는 부드럽게
        sh = int(opt("--결옮김", "70"))
        src_ = np.roll(im[..., :3], sh, axis=1).astype(np.float32)
        wq = cv2.GaussianBlur(line.astype(np.float32), (0, 0), 4)[..., None]
        im[..., :3] = (im[..., :3] * (1 - wq) + src_ * wq).astype(np.uint8)
    else:
        im[line, :3] = fill[line].astype(np.uint8)
    print("밝은 줄 메움 %.2f%%" % (line.mean() * 100))
if "--칸어둡게" in a:   # 네모(x0,y0,x1,y1) 안의 푸른 기 도는 옅은 머리 가닥·두피를 머리색으로 짙게 (2026-11-28 '여기 부분 조금 메워줘' — 가르마 끝 청록 두피)
    x0, y0, x1, y1 = (int(v) for v in opt("--칸어둡게", "0,0,0,0").split(","))
    rg = im[..., :3].astype(np.float32); coolk = (rg[..., 1] + rg[..., 2]) / 2 - rg[..., 0]
    Lk = cv2.cvtColor(im[..., :3], cv2.COLOR_RGB2LAB)[..., 0].astype(np.float32)
    box = np.zeros(Lk.shape, np.float32); box[y0:y1, x0:x1] = 1; box = cv2.GaussianBlur(box, (0, 0), 8)
    hairc = np.median(rg[(Lk < 40)].reshape(-1, 3), 0)
    LABk = cv2.cvtColor(im[..., :3], cv2.COLOR_RGB2LAB).astype(np.float32)
    chroma = np.hypot(LABk[..., 1] - 128, LABk[..., 2] - 128)
    wk = np.clip((14 - chroma) / 8, 0, 1) * np.clip((Lk - 25) / 40, 0, 1) * box     # 색 없는 회색 두피·옅은 가닥(빛을 받으면 청록으로 보임)
    wk = cv2.GaussianBlur(wk, (0, 0), 1.5)[..., None]
    grain = np.clip(Lk / (cv2.GaussianBlur(Lk, (0, 0), 3) + 1e-3), 0.4, 2.2)[..., None]   # 머리카락 결(밝고 어두운 가닥)은 살림
    im[..., :3] = np.clip(rg * (1 - wk) + hairc * grain * wk, 0, 255).astype(np.uint8)
    print("칸 어둡게: 바뀐 점", int((wk[..., 0] > 0.3).sum()))
Image.fromarray(im).save(dst); print("머리색 바꿈 %.0f%% →" % (m.mean() * 100), dst)
