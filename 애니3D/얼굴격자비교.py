"""사진 얼굴과 3D 얼굴(정면 렌더)을 눈동자 두 점에 맞춰 같은 크기·자리로 놓고, 사진 기준 격자(눈썹·눈·코밑·입·턱 가로줄, 눈꼬리·눈머리·콧볼·입꼬리·얼굴 옆 세로줄)를 둘 다에 그려 비교 (사용자 2026-11-27 '얼굴에 격자를 그려서 비교')
   - 3D 쪽에는 자기 표지점을 초록 점으로 → 빨간 격자(사진)에서 얼마나 벗어나는지 보임, 세 번째 칸은 반투명 겹침
   - 수치: 눈동자 사이 거리(IPD)=1 로 나눈 비율과 3D/사진 배율 (_격자수치.txt)
   사용: <mediapipe 파이썬> 애니3D/얼굴격자비교.py <사진> <3D 정면 그림> <출력.png>"""
import sys, os
import numpy as np, cv2
import mediapipe as mp

ph_p, md_p, out_p = sys.argv[1:4]
fm = mp.solutions.face_mesh.FaceMesh(static_image_mode=True, refine_landmarks=True, max_num_faces=1, min_detection_confidence=0.3)
def lm(im):
    r = fm.process(cv2.cvtColor(im, cv2.COLOR_BGR2RGB))
    if not r.multi_face_landmarks: sys.exit("얼굴 표지점 못 찾음")
    h, w = im.shape[:2]; return np.array([[l.x * w, l.y * h] for l in r.multi_face_landmarks[0].landmark])
CW, CH = 800, 1000; PL, PR = np.array([320., 400.]), np.array([480., 400.])   # 눈동자 자리(캔버스)
def align(im, L):
    a, b = L[468], L[473]                          # 두 눈동자 (사진 속 왼쪽·오른쪽)
    if a[0] > b[0]: a, b = b, a
    src = np.float32([a, b, a + np.array([-(b - a)[1], (b - a)[0]])]); dst = np.float32([PL, PR, PL + np.array([0, PR[0] - PL[0]])])
    M = cv2.getAffineTransform(src, dst)
    img = cv2.warpAffine(im, M, (CW, CH), borderValue=(255, 255, 255))
    L2 = np.c_[L, np.ones(len(L))] @ M.T; return img, L2
ph = cv2.imread(ph_p); md = cv2.imread(md_p)
Ip, Lp = align(ph, lm(ph)); Im, Lm = align(md, lm(md))
IPD = PR[0] - PL[0]
H = {"이마(얼굴 윗선)": [10], "눈썹": [105, 334], "눈": [468, 473], "코밑": [2], "입": [13, 14], "턱끝": [152]}
V = {"얼굴 옆": [234, 454], "눈꼬리": [33, 263], "눈머리": [133, 362], "콧볼": [129, 358], "입꼬리": [61, 291]}
def hy(L, ids): return L[ids, 1].mean()
def grid(img, L, col, thick=1):
    for k, ids in H.items():
        y = int(round(hy(L, ids))); cv2.line(img, (0, y), (CW, y), col, thick)
    for k, ids in V.items():
        for i in ids:
            x = int(round(L[i, 0])); cv2.line(img, (x, 0), (x, CH), col, thick)
RED, GRN = (0, 0, 255), (0, 170, 0)
A = Ip.copy(); grid(A, Lp, RED, 2)
B = Im.copy(); grid(B, Lp, RED, 2)
for ids in list(H.values()) + list(V.values()):
    for i in ids: cv2.circle(B, tuple(int(v) for v in Lm[i]), 6, GRN, -1)
C = cv2.addWeighted(Ip, 0.5, Im, 0.5, 0); grid(C, Lp, RED, 1)
for i in [i for ids in V.values() for i in ids] + [10, 152, 2, 13, 105, 334]: cv2.circle(C, tuple(int(v) for v in Lm[i]), 5, GRN, -1)
def tag(img, t): cv2.rectangle(img, (0, 0), (CW, 44), (255, 255, 255), -1); cv2.putText(img, t, (10, 32), 0, 1.0, (0, 0, 0), 2); return img
out = np.hstack([tag(A, "photo + grid"), tag(B, "3D + photo grid (green = 3D)"), tag(C, "overlay 50%")])
# 위아래 자르기: 이마 위 80 ~ 턱 아래 80
y0 = int(max(0, min(hy(Lp, [10]), hy(Lm, [10])) - 120)); y1 = int(min(CH, max(hy(Lp, [152]), hy(Lm, [152])) + 90))
out = np.vstack([out[:44], out[max(44, y0):y1]])
cv2.imwrite(out_p, out)
def d(L, i, j): return np.linalg.norm(L[i] - L[j]) / IPD
items = [("얼굴 너비(볼 옆)", lambda L: d(L, 234, 454)), ("얼굴 높이(이마선~턱)", lambda L: (L[152, 1] - L[10, 1]) / IPD),
         ("눈 가로", lambda L: (d(L, 33, 133) + d(L, 263, 362)) / 2), ("눈 세로(뜬 정도)", lambda L: (d(L, 159, 145) + d(L, 386, 374)) / 2),
         ("눈머리 사이", lambda L: d(L, 133, 362)), ("눈썹~눈", lambda L: (hy(L, [468, 473]) - hy(L, [105, 334])) / IPD),
         ("콧볼 너비", lambda L: d(L, 129, 358)), ("눈~코밑", lambda L: (L[2, 1] - hy(L, [468, 473])) / IPD),
         ("입 너비", lambda L: d(L, 61, 291)), ("코밑~입", lambda L: (hy(L, [13, 14]) - L[2, 1]) / IPD),
         ("입~턱끝", lambda L: (L[152, 1] - hy(L, [13, 14])) / IPD), ("턱 너비(턱각)", lambda L: d(L, 172, 397))]
lines = ["항목 (눈동자 사이 = 1)        사진    3D    3D/사진"]
for n, f in items:
    p, m = f(Lp), f(Lm); lines.append(f"{n:16s} {p:6.2f} {m:6.2f}  {m / p:5.2f}{'  ←' if abs(m / p - 1) > 0.08 else ''}")
txt = "\n".join(lines); print(txt)
open(os.path.splitext(out_p)[0] + "_격자수치.txt", "w", encoding="utf-8").write(txt + "\n")
