import sys,os; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from s3d import *
T,E,DUR,cs=chapter(7)
sc=setup(texture=True)
floor(extent=2600)
S=3.0
def r_at(z):
    best=0
    for (r1,z1),(r2,z2) in zip(PUNCH,PUNCH[1:]):
        if min(z1,z2)<=z<=max(z1,z2) and z2!=z1: best=max(best,r1+(r2-r1)*(z-z1)/(z2-z1))
        elif z1==z2 and abs(z-z1)<0.5: best=max(best,r1,r2)
    return best
# 1) 쇠막대 → 선반 (원판 40장이 공구가 지나가면 줄어듦)
LX=0
lathe=empty('lathe',(LX,0,40))
N=40; R0=20.5
discs=[]
tA=T(3)+0.3; tB=T(3)+4.0
for i in range(N):
    z0=60*i/N; z1=60*(i+1)/N; zm=(z0+z1)/2; rf=max(r_at(z0+0.01),r_at(zm),r_at(z1-0.01))
    d=cyl(R0*S,(z1-z0)*S+0.2,(0,0,zm*S),(0.66,0.68,0.72),seg=64,name='disc'); d.parent=lathe
    tp=tA+(tB-tA)*(1-zm/60)
    k=rf/R0
    keyv(d,'scale',[(0,(1,1,1)),(tp,(1,1,1)),(tp+0.25,(k,k,1))])
    discs.append(d)
spin(lathe,T(1),T(4),turns=40)
tool=box((40,22,14),(0,0,0),COL['accent'],name='tool'); tip=cyl(4,20,(0,0,0),COL['white'],seg=6,rot=(0,math.radians(90),0)); tip.parent=tool; tip.location=(-28,0,0)
keyv(tool,'location',[(0,(LX+R0*S+120,0,40+60*S)),(tA-0.5,(LX+R0*S+120,0,40+60*S)),(tA,(LX+18*S+32,0,40+60*S))])
for j in range(13):
    z=60-j*5; tt=tA+(tB-tA)*(j/12)
    key(tool,'location',tt,(LX+r_at(z)*S+32,0,40+z*S))
key(tool,'location',tB+0.5,(LX+R0*S+140,0,40))
t1=text('가공',44,(LX,-80,290),rgb=COL['accent']); show(t1,T(1)+0.1,E(1)+0.2)
t3=text('선반: 돌리며 바깥 깎기',26,(LX,-80,290),rgb=COL['white']); show(t3,T(3)+0.2,E(3)-2.0)
# 연삭 숫돌
wh=empty('wheel',(LX-220,0,40+30*S))
w=cyl(90,40,(0,0,0),(0.85,0.85,0.80),seg=64,rot=(0,0,0)); w.parent=wh
spin(wh,0,DUR,turns=30)
keyv(wh,'location',[(0,(LX-600,0,40+30*S)),(E(3)-2.2,(LX-600,0,40+30*S)),(E(3)-1.6,(LX-(15*S+90),0,40+20*S)),(E(3)-0.4,(LX-(15*S+90),0,40+45*S)),(E(3)+0.2,(LX-600,0,40+45*S))])
t3b=text('연삭: 지름 Ø30 정밀 맞춤',26,(LX,-80,290),rgb=COL['sky']); show(t3b,E(3)-2.0,E(3)+0.3)
# 2) CAM 공구 경로 (STEP → 경로)
cpath=[]
for j in range(220):
    a=j*0.35; z=60-60*j/220
    rr=r_at(z)+3
    cpath.append((LX+rr*S*math.cos(a),rr*S*math.sin(a),40+z*S))
