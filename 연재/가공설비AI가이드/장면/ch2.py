import sys,os; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from g3d import *
T,E,DUR,cs=chapter(2)
sc=setup(texture=True); floor(extent=2400)
# AI 구슬(가운데) · 사람 넷(설계·CAM·작업자·품질)
ai=ai_orb((0,0,230),60); spin(ai,0,DUR,2); show(ai,T(1)-0.2,base=(1,1,1))
ROLES=[('설계',(0.62,0.42,0.95),(-600,250,0)),('CAM 담당',(0.30,0.65,0.95),(-200,350,0)),('가공 작업자',(0.95,0.60,0.25),(200,350,0)),('품질',(0.35,0.80,0.45),(600,250,0))]
ppl=[]
for i,(nm,c,p) in enumerate(ROLES):
    pg=person(p,c,name='p%d'%i,scale=1.4); keyv(pg,'scale',[(0,(0,0,0)),(T(1)+0.4+i*0.25,(0,0,0)),(T(1)+0.7+i*0.25,(1.4,1.4,1.4))]); pedestal(p,r=90,h=8)
    t=text(nm,28,(p[0],p[1]-60,250),rgb=c); show(t,T(1)+0.6+i*0.25); ppl.append((pg,p))
l1=text('AI: 초안 · 계산 · 검사',34,(0,-120,390),rgb=COL['accent']); show(l1,T(1)+0.3)
l2=text('사람: 결정 · 확인',34,(0,-120,340),rgb=COL['white']); show(l2,T(1)+1.6)
# 강조 고리 + 할 일 카드
tasks=[(0,T(2),['공정안 · 금형 치수','작업지시서 발행']),(1,T(3),['공구 · 조건 · 경로','충돌 검사']),(2,T(4),['셋업 · 첫 가공']),(3,T(4)+2.2,['치수 측정','보정값 돌려줌'])]
for i,t0,ls in tasks:
    p=ROLES[i][2]
    bpy.ops.mesh.primitive_torus_add(major_radius=100,minor_radius=5,location=(p[0],p[1],10)); r=bpy.context.object; paint(r,COL['accent']); r.select_set(False)
    keyv(r,'scale',[(0,(0,0,0)),(t0,(0,0,0)),(t0+0.3,(1.1,1.1,1.1)),(t0+0.5,(1,1,1)),(t0+2.6,(1,1,1)),(t0+2.9,(0,0,0))])
    for k,s_ in enumerate(ls):
        o=text(s_,20,(p[0],p[1]-110,-20+0+k*0),rgb=COL['white']); o.location=(p[0],p[1]-90,300-k*30); show(o,t0+0.4+k*0.3)
# AI 결과 카드 + 다시 읽어 검사
outs=['치수 표','공정표','NC','작업지시서']
for i,s_ in enumerate(outs):
    g=card(s_,'초안',(-300+i*200,-300,120),COL['accent'],w=160,h=70,tsize=22)
    keyv(g,'scale',[(0,(0,0,0)),(T(5)+0.3+i*0.3,(0,0,0)),(T(5)+0.5+i*0.3,(1,1,1))])
    keyv(g,'location',[(0,(0,0,230)),(T(5)+0.3+i*0.3,(0,0,230)),(T(5)+0.9+i*0.3,(-300+i*200,-300,120))])
scan=box((900,12,6),(0,-310,80),(0.4,1,0.5),name='scan')
keyv(scan,'location',[(0,(0,-310,-200)),(T(5)+2.6,(0,-310,-200)),(T(5)+2.7,(0,-310,80)),(E(5),(0,-310,170)),(E(5)+0.2,(0,-310,-200))])
# 문서 · 이력 (저장소)
for k in range(6):
    c=cube=box((50,50,50),(-250+k*100,-300,330),COL['sky'] if k<5 else (0.4,1,0.5),bevel=6,name='commit'); show(c,T(6)+0.3+k*0.3)
    if k: l=curve_line([(-250+(k-1)*100+25,-300,330),(-250+k*100-25,-300,330)],bevel=4,rgb=COL['white']); show(l,T(6)+0.3+k*0.3)
gt=text('바뀐 내용 = 저장소 이력',26,(0,-300,400),rgb=COL['white']); show(gt,T(6)+0.6)
cam,tgt=camera(35)
cam_keys(cam,tgt,[(0,(0,-1500,700),(0,100,200)),(T(1)+0.6,(0,-1300,560),(0,100,200)),(E(1),(80,-1250,540),(0,100,200))])
for i,t0,ls in tasks:
    p=ROLES[i][2]; cam_keys(cam,tgt,[(t0+0.4,(p[0]*0.7,p[1]-650,330),(p[0],p[1],170))]); sfx(t0,'whoosh',0.7)
cam_keys(cam,tgt,[(T(5)+0.6,(0,-1100,420),(0,-300,180)),(E(5),(60,-1050,400),(0,-300,180))])
cam_keys(cam,tgt,[(T(6)+0.6,(0,-1000,520),(0,-300,330)),(DUR,(80,-1050,540),(0,-300,330))])
handheld(cam,0.5)
finish('ch2',DUR)
