"""《마지막 방어선》(우주 전쟁, 5분, 대사 없음) 장면 모형 + 샷 목록 + 글자·효과음 시간표 → 연재/지구방위선/장면/…
   세트: O 궤도(지구·달·별·기지·함대·모함 — 0~200, 232~300) / I 모함 안(굴·핵 — 200~232).  시간은 직접 정한 초(콘티.txt)
   사용: python 우주_장면.py [O|I|all]"""
import sys, os, json, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 우주_부품 import *
import 장면도구 as D
from 장면도구 import cam, two, orbit, sh, vis, cyc, puff, flicker, caption
import 겹침면_검사
ROOT='/home/user/youtubeshot/연재/지구방위선'; OUT=f'{ROOT}/장면'; os.makedirs(OUT,exist_ok=True)
L=300.0; D.init(L); SKY=['#03040c','#03040c']; CUES=[]
def cue(t,kind,vol=1.0): CUES.append({'t':round(t,2),'kind':kind,'vol':vol})
MS=(0,200,2600); MAWZ=2600-455; STN=(-420,-40,150)
# 촬영이 느려지지 않게 궤도 세트를 시간대별 파일로 나눔: 그 시간대에 일어나는 폭발·탄·파편의 움직임만 넣음 (움직이는 묶음이 많을수록 한 장 찍는 시간이 길어짐)
WINS=dict(O1=(0,92),O2=(92,150),O3=(150,200),O4=(232,300)); WIN=[0,300]
_burst=burst; _explode=explode
def burst(M,A,box,t,*a,**k):
    if WIN[0]-3<=t<=WIN[1]: _burst(M,A,box,t,*a,**k)
def explode(A,ship,t0,**k):
    if t0<=WIN[1]: _explode(A,ship,t0,**k)

class Craft:
    """함선 하나의 움직임: 길(pts=[(t,x,y,z)…])을 따라 날고, 가는 쪽으로 머리를 돌리고(yaw), 오르내릴 때 기수를 들고(pitch), 돌 때 기울임(roll)"""
    ALL=[]
    def __init__(s,M,A,top,ship,x,y,z,yaw=180):
        s.M=M; s.A=A; s.ship=ship; s.root=ship.group(); s.fx=M.group(ship.tag+'fx',[0,0,0],[]); s.out=M.group(ship.tag+'mv',[0,0,0],[s.root,s.fx]); top.append(s.out)
        s.pts=[(0.0,x,y,z)]; s.yaw0=yaw; s.spans=None; s.dead=None; s.bank=True; Craft.ALL.append(s)
    def to(s,t,x,y,z): s.pts.append((float(t),x,y,z)); return s
    def path(s,pts):
        for p in pts: s.pts.append(tuple(float(v) for v in p))
        return s
    def hold(s,t): _,x,y,z=s.pts[-1]; s.pts.append((float(t),x,y,z)); return s
    def at(s,t):
        P=s.pts
        if t<=P[0][0]: return P[0][1:]
        for a,b in zip(P,P[1:]):
            if a[0]<=t<=b[0]:
                f=(t-a[0])/max(1e-6,b[0]-a[0]); return tuple(a[i]+(b[i]-a[i])*f for i in (1,2,3))
        return P[-1][1:]
    def show(s,spans): s.spans=spans; return s
    def boom(s,t,power=40,dur=1.6,seed=0,size=1.0,cuek='boom',**kw):
        """블록 분해 + 불덩이"""
        cue(t,cuek,min(1.5,0.6+size*0.3))
        if t>WIN[1]: return s                     # 이 시간대엔 아직 멀쩡함
        s.dead=t; M=s.M
        if t+dur+0.5<WIN[0]: s.gone=True; return s  # 이미 터져 사라짐 → 통째로 숨김
        explode(s.A,s.ship,t,power=power,dur=dur,seed=seed,**kw)
        burst(M,s.A,s.fx['children'],t,(0,0,0),n=int(8+size*3),speed=30+size*26,size=2.2+size*1.6,dur=1.0+size*0.25,seed=seed)
        g=M.group(f'{s.ship.tag}fb',[0,0,0],[M.cube('fb',[-1,-1,-1],[1,1,1],'fire3')]); s.fx['children'].append(g); k=6+size*5
        s.A.add(g,'scale',[(0,(0,0,0)),(t-0.02,(0,0,0)),(t,(k*0.3,)*3),(t+0.12,(k,)*3),(t+0.4,(0,0,0))]); s.A.add(g,'rotation',[(t,(0,0,0)),(t+0.4,(60,80,30))])
        return s
    def finish(s):
        P=s.pts; A=s.A; n=len(P); yaw=s.yaw0
        if getattr(s,'gone',False): vis(A,s.out,[]); return
        pk=[(t,(-x,y,z)) for t,x,y,z in P]
        # 방향: 길목 점마다 따로 계산하면 돌 때 덜덜 떨림(사용자 지적 2026-11-11) → 0.25초마다 '앞뒤 0.6초의 움직임'으로 방향을 재고, 1.25초 평균으로 고르게 한 뒤 촘촘한 직선 키로 넣음
        dt=0.25; ts=[P[0][0]+k*dt for k in range(int((P[-1][0]-P[0][0])/dt)+2)]; ys=[]; ps=[]
        for t in ts:
            a_=s.at(t-0.6); b_=s.at(t+0.6); dx=b_[0]-a_[0]; dy=b_[1]-a_[1]; dz=b_[2]-a_[2]; h=math.hypot(dx,dz)
            if h>1.5: yaw+= (math.degrees(math.atan2(dx,-dz))-yaw+180)%360-180
            ys.append(yaw); ps.append(max(-45,min(45,-math.degrees(math.atan2(dy,max(h,1e-6))))) if h>1.5 else 0)
        sm=lambda v: [sum(v[max(0,i-2):i+3])/len(v[max(0,i-2):i+3]) for i in range(len(v))]
        ys=sm(sm(ys)); ps=sm(sm(ps)); rate=[(ys[min(len(ys)-1,i+1)]-ys[max(0,i-1)])/(2*dt) for i in range(len(ys))]; rl=sm(sm([max(-35,min(35,r*0.22)) for r in rate]))
        A.add(s.out,'rotation',[(t,(0,ys[i],0)) for i,t in enumerate(ts)],'linear')
        if s.bank: A.add(s.root,'rotation',[(t,(ps[i],0,rl[i])) for i,t in enumerate(ts)],'linear')      # 큰 함선은 기울이지 않음(bank=False)
        A.add(s.out,'position',pk,'catmullrom')
        sp=s.spans if s.spans is not None else [(0,L)]
        if s.dead is not None: sp=[(a,min(b,s.dead+4)) for a,b in sp if a<s.dead+4]
        vis(A,s.out,sp)
        for g in s.ship.extra:
            if 'engine' in g['name']: cyc(A,g,'scale',0,min(L,s.dead or L),(1,1,1),(1,1,1.5),0.16,rest=(1,1,1),interp='linear') if s.dead is None else None
