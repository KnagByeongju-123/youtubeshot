"""《저공 침투》(조종석 1인칭 비행, 3분, 대사 없음) 장면 모형 + 샷 목록 + 시간표 → 연재/저공침투/장면/…
   세트: A 격납고·발진(0~12) / B 도시(12~58) / C 협곡·장애물(58~102) / D 터널(102~148) / E 핵·탈출(148~172) / F 새벽(172~180) / K 조종석 틀(한 장)
   1인칭 샷은 1초 12장으로 찍고 RIFE(중간장면.py)로 24장으로 메움. 조종석 틀·계기 글자는 조립 때 덧씌움(조종석_조립.py)
   앞 = -z, 오른쪽 = +x.  사용: python 조종석_장면.py [A|B|C|D|E|F|K|all]"""
import sys, os, json, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import ImageDraw
from 블록인물 import Anim
from 신라인물 import BigModel
from 우주_부품 import Ship, explode, burst, fighter, _panel
import 장면도구 as D
from 장면도구 import vis, caption
import 겹침면_검사
ROOT='/home/user/youtubeshot/연재/저공침투'; OUT=f'{ROOT}/장면'; os.makedirs(OUT,exist_ok=True)
L=180.0; D.init(L); FPS=12; CUES=[]; FIRE=[]; HIT=[]; WARN=[]; FLASH=[]; RUNS=[]
def cue(t,kind,vol=1.0): CUES.append({'t':round(t,2),'kind':kind,'vol':vol})
add=lambda a,b: tuple(a[i]+b[i] for i in range(3)); sub=lambda a,b: tuple(a[i]-b[i] for i in range(3)); mul=lambda a,k: tuple(v*k for v in a)
def norm(a): n=math.sqrt(sum(v*v for v in a)) or 1; return tuple(v/n for v in a)
def cross(a,b): return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
clamp=lambda v,a,b: max(a,min(b,v))
def lerpk(keys,t,dv=0.0):
    if not keys: return dv
    if t<=keys[0][0]: return keys[0][1]
    for a,b in zip(keys,keys[1:]):
        if a[0]<=t<=b[0]: f=(t-a[0])/max(1e-6,b[0]-a[0]); f=f*f*(3-2*f); return a[1]+(b[1]-a[1])*f
    return keys[-1][1]

class Path:
    """비행 길: 길목 점 (t,x,y,z) 을 부드럽게 잇는 곡선. rolls=[(t,도)] 더 기울이기, fovs=[(t,시야각)]"""
    def __init__(s,pts,rolls=(),fovs=()):
        s.P=sorted(tuple(float(v) for v in p) for p in pts); s.rolls=list(rolls); s.fovs=list(fovs); P=s.P; s.m=[]
        for i in range(len(P)):
            a=P[max(0,i-1)]; b=P[min(len(P)-1,i+1)]; s.m.append(tuple((b[k]-a[k])/max(1e-6,b[0]-a[0]) for k in (1,2,3)))
    def pos(s,t):
        P=s.P
        if t<=P[0][0]: return tuple(P[0][k+1]+s.m[0][k]*(t-P[0][0]) for k in range(3))
        if t>=P[-1][0]: return tuple(P[-1][k+1]+s.m[-1][k]*(t-P[-1][0]) for k in range(3))
        for i in range(len(P)-1):
            if P[i][0]<=t<=P[i+1][0]:
                h=P[i+1][0]-P[i][0]; u=(t-P[i][0])/h; u2=u*u; u3=u2*u
                return tuple((2*u3-3*u2+1)*P[i][k+1]+(u3-2*u2+u)*h*s.m[i][k]+(-2*u3+3*u2)*P[i+1][k+1]+(u3-u2)*h*s.m[i+1][k] for k in range(3))
    def fw(s,t,d=0.3): return norm(sub(s.pos(t+d),s.pos(t-d)))
    def yaw(s,t): f=s.fw(t); return math.degrees(math.atan2(f[0],-f[2]))
    def frame(s,t):
        f=s.fw(t); r=norm(cross(f,(0,1,0))); return f,r,cross(r,f)
    def roll(s,t):
        """돌 때 기울기: 0.6초 동안 얼마나 돌았나 → 기울기(오른쪽으로 돌면 +), 앞뒤 5점 평균으로 고르게"""
        def raw(t):
            d=(s.yaw(t+0.3)-s.yaw(t-0.3)+180)%360-180; return clamp(d/0.6*0.75,-58,58)
        return sum(raw(t+k*0.1) for k in range(-3,4))/7+lerpk(s.rolls,t)
    def speed(s,t): a=s.pos(t-0.1); b=s.pos(t+0.1); return math.dist(a,b)/0.2

def pal(M):
    S=M.swatch; B=M.big
    for n,c,j in [('e_w',(226,230,236),4),('e_g',(150,158,170),5),('e_d',(84,90,104),5),('e_dd',(40,44,54),4),('e_blue',(50,110,220),5),('e_or',(255,150,40),4),('e_glass',(120,220,255),3),('e_red',(220,50,50),4),
        ('glow_c',(150,240,255),2),('glow_w',(255,255,240),2),('glow_o',(255,190,80),3),('glow_y',(255,240,140),2),('glow_r',(255,70,60),2),('glow_g',(120,255,150),2),
        ('a_k',(26,20,36),4),('a_p',(70,40,110),6),('a_m',(255,60,200),3),('a_mc',(255,190,240),2),('a_g',(120,255,120),3),
        ('fire1',(255,220,90),10),('fire2',(255,130,40),14),('fire3',(255,250,220),4),('smoke',(90,86,92),10),('black',(4,4,8),1),('sun',(255,244,200),2),
        ('conc',(96,100,110),8),('conc_d',(60,64,74),8),('steel',(120,126,138),6),('rust',(140,84,56),10),('key',(0,255,0),0)]: S(n,c,j)
    def tower(base,lit,p,seed):
        def fn(im,x,y,w,h):
            d=ImageDraw.Draw(im); r=random.Random(seed); d.rectangle([x,y,x+w-1,y+h-1],fill=base)
            for yy in range(3,h-4,6):
                for xx in range(3,w-4,6):
                    c=r.choice(lit) if r.random()<p else tuple(int(v*0.55) for v in base); d.rectangle([x+xx,y+yy,x+xx+3,y+yy+3],fill=c)
        return fn
    B('tw1',64,128,tower((44,52,74),[(255,214,120),(255,236,170),(140,200,255)],0.33,1)); B('tw2',64,128,tower((58,54,70),[(255,200,110),(255,160,90)],0.25,2))
    B('tw3',64,128,tower((34,44,58),[(150,220,255),(255,255,220)],0.42,3)); B('tw4',64,128,tower((70,74,86),[(255,220,140)],0.18,4))
    def road(im,x,y,w,h):
        d=ImageDraw.Draw(im); r=random.Random(5); d.rectangle([x,y,x+w-1,y+h-1],fill=(30,32,40))
        for k in range(0,w,32): d.rectangle([x+k,y,x+k+5,y+h-1],fill=(52,54,62)); d.rectangle([x,y+k,x+w-1,y+k+5],fill=(52,54,62))
        for k in range(160): d.point((x+r.randint(0,w-1),y+r.randint(0,h-1)),fill=r.choice([(255,214,120),(255,120,80),(140,200,255)]))
    B('road',128,128,road)
    def hazard(im,x,y,w,h):
        d=ImageDraw.Draw(im); d.rectangle([x,y,x+w-1,y+h-1],fill=(240,190,40))
        for k in range(-h,w,16): d.polygon([(x+k,y+h-1),(x+k+8,y+h-1),(x+k+8+h,y),(x+k+h,y)],fill=(24,24,28))
        d.rectangle([x,y,x+w-1,y],fill=(24,24,28)); d.rectangle([x,y+h-1,x+w-1,y+h-1],fill=(24,24,28))
    B('hazard',64,16,hazard)
    B('hull_a',64,64,_panel((30,24,42),(64,40,96),[(255,60,200),(150,90,255),(120,255,120)],22,3)); B('hull_a2',64,64,_panel((22,18,32),(48,30,76),[(255,60,200),(150,90,255)],34,4))
    B('hull_a3',64,64,_panel((40,30,56),(84,52,124),[(255,60,200)],10,5)); B('hull_e',64,64,_panel((150,156,168),(110,116,130),[(60,130,240),(255,230,120)],10,1))
    B('hull_h',64,64,_panel((70,76,90),(50,56,68),[(255,230,120),(255,120,60)],8,6)); B('dash',64,64,_panel((36,40,50),(60,66,80),[(120,240,255),(255,190,80),(120,255,150)],40,7))
    B('scr1',64,32,_panel((10,40,50),(40,180,200),[(150,240,255),(255,255,255)],30,8)); B('scr2',64,32,_panel((40,24,10),(220,140,40),[(255,220,120)],26,9))

def newset(): M=BigModel(1024); pal(M); return M,Anim(L),[]
def save(M,A,top,name,key):
    A.bake([t for t in top if isinstance(t,dict)]); n=겹침면_검사.fix(M.els,top)
    M.save(f'{OUT}/{key}_{name}.bbmodel',top,[A.json()],name=key); print(key,name,len(M.els),'상자, 겹침 고침',n,flush=True)
def pk(p): return (-p[0],p[1],p[2])

