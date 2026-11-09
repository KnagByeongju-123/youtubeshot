"""《물로 움직인 900년 전 시계탑의 비밀》 블록 장면 → 연재/물시계탑/장면/*.bbmodel + 세트정보.json + 숫자.json
   세트: A 카이펑 궁궐(시계탑·사람들·밤 장면·해체) / C 설명 무대(물레바퀴·걸쇠, 퍼 올리는 바퀴, 사슬·톱니, 책·모형)"""
import sys, os, json, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 물시계기구 import *
import 화성_장면 as H
ROOT='/home/user/youtubeshot/연재/물시계탑'
OUT=f'{ROOT}/장면'; os.makedirs(OUT,exist_ok=True)
TIM=json.load(open(f'{ROOT}/물시계탑_시간.json',encoding='utf-8')); SEG=TIM['segs']; L=round(TIM['duration']+1,2)
T=lambda i: SEG[i]['t0']
E=lambda i: SEG[i]['t0']+SEG[i]['dur']-0.3
vis,grow,hammer,crank,walk_cycle,P,hill,pine,ground,far_ground=H.vis,H.grow,H.hammer,H.crank,H.walk_cycle,H.P,H.hill,H.pine,H.ground,H.far_ground
def mk():
    M=BigModel(512); silla_palette(M); pagoda_palette(M); hwaseong_palette(M); chapssal_palette(M); clock_palette(M); H.world_palette(M); return M
def arms(A,p,keys):
    n=p['name'][:-4]
    for arm in ('arm_left','arm_right'): A.add(find(p,n+arm),'rotation',keys,'catmullrom')
def nod(A,p,t,deg=10):
    n=p['name'][:-4]; A.add(find(p,n+'head'),'rotation',[(t,(0,0,0)),(t+0.4,(deg,0,0)),(t+0.8,(0,0,0)),(t+1.2,(deg,0,0)),(t+1.6,(0,0,0))],'catmullrom')
def look(A,p,t0,t1,r):
    n=p['name'][:-4]; A.add(find(p,n+'head'),'rotation',[(t0,(0,0,0)),(t0+0.5,r),(t1,r),(t1+0.4,(0,0,0))],'catmullrom')

def step_wheel(A, wheel, esc, chain, step, t0, t1, per=3.0, deg=30, fast=None):
    """물레바퀴를 per 초마다 deg 만큼 '철컥' 돌림 + 걸쇠 지렛대 기울기 + 사슬 한 칸 위로.  fast=(a,b): 그 사이엔 마구 빙글빙글"""
    wk=[(0,(0,0,0))]; lk=[(0,(0,0,0))]; ck=[(0,(0,0,0))]; ch=[(0,(0,0,0))]
    t=t0; ang=0; k=0
    while t<t1:
        if fast and fast[0]<=t<fast[1]:
            n=int((fast[1]-fast[0])/0.25)
            for j in range(n): ang-=40; wk.append((fast[0]+j*0.25+0.25,(0,0,ang)))
            t=fast[1]; continue
        wk+= [(t+per*0.8,(0,0,ang)),(t+per*0.8+0.35,(0,0,ang-deg))]; ang-=deg
        lk+= [(t+per*0.75,(0,0,0)),(t+per*0.8,(0,0,-14)),(t+per*0.95,(0,0,0))]
        ck+= [(t+per*0.78,(0,0,0)),(t+per*0.82,(0,0,30)),(t+per*0.95,(0,0,0))]
        if chain is not None:
            k+=1; off=(k%2)*step; ch+= [(t+per*0.8,(0,(1-k%2)*step,0)),(t+per*0.8+0.35,(0,off,0))]
        t+=per
    if wheel is not None: A.add(wheel,'rotation',wk)
    if wheel is None: wk=None
    if wk is not None: pass
    if esc is not None:
        nm=esc['name'][:-4]; A.add(find(esc,nm+'lever'),'rotation',lk,'catmullrom'); A.add(find(esc,nm+'catch'),'rotation',ck)
    if chain is not None:
        A.add(find(chain,chain['name'][:-4]+'links'),'position',ch)

