import sys,os; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from r3d import *
T,E,DUR,cs=chapter(9)
sc=setup(); floor(grid=False,z=-200)
# 부품 도면 → 고속가공기 · 와이어커팅 → 조립(부품이 내려와 끼워짐) → 시험 타발(상형 오르내림) → 측정 → 금형 완성
X1,X2,X3=-1500,-800,600
for i,s in enumerate(('부품 도면','부품 목록')):
    c=card(s,'',(X1+(i-0.5)*240,-100,260),COL['white'],w=220,h=70,tsize=24); pop(c,T(1)+0.2+i*0.5)
vg,vh,vz=vmc((X2-300,0,-200)); pop(vg,T(2)-0.3)
wg,wu,wz=wire_edm((X2+350,0,-200)); pop(wg,T(2)+0.3)
for x,s in ((X2-300,'고속가공기: 판 · 인서트'),(X2+350,'와이어커팅: 다이 구멍 윤곽')):
    c=card(s,'',(x,-260,460),COL['sky'],w=330,h=56,tsize=20); pop(c,T(2)+0.6)
parts,up,root=die_set((X3,0,0))
lows=[o for o,g in parts if g=='lower']; strips=[o for o,g in parts if g=='strip']
for k,o in enumerate(sorted(lows,key=lambda o:o.location.z)):
    t=T(3)-0.6+min(k,40)*0.03; z0=o.location.z
    keyv(o,'location',[(0,(o.location.x,o.location.y,z0+600)),(t,(o.location.x,o.location.y,z0+600)),(t+0.5,(o.location.x,o.location.y,z0))])
for o in strips: pop(o,T(3)+1.4)
ts=[(0,(0,0,700)),(T(3)+0.6,(0,0,700)),(T(3)+1.4,(0,0,170))]
t=T(3)+1.8
while t<E(4)-0.6:
    ts+=[(t,(0,0,170)),(t+0.35,(0,0,0)),(t+0.55,(0,0,0)),(t+0.9,(0,0,170))]; t+=1.3
keyv(up,'location',ts)
m=card('측정: 버링 높이 · 끝 갈라짐','필요하면 기초 구멍 지름 조정',(X3,-200,360),COL['accent'],w=420,h=70,tsize=22,ssize=15); pop(m,T(4)+0.3,T(5)-0.1)
dn=card('금형 완성 → 양산','',(X3,-200,360),(0.35,1,0.45),w=380,h=70,tsize=28); pop(dn,T(5)+0.3)
cam,tgt=camera(32)
cam_keys(cam,tgt,[(0,(X1,-900,300),(X1,0,230)),(T(2)-0.4,(X1+100,-920,300),(X1,0,230)),(T(2)+0.3,(X2,-1700,500),(X2,0,150)),(T(3)-0.8,(X2+80,-1720,500),(X2,0,150)),
                  (T(3)-0.1,(X3,-1500,650),(X3,0,100)),(T(4)-0.1,(X3+120,-1450,600),(X3,0,100)),(T(4)+0.5,(X3+60,-1150,380),(X3,0,130)),(DUR,(X3+80,-1170,390),(X3,0,130))])
handheld(cam,0.5)
finish('ch9',DUR)
