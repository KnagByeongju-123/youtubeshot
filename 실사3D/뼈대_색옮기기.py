# 사용: .bpy_venv/bin/python -I 실사3D/뼈대_색옮기기.py <텍스처_굽기 완성.blend> <뼈대 GLB(같은 모양)> <결과폴더>
#  → 뼈대텍스처.png(4096) · 뼈대_완성.blend · 뼈대_완성.glb   (메시 AI 자동 리깅 GLB 는 색이 없어서, 구운 색을 표면→표면으로 옮김)
# 색 있는 모델(완성.blend 의 Mesh_0, 구운 텍스처) → 뼈대 있는 모델로 표면 색을 구워 옮김
import bpy,sys,os,math
done_blend,rig_glb,out=sys.argv[1],sys.argv[2],os.path.abspath(sys.argv[3]); os.makedirs(out,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=done_blend); sc=bpy.context.scene
src=next(o for o in sc.objects if o.type=='MESH'); src.name="색모델"
bpy.ops.import_scene.gltf(filepath=rig_glb)
for o in list(sc.objects):
    if o.type=='MESH' and o.name.startswith('Icosphere'): bpy.data.objects.remove(o)
dst=next(o for o in sc.objects if o.type=='MESH' and o.name.startswith('Announcer'))
arm=next(o for o in sc.objects if o.type=='ARMATURE')
# 색 모델: 텍스처를 빛 없이 그대로 내보내는 재질
m=src.data.materials[0]; nt=m.node_tree; tex=next(n for n in nt.nodes if n.type=='TEX_IMAGE')
em=nt.nodes.new('ShaderNodeEmission'); nt.links.new(tex.outputs['Color'],em.inputs['Color']); nt.links.new(em.outputs[0],nt.nodes['Material Output'].inputs['Surface'])
# 뼈대 모델: 펼친 지도 + 빈 그림
bpy.ops.object.select_all(action='DESELECT'); bpy.context.view_layer.objects.active=dst; dst.select_set(True)
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=0.002); bpy.ops.object.mode_set(mode='OBJECT')
img=bpy.data.images.new("뼈대텍스처",4096,4096)
d=bpy.data.materials.new("피부"); d.use_nodes=True; dn=d.node_tree; b=dn.nodes["Principled BSDF"]; t=dn.nodes.new('ShaderNodeTexImage'); t.image=img
dn.links.new(t.outputs['Color'],b.inputs['Base Color']); b.inputs['Roughness'].default_value=0.7; dn.nodes.active=t
dst.data.materials[0]=d                     # 첫 재질(몸)만 바꿈 — 입속 같은 다른 재질(Mouth_Interior_Dark)은 그대로
for m2 in dst.data.materials[1:]:                # 굽기는 재질마다 '고른 그림'이 있어야 함 → 같은 그림을 고르기만 (색엔 안 씀)
    if m2 and m2.use_nodes:
        t2=m2.node_tree.nodes.new('ShaderNodeTexImage'); t2.image=img; m2.node_tree.nodes.active=t2
src.select_set(True); dst.select_set(True); bpy.context.view_layer.objects.active=dst
sc.render.engine='CYCLES'; sc.cycles.device='CPU'; sc.cycles.samples=1
sc.render.bake.use_selected_to_active=True; sc.render.bake.cage_extrusion=0.02; sc.render.bake.max_ray_distance=0.05; sc.render.bake.margin=8
bpy.ops.object.bake(type='EMIT')
img.filepath_raw=out+"/뼈대텍스처.png"; img.file_format='PNG'; img.save()
bpy.data.objects.remove(src)
bpy.ops.wm.save_as_mainfile(filepath=out+"/뼈대_완성.blend")
bpy.ops.export_scene.gltf(filepath=out+"/뼈대_완성.glb",use_selection=False)
print("DONE", [b.name for b in arm.data.bones][:5])