def bolt(M,A,top,t,p0,p1,col='glow_c',speed=1500,length=26,thick=1.0,cuek=None):
    """레이저 탄: p0 에서 p1 로 날아가는 가늘고 긴 빛"""
    if cuek: cue(t,cuek,0.5)
    if not (WIN[0]-3<=t<=WIN[1]): return t
    dx,dy,dz=(p1[i]-p0[i] for i in range(3)); dist=math.sqrt(dx*dx+dy*dy+dz*dz) or 1; dur=max(0.08,dist/speed); h=math.hypot(dx,dz)
    inner=M.group('b',[0,0,0],[M.cube('bolt',[-thick,-thick,-length/2],[thick,thick,length/2],col)]); o=M.group('bo',[0,0,0],[inner]); top.append(o)
    A.add(inner,'rotation',[(0,(-math.degrees(math.atan2(dy,max(h,1e-6))),0,0))]); A.add(o,'rotation',[(0,(0,math.degrees(math.atan2(dx,-dz)),0))])
    A.add(o,'position',[(0,(-p0[0],p0[1],p0[2])),(t,(-p0[0],p0[1],p0[2])),(t+dur,(-p1[0],p1[1],p1[2]))]); A.add(o,'scale',[(0,(0,0,0)),(max(0,t-0.02),(0,0,0)),(t,(1,1,1)),(t+dur,(1,1,1)),(t+dur+0.02,(0,0,0))])
    return t+dur
def volley(M,A,top,a,b,t0,n=3,gap=0.14,col='glow_c',cuek='laser',spread=10,seed=0,**kw):
    r=random.Random(seed+int(t0*10))
    for i in range(n):
        t=t0+i*gap; p0=a.at(t) if isinstance(a,Craft) else a; p1=b.at(t+0.25) if isinstance(b,Craft) else b
        bolt(M,A,top,t,p0,tuple(p1[k]+r.uniform(-spread,spread) for k in range(3)),col,cuek=cuek if i==0 else None,**kw)
def newset():
    M=BigModel(1024); space_palette(M); return M,Anim(L),[]
def save(M,A,top,name,key):
    for c in Craft.ALL: c.finish()
    Craft.ALL.clear(); D.finish_all(); A.bake([t for t in top if isinstance(t,dict)]); n=겹침면_검사.fix(M.els,top)
    def flat(g):       # 움직임이 없는 조각 묶음은 풀어서 상자만 남김 (묶음이 많으면 한 장 찍는 시간이 길어짐)
        out=[]
        for c in g['children']:
            if isinstance(c,dict):
                flat(c)
                if c['uuid'] not in A.tr and all(not isinstance(x,dict) for x in c['children']) and not any(abs(v)>1e-6 for v in c.get('rotation',[0,0,0])): out+=c['children']
                else: out.append(c)
            else: out.append(c)
        g['children']=out
    for t in top:
        if isinstance(t,dict): flat(t)
    M.save(f'{OUT}/{key}_{name}.bbmodel',top,[A.json()],name=key); print(key,name,len(M.els),'상자, 겹침 고침',n)

