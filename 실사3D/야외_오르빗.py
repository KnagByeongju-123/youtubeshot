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


def fetch(PLACE=PLACE):
    o = urllib.request.build_opener(); o.addheaders = [("User-Agent", "asset-fetcher/1.0")]; urllib.request.install_opener(o)
    f = None
    for name, key in ((f"{PLACE}.jpg", "tonemapped"), (f"{PLACE}_1k.hdr", "hdr")):
        p = os.path.join(A, name)
        if os.path.exists(p): continue
        f = f or json.load(urllib.request.urlopen(f"https://api.polyhaven.com/files/{PLACE}"))
        url = f["tonemapped"]["url"] if key == "tonemapped" else f["hdri"]["1k"]["hdr"]["url"]
        urllib.request.urlretrieve(url, p); print("받음", p)


fetch()
# 배경 바꾸기(--장소2 <HDRI> --방향2 0.5 --전환 4.0,4.9): 전환 시간 동안 사진(카메라에 보이는 것·빛 모두)이 두 번째 장소로 부드럽게 바뀜 (사용자 2026-11-24 '정면으로 돌 때 해변으로')
PLACE2 = a[a.index("--장소2") + 1] if "--장소2" in a else None
XF_T = [float(v) for v in a[a.index("--전환") + 1].split(",")] if "--전환" in a else [4.0, 4.9]
if PLACE2: fetch(PLACE2)
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
W_, H_ = (int(v) for v in opt["--크기"].split("x"))
sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"; sc.cycles.samples = int(opt["--샘플"]); sc.cycles.use_denoising = True
sc.render.resolution_x, sc.render.resolution_y = W_, H_; sc.render.film_transparent = "--투명" in a   # --투명: 배경 없이(인물만) 찍음 — 의상 바꾸기 기준 사진용
sc.view_settings.view_transform = "Standard"; sc.cycles.max_bounces = 4
sc.render.fps = 24
if "--영역" in a:   # 이 칸만 찍음(x0,y0,x1,y1 화면 비율, 위가 0) — 몸이 가만히 있고 입·눈만 움직이는 장면은 얼굴 칸만 찍어 한 장에 붙이면 몇 배 빠름 (교육 영상, 2026-11-25)
    bx0, by0, bx1, by1 = (float(v) for v in a[a.index("--영역") + 1].split(","))
    sc.render.use_border = True; sc.render.use_crop_to_border = True
    sc.render.border_min_x, sc.render.border_max_x = bx0, bx1; sc.render.border_min_y, sc.render.border_max_y = 1 - by1, 1 - by0

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
XF = None
if PLACE2:
    mp2 = nt.nodes.new("ShaderNodeMapping"); nt.links.new(tc.outputs["Generated"], mp2.inputs["Vector"])
    mp2.inputs["Rotation"].default_value = (0, 0, math.radians((float(a[a.index("--방향2") + 1] if "--방향2" in a else 0.5) - 0.75) * 360))
    e_cam2 = nt.nodes.new("ShaderNodeTexEnvironment"); e_cam2.image = bpy.data.images.load(os.path.join(A, f"{PLACE2}.jpg"))
    e_lit2 = nt.nodes.new("ShaderNodeTexEnvironment"); e_lit2.image = bpy.data.images.load(os.path.join(A, f"{PLACE2}_1k.hdr"))
    for e in (e_cam2, e_lit2): nt.links.new(mp2.outputs["Vector"], e.inputs["Vector"])
    XF = nt.nodes.new("ShaderNodeValue"); XF.outputs[0].default_value = 0.0
    mixes = []
    for e1, e2, dst_ in ((e_cam, e_cam2, b_cam), (e_lit, e_lit2, b_lit)):
        mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = "RGBA"
        nt.links.new(XF.outputs[0], mx.inputs["Factor"]); nt.links.new(e1.outputs["Color"], mx.inputs[6]); nt.links.new(e2.outputs["Color"], mx.inputs[7])
        nt.links.new(mx.outputs[2], dst_.inputs["Color"])
else:
    nt.links.new(e_cam.outputs["Color"], b_cam.inputs["Color"]); nt.links.new(e_lit.outputs["Color"], b_lit.inputs["Color"])
def set_xf(i):
    if XF is None: return
    t = i / 24.0; u = min(1.0, max(0.0, (t - XF_T[0]) / max(XF_T[1] - XF_T[0], 1e-6)))
    XF.outputs[0].default_value = u * u * (3 - 2 * u)
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
    sc_objs = set(bpy.context.scene.objects)          # 불러오기가 만든 숨은 뼈 모양(Icosphere)은 빼고 (Rocketbox 인물이 1m 떠 있었음, 2026-11-26)
    pts = [o.matrix_world @ mathutils.Vector(c) for o in objs if o.type == "MESH" and o in sc_objs and o.name != "Icosphere" for c in o.bound_box]
    return pts
pts = bbox(); k = float(opt["--키"]) / (max(p.z for p in pts) - min(p.z for p in pts))
for r in roots: r.scale = (r.scale[0] * k, r.scale[1] * k, r.scale[2] * k)
bpy.context.view_layer.update(); pts = bbox()
for r in roots:
    r.location.x -= (min(p.x for p in pts) + max(p.x for p in pts)) / 2; r.location.y -= (min(p.y for p in pts) + max(p.y for p in pts)) / 2
    r.location.z -= min(p.z for p in pts)
if "--인물방향" in a:     # 인물을 제자리에서 돌림(도, + = 화면 오른쪽을 봄) — 사용자 2026-11-25 '아나운서는 오른쪽 방향을 보게'
    bpy.context.view_layer.update()                                       # 위에서 옮긴 자리를 먼저 반영 (안 하면 돌릴 때 옮기기 전 자리로 돌아감)
    Rz_ = mathutils.Matrix.Rotation(math.radians(float(a[a.index("--인물방향") + 1])), 4, "Z")
    for r in roots: r.matrix_world = Rz_ @ r.matrix_world
    bpy.context.view_layer.update()
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
POINT_SIDE = a[a.index('--가리킬손') + 1] if '--가리킬손' in a else 'R'
WRAP = float(a[a.index('--감싸기') + 1]) if '--감싸기' in a else 0.42; CUP_GRIP = a[a.index('--컵잡기') + 1] if '--컵잡기' in a else '한손'; WRAP1 = float(a[a.index('--한손감싸기') + 1]) if '--한손감싸기' in a else 0.55; CUP_MID = 0.12; CUP_UP = -0.035; CUP_SIDE = 'R'; SEAT_H = float(a[a.index('--의자높이') + 1]) if '--의자높이' in a else 0.46; CAFE_DY = 0.0                          # 커피: 컵 든 손, 의자 앉는 판 높이(m)   # 가리키기: 어느 손으로 (R/L)
ARMUP = float(a[a.index('--팔높이') + 1]) if '--팔높이' in a else 0.0   # 팔벌려: 0 = 수평, -0.3 = 살짝 아래
HAND_S = float(a[a.index('--손굵기') + 1]) if '--손굵기' in a else 1.0     # 손 굵기는 모델에서 직접 가늘게 함(glb_손가늘게.py) — 뼈 크기로 줄이면 손가락 틈이 벌어졌음
MIC_F = (0.30, 0.45, 0.85); MIC_CURL = 1.25; FIST = float(a[a.index('--주먹') + 1]) if '--주먹' in a else 0.32   # 주먹 = 마디마다 굽힘(라디안)
CH_U, CH_F = (float(v) for v in (a[a.index('--팔벌림') + 1] if '--팔벌림' in a else '0.12,0.10').split(','))   # 차렷 팔이 몸에서 떨어진 정도(위팔,아래팔)
arm = next((o for o in objs if o.type == "ARMATURE"), None)
SHRUG = float(a[a.index('--어깨들기') + 1]) if '--어깨들기' in a else 0.7    # 팔을 들 때 어깨 뼈가 같이 드는 비율 (어깨 뼈가 있는 모델만, glb_어깨뼈.py)
def shrug(sd, arm_dir_world):
    """어깨 뼈(Shoulder.L/R)를 팔 방향 쪽으로 '팔이 수평 아래 50° 를 넘어 든 만큼 × SHRUG' 돌림 — 어깨선이 팔과 이어지게"""
    if arm is None or f"Shoulder.{sd}" not in arm.pose.bones: return
    pb = arm.pose.bones[f"Shoulder.{sd}"]; bpy.context.view_layer.update()
    MW_ = arm.matrix_world; d = mathutils.Vector(arm_dir_world).normalized(); down = mathutils.Vector((0, 0, -1))
    elev = down.angle(d)                                                        # 0 = 팔이 곧게 아래, 90° = 수평
    amt = max(0.0, elev - math.radians(40)) * SHRUG
    if amt < 1e-4: return
    ax = down.cross(d)
    if ax.length < 1e-6: return
    R_ = (MW_.inverted().to_3x3() @ mathutils.Matrix.Rotation(amt, 3, ax.normalized()) @ MW_.to_3x3()).to_4x4()
    T1 = mathutils.Matrix.Translation(pb.head); T0 = mathutils.Matrix.Translation(-pb.head)
    pb.matrix = T1 @ R_ @ T0 @ pb.matrix; bpy.context.view_layer.update()
