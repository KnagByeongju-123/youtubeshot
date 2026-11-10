"""《화성의 오디세이》 블록 장면 모형 + 샷 목록 → 연재/화성의오디세이/장면/<세트>_<이름>.bbmodel · 세트정보.json · 샷목록.json · ../숫자.json
   시간은 모두 '영상 시간(초)': 화성의오디세이_시간.json 의 문단 시작 T(i)·끝 E(i).  문단은 번호 대신 글귀로 찾음 I('글귀')
   세트: S 우주 / X 전시실(들어가며) / Y 전시실(숨은 뜻) / A 착륙지 / B 추락 사막 / C 만남·모닥불 / D 피라미드 줄 / Ecanal 운하 / F 진흙 도시 / G 굴 속
   사용: python 화성_장면.py [세트글자들 예: SXA | all]"""
import sys, os, json, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 화성_세트 import *
import 겹침면_검사
ROOT='/home/user/youtubeshot/연재/화성의오디세이'
OUT=f'{ROOT}/장면'; os.makedirs(OUT,exist_ok=True)
TIM=json.load(open(f'{ROOT}/화성의오디세이_시간.json',encoding='utf-8')); SEG=TIM['segs']; L=round(TIM['duration']+1,2)
T=lambda i: SEG[i]['t0']
E=lambda i: SEG[i]['t0']+SEG[i]['dur']
def I(s,nth=0):
    hit=[i for i,g in enumerate(SEG) if s in g['text'].replace(',','')]
    if len(hit)<=nth: raise SystemExit(f'문단을 못 찾음: {s}')
    return hit[nth]

# ---------------- 하늘 ----------------
DAY=['#c98a5c','#f0cfa4']; MORN=['#d99a86','#f6dcc0']; DUSK=['#3a2f55','#c9683a','#f0b070']; NIGHT=['#04050d','#1a1430']
SPACE=['#02030a','#0b0d20']; HALLBG=['#1a1420','#2a2030']; CAVE=['#0e0908','#1a100c']

# ---------------- 샷 ----------------
SHOTS=[]; NUMS=[]
def cam(*keys):
    """키 = (u, 카메라 자리, 보는 곳[, 흔들림 배율 0~1])"""
    return [dict(u=k[0],pos=list(k[1]),tgt=list(k[2]),**({'shake':k[3]} if len(k)>3 else {})) for k in keys]
def two(p0,t0,p1=None,t1=None): return cam((0,p0,t0),(1,p1 or p0,t1 or t0))
def orbit(c,r,h,a0,a1,tgt=None,n=6,r1=None,h1=None,shake=None):
    """c=(x,z) 둘레를 a0→a1 도 만큼 도는 카메라 (0도 = -z 쪽에서 봄, +는 화면 왼쪽(+x)으로 돎). r·h 가 r1·h1 로 바뀌면 다가가며/솟으며 돎"""
    ks=[]; r1=r if r1 is None else r1; h1=h if h1 is None else h1; tgt=tgt or (c[0],h*0.6,c[1])
    for i in range(n+1):
        u=i/n; a=math.radians(a0+(a1-a0)*u); rr=r+(r1-r)*u; k={'u':u,'pos':[c[0]+rr*math.sin(a),h+(h1-h)*u,c[1]-rr*math.cos(a)],'tgt':list(tgt)}
        if shake is not None: k['shake']=shake
        ks.append(k)
    return ks
def sh(name,st,a,b,camk,sky=DAY,fps=12,**kw):
    """a,b = 문단 번호 (a 시작 ~ b 시작). 숫자 대신 (번호,초 더하기) 도 됨"""
    ta=(0.0 if a==0 else T(a)) if isinstance(a,int) else T(a[0])+a[1]; tb=(L if b>=len(SEG) else T(b)) if isinstance(b,int) else T(b[0])+b[1]
    SHOTS.append(dict(name=f'{len(SHOTS):03d}_{name}',set=st,t0=round(ta,3),t1=round(tb,3),fps=fps,cam=camk,sky=sky,**kw))
def num(i,text,extra=0): NUMS.append({'seg':i,'text':text,**({'extra':extra} if extra else {})})

# ---------------- 움직임 도우미 ----------------
def vis(A,g,spans):
    spans=sorted(spans); on0=bool(spans) and spans[0][0]<=0.02
    pts=[(0,(1,1,1) if on0 else (0,0,0))]
    for a,b in spans:
        if a>0.02: pts+= [(a-0.02,(0,0,0)),(a,(1,1,1))]
        if b<L-0.05: pts+= [(b,(1,1,1)),(b+0.02,(0,0,0))]
    A.add(g,'scale',pts)
def grow(A,g,t0,t1,hide_after=None,axis='y'):
    s0=(1,0.02,1) if axis=='y' else (0.02,0.02,0.02)
    pts=[(0,(0,0,0)),(max(0,t0-0.02),(0,0,0)),(t0,s0),(t1,(1,1,1))]
    if hide_after: pts+= [(hide_after,(1,1,1)),(hide_after+0.02,(0,0,0))]
    A.add(g,'scale',pts)
def cyc(A,g,ch,t0,t1,a,b,per,rest=None,interp='catmullrom'):
    """t0~t1 동안 a↔b 를 per 초마다 오감"""
    pts=[(max(0,t0-0.01),rest if rest is not None else a)]; t=t0; k=0
    while t<t1-1e-6: pts.append((t,a if k%2==0 else b)); t+=per/2; k+=1
    pts.append((t1,rest if rest is not None else a)); A.add(g,ch,pts,interp)

class Act:
    """움직이는 것 하나 (인물·로켓·수레). 모형은 원점에 만들고, 바깥 묶음의 위치·방향 키로 세계에 놓음.
       위치 x 는 Blockbench 에서 반대로 적용되므로 여기서 뒤집음. 방향 yaw: 0 = -z(카메라 쪽)를 봄, +90 = +x, 180 = +z"""
    def __init__(s,M,A,top,g,tag,x,z,yaw=0,y=0,legs='two'):
        s.M=M; s.A=A; s.g=g; s.tag=tag; s.legs=legs
        s.out=M.group(tag+'mv',[0,0,0],[g]); top.append(s.out)
        s.pk=[(0,(x,y,z),'linear')]; s.yk=[(0,yaw)]; s.cur=(x,y,z); s.yaw=yaw; s.t=0
    def part(s,name): return find(s.g,s.tag+name)
    def hold(s,t):
        if t>s.pk[-1][0]+1e-6: s.pk.append((t,s.cur,'linear'))
        if t>s.yk[-1][0]+1e-6: s.yk.append((t,s.yaw))
    def at(s,t,x,z,yaw=None,y=0):
        """순간 이동 (컷이 바뀔 때)"""
        s.hold(t-0.02); s.cur=(x,y,z); s.pk.append((t,s.cur,'linear'))
        if yaw is not None: s.yaw=yaw
        s.yk.append((t,s.yaw)); return s
    def turn(s,t,yaw,dur=0.3):
        s.hold(t); d=(yaw-s.yaw+180)%360-180; s.yaw=s.yaw+d; s.yk.append((t+dur,s.yaw)); return s
    def look(s,t,x,z,dur=0.3):
        dx=x-s.cur[0]; dz=z-s.cur[2]; return s.turn(t,math.degrees(math.atan2(dx,-dz)),dur)
    def go(s,t0,t1,x,z,y=0,walk=True,face=True,amp=26,per=0.9,interp='linear'):
        if face and (abs(x-s.cur[0])+abs(z-s.cur[2])>1): s.look(max(0,t0-0.25),x,z,0.25)
        s.hold(t0); s.cur=(x,y,z); s.pk.append((t1,s.cur,interp)); s.yk.append((t1,s.yaw))
        if walk: s.walk(t0,t1,amp,per)
        return s
    def walk(s,t0,t1,amp=26,per=0.9):
        if s.legs=='two':
            for nm,sg in (('leg_left',1),('leg_right',-1),('arm_left',-1),('arm_right',1)):
                g=s.part(nm)
                if g: cyc(s.A,g,'rotation',t0,t1,(sg*amp,0,0),(-sg*amp,0,0),per,rest=(0,0,0))
        elif s.legs=='four':
            for nm,sg in (('leg_fl',1),('leg_br',1),('leg_fr',-1),('leg_bl',-1)):
                cyc(s.A,s.part(nm),'rotation',t0,t1,(sg*amp,0,0),(-sg*amp,0,0),per,rest=(0,0,0))
    def hop(s,t0,t1,x,z,h=10,n=3):
        """통통 뛰며 감 (화성의 약한 중력)"""
        s.look(max(0,t0-0.25),x,z,0.25); s.hold(t0); x0,_,z0=s.cur
        for i in range(n):
            ta=t0+(t1-t0)*(i+0.5)/n; tb=t0+(t1-t0)*(i+1)/n; f1=(i+0.5)/n; f2=(i+1)/n
            s.pk.append((ta,(x0+(x-x0)*f1,h,z0+(z-z0)*f1),'catmullrom')); s.pk.append((tb,(x0+(x-x0)*f2,0,z0+(z-z0)*f2),'catmullrom'))
        s.cur=(x,0,z); s.yk.append((t1,s.yaw)); s.walk(t0,t1,18,(t1-t0)/n); return s
    def finish(s):
        for t,(x,y,z),ip in s.pk: s.A.add(s.out,'position',[(t,(-x,y,z))],ip)
        s.A.add(s.out,'rotation',[(t,(0,yw,0)) for t,yw in s.yk])
    def show(s,spans): vis(s.A,s.out,spans); return s
    # --- 몸짓 ---
    def arm(s,side,t0,t1,rx=-80,rz=0,ease=0.35):
        g=s.part('arm_right' if side=='r' else 'arm_left')
        s.A.add(g,'rotation',[(max(0,t0-0.01),(0,0,0)),(t0+ease,(rx,0,rz)),(max(t0+ease,t1-ease),(rx,0,rz)),(t1,(0,0,0))],'catmullrom'); return s
    def nod(s,t0,t1,rx=12,per=0.7):
        cyc(s.A,s.part('head'),'rotation',t0,t1,(rx,0,0),(-rx*0.3,0,0),per,rest=(0,0,0)); return s
    def tilt(s,t0,t1,rz=14):
        s.A.add(s.part('head'),'rotation',[(max(0,t0-0.01),(0,0,0)),(t0+0.4,(0,0,rz)),(max(t0+0.4,t1-0.3),(0,0,rz)),(t1,(0,0,0))],'catmullrom'); return s
    def headturn(s,t0,t1,ry=40):
        s.A.add(s.part('head'),'rotation',[(max(0,t0-0.01),(0,0,0)),(t0+0.4,(0,ry,0)),(max(t0+0.4,t1-0.3),(0,ry,0)),(t1,(0,0,0))],'catmullrom'); return s

ACTS=[]
def actor(M,A,top,g,tag,x,z,yaw=0,y=0,legs='two'):
    a=Act(M,A,top,g,tag,x,z,yaw,y,legs); ACTS.append(a); return a
def J(M,A,top,x,z,yaw=0,tag='j_',tank=True,gun=False): return actor(M,A,top,human(M,tag,'jarvis',tank=tank,gun=gun),tag,x,z,yaw)
def H(M,A,top,kind,x,z,yaw=0,tag=None,s=1.0): tag=tag or kind[0]+'_'; return actor(M,A,top,human(M,tag,kind,s),tag,x,z,yaw)
def TW(M,A,top,x,z,yaw=0,tag='t_',gun=False,s=1.0): return actor(M,A,top,tweel(M,tag,s,gun=gun),tag,x,z,yaw)

STICK_PITCH=135; STICK_Y=30
def leap(tw,t0,t1,x,z,h=90,stick=0.0,face=True):
    """트윌의 도약: 창처럼 몸을 눕혀 날아가 부리로 내려앉음. stick>0 이면 부리를 꽂고 그만큼 머묾"""
    A=tw.A; root=tw.g
    if face: tw.look(max(0,t0-0.2),x,z,0.2)
    tw.hold(t0); x0,_,z0=tw.cur; tm=(t0+t1)/2
    tw.pk.append((tm,((x0+x)/2,h,(z0+z)/2),'catmullrom')); tw.pk.append((t1,(x,STICK_Y,z),'catmullrom'))
    te=t1+stick; tw.pk.append((te,(x,STICK_Y,z),'linear')); tw.pk.append((te+0.35,(x,0,z),'linear')); tw.cur=(x,0,z)
    tw.yk.append((te+0.35,tw.yaw))
    A.add(root,'rotation',[(max(0,t0-0.01),(0,0,0)),(t0+(tm-t0)*0.5,(60,0,0)),(tm,(95,0,0)),(t1,(STICK_PITCH,0,0)),(te,(STICK_PITCH,0,0)),(te+0.35,(0,0,0))],'linear')
    return tw
def puff(M,A,top,x,y,z,t0,dur=1.2,n=6,col='smoke_l',spread=16,rise=18,size=5,seed=0):
    """먼지·김: 작은 상자들이 퍼지며 사라짐"""
    r=random.Random(seed+int(x)+int(z))
    for i in range(n):
        s=size*r.uniform(0.6,1.3); g=M.group(f'puff{len(top)}_{i}',[x,y,z],[M.cube('puff',[x-s,y-s,z-s],[x+s,y+s,z+s],col)]); top.append(g)
        dx=r.uniform(-spread,spread); dz=r.uniform(-spread,spread); dy=r.uniform(rise*0.4,rise)
        A.add(g,'position',[(0,(0,0,0)),(t0,(0,0,0)),(t0+dur,(-dx,dy,dz))])
        A.add(g,'scale',[(0,(0,0,0)),(max(0,t0-0.02),(0,0,0)),(t0,(0.3,0.3,0.3)),(t0+dur*0.4,(1,1,1)),(t0+dur,(0.05,0.05,0.05)),(t0+dur+0.02,(0,0,0))])
def smoke_col(M,A,top,x,y,z,t0,t1,per=2.4,n=5,col='smoke',rise=90,size=7):
    """피어오르는 연기 기둥 (t0~t1 동안 되풀이)"""
    for i in range(n):
        s=size*(0.8+0.15*i); g=M.group(f'smk{len(top)}_{i}',[x,y,z],[M.cube('smk',[x-s,y-s,z-s],[x+s,y+s,z+s],col if i%2 else 'smoke_l')]); top.append(g)
        pp=[(0,(0,0,0))]; sc=[(0,(0,0,0))]; t=t0+per*i/n
        while t<t1:
            pp+= [(t,(0,0,0)),(t+per*0.98,(-(i%3-1)*12,rise,(i%2)*10))]; sc+= [(max(0.01,t-0.02),(0,0,0)),(t,(0.4,0.4,0.4)),(t+per*0.5,(1.2,1.2,1.2)),(t+per*0.98,(0.1,0.1,0.1)),(t+per,(0,0,0))]; t+=per
        A.add(g,'position',pp); A.add(g,'scale',sc)
def flicker(A,g,t0,t1,per=0.3):
    cyc(A,g,'scale',t0,t1,(1,1,1),(0.8,1.25,0.8),per,rest=(1,1,1),interp='linear')
def night(M,A,top,spans,n=150,seed=5):
    st=stars(M,'stars',n,seed); mo=moons(M,'moons'); top+= [st,mo]; vis(A,st,spans); vis(A,mo,spans)
def save(M,A,top,name,key,info=None):
    for a in ACTS: a.finish()
    ACTS.clear(); A.bake(top); nfix=겹침면_검사.fix(M.els,top)        # 같은 높이로 겹친 면 → 두께를 달리함 (색이 번갈아 바뀌는 깜박임 방지)
    M.save(f'{OUT}/{key}_{name}.bbmodel',top,[A.json()],name=key); print(key,name,len(M.els),'상자, 겹침 고침',nfix)
    return info or {}
def newset(tex=1024):
    M=BigModel(tex); M.big('cover',128,160,cover_art); mars_palette(M); world_palette(M); return M,Anim(L)

