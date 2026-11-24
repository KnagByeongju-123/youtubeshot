"""실사 야외 배경 + 말하는 3D 인물 + 카메라 오르빗 (블렌더 Cycles, 그래픽카드 없이)
   배경 = Poly Haven 360° 사진(HDRI, CC0)을 '세상' 전체로 씀 → 화면(스크린) 없이 실제 그 장소에 선 것처럼.
     카메라가 보는 배경은 고화질 사진(tonemapped 8K jpg), 빛·반사는 HDR(1k)
   인물 = GLB(애니3D/glb_다시리깅.py·glb_입모양고치기.py 로 고친 것), 발밑은 그림자만 받는 바닥(shadow catcher)
   입 = 애니3D/입모양_프레임.py 결과(open·wide·round) → 모양 키 MouthOpen·MouthWide·MouthRound, 눈 깜빡임 Blink
   사용: .bpy_venv/bin/python -I 실사3D/야외_오르빗.py <인물.glb> <프레임폴더> [--장소 shanghai_bund] [--방향 0.59]
             [--입 <입모양.json>] [--장수 192] [--시작장 0] [--끝장 -1] [--샘플 16] [--크기 1024x576] [--키 1.62]
             [--각도 -35,35] [--거리 2.6] [--높이 1.45] [--보기 1.3] [--미리보기 <장번호>]
     --방향: 사진에서 인물 뒤에 둘 것의 가로 자리(0~1). 동방명주 = 0.41 (shanghai_bund — 값을 줄이면 배경이 오른쪽→가운데로 옴)
     --각도: 카메라가 인물 둘레를 도는 각도 범위(도). 0 = 정면
   (사용자 결정 2026-11-23: 동방명주 배경으로 방송하는 여자 아나운서, 실사 배경, 스크린 없이, 오르빗 촬영)"""
import json, math, os, sys, urllib.request
import bpy, mathutils

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
a = sys.argv[1:]
glb, folder = a[0], a[1]
opt = {"--장소": "shanghai_bund", "--방향": "0.41", "--입": None, "--장수": "192", "--시작장": "0", "--끝장": "-1", "--샘플": "16",
       "--크기": "1024x576", "--키": "1.62", "--각도": "-35,35", "--거리": "2.6", "--높이": "1.45", "--보기": "1.3", "--미리보기": None}
for k in list(opt):
    if k in a: opt[k] = a[a.index(k) + 1]
PLACE = opt["--장소"]; A = os.path.join(ROOT, "models", "polyhaven", "_hdri"); os.makedirs(A, exist_ok=True)


def fetch():
    o = urllib.request.build_opener(); o.addheaders = [("User-Agent", "asset-fetcher/1.0")]; urllib.request.install_opener(o)
    f = None
    for name, key in ((f"{PLACE}.jpg", "tonemapped"), (f"{PLACE}_1k.hdr", "hdr")):
        p = os.path.join(A, name)
        if os.path.exists(p): continue
        f = f or json.load(urllib.request.urlopen(f"https://api.polyhaven.com/files/{PLACE}"))
        url = f["tonemapped"]["url"] if key == "tonemapped" else f["hdri"]["1k"]["hdr"]["url"]
        urllib.request.urlretrieve(url, p); print("받음", p)


fetch()
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
W_, H_ = (int(v) for v in opt["--크기"].split("x"))
sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"; sc.cycles.samples = int(opt["--샘플"]); sc.cycles.use_denoising = True
sc.render.resolution_x, sc.render.resolution_y = W_, H_; sc.render.film_transparent = False
sc.view_settings.view_transform = "Standard"; sc.cycles.max_bounces = 4
sc.render.fps = 24

# ── 세상: 카메라에는 고화질 사진, 빛은 HDR ──
w = bpy.data.worlds.new("세상"); sc.world = w; w.use_nodes = True; nt = w.node_tree; nt.nodes.clear()
tc = nt.nodes.new("ShaderNodeTexCoord"); mp = nt.nodes.new("ShaderNodeMapping")
# 사진 가로 자리 u 가 +Y(카메라가 처음 보는 쪽, 인물 뒤)로 오게 돌림: 블렌더 360° 사진에서 +Y 는 u=0.75
mp.inputs["Rotation"].default_value = (0, 0, math.radians((float(opt["--방향"]) - 0.75) * 360))
nt.links.new(tc.outputs["Generated"], mp.inputs["Vector"])
e_cam = nt.nodes.new("ShaderNodeTexEnvironment"); e_cam.image = bpy.data.images.load(os.path.join(A, f"{PLACE}.jpg"))
e_lit = nt.nodes.new("ShaderNodeTexEnvironment"); e_lit.image = bpy.data.images.load(os.path.join(A, f"{PLACE}_1k.hdr"))
for e in (e_cam, e_lit): nt.links.new(mp.outputs["Vector"], e.inputs["Vector"])
b_cam = nt.nodes.new("ShaderNodeBackground"); b_lit = nt.nodes.new("ShaderNodeBackground"); b_lit.inputs["Strength"].default_value = float(a[a.index("--세상빛") + 1]) if "--세상빛" in a else 0.6   # 사진에서 오는 빛 세기 (인물 밝기)
nt.links.new(e_cam.outputs["Color"], b_cam.inputs["Color"]); nt.links.new(e_lit.outputs["Color"], b_lit.inputs["Color"])
lp = nt.nodes.new("ShaderNodeLightPath"); mix = nt.nodes.new("ShaderNodeMixShader"); outw = nt.nodes.new("ShaderNodeOutputWorld")
nt.links.new(lp.outputs["Is Camera Ray"], mix.inputs["Fac"]); nt.links.new(b_lit.outputs["Background"], mix.inputs[1]); nt.links.new(b_cam.outputs["Background"], mix.inputs[2])
nt.links.new(mix.outputs["Shader"], outw.inputs["Surface"])

# ── 바닥: 그림자만 받음 ──
bpy.ops.mesh.primitive_plane_add(size=30, location=(0, 0, 0)); fl = bpy.context.object; fl.is_shadow_catcher = True

# ── 인물 ──
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=os.path.abspath(glb))
objs = [o for o in bpy.data.objects if o not in before]; roots = [o for o in objs if o.parent is None]
bpy.context.view_layer.update()
def bbox():
    pts = [o.matrix_world @ mathutils.Vector(c) for o in objs if o.type == "MESH" for c in o.bound_box]
    return pts
