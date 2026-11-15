import sys,os; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from s3d import *
T,E,DUR,cs=chapter(8)
sc=setup(texture=True)
floor(extent=2600)
ST=[('프롬프트','2D 도면'),('블렌더','3D 모델'),('프리캐드','MCP'),('부품 도면','PDF'),('성형해석',''),('역설계',''),('가공','')]
X0,DX=-900,300
xs=[X0+i*DX for i in range(7)]
lit=[T(2)+0.3,T(2)+2.4,T(2)+3.6,T(3)+0.4,T(3)+2.6,T(4)+0.3,T(4)+1.6]
for i,(a,b) in enumerate(ST):
    x=xs[i]; pedestal((x,0,0),r=95,h=10)
    lamp=cyl(70,6,(x,0,13),COL['accent'],seg=64); keyv(lamp,'scale',[(0,(0,0,1)),(lit[i],(0,0,1)),(lit[i]+0.3,(1.1,1.1,1)),(lit[i]+0.5,(1,1,1))])
    t=text(a,24,(x,-30,190)); t2=text(b,18,(x,-30,160),rgb=COL['accent']) if b else None
    n=text(str(i+1),30,(x,-30,230),rgb=COL['accent'])
# 각 단계 작은 모형
p=revolve(PUNCH,'p',rgb=COL['punch'],loc=(xs[1],0,16)); p.scale=(1.6,)*3; spin(p,0,DUR,0.6)
image_plane(os.path.join(HERE,'도면_1_버링펀치.png'),120,(xs[0],20,75),rot=(math.radians(75),0,0))
box((60,30,30),(xs[2]-45,0,45),COL['sky'],bevel=4); box((60,30,30),(xs[2]+45,0,45),COL['purple'],bevel=4)
for k in range(3): image_plane(os.path.join(HERE,['도면_1_버링펀치','도면_2_버링다이','도면_3_펀치고정판'][k]+'.png'),110,(xs[3]-15+k*12,k*10,80+k*3),rot=(math.radians(80),0,0))
for k,(rr,c_) in enumerate([(70,(0.1,0.2,0.75)),(52,(0.2,0.7,0.9)),(36,(1,0.85,0.2)),(22,(0.95,0.25,0.15))]): cyl(rr,3+k*2,(xs[4],0,16+k),c_,name='fem')
s2=loop_obj(seal_profile(),'seal',COL['sheet'],angle=360,seg=96,loc=(xs[5],0,60),scale=2.2); spin(s2,0,DUR,0.5)
cyl(12,80,(xs[6],0,95),COL['post']); cyl(4,30,(xs[6],0,45),COL['white']); box((140,90,24),(xs[6],0,28),COL['plate'],bevel=2)
# 사람이 마지막 확인
hm=text('반복은 AI · 마지막 확인은 사람',40,(2000,-300,640),rgb=COL['white']); show(hm,T(5)+0.5,E(5)+0.4)
okk=text('OK',80,(2000,-300,565),rgb=(0.4,1,0.5)); show(okk,T(5)+2.8,E(5)+0.4)
# 마지막: 금형 세트
DXS=2000
parts,up,root=die_set((DXS,0,145))
# 가공을 마친 부품이 금형에 장착됨 (다이 → 펀치 차례)
tM0=T(4)+2.8; tM1=E(5)-0.1
keyv(up,'location',[(0,(0,0,260)),(tM1-0.2,(0,0,260)),(T(10)+0.3,(0,0,140)),(T(11)+0.6,(0,0,140)),(DUR-1.2,(0,0,0))])
dies=[o for o,g in parts if g=='lower' and (o.name.endswith('_die') or '_die_' in o.name or o.name.endswith('_pad'))]
puns=[o for o,g in parts if g=='upper' and ('_punch' in o.name or 'pilot_pierce' in o.name)]
dies.sort(key=lambda o:o.name); puns.sort(key=lambda o:o.name)
nd=len(dies); npn=len(puns); half=tM0+(tM1-tM0)*0.48
for i,o in enumerate(dies):
    t0=tM0+(half-tM0)*i/nd
    keyv(o,'scale',[(0,(0,0,0)),(t0,(0,0,0)),(t0+0.25,(1,1,1))])
    keyv(o,'location',[(0,(0,0,190)),(t0+0.25,(0,0,190)),(t0+0.85,(0,0,-2)),(t0+1.0,(0,0,0))])