# ---------------- 탄·적·우리 기체 ----------------
def bolt(M,A,top,t,p0,p1,col='glow_c',speed=2200,length=30,thick=1.2):
    dx,dy,dz=(p1[i]-p0[i] for i in range(3)); dist=math.sqrt(dx*dx+dy*dy+dz*dz) or 1; dur=max(0.08,dist/speed); h=math.hypot(dx,dz)
    inner=M.group('b',[0,0,0],[M.cube('bolt',[-thick,-thick,-length/2],[thick,thick,length/2],col)]); o=M.group('bo',[0,0,0],[inner]); top.append(o)
    A.add(inner,'rotation',[(0,(-math.degrees(math.atan2(dy,max(h,1e-6))),0,0))]); A.add(o,'rotation',[(0,(0,math.degrees(math.atan2(dx,-dz)),0))])
    A.add(o,'position',[(0,pk(p0)),(t,pk(p0)),(t+dur,pk(p1))]); A.add(o,'scale',[(0,(0,0,0)),(max(0,t-0.02),(0,0,0)),(t,(1,1,1)),(t+dur,(1,1,1)),(t+dur+0.02,(0,0,0))])
    return dur
def shoot(M,A,top,path,t_hit,target,n=3,gap=0.11):
    """우리 기체가 쏨: 양쪽 포구에서 두 줄기씩, t_hit 에 target 에 닿게"""
    for i in range(n):
        th=t_hit-0.02-(n-1-i)*gap
        for sx in (-1,1):
            t=th-0.16
            for _ in range(4):
                f,r,u=path.frame(t); p0=add(path.pos(t),add(mul(r,9*sx),add(mul(u,-6.5),mul(f,16)))); t=th-math.dist(p0,target)/2600
            bolt(M,A,top,t,p0,target,'glow_c',speed=2600,length=34,thick=1.1)
        FIRE.append(round(t,3)); cue(t,'laser',0.8)
def drone(M,tag,k=3.2):
    s=Ship(M,tag,k); c=s.cube
    c([-2.4,-2,-3],[2.4,2,4],'a_k'); c([-1,-0.8,-9],[1,0.8,-3],'a_p'); c([3,-0.6,-8],[4.4,0.6,2],'a_p'); c([-4.4,-0.6,-8],[-3,0.6,2],'a_p')
    c([2.4,-3.6,0],[3.6,3.6,6],'a_k'); c([-3.6,-3.6,0],[-2.4,3.6,6],'a_k'); c([-0.6,2,-1],[0.6,6,5],'a_p'); c([-1.4,-1,-3.6],[1.4,1,-3],'a_m')
    s.glow('engine',[-1.6,-1.2,4],[1.6,1.2,6.2],'a_m'); return s
def turret(M,tag,k=2.6):
    s=Ship(M,tag,k); c=s.cube
    c([-5,0,-5],[5,4,5],'a_k'); c([-3.4,4,-3.4],[3.4,8,3.4],'a_p'); c([-1,5,3],[1,7,11],'a_k'); c([-4.6,8,-1.6],[-2.6,10,1.6],'a_m'); c([2.6,8,-1.6],[4.6,10,1.6],'a_m')
    s.glow('eye',[-1.4,5.2,3.4],[1.4,6.8,4.4],'a_m'); return s
class Foe:
    def __init__(s,M,A,top,ship,pos,yaw=180):
        s.M=M; s.A=A; s.top=top; s.ship=ship; s.root=ship.group(); s.fx=M.group(ship.tag+'fx',[0,0,0],[]); s.out=M.group(ship.tag+'mv',[0,0,0],[s.root,s.fx]); top.append(s.out)
        s.p=pos; A.add(s.out,'rotation',[(0,(0,yaw,0))]); s.keys=[(0,pk(pos))]; s.t1=L; s.t0=0
    def fly(s,pts):
        """pts=[(t,(x,y,z))…] 로 움직임"""
        s.keys=[(0,pk(pts[0][1]))]+[(t,pk(p)) for t,p in pts]; s.p=pts[-1][1]; s.pts=pts; return s
    def at(s,t):
        if not hasattr(s,'pts'): return s.p
        return tuple(lerpk([(a,b[k]) for a,b in s.pts],t) for k in range(3)) if False else s._lin(t)
    def _lin(s,t):
        P=s.pts
        if t<=P[0][0]: return P[0][1]
        for a,b in zip(P,P[1:]):
            if a[0]<=t<=b[0]: f=(t-a[0])/max(1e-6,b[0]-a[0]); return tuple(a[1][k]+(b[1][k]-a[1][k])*f for k in range(3))
        return P[-1][1]
    def boom(s,t,power=70,dur=1.5,size=1.0,cuek='boom'):
        M=s.M; cue(t,cuek,min(1.5,0.7+size*0.25)); s.t1=t+dur+0.4; HIT.append((round(t,2),round(0.5+size*0.3,2)))
        explode(s.A,s.ship,t,power=power,dur=dur,seed=len(M.els))
        burst(M,s.A,s.fx['children'],t,(0,0,0),n=int(7+size*3),speed=40+size*30,size=3+size*2.2,dur=1.0+size*0.2,seed=len(M.els))
        g=M.group(f'{s.ship.tag}fb',[0,0,0],[M.cube('fb',[-1,-1,-1],[1,1,1],'fire3')]); s.fx['children'].append(g); k=9+size*8
        s.A.add(g,'scale',[(0,(0,0,0)),(t-0.02,(0,0,0)),(t,(k*0.3,)*3),(t+0.14,(k,)*3),(t+0.45,(0,0,0))]); s.A.add(g,'rotation',[(t,(0,0,0)),(t+0.45,(60,80,30))]); return s
    def show(s,t0): s.t0=t0; return s
    def done(s): s.A.add(s.out,'position',s.keys); vis(s.A,s.out,[(s.t0,s.t1)])
def enemy_fire(M,A,top,path,foe,t,miss=(14,8,0)):
    """적이 쏨: 조종석 옆을 스쳐 지나감"""
    p0=foe.at(t) if isinstance(foe,Foe) else foe; p0=add(p0,(0,6,0)); dur=0.5
    for _ in range(3): aim=add(path.pos(t+dur),miss); dur=math.dist(p0,aim)/1100
    p1=add(p0,mul(sub(aim,p0),1.5)); bolt(M,A,top,t,p0,p1,'glow_r',speed=1100,length=28,thick=1.4); cue(t,'laser2',0.6); WARN.append(round(t+dur,2))
def engage(M,A,top,path,tb,off=(0,0,0),kind='drone',lead=0.85,fire_at=(2.6,1.7),size=1.0,tag=None):
    """tb 에 터질 적을 길 앞쪽(lead 초 앞)에 둠. 그 전에 적이 쏘고, 우리가 쏴서 맞힘"""
    tag=tag or f'f{len(M.els)}_'; q=add(path.pos(tb+lead),off)
    fo=Foe(M,A,top,(drone if kind=='drone' else turret)(M,tag),q,yaw=180); fo.show(max(0,tb-9))
    for k,dt in enumerate(fire_at): enemy_fire(M,A,top,path,fo,tb-dt,miss=((16 if k%2 else -15),7+3*k,0))
    shoot(M,A,top,path,tb,add(q,(0,2,0))); fo.boom(tb,size=size); fo.done(); return fo
def player(M,A,top,path,spans):
    """밖에서 보는 샷에만 보이는 우리 기체 (길을 그대로 따라감)"""
    sp=fighter(M,'pl_','e_or'); root=sp.group(); out=M.group('pl_mv',[0,0,0],[root]); top.append(out); pos=[]; ry=[]; rr=[]
    for a,b in spans:
        n=int((b-a+0.6)*24)
        for i in range(n+1):
            t=a-0.3+i/24; f=path.fw(t,0.2); h=math.hypot(f[0],f[2])
            pos.append((t,pk(path.pos(t)))); ry.append((t,(0,path.yaw(t),0))); rr.append((t,(-math.degrees(math.atan2(f[1],max(h,1e-6))),0,clamp(path.roll(t)*0.8,-80,80))))
    A.add(out,'position',[(0,pos[0][1])]+pos); A.add(out,'rotation',[(0,ry[0][1])]+ry); A.add(root,'rotation',[(0,rr[0][1])]+rr); vis(A,out,[(a-0.05,b+0.05) for a,b in spans])
    for g in sp.extra: A.add(g,'scale',[(0,(1,1,1))])
    return out

# ---------------- 샷 ----------------
def fp(name,key,t0,t1,path,sky,chunk=6.0,fov=66):
    """조종석 1인칭: 1초 12장, 카메라 키를 장마다 넣음(직선 보간). 6초씩 나눠 찍고 조립 때 한 줄기(run)로 이음"""
    run=len(RUNS); RUNS.append(dict(run=run,t0=t0,t1=t1,kind='fp',set=key)); a=t0; k=0
    while a<t1-1e-6:
        b=min(t1,a+chunk); n=max(2,round((b-a)*FPS)); keys=[]
        for i in range(n):
            t=a+i/FPS; p=path.pos(t); q=path.pos(t+0.42)
            keys.append({'u':i/(n-1),'pos':[round(v,2) for v in p],'tgt':[round(v,2) for v in q],'roll':round(path.roll(t),2),'fov':round(lerpk(path.fovs,t,fov),1)})
        D.sh(f'{name}{k}',key,a,b,keys,sky,fps=FPS,lin=True,run=run,kind='fp'); a=b; k+=1
