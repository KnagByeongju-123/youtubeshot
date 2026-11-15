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
hm=text('반복은 AI · 마지막 확인은 사람',44,(2000,-150,680),rgb=COL['white']); show(hm,T(5)+0.5,E(5)+0.4)
okk=text('OK',90,(2000,-150,590),rgb=(0.4,1,0.5)); show(okk,T(5)+2.8,E(5)+0.4)
# 마지막: 금형 세트
DXS=2000
parts,up,root=die_set((DXS,0,145))
# 가공을 마친 부품이 금형에 장착됨 (다이 → 펀치 차례)
tM0=T(4)+2.8; tM1=T(6)-0.6
keyv(up,'location',[(0,(0,0,260)),(tM1-0.2,(0,0,260)),(T(6)+0.3,(0,0,140)),(T(7)+0.6,(0,0,140)),(DUR-1.2,(0,0,0))])
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
mt=text('가공을 마친 부품 → 금형에 장착',40,(2000,-150,680),rgb=COL['white']); show(mt,tM0+0.2,T(5)+0.2)
SXc=DXS; ZC=145+38
ti=text('AI로 금형 만들기',64,(DXS,-150,480),rgb=COL['accent']); show(ti,T(7)+0.6)
ty=text('들어 주셔서 감사합니다',40,(DXS,-150,410),rgb=COL['white']); show(ty,T(7)+0.9)
# 카메라: 받침대 따라 → 금형 세트
cam,tgt=camera(35)
cam_keys(cam,tgt,[(0,(0,-2000,1100),(0,0,80)),(T(2)-0.3,(xs[0]-200,-700,420),(xs[0],0,100))])
for i in range(7):
    cam_keys(cam,tgt,[(lit[i]+0.15,(xs[i]+80,-560,300),(xs[i],0,100))])
    if i: sfx(lit[i]-0.3,'whoosh',0.8)
    nxt=lit[i+1]-0.3 if i<6 else lit[i]+1.0
    if nxt>lit[i]+0.4: cam_keys(cam,tgt,[(nxt,(xs[i]+115,-520,285),(xs[i]+12,0,100))])
cam_keys(cam,tgt,[(tM0+0.6,(DXS-350,-1450,480),(DXS,0,290)),(half,(DXS-150,-1300,420),(DXS,0,280)),(tM1,(DXS+200,-1350,480),(DXS,0,300)),(E(5),(DXS+120,-1400,560),(DXS,0,360))])
cam_keys(cam,tgt,[(T(6)+0.3,(SXc-80,-560,ZC+60),(SXc,0,ZC)),(T(6)+1.2,(SXc,-95,ZC+8),(SXc,0,ZC))])
cam.data.lens=35; cam.data.keyframe_insert('lens',frame=F(T(6)+0.3)); cam.data.lens=18; cam.data.keyframe_insert('lens',frame=F(T(6)+1.2))
orbit(cam,tgt,T(6)+1.2,T(7)-0.1,(SXc,0,ZC),95,8,-90,190,n=12)
cam.data.keyframe_insert('lens',frame=F(T(7)-0.1))
cam_keys(cam,tgt,[(T(7)+0.4,(SXc-200,-420,ZC+30),(SXc,0,ZC+20))])
cam.data.lens=35; cam.data.keyframe_insert('lens',frame=F(T(7)+0.9))
cam_keys(cam,tgt,[(T(7)+1.8,(DXS-280,-1250,560),(DXS,0,230)),(DUR,(DXS-200,-1300,600),(DXS,0,230))])
sfx(tM0-0.5,'whoosh',1.0)
for i_,o_ in enumerate(dies): sfx(tM0+(half-tM0)*i_/nd+0.85,'click',0.5)
for i_,o_ in enumerate(puns): sfx(half+(tM1-half-1.0)*i_/npn+0.85,'click',0.6)
sfx(T(6)+0.3,'whoosh',1.0); sfx(T(7)-0.1,'whoosh',0.9); sfx(DUR-1.3,'click',1.0)
handheld(cam,0.5)
finish('ch8',DUR)