if arm is not None and "--자세없음" not in a:
    bpy.context.view_layer.objects.active = arm; bpy.ops.object.mode_set(mode="POSE")
    MW = arm.matrix_world; MWi = MW.inverted()
    def aim_bone(name_cands, target_dir_world, child_cands):
        """뼈를 관절 기준으로 돌려, 이 관절→다음 관절(자식) 방향이 목표 방향이 되게 (블렌더 뼈 꼬리 방향은 실제 팔 방향과 다를 수 있음)"""
        pb = next((arm.pose.bones[n] for n in name_cands if n in arm.pose.bones), None)
        ch = next((arm.pose.bones[n] for n in child_cands if n in arm.pose.bones), None)
        if pb is None or ch is None: return
        if pb.name.startswith("UpperArm."): shrug(pb.name[-1], target_dir_world)
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
    def curl(side, amt, thumb=None, only=None):
        """손가락을 손바닥 쪽으로 굽힘 (amt = 마디마다 굽히는 각도, 라디안). only: 이 손가락들만"""
        if side not in palm: return
        for f in (only or ("Index", "Middle", "Ring", "Little", "Thumb")):
            th0 = (thumb if thumb is not None else amt * 0.5) if f == "Thumb" else amt
            fm = {"Index": 0.92, "Middle": 1.0, "Ring": 1.05, "Little": 1.1, "Thumb": 1.0}[f]   # 새끼 쪽일수록 조금 더 (실제 주먹처럼)
            for k in (1, 2, 3):
                th = th0 * fm * ((0.85, 1.2, 0.8) if f != "Thumb" else (0.5, 1.0, 1.0))[k - 1]     # 가운데 마디를 가장 많이, 엄지 뿌리는 조금만
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
    if POSE == '커피':                                          # 노천카페 의자에 앉음 (사용자 2026-11-24 '노천카페에 앉아서 커피 마시는 장면')
        bpy.context.view_layer.update()
        foot0 = {sd: B(f"Foot.{sd}").matrix.to_3x3().to_4x4() for sd in ("L", "R") if B(f"Foot.{sd}")}
        hz = (W(B("UpperLeg.L")).z + W(B("UpperLeg.R")).z) / 2
        drop = hz - (SEAT_H + 0.09)                                # 엉덩관절 = 앉는 판 위 9cm
        hp_ = B("Hips"); hp_.matrix = mathutils.Matrix.Translation(MWi.to_3x3() @ mathutils.Vector((0, 0.04, -drop))) @ hp_.matrix
        bpy.context.view_layer.update()
        if "Spine" in arm.pose.bones:                              # 상체는 곧게, 아주 살짝 앞으로
            sp = B("Spine"); R_ = (MWi.to_3x3() @ mathutils.Matrix.Rotation(math.radians(6), 3, (1, 0, 0)) @ MW.to_3x3()).to_4x4()
            sp.matrix = mathutils.Matrix.Translation(sp.head) @ R_ @ mathutils.Matrix.Translation(-sp.head) @ sp.matrix; bpy.context.view_layer.update()
        for sd, sx in (("L", 1), ("R", -1)):
            aim_bone([f"UpperLeg.{sd}"], (sx * 0.06, -1.0, -0.08), [f"LowerLeg.{sd}"])   # 허벅지: 앞으로 거의 수평
            aim_bone([f"LowerLeg.{sd}"], (sx * 0.02, -0.12, -1.0), [f"Foot.{sd}"])        # 종아리: 아래로
            fb_ = B(f"Foot.{sd}"); fb_.matrix = mathutils.Matrix.Translation(fb_.matrix.translation) @ foot0[sd]; bpy.context.view_layer.update()
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
        elif POSE == '커피' and CUP_GRIP == '한손' and side != CUP_SIDE:   # 한손 잡기: 다른 팔은 탁자 위에
            aim_bone(ub, (sgn * 0.15, -0.45, -0.88), fb)
            aim_bone(fb, (-sgn * 0.30, -0.95, -0.02), hb)
            aim_bone(hb, (-sgn * 0.20, -0.95, -0.15), [f"Middle1.{side}"])
            curl(side, 0.35, thumb=0.2)
        elif POSE == '커피' and CUP_GRIP == '한손':             # 한손 잡기: 손 모양을 먼저 잡고(손가락이 앞을 향해 C 자로 컵을 감쌀 모양), 컵은 그 손 안에 맞춰 놓음 (사용자 2026-11-25)
            aim_bone(ub, (sgn * 0.28, -0.30, -0.91), fb)
            aim_bone(fb, (-sgn * 0.30, -0.85, 0.42), hb)
            aim_bone(hb, (-sgn * 0.10, -0.98, 0.10), [f"Middle1.{side}"])
            if side in palm:                                       # 손바닥이 몸 가운데 쪽(컵 쪽)을 보게
                bpy.context.view_layer.update()
                hpb_ = B(f"Hand.{side}"); ax_ = (W(B(f"Middle1.{side}")) - W(hpb_)).normalized()
                n_ = palm_now(side); tg_ = mathutils.Vector((-sgn, 0, -0.15)); tg_ = (tg_ - ax_ * ax_.dot(tg_)).normalized(); n_ = (n_ - ax_ * ax_.dot(n_)).normalized()
                ang_ = math.atan2(ax_.dot(n_.cross(tg_)), n_.dot(tg_))
                R_ = (MWi.to_3x3() @ mathutils.Matrix.Rotation(ang_, 3, ax_) @ MW.to_3x3()).to_4x4()
                hpb_.matrix = mathutils.Matrix.Translation(hpb_.head) @ R_ @ mathutils.Matrix.Translation(-hpb_.head) @ hpb_.matrix; bpy.context.view_layer.update()
            curl(side, WRAP1, thumb=0.45)                          # C 자로 둥글게, 엄지는 맞은편
        elif POSE == '커피':                                     # 두 손으로 컵을 감싸 쥠 (사용자 2026-11-25 선택: 손잡이 대신 감싸 쥐기)
            aim_bone(ub, (sgn * 0.26, -0.32, -0.91), fb)
            aim_bone(fb, (-sgn * 0.55, -0.72, 0.42), hb)
            aim_bone(hb, (-sgn * 0.30, -0.80, 0.52), [f"Middle1.{side}"])
            if side in palm:                                       # 손바닥이 서로 마주 보게 (몸 가운데 쪽)
                bpy.context.view_layer.update()
                hpb_ = B(f"Hand.{side}"); ax_ = (W(B(f"Middle1.{side}")) - W(hpb_)).normalized()
                n_ = palm_now(side); tg_ = mathutils.Vector((-sgn, 0.15, -0.1)); tg_ = (tg_ - ax_ * ax_.dot(tg_)).normalized(); n_ = (n_ - ax_ * ax_.dot(n_)).normalized()
                ang_ = math.atan2(ax_.dot(n_.cross(tg_)), n_.dot(tg_))
                R_ = (MWi.to_3x3() @ mathutils.Matrix.Rotation(ang_, 3, ax_) @ MW.to_3x3()).to_4x4()
                hpb_.matrix = mathutils.Matrix.Translation(hpb_.head) @ R_ @ mathutils.Matrix.Translation(-hpb_.head) @ hpb_.matrix; bpy.context.view_layer.update()
            curl(side, WRAP, thumb=0.25)                          # 손가락을 둥글게 (컵 몸통을 감쌈)
        elif POSE == '가리키기' and side == POINT_SIDE:          # 한쪽 팔을 들어 검지로 앞을 가리킴 (사용자 2026-11-24)
            aim_bone(ub, (sgn * 0.22, -1.0, 0.18), fb)          # 위팔: 앞으로, 어깨보다 살짝 위·바깥
            aim_bone(fb, (sgn * 0.12, -1.0, 0.22), hb)          # 아래팔: 거의 곧게
            aim_bone(hb, (sgn * 0.05, -1.0, 0.20), [f"Middle1.{side}"])
            curl(side, 1.05, only=("Middle", "Ring", "Little"))   # 가운데·약지·새끼는 쥐고
            curl(side, 0.0, thumb=0.95, only=("Thumb",))          # 엄지는 접어 가운데손가락 위로 (0.55 는 총 모양처럼 섰음)
            curl(side, 0.06, only=("Index",))                     # 검지만 곧게 (힘 살짝 뺌)
        elif POSE == '팔벌려':                                  # 두 팔을 옆으로 어깨 높이까지 활짝 (사용자 2026-11-24 어깨 확인)
            aim_bone(ub, (sgn * 1.0, 0.0, ARMUP), fb)           # 위팔: 옆으로 (ARMUP 0 = 수평)
            aim_bone(fb, (sgn * 1.0, 0.0, ARMUP), hb)
            aim_bone(hb, (sgn * 1.0, 0.0, ARMUP), [f"Middle1.{side}"])
            curl(side, 0.12, thumb=0.05)
        elif POSE == '손바닥':                                   # 손바닥을 펴서 앞(카메라)으로 보여 줌 (사용자 2026-11-24)
            aim_bone(ub, (sgn * 0.45, -0.35, -0.82), fb)       # 위팔: 옆·아래로, 팔꿈치는 몸 옆
            aim_bone(fb, (sgn * 0.12, -0.35, 0.93), hb)        # 아래팔: 거의 곧게 위로 → 손이 어깨 높이
            aim_bone(hb, (sgn * 0.05, -0.15, 1.0), [f"Middle1.{side}"])   # 손가락이 위를 향하게
            if side in palm:                                   # 손바닥이 앞(-y)을 보도록 손을 손가락 축으로 돌림
                bpy.context.view_layer.update()
                hpb_ = B(f"Hand.{side}"); ax_ = (W(B(f"Middle1.{side}")) - W(hpb_)).normalized()
                n_ = palm_now(side); tgt_ = mathutils.Vector((0, -1, 0)); tgt_ = (tgt_ - ax_ * ax_.dot(tgt_)).normalized(); n_ = (n_ - ax_ * ax_.dot(n_)).normalized()
                ang_ = math.atan2(ax_.dot(n_.cross(tgt_)), n_.dot(tgt_))
                R_ = (MWi.to_3x3() @ mathutils.Matrix.Rotation(ang_, 3, ax_) @ MW.to_3x3()).to_4x4()
                T1 = mathutils.Matrix.Translation(hpb_.head); T0 = mathutils.Matrix.Translation(-hpb_.head)
                hpb_.matrix = T1 @ R_ @ T0 @ hpb_.matrix; bpy.context.view_layer.update()
            curl(side, 0.05, thumb=0.0)                        # 손가락은 펴고 힘만 살짝 뺌
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
    if POSE == '커피':
        # Poly Haven 노천카페 탁자·의자(outdoor_table_chair_set_01)와 찻잔(tea_set_01), CC0 — 사람 뒤에 의자, 앞에 탁자, 컵은 오른손에
        MD = os.path.join(ROOT, "models", "polyhaven", "_models")
        def imp(mid):
            b4 = set(bpy.data.objects); bpy.ops.import_scene.gltf(filepath=os.path.join(MD, mid, f"{mid}.gltf"))
            return {o.name: o for o in bpy.data.objects if o not in b4}
        fur = imp("outdoor_table_chair_set_01")
        Rz = mathutils.Matrix.Rotation(math.pi, 4, "Z")              # 의자 하나가 사람 쪽(-y 를 보게)
        for o in fur.values():
            if o.parent is None: o.matrix_world = mathutils.Matrix.Translation((0.03, -0.52 + CAFE_DY, 0)) @ Rz @ o.matrix_world
        tea = imp("tea_set_01")
        keep = {"tea_set_01_cup_small_01", "tea_set_01_saucer_circular_04"}
        bpy.context.view_layer.update()
        tbl = next(o for n, o in fur.items() if n.endswith("_table")); ttop = max((tbl.matrix_world @ mathutils.Vector(c)).z for c in tbl.bound_box)
        tcen = sum((tbl.matrix_world @ mathutils.Vector(c) for c in tbl.bound_box), mathutils.Vector()) / 8
        for n, o in tea.items():
            if o.type != "MESH": continue
            if not any(n.startswith(k) for k in keep): o.hide_render = True; continue
        cup = next(o for n, o in tea.items() if n.startswith("tea_set_01_cup_small_01") and o.type == "MESH")
        sau = next(o for n, o in tea.items() if n.startswith("tea_set_01_saucer_circular_04") and o.type == "MESH")
        def move_to(o, p):
            bpy.context.view_layer.update(); bb = [o.matrix_world @ mathutils.Vector(c) for c in o.bound_box]
            c0 = mathutils.Vector((sum(q.x for q in bb) / 8, sum(q.y for q in bb) / 8, min(q.z for q in bb)))
            o.matrix_world = mathutils.Matrix.Translation(p - c0) @ o.matrix_world
        move_to(sau, mathutils.Vector((tcen.x - 0.12, tcen.y + 0.10, ttop)))
        bpy.context.view_layer.update()
        h_ = arm.pose.bones[f"Hand.{CUP_SIDE}"]
        bpy.context.view_layer.update()
        if CUP_GRIP == '한손':
            # 손 모양에 컵을 맞춤: 손바닥 가운데·손가락 마디·엄지 끝을 위에서 본 점들로 원을 맞춰 그 원의 가운데 = 컵 축, 높이는 손가락 높이
            MWc = arm.matrix_world; PBc = arm.pose.bones; sd_ = CUP_SIDE
            pts = [(MWc @ PBc[f"Hand.{sd_}"].head) * 0.3 + (MWc @ PBc[f"Middle1.{sd_}"].head) * 0.7]
            for f_ in ("Index", "Middle", "Ring", "Little"):
                pts += [MWc @ PBc[f"{f_}2.{sd_}"].head, MWc @ PBc[f"{f_}3.{sd_}"].head, MWc @ PBc[f"{f_}3.{sd_}"].tail]
            pts += [MWc @ PBc[f"Thumb3.{sd_}"].tail]
            import numpy as _np
            X = _np.array([[q.x, q.y] for q in pts]); A_ = _np.c_[2 * X, _np.ones(len(X))]; b_ = (X ** 2).sum(1)
            cx, cy, c_ = _np.linalg.lstsq(A_, b_, rcond=None)[0]; rr = float(_np.sqrt(c_ + cx * cx + cy * cy))
            # 손 모양 원이 컵보다 작으면(손가락이 컵 속으로) → 손바닥에서 손바닥 방향으로 '컵 반지름 + 1.2cm' 떨어진 곳을 컵 축으로
            vw_ = [cup.matrix_world @ v.co for v in cup.data.vertices]; zz0 = min(v.z for v in vw_); zz1 = max(v.z for v in vw_)
            bo_ = [v for v in vw_ if v.z < zz0 + 0.25 * (zz1 - zz0)]; ac_ = mathutils.Vector((sum(v.x for v in bo_) / len(bo_), sum(v.y for v in bo_) / len(bo_), 0))
            rim = [v for v in vw_ if v.z > zz1 - 0.01]; Rcup = max(((v.x - ac_.x) ** 2 + (v.y - ac_.y) ** 2) ** 0.5 for v in rim)
            Rbody = sorted(((v.x - ac_.x) ** 2 + (v.y - ac_.y) ** 2) ** 0.5 for v in vw_ if zz0 + 0.3 * (zz1 - zz0) < v.z < zz0 + 0.6 * (zz1 - zz0))[len(vw_) // 40 if False else 0]
            pn = palm_now(sd_); pn = mathutils.Vector((pn.x, pn.y, 0)).normalized()
            cc = pts[0] + pn * (Rcup * 0.85 + 0.012)
            if rr < Rcup: cx, cy = cc.x, cc.y
            zf = sum(q.z for q in pts) / len(pts)
            vw = [cup.matrix_world @ v.co for v in cup.data.vertices]; z0c, z1c = min(v.z for v in vw), max(v.z for v in vw)
            bod = [v for v in vw if v.z < z0c + 0.25 * (z1c - z0c)]
            axc = mathutils.Vector((sum(v.x for v in bod) / len(bod), sum(v.y for v in bod) / len(bod), z0c))
            far = max(vw, key=lambda v: (v.x - axc.x) ** 2 + (v.y - axc.y) ** 2)
            hdir = mathutils.Vector((far.x - axc.x, far.y - axc.y, 0)).normalized()
            pal = mathutils.Vector((pts[0].x - cx, pts[0].y - cy, 0)).normalized()   # 손바닥 쪽 → 손잡이는 반대(바깥)로
            ang = math.atan2(hdir.cross(-pal).z, hdir.dot(-pal))
            cup.matrix_world = mathutils.Matrix.Translation(axc) @ mathutils.Matrix.Rotation(ang, 4, "Z") @ mathutils.Matrix.Translation(-axc) @ cup.matrix_world
            cup.matrix_world = mathutils.Matrix.Translation(mathutils.Vector((cx, cy, zf - (z1c - z0c) * 0.45)) - axc) @ cup.matrix_world
            print(f"컵: 손 모양에 맞춘 원 반지름 {rr * 100:.1f}cm (컵 반지름 약 {((bod[0].x - axc.x) ** 2 + (bod[0].y - axc.y) ** 2) ** 0.5 * 100:.1f}~)")
            grip = mathutils.Vector((cx, cy, zf))
        # 두 손바닥 가운데에 컵 몸통 (손잡이는 몸 쪽으로 돌려 숨김) — 손바닥 사이가 컵 폭과 맞게 확인
        if CUP_GRIP != '한손':
            MWc = arm.matrix_world; PBc = arm.pose.bones
            pc = {s_: (MWc @ PBc[f"Hand.{s_}"].head) * 0.35 + (MWc @ PBc[f"Middle1.{s_}"].head) * 0.65 for s_ in ("L", "R")}
            mid = (pc["L"] + pc["R"]) / 2
            vw = [cup.matrix_world @ v.co for v in cup.data.vertices]; z0c, z1c = min(v.z for v in vw), max(v.z for v in vw)
            bod = [v for v in vw if v.z < z0c + 0.25 * (z1c - z0c)]
            axc = mathutils.Vector((sum(v.x for v in bod) / len(bod), sum(v.y for v in bod) / len(bod), z0c))
            far = max(vw, key=lambda v: (v.x - axc.x) ** 2 + (v.y - axc.y) ** 2)
            hdir = mathutils.Vector((far.x - axc.x, far.y - axc.y, 0)).normalized()
            ang = math.atan2(hdir.cross(mathutils.Vector((0, 1, 0))).z, hdir.dot(mathutils.Vector((0, 1, 0))))   # 손잡이 → 몸 쪽(+y)
            cup.matrix_world = mathutils.Matrix.Translation(axc) @ mathutils.Matrix.Rotation(ang, 4, "Z") @ mathutils.Matrix.Translation(-axc) @ cup.matrix_world
            cup.matrix_world = mathutils.Matrix.Translation(mid - (axc + mathutils.Vector((0, 0, (z1c - z0c) * CUP_MID)))) @ cup.matrix_world
            print(f"컵: 두 손바닥 사이 {(pc['L'] - pc['R']).length * 100:.1f}cm, 컵 폭 {2 * ((far.x - axc.x) ** 2 + (far.y - axc.y) ** 2) ** 0.5 * 100:.1f}cm(손잡이 포함)")
            grip = mid
        mw_ = cup.matrix_world.copy(); cup.parent = arm; cup.parent_type = "BONE"; cup.parent_bone = h_.name
        bpy.context.view_layer.update(); cup.matrix_world = mw_
        print("카페: 탁자 높이", round(ttop, 3), "컵", tuple(round(v, 3) for v in grip))
# ── 손 안내(--안내 t1,t2,...): 모음 자세에서 화면 왼쪽 손을 펴 옆(사진 쪽)으로 내밀었다가 돌아옴 — 사용자 2026-11-25 '아나운서가 손으로 안내'
#   두 자세(모음 A·안내 B)의 뼈 값을 기억해 두고, 장면마다 섞음(0.6초 올림·2.2초 멈춤·0.7초 내림). 안내하는 동안 고개도 사진 쪽으로 살짝
GUIDE_T = [float(v) for v in a[a.index("--안내") + 1].split(",")] if "--안내" in a else []
GUIDE_POSE = None; GXN = [-1]
if GUIDE_T and arm is not None:
    PBg = arm.pose.bones; bpy.context.view_layer.update()
    poseA = {b.name: b.matrix_basis.copy() for b in PBg}
    GX = 1 if ("--안내쪽" in a and a[a.index("--안내쪽") + 1] == "오른") else -1   # 사진이 화면 오른쪽이면 오른쪽(+x) 손 (--안내쪽 오른, 사용자 2026-11-25 '왼쪽에 아나운서')
    gs = next(sd for sd in ("L", "R") if f"UpperArm.{sd}" in PBg and (MW @ PBg[f"UpperArm.{sd}"].head).x * GX > 0)
    for b in PBg:
        if b.name.endswith("." + gs) and not b.name.startswith(("UpperLeg", "LowerLeg", "Foot")): b.matrix_basis = mathutils.Matrix.Identity(4)
    bpy.context.view_layer.update()
    GV = [float(v) for v in a[a.index("--안내팔") + 1].split(",")] if "--안내팔" in a else [0.35, -0.45, -0.82, 0.62, -0.72, 0.22, 0.70, -0.60, 0.30]
    aim_bone([f"UpperArm.{gs}"], (GX * GV[0], GV[1], GV[2]), [f"ForeArm.{gs}"])
    aim_bone([f"ForeArm.{gs}"], (GX * GV[3], GV[4], GV[5]), [f"Hand.{gs}"])
    aim_bone([f"Hand.{gs}"], (GX * GV[6], GV[7], GV[8]), [f"Middle1.{gs}"])
    if gs in palm:                                          # 손바닥이 위·앞(카메라 쪽)을 보게
        bpy.context.view_layer.update()
        hpb_ = B(f"Hand.{gs}"); ax_ = (W(B(f"Middle1.{gs}")) - W(hpb_)).normalized()
        n_ = palm_now(gs); tg_ = mathutils.Vector((0, -0.55, 0.85)); tg_ = (tg_ - ax_ * ax_.dot(tg_)).normalized(); n_ = (n_ - ax_ * ax_.dot(n_)).normalized()
        ang_ = math.atan2(ax_.dot(n_.cross(tg_)), n_.dot(tg_))
        R_ = (MWi.to_3x3() @ mathutils.Matrix.Rotation(ang_, 3, ax_) @ MW.to_3x3()).to_4x4()
        hpb_.matrix = mathutils.Matrix.Translation(hpb_.head) @ R_ @ mathutils.Matrix.Translation(-hpb_.head) @ hpb_.matrix; bpy.context.view_layer.update()
    curl(gs, 0.10, thumb=0.02)                              # 손가락은 가지런히 펴고 힘만 살짝 뺌
    poseB = {b.name: b.matrix_basis.copy() for b in PBg}; GXN[0] = GX
    GUIDE_POSE = [(n, poseA[n].decompose(), poseB[n].decompose()) for n in poseA if poseA[n] != poseB[n]]
    for b in PBg: b.matrix_basis = poseA[b.name]
    bpy.context.view_layer.update()
    print("안내: 손", gs, "뼈", len(GUIDE_POSE), "때", GUIDE_T)
def guide_w(t):
    w = 0.0
    for t0 in GUIDE_T:
        u = t - t0
        if 0 <= u < 0.6: v = u / 0.6
        elif 0.6 <= u < 2.8: v = 1.0
        elif 2.8 <= u < 3.5: v = 1 - (u - 2.8) / 0.7
        else: v = 0.0
        w = max(w, v * v * (3 - 2 * v))
    return w
def guide_apply(i):
    if not GUIDE_POSE: return 0.0
    w = guide_w(i / 24.0); PBg = arm.pose.bones
    for n, (la, ra, sa), (lb, rb, sb) in GUIDE_POSE:
        PBg[n].matrix_basis = mathutils.Matrix.LocRotScale(la.lerp(lb, w), ra.slerp(rb, w), sa.lerp(sb, w))
    bpy.context.view_layer.update(); return w
# ── 이(치아, --이): 모델엔 입 안이 어두운 면뿐 → 윗니·아랫니를 곡선(치열궁)을 따라 가지런히 만들어 머리에 붙임 (2026-11-25)
#   윗니는 머리에 고정, 아랫니는 '입 벌림' 모양 키로 아랫입술을 따라 내려감. 크기는 입 너비에 맞춰 늘고 줄음
if "--이" in a and any(o.type == "MESH" and o.name.startswith("Teeth") for o in objs):
    print("이: GLB 에 이미 있음(애니3D/glb_이넣기.py) → 그대로 씀")
elif "--이" in a:
    import bmesh
    body_ = max((o for o in objs if o.type == "MESH"), key=lambda o: len(o.data.vertices))
    mi_ = next(o for o in objs if o.type == "MESH" and o.name.startswith("Mouth_Inside"))
    mi2 = next((o for o in objs if o.type == "MESH" and o.name.startswith("Mouth_Interior")), mi_)
    bw = [mi_.matrix_world @ mathutils.Vector(c) for c in mi_.bound_box]; bw2 = [mi2.matrix_world @ mathutils.Vector(c) for c in mi2.bound_box]
    S = (max(v.x for v in bw) - min(v.x for v in bw)) / 0.0417               # 입(입술 사이 구멍) 너비 4.2cm 기준 비율
    cx = (max(v.x for v in bw) + min(v.x for v in bw)) / 2                   # 입 가운데 (얼굴 가운데보다 살짝 옆)
    yfront = min(v.y for v in bw); zline = min(v.z for v in bw)                # 입술이 만나는 선(앞쪽)
    kbs = body_.data.shape_keys.key_blocks; mwb = body_.matrix_world; R3 = mwb.to_3x3()
    best = mathutils.Vector((0, 0, 0))
    for v0, v1 in zip(kbs["Basis"].data, kbs["MouthOpen"].data):          # 아랫입술 가운데가 입 벌림 때 움직이는 양
        w = mwb @ v0.co
        if abs(w.x - cx) < 0.004 * S and zline - 0.008 * S < w.z < zline:
            d = R3 @ (v1.co - v0.co)
            if d.length > best.length: best = d
    IA = float(a[a.index("--이밝기") + 1]) if "--이밝기" in a else 0.92
    mat = bpy.data.materials.new("이"); mat.use_nodes = True; bs = mat.node_tree.nodes["Principled BSDF"]
    bs.inputs["Base Color"].default_value = (0.86 * IA, 0.84 * IA, 0.78 * IA, 1); bs.inputs["Roughness"].default_value = 0.32
    def row(name, widths, front, c, z_edge, height, up):
        # widths: 가운데부터 한쪽 이 너비들 (좌우 대칭). 이 하나 = 둥근 모서리 상자, 곡선 y = front + c·x²
        bm = bmesh.new(); xs = []; x = 0.0; gap = 0.00012 * S
        for i, w in enumerate(widths):
            for sg in (1, -1): xs.append((sg * (x + w / 2), w, i))   # 입 가운데 cx 기준
            x += w + gap
        for xc, w, i in xs:
            yc = front + c * xc * xc; ang = math.atan(2 * c * xc)      # 입술 안쪽 곡선을 따라 뒤로 휨
            h = height[i]; ze = z_edge + 0.00025 * S * i * (1 if up else -1)        # 이 끝선은 가지런하게, 옆으로 갈수록 아주 조금 올라감
            th = 0.0042 * S * (1 - 0.1 * i)
            r = bmesh.ops.create_cube(bm, size=1.0)["verts"]
            for v in r:
                lx, ly, lz = v.co.x * (w - gap), v.co.y * th, v.co.z * h
                lx *= 1 - 0.18 * (lz / h + 0.5 if up else 0.5 - lz / h)     # 잇몸 쪽으로 살짝 좁게
                px = cx + xc + lx * math.cos(ang) - ly * math.sin(ang); py = yc + ly * math.cos(ang) + lx * math.sin(ang)
                pz = (ze + h / 2 + lz) if up else (ze - h / 2 + lz)
                v.co = mathutils.Vector((px, py + th / 2, pz))
        me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
        ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob)
        inv = mwb.inverted()
        for v in me.vertices: v.co = inv @ v.co
        ob.parent = body_.parent; ob.matrix_parent_inverse = body_.matrix_parent_inverse.copy(); ob.matrix_basis = body_.matrix_basis.copy()
        me.materials.append(mat)
        bv = ob.modifiers.new("둥글게", "BEVEL"); bv.width = 0.0005 * S / max(body_.matrix_world.to_scale()); bv.segments = 3; bv.limit_method = "NONE"
        am = next((m for m in body_.modifiers if m.type == "ARMATURE"), None)
        if am:
            vg = ob.vertex_groups.new(name="Head"); vg.add(list(range(len(me.vertices))), 1.0, "REPLACE")
            m2 = ob.modifiers.new("Armature", "ARMATURE"); m2.object = am.object
        for poly in me.polygons: poly.use_smooth = True
        objs.append(ob); return ob
    C = 31.0 / S                                                              # 입술 안쪽 곡선 y = 앞 + C·x² (모델에서 잰 값)
    up = row("윗니", [0.0056 * S, 0.0046 * S, 0.0046 * S, 0.0038 * S], yfront + 0.0030 * S, C * 1.15,
             zline - 0.0014 * S, [0.0080 * S, 0.0070 * S, 0.0075 * S, 0.0065 * S], True)
    lo = row("아랫니", [0.0040 * S, 0.0042 * S, 0.0045 * S, 0.0040 * S], yfront + 0.0055 * S, C * 1.3,
             zline + 0.0003 * S, [0.0045 * S, 0.0045 * S, 0.0046 * S, 0.0042 * S], False)      # 짧게·뒤로: 길면 턱 피부를 뚫고 나왔음
    lo.shape_key_add(name="Basis"); kk = lo.shape_key_add(name="MouthOpen", from_mix=False)
    dl = mwb.to_3x3().inverted() @ (best * 0.85)
    for v in kk.data: v.co = v.co + dl
    print(f"이: 입 너비 비율 {S:.2f}, 입술선 z {zline:.4f}, 아랫입술 벌림 {best.length * 100:.2f}cm")
