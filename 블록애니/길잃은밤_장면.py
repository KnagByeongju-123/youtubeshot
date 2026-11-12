"""《길 잃은 밤》 장면 모형 + 움직임 (세트 A, 0~45초) → 연재/길잃은밤/장면/A_숲.bbmodel, 세트정보.json
   나무 인형(원통·공). 실제 세계 좌표, 위치 움직임은 x 를 뒤집어 넣음(P).  yaw: 0 = -z, +90 = +x, 180 = +z
   장소(떨어진 곳에 따로):  ① 낮 숲길 x -110~70, z 0   ② 갈림길 (230,0,0)   ③ 밤 큰 나무 (450,0,30), 먼 불빛 (650,·,0)
   ④ 공방 (922,0,40~76) 문은 -z 쪽
   목줄: 소년 오른손(by_hand_r) ↔ 강아지 목걸이(dg_leash) — 처음부터 끝까지 (세트정보.json ropes)"""
import sys, os, json, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 나무인형 import *
OUT=sys.argv[1] if len(sys.argv)>1 else '/home/user/youtubeshot/연재/길잃은밤/장면'
os.makedirs(OUT,exist_ok=True)
L=45.0; random.seed(11)
M=Model(512); palette(M)
M.swatch('grass',(104,152,80),10); M.swatch('grass_d',(92,140,72),10); M.swatch('path',(196,170,124),8); M.swatch('soil',(120,90,60),6)
M.swatch('bark',wood_fn((112,80,52),(80,55,34),21),4); M.swatch('leaf',(70,130,64),14); M.swatch('leaf2',(92,150,74),14); M.swatch('leaf3',(58,112,60),14)
M.swatch('plank',wood_fn((190,145,95),(150,108,65),22),4); M.swatch('plank_d',wood_fn((150,108,68),(115,80,48),23),4)
M.swatch('wall',(222,206,180),5); M.swatch('roof',(150,70,55),6); M.swatch('lamp',(255,214,110),2); M.swatch('lamp2',(255,236,170),2)
M.swatch('iron',(80,78,76),3); M.swatch('rope',(150,40,36),3); M.swatch('stone',(150,150,145),8); M.swatch('bush',(66,120,60),12)
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
def swing(gs, t0, t1, amp, period):
    """gs = [(묶음, 부호)] 를 t0~t1 동안 앞뒤로 흔들고 0 으로 돌아옴"""
    t=t0; s=1; pts=[]
    while t<t1-1e-6: pts.append((t+period/4,s)); t+=period/2; s=-s
    for g,sg in gs:
        R(g,[(t0,(0,0,0))]+[(tt,(sg*ss*amp,0,0)) for tt,ss in pts if tt<t1]+[(t1,(0,0,0))],'catmullrom')
def walk(p, t0, t1, amp=26, period=0.6, arms=(True,True)):
    legL,legR,armL,armR=[part(p,n) for n in ('leg_left','leg_right','arm_left','arm_right')]
    gs=[(legL,1),(legR,-1)]+([(armL,-1)] if arms[0] else [])+([(armR,1)] if arms[1] else [])
    swing(gs,t0,t1,amp,period)
def dwalk(t0, t1, amp=28, period=0.4):
    """강아지 네 발 걸음 (대각선 다리끼리 같이)"""
    swing([(DFL,1),(DBR,1),(DFR,-1),(DBL,-1)],t0,t1,amp,period)
def wag(t0, t1, amp=30, period=0.22):
    pts=[]; t=t0; s=1
    while t<t1: pts.append((t,(0,s*amp,0))); t+=period/2; s=-s
    R(DT,[(t0-0.01,(0,0,0))]+pts+[(t1,(0,0,0))])

def tree(x, z, h=30, r=2.6, big=1.0, col='leaf'):
    return M.group('tree',[x,0,z],[cyl(M,'t',[x,0,z],[x,h,z],r,r*0.75,'bark',seg=10),
        sphere(M,'c',[x,h+7*big,z],11*big,col,seg=12,rings=8,sy=0.85), sphere(M,'c2',[x+5*big,h+1,z-3],7*big,'leaf2',seg=10,rings=6)])