cp=curve_line(cpath,bevel=0.9,rgb=(0.4,1,0.5),name='cam'); draw_on(cp,T(2)+0.8,E(2)-0.3)
keyv(cp,'scale',[(0,(1,1,1)),(E(2),(1,1,1)),(E(2)+0.3,(0,0,0))]); cp.location=(0,0,0)
stp=empty('stp',(LX-280,0,260)); b=box((80,10,100),(0,0,0),COL['paper'],bevel=4); b.parent=stp; tx=text('STEP',20,(0,-8,0),rgb=COL['ink']); tx.parent=stp
keyv(stp,'scale',[(0,(0,0,0)),(T(2)+0.1,(0,0,0)),(T(2)+0.4,(1,1,1)),(E(2),(1,1,1)),(E(2)+0.3,(0,0,0))])
t2=text('CAM: 공구가 지나갈 길 계산',26,(LX,-80,290),rgb=(0.4,1,0.5)); show(t2,T(2)+0.6,E(2))
# 3) 머시닝센터: 판에 구멍
MX=800
plate=box((440,200,40),(MX,0,20),COL['plate'],bevel=2,name='plate'); show(plate,T(4)-0.3)
HOLES=[(-120,0,31),(0,0,37),(120,0,31),(-170,-70,8.5),(170,-70,8.5),(-170,70,8.5),(170,70,8.5)]
mill=empty('mill',(MX,0,300))
sp=cyl(30,90,(0,0,60),(0.5,0.52,0.58)); sp.parent=mill
em=cyl(8,70,(0,0,-15),COL['post']); em.parent=mill
keyv(mill,'scale',[(0,(0,0,0)),(T(4)-0.3,(0,0,0)),(T(4),(1,1,1))])
order=[3,4,0,1,2,5,6]
tA4=T(4)+0.3; dt=(E(4)+0.8-tA4)/len(order)
for k,i in enumerate(order):
    x,y,d=HOLES[i]; t0=tA4+k*dt
    key(mill,'location',t0,(MX+x,y,140)); key(mill,'location',t0+dt*0.45,(MX+x,y,75)); key(mill,'location',t0+dt*0.9,(MX+x,y,140))
    h=cyl(d,42,(MX+x,y,21),(0.10,0.11,0.14),seg=48,name='hole'); keyv(h,'scale',[(0,(0,0,0)),(t0+dt*0.3,(0,0,0)),(t0+dt*0.45,(1,1,1))])
t4=text('머시닝센터: 구멍 · 홈',26,(MX,-80,260),rgb=COL['white']); show(t4,T(4)+0.1,E(4)+0.5)
# 4) 와이어 방전: 다이 구멍
WX=1600
blk=box((260,260,90),(WX,0,45),COL['die'],bevel=2,name='blk'); show(blk,T(5)-0.4)
rr=15.6*S*1.5
wire=cyl(1.4,520,(WX+rr,0,60),COL['accent'],seg=8,name='wire')
keyv(wire,'scale',[(0,(0,0,0)),(T(5)-0.2,(0,0,0)),(T(5)+0.2,(1,1,1))])
tW0=T(5)+0.8; tW1=E(5)-0.6
for j in range(25):
    a=2*math.pi*j/24; key(wire,'location',tW0+(tW1-tW0)*j/24,(WX+rr*math.cos(a),rr*math.sin(a),60))
for fc_ in wire.animation_data.action.fcurves:
    if fc_.data_path=='location':
        for kp in fc_.keyframe_points: kp.interpolation='LINEAR'
