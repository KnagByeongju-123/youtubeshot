import sys,os; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from g3d import *
T,E,DUR,cs=chapter(8)
sc=setup(texture=True); floor(extent=3200)
# 길과 세 관문 (지금 바로 · 단기 · 중기)
road=box((3000,180,6),(1200,0,3),(0.20,0.23,0.30),name='road'); show(road,0.1)
for k in range(30):
    d=box((50,10,7),(-250+k*100,0,4),COL['accent'],name='dash'); show(d,0.1+k*0.02)
G=[('지금 바로','샘플로 확인된 것',0,['치수 표 → 모델','구멍 NC','와이어 NC']),
   ('단기 1~2개월','사내 기계 값 채우기',1100,['조건표 · 보정값','실제 도면 1건']),
   ('중기 3~6개월','도구 넓히기',2200,['도면 직접 읽기','시뮬레이션','측정 통계'])]
for i,(nm,sub,x,items) in enumerate(G):
    for sx in (-1,1):
        p=box((30,30,320),(x,sx*120,160),(0.55,0.58,0.64),bevel=4); show(p,0.2+i*0.2)
    bm=box((280,30,40),(x,0,330),(0.95,0.75,0.25),bevel=4); show(bm,0.3+i*0.2)
    t=text(nm,28,(x,-20,330),rgb=COL['ink']); show(t,0.4+i*0.2)
    s_=text(sub,22,(x,-20,380),rgb=COL['white']); show(s_,T(i+1)+0.2)
    for k,it in enumerate(items):
        g=card(it,'',(x+260,-40,240-k*80),(0.4,1,0.5),w=230,h=60,tsize=20)
        keyv(g,'scale',[(0,(0,0,0)),(T(i+1)+0.6+k*0.5,(0,0,0)),(T(i+1)+0.9+k*0.5,(1,1,1))])
# 정리: AI 와 사람
SX=3300
ai=ai_orb((SX-250,0,220),60); spin(ai,0,DUR,1.5); keyv(ai,'scale',[(0,(0,0,0)),(T(4)-0.1,(0,0,0)),(T(4)+0.3,(1,1,1)),(T(5),(1,1,1)),(T(5)+0.3,(0,0,0))])
hu=person((SX+250,0,0),(0.62,0.42,0.95),name='human',scale=1.8); keyv(hu,'scale',[(0,(0,0,0)),(T(4)-0.1,(0,0,0)),(T(4)+0.3,(1.8,1.8,1.8)),(T(5),(1.8,1.8,1.8)),(T(5)+0.3,(0,0,0))])
a1=text('초안 · 계산 · 검사 · 문서',26,(SX-250,-80,360),rgb=COL['accent']); show(a1,T(4)+0.5,T(5))
a2=text('확정 · 승인',30,(SX+250,-80,360),rgb=COL['white']); show(a2,T(4)+2.0,T(5))
# 끝: 금형 세트 + 인사
parts,up,root=die_set((SX,600,145))
keyv(up,'location',[(0,(0,0,100)),(T(5),(0,0,100)),(DUR-0.3,(0,0,0))])
ty=text('들어 주셔서 감사합니다',44,(SX,450,520),rgb=COL['accent']); show(ty,T(5)+0.2)
cam,tgt=camera(35)
cam_keys(cam,tgt,[(0,(-600,-900,500),(0,0,200))])
for i,(nm,sub,x,items) in enumerate(G):
    cam_keys(cam,tgt,[(T(i+1)+0.1,(x-150,-750,330),(x+120,0,240)),(E(i+1)-0.2,(x-60,-720,320),(x+160,0,240))]); sfx(T(i+1)-0.25,'whoosh',0.8)
cam_keys(cam,tgt,[(T(4)+0.4,(SX,-1250,480),(SX,0,230)),(E(4),(SX+40,-1220,470),(SX,0,230))])
cam_keys(cam,tgt,[(T(5)+0.4,(SX-300,-650,480),(SX,600,260))])
orbit(cam,tgt,T(5)+0.4,DUR,(SX,600,260),1250,380,-104,-80,n=6)
handheld(cam,0.5)
finish('ch8',DUR)
