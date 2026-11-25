"""손목 가늘게 (사용자 2026-11-25 '손목이 굵음' — 손을 들어 안내할 때 소매에서 나온 손목이 손바닥만큼 넓어 보였음)
   잰 것(GLB 단위): 손목 관절 근처 단면 폭 85~96 × 두께 55 — 손바닥 폭(엄지 포함 약 120)의 3/4 이 넘음
   고침: 피부(밝은 그림) 점만, 아래팔 축 둘레로 단면의 넓은 쪽은 --폭(기본 0.80), 좁은 쪽은 --두께(기본 0.92) 배로 줄임.
         관절 앞 1.5cm ~ 관절 0.5cm 뒤가 가장 많이, 소매 속 3.5cm·손바닥 3.5cm 까지 부드럽게 줄어듦. 소매(어두운 그림) 점은 그대로.
   사용: python 애니3D/glb_손목가늘게.py <입력.glb> <출력.glb> [--폭 0.80] [--두께 0.92]"""
import io, json, struct, sys
import numpy as np
from PIL import Image

a = sys.argv[1:]; src, dst = a[0], a[1]
SW = float(a[a.index("--폭") + 1]) if "--폭" in a else 0.80
ST = float(a[a.index("--두께") + 1]) if "--두께" in a else 0.92
raw = open(src, "rb").read()
jl = struct.unpack("<I", raw[12:16])[0]; g = json.loads(raw[20:20 + jl])
bo = 20 + jl; bl = struct.unpack("<I", raw[bo:bo + 4])[0]; binb = bytearray(raw[bo + 8:bo + 8 + bl])
CT = {5121: np.uint8, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}; NC = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}
def view(ai, write=False):
    acc = g["accessors"][ai]; bv = g["bufferViews"][acc["bufferView"]]; dt = np.dtype(CT[acc["componentType"]]); n = NC[acc["type"]]
    off = bv.get("byteOffset", 0) + acc.get("byteOffset", 0)
    if write: return np.ndarray((acc["count"], n), dt, buffer=binb, offset=off)
    return np.frombuffer(bytes(binb[off:off + acc["count"] * n * dt.itemsize]), dt).reshape(acc["count"], n)
sk = g["skins"][0]; name = {k: g["nodes"][j]["name"] for k, j in enumerate(sk["joints"])}
ibm = view(sk["inverseBindMatrices"]).reshape(-1, 4, 4).transpose(0, 2, 1)
pos = {name[k]: np.linalg.inv(ibm[k].astype(float))[:3, 3] for k in name}
p = g["meshes"][0]["primitives"][0]
m = g["materials"][p["material"]]; ti = m["pbrMetallicRoughness"]["baseColorTexture"]["index"]
im = g["images"][g["textures"][ti]["source"]]; bv = g["bufferViews"][im["bufferView"]]; o_ = bv.get("byteOffset", 0)
tex = np.asarray(Image.open(io.BytesIO(bytes(binb[o_:o_ + bv["byteLength"]]))).convert("RGB")).astype(float) / 255; TH, TW = tex.shape[:2]
Pw = view(p["attributes"]["POSITION"], write=True); P = Pw.astype(float); UV = view(p["attributes"]["TEXCOORD_0"]).astype(float)
br = tex[(UV[:, 1] * (TH - 1)).astype(int).clip(0, TH - 1), (UV[:, 0] * (TW - 1)).astype(int).clip(0, TW - 1)].mean(1)
def bump(d):                                                   # 1: -0.015~+0.005, 0: -0.035 이하·+0.035 이상
    u = np.where(d < -0.015, (d + 0.035) / 0.02, np.where(d > 0.005, (0.035 - d) / 0.03, 1.0)); u = np.clip(u, 0, 1); return u * u * (3 - 2 * u)
for sd in ("L", "R"):
    h, f = pos[f"Hand.{sd}"], pos[f"ForeArm.{sd}"]; ax = (h - f) / np.linalg.norm(h - f)
    d = (P - h) @ ax; v = (P - h) - np.outer(d, ax); r = np.linalg.norm(v, axis=1)
    sl = (np.abs(d + 0.005) < 0.006) & (r < 0.07) & (br > 0.35)
    e, vec = np.linalg.eigh(np.cov(v[sl].T)); wide, thin = vec[:, 2], vec[:, 1]       # 단면의 넓은 쪽·좁은 쪽
    sel = (d > -0.035) & (d < 0.035) & (r < 0.07) & (br > 0.35)
    w = bump(d[sel]); vw = v[sel] @ wide; vt = v[sel] @ thin
    P[sel] += np.outer(vw * (SW - 1) * w, wide) + np.outer(vt * (ST - 1) * w, thin)
    print(f"{sd}: 피부 점 {sel.sum()}개, 폭 ×{SW} 두께 ×{ST} (가장 많이 줄인 곳)")
Pw[:] = P.astype(np.float32)
acc = g["accessors"][p["attributes"]["POSITION"]]; acc["min"] = P.min(0).tolist(); acc["max"] = P.max(0).tolist()
js = json.dumps(g, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
while len(js) % 4: js += b" "
open(dst, "wb").write(struct.pack("<4sII", b"glTF", 2, 12 + 8 + len(js) + 8 + len(binb)) + struct.pack("<I4s", len(js), b"JSON") + js
                      + struct.pack("<I4s", len(binb), b"BIN\0") + bytes(binb))
print("→", dst)