def ext(name,key,t0,t1,path,sky,o0,o1,lead=0.0,fov=46):
    """밖에서 보는 샷: 카메라 자리 = 기체 기준 (오른쪽, 위, 앞) o0 → o1, 기체(조금 앞 lead)를 봄. 24장"""
    run=len(RUNS); RUNS.append(dict(run=run,t0=t0,t1=t1,kind='ext',set=key)); n=round((t1-t0)*24); keys=[]
    for i in range(n):
        t=t0+i/24; u=i/(n-1); w=u*u*(3-2*u); o=[o0[j]+(o1[j]-o0[j])*w for j in range(3)]; f,r,up=path.frame(t); f=norm((f[0],0,f[2])); r=norm(cross(f,(0,1,0)))
        p=add(path.pos(t),add(mul(r,o[0]),add((0,o[1],0),mul(f,o[2])))); q=add(path.pos(t),mul(f,lead))
        keys.append({'u':u,'pos':[round(v,2) for v in p],'tgt':[round(v,2) for v in q],'fov':fov})
    D.sh(name,key,t0,t1,keys,sky,fps=24,lin=True,run=run,kind='ext')
def still(name,key,t0,t1,p0,q0,p1,q1,sky,fov=46,fps=24):
    run=len(RUNS); RUNS.append(dict(run=run,t0=t0,t1=t1,kind='ext',set=key)); n=round((t1-t0)*fps)
    keys=[{'u':i/(n-1),'pos':[p0[j]+(p1[j]-p0[j])*i/(n-1) for j in range(3)],'tgt':[q0[j]+(q1[j]-q0[j])*i/(n-1) for j in range(3)],'fov':fov} for i in range(n)]
    D.sh(name,key,t0,t1,keys,sky,fps=fps,lin=True,run=run,kind='ext')

DAWN=['#141c48','#5a3f86','#e8785a','#ffc27a']; DUSK=['#120c2a','#4a2260','#c8584a']; DARK=['#06060c','#06060c']

# =====================================================================
#  A : 격납고 → 발진 굴 (0~12)
# =====================================================================
def set_A():
    M,A,top=newset(); c=M.cube; T0=0
    def z(t): return 0 if t<5 else -2700*((t-5)/6.6)**2
    path=Path([(t,0,24,z(t)) for t in [0,2,4,5,5.5,6,6.5,7,7.5,8,8.5,9,9.5,10,10.5,11,11.6,12.2]],fovs=[(4.8,60),(7,74),(11,90),(11.6,100)])
    # 격납고 방 (z +120 ~ -160), 발진 굴 (z -160 ~ -2760)
    top+= [c('fl',[-170,-6,-160],[170,0,160],'hull_h'), c('ce',[-170,110,-160],[170,116,160],'e_dd'), c('wl',[-176,0,-160],[-170,110,160],'hull_h'), c('wr',[170,0,-160],[176,110,160],'hull_h'), c('wb',[-170,0,160],[170,110,166],'hull_h')]
    top+= [c('wf_l',[-170,0,-166],[-34,110,-160],'hull_h'), c('wf_r',[34,0,-166],[170,110,-160],'hull_h'), c('wf_t',[-34,62,-166],[34,110,-160],'hazard')]
    for x in (-110,-60,60,110):
        top+= [c('lamp',[x-14,107,-90],[x+14,109,-40],'glow_w'), c('lamp',[x-14,107,40],[x+14,109,90],'glow_w')]
    top+= [c('rail',[-22,0,-160],[-18,3,150],'hazard'), c('rail',[18,0,-160],[22,3,150],'hazard'), c('line',[-3,0,-160],[3,1.2,150],'glow_y')]
    for i,x in enumerate((-120,-75,75,120)):      # 옆에 선 다른 기체들
        s=fighter(M,f'pk{i}_','e_blue'); g=s.group(); o=M.group(f'pk{i}mv',[0,0,0],[g]); top.append(o); A.add(o,'position',[(0,pk((x,10,-60 if i%2 else 30)))]); A.add(o,'scale',[(0,(2.2,2.2,2.2))]); A.add(o,'rotation',[(0,(0,0,0))])
        for e in s.extra: A.add(e,'scale',[(0,(1,1,1))])
        top.append(c('pad',[x-22,0,(-60 if i%2 else 30)-26],[x+22,1.5,(-60 if i%2 else 30)+26],'hazard'))
    # 문 (3.2~4.8 열림)
    dl=M.group('door_l',[0,0,0],[c('dl',[-34,0,-158],[0,62,-152],'hazard')]); dr=M.group('door_r',[0,0,0],[c('dr',[0,0,-158.5],[34,62,-152.5],'hazard')]); top+= [dl,dr]
    A.add(dl,'position',[(0,(0,0,0)),(3.2,(0,0,0)),(4.8,pk((-36,0,0)))]); A.add(dr,'position',[(0,(0,0,0)),(3.2,(0,0,0)),(4.8,pk((36,0,0)))]); cue(0.6,'beep',0.7); cue(3.2,'door',1.0); cue(5.0,'launch',1.3); cue(2.2,'alarm',0.35)
    for k in range(13):        # 굴: 200 씩
        z0=-166-k*200; z1=z0-200
        top+= [c('tf',[-36,-6,z1],[36,0,z0],'hull_h'), c('tc',[-36,60,z1],[36,66,z0],'e_dd'), c('tl',[-42,0,z1],[-36,60,z0],'hull_e'), c('tr',[36,0,z1],[42,60,z0],'hull_e')]
        top+= [c('ts',[-35,26,z1+20],[-33.5,30,z0-20],'glow_c'), c('ts',[33.5,26,z1+20],[35,30,z0-20],'glow_c'), c('tk',[-3,0,z1],[3,1.2,z0],'glow_y')]
        for zz in (z0-60,z0-160): top+= [c('rib',[-36,57,zz-5],[36,59,zz+5],'glow_o'), c('rib',[-36,0,zz-4],[-33,60,zz+4],'e_or'), c('rib',[33,0,zz-4],[36,60,zz+4],'e_or')]
    top.append(c('out',[-60,-20,-2790],[60,90,-2780],'glow_w'))
    fp('발진',  'A',0,12,path,DARK)
    FLASH.append((11.5,12.3,'w')); cue(11.4,'whiteout',0.6)
    save(M,A,top,'격납고','A'); return path

