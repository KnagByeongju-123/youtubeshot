"""GLB 인물 A 의 머리(목 위: 얼굴·머리카락·이·입속)를 GLB 인물 B 의 몸에 옮겨 붙임 (사용자 2026-11-26 '여자아나운서2의 얼굴을 여자아나운서1의 얼굴로')
   - A 머리 = 높이 --자르기 위의 그물(A 좌표). 크기·자리는 얼굴 표지 두 개로 맞춤: 턱 끝 높이(--턱 A,B)와 코끝 앞쪽(--코앞 A,B), 배율 --배율
     (정면 가운데 줄의 앞쪽 윤곽으로 찾음: 목→턱 끝에서 앞으로 확 튀어나오는 곳, 가장 앞 = 코끝)
   - B 쪽은 머리 재질(--지울재질, 이름에 들어간 글자)의 --지우기 높이 위 점과, 속눈썹·이·머리카락 재질(--지울재질2)의 --지우기2 위 점을 지움
   - 옮긴 머리는 B 뼈대에 묶음: 목 아래쪽은 Neck, 위로 갈수록 Head (--목섞기 z0,z1, B 좌표)
   - 모양 키(MouthOpen·MouthWide·MouthRound·Blink)는 A 것을 그대로 가져감
   사용: .bpy_venv/bin/python -I 애니3D/얼굴바꾸기.py <A.glb> <B.glb> <결과.glb> --자르기 0.625 --턱 0.663,1.508 --코앞 -0.116,-0.072 --배율 0.92
         [--지우기 1.478] [--지울재질 head] [--지울재질2 opacity] [--지우기2 1.45] [--목섞기 1.48,1.53] [--머리카락아래 0.55] [--옷위 0.06] [--목색 on|off] [--옆자르기 0.655 --옆x 0.06] [--목조이기 0.85] [--조각 3000] [--이음 0.016] [--안으로 on|off] [--목색보정 1.02,1.125,1.18] [--목띠 0.025] [--목걸이 on|off] [--깃띠 1.455] [--머리뼈 Head] [--목뼈 Neck]"""
