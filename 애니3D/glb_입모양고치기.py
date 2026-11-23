"""GLB 사람 모델의 입 모양 키(MouthOpen·MouthWide·MouthRound)를 '그려진 입술' 자리에 맞춰 새로 만듦
   AI 로 만든 3D 사람은 겉면 그림(텍스처)의 입술과 실제 모양(메시)의 입 자리가 어긋나 있고, 자동으로 만든 입 모양 키가
   코 밑을 잡아당겨 코가 길게 늘어나기도 함 (2026-11-22 남자 아나운서: 그려진 입술 0.704, 키가 움직이는 곳 0.73 = 코 밑).
   방법: 얼굴 가운데 줄의 점마다 겉면 그림 색을 읽어 '입술 사이 어두운 선'(입술선)을 x 마다 찾고, 그 선을 기준으로
     · MouthOpen  : 입술선 아래(아랫입술~턱)를 아래·조금 뒤로 (아랫입술이 가장 많이, 턱 쪽으로 갈수록 덜). 윗입술은 아주 조금 위로
                    → 입술선 걸친 면이 늘어나며 입술 사이 어두운 색이 벌어진 입처럼 보임 (메시에 입 안이 없어도)
     · MouthWide  : 입꼬리를 옆으로·조금 위로
     · MouthRound : 입술을 가운데로 모으고 앞으로 내밈
     · Blink 등 다른 키는 그대로
   사용: python 애니3D/glb_입모양고치기.py <입력.glb> <결과.glb> [--벌림 0.012] [--확인 <그림.png>] [--입술칠]
     --입술칠: 입술선 바로 위·아래 띠를 겉면 그림에서 아랫입술 색으로 칠함 (입을 벌리면 윗입술 안쪽이 살색·흰 점으로 보일 때, 여자 아나운서 2026-11-23)
   (모양 키 이름이 MouthOpen/MouthWide/MouthRound 인 모델. 정점 수·순서는 그대로라 리깅과 함께 써도 됨)"""
import io, json, struct, sys
import numpy as np
from PIL import Image

a = sys.argv[1:]
OPEN = 0.012; check = None; PAINT = False
if "--입술칠" in a: a.remove("--입술칠"); PAINT = True
if "--벌림" in a: i = a.index("--벌림"); OPEN = float(a[i + 1]); del a[i:i + 2]
if "--확인" in a: i = a.index("--확인"); check = a[i + 1]; del a[i:i + 2]
src, dst = a
raw = open(src, "rb").read()
n = struct.unpack("<I", raw[12:16])[0]; j = json.loads(raw[20:20 + n]); bin0 = 20 + n + 8
binlen = struct.unpack("<I", raw[20 + n:24 + n])[0]; BIN = raw[bin0:bin0 + binlen]
views = [BIN[v.get("byteOffset", 0):v.get("byteOffset", 0) + v["byteLength"]] for v in j["bufferViews"]]
COMP = {5126: np.float32, 5125: np.uint32, 5123: np.uint16, 5121: np.uint8}; K = {"VEC2": 2, "VEC3": 3, "VEC4": 4, "SCALAR": 1}


def get(i):
    """접근자 자료를 꽉 찬 배열로 (sparse = 움직이는 점만 적어 둔 모양 키도 펼침)"""
    ac = j["accessors"][i]; dt = np.dtype(COMP[ac["componentType"]]); k = K[ac["type"]]
    if "bufferView" in ac: out = np.frombuffer(views[ac["bufferView"]], dt, ac["count"] * k, ac.get("byteOffset", 0)).reshape(-1, k).astype(float)
    else: out = np.zeros((ac["count"], k))
    sp = ac.get("sparse")
    if sp:
        si = np.frombuffer(views[sp["indices"]["bufferView"]], np.dtype(COMP[sp["indices"]["componentType"]]), sp["count"], sp["indices"].get("byteOffset", 0))
        sv = np.frombuffer(views[sp["values"]["bufferView"]], dt, sp["count"] * k, sp["values"].get("byteOffset", 0)).reshape(-1, k)
        out[si.astype(int)] = sv
    return out


def put(i, arr):
    ac = j["accessors"][i]
    if "sparse" in ac or "bufferView" not in ac:      # 꽉 찬 자료로 새로 씀
        ac.pop("sparse", None); views.append(b""); j["bufferViews"].append({"buffer": 0, "byteLength": 0}); ac["bufferView"] = len(j["bufferViews"]) - 1; ac.pop("byteOffset", None)
    assert ac.get("byteOffset", 0) == 0
    views[ac["bufferView"]] = np.asarray(arr, np.float32).tobytes()
    ac["min"] = [float(v) for v in arr.min(0)]; ac["max"] = [float(v) for v in arr.max(0)]


