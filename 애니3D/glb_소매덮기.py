"""소매 끝 밖 손목을 안감 색으로 덮어 굵은 손목 밑동을 가림 (사용자 2026-11-25 '안감으로 손목이 굵은 것을 커버')
   면 단위로 색을 바꾸면 경계가 톱니처럼 들쭉날쭉했음 → 피부 그림(텍스처)에 직접 칠함: 그림 점마다 3D 자리를 구해
   아래팔 축을 따라 소매 끝에서 --덮기 만큼까지 칠하고, 경계는 --부드럽게 폭으로 섞어 소매 끝과 나란한 매끈한 선이 되게.
   색: --색 안감(기본, 소매 겉감 평균색 × 0.55) | 자켓(겉감 평균색) | 'r,g,b'(0~1 sRGB)
   사용: python 애니3D/glb_소매덮기.py <입력.glb> <출력.glb> [--덮기 0.012] [--덮기L 0.02] [--부드럽게 0.0015] [--색 안감]"""
import io, json, struct, sys
import numpy as np
from PIL import Image

a = sys.argv[1:]; src, dst = a[0], a[1]
COVER = float(a[a.index("--덮기") + 1]) if "--덮기" in a else 0.012
SOFT = float(a[a.index("--부드럽게") + 1]) if "--부드럽게" in a else 0.0015
COLOR = a[a.index("--색") + 1] if "--색" in a else "안감"
SIDE_COVER = {}                                                   # --덮기L 0.02 / --덮기R … : 한쪽 손만 다르게 (사용자 2026-11-25 '옆으로 펼친 손은 블라우스가 손목을 조금 더 감싸게')
for sd_ in ("L", "R"):
    if f"--덮기{sd_}" in a: SIDE_COVER[sd_] = float(a[a.index(f"--덮기{sd_}") + 1])
raw = open(src, "rb").read()
jl = struct.unpack("<I", raw[12:16])[0]; g = json.loads(raw[20:20 + jl])
bo = 20 + jl; bl = struct.unpack("<I", raw[bo:bo + 4])[0]; binb = bytes(raw[bo + 8:bo + 8 + bl])
CT = {5121: np.uint8, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}; NC = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}
def view(ai):
    acc = g["accessors"][ai]; bv = g["bufferViews"][acc["bufferView"]]; dt = np.dtype(CT[acc["componentType"]]); n = NC[acc["type"]]
    off = bv.get("byteOffset", 0) + acc.get("byteOffset", 0)
    return np.frombuffer(binb, dt, acc["count"] * n, off).reshape(acc["count"], n)
