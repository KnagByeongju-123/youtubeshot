import sys,os; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from s3d import *
T,E,DUR,cs=chapter(3)
sc=setup(texture=True)
floor(extent=2000)
# AI 상자 · 프리캐드 상자
AX,FX=-520,520
ai=box((180,180,180),(AX,0,110),COL['sky'],bevel=18,name='ai'); show(ai,T(1)+0.2)
ta=text('AI',60,(AX,-92,120),rgb=COL['ink']); show(ta,T(1)+0.4)
fc=box((220,180,200),(FX,0,120),COL['purple'],bevel=14,name='fc'); show(fc,T(1)+0.8)
tf=text('FreeCAD',34,(FX,-92,170),rgb=COL['white']); show(tf,T(1)+1.0)
scr=box((170,4,90),(FX,-92,80),(0.10,0.12,0.16),name='scr'); show(scr,T(1)+1.0)
# MCP 플러그 (AI 쪽) → 소켓 (프리캐드 쪽)
pipe=cyl(14,300,(0,0,110),(0.30,0.34,0.42),rot=(0,math.radians(90),0),name='pipe'); show(pipe,T(2)+0.1)
plug=empty('plug',(0,0,110))
pb=box((70,60,60),(0,0,0),COL['accent'],bevel=6,name='plugb'); pb.parent=plug
for dy in (-14,14): p_=box((40,8,14),(55,dy,0),COL['post'],name='pin'); p_.parent=plug
keyv(plug,'location',[(0,(-160,0,110)),(T(3)+0.5,(-160,0,110)),(T(3)+2.0,(60,0,110)),(T(3)+2.2,(52,0,110))])
show(plug,T(2)+0.2,base=(1,1,1))
sock=box((40,90,90),(150,0,110),(0.25,0.28,0.35),bevel=6,name='sock'); show(sock,T(2)+0.3)
tm=text('MCP',44,(0,-60,230),rgb=COL['accent']); show(tm,T(2)+0.1)
tm2=text('AI ↔ 프로그램을 잇는 표준 연결',26,(0,-60,190),rgb=COL['white']); show(tm2,T(3)+0.3,E(4))
flash=box((60,100,100),(150,0,110),(1,1,0.7),name='flash'); keyv(flash,'scale',[(0,(0,0,0)),(T(3)+2.0,(0,0,0)),(T(3)+2.1,(1.2,1.2,1.2)),(T(3)+2.5,(0,0,0))])
# 명령 조각이 관을 따라 흐름
cmds=[('스케치',COL['white']),('회전',COL['sky']),('모서리 R',COL['accent']),('STEP 저장',(0.4,1,0.5))]
for i,(s_,c_) in enumerate(cmds):
    g=empty('cmd%d'%i,(AX,0,110))
    b=box((110,40,40),(0,0,0),(0.12,0.15,0.2),bevel=6); b.parent=g
    t=text(s_,16,(0,-22,0),rgb=c_); t.parent=g
    t0=T(4)+0.4+i*1.4 if i<2 else T(5)+0.2+(i-2)*1.6
    keyv(g,'location',[(0,(AX,-100,150)),(t0,(AX+60,-100,150)),(t0+1.4,(FX-60,-100,150)),(t0+1.6,(FX-60,-100,150))])
    keyv(g,'scale',[(0,(0,0,0)),(t0-0.01,(0,0,0)),(t0+0.2,(1,1,1)),(t0+1.4,(1,1,1)),(t0+1.7,(0,0,0))])
# 작업대: 스케치 → 회전 → 모서리 → STEP
WX,WY=1150,0; S=2.4
grid=empty('grid',(WX,WY,1))
for k in range(-6,7):
    l=curve_line([(k*30,-180,0),(k*30,180,0)],bevel=0.4,rgb=(0.25,0.3,0.4)); l.parent=grid
    l=curve_line([(-180,k*30,0),(180,k*30,0)],bevel=0.4,rgb=(0.25,0.3,0.4)); l.parent=grid
keyv(grid,'scale',[(0,(0,0,0)),(T(5)-0.5,(0,0,0)),(T(5)+0.2,(1,1,1))])
sk=curve_line([(r*S,0,z*S) for r,z in PUNCH],bevel=1.4,rgb=COL['white'],name='sketch'); sk.location=(WX,WY,2)
draw_on(sk,T(5)+0.3,T(5)+2.6)
dots=[]
for (r,z) in (PUNCH[1],PUNCH[-5],PUNCH[-4],PUNCH[-1]):
    d=sphere(3.5,(WX+r*S,WY,2+z*S),(0.3,1,0.4)); show(d,T(5)+2.6)