# =====================================================================
#  S : 우주 — 화성으로 가는 아레스호 · 끝 장면(와인바움 구덩이)
# =====================================================================
def set_S():
    M,A=newset(); top=[]
    top.append(stars(M,'st_far',260,seed=3,zfar=3200,spread=5200,ymin=-2600,ymax=2600))
    r=random.Random(8)
    for i in range(70):     # 가까운 별 (깊이감)
        x=r.uniform(-2600,2600); y=r.uniform(-1500,1500); z=r.uniform(900,2600); s=r.choice([3,4,6])
        top.append(M.cube('star_n',[x-s,y-s,z-s],[x+s,y+s,z+s],'star' if i%3 else 'star_b'))
    mars=globe(M,'mars',0,0,1500,520); top.append(mars); A.add(mars,'rotation',[(0,(0,0,8)),(L,(0,0,8))])
    top.append(globe(M,'phobos_g',-760,330,1150,34,cols=('rk','rk_d','rk_g'),ice=False,seed=5,step=8))
    top.append(globe(M,'deimos_g',820,-260,1250,22,cols=('rk_g','rk','rk_d'),ice=False,seed=6,step=6))
    top.append(globe(M,'earth_g',1500,820,2600,60,cols=('m_b','m_g','star'),ice=True,seed=7,step=10))
    top.append(globe(M,'sun_g',-2300,1100,3000,150,cols=('fl1','fl3','fl1'),ice=False,seed=9,step=22))
    # 구덩이 표시 (끝 장면): 화성 앞면의 둥근 테 + 깜박이는 점
    cx,cy,cz=-150,-110,1500-492
    ring=[M.cube('crater_in',[cx-44,cy-44,cz-3],[cx+44,cy+44,cz+4],'mars2')]
    for i in range(12):
        a=i/12*6.283; ring.append(M.cube('crater_rim',[cx+58*math.cos(a)-11,cy+58*math.sin(a)-11,cz-8],[cx+58*math.cos(a)+11,cy+58*math.sin(a)+11,cz+3],'mars3'))
    top.append(M.group('crater',[cx,cy,cz],ring))
    mk=M.group('mark',[cx,cy,cz-14],[M.cube('mark',[cx-9,cy-9,cz-16],[cx+9,cy+9,cz-8],'mark'), M.cube('mark',[cx-3,cy-80,cz-14],[cx+3,cy-64,cz-10],'mark'), M.cube('mark',[cx-3,cy+64,cz-14],[cx+3,cy+80,cz-10],'mark'),
        M.cube('mark',[cx-80,cy-3,cz-14],[cx-64,cy+3,cz-10],'mark'), M.cube('mark',[cx+64,cy-3,cz-14],[cx+80,cy+3,cz-10],'mark')]); top.append(mk)
    iw=I('그의 이름이 붙은 구덩이'); vis(A,mk,[(T(iw)+0.6,L)]); cyc(A,mk,'scale',T(iw)+0.7,L,(3.2,3.2,1),(4,4,1),1.2,rest=(3.2,3.2,1))
    # 아레스호 (비스듬히 화성 쪽으로)
    ar=ares(M,'ar_'); fl=M.group('ar_flame',[0,6,0],[M.cube('fl',[-14,-40,-14],[14,8,14],'fl2'), M.cube('fl',[-9,-90,-9],[9,-36,9],'fl1'), M.cube('fl',[-4,-130,-4],[4,-86,4],'fl3')]); ar['children'].append(fl)
    flicker(A,fl,0,L,0.25)
    hold=M.group('ar_tilt',[0,160,0],[ar]); A.add(hold,'rotation',[(0,(55,0,38)),(L,(55,0,38))])
    ia=I('가까운 미래'); ib=I('구십 년 전에 쓰인')
    a=actor(M,A,top,hold,'ar_',900,-900,0,y=-620); a.at(T(ib),820,-820,y=-560); a.go(T(ib),T(ia),640,-520,y=-420,walk=False,face=False); a.go(T(ia),E(ia)+1.5,220,300,y=-120,walk=False,face=False); a.show([(0,E(ia)+2)])
    # 샷
    sh('우주로',  'S',ib,ia,two([150,60,-1500],[60,0,600],[110,40,-1250],[40,0,700]),SPACE)
    sh('아레스호','S',ia,ia+1,cam((0,[760,-420,-1000],[620,-420,-500]),(0.5,[520,-300,-900],[420,-270,-100]),(1,[300,-60,-520],[150,-100,600])),SPACE,fps=24)
    num(ia,'21세기 · 인류의 첫 화성 탐사선 아레스호')
    sh('구덩이',  'S',iw,iw+1,two([-150,-60,-600],[-150,-110,1000],[-150,-90,-150],[-150,-110,1000]),SPACE)
    sh('친구의별','S',iw+1,999,two([-150,-90,-150],[-150,-110,1000],[260,160,-1900],[0,0,1200]),SPACE)
    num(iw,'화성의 와인바움 구덩이(크레이터)')
    return save(M,A,top,'우주','S')

# =====================================================================
#  X : 전시실 (들어가며) — 1934년 잡지 · 옛 소설의 외계인 두 가지 · 트윌
# =====================================================================
def set_X():
    M,A=newset(); top=hall(M)
    i0=I('천구백삼십사 년'); i_two=I('대개 두 가지'); i_mon=I('지구를 빼앗으러 온'); i_new=I('전혀 다른 외계인'); i_smart=I('사람만큼 똑똑하지만'); i_asi=I('아이작 아시모프'); i_end=I('구십 년 전에 쓰인')
    top.append(magazine(M,'mag_',0,-150,1.3)); top+= pedestal(M,0,-150,90,6,'magped')
    top+= pedestal(M,190,40,60,18)+pedestal(M,-190,40,60,18)+pedestal(M,0,130,64,26)+barrier(M,-300,300,-40)
    mon=dream_beast(M,'d_',2.6); mv=actor(M,A,top,mon,'d_',190,40,0,y=18,legs=None)
    for i in range(6): cyc(A,find(mon,f'd_arm{i}'),'rotation',0,T(i_end),((i%2*2-1)*10,0,(i%3-1)*10),(-(i%2*2-1)*10,0,-(i%3-1)*10),1.6+i*0.2,rest=(0,0,0))
    al=H(M,A,top,'alien',-190,40,0,tag='al_',s=1.6); al.at(0,-190,40,0,y=18); al.arm('r',T(i_mon)+2.2,E(i_mon),rx=-150,rz=-20)
    tw=TW(M,A,top,0,130,0,s=1.8); tw.at(0,0,130,0,y=26); tw.show([(T(i_new)+0.5,L)])
    grow(A,tw.g,T(i_new)+0.5,T(i_new)+1.3,axis='all')
    tw.tilt(T(i_smart)+0.5,E(i_smart),rz=18); cyc(A,tw.part('beak'),'rotation',T(i_new)+1.5,T(i_end),(0,14,0),(0,-14,0),2.4,rest=(0,0,0))
    tw.arm('l',T(i_asi)+0.5,E(i_asi),rx=-60)
    # 구경꾼 (읽는 사람들): 아시모프 문단에서 잡지 앞에 모여듦
    for k,(kind,x) in enumerate([('putz',70),('leroy',-80),('harrison',140),('fancy',-150)]):
        p=H(M,A,top,kind,x*3,-520,0,tag=f'r{k}_',s=0.95 if kind!='leroy' else 0.88); p.show([(T(i_asi)-0.1,L)])
        p.at(T(i_asi)-0.05,x*2.2,-470,180); p.go(T(i_asi)+0.2,T(i_asi)+3.0+k*0.3,x,-250,per=0.8); p.nod(T(i_asi)+3.5,T(i_end),8,1.1+k*0.1)
    sh('잡지',    'X',0,i0+1,two([0,150,-520],[0,100,0],[0,95,-330],[0,85,-150]),HALLBG)
    sh('제목',    'X',i0+1,i_two,two([-40,90,-290],[0,80,-150],[-12,84,-235],[0,80,-150]),HALLBG)
    sh('두가지',  'X',i_two,i_mon,two([0,120,-330],[0,60,60],[0,100,-250],[0,55,60]),HALLBG)
    sh('괴물','X',i_mon,(i_mon,2.3),orbit((190,40),190,70,-50,10,(190,50,40),r1=150),HALLBG)
    sh('분장사람','X',(i_mon,2.3),i_new,orbit((-190,40),180,70,40,-20,(-190,52,40),r1=140),HALLBG)
    sh('트윌등장','X',i_new,i_smart,cam((0,[90,120,-110],[0,70,130]),(1,[26,84,-10],[0,74,130])),HALLBG,fps=24)
    sh('트윌얼굴','X',i_smart,i_asi,orbit((0,130),110,92,-40,35,(0,84,130),r1=84),HALLBG)
    sh('독자들',  'X',i_asi,i_end,cam((0,[230,150,-520],[0,60,-170]),(1,[90,70,-400],[0,62,-190])),HALLBG)
    num(i0,'1934년 7월 · 미국 잡지 『원더 스토리스』'); num(i0+1,'스탠리 G. 와인바움 「화성의 오디세이」')
    return save(M,A,top,'전시실','X')

# =====================================================================
#  Y : 전시실 (숨은 뜻) — 화성 생물 넷 · 친구와 친구 아닌 것 · 작가
# =====================================================================
def set_Y():
    M,A=newset(); top=hall(M)
    i0=I('화성 생물이 넷'); iP=I('생각이 없는 생명'); iD=I('남의 생각을 훔쳐'); iB=I('끝내 알 수 없는'); iT=I('친구가 될 수 있는 생명'); i4=I('네 단계로')
    iF=I('또렷하게 말했습니다'); iN=I('하지만 친구가 아니었습니다'); iW=I('예닐곱 개밖에'); iY=I('하지만 친구였습니다'); iS=I('말을 잘 따라 한다고'); iM=I('기계와 함께 사는')
    iA=I('처음 발표한'); iDie=I('서른세 살'); iV=I('천구백칠십 년'); i2=I('둘째 자리'); iEnd=I('그의 이름이 붙은 구덩이')
    xs=[255,85,-85,-255]
    for x in xs: top+= pedestal(M,x,60,58,20)
    top+= barrier(M,-340,340,-30)
    pb=actor(M,A,top,pyramid_beast(M,'y_',2.0),'y_',xs[0],60,0,y=20,legs=None)
    arm=find(pb.g,'y_arm'); cyc(A,arm,'rotation',T(iP),E(iP),(0,0,0),(0,0,-40),2.0,rest=(0,0,0))
    for j in range(4):
        b=M.group(f'ybrick{j}',[xs[0]-12+j*9,20,34],[M.cube('brick',[xs[0]-26+j*9,20,31],[xs[0]-18+j*9,24,37],'brick')]); top.append(b); grow(A,b,T(iP)+0.6+j*0.9,T(iP)+0.9+j*0.9,axis='all')
    db=dream_beast(M,'d_',2.4); actor(M,A,top,db,'d_',xs[1],60,0,y=20,legs=None)
    for i in range(6): cyc(A,find(db,f'd_arm{i}'),'rotation',T(i0),T(iA),((i%2*2-1)*10,0,(i%3-1)*10),(-(i%2*2-1)*10,0,-(i%3-1)*10),1.6+i*0.2,rest=(0,0,0))
    bb=actor(M,A,top,barrel_being(M,'b_',2.0),'b_',xs[2],60,0,y=20,legs='four')
    drum=find(bb.g,'b_body')
    for t0,t1 in ((T(iB)+0.5,E(iB)),(T(iF)+2.5,E(iF))): cyc(A,drum,'scale',t0,t1,(1,1,1),(1.04,0.96,1.04),0.22,rest=(1,1,1),interp='linear')
    tw=TW(M,A,top,xs[3],60,0,s=1.8); tw.at(0,xs[3],60,0,y=20); tw.tilt(T(iT)+0.4,E(iT),16); tw.arm('r',T(iY)+0.2,E(iY),rx=-70); tw.arm('l',T(iY)+0.2,E(iY),rx=-70)
    cyc(A,tw.part('beak'),'rotation',T(i0),T(iA),(0,12,0),(0,-12,0),2.6,rest=(0,0,0))
    # 말풍선: 통 생물 = 반듯한 글 줄(또렷한 말) / 트윌 = 삐뚤빼뚤 몇 점
    def bubble(tag,x,lines,spans):
        k=[M.cube('bub',[x-34,112,52],[x+34,150,58],'th'), M.cube('bub_t',[x-5,102,52],[x+5,112,58],'th')]
        for (dx,dy,w) in lines: k.append(M.cube('bub_ink',[x+dx-w/2,118+dy,50.5],[x+dx+w/2,123+dy,52.5],'ink'))
        g=M.group(tag,[x,112,55],k); top.append(g); vis(A,g,spans); return g
    bubble('bub_b',xs[2],[(0,20,52),(0,10,52),(0,0,52)],[(T(iF)+2.3,T(iW)-0.06)])
    bubble('bub_t',xs[3],[(-14,18,10),(8,8,14),(-4,-2,8)],[(T(iW)+0.4,T(iS)-0.06)])
    xno=M.group('xno',[xs[2],132,46],[M.cube('xno',[xs[2]-22,128,45],[xs[2]+22,136,49],'red')]); top.append(xno); vis(A,xno,[(T(iN)+0.3,T(iW)-0.06)])
    A.add(xno,'rotation',[(0,(0,0,35)),(L,(0,0,35))])
    hrt=M.group('heart',[xs[3],175,56],[M.cube('h',[xs[3]-12,168,54],[xs[3]+12,180,58],'red'), M.cube('h',[xs[3]-12,180,54],[xs[3]-2,186,58],'red'), M.cube('h',[xs[3]+2,180,54],[xs[3]+12,186,58],'red'), M.cube('h',[xs[3]-6,162,54],[xs[3]+6,168,58],'red')]); top.append(hrt)
    vis(A,hrt,[(T(iY)+0.3,T(iS)-0.06)]); cyc(A,hrt,'scale',T(iY)+0.3,T(iS),(1,1,1),(1.2,1.2,1),0.8,rest=(1,1,1))
    # 기계 (말을 그럴듯하게 하는 기계): 작은 상자 로봇이 걸어 나옴
    rb=M.group('rb_root',[0,0,0],[M.cube('rb_body',[-8,8,-6],[8,26,6],'steel'), M.cube('rb_head',[-6,26,-5],[6,36,5],'hull'), M.cube('rb_eye',[-4,30,-5.6],[4,33,-5],'win'),
        M.cube('rb_mouth',[-3,27.4,-5.6],[3,28.4,-5],'ink'), M.cube('rb_ant',[-0.6,36,-0.6],[0.6,42,0.6],'jet'), M.cube('rb_antb',[-1.5,42,-1.5],[1.5,45,1.5],'hull_r'),
        M.cube('rb_l1',[-6,0,-3],[-2,8,3],'steel_d'), M.cube('rb_l2',[2,0,-3],[6,8,3],'steel_d'), M.cube('rb_a1',[8,12,-2],[11,24,2],'steel_d'), M.cube('rb_a2',[-11,12,-2],[-8,24,2],'steel_d')])
    ra=actor(M,A,top,rb,'rb_',-420,-300,0,legs=None); ra.show([(T(iM)-0.1,T(iA))]); ra.go(T(iM),T(iM)+3.5,0,-150,walk=False); ra.turn(T(iM)+3.6,0,0.4)
    rbub=bubble('bub_r',0,[(0,20,52),(0,10,52),(0,0,40)],[(T(iM)+4.2,T(iA))]); move(M,rbub,0,-58,-205)
    # 작가의 자리: 책상·타자기·빈 의자 + 잡지 (왼쪽 앞)
    dx,dz=250,-250
    desk=[M.cube('desk',[dx-46,26,dz-22],[dx+46,30,dz+22],'wood'), M.cube('dleg',[dx-44,0,dz-20],[dx-40,26,dz-16],'wood_d'), M.cube('dleg',[dx+40,0,dz-20],[dx+44,26,dz-16],'wood_d'),
          M.cube('dleg',[dx-44,0,dz+16],[dx-40,26,dz+20],'wood_d'), M.cube('dleg',[dx+40,0,dz+16],[dx+44,26,dz+20],'wood_d'),
          M.cube('tw_base',[dx-12,30,dz-8],[dx+12,36,dz+8],'jet'), M.cube('tw_keys',[dx-10,36,dz-9],[dx+10,38,dz-3],'hull_d'), M.cube('tw_roll',[dx-13,38,dz+2],[dx+13,42,dz+6],'ink'), M.cube('tw_paper',[dx-8,40,dz+3],[dx+8,56,dz+4],'paper'),
          M.cube('pile',[dx+22,30,dz-10],[dx+40,35,dz+10],'paper'), M.cube('dlamp_p',[dx-38,30,dz+8],[dx-36,50,dz+10],'rod'), M.cube('dlamp',[dx-42,48,dz+2],[dx-30,54,dz+14],'lamp'),
          M.cube('chair',[dx-12,14,dz-48],[dx+12,17,dz-26],'wood_d'), M.cube('chair_b',[dx-12,17,dz-48],[dx+12,44,dz-45],'wood_d'), M.cube('cleg',[dx-11,0,dz-47],[dx-8,14,dz-44],'wood_d'), M.cube('cleg',[dx+8,0,dz-47],[dx+11,14,dz-44],'wood_d'),
          M.cube('cleg',[dx-11,0,dz-29],[dx-8,14,dz-26],'wood_d'), M.cube('cleg',[dx+8,0,dz-29],[dx+11,14,dz-26],'wood_d')]
    top+= desk; top.append(magazine(M,'mag_',dx+110,dz+40,0.9))
    # 투표 단상 (오른쪽 앞): 1·2·3 단, 2단 위에 잡지
    px,pz=-270,-240
    top+= [M.cube('pod1',[px-20,0,pz-20],[px+20,44,pz+20],'ped'), M.cube('pod2',[px+20,0,pz-20],[px+60,30,pz+20],'ped'), M.cube('pod3',[px-60,0,pz-20],[px-20,20,pz+20],'ped'),
           M.cube('pod_t',[px-62,0,pz-22],[px+62,3,pz+22],'gold_f'), M.cube('n1',[px-3,18,pz-21],[px+3,36,pz-20],'gold_f'),
           M.cube('n2',[px+33,8,pz-21],[px+37,22,pz-20],'gold_f'), M.cube('n2',[px+43,8,pz-21],[px+47,22,pz-20],'gold_f'),
           M.cube('n3',[px-49,4,pz-21],[px-47,14,pz-20],'gold_f'), M.cube('n3',[px-42,4,pz-21],[px-40,14,pz-20],'gold_f'), M.cube('n3',[px-35,4,pz-21],[px-33,14,pz-20],'gold_f')]
    m2=magazine(M,'mag2_',px+40,pz,0.55,y=30); top.append(m2); grow(A,m2,T(i2)+0.2,T(i2)+1.0,axis='all')
    bk=M.group('book1st',[px,44,pz],[M.cube('bk',[px-12,44,pz-3],[px+12,74,pz+3],'book2'), M.cube('bk_s',[px-8,62,pz-3.6],[px+8,66,pz-3],'gold_f')]); top.append(bk)
    cyc(A,m2,'position',T(i2)+1.2,E(i2)+1.5,(0,0,0),(0,5,0),1.0,rest=(0,0,0))
    # 샷
    sh('넷',      'Y',i0-1,iP,cam((0,[0,40,-420],[0,60,60]),(1,[0,170,-330],[0,60,60])),HALLBG)
    sh('쌓는것',  'Y',iP,iD,orbit((xs[0],60),170,84,-45,20,(xs[0],52,60),r1=140),HALLBG)
    sh('꿈보여',  'Y',iD,iB,orbit((xs[1],60),170,90,35,-30,(xs[1],56,60),r1=135),HALLBG)
    sh('수레미는','Y',iB,iT,orbit((xs[2],60),175,80,-40,30,(xs[2],48,60),r1=135),HALLBG)
    sh('트윌',    'Y',iT,i4,orbit((xs[3],60),175,96,40,-30,(xs[3],62,60),r1=130),HALLBG)
    sh('네단계',  'Y',i4,iF,two([330,120,-330],[0,56,60],[-330,120,-330],[0,56,60]),HALLBG)
    sh('또렷한말','Y',iF,iW,two([xs[2]+10,90,-150],[xs[2],88,60],[xs[2]+4,96,-110],[xs[2],92,60]),HALLBG)
    sh('여섯마디','Y',iW,iS,two([xs[3]-10,96,-150],[xs[3],96,60],[xs[3]-4,104,-110],[xs[3],104,60]),HALLBG)
    sh('둘나란히','Y',iS,iM,orbit((-170,60),330,90,-22,22,(-170,62,60),r1=290),HALLBG)
    sh('기계',    'Y',iM,iA,two([-110,60,-330],[-30,34,-170],[40,50,-250],[0,36,-170]),HALLBG,fps=24)
    sh('작가자리','Y',iA,iDie,two([dx-90,100,dz-190],[dx+20,44,dz],[dx-50,80,dz-150],[dx+20,44,dz]),HALLBG)
    sh('빈의자',  'Y',iDie,iV,two([dx-10,60,dz-130],[dx,34,dz-20],[dx-4,70,dz-170],[dx,34,dz-20]),HALLBG)
    sh('투표',    'Y',iV,i2,two([px+90,90,pz-200],[px,36,pz],[px+40,70,pz-150],[px,36,pz]),HALLBG)
    sh('둘째',    'Y',i2,iEnd,two([px+60,66,pz-110],[px+40,50,pz],[px+48,62,pz-80],[px+40,52,pz]),HALLBG)
    num(iA,'스탠리 G. 와인바움 (1902~1935)'); num(iDie,'1935년 12월 · 발표 뒤 일 년 반이 못 되어'); num(iV,'1970년 · 미국 SF 작가 협회 투표'); num(i2,'1위는 아시모프 「전설의 밤」')
    num(iP,'① 생각이 없는 생명'); num(iD,'② 남의 생각을 훔쳐 쓰는 생명'); num(iB,'③ 생각은 하지만 알 수 없는 생명'); num(iT,'④ 다르게 생각하지만 친구가 되는 생명')
    return save(M,A,top,'전시실끝','Y')

