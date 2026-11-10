"""《13층 아래》 블록 장면 모형 + 샷 목록 + 자막(제목 등) + 효과음 시간표 → 연재/13층아래/장면/…
   대사·나레이션이 없어 시간은 모두 직접 정한 초(콘티.txt).  세트: A B13 실험실 / H 엘리베이터 통로 / B B10 레이저 / C B9 창고 / D B7 침수 / E B3 경비실 / F B1 환기구 / U 지상
   사용: python 탈출_장면.py [세트글자들 | all]"""
import sys, os, json, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 탈출_세트 import *
import 장면도구 as D
from 장면도구 import cam, two, orbit, sh, vis, grow, cyc, puff, flicker, actor, fall, caption
import 겹침면_검사
ROOT='/home/user/youtubeshot/연재/13층아래'; OUT=f'{ROOT}/장면'; os.makedirs(OUT,exist_ok=True)
L=420.0; D.init(L)
IN=['#0c0c10','#16161c']
CUES=[]
def cue(t,kind,vol=1.0): CUES.append({'t':round(t,2),'kind':kind,'vol':vol})
# 떨어져 나가는 때 (초)
LOST=dict(antenna=88.0, tank=121.5, arm_left=163.0, leg_left_armor=186.0, leg_right_armor=187.5, leg_right=192.5, headshell=228.0, shell=268.0, arm_right=305.5)
RIDE=[(40.0,248.0)]          # 핍이 모프 머리 위에 타고 있는 동안
PIPS=1.3

def newset():
    M=BigModel(1024); robot_palette(M); lab_palette(M); return M,Anim(L),[]
def save(M,A,top,name,key):
    D.finish_all(); A.bake([t for t in top if isinstance(t,dict)]); n=겹침면_검사.fix(M.els,top)
    M.save(f'{OUT}/{key}_{name}.bbmodel',top,[A.json()],name=key); print(key,name,len(M.els),'상자, 겹침 고침',n); return {}
def MOP(M,A,top,x,z,yaw=180,tag='m_',lost=LOST,ride=RIDE,patch=False,y=0):
    """모프 + (머리 위에 탄) 핍. 부품은 LOST 시간 뒤로 안 보임"""
    g=mop(M,tag,patch=patch); a=actor(M,A,top,g,tag,x,z,yaw,y=y)
    for part,t in (lost or {}).items(): vis(A,find(g,tag+part),[(0,t)])
    if ride:
        rp=pip(M,tag+'rp_',PIPS); move(M,rp,-1.2,30.2,0.5); find(g,tag+'head')['children'].append(rp); vis(A,rp,ride); a.rp=rp
        cyc(A,find(rp,tag+'rp_lamp'),'scale',ride[0][0],ride[-1][1],(1,1,1),(1.5,1.5,1.5),0.6,rest=(1,1,1))
    return a
def PIP(M,A,top,x,z,yaw=0,tag='p_',y=0): return actor(M,A,top,pip(M,tag,PIPS),tag,x,z,yaw,y=y)
def GUARD(M,A,top,x,z,yaw=0,tag='g_'): return actor(M,A,top,guard(M,tag),tag,x,z,yaw)
def part_model(M,kind,patch=False):
    """떨어져 나간 부품 하나 (원점 기준)"""
    c=M.cube; P=(lambda a,b:b) if patch else (lambda a,b:a)
    mk={'antenna':lambda:[c('pa',[-0.5,0,-0.5],[0.5,4.6,0.5],'joint'), c('pa',[-0.9,4.6,-0.9],[0.9,6.4,0.9],P('chest','pip_l'))],
       'tank':lambda:[c('pt',[-4,0,-2.1],[4,9.5,2.1],P('tank','p_or')), c('pt',[-2,9.5,-1.3],[2,10.9,1.3],P('tank_d','rust'))],
       'arm':lambda:[c('pm',[-1.8,7,-2.4],[1.8,10.2,2.4],P('teal','p_or')), c('pm',[-1,0,-1.3],[1,7.6,1.3],'frame'), c('pm',[-1.6,0,-2],[1.6,2.4,2],P('w','p_ye'))],
       'legarmor':lambda:[c('pl',[-2.6,0,-2.8],[2.6,6,2.8],P('w','p_gr'))],
       'leg':lambda:[c('pg',[-1.2,1.5,-1.4],[1.2,8,1.4],'frame'), c('pg',[-2,0,-3.4],[2,1.6,2.4],'frame_d')],
       'headshell':lambda:[c('ph',[-4.6,0,-3.4],[4.6,7.4,4.4],P('w','p_ye')), c('ph',[-4.9,5,-4.4],[4.9,7.7,-3.2],P('teal','p_rd'))],
       'shell':lambda:[c('ps',[-6,0,-4.4],[6,11.6,4.4],P('w','p_gr')), c('ps',[-6.3,2,-4.7],[6.3,3.6,4.7],P('teal','p_rd'))]}
    k=mk[kind]()          # 쓰는 부품만 만듦 (다 만들면 안 쓴 상자가 원점에 떠 있음)
    return M.group('part_'+kind+U()[:4],[0,5,0],k)
def run_pose(A,a,t0,t1):
    """달릴 때 몸을 앞으로 숙임"""
    A.add(a.part('body'),'rotation',[(max(0,t0-0.01),(0,0,0)),(t0+0.25,(14,0,0)),(max(t0+0.25,t1-0.25),(14,0,0)),(t1,(0,0,0))],'catmullrom')
def alarms(M,A,top,pts,t0,t1,y=88):
    for i,(x,z) in enumerate(pts):
        g=alarm_lamp(M,f'al{i}',x,y,z); top.append(g); vis(A,g,[(t0,t1)]); A.add(g,'rotation',[(t0,(0,0,0)),(t1,(0,360*(t1-t0)/1.1,0))])

# =====================================================================
#  A : B13 실험실 (0~65) — 닦기 · 깜박임 · 유리 깨기 · 경보 · 추격 · 엘리베이터 문
# =====================================================================
def set_A():
    M,A,top=newset(); Z1=640
    top+= corridor(M,0,Z1,wall='w_lab',wall2='w_lab2')+end_wall(M,Z1,door='door',label=13)+end_wall(M,0,facing=1,door='door')+ceiling_lamps(M,0,Z1)
    dl,dr=sliding_door(M,'ed_',0,Z1); top+= [dl,dr]; bl,br=sliding_door(M,'bd_',0,-8); top+= [bl,br]
    top.append(M.cube('shaft_dark',[-40,0,Z1+8],[40,90,Z1+60],'black')); top.append(M.cube('shaft_lad',[-8,0,Z1+40],[8,96,Z1+41],'ladder')); top.append(M.cube('back_dark',[-40,0,-70],[40,90,-10],'black'))
    TX=78; TZ=[200,270,340,410]
    for i,z in enumerate(TZ):
        k,gl=tube(M,f'tb{i}_',TX,z,lit=(i==2),robot=(i!=2)); top+= k; top.append(gl)
        if i==2: glass=gl
    PZ=TZ[2]
    top+= console(M,-72,150)+console(M,-72,214,screen='scr_b')+console(M,-72,300,screen='scr_g')+locker_row(M,-100,360,5,side=1)+shelf_unit(M,-70,500,seed=2)
    top+= pipe_run(M,96,84,0,Z1)+pipe_run(M,-96,88,0,Z1,col='pipe_b')+crate_stack(M,72,500,3,seed=1)+crate_stack(M,66,548,2,seed=2)+crate_stack(M,-72,84,2,seed=4)
    top+= [M.cube('haz',[-100,0.3,Z1-34],[100,0.7,Z1-18],'hazard'), M.cube('cam_arm',[-2,84,118],[2,92,122],'dark'), M.cube('cam_box',[-5,78,112],[5,84,124],'dark'), M.cube('cam_eye',[-2,79.4,110.6],[2,82.6,112],'red')]
    # 청소 도구: 물 양동이 + '미끄럼 주의' 세움판 + 젖은 바닥
    top+= [M.cube('bucket',[14,0,70],[26,11,82],'tank'), M.cube('bucket_w',[15,10.4,71],[25,11.4,81],'wat_l'), M.cube('sign',[-34,0,96],[-22,20,98],'yellow'), M.cube('sign2',[-34,0,102],[-22,20,104],'yellow'), M.cube('sign_t',[-34,19,96],[-22,21,104],'yellow')]
    wet=M.group('wet',[0,0,160],[M.cube('wet',[-40,0.25,100],[40,0.55,170],'wat_l')]); top.append(wet); A.add(wet,'scale',[(0,(1,1,0.1)),(4,(1,1,0.1)),(12,(1,1,1)),(L,(1,1,1))])
    # 붉은 경보 (36초부터): 천장 등이 붉게 + 도는 경보등
    red=M.group('redlamps',[0,95,0],[M.cube('rlamp',[-36,93,z],[36,95.4,z+20],'red') for z in range(40,Z1-20,128)]); top.append(red); vis(A,red,[(36,L)]); cyc(A,red,'scale',36,L,(1,1,1),(1,0.2,1),0.55,rest=(1,1,1),interp='linear')
    alarms(M,A,top,[(0,160),(0,400),(0,580)],36,L)
    # 핍 (유리관 안 → 밖)
    pp=PIP(M,A,top,TX,PZ,-90,y=9); lamp=pp.part('lamp')
    A.add(lamp,'scale',[(0,(1,1,1))]+[(12+k*0.25,(2.2,2.2,2.2) if (k%8 in (0,1,2,4)) else (0.4,0.4,0.4)) for k in range(int((34-12)/0.25))]+[(34.2,(1,1,1))],'linear')
    pp.show([(0,39.6)]); pp.hop(34.8,36.2,58,PZ-6,h=14,n=1); pp.hop(37.0,39.6,24,PZ-10,h=18,n=2)
    # 모프
    mo=MOP(M,A,top,10,80,180); mr=mo.part('arm_right')
    mo.go(4,12,6,170,per=1.1,amp=14); cyc(A,mr,'rotation',1,12,(-30,0,10),(-52,0,-12),0.9,rest=(0,0,0))
    mo.go(12.5,14,2,200,per=1.1,amp=14); mo.headturn(14.5,19,ry=-70); mo.look(19.2,TX,PZ,0.6); mo.go(20,23.5,36,PZ-6,per=1.0,amp=16); mo.look(23.6,TX,PZ,0.2)
    mo.tilt(24,26,12); mo.headturn(26.2,27.4,ry=75); mo.headturn(27.6,28.8,ry=-75)
    mo.turn(29,270,0.5); mo.go(29.6,30.8,14,PZ-6,per=0.9,amp=14,face=False); mo.look(31.6,TX,PZ,0.5); mo.go(32.2,33.2,40,PZ-6,per=0.6)
    A.add(mr,'rotation',[(33.2,(0,0,0)),(33.9,(-165,0,0)),(34.25,(-165,0,0)),(34.5,(-60,0,0)),(35.2,(-60,0,0)),(35.8,(0,0,0))],'catmullrom')
    vis(A,glass,[(0,34.5)])
    for k in range(3): puff(M,A,top,TX-12,30+k*10,PZ-10,34.5+k*0.05,1.0,7,'glass',26,-18,2.6,seed=k)
    cue(34.5,'glass'); cue(36,'alarm'); cue(12,'blink'); cue(28,'blink')
    A.add(mo.part('arm_left'),'rotation',[(36.6,(0,0,0)),(37.4,(-70,0,-20)),(39.4,(-70,0,-20)),(40.0,(-150,0,0)),(40.6,(0,0,0))],'catmullrom')
    mo.turn(40.6,180,0.4)
    # 추격: 경비 로봇이 뒤쪽 문에서
    A.add(bl,'position',[(0,(0,0,0)),(41,(0,0,0)),(42,(-30,0,0))]); A.add(br,'position',[(0,(0,0,0)),(41,(0,0,0)),(42,(30,0,0))]); cue(41,'door')
    gd=GUARD(M,A,top,0,-40,180); gd.show([(41,L)]); gd.go(42,47,0,150,per=0.7,amp=24); gd.go(47,58,-6,520,per=0.5,amp=34); gd.go(58,64.5,0,600,per=0.6,amp=28)
    A.add(gd.part('arm_right'),'rotation',[(47,(0,0,0)),(48,(-80,0,0)),(64,(-80,0,0))])
    mo.go(43.5,49,-8,Z1-52,per=0.36,amp=44); run_pose(A,mo,43.5,49); cue(43.5,'run'); cue(42,'stomp'); cue(47,'stomp')
    mo.go(49,50,0,Z1-16,per=0.5)
    for arm in ('arm_left','arm_right'): A.add(mo.part(arm),'rotation',[(50,(0,0,0)),(50.5,(-85,0,0)),(61,(-85,0,0)),(61.6,(0,0,0))] if arm=='arm_left' else [(50,(0,0,0)),(50.5,(-70,0,0)),(61,(-70,0,0)),(61.6,(0,0,0))],'catmullrom')
    cyc(A,mo.g,'rotation',50.6,59,(0,0,3),(0,0,-3),0.5,rest=(0,0,0))
    A.add(dl,'position',[(0,(0,0,0)),(52,(0,0,0)),(55,(-6,0,0)),(57,(-5,0,0)),(60.5,(-28,0,0))]); A.add(dr,'position',[(0,(0,0,0)),(52,(0,0,0)),(55,(6,0,0)),(57,(5,0,0)),(60.5,(28,0,0))]); cue(52,'creak'); cue(57,'creak')
    mo.go(61.8,63.4,0,Z1+34,per=0.4,amp=36,y=0); mo.show([(0,63.6)]); cue(63.4,'whoosh')
    # 샷
    sh('제목',    'A',0,4,cam((0,[0,60,-2],[0,44,300],{'fov':50}),(1,[0,50,40],[0,34,300],{'fov':42})),IN)
    sh('닦는모프','A',4,12,cam((0,[-30,22,236],[6,18,120]),(1,[-34,26,262],[6,20,170])),IN)
    sh('깜박임',  'A',12,16,cam((0,[20,40,PZ-70],[TX,22,PZ],{'fov':40}),(1,[36,34,PZ-44],[TX,20,PZ],{'fov':28})),IN)
    sh('돌아봄',  'A',16,20,orbit((2,200),70,30,150,95,(2,26,200),r1=56),IN)
    sh('유리관앞','A',20,24,cam((0,[-60,40,PZ-60],[50,24,PZ]),(1,[-30,30,PZ-50],[56,22,PZ])),IN)
    sh('핍눈',    'A',24,26,cam((0,[52,22,PZ-12],[TX,19,PZ],{'fov':30}),(1,[56,21,PZ-10],[TX,19,PZ],{'fov':24})),IN)
    sh('망설임',  'A',26,31,orbit((36,PZ-6),64,30,-150,-60,(36,26,PZ-6),r1=54),IN)
    sh('돌아섬',  'A',31,33.2,cam((0,[-40,14,PZ-60],[30,24,PZ-6],{'fov':44}),(1,[-20,16,PZ-40],[36,26,PZ-6],{'fov':36})),IN)
    sh('깬다',    'A',33.2,36,cam((0,[-10,30,PZ-70],[60,30,PZ],{'fov':40}),(0.45,[-10,30,PZ-70],[60,30,PZ],{'fov':40,'shake':0}),(0.5,[4,30,PZ-56],[62,30,PZ],{'fov':52,'shake':1,'roll':6}),(1,[0,28,PZ-64],[60,24,PZ],{'fov':44,'shake':0.2,'roll':0})),IN,shake=3)
    sh('나온핍',  'A',36,40.6,cam((0,[20,10,PZ-50],[56,12,PZ-6]),(0.6,[10,14,PZ-56],[30,20,PZ-10]),(1,[4,34,PZ-66],[36,30,PZ-8])),IN)
    sh('경비등장','A',40.6,43.5,cam((0,[30,20,120],[0,26,-10],{'fov':38}),(1,[20,14,96],[0,30,10],{'fov':30})),IN,shake=1)
    sh('달린다',  'A',43.5,49,cam((0,[24,30,-90],[0,22,60],{'fov':42,'roll':0}),(0.5,[-20,22,-70],[0,22,80],{'fov':64,'roll':-6}),(1,[16,34,-80],[0,24,70],{'fov':58,'roll':5})),IN,follow='m_mv',shake=1.6)
    sh('문앞',    'A',49,52,cam((0,[-30,50,Z1-170],[0,30,Z1-10],{'fov':44}),(1,[-20,30,Z1-90],[0,30,Z1-10],{'fov':38})),IN)
    sh('다가옴',  'A',52,55,cam((0,[0,26,Z1-40],[0,34,300],{'fov':34}),(1,[0,26,Z1-40],[0,34,300],{'fov':24})),IN,shake=1.2)
    sh('문열기',  'A',55,61.8,orbit((0,Z1-16),70,26,-70,60,(0,26,Z1-6),r1=58,h1=40),IN,shake=1)
    sh('뛰어듦',  'A',61.8,65,cam((0,[-60,40,Z1-110],[0,26,Z1],{'fov':46}),(0.5,[-40,34,Z1-90],[0,26,Z1+20],{'fov':52}),(1,[-10,30,Z1-70],[0,40,Z1+30],{'fov':40})),IN,shake=2)
    caption(0.4,3.6,'13층 아래','Title'); caption(13,19,'「 꺼 내  줘 」','Blink'); caption(4.5,8,'B13','Floor')
    return save(M,A,top,'B13','A')