def bush(x, z, r=4): return sphere(M,'bush',[x,r*0.5,z],r,'bush',seg=10,rings=6,sy=0.7)
def forest(x0, x1, zs, keep, n, seed):
    """x0~x1, z 범위들(zs) 안에 나무 n 그루. keep(x,z) 가 참인 자리는 비움 (길·인물 동선)"""
    rnd=random.Random(seed); out=[]
    while len(out)<n:
        x=rnd.uniform(x0,x1); z0,z1=rnd.choice(zs); z=rnd.uniform(z0,z1)
        if keep(x,z): continue
        out.append(tree(x,z,rnd.uniform(26,40),rnd.uniform(2.2,3.2),rnd.uniform(0.8,1.25),rnd.choice(['leaf','leaf2','leaf3'])))
    return out

# ---------------- 땅 ----------------
W=[X('far',[-3000,-20,-3000],[3000,-0.4,3000],'grass_d')]
for x in range(-160,1000,40):
    for z in range(-120,200,40): W.append(X('g',[x,-2,z],[x+40,0,z+40],'grass' if ((x+z)//40)%2 else 'grass_d'))
# ① 낮 숲길 (z -5~5)
for x in range(-120,80,10): W.append(X('path',[x,0.02,-5],[x+10,0.2,5],'path'))
top.append(M.group('world',[0,0,0],W))
top+= forest(-130,90,[(14,70)],lambda x,z:False,22,1)                      # 길 뒤쪽 숲
top+= [M.group('bushes',[0,0,0],[bush(x,z,r) for x,z,r in [(-90,-14,3.5),(-40,-16,3),(30,-15,3.5),(70,-14,3)]])]
# ② 갈림길: 왼쪽에서 온 길이 두 갈래로 + 글자 없는 이정표
CX=230
G2=[X('p2',[CX-60+i*6,0.03,-5],[CX-54+i*6,0.21,5],'path') for i in range(10)]
for i in range(8):   # 두 갈래 (조각끼리 겹치지 않게 x 로 5씩, 두 갈래는 높이를 다르게)
    G2.append(X('pa',[CX+i*5,0.04,i*5-4],[CX+i*5+5,0.22,i*5+4],'path'))
    if i>=2: G2.append(X('pb',[CX+i*5,0.06,-i*5-4],[CX+i*5+5,0.3,-i*5+4],'path'))
G2+= [cyl(M,'post',[CX+4,0,12],[CX+4,22,12],0.8,0.7,'plank_d',seg=8), X('sign1',[CX+4.8,17,11.4],[CX+14,20,12.4],'plank'),
      X('sign2',[CX-5,13.5,11.6],[CX+3.2,16.5,12.6],'plank')]
top.append(M.group('cross',[0,0,0],G2))
top+= forest(CX-80,CX+80,[(16,80)],lambda x,z:False,16,2)
top+= forest(CX+10,CX+80,[(-80,-50)],lambda x,z:False,4,3)
# ③ 밤: 큰 나무 + 먼 불빛 (불빛 쪽 z -14~20, x 455~660 은 비움)
TX,TZ=450,30
top.append(M.group('bigtree',[TX,0,TZ],[cyl(M,'trunk',[TX,0,TZ],[TX,36,TZ],5.0,3.6,'bark',seg=14),
     cyl(M,'rootL',[TX-3,1,TZ-3],[TX-8,0,TZ-7],1.6,0.8,'bark',seg=8), cyl(M,'rootR',[TX+3,1,TZ-3],[TX+9,0,TZ-6],1.6,0.8,'bark',seg=8),
     sphere(M,'crown',[TX,48,TZ],18,'leaf3',seg=16,rings=10,sy=0.8), sphere(M,'crown2',[TX+12,42,TZ-4],10,'leaf',seg=12,rings=8),
     sphere(M,'crown3',[TX-12,43,TZ+3],11,'leaf2',seg=12,rings=8)]))
top+= forest(380,700,[(42,110)],lambda x,z:abs(x-TX)<20,22,4)
top+= forest(470,700,[(26,40)],lambda x,z:False,10,5)
top+= forest(380,440,[(-60,-30)],lambda x,z:False,3,6)
LX=600   # 먼 불빛: 작은 오두막 창
top.append(M.group('farlight',[0,0,0],[X('cab',[LX,0,-6],[LX+20,16,12],'plank_d'), X('cab_roof',[LX-2,16,-8],[LX+22,19,14],'roof'), X('cab_roof2',[LX+2,19,-6],[LX+18,22,12],'roof'), X('cab_win',[LX-0.3,5,-2],[LX,14,8],'lamp'),
     sphere(M,'glow',[LX-1,9.5,3],3.4,'lamp2',seg=10,rings=6,sx=0.4)]))
# ④ 공방 (문 x 913~931 은 -z 쪽 z 40)
HX=922; HZ=40
H=[X('h_wall',[HX-24,0,HZ],[HX+24,30,HZ+36],'wall')]
for i in range(4): H.append(X('h_roof',[HX-27+i*6,30+i*5,HZ-3],[HX+27-i*6,30+(i+1)*5,HZ+39],'roof'))
H+= [X('h_win',[HX-20,11,HZ-0.3],[HX-12,19,HZ],'lamp'), X('h_win2',[HX+13,11,HZ-0.3],[HX+21,19,HZ],'lamp'),
     X('h_winf',[HX-21,10,HZ-0.2],[HX-11,20,HZ-0.1],'plank_d'), X('h_winf2',[HX+12,10,HZ-0.2],[HX+22,20,HZ-0.1],'plank_d'),
     X('h_step',[HX-11,0,HZ-6],[HX+11,1.6,HZ-0.05],'plank'), cyl(M,'h_lamp',[HX+14,24,HZ-0.5],[HX+14,24,HZ-3],1.2,1.2,'lamp',seg=8)]
top.append(M.group('house',[0,0,0],H))
door=M.group('h_door',[0,0,0],[X('door',[HX-9,0,HZ-0.6],[HX+9,24,HZ],'plank_d'), X('knob',[HX+5,11,HZ-1.1],[HX+6.4,12.4,HZ-0.6],'iron')]); top.append(door)
dopen=M.group('h_open',[0,0,0],[X('glowdoor',[HX-8.8,0.1,HZ-0.35],[HX+8.8,23.8,HZ-0.1],'lamp2')])
top.append(dopen); show(door,[(0,42.0)]); show(dopen,[(42.0,45)])
top+= forest(820,1000,[(80,140)],lambda x,z:False,12,7)
top+= forest(820,880,[(30,70)],lambda x,z:False,4,8)
top+= forest(960,1000,[(-40,30)],lambda x,z:False,3,9)
top.append(M.group('fence4',[0,0,0],[X('f',[x,0,HZ-12],[x+1.5,9,HZ-10.5],'plank') for x in range(944,980,8)]+[X('fr',[944.3,5,HZ-11.8],[979.7,6.4,HZ-10.7],'plank')]))

# ---------------- 인물 ----------------
KS=0.9; DS=0.9
boy=doll(M,'by_',KS,kind='boy'); top.append(boy)
dog=wood_dog4(M,'dg_',DS); top.append(dog)
gp=doll(M,'gp_',1.12,kind='grandpa'); top.append(gp)
BYL,BYR,BYH,BYB=[part(boy,n) for n in ('arm_left','arm_right','head','body')]
DB,DH,DT=[part(dog,n) for n in ('body','head','tail')]
DFL,DFR,DBL,DBR=[part(dog,n) for n in ('leg_fl','leg_fr','leg_bl','leg_br')]
GPL,GPR,GPH,GPB=[part(gp,n) for n in ('arm_left','arm_right','head','body')]
# 할아버지 등불 (왼손에 매달림)
gs=1.12; hx=5.4*gs; hy=11.2*gs
lan=M.group('gp_lantern',[hx,hy,0],[cyl(M,'l_h',[hx,hy,0],[hx,hy-2.2,0],0.25,0.25,'iron',seg=6), cyl(M,'l_top',[hx,hy-2.2,0],[hx,hy-3.0,0],0.6,1.5,'iron',seg=8),
      cyl(M,'l_glass',[hx,hy-3.0,0],[hx,hy-6.4,0],1.3,1.3,'lamp',seg=10), cyl(M,'l_bot',[hx,hy-6.4,0],[hx,hy-7.0,0],1.5,1.5,'iron',seg=8)])
find(gp,'gp_hand_l')['children'].append(lan)
# 목줄 (촬영 때 소년 오른손 ↔ 강아지 목걸이로 늘려 붙임)
top.append(M.group('ropes',[0,0,0],[X('rope_0',[-0.22,-0.22,0],[0.22,0.22,1],'rope')]))
show(gp,[(33.0,45)])

# ===== 0~10 낮 숲길: 소년이 앞장, 강아지가 뒤에서 따라옴 =====
GAP=19
P(boy,[(0,(-80,0,0)),(5.0,(-38,0,0)),(9.98,(26,0,0))])
yaw(boy,[(0,90),(9.98,90)])
walk(boy,0,5.0,amp=26,period=0.6,arms=(True,False)); walk(boy,5.0,9.98,amp=38,period=0.42,arms=(True,False))
R(BYR,[(0,(28,0,0)),(9.98,(28,0,0))])                                  # 줄 쥔 오른팔은 뒤로
R(BYH,[(0,(0,0,0)),(1.6,(0,-25,0)),(2.6,(0,0,0)),(9.98,(0,0,0))],'catmullrom')   # 한 번 돌아보고 웃음
dxs=[(0,-80-GAP),(5.0,-38-GAP),(9.98,26-GAP)]
# 강아지: 8.0초에 나무뿌리(ROOT_X)에 앞발이 걸려 휘청
def dogx(t):
    for (t0,x0),(t1,x1) in zip(dxs,dxs[1:]):
        if t0<=t<=t1: return x0+(x1-x0)*(t-t0)/(t1-t0)
TB=8.0; ROOT_X=round(dogx(TB)+5.5,1)
P(dog,[(0,(dxs[0][1],0,0)),(5.0,(dxs[1][1],0,0)),(7.95,(dogx(7.95),0,0)),(8.15,(dogx(8.15),1.2,0)),(8.4,(dogx(8.4)-0.5,0,0)),(9.98,(26-GAP-1.5,0,0))])
yaw(dog,[(0,90),(9.98,90)])
dwalk(0,7.95,amp=26,period=0.4); dwalk(8.5,9.98,amp=32,period=0.32)
R(DB,[(7.95,(0,0,0)),(8.12,(0,0,14)),(8.3,(0,0,-8)),(8.5,(0,0,0))],'catmullrom')     # 휘청 (옆으로 기우뚱)
R(DH,[(0,(0,0,0)),(7.95,(0,0,0)),(8.15,(15,0,0)),(8.6,(0,0,0)),(9.98,(0,0,0))])
wag(0.2,7.8)
top.append(M.group('root1',[ROOT_X,0,0],[cyl(M,'root',[ROOT_X-2,0.5,-6],[ROOT_X+1,0.7,6],0.9,0.7,'bark',seg=8)]))   # 강아지 앞발이 걸리는 나무뿌리

# ===== 10~15 해 질 녘 갈림길: 두리번 =====
P(boy,[(10.0,(CX-26,0,0)),(11.6,(CX-4,0,0)),(14.99,(CX-4,0,0))])
R(BYL,[(11.6,(0,0,0)),(14.98,(0,0,0))])
walk(boy,10.0,11.6,amp=22,period=0.6,arms=(True,False))
yaw(boy,[(10.0,90),(11.8,90),(12.2,40),(12.9,40),(13.3,140),(14.0,140),(14.4,90),(14.99,90)])
R(BYH,[(10.0,(0,0,0)),(11.8,(0,0,0)),(12.2,(-8,40,0)),(12.9,(-8,40,0)),(13.3,(-8,-40,0)),(14.0,(-8,-40,0)),(14.4,(0,0,0)),(14.6,(22,0,0)),(14.99,(22,0,0))],'catmullrom')
R(BYB,[(14.3,(0,0,0)),(14.7,(10,0,0)),(14.99,(10,0,0))])
R(BYR,[(10.0,(20,0,0)),(14.99,(20,0,0))])
P(dog,[(10.0,(CX-26-GAP+3,0,0)),(11.8,(CX-21,0,0)),(14.99,(CX-21,0,0))])
yaw(dog,[(10.0,90),(14.99,90)])
dwalk(10.0,11.8,amp=24,period=0.42)
R(DH,[(10.0,(0,0,0)),(12.0,(0,0,0)),(12.4,(-10,35,0)),(13.2,(-10,-35,0)),(14.0,(0,0,0)),(14.99,(10,0,0))],'catmullrom')

# ===== 15~27 밤, 큰 나무 아래 =====
SIT=-(12*KS-1.4)
BX,BZ=TX,TZ-15        # 소년 자리 (나무 앞, 카메라 쪽을 봄)
P(boy,[(15.0,(BX,SIT,BZ)),(27.6,(BX,SIT,BZ)),(28.4,(BX,0,BZ-2))])
yaw(boy,[(15.0,0),(27.8,0),(28.4,90)])
for lg in (part(boy,'leg_left'),part(boy,'leg_right')): R(lg,[(14.99,(0,0,0)),(15.0,(-80,0,0)),(27.6,(-80,0,0)),(28.3,(0,0,0))])
R(BYL,[(15.0,(-62,0,-18)),(27.6,(-62,0,-18)),(28.3,(0,0,0))]); R(BYR,[(15.0,(-62,0,18)),(27.6,(-62,0,18)),(28.3,(-55,0,0))])
sob=[(15.0,(20,0,0))]; t=15.2; s_=1
while t<21.0: sob.append((t,(26 if s_>0 else 18,0,0))); t+=0.34; s_=-s_
R(BYB,sob+[(21.4,(14,0,0)),(27.6,(8,0,0)),(28.4,(10,0,0))],'catmullrom')
R(BYH,[(15.0,(30,0,0)),(21.0,(30,0,0)),(21.6,(8,35,0)),(23.6,(8,35,0)),(24.4,(-5,70,0)),(27.4,(-5,70,0)),(28.2,(0,0,0))],'catmullrom')
# 강아지: 옆에서 바라봄 → 다가와 무릎에 머리를 비빔 → 고개를 번쩍 → 몸을 돌려 불빛 쪽
DX0=BX+17
P(dog,[(15.0,(DX0,0,BZ-6)),(19.0,(DX0,0,BZ-6)),(19.8,(BX+14,0,BZ-6.5)),(20.3,(BX+13,0,BZ-6.5)),(20.7,(BX+14,0,BZ-6.5)),(21.1,(BX+13,0,BZ-6.5)),
       (21.5,(BX+14,0,BZ-6.5)),(23.0,(BX+14,0,BZ-6.5)),(24.0,(BX+14,0,BZ-8)),(27.0,(BX+14,0,BZ-8)),(28.0,(BX+26,0,BZ-6))])
yaw(dog,[(15.0,-90),(23.0,-90),(24.0,90),(28.0,90)])
dwalk(19.0,19.8,amp=22,period=0.4); dwalk(23.0,24.0,amp=18,period=0.5); dwalk(27.0,28.0,amp=30,period=0.36)
R(DH,[(15.0,(10,0,-18)),(19.0,(10,0,-18)),(19.8,(25,0,0)),(20.3,(25,0,12)),(20.7,(25,0,-12)),(21.1,(25,0,12)),(21.5,(20,0,0)),
      (22.2,(20,0,0)),(22.5,(-25,0,0)),(23.0,(-25,20,0)),(24.0,(-10,0,0)),(27.0,(-10,0,0)),(28.0,(0,0,0))],'catmullrom')
wag(24.6,27.0,amp=34,period=0.2)

# ===== 27~33 강아지가 앞장, 소년이 뒤따라감 =====
P(dog,[(28.0,(BX+26,0,BZ-6)),(29.0,(BX+30,0,-2)),(32.98,(BX+76,0,0))])
yaw(dog,[(28.0,90),(32.98,90)])
dwalk(28.0,32.98,amp=28,period=0.4)
R(DB,[(28.0,(0,0,0)),(32.98,(0,0,0))]); R(DH,[(28.0,(0,0,0)),(29.4,(0,-30,0)),(30.0,(0,0,0)),(32.98,(0,0,0))],'catmullrom')   # 한 번 돌아봄
P(boy,[(28.4,(BX,0,BZ-2)),(29.4,(BX+10,0,-1)),(32.98,(BX+76-GAP,0,0))])
walk(boy,28.4,32.98,amp=24,period=0.6,arms=(True,False))
R(BYR,[(28.3,(-55,0,0)),(32.98,(-55,0,0))])                            # 줄 쥔 팔을 앞으로 (끌려감)
R(BYB,[(28.4,(10,0,0)),(32.98,(10,0,0)),(33.0,(0,0,0))])
wag(29.0,32.9,amp=22,period=0.3)

# ===== 33~45 공방: 등불 든 할아버지 → 안아 줌 → 집으로 =====
P(dog,[(33.0,(856,0,6)),(36.6,(876,0,9)),(41.8,(876,0,9)),(45,(906,0,26))])
yaw(dog,[(33.0,75),(36.6,75),(37.2,40),(41.8,40),(42.4,125),(45,125)])
dwalk(33.0,36.6,amp=26,period=0.4); dwalk(41.8,45,amp=22,period=0.42)
R(DH,[(33.0,(0,0,0)),(36.0,(-12,0,0)),(38.0,(-15,0,0)),(41.8,(-15,0,0)),(42.4,(0,0,0))],'catmullrom')
wag(36.4,42.2,amp=38,period=0.18)
P(boy,[(33.0,(838,0,4)),(37.6,(884,0,18)),(41.8,(884,0,18)),(45,(902,0,32))])
yaw(boy,[(33.0,75),(37.4,75),(37.8,90),(41.8,90),(42.4,130),(45,130)])
walk(boy,33.0,37.6,amp=24,period=0.6,arms=(True,False)); walk(boy,42.4,45,amp=20,period=0.62,arms=(True,False))
R(BYR,[(33.0,(-40,0,0)),(37.2,(-40,0,0)),(37.8,(0,0,0)),(38.4,(-80,0,10)),(41.8,(-80,0,10)),(42.4,(10,0,0)),(45,(10,0,0))])
R(BYL,[(37.6,(0,0,0)),(38.4,(-80,0,-10)),(41.8,(-80,0,-10)),(42.4,(0,0,0))])
R(BYH,[(33.0,(0,0,0)),(35.0,(-8,0,0)),(37.6,(-12,0,0)),(38.4,(-8,0,0)),(41.8,(-8,0,0)),(42.4,(0,0,0))],'catmullrom')
# 할아버지: 문 앞에서 등불을 듦 → 걸어와 몸을 숙여 안아 줌 → 셋이 문으로
P(gp,[(33.0,(HX,0,HZ-9)),(35.8,(HX,0,HZ-9)),(37.8,(898,0,18)),(41.8,(898,0,18)),(45,(916,0,34))])
yaw(gp,[(33.0,0),(34.6,0),(35.2,-70),(37.8,-90),(41.8,-90),(42.4,-230),(45,-230)])
walk(gp,35.8,37.8,amp=18,period=0.7,arms=(False,True)); walk(gp,42.4,45,amp=16,period=0.7,arms=(False,False))
R(GPL,[(33.0,(-20,0,0)),(34.4,(-20,0,0)),(35.0,(-75,0,0)),(35.8,(-75,0,0)),(36.4,(-15,0,0)),(45,(-15,0,0))])   # 등불을 들어 비춰 봄
R(GPH,[(33.0,(0,0,0)),(34.6,(0,0,0)),(35.2,(-10,-20,0)),(37.8,(10,0,0)),(38.4,(18,0,0)),(41.8,(18,0,0)),(42.4,(0,0,0))],'catmullrom')
R(GPB,[(37.8,(0,0,0)),(38.4,(12,0,0)),(41.8,(12,0,0)),(42.4,(0,0,0))])
R(GPR,[(37.8,(0,0,0)),(38.4,(-80,0,8)),(41.8,(-80,0,8)),(42.4,(0,0,0))])
R(BYB,[(37.6,(0,0,0)),(38.4,(-6,0,0)),(41.8,(-6,0,0)),(42.4,(0,0,0))])

A.bake(top)
M.save(f'{OUT}/A_숲.bbmodel',top,[A.json()],name='A')
json.dump({'A':{'ropes':[['by_hand_r','dg_leash']]}},open(f'{OUT}/세트정보.json','w',encoding='utf-8'))
print('ok',len(M.els),'parts','root',ROOT_X)