pts = bbox(); k = float(opt["--키"]) / (max(p.z for p in pts) - min(p.z for p in pts))
for r in roots: r.scale = (r.scale[0] * k, r.scale[1] * k, r.scale[2] * k)
bpy.context.view_layer.update(); pts = bbox()
for r in roots:
    r.location.x -= (min(p.x for p in pts) + max(p.x for p in pts)) / 2; r.location.y -= (min(p.y for p in pts) + max(p.y for p in pts)) / 2
    r.location.z -= min(p.z for p in pts)
# ── 다리 구멍 메우기(기본 켬, --구멍그대로 면 끔): 다리를 거울로 다시 세운 모델의 이음매에 남은 작은 구멍을 블렌더 '구멍 채우기'로 막음 ──
#   같은 자리 점을 합친 뒤(그림 좌표는 면 모서리마다 따로라 그대로), 허리 아래 열린 모서리 고리를 채우고 새 면의 그림 좌표는 이웃 면에서 가져옴
if "--구멍그대로" not in a:
    import bmesh
    body_ = max((o for o in objs if o.type == "MESH"), key=lambda o: len(o.data.vertices))
    me_ = body_.data; bm = bmesh.new(); bm.from_mesh(me_)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    mw_ = body_.matrix_world; ztop = 0.52 * float(opt["--키"])          # 허리 아래(다리)만
    bnd = [e for e in bm.edges if e.is_boundary and all((mw_ @ v.co).z < ztop for v in e.verts)]
    res = bmesh.ops.holes_fill(bm, edges=bnd, sides=0)
    uvl = bm.loops.layers.uv.active; nf = 0
    for f in res["faces"]:
        nf += 1
        f.smooth = True
        if f.material_index == 0 and len(f.verts) and f.verts[0].link_faces:
            src = next((g for g in f.verts[0].link_faces if g is not f), None)
            if src is not None: f.material_index = src.material_index
        if uvl is not None:
            for lp in f.loops:
                other = next((l2 for l2 in lp.vert.link_loops if l2.face is not f and l2.face not in res["faces"]), None)
                if other is not None: lp[uvl].uv = other[uvl].uv
    bm.to_mesh(me_); bm.free(); me_.update()
    print(f"다리 구멍 {nf}개 채움 (열린 모서리 {len(bnd)}개)")
# ── 따로 된 구두(--구두 <폴더>, 애니3D/glb_구두떼기.py 결과): 각 발 뼈에 붙임 — 원래 몸 구두는 그 안에 가려짐 (사용자 결정 2026-11-24) ──
if "--구두" in a:
    import numpy as np
    sd_ = a[a.index("--구두") + 1]; z_ = np.load(os.path.join(sd_, "구두.npz"))
    arm0 = next((o for o in objs if o.type == "ARMATURE"), None)
    body = max((o for o in objs if o.type == "MESH"), key=lambda o: len(o.data.vertices))
    bpy.context.view_layer.update()
    smat = bpy.data.materials.new("구두"); smat.use_nodes = True; bsdf = smat.node_tree.nodes["Principled BSDF"]
    tx = smat.node_tree.nodes.new("ShaderNodeTexImage"); tx.image = bpy.data.images.load(os.path.abspath(os.path.join(sd_, "구두_그림.png")))
    smat.node_tree.links.new(tx.outputs["Color"], bsdf.inputs["Base Color"]); bsdf.inputs["Roughness"].default_value = 0.3
    for k_, sdn in ((0, "L"), (1, "R")):
        m_ = z_["side"] == k_
        if not m_.any(): continue
        idx = np.where(m_)[0]; remap = -np.ones(len(m_), int); remap[idx] = np.arange(len(idx))
        T_ = z_["I"][np.isin(z_["I"], idx).all(1)]; T_ = remap[T_]
        Pg = z_["P"][idx]; Pb = [(float(x), float(-zz), float(y)) for x, y, zz in Pg]          # GLB(y 위) → 블렌더(z 위)
        me = bpy.data.meshes.new(f"구두.{sdn}"); me.from_pydata(Pb, [], [tuple(int(v) for v in t) for t in T_]); me.update()
        uvl = me.uv_layers.new(name="UV"); U_ = z_["UV"][idx]
        for poly in me.polygons:
            for li in poly.loop_indices:
                vi = me.loops[li].vertex_index; uvl.data[li].uv = (float(U_[vi, 0]), float(1 - U_[vi, 1]))
        ob = bpy.data.objects.new(f"구두.{sdn}", me); bpy.context.collection.objects.link(ob); me.materials.append(smat)
        for poly in me.polygons: poly.use_smooth = True
        ob.matrix_world = body.matrix_world.copy()          # 몸과 같은 자리·크기
        if arm0 is not None and f"Foot.{sdn}" in arm0.pose.bones:
            mw = ob.matrix_world.copy(); ob.parent = arm0; ob.parent_type = "BONE"; ob.parent_bone = f"Foot.{sdn}"
            bpy.context.view_layer.update(); ob.matrix_world = mw
        objs.append(ob)
        if "capP" in z_.files and len(z_["capP"]):
            cm_ = z_["capSide"] == k_; cidx = np.where(cm_)[0]; crm = -np.ones(len(cm_), int); crm[cidx] = np.arange(len(cidx))
            CT = crm[z_["capI"][np.isin(z_["capI"], cidx).all(1)]]
            me2 = bpy.data.meshes.new(f"발등.{sdn}"); me2.from_pydata([(float(x), float(-zz), float(y)) for x, y, zz in z_["capP"][cidx]], [], [tuple(int(v) for v in t) for t in CT]); me2.update()
            for poly in me2.polygons: poly.use_smooth = True
            if "발등살" not in bpy.data.materials:
                fm = bpy.data.materials.new("발등살"); fm.use_nodes = True; fb = fm.node_tree.nodes["Principled BSDF"]
                sk = [float(c) for c in z_["skin"]]; lin = [((c + 0.055) / 1.055) ** 2.4 if c > 0.04045 else c / 12.92 for c in sk]
                fb.inputs["Base Color"].default_value = (*lin, 1); fb.inputs["Roughness"].default_value = 0.55
            me2.materials.append(bpy.data.materials["발등살"])
            ob2 = bpy.data.objects.new(f"발등.{sdn}", me2); bpy.context.collection.objects.link(ob2); ob2.matrix_world = body.matrix_world.copy()
            if arm0 is not None and f"Foot.{sdn}" in arm0.pose.bones:
                mw2 = ob2.matrix_world.copy(); ob2.parent = arm0; ob2.parent_type = "BONE"; ob2.parent_bone = f"Foot.{sdn}"
                bpy.context.view_layer.update(); ob2.matrix_world = mw2
            objs.append(ob2)
    print("구두 붙임:", sd_)
