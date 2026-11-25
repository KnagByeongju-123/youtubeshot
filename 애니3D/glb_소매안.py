"""소매 안쪽을 어두운 안감 색으로 (사용자 2026-11-25 '소매 안쪽도 색상이 흰색인 듯')
   잰 것: 손목 피부(밝은 그림)가 소매 끝에서 5cm 안쪽까지 소매 속으로 이어져 있음 → 손을 들면 소매 끝 구멍으로 밝게 보임.
   고침: 아래팔 축을 따라 소매가 끝나는 자리(어두운 소매 면이 있는 가장 손 쪽)를 재고, 그보다 안쪽(팔꿈치 쪽)의 밝은 면만
         어두운 재질(틈막음_어두움, 없으면 새로 만듦)로 옮김. 점·뼈 무게·모양 키는 그대로(같은 점을 쓰는 새 묶음을 추가).
   --덮기 0.012 (사용자 2026-11-25 '안감으로 손목이 굵은 것을 커버'): 소매 끝 밖으로 이만큼의 손목 피부도 어두운 재질로 → 소매가 그만큼 길어 보여
         굵은 손목 밑동이 가려짐. --색 자켓 이면 안감 대신 소매 겉감 평균색(새 재질 '소매덮개')
   사용: python 애니3D/glb_소매안.py <입력.glb> <출력.glb> [--여유 0.0025] [--깊이 0.07] [--덮기 0] [--색 안감|자켓]"""
import io, json, struct, sys
import numpy as np
from PIL import Image

a = sys.argv[1:]; src, dst = a[0], a[1]
MARGIN = float(a[a.index("--여유") + 1]) if "--여유" in a else 0.0025      # 소매 끝에서 이만큼 안쪽부터
DEPTH = float(a[a.index("--깊이") + 1]) if "--깊이" in a else 0.07         # 손목 관절에서 팔꿈치 쪽으로 이만큼까지만
COVER = float(a[a.index("--덮기") + 1]) if "--덮기" in a else 0.0
COLOR = a[a.index("--색") + 1] if "--색" in a else "안감"
raw = open(src, "rb").read()
jl = struct.unpack("<I", raw[12:16])[0]; g = json.loads(raw[20:20 + jl])
bo = 20 + jl; bl = struct.unpack("<I", raw[bo:bo + 4])[0]; binb = bytearray(raw[bo + 8:bo + 8 + bl])
CT = {5121: np.uint8, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}; NC = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}
def view(ai):
    acc = g["accessors"][ai]; bv = g["bufferViews"][acc["bufferView"]]; dt = np.dtype(CT[acc["componentType"]]); n = NC[acc["type"]]
    off = bv.get("byteOffset", 0) + acc.get("byteOffset", 0)
    return np.frombuffer(bytes(binb[off:off + acc["count"] * n * dt.itemsize]), dt).reshape(acc["count"], n)
