"""《600년 성벽을 붙인 찹쌀죽의 비밀》 블록 장면 → 연재/찹쌀성벽/장면/*.bbmodel + 세트정보.json + 숫자.json
   시간 = 영상 시간 (연재/찹쌀성벽/찹쌀성벽_시간.json 의 T(i)·E(i)).  인물은 장소마다 따로 만들어 보였다 숨겼다 함(위치 움직임 최소)
   세트: A 지금 난징(+불도저 무덤) / B 명나라 공사터 / C 설명 무대(벽돌 틈·석회·녹말·현미경·실험실) / D 옛 다리 보수"""
import sys, os, json, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 찹쌀기구 import *
import 화성_장면 as H   # 공용 도우미(vis·grow·hammer·crank·walk_cycle·P·hill·pine·ground·houses)는 그대로 씀
ROOT='/home/user/youtubeshot/연재/찹쌀성벽'
OUT=f'{ROOT}/장면'; os.makedirs(OUT,exist_ok=True)
TIM=json.load(open(f'{ROOT}/찹쌀성벽_시간.json',encoding='utf-8')); SEG=TIM['segs']; L=round(TIM['duration']+1,2)
T=lambda i: SEG[i]['t0']
E=lambda i: SEG[i]['t0']+SEG[i]['dur']-0.3      # 문단 끝 (다음 문단 시작과 겹치지 않게 0.3초 앞)
vis,grow,hammer,crank,walk_cycle,P,hill,pine,ground,far_ground,houses=H.vis,H.grow,H.hammer,H.crank,H.walk_cycle,H.P,H.hill,H.pine,H.ground,H.far_ground,H.houses
def mk():
    M=BigModel(512); silla_palette(M); pagoda_palette(M); hwaseong_palette(M); chapssal_palette(M); H.world_palette(M); return M
def stir(A,p,t0,t1,per=1.4):
    """두 팔로 솥 젓기 (앞으로 내밀고 좌우로 둥글게)"""
    n=p['name'][:-4]
    for arm,ph in (('arm_left',0),('arm_right',0.0)):
        pts=[(max(0,t0-0.01),(0,0,0))]; t=t0
        while t<t1: a=2*math.pi*(t-t0)/per+ph; pts.append((t,(-60+12*math.sin(a),12*math.cos(a),0))); t+=per/6
        pts.append((t1+0.2,(0,0,0))); A.add(find(p,n+arm),'rotation',pts,'catmullrom')
def arms(A,p,keys):
    n=p['name'][:-4]
    for arm in ('arm_left','arm_right'): A.add(find(p,n+arm),'rotation',keys,'catmullrom')
def nod(A,p,t,deg=10):
    n=p['name'][:-4]; A.add(find(p,n+'head'),'rotation',[(t,(0,0,0)),(t+0.4,(deg,0,0)),(t+0.8,(0,0,0)),(t+1.2,(deg,0,0)),(t+1.6,(0,0,0))],'catmullrom')
def tilt(A,p,t0,t1,deg=14):
    n=p['name'][:-4]; A.add(find(p,n+'head'),'rotation',[(t0,(0,0,0)),(t0+0.5,(0,0,deg)),(t1,(0,0,deg)),(t1+0.3,(0,0,0))],'catmullrom')

def numbers():
    return [
     {'seg':1,'text':'중국 난징 성벽 · 명나라 (14세기)'},
     {'seg':3,'text':'처음 둘레 약 35km'},
     {'seg':5,'text':'접착제 재료: 찹쌀'},
     {'seg':19,'text':'벽돌에 새긴 만든 곳·사람 이름'},
     {'seg':54,'text':'소석회 + 이산화탄소 → 탄산칼슘'},
     {'seg':63,'text':'아밀로펙틴 · 가지가 많은 녹말'},
     {'seg':67,'text':'2010년 · 저장대학교 장빙젠 교수 연구팀'},
     {'seg':72,'text':'찹쌀 모르타르: 알갱이가 작고 촘촘'},
     {'seg':76,'text':'유기물 + 무기물 복합 재료'},
     {'seg':80,'text':'찹쌀을 넣은 쪽이 더 단단하고 물에 강함'},
     {'seg':82,'text':'강도는 평범, 줄어듦을 막는 효과는 흥미로움 (다른 학자 평가)'},
     {'seg':90,'text':'팔백 년 된 다리 보수에 찹쌀 석회 반죽'},
    ]

