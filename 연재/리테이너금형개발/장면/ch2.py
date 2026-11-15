import sys,os; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from r3d import *
T,E,DUR,cs=chapter(2)
sc=setup(); floor(grid=False,z=-40)
# 요청 Ø50/Ø60 → 띠 5 mm 에 버링(지름 10 넘음)이 못 들어감 → Ø80 으로 → 버링 14개 · 간격
# 설명 카드는 링 왼쪽(x = -78)에 하나씩 바꿔 가며
CX=-80
def info(s,sub,t0,t1,col=COL['white'],z=20):
    c=card(s,sub,(CX,-10,z),col,w=66,h=16 if not sub else 22,tsize=6,ssize=4.2); pop(c,t0,t1); return c
r60=ring(25,30,1.4,(0,0,0)); pop(r60,T(1),T(4)-0.1)
info('요청: 안 Ø50 · 바깥 Ø60','링 폭 5 mm',T(1)+0.3,T(4)-0.1)
# 버링 자리(지름 10.6, 뿌리 R 까지 약 12.8): 띠 밖으로 넘침. 윗면은 링 윗면보다 살짝 아래(같은 높이면 지글거림)
b=revolve([(0,-2.6),(6.4,-2.6),(6.4,1.3),(0,1.3)],'bz',seg=48,rgb=COL['red'],loc=(27.5,0,0),closed=True); pop(b,T(2)+0.4,T(4)-0.1)
x=mark(False,(27.5,-8,14),10); pop(x,T(3)+0.2,T(4)-0.1)
info('버링 하나 지름 10 넘음','띠 5 mm 에 못 들어감',T(3)+0.2,T(4)-0.1,COL['red'],z=-2)
r80=ring(25,40,1.4,(0,0,0)); pop(r80,T(4)+0.1)
info('바깥 Ø80 으로 넓힘 (제안)','',T(4)+0.3,T(7)-0.1,COL['accent'])
pc=circle_line(32.5,(0,0,1.55),COL['sky'],bevel=0.25); pop(pc,T(5))
for k,(bx,by) in enumerate(burr_xy()):
    c=revolve([(4,1.3),(5.3,1.3),(5.3,-2.6),(4,-2.6)],'b%d'%k,seg=40,rgb=COL['punch'],loc=(bx,by,0),closed=True); pop(c,T(5)+0.3+k*0.08)
info('버링: Ø65 원 위 14개','안 Ø8 · 뿌리 R1',T(5)+0.4,T(7)-0.1,COL['sky'],z=-2)
dm=curve_line([(32.5,0,2.2),(32.5*math.cos(2*math.pi/14),32.5*math.sin(2*math.pi/14),2.2)],0.35,COL['accent']); pop(dm,T(6))
dt=text('14.6',4,(37,-6,5),rgb=COL['accent']); pop(dt,T(6)+0.2)
info('버링 간격 약 14.6','',T(6)+0.3,T(7)-0.1,COL['accent'],z=-22)
info('고객 협의 → 확정','숫자와 그림으로 설명',T(7)+0.2,None,(0.35,1,0.45))
cam,tgt=camera(40)
cam_keys(cam,tgt,[(0,(-25,-170,110),(-22,0,0)),(T(2)+0.1,(-25,-170,110),(-22,0,0)),(T(2)+0.9,(5,-120,80),(5,0,5)),(T(4)-0.2,(8,-118,78),(5,0,5)),
                  (T(4)+0.6,(-25,-175,115),(-22,0,0)),(T(6)-0.2,(-22,-178,115),(-22,0,0)),(T(6)+0.6,(10,-110,75),(10,5,3)),(T(7)-0.2,(12,-108,74),(10,5,3)),
                  (T(7)+0.6,(-25,-175,110),(-22,0,0)),(DUR,(-20,-178,112),(-22,0,0))])
handheld(cam,0.12)
finish('ch2',DUR)
