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
# 파이썬 창
code=empty('codeG',(-420,0,170))
cp=panel(380,300,(0,25,0),rgb=(0.07,0.08,0.11),name='codep'); cp.parent=code
hd=text('Blender + Python',22,(-170,15,120),rgb=COL['accent'],align='LEFT'); hd.parent=code
src=['import bpy','prof = read_dxf("punch.dxf")','obj = make_profile(prof)','scr = obj.modifiers.new("SCREW")','scr.angle = radians(360)','obj.color = BLUE']
for i,l in enumerate(src):
    o=text(' ',16,(-170,15,70-i*32),rgb=(0.55,0.95,0.6) if i==0 else COL['white'],bold=False,align='LEFT'); o.parent=code
    a_=T(5)+1.0+i*0.9; typewriter(o,l,a_,a_+0.8)
keyv(code,'scale',[(0,(0,0,0)),(T(5)+0.2,(0,0,0)),(T(5)+0.6,(1.05,1.05,1.05)),(T(5)+0.9,(1,1,1)),(E(6),(1,1,1)),(E(6)+0.4,(0,0,0))])
# 다이(초록) · 판재(주황) 등장
die=revolve(DIE_P,'die',rgb=COL['die'],angle=270); die.scale=(S,)*3; die.rotation_euler=(0,0,math.radians(-45))
sheet,sk=burr_sheet(Ro=40,Rh=12.6,scale=S); sheet.modifiers['screw'].angle=math.radians(270); sheet.rotation_euler=(0,0,math.radians(-45))
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
cam_keys(cam,tgt,[(T(5)+0.8,(-200,-760,260),(-200,0,140)),(E(6)-0.5,(-150,-720,250),(-150,0,140))])
cam_keys(cam,tgt,[(T(7)+1.2,(-120,-640,330),(-60,0,150)),(E(7),(-60,-600,300),(-40,0,150))])
cam_keys(cam,tgt,[(T(8)+0.8,(DXS-200,-1300,700),(DXS,0,140)),(E(8)-0.3,(DXS+250,-1150,520),(DXS,0,150))])
cam_keys(cam,tgt,[(T(9)+1.0,(SXc-60,-520,ZC+40),(SXc,0,ZC)),(T(9)+2.2,(SXc,-95,ZC+8),(SXc,0,ZC),None)])
cam.data.lens=35; cam.data.keyframe_insert('lens',frame=F(T(9)+1.0)); cam.data.lens=18; cam.data.keyframe_insert('lens',frame=F(T(9)+2.2))
orbit(cam,tgt,T(9)+2.2,E(9)-0.2,(SXc,0,ZC),95,8,-90,270,n=16)
cam.data.keyframe_insert('lens',frame=F(E(9)-0.2)); cam.data.lens=35; cam.data.keyframe_insert('lens',frame=F(T(10)+0.8))
cam_keys(cam,tgt,[(T(10)+0.9,(DXS-500,-1050,520),(DXS,0,190))])
orbit(cam,tgt,T(10)+0.9,DUR,(DXS,0,190),1150,380,-115,-60,n=10)
handheld(cam,0.5)
finish('ch2',DUR)
