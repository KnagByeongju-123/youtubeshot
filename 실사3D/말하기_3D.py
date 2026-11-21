# 걸어오며: 설정에 "walk":true (또는 {"dist":3.4,"stop":5.2,...}) — 전신에서 시작해 걸어와 상반신에서 멈춤
# 사용: .bpy_venv/bin/python -I 실사3D/말하기_3D.py <입모양_만들기 결과.blend> <나레이션.wav> <발음시각.json> <프레임폴더> [{"still":40,"tz":-0.06,"d0":2.5,"d1":2.25}]
#  → ffmpeg -framerate 24 -i 폴더/f%04d.png -i 나레이션.wav ... 결과.mp4
# Meshy 3D 아나운서가 나레이션에 맞춰 말하기 (새 입 모양 + 고개·몸 + 조명 B)
import bpy,sys,json,math,wave,mathutils,numpy as np
blend,wav,timing,out=sys.argv[1:5]; opt=json.loads(sys.argv[5]) if len(sys.argv)>5 else {}
FPS=24
bpy.ops.wm.open_mainfile(filepath=blend); sc=bpy.context.scene
o=max((x for x in sc.objects if x.type=='MESH' and x.data.shape_keys),key=lambda x:len(x.data.vertices)); ar=next(x for x in sc.objects if x.type=='ARMATURE')
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
# 부드럽게: 열릴 때 0.035초·닫힐 때 0.05초 따라감 (Rhubarb 립싱크 예제의 attack/release 방식), 입술 닫힘은 그대로 강하게
ATT,REL=opt.get('attack',0.035),opt.get('release',0.05)
for k in KEYS:
    if k=='입_다묾': continue
    cur=0.0; sm=np.zeros(N)
    for f in range(N):
        tau=ATT if vals[k][f]>cur else REL; cur+=(vals[k][f]-cur)*(1-math.exp(-1/FPS/tau)); sm[f]=cur
    vals[k]=sm
shut=np.array([1.0 if plan[f].get('shut') else 0.0 for f in range(N)])
for k in KEYS:
    if k!='입_다묾': vals[k]*=(1-shut)                     # 닫히는 칸에선 다른 입 모양을 끔
for f in range(N):
    for k in KEYS: kb[k].value=float(vals[k][f]); kb[k].keyframe_insert('value',frame=f+1)
# 눈 깜빡임: 3.2~4.8초마다 0.17초 (눈감기_만들기 로 만든 '눈감기', 없으면 모델의 Blink)
BK='눈감기' if '눈감기' in kb else ('Blink' if 'Blink' in kb else None)
if BK and opt.get('blink',True):
    rng=np.random.default_rng(7); t=1.2
    while t<SEC:
        f0=int(t*FPS)
        for df,v in((-1,0),(0,0.6),(1,1),(2,1),(3,0.4),(4,0)):
            if 0<=f0+df<N: kb[BK].value=v; kb[BK].keyframe_insert('value',frame=f0+df+1)
        t+=rng.uniform(3.2,4.8)
# 고개·몸 (작게)
def key(bn,f,rot):
    pb=ar.pose.bones.get(bn)
    if pb: pb.rotation_mode='XYZ'; pb.rotation_euler=[math.radians(r) for r in rot]; pb.keyframe_insert('rotation_euler',frame=f)
for x in list(sc.objects):
    if x.type in('CAMERA','LIGHT') or x.name.startswith('Icosphere'): bpy.data.objects.remove(x)
if ar.animation_data: ar.animation_data.action=None
hd=ar.matrix_world@ar.data.bones['Head'].head_local
wd=sc.world or bpy.data.worlds.new("w"); sc.world=wd; wd.use_nodes=True; bg=wd.node_tree.nodes["Background"]; bg.inputs[0].default_value=(0.05,0.08,0.15,1); bg.inputs[1].default_value=0.35
def light(nm,loc,en,size,base=None):
    base=base or hd
    L=bpy.data.objects.new(nm,bpy.data.lights.new(nm,"AREA")); L.data.energy=en; L.data.size=size; L.location=base+mathutils.Vector(loc)
    L.rotation_euler=(base-L.location).to_track_quat('-Z','Y').to_euler(); sc.collection.objects.link(L)