mesh = next(m for m in j["meshes"] if m.get("extras", {}).get("targetNames"))
names = mesh["extras"]["targetNames"]; pr = mesh["primitives"][0]
P = get(pr["attributes"]["POSITION"]); UV = get(pr["attributes"]["TEXCOORD_0"])
mat = j["materials"][pr["material"]]; img = j["images"][j["textures"][mat["pbrMetallicRoughness"]["baseColorTexture"]["index"]]["source"]]
TEX = np.asarray(Image.open(io.BytesIO(views[img["bufferView"]])).convert("RGB")).astype(float)
th, tw = TEX.shape[:2]


def color(m):
    u = UV[m]; px = np.clip((u[:, 0] * tw).astype(int), 0, tw - 1); py = np.clip((u[:, 1] * th).astype(int), 0, th - 1)
    return TEX[py, px]


# 얼굴 앞쪽·코끝 높이: 가운데 줄(x≈0)에서 가장 앞으로 나온 곳
mid = (np.abs(P[:, 0]) < 0.006)
head_top = P[:, 1].max(); H_ = head_top - P[:, 1].min()
face = mid & (P[:, 1] > head_top - 0.2 * H_) & (P[:, 1] < head_top - 0.06 * H_)
nose_y = P[face][np.argmax(P[face][:, 2]), 1]
# 입술 = 코끝 아래 0.5~4cm 에서 가장 붉고 어두운 줄 (가운데에서 찾고, 옆으로 1mm 칸마다 따라감)
def lip_y(xc, around, span=0.012):
    best = None
    for yy in np.arange(around - span, around + span, 0.001):
        m = (np.abs(P[:, 0] - xc) < 0.003) & (np.abs(P[:, 1] - yy) < 0.001) & (P[:, 2] > P[face][:, 2].max() - 0.06)
        if m.sum() < 2: continue
        c = color(m).mean(0); score = (c[0] - c[1]) - 0.6 * c.mean()      # 붉고 어두울수록
        if best is None or score > best[1]: best = (yy, score, c)
    return best
c0 = lip_y(0.0, nose_y - 0.025, 0.02)
assert c0, "입술을 못 찾음"
LY0 = c0[0]
xs, ys, red = [0.0], [LY0], [c0[2][0] - c0[2][1]]
for sgn in (1, -1):
    yy = LY0
    for xx in np.arange(0.002, 0.05, 0.002):
        r = lip_y(sgn * xx, yy, 0.005)
        if not r: break
        yy = r[0]; xs.append(sgn * xx); ys.append(yy); red.append(r[2][0] - r[2][1])
o = np.argsort(xs); xs, ys, red = np.array(xs)[o], np.array(ys)[o], np.array(red)[o]
skin_red = color(mid & (np.abs(P[:, 1] - (nose_y + 0.03)) < 0.002)).mean(0); skin_red = skin_red[0] - skin_red[1]
lipm = red > skin_red + 0.5 * (red.max() - skin_red)                  # 붉은 입술이 있는 x 범위 = 입 너비
HW = max(0.018, float(np.abs(xs[lipm]).max()))
HWP = max(0.016, float(xs[lipm & (xs > 0)].max())) if (lipm & (xs > 0)).any() else HW      # 왼·오른쪽 입꼬리를 따로 (얼굴이 조금 비뚤어도 입꼬리 밖으로 틈이 나가지 않게)
HWN = max(0.016, float(-xs[lipm & (xs < 0)].min())) if (lipm & (xs < 0)).any() else HW
XC = (HWP - HWN) / 2; HWH = (HWP + HWN) / 2          # 입 가운데·반너비 = 그려진 두 입꼬리의 가운데·반 (얼굴이 x=0 에서 몇 mm 비켜 있기도 함, 남자 아나운서 -7mm)
HWP, HWN = max(HWP, 0.8 * HW), max(HWN, 0.8 * HW)                           # 한쪽만 너무 좁게 재지면(그늘 탓) 입이 비뚤게 벌어지므로 80% 아래로는 안 줄임
ys = np.convolve(np.pad(ys, 2, mode="edge"), np.ones(5) / 5, "valid")         # 입술선을 살짝 매끈하게
print(f"코끝 높이 {nose_y:.3f} · 입술선 가운데 {LY0:.3f} (코끝 아래 {100 * (nose_y - LY0):.1f}cm) · 입 가운데 x {100 * XC:+.1f}cm · 반너비 {100 * HWH:.1f}cm")


def ly(x): return np.interp(x, xs, ys)


HWS = HWH


def hw(x): return np.full(np.shape(x), HWS)      # 입꼬리까지 거리 — 왼·오른쪽 같게 (따로 재면 한쪽만 크게 벌어져 비뚤어 보였음, 사용자 2026-11-23)


def sstep(t): t = np.clip(t, 0, 1); return t * t * (3 - 2 * t)


x, y, z = P[:, 0], P[:, 1], P[:, 2]
front = z > P[face][:, 2].max() - 0.07                                # 얼굴 앞쪽(뒤통수·목 뒤 아님)

