"""GLB 사람 모델: 무릎 아래 다리·발(구두 포함)을 다리마다 '바깥쪽 반의 거울'로 다시 세움
   AI 로 만든 몸은 두 발·발목이 붙은 채 만들어져, 리깅으로 떼어 내도 안쪽이 평평한 판·틈·덩어리로 남음
   (여자 아나운서: 왼발 갈라짐, 오른 구두 버, 발목 안쪽 쐐기 — 덮거나 눌러 붙이는 방법으로는 계속 흠이 남음, 사용자 결정 2026-11-24 '발부터 새로')
   → 다리마다 높이별 다리 가운데 면 x=c(y)를 재고, --높이 아래에서 가운데 면 안쪽 삼각형을 모두 지운 뒤
     바깥쪽 반 삼각형을 복사해 x' = 2c(y) - x 로 뒤집어 붙임. 복사한 점은 원래 점의 무게(뼈)·겉면 그림 좌표를 그대로 가져
     구두·발·다리가 처음부터 따로 떨어진 온전한 모양이 됨. 위쪽 이음매(원래 안쪽과 거울 안쪽 사이 좁은 틈)는 glb_구멍막기.py 로 막음
   사용: python 애니3D/glb_다리거울.py <입력.glb> <결과.glb> [--높이 -0.60]   (리깅·입 고친 뒤의 모델, 모델 좌표 y)"""
import json, struct, sys
import numpy as np

a = sys.argv[1:]
YTOP = -0.60
if "--높이" in a: i = a.index("--높이"); YTOP = float(a[i + 1]); del a[i:i + 2]
src, dst = a
raw = open(src, "rb").read(); n = struct.unpack("<I", raw[12:16])[0]; j = json.loads(raw[20:20 + n]); b0 = 20 + n + 8
BIN = raw[b0:b0 + struct.unpack("<I", raw[20 + n:24 + n])[0]]
views = [BIN[v.get("byteOffset", 0):v.get("byteOffset", 0) + v["byteLength"]] for v in j["bufferViews"]]
COMP = {5126: np.float32, 5125: np.uint32, 5123: np.uint16, 5121: np.uint8}; K = {"VEC2": 2, "VEC3": 3, "VEC4": 4, "SCALAR": 1}


def get(i):
    ac = j["accessors"][i]; dt = np.dtype(COMP[ac["componentType"]])
    if "bufferView" not in ac: return np.zeros((ac["count"], K[ac["type"]]), dt)
    return np.frombuffer(views[ac["bufferView"]], dt, ac["count"] * K[ac["type"]], ac.get("byteOffset", 0)).reshape(-1, K[ac["type"]]).copy()


def put(i, arr):
    """접근자 i 의 자료를 arr 로 바꿈 (점 수가 늘어도 됨) — 그 칸을 혼자 쓰므로 칸을 통째로 바꿈"""
    ac = j["accessors"][i]; dt = np.dtype(COMP[ac["componentType"]])
    if "bufferView" not in ac:                   # 드문 모양 키(sparse): 바뀐 점만 적혀 있어 수만 늘림
        ac["count"] = len(arr); return
    views[ac["bufferView"]] = arr.astype(dt).reshape(-1).tobytes(); ac["byteOffset"] = 0; ac["count"] = len(arr)
    j["bufferViews"][ac["bufferView"]].pop("byteStride", None)
    if "min" in ac: ac["min"] = [float(v) for v in arr.min(0)]; ac["max"] = [float(v) for v in arr.max(0)]


