"""GLB 사람 모델: 손·손가락을 가늘게 (모양 자체를 바꿔 모든 자세·영상에 적용)
   AI 로 만든 몸은 손이 굵고 뭉툭함 (여자 아나운서 2026-11-23·24 사용자 '손이 너무 굵은 것 같아', '손을 좀 더 가늘게')
   → 점마다 가장 센 손·손가락 뼈의 축(손 = 손목→중지 뿌리, 손가락 = 이 마디→다음 마디)에서 떨어진 거리만 줄임 (길이는 그대로).
     손목 쪽 2cm 는 점점 약하게 해서 소매·팔목과 이음매 없게
   사용: python 애니3D/glb_손가늘게.py <입력.glb> <결과.glb> [--손 0.86] [--손가락 0.84]"""
import json, struct, sys
import numpy as np

a = sys.argv[1:]
SH, SF = 0.86, 0.84
SMOOTH = 20; WSMOOTH = 15
if "--손" in a: i = a.index("--손"); SH = float(a[i + 1]); del a[i:i + 2]
if "--손가락" in a: i = a.index("--손가락"); SF = float(a[i + 1]); del a[i:i + 2]
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
    if "min" in ac: ac["min"] = [float(v) for v in arr.min(0)]; ac["max"] = [float(v) for v in arr.max(0)]


pr = j["meshes"][0]["primitives"][0]; at = pr["attributes"]
P = get(at["POSITION"]).astype(float); J = get(at["JOINTS_0"]).astype(np.int64); W = get(at["WEIGHTS_0"]).astype(float)
W /= 255.0 if W.max() > 1.5 and W.max() <= 255 else (65535.0 if W.max() > 255 else 1.0)
sk = j["skins"][0]; names = [j["nodes"][q]["name"] for q in sk["joints"]]
ibm = get(sk["inverseBindMatrices"]).reshape(-1, 4, 4)
JP = {nm: np.linalg.inv(m.T)[:3, 3] for nm, m in zip(names, ibm)}
FING = ("Thumb", "Index", "Middle", "Ring", "Little")
seg = {}                                                                     # 뼈 번호 → (시작점, 끝점, 줄이는 배율)
for s in ("L", "R"):
    h = f"Hand.{s}"
    if h not in JP: continue
    seg[names.index(h)] = (JP[h], JP.get(f"Middle1.{s}", JP[h]), SH)
    for f in FING:
        ch = [JP.get(f"{f}{k}.{s}") for k in (1, 2, 3)]
        if any(c is None for c in ch): continue
        tip = ch[2] + (ch[2] - ch[1]) * 0.9
        for k, (p0, p1) in enumerate(((ch[0], ch[1]), (ch[1], ch[2]), (ch[2], tip))):
            seg[names.index(f"{f}{k + 1}.{s}")] = (p0, p1, SF)
# 뼈 무게로 섞음: 점마다 각 손·손가락 뼈 축 기준으로 줄인 위치를 그 뼈의 무게만큼 더함 (가장 센 뼈 하나만 쓰면 마디 경계에서 계단이 생겼음)
Pn = P.copy(); acc_w = np.zeros(len(P)); acc_p = np.zeros_like(P); moved = 0
for b, (p0, p1, sc) in seg.items():
    wb = ((J == b) * W).sum(1); m = wb > 1e-4
    if not m.any(): continue
    d = p1 - p0; L = np.linalg.norm(d); d /= max(L, 1e-9)
    q = P[m] - p0; tpar = q @ d; axis_pt = p0 + np.clip(tpar, -0.02, L + 0.03)[:, None] * d
    f = np.full(m.sum(), sc)
    if names[b].startswith("Hand"): f = 1 - (1 - sc) * np.clip((tpar + 0.005) / 0.025, 0, 1)   # 손목 쪽은 점점 약하게
    acc_p[m] += wb[m, None] * (axis_pt + (P[m] - axis_pt) * f[:, None]); acc_w[m] += wb[m]; moved += int(m.sum())
