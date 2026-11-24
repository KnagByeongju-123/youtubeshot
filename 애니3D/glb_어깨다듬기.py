"""GLB 사람 모델: 어깨 둘레 뼈 무게 고르게 — 팔을 들 때 재킷 어깨 끝이 뿔처럼 솟고 겨드랑이가 접히는 것 줄이기
   (여자 아나운서 2026-11-24 '팔 벌려 자세에서 어깨 쪽 확인': 팔을 옆으로 들면 어깨 패드가 가슴 뼈에만 붙어 제자리에 남아 위로 뾰족하게 솟았음)
   → 위팔 뼈 머리(어깨 관절)에서 --반경 안의 점마다 뼈 무게를 이웃 평균으로 여러 번 고르게 (가슴↔위팔이 부드럽게 섞임)
   사용: python 애니3D/glb_어깨다듬기.py <입력.glb> <결과.glb> [--반경 0.10] [--번 25]"""
import json, struct, sys
import numpy as np

a = sys.argv[1:]
RAD, NIT = 0.10, 25
if "--반경" in a: i = a.index("--반경"); RAD = float(a[i + 1]); del a[i:i + 2]
if "--번" in a: i = a.index("--번"); NIT = int(a[i + 1]); del a[i:i + 2]
src, dst = a
raw = open(src, "rb").read(); n = struct.unpack("<I", raw[12:16])[0]; j = json.loads(raw[20:20 + n]); b0 = 20 + n + 8
BIN = raw[b0:b0 + struct.unpack("<I", raw[20 + n:24 + n])[0]]
views = [BIN[v.get("byteOffset", 0):v.get("byteOffset", 0) + v["byteLength"]] for v in j["bufferViews"]]
COMP = {5126: np.float32, 5125: np.uint32, 5123: np.uint16, 5121: np.uint8}; K = {"VEC2": 2, "VEC3": 3, "VEC4": 4, "SCALAR": 1, "MAT4": 16}


def get(i):
    ac = j["accessors"][i]; dt = np.dtype(COMP[ac["componentType"]])
    return np.frombuffer(views[ac["bufferView"]], dt, ac["count"] * K[ac["type"]], ac.get("byteOffset", 0)).reshape(-1, K[ac["type"]]).copy()


def put_same(i, arr):
    ac = j["accessors"][i]; dt = np.dtype(COMP[ac["componentType"]]); b = arr.astype(dt).reshape(-1).tobytes()
    vi = ac["bufferView"]; o = ac.get("byteOffset", 0); bb = bytearray(views[vi]); bb[o:o + len(b)] = b; views[vi] = bytes(bb)


pr = j["meshes"][0]["primitives"][0]; at = pr["attributes"]
P = get(at["POSITION"]).astype(float); J = get(at["JOINTS_0"]).astype(np.int64); W = get(at["WEIGHTS_0"]).astype(float)
wac = j["accessors"][at["WEIGHTS_0"]]; wmax = 255.0 if wac["componentType"] == 5121 else 65535.0 if wac["componentType"] == 5123 else 1.0
W /= wmax
sk = j["skins"][0]; names = [j["nodes"][q]["name"] for q in sk["joints"]]
ibm = get(sk["inverseBindMatrices"]).reshape(-1, 4, 4); JP = {nm: np.linalg.inv(m.T)[:3, 3] for nm, m in zip(names, ibm)}
I = np.concatenate([get(p_["indices"]).reshape(-1, 3).astype(np.int64) for p_ in j["meshes"][0]["primitives"] if p_["attributes"]["POSITION"] == at["POSITION"]])
I = I[(I[:, 0] != I[:, 1]) & (I[:, 1] != I[:, 2])]
_, g = np.unique(np.round(P * 2e4).astype(np.int64), axis=0, return_inverse=True); g = g.reshape(-1); G = g.max() + 1
cnt = np.bincount(g, minlength=G).astype(float)
gpos = np.zeros((G, 3)); np.add.at(gpos, g, P); gpos /= cnt[:, None]
gi = g[I]; e = np.concatenate([gi[:, [0, 1]], gi[:, [1, 2]], gi[:, [2, 0]]]); e = e[e[:, 0] != e[:, 1]]; e = np.concatenate([e, e[:, ::-1]])
e = np.unique(e, axis=0); deg = np.bincount(e[:, 0], minlength=G).astype(float)
NJ = int(J.max()) + 1; D = np.zeros((G, NJ)); np.add.at(D, (np.repeat(g, 4), J.reshape(-1)), W.reshape(-1)); D /= cnt[:, None]
sh = [JP[n_] for n_ in names if n_.startswith("UpperArm") or n_ in ("LeftUpperArm", "RightUpperArm")]
dmin = np.min(np.stack([np.linalg.norm(gpos - s_, axis=1) for s_ in sh]), 0)
# 머리·목 쪽(어깨 관절보다 많이 높은 곳)과 손 쪽은 빼고
top = max(s_[1] for s_ in sh)
wz = np.clip((RAD - dmin) / (RAD * 0.35), 0, 1) * (gpos[:, 1] < top + 0.06)
for _ in range(NIT):
    sm_ = np.zeros_like(D); np.add.at(sm_, e[:, 0], D[e[:, 1]])
    D = D + (0.5 * wz)[:, None] * (np.where(deg[:, None] > 0, sm_ / np.maximum(deg, 1)[:, None], D) - D)
ch = wz[g] > 0
tp = np.argsort(-D[g[ch]], axis=1)[:, :4]; tw = np.take_along_axis(D[g[ch]], tp, 1); tw /= np.maximum(tw.sum(1, keepdims=True), 1e-9)
J[ch] = tp; W[ch] = tw
Wq = np.round(W * wmax) if wmax > 1 else W
if wmax > 1: Wq[:, 0] += wmax - Wq.sum(1)
put_same(at["JOINTS_0"], J); put_same(at["WEIGHTS_0"], Wq)
print(f"어깨 둘레 점 {int(ch.sum())}개 뼈 무게 고르게 (반경 {RAD}m, {NIT}번)")
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