# ── 코와 입 사이 두툼한 곳 펴기 (사용자 2026-11-22: "코와 입 사이 두툼한 것 수정") ──
#   메시의 원래 입술 볼록함이 그려진 입술보다 위(코 밑)에 있어 콧수염 자리가 부풀어 보임.
#   윗입술 위(입술선 + 4mm) ~ 코 밑(그려진 콧구멍 바로 아래) 띠에서, 위·아래 끝을 잇는 부드러운 곡면보다 앞으로 나온 만큼만 뒤로 밂
def nostril_y():
    best = None
    for yy in np.arange(LY0 + 0.012, LY0 + 0.05, 0.001):
        m = front & (np.abs(np.abs(x) - 0.009) < 0.004) & (np.abs(y - yy) < 0.001)
        if m.sum() < 3: continue
        v = color(m).mean()
        if best is None or v < best[1]: best = (yy, v)
    return best[0]
Y_HI = nostril_y() - 0.003; Y_LO = LY0 + 0.004
def row_z(yy):
    """그 높이에서 x 2mm 칸마다 가장 앞 z (겉 살)"""
    gx = np.arange(-0.07, 0.0701, 0.002); gz = np.full(len(gx), np.nan)
    band = front & (np.abs(y - yy) < 0.0015)
    for k_, xx in enumerate(gx):
        m = band & (np.abs(x - xx) < 0.0015)
        if m.any(): gz[k_] = z[m].max()
    ok_ = ~np.isnan(gz); return gx, np.interp(gx, gx[ok_], gz[ok_])
gx, zlo = row_z(Y_LO); _, zhi = row_z(Y_HI)
reg = front & (y > Y_LO) & (y < Y_HI) & (np.abs(x - XC) < HW * 2.6)
s_ = np.clip((y - Y_LO) / (Y_HI - Y_LO), 0, 1)
zt = np.interp(x, gx, zlo) + (np.interp(x, gx, zhi) - np.interp(x, gx, zlo)) * s_ ** 1.4 - 0.0015 * np.sin(np.pi * s_) * (1 - sstep((np.abs(x - XC) - 0.006) / 0.01))   # 가운데는 살짝 오목(인중)
wgt = reg * (1 - sstep((np.abs(x - XC) - HW * 1.2) / (HW * 1.4))) * sstep(np.minimum(y - Y_LO, Y_HI - y) / 0.003 + 0.25)
dz = np.where(reg, np.maximum(0, z - zt), 0) * wgt
# 미는 양을 이웃 점끼리 여러 번 고르게 (점마다 들쭉날쭉 밀면 면이 울퉁불퉁해져 얼룩 그늘이 생겼음)
#   같은 자리 점(겉면 그림 이음매로 갈라진 점)은 하나로 묶어 함께 움직임
_Ia = pr["indices"]; _I = np.frombuffer(views[j["accessors"][_Ia]["bufferView"]], np.dtype(COMP[j["accessors"][_Ia]["componentType"]]),
                                       j["accessors"][_Ia]["count"]).reshape(-1, 3).astype(np.int64)
_, gid = np.unique(np.round(P * 2e4).astype(np.int64), axis=0, return_inverse=True); gid = gid.reshape(-1)
near_mouth = front & (np.abs(x - XC) < HW * 3.0) & (y > LY0 - 0.01) & (y < Y_HI + 0.015)
tri_m = near_mouth[_I].all(1); E = np.concatenate([_I[tri_m][:, [0, 1]], _I[tri_m][:, [1, 2]], _I[tri_m][:, [2, 0]]])
Eg = gid[E]; ng = gid.max() + 1
dzg = np.zeros(ng); np.maximum.at(dzg, gid, dz)
keep = np.zeros(ng, bool); keep[gid[~near_mouth]] = True                  # 바깥 점은 그대로(0)
lock_lo = np.zeros(ng, bool); lock_lo[gid[near_mouth & (y <= Y_LO)]] = True  # 입술 쪽은 움직이지 않음
for _ in range(25):
    sm = np.zeros(ng); cnt = np.zeros(ng)
    np.add.at(sm, Eg[:, 0], dzg[Eg[:, 1]]); np.add.at(cnt, Eg[:, 0], 1)
    np.add.at(sm, Eg[:, 1], dzg[Eg[:, 0]]); np.add.at(cnt, Eg[:, 1], 1)
    avg = np.where(cnt > 0, sm / np.maximum(cnt, 1), dzg)
    dzg = np.where(keep | lock_lo, dzg, 0.5 * dzg + 0.5 * avg)