# =====================================================================
#  H : 엘리베이터 통로 — (65~100) 사다리, 내려오는 엘리베이터, B10 으로 / (205~240) 엘리베이터 지붕 위, 드론
# =====================================================================
def set_H():
    M,A,top=newset(); LH=120; NL=11; W=176; h=W/2
    top+= shaft(M,NL,W=W,LH=LH,first=13)
    lv=lambda n: (13-n)*LH               # n층 바닥 높이
    # 엘리베이터 (지붕 높이가 원점)
    car=actor(M,A,top,elevator_car(M,'car_',W=156),'car_',0,0,0,y=lv(4)+90,legs=None)
    car.at(65,0,0,y=lv(5)+90); car.go(78,89.6,0,0,y=lv(10)+150,walk=False,face=False); cue(78,'elevator'); cue(88.5,'clang')
    car.at(200,0,0,y=lv(7)+90); car.go(206,236,0,0,y=lv(3)+90,walk=False,face=False); cue(206,'elevator')
    cl=find(car.g,'car_root'); 
    # --- 1부: 사다리 (x 66, z h-10) ---
    LX,LZ=66,h-12
    mo=MOP(M,A,top,0,h-26,180); mo.show([(65,99.6),(204,L)])
    mo.at(65,0,h-26,180,y=lv(13)); mo.go(65.5,67,LX,LZ,per=0.5); mo.turn(67,180,0.2)
    mo.go(67.4,88.2,LX,LZ,y=lv(10)+24,walk=False,face=False); cyc(A,mo.part('arm_left'),'rotation',67.4,89.4,(-150,0,0),(-60,0,0),0.7,rest=(0,0,0)); cyc(A,mo.part('arm_right'),'rotation',67.4,89.4,(-60,0,0),(-150,0,0),0.7,rest=(0,0,0))
    cyc(A,mo.part('leg_left'),'rotation',67.4,89.4,(-40,0,0),(10,0,0),0.7,rest=(0,0,0)); cyc(A,mo.part('leg_right'),'rotation',67.4,89.4,(10,0,0),(-40,0,0),0.7,rest=(0,0,0)); cue(67.4,'climb')
    A.add(mo.part('head'),'rotation',[(76,(0,0,0)),(77,(-40,0,0)),(86,(-40,0,0)),(87,(0,0,0))])
    # 더듬이가 엘리베이터 바닥에 스쳐 부러짐 → 옆 문턱으로 뛰어내림
    fall(M,A,top,part_model(M,'antenna'),LOST['antenna'],LX+3,lv(10)+56,LZ,40,40,dur=0.9,keep=6); cue(88,'snap')
    mo.hold(89.4); mo.pk.append((89.9,((LX+0)/2+6,lv(10)+18,h-22),'catmullrom')); mo.pk.append((90.5,(0,lv(10),h-22),'catmullrom')); mo.cur=(0,lv(10),h-22); mo.yk.append((90.5,180))
    puff(M,A,top,0,lv(10)+2,h-22,90.5,0.7,5,'steam',10,6,2)
    for arm in ('arm_left','arm_right'): A.add(mo.part(arm),'rotation',[(92,(0,0,0)),(92.6,(-80,0,0)),(97,(-80,0,0)),(97.6,(0,0,0))],'catmullrom')
    b10=M.group('b10door',[0,lv(10),h+3],[M.cube('b10cover',[-32,lv(10),h-0.6],[32,lv(10)+56,h+0.6],'door')]); top.append(b10)
    A.add(b10,'scale',[(0,(1,1,1)),(93,(1,1,1)),(97,(0.04,1,1)),(100.5,(0.04,1,1)),(101,(1,1,1))]); cue(93,'creak')
    mo.go(97.8,99.4,0,h+30,y=lv(10),per=0.4)
    gd=GUARD(M,A,top,0,h-30,180); gd.show([(70,99)]); gd.at(70,0,h-24,180,y=lv(13)); A.add(gd.part('head'),'rotation',[(70,(0,0,0)),(71,(-50,0,0)),(99,(-50,0,0))]); A.add(gd.part('arm_right'),'rotation',[(72,(0,0,0)),(73,(-150,0,0)),(99,(-150,0,0))])
    # --- 2부: 엘리베이터 지붕 위 (205~240), 드론 셋 ---
    ry=lambda t: lv(7)+90+(lv(3)-lv(7))*min(1,max(0,(t-206)/30))+3
    mo.at(204,10,-10,160,y=ry(204)); 
    def on_roof(a,t0,t1,x,z,**kw): a.go(t0,t1,x,z,y=ry(t1),walk=False,face=False,**kw)
    tt=206
    while tt<236: on_roof(mo,tt,min(tt+2,236),10+6*math.sin(tt),-10+5*math.cos(tt*0.7)); tt+=2
    drs=[]
    for i in range(3):
        d=actor(M,A,top,drone(M,f'd{i}_',1.3),f'd{i}_',0,0,0,y=lv(2),legs=None); d.show([(208+i*1.5,L if i==2 else (222 if i==0 else 231))]); drs.append(d)
        A.add(find(d.g,f'd{i}_rotor'),'rotation',[(0,(0,0,0)),(L,(0,360*L*3,0))])
        t=208+i*1.5; d.at(t,60*math.cos(i*2.1),60*math.sin(i*2.1),0,y=ry(t)+150)
        while t<236:
            a=t*1.9+i*2.1; r=52+18*math.sin(t*1.3+i); t2=min(t+0.8,236)
            d.go(t,t2,r*math.cos(a),-14+r*math.sin(a),y=ry(t2)+34+16*math.sin(t*2.3+i*1.7),walk=False,face=False,interp='catmullrom'); d.look(t2-0.1,10,-10,0.1); t=t2
    cue(208,'drone'); cue(214,'drone'); cue(220,'drone')
    # 모프가 걸레로 하나를 쳐냄 (221.5) → 드론 0 추락
    A.add(mo.part('arm_right'),'rotation',[(212,(0,0,0)),(212.5,(-120,0,0)),(220.8,(-140,0,-20)),(221.5,(-40,0,50)),(222.3,(-120,0,0)),(227.5,(-130,0,0)),(229,(0,0,0))],'catmullrom')
    cyc(A,mo.g,'rotation',212,227,(0,25,0),(0,-25,0),1.6,rest=(0,0,0))
    d0=drs[0]; d0.hold(221.5); d0.go(221.5,222.4,90,70,y=ry(222.4)-200,walk=False,face=False,interp='catmullrom'); puff(M,A,top,30,ry(221.5)+30,10,221.5,0.8,8,'spark',22,16,2.4); cue(221.5,'hit')
    # 드론 1 이 머리를 들이받음 (228) → 머리 껍데기가 날아감, 드론 1 도 튕겨 떨어짐
    d1=drs[1]; d1.hold(227.2); d1.go(227.2,228.0,10,-10,y=ry(228)+27,walk=False,face=False); d1.go(228.0,229.2,-80,-70,y=ry(229.2)-160,walk=False,face=False,interp='catmullrom')
    fall(M,A,top,part_model(M,'headshell'),LOST['headshell'],10,ry(228)+26,-10,-50,30,dur=1.6,keep=0.1); puff(M,A,top,10,ry(228)+28,-10,228,0.7,8,'spark',18,14,2.2); cue(228,'hit'); cue(228.1,'snap')
    A.add(mo.g,'rotation',[(228,(0,0,0)),(228.3,(-30,0,10)),(229.4,(0,0,0))],'catmullrom')
    eye=mo.part('eye'); cyc(A,eye,'scale',228.2,233,(1,1,1),(0,0,0),0.22,rest=(1,1,1),interp='linear')
    d2=drs[2]; d2.hold(236); d2.go(236,238.5,0,-40,y=lv(3)+330,walk=False,face=False)
    # B3 도착: 문턱으로 내림
    b3=M.group('b3door',[0,lv(3),h+3],[M.cube('b3cover',[-32,lv(3),h-0.6],[32,lv(3)+56,h+0.6],'door')]); top.append(b3); A.add(b3,'scale',[(0,(1,1,1)),(236.5,(1,1,1)),(238,(0.04,1,1)),(L,(0.04,1,1))]); cue(236,'clang'); cue(236.6,'door')
    mo.at(236.2,10,-10,180,y=lv(3)+93); mo.hop(237,239.6,0,h+26,h=10,n=3); 
    # 샷 1부
    sh('통로안',  'H',65,67.4,cam((0,[-50,lv(13)+40,-40],[20,lv(13)+30,h],{'fov':50}),(1,[-40,lv(13)+90,-50],[40,lv(13)+60,h],{'fov':56})),IN)
    sh('올려다봄','H',67.4,72,cam((0,[-30,lv(13)+10,-30],[40,lv(13)+400,40],{'fov':60,'roll':-8}),(1,[-10,lv(13)+60,-10],[30,lv(13)+600,50],{'fov':70,'roll':10})),IN)
    sh('오른다',  'H',72,78,cam((0,[-70,30,-60],[0,20,0],{'fov':46}),(1,[-30,50,-70],[0,22,0],{'fov':40})),IN,follow='m_mv')
    sh('내려온다','H',78,84,cam((0,[0,8,-40],[0,300,-14],{'fov':62}),(1,[10,30,-30],[0,200,-14],{'fov':48})),IN,follow='m_mv',shake=1.5)
    sh('아찔',    'H',84,88,cam((0,[-50,34,-50],[-20,-200,-20],{'fov':66,'roll':-12}),(1,[-40,24,-40],[-20,-300,-20],{'fov':74,'roll':8})),IN,follow='m_mv',shake=1)
    sh('스친다',  'H',88,91,cam((0,[-70,lv(10)+44,-50],[LX,lv(10)+44,LZ],{'fov':40}),(0.5,[-60,lv(10)+36,-40],[30,lv(10)+30,LZ],{'fov':46,'shake':1}),(1,[-50,lv(10)+30,-30],[0,lv(10)+20,h-20],{'fov':40})),IN,shake=4)
    sh('떨어지는더듬이','H',91,93,cam((0,[-40,lv(10)+40,-40],[20,lv(10)+20,60],{'fov':40}),(1,[-30,lv(10)+34,-30],[30,lv(10)+4,50],{'fov':30})),IN)
    sh('B10문',   'H',93,100,cam((0,[-40,lv(10)+44,-60],[0,lv(10)+30,h],{'fov':44}),(1,[-20,lv(10)+34,-20],[0,lv(10)+30,h],{'fov':36})),IN)
    # 샷 2부
    sh('지붕위',  'H',205,208,cam((0,[50,60,-60],[0,24,0],{'fov':50}),(1,[40,40,-54],[0,26,0],{'fov':44})),IN,follow='m_mv')
    sh('드론온다','H',208,213,cam((0,[-36,14,-44],[30,120,60],{'fov':64,'roll':6}),(1,[-30,18,-40],[40,80,40],{'fov':56,'roll':-10})),IN,follow='m_mv',shake=1)
    sh('빙글',    'H',213,221,[dict(k,roll=(-10 if i%2 else 10),fov=56) for i,k in enumerate(orbit((0,0),56,54,0,400,(0,26,0),n=10,r1=48,h1=40))],IN,follow='m_mv',shake=1.2)
    sh('쳐낸다',  'H',221,224,cam((0,[-50,30,-40],[0,34,0],{'fov':44}),(0.2,[-44,30,-36],[10,36,6],{'fov':38,'shake':1}),(1,[-60,60,-50],[60,-80,60],{'fov':56,'roll':12})),IN,follow='m_mv',shake=3)
    sh('층이지나감','H',224,227.2,cam((0,[-40,20,-50],[60,30,h],{'fov':70,'roll':-6}),(1,[-40,24,-50],[60,34,h],{'fov':70,'roll':6})),IN,follow='car_mv',shake=1.4)
    sh('들이받음','H',227.2,230,cam((0,[40,40,-50],[0,30,0],{'fov':44}),(0.3,[30,36,-40],[0,30,0],{'fov':34,'shake':1}),(1,[36,30,-46],[0,26,0],{'fov':40,'roll':-8})),IN,follow='m_mv',shake=5)
    sh('깜박이는눈','H',230,234,cam((0,[6,28,-40],[0,26,0],{'fov':30}),(1,[-10,28,-34],[0,27,0],{'fov':24})),IN,follow='m_mv')
    sh('도착',    'H',234,240,cam((0,[-30,56,-56],[0,20,20],{'fov':50}),(0.4,[-26,44,-50],[0,20,30],{'fov':44,'shake':1}),(1,[-20,34,-40],[0,24,h+10],{'fov':38})),IN,follow='car_mv',shake=2)
    caption(66,69,'B12','Floor'); caption(93.5,97,'B10','Floor'); caption(206,209,'B6','Floor'); caption(218,221,'B5','Floor'); caption(226,229,'B4','Floor'); caption(236.5,239.5,'B3','Floor')
    return save(M,A,top,'통로','H')

