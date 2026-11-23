"""GLB 사람 모델: 손등·손바닥에 난 구멍 메우기 (리깅 도구가 손가락 사이를 자르다 손등까지 자른 곳)
   glb_다시리깅.py 는 손가락끼리 이어진 삼각형을 없애 손가락을 떼는데, AI 로 만든 몸은 손가락 뿌리(손등·손바닥)에서도
   점마다 가장 센 손가락 뼈가 달라 그 삼각형까지 없어짐 → 손등에 구멍이 나 안쪽(뒷면)이 검은 얼룩처럼 보임
   (여자 아나운서 오른손, 2026-11-23 손가락 검사: 화면 점을 찍어 보니 '뒷면' = 구멍)
   → 자르기 전 모델에서 그 삼각형을 되살림. 손가락 첫 마디 관절에서 손가락 끝 쪽으로 --여유(기본 0.012) 넘게 나간 곳은
     손가락 사이라 그대로 떼어 둠 (구부릴 때 손가락이 서로 붙어 늘어나지 않게)
   사용: python 애니3D/glb_손구멍메우기.py <자르기 전.glb> <입력.glb> <결과.glb> [--여유 0.012]
     (삼각형 순서가 같은 모델끼리만: 입모양 고치기·얼룩 칠하기는 삼각형 순서를 바꾸지 않음)"""
import json, struct, sys
import numpy as np

a = sys.argv[1:]
MARGIN = 0.012
if "--여유" in a: i = a.index("--여유"); MARGIN = float(a[i + 1]); del a[i:i + 2]
orig, src, dst = a


def load(f):
    raw = open(f, "rb").read(); n = struct.unpack("<I", raw[12:16])[0]; j = json.loads(raw[20:20 + n]); b0 = 20 + n + 8
    bl = struct.unpack("<I", raw[20 + n:24 + n])[0]; BIN = raw[b0:b0 + bl]
    return j, [BIN[v.get("byteOffset", 0):v.get("byteOffset", 0) + v["byteLength"]] for v in j["bufferViews"]]


COMP = {5126: np.float32, 5125: np.uint32, 5123: np.uint16, 5121: np.uint8}; K = {"VEC2": 2, "VEC3": 3, "VEC4": 4, "SCALAR": 1, "MAT4": 16}


def get(j, views, i):
    ac = j["accessors"][i]; dt = np.dtype(COMP[ac["componentType"]])
    return np.frombuffer(views[ac["bufferView"]], dt, ac["count"] * K[ac["type"]], ac.get("byteOffset", 0)).reshape(-1, K[ac["type"]])


j0, v0 = load(orig); j, views = load(src)
pr0 = j0["meshes"][0]["primitives"][0]; pr = j["meshes"][0]["primitives"][0]
I0 = get(j0, v0, pr0["indices"]).reshape(-1, 3).astype(np.int64)
iac = j["accessors"][pr["indices"]]; I = get(j, views, pr["indices"]).reshape(-1, 3).astype(np.int64).copy()
P = get(j, views, pr["attributes"]["POSITION"]).astype(float)
assert len(I0) == len(I), "삼각형 수가 달라 맞출 수 없음"
gone = (I[:, 0] == I[:, 1]) & (I[:, 1] == I[:, 2]) & ~((I0[:, 0] == I0[:, 1]) & (I0[:, 1] == I0[:, 2]))
sk = j["skins"][0]; names = [j["nodes"][q]["name"] for q in sk["joints"]]
ibm = get(j, views, sk["inverseBindMatrices"]).reshape(-1, 4, 4).astype(float)
JP = {nm: np.linalg.inv(m.T)[:3, 3] for nm, m in zip(names, ibm)}
cen = P[I0].mean(1); back = np.zeros(len(I), bool)
for s in ("L", "R"):
    if f"Hand.{s}" not in JP: continue
    w0 = JP[f"Hand.{s}"]; roots = [JP[f"{f}1.{s}"] for f in ("Index", "Middle", "Ring", "Little") if f"{f}1.{s}" in JP]
    dv = np.mean(roots, 0) - w0; dv /= np.linalg.norm(dv)
    knuckle = max(float((r - w0) @ dv) for r in roots)              # 손가락 뿌리 관절 중 가장 먼 것
    near = np.linalg.norm(cen - w0, axis=1) < 0.2
    far = (P[I0] - w0) @ dv                                         # 세 꼭짓점 모두 손가락 뿌리 + 여유 안쪽이면 되살림
    back |= gone & near & (far.max(1) < knuckle + MARGIN)
I[back] = I0[back]
print(f"손에서 잘려 나간 삼각형 {int((gone & (np.linalg.norm(cen - JP.get('Hand.R', cen[0]), axis=1) < 0.2)).sum() + (gone & (np.linalg.norm(cen - JP.get('Hand.L', cen[0]), axis=1) < 0.2)).sum())}개 중 손등·손바닥 {int(back.sum())}개 되살림")
dt = np.dtype(COMP[iac["componentType"]])
nb = I.reshape(-1).astype(dt).tobytes(); vi = iac["bufferView"]; off = iac.get("byteOffset", 0)
buf = bytearray(views[vi]); buf[off:off + len(nb)] = nb; views[vi] = bytes(buf)
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
