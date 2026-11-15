import sys,os; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from r3d import *
T,E,DUR,cs=chapter(7)
sc=setup(); floor(grid=False,z=-200)
# 금형 전체 (상형 들어 올림) → 색 구분 → 리프터 확대 → 하프블랭킹 패드 → 프레스 하중
parts,up,root=die_set((0,0,0))
keyv(up,'location',[(0,(0,0,0)),(T(1)+1.0,(0,0,0)),(T(1)+2.5,(0,0,170))])
c0=card('부품 192개','상형 + 하형 + 판재',(0,-200,330),COL['white'],w=260,h=60,tsize=22,ssize=14); pop(c0,T(1)+0.6,T(2)-0.1)
for i,(s,cl) in enumerate((('상형 펀치',COL['punch']),('하형 다이',COL['die']),('판재',COL['sheet']))):
    c=card(s,'',(-220+i*220,-200,330),cl,w=190,h=56,tsize=22); pop(c,T(2)+0.3+i*0.5,T(3)-0.2)
lf=card('리프터: 스트립을 4.2 띄움','버링이 다이에 걸리지 않게',(SX[2]-40,-60,62),COL['sky'],w=120,h=34,tsize=9,ssize=6); pop(lf,T(3)+0.4,T(4)-0.1)
hp=card('하프블랭킹 받침 패드','링만 내려가고 가운데 조각은 그대로',(SX[5]-40,-60,62),COL['accent'],w=140,h=34,tsize=9,ssize=5.5); pop(hp,T(4)+0.4,T(5)-0.1)
pr=card('합계 ≈ 634 kN (약 65 톤)','→ 80 톤 이상 프레스',(0,-200,330),COL['red'],w=380,h=70,tsize=24,ssize=16); pop(pr,T(5)+0.3)
cam,tgt=camera(32)
orbit(cam,tgt,0,T(2)-0.2,(0,0,40),1300,520,-125,-80,n=10)
cam_keys(cam,tgt,[(T(2)+0.3,(0,-1350,520),(0,0,90)),(T(3)-0.1,(80,-1380,520),(0,0,90)),(T(3)+0.8,(SX[2]-30,-300,90),(SX[2],0,10)),(T(4)-0.1,(SX[2]+10,-290,80),(SX[2],0,10)),
                  (T(4)+0.8,(SX[5]-20,-280,100),(SX[5],0,10)),(T(5)-0.1,(SX[5]+10,-270,90),(SX[5],0,10)),(T(5)+0.9,(-150,-1400,600),(0,0,100)),(DUR,(-180,-1420,610),(0,0,100))])
handheld(cam,0.5)
finish('ch7',DUR)