for i,o in enumerate(puns):
    t0=half+(tM1-half-1.0)*i/npn
    keyv(o,'scale',[(0,(0,0,0)),(t0,(0,0,0)),(t0+0.25,(1,1,1))])
    keyv(o,'location',[(0,(0,0,-170)),(t0+0.25,(0,0,-170)),(t0+0.85,(0,0,2)),(t0+1.0,(0,0,0))])
strips=[o for o,g in parts if g=='strip']
for o in strips:
    keyv(o,'location',[(0,(-760,0,0)),(tM1-1.2,(-760,0,0)),(tM1+0.2,(0,0,0))])
mt=text('가공을 마친 부품 → 금형에 장착',40,(2000,-300,640),rgb=COL['white']); show(mt,tM0+0.2,T(5)+0.2)
SXc=DXS; ZC=145+38
ti=text('AI로 금형 만들기',64,(DXS,-150,480),rgb=COL['accent']); show(ti,T(11)+0.6)
ty=text('들어 주셔서 감사합니다',40,(DXS,-150,410),rgb=COL['white']); show(ty,T(11)+0.9)
# 카메라: 받침대 따라 → 금형 세트
cam,tgt=camera(35)
cam_keys(cam,tgt,[(0,(0,-2000,1100),(0,0,80)),(T(2)-0.3,(xs[0]-200,-700,420),(xs[0],0,100))])
for i in range(7):
    cam_keys(cam,tgt,[(lit[i]+0.15,(xs[i]+80,-560,300),(xs[i],0,100))])
    if i: sfx(lit[i]-0.3,'whoosh',0.8)
    nxt=lit[i+1]-0.3 if i<6 else lit[i]+1.0
    if nxt>lit[i]+0.4: cam_keys(cam,tgt,[(nxt,(xs[i]+115,-520,285),(xs[i]+12,0,100))])
cam_keys(cam,tgt,[(tM0+0.6,(DXS-350,-1500,520),(DXS,0,320)),(half,(DXS-150,-1400,470),(DXS,0,310)),(tM1,(DXS+200,-1450,520),(DXS,0,330)),(E(5),(DXS+120,-1500,600),(DXS,0,380))])
cam_keys(cam,tgt,[(T(10)+0.3,(SXc-80,-560,ZC+60),(SXc,0,ZC)),(T(10)+1.2,(SXc,-95,ZC+8),(SXc,0,ZC))])
cam.data.lens=35; cam.data.keyframe_insert('lens',frame=F(T(10)+0.3)); cam.data.lens=18; cam.data.keyframe_insert('lens',frame=F(T(10)+1.2))
orbit(cam,tgt,T(10)+1.2,T(11)-0.1,(SXc,0,ZC),95,8,-90,190,n=12)
cam.data.keyframe_insert('lens',frame=F(T(11)-0.1))
cam_keys(cam,tgt,[(T(11)+0.4,(SXc-200,-420,ZC+30),(SXc,0,ZC+20))])
cam.data.lens=35; cam.data.keyframe_insert('lens',frame=F(T(11)+0.9))
cam_keys(cam,tgt,[(T(11)+1.8,(DXS-280,-1250,560),(DXS,0,230)),(DUR,(DXS-200,-1300,600),(DXS,0,230))])
sfx(tM0-0.5,'whoosh',1.0)
for i_,o_ in enumerate(dies): sfx(tM0+(half-tM0)*i_/nd+0.85,'click',0.5)
for i_,o_ in enumerate(puns): sfx(half+(tM1-half-1.0)*i_/npn+0.85,'click',0.6)
sfx(T(10)+0.3,'whoosh',1.0); sfx(T(11)-0.1,'whoosh',0.9); sfx(DUR-1.3,'click',1.0)
# 문서 작성 = 낭비 (새 6번 문장)
WX0=3600-700
for i in range(14):
    pg=box((110,80,6),(0,0,0),COL['paper'],bevel=2,name='doc')
    t0=T(6)+0.2+i*0.22; z=10+i*9
    keyv(pg,'location',[(0,(WX0+i%2*8,0,420)),(t0,(WX0+i%2*8,0,420)),(t0+0.35,(WX0+(i%3)*6-6,0,z))])
    keyv(pg,'scale',[(0,(0,0,0)),(t0-0.05,(0,0,0)),(t0+0.05,(1,1,1)),(E(6)+0.2,(1,1,1)),(E(6)+0.5,(0,0,0))])
