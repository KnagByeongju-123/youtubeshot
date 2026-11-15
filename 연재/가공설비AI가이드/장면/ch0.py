import sys,os; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from g3d import *
T,E,DUR,cs=chapter(0)
sc=setup(texture=True); floor(extent=2400)
# 금형 세트 회전 무대 → 네 단계 받침대 순간이동 → 데이터·결과·담당·AI 카드
parts,up,root=die_set((0,0,145))
keyv(up,'location',[(0,(0,0,120)),(E(1)-1.0,(0,0,120)),(E(1)+0.6,(0,0,0))])
ST=[('역설계',COL['sheet']),('공통 준비',COL['sky']),('고속가공기',COL['punch']),('와이어커팅',COL['die'])]
X0=1100; DX=420; xs=[X0+i*DX for i in range(4)]
for i,(nm,c) in enumerate(ST):
    pedestal((xs[i],0,0),r=120,h=12)
    t=text(nm,34,(xs[i],-40,230),rgb=c); show(t,T(2)+0.2+i*0.6)
    n=text(str(i+1),40,(xs[i],-40,290),rgb=COL['accent']); show(n,T(2)+0.2+i*0.6)
# 단계 모형
seal=revolve(seal_profile(),'seal',seg=96,rgb=COL['sheet']); seal.location=(xs[0],0,60); seal.scale=(2.6,)*3; spin(seal,0,DUR,0.5)
image_plane(os.path.join(HERE,'도면_1_버링펀치.png'),170,(xs[1],10,90),rot=(math.radians(78),0,0))
vg,vh,vz=vmc((xs[2],0,12)); vg.scale=(0.28,)*3
wg,wu,wz=wire_edm((xs[3],0,12)); wg.scale=(0.28,)*3
# 데이터 · 결과 · 담당 · AI 카드
for i,(nm,c) in enumerate((('데이터',COL['white']),('결과',COL['sky']),('담당',COL['purple']),('AI',COL['accent']))):
    g=card(nm,'',(X0+DX*1.5+(i-1.5)*230,-150,430),c,w=200,h=80,tsize=34)
    keyv(g,'scale',[(0,(0,0,0)),(T(3)+0.3+i*0.5,(0,0,0)),(T(3)+0.5+i*0.5,(1.1,1.1,1.1)),(T(3)+0.7+i*0.5,(1,1,1))])
cam,tgt=camera(35)
cam_keys(cam,tgt,[(0,(-500,-1300,700),(0,0,180))])
orbit(cam,tgt,0.5,E(1)+0.4,(0,0,170),1250,420,-112,-70,n=8)
# 받침대 순간이동
for i in range(4):
    t=T(2)+0.3+i*0.6
    cam_keys(cam,tgt,[(t,(xs[i]+60,-620,300),(xs[i],0,130))]); sfx(t-0.35,'whoosh',0.8)
cam_keys(cam,tgt,[(T(3)+0.6,(X0+DX*1.5,-1700,700),(X0+DX*1.5,0,250)),(DUR,(X0+DX*1.5+60,-1750,720),(X0+DX*1.5,0,260))])
handheld(cam,0.5)
finish('ch0',DUR)
