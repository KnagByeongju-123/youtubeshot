import sys,os; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from g3d import *
T,E,DUR,cs=chapter(5)
sc=setup(texture=True); floor(extent=2600)
VX=0
vg,head,TZ=vmc((VX,0,0))
wp=box((220,140,60),(VX,-20,TZ+30),(0.72,0.74,0.78),bevel=2,name='work')
# 1) 원점 맞추기 + 구멍 표
org=empty('org',(VX-110,-90,TZ+60))
for ax,c in (((40,0,0),COL['red']),((0,40,0),(0.3,0.9,0.4)),((0,0,40),COL['sky'])):
    l=curve_line([(0,0,0),ax],bevel=2.5,rgb=c); l.parent=org
keyv(org,'scale',[(0,(0,0,0)),(T(1)+0.3,(0,0,0)),(T(1)+0.6,(1,1,1))])
keyv(wp,'rotation_euler',[(0,(0,0,math.radians(18))),(T(1)+0.6,(0,0,math.radians(18))),(T(1)+1.8,(0,0,0))])
HP=[(-60,-40),(60,-40),(-60,20),(60,20)]
for i,(x,y) in enumerate(HP):
    h=cyl(8,2,(VX+x,y-20,TZ+61),(0.08,0.09,0.11),seg=24); keyv(h,'scale',[(0,(0,0,0)),(T(1)+2.0+i*0.3,(0,0,0)),(T(1)+2.2+i*0.3,(1,1,1))])
ht=table((VX+420,-80,520),['구멍','X','Y','깊이'],[['1','-60','-40','20'],['2','60','-40','20'],['3','-60','20','20'],['4','60','20','20']],[-150,-60,20,100],w=340,t0=T(1)+2.2,dt=0.3,size=12)
keyv(ht,'scale',[(0,(0,0,0)),(T(1)+1.9,(0,0,0)),(T(1)+2.1,(1,1,1)),(E(1)+0.4,(1,1,1)),(E(1)+0.7,(0,0,0))])
# 2) 회전수 · 이송 계산 (계기판)
fm=text('S = 1000 · Vc ÷ (π · D)',26,(VX+420,-80,520),rgb=COL['white']); show(fm,T(2)+0.2,E(2)+0.3)
fm2=text('F = S · 날수 · fz',26,(VX+420,-80,480),rgb=COL['white']); show(fm2,T(2)+0.6,E(2)+0.3)
gauge=empty('gauge',(VX+420,-80,380))
bg=box((300,6,24),(0,0,0),(0.2,0.24,0.3)); bg.parent=gauge
fill=empty('fill',(-150,-1,0)); fb_=box((1,8,26),(0.5,0,0),(0.4,1,0.5)); fb_.parent=fill; fill.parent=gauge
lim=box((5,10,44),(120,-2,0),COL['red']); lim.parent=gauge
lt=text('주축 최고',13,(120,-2,32),rgb=COL['red']); lt.parent=gauge
keyv(gauge,'scale',[(0,(0,0,0)),(T(2)+0.8,(0,0,0)),(T(2)+1.1,(1,1,1)),(E(2)+0.3,(1,1,1)),(E(2)+0.5,(0,0,0))])
keyv(fill,'scale',[(T(2)+1.1,(0,1,1)),(T(2)+2.6,(250,1,1)),(T(2)+3.0,(240,1,1))])
# 3) 파워밀 경로(황삭·중삭·정삭) + 구멍 NC
def zig(z,step,col,name):
    pts=[]
    for k in range(int(200/step)+1):
        x=-100+k*step; pts+= [(VX+x,-80,z),(VX+x,40,z)] if k%2==0 else [(VX+x,40,z),(VX+x,-80,z)]
    c=curve_line(pts,bevel=1.2,rgb=col,name=name); return c
for i,(z,st,c) in enumerate(((TZ+75,40,(0.95,0.45,0.25)),(TZ+68,20,COL['accent']),(TZ+62,8,(0.4,1,0.5)))):
    p=zig(z,st,c,'path%d'%i); draw_on(p,T(3)+0.3+i*1.2,T(3)+1.4+i*1.2); keyv(p,'scale',[(0,(1,1,1)),(E(3)+0.4,(1,1,1)),(E(3)+0.6,(0,0,0))])
for i,s_ in enumerate(('황삭','중삭','정삭')):
    o=text(s_,22,(VX-170,-130,TZ+90-i*28),rgb=((0.95,0.45,0.25),COL['accent'],(0.4,1,0.5))[i],align='RIGHT'); show(o,T(3)+0.3+i*1.2,E(3)+0.6)
mac=card('PUNCH.mac','파워밀 매크로',(VX-450,-80,420),COL['sky'],w=200,h=80,tsize=22); keyv(mac,'scale',[(0,(0,0,0)),(T(3)-0.1,(0,0,0)),(T(3)+0.2,(1,1,1)),(E(3)+0.4,(1,1,1)),(E(3)+0.6,(0,0,0))])
# 4) NC 다시 읽기 검사 + 시뮬레이션
codes=['O1001','G90 G54','G81 X-60. Y-40. Z-20.','X60. Y-40.','X-60. Y20.','X60. Y20.','M29 S800','G84 F1000.']
ncp=empty('ncp',(VX+430,-80,560))
bgp=box((330,6,300),(0,8,-130),(0.07,0.08,0.11),bevel=4); bgp.parent=ncp
for i,cd in enumerate(codes):
    o=text(cd,15,(-150,-3,-i*32),rgb=COL['white'],bold=False,align='LEFT'); o.parent=ncp
    okk=text('OK',13,(130,-3,-i*32),rgb=(0.4,1,0.5)); okk.parent=ncp; keyv(okk,'scale',[(0,(0,0,0)),(T(4)+0.5+i*0.4,(0,0,0)),(T(4)+0.6+i*0.4,(1,1,1))])
