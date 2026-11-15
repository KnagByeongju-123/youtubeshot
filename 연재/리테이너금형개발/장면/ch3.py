import sys,os; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from r3d import *
T,E,DUR,cs=chapter(3)
sc=setup(); floor(grid=False,z=-40)
# 제품 3D: 돌며 보기 → 아래에서 버링 끝 확대 → 무게
p=product((0,0,0))
c1=card('해석 단면을 그대로 돌려 붙임','',(0,-50,45),COL['sky'],w=170,h=24,tsize=10); pop(c1,T(2)+0.2,T(3)+1.5)
c2=card('제품 무게 ≈ 31.2 g','SPCC · t1.4 · 버링 14',(0,-30,52),COL['accent'],w=110,h=26,tsize=10,ssize=6); pop(c2,T(4)+0.2)
cam,tgt=camera(40)
orbit(cam,tgt,0,T(2)+1.0,(0,0,0),150,70,-120,-60,n=8)
cam_keys(cam,tgt,[(T(3)-0.3,(10,-110,-40),(25,5,-2)),(T(3)+0.8,(45,-30,-22),(30,5,-2)),(T(4)-0.3,(50,-22,-20),(30,8,-2)),(T(4)+0.6,(0,-150,40),(0,0,10)),(DUR,(15,-155,45),(0,0,10))])
handheld(cam,0.15)
finish('ch3',DUR)