# ── 자세: 기본 = 차렷(팔을 몸 옆에 자연스럽게 내림, 사용자 결정 2026-11-23), --자세 모음 = 손을 허리 앞에 모음 — 뼈 방향을 목표 방향으로 돌림 ──
POSE = a[a.index('--자세') + 1] if '--자세' in a else '차렷'     # 앞나란히 / 차렷(기본, 사용자 결정 2026-11-23: 마이크 없이 자연스러운 팔) / 마이크 / 모음
MIC_SIDE = a[a.index('--마이크손') + 1] if '--마이크손' in a else 'R'
HAND_S = float(a[a.index('--손굵기') + 1]) if '--손굵기' in a else 0.82
MIC_F = (0.30, 0.45, 0.85); MIC_CURL = 1.25; FIST = float(a[a.index('--주먹') + 1]) if '--주먹' in a else 0.32   # 주먹 = 마디마다 굽힘(라디안)
CH_U, CH_F = (float(v) for v in (a[a.index('--팔벌림') + 1] if '--팔벌림' in a else '0.12,0.10').split(','))   # 차렷 팔이 몸에서 떨어진 정도(위팔,아래팔)
arm = next((o for o in objs if o.type == "ARMATURE"), None)
if arm is not None and "--자세없음" not in a:
    bpy.context.view_layer.objects.active = arm; bpy.ops.object.mode_set(mode="POSE")
    MW = arm.matrix_world; MWi = MW.inverted()
    def aim_bone(name_cands, target_dir_world, child_cands):
        """뼈를 관절 기준으로 돌려, 이 관절→다음 관절(자식) 방향이 목표 방향이 되게 (블렌더 뼈 꼬리 방향은 실제 팔 방향과 다를 수 있음)"""
        pb = next((arm.pose.bones[n] for n in name_cands if n in arm.pose.bones), None)
        ch = next((arm.pose.bones[n] for n in child_cands if n in arm.pose.bones), None)
        if pb is None or ch is None: return
        bpy.context.view_layer.update()
        head = MW @ pb.head; cur = ((MW @ ch.head) - head).normalized()
        q = cur.rotation_difference(mathutils.Vector(target_dir_world).normalized())
        R = (MWi.to_3x3() @ q.to_matrix() @ MW.to_3x3()).to_4x4()
        hd = pb.head.copy(); T1 = mathutils.Matrix.Translation(hd); T0 = mathutils.Matrix.Translation(-hd)
        pb.matrix = T1 @ R @ T0 @ pb.matrix
        bpy.context.view_layer.update()
    def B(n): return arm.pose.bones.get(n)
    def W(pb): return MW @ pb.head
    # 손바닥 방향: 처음 자세(팔을 옆으로 편)에서 손바닥은 아래(-z) → 손 뼈 기준 방향으로 기억해 두고, 팔을 돌린 뒤 다시 계산
    palm = {}
    bpy.context.view_layer.update()
    for side in ("L", "R"):
        h, i1, l1 = B(f"Hand.{side}"), B(f"Index1.{side}"), B(f"Little1.{side}")
        if not (h and i1 and l1): continue
        n = (W(i1) - W(h)).cross(W(l1) - W(h)).normalized()
        t3 = B(f"Thumb3.{side}")
        if t3 is not None and n.dot(W(t3) - W(h)) < 0: n = -n        # 손바닥 쪽 = 엄지 끝이 있는 쪽 (팔을 내리면 손바닥이 허벅지 쪽, 손가락도 허벅지 쪽으로 굽어야 함 — 2026-11-23 손 가까이 찍어 확인)
        elif t3 is None and n.z > 0: n = -n
        palm[side] = (h.matrix.to_3x3().inverted() @ MWi.to_3x3() @ n)
    def palm_now(side):
        bpy.context.view_layer.update(); return (MW.to_3x3() @ B(f"Hand.{side}").matrix.to_3x3() @ palm[side]).normalized()
    def curl(side, amt, thumb=None):
        """손가락을 손바닥 쪽으로 굽힘 (amt = 마디마다 굽히는 각도, 라디안)"""
        if side not in palm: return
        for f in ("Index", "Middle", "Ring", "Little", "Thumb"):
            th = (thumb if thumb is not None else amt * 0.5) if f == "Thumb" else amt
            for k in (1, 2, 3):
                pb = B(f"{f}{k}.{side}")
                if pb is None: continue
                # 손가락 방향 = 이 마디 → 다음 마디 (블렌더 뼈 꼬리 방향은 손가락 방향과 다를 수 있어 쓰지 않음; 끝 마디는 앞 마디 방향)
                nx = B(f"{f}{k + 1}.{side}") if k < 3 else None
                a0 = MW @ pb.head
                if nx is not None: cur = ((MW @ nx.head) - a0).normalized()
                else: cur = (a0 - (MW @ B(f"{f}{k - 1}.{side}").head)).normalized()
                n = palm_now(side); ax = cur.cross(n)
                if ax.length < 1e-6: continue
                q = mathutils.Quaternion(ax.normalized(), th); R = (MWi.to_3x3() @ q.to_matrix() @ MW.to_3x3()).to_4x4()
                T1 = mathutils.Matrix.Translation(pb.head); T0 = mathutils.Matrix.Translation(-pb.head)
                pb.matrix = T1 @ R @ T0 @ pb.matrix; bpy.context.view_layer.update()
    mic_hand = None
    for side in ("L", "R"):
        ub = [f"UpperArm.{side}", f"{'Left' if side == 'L' else 'Right'}UpperArm"]
        fb = [f"ForeArm.{side}", f"{'Left' if side == 'L' else 'Right'}ForeArm"]
        hb = [f"Hand.{side}", f"{'Left' if side == 'L' else 'Right'}Hand"]
        pb = next((arm.pose.bones[n] for n in ub if n in arm.pose.bones), None)
        if pb is None: continue
        sgn = 1 if (MW @ pb.head).x > 0 else -1
        if POSE == '모음':
            aim_bone(ub, (sgn * 0.14, -0.22, -0.96), fb)       # 위팔: 아래로, 몸에 붙여 살짝 앞
            aim_bone(fb, (-sgn * 0.62, -0.72, -0.30), hb)      # 아래팔: 앞·안쪽으로 → 손이 허리 앞에서 모임
        elif POSE == '앞나란히':                                 # 두 팔을 어깨 높이로 앞으로 곧게 (사용자 2026-11-24 '앞으로 나란히')
            aim_bone(ub, (sgn * 0.02, -1.0, 0.0), fb)          # 위팔: 곧게 앞으로, 어깨 너비 그대로
            aim_bone(fb, (sgn * 0.0, -1.0, 0.0), hb)           # 아래팔: 위팔과 한 줄
            aim_bone(hb, (0.0, -1.0, -0.02), [f"Middle1.{side}"])   # 손: 손끝이 앞으로, 손바닥은 안쪽
            curl(side, 0.08, thumb=0.05)                       # 손가락은 거의 펴고 힘만 살짝 뺌
        elif POSE == '마이크' and side == MIC_SIDE:
            aim_bone(ub, (sgn * 0.10, -0.30, -0.95), fb)       # 위팔: 아래로, 팔꿈치는 몸 옆 살짝 앞
            aim_bone(fb, (-sgn * MIC_F[0], -MIC_F[1], MIC_F[2]), hb)   # 아래팔: 가슴 앞으로 들어 올림
            aim_bone(hb, (-sgn * 0.30, -0.55, 0.78), [f"Middle1.{side}"])   # 손: 손가락이 앞·위를 향하게 (마이크를 세워 쥠)
            curl(side, MIC_CURL, thumb=0.45); mic_hand = side
        else:
            aim_bone(ub, (sgn * CH_U, -0.03, -1.0), fb)        # 위팔: 곧게 아래로, 엉덩이에 닿지 않게 살짝 바깥
            aim_bone(fb, (sgn * CH_F, -0.10, -1.0), hb)        # 아래팔: 아래로, 팔꿈치를 아주 살짝 굽혀 자연스럽게
            curl(side, FIST, thumb=FIST * 0.4)                 # 손가락을 살짝 굽혀 힘을 뺀 손 (편 채 늘어뜨리면 어색함)
        hpb = next((arm.pose.bones[n] for n in hb if n in arm.pose.bones), None)
        if hpb is not None and HAND_S != 1:                    # 손이 너무 굵다는 지적(2026-11-23) → 손 두께·폭만 줄임(뼈 길이 방향 y 는 조금만)
            hpb.scale = (HAND_S, 0.5 + 0.5 * HAND_S, HAND_S)
    # 무선 마이크: 손 안(손바닥 쪽)에 세워 쥐고, 머리(공 모양 망)는 입 쪽으로
    if mic_hand:
        bpy.context.view_layer.update(); bpy.ops.object.mode_set(mode="OBJECT")
        h, m1, i1, l1 = (W(B(f"{n}.{mic_hand}")) for n in ("Hand", "Middle1", "Index1", "Little1"))
        n = palm_now(mic_hand)
        grip = (h + m1) / 2 * 0.35 + m1 * 0.65 + n * 0.022                 # 손바닥 안쪽, 손가락이 감싸는 자리
        axis = (i1 - l1).normalized()                                       # 마이크 방향 = 새끼→검지 (주먹 안을 지나는 방향)
        if axis.z < 0: axis = -axis
        axis = (axis + mathutils.Vector((0, -0.15, 0))).normalized()
        def mat(nm, col, rough, metal):
            m = bpy.data.materials.new(nm); m.use_nodes = True; bs = m.node_tree.nodes["Principled BSDF"]
            bs.inputs["Base Color"].default_value = (*col, 1); bs.inputs["Roughness"].default_value = rough; bs.inputs["Metallic"].default_value = metal; return m
        rot = mathutils.Vector((0, 0, 1)).rotation_difference(axis).to_euler()
        L_ = 0.20; base = grip - axis * 0.07                                 # 손 아래로 7cm 나옴
        bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=0.017, depth=L_, location=base + axis * (L_ / 2), rotation=rot)
        body = bpy.context.object; body.data.materials.append(mat("마이크몸통", (0.02, 0.02, 0.022), 0.35, 0.3)); bpy.ops.object.shade_smooth()
        bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=0.021, depth=0.025, location=base + axis * (L_ - 0.005), rotation=rot)
        ring = bpy.context.object; ring.data.materials.append(mat("마이크고리", (0.55, 0.56, 0.6), 0.25, 1.0)); bpy.ops.object.shade_smooth()
        bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=0.029, location=base + axis * (L_ + 0.022))
        head_ = bpy.context.object; head_.data.materials.append(mat("마이크망", (0.12, 0.12, 0.13), 0.55, 0.9)); bpy.ops.object.shade_smooth()
        print("마이크 머리 위치", tuple(round(v, 3) for v in head_.location))
    if bpy.context.object and bpy.context.object.mode != "OBJECT": bpy.ops.object.mode_set(mode="OBJECT")