import os, sys
import bpy, bmesh
import numpy as np
from mathutils import Matrix, Vector as _V

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
SNAP = float(opt("--이음", "0.016"))
FIXCOL = np.array([float(v) for v in opt("--목색보정", "1,1,1").split(",")])   # 촬영해 보니 B 목이 더 붉게 나옴 → 그림 색에 더 곱함 (예: 1.02,1.125,1.18)
FEATHER = float(opt("--목띠", "0.025"))     # A 목 아래 이 높이(A 좌표)를 깨끗한 목 색으로 섞음 (0 = 끔)
NECKLACE = opt("--목걸이", "on") != "off"
FILLHOLE = opt("--구멍메우기", "on") != "off"
BISECT = opt("--반듯", "on") != "off"
CLOTHCO = set()
NECKCY = 0.036
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
                if CUT <= z < SIDECUT and (co_.y > 0.0 or abs(co_.x) > SIDEX) and mx < 0.6 and r >= g >= b and not (mx > 0.45 and r - b > 0.15 and mn > 0.3):
                    clothv.add(v); continue     # 뒤 가운데 머리카락도 옆과 같은 높이로 (안쪽으로 말린 뒷머리가 따로 늘어져 보였음)
                if z >= CUT:                    # 자르기 위 옷(남색 재킷 깃·흰 셔츠)은 빼고, 목 앞 피부색은 모음
                    frontneck = abs(co_.x) < 0.065 and co_.y < -0.005      # 목 앞쪽은 피부 — 색으로 지우면 끝이 들쭉날쭉했음
                    darkcloth = mx < 0.4 and b >= r - 0.02 and not (abs(co_.x) < 0.07 and co_.y < 0.03)   # 짙은 남색 재킷 깃 — 목 앞·옆 피부의 어두운 자국은 빼고(지웠더니 목 옆에 구멍)
                    if darkcloth or (not frontneck and ((b > r + 0.01) or (mn > 0.75 and mx - mn < 0.06 and abs(co_.x) > 0.04))): clothv.add(v)
                    elif abs(co_.x) < 0.035 and co_.y < 0 and CUT + 0.03 < z < CUT + 0.06: NECKCOL.append((r, g, b))   # 깨끗한 목 피부(아래 띠는 셔츠 깃 그림자 얼룩)
                    continue
                if r >= g >= b and mx < 0.55 and mx - mn > 0.04 and mx > 0.04 and not (r > 0.35 and (r - b) > 0.12 and mx > 0.45): hairv.add(v)
            print("  자르기 아래 머리카락 점", len(hairv), "· 자르기 위 옷 점", len(clothv))
            CLOTHCO = {tuple(round(c, 5) for c in o.data.vertices[i].co) for i in clothv}
            if FEATHER > 0 and NECKCOL:      # 목 아래 띠(--목띠 높이)의 그림 색을 깨끗한 목 색으로 점점 섞음 — 하얀 얼룩·경계선 없앰 (사용자 2026-11-26 앞목 경계 표시)
                tgt = np.median(np.array(NECKCOL), 0); n_ = 0; done_ = np.zeros((H_, W_), bool)
                V_ = o.data.vertices
                for poly in o.data.polygons:
                    zs_ = [V_[i].co.z for i in poly.vertices]
                    if min(zs_) > CUT + FEATHER or max(zs_) < CUT - 0.01: continue
                    lis = list(poly.loop_indices)
                    for t_ in range(1, len(lis) - 1):
                        tri = [lis[0], lis[t_], lis[t_ + 1]]
                        uv = np.array([tuple(uvd[li].uv) for li in tri]) * [W_, H_]
                        xyz = np.array([tuple(V_[o.data.loops[li].vertex_index].co) for li in tri])
                        x0, y0 = np.floor(uv.min(0)).astype(int); x1, y1 = np.ceil(uv.max(0)).astype(int)
                        if x1 - x0 > 200 or y1 - y0 > 200: continue
                        xs, ys = np.meshgrid(np.arange(x0, x1 + 1), np.arange(y0, y1 + 1)); pts = np.stack([xs.ravel() + 0.5, ys.ravel() + 0.5], 1)
                        Tm = np.array([[uv[0, 0] - uv[2, 0], uv[1, 0] - uv[2, 0]], [uv[0, 1] - uv[2, 1], uv[1, 1] - uv[2, 1]]])
                        if abs(np.linalg.det(Tm)) < 1e-9: continue
                        l12 = np.linalg.solve(Tm, (pts - uv[2]).T).T; L = np.column_stack([l12, 1 - l12.sum(1)]); ins = (L >= -0.35).all(1)   # 삼각형 둘레도 칠함(그림 경계의 어두운 칸이 섞여 목 끝에 가는 검은 줄)
                        if not ins.any(): continue
                        q = np.clip(L[ins], 0, 1); q = (q / q.sum(1, keepdims=True)) @ xyz; pp = pts[ins].astype(int); xx = pp[:, 0].clip(0, W_ - 1); yy = pp[:, 1].clip(0, H_ - 1)
                        keep_ = ~done_[yy, xx]; xx, yy, q = xx[keep_], yy[keep_], q[keep_]
                        t = np.clip((q[:, 2] - CUT) / FEATHER, 0, 1); w = 1 - t * t * (3 - 2 * t)
                        cur = px[yy, xx, :3]; skin = (cur[:, 0] > cur[:, 1]) & (cur[:, 1] > cur[:, 2]) & (cur[:, 0] > 0.5)
                        w = w * (skin | (w > 0.5))          # 목 끝 가까이는 피부가 아니어도(그림 경계 어두운 칸) 칠함
                        px[yy, xx, :3] = cur * (1 - w[:, None]) + tgt * w[:, None]; done_[yy, xx] = True; n_ += int((w > 0).sum())
                img.pixels.foreach_set(px.ravel())
                tmpA = os.path.join(os.path.dirname(os.path.abspath(dst)), "_목띠.png"); img.filepath_raw = tmpA; img.file_format = "PNG"; img.save(); img.pack()
                print("  목 아래 띠 섞은 그림 점", n_, "색", tgt.round(3))
    bm = bmesh.new(); bm.from_mesh(o.data)
    if BISECT and len(bm.verts) > 10000:      # 자르는 높이에서 면을 반듯하게 갈라 끝이 톱니처럼 들쭉날쭉하지 않게 (사용자 2026-11-26 '목경계와 뒷머리카락')
        for zc in [CUT] + ([SIDECUT] if SIDECUT > CUT else []):
            bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], dist=1e-6, plane_co=(0, 0, zc), plane_no=(0, 0, 1))
        bm.verts.ensure_lookup_table(); bm.verts.index_update()
        hairv = {v.index for v in bm.verts if v.co.z < CUT - 1e-5 and False}   # (머리카락 남기기는 끔: 번호가 바뀜)
        clothv = {v.index for v in bm.verts if v.co.z >= CUT and v.co.z <= max(CUT + CLOTHUP, SIDECUT) and tuple(round(c, 5) for c in v.co) in CLOTHCO}
    gone = [v for v in bm.verts if (v.co.z < CUT - 1e-5 and v.index not in hairv) or v.index in clothv
            ]   # 단발 끝은 머리카락 색 점만 자름(위 clothv) — 높이만 보고 자르면 목 옆 피부까지 잘려 깃 뒤로 구멍이 났음 (사용자 2026-11-26 '오른쪽 목 옆 구멍')          # 어깨 위 머리카락 끝(바깥으로 말린 곳): B 어깨가 좁아 떠 보여서 단발 끝을 고르게 자름
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
    if FILLHOLE and len(bm.verts) > 10000:
        # 목 옆 구멍 메우기 (사용자 2026-11-26 '오른쪽 목 옆에 구멍도 메워주고'): 1번은 목 옆에 머리카락이 붙어 있던 자리에 피부가 없어
        # 머리카락 조각을 지우면 구멍이 남음 → 같은 자리 점을 붙여 본 진짜 테두리 고리 중 목 높이의 작은 고리를 면으로 메우고 깨끗한 목 피부 그림 자리를 입힘
        b3 = bm.copy(); bmesh.ops.remove_doubles(b3, verts=b3.verts, dist=1e-4); b3.edges.ensure_lookup_table()
        bnd = [e for e in b3.edges if e.is_boundary]; used = set(); loops_ = []
        adj = {}
        for e in bnd:
            for v in e.verts: adj.setdefault(v.index, []).append(e)
        for e0 in bnd:
            if e0.index in used: continue
            ring_ = [e0.verts[0]]; cur = e0.verts[1]; prev = e0; used.add(e0.index); ok = True
            while cur.index != ring_[0].index:
                ring_.append(cur); nx_ = [e for e in adj.get(cur.index, []) if e.index not in used]
                if not nx_: ok = False; break
                prev = nx_[0]; used.add(prev.index); cur = prev.other_vert(cur)
                if len(ring_) > 400: ok = False; break
            if ok: loops_.append([v.co.copy() for v in ring_])
        from mathutils.kdtree import KDTree as _KD
        kd2 = _KD(len(bm.verts))
        for v in bm.verts: kd2.insert(v.co, v.index)
        kd2.balance(); bm.verts.ensure_lookup_table(); uvl = bm.loops.layers.uv.active; nf = 0
        skin_uv = None
        for f in bm.faces:      # 깨끗한 목 피부 자리(앞 가운데, 자른 곳 위 4cm)의 그림 좌표
            c = f.calc_center_median()
            if abs(c.x) < 0.01 and c.y < 0 and CUT + 0.035 < c.z < CUT + 0.045: skin_uv = f.loops[0][uvl].uv.copy(); break
        for ring_ in loops_:
            zs_ = [c.z for c in ring_]; xs_ = [c.x for c in ring_]
            per = sum((ring_[i] - ring_[i - 1]).length for i in range(len(ring_)))
            if min(zs_) < CUT + 0.004 or max(zs_) > CUT + 0.12 or per > 0.12 or max(abs(x) for x in xs_) > 0.085: continue   # 자른 목 끝 고리·큰 고리는 아님
            vs_ = []
            for c in ring_:
                _, i_, d_ = kd2.find(c)
                if d_ < 2e-4 and bm.verts[i_] not in vs_: vs_.append(bm.verts[i_])
            if len(vs_) < 3: continue
            try: nfc = bm.faces.new(vs_)
            except ValueError: continue
            res = bmesh.ops.triangulate(bm, faces=[nfc]); nf += 1
            cen = sum((v.co for v in vs_), vs_[0].co * 0) / len(vs_)
            for tf in res["faces"]:
                if tf.normal.dot(tf.calc_center_median() - _V((0, cen.y + 0.03, tf.calc_center_median().z))) < 0: tf.normal_flip()
                if skin_uv is not None:
                    for lp in tf.loops: lp[uvl].uv = skin_uv
        b3.free(); print("  목 옆 구멍 메움", nf, "곳")
    bm.to_mesh(o.data); bm.free()
    if not len(o.data.vertices): bpy.data.objects.remove(o); continue
    o.data.transform(T, shape_keys=True)
    if neckB is not None and SNAP > 0 and len(o.data.vertices) > 10000:
        # 목 아래 끝 띠(--이음 높이)를 B 목 원래 겉면으로 옆(가운데 축에서 바깥 방향)으로 옮김 → 1번 목 끝이 2번 목에 턱 없이 이어짐
        # (사용자 2026-11-26 '체크부분 목선 부드럽게': 1번 목 끝이 2번 목보다 3mm 바깥에 떠서 가로선이 보였음). 위로 갈수록 덜 (부드러운 곡선)
        from mathutils import Vector as _V3
        zb = CB + (CUT - CA) * S; band = SNAP * S; n_ = 0
        ring = [p_ for p_ in _vB if zb - 0.01 < p_.z < zb + band + 0.01 and abs(p_.x) < 0.08 and p_.y < 0.13]
        cy_ = sum(p_.y for p_ in ring) / len(ring) if ring else 0.0
        kb_ = o.data.shape_keys.key_blocks if o.data.shape_keys else []
        for v in o.data.vertices:
            if v.co.z >= zb + band: continue
            d = _V3((v.co.x, v.co.y - cy_, 0.0))
            if d.length < 1e-6: continue
            d.normalize(); org = _V3((0.0, cy_, v.co.z)); hit = neckB.ray_cast(org, d, 0.2)
            if hit[0] is None: continue
            rB = (hit[0] - org).length; rA = _V3((v.co.x, v.co.y - cy_, 0)).length
            if abs(rB - rA) > 0.02: continue
            t = max(v.co.z - zb, 0) / band; w_ = 1 - t * t * (3 - 2 * t)
            tuck = 0.0015 * max(0.0, 1 - t / 0.35)     # 맨 아래 끝은 2번 겉면 1.5mm 안으로 숨김 — 두 겉면이 딱 겹치면 검은 줄(그림자 자국)이 생겼음
            dd = d * ((rB - tuck - rA) * w_); v.co += dd; n_ += 1
            for kb in kb_: kb.data[v.index].co += dd
        print("  목 끝 띠를 B 겉면에 맞춘 점", n_, "가운데 y", round(cy_, 3)); NECKCY = cy_
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

