"""점토 인형(오리지널 캐릭터) 부품 — 나무 인형과 같은 원통·공 메시에 '손으로 빚은' 느낌을 더함.
   - 공·원통 표면을 살짝 울퉁불퉁하게 (lump): 손으로 주물러 만든 점토처럼
   - 나뭇결 대신 무광 단색 + 옅은 얼룩 (clay_fn)
   - 단추 눈(흰 공 + 검은 점), 큰 머리·짧고 통통한 팔다리
   유명 점토 캐릭터(월레스와 그로밋·핑구·숀더쉽)의 생김새는 쓰지 않음.
   묶음 이름은 블록 인물과 같게(body·head·arm_left·arm_right·leg_left·leg_right·hand_l·hand_r) → 걷기·손 흔들기 그대로.
   앞 = -z"""
import os, sys, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 블록인물 import Model, move, Anim, find, U
from 나무인형 import cyl, sphere

# ---------------- 점토 색 (무광 + 옅은 얼룩) ----------------
def clay_fn(base, seed, amt=0.07):
    rnd=random.Random(seed); ph=[rnd.uniform(0,6.28) for _ in range(4)]
    def fn(x,y):
        t=(math.sin(x*0.7+ph[0])*math.cos(y*0.55+ph[1])+math.sin((x+y)*0.4+ph[2])*0.6)/1.6
        k=1+amt*t
        return tuple(max(0,min(255,int(c*k))) for c in base)
    return fn

def clay_palette(M):
    C=lambda n,c,s: M.swatch(n,clay_fn(c,s),3)
    C('skin',(255,214,180),1); C('skin_d',(245,188,150),2)
    C('sweater',(222,92,62),3); C('stripe',(248,232,196),4)
    C('pants',(70,112,168),5); C('shoe',(120,78,52),6); C('hair',(92,56,36),7)
    M.swatch('eye_w',(252,252,250),1); M.swatch('eye_k',(28,24,24),1)
    C('cheek',(244,150,140),8); C('mouth',(150,58,52),9); C('brow',(80,48,32),10)
    C('dog',(255,248,228),11); C('dog_p',(196,128,72),12); C('collar',(60,150,120),13)
    C('tongue',(236,120,130),14); C('dnose',(40,32,30),15); C('tag',(240,200,80),16)

# ---------------- 손으로 빚은 울퉁불퉁함 ----------------
def lump(M, c, amt=0.035, seed=0):
    """방금 만든 메시(M.els[-1])의 꼭짓점을 중심 c 에서 멀어지거나 가까워지게 부드럽게 흔듦"""
    e=M.els[-1]; rnd=random.Random(seed); P=[(rnd.uniform(1.5,3.0),rnd.uniform(0,6.28)) for _ in range(3)]
    for k,v in e['vertices'].items():
        d=[v[i]-c[i] for i in range(3)]; L=math.sqrt(sum(x*x for x in d)) or 1
        n=[x/L for x in d]
        f=sum(math.sin(n[0]*fr+ph)*math.cos(n[1]*fr*0.8+ph*0.5)*math.sin(n[2]*fr*1.1+ph*1.3) for fr,ph in P)/3
        s=1+amt*f*2
        e['vertices'][k]=[round(c[i]+d[i]*s,4) for i in range(3)]

_seed=[0]
def _ns(): _seed[0]+=1; return _seed[0]

def CB(M, n, c, r, col, amt=0.035, **k):
    """점토 공"""
    k.setdefault('seg',18); k.setdefault('rings',12)
    u=sphere(M,n,c,r,col,**k); lump(M,c,amt,_ns()); return u
def CC(M, n, a, b, r0, r1, col, amt=0.03, seg=14):
    """점토 원통 (가운데 기준으로 살짝 울퉁불퉁)"""
    u=cyl(M,n,a,b,r0,r1,col,seg); lump(M,[(a[i]+b[i])/2 for i in range(3)],amt,_ns()); return u

def _on(c, r, dx, dy, out=0.0, sx=1, sy=1, sz=1):
    """공(중심 c, 반지름 r, 납작 비율 sx·sy·sz) 앞면(-z) 위의 점: 가로 dx, 세로 dy 만큼 옮긴 곳 + 바깥으로 out"""
    X=dx/(r*sx); Y=dy/(r*sy); Z=math.sqrt(max(0.0,1-X*X-Y*Y))
    p=[c[0]+dx, c[1]+dy, c[2]-r*sz*Z]
    n=[X/sx, Y/sy, -Z/sz]; L=math.sqrt(sum(x*x for x in n)) or 1
    return [p[i]+out*n[i]/L for i in range(3)]

