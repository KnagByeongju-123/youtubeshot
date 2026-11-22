"""GLB 사람 모델의 입 모양 키(MouthOpen·MouthWide·MouthRound)를 '그려진 입술' 자리에 맞춰 새로 만듦
   AI 로 만든 3D 사람은 겉면 그림(텍스처)의 입술과 실제 모양(메시)의 입 자리가 어긋나 있고, 자동으로 만든 입 모양 키가
   코 밑을 잡아당겨 코가 길게 늘어나기도 함 (2026-11-22 남자 아나운서: 그려진 입술 0.704, 키가 움직이는 곳 0.73 = 코 밑).
   방법: 얼굴 가운데 줄의 점마다 겉면 그림 색을 읽어 '입술 사이 어두운 선'(입술선)을 x 마다 찾고, 그 선을 기준으로
     · MouthOpen  : 입술선 아래(아랫입술~턱)를 아래·조금 뒤로 (아랫입술이 가장 많이, 턱 쪽으로 갈수록 덜). 윗입술은 아주 조금 위로
                    → 입술선 걸친 면이 늘어나며 입술 사이 어두운 색이 벌어진 입처럼 보임 (메시에 입 안이 없어도)
     · MouthWide  : 입꼬리를 옆으로·조금 위로
     · MouthRound : 입술을 가운데로 모으고 앞으로 내밈
     · Blink 등 다른 키는 그대로
   사용: python 애니3D/glb_입모양고치기.py <입력.glb> <결과.glb> [--벌림 0.012] [--확인 <그림.png>]
   (모양 키 이름이 MouthOpen/MouthWide/MouthRound 인 모델. 정점 수·순서는 그대로라 리깅과 함께 써도 됨)"""
import io, json, struct, sys
import numpy as np
from PIL import Image

a = sys.argv[1:]
OPEN = 0.012; check = None
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
print(f"코끝 높이 {nose_y:.3f} · 입술선 가운데 {LY0:.3f} (코끝 아래 {100 * (nose_y - LY0):.1f}cm) · 입 반너비 {100 * HW:.1f}cm")


def ly(x): return np.interp(x, xs, ys)


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
reg = front & (y > Y_LO) & (y < Y_HI) & (np.abs(x) < HW * 1.9)
s_ = np.clip((y - Y_LO) / (Y_HI - Y_LO), 0, 1)
zt = np.interp(x, gx, zlo) + (np.interp(x, gx, zhi) - np.interp(x, gx, zlo)) * s_ ** 1.4 - 0.0015 * np.sin(np.pi * s_) * (1 - sstep((np.abs(x) - 0.006) / 0.01))   # 가운데는 살짝 오목(인중)
wgt = reg * (1 - sstep((np.abs(x) - HW * 1.4) / (HW * 0.5))) * sstep(np.minimum(y - Y_LO, Y_HI - y) / 0.003 + 0.25)
dz = np.where(reg, np.maximum(0, z - zt), 0) * wgt
# 미는 양을 이웃 점끼리 여러 번 고르게 (점마다 들쭉날쭉 밀면 면이 울퉁불퉁해져 얼룩 그늘이 생겼음)
#   같은 자리 점(겉면 그림 이음매로 갈라진 점)은 하나로 묶어 함께 움직임
_Ia = pr["indices"]; _I = np.frombuffer(views[j["accessors"][_Ia]["bufferView"]], np.dtype(COMP[j["accessors"][_Ia]["componentType"]]),
                                       j["accessors"][_Ia]["count"]).reshape(-1, 3).astype(np.int64)
_, gid = np.unique(np.round(P * 2e4).astype(np.int64), axis=0, return_inverse=True); gid = gid.reshape(-1)
near_mouth = front & (np.abs(x) < HW * 2.4) & (y > LY0 - 0.01) & (y < Y_HI + 0.012)
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
lat = 1 - sstep((np.abs(x) - HW * 0.45) / (HW * 0.42))                # 입 가운데 1 → 입꼬리(틈 끝)에서 0 (입꼬리 살이 찢기지 않게)
lat_chin = 1 - sstep((np.abs(x) - HW) / 0.035)                        # 턱은 조금 더 넓게
dy = y - ly(x)                                                        # 입술선에서 위(+)·아래(-)
chin_y = LY0 - 0.045
# 벌림: 아랫입술 1 → 턱 끝 0.55 → 목 0
below = (dy < 0) & front
f_low = np.where(dy < 0, np.where(y > chin_y, 1 - 0.45 * sstep(-dy / (LY0 - chin_y)), 0.55 * (1 - sstep((chin_y - y) / 0.02))), 0)
f_low *= np.maximum(lat, 0.55 * lat_chin * sstep(-dy / 0.015)) * front      # 입꼬리 옆 살은 입술선 바로 아래에선 안 움직임
f_up = np.where((dy >= 0) & front, np.exp(-dy / 0.005) * lat, 0)     # 윗입술 아주 조금 위로
D_open = np.zeros_like(P)
D_open[:, 1] = -OPEN * f_low + 0.12 * OPEN * f_up
D_open[:, 2] = -0.35 * OPEN * f_low
# 옆으로: 입술선 ±1.2cm 안, 입꼬리 쪽일수록
near = np.exp(-(dy / 0.008) ** 2) * front
side = sstep(np.abs(x) / HW) * (1 - sstep((np.abs(x) - HW) / 0.02))
D_wide = np.zeros_like(P)
D_wide[:, 0] = np.sign(x) * 0.006 * side * near
D_wide[:, 1] = 0.0015 * side * near
# 오므림: 입술을 가운데로 모으고 앞으로
lipzone = np.exp(-(dy / 0.010) ** 2) * front * (1 - sstep((np.abs(x) - HW) / 0.02))
D_round = np.zeros_like(P)
D_round[:, 0] = -np.sign(x) * 0.0055 * sstep(np.abs(x) / HW) * lipzone
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
zone = front & (np.abs(x) < HW * 0.9) & (np.abs(dy) < 0.012)
side_ = np.where(dy < 0, 1, 2) * zone
tri_s = side_[I]
cross = (tri_s == 1).any(1) & (tri_s == 2).any(1)
# 틈 가장자리 점을 입술선 위로 모음 → 다물면 한 줄로 딱 닫힘 (들쭉날쭉한 가장자리를 곧게, 가장자리 점은 몇 mm 만 움직임)
edge = np.unique(I[cross].reshape(-1)); edge = edge[zone[edge]]
P2 = P.copy(); P2[edge, 1] = ly(x[edge])
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
    nn = NR[sub] + (after[sub] - before[sub]); nn /= np.maximum(np.linalg.norm(nn, axis=1, keepdims=True), 1e-12)
    NR[sub] = nn; put(pr["attributes"]["NORMAL"], NR)
    print(f"  면 방향 다시 계산: 점 {int(near_chg.sum())}개")