# =====================================================================
#  B : 도시 (12~58) — 건물 사이를 누비며 적 드론·포탑과 싸움
# =====================================================================
def set_B():
    M,A,top=newset(); c=M.cube; T0=12; V=250; rng=random.Random(7); Z=lambda t: -V*(t-T0)
    W=[(11,0,330),(12,0,330),(14,20,330),(16.5,-60,300),(19,120,250),(21,60,200),(23.4,-140,240),(25.5,-220,300),(27.6,-80,210),(29.6,90,170),(31.5,200,230),(33.2,110,280),
       (35,-40,260),(37,-170,200),(39,-250,150),(41,-120,190),(42.8,40,260),(44.6,180,300),(46.4,240,220),(48.2,100,160),(50,-60,180),(52,-150,240),(54,-40,300),(56,0,360),(58,0,420),(60,0,460)]
    path=Path([(t,x,y,Z(t)) for t,x,y in W],fovs=[(12,84),(13.5,66)])
    px=lambda z: path.pos(T0-z/V)
    top+= [c('gr',[-2600,-8,-1000*(k+1)],[2600,0,-1000*k+400],'road') for k in range(0,13)]
    TW=['tw1','tw2','tw3','tw4']; n=0; roofs=[]
    for zr in range(-260,-11400,-235):
        for xc in range(-760,761,190):
            x=xc+rng.uniform(-30,30); z=zr+rng.uniform(-40,40); w=rng.uniform(90,150); d=rng.uniform(90,160); h=rng.choice([260,340,420,520,640,780,940])
            if any(abs(x-px(zz)[0])<w/2+42 and h>px(zz)[1]-40 for zz in (z-d/2-40,z,z+d/2+40)): continue
            tx=rng.choice(TW); top.append(c('tw',[x-w/2,-4,z-d/2],[x+w/2,h,z+d/2],'conc_d',north=tx,south=tx,east=tx,west=tx)); n+=1; roofs.append((x,h,z,w,d))
            r=rng.random()
            if r<0.22: top.append(c('ant',[x-3,h-2,z-3],[x+3,h+rng.choice([60,90,130]),z+3],'steel'))
            elif r<0.40: top.append(c('box',[x-w/4,h-2,z-d/4],[x+w/4,h+26,z+d/4],'conc'))
            elif r<0.50: top.append(c('bea',[x-8,h-2,z-8],[x+8,h+14,z+8],'a_m'))
    for side in (-1,1):       # 바깥 큰 건물 (멀리 벽처럼)
        for k in range(24):
            z=-200-k*480+rng.uniform(-60,60); x=side*(1100+rng.uniform(0,500)); w=rng.uniform(260,420); h=rng.uniform(700,1500); tx=rng.choice(TW)
            top.append(c('far',[x-w/2,-4,z-200],[x+w/2,h,z+200],'conc_d',north=tx,south=tx,east=tx,west=tx))
    # 하늘다리 (아래로 지나가거나 위로 넘음)
    for t,under in [(17.6,True),(22.2,False),(26.6,True),(30.6,True),(40,False),(43.6,True),(49,True),(53,False)]:
        p=path.pos(t); y0=p[1]+34 if under else p[1]-70
        top+= [c('br',[p[0]-230,y0,p[2]-16],[p[0]+230,y0+30,p[2]+16],'steel',north='hazard',south='hazard'), c('brl',[p[0]-230,y0+30,p[2]-3],[p[0]+230,y0+36,p[2]+3],'glow_o')]
        cue(t,'whoosh',0.8)
    # 요새 벽 (끝): 협곡 들머리
    ze=Z(58)-900
    top+= [c('fort',[-2600,-4,ze-300],[-150,1500,ze],'hull_a',south='hull_a2'), c('fort',[150,-4,ze-300],[2600,1500,ze],'hull_a',south='hull_a2'), c('fortb',[-150,-4,ze-300],[150,60,ze],'hull_a3'), c('glowin',[-150,60,ze-290],[150,1500,ze-280],'a_m')]
    for x in (-900,-450,450,900): top.append(c('spire',[x-40,1490,ze-200],[x+40,1900,ze-120],'a_p')); top.append(c('spl',[x-12,1890,ze-172],[x+12,1960,ze-148],'a_m'))
    # 적
    for tb,off in [(21.2,(0,6,0)),(24.6,(-16,10,0)),(28.3,(12,-4,0)),(31.8,(0,12,0)),(38.2,(-10,4,0)),(41.4,(14,8,0)),(45,(0,0,0)),(47.6,(-14,10,0)),(51,(10,2,0)),(54.4,(0,12,0)),(56.4,(-18,0,0))]:
        engage(M,A,top,path,tb,off)
    # 지붕 포탑 (쏘기만 함) · 머리 위를 스치는 적 편대
    for t in (19.5,26.2,36.6,46,52.6):
        p=path.pos(t+1.6); cand=sorted(roofs,key=lambda r: abs(r[2]-p[2])+abs(r[0]-p[0])*0.5)[0]; q=(cand[0],cand[1],cand[2])
        fo=Foe(M,A,top,turret(M,f'tr{int(t*10)}_',3.4),q); fo.done()
        for dt in (0,0.25,0.5): enemy_fire(M,A,top,path,q,t+dt,miss=(rng.choice([-18,18]),rng.uniform(6,14),0))
    for t in (15.2,33.6,48.8):
        for k in range(3):
            p0=add(path.pos(t+2.6),((k-1)*46,50+k*8,-200)); p1=add(path.pos(t+0.9),((k-1)*40,34,300))
            fo=Foe(M,A,top,drone(M,f'by{int(t*10)}{k}_',3.0),p0,yaw=0).fly([(t,p0),(t+1.3,p1)]); fo.t0=t-0.02; fo.t1=t+1.32; fo.done()
        cue(t+0.9,'whoosh',1.0)
    ex=[(34.2,36.8)]; player(M,A,top,path,ex)
    fp('도시a','B',12,34.2,path,DAWN); ext('밖_도시','B',34.2,36.8,path,DAWN,(26,10,-46),(-30,16,34),lead=6); fp('도시b','B',36.8,58,path,DAWN)
    caption(14.6,19.2,'저공 침투','Title'); FLASH.append((12.0,12.5,'w'))
    for fo in []: pass
    save(M,A,top,'도시','B'); print('  건물',n); return path

# =====================================================================
#  C : 협곡 (58~102) — 요새 벽 사이 좁은 골: 막대·틈·기둥·돌개·빛살·압착기·고리 → 굴 들머리
# =====================================================================
def set_C():
    M,A,top=newset(); c=M.cube; T0=58; V=260; rng=random.Random(9); Z=lambda t: -V*(t-T0); HW=150; HT=420
    W=[(57,0,560),(58,0,520),(59.6,0,330),(61,0,230),(63,-40,250),(64.3,-10,170),(65.5,30,62),(66.8,10,110),(68,0,150),(69.5,60,120),(71,-85,110),(72.2,85,130),(73.4,-75,100),(74.8,0,160),
       (76.5,-88,200),(78,-20,190),(79.5,40,182),(81,10,150),(82.5,0,120),(84,-30,100),(85.5,-100,42),(86.8,-40,120),(88,30,215),(89.5,20,130),(91,0,52),(92.6,0,120),(94,-30,262),(95.2,20,62),(96.4,0,140),
       (97.5,0,200),(98.1,0,190),(98.7,0,176),(100,0,130),(101.2,0,110),(102,0,110),(103.5,0,110)]
    path=Path([(t,x,y,Z(t)) for t,x,y in W],rolls=[(67.25,0),(67.75,88),(68.3,88),(68.9,0),(90.5,0),(90.9,0),(97.2,0),(98.9,360),(99,360)],fovs=[(58,70),(100,70),(101.8,84)])
    zend=Z(101.75)
    top+= [c('fl',[-HW-10,-8,-1000*(k+1)],[HW+10,0,-1000*k+600],'hull_a2') for k in range(0,12)]
    for k in range(-2,29):
        z0=-k*400; z1=z0-400
        if z1<zend-10: continue
        for sd in (-1,1):
            xa,xb=(sd*HW,sd*(HW+60)) if sd>0 else (sd*(HW+60),sd*HW); tx=rng.choice(['hull_a','hull_a2','hull_a3'])
            top.append(c('wall',[xa,-4,z1],[xb,HT+rng.choice([0,0,30,60]),z0],'a_k',west=tx,east=tx))
            for j in range(2):
                zz=z0-rng.uniform(40,360); yy=rng.uniform(30,HT-70); dp=rng.uniform(8,24); hh=rng.uniform(30,90); ww=rng.uniform(30,90)
                top.append(c('gb',[sd*HW-dp if sd>0 else sd*HW-2,yy,zz-ww/2],[sd*HW+2 if sd>0 else sd*HW+dp,yy+hh,zz+ww/2],rng.choice(['a_p','hull_a3','a_k'])))
            top.append(c('ls',[sd*HW-3 if sd>0 else sd*HW-1.2,HT-40,z1+30],[sd*HW+1.2 if sd>0 else sd*HW+3,HT-32,z0-30],'a_m'))
            if k%2==0: top.append(c('top',[sd*(HW+60) if sd>0 else -2600,HT-60,z1-400],[2600 if sd>0 else sd*(HW+60),HT-6+ (0 if k%4 else 12),z0],'hull_a'))
        if rng.random()<0.6: zz=z0-rng.uniform(60,340); x=rng.uniform(-110,110); top.append(c('fbx',[x-18,-2,zz-18],[x+18,rng.uniform(8,22),zz+18],'a_p'))
    def bar(t,y0,y1,col='hull_a3'):
        z=Z(t); top.append(c('bar',[-HW-4,y0,z-22],[HW+4,y1,z+22],'a_k',south=col,north=col)); top.append(c('barl',[-HW,y1-2 if y0<10 else y0-6,z+22],[HW,y1+4 if y0<10 else y0+2,z+25],'a_m')); cue(t,'whoosh',0.9)
    bar(63,-4,150); bar(65.5,130,HT+20); bar(94,-4,190); bar(95.2,120,HT+20)
    # 세로 틈 (68): 폭 46 — 옆으로 서서 빠져나감
    z=Z(68); top+= [c('sl',[-HW-4,-4,z-30],[-23,HT+30,z+30],'a_k',south='hull_a3'), c('sr',[23,-4,z-30],[HW+4,HT+30,z+30],'a_k',south='hull_a3'), c('se',[-26,-4,z+30],[-23,HT+30,z+33],'a_m'), c('se',[23,-4,z+30],[26,HT+30,z+33],'a_m')]; cue(68,'whoosh',1.2)
    # 가로 틈 (91): 높이 22~84
    z=Z(91); top+= [c('hl',[-HW-4,84,z-30],[HW+4,HT+30,z+30],'a_k',south='hull_a3'), c('hb',[-HW-4,-4,z-30],[HW+4,22,z+30],'a_k',south='hull_a3'), c('he',[-HW,84,z+30],[HW,87,z+33],'a_m')]; cue(91,'whoosh',1.2)
    # 기둥 사이 (71~73.4)
    for t,x in [(71,10),(72.2,-15),(73.4,20),(71.6,120),(72.8,-120)]:
        z=Z(t); top+= [c('py',[x-34,-4,z-34],[x+34,HT+60,z+34],'a_k',south='hull_a',east='hull_a2',west='hull_a2'), c('pyl',[x-36,200,z-36],[x+36,212,z+36],'a_m')]
    for t in (71,72.2,73.4): cue(t,'whoosh',0.8)
    # 돌개 (76.5): 큰 막대가 돎 — 지나는 순간 막대는 세로
    def fan(t,cy,w=140):
        z=Z(t); g=M.group(f'fan{int(t)}',[0,cy,z],[c('blade',[-17,cy-235,z-12],[17,cy+235,z+12],'steel',south='hazard',north='hazard'), c('hub',[-30,cy-30,z-18],[30,cy+30,z+18],'a_p')]); top.append(g)
        A.add(g,'rotation',[(0,(0,0,-w*t)),(L,(0,0,w*(L-t)))]); top.append(c('axle',[-HW-4,cy-12,z-8],[HW+4,cy+12,z+8],'a_k')); cue(t,'whoosh',1.2)
    fan(76.5,235)
    # 빛살 창살 (79.5): 틈 y 150~214
    z=Z(79.5)
    for y in [18,56,94,132,232,270,308,346,384]: top.append(c('lz',[-HW,y-3,z-3],[HW,y+3,z+3],'a_m'))
    top+= [c('lzp',[-HW-2,-4,z-10],[-HW+12,HT,z+10],'a_p'), c('lzp',[HW-12,-4,z-10],[HW+2,HT,z+10],'a_p')]; cue(79.5,'zap',1.0)
    # 압착기 (82.5): 양쪽 벽이 닫힘
    z=Z(82.5)
    for sd in (-1,1):
        g=M.group(f'cr{sd}',[0,0,0],[c('crs',[sd*HW-(0 if sd<0 else 150),-4,z-40],[sd*HW+(150 if sd<0 else 0),HT-40,z+40],'a_k',south='hazard',east='hull_a3',west='hull_a3')]); top.append(g)
        A.add(g,'position',[(0,pk((sd*150,0,0))),(80.2,pk((sd*150,0,0))),(82.5,pk((sd*-108,0,0))),(82.9,pk((sd*-150,0,0)))])
    cue(81,'door',1.2); cue(82.6,'clang',1.2)
    # 쓰러진 탑 (85.5): 계단처럼 쌓인 덩어리, 왼쪽 아래만 뚫림
    z=Z(85.5)
    for i,x0 in enumerate([-40,-90,-150,-150,-150]): top.append(c('ft',[x0-(4 if x0==-150 else 0),78+i*70-4,z-36+i*3],[HW+4,78+(i+1)*70,z+36-i*3],'conc_d',south='tw2',north='tw2'))
    top.append(c('ft0',[-30,-4,z-36],[HW+4,78,z+36],'conc_d',south='tw2')); cue(85.5,'whoosh',1.1)
    # 고리 셋 (97.5~98.7): 통돌이로 지나감
    for t,hs in [(97.5,74),(98.1,62),(98.7,52)]:
        p=path.pos(t); z=p[2]; cy=p[1]
        top+= [c('rg',[-hs-22,cy-hs-22,z-10],[hs+22,cy-hs,z+10],'a_p'), c('rg',[-hs-22,cy+hs,z-10.5],[hs+22,cy+hs+22,z+10.5],'a_p'), c('rg',[-hs-22,cy-hs,z-11],[-hs,cy+hs,z+11],'a_p'), c('rg',[hs,cy-hs,z-11.5],[hs+22,cy+hs,z+11.5],'a_p')]
        top+= [c('rgl',[-hs-4,cy-hs-4,z+10.5],[hs+4,cy-hs,z+13],'a_m'), c('rgl',[-hs-4,cy+hs,z+11],[hs+4,cy+hs+4,z+13.5],'a_m')]; cue(t,'whoosh',0.7)
    # 끝 벽 + 굴 들머리 (x±62, y 58~162)
    top+= [c('ew',[-HW-60,-4,zend-60],[-62,HT+200,zend],'a_k',south='hull_a'), c('ew',[62,-4,zend-60],[HW+60,HT+200,zend],'a_k',south='hull_a'), c('ew',[-62,162,zend-60],[62,HT+200,zend],'a_k',south='hull_a'), c('ew',[-62,-4,zend-60],[62,58,zend],'a_k',south='hull_a')]
    top+= [c('em',[-66,54,zend],[66,58,zend+4],'a_m'), c('em',[-66,162,zend],[66,166,zend+4.5],'a_m'), c('em',[-66,58,zend],[-62,162,zend+5],'a_m'), c('em',[62,58,zend],[66,162,zend+5.5],'a_m')]
    top+= [c('ti',[-62,54,zend-900],[62,58,zend-60],'black'), c('ti',[-62,162,zend-900],[62,166,zend-60],'black'), c('ti',[-66,54,zend-900],[-62,166,zend-60],'black'), c('ti',[62,54,zend-900],[66,166,zend-60],'black'), c('ti',[-66,54,zend-904],[66,166,zend-900],'black')]
    # 적: 마주 오는 드론 · 바닥 포탑
    for tb,off in [(66.9,(0,8,0)),(74.9,(0,6,0)),(84.1,(10,10,0)),(92.7,(0,10,0)),(96.5,(-8,6,0))]: engage(M,A,top,path,tb,off)
    for tb,x in [(87.6,-70),(88.4,60),(89.2,-20)]:
        q=(x,0,Z(tb+0.8)); fo=Foe(M,A,top,turret(M,f'ct{int(tb*10)}_',3.2),q); fo.show(tb-9)
        enemy_fire(M,A,top,path,fo,tb-1.9,miss=(14,8,0)); enemy_fire(M,A,top,path,fo,tb-1.2,miss=(-14,10,0)); shoot(M,A,top,path,tb,add(q,(0,14,0)),n=2); fo.boom(tb,size=1.2); fo.done()
    player(M,A,top,path,[(58,60.8)])
    ext('밖_협곡','C',58,60.8,path,DUSK,(-40,34,-90),(34,12,-40),lead=20,fov=50); fp('협곡','C',60.8,102,path,DUSK)
    FLASH.append((101.75,102.4,'k'))
    save(M,A,top,'협곡','C'); return path

