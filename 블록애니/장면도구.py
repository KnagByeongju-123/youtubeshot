"""블록 애니 장면 도구 (《화성의 오디세이》에서 쓰던 것을 따로 떼어 냄 — 새 장면 프로그램은 이걸 import)
   - Act: 움직이는 것(인물·탈것). 모형은 원점에 만들고 바깥 묶음의 위치·방향 키로 놓음 (위치 x 뒤집기 포함)
   - 샷: sh(이름, 세트, 시작초, 끝초, 카메라 키들, …) / cam()·two()·orbit() / 흔들림·시야각·기울기
   - vis·grow·cyc·puff·smoke_col·flicker
   쓰기 전에 init(영상 길이) 를 부름.  방향 yaw: 0 = -z(카메라 쪽), +90 = +x, 180 = +z"""
import math, random, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 블록인물 import Model, move, anchor, Anim, find, U
L=0; SHOTS=[]; CAPS=[]; ACTS=[]
def init(length):
    global L
    L=length; SHOTS.clear(); CAPS.clear(); ACTS.clear()

def cam(*keys):
    """키 = (u, 카메라 자리, 보는 곳[, 흔들림 배율 0~1])"""
    out=[]
    for k in keys:
        d=dict(u=k[0],pos=list(k[1]),tgt=list(k[2]))
        if len(k)>3:
            d.update(k[3] if isinstance(k[3],dict) else {'shake':k[3]})      # 넷째 = 흔들림 배율, 또는 {'fov':시야각,'roll':기울기(도),'shake':배율}
        out.append(d)
    return out
def two(p0,t0,p1=None,t1=None): return cam((0,p0,t0),(1,p1 or p0,t1 or t0))
def orbit(c,r,h,a0,a1,tgt=None,n=6,r1=None,h1=None,shake=None):
    """c=(x,z) 둘레를 a0→a1 도 만큼 도는 카메라 (0도 = -z 쪽에서 봄, +는 화면 왼쪽(+x)으로 돎). r·h 가 r1·h1 로 바뀌면 다가가며/솟으며 돎"""
    ks=[]; r1=r if r1 is None else r1; h1=h if h1 is None else h1; tgt=tgt or (c[0],h*0.6,c[1])
    for i in range(n+1):
        u=i/n; a=math.radians(a0+(a1-a0)*u); rr=r+(r1-r)*u; k={'u':u,'pos':[c[0]+rr*math.sin(a),h+(h1-h)*u,c[1]-rr*math.cos(a)],'tgt':list(tgt)}
        if shake is not None: k['shake']=shake
        ks.append(k)
    return ks
def sh(name,st,t0,t1,camk,sky=None,fps=24,**kw):
    """t0~t1 = 영상 시간(초). camk = cam()/two()/orbit() 키들. kw: follow(따라갈 묶음), shake(흔들림), only"""
    SHOTS.append(dict(name=f'{len(SHOTS):03d}_{name}',set=st,t0=round(t0,3),t1=round(t1,3),fps=fps,cam=camk,sky=sky or ['#101014','#1c1c24'],**kw))
def caption(t0,t1,text,style='Sub'): CAPS.append({'t0':round(t0,2),'t1':round(t1,2),'text':text,'style':style})

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

def actor(M,A,top,g,tag,x,z,yaw=0,y=0,legs='two'):
    a=Act(M,A,top,g,tag,x,z,yaw,y,legs); ACTS.append(a); return a
def finish_all():
    for a in ACTS: a.finish()
    ACTS.clear()
def fall(M,A,top,g,t0,x0,y0,z0,x1,z1,dur=0.9,spin=(220,0,140),keep=None):
    """떨어져 나가는 부품: 따로 만든 묶음 g(원점 기준 모형)를 (x0,y0,z0)에서 튕겨 (x1,0,z1) 바닥으로. keep 초 뒤 사라짐(None = 남음)"""
    out=M.group(g['name']+'_fall',[0,0,0],[g]); top.append(out)
    A.add(out,'position',[(0,(-x0,y0,z0)),(t0,(-x0,y0,z0)),(t0+dur*0.4,(-(x0+x1)/2,y0+12,(z0+z1)/2)),(t0+dur,(-x1,1,z1))],'catmullrom')
    A.add(g,'rotation',[(0,(0,0,0)),(t0,(0,0,0)),(t0+dur,spin)])
    sc=[(0,(0,0,0)),(max(0,t0-0.02),(0,0,0)),(t0,(1,1,1))]
    if keep is not None: sc+= [(t0+dur+keep,(1,1,1)),(t0+dur+keep+0.3,(0,0,0))]
    A.add(out,'scale',sc); return out
