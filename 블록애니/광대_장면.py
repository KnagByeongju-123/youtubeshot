"""《줄 끊긴 광대》 장면 모형 + 움직임 (세트 A, 0~45초) → 연재/줄끊긴광대/장면/A_무대.bbmodel, 세트정보.json(줄 8개: 시간에 따라 끊김)
   실제 세계 좌표, 위치 움직임은 x 를 뒤집어 넣음.  yaw: 0 = -z(객석), 180 = +z
   방: 무대(0,0,0) 폭 70·높이 8, 뒷벽 z 40 (창 x 22..52, 문 x -52..-34), 바깥 마당 z > 40.  조종 막대 y 60"""
import sys, os, json, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 광대인물 import *
from 블록인물 import move
OUT=sys.argv[1] if len(sys.argv)>1 else '/home/user/youtubeshot/연재/줄끊긴광대/장면'
os.makedirs(OUT,exist_ok=True)
L=45.0; random.seed(4)
M=Model(512); palette_all(M)
M.swatch('floor',wood_fn((175,130,85),(140,100,62),61),4); M.swatch('wall',(205,190,165),5); M.swatch('wall_d',(180,165,140),5)
M.swatch('grass',(115,170,82),10); M.swatch('grass_d',(100,155,72),10); M.swatch('frame',(250,250,245),2)
M.swatch('trunk',(115,85,55),5); M.swatch('leaf',(86,150,72),14)
A=Anim(L); top=[]
X=lambda n,fr,to,col,**f: M.cube(n,fr,to,col,**f)
def P(g, pts, interp='linear'): A.add(g,'position',[(t,(-v[0],v[1],v[2])) for t,v in pts],interp)
def R(g, pts, interp='linear'): A.add(g,'rotation',pts,interp)
def show(g, spans, eps=0.02):
    pts=[(0,0)]
    for a,b in spans: pts+= [(max(0,a-eps),0),(a,1),(b,1),(b+eps,0)]
    A.add(g,'scale',[(t,(v,v,v)) for t,v in pts])
def yaw(g, pts, interp='linear'): R(g,[(t,(0,y,0)) for t,y in pts],interp)
def part(g, name): return find(g, g['name'].replace('root',name))
def walk(p, t0, t1, amp=24, period=0.7, arms=True):
    legL,legR,armL,armR=[part(p,n) for n in ('leg_left','leg_right','arm_left','arm_right')]
    t=t0; s=1; pts=[]
    while t<t1-1e-6: pts.append((t+period/4,s)); t+=period/2; s=-s
    for g,sg in [(legL,1),(legR,-1)]+([(armL,-1),(armR,1)] if arms else []):
        R(g,[(t0,(0,0,0))]+[(tt,(sg*ss*amp,0,0)) for tt,ss in pts if tt<t1]+[(t1,(0,0,0))],'catmullrom')

# ---------------- 방·무대·바깥 ----------------
W=[X('far',[-3000,-20,-3000],[3000,-0.4,3000],'grass')]
W+= [X('floor',[-90,-1,-60],[90,0,40],'floor')]
# 뒷벽(z 40~42): 창 구멍 x 22..52 y 18..44, 문 구멍 x -52..-34 y 0..30
WZ=40
for a,b,y0,y1 in [(-90,-52,0,70),(-34,40,0,70),(70,90,0,70),(-52,-34,30,70),(40,70,0,18),(40,70,44,70)]:   # 창은 무대 뒤 커튼에 가리지 않게 x 40..70
    W.append(X('wall_b',[a,y0,WZ],[b,y1,WZ+2],'wall'))
W+= [X('win_f1',[39,17,WZ-0.4],[71,18,WZ+2.2],'frame'), X('win_f2',[39,44,WZ-0.4],[71,45,WZ+2.2],'frame'),
     X('win_f3',[39,17,WZ-0.4],[40,45,WZ+2.2],'frame'), X('win_f4',[70,17,WZ-0.4],[71,45,WZ+2.2],'frame'), X('win_m',[54.5,18,WZ+0.6],[55.5,44,WZ+1.4],'frame'),
     X('wall_l',[-92,0,-60],[-90,70,42],'wall_d'), X('wall_r',[90,0,-60],[92,70,42],'wall_d')]
