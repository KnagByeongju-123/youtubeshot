import sys,os; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from r3d import *
T,E,DUR,cs=chapter(4)
sc=setup(texture=True)
# 성형해석 화면(버링이 서는 과정) + 반복 계산 표 + 얇아짐 경고
FR=['S2_burring_00','S2_burring_04','S2_burring_08','S2_burring_12','S2_burring_16','S2_burring_22']
t0,t1=T(1)+0.3,E(3)
for i,f in enumerate(FR):
    o=image_plane(os.path.join(AI,f+'.png'),240,(-200,-i*0.2,0),name=f)
    a=t0+(t1-t0)*i/len(FR); b=t0+(t1-t0)*(i+1)/len(FR) if i<len(FR)-1 else None
    keyv(o,'scale',[(0,(0,0,0)),(max(0,a-0.01),(0,0,0)),(a,(1,1,1))]+([(b,(1,1,1)),(b+0.01,(0,0,0))] if b else []),interp='CONSTANT')
lb=text('기초 구멍 → 펀치로 넓히며 버링을 세움',18,(-200,-10,175),rgb=COL['white']); pop(lb,T(1)+0.2)
c=card('기초 피어싱 지름 = 버링 높이를 결정','',(-200,-10,-185),COL['accent'],w=380,h=50,tsize=18); pop(c,T(2)+0.2)
tb=table((170,-20,130),['회차','기초 구멍','버링 높이','판정'],[['1','Ø4.700','4.78','높음'],['2','Ø7.800','2.23','낮음'],['3','Ø5.646','3.97','맞음 ✔']],
         [-190,-130,-20,90],w=400,rh=40,size=18,t0=T(4)+0.2,dt=0.9)
pop(tb,T(3)+0.4)
th=image_plane(os.path.join(AI,'얇아짐_확대.png'),300,(-200,-6,0),name='thin'); pop(th,T(5))
w1=card('끝 두께 0.66 · 약 32 % 얇아짐','',(200,-35,-90),COL['red'],w=360,h=46,tsize=18); pop(w1,T(5)+0.3)
w2=card('갈라짐 위험 → 시험 타발로 확인','',(200,-35,-145),COL['red'],w=360,h=40,tsize=16); pop(w2,T(6)+0.2)
w3=card('높이 3.5 → 얇아짐 약 20 %','고객과 협의할 내용',(200,-35,-215),COL['accent'],w=340,h=70,tsize=18,ssize=13); pop(w3,T(7)+0.2)
cam,tgt=camera(35)
cam_keys(cam,tgt,[(0,(-200,-520,20),(-200,0,0)),(T(3)-0.3,(-180,-560,10),(-190,0,0)),(T(3)+0.6,(0,-860,0),(0,0,-10)),(T(5)-0.3,(0,-880,0),(0,0,-10)),
                  (T(5)+0.6,(0,-880,-20),(0,0,-20)),(DUR,(10,-890,-20),(0,0,-20))])
handheld(cam,0.4)
finish('ch4',DUR)
