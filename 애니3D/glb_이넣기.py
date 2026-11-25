"""GLB 아나운서에 이(윗니·아랫니)를 넣어 새 GLB 로 저장 (사용자 2026-11-25 '3D 여자아나운서로 사용하게')
   모델엔 입 안이 어두운 면뿐 → 입술 안쪽 곡선을 따라 가지런한 윗니 8·아랫니 8 을 'Teeth' 부품으로 추가.
   머리뼈(Head)에 붙고, 아랫니는 모양 키 MouthOpen 으로 아랫입술을 따라 내려감 → three.js·블렌더 등 어디서 열어도 이가 있음.
   모양·자리는 실사3D/야외_오르빗.py --이 와 같음(그 스크립트는 GLB 에 Teeth 가 있으면 다시 만들지 않음).
   사용: .bpy_venv/bin/python -I 애니3D/glb_이넣기.py <입력.glb> <출력.glb> [--이밝기 0.92]"""
import json, math, struct, sys
import numpy as np
import bpy, bmesh, mathutils

a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
src, dst = a[0], a[1]
IA = float(a[a.index("--이밝기") + 1]) if "--이밝기" in a else 0.92

raw = open(src, "rb").read()
jl = struct.unpack("<I", raw[12:16])[0]; g = json.loads(raw[20:20 + jl])
bo = 20 + jl; bl = struct.unpack("<I", raw[bo:bo + 4])[0]; binb = bytearray(raw[bo + 8:bo + 8 + bl])
if any(m.get("name") == "Teeth" for m in g["meshes"]):
    sys.exit("이미 Teeth 가 있음")

# ── 블렌더로 불러와 이 모양 만들기 (야외_오르빗 --이 와 같은 계산) ──
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
objs = list(bpy.data.objects)
body_ = max((o for o in objs if o.type == "MESH"), key=lambda o: len(o.data.vertices))
mi_ = next(o for o in objs if o.type == "MESH" and o.name.startswith("Mouth_Inside"))
bw = [mi_.matrix_world @ mathutils.Vector(c) for c in mi_.bound_box]
S = (max(v.x for v in bw) - min(v.x for v in bw)) / 0.0417
cx = (max(v.x for v in bw) + min(v.x for v in bw)) / 2
yfront = min(v.y for v in bw); zline = min(v.z for v in bw)
kbs = body_.data.shape_keys.key_blocks; mwb = body_.matrix_world; R3 = mwb.to_3x3()
best = mathutils.Vector((0, 0, 0))
for v0, v1 in zip(kbs["Basis"].data, kbs["MouthOpen"].data):
    w = mwb @ v0.co
    if abs(w.x - cx) < 0.004 * S and zline - 0.008 * S < w.z < zline:
        d = R3 @ (v1.co - v0.co)
        if d.length > best.length: best = d

def row(widths, front, c, z_edge, height, up):
    bm = bmesh.new(); xs = []; x = 0.0; gap = 0.00012 * S
    for i, w in enumerate(widths):
        for sg in (1, -1): xs.append((sg * (x + w / 2), w, i))
        x += w + gap
    for xc, w, i in xs:
        yc = front + c * xc * xc; ang = math.atan(2 * c * xc)
        h = height[i]; ze = z_edge + 0.00025 * S * i * (1 if up else -1)
        th = 0.0042 * S * (1 - 0.1 * i)
        for v in bmesh.ops.create_cube(bm, size=1.0)["verts"]:
            lx, ly, lz = v.co.x * (w - gap), v.co.y * th, v.co.z * h
            lx *= 1 - 0.18 * (lz / h + 0.5 if up else 0.5 - lz / h)
            px = cx + xc + lx * math.cos(ang) - ly * math.sin(ang); py = yc + ly * math.cos(ang) + lx * math.sin(ang)
            pz = (ze + h / 2 + lz) if up else (ze - h / 2 + lz)
            v.co = mathutils.Vector((px, py + th / 2, pz))
    bmesh.ops.bevel(bm, geom=list(bm.verts) + list(bm.edges), offset=0.0005 * S, segments=3, affect="EDGES")
    bmesh.ops.triangulate(bm, faces=bm.faces)
    bm.normal_update()
    inv = mwb.inverted(); inv3 = inv.to_3x3()
    P = np.array([tuple(inv @ v.co) for v in bm.verts], np.float32)
    N = np.array([tuple((inv3 @ v.normal).normalized()) for v in bm.verts], np.float32)
    idx = {v: k for k, v in enumerate(bm.verts)}
    F = np.array([[idx[l.vert] for l in f.loops] for f in bm.faces], np.uint32)
    bm.free(); return P, N, F