cam=bpy.data.objects.new("cam",bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera=cam
WALK=opt.get('walk')
if not WALK:
    for f in range(1,N+1,3):
        t=f/FPS
        key('Head',f,(1.8*math.sin(t*1.9)+0.8*math.sin(t*3.1),1.2*math.sin(t*0.9),1.5*math.sin(t*0.7)))
        key('Neck',f,(0.6*math.sin(t*1.3),0,0.5*math.sin(t*0.5)))
        key('Spine1' if 'Spine1' in ar.pose.bones else 'Chest',f,(0.5*math.sin(t*1.1),0,0.6*math.sin(t*0.6)))
    # 조명 B + 카메라 (허리 위, 천천히 다가감)
    light("key",(-1.2,-2.2,0.8),60,1.5); light("fill",(1.4,-2.0,0.2),25,2); light("rim",(0.5,1.6,1.0),40,1)
    cam.data.lens=opt.get('lens',85)
    tgt=hd+mathutils.Vector((0,0,opt.get('tz',-0.18)))
    d0,d1=opt.get('d0',2.6),opt.get('d1',2.35)
    for f,d,xo in((1,d0,0.08),(N,d1,-0.04)):
        cam.location=tgt+mathutils.Vector((xo,-d,0.03)); cam.keyframe_insert('location',frame=f)
    cam.rotation_euler=(math.radians(89),0,0)
else:
    # 걸어오며 말하기 (사용자 요청 2026-11-21: 전신이 보이는 곳에서 걸어오며 나레이션)
    # 두 번째 메시 AI 모델 뼈대(뼈마다 X=세계 X, Y=위, Z=세계 -Y): 다리 X- = 앞으로, 무릎 X+ = 굽힘, 팔 X+ = 뒤로, 왼팔 Z- / 오른팔 Z+ = 몸 쪽
    W=dict(dict(dist=3.4,stop=5.2,period=1.1,thigh=17,knee=28,arm=9,lens=50,cam_d=2.45),**(WALK if isinstance(WALK,dict) else {}))
    FLOOR=min((o.matrix_world@mathutils.Vector(c)).z for c in o.bound_box)
    def env(t):                     # 걷기 세기: 0→1(0.4초) … 1→0(멈추기 전 0.8초)
        return max(0.0,min(1.0,t/0.4,(W['stop']-t)/0.8))
    pos=0.0; ph=0.0; root=ar.pose.bones['Root']; root.rotation_mode='XYZ'
    sp=W['dist']/max(0.1,W['stop']-0.6)          # 평균 빠르기 (시작·멈춤 느린 것 보정)
    for f in range(1,N+1):
        t=(f-1)/FPS; e=env(t)
        ph+=2*math.pi/W['period']/FPS*(0.3+0.7*e) if e>0 else 0
        pos+=sp/FPS*e
        s1,c1=math.sin(ph),math.cos(ph)
        thL,thR=-W['thigh']*s1*e, W['thigh']*s1*e
        knL=W['knee']*max(0,c1)**2*e; knR=W['knee']*max(0,-c1)**2*e
        key('UpperLeg.L',f,(thL,0,0)); key('UpperLeg.R',f,(thR,0,0))
        key('LowerLeg.L',f,(knL,0,0)); key('LowerLeg.R',f,(knR,0,0))
        key('Foot.L',f,(-(thL+knL)*0.5,0,0)); key('Foot.R',f,(-(thR+knR)*0.5,0,0))
        key('UpperArm.L',f,(W['arm']*s1*e,0,-15)); key('UpperArm.R',f,(-W['arm']*s1*e,0,15))
        key('ForeArm.L',f,(-4-3*e,0,0)); key('ForeArm.R',f,(-4-3*e,0,0))
        key('Hips',f,(0,4*s1*e,1.2*s1*e)); key('Spine',f,(1.0*e,-3*s1*e,-1.0*s1*e))
        key('Head',f,(1.2*math.sin(t*1.9)+0.6*math.sin(t*3.1),1.0*math.sin(t*0.9)+1.5*s1*e,1.2*math.sin(t*0.7)))
        key('Neck',f,(0.5*math.sin(t*1.3),0,0.4*math.sin(t*0.5)))
        # 앞으로(세계 -Y = Root 로컬 +Z) + 위아래 출렁임(로컬 Y)
        root.location=(0, -0.012*abs(math.cos(ph))*e, pos-W['dist']); root.keyframe_insert('location',frame=f)
    # 무대: 바닥(살짝 반사) + 뒤 벽 + 큰 부드러운 조명
    bpy.ops.mesh.primitive_plane_add(size=30,location=(0,6,FLOOR-0.001)); fl=bpy.context.object
    m=bpy.data.materials.new("바닥"); m.use_nodes=True; b=m.node_tree.nodes["Principled BSDF"]; b.inputs['Base Color'].default_value=(0.06,0.07,0.09,1); b.inputs['Roughness'].default_value=0.35
    fl.data.materials.append(m)
    bpy.ops.mesh.primitive_plane_add(size=30,location=(0,9,FLOOR+5),rotation=(math.radians(90),0,0)); wl=bpy.context.object
    m2=bpy.data.materials.new("벽"); m2.use_nodes=True; m2.node_tree.nodes["Principled BSDF"].inputs['Base Color'].default_value=(0.05,0.09,0.18,1); wl.data.materials.append(m2)
    mid=mathutils.Vector((0,W['dist']*0.5,0.3))
    light("key",(-1.8,-3.2,1.6),260,3.5,mid); light("fill",(2.2,-3.0,0.6),110,4,mid); light("rim",(0.8,2.5,1.8),160,2.5,mid)
    cam.data.lens=W['lens']
    tg=bpy.data.objects.new("보는곳",None); sc.collection.objects.link(tg)
    c=cam.constraints.new('TRACK_TO'); c.target=tg; c.track_axis='TRACK_NEGATIVE_Z'; c.up_axis='UP_Y'
    for f in range(1,N+1,4):
        sc.frame_set(f); p=ar.matrix_world@ar.pose.bones['Hips'].head
        k=min(1.0,max(0.0,(f/FPS)/W['stop']))
        tg.location=(0,p.y,0.05+0.45*k**1.3); tg.keyframe_insert('location',frame=f)
    cam.location=(0.15,-W['cam_d'],0.25); cam.keyframe_insert('location',frame=1)
    cam.location=(0.05,-W['cam_d'],0.48); cam.keyframe_insert('location',frame=N)
sc.render.engine='CYCLES'; sc.cycles.device='CPU'; sc.cycles.samples=opt.get('samples',16); sc.cycles.use_denoising=True
sc.view_settings.view_transform='Standard'
sc.render.resolution_x,sc.render.resolution_y=1024,576; sc.frame_start,sc.frame_end,sc.render.fps=opt.get('from',1),N,FPS   # from: 고친 뒷부분만 다시 찍기
if opt.get('still'):
    sc.frame_set(opt['still']); sc.render.filepath=out+"/still.png"; bpy.ops.render.render(write_still=True)
else:
    sc.render.filepath=out+"/f"; bpy.ops.render.render(animation=True)
print("DONE",N)
