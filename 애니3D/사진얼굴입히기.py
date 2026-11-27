"""사진 한 장의 얼굴을 Rocketbox 머리 그림(head_color)에 입힘 (사용자 2026-11-27 'Rocketbox 원래 머리에 사진 얼굴 입히기' — 사진 속 인물 본인·허락 확인함)
   순서: ① Rocketbox 머리를 정면에서 그림(numpy, 그래픽카드 없이) ② 사진·정면 그림에서 얼굴 표지점 478개(MediaPipe Face Mesh, Apache-2.0)
         ③ 사진을 표지점끼리 맞도록 휘어(조각별 아핀) 정면 그림 자리로 옮김 ④ 얼굴 그림의 점(텍셀)마다 3D 자리 → 정면 화면 자리에서 사진 색을 가져와
         얼굴 윤곽 안쪽만 부드럽게 섞음(눈 안·입 안·머리카락에 가려진 곳·옆을 향한 곳은 원래 그림) ⑤ 나머지 피부색은 사진 피부색 쪽으로 옮겨 이음매를 줄임
   먼저: .bpy_venv/bin/python -I 애니3D/rocketbox_얼굴정보.py <인물 폴더> <정보폴더>
   사용: <mediapipe 가 있는 파이썬> 애니3D/사진얼굴입히기.py <사진> <정보폴더> <출력 그림폴더> [--크기 1024] [--위자르기 0.18] [--피부맞춤 1.0] [--섞기폭 0.06] [--눈꺼풀 1.3] [--옆줄이기 0.9] [--밝기 1.25] [--채도 1.0]
   결과: <출력 그림폴더>/<원래 이름>_head_color.tga (rocketbox_변환.py --그림폴더 로 씀) + 확인 그림 _확인_*.png"""
import os, sys, json
import numpy as np, cv2
from PIL import Image
import mediapipe as mp
from skimage.transform import PiecewiseAffineTransform, warp

a = sys.argv[1:]
photo_p, info_d, out_d = a[0], a[1], a[2]
def opt(k, d): return a[a.index(k) + 1] if k in a else d
RES = int(opt("--크기", "1024"))
TOPCUT = float(opt("--위자르기", "0.18"))     # 얼굴 윤곽 위쪽(이마) 중 이 비율은 섞지 않음 — 사진의 앞머리·머리카락이 들어오지 않게
SKIN = float(opt("--피부맞춤", "1.0"))        # 나머지 피부색을 사진 피부색으로 옮기는 세기 (0 = 안 옮김)
FEATHER = float(opt("--섞기폭", "0.06"))      # 경계를 부드럽게 섞는 폭(얼굴 너비 비율)
os.makedirs(out_d, exist_ok=True)
T = np.load(os.path.join(info_d, "tris.npz")); XYZ, UV, MAT = T["xyz"].astype(np.float64), T["uv"].astype(np.float64), T["mat"]
info = json.load(open(os.path.join(info_d, "info.json")))
HEAD = next(i for i, m in enumerate(info["materials"]) if m["name"] and "head" in m["name"].lower())
def read_tex(f):   # tga 는 OpenCV 가 못 읽음 → PIL, BGR(A) 순서로
    im = np.array(Image.open(f)); return im[..., [2, 1, 0, 3]] if im.shape[2] == 4 else im[..., ::-1].copy()
texs = [read_tex(m["color"]) if m["color"] else None for m in info["materials"]]
OPAC = [i for i, m in enumerate(info["materials"]) if m["name"] and "opacity" in m["name"].lower()]