# ── 입속 막(--입속 R,G,B): 입 안 그물이 없는 인물(Rocketbox Female_Adult_12 등)은 입을 벌리면 머리 안쪽 뒷면이 보여 새까맸음
#   → 입술 바로 뒤에 짙은 선홍색 둥근 막을 넣고 머리 뼈에 붙임 (사용자 2026-11-26 '입 속이 너무 검은색, 짙은 선홍색이 나을 듯')
if "--입속" in a:
    import bmesh
    col_ = [float(v) / 255 for v in a[a.index("--입속") + 1].split(",")]
    bodyM = max((o for o in objs if o.type == "MESH" and o.data.shape_keys and "MouthOpen" in o.data.shape_keys.key_blocks), key=lambda o: len(o.data.vertices), default=None)
    if bodyM is not None:
        kb_ = bodyM.data.shape_keys.key_blocks; mw_ = bodyM.matrix_world
        mv = [mw_ @ b.co for b, k in zip(kb_["Basis"].data, kb_["MouthOpen"].data) if (k.co - b.co).length > 0.002 * (1 / max(mw_.to_scale()))]
        if mv:
            fy0 = min(v.y for v in mv); lp = [v for v in mv if v.y < fy0 + 0.010]          # 입술 앞쪽만 (턱까지 잡으면 막이 커져 턱 밖으로 나왔음)
            cx_ = sum(v.x for v in lp) / len(lp); cz_ = sum(v.z for v in lp) / len(lp); fy_ = fy0
            wd_ = (max(v.x for v in lp) - min(v.x for v in lp)) * 0.40
            bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=12, radius=1.0)
            for v in bm.verts: v.co = mathutils.Vector((cx_ + v.co.x * wd_, fy_ + 0.024 + v.co.y * 0.014, cz_ + v.co.z * 0.012))
            me_ = bpy.data.meshes.new("입속"); bm.to_mesh(me_); bm.free()
            ob_ = bpy.data.objects.new("입속", me_); bpy.context.scene.collection.objects.link(ob_)
            mt_ = bpy.data.materials.new("입속"); mt_.use_nodes = True; bs_ = mt_.node_tree.nodes["Principled BSDF"]
            bs_.inputs["Base Color"].default_value = (*[c ** 2.2 for c in col_], 1); bs_.inputs["Roughness"].default_value = 0.55
            bs_.inputs["Emission Color"].default_value = (*[c ** 2.2 for c in col_], 1); bs_.inputs["Emission Strength"].default_value = 0.35   # 그늘에서도 색이 보이게 아주 살짝 빛
            me_.materials.append(mt_)
            am_ = next((m for m in bodyM.modifiers if m.type == "ARMATURE"), None)
            inv_ = mw_.inverted()                                   # 이(치아)처럼: 몸 그물과 같은 자리·같은 부모, 머리 뼈 무게 1
            for v in me_.vertices: v.co = inv_ @ v.co
            ob_.parent = bodyM.parent; ob_.matrix_parent_inverse = bodyM.matrix_parent_inverse.copy(); ob_.matrix_basis = bodyM.matrix_basis.copy()
            if am_:
                vg_ = ob_.vertex_groups.new(name="Head"); vg_.add(list(range(len(me_.vertices))), 1.0, "REPLACE")
                m2_ = ob_.modifiers.new("Armature", "ARMATURE"); m2_.object = am_.object
            objs.append(ob_); print("입속 막:", tuple(round(c, 3) for c in (cx_, fy_, cz_)), "폭", round(wd_ * 2, 3))