hm = acc_w > 0
Pn[hm] = acc_p[hm] + (1 - acc_w[hm])[:, None] * P[hm]                        # 손이 아닌 뼈 무게 몫은 제자리
# 같은 자리 점은 같이 (꿰맨 이음매가 벌어지지 않게) + 옮긴 양을 이웃끼리 고르게 (마디·엄지 뿌리 경계의 계단 없애기)
_, g = np.unique(np.round(P * 2e4).astype(np.int64), axis=0, return_inverse=True); g = g.reshape(-1); G = g.max() + 1
cnt = np.bincount(g, minlength=G).astype(float)
D = np.zeros((G, 3)); np.add.at(D, g, Pn - P); D /= cnt[:, None]
I = np.concatenate([get(p_["indices"]).reshape(-1, 3).astype(np.int64) for p_ in j["meshes"][0]["primitives"] if p_["attributes"]["POSITION"] == at["POSITION"]])
gi = g[I]; e = np.concatenate([gi[:, [0, 1]], gi[:, [1, 2]], gi[:, [2, 0]]]); e = e[e[:, 0] != e[:, 1]]
deg = np.bincount(e[:, 0], minlength=G).astype(float)
hg = np.zeros(G); np.maximum.at(hg, g, hm.astype(float))
for _ in range(SMOOTH):
    sm_ = np.zeros_like(D); np.add.at(sm_, e[:, 0], D[e[:, 1]])
    D = np.where((hg > 0)[:, None] & (deg > 0)[:, None], 0.5 * D + 0.5 * sm_ / np.maximum(deg, 1)[:, None], D)
Pn = P + D[g]
put_same(at["POSITION"], Pn.astype(np.float32))
# 손가락 뿌리(손등 마디) 둘레 뼈 무게 고르게: 이웃한 두 손가락에 따로 붙은 점이 섞여 있으면 굽힐 때 마디에 주름·홈이 생김 (검지·중지 사이 검은 홈)
wac = j["accessors"][at["WEIGHTS_0"]]; wmax = 255.0 if wac["componentType"] == 5121 else 65535.0 if wac["componentType"] == 5123 else 1.0
NJ = int(J.max()) + 1; Dw = np.zeros((G, NJ)); np.add.at(Dw, (np.repeat(g, 4), J.reshape(-1)), W.reshape(-1)); Dw /= cnt[:, None]
roots_ = [JP[f"{f}1.{s_}"] for s_ in ("L", "R") for f in ("Index", "Middle", "Ring", "Little") if f"{f}1.{s_}" in JP]
gpos = np.zeros((G, 3)); np.add.at(gpos, g, P); gpos /= cnt[:, None]
dmin = np.min(np.stack([np.linalg.norm(gpos - r_, axis=1) for r_ in roots_]), 0) if roots_ else np.full(G, 9.0)
wz = np.clip((0.035 - dmin) / 0.015, 0, 1) * (hg > 0)
for _ in range(WSMOOTH):
    sm_ = np.zeros_like(Dw); np.add.at(sm_, e[:, 0], Dw[e[:, 1]])
    Dw = Dw + (0.5 * wz)[:, None] * (np.where(deg[:, None] > 0, sm_ / np.maximum(deg, 1)[:, None], Dw) - Dw)
ch = wz[g] > 0
top = np.argsort(-Dw[g[ch]], axis=1)[:, :4]; tw = np.take_along_axis(Dw[g[ch]], top, 1); tw /= np.maximum(tw.sum(1, keepdims=True), 1e-9)
J2 = J.copy(); W2 = W.copy(); J2[ch] = top; W2[ch] = tw
Wq = np.round(W2 * wmax) if wmax > 1 else W2
if wmax > 1: Wq[:, 0] += wmax - Wq.sum(1)
put_same(at["JOINTS_0"], J2); put_same(at["WEIGHTS_0"], Wq)
print(f"손가락 뿌리 둘레 점 {int(ch.sum())}개 뼈 무게 고르게")
print(f"손·손가락 점 {moved}개를 가늘게 (손 {SH}, 손가락 {SF}), 가장 많이 옮긴 {np.linalg.norm(Pn - P, axis=1).max() * 1000:.1f}mm")
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