# ---------- ① 정면 그림 (얼굴은 -Y 쪽을 봄) ----------
top = XYZ[..., 2].max()
hv = XYZ[MAT == HEAD].reshape(-1, 3); hv = hv[hv[:, 2] > top - 0.32]
CX, CZ, SC = (hv[:, 0].min() + hv[:, 0].max()) / 2, top - 0.13, 0.27
def to_px(P): return (P[..., 0] - CX) / SC * RES + RES / 2, RES / 2 - (P[..., 2] - CZ) / SC * RES
def bary_raster(x, y, W, H):
    """세모 하나를 화면에 깔 때 덮는 점들과 무게 (w0,w1,w2)"""
    x0, x1 = int(max(0, np.floor(x.min()))), int(min(W - 1, np.ceil(x.max())))
    y0, y1 = int(max(0, np.floor(y.min()))), int(min(H - 1, np.ceil(y.max())))
    if x0 > x1 or y0 > y1: return None
    gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
    den = (y[1] - y[2]) * (x[0] - x[2]) + (x[2] - x[1]) * (y[0] - y[2])
    if abs(den) < 1e-14: return None
    w0 = ((y[1] - y[2]) * (gx - x[2]) + (x[2] - x[1]) * (gy - y[2])) / den
    w1 = ((y[2] - y[0]) * (gx - x[2]) + (x[0] - x[2]) * (gy - y[2])) / den
    w2 = 1 - w0 - w1; e = -1e-6; ins = (w0 >= e) & (w1 >= e) & (w2 >= e)
    if not ins.any(): return None
    return gy[ins].astype(int), gx[ins].astype(int), w0[ins], w1[ins], w2[ins]
def tex_sample(img, u, v):
    h, w = img.shape[:2]
    xs = np.clip((u % 1.0) * w, 0, w - 1).astype(int); ys = np.clip((1 - v % 1.0) * h, 0, h - 1).astype(int)
    return img[ys, xs]
PX, PY = to_px(XYZ); DEP = XYZ[..., 1]
front = np.zeros((RES, RES, 3), np.uint8); depth = np.full((RES, RES), np.inf)
order = np.argsort(MAT == HEAD)   # 아무 순서나 상관없음(깊이 비교)
for k in order:
    r = bary_raster(PX[k], PY[k], RES, RES)
    if r is None: continue
    yy, xx, w0, w1, w2 = r
    d = w0 * DEP[k, 0] + w1 * DEP[k, 1] + w2 * DEP[k, 2]
    uu = w0 * UV[k, 0, 0] + w1 * UV[k, 1, 0] + w2 * UV[k, 2, 0]; vv = w0 * UV[k, 0, 1] + w1 * UV[k, 1, 1] + w2 * UV[k, 2, 1]
    img = texs[MAT[k]]
    if img is None: continue
    c = tex_sample(img, uu, vv)
    keep = d < depth[yy, xx]
    if MAT[k] in OPAC and img.shape[2] == 4: keep &= c[:, 3] > 128     # 속눈썹·머리카락은 투명한 곳 빼고
    depth[yy[keep], xx[keep]] = d[keep]; front[yy[keep], xx[keep]] = c[keep, :3]
cv2.imwrite(os.path.join(out_d, "_확인_정면.png"), front)

# ---------- ② 얼굴 표지점 ----------
fm = mp.solutions.face_mesh.FaceMesh(static_image_mode=True, refine_landmarks=True, max_num_faces=1, min_detection_confidence=0.3)
def landmarks(bgr):
    r = fm.process(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB))
    if not r.multi_face_landmarks: return None
    h, w = bgr.shape[:2]
    return np.array([[l.x * w, l.y * h] for l in r.multi_face_landmarks[0].landmark])
photo = cv2.imread(photo_p)
LP = landmarks(photo)
bg = front.copy(); bg[np.isinf(depth)] = (200, 200, 200)
LR = landmarks(bg)
if LP is None or LR is None: sys.exit(f"얼굴 표지점을 못 찾음: 사진 {LP is not None}, 정면 그림 {LR is not None}")
LP, LR = LP[:468], LR[:468]
INNER_LIP_ = [78, 95, 88, 178, 87, 14, 317, 402, 318, 324, 308, 415, 310, 311, 312, 13, 82, 81, 80, 191]
# 사진에서 웃을 때 보이는 이·입속을 지움: 입 안쪽을 입술 색으로 메움 (모델 입은 다문 입이라 이가 입술에 하얀 줄로 남음)
mm = np.zeros(photo.shape[:2], np.uint8); cv2.fillPoly(mm, [LP[INNER_LIP_].astype(np.int32)], 255)
mm = cv2.dilate(mm, np.ones((3, 3), np.uint8))
ring = cv2.dilate(mm, np.ones((9, 9), np.uint8)) & ~mm
lipc = np.median(photo[ring > 0], 0)
photo = photo.copy(); photo[mm > 0] = lipc
sm = cv2.GaussianBlur(photo, (7, 7), 0); photo[mm > 0] = sm[mm > 0]
def edges_to_poly(conns):
    """MediaPipe 연결선 목록 → 순서대로 이은 다각형 점 번호"""
    nxt = {}
    for i, j in conns: nxt.setdefault(i, []).append(j); nxt.setdefault(j, []).append(i)
    start = next(iter(nxt)); poly = [start]; prev = None
    while True:
        cand = [n for n in nxt[poly[-1]] if n != prev]
        if not cand or cand[0] == start: break
        prev = poly[-1]; poly.append(cand[0])
        if len(poly) > 500: break
    return poly