pu=revolve(PUNCH,'fcpunch',rgb=(0.72,0.74,0.80),angle=0.1); pu.scale=(S,)*3; pu.location=(WX,WY,2)
md=pu.modifiers['screw']; md.angle=math.radians(0.1); md.keyframe_insert('angle',frame=F(T(5)+3.0)); md.angle=math.radians(360); md.keyframe_insert('angle',frame=F(T(5)+5.4))
# 모서리 둥글게: 빛나는 고리
for z,r in ((0,8),(60,17.5)):
    bpy.ops.mesh.primitive_torus_add(major_radius=r*S,minor_radius=2.2,location=(WX,WY,2+z*S)); tr=bpy.context.object; paint(tr,COL['accent']); tr.select_set(False)
    keyv(tr,'scale',[(0,(0,0,0)),(T(6)+0.2,(0,0,0)),(T(6)+0.5,(1.15,1.15,1.15)),(T(6)+0.8,(1,1,1)),(T(6)+2.4,(1,1,1)),(T(6)+2.6,(0,0,0))])
# 기능 목록 (왼쪽)
tree=[('Sketch',T(5)+0.3),('Revolution',T(5)+3.0),('Fillet R7',T(6)+0.3),('Export  punch.step',T(6)+2.5)]
for i,(s_,t_) in enumerate(tree):
    o=text('▸ '+s_,18,(WX-250,WY-10,250-i*34),rgb=COL['white'] if i<3 else (0.4,1,0.5),bold=False,align='LEFT'); show(o,t_,T(8)-0.3)
# STEP 파일
stp=empty('stp',(WX+170,WY,170))
sb=box((90,10,110),(0,0,0),COL['paper'],bevel=4); sb.parent=stp
st_=text('STEP',22,(0,-8,0),rgb=COL['ink']); st_.parent=stp
keyv(stp,'scale',[(0,(0,0,0)),(T(6)+2.6,(0,0,0)),(T(6)+3.0,(1.1,1.1,1.1)),(T(6)+3.3,(1,1,1))])
# 화면 확인 (캡처 번쩍) → 고침
fl=box((400,4,320),(WX,WY-170,150),(1,1,1),name='camflash')
keyv(fl,'scale',[(0,(0,0,0)),(T(7)+0.4,(0,0,0)),(T(7)+0.5,(1,1,1)),(T(7)+0.8,(0,0,0))])
er=text('R7 → 확인',26,(WX,WY-60,330),rgb=(0.4,1,0.5)); show(er,T(7)+1.3,E(7)+0.4)
# 솔리드 단면 (반으로 잘라 보여 줌)
sol=revolve(PUNCH,'solid',rgb=(0.72,0.74,0.80),angle=180,seg=96); sol.scale=(S,)*3; sol.location=(WX,WY,2); sol.rotation_euler=(0,0,math.radians(0))
cap=bpy.data.meshes.new('cap'); bm=bmesh.new(); vs=[bm.verts.new((r,0,z)) for r,z in PUNCH]+[bm.verts.new((-r,0,z)) for r,z in reversed(PUNCH)]
bm.faces.new(vs[:-1] if False else [v for v in vs]) if False else None
bm.free()
keyv(sol,'scale',[(0,(0,0,0)),(T(8)-0.1,(0,0,0)),(T(8)+0.01,(S,S,S))])
keyv(pu,'scale',[(0,(S,S,S)),(T(8)-0.1,(S,S,S)),(T(8)+0.01,(0,0,0))])
key(sol,'rotation_euler',T(8),(0,0,0)); key(sol,'rotation_euler',E(8),(0,0,math.radians(-30)))
ts=text('솔리드: 곡면·치수가 정확',26,(WX,WY-60,330),rgb=COL['white']); show(ts,T(8)+0.4,E(8)+0.3)
# 프리캐드에서 2D·3D 도면 완성 → 3D 분해도 → 2D 도면이 조각으로 분해돼 넘어감
import random
random.seed(5)
DP=os.path.join(HERE,'도면_1_버링펀치.png'); NXT,NYT=6,4; W=300; PXc,PZc=WX-380,190
tiles=[]
for i in range(NXT):
    for j in range(NYT):
        o,tw,th=tile_plane(DP,i,j,NXT,NYT,W,(0,0,0),name='tile')
        p0=(PXc-W/2+tw*(i+0.5),WY+30,PZc-W*0.707/2+th*(j+0.5)); tiles.append((o,p0))