# ---------------- 점토 소년 ----------------
def clay_boy(M, tag, s=1.0):
    """점토 소년: 큰 머리, 빨간 털실 스웨터(크림색 줄), 파란 바지, 갈색 신발, 갈색 머리 뭉치, 단추 눈.  키 약 31"""
    S=lambda p:[x*s for x in p]
    B=lambda n,c,r,col,**k: CB(M,n,S(c),r*s,col,**k)
    C=lambda n,a,b,r0,r1,col,**k: CC(M,n,S(a),S(b),r0*s,r1*s,col,**k)
    G=lambda n,o,ch: M.group(tag+n,S(o),ch)
    def leg(side):
        x=2.2*side
        k=[C('leg',[x,9.5,0],[x,2.6,0],2.15,1.95,'pants'),
           B('shoe',[x,1.35,-0.7],2.2,'shoe',sx=1.0,sy=0.62,sz=1.4)]
        return G('leg_'+('left' if side>0 else 'right'),[x,9.5,0],k)
    def arm(side):
        x=5.3*side; n='l' if side>0 else 'r'
        k=[B('shoulder',[x,17.4,0],2.0,'sweater'),
           C('arm',[x+0.5*side,17.0,0],[x+0.9*side,11.4,0],1.75,1.55,'sweater'),
           C('cuff',[x+0.9*side,11.9,0],[x+0.95*side,10.9,0],1.7,1.7,'stripe'),
           B('hand',[x+1.0*side,9.6,0],1.75,'skin',sx=0.9,sy=1.0,sz=0.95),
           B('thumb',[x+0.6*side,10.1,-1.4],0.7,'skin'),
           G('hand_'+n,[x+1.0*side,9.2,0],[])]
        return G('arm_'+('left' if side>0 else 'right'),[x,17.5,0],k)
    body=[B('torso',[0,13.4,0],5.3,'sweater',seg=24,rings=16,sy=1.0,sz=0.9),
          C('stripe',[0,13.0,0],[0,14.6,0],5.32,5.25,'stripe',seg=20,amt=0.02),
          B('hips',[0,9.8,0],4.4,'pants',seg=16,rings=10,sy=0.6,sz=0.85),
          C('neck',[0,17.8,0],[0,19.6,0],2.0,1.9,'skin')]
    hc=[0,24.6,0]; R=6.4
    hk=[B('head',hc,R,'skin',seg=28,rings=20,sy=0.95,sz=0.95,amt=0.012),
        # 머리카락: 뒤·위를 덮는 뭉치 + 앞머리 덩어리 3개
        B('hair',[0,26.6,0.5],6.45,'hair',seg=28,rings=18,sy=0.74,sz=0.98,amt=0.03),
        B('tuft1',[1.8,29.4,-3.6],1.8,'hair'), B('tuft2',[-1.3,29.8,-3.3],2.0,'hair'), B('tuft3',[0.3,30.9,-1.4],1.8,'hair'),
        B('ear_l',[6.1,24.4,0.3],1.3,'skin',sx=0.6,sz=0.9), B('ear_r',[-6.1,24.4,0.3],1.3,'skin',sx=0.6,sz=0.9)]
    on=lambda dx,dy,out=0: _on(hc,R,dx,dy,out,sy=0.95,sz=0.95)
    for nm,dx in (('l',1.9),('r',-1.9)):
        hk+= [B('eye_'+nm,on(dx,0.9,-0.6),1.45,'eye_w',seg=12,rings=8,sz=0.6,amt=0.02),
              B('pupil_'+nm,on(dx*0.92,0.6,0.35),0.6,'eye_k',seg=10,rings=6,sz=0.5,amt=0.0),
              C('brow_'+nm,on(dx-0.8,3.0,0.05),on(dx+0.8,3.2 if dx>0 else 2.8,0.05),0.35,0.35,'brow',seg=8,amt=0.0),
              B('cheek_'+nm,on(dx*1.6,-1.6,0.0),1.0,'cheek',seg=10,rings=6,sz=0.35,amt=0.0)]
    hk.append(B('nose',on(0,-0.6,0.5),1.05,'skin_d',seg=12,rings=8))
    # 웃는 입: 작은 원통 조각을 활 모양으로
    pts=[on(1.6*math.cos(a),-2.6-0.9*math.sin(a),-0.15) for a in [math.pi*(0.15+0.7*i/5) for i in range(6)]]
    for i in range(5): hk.append(C(f'mouth{i}',pts[i],pts[i+1],0.32,0.32,'mouth',seg=8,amt=0.0))
    head=G('head',[0,19.6,0],hk)
    bod=G('body',[0,9.5,0],body+[head,arm(1),arm(-1)])
    return G('root',[0,0,0],[bod,leg(1),leg(-1)])

