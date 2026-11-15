import sys,os; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from r3d import *
T,E,DUR,cs=chapter(1)
sc=setup(texture=True)
# 가정 고객 도면 → AI 가 사양 표 · 질문 목록 → 비공개 저장소
d=image_plane(os.path.join(AI,'고객도면.png'),400,(0,0,0)); pop(d,0.3)
tb=table((330,-20,120),['항목','내용'],[['품명','리테이너 (스프링 코킹)'],['재질','SPCC  t1.4'],['링','안 Ø50 · 바깥 Ø60 정도'],['버링','14개 같은 간격, 높이 4'],['버링 지름','안 · 바깥 : 미지정']],
         [-170,-60],w=360,rh=34,size=16,t0=T(4)+0.3,dt=0.45)
for o in [tb]: pop(o,T(4)+0.1)
tb.location.x=430
ai=ai_orb((260,-60,170),r=26); pop(ai,T(4)-0.4); spin(ai,0,DUR,2.0)
q=card('질문 목록','버링 안지름 ?  ·  버링 바깥지름 ?',(430,-60,-150),COL['red'],w=380,h=80,tsize=22,ssize=16); pop(q,T(5)+0.2)
lk=card('비공개 저장소','밖으로 나가는 자료엔 도면 번호 없음',(0,-80,-180),COL['purple'],w=430,h=80,tsize=22,ssize=16); pop(lk,T(6)+0.2)
hl=[('SPCC t1.4',T(2)),('버링 14 · 높이 4',T(3))]
for i,(s,t) in enumerate(hl):
    c=card(s,'',(-120+i*240,-40,190),COL['accent'],w=220,h=56,tsize=20); pop(c,t+0.2,T(4)-0.3)
cam,tgt=camera(35)
cam_keys(cam,tgt,[(0,(0,-620,40),(0,0,10)),(T(2),(-40,-560,60),(0,0,30)),(T(4)-0.2,(-20,-600,40),(20,0,20)),(T(4)+0.8,(220,-860,40),(220,0,10)),
                  (T(6)-0.2,(240,-880,20),(220,0,0)),(T(6)+0.6,(140,-900,-40),(150,0,-60)),(DUR,(150,-920,-40),(150,0,-60))])
handheld(cam,0.4)
finish('ch1',DUR)