I[cross] = I[cross][:, :1]
views[j["accessors"][I_acc]["bufferView"]] = I.astype(np.dtype(COMP[j["accessors"][I_acc]["componentType"]])).tobytes()
print(f"  입 틈: 입술선을 가로지르는 삼각형 {int(cross.sum())}개 없앰")

# ── 입 안: 입술 바로 뒤에 어두운 둥근 면(입 안) + 윗니 띠 — 머리 뼈를 따라감 ──
lip_z = float(np.median(z[front & (np.abs(x) < 0.01) & (np.abs(dy) < 0.004)]))
head_j = None
for k_, nd_i in enumerate(j["skins"][0]["joints"]):
    if j["nodes"][nd_i].get("name") == "Head": head_j = k_
def add_mesh(name, pos, idx, color, open_disp=None):
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
    if open_disp is not None:          # 입을 벌리면 같이 움직임 (아랫니·입 안 아래쪽)
        prim["targets"] = [{"POSITION": acc_(open_disp.astype(np.float32), 5126, "VEC3", 34962, True)}]
        m_["extras"] = {"targetNames": ["MouthOpen"]}; m_["weights"] = [0.0]
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
    bp, bi = bowl(0.0, LY0 - 0.003, lip_z - 0.004, HW * 0.76, 0.013, 0.03)      # 입 틈(0.9) 안쪽까지만 — 입꼬리 살 뒤로 테두리가 비치지 않게
    # 그릇 점마다 가장 가까운 얼굴 점(앞에서 본 x·y)을 찾아 ① 그 겉면보다 2.5mm 뒤에 두고 ② 입을 벌릴 때 그 점과 똑같이 움직임
    #   → 테두리가 입술·턱 살 밖으로 나오지 않음 (입술 바로 뒤라 메시 안쪽 접힌 면도 가림)
    FM = np.where(front & (np.abs(x) < HW * 1.5) & (np.abs(y - LY0) < 0.04))[0]
    def nearest(pt):        # 3mm 안 점 가운데 가장 앞(겉 살) — 없으면 가장 가까운 점
        d2 = (x[FM] - pt[0]) ** 2 + (y[FM] - pt[1]) ** 2; c_ = FM[d2 < 0.003 ** 2]
        return c_[np.argmax(z[c_])] if len(c_) else FM[np.argmin(d2)]
    near_i = np.array([nearest(q_) for q_ in bp])
    bp[:, 2] = np.minimum(bp[:, 2], z[near_i] - 0.0025)
    bd = D_open[near_i].copy(); bd[:, 2] = np.minimum(bd[:, 2], 0)
    add_mesh("Mouth_Inside", bp, bi, [0.26, 0.07, 0.07, 1.0], bd)
    tw_, th_ = HW * 0.36, 0.0032                                        # 윗니: 입술선 바로 위·안쪽, 벌렸을 때만 보이게 (가운데가 조금 앞으로 둥글게)
    tx = np.linspace(-tw_, tw_, 13); tp, ti = [], []
    for k_, xx in enumerate(tx):
        zz = lip_z - 0.011 - 0.010 * (xx / tw_) ** 2
        tp += [[xx, LY0 + 0.0035, zz], [xx, LY0 + 0.0035 - th_, zz]]
        if k_: a_ = 2 * (k_ - 1); ti += [[a_, a_ + 1, a_ + 2], [a_ + 1, a_ + 3, a_ + 2]]
    add_mesh("Teeth_Upper", np.array(tp), np.array(ti), [0.78, 0.75, 0.70, 1.0])
    # 아랫니는 넣지 않음: 말할 때 대부분 아랫입술에 가려지고, 모양 키로 따라 움직이면 늘어나 이 하나처럼 보였음 (2026-11-22)
    print(f"  입 안(어두운 그릇, 아랫입술과 함께 벌어짐)·윗니 더함 (입술 앞면 z {lip_z:.3f})")

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
    for (px_, py_), c in zip(P[m][:, :2], cs): d.point((350 + px_ * sc, 350 - (py_ - LY0) * sc), fill=tuple(int(v) for v in c))
    d.line([(350 + a_ * sc, 350 - (b_ - LY0) * sc) for a_, b_ in zip(xs, ys)], fill="red", width=2)
    d.line([(0, 350 - (nose_y - LY0) * sc), (700, 350 - (nose_y - LY0) * sc)], fill="blue")
    im.save(check); print("확인 그림:", check)