FMs = mp.solutions.face_mesh
OVAL = edges_to_poly(FMs.FACEMESH_FACE_OVAL)
LEYE, REYE = edges_to_poly(FMs.FACEMESH_LEFT_EYE), edges_to_poly(FMs.FACEMESH_RIGHT_EYE)
INNER_LIP = [78, 95, 88, 178, 87, 14, 317, 402, 318, 324, 308, 415, 310, 311, 312, 13, 82, 81, 80, 191]
# 얼굴 모양 맞추기용(애니3D/얼굴모양맞추기.py): 사진 표지점을 모델 크기로 맞춘(닮음 변환) 목표 자리. 웃는 입·눈은 모양 대신 가운데 자리만 따라감
def sim_fit(A, B):        # A 를 B 에 맞추는 크기·회전·이동 (Umeyama)
    ma, mb = A.mean(0), B.mean(0); A0, B0 = A - ma, B - mb
    U, S_, Vt = np.linalg.svd(B0.T @ A0); R = U @ Vt
    if np.linalg.det(R) < 0: U[:, -1] *= -1; R = U @ Vt
    sc = S_.sum() / (A0 ** 2).sum(); return lambda P: (P - ma) @ (sc * R).T + mb
TGT = sim_fit(LP, LR)(LP)
lip_ids = sorted({i for c in FMs.FACEMESH_LIPS for i in c})
for ids in (LEYE, REYE, lip_ids):
    ids = list(ids); TGT[ids] = LR[ids] + (TGT[ids].mean(0) - LR[ids].mean(0))
toM = lambda P: np.stack([(P[:, 0] - RES / 2) / RES * SC + CX, (RES / 2 - P[:, 1]) / RES * SC + CZ], 1)
np.savez(os.path.join(out_d, "shape_lm.npz"), src=toM(LR), dst=toM(TGT), oval=toM(LR[OVAL]))
vis = bg.copy()
for x, y in LR: cv2.circle(vis, (int(x), int(y)), 2, (0, 255, 0), -1)
cv2.imwrite(os.path.join(out_d, "_확인_정면표지점.png"), vis)

# ---------- ③ 사진을 정면 그림 자리로 휘기 ----------
tf = PiecewiseAffineTransform(); tf.estimate(LR, LP)            # 정면 그림 자리 → 사진 자리
warped = warp(photo[..., ::-1] / 255.0, tf, output_shape=(RES, RES), order=1, mode="constant", cval=-1)
valid = warped[..., 0] >= 0
warped = (np.clip(warped, 0, 1)[..., ::-1] * 255).astype(np.uint8)

# 섞는 범위: 얼굴 윤곽 안 (위쪽 이마 일부 빼고), 눈 안·입 안 빼고, 경계는 부드럽게
face_w = LR[:, 0].max() - LR[:, 0].min()
mask = np.zeros((RES, RES), np.uint8)
ovc = LR[OVAL].mean(0); ovp = LR[OVAL].copy(); ovp[:, 0] = ovc[0] + (ovp[:, 0] - ovc[0]) * float(opt("--옆줄이기", "0.9"))   # 사진 얼굴 가장자리의 머리카락이 볼에 묻지 않게
cv2.fillPoly(mask, [ovp.astype(np.int32)], 255)
ytop, ybot = LR[OVAL, 1].min(), LR[OVAL, 1].max()
mask[: int(ytop + (ybot - ytop) * TOPCUT)] = 0
hole = np.zeros_like(mask)
cv2.fillPoly(hole, [LR[INNER_LIP].astype(np.int32)], 255)
for poly in (LEYE, REYE):                     # 눈: 위 눈꺼풀(쌍꺼풀 선까지)도 원래 그림 — 눈 감을 때 내려오는 꺼풀에 사진 속눈썹이 줄무늬로 늘어남
    P = LR[poly]; eh = P[:, 1].max() - P[:, 1].min(); ew = P[:, 0].max() - P[:, 0].min()
    Q = P.copy(); up = Q[:, 1] < P[:, 1].mean(); Q[up, 1] -= eh * float(opt("--눈꺼풀", "1.3"))
    Q[:, 0] = P[:, 0].mean() + (Q[:, 0] - P[:, 0].mean()) * 1.12
    cv2.fillPoly(hole, [cv2.convexHull(Q.astype(np.int32))], 255)