# 모양 키(입·눈) 모으기
keyed = [o for o in objs if o.type == "MESH" and o.data.shape_keys]
def set_shape(name, v, frame=None):
    for o in keyed:
        kb = o.data.shape_keys.key_blocks.get(name)
        if kb is not None:
            kb.value = v
            if frame is not None: kb.keyframe_insert("value", frame=frame)

# ── 얼굴 조명(방송용 부드러운 빛) ──
def area(loc, power, size, color):
    bpy.ops.object.light_add(type="AREA", location=loc); l = bpy.context.object; l.data.energy = power; l.data.size = size; l.data.color = color
    d = mathutils.Vector((0, 0, 1.45)) - l.location; l.rotation_euler = d.to_track_quat("-Z", "Y").to_euler(); return l
LG = float(a[a.index('--조명') + 1]) if '--조명' in a else 0.12     # 얼굴 조명 세기 배율 (1 = 예전, 얼굴이 너무 밝다는 지적 2026-11-23 → 0.12)
area((-1.6, -2.0, 2.4), 160 * LG, 1.5, (1.0, 0.95, 0.9))
area((1.8, -1.6, 1.8), 60 * LG, 1.5, (0.9, 0.93, 1.0))
area((0.3, 1.8, 2.4), 120 * LG, 1.0, (0.8, 0.85, 1.0))       # 뒤 윤곽광 (도시 빛과 어울리게 살짝 푸름)

# ── 카메라: 인물 둘레를 돎 ──
bpy.ops.object.camera_add(); cam = bpy.context.object; sc.camera = cam; cam.data.lens = 40
a0, a1 = (math.radians(float(v)) for v in opt["--각도"].split(","))
R, HC, LOOK = float(opt["--거리"]), float(opt["--높이"]), float(opt["--보기"])
N = int(opt["--장수"])
HANDVIEW = a[a.index('--손보기') + 1] if '--손보기' in a else None   # 검사용: 손 가까이 찍기 (R 또는 L)
HP = None
if HANDVIEW and arm is not None:
    bpy.context.view_layer.update()
    hb_, mb_ = arm.pose.bones[f"Hand.{HANDVIEW}"], arm.pose.bones[f"Middle3.{HANDVIEW}"]
    HP = ((arm.matrix_world @ hb_.head) + (arm.matrix_world @ mb_.tail)) / 2