def numbers():
    return [
     {'seg':1,'text':'1088년 무렵 · 송나라 서울 카이펑'},
     {'seg':2,'text':'높이 약 12m · 3층'},
     {'seg':12,'text':'소송 (1020~1101)'},
     {'seg':15,'text':'한공렴 · 셈과 기계에 밝은 관리'},
     {'seg':32,'text':'혼의 · 10~20톤으로 추정'},
     {'seg':33,'text':'혼상 · 지름 약 1.4m'},
     {'seg':36,'text':'시간 알림 인형 133개'},
     {'seg':39,'text':'물레바퀴 지름 약 3.4m · 물통 36개'},
     {'seg':55,'text':'탈진기 = 움직임을 일정하게 끊어 주는 장치'},
     {'seg':61,'text':'하늘 사다리 · 고리 사슬 약 6m'},
     {'seg':66,'text':'톱니 600개 → 한 칸 2분 24초'},
     {'seg':77,'text':'『신의상법요』 · 1094년 · 그림 47장'},
     {'seg':80,'text':'1127년 · 금나라가 카이펑 점령'},
     {'seg':85,'text':'1950년대 · 왕전둬의 5분의 1 모형'},
    ]

# =====================================================================
#  A : 카이펑 궁궐 — 시계탑(앞 = -z) · 궁궐 건물 · 사람들 · 밤 별 · 해체(80~82)
# =====================================================================
def set_A():
    M=mk(); A=Anim(L); top=[far_ground(M)]+ground(M,-900,900,-700,700,a='granite_b',b='granite_bd')
    import 분황사_장면 as BH   # 법당 모양(붉은 기둥·흰 벽·검은 기와) 재사용
    top+= [BH.hall(M,'hall1',-420,120,200,110), BH.hall(M,'hall2',480,160,180,100)]
    for i,(x,z) in enumerate([(-650,-300),(650,-320),(-700,400),(700,420)]): top.append(pine(M,f'pine{i}',x,z,80))
    tw,parts=clock_tower(M,'ct_',0,100); top.append(tw)
    # 시계탑이 지어지는 과정: 10~17 은 탁자 위 나무 모형만, 18 부터 탑이 아래부터 자라 29 에 완성
    A.add(tw,'scale',[(0,(1,1,1)),(T(9)-0.02,(1,1,1)),(T(9),(0,0,0)),(T(18)+0.28,(0,0,0)),(T(18)+0.3,(1,0.02,1)),(T(28)-0.5,(1,1,1)),(E(81)+0.5,(1,1,1)),(E(81)+0.52,(0,0,0)),(T(89)-0.02,(0,0,0)),(T(89),(1,1,1))])
    model,_=clock_tower(M,'mdl_',-150,-160); top.append(model)
    A.add(model,'scale',[(0,(0.18,0.18,0.18)),(T(18)-0.05,(0.18,0.18,0.18)),(T(18),(0,0,0))])
    A.add(model,'position',[(0,(0,16,0))])
    tbl=M.group('table',[-150,0,-160],[M.cube('tbl',[-190,0,-190],[-110,16,-130],'timber_d')]); top.append(tbl); vis(A,tbl,[(0,T(18))])
    # 바퀴·걸쇠·사슬: 처음부터 끝까지 한 칸씩 (해체 때 멈춤)
    step_wheel(A,parts['wheel'],parts['esc'],parts['chain'],parts['chain_step'],T(28),T(80),per=3.0)
    A.add(parts['globe'],'rotation',[(0,(0,0,0)),(L,(0,360*L/240,0))])
    A.add(find(parts['arm'],'ct_arminner'),'rotation',[(0,(0,0,0)),(L,(0,0,360*L/300))])
    # 지붕 판: 32 와 끝 장면(90~)에 위로 걷힘
    A.add(parts['roof'],'position',[(0,(0,0,0)),(T(32)+0.3,(0,0,0)),(T(32)+1.5,(0,45,0)),(E(32),(0,45,0)),(E(32)+1,(0,0,0)),(T(90),(0,0,0)),(T(90)+0.01,(0,45,0)),(L,(0,45,0))],'catmullrom')
    # 인형들(67~74): 문마다 인형 — 71 종, 72 북·팻말
    jacks=[]
    for i,(dx,dy,dz) in enumerate(parts['doors']):
        j=jack(M,f'jk{i}_',dx,dy,dz-2,s=0.42); top.append(j); jacks.append(j)
        tshow=T(71)+i*0.9 if i<2 else T(72)+(i-2)*0.9
        A.add(j,'position',[(0,(0,0,8)),(tshow,(0,0,8)),(tshow+0.5,(0,0,-4)),(L,(0,0,-4))],'catmullrom')
        A.add(find(j,f'jk{i}_arm'),'rotation',[(0,(0,0,0)),(tshow+0.6,(0,0,0)),(tshow+0.9,(-120,0,0)),(tshow+1.2,(-40,0,0)),(tshow+1.5,(-120,0,0)),(tshow+1.8,(0,0,0))],'catmullrom')
        vis(A,j,[(T(67),T(76))])
    bd=bell_drum(M,'bd',-10,10,20); top.append(bd)
    pl=M.group('plaque',[-10,60,40],[M.cube('pq',[-18,48,38],[-2,64,40],'plaque'),M.cube('pqi',[-15,56,37.8],[-5,58,37.6],'ink')]); top.append(pl); vis(A,pl,[(T(72)+1,T(76))])
    # 해체 (80~82): 지붕·혼의 떠나고, 탑 전체가 기울며 사라짐 → 89 까지 숨김, 끝 장면에 다시
    A.add(tw,'rotation',[(0,(0,0,0)),(T(81),(0,0,0)),(E(81),(0,0,8)),(T(89)-0.02,(0,0,8)),(T(89),(0,0,0))])
    A.add(tw,'position',[(0,(0,0,0)),(T(81),(0,0,0)),(E(81),(0,-60,0)),(T(89)-0.02,(0,-60,0)),(T(89),(0,0,0))])
    smoke=M.group('smoke',[0,200,100],[M.cube('sm',[-60+(j%3)*40,180+j*20,60+(j%2)*30],[-20+(j%3)*40,210+j*20,100+(j%2)*30],'smoke') for j in range(8)]); top.append(smoke)
    vis(A,smoke,[(T(80),E(82))]); A.add(smoke,'position',[(T(80),(0,0,0)),(E(82),(0,60,0))])
    # 별 (밤 장면 89~): 탑 뒤 멀리
    stars=M.group('stars',[0,600,1500],[M.cube('star',[x,y,1500],[x+6,y+6,1506],'star') for x,y in [(random.Random(i).randint(-1400,1400),random.Random(i+99).randint(250,900)) for i in range(70)]]); top.append(stars)
    vis(A,stars,[(T(89),L)])
    # ---- 사람들 ----
    ss=P(M,'ss_','susong',-185,-200); hn=P(M,'hn_','han',-115,-200); top+= [ss,hn]
    for g,yaw in ((ss,(0,-40,0)),(hn,(0,40,0))): A.add(g,'rotation',[(0,yaw)]); vis(A,g,[(0,T(18)-0.05)])
    nod(A,ss,T(15)); arms(A,hn,[(T(16),(0,0,0)),(T(16)+0.5,(-60,0,0)),(E(16),(-60,0,0)),(E(16)+0.3,(0,0,0))])
    # 아밍 물 나르기 (18~27): 우물 → 물탱크 사다리
    am=P(M,'am_','aming',160,-200,s=0.8); top.append(am); vis(A,am,[(T(18)-0.05,T(28)-0.05)])
    A.add(am,'rotation',[(0,(0,180,0)),(T(22),(0,180,0)),(T(22)+0.3,(0,0,0)),(E(25),(0,0,0)),(E(25)+0.3,(0,180,0))])
    A.add(am,'position',[(0,(0,0,0)),(T(19),(0,0,0)),(E(21),(0,0,140)),(T(22),(0,0,140)),(E(27),(0,0,140))])
    walk_cycle(A,am,T(19),E(21),amp=22,period=1.0)
    yoke=M.group('am_yoke',[160,26,-200],[M.cube('yk',[146,26,-201],[174,27.5,-199],'timber'),M.cube('bkt',[144,14,-204],[150,22,-196],'timber_d'),M.cube('bkt',[170,14,-204],[176,22,-196],'timber_d')])
    top.append(yoke); vis(A,yoke,[(T(18)-0.05,T(28)-0.05)]); A.add(yoke,'position',[(0,(0,0,0)),(T(19),(0,0,0)),(E(21),(0,0,140)),(L,(0,0,140))])
    A.add(find(am,'am_body'),'rotation',[(0,(0,0,0)),(T(26),(0,0,0)),(T(26)+0.4,(15,0,0)),(E(26),(15,0,0)),(E(26)+0.3,(0,0,0))],'catmullrom')
    look(A,am,T(25),E(25),(0,0,14))
    hn2=P(M,'hn2_','han',110,-90); top.append(hn2); vis(A,hn2,[(T(23)-0.05,T(25))]); A.add(hn2,'rotation',[(0,(0,90,0))])
    arms(A,hn2,[(T(24),(0,0,0)),(T(24)+0.5,(-70,0,0)),(E(24),(-70,0,0)),(E(24)+0.3,(0,0,0))])
    # 인형 구경 (68~74): 아밍·일꾼들·한공렴 — 탑 앞
    crowd=[]
    for j,(x,z,kind,s) in enumerate([(-30,-120,'aming',0.8),(20,-125,'man',1.0),(-80,-130,'man2',1.0),(60,-135,'uncle',1.0),(-50,-150,'han',1.0)]):
        g=P(M,f'cw{j}_',kind,x,z,s=s); top.append(g); crowd.append(g); A.add(g,'rotation',[(0,(0,180,0))]); vis(A,g,[(T(67),T(75))])
    look(A,crowd[0],T(73),E(73),(-15,0,0))
    A.add(crowd[0],'rotation',[(0,(0,180,0)),(T(73),(0,180,0)),(T(73)+0.3,(0,0,0)),(E(73),(0,0,0)),(E(73)+0.3,(0,180,0))])
    arms(A,crowd[4],[(T(74),(0,0,0)),(T(74)+0.4,(-60,0,0)),(E(74),(-60,0,0)),(E(74)+0.3,(0,0,0))])
    # 끝 장면 (89~): 밤, 아밍(물동이 내려놓고 올려다봄), 소송·한공렴 나란히
    am3=P(M,'am3_','aming',-40,-140,s=0.8); top.append(am3); vis(A,am3,[(T(89),L)]); A.add(am3,'rotation',[(0,(0,180,0))])
    look(A,am3,T(91),L-1,(-30,0,0))
    ss3=P(M,'ss3_','susong',30,-170); hn3=P(M,'hn3_','han',70,-170); top+= [ss3,hn3]
    for g in (ss3,hn3): vis(A,g,[(T(89),L)]); A.add(g,'rotation',[(0,(0,180,0))]); look(A,g,T(94),L-1,(-25,0,0))
    A.bake(top); M.save(f'{OUT}/A_궁궐.bbmodel',top,[A.json()],name='A'); return {}

