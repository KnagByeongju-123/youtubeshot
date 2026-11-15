import sys,os; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from g3d import *
T,E,DUR,cs=chapter(1)
sc=setup(texture=True); floor(extent=2400)
# 네 줄 작업 흐름 (레인)
LANES=[('역설계',COL['sheet'],['제품 단면','형상 분석','공정안','성형해석','공정·블랭크','금형 치수','입체 검토']),
       ('공통 준비',COL['sky'],['도면 접수','치수·공차','입체 모델','공정 계획','작업지시서']),
       ('고속가공기',COL['punch'],['가공 모델','공구·조건','파워밀','NC 출력','시뮬레이션','셋업·가공','측정']),
       ('와이어커팅',COL['die'],['윤곽 추출','시작 구멍','NC 작성','조건·보정','드라이런','가공','측정·보정'])]
Y=[300,100,-100,-300]; SX=150
starts=[T(1)+0.2,T(2)+0.2,T(4)+0.2,T(4)+0.6]
for li,(nm,c,steps) in enumerate(LANES):
    y=Y[li]; x0=-500 if li<2 else 200
    if li==1: x0=-500+0
    lane=box((SX*len(steps)+40,70,8),(x0+SX*(len(steps)-1)/2,y,4),(0.18,0.21,0.27)); show(lane,starts[li]-0.4)
    t=text(nm,32,(x0-100,y-40,40),rgb=c,align='RIGHT'); show(t,starts[li]-0.3)
    for k,s_ in enumerate(steps):
        b=box((136,56,54),(x0+k*SX,y,34),c,bevel=4); show(b,starts[li]+k*0.25)
        tx=text(s_,17,(x0+k*SX,y-30,36),rgb=COL['ink']); show(tx,starts[li]+k*0.25+0.05)
        nn=text(str(k+1),18,(x0+k*SX,y-30,74),rgb=COL['accent']); show(nn,starts[li]+k*0.25+0.05)
# 흐르는 판재 토큰
tok=empty('tok',(-500,300,80)); tb=revolve(seal_profile(),'tokseal',seg=64,rgb=COL['accent']); tb.parent=tok; tb.scale=(1.5,1.5,1.5)
keyv(tok,'location',[(0,(-500,300,80)),(T(1)+0.5,(-500,300,80)),(E(1)-0.3,(-500+SX*6,300,80)),(T(2)+0.4,(-500,100,80)),(E(2)-0.3,(-500+SX*4,100,80))])
keyv(tok,'scale',[(0,(0,0,0)),(T(1)+0.3,(0,0,0)),(T(1)+0.6,(1,1,1)),(T(3)+0.3,(1,1,1)),(T(3)+0.6,(0,0,0))])
# 둘로 나뉨
for k,yy in ((0,-100),(1,-300)):
    tk=empty('tk%d'%k,(-500+SX*4,100,80)); m=revolve(PUNCH if k==0 else DIE_P,'tkm%d'%k,rgb=COL['punch'] if k==0 else COL['die']); m.parent=tk; m.scale=(1.2,1.2,1.2)
    keyv(tk,'location',[(0,(-500+SX*4,100,80)),(T(3)+0.4,(-500+SX*4,100,80)),(T(3)+1.4,(200,yy,80)),(E(4)-0.2,(200+SX*6,yy,80))])
    keyv(tk,'scale',[(0,(0,0,0)),(T(3)+0.35,(0,0,0)),(T(3)+0.6,(1,1,1))])
    sfx(T(3)+0.4,'whoosh',0.7)
spl=text('두 설비로 나눔',30,(-500+SX*4+220,0,230),rgb=COL['accent']); show(spl,T(3)+0.3,E(4))
# 측정값 되돌림 화살표
fb=curve_line([(200+SX*6+80,-200,40),(200+SX*6+160,-200,200),(-560,-200,320),(-640,250,200),(-600,300,80)],bevel=5,rgb=(0.4,1,0.5),name='fb'); draw_on(fb,T(5)+0.2,E(5)-0.3)
ft=text('측정값 → 다음 조건에 반영',30,(0,-200,360),rgb=(0.4,1,0.5)); show(ft,T(5)+0.6)
cam,tgt=camera(32)
cam_keys(cam,tgt,[(0,(-700,-900,700),(-200,200,40)),(T(1)+0.6,(-500,-700,520),(-80,280,40)),(E(1),(0,-700,520),(150,280,40))])
cam_keys(cam,tgt,[(T(2)+0.6,(-500,-850,480),(-150,100,40)),(E(2),(-100,-850,480),(0,100,40))])
cam_keys(cam,tgt,[(T(3)+0.8,(0,-1100,700),(150,-50,40)),(E(4),(500,-1200,700),(500,-200,40))])
cam_keys(cam,tgt,[(T(5)+0.6,(200,-1350,850),(200,0,80)),(DUR,(250,-1380,870),(200,0,80))])
handheld(cam,0.5)
finish('ch1',DUR)
