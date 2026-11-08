"""《분황사 탑은 원래 몇 층이었을까》 블록 장면 모형 → 연재/분황사탑/장면/<세트>_<이름>.bbmodel + 세트정보.json
   시간은 모두 '영상 시간(초)' 그대로: 연재/분황사탑/분황사탑_시간.json 의 문단 시작(T)·끝(E)
   세트: A 지금 들판 / B 신라 공사터 / C 재료 무대 / F 층수 무대 / D 무너지는 탑 / E 1915 수리·사리함"""
import sys, os, json, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 신라인물 import *
ROOT='/home/user/youtubeshot/연재/분황사탑'
OUT=f'{ROOT}/장면'; os.makedirs(OUT,exist_ok=True)
TIM=json.load(open(f'{ROOT}/분황사탑_시간.json',encoding='utf-8')); SEG=TIM['segs']; L=round(TIM['duration']+1,2)
T=lambda i: SEG[i]['t0']
E=lambda i: SEG[i]['t0']+SEG[i]['dur']

# ---------------- 공용 ----------------
def world_palette(M):
    M.swatch('grass',(110,160,80),12); M.swatch('grass_d',(96,145,70),12); M.swatch('dirt',(150,115,80),10); M.swatch('dirt_d',(125,95,65),10)
    M.swatch('pine',(55,105,60),12); M.swatch('pine_d',(45,88,50),10); M.swatch('trunk',(110,80,55),6)
    M.swatch('hill',(85,130,75),10); M.swatch('hill_d',(70,112,64),10)
    M.swatch('tile',(70,72,78),6); M.swatch('pillar',(150,60,45),6); M.swatch('wall_w',(225,215,190),5)
    M.swatch('fire',(250,140,40),20); M.swatch('fire_y',(255,215,80),15); M.swatch('smoke',(120,118,115),10)
    M.swatch('fog',(238,242,246),3); M.swatch('floor',(226,220,205),5); M.swatch('floor_d',(212,205,190),5)
    M.swatch('water',lambda x,y:(55,115,175) if (x+2*y)%7 else (90,150,205),6); M.swatch('foam',(235,240,245),5)
    M.swatch('copper',(170,110,60),8); M.swatch('gold',(230,190,70),8); M.swatch('shell',(240,232,215),6); M.swatch('cloth_r',(150,40,40),5)
    M.swatch('pole',(140,105,70),6); M.swatch('rope',(200,175,120),5); M.swatch('clay',(170,105,70),10)