cut=curve_line([(WX+rr*math.cos(2*math.pi*j/96),rr*math.sin(2*math.pi*j/96),91) for j in range(97)],bevel=1.6,rgb=COL['red'],name='cut'); draw_on(cut,tW0,tW1)
slug=cyl(rr-1.5,86,(WX,0,45),(0.20,0.62,0.30),seg=64,name='slug')
keyv(slug,'location',[(0,(WX,0,45)),(tW1+0.2,(WX,0,45)),(tW1+1.0,(WX,0,-80))])
hole2=cyl(rr,1,(WX,0,90.6),(0.08,0.09,0.11),seg=64); keyv(hole2,'scale',[(0,(0,0,0)),(tW1+0.3,(0,0,0)),(tW1+0.6,(1,1,1))])
t5=text('와이어 방전: 가는 쇠줄 + 전기',26,(WX,-80,260),rgb=COL['white']); show(t5,T(5)+0.2,E(5)+0.4)
# 5) 펀치-다이 틈 (단면)
CX=2400
pn=box((150,120,220),(CX,0,330),COL['punch'],name='cp'); show(pn,T(6)-0.4)
dl=box((200,120,140),(CX-183,0,70),COL['die'],name='cdl'); show(dl,T(6)-0.4)
dr=box((200,120,140),(CX+183,0,70),COL['die'],name='cdr'); show(dr,T(6)-0.4)
keyv(pn,'location',[(0,(CX,0,330)),(T(6),(CX,0,330)),(T(6)+1.2,(CX,0,200))])
gap=text('틈 = 판 두께의 8 %',20,(CX+175,-80,250),rgb=COL['accent']); show(gap,T(6)+1.3)
gap2=text('한쪽 약 0.05 mm',18,(CX+175,-80,222),rgb=COL['white']); show(gap2,T(6)+2.4)
for x in (CX+75,CX+83): 
    l=curve_line([(x,-62,150),(x,-62,165)],bevel=0.8,rgb=COL['red']); show(l,T(6)+1.5)
ar=curve_line([(CX+40,-62,160),(CX+118,-62,160)],bevel=1.2,rgb=COL['red']); show(ar,T(6)+1.5)
# 6) AI 작업표
AX=3200
pnl=box((520,6,380),(AX,10,230),(0.12,0.15,0.20),bevel=4,name='sheet'); show(pnl,T(7)-0.3)
ht=text('AI 가 정리한 작업표',30,(AX,0,385),rgb=COL['accent']); show(ht,T(7))
rows=['1  선반 · 바깥 깎기','2  연삭 · Ø30 h6 맞춤','3  머시닝센터 · 구멍 · 홈','4  와이어 방전 · 다이 구멍','5  공구 · 조건 점검']
for i,s_ in enumerate(rows):
    o=text(s_,24,(AX-230,0,320-i*55),rgb=COL['white'],bold=False,align='LEFT'); show(o,T(7)+0.4+i*0.6)
    okk=text('OK',22,(AX+200,0,320-i*55),rgb=(0.4,1,0.5)); show(okk,T(7)+2.6+i*0.7)
# 카메라
cam,tgt=camera(35)
cam_keys(cam,tgt,[(0,(LX-200,-900,520),(LX,0,140)),(T(1)+2,(LX-120,-760,360),(LX,0,140))])
cam_keys(cam,tgt,[(T(2)+0.6,(LX+150,-720,330),(LX,0,150)),(E(2),(LX+220,-660,300),(LX,0,150))])
cam_keys(cam,tgt,[(T(3)+0.4,(LX+120,-620,240),(LX,0,140)),(E(3)-2.0,(LX+60,-600,240),(LX,0,140)),(E(3),(LX-80,-620,250),(LX-60,0,150))])
cam_keys(cam,tgt,[(T(4)+0.6,(MX-100,-700,420),(MX,0,80)),(E(4)+0.4,(MX+80,-680,400),(MX,0,80))])
cam_keys(cam,tgt,[(T(5)+0.6,(WX-150,-620,380),(WX,0,90)),(E(5),(WX+120,-600,360),(WX,0,90))])
cam_keys(cam,tgt,[(T(6)+0.6,(CX-20,-700,300),(CX,0,230)),(T(6)+2.4,(CX+40,-330,190),(CX+70,0,170)),(E(6),(CX+50,-320,185),(CX+75,0,165))])
cam_keys(cam,tgt,[(T(7)+0.7,(AX,-820,260),(AX,0,240)),(DUR,(AX+40,-860,270),(AX,0,240))])
handheld(cam,0.5)
finish('ch7',DUR)
