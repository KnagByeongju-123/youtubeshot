"""《같이 들어온 결승선》 장면 모형 + 움직임 (세트 A 운동장, 0~45초) → 연재/같이들어온결승선/장면/A_운동장.bbmodel, 세트정보.json
   실제 세계 좌표, 위치 움직임은 x 를 뒤집어 넣음(P).  yaw: 0 = -z, +90 = +x, -90 = -x, 180 = +z
   직선 트랙은 x 방향: 출발선 x=-70 → 결승선 FX=50.  레인 z: 파랑 -24 · 서연 -12 · 하준 0 · 빨강 12 · 보라 24
   끝에 손잡는 줄 z: 파랑 -20 · 서연 -10 · 하준 0 · 빨강 10 · 보라 20 (간격 10 = 아래로 내린 손이 맞닿음)"""
import sys, os, json, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import 밥그릇인물 as BG
from 결승선인물 import *
from 블록인물 import find
OUT=sys.argv[1] if len(sys.argv)>1 else '/home/user/youtubeshot/연재/같이들어온결승선/장면'
os.makedirs(OUT,exist_ok=True)
L=45.0; random.seed(5)
M=Model(256); BG.palette(M); palette(M)
M.swatch('grass',(112,170,82),10); M.swatch('grass_d',(98,155,72),10)
M.swatch('dirt',(196,140,95),8); M.swatch('dirt_d',(184,128,85),8); M.swatch('line',(250,250,248),2)
M.swatch('wall',(238,228,205),5); M.swatch('wall_d',(210,198,175),5); M.swatch('roof',(150,70,60),6)
M.swatch('win',(150,195,225),4); M.swatch('trunk',(115,85,55),5); M.swatch('leaf',(70,150,65),12)
M.swatch('tent',(245,245,245),2); M.swatch('tent_b',(60,110,200),3); M.swatch('metal',(150,150,155),3)
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
def swing(p, t0, t1, ampL, ampR, armamp, period, lean=0):
    """걷기·달리기: 다리 엇갈려 흔들기 (ampL 왼다리, ampR 오른다리), 팔은 반대로"""
    legL,legR,armL,armR,body=[part(p,n) for n in ('leg_left','leg_right','arm_left','arm_right','body')]
    t=t0; s=1; pts=[]
    while t<t1-1e-6: pts.append((t+period/4,s)); t+=period/2; s=-s
    pts=[q for q in pts if q[0]<t1]
    for g,sg,amp in [(legL,1,ampL),(legR,-1,ampR)]+([(armL,-1,armamp),(armR,1,armamp)] if armamp else []):
        R(g,[(t0,(0,0,0))]+[(tt,(sg*ss*amp,0,0)) for tt,ss in pts]+[(t1,(0,0,0))],'catmullrom')
    if lean: R(body,[(t0,(0,0,0)),(t0+0.25,(lean,0,0)),(t1-0.2,(lean,0,0)),(t1,(0,0,0))])
def run(p,t0,t1,amp=55,period=0.36): swing(p,t0,t1,amp,amp,amp,period,lean=12)
def walk(p,t0,t1,amp=24,period=0.7,arms=True): swing(p,t0,t1,amp,amp,amp if arms else 0,period)
def limp(p,t0,t1,period=0.8,arms=True,lean=0):
    """하준 걸음: 보조기 다리(오른다리)는 거의 안 굽히고 끌듯이, 몸이 그쪽으로 살짝 기욺"""
    swing(p,t0,t1,30,9,16 if arms else 0,period)
    body=part(p,'body'); t=t0; s=1; pts=[(t0,(lean,0,0))]
    while t<t1-1e-6: pts.append((t+period/4,(lean,0,-5*s))); t+=period/2; s=-s
    R(body,[q for q in pts if q[0]<t1]+[(t1,(lean,0,0))],'catmullrom')
def keys(g, pts):
    """위치·방향 키 한꺼번에: (t, x, z, yaw[, y])"""
    P(g,[(t,(x,(r[0] if r else 0),z)) for t,x,z,y,*r in pts]); yaw(g,[(t,y) for t,x,z,y,*r in pts])