R1 = float(a[a.index("--끝거리") + 1]) if "--끝거리" in a else R          # 카메라가 뒤로 빠지는 끝 거리 (없으면 그대로)
LOOK1 = float(a[a.index("--끝보기") + 1]) if "--끝보기" in a else LOOK
HC1 = float(a[a.index("--끝높이") + 1]) if "--끝높이" in a else HC
WHO = [mathutils.Vector((0, 0, 0))]
# 게임 카메라(--게임카메라): (초, 각도°, 거리, 높이, 보는 높이, 렌즈mm) — 춤 마디에 맞춰 구도가 바뀜 (사용자 2026-11-24 '게임 카메라무빙')
#   스텝: 낮은 앵글로 크게 돌기 → 손뼉: 정면 상반신으로 밀고 들어감 → 엉덩이: 옆 낮은 높이로 쓸고 지나감 → 돌기: 높이 올라가며(크레인) 반대쪽으로 크게 돎
GAMECAM = "--게임카메라" in a; GAMECAM_ROLL = 4.0
GAMECAM_KEYS = [(0.0, -40, 3.4, 0.45, 0.85, 30), (2.2, 30, 2.6, 0.55, 0.95, 34), (3.0, 5, 1.9, 1.35, 1.25, 48), (4.5, -8, 1.8, 1.3, 1.22, 50),
                (5.1, 60, 2.6, 0.6, 0.88, 32), (6.6, 105, 2.8, 0.65, 0.9, 32), (7.3, 150, 3.3, 2.5, 0.95, 28), (9.0, 250, 3.6, 1.7, 0.95, 30),
                (12.0, 360, 3.6, 1.4, 0.95, 32)]
def place(i, who=None):
    s = i / max(1, N - 1); s = s * s * (3 - 2 * s); th = a0 + (a1 - a0) * s
    r_ = R + (R1 - R) * s; lk = LOOK + (LOOK1 - LOOK) * s; hc = HC + (HC1 - HC) * s
    c0 = who if who is not None else mathutils.Vector((0, 0, 0))
    cam.location = (c0.x + r_ * math.sin(th), c0.y - r_ * math.cos(th), hc)
    if "--카메라" in a:      # 검사용: 카메라 자리·보는 곳을 직접 (x,y,z,보는x,보는y,보는z — 인물이 걸어온 만큼 같이 옮김)
        v6 = [float(q) for q in a[a.index("--카메라") + 1].split(",")]; wv = WHO[0]
        cam.location = mathutils.Vector(v6[:3]) + wv; d = mathutils.Vector(v6[3:]) + wv - cam.location
        cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler(); return
    if GAMECAM and HP is None:                     # 게임 카메라: 동작마다 다른 구도로 부드럽게 날아다님
        t = i / 24.0; ks = GAMECAM_KEYS
        k = max(0, min(len(ks) - 2, next((n for n in range(len(ks) - 1) if ks[n + 1][0] > t), len(ks) - 2)))
        (ta, *A), (tb, *Bk) = ks[k], ks[k + 1]
        u = min(1.0, max(0.0, (t - ta) / max(tb - ta, 1e-6))); u = u * u * (3 - 2 * u)
        ang, rad, hgt, lz, lens = [A[q] + (Bk[q] - A[q]) * u for q in range(5)]
        sh = 0.006 * math.sin(t * 7.3) + 0.004 * math.sin(t * 12.1)           # 손으로 든 듯한 아주 작은 흔들림
        th = math.radians(ang)
        cam.location = (c0.x + rad * math.sin(th) + sh, c0.y - rad * math.cos(th), hgt + sh * 0.6)
        cam.data.lens = lens
        d = mathutils.Vector((c0.x, c0.y, lz)) - cam.location; cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
        if GAMECAM_ROLL: cam.rotation_euler.rotate_axis("Z", math.radians(GAMECAM_ROLL * math.sin(math.pi * u) * (1 if k % 2 else -1)))
        return
    if HP is None:
        d = mathutils.Vector((c0.x, c0.y, lk)) - cam.location; cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler(); return
    if HP is not None:
        sx = 1 if HP.x > 0 else -1
        cam.location = HP + mathutils.Vector((sx * 0.22, -0.38, 0.05)); cam.data.lens = 50
        d = HP - cam.location; cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler(); return
    d = mathutils.Vector((0, 0, LOOK)) - cam.location; cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()

