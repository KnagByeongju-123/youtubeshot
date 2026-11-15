import sys,os; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from r3d import *
T,E,DUR,cs=chapter(0)
sc=setup(); floor(grid=False,z=-320)
# 제품이 돌며 등장 → 제목 → 7단계 흐름 칩 → 향후 과제 카드
p=product((0,0,0)); p.scale=(3.0,)*3; spin(p,0,DUR,0.6); p.rotation_euler=(math.radians(-25),0,0)
pd=pedestal((0,0,-40),r=140,h=10)
t1=text('고객 도면 접수부터 금형 완성까지',26,(0,-60,165),rgb=COL['white']); show(t1,0.6)
t2=text('리테이너 · 프로그레시브 금형',18,(0,-60,132),rgb=COL['accent']); show(t2,1.2)
ST=['도면 접수','제품 검토','성형해석','금형 설계','검증','가공·조립','시험 타발']
gs=chips(ST,(-3*120,-160,-125),120,size=17,col=COL['sky'],t0=T(2)+0.2,dt=0.45,h=48)
for i in range(6):
    a=text('›',22,(-3*120+i*120+60,-162,-125),rgb=COL['accent']); show(a,T(2)+0.4+i*0.45)
c=card('향후 과제','금형비용 산출 (mold2 실적 → 견적)',(0,-200,-195),COL['accent'],w=420,h=70,tsize=22,ssize=15); pop(c,T(3)+0.3)
cam,tgt=camera(35)
cam_keys(cam,tgt,[(0,(0,-600,140),(0,0,50)),(T(2)-0.3,(60,-640,120),(0,0,40)),(T(2)+0.6,(0,-760,-20),(0,0,-60)),(DUR,(30,-800,-40),(0,0,-90))])
handheld(cam,0.4)
finish('ch0',DUR)