hole = cv2.dilate(hole, np.ones((5, 5), np.uint8))
lid = hole.copy(); cv2.fillPoly(lid, [LR[INNER_LIP].astype(np.int32)], 0)
for poly in (LEYE, REYE): cv2.fillPoly(lid, [LR[poly].astype(np.int32)], 0)
lid = cv2.GaussianBlur(cv2.dilate(lid, np.ones((9, 9), np.uint8)).astype(np.float32) / 255, (15, 15), 0)   # 눈꺼풀(원래 그림을 쓰는 곳): 화장 색을 피부색으로
f = max(3, int(face_w * FEATHER)) | 1
soft = cv2.GaussianBlur(cv2.erode(mask, np.ones((f, f), np.uint8)).astype(np.float32) / 255, (f * 2 + 1, f * 2 + 1), 0)
soft *= 1 - cv2.GaussianBlur(hole.astype(np.float32) / 255, (9, 9), 0)
soft *= valid
cv2.imwrite(os.path.join(out_d, "_확인_사진휨.png"), np.where(valid[..., None], warped, 128))

# ---------- ⑤ 피부색 맞춤: 볼 부분 Lab 평균을 비교해 원래 머리 그림 전체를 사진 피부색 쪽으로 ----------
cheek = (soft > 0.9)
lab_p = cv2.cvtColor(warped, cv2.COLOR_BGR2LAB).astype(np.float32)[cheek]
lab_r = cv2.cvtColor(front, cv2.COLOR_BGR2LAB).astype(np.float32)[cheek]
mp_, mr_ = np.median(lab_p, 0), np.median(lab_r, 0)
shift = (mp_ - mr_) * SKIN
print("피부색(Lab) 사진", mp_.round(1), "모델", mr_.round(1), "옮김", shift.round(1))

# ---------- ④ 얼굴 그림(UV)에 칠하기 ----------
tex = texs[HEAD].copy(); has_a = tex.shape[2] == 4
th, tw = tex.shape[:2]
lab = cv2.cvtColor(tex[..., :3], cv2.COLOR_BGR2LAB).astype(np.float32)
lab += shift
base = cv2.cvtColor(np.clip(lab, 0, 255).astype(np.uint8), cv2.COLOR_LAB2BGR).astype(np.float32)
lidw = np.zeros((th, tw)); acc = np.zeros((th, tw)); col = np.zeros((th, tw, 3))
FN = np.cross(XYZ[:, 1] - XYZ[:, 0], XYZ[:, 2] - XYZ[:, 0])            # 면 법선(넓이 무게)
key = np.round(XYZ.reshape(-1, 3) * 2000).astype(np.int64)             # 같은 자리 점끼리 법선을 평균 → 부드러운 법선(각진 경계 없앰)
_, inv = np.unique(key, axis=0, return_inverse=True); inv = inv.ravel()
vn = np.zeros((inv.max() + 1, 3)); np.add.at(vn, inv, np.repeat(FN, 3, axis=0))
vn /= np.linalg.norm(vn, axis=1, keepdims=True) + 1e-12
CN = vn[inv].reshape(-1, 3, 3)
for k in np.where(MAT == HEAD)[0]:
    if -CN[k, :, 1].max() < 0.15: continue
    ux, uy = UV[k, :, 0] * tw, (1 - UV[k, :, 1]) * th
    r = bary_raster(ux, uy, tw, th)
    if r is None: continue
    yy, xx, w0, w1, w2 = r
    P = w0[:, None] * XYZ[k, 0] + w1[:, None] * XYZ[k, 1] + w2[:, None] * XYZ[k, 2]
    sx, sy = to_px(P)
    ix, iy = np.clip(sx.astype(int), 0, RES - 1), np.clip(sy.astype(int), 0, RES - 1)
    seen = np.abs(P[:, 1] - depth[iy, ix]) < 0.004                # 앞에서 보이는 곳만 (머리카락·속눈썹에 가린 곳 제외)
    N = w0[:, None] * CN[k, 0] + w1[:, None] * CN[k, 1] + w2[:, None] * CN[k, 2]; N /= np.linalg.norm(N, axis=1, keepdims=True) + 1e-12
    ff = -N[:, 1]                                                  # 1 = 정면을 똑바로 봄
    down = np.clip(1 + (N[:, 2] + 0.35) * 2.5, 0, 1)                # 아래를 향한 곳(콧구멍 밑·턱 밑)은 사진 그림자가 늘어나므로 뺌
    wgt = soft[iy, ix] * np.clip((ff - 0.25) / 0.4, 0, 1) * down * seen
    c = cv2.remap(warped, sx.astype(np.float32).reshape(-1, 1), sy.astype(np.float32).reshape(-1, 1), cv2.INTER_LINEAR).reshape(-1, 3)
    acc[yy, xx] = wgt; col[yy, xx] = c
    lidw[yy, xx] = lid[iy, ix] * seen
