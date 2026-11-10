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
    k={'antenna':[c('pa',[-0.5,0,-0.5],[0.5,4.6,0.5],'joint'), c('pa',[-0.9,4.6,-0.9],[0.9,6.4,0.9],P('chest','pip_l'))],
       'tank':[c('pt',[-4,0,-2.1],[4,9.5,2.1],P('tank','p_or')), c('pt',[-2,9.5,-1.3],[2,10.9,1.3],P('tank_d','rust'))],
       'arm':[c('pm',[-1.8,7,-2.4],[1.8,10.2,2.4],P('teal','p_or')), c('pm',[-1,0,-1.3],[1,7.6,1.3],'frame'), c('pm',[-1.6,0,-2],[1.6,2.4,2],P('w','p_ye'))],
       'legarmor':[c('pl',[-2.6,0,-2.8],[2.6,6,2.8],P('w','p_gr'))],
       'leg':[c('pg',[-1.2,1.5,-1.4],[1.2,8,1.4],'frame'), c('pg',[-2,0,-3.4],[2,1.6,2.4],'frame_d')],
       'headshell':[c('ph',[-4.6,0,-3.4],[4.6,7.4,4.4],P('w','p_ye')), c('ph',[-4.9,5,-4.4],[4.9,7.7,-3.2],P('teal','p_rd'))],
       'shell':[c('ps',[-6,0,-4.4],[6,11.6,4.4],P('w','p_gr')), c('ps',[-6.3,2,-4.7],[6.3,3.6,4.7],P('teal','p_rd'))]}[kind]
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
    sh('닦는모프','A',4,12,cam((0,[-50,22,250],[6,18,120]),(1,[-56,26,292],[6,20,170])),IN)
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
    sh('문앞',    'A',49,52,cam((0,[60,50,Z1-150],[0,30,Z1-10],{'fov':44}),(1,[30,30,Z1-90],[0,30,Z1-10],{'fov':38})),IN)
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
    car=actor(M,A,top,elevator_car(M,'car_'),'car_',0,-14,0,y=lv(4)+90,legs=None)
    car.at(65,0,-14,y=lv(5)+90); car.go(78,91,0,-14,y=lv(11)+90+60,walk=False,face=False); cue(78,'elevator'); cue(88.5,'clang')
    car.at(200,0,-14,y=lv(7)+90); car.go(206,236,0,-14,y=lv(3)+90,walk=False,face=False); cue(206,'elevator')
    cl=find(car.g,'car_root'); 
    # --- 1부: 사다리 (x 66, z h-10) ---
    LX,LZ=66,h-12
    mo=MOP(M,A,top,0,h-26,180); mo.show([(65,99.6),(204,L)])
    mo.at(65,0,h-26,180,y=lv(13)); mo.go(65.5,67,LX,LZ,per=0.5); mo.turn(67,180,0.2)
    mo.go(67.4,89.4,LX,LZ,y=lv(10)+6,walk=False,face=False); cyc(A,mo.part('arm_left'),'rotation',67.4,89.4,(-150,0,0),(-60,0,0),0.7,rest=(0,0,0)); cyc(A,mo.part('arm_right'),'rotation',67.4,89.4,(-60,0,0),(-150,0,0),0.7,rest=(0,0,0))
    cyc(A,mo.part('leg_left'),'rotation',67.4,89.4,(-40,0,0),(10,0,0),0.7,rest=(0,0,0)); cyc(A,mo.part('leg_right'),'rotation',67.4,89.4,(10,0,0),(-40,0,0),0.7,rest=(0,0,0)); cue(67.4,'climb')
    A.add(mo.part('head'),'rotation',[(76,(0,0,0)),(77,(-40,0,0)),(86,(-40,0,0)),(87,(0,0,0))])
    # 더듬이가 엘리베이터 바닥에 스쳐 부러짐 → 옆 문턱으로 뛰어내림
    fall(M,A,top,part_model(M,'antenna'),LOST['antenna'],LX+3,lv(10)+40,LZ,20,-30,dur=2.4,keep=0.2); cue(88,'snap')
    mo.hold(89.4); mo.pk.append((89.9,((LX+0)/2+6,lv(10)+16,h-24),'catmullrom')); mo.pk.append((90.5,(0,lv(10),h-22),'catmullrom')); mo.cur=(0,lv(10),h-22); mo.yk.append((90.5,180))
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
    sh('아찔',    'H',84,88,cam((0,[20,80,-40],[0,-200,10],{'fov':66,'roll':-12}),(1,[30,60,-30],[0,-300,0],{'fov':74,'roll':8})),IN,follow='m_mv',shake=1)
    sh('스친다',  'H',88,91,cam((0,[-70,lv(10)+70,-50],[LX,lv(10)+40,LZ],{'fov':40}),(0.5,[-60,lv(10)+50,-40],[30,lv(10)+30,LZ],{'fov':46,'shake':1}),(1,[-50,lv(10)+30,-30],[0,lv(10)+20,h-20],{'fov':40})),IN,shake=4)
    sh('떨어지는더듬이','H',91,93,cam((0,[0,lv(10)+10,-30],[20,lv(10)-200,-30],{'fov':60,'roll':15}),(1,[0,lv(10)+10,-30],[20,lv(10)-400,-30],{'fov':72,'roll':-10})),IN)
    sh('B10문',   'H',93,100,cam((0,[-40,lv(10)+70,-60],[0,lv(10)+30,h],{'fov':44}),(1,[-20,lv(10)+34,-20],[0,lv(10)+30,h],{'fov':36})),IN)
    # 샷 2부
    sh('지붕위',  'H',205,208,cam((0,[80,60,-80],[0,24,0],{'fov':50}),(1,[60,40,-70],[0,26,0],{'fov':44})),IN,follow='m_mv')
    sh('드론온다','H',208,213,cam((0,[0,26,-6],[40,140,60],{'fov':64,'roll':6}),(1,[0,26,-6],[-50,90,-40],{'fov':56,'roll':-10})),IN,follow='m_mv',shake=1)
    sh('빙글',    'H',213,221,[dict(k,roll=(-10 if i%2 else 10),fov=56) for i,k in enumerate(orbit((0,0),78,54,0,400,(0,26,0),n=10,r1=64,h1=40))],IN,follow='m_mv',shake=1.2)
    sh('쳐낸다',  'H',221,224,cam((0,[-50,30,-40],[0,34,0],{'fov':44}),(0.2,[-44,30,-36],[10,36,6],{'fov':38,'shake':1}),(1,[-60,60,-50],[60,-80,60],{'fov':56,'roll':12})),IN,follow='m_mv',shake=3)
    sh('층이지나감','H',224,227.2,cam((0,[-40,20,-50],[60,30,h],{'fov':70,'roll':-6}),(1,[-40,24,-50],[60,34,h],{'fov':70,'roll':6})),IN,follow='car_mv',shake=1.4)
    sh('들이받음','H',227.2,230,cam((0,[40,40,-50],[0,30,0],{'fov':44}),(0.3,[30,36,-40],[0,30,0],{'fov':34,'shake':1}),(1,[36,30,-46],[0,26,0],{'fov':40,'roll':-8})),IN,follow='m_mv',shake=5)
    sh('깜박이는눈','H',230,234,cam((0,[6,28,-40],[0,26,0],{'fov':30}),(1,[-10,28,-34],[0,27,0],{'fov':24})),IN,follow='m_mv')
    sh('도착',    'H',234,240,cam((0,[-60,60,-70],[0,20,20],{'fov':50}),(0.4,[-50,40,-60],[0,20,30],{'fov':44,'shake':1}),(1,[-30,30,-30],[0,24,h+10],{'fov':38})),IN,follow='car_mv',shake=2)
    caption(66,69,'B12','Floor'); caption(93.5,97,'B10','Floor'); caption(206,209,'B6','Floor'); caption(218,221,'B5','Floor'); caption(226,229,'B4','Floor'); caption(236.5,239.5,'B3','Floor')
    return save(M,A,top,'통로','H')
