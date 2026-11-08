"""《10년 걸릴 성을 32개월 만에, 수원 화성의 비밀》 블록 장면 → 연재/수원화성/장면/<세트>_<이름>.bbmodel + 세트정보.json + 숫자.json
   시간 = 영상 시간: 연재/수원화성/수원화성_시간.json 의 문단 시작 T(i)·끝 E(i)
   세트: A 지금 화성 / B 1794 공사터 / C 설명 무대(새 고을·도르래·책) / D 무너진 성과 복원"""
import sys, os, json, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 화성기구 import *
ROOT='/home/user/youtubeshot/연재/수원화성'
OUT=f'{ROOT}/장면'; os.makedirs(OUT,exist_ok=True)
TIM=json.load(open(f'{ROOT}/수원화성_시간.json',encoding='utf-8')); SEG=TIM['segs']; L=round(TIM['duration']+1,2)
T=lambda i: SEG[i]['t0']
E=lambda i: SEG[i]['t0']+SEG[i]['dur']

# ---------------- 공용 ----------------
def world_palette(M):
    M.swatch('grass',(110,160,80),12); M.swatch('grass_d',(96,145,70),12); M.swatch('dirt',(150,115,80),10); M.swatch('dirt_d',(125,95,65),10)
    M.swatch('pine',(55,105,60),12); M.swatch('pine_d',(45,88,50),10); M.swatch('trunk',(110,80,55),6)
    M.swatch('hill',(85,130,75),10); M.swatch('hill_d',(70,112,64),10)
    M.swatch('floor',(226,220,205),5); M.swatch('floor_d',(212,205,190),5)
    M.swatch('asphalt',(90,92,96),6); M.swatch('bldg',(200,200,196),6); M.swatch('bldg_d',(160,162,168),6); M.swatch('window',(110,150,185),8)
    M.swatch('thatch',lambda x,y:(190,160,90) if (x+y)%4 else (150,120,60),6); M.swatch('mudwall',(200,175,140),6)
    M.swatch('book',(60,80,130),5); M.swatch('book_l',(230,225,205),4); M.swatch('page',(240,236,222),3); M.swatch('ink',(40,36,34),3)
    M.swatch('copper',(170,110,60),8); M.swatch('cloth_r',(150,40,40),5); M.swatch('fog',(238,242,246),3)