# =====================================================================
#  D : 터널 (102~148)
# =====================================================================
def set_D():
    M,A,top=newset(); c=M.cube; T0=102; V=220; rng=random.Random(13); Z=lambda t: -V*(t-T0); HW=58; HH=50
    # 굴 가운데 줄 (느리게 굽음) / 큰 방 두 곳: 방1 109.5~115 , 방2 132.5~139.5
    CL=[(101,0,110),(104,0,110),(109,40,110),(115,40,140),(120,-30,140),(124,-30,90),(128,20,90),(132,20,120),(140,-20,120),(144,0,110),(149,0,110)]
    cl=Path([(t,x,y,Z(t)) for t,x,y in CL]); CH=[(109.6,115.0),(132.6,139.6)]; inch=lambda t: any(a<=t<=b for a,b in CH)
    W=[(101,0,0),(102,0,0),(103.4,0,10),(104.6,-10,-26),(105.8,14,-12),(107.2,0,0),(108.4,-20,14),(109.6,0,0),(110.6,-90,40),(111.6,-40,90),(112.6,80,60),(113.6,110,-10),(114.4,40,-20),(115,0,0),
       (116.4,18,-14),(118,-26,6),(119.4,10,20),(120.4,0,0),(121.6,0,-10),(123,-20,10),(124.6,20,16),(126,0,-18),(127.4,-24,0),(129,26,0),(130.2,-28,6),(131.4,26,-4),(132.6,0,0),
       (133.6,70,60),(134.8,120,10),(136,20,-50),(137.2,-110,-10),(138.4,-70,70),(139.6,0,0),(141,14,-14),(142.4,-10,10),(144,0,0),(145.4,0,0),(146.6,0,6),(148,0,0),(149.5,0,0)]
    path=Path([(t,cl.pos(t)[0]+x,cl.pos(t)[1]+y,Z(t)) for t,x,y in W],rolls=[(143.4,0),(143.9,88),(144.3,88),(144.8,0)],fovs=[(102,84),(103.5,70),(146,70),(148,82)])
    z=0; k=0; zend=Z(148.4)
    while z>zend:
        t=T0-z/V; z1=z-110
        if inch(t) or inch(T0-z1/V): z=z1; k+=1; continue
        cx,cy,_=cl.pos(T0-(z-55)/V); cx=round(cx/4)*4; cy=round(cy/4)*4; tx=['hull_a','hull_a2','hull_a3'][k%3]
        top+= [c('tf',[cx-HW-12,cy-HH-12,z1-1],[cx+HW+12,cy-HH,z+1],'a_k',up=tx), c('tc',[cx-HW-12,cy+HH,z1-1],[cx+HW+12,cy+HH+12,z+1],'a_k',down=tx), c('tl',[cx-HW-12,cy-HH,z1-1],[cx-HW,cy+HH,z+1],'a_k',east=tx,west=tx), c('tr',[cx+HW,cy-HH,z1-1],[cx+HW+12,cy+HH,z+1],'a_k',east=tx,west=tx)]
        col='a_m' if k%4==0 else ('glow_c' if k%4==2 else 'a_p')
        top+= [c('rb',[cx-HW-2,cy-HH-2,z-58],[cx-HW+5,cy+HH+2,z-50],col), c('rb',[cx+HW-5,cy-HH-2,z-58],[cx+HW+2,cy+HH+2,z-50],col), c('rb',[cx-HW,cy+HH-5,z-58.5],[cx+HW,cy+HH+2,z-49.5],col), c('rb',[cx-HW,cy-HH-2,z-58.5],[cx+HW,cy-HH+4,z-49.5],col)]
        top.append(c('cl',[cx-4,cy+HH-2.5,z1+8],[cx+4,cy+HH+1,z-8],'glow_w' if k%2 else 'glow_c'))
        z=z1; k+=1
    def room(a,b,hw,hh,tag):
        nonlocal top
        za=Z(a)+30; zb=Z(b)-30; cx,cy,_=cl.pos((a+b)/2); cx=round(cx); cy=round(cy)
        top+= [c('rf',[cx-hw,cy-hh-14,zb],[cx+hw,cy-hh,za],'a_k',up='hull_a2'), c('rc',[cx-hw,cy+hh,zb],[cx+hw,cy+hh+14,za],'a_k',down='hull_a'), c('rl',[cx-hw-14,cy-hh,zb],[cx-hw,cy+hh,za],'a_k',east='hull_a',west='hull_a'), c('rr',[cx+hw,cy-hh,zb],[cx+hw+14,cy+hh,za],'a_k',east='hull_a',west='hull_a')]
        for zz,e in ((za,cl.pos(a)),(zb,cl.pos(b))):      # 앞·뒤 벽 (굴 구멍만 뚫림)
            ex=round(e[0]/4)*4; ey=round(e[1]/4)*4; d=14 if zz==za else -14
            z0,z1=min(zz,zz+d),max(zz,zz+d)
            top+= [c('rw',[cx-hw,cy-hh,z0],[ex-HW,cy+hh,z1],'a_k',south='hull_a',north='hull_a'), c('rw',[ex+HW,cy-hh,z0],[cx+hw,cy+hh,z1],'a_k',south='hull_a',north='hull_a'), c('rw',[ex-HW,ey+HH,z0],[ex+HW,cy+hh,z1],'a_k',south='hull_a',north='hull_a'), c('rw',[ex-HW,cy-hh,z0],[ex+HW,ey-HH,z1],'a_k',south='hull_a',north='hull_a')]
            top+= [c('rwl',[ex-HW-5,ey-HH-5,z0-2],[ex+HW+5,ey-HH,z1+2],'a_m'), c('rwl',[ex-HW-5,ey+HH,z0-2.5],[ex+HW+5,ey+HH+5,z1+2.5],'a_m')]
        r=random.Random(int(a))
        for i in range(9):      # 기둥·빛 기둥
            x=cx+r.uniform(-hw+40,hw-40); zz=r.uniform(zb+120,za-120)
            if any(math.hypot(x-path.pos(T0-zq/V)[0],0)<46 for zq in (zz-30,zz,zz+30)): continue
            top+= [c('pl',[x-16,cy-hh,zz-16],[x+16,cy+hh,zz+16],'a_k',south='hull_a3',east='hull_a3',west='hull_a3',north='hull_a3'), c('plg',[x-18,cy-6,zz-18],[x+18,cy+6,zz+18],'a_m' if i%2 else 'glow_c')]
        for i in range(6): x=cx+(-1 if i%2 else 1)*(hw-3); zz=zb+ (za-zb)*(i+0.5)/6; top.append(c('rls',[x-2.5,cy-hh+20,zz-60],[x+2.5,cy-hh+34,zz+60],'a_m'))
        return cx,cy
    room(109.6,115.0,190,150,'r1'); room(132.6,139.6,210,150,'r2')
    cen=lambda t: (round(cl.pos(t)[0]/4)*4, round(cl.pos(t)[1]/4)*4)
    # 가로지르는 관 (104.6: 위쪽 → 낮게 / 105.8)
    cx,cy=cen(104.6); z=Z(104.6); top+= [c('pp',[cx-HW,cy-6,z-7],[cx+HW,cy+8,z+7],'rust'), c('pp',[cx-HW,cy+20,z-37],[cx+HW,cy+34,z-23],'steel')]; cue(104.6,'whoosh',0.8)
    cx,cy=cen(105.8); z=Z(105.8); top+= [c('pp',[cx-HW,cy-HH,z-7],[cx+HW,cy-30,z+7],'rust'), c('pp',[cx-HW,cy+14,z-7.5],[cx+HW,cy+HH,z+7.5],'a_p'), c('ppv',[cx-HW,cy-HH,z-8],[cx-8,cy+HH,z+8],'hull_a3')]; cue(105.8,'whoosh',0.8)
    # 닫히는 문 (108.4): 위·아래 판 — 지나갈 때 틈 44
    def door(t,gap=44,dy=0,vert=True,t_open=2.6):
        cx,cy=cen(t); z=Z(t); p=path.pos(t); gx=p[0]-cx; gy=p[1]-cy
        if vert:
            a=M.group(f'dA{int(t*10)}',[0,0,0],[c('dA',[cx-HW,cy+HH,z-9],[cx+HW,cy+HH+2*HH,z+9],'a_k',south='hazard',north='hazard')]); b=M.group(f'dB{int(t*10)}',[0,0,0],[c('dB',[cx-HW,cy-HH-2*HH,z-9.5],[cx+HW,cy-HH,z+9.5],'a_k',south='hazard',north='hazard')])
            A.add(a,'position',[(0,(0,0,0)),(t-t_open,(0,0,0)),(t,(0,-(HH-gy-gap/2),0)),(t+0.3,(0,-(HH-gy-2),0))]); A.add(b,'position',[(0,(0,0,0)),(t-t_open,(0,0,0)),(t,(0,(HH+gy-gap/2),0)),(t+0.3,(0,(HH+gy-2),0))])
        else:
            a=M.group(f'dA{int(t*10)}',[0,0,0],[c('dA',[cx-HW-2*HW,cy-HH,z-9],[cx-HW,cy+HH,z+9],'a_k',south='hazard',north='hazard')]); b=M.group(f'dB{int(t*10)}',[0,0,0],[c('dB',[cx+HW,cy-HH,z-9.5],[cx+HW+2*HW,cy+HH,z+9.5],'a_k',south='hazard',north='hazard')])
            A.add(a,'position',[(0,(0,0,0)),(t-t_open,(0,0,0)),(t,pk((HW+gx-gap/2,0,0))),(t+0.3,pk((HW+gx-2,0,0)))]); A.add(b,'position',[(0,(0,0,0)),(t-t_open,(0,0,0)),(t,pk((-(HW-gx-gap/2),0,0))),(t+0.3,pk((-(HW-gx-2),0,0)))])
        top.extend([a,b]); cue(t-t_open,'door',1.0); cue(t+0.3,'clang',1.1); cue(t-t_open,'alarm',0.4)
    door(108.4); door(144.1,gap=40,vert=False,t_open=2.8); door(126,gap=40)
    # 돌개 (118)
    cx,cy=cen(118); z=Z(118); g=M.group('fanD',[cx,cy,z],[c('blade',[cx-11,cy-HH+1,z-6],[cx+11,cy+HH-1,z+6],'steel',south='hazard',north='hazard'), c('hub',[cx-15,cy-15,z-9],[cx+15,cy+15,z+9],'a_p')]); top.append(g)
    A.add(g,'rotation',[(0,(0,0,-170*118)),(L,(0,0,170*(L-118)))]); cue(118,'whoosh',1.1)
    # 막 (121.6, 141): 빛 창살이 굴을 막음 → 양쪽 발생기를 쏴서 끔
    def barrier(t):
        cx,cy=cen(t); z=Z(t); bars=[c('bz',[cx-HW,cy-HH+8+i*14-2,z-2],[cx+HW,cy-HH+8+i*14+2,z+2],'a_m') for i in range(7)]+[c('bz',[cx-HW+10+i*24-2,cy-HH,z-2.6],[cx-HW+10+i*24+2,cy+HH,z+2.6],'a_mc') for i in range(5)]
        g=M.group(f'bar{int(t)}',[cx,cy,z],bars); top.append(g); A.add(g,'scale',[(0,(1,1,1)),(t-0.72,(1,1,1)),(t-0.66,(1,0.02,1)),(t-0.62,(0,0,0))])
        for sd in (-1,1):
            q=(cx+sd*(HW-10),cy-HH+12,z+16); s=Ship(M,f'gen{int(t)}{sd}_',1.0); s.cube([-8,-12,-8],[8,6,8],'a_k'); s.cube([-5,6,-5],[5,14,5],'a_p'); s.glow('eye',[-3,14,-3],[3,20,3],'a_mc')
            fo=Foe(M,A,top,s,q); shoot(M,A,top,path,t-0.8+ (0.08 if sd>0 else 0),add(q,(0,6,0)),n=2); fo.boom(t-0.8+(0.08 if sd>0 else 0),power=40,dur=1.0,size=0.6); fo.done()
        cue(t-0.7,'zap',1.0)
    barrier(121.6); barrier(141.0)
    # 옆에서 튀어나오는 압착기 셋 (129~131.4)
    for i,t in enumerate((129,130.2,131.4)):
        cx,cy=cen(t); z=Z(t); sd=1 if i%2==0 else -1      # 길이 +x 로 피하면 왼쪽(-x)에서 나옴
        sd=-1 if path.pos(t)[0]-cx>0 else 1
        g=M.group(f'pc{i}',[0,0,0],[c('pcs',[cx+sd*HW-(0 if sd<0 else 0),cy-HH,z-16] if sd<0 else [cx+HW,cy-HH,z-16],[cx-HW,cy+HH,z+16] if sd<0 else [cx+HW+2*HW,cy+HH,z+16],'a_k',south='hazard',north='hazard')]) if False else None
        x0,x1=(cx-HW-70,cx-HW) if sd<0 else (cx+HW,cx+HW+70)
        g=M.group(f'pc{i}',[0,0,0],[c('pcs',[x0,cy-HH,z-16],[x1,cy+HH,z+16],'a_k',south='hazard',north='hazard',east='hull_a3',west='hull_a3')]); top.append(g)
        A.add(g,'position',[(0,(0,0,0)),(t-1.1,(0,0,0)),(t-0.25,pk((-sd*66,0,0))),(t+0.4,pk((-sd*66,0,0)))]); cue(t-0.3,'clang',0.9)
    # 적
    for tb,off in [(111.4,(0,10,0)),(112.9,(-10,0,0)),(116.6,(0,4,0)),(123.2,(0,2,0)),(134.4,(0,12,0)),(135.8,(14,-6,0)),(137.4,(-12,8,0)),(138.8,(0,0,0)),(146.4,(0,0,0))]:
        engage(M,A,top,path,tb,off,lead=0.8,fire_at=(2.2,1.4))
    # 끝: 밝은 빛 (핵 방)
    top.append(c('endglow',[-200,-90,zend-60],[200,310,zend-50],'a_mc'))
    player(M,A,top,path,[(127.2,128.6)])
    fp('터널a','D',102,148,path,DARK,fov=70)
    FLASH.append((102.0,102.5,'k')); FLASH.append((147.7,148.3,'m'))
    save(M,A,top,'터널','D'); return path

