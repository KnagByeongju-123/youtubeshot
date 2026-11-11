"""《빈 밥그릇》 장면 모형 + 움직임 (세트 A 하나, 시간 = 영상 시간 0~45초)
   → 연재/빈밥그릇/장면/A_동네.bbmodel, 세트정보.json
   좌표: 실제 세계 좌표로 적고, 위치 움직임은 x 를 뒤집어 넣음(Blockbench 위치 x 반대).
   방향(yaw): 0 = -z 를 봄, +90 = +x, -90 = -x, 180 = +z.
   배치: 차도 z -60..0 (x 방향으로 뻗음), 인도 z 0..40, 집 앞마당 z 40..80, 집 z 80~"""
import sys, os, json, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 밥그릇인물 import *
OUT=sys.argv[1] if len(sys.argv)>1 else '/home/user/youtubeshot/연재/빈밥그릇/장면'
os.makedirs(OUT,exist_ok=True)
L=45.0

M=Model(256); palette(M)
M.swatch('asphalt',(78,80,86),6); M.swatch('lane',(240,205,70),4); M.swatch('walk',(196,192,184),6); M.swatch('curb',(160,158,152),4)
M.swatch('grass',(108,165,80),10); M.swatch('grass_d',(95,150,70),10)
for n,cc in [('wall1',(235,225,205)),('wall2',(205,225,235)),('wall3',(240,205,190)),('wall4',(220,232,200))]: M.swatch(n,cc,5)
M.swatch('roof1',(170,70,55),6); M.swatch('roof2',(70,95,130),6); M.swatch('roof3',(95,120,80),6)
M.swatch('win',(150,195,225),3); M.swatch('frame',(250,250,250),2); M.swatch('door',(130,85,50),5)
M.swatch('trunk',(115,85,55),5); M.swatch('leaf',(80,150,70),14); M.swatch('leaf2',(105,170,80),14)
M.swatch('step',(175,170,165),6); M.swatch('fence',(235,235,230),3)

A=Anim(L); top=[]

