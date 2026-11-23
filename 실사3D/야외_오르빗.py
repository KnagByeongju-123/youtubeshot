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
# ── 자세: 기본 = 차렷(팔을 몸 옆에 자연스럽게 내림, 사용자 결정 2026-11-23), --자세 모음 = 손을 허리 앞에 모음 — 뼈 방향을 목표 방향으로 돌림 ──
POSE = a[a.index('--자세') + 1] if '--자세' in a else '마이크'     # 마이크(보도, 기본) / 차렷 / 모음
MIC_SIDE = a[a.index('--마이크손') + 1] if '--마이크손' in a else 'R'
MIC_F = (0.30, 0.45, 0.85); MIC_CURL = 1.25; FIST = float(a[a.index('--주먹') + 1]) if '--주먹' in a else 0.55   # 주먹 = 마디마다 굽힘(라디안)
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
        if n.z > 0: n = -n
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
                n = palm_now(side); hd = MW @ pb.head; cur = ((MW @ pb.tail) - hd).normalized()
                nn = n - cur * cur.dot(n)
                if nn.length < 1e-6: continue
                tgt = cur * math.cos(th) + nn.normalized() * math.sin(th)
                q = cur.rotation_difference(tgt); R = (MWi.to_3x3() @ q.to_matrix() @ MW.to_3x3()).to_4x4()
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
        elif POSE == '마이크' and side == MIC_SIDE:
            aim_bone(ub, (sgn * 0.10, -0.30, -0.95), fb)       # 위팔: 아래로, 팔꿈치는 몸 옆 살짝 앞
            aim_bone(fb, (-sgn * MIC_F[0], -MIC_F[1], MIC_F[2]), hb)   # 아래팔: 가슴 앞으로 들어 올림
            aim_bone(hb, (-sgn * 0.30, -0.55, 0.78), [f"Middle1.{side}"])   # 손: 손가락이 앞·위를 향하게 (마이크를 세워 쥠)
            curl(side, MIC_CURL, thumb=0.45); mic_hand = side
        else:
            aim_bone(ub, (sgn * CH_U, -0.03, -1.0), fb)        # 위팔: 곧게 아래로, 엉덩이에 닿지 않게 살짝 바깥
            aim_bone(fb, (sgn * CH_F, -0.10, -1.0), hb)        # 아래팔: 아래로, 팔꿈치를 아주 살짝 굽혀 자연스럽게
            curl(side, FIST, thumb=FIST * 0.4)                 # 살짝 주먹 (손가락을 편 채 늘어뜨리면 어색함)
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
def place(i):
    s = i / max(1, N - 1); s = s * s * (3 - 2 * s); th = a0 + (a1 - a0) * s
    cam.location = (R * math.sin(th), -R * math.cos(th), HC)
    d = mathutils.Vector((0, 0, LOOK)) - cam.location; cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()

# ── 입·눈 ──
lip = json.load(open(opt["--입"])) if opt["--입"] else {"frames": []}
blinks = [1.3, 4.2, 7.0, 9.8, 12.6]
def face(i):
    t = i / 24.0; lf = lip["frames"][i] if i < len(lip["frames"]) else [0, 0, 0]
    set_shape("MouthOpen", lf[0]); set_shape("MouthWide", lf[1]); set_shape("MouthRound", lf[2])
    set_shape("Blink", max([0.0] + [max(0.0, 1 - abs(t - c) / 0.07) for c in blinks]))

os.makedirs(folder, exist_ok=True)
frames = [int(opt["--미리보기"])] if opt["--미리보기"] else range(int(opt["--시작장"]), N if int(opt["--끝장"]) < 0 else int(opt["--끝장"]))
for i in frames:
    place(i); face(i)
    sc.render.filepath = os.path.join(os.path.abspath(folder), f"f{i:04d}.png"); bpy.ops.render.render(write_still=True)
print("찍음:", len(list(frames)), "장 →", folder)
