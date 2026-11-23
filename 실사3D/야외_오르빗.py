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
b_cam = nt.nodes.new("ShaderNodeBackground"); b_lit = nt.nodes.new("ShaderNodeBackground"); b_lit.inputs["Strength"].default_value = 1.0
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
# ── 자세: 팔을 내려 손을 허리 앞에 모음 (방송 리포터처럼) — 뼈 방향을 목표 방향으로 돌림 ──
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
    for side, sx in (("L", None), ("R", None)):
        ub = [f"UpperArm.{side}", f"{'Left' if side == 'L' else 'Right'}UpperArm"]
        fb = [f"ForeArm.{side}", f"{'Left' if side == 'L' else 'Right'}ForeArm"]
        hb = [f"Hand.{side}", f"{'Left' if side == 'L' else 'Right'}Hand"]
        pb = next((arm.pose.bones[n] for n in ub if n in arm.pose.bones), None)
        if pb is None: continue
        sgn = 1 if (MW @ pb.head).x > 0 else -1
        aim_bone(ub, (sgn * 0.14, -0.22, -0.96), fb)       # 위팔: 아래로, 몸에 붙여 살짝 앞
        aim_bone(fb, (-sgn * 0.62, -0.72, -0.30), hb)      # 아래팔: 앞·안쪽으로 → 손이 허리 앞에서 모임
    bpy.ops.object.mode_set(mode="OBJECT")
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
area((-1.6, -2.0, 2.4), 160, 1.5, (1.0, 0.95, 0.9))
area((1.8, -1.6, 1.8), 60, 1.5, (0.9, 0.93, 1.0))
area((0.3, 1.8, 2.4), 120, 1.0, (0.8, 0.85, 1.0))       # 뒤 윤곽광 (도시 빛과 어울리게 살짝 푸름)

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