# 모양 키(입·눈) 모으기
keyed = [o for o in objs if o.type == "MESH" and o.data.shape_keys]
for o in keyed: o.data.shape_keys.animation_data_clear()   # GLB 의 Idle 동작이 모양 키(입·눈)를 매 장면 0 으로 되돌려 립싱크가 안 됐음 (2026-11-25)
def set_shape(name, v, frame=None):
    for o in keyed:
        kb = o.data.shape_keys.key_blocks.get(name)
        if kb is not None:
            if v < kb.slider_min: kb.slider_min = -1.0      # 음수 = 굳힌 미소 풀기(입 오므릴 때)
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

# ── 해(--해 방위°,높이°,세기): 사진 배경판과 빛을 맞출 때 — 방위 0 = 인물 뒤(+y), 90 = 오른쪽(+x) (사용자 2026-11-25 '주인공 조명은 주변과 어울리게') ──
if "--해" in a:
    az, el, en = (float(v) for v in a[a.index("--해") + 1].split(","))
    bpy.ops.object.light_add(type="SUN"); sun = bpy.context.object; sun.data.energy = en; sun.data.angle = math.radians(0.6)
    sun.data.color = (1.0, 0.97, 0.92)
    d = mathutils.Vector((math.sin(math.radians(az)) * math.cos(math.radians(el)), math.cos(math.radians(az)) * math.cos(math.radians(el)), math.sin(math.radians(el))))
    sun.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()      # 해에서 인물 쪽으로 비춤
