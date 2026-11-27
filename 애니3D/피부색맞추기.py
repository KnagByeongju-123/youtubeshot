"""얼굴 그림(head_color)의 피부색만 목표 색으로 옮김 — 모양·다른 그림은 그대로 (사용자 2026-11-27 '얼굴 텍스처만 수정해봐. 피부색을')
   피부 = 지금 피부 가운데 색(Lab)과 색조가 가까운 곳(입술·눈썹·머리카락·눈은 색조·밝기가 달라 덜 바뀜). 밝기 차이·색조 차이를 그 정도만큼 더함
   목표는 OpenCV Lab(0~255): L 밝기, a 클수록 붉게(분홍), b 클수록 노랗게(살구). 사진 볼 ≈ 174,149,146 · 이마 ≈ 193,146,144
   사용: python 애니3D/피부색맞추기.py <입력.tga> <출력.tga> --목표 190,149,147 [--넓이 14] [--고르게 0.8] [--얼룩크기 0.012]"""
import sys
import numpy as np, cv2
from PIL import Image

a = sys.argv[1:]; src, dst = a[0], a[1]
def opt(k, d): return a[a.index(k) + 1] if k in a else d
tgt = np.array([float(v) for v in opt("--목표", "190,149,147").split(",")])
WID = float(opt("--넓이", "14"))
im = np.array(Image.open(src)); has_a = im.shape[2] == 4
bgr = im[..., [2, 1, 0]].copy()
lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB).astype(np.float32)
rough = (lab[..., 0] > 120) & (np.abs(lab[..., 1] - 146) < 14) & (np.abs(lab[..., 2] - 147) < 16)
med = np.median(lab[rough], 0)
dab = np.linalg.norm(lab[..., 1:] - med[1:], axis=2)
w = np.exp(-(dab / WID) ** 2) * np.clip((lab[..., 0] - 70) / 50, 0, 1)    # 피부와 색조가 가깝고 너무 어둡지 않은 곳
w = cv2.GaussianBlur(w, (0, 0), 2)
EVEN = float(opt("--고르게", "0"))     # 0~1: 피부의 큰 얼룩(볼 그림자·눈가 붉은 테·코 그늘 — 사진 조명이 구워진 것)을 목표 색으로 고르게, 잔결(모공·주근깨)은 그대로
if EVEN > 0:
    sig = im.shape[0] * float(opt("--얼룩크기", "0.012"))
    ww = cv2.GaussianBlur(w, (0, 0), sig) + 1e-6
    low = np.stack([cv2.GaussianBlur(lab[..., i] * w, (0, 0), sig) for i in range(3)], -1) / ww[..., None]   # 피부만으로 낸 큰 얼룩 색
    g = (EVEN * w)[..., None]
    lab = lab + (tgt - low) * g
    med = tgt.copy()
lab[..., 0] += (tgt[0] - med[0]) * w * np.clip(lab[..., 0] / med[0], 0, 1.2)   # 밝기는 비율로(그늘·주근깨 결 유지)
lab[..., 1:] += (tgt[1:] - med[1:]) * w[..., None]
out = cv2.cvtColor(np.clip(lab, 0, 255).astype(np.uint8), cv2.COLOR_LAB2BGR)[..., ::-1]
res = im.copy(); res[..., :3] = out
Image.fromarray(res).save(dst)
print("피부 가운데 색", med.round(1), "→ 목표", tgt, "바뀐 넓이 %.0f%%" % ((w > 0.5).mean() * 100), "→", dst)
