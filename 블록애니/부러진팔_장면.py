"""《부러진 팔》 장면 모형 + 움직임 (세트 A, 0~45초) → 연재/부러진팔/장면/A_마당.bbmodel, 세트정보.json
   나무 인형(원통·공 모양). 실제 세계 좌표, 위치 움직임은 x 를 뒤집어 넣음.  yaw: 0 = -z, +90 = +x, 180 = +z
   마당: 나무 (-6,0,44), 공방 바깥 (60,0,50) 문은 -z 쪽.  공방 안(따로 떨어진 방): 작업대 (300,0,310), 뒷벽 창 z 330"""
import sys, os, json, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 나무인형 import *
OUT=sys.argv[1] if len(sys.argv)>1 else '/home/user/youtubeshot/연재/부러진팔/장면'
os.makedirs(OUT,exist_ok=True)
L=45.0; random.seed(5)
M=Model(512); palette(M)
M.swatch('grass',(118,172,86),10); M.swatch('grass_d',(104,158,76),10); M.swatch('path',(205,182,140),8)
M.swatch('bark',wood_fn((120,85,55),(85,58,36),21),4); M.swatch('leaf',(86,150,72),14); M.swatch('leaf2',(110,170,84),14)
M.swatch('plank',wood_fn((190,145,95),(150,108,65),22),4); M.swatch('plank_d',wood_fn((150,108,68),(115,80,48),23),4)
M.swatch('wall',(236,226,206),5); M.swatch('roof',(165,75,58),6); M.swatch('glass',(150,195,225),3); M.swatch('night_glass',(40,55,95),3)
M.swatch('moon',(250,245,215),2); M.swatch('fence',wood_fn((225,205,170),(190,170,135),24),3); M.swatch('chip',(236,205,150),8)
M.swatch('iron',(110,110,115),3); M.swatch('lamp',(255,225,140),2)
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
def walk(p, t0, t1, amp=26, period=0.6, arms=(True,True)):
    legL,legR,armL,armR=[part(p,n) for n in ('leg_left','leg_right','arm_left','arm_right')]
    t=t0; s=1; pts=[]
    while t<t1-1e-6: pts.append((t+period/4,s)); t+=period/2; s=-s
    gs=[(legL,1),(legR,-1)]+([(armL,-1)] if arms[0] else [])+([(armR,1)] if arms[1] else [])
    for g,sg in gs:
        R(g,[(t0,(0,0,0))]+[(tt,(sg*ss*amp,0,0)) for tt,ss in pts if tt<t1]+[(t1,(0,0,0))],'catmullrom')