# ── 카메라: 인물 둘레를 돎 ──
bpy.ops.object.camera_add(); cam = bpy.context.object; sc.camera = cam; cam.data.lens = 40
a0, a1 = (math.radians(float(v)) for v in opt["--각도"].split(","))
R, HC, LOOK = float(opt["--거리"]), float(opt["--높이"]), float(opt["--보기"])
N = int(opt["--장수"])
HANDVIEW = a[a.index('--손보기') + 1] if '--손보기' in a else None   # 검사용: 손 가까이 찍기 (R 또는 L)
HANDSIDE = -1 if '--손안쪽' in a else 1                             # --손안쪽: 손바닥 쪽(몸 안쪽)에서
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
GAMECAM = "--게임카메라" in a or "--트래킹오르빗" in a or "--카페카메라" in a; GAMECAM_ROLL = 0.0 if "--트래킹오르빗" in a else 4.0
GAMECAM_KEYS = [(0.0, -40, 3.4, 0.45, 0.85, 30), (2.2, 30, 2.6, 0.55, 0.95, 34), (3.0, 5, 1.9, 1.35, 1.25, 48), (4.5, -8, 1.8, 1.3, 1.22, 50),
                (5.1, 60, 2.6, 0.6, 0.88, 32), (6.6, 105, 2.8, 0.65, 0.9, 32), (7.3, 150, 3.3, 2.5, 0.95, 28), (9.0, 250, 3.6, 1.7, 0.95, 30),
                (12.0, 360, 3.6, 1.4, 0.95, 32)]
