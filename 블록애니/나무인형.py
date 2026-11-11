"""나무 인형(오리지널 캐릭터) 부품 — 원통·공·원뿔 모양(Blockbench 메시) + 나뭇결 무늬.
   디즈니 피노키오 생김새(깃털 빨간 모자·노란 멜빵바지·파란 나비넥타이)는 쓰지 않음 → 세이지 셔츠·남색 반바지·빨간 나무 신발.
   묶음 이름은 블록 인물과 같게(body·head·arm_left·arm_right·leg_left·leg_right·hand_l·hand_r). 팔·다리는 한 덩어리(블록처럼 흔들기)
   키 약 32 (s=1).  앞 = -z"""
import os, sys, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 블록인물 import Model, move, Anim, find, U

# ---------------- 메시 모양 (원통·공) ----------------
def _basis(d):
    """방향 d 에 수직인 두 단위 벡터"""
    dx,dy,dz=d; L=math.sqrt(dx*dx+dy*dy+dz*dz); d=(dx/L,dy/L,dz/L)
    a=(1,0,0) if abs(d[0])<0.9 else (0,0,1)
    u=(d[1]*a[2]-d[2]*a[1], d[2]*a[0]-d[0]*a[2], d[0]*a[1]-d[1]*a[0]); Lu=math.sqrt(sum(x*x for x in u)); u=tuple(x/Lu for x in u)
    v=(d[1]*u[2]-d[2]*u[1], d[2]*u[0]-d[0]*u[2], d[0]*u[1]-d[1]*u[0])
    return d,u,v

def _mesh(M, name, V, F):
    e={'name':name,'type':'mesh','uuid':U(),'origin':[0,0,0],'rotation':[0,0,0],'vertices':V,'faces':F,'color':0,'export':True,'visibility':True}
    M.els.append(e); return e['uuid']

def cyl(M, name, p0, p1, r0, r1, col, seg=12, caps=True):
    """p0 → p1 원통 (r0 → r1 굵기, r1≈0 이면 원뿔)"""
    d,u,v=_basis([p1[i]-p0[i] for i in range(3)]); u0,v0,u1,v1=M.sw[col]; V={}; F={}
    for i in range(seg):
        a=2*math.pi*i/seg; ca,sa=math.cos(a),math.sin(a)
        V[f'b{i}']=[p0[k]+r0*(ca*u[k]+sa*v[k]) for k in range(3)]
        V[f't{i}']=[p1[k]+max(r1,0.01)*(ca*u[k]+sa*v[k]) for k in range(3)]
    for i in range(seg):
        j=(i+1)%seg; uu0=u0+(u1-u0)*i/seg; uu1=u0+(u1-u0)*(i+1)/seg
        F[f's{i}']={'uv':{f'b{i}':[uu0,v1],f'b{j}':[uu1,v1],f't{j}':[uu1,v0],f't{i}':[uu0,v0]},'vertices':[f'b{j}',f'b{i}',f't{i}',f't{j}'],'texture':0}
    if caps:
        V['bc']=list(p0); V['tc']=list(p1); m=[(u0+u1)/2,(v0+v1)/2]
        for i in range(seg):
            j=(i+1)%seg
            F[f'top{i}']={'uv':{f't{i}':[u0,v0],f't{j}':[u1,v0],'tc':m},'vertices':[f't{j}','tc',f't{i}'],'texture':0}
            F[f'bot{i}']={'uv':{f'b{i}':[u0,v1],f'b{j}':[u1,v1],'bc':m},'vertices':[f'b{i}','bc',f'b{j}'],'texture':0}
    return _mesh(M,name,V,F)

def sphere(M, name, c, r, col, seg=12, rings=8, sx=1.0, sy=1.0, sz=1.0):
    """공 (sx·sy·sz 로 납작·길쭉하게).  위·아래 끝은 꼭짓점 하나에 세모로 모음 (한 점에 겹친 꼭짓점이 검은 점으로 보이지 않게)"""
    u0,v0,u1,v1=M.sw[col]; V={}; F={}
    P=lambda th,a:[c[0]+r*sx*math.sin(th)*math.cos(a), c[1]-r*sy*math.cos(th), c[2]+r*sz*math.sin(th)*math.sin(a)]
    V['bot']=[c[0],c[1]-r*sy,c[2]]; V['top']=[c[0],c[1]+r*sy,c[2]]
    for k in range(1,rings):
        for i in range(seg): V[f'p{k}_{i}']=P(math.pi*k/rings,2*math.pi*i/seg)
    for i in range(seg):
        j=(i+1)%seg; uu0=u0+(u1-u0)*i/seg; uu1=u0+(u1-u0)*(i+1)/seg; vr=(v1-v0)/rings
        F[f'b{i}']={'uv':{'bot':[(uu0+uu1)/2,v1],f'p1_{j}':[uu1,v1-vr],f'p1_{i}':[uu0,v1-vr]},'vertices':['bot',f'p1_{j}',f'p1_{i}'],'texture':0}
        F[f't{i}']={'uv':{'top':[(uu0+uu1)/2,v0],f'p{rings-1}_{i}':[uu0,v0+vr],f'p{rings-1}_{j}':[uu1,v0+vr]},'vertices':['top',f'p{rings-1}_{i}',f'p{rings-1}_{j}'],'texture':0}
        for k in range(1,rings-1):
            vv0=v1-vr*k; vv1=v1-vr*(k+1)
            F[f'q{k}_{i}']={'uv':{f'p{k}_{i}':[uu0,vv0],f'p{k}_{j}':[uu1,vv0],f'p{k+1}_{j}':[uu1,vv1],f'p{k+1}_{i}':[uu0,vv1]},
                            'vertices':[f'p{k}_{i}',f'p{k}_{j}',f'p{k+1}_{j}',f'p{k+1}_{i}'],'texture':0}
    return _mesh(M,name,V,F)