sk = g["skins"][0]; name = {k: g["nodes"][j]["name"] for k, j in enumerate(sk["joints"])}
ibm = view(sk["inverseBindMatrices"]).reshape(-1, 4, 4).transpose(0, 2, 1)
pos = {name[k]: np.linalg.inv(ibm[k].astype(float))[:3, 3] for k in name}
p = g["meshes"][0]["primitives"][0]
P = view(p["attributes"]["POSITION"]).astype(float); UV = view(p["attributes"]["TEXCOORD_0"]).astype(float); F = view(p["indices"]).reshape(-1, 3)
m = g["materials"][p["material"]]; ti = m["pbrMetallicRoughness"]["baseColorTexture"]["index"]; ii = g["textures"][ti]["source"]
ibv = g["bufferViews"][g["images"][ii]["bufferView"]]; o_ = ibv.get("byteOffset", 0)
img = Image.open(io.BytesIO(binb[o_:o_ + ibv["byteLength"]])).convert("RGB"); tex = np.asarray(img).astype(np.float32) / 255; TH, TW = tex.shape[:2]
def tcol(uv): return tex[(uv[:, 1] * (TH - 1)).astype(int).clip(0, TH - 1), (uv[:, 0] * (TW - 1)).astype(int).clip(0, TW - 1)]
C = P[F].mean(1); cu = UV[F].mean(1); br = tcol(cu).mean(1)
out = tex.copy(); total = 0
for sd in ("L", "R"):
    h, f = pos[f"Hand.{sd}"], pos[f"ForeArm.{sd}"]; ax = (h - f) / np.linalg.norm(h - f)
    d = (C - h) @ ax; r = np.linalg.norm((C - h) - np.outer(d, ax), axis=1)
    near = (d > -0.07) & (d < 0.03) & (r < 0.07); sleeve = near & (br <= 0.35) & (r > 0.02)
    cuff = d[sleeve].max(); jac = tcol(cu[sleeve]).mean(0)
    col = jac * 0.55 if COLOR == "안감" else jac if COLOR == "자켓" else np.array([float(v) for v in COLOR.split(",")])
    edge = cuff + SIDE_COVER.get(sd, COVER)
    tris = np.where(near & (br > 0.35) & (d > cuff - 0.006) & (d < edge + 0.008))[0]        # 피부 면만 (자켓 테두리에 묻지 않게)
    dv = (P - h) @ ax                                          # 점마다 축 위 거리
    for t in tris:
        i0, i1, i2 = F[t]; uv = UV[[i0, i1, i2]] * [TW - 1, TH - 1]; dd = dv[[i0, i1, i2]]
        x0, y0 = np.floor(uv.min(0)).astype(int); x1, y1 = np.ceil(uv.max(0)).astype(int)
        if x1 - x0 > 200 or y1 - y0 > 200: continue
        xs, ys = np.meshgrid(np.arange(x0, x1 + 1), np.arange(y0, y1 + 1)); pts = np.stack([xs.ravel() + 0.5, ys.ravel() + 0.5], 1)
        T_ = np.array([[uv[0, 0] - uv[2, 0], uv[1, 0] - uv[2, 0]], [uv[0, 1] - uv[2, 1], uv[1, 1] - uv[2, 1]]])
        if abs(np.linalg.det(T_)) < 1e-9: continue
        l12 = np.linalg.solve(T_, (pts - uv[2]).T).T; l3 = 1 - l12.sum(1); L = np.column_stack([l12, l3])
        ins = (L >= -0.02).all(1)
        if not ins.any(): continue
        dp = L[ins] @ dd; wgt = np.clip((edge - dp) / SOFT + 0.5, 0, 1)          # 소매 쪽 1 → 경계에서 부드럽게 0
        px = pts[ins].astype(int); px[:, 0] = px[:, 0].clip(0, TW - 1); px[:, 1] = px[:, 1].clip(0, TH - 1)
        yy, xx = px[:, 1], px[:, 0]; cur = out[yy, xx]
        out[yy, xx] = cur * (1 - wgt[:, None]) + col * wgt[:, None]
        total += int((wgt > 0).sum())
    print(f"{sd}: 소매 끝 d={cuff:+.4f} → {edge:+.4f} 까지 덮음, 색(sRGB) {np.round(col, 3)}")
print("칠한 그림 점", total)
bufimg = io.BytesIO(); Image.fromarray((out * 255 + 0.5).clip(0, 255).astype(np.uint8)).save(bufimg, "JPEG", quality=95); newimg = bufimg.getvalue()
# 버퍼를 다시 짬(바꾼 그림만 새 바이트로)
nb = bytearray(); target = g["images"][ii]["bufferView"]
for k, bv in enumerate(g["bufferViews"]):
    o = bv.get("byteOffset", 0); data = newimg if k == target else binb[o:o + bv["byteLength"]]
    while len(nb) % 4: nb.append(0)
    bv["byteOffset"] = len(nb); bv["byteLength"] = len(data); nb.extend(data)
while len(nb) % 4: nb.append(0)
g["buffers"][0]["byteLength"] = len(nb)
js = json.dumps(g, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
while len(js) % 4: js += b" "
open(dst, "wb").write(struct.pack("<4sII", b"glTF", 2, 12 + 8 + len(js) + 8 + len(nb)) + struct.pack("<I4s", len(js), b"JSON") + js
                      + struct.pack("<I4s", len(nb), b"BIN\0") + bytes(nb))
print("→", dst)