# =====================================================================
#  A : 착륙지 (잿빛 평원, 아레스호) — 대원 넷 · 보조 로켓 출발 · 끝(돌아온 자비스, 수정)
# =====================================================================
def set_A():
    M,A=newset(); G=('g1','g2','g3')
    top=[far_ground(M,'g2')]+tiles(M,-768,768,-768,768,cols=G,seed=2)
    top+= cliff_line(M,1250,-2600,2600,130,seed=11)+cliff_line(M,1900,-3000,3000,240,seed=17)
    top+= dune(M,-520,420,360,200,30,cols=G)+dune(M,560,520,420,220,38,cols=G)+dune(M,-80,700,500,200,26,cols=G)
    top+= patches(M,-700,700,-700,500,22,col='g_d',seed=4)+pebbles(M,-600,600,-650,300,70,seed=3,cols=('rk_g','g_d','rk_d'))
    for i,(x,z,s) in enumerate([(-330,-180,16),(380,-240,20),(520,60,26),(-560,120,22),(210,330,18),(-250,380,24),(640,-420,16),(-640,-380,20)]): top+= rock(M,x,z,s,'rk_g',seed=i)
    top+= crater(M,-420,-420,46,'g_d','g3')+crater(M,470,300,60,'g_d','g3')
    av=[(0,150,200,220),(-240,-110,90,90),(250,-90,90,90),(0,-170,140,80)]
    top+= stumps(M,-720,720,-700,620,46,seed=6,avoid=av)+grass(M,-600,600,-640,200,160,seed=7,avoid=av)
    top.append(ares(M,'ar_',0,160))
    # 야영 물건: 상자·천막·깃대·등
    for i,(x,z,w,h,col) in enumerate([(120,-10,24,18,'wood'),(146,-4,18,14,'hull_d'),(128,-12,14,10,'hull_r'),(-130,10,26,20,'wood'),(-156,0,16,16,'steel'),(-118,-14,12,12,'wood_d')]):
        top.append(M.cube('crate',[x-w/2,0 if i not in (2,) else 18,z-w/2],[x+w/2,(h if i!=2 else 28),z+w/2],col))
    for j in range(4): top.append(M.cube('tent',[-330+j*9,j*12,60+j*9],[-210-j*9,(j+1)*12,180-j*9],'hull' if j%2 else 'hull_d'))
    top+= [M.cube('tent_d',[-284,0,58],[-256,26,61],'jet'), M.cube('mast',[300,0,110],[303,150,113],'jet'), M.cube('mast_d',[290,150,104],[314,154,120],'hull_d'), M.cube('flag',[303,118,111],[340,140,112.5],'hull_r')]
    lamps=[]
    for x,z in ((90,-70),(-90,-70),(200,40),(-200,40)):
        top.append(M.cube('lpost',[x-1.5,0,z-1.5],[x+1.5,44,z+1.5],'jet')); lamps.append(M.cube('lhead',[x-5,44,z-5],[x+5,52,z+5],'lamp'))
    top.append(M.group('lamps',[0,0,0],lamps))
    iC=I('대원은 네 명'); iGo=I('보조 로켓을 타고'); iFar=I('천삼백 킬로미터'); iBack=I('아레스호에 돌아온'); iCap=I('대장이 아쉬워합니다'); iPk=I('주머니에서 반짝이는'); iHere=I('여기 있어'); iNext=I('화성 생물이 넷')-1
    night(M,A,top,[(T(iBack)-0.2,L)])
    # 대원 넷 (왼쪽부터 화면: 해리슨·푸츠·르루아·자비스 → x 큰 쪽이 화면 왼쪽)
    ha=H(M,A,top,'harrison',66,-150,0); pu=H(M,A,top,'putz',22,-150,0); le=H(M,A,top,'leroy',-22,-150,0,s=0.88); ja=J(M,A,top,-66,-150,0,tank=False)
    for k,p in enumerate((ha,pu,le,ja)): p.arm('r',T(iC)+1.2+k*1.5,T(iC)+2.4+k*1.5,rx=-150,rz=(-18 if k<3 else -18))
    ja.show([(0,T(iGo)+2.0),(T(iBack)-0.2,L)]); ja.go(T(iGo)+0.3,T(iGo)+2.0,-232,-112,per=0.7)
    # 보조 로켓 둘: 자비스 것(화면 오른쪽 = -x)이 떠서 남쪽(+z)으로
    r1=actor(M,A,top,aux_rocket(M,'r1_'),'r1_',-240,-110,180,legs=None); r2=actor(M,A,top,aux_rocket(M,'r2_'),'r2_',250,-90,180,legs=None)
    for r in (r1,r2): vis(A,r.part('flame'),[]) if r is r2 else None
    vis(A,r2.part('under'),[]); vis(A,r2.part('flame'),[])
    t1=T(iGo)+2.4; vis(A,r1.part('under'),[(t1,t1+3.2)]); vis(A,r1.part('flame'),[(t1+1.6,T(iFar))]); flicker(A,r1.part('under'),t1,t1+3.2,0.2); flicker(A,r1.part('flame'),t1+1.6,T(iFar),0.2)
    r1.go(t1,t1+2.0,-240,-110,y=90,walk=False,face=False,interp='catmullrom'); r1.go(t1+2.0,T(iFar),-420,1900,y=420,walk=False,face=False,interp='catmullrom')
    r1.show([(0,T(iFar)),(T(iBack)-0.2,L)]); r1.at(T(iBack)-0.2,-240,-110,180)
    puff(M,A,top,-240,4,-110,t1,1.6,10,'smoke_l',40,14,7)
    for p,sgn in ((ha,-1),(pu,-1),(le,-1)): p.headturn(T(iGo)+2.6,T(iFar)-0.3,ry=-55)
    # 끝: 밤, 넷이 다시 모임 — 자비스가 이야기를 마치고 수정을 꺼냄
    tB=T(iBack)-0.2
    ha.at(tB,70,-170,-70); pu.at(tB,40,-120,-50); le.at(tB,-10,-112,10); ja.at(tB,-52,-165,75)
    ja.nod(T(iBack)+0.3,E(iBack),8,0.9); ha.arm('l',T(iCap)+0.4,E(iCap)-0.3,rx=-55); ha.nod(T(iCap)+0.4,E(iCap),8,0.8)
    cr=M.group('j_crys',[-6,11,-3],[M.cube('crys',[-7.6,9.6,-4.6],[-4.4,12.8,-1.4],'crystal'), M.cube('crys_g',[-8.4,10.4,-5.4],[-3.6,12,-0.6],'crystal')]); ja.part('arm_right')['children'].append(cr)
    vis(A,cr,[(T(iPk)+0.9,L)]); cyc(A,cr,'scale',T(iPk)+0.9,L,(1,1,1),(1.3,1.3,1.3),0.7,rest=(1,1,1))
    ja.arm('r',T(iPk)+0.3,T(iNext),rx=-75)
    for p in (ha,pu,le): p.tilt(T(iPk)+1.4,T(iNext)-0.2,rz=8)
    top+= [M.cube('firelog',[-6,0,-140],[6,3,-134],'fire_w')]
    cf,fl=campfire(M,'cf_',0,-150); top.append(cf); vis(A,cf,[(tB,L)]); flicker(A,fl,tB,L,0.3)
    # 샷
    sh('대원넷',  'A',iC,iGo,cam((0,[160,150,-360],[0,150,160]),(0.3,[110,40,-290],[0,30,-150]),(1,[-110,34,-270],[0,28,-150])))
    sh('출발',    'A',iGo,iFar,cam((0,[-80,40,-300],[-200,26,-110]),(0.5,[-60,50,-330],[-240,90,-110]),(1,[-40,60,-360],[-380,330,1200])),fps=24)
    sh('돌아옴',  'A',iBack,iCap,cam((0,[0,300,-330],[0,200,160]),(1,[0,46,-280],[0,28,-150])),NIGHT)
    sh('대장',    'A',iCap,iPk,two([10,34,-235],[64,30,-170],[18,32,-225],[64,30,-170]),NIGHT)
    sh('수정',    'A',iPk,iNext,cam((0,[-20,30,-232],[-52,22,-165]),(0.35,[-34,26,-212],[-56,18,-172]),(1,[110,70,-300],[0,26,-150])),NIGHT,fps=24)
    num(iC,'해리슨(대장) · 푸츠(기관사) · 르루아(생물학자) · 자비스(화학자)')
    return save(M,A,top,'착륙지','A')

# =====================================================================
#  B : 추락한 사막 (주황빛 틸레) — 엔진 꺼짐 · 처박힘 · 걸어서 돌아가기로
# =====================================================================
def set_B():
    M,A=newset()
    top=[far_ground(M,'o2')]+tiles(M,-768,768,-768,896,seed=3)
    top+= cliff_line(M,1500,-2800,2800,170,seed=21)+cliff_line(M,2200,-3200,3200,300,seed=27)
    top+= dune(M,-460,360,420,220,40)+dune(M,480,480,380,200,34)+dune(M,60,760,560,220,30)+dune(M,-620,-260,300,160,24)+dune(M,620,-320,280,170,28)
    top+= patches(M,-700,700,-700,800,26,seed=5)+pebbles(M,-650,650,-650,500,90,seed=6)
    for i,(x,z,s) in enumerate([(-300,-120,18),(330,-200,22),(470,120,28),(-520,140,24),(180,300,16),(-200,420,26),(600,-460,18),(-600,-420,20),(-120,-380,12),(260,-480,14)]): top+= rock(M,x,z,s,seed=i)
    top+= crater(M,-380,-330,50)+crater(M,400,330,70)+mesa(M,-700,620,240,200,150,seed=3)+mesa(M,760,700,260,220,190,seed=5)
    iFar=I('천삼백 킬로미터'); iCr=I('처박혔습니다'); iRa=I('무전은 닿지 않고'); iDe=I('걸어서 돌아가기로'); iTk=I('물통을 등에 지고'); iGr=I('중력이 약해서'); i60=I('육십 킬로미터'); iNx=I('첫날 해 질 무렵')-1
    # 로켓: 높이 날다 불이 꺼지고 떨어져 처박힘 (x 0, z -60 근처, 코를 모래에 박고 기욺)
    rk=aux_rocket(M,'r_'); tilt=M.group('r_tilt',[0,14,-10],[rk]); r=actor(M,A,top,tilt,'r_',700,-200,90,y=330,legs=None)
    flame=find(rk,'r_flame'); under=find(rk,'r_under'); tq=T(iFar)+(E(iFar)-T(iFar))*0.62
    vis(A,flame,[(0,tq)]); vis(A,under,[(0,tq)]); flicker(A,flame,0,tq,0.2)
    for k in range(3): A.add(flame,'scale',[(tq-0.5+k*0.15,(1,1,1)),(tq-0.43+k*0.15,(0.3,0.3,0.3))])
    r.at(T(iFar),-700,-200,90,y=330); r.go(T(iFar),tq,-150,-150,y=320,walk=False,face=False); r.go(tq,T(iCr)+0.9,20,-70,y=4,walk=False,face=False,interp='catmullrom')
    A.add(tilt,'rotation',[(0,(0,0,0)),(tq,(0,0,0)),(T(iCr)+0.5,(28,0,0)),(T(iCr)+0.9,(20,0,-14)),(T(iCr)+1.3,(16,0,-10))],'catmullrom')
    tc=T(iCr)+0.9
    puff(M,A,top,40,6,-70,tc,1.8,14,'o3',70,30,10,seed=2); puff(M,A,top,60,6,-60,tc+0.2,2.0,8,'smoke_l',50,40,8,seed=4)
    trench=M.group('trench',[-90,0,-110],[M.cube('trench',[-110,0,-124],[20,0.9,-100],'o_d'), M.cube('trench_e',[-110,0,-128],[20,3,-124],'o3'), M.cube('trench_e',[-110,0,-100],[20,3,-96],'o3')]); top.append(trench); vis(A,trench,[(tc,L)])
    smoke_col(M,A,top,70,26,-58,tc+0.6,L,per=2.6,n=7,rise=120,size=3.5)
    brk=M.group('broken',[0,0,0],[M.cube('wing_off',[-60,0,-30],[-28,3,-6],'hull_d'), M.cube('gear_off',[96,0,-120],[100,8,-116],'jet'), M.cube('bit',[110,0,-40],[116,3,-34],'hull_r'), M.cube('bit',[-10,0,-150],[-4,2,-145],'hull')]); top.append(brk); vis(A,brk,[(tc,L)])
    # 자비스
    ja=J(M,A,top,-40,-120,0,tank=False); ja.show([(T(iRa)-0.3,T(iTk)+0.4)])
    ja.at(T(iRa)-0.3,-28,-104,0); ja.arm('r',T(iRa)+0.4,E(iRa)-0.6,rx=-140,rz=-10); ja.headturn(T(iRa)+2.0,E(iRa),ry=50)
    ja.turn(T(iDe)+0.3,150,0.6); ja.arm('l',T(iDe)+1.6,E(iDe),rx=-80)
    jt=J(M,A,top,-28,-104,150,tag='k_',tank=True,gun=False); jt.show([(T(iTk)+0.4,L)])       # 물통을 진 자비스
    hol=M.group('k_gunh',[0,0,0],[M.cube('gun',[-5.6,9,-1],[-4.6,13,1],'black')]); jt.part('body')['children'].append(hol)
    jt.at(T(iTk)+0.4,-28,-104,150); jt.turn(T(iTk)+1.5,20,0.8); jt.arm('r',T(iTk)+2.6,E(iTk),rx=-40)
    jt.turn(T(iGr),180,0.4); jt.hop(T(iGr)+0.6,E(iGr)+0.4,-60,160,h=16,n=4)
    jt.go(T(i60),T(iNx)+3,-90,820,per=0.75)
    # 샷
    sh('비행',    'B',iFar,iCr,cam((0,[60,40,-190],[0,14,0],0),(0.55,[20,30,-170],[0,12,0],0.3),(1,[-40,60,-220],[0,0,0],1)),fps=24,follow='r_mv',shake=3)
    sh('처박힘',  'B',iCr,iRa,cam((0,[-170,40,-300],[10,90,-80],1),(0.25,[-160,36,-290],[20,20,-70],1),(0.5,[-150,40,-280],[20,24,-70],0.2),(1,[-90,70,-260],[20,26,-70],0)),fps=24,shake=5)
    sh('무전',    'B',iRa,iDe,two([-70,40,-230],[-10,26,-90],[-52,36,-200],[-16,26,-96]))
    sh('결심',    'B',iDe,iTk,orbit((-28,-104),100,36,-70,-160,(-28,26,-104),r1=120,h1=44))
    sh('물통',    'B',iTk,iGr,two([-110,44,-30],[-28,24,-104],[-80,36,-190],[-28,24,-104]))
    sh('가벼움',  'B',iGr,i60,cam((0,[-190,26,-40],[-40,26,-40]),(1,[-200,30,150],[-56,26,150])),fps=24)
    sh('먼길',    'B',i60,iNx,cam((0,[-70,14,-150],[-80,30,300]),(1,[-80,340,-560],[-90,60,900])))
    num(iFar,'약 1,300km (원문 800마일)'); num(iRa,'지구로 떠날 날까지 약 20일'); num(iGr,'화성의 중력 = 지구의 약 3분의 1'); num(i60,'하루 약 64km (원문 40마일)')
    return save(M,A,top,'추락사막','B')