pr = j["meshes"][0]["primitives"][0]; at = pr["attributes"]
P = get(at["POSITION"]).astype(float); I = get(pr["indices"]).reshape(-1, 3).astype(np.int64)
NV = len(P)
ok = (I[:, 0] != I[:, 1]) & (I[:, 1] != I[:, 2]) & (I[:, 0] != I[:, 2])
cen = P[I].mean(1)
keepT = np.ones(len(I), bool); newT = []; src_v = []; newX = []
for sd, sgn in (("L", 1), ("R", -1)):
    leg = (P[:, 1] < YTOP + 0.06) & (P[:, 0] * sgn > 0.0)
    # 높이별 가운데 면: 붙어 있던 가운데(|x|<1.5cm)는 빼고 바깥 끝·안쪽 끝 가운데, 높이 방향으로 고르게
    ys = np.arange(P[leg, 1].min(), YTOP + 0.06, 0.01); cs = []
    for y0 in ys:
        m = leg & (np.abs(P[:, 1] - y0) < 0.008) & (P[:, 0] * sgn > 0.015)
        cs.append((np.percentile(P[m, 0] * sgn, 99.5) + np.percentile(P[m, 0] * sgn, 0.5)) / 2 if m.sum() > 20 else np.nan)
    cs = np.array(cs); good = ~np.isnan(cs); cs = np.interp(ys, ys[good], cs[good])
    cs = np.convolve(np.pad(cs, 3, mode="edge"), np.ones(7) / 7, mode="valid")
    cfun = lambda y: np.interp(y, ys, cs)
    # 지울 것: 이 다리 쪽, 높이 아래, 가운데 면 안쪽(삼각형 한 점이라도 안쪽) + 가운데 덩어리
    tri_side = (cen[:, 0] * sgn > -0.004)
    low = P[I][:, :, 1].max(1) < YTOP
    xin = (P[I][:, :, 0] * sgn) < cfun(P[I][:, :, 1]) - 0.0005
    kill = ok & tri_side & low & xin.any(1)
    keepT &= ~kill
    # 복사할 것: 이 다리 쪽, 높이 아래, 세 점 모두 가운데 면 바깥(또는 위)
    cp = ok & tri_side & low & ~xin.any(1) & (cen[:, 0] * sgn > 0.004)
    T = I[cp]; vid, inv = np.unique(T, return_inverse=True)
    q = P[vid]; c_ = cfun(q[:, 1])
    on_plane = (q[:, 0] * sgn - c_) < 0.0015                                  # 가운데 면에 붙은 점은 원래 점을 그대로 같이 씀(이음매 없게)
    nx = sgn * (2 * c_ - q[:, 0] * sgn)
    idmap = np.where(on_plane, vid, -1)
    nnew = int((~on_plane).sum()); base = NV + len(src_v)
    idmap[~on_plane] = base + np.arange(nnew)
    src_v.extend(vid[~on_plane].tolist()); newX.extend(nx[~on_plane].tolist())
    T2 = idmap[inv.reshape(-1, 3)][:, ::-1]                                    # 뒤집었으니 삼각형 방향도 뒤집음
    newT.append(T2)
    print(f"{sd} 다리: 안쪽 삼각형 {int(kill.sum())}개 지움, 바깥쪽 {len(T)}개를 거울로 붙임 (새 점 {nnew}개), 가운데 x {cs.min() * sgn:+.3f}~{cs.max() * sgn:+.3f}")
src_v = np.array(src_v, np.int64); newX = np.array(newX)
# 점 자료 늘리기
for name, ai in at.items():
    arr = get(ai); add = arr[src_v].copy()
    if name == "POSITION": add = add.astype(np.float32); add[:, 0] = newX
    if name == "NORMAL": add[:, 0] = -add[:, 0]
    if name == "TANGENT": add[:, 0] = -add[:, 0]; add[:, 3] = -add[:, 3]
    put(ai, np.concatenate([arr, add]))
for t in pr.get("targets", []):
    for name, ai in t.items():
        arr = get(ai); add = arr[src_v].copy()
        if name in ("POSITION", "NORMAL"): add[:, 0] = -add[:, 0]
        put(ai, np.concatenate([arr, add]))
I2 = np.concatenate([I[keepT]] + newT)
put(pr["indices"], I2.reshape(-1, 1))
print(f"삼각형 {len(I)} → {len(I2)}, 점 {NV} → {NV + len(src_v)}")
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