sk = g["skins"][0]; name = {k: g["nodes"][j]["name"] for k, j in enumerate(sk["joints"])}
ibm = view(sk["inverseBindMatrices"]).reshape(-1, 4, 4).transpose(0, 2, 1)
pos = {name[k]: np.linalg.inv(ibm[k].astype(float))[:3, 3] for k in name}
mesh = g["meshes"][0]; p = mesh["primitives"][0]
P = view(p["attributes"]["POSITION"]).astype(float); UV = view(p["attributes"]["TEXCOORD_0"]); F = view(p["indices"]).reshape(-1, 3)
m = g["materials"][p["material"]]; ti = m["pbrMetallicRoughness"]["baseColorTexture"]["index"]
im = g["images"][g["textures"][ti]["source"]]; bv = g["bufferViews"][im["bufferView"]]; o_ = bv.get("byteOffset", 0)
tex = np.asarray(Image.open(io.BytesIO(bytes(binb[o_:o_ + bv["byteLength"]]))).convert("RGB")).astype(float) / 255; TH, TW = tex.shape[:2]
C = P[F].mean(1); cu = UV[F].astype(float).mean(1)
br = tex[(cu[:, 1] * (TH - 1)).astype(int).clip(0, TH - 1), (cu[:, 0] * (TW - 1)).astype(int).clip(0, TW - 1)].mean(1)
inner = np.zeros(len(F), bool); cover = np.zeros(len(F), bool); jacket = []
for sd in ("L", "R"):
    h, f = pos[f"Hand.{sd}"], pos[f"ForeArm.{sd}"]; ax = (h - f) / np.linalg.norm(h - f)
    d = (C - h) @ ax; r = np.linalg.norm((C - h) - np.outer(d, ax), axis=1)
    near = (d > -DEPTH) & (d < 0.03) & (r < 0.07)
    sleeve = near & (br <= 0.35) & (r > 0.02)
    cuff = d[sleeve].max()                                    # 소매가 끝나는 자리(손 쪽 끝)
    sel = near & (br > 0.35) & (d < cuff - MARGIN)
    cv = near & (br > 0.35) & (d >= cuff - MARGIN) & (d < cuff + COVER) if COVER > 0 else np.zeros(len(F), bool)
    if COLOR == "자켓": cover |= cv; jacket.append(cu[sleeve])
    else: sel = sel | cv
    inner |= sel; print(f"{sd}: 소매 끝 d={cuff:+.4f}, 소매 속 밝은 면 {sel.sum()}개, 덮은 손목 면 {cv.sum()}개")
dark = next((k for k, mm in enumerate(g["materials"]) if mm.get("name") == "틈막음_어두움"), None)
if dark is None:
    g["materials"].append({"name": "소매안", "pbrMetallicRoughness": {"baseColorFactor": [0.02, 0.025, 0.04, 1], "metallicFactor": 0, "roughnessFactor": 0.9}}); dark = len(g["materials"]) - 1
def add_idx(arr):
    while len(binb) % 4: binb.append(0)
    off = len(binb); binb.extend(arr.astype(np.uint32).tobytes())
    g["bufferViews"].append({"buffer": 0, "byteOffset": off, "byteLength": arr.size * 4, "target": 34963})
    g["accessors"].append({"bufferView": len(g["bufferViews"]) - 1, "componentType": 5125, "count": int(arr.size), "type": "SCALAR"})
    return len(g["accessors"]) - 1
keep = ~inner & ~cover
if cover.any():                                               # 소매 겉감 평균색(그림 sRGB → 선형)으로 새 재질
    cuv = np.vstack(jacket); cc = tex[(cuv[:, 1] * (TH - 1)).astype(int).clip(0, TH - 1), (cuv[:, 0] * (TW - 1)).astype(int).clip(0, TW - 1)].mean(0)
    lin = [float(((c + 0.055) / 1.055) ** 2.4 if c > 0.04045 else c / 12.92) for c in cc]
    g["materials"].append({"name": "소매덮개", "pbrMetallicRoughness": {"baseColorFactor": lin + [1.0], "metallicFactor": 0, "roughnessFactor": 0.8}})
    q2 = {k: v for k, v in p.items() if k not in ("indices", "material")}; q2["indices"] = None; q2["material"] = len(g["materials"]) - 1
    print("소매덮개 색(sRGB)", np.round(cc, 3), "면", int(cover.sum()))
p["indices"] = add_idx(F[keep].reshape(-1))
q = {k: v for k, v in p.items() if k not in ("indices", "material")}; q["indices"] = add_idx(F[inner].reshape(-1)); q["material"] = dark
mesh["primitives"].append(q)
if cover.any(): q2["indices"] = add_idx(F[cover].reshape(-1)); mesh["primitives"].append(q2)
g["buffers"][0]["byteLength"] = len(binb)
while len(binb) % 4: binb.append(0)
js = json.dumps(g, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
while len(js) % 4: js += b" "
open(dst, "wb").write(struct.pack("<4sII", b"glTF", 2, 12 + 8 + len(js) + 8 + len(binb)) + struct.pack("<I4s", len(js), b"JSON") + js
                      + struct.pack("<I4s", len(binb), b"BIN\0") + bytes(binb))
print("→", dst)