def tex_of(obj, pick_skin=True):
    """그 그물의 겉면 색 그림(여러 개면 피부색이 가장 많은 것)"""
    ims = [n.image for m in obj.data.materials if m and m.node_tree for n in m.node_tree.nodes if n.type == "TEX_IMAGE" and n.image]
    def sk(im):
        q = np.empty(im.size[0] * im.size[1] * 4, np.float32); im.pixels.foreach_get(q); q = q.reshape(-1, 4)[::97, :3]
        return float(((q[:, 0] > q[:, 1]) & (q[:, 1] > q[:, 2])).mean())
    if not ims: return None
    return max(ims, key=sk) if pick_skin else ims[0]      # A 는 첫 그림(목띠 섞기와 같은 그림) — 피부 비율로 고르면 다른 그림이 잡혔음

if NECKLACE:   # 목걸이 줄 살리기 (사용자 2026-11-26 '목걸이 선을 살려줘'): B 그림에 그려진 줄 중 A 목에 가려지는 곳(목 옆·뒤)을 A 목 그림의 같은 자리에 옮겨 그림
    mwB_ = bodyB.matrix_world; matsB_ = [m.name.lower() if m else "" for m in bodyB.data.materials]
    miB = next(i for i, m in enumerate(matsB_) if M1 in m)
    imB = tex_of(bodyB); WB, HB = imB.size; pxB = np.empty(WB * HB * 4, np.float32); imB.pixels.foreach_get(pxB); pxB = pxB.reshape(HB, WB, 4)
    uvB = bodyB.data.uv_layers.active.data; VB = bodyB.data.vertices; chain = []
    for poly in bodyB.data.polygons:
        if poly.material_index != miB: continue
        zs_ = [(mwB_ @ VB[i].co).z for i in poly.vertices]
        if max(zs_) < ZBOT - 0.01 or min(zs_) > DEL + 0.04: continue
        lis = list(poly.loop_indices)
        for t_ in range(1, len(lis) - 1):
            tri = [lis[0], lis[t_], lis[t_ + 1]]
            uv = np.array([tuple(uvB[li].uv) for li in tri]) * [WB, HB]; xyz = np.array([tuple(mwB_ @ VB[bodyB.data.loops[li].vertex_index].co) for li in tri])
            x0, y0 = np.floor(uv.min(0)).astype(int); x1, y1 = np.ceil(uv.max(0)).astype(int)
            xs, ys = np.meshgrid(np.arange(x0, x1 + 1), np.arange(y0, y1 + 1)); P = np.stack([xs.ravel() + 0.5, ys.ravel() + 0.5], 1)
            Tm = np.array([[uv[0, 0] - uv[2, 0], uv[1, 0] - uv[2, 0]], [uv[0, 1] - uv[2, 1], uv[1, 1] - uv[2, 1]]])
            if abs(np.linalg.det(Tm)) < 1e-12: continue
            l_ = np.linalg.solve(Tm, (P - uv[2]).T).T; L = np.column_stack([l_, 1 - l_.sum(1)]); ins = (L >= 0).all(1)
            q = L[ins] @ xyz; pp = P[ins].astype(int); c = pxB[pp[:, 1].clip(0, HB - 1), pp[:, 0].clip(0, WB - 1), :3]
            mx, mn = c.max(1), c.min(1); ok = (mx - mn < 0.10) & (mx < 0.62) & (mx > 0.15) & (q[:, 1] < 0.12) & (q[:, 2] > ZBOT + 0.002)
            chain += [(tuple(q[k]), c[k]) for k in np.where(ok)[0]]
    imA = tex_of(mainA, False); WA, HA = imA.size; pxA = np.empty(WA * HA * 4, np.float32); imA.pixels.foreach_get(pxA); pxA = pxA.reshape(HA, WA, 4)
    uvA = mainA.data.uv_layers.active.data; nA = 0
    from mathutils import Vector as _V2
    from mathutils.geometry import barycentric_transform
    for co_, c in chain:
        hit = bvhA.find_nearest(_V2(co_))
        if hit[0] is None or hit[3] > 0.006 or hit[0].z < ZBOT + 0.002: continue   # 1번 목 겉면에 닿는 점만 (아래 점이 목 끝 가장자리에 몰려 가로줄이 됐음)
        poly = mainA.data.polygons[hit[2]]; vi = list(poly.vertices)[:3]; li = list(poly.loop_indices)[:3]
        P3 = [mainA.data.vertices[i].co for i in vi]; U3 = [_V2((*uvA[k].uv, 0)) for k in li]
        uvp = barycentric_transform(hit[0], P3[0], P3[1], P3[2], U3[0], U3[1], U3[2])
        x_, y_ = int(uvp.x * WA), int(uvp.y * HA)
        for dx in (0, 1):
            for dy in (0, 1):
                if 0 <= x_ + dx < WA and 0 <= y_ + dy < HA: pxA[y_ + dy, x_ + dx, :3] = c * 0.9; nA += 1
    if nA:
        imA.pixels.foreach_set(pxA.ravel()); tmpN = os.path.join(os.path.dirname(os.path.abspath(dst)), "_목걸이.png")
        imA.filepath_raw = tmpN; imA.file_format = "PNG"; imA.save(); imA.pack()
    print("목걸이 줄 옮겨 그린 점", len(chain), "→ 그림 칸", nA)

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
        # 옷 조각 중 A 목 겉면 안쪽·바로 위(2mm)에 있는 것 = 원래 B 목 속에 숨어 있던 깃 안쪽 → A 목 밖으로 검은 점처럼 튀어나옴 → 지움 (사용자 '오른쪽 목 옆 구멍')
        ps_ = [mw @ v.co for v in f.verts]; cz = sum(p.z for p in ps_) / len(ps_)
        if cz > ZBOT + 0.003 and abs(sum(p.x for p in ps_) / len(ps_)) < 0.08:
            from mathutils import Vector as _V4
            cx_, cyy = sum(p.x for p in ps_) / len(ps_), sum(p.y for p in ps_) / len(ps_)
            d4 = _V4((cx_, cyy - NECKCY, 0));
            if d4.length > 1e-6:
                d4.normalize(); o4 = _V4((0, NECKCY, cz)); h4 = neckB.ray_cast(o4, d4, 0.2) if neckB else (None,)
                # 원래 B 목 겉면 안쪽·바로 바깥(4mm)에 있던 옷 = B 목에 가려 안 보이던 깃 안쪽 → 이제 드러나 검은 점
                if h4[0] is not None and _V4((cx_, cyy - NECKCY, 0)).length < (h4[0] - o4).length + 0.004: gone.add(f)
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
# 머리를 지운 뒤 목 근처에 떨어져 남은 작은 옷 조각(깃 안쪽 끄트머리 몇 면)은 1번 목 앞에 검은 점처럼 보였음 → 지움 (사용자 '오른쪽 목 옆 구멍')
bm.faces.ensure_lookup_table(); seenf = set(); lone = []
for f0 in bm.faces:
    if f0.index in seenf: continue
    st = [f0]; isl = []; seenf.add(f0.index)
    while st:
        f = st.pop(); isl.append(f)
        for e in f.edges:
            for g in e.link_faces:
                if g.index not in seenf: seenf.add(g.index); st.append(g)
    if len(isl) < 40 and max((mw @ v.co).z for f in isl for v in f.verts) > ZBOT - 0.01 and min((mw @ v.co).z for f in isl for v in f.verts) > 1.3:
        lone += isl
