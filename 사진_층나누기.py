"""사진을 앞층·뒤층으로 나눔 — 블렌더 '공간 통과' 영상용 (사용자 제안 2026-11-07 '사물들 사이를 통과, 공간 내부 통과')
.sd_venv/bin/python -X utf8 사진_층나누기.py <사진> <깊이.npy> <결과폴더> [--앞비율 0.3]
  - 깊이(0=멀다 1=가깝다)에서 가장 가까운 쪽 '앞비율'(기본 30%)을 앞층으로 (작은 조각은 버리고 가장자리를 조금 넓힘)
  - 앞층이 가리던 뒤 배경을 채움(OpenCV inpaint, 그림·깊이 모두) → 카메라가 앞층을 지나가면 그 뒤 공간이 보임
  - 결과: <폴더>/앞층_mask.png (흰색 = 앞층), 뒤층.png, 뒤층_깊이.npy"""
import os
import sys

import cv2
import numpy as np

img_p, npy_p, out = sys.argv[1], sys.argv[2], sys.argv[3]
ratio = float(sys.argv[sys.argv.index("--앞비율") + 1]) if "--앞비율" in sys.argv else 0.3
os.makedirs(out, exist_ok=True)
img = cv2.imread(img_p)
H, W = img.shape[:2]
dep = cv2.resize(np.load(npy_p).astype(np.float32), (W, H), interpolation=cv2.INTER_LINEAR)
thr = np.quantile(dep, 1 - ratio)
m = (dep >= thr).astype(np.uint8)
m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((9, 9), np.uint8))       # 작은 조각 버림
n, lab, st, _ = cv2.connectedComponentsWithStats(m)
keep = np.zeros_like(m)
for k in range(1, n):
    if st[k, 4] > H * W * 0.004:
        keep[lab == k] = 1
grow = cv2.dilate(keep, np.ones((15, 15), np.uint8))                     # 가장자리 번짐까지 지우게 넓힘
cv2.imwrite(os.path.join(out, "앞층_mask.png"), keep * 255)
s = 0.5                                                                  # 빠르게 하려고 반 크기로 채운 뒤 키움
small = cv2.resize(img, None, fx=s, fy=s)
gm = cv2.resize(grow * 255, None, fx=s, fy=s, interpolation=cv2.INTER_NEAREST)
bg = cv2.inpaint(small, gm, 12, cv2.INPAINT_TELEA)
bg = cv2.resize(bg, (W, H))
bg = np.where(grow[..., None] > 0, cv2.GaussianBlur(bg, (0, 0), 3), img)  # 채운 곳만 바꾸고 나머지는 원본
cv2.imwrite(os.path.join(out, "뒤층.png"), bg)
d8 = (dep / dep.max() * 65535).astype(np.uint16)
dfill = cv2.inpaint(cv2.resize((d8 >> 8).astype(np.uint8), None, fx=s, fy=s), gm, 12, cv2.INPAINT_TELEA)
dfill = cv2.resize(dfill, (W, H)).astype(np.float32) / 255 * dep.max()
bdep = np.where(grow > 0, np.minimum(dfill, thr * 0.95), dep)            # 채운 배경은 앞층보다 확실히 뒤로
np.save(os.path.join(out, "뒤층_깊이.npy"), cv2.resize(bdep, (np.load(npy_p).shape[1], np.load(npy_p).shape[0])).astype(np.float16))
print("OK 앞층 비율 %.1f%%" % (keep.mean() * 100), out)
