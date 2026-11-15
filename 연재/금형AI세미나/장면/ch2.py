import sys,os; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from s3d import *
T,E,DUR,cs=chapter(2)
sc=setup(texture=True)
floor(extent=2600)
S=3.0
# 도면 (바닥에 비스듬히 누움)
dw=image_plane(os.path.join(HERE,'도면_1_버링펀치.png'),520,(0,120,1),rot=(0,0,0),name='dwg')
# 반쪽 단면 선 (노랑) — 도면 위에서 일어남
prof=empty('profG',(0,0,0))
pts=[(r*S,0,z*S) for r,z in PUNCH]
ln=curve_line(pts,bevel=1.6,rgb=COL['accent'],name='prof'); ln.parent=prof
ax=curve_line([(0,0,-40),(0,0,60*S+40)],bevel=0.9,rgb=COL['red'],name='axis'); ax.parent=prof
key(prof,'rotation_euler',0,(math.radians(-90),0,0)); key(prof,'location',0,(0,40,2))
key(prof,'rotation_euler',T(1)+0.3,(math.radians(-90),0,0)); key(prof,'location',T(1)+0.3,(0,40,2))
key(prof,'rotation_euler',T(2)+1.5,(0,0,0)); key(prof,'location',T(2)+1.5,(0,0,0))
keyv(prof,'scale',[(0,(1,1,1)),(T(4)+2,(1,1,1)),(T(4)+2.4,(0,0,0))])
t1=text('반쪽 단면',22,(-170,0,200),rgb=COL['accent']); show(t1,T(2)+0.8,E(2)+1)
t2=text('회전 축',18,(60,0,-28),rgb=COL['red']); show(t2,T(2)+1.5,E(3))
# 회전체 (Screw 각도 0 → 360)
pu=revolve(PUNCH,'punch',rgb=(0.80,0.82,0.86),angle=0.1); pu.scale=(S,)*3
md=pu.modifiers['screw']
md.angle=math.radians(0.1); md.keyframe_insert('angle',frame=F(T(3)))
md.angle=math.radians(360); md.keyframe_insert('angle',frame=F(T(3)+4.5))
key(dw,'location',T(3),(0,120,1)); key(dw,'location',T(4)+1,(0,900,-10))
t3=text('회전 = 리볼브 (Revolve)',30,(0,-60,250),rgb=COL['white']); show(t3,T(4)+0.2,E(4)+0.5)
# 파란색 입히기
m=pu.data.materials[0]
m.diffuse_color=(0.80,0.82,0.86,1); m.keyframe_insert('diffuse_color',frame=F(T(6)+3.0))
m.diffuse_color=(*COL['punch'],1); m.keyframe_insert('diffuse_color',frame=F(T(6)+4.0))
# 도면 → 조각 → AI → 코드 → 2D 캐드 → 3D (블렌더 + 파이썬)
import random
random.seed(11)
PX=-1400; tA=T(5)+1.2
core=empty('core',(PX,0,200))
cs_=sphere(55,(0,0,0),COL['sky']); cs_.parent=core
for k,ang in enumerate((0,60,120)):
    bpy.ops.mesh.primitive_torus_add(major_radius=85,minor_radius=2.5,location=(0,0,0),rotation=(math.radians(90),math.radians(ang),0)); tr=bpy.context.object; paint(tr,COL['accent']); tr.parent=core; tr.select_set(False)
ct=text('AI',40,(0,-58,0),rgb=COL['ink']); ct.parent=core
spin(core,0,DUR,turns=3)
keyv(core,'scale',[(0,(0,0,0)),(T(5)+0.2,(0,0,0)),(T(5)+0.6,(1.1,1.1,1.1)),(T(5)+0.8,(1,1,1)),(E(6)-1.0,(1,1,1)),(E(6)-0.6,(0,0,0))])
DP=os.path.join(HERE,'도면_1_버링펀치.png'); NXT,NYT=6,4; W=360; DXP=PX-470
for i in range(NXT):
    for j in range(NYT):
        o,tw,th=tile_plane(DP,i,j,NXT,NYT,W,(0,0,0),name='tile')
        p0=(DXP-W/2+tw*(i+0.5),0,200-W*0.707/2+th*(j+0.5))
        p1=(p0[0]+random.uniform(-60,60),random.uniform(-160,-40),p0[2]+random.uniform(-60,60))
        tg=tA+0.9+(i*NYT+j)*0.05
        keyv(o,'location',[(0,p0),(tA,p0),(tA+0.6,p1),(tg,p1),(tg+0.6,(PX,0,200))])
        keyv(o,'rotation_euler',[(0,(math.radians(90),0,0)),(tA,(math.radians(90),0,0)),(tA+0.6,(math.radians(90)+random.uniform(-0.7,0.7),random.uniform(-0.5,0.5),random.uniform(-0.6,0.6))),(tg+0.6,(math.radians(90),0,0))])
        keyv(o,'scale',[(0,(0,0,0)),(T(5)+0.1,(0,0,0)),(T(5)+0.4,(1,1,1)),(tg+0.45,(1,1,1)),(tg+0.6,(0,0,0))])
