"""GLB 인물 A 의 머리(목 위: 얼굴·머리카락·이·입속)를 GLB 인물 B 의 몸에 옮겨 붙임 (사용자 2026-11-26 '여자아나운서2의 얼굴을 여자아나운서1의 얼굴로')
   - A 머리 = 높이 --자르기 위의 그물(A 좌표). 크기·자리는 얼굴 표지 두 개로 맞춤: 턱 끝 높이(--턱 A,B)와 코끝 앞쪽(--코앞 A,B), 배율 --배율
     (정면 가운데 줄의 앞쪽 윤곽으로 찾음: 목→턱 끝에서 앞으로 확 튀어나오는 곳, 가장 앞 = 코끝)
   - B 쪽은 머리 재질(--지울재질, 이름에 들어간 글자)의 --지우기 높이 위 점과, 속눈썹·이·머리카락 재질(--지울재질2)의 --지우기2 위 점을 지움
   - 옮긴 머리는 B 뼈대에 묶음: 목 아래쪽은 Neck, 위로 갈수록 Head (--목섞기 z0,z1, B 좌표)
   - 모양 키(MouthOpen·MouthWide·MouthRound·Blink)는 A 것을 그대로 가져감
   사용: .bpy_venv/bin/python -I 애니3D/얼굴바꾸기.py <A.glb> <B.glb> <결과.glb> --자르기 0.625 --턱 0.663,1.508 --코앞 -0.116,-0.072 --배율 0.92
         [--지우기 1.478] [--지울재질 head] [--지울재질2 opacity] [--지우기2 1.45] [--목섞기 1.48,1.53] [--머리카락아래 0.55] [--옷위 0.06] [--목색 on|off] [--옆자르기 0.655 --옆x 0.06] [--목조이기 0.85] [--조각 3000] [--이음 0] [--안으로 on|off] [--목색보정 1.02,1.125,1.18] [--깃띠 1.455] [--머리뼈 Head] [--목뼈 Neck]"""
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
ISLMIN = int(opt("--조각", "3000"))        # 자른 곳 근처에서 이보다 점이 적은 떨어진 조각은 지움
SIDECUT = float(opt("--옆자르기", "0"))     # |x| > --옆x 인 곳은 이 높이(A 좌표) 아래를 지움 (예: 0.655)
SIDEX = float(opt("--옆x", "0.06"))
SHRINK = float(opt("--목조이기", "1.0"))    # B 목 아래쪽(머리 재질, 남는 곳 위 4cm)을 목 가운데 쪽으로 이 배율로 오므림 → A 목 안에 숨음
COLLAR = float(opt("--깃띠", "0"))          # 몸 재질 중 이 높이(B 좌표) 위, 목 둘레 안쪽 띠를 지움 (예: 1.455)
SNAP = float(opt("--이음", "0"))
FIXCOL = np.array([float(v) for v in opt("--목색보정", "1,1,1").split(",")])   # 촬영해 보니 B 목이 더 붉게 나옴 → 그림 색에 더 곱함 (예: 1.02,1.125,1.18)
BISECT = opt("--반듯", "on") != "off"
CLOTHCO = set()
PUSHIN = opt("--안으로", "on") != "off"       # A 목 아래 끝 이만큼(A 좌표)을 B 목 표면에 붙임
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
from mathutils.bvhtree import BVHTree
_mwB = bodyB.matrix_world; _matsB = [m.name.lower() if m else "" for m in bodyB.data.materials]
_vB = [_mwB @ v.co for v in bodyB.data.vertices]
_fB = [list(f.vertices) for f in bodyB.data.polygons if M1 in _matsB[f.material_index] and 1.38 < _vB[f.vertices[0]].z < 1.52 and _vB[f.vertices[0]].y < 0.13]
neckB = BVHTree.FromPolygons(_vB, _fB) if _fB else None      # A 목 아래 끝을 붙일 B 목 표면
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
                if v in hairv or z > max(CUT + CLOTHUP, SIDECUT) or (z < CUT and z < HAIRLOW): continue
                u, w = uvd[lp.index].uv; r, g, b = px[min(int(w * H_), H_ - 1) % H_, min(int(u * W_), W_ - 1) % W_, :3]
                mx, mn = max(r, g, b), min(r, g, b)
                if CUT <= z < SIDECUT and co_.y > 0.0 and abs(co_.x) <= SIDEX and mx < 0.6 and r >= g >= b and not (mx > 0.45 and r - b > 0.15 and mn > 0.3):
                    clothv.add(v); continue     # 뒤 가운데 머리카락도 옆과 같은 높이로 (안쪽으로 말린 뒷머리가 따로 늘어져 보였음)
                if z >= CUT:                    # 자르기 위 옷(남색 재킷 깃·흰 셔츠)은 빼고, 목 앞 피부색은 모음
                    frontneck = abs(co_.x) < 0.065 and co_.y < -0.005      # 목 앞쪽은 피부 — 색으로 지우면 끝이 들쭉날쭉했음
                    if not frontneck and ((b > r + 0.01) or (mn > 0.75 and mx - mn < 0.06 and abs(co_.x) > 0.04)): clothv.add(v)
                    elif abs(co_.x) < 0.035 and co_.y < 0 and z < CUT + 0.03: NECKCOL.append((r, g, b))
                    continue
                if r >= g >= b and mx < 0.55 and mx - mn > 0.04 and mx > 0.04 and not (r > 0.35 and (r - b) > 0.12 and mx > 0.45): hairv.add(v)
            print("  자르기 아래 머리카락 점", len(hairv), "· 자르기 위 옷 점", len(clothv))
            CLOTHCO = {tuple(round(c, 5) for c in o.data.vertices[i].co) for i in clothv}
    bm = bmesh.new(); bm.from_mesh(o.data)
    if BISECT and len(bm.verts) > 10000:      # 자르는 높이에서 면을 반듯하게 갈라 끝이 톱니처럼 들쭉날쭉하지 않게 (사용자 2026-11-26 '목경계와 뒷머리카락')
        for zc in [CUT] + ([SIDECUT] if SIDECUT > CUT else []):
            bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], dist=1e-6, plane_co=(0, 0, zc), plane_no=(0, 0, 1))
        bm.verts.ensure_lookup_table(); bm.verts.index_update()
        hairv = {v.index for v in bm.verts if v.co.z < CUT - 1e-5 and False}   # (머리카락 남기기는 끔: 번호가 바뀜)
        clothv = {v.index for v in bm.verts if v.co.z >= CUT and v.co.z <= max(CUT + CLOTHUP, SIDECUT) and tuple(round(c, 5) for c in v.co) in CLOTHCO}
    gone = [v for v in bm.verts if (v.co.z < CUT - 1e-5 and v.index not in hairv) or v.index in clothv
            or (v.co.z < SIDECUT - 1e-5 and abs(v.co.x) > SIDEX)]          # 어깨 위 머리카락 끝(바깥으로 말린 곳): B 어깨가 좁아 떠 보여서 단발 끝을 고르게 자름
    bmesh.ops.delete(bm, geom=gone, context="VERTS")
    # 예전에 구멍을 메운 어두운 덧댐(재질 이름 '틈막음')은 목 둘레에 검은 띠로 보였음 → 지움 (사용자 2026-11-26 '목 이음매')
    fill_mi = {i for i, m in enumerate(o.data.materials) if m and "틈막음" in m.name}
    if fill_mi:
        ff = [f for f in bm.faces if f.material_index in fill_mi]
        bmesh.ops.delete(bm, geom=ff, context="FACES_ONLY"); print("  덧댐 면 지움", len(ff))
        lone = [v for v in bm.verts if not v.link_faces]; bmesh.ops.delete(bm, geom=lone, context="VERTS")
    # 자른 곳 근처에 떨어져 남은 작은 조각(옷 끄트머리·머리카락 부스러기·목 옆 잔재) 지우기 (사용자 2026-11-26 '옆쪽 목주변의 잔재들 삭제')
    from mathutils.kdtree import KDTree
    b2 = bm.copy() if len(bm.verts) > 10000 else bmesh.new()   # 얼굴·몸 그물만 (이·입속은 작아서 통째로 지워졌음)
    bmesh.ops.remove_doubles(b2, verts=b2.verts, dist=1e-4)   # 그림 이음선에서 같은 자리 점이 둘로 나뉘어 있음 → 붙여서 조각을 셈
    b2.verts.ensure_lookup_table(); seen = set(); smallco = []
    for v0 in b2.verts:
        if v0.index in seen: continue
        st = [v0]; isl = []; seen.add(v0.index)
        while st:
            v = st.pop(); isl.append(v)
            for e in v.link_edges:
                w_ = e.other_vert(v)
                if w_.index not in seen: seen.add(w_.index); st.append(w_)
        if len(isl) < ISLMIN and min(v.co.z for v in isl) < CUT + CLOTHUP + 0.02: smallco += [v.co.copy() for v in isl]
    b2.free(); small = []
    if smallco:
        kd = KDTree(len(smallco))
        for i, c in enumerate(smallco): kd.insert(c, i)
        kd.balance(); small = [v for v in bm.verts if kd.find(v.co)[2] < 2e-4]
    if small: bmesh.ops.delete(bm, geom=small, context="VERTS"); print("  목 근처 작은 조각 점", len(small))
    bm.to_mesh(o.data); bm.free()
    if not len(o.data.vertices): bpy.data.objects.remove(o); continue
    o.data.transform(T, shape_keys=True)
    if neckB is not None and SNAP > 0:       # 목 아래 끝(자른 곳 위 --이음 높이)을 B 목 표면으로 옮겨 이음매 없이 이어지게, 위로 갈수록 덜
        zb = CB + (CUT - CA) * S; band = SNAP * S; n_ = 0
        kb_ = o.data.shape_keys.key_blocks if o.data.shape_keys else []
        for v in o.data.vertices:
            if v.co.z < zb + band:
                hit = neckB.find_nearest(v.co)
                if hit[0] is not None and hit[3] < 0.03:
                    w_ = 1 - max(v.co.z - zb, 0) / band; d_ = (hit[0] - v.co) * w_
                    v.co += d_; n_ += 1
                    for kb in kb_: kb.data[v.index].co += d_
        print("  목 끝 B 표면에 붙인 점", n_)
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
mainA = max(keep, key=lambda x: len(x.data.vertices))
bvhA = BVHTree.FromPolygons([v.co.copy() for v in mainA.data.vertices], [list(f.vertices) for f in mainA.data.polygons])   # A 는 세상 좌표로 굳혀 둠
ZBOT = CB + (CUT - CA) * S