# ---------------- 마당 ----------------
W=[X('far',[-3000,-20,-3000],[3000,-0.4,3000],'grass')]
for x in range(-160,200,40):
    for z in range(-120,200,40): W.append(X('g',[x,-2,z],[x+40,0,z+40],'grass' if ((x+z)//40)%2 else 'grass_d'))
for z in range(-10,48,8): W.append(X('path',[52,0.02,z],[68,0.2,z+8],'path'))
# 울타리 (뒤쪽)
for x in range(-150,190,12):
    W+= [X('post',[x,0,118],[x+2,14,120],'fence'), X('rail',[x,8,118.5],[x+12,10,119.5],'fence')]
top.append(M.group('world',[0,0,0],W))
# 큰 나무 (원통 기둥 + 공 잎)
TX,TZ=-6,44
top.append(M.group('tree',[TX,0,TZ],[cyl(M,'trunk',[TX,0,TZ],[TX,34,TZ],3.2,2.4,'bark',seg=14),
     sphere(M,'crown',[TX,44,TZ],16,'leaf',seg=16,rings=10,sy=0.8), sphere(M,'crown2',[TX+10,38,TZ-4],9,'leaf2',seg=12,rings=8),
     sphere(M,'crown3',[TX-11,39,TZ+3],10,'leaf2',seg=12,rings=8)]))
# 다른 나무 몇 그루
for i,(x,z,h) in enumerate([(-80,90,30),(-110,40,26),(110,95,32),(130,20,28),(-60,-60,24)]):
    top.append(M.group(f'tr{i}',[x,0,z],[cyl(M,'t',[x,0,z],[x,h,z],2.4,1.8,'bark'), sphere(M,'c',[x,h+8,z],11,'leaf',seg=12,rings=8,sy=0.85)]))
# 공방 바깥 (문은 -z 쪽, x 60)
SX,SZ=60,50
B=[X('sh_wall',[SX-22,0,SZ],[SX+22,30,SZ+36],'wall')]
for i in range(4): B.append(X('sh_roof',[SX-25+i*5.5,30+i*5,SZ-3],[SX+25-i*5.5,30+(i+1)*5,SZ+39],'roof'))
B+= [X('sh_door',[SX-6,0,SZ-0.6],[SX+6,22,SZ],'plank_d'), X('sh_knob',[SX+3,10,SZ-1.1],[SX+4.4,11.4,SZ-0.5],'iron'),
     X('sh_winf',[SX+9,11,SZ-0.6],[SX+19,21,SZ],'fence'), X('sh_win',[SX+10,12,SZ-0.8],[SX+18,20,SZ-0.6],'glass'),
     X('sh_step',[SX-9,0,SZ-6],[SX+9,2,SZ-0.05],'plank')]
top.append(M.group('shed',[0,0,0],B))
# 문이 열림 (30~33초: 할아버지가 문가에서 봄)
door=M.group('sh_door_open',[SX-6,0,SZ],[X('door_o',[SX-6,0,SZ-12],[SX-5.4,22,SZ],'plank_d')]); top.append(door); show(door,[(30.0,33.0)])

# ---------------- 공방 안 (떨어진 방) ----------------
IX,IZ=300,310
I=[X('floor',[IX-40,-0.4,IZ-40],[IX+40,0.1,IZ+22],'plank'), X('back',[IX-40,0,IZ+20],[IX+40,46,IZ+22],'plank_d'),
   X('left',[IX-42,0,IZ-40],[IX-40,46,IZ+22],'plank_d'), X('right',[IX+40,0,IZ-40],[IX+42,46,IZ+22],'plank_d'),
   X('ceil',[IX-42,46,IZ-40],[IX+42,48,IZ+22],'plank_d'),
   X('winf',[IX-12,22,IZ+19.4],[IX+12,40,IZ+20],'fence'), X('bench_top',[IX-20,12,IZ-6],[IX+20,14,IZ+6],'plank'),
   X('bench_l1',[IX-18,0,IZ-5],[IX-15,12,IZ-2],'plank_d'), X('bench_l2',[IX+15,0,IZ-5],[IX+18,12,IZ-2],'plank_d'),
   X('bench_l3',[IX-18,0,IZ+2],[IX-15,12,IZ+5],'plank_d'), X('bench_l4',[IX+15,0,IZ+2],[IX+18,12,IZ+5],'plank_d'),
   X('shelf',[IX-38,26,IZ+12],[IX-18,27,IZ+20],'plank'), X('saw',[IX+22,24,IZ+19.0],[IX+34,30,IZ+19.4],'iron'),
   X('saw_h',[IX+31,23,IZ+18.8],[IX+36,27,IZ+19.0],'plank_d')]
for i in range(14):   # 대패밥
    x=IX+random.uniform(-30,30); z=IZ+random.uniform(-30,14)
    I.append(X('chip',[x,0.12,z],[x+random.uniform(1.5,3),0.5,z+random.uniform(1,2)],'chip'))
for i,(x,z,c) in enumerate([(IX+12,IZ-1,'plank'),(IX+16,IZ+2,'plank_d')]): I.append(X('block',[x,14,z],[x+4,17,z+3],c))   # 소년·할아버지 손을 가리지 않게 오른쪽 끝에
top.append(M.group('room',[0,0,0],I))
# 창: 밤(15~22)은 어두운 유리 + 달, 낮은 밝은 유리
wn=M.group('win_night',[0,0,0],[X('wn',[IX-11,23,IZ+19.2],[IX+11,39,IZ+19.4],'night_glass'), sphere(M,'moon',[IX+5,33,IZ+19.0],3.0,'moon',seg=12,rings=8,sz=0.2)])
wd=M.group('win_day',[0,0,0],[X('wd',[IX-11,23,IZ+19.2],[IX+11,39,IZ+19.4],'glass')])
top+= [wn,wd]; show(wn,[(15.0,22.0)]); show(wd,[(0,15.0),(22.0,45)])
lamp=M.group('lamp',[IX,46,IZ],[cyl(M,'cord',[IX,46,IZ],[IX,40,IZ],0.2,0.2,'iron',seg=6), sphere(M,'bulb',[IX,39,IZ],1.6,'lamp',seg=10,rings=6)]); top.append(lamp)

# ---------------- 인물 ----------------
KS=0.9
boy=doll(M,'by_',KS,kind='boy',extra_arms=[('r','paint_dress',True)]); top.append(boy)
girl=doll(M,'gl_',KS,kind='girl',extra_arms=[('l','paint_shirt',False)]); top.append(girl)
gp=doll(M,'gp_',1.12,kind='grandpa'); top.append(gp)
BYR,BYL,BYR2,BYH,BYB=[part(boy,n) for n in ('arm_right','arm_left','arm_right2','head','body')]
GLL,GLR,GLL2,GLH,GLB=[part(girl,n) for n in ('arm_left','arm_right','arm_left2','head','body')]
show(BYR,[(0,19.4)]); show(BYR2,[(40.0,45)])          # 소년 오른팔: 밤에 떼어 냄 → 끝에 소녀의 산호색 팔
show(GLL,[(0,6.62)]); show(GLL2,[(26.0,45)])           # 소녀 왼팔: 넘어질 때 빠짐 → 소년의 초록 팔

# --- 0~9 마당 놀이 → 넘어짐 ---
P(girl,[(0,(-44,0,12)),(3.4,(-2,0,12)),(3.8,(0,0,9)),(6.4,(0,0,-6)),(6.75,(0,2.2,-8)),(8.985,(0,2.2,-8))],'catmullrom')   # 엎어진 채 그 자리 (다음 장면 자리로 미끄러지지 않게)
yaw(girl,[(0,90),(3.4,90),(3.8,0),(6.4,0)])
walk(girl,0,6.4,amp=38,period=0.42)
R(girl,[(6.4,(0,0,0)),(6.75,(82,0,6)),(8.985,(82,0,6))])                       # 앞(-z)으로 엎어짐 (몸 전체는 x +가 앞으로 — 위에서 찍어 확인함)
R(GLH,[(0,(0,0,0)),(1.5,(0,60,0)),(2.4,(0,0,0)),(6.4,(0,0,0))],'catmullrom') # 뒤돌아보며 웃음
P(boy,[(8.96,(-11,0,1)),(8.97,(16,0,18))]); P(boy,[(0,(-62,0,16)),(3.4,(-18,0,16)),(3.8,(-15,0,13)),(6.0,(-12,0,2)),(6.5,(-11,0,1)),(8.95,(-11,0,1))],'catmullrom')
yaw(boy,[(0,90),(3.4,90),(3.8,20),(6.0,20),(6.6,40),(8.95,40)])
walk(boy,0,6.1,amp=38,period=0.42)
R(BYH,[(6.5,(0,0,0)),(6.9,(20,0,0)),(8.95,(20,0,0))])
# 빠진 팔 두 동강 (땅 위 6.6~9)
up,low=loose_arm(M,'ga_',[0,0,0],[9.8*KS,0,0],'paint_dress',True,KS,pieces=2)
gnd=M.group('ga_ground',[0,0,0],[up,low]); top.append(gnd)
P(gnd,[(0,(6,1.3,-20)),(6.6,(6,1.3,-20)),(6.6,(6,3.0,-20)),(7.2,(9,1.3,-24)),(9,(9,1.3,-24))],'catmullrom')   # 엎어진 소녀 어깨 옆
R(gnd,[(6.6,(0,30,0)),(7.2,(0,55,0)),(9,(0,55,0))]); R(low,[(6.6,(0,0,0)),(7.2,(0,0,0)),(7.3,(0,-40,0)),(9,(0,-40,0))])
show(gnd,[(6.6,9.0)])

# --- 9~15 나무 아래 울음 / 바라보는 소년 ---
SIT=-(12*KS-1.4)
P(girl,[(9.0,(-4,SIT,32)),(14.99,(-4,SIT,32))]); yaw(girl,[(9.0,0),(14.99,0)])
R(girl,[(8.99,(0,0,0)),(14.99,(0,0,0))])
for lg in (part(girl,'leg_left'),part(girl,'leg_right')): R(lg,[(8.98,(0,0,0)),(9.0,(-80,0,0)),(14.99,(-80,0,0)),(15.0,(0,0,0))])
# 무릎 위에 안은 부러진 팔 (소녀 몸에 붙음)
lap=loose_arm(M,'gl_lap_',[-4.2*KS,15.5*KS,-4.4*KS],[4.6*KS,15.0*KS,-4.4*KS],'paint_dress',True,KS); GLB['children'].append(lap); show(lap,[(9.0,15.0)])
R(GLR,[(8.98,(0,0,0)),(9.0,(-55,0,-30)),(14.99,(-55,0,-30)),(15.0,(0,0,0))])
sob=[(9.0,(20,0,0))]; t=9.2; s_=1
while t<14.9: sob.append((t,(26 if s_>0 else 18,0,0))); t+=0.32; s_=-s_
R(GLB,sob+[(14.99,(20,0,0)),(15.0,(0,0,0))])
R(GLH,[(9.0,(28,0,0)),(14.99,(28,0,0)),(15.0,(0,0,0))])
P(boy,[(9.0,(16,0,18)),(12.4,(16,0,18)),(14.99,(46,0,12))])
yaw(boy,[(9.0,-40),(12.0,-40),(12.4,100),(14.99,100)])
R(BYH,[(9.0,(15,0,0)),(12.0,(15,0,0)),(12.4,(0,-70,0)),(13.6,(0,-70,0)),(14.2,(0,0,0))],'catmullrom')   # 걸어가며 한 번 돌아봄
walk(boy,12.4,14.99,amp=24,period=0.6)

# --- 15~22 밤 공방: 소년이 오른팔을 떼어 냄 ---
P(boy,[(15.0,(IX-6,0,IZ+13)),(21.99,(IX-6,0,IZ+13))]); yaw(boy,[(15.0,0),(16.6,0),(17.0,-30),(21.99,-30)])
R(BYH,[(15.0,(25,0,0)),(16.6,(25,0,0)),(17.0,(25,40,0)),(18.6,(30,40,0)),(19.4,(30,0,0)),(21.99,(40,0,0))],'catmullrom')
R(BYL,[(16.8,(0,0,0)),(17.6,(-20,0,-55)),(19.4,(-20,0,-55)),(20.2,(-40,0,0)),(21.99,(-40,0,0))])            # 왼손으로 오른 어깨를 잡음 → 떼어 든 팔
R(BYR,[(17.6,(0,0,0)),(18.4,(0,0,8)),(18.8,(0,0,-4)),(19.3,(0,0,14))])
# 떼어 든 초록 팔 (왼손에, 19.4~26)
held=loose_arm(M,'by_held_',[5.4*KS,11.6*KS,-0.2],[5.4*KS,11.6*KS-9.8*KS,-0.2],'paint_shirt',False,KS); BYL['children'].append(held); show(held,[(19.4,26.0)])
show(boy,[(0,45)])

# --- 22~28 다음 날: 한 팔로 비틀비틀 → 초록 팔을 건넴 ---
P(boy,[(22.0,(44,0,18)),(25.0,(4,0,24))]); yaw(boy,[(22.0,-80),(25.0,-60)])
walk(boy,22.0,25.0,amp=18,period=0.8,arms=(False,False))
wob=[(22.0,(0,0,0))]; t=22.2; s_=1
while t<25: wob.append((t,(0,0,9*s_))); t+=0.4; s_=-s_
R(BYB,wob+[(25.0,(0,0,0))],'catmullrom')
R(BYL,[(22.0,(-62,0,0)),(25.0,(-62,0,0)),(25.6,(-70,0,0)),(26.0,(-70,0,0)),(26.4,(0,0,0))])
R(BYH,[(22.0,(10,0,0)),(25.0,(10,0,0)),(25.4,(15,0,0)),(27.0,(-5,0,0)),(27.99,(-5,0,0))])
P(girl,[(22.0,(-4,SIT,32)),(26.6,(-4,SIT,32)),(26.61,(-4,0,32)),(27.99,(-4,0,32))]); yaw(girl,[(22.0,0),(26.6,40),(27.99,40)])
for lg in (part(girl,'leg_left'),part(girl,'leg_right')): R(lg,[(21.99,(0,0,0)),(22.0,(-80,0,0)),(26.6,(-80,0,0)),(26.61,(0,0,0))])
R(GLH,[(22.0,(30,0,0)),(23.6,(30,0,0)),(24.2,(5,40,0)),(25.6,(5,40,0)),(26.2,(30,-30,0)),(27.0,(30,-30,0)),(27.6,(0,40,0))],'catmullrom')
R(GLB,[(22.0,(20,0,0)),(24.0,(5,0,0)),(27.99,(0,0,0))])
R(GLR,[(25.0,(0,0,0)),(25.6,(-60,0,0)),(26.0,(-60,0,0)),(26.4,(0,0,0))])
R(GLL2,[(26.0,(0,0,0)),(26.3,(-40,0,10)),(27.4,(-40,0,10)),(27.99,(0,0,0))])    # 새 팔을 들어 바라봄

# --- 28~33 다시 놀이: 비틀거리는 소년을 초록 팔로 붙잡음 ---
P(girl,[(28.0,(-14,0,8)),(30.4,(4,0,8)),(30.9,(5,0,8)),(32.99,(20,0,8))]); yaw(girl,[(28.0,90),(32.99,90)])
P(boy,[(28.0,(-14,0,-4)),(30.4,(4,0,-4)),(31.4,(6,0,-3)),(32.99,(20,0,-4))]); yaw(boy,[(28.0,90),(32.99,90)])
walk(girl,28.0,30.4,amp=26); walk(girl,30.9,32.99,amp=24)
walk(boy,28.0,30.4,amp=26,arms=(True,False)); walk(boy,31.4,32.99,amp=24,arms=(True,False))
R(BYB,[(28.0,(0,0,0)),(30.4,(0,0,0)),(30.8,(-6,0,-28)),(31.2,(-6,0,-24)),(31.6,(0,0,-4)),(32.99,(0,0,0))],'catmullrom')   # 기우뚱
R(GLL2,[(28.0,(0,0,0)),(30.4,(0,0,0)),(30.7,(-70,0,0)),(31.4,(-70,0,0)),(31.8,(-15,0,0)),(32.99,(-15,0,0))])
R(GLH,[(28.0,(0,0,0)),(30.5,(0,-60,0)),(31.6,(0,-60,0)),(32.2,(0,-30,0))],'catmullrom')
# 할아버지: 공방 문가에서 지켜봄
P(gp,[(0,(SX-1,0,SZ-4)),(32.99,(SX-1,0,SZ-4))]); yaw(gp,[(0,-15),(32.99,-15)])
R(part(gp,'head'),[(30.0,(0,0,0)),(31.0,(0,-25,0)),(31.8,(15,-25,0)),(32.2,(0,-25,0)),(32.6,(15,-25,0)),(32.99,(5,-25,0))],'catmullrom')
show(gp,[(30.0,45)])

# --- 33~38 공방: 할아버지가 부러진 팔을 맞붙여 고침 ---
P(gp,[(33.0,(IX,0,IZ+13)),(37.99,(IX,0,IZ+13))]); yaw(gp,[(33.0,0),(37.99,0)])
GPL,GPR,GPH,GPB=[part(gp,n) for n in ('arm_left','arm_right','head','body')]
R(GPB,[(33.0,(18,0,0)),(37.99,(18,0,0)),(38.0,(0,0,0))])
R(GPH,[(33.0,(25,0,0)),(37.99,(25,0,0)),(38.0,(0,0,0))])
work=[(33.0,(-50,0,0))]; t=33.2; s_=1
while t<37.8: work.append((t,(-50+6*s_,0,8*s_))); t+=0.35; s_=-s_
R(GPL,work+[(37.99,(-50,0,0)),(38.0,(0,0,0))]); R(GPR,[(33.0,(-55,0,0)),(35.8,(-55,0,0)),(36.2,(-62,0,0)),(36.6,(-55,0,0)),(37.99,(-55,0,0)),(38.0,(0,0,0))])
bu,bl=loose_arm(M,'gb_',[IX-5,14.9,IZ-3],[IX-5+9.8*KS,14.9,IZ-3],'paint_dress',True,KS,pieces=2)
bench_arm=M.group('gb_bench',[0,0,0],[bu,bl]); top.append(bench_arm); show(bench_arm,[(33.0,38.0)])
R(bl,[(33.0,(0,35,0)),(36.0,(0,35,0)),(36.8,(0,0,0)),(38,(0,0,0))])     # 떨어진 아래팔을 제자리에 맞붙임

# --- 38~45 달아 줌 → 셋이 손잡고 걸어감 ---
P(boy,[(38.0,(0,0,6)),(40.8,(0,0,6)),(45,(0,0,40))]); yaw(boy,[(38.0,0),(40.6,0),(41.0,180),(45,180)])
P(girl,[(38.0,(-11,0,6)),(40.8,(-11,0,6)),(45,(-11,0,40))]); yaw(girl,[(38.0,30),(40.6,30),(41.0,180),(45,180)])
P(gp,[(38.0,(11,0,8)),(40.8,(11,0,8)),(45,(12,0,42))]); yaw(gp,[(38.0,-80),(40.6,-80),(41.0,180),(45,180)])
R(GPB,[(38.0,(20,0,0)),(40.4,(20,0,0)),(40.9,(0,0,0))])
R(GPL,[(38.0,(-60,0,0)),(39.8,(-60,0,0)),(40.4,(-20,0,0)),(40.9,(0,0,0))]); R(GPR,[(38.0,(-60,0,0)),(39.8,(-60,0,0)),(40.4,(-20,0,0)),(40.9,(0,0,0))])
R(GPH,[(38.0,(20,0,0)),(40.4,(20,0,0)),(40.9,(0,0,0))])
R(BYH,[(38.0,(0,-50,0)),(40.0,(0,-60,0)),(40.3,(-10,-60,0)),(40.8,(0,0,0))],'catmullrom')
R(BYR2,[(40.0,(0,0,0)),(40.3,(-30,0,0)),(40.6,(0,0,0))])
R(GLH,[(38.0,(5,40,0)),(40.8,(5,40,0)),(41.0,(0,0,0))])
for g,amp in ((boy,16),(girl,16),(gp,14)): walk(g,41.0,45,amp=amp,period=0.9,arms=(False,False))
R(BYR2,[(41.0,(0,0,14)),(45,(0,0,14))]); R(BYL,[(41.0,(0,0,-14)),(45,(0,0,-14))])     # 양쪽으로 손을 내밀어 잡음
R(GLL2,[(41.0,(0,0,-14)),(45,(0,0,-14))]); R(GPR,[(41.0,(0,0,14)),(45,(0,0,14))])

A.bake(top)
M.save(f'{OUT}/A_마당.bbmodel',top,[A.json()],name='A')
json.dump({'A':{'ropes':[]}},open(f'{OUT}/세트정보.json','w',encoding='utf-8'))
print('ok',len(M.els),'parts')
