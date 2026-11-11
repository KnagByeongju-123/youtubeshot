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
    M.swatch('paint_dress',wood_fn((235,125,105),(200,95,80),7),3); M.swatch('paint_sock',(245,242,235),2); M.swatch('paint_ribbon',(250,215,90),3)
    M.swatch('paint_mustard',wood_fn((215,170,70),(180,135,50),8),3); M.swatch('paint_apron',wood_fn((140,95,60),(110,72,45),9),3)
    M.swatch('paint_pants',wood_fn((95,95,100),(70,70,75),10),3); M.swatch('paint_cap',wood_fn((70,110,150),(50,85,120),11),3)
    M.swatch('wood_grey',wood_fn((205,200,190),(165,160,150),12),3); M.swatch('wood_dk',wood_fn((150,100,58),(105,68,38),13),3)

def doll(M, tag, s=1.0, nose=1.8, kind='boy', extra_arms=()):
    """오리지널 나무 인형.  팔·다리는 블록 인물처럼 통째로 흔들림.  nose: 코 길이(짧고 끝이 둥글게)
       kind: boy(나무 소년) / girl(나무 소녀: 원피스·양갈래) / grandpa(목수 할아버지: 수염·털모자·앞치마·긴 바지)
       extra_arms: 갈아 끼울 팔 [(쪽 'l'|'r', 소매 색, 짧은 소매?)] → 묶음 arm_left2 / arm_right2 (처음엔 숨겨 두고 장면에서 보이게)"""
    S=lambda p:[x*s for x in p]
    def C(n,a,b,r0,r1,col,seg=12): return cyl(M,n,S(a),S(b),r0*s,r1*s,col,seg)
    def B(n,c,r,col,**k): return sphere(M,n,S(c),r*s,col,**k)
    def X(n,a,b,col): return M.cube(n,S(a),S(b),col)
    G=lambda n,o,ch: M.group(tag+n,S(o),ch)
    shirt={'boy':'paint_shirt','girl':'paint_dress','grandpa':'paint_mustard'}[kind]
    bottom={'boy':'paint_short','girl':'paint_dress','grandpa':'paint_pants'}[kind]
    shoe={'boy':'paint_shoe','girl':'paint_shoe','grandpa':'paint_apron'}[kind]
    # 다리·팔은 블록 인물처럼 한 덩어리 (엉덩이·어깨에서만 흔들림, 사용자 결정 2026-11-11: 팔꿈치·무릎 관절이 어색함)
    def leg(side):
        x=2.1*side; k=[]
        if kind=='boy':     k+= [C('thigh',[x,12.2,0],[x,7.0,0],1.9,1.6,bottom), C('shin',[x,7.4,0],[x,1.6,0],1.3,1.1,'wood')]
        elif kind=='girl':  k+= [C('shin',[x,11.5,0],[x,4.4,0],1.2,1.05,'wood'), C('sock',[x,4.6,0],[x,1.6,0],1.25,1.15,'paint_sock')]
        else:               k+= [C('pants',[x,12.2,0],[x,2.2,0],1.9,1.65,bottom)]
        k.append(B('shoe',[x,1.2,-0.8],2.0,shoe,sx=0.95,sy=0.62,sz=1.45))
        return G('leg_'+('left' if side>0 else 'right'),[x,12,0],k)
    def arm(side, col=None, short=None, suffix=''):
        col=col or shirt; short=(kind=='girl') if short is None else short
        x=5.4*side; n=('l' if side>0 else 'r')+suffix
        hand=G('hand_'+n,[x,11.2,0],[])
        sleeve_end=18.0 if short else 15.6
        return G('arm_'+('left' if side>0 else 'right')+suffix,[x,21.5,0],[B('shoulder',[x,21.4,0],1.6,col),
               C('upper',[x,21,0],[x,sleeve_end,0],1.3,1.15,col), C('fore',[x,sleeve_end+0.6,0],[x,12.4,0],1.05,0.9,'wood'),
               B('hand',[x,11.6,0],1.35,'wood_l',sx=0.9,sy=1.1,sz=0.9), hand])
    legL,legR=leg(1),leg(-1); armL,armR=arm(1),arm(-1)
    extras=[arm(1 if sd=='l' else -1, col, sh, '2') for sd,col,sh in extra_arms]
    if kind=='girl':    # 원피스: 위는 몸통, 아래는 퍼지는 치마
        body=[C('chest',[0,14.6,0],[0,21.6,0],3.4,4.0,shirt,seg=16), C('skirt',[0,15.0,0],[0,8.4,0],3.5,5.4,shirt,seg=18),
              C('collar',[0,21.2,0],[0,22.0,0],2.2,1.6,'paint_sock',seg=12)]
    else:
        body=[C('waist',[0,12,0],[0,14.6,0],3.6,3.5,bottom,seg=16), C('belt',[0,14.5,0],[0,15.5,0],3.65,3.6,'paint_belt',seg=16),
              C('chest',[0,15.4,0],[0,21.6,0],3.5,4.1,shirt,seg=16)]
    body+= [B('shoulder_top',[0,21.6,0],4.1 if kind!='girl' else 4.0,shirt,sy=0.35,seg=16), C('neck',[0,22.6,0],[0,24.4,0],1.1,1.1,'wood')]
    if kind=='boy': body+= [B('btn1',[0,19.6,-3.85],0.45,'button',seg=8,rings=6), B('btn2',[0,17.4,-3.7],0.45,'button',seg=8,rings=6)]
    if kind=='grandpa': body+= [X('apron',[-2.9,8.6,-4.25],[2.9,19.5,-3.85],'paint_apron'), X('apron_pocket',[-1.6,12,-4.45],[1.6,14.2,-4.25],'wood_dk'),
                                X('strap_l',[1.6,19.4,-4.1],[2.4,21.8,-3.6],'paint_apron'), X('strap_r',[-2.4,19.4,-4.1],[-1.6,21.8,-3.6],'paint_apron')]
    # 머리: 공 + 깎은 머리카락 + 짧고 둥근 코 + 동그란 눈 + 볼터치
    hk=[B('head',[0,28,0],4.0,'wood',seg=16,rings=10),
        C('nose',[0,27.4,-3.5],[0,27.5,-3.5-nose],0.85,0.7,'wood_l',seg=10), B('nose_tip',[0,27.5,-3.5-nose],0.72,'wood_l',seg=10,rings=6),
        B('eye_l',[1.55,28.6,-3.45],0.85,'eye_w',seg=10,rings=6,sz=0.55), B('eye_r',[-1.55,28.6,-3.45],0.85,'eye_w',seg=10,rings=6,sz=0.55),
        B('pupil_l',[1.55,28.5,-3.95],0.42,'eye_k',seg=8,rings=6,sz=0.5), B('pupil_r',[-1.55,28.5,-3.95],0.42,'eye_k',seg=8,rings=6,sz=0.5),
        B('cheek_l',[2.5,26.6,-3.0],0.75,'cheek',seg=8,rings=6,sz=0.4), B('cheek_r',[-2.5,26.6,-3.0],0.75,'cheek',seg=8,rings=6,sz=0.4)]
    if kind=='boy':
        hk+= [B('hair',[0,29.3,0.5],4.15,'wood_hair',seg=16,rings=10,sy=0.82,sz=0.98), C('mouth',[-0.9,25.7,-3.1],[0.9,25.7,-3.1],0.24,0.24,'mouth',seg=6)]
    if kind=='girl':
        hk+= [B('hair',[0,29.3,0.4],4.18,'wood_hair',seg=16,rings=10,sy=0.84,sz=0.99), C('mouth',[-0.8,25.7,-3.1],[0.8,25.7,-3.1],0.24,0.24,'mouth',seg=6),
              B('tail_l',[4.6,27.2,1.0],1.5,'wood_hair',seg=10,rings=6,sy=1.5), B('tail_r',[-4.6,27.2,1.0],1.5,'wood_hair',seg=10,rings=6,sy=1.5),
              B('ribbon_l',[4.1,29.2,1.0],0.9,'paint_ribbon',seg=8,rings=6,sx=0.7,sz=1.4), B('ribbon_r',[-4.1,29.2,1.0],0.9,'paint_ribbon',seg=8,rings=6,sx=0.7,sz=1.4)]
    if kind=='grandpa':
        hk+= [B('cap',[0,30.0,0.2],4.2,'paint_cap',seg=16,rings=10,sy=0.72), C('cap_rim',[0,29.1,0.2],[0,30.1,0.2],4.25,4.25,'paint_cap',seg=16),
              B('cap_ball',[0,33.1,0.2],0.9,'paint_sock',seg=8,rings=6),
              B('side_hair_l',[3.5,27.4,1.8],1.05,'wood_grey',seg=10,rings=6,sx=0.8,sz=1.3), B('side_hair_r',[-3.5,27.4,1.8],1.05,'wood_grey',seg=10,rings=6,sx=0.8,sz=1.3), B('back_hair',[0,27.2,3.2],2.6,'wood_grey',seg=12,rings=6,sy=0.55,sz=0.5),   # 귀 뒤·뒤통수 흰머리 (얼굴 옆을 가리지 않게)
              B('beard',[0,24.9,-2.4],2.7,'wood_grey',seg=12,rings=8,sx=1.15,sy=1.05,sz=0.7), B('mustache',[0,26.4,-3.55],1.5,'wood_grey',seg=10,rings=6,sx=1.3,sy=0.45,sz=0.5)]
    head=G('head',[0,24.4,0],hk)
    bod=G('body',[0,12,0],body+[head,armL,armR]+extras)
    return G('root',[0,0,0],[bod,legL,legR])