# =====================================================================
#  A : 지금 난징 — 긴 성벽 + 문루 + 현대 건물 / 불도저와 무덤 (x 1600)
# =====================================================================
def set_A():
    M=mk(); A=Anim(L); top=[far_ground(M)]+ground(M,-1280,1280,-900,900)
    for tag,(x0,x1) in [('wl_',(-1100,-70)),('wr_',(70,1100))]:
        top.append(M.group(tag+'all',[0,0,0],nanjing_wall(M,tag,x0,x1,-30,H=150,T=60)))
    top.append(gate(M,'gate_',0,0,W=140,H=150))
    top.append(M.cube('road',[-1280,-15,-260],[1280,0.5,-200],'asphalt'))
    rnd=random.Random(8)
    for i in range(24):
        side=-1 if i%2 else 1; x=-1150+(i//2)*100+rnd.randint(-10,10); z=side*(330+rnd.randint(0,200))
        if abs(x)<140 and side<0: continue
        h=70+rnd.randint(0,180); w=60+rnd.randint(0,25)
        top.append(M.group(f'b{i}',[x,0,z],[M.cube('bldg',[x-w/2,0,z-w/2],[x+w/2,h,z+w/2],'bldg' if i%3 else 'bldg_d',north='window',south='window')]))
    for i,(x,z) in enumerate([(-300,-120),(-180,-140),(200,-130),(340,-120),(-700,-120),(700,-110)]): top.append(pine(M,f'pine{i}',x,z,60+(i%3)*12))
    # 불도저 vs 무덤 (seg 6)
    X=1700
    top+= ground(M,X-300,X+300,-300,300)
    tomb=mound(M,'tomb',X,40,60); top.append(tomb)
    bd=bulldozer(M,'bd',X+30,-150); top.append(bd)
    # 불도저가 무덤 쪽(+z)으로 밀다가 튕겨 나옴: 위치 z 만 움직임
    A.add(bd,'position',[(0,(0,0,0)),(T(6)+0.3,(0,0,0)),(T(6)+1.6,(0,0,95)),(T(6)+1.9,(0,0,80)),(T(6)+2.4,(0,0,95)),(T(6)+2.7,(0,0,78)),(E(6),(0,0,70))],'catmullrom')
    A.add(bd,'rotation',[(0,(0,90,0))])
    A.bake(top); M.save(f'{OUT}/A_지금.bbmodel',top,[A.json()],name='A'); return {}

# =====================================================================
#  B : 명나라 공사터 — 가마·벽돌 더미·성벽(줄줄이)·가마솥 넷·석회 통·반죽 통, 사람들, 끝 장면(저녁 성벽 위)
# =====================================================================
def set_B():
    M=mk(); A=Anim(L); top=[far_ground(M,'dirt')]+ground(M,-900,900,-700,700,a='dirt',b='dirt_d')
    top.append(hill(M,'mt',-200,700,1200,240,500))
    for i,(x,z) in enumerate([(-700,300),(-620,520),(680,360),(740,560),(-780,-420),(780,-430)]): top.append(pine(M,f'pine{i}',x,z,70))
    rows=nanjing_wall(M,'w_',-320,320,100,H=150,T=60,rows=10); top+= rows
    plan=[0,0,0,0,T(31)-0.5,T(31),T(41)-1,T(92)-3,T(92)-2,T(92)-1.5,T(92)-1.0]
    for j,g in enumerate(rows):
        if plan[j]<=0.02: continue
        grow(A,g,plan[j],plan[j]+1.0)
    # 가마 둘 + 벽돌 더미
    top+= [kiln(M,'kiln1',-460,-160), kiln(M,'kiln2',-360,-300)]
    smoke=M.group('ksmoke',[-460,100,-160],[M.cube('sm',[-470+(j%2)*8,92+j*20,-170],[-445+(j%2)*8,112+j*20,-148],'smoke') for j in range(6)])
    top.append(smoke); A.add(smoke,'position',[(0,(0,0,0))]+[(k*3.0,(0,(k%2)*12,0)) for k in range(1,int(L/3))],'catmullrom')
    for j,(x,z) in enumerate([(-320,-150),(-250,-200),(-150,-60),(60,30)]):
        bk=[M.cube('bp',[x-24+(i%4)*12,(i//8)*7,z-10+((i//4)%2)*12],[x-13+(i%4)*12,(i//8)*7+6,z+(i//4%2)*12],'nbrick') for i in range(24)]
        top.append(M.group(f'bpile{j}',[x,0,z],bk))
    # 이름 벽돌 (작업대 위, 14~18 가까이)
    bench=M.group('bench',[-340,0,-230],[M.cube('bench',[-370,0,-245],[-310,20,-215],'wood_d')]); top.append(bench)
    nb=name_brick(M,'namebrick',-340,20,-230,0.6); top.append(nb)
    # 가마솥 넷 (x 140~320, z -150) + 석회 통 + 반죽 통
    pots=[cauldron(M,f'pot{i}_',140+i*60,-150) for i in range(4)]; top+= pots
    for i,pg in enumerate(pots):
        st=find(pg,f'pot{i}_steam'); A.add(st,'position',[(k*1.0,(0,(k%2)*5,0)) for k in range(int(L))],'catmullrom')
    lt=tub(M,'lime_',230,-70,'lime'); mt=tub(M,'mort_',120,40,'mortar',w=40,d=26); top+= [lt,mt]
    # 29: 석회 통이 회색 반죽으로 (채움 묶음 크기 바꿈: 하얀 것 → 숨기고 회색 채움 보임)
    gray=M.group('lime_gray',[230,2,-70],[M.cube('fill_g',[217,2,-79],[243,10,-61],'mortar')]); top.append(gray)
    vis(A,find(lt,'lime_fill'),[(0,T(30)+0.5)]); vis(A,gray,[(T(30)+0.5,L)])
    # ---- 사람들 (장소마다 따로) ----
    # 가마 앞 (9~22): 아푸(땔감 → 벽돌 보기 → 두드리기), 삼촌
    apu1=P(M,'apu1_','apu',-380,-230,s=0.82); top.append(apu1); vis(A,apu1,[(0,T(23)-0.05)])
    A.add(apu1,'rotation',[(0,(0,0,0)),(T(14),(0,0,0)),(T(14)+0.3,(0,90,0)),(E(19),(0,90,0)),(T(20),(0,0,0))])
    wood=M.group('firewood',[-380,14,-238],[M.cube('fw',[-388,12+i*2.5,-242],[-372,14+i*2.5,-238+0.0],'wood') for i in range(3)]); top.append(wood); vis(A,wood,[(T(12),E(13))])
    A.add(apu1,'position',[(0,(0,0,0)),(T(12),(0,0,-40)),(E(12),(0,0,20)),(E(13),(0,0,20))])
    walk_cycle(A,apu1,T(12),E(12),amp=24,period=0.9); A.add(wood,'position',[(0,(0,0,0)),(T(12),(0,0,-40)),(E(12),(0,0,20)),(E(13),(0,0,20))])
    arms(A,apu1,[(T(12),(-50,0,0)),(E(13),(-50,0,0)),(T(14),(0,0,0)),(T(22),(0,0,0)),(T(22)+0.3,(-80,0,0)),(T(22)+0.6,(-60,0,0)),(T(22)+0.9,(-80,0,0)),(E(22),(0,0,0))])
    tilt(A,apu1,T(15),E(15))
    un=P(M,'un_','uncle',-300,-230); top.append(un); vis(A,un,[(0,T(23)-0.05)])
    A.add(un,'rotation',[(0,(0,-90,0))])
    arms(A,un,[(0,(0,0,0)),(T(20),(0,0,0)),(T(20)+0.4,(-80,0,0)),(T(20)+0.7,(-60,0,0)),(T(20)+1.0,(-80,0,0)),(T(20)+1.3,(-60,0,0)),(E(21),(0,0,0))])
    nod(A,un,T(18))
    # 솥 앞 (23~40): 아푸, 왕 할머니 (둘째 솥), 일꾼 둘(통 섞기)
    apu2=P(M,'apu2_','apu',170,-205,s=0.82); top.append(apu2); vis(A,apu2,[(T(23)-0.05,T(41)-0.05)])
    A.add(apu2,'rotation',[(0,(0,180,0)),(T(34),(0,180,0)),(T(34)+0.01,(0,140,0))])
    tilt(A,apu2,T(32),E(32)); stir(A,apu2,T(37),E(38))
    gm=P(M,'gm_','grandma',215,-190,s=0.9); top.append(gm); vis(A,gm,[(T(23)-0.05,T(41)-0.05)])
    A.add(gm,'rotation',[(0,(0,180,0)),(T(29),(0,180,0)),(T(29)+0.3,(0,90,0)),(E(29),(0,90,0)),(E(29)+0.3,(0,180,0))])
    stir(A,gm,T(25),E(26)); stir(A,gm,T(35),E(36)); stir(A,gm,T(39),E(40))
    arms(A,gm,[(T(29),(0,0,0)),(T(29)+0.5,(-90,0,0)),(E(29),(-90,0,0)),(E(29)+0.3,(0,0,0))])
    A.add(find(gm,'gm_head'),'rotation',[(T(28),(0,0,0)),(T(28)+0.4,(0,-30,0)),(E(28),(0,-30,0)),(E(28)+0.3,(0,0,0))],'catmullrom')
    for j,(x,z,kind) in enumerate([(205,-40,'man'),(255,-40,'man2')]):
        g=P(M,f'mx{j}_',kind,x,z); top.append(g); A.add(g,'rotation',[(0,(0,180 if j==0 else 180,0))]); crank(A,g,T(30),E(30),per=1.0)
    # 석수들 (성벽 앞, 31 벽돌 얹기) — 성벽 바로 앞 z 70
    for j,(x,kind) in enumerate([(-120,'man'),(-40,'uncle'),(60,'man2')]):
        g=P(M,f'ms{j}_',kind,x,70,tool='chisel'); top.append(g); A.add(g,'rotation',[(0,(0,180,0))])
        hammer(A,g,1.0,T(92)-1,per=0.55+j*0.05)
    ob=M.group('onbrick',[-40,58,95],[M.cube('ob',[-60,58,85],[-20,68,105],'nbrick')]); top.append(ob)
    A.add(ob,'position',[(0,(0,0,0)),(T(31),(0,40,-30)),(T(31)+1.2,(0,10,-10)),(E(31),(0,0,0))],'catmullrom'); vis(A,ob,[(T(31),T(41))])
    # ---- 끝 장면 (92~): 저녁, 다 지은 성벽 위 아푸(어른 키), 솥 닦는 할머니
    apu3=P(M,'apu3_','apu',0,125,s=1.0,y=150); top.append(apu3); vis(A,apu3,[(T(92)-0.05,L)])
    A.add(apu3,'rotation',[(0,(0,180,0)),(T(96),(0,180,0)),(T(96)+0.4,(0,0,0)),(E(96),(0,0,0)),(E(96)+0.4,(0,180,0))])
    A.add(find(apu3,'apu3_body'),'rotation',[(0,(0,0,0)),(T(94),(0,0,0)),(T(94)+0.5,(20,0,0)),(E(95),(20,0,0)),(E(95)+0.4,(0,0,0))],'catmullrom')
    A.add(find(apu3,'apu3_arm_right'),'rotation',[(0,(0,0,0)),(T(94),(0,0,0)),(T(94)+0.5,(-70,0,0)),(T(94)+1.5,(-70,30,0)),(T(94)+2.5,(-70,-30,0)),(E(95),(0,0,0))],'catmullrom')
    gm2=P(M,'gm2_','grandma',215,-190,s=0.9); top.append(gm2); vis(A,gm2,[(T(92)-0.05,L)]); A.add(gm2,'rotation',[(0,(0,180,0))])
    stir(A,gm2,T(97),E(97),per=1.0)
    for g in [*pots]: pass
    A.bake(top); M.save(f'{OUT}/B_공사터.bbmodel',top,[A.json()],name='B'); return {}

# =====================================================================
#  C : 설명 무대
#   ① x 0 벽돌 틈(41~47)  ② x -1500 석회(48~58)  ③ x 1500 녹말(59~65)  ④ x 3000 현미경(66~76)  ⑤ x -3000 실험실(77~84)
# =====================================================================
def set_C():
    M=mk(); A=Anim(L); top=[M.cube('st_floor',[-4000,-16,-1400],[4000,0,1400],'floor'),M.cube('st_back',[-4000,0,900],[4000,1100,920],'floor_d')]
    # ① 벽돌 두 장: 울퉁불퉁한 면(작은 혹) → 금(43~44) → 반죽(45) → 빗물 막기(46)
    b1=M.group('cb1',[0,0,0],[M.cube('cb',[-80,0,-30],[80,40,30],'nbrick')]+[M.cube('bump',[-70+i*30,40,-20],[-62+i*30,43,-12+((i%2)*20)],'nbrick_d') for i in range(6)])
    b2=M.group('cb2',[0,43,0],[M.cube('cb',[-80,43,-30],[80,83,30],'nbrick')]); top+= [b1,b2]
    A.add(b2,'position',[(0,(0,0,0)),(T(45),(0,0,0)),(T(45)+0.6,(0,25,0)),(T(45)+1.6,(0,25,0)),(T(45)+2.4,(0,3,0)),(L,(0,3,0))],'catmullrom')
    crack=M.group('crack',[0,62,-30.5],[M.cube('ck',[-10+i*4,48+((i*7)%30),-30.6],[-6+i*4,52+((i*7)%30),-30.3],'dark') for i in range(8)]); top.append(crack)
    vis(A,crack,[(T(44)+0.3,T(45)+0.5)])
    mor=M.group('cmor',[0,40,0],[M.cube('mor',[-80,40,-30],[80,46,30],'mortar')]); top.append(mor); grow(A,mor,T(45)+0.8,T(45)+1.8)
    drops=M.group('drops',[0,150,-60],[M.cube('drop',[-60+i*24,140+(i%3)*12,-62],[-57+i*24,148+(i%3)*12,-58],'water') for i in range(6)]); top.append(drops)
    vis(A,drops,[(T(46),E(46))]); A.add(drops,'position',[(T(46),(0,0,0)),(E(46),(0,-80,0))])
    # ② 석회 (x -1500): 석회암 → 가마(불) → 생석회 덩이 → 물 붓기(김) → 하얀 가루 → 벽돌 사이 → CO2 → 회색 돌 → 금 → 물
    X=-1500
    rock=M.group('limestone',[X-200,0,0],[M.cube('ls',[X-230,0,-25],[X-170,45,25],'rock')]); top.append(rock); vis(A,rock,[(0,T(50)+1.5)])
    kl=kiln(M,'ckiln',X-60,20); top.append(kl); vis(A,kl,[(T(49),T(51))])
    lumps=M.group('quick',[X+80,0,0],[M.cube('ql',[X+60+(i%3)*14,0,-15+(i//3)*14],[X+72+(i%3)*14,10,-3+(i//3)*14],'granite_b') for i in range(6)]); top.append(lumps)
    vis(A,lumps,[(T(50)+1.5,T(53))])
    can=M.group('watercan',[X+80,60,-10],[M.cube('wc',[X+70,50,-20],[X+90,70,0],'steel'),M.cube('wsp',[X+66,60,-12],[X+70,62,-8],'steel')]); top.append(can)
    vis(A,can,[(T(51),E(51))]); A.add(can,'rotation',[(T(51),(0,0,0)),(T(51)+0.6,(0,0,40)),(E(51),(0,0,40))])
    stm=M.group('csteam',[X+80,30,0],[M.cube('st',[X+65+(j%2)*12,15+j*12,-10],[X+80+(j%2)*12,25+j*12,5],'steam') for j in range(5)]); top.append(stm)
    vis(A,stm,[(T(51)+0.5,T(53))]); A.add(stm,'position',[(T(51),(0,0,0)),(T(53),(0,30,0))])
    powder=M.group('powder',[X+80,0,0],[M.cube('pw',[X+55,0,-20],[X+105,12,20],'lime'),M.cube('pw2',[X+65,12,-12],[X+95,18,12],'lime')]); top.append(powder)
    vis(A,powder,[(T(53),T(54)+0.5)])
    # 벽돌 사이 하얀 반죽 → CO2 들어감 → 회색 돌 → 금 → 물
    lb1=M.group('lb1',[X+260,0,0],[M.cube('lb',[X+200,0,-25],[X+320,30,25],'nbrick')]); lb2=M.group('lb2',[X+260,36,0],[M.cube('lb',[X+200,36,-25],[X+320,66,25],'nbrick')])
    lm=M.group('lmor',[X+260,30,0],[M.cube('lm',[X+200,30,-25],[X+320,36,25],'lime')]); lm2=M.group('lmor2',[X+260,30,0],[M.cube('lm',[X+200,30,-25.2],[X+320,36,25.2],'mortar')])
    top+= [lb1,lb2,lm,lm2]
    for g in (lb1,lb2): vis(A,g,[(T(54),L)])
    vis(A,lm,[(T(54),T(55)+0.8)]); vis(A,lm2,[(T(55)+0.8,L)])
    co2=M.group('co2',[X+260,90,-40],[M.cube('co2',[X+210+i*20,80+(i%2)*14,-44],[X+216+i*20,86+(i%2)*14,-38],'smoke') for i in range(6)]); top.append(co2)
    vis(A,co2,[(T(54)+0.5,T(55)+0.8)]); A.add(co2,'position',[(T(54)+0.5,(0,0,0)),(T(55)+0.8,(0,-50,30))])
    lcr=M.group('lcrack',[X+260,33,-26],[M.cube('lc',[X+215+i*12,30.5,-25.6],[X+222+i*12,35.5,-25.3],'dark') for i in range(8)]); top.append(lcr); vis(A,lcr,[(T(57)+0.5,L)])
    ldr=M.group('ldrops',[X+260,120,-40],[M.cube('d',[X+220+i*18,110+(i%3)*10,-42],[X+223+i*18,117+(i%3)*10,-38],'water') for i in range(5)]); top.append(ldr)
    vis(A,ldr,[(T(58),E(58))]); A.add(ldr,'position',[(T(58),(0,0,0)),(E(58),(0,-80,15))])
    # ③ 녹말 (x 1500): 쌀알 → 곧은 사슬(아밀로스, 파랑) / 가지 사슬(아밀로펙틴, 노랑) → 찹쌀떡 늘어남
    X=1500
    grain=M.group('grain',[X,40,0],[M.cube('rg',[X-30,20,-14],[X+30,60,14],'porridge'),M.cube('rg2',[X-22,14,-10],[X+22,66,10],'porridge')]); top.append(grain)
    vis(A,grain,[(0,T(62))])
    ch1=chain(M,'amylose',X-200,120,0,n=14,step=8,col='chain_b'); ch2=chain(M,'amylopectin',X+40,90,0,n=14,step=8,col='chain_a',branch=True)
    top+= [ch1,ch2]; grow(A,ch1,T(62)+0.2,T(62)+1.5,axis='all'); grow(A,ch2,T(62)+2.0,T(62)+3.5,axis='all')
    A.add(ch2,'scale',[(T(63),(1,1,1)),(T(63)+0.5,(1.2,1.2,1.2)),(T(63)+1.0,(1,1,1))],'catmullrom')
    mochi_l=M.group('mochi_l',[X-50,0,-150],[M.cube('ml',[X-80,0,-170],[X-40,30,-130],'porridge')])
    mochi_r=M.group('mochi_r',[X+50,0,-150],[M.cube('mr',[X+40,0,-170],[X+80,30,-130],'porridge')])
    mochi_m=M.group('mochi_m',[X,15,-150],[M.cube('mm',[X-40,8,-160],[X+40,22,-140],'porridge')])
    top+= [mochi_l,mochi_r,mochi_m]
    for g in (mochi_l,mochi_r,mochi_m): vis(A,g,[(T(65),L)])
    A.add(mochi_l,'position',[(T(65),(0,0,0)),(E(65),(40,0,0))]); A.add(mochi_r,'position',[(T(65),(0,0,0)),(E(65),(-40,0,0))])   # 위치 x 반대
    A.add(mochi_m,'scale',[(T(65),(0.5,1,1)),(E(65),(2.0,0.6,1))])
    # ④ 현미경 (x 3000): 연구원·현미경 → 화면 속 알갱이: 큰(보통 석회) vs 작은(찹쌀)
    X=3000
    sci=P(M,'sci_','sci',X-60,-40); top.append(sci); A.add(sci,'rotation',[(0,(0,-60,0))])
    scope=M.group('scope',[X,0,0],[M.cube('ms_base',[X-15,30,-15],[X+15,34,15],'dark'),M.cube('ms_arm',[X+6,34,-4],[X+12,70,4],'dark'),M.cube('ms_tube',[X-4,50,-4],[X+4,74,4],'steel'),
        M.cube('ms_stage',[X-12,44,-12],[X+6,46,12],'dark')]+[M.cube('tbl',[X-40,26,-30],[X+40,30,30],'table')]+[M.cube('leg',[X+a-2,0,z_-2],[X+a+2,26,z_+2],'table') for a in (-36,36) for z_ in (-26,26)])
    top.append(scope); vis(A,scope,[(0,T(71))]); vis(A,sci,[(0,T(71))])
    A.add(find(sci,'sci_body'),'rotation',[(0,(0,0,0)),(T(69),(0,0,0)),(T(69)+0.5,(25,0,0)),(E(70),(25,0,0)),(E(70)+0.3,(0,0,0))],'catmullrom')
    cb=crystals(M,'cr_big',X-70,20,100,big=True); cs=crystals(M,'cr_small',X+70,20,100,big=False)
    top+= [cb,cs]; vis(A,cb,[(T(71),L)]); vis(A,cs,[(T(72),L)])
    lab1=M.group('lab_big',[X-70,8,100],[M.cube('lb',[X-110,6,96],[X-30,12,104],'lime')]); lab2=M.group('lab_small',[X+70,8,100],[M.cube('lb',[X+30,6,96],[X+110,12,104],'porridge')])
    top+= [lab1,lab2]; vis(A,lab1,[(T(71),L)]); vis(A,lab2,[(T(72),L)])
    pick=chain(M,'pick',X+30,90,90,n=10,step=8,col='chain_a',branch=True); top.append(pick); vis(A,pick,[(T(73),E(73))])
    drops2=M.group('drops2',[X,130,80],[M.cube('d',[X-110+i*30,120+(i%3)*8,78],[X-107+i*30,127+(i%3)*8,82],'water') for i in range(8)]); top.append(drops2)
    vis(A,drops2,[(T(75),E(75))]); A.add(drops2,'position',[(T(75),(0,0,0)),(E(75),(0,-60,0))])
    # ⑤ 실험실 (x -3000): 탁자·비커 + 누르는 기계 둘(찹쌀 넣은 / 안 넣은), 연구원
    X=-3000
    top.append(lab_table(M,'labt',X,60))
    pA=press(M,'pa_',X-90,-60); pB=press(M,'pb_',X+90,-60); top+= [pA,pB]
    for p,crk in ((pA,False),(pB,True)):
        nm=p['name'][:-4]
        A.add(find(p,nm+'ram'),'position',[(0,(0,0,0)),(T(80),(0,0,0)),(T(80)+1.2,(0,-30,0)),(E(80),(0,-30,0)),(E(80)+0.3,(0,0,0))],'catmullrom')
        if crk: A.add(find(p,nm+'sample'),'scale',[(0,(1,1,1)),(T(80)+1.0,(1,1,1)),(T(80)+1.4,(1.4,0.45,1.4)),(L,(1.4,0.45,1.4))])
    tagA=M.group('tagA',[X+90,40,-80],[M.cube('ta',[X+80,30,-81],[X+100,40,-80],'porridge')]); top.append(tagA)
    sci2=P(M,'sci2_','sci',X,-130); top.append(sci2)
    A.add(find(sci2,'sci2_head'),'rotation',[(0,(0,0,0)),(T(81),(0,0,0)),(T(81)+0.5,(0,0,12)),(E(84),(0,0,12)),(E(84)+0.3,(0,0,0))],'catmullrom')
    egg=M.group('egg',[X-40,40,60],[M.cube('egg',[X-46,34,54],[X-34,48,66],'porridge')]); top.append(egg); vis(A,egg,[(T(84),L)])
    A.bake(top); M.save(f'{OUT}/C_무대.bbmodel',top,[A.json()],name='C'); return {}

# =====================================================================
#  D : 옛 다리 보수 (85~91) — 돌 무지개다리, 시멘트 자루 vs 석회 반죽 통, 연구원이 반죽을 바름
# =====================================================================
def set_D():
    M=mk(); A=Anim(L); top=[far_ground(M)]+ground(M,-900,900,-700,700)
    top.append(M.cube('river',[-900,-6,-40],[900,1,40],'water'))
    br=arch_bridge(M,'bridge',0,0,L=300,H=70,W=60); top.append(br)
    cracks=M.group('bcracks',[0,40,-30.5],[M.cube('bc',[-120+i*25,28+(i*11)%25,-31],[-114+i*25,32+(i*11)%25,-30.4],'dark') for i in range(10)]); top.append(cracks)
    vis(A,cracks,[(0,T(90)+1.5)])
    patch=M.group('patch',[0,40,-30.6],[M.cube('pt',[-120+i*25,28+(i*11)%25,-31.2],[-114+i*25,32+(i*11)%25,-30.6],'mortar') for i in range(10)]); top.append(patch)
    grow(A,patch,T(90)+0.5,T(90)+2.0,axis='all')
    cem=M.group('cement',[-220,0,-120],[M.cube('bag',[-240,0,-130],[-200,24,-110],'granite_bd'),M.cube('bag2',[-236,24,-128],[-204,30,-112],'granite_bd')]); top.append(cem)
    xm=M.group('xmark',[-220,50,-120],[M.cube('x1',[-235,40,-121],[-205,44,-119],'cloth_r'),M.cube('x2',[-222,28,-121],[-218,56,-119],'cloth_r')]); top.append(xm)
    A.add(xm,'rotation',[(0,(0,0,45))]); vis(A,xm,[(T(88),E(88))])
    lt=tub(M,'dl_',200,-120,'mortar'); top.append(lt)
    sci=P(M,'dsci_','sci',60,-80); top.append(sci); A.add(sci,'rotation',[(0,(0,180,0))]); hammer(A,sci,T(90)+0.3,E(91),per=0.8)
    w=P(M,'dw_','man',-40,-80,tool='chisel'); top.append(w); A.add(w,'rotation',[(0,(0,180,0))]); hammer(A,w,T(90),E(91),per=0.6)
    for i,(x,z) in enumerate([(-500,-250),(520,-260),(-560,260),(580,280)]): top.append(pine(M,f'pine{i}',x,z,70))
    A.bake(top); M.save(f'{OUT}/D_다리.bbmodel',top,[A.json()],name='D'); return {}

if __name__=='__main__':
    info={'A':set_A(),'B':set_B(),'C':set_C(),'D':set_D()}
    for k in info: info[k].setdefault('ropes',[])
    json.dump(info,open(f'{OUT}/세트정보.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
    json.dump(numbers(),open(f'{ROOT}/숫자.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
    for f in sorted(os.listdir(OUT)):
        if f.endswith('.bbmodel'): print(f, len(json.load(open(f'{OUT}/{f}',encoding='utf-8'))['elements']),'cubes')