# =====================================================================
#  E : 핵 방 (148~172) — 방어 기둥 넷 → 핵 → 무너지는 굴로 탈출
# =====================================================================
def set_E():
    M,A,top=newset(); c=M.cube; rng=random.Random(21); CO=(0,300,-1100); R=900
    top+= [c('fl',[-R,-320,-2000],[R,-300,-200],'a_k',up='hull_a2'), c('ce',[-R,900,-2000],[R,920,-200],'a_k',down='hull_a'), c('wl',[-R-20,-300,-2000],[-R,900,-200],'a_k',east='hull_a',west='hull_a'), c('wr',[R,-300,-2000],[R+20,900,-200],'a_k',east='hull_a',west='hull_a')]
    for zz,d in ((-200,20),(-2000,-20)):
        z0,z1=min(zz,zz+d),max(zz,zz+d); top+= [c('w',[-R,-300,z0],[-70,900,z1],'a_k',south='hull_a',north='hull_a'), c('w',[70,-300,z0],[R,900,z1],'a_k',south='hull_a',north='hull_a'), c('w',[-70,360,z0],[70,900,z1],'a_k',south='hull_a',north='hull_a'), c('w',[-70,-300,z0],[70,240,z1],'a_k',south='hull_a',north='hull_a')]
        top+= [c('wm',[-76,234,z0-3],[76,240,z1+3],'a_m'), c('wm',[-76,360,z0-3.5],[76,366,z1+3.5],'a_m')]
    top+= [c('in',[-70,228,-200],[70,240,200],'a_k',up='hull_a2'), c('in',[-70,360,-200],[70,372,200],'a_k',down='hull_a2'), c('in',[-82,240,-200],[-70,360,200],'a_k',east='hull_a3',west='hull_a3'), c('in',[70,240,-200],[82,360,200],'a_k',east='hull_a3',west='hull_a3')]
    # 핵: 가운데 빛 덩어리 + 둘레 껍질 조각 (블록 분해)
    core=Ship(M,'core_',1.0)
    for ix in (-1,0,1):
        for iy in (-1,0,1):
            for iz in (-1,0,1):
                if (ix,iy,iz)==(0,0,0): continue
                s=44 if abs(ix)+abs(iy)+abs(iz)==1 else (34 if abs(ix)+abs(iy)+abs(iz)==2 else 26); p=(ix*96,iy*96,iz*96)
                core.cube([p[0]-s,p[1]-s,p[2]-s],[p[0]+s,p[1]+s,p[2]+s],'hull_a3' if (ix+iy+iz)%2 else 'a_p')
    for k in range(10): a=rng.uniform(0,6.28); b=rng.uniform(-1,1); core.cube([math.cos(a)*150-12,b*140-12,math.sin(a)*150-12],[math.cos(a)*150+12,b*140+12,math.sin(a)*150+12],'a_m')
    core.cube([-52,-52,-52],[52,52,52],'a_m'); core.glow('heart',[-40,-40,-40],[40,40,40],'glow_w')
    cf=Foe(M,A,top,core,CO); A.add(cf.root,'rotation',[(0,(0,0,0)),(164,(0,164*14,0))])
    hrt=core.extra[0]; A.add(hrt,'scale',[(0,(1,1,1))]+[(148+i*0.4,((1.0 if i%2 else 1.5),)*3) for i in range(40)]+[(164.0,(2.4,2.4,2.4)),(164.05,(0,0,0))],'linear')
    # 방어 기둥 넷 + 핵으로 가는 빛줄
    PY=[(520,-300,-760),(-470,-300,-1500),(480,-300,-1560),(-540,-300,-700)]; pyf=[]
    for i,(x,y,z) in enumerate(PY):
        s=Ship(M,f'py{i}_',1.0)
        for j in range(6): s.cube([-40+j*3,j*100,-40+j*3],[40-j*3,(j+1)*100,40-j*3],'a_k' if j%2 else 'hull_a3')
        s.cube([-30,600,-30],[30,660,30],'a_m'); s.glow('eye',[-16,660,-16],[16,700,16],'a_mc')
        fo=Foe(M,A,top,s,(x,y,z)); pyf.append(fo)
        tip=(x,y+640,z); d=sub(CO,tip); n=math.sqrt(sum(v*v for v in d)); h=math.hypot(d[0],d[2])
        inner=M.group(f'lk{i}i',[0,0,0],[c('link',[-4,-4,-n],[4,4,0],'a_mc')]); o=M.group(f'lk{i}',[0,0,0],[inner]); top.append(o)
        A.add(inner,'rotation',[(0,(-math.degrees(math.atan2(d[1],max(h,1e-6))),0,0))]); A.add(o,'rotation',[(0,(0,math.degrees(math.atan2(d[0],-d[2])),0))]); A.add(o,'position',[(0,pk(tip))]); fo.link=o
    for k in range(14):
        x=rng.uniform(-R+60,R-60); z=rng.uniform(-1900,-300)
        if math.hypot(x-CO[0],z-CO[2])<330: continue
        hh=rng.uniform(60,220); top.append(c('st',[x-30,-304,z-30],[x+30,-300+hh,z+30],'a_k',south='hull_a3',north='hull_a3',east='hull_a3',west='hull_a3')); top.append(c('stl',[x-8,-300+hh,z-8],[x+8,-292+hh,z+8],'a_m'))
    # 길: 들어옴 → 오른쪽으로 크게 돌며 기둥 넷 → 정면에서 핵 → 스쳐 지나 뒤쪽 굴로
    path=Path([(147,0,300,200),(148,0,300,0),(149.4,0,300,-330),(150.8,330,340,-640),(152.4,640,420,-1040),(154,560,470,-1500),(155.6,160,430,-1820),(157.2,-330,380,-1700),(158.8,-640,330,-1300),
               (160.2,-640,300,-880),(161.4,-420,300,-520),(162.6,-170,330,-520),(163.3,-60,400,-760),(164.1,0,500,-1100),(165,0,420,-1500),(165.8,0,320,-1800),(166.6,0,300,-2040),(168,0,300,-2600),(170,0,300,-3460),(171.6,0,300,-4200),(173,0,300,-4900)],
              fovs=[(148,82),(149.5,68),(164,68),(166.6,84),(171.6,96)])
    hits=[(152.0,0),(154.9,2),(157.0,1),(160.0,3)]
    for tb,i in hits:
        fo=pyf[i]; q=add(PY[i],(0,640,0)); enemy_fire(M,A,top,path,q,tb-1.6,miss=(14,8,0)); enemy_fire(M,A,top,path,q,tb-1.0,miss=(-16,6,0))
        shoot(M,A,top,path,tb,q); fo.boom(tb,power=160,dur=2.0,size=2.2,cuek='boom'); A.add(fo.link,'scale',[(0,(1,1,1)),(tb,(1,1,1)),(tb+0.05,(0,0,0))])
    for fo in pyf: fo.t1=L; fo.done()
    for th in (162.7,163.0,163.3,163.6): shoot(M,A,top,path,th,add(CO,(rng.uniform(-30,30),rng.uniform(-30,30),0)),n=2)
    cue(163.7,'charge',0.0); cf.t1=L
    explode(A,core,164.0,power=520,dur=4.0,seed=5,delay=0.5,keep_scale=0.5,spin=220); cue(164.0,'bigboom',1.5); HIT.append((164.0,3.0)); cf.done()
    for k in range(10): burst(M,A,top,164.0+k*0.22,add(CO,(rng.uniform(-200,200),rng.uniform(-200,200),rng.uniform(-200,200))),n=8,speed=260,size=26,dur=1.8,cols=('a_m','a_mc','glow_w','fire1'),seed=k)
    FLASH.append((163.95,164.7,'w'))
    # 탈출 굴 (z -2020 ~ -4300): 불길·떨어지는 덩어리
    for k in range(21):
        z0=-2020-k*110; z1=z0-110; tx=['hull_a','hull_a2','hull_a3'][k%3]
        top+= [c('tf',[-82,228,z1-1],[82,240,z0+1],'a_k',up=tx), c('tc',[-82,360,z1-1],[82,372,z0+1],'a_k',down=tx), c('tl',[-82,240,z1-1],[-70,360,z0+1],'a_k',east=tx,west=tx), c('tr',[70,240,z1-1],[82,360,z0+1],'a_k',east=tx,west=tx)]
        top+= [c('rb',[-72,238,z0-58],[-65,362,z0-50],'glow_r' if k%2 else 'a_m'), c('rb',[65,238,z0-58],[72,362,z0-50],'glow_r' if k%2 else 'a_m'), c('rb',[-70,355,z0-58.5],[70,362,z0-49.5],'glow_r' if k%2 else 'a_m')]
        tt=166.6+ (k*110)/((4200-2040)/5.0)
        if k%2==0: burst(M,A,top,tt-0.55,(rng.choice([-55,55]),rng.uniform(250,350),z1),n=6,speed=70,size=9,dur=0.9,seed=k); cue(tt-0.55,'boom',0.6); HIT.append((round(tt-0.5,2),0.9))
        if k%3==1:      # 천장에서 떨어지는 덩어리
            x=rng.uniform(-50,50); g=M.group(f'fall{k}',[0,0,0],[c('fa',[x-12,362,z1-12],[x+12,386,z1+12],'a_p')]); top.append(g)
            A.add(g,'position',[(0,(0,0,0)),(tt-1.2,(0,0,0)),(tt+0.1,(0,-150,0))]); A.add(g,'rotation',[(tt-1.2,(0,0,0)),(tt+0.1,(40,0,25))])
    top.append(c('out',[-200,100,-4380],[200,500,-4370],'glow_w'))
    cue(165.6,'alarm',0.5); cue(168.5,'rumble',1.2); cue(171.3,'whiteout',0.8)
    fp('핵','E',148,172,path,DARK,fov=68)
    FLASH.append((171.5,172.4,'w'))
    save(M,A,top,'핵','E'); return path

