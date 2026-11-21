# 사용: .bpy_venv/bin/python -I 실사3D/말하기_3D.py <입모양_만들기 결과.blend> <나레이션.wav> <발음시각.json> <프레임폴더> [{"still":40,"tz":-0.06,"d0":2.5,"d1":2.25}]
#  → ffmpeg -framerate 24 -i 폴더/f%04d.png -i 나레이션.wav ... 결과.mp4
# Meshy 3D 아나운서가 나레이션에 맞춰 말하기 (새 입 모양 + 고개·몸 + 조명 B)
import bpy,sys,json,math,wave,mathutils,numpy as np
blend,wav,timing,out=sys.argv[1:5]; opt=json.loads(sys.argv[5]) if len(sys.argv)>5 else {}
FPS=24
bpy.ops.wm.open_mainfile(filepath=blend); sc=bpy.context.scene
o=next(x for x in sc.objects if x.type=='MESH' and x.data.shape_keys); ar=next(x for x in sc.objects if x.type=='ARMATURE')
kb=o.data.shape_keys.key_blocks
for k in list(kb)[1:]:
    if k.name in('Smile','Frown'): o.shape_key_remove(k)
kb=o.data.shape_keys.key_blocks
w=wave.open(wav); sr=w.getframerate(); a=np.frombuffer(w.readframes(w.getnframes()),np.int16).astype(np.float32)/32768
SEC=opt.get('sec',len(a)/sr); N=int(SEC*FPS); hop=sr//FPS
rms=np.array([np.sqrt(np.mean(a[i*hop:(i+1)*hop]**2)+1e-12) if i*hop<len(a) else 0 for i in range(N)])
rms=np.convolve(rms,[0.25,0.5,0.25],'same'); rms=np.clip(rms/(np.percentile(rms,95)+1e-9),0,1.2)
# 모음 → 입 모양 (입모양표 벌림: 아1.36 에1.25 이1.08 어0.95 으0.91 오0.67 우0.63)
def shape(jung):
    if jung in(0,1,2,3,9,10,11): return {'입_아':0.85,'입_이':0.2}          # ㅏㅐㅑㅒ ㅘㅙㅚ
    if jung in(5,6,7,15,16):     return {'입_아':0.6,'입_이':0.45}          # ㅔㅕㅖ ㅞㅟ
    if jung in(4,14):            return {'입_아':0.55,'입_오':0.3}          # ㅓ ㅝ
    if jung in(8,12):            return {'입_오':0.9,'입_아':0.15}          # ㅗ ㅛ
    if jung in(13,17):           return {'입_우':0.9}                       # ㅜ ㅠ
    if jung in(18,19):           return {'입_이':0.6,'입_아':0.2}           # ㅡ ㅢ
    return {'입_이':0.8,'입_아':0.15}                                       # ㅣ
LAG=-0.2; plan=[dict() for _ in range(N)]
for ch,s0,e0 in json.load(open(timing,encoding='utf-8')):
    v=ord(ch)-0xAC00
    if not 0<=v<11172: continue
    cho,jung,jong=v//588,(v%588)//28,v%28
    f0=int((s0+LAG)*FPS); f1=max(f0+1,int(round((e0+LAG)*FPS)))
    fr=[f for f in range(f0,f1) if 0<=f<N]
    for k,f in enumerate(fr):
        t=k/max(len(fr),1)
        if (cho in(6,7,8,17) and t<0.25) or (jong in(16,17,26) and t>(0.15 if jung in(18,19,20) else 0.4)): plan[f]={'입_다묾':1.0,'shut':1}
        else: plan[f]=shape(jung)
    if jong in(16,17,26) and fr and fr[-1]+1<N: plan[fr[-1]+1]={'입_다묾':1.0,'shut':1}
KEYS=['입_아','입_이','입_오','입_우','입_다묾']
vals={k:np.zeros(N) for k in KEYS}
for f in range(N):
    for k in KEYS:
        v=plan[f].get(k,0.0); vals[k][f]=v if k=='입_다묾' else v*min(1.0,0.35+rms[f])
for k in KEYS:   # 부드럽게 (닫힘은 그대로 강하게)
    sm=np.convolve(vals[k],[0.2,0.6,0.2],'same')
    vals[k]=np.maximum(sm,vals[k]) if k=='입_다묾' else sm
for f in range(N):
    for k in KEYS: kb[k].value=float(vals[k][f]); kb[k].keyframe_insert('value',frame=f+1)
# 고개·몸 (작게)
def key(bn,f,rot):
    pb=ar.pose.bones.get(bn)
    if pb: pb.rotation_mode='XYZ'; pb.rotation_euler=[math.radians(r) for r in rot]; pb.keyframe_insert('rotation_euler',frame=f)
for f in range(1,N+1,3):
    t=f/FPS
    key('Head',f,(1.8*math.sin(t*1.9)+0.8*math.sin(t*3.1),1.2*math.sin(t*0.9),1.5*math.sin(t*0.7)))
    key('Neck',f,(0.6*math.sin(t*1.3),0,0.5*math.sin(t*0.5)))
    key('Spine1',f,(0.5*math.sin(t*1.1),0,0.6*math.sin(t*0.6)))
# 조명 B + 카메라 (허리 위, 천천히 다가감)
for x in list(sc.objects):
    if x.type in('CAMERA','LIGHT') or x.name.startswith('Icosphere'): bpy.data.objects.remove(x)
hd=ar.matrix_world@ar.data.bones['Head'].head_local
wd=sc.world or bpy.data.worlds.new("w"); sc.world=wd; wd.use_nodes=True; bg=wd.node_tree.nodes["Background"]; bg.inputs[0].default_value=(0.05,0.08,0.15,1); bg.inputs[1].default_value=0.35
def light(nm,loc,en,size):
    L=bpy.data.objects.new(nm,bpy.data.lights.new(nm,"AREA")); L.data.energy=en; L.data.size=size; L.location=hd+mathutils.Vector(loc)
    L.rotation_euler=(hd-L.location).to_track_quat('-Z','Y').to_euler(); sc.collection.objects.link(L)
light("key",(-1.2,-2.2,0.8),60,1.5); light("fill",(1.4,-2.0,0.2),25,2); light("rim",(0.5,1.6,1.0),40,1)
cam=bpy.data.objects.new("cam",bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera=cam; cam.data.lens=opt.get('lens',85)
tgt=hd+mathutils.Vector((0,0,opt.get('tz',-0.18)))
d0,d1=opt.get('d0',2.6),opt.get('d1',2.35)
for f,d,xo in((1,d0,0.08),(N,d1,-0.04)):
    cam.location=tgt+mathutils.Vector((xo,-d,0.03)); cam.keyframe_insert('location',frame=f)
cam.rotation_euler=(math.radians(89),0,0)
sc.render.engine='CYCLES'; sc.cycles.device='CPU'; sc.cycles.samples=opt.get('samples',16); sc.cycles.use_denoising=True
sc.view_settings.view_transform='Standard'
sc.render.resolution_x,sc.render.resolution_y=1024,576; sc.frame_start,sc.frame_end,sc.render.fps=1,N,FPS
if opt.get('still'):
    sc.frame_set(opt['still']); sc.render.filepath=out+"/still.png"; bpy.ops.render.render(write_still=True)
else:
    sc.render.filepath=out+"/f"; bpy.ops.render.render(animation=True)
print("DONE",N)
