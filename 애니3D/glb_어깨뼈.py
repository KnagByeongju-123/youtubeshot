"""GLB 사람 모델에 어깨 뼈(Shoulder.L/R, 쇄골) 넣기 — 팔을 들 때 어깨선이 팔과 함께 올라가게
   (여자 아나운서 2026-11-24: 팔 벌려 자세에서 재킷 어깨 끝이 뿔처럼 솟음 → 사용자 '어깨선이 일치하게 본을 늘려야 하나' → 어깨 뼈 추가)
   뼈대: Chest → Shoulder(목 옆, 위팔 관절 x 의 30%) → UpperArm. 살 무게: 겨드랑이보다 위, 목 옆~어깨 끝의 가슴 무게를 바깥으로 갈수록 어깨 뼈로,
   위팔 관절 바로 둘레 위쪽은 위팔 무게 일부도 어깨 뼈로 → 이웃끼리 고르게. 움직임은 촬영 도구가 팔을 들 때 어깨 뼈를 팔 각도의 일부만큼 같이 듦
   사용: python 애니3D/glb_어깨뼈.py <입력.glb> <결과.glb>"""
import json, struct, sys
import numpy as np

src, dst = sys.argv[1:3]
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


nodes = j["nodes"]; NI = {nd.get("name"): k for k, nd in enumerate(nodes)}
HAVE = "Shoulder.L" in NI          # 이미 어깨 뼈가 있으면(뼈대옮기기로 1번 뼈대를 받은 모델) 뼈는 두고 살 무게만 (2026-11-28 여자아나운서5)
sk = j["skins"][0]; names = [nodes[q]["name"] for q in sk["joints"]]
ibm = get(sk["inverseBindMatrices"]).reshape(-1, 4, 4); JP = {nm: np.linalg.inv(m.T)[:3, 3] for nm, m in zip(names, ibm)}
# ① 뼈 노드
new_ibm = []
for s in (() if HAVE else ("L", "R")):
    ua, ch = NI[f"UpperArm.{s}"], NI["Chest"]
    U = JP[f"UpperArm.{s}"]; S = np.array([0.3 * U[0], U[1] + 0.01, U[2]])
    nodes.append({"name": f"Shoulder.{s}", "translation": [float(v) for v in (S - JP["Chest"])], "children": [ua]}); si = len(nodes) - 1
    nodes[ch]["children"] = [si if c == ua else c for c in nodes[ch]["children"]]
    nodes[ua]["translation"] = [float(v) for v in (U - S)]
    sk["joints"].append(si); m = np.eye(4); m[:3, 3] = -S; new_ibm.append(m.T.reshape(-1))
    JP[f"Shoulder.{s}"] = S; names.append(f"Shoulder.{s}")