# =====================================================================
#  B : B10 레이저 복도 (100~135)
# =====================================================================
def set_B():
    M,A,top=newset(); Z1=576
    top+= corridor(M,0,Z1,wall='w_dark',floor='f_dark',ceil='c_red')+end_wall(M,Z1,wall='w_dark',door='door',label=9)+end_wall(M,0,wall='w_dark',facing=1,door='door',label=10)
    dl,dr=sliding_door(M,'xd_',0,Z1); top+= [dl,dr]; top.append(M.cube('back_dark',[-40,0,-70],[40,90,-10],'black')); top.append(M.cube('fwd_dark',[-40,0,Z1+8],[40,90,Z1+60],'black'))
    top+= pipe_run(M,96,86,0,Z1,col='steel_d')+pipe_run(M,-96,86,0,Z1,col='steel_d')+[M.cube('haz',[-100,0.3,70],[100,0.7,86],'hazard'), M.cube('haz2',[-100,0.3,Z1-90],[100,0.7,Z1-74],'hazard')]
    top+= console(M,-70,40,screen='scr_r')+crate_stack(M,74,40,2,seed=3)+crate_stack(M,-72,Z1-40,2,seed=5)+crate_stack(M,74,Z1-44,3,seed=6)
    # 레이저: 가로 빛줄기 11개 (높이가 오르내림) + 세로 빛줄기 3개 (좌우로 오감). 발사기는 벽에
    beams=[]
    for i in range(11):
        z=110+i*36; y0=10+(i*17)%50; g=M.group(f'beam{i}',[0,y0,z],[M.cube('beam',[-100,y0-0.9,z-0.9],[100,y0+0.9,z+0.9],'laser'), M.cube('beam_c',[-100,y0-0.35,z-1.2],[100,y0+0.35,z+1.2],'laser_c')]); top.append(g); beams.append(g)
        top+= [M.cube('emit',[94,y0-5,z-5],[100,y0+5,z+5],'dark'), M.cube('emit',[-100,y0-5,z-5],[-94,y0+5,z+5],'dark')]
        amp=14+(i%3)*8; per=1.6+(i%4)*0.35; cyc(A,g,'position',100,L,(0,amp,0),(0,-min(amp,y0-4),0),per,rest=(0,0,0))
    for i in range(3):
        z=170+i*130; g=M.group(f'vbeam{i}',[0,48,z],[M.cube('vbeam',[-0.9,0,z-0.9],[0.9,96,z+0.9],'laser'), M.cube('vbeam_c',[-1.2,0,z-0.35],[1.2,96,z+0.35],'laser_c')]); top.append(g); beams.append(g)
        cyc(A,g,'position',100,L,(70,0,0),(-70,0,0),2.2+i*0.5,rest=(0,0,0))
    for g in beams:      # 김이 퍼진 동안(122.5~131) 빛줄기가 흐려져 깜박이다 꺼짐
        A.add(g,'scale',[(0,(1,1,1)),(122.4,(1,1,1)),(122.9,(1,0.25,0.25)),(123.6,(1,1,1)),(124.2,(1,0.1,0.1)),(125,(0,0,0)),(131,(0,0,0)),(131.8,(1,1,1))])
    mo=MOP(M,A,top,0,-40,180)
    mo.go(100.5,102.5,0,56,per=0.7); mo.headturn(103,105.5,ry=40); A.add(mo.part('head'),'rotation',[(106,(0,0,0)),(106.8,(16,0,0)),(107.8,(-16,0,0)),(108.8,(16,0,0)),(109.8,(-16,0,0)),(110.6,(0,0,0))],'catmullrom')
    # 1) 미끄러져 지나감 (112~114.5): 몸을 뒤로 눕히고 낮게
    A.add(mo.g,'rotation',[(111.9,(0,0,0)),(112.4,(-62,0,0)),(114.0,(-62,0,0)),(114.6,(0,0,0))],'catmullrom')
    mo.go(111.2,112.2,0,96,per=0.4,amp=40); mo.go(112.2,114.2,0,200,walk=False,y=-3); mo.go(114.2,114.7,0,214,walk=False,y=0); cue(112.2,'slide')
    # 2) 뛰어넘음 (115.4~117)  3) 멈칫 (117~118.6)  4) 옆으로 구르듯 (118.6~121)
    mo.hop(115.4,117.0,-30,300,h=34,n=1); cue(115.4,'jump'); mo.tilt(117.2,118.4,10)
    mo.go(118.6,121.2,36,372,per=0.36,amp=44); run_pose(A,mo,118.6,121.2)
    # 빛이 물통을 자름 → 김
    tk=fall(M,A,top,part_model(M,'tank'),LOST['tank'],36,16,366,54,330,dur=1.0); cue(121.5,'zap'); cue(121.8,'steam')
    for k in range(18): puff(M,A,top,40+((k*37)%150-75),6+(k%4)*9,330+k*12,121.8+k*0.1,5.5,4,'steam',34,16,5.5,seed=k)
    A.add(mo.g,'rotation',[(121.5,(0,0,0)),(121.8,(20,0,-14)),(122.6,(0,0,0))],'catmullrom')
    mo.go(122.8,129.5,0,Z1-26,per=0.45,amp=36); run_pose(A,mo,122.8,129.5)
    A.add(dl,'position',[(0,(0,0,0)),(128.6,(0,0,0)),(130.2,(-28,0,0))]); A.add(dr,'position',[(0,(0,0,0)),(128.6,(0,0,0)),(130.2,(28,0,0))]); cue(128.6,'door')
    mo.go(130.4,132.4,0,Z1+34,per=0.5); mo.show([(0,132.8)])
    sh('레이저층','B',100,103,cam((0,[0,40,24],[0,36,300],{'fov':40}),(1,[0,60,40],[0,30,300],{'fov':62})),IN)
    sh('살핀다',  'B',103,106,orbit((0,56),60,28,170,120,(0,26,56),r1=50),IN)
    sh('박자',    'B',106,111.2,cam((0,[-60,16,120],[60,30,260],{'fov':50}),(1,[-70,20,150],[70,30,300],{'fov':44})),IN)
    sh('미끄러짐','B',111.2,114.7,cam((0,[50,8,-40],[0,10,60],{'fov':60,'roll':-8}),(1,[44,6,-20],[0,8,70],{'fov':68,'roll':6})),IN,follow='m_mv',shake=1)
    sh('뛰어넘음','B',114.7,117.2,cam((0,[-80,10,250],[-10,26,270],{'fov':50,'roll':10}),(1,[-90,14,300],[-20,30,290],{'fov':44,'roll':-4})),IN,shake=1)
    sh('숨고르기','B',117.2,118.6,cam((0,[-70,34,356],[-30,28,300],{'fov':36}),(1,[-66,32,350],[-30,28,300],{'fov':30})),IN)
    sh('옆으로',  'B',118.6,121.4,cam((0,[20,30,-80],[0,22,50],{'fov':58,'roll':-10}),(1,[-24,24,-70],[0,22,60],{'fov':66,'roll':8})),IN,follow='m_mv',shake=1.6)
    sh('물통',    'B',121.4,124,cam((0,[-30,40,300],[40,20,366],{'fov':40}),(0.2,[-20,34,310],[42,18,362],{'fov':30,'shake':1}),(1,[-50,50,280],[40,24,360],{'fov':52,'roll':8})),IN,shake=3)
    sh('김속으로','B',124,129.5,cam((0,[10,44,70],[0,22,-20],{'fov':46}),(0.7,[-10,40,50],[0,22,-20],{'fov':54}),(1,[-30,36,-60],[0,22,10],{'fov':50})),IN,follow='m_mv',shake=1)
    sh('문으로',  'B',129.5,135,cam((0,[60,50,Z1-170],[0,26,Z1-10],{'fov':46}),(1,[30,30,Z1-90],[0,26,Z1+10],{'fov':38})),IN)
    caption(100.5,104,'B10','Floor')
    return save(M,A,top,'B10','B')