# =====================================================================
#  C : 만남 (잿빛 평원, 절벽 아래) — 트윌 구하기 · 이름 · 모닥불 밤(말·셈·별 그림·도약) · 아침 길
# =====================================================================
def set_C():
    M,A=newset(); G=('g1','g2','g3')
    top=[far_ground(M,'g2')]+tiles(M,-896,896,-640,448,cols=G,seed=5)
    # 바로 뒤의 높은 절벽 (틸레 고원) + 그 너머
    top+= cliff_line(M,470,-1500,1500,210,seed=31,d=300,step=260)+cliff_line(M,1100,-2600,2600,330,seed=37)
    top+= dune(M,-560,160,300,150,22,cols=G)+dune(M,600,120,280,140,26,cols=G)+patches(M,-800,800,-600,300,26,col='g_d',seed=8)+pebbles(M,-800,800,-600,250,110,seed=9,cols=('rk_g','g_d','rk_d'))
    for i,(x,z,s) in enumerate([(-260,60,20),(300,90,24),(430,-260,16),(-470,-300,18),(140,170,14),(-80,230,22),(640,-80,20),(-680,-60,22),(60,-420,12)]): top+= rock(M,x,z,s,'rk_g',seed=i)
    av=[(60,-40,90,90),(-120,-90,120,90),(0,-230,260,150),(0,-140,900,50),(-330,-200,120,120)]
    top+= stumps(M,-860,860,-560,330,60,seed=12,avoid=av)+grass(M,-700,700,-560,200,220,seed=13,avoid=av)
    i1=I('첫날 해 질 무렵'); i2=I('타조를 닮은 생물'); i3=I('그냥 지나치려'); i4=I('작은 가방 하나가'); i5=I('가방을 멘다는 건'); i6=I('권총을 쏘았고'); i7=I('마주 봅니다'); i8=I('긴 목 끝에 작은 머리')
    i9=I('손가락은 네 개'); i10=I('빈 두 손을 내밀어'); i11=I('이름을 말합니다'); i12=I('생물이 따라 합니다'); i13=I('휘파람처럼')
    j1=I('여기서부터 막힙니다'); j2=I('같은 것을 두 번'); j3=I('바위도 불도'); j4=I('낱말을 하나도'); j5=I('예닐곱 개 외웠습니다'); j6=I('셈을 해 봅니다'); j7=I('둘 더하기 둘'); j8=I('태양과 행성들')
    j9=I('수성까지 알고'); j10=I('고향이라고 알려 주자'); j11=I('이십 미터 넘게'); j12=I('한가운데에 꽂힙니다'); j13=I('몇 번을 다시'); j14=I('어디까지는 통하고'); j15=I('트윌이 좋았습니다')
    j16=I('다음 날 아침'); j17=I('사오십 미터씩'); nx=I('며칠 뒤 주황빛')-1
    tN0=T(j1-1); tN1=T(j16)      # 밤 (챕터 제목부터)
    night(M,A,top,[(tN0,tN1)]); earth=M.group('earthstar',[300,900,2400],[M.cube('earth',[286,886,2400],[314,914,2410],'earth')]); top.append(earth); vis(A,earth,[(tN0,tN1)])
    cyc(A,earth,'scale',T(j10),E(j10),(1,1,1),(1.8,1.8,1),0.8,rest=(1,1,1))
    # 꿈 괴물 구덩이 + 붙잡힌 트윌
    bx,bz=60,-40
    db=dream_beast(M,'d_',1.3); be=actor(M,A,top,db,'d_',bx,bz,0,legs=None)
    for k in range(6): cyc(A,find(db,f'd_arm{k}'),'rotation',0,T(i6)+1.2,((k%2*2-1)*16,0,(k%3-1)*16),(-(k%2*2-1)*16,0,-(k%3-1)*16),0.7+k*0.08,rest=(0,0,0))
    ts=T(i6)+1.0; be.hold(ts); be.go(ts,ts+1.2,bx,bz,y=-40,walk=False,face=False); be.show([(0,ts+1.3)])
    pit=M.group('pit',[bx,0,bz],[M.cube('pit',[bx-13,0,bz-13],[bx+13,1.2,bz+13],'pit'), M.cube('pit_in',[bx-10,0.8,bz-10],[bx+10,1.6,bz+10],'hole')]); top.append(pit)
    tw=TW(M,A,top,bx-8,bz-12,-60,gun=True); vis(A,tw.part('gun'),[])
    cyc(A,tw.g,'rotation',T(i1),ts,(0,0,10),(0,0,-10),0.35,rest=(0,0,0)); cyc(A,tw.part('neck'),'rotation',T(i1),ts,(25,0,0),(-10,0,0),0.3,rest=(0,0,0))
    cyc(A,tw.part('arm_left'),'rotation',T(i1),ts,(-120,0,0),(-40,0,0),0.4,rest=(0,0,0)); cyc(A,tw.part('arm_right'),'rotation',T(i1),ts,(-40,0,0),(-120,0,0),0.4,rest=(0,0,0))
    # 자비스 (물통·권총)
    ja=J(M,A,top,-460,-150,90,gun=True); gun=ja.part('gun'); vis(A,gun,[(T(i6)+0.2,T(i7)+1.0)])
    ja.go(T(i1)-3.5,T(i1)+3.0,-200,-120,per=0.8); ja.look(T(i1)+3.2,bx,bz); ja.headturn(T(i1)+3.4,E(i1),ry=-25)
    ja.go(T(i2)+0.5,T(i2)+2.5,-130,-95,per=0.8); ja.look(T(i2)+2.6,bx,bz)
    ja.turn(T(i3)+0.4,150,0.6); ja.go(T(i3)+1.0,E(i3),-150,-125,per=0.9,face=False); ja.look(T(i4)+0.3,bx,bz,0.5)
    ja.arm('r',T(i6)+0.2,T(i7)+1.0,rx=-88)
    for k in range(3):
        t=T(i6)+0.8+k*0.25; puff(M,A,top,-118+k*2,23,-88,t,0.35,3,'fl1',6,4,2,seed=k); puff(M,A,top,bx,14,bz,t+0.1,0.6,5,'rope',16,16,3,seed=k+5)
    puff(M,A,top,bx,2,bz,ts+0.6,1.4,8,'g3',26,14,5,seed=3)
    # 풀려난 트윌: 비틀거리다 자비스를 마주 봄
    tw.go(ts+0.2,ts+1.6,bx-40,bz-30,per=0.5,amp=34,face=False); tw.look(T(i7)+0.5,-130,-95,0.6)
    cyc(A,tw.part('beak'),'rotation',T(i8),E(i8),(0,20,0),(0,-20,0),1.4,rest=(0,0,0)); tw.tilt(T(i8)+0.3,E(i8),12)
    cyc(A,tw.part('arm_left'),'rotation',T(i9)+0.2,E(i9),(-75,0,0),(-95,0,0),0.9,rest=(0,0,0))
    tw.arm('l',T(i10)+0.2,E(i10),rx=-80); tw.arm('r',T(i10)+0.2,E(i10),rx=-80)
    ja.go(T(i10)+1.5,E(i10),-90,-85,per=0.8); ja.arm('l',T(i11)+0.8,E(i11),rx=-35,rz=-40); ja.nod(T(i11)+1.6,E(i11),8,0.5)
    tw.nod(T(i12)+0.6,E(i12),14,0.5); tw.arm('l',T(i12)+0.2,E(i12),rx=-70)
    tw.A.add(tw.part('neck'),'rotation',[(T(i13),(0,0,0)),(T(i13)+0.8,(-25,0,0)),(E(i13)-0.3,(-25,0,0)),(E(i13),(0,0,0))],'catmullrom'); tw.arm('r',T(i13)+0.4,E(i13),rx=-30,rz=30)
    # --- 밤: 모닥불 (절벽 아래), 둘이 불을 사이에 두고 ---
    fx,fz=0,-200
    cf,fl=campfire(M,'cf_',fx,fz+70); top.append(cf); vis(A,cf,[(tN0,tN1)]); flicker(A,fl,tN0,tN1,0.3)
    ja.at(tN0,-60,fz+60,70); tw.at(tN0,62,fz+60,-70)
    tw.arm('r',T(j2)+0.5,E(j2),rx=-70); tw.arm('l',T(j3)+0.2,T(j3)+1.6,rx=-80,rz=40); tw.arm('r',T(j3)+1.8,E(j3),rx=-60)
    ja.tilt(T(j4)+0.3,E(j4),14); ja.arm('l',T(j4)+0.5,E(j4),rx=-30,rz=-30); tw.nod(T(j5)+0.5,E(j5),10,0.6)
    # 셈: 조약돌 2+2=4, 3+3=6
    def stones(tag,x0,z0,groups,t0,dt):
        t=t0; x=x0
        for gi,n in enumerate(groups):
            for k in range(n):
                g=M.group(f'{tag}{gi}_{k}',[x,0,z0],[M.cube('peb_c',[x-2,0,z0-2],[x+2,3,z0+2],'rk_g' if tag=='pa' else 'bulb')]); top.append(g)
                grow(A,g,t,t+0.25,hide_after=tN1,axis='all'); x+=5; t+=dt
            x+=7
    ja.at(T(j6),-34,fz+10,10); tw.at(T(j6),36,fz+10,-10)
    ja.arm('r',T(j7)+0.2,T(j7)+3.0,rx=-50); stones('pa',-44,fz-22,[2,2,4],T(j7)+0.4,0.28)
    tw.arm('l',T(j7)+3.4,E(j7),rx=-50); stones('pb',6,fz-22,[3,3,6],T(j7)+3.6,0.22)
    # 별 그림: 해·수성·금성·지구(+달)·화성(+달 둘)
    dz=fz-60
    def disc(tag,x,z,r,col,t0,pulse=None):
        g=M.group(tag,[x,0,z],[M.cube('disc',[x-r,0,z-r*0.7],[x+r,0.9,z+r*0.7],col), M.cube('disc',[x-r*0.7,0,z-r],[x+r*0.7,0.9,z+r],col)]); top.append(g); grow(A,g,t0,t0+0.35,hide_after=tN1,axis='all')
        if pulse: A.add(g,'scale',[(pulse[0],(1,1,1)),(pulse[0]+0.4,(2,1,2)),(pulse[1]-0.4,(2,1,2)),(pulse[1],(1,1,1))])
        return g
    t8=T(j8)+0.4; d8=(E(j8)-T(j8))
    disc('d_sun',0,dz,9,'fl1',t8); disc('d_mer',-17,dz+2,2.4,'rk_g',t8+0.5,pulse=(T(j9)+0.3,E(j9))); disc('d_ven',-29,dz-3,3.4,'bulb',t8+0.9); disc('d_ear',-43,dz+3,3.8,'m_b',t8+1.3); disc('d_mar',-59,dz-2,3.2,'mars1',t8+1.7)
    disc('d_ph',-63,dz-8,1.1,'moon',t8+d8*0.55); disc('d_de',-56,dz-9,1.0,'moon',t8+d8*0.65); disc('d_mo',-47,dz+10,1.3,'moon',t8+d8*0.8)
    ja.at(T(j8),-70,dz+40,0); tw.at(T(j8),40,dz+34,-30); ja.arm('r',T(j8)+0.3,T(j8)+d8*0.5,rx=-45); tw.go(T(j8)+d8*0.45,T(j8)+d8*0.55,-36,dz+34,per=0.5); tw.arm('l',T(j8)+d8*0.55,E(j8),rx=-50)
    ja.arm('r',T(j10)+0.4,E(j10),rx=-150,rz=-20); ja.A.add(ja.part('head'),'rotation',[(T(j10),(0,0,0)),(T(j10)+0.5,(-28,0,0)),(E(j10),(-28,0,0)),(E(j10)+0.3,(0,0,0))])
    # 트윌: 제 몸과 별을 번갈아 가리키더니 뛰어오름 → 해 그림 한가운데에 부리로 꽂힘
    cyc(A,tw.part('arm_left'),'rotation',T(j11)+0.2,T(j11)+2.4,(-160,0,0),(-30,0,30),0.7,rest=(0,0,0))
    tL=T(j11)+2.6
    leap(tw,tL,E(j12)-1.9,0,dz,h=330,stick=1.7,face=False)
    puff(M,A,top,0,2,dz,E(j12)-1.9,0.9,8,'g3',22,12,3,seed=6)
    ja.A.add(ja.part('head'),'rotation',[(tL,(0,0,0)),(tL+0.8,(-40,0,0)),(E(j12)-2.2,(-40,0,0)),(E(j12)-1.7,(10,0,0)),(E(j12),(10,0,0)),(E(j12)+0.3,(0,0,0))])
    tw.go(T(j13)+0.2,T(j13)+0.9,36,dz+30,per=0.4); leap(tw,T(j13)+1.2,T(j13)+2.4,0,dz,h=160,stick=0.9)
    puff(M,A,top,0,2,dz,T(j13)+2.4,0.8,6,'g3',20,10,3,seed=7)
    ja.at(T(j14),-60,fz+60,70); tw.at(T(j14),62,fz+60,-70); ja.tilt(T(j14)+0.5,E(j14),-10); tw.tilt(T(j14)+1.0,E(j14),12)
    ja.nod(T(j15)+0.4,E(j15),6,1.0); cyc(A,tw.part('beak'),'rotation',T(j15),E(j15),(0,12,0),(0,-12,0),1.6,rest=(0,0,0))
    # --- 아침: 북쪽(화면 왼쪽 = +x)으로. 트윌은 뛰어 앞서 갔다가 돌아옴 ---
    ja.at(tN1,-260,-140,90); tw.at(tN1,-330,-150,90)
    ja.go(T(j16)+0.3,T(nx)+4.5,520,-140,per=0.8)
    tw.go(T(j16)+1.0,E(j16),-150,-165,per=0.5)
    t=T(j17)+0.2; leap(tw,t,t+1.6,170,-160,h=90,stick=0.5); t+=2.6; leap(tw,t,t+1.5,-40,-170,h=80,stick=0.4); t+=2.5; leap(tw,t,min(t+1.6,T(nx)+3.6),330,-160,h=95,stick=0.5)
    # 샷
    sh('해질무렵','C',i1-1,i2,cam((0,[-380,60,-300],[-330,60,200]),(0.5,[-330,34,-270],[-220,24,-120]),(1,[-260,30,-240],[-150,24,-100])),DUSK)
    sh('붙잡힌',  'C',i2,i3,orbit((bx,bz),150,34,-60,-10,(bx,24,bz),r1=110),DUSK,fps=24,shake=1.5)
    sh('지나치려','C',i3,i4,two([-190,34,-230],[-140,26,-110],[-175,32,-215],[-140,26,-110]),DUSK)
    sh('가방',    'C',i4,i6,cam((0,[-70,30,-110],[bx-8,22,bz-12]),(1,[10,26,-74],[bx-8,22,bz-12])),DUSK,fps=24,shake=0.6)
    sh('총',      'C',i6,i7,cam((0,[-230,34,-170],[-60,22,-70],0),(0.25,[-200,30,-150],[20,18,-50],1),(1,[-120,60,-230],[20,10,-50],0.3)),DUSK,fps=24,shake=3)
    sh('마주봄',  'C',i7,i8,orbit((-55,-80),230,34,-20,15,(-55,24,-80),r1=190),DUSK)
    sh('트윌모습','C',i8,i9,orbit((bx-40,bz-30),70,40,-70,-20,(bx-40,30,bz-30),r1=58,h1=36),DUSK)
    sh('손',      'C',i9,i10,two([bx-10,22,bz-78],[bx-33,14,bz-34],[bx-16,20,bz-70],[bx-33,14,bz-34]),DUSK)
    sh('빈손',    'C',i10,i11,cam((0,[-110,30,-130],[bx-40,24,bz-30]),(1,[-70,28,-150],[bx-50,24,bz-36])),DUSK)
    sh('딕',      'C',i11,i12,two([-10,30,-120],[-90,26,-85],[-24,29,-112],[-90,26,-85]),DUSK)
    sh('틱',      'C',i12,j1-1,orbit((bx-40,bz-30),90,36,-95,-55,(bx-40,28,bz-30),r1=74),DUSK)
    sh('모닥불',  'C',j1-1,j2,cam((0,[0,230,-640],[0,90,0]),(0.5,[0,60,-360],[0,24,fz+60]),(1,[20,34,-290],[0,22,fz+60])),NIGHT)
    sh('말',      'C',j2,j4,orbit((0,fz+60),120,30,-25,25,(0,22,fz+60)),NIGHT)
    sh('못배움',  'C',j4,j5,two([-10,28,fz-10],[-60,26,fz+60],[-16,27,fz],[-60,26,fz+60]),NIGHT)
    sh('외운트윌','C',j5,j6,two([10,30,fz-10],[62,28,fz+60],[16,30,fz],[62,29,fz+60]),NIGHT)
    sh('셈',      'C',j6,j8,cam((0,[-70,34,fz-120],[0,10,fz-10]),(1,[10,26,fz-86],[6,2,fz-22])),NIGHT)
    sh('별그림',  'C',j8,j9,cam((0,[-10,60,dz-100],[-24,6,dz+10]),(1,[-36,44,dz-70],[-30,2,dz+2])),NIGHT)
    sh('수성',    'C',j9,j10,two([-30,46,dz-40],[-24,0,dz],[-22,30,dz-26],[-18,0,dz+1]),NIGHT)
    sh('고향',    'C',j10,j11,cam((0,[-150,14,dz-40],[-60,36,dz+50]),(1,[-170,10,dz-70],[40,150,dz+500])),NIGHT)
    sh('도약',    'C',j11,j12,cam((0,[-40,22,dz-110],[30,26,dz+30]),(0.55,[-40,22,dz-110],[30,26,dz+30]),(0.75,[-80,14,dz-190],[20,150,dz+10]),(1,[-90,12,dz-210],[10,250,dz])),NIGHT,fps=24)
    sh('꽂힘',    'C',j12,j13,cam((0,[-90,12,dz-210],[0,250,dz],0),(0.42,[-70,30,dz-130],[0,30,dz],1),(1,[-46,26,dz-84],[0,16,dz],0)),NIGHT,fps=24,shake=2)
    sh('다시',    'C',j13,j14,orbit((0,dz),150,40,15,-20,(0,30,dz)),NIGHT,fps=24)
    sh('통하는곳','C',j14,j15,cam((0,[0,40,fz-130],[0,24,fz+60]),(1,[0,150,fz-330],[0,60,fz+200])),NIGHT)
    sh('좋았다',  'C',j15,j16,orbit((0,fz+60),130,28,30,-20,(0,24,fz+60)),NIGHT)
    sh('아침',    'C',j16,j17,cam((0,[-330,170,-520],[-200,30,-140]),(1,[-170,40,-330],[-120,26,-150])),MORN)
    sh('뛰는트윌','C',j17,nx,cam((0,[60,26,-170],[0,26,0]),(1,[110,34,-150],[0,26,0])),MORN,fps=24,follow='j_mv')
    num(j11,'약 23m (원문 75피트)'); num(j17,'한 번에 약 46m (원문 150피트)'); num(j9,'맨눈으로는 보기 힘든 수성 → 망원경을 쓰는 문명')
    return save(M,A,top,'만남','C')