tp=text('2D 도면 완성 (TechDraw)',18,(PXc,WY+20,PZc+130),rgb=COL['white']); show(tp,T(8)+0.5,T(9)+0.4)
t3=text('3D 모델 완성',18,(WX,WY-20,PZc+180),rgb=COL['sky']); show(t3,T(8)+0.7,E(8))
# 3D 분해도 (끝 · 몸통 · 머리)
secs=[[(0,0),(8,0)]+arcpts(8,7,7,-90,0)[1:]+[(0,7)],[(0,7),(15,7),(15,54),(0,54)],[(0,54),(18,54),(18,59.5),(17.5,60),(0,60)]]
tX0=T(8)+2.6; tX1=E(8)-0.6
for k,sp_ in enumerate(secs):
    o=revolve(sp_,'sec%d'%k,rgb=(0.72,0.74,0.80)); o.scale=(S,)*3
    dz=(-45,0,45)[k]
    keyv(o,'location',[(0,(WX,WY,2)),(tX0+0.3,(WX,WY,2)),(tX0+0.9,(WX,WY,2+dz)),(tX1-0.5,(WX,WY,2+dz)),(tX1,(WX,WY,2))])
    keyv(o,'scale',[(0,(0,0,0)),(tX0,(0,0,0)),(tX0+0.01,(S,S,S)),(tX1,(S,S,S)),(tX1+0.01,(0,0,0))])
keyv(sol,'scale',[(tX0,(S,S,S)),(tX0+0.01,(0,0,0)),(tX1,(0,0,0)),(tX1+0.01,(S,S,S))])
tx=text('분해도',22,(WX+140,WY-20,PZc+40),rgb=COL['accent']); show(tx,tX0+0.6,tX1-0.3)
# 다른 프로그램으로 넘기기
for i,(nm,c_) in enumerate((('CATIA',(0.25,0.55,0.95)),('PowerMill',(0.95,0.45,0.25)))):
    x=WX+360+i*240
    b=box((190,120,90),(x,0,50),c_,bevel=10); show(b,T(9)+0.2+i*0.3)
    t=text(nm,24,(x,-62,55),rgb=COL['white']); show(t,T(9)+0.3+i*0.3)
for n_,(o,p0) in enumerate(tiles):
    p1=(p0[0]+random.uniform(-50,50),WY-random.uniform(40,160),p0[2]+random.uniform(-50,80))
    dst=(WX+360+240*(n_%2),0,90)
    tb=T(9)+0.4; tf=tb+0.7+n_*0.05
    keyv(o,'location',[(0,p0),(tb,p0),(tb+0.5,p1),(tf,p1),(tf+0.6,dst)])
    keyv(o,'rotation_euler',[(0,(math.radians(90),0,0)),(tb,(math.radians(90),0,0)),(tb+0.5,(math.radians(90)+random.uniform(-0.8,0.8),random.uniform(-0.5,0.5),random.uniform(-0.6,0.6))),(tf+0.6,(math.radians(90),0,0))])
    keyv(o,'scale',[(0,(0,0,0)),(T(8)+0.3,(0,0,0)),(T(8)+0.6,(1,1,1)),(tf+0.45,(1,1,1)),(tf+0.6,(0,0,0))])
keyv(stp,'location',[(T(9)+0.6,(WX+170,WY,170)),(T(9)+2.0,(WX+360,0,165)),(T(9)+2.2,(WX+360,0,160))])
s2=empty('stp2',(WX+170,WY,170)); b2=box((90,10,110),(0,0,0),COL['paper'],bevel=4); b2.parent=s2; t2=text('STEP',22,(0,-8,0),rgb=COL['ink']); t2.parent=s2
keyv(s2,'scale',[(0,(0,0,0)),(T(9)+0.9,(0,0,0)),(T(9)+1.0,(1,1,1))])
keyv(s2,'location',[(T(9)+1.0,(WX+170,WY,170)),(T(9)+2.6,(WX+600,0,160))])
# 카메라
cam,tgt=camera(35)
cam_keys(cam,tgt,[(0,(0,-1500,700),(0,0,110)),(T(1)+2,(0,-1250,420),(0,0,120)),(T(2)+0.3,(-80,-900,340),(0,0,130))])
cam_keys(cam,tgt,[(T(3)+1.0,(0,-640,260),(60,0,130)),(T(3)+2.6,(60,-560,230),(80,0,120)),(E(3),(40,-900,380),(0,0,130))])
cam_keys(cam,tgt,[(T(4)+0.8,(0,-1300,520),(0,-100,140)),(E(4),(80,-1300,520),(80,-100,140))])
cam_keys(cam,tgt,[(T(5)+0.6,(WX-60,WY-700,420),(WX,WY,120)),(E(5),(WX+40,WY-660,360),(WX,WY,130))])
orbit(cam,tgt,E(5),E(6),(WX,WY,130),660,230,-95,-60,n=6)
cam_keys(cam,tgt,[(T(7)+0.4,(WX,WY-600,260),(WX,WY,150)),(E(7),(WX-40,WY-580,240),(WX,WY,150))])
cam_keys(cam,tgt,[(T(8)+0.6,(WX-180,WY-900,300),(WX-180,WY,170)),(E(8),(WX-150,WY-880,290),(WX-170,WY,170))])
cam_keys(cam,tgt,[(T(9)+0.8,(WX+250,WY-1050,420),(WX+300,WY,110)),(DUR,(WX+280,WY-1100,440),(WX+300,WY,110))])
handheld(cam,0.5)
finish('ch3',DUR)
