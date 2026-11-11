"""《돌아온 새》 장면 모형 + 움직임 (세트 A 하나, 0~45초) → 연재/돌아온새/장면/A_바닷가.bbmodel, 세트정보.json
   좌표는 실제 세계 좌표, 위치 움직임은 x 를 뒤집어 넣음.  yaw: 0 = -z(바다 쪽), +90 = +x, -90 = -x, 180 = +z
   배치: 바다 z < -70, 모래 -70..-20, 풀밭 언덕 -20~ , 오두막 (-30,0,40), 등대 (70,0,70), 벤치 (20,0,-5)"""
import sys, os, json, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 새인물 import *
OUT=sys.argv[1] if len(sys.argv)>1 else '/home/user/youtubeshot/연재/돌아온새/장면'
os.makedirs(OUT,exist_ok=True)
L=45.0; random.seed(7)
M=Model(256); palette(M)
M.swatch('sea',lambda x,y:(55,125,190) if (x+2*y)%7 else (95,160,215),6); M.swatch('sand',(226,206,160),8)
M.swatch('grass',(110,168,82),10); M.swatch('grass_d',(96,152,72),10); M.swatch('rock',(120,118,115),12); M.swatch('rock_d',(92,90,88),10)
M.swatch('snow',(246,248,252),3); M.swatch('path',(200,180,140),8)
M.swatch('fl_r',(230,70,80),6); M.swatch('fl_y',(250,215,70),6); M.swatch('fl_p',(240,150,200),6); M.swatch('stem',(70,140,60),6)
M.swatch('pine',(55,115,70),10); M.swatch('bench',(150,100,60),6)
A=Anim(L); top=[]
C=lambda n,fr,to,col,**f: M.cube(n,fr,to,col,**f)

# ---------------- 도우미 ----------------
def P(g, pts, interp='linear'): A.add(g,'position',[(t,(-v[0],v[1],v[2])) for t,v in pts],interp)
def R(g, pts, interp='linear'): A.add(g,'rotation',pts,interp)
def show(g, spans, eps=0.02):
    pts=[(0,0)]
    for a,b in spans: pts+= [(max(0,a-eps),0),(a,1),(b,1),(b+eps,0)]
    A.add(g,'scale',[(t,(v,v,v)) for t,v in pts])
def yaw(g, pts, interp='linear'): R(g,[(t,(0,y,0)) for t,y in pts],interp)
def part(g, name): return find(g, g['name'].replace('root',name))
def face_dir(dx,dz): return math.degrees(math.atan2(dx,-dz))
def walk(p, t0, t1, amp=22, period=0.7, arms=True):
    legL,legR,armL,armR=[part(p,n) for n in ('leg_left','leg_right','arm_left','arm_right')]
    t=t0; s=1; pts=[]
    while t<t1-1e-6: pts.append((t+period/4,s)); t+=period/2; s=-s
    for g,sg in [(legL,1),(legR,-1)]+([(armL,-1),(armR,1)] if arms else []):
        R(g,[(t0,(0,0,0))]+[(tt,(sg*ss*amp,0,0)) for tt,ss in pts if tt<t1]+[(t1,(0,0,0))],'catmullrom')
def flap(b, t0, t1, period=0.24, up=110, down=35):
    """날갯짓: wing_l(+x) z +, wing_r(-x) z -"""
    wl,wr=part(b,'wing_l'),part(b,'wing_r'); t=t0; s=1; pl=[(t0-0.01,(0,0,0))]; pr=[(t0-0.01,(0,0,0))]
    while t<t1-1e-6:
        a=up if s>0 else down; pl.append((t,(0,0,a))); pr.append((t,(0,0,-a))); t+=period/2; s=-s
    pl.append((t1,(0,0,0))); pr.append((t1,(0,0,0)))
    R(wl,pl,'catmullrom'); R(wr,pr,'catmullrom')
def peck(b, t0, t1, period=0.4):
    h=part(b,'head'); pts=[(t0,(0,0,0))]; t=t0+period/2; s=1
    while t<t1: pts.append((t,(35 if s>0 else 0,0,0))); t+=period/2; s=-s
    R(h,pts+[(t1,(0,0,0))])