ck=empty('wclock',(WX0+170,-40,240)); cf2=cyl(45,8,(0,0,0),COL['white'],seg=48,rot=(math.radians(90),0,0)); cf2.parent=ck
hp2=empty('hp2',(0,-8,0)); hp2.parent=ck; hd2=box((5,4,36),(0,0,16),COL['ink']); hd2.parent=hp2
keyv(ck,'scale',[(0,(0,0,0)),(T(6),(0,0,0)),(T(6)+0.3,(1,1,1)),(E(6)+0.2,(1,1,1)),(E(6)+0.5,(0,0,0))])
keyv(hp2,'rotation_euler',[(T(6),(0,0,0)),(E(6),(0,math.radians(1080),0))])
dt=text('문서 작성에 쓰는 시간',26,(WX0,-80,330),rgb=COL['white']); show(dt,T(6)+0.3,E(6)+0.3)
ws=text('낭비',90,(WX0,-90,170),rot=(math.radians(90),math.radians(-12),0),rgb=COL['red'])
tW=T(6)+2.6; keyv(ws,'scale',[(0,(0,0,0)),(tW-0.05,(0,0,0)),(tW,(2.2,2.2,2.2)),(tW+0.18,(1,1,1)),(E(6)+0.3,(1,1,1)),(E(6)+0.5,(0,0,0))]); sfx(tW+0.15,'click',1.2)
cam_keys(cam,tgt,[(T(6)+0.5,(WX0-60,-800,320),(WX0+40,0,180)),(E(6),(WX0+20,-760,300),(WX0+60,0,180))])
sfx(T(6)+0.1,'whoosh',0.9)
# 관리 기법의 전환: AI 비서가 표준대로 생성 → 관리자는 체크 → 아낀 시간으로 현장 실무 관리
MG=3600
def person(loc,col=(0.62,0.42,0.95)):
    g=empty('person',loc)
    b=cyl(22,90,(0,0,45),col,seg=24); b.parent=g
    h=sphere(20,(0,0,112),(0.95,0.82,0.70)); h.parent=g
    for sx in (-1,1):
        a=box((10,10,60),(sx*28,0,60),col); a.parent=g
    return g
tt=text('관리 기법의 전환',44,(MG,-150,470),rgb=COL['accent']); show(tt,T(7)+0.1)
o1=text('기존: 관리자가 직접 작성',22,(MG-380,-150,415),rgb=(0.85,0.55,0.5)); show(o1,T(7)+0.5,E(9))
o2=text('AI 비서가 표준대로 생성 · 관리자는 체크',22,(MG+330,-150,415),rgb=(0.4,1,0.5)); show(o2,T(7)+1.4,E(9))
ar_=curve_line([(MG-170,-150,415),(MG+40,-150,415)],bevel=3,rgb=COL['accent']); show(ar_,T(7)+1.0,E(9))
# 표준 책 → AI 비서 → 카드들
std=empty('std',(MG-520,0,200)); sb=box((70,90,100),(0,0,0),(0.85,0.75,0.40),bevel=4); sb.parent=std; stx=text('표준',22,(0,-48,0),rgb=COL['ink']); stx.parent=std
keyv(std,'scale',[(0,(0,0,0)),(T(8)-0.4,(0,0,0)),(T(8)-0.1,(1,1,1))])
keyv(std,'location',[(T(8)+0.1,(MG-520,0,200)),(T(8)+0.9,(MG-260,0,220))]); keyv(std,'scale',[(T(8)+0.7,(1,1,1)),(T(8)+0.9,(0,0,0))])
ai=empty('ai',(MG-260,0,220)); asp=sphere(55,(0,0,0),COL['sky']); asp.parent=ai
bpy.ops.mesh.primitive_torus_add(major_radius=80,minor_radius=3,location=(0,0,0),rotation=(math.radians(90),0,0)); tr_=bpy.context.object; paint(tr_,COL['accent']); tr_.parent=ai; tr_.select_set(False)
atx=text('AI 비서',20,(0,-58,0),rgb=COL['ink']); atx.parent=ai
keyv(ai,'scale',[(0,(0,0,0)),(T(7)+1.6,(0,0,0)),(T(7)+2.0,(1,1,1))]); spin(ai,0,DUR,turns=2)
mgr=person((MG+300,0,0)); keyv(mgr,'scale',[(0,(0,0,0)),(T(8)-0.4,(0,0,0)),(T(8)-0.1,(1,1,1))])
clip=box((60,8,80),(MG+260,-40,95),COL['paper'],bevel=3); show(clip,T(8)-0.1)
ctx=text('점검표',12,(MG+260,-45,120),rgb=COL['ink']); show(ctx,T(8))
cards=[('도면',COL['white']),('PDF',(0.9,0.25,0.22)),('NC',(0.4,1,0.5)),('STEP',(0.35,0.62,1.0))]
for i,(nm,col) in enumerate(cards):
    g=empty('card%d'%i,(MG-260,0,220)); b=box((90,8,60),(0,0,0),(0.10,0.13,0.18),bevel=3); b.parent=g; tx=text(nm,18,(0,-6,6),rgb=col); tx.parent=g
    t0=T(8)+1.0+i*0.7; dst=(MG+40+i*0,-60,330-i*70)
    keyv(g,'scale',[(0,(0,0,0)),(t0-0.05,(0,0,0)),(t0+0.15,(1,1,1))])
    keyv(g,'location',[(0,(MG-260,0,220)),(t0,(MG-260,0,220)),(t0+0.6,dst)])
    ok=text('OK',16,(dst[0]+60,-70,dst[2]),rgb=(0.4,1,0.5)); show(ok,t0+0.9); sfx(t0+0.9,'pop',0.6)