tl=text('2D 도면',26,(DXP,-60,350),rgb=COL['white']); show(tl,T(5)+0.4,tA+1.5)
# 코드 블록이 쏟아져 나와 벽으로
src=['import bpy','prof = read_dxf("punch.dxf")','pts = [(0,0),(8,0),...]','obj = make_profile(pts)','scr = obj.modifiers.new("SCREW")','scr.angle = radians(360)','obj.color = BLUE','save("punch.blend")']
CW=PX+420; tC=tA+2.6
cb=[]
for i,s_ in enumerate(src):
    g=empty('code%d'%i,(PX,0,200)); b=box((230,6,26),(0,0,0),(0.08,0.10,0.14),bevel=2); b.parent=g
    tx=text(s_,11,(0,-4,0),rgb=(0.45,1,0.55) if i==0 else COL['white'],bold=False); tx.parent=g
    tt=tC+i*0.22; dest=(CW,-20,300-i*34)
    keyv(g,'location',[(0,(PX,0,200)),(tt,(PX,0,200)),(tt+0.55,dest)])
    keyv(g,'scale',[(0,(0,0,0)),(tt-0.01,(0,0,0)),(tt+0.2,(1,1,1))])
    cb.append((g,dest))
tcd=text('AI 가 쓴 파이썬 코드',24,(CW,-60,350),rgb=COL['accent']); show(tcd,tC+0.3,T(6)+2.0)
# 코드 → 2D 캐드 선 (모눈 위) → 3D
CX2=PX+880; S2=2.6; tD=T(6)+0.9
for g,dest in cb:
    keyv(g,'location',[(tD,dest),(tD+0.7,(CX2,0,120))]); keyv(g,'scale',[(tD+0.45,(1,1,1)),(tD+0.7,(0,0,0))])
grid=empty('grid2',(CX2,0,40))
for k in range(-5,6):
    l=curve_line([(k*20,0,0),(k*20,0,200)],bevel=0.35,rgb=(0.25,0.3,0.4)); l.parent=grid
for k in range(0,11):
    l=curve_line([(-100,0,k*20),(100,0,k*20)],bevel=0.35,rgb=(0.25,0.3,0.4)); l.parent=grid
grid.location=(CX2,30,40)
keyv(grid,'scale',[(0,(0,0,0)),(tD-0.3,(0,0,0)),(tD,(1,1,1)),(T(6)+3.6,(1,1,1)),(T(6)+4.0,(0,0,0))])
cad=curve_line([(CX2+r*S2,0,40+z*S2) for r,z in PUNCH],bevel=1.4,rgb=COL['accent'],name='cad2'); draw_on(cad,tD+0.5,tD+1.8)
cax=curve_line([(CX2,0,20),(CX2,0,40+60*S2+20)],bevel=0.7,rgb=COL['red']); show(cax,tD+0.4,T(6)+4.2)
t2d=text('2D 캐드 도면',24,(CX2,-60,250),rgb=COL['white']); show(t2d,tD+0.6,tD+2.6)
p3=revolve(PUNCH,'p3d',rgb=COL['punch'],angle=0.1,loc=(CX2,0,40)); p3.scale=(S2,)*3
m3=p3.modifiers['screw']; m3.angle=math.radians(0.1); m3.keyframe_insert('angle',frame=F(tD+2.0)); m3.angle=math.radians(360); m3.keyframe_insert('angle',frame=F(tD+3.4))
keyv(p3,'scale',[(0,(0,0,0)),(tD+1.95,(0,0,0)),(tD+2.0,(S2,S2,S2))])
t3d=text('3D 모델',30,(CX2,-60,250),rgb=COL['sky']); show(t3d,tD+3.0,E(6)+0.3)
spin(p3,tD+3.4,E(6)+1,turns=0.5)
# 다이(초록) · 판재(주황) 등장
die=revolve(DIE_P,'die',rgb=COL['die'],angle=270); die.scale=(S,)*3; die.rotation_euler=(0,0,math.radians(-45))
sheet,sk=burr_sheet(Ro=40,Rh=12.6,scale=S); cut(sheet,270); sheet.rotation_euler=(0,0,math.radians(-45))
keyk(sk,[(0,1)])
key(pu,'location',0,(0,0,0)); key(pu,'location',T(7)-0.2,(0,0,0)); key(pu,'location',T(7)+1.2,(0,0,30*S+0.6*S-5.6*S+60))
ztop=30*S+0.6*S
keyv(die,'location',[(0,(0,0,-400)),(T(7)+0.3,(0,0,-400)),(T(7)+1.6,(0,0,0))])
keyv(sheet,'location',[(0,(0,0,-400)),(T(7)+1.2,(0,0,-400)),(T(7)+2.4,(0,0,ztop))])
for s_,p_,c_,tt in (('상형 펀치',(-260,0,ztop+150),COL['sky'],T(7)+0.3),('하형 다이',(-260,0,50),COL['die'],T(7)+2.0),('판재',(-260,0,ztop+10),COL['sheet'],T(7)+3.6)):
    o=text(s_,24,p_,rgb=c_); show(o,tt,E(7)+0.3)