# =====================================================================
#  C : B9 창고 (135~170) — 상자 사이 추격, 내려오는 방화문, 왼팔
# =====================================================================
def set_C():
    M,A,top=newset(); Z1=640; W=384
    top+= corridor(M,0,Z1,W=W,H=128,wall='w_ware',floor='f_conc',ceil='c_dark')+end_wall(M,0,W=W,H=128,wall='w_ware',facing=1,door='door',label=9)+ceiling_lamps(M,0,Z1,W=W,H=128,col='lamp')
    # 끝 벽: 가운데 넓은 방화문 자리(폭 120)
    for x in range(-192,192,64):
        if abs(x+32)>70: top.append(M.cube('end',[x,0,Z1],[x+64,128,Z1+8],'w_ware'))
    top+= [M.cube('endT',[-64,96,Z1],[64,128,Z1+8],'steel_d'), M.cube('fr_l',[60,0,Z1-2],[68,98,Z1+2],'yellow'), M.cube('fr_r',[-68,0,Z1-2],[-60,98,Z1+2],'yellow'), M.cube('fwd_dark',[-64,0,Z1+10],[64,100,Z1+70],'black'),
           M.cube('haz',[-64,0.3,Z1-30],[64,0.7,Z1-14],'hazard'), M.cube('back_dark',[-40,0,-70],[40,90,-10],'black')]
    top+= big_label(M,0,100,Z1-0.2,8,w=56)
    stacks=[(-150,90,4),(-150,150,3),(-96,120,3),(140,100,4),(150,170,3),(96,60,2),(-140,300,4),(-84,330,3),(-150,380,3),(150,320,4),(96,350,3),(150,420,3),(-150,520,4),(150,540,4),(110,560,2),(-100,570,2),(40,250,2),(-30,430,3)]
    for i,(x,z,n) in enumerate(stacks): top+= crate_stack(M,x,z,n,s=30,seed=i)
    top+= shelf_unit(M,-150,210,w=64,levels=4,seed=3)+shelf_unit(M,150,230,w=64,levels=4,seed=4)+shelf_unit(M,-150,450,w=64,levels=4,seed=5)+shelf_unit(M,150,470,w=64,levels=4,seed=6)
    top+= pipe_run(M,186,116,0,Z1)+pipe_run(M,-186,112,0,Z1,col='pipe_b')
    # 지게차 (세워 둠)
    fx,fz=-60,200
    top+= [M.cube('fk_body',[fx-14,6,fz-20],[fx+14,26,fz+16],'orange'), M.cube('fk_cab',[fx-12,26,fz-4],[fx+12,48,fz+14],'dark'), M.cube('fk_mast',[fx-10,0,fz-24],[fx-7,60,fz-21],'steel_d'), M.cube('fk_mast',[fx+7,0,fz-24],[fx+10,60,fz-21],'steel_d'),
           M.cube('fk_fork',[fx-9,3,fz-44],[fx-5,5,fz-22],'steel'), M.cube('fk_fork',[fx+5,3,fz-44],[fx+9,5,fz-22],'steel'), M.cube('fk_w',[fx-16,0,fz-16],[fx-12,10,fz-6],'rubber'), M.cube('fk_w',[fx+12,0,fz-16],[fx+16,10,fz-6],'rubber'),
           M.cube('fk_w',[fx-16,0,fz+4],[fx-12,10,fz+14],'rubber'), M.cube('fk_w',[fx+12,0,fz+4],[fx+16,10,fz+14],'rubber'), M.cube('fk_lamp',[fx-3,48,fz+2],[fx+3,52,fz+8],'yellow')]
    alarms(M,A,top,[(0,120),(0,360),(0,580)],135,L,y=118)
    # 방화문 (152~162 내려옴). 원점 = 문 아래쪽
    door=actor(M,A,top,M.group('fd_root',[0,0,0],[M.cube('fdoor',[-60,0,-4],[60,100,4],'steel_d'), M.cube('fdoor_h',[-60,0,-4.6],[60,10,-4],'hazard'), M.cube('fdoor_b',[-60,40,-4.8],[60,46,4.8],'yellow')]),'fd_',0,Z1+4,0,y=98,legs=None)
    door.go(150,152,0,Z1+4,y=98,walk=False,face=False); door.go(152,161.4,0,Z1+4,y=13,walk=False,face=False); door.go(161.4,165.6,0,Z1+4,y=11,walk=False,face=False); door.go(165.6,166.0,0,Z1+4,y=0,walk=False,face=False)
    cue(152,'rumble'); cue(166,'slam')
    # 쓰러뜨릴 상자 더미 (148)
    tp=M.group('topple',[20,0,300],crate_stack(M,20,300,4,s=30,seed=9)); top.append(tp); A.add(tp,'rotation',[(0,(0,0,0)),(147.6,(0,0,0)),(148.6,(0,0,-84))],'catmullrom'); cue(148.4,'crash')
    for k in range(2): puff(M,A,top,-60,8,300,148.5+k*0.1,1.2,8,'conc',40,18,6,seed=k)
    mo=MOP(M,A,top,0,-40,180)
    mo.go(135.5,137.5,0,50,per=0.5); mo.headturn(137.6,139,ry=-60)
    g1=GUARD(M,A,top,170,60,-90,tag='g1_'); g2=GUARD(M,A,top,-170,560,90,tag='g2_')
    g1.show([(138,L)]); g1.at(138,176,40,-90); g1.go(138.4,141,60,60,per=0.5,amp=30)
    path=[(139.4,141.4,-40,140),(141.4,143.2,60,190),(143.2,145.2,90,280),(145.2,147.4,56,300),(148.8,151,-30,400),(151,153.6,40,500)]
    for t0,t1,x,z in path: mo.go(t0,t1,x,z,per=0.34,amp=44)
    run_pose(A,mo,139.4,147.4); run_pose(A,mo,148.8,159.4)
    A.add(mo.part('arm_left'),'rotation',[(147.4,(0,0,0)),(147.7,(-90,0,-60)),(148.4,(-90,0,30)),(148.9,(0,0,0))],'catmullrom')
    for t0,t1,x,z in [(141,143,-20,150),(143,145.4,70,200),(145.4,148.2,60,286)]: g1.go(t0,t1,x,z,per=0.42,amp=32)
    A.add(g1.g,'rotation',[(148.4,(0,0,0)),(148.9,(-70,0,0)),(L,(-70,0,0))]); g1.go(148.4,148.9,40,270,walk=False,face=False,y=4)
    g2.show([(150,L)]); g2.go(150.5,153,-90,520,per=0.5,amp=30); g2.go(153,158.5,-10,590,per=0.45,amp=30); g2.look(158.6,0,Z1,0.2)
    A.add(g2.part('arm_right'),'rotation',[(153,(0,0,0)),(153.6,(-85,0,0)),(L,(-85,0,0))])
    mo.go(153.6,156.4,60,560,per=0.34,amp=44); mo.go(156.4,159.4,10,Z1-40,per=0.34,amp=44)
    # 미끄러져 문 밑으로 (159.4~161.4) → 왼팔이 끼임 → 떼고 빠져나옴 (163)
    A.add(mo.g,'rotation',[(159.2,(0,0,0)),(159.7,(-70,0,0)),(165.2,(-70,0,0)),(166.2,(0,0,0))],'catmullrom')
    mo.go(159.4,161.4,10,Z1+16,walk=False,y=-3); cue(159.4,'slide'); cue(161.4,'clang')
    A.add(mo.part('arm_left'),'rotation',[(160.6,(0,0,0)),(161.4,(-160,0,0)),(163,(-160,0,0))])
    cyc(A,mo.out,'scale',161.6,162.9,(1,1,1),(1,1,1.06),0.3,rest=(1,1,1))
    stuck=M.group('stuckarm',[18,6,Z1+2],[M.cube('sa',[15.4,3,Z1-8],[20.6,6.2,Z1+10],'frame'), M.cube('sa2',[15,2.6,Z1-12],[21,6.6,Z1-7],'teal')]); top.append(stuck); vis(A,stuck,[(163,L)])
    puff(M,A,top,18,8,Z1+6,163,0.8,8,'spark',14,12,2); cue(163,'snap'); cue(163.1,'spark')
    mo.go(163,164.2,6,Z1+50,walk=False,y=-3); mo.show([(0,166.4)])
    sh('창고',    'C',135,139.4,cam((0,[0,110,10],[0,40,300],{'fov':56}),(1,[30,60,-10],[0,30,200],{'fov':44})),IN)
    sh('상자사이','C',139.4,145.2,cam((0,[26,30,-44],[0,22,60],{'fov':56,'roll':-8}),(0.35,[-30,22,-70],[0,22,70],{'fov':66,'roll':10}),(0.7,[30,26,-76],[0,22,70],{'fov':62,'roll':-10}),(1,[-10,34,-84],[0,22,60],{'fov':56,'roll':4})),IN,follow='m_mv',shake=1.6)
    sh('쫓는경비','C',145.2,147.4,cam((0,[0,34,60],[0,40,-40],{'fov':50}),(1,[0,30,50],[0,40,-40],{'fov':60})),IN,follow='g1_mv',shake=2)
    sh('무너뜨림','C',147.4,150,cam((0,[-110,70,220],[20,40,300],{'fov':46}),(0.4,[-100,60,230],[10,30,300],{'fov':40,'shake':1}),(1,[-130,90,200],[-20,10,300],{'fov':54,'roll':-6})),IN,shake=4)
    sh('방화문',  'C',150,153.6,cam((0,[60,26,440],[0,60,Z1],{'fov':44}),(1,[36,18,490],[0,50,Z1],{'fov':34})),IN,shake=1)
    sh('전력질주','C',153.6,159.4,cam((0,[20,26,-90],[0,22,80],{'fov':60,'roll':6}),(0.5,[-16,18,-70],[0,24,90],{'fov':72,'roll':-8}),(1,[0,12,-60],[0,22,100],{'fov':78,'roll':0})),IN,follow='m_mv',shake=2)
    sh('문밑으로','C',159.4,161.6,cam((0,[70,8,Z1-60],[10,10,Z1],{'fov':48,'roll':-10}),(1,[50,6,Z1-36],[10,8,Z1+6],{'fov':40,'roll':4})),IN,shake=2)
    sh('끼인팔',  'C',161.6,163.2,cam((0,[50,14,Z1-40],[18,8,Z1],{'fov':30}),(1,[44,12,Z1-34],[18,8,Z1],{'fov':24})),IN,shake=1.5)
    sh('닫힘',    'C',163.2,170,cam((0,[40,20,Z1-60],[16,10,Z1],{'fov':34}),(0.4,[20,30,Z1-110],[0,40,Z1],{'fov':44,'shake':0.2}),(0.45,[20,30,Z1-110],[0,40,Z1],{'fov':44,'shake':1}),(1,[0,50,Z1-200],[0,44,Z1],{'fov':50,'shake':0})),IN,shake=5)
    caption(135.5,139,'B9','Floor')
    return save(M,A,top,'B9','C')