if "--카페카메라" in a:   # 노천카페: 비스듬한 앞에서 천천히 다가가며 살짝 돎 (마시는 순간 얼굴이 잘 보이게)
    GAMECAM_KEYS = [(0.0, 42, 2.6, 1.3, 1.0, 38), (5.0, 26, 1.9, 1.28, 1.08, 44)]
if "--트래킹오르빗" in a:   # 전진 트래킹(정면에서 곧게 다가감) → 멈추지 않고 인물 둘레를 돎 (사용자 2026-11-24)
    # 180° 까지, 전진은 점점 빠르게 → 돌기는 빠르게 시작해 배경이 바뀐 뒤 천천히 멈춤 (사용자 2026-11-24)
    GAMECAM_KEYS = [(0.0, 0, 7.0, 1.55, 1.25, 35), (2.6, 0, 2.7, 1.45, 1.3, 40, "점점빠르게"), (6.0, 180, 2.7, 1.5, 1.3, 40, "점점느리게"), (9.0, 180, 2.7, 1.5, 1.3, 40)]
def place(i, who=None):
    s = i / max(1, N - 1); s = s * s * (3 - 2 * s); th = a0 + (a1 - a0) * s
    r_ = R + (R1 - R) * s; lk = LOOK + (LOOK1 - LOOK) * s; hc = HC + (HC1 - HC) * s
    c0 = who if who is not None else mathutils.Vector((0, 0, 0))
    cam.location = (c0.x + r_ * math.sin(th), c0.y - r_ * math.cos(th), hc)
    if "--고정카메라" in a:   # 카메라가 인물을 따라가지 않고 한 자리에 (x,y,z,보는x,보는y,보는z[,렌즈mm]) — 인물이 카메라 쪽으로 걸어오는 장면용
        v7 = [float(q) for q in a[a.index("--고정카메라") + 1].split(",")]
        cam.location = mathutils.Vector(v7[:3]); d = mathutils.Vector(v7[3:6]) - cam.location
        cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
        if len(v7) > 6: cam.data.lens = v7[6]
        return
    if "--카메라" in a:      # 검사용: 카메라 자리·보는 곳을 직접 (x,y,z,보는x,보는y,보는z — 인물이 걸어온 만큼 같이 옮김)
        v6 = [float(q) for q in a[a.index("--카메라") + 1].split(",")]; wv = WHO[0]
        cam.location = mathutils.Vector(v6[:3]) + wv; d = mathutils.Vector(v6[3:]) + wv - cam.location
        cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler(); return
    if GAMECAM and HP is None:                     # 게임 카메라: 동작마다 다른 구도로 부드럽게 날아다님
        t = i / 24.0; ks = GAMECAM_KEYS
        k = max(0, min(len(ks) - 2, next((n for n in range(len(ks) - 1) if ks[n + 1][0] > t), len(ks) - 2)))
        (ta, *A), (tb, *Bk) = ks[k], ks[k + 1]
        u = min(1.0, max(0.0, (t - ta) / max(tb - ta, 1e-6)))
        ez = Bk[5] if len(Bk) > 5 else "부드럽게"                              # 이 구간 빠르기: 점점빠르게 / 점점느리게 / 부드럽게
        # 점점빠르게 = u³, 점점느리게 = 1-(1-u)², 부드럽게 = smoothstep — 전진(4.3m/2.6초)이 끝날 때 빠르기와 돌기(반원 8.5m/3.4초)가 시작할 때 빠르기가 같아 이음매에서 덜컥이지 않음
        u = u ** 3 if ez == "점점빠르게" else 1 - (1 - u) ** 2 if ez == "점점느리게" else u * u * (3 - 2 * u)
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
        side_ = HANDSIDE * sx
        cam.location = HP + mathutils.Vector((side_ * 0.22, -0.38, 0.05)); cam.data.lens = 50
        d = HP - cam.location; cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler(); return
    d = mathutils.Vector((0, 0, LOOK)) - cam.location; cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()

