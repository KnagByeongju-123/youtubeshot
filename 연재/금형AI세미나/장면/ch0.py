import sys,os; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from s3d import *
T,E,DUR,cs=chapter(0)
sc=setup(texture=True)
floor(extent=1400)
# 베어링 씰 (주황) — 회전 무대 위
seal=revolve(seal_profile(),'seal',seg=128,rgb=COL['sheet'],closed=True); seal=apply_mods(seal)
hero=empty('hero',(0,0,30)); seal.parent=hero; seal.scale=(3,3,3); seal.location=(0,0,-6)
pedestal((0,0,0),r=110,h=14)
spin(hero,0,24,turns=0.5)
key(hero,'rotation_euler',0,(0,0,0))
# 치수 라벨
l1=text('지름 52 mm',16,(0,-40,140),rgb=COL['white']); show(l1,T(2)+0.3,E(3))
l2=text('높이 4 mm',14,(-150,-40,95),rgb=COL['sky']); show(l2,T(2)+2.2,E(3))
l3=text('두께 0.6 mm · 스테인리스',14,(150,-40,95),rgb=COL['accent']); show(l3,T(3)+0.4,E(3))
# 단계 받침대 (게임 맵처럼 한 줄)
ST=[('프롬프트','2D 도면'),('블렌더','3D 모델'),('프리캐드','MCP'),('부품 도면','PDF'),('성형해석',''),('역설계',''),('가공','')]
X0,DX,Y=420,300,0
icons=[]
for i,(a,b) in enumerate(ST):
    x=X0+i*DX
    pedestal((x,Y,0),r=95,h=10)
    t=text(a,24,(x,Y-30,190)); show(t,0.1)
    if b: t2=text(b,18,(x,Y-30,160),rgb=COL['accent']); show(t2,0.1)
    num=text(str(i+1),30,(x,Y-30,230),rgb=COL['accent']); 
    icons.append(x)
# 아이콘 모형
x=icons[0]; box((110,8,60),(x-30,Y,75),COL['white'],bevel=6); [box((70-k*18,9,5),(x-40,Y-1,90-k*16),COL['ink']) for k in range(3)]
image_plane(os.path.join(HERE,'도면_1_버링펀치.png'),110,(x+45,Y+20,60),rot=(math.radians(75),0,0),name='dwg')
x=icons[1]; p=revolve(PUNCH,'p3',rgb=COL['punch'],loc=(x,Y,12)); p.scale=(1.6,1.6,1.6); spin(p,0,DUR,turns=1)
x=icons[2]; box((60,30,30),(x-55,Y,40),COL['sky'],bevel=4); box((60,30,30),(x+55,Y,40),COL['purple'],bevel=4); curve_line([(x-25,Y,40),(x+25,Y,40)],bevel=4,rgb=COL['accent'])
text('AI',16,(x-55,Y-16,40),rgb=COL['ink']); text('CAD',14,(x+55,Y-16,40),rgb=COL['ink'])
for k in range(3):
    sp=sphere(5,(x-20,Y,40)); keyv(sp,'location',[(k*0.5+j*1.5,(x-20+40*((j%2)),Y,40)) for j in range(int(DUR/1.5)+1)])
x=icons[3]
for k in range(4): image_plane(os.path.join(HERE,'도면_%d_%s.png'%((k%3)+1,['버링펀치','버링다이','펀치고정판'][k%3])),120,(x-20+k*10,Y+k*10,75+k*3),rot=(math.radians(80),0,0),name='pg')

x=icons[4]
for k,(rr,c_) in enumerate([(70,(1,0.85,0.2)),(55,(1,0.55,0.1)),(40,(0.95,0.25,0.15)),(25,(0.25,0.55,1))]): cyl(rr,3+k*2,(x,Y,14+k),c_,name='fem')
p5=revolve(PUNCH,'p5',rgb=COL['punch'],loc=(x,Y,40)); p5.scale=(1.3,1.3,1.3); keyv(p5,'location',[(0,(x,Y,60)),(2,(x,Y,25)),(4,(x,Y,60)),(6,(x,Y,25)),(8,(x,Y,60))])
x=icons[5]; seal2=revolve(seal_profile(),'seal2',seg=96,rgb=COL['sheet'],closed=True); seal2.location=(x,Y,60); seal2.scale=(2.2,2.2,2.2); spin(seal2,0,DUR,turns=0.6)
curve_line([(x+70,Y-10,120),(x-70,Y-10,120)],bevel=4,rgb=COL['accent']); cone=cyl(10,20,(x-75,Y-10,120),COL['accent'],seg=4,rot=(0,math.radians(-90),0))
x=icons[6]; cyl(12,80,(x,Y,95),COL['post']); cyl(4,30,(x,Y,45),COL['white']); box((140,90,24),(x,Y,22),COL['plate'],bevel=2)
# 카메라: 크레인 다운 → 오빗 → 받침대 따라 비행
cam,tgt=camera(35)
cam_keys(cam,tgt,[(0,(0,-700,520),(0,0,40)),(T(1)+3,(0,-360,190),(0,0,50))])
orbit(cam,tgt,T(1)+3,E(3)-1,(0,0,55),360,140,-90,-55,n=8)
cam_keys(cam,tgt,[(E(3)+0.4,(250,-650,320),(500,0,90))])
stops=[T(4)+1.0,T(4)+4.0,T(5)+1.5,T(6)+1.5,T(7)+0.8,T(7)+3.6,T(8)+0.6,T(8)+2.8]
for i,t in enumerate(stops[1:]):
    x=icons[min(i,6)]
    cam_keys(cam,tgt,[(t,(x+60,-420,230),(x,0,100))])
cam_keys(cam,tgt,[(E(8)-0.2,(X0+3*DX,-1700,900),(X0+3*DX,0,60),None),(DUR,(X0+3*DX,-1750,920),(X0+3*DX,0,60))])
handheld(cam,0.6)
finish('ch0',DUR)
