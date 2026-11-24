"""GLB 사람 모델: 맨다리(구두 윗선 ~ 치마 아랫단) 살을 고르게 다듬어 작은 혹·버 없애기
   AI 로 만든 몸은 종아리·무릎에 작은 혹이 있어 걸을 때 버처럼 튀어 보임 (여자 아나운서 2026-11-24 사용자 지적 '종아리도 버어제거')
   → 같은 자리 점끼리 묶은 뒤 Taubin 다듬기(λ=0.5, μ=-0.53, 모양은 줄어들지 않고 작은 울퉁불퉁만 펴짐)를 그 구간 점에만 적용,
     구간 위·아래 끝 1.5cm 는 점점 약하게. 겉면 방향(NORMAL)도 새 모양으로 다시 계산
   사용: python 애니3D/glb_다리다듬기.py <입력.glb> <결과.glb> [--번 20]"""
import json, struct, sys
import numpy as np

a = sys.argv[1:]
N_IT = 20
if "--번" in a: i = a.index("--번"); N_IT = int(a[i + 1]); del a[i:i + 2]
src, dst = a
raw = open(src, "rb").read(); n = struct.unpack("<I", raw[12:16])[0]; j = json.loads(raw[20:20 + n]); b0 = 20 + n + 8
BIN = raw[b0:b0 + struct.unpack("<I", raw[20 + n:24 + n])[0]]
views = [BIN[v.get("byteOffset", 0):v.get("byteOffset", 0) + v["byteLength"]] for v in j["bufferViews"]]
COMP = {5126: np.float32, 5125: np.uint32, 5123: np.uint16, 5121: np.uint8}; K = {"VEC2": 2, "VEC3": 3, "VEC4": 4, "SCALAR": 1}


def get(i):
    ac = j["accessors"][i]; dt = np.dtype(COMP[ac["componentType"]])
    return np.frombuffer(views[ac["bufferView"]], dt, ac["count"] * K[ac["type"]], ac.get("byteOffset", 0)).reshape(-1, K[ac["type"]]).copy()


def put_same(i, arr):
    ac = j["accessors"][i]; dt = np.dtype(COMP[ac["componentType"]]); b = arr.astype(dt).reshape(-1).tobytes()
    vi = ac["bufferView"]; o = ac.get("byteOffset", 0); bb = bytearray(views[vi]); bb[o:o + len(b)] = b; views[vi] = bytes(bb)
    if "min" in ac: ac["min"] = [float(v) for v in arr.min(0)]; ac["max"] = [float(v) for v in arr.max(0)]


prims = j["meshes"][0]["primitives"]; pr = prims[0]
P = get(pr["attributes"]["POSITION"]).astype(float)
I = np.concatenate([get(p["indices"]).reshape(-1, 3).astype(np.int64) for p in prims if p["attributes"]["POSITION"] == pr["attributes"]["POSITION"]])
I = I[(I[:, 0] != I[:, 1]) & (I[:, 1] != I[:, 2]) & (I[:, 0] != I[:, 2])]
ymin, ymax = P[:, 1].min(), P[:, 1].max(); H = ymax - ymin
y0, y1 = ymin + 0.085 * H, ymin + 0.305 * H                 # 구두 윗선 조금 위 ~ 치마 아랫단 조금 아래
_, g = np.unique(np.round(P * 2e4).astype(np.int64), axis=0, return_inverse=True); g = g.reshape(-1); G = g.max() + 1
gp = np.zeros((G, 3)); np.add.at(gp, g, P); cnt = np.bincount(g, minlength=G); gp /= cnt[:, None]
gi = g[I]; e = np.concatenate([gi[:, [0, 1]], gi[:, [1, 2]], gi[:, [2, 0]]]); e = np.unique(np.sort(e, 1), axis=0); e = e[e[:, 0] != e[:, 1]]
yy = gp[:, 1]
wgt = np.clip(np.minimum((yy - y0) / 0.015, (y1 - yy) / 0.015), 0, 1); wgt[np.abs(gp[:, 0]) > 0.2] = 0     # 손은 빼기(다리 높이에 손이 없게 x 로도)
deg = np.bincount(e.ravel(), minlength=G).astype(float)
def lap(X):
    s = np.zeros_like(X); np.add.at(s, e[:, 0], X[e[:, 1]]); np.add.at(s, e[:, 1], X[e[:, 0]])
    return np.where(deg[:, None] > 0, s / np.maximum(deg, 1)[:, None] - X, 0)
X = gp.copy()
for _ in range(N_IT):
    X = X + 0.5 * wgt[:, None] * lap(X)
    X = X - 0.53 * wgt[:, None] * lap(X)
mv = np.linalg.norm(X - gp, axis=1)
print(f"맨다리 점 {int((wgt > 0).sum())}개 다듬음: 가장 많이 옮긴 {mv.max() * 1000:.1f}mm, 평균 {mv[wgt > 0].mean() * 1000:.2f}mm")
Pn = X[g]
# 겉면 방향 다시: 면 방향을 점 묶음마다 더해 고르게
fn = np.cross(Pn[I[:, 1]] - Pn[I[:, 0]], Pn[I[:, 2]] - Pn[I[:, 0]])
gn = np.zeros((G, 3)); 
for k in range(3): np.add.at(gn, g[I[:, k]], fn)
gn /= np.maximum(np.linalg.norm(gn, axis=1), 1e-12)[:, None]
put_same(pr["attributes"]["POSITION"], Pn.astype(np.float32))
if "NORMAL" in pr["attributes"]:
    Nold = get(pr["attributes"]["NORMAL"]).astype(float); ch = wgt[g] > 0
    Nold[ch] = gn[g[ch]]; put_same(pr["attributes"]["NORMAL"], Nold.astype(np.float32))
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
