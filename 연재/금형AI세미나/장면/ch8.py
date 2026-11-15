import sys,os; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from s3d import *
T,E,DUR,cs=chapter(8)
sc=setup(texture=True)
floor(extent=2600)
ST=[('프롬프트','2D 도면'),('블렌더','3D 모델'),('프리캐드','MCP'),('부품 도면','PDF'),('성형해석',''),('역설계',''),('가공','')]
X0,DX=-900,300
xs=[X0+i*DX for i in range(7)]
lit=[T(2)+0.3,T(2)+2.4,T(2)+3.6,T(3)+0.4,T(3)+2.6,T(4)+0.4,T(4)+2.6]
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
hm=text('반복은 AI · 마지막 확인은 사람',56,(0,-60,420),rgb=COL['white']); show(hm,T(5)+0.3,E(5)+0.4)
okk=text('OK',90,(0,-60,320),rgb=(0.4,1,0.5)); show(okk,T(5)+2.8,E(5)+0.4)
# 마지막: 금형 세트
DXS=2000
parts,up,root=die_set((DXS,0,145))
keyv(up,'location',[(0,(0,0,90)),(T(6),(0,0,90)),(T(6)+1.6,(0,0,0)),(T(6)+2.4,(0,0,0)),(T(6)+3.6,(0,0,90))])
ti=text('AI로 금형 만들기',64,(DXS,-150,480),rgb=COL['accent']); show(ti,T(6)+0.2)
ty=text('들어 주셔서 감사합니다',40,(DXS,-150,410),rgb=COL['white']); show(ty,T(7)-0.2)
# 카메라: 받침대 따라 → 금형 세트
cam,tgt=camera(35)
cam_keys(cam,tgt,[(0,(0,-2000,1100),(0,0,80)),(T(2)-0.3,(xs[0]-200,-700,420),(xs[0],0,100))])
for i in range(7):
    cam_keys(cam,tgt,[(lit[i]+0.6,(xs[i]+80,-560,300),(xs[i],0,100))])
cam_keys(cam,tgt,[(T(5)+0.6,(0,-1650,640),(0,0,220)),(E(5),(0,-1600,620),(0,0,220))])
cam_keys(cam,tgt,[(T(6)+1.0,(DXS-300,-1250,600),(DXS,0,200))])
orbit(cam,tgt,T(6)+1.0,DUR,(DXS,0,200),1250,420,-104,-70,n=8)
handheld(cam,0.5)
finish('ch8',DUR)