def ground(M,x0,x1,z0,z1,tile=64,a='grass',b='grass_d',y=0):
    return [M.cube('g',[x,y-16,z],[x+tile,y,z+tile],a if (x//tile+z//tile)%2 else b) for x in range(x0,x1,tile) for z in range(z0,z1,tile)]
def far_ground(M,col='grass'): return M.cube('far_ground',[-5000,-20,-5000],[5000,-15,5000],col)
def pine(M,tag,x,z,h=70):
    k=[M.cube('trunk',[x-3,0,z-3],[x+3,h*0.45,z+3],'trunk')]
    for j,(w,y0) in enumerate([(34,h*0.3),(26,h*0.55),(16,h*0.78)]):
        k.append(M.cube('pine',[x-w/2,y0,z-w/2],[x+w/2,y0+h*0.22,z+w/2],'pine' if j%2 else 'pine_d'))
    return M.group(tag,[x,0,z],k)
def hill(M,tag,x,z,w=500,h=220,d=400):
    k=[]
    for j in range(6):
        f=1-j/6; k.append(M.cube('hill',[x-w*f/2,j*h/6,z-d*f/2],[x+w*f/2,(j+1)*h/6,z+d*f/2],'hill' if j%2 else 'hill_d'))
    return M.group(tag,[x,0,z],k)
def vis(A,g,spans):
    spans=sorted(spans); on0=bool(spans) and spans[0][0]<=0.02
    pts=[(0,(1,1,1) if on0 else (0,0,0))]
    for a,b in spans:
        if a>0.02: pts+= [(a-0.02,(0,0,0)),(a,(1,1,1))]
        pts+= [(b,(1,1,1)),(b+0.02,(0,0,0))]
    A.add(g,'scale',pts)
def grow(A,g,t0,t1,hide_after=None,axis='y'):
    s0=(1,0.02,1) if axis=='y' else (0.02,0.02,0.02)
    pts=[(0,(0,0,0)),(max(0,t0-0.02),(0,0,0)),(t0,s0),(t1,(1,1,1))]
    if hide_after: pts+= [(hide_after,(1,1,1)),(hide_after+0.02,(0,0,0))]
    A.add(g,'scale',pts)
def walk_cycle(A,p,t0,t1,amp=26,period=1.0):
    n=p['name'][:-4]
    parts=[(find(p,n+'leg_left'),1),(find(p,n+'leg_right'),-1),(find(p,n+'arm_left'),-1),(find(p,n+'arm_right'),1)]
    t=t0; s=1; pts=[]
    while t<t1-1e-6: pts.append((t,s)); t+=period/2; s=-s
    for g,sg in parts: A.add(g,'rotation',[(max(0,t0-0.01),(0,0,0))]+[(tt,(sg*ss*amp,0,0)) for tt,ss in pts]+[(t1,(0,0,0))],'catmullrom')
def hammer(A,p,t0,t1,per=0.45):
    n=p['name'][:-4]; ar=find(p,n+'arm_right'); al=find(p,n+'arm_left')
    pts=[(max(0,t0-0.01),(-30,0,0))]; t=t0; up=True
    while t<t1: pts.append((t,(-95 if up else -45,0,0))); up=not up; t+=per/2
    pts.append((t1+0.2,(-30,0,0))); A.add(ar,'rotation',pts,'catmullrom')
    A.add(al,'rotation',[(max(0,t0-0.01),(-30,0,0)),(t1+0.2,(-30,0,0))])
def crank(A,p,t0,t1,per=1.2):
    """두 팔로 얼레 손잡이를 돌림 (팔을 앞에서 원 그리듯)"""
    n=p['name'][:-4]
    for arm,ph in (('arm_left',0),('arm_right',math.pi)):
        pts=[(max(0,t0-0.01),(0,0,0))]; t=t0
        while t<t1: a=2*math.pi*(t-t0)/per+ph; pts.append((t,(-75+25*math.sin(a),0,0))); t+=per/6
        pts.append((t1+0.2,(0,0,0))); A.add(find(p,n+arm),'rotation',pts,'catmullrom')
def P(M,tag,kind,x,z,yaw=0,s=1.0,tool=None,y=0):
    g=person(M,tag,kind,s,tool); move(M,g,x,y,z); g['rotation']=[0,yaw,0]; return g
def spin(A,g,t0,t1,deg_per_s=120,axis=2):
    """묶음을 t0~t1 동안 돌림 (axis 0=x,1=y,2=z)"""
    n=max(2,int((t1-t0)*4)); pts=[(0,(0,0,0)),(t0,(0,0,0))]
    for k in range(1,n+1):
        t=t0+(t1-t0)*k/n; r=[0,0,0]; r[axis]=deg_per_s*(t-t0); pts.append((t,tuple(r)))
    A.add(g,'rotation',pts)
def mk():
    M=BigModel(512); silla_palette(M); pagoda_palette(M); hwaseong_palette(M); world_palette(M); return M
def houses(M,tag,cx,cz,n=8,seed=3):
    rnd=random.Random(seed); out=[]
    for i in range(n):
        x=cx+(i%4)*42-63+rnd.randint(-6,6); z=cz+(i//4)*46-23+rnd.randint(-6,6)
        k=[M.cube('hw',[x-14,0,z-11],[x+14,16,z+11],'mudwall'), M.cube('hr',[x-17,16,z-14],[x+17,22,z+14],'thatch'), M.cube('hr2',[x-11,22,z-9],[x+11,27,z+9],'thatch')]
        out.append(M.group(f'{tag}{i}',[x,0,z],k))
    return out

def numbers():
    return [
     {'seg':2,'text':'수원 화성 · 둘레 약 5.7km'},
     {'seg':3,'text':'처음 계획: 10년'},
     {'seg':4,'text':'실제: 32개월 (1794년 1월 ~ 1796년 가을)'},
     {'seg':11,'text':'1789년 · 사도세자 무덤을 수원 화산으로'},
     {'seg':25,'text':'『화성성역의궤』 · 품삯 기록'},
     {'seg':37,'text':'참고한 책: 『기기도설』'},
     {'seg':46,'text':'움직도르래 1개 → 힘 ½'},
     {'seg':50,'text':'40근의 힘 → 2만 5천 근 (국립중앙박물관 설명)'},
     {'seg':76,'text':'『화성성역의궤』 · 1801년 · 9권'},
     {'seg':81,'text':'공사비 87만여 냥'},
     {'seg':88,'text':'1970년대 중반 · 복원 공사'},
     {'seg':92,'text':'1997년 12월 · 유네스코 세계유산'},
     {'seg':97,'text':'2007년 · 조선왕조 의궤 · 세계기록유산'},
    ]

# =====================================================================
#  A : 지금 화성 (현대 도시 속 성벽·팔달문)
# =====================================================================
def set_A():
    M=mk(); A=Anim(L); top=[far_ground(M)]+ground(M,-1280,1280,-900,900)
    # 성벽: 팔달문(x 0) 양쪽으로 길게, 살짝 꺾임
    top.append(gate(M,'gate_',0,0))
    for tag,(x0,x1,z) in [('wl_',(-900,-66,0)),('wr_',(66,900,0))]:
        top.append(M.group(tag+'all',[0,0,0],hwaseong_wall(M,tag,x0,x1,z-20,H=90,T=40,rows=6)))
    top.append(M.cube('road',[-1280,-15,-260],[1280,0.5,-200],'asphalt'))
    top.append(M.cube('road2',[-40,-15,-900],[40,0.5,-260],'asphalt'))
    rnd=random.Random(5)
    for i in range(26):   # 현대 건물 (성 밖 앞쪽·뒤쪽)
        side=-1 if i%2 else 1; x=-1150+(i//2)*95+rnd.randint(-10,10); z=side*(330+rnd.randint(0,200))
        if abs(x)<120 and side<0: continue
        h=60+rnd.randint(0,160); w=60+rnd.randint(0,20)
        top.append(M.group(f'b{i}',[x,0,z],[M.cube('bldg',[x-w/2,0,z-w/2],[x+w/2,h,z+w/2],'bldg' if i%3 else 'bldg_d',north='window',south='window')]))
    for i,(x,z) in enumerate([(-300,-120),(-180,-140),(200,-130),(340,-120),(-520,140),(520,150),(-700,-120),(700,-110)]):
        top.append(pine(M,f'pine{i}',x,z,60+(i%3)*12))
    A.bake(top); M.save(f'{OUT}/A_지금.bbmodel',top,[A.json()],name='A'); return {}

# =====================================================================
#  B : 1794 공사터 — 성벽이 줄줄이 올라감, 거중기·녹로·유형거, 벽돌 가마, 사람들, 끝 장면(노을·성벽 위)
# =====================================================================
def set_B():
    M=mk(); A=Anim(L); top=[far_ground(M,'dirt')]+ground(M,-900,900,-700,700,a='dirt',b='dirt_d')
    top.append(hill(M,'paldal',-150,650,900,260,500))           # 팔달산 (뒤)
    for i,(x,z) in enumerate([(-700,300),(-600,520),(650,350),(720,560),(-760,-400),(760,-420)]): top.append(pine(M,f'pine{i}',x,z,70))
    # 성벽: x -320 ~ 300, 앞면 z 100, 10줄 + 여장
    rows=hwaseong_wall(M,'w_',-320,300,100,H=100,T=40,rows=10); top+= rows
    plan=[0,0,T(31),T(31)+1.0,T(31)+2.0,T(56),T(56)+1.5,T(64)+0.3,T(64)+2.0,T(65)+0.5,T(67)+0.3]   # 줄마다 나타나는 때
    for j,g in enumerate(rows):
        if plan[j]<=0.02: continue
        grow(A,g,plan[j],plan[j]+1.2)
    # 성문 (팔달문): x 470, 68 에 아래부터 자라남
    gt=gate(M,'gate_',470,120); top.append(gt); grow(A,gt,T(68)+0.2,T(68)+3.0)
    # 69: 비뚤게 앉은 돌 (성벽 위) → 헐어 냄
    bad=stone_block(M,'badstone',-60,80,118,26,12,18); top.append(bad)
    A.add(bad,'rotation',[(0,(0,0,0)),(T(69),(0,0,14)),(T(69)+2.2,(0,0,14)),(T(69)+3.0,(0,0,0))])
    vis(A,bad,[(T(69),T(69)+3.4)])
    # 거중기 (x 0, z 40) : 38 에 큰 돌을 들어 올림, 52~53 막동이 얼레 → 한 뼘
    gj=geojunggi(M,'gj_',0,40); top.append(gj); grow(A,gj,T(32)+0.2,T(32)+3.0)
    low=find(gj,'gj_lower')
    A.add(low,'position',[(0,(0,-14,0)),(T(38)+0.3,(0,-14,0)),(E(38)+0.5,(0,30,0)),(E(41),(0,30,0)),(E(41)+0.1,(0,-14,0)),
                          (T(52),(0,-14,0)),(E(53),(0,-4,0)),(E(54),(0,-4,0))],'catmullrom')
    for nm in ('gj_winchL','gj_winchR'):
        w=find(gj,nm); A.add(w,'rotation',[(0,(0,0,0)),(T(38)+0.3,(0,0,0)),(E(38)+0.5,(0,0,-720)),(T(52),(0,0,-720)),(E(53),(0,0,-1000))])
    # 얼레 돌리는 일꾼 둘 (38) — 얼레 x ±52 옆, 얼레를 봄
    wk=[]
    for j,(sx,kind) in enumerate([(-1,'man'),(1,'man2')]):
        g=P(M,f'wk{j}_',kind,sx*52,10,yaw=0); top.append(g); wk.append(g)
        A.add(g,'rotation',[(0,(0,180,0))])
        crank(A,g,T(38)+0.3,E(38)+0.5)
    vis(A,wk[0],[(T(32),T(52)-0.05),(E(54),T(99))]); vis(A,wk[1],[(T(32),T(99))])
    # 녹로 (x -200, z 30): 57~58 에 돌을 높이 (밧줄: 꼭대기 → 돌)
    nk=noklo(M,'nk_',-200,30,lean=14); top.append(nk); grow(A,nk,T(56)-0.05,T(56)+1.5)
    nst=M.group('nk_stone',[-200,0,10],[M.cube('nst',[-212,0,2],[-188,14,18],'granite_b'),anchor(M,'nk_hook',[-200,14,10])]); top.append(nst)
    vis(A,nst,[(T(56)-0.05,T(63))])
    A.add(nst,'position',[(0,(0,0,0)),(T(58),(0,0,0)),(E(58),(0,60,-8))],'catmullrom')
    A.add(find(nk,'nk_drum_g'),'rotation',[(0,(0,0,0)),(T(58),(0,0,0)),(E(58),(-540,0,0))])
    # 유형거 + 막동이 (61~62): 채석장(z -500) → 성벽 쪽(z -60) 으로 끌고 감 (+z)
    cart=yuhyeonggeo(M,'cart_',-420,-480); top.append(cart)
    cstone=stone_block(M,'cart_stone',-420,16,-480,20,12,16); top.append(cstone)
    for g in (cart,cstone):
        A.add(g,'position',[(0,(0,0,0)),(T(59),(0,0,0)),(T(59)+0.01,(0,0,0)),(E(62)-0.4,(0,0,360))])
    A.add(cart,'rotation',[(0,(0,180,0))]); A.add(cstone,'rotation',[(0,(0,180,0))])
    for nm in ('cart_wheelL','cart_wheelR'): A.add(find(cart,nm),'rotation',[(0,(0,0,0)),(T(59),(0,0,0)),(E(62),(1800,0,0))])
    vis(A,cart,[(T(56),T(63))]); vis(A,cstone,[(T(56),T(63))])
    # 채석장 돌 더미 + 벽돌 가마 (연기)
    for j,(x,z,n_) in enumerate([(-470,-560,60),(-560,-470,40),(-250,-150,36),(200,-120,40),(320,-60,30)]):
        top.append(stone_pile(M,f'pile{j}',x,z,n=n_,r=34,seed=j+3))
    kiln=M.group('kiln',[460,0,-300],[M.cube('kiln',[420,0,-340],[500,50,-260],'clay'),M.cube('kiln_top',[430,50,-330],[490,70,-270],'clay'),M.cube('kiln_door',[445,4,-341],[475,30,-339],'dark')])
    smoke=M.group('smoke',[460,90,-300],[M.cube('sm',[440+(j%2)*10,80+j*22,-320+(j%3)*6],[470+(j%2)*10,104+j*22,-290+(j%3)*6],'smoke') for j in range(6)])
    top+= [kiln,smoke]; A.add(smoke,'position',[(0,(0,0,0))]+[(k*3.0,(0,(k%2)*14,0)) for k in range(1,int(L/3))],'catmullrom')
    # 막동이 (아이 키 0.88) : 19 들어옴 → 21~29 오 서방과 / 38~41 거중기 구경 / 52~54 얼레 / 61~62 유형거 / 70~71 정 / 끝(100~)은 성벽 위
    mk_=P(M,'mk_','makdong',-60,-330,yaw=0,s=0.88); top.append(mk_)
    pos=[(0,(0,0,0)),(T(19),(0,0,0)),(T(19)+3.5,(0,0,120)),(E(29)-0.5,(0,0,120)),                       # 성벽 앞 (z -210)
         (T(30),(30,0,250)),(E(41)-0.5,(30,0,250)),                                                     # 거중기 앞 왼쪽 (x -90? → 위치 x 반대: 실제 x = -60-30 = -90) z -80
         (T(52),(-8,0,340)),(E(54),(-8,0,340)),                                                     # 왼쪽 얼레 자리 (실제 x -52, z 10)
         (T(59),(360,0,-100)),(T(59)+0.01,(360,0,-100)),(E(62)-0.4,(360,0,256)),                       # 유형거 손잡이 앞 (실제 x -420, z -430→-74)
         (T(63),(-10,0,285)),(T(72),(-10,0,285))]                                                    # 성벽 앞 오 서방 곁 (실제 x -30, z -30)
    A.add(mk_,'position',pos)
    walk_cycle(A,mk_,T(19),T(19)+3.5,amp=24,period=0.9); walk_cycle(A,mk_,T(59)+0.3,E(62)-0.4,amp=22,period=1.0)
    A.add(mk_,'rotation',[(0,(0,0,0)),(T(19),(0,180,0)),(E(29)-0.5,(0,180,0)),(T(30),(0,135,0)),(E(41)-0.5,(0,135,0)),(T(52),(0,180,0)),(E(54),(0,180,0)),
                          (T(59),(0,180,0)),(E(62)-0.4,(0,180,0)),(T(63),(0,0,0)),(T(72),(0,0,0))])
    mh=find(mk_,'mk_head')
    A.add(mh,'rotation',[(0,(0,0,0)),(T(23),(0,0,0)),(T(23)+0.4,(-8,0,0)),(E(24),(-8,0,0)),(E(24)+0.3,(0,0,0)),
                         (T(38),(0,0,0)),(T(38)+1,(-25,0,0)),(E(39),(-25,0,0)),(E(39)+0.3,(0,0,0)),(T(54),(0,0,0)),(T(54)+0.4,(12,0,0)),(T(54)+0.8,(0,0,0)),(T(54)+1.2,(12,0,0)),(T(54)+1.6,(0,0,0))],'catmullrom')
    crank(A,mk_,T(52),E(53),per=2.0); hammer(A,mk_,T(70),E(71),per=0.6)
    # 29 언 손 비비기: 두 팔 앞으로 모음
    for arm in ('arm_left','arm_right'): A.add(find(mk_,'mk_'+arm),'rotation',[(T(29),(0,0,0)),(T(29)+0.4,(-60,0,0)),(E(29),(-60,0,0)),(E(29)+0.3,(0,0,0))],'catmullrom')
    # 유형거 끌 때 두 팔 뒤로 (손잡이 잡기)
    for arm in ('arm_left','arm_right'): A.add(find(mk_,'mk_'+arm),'rotation',[(T(59),(0,0,0)),(T(59)+0.3,(-35,0,0)),(E(62),(-35,0,0)),(E(62)+0.2,(0,0,0))])
    # 오 서방 (정·망치): 21~29 막동이 맞이 / 40~41 팔짱→끄덕 / 64~71 성벽 앞 돌 다듬기
    oh=P(M,'oh_','oh',-20,-160,yaw=0,tool='chisel'); top.append(oh)
    A.add(oh,'rotation',[(0,(0,0,0)),(T(30),(0,0,0)),(T(30)+0.01,(0,135,0)),(E(41),(0,135,0)),(E(41)+0.01,(0,0,0))])
    A.add(oh,'position',[(0,(0,0,0)),(T(30),(0,0,0)),(T(30)+0.01,(80,0,90)),(E(41),(80,0,90)),(T(63),(0,0,130)),(T(72),(0,0,130))])   # 거중기 구경: 실제 x -100 z -70 / 성벽 앞: x -20 z -30
    A.add(find(oh,'oh_head'),'rotation',[(0,(0,0,0)),(T(40),(0,0,0)),(T(40)+0.5,(10,0,0)),(T(40)+1.0,(0,0,0)),(T(40)+1.5,(10,0,0)),(T(40)+2.0,(0,0,0))],'catmullrom')
    hammer(A,oh,T(64),E(66)); hammer(A,oh,T(69)+1,E(71),per=0.6)
    for j,x in enumerate((-50,-20)):   # 다듬는 돌 (두 사람 앞)
        ws=stone_block(M,f'work{j}',x,0,-46,18,12,14); top.append(ws); vis(A,ws,[(T(63),T(72))])
    # 정약용 (35~37): 거중기 옆에서 손으로 가리킴
    da=P(M,'da_','dasan',90,-40,yaw=0); top.append(da); vis(A,da,[(T(35)-0.05,E(37))])
    A.add(da,'rotation',[(0,(0,-135,0))])
    A.add(find(da,'da_arm_right'),'rotation',[(0,(0,0,0)),(T(36),(0,0,0)),(T(36)+0.6,(-100,0,-20)),(E(37),(-100,0,-20)),(E(37)+0.3,(0,0,0))],'catmullrom')
    # 일꾼들 (배경) 돌 다듬기
    for j,(x,z) in enumerate([(240,-200),(-300,-260),(120,-300)]):
        g=P(M,f'bg{j}_',['man','man2','man'][j],x,z,yaw=[90,-90,180][j],tool='chisel'); top.append(g); hammer(A,g,0.5,T(99),per=0.5+j*0.06)
    # ---- 끝 장면 (100~): 노을, 성벽 위(y 100)에 막동이(키 1.0)·오 서방, 팔달문(x 470) 쪽을 봄
    for g in (mk_,oh): vis(A,g,[(0,T(99)-0.05)])
    mk2=P(M,'mk2_','makdong',60,124,yaw=0,s=1.0,y=100); top.append(mk2)
    oh2=P(M,'oh2_','oh',100,124,yaw=0,y=100); top.append(oh2)
    for g in (mk2,oh2): vis(A,g,[(T(99)-0.05,L)]); A.add(g,'rotation',[(0,(0,60,0))])
    A.add(find(mk2,'mk2_head'),'rotation',[(0,(0,0,0)),(T(103),(0,0,0)),(T(103)+0.4,(0,30,0)),(E(103),(0,30,0)),(E(103)+0.4,(0,0,0))],'catmullrom')
    A.add(find(oh2,'oh2_head'),'rotation',[(0,(0,0,0)),(T(104),(0,0,0)),(T(104)+0.4,(0,-30,0)),(E(104),(0,-30,0)),(E(104)+0.4,(0,0,0))],'catmullrom')
    # 끝 장면엔 기구·더미 숨김 (다 지은 성)
    for g in [gj,nk]: vis(A,g,[(T(32) if g is gj else T(56)-0.05, T(99)-0.05)])
    ropes_=[['gj_up0','gj_lo0'],['gj_up1','gj_lo1'],['gj_up2','gj_lo2'],['gj_up3','gj_lo3'],['gj_drumL','gj_up0'],['gj_drumR','gj_up3'],['nk_top','nk_hook'],['nk_drum','nk_top']]
    top.append(M.group('ropes',[0,0,0],[M.cube(f'rope_{i}',[-0.7,-0.7,0],[0.7,0.7,1],'rope') for i in range(len(ropes_))]))
    A.bake(top); M.save(f'{OUT}/B_공사터.bbmodel',top,[A.json()],name='B'); return {'ropes':ropes_}

# =====================================================================
#  C : 설명 무대 — ① 새 고을(무덤·고을 옮기기·성·행궁·정약용) x 0  ② 도르래 x -2000  ③ 책 x 2000
# =====================================================================
def set_C():
    M=mk(); A=Anim(L); top=[M.cube('st_floor',[-3000,-16,-1400],[3000,0,1400],'floor'),M.cube('st_back',[-3000,0,900],[3000,1100,920],'floor_d')]
    # ① 새 고을
    top.append(hill(M,'hwasan',-320,250,260,90,220)); md=mound(M,'mound',-320,40,40); top.append(md); grow(A,md,T(11)+0.3,T(11)+1.5,axis='all')
    top.append(hill(M,'paldal',280,300,360,150,260))
    hs=houses(M,'house',-250,-60,8,seed=4)
    for i,h in enumerate(hs):   # 12: 무덤 근처 → 팔달산 아래 (+x 로 480 → 위치 x 는 반대로 -480)
        top.append(h); ta=T(12)+0.3+i*0.25
        A.add(h,'position',[(0,(0,0,0)),(ta,(0,0,0)),(ta+0.4,(-120,25,0)),(ta+0.9,(-480,0,60))],'catmullrom')
    ring=hwaseong_wall(M,'ring_',90,370,-60,H=24,T=10,rows=2,parapet=False)+hwaseong_wall(M,'ring2_',90,370,150,H=24,T=10,rows=2,parapet=False)
    for j,g in enumerate(ring): top.append(g); grow(A,g,T(13)+0.2+j*0.3,T(13)+0.9+j*0.3)
    hg=M.group('haenggung',[300,0,40],[M.cube('hg_base',[255,0,10],[345,6,70],'granite_b'),M.cube('hg_wall',[262,6,18],[338,30,62],'wall_w'),
        M.cube('hg_roof',[250,30,6],[350,38,74],'tile'),M.cube('hg_roof2',[262,38,18],[338,46,62],'tile_d')]+[M.cube('hg_p',[262+i*25,6,15],[266+i*25,30,19],'pillar') for i in range(4)])
    top.append(hg); grow(A,hg,T(14)+0.2,T(14)+1.5)
    da=P(M,'da_','dasan',150,-130,yaw=0,s=1.4); top.append(da); vis(A,da,[(T(15),E(16))])
    scroll=M.group('scroll',[150,22,-150],[M.cube('paper',[140,16,-152],[160,30,-150.5],'page'),M.cube('ink1',[143,25,-152.3],[157,26,-152.1],'ink'),M.cube('ink2',[143,21,-152.3],[153,22,-152.1],'ink')])
    top.append(scroll); vis(A,scroll,[(T(16),E(16))])
    for arm in ('arm_left','arm_right'): A.add(find(da,'da_'+arm),'rotation',[(0,(0,0,0)),(T(16),(-80,0,0)),(E(16),(-80,0,0))])
    # ② 도르래 (x -2000): 왼쪽(-x 쪽이 화면 오른쪽) 고정 도르래, 오른쪽 움직도르래, 뒤에 거중기
    X=-2000
    fr=[M.cube('beam',[X-260,150,-6],[X+60,158,6],'wood')]+[M.cube('leg',[X+x0-4,0,-6],[X+x0+4,150,6],'wood_d') for x0 in (-256,-100,56)]
    top.append(M.group('pframe',[X,0,0],fr))
    # 고정 도르래 데모 (x X+20 쪽): 바퀴, 돌(왼쪽 줄), 당기는 사람(오른쪽 줄)
    f_wh=wheel(M,'f_wheel',X-20,140,0,r=8,w=3,axis='z',col='pulley'); top.append(f_wh)
    f_st=M.group('f_stone',[X-29,0,0],[M.cube('fst',[X-40,0,-10],[X-18,16,10],'granite_b'),anchor(M,'f_st_top',[X-29,16,0])]); top.append(f_st)
    f_man=P(M,'fman_','man',X-11+0,-0,yaw=0); move(M,f_man,10,0,-25); top.append(f_man)
    top+= [anchor(M,'f_wl',[X-28,140,0]),anchor(M,'f_wr',[X-12,140,0])]
    A.add(f_st,'position',[(0,(0,0,0)),(T(44)+0.5,(0,0,0)),(E(44),(0,40,0)),(T(45),(0,0,0))],'catmullrom')
    for arm in ('arm_left','arm_right'): A.add(find(f_man,'fman_'+arm),'rotation',[(0,(-170,0,0)),(T(44)+0.5,(-170,0,0)),(E(44),(-60,0,0)),(T(45),(-170,0,0))],'catmullrom')
    f_hand=anchor(M,'f_hand',[X-1+0,40,-25]); top.append(f_hand)
    # 움직도르래 데모 (x X-180): 들보 고리 → 아래 바퀴(돌과 함께) → 위 바퀴 → 사람
    m_top=wheel(M,'m_wheel_top',X-170,140,0,r=8,w=3,axis='z',col='pulley'); top.append(m_top)
    m_mv=M.group('m_move',[X-200,60,0],[M.cube('mst',[X-212,20,-10],[X-188,36,10],'granite_b'),M.cube('mhook',[X-201,36,-1],[X-199,44,1],'iron')]+[wheel(M,'m_wheel_low',X-200,52,0,r=8,w=3,axis='z',col='pulley')]
                                       +[anchor(M,'m_low_l',[X-208,52,0]),anchor(M,'m_low_r',[X-192,52,0])])
    top.append(m_mv); top+= [anchor(M,'m_beam',[X-208,150,0]),anchor(M,'m_tl',[X-178,140,0]),anchor(M,'m_tr',[X-162,140,0])]
    m_man=P(M,'mman_','man2',X-150,-25,yaw=0); top.append(m_man); top.append(anchor(M,'m_hand',[X-150,40,-25]))
    A.add(m_mv,'position',[(0,(0,0,0)),(T(46),(0,0,0)),(E(46),(0,30,0)),(T(47),(0,0,0))],'catmullrom')
    for arm in ('arm_left','arm_right'): A.add(find(m_man,'mman_'+arm),'rotation',[(0,(-170,0,0)),(T(46),(-170,0,0)),(E(46),(-60,0,0)),(T(47),(-170,0,0))],'catmullrom')
    # 47~51: 거중기 큰 모형 (x X+400)
    gj=geojunggi(M,'gj_',X+400,0); top.append(gj)
    low=find(gj,'gj_lower'); A.add(low,'position',[(0,(0,-14,0)),(T(47),(0,-14,0)),(E(48),(0,30,0)),(T(50),(0,-14,0)),(E(50),(0,30,0))],'catmullrom')
    for nm in ('gj_winchL','gj_winchR'): A.add(find(gj,nm),'rotation',[(0,(0,0,0)),(T(47),(0,0,0)),(E(48),(0,0,-900)),(T(50),(0,0,-900)),(E(50),(0,0,-1800))])
    # ③ 책 (x 2000): 아홉 권 쌓임 → 한 권 펼침(표지 회전) → 펼친 쪽 위에 작은 거중기 그림(종이 판) / 엽전 더미
    BX=2000; books=[]
    for i in range(9):
        b=M.group(f'book{i}',[BX-120,i*7,0],[M.cube('bk',[BX-150,i*7,-22],[BX-90,i*7+6,22],'book',up='book'),M.cube('bkp',[BX-149,i*7+0.5,-21.5],[BX-91,i*7+5.5,21.6],'book_l')])
        top.append(b); books.append(b); grow(A,b,T(75)+0.5+i*0.3,T(75)+0.8+i*0.3,axis='all')
    open_pages=M.group('openbook',[BX+40,0,0],[M.cube('pg_l',[BX-20,0,-30],[BX+40,3,30],'page'),M.cube('pg_r',[BX+40,0,-30],[BX+100,3,30],'page'),
        M.cube('spine',[BX+38,0,-30],[BX+42,4,30],'book')]+
        [M.cube('line',[BX-14,3,-24+j*7],[BX+34,3.2,-23+j*7],'ink') for j in range(7)])
    top.append(open_pages); grow(A,open_pages,T(78)-0.05,T(78)+0.8,axis='all')
    # 펼친 오른쪽 쪽 위 작은 거중기 그림 (먹선 막대)
    drawing=[M.cube('dw',[BX+52,3,-22],[BX+54,3.3,18],'ink'),M.cube('dw',[BX+86,3,-22],[BX+88,3.3,18],'ink'),M.cube('dw',[BX+52,3,16],[BX+88,3.3,18],'ink'),
             M.cube('dw',[BX+62,3,0],[BX+78,3.3,2],'ink'),M.cube('dw',[BX+64,3,-12],[BX+76,3.3,-6],'ink')]
    dg=M.group('drawing',[BX+70,3,0],drawing); top.append(dg); grow(A,dg,T(80),T(80)+1.0,axis='all')
    coins=M.group('coins',[BX+220,0,0],[M.cube('coin',[BX+200+(i%5)*9-(i//5)*3,(i//5)*2,-15+(i%3)*12],[BX+207+(i%5)*9-(i//5)*3,(i//5)*2+2,-8+(i%3)*12],'copper') for i in range(30)])
    top.append(coins); grow(A,coins,T(81),T(81)+1.0,axis='all')
    # 끝: 각 구역 소품은 그 문단에만 (같은 무대 공유)
    rp=[['f_st_top','f_wl'],['f_wr','f_hand'],['m_beam','m_low_l'],['m_low_r','m_tl'],['m_tr','m_hand'],
        ['gj_up0','gj_lo0'],['gj_up1','gj_lo1'],['gj_up2','gj_lo2'],['gj_up3','gj_lo3'],['gj_drumL','gj_up0'],['gj_drumR','gj_up3']]
    top.append(M.group('ropes',[0,0,0],[M.cube(f'rope_{i}',[-0.7,-0.7,0],[0.7,0.7,1],'rope') for i in range(len(rp))]))
    A.bake(top); M.save(f'{OUT}/C_무대.bbmodel',top,[A.json()],name='C')
    return {'ropes':rp}

# =====================================================================
#  D : 무너진 성 → 복원 (83~90)
# =====================================================================
def set_D():
    M=mk(); A=Anim(L); top=[far_ground(M)]+ground(M,-900,900,-700,700)
    top.append(hill(M,'paldal',-150,650,900,260,500))
    # 성벽 세 토막: 가운데 토막이 무너짐 (줄을 위에서부터 숨김 → 88~ 다시 자람)
    for tag,(x0,x1) in [('wa_',(-500,-180)),('wb_',(-180,140)),('wc_',(140,330))]:
        rows=hwaseong_wall(M,tag,x0,x1,100,H=100,T=40,rows=10); top+= rows
        if tag=='wb_':
            for j,g in enumerate(rows):
                if j>=3:
                    tf=T(85)+0.3+(10-j)*0.2; tr=T(88)+0.5+(j-3)*0.45
                    vis(A,g,[(0,tf),(tr,L)])
                    A.add(g,'scale',[(tr,(1,0.02,1)),(tr+0.4,(1,1,1))])
    gt=gate(M,'gate_',470,120); top.append(gt)
    pav=[c for c in gt['children'] if isinstance(c,str)]
    # 문루(위층 나무 건물)만 따로 숨기기 어려우므로, 불탄 문루 = 성문 전체를 잠시 숨기고 아래 화강암 부분만 다른 모형으로
    gbase=M.group('gate_base',[470,0,120],[M.cube('gb',[470-65,0,90],[470-16,70,150],'granite_b'),M.cube('gb',[470+16,0,90],[470+65,70,150],'granite_b'),
        M.cube('gb_arch',[470-16,44,90],[470+16,70,150],'granite_b'),M.cube('gb_dark',[470-16,0,89.6],[470+16,30,90.2],'dark')])
    top.append(gbase)
    vis(A,gt,[(0,T(85)+0.5),(T(89)+1.0,L)]); vis(A,gbase,[(T(85)+0.5,T(89)+1.0)])
    fire=M.group('fire',[470,90,120],[M.cube('fire',[440+(j*13)%60,70+(j%3)*10,100+(j*7)%40],[460+(j*13)%60,95+(j%3)*12,118+(j*7)%40],'fire' if j%2 else 'fire_y') for j in range(9)])
    smoke=M.group('smoke2',[470,140,120],[M.cube('sm',[450+(j%2)*12,110+j*20,105],[480+(j%2)*12,134+j*20,135],'smoke') for j in range(6)])
    top+= [fire,smoke]
    A.add(fire,'scale',[(0,(0,0,0)),(T(85)-0.02,(0,0,0))]+[(T(85)+k*0.3,((1.1,1.25,1.1) if k%2 else (0.9,0.8,0.9))) for k in range(int((E(85)-T(85))/0.3)+1)]+[(E(85)+0.02,(0,0,0))])
    vis(A,smoke,[(T(85),E(87))]); A.add(smoke,'position',[(T(85),(0,0,0)),(E(87),(0,50,0))])
    # 흩어진 돌 (85~) → 87 집이 들어섬 → 88~ 사라짐
    piles=[stone_pile(M,f'dp{j}',x,z,n=45,r=30,seed=40+j) for j,(x,z) in enumerate([(-120,40),(-20,60),(80,30),(-60,-60)])]
    for p in piles: top.append(p); A.add(p,'scale',[(0,(0,0,0)),(T(85)+0.5,(0,0,0)),(T(85)+1.5,(1,1,1)),(T(88)+0.5,(1,1,1)),(T(88)+2.5,(0,0,0))])
    hs=houses(M,'dh',-20,150,6,seed=9)
    for h in hs: top.append(h); vis(A,h,[(T(87),T(88)+0.6)])
    # 복원 (88~90): 커다란 책을 펼쳐 놓음 (그림 쪽) — 성벽 앞
    bk=M.group('bigbook',[-20,0,-120],[M.cube('pg_l',[-80,0,-150],[-20,4,-90],'page'),M.cube('pg_r',[-20,0,-150],[40,4,-90],'page'),M.cube('spine',[-22,0,-150],[-18,5,-90],'book')]+
        [M.cube('dw',[-72+j*10,4,-140],[-70+j*10,4.3,-100],'ink') for j in range(5)]+[M.cube('dw',[-8,4,-140],[30,4.3,-138],'ink'),M.cube('dw',[-8,4,-120],[30,4.3,-118],'ink'),M.cube('roofdw',[-10,4,-110],[32,4.3,-104],'ink')])
    top.append(bk); grow(A,bk,T(89),T(89)+1.0,axis='all')
    for i,(x,z) in enumerate([(-600,-200),(600,-220),(-650,300),(680,280)]): top.append(pine(M,f'pine{i}',x,z,70))
    A.bake(top); M.save(f'{OUT}/D_무너짐.bbmodel',top,[A.json()],name='D'); return {}

if __name__=='__main__':
    info={'A':set_A(),'B':set_B(),'C':set_C(),'D':set_D()}
    for k in info: info[k].setdefault('ropes',[])
    json.dump(info,open(f'{OUT}/세트정보.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
    json.dump(numbers(),open(f'{ROOT}/숫자.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
    for f in sorted(os.listdir(OUT)):
        if f.endswith('.bbmodel'): print(f, len(json.load(open(f'{OUT}/{f}',encoding='utf-8'))['elements']),'cubes')