raw_max = dz.max(); dz = dzg[gid]
if dz.max() > 0: dz = np.minimum(dz * min(2.0, 0.8 * raw_max / dz.max()), np.maximum(0, z - (zt - 0.002)) + dz * 0)   # 고르게 하며 줄어든 양을 되살림(원래 미는 양의 80%)
P_ORIG = P.copy(); P = P.copy(); P[:, 2] -= dz; z = P[:, 2]
moved_n = int((dz > 1e-4).sum())
print(f"  코 밑 두툼한 곳: 높이 {Y_LO:.3f}~{Y_HI:.3f}, 점 {moved_n}개를 최대 {dz.max() * 1000:.1f}mm 뒤로")
FLAT_DZ = dz
lat = np.clip(1 - (np.abs(x - XC) / (hw(x) * 0.86)) ** 2, 0, 1) ** 0.75          # 타원 모양: 가운데에서 입꼬리까지 고르게 줄어듦 (평평하다 갑자기 줄면 아랫입술 가장자리가 꺾여 계단처럼 보였음)
lat_chin = 1 - sstep((np.abs(x - XC) - HW) / 0.035)                        # 턱은 조금 더 넓게
dy = y - ly(x)                                                        # 입술선에서 위(+)·아래(-)
chin_y = LY0 - 0.045
# 벌림: 아랫입술 1 → 턱 끝 0.55 → 목 0
below = (dy < 0) & front
f_low = np.where(dy < 0, np.where(y > chin_y, 1 - 0.45 * sstep(-dy / (LY0 - chin_y)), 0.55 * (1 - sstep((chin_y - y) / 0.02))), 0)
f_low *= np.maximum(lat, 0.55 * lat_chin * sstep(-dy / 0.015)) * front      # 입꼬리 옆 살은 입술선 바로 아래에선 안 움직임
f_up = np.where((dy >= 0) & front, np.exp(-dy / 0.008) * lat, 0)     # 윗입술도 조금 위로 (아랫입술만 내려가면 균형이 안 맞음)
D_open = np.zeros_like(P)
D_open[:, 1] = -0.85 * OPEN * f_low + 0.32 * OPEN * f_up
D_open[:, 2] = -0.35 * OPEN * f_low
# 옆으로: 입술선 ±1.2cm 안, 입꼬리 쪽일수록
near = np.exp(-(dy / 0.008) ** 2) * front
side = sstep(np.abs(x - XC) / HW) * (1 - sstep((np.abs(x - XC) - HW) / 0.02))
D_wide = np.zeros_like(P)
D_wide[:, 0] = np.sign(x - XC) * 0.006 * side * near
D_wide[:, 1] = 0.0015 * side * near
# 오므림: 입술을 가운데로 모으고 앞으로
lipzone = np.exp(-(dy / 0.010) ** 2) * front * (1 - sstep((np.abs(x - XC) - HW) / 0.02))
D_round = np.zeros_like(P)
D_round[:, 0] = -np.sign(x - XC) * 0.0055 * sstep(np.abs(x - XC) / HW) * lipzone
D_round[:, 2] = 0.005 * lipzone * lat
D_round[:, 1] = -0.002 * np.where(dy < 0, lipzone, 0)                 # 아랫입술 조금 내려 'O'
new = {"MouthOpen": D_open, "MouthWide": D_wide, "MouthRound": D_round}
for t_, nm in enumerate(names):
    if nm in new:
        put(pr["targets"][t_]["POSITION"], new[nm]); print(f"  {nm}: 새로 만듦 (움직이는 점 {(np.linalg.norm(new[nm], axis=1) > 1e-4).sum()}개)")
# 예전 입 안 메시(이름에 Mouth 가 든 다른 메시)는 엉뚱한 자리(코 밑)에 있어 장면에서 뺌 — 새 입 안을 아래에서 더함
sc_nodes = j["scenes"][j.get("scene", 0)]["nodes"]
for ni_, nd_ in enumerate(j["nodes"]):
    if "mesh" in nd_ and j["meshes"][nd_["mesh"]] is not mesh and "mouth" in j["meshes"][nd_["mesh"]].get("name", "").lower() and ni_ in sc_nodes:
        sc_nodes.remove(ni_); print(f"  예전 입 안 '{j['meshes'][nd_['mesh']]['name']}' 을 장면에서 뺌")
# 다른 메시(입 안 등)에도 같은 이름 키가 있으면 0 으로 (어긋난 자리에서 움직이지 않게)
for m in j["meshes"]:
    if m is mesh: continue
    tn = m.get("extras", {}).get("targetNames", [])
    for p_ in m["primitives"]:
        for t_, nm in enumerate(tn):
            if nm in new and t_ < len(p_.get("targets", [])): put(p_["targets"][t_]["POSITION"], np.zeros((j["accessors"][p_["targets"][t_]["POSITION"]]["count"], 3)))

# ── 입 틈: 입꼬리 사이 입술선을 가로지르는 삼각형을 없앰 → 벌리면 실제로 갈라짐 (닫으면 얇은 어두운 선) ──
I_acc = pr["indices"]; I = np.frombuffer(views[j["accessors"][I_acc]["bufferView"]], np.dtype(COMP[j["accessors"][I_acc]["componentType"]]),
                                          j["accessors"][I_acc]["count"]).reshape(-1, 3).copy()
