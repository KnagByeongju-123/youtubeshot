"""GLB 인물 A 의 머리(목 위: 얼굴·머리카락·이·입속)를 GLB 인물 B 의 몸에 옮겨 붙임 (사용자 2026-11-26 '여자아나운서2의 얼굴을 여자아나운서1의 얼굴로')
   - A 머리 = 높이 --자르기 위의 그물(A 좌표). 크기·자리는 얼굴 표지 두 개로 맞춤: 턱 끝 높이(--턱 A,B)와 코끝 앞쪽(--코앞 A,B), 배율 --배율
     (정면 가운데 줄의 앞쪽 윤곽으로 찾음: 목→턱 끝에서 앞으로 확 튀어나오는 곳, 가장 앞 = 코끝)
   - B 쪽은 머리 재질(--지울재질, 이름에 들어간 글자)의 --지우기 높이 위 점과, 속눈썹·이·머리카락 재질(--지울재질2)의 --지우기2 위 점을 지움
   - 옮긴 머리는 B 뼈대에 묶음: 목 아래쪽은 Neck, 위로 갈수록 Head (--목섞기 z0,z1, B 좌표)
   - 모양 키(MouthOpen·MouthWide·MouthRound·Blink)는 A 것을 그대로 가져감
   사용: .bpy_venv/bin/python -I 애니3D/얼굴바꾸기.py <A.glb> <B.glb> <결과.glb> --자르기 0.625 --턱 0.663,1.508 --코앞 -0.116,-0.072 --배율 0.92
         [--지우기 1.478] [--지울재질 head] [--지울재질2 opacity] [--지우기2 1.45] [--목섞기 1.48,1.53] [--머리카락아래 0.55] [--옷위 0.06] [--목색 on|off] [--머리뼈 Head] [--목뼈 Neck]"""
import os, sys
import bpy, bmesh
import numpy as np
from mathutils import Matrix

a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
srcA, srcB, dst = a[0], a[1], a[2]
def opt(k, d): return a[a.index(k) + 1] if k in a else d
CUT = float(opt("--자르기", "0.625")); S = float(opt("--배율", "0.92"))
CA, CB = (float(v) for v in opt("--턱", "0.663,1.508").split(","))
NA, NB = (float(v) for v in opt("--코앞", "-0.116,-0.072").split(","))
DEL = float(opt("--지우기", "1.478")); DEL2 = float(opt("--지우기2", "1.45"))
M1, M2 = opt("--지울재질", "head"), opt("--지울재질2", "opacity")
N0, N1 = (float(v) for v in opt("--목섞기", "1.48,1.53").split(","))
HEAD, NECK = opt("--머리뼈", "Head"), opt("--목뼈", "Neck")
BACKY = float(opt("--뒷머리y", "0.13"))      # B 머리 재질 중 이보다 뒤(y)는 머리 뒤 꽁지머리 → 지움
CLOTHUP = float(opt("--옷위", "0.06"))      # 자르기 위 이만큼까지 옷 색 점을 지움
NECKCOL = []
HAIRLOW = float(opt("--머리카락아래", "9"))     # 이 높이(A 좌표)까지는 머리카락 색 점을 남김 (예: 0.55)

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.abspath(srcB))
objsB = set(bpy.data.objects)
armB = next(o for o in objsB if o.type == "ARMATURE")
bodyB = max((o for o in objsB if o.type == "MESH" and o.name != "Icosphere"), key=lambda o: len(o.data.vertices))
bpy.ops.import_scene.gltf(filepath=os.path.abspath(srcA))
objsA = set(bpy.data.objects) - objsB
bpy.context.view_layer.update()