# B 머리 지우기
mw = bodyB.matrix_world; mats = [m.name.lower() if m else "" for m in bodyB.data.materials]
bm = bmesh.new(); bm.from_mesh(bodyB.data); bm.verts.ensure_lookup_table()
gone = set()
for f in bm.faces:
    nm = mats[f.material_index] if f.material_index < len(mats) else ""
    lim = DEL if M1 in nm else DEL2 if M2 in nm else None
    if lim is None:
        # 옷(몸 재질) 중 목을 감싸는 안쪽 띠: B 의 굵은 목 안에 숨어 있었는데 A 목이 가늘어 검은 띠로 드러났음 (사용자 2026-11-26 '목 이음매')
        if COLLAR > 0:
            ps_ = [mw @ v.co for v in f.verts]
            if min(p.z for p in ps_) > COLLAR and max(abs(p.x) for p in ps_) < 0.075 and min(p.y for p in ps_) < 0.06: gone.add(f)
        continue
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
        ga = np.median(np.array(NECKCOL), 0); gb = np.median(np.array(cols), 0); k = np.clip(ga / np.maximum(gb, 1e-3), 0.5, 2.0) * FIXCOL
        rgb_ = px[..., :3]; skin_ = ((rgb_[..., 0] > rgb_[..., 1]) & (rgb_[..., 1] > rgb_[..., 2]) & (rgb_[..., 0] > 0.3))[..., None]   # 피부만 (목걸이·옷은 그대로)
        px[..., :3] = np.where(skin_, np.clip(rgb_ * k, 0, 1), rgb_); img.pixels.foreach_set(px.ravel())
        tmp = os.path.join(os.path.dirname(os.path.abspath(dst)), "_목색맞춤.png"); img.filepath_raw = tmp; img.file_format = "PNG"; img.save(); img.pack()
        print("목색 맞춤 A", ga.round(3), "B", gb.round(3), "배율", k.round(3))