# ---------------- 운동장 ----------------
W=[X('far',[-3000,-20,-3000],[3000,-0.4,3000],'grass')]
for x in range(-160,200,40):
    for z in range(-80,80,40): W.append(X('d',[x,-2,z],[x+40,0,z+40],'dirt' if ((x+z)//40)%2 else 'dirt_d'))
for x in range(-240,280,40):
    for z in (-120,80):
        W.append(X('g',[x,-2,z],[x+40,0,z+40],'grass' if ((x+z)//40)%2 else 'grass_d'))
for z in (-30,-18,-6,6,18,30):   # 레인 흰 줄
    W.append(X('lane',[-150,0,z-0.3],[190,0.1,z+0.3],'line'))
W.append(X('start',[-74.5,0.02,-30.3],[-73.5,0.13,30.3],'line'))       # 출발선 (레인 줄보다 살짝 높게)
FX=50
W.append(X('finish',[FX-0.5,0.02,-30.3],[FX+0.5,0.13,30.3],'line'))
# 학교 건물 (뒤쪽 +z), 창문은 벽보다 0.2 앞
SZ=140
W+= [X('school',[-130,0,SZ],[130,52,SZ+30],'wall',north='wall'), X('school_roof',[-133,52,SZ-3],[133,56,SZ+33],'roof'),
     X('school_base',[-130.3,0,SZ-0.3],[130.3,4,SZ+30.3],'wall_d'), X('door',[-8,0,SZ-0.5],[8,14,SZ-0.2],'trunk')]
for fl in (10,28):
    for x in range(-120,120,16):
        if fl==10 and -12<x<12: continue
        W.append(X('win',[x+2,fl,SZ-0.25],[x+12,fl+12,SZ],'win'))
# 나무 (트랙 양옆 멀리)
for x,z,h in [(-140,100,30),(-90,105,26),(90,104,28),(150,98,32),(-150,-100,28),(-60,-110,26),(60,-108,30),(150,-100,26)]:
    W+= [X('t',[x-2.5,0,z-2.5],[x+2.5,h,z+2.5],'trunk'), X('l',[x-10,h-5,z-10],[x+10,h+12,z+10],'leaf')]
for z in range(-130,140,26):   # 트랙 끝(-x) 뒤 나무 줄 (멀리 찍을 때 배경)
    h=24+(z//26)%3*4; W+= [X('t',[-182.5,0,z-2.5],[-177.5,h,z+2.5],'trunk'), X('l',[-190,h-5,z-10],[-170,h+12,z+10],'leaf')]
top.append(M.group('world',[0,0,0],W))

# ---------------- 운동회 날에만: 만국기·천막·결승 테이프·응원하는 어른 ----------------
fest=[]
for z in (-52,52):
    for x in (-100,100): fest.append(X('fpole',[x-0.6,0,z-0.6],[x+0.6,34,z+0.6],'metal'))
    fest.append(flags(M,'fl%d_'%z,-100,100,33,z,n=40))
TZ=66   # 천막 (뒤쪽, 학교 앞)
for x in (-34,34):
    for z in (TZ-8,TZ+8): fest.append(X('tpole',[x-0.5,0,z-0.5],[x+0.5,24,z+0.5],'metal'))
for i,x in enumerate(range(-36,36,8)):
    fest.append(X('troof',[x,24,TZ-10],[x+8,26.5,TZ+10],'tent' if i%2 else 'tent_b'))
for z in (-32.5,32.5):   # 결승 기둥 (흰·빨강 줄무늬)
    for i in range(0,26,4): fest.append(X('pole',[FX-0.8,i,z-0.8],[FX+0.8,min(i+4,26),z+0.8],'pole' if (i//4)%2==0 else 'pole_r'))
    fest.append(X('pole_top',[FX-1.1,26,z-1.1],[FX+1.1,27.2,z+1.1],'pole_r'))
TY=13.5   # 테이프 높이 (아이 가슴)
tape_l=M.group('tape_l',[FX,TY,-32.5],[X('tape',[FX-0.1,TY-0.6,-31.7],[FX+0.1,TY+0.6,0],'tie')])
tape_r=M.group('tape_r',[FX,TY,32.5],[X('tape',[FX-0.1,TY-0.6,0],[FX+0.1,TY+0.6,31.7],'tie')])
fest_g=M.group('fest',[0,0,0],fest); top+= [fest_g,tape_l,tape_r]
show(fest_g,[(23.0,45)]); show(tape_l,[(23.0,45)]); show(tape_r,[(23.0,45)])
# 테이프가 끊겨 양쪽 기둥 쪽으로 휘어 넘어감 (40.25)
TB=40.25
R(tape_l,[(TB,(0,0,0)),(TB+0.5,(0,-70,-30)),(TB+1.2,(0,-80,-55)),(45,(0,-80,-55))],'catmullrom')
R(tape_r,[(TB,(0,0,0)),(TB+0.5,(0,70,30)),(TB+1.2,(0,80,55)),(45,(0,80,55))],'catmullrom')

adults=[]
for i,(kind,x) in enumerate([('dad',-24),('adult',-12),('dad',0),('adult',12),('dad',24)]):
    a=BG.person(M,'ad%d_'%i,kind,0.95); top.append(a); adults.append((a,x))
    show(a,[(23.0,45)])
    keys(a,[(0,x,TZ,0),(45,x,TZ,0)])   # 트랙(-z)을 봄
    AL,AR=part(a,'arm_left'),part(a,'arm_right')
    # 손뼉: 두 팔을 앞으로 들어 모았다 벌렸다 (출발 24.0~25.5, 끝 40.3~)
    for a0,a1 in ((24.0,25.6),(40.4,45)):
        pl=[(a0,(0,0,0)),(a0+0.3,(-70,0,-18))]; pr=[(a0,(0,0,0)),(a0+0.3,(-70,0,18))]; t=a0+0.3+0.05*i; s=1
        while t<a1-0.2: pl.append((t,(-70,0,-18 if s>0 else -6))); pr.append((t,(-70,0,18 if s>0 else 6))); t+=0.18; s=-s
        R(AL,pl+[(a1,(0,0,0))]); R(AR,pr+[(a1,(0,0,0))])

# ---------------- 아이들 ----------------
HJ=kid(M,'hj_','hajun'); SY=kid(M,'sy_','seoyeon'); RD=kid(M,'rd_','red',0.75); BL=kid(M,'bl_','blue'); PU=kid(M,'pu_','purple')
top+= [HJ,SY,RD,BL,PU]
S0=-70; LANE={'bl':-24,'sy':-12,'hj':0,'rd':12,'pu':24}; ROW={'bl':-24,'sy':-12,'hj':0,'rd':12,'pu':24}
FOUR=[('sy',SY),('rd',RD),('bl',BL),('pu',PU)]
SIT=-7.3   # 앉을 때 몸 내리기 (다리 길이 12*0.7 - 두께)

# ===== 1부 (0~6) 연습: 넷은 앞서 달려 나가고 하준은 혼자 남음 =====
GO=1.0
for i,(k,g) in enumerate(FOUR):
    sp=30-1.2*i; z=LANE[k]; x1=S0+sp*4.6
    keys(g,[(0,S0,z,90),(GO+0.1,S0,z,90),(GO+0.1+4.6,x1,z,90),(GO+5.0,x1+5,z,90),(5.99,x1+5,z,90)])
    run(g,GO+0.1,GO+4.9)
HX1=S0+6.0*3.4   # 하준이 멈춘 자리 (-49.6)
keys(HJ,[(0,S0,0,90),(GO+0.3,S0,0,90),(GO+3.4,HX1,0,90),(5.99,HX1,0,90)])
limp(HJ,GO+0.3,GO+3.4)   # 6칸쯤 가다 멈춤
H=part(HJ,'head')
R(H,[(GO+3.4,(0,0,0)),(GO+3.9,(0,0,0)),(GO+4.2,(-10,0,0)),(GO+4.5,(28,0,0)),(6.0,(28,0,0))])   # 앞을 올려다봤다가 다리를 내려다봄

# ===== 2부 (6~11) 흐린 오후: 하준은 트랙 가에 앉아 고개 숙임, 넷은 결승선 너머에서 뛰어놂 =====
HS=(-30,-36)
keys(HJ,[(6.0,HS[0],HS[1],90,SIT),(15.3,HS[0],HS[1],90,SIT)])
for lg in ('leg_left','leg_right'): R(part(HJ,lg),[(5.99,(0,0,0)),(6.0,(-90,0,0)),(15.0,(-90,0,0)),(15.9,(0,0,0))])
R(H,[(6.0,(30,0,0)),(9.4,(30,0,0)),(9.9,(5,25,0)),(10.6,(5,25,0)),(11.0,(30,0,0)),(14.4,(30,0,0)),(14.8,(-15,0,0)),(15.6,(-10,0,0)),(16.2,(0,0,0))],'catmullrom')
R(part(HJ,'body'),[(5.99,(0,0,0)),(6.0,(14,0,0)),(14.4,(14,0,0)),(14.8,(0,0,0))])
R(part(HJ,'arm_left'),[(5.99,(0,0,0)),(6.0,(-40,0,0)),(14.6,(-40,0,0)),(15.0,(-100,0,0)),(15.6,(-70,0,0)),(16.0,(0,0,0))])   # 무릎을 감싼 팔 → 손 내밂
R(part(HJ,'arm_right'),[(5.99,(0,0,0)),(6.0,(-40,0,0)),(14.6,(-40,0,0)),(15.0,(-100,0,0)),(15.6,(-70,0,0)),(16.0,(0,0,0))])
PLAY=[('sy',SY,56,-8,-1),('rd',RD,62,6,0.12),('bl',BL,53,10,0.25),('pu',PU,64,-4,0.37)]
for k,g,x,z,ph in PLAY:
    keys(g,[(6.0,x,z,random.choice([-60,40,150,-140])),(10.99,x,z,random.choice([-60,40,150,-140]))])
    pts=[]; t=6.2+ph
    while t<10.8: pts+= [(t,(-x,0,z)),(t+0.2,(-x,3.2,z)),(t+0.4,(-x,0,z))]; t+=0.75
    A.add(g,'position',pts)
    R(part(g,'arm_left'),[(6.0,(0,0,150)),(11.0,(0,0,150))]); R(part(g,'arm_right'),[(6.0,(0,0,-150)),(11.0,(0,0,-150))])

# ===== 3부 (11~17) 노을: 서연이 돌아와 손을 내밀어 일으킴 =====
SYW=[(11.0,-2,-36,-90),(13.0,-22,-36,-90),(13.2,-22,-36,-90)]
keys(SY,[(11.0,4,-36,-90),(13.0,-16,-36,-90),(14.2,-16,-36,-90),(14.5,-16.5,-36,-90),(15.95,-16.5,-36,-90),
         (16.0,-28,-48,90),(16.4,-28,-48,90),(16.99,-24,-48,90)])
walk(SY,11.0,13.0,amp=26,period=0.6)
R(part(SY,'arm_left'),[(13.0,(0,0,0)),(13.3,(0,0,0))])
# 13.0~14.2: 서 있다가 → 몸을 숙여 손을 내밂 (14.5~15.3) → 끌어당김 (15.3~15.9)
R(part(SY,'body'),[(14.4,(0,0,0)),(14.8,(30,0,0)),(15.4,(30,0,0)),(15.9,(5,0,0)),(16.2,(0,0,0))])
R(part(SY,'arm_right'),[(11.0,(0,0,0)),(13.0,(0,0,0)),(14.4,(0,0,0)),(14.8,(-20,0,0)),(15.4,(-20,0,0)),(15.9,(-45,0,0)),(16.2,(0,0,-15)),(17.0,(0,0,-15))])
R(part(SY,'head'),[(13.0,(0,0,0)),(13.4,(15,0,0)),(14.3,(15,0,0)),(14.8,(30,0,0)),(15.9,(0,0,0))])
# 일어남: 15.3~15.9 몸 올림
keys(HJ,[(15.3,HS[0],HS[1],90,SIT),(15.9,HS[0],HS[1],90,0),(16.4,HS[0],HS[1],90,0),(16.99,HS[0]+4,HS[1],90,0)])
R(part(HJ,'arm_left'),[(16.0,(0,0,0)),(16.2,(0,0,15)),(17.0,(0,0,15))])   # 서연과 손잡음 (서연이 왼쪽 -z)
limp(HJ,16.4,16.99,arms=False); walk(SY,16.4,16.99,arms=False)

# ===== 4부 (17~23) 날마다 둘이 나란히 달림, 친구 셋이 트랙 가에서 바라보다 손 흔듦 =====
SEG=[(17.0,19.0,-62,8),(19.0,21.0,-24,10),(21.0,23.0,8,12)]
for t0,t1,x0,sp in SEG:
    x1=x0+sp*(t1-t0)
    keys(HJ,[(t0,x0,0,90),(t1-0.01,x1,0,90)]); keys(SY,[(t0,x0,-12,90),(t1-0.01,x1,-12,90)])
    limp(HJ,t0,t1-0.01,period=0.62 if sp<11 else 0.5,lean=6); run(SY,t0,t1-0.01,amp=34,period=0.5)
WATCH=[('rd',RD,22),('bl',BL,30),('pu',PU,38)]
for k,g,x in WATCH:
    keys(g,[(17.0,x,40,0),(22.99,x,40,0)])
    ar=part(g,'arm_right')
    if k!='bl':
        R(ar,[(17.0,(0,0,0)),(21.6,(0,0,0)),(21.9,(0,0,-150)),(22.15,(0,0,-125)),(22.4,(0,0,-155)),(22.65,(0,0,-125)),(22.99,(0,0,-150))])
    else:   # 파랑은 두 손을 입가에 모아 응원
        R(ar,[(17.0,(0,0,0)),(21.6,(0,0,0)),(21.9,(-120,0,25)),(22.99,(-120,0,25))]); R(part(g,'arm_left'),[(17.0,(0,0,0)),(21.6,(0,0,0)),(21.9,(-120,0,-25)),(22.99,(-120,0,-25))])
    R(part(g,'arm_left' if k!='bl' else 'head'),[(17.0,(0,0,0)),(22.99,(0,0,0))])
R(part(SY,'arm_left'),[(16.99,(0,0,0)),(17.0,(0,0,0))])
for g in (RD,PU,BL):   # 1부 손 위치(놀이 때 든 팔) 초기화
    R(part(g,'arm_left'),[(11.0,(0,0,150)),(11.02,(0,0,0))]); R(part(g,'arm_right'),[(11.0,(0,0,-150)),(11.02,(0,0,0))])
for g in (SY,):
    R(part(g,'arm_left'),[(6.0,(0,0,150)),(10.99,(0,0,150)),(11.0,(0,0,0))]); R(part(g,'arm_right'),[(6.0,(0,0,-150)),(10.99,(0,0,-150)),(11.0,(0,0,0))])
# 3부 동안 친구 셋은 화면 밖(결승선 너머)
for k,g,x,z,ph in PLAY[1:]: keys(g,[(11.0,x+40,z,0),(16.99,x+40,z,0)])

# ===== 5부 (23~29) 운동회: 다섯이 출발선 → 넷이 앞서 나감, 하준 뒤처짐 =====
GO2=24.0; STOP=41.5   # 넷이 멈추는 자리 (테이프 FX=50 바로 앞)
for i,(k,g) in enumerate(FOUR):
    z=LANE[k]; sp=26-0.6*i; t_arr=GO2+0.1+(STOP-1.5-S0)/sp
    keys(g,[(23.0,S0,z,90),(GO2+0.1,S0,z,90),(t_arr,STOP-1.5,z,90),(29.0,STOP,z,90)])
    run(g,GO2+0.1,min(t_arr+0.3,29.0))
MX=-10; T_H=GO2+0.3+(MX-S0)/7.0   # 하준이 MX 에 닿는 때 (32.87)
keys(HJ,[(23.0,S0,0,90),(GO2+0.3,S0,0,90),(T_H,MX,0,90),(33.4,MX,0,90)])
limp(HJ,GO2+0.3,T_H,period=0.7)

# ===== 6부 (29~34) 결승 앞에서 넷이 멈춰 돌아섬 → 되돌아 뛰어가 하준 옆에 섬 =====
BACK={'sy':30.0,'rd':30.55,'bl':30.7,'pu':30.85}
for k,g in FOUR:
    tb=BACK[k]; ta=tb+(STOP-MX)/26.0
    keys(g,[(29.0,STOP,LANE[k],90),(29.25,STOP,LANE[k],90),(29.8,STOP,LANE[k],-90),(tb,STOP,LANE[k],-90),
            (ta,MX+1.5,ROW[k],-90),(ta+0.25,MX,ROW[k],-90),(ta+0.75,MX,ROW[k],90),(34.6,MX,ROW[k],90)])
    run(g,tb,ta+0.2,amp=50,period=0.38)
    R(part(g,'head'),[(29.0,(0,0,0)),(29.5,(-5,0,0)),(29.8,(10,0,0)),(tb,(0,0,0))])
R(part(HJ,'head'),[(29.5,(0,0,0)),(31.6,(0,0,0)),(32.0,(-12,0,0)),(32.9,(-12,0,0)),(33.4,(-5,-30,0)),(33.9,(-5,30,0)),(34.4,(0,0,0))],'catmullrom')

# ===== 7부 (34~40) 다섯이 손잡고 한 줄로 걸어감 =====
HOLD=33.9; W0=34.6; W1=40.2; XW=FX-1.5   # 40.2 에 가슴이 테이프에 닿음
for k,g in [('hj',HJ)]+FOUR:
    al,ar=part(g,'arm_left'),part(g,'arm_right')
    lz=15 if k!='bl' else 0; rz=-15 if k!='pu' else 0    # 맨 끝 아이 바깥손은 내림 (왼쪽 = -z 쪽 이웃)
    R(al,[(HOLD-0.4,(0,0,0)),(HOLD,(0,0,lz)),(41.3,(0,0,lz)),(41.8,(0,0,170)),(45,(0,0,170))])
    R(ar,[(HOLD-0.4,(0,0,0)),(HOLD,(0,0,rz)),(41.3,(0,0,rz)),(41.8,(0,0,-170)),(45,(0,0,-170))])
    z=ROW[k]
    keys(g,[(W0,MX,z,90),(W1,XW,z,90),(41.2,XW+8,z,90),(45,XW+8,z,90)])
    if k=='hj': limp(g,W0,41.2,period=0.75,arms=False)
    else: walk(g,W0,41.2,amp=20,period=0.75,arms=False)
    # 테이프를 끊은 뒤 손을 번쩍 들고 깡충
    pts=[]; t=42.0+0.06*list(ROW).index(k)
    while t<44.4: pts+= [(t,(-(XW+8),0,z)),(t+0.18,(-(XW+8),2.6,z)),(t+0.36,(-(XW+8),0,z))]; t+=0.7
    A.add(g,'position',pts)
    R(part(g,'head'),[(41.3,(0,0,0)),(41.8,(-15,0,0)),(45,(-15,0,0))])

A.bake(top)
M.save(f'{OUT}/A_운동장.bbmodel',top,[A.json()],name='A')
json.dump({'A':{'ropes':[]}},open(f'{OUT}/세트정보.json','w',encoding='utf-8'))
print('ok',len(M.els),'cubes', 'T_H=%.2f'%T_H)