# ---------------- 점토 강아지 ----------------
def clay_dog(M, tag, s=1.0):
    """점토 강아지: 크림색 몸 + 갈색 얼룩, 처진 귀, 짧은 다리, 초록 목걸이 + 노란 방울, 혀 살짝.  앞 = -z
       묶음: body·head·tail·leg_fl·leg_fr·leg_bl·leg_br"""
    S=lambda p:[x*s for x in p]
    B=lambda n,c,r,col,**k: CB(M,n,S(c),r*s,col,**k)
    C=lambda n,a,b,r0,r1,col,**k: CC(M,n,S(a),S(b),r0*s,r1*s,col,**k)
    G=lambda n,o,ch: M.group(tag+n,S(o),ch)
    legs=[]
    for nm,x,z in (('fl',1.9,-3.4),('fr',-1.9,-3.4),('bl',1.9,3.4),('br',-1.9,3.4)):
        col='dog_p' if nm=='bl' else 'dog'
        legs.append(G('leg_'+nm,[x,5.2,z],[C('leg',[x,5.6,z],[x,1.4,z],1.25,1.15,col),
                                              B('paw',[x,0.95,z-0.35],1.35,'dog',sy=0.6,sz=1.25)]))
    body=[B('torso',[0,7.0,0],4.1,'dog',seg=24,rings=16,sx=0.95,sy=0.9,sz=1.45),
          B('spot1',[1.9,9.4,1.6],2.0,'dog_p',sy=0.45,sz=1.1),   # 등 얼룩
          B('spot2',[-3.0,7.4,2.4],1.4,'dog_p',sx=0.45),
          C('collar',[0,8.9,-4.2],[0,9.8,-5.2],2.55,2.45,'collar',seg=16,amt=0.0),
          B('bell',[0,7.4,-5.6],0.7,'tag',seg=10,rings=6)]
    hc=[0,11.6,-6.4]; R=3.7
    on=lambda dx,dy,out=0: _on(hc,R,dx,dy,out)
    hk=[B('head',hc,R,'dog',seg=24,rings=16,amt=0.02),
        B('muzzle',[0,10.3,-9.4],2.0,'dog',sx=1.15,sy=0.85,sz=1.0),
        B('dnose',[0,11.0,-11.3],0.8,'dnose',sx=1.2,sy=0.85),
        B('tongue',[0.3,9.0,-10.6],0.7,'tongue',sx=0.9,sy=0.5),
        B('eyepatch',on(1.5,0.9,-0.4),1.5,'dog_p',sz=0.4),     # 한쪽 눈가 갈색 얼룩
        B('ear_l',[3.5,10.4,-5.0],1.25,'dog_p',sx=0.45,sy=1.7,sz=0.85),
        B('ear_r',[-3.5,10.4,-5.0],1.25,'dog_p',sx=0.45,sy=1.7,sz=0.85)]
    for nm,dx in (('l',1.4),('r',-1.4)):
        hk+= [B('eye_'+nm,on(dx,0.9,-0.2),0.95,'eye_w',seg=12,rings=8,sz=0.6,amt=0.0),
              B('pupil_'+nm,on(dx*0.9,0.7,0.3),0.48,'eye_k',seg=10,rings=6,sz=0.5,amt=0.0)]
    head=G('head',[0,10.0,-5.0],hk)
    tail=G('tail',[0,8.5,5.6],[C('tail',[0,8.5,5.6],[0,11.6,7.2],0.75,0.55,'dog'), B('tail_tip',[0,11.9,7.35],0.8,'dog_p')])
    bod=G('body',[0,7.0,0],body+[head,tail])
    return G('root',[0,0,0],[bod]+legs)
