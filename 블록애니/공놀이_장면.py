"""《마지막 공놀이》 장면 모형 + 움직임 (세트 A, 0~45초) → 연재/마지막공놀이/장면/A_언덕.bbmodel, 세트정보.json
   실제 세계 좌표, 위치 움직임은 x 를 뒤집어 넣음.  yaw: 0 = -z, +90 = +x, -90 = -x, 180 = +z
   던지는 자리 (-20,0,10) 에서 +x 쪽으로 던짐. 큰 나무 (0,0,40). 노을은 -z 쪽 하늘"""
import sys, os, json, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 밥그릇인물 import *
OUT=sys.argv[1] if len(sys.argv)>1 else '/home/user/youtubeshot/연재/마지막공놀이/장면'
os.makedirs(OUT,exist_ok=True)
L=45.0; random.seed(9)
M=Model(256); palette(M)
M.swatch('grass',(112,170,82),10); M.swatch('grass_d',(98,155,72),10); M.swatch('path',(205,182,140),8)
M.swatch('trunk',(115,85,55),5); M.swatch('lf_spring',(245,180,200),10); M.swatch('lf_summer',(70,150,65),12); M.swatch('lf_autumn',(225,130,50),14)
M.swatch('snow',(246,248,252),3); M.swatch('flower_y',(250,215,70),6); M.swatch('flower_w',(250,250,245),4); M.swatch('bench',(150,100,60),5)
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
def walk(p, t0, t1, amp=26, period=0.6, arms=True):
    legL,legR,armL,armR=[part(p,n) for n in ('leg_left','leg_right','arm_left','arm_right')]
    t=t0; s=1; pts=[]
    while t<t1-1e-6: pts.append((t+period/4,s)); t+=period/2; s=-s
    for g,sg in [(legL,1),(legR,-1)]+([(armL,-1),(armR,1)] if arms else []):
        R(g,[(t0,(0,0,0))]+[(tt,(sg*ss*amp,0,0)) for tt,ss in pts if tt<t1]+[(t1,(0,0,0))],'catmullrom')
def dog_gait(d, t0, t1, amp=35, period=0.5, run=False):
    fl,fr,bl,br=[part(d,n) for n in ('leg_fl','leg_fr','leg_bl','leg_br')]
    t=t0; s=1; pts=[]
    while t<t1-1e-6: pts.append((t+period/4,s)); t+=period/2; s=-s
    pairs=[(fl,1),(br,1),(fr,-1),(bl,-1)] if not run else [(fl,1),(fr,1),(bl,-1),(br,-1)]
    for g,sg in pairs: R(g,[(t0,(0,0,0))]+[(tt,(sg*ss*amp,0,0)) for tt,ss in pts if tt<t1]+[(t1,(0,0,0))],'catmullrom')
def wag(d, t0, t1, amp=30, period=0.25):
    tl=part(d,'tail'); pts=[(t0,(0,0,0))]; t=t0+period/2; s=1
    while t<t1: pts.append((t,(0,s*amp,0))); t+=period/2; s=-s
    R(tl,pts+[(t1,(0,0,0))],'catmullrom')

