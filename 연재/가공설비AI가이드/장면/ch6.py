import sys,os; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from g3d import *
import random
T,E,DUR,cs=chapter(6)
sc=setup(texture=True); floor(extent=2600)
WX=0
wg,up,TZ=wire_edm((WX,0,0))
blk=box((240,200,60),(WX,-10,TZ+30),COL['die'],bevel=2,name='blk')
# 윤곽 (사각 다이 구멍 + 둥근 모서리)
def contour(w,h,r,z,n=6):
    pts=[]
    for cx,cy,a0 in ((w/2-r,h/2-r,0),(-w/2+r,h/2-r,90),(-w/2+r,-h/2+r,180),(w/2-r,-h/2+r,270)):
        for k in range(n+1):
            a=math.radians(a0+90*k/n); pts.append((WX+cx+r*math.cos(a),-10+cy+r*math.sin(a),z))
    pts.append(pts[0]); return pts
C=contour(120,90,14,TZ+61)
# 1) 가는 쇠줄 (위아래 가이드 사이)
wire=cyl(1.3,400,(WX,-10,TZ+200),COL['accent'],seg=8,name='wire')
keyv(wire,'scale',[(0,(0,0,0)),(T(1)+0.2,(0,0,0)),(T(1)+0.5,(1,1,1))])
wt=text('실 지름 Ø0.25',26,(WX+220,-150,520),rgb=COL['accent']); show(wt,T(1)+0.4,E(1)+0.4)
# 2) 윤곽 추출 (입체에서 떠오름) + 시작 구멍 + 진입 위치
cl=curve_line(C,bevel=2.0,rgb=(0.4,1,0.5),name='contour'); draw_on(cl,T(2)+0.3,T(2)+2.0)
keyv(cl,'location',[(0,(0,0,120)),(T(2)+2.0,(0,0,120)),(T(2)+2.8,(0,0,0))])
sh=cyl(4,62,(WX,-10,TZ+30),(0.06,0.07,0.09),seg=24,name='starthole'); keyv(sh,'scale',[(0,(0,0,0)),(T(2)+3.0,(0,0,0)),(T(2)+3.3,(1,1,1))])
en=curve_line([(WX,-10,TZ+62),(WX+60,-10,TZ+62)],bevel=2.5,rgb=COL['red']); show(en,T(2)+3.6)
et=text('중요한 면을 피해 진입',18,(WX+60,-150,TZ+190),rgb=COL['red']); show(et,T(2)+3.8,E(2)+0.4)
# 3) NC → 장비 형식 변환 → 침범 검사
ncA=card('NC (G41)','윤곽에서 생성',(WX+460,-80,500),COL['white'],w=200,h=80,tsize=22)
ncB=card('장비 형식','D→H · 조건→C',(WX+700,-80,500),COL['sky'],w=200,h=80,tsize=22)
for i,g in enumerate((ncA,ncB)): keyv(g,'scale',[(0,(0,0,0)),(T(3)+0.2+i*1.2,(0,0,0)),(T(3)+0.5+i*1.2,(1,1,1)),(E(4)+0.3,(1,1,1)),(E(4)+0.6,(0,0,0))])
ar=curve_line([(WX+560,-80,500),(WX+600,-80,500)],bevel=4,rgb=COL['accent']); show(ar,T(3)+1.0,E(4)+0.6)
plate=curve_line(contour(240,200,1,TZ+62,1),bevel=2.0,rgb=COL['sky'],name='plate'); show(plate,T(3)+2.6,E(3)+0.5)
ck=text('판 침범 없음 · 보정 방향 OK',22,(WX+200,-150,TZ+190),rgb=(0.4,1,0.5)); show(ck,T(3)+3.2,E(3)+0.5)
# 4) 조건 · 보정 + 드라이런 (불꽃 없이 한 바퀴)
cd=table((WX+580,-80,380),['단계','조건','보정'],[['1차','C001','H001'],['2차','C002','H002'],['3차','C003','H003']],[-130,-20,80],w=300,t0=T(4)+0.4,dt=0.4,size=13)
keyv(cd,'scale',[(0,(0,0,0)),(T(4)+0.1,(0,0,0)),(T(4)+0.3,(1,1,1)),(E(4)+0.3,(1,1,1)),(E(4)+0.6,(0,0,0))])
dr=text('드라이런',30,(WX,-150,TZ+130),rgb=COL['accent']); show(dr,T(4)+1.6,E(4)+0.2)
# 와이어가 윤곽을 따라감 (드라이런 → 가공은 불꽃)
tA=T(4)+1.8; tB=E(4)-0.2; tC=T(7)+0.2; tD=E(7)-0.3
wk=[(0,(WX,-10,TZ+200)),(tA-0.2,(WX,-10,TZ+200)),(tA,(C[0][0],C[0][1],TZ+200))]
for k,p in enumerate(C): wk.append((tA+(tB-tA)*k/(len(C)-1),(p[0],p[1],TZ+200)))
wk.append((tC-0.2,(C[0][0],C[0][1],TZ+200)))
for k,p in enumerate(C): wk.append((tC+(tD-tC)*k/(len(C)-1),(p[0],p[1],TZ+200)))
keyv(wire,'location',wk)
for fc in wire.animation_data.action.fcurves:
    if fc.data_path=='location':
        for kp in fc.keyframe_points: kp.interpolation='LINEAR'