# A 머리 조각: 모든 그물(얼굴·몸, 이, 입속)을 세상 좌표로 굳히고 자르기 아래를 지움 → 배율·이동 → B 뼈대에 묶음
T = Matrix.Translation((0, NB - NA * S, CB)) @ Matrix.Scale(S, 4) @ Matrix.Translation((0, 0, -CA))
keep = []
for o in sorted(objsA, key=lambda x: x.name):
    if o.type != "MESH" or o.name.startswith("Icosphere"): continue
    for m in list(o.modifiers): o.modifiers.remove(m)
    mw = o.matrix_world.copy(); o.parent = None; o.matrix_world = Matrix()
    o.data.transform(mw, shape_keys=True)
    hairv = set(); clothv = set()
    if o.data.uv_layers and o.data.materials:      # 머리카락 끝은 자르기 아래까지 살림(그림 색이 갈색·어두움, 파랑 옷·흰 셔츠·피부는 빼고)
        img = next((n.image for m in o.data.materials if m and m.node_tree for n in m.node_tree.nodes if n.type == "TEX_IMAGE" and n.image), None)
        if img is not None:
            W_, H_ = img.size; px = np.empty(W_ * H_ * 4, np.float32); img.pixels.foreach_get(px); px = px.reshape(H_, W_, 4)
            uvd = o.data.uv_layers.active.data
            for lp in o.data.loops:
                v = lp.vertex_index; co_ = o.data.vertices[v].co; z = co_.z
                if z < HAIRLOW or v in hairv or z > CUT + CLOTHUP: continue
                u, w = uvd[lp.index].uv; r, g, b = px[min(int(w * H_), H_ - 1) % H_, min(int(u * W_), W_ - 1) % W_, :3]
                mx, mn = max(r, g, b), min(r, g, b)
                if z >= CUT:                    # 자르기 위 옷(남색 재킷 깃·흰 셔츠)은 빼고, 목 앞 피부색은 모음
                    if (b > r + 0.01) or (mn > 0.75 and mx - mn < 0.06 and abs(co_.x) > 0.04): clothv.add(v)
                    elif abs(co_.x) < 0.035 and co_.y < 0 and z < CUT + 0.03: NECKCOL.append((r, g, b))
                    continue
                if r >= g >= b and mx < 0.55 and mx - mn > 0.04 and mx > 0.04 and not (r > 0.35 and (r - b) > 0.12 and mx > 0.45): hairv.add(v)
            print("  자르기 아래 머리카락 점", len(hairv), "· 자르기 위 옷 점", len(clothv))
    bm = bmesh.new(); bm.from_mesh(o.data)
    gone = [v for v in bm.verts if (v.co.z < CUT and v.index not in hairv) or v.index in clothv]
    bmesh.ops.delete(bm, geom=gone, context="VERTS"); bm.to_mesh(o.data); bm.free()
    if not len(o.data.vertices): bpy.data.objects.remove(o); continue
    o.data.transform(T, shape_keys=True)
    o.vertex_groups.clear()
    gh, gn = o.vertex_groups.new(name=HEAD), o.vertex_groups.new(name=NECK)
    for v in o.data.vertices:
        t = min(max((v.co.z - N0) / (N1 - N0), 0.0), 1.0)
        if t > 0: gh.add([v.index], t, "REPLACE")
        if t < 1: gn.add([v.index], 1 - t, "REPLACE")
    o.parent = armB; o.matrix_parent_inverse = armB.matrix_world.inverted()
    md = o.modifiers.new("Armature", "ARMATURE"); md.object = armB
    keep.append(o); print("옮긴 조각", o.name, len(o.data.vertices), "점", "키", [k.name for k in o.data.shape_keys.key_blocks] if o.data.shape_keys else [])
for o in list(objsA):
    if o not in keep: bpy.data.objects.remove(o)

# B 머리 지우기
mw = bodyB.matrix_world; mats = [m.name.lower() if m else "" for m in bodyB.data.materials]
bm = bmesh.new(); bm.from_mesh(bodyB.data); bm.verts.ensure_lookup_table()
gone = set()
for f in bm.faces:
    nm = mats[f.material_index] if f.material_index < len(mats) else ""
    lim = DEL if M1 in nm else DEL2 if M2 in nm else None
    if lim is None: continue
    ps_ = [mw @ v.co for v in f.verts]
    if max(p.z for p in ps_) > lim or (min(p.y for p in ps_) > BACKY and max(p.z for p in ps_) > 1.2): gone.add(f)   # 뒷머리(묶은 머리)도
# 목색 맞추기: B 머리 재질 그림(남는 곳 = 목 아래·가슴)을 A 목 피부색 쪽으로 (채널마다 배율)
if NECKCOL and opt("--목색", "on") != "off":
    mi = next(i for i, m in enumerate(mats) if M1 in m); mat = bodyB.data.materials[mi]
    img = next((n.image for n in mat.node_tree.nodes if n.type == "TEX_IMAGE" and n.image and "color" in n.image.name.lower()), None) or \
          next((n.image for n in mat.node_tree.nodes if n.type == "TEX_IMAGE" and n.image), None)
    W_, H_ = img.size; px = np.empty(W_ * H_ * 4, np.float32); img.pixels.foreach_get(px); px = px.reshape(H_, W_, 4)
    uvd = bodyB.data.uv_layers.active.data; cols = []
    for poly in bodyB.data.polygons:
        if poly.material_index != mi: continue
        for li in poly.loop_indices:
            co_ = mw @ bodyB.data.vertices[bodyB.data.loops[li].vertex_index].co
            if DEL - 0.05 < co_.z < DEL and abs(co_.x) < 0.035 and co_.y < 0.02:
                u, w = uvd[li].uv; cols.append(px[min(int(w * H_), H_ - 1) % H_, min(int(u * W_), W_ - 1) % W_, :3])
    if cols:
        ga = np.median(np.array(NECKCOL), 0); gb = np.median(np.array(cols), 0); k = np.clip(ga / np.maximum(gb, 1e-3), 0.5, 2.0)
        px[..., :3] = np.clip(px[..., :3] * k, 0, 1); img.pixels.foreach_set(px.ravel())
        tmp = os.path.join(os.path.dirname(os.path.abspath(dst)), "_목색맞춤.png"); img.filepath_raw = tmp; img.file_format = "PNG"; img.save(); img.pack()
        print("목색 맞춤 A", ga.round(3), "B", gb.round(3), "배율", k.round(3))
bmesh.ops.delete(bm, geom=list(gone), context="FACES"); bm.to_mesh(bodyB.data); bm.free()
print("B 머리 면 지움", len(gone))
for o in list(bpy.data.objects):
    if o.name.startswith("Icosphere"): bpy.data.objects.remove(o)
bpy.ops.export_scene.gltf(filepath=os.path.abspath(dst), export_format="GLB", export_morph=True, export_skins=True, export_animations=False)
print("저장", dst)
