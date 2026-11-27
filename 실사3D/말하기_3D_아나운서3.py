# 여자아나운서3(models/glb/여자아나운서3.glb) 말하기 — 다른 영상 위에 얹는 전신(투명 배경·바닥 그림자) (사용자 2026-11-27 'A안')
# 사용: .bpy_venv/bin/python -I 실사3D/말하기_3D_아나운서3.py <여자아나운서3.glb> <나레이션.wav(16k)> <발음시각.json> <프레임폴더> ['{설정}']
#   설정: from·to(프레임), still, size "640x800", turn 12(금형 쪽으로 돎), gestures [[시작초,끝초]] (왼팔 소개), light 0.55, samples 16
#   → 프레임(24fps, 투명 PNG) → ffmpeg overlay: scale=-1:666, overlay=-16:243 (인트로 A안 자리)
# 이 모델은 입 모양 키(AA_VI_*, MouthOpen/Round, AK_*)가 잘 움직여서 그대로 섞어 씀 (1·2번 Meshy 모델처럼 새로 만들 필요 없음)
# 뼈 방향이 팔과 달라서(뼈 끝이 다음 마디를 안 가리킴) 각도 대신 손목 자리 → 팔꿈치 계산(두 마디 IK)으로 자세를 잡음
import bpy,sys,json,math,wave,mathutils,numpy as np
V=mathutils.Vector
glb,wav,timing,out=sys.argv[1:5]; opt=json.loads(sys.argv[5]) if len(sys.argv)>5 else {}
FPS=24
bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=glb); sc=bpy.context.scene
for x in list(sc.objects):
    if x.name.startswith('Icosphere') or x.type in('CAMERA','LIGHT'): bpy.data.objects.remove(x)
ar=next(x for x in sc.objects if x.type=='ARMATURE')
if ar.animation_data: ar.animation_data.action=None
o=max((x for x in sc.objects if x.type=='MESH' and x.data.shape_keys),key=lambda x:len(x.data.vertices)); kb=o.data.shape_keys.key_blocks
for md in o.modifiers:
    if md.type=='ARMATURE': md.use_deform_preserve_volume=True
bpy.context.view_layer.update()
# 발을 예전 아나운서와 같은 바닥(-0.95)에
FLOOR=-0.95
mn=min((m.matrix_world@V(c)).z for m in sc.objects if m.type=='MESH' for c in m.bound_box)
for x in sc.objects:
    if x.parent is None: x.location.z+=FLOOR-mn
bpy.context.view_layer.update()
# ---------- 입 모양 (발음 시각 → 모음별 입 모양 → 부드럽게) ----------
MIX={'입_아':{'MouthOpen':0.55,'AK_25_JawOpen':0.15},'입_이':{'AA_VI_07_SS':0.8,'MouthWide':0.2},'입_오':{'AA_VI_13_O':0.85},
     '입_우':{'MouthRound':0.9,'AA_VI_13_O':0.15},'입_다묾':{'AA_VI_01_PP':1.0}}
w=wave.open(wav); sr=w.getframerate(); a=np.frombuffer(w.readframes(w.getnframes()),np.int16).astype(np.float32)/32768
if w.getnchannels()>1: a=a.reshape(-1,w.getnchannels()).mean(1)
SEC=opt.get('sec',len(a)/sr); N=int(SEC*FPS); hop=sr//FPS
rms=np.array([np.sqrt(np.mean(a[i*hop:(i+1)*hop]**2)+1e-12) if i*hop<len(a) else 0 for i in range(N)])
rms=np.convolve(rms,[0.25,0.5,0.25],'same'); rms=np.clip(rms/(np.percentile(rms,95)+1e-9),0,1.2)
def shape(jung):
    if jung in(0,1,2,3,9,10,11): return {'입_아':0.85,'입_이':0.2}
    if jung in(5,6,7,15,16):     return {'입_아':0.6,'입_이':0.45}
    if jung in(4,14):            return {'입_아':0.55,'입_오':0.3}
    if jung in(8,12):            return {'입_오':0.9,'입_아':0.15}
    if jung in(13,17):           return {'입_우':0.9}
    if jung in(18,19):           return {'입_이':0.6,'입_아':0.2}
    return {'입_이':0.8,'입_아':0.15}
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
KEYS=list(MIX)
vals={k:np.zeros(N) for k in KEYS}
for f in range(N):
    for k in KEYS:
        v=plan[f].get(k,0.0); vals[k][f]=v if k=='입_다묾' else v*min(1.0,0.35+rms[f])