bmesh.ops.delete(bm, geom=list(gone), context="FACES")
if PUSHIN:   # 겹친 곳의 B 목을 A 목 안쪽(2mm)으로 밀어 넣음 → 틈 없이 겹치고 B 가 A 밖으로 삐져나오지 않음
    mi = next(i for i, m in enumerate(mats) if M1 in m); inv = mw.inverted(); n_ = 0
    for v in {v for f in bm.faces if f.material_index == mi for v in f.verts}:
        p = mw @ v.co
        if p.z < ZBOT - 0.004: continue
        hit = bvhA.find_nearest(p)
        if hit[0] is None or hit[3] > 0.06: continue
        nrm = hit[1]
        if (p - hit[0]).dot(nrm) > -0.002: v.co = inv @ (hit[0] - nrm * 0.002); n_ += 1
    print("B 목 안으로 넣은 점", n_)
if SHRINK < 1.0:      # A 목보다 굵은 B 목 윗부분이 A 목 밖으로 삐져나와 들쭉날쭉한 띠로 보였음 → 안쪽으로 오므림
    mi = next(i for i, m in enumerate(mats) if M1 in m); inv = mw.inverted()
    vs = {v for f in bm.faces if f.material_index == mi for v in f.verts if (mw @ v.co).z > CB + (CUT - CA) * S}
    if vs:
        yc = sum((mw @ v.co).y for v in vs) / len(vs)
        for v in vs:
            p = mw @ v.co; z0_ = CB + (CUT - CA) * S + 0.002; t = min(max((p.z - z0_) / 0.012, 0), 1); k = 1 - (1 - SHRINK) * t
            p.x *= k; p.y = yc + (p.y - yc) * k; v.co = inv @ p
        print("B 목 오므림 점", len(vs))
bm.to_mesh(bodyB.data); bm.free()
print("B 머리 면 지움", len(gone))
for o in list(bpy.data.objects):
    if o.name.startswith("Icosphere"): bpy.data.objects.remove(o)
bpy.ops.export_scene.gltf(filepath=os.path.abspath(dst), export_format="GLB", export_morph=True, export_skins=True, export_animations=False)
print("저장", dst)
