import sys,os; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from r3d import *
T,E,DUR,cs=chapter(10)
sc=setup()
# ESG Smart Factory · mold2 실적 → 이번 설계 값 → 비교 → 견적 초안 → 담당자 확인 → 정리
tt=card('향후 과제','금형비용 산출',(-330,-60,40),COL['accent'],w=420,h=110,tsize=40,ssize=26); pop(tt,T(1)+0.2,T(2)-0.4)
pn=box((640,8,420),(-330,10,40),(0.10,0.13,0.18),bevel=6); pop(pn,T(2)-0.2)
hd=box((640,9,50),(-330,4,225),COL['purple']); pop(hd,T(2)-0.2)
ht=text('ESG Smart Factory · mold2',26,(-330,-2,225),rgb=COL['white']); pop(ht,T(2))
st=text('금형비용 실적 (백데이터)',18,(-330,-2,180),rgb=COL['accent']); pop(st,T(2)+0.4)
vals=[0.55,0.8,0.42,0.68,0.9,0.5]
for i,v in enumerate(vals):
    z=130-i*55
    lb=text('실적 금형 %s'%'ABCDEF'[i],15,(-610,-4,z),rgb=COL['white'],align='LEFT'); pop(lb,T(2)+0.6+i*0.2)
    b=box((300*v,8,26),(-420+150*v,-2,z),COL['sky']); pop(b,T(3)+0.2+i*0.25)
nv=[('공정 수','10'),('부품 수','192'),('판 크기','962 × 210'),('프레스','100 톤')]
for i,(a,b) in enumerate(nv):
    c=card(a,b,(240,-40,190-i*80),COL['accent'],w=230,h=64,tsize=18,ssize=16); pop(c,T(4)+0.2+i*0.35)
ar=text('비교 →',22,(-10,-30,40),rgb=COL['accent']); pop(ar,T(4)+1.6)
es=card('견적 초안','도면 접수 단계에서 바로',(240,-60,-170),(0.35,1,0.45),w=320,h=80,tsize=26,ssize=16); pop(es,T(5)+0.2)
pe=person((470,-40,-280),scale=1.4); pop(pe,T(6)+0.1)
ck=card('담당자 확인 · 결정','',(470,-60,-80),COL['purple'],w=230,h=50,tsize=18); pop(ck,T(6)+0.3)
f1=card('AI','정리 · 계산 · 해석 · 검사',(1800,0,20),COL['sky'],w=360,h=90,tsize=30,ssize=18); pop(f1,T(7)+0.2)
f2=card('사람','확정 · 승인',(2200,0,20),COL['accent'],w=360,h=90,tsize=30,ssize=18); pop(f2,T(7)+0.7)
ty=text('들어 주셔서 감사합니다',34,(2000,0,160),rgb=COL['white']); pop(ty,T(8)+0.1)
cam,tgt=camera(32)
cam_keys(cam,tgt,[(0,(-330,-700,60),(-330,0,40)),(T(2)-0.4,(-330,-760,60),(-330,0,40)),(T(3)+1.4,(-300,-780,40),(-330,0,40)),(T(4)-0.1,(-300,-790,40),(-330,0,40)),
                  (T(4)+0.7,(-40,-1000,30),(-40,0,10)),(T(7)-0.3,(-20,-1020,20),(-20,0,0)),(T(7)+0.05,(2000,-900,120),(2000,0,80)),(DUR,(2020,-920,125),(2000,0,80))]); sfx(T(7)-0.3,'whoosh',0.8)
handheld(cam,0.4)
finish('ch10',DUR)
