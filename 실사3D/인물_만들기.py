"""MPFB2 로 오리지널 사람(3D) 만들고 캐릭터 시트(앞·왼옆·오른옆·뒤, 흰 바탕) 찍기
먼저: bash 실사3D/준비.sh
사용: BLENDER_USER_RESOURCES=$PWD/models/blender_user .bpy_venv/bin/python -I 실사3D/인물_만들기.py \
        <이름> <머리> <옷> <신발> <결과폴더> '<추가 JSON>'
  머리: bob01 bob02 long01 ponytail01 braid01 short01~04 afro01 (data/hair)
  옷:   female_elegantsuit01(줄무늬 셔츠+치마, 사무실용) female_casualsuit01·02 female_sportsuit01 male_* (data/clothes)
  신발: shoes01(갈색 구두) shoes03(검은 부츠) shoes04(검은 구두) shoes02·05·06(운동화) — 흰 양말이 붙어 있어 shoes_color 로 함께 칠함
  추가 JSON 예: {"samples":40,"suit_color":[0.012,0.018,0.05],"hair_mul":[0.25,0.2,0.18],"ph":{"age":0.55},
                 "skin":"young_asian_female","gender":"female"}
  결과: <폴더>/<이름>_0~3.png(투명 바탕) + <이름>.blend (영상 장면에서 불러 씀)
  흰 바탕 시트: ffmpeg -f lavfi -i color=white:s=2240x1120 -i 이름_0.png -i 이름_1.png -i 이름_2.png -i 이름_3.png \
        -filter_complex "[1][2][3][4]hstack=4[h];[0][h]overlay" -frames:v 1 이름_시트.jpg
"""
import bpy,sys,json,math,mathutils,os
import addon_utils; addon_utils.enable('bl_ext.user_default.mpfb',default_set=True)
from bl_ext.user_default.mpfb.services.humanservice import HumanService
DATA=os.environ['BLENDER_USER_RESOURCES']+'/extensions/.user/user_default/mpfb/data'
name,hair,suit,shoes,outdir=sys.argv[1:6]
extra=json.loads(sys.argv[6]) if len(sys.argv)>6 else {}
for o in list(bpy.data.objects): bpy.data.objects.remove(o)
info=HumanService._create_default_human_info_dict()
info["phenotype"].update({"gender":0.0 if extra.get("gender","female")=="female" else 1.0,"age":0.5,"muscle":0.45,"weight":0.42,"height":0.55,"proportions":0.7,"cupsize":0.45,"race":{"asian":1.0,"caucasian":0.0,"african":0.0}})
info["phenotype"].update(extra.get("ph",{}))
info.update({"name":name,"eyes":"high-poly/high-poly.mhclo","eyebrows":"eyebrow001/eyebrow001.mhclo","eyelashes":"eyelashes01/eyelashes01.mhclo",
 "teeth":"teeth_base/teeth_base.mhclo","tongue":"tongue01/tongue01.mhclo","hair":f"{hair}/{hair}.mhclo",
 "clothes":[f"{suit}/{suit}.mhclo",f"{shoes}/{shoes}.mhclo"],"skin_mhmat":f"{extra.get('skin','young_asian_female')}/{extra.get('skin','young_asian_female')}.mhmat",
 "skin_material_type":"ENHANCED_SSS","rig":"default"})
st=HumanService.get_default_deserialization_settings(); st["subdiv_levels"]=1
body=HumanService.deserialize_from_dict(info,st)
sc=bpy.context.scene
# 팔 내리기: 기본은 A자로 벌린 자세 → upperarm01 을 Z축으로 -32도 (+ 쪽은 T자로 올라감)
rig=next((o for o in sc.objects if o.type=='ARMATURE'),None)
if rig:
    for side,sgn in (("l",1),("r",-1)):
        for bn in (f"upperarm01.{side.upper()}",):
            b=rig.pose.bones.get(bn)
            if b: b.rotation_mode='XYZ'; b.rotation_euler=[math.radians(sgn*extra.get('arm',-32)) if k==extra.get('axis',2) else 0 for k in range(3)]
    bpy.context.view_layer.update()
def insert_mul(mat,col,replace=False):
    nt=mat.node_tree; bsdf=next(n for n in nt.nodes if n.type=='BSDF_PRINCIPLED'); inp=bsdf.inputs['Base Color']
    if replace or not inp.links:
        for l in list(inp.links): nt.links.remove(l)
        inp.default_value=(*col,1); return
    src=inp.links[0].from_socket; m=nt.nodes.new('ShaderNodeMix'); m.data_type='RGBA'; m.blend_type='MULTIPLY'; m.inputs['Factor'].default_value=1
    nt.links.new(src,m.inputs[6]); m.inputs[7].default_value=(*col,1); nt.links.new(m.outputs[2],inp)
for o in sc.objects:
    if o.type!='MESH' or not o.data.materials: continue
    mat=o.data.materials[0]; n=o.name.lower()
    if hair in n: insert_mul(mat,extra.get('hair_mul',(0.35,0.3,0.28)))
    if suit in n and 'suit_color' in extra: insert_mul(mat,extra['suit_color'],replace=True)
    if shoes in n: insert_mul(mat,extra.get('shoes_color',(0.025,0.025,0.03)),replace=True)
    if 'high-poly' in n:
        for nd in mat.node_tree.nodes:
            if nd.type=='TEX_IMAGE' and nd.image: nd.image=bpy.data.images.load(DATA+'/eyes/materials/brown_eye.png')
meshes=[o for o in sc.objects if o.type=='MESH' and not o.hide_render]
pts=[o.matrix_world@mathutils.Vector(c) for o in meshes for c in o.bound_box]
mn=mathutils.Vector([min(p[i] for p in pts) for i in range(3)]);mx=mathutils.Vector([max(p[i] for p in pts) for i in range(3)])
H=mx.z-mn.z; c=mathutils.Vector((0,0,mn.z+H/2))
w=bpy.data.worlds.new("w"); sc.world=w; w.use_nodes=True; bg=w.node_tree.nodes["Background"]; bg.inputs[0].default_value=(1,1,1,1); bg.inputs[1].default_value=0.5; sc.render.film_transparent=True
cam=bpy.data.objects.new("cam",bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera=cam
cam.data.type='ORTHO'; cam.data.ortho_scale=H*1.08
for nm,loc,en in (("key",(-2,-3,3),350),("fill",(3,-2,2),120),("back",(0,4,3),250)):
    L=bpy.data.objects.new(nm,bpy.data.lights.new(nm,"AREA")); L.data.energy=en; L.data.size=3; L.location=loc
    L.rotation_euler=(c-L.location).to_track_quat('-Z','Y').to_euler(); sc.collection.objects.link(L)
sc.render.engine='CYCLES'; sc.cycles.device='CPU'; sc.cycles.samples=int(extra.get("samples",48)); sc.cycles.use_denoising=True
sc.render.resolution_x=560; sc.render.resolution_y=1120
os.makedirs(outdir,exist_ok=True)
for i,(vn,ang) in enumerate((("앞",0),("왼옆",90),("오른옆",-90),("뒤",180))[:int(extra.get("nviews",4))]):
    t=math.radians(ang); d=10
    cam.location=(c.x+d*math.sin(t),c.y-d*math.cos(t),c.z)
    cam.rotation_euler=(c-cam.location).to_track_quat('-Z','Y').to_euler()
    sc.render.filepath=f"{outdir}/{name}_{i}.png"; bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=f"{outdir}/{name}.blend")
print("DONE",name,H)