def fly_path(b, pts, flap_t=None):
    """[(t,x,y,z)] 위치 + 진행 방향으로 몸 돌리기"""
    P(b,[(t,(x,y,z)) for t,x,y,z in pts],'catmullrom')
    ys=[]
    for i,(t,x,y,z) in enumerate(pts):
        j=min(i+1,len(pts)-1); k=max(i-1,0); dx=pts[j][1]-pts[k][1]; dz=pts[j][3]-pts[k][3]
        if abs(dx)+abs(dz)>1e-6: ys.append((t,face_dir(dx,dz)))
    # 각도가 한 바퀴 넘어가며 튀지 않게 이어 붙임
    out=[]; prev=None
    for t,a in ys:
        if prev is not None:
            while a-prev>180: a-=360
            while a-prev<-180: a+=360
        out.append((t,a)); prev=a
    yaw(b,out,'catmullrom')

# ---------------- 장소 ----------------
W=[C('sea',[-3000,-14,-3000],[3000,-4,-70],'sea'), C('far_land',[-3000,-14,-70],[3000,-0.4,3000],'grass')]
for x in range(-300,300,60):
    W.append(C('sand',[x,-3,-72],[x+60,-0.2,-20],'sand'))
    for z in range(-20,300,60): W.append(C('grass',[x,-3,z],[x+60,0,z+60],'grass' if ((x+z)//60)%2 else 'grass_d'))
# 오두막까지 흙길
for z in range(-20,40,8): W.append(C('path',[-36,-2.9,z+0.05],[-24,0.15,z+8],'path'))
# 바위
ROCKS=[(-20,-40,10,6,8),(-34,-48,14,9,10),(-6,-52,8,5,7),(40,-46,12,7,9),(60,-56,16,10,10)]
for i,(x,z,w,h,d) in enumerate(ROCKS):
    W+= [C('rock',[x-w/2,-1,z-d/2],[x+w/2,h,z+d/2],'rock' if i%2 else 'rock_d')]
# 소나무
def pine(n,x,z,h=40):
    k=[C(n+'_t',[x-2,0,z-2],[x+2,h*0.3,z+2],'wood_d')]
    for i,w in enumerate((16,12,8,4)): k.append(C(n+'_l',[x-w/2,h*0.3+i*h*0.17,z-w/2],[x+w/2,h*0.3+(i+1)*h*0.17,z+w/2],'pine'))
    return k
PINES=[(-90,60),(-110,110),(-70,140),(120,30),(140,90),(100,150),(-140,20),(160,-5)]
for i,(x,z) in enumerate(PINES): W+= pine(f'pn{i}',x,z,38+(i%3)*8)
# 벤치 (바다를 봄)
BX,BZ=20,-5
W+= [C('bench_seat',[BX-12,5,BZ-3],[BX+12,6,BZ+3],'bench'), C('bench_back',[BX-12,6,BZ+2],[BX+12,12,BZ+3],'bench'),
     C('bench_l',[BX-11,0,BZ-3],[BX-9,5,BZ+3],'wood_d'), C('bench_r',[BX+9,0,BZ-3],[BX+11,5,BZ+3],'wood_d')]
top.append(M.group('world',[0,0,0],W))
ct=cottage(M,'ct_'); move(M,ct,-30,0,40); top.append(ct)
lh=lighthouse(M,'lh_'); move(M,lh,70,0,70); top.append(lh)
NBX,NBY,NBZ=-16,12,26   # 마당의 나무 기둥 위 둥지 상자 (앞이 바다 쪽 -z)
nb=nest_box(M,'nb_'); move(M,nb,NBX,NBY,NBZ); top.append(nb)
top.append(M.group('nb_post',[0,0,0],[C('post',[NBX-1.5,0,NBZ-1.5],[NBX+1.5,NBY,NBZ+1.5],'wood_d')]))

# 겨울 눈 (23~31초만 보임) / 봄 꽃 (31초~)
S=[]
for x in range(-300,300,60):
    for z in range(-20,300,60): S.append(C('snow_g',[x,0,z],[x+60,0.5,z+60],'snow'))
    S.append(C('snow_s',[x,-0.2,-72],[x+60,0.3,-20],'snow'))
for i in range(4):   # 오두막 지붕 층마다 위에 눈
    S.append(C('snow_roof',[-30-28+i*5-0.3,26+(i+1)*5,37-0.3],[-30+28-i*5+0.3,26+(i+1)*5+1.2,79+0.3],'snow'))
S+= [C('snow_bench',[BX-12,6,BZ-3],[BX+12,7,BZ+1.9],'snow'), C('snow_nb',[NBX-7,NBY+7,NBZ-5],[NBX+7,NBY+8,NBZ+5],'snow'),
     C('snow_lhbal',[57,112,57],[83,113,83],'snow'), C('snow_lhroof',[60,127,60],[80,128,80],'snow')]
for i,(x,z) in enumerate(PINES): S+= [C('snow_p',[x-6.3,30,z-6.3],[x+6.3,33,z+6.3],'snow'), C('snow_p2',[x-3,48,z-3],[x+3,50,z+3],'snow')]
for x,z,w,h,d in ROCKS: S.append(C('snow_r',[x-w/2,h,z-d/2],[x+w/2,h+0.8,z+d/2],'snow'))
S.append(C('snow_far',[-3000,-0.3,-70],[3000,0.1,3000],'snow'))   # 먼 땅까지 눈
SNOW=M.group('snow',[0,0,0],S); top.append(SNOW); show(SNOW,[(23.0,31.0)])
F=[]
for i in range(140):
    x=random.uniform(-80,110); z=random.uniform(-18,120)
    if -60<x<0 and 34<z<80: continue
    if -40<x<-20 and -20<z<40: continue
    col=random.choice(['fl_r','fl_y','fl_p','fl_y'])
    F+= [C('stem',[x-0.3,0,z-0.3],[x+0.3,2.2,z+0.3],'stem'), C('flower',[x-1,2.2,z-1],[x+1,3.6,z+1],col)]
FLOW=M.group('flowers',[0,0,0],F); top.append(FLOW); show(FLOW,[(31.0,45.0)])

# ---------------- 할머니 ----------------
gm=grandma(M,'gm_'); top.append(gm)
GB=part(gm,'body'); GH=part(gm,'head'); GAR=part(gm,'arm_right'); GAL=part(gm,'arm_left')
# 손 위의 새 (오른팔에 붙음, 팔을 든 만큼 반대로 돌려 똑바로 서게) — 붕대는 18초에 풂
hb=bird(M,'hb_',1.0); move(M,hb,-5.9,11.2,-1.6); GAR['children'].append(hb)
show(hb,[(4.3,4.97),(17.0,19.17),(39.45,45)]); show(part(hb,'bandage'),[(0,17.9)])
# 어깨 위의 새 (11~13초) · 어깨 위 새끼 새 (41.2~)
sb=bird(M,'sb_',1.0); move(M,sb,6.2,22.2,0.3); GB['children'].append(sb); show(sb,[(11.0,13.0)])
sc=bird(M,'sc_',0.6,chick=True,bandage=False); move(M,sc,-6.2,22.2,0.3); GB['children'].append(sc)

gp=[(0,14,0,-8),(2.4,-12,0,-30),(4.9,-12,0,-30),            # 바위 쪽으로 걸어가 새를 들어 올림
    (5.0,-16,0,36),(10.99,-16,0,36),                            # 둥지 뒤에서 손바닥 내밀기
    (11.0,-30,0,12),(13.0,-30,0,-4),                           # (a) 아침: 어깨에 새를 얹고 흙길을 걸어 내려옴
    (13.01,-6,0,6),(14.99,-6,0,6),                              # (b) 낮: 새 날갯짓 연습 지켜보기
    (15.0,20-4,6-10,BZ-0.5),(16.99,20-4,6-10,BZ-0.5),           # (c) 저녁: 벤치에 앉음
    (17.0,0,0,-24),(22.99,0,0,-24),                             # 바닷가 끝에서 날려 보냄
    (23.0,-16,0,36),(30.99,-16,0,36),                           # 겨울: 빈 둥지 뒤
    (31.0,-16,0,36),(34.0,-16,0,36),(35.0,-2,0,34),(36.6,-6,0,6),(45,-6,0,6)]  # 봄: 둥지 치우려다 멈춤 → 나와서 하늘을 봄
P(gm,[(t,(x,y,z)) for t,x,y,z in gp])
yaw(gm,[(0,face_dir(-26,-22)),(2.4,face_dir(-26,-22)),(4.9,face_dir(-26,-22)),(5.0,0),(10.99,0),
        (11.0,0),(13.0,0),(13.01,-20),(14.99,-20),(15.0,0),(16.99,0),(17.0,0),(22.99,0),
        (23.0,0),(30.99,0),(31.0,0),(34.0,0),(34.3,90),(35.0,90),(35.3,10),(36.6,10),(37.2,0),(45,0)])
walk(gm,0.1,2.4); walk(gm,11.0,13.0,arms=False); walk(gm,34.0,36.6)
# 앉기 (15~17)
for lg in (part(gm,'leg_left'),part(gm,'leg_right')): R(lg,[(14.99,(0,0,0)),(15.0,(-90,0,0)),(16.99,(-90,0,0)),(17.0,(0,0,0))])
# 몸 숙이기: 새 들어 올릴 때
R(GB,[(2.4,(0,0,0)),(3.2,(35,0,0)),(4.3,(35,0,0)),(4.9,(10,0,0)),(4.99,(0,0,0))])
# 팔: 들어 올리기(2.4~5) / 손바닥 내밀기(5~11) / 손뼉(13~15) / 새를 들고 위로(17~19.2) / 손 흔들기(19.2~23) / 둥지에 손 뻗기(31~34) / 손 내밀기(37.5~)
R(GAR,[(2.4,(0,0,0)),(3.4,(-50,0,0)),(4.3,(-50,0,0)),(4.9,(-60,0,0)),(4.99,(-60,0,0)),
       (5.0,(-45,0,0)),(10.99,(-45,0,0)),(11.0,(0,0,0)),
       (13.01,(-45,0,-15)),(13.3,(-45,0,15)),(13.6,(-45,0,-15)),(13.9,(-45,0,15)),(14.2,(-45,0,-15)),(14.5,(-45,0,15)),(14.99,(-45,0,0)),(15.0,(0,0,0)),
       (17.0,(-60,0,0)),(18.0,(-60,0,0)),(18.8,(-160,0,0)),(19.2,(-160,0,0)),(19.5,(-150,0,-20)),
       (20.0,(-150,0,-40)),(20.4,(-150,0,-10)),(20.8,(-150,0,-40)),(21.2,(-150,0,-10)),(21.6,(-150,0,-40)),(22.0,(-150,0,-10)),(22.6,(-60,0,0)),(22.99,(0,0,0)),
       (31.0,(0,0,0)),(32.0,(-55,0,0)),(33.6,(-55,0,0)),(34.0,(-10,0,0)),(34.3,(0,0,0)),
       (37.4,(0,0,0)),(38.4,(-80,0,0)),(45,(-80,0,0))])
R(hb,[(4.3,(50,0,0)),(4.9,(60,0,0)),(17.0,(60,0,0)),(18.0,(60,0,0)),(18.8,(160,0,0)),(19.2,(160,0,0)),(37.4,(0,0,0)),(38.4,(80,0,0)),(45,(80,0,0))])
R(GAL,[(2.4,(0,0,0)),(3.4,(-50,0,0)),(4.9,(-50,0,0)),(4.99,(0,0,0)),
       (13.01,(-45,0,15)),(13.3,(-45,0,-15)),(13.6,(-45,0,15)),(13.9,(-45,0,-15)),(14.2,(-45,0,15)),(14.5,(-45,0,-15)),(14.99,(-45,0,0)),(15.0,(0,0,0)),
       (15.01,(-30,0,-20)),(16.99,(-30,0,-20)),(17.0,(-60,0,0)),(18.0,(-60,0,0)),(18.8,(-160,0,0)),(19.2,(-160,0,0)),(19.6,(0,0,0))])
# 머리: 새 보기·하늘 보기·끄덕
R(GH,[(0,(0,0,0)),(2.4,(15,0,0)),(4.9,(25,0,0)),(5.0,(15,0,0)),(10.99,(15,0,0)),(11.0,(0,0,0)),(11.6,(0,40,0)),(12.6,(0,40,0)),(13.0,(0,0,0)),
      (13.01,(15,0,0)),(14.99,(15,0,0)),(15.0,(0,0,0)),(15.6,(0,-30,0)),(16.99,(0,-30,0)),(17.0,(0,0,0)),
      (18.6,(-30,0,0)),(20.0,(-35,15,0)),(21.0,(-35,-15,0)),(22.0,(-25,0,0)),(22.99,(-20,0,0)),
      (23.0,(-15,0,0)),(25.0,(-30,0,0)),(28.0,(-30,0,0)),(29.5,(10,0,0)),(30.99,(10,0,0)),
      (31.0,(0,0,0)),(33.6,(0,0,0)),(34.0,(-25,0,0)),(36.6,(-35,0,0)),(38.0,(-35,0,0)),(39.5,(10,0,0)),(41.0,(5,-25,0)),(42.0,(15,0,0)),(42.6,(5,0,0)),(43.2,(15,0,0)),(45,(8,0,0))],'catmullrom')

# ---------------- 파랑새 (자유롭게 움직이는 새) ----------------
bd=bird(M,'bd_',1.0); top.append(bd); BAND=part(bd,'bandage'); BH=part(bd,'head')
show(BAND,[(0,17.9)])
RX,RY,RZ=-20,6,-40     # 바위 위
bp=[(0,RX,RY,RZ),(4.29,RX,RY,RZ),
    (5.0,NBX+2,NBY+1,NBZ-1),(10.99,NBX+2,NBY+1,NBZ-1),            # 둥지 상자 안 (짚 위)
    (13.01,-6,0,-8),(14.99,-6,0,-8),                               # 풀밭에서 날갯짓 연습
    (15.0,20+6,6,BZ-1),(16.99,20+6,6,BZ-1)]                        # 벤치 위
P(bd,[(t,(x,y,z)) for t,x,y,z in bp])
# 연습: 뛰어오름
P(bd,[(13.2,(-6,0,-8)),(13.6,(-6,5,-8)),(14.0,(-6,0,-8)),(14.3,(-6,7,-8)),(14.7,(-6,0,-8))],'catmullrom')
yaw(bd,[(0,30),(4.29,30),(5.0,0),(10.99,0),(13.01,0),(14.99,0),(15.0,0),(16.99,0)])
R(part(bd,'wing_l'),[(0,(0,0,25)),(4.29,(0,0,25)),(4.3,(0,0,0))])     # 다친 날개가 처짐
peck(bd,6.0,10.8)
flap(bd,13.1,14.9,period=0.2)
# 날아감 (19.2~23): 할머니 머리 위 → 한 바퀴 → 바다로
fp=[(19.2,0,34,-28)]
for i in range(1,9):
    a=math.radians(i*45); fp.append((19.2+i*0.22,0+14*math.sin(a),36+i*1.2,-24-14*math.cos(a)))
fp+= [(21.4,4,50,-50),(22.2,0,62,-100),(23.0,-6,74,-160)]
fly_path(bd,fp); flap(bd,19.2,23.0)
# 돌아옴 (37~39.45): 바다 위 → 할머니 손
fr=[(36.9,30,70,-170),(37.6,20,56,-110),(38.4,8,38,-50),(39.0,-2,26,-18),(39.44,-11.9,20.5,-4.5)]
fly_path(bd,fr); flap(bd,36.9,39.3)
show(bd,[(0,4.3),(5.0,10.97),(13.01,16.97),(19.2,23.0),(36.9,39.45)])   # 손·어깨 위에 있을 땐 숨김 (두 마리로 보이지 않게)
R(BH,[(0,(20,0,0)),(4.29,(20,0,0)),(4.3,(0,0,0))])

# ---------------- 새끼 새 3마리 (39.2~) ----------------
CH=[]
# 할머니 몸에 붙는 새끼 새 자리 (머리 위·왼쪽 어깨·오른쪽 어깨) — 화면에 잘 보이게 (2026-11-11 검수: 둥지·엄마 새 뒤에 가려 안 보였음)
GHd=part(gm,'head')
sc2=bird(M,'sc2_',0.6,chick=True,bandage=False); move(M,sc2,6.2,22.2,0.3); GB['children'].append(sc2)
sc3=bird(M,'sc3_',0.6,chick=True,bandage=False); move(M,sc3,0,30.3,0.5); GHd['children'].append(sc3)
GX,GZ=-6,6     # 이때 할머니 자리
dests=[(38.6,(GX,30.3,GZ+0.5),sc3),(39.0,(GX+6.2,22.2,GZ+0.3),sc2),(39.4,(GX-6.2,22.2,GZ+0.3),sc)]
for i,(t0,(x,y,z),seat) in enumerate(dests):
    c=bird(M,f'ch{i}_',0.6,chick=True,bandage=False); top.append(c); CH.append(c)
    pts=[(t0,30+i*10,70+i*4,-170),(t0+0.8,18+i*4,48,-100),(t0+1.4,x+5,y+10,z-28),(t0+2.0,x,y,z)]
    fly_path(c,pts); flap(c,t0,t0+2.0,period=0.18)
    end=t0+2.0
    show(c,[(t0,end+0.03)]); show(seat,[(end+0.02,45)])
    R(part(seat,'head'),[(end+0.3,(0,0,0)),(end+0.9,(0,35,0)),(end+1.6,(0,-25,0)),(end+2.4,(0,0,0)),(45,(0,0,0))])
# 손 위 새: 끝에 고개 갸웃
R(part(hb,'head'),[(39.5,(0,0,0)),(40.4,(0,0,15)),(41.4,(0,25,0)),(42.4,(0,0,-10)),(45,(0,0,0))])

A.bake(top)
M.save(f'{OUT}/A_바닷가.bbmodel',top,[A.json()],name='A')
json.dump({'A':{'ropes':[]}},open(f'{OUT}/세트정보.json','w',encoding='utf-8'))
print('ok',len(M.els),'cubes')