# =====================================================================
#  F : 새벽 (172~180) — 요새에서 빠져나와 해 쪽으로
# =====================================================================
def set_F():
    M,A,top=newset(); c=M.cube; rng=random.Random(31)
    top+= [c('gr',[-3000,-8,-1000*(k+1)],[3000,0,-1000*k+1400],'road') for k in range(0,6)]
    fort=Ship(M,'ft_',1.0)
    for ix in range(-6,6):
        for iy in range(5):
            if ix in (-1,0) and iy==1: continue
            fort.cube([ix*260,iy*240,900],[ix*260+260,iy*240+240,1200],'hull_a' if (ix+iy)%2 else 'hull_a2')
    for x in (-900,-300,300,900): fort.cube([x-40,1200,960],[x+40,1650,1040],'a_p')
    fr=fort.group(); top.append(fr); explode(A,fort,173.2,center=(0,300,1050),power=900,dur=6.5,seed=2,delay=2.2,keep_scale=0.6,spin=120)
    top.append(c('hole',[-262,238,1195],[2,482,1210],'fire1'))
    for k in range(16): burst(M,A,top,172.6+k*0.3,(rng.uniform(-900,900),rng.uniform(100,1000),890),n=7,speed=260,size=34,dur=1.6,seed=k,bias=(0,0.3,-1.2));
    for t in (173.2,174.4,175.8): cue(t,'bigboom',1.2)
    TW=['tw1','tw2','tw3','tw4']
    for zr in range(300,-5200,-330):
        for xc in range(-1500,1501,300):
            if abs(xc)<200: continue
            x=xc+rng.uniform(-60,60); z=zr+rng.uniform(-60,60); w=rng.uniform(110,190); h=rng.choice([200,280,360,460,600]); tx=rng.choice(TW)
            top.append(c('tw',[x-w/2,-4,z-w/2],[x+w/2,h,z+w/2],'conc_d',north=tx,south=tx,east=tx,west=tx))
    top+= [c('sun',[-360,300,-9000],[360,1020,-8980],'sun'), c('sunc',[-250,410,-8975],[250,910,-8965],'glow_w'), c('sunh',[-1400,640,-8990],[1400,700,-8984],'glow_y')]
    path=Path([(171,-130,360,1500),(172,-130,360,1100),(173.5,-90,420,500),(175,0,520,-160),(176.5,60,600,-820),(178,40,680,-1500),(180,0,760,-2400),(181,0,800,-2850)])
    player(M,A,top,path,[(172,180)])
    still('탈출','F',172,176.4,(60,330,-420),(-110,400,700),(150,470,-330),(0,520,-160),DAWN,fov=50)
    ext('해돋이','F',176.4,180,path,DAWN,(14,8,54),(0,16,90),lead=-200,fov=52)
    caption(176.8,180,'임무 완료','End'); FLASH.append((172.0,172.5,'w'))
    save(M,A,top,'새벽','F'); return path