iac = j["accessors"][sk["inverseBindMatrices"]]
if HAVE: print("어깨 뼈 있음 → 살 무게만"); new_ibm = np.zeros((0, 16))
allm = np.concatenate([ibm.reshape(-1, 16), np.array(new_ibm)]).astype(np.float32)
views[iac["bufferView"]] = allm.tobytes(); iac["byteOffset"] = 0; iac["count"] = len(allm); j["bufferViews"][iac["bufferView"]].pop("byteStride", None)
JI = {nm: k for k, nm in enumerate(names)}
# ② 살 무게
pr = j["meshes"][0]["primitives"][0]; at = pr["attributes"]
P = get(at["POSITION"]).astype(float); J = get(at["JOINTS_0"]).astype(np.int64); W = get(at["WEIGHTS_0"]).astype(float)
wac = j["accessors"][at["WEIGHTS_0"]]; wmax = 255.0 if wac["componentType"] == 5121 else 65535.0 if wac["componentType"] == 5123 else 1.0
W /= wmax
NJ = len(names); Dv = np.zeros((len(P), NJ)); np.add.at(Dv, (np.repeat(np.arange(len(P)), 4), J.reshape(-1)), W.reshape(-1))
ss = lambda x: np.clip(x, 0, 1) ** 2 * (3 - 2 * np.clip(x, 0, 1))
moved = 0
for s, sg in (("L", 1), ("R", -1)):
    U, S = JP[f"UpperArm.{s}"], JP[f"Shoulder.{s}"]; ks, kc, ku = JI[f"Shoulder.{s}"], JI["Chest"], JI[f"UpperArm.{s}"]
    xs = P[:, 0] * sg
    lat = ss((xs - S[0] * sg) / ((U[0] - S[0]) * sg))                         # 목 옆 0 → 어깨 관절 1
    up = ss((P[:, 1] - (U[1] - 0.04)) / 0.06) * ss(((U[1] + 0.16) - P[:, 1]) / 0.05)   # 어깨 관절 높이부터 위(겨드랑이·옆구리는 빼야 들 때 옆구리가 찢어지지 않음), 목·머리 아래
    side = xs > S[0] * sg - 0.01
    tc = Dv[:, kc] * lat * up * side * 0.9
    near = ss(1 - np.clip((xs - (U[0] * sg - 0.03)) / 0.09, 0, 1)) * ss((P[:, 1] - (U[1] - 0.02)) / 0.04) * (xs > U[0] * sg - 0.03)
    tu = Dv[:, ku] * near * 0.45
    Dv[:, kc] -= tc; Dv[:, ku] -= tu; Dv[:, ks] += tc + tu; moved += int(((tc + tu) > 0.01).sum())
# ③ 이웃끼리 고르게 (어깨 둘레)
I = np.concatenate([get(p_["indices"]).reshape(-1, 3).astype(np.int64) for p_ in j["meshes"][0]["primitives"] if p_["attributes"]["POSITION"] == at["POSITION"]])
I = I[(I[:, 0] != I[:, 1]) & (I[:, 1] != I[:, 2])]
_, g = np.unique(np.round(P * 2e4).astype(np.int64), axis=0, return_inverse=True); g = g.reshape(-1); G = g.max() + 1
cnt = np.bincount(g, minlength=G).astype(float)
D = np.zeros((G, NJ)); np.add.at(D, g, Dv); D /= cnt[:, None]
gpos = np.zeros((G, 3)); np.add.at(gpos, g, P); gpos /= cnt[:, None]
gi = g[I]; e = np.concatenate([gi[:, [0, 1]], gi[:, [1, 2]], gi[:, [2, 0]]]); e = e[e[:, 0] != e[:, 1]]; e = np.unique(np.concatenate([e, e[:, ::-1]]), axis=0)
deg = np.bincount(e[:, 0], minlength=G).astype(float)
dm = np.min(np.stack([np.linalg.norm(gpos - JP[f"UpperArm.{s}"], axis=1) for s in ("L", "R")]), 0)
wz = np.clip((0.14 - dm) / 0.05, 0, 1)
for _ in range(20):
    sm_ = np.zeros_like(D); np.add.at(sm_, e[:, 0], D[e[:, 1]])
    D = D + (0.5 * wz)[:, None] * (np.where(deg[:, None] > 0, sm_ / np.maximum(deg, 1)[:, None], D) - D)
Dv2 = np.where((wz[g] > 0)[:, None], D[g], Dv)
tp = np.argsort(-Dv2, axis=1)[:, :4]; tw = np.take_along_axis(Dv2, tp, 1); tw = np.clip(tw, 0, None); tw /= np.maximum(tw.sum(1, keepdims=True), 1e-9)
Wq = np.round(tw * wmax) if wmax > 1 else tw
if wmax > 1: Wq[:, 0] += wmax - Wq.sum(1)
put_same(at["JOINTS_0"], tp); put_same(at["WEIGHTS_0"], Wq)
print(f"어깨 뼈 2개 추가 (가슴 → 어깨 → 위팔), 어깨 둘레 점 {moved}개 무게를 어깨 뼈로")
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