# =====================================================================
#  D : 피라미드 줄 (주황빛 잔투스 사막) — 작은 것에서 큰 것으로 · 마지막 피라미드에서 나온 것 · 벽돌 = 날숨
# =====================================================================
def set_D():
    M,A=newset()
    top=[far_ground(M,'o2')]+tiles(M,-1088,1088,-512,512,seed=7)
    top+= cliff_line(M,1100,-3000,3000,180,seed=41)+cliff_line(M,1800,-3600,3600,320,seed=47)
    top+= dune(M,-700,300,420,200,36)+dune(M,-100,360,460,200,30)+dune(M,560,320,420,200,40)+dune(M,980,-360,300,170,26)+dune(M,-900,-380,300,170,26)
    top+= patches(M,-1000,1000,-480,460,34,seed=15)+pebbles(M,-1000,1000,-460,-90,120,seed=16)+pebbles(M,-1000,1000,60,300,60,seed=17)
    for i,(x,z,s) in enumerate([(-600,150,22),(-200,190,26),(260,160,20),(700,200,28),(-860,-300,16),(-320,-330,20),(240,-380,18),(820,-330,22),(980,120,24)]): top+= rock(M,x,z,s,seed=i)
    top+= crater(M,-420,-300,46)+crater(M,480,-330,56)
    d1=I('며칠 뒤 주황빛'); d2=I('손바닥 높이의'); d3=I('속이 빈 피라미드'); d4=I('점점 커졌습니다'); d5=I('벽돌 크기가 커진'); d6=I('한낮에는 어깨 높이'); d7=I('오십만 년쯤')
    d8=I('사람이 만든 거야'); d9=I('아니. 하나 하나 둘'); d10=I('생각하지 않는 존재가'); d11=I('꼭대기가 막혀'); d12=I('은회색 팔 하나가'); d13=I('통처럼 생긴 몸'); d14=I('꼬리를 모래에 꽂고')
    d15=I('벽돌 한 장을 꺼내'); d16=I('십 분 뒤 또'); d17=I('그것을 가리키며 말합니다'); d18=I('화학자인 자비스는'); d19=I('탄소로 되어'); d20=I('규소로 되어'); d21=I('벽돌은 이 생물의 날숨')
    d22=I('제 날숨에 파묻히면'); d23=I('오십만 년 동안'); nx=I('운하 근처에 이르렀을 때')-1
    # 피라미드 줄: 화면 오른쪽(-x) 끝이 가장 작고 오래된 것, 왼쪽(+x)으로 갈수록 큼. 마지막(가장 큰 것)만 꼭대기가 막힘
    N=24; xs=[]; hs=[]; x=-940
    for i in range(N):
        h=5+(54-5)*(i/(N-1))**1.5; xs.append(x); hs.append(h); x+=h*1.25+18+i*1.3
    XL=xs[-1]; HL=hs[-1]
    pyr=[]
    for i in range(N):
        g=pyramid(M,f'py{i}_',xs[i],0,hs[i],capped=(i==N-1),old=(i<N*0.45)); top.append(g); pyr.append(g)
    for i in range(0,6):      # 가장 오래된 것들은 부스러져 조각이 흩어짐
        for k in range(3): top.append(M.cube('crumb',[xs[i]-6+k*5,0,-9-k*2],[xs[i]-4.4+k*5,1.2,-7.4-k*2],'brick'))
    # 마지막 피라미드: 꼭대기 두 층이 흔들리다 미끄러져 내림
    last=pyr[-1]; L4=find(last,f'py{N-1}_L4'); L3=find(last,f'py{N-1}_L3'); t12=T(d12)
    cyc(A,L4,'rotation',T(d11)+1.5,t12+1.4,(0,0,4),(0,0,-4),0.22,rest=(0,0,0))
    A.add(L4,'position',[(0,(0,0,0)),(t12+1.4,(0,0,0)),(t12+2.2,(-16,-HL*0.7,-26))],'catmullrom'); A.add(L4,'scale',[(0,(1,1,1)),(t12+2.2,(1,1,1)),(t12+2.5,(0,0,0))])
    A.add(L3,'position',[(0,(0,0,0)),(t12+1.8,(0,0,0)),(t12+2.7,(22,-HL*0.5,-30))],'catmullrom'); A.add(L3,'scale',[(0,(1,1,1)),(t12+2.7,(1,1,1)),(t12+3.0,(0,0,0))])
    for k in range(7): top.append(M.group(f'fallen{k}',[XL,0,-40],[M.cube('fallen',[XL-28+k*8,0,-44-(k%3)*5],[XL-22+k*8,2.6,-40-(k%3)*5],'brick')])); vis(A,top[-1],[(t12+2.4,L)])
    puff(M,A,top,XL,6,-36,t12+2.2,1.3,10,'o3',34,20,6,seed=3)
    # 쌓는 것: 피라미드 속에서 솟아 나와 옆(앞쪽)으로 떨어져 앉음
    SB=1.3; pb=pyramid_beast(M,'y_',SB); be=actor(M,A,top,pb,'y_',XL,0,0,y=2,legs=None); be.show([(t12+1.0,L)])
    BX,BZ=XL-4,-78
    be.hold(t12+2.2); be.go(t12+2.2,t12+3.6,XL,0,y=HL*0.75,walk=False,face=False,interp='catmullrom'); be.go(t12+3.6,T(d13)-0.6,BX,BZ,y=30,walk=False,face=False,interp='catmullrom'); be.go(T(d13)-0.6,T(d13)-0.1,BX,BZ,y=0,walk=False,face=False)
    A.add(pb,'rotation',[(0,(0,0,0)),(t12+3.6,(0,0,0)),(T(d13)-0.6,(-50,0,20)),(T(d13)-0.1,(0,0,0))],'catmullrom')
    puff(M,A,top,BX,3,BZ,T(d13)-0.15,1.2,10,'o3',30,14,5,seed=5)
    arm=find(pb,'y_arm'); fore=find(pb,'y_forearm')
    cyc(A,arm,'rotation',t12+1.2,t12+3.4,(0,0,50),(0,0,10),0.8,rest=(0,0,0))
    # 벽돌 놓기: 팔이 입으로 → 벽돌 → 바닥. (영상에선 십 분을 몇 초로)
    bt=[]; t=T(d15)+0.3
    while t<E(d16)-1.2: bt.append(t); t+=2.3
    bt+= [T(d17)+2.0+k*2.4 for k in range(2)]+[T(d20)+0.3, T(d21)+0.4]
    ak=[(0,(0,0,0))]; fk=[(0,(0,0,0))]
    for k,t in enumerate(bt):
        ak+= [(t,(0,0,0)),(t+0.5,(0,0,38)),(t+0.9,(0,0,38)),(t+1.5,(0,0,-12)),(t+1.9,(0,0,0))]; fk+= [(t,(0,0,0)),(t+0.5,(0,0,-110)),(t+0.9,(0,0,-110)),(t+1.5,(0,0,-10)),(t+1.9,(0,0,0))]
        gx=BX-18*SB-(k%4)*7.5; gz=BZ-6+(k//4)*5.5; gy=0
        b=M.group(f'nb{k}',[gx,gy,gz],[M.cube('brick',[gx-3.4,gy,gz-2.4],[gx+3.4,gy+2.6,gz+2.4],'brick')]); top.append(b)
        mx,my,mz=BX,28*SB,BZ
        A.add(b,'position',[(0,(-(mx-gx),my-gy,mz-gz)),(t+0.9,(-(mx-gx),my-gy+2,mz-gz)),(t+1.5,(0,1,0)),(t+1.6,(0,0,0))],'catmullrom')
        A.add(b,'scale',[(0,(0,0,0)),(t+0.65,(0,0,0)),(t+0.9,(1,1,1))])
    A.add(arm,'rotation',ak,'catmullrom'); A.add(fore,'rotation',fk,'catmullrom')
    # 날숨 설명: 사람의 숨(흰 김) / 이 생물의 숨(벽돌)
    # 자비스·트윌
    ja=J(M,A,top,xs[0]-150,-70,90); tw=TW(M,A,top,xs[0]-210,-90,90)
    ja.go(T(d1)-3.0,T(d1)+3.2,xs[2]-10,-96,per=0.8); tw.go(T(d1)-2.6,T(d1)+3.6,xs[1]-30,-124,per=0.5)
    ja.look(T(d2)+0.2,xs[3],0); ja.A.add(ja.part('head'),'rotation',[(T(d2),(0,0,0)),(T(d2)+0.6,(30,0,0)),(E(d3),(30,0,0)),(E(d3)+0.3,(0,0,0))])
    tw.look(T(d2)+0.5,xs[3],0); tw.tilt(T(d3),E(d3),14)
    xa=xs[int(N*0.82)]+10
    ja.go(T(d4)+0.2,E(d6)-0.6,xa,-80,per=0.7); tw.go(T(d4)+0.6,E(d6)-0.2,xa-70,-104,per=0.45)
    # d8~d10: 큰 피라미드 옆에서 묻고 답함
    xq=xs[N-3]; ja.at(T(d8),xq-30,-70,60); tw.at(T(d8),xq-96,-84,80)
    ja.look(T(d8)+0.1,xq-96,-84); ja.arm('l',T(d8)+0.3,E(d8)-0.4,rx=-80,rz=-30); tw.look(T(d8)+0.1,xq-30,-70)
    cyc(A,tw.part('arm_left'),'rotation',T(d8)+2.2,E(d9),(-28,0,-24),(-44,0,-34),0.5,rest=(0,0,0)); cyc(A,tw.part('head'),'rotation',T(d9),E(d9),(0,22,0),(0,-22,0),0.6,rest=(0,0,0))
    ja.tilt(T(d10)+0.3,E(d10),-10)
    # d11~: 마지막 피라미드 앞
    ja.at(T(d11),XL-150,-120,70); tw.at(T(d11),XL-190,-150,70); ja.look(T(d11),XL,0); tw.look(T(d11),XL,0)
    gun=None
    ja.A.add(ja.part('head'),'rotation',[(T(d11),(0,0,0)),(T(d11)+0.5,(-22,0,0)),(T(d13)-0.6,(-22,0,0)),(T(d13),(0,0,0))])
    ja.go(t12+0.6,t12+1.6,XL-170,-150,per=0.6,face=False); 
    ja.look(T(d13),BX,BZ); tw.look(T(d13),BX,BZ)
    # d17: 트윌이 뛰어가 두드림
    leap(tw,T(d17)+0.4,T(d17)+1.5,BX-40,BZ-20,h=50,stick=0.3); tw.go(T(d18)+0.2,T(d18)+1.2,BX-104,BZ-6,per=0.4); tw.look(T(d18)+1.3,BX,BZ,0.2); tw.look(T(d17)+2.2,BX,BZ,0.2)
    cyc(A,tw.part('arm_right'),'rotation',T(d17)+2.5,E(d17),(-80,0,0),(-50,0,0),0.3,rest=(0,0,0))
    ja.go(T(d18)+0.2,T(d18)+1.6,BX-64,BZ+10,per=0.7); ja.look(T(d18)+1.7,BX,BZ); ja.arm('r',T(d18)+2.0,E(d18),rx=-60)
    for k in range(4): puff(M,A,top,BX-62,30,BZ+4,T(d19)+1.2+k*0.8,0.9,3,'th',5,8,1.6,seed=k)
    ja.nod(T(d21)+0.3,E(d21),8,0.8)
    # d22: 벽돌이 둘레에 차오름 (세월을 빠르게) → 새 피라미드
    ring=[]
    for lay in range(4):
        w=(34-lay*7)*SB; g=M.group(f'newpy{lay}',[BX,lay*7,BZ],[M.cube('np',[BX-w,lay*7,BZ-w],[BX+w,(lay+1)*7,BZ+w],'bw_sil',up='brick')]); top.append(g)
        grow(A,g,T(d22)+0.5+lay*0.9,T(d22)+1.3+lay*0.9)
    ja.at(T(d22),BX-150,BZ-40,60); tw.at(T(d22),BX-190,BZ-70,60)
    # 샷
    sh('사막',    'D',d1-1,d2,cam((0,[xs[0]-200,260,-700],[xs[6],40,0]),(1,[xs[1]-40,30,-220],[xs[3],8,0])))
    sh('작은줄',  'D',d2,d3,cam((0,[xs[0]-36,7,-34],[xs[4],5,0]),(1,[xs[2]-30,11,-40],[xs[8],8,0])))
    sh('속빈',    'D',d3,d4,cam((0,[xs[2]-14,22,-30],[xs[2],4,0]),(1,[xs[2]-4,30,-12],[xs[2],2,0])))
    sh('커진다',  'D',d4,d7,cam((0,[20,40,-190],[60,22,60]),(0.5,[10,30,-170],[70,22,60]),(1,[-10,46,-210],[80,26,60])),fps=24,follow='j_mv')
    sh('닳은것',  'D',d7,d8,orbit((xs[1],0),60,14,-40,30,(xs[1],3,0),r1=44,h1=10))
    sh('묻다',    'D',d8,d9,two([xq-150,34,-200],[xq-50,26,-70],[xq-130,32,-180],[xq-56,26,-74]))
    sh('배문지름','D',d9,d10,orbit((xq-96,-84),80,36,-80,-30,(xq-96,26,-84),r1=64))
    sh('생각없는','D',d10,d11,cam((0,[xq-70,24,-150],[xq,30,0]),(1,[xq-160,120,-330],[XL-200,30,0])))
    sh('막힌꼭대기','D',d11,d12,cam((0,[XL-210,26,-230],[XL,20,0]),(1,[XL-90,HL+30,-150],[XL,HL-4,0])))
    sh('나온다',  'D',d12,d13,cam((0,[XL-70,HL+24,-130],[XL,HL-2,0],1),(0.45,[XL-80,HL+30,-140],[XL,HL+4,0],1),(1,[XL-150,50,-250],[XL,30,-50],0.3)),fps=24,shake=2.5)
    sh('모습',    'D',d13,d14,orbit((BX,BZ),120,30,-30,50,(BX,20,BZ),r1=92))
    sh('앉음',    'D',d14,d15,two([BX-150,24,BZ-150],[BX,18,BZ],[BX-140,22,BZ-140],[BX,18,BZ]))
    sh('벽돌',    'D',d15,d17,cam((0,[BX-70,40,BZ-90],[BX-10,22,BZ]),(1,[BX-50,26,BZ-70],[BX-16,10,BZ])),fps=24)
    sh('바위',    'D',d17,d18,cam((0,[BX-210,40,BZ-190],[BX-80,24,BZ-40]),(1,[BX-110,34,BZ-130],[BX-20,22,BZ-10])),fps=24)
    sh('화학자',  'D',d18,d19,two([BX-10,30,BZ-110],[BX-50,26,BZ+6],[BX-20,30,BZ-96],[BX-56,26,BZ+8]))
    sh('탄소',    'D',d19,d20,two([BX-110,34,BZ-80],[BX-62,30,BZ+6],[BX-104,36,BZ-70],[BX-62,34,BZ+6]))
    sh('규소',    'D',d20,d22,orbit((BX-14,BZ),100,26,10,60,(BX-14,12,BZ-2),r1=76,h1=18),fps=24)
    sh('차오름',  'D',d22,d23,cam((0,[BX-120,30,BZ-190],[BX,16,BZ]),(1,[BX-160,70,BZ-260],[BX,20,BZ])),fps=24)
    sh('한줄',    'D',d23,nx,cam((0,[XL-60,90,-330],[XL-200,20,0]),(1,[XL-900,520,-900],[XL-900,0,0])))
    num(d2,'약 15cm (원문 6인치)'); num(d6,'약 3m (원문 10피트)'); num(d7,'약 50만 년 (자비스의 짐작)'); num(d19,'탄소 생물 → 날숨은 이산화탄소 (기체)'); num(d20,'규소 생물 → 날숨은 이산화규소 (단단한 돌)')
    return save(M,A,top,'피라미드','D')

def BR(M,A,top,x,z,yaw,tag,load=None,cartless=False):
    """수레를 미는 것 + 수레 (바깥 묶음에 함께 → 같이 움직임). 수레 묶음은 .cart"""
    a=actor(M,A,top,barrel_being(M,tag),tag,x,z,yaw,legs='four'); a.cart=None
    if not cartless:
        c=cart(M,tag+'c_',load='rubble'); move(M,c,0,0,-24); a.out['children'].append(c); a.cart=c; a.load=find(c,tag+'c_load')
        if load is None: vis(A,a.load,[])
    return a
def drum(A,a,t0,t1): cyc(A,a.part('body'),'scale',t0,t1,(1,1,1),(1.05,0.95,1.05),0.2,rest=(1,1,1),interp='linear')

# =====================================================================
#  E : 운하 가 — 그리운 사람의 환영 · 꿈을 보여 주는 것
# =====================================================================
def set_E():
    M,A=newset(); G=('g1','g2','g3')
    top=[far_ground(M,'o2')]+tiles(M,-896,896,-640,128,seed=9)+tiles(M,-896,896,128,640,cols=G,seed=10)
    # 운하: 넓고 곧은 마른 도랑 (둑 + 어두운 바닥 + 누런 물줄기) — 뒤쪽을 가로지름
    top+= [M.cube('bank',[-2000,0,300],[2000,7,330],'g_d'), M.cube('canal',[-2000,0,330],[2000,1.2,640],'canal'), M.cube('water',[-2000,1,450],[2000,1.8,500],'wat'), M.cube('bank2',[-2000,0,640],[2000,9,672],'g_d')]
    for i,x in enumerate(range(-860,900,95)):
        top+= rubber_tree(M,x+(i%3)*18,190+(i%4)*24,62+(i*17)%40,seed=i)
        top+= rubber_tree(M,x+40,720+(i%3)*30,70+(i*13)%40,seed=i+40)
    for i,(x,z,w,h) in enumerate([(-600,900,200,120),(-360,960,150,90),(-120,900,180,110),(160,980,220,140),(420,920,160,100),(660,960,200,120)]): top+= mound(M,x,z,w,h,seed=i)
    top+= cliff_line(M,1700,-3200,3200,260,seed=51)
    top+= dune(M,-620,-360,320,170,26)+dune(M,560,-420,340,180,30)+patches(M,-800,800,-600,100,20,seed=21)+pebbles(M,-800,800,-600,100,70,seed=22)
    for i,(x,z,s) in enumerate([(-520,-60,18),(480,-120,22),(-260,-420,16),(300,-460,14),(700,40,20),(-740,60,22)]): top+= rock(M,x,z,s,seed=i)
    FX,FZ=210,170
    av=[(FX,FZ,40,40),(0,60,500,70)]
    top+= grass(M,-860,860,130,300,420,seed=23,avoid=av)+stumps(M,-860,860,-560,60,26,seed=24,avoid=[(0,40,700,90)])
    e1=I('운하 근처에 이르렀을 때'); e2=I('따뜻한 밥과 뉴욕'); e3=I('팬시 롱입니다'); e4=I('바로 그 여인이 서 있었습니다'); e5=I('정신없이 달려갑니다'); e6=I('팔을 붙잡습니다'); e7=I('유리로 된 작은 총')
    e8=I('여인은 사라졌습니다'); e9=I('괴물이 꿈틀'); e10=I('너 하나 하나 둘'); e11=I('네가 생각한 것을'); e12=I('가장 그리워하는 것'); e13=I('트윌도 그날'); e14=I('낱말 몇 개만으로'); e15=I('자신이 없었습니다'); nx=I('진흙 언덕으로 된 도시')-1
    ja=J(M,A,top,-520,20,90); tw=TW(M,A,top,-590,-10,90,gun=True); gun=tw.part('gun'); vis(A,gun,[(T(e7)+0.2,T(e10))])
    ja.go(T(e1)-3,E(e3),-150,40,per=1.2,amp=16); tw.go(T(e1)-2.6,E(e3),-215,10,per=0.7,amp=20)
    ja.A.add(ja.part('head'),'rotation',[(T(e1),(14,0,0)),(E(e3)-0.3,(14,0,0)),(T(e4)+0.3,(-6,0,0)),(T(e5),(0,0,0))])
    # 생각 풍선 (자비스 머리 위): 밥그릇 → 뉴욕 빌딩
    th=[M.cube('th',[-3,40,-2],[3,45,3],'th'), M.cube('th',[-8,48,-3],[4,56,4],'th'), M.cube('th',[-34,58,-5],[30,96,6],'th'), M.cube('th',[-28,96,-4],[24,102,5],'th')]
    bowl=M.group('th_bowl',[-2,66,-6],[M.cube('bowl',[-12,66,-7],[8,72,-5.4],'hull_r'), M.cube('rice',[-10,72,-7],[6,77,-5.4],'star'), M.cube('steam',[-6,80,-7],[-4,86,-5.4],'smoke_l'), M.cube('steam',[0,82,-7],[2,89,-5.4],'smoke_l')])
    ny=[M.cube('ny',[-28+k*10,62,-7],[-21+k*10,74+((k*7)%5)*4,-5.4],'ny') for k in range(6)]+[M.cube('nyw',[-26+k*10,70,-7.4],[-24+k*10,72,-6.8],'ny_w') for k in range(6)]+[M.cube('nyw',[-26+k*10,65,-7.4],[-24+k*10,67,-6.8],'ny_w') for k in range(6)]
    nyg=M.group('th_ny',[0,62,-6],ny)
    girl=M.group('th_girl',[0,62,-6],[M.cube('gh',[-4,80,-7],[4,88,-5.4],'skin'), M.cube('gh2',[-5,84,-7.2],[5,90,-5.2],'h_blond'), M.cube('gd',[-5,64,-7],[5,80,-5.4],'red')])
    thg=M.group('thought',[0,40,0],th+[bowl,nyg,girl]); ja.out['children'].append(thg)
    vis(A,thg,[(T(e2)+0.3,T(e4)+0.4)]); d2=(E(e2)-T(e2)); vis(A,bowl,[(T(e2)+0.3,T(e2)+d2*0.45)]); vis(A,nyg,[(T(e2)+d2*0.45,T(e3)+0.2)]); vis(A,girl,[(T(e3)+0.2,T(e4)+0.4)])
    A.add(thg,'rotation',[(0,(0,-90,0)),(L,(0,-90,0))])      # 자비스가 옆(+x)을 보고 걸으므로 풍선은 카메라 쪽으로
    # 팬시 롱 (환영) → 꿈 괴물
    fa=H(M,A,top,'fancy',FX,FZ,-100,tag='f_',s=0.95); fa.show([(T(e4)+0.2,T(e8)+1.0)]+[(T(e12)+0.6+k*1.2,T(e12)+1.1+k*1.2) for k in range(3)])
    cyc(A,fa.part('arm_left'),'rotation',T(e4),T(e8)+1.0,(0,0,150),(0,0,115),0.6,rest=(0,0,150)); A.add(fa.part('arm_left'),'rotation',[(T(e12),(0,0,150)),(L,(0,0,150))])
    db=dream_beast(M,'d_',1.3); be=actor(M,A,top,db,'d_',FX,FZ,0,legs=None); be.show([(T(e8)+1.0,L)])
    for k in range(6): cyc(A,find(db,f'd_arm{k}'),'rotation',T(e8)+1.0,T(e14),((k%2*2-1)*22,0,(k%3-1)*22),(-(k%2*2-1)*22,0,-(k%3-1)*22),0.6+k*0.07,rest=(30*(k%2*2-1),0,40))
    be.hold(T(e14)); be.go(T(e14),T(e14)+2.5,FX,FZ,y=-34,walk=False,face=False)
    top+= rubber_tree(M,FX+34,FZ+30,96,seed=77)
    # 달려감 → 트윌이 날아와 붙잡음
    ja.go(T(e5)+0.2,T(e6)+0.8,FX-90,FZ-40,per=0.42,amp=44)
    leap(tw,T(e5)+1.4,T(e6)+0.8,FX-118,FZ-52,h=70,stick=0.15); tw.look(T(e6)+1.4,FX-90,FZ-40,0.2)
    cyc(A,tw.part('arm_left'),'rotation',T(e6)+1.5,E(e6),(-85,0,-30),(-70,0,-30),0.25,rest=(0,0,0)); cyc(A,ja.g,'rotation',T(e6)+1.0,E(e6),(0,0,5),(0,0,-5),0.3,rest=(0,0,0))
    tw.look(T(e7)+0.2,FX,FZ); tw.arm('r',T(e7)+0.3,T(e10),rx=-85); ja.look(T(e7)+0.5,FX,FZ)
    puff(M,A,top,FX-100,26,FZ-46,T(e8)+0.3,0.7,4,'th',6,10,2,seed=1); puff(M,A,top,FX,22,FZ,T(e8)+0.8,1.2,12,'th',22,26,5,seed=2)
    ja.A.add(ja.out,'position',[],'linear'); ja.go(T(e9)+0.4,T(e9)+1.2,FX-112,FZ-60,per=0.5,face=False)
    tw.look(T(e10),FX-112,FZ-60,0.3); tw.arm('l',T(e10)+0.5,T(e10)+1.8,rx=-70); tw.A.add(tw.part('arm_right'),'rotation',[(T(e10)+2.0,(0,0,0)),(T(e10)+2.4,(-80,0,40)),(E(e10),(-80,0,40)),(E(e10)+0.3,(0,0,0))])
    ja.tilt(T(e11)+0.3,E(e11),12); tw.look(T(e13),FX,FZ,0.4); tw.nod(T(e13)+0.5,E(e13),10,0.9)
    ja.look(T(e14),FX-150,FZ-70,0.4); ja.nod(T(e14)+0.8,E(e14),6,1.0)
    ja.go(T(e15)+0.3,T(nx)+4.5,FX+260,FZ-150,per=0.9); tw.go(T(e15)+0.8,T(nx)+4.5,FX+200,FZ-190,per=0.5)
    # 샷
    sh('지친걸음','E',e1-1,e2,cam((0,[-420,200,-460],[-200,40,200]),(1,[-300,34,-190],[-330,26,30])))
    sh('생각',    'E',e2,e4,cam((0,[-40,50,-210],[0,52,0]),(1,[-10,56,-180],[0,54,0])),follow='j_mv')
    sh('여인',    'E',e4,e5,cam((0,[-220,40,-90],[FX,26,FZ],0),(0.3,[-200,36,-60],[FX,26,FZ],0),(1,[FX-110,28,FZ-90],[FX,24,FZ],0)),fps=24)
    sh('달려감',  'E',e5,e6,cam((0,[-60,22,-90],[30,24,10]),(1,[-40,26,-110],[30,26,10])),fps=24,follow='j_mv',shake=1.2)
    sh('붙잡음',  'E',e6,e7,orbit((FX-100,FZ-46),150,34,-40,10,(FX-100,24,FZ-46),r1=110),fps=24,shake=1.0)
    sh('유리총',  'E',e7,e8,cam((0,[FX-80,34,FZ-200],[FX-60,24,FZ-20]),(1,[FX-40,30,FZ-170],[FX-56,24,FZ-20])))
    sh('사라짐',  'E',e8,e9,cam((0,[FX-20,34,FZ-170],[FX,24,FZ],0),(0.4,[FX-10,30,FZ-130],[FX,22,FZ],1),(1,[FX-6,26,FZ-100],[FX,18,FZ],0.2)),fps=24,shake=2)
    sh('괴물',    'E',e9,e10,orbit((FX,FZ),120,40,-5,45,(FX,16,FZ),r1=90,h1=30),fps=24)
    sh('하나하나둘','E',e10,e12,orbit((FX-112,FZ-56),100,34,-110,-60,(FX-112,26,FZ-56),r1=84))
    sh('그리움',  'E',e12,e13,cam((0,[FX-90,60,FZ-150],[FX,24,FZ]),(1,[FX-60,40,FZ-110],[FX,22,FZ])),fps=24)
    sh('트윌도',  'E',e13,e14,two([FX-190,34,FZ-10],[FX-118,30,FZ-52],[FX-180,34,FZ-20],[FX-118,31,FZ-52]))
    sh('깨달음',  'E',e14,e15,orbit((FX-114,FZ-56),96,32,-30,25,(FX-114,26,FZ-56),r1=80))
    sh('떠남',    'E',e15,nx,cam((0,[FX-200,36,FZ-250],[FX-60,26,FZ-80]),(1,[FX-260,190,FZ-460],[FX+200,30,FZ+200])))
    return save(M,A,top,'운하','E')

# =====================================================================
#  F : 진흙 언덕 도시 — 수레 미는 것들 · "우리는 친구다" · (끝) 막다른 곳의 싸움 · 푸츠의 로켓
# =====================================================================
def set_F():
    M,A=newset(); MU=('mud','mud2','mud3')
    top=[far_ground(M,'o2')]+tiles(M,-896,896,-768,640,seed=11,cols=('o1','o2','mud3'))
    top+= cliff_line(M,1900,-3400,3400,280,seed=61)
    top+= [M.cube('canal',[-2000,0,1050],[2000,1.2,1300],'canal'), M.cube('water',[-2000,1,1150],[2000,1.8,1200],'wat')]
    for i,x in enumerate(range(-900,950,110)): top+= rubber_tree(M,x+(i%3)*20,990+(i%2)*26,70+(i*11)%40,seed=i)
    # 길: 카메라 쪽(-z)에서 큰 언덕의 입구(z 250)까지 곧게
    top+= [M.cube('road',[-26,0,-768],[26,0.8,256],'road'), M.cube('road_e',[-30,0,-768],[-26,1.6,256],'mud2'), M.cube('road_e',[26,0,-768],[30,1.6,256],'mud2')]
    top+= mound(M,0,420,340,200,door='n',seed=1)
    city=[(-330,360,220,130),(340,380,240,150),(-560,560,260,160),(600,600,280,170),(-180,700,220,140),(220,720,240,150),(-760,300,200,110),(800,330,200,120),(-420,840,260,170),(460,880,280,180),(0,880,260,190),
          (-300,60,150,80),(300,40,160,90),(-560,-60,180,100),(-420,60,170,110),(600,-40,180,100),(-700,-330,160,90),(700,-360,170,95)]
    for i,(x,z,w,h) in enumerate(city): top+= mound(M,x,z,w,h,seed=i+3)
    top+= patches(M,-800,800,-700,200,24,col='mud2',seed=31)+pebbles(M,-800,800,-700,200,90,seed=32,cols=('mud_d','rk','mud3'))
    for i,(x,z,s) in enumerate([(-230,-200,14),(230,-330,16),(-250,-600,12),(210,-640,14),(420,-260,18),(-330,-420,14)]): top+= rock(M,x,z,s,seed=i)
    top+= stumps(M,-800,800,-700,-100,22,seed=33,avoid=[(0,-300,200,500),(-400,-150,220,220)])
    for i,(x,z) in enumerate([(-150,-90),(150,-180),(-170,-470),(150,-560)]):      # 길가의 쓰레기 더미·말뚝
        top+= [M.cube('heap',[x-10,0,z-8],[x+10,6,z+8],'sand'), M.cube('heap',[x-5,6,z-4],[x+6,10,z+4],'rk'), M.cube('stake',[x+14,0,z],[x+16,20,z+2],'copper_d')]
    f1=I('진흙 언덕으로 된 도시'); f2=I('구릿빛 수레를 밀며'); f3=I('다리 넷 팔 넷'); f4=I('길을 막고 말합니다'); f5=I('북 같은 윗면을 울려'); f6=I('밀치고 가 버립니다'); f7=I('모두가 같은 말을')
    f8=I('하나 하나 둘 맞아'); f9=I('생각은 한다'); f10=I('굴로 따라 들어갔다가'); g1=I('전등이 켜진 미로를')
    k1=I('막다른 곳에 몰립니다'); k2=I('구리 화살이'); k3=I('영하 육십 도'); k4=I('그때 자비스는 깨닫습니다'); k5=I('뒤쪽 언덕을 뛰어넘어'); k6=I('위를 가리키며 가라고'); k7=I('유리 총을 쏘며 곁에')
    k8=I('넌 진짜 사나이야'); k9=I('이게 칭찬이 될까'); k10=I('하늘에서 불기둥이'); k11=I('올라타 돌아봤을 때'); k12=I('이름을 백 번 넘게'); kend=I('아레스호에 돌아온')
    tK=T(k1)-0.3
    night(M,A,top,[(T(k12)-0.1,L)])
    # 자비스·트윌 (길가)
    ja=J(M,A,top,-330,-520,90,gun=True); vis(A,ja.part('gun'),[(T(k2)+1.5,T(k11))]); tw=TW(M,A,top,-380,-560,90,gun=True); vis(A,tw.part('gun'),[(T(k2)+1.5,T(k11))])
    ja.go(T(f1)-2,E(f1)+1.0,-70,-300,per=0.8); tw.go(T(f1)-1.6,E(f1)+1.4,-112,-330,per=0.5)
    ja.look(E(f1)+1.2,0,-200); tw.look(E(f1)+1.6,0,-200)
    # 수레 미는 것들: 입구(z 250)에서 나와 길을 따라 카메라 쪽으로 달려감(빈 수레) → 짐을 싣고 돌아옴
    brs=[]
    def run(b,t0,z0,z1,lane,sp=260):
        b.at(t0,lane,z0,0 if z1<z0 else 180); t1=t0+abs(z1-z0)/sp; b.go(t0,t1,lane,z1,per=0.28,amp=34,face=False); return t1
    tA=T(f2)-1.0
    for k in range(6):
        b=BR(M,A,top,9,300,0,f'b{k}_',load=True); brs.append(b)
    sched=[]      # (barrel, 시작 시간, 나감/들어옴)
    # f2~f3: 셋이 차례로 지나감
    b0,b1,b2,b3,b4,b5=brs
    for b,t in ((b0,tA),(b3,tA+0.9),(b1,tA+1.8),(b4,tA+2.7),(b5,tA+3.6)): vis(A,b.load,[]); run(b,t,250,-760,9,sp=210)
    # f4: 셋째(b2)를 자비스가 막아섬 (z -200 에서 멈춤)
    vis(A,b2.load,[]); t4=T(f4); ja.go(t4-1.6,t4-0.4,4,-232,per=0.6); ja.turn(t4-0.3,180,0.3); ja.arm('l',t4+0.3,E(f4),rx=-70,rz=-50); ja.arm('r',t4+0.3,E(f4),rx=-70,rz=50)
    b2.at(t4-1.8,9,250,0); b2.go(t4-1.8,t4+0.2,9,-170,per=0.28,amp=34,face=False); drum(A,b2,T(f5)+1.6,E(f5))
    t6=T(f6)+0.4; b2.go(t6,t6+0.5,9,-205,per=0.25,amp=34,face=False); ja.hold(t6+0.3); ja.go(t6+0.3,t6+0.8,-52,-246,per=0.3,face=False); b2.go(t6+0.6,t6+2.8,9,-760,per=0.28,amp=34,face=False)
    ja.look(t6+1.0,9,-500,0.4); ja.turn(E(f6),100,0.5)
    # f7: 줄지어 지나가며 모두 같은 말 (나가는 것 + 짐 싣고 돌아오는 것)
    t7=T(f7)
    for i,(b,dt,ld,lane,z0,z1) in enumerate([(b3,0.0,0,9,250,-760),(b0,0.9,1,-9,-760,250),(b4,1.8,0,9,250,-760),(b1,2.7,1,-9,-760,250),(b5,3.6,0,9,250,-760)]):
        if not ld: vis(A,b.load,[])
        te=run(b,t7+dt,z0,z1,lane); drum(A,b,t7+dt+0.4,te)
    vis(A,b0.load,[(t7,T(f10))]); vis(A,b1.load,[(t7,T(f10))])
    tw.look(T(f8),-52,-246,0.3); tw.arm('l',T(f8)+0.4,T(f8)+2.2,rx=-70); cyc(A,tw.part('head'),'rotation',T(f8)+2.6,E(f8),(0,24,0),(0,-24,0),0.6,rest=(0,0,0)); ja.look(T(f8),-112,-330,0.4)
    for i,(b,dt,lane,z0,z1) in enumerate([(b2,0.3,-9,-760,250),(b3,2.0,-9,-760,250)]): run(b,T(f8)+dt,z0,z1,lane,sp=220)
    vis(A,b2.load,[(T(f8),T(f10))]); vis(A,b3.load,[(T(f8),T(f10))])
    # f10: 둘이 굴 입구로 걸어 들어감
    ja.go(T(f10)+0.2,E(f10)-0.2,-6,240,per=0.7); tw.go(T(f10)+0.6,E(f10),8,215,per=0.45); run(b4,T(f10)+0.5,-760,250,-9,sp=330)
    ja.show([(0,E(f10)+0.2),(tK,T(k11)+1.6)]); tw.show([(0,E(f10)+0.2),(tK,L)])
    # ---------- 끝: 언덕 사이 막다른 곳 (해 질 녘) ----------
    CX,CZ=-470,-150       # 구석 (두 언덕 (-560,-60)·(-420,60) 사이)
    jx,jz=-440,-70; tx,tz=-398,-52
    ja.at(tK,jx,jz,150); tw.at(tK,tx,tz,150)
    army=brs+[BR(M,A,top,0,300,0,f'a{k}_',cartless=True) for k in range(6)]
    for b in army[6:]: b.show([(tK,L)])
    spots=[]
    for k,b in enumerate(army):
        a=math.radians(-35+k*13); r=150+(k%3)*34; sx=jx+r*math.sin(a)+30; sz=jz-r*math.cos(a)
        spots.append((sx,sz)); b.at(tK,sx+40*math.sin(a),sz-150,0); b.go(tK+0.2+k*0.1,T(k1)+2.6+k*0.1,sx,sz,per=0.28,amp=34); b.look(T(k1)+2.9,jx,jz,0.2)
        if b.cart is not None: vis(A,b.load,[]) if k!=0 else None
        drum(A,b,T(k1)+3.0,T(k10))
    vis(A,army[0].load,[]) 
    # 화살 수레: 화살 더미 + 날아오는 구리 화살
    dc=M.group('dartpile',[jx+60,6,jz-200],[M.cube('dart',[jx+56+k*2,8,jz-206],[jx+57+k*2,9,jz-190],'copper') for k in range(5)]); top.append(dc); vis(A,dc,[(T(k2),T(k10))])
    for k in range(14):
        sx,sz=spots[k%12]; t=T(k2)+0.5+k*0.9
        if t>T(k10)-0.8: break
        ex=jx+((k*37)%60-30); ez=jz+26+((k*17)%20); ey=6+((k*13)%40)
        g=M.group(f'dart{k}',[sx,26,sz],[M.cube('dart',[sx-0.6,25.4,sz-8],[sx+0.6,26.6,sz+8],'copper')]); top.append(g)
        A.add(g,'position',[(0,(0,0,0)),(t,(0,0,0)),(t+0.45,(-(ex-sx),ey-26+10,ez-sz))]); A.add(g,'scale',[(0,(0,0,0)),(t-0.02,(0,0,0)),(t,(1,1,1)),(t+0.45,(1,1,1)),(t+1.6,(1,1,1)),(t+1.7,(0,0,0))])
    ja.arm('r',T(k2)+1.5,T(k6),rx=-88); tw.arm('r',T(k2)+1.6,T(k6),rx=-85)
    for k in range(5): puff(M,A,top,jx+6,24,jz-14,T(k2)+2.0+k*1.3,0.3,3,'fl1',5,4,1.6,seed=k); puff(M,A,top,tx+4,24,tz-14,T(k2)+2.4+k*1.3,0.4,3,'th',5,6,1.6,seed=k+9)
    for k,b in enumerate(army[1:4]):      # 맞은 것들은 물러남
        t=T(k2)+2.2+k*1.3; b.hold(t); b.go(t,t+0.6,spots[k+1][0]+60,spots[k+1][1]-120,per=0.25,face=False)
    ja.A.add(ja.part('head'),'rotation',[(T(k4),(0,0,0)),(T(k4)+0.5,(0,-50,0)),(E(k5),(0,-50,0)),(E(k5)+0.3,(0,0,0))])
    ja.look(T(k6),tx,tz,0.3); ja.arm('l',T(k6)+0.4,T(k6)+2.6,rx=-165,rz=-10); tw.look(T(k6)+0.5,jx,jz,0.3); cyc(A,tw.part('head'),'rotation',T(k6)+2.8,E(k6),(0,25,0),(0,-25,0),0.5,rest=(0,0,0))
    tw.look(T(k7),jx+60,jz-160,0.3); tw.arm('r',T(k7)+0.3,T(k10)+1.5,rx=-85); ja.look(T(k7)+0.4,jx+60,jz-160,0.3); ja.arm('r',T(k7)+0.5,T(k8),rx=-88)
    for k in range(4): puff(M,A,top,tx+4,24,tz-14,T(k7)+0.8+k*0.7,0.4,3,'th',5,6,1.6,seed=k+20)
    ja.look(T(k8),tx,tz,0.3); ja.nod(T(k8)+0.6,E(k8),8,0.6); tw.look(T(k8)+0.3,jx,jz,0.3)
    ja.look(T(k9),jx+60,jz-160,0.5)
    # 푸츠의 로켓: 불기둥을 내뿜으며 내려와 수레 미는 것들을 흩어 버림
    RX,RZ=jx+140,jz-190
    rk=actor(M,A,top,aux_rocket(M,'r_'),'r_',RX+500,RZ-300,-60,y=700,legs=None); rk.show([(T(k10)-0.2,L)])
    under=rk.part('under'); A.add(under,'scale',[(0,(2.2,3.2,2.2)),(L,(2.2,3.2,2.2))]); vis(A,rk.part('flame'),[(T(k12),L)]); flicker(A,rk.part('flame'),T(k12),L,0.2)
    t10=T(k10); rk.at(t10-0.2,RX+420,RZ-260,-60,y=640); rk.go(t10,t10+2.6,RX,RZ,y=150,walk=False,face=False,interp='catmullrom'); rk.go(t10+2.6,E(k10),RX,RZ,y=14,walk=False,face=False)
    for k in range(6): puff(M,A,top,RX+((k*53)%120-60),6,RZ+((k*31)%120-60),t10+1.6+k*0.35,1.4,8,'fl2' if k%2 else 'o3',60,40,8,seed=k)
    for k,b in enumerate(army):
        t=t10+1.4+(k%5)*0.25; a=math.radians(k*30+10); b.hold(t); b.go(t,t+1.3,jx+900*math.sin(a)+200,jz-900*abs(math.cos(a))-200,per=0.2,amp=40); b.show([(0,t+1.4)] if b in brs else [(tK,t+1.4)])
    ja.go(T(k11)+0.2,T(k11)+1.5,RX-24,RZ+18,per=0.4,amp=40)
    leap(tw,T(k11)+2.2,T(k11)+4.2,tx-40,tz+420,h=300,stick=0.0); tw.show([(0,E(f10)+0.2),(tK,T(k11)+4.2)]) if False else None
    A.add(tw.out,'scale',[(T(k11)+4.15,(1,1,1)),(T(k11)+4.2,(0,0,0))])
    # 밤: 로켓이 사막 위를 돌며 찾음
    t12=T(k12); rk.go(E(k11)-0.2,t12,RX,RZ,y=120,walk=False,face=False); 
    pts=[(-300,-500),(300,-300),(500,200),(0,500),(-500,200),(-300,-400)]
    for i,(x,z) in enumerate(pts):
        ta=t12+(T(kend)-0.2-t12)*i/len(pts); tb=t12+(T(kend)-0.2-t12)*(i+1)/len(pts); rk.go(ta,tb,x,z,y=260,walk=False,face=True)
    vis(A,under,[(t10-0.2,t12)])
    # 샷
    sh('도시',    'F',f1-1,f2,cam((0,[-300,330,-900],[0,90,300]),(1,[-170,50,-520],[0,60,200])))
    sh('수레들',  'F',f2,f3,cam((0,[40,12,-300],[9,20,-60]),(1,[34,18,-360],[9,18,-200])),fps=24)
    sh('통몸',    'F',f3,f4,cam((0,[40,20,-34],[0,16,0]),(1,[-46,24,-30],[0,14,0])),fps=24,follow='b1_mv')
    sh('막아섬',  'F',f4,f5,cam((0,[-30,34,-390],[6,22,-210]),(1,[-50,30,-340],[6,22,-200])),fps=24)
    sh('북',      'F',f5,f6,cam((0,[40,60,-250],[9,24,-170]),(1,[26,44,-222],[9,24,-170])),fps=24)
    sh('밀침',    'F',f6,f7,cam((0,[-120,30,-300],[0,22,-220],0),(0.25,[-120,30,-300],[0,22,-220],1),(1,[-130,40,-200],[0,18,-500],0)),fps=24,shake=2)
    sh('모두',    'F',f7,f8,cam((0,[60,14,-520],[0,24,-200]),(1,[90,60,-560],[0,30,-100])),fps=24)
    sh('맞아아니야','F',f8,f9,orbit((-90,-300),110,32,-140,-80,(-90,26,-300),r1=96))
    sh('다른방식','F',f9,f10,cam((0,[-200,40,-430],[0,50,250]),(1,[-120,120,-560],[0,80,300])),fps=24)
    sh('굴로',    'F',f10,g1-0,cam((0,[-70,40,-60],[0,26,200]),(1,[-60,44,120],[0,22,250])),fps=24)
    sh('막다른곳','F',k1,k2,cam((0,[jx+190,170,jz-430],[jx,30,jz]),(1,[jx+150,70,jz-320],[jx,26,jz])),DUSK,fps=24)
    sh('화살',    'F',k2,k3,cam((0,[jx+80,26,jz-150],[jx-10,26,jz+40],0.3),(1,[jx+50,30,jz-110],[jx-10,26,jz+40],1)),DUSK,fps=24,shake=2)
    sh('해가진다','F',k3,k4,cam((0,[jx+40,40,jz-260],[jx,40,jz]),(1,[jx+100,330,jz-600],[jx,120,jz+400])),DUSK)
    sh('깨달음',  'F',k4,k6,orbit((jx+10,jz),80,34,-5,50,(jx+12,28,jz+6),r1=64),DUSK)
    sh('가라',    'F',k6,k7,cam((0,[jx+70,30,jz-80],[jx-6,28,jz+10]),(1,[jx+50,32,jz-60],[jx-10,30,jz+16])),DUSK)
    sh('곁에',    'F',k7,k8,cam((0,[tx+70,26,tz-60],[jx+10,24,jz],0.5),(1,[tx+50,30,tz-90],[jx+10,24,jz-10],1)),DUSK,fps=24,shake=2)
    sh('사나이',  'F',k8,k10,orbit((jx-4,jz+10),70,32,30,-30,(jx-6,28,jz+12),r1=56),DUSK)
    sh('불기둥',  'F',k10,k11,cam((0,[jx+10,14,jz-40],[RX+200,500,RZ-100],0),(0.45,[jx+6,18,jz-34],[RX,160,RZ],0.6),(1,[jx-10,30,jz-20],[RX,30,RZ],1)),DUSK,fps=24,shake=6)
    sh('트윌떠남','F',k11,k12,cam((0,[RX-110,34,RZ-90],[RX-20,24,RZ+20],0.6),(0.4,[RX-120,36,RZ-80],[tx,30,tz],0.3),(0.7,[RX-150,30,RZ-110],[tx-20,200,tz+150],0),(1,[RX-160,30,RZ-120],[tx-30,120,tz+300],0)),DUSK,fps=24,shake=2)
    sh('찾는밤',  'F',k12,kend,cam((0,[0,90,-900],[0,240,0]),(1,[100,420,-1000],[0,200,100])),NIGHT)
    num(k3,'화성의 밤 = 영하 약 62℃ (원문 화씨 영하 80도)')
    return save(M,A,top,'진흙도시','F')

# =====================================================================
#  G : 굴 속 — 전등 미로 · 큰 바퀴의 방 · 수정 · 몰려오는 것들 · 연기가 알려 준 출구
# =====================================================================
def set_G():
    M,A=newset(); top=[]
    # 통로 (z -700 ~ -160, 폭 150, 높이 100) + 둥근 큰 방 (가운데 z 140, 반지름 300)
    def box(n,fr,to,col): top.append(M.cube(n,fr,to,col))
    for z in range(-704,-160,64):
        for x in (-75,-11,53): box('cfloor',[x,-8,z],[x+64,0,z+64],'cave' if ((x+75)//64+z//64)%2 else 'cave2')
        box('cwall',[75,0,z],[110,100,z+64],'cave2' if (z//64)%2 else 'cave'); box('cwall',[-110,0,z],[-75,100,z+64],'cave' if (z//64)%2 else 'cave2')
        box('cceil',[-110,100,z],[110,118,z+64],'cave_d'); box('rib',[72,0,z],[78,100,z+6],'cave_d'); box('rib',[-78,0,z],[-72,100,z+6],'cave_d'); box('ribt',[-78,94,z],[78,100,z+6],'cave_d')
    for i,z in enumerate(range(-650,-180,120)):
        top+= cave_light(M,74 if i%2 else -74,62,z,-1 if i%2 else 1)
    for i,(sx,z) in enumerate([(1,-560),(-1,-430),(1,-300)]):      # 옆 굴 (어두운 구멍)
        box('side',[sx*72 if sx>0 else -76,0,z-22],[sx*76 if sx>0 else -72,60,z+22],'hole')
    mws=[]
    for i,(x,z) in enumerate([(-54,-500),(54,-370),(-54,-240)]):
        k,w=idle_machine(M,f'im{i}_',x,z); top+= k; top.append(w); A.add(w,'rotation',[(0,(0,0,0)),(L,(0,0,(1 if i%2 else -1)*360*L/3))])
    R=300; CZ=140
    for x in range(-320,320,64):
        for z in range(CZ-320,CZ+320,64):
            if (x+32)**2+(z+32-CZ)**2<(R+40)**2: box('rfloor',[x,-8,z],[x+64,0,z+64],'cave' if (x//64+z//64)%2 else 'cave2')
    n=20
    for i in range(n):
        a=i/n*6.283; cx=R*math.sin(a); cz=CZ-R*math.cos(a)
        if abs(cx)<150 and cz<CZ: continue                       # 통로 쪽은 뚫림
        w=56; box('rwall',[cx-w,0,cz-w],[cx+w,150,cz+w],'cave' if i%2 else 'cave2')
        if i%3==0: top+= cave_light(M,cx*0.8,70,CZ+(cz-CZ)*0.8,0.01)
    for j in range(7):       # 둥근 천장: 줄어드는 고리
        r0=R+30-j*42; r1=r0-52; y=150+j*26
        for i in range(12):
            a=i/12*6.283; cx=(r0+r1)/2*math.sin(a); cz=CZ-(r0+r1)/2*math.cos(a); w=max(34,(r0+r1)/2*0.3)
            box('dome',[cx-w,y,cz-w],[cx+w,y+30,cz+w],'cave_d' if (i+j)%2 else 'cave2')
    box('skylight',[-10,326,CZ-44],[10,332,CZ+44],'fl3'); box('beam',[-6,0.2,CZ-30],[6,0.6,CZ+30],'cave_l')
    box('door_arch',[-110,100,-170],[110,150,-150],'cave_d')
    # 큰 바퀴 + 찧는 구덩이 + 가루 더미
    WZ=CZ+40; wh=big_wheel(M,'wheel',0,84,WZ,R=72,width=64); top.append(wh); A.add(wh,'rotation',[(0,(0,0,0)),(L,(360*L/9,0,0))])
    for sx in (-1,1): box('axle_post',[sx*46-8,0,WZ-10],[sx*46+8,96,WZ+10],'steel_d'); box('axle',[sx*40-6,78,WZ-6],[sx*40+6,90,WZ+6],'copper')
    box('pit',[-40,0,WZ-70],[40,1.6,WZ+70],'hole'); box('pit_rim',[-46,0,WZ-76],[-40,5,WZ+76],'cave_d'); box('pit_rim',[40,0,WZ-76],[46,5,WZ+76],'cave_d')
    for k,(x,z,s) in enumerate([(-70,WZ+60,14),(76,WZ+50,12),(-60,WZ-70,9),(66,WZ-80,10)]): box('powder',[x-s,0,z-s],[x+s,s*0.6,z+s],'sand'); box('powder',[x-s*0.5,s*0.6,z-s*0.5],[x+s*0.5,s,z+s*0.5],'o3')
    # 수정 받침대 (바퀴 뒤)
    PZ=CZ+190; top+= pedestal(M,0,PZ,30,22,'cped')
    cr=M.group('crystal',[0,26,PZ],[M.cube('crys',[-2.4,22,PZ-2.4],[2.4,29,PZ+2.4],'crystal'), M.cube('crys_g',[-3.6,23.6,PZ-3.6],[3.6,27.4,PZ+3.6],'crystal')]); top.append(cr)
    cyc(A,cr,'scale',0,L,(1,1,1),(1.25,1.1,1.25),0.9,rest=(1,1,1))
    for k in range(8):
        a=k/8*6.283; g=M.group(f'ray{k}',[0,26,PZ],[M.cube('ray',[10*math.cos(a)-0.7,25.3,PZ+10*math.sin(a)-0.7],[10*math.cos(a)+0.7,26.7,PZ+10*math.sin(a)+0.7],'crystal')]); top.append(g); cyc(A,g,'scale',0,L,(1,1,1),(2.4,1,2.4),0.7+k*0.05,rest=(1,1,1))
    g1=I('전등이 켜진 미로를'); g2=I('거대한 바퀴가'); g3=I('쏟아붓습니다'); g4=I('스스로 바퀴 밑으로'); g5=I('그 수레를 받아'); g6=I('어깨를 으쓱'); g7=I('달걀만 한 수정'); g8=I('사마귀가 말라')
    h1=I('사방에서 북소리'); h2=I('몰려오고 있었습니다'); h3=I('연기가 한쪽으로'); k1=I('막다른 곳에 몰립니다')
    ja=J(M,A,top,-20,-660,180); tw=TW(M,A,top,24,-690,180)
    d1=E(g1)-T(g1); ja.go(T(g1),T(g1)+d1*0.6,-24,-230,per=0.8); tw.go(T(g1)+0.3,T(g1)+d1*0.62,26,-270,per=0.5)
    ja.headturn(T(g1)+1.0,T(g1)+d1*0.5,ry=45); ja.go(T(g1)+d1*0.6,E(g1),-90,10,per=0.8); tw.go(T(g1)+d1*0.62,E(g1),-124,-30,per=0.5)
    ja.look(E(g1),0,WZ); tw.look(E(g1),0,WZ)
    # 수레 미는 것들: 통로 → 구덩이 앞 → 쏟고 → 옆으로 나감
    bs=[BR(M,A,top,0,-700,180,f'b{k}_',load=True) for k in range(5)]
    def dump(b,t0,exit_x=1):
        b.at(t0,0,-200,180); b.go(t0,t0+1.6,0,WZ-104,per=0.28,amp=34,face=False)
        A.add(b.cart,'rotation',[(t0+1.6,(0,0,0)),(t0+2.0,(-38,0,0)),(t0+2.6,(-38,0,0)),(t0+3.0,(0,0,0))]); A.add(b.load,'scale',[(t0+2.0,(1,1,1)),(t0+2.5,(0,0,0))])
        puff(M,A,top,0,6,WZ-66,t0+2.2,1.0,7,'o3',26,14,4,seed=int(t0*10)); return t0+3.1
    te=dump(bs[0],T(g2)+0.5); bs[0].go(te,te+1.6,230,CZ-60,per=0.28,amp=34)
    te=dump(bs[1],T(g3)+0.2); bs[1].go(te,te+1.6,-230,CZ-80,per=0.28,amp=34); te=dump(bs[2],T(g3)+3.0); bs[2].go(te,te+1.6,230,CZ-40,per=0.28,amp=34)
    # g4: 짐을 비운 하나(b3)가 수레를 두고 스스로 바퀴 밑으로 — 수레는 따로 남김
    b3=bs[3]; t4=dump(b3,T(g4)-2.6); A.add(b3.cart,'scale',[(0,(1,1,1)),(t4+0.3,(1,1,1)),(t4+0.32,(0,0,0))])
    lone=cart(M,'lone_'); la=actor(M,A,top,lone,'lone_',-34,WZ-128,180,legs=None); la.show([(t4+0.3,T(g5)+1.2)])
    b3.go(t4+0.3,t4+0.9,22,WZ-96,per=0.3,face=False); b3.go(T(g4)+3.0,T(g4)+5.2,0,WZ-30,per=0.6,amp=20); b3.show([(0,T(g4)+5.2)])
    puff(M,A,top,0,8,WZ-20,T(g4)+5.2,1.2,8,'o3',20,12,4,seed=77)
    # g5: 다음 것(b4, 수레 없이 온)이 그 수레를 받아 밀고 나감
    b4=bs[4]; vis(A,b4.load,[]); A.add(b4.cart,'scale',[(0,(0,0,0)),(T(g5)+1.2,(0,0,0)),(T(g5)+1.22,(1,1,1))])
    b4.at(T(g5)-1.5,200,CZ-90,-90); b4.go(T(g5)-1.5,T(g5)+0.9,-10,WZ-150,per=0.3,amp=30); b4.turn(T(g5)+0.9,180,0.3); b4.go(T(g5)+1.3,T(g5)+1.5,-34,WZ-152,per=0.3,face=False)
    b4.go(T(g5)+1.8,E(g5)+0.6,0,-640,per=0.28,amp=34)
    ja.tilt(T(g4)+3.2,E(g4),10); ja.look(T(g6),-124,-30,0.4)
    tw.look(T(g6),-90,10,0.3); tw.arm('l',T(g6)+1.6,E(g6)-0.2,rx=-40,rz=50); tw.arm('r',T(g6)+1.6,E(g6)-0.2,rx=-40,rz=-50); tw.tilt(T(g6)+1.6,E(g6),10)
    ja.go(T(g7)-0.6,T(g7)+2.4,-60,PZ-10,per=0.8); ja.look(T(g7)+2.5,0,PZ); tw.go(T(g7),T(g7)+2.8,-110,PZ-40,per=0.5); tw.look(T(g7)+2.9,0,PZ)
    ja.go(T(g8),T(g8)+0.8,-30,PZ-4,per=0.6); ja.look(T(g8)+0.9,0,PZ,0.2); ja.arm('l',T(g8)+1.0,E(g8)-0.3,rx=-75)
    # h1~h3: 몰려옴 → 트윌이 수레의 풀에 불을 붙임 → 연기가 흘러가는 쪽이 출구
    th=T(h1)-0.4; ja.at(th,-40,WZ-170,160); tw.at(th,0,WZ-150,180)
    crowd=[BR(M,A,top,0,-700,180,f'c{k}_',cartless=True) for k in range(7)]
    for k,b in enumerate(crowd):
        a=math.radians(k*51+20); x0=260*math.sin(a); z0=CZ-260*math.cos(a)+120; b.show([(th,L)]); b.at(th,x0,z0,0); b.look(th+0.05,-20,WZ-160,0.05)
        b.go(T(h1)+0.6+k*0.15,E(h2),x0*0.5-10,(z0-(WZ-160))*0.5+WZ-160,per=0.4,amp=28); drum(A,b,T(h1),T(k1))
    ja.look(T(h1)+0.5,200,CZ,0.3); ja.headturn(T(h1)+1.0,E(h1),ry=-70); tw.look(T(h2),-200,CZ,0.3)
    fc=bs[1]; A.add(fc.cart,'rotation',[(T(h3)-0.5,(0,0,0))]); A.add(fc.load,'scale',[(T(h3)-0.6,(0,0,0)),(T(h3)-0.5,(1,1,1))])
    fc.at(T(h3)-0.4,60,-150,0); fc.go(T(h3)-0.4,T(h3)+1.2,30,WZ-190,per=0.3,amp=30,face=False); fc.go(T(h3)+1.2,E(h3),20,WZ-60,per=0.5,amp=24,face=False)
    tw.look(T(h3)+0.6,30,WZ-200,0.2); tw.arm('l',T(h3)+0.8,T(h3)+1.8,rx=-80)
    fire=M.group('cartfire',[0,10,-24],[M.cube('fl',[-4,9,-30],[4,18,-18],'fl2'), M.cube('fl',[-2.5,17,-28],[2.5,25,-21],'fl1'), M.cube('fl',[-1,24,-26],[1,30,-23],'fl3')]); fc.out['children'].append(fire)
    vis(A,fire,[(T(h3)+1.3,L)]); flicker(A,fire,T(h3)+1.3,L,0.22)
    for k in range(9):      # 연기가 통로(출구) 쪽으로 흘러감
        s=5+k%3*2; g=M.group(f'exsmoke{k}',[30,40,WZ-200],[M.cube('smk',[30-s,40-s,WZ-200-s],[30+s,40+s,WZ-200+s],'smoke' if k%2 else 'smoke_l')]); top.append(g)
        t=T(h3)+1.6+k*0.45; A.add(g,'position',[(0,(0,0,0)),(t,(0,0,0)),(t+2.4,((k%3-1)*20,30+(k%2)*14,-560))]); A.add(g,'scale',[(0,(0,0,0)),(t-0.02,(0,0,0)),(t,(0.5,0.5,0.5)),(t+1.2,(1.6,1.6,1.6)),(t+2.4,(0.4,0.4,0.4)),(t+2.42,(0,0,0))])
    ja.look(T(h3)+3.0,0,-600,0.3); tw.look(T(h3)+3.2,0,-600,0.3)
    te=E(h3); ja.go(te-1.6,te+0.3,-10,-500,per=0.4,amp=40); tw.go(te-1.4,te+0.3,20,-520,per=0.3,amp=34)
    # 샷
    sh('미로',    'G',g1,g2,cam((0,[0,50,-560],[-10,36,-200]),(0.6,[10,40,-330],[-20,30,-60]),(1,[30,60,-200],[0,70,WZ])),CAVE,fps=24)
    sh('바퀴',    'G',g2,g3,cam((0,[-40,24,-110],[0,90,WZ]),(1,[-60,130,-60],[0,70,WZ])),CAVE,fps=24)
    sh('쏟는다',  'G',g3,g4,orbit((0,WZ-70),190,60,-55,25,(0,30,WZ-50),r1=150,h1=44),CAVE,fps=24)
    sh('스스로',  'G',g4,g5,cam((0,[110,50,WZ-200],[0,30,WZ-70]),(0.5,[96,44,WZ-180],[0,30,WZ-50]),(1,[70,36,WZ-160],[0,30,WZ-20])),CAVE,fps=24)
    sh('수레받음','G',g5,g6,cam((0,[-90,60,WZ-230],[-20,20,WZ-140]),(1,[-40,60,-180],[0,24,-420])),CAVE,fps=24)
    sh('으쓱',    'G',g6,g7,orbit((-106,-10),76,34,-150,-100,(-106,28,-10),r1=66),CAVE)
    sh('수정',    'G',g7,g8,cam((0,[-150,50,PZ-200],[0,26,PZ]),(1,[-50,34,PZ-90],[0,26,PZ])),CAVE)
    sh('사마귀',  'G',g8,h1-1,cam((0,[-80,36,PZ-70],[-10,26,PZ-2]),(1,[-56,32,PZ-52],[-8,25,PZ-2])),CAVE,fps=24)
    sh('북소리',  'G',h1-1,h2,cam((0,[0,50,-20],[0,60,WZ],0),(0.5,[0,110,-40],[-20,30,WZ-150],0.5),(1,[30,80,-60],[-20,30,WZ-150],1)),CAVE,fps=24,shake=2)
    sh('몰려옴',  'G',h2,h3,orbit((-20,WZ-160),130,40,-120,-30,(-20,26,WZ-160),r1=100),CAVE,fps=24,shake=1.5)
    sh('연기',    'G',h3,k1,cam((0,[-110,40,WZ-120],[20,24,WZ-190]),(0.4,[-100,50,WZ-90],[20,40,WZ-260]),(1,[-40,90,WZ-40],[0,50,-560])),CAVE,fps=24)
    return save(M,A,top,'굴속','G')

SETS=dict(S=set_S,X=set_X,Y=set_Y,A=set_A,B=set_B,C=set_C,D=set_D,E=set_E,F=set_F,G=set_G)
if __name__=='__main__':
    want=sys.argv[1] if len(sys.argv)>1 else 'all'
    info={}
    for k,f in SETS.items():
        if want!='all' and k not in want:
            _s=M_save=None
            import 블록인물 as _b; _orig=Model.save; Model.save=lambda *a,**kw: None      # 샷 목록만 필요 → 모형은 저장 안 함
            try: info[k]=f()
            finally: Model.save=_orig
        else: info[k]=f()
    for k in info: info[k].setdefault('ropes',[])
    json.dump(info,open(f'{OUT}/세트정보.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
    SHOTS.sort(key=lambda s:s['t0'])
    FAST={'비행','처박힘','총','도약','꽂힘','다시','뛰는트윌','나온다','달려감','사라짐','밀침','불기둥','트윌떠남','화살','출발'}      # 빠른 움직임만 1초 24장, 나머지는 12장 (촬영 시간 때문에)
    for s_ in SHOTS:
        if s_['fps']==24 and s_['name'].split('_',1)[1] not in FAST: s_['fps']=12
    for i,s in enumerate(SHOTS): s['name']=f"{i:03d}_{s['name'].split('_',1)[1]}"
    bad=[(a['name'],b['name'],round(b['t0']-a['t1'],2)) for a,b in zip(SHOTS,SHOTS[1:]) if abs(b['t0']-a['t1'])>0.02]
    if SHOTS[0]['t0']>0.02: bad.insert(0,('처음',SHOTS[0]['name'],SHOTS[0]['t0']))
    json.dump({'shots':SHOTS},open(f'{OUT}/샷목록.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
    NUMS.sort(key=lambda n:n['seg']); json.dump(NUMS,open(f'{ROOT}/숫자.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
    print(len(SHOTS),'샷',sum(round((s['t1']-s['t0'])*s['fps']) for s in SHOTS),'장',round(SHOTS[-1]['t1'],1),'초 | 이어지지 않는 곳:',bad or '없음')