# =====================================================================
#  D : B7 침수 (170~205) — 차오르는 물, 불꽃, 떠다니는 상자, 다리
# =====================================================================
def set_D():
    M,A,top=newset(); Z1=608; W=224
    top+= corridor(M,0,Z1,W=W,H=112,wall='w_conc',floor='f_conc',ceil='c_dark')+end_wall(M,0,W=W,H=112,wall='w_conc',facing=1,door='door',label=7)+end_wall(M,Z1,W=W,H=112,wall='w_conc')
    top+= pipe_run(M,104,96,0,Z1,col='pipe_b',r=5)+pipe_run(M,-104,90,0,Z1,col='pipe',r=4)+pipe_run(M,60,106,0,Z1,col='steel_d',r=3)+[M.cube('back_dark',[-40,0,-70],[40,90,-10],'black')]
    top+= ceiling_lamps(M,0,Z1,W=W,H=112,col='lamp_c')+locker_row(M,-112,60,4,side=1)+console(M,80,60,screen='scr_r')
    # 끝: 높은 발판 + 사다리 + 통로 문(위)
    top+= [M.cube('plat',[-112,0,Z1-70],[112,44,Z1],'conc_d'), M.cube('plat_e',[-112,44,Z1-72],[112,47,Z1-66],'hazard'), M.cube('plat_door',[-32,44,Z1-1.6],[32,104,Z1],'dark',north='door')]
    top+= big_label(M,0,106,Z1-0.4,6,w=40)+[M.cube('plat_lad',[70,0,Z1-73],[86,48,Z1-72],'ladder')]
    # 터진 배관: 물줄기 (깜박이는 상자들)
    for i,(x,y,z) in enumerate([(100,90,150),(-100,84,300),(100,90,430)]):
        sx=-1 if x>0 else 1
        jet=M.group(f'jet{i}',[x,y,z],[M.cube('jet',[min(x,x+sx*60),y-40,z-4],[max(x,x+sx*60),y,z+4],'wat_l'), M.cube('jet2',[min(x+sx*40,x+sx*80),0,z-6],[max(x+sx*40,x+sx*80),y-36,z+6],'wat_l')]); top.append(jet)
        vis(A,jet,[(172+i*1.5,L)]); flicker(A,jet,172+i*1.5,L,0.18); cue(172+i*1.5,'burst')
    cue(172,'water')
    WT=lambda t: 0.5+21*min(1,max(0,(t-173)/22))
    water=M.group('water',[0,0,0],[M.cube('water',[-112,0,0],[112,1,Z1-70],'water')]); top.append(water)
    A.add(water,'scale',[(0,(1,0.01,1)),(173,(1,0.5,1))]+[(t,(1,WT(t),1)) for t in range(175,206,2)])
    # 떠다니는 상자들
    floats=[(-70,190,0.0),(-30,380,2.0),(50,455,0.6),(0,505,0.9),(80,250,1.4)]
    fl=[]
    for i,(x,z,ph) in enumerate(floats):
        g=M.group(f'fl{i}',[x,0,z],[crate(M,x,z,s=34,y=-22,tex=['crate_a','crate_b','crate_c'][i%3],name='fcrate')]); top.append(g); fl.append(g)
        A.add(g,'position',[(0,(0,22,0))]+[(t,(-6*math.sin(t*0.5+ph),max(22,WT(t)+10+2.5*math.sin(t*1.7+ph)),5*math.cos(t*0.4+ph))) for t in [173+k*0.5 for k in range(66)]],'catmullrom')
        A.add(g,'rotation',[(173+k,(4*math.sin(k+ph),k*3,4*math.cos(k*0.8+ph))) for k in range(33)],'catmullrom')
    # 불꽃 튀는 조작판
    for k in range(14): puff(M,A,top,80,40,60,176+k*1.9,0.5,5,'spark',16,14,1.6,seed=k); 
    cue(176,'spark'); cue(184,'spark'); cue(192.3,'spark')
    mo=MOP(M,A,top,0,-40,180)
    mo.go(170.5,172.2,0,40,per=0.6); mo.headturn(172.4,174.4,ry=50)
    mo.go(175,186,-20,250,per=1.0,amp=20); cue(175,'wade')
    A.add(mo.part('arm_left'),'rotation',[(178,(0,0,0)),(179,(-170,0,0)),(193,(-170,0,0)),(193.6,(0,0,0))])       # (왼팔은 이미 없음 — 자세만)
    # 다리 덮개 둘이 떠내려감 (186, 187.5) → 불꽃에 오른다리가 떨어짐 (192.5)
    for k,(nm,t,dx) in enumerate((('leg_left_armor',LOST['leg_left_armor'],40),('leg_right_armor',LOST['leg_right_armor'],-50))):
        g=part_model(M,'legarmor'); out=M.group(f'arm_float{k}',[0,0,0],[g]); top.append(out)
        A.add(out,'position',[(0,(20,0,250)),(t,(20,WT(t)-4,250)),(t+8,(-(-20+dx),WT(t+8)-2,250-60-k*30)),(L,(-(-20+dx),31,160))]); A.add(out,'scale',[(0,(0,0,0)),(t-0.02,(0,0,0)),(t,(1,1,1))]); A.add(g,'rotation',[(t,(0,0,0)),(t+8,(40,200,30))])
    cue(186,'plop'); cue(187.5,'plop')
    mo.go(186,192,10,330,per=1.1,amp=18)
    puff(M,A,top,10,WT(192.5),330,192.5,0.7,10,'spark',18,16,2.2); cue(192.5,'zap')
    lg=part_model(M,'leg'); lo=M.group('leg_float',[0,0,0],[lg]); top.append(lo); A.add(lo,'position',[(0,(-10,0,330)),(192.5,(-10,WT(192.5)-6,330)),(200,(-60,WT(200)-3,290)),(L,(-60,30,280))]); A.add(lo,'scale',[(0,(0,0,0)),(192.48,(0,0,0)),(192.5,(1,1,1))]); A.add(lg,'rotation',[(192.5,(0,0,0)),(200,(80,120,40))])
    A.add(mo.g,'rotation',[(192.5,(0,0,0)),(192.9,(0,0,-22)),(193.8,(0,0,-8)),(194.4,(0,0,0))],'catmullrom')
    # 떠다니는 상자를 딛고 (194~201) 발판으로
    def top_of(i,t): return max(22,WT(t)+10)+12
    hops=[(194.0,195.2,-30,380,1),(196.0,197.2,50,455,2),(198.0,199.2,0,505,3),(200.0,201.4,40,Z1-40,None)]
    for t0,t1,x,z,i in hops:
        mo.hold(t0); x0,y0,z0=mo.cur; y1=top_of(i,t1) if i is not None else 44
        mo.pk.append(((t0+t1)/2,((x0+x)/2,max(y0,y1)+26,(z0+z)/2),'catmullrom')); mo.pk.append((t1,(x,y1,z),'catmullrom')); mo.cur=(x,y1,z); mo.look(t0-0.2,x,z,0.2); mo.yk.append((t1,mo.yaw)); cue(t0,'jump'); cue(t1,'thud')
        if i is not None and t1+0.7<200: mo.hold(t1+0.7)
    mo.turn(201.6,180,0.3); mo.go(202,204,0,Z1-8,y=44,per=0.5); mo.show([(0,204.4)])
    sh('침수층',  'D',170,174.6,cam((0,[0,60,10],[0,40,300],{'fov':46}),(0.5,[20,40,20],[80,80,150],{'fov':40,'shake':1}),(1,[-10,50,10],[0,30,300],{'fov':56})),IN,shake=2)
    sh('물이찬다','D',174.6,179,cam((0,[0,14,90],[0,6,300],{'fov':50}),(1,[0,34,110],[0,14,300],{'fov':44})),IN)
    sh('건넌다',  'D',179,186,cam((0,[-60,40,70],[0,28,0],{'fov':44,'roll':3}),(1,[60,36,80],[0,28,0],{'fov':40,'roll':-3})),IN,follow='m_mv')
    sh('떠내려감','D',186,189.5,cam((0,[30,WT(186)+14,300],[-10,WT(186),250],{'fov':36}),(1,[40,WT(189)+12,290],[-40,WT(189),210],{'fov':30})),IN)
    sh('물속걸음','D',189.5,192.4,cam((0,[0,34,70],[0,30,0],{'fov':38}),(1,[10,36,56],[0,30,0],{'fov':32})),IN,follow='m_mv')
    sh('불꽃',    'D',192.4,194,cam((0,[60,50,280],[10,34,330],{'fov':40}),(0.2,[56,48,284],[10,34,330],{'fov':32,'shake':1}),(1,[66,54,270],[0,30,330],{'fov':46,'roll':-10})),IN,shake=4)
    sh('상자딛기','D',194,201.6,cam((0,[-84,60,326],[0,30,430],{'fov':54,'roll':-6}),(0.5,[-80,64,380],[20,36,480],{'fov':60,'roll':6}),(1,[-70,74,440],[30,44,570],{'fov':50,'roll':0})),IN,shake=1.5)
    sh('발판',    'D',201.6,205,cam((0,[-70,70,Z1-170],[0,60,Z1-20],{'fov':44}),(1,[-40,64,Z1-120],[0,70,Z1],{'fov':36})),IN)
    caption(170.5,174,'B7','Floor')
    return save(M,A,top,'B7','D')