# 아낀 시간 → 현장
FAC=MG+900
fb=box((340,220,170),(FAC,60,85),(0.42,0.46,0.52),bevel=4); show(fb,T(9)-0.3)
for k in range(4):
    r_=box((85,230,40),(FAC-128+k*85,60,190),(0.55,0.58,0.64)); r_.rotation_euler=(0,math.radians(-25),0); show(r_,T(9)-0.2)
ftx=text('현장',36,(FAC,-52,95),rgb=COL['ink']); show(ftx,T(9))
clk=empty('clock',(MG+520,-60,400)); cf=cyl(55,8,(0,0,0),COL['white'],seg=48,rot=(math.radians(90),0,0)); cf.parent=clk
hand=box((6,4,45),(0,-8,20),COL['ink']); hp=empty('hp',(0,-8,0)); hp.parent=clk; hand.parent=hp; hand.location=(0,0,20)
keyv(clk,'scale',[(0,(0,0,0)),(T(9)-0.2,(0,0,0)),(T(9)+0.1,(1,1,1))])
keyv(hp,'rotation_euler',[(T(9),(0,0,0)),(E(9),(0,math.radians(720),0))])
for i in range(6):
    tb_=box((26,26,26),(0,0,0),COL['accent'],bevel=3,name='tblk')
    t0=T(9)+0.6+i*0.35
    keyv(tb_,'location',[(0,(MG+520,-60,330)),(t0,(MG+520,-60,330)),(t0+0.9,(FAC-120+i*45,-80,40))])
    keyv(tb_,'scale',[(0,(0,0,0)),(t0-0.05,(0,0,0)),(t0+0.1,(1,1,1))])
st=text('절약된 시간',24,(MG+520,-70,480),rgb=COL['accent']); show(st,T(9)+0.3,E(9)+0.3)
keyv(mgr,'location',[(T(9)+1.4,(MG+300,0,0)),(E(9)-0.3,(FAC-60,-160,0))])
fs=text('현장 실무 관리 강화',34,(FAC,-150,330),rgb=(0.4,1,0.5)); show(fs,T(9)+2.0,E(9)+0.3)
cam_keys(cam,tgt,[(T(7)+0.5,(MG,-1550,460),(MG,0,300)),(E(7),(MG-40,-1500,440),(MG-20,0,290)),(T(8)+0.6,(MG,-1450,420),(MG,0,270)),(E(8),(MG+80,-1450,420),(MG+60,0,270)),(T(9)+0.8,(MG+560,-1350,420),(MG+600,0,230)),(E(9),(FAC-150,-1250,400),(FAC-150,0,200))])
sfx(T(7)+0.1,'whoosh',1.0); sfx(T(8)+0.9,'whoosh',0.6); sfx(T(9)+0.5,'whoosh',0.8)
handheld(cam,0.5)
finish('ch8',DUR)