# ── 걷기(--걷기): 인물이 카메라 쪽(-y)으로 두어 걸음 걸어와 멈춤, 카메라는 뒤로 빠지며 돎 (사용자 결정 2026-11-23) ──
#   발 자리를 시간마다 정하고(오른발 → 왼발 → 오른발을 모음), 골반은 두 발 가운데, 다리는 두 마디 IK(무릎은 앞으로), 발은 바닥과 평평하게.
#   팔은 걷는 동안 반대쪽 다리와 함께 앞뒤로 조금 흔듦
WALK = "--걷기" in a
SIP = "--마시기" in a        # 커피 자세에서 컵을 입으로 가져가 한 모금 마시고 내려놓음 (사용자 2026-11-24)
DANCE = "--춤" in a or "--조지아" in a          # 가벼운 춤(스텝 터치): 옆으로 한 발 내딛고 모으기를 박자에 맞춰, 무릎 반동·골반·팔 흔들기 (사용자 2026-11-24 "약간의 댄스")
BPM = float(a[a.index("--박자") + 1]) if "--박자" in a else 112
ROUTINE = (a[a.index("--춤순서") + 1] if "--춤순서" in a else "스텝,손뼉,엉덩이,돌기").split(",")   # 4박마다 바뀌는 동작 순서
STEP = float(a[a.index("--보폭") + 1]) if "--보폭" in a else 0.28     # 엉덩이~발목 0.55m·몸에 붙는 치마·굽 구두 → 작은 걸음 (0.40 이면 골반이 내려가 무릎 굽은 채 걸음)
if (WALK or DANCE or SIP) and arm is not None:
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
    LIFT = 0.035; NSTEP = int(a[a.index('--걸음수') + 1]) if '--걸음수' in a else 2; TEND = T0 + NSTEP * D1 + D3
    # 걸음표: (시작, 길이, 발, 출발 y, 도착 y) — 오른발부터 번갈아, 첫 걸음은 반걸음, 마지막에 뒤 발을 모음 (--걸음수 N, 사용자 2026-11-25 카메라 쪽으로 걸어오기)
    SCHED = []
    for k_ in range(NSTEP):
        SCHED.append((T0 + k_ * D1, D1, "R" if k_ % 2 == 0 else "L", -max(0, k_ - 1) * STEP if k_ > 0 else 0.0, -(k_ + 1) * STEP))
    SCHED.append((T0 + NSTEP * D1, D3, "L" if NSTEP % 2 == 0 else "R", -(NSTEP - 1) * STEP, -NSTEP * STEP))
    def foot_u(sd, t):                                       # 이 발이 지금 몇 번째 걸음의 어디쯤(0~1)인지, 걸음 길이
        segs = [(s0, d) for s0, d, f_, _, _ in SCHED if f_ == sd]
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
        y = 0.0
        for s0, d, f_, y0, y1 in SCHED:
            if f_ != sd: continue
            if t >= s0 + d: y = y1
            elif t > s0: y = y0 + (y1 - y0) * sm((t - s0) / d)
        return y
    def foot_lift(sd, t):
        return sum((LIFT if k_ < len(SCHED) - 1 else LIFT * 0.6) * math.sin(math.pi * min(1, max(0, (t - s0) / d))) for k_, (s0, d, f_, _, _) in enumerate(SCHED) if f_ == sd)
    def set_world_aim(name, child_head_world, target_world):
        if name.startswith("UpperArm."): bpy.context.view_layer.update(); shrug(name[-1], target_world - (MW @ PB[name].head))
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
        py_ = 0.5 * (-NSTEP * STEP * smoother((t - T0 + 0.1) / (TEND - T0 + 0.05))) + 0.5 * (fy['L'] + fy['R']) / 2   # 골반: 고르게 앞으로 + 두 발 가운데를 반씩 (멈칫도, 무릎 굽힘도 없게)
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
    GEORGIA = "--조지아" in a      # 조지아 여성 전통무용 느낌(사용자 2026-11-26 샘플): 꼿꼿한 몸·잔걸음으로 원을 그리며 미끄러지듯, 한 팔 위로 둥글게·한 팔 옆으로, 손목을 굴림
    GR = float(a[a.index("--조지아") + 1]) if "--조지아" in a and a.index("--조지아") + 1 < len(a) and a[a.index("--조지아") + 1][0].isdigit() else 0.45   # 원 반지름(m)
    def georgia(i):
        t = i / 24.0; t0 = 0.3
        for b in PB: b.matrix_basis = base[b.name]
        for r in roots: r.matrix_world = ROOT0[r.name]
        bpy.context.view_layer.update()
        on = sm2_(min(1.0, max(0.0, (t - t0) / 1.0)))
        tt = max(0.0, t - t0); per = 9.0                                    # 한 바퀴 9초
        th = 2 * math.pi * sm2_(min(1.0, tt / 1.5)) * 0 + 2 * math.pi * max(0.0, tt - 0.75) / per * on
        # 몸: 꼿꼿, 가슴 살짝 펴고 고개 들기, 아주 작은 오르내림(잔걸음)
        step = 0.006 * (0.5 - 0.5 * math.cos(2 * math.pi * 3.0 * tt)) * on
        hp = PB["Hips"]; hp.matrix = mathutils.Matrix.Translation(M3i @ mathutils.Vector((0, 0, -step))) @ hp.matrix; bpy.context.view_layer.update()
        if "Chest" in PB: rot_world("Chest", (1, 0, 0), -0.04 * on)
        if "Head" in PB: rot_world("Head", (1, 0, 0), -0.03 * on); rot_world("Head", (0, 1, 0), 0.06 * math.sin(2 * math.pi * tt / 6) * on)
        # 발: 번갈아 아주 조금 듦 (치마 아래 잔걸음, 초당 3번)
        for k, sd in enumerate(("L", "R")):
            g = leg[sd]; H = MW @ PB[f"UpperLeg.{sd}"].head
            lift = 0.014 * max(0.0, math.sin(2 * math.pi * 3.0 * tt + k * math.pi)) * on
            F = g["F0"] + mathutils.Vector((0, 0, lift))
            d = F - H; dl = min(d.length, g["L1"] + g["L2"] - 1e-4)
            ca = (g["L1"] ** 2 + dl ** 2 - g["L2"] ** 2) / (2 * g["L1"] * dl); ang = math.acos(max(-1, min(1, ca)))
            dn = d.normalized(); fwd = mathutils.Vector((0, -1, 0)); sidev = dn.cross(fwd).normalized(); perp = sidev.cross(dn).normalized()
            if perp.dot(fwd) < 0: perp = -perp
            knee = H + (dn * math.cos(ang) + perp * math.sin(ang)) * g["L1"]
            set_world_aim(f"UpperLeg.{sd}", lambda sd=sd: MW @ PB[f"LowerLeg.{sd}"].head, knee)
            set_world_aim(f"LowerLeg.{sd}", lambda sd=sd: MW @ PB[f"Foot.{sd}"].head, F)
            fb = PB[f"Foot.{sd}"]; fb.matrix = mathutils.Matrix.Translation(fb.matrix.translation) @ FOOT0[sd]; bpy.context.view_layer.update()
        # 팔: 4.5초마다 위로 든 팔이 바뀜 (1.2초에 걸쳐 부드럽게)
        V = mathutils.Vector
        cyc = tt / 4.5; k_ = int(cyc); fr = cyc - k_; bl = sm2_(min(1.0, max(0.0, (fr - 0.73) / 0.27)))
        def dirs(high, sgn):
            if high: return V((sgn * 0.62, -0.22, 0.75)), V((-sgn * 0.88, -0.18, 0.40))   # 팔꿈치를 굽혀 머리 위로 둥글게 감쌈 (곧게 뻗으면 체조 같았음)
            return V((sgn * 0.95, -0.22, 0.05)), V((sgn * 0.85, -0.42, 0.30))             # 옆으로, 앞으로 살짝 휘게
        for sd in ("L", "R"):
            ub, fa, hb_ = f"UpperArm.{sd}", f"ForeArm.{sd}", f"Hand.{sd}"
            if ub not in PB or hb_ not in PB: continue
            sgn = 1 if (MW @ PB[ub].head).x > 0 else -1
            hi_now = ((k_ % 2 == 0) == (sd == "R")); u1, f1 = dirs(hi_now, sgn); u2, f2 = dirs(not hi_now, sgn)
            u0, f0 = V((sgn * CH_U, -0.03, -1.0)), V((sgn * CH_F, -0.10, -1.0))
            ud = (u1 * (1 - bl) + u2 * bl) * on + u0 * (1 - on); fd = (f1 * (1 - bl) + f2 * bl) * on + f0 * (1 - on)
            set_world_aim(ub, lambda fa=fa: MW @ PB[fa].head, (MW @ PB[ub].head) + ud)
            set_world_aim(fa, lambda hb_=hb_: MW @ PB[hb_].head, (MW @ PB[fa].head) + fd)
            if hb_ in PB:                                                    # 손목을 살랑 굴림
                hpb = PB[hb_]; ax = ((MW @ hpb.head) - (MW @ PB[fa].head)).normalized()
                R_ = (M3i @ mathutils.Matrix.Rotation(0.35 * math.sin(2 * math.pi * tt / 1.5 + (0 if sd == "L" else 1.5)) * on, 3, ax) @ M3).to_4x4()
                hpb.matrix = mathutils.Matrix.Translation(hpb.head) @ R_ @ mathutils.Matrix.Translation(-hpb.head) @ hpb.matrix; bpy.context.view_layer.update()
        # 원을 그리며 미끄러지듯: 반지름 GR, 몸은 가는 쪽을 봄
        if on > 0:
            pos = mathutils.Vector((GR * math.sin(th), -GR * math.cos(th) + GR, 0)) * 1.0
            Rz = mathutils.Matrix.Rotation(th, 4, "Z")
            for r in roots: r.matrix_world = mathutils.Matrix.Translation(pos) @ Rz @ ROOT0[r.name]
            bpy.context.view_layer.update()
        return mathutils.Vector((0, 0, 0))
    def dance(i):
        if GEORGIA: return georgia(i)
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
                return V((sgn * 0.30, -0.65, -0.70)), V((-sgn * (0.15 + 0.56 * c), -0.80 + 0.14 * c, 0.50 - 0.05 * c))   # 손이 가운데에서 딱 만나고 넘어가지 않게
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
    def sip(i):
        """컵 든 팔: 가슴 앞(쉼) → 입가로 들어 올림 → 한 모금(고개 살짝 뒤로) → 내림. 박자: 0~1초 쉼, 1~2.2 올림, 2.2~3.4 마심, 3.4~4.6 내림"""
        t = i / 24.0
        for b in PB: b.matrix_basis = base[b.name]
        bpy.context.view_layer.update()
        sm3 = lambda u: 0.0 if u <= 0 else 1.0 if u >= 1 else u * u * (3 - 2 * u)
        k = sm3((t - 1.0) / 1.2) * (1 - sm3((t - 3.4) / 1.2))                # 0 쉼 ↔ 1 입가
        V = mathutils.Vector
        lerp = lambda p_, q_: (p_ * (1 - k) + q_ * k)
        for sd in ((CUP_SIDE,) if CUP_GRIP == '한손' else ("L", "R")):   # 한손: 컵 든 손만 / 두손: 두 손이 함께 입으로
            ub, fa, hb_ = f"UpperArm.{sd}", f"ForeArm.{sd}", f"Hand.{sd}"
            sgn = 1 if (MW @ PB[ub].head).x > 0 else -1
            ud = lerp(V((sgn * 0.26, -0.32, -0.91)), V((sgn * 0.20, -0.80, -0.20)))
            fd = lerp(V((-sgn * 0.55, -0.72, 0.42)), V((-sgn * 0.55, -0.20, 0.82)))
            set_world_aim(ub, lambda fa=fa: MW @ PB[fa].head, (MW @ PB[ub].head) + ud)
            set_world_aim(fa, lambda hb_=hb_: MW @ PB[hb_].head, (MW @ PB[fa].head) + fd)
        drink = sm3((t - 2.1) / 0.4) * (1 - sm3((t - 3.2) / 0.4))
        if "Head" in PB: rot_world("Head", (1, 0, 0), -0.18 * drink)            # 마실 때 고개 살짝 뒤로
        if "Head" in PB: rot_world("Head", (0, 0, 1), 0.08 * (1 - k) * math.sin(t * 0.9))   # 쉴 때 주위를 살짝 둘러봄
        return mathutils.Vector((0, 0, 0))
    if DANCE: walk = dance
    if SIP: walk = sip
else:
    walk = lambda i: mathutils.Vector((0, 0, 0))