# ── 걷기(--걷기): 인물이 카메라 쪽(-y)으로 두어 걸음 걸어와 멈춤, 카메라는 뒤로 빠지며 돎 (사용자 결정 2026-11-23) ──
#   발 자리를 시간마다 정하고(오른발 → 왼발 → 오른발을 모음), 골반은 두 발 가운데, 다리는 두 마디 IK(무릎은 앞으로), 발은 바닥과 평평하게.
#   팔은 걷는 동안 반대쪽 다리와 함께 앞뒤로 조금 흔듦
WALK = "--걷기" in a
DANCE = "--춤" in a          # 가벼운 춤(스텝 터치): 옆으로 한 발 내딛고 모으기를 박자에 맞춰, 무릎 반동·골반·팔 흔들기 (사용자 2026-11-24 "약간의 댄스")
BPM = float(a[a.index("--박자") + 1]) if "--박자" in a else 112
ROUTINE = (a[a.index("--춤순서") + 1] if "--춤순서" in a else "스텝,손뼉,엉덩이,돌기").split(",")   # 4박마다 바뀌는 동작 순서
STEP = float(a[a.index("--보폭") + 1]) if "--보폭" in a else 0.28     # 엉덩이~발목 0.55m·몸에 붙는 치마·굽 구두 → 작은 걸음 (0.40 이면 골반이 내려가 무릎 굽은 채 걸음)
if (WALK or DANCE) and arm is not None:
    bpy.context.view_layer.update()
    MW = arm.matrix_world.copy(); MWi = MW.inverted(); M3 = MW.to_3x3(); M3i = MWi.to_3x3()
    PB = arm.pose.bones
    base = {b.name: b.matrix_basis.copy() for b in PB}          # 차렷 자세(팔·손가락 굽힘 포함) 그대로 기억
    hips0 = MW @ PB["Hips"].head
    FOOT0 = {sd: PB[f"Foot.{sd}"].matrix.to_3x3().to_4x4() for sd in ("L", "R")}
    leg = {}
    for sd in ("L", "R"):
        H = MW @ PB[f"UpperLeg.{sd}"].head; Kn = MW @ PB[f"LowerLeg.{sd}"].head; F = MW @ PB[f"Foot.{sd}"].head
        leg[sd] = dict(H=H, L1=(Kn - H).length, L2=(F - Kn).length, F0=F.copy())
    LL = (leg["L"]["L1"] + leg["L"]["L2"] + leg["R"]["L1"] + leg["R"]["L2"]) / 2
    sm = lambda u: 0.0 if u <= 0 else 1.0 if u >= 1 else u * u * (3 - 2 * u)
    T0 = 0.5; D1 = 0.62; D3 = 0.5                            # 걷기 시작 0.5초, 한 걸음 0.62초, 마지막 모으기 0.5초
    # 걷기 분석(2026-11-24 사용자 '걸어가는 샷 분석해서 수정')에서 고친 것:
    #   발을 6cm 들어 무릎이 계단 오르듯 높이 올라감 → 3.5cm · 골반이 두 발 가운데를 따라 걸음마다 멈칫 → 처음부터 끝까지 고르게 앞으로
    #   발이 늘 평평 → 뗄 때 뒤꿈치 들고(14°) 디딜 때 앞꿈치 살짝 듦 · 몸통이 막대처럼 → 골반 좌우 돌림·기울임, 가슴은 반대로, 살짝 앞으로 숙임
    #   팔 흔들림이 거의 없음 → 크게, 앞으로 갈 때 팔꿈치 살짝 굽힘
    LIFT = 0.035; TEND = T0 + 2 * D1 + D3
    def foot_u(sd, t):                                       # 이 발이 지금 몇 번째 걸음의 어디쯤(0~1)인지, 걸음 길이
        segs = [(T0, D1), (T0 + 2 * D1, D3)] if sd == "R" else [(T0 + D1, D1)]
        for s0, d in segs:
            if s0 <= t <= s0 + d: return (t - s0) / d
        return None
    def foot_pitch(u):                                       # +면 뒤꿈치가 들림 (라디안)
        if u is None: return 0.0
        if u < 0.35: return math.radians(14) * math.sin(math.pi * u / 0.35 * 0.5 + 0.0) * (1 - u / 0.35) * 2
        if u > 0.75: return -math.radians(6) * math.sin(math.pi * (u - 0.75) / 0.25)
        return 0.0
    def rot_world(name, axis, ang):
        pb = PB[name]; bpy.context.view_layer.update()
        R_ = (M3i @ mathutils.Matrix.Rotation(ang, 3, axis) @ M3).to_4x4()
        T1 = mathutils.Matrix.Translation(pb.head); T0_ = mathutils.Matrix.Translation(-pb.head)
        pb.matrix = T1 @ R_ @ T0_ @ pb.matrix; bpy.context.view_layer.update()
    def foot_y(sd, t):
        if sd == "R":   # 오른발 먼저 한 걸음, 마지막에 왼발 옆으로 모음
            return -STEP * sm((t - T0) / D1) - STEP * sm((t - T0 - 2 * D1) / D3)
        return -2 * STEP * sm((t - T0 - D1) / D1)
    def foot_lift(sd, t):
        ph = [(T0, D1, LIFT), (T0 + 2 * D1, D3, LIFT * 0.6)] if sd == "R" else [(T0 + D1, D1, LIFT)]
        return sum(h * math.sin(math.pi * min(1, max(0, (t - s0) / d))) for s0, d, h in ph)
    def set_world_aim(name, child_head_world, target_world):
        pb = PB[name]; bpy.context.view_layer.update()
        hd = MW @ pb.head; cur = (child_head_world() - hd).normalized()
        q = cur.rotation_difference((target_world - hd).normalized()); R_ = (M3i @ q.to_matrix() @ M3).to_4x4()
        T1 = mathutils.Matrix.Translation(pb.head); T0_ = mathutils.Matrix.Translation(-pb.head)
        pb.matrix = T1 @ R_ @ T0_ @ pb.matrix; bpy.context.view_layer.update()
    def walk(i):
        t = i / 24.0
        for b in PB: b.matrix_basis = base[b.name]    # 처음 자세(차렷)로 되돌림
        bpy.context.view_layer.update()
        fy = {sd: foot_y(sd, t) for sd in ("L", "R")}
        gap = abs(fy["L"] - fy["R"])
        drop = LL - math.sqrt(max(LL * LL - (gap / 2) ** 2, 1e-6)) + 0.004 * min(1, gap / STEP)
        def smoother(u): u = min(1.0, max(0.0, u)); return u * u * u * (u * (6 * u - 15) + 10)
        py_ = 0.5 * (-2 * STEP * smoother((t - T0 + 0.1) / (TEND - T0 + 0.05))) + 0.5 * (fy['L'] + fy['R']) / 2   # 골반: 고르게 앞으로 + 두 발 가운데를 반씩 (멈칫도, 무릎 굽힘도 없게)
        lead = (fy["R"] - fy["L"]) / max(STEP, 1e-3)                            # -1: 오른발이 앞, +1: 왼발이 앞
        sway = 0.012 * math.sin(math.pi * (fy["R"] - fy["L"]) / max(STEP, 1e-3))   # 몸무게를 디딘 발 쪽으로 살짝
        # 골반 높이: 골반이 고르게 앞으로 가니 두 발 가운데가 아님 → 더 먼 발에 닿을 만큼만 낮춤 (가운데로 계산하면 너무 낮아 무릎이 굽은 채 걸었음)
        far = max(abs(py_ - fy["L"]), abs(py_ - fy["R"]))
        drop = LL - math.sqrt(max(LL * LL - far * far, 1e-6)) + 0.003 * min(1, gap / STEP)
        off = mathutils.Vector((sway, py_, -drop))
        hp = PB["Hips"]; hp.matrix = mathutils.Matrix.Translation(M3i @ off) @ hp.matrix; bpy.context.view_layer.update()
        walking = 1.0 if T0 - 0.1 < t < TEND + 0.1 else 0.0
        rot_world("Hips", (0, 0, 1), -0.07 * lead * walking)                   # 골반: 앞으로 나간 다리 쪽이 앞으로 돌아감
        rot_world("Hips", (0, 1, 0), 0.03 * math.sin(math.pi * lead) * walking)  # 골반 좌우 기울임 (디딘 쪽이 올라감)
        if "Chest" in PB: rot_world("Chest", (0, 0, 1), 0.10 * lead * walking)  # 가슴은 반대로 (골반 돌림을 되돌리고 조금 더)
        if "Spine" in PB: rot_world("Spine", (1, 0, 0), -0.05 * smoother((t - T0) / 0.3) * (1 - smoother((t - TEND) / 0.4)))   # 걸을 때 살짝 앞으로
        for sd in ("L", "R"):
            g = leg[sd]; H = MW @ PB[f"UpperLeg.{sd}"].head
            pit = foot_pitch(foot_u(sd, t))
            F = g["F0"] + mathutils.Vector((0, fy[sd], foot_lift(sd, t) + 0.14 * math.sin(max(pit, 0.0))))   # 뒤꿈치를 들면 발목도 그만큼 올라감
            d = F - H; dl = min(d.length, g["L1"] + g["L2"] - 1e-4)
            if os.environ.get('WALKDBG'): print('DBG', i, sd, round(d.length, 3), round(g['L1'] + g['L2'], 3), 'H', tuple(round(v, 3) for v in H), 'F', tuple(round(v, 3) for v in F), 'drop', round(drop, 3), 'py', round(py_, 3))
            ca = (g["L1"] ** 2 + dl ** 2 - g["L2"] ** 2) / (2 * g["L1"] * dl); ang = math.acos(max(-1, min(1, ca)))
            dn = d.normalized(); fwd = mathutils.Vector((0, -1, 0)); side = dn.cross(fwd).normalized(); perp = side.cross(dn).normalized()
            if perp.dot(fwd) < 0: perp = -perp
            knee = H + (dn * math.cos(ang) + perp * math.sin(ang)) * g["L1"]
            set_world_aim(f"UpperLeg.{sd}", lambda sd=sd: MW @ PB[f"LowerLeg.{sd}"].head, knee)
            set_world_aim(f"LowerLeg.{sd}", lambda sd=sd: MW @ PB[f"Foot.{sd}"].head, F)
            fb = PB[f"Foot.{sd}"]; rot = FOOT0[sd]                                # 발은 처음 방향 그대로 (바닥과 평평)
            fb.matrix = mathutils.Matrix.Translation(fb.matrix.translation) @ rot; bpy.context.view_layer.update()
            if abs(pit) > 1e-4: rot_world(f"Foot.{sd}", (1, 0, 0), pit)
        # 팔 흔들기: 오른다리가 앞이면 왼팔이 앞
        sw = 0.34 * lead * walking
        for sd in ("L", "R"):
            ub = f"UpperArm.{sd}"
            if ub not in PB: continue
            sgn = 1 if (MW @ PB[ub].head).x > 0 else -1
            s_ = sw if sd == "L" else -sw                                     # +면 앞(-y)으로
            tgt = (MW @ PB[ub].head) + mathutils.Vector((sgn * CH_U, -0.03 + s_ * 0.9, -1.0))
            set_world_aim(ub, lambda sd=sd: MW @ PB[f"ForeArm.{sd}"].head, tgt)
            fa = f"ForeArm.{sd}"
            if fa in PB and s_ > 0:                                             # 앞으로 갈 때 팔꿈치 살짝 굽힘
                rot_world(fa, (1, 0, 0), -0.5 * s_)
        return mathutils.Vector((0, py_, 0))
    ROOT0 = {r.name: r.matrix_world.copy() for r in roots}
    sm2_ = lambda u: u * u * (3 - 2 * u)
    def dance(i):
        """4박 한 마디씩 동작을 바꿈 (사용자 2026-11-24 '손뼉, 한 바퀴 돌기, 엉덩이 흔들기'):
           마디1 스텝 터치 → 마디2 손뼉(2·4박에 짝) → 마디3 엉덩이 흔들기 → 마디4 한 바퀴 돌기 → 다시 처음.
           박마다 무릎 반동, 팔은 마디 사이에서 부드럽게 바뀜"""
        t = i / 24.0; t0 = 0.4
        for b in PB: b.matrix_basis = base[b.name]
        for r in roots: r.matrix_world = ROOT0[r.name]
        bpy.context.view_layer.update()
        on = sm2_(min(1.0, max(0.0, (t - t0) / 0.8)))                       # 춤 시작도 0.8초에 걸쳐 천천히
        bt = max(0.0, (t - t0)) * BPM / 60.0
        bar = int(bt // 4) % len(ROUTINE); ph = bt % 4.0; mvname = ROUTINE[bar]
        sm2 = lambda u: u * u * (3 - 2 * u)
        SW = 0.20; xR = xL = 0.0; mv = None; u = 0.0; hipx = 0.0
        if mvname == "스텝":
            if ph < 1:   xR = -SW * sm2(ph);              mv, u = "R", ph
            elif ph < 2: xR, xL = -SW, -SW * sm2(ph - 1); mv, u = "L", ph - 1
            elif ph < 3: xR, xL = -SW, -SW * (1 - sm2(ph - 2)); mv, u = "L", ph - 2
            else:        xR = -SW * (1 - sm2(ph - 3));    mv, u = "R", ph - 3
        elif mvname == "엉덩이":
            hipx = 0.09 * math.sin(math.pi * ph) * min(1.0, ph * 2, (4 - ph) * 2)   # 박마다 좌우로 크게
        xR *= on; xL *= on; fx = {"R": xR, "L": xL}
        bounce = (0.035 if mvname != "돌기" else 0.02) * (0.5 - 0.5 * math.cos(2 * math.pi * bt)) * on
        px = (xR + xL) / 2 + hipx * on
        hp = PB["Hips"]; off = mathutils.Vector((px, 0, -bounce - 0.006 * on))
        hp.matrix = mathutils.Matrix.Translation(M3i @ off) @ hp.matrix; bpy.context.view_layer.update()
        side = math.sin(math.pi * bt / 2) if mvname != "엉덩이" else math.sin(math.pi * ph) * 1.6
        rot_world("Hips", (0, 1, 0), -0.10 * side * on)
        rot_world("Hips", (0, 0, 1), 0.05 * side * on)
        if "Chest" in PB: rot_world("Chest", (0, 1, 0), 0.12 * side * on); rot_world("Chest", (0, 0, 1), -0.14 * side * on)
        if "Head" in PB: rot_world("Head", (1, 0, 0), 0.05 * math.sin(2 * math.pi * bt) * on)
        for sd in ("L", "R"):
            g = leg[sd]; H = MW @ PB[f"UpperLeg.{sd}"].head
            lift = 0.03 * math.sin(math.pi * u) * on if sd == mv else 0.0
            if mvname == "돌기": lift = 0.02 * max(0.0, math.sin(2 * math.pi * bt + (0 if sd == "L" else math.pi))) * on   # 돌면서 발을 번갈아 살짝
            F = g["F0"] + mathutils.Vector((fx[sd], 0, lift))
            d = F - H; dl = min(d.length, g["L1"] + g["L2"] - 1e-4)
            ca = (g["L1"] ** 2 + dl ** 2 - g["L2"] ** 2) / (2 * g["L1"] * dl); ang = math.acos(max(-1, min(1, ca)))
            dn = d.normalized(); fwd = mathutils.Vector((0, -1, 0)); sidev = dn.cross(fwd).normalized(); perp = sidev.cross(dn).normalized()
            if perp.dot(fwd) < 0: perp = -perp
            knee = H + (dn * math.cos(ang) + perp * math.sin(ang)) * g["L1"]
            set_world_aim(f"UpperLeg.{sd}", lambda sd=sd: MW @ PB[f"LowerLeg.{sd}"].head, knee)
            set_world_aim(f"LowerLeg.{sd}", lambda sd=sd: MW @ PB[f"Foot.{sd}"].head, F)
            fb = PB[f"Foot.{sd}"]; fb.matrix = mathutils.Matrix.Translation(fb.matrix.translation) @ FOOT0[sd]; bpy.context.view_layer.update()
        # 팔: 동작별 (위팔 방향, 아래팔 방향) — 마디가 바뀌기 전 0.35박 동안 다음 동작 쪽으로 섞음
        def arm_dirs(name, ph_, sgn, sd):
            V = mathutils.Vector
            if name == "스텝":
                w = math.sin(math.pi * (bt if True else 0) + (0 if sd == "L" else math.pi))
                return V((sgn * 0.55, -0.30 - 0.20 * w, -0.75 + 0.22 * w)), V((sgn * 0.05, -0.75, 0.55 + 0.22 * w))   # 흔드는 폭을 줄여 팔이 휙휙 움직이지 않게
            if name == "손뼉":
                c = math.sin(math.pi * ph_ / 2) ** 2                              # 1·3박(=2·4번째 박)에 손이 만남
                return V((sgn * 0.30, -0.65, -0.70)), V((-sgn * (0.2 + 0.75 * c), -0.75 + 0.25 * c, 0.45 - 0.15 * c))
            if name == "엉덩이":
                return V((sgn * 0.65, 0.20, -0.75)), V((-sgn * 0.55, -0.05, -0.65))   # 팔꿈치를 옆으로, 손은 허리에
            if name == "돌기":
                return V((sgn * 0.85, -0.15, -0.50)), V((sgn * 0.85, -0.30, -0.25))   # 팔을 옆으로 벌려 돎
            return V((sgn * CH_U, -0.03, -1.0)), V((sgn * CH_F, -0.10, -1.0))
        nxt = ROUTINE[(bar + 1) % len(ROUTINE)]; bl = sm2(min(1.0, max(0.0, (ph - 3.0) / 1.0)))   # 마디 마지막 1박 동안 천천히 다음 동작으로 (0.35박이면 팔이 순간 휙 바뀌었음, 사용자 2026-11-24)
        for sd in ("L", "R"):
            ub, fa, hb_ = f"UpperArm.{sd}", f"ForeArm.{sd}", f"Hand.{sd}"
            if ub not in PB or hb_ not in PB: continue
            sgn = 1 if (MW @ PB[ub].head).x > 0 else -1
            u1, f1 = arm_dirs(mvname, ph, sgn, sd); u2, f2 = arm_dirs(nxt, 0.0, sgn, sd); u0, f0 = arm_dirs("차렷", 0, sgn, sd)
            ud = (u1 * (1 - bl) + u2 * bl) * on + u0 * (1 - on); fd = (f1 * (1 - bl) + f2 * bl) * on + f0 * (1 - on)
            set_world_aim(ub, lambda fa=fa: MW @ PB[fa].head, (MW @ PB[ub].head) + ud)
            set_world_aim(fa, lambda hb_=hb_: MW @ PB[hb_].head, (MW @ PB[fa].head) + fd)
        # 한 바퀴 돌기: 몸 전체를 제자리에서 4박 동안 한 바퀴
        if mvname == "돌기" and on > 0:
            Rz = mathutils.Matrix.Rotation(2 * math.pi * sm2(ph / 4.0), 4, "Z")
            for r in roots: r.matrix_world = Rz @ ROOT0[r.name]
            bpy.context.view_layer.update()
        return mathutils.Vector((0, 0, 0))
    if DANCE: walk = dance
else:
    walk = lambda i: mathutils.Vector((0, 0, 0))

# ── 입·눈 ──
lip = json.load(open(opt["--입"])) if opt["--입"] else {"frames": []}
blinks = [1.3, 4.2, 7.0, 9.8, 12.6]
def face(i):
    t = i / 24.0; lf = lip["frames"][i] if i < len(lip["frames"]) else [0, 0, 0]
    set_shape("MouthOpen", lf[0]); set_shape("MouthWide", lf[1]); set_shape("MouthRound", lf[2])
    set_shape("Blink", max([0.0] + [max(0.0, 1 - abs(t - c) / 0.07) for c in blinks]))

os.makedirs(folder, exist_ok=True)
if "--찍점" in a:      # 검사용: 화면 점(x,y) 아래에 무엇이 있는지 (물체·재질·겉면 그림 좌표)
    px, py = (float(v) for v in a[a.index("--찍점") + 1].split(","))
    fi_ = int(opt["--미리보기"] or 0); sc.frame_set(fi_); WHO[0] = walk(fi_); place(fi_, WHO[0] * 0.6); bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get(); fr = cam.data.view_frame(scene=sc)
    tr, br, bl, tl = [cam.matrix_world @ v for v in fr]; u, v = px / W_, py / H_
    tgt = tl + (tr - tl) * u + (bl - tl) * v; o = cam.matrix_world.translation; d = (tgt - o).normalized()
    for _ in range(4):
        hit, loc, nor, fi, ob, mw = sc.ray_cast(dg, o, d)
        if not hit: print("찍점: 없음"); break
        me = ob.evaluated_get(dg).data; poly = me.polygons[fi]
        uvl = me.uv_layers.active; uv = [tuple(round(c, 4) for c in uvl.data[li].uv) for li in poly.loop_indices] if uvl else None
        print("찍점:", ob.name, "재질", me.materials[poly.material_index].name if me.materials else None, "면", fi, "위치", tuple(round(c, 3) for c in loc),
              "앞면" if nor.dot(d) < 0 else "뒷면", "uv", uv)
        o = loc + d * 1e-4
    sys.exit(0)
frames = [int(opt["--미리보기"])] if opt["--미리보기"] else range(int(opt["--시작장"]), N if int(opt["--끝장"]) < 0 else int(opt["--끝장"]))
for i in frames:
    who = walk(i); WHO[0] = who; place(i, who * 0.6); face(i)     # 카메라는 인물을 반쯤 따라감 (나머지는 인물이 다가오는 느낌)
    sc.render.filepath = os.path.join(os.path.abspath(folder), f"f{i:04d}.png"); bpy.ops.render.render(write_still=True)
print("찍음:", len(list(frames)), "장 →", folder)