ATT,REL=opt.get('attack',0.035),opt.get('release',0.05)
for k in KEYS:
    if k=='입_다묾': continue
    cur=0.0; sm=np.zeros(N)
    for f in range(N):
        tau=ATT if vals[k][f]>cur else REL; cur+=(vals[k][f]-cur)*(1-math.exp(-1/FPS/tau)); sm[f]=cur
    vals[k]=sm
shut=np.array([1.0 if plan[f].get('shut') else 0.0 for f in range(N)])
for k in KEYS:
    if k!='입_다묾': vals[k]*=(1-shut)
blink=np.zeros(N); rng=np.random.default_rng(7); t=1.2
while t<SEC:
    f0=int(t*FPS)
    for df,v in((-1,0),(0,0.6),(1,1),(2,1),(3,0.4),(4,0)):
        if 0<=f0+df<N: blink[f0+df]=v
    t+=rng.uniform(3.2,4.8)
used=sorted({s for m in MIX.values() for s in m}|{'AK_09_EyeBlinkLeft','AK_10_EyeBlinkRight'})
for f in range(N):
    tot={s:0.0 for s in used}
    for k in KEYS:
        for s,wt in MIX[k].items(): tot[s]+=vals[k][f]*wt
    tot['AK_09_EyeBlinkLeft']=tot['AK_10_EyeBlinkRight']=blink[f]
    for s in used:
        kb[s].value=min(1.0,tot[s]); kb[s].keyframe_insert('value',frame=f+1)
# ---------- 자세 (손목 자리 → 팔꿈치 계산) ----------
P=lambda bn: ar.matrix_world@ar.pose.bones[bn].head
def reset():
    for pb in ar.pose.bones: pb.rotation_mode='QUATERNION'; pb.rotation_quaternion=(1,0,0,0); pb.location=(0,0,0)
    bpy.context.view_layer.update()
def rotw(bn,axis,deg):                 # 뼈를 세계 축 둘레로 돌림 (자식도 따라감)
    pb=ar.pose.bones[bn]; M=ar.matrix_world@pb.matrix; h=M.to_translation()
    R=mathutils.Matrix.Rotation(math.radians(deg),4,V(axis))
    pb.matrix=ar.matrix_world.inverted()@(mathutils.Matrix.Translation(h)@R@mathutils.Matrix.Translation(-h)@M); bpy.context.view_layer.update()
def aim(bn,child,target_dir):          # 뼈→자식 방향을 세계 방향으로
    pb=ar.pose.bones[bn]; M=ar.matrix_world@pb.matrix; h=M.to_translation()
    cur=(P(child)-h).normalized(); R=cur.rotation_difference(V(target_dir).normalized()).to_matrix().to_4x4()
    pb.matrix=ar.matrix_world.inverted()@(mathutils.Matrix.Translation(h)@R@mathutils.Matrix.Translation(-h)@M); bpy.context.view_layer.update()
def arm(s,T,pole,hand_dir):
    S=P('UpperArm.'+s); L1=(P('ForeArm.'+s)-S).length; L2=(P('Hand.'+s)-P('ForeArm.'+s)).length
    d=min((T-S).length,(L1+L2)*0.995); u=(T-S).normalized(); T=S+u*d
    a_=(L1*L1-L2*L2+d*d)/(2*d); h=math.sqrt(max(L1*L1-a_*a_,1e-8))
    p=V(pole); p=(p-u*p.dot(u)).normalized(); E=S+u*a_+p*h
    aim('UpperArm.'+s,'ForeArm.'+s,E-S); aim('ForeArm.'+s,'Hand.'+s,T-E); aim('Hand.'+s,'Middle1.'+s,hand_dir)