random.seed(4)
for i in range(110):
    ti=tC+(tD-tC)*i/110; k=int((len(C)-1)*i/110); p=C[k]
    s_=sphere(random.uniform(2,3.5),(p[0]+random.uniform(-3,3),p[1]+random.uniform(-3,3),TZ+random.uniform(5,58)),(1,0.92,0.45),name='spark')
    keyv(s_,'scale',[(0,(0,0,0)),(ti-0.05,(0,0,0)),(ti+0.04,(1,1,1)),(ti+0.16,(0,0,0))])
kerf=curve_line(C,bevel=1.6,rgb=(0.03,0.03,0.04),name='kerf'); kerf.location=(0,0,0.6); draw_on(kerf,tC,tD)
# 5~6) 핀 구멍 측정 → 보정 계산
pin=cyl(16,120,(WX+60,-200,TZ+200),(0.85,0.86,0.90),seg=32,name='pin')
keyv(pin,'scale',[(0,(0,0,0)),(T(5)+0.2,(0,0,0)),(T(5)+0.5,(1,1,1))])
keyv(pin,'location',[(T(5)+0.5,(WX+300,-200,TZ+200)),(T(5)+1.6,(WX+300,-200,TZ+120))])
m1=text('목표 Ø8.008',30,(WX+420,-150,560),rgb=COL['white']); show(m1,T(6)+0.3,E(6)+0.3)
m2=text('측정 Ø8.004',30,(WX+420,-150,510),rgb=COL['red']); show(m2,T(6)+1.4,E(6)+0.3)
m3=text('보정 = 차이 ÷ 2 → 구멍을 키움',26,(WX+420,-150,460),rgb=(0.4,1,0.5)); show(m3,T(6)+3.0,E(6)+0.3)
# 7) 작업자: 가공 · 실 결선 · 슬러그 제거
wkp=person((WX-380,-200,0),(0.95,0.60,0.25),name='worker',scale=1.4); keyv(wkp,'scale',[(0,(0,0,0)),(T(7)-0.1,(0,0,0)),(T(7)+0.3,(1.4,1.4,1.4))])
slug=box((118,88,58),(WX,-10,TZ+30),(0.18,0.55,0.30),name='slug')
keyv(slug,'location',[(0,(WX,-10,TZ+30)),(tD,(WX,-10,TZ+30)),(tD+0.6,(WX-200,-150,TZ+30))])
keyv(slug,'scale',[(0,(0,0,0)),(tC-0.1,(0,0,0)),(tC,(1,1,1))])
wt2=text('가공 · 실 결선 · 슬러그 제거 = 작업자',24,(WX,-150,560),rgb=COL['accent']); show(wt2,T(7)+0.6)
cam,tgt=camera(35)
cam_keys(cam,tgt,[(0,(WX-800,-1200,800),(WX,0,300)),(T(1)+0.5,(WX-200,-700,420),(WX,0,300)),(E(1),(WX-100,-720,430),(WX+60,0,330))])
cam_keys(cam,tgt,[(T(2)+0.4,(WX+60,-420,TZ+260),(WX,-10,TZ+60)),(E(2),(WX+120,-380,TZ+230),(WX,-10,TZ+60))])
cam_keys(cam,tgt,[(T(3)+0.4,(WX+350,-950,450),(WX+400,0,380)),(E(3),(WX+330,-900,430),(WX+300,0,320))])
cam_keys(cam,tgt,[(T(4)+0.4,(WX+300,-900,420),(WX+300,0,330)),(E(4),(WX+150,-500,TZ+250),(WX,-10,TZ+60))])
cam_keys(cam,tgt,[(T(5)+0.3,(WX+250,-650,TZ+260),(WX+300,-200,TZ+150)),(E(6),(WX+380,-900,450),(WX+400,-150,450))])
for j in range(9):
    t=tC+(tD-tC)*j/8; k=int((len(C)-1)*j/8); p=C[k]
    cam_keys(cam,tgt,[(t,(p[0]+(p[0]-WX)*1.8+30,p[1]+(p[1]+10)*1.8-120,TZ+120),(p[0],p[1],TZ+40))])
cam_keys(cam,tgt,[(E(7)+0.2,(WX-100,-900,420),(WX-100,0,250)),(DUR,(WX-80,-920,430),(WX-100,0,250))])
handheld(cam,0.5)
finish('ch6',DUR)
