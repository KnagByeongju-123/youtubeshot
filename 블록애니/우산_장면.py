"""《할아버지의 우산》 장면 모형 + 움직임 (세트 A, 0~45초) → 연재/할아버지의우산/장면/A_정류장.bbmodel, 세트정보.json
   실제 세계 좌표, 위치 움직임은 x 를 뒤집어 넣음.  yaw: 0 = -z(차도 쪽), +90 = +x, -90 = -x
   배치: 차도 z -60..0 (x 방향), 인도 z 0..40, 정류장 표지판 (0,0,6), 할아버지 집 (-80, 문 z 80)
   처음(0~17)과 끝(22~45)은 같은 자리: 우산 든 사람 (-12,12), 기다리는 사람 (-4~-6,10)"""
import sys, os, json, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 우산인물 import *
OUT=sys.argv[1] if len(sys.argv)>1 else '/home/user/youtubeshot/연재/할아버지의우산/장면'
os.makedirs(OUT,exist_ok=True)
L=45.0
M=Model(256); palette(M)
M.swatch('asphalt',(78,80,86),6); M.swatch('lane',(240,205,70),4); M.swatch('walk',(196,192,184),6); M.swatch('curb',(160,158,152),4)
M.swatch('grass',(108,165,80),10); M.swatch('grass_d',(95,150,70),10)
for n,cc in [('wall1',(235,225,205)),('wall2',(205,225,235)),('wall3',(240,205,190)),('wall4',(220,232,200))]: M.swatch(n,cc,5)
M.swatch('roof1',(170,70,55),6); M.swatch('roof2',(70,95,130),6); M.swatch('roof3',(95,120,80),6)
M.swatch('win',(150,195,225),3); M.swatch('frame',(250,250,250),2); M.swatch('door',(130,85,50),5); M.swatch('step',(175,170,165),6)
M.swatch('trunk',(115,85,55),5); M.swatch('leaf',(80,150,70),14); M.swatch('leaf2',(105,170,80),14)
M.swatch('lf_spring',(245,180,200),10); M.swatch('lf_summer',(60,140,60),12); M.swatch('lf_autumn',(225,130,50),14); M.swatch('snow',(246,248,252),3)
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
def walk(p, t0, t1, amp=24, period=0.7, arms=(True,True)):
    legL,legR,armL,armR=[part(p,n) for n in ('leg_left','leg_right','arm_left','arm_right')]
    t=t0; s=1; pts=[]
    while t<t1-1e-6: pts.append((t+period/4,s)); t+=period/2; s=-s
    gs=[(legL,1),(legR,-1)]+([(armL,-1)] if arms[0] else [])+([(armR,1)] if arms[1] else [])
    for g,sg in gs:
        R(g,[(t0,(0,0,0))]+[(tt,(sg*ss*amp,0,0)) for tt,ss in pts if tt<t1]+[(t1,(0,0,0))],'catmullrom')