for x in range(-200,240,40):   # 바깥 마당
    for z in range(42,200,40): W.append(X('g',[x,-1.5,z],[x+40,0,z+40],'grass' if ((x+z)//40)%2 else 'grass_d'))
for i,(x,z,h) in enumerate([(80,120,30),(-110,110,34),(10,150,28),(140,70,26)]):
    W+= [X('t',[x-2.5,0,z-2.5],[x+2.5,h,z+2.5],'trunk'), X('l',[x-11,h-5,z-11],[x+11,h+12,z+11],'leaf')]
top.append(M.group('world',[0,0,0],W))
door=M.group('door',[-52,0,WZ],[X('door_p',[-52,0,WZ-1.2],[-34,30,WZ-0.4],'bar'), X('door_k',[-37,14,WZ-2.0],[-35.6,15.4,WZ-1.2],'gold')])
top.append(door); R(door,[(0,(0,0,0)),(34.0,(0,0,0)),(35.0,(0,-100,0)),(45,(0,-100,0))])   # 문을 밀고 나감
st=stage(M,'st_'); top.append(st)
SH=8   # 무대 높이

# ---------------- 조종 막대·줄 ----------------
BY=60
bar=control_bar(M,'bar_',BY); top.append(bar)
dang={}
for n,(x,z) in {'hl':(8.5,0),'hr':(-8.5,0),'kl':(2.5,-5.5),'kr':(-2.5,-5.5)}.items():
    g=M.group('dangle_'+n,[x,BY-22,z],[]); bar['children'].append(g); dang[n]=g
ropes=M.group('ropes',[0,0,0],[M.cube(f'rope_{i}',[-0.22,-0.22,0],[0.22,0.22,1],'rope') for i in range(8)]); top.append(ropes)
# 공연(0~8): 막대가 위아래로 흔들리고 기울어짐 → 광대가 따라 춤춤
bp=[(0,(0,0,0))]; br=[(0,(0,0,0))]
for k in range(16):
    t=0.25+k*0.5; s_=1 if k%2==0 else -1
    bp.append((t,(0,3 if s_>0 else -1,0))); br.append((t,(0,0,12*s_)))
bp+= [(8.0,(0,0,0)),(9.0,(0,-6,0)),(45,(0,-6,0))]; br+= [(8.0,(0,0,0)),(45,(0,0,0))]
P(bar,bp,'catmullrom'); R(bar,br,'catmullrom')
# 끊긴 줄 끝은 흔들림
CUT={'hl':15.6,'hr':19.2,'kl':22.4,'kr':25.4}
for n,tc in CUT.items():
    sw=[(0,(0,0,0)),(tc,(0,0,0))]; t=tc+0.3; a=28; s_=1
    while t<45: sw.append((t,(a*s_,0,a*0.4*s_))); a=max(4,a*0.82); t+=0.7; s_=-s_
    R(dang[n],sw,'catmullrom')

# ---------------- 광대 ----------------
CS=1.0
cl=clown(M,'cl_',CS); top.append(cl)
CB,CH,CAL,CAR,CLL,CLR=[part(cl,n) for n in ('body','head','arm_left','arm_right','leg_left','leg_right')]
# 0~8 춤 (줄에 당겨짐): 몸 들썩·팔 번갈아 들기·다리 차기
P(cl,[(0,(0,SH,0)),(8.0,(0,SH,0))])
yaw(cl,[(0,0),(8.0,0)])
bob=[(0,(0,SH,0))]; armL=[(0,(0,0,0))]; armR=[(0,(0,0,0))]; legL=[(0,(0,0,0))]; legR=[(0,(0,0,0))]; bodyR=[(0,(0,0,0))]
for k in range(16):
    t=0.25+k*0.5; s_=1 if k%2==0 else -1
    bob.append((t,(0,SH+(1.2 if s_>0 else 0),0)))
    armL.append((t,(0,0,95 if s_>0 else 35))); armR.append((t,(0,0,-35 if s_>0 else -95)))
    legL.append((t,(-35 if s_>0 else 0,0,0))); legR.append((t,(0 if s_>0 else -35,0,0)))
    bodyR.append((t,(0,0,8*s_)))
P(cl,bob,'catmullrom'); R(CAL,armL,'catmullrom'); R(CAR,armR,'catmullrom'); R(CLL,legL,'catmullrom'); R(CLR,legR,'catmullrom'); R(CB,bodyR,'catmullrom')
R(CH,[(0,(0,0,0)),(2,(0,0,10)),(4,(0,0,-10)),(6,(0,0,10)),(8,(0,0,0))],'catmullrom')
# 8~26 줄에 걸린 채 주저앉음 (무대 위, 다리 앞으로)
SIT=SH-(12*CS-1.6)
P(cl,[(8.0,(0,SH,0)),(9.0,(0,SIT,0)),(28.0,(0,SIT,0))])
for lg in (CLL,CLR): R(lg,[(8.0,(0,0,0)),(9.0,(-85,0,0))])
R(CB,[(8.0,(0,0,0)),(9.0,(14,0,0))])
R(CH,[(8.0,(0,0,0)),(9.0,(30,0,0)),(10.5,(10,30,0)),(12.5,(10,30,0)),(13.2,(25,0,0))],'catmullrom')   # 창밖을 바라봄
# 줄이 팔·다리를 들어 올린 채 → 끊기면 툭 떨어짐
R(CAL,[(8.0,(0,0,0)),(9.0,(0,0,55)),(CUT['hl'],(0,0,55)),(CUT['hl']+0.25,(0,0,0))])
R(CAR,[(8.0,(0,0,0)),(9.0,(0,0,-55)),(CUT['hr'],(0,0,-55)),(CUT['hr']+0.25,(0,0,0))])
R(CLL,[(9.0,(-85,0,0)),(CUT['kl'],(-85,0,0)),(CUT['kl']+0.05,(-95,0,0)),(CUT['kl']+0.3,(-90,0,0))])
R(CLR,[(9.0,(-85,0,0)),(CUT['kr'],(-85,0,0)),(CUT['kr']+0.05,(-95,0,0)),(CUT['kr']+0.3,(-90,0,0))])
R(CH,[(CUT['hl']-0.4,(25,0,0)),(CUT['hl']+0.3,(20,30,0)),(17.5,(20,30,0)),(CUT['hr']+0.3,(20,-30,0)),(21.0,(25,0,0)),(26.0,(30,0,0)),(26.8,(-10,0,0)),(28.0,(-10,0,0))],'catmullrom')
R(CB,[(25.6,(14,0,0)),(26.2,(28,0,0)),(27.0,(10,0,0)),(28.0,(0,0,0))],'catmullrom')   # 마지막 줄이 끊기자 털썩
# 28~35 일어나다 넘어지고 다시 일어나 비틀비틀 걸어 무대를 내려옴
P(cl,[(28.0,(0,SIT,0)),(28.8,(0,SH,0)),(29.3,(0,SH,0)),(29.8,(0,SIT,0)),(30.6,(0,SIT,0)),(31.4,(0,SH,0)),
      (33.0,(0,SH,-14)),(33.5,(0,SH+2,-20)),(34.0,(0,0,-25)),(35.0,(-24,0,-27))],'catmullrom')   # 무대 앞으로 뛰어내려 왼쪽으로 (무대 속을 지나지 않게)
for lg in (CLL,CLR): R(lg,[(28.0,(-90,0,0)),(28.8,(0,0,0)),(29.3,(0,0,0)),(29.8,(-90,0,0)),(30.6,(-90,0,0)),(31.4,(0,0,0))])
R(CB,[(28.6,(0,0,0)),(29.1,(0,0,-14)),(29.5,(-20,0,8)),(29.8,(10,0,0)),(31.4,(0,0,0)),(31.8,(0,0,10)),(32.4,(0,0,-10)),(33.0,(0,0,6)),(34.0,(0,0,0))],'catmullrom')
R(CAL,[(28.4,(0,0,0)),(28.8,(0,0,40)),(29.8,(0,0,10)),(31.4,(0,0,45)),(33.0,(0,0,30)),(34.0,(0,0,0))],'catmullrom')   # 균형 잡기
R(CAR,[(28.4,(0,0,0)),(28.8,(0,0,-40)),(29.8,(0,0,-10)),(31.4,(0,0,-45)),(33.0,(0,0,-30)),(34.0,(0,0,0))],'catmullrom')
walk(cl,31.4,33.0,amp=20,period=0.9,arms=False)
yaw(cl,[(28.0,0),(33.6,0),(34.2,-90),(35.0,-90)])
# 35~45 문을 지나 마당으로 → 아이들 곁에서 스스로 춤
P(cl,[(35.0,(-24,0,-27)),(35.8,(-44,0,-26)),(37.4,(-44,0,30)),(38.6,(-43,0,56)),(39.4,(-43,0,62)),(45,(-43,0,62))],'catmullrom')   # 무대 옆(x -44)으로 돌아 문으로
yaw(cl,[(35.0,-90),(35.6,-90),(36.2,180),(39.4,180),(39.8,0),(45,0)])
walk(cl,35.0,39.4,amp=26,period=0.6)
dance=[(39.8,(0,0,0))]; dl=[(39.8,(0,0,0))]; dr=[(39.8,(0,0,0))]; t=40.0; s_=1
while t<45:
    dl.append((t,(0,0,120 if s_>0 else 40))); dr.append((t,(0,0,-40 if s_>0 else -120))); dance.append((t,(0,0,8*s_))); t+=0.45; s_=-s_
R(CAL,dl,'catmullrom'); R(CAR,dr,'catmullrom'); R(CB,dance,'catmullrom')
R(CH,[(34.0,(0,0,0)),(39.8,(-10,0,0)),(41,(-15,0,8)),(42,(-15,0,-8)),(43,(-15,0,8)),(45,(-10,0,0))],'catmullrom')

# ---------------- 쥐 ----------------
ms=mouse(M,'ms_',1.0); top.append(ms)
MH=part(ms,'head'); MT=part(ms,'tail')
HLX=5.4+3.0; HRX=-(5.4+3.0)   # 앉은 광대 손목 옆
P(ms,[(0,(30,SH,6)),(13.4,(30,SH,6)),(14.6,(HLX+2,SH,2)),(CUT['hl']+0.4,(HLX+2,SH,2)),(17.4,(HLX+1,SH,-6)),(18.4,(HRX-2,SH,-2)),(CUT['hr']+0.4,(HRX-2,SH,-2)),
      (20.6,(HRX,SH,-10)),(21.4,(3,SH,-13)),(CUT['kl']+0.4,(3,SH,-13)),(23.4,(-1,SH,-14)),(24.2,(-3,SH,-13)),(CUT['kr']+0.4,(-3,SH,-13)),
      (27.0,(-8,SH,-14)),(31.0,(-8,SH,-14)),(33.5,(-8,SH,-16)),(34.0,(-10,0,-24)),(35.4,(-30,0,-30)),(36.2,(-48,0,-28)),(37.6,(-48,0,28)),(38.8,(-38,0,54)),(45,(-38,0,56))],'catmullrom')
yaw(ms,[(0,90),(13.4,90),(14.0,110),(14.6,-120),(16.0,-120),(17.4,-90),(18.4,90),(20.0,90),(20.6,140),(21.4,0),(23.4,0),(24.2,0),
        (27.0,30),(31.0,30),(33.0,0),(34.2,-90),(36.0,-90),(36.4,180),(38.8,180),(39.2,0),(45,0)])
def gnaw(t0,t1):
    pts=[(t0,(0,0,0))]; t=t0+0.12; s_=1
    while t<t1: pts.append((t,(25 if s_>0 else 5,0,0))); t+=0.12; s_=-s_
    R(MH,pts+[(t1,(0,0,0))])
for n,tc in CUT.items(): gnaw(tc-1.4,tc)
wt=[(0,(0,0,0))]; t=0.3; s_=1
while t<45: wt.append((t,(0,18*s_,0))); t+=0.6; s_=-s_
R(MT,wt,'catmullrom')
show(ms,[(13.0,45)])

# ---------------- 바깥 아이들 (창밖 10~14초, 마당 38~45초) ----------------
kids=[doll2(M,'kb_',0.85,dict(shirt='paint_shirt',bottom='shorts',bottom_col='paint_short',shoe='paint_shoe')),
      doll2(M,'kg_',0.85,dict(shirt='paint_dress',bottom='skirt',bottom_col='paint_dress',shoe='paint_shoe',hair='pigtails',leg_col='wood'))]
top+= kids
for i,k in enumerate(kids):
    x0=44+i*14
    P(k,[(0,(x0,0,70)),(14.0,(x0+18,0,70)),(14.01,(-58+i*30,0,72)),(45,(-58+i*30,0,72))])
    yaw(k,[(0,90),(14.0,90),(14.01,180),(38.0,180),(38.4,0),(45,0)])
    walk(k,8.0,14.0,amp=32,period=0.45)
    dl=[(38.4,(0,0,0))]; dr=[(38.4,(0,0,0))]; t=38.6+i*0.2; s_=1
    while t<45: dl.append((t,(0,0,110 if s_>0 else 30))); dr.append((t,(0,0,-30 if s_>0 else -110))); t+=0.45; s_=-s_
    R(part(k,'arm_left'),dl,'catmullrom'); R(part(k,'arm_right'),dr,'catmullrom')
    show(k,[(8.0,14.0),(38.0,45)])

A.bake(top)
M.save(f'{OUT}/A_무대.bbmodel',top,[A.json()],name='A')
R_=[['bar_bar_hl','cl_hand_l',0,CUT['hl']],['bar_bar_hr','cl_hand_r',0,CUT['hr']],['bar_bar_kl','cl_knee_l',0,CUT['kl']],['bar_bar_kr','cl_knee_r',0,CUT['kr']],
    ['bar_bar_hl','dangle_hl',CUT['hl'],99],['bar_bar_hr','dangle_hr',CUT['hr'],99],['bar_bar_kl','dangle_kl',CUT['kl'],99],['bar_bar_kr','dangle_kr',CUT['kr'],99]]
json.dump({'A':{'ropes':R_}},open(f'{OUT}/세트정보.json','w',encoding='utf-8'),ensure_ascii=False)
print('ok',len(M.els),'parts')