# ── 입·눈 ──
lip = json.load(open(opt["--입"])) if opt["--입"] else {"frames": []}
# 눈 깜빡임: 영상 끝까지 2.2~5초 간격으로 불규칙하게 (예전엔 13초까지 5번뿐), 가끔 두 번 연달아 — 사용자 2026-11-25 '말할 때 눈도 깜빡이고'
import random as _rnd
_rg = _rnd.Random(7); blinks = []; _tb = 1.1
while _tb < N / 24.0 + 1:
    blinks.append(_tb)
    if _rg.random() < 0.15: blinks.append(_tb + 0.32)
    _tb += _rg.uniform(2.2, 5.0)
def blink_v(t):                                   # 빨리 감고(0.06초) 조금 천천히 뜸(0.11초)
    v = 0.0
    for c in blinks:
        d = t - c
        if -0.06 < d <= 0: v = max(v, 1 + d / 0.06)
        elif 0 < d < 0.11: v = max(v, 1 - d / 0.11)
    return v
# 말할 때 고개: 천천히 좌우·기울임 + 말 세기(입 벌림)에 따라 살짝 끄덕임 (--고개고정 이면 끔) — 사용자 2026-11-25 '얼굴 방향도 조금씩'
_lo = [f[0] for f in lip["frames"]]
def _energy(i, w=10):
    seg = _lo[max(0, i - w): i + w + 1]; return sum(seg) / len(seg) if seg else 0.0
_E = (sum(_lo) / len(_lo)) if _lo else 0.0
HEAD_MOVE = bool(_lo) and "--고개고정" not in a and arm is not None and "Head" in arm.pose.bones
_HB0 = {}; GWN = [0.0]
def head_move(i):
    t = i / 24.0; PBh = arm.pose.bones
    static = not (WALK or DANCE or SIP)
    for nm in ("Neck", "Head"):
        if nm not in PBh: continue
        if static:
            if nm not in _HB0: _HB0[nm] = PBh[nm].matrix_basis.copy()
            PBh[nm].matrix_basis = _HB0[nm].copy()
    bpy.context.view_layer.update()
    pitch = 0.9 * math.sin(1.3 * t + 0.3) + 0.5 * math.sin(2.9 * t + 1.0) + 9.0 * (_energy(i) - _E) - 0.6 * math.sin(math.pi * min(1, _energy(i, 3) * 1.2))
    yaw = 2.0 * math.sin(0.55 * t + 0.5) + 0.9 * math.sin(1.37 * t + 2.0) + 13.0 * GWN[0] * GXN[0]      # 안내할 때 사진 쪽으로
    roll = 1.4 * math.sin(0.43 * t + 2.0) + 0.5 * math.sin(1.1 * t)
    MWa = arm.matrix_world; M3a = MWa.to_3x3(); M3ai = M3a.inverted()
    for nm, sh in (("Neck", 0.4), ("Head", 0.6)):
        if nm not in PBh: continue
        pb = PBh[nm]
        Rw = (mathutils.Matrix.Rotation(math.radians(yaw * sh), 3, "Z") @ mathutils.Matrix.Rotation(math.radians(-pitch * sh), 3, "X")
              @ mathutils.Matrix.Rotation(math.radians(roll * sh), 3, "Y"))
        R_ = (M3ai @ Rw @ M3a).to_4x4()
        pb.matrix = mathutils.Matrix.Translation(pb.head) @ R_ @ mathutils.Matrix.Translation(-pb.head) @ pb.matrix
        bpy.context.view_layer.update()
EXPR = [(kv.split('=')[0], float(kv.split('=')[1])) for kv in a[a.index('--표정') + 1].split(',')] if '--표정' in a else []
VISEME = '--입방식' in a and a[a.index('--입방식') + 1] == '15'      # --입방식 15 : Rocketbox 15가지 입 모양(AA_VI_*)
MOUTH_SCALE = float(a[a.index('--입세기') + 1]) if '--입세기' in a else 1.0     # Rocketbox 는 '아' 입이 커서 O 자로 벌어졌음 (사용자 2026-11-26 '입 벌림 작게')
def face(i):
    t = i / 24.0; lf = lip["frames"][i] if i < len(lip["frames"]) else [0, 0, 0]
    MS = MOUTH_SCALE
    if VISEME and len(lf) >= 15:      # Rocketbox 15가지 입 모양: 모음 aa·ih·ou·ee·oh(배운 표) + 자음 pp·dd·nn·rr·ss·ch·kk (사용자 2026-11-26 '15가지 입 모양으로')
        aa, ih, ou, ee, oh, pp, dd, nn, rr, ss, ch, kk = lf[3:15]
        set_shape("MouthWide", ih * MS)
        set_shape("AA_VI_11_E", ee * MS)
        # ㅗ·ㅜ 는 입을 오므림(사용자 2026-11-26 'ㅗ(아래로 입을 모음), ㅜ(위로 입을 모음)는 입을 오므려야'): 굳힌 미소가 입을 옆으로 당겨
        #   MouthRound·Pucker 가 거의 안 보였음 → 오므릴 때 미소를 풀고(음수), ㅗ = 깔때기+O(조금 벌림), ㅜ = 입술 내밀어 작게 모음
        ro, ru = min(1.0, oh * 1.3), min(1.0, ou * 1.3); rr_ = max(ro, ru)
        set_shape("HB_07_MouthSmile", -0.45 * rr_); set_shape("AU_06_CheekRaiser", -0.3 * rr_)
        set_shape("AA_VI_13_O", 0.4 * ro); set_shape("AK_32_MouthFunnel", 0.5 * ro)
        set_shape("AU_18_LipPuckerer", 0.75 * ru); set_shape("AU_22_LipFunneler", 0.3 * ro + 0.5 * ru)
        set_shape("MouthOpen", aa * MS * (1 - 0.5 * rr_)); set_shape("MouthRound", 0.0)
        set_shape("AA_VI_01_PP", pp * 0.9); set_shape("AA_VI_04_DD", dd * 0.6 * MS); set_shape("AA_VI_08_nn", nn * 0.6 * MS)
        set_shape("AA_VI_09_RR", rr * 0.6 * MS); set_shape("AA_VI_07_SS", ss * 0.7 * MS); set_shape("AA_VI_06_CH", ch * 0.7 * MS); set_shape("AA_VI_05_KK", kk * 0.5 * MS)
    else:
        set_shape("MouthOpen", lf[0] * MS); set_shape("MouthWide", lf[1] * MS); set_shape("MouthRound", lf[2] * MS)   # --입세기 0.5: 입 벌림 줄이기
    set_shape("Blink", blink_v(t))
    for nm_, v_ in EXPR: set_shape(nm_, v_)               # --표정 mouthSmileLeft=0.6,… : 늘 띄울 얼굴 표정(모양 키 이름=값)
    GWN[0] = guide_apply(i)
    if HEAD_MOVE: head_move(i)

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
if "--애니저장" in a:   # 찍지 않고, 장면마다 뼈 자세·인물 자리·모양 키를 기록해 움직이는 GLB 로 내보냄 (사용자 2026-11-26 조지아 춤 'GLB로 저장')
    dst_ = os.path.abspath(a[a.index("--애니저장") + 1]); sc.render.fps = 24; sc.frame_start = 0; sc.frame_end = N - 1
    keep_ = [o for o in objs if o.type in ("ARMATURE", "MESH") and o.name != "Icosphere"]
    for i in range(N):
        sc.frame_set(i); set_xf(i); who = walk(i); WHO[0] = who; face(i); bpy.context.view_layer.update()
        if arm is not None:
            for pb in arm.pose.bones:
                pb.keyframe_insert("location", frame=i); pb.keyframe_insert("rotation_quaternion", frame=i); pb.keyframe_insert("scale", frame=i)
        for r in roots:
            if r.type == "ARMATURE" or r in keep_:
                r.keyframe_insert("location", frame=i); r.keyframe_insert("rotation_euler", frame=i); r.keyframe_insert("scale", frame=i)
        for o in keyed: 
            for k in o.data.shape_keys.key_blocks[1:]:
                if abs(k.value) > 1e-4 or i == 0: k.keyframe_insert("value", frame=i)
    for pb in (arm.pose.bones if arm else []): pb.rotation_mode = "QUATERNION"
    bpy.ops.object.select_all(action="DESELECT")
    for o in keep_: o.select_set(True)
    if arm: arm.select_set(True)
    if bpy.context.object and bpy.context.object.mode != "OBJECT": bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.export_scene.gltf(filepath=dst_, export_format="GLB", use_selection=True, export_animations=True, export_frame_range=True,
                              export_force_sampling=True, export_morph=True, export_skins=True, export_image_format="AUTO", export_animation_mode="SCENE")
    print("움직이는 GLB:", dst_, os.path.getsize(dst_) // 1024, "KB,", N, "장면"); sys.exit(0)
for i in frames:
    set_xf(i); who = walk(i); WHO[0] = who; place(i, who * 0.6); face(i)     # 카메라는 인물을 반쯤 따라감 (나머지는 인물이 다가오는 느낌)
    sc.render.filepath = os.path.join(os.path.abspath(folder), f"f{i:04d}.png"); bpy.ops.render.render(write_still=True)
print("찍음:", len(list(frames)), "장 →", folder)