# =====================================================================
#  O : 궤도 — 고요 · 모함 도착 · 출격 · 전투 · 주포 · 돌입 / (232~) 모함 붕괴 · 새벽
# =====================================================================
def set_O(key='O1'):
    WIN[0],WIN[1]=WINS[key]; M,A,top=newset(); rng=random.Random(11)
    sh=lambda name,st,t0,t1,*a,**k: D.sh(name,key,t0,t1,*a,**k) if WIN[0]<=t0<WIN[1] else None
    top+= skybox(M)+planet_cap(M,'earth',(0,-9200,2600),8200,1300,step=40,seed=4)+globe(M,'moon',(4200,1500,6200),600,MOON,seed=3,spots=10)
    sun=M.group('sun',[-3000,0,8500],[M.cube('sun',[-3380,-380,8500],[-2620,380,8520],'sun'), M.cube('sun_c',[-3260,-260,8490],[-2740,260,8500],'glow_w'), M.cube('sun_h',[-3900,-50,8524],[-2100,50,8530],'glow_y'), M.cube('sun_v',[-3050,-800,8524],[-2950,800,8530],'glow_y')]); top.append(sun)
    A.add(sun,'position',[(0,(0,-6000,0)),(258,(0,-6000,0)),(268,(0,-2600,0)),(300,(0,-1300,0))])
    # --- 기지·함대 ---
    stn=Craft(M,A,top,station(M,'st_'),*STN,yaw=0); A.add(stn.root,'rotation',[(0,(0,0,0)),(L,(0,L*4,0))]) ; stn.finish=lambda: (A.add(stn.out,'position',[(0,(-STN[0],STN[1],STN[2]))]),None)[1]
    fl=Craft(M,A,top,flagship(M,'fl_'),-160,60,380); c1=Craft(M,A,top,cruiser(M,'c1_'),160,150,420); c2=Craft(M,A,top,cruiser(M,'c2_'),-520,120,520); fl.bank=c1.bank=c2.bank=False
    fl.path([(50,-160,60,380),(74,-150,170,560),(150,-150,170,600),(182,-150,180,640),(200,-120,200,1250),(232,-120,200,1380),(262,-140,180,1300),(300,-160,120,900)])
    c1.path([(52,160,150,420),(76,0,200,800),(160,0,200,820)]); c2.path([(54,-520,120,520),(78,330,200,720),(172,330,200,740)])
    # --- 모함: 깊은 우주에서 다가옴 (22~48) ---
    ms=Craft(M,A,top,mothership(M,'ms_'),0,900,8200,yaw=0); ms.bank=False; ms.show([(21,L)]); ms.path([(20,0,900,8200),(40,0,300,3500),(50,*MS),(L,*MS)]); ms.finish_orig=ms.finish
    cue(22,'rumble',1.2); cue(36,'rumble',1.4); cue(44,'horn',1.3)
    mg=[g for g in ms.ship.extra if 'mawglow' in g['name']][0]
    A.add(mg,'scale',[(0,(1,1,1)),(150,(1,1,1)),(159.6,(2.4,1.3,1)),(160,(1,1,1)),(164,(1,1,1)),(171.6,(2.4,1.3,1)),(172,(1,1,1))],'linear')
    for t0 in (150,164): burst(M,A,top,t0+7.5,(0,MS[1],MAWZ+40),n=10,speed=120,size=14,dur=2.0,cols=('a_m','a_mc','glow_w'),seed=int(t0)); cue(150,'charge',1.2); cue(164,'charge',1.2)
    # --- 주포 (160, 172): 아가리에서 뻗는 굵은 빛 ---
    def beam(t,target,tag):
        dx=target[0]-MS[0]; dz=target[2]-(MAWZ-10); Lb=math.hypot(dx,dz)+140
        g=M.group(tag,[0,MS[1],MAWZ-10],[M.cube('beam',[-16,MS[1]-34,MAWZ-10-Lb],[16,MS[1]+34,MAWZ-10],'a_m'), M.cube('beam_c',[-7,MS[1]-16,MAWZ-12-Lb],[7,MS[1]+16,MAWZ-8],'glow_w')]); top.append(g)
        A.add(g,'rotation',[(0,(0,math.degrees(math.atan2(dx,-dz)),0))]); A.add(g,'scale',[(0,(0,0,0)),(t-0.02,(0,0,0)),(t,(0.3,0.3,1)),(t+0.2,(1.4,1.4,1)),(t+1.5,(1,1,1)),(t+2.0,(0.1,0.1,1)),(t+2.05,(0,0,0))]); cue(t,'beam',1.4)
    beam(160,(0,200,820),'beam1'); c1.boom(160.9,power=260,dur=4.5,seed=3,size=6,cuek='bigboom',keep_scale=0.7,spin=200)
    beam(172,(330,200,740),'beam2'); c2.boom(172.9,power=260,dur=4.5,seed=4,size=6,cuek='bigboom',keep_scale=0.7,spin=200)
    # --- 전투기 8 (0 = 주인공, 주황 줄) · 요격기 12 ---
    F=[Craft(M,A,top,fighter(M,f'f{i}_','e_or' if i==0 else 'e_blue'),STN[0]+(i%4)*14-20,STN[1]-70,STN[2]+(i//4)*16) for i in range(8)]
    # 0~22: 둘이 순찰 (기지 둘레를 크게 돎)
    for i in (0,1):
        F[i].pts=[(0.0,-700+i*30,60+i*10,-200-i*30)]; F[i].path([(6,-300,90,-420),(12,150,70,-300),(18,200,40,60),(24,-80,20,330),(32,-380,30,420),(40,-560,10,260),(50,-470,-60,150+i*20),(52+i*1.6,STN[0],STN[1]-70,STN[2])])
    for i in range(2,8): F[i].show([(52,L)])
    for i in range(8):      # 출격 52~66 → 78 에 줄지어 섬
        t=52+i*1.6; F[i].path([(t,STN[0],STN[1]-70,STN[2]),(t+1.5,STN[0]+30,STN[1]-120,STN[2]+120),(78+i*0.2,-180+i*50+(0 if i<4 else -200),150+(i%3)*40,820+(i%2)*60)]); cue(t,'launch',0.7)
    cue(50,'alarm',0.8)
    I=[Craft(M,A,top,interceptor(M,f'i{i}_'),MS[0],MS[1],MAWZ+200,yaw=0).show([(76+i,L)]) for i in range(12)]
    for i,c in enumerate(I):
        t=76+i; c.path([(t,0,MS[1]+(i%5-2)*40,MAWZ+120),(t+1.2,(i%2*2-1)*60,MS[1]+(i%5-2)*60,MAWZ-160),(92+i*0.15,-420+i*76,120+(i%4)*70,1500+(i%3)*90)]); cue(t,'whoosh',0.5)
    # 전투 92~150: 구역 안을 누비는 길. 요격기 j 는 전투기 j%8 을 0.9초 뒤에서 쫓음
    def weave(c,t0,t1,seed,zone=(-520,520,40,420,900,1650),step=2.6):
        r=random.Random(seed); t=t0; x,y,z=c.pts[-1][1:]
        while t<t1:
            t=min(t1,t+step*r.uniform(0.8,1.2))
            for _ in range(20):
                nx,ny,nz=r.uniform(zone[0],zone[1]),r.uniform(zone[2],zone[3]),r.uniform(zone[4],zone[5])
                if 260<math.dist((x,y,z),(nx,ny,nz))<700: break
            x,y,z=nx,ny,nz; c.to(t,x,y,z)
    FK={5:107.0,6:119.0,7:128.0,4:141.0}; IK={0:98.0,3:104.0,6:109.0,1:116.0,9:123.0,4:131.0,10:138.0,7:146.0}
    for i,c in enumerate(F): weave(c,92,FK.get(i,150),100+i)
    for j,c in enumerate(I):
        tgt=F[j%8]; te=min(IK.get(j,150),FK.get(j%8,150)+0.5,150); t=92.9
        while t<te: p=tgt.at(t-0.9); c.to(t,p[0]+(j%3-1)*14,p[1]+8,p[2]); t+=0.65
        if j not in IK: weave(c,te,150,200+j)
    for j,t in IK.items():
        k=[f for f in range(8) if f not in FK or FK[f]>t+1][j%4]; volley(M,A,top,F[k],I[j],t-0.9,4,col='glow_c',seed=j); I[j].boom(t,power=46,dur=1.6,seed=j,size=1.2)
    for f,t in FK.items():
        j=[q for q in range(12) if q%8==f][0]; volley(M,A,top,I[j],F[f],t-0.9,4,col='a_m',cuek='laser2',seed=f); F[f].boom(t,power=50,dur=1.8,seed=f,size=1.3)
    for t in [94+k*1.7 for k in range(33)]:      # 여기저기 오가는 탄 (전투의 밀도)
        k=rng.randrange(12); f=rng.randrange(8)
        if (k in IK and IK[k]<t+1) or (f in FK and FK[f]<t+1): continue
        if rng.random()<0.5: volley(M,A,top,F[f],I[k],t,3,col='glow_c',spread=40,seed=k)
        else: volley(M,A,top,I[k],F[f],t,3,col='a_m',cuek='laser2',spread=40,seed=f)
    for t in [86+k*4.2 for k in range(15)]:      # 순양함·기함의 굵은 포
        s_=[fl,c1,c2][int(t)%3]; k=rng.randrange(12)
        if k in IK and IK[k]<t+1: k=11
        volley(M,A,top,s_,I[k] if rng.random()<0.6 else (rng.uniform(-300,300),rng.uniform(60,340),MAWZ),t,2,gap=0.25,col='glow_o',cuek='cannon',spread=60,thick=2.4,length=44,speed=1900,seed=int(t))
    # 150~185: 물러나 다시 모임 → 185~200 돌입 (0,1,2,3) · 남은 요격기 넷(2,5,8,11)이 막아섬
    for i in (0,1,2,3): F[i].path([(156,-260+i*40,120+i*20,1000),(166,-220+i*60,150,700),(182,-200+i*50,190,760)])
    for j in (2,5,8,11): I[j].path([(156,-200+j*40,MS[1]+(j%3-1)*80,1900),(184,-160+j*30,MS[1]+(j%3-1)*60,1850)])
    F[0].path([(188,-60,210,1250),(193,40,230,1650),(197,10,205,1950),(199.6,0,200,MAWZ+40),(200.4,0,200,MAWZ+260)]); F[0].show([(0,200.4),(232,L)])
    F[1].path([(188,-110,180,1240),(193,-30,190,1640),(197.5,-160,330,1900),(206,-520,420,1500),(232,-400,300,1200),(262,-240,200,1150),(300,-260,140,820)])
    F[2].path([(188,-10,250,1260),(193,90,260,1640),(195,100,240,1790)]); F[3].path([(188,-160,230,1230),(190,-120,236,1400)])
    I[2].path([(186,-150,236,1700),(190,-125,238,1460),(194,60,230,1500),(197,-40,190,1840)]); I[5].path([(186,80,250,1800),(191,60,250,1740),(195,95,242,1830),(199,160,300,1700),(232,300,380,1900)])
    I[8].path([(187,-40,200,1900),(192,-36,196,1700)]); I[11].path([(188,40,170,1960),(196.5,24,196,1990),(197,20,200,1960)])
    volley(M,A,top,I[2],F[3],189.2,4,col='a_m',cuek='laser2'); F[3].boom(190,power=50,dur=1.8,seed=13,size=1.3)
    volley(M,A,top,fl,I[8],191.2,3,gap=0.2,col='glow_o',cuek='cannon',thick=2.4,length=44,speed=1900); I[8].boom(192,power=46,seed=18,size=1.2)
    volley(M,A,top,I[5],F[2],194.2,4,col='a_m',cuek='laser2'); F[2].boom(195,power=50,dur=1.8,seed=12,size=1.3)
    volley(M,A,top,F[0],I[11],196.2,5,col='glow_c'); I[11].boom(197,power=46,seed=21,size=1.2); volley(M,A,top,fl,I[2],196.3,3,gap=0.2,col='glow_o',cuek='cannon',thick=2.4,length=44,speed=1900); I[2].boom(197.2,power=46,seed=22,size=1.2)
    for t in (184,187,190,193,196): volley(M,A,top,fl,(rng.uniform(-200,200),rng.uniform(100,300),MAWZ),t,2,gap=0.3,col='glow_o',cuek='cannon',thick=2.4,length=44,speed=1900,seed=int(t))
    # --- 232~: 주인공이 아가리에서 튀어나옴 → 모함이 안쪽부터 물결치듯 분해 ---
    F[0].path([(232,0,200,MAWZ+200),(234,0,200,MAWZ-200),(238,200,260,1500),(246,330,260,1150),(262,260,240,900),(280,-60,160,560),(292,-160,60,200),(300,-420,20,-300)]); cue(232.4,'whoosh',1.0)
    for k in range(5): burst(M,A,top,233+k*0.7,(0,MS[1]+(k%3-1)*80,MAWZ-20),n=12,speed=260+k*60,size=22+k*6,dur=1.8,seed=k,bias=(0,0,-1.6))
    cue(233,'boom',1.2)
    for g,c in ms.ship.pcs: pass
    explode(A,ms.ship,237.0,power=900,dur=9.0,seed=5,delay=6.0,keep_scale=0.55,spin=160)
    for k,t in enumerate((237,238.6,240.2,241.8,243.4,245)): cue(t,'bigboom',1.5-k*0.1)
    for k in range(9):       # 선체 곳곳의 불덩이
        t=237.3+k*0.8; x=rng.uniform(-700,700); y=MS[1]+rng.uniform(-250,250); z=MS[2]+rng.uniform(-400,300)
        burst(M,A,top,t,(x,y,z),n=10,speed=380,size=46,dur=2.2,seed=k+40)
    burst(M,A,top,245.0,(0,200,2600),n=22,speed=900,size=70,dur=3.2,cols=('glow_w','fire3','fire1','a_mc'),seed=99); cue(245,'whiteout',1.4)
    ms.dead=None
    # 기지 불빛·경보
    # ---------------- 샷 ----------------
    sh('지구','O',0,6,cam((0,[-900,-200,-900],[-300,-700,2000],{'fov':46}),(1,[-700,40,-700],[-380,-60,200],{'fov':40})),SKY)
    sh('기지','O',6,13,orbit((STN[0],STN[2]),330,60,-150,-60,(STN[0],STN[1],STN[2]),n=6,r1=260,h1=10),SKY)
    sh('순찰','O',13,22,cam((0,[26,10,-46],[0,2,0],{'fov':50,'roll':-6}),(0.5,[-30,14,-40],[0,2,0],{'fov':56,'roll':8}),(1,[20,6,-50],[0,2,30],{'fov':50,'roll':-4})),SKY,follow='f0_mv')
    sh('먼빛','O',22,28,cam((0,[-380,20,-150],[0,700,6000],{'fov':30}),(1,[-380,20,-150],[0,560,5000],{'fov':18})),SKY,shake=0.6)
    sh('다가옴','O',28,36,cam((0,[-700,-100,-200],[-200,200,2600],{'fov':44}),(1,[-640,-110,-260],[-150,260,2600],{'fov':52})),SKY,shake=1.2)
    sh('그림자','O',36,43,cam((0,[STN[0]+60,STN[1]-150,STN[2]-360],[STN[0]-20,STN[1]+60,STN[2]+400],{'fov':60}),(1,[STN[0]+90,STN[1]-170,STN[2]-400],[STN[0]+60,STN[1]+140,STN[2]+600],{'fov':66})),SKY,shake=1.5)
    sh('크기','O',43,50,cam((0,[560,760,3400],[-200,0,300],{'fov':60}),(1,[430,680,2500],[-240,0,300],{'fov':50})),SKY,shake=1)
    sh('경보','O',50,56,orbit((STN[0],STN[2]),300,-120,40,110,(STN[0],STN[1]-40,STN[2]),n=5,r1=240),SKY)
    sh('출격','O',56,66,cam((0,[STN[0]+90,STN[1]-150,STN[2]+10],[STN[0]+20,STN[1]-100,STN[2]+90],{'fov':56,'roll':6}),(1,[STN[0]+150,STN[1]-170,STN[2]-60],[STN[0]+60,STN[1]-40,STN[2]+500],{'fov':50,'roll':-4})),SKY,shake=0.8)
    sh('함대','O',66,74,cam((0,[-380,260,60],[-80,160,640],{'fov':50}),(1,[-520,230,300],[0,190,900],{'fov':44})),SKY)
    sh('함교뒤','O',74,82,cam((0,[0,60,-190],[0,40,0],{'fov':50}),(1,[30,70,-230],[0,60,400],{'fov':40})),SKY,follow='fl_mv')
    sh('쏟아짐','O',82,92,cam((0,[260,330,MAWZ-420],[0,200,MAWZ],{'fov':50}),(1,[420,380,MAWZ-760],[0,200,MAWZ-100],{'fov':60})),SKY,shake=1)
    sh('돌격','O',92,99,cam((0,[30,14,-56],[0,2,0],{'fov':60,'roll':8}),(1,[-34,10,-48],[0,2,0],{'fov':70,'roll':-10})),SKY,follow='f0_mv',shake=1.6)
    sh('난전','O',99,108,cam((0,[-620,330,820],[0,220,1300],{'fov':50}),(1,[-460,280,980],[60,220,1350],{'fov':44})),SKY,shake=0.8)
    sh('쫓김','O',108,116,cam((0,[20,10,-50],[0,0,10],{'fov':64,'roll':-12}),(0.5,[-24,16,-44],[0,0,10],{'fov':70,'roll':10}),(1,[10,6,-56],[0,0,10],{'fov':64,'roll':-6})),SKY,follow='f1_mv',shake=2)
    sh('포격','O',116,124,cam((0,[80,40,-150],[0,10,20],{'fov':50}),(1,[-90,60,-120],[0,10,200],{'fov':46})),SKY,follow='c1_mv',shake=1.4)
    sh('요격기','O',124,132,cam((0,[16,8,-40],[0,0,0],{'fov':60,'roll':10}),(1,[-20,10,-36],[0,0,0],{'fov':66,'roll':-10})),SKY,follow='i4_mv',shake=2)
    sh('위에서','O',132,142,[dict(k,fov=50,roll=(6 if i%2 else -6)) for i,k in enumerate(orbit((0,1280),620,300,-150,-40,(0,220,1280),n=6,r1=460,h1=250))],SKY,shake=0.8)
    sh('주인공','O',142,150,cam((0,[-24,8,-44],[0,2,0],{'fov':56,'roll':6}),(1,[26,12,-50],[0,2,0],{'fov':60,'roll':-8})),SKY,follow='f0_mv',shake=1.6)
    sh('충전','O',150,159.6,cam((0,[420,320,1000],[0,200,MAWZ],{'fov':46}),(1,[260,270,1250],[0,200,MAWZ],{'fov':38})),SKY,shake=1.5)
    sh('주포1','O',159.6,166,cam((0,[330,300,460],[0,200,900],{'fov':56}),(0.2,[320,290,480],[0,200,860],{'fov':60,'shake':1}),(1,[420,340,360],[0,200,820],{'fov':50,'shake':0.4})),SKY,shake=6)
    sh('잔해','O',166,171.6,cam((0,[-60,230,700],[0,200,820],{'fov':60,'roll':10}),(1,[-90,250,640],[0,200,830],{'fov':66,'roll':-6})),SKY,shake=1)
    sh('주포2','O',171.6,178,cam((0,[-200,300,300],[330,200,740],{'fov':50}),(0.22,[-190,296,320],[330,200,740],{'fov':56,'shake':1}),(1,[-300,330,200],[300,200,760],{'fov':46,'shake':0.3})),SKY,shake=6)
    sh('결심','O',178,186,cam((0,[60,70,-200],[0,40,0],{'fov':46}),(1,[-80,90,-240],[0,50,300],{'fov':40})),SKY,follow='fl_mv',shake=0.8)
    sh('돌입1','O',186,193,cam((0,[24,10,-50],[0,2,10],{'fov':66,'roll':8}),(1,[-20,8,-44],[0,2,20],{'fov':74,'roll':-10})),SKY,follow='f0_mv',shake=2.2)
    sh('엄호','O',193,197,cam((0,[-500,420,1300],[0,220,1800],{'fov':46}),(1,[-420,380,1450],[0,210,1900],{'fov':40})),SKY,shake=1.2)
    sh('아가리','O',197,200,cam((0,[0,8,-44],[0,2,30],{'fov':70}),(1,[0,6,-36],[0,2,30],{'fov':84})),SKY,follow='f0_mv',shake=2.6)
    sh('탈출','O',232,237,cam((0,[160,260,MAWZ-520],[0,200,MAWZ],{'fov':50}),(0.5,[150,250,MAWZ-600],[0,200,MAWZ-150],{'fov':56,'shake':1}),(1,[120,240,MAWZ-760],[-30,215,MAWZ-520],{'fov':50})),SKY,shake=3)
    sh('붕괴1','O',237,246,cam((0,[-1500,700,900],[0,200,2500],{'fov':50}),(1,[-1900,900,500],[0,200,2600],{'fov':56})),SKY,shake=3)
    sh('붕괴2','O',246,254,cam((0,[40,16,-70],[-200,-20,900],{'fov':60}),(1,[50,22,-80],[-260,-30,1300],{'fov':66})),SKY,follow='f0_mv',shake=2)
    sh('고요','O',254,266,cam((0,[1400,900,800],[0,200,2400],{'fov':50}),(1,[1700,1000,400],[-100,150,2300],{'fov':46})),SKY)
    sh('해돋이','O',266,280,cam((0,[500,120,-400],[-2300,-900,7000],{'fov':44}),(1,[440,60,-520],[-2500,-300,7000],{'fov':36})),SKY)
    sh('귀환','O',280,290,cam((0,[30,10,-60],[0,2,0],{'fov':50,'roll':4}),(1,[-40,16,-70],[0,2,0],{'fov':46,'roll':-3})),SKY,follow='f0_mv')
    sh('끝','O',290,300,cam((0,[-800,100,-700],[-300,0,600],{'fov':44}),(1,[-1100,260,-1100],[-200,60,1200],{'fov':40})),SKY)
    caption(2.5,6.5,'마지막 방어선','Title'); caption(292,299.5,'마지막 방어선','Title')
    save(M,A,top,'궤도','%s'%key)

# =====================================================================
#  I : 모함 안 (200~232) — 굴을 따라 핵까지
# =====================================================================
def set_I():
    WIN[0],WIN[1]=200,232; M,A,top=newset(); W=260; H=260; ZE=2600; rng=random.Random(3); tex=['hull_a','hull_a2','hull_a3']
    for i,z in enumerate(range(-780,ZE,260)):
        top+= [M.cube('tw',[W/2,-H/2,z],[W/2+40,H/2,z+260],tex[i%3]), M.cube('tw',[-W/2-40,-H/2,z],[-W/2,H/2,z+260],tex[(i+1)%3]), M.cube('tf',[-W/2,-H/2-40,z],[W/2,-H/2,z+260],tex[(i+2)%3]), M.cube('tc',[-W/2,H/2,z],[W/2,H/2+40,z+260],tex[i%3])]
        top+= [M.cube('rib',[W/2-10,-H/2,z],[W/2,H/2,z+14],'a_p'), M.cube('rib',[-W/2,-H/2,z],[-W/2+10,H/2,z+14],'a_p'), M.cube('ribt',[-W/2,H/2-10,z],[W/2,H/2,z+14],'a_p'), M.cube('ribb',[-W/2,-H/2,z],[W/2,-H/2+10,z+14],'a_p')]
        top+= [M.cube('strip',[W/2-3,-6,z+30],[W/2-0.5,6,z+230],'a_m'), M.cube('strip',[-W/2+0.5,-6,z+30],[-W/2+3,6,z+230],'a_m')]
    top.append(M.cube('tback',[-W/2,-H/2,-820],[W/2,H/2,-782],'maw'))
    OBS=[(400,-1,'v'),(640,1,'v'),(860,0,'h'),(1080,-1,'v'),(1280,1,'h'),(1480,1,'v'),(1680,-1,'h'),(1900,0,'v'),(2100,1,'v'),(2260,-1,'h')]
    for z,sd,kind in OBS:        # 장애물: 세로 기둥(왼·오른·가운데) / 가로 들보(위·아래·가운데)
        if kind=='v': top+= [M.cube('pil',[sd*70-34,-H/2,z-20],[sd*70+34,H/2,z+20],'hull_a3'), M.cube('pil_l',[sd*70-36,-8,z-22],[sd*70+36,8,z+22],'a_m')]
        else: top+= [M.cube('bar',[-W/2,sd*70-32,z-20],[W/2,sd*70+32,z+20],'hull_a3'), M.cube('bar_l',[-8,sd*70-34,z-22],[8,sd*70+34,z+22],'a_g')]
    # 닫히는 문 (z 2480): 위아래 두 짝
    for sy,nm in ((1,'gate_u'),(-1,'gate_d')):
        g=M.group(nm,[0,0,2480],[M.cube('gate',[-W/2,0 if sy>0 else -H/2,2470],[W/2,H/2 if sy>0 else 0,2500],'a_p'), M.cube('gate_e',[-W/2,-6 if sy>0 else -1,2468],[W/2,1 if sy>0 else 6,2502],'a_m')]); top.append(g)
        A.add(g,'position',[(0,(0,sy*H/2,0)),(219,(0,sy*H/2,0)),(223.4,(0,sy*8,0)),(223.8,(0,0,0))])
    cue(219,'rumble',1.0); cue(223.8,'slam',1.2)
    # 핵의 방 (z 2600~3500, 900 칸) + 핵
    CZ=3050; R=450
    for nm,fr,to in (('cw',[R,-R,ZE],[R+40,R,ZE+900]),('cw',[-R-40,-R,ZE],[-R,R,ZE+900]),('cf',[-R,-R-40,ZE],[R,-R,ZE+900]),('cc',[-R,R,ZE],[R,R+40,ZE+900]),('cb',[-R,-R,ZE+900],[R,R,ZE+940])): top.append(M.cube(nm,fr,to,'hull_a2'))
    for sx in (-1,1):
        top+= [M.cube('cfw',[min(sx*W/2,sx*R),-R,ZE-10],[max(sx*W/2,sx*R),R,ZE],'hull_a'), M.cube('cfw2',[-W/2,sx*H/2 if sx>0 else -R,ZE-10],[W/2,R if sx>0 else -H/2,ZE],'hull_a')]
    for a in range(8):
        an=a/8*6.283; x=380*math.cos(an); y=380*math.sin(an); top+= [M.cube('cstrut',[min(x*0.3,x)-10,min(y*0.3,y)-10,CZ-12],[max(x*0.3,x)+10,max(y*0.3,y)+10,CZ+12],'a_p')] if a%2==0 else [M.cube('clight',[x-14,y-14,ZE+880],[x+14,y+14,ZE+900],'a_m')]
    core=Ship(M,'core_'); n=3; s_=62
    for i in range(n):
        for j in range(n):
            for k in range(n):
                core.cube([(i-1.5)*s_,(j-1.5)*s_,CZ+(k-1.5)*s_],[(i-0.5)*s_,(j-0.5)*s_,CZ+(k-0.5)*s_],'maw' if (i+j+k)%2 else 'a_mc')
    core.glow('heart',[-40,-40,CZ-40],[40,40,CZ+40],'glow_w'); cg=core.group(); cg['origin']=[0,0,CZ]; top.append(cg); cyc(A,cg,'scale',200,229.4,(1,1,1),(1.06,1.06,1.06),0.5,rest=(1,1,1)); A.add(cg,'rotation',[(0,(0,0,0)),(229.4,(0,229.4*20,0))])
    explode(A,core,229.5,center=(0,0,CZ),power=420,dur=2.4,seed=2,keep_scale=0.3); cue(229.5,'bigboom',1.5)
    fl=M.group('flash',[0,0,CZ],[M.cube('fl',[-1,-1,CZ-1],[1,1,CZ+1],'glow_w')]); top.append(fl); A.add(fl,'scale',[(0,(0,0,0)),(229.4,(0,0,0)),(229.7,(110,)*3),(232,(400,)*3),(L,(400,)*3)]); burst(M,A,top,229.5,(0,0,CZ),n=20,speed=520,size=30,dur=2.4,cols=('a_m','a_mc','glow_w','fire1'),seed=7); cue(230.2,'whiteout',1.3)
    # 주인공 + 쫓는 요격기 둘
    def slalom(t0,t1,off=(0,0),lag=0.0):
        pts=[(200+lag,0,0,-200)]; zs=[0]+[z for z,_,_ in OBS]+[2480]; n_=len(zs)
        for q,z in enumerate(zs[1:-1]):
            _,sd,kind=OBS[q]; t=t0+(t1-t0)*(z/2480)+lag; x=(-sd*74 if kind=='v' and sd else (80 if kind=='v' else rng.uniform(-50,50)))+off[0]; y=(-sd*78 if kind=='h' and sd else (80 if kind=='h' else rng.uniform(-40,40)))+off[1]
            pts.append((t,x,y,z))
        pts.append((t1+lag,0+off[0],0+off[1],2480)); return pts
    hero=Craft(M,A,top,fighter(M,'f0_','e_or'),0,0,-200,yaw=180); rng=random.Random(3); hp=slalom(201,223.0); hero.path(hp)
    hero.path([(225,0,0,2640),(227,180,60,2780),(229.2,300,120,3000),(231,330,200,3300),(232,330,220,3400)])
    for q,(lag,off) in enumerate(((1.0,(12,10)),(1.7,(-14,-8)))):
        rng=random.Random(3); c=Craft(M,A,top,interceptor(M,f'i{q}_'),0,0,-300,yaw=180).show([(203,L)]); pts=[(p[0]+lag,p[1]+off[0],p[2]+off[1],p[3]) for p in hp]
        if q==0:      # 기둥(z 1480)에 부딪힘
            pts=[p for p in pts if p[3]<1480]+[(pts[[i for i,p in enumerate(pts) if p[3]>=1480][0]][0],70,10,1468)]; c.path(pts); c.boom(pts[-1][0],power=50,seed=31,size=1.4)
        else:         # 닫히는 문에 부딪힘
            pts=[p for p in pts if p[3]<2400]+[(224.6,0,0,2462)]; c.path(pts); c.boom(224.6,power=50,seed=32,size=1.4)
        for t in (206+q*2,210+q*2,214+q): volley(M,A,top,c,hero,t,3,col='a_m',cuek='laser2',spread=30,seed=int(t))
        globals()[f'_ic{q}']=c
    for k,t in enumerate((226.2,226.9,227.6,228.3,229.0)): volley(M,A,top,hero,(rng.uniform(-40,40),rng.uniform(-40,40),CZ-90),t,3,col='glow_c',spread=8,seed=k)
    cue(200.5,'whoosh',1.0)
    C1=cam((0,[0,14,-64],[0,4,60],{'fov':74,'roll':0}),(0.25,[10,10,-56],[0,2,60],{'fov':82,'roll':-12}),(0.5,[-10,12,-60],[0,2,60],{'fov':78,'roll':12}),(0.75,[8,8,-52],[0,2,60],{'fov':84,'roll':-10}),(1,[0,12,-60],[0,2,60],{'fov':76,'roll':6}))
    sh('굴1','I',200,206,C1,SKY,follow='f0_mv',shake=2.4)
    sh('앞에서','I',206,210,cam((0,[0,8,90],[0,4,-40],{'fov':60,'roll':6}),(1,[10,10,80],[0,4,-40],{'fov':66,'roll':-6})),SKY,follow='f0_mv',shake=2)
    sh('일인칭','I',210,215,cam((0,[0,5,14],[0,3,120],{'fov':86,'roll':10}),(0.5,[0,5,14],[0,3,120],{'fov':92,'roll':-14}),(1,[0,5,14],[0,3,120],{'fov':86,'roll':8})),SKY,follow='f0_mv',shake=2.6)
    sh('기둥충돌','I',215,218,cam((0,[-100,-50,1330],[40,0,1470],{'fov':60}),(1,[-90,-40,1370],[60,0,1470],{'fov':50})),SKY,shake=4)
    sh('굴2','I',218,222,C1,SKY,follow='f0_mv',shake=2.6)
    sh('문','I',222,225,cam((0,[80,40,2300],[0,0,2480],{'fov':60,'roll':-8}),(0.45,[70,30,2330],[0,0,2480],{'fov':52,'roll':0,'shake':0.5}),(1,[60,30,2350],[0,0,2470],{'fov':56,'shake':1})),SKY,shake=4)
    sh('핵','I',225,229.4,cam((0,[0,20,-80],[30,10,200],{'fov':64}),(1,[40,24,-70],[-60,-20,200],{'fov':56})),SKY,follow='f0_mv',shake=1.6)
    sh('핵폭발','I',229.4,232,cam((0,[-380,200,2640],[0,0,CZ],{'fov':60}),(1,[-400,220,2620],[0,0,CZ],{'fov':70})),SKY,shake=6)
    save(M,A,top,'모함안','I')

SETS=dict(O1=lambda: set_O('O1'),O2=lambda: set_O('O2'),O3=lambda: set_O('O3'),O4=lambda: set_O('O4'),I=set_I)
if __name__=='__main__':
    want=sys.argv[1] if len(sys.argv)>1 else 'all'
    for k,f in SETS.items():
        if want!='all' and k not in want:
            _o=Model.save; Model.save=lambda *a,**kw: None
            try: f()
            finally: Model.save=_o
        else: f()
    json.dump({k:{'ropes':[]} for k in SETS},open(f'{OUT}/세트정보.json','w'))
    S=sorted(D.SHOTS,key=lambda s:s['t0'])
    uniq=lambda L_,k: list({k(x):x for x in L_}.values()); D.CAPS[:]=uniq(D.CAPS,lambda c:(c['t0'],c['text'])); CUES[:]=uniq(CUES,lambda c:(c['t'],c['kind']))
    for i,s in enumerate(S): s['name']=f"{i:03d}_{s['name'].split('_',1)[1]}"
    SLOW={'지구','기지','먼빛','다가옴','그림자','크기','경보','함대','함교뒤','충전','잔해','결심','고요','해돋이','끝'}      # 느린 장면은 1초 12장 (촬영 시간 때문에), 전투는 24장
    for s in S:
        if s['name'].split('_',1)[1] in SLOW: s['fps']=12
    bad=[(a['name'],b['name'],round(b['t0']-a['t1'],2)) for a,b in zip(S,S[1:]) if abs(b['t0']-a['t1'])>0.02]
    json.dump({'shots':S},open(f'{OUT}/샷목록.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
    json.dump({'duration':L,'captions':sorted(D.CAPS,key=lambda c:c['t0']),'cues':sorted(CUES,key=lambda c:c['t'])},open(f'{ROOT}/시간표.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
    print(len(S),'샷',sum(round((s['t1']-s['t0'])*s['fps']) for s in S),'장',S[-1]['t1'],'초 | 이어지지 않는 곳:',bad or '없음','| 효과음',len(CUES))