def ground(M,x0,x1,z0,z1,tile=64,a='grass',b='grass_d',y=0):
    return [M.cube('g',[x,y-16,z],[x+tile,y,z+tile],a if (x//tile+z//tile)%2 else b) for x in range(x0,x1,tile) for z in range(z0,z1,tile)]

def far_ground(M,col='grass'): return M.cube('far_ground',[-4000,-20,-4000],[4000,-15,4000],col)

def pine(M,tag,x,z,h=70):
    k=[M.cube('trunk',[x-3,0,z-3],[x+3,h*0.45,z+3],'trunk')]
    for j,(w,y0) in enumerate([(34,h*0.3),(26,h*0.55),(16,h*0.78)]):
        k.append(M.cube('pine',[x-w/2,y0,z-w/2],[x+w/2,y0+h*0.22,z+w/2],'pine' if j%2 else 'pine_d'))
    return M.group(tag,[x,0,z],k)

def hills(M,z=1400):
    k=[]
    for i,(x,w,h) in enumerate([(-1400,900,260),(-500,800,200),(300,900,300),(1200,800,220),(-900,600,150),(800,700,170)]):
        zz=z+(i%3)*120; k.append(M.cube('hill',[x-w/2,-10,zz],[x+w/2,h,zz+300],'hill' if i%2 else 'hill_d'))
    return k

def hall(M,tag,x,z,w=150,d=90):
    """나무 법당 (붉은 기둥·흰 벽·검은 기와)"""
    k=[M.cube('h_base',[x-w/2-6,0,z-d/2-6],[x+w/2+6,8,z+d/2+6],'rock')]
    for px in (-w/2,-w/6,w/6,w/2-6):
        for pz in (-d/2,d/2-6): k.append(M.cube('h_pillar',[x+px,8,z+pz],[x+px+6,56,z+pz+6],'pillar'))
    k.append(M.cube('h_wall',[x-w/2+3,8,z-d/2+3],[x+w/2-3,56,z+d/2-3],'wall_w'))
    for j in range(6):
        e=26-j*4; k.append(M.cube('h_roof',[x-w/2-e,56+j*6,z-d/2-e],[x+w/2+e,62+j*6,z+d/2+e],'tile'))
    return M.group(tag,[x,0,z],k)

def vis(A,g,spans):
    """spans=[(켜짐,꺼짐),...] 그 사이에만 보임 (크기 1)"""
    spans=sorted(spans); on0=bool(spans) and spans[0][0]<=0.02
    pts=[(0,(1,1,1) if on0 else (0,0,0))]
    for a,b in spans:
        if a>0.02: pts+= [(a-0.02,(0,0,0)),(a,(1,1,1))]
        pts+= [(b,(1,1,1)),(b+0.02,(0,0,0))]
    A.add(g,'scale',pts)

def grow(A,g,t0,t1,hide_after=None,axis='y'):
    """t0~t1 동안 아래에서 위로 자라남 (그 전엔 안 보임)"""
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
    """오른팔로 망치질 (정은 왼손)"""
    n=p['name'][:-4]; ar=find(p,n+'arm_right'); al=find(p,n+'arm_left')
    pts=[(max(0,t0-0.01),(-30,0,0))]; t=t0; up=True
    while t<t1: pts.append((t,(-95 if up else -45,0,0))); up=not up; t+=per/2
    pts.append((t1+0.2,(-30,0,0))); A.add(ar,'rotation',pts,'catmullrom')
    A.add(al,'rotation',[(max(0,t0-0.01),(-30,0,0)),(t1+0.2,(-30,0,0))])

def setrot(A,g,t,r): A.add(g,'rotation',[(t,r)])

def P(M,tag,kind,x,z,yaw=0,s=1.0,tool=None,y=0):
    g=person(M,tag,kind,s,tool); move(M,g,x,y,z); g['rotation']=[0,yaw,0]; return g

def numbers():
    return [
     {'seg':2,'text':'분황사 모전석탑 · 국보'},
     {'seg':9,'text':'지금 3층 · 높이 9.3m'},
     {'seg':25,'text':'634년(선덕여왕 3년) · 『삼국사기』'},
     {'seg':27,'text':'모전석탑 = 벽돌(塼)을 본뜬(模) 돌탑'},
     {'seg':30,'text':'안산암 · 회색빛 검은 돌'},
     {'seg':32,'text':'유력한 산지 · 울산 북쪽 동해 바닷가 (연구 추정)'},
     {'seg':62,'text':'『동경잡기』 (조선 시대 경주 이야기책)의 기록'},
     {'seg':66,'text':'1857년 · 선비 송달수의 글'},
     {'seg':69,'text':'1915년 해체 수리'},
     {'seg':74,'text':'구리 가위 · 금 바늘 · 조개껍데기'},
     {'seg':76,'text':'숭녕통보 · 1100년대 초 송나라 동전'},
     {'seg':84,'text':'① 3층 또는 5층 — 고유섭'},
     {'seg':88,'text':'② 7층 — 중국 시안 대안탑 7층'},
     {'seg':90,'text':'③ 9층 — 『동경잡기』 · 세키노 다다시'},
     {'seg':93,'text':'1990년대 이후 · 흩어진 돌의 양 계산'},
     {'seg':95,'text':'모아 둔 돌의 양 ≈ 9층 탑'},
     {'seg':99,'text':'약 300m 떨어진 구황동 절터'},
     {'seg':103,'text':'황룡사 9층 목탑 (신라 세 보물)'},
     {'seg':108,'text':'아래층 몸체가 불룩 (손상 조사 연구)'},
    ]

# =====================================================================
#  A : 지금 들판 (현재의 3층 탑) — 들어가며 · 지금 모습 · 끝
# =====================================================================
def set_A():
    M=BigModel(512); silla_palette(M); pagoda_palette(M); world_palette(M); A=Anim(L)
    top=[far_ground(M)]+ground(M,-640,640,-640,640)+hills(M)
    top.append(M.cube('path',[-14,-15,-640],[14,0.6,-125],'dirt'))
    tw,fl,h=pagoda(M,'t_',3); top.append(tw)
    gh,gfl,_=pagoda(M,'g_',9,ghost_from=3,base=False,doors=False,finial=False); move(M,gh,0,19,0); top.append(gh)
    for i,g in enumerate(gfl):
        if i<3: vis(A,g,[])
        else: vis(A,g,[(T(10)+0.3+(i-3)*0.35,E(11))])
    for i,(x,z) in enumerate([(-330,-260),(-420,60),(360,-300),(450,120),(-300,330),(320,360),(-520,-420),(560,-380),(150,-520),(-180,-560)]):
        top.append(pine(M,f'pine{i}',x,z,60+(i%4)*12))
    A.bake(top); M.save(f'{OUT}/A_들판.bbmodel',top,[A.json()],name='A'); return {}

# =====================================================================
#  B : 신라 공사터 (634년) — 돌 깎기 · 탑 쌓기 · 문과 금강역사 · 마지막 장면(안개)
# =====================================================================
def set_B():
    M=BigModel(512); silla_palette(M); pagoda_palette(M); world_palette(M); A=Anim(L)
    top=[far_ground(M,'dirt')]+ground(M,-640,640,-640,640,a='dirt',b='dirt_d')+hills(M,1300)
    top+= [hall(M,'hall1',330,80), hall(M,'hall2',-360,160,170,100)]
    for i,(x,z) in enumerate([(-520,-300),(520,-320),(-560,400),(560,420)]): top.append(pine(M,f'pine{i}',x,z,70))
    # --- 탑: 바닥(38) → 1층 몸 줄줄이(39~41) → 1층 지붕 계단 하나씩(42~45) → 2·3층(50 전에) → 문·금강역사(51~54) → 사자(56) → 끝 장면 9층 + 안개
    tw,fl,ytop=pagoda(M,'t_',9,doors=False,lions=False,finial=False); top.append(tw)
    base=tw['children'][0]; grow(A,base,T(38)+0.2,E(38)-0.3)
    # 1층: 몸을 여러 줄로 나눠 차례로 쌓음 (실제 1층 상자는 숨기고 따로 만듦)
    w,h,out=floor_dims(9,0); y=19; n=14; rows=[]
    for j in range(n):
        g=M.group(f'row{j}',[0,y+j*h/n,0],[M.cube('row',[-w/2,y+j*h/n,-w/2],[w/2,y+(j+1)*h/n,w/2],'wall')])
        top.append(g); rows.append(g)
        ta=T(39)+(E(41)-T(39))*j/n; grow(A,g,ta,ta+0.25)
    rk,_y1,_=roof(M,0,y+h,0,w,out)
    steps=[]
    for j,c in enumerate(rk):
        g=M.group(f'rstep{j}',[0,y+h,0],[c]); top.append(g); steps.append(g)
    n_out=max(3,int(round(out/2.3)))
    for j,g in enumerate(steps):
        if j<n_out: ta=T(42)+(E(44)-T(42))*j/n_out
        else: ta=T(45)+(E(45)-T(45)-0.4)*(j-n_out)/(len(steps)-n_out)
        grow(A,g,ta,ta+0.3)
    # 문·금강역사: 1층 문만 따로 (51~)
    dk=[]; w0=w
    for f in 'nsew':
        dw,dh=26,32
        if f=='n': fr,to=[-dw/2,25,-w0/2-0.6],[dw/2,25+dh,-w0/2+0.2]
        elif f=='s': fr,to=[-dw/2,25,w0/2-0.2],[dw/2,25+dh,w0/2+0.6]
        elif f=='e': fr,to=[w0/2-0.2,25,-dw/2],[w0/2+0.6,25+dh,dw/2]
        else: fr,to=[-w0/2-0.6,25,-dw/2],[-w0/2+0.2,25+dh,dw/2]
        dk.append(M.cube('door',fr,to,'granite'))
    doors=M.group('doors',[0,25,0],dk); top.append(doors); grow(A,doors,T(51)+0.3,T(51)+1.2)
    gk=[]
    for side in (-1,1): gk+= guardian(M,side*(26/2+13),23,-w0/2,'n',1.0)
    for f,sgn in (('s',1),('e',1),('w',1)):
        for side in (-1,1):
            off=side*(26/2+13)
            if f=='s': gk+= guardian(M,-off,23,w0/2,'s',1.0)
            elif f=='e': gk+= guardian(M,w0/2,23,off,'e',1.0)
            else: gk+= guardian(M,-w0/2,23,-off,'w',1.0)
    guards=M.group('guards',[0,23,0],gk); top.append(guards); grow(A,guards,T(53)+0.2,T(53)+1.5)
    lions=[]
    for j,(x,z,yaw) in enumerate([(-1,-1,45),(1,-1,-45),(-1,1,135),(1,1,-135)]):
        lg=lion(M,f'lion{j}',x*111,19,z*111,yaw); top.append(lg); lions.append(lg); grow(A,lg,T(56)+0.3+j*0.4,T(56)+0.9+j*0.4,axis='all')
    # 2층부터: 50 전에 2·3층(몇 해 흐름), 끝 장면(112~)엔 9층까지
    for i,g in enumerate(fl):
        if i==0: vis(A,g,[]); continue
        if i<=2: ta=T(49)+0.5+(i-1)*1.2; grow(A,g,ta,ta+1.0)
        else: grow(A,g,T(111)-0.05,T(111))
    # 안개 (끝 장면): 4층 위로 감싸는 흰 구름 띠, 천천히 흐름
    fog=[]
    for j in range(22):
        a=j/22*6.283; r=120+(j%3)*25; yy=150+(j*37)%170; s=50+(j*13)%40
        fog.append(M.cube('fog',[r*math.cos(a)-s,yy,r*math.sin(a)-s*0.7],[r*math.cos(a)+s,yy+30+(j%4)*8,r*math.sin(a)+s*0.7],'fog'))
    fog.append(M.cube('fog_core',[-110,165,-110],[110,375,110],'fog'))
    fg=M.group('fog',[0,250,0],fog); top.append(fg); vis(A,fg,[(T(111)-0.05,L)])
    A.add(fg,'rotation',[(T(111),(0,0,0)),(L,(0,25,0))])
    # 비계(나무 발판) 꼭대기 — 어른 바우가 서 있을 자리
    ytop9=19+sum(floor_dims(9,i)[1] for i in range(9))
    # 지붕 높이까지 포함한 정확한 꼭대기는 fl 의 마지막 지붕에서
    # --- 사람들 ---
    # 덕보 할아버지 (정·망치) + 바우: 공사터 앞쪽 작업대 (z -200)
    deok=P(M,'deok_','deokbo',18,-205,yaw=0,s=0.97,tool='chisel'); top.append(deok)
    bau=P(M,'bau_','bau',-30,-210,yaw=0,s=0.78); top.append(bau)
    work=M.group('work',[0,0,-205],[M.cube('work_rock',[-6,0,-214],[10,14,-196],'rock'),M.cube('work_block',[-4,14,-210],[8,20,-200],'stone')])
    top.append(work)
    blk=brick(M,'cut_brick',2,14,-205); top.append(blk)   # 다 깎은 돌 (작업대 위)
    vis(A,blk,[(T(17),T(22)),(E(23),T(24))])
    for j,(x,z,n_) in enumerate([(-120,-170,40),(120,-160,34),(-80,-290,30),(150,-260,26)]):
        pg=stone_pile(M,f'pile{j}',x,z,n=n_,r=22,seed=j+5); top.append(pg)
        grow(A,pg,max(0.05,T(13)) if j<2 else T(36),(T(13)+0.1) if j<2 else T(36)+2.5,axis='all')
    # 석공들 (배경에서 돌 깎기)
    for j,(x,z,yaw) in enumerate([(-210,-270,90),(230,-250,-90)]):
        g=P(M,f'w{j}_',['man','man2'][j],x,z,yaw=yaw,tool='chisel'); top.append(g); hammer(A,g,T(13),T(35)-0.5,per=0.5+j*0.07)
    # 덕보 망치질
    hammer(A,deok,T(16),E(18))
    # 바우: 19 고개 갸웃, 22 돌 들기(두 팔 앞으로), 23 고개 숙임
    bh=find(bau,'bau_head'); A.add(bh,'rotation',[(0,(0,0,0)),(T(19),(0,0,0)),(T(19)+0.5,(0,0,14)),(E(19),(0,0,14)),(E(19)+0.3,(0,0,0)),
        (T(23),(0,0,0)),(T(23)+0.6,(15,0,0)),(E(23),(15,0,0)),(E(23)+0.3,(0,0,0))],'catmullrom')
    bbrick=brick(M,'bau_brick',0,0,0)
    bl=find(bau,'bau_arm_left'); br_=find(bau,'bau_arm_right')
    for arm in (bl,br_): A.add(arm,'rotation',[(0,(0,0,0)),(T(22),(0,0,0)),(T(22)+0.5,(-70,0,0)),(E(22),(-70,0,0)),(E(22)+0.4,(0,0,0)),
        (T(55),(0,0,0)),(T(55)+0.5,(-20,0,0)),(E(55),(-20,0,0)),(E(55)+0.3,(0,0,0))],'catmullrom')
    # 바우가 들고 있는 돌 (22): 손 앞에 떠 있는 벽돌
    hb=brick(M,'held',-20,13,-210,along='z'); top.append(hb); vis(A,hb,[(T(22)+0.5,E(22))])
    # 쌓기 장면(36~48): 둘이 탑 앞으로 (z -150), 덕보는 지붕 줄을 내밂(42~), 바우 실 당기기(48)
    A.add(deok,'position',[(0,(0,0,0)),(T(36),(0,0,0)),(T(36)+0.01,(0,0,60)),(T(49),(0,0,60)),(T(49)+0.01,(0,0,0))])
    A.add(bau,'position',[(0,(0,0,0)),(T(36),(0,0,0)),(T(36)+0.01,(0,0,62)),(T(49),(0,0,62)),(T(49)+0.01,(0,0,0)),
        (T(50),(0,0,0)),(T(50)+0.01,(0,0,62)),(T(58),(0,0,62)),(T(58)+0.01,(0,0,0))])
    # 탑을 볼 때(36~58) 둘 다 탑(+z)을 봄
    A.add(deok,'rotation',[(0,(0,-90,0)),(T(36),(0,-90,0)),(T(36)+0.01,(0,180,0)),(T(49),(0,180,0)),(T(49)+0.01,(0,-90,0))])
    A.add(bau,'rotation',[(0,(0,90,0)),(T(36),(0,90,0)),(T(36)+0.01,(0,180,0)),(T(58),(0,180,0)),(T(58)+0.01,(0,90,0))])
    da=find(deok,'deok_arm_left');
    A.add(find(deok,'deok_arm_right'),'rotation',[(T(42)-0.01,(-30,0,0)),(T(42)+0.4,(-110,0,0)),(E(44),(-110,0,0)),(E(44)+0.4,(-30,0,0))],'catmullrom')
    # 바우 50~57: 올려다봄
    A.add(bh,'rotation',[(T(50),(0,0,0)),(T(50)+0.6,(-25,0,0)),(E(57),(-25,0,0)),(E(57)+0.3,(0,0,0))],'catmullrom')
    # 47 덕보 말하며 고개 끄덕, 48 바우 두 팔 벌려 실 당김
    A.add(find(deok,'deok_head'),'rotation',[(T(47),(0,0,0)),(T(47)+0.4,(10,0,0)),(T(47)+0.8,(0,0,0)),(T(47)+1.2,(10,0,0)),(T(47)+1.6,(0,0,0))],'catmullrom')
    string=M.group('string',[0,0,0],[M.cube('string',[-30.3,13,-143],[-29.7,13.6,-66],'rope')]); top.append(string); vis(A,string,[(T(48)+0.4,E(48))])
    for arm,zr in ((bl,60),(br_,-60)):
        A.add(arm,'rotation',[(T(48),(0,0,0)),(T(48)+0.4,(-80,0,zr*0)),(E(48),(-80,0,0)),(E(48)+0.3,(0,0,0))],'catmullrom')
    # 아이 바우·덕보는 끝 장면 전까지 / 끝 장면: 어른 바우(꼭대기 비계) + 지팡이 덕보(아래)
    for g in (bau,hb,blk,work): pass
    vis(A,bau,[(0.0,T(111)-0.05)])
    vis(A,deok,[(0.0,T(111)-0.05)])
    scaf=M.group('scaf',[0,ytop,0],[M.cube('scaf_floor',[-40,ytop,-70],[40,ytop+3,-30],'pole'),
        M.cube('scaf_p1',[-40,ytop-60,-70],[-36,ytop+3,-66],'pole'),M.cube('scaf_p2',[36,ytop-60,-70],[40,ytop+3,-66],'pole'),
        M.cube('scaf_rail',[-40,ytop+14,-70],[40,ytop+16,-67],'pole')])
    top.append(scaf); vis(A,scaf,[(T(111)-0.05,L)])
    bo=P(M,'bauo_','bau_old',0,-50,yaw=0,y=ytop+3); top.append(bo); vis(A,bo,[(T(111)-0.05,L)])
    A.add(bo,'rotation',[(0,(0,180,0)),(T(115)-0.4,(0,180,0)),(T(115),(0,0,0)),(E(115),(0,0,0)),(E(115)+0.5,(0,180,0))])
    last=brick(M,'last',0,ytop-0.5,-24); top.append(last)
    A.add(last,'position',[(0,(0,0,0)),(T(113),(0,8,-12)),(T(113)+2.2,(0,0,0))],'catmullrom'); vis(A,last,[(T(113),L)])
    for arm in ('arm_left','arm_right'):
        A.add(find(bo,'bauo_'+arm),'rotation',[(0,(0,0,0)),(T(113),(-70,0,0)),(T(113)+2.2,(-40,0,0)),(E(113),(0,0,0)),
            (T(115),(0,0,0)),(T(115)+0.4,(-170,0,0)),(E(115)-0.2,(-170,0,0)),(E(115)+0.3,(0,0,0))],'catmullrom')
    old=P(M,'old_','deokbo',30,-190,yaw=180,s=0.95,tool='staff'); top.append(old); vis(A,old,[(T(111)-0.05,L)])
    A.add(find(old,'old_head'),'rotation',[(0,(0,0,0)),(T(114),(0,0,0)),(T(114)+1.0,(-35,0,0)),(L,(-35,0,0))],'catmullrom')
    A.add(find(old,'old_body'),'rotation',[(0,(8,0,0))])
    A.bake(top); M.save(f'{OUT}/B_공사터.bbmodel',top,[A.json()],name='B'); return {'ytop':ytop}

# =====================================================================
#  C : 재료 무대 — 연도·이름·전탑(흙 벽돌) vs 돌탑·안산암·바닷가 바위·벽돌 가마
# =====================================================================
def studio(M,size=1400):
    return [M.cube('st_floor',[-size,-16,-size],[size,0,size],'floor'),
            M.cube('st_back',[-size,0,size*0.6],[size,size*0.8,size*0.6+20],'floor_d')]

def set_C():
    M=BigModel(512); silla_palette(M); pagoda_palette(M); world_palette(M); A=Anim(L); top=studio(M)
    tw,_,_=pagoda(M,'t_',3,base_w=200); top.append(tw)                       # 가운데: 분황사 돌탑
    jt,jfl,_=pagoda(M,'j_',7,base=True,doors=False,lions=False,finial=True,base_w=180,style='clay'); move(M,jt,380,0,60); top.append(jt)   # 화면 왼쪽(+x): 중국 전탑
    vis(A,jt,[(T(28),E(29)),(T(33),E(34))])
    # 벽돌 가마 (전탑 옆, 불)
    kiln=M.group('kiln',[520,0,-80],[M.cube('kiln',[480,0,-120],[560,50,-40],'clay'),M.cube('kiln_top',[490,50,-110],[550,70,-50],'clay'),
         M.cube('kiln_door',[505,4,-121],[535,30,-119],'dark')])
    flame=M.group('flame',[520,4,-122],[M.cube('fl1',[508,4,-123],[532,22,-121],'fire'),M.cube('fl2',[513,8,-124],[527,28,-122],'fire_y')])
    top+= [kiln,flame]; vis(A,kiln,[(T(33),E(34))]); vis(A,flame,[(T(33),E(34))])
    A.add(flame,'rotation',[(T(33)+k*0.25,(0,0,(4 if k%2 else -4))) for k in range(int((E(34)-T(33))/0.25)+1)])
    # 큰 돌 벽돌 하나 (화면 오른쪽 -x) — 안산암 (30~31 천천히 돎)
    big=M.group('bigbrick',[-380,60,0],[M.cube('bb',[-440,40,-22],[-320,80,22],'stone',north='stone_l',up='stone_l')]); top.append(big)
    vis(A,big,[(T(30),E(31))]); A.add(big,'rotation',[(T(30),(0,0,0)),(E(31),(0,200,0))])
    chis=M.group('chis',[-380,90,-30],[M.cube('ch',[-384,82,-40],[-376,110,-34],'iron'),M.cube('chh',[-386,108,-42],[-374,116,-32],'wood')])
    top.append(chis); vis(A,chis,[(T(33),E(34))])
    # 바닷가 바위 (뒤쪽 멀리 z +700): 바다 + 절벽 (32)
    sea=[M.cube('sea',[-4000,-4,-6000],[4000,1,-1760],'water'), M.cube('land',[-4000,-16,-1760],[4000,0.5,-1400],'grass')]
    for j in range(11):
        x=-900+j*165; hh=50+(j*37)%70
        sea.append(M.cube('cliff',[x,0,-1790-(j%2)*25],[x+150,hh,-1740+(j%3)*10],'stone' if j%2 else 'stone_d'))
        sea.append(M.cube('foam',[x,0,-1830-(j%3)*15],[x+150,1.6,-1790-(j%2)*25],'foam'))
    cliff=M.group('coast',[0,0,-1760],sea); top.append(cliff); vis(A,cliff,[(T(32)-0.05,E(32)+0.05)])
    vis(A,tw,[(0,T(32)-0.05),(E(32)+0.05,L)])
    A.bake(top); M.save(f'{OUT}/C_재료.bbmodel',top,[A.json()],name='C'); return {}

# =====================================================================
#  F : 층수 무대 — 3·5·7·9층 쌓아 보기, 흔들림, 돌 양 계산(7 vs 9), 구황동 돌, 황룡사 목탑
# =====================================================================
def mokap(M,tag,x,z,floors=9):
    """황룡사 9층 목탑 (나무: 붉은 기둥·흰 벽·검은 기와) — 크고 높음"""
    k=[M.cube('mt_base',[x-100,0,z-100],[x+100,12,z+100],'rock')]; y=12
    for i in range(floors):
        w=150*(0.95**i); hh=40
        k.append(M.cube('mt_wall',[x-w/2,y,z-w/2],[x+w/2,y+hh,z+w/2],'wall_w'))
        for px in (-w/2,w/2-5):
            for pz in (-w/2,w/2-5): k.append(M.cube('mt_p',[x+px,y,z+pz],[x+px+5,y+hh,z+pz+5],'pillar'))
        y+=hh; e=18*(0.95**i)
        k.append(M.cube('mt_roof',[x-w/2-e,y,z-w/2-e],[x+w/2+e,y+6,z+w/2+e],'tile')); y+=6
        k.append(M.cube('mt_roof2',[x-w/2-e/2,y,z-w/2-e/2],[x+w/2+e/2,y+4,z+w/2+e/2],'tile')); y+=4
    k.append(M.cube('mt_spire',[x-3,y,z-3],[x+3,y+60,z+3],'gold'))
    return M.group(tag,[x,0,z],k)

def set_F():
    M=BigModel(512); silla_palette(M); pagoda_palette(M); world_palette(M); A=Anim(L); top=studio(M,1800)
    # 가운데 탑: 9층 (4층부터 하늘색 = 상상)
    tw,fl,_=pagoda(M,'t_',9,ghost_from=3,finial=False); top.append(tw)
    plan=[(0,T(86),3),(T(86),T(87),5),(T(87),T(88),9),(T(88),T(90),7),(T(90),T(92)-0.05,9),(T(92)-0.05,T(98)-0.05,0),(T(98)-0.05,T(102),3),(T(102),L,9)]
    for i,g in enumerate(fl):
        sp=[(max(0,a),b) for a,b,n in plan if n>i]
        mg=[]
        for a,b in sp:
            if mg and abs(mg[-1][1]-a)<0.05: mg[-1]=(mg[-1][0],b)
            else: mg.append((a,b))
        vis(A,g,mg)
    vis(A,tw['children'][0],[(0,T(92)-0.05),(T(98)-0.05,L)])
    # 87: 너무 높으면 흔들 → 탑 전체가 살짝 기우뚱
    A.add(tw,'rotation',[(0,(0,0,0)),(T(87)+1.2,(0,0,0))]+[(T(87)+1.2+k*0.5,(0,0,(2.2 if k%2 else -2.2))) for k in range(1,int((E(87)-T(87)-1.2)/0.5))]+[(E(87),(0,0,0))],'catmullrom')
    # 92~96: 왼쪽(+x) 7층 상상, 오른쪽(-x) 9층 상상, 앞에 돌 더미
    t7,f7,_=pagoda(M,'s7_',7,ghost_from=3,finial=False,lions=False); move(M,t7,260,0,0); top.append(t7)
    t9,f9,_=pagoda(M,'s9_',9,ghost_from=3,finial=False,lions=False); move(M,t9,-260,0,0); top.append(t9)
    s9,fs9,_=pagoda(M,'f9_',9,finial=False,lions=False,doors=False,base=False); move(M,s9,-260,19,0); top.append(s9)
    vis(A,t7,[(T(92)-0.05,T(98)-0.05)]); vis(A,t9,[(T(92)-0.05,T(98)-0.05)])
    for i,g in enumerate(fs9):
        if i<3: vis(A,g,[]); continue
        ta=T(95)+0.3+(i-3)*0.45; vis(A,g,[(ta,T(98)-0.05)])
    pile=stone_pile(M,'pile',0,-200,n=90,r=55,seed=11); top.append(pile)
    A.add(pile,'scale',[(0,(0,0,0)),(T(92)-0.05,(0,0,0)),(T(93),(1,1,1)),(T(95)+0.3,(1,1,1)),(T(95)+3.0,(0.25,0.25,0.25)),(T(98)-0.05,(0.25,0.25,0.25)),(T(98),(0,0,0)),
        (T(99),(0,0,0)),(T(99)+0.01,(1,1,1)),(E(101),(1,1,1)),(E(101)+0.02,(0,0,0))])
    # 날아가는 돌 (95: 더미 → 9층 탑)
    for j in range(8):
        b=brick(M,f'fly{j}',0,6,-200); top.append(b); ta=T(95)+0.2+j*0.3
        A.add(b,'position',[(0,(0,0,0)),(ta,(0,0,0)),(ta+0.6,(130,140+j*12,100)),(ta+1.1,(260,90+j*25,200))],'catmullrom')   # x 반대: +x 위치 = 화면 -x 쪽 9층 탑
        vis(A,b,[(ta,ta+1.1)])
    # 99~101: 구황동 절터 (멀리 화면 오른쪽 -x 700) — 같은 모양 돌 + 금강역사 조각, 돌이 이쪽 더미로 날아옴
    gh=stone_pile(M,'guhwang',-700,-150,n=80,r=55,seed=21); top.append(gh)
    gk=guardian(M,-700,0,-230,'n',3.0); ggrd=M.group('guhwang_g',[-700,0,-230],gk+[M.cube('gslab',[-726,0,-231],[-674,82,-228],'stone_l')]); top.append(ggrd)
    for g in (gh,ggrd): vis(A,g,[(T(99),E(101))])
    for j in range(6):
        b=brick(M,f'gfly{j}',-700,8,-150); top.append(b); ta=T(100)+0.3+j*0.45
        A.add(b,'position',[(0,(0,0,0)),(ta,(0,0,0)),(ta+0.7,(-350,120,-25)),(ta+1.4,(-700,0,-50))],'catmullrom')
        vis(A,b,[(ta,ta+1.4)])
    # 103~104: 황룡사 9층 목탑 (화면 왼쪽 +x 450) 나란히
    mt=mokap(M,'mok',520,150); top.append(mt); vis(A,mt,[(T(103),E(104))])
    A.bake(top); M.save(f'{OUT}/F_층수.bbmodel',top,[A.json()],name='F'); return {}

# =====================================================================
#  D : 무너지는 탑 — 몽골 침입 불길, 『동경잡기』의 9층, 반이 허물어짐, 스님, 선비, 흩어진 돌
# =====================================================================
def fall(A,g,t0,dx,dz,drop,rot,hide=True):
    A.add(g,'position',[(0,(0,0,0)),(t0,(0,0,0)),(t0+0.5,(-dx*0.4,6,dz*0.4)),(t0+1.4,(-dx,-drop,dz))],'catmullrom')
    A.add(g,'rotation',[(0,(0,0,0)),(t0,(0,0,0)),(t0+1.4,rot)],'catmullrom')

def set_D():
    M=BigModel(512); silla_palette(M); pagoda_palette(M); world_palette(M); A=Anim(L)
    top=[far_ground(M)]+ground(M,-640,640,-640,640)+hills(M)
    tw,fl,_=pagoda(M,'t_',9,finial=False); top.append(tw)
    hl=hall(M,'hall',-330,-60); top.append(hl)
    hl2=hall(M,'hall2',320,40,130,80); top.append(hl2)
    # 60: 불 (법당 두 채), 연기
    for hi,(hx,hz) in enumerate([(-330,-60),(320,40)]):
        fk=[]; sk=[]
        for j in range(10):
            x=hx-60+(j*29)%120; z=hz-35+(j*17)%70; s=14+(j%3)*6
            fk.append(M.cube('fire',[x-s,80+(j%4)*8,z-s],[x+s,110+(j%4)*14,z+s],'fire' if j%2 else 'fire_y'))
        for j in range(6): x=hx-30+(j%3)*20; sk.append(M.cube('smoke',[x-22,130+j*22,hz-22+(j%2)*8],[x+22,160+j*22,hz+22],'smoke'))
        fg=M.group(f'fire{hi}',[hx,80,hz],fk); sg=M.group(f'smoke{hi}',[hx,100,hz],sk); top+= [fg,sg]
        A.add(fg,'scale',[(0,(0,0,0)),(T(60)-0.02,(0,0,0))]+[(T(60)+k*0.3,((1.1,1.25,1.1) if k%2 else (0.9,0.8,0.9))) for k in range(int((E(60)-T(60))/0.3)+1)]+[(E(60)+0.02,(0,0,0))])
        vis(A,sg,[(T(60),E(60))]); A.add(sg,'position',[(T(60),(0,0,0)),(E(60),(0,60,0))])
    # 불탄 뒤 법당은 무너짐(지붕만 남은 잔해) → 61 부터 숨김
    vis(A,hl,[(0,E(60))]); vis(A,hl2,[(0,E(60))])
    ruins=[]
    for hi,(hx,hz) in enumerate([(-330,-60),(320,40)]):
        rg=M.group(f'ruin{hi}',[hx,0,hz],[M.cube('ruin',[hx-70,0,hz-40],[hx+70,10,hz+40],'tile'),M.cube('ruin_p',[hx-50,0,hz-30],[hx-44,30,hz-24],'pillar'),
            M.cube('ruin_p',[hx+30,0,hz+10],[hx+36,22,hz+16],'pillar')]); top.append(rg); ruins.append(rg); vis(A,rg,[(E(60),L)])
    # 63: 5~9층이 무너짐 (절반)
    for i in range(4,9):
        g=fl[i]; ang=(i*73)%360; dx=math.cos(math.radians(ang))*(90+i*12); dz=math.sin(math.radians(ang))*(90+i*12)
        fall(A,g,T(63)+0.3+(8-i)*0.35,dx,dz,120+i*25,(35*(1 if i%2 else -1),0,50*(1 if i%3 else -1)))
        vis(A,g,[(0,T(63)+0.3+(8-i)*0.35+1.35)])
    # 64: 스님이 고쳐 쌓다가 3·4층도 무너짐 (남는 것: 1층 + 2층 반쯤)
    monk=P(M,'monk_','monk',40,-170,yaw=180); top.append(monk); vis(A,monk,[(T(64)-0.05,E(65))])
    fixb=[]
    for j in range(5):
        b=brick(M,f'fix{j}',-30+j*14,0,-150); top.append(b); fixb.append(b)
        A.add(b,'position',[(0,(0,0,0)),(T(64)+0.3+j*0.4,(0,0,0)),(T(64)+0.9+j*0.4,(0,150,90))],'catmullrom')
        vis(A,b,[(T(64)+0.3+j*0.4,T(64)+3.0)])
    hammer(A,monk,T(64)+0.2,T(64)+2.8,per=0.6)
    for i in (2,3):
        g=fl[i]; ta=T(64)+3.0+(3-i)*0.4; dx=(-1 if i==3 else 1)*110; dz=-60*(1 if i==3 else -1)
        fall(A,g,ta,dx,dz,60+i*20,(25,0,-40 if i==3 else 40)); vis(A,g,[(0,ta+1.35)])
    # 2층은 반쯤 깨진 모습으로 (위쪽 줄여서)
    A.add(fl[1],'scale',[(0,(1,1,1)),(T(64)+3.6,(1,1,1)),(T(64)+4.0,(1,0.6,1)),(L,(1,0.6,1))])
    A.add(find(monk,'monk_head'),'rotation',[(T(64)+3.0,(0,0,0)),(T(64)+3.6,(-25,0,0)),(E(65),(-25,0,0))],'catmullrom')
    # 무너진 돌 더미 (63 이후 커짐, 67 에 흩어짐)
    piles=[]
    for j,(x,z,n_) in enumerate([(-160,-120,50),(170,-90,46),(-140,170,44),(150,160,40),(0,-200,36),(-260,30,30),(260,-20,30)]):
        pg=stone_pile(M,f'dp{j}',x,z,n=n_,r=30,seed=31+j); top.append(pg); piles.append(pg)
        ta=T(63)+0.8+j*0.3 if j<4 else T(67)+j*0.3-1.0
        A.add(pg,'scale',[(0,(0,0,0)),(ta,(0,0,0)),(ta+0.8,(1,1,1)),(L,(1,1,1))])
    # 66: 선비 (갓·도포) 걸어와 탑을 봄
    sb=P(M,'sb_','seonbi',-120,-330,yaw=180); top.append(sb); vis(A,sb,[(T(66)-0.05,E(67))])
    A.add(sb,'position',[(0,(0,0,0)),(T(66),(0,0,0)),(T(66)+3.5,(-30,0,110)),(E(67),(-30,0,110))])
    walk_cycle(A,sb,T(66),T(66)+3.5,amp=22,period=1.0)
    A.add(find(sb,'sb_head'),'rotation',[(T(66)+3.5,(0,0,0)),(T(66)+4.2,(-15,0,0)),(E(67),(-15,0,0))],'catmullrom')
    A.bake(top); M.save(f'{OUT}/D_무너짐.bbmodel',top,[A.json()],name='D'); return {}

# =====================================================================
#  E : 1915 해체 수리 + 사리함 (멀리 따로 놓은 탁자, x -1200)
# =====================================================================
def coin(M,x,y,z,s=1.0,col='copper'):
    """둥근 동전 + 가운데 네모 구멍 (줄마다 폭을 달리해 둥글게)"""
    k=[]; R_=4.5; hole=1.3
    for j in range(-4,5):
        zz0,zz1=z+j*s-0.5*s,z+j*s+0.5*s; w=math.sqrt(max(0,R_*R_-(j*1.0)**2))
        if abs(j)<=1:
            k.append(M.cube('coin',[x-w*s,y,zz0],[x-hole*s,y+0.8*s,zz1],col)); k.append(M.cube('coin',[x+hole*s,y,zz0],[x+w*s,y+0.8*s,zz1],col))
        else: k.append(M.cube('coin',[x-w*s,y,zz0],[x+w*s,y+0.8*s,zz1],col))
    return k

def set_E():
    M=BigModel(512); silla_palette(M); pagoda_palette(M); world_palette(M); A=Anim(L)
    top=[far_ground(M)]+ground(M,-640,640,-640,640)+hills(M)
    tw,fl,_=pagoda(M,'t_',3); top.append(tw)
    # 69: 무너져 가는 탑 = 1층 + 2층 반, 3층·꽃장식 없음 → 70 에 해체(2층 사라짐) → 71 다시 3층
    A.add(fl[1],'scale',[(0,(1,0.6,1)),(T(70)+0.5,(1,0.6,1)),(T(70)+2.5,(1,0,1)),(T(70)+3.5,(1,0,1)),(T(71)-0.6,(1,1,1)),(L,(1,1,1))])
    vis(A,fl[2],[(T(71)-0.3,L)]); vis(A,fl[3],[(T(71),L)])
    # 나무 비계 (69~70)
    sk=[]
    for x in (-90,90):
        for z in (-90,90): sk.append(M.cube('pole',[x-3,0,z-3],[x+3,150,z+3],'pole'))
    for y in (40,80,120):
        sk+= [M.cube('bar',[-93,y,-93],[93,y+3,-87],'pole'),M.cube('bar',[-93,y,87],[93,y+3,93],'pole'),
              M.cube('bar',[-93,y,-93],[-87,y+3,93],'pole'),M.cube('bar',[87,y,-93],[93,y+3,93],'pole')]
    sk.append(M.cube('crane',[-3,150,-100],[3,156,0],'pole')); sk.append(M.cube('crane_up',[-3,0,-103],[3,156,-97],'pole'))
    scaf=M.group('scaf',[0,0,0],sk); top.append(scaf); vis(A,scaf,[(0,E(70))])
    # 내려오는 돌들 (밧줄에 매달린 벽돌 묶음) 69~70
    for j in range(5):
        b=M.group(f'down{j}',[0,110,-60],[M.cube('pack',[-10,104,-66],[10,112,-54],'stone'),M.cube('line',[-0.6,112,-60.6],[0.6,150,-59.4],'rope')])
        top.append(b); ta=T(69)+0.5+j*((E(70)-T(69)-1.5)/5)
        A.add(b,'position',[(0,(0,0,0)),(ta,(0,0,0)),(ta+1.6,(0,-100,-30))],'catmullrom'); vis(A,b,[(ta,ta+1.6)])
    stacks=[]
    for j,(x,z) in enumerate([(-170,-150),(-120,-190),(160,-160),(200,-110)]):
        pg=stone_pile(M,f'ep{j}',x,z,n=40,r=25,seed=51+j); top.append(pg)
        A.add(pg,'scale',[(0,(0.6,0.6,0.6)),(T(69),(0.6,0.6,0.6)),(E(70),(1,1,1)),(T(71)-0.5,(1,1,1)),(T(71)+0.5,(0.3,0.3,0.3)),(L,(0.3,0.3,0.3))])
    # --- 사리함 탁자 (x -1200 → 위치값은 그대로 move) ---
    X=-1200
    tk=[M.cube('table',[X-60,0,-40],[X+60,30,40],'wood_d'),M.cube('cloth',[X-50,30,-32],[X+50,31,32],'cloth_r')]
    box=[M.cube('box',[X-16,31,-14],[X+16,51,14],'granite')]
    lid=M.group('lid',[X,51,14],[M.cube('lid',[X-18,51,-16],[X+18,57,16],'granite_d')])
    top+= [M.group('table',[X,0,0],tk+box),lid]
    A.add(lid,'rotation',[(0,(0,0,0)),(T(73)+0.5,(0,0,0)),(T(73)+2.0,(-110,0,0)),(L,(-110,0,0))],'catmullrom')
    # 물건들: 가위(X 모양), 금 바늘, 고둥 껍데기 → 상자 앞 천 위에 차례로
    sc=M.group('scissors',[X+30,32,-25],[M.cube('sc1',[X+18,31,-27],[X+42,32.5,-24.5],'copper'),M.cube('sc2',[X+18,31,-23],[X+42,32.5,-20.5],'copper'),
        M.cube('sc_ring1',[X+42,31,-29],[X+48,32.5,-24],'copper'),M.cube('sc_ring2',[X+42,31,-22],[X+48,32.5,-17],'copper')])
    nd=M.group('needle',[X,32,-24],[M.cube('nd',[X-10,31,-24.5],[X+10,31.8,-23.7],'gold'),M.cube('nd_eye',[X+10,31,-25],[X+12,32,-23.2],'gold')])
    sh=M.group('shell',[X-30,32,-24],[M.cube('sh1',[X-36,31,-30],[X-24,35,-18],'shell'),M.cube('sh2',[X-34,35,-28],[X-26,39,-20],'shell'),M.cube('sh3',[X-32,39,-26],[X-28,43,-22],'shell')])
    for g,k in ((sc,0),(nd,1),(sh,2)): top.append(g); grow(A,g,T(74)+0.3+k*1.0,T(74)+0.8+k*1.0,axis='all')
    coins=[]
    for j,(x,z) in enumerate([(-40,0),(-40,12),(40,2),(40,14)]):
        cg=M.group(f'coin{j}',[X+x,32,z],coin(M,X+x,31,z,1.0)); top.append(cg); coins.append(cg); grow(A,cg,T(75)+0.2+j*0.3,T(75)+0.6+j*0.3,axis='all')
    # 76: 숭녕통보 크게 (탁자 위로 떠오름)
    bc=M.group('bigcoin',[X,70,0],coin(M,X,68,0,4.0)); top.append(bc)
    A.add(bc,'rotation',[(0,(0,0,0)),(T(76),(-80,0,0)),(E(77),(-80,40,0))]); vis(A,bc,[(T(76),E(77))])
    A.bake(top); M.save(f'{OUT}/E_수리.bbmodel',top,[A.json()],name='E'); return {}

if __name__=='__main__':
    info={'A':set_A(),'B':set_B(),'C':set_C(),'F':set_F(),'D':set_D(),'E':set_E()}
    for k in info: info[k].setdefault('ropes',[])
    json.dump(info,open(f'{OUT}/세트정보.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
    json.dump(numbers(),open(f'{ROOT}/숫자.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
    for f in sorted(os.listdir(OUT)):
        if f.endswith('.bbmodel'): print(f, len(json.load(open(f'{OUT}/{f}',encoding='utf-8'))['elements']),'cubes')
