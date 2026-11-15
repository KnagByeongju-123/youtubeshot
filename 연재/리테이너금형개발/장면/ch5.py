import sys,os; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from r3d import *
T,E,DUR,cs=chapter(5)
sc=setup()
# 일체형 버링 펀치 인서트 → 어깨 R 원이 이웃과 겹침 → "하나씩" → 개별 펀치 14개가 끼워짐
one=empty('one',(0,0,0))
dk=cyl(43,30,(0,0,16.4),COL['punch'],seg=96); dk.parent=one
for k,(bx,by) in enumerate(burr_xy()):
    c=revolve([(0,-3.6),(4,-3.6),(4,-1.0)]+[(4+3.4-3.4*math.cos(math.radians(a)),1.4-3.4+3.4*math.sin(math.radians(a))) for a in range(0,91,10)]+[(7.4,1.6),(0,1.6)],'pp%d'%k,seg=40,rgb=COL['punch'],loc=(bx,by,0),closed=True); c.parent=one
pop(one,T(1)+0.1,T(4)+0.2)
l1=card('처음: 원판 하나에 펀치 14개 (일체형)','',(0,-60,62),COL['sky'],w=200,h=22,tsize=10); pop(l1,T(1)+0.3,T(3)-0.1)
rs=[]
for k,(bx,by) in enumerate(burr_xy()):
    r=circle_line(7.4,(bx,by,-3.0),COL['red'],bevel=0.35,n=48,name='ov%d'%k); pop(r,T(2)+0.2+k*0.05,T(4)); rs.append(r)
l2=card('어깨 R3.4 → 펀치 굵기 Ø14.8 > 간격 14.6','',(0,-60,-40),COL['red'],w=220,h=22,tsize=10); pop(l2,T(2)+0.4,T(3)-0.2)
q=card('검토 의견','펀치는 하나씩 따로 끼워야 한다',(0,-60,-45),COL['accent'],w=200,h=34,tsize=12,ssize=9); pop(q,T(3)+0.1,T(5)-0.1)
c4=card('하나 부러지면 그것만 교체','',(0,-60,-75),(0.35,1,0.45),w=180,h=22,tsize=11); pop(c4,T(4)+0.3,T(5)-0.1)
# 개별 펀치: 금형 좌표의 2번 공정 펀치 14개를 가운데로
pg=empty('pg',(-SX[1],0,0))
ps=[]
for k in range(14):
    o=part('st2_burring_punch_%02d'%(k+1),COL['punch'],pg); ps.append(o)
    t=T(4)+0.4+k*0.12
    keyv(o,'location',[(0,(0,0,160)),(t,(0,0,160)),(t+0.45,(0,0,0))])
    keyv(o,'scale',[(0,(0,0,0)),(t-0.01,(0,0,0)),(t,(1,1,1))])
ri=card('어깨 R 3.4 → 2.4 로 줄이고 다시 해석','',(0,-60,-40),COL['sky'],w=220,h=22,tsize=10); pop(ri,T(5)+0.2,T(7)-0.1)
tm=card('해석 1회 ≈ 몇 초','바꾸고 → 다시 확인이 빠름',(0,-60,90),COL['accent'],w=170,h=34,tsize=12,ssize=9); pop(tm,T(6)+0.2,T(7)-0.1)
ok=card('몸통 Ø12.8 < 간격 14.6 ✔','결과는 거의 같음',(0,-60,90),(0.35,1,0.45),w=190,h=34,tsize=12,ssize=9); pop(ok,T(7)+0.2,T(8)-0.2)
# 펀치 끝 R2 · 클리어런스 비교 (1번 펀치 끝 가까이)
NX=32.5
def tip_card(s,sub,t0,t1,col):
    c=card(s,sub,(NX+33,-49,-1.5),col,w=240,h=65 if not sub else 85,tsize=20,ssize=14); pop(c,t0,t1,s=0.1); return c
tip_card('버링 펀치 끝 R2','구멍에 부드럽게 들어감',T(8)+0.2,T(9)-0.1,COL['sky'])
tip_card('끝 각짐 32 % → 끝 R2 29 %','버링 끝 두께 0.66 → 0.77',T(9)+0.2,T(10)-0.1,COL['accent'])
tip_card('틈을 좁혀 훑기 (0.85t · 0.7t)','높이 거의 그대로 · 하중 2~3배',T(10)+0.2,T(11)-0.1,COL['red'])
tip_card('틈 = 판 두께 1.4 ✔','펀치 Ø8 · 다이 구멍 Ø10.8',T(11)+0.2,None,(0.35,1,0.45))
cam,tgt=camera(40)
cam_keys(cam,tgt,[(0,(60,-150,-70),(0,0,10)),(T(2)-0.2,(40,-140,-80),(0,0,0)),(T(2)+0.6,(0,-60,-190),(0,0,0)),(T(3)-0.1,(40,-170,-80),(0,0,-25)),(T(4)-0.1,(45,-175,-78),(0,0,-25)),
                  (T(4)+0.3,(90,-160,60),(0,0,30)),(T(6)-0.2,(110,-150,40),(0,0,30)),(T(7)+0.2,(0,-240,40),(0,0,25)),(T(8)-0.3,(10,-245,40),(0,0,25)),(T(8)+0.5,(NX+40,-110,-15),(NX+6,0,0)),(DUR,(NX+42,-112,-14),(NX+6,0,0))])
handheld(cam,0.15)
finish('ch5',DUR)