C = 31.0 / S
Pu, Nu, Fu = row([0.0056 * S, 0.0046 * S, 0.0046 * S, 0.0038 * S], yfront + 0.0030 * S, C * 1.15,
                 zline - 0.0014 * S, [0.0080 * S, 0.0070 * S, 0.0075 * S, 0.0065 * S], True)
Pl, Nl, Fl = row([0.0040 * S, 0.0042 * S, 0.0045 * S, 0.0040 * S], yfront + 0.0055 * S, C * 1.3,
                 zline + 0.0003 * S, [0.0045 * S, 0.0045 * S, 0.0046 * S, 0.0042 * S], False)
dl = np.array(tuple(R3.inverted() @ (best * 0.85)), np.float32)
P = np.vstack([Pu, Pl]); N = np.vstack([Nu, Nl]); F = np.vstack([Fu, Fl + len(Pu)])
D = np.zeros_like(P); D[len(Pu):] = dl

# 블렌더(z 위, -y 앞) → glTF(y 위, +z 앞): (x, y, z) → (x, z, -y). 몸 부품 점과 같은 공간인지 확인
def to_gl(A): return np.stack([A[:, 0], A[:, 2], -A[:, 1]], 1).astype(np.float32)
acc0 = g["accessors"][g["meshes"][0]["primitives"][0]["attributes"]["POSITION"]]; bv0 = g["bufferViews"][acc0["bufferView"]]
p0 = np.frombuffer(bytes(binb[bv0.get("byteOffset", 0) + acc0.get("byteOffset", 0):][:12]), np.float32).copy()
b0 = np.array(tuple(body_.data.vertices[0].co), np.float32)
print("확인: glTF 첫 점", p0.round(4), "블렌더 첫 점→glTF", to_gl(b0[None])[0].round(4))
P, N, D = to_gl(P), to_gl(N), to_gl(D)

# ── GLB 에 붙이기 ──
def add_view(arr, target=None):
    while len(binb) % 4: binb.append(0)
    off = len(binb); binb.extend(arr.tobytes())
    v = {"buffer": 0, "byteOffset": off, "byteLength": arr.nbytes}
    if target: v["target"] = target
    g["bufferViews"].append(v); return len(g["bufferViews"]) - 1
def add_acc(arr, ctype, typ, target=34962, minmax=False, norm=False):
    acc = {"bufferView": add_view(arr, target), "componentType": ctype, "count": len(arr), "type": typ}
    if minmax: acc["min"] = arr.min(0).tolist(); acc["max"] = arr.max(0).tolist()
    if norm: acc["normalized"] = True
    g["accessors"].append(acc); return len(g["accessors"]) - 1
head = next(k for k, j in enumerate(g["skins"][0]["joints"]) if g["nodes"][j].get("name") == "Head")
J = np.zeros((len(P), 4), np.uint8); J[:, 0] = head
W = np.zeros((len(P), 4), np.uint8); W[:, 0] = 255
attrs = {"POSITION": add_acc(P, 5126, "VEC3", minmax=True), "NORMAL": add_acc(N, 5126, "VEC3"),
         "JOINTS_0": add_acc(J, 5121, "VEC4"), "WEIGHTS_0": add_acc(W, 5121, "VEC4", norm=True)}
tgt = {"POSITION": add_acc(D, 5126, "VEC3", minmax=True)}
ind = add_acc(F.reshape(-1).astype(np.uint32), 5125, "SCALAR", target=34963)
g["materials"].append({"name": "Teeth", "pbrMetallicRoughness": {"baseColorFactor": [0.86 * IA, 0.84 * IA, 0.78 * IA, 1.0],
                                                                 "metallicFactor": 0.0, "roughnessFactor": 0.32}})
g["meshes"].append({"name": "Teeth", "primitives": [{"attributes": attrs, "indices": ind, "material": len(g["materials"]) - 1,
                                                     "targets": [tgt]}], "weights": [0.0], "extras": {"targetNames": ["MouthOpen"]}})
g["nodes"].append({"name": "Teeth", "mesh": len(g["meshes"]) - 1, "skin": 0})
g["scenes"][g.get("scene", 0)]["nodes"].append(len(g["nodes"]) - 1)
g["buffers"][0]["byteLength"] = len(binb)
while len(binb) % 4: binb.append(0)
js = json.dumps(g, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
while len(js) % 4: js += b" "
out = struct.pack("<4sII", b"glTF", 2, 12 + 8 + len(js) + 8 + len(binb)) + struct.pack("<I4s", len(js), b"JSON") + js + struct.pack("<I4s", len(binb), b"BIN\0") + bytes(binb)
open(dst, "wb").write(out)
print(f"이: 점 {len(P)}개 · 면 {len(F)}개 · 입 너비 비율 {S:.2f} · 아랫니 벌림 {np.linalg.norm(dl) * 100:.2f}cm → {dst}")