def wood_dog(M, tag, s=1.0):
    """끌고 다니는 나무 강아지 장난감 (바퀴 넷).  앞 = -z.  묶음: body·head·tail·wheels"""
    S=lambda p:[x*s for x in p]
    def C(n,a,b,r0,r1,col,seg=12): return cyl(M,n,S(a),S(b),r0*s,r1*s,col,seg)
    def B(n,c,r,col,**k): return sphere(M,n,S(c),r*s,col,**k)
    G=lambda n,o,ch: M.group(tag+n,S(o),ch)
    k=[C('board',[0,3.4,-6],[0,3.4,6],0.01,0.01,'wood_dk')]   # (자리만)
    k=[M.cube('board',S([-3,2.6,-6.5]),S([3,3.6,6.5]),'wood_dk')]
    for x in (-3.4,3.4):
        for z in (-4.5,4.5): k.append(C('wheel',[x-0.6,2.1,z],[x+0.6,2.1,z],1.9,1.9,'paint_shoe',seg=14))
    for x in (-1.6,1.6):
        for z in (-3.6,3.6): k.append(C('leg',[x,3.6,z],[x,6.4,z],0.75,0.75,'wood'))
    k+= [C('torso',[0,8.6,5.2],[0,8.6,-5.2],3.0,3.0,'wood',seg=14), B('spot',[1.2,10.6,1.5],1.6,'wood_dk',seg=10,rings=6,sy=0.5),
         B('collar',[0,9.2,-5.0],2.6,'paint_shoe',seg=12,rings=6,sz=0.35)]
    hk=[B('head',[0,12.4,-6.4],3.0,'wood',seg=14,rings=8), C('snout',[0,11.6,-8.6],[0,11.5,-10.2],1.4,1.2,'wood_l',seg=10),
        B('dnose',[0,11.9,-10.3],0.6,'eye_k',seg=8,rings=6), B('deye_l',[1.2,13.3,-8.9],0.5,'eye_k',seg=8,rings=6), B('deye_r',[-1.2,13.3,-8.9],0.5,'eye_k',seg=8,rings=6),
        B('ear_l',[3.0,12.2,-6.2],1.3,'wood_dk',seg=10,rings=6,sx=0.45,sy=1.6), B('ear_r',[-3.0,12.2,-6.2],1.3,'wood_dk',seg=10,rings=6,sx=0.45,sy=1.6)]
    head=G('head',[0,10.6,-5.4],hk)
    tail=G('tail',[0,10.2,5.2],[C('tail',[0,10.2,5.2],[0,13.2,6.8],0.5,0.35,'wood',seg=8)])
    return G('root',[0,0,0],k+[head,tail])


def loose_arm(M, tag, top, bottom, col, short=False, s=1.0, pieces=1):
    """몸에서 떨어진 팔 (소품).  top → bottom 방향으로 어깨~손.  pieces=2 면 팔꿈치에서 두 동강 (묶음 tag+'up', tag+'low')"""
    def P(t): return [top[i]+(bottom[i]-top[i])*t for i in range(3)]
    L=math.dist(top,bottom); k=(21.4-(18.0 if short else 15.6))/9.8   # 소매 끝 비율
    up=[sphere(M,'l_sh',top,1.6*s,col), cyl(M,'l_up',top,P(k),1.3*s,1.15*s,col)]
    low=[cyl(M,'l_fore',P(k+0.06),P(0.92),1.05*s,0.9*s,'wood'), sphere(M,'l_hand',bottom,1.35*s,'wood_l')]
    if pieces==1: return M.group(tag+'root',top,up+low)
    return M.group(tag+'up',top,up), M.group(tag+'low',P(k),low)
