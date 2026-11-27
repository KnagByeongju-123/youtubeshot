"""3D 얼굴 정면(정사영 렌더)과 사진의 표지점 차이로 '얼굴모양맞추기.py --2D' 용 목표(shape_lm.npz)를 만듦 — 격자 비교에서 벗어난 만큼 되돌려 맞추기 (사용자 2026-11-27 '격자 차이대로 다시 맞춰줘')
   - 정사영 렌더(view5.html ?os=반폭) 이라 화면 점 → 실제 자리(m)가 정확: x = (px - W/2)/(W/2)·os, 높이 = cy - (py - H/2)/(H/2)·os
   - 사진 표지점을 전체 표지점에 가장 잘 맞게(크기·회전·이동) 옮긴 뒤 목표로 씀 → 머리 크기는 그대로, 눈 사이·턱 길이·얼굴 윤곽 비율만 맞춤
   - 눈·입 테두리는 모양(눈 뜬 높이·입 벌림)은 두고 가운데 자리와 가로 폭만 따라감 (눈 뜬 높이는 표정굳히기로 따로)
   사용: <mediapipe 파이썬> 애니3D/얼굴격자맞추기.py <사진> <정사영 렌더.png> <출력 shape_lm.npz> [--cy 1.6] [--os 0.16] [--세기 1.0]"""
import sys
import numpy as np, cv2
import mediapipe as mp

a = sys.argv[1:]; ph_p, md_p, out = a[0], a[1], a[2]
def opt(k, d): return float(a[a.index(k) + 1]) if k in a else d
CY, OS, K = opt("--cy", 1.6), opt("--os", 0.16), opt("--세기", 1.0)
fm = mp.solutions.face_mesh.FaceMesh(static_image_mode=True, refine_landmarks=True, max_num_faces=1, min_detection_confidence=0.3)
def lm(im):
    r = fm.process(cv2.cvtColor(im, cv2.COLOR_BGR2RGB)); h, w = im.shape[:2]
    return np.array([[l.x * w, l.y * h] for l in r.multi_face_landmarks[0].landmark])[:468]
P = lm(cv2.imread(ph_p)); md = cv2.imread(md_p); Hh, Ww = md.shape[:2]; Mpx = lm(md)
M = np.stack([(Mpx[:, 0] - Ww / 2) / (Ww / 2) * OS, CY - (Mpx[:, 1] - Hh / 2) / (Hh / 2) * OS], 1)   # 블렌더 x, z (m)
Pm = np.stack([P[:, 0], -P[:, 1]], 1)                                                                     # 사진: 위가 + 가 되게
ma, mb = Pm.mean(0), M.mean(0); A0, B0 = Pm - ma, M - mb
U, S_, Vt = np.linalg.svd(B0.T @ A0); R = U @ Vt
if np.linalg.det(R) < 0: U[:, -1] *= -1; R = U @ Vt
sc = S_.sum() / (A0 ** 2).sum(); T = A0 @ (sc * R).T + mb
FMs = mp.solutions.face_mesh
def ids(c): return sorted({i for e in c for i in e})
for grp in (ids(FMs.FACEMESH_LEFT_EYE), ids(FMs.FACEMESH_RIGHT_EYE), ids(FMs.FACEMESH_LIPS)):
    cm, ct = M[grp].mean(0), T[grp].mean(0)
    wr = np.ptp(T[grp, 0]) / max(1e-6, np.ptp(M[grp, 0]))
    T[grp, 0] = ct[0] + (M[grp, 0] - cm[0]) * wr; T[grp, 1] = ct[1] + (M[grp, 1] - cm[1])
D = M + (T - M) * K
oval = ids(FMs.FACEMESH_FACE_OVAL)
d = np.linalg.norm(D - M, axis=1) * 1000
print("옮길 거리 평균 %.1fmm, 최대 %.1fmm (눈 사이·턱·윤곽)" % (d.mean(), d.max()))
for n, i, j in (("눈동자 사이(눈 가운데)", 133, 362), ("턱끝 높이", 152, 152), ("얼굴 옆 폭", 234, 454)):
    print(f"  {n}: 지금 {M[i] if i == j else np.linalg.norm(M[i] - M[j]):} → 목표 {D[i] if i == j else np.linalg.norm(D[i] - D[j])}")
np.savez(out, src=M, dst=D, oval=M[oval])
print("→", out)