zone = front & (np.abs(x - XC) < hw(x) * 0.88) & (np.abs(dy) < 0.004)      # 입술선에서 4mm 안 점만 (멀리 있는 점을 선으로 끌면 옆 삼각형이 뒤집혀 배경이 비쳤음)
side_ = np.where(dy < 0, 1, 2) * zone
tri_s = side_[I]
cross = (tri_s == 1).any(1) & (tri_s == 2).any(1) & (tri_s > 0).all(1)      # 세 점 모두 틈 범위 안일 때만 (입꼬리에 구멍이 남지 않게)
# 틈 가장자리 점을 입술선 위로 모음 → 다물면 한 줄로 딱 닫힘 (들쭉날쭉한 가장자리를 곧게, 가장자리 점은 몇 mm 만 움직임)
edge = np.unique(I[cross].reshape(-1)); edge = edge[zone[edge]]
P2 = P.copy(); P2[edge, 1] = ly(x[edge])
# 같은 자리에 겹친 점(겉면 그림 이음매로 갈라진 점)은 함께 끌어옴 — 하나만 끌면 틈이 벌어져 흰 V 자처럼 보였음 (여자 아나운서 2026-11-23)
_, gsnap = np.unique(np.round(P * 2e4).astype(np.int64), axis=0, return_inverse=True); gsnap = gsnap.reshape(-1)
same = np.isin(gsnap, gsnap[edge]) & ~np.isin(np.arange(len(P)), edge)
gy = np.zeros(gsnap.max() + 1); gy[gsnap[edge]] = P2[edge, 1]
P2[same, 1] = gy[gsnap[same]]
print(f"  같은 자리 겹친 점 {int(same.sum())}개도 함께 입술선으로")
put(pr["attributes"]["POSITION"], P2)
# 펴거나 모은 점 둘레의 면 방향(법선)을 다시 계산 → 예전 볼록한 그늘이 남지 않게
if "NORMAL" in pr["attributes"]:
    NR = get(pr["attributes"]["NORMAL"])
    Ifull = I
    def vnorm(Pq):      # 같은 자리 점(겉면 그림 이음매로 갈라진 점)을 묶어 면 방향을 더함
        v0, v1, v2 = Pq[Ifull[:, 0]], Pq[Ifull[:, 1]], Pq[Ifull[:, 2]]
        fn = np.cross(v1 - v0, v2 - v0); a_ = np.zeros_like(Pq)
        for c_ in range(3): np.add.at(a_, Ifull[:, c_], fn)
        _, inv = np.unique(np.round(Pq * 2e4).astype(np.int64), axis=0, return_inverse=True)
        g_ = np.zeros((inv.max() + 1, 3)); np.add.at(g_, inv.reshape(-1), a_); a_ = g_[inv.reshape(-1)]
        return a_ / np.maximum(np.linalg.norm(a_, axis=1, keepdims=True), 1e-12)
    chg = (FLAT_DZ > 1e-5) | np.isin(np.arange(len(P2)), edge)
    near_chg = np.zeros(len(P2), bool); tri_c = chg[Ifull].any(1); near_chg[np.unique(Ifull[tri_c])] = True
    # 원래 면 방향은 그대로 두고, 펴기 전·후 계산값의 '차이'만 더함 (원래의 매끈한 그늘을 지키면서 볼록한 그늘만 없앰)
    sub = np.where(near_chg)[0]
    before, after = vnorm(P_ORIG), vnorm(P2)
    # 펴진 곳: 새 면 방향을 이웃끼리 3번 고르게 → 원래 값과 '펴진 정도'에 따라 섞음 (가장자리는 원래 그대로, 얼룩·경계선 없게)
    _, gidn = np.unique(np.round(P2 * 2e4).astype(np.int64), axis=0, return_inverse=True); gidn = gidn.reshape(-1)
    okn = Ifull[:, 0] != Ifull[:, 1]
    En = gidn[np.concatenate([Ifull[okn][:, [0, 1]], Ifull[okn][:, [1, 2]], Ifull[okn][:, [2, 0]]])]
    ngn = gidn.max() + 1; an = np.zeros((ngn, 3)); np.add.at(an, gidn, after)
    for _ in range(3):
        sm_ = np.zeros((ngn, 3)); np.add.at(sm_, En[:, 0], an[En[:, 1]]); np.add.at(sm_, En[:, 1], an[En[:, 0]]); an = 0.5 * an + 0.5 * sm_ / np.maximum(np.linalg.norm(sm_, axis=1, keepdims=True), 1e-12)
    an /= np.maximum(np.linalg.norm(an, axis=1, keepdims=True), 1e-12)
    mix = np.clip(FLAT_DZ / 0.0015, 0, 1)[sub][:, None]
    nn = (1 - mix) * (NR[sub] + (after[sub] - before[sub])) + mix * an[gidn[sub]]; nn /= np.maximum(np.linalg.norm(nn, axis=1, keepdims=True), 1e-12)
    NR[sub] = nn; put(pr["attributes"]["NORMAL"], NR)
    print(f"  면 방향 다시 계산: 점 {int(near_chg.sum())}개")