# =====================================================================
#  E : B3 경비실 (240~280) — 잠든 경비 로봇들, 핍이 문을 연다, 내려오는 문을 몸으로 받침
# =====================================================================
def set_E():
    M,A,top=newset(); Z1=600; DZ=520
    top+= corridor(M,0,Z1,W=224,wall='w_sec',floor='f_dark',ceil='c_dark')+end_wall(M,0,W=224,wall='w_sec',facing=1,door='door',label=3)+end_wall(M,Z1,W=224,wall='w_sec',door='door',label=2)
    top+= [M.cube('back_dark',[-40,0,-70],[40,90,-10],'black'), M.cube('fwd_dark',[-40,0,Z1+8],[40,90,Z1+60],'black')]+ceiling_lamps(M,0,Z1,W=224,col='lamp_c')+pipe_run(M,106,88,0,Z1,col='steel_d')+pipe_run(M,-106,88,0,Z1,col='steel_d')
    # 가운데 칸막이 벽 + 무거운 문 자리 (z DZ, 폭 80)
    top+= [M.cube('pw_l',[40,0,DZ],[112,96,DZ+10],'w_sec'), M.cube('pw_r',[-112,0,DZ],[-40,96,DZ+10],'w_sec'), M.cube('pw_t',[-40,78,DZ],[40,96,DZ+10],'steel_d'), M.cube('pw_fl',[38,0,DZ-2],[44,80,DZ+12],'yellow'), M.cube('pw_fr',[-44,0,DZ-2],[-38,80,DZ+12],'yellow'),
           M.cube('haz',[-40,0.3,DZ-26],[40,0.7,DZ-10],'hazard')]
    # 경비 로봇 충전 칸 (좌우 셋씩) + 조작판·화면·무기 선반
    gs=[]
    for i,(sx,z) in enumerate([(1,110),(-1,150),(1,230),(-1,270),(1,350),(-1,390)]):
        x=sx*84; top+= [M.cube('bay',[x-18,0,z-18],[x+18,3,z+18],'yellow'), M.cube('bay_post',[x+sx*20,0,z-3],[x+sx*26,70,z+3],'steel_d'), M.cube('bay_lamp',[x+sx*19,62,z-4],[x+sx*27,68,z+4],'green_l')]
        g=GUARD(M,A,top,x,z,-sx*90,tag=f'q{i}_'); gs.append(g)
        A.add(g.part('head'),'rotation',[(0,(28,0,0)),(259+i*0.3,(28,0,0)),(259.8+i*0.3,(0,0,0))],'catmullrom')
        g.look(260.4+i*0.25,0,DZ-20,0.5); g.go(261.4+i*0.4,266.5+i*0.3,sx*(10+(i%3)*14),DZ-40-(i//2)*26,per=0.6,amp=26)
        A.add(g.part('arm_right'),'rotation',[(262,(0,0,0)),(263,(-85,0,0)),(L,(-85,0,0))])
        cyc(A,g.part('arm_left'),'rotation',271.5+i*0.2,280,(-120,0,0),(-60,0,0),0.5,rest=(0,0,0))
    CX,CZ=-78,470
    top+= console(M,CX,CZ,w=44,screen='scr_r')+console(M,78,470,w=44,screen='scr_b')+shelf_unit(M,78,40,w=50,seed=7)+locker_row(M,-112,30,3,side=1)
    scr2=M.group('scr_ok',[CX,37,CZ+2.4],[M.cube('scr_ok',[CX-19,26.4,CZ+2.2],[CX+19,47.6,CZ+2.9],'dark',north='scr_g')]); top.append(scr2); vis(A,scr2,[(255.5,L)])
    alarms(M,A,top,[(0,200),(0,440)],258.5,L); cue(258.5,'alarm')
    # 무거운 문 (원점 = 아래). 닫힘 → 256~260 올라감 → 262~ 다시 내려옴 → 모프가 받침(264~270) → 쾅(270.6)
    door=actor(M,A,top,M.group('hd_root',[0,0,0],[M.cube('hdoor',[-38,0,0],[38,80,9],'steel_d'), M.cube('hdoor_h',[-38,0,-0.7],[38,9,0],'hazard'), M.cube('hdoor_x',[-30,30,-1],[30,50,0],'red_d'), M.cube('hdoor_lock',[-6,34,-2],[6,46,-1],'red')]),'hd_',0,DZ,0,legs=None)
    door.go(256,260,0,DZ,y=72,walk=False,face=False); door.go(262,264.2,0,DZ,y=27,walk=False,face=False); door.go(264.2,268,0,DZ,y=20,walk=False,face=False); door.go(268,270.4,0,DZ,y=12,walk=False,face=False); door.go(270.4,270.7,0,DZ,y=0,walk=False,face=False)
    cue(256,'rumble'); cue(262,'rumble'); cue(264.2,'clang'); cue(268,'crunch'); cue(270.6,'slam')
    for k in range(4): cyc(A,door.out,'rotation',271.4+k*1.6,271.9+k*1.6,(0,0,0.8),(0,0,-0.8),0.12,rest=(0,0,0)); cue(271.4+k*1.6,'thud')
    mo=MOP(M,A,top,0,-40,180)
    mo.hop(240.6,246.5,-6,430,h=5,n=10); cue(240.6,'tiptoe'); mo.headturn(242,245,ry=60)
    mo.hop(246.6,248.6,0,DZ-22,h=5,n=3); A.add(mo.part('arm_right'),'rotation',[(248.8,(0,0,0)),(249.4,(-80,0,0)),(250.6,(-80,0,0)),(251.2,(0,0,0))]); mo.look(251.4,CX,CZ,0.4)
    # 핍이 내려와 조작판으로
    pp=PIP(M,A,top,0,DZ-30,90); pp.show([(248,L)]); pp.at(248,-8,DZ-30,90,y=30)
    pp.hop(248,248.8,-24,DZ-34,h=8,n=1); pp.go(249,251.6,CX+6,CZ-18,per=0.22,amp=40); pp.hop(251.8,252.8,CX,CZ-4,h=20,n=1)
    pp.pk[-1]=(252.8,(CX,27.4,CZ-4),'catmullrom'); pp.cur=(CX,27.4,CZ-4)
    A.add(pp.part('arm_left'),'rotation',[(253,(0,0,0)),(253.5,(-90,0,0)),(256.5,(-90,0,0)),(257,(0,0,0))]); cyc(A,pp.part('lamp'),'scale',253.4,255.6,(1,1,1),(2.2,2.2,2.2),0.3,rest=(1,1,1)); cue(253.4,'beep'); cue(255.5,'ok')
    pp.hop(260.6,261.8,CX+16,CZ-20,h=10,n=1); pp.go(262,265.8,-10,DZ-24,per=0.2,amp=40); pp.go(266.2,267.6,0,DZ+40,per=0.2,amp=40); pp.look(268,0,DZ,0.2)
    cyc(A,pp.g,'position',268.4,270.2,(0,0,0),(0,3,0),0.3,rest=(0,0,0))
    # 모프가 문을 받침
    mo.hop(262.4,264.0,0,DZ+4,h=5,n=2); mo.turn(264,180,0.1)
    A.add(mo.part('arm_right'),'rotation',[(263.8,(0,0,0)),(264.2,(-175,0,0)),(268,(-175,0,0)),(268.4,(-90,0,0)),(270,(-90,0,0))])
    sh_=mo.part('shell'); A.add(sh_,'scale',[(0,(1,1,1)),(264.2,(1,1,1)),(267.8,(1.12,0.72,1.12)),(268,(0,0,0))])
    A.add(mo.part('body'),'position',[(264.2,(0,0,0)),(267.8,(0,-5,0)),(268.2,(0,0,0))])
    fall(M,A,top,part_model(M,'shell'),LOST['shell'],0,14,DZ+2,-30,DZ-30,dur=0.9); puff(M,A,top,0,18,DZ+4,268,0.8,10,'spark',20,14,2.4); cue(268.1,'snap')
    A.add(mo.g,'rotation',[(268,(0,0,0)),(268.8,(80,0,0)),(L,(80,0,0))],'catmullrom'); mo.go(268.2,270.2,0,DZ+34,walk=False,face=False,y=3)
    pp.go(271.5,273,8,DZ+48,per=0.2); A.add(pp.part('arm_right'),'rotation',[(273.2,(0,0,0)),(273.6,(-80,0,0)),(280,(-80,0,0))])
    mo.go(274,280,0,Z1-20,walk=False,face=False,y=3); pp.go(274,280,10,Z1-6,per=0.3,face=False); cyc(A,mo.part('arm_right'),'rotation',274,280,(-150,0,0),(-60,0,0),1.0,rest=(-90,0,0)); cue(274,'drag')
    sh('경비실',  'E',240,243,cam((0,[0,14,20],[0,40,300],{'fov':66}),(1,[0,10,60],[0,44,300],{'fov':74})),IN)
    sh('살금살금','E',243,247,cam((0,[70,10,-30],[0,20,40],{'fov':60,'roll':-5}),(1,[-70,12,-20],[0,22,50],{'fov':60,'roll':5})),IN,follow='m_mv')
    sh('잠든눈',  'E',247,248.8,cam((0,[-50,44,300],[-84,40,270],{'fov':30}),(1,[-46,42,296],[-84,40,270],{'fov':24})),IN)
    sh('잠긴문',  'E',248.8,251.6,cam((0,[60,40,DZ-120],[0,30,DZ],{'fov':44}),(1,[40,24,DZ-90],[-30,10,DZ-30],{'fov':38})),IN)
    sh('핍달림',  'E',251.6,253,cam((0,[20,8,-30],[0,6,10],{'fov':60}),(1,[14,10,-24],[0,8,10],{'fov':50})),IN,follow='p_mv',shake=1)
    sh('접속',    'E',253,256,cam((0,[CX+40,40,CZ-50],[CX,32,CZ],{'fov':36}),(1,[CX+26,38,CZ-34],[CX,34,CZ+2],{'fov':28})),IN)
    sh('문열림',  'E',256,258.5,cam((0,[0,20,DZ-110],[0,30,DZ],{'fov':44}),(1,[0,14,DZ-80],[0,44,DZ],{'fov':50})),IN,shake=1)
    sh('깨어남',  'E',258.5,262,cam((0,[0,40,60],[0,40,400],{'fov':50}),(0.5,[30,40,160],[84,40,230],{'fov':36,'shake':1}),(1,[0,44,120],[0,40,400],{'fov':60})),IN,shake=2)
    sh('문내려옴','E',262,264.4,cam((0,[50,16,DZ-90],[0,30,DZ],{'fov':46,'roll':-6}),(1,[30,12,DZ-60],[0,26,DZ],{'fov':40,'roll':0})),IN,shake=2)
    sh('받친다',  'E',264.4,268,cam((0,[40,14,DZ+80],[0,22,DZ],{'fov':44}),(0.6,[20,12,DZ+60],[0,22,DZ],{'fov':36,'shake':0.6}),(1,[10,12,DZ+50],[0,20,DZ],{'fov':30,'shake':1})),IN,shake=2.5)
    sh('찌그러짐','E',268,271,cam((0,[-40,20,DZ+70],[0,16,DZ+10],{'fov':40}),(0.3,[-36,16,DZ+64],[0,10,DZ+20],{'fov':46,'shake':1}),(0.85,[-30,14,DZ+80],[0,20,DZ],{'fov':40,'shake':0.3}),(0.9,[-30,14,DZ+80],[0,20,DZ],{'fov':40,'shake':1}),(1,[-30,14,DZ+80],[0,20,DZ],{'fov':40,'shake':0.6})),IN,shake=5)
    sh('두드림',  'E',271,274,cam((0,[0,30,DZ-140],[0,40,DZ],{'fov':40}),(1,[0,30,DZ-110],[0,40,DZ],{'fov':34})),IN,shake=2)
    sh('끌고간다','E',274,280,cam((0,[50,10,DZ+50],[4,6,DZ+44],{'fov':40}),(1,[-50,30,DZ+24],[4,6,Z1-20],{'fov':46})),IN)
    caption(240.5,244,'B3','Floor')
    return save(M,A,top,'B3','E')

# =====================================================================
#  F : B1 환기구 (280~315) — 기어감, 경비 로봇의 손, 손잡이, 큰 환풍기
# =====================================================================
def set_F():
    M,A,top=newset(); Z1=560; W=72; H=56
    k=[]
    for i,z in enumerate(range(0,Z1,64)):
        wt='w_duct'
        k+= [M.cube('dL',[W/2,0,z],[W/2+6,H,z+64],wt), M.cube('dR',[-W/2-6,0,z],[-W/2,H,z+64],wt), M.cube('dF',[-W/2,-6,z],[W/2,0,z+64],'f_grate'), M.cube('dC',[-W/2,H,z],[W/2,H+6,z+64],wt)]
        k+= [M.cube('rib',[W/2-1.6,0,z],[W/2,H,z+3],'steel_d'), M.cube('rib',[-W/2,0,z],[-W/2+1.6,H,z+3],'steel_d'), M.cube('ribt',[-W/2,H-1.6,z],[W/2,H,z+3],'steel_d')]
        if i%2: k.append(M.cube('slat',[-14,H-0.5,z+20],[14,H-0.1,z+44],'lamp_c')); k.append(M.cube('slat_f',[-12,0.1,z+22],[12,0.35,z+42],'steel'))
    top+= k
    # 뒤쪽 끝(z 0): 큰 환풍기 + 그 뒤 어둠 / 앞쪽 끝(z Z1): 밝은 출구 + 사다리
    fan=M.group('fan',[0,H/2,14],[M.cube('fb',[-26,H/2-4,12],[26,H/2+4,16],'steel_d'), M.cube('fb2',[-4,H/2-26,12],[4,H/2+26,16],'steel_d'), M.cube('fhub',[-6,H/2-6,10],[6,H/2+6,18],'dark')]); top.append(fan)
    top+= [M.cube('fan_ring',[-W/2,0,20],[W/2,4,24],'yellow'), M.cube('fan_ring',[-W/2,H-4,20],[W/2,H,24],'yellow'), M.cube('fan_back',[-W/2,0,-30],[W/2,H,0],'black')]
    A.add(fan,'rotation',[(0,(0,0,0)),(303,(0,0,60)),(304,(0,0,400)),(L,(0,0,400+(L-304)*900))]); cue(303.2,'fan')
    top+= [M.cube('exit_glow',[-W/2,0,Z1],[W/2,H+60,Z1+6],'lamp'), M.cube('exit_lad',[-8,0,Z1-3],[8,H,Z1-2],'ladder'), M.cube('exit_hole',[-16,H-0.2,Z1-34],[16,H+6.4,Z1-2],'lamp')]
    top+= big_label(M,0,H-16,Z1-3.4,1,w=30)
    LX,LZ=W/2-2,330       # 손잡이 (왼쪽 벽 = +x)
    top+= [M.cube('lv_box',[LX-3,18,LZ-8],[LX+1.4,36,LZ+8],'yellow'), M.cube('lv_haz',[LX-3.4,14,LZ-10],[LX-3,18,LZ+10],'hazard')]
    lever=M.group('lever',[LX-3,27,LZ],[M.cube('lv_rod',[LX-12,26,LZ-1.2],[LX-3,28.4,LZ+1.2],'steel'), M.cube('lv_knob',[LX-15,24.6,LZ-2.4],[LX-11,29.8,LZ+2.4],'red')]); top.append(lever)
    A.add(lever,'rotation',[(0,(0,0,-35)),(302.6,(0,0,-35)),(303.2,(0,0,40)),(L,(0,0,40))]); cue(303,'lever')
    # 모프: 뼈대만 남아 한 팔로 김 (엎드림). 핍이 앞에서 끈다
    mo=MOP(M,A,top,0,70,180,ride=None); A.add(mo.g,'rotation',[(0,(80,0,0)),(L,(80,0,0))])
    mo.at(280,0,70,180,y=3); mo.go(281,297,0,250,walk=False,face=False,y=3); cyc(A,mo.part('arm_right'),'rotation',281,297,(-160,0,0),(-70,0,0),1.3,rest=(-90,0,0)); cue(281,'drag')
    pp=PIP(M,A,top,6,100,0); pp.go(281,297,6,292,per=0.5,amp=20,face=False); A.add(pp.part('arm_right'),'rotation',[(0,(-80,0,0)),(297.5,(-80,0,0)),(298,(0,0,0))])
    cyc(A,pp.part('lamp'),'scale',280,L,(1,1,1),(1.6,1.6,1.6),0.5,rest=(1,1,1))
    # 경비 로봇이 뒤에서 기어 옴 (292~), 손이 닿으려는 순간
    gd=GUARD(M,A,top,0,-10,180,tag='g_'); gd.show([(291,307.5)]); A.add(gd.g,'rotation',[(0,(78,0,0)),(L,(78,0,0))]); gd.at(291,0,30,180,y=6)
    gd.go(292,302.4,0,196,walk=False,face=False,y=6); cyc(A,gd.part('arm_left'),'rotation',292,300,(-170,0,0),(-80,0,0),0.9,rest=(-150,0,0)); A.add(gd.part('arm_right'),'rotation',[(292,(-90,0,0)),(299,(-90,0,0)),(300.5,(-175,0,0)),(303,(-175,0,0))]); cue(292,'stomp'); cue(296,'stomp'); cue(299,'stomp')
    # 모프가 손잡이를 당김 (300~303.2) → 환풍기 → 경비 로봇이 빨려 감
    mo.go(297.6,300,14,LZ-22,walk=False,face=False,y=3); A.add(mo.part('arm_right'),'rotation',[(300,(-90,0,0)),(301.2,(-150,0,-40)),(302.6,(-150,0,-40)),(303.2,(-100,0,-40)),(305.4,(-100,0,-40))],'catmullrom')
    pp.go(298,299.2,-12,LZ+10,per=0.2); pp.look(299.4,0,150,0.2); cyc(A,pp.g,'rotation',299.6,303,(0,0,8),(0,0,-8),0.25,rest=(0,0,0))
    gd.hold(303.4); gd.go(303.4,305.4,0,40,walk=False,face=False,y=14,interp='catmullrom'); cyc(A,gd.g,'rotation',303.4,305.4,(78,0,30),(78,0,-30),0.3,rest=(78,0,0)); cue(305.4,'crash')
    for k in range(10): puff(M,A,top,((k*29)%50)-25,10+(k%3)*12,300-k*20,303.6+k*0.15,0.9,4,'steam',10,4,2,seed=k)
    puff(M,A,top,0,H/2,30,305.4,1.0,12,'spark',30,10,3)
    # 바람에 오른팔이 손잡이에 걸린 채 뜯겨 나감 (305.5)
    hang=M.group('hangarm',[LX-13,27,LZ],[M.cube('ha',[LX-14,17,LZ-1.3],[LX-12,27,LZ+1.3],'frame'), M.cube('ha2',[LX-15,14.6,LZ-2],[LX-11,17.4,LZ+2],'w')]); top.append(hang); vis(A,hang,[(LOST['arm_right'],L)]); cyc(A,hang,'rotation',305.5,L,(12,0,0),(-12,0,0),0.5,rest=(0,0,0))
    cue(305.5,'snap'); mo.go(303.4,305.4,6,LZ-40,walk=False,face=False,y=3); pp.hold(303.4); pp.go(303.4,305.2,-16,LZ-14,walk=False,face=False)
    A.add(pp.part('arm_left'),'rotation',[(303.3,(0,0,0)),(303.6,(-90,0,60)),(305.4,(-90,0,60)),(305.8,(0,0,0))])
    # 핍이 뒤에서 밀어 출구로
    pp.go(306.4,307.8,4,LZ-62,per=0.2); pp.turn(307.9,180,0.2); A.add(pp.part('arm_left'),'rotation',[(308,(0,0,0)),(308.4,(-85,0,0)),(L,(-85,0,0))]); A.add(pp.part('arm_right'),'rotation',[(308,(0,0,0)),(308.4,(-85,0,0)),(L,(-85,0,0))])
    mo.go(308.6,315,0,Z1-40,walk=False,face=False,y=3); pp.go(308.6,315,2,Z1-76,per=0.3,amp=30,face=False); cue(308.6,'drag')
    sh('환기구',  'F',280,284,cam((0,[0,40,Z1-60],[0,10,100],{'fov':50}),(1,[0,30,Z1-160],[0,10,100],{'fov':40})),IN)
    sh('긴다',    'F',284,289,cam((0,[22,8,60],[0,6,10],{'fov':56,'roll':-8}),(1,[-22,10,50],[0,6,10],{'fov':56,'roll':8})),IN,follow='m_mv')
    sh('일인칭',  'F',289,292,cam((0,[0,13,26],[4,12,60],{'fov':66}),(1,[0,13,26],[6,13,60],{'fov':58})),IN,follow='m_mv',shake=1.2)
    sh('뒤에서',  'F',292,296,cam((0,[0,24,150],[0,18,20],{'fov':40}),(1,[0,24,150],[0,18,20],{'fov':28})),IN,shake=1.5)
    sh('손이온다','F',296,300,cam((0,[20,10,-70],[0,8,10],{'fov':60,'roll':10}),(1,[-10,8,-50],[0,8,0],{'fov':50,'roll':-4})),IN,follow='m_mv',shake=2)
    sh('손잡이',  'F',300,303.4,cam((0,[-26,30,LZ-60],[LX-10,26,LZ],{'fov':40}),(0.8,[-20,28,LZ-40],[LX-10,26,LZ],{'fov':26,'shake':0.3}),(1,[-20,28,LZ-40],[LX-10,24,LZ],{'fov':30,'shake':1})),IN,shake=3)
    sh('환풍기',  'F',303.4,306,cam((0,[0,28,260],[0,24,20],{'fov':44,'roll':0}),(0.5,[4,28,230],[0,24,20],{'fov':58,'roll':14}),(1,[-4,28,210],[0,24,20],{'fov':66,'roll':-14})),IN,shake=5)
    sh('남은팔',  'F',306,308.6,cam((0,[-20,26,LZ-40],[LX-13,22,LZ],{'fov':30}),(1,[-10,20,LZ-70],[4,6,LZ-50],{'fov':40})),IN,shake=1)
    sh('민다',    'F',308.6,315,cam((0,[20,10,-60],[0,8,20],{'fov':50}),(1,[0,24,-80],[0,20,80],{'fov':40})),IN,follow='m_mv')
    caption(280.5,284,'B1','Floor')
    return save(M,A,top,'B1','F')

# =====================================================================
#  U : 지상 (315~420) — 뚜껑, 새벽, 꺼지는 눈, 고물 더미, 다시 맞추기, 해 쪽으로
# =====================================================================
def set_U():
    M,A,top=newset()
    top+= field(M,R=640)+facility(M,-620,480)
    for i,(x,z,h) in enumerate([(-420,260,90),(-520,80,110),(-360,-120,80),(430,220,100),(520,20,120),(380,-200,90),(-600,420,100),(600,400,110),(-250,430,84),(260,440,92),(-620,-260,96),(640,-300,104)]): top+= tree(M,x,z,h,seed=i)
    JX,JZ=-190,90; MX,MZ=40,-70
    top+= junk_pile(M,JX,JZ,r_=74,n=70)+tuft(M,-600,600,-600,480,260,seed=4,avoid=[(0,0,50,50),(JX,JZ,80,70),(MX,MZ,40,40)])
    top+= [M.cube('path',[-10,0.2,-640],[10,0.6,-40],'dirt'), M.cube('rock',[150,0,-40],[176,14,-18],'conc'), M.cube('rock',[160,14,-36],[174,22,-24],'conc_d'), M.cube('rock',[-90,0,-200],[-70,10,-184],'conc')]
    hk,lid=hatch(M,'h_',0,0); top+= hk; top.append(lid); A.add(lid,'rotation',[(0,(0,0,0)),(317.5,(0,0,0)),(319.5,(-104,0,0)),(L,(-104,0,0))],'catmullrom'); cue(317.5,'creak'); cue(319.5,'thud')
    # 해 (멀리 +z 지평선에서 떠오름) + 구름
    sun=M.group('sun',[300,0,3000],[M.cube('sun',[60,-240,3000],[540,240,3010],'sun'), M.cube('sun_c',[140,-160,2996],[460,160,3000],'sun_c')]); top.append(sun)
    A.add(sun,'position',[(0,(0,-400,0)),(330,(0,-300,0)),(365,(0,-60,0)),(400,(0,420,0)),(L,(0,520,0))])
    for i,(x,y,z,w) in enumerate([(-900,520,2600,300),(500,640,2700,360),(1300,460,2500,260),(-200,760,2800,420),(-1500,620,2700,300)]):
        g=M.group(f'cloud{i}',[x,y,z],[M.cube('cloud',[x-w/2,y,z],[x+w/2,y+50,z+40],'cloud'), M.cube('cloud',[x-w/4,y+40,z],[x+w/3,y+86,z+40],'cloud')]); top.append(g); A.add(g,'position',[(0,(0,0,0)),(365,(-40,0,0)),(400,(-400-i*60,0,0)),(L,(-440-i*60,0,0))])
    # 모프: 다시 맞춘 몸(patch). 처음엔 뼈대·한쪽 다리만 → 부품이 붙는 때
    REB=dict(leg_right=373.0, leg_left_armor=376.0, leg_right_armor=376.6, arm_left=380.5, arm_right=385.0, shell=389.5, tank=392.0, headshell=395.0, antenna=397.5)
    mo=MOP(M,A,top,MX,MZ,200,lost=None,ride=[(410.6,L)],patch=True)
    for part,t in REB.items(): vis(A,mo.part(part),[(t,L)]); cue(t,'attach')
    eye=mo.part('eye'); A.add(eye,'scale',[(0,(1,1,1)),(334,(1,1,1)),(334.3,(0,0,0)),(334.7,(1,1,1)),(336.2,(1,1,1)),(336.4,(0,0,0)),(336.9,(1,1,1)),(338.6,(1,1,1)),(339.4,(0.3,0.3,0.3)),(340,(0,0,0)),(401.6,(0,0,0)),(401.8,(1,1,1)),(402.1,(0,0,0)),(402.5,(1,1,1)),(403,(0,0,0)),(403.3,(1,1,1))],'linear'); cue(340,'powerdown'); cue(401.8,'powerup')
    A.add(mo.g,'rotation',[(0,(-84,0,0)),(404,(-84,0,0)),(406.4,(-30,0,0)),(408,(0,0,0))],'catmullrom')     # 누워 있다가 일어남
    mo.show([(321,L)]); mo.at(321,0,-6,200,y=12); mo.go(321,326,MX*0.5,MZ*0.6,walk=False,face=False,y=4); mo.go(326,330,MX,MZ,walk=False,face=False,y=4); cue(321,'drag')
    mo.go(404,406.4,MX,MZ,walk=False,face=False,y=2); mo.go(406.4,408,MX,MZ,walk=False,face=False,y=0)
    A.add(mo.part('arm_left'),'rotation',[(408.2,(0,0,0)),(408.9,(-80,0,-20)),(410,(-80,0,-20)),(410.6,(0,0,0))],'catmullrom'); A.add(mo.part('head'),'rotation',[(408.2,(0,0,0)),(408.9,(26,0,0)),(410,(26,0,0)),(410.6,(0,0,0))],'catmullrom')
    mo.turn(411.4,180,0.8); mo.go(412.6,L,MX+130,MZ+420,per=1.0,amp=22)
    # 핍
    pp=PIP(M,A,top,0,0,180); pp.show([(319.6,410.6)]); pp.at(319.6,0,-4,180,y=12); cyc(A,pp.part('lamp'),'scale',319.6,L,(1,1,1),(1.6,1.6,1.6),0.6,rest=(1,1,1))
    pp.hop(320,321,-8,-36,h=10,n=1); pp.go(321,326,MX*0.5-10,MZ*0.6-16,per=0.4,face=False); pp.go(326,330,MX-12,MZ-14,per=0.4,face=False); pp.look(330.4,MX,MZ,0.3)
    A.add(pp.part('arm_left'),'rotation',[(321,(-80,0,0)),(330,(-80,0,0)),(330.4,(0,0,0)),(341.5,(0,0,0)),(342,(-80,0,0)),(342.4,(-40,0,0)),(342.8,(-80,0,0)),(343.2,(-40,0,0)),(343.8,(0,0,0))])
    A.add(pp.part('head'),'rotation',[(332,(0,0,0)),(333,(-30,0,0)),(335,(-30,0,0)),(336,(0,0,0)),(345,(0,0,0)),(346,(24,0,0)),(351,(24,0,0)),(352,(0,0,0))],'catmullrom')
    A.add(pp.out,'scale',[(345,(1,1,1)),(346,(1,0.8,1)),(351.6,(1,0.8,1)),(352.2,(1,1,1))])          # 풀썩 앉음
    pp.look(355.6,JX,JZ,0.4); pp.hop(356.4,357.2,MX-12,MZ-14,h=8,n=1); pp.go(357.6,364,JX+60,JZ-30,per=0.22,amp=40); cue(357.6,'patter')
    # 부품 나르기: 고물 더미 → 모프 (끌고 옴)
    order=[('leg',REB['leg_right']),('legarmor',REB['leg_left_armor']),('arm',REB['arm_left']),('arm',REB['arm_right']),('shell',REB['shell']),('tank',REB['tank']),('headshell',REB['headshell']),('antenna',REB['antenna'])]
    t=364.6
    for i,(kind,ta) in enumerate(order):
        tgo=max(t,ta-3.0); px,pz=JX+50+((i*13)%20),JZ-40+((i*7)%24)
        if i: pp.go(t,tgo-0.1,px+6,pz-4,per=0.2,amp=40)
        pm=part_model(M,kind,patch=True); out=M.group(f'carry{i}',[0,0,0],[pm]); top.append(out)
        A.add(out,'position',[(0,(-px,2,pz)),(tgo,(-px,2,pz)),(ta-0.3,(-(MX-10),2,MZ-10)),(ta,(-MX,6,MZ))]); A.add(out,'scale',[(0,(1,1,1)),(ta-0.02,(1,1,1)),(ta,(0,0,0))])
        pp.go(tgo,ta-0.3,MX-16,MZ-16,per=0.22,amp=36); puff(M,A,top,MX,8,MZ,ta,0.5,5,'spark',12,10,1.6,seed=i)
        t=ta+0.2
    pp.look(398.2,MX,MZ,0.3)
    pp.hop(403.6,405.6,MX-20,MZ-22,h=10,n=3); pp.hop(409.6,410.6,MX,MZ,h=34,n=1)
    # 하늘 (샷마다): 새벽 전 → 동틀 녘 → 아침
    PRE=['#0c1230','#2a2e5e','#6a4a70']; DAWN=['#243060','#b0607a','#f6a860']; GOLD=['#4a78c0','#f0b070','#ffe0a0']; DAY=['#5aa0e6','#bfe0ff']
    sh('뚜껑',    'U',315,319.6,cam((0,[60,30,-140],[0,10,0],{'fov':44}),(1,[30,16,-100],[0,14,0],{'fov':34})),PRE,shake=1)
    sh('밖으로',  'U',319.6,326,cam((0,[-70,14,-90],[0,12,-10],{'fov':44}),(1,[-90,40,-150],[20,8,-40],{'fov':40})),PRE)
    sh('새벽',    'U',326,332,cam((0,[MX-80,10,MZ-90],[MX,8,MZ],{'fov':40}),(1,[MX-200,150,MZ-420],[100,60,600],{'fov':50})),DAWN)
    sh('눈꺼짐',  'U',332,341.5,cam((0,[MX-36,12,MZ-30],[MX+4,5,MZ-22],{'fov':30}),(1,[MX-30,10,MZ-34],[MX+6,5,MZ-24],{'fov':22})),DAWN)
    sh('흔든다',  'U',341.5,345,cam((0,[MX+50,14,MZ-70],[MX-6,6,MZ-12],{'fov':36}),(1,[MX+44,12,MZ-60],[MX-6,6,MZ-12],{'fov':30})),DAWN)
    sh('앉는다',  'U',345,352.4,cam((0,[MX-90,16,MZ-150],[MX,10,MZ],{'fov':36}),(1,[MX-140,60,MZ-300],[MX+40,40,300],{'fov':40})),DAWN)
    sh('고물더미','U',352.4,357.6,cam((0,[MX+20,12,MZ-50],[MX-12,8,MZ-14],{'fov':30}),(0.45,[MX+20,12,MZ-50],[MX-12,8,MZ-14],{'fov':30}),(0.6,[MX+30,20,MZ-70],[JX,20,JZ],{'fov':40,'roll':-8}),(1,[MX+30,24,MZ-80],[JX,24,JZ],{'fov':30,'roll':0})),DAWN)
    sh('달려감',  'U',357.6,364.6,cam((0,[30,8,-40],[0,6,10],{'fov':58,'roll':6}),(1,[-30,10,-36],[0,6,10],{'fov':58,'roll':-6})),GOLD,follow='p_mv',shake=1.2)
    sh('끌고온다','U',364.6,376,cam((0,[JX+140,30,JZ-200],[JX+90,6,JZ-40],{'fov':40}),(0.5,[MX-150,40,MZ-160],[MX-40,6,MZ-30],{'fov':40}),(1,[MX-90,24,MZ-100],[MX,8,MZ],{'fov':36})),GOLD)
    sh('맞춘다',  'U',376,390,orbit((MX,MZ),110,34,-150,20,(MX,8,MZ),n=8,r1=80,h1=26),GOLD)
    sh('해가뜬다','U',390,398.4,cam((0,[MX-60,8,MZ-110],[MX+40,60,600],{'fov':50}),(1,[MX-30,10,MZ-80],[MX+60,150,600],{'fov':44})),GOLD)
    sh('기다림',  'U',398.4,401.6,cam((0,[MX+56,14,MZ-56],[MX-4,7,MZ-10],{'fov':30}),(1,[MX+46,12,MZ-46],[MX-4,7,MZ-10],{'fov':24})),DAY)
    sh('눈뜸',    'U',401.6,404,cam((0,[MX-30,30,MZ-46],[MX+2,6,MZ-24],{'fov':30}),(1,[MX-24,26,MZ-40],[MX+2,6,MZ-24],{'fov':22})),DAY,shake=0.6)
    sh('일어남',  'U',404,411.4,orbit((MX,MZ),90,26,-40,60,(MX,20,MZ),n=6,r1=74,h1=36),DAY)
    sh('함께',    'U',411.4,420,cam((0,[MX-20,24,MZ-70],[MX,24,MZ+40],{'fov':40}),(0.4,[MX-10,30,MZ-90],[MX+10,30,MZ+200],{'fov':44}),(1,[MX-80,200,MZ-300],[MX+200,160,1200],{'fov':50})),DAY)
    caption(319.8,323,'지상','Floor'); caption(413.5,419.6,'13층 아래','Title')
    cue(326,'birds'); cue(398.4,'birds')
    return save(M,A,top,'지상','U')

SETS=dict(A=set_A,H=set_H,B=set_B,C=set_C,D=set_D,E=set_E,F=set_F,U=set_U)
if __name__=='__main__':
    want=sys.argv[1] if len(sys.argv)>1 else 'all'; info={}
    for k,f in SETS.items():
        if want!='all' and k not in want:
            _orig=Model.save; Model.save=lambda *a,**kw: None
            try: info[k]=f()
            finally: Model.save=_orig
        else: info[k]=f()
    for k in info: info[k].setdefault('ropes',[])
    json.dump(info,open(f'{OUT}/세트정보.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
    S=[s for s in D.SHOTS if s]; S.sort(key=lambda s:s['t0'])
    for i,s in enumerate(S): s['name']=f"{i:03d}_{s['name'].split('_',1)[1]}"
    bad=[(a['name'],b['name'],round(b['t0']-a['t1'],2)) for a,b in zip(S,S[1:]) if abs(b['t0']-a['t1'])>0.02]
    json.dump({'shots':S},open(f'{OUT}/샷목록.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
    json.dump({'duration':L,'captions':sorted(D.CAPS,key=lambda c:c['t0']),'cues':sorted(CUES,key=lambda c:c['t'])},open(f'{ROOT}/시간표.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
    print(len(S),'샷',sum(round((s['t1']-s['t0'])*s['fps']) for s in S),'장',S[-1]['t1'],'초 | 이어지지 않는 곳:',bad or '없음', '| 효과음',len(CUES))
