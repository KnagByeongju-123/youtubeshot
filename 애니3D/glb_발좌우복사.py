"""GLB 사람 모델: 오른쪽 아랫다리·발·구두를 좌우로 뒤집어 왼쪽에 그대로 붙이고, 구두 굽은 떼어 따로 된 물체로
   (사용자 결정 2026-11-24: '오른발과 구두를 같이 미러', '구두 굽이 없는 상태로 해서 다시', '분리')
   ① 오른발 구두 굽(바닥에서 --굽높이 아래·뒤꿈치 쪽 5cm)을 몸에서 떼어 냄 → 굽 조각은 <굽 폴더>/구두.npz (왼쪽은 거울)
   ② --높이 아래 왼쪽 다리 삼각형을 모두 지우고, 오른쪽(굽 뺀 것)을 x → -x 로 뒤집어 붙임.
      이음매(--높이)에서 두 다리 단면 가운데가 맞도록 왼쪽으로 옮기고, 뼈는 .R → .L 로 바꿈
   ③ 위쪽 이음매는 남겨 둔 왼쪽 다리 아래 끝 점에 맞춤. 남은 틈은 glb_구멍막기.py 로
   사용: python 애니3D/glb_발좌우복사.py <입력.glb> <결과.glb> <굽 폴더> [--높이 -0.60] [--굽높이 0.048] [--굽가져오기 <다리 고치기 전.glb>]
     사용자가 고른 방법(2026-11-24 "이게 깔끔했어"): 굽 없는 거울 다리(glb_다리거울 a1e4ad6 판) + --굽높이 0 --굽가져오기 lip4 = 오른발·구두에 원래 굽을 넣고 통째로 왼쪽에 뒤집어 붙임
   굽 붙이기: 실사3D/야외_오르빗.py ... --구두 <굽 폴더>"""
import io, json, os, struct, sys
from collections import Counter
import numpy as np
from PIL import Image

a = sys.argv[1:]
YTOP, HEELH = -0.60, 0.048
if "--높이" in a: i = a.index("--높이"); YTOP = float(a[i + 1]); del a[i:i + 2]
if "--굽높이" in a: i = a.index("--굽높이"); HEELH = float(a[i + 1]); del a[i:i + 2]
HEELSRC = None
if "--굽가져오기" in a: i = a.index("--굽가져오기"); HEELSRC = a[i + 1]; del a[i:i + 2]
src, dst, heel_dir = a
raw = open(src, "rb").read(); n = struct.unpack("<I", raw[12:16])[0]; j = json.loads(raw[20:20 + n]); b0 = 20 + n + 8
BIN = raw[b0:b0 + struct.unpack("<I", raw[20 + n:24 + n])[0]]
views = [BIN[v.get("byteOffset", 0):v.get("byteOffset", 0) + v["byteLength"]] for v in j["bufferViews"]]
COMP = {5126: np.float32, 5125: np.uint32, 5123: np.uint16, 5121: np.uint8}; K = {"VEC2": 2, "VEC3": 3, "VEC4": 4, "SCALAR": 1}


def get(i):
    ac = j["accessors"][i]; dt = np.dtype(COMP[ac["componentType"]])
    if "bufferView" not in ac: return np.zeros((ac["count"], K[ac["type"]]), dt)
    return np.frombuffer(views[ac["bufferView"]], dt, ac["count"] * K[ac["type"]], ac.get("byteOffset", 0)).reshape(-1, K[ac["type"]]).copy()


def put(i, arr):
    ac = j["accessors"][i]; dt = np.dtype(COMP[ac["componentType"]])
    if "bufferView" not in ac: ac["count"] = len(arr); return
    views[ac["bufferView"]] = arr.astype(dt).reshape(-1).tobytes(); ac["byteOffset"] = 0; ac["count"] = len(arr)
    j["bufferViews"][ac["bufferView"]].pop("byteStride", None)
    if "min" in ac: ac["min"] = [float(v) for v in arr.min(0)]; ac["max"] = [float(v) for v in arr.max(0)]


pr = j["meshes"][0]["primitives"][0]; at = pr["attributes"]
P = get(at["POSITION"]).astype(float); UV = get(at["TEXCOORD_0"]).astype(float); I = get(pr["indices"]).reshape(-1, 3).astype(np.int64)
NV = len(P); ymin = P[:, 1].min()
ok = (I[:, 0] != I[:, 1]) & (I[:, 1] != I[:, 2]) & (I[:, 0] != I[:, 2]); cen = P[I].mean(1)
names = [j["nodes"][q]["name"] for q in j["skins"][0]["joints"]]; JI = {nm: k for k, nm in enumerate(names)}
remap = np.arange(len(names))
for k, nm in enumerate(names):
    for a_, b_ in ((".R", ".L"), ("Right", "Left")):
        if a_ in nm and nm.replace(a_, b_) in JI: remap[k] = JI[nm.replace(a_, b_)]
