import sys,os; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from r3d import *
T,E,DUR,cs=chapter(8)
sc=setup(); floor(grid=False,z=-60)
# 간섭 검사: 이웃 다이 인서트가 겹침(빨강) → 빈 공정을 넣어 떨어뜨림 → 판재 성형면 접촉만 → 산출물 카드
A=cyl(48,30,(-42,0,-15),COL['die'],seg=96); B=cyl(43,30,(42,0,-15),COL['die'],seg=96)
pop(A,T(1)+0.1); pop(B,T(1)+0.3)
ov=cyl(6,31,(0,0,-15),COL['red'],seg=48); ov.scale=(1,4.2,1); pop(ov,T(1)+0.8,T(2)+1.0,s=1.0)
ovt=card('겹침 발견','이웃 공정 다이 인서트',(0,-70,60),COL['red'],w=170,h=34,tsize=13,ssize=9); pop(ovt,T(1)+1.0,T(2)+0.6)
keyv(B,'location',[(0,(42,0,-15)),(T(2)+0.6,(42,0,-15)),(T(2)+1.6,(126,0,-15))])
idl=text('빈 공정',10,(42,-50,8),rgb=(0.7,0.72,0.76)); pop(idl,T(2)+1.6)
fx=card('빈 공정 + 도피 홈 → 겹침 없음 ✔','',(40,-70,60),(0.35,1,0.45),w=230,h=26,tsize=12); pop(fx,T(2)+1.8,T(4)-0.1)
ct=card('남은 것: 판재 성형면 접촉','버링 하나당 0.4 mm³ 이하',(40,-70,30),COL['sky'],w=230,h=32,tsize=12,ssize=9); pop(ct,T(3)+0.2,T(4)-0.1)
for i,(s,sub) in enumerate((('STEP','부품 192개 · 조립'),('부품표','이름 · 크기 · 부피'),('설계 요약','치수 · 하중 · 공정'))):
    c=card(s,sub,(-80+i*120,-70,55),COL['accent'],w=110,h=44,tsize=14,ssize=8); pop(c,T(4)+0.2+i*0.4)
cam,tgt=camera(40)
cam_keys(cam,tgt,[(0,(0,-260,140),(0,0,0)),(T(2)+0.5,(20,-270,140),(20,0,0)),(T(2)+1.6,(60,-280,150),(50,0,0)),(T(4),(60,-290,150),(50,0,10)),(T(4)+0.6,(40,-230,90),(40,0,40)),(DUR,(45,-235,92),(40,0,40))])
handheld(cam,0.2)
finish('ch8',DUR)