# ---------------- 나뭇결 색 ----------------
def wood_fn(base, dark, seed):
    rnd=random.Random(seed); waves=[(rnd.uniform(0,6.28),rnd.uniform(0.25,0.6)) for _ in range(3)]
    def fn(x,y):   # 세로로 흐르는 나뭇결 (y = 결 방향)
        g=sum(math.sin(x*f+ph+math.sin(y*0.35+ph)*1.4) for ph,f in waves)/3
        t=0.5+0.5*g; t=t*t
        return tuple(int(base[i]*(1-t*0.45)+dark[i]*(t*0.45)) for i in range(3))
    return fn

def palette(M):
    M.swatch('wood',wood_fn((214,168,112),(150,100,55),1),4); M.swatch('wood_l',wood_fn((228,186,132),(170,120,70),2),3)
    M.swatch('wood_hair',wood_fn((92,58,34),(55,32,18),3),3)
    M.swatch('paint_shirt',wood_fn((132,168,140),(100,135,110),4),3); M.swatch('paint_short',wood_fn((52,66,108),(38,48,84),5),3)
    M.swatch('paint_shoe',wood_fn((190,55,45),(150,40,35),6),3); M.swatch('paint_belt',(70,45,30),3)
    M.swatch('eye_w',(250,250,248),2); M.swatch('eye_k',(25,22,22),2); M.swatch('cheek',(240,140,130),3); M.swatch('mouth',(150,60,55),3)
    M.swatch('button',(235,205,120),3)

def doll(M, tag, s=1.0, nose=4.0):
    """오리지널 나무 인형.  팔·다리는 블록 인물처럼 통째로 흔들림.  nose: 코 길이"""
    S=lambda p:[x*s for x in p]
    def C(n,a,b,r0,r1,col,seg=12): return cyl(M,n,S(a),S(b),r0*s,r1*s,col,seg)
    def B(n,c,r,col,**k): return sphere(M,n,S(c),r*s,col,**k)
    G=lambda n,o,ch: M.group(tag+n,S(o),ch)
    # 다리·팔은 블록 인물처럼 한 덩어리 (엉덩이·어깨에서만 흔들림, 사용자 결정 2026-11-11: 팔꿈치·무릎 관절이 어색함)
    def leg(side):
        x=2.1*side
        return G('leg_'+('left' if side>0 else 'right'),[x,12,0],[C('thigh',[x,12.2,0],[x,7.0,0],1.9,1.6,'paint_short'),
                 C('shin',[x,7.4,0],[x,1.6,0],1.3,1.1,'wood'), B('shoe',[x,1.2,-0.8],2.0,'paint_shoe',sx=0.95,sy=0.62,sz=1.45)])
    def arm(side):
        x=5.4*side; n='l' if side>0 else 'r'
        hand=G('hand_'+n,[x,11.2,0],[])
        return G('arm_'+('left' if side>0 else 'right'),[x,21.5,0],[B('shoulder',[x,21.4,0],1.6,'paint_shirt'),
               C('upper',[x,21,0],[x,15.6,0],1.3,1.15,'paint_shirt'), C('fore',[x,16.2,0],[x,12.4,0],1.05,0.9,'wood'),
               B('hand',[x,11.6,0],1.35,'wood_l',sx=0.9,sy=1.1,sz=0.9), hand])
    legL,legR=leg(1),leg(-1); armL,armR=arm(1),arm(-1)
    body=[C('waist',[0,12,0],[0,14.6,0],3.6,3.5,'paint_short',seg=16), C('belt',[0,14.5,0],[0,15.5,0],3.65,3.6,'paint_belt',seg=16),
          C('chest',[0,15.4,0],[0,21.6,0],3.5,4.1,'paint_shirt',seg=16), B('shoulder_top',[0,21.6,0],4.1,'paint_shirt',sy=0.35,seg=16),
          B('btn1',[0,19.6,-3.85],0.45,'button',seg=8,rings=6), B('btn2',[0,17.4,-3.7],0.45,'button',seg=8,rings=6),
          C('neck',[0,22.6,0],[0,24.4,0],1.1,1.1,'wood')]
    # 머리: 공 + 깎은 머리카락 + 긴 원뿔 코 + 동그란 눈 + 볼터치
    hk=[B('head',[0,28,0],4.0,'wood',seg=16,rings=10), B('hair',[0,29.3,0.5],4.15,'wood_hair',seg=16,rings=10,sy=0.82,sz=0.98),
        C('nose',[0,27.4,-3.6],[0,27.6,-3.6-nose],0.75,0.12,'wood_l',seg=10),
        B('eye_l',[1.55,28.6,-3.45],0.85,'eye_w',seg=10,rings=6,sz=0.55), B('eye_r',[-1.55,28.6,-3.45],0.85,'eye_w',seg=10,rings=6,sz=0.55),
        B('pupil_l',[1.55,28.5,-3.95],0.42,'eye_k',seg=8,rings=6,sz=0.5), B('pupil_r',[-1.55,28.5,-3.95],0.42,'eye_k',seg=8,rings=6,sz=0.5),
        B('cheek_l',[2.5,26.6,-3.0],0.75,'cheek',seg=8,rings=6,sz=0.4), B('cheek_r',[-2.5,26.6,-3.0],0.75,'cheek',seg=8,rings=6,sz=0.4),
        C('mouth',[-0.9,25.7,-3.1],[0.9,25.7,-3.1],0.24,0.24,'mouth',seg=6)]
    head=G('head',[0,24.4,0],hk)
    bod=G('body',[0,12,0],body+[head,armL,armR])
    return G('root',[0,0,0],[bod,legL,legR])