# 굽 가져오기(--굽가져오기 <다리 고치기 전 glb>): 거울로 세우며 굽이 없어진 모델에, 원래 모델의 오른 구두 굽 삼각형을 다시 넣음
#   (점 번호는 앞부분이 같음 — glb_다리거울.py 는 점을 뒤에 덧붙이기만 함). 넣은 굽은 아래에서 오른발과 함께 왼쪽으로도 뒤집혀 붙음
if HEELSRC:
    # 굽을 점째로 가져옴: 원본(굽이 온전한 모델)의 오른 구두 굽 삼각형과 그 점들(무게·그림 좌표 포함)을 이 모델 끝에 덧붙임
    r2 = open(HEELSRC, "rb").read(); n2 = struct.unpack("<I", r2[12:16])[0]; j2 = json.loads(r2[20:20 + n2]); B2 = r2[20 + n2 + 8:]
    def get2(i):
        ac = j2["accessors"][i]; dt = np.dtype(COMP[ac["componentType"]])
        if "bufferView" not in ac: return np.zeros((ac["count"], K[ac["type"]]), dt)
        bv = j2["bufferViews"][ac["bufferView"]]
        return np.frombuffer(B2, dt, ac["count"] * K[ac["type"]], bv.get("byteOffset", 0) + ac.get("byteOffset", 0)).reshape(-1, K[ac["type"]]).copy()
    pr2 = j2["meshes"][0]["primitives"][0]; P2 = get2(pr2["attributes"]["POSITION"]).astype(float); I0 = get2(pr2["indices"]).reshape(-1, 3).astype(np.int64)
    I0 = I0[(I0[:, 0] != I0[:, 1]) & (I0[:, 1] != I0[:, 2])]
    c0 = P2[I0].mean(1); y2 = P2[:, 1].min(); zr = P2[I0[c0[:, 0] < 0]].reshape(-1, 3)[:, 2].min()
    zone = (c0[:, 0] < 0) & ((P2[I0][:, :, 1] < y2 + 0.11) & (P2[I0][:, :, 2] < zr + 0.06)).all(1)   # 굽 높이 전체(약 8cm)
    # 이미 이 모델에 있는 구두 면(뒤꿈치 겉면)과 겹치는 삼각형은 빼고, 구두 밖으로 나온 굽만
    from scipy.spatial import cKDTree
    here = (P[:, 0] < 0) & (P[:, 1] < y2 + 0.12); tree = cKDTree(P[here])
    dmin = np.stack([tree.query(P2[I0[zone]][:, k])[0] for k in range(3)], 1).max(1)
    hz = zone.copy(); hz[np.where(zone)[0]] = dmin > 0.002
    hv, hinv = np.unique(I0[hz], return_inverse=True)
    for name, ai in at.items():
        arr = get(ai); add = get2(pr2["attributes"][name])[hv] if name in pr2["attributes"] else np.zeros((len(hv), arr.shape[1]), arr.dtype)
        put(ai, np.concatenate([arr, add.astype(arr.dtype)]))
    for t in pr.get("targets", []):
        for name, ai in t.items():
            arr = get(ai); put(ai, np.concatenate([arr, np.zeros((len(hv), arr.shape[1]), arr.dtype)]))
    I = np.concatenate([I, NV + hinv.reshape(-1, 3)])
    P = get(at["POSITION"]).astype(float); UV = get(at["TEXCOORD_0"]).astype(float); NV = len(P)
    ok = (I[:, 0] != I[:, 1]) & (I[:, 1] != I[:, 2]) & (I[:, 0] != I[:, 2]); cen = P[I].mean(1)
    print(f"굽이 온전한 모델에서 오른 구두 굽 삼각형 {int(hz.sum())}개(점 {len(hv)}개)를 가져와 넣음")
