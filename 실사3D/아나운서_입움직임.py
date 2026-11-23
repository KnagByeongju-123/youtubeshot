"""아나운서(MPFB2 인물)가 나레이션에 맞춰 입을 움직이는 영상 (상반신, 파란 스튜디오 벽)
먼저: 인물_만들기.py 로 만든 <이름>.blend, 나레이션 mp3 (검사 통과한 것)
  ffmpeg -i 나레이션.mp3 -ac 1 -ar 16000 n.wav
  BLENDER_USER_RESOURCES=$PWD/models/blender_user .bpy_venv/bin/python -I 실사3D/아나운서_입움직임.py \
      <인물.blend> n.wav "<대본 글>" <프레임폴더> '{"samples":16}'
  → <프레임폴더>/f0001.png …  →  ffmpeg -framerate 24 -i <폴더>/f%04d.png -i 나레이션.mp3 -c:v libx264 -pix_fmt yuv420p -crf 18 -c:a aac -shortest 결과.mp4
  시험 한 장: '{"still":60}' → <폴더>/still.png
  옵션: size "1024x576"(기본), lens 70, dist 1.7(카메라 거리 m), tz -0.03(보는 높이), gain 1.0(입 벌림 크기), frames(앞부분만)
방법: 소리 크기(1/24초마다) = 입 벌림 정도, 대본 음절을 소리 난 구간에 순서대로 나눠 모음마다 입 모양
      (ㅏ=aa, ㅓ=ah, ㅔㅐ=eh, ㅗ=ow, ㅜ=uw, ㅣㅡ=iy, 첫소리 ㅁㅂㅍ·받침 ㅁㅂ = 입 닫음). 눈 깜빡임 약 2.9초마다, 고개 살짝 끄덕임
EEVEE 는 그래픽카드 없는 서버에서 안 됨 → Cycles 16샘플, 1280×720 한 장 약 10초 (7초 영상 약 30분)
"""
import bpy,sys,math,wave,json,addon_utils
import numpy as np
addon_utils.enable('bl_ext.user_default.mpfb',default_set=True)
from bl_ext.user_default.mpfb.services.faceservice import FaceService
blend,wav,text,out=sys.argv[1:5]; opt=json.loads(sys.argv[5]) if len(sys.argv)>5 else {}
FPS=24
bpy.ops.wm.open_mainfile(filepath=blend)
sc=bpy.context.scene
body=[o for o in bpy.data.objects if o.name.endswith('.body')][0]
FaceService.load_targets(body,load_microsoft_visemes=True,load_arkit_faceunits=True)
FaceService.interpolate_targets(body)
# --- 소리 크기
w=wave.open(wav); sr=w.getframerate(); a=np.frombuffer(w.readframes(w.getnframes()),dtype=np.int16).astype(np.float32)/32768
hop=sr//FPS; N=len(a)//hop+1
rms=np.array([np.sqrt(np.mean(a[i*hop:(i+1)*hop+hop//2]**2)+1e-12) for i in range(N)])
rms=np.convolve(rms,[0.25,0.5,0.25],'same'); peak=np.percentile(rms,95); thr=peak*0.12
voiced=[i for i in range(N) if rms[i]>thr]
# --- 글자(음절) → 입 모양
VOW={**{k:'aa_02' for k in (0,2,9)},**{k:'aa_ah_ax_01' for k in (4,6,14)},**{k:'ey_eh_uh_04' for k in (1,3,5,7,10,11,15)},
     **{k:'ow_08' for k in (8,12)},**{k:'w_uw_07' for k in (13,16,17)},18:'y_iy_ih_ix_06',19:'y_iy_ih_ix_06',20:'y_iy_ih_ix_06'}
VW={'aa_02':1.0,'aa_ah_ax_01':0.85,'ey_eh_uh_04':0.75,'ow_08':0.8,'w_uw_07':0.8,'y_iy_ih_ix_06':0.6}
syl=[c for c in text if 0xAC00<=ord(c)<=0xD7A3]
# 음절을 소리 난 구간(voiced)에 순서대로 고르게 나눔
per=len(voiced)/len(syl); plan={}
for j,ch in enumerate(syl):
    v=ord(ch)-0xAC00; cho,jung,jong=v//588,(v%588)//28,v%28
    fr=voiced[int(j*per):max(int((j+1)*per),int(j*per)+1)]
    for k,f in enumerate(fr):
        t=k/max(len(fr),1)
        if cho in (6,7,8,17) and t<0.3: key,wt='p_b_m_21',1.0
        elif jong in (16,17) and t>0.75: key,wt='p_b_m_21',1.0       # 받침 ㅁ·ㅂ → 입 닫음
        else: key,wt=VOW[jung],VW[VOW[jung]]
        plan[f]=(key,wt)
USED=sorted(set(k for k,_ in plan.values()))
objs=[o for o in bpy.data.objects if o.type=='MESH' and o.data.shape_keys]
gain=float(opt.get("gain",1.0))
for f in range(N):
    key,wt=plan.get(f,(None,0)); lvl=min(1.0,rms[f]/peak*1.2)*gain
    for o in objs:
        kb=o.data.shape_keys.key_blocks
        for k in USED:
            if k in kb:
                kb[k].value=(wt*lvl if k==key else 0.0); kb[k].keyframe_insert('value',frame=f+1)
# 눈 깜빡임 (약 3초마다, 0.2초)
blinks=[k for k in ('eyeBlinkLeft','eyeBlinkRight')]
for o in objs:
    kb=o.data.shape_keys.key_blocks
    for b in blinks:
        if b not in kb: continue
        for s in np.arange(1.2,N/FPS,2.9):
            f0=int(s*FPS)
            for df,v in ((0,0),(2,1),(4,0)): kb[b].value=v; kb[b].keyframe_insert('value',frame=f0+df)
# 고개: 아주 작게 끄덕임·기울임
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE')
hd=rig.pose.bones.get('head'); nk=rig.pose.bones.get('neck01')
for f in range(0,N,4):
    t=f/FPS
    for b,amp in ((hd,1.0),(nk,0.5)):
        if not b: continue
        b.rotation_mode='XYZ'; b.rotation_euler=(math.radians(amp*(1.6*math.sin(t*1.7)+0.8*math.sin(t*3.1))),math.radians(amp*1.2*math.sin(t*0.9)),math.radians(amp*1.0*math.sin(t*0.6)))
        b.keyframe_insert('rotation_euler',frame=f+1)
# --- 스튜디오: 배경 벽, 조명, 상반신 카메라
for o in list(bpy.data.objects):
    if o.type in ('CAMERA','LIGHT'): bpy.data.objects.remove(o)
sc.render.film_transparent=False
w=sc.world; bg=w.node_tree.nodes["Background"]; bg.inputs[0].default_value=(0.02,0.04,0.09,1); bg.inputs[1].default_value=1.0
hb=rig.matrix_world@rig.pose.bones['head'].head
bpy.ops.mesh.primitive_plane_add(size=8,location=(0,2.2,hb.z-0.5),rotation=(math.radians(90),0,0))
wall=bpy.context.object; m=bpy.data.materials.new("벽"); m.use_nodes=True; p=m.node_tree.nodes["Principled BSDF"]
p.inputs["Base Color"].default_value=(0.03,0.08,0.2,1); p.inputs["Roughness"].default_value=0.6; wall.data.materials.append(m)
def light(nm,loc,en,size,col=(1,1,1)):
    L=bpy.data.objects.new(nm,bpy.data.lights.new(nm,"AREA")); L.data.energy=en; L.data.size=size; L.data.color=col; L.location=loc
    L.rotation_euler=(hb-L.location).to_track_quat('-Z','Y').to_euler() if hasattr(hb,'to_track_quat') else (0,0,0); sc.collection.objects.link(L)
import mathutils
hb=mathutils.Vector(hb)
light("key",(-0.9,-1.6,hb.z+0.6),55,1.2); light("fill",(1.0,-1.4,hb.z+0.1),22,1.5); light("rim",(0.6,1.2,hb.z+0.5),60,0.8,(0.8,0.9,1))
L=bpy.data.objects.new("wall",bpy.data.lights.new("wall","AREA")); L.data.energy=60; L.data.size=3; L.location=(0,1.0,hb.z+1.2); L.rotation_euler=(math.radians(-60),0,0); sc.collection.objects.link(L)
cam=bpy.data.objects.new("cam",bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera=cam
cam.data.lens=float(opt.get("lens",70)); tgt=hb+mathutils.Vector((0,0,float(opt.get("tz",-0.03))))
cam.location=tgt+mathutils.Vector((0,-float(opt.get("dist",1.7)),0.02)); cam.rotation_euler=(tgt-cam.location).to_track_quat('-Z','Y').to_euler()
cam.data.dof.use_dof=True; cam.data.dof.focus_distance=(hb-cam.location).length; cam.data.dof.aperture_fstop=2.8
sc.frame_start=1; sc.frame_end=int(opt.get("frames",N)); sc.render.fps=FPS
sc.render.engine=opt.get("engine",'CYCLES')
if sc.render.engine=='CYCLES': sc.cycles.device='CPU'; sc.cycles.samples=int(opt.get("samples",16)); sc.cycles.use_denoising=True
rx,ry=map(int,opt.get("size","1024x576").split('x')); sc.render.resolution_x=rx; sc.render.resolution_y=ry
sc.render.image_settings.file_format='PNG'; sc.render.filepath=out+"/f"
if opt.get("still"):
    sc.frame_set(int(opt["still"])); sc.render.filepath=out+"/still.png"; bpy.ops.render.render(write_still=True)
else: bpy.ops.render.render(animation=True)
print("DONE",N,USED)