# =====================================================================
#  K : 조종석 틀 (초록 바탕에 한 장 찍어 조립 때 덧씌움)
# =====================================================================
def set_K():
    M,A,top=newset(); c=M.cube
    # 눈 = (0,0,0), 앞 = -z.  계기판·기수·창틀·포신
    top+= [c('nose',[-9,-13,-64],[9,-9.5,-22],'e_w'), c('nose2',[-5,-12,-84],[5,-9.8,-64],'e_or'), c('nose3',[-2,-11.6,-96],[2,-10.2,-84],'e_g')]
    top+= [c('dash',[-34,-22,-24],[34,-10.4,-17],'e_dd',south='dash'), c('dasht',[-34,-10.8,-27],[34,-9.8,-17],'e_d'), c('scr',[-8,-17.5,-17],[8,-11.5,-16.4],'scr1'), c('scl',[-24,-17.5,-17.2],[-11,-12,-16.5],'scr2'), c('scrr',[11,-17.5,-17.2],[24,-12,-16.5],'scr2')]
    top+= [c('pl',[-37,-22,-27],[-33,-7,-10],'e_d'), c('pr',[33,-22,-27],[37,-7,-10],'e_d')]
    for sd in (-1,1):       # 창틀: 아래에서 위로 안쪽으로 기우는 계단 기둥
        for i in range(7):
            x=sd*(36-i*2.6); top.append(c('fr',[min(x,x+sd*3),-8+i*5.2,-27-i*0.8],[max(x,x+sd*3),-2.6+i*5.2,-24-i*0.8],'e_g' if i%2 else 'e_d'))
        top.append(c('gun',[sd*17-2,-14.5,-58],[sd*17+2,-12,-24],'e_d')); top.append(c('gunt',[sd*17-1.2,-14,-63],[sd*17+1.2,-12.5,-58],'e_or'))
        top.append(c('wing',[sd*20,-14,-40],[sd*46,-12.6,-23],'e_w')); top.append(c('wingt',[sd*40,-14.4,-42],[sd*46,-11.6,-23],'e_or'))
    top+= [c('arch',[-19,28.2,-33],[19,31,-30],'e_g'), c('archl',[-2,26,-33.5],[2,28.4,-30.5],'glow_o')]
    top+= [c('stick',[-1,-22,-14],[1,-13,-12.4],'e_dd'), c('grip',[-1.6,-14,-14.6],[1.6,-11.4,-12],'e_or')]
    D.sh('조종석','K',0,0.5,[{'u':0,'pos':[0,0,0],'tgt':[0,0,-100],'fov':66},{'u':1,'pos':[0,0,0],'tgt':[0,0,-100],'fov':66}],['#00ff00','#00ff00'],fps=2,lin=True,run=-1,kind='key')
    save(M,A,top,'조종석','K')

if __name__=='__main__':
    which=sys.argv[1] if len(sys.argv)>1 else 'all'
    P={}
    for k,fn in (('A',set_A),('B',set_B),('C',set_C),('D',set_D),('E',set_E),('F',set_F),('K',set_K)): P[k]=fn()
    json.dump({k:{'ropes':[]} for k in 'ABCDEFK'},open(f'{OUT}/세트정보.json','w'))
    shots=sorted([s for s in D.SHOTS if s['kind']!='key'],key=lambda s:s['t0'])+[s for s in D.SHOTS if s['kind']=='key']
    json.dump({'shots':shots},open(f'{OUT}/샷목록.json','w',encoding='utf-8'),ensure_ascii=False)
    # 조립용 시간표: 속도(계기), 쏜 때, 맞은 때(흔들림), 적 탄이 스친 때(경고), 번쩍임
    spd=[]
    for r in RUNS:
        if r['kind']!='fp': continue
        p=P[r['set']]; t=r['t0']
        while t<r['t1']: spd.append((round(t,2),round(p.speed(t)),round(p.pos(t)[1]),round(p.roll(t),1))); t+=0.25
    seen=set(); cues=[]
    for q in sorted(CUES,key=lambda q:q['t']):
        k=(round(q['t'],1),q['kind'])
        if k in seen: continue
        seen.add(k); cues.append(q)
    json.dump({'duration':L,'runs':RUNS,'cues':cues,'fire':sorted(FIRE),'hit':sorted(HIT),'warn':sorted(WARN),'flash':FLASH,'speed':spd,'captions':D.CAPS},open(f'{ROOT}/시간표.json','w',encoding='utf-8'),ensure_ascii=False,indent=0)
    print('샷',len(shots),'/ 장 수',sum(round((s['t1']-s['t0'])*s['fps']) for s in shots),'/ 효과음',len(cues))