low = P[I][:, :, 1].max(1) < YTOP
R_t = ok & low & (cen[:, 0] < 0); L_t = ok & low & (cen[:, 0] > 0)
# ① 오른발 굽: 바닥에서 HEELH 아래 + 오른발 뒤꿈치 쪽 5cm
zminR = P[I[R_t]].reshape(-1, 3)[:, 2].min()
heel = R_t & ((P[I][:, :, 1] < ymin + HEELH) & (P[I][:, :, 2] < zminR + 0.05)).all(1)
print(f"오른발 굽 삼각형 {int(heel.sum())}개 떼어 냄")
# 이음매에서 두 다리 단면 가운데
band = lambda sg: (P[:, 1] > YTOP) & (P[:, 1] < YTOP + 0.03) & (P[:, 0] * sg > 0.01)
cL = np.array([(P[band(1), 0].min() + P[band(1), 0].max()) / 2, 0, P[band(1), 2].mean()])
cR = np.array([(P[band(-1), 0].min() + P[band(-1), 0].max()) / 2, 0, P[band(-1), 2].mean()])
shift = np.array([cL[0] + cR[0], 0, cL[2] - cR[2]])           # 뒤집은 오른쪽(x=-x) 가운데를 왼쪽 가운데로
print(f"이음매 가운데: 왼 x={cL[0]:+.3f} 오른 x={cR[0]:+.3f} → 뒤집은 뒤 옮김 x {shift[0]:+.4f}, z {shift[2]:+.4f}")
copyT = R_t & ~heel
T = I[copyT]; vid, inv = np.unique(T, return_inverse=True)
newpos = P[vid].copy(); newpos[:, 0] = -newpos[:, 0]; newpos += shift
# ③ 위쪽 이음매: 복사 조각의 위쪽 가장자리 점을 남은 왼쪽 다리 아래 끝 점에 맞춤
gk = np.round(P * 2e4).astype(np.int64); _, gid = np.unique(gk, axis=0, return_inverse=True); gid = gid.reshape(-1)
def boundary_verts(tris):
    ec = Counter()
    for t in gid[tris]:
        for e in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])): ec[(min(e), max(e))] += 1
    return set(x for e, c in ec.items() if c == 1 for x in e)
bc = boundary_verts(T); keepL = ok & ~L_t & (cen[:, 0] > 0); bk = boundary_verts(I[keepL])
rep = np.zeros(gid.max() + 1, np.int64); rep[gid] = np.arange(len(gid))
KB = np.array([P[rep[g]] for g in bk]); KB = KB[np.abs(KB[:, 1] - YTOP) < 0.03] if len(KB) else KB
top = np.array([gid[v] in bc for v in vid]) & (P[vid, 1] > YTOP - 0.02)
ns = 0
if len(KB):
    for k in np.where(top)[0]:
        d2 = ((KB - newpos[k]) ** 2).sum(1); m = d2.argmin()
        if d2[m] < 0.025 ** 2: newpos[k] = KB[m]; ns += 1
print(f"위쪽 이음매 점 {ns}개 맞춤")
# 점 자료 늘리기
for name, ai in at.items():
    arr = get(ai); add = arr[vid].copy()
    if name == "POSITION": add = newpos.astype(arr.dtype)
    if name == "NORMAL": add[:, 0] = -add[:, 0]
    if name == "TANGENT": add[:, 0] = -add[:, 0]; add[:, 3] = -add[:, 3]
    if name.startswith("JOINTS"): add = remap[add.astype(np.int64)].astype(arr.dtype)
    put(ai, np.concatenate([arr, add]))
for t in pr.get("targets", []):
    for name, ai in t.items():
        arr = get(ai); add = arr[vid].copy()
        if name in ("POSITION", "NORMAL"): add[:, 0] = -add[:, 0]
        put(ai, np.concatenate([arr, add]))
newT = (NV + inv.reshape(-1, 3))[:, ::-1]
I2 = np.concatenate([I[~L_t & ~heel], newT])
put(pr["indices"], I2.reshape(-1, 1))
print(f"왼쪽 아래 다리 삼각형 {int(L_t.sum())}개 지우고 오른쪽 {len(T)}개를 뒤집어 붙임 (새 점 {len(vid)}개)")
# 굽 조각 (오른 = 그대로, 왼 = 뒤집고 옮김)
HT = I[heel]; hv, hinv = np.unique(HT, return_inverse=True); HP = P[hv]; HU = UV[hv]; HT2 = hinv.reshape(-1, 3)
HPl = HP.copy(); HPl[:, 0] = -HPl[:, 0]; HPl += shift
mat = j["materials"][pr["material"]]; img = j["images"][j["textures"][mat["pbrMetallicRoughness"]["baseColorTexture"]["index"]]["source"]]
os.makedirs(heel_dir, exist_ok=True)
np.savez(os.path.join(heel_dir, "구두.npz"), P=np.concatenate([HPl, HP]).astype(np.float32), UV=np.concatenate([HU, HU]).astype(np.float32),
         I=np.concatenate([HT2[:, ::-1], HT2 + len(HP)]).astype(np.int32), side=np.concatenate([np.zeros(len(HP)), np.ones(len(HP))]).astype(np.int8))
Image.open(io.BytesIO(views[img["bufferView"]])).convert("RGB").save(os.path.join(heel_dir, "구두_그림.png"))
print(f"굽 조각 → {heel_dir} (한 짝 삼각형 {len(HT2)}개)")
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