if lone: bmesh.ops.delete(bm, geom=lone, context="FACES"); print("B 목 근처 작은 조각 면 지움", len(lone))
if PUSHIN:   # 겹친 곳의 B 목을 A 목 안쪽으로 밀어 넣음 → 틈 없이 겹치고 B 가 A 밖으로 삐져나오지 않음
    # 목 가운데 축에서 바깥으로 같은 높이의 A 겉면을 찾아(광선) 그보다 3mm 안쪽으로 (A 목 끝 바로 아래 3mm 도 — 경계 위로 물결처럼 튀어나왔음)
    from mathutils import Vector as _V
    mi = next(i for i, m in enumerate(mats) if M1 in m); inv = mw.inverted(); n_ = 0
    vs = [v for v in {v for f in bm.faces if f.material_index == mi for v in f.verts} if (mw @ v.co).z > ZBOT - 0.001]
    if vs:
        cy = sum((mw @ v.co).y for v in vs) / len(vs)
        for v in vs:
            p = mw @ v.co; zz = max(p.z, ZBOT + 0.0015)
            d = _V((p.x, p.y - cy, 0.0))
            if d.length < 1e-6: continue
            d.normalize(); hit = bvhA.ray_cast(_V((0.0, cy, zz)), d, 0.2)
            if hit[0] is None: continue
            rA = (hit[0] - _V((0.0, cy, zz))).length; rB = _V((p.x, p.y - cy, 0)).length
            if p.z < ZBOT + 0.6 * SNAP * S: continue        # 1번 목 끝 띠(2번 겉면에 맞춘 곳)의 2번 목은 그대로 — 넣으면 접혀서 검은 줄
            dep = 0.003
            if rB > rA - dep:
                k = (rA - dep) / rB; p.x *= k; p.y = cy + (p.y - cy) * k; v.co = inv @ p; n_ += 1
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