# =====================================================================
#  C : 설명 무대 — ① x 0 물레바퀴·탱크·물줄기·걸쇠  ② x -1500 퍼 올리는 바퀴  ③ x 1500 사슬·톱니  ④ x 3000 책·모형
# =====================================================================
def set_C():
    M=mk(); A=Anim(L); top=[M.cube('st_floor',[-4000,-16,-1400],[4000,0,1400],'floor'),M.cube('st_back',[-4000,0,900],[4000,1100,920],'floor_d')]
    # ① 큰 물레바퀴 (중심 y 90)
    ww=waterwheel(M,'big_wheel',0,90,0,r=70,n=12,w=14); top.append(ww)
    tk=tank(M,'big_tank',40,175,0,w=40); top.append(tk)
    st=stream(M,'big_stream',12,178,160,0); top.append(st); vis(A,st,[(T(40),L)])
    # 꼭대기 물통에 물이 차오름 (40~41, 51~52): 꼭대기 자리(12시)에 놓인 '차는 물' 상자
    fill=M.group('fill',[0,160,0],[M.cube('fill',[-6,156,-6],[6,166,6],'water2')]); top.append(fill)
    A.add(fill,'scale',[(0,(0,0,0)),(T(40)-0.02,(0,0,0)),(T(40),(1,0.05,1)),(E(40),(1,1,1)),(E(40)+0.3,(0,0,0)),(T(51)-0.02,(0,0,0)),(T(51),(1,0.05,1)),(E(52)-0.5,(1,1,1)),(E(52),(0,0,0))])
    es=escapement(M,'big_esc',-75,150,-10); top.append(es)
    # 바퀴: 41 한 칸 / 48 마구 빙글 / 49~ 한 칸씩
    step_wheel(A,ww,es,None,0,T(41),T(48),per=2.5)
    step_wheel(A,ww,es,None,0,T(48),T(59),per=2.5,fast=(T(48),E(48)))
    arrow=M.group('weight_arrow',[-55,120,-20],[M.cube('ar',[-57,110,-21],[-53,130,-19],'cloth_r'),M.cube('arh',[-60,106,-21],[-50,110,-19],'cloth_r')]); top.append(arrow)
    vis(A,arrow,[(T(51),E(52))])
    # ② 퍼 올리는 바퀴 (x -1500) + 일꾼 둘
    X=-1500
    nr=noria(M,'nr_',X,0); top.append(nr)
    A.add(find(nr,'nr_wheel'),'rotation',[(0,(0,0,0)),(L,(0,0,L*40))])
    top.append(M.cube('nr_pool',[X-60,0,-40],[X+60,6,40],'water2')); top.append(tank(M,'nr_tank',X+60,60,0,w=30))
    for j,(dz,kind) in enumerate([(-30,'man'),(30,'man2')]):
        g=P(M,f'nw{j}_',kind,X-25,dz); top.append(g); A.add(g,'rotation',[(0,(0,-90,0))]); crank(A,g,T(42),E(45),per=1.4)
    # ③ 사슬·톱니 (x 1500)
    X=1500
    ch,stp=chain_loop(M,'ch_',X-60,20,220,0,n=16); top.append(ch)
    step_wheel(A,None,None,ch,stp,T(60),T(67),per=1.5)
    g1=gear(M,'gear1',X+80,110,0,r=60,teeth=60); top.append(g1)
    A.add(g1,'rotation',[(0,(0,0,0)),(T(65),(0,0,0)),(E(66),(0,0,-90))])
    armi=armillary(M,'ca_',X-60,222,0,r=26); top.append(armi)
    A.add(find(armi,'ca_inner'),'rotation',[(0,(0,0,0)),(L,(0,0,L*20))])
    # ④ 책·모형 (x 3000): 책(76~78), 왕전둬 모형(85), 과학박물관 모형(86)
    X=3000
    book=M.group('book',[X-150,0,0],[M.cube('pg_l',[X-210,30,-40],[X-150,33,40],'page'),M.cube('pg_r',[X-150,30,-40],[X-90,33,40],'page'),M.cube('spine',[X-152,30,-40],[X-148,34,40],'book')]+
        [M.cube('tbl',[X-230,0,-60],[X-70,30,60],'timber_d')]+
        [rcube(M,'dw',[X-185+i*0,33,-25],[X-175,33.3,25],'ink',[X-180,33,0],[0,i*30,0]) for i in range(6)]+
        [M.cube('dw2',[X-140+j*8,33,-30],[X-138+j*8,33.3,30],'ink') for j in range(6)])
    top.append(book); grow(A,book,T(77),T(77)+0.8,axis='all')
    mdl,_=clock_tower(M,'wm_',X+120,0); top.append(mdl)
    A.add(mdl,'scale',[(0,(0,0,0)),(T(85)-0.02,(0,0,0)),(T(85),(0.22,0.22,0.22)),(L,(0.22,0.22,0.22))]); A.add(mdl,'position',[(0,(0,30,0))])
    top.append(M.cube('mtable',[X+60,0,-50],[X+180,30,50],'timber_d'))
    sci=P(M,'sci_','sci',X+40,-80); top.append(sci); A.add(sci,'rotation',[(0,(0,-60,0))]); vis(A,sci,[(T(85),L)])
    A.add(find(sci,'sci_head'),'rotation',[(0,(0,0,0)),(T(87),(0,0,0)),(T(87)+0.5,(0,0,14)),(E(88),(0,0,14)),(E(88)+0.3,(0,0,0))],'catmullrom')
    A.bake(top); M.save(f'{OUT}/C_무대.bbmodel',top,[A.json()],name='C'); return {}

if __name__=='__main__':
    info={'A':set_A(),'C':set_C()}
    for k in info: info[k].setdefault('ropes',[])
    json.dump(info,open(f'{OUT}/세트정보.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
    json.dump(numbers(),open(f'{ROOT}/숫자.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
    for f in sorted(os.listdir(OUT)):
        if f.endswith('.bbmodel'): print(f, len(json.load(open(f'{OUT}/{f}',encoding='utf-8'))['elements']),'cubes')