reset()
SIDE={s:(1 if P('UpperArm.'+s).x>0 else -1) for s in('L','R')}
HIP=P('Hips'); CH=P('Chest') if 'Chest' in ar.pose.bones else P('Spine1')
BONES=[b.name for b in ar.pose.bones if b.name in('Hips','Spine','Spine1','Chest','Neck','Head') or b.name.split('.')[0] in('Shoulder','UpperArm','ForeArm','Hand')]
GEST=opt.get('gestures',[[9.9,17.0]]); RP=opt.get('gesture_ramp',1.2)
FR=[opt['still']] if opt.get('still') else range(opt.get('from',1),opt.get('to',N)+1)   # 찍을 프레임만 자세 계산
for f in FR:
    t=(f-1)/FPS; reset()
    br=0.5-0.5*math.cos(2*math.pi*t/4.2)
    g=0.0
    for g0,g1 in GEST: g=max(g,min(1.0,max(0.0,(t-g0)/RP),max(0.0,(g1-t)/RP)))
    g=g*g*(3-2*g)
    # 몸: 천천히 몸무게 옮기듯 + 소개할 때 금형 쪽으로 몸을 조금 돌림
    rotw('Spine',(0,0,1),1.0*math.sin(t*0.5)+7*g); rotw('Spine',(0,1,0),0.8*math.sin(t*0.37+1))
    rotw('Chest' if 'Chest' in ar.pose.bones else 'Spine1',(1,0,0),0.6*br)
    rotw('Head',(1,0,0),1.2*math.sin(t*1.9)+0.6*math.sin(t*3.1)); rotw('Head',(0,0,1),1.0*math.sin(t*0.9)-4*g); rotw('Head',(0,1,0),1.0*math.sin(t*0.7))
    hip=P('Hips')
    for s in('L','R'):
        sd=SIDE[s]
        Tc=V((sd*opt.get('hand_gap',0.085),hip.y-opt.get('hand_front',0.20),hip.z+0.10+0.004*br))   # 두 손을 배 앞에 (사용자 2026-11-27 '손이 겹치거나 몸을 통과하지 않게': 손 사이를 띄우고 배에서 20cm 앞)
        # 소개 팔 = 화면 오른쪽(금형 쪽, x>0) 팔
        if sd>0 and g>0:
            Sh=P('UpperArm.'+s); wob=0.012*math.sin(t*1.6)*g
            Tg=Sh+V((0.40,-0.30,-0.30+wob))
            T=Tc.lerp(Tg,g); pole=V((0.3,0.6,-0.6)).lerp(V((0.0,0.4,-1.0)),g)
            hd=V((-sd*0.3,-0.4,-0.87)).lerp(V((0.55,-0.55,0.05)),g)
        else:
            T=Tc; pole=V((sd*0.3,0.6,-0.6)); hd=V((-sd*0.3,-0.4,-0.87))
        arm(s,T,pole,hd)
    for bn in BONES:
        pb=ar.pose.bones[bn]; pb.keyframe_insert('rotation_quaternion',frame=f); pb.keyframe_insert('location',frame=f)
# 금형 쪽으로 몸을 돌림 (얼굴 방향 +는 화면 오른쪽)
for x in sc.objects:
    if x.parent is None: x.rotation_euler.z+=math.radians(opt.get('turn',12))
# ---------- 조명·카메라 (예전 인트로 아나운서와 같음) ----------
wd=bpy.data.worlds.new("w"); sc.world=wd; wd.use_nodes=True; bg=wd.node_tree.nodes["Background"]; bg.inputs[0].default_value=(0.05,0.08,0.15,1); bg.inputs[1].default_value=0.35
def light(nm,loc,en,size,base):
    L=bpy.data.objects.new(nm,bpy.data.lights.new(nm,"AREA")); L.data.energy=en; L.data.size=size; L.location=base+V(loc)
    L.rotation_euler=(base-L.location).to_track_quat('-Z','Y').to_euler(); sc.collection.objects.link(L)
mid=V((0,0,0.3)); LS=opt.get('light',0.55)
light("key",(-1.8,-3.2,1.6),260*LS,3.5,mid); light("fill",(2.2,-3.0,0.6),110*LS,4,mid); light("rim",(0.8,2.5,1.8),160*LS,2.5,mid)
bpy.ops.mesh.primitive_plane_add(size=30,location=(0,6,FLOOR-0.001)); fl=bpy.context.object; fl.is_shadow_catcher=True
sc.render.film_transparent=True
cam=bpy.data.objects.new("cam",bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera=cam; cam.data.lens=50
tg=bpy.data.objects.new("t",None); sc.collection.objects.link(tg); tg.location=(0,0,-0.02)
c=cam.constraints.new('TRACK_TO'); c.target=tg; c.track_axis='TRACK_NEGATIVE_Z'; c.up_axis='UP_Y'; cam.location=(0,-3.1,0)
if opt.get('view')=='side': cam.location=(3.1,0,0)      # 검수용: 옆에서 (손이 몸을 뚫는지)
if opt.get('view')=='top': cam.location=(0,-0.6,3.0)     # 검수용: 위에서 (두 손이 겹치는지)
sc.render.engine='CYCLES'; sc.cycles.device='CPU'; sc.cycles.samples=opt.get('samples',16); sc.cycles.use_denoising=True
sc.view_settings.view_transform='Standard'
sc.render.resolution_x,sc.render.resolution_y=map(int,opt.get('size','640x800').split('x'))
sc.frame_start,sc.frame_end,sc.render.fps=opt.get('from',1),opt.get('to',N),FPS
if opt.get('still'):
    sc.frame_set(opt['still']); sc.render.filepath=out+"/still_%04d.png"%opt['still']; bpy.ops.render.render(write_still=True)
else:
    sc.render.filepath=out+"/f"; bpy.ops.render.render(animation=True)
print("DONE",N)