# ---------------- 동네 ----------------
def C(n,fr,to,col,**f): return M.cube(n,fr,to,col,**f)
W=[]
W.append(C('far_ground',[-3000,-20,-3000],[3000,-0.4,3000],'grass'))
X0,X1=-400,1000
for x in range(X0,X1,100):
    W+= [C('road',[x,-2,-60],[x+100,0,0],'asphalt'), C('walk',[x,-2,0],[x+100,0.4,40],'walk'), C('curb',[x,-2,-1.5],[x+100,0.8,0],'curb'),
         C('walk2',[x,-2,-90],[x+100,0.4,-60],'walk')]
    for xx in range(x,x+100,40): W.append(C('lane',[xx,0,-31],[xx+20,0.15,-29],'lane'))
    W.append(C('yard',[x,-2,40],[x+100,0.2,80],'grass' if (x//100)%2 else 'grass_d'))
def house(n,x,z,w,d,h,wall,roof,door=True,yaw_front=-1):
    """yaw_front -1: 앞(문)이 -z 쪽 (길 쪽).  +1: 앞이 +z (길 건너 집)"""
    k=[C(n+'_wall',[x-w/2,0,z],[x+w/2,h,z+d],wall)]
    for i in range(4): k.append(C(n+'_roof',[x-w/2-3+i*w/8,h+i*7,z-3],[x+w/2+3-i*w/8,h+(i+1)*7,z+d+3],roof))
    fz=z if yaw_front<0 else z+d; s=-1 if yaw_front<0 else 1
    def face(a,b,y0,y1,col):  # 앞면에 붙는 얇은 판
        return C(n+'_f',[a,y0,min(fz,fz+s*0.6)],[b,y1,max(fz,fz+s*0.6)],col)
    if door: k+= [face(x-6,x+6,0,22,'door'), face(x+3,x+4.5,10,12,'tire')]
    for wx in (x-w/2+8, x+w/2-22):
        if door and abs(wx+7-x)<12: continue
        k+= [face(wx-1,wx+15,13,29,'frame'), face(wx,wx+14,14,28,'win')]
    return k
cols=['wall1','wall2','wall3','wall4']; roofs=['roof1','roof2','roof3']
i=0
for x in range(-380,980,95):
    if x==-0: pass
    W+= house(f'h{i}',x if x!=-0 else 0,85,70,46,34,cols[i%4],roofs[i%3])
    W+= house(f'g{i}',x+40,-160,64,44,32,cols[(i+2)%4],roofs[(i+1)%3],yaw_front=1)
    i+=1
# 주인공 집 (x 0): 문 앞 계단 + 담장 (문 앞만 열림)
HX=0
W+= house('home',HX,85,80,48,36,'wall1','roof1')
W+= [C('step',[HX-14,0,74],[HX+14,5,85],'step')]
for a,b in ((-40,-12),(12,40)): W.append(C('fence',[HX+a,0,40],[HX+b,9,42],'fence'))
def tree(n,x,z,h=40):
    return [C(n+'_t',[x-2.5,0,z-2.5],[x+2.5,h,z+2.5],'trunk'), C(n+'_l1',[x-12,h-6,z-12],[x+12,h+12,z+12],'leaf'),
            C(n+'_l2',[x-8,h+12,z-8],[x+8,h+20,z+8],'leaf2')]
for j,x in enumerate(range(-330,980,75)):
    if not (abs(x-(-60))<20 or abs(x)<45 or 370<x<480):   # 이야기 자리를 가리는 나무는 뺌
        W+= tree(f'tr{j}',x,34,38+(j%3)*6)
    W+= tree(f'tq{j}',x+30,-75,36+(j%2)*8)
# 강아지 비 피하는 상자 (옆으로 눕힌 상자, 입구가 -x 쪽)
BX,BZ=-66,30
W+= [C('shelter_top',[BX-9,14,BZ-9],[BX+9,15,BZ+9],'box',up='box_t'), C('shelter_back',[BX+8,0,BZ-9],[BX+9,15,BZ+9],'box'),
     C('shelter_s',[BX-9,0,BZ+8],[BX+9,15,BZ+9],'box'), C('shelter_n',[BX-9,0,BZ-9],[BX+9,15,BZ-8],'box'),
     C('shelter_b',[BX-9,0,BZ-9],[BX+9,0.6,BZ+9],'box_t')]
top.append(M.group('world',[0,0,0],W))

# ---------------- 도우미 ----------------
def P(g, pts, interp='linear'):
    """위치 키 (실제 좌표) — x 를 뒤집어 넣음"""
    A.add(g,'position',[(t,(-v[0],v[1],v[2])) for t,v in pts],interp)
def R(g, pts, interp='linear'): A.add(g,'rotation',pts,interp)
def S(g, pts): A.add(g,'scale',[(t,(v,v,v)) for t,v in pts],'step' if False else 'linear')
def show(g, spans, eps=0.02):
    """spans = [(보이기 시작, 숨기기)...] — 그 사이만 크기 1"""
    pts=[(0,0)]
    for a,b in spans:
        pts+= [(max(0,a-eps),0),(a,1),(b,1),(b+eps,0)]
    S(g,pts)
def yaw(g, pts, interp='linear'): R(g,[(t,(0,y,0)) for t,y in pts],interp)
def part(g, name): return find(g, g['name'].replace('root',name))

def walk(p, t0, t1, amp=30, period=0.6, arms=True):
    """사람 걷기/뛰기: 다리(팔) 흔들기"""
    legL,legR,armL,armR=[part(p,n) for n in ('leg_left','leg_right','arm_left','arm_right')]
    t=t0; s=1; pts=[]
    while t<t1-1e-6: pts.append((t+period/4,s)); t+=period/2; s=-s
    gs=[(legL,1),(legR,-1)]+([(armL,-1),(armR,1)] if arms else [])
    for g,sg in gs:
        R(g,[(t0,(0,0,0))]+[(tt,(sg*ss*amp,0,0)) for tt,ss in pts if tt<t1]+[(t1,(0,0,0))],'catmullrom')

def dog_gait(d, t0, t1, amp=35, period=0.5, run=False):
    fl,fr,bl,br=[part(d,n) for n in ('leg_fl','leg_fr','leg_bl','leg_br')]
    t=t0; s=1; pts=[]
    while t<t1-1e-6: pts.append((t+period/4,s)); t+=period/2; s=-s
    pairs=[(fl,1),(br,1),(fr,-1),(bl,-1)] if not run else [(fl,1),(fr,1),(bl,-1),(br,-1)]
    for g,sg in pairs:
        R(g,[(t0,(0,0,0))]+[(tt,(sg*ss*amp,0,0)) for tt,ss in pts if tt<t1]+[(t1,(0,0,0))],'catmullrom')

def wag(d, t0, t1, amp=30, period=0.25):
    tl=part(d,'tail'); pts=[(t0,(0,0,0))]; t=t0+period/2; s=1
    while t<t1: pts.append((t,(0,s*amp,0))); t+=period/2; s=-s
    R(tl,pts+[(t1,(0,0,0))],'catmullrom')

def path(pts):
    """[(t,x,z)] → 위치 키 (y 0)"""
    return [(t,(x,0,z)) for t,x,z in pts]

def face_dir(dx,dz):
    """(dx,dz) 쪽을 보는 yaw (도)"""
    return math.degrees(math.atan2(dx,-dz))

# ---------------- 강아지 ----------------
dog_=dog(M,'dg_',1.0,with_bowl=True); top.append(dog_)
DH=part(dog_,'head'); DB=part(dog_,'body'); MB=part(dog_,'mbowl')
DX,DZ=-50,32
# 0~5 비: 상자 옆에서 떪 / 5~11 꼬마를 봄 / 11~17 날마다 / 17~ 이삿날 / 23~ 쫓아감 / 35~ 만남 / 40~ 안김
dpos=[(0,DX,DZ),(10.9,DX,DZ),
      (11.0,-50,32),(12.99,-50,32),                     # (a) 아침: 그릇 앞에서 먹기
      (13.0,52,20),(15.0,4,20),(15.01,-11,68),(16.99,-11,68),   # (b) 졸졸 따라감 → (c) 저녁 계단 옆
      (17.0,DX,DZ),(26.0,DX,DZ),(26.6,-44,14),(27.2,-34,4)]
# 쫓아 달리기: 27.2초 x -34 → 36.9초 x 389 (z 4)
x=-34; t=27.2
while t<36.9-1e-6:
    t2=min(36.9,t+0.5); x=-34+(389+34)*(t2-27.2)/(36.9-27.2); dpos.append((t2,x,4)); t=t2
dpos+= [(45,389,4)]
P(dog_,[(t,(x,0,z)) for t,x,z in dpos])
# 안기기 (40.0~): 위로 들려 꼬마 품에
P(dog_,[(40.0,(389,0,4)),(40.8,(407,9,4)),(45,(407,9,4))])
dyaw=[(0,0),(10.9,0),(11.0,0),(12.99,0),(13.0,-90),(14.99,-90),(15.0,-90),(15.01,0),(16.99,0),
      (17.0,0),(23.4,0),(24.0,60),(25.0,60),(25.2,0),(26.0,0),(26.6,40),(27.2,90),(36.9,90),(40.0,90),(40.8,180),(45,180)]
yaw(dog_,dyaw)
# 떨기 (0~5)
sh=[(0,(0,0,0))]; t=0.1; s=1
while t<5.0: sh.append((t,(0,0,s*3))); t+=0.12; s=-s
sh+= [(5.1,(0,0,0))]
# 몸 위아래 (달리기)
t=27.3; s=1
while t<36.8: sh.append((t,(s*4,0,0))); t+=0.2; s=-s
sh+= [(36.9,(0,0,0))]
R(DB,sh)
# 머리: 고개 숙임(+x)·듦(-x)·돌림(y)
R(DH,[(0,(18,0,0)),(5.0,(18,0,0)),(5.6,(0,-25,0)),(7.4,(0,-35,0)),(8.0,(0,10,0)),(10.0,(0,0,0)),(10.6,(-20,0,0)),(10.99,(-20,0,0)),
      (11.0,(30,0,0)),(11.4,(38,0,0)),(11.8,(30,0,0)),(12.2,(38,0,0)),(12.6,(30,0,0)),(12.99,(30,0,0)),
      (13.0,(0,0,0)),(15.0,(0,0,0)),(15.01,(-15,20,0)),(16.99,(-15,20,0)),
      (17.0,(0,0,0)),(19.0,(0,0,0)),(19.4,(0,40,0)),(22.6,(0,40,0)),(23.4,(0,30,0)),(24.0,(0,0,0)),(25.2,(0,0,0)),
      (25.5,(35,0,0)),(25.8,(28,0,0)),(26.0,(40,0,0)),(26.3,(10,0,0)),(27.0,(0,0,0)),
      (36.9,(0,0,0)),(37.4,(40,0,0)),(38.0,(40,0,0)),(38.4,(-25,0,0)),(39.99,(-25,0,0)),(40.8,(-10,-20,0)),(45,(-10,-20,0))],'catmullrom')
# 다리
dog_gait(dog_,13.0,15.0,amp=30,period=0.45)
dog_gait(dog_,26.0,27.2,amp=30,period=0.4)
dog_gait(dog_,27.2,36.9,amp=45,period=0.36,run=True)
for a,b in ((10.6,11.0),(11.0,13.0),(13.0,15.0),(15.01,17.0),(38.4,40.0),(41.0,45.0)): wag(dog_,a,b)
show(MB,[(26.15,38.0)])

# ---------------- 밥그릇 (땅) ----------------
def ground_bowl(tag):
    b=bowl(M,tag,1.0,food=False); f=M.group(tag+'food',[0,1.7,0],[M.cube('food',[-2.6,1,-2.6],[2.6,2.4,2.6],'food')])
    b['children'].append(f); top.append(b); return b,f
GB,GF=ground_bowl('gb_')
P(GB,[(0,(DX,0,DZ-18)),(45,(DX,0,DZ-18))])
show(GB,[(10.55,26.15)]); show(GF,[(10.55,17.0)])
GB2,GF2=ground_bowl('gb2_'); show(GF2,[]); show(GB2,[(38.0,45)])
P(GB2,[(0,(405,0,4)),(45,(405,0,4))])

# ---------------- 꼬마 ----------------
kid=person(M,'kd_','kid',0.7); top.append(kid)
KR=part(kid,'arm_right'); KL=part(kid,'arm_left'); KH=part(kid,'head'); KBODY=part(kid,'body')
kb=M.group('kb_root',[-3*0.7,6.3,-2],bowl_cubes(M,-3*0.7,4.6,-2,0.7,food=True)); KR['children'].append(kb)
show(kb,[(8.9,10.55)])
R(kb,[(0,(0,0,0)),(8.9,(70,0,0)),(10.55,(70,0,0))])
kp=[(0,140,8),(5.0,140,8),(5.1,70,8),(7.0,-38,8),            # 걸어 들어와 멈춤
    (7.5,-38,8),(8.6,-4,62),(8.9,-4,64),(10.0,-50,6),(10.55,-50,6),(10.99,-50,6),   # 집에 갔다 그릇 들고 옴
    (11.0,-50,4),(12.99,-50,4),                          # (a) 아침
    (13.0,30,20),(15.0,-18,20),                          # (b) 걷기, 강아지가 뒤따름
    (15.01,0,77),(16.99,0,77),                           # (c) 저녁 계단에 앉음
    (17.0,-36,14),(20.4,-36,14),(22.2,30,-2),(22.6,30,-2)]
P(kid,[(t,(x,0,z)) for t,x,z in kp])
P(kid,[(15.01,(0,5-8.4,77)),(16.99,(0,5-8.4,77)),(17.0,(-36,0,14))])
# 트럭에서 내린 뒤 (36.1~)
P(kid,[(36.09,(30,0,-2)),(36.1,(460,0,-8)),(37.2,(415,0,4)),(45,(415,0,4))])
kyaw=[(0,-90),(7.0,-90),(7.3,-160),(7.5,-218+0),(8.6,-218),(8.9,-180),(9.0,-322),(10.0,-322),(10.2,-180),(10.99,-180),
      (11.0,180),(12.99,180),(13.0,-90),(15.0,-90),(15.01,0),(16.99,0),
      (17.0,180),(18.0,180),(18.4,90),(19.4,90),(19.8,180),(20.4,90),(22.2,90),(22.6,180),
      (36.1,-90),(45,-90)]
yaw(kid,kyaw)
walk(kid,5.1,7.0,amp=28,period=0.6)
walk(kid,7.5,8.6,amp=40,period=0.4)
walk(kid,9.0,10.0,amp=40,period=0.4,arms=False)
walk(kid,13.0,15.0,amp=26,period=0.6)
walk(kid,20.4,22.2,amp=26,period=0.6,arms=False)
walk(kid,36.1,37.2,amp=40,period=0.4)
# 팔: 그릇 들기(8.9~10.55) / 쓰다듬기(15~17) / 아빠 손 잡기(20.4~22.2, 왼팔) / 안기(40~)
for arm in (KR,KL):
    R(arm,[(8.7,(0,0,0)),(8.9,(-70,0,0)),(10.2,(-70,0,0)),(10.55,(-35,0,0)),(10.8,(0,0,0))])
R(KR,[(15.01,(-45,0,-15)),(15.6,(-60,0,-15)),(16.2,(-45,0,-15)),(16.8,(-60,0,-15)),(16.99,(-45,0,-15)),(17.0,(0,0,0))],'catmullrom')
R(KR,[(20.4,(0,0,0)),(20.6,(-20,0,-25)),(22.2,(-20,0,-25)),(22.4,(0,0,0))])   # 꼬마 -z 쪽 팔 → 아빠
for arm in (KR,KL): R(arm,[(37.2,(0,0,0)),(38.6,(0,0,0)),(39.2,(-40,0,0)),(40.0,(-55,0,0)),(40.8,(-75,0,0)),(45,(-75,0,0))])
# 다리: 앉기
for lg in (part(kid,'leg_left'),part(kid,'leg_right')): R(lg,[(15.0,(0,0,0)),(15.01,(-90,0,0)),(16.99,(-90,0,0)),(17.0,(0,0,0))])
# 몸: 그릇 놓을 때 숙임
R(KBODY,[(10.0,(0,0,0)),(10.3,(25,0,0)),(10.6,(25,0,0)),(10.9,(0,0,0)),(40.0,(0,0,0)),(40.6,(10,0,0)),(41.4,(0,0,0))])
# 머리: 강아지 보기·뒤돌아보기
R(KH,[(0,(0,0,0)),(7.0,(0,0,0)),(7.2,(10,0,0)),(7.5,(0,0,0)),(10.6,(15,0,0)),(10.99,(15,0,0)),(11.0,(20,0,0)),(12.99,(20,0,0)),
      (13.0,(0,0,0)),(13.8,(0,0,0)),(14.1,(0,60,0)),(14.6,(0,60,0)),(14.9,(0,0,0)),(15.01,(15,30,0)),(16.99,(15,30,0)),
      (17.0,(0,0,0)),(18.4,(0,-70,0)),(19.4,(0,-70,0)),(19.8,(0,0,0)),(20.4,(0,-60,0)),(21.0,(0,-30,0)),(21.4,(0,-80,0)),(22.2,(0,-80,0)),(22.6,(0,0,0)),
      (37.2,(0,0,0)),(37.8,(25,0,0)),(39.6,(25,0,0)),(40.8,(10,0,0)),(45,(10,0,0))],'catmullrom')
show(kid,[(0,22.6),(36.1,45)])

# ---------------- 아빠 ----------------
dad=person(M,'dd_','dad',1.0); top.append(dad)
DR=part(dad,'arm_right'); DL=part(dad,'arm_left'); DHd=part(dad,'head')
cb=M.group('cb_root',[0,26,-8],[M.cube('box',[-6,20,-14],[6,30,-3],'box',up='box_t')]); part(dad,'body')['children'].append(cb)
show(cb,[(17.0,19.4)])
pp=[(17.0,0,72),(17.6,0,60),(19.2,10,-6),(19.6,10,-6),(20.4,-26,6),(22.2,22,-9),(22.6,22,-9)]
P(dad,[(t,(x,0,z)) for t,x,z in pp])
yaw(dad,[(17.0,0),(17.6,0),(17.7,10),(19.2,10),(19.6,-119),(20.4,-119),(20.6,90),(22.2,90)])
walk(dad,17.0,19.2,amp=22,period=0.7,arms=False)
walk(dad,19.6,20.4,amp=22,period=0.7)
walk(dad,20.4,22.2,amp=22,period=0.7,arms=False)
for arm in (DR,DL): R(arm,[(17.0,(-60,0,0)),(19.2,(-60,0,0)),(19.5,(0,0,0))])
R(DL,[(20.4,(0,0,0)),(20.6,(-20,0,25)),(22.2,(-20,0,25)),(22.4,(0,0,0))])   # 아빠 +z 쪽 팔 → 꼬마
# 내려서 지켜보기 (39~)
P(dad,[(38.99,(22,0,-9)),(39.0,(446,0,-4)),(45,(446,0,-4))]); yaw(dad,[(39.0,-90),(45,-90)])
R(DHd,[(39.0,(0,0,0)),(41.4,(0,0,0)),(41.8,(18,0,0)),(42.2,(0,0,0)),(42.6,(18,0,0)),(43.0,(4,0,0)),(45,(4,0,0))],'catmullrom')
show(dad,[(17.0,22.6),(39.0,45)])

# ---------------- 트럭 (안에 꼬마·아빠) ----------------
tr=truck(M,'tr_')
k2=person(M,'k2_','kid',0.7); move(M,k2,6,6,-23); d2=person(M,'d2_','dad',1.0); move(M,d2,-6,-3,-24)
tr['children']+= [k2,d2]; top.append(tr)
TX=10; TZ=-30
tp=[(0,TX),(23.0,TX),(24.0,16),(25.0,34),(26.0,66),(30.0,226),(34.0,386),(35.0,426),(35.6,440),(45,440)]
P(tr,[(t,(x,0,TZ)) for t,x in tp],'catmullrom')
yaw(tr,[(0,90),(45,90)])
show(tr,[(17.0,45)])
show(k2,[(22.6,36.1)]); show(d2,[(22.6,39.0)])
door=part(tr,'door_l')
R(door,[(22.0,(0,0,0)),(22.3,(0,70,0)),(22.8,(0,70,0)),(23.0,(0,0,0)),(35.8,(0,0,0)),(36.1,(0,70,0)),(36.6,(0,70,0)),(36.9,(0,0,0))])
K2H=part(k2,'head'); K2R=part(k2,'arm_right'); D2H=part(d2,'head')
R(K2H,[(29.9,(0,0,0)),(30.4,(0,0,0)),(31.2,(0,110,0)),(33.4,(0,110,0)),(33.8,(0,-40,0)),(36.1,(0,-40,0))],'catmullrom')
R(K2R,[(33.6,(0,0,0)),(34.0,(-50,0,-30)),(36.1,(-50,0,-30))])
R(D2H,[(34.0,(0,0,0)),(34.5,(0,45,0)),(36.0,(0,45,0))])

A.bake(top)
M.save(f'{OUT}/A_동네.bbmodel',top,[A.json()],name='A')
json.dump({'A':{'ropes':[]}},open(f'{OUT}/세트정보.json','w',encoding='utf-8'))
print('ok', len(M.els),'cubes')
