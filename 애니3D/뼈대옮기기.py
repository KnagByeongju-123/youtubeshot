"""뼈대 없는 GLB 사람에 다른 GLB 의 뼈대를 옮겨 붙임 — 이어서 glb_다시리깅.py 로 관절 자리·무게를 새 모양에 맞춤 (사용자 2026-11-28 '여자아나운서1 기준, 복장도 똑같으니 그대로 리깅')
   - 기준 GLB 의 뼈대를 가져오고(손가락 뼈는 지움 — 다시리깅이 새 손 모양으로 다시 만듦), 새 모델(Meshy 등)을 그 뼈대에 묶음
   - 처음 무게는 기준 모델 겉면에서 가장 가까운 점의 무게를 그대로 가져옴(데이터 옮기기) → 다시리깅이 덮어씀
   - 두 모델은 같은 좌표·크기여야 함(Meshy 는 키 1.9, 가운데 0 으로 같음). 금속 1 로 된 재질은 0 으로
   사용: .bpy_venv/bin/python -I 애니3D/뼈대옮기기.py <기준.glb> <새 모델.glb> <출력.glb>
   그다음: python3 애니3D/glb_다시리깅.py <출력.glb> <리깅.glb> --확인 <손가락.png>"""
import sys
import bpy

a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
ref, new, dst = a[0], a[1], a[2]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=ref)
arm = next(o for o in bpy.data.objects if o.type == "ARMATURE")
refm = max((o for o in bpy.data.objects if o.type == "MESH"), key=lambda o: len(o.data.vertices))
for o in [o for o in bpy.data.objects if o.type == "MESH" and o is not refm]: bpy.data.objects.remove(o, do_unlink=True)
FING = ("Thumb", "Index", "Middle", "Ring", "Little", "Pinky")
bpy.context.view_layer.objects.active = arm; bpy.ops.object.mode_set(mode="EDIT")
for eb in [e for e in arm.data.edit_bones if any(k in e.name for k in FING)]: arm.data.edit_bones.remove(eb)
bpy.ops.object.mode_set(mode="OBJECT")
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=new)
nm = next(o for o in bpy.data.objects if o not in before and o.type == "MESH")
for o in [o for o in bpy.data.objects if o not in before and o is not nm and o.type != "MESH"]: pass
mw = nm.matrix_world.copy(); nm.parent = None; nm.matrix_world = mw
for g in refm.vertex_groups:
    if not any(k in g.name for k in FING): nm.vertex_groups.new(name=g.name)
for m in nm.data.materials:
    if m and m.node_tree:
        bs = next((n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
        if bs:
            for l in list(bs.inputs["Metallic"].links): m.node_tree.links.remove(l)
            bs.inputs["Metallic"].default_value = 0.0
dt = nm.modifiers.new("dt", "DATA_TRANSFER"); dt.object = refm
dt.use_vert_data = True; dt.data_types_verts = {"VGROUP_WEIGHTS"}; dt.vert_mapping = "POLYINTERP_NEAREST"
dt.layers_vgroup_select_src = "ALL"; dt.layers_vgroup_select_dst = "NAME"
bpy.context.view_layer.objects.active = nm
bpy.ops.object.modifier_apply(modifier="dt")
am = nm.modifiers.new("arm", "ARMATURE"); am.object = arm
nm.parent = arm; nm.matrix_parent_inverse = arm.matrix_world.inverted()
bpy.data.objects.remove(refm, do_unlink=True)
for o in [o for o in bpy.data.objects if o.type == "EMPTY"]: bpy.data.objects.remove(o, do_unlink=True)
print("뼈", len(arm.data.bones), "점", len(nm.data.vertices), "무리", len(nm.vertex_groups))
bpy.ops.export_scene.gltf(filepath=dst, export_format="GLB", export_skins=True, export_morph=True, export_animations=False, export_image_format="AUTO")
print("→", dst)