I[cross] = I[cross][:, :1]
views[j["accessors"][I_acc]["bufferView"]] = I.astype(np.dtype(COMP[j["accessors"][I_acc]["componentType"]])).tobytes()
print(f"  입 틈: 입술선을 가로지르는 삼각형 {int(cross.sum())}개 없앰")
# 입 모양 움직임을 이웃 점끼리 고르게 (가장자리가 톱니처럼 들쭉날쭉하지 않고 매끈한 곡선) — 틈 낸 뒤의 이웃(윗·아랫입술은 서로 이웃 아님)
_, gid2 = np.unique(np.round(P * 2e4).astype(np.int64), axis=0, return_inverse=True); gid2 = gid2.reshape(-1)
mz = front & (np.abs(x - XC) < HW * 1.6) & (np.abs(dy) < 0.05)
ok_t = (I[:, 0] != I[:, 1]) & mz[I].all(1)
E2 = gid2[np.concatenate([I[ok_t][:, [0, 1]], I[ok_t][:, [1, 2]], I[ok_t][:, [2, 0]]])]
E2 = E2[E2[:, 0] != E2[:, 1]]; ng2 = gid2.max() + 1
inside = np.zeros(ng2, bool); inside[gid2[mz]] = True; inside[gid2[~mz]] = False
for nm_, D_ in new.items():
    dg = np.zeros((ng2, 3)); cnt_ = np.zeros(ng2); np.add.at(dg, gid2, D_); np.add.at(cnt_, gid2, 1); dg /= np.maximum(cnt_, 1)[:, None]
    for _ in range(8):
        sm = np.zeros((ng2, 3)); c_ = np.zeros(ng2)
        np.add.at(sm, E2[:, 0], dg[E2[:, 1]]); np.add.at(c_, E2[:, 0], 1)
        np.add.at(sm, E2[:, 1], dg[E2[:, 0]]); np.add.at(c_, E2[:, 1], 1)
        avg = np.where(c_[:, None] > 0, sm / np.maximum(c_, 1)[:, None], dg)
        dg = np.where(inside[:, None], 0.5 * dg + 0.5 * avg, dg)
    D_[:] = dg[gid2]