# ---------------- 동네 ----------------
W=[C('far_ground',[-3000,-20,-3000],[3000,-0.4,3000],'grass')]
for x in range(-300,400,100):
    W+= [C('road',[x,-2,-60],[x+100,0,0],'asphalt'), C('walk',[x,-2,0],[x+100,0.4,40],'walk'), C('curb',[x,-2,-1.5],[x+100,0.8,-0.05],'curb'),
         C('walk2',[x,-2,-90],[x+100,0.4,-60],'walk'), C('yard',[x,-2,40],[x+100,0.2,80],'grass' if (x//100)%2 else 'grass_d')]
    for xx in range(x,x+100,40): W.append(C('lane',[xx,0,-31],[xx+20,0.15,-29],'lane'))
def house(n,x,z,w,d,h,wall,roof,front=-1):
    k=[C(n+'_wall',[x-w/2,0,z],[x+w/2,h,z+d],wall)]
    for i in range(4): k.append(C(n+'_roof',[x-w/2-3+i*w/8,h+i*7,z-3],[x+w/2+3-i*w/8,h+(i+1)*7,z+d+3],roof))
    fz=z if front<0 else z+d; s=-1 if front<0 else 1
    def face(a,b,y0,y1,col,off=0.0,dep=0.6):   # 벽에 붙는 판: 판마다 깊이를 다르게 (면 겹침 막기)
        z0,z1=fz+s*off,fz+s*(off+dep); return C(n+'_f',[a,y0,min(z0,z1)],[b,y1,max(z0,z1)],col)
    k+= [face(x-6,x+6,0,22,'door'), face(x+3,x+4.5,10,12,'tire',off=0.1,dep=0.9)]
    for wx in (x-w/2+8, x+w/2-22):
        k+= [face(wx-1,wx+15,13,29,'frame'), face(wx,wx+14,14,28,'win',off=0.1)]
    return k
HX,HZ=-80,80        # 할아버지 집 (문 앞이 세월 장면)
cols=['wall1','wall2','wall3','wall4']; roofs=['roof1','roof2','roof3']
for i,x in enumerate(range(-300,400,95)):
    if abs(x-HX)>80: W+= house(f'h{i}',x,85,70,46,34,cols[i%4],roofs[i%3])   # 할아버지 집과 겹치지 않게
    W+= house(f'g{i}',x+40,-160,64,44,32,cols[(i+2)%4],roofs[(i+1)%3],front=1)
W+= house('home',HX,HZ,76,48,36,'wall1','roof1') + [C('step',[HX-12,0,HZ-10],[HX+12,4,HZ-0.05],'step')]
def tree(n,x,z,h=40,leafcol='leaf'):
    return [C(n+'_t',[x-2.5,0,z-2.5],[x+2.5,h,z+2.5],'trunk'), C(n+'_l1',[x-12,h-6,z-12],[x+12,h+12,z+12],leafcol),
            C(n+'_l2',[x-8,h+12,z-8],[x+8,h+20,z+8],leafcol if leafcol!='leaf' else 'leaf2')]
for j,x in enumerate(range(-290,400,70)):
    if abs(x)<40 or abs(x-HX)<40: continue
    W+= tree(f'tr{j}',x,34,38+(j%3)*6)
    W+= tree(f'tq{j}',x+30,-75,36+(j%2)*8)
top.append(M.group('world',[0,0,0],W))
bs=bus_stop(M,'bs_'); move(M,bs,0,0,6); top.append(bs)
# 벤치는 따로 묶어 마지막에 걸어갈 때(38초~)는 숨김 — 옆에서 찍을 때 두 사람 다리를 가리지 않게 (장면이 바뀌는 순간이라 티 나지 않음)
byid={e['uuid']:e for e in M.els}
bench_ids=[c for c in bs['children'] if isinstance(c,str) and byid[c]['name'] in ('bs_seat','bs_back','bs_l1','bs_l2')]
bs['children']=[c for c in bs['children'] if c not in bench_ids]
bench=M.group('bs_bench',[15,0,6],bench_ids); top.append(bench); show(bench,[(0,37.99)])

# 세월 나무 (할아버지 집 옆): 봄·여름·가을·겨울 잎을 따로 두고 차례로 보이게 (17~22초)
TX,TZ=HX+30,HZ-14
top.append(M.group('ss_trunk',[0,0,0],[C('ss_t',[TX-2.5,0,TZ-2.5],[TX+2.5,40,TZ+2.5],'trunk')]))
SEASON=[('spring','lf_spring',17.0,18.25),('summer','lf_summer',18.25,19.5),('autumn','lf_autumn',19.5,20.75)]
for nm,col,a,b in SEASON:
    g=M.group('ss_'+nm,[TX,40,TZ],[C('l1',[TX-12,34,TZ-12],[TX+12,52,TZ+12],col),C('l2',[TX-8,52,TZ-8],[TX+8,60,TZ+8],col)])
    top.append(g); show(g,[(a,b)] if nm!='summer' else [(0,17.0),(b-1.25,b),(22.0,45)])
snow=M.group('ss_winter',[0,0,0],[C('w_branch',[TX-6,38,TZ-1],[TX+6,40,TZ+1],'trunk'), C('w_snow',[TX-6.2,40,TZ-1.2],[TX+6.2,41,TZ+1.2],'snow'),
      C('w_ground',[HX-40,0.25,HZ-40],[HX+50,0.7,HZ-0.1],'snow'), C('w_roof',[HX-13.5,62.95,HZ-3.3],[HX+13.5,64.3,HZ+51.3],'snow')])
top.append(snow); show(snow,[(20.75,22.0)])
# 접은 우산: 문 옆에 세워 둠 (17~22초)
cu=umbrella_closed(M,'cu_'); move(M,cu,HX+15,0.25,HZ-2.5); top.append(cu)
R(cu,[(0,(0,0,-12)),(45,(0,0,-12))]); show(cu,[(17.0,22.0)])

# ---------------- 처음: 할아버지 + 꼬마 손녀 (0~17) ----------------
gp=person(M,'gp_','grandpa'); top.append(gp)
GAL,GAR,GH=part(gp,'arm_left'),part(gp,'arm_right'),part(gp,'head')
# 우산: 왼팔(+x, 손녀 쪽)에. 팔을 앞으로 든 만큼 반대로 돌려 우산대를 곧게, 손녀 쪽(+x)으로 기울이기 = z 회전 -
ug=umbrella(M,'ug_'); move(M,ug,6.2,11.5,0); GAL['children'].append(ug)
gw=[(0,-90,0,14),(2.6,-12,0,12),(17,-12,0,12)]
P(gp,[(t,(x,y,z)) for t,x,y,z in gw]); yaw(gp,[(0,90),(2.6,90),(2.9,0),(16.9,0)])
walk(gp,0,2.6,arms=(False,True))
R(GAL,[(0,(-35,0,0)),(17,(-35,0,0))])
R(ug,[(0,(35,0,0)),(3.0,(35,0,0)),(3.7,(35,0,-20)),(14.3,(35,0,-20)),(15.0,(35,0,-4)),(17,(35,0,-4))])
show(part(gp,'wet_r'),[(6.0,17.0)]); show(part(gp,'wet_l'),[])
R(GH,[(0,(0,0,0)),(3.2,(0,0,0)),(3.8,(15,30,0)),(8.5,(15,30,0)),(9.2,(10,40,0)),(12.6,(0,0,0)),(13.2,(0,40,0)),(15.0,(0,70,0)),(17,(0,70,0))],'catmullrom')
R(GAR,[(15.2,(0,0,0)),(15.5,(0,0,-150)),(15.8,(0,0,-120)),(16.1,(0,0,-150)),(16.4,(0,0,-120)),(16.7,(0,0,-150)),(17,(0,0,-140))])   # 버스에 손 흔들기
show(gp,[(0,17.0)])

girl=person(M,'gl_','girl',0.68); top.append(girl)
GLH=part(girl,'head')
P(girl,[(0,(-4,0,10)),(12.8,(-4,0,10)),(14.0,(4,0,-3.5)),(14.3,(4,0,-4.5)),(17,(4,0,-4.5))])
yaw(girl,[(0,0),(12.8,0),(12.9,150),(14.3,180)])
walk(girl,12.8,14.0,amp=30,period=0.45)
R(GLH,[(0,(18,0,0)),(2.8,(18,0,0)),(3.4,(-20,-40,0)),(5.0,(-20,-40,0)),(7.0,(-15,-30,0)),(11.0,(-15,-30,0)),(11.6,(0,-60,0)),(12.8,(0,-60,0)),(13.0,(0,0,0))],'catmullrom')
show(part(girl,'wet_l'),[]); show(part(girl,'wet_r'),[])
show(girl,[(0,14.3)])
# 노란 버스 (11~17): -x 에서 와서 서고, 손녀를 태우고 +x 로 떠남. 문은 버스 +z 쪽 (앞에서 25)
bu=bus(M,'bu_')
g2=person(M,'g2_','girl',0.68); move(M,g2,8,8,-12); bu['children'].append(g2)   # 버스 안 손녀 (창가)
show(part(g2,'wet_l'),[]); show(part(g2,'wet_r'),[])
top.append(bu)
BZ=-18
P(bu,[(t,(x,0,BZ)) for t,x in [(0,-260),(11.0,-260),(12.6,-20),(15.2,-20),(16.0,0),(17.0,60),(45,60)]],'catmullrom')
yaw(bu,[(0,90),(45,90)])
show(bu,[(11.0,17.0)]); show(g2,[(14.3,17.0)])
R(part(g2,'arm_left'),[(14.4,(0,0,0)),(14.8,(0,0,150)),(15.1,(0,0,120)),(15.4,(0,0,150)),(15.7,(0,0,120)),(16.0,(0,0,150)),(16.3,(0,0,120)),(17,(0,0,150))])
R(part(g2,'head'),[(14.3,(0,0,0)),(14.6,(0,80,0)),(17,(0,80,0))])   # 창문 쪽(버스 +x 쪽)을 봄

# ---------------- 끝: 늙은 할아버지 + 어른 손녀 (22~45) ----------------
og=person(M,'og_','grandpa_old'); top.append(og)
OB,OH,OAR=part(og,'body'),part(og,'head'),part(og,'arm_right')
P(og,[(0,(-4,0,10)),(38.0,(-4,0,10)),(44.0,(30,0,12)),(45,(34,0,12))])
yaw(og,[(0,0),(37.6,0),(38.2,90),(45,90)])
R(OB,[(0,(22,0,0)),(45,(22,0,0))])     # 굽은 허리
R(OH,[(22.0,(10,0,0)),(23.0,(14,0,-4)),(24.0,(10,0,4)),(25.0,(14,0,-4)),(26.0,(10,0,0)),(29.2,(10,0,0)),
      (32.0,(10,0,0)),(32.8,(-25,-35,0)),(35.0,(-25,-40,0)),(35.6,(-10,-40,0)),(36.0,(-25,-40,0)),(36.6,(-10,-40,0)),(38.0,(-15,-30,0)),(45,(-15,-30,0))],'catmullrom')
R(OAR,[(0,(-22,0,0)),(45,(-22,0,0))])    # 지팡이 짚은 팔
walk(og,38.0,44.6,amp=14,period=1.0,arms=(False,False))
show(part(og,'wet_l'),[]); show(part(og,'wet_r'),[])
show(og,[(22.0,45)])

wm=person(M,'wm_','woman'); top.append(wm)
WAR,WAL,WH=part(wm,'arm_right'),part(wm,'arm_left'),part(wm,'head')
# 우산: 오른팔(-x, 바깥쪽)에 들고 할아버지 쪽(+x)으로 크게 기울임 → 손녀 오른쪽 어깨(-x)가 젖음
uw=umbrella(M,'uw_',old=True); move(M,uw,-6.2,11.5,0); WAR['children'].append(uw)
P(wm,[(0,(-90,0,14)),(27.0,(-90,0,14)),(29.0,(-14,0,12)),(38.0,(-14,0,12)),(44.0,(20,0,12)),(45,(24,0,12))])
yaw(wm,[(0,90),(29.0,90),(29.3,0),(37.6,0),(38.2,90),(45,90)])
walk(wm,27.0,29.0,amp=38,period=0.42,arms=(True,False))
walk(wm,38.0,44.6,amp=14,period=1.0,arms=(False,False))
R(WAR,[(0,(-35,0,0)),(45,(-35,0,0))])
R(uw,[(0,(35,0,0)),(29.2,(35,0,0)),(29.9,(35,0,-24)),(45,(35,0,-24))])
show(part(wm,'wet_r'),[(30.6,45)]); show(part(wm,'wet_l'),[])
R(WH,[(29.3,(0,0,0)),(30.0,(15,40,0)),(33.0,(15,40,0)),(33.6,(5,35,0)),(38.0,(5,35,0)),(38.4,(0,0,0)),(40.0,(0,40,0)),(41.5,(0,40,0)),(42.2,(0,0,0))],'catmullrom')
# 할아버지 등에 왼손을 얹음 (34.5~)
R(WAL,[(34.2,(0,0,0)),(35.0,(-40,0,35)),(45,(-40,0,35))])   # 왼팔(+x, 할아버지 쪽) 바깥으로 = z +
show(wm,[(27.0,45)])

A.bake(top)
M.save(f'{OUT}/A_정류장.bbmodel',top,[A.json()],name='A')
json.dump({'A':{'ropes':[]}},open(f'{OUT}/세트정보.json','w',encoding='utf-8'))
print('ok',len(M.els),'cubes')