# 그림 조각 가장자리에서 원래 색이 비치지 않게 칠한 곳을 3칸 넓힘
for _ in range(3):
    grow = (acc == 0)
    dil_a = cv2.dilate(acc, np.ones((3, 3)))
    dil_c = np.stack([cv2.dilate(col[..., i] * (acc > 0), np.ones((3, 3))) for i in range(3)], -1)
    acc = np.where(grow, dil_a * 0.999, acc); col = np.where(grow[..., None], dil_c, col)
lidw = cv2.GaussianBlur(cv2.dilate(lidw, np.ones((5, 5))), (9, 9), 0)
blab = cv2.cvtColor(np.clip(base, 0, 255).astype(np.uint8), cv2.COLOR_BGR2LAB).astype(np.float32)
blab[..., 1:] = blab[..., 1:] * (1 - lidw[..., None]) + mp_[1:] * lidw[..., None]        # 눈꺼풀 화장(보라·분홍) → 사진 피부의 색조
base = cv2.cvtColor(np.clip(blab, 0, 255).astype(np.uint8), cv2.COLOR_LAB2BGR).astype(np.float32)
outc = base * (1 - acc[..., None]) + col * acc[..., None]
BRT, SAT = float(opt("--밝기", "1.25")), float(opt("--채도", "1.0"))   # 얼굴 그림 전체를 고르게 밝게 (피부밝게.py 는 사진의 발그레한 볼을 피부로 못 잡아 분홍 얼룩이 남았음)
lab = cv2.cvtColor(np.clip(outc, 0, 255).astype(np.uint8), cv2.COLOR_BGR2LAB).astype(np.float32)
Lw = np.clip((lab[..., 0] - 50) / 60, 0, 1)                            # 어두운 머리카락·눈썹은 덜 밝힘
lab[..., 0] = np.minimum(lab[..., 0] * (1 + (BRT - 1) * Lw), 250 - (250 - lab[..., 0]) * 0.15)
lab[..., 1:] = 128 + (lab[..., 1:] - 128) * (1 - (1 - SAT) * Lw[..., None])
outc = cv2.cvtColor(np.clip(lab, 0, 255).astype(np.uint8), cv2.COLOR_LAB2BGR)
res = tex.copy(); res[..., :3] = np.clip(outc, 0, 255).astype(np.uint8)
name = os.path.basename(info["materials"][HEAD]["color"])
Image.fromarray(res[..., [2, 1, 0, 3]] if has_a else res[..., ::-1].copy()).save(os.path.join(out_d, name))
cv2.imwrite(os.path.join(out_d, "_확인_얼굴그림.png"), cv2.resize(res[..., :3], (1024, 1024)))
print("→", os.path.join(out_d, name), "칠한 점", int((acc > 0.5).sum()))
