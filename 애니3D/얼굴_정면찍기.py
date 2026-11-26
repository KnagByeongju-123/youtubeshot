"""GLB 인물의 얼굴을 정면에서 찍기 — ① 고른 빛의 얼굴 사진 ② 화면 점마다 몸 그림 좌표(UV)를 색으로 담은 EXR
   (AI 로 그린 실사 얼굴 사진을 그 자리 그대로 몸 그림에 옮겨 붙이는 '얼굴 사진 입히기'용, 사용자 2026-11-26)
   사용: .bpy_venv/bin/python -I 애니3D/얼굴_정면찍기.py <인물.glb> <저장폴더> [--크기 1024] [--렌즈 135]"""
import os, sys, math
import bpy, mathutils

a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
glb, out = a[0], a[1]; os.makedirs(out, exist_ok=True)
S = int(a[a.index("--크기") + 1]) if "--크기" in a else 1024
LENS = float(a[a.index("--렌즈") + 1]) if "--렌즈" in a else 135
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.abspath(glb))
sc = bpy.context.scene
body = next((o for o in sc.objects if o.type == "MESH" and o.name.lower().endswith(".body")), None) or max((o for o in sc.objects if o.type == "MESH"), key=lambda o: len(o.data.vertices))   # MPFB 는 정장이 몸보다 점이 많음
arm = next(o for o in sc.objects if o.type == "ARMATURE")
for o in sc.objects:
    if o.type == "MESH" and o.data.shape_keys and o.data.shape_keys.animation_data: o.data.shape_keys.animation_data_clear()
    if o.animation_data: o.animation_data_clear()
    if o.type == "MESH" and o.data.shape_keys:                # 표정 키는 모두 0 (눈 뜨고 입 다문 얼굴)
        for k in o.data.shape_keys.key_blocks[1:]: k.value = 0.0
for o in sc.objects:                                         # 처음 자세(묶을 때 자세)로
    if o.type == "ARMATURE":
        for pb in o.pose.bones: pb.matrix_basis = mathutils.Matrix.Identity(4)
bpy.context.view_layer.update()
hb = arm.pose.bones["Head"]; hp = arm.matrix_world @ hb.head; ht = arm.matrix_world @ hb.tail
# 얼굴 가운데: 머리뼈 머리~꼬리 사이 위쪽, 얼굴 앞 = 몸 점들 중 머리 높이에서 가장 앞(-y)
dg = bpy.context.evaluated_depsgraph_get(); em_ = body.evaluated_get(dg).to_mesh()
vs = [body.matrix_world @ v.co for v in em_.vertices]          # 뼈대로 움직인 실제 자리
zt = max(v.z for v in vs)                                      # 머리 꼭대기(몸 그물 기준 — 뼈 자리와 몸 그물 자리가 어긋난 GLB 도 있음)
face = [v for v in vs if zt - 0.26 < v.z < zt - 0.03 and abs(v.x) < 0.09]
cx = sum(v.x for v in face) / len(face); fy = min(v.y for v in face); cz = zt - 0.13
H = 0.30                                                     # 화면 높이 0.30m (턱 아래~이마 위)
cam_d = 1.6
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam
cam.data.lens = LENS; cam.data.sensor_fit = "VERTICAL"; cam.data.sensor_height = LENS * H / cam_d
cam.location = (cx, fy - cam_d, cz); cam.rotation_euler = (math.radians(90), 0, 0)
sc.render.resolution_x = sc.render.resolution_y = S; sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"
w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True; w.node_tree.nodes["Background"].inputs[1].default_value = 0.55
w.node_tree.nodes["Background"].inputs[0].default_value = (0.85, 0.85, 0.85, 1)
L = bpy.data.objects.new("key", bpy.data.lights.new("key", "AREA")); sc.collection.objects.link(L)
L.data.energy = 18; L.data.size = 1.5; L.location = (cx, fy - 1.2, cz + 0.4); L.rotation_euler = (math.radians(70), 0, 0)
sc.cycles.samples = 64; sc.view_settings.view_transform = "Standard"
sc.render.filepath = os.path.join(out, "얼굴.png"); bpy.ops.render.render(write_still=True)
# ② 좌표(UV) 그림: 몸 = (u, v, 1), 다른 것(머리카락·옷·눈) = 검정 → 32비트 EXR
uvmat = bpy.data.materials.new("uv"); uvmat.use_nodes = True; nt = uvmat.node_tree; nt.nodes.clear()
tc = nt.nodes.new("ShaderNodeTexCoord"); sep = nt.nodes.new("ShaderNodeSeparateXYZ"); comb = nt.nodes.new("ShaderNodeCombineXYZ")
em = nt.nodes.new("ShaderNodeEmission"); outn = nt.nodes.new("ShaderNodeOutputMaterial")
nt.links.new(tc.outputs["UV"], sep.inputs[0]); nt.links.new(sep.outputs[0], comb.inputs[0]); nt.links.new(sep.outputs[1], comb.inputs[1]); comb.inputs[2].default_value = 1.0
nt.links.new(comb.outputs[0], em.inputs[0]); nt.links.new(em.outputs[0], outn.inputs[0])
blk = bpy.data.materials.new("blk"); blk.use_nodes = True; bn = blk.node_tree; bn.nodes.clear()
e2 = bn.nodes.new("ShaderNodeEmission"); e2.inputs[0].default_value = (0, 0, 0, 1); o2 = bn.nodes.new("ShaderNodeOutputMaterial"); bn.links.new(e2.outputs[0], o2.inputs[0])
skin_slots = []
for o in sc.objects:
    if o.type != "MESH": continue
    for i, s in enumerate(o.material_slots):
        is_skin = (o == body and s.material and ("skin" in s.material.name.lower() or "body" in s.material.name.lower() or i == 0))
        if is_skin: skin_slots.append(s.material.name)
        s.material = uvmat if is_skin else blk
print("피부 재질:", skin_slots)
w.node_tree.nodes["Background"].inputs[1].default_value = 0.0; L.data.energy = 0
sc.cycles.samples = 1; sc.cycles.pixel_filter_type = "BOX"; sc.cycles.filter_width = 0.01; sc.view_settings.view_transform = "Standard"
sc.render.image_settings.file_format = "OPEN_EXR"; sc.render.image_settings.color_depth = "32"
sc.render.filepath = os.path.join(out, "좌표.exr"); bpy.ops.render.render(write_still=True)
print("저장:", out)