keyv(ncp,'scale',[(0,(0,0,0)),(T(4)-0.1,(0,0,0)),(T(4)+0.2,(1,1,1)),(E(4)+0.3,(1,1,1)),(E(4)+0.5,(0,0,0))])
scan=box((330,4,6),(VX+430,-90,560),(0.4,1,0.5),name='ncscan')
keyv(scan,'location',[(0,(VX+430,-90,-300)),(T(4)+0.35,(VX+430,-90,-300)),(T(4)+0.4,(VX+430,-90,560)),(T(4)+3.6,(VX+430,-90,340)),(T(4)+3.7,(VX+430,-90,-300))])
# 주축 움직임: 구멍 위로 차례로 (시뮬레이션)
hk=[(0,(0,-10,380))]
for i,(x,y) in enumerate(HP):
    t=T(4)+0.5+i*0.8; hk+=[(t,(x,y-20,330)),(t+0.3,(x,y-20,TZ+130)),(t+0.6,(x,y-20,330))]
keyv(head,'location',hk+[(E(4)+0.2,(0,-10,380))])
sim=text('시뮬레이션: 충돌 없음',22,(VX,-150,560),rgb=(0.4,1,0.5)); show(sim,T(4)+3.6,E(4)+0.3)
# 5) 작업자 셋업 · 측정 → 보정
wk=person((VX-380,-200,0),(0.95,0.60,0.25),name='worker',scale=1.4); keyv(wk,'scale',[(0,(0,0,0)),(T(5)-0.1,(0,0,0)),(T(5)+0.3,(1.4,1.4,1.4))])
probe=cyl(5,90,(VX+60,-60,TZ+140),(0.95,0.95,0.97),seg=16,name='probe'); keyv(probe,'location',[(0,(VX+60,-60,900)),(T(5)+1.4,(VX+60,-60,900)),(T(5)+2.0,(VX+60,-60,TZ+110)),(E(5),(VX+60,-60,TZ+110)),(E(5)+0.4,(VX+60,-60,900))])
ms=text('측정 → 다음 조건 · 보정',24,(VX,-150,560),rgb=COL['accent']); show(ms,T(5)+1.8,E(5)+0.4)
# 6~7) 프롬프트: 공구 · 주축 최고 · 열처리 전후
pc=box((800,8,170),(VX+60,-260,560),(0.08,0.10,0.15),bevel=6,name='prompt'); show(pc,T(6)-0.2)
p1=text(' ',18,(VX-320,-265,590),rgb=COL['white'],bold=False,align='LEFT'); typewriter(p1,'"공구 D10 평 · D6 R0.5 · 볼 D4, 주축 최고 회전수,',T(6)+0.3,T(6)+3.0); show(p1,T(6)-0.1,base=(1,1,1))
p2=text(' ',18,(VX-320,-265,550),rgb=COL['accent'],bold=False,align='LEFT'); typewriter(p2,' 열처리 전 황삭과 후 정삭을 나눠 매크로를 만들어 줘."',T(6)+3.0,T(6)+5.2); show(p2,T(6)-0.1,base=(1,1,1))
for i,nm in enumerate(('공구표','S · F 표','PUNCH.mac')):
    o=card(nm,'기계에 맞게',(VX-200+i*250,-260,390),(0.4,1,0.5),w=200,h=70,tsize=20)
    keyv(o,'scale',[(0,(0,0,0)),(T(7)+0.3+i*0.5,(0,0,0)),(T(7)+0.6+i*0.5,(1,1,1))])
cam,tgt=camera(35)
cam_keys(cam,tgt,[(0,(VX-900,-1300,800),(VX,0,300)),(T(1)+0.5,(VX-250,-650,380),(VX+80,0,TZ+60)),(E(1),(VX-150,-750,420),(VX+200,0,300))])
cam_keys(cam,tgt,[(T(2)+0.4,(VX+420,-650,450),(VX+420,0,450)),(E(2),(VX+430,-620,440),(VX+420,0,440))])
cam_keys(cam,tgt,[(T(3)+0.3,(VX+120,-380,TZ+220),(VX,-20,TZ+60))])
orbit(cam,tgt,T(3)+0.3,E(3),(VX,-20,TZ+60),360,160,-75,-130,n=8)
cam_keys(cam,tgt,[(T(4)+0.4,(VX+180,-1000,480),(VX+200,0,380)),(E(4),(VX+200,-980,470),(VX+200,0,380))])
cam_keys(cam,tgt,[(T(5)+0.5,(VX-200,-900,380),(VX-100,0,250)),(E(5),(VX-150,-880,370),(VX-100,0,250))])
cam_keys(cam,tgt,[(T(6)+0.4,(VX+60,-1150,560),(VX+60,-260,470)),(DUR,(VX+90,-1180,570),(VX+60,-260,470))])
sfx(T(3)+0.2,'whoosh',0.8); sfx(T(4)+0.2,'whoosh',0.8)
handheld(cam,0.5)
finish('ch5',DUR)
