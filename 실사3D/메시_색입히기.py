# 모양만 있는 3D 모델(GLB, 예: 메시 AI 에서 '모양만' 받은 것)에 원본 그림을 앞에서 비춰 색으로 입힘 (앞모습 ±30도용)
# 사용: .bpy_venv/bin/python -I 실사3D/메시_색입히기.py <모델.glb> <원본그림.png> <결과이름>
#   → <결과이름>_앞.png·_비스듬.png·_얼굴.png + <결과이름>.blend
# 원본 그림에서 사람이 차지하는 위·아래·가운데(IW·IH·TOP·BOT·CX)를 맞춰야 함 (2026-11-21 메시 아나운서: 1696×2528, 89·2449·886).
# 하얀 테두리 막기: 원본 그림의 흰 배경을 사람 가장자리 색으로 번지게 채운 그림을 씀. 머리 폭이 다르면 그림을 좌우로 늘려 맞춤(실사3D.md)
# 모양만 있는 GLB 에 원본 그림을 앞에서 비춰 색으로 입힘 (앞모습용)
import bpy,sys,math,mathutils
glb,img,out=sys.argv[1],sys.argv[2],sys.argv[3]
IW,IH=1696,2528; TOP,BOT,CX=89,2449,886
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
sc=bpy.context.scene; ob=next(o for o in sc.objects if o.type=='MESH')
zmin,zmax=-0.952,0.951; s=(zmax-zmin)/(BOT-TOP)
pc=bpy.data.objects.new("proj",bpy.data.cameras.new("proj")); sc.collection.objects.link(pc)
pc.data.type='ORTHO'; pc.data.ortho_scale=max(IW,IH)*s
pc.location=((IW/2-CX)*s, -5, zmax-(IH/2-TOP)*s); pc.rotation_euler=(math.radians(90),0,0)
ob.data.uv_layers.new(name="proj")
md=ob.modifiers.new("uvp",'UV_PROJECT'); md.uv_layer="proj"; md.projector_count=1; md.projectors[0].object=pc; md.aspect_x=IW; md.aspect_y=IH
m=bpy.data.materials.new("사진색"); m.use_nodes=True; nt=m.node_tree; b=nt.nodes["Principled BSDF"]
t=nt.nodes.new('ShaderNodeTexImage'); t.image=bpy.data.images.load(img); t.extension='EXTEND'
uv=nt.nodes.new('ShaderNodeUVMap'); uv.uv_map="proj"; nt.links.new(uv.outputs[0],t.inputs[0]); nt.links.new(t.outputs[0],b.inputs['Base Color'])
b.inputs['Roughness'].default_value=0.75
ob.data.materials.clear(); ob.data.materials.append(m)
w=bpy.data.worlds.new("w"); sc.world=w; w.use_nodes=True; bg=w.node_tree.nodes["Background"]; bg.inputs[0].default_value=(0.9,0.9,0.92,1); bg.inputs[1].default_value=0.8
def light(nm,loc,en,size):
    L=bpy.data.objects.new(nm,bpy.data.lights.new(nm,"AREA")); L.data.energy=en; L.data.size=size; L.location=loc
    L.rotation_euler=(mathutils.Vector((0,0,0.3))-mathutils.Vector(loc)).to_track_quat('-Z','Y').to_euler(); sc.collection.objects.link(L)
light("key",(-1.2,-2.5,1.6),120,2); light("fill",(1.5,-2,0.8),50,2.5)
cam=bpy.data.objects.new("cam",bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera=cam
sc.render.engine='CYCLES'; sc.cycles.device='CPU'; sc.cycles.samples=16; sc.cycles.use_denoising=True
sc.view_settings.view_transform='Standard'
for nm,ang,tz,dist,lens,res in (("앞",0,0.0,5.2,50,(400,800)),("비스듬",25,0.0,5.2,50,(400,800)),("얼굴",0,0.78,1.1,85,(500,500))):
    t_=mathutils.Vector((0,0,tz)); a=math.radians(ang)
    cam.data.lens=lens; cam.location=t_+mathutils.Vector((dist*math.sin(a),-dist*math.cos(a),0)); cam.rotation_euler=(t_-cam.location).to_track_quat('-Z','Y').to_euler()
    sc.render.resolution_x,sc.render.resolution_y=res; sc.render.filepath=f"{out}_{nm}.png"; bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=out+".blend")
print("DONE")