# ---------------- 언덕 공원 ----------------
W=[X('far',[-3000,-20,-3000],[3000,-0.4,3000],'grass')]
for x in range(-200,240,40):
    for z in range(-160,200,40): W.append(X('g',[x,-2,z],[x+40,0,z+40],'grass' if ((x+z)//40)%2 else 'grass_d'))
for i in range(90):   # 들꽃
    x=random.uniform(-90,120); z=random.uniform(-60,110)
    if -30<x<60 and -4<z<26: continue   # 공놀이 길에는 꽃이 없게 (공·발이 묻히지 않게)
    W.append(X('fl',[x,0,z],[x+1.4,1.2,z+1.4],random.choice(['flower_y','flower_w'])))
for i,(x,z,h) in enumerate([(-90,80,30),(120,90,34),(-120,-20,26),(140,0,28),(70,130,30)]):
    W+= [X('t',[x-2.5,0,z-2.5],[x+2.5,h,z+2.5],'trunk'), X('l',[x-11,h-5,z-11],[x+11,h+12,z+11],'lf_summer')]
W+= [X('bench_s',[-44,5,30],[-24,6,36],'bench'), X('bench_b',[-44,6,35],[-24,12,36],'bench'),
     X('bench_l',[-43,0,31],[-41,5,35],'trunk'), X('bench_r',[-27,0,31],[-25,5,35],'trunk')]
top.append(M.group('world',[0,0,0],W))
# 큰 나무 + 계절 잎 (14~18초에 차례로)
TX,TZ=-50,60   # 공놀이 길·카메라를 가리지 않게 옆으로
top.append(M.group('tree_trunk',[0,0,0],[X('tt',[TX-3,0,TZ-3],[TX+3,38,TZ+3],'trunk'),X('tb',[TX-8,30,TZ-1],[TX+8,32,TZ+1],'trunk')]))
SEAS=[('spring','lf_spring',14.0,15.0),('summer','lf_summer',15.0,16.0),('autumn','lf_autumn',16.0,17.0)]
for nm,col,a,b in SEAS:
    g=M.group('tree_'+nm,[0,0,0],[X('l1',[TX-16,32,TZ-16],[TX+16,50,TZ+16],col),X('l2',[TX-10,50,TZ-10],[TX+10,58,TZ+10],col)])
    top.append(g); show(g,[(a,b)] if nm!='summer' else [(0,14.0),(a,b),(18.0,45)])
win=M.group('tree_winter',[0,0,0],[X('ws',[TX-8.2,32,TZ-1.2],[TX+8.2,33,TZ+1.2],'snow'), X('wg',[TX-24,0.05,TZ-24],[TX+24,0.5,TZ+24],'snow')])
top.append(win); show(win,[(17.0,18.0)])

# ---------------- 인물 ----------------
kid=person(M,'kd_','kid',0.7); adult=person(M,'ad_','adult',1.0)
pup=dog(M,'pp_',0.8); old=dog(M,'od_',1.0,old=True)
bl=ball(M,'bl_',1.6); top+= [kid,adult,pup,old,bl]   # 인물·공을 장면에 넣음
show(kid,[(0,14.0)]); show(pup,[(0,14.0)]); show(adult,[(18.0,45)]); show(old,[(18.0,45)])

TX0,TZ0=-20,10    # 던지는 자리
def throw(p, s, t0, land, roll=4, hand=None):
    """사람 p 가 t0 에 +x 로 공을 던짐 → land(x) 에 떨어져 roll 만큼 굴러감.  돌아오는 값: 공이 멈춘 시각, 자리"""
    AR=part(p,'arm_right')
    R(AR,[(t0-0.6,(0,0,0)),(t0-0.2,(-160,0,0)),(t0,(-160,0,0)),(t0+0.15,(-40,0,0)),(t0+0.5,(0,0,0))])
    R(part(p,'body'),[(t0-0.6,(0,0,0)),(t0-0.2,(0,0,-8)),(t0+0.15,(0,0,6)),(t0+0.5,(0,0,0))])
    hx,hy=TX0+2*s,24*s
    pts=[(t0+0.15,(hx,hy,TZ0))]; dur=1.0+0.012*(land-hx); peak=hy+10+0.12*(land-hx)
    for i in range(1,11):
        u=i/10; pts.append((t0+0.15+dur*u,(hx+(land-hx)*u, 1.6+(hy-1.6)*(1-u)+4*(peak-hy)*u*(1-u)*1.0, TZ0)))
    tl=t0+0.15+dur
    pts+= [(tl+0.25,(land+roll*0.6,3.2,TZ0)),(tl+0.5,(land+roll,1.6,TZ0))]
    P(bl,pts,'catmullrom'); return tl+0.5,land+roll

def fetch(d, s, t0, tball, bx, home, speed=28.0, run=True, back=True):
    """강아지 d 가 t0 에 달려 나가 공(bx)을 물고 home(x) 로 돌아옴.  공은 입에 붙여 따라감"""
    x0=home
    ta=max(tball, t0+abs(bx-x0)/speed)
    P(d,[(t0,(x0+14*s,0,TZ0)),(ta,(bx-12*s,0,TZ0))]); yaw(d,[(t0,90),(ta,90)])
    dog_gait(d,t0,ta,amp=45 if run else 22,period=0.36 if run else 0.8,run=run)
    H=part(d,'head'); R(H,[(ta,(0,0,0)),(ta+0.3,(40,0,0)),(ta+0.6,(0,0,0))])
    if not back: return ta
    tb=ta+0.7; te=tb+abs(bx-x0)/speed
    yaw(d,[(ta+0.6,90),(tb,-90),(te,-90)])
    P(d,[(ta+0.6,(bx-12*s,0,TZ0)),(tb,(bx-12*s,0,TZ0)),(te,(x0+14*s,0,TZ0))])
    dog_gait(d,tb,te,amp=45,period=0.36,run=True)
    # 입에 문 공: 돌아올 땐 강아지 앞(-x 쪽)
    mx=lambda xx: xx-15*s
    P(bl,[(ta+0.35,(bx,1.6,TZ0)),(ta+0.6,(bx-12*s+15*s*0+3*s,10.5*s,TZ0)),(tb,(bx-12*s-15*s,10.5*s,TZ0)),(te,(mx(x0+14*s),10.5*s,TZ0)),
          (te+0.3,(mx(x0+14*s),10.5*s,TZ0)),(te+0.6,(mx(x0+14*s)-1,1.6,TZ0))])
    R(H,[(te,(0,0,0)),(te+0.3,(35,0,0)),(te+0.7,(0,0,0))])
    return te+0.6

# --- 0~14 꼬마와 어린 강아지: 세 번 던지고 물어 오기 ---
P(kid,[(0,(TX0,0,TZ0)),(14,(TX0,0,TZ0))]); yaw(kid,[(0,90),(14,90)])
P(bl,[(0,(TX0+2*0.7,24*0.7,TZ0)),(1.15,(TX0+2*0.7,24*0.7,TZ0))])
t=1.2
for k,(land,start) in enumerate([(34,1.2),(26,8.0)]):
    tl,bx=throw(kid,0.7,start,land)
    tend=fetch(pup,0.8,start+0.15,tl,bx,TX0+8,speed=34.0)
    # 공을 다시 손에
    P(bl,[(tend+0.15,(TX0+1.4,16.8,TZ0)),(13.9 if k else 7.8,(TX0+1.4,16.8,TZ0))])
    wag(pup,tend-0.6,tend+1.2)
P(pup,[(0,(TX0+8+11.2,0,TZ0)),(1.35,(TX0+8+11.2,0,TZ0))]); yaw(pup,[(0,-90),(1.0,-90),(1.35,90)])
# 쓰다듬기 (5.6~7.8)
R(part(kid,'body'),[(5.6,(0,0,0)),(6.0,(28,0,0)),(7.4,(28,0,0)),(7.8,(0,0,0))])
R(part(kid,'arm_left'),[(5.6,(0,0,0)),(6.0,(-60,0,0)),(6.4,(-50,0,0)),(6.8,(-60,0,0)),(7.2,(-50,0,0)),(7.8,(0,0,0))])
R(part(pup,'head'),[(6.0,(0,0,0)),(6.3,(-20,0,0)),(7.4,(-20,0,0)),(7.8,(0,0,0))])

# --- 14~18 세월: 나무 아래 빨간 공 ---
P(bl,[(13.99,(TX0+1.4,16.8,TZ0)),(14.0,(TX+12,1.6,TZ-16)),(18.0,(TX+12,1.6,TZ-16))])

# --- 18~45 어른과 늙은 강아지 ---
P(adult,[(18.0,(TX0,0,TZ0)),(25.0,(TX0,0,TZ0))]); yaw(adult,[(18.0,90),(25.0,90)])
P(bl,[(18.0,(TX0+2,24,TZ0)),(19.15,(TX0+2,24,TZ0))])
tl,bx=throw(adult,1.0,19.2,30,roll=4)
# 늙은 강아지: 천천히 따라가다 중간(x 4)에 멈춰 엎드림
OD=old
P(OD,[(18.0,(TX0+8,0,TZ0+5)),(19.6,(TX0+8,0,TZ0+5)),(23.4,(4,0,TZ0+1)),(24.4,(4,-3.2,TZ0+1)),(45,(4,-3.2,TZ0+1))])
yaw(OD,[(18.0,90),(23.4,90),(45,90)])
dog_gait(OD,19.6,23.4,amp=18,period=1.0)
for n,a in (('leg_fl',-80),('leg_fr',-80),('leg_bl',-80),('leg_br',-80)):   # 네 다리를 배 밑 앞으로 접음 (뒷다리 + 면 위로 솟음)
    R(part(OD,n),[(23.4,(0,0,0)),(24.4,(a,0,0)),(45,(a,0,0))])
OH=part(OD,'head'); OB=part(OD,'body')
breathe=[(24.4,(0,0,0))]; tt=24.9; s_=1
while tt<31: breathe.append((tt,(0,0,0) if s_>0 else (2,0,0))); tt+=0.6; s_=-s_
R(OB,breathe)
R(OH,[(23.4,(0,0,0)),(24.4,(25,0,0)),(26.0,(25,0,0)),(26.6,(15,-40,0)),(28.0,(15,-40,0)),(30.0,(20,-60,0)),(31.0,(20,-60,0))],'catmullrom')
# 어른: 공을 주우러 갔다가 강아지 옆으로 와 앉음
AD=adult
P(AD,[(25.0,(TX0,0,TZ0)),(27.6,(bx-3,0,TZ0-2)),(28.0,(bx-3,0,TZ0-2)),(30.2,(8,0,TZ0-6)),(30.6,(8,-10.4,TZ0-6)),(45,(8,-10.4,TZ0-6))])
yaw(AD,[(25.0,90),(27.6,90),(28.0,-90),(29.8,-90),(30.4,-150),(45,-150)])
walk(AD,25.0,27.6,amp=24,period=0.7); walk(AD,28.0,30.2,amp=24,period=0.7,arms=False)
R(part(AD,'body'),[(27.4,(0,0,0)),(27.7,(40,0,0)),(28.0,(0,0,0))])
for lg in (part(AD,'leg_left'),part(AD,'leg_right')): R(lg,[(30.2,(0,0,0)),(30.6,(-90,0,0)),(45,(-90,0,0))])
P(bl,[(tl+0.5,(bx,1.6,TZ0)),(27.7,(bx,1.6,TZ0)),(27.9,(bx-3,13,TZ0-3)),(30.2,(9,13,TZ0-4)),(30.6,(8.5,5,TZ0-2.5)),(31.6,(8.5,5,TZ0-2.5))])
# 쓰다듬기 (30.6~31.6) → 공을 코앞에 살짝 굴려 줌 (31.6~33)
AL=part(AD,'arm_left'); AR=part(AD,'arm_right')
R(AL,[(30.6,(0,0,0)),(30.9,(-55,0,-10)),(31.2,(-45,0,-10)),(31.5,(-55,0,-10)),(31.8,(0,0,0)),(36.0,(0,0,0)),(36.4,(-50,0,-10)),(45,(-50,0,-10))])
R(AR,[(31.6,(0,0,0)),(32.0,(-45,0,0)),(32.6,(-30,0,0)),(33.0,(0,0,0))])
NX,NZ=4+15+1.8,TZ0+1   # 늙은 강아지 코앞 (+x 쪽을 봄)
P(bl,[(31.6,(8.5,5,TZ0-2.5)),(32.0,(10,1.6,TZ0-2)),(33.0,(NX,1.6,NZ)),(34.2,(NX,1.6,NZ)),(34.6,(NX+2.5,1.6,NZ)),(45,(NX+2.5,1.6,NZ))],'catmullrom')
R(OH,[(31.0,(20,-60,0)),(31.8,(25,0,0)),(33.2,(20,0,0)),(33.8,(40,0,0)),(34.3,(42,0,0)),(34.7,(15,0,0)),(36.0,(5,30,0)),(45,(10,40,0))],'catmullrom')
wag(OD,34.6,45,amp=26,period=0.35)
R(part(AD,'head'),[(30.6,(25,40,0)),(33.0,(30,40,0)),(36.0,(15,30,0)),(38.0,(-5,0,0)),(45,(-5,0,0))],'catmullrom')

A.bake(top)
M.save(f'{OUT}/A_언덕.bbmodel',top,[A.json()],name='A')
json.dump({'A':{'ropes':[]}},open(f'{OUT}/세트정보.json','w',encoding='utf-8'))
print('ok',len(M.els),'cubes')