# 금형 세트 (오른쪽) — 위에서 차례로 떨어져 조립
DXS=1500
parts,up,root=die_set((DXS,0,145),wire=True)
order=sorted(parts,key=lambda pg:min((pg[0].matrix_world@v.co).z for v in pg[0].data.vertices[:200]) if pg[0].data.vertices else 0)
order=sorted(parts,key=lambda pg:pg[0].location.z+sum(v.co.z for v in pg[0].data.vertices[:60])/60)
n=len(order); ta=T(8)+0.6; tb=E(8)-0.6
for i,(o,g) in enumerate(order):
    t=ta+(tb-ta)*i/n
    key(o,'location',0,(0,0,700)); key(o,'location',t,(0,0,700)); key(o,'location',t+0.55,(0,0,-4)); key(o,'location',t+0.75,(0,0,0))
# 열기 (상형 크게 들어 올림) → 카메라가 금형 안으로 들어가 버링 스테이션 둘레를 돎
LIFT=140; ZG=145
keyv(up,'location',[(0,(0,0,0)),(T(9)-0.2,(0,0,0)),(T(9)+1.2,(0,0,LIFT))])
SXc=DXS-108; ZC=ZG+38      # 버링 스테이션 중심 (스트립 위, 매달린 펀치 아래)
# 보기 바꾸기: 솔리드 → 와이어 → 엑스레이 (보여 주고 확인하는 용도)
tv=T(10)
view_modes(parts,[(0,'solid'),(tv+2.0,'wire'),(tv+4.6,'xray')])
keyv(up,'location',[(E(9)-0.2,(0,0,LIFT)),(tv+1.4,(0,0,40))])
md_=text(' ',40,(DXS,-200,420),rgb=COL['accent']); text_seq(md_,[(0,' '),(tv+0.5,'솔리드'),(tv+2.0,'와이어'),(tv+4.6,'엑스레이')])
tm=text('메쉬 = 작은 삼각형 면의 모음 · 보여 주기 · 확인용',24,(DXS,-200,370),rgb=COL['white']); show(tm,tv+0.6)
# 카메라
cam,tgt=camera(35)
cam_keys(cam,tgt,[(0,(0,-420,520),(0,60,0)),(T(2)-0.2,(0,-420,460),(0,40,40)),(T(2)+1.6,(-200,-560,240),(0,0,90))])
orbit(cam,tgt,T(3),T(4)+3,(0,0,90),560,150,-110,-40,n=8)
cam_keys(cam,tgt,[(T(5)+0.9,(DXP+120,-1000,320),(DXP+250,0,210)),(tA+1.6,(PX-100,-900,300),(PX,0,210)),(tC+1.5,(PX+200,-950,300),(PX+250,0,220)),(tD+0.8,(CX2-150,-800,260),(CX2-60,0,170)),(tD+3.4,(CX2+20,-620,230),(CX2,0,130)),(E(6),(CX2+80,-600,220),(CX2,0,130))])
cam_keys(cam,tgt,[(T(7)+1.2,(-120,-640,330),(-60,0,150)),(E(7),(-60,-600,300),(-40,0,150))])
cam_keys(cam,tgt,[(T(8)+0.8,(DXS-200,-1300,700),(DXS,0,140)),(E(8)-0.3,(DXS+250,-1150,520),(DXS,0,150))])
cam_keys(cam,tgt,[(T(9)+1.0,(SXc-60,-520,ZC+40),(SXc,0,ZC)),(T(9)+2.2,(SXc,-95,ZC+8),(SXc,0,ZC),None)])
cam.data.lens=35; cam.data.keyframe_insert('lens',frame=F(T(9)+1.0)); cam.data.lens=18; cam.data.keyframe_insert('lens',frame=F(T(9)+2.2))
orbit(cam,tgt,T(9)+2.2,E(9)-0.2,(SXc,0,ZC),95,8,-90,270,n=16)
cam.data.keyframe_insert('lens',frame=F(E(9)-0.2)); cam.data.lens=35; cam.data.keyframe_insert('lens',frame=F(T(10)+0.8))
cam_keys(cam,tgt,[(T(10)+0.9,(DXS-500,-1050,520),(DXS,0,190))])
orbit(cam,tgt,T(10)+0.9,DUR,(DXS,0,190),1150,380,-115,-60,n=10)
sfx(tA,'whoosh',0.9); sfx(tC,'whoosh',0.6); sfx(tD,'whoosh',0.6); sfx(tD+2.0,'whoosh',0.5)
for k_,(o_,g_) in enumerate(order):
    if k_%9==0: sfx(ta+(tb-ta)*k_/n+0.5,'click',0.5)
sfx(T(9)+1.0,'whoosh',1.0); sfx(E(9)-0.2,'whoosh',0.8); sfx(tv+2.0,'pop',0.7); sfx(tv+4.6,'pop',0.7)
handheld(cam,0.5)
finish('ch2',DUR)