# 틈 가장자리(윗·아랫입술 따로)는 왼→오 차례로 늘어놓고 움직임을 7칸 평균 → 벌렸을 때 가장자리가 계단·톱니 없이 매끈한 곡선 (사용자 2026-11-23)
for side_m in (dy[edge] >= 0, dy[edge] < 0):
    ids = edge[side_m]
    if len(ids) < 5: continue
    ids = ids[np.argsort(x[ids])]
    for D_ in new.values():
        v_ = D_[ids]; k_ = 7; pad = np.pad(v_, ((k_ // 2, k_ // 2), (0, 0)), mode="edge")
        sm_ = np.stack([np.convolve(pad[:, c_], np.ones(k_) / k_, "valid") for c_ in range(3)], 1)
        D_[ids] = sm_
        same_ = np.isin(gid2, gid2[ids]) & ~np.isin(np.arange(len(D_)), ids)          # 같은 자리 겹친 점도 같게
        gv = np.zeros((gid2.max() + 1, 3)); gv[gid2[ids]] = sm_; D_[same_] = gv[gid2[same_]]
for t_, nm in enumerate(names):
    if nm in new: put(pr["targets"][t_]["POSITION"], new[nm])
print("  입 모양 움직임을 이웃끼리 고르게 (8번) + 입술 가장자리는 왼→오 7칸 평균")

# ── 입 안: 입술 바로 뒤에 어두운 둥근 면(입 안) + 윗니 띠 — 머리 뼈를 따라감 ──
lip_z = float(np.median(z[front & (np.abs(x - XC) < 0.01) & (np.abs(dy) < 0.004)]))
head_j = None
for k_, nd_i in enumerate(j["skins"][0]["joints"]):
    if j["nodes"][nd_i].get("name") == "Head": head_j = k_
def add_mesh(name, pos, idx, color, open_disp=None, targets=None):
    """새 메시(머리 뼈 100%)를 GLB 에 붙임. open_disp = MouthOpen 모양 키(입을 벌릴 때 점마다 움직임)"""
    nrm = np.zeros_like(pos); nrm[:, 2] = 1
    def acc_(arr, ctype, typ, target=None, mm=False):
        views.append(arr.tobytes()); bv = {"buffer": 0, "byteLength": len(arr.tobytes())}
        if target: bv["target"] = target
        j["bufferViews"].append(bv)
        ac = {"bufferView": len(j["bufferViews"]) - 1, "componentType": ctype, "count": len(arr), "type": typ}
        if mm: ac["min"] = [float(v) for v in arr.min(0)]; ac["max"] = [float(v) for v in arr.max(0)]
        j["accessors"].append(ac); return len(j["accessors"]) - 1
    jn = np.zeros((len(pos), 4), np.uint8); jn[:, 0] = head_j
    wt = np.zeros((len(pos), 4), np.float32); wt[:, 0] = 1
    prim = {"attributes": {"POSITION": acc_(pos.astype(np.float32), 5126, "VEC3", 34962, True), "NORMAL": acc_(nrm.astype(np.float32), 5126, "VEC3", 34962),
                           "JOINTS_0": acc_(jn, 5121, "VEC4", 34962), "WEIGHTS_0": acc_(wt, 5126, "VEC4", 34962)},
            "indices": acc_(idx.astype(np.uint32).reshape(-1), 5125, "SCALAR", 34963), "material": len(j["materials"])}
    j["materials"].append({"name": name, "doubleSided": True, "pbrMetallicRoughness": {"baseColorFactor": color, "metallicFactor": 0, "roughnessFactor": 0.8}})
    m_ = {"name": name, "primitives": [prim]}
    if open_disp is not None: targets = {"MouthOpen": open_disp}
    if targets:                        # 입 모양 키 (얼굴과 같은 이름 → 같이 움직임)
        prim["targets"] = [{"POSITION": acc_(np.asarray(d_, np.float32), 5126, "VEC3", 34962, True)} for d_ in targets.values()]
        m_["extras"] = {"targetNames": list(targets)}; m_["weights"] = [0.0] * len(targets)
    j["meshes"].append(m_)
    j["nodes"].append({"name": name, "mesh": len(j["meshes"]) - 1, "skin": 0})
    j["scenes"][j.get("scene", 0)]["nodes"].append(len(j["nodes"]) - 1)
def bowl(cx, cy, cz, rx, ry, rz, nu=24, nv=10):
    """앞이 열린 반 타원 그릇 (안쪽이 앞을 봄)"""
    pts, idx = [], []
    for iv in range(nv + 1):
        th = np.pi / 2 * iv / nv
        for iu in range(nu + 1):
            ph = np.pi * 2 * iu / nu
            pts.append([cx + rx * np.sin(th) * np.cos(ph), cy + ry * np.sin(th) * np.sin(ph), cz - rz * np.cos(th)])
    for iv in range(nv):
        for iu in range(nu):
            a_ = iv * (nu + 1) + iu; b_ = a_ + nu + 1
            idx += [[a_, a_ + 1, b_], [a_ + 1, b_ + 1, b_]]
    return np.array(pts), np.array(idx)
if head_j is not None:
    # 입 안 = 입 틈 가장자리 점들에 그대로 붙은 '주머니' — 입술과 똑같이 움직여 틈·테두리가 생기지 않음
    #   윗입술 가장자리(왼→오) + 아랫입술 가장자리(오→왼) 고리 → 안쪽으로 작아지며 들어가는 고리 3개 → 맨 안 가운데 점
    def uniq(ids):
        _, first = np.unique(gid2[ids], return_index=True); return ids[np.sort(first)]
    U = uniq(edge[dy[edge] >= 0]); L = uniq(edge[dy[edge] < 0])
    U = U[np.argsort(x[U])]; L = L[np.argsort(-x[L])]
    ring = np.concatenate([U, L]); n_r = len(ring)
    R0 = P2[ring]; ctr = np.array([XC, LY0, lip_z])
    Ds = {nm_: new[nm_][ring] for nm_ in new}
    pts = [R0]; tg = {nm_: [Ds[nm_]] for nm_ in new}
    for sc_, dd_, w_ in ((0.88, 0.004, 0.9), (0.65, 0.010, 0.7), (0.35, 0.016, 0.45)):
        q_ = ctr + (R0 - ctr) * [sc_, sc_, 0]; q_[:, 2] = R0[:, 2] - dd_ - (1 - sc_) * 0.004
        pts.append(q_)
        for nm_ in new: tg[nm_].append(Ds[nm_] * w_)
    back = np.array([[XC, LY0, lip_z - 0.022]]); pts.append(back)
    for nm_ in new: tg[nm_].append(np.mean(Ds[nm_], 0, keepdims=True) * 0.3)
    bp = np.concatenate(pts); bi = []
    for r_ in range(3):
        for k_ in range(n_r):
            a_ = r_ * n_r + k_; b_ = r_ * n_r + (k_ + 1) % n_r
            bi += [[a_, b_, a_ + n_r], [b_, b_ + n_r, a_ + n_r]]
    cidx = len(bp) - 1
    for k_ in range(n_r): bi += [[3 * n_r + k_, 3 * n_r + (k_ + 1) % n_r, cidx]]
    add_mesh("Mouth_Inside", bp, np.array(bi), [0.26, 0.07, 0.07, 1.0], targets={nm_: np.concatenate(tg[nm_]) for nm_ in new})
    print(f"  입 안 주머니: 입술 가장자리 점 {n_r}개(윗 {len(U)}·아래 {len(L)})에 붙임")
    # 이는 넣지 않음 (사용자 2026-11-23: '이빨은 없애줘' — 단순한 흰 띠라 어색했음)
    print(f"  입 안 주머니 더함 (이 없음) (입술 앞면 z {lip_z:.3f})")

if PAINT:     # 입술선 둘레 띠를 아랫입술 색으로 (겉면 그림에서 삼각형을 칠하고 가장자리는 흐리게)
    from PIL import ImageDraw, ImageFilter
    ax_ = np.abs(x - XC)
    samp = front & (ax_ < 0.012) & (dy < -0.0025) & (dy > -0.0055)
    lipc = np.median(color(samp), 0) * 0.97
    wv = np.where((dy > -0.0035) & (dy < 0.0035) & front, np.where(dy >= 0, 1 - sstep((dy - 0.0012) / 0.0023), 1 - sstep((-dy - 0.002) / 0.0015)), 0) * (1 - sstep((ax_ - hw(x) * 0.78) / (hw(x) * 0.2)))      # 윗입술 안쪽 + 아랫입술 가장자리 3mm, 입꼬리 쪽으로 옅어짐
    alpha = Image.new("L", (tw, th), 0); da = ImageDraw.Draw(alpha)
    for t3 in I:
        if t3[0] == t3[1]: continue
        w3 = wv[t3]
        if w3.max() <= 0.02: continue
        uv = [(float(UV[k_, 0] * tw), float(UV[k_, 1] * th)) for k_ in t3]
        us_, vs_ = [q_[0] for q_ in uv], [q_[1] for q_ in uv]
        if max(us_) - min(us_) > 30 or max(vs_) - min(vs_) > 30: continue       # 겉면 그림 이음매를 건너는 큰 삼각형은 칠하지 않음 (볼까지 줄무늬로 번졌음)
        da.polygon(uv, fill=int(255 * 0.9 * w3.mean()))
    al = np.asarray(alpha.filter(ImageFilter.GaussianBlur(2)), float)[:, :, None] / 255
    newtex = TEX * (1 - al) + lipc[None, None, :] * al
    bio = io.BytesIO(); Image.fromarray(np.clip(newtex, 0, 255).astype(np.uint8)).save(bio, "JPEG" if img.get("mimeType") == "image/jpeg" else "PNG", quality=95)
    views[img["bufferView"]] = bio.getvalue()
    print(f"  입술칠: 입술선 둘레를 아랫입술 색 {lipc.astype(int)} 로 (겉면 그림 칠한 칸 {int((al > 0.05).sum())}개)")

out = bytearray()
for i, v in enumerate(j["bufferViews"]):
    while len(out) % 4: out += b"\0"
    v["byteOffset"] = len(out); v["byteLength"] = len(views[i]); out += views[i]
while len(out) % 4: out += b"\0"
j["buffers"][0]["byteLength"] = len(out)
js = json.dumps(j, ensure_ascii=False, separators=(",", ":")).encode()
while len(js) % 4: js += b" "
open(dst, "wb").write(struct.pack("<III", 0x46546C67, 2, 28 + len(js) + len(out)) + struct.pack("<II", len(js), 0x4E4F534A) + js
                      + struct.pack("<II", len(out), 0x004E4942) + bytes(out))
print("→", dst)
if check:     # 확인 그림: 얼굴 앞 점들(겉면 색) + 찾은 입술선(빨강) + 코끝 높이(파랑)
    from PIL import ImageDraw
    im = Image.new("RGB", (700, 700), "white"); d = ImageDraw.Draw(im); sc = 7000
    m = front & (np.abs(x) < 0.05) & (np.abs(y - LY0) < 0.05)
    cs = color(m)
    for (px_, py_), c in zip(P[m][:, :2], cs):
        u_, v_ = 350 + px_ * sc, 350 - (py_ - LY0) * sc; d.rectangle([u_ - 2, v_ - 2, u_ + 2, v_ + 2], fill=tuple(int(v) for v in c))
    for xx_ in (XC - hw(0.0) * 0.88, XC + hw(0.0) * 0.88): d.line([(350 + xx_ * sc, 0), (350 + xx_ * sc, 700)], fill="green")     # 틈 끝(입꼬리)
    d.line([(350 + a_ * sc, 350 - (b_ - LY0) * sc) for a_, b_ in zip(xs, ys)], fill="red", width=2)
    d.line([(0, 350 - (nose_y - LY0) * sc), (700, 350 - (nose_y - LY0) * sc)], fill="blue")
    im.save(check); print("확인 그림:", check)
