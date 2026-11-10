"""《철길 끝 증기 기차 여관의 마지막 손님》 블록 장면 → 연재/증기기차여관/장면/*.bbmodel + 세트정보.json + 숫자.json
   A 사막 종착역(바깥: 오늘·회상·폭풍 밤·출발)  B 객차 안(여관 방)  C 기관실 안  D 협곡 철교(달리기)  E 바닷가 마지막 역(등대·비행선)
   앞 = -z (기관차가 달려가는 쪽).  사람 yaw: 0 = -z 를 봄, 90 = -x, -90 = +x, 180 = +z"""
import sys, os, json, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 증기기구 import *
import 화성_장면 as H
ROOT='/home/user/youtubeshot/연재/증기기차여관'
OUT=f'{ROOT}/장면'; os.makedirs(OUT,exist_ok=True)
TIM=json.load(open(f'{ROOT}/증기기차여관_시간.json',encoding='utf-8')); SEG=TIM['segs']; L=round(TIM['duration']+1,2)
T=lambda i: SEG[i]['t0']
E=lambda i: SEG[i]['t0']+SEG[i]['dur']-0.3
grow,hammer,walk_cycle,P=H.grow,H.hammer,H.walk_cycle,H.P
def vis(A,g,spans):
    """보이는 구간 끝을 0.4초 늘림 (E(i) 는 문단 끝보다 0.3초 앞이라 샷 끝에 사람이 사라지지 않게)"""
    H.vis(A,g,[(a,min(L,b+0.4)) for a,b in spans])
X=lambda x,y=0,z=0:(-x,y,z)     # 움직임 위치 키는 x 가 거꾸로
def mk():
    M=BigModel(512); silla_palette(M); pagoda_palette(M); hwaseong_palette(M); chapssal_palette(M); clock_palette(M); H.world_palette(M); steam_palette(M)
    M.swatch('coal',(35,33,32),6); M.swatch('sheet',(240,238,230),3); M.swatch('blanket',(150,60,50),5); M.swatch('sepia_wall',(120,90,60),5); M.swatch('sign',(230,200,140),4)
    return M
def arms(A,p,keys):
    n=p['name'][:-4]
    for arm in ('arm_left','arm_right'): A.add(find(p,n+arm),'rotation',keys,'catmullrom')
def arm1(A,p,side,keys):
    n=p['name'][:-4]; A.add(find(p,n+('arm_left' if side=='L' else 'arm_right')),'rotation',keys,'catmullrom')
def nod(A,p,t,deg=10):
    n=p['name'][:-4]; A.add(find(p,n+'head'),'rotation',[(t,(0,0,0)),(t+0.4,(deg,0,0)),(t+0.8,(0,0,0)),(t+1.2,(deg,0,0)),(t+1.6,(0,0,0))],'catmullrom')
def shake(A,p,t,deg=18):
    n=p['name'][:-4]; A.add(find(p,n+'head'),'rotation',[(t,(0,0,0)),(t+0.3,(0,deg,0)),(t+0.6,(0,-deg,0)),(t+0.9,(0,deg,0)),(t+1.2,(0,0,0))],'catmullrom')
def look(A,p,t0,t1,r):
    n=p['name'][:-4]; A.add(find(p,n+'head'),'rotation',[(t0,(0,0,0)),(t0+0.5,r),(t1,r),(t1+0.4,(0,0,0))],'catmullrom')
def talk(A,p,t0,t1,amp=-35):
    """말할 때 한 팔을 가볍게 흔듦"""
    n=p['name'][:-4]; pts=[(t0,(0,0,0))]; t=t0+0.4; k=0
    while t<t1: pts.append((t,(amp if k%2==0 else amp*0.4,0,0))); t+=0.6; k+=1
    pts.append((t1+0.3,(0,0,0))); A.add(find(p,n+'arm_right'),'rotation',pts,'catmullrom')
def puffs(M,A,tag,x,y,z,spans,per=1.6,n=4,size=5,rise=34,col='steam2',drift=(0,0,10)):
    """굴뚝·주둥이 김: 작은 상자 n 개가 차례로 올라가며 커지다 사라짐 (spans 동안만)"""
    gs=[]
    for i in range(n):
        g=M.group(f'{tag}{i}',[x,y,z],[M.cube('puff',[x-size/2,y,z-size/2],[x+size/2,y+size,z+size/2],col)])
        pk=[(0,(0,0,0))]; sk=[(0,(0,0,0))]
        for a,b in spans:
            t=a+i*per/n
            while t+per<=b:
                pk+= [(t,(0,0,0)),(t+per-0.02,X(drift[0],rise,drift[2]))]
                sk+= [(t-0.02 if t-0.02>a else t,(0,0,0)),(t+0.01,(0.5,0.5,0.5)),(t+per*0.7,(1.5,1.5,1.5)),(t+per-0.02,(0,0,0))]
                t+=per
        A.add(g,'position',pk); A.add(g,'scale',sk); gs.append(g)
    return gs
def spin_x(A,g,t0,t1,deg_per_s,t_stop=None):
    n=max(2,int((t1-t0)*3)); pts=[(0,(0,0,0)),(t0,(0,0,0))]
    for k in range(1,n+1): t=t0+(t1-t0)*k/n; pts.append((t,(deg_per_s*(t-t0),0,0)))
    A.add(g,'rotation',pts)
def wheels(A,root_tag,t0,t1,dps):
    pass
def train_wheels(A,tr,tag,t0,t1,dps):
    for i in range(3):
        for s in 'LR': spin_x(A,find(tr,f'{tag}loco_w{i}{s}'),t0,t1,dps)
def walker_walk(A,wc,tag,t0,t1,per=1.2,amp=22,sink=None):
    """걷는 증기차 다리: 대각선 다리 짝(0·3 / 1·2)이 번갈아 앞뒤로 + 무릎 굽힘 + 몸통 위아래.  sink=(t,깊이): 모래에 빠져 버둥"""
    for i in range(4):
        ph=0 if i in (0,3) else 1
        hk=[(max(0,t0-0.02),(0,0,0))]; kk=[(max(0,t0-0.02),(0,0,0))]; t=t0; k=ph
        while t<t1:
            a=amp*(1 if k%2==0 else -1); hk.append((t,(a,0,0))); kk.append((t,(0 if k%2==0 else 28,0,0))); t+=per/2; k+=1
        hk.append((t1+0.2,(0,0,0))); kk.append((t1+0.2,(0,0,0)))
        A.add(find(wc,f'{tag}leg{i}'),'rotation',hk,'catmullrom'); A.add(find(wc,f'{tag}leg{i}_knee'),'rotation',kk,'catmullrom')
    bk=[(max(0,t0-0.02),(0,0,0))]; t=t0; k=0
    while t<t1: bk.append((t,(0,2.5 if k%2 else 0,0))); t+=per/4; k+=1
    bk.append((t1+0.2,(0,0,0))); A.add(find(wc,f'{tag}body'),'position',bk,'catmullrom')
    A.add(find(wc,f'{tag}gear'),'rotation',[(0,(0,0,0)),(t0,(0,0,0)),(t1,(-(t1-t0)*120,0,0))])
def gauge(M,tag,x,y,z,r=4,face=1):
    f=face
    k=[M.cube('gg_rim',[x-r,y-r,z-1],[x+r,y+r,z+1],'brass2'), M.cube('gg_face',[x-r+1,y-r+1,min(z+1.3*f,z+1*f)],[x+r-1,y+r-1,max(z+1.3*f,z+1*f)],'plaque'),
       M.cube('gg_ndl',[x-0.4,y,min(z+1.5*f,z+1.3*f)],[x+0.4,y+r-1.5,max(z+1.5*f,z+1.3*f)],'ink')]
    return M.group(tag,[x,y,z],k)
def storm(M,A,tag,cx,cz,spans,w=700):
    """모래 폭풍: 모래 알갱이 상자들이 옆으로 휙휙 날아감"""
    rnd=random.Random(5); out=[]
    for i in range(36):
        x=cx-w/2+rnd.random()*w*0.3; y=rnd.random()*120+5; z=cz-w/2+rnd.random()*w
        g=M.group(f'{tag}{i}',[x,y,z],[M.cube('sand_p',[x,y,z],[x+rnd.choice((6,10,16)),y+2,z+2],'sand')])
        per=1.0+rnd.random()*0.8; pk=[(0,(0,0,0))]
        for a,b in spans:
            t=a+rnd.random()*per
            while t+per<=b: pk+= [(t,(0,0,0)),(t+per-0.02,X(w*0.9,-10,40))]; t+=per
        A.add(g,'position',pk); vis(A,g,spans); out.append(g)
    return out

def flip_yaw(A):
    """움직임 화면의 y 회전은 부호가 반대 → 이 파일의 약속(yaw 90 = -x 를 봄)에 맞게 모든 회전 키의 y 를 뒤집음"""
    for uid,(nm,lst) in A.tr.items():
        for k in lst:
            if k['channel']=='rotation':
                dp=k['data_points'][0]; dp['y']=str(round(-float(dp['y']),3))
def widen(M,A,top,K):
    """세트를 x·z 로 K 배 넓힘: 사람·로봇(…root)은 자리만 옮기고 크기는 그대로, 나머지는 x·z 크기까지 늘림. 위치 키도 K 배"""
    byid={e['uuid']:e for e in M.els}
    def sc(n):
        n['origin']=[n['origin'][0]*K,n['origin'][1],n['origin'][2]*K]
        for c in n['children']:
            if isinstance(c,dict): sc(c)
            else:
                e=byid[c]; e['from']=[e['from'][0]*K,e['from'][1],e['from'][2]*K]; e['to']=[e['to'][0]*K,e['to'][1],e['to'][2]*K]
                if 'origin' in e: e['origin']=[e['origin'][0]*K,e['origin'][1],e['origin'][2]*K]
    for g in top:
        if isinstance(g,dict):
            if g['name'].endswith('root'): move(M,g,g['origin'][0]*(K-1),0,g['origin'][2]*(K-1))
            else: sc(g)
        else:
            e=byid[g]; e['from']=[e['from'][0]*K,e['from'][1],e['from'][2]*K]; e['to']=[e['to'][0]*K,e['to'][1],e['to'][2]*K]
            if 'origin' in e: e['origin']=[e['origin'][0]*K,e['origin'][1],e['origin'][2]*K]
    for uid,(nm,lst) in A.tr.items():
        for k in lst:
            if k['channel']=='position':
                dp=k['data_points'][0]; dp['x']=str(round(float(dp['x'])*K,3)); dp['z']=str(round(float(dp['z'])*K,3))

def numbers(): return [{'seg':83,'text':'압력계 테두리에 새겨진 이름 · 마리'}]

# =====================================================================
#  A : 사막 종착역 (바깥).  기관차 앞 z -62, 객차 끝 z 347, 멈춤 막이 z 360.  사건은 모두 -x 쪽(객차 문 쪽)
# =====================================================================
def set_A():
    M=mk(); A=Anim(L); top=[H.far_ground(M,'sand_d')]+desert(M,-1200,1200,-2600,1000,tile=200)
    top+= [mesa(M,'mesa1',-900,-900,320,180,260), mesa(M,'mesa2',800,-1400,260,150,240), mesa(M,'mesa3',-700,700,240,120,200), mesa(M,'mesa4',900,500,300,160,220)]
    top.append(track(M,'track',0,-2600,370))
    top.append(M.group('buffer',[0,0,365],[M.cube('buf',[-18,0,358],[18,22,372],'lacquer'),M.cube('buf_b',[-14,12,354],[-8,18,358],'loco_d'),M.cube('buf_b2',[8,12,354],[14,18,358],'loco_d')]))
    # 회상 때만 보이는 나무 역 간판 / 오늘 보이는 낡은 표지
    tr,lo=inn_train(M,'tr_',0,0); top.append(tr)
    # 출발 (71~75): 천천히 → 쇠 기둥을 밀어내고 → 빠르게 멀어짐
    A.add(tr,'position',[(0,(0,0,0)),(T(71)+0.5,(0,0,0)),(T(72)+1.2,(0,0,-110)),(E(73),(0,0,-420)),(E(75),(0,0,-1900)),(T(86)-0.06,(0,0,-1900)),(T(86)-0.04,(0,0,0)),(L,(0,0,0))])
    train_wheels(A,tr,'tr_',T(71)+0.5,E(75),-260)
    top+= puffs(M,A,'stk',0,72,-45,[(0,T(30)),(T(55),E(75))],per=2.4,n=4,size=6)
    top+= puffs(M,A,'stkF',0,72,-45,[(T(71),E(75))],per=0.8,n=5,size=8,drift=(0,0,40))
    for i,zc in enumerate((110,206,302)): puffs(M,A,f'cc{i}',9,72,zc-22,[(0,L)],per=3.0,n=2,size=4)
    # 회상(17~19, 22~27, 86~89): 마리·젊은 오웬, 손님들
    FL=[(T(17),E(19)),(T(22),E(27)),(T(86),E(89))]
    mari=P(M,'mr_','mari',-26,30,yaw=90); top.append(mari); vis(A,mari,[(T(17),T(19)),(T(22),T(25)),(T(27),T(28))])
    A.add(mari,'position',[(0,(0,0,0))]); arm1(A,mari,'L',[(T(22),(0,0,0)),(T(22)+0.4,(-150,0,0)),(E(22),(-150,0,0)),(E(22)+0.3,(0,0,0))])
    talk(A,mari,T(24),E(24)); talk(A,mari,T(27),E(27))
    ow0=P(M,'oy_','owen_y',-40,60,yaw=90); top.append(ow0); vis(A,ow0,[(T(17),E(17)),(T(23),E(23))])
    look(A,ow0,T(17),E(17),(0,-30,0))
    # 25 손님 맞이: 젊은 오웬·마리 문 앞, 여행자 둘이 걸어옴
    mr2=P(M,'mr2_','mari',-30,128,yaw=90); oy2=P(M,'oy2_','owen_y',-30,166,yaw=90); top+= [mr2,oy2]
    for g in (mr2,oy2): vis(A,g,[(T(25),E(26))])
    arms(A,oy2,[(T(25)+1,(0,0,0)),(T(25)+1.5,(-70,0,0)),(E(25),(-70,0,0)),(E(25)+0.3,(0,0,0))])
    for j,(kind,dz) in enumerate([('trav',140),('man2',156)]):
        g=P(M,f'tv{j}_','trav' if j==0 else 'worker',-260,dz,yaw=-90); top.append(g); vis(A,g,[(T(25),E(26))])
        A.add(g,'position',[(0,X(0)),(T(25),X(0)),(E(25),X(190)),(E(26),X(205))]); walk_cycle(A,g,T(25),E(25),amp=24,period=0.9)
    top+= storm(M,A,'stA',-150,150,[(T(26),E(26)),(T(30),E(34)),(T(86),E(89))],w=600)
    # 86~89 회상: 폭풍 밤, 아기를 안은 여행자 · 마리가 압력계를 건넴
    tv3=P(M,'tv3_','trav',-48,146,yaw=-90); mr3=P(M,'mr3_','mari',-26,146,yaw=90); top+= [tv3,mr3]
    for g in (tv3,mr3): vis(A,g,[(T(86),E(89))])
    baby=M.group('baby',[-41,17,146],[M.cube('bb',[-44,15,142],[-38,20,150],'sheet'),M.cube('bbf',[-44.3,17,148],[-40,20,150],'skin')]); top.append(baby); vis(A,baby,[(T(86),E(89))])
    arms(A,tv3,[(T(86),(-55,0,0)),(E(89),(-55,0,0))])
    g3=gauge(M,'gauge3',-36,18,146,r=2,face=-1); top.append(g3); vis(A,g3,[(T(88)+1.5,E(89))])
    arm1(A,mr3,'R',[(T(88),(0,0,0)),(T(88)+1,(-60,0,0)),(E(89),(-60,0,0))])
    # ---- 오늘 ----
    ow=P(M,'ow_','owen',-30,150,yaw=90); top.append(ow); vis(A,ow,[(0,T(4)-0.05)])                # 1~3 멀리 문 앞
    tok_A=tok(M,'tkA_',-34,0,170,s=0.9); top.append(tok_A); vis(A,tok_A,[(0,T(4)-0.05)]); A.add(tok_A,'rotation',[(0,(0,90,0))])
    # 걷는 증기차 (11~): -x 멀리서 걸어와 z -60 에 멈춤 (앞이 +x 를 봄)
    wc=walking_car(M,'wc_',-110,-70); top.append(wc); A.add(wc,'rotation',[(0,(0,-90,0)),(E(72),(0,-90,0)),(E(72)+1.0,(0,0,0)),(L,(0,0,0))],'catmullrom')
    A.add(wc,'position',[(0,X(-700)),(T(11),X(-700)),(E(11)-0.6,X(0)),(T(73)+1.5,X(0)),(T(74),(0,0,-140)),(T(74)+1.2,(0,-18,-170)),(L,(0,-18,-170))],'catmullrom')
    walker_walk(A,wc,'wc_',T(11),E(11)-0.6,per=1.3); vis(A,wc,[(T(11)-0.2,E(16)),(T(58)-0.2,T(76))])
    walker_walk(A,wc,'wc_',T(73)+1.5,E(75),per=0.8,amp=30)
    # 74 모래에 빠져 비틀: 몸통 좌우로 흔들
    A.add(find(wc,'wc_body'),'rotation',[(0,(0,0,0)),(T(74)+1.2,(0,0,0)),(T(74)+1.8,(0,0,10)),(T(74)+2.6,(0,0,-8)),(T(74)+3.4,(0,0,9)),(T(74)+4.2,(0,0,-6)),(E(75),(0,0,4))],'catmullrom')
    top+= puffs(M,A,'wcs',-116,109,-70,[(T(11),E(11)),(T(58),E(60)),(T(73),E(75))],per=1.2,n=4,size=5)
    top+= storm(M,A,'dust',-110,-200,[(T(74),E(75))],w=260)
    gr=P(M,'gr_','grimes',-90,-30,yaw=-90); top.append(gr); vis(A,gr,[(T(12),E(12))])
    A.add(gr,'position',[(0,X(0)),(T(12),X(0)),(E(12)-1,X(40))]); walk_cycle(A,gr,T(12),E(12)-1,amp=20,period=1.0)
    # 58~66: 그림스·인부 셋, 쇠 기둥 둘
    gr2=P(M,'gr2_','grimes',-80,-20,yaw=-90); top.append(gr2); vis(A,gr2,[(T(58),E(60)),(T(64),T(73)+1.4)])
    talk(A,gr2,T(60),E(60),amp=-60)
    A.add(find(gr2,'gr2_head'),'rotation',[(0,(0,0,0)),(T(65),(0,0,0)),(T(65)+0.3,(-12,0,0)),(E(66),(-12,0,0))])
    A.add(gr2,'position',[(0,X(0)),(T(73),X(0)),(T(73)+1.3,X(-25,0,-25))]); walk_cycle(A,gr2,T(73),T(73)+1.3,amp=26,period=0.6)
    posts=[iron_post(M,f'post{i}',x,z) for i,(x,z) in enumerate([(-8,-150),(8,-190)])]
    for i,p in enumerate(posts):
        top.append(p); A.add(p,'scale',[(0,(0,0,0)),(T(59)+1.5+i*0.6,(0,0,0)),(T(59)+1.52+i*0.6,(1,0.1,1)),(T(59)+3+i*0.6,(1,1,1))])
        tf=T(72)+0.9+i*0.6
        A.add(p,'rotation',[(0,(0,0,0)),(tf,(0,0,0)),(tf+0.6,(-82,0,15*(1 if i else -1)))],'catmullrom')
        A.add(p,'position',[(0,(0,0,0)),(tf,(0,0,0)),(tf+0.6,X(-30 if i==0 else 30,0,-10))])
    for j,(x,z) in enumerate([(-30,-150),(30,-190),(-34,-210)]):
        w=P(M,f'wk{j}_','worker',x,z,yaw=-90 if x<0 else 90); top.append(w); vis(A,w,[(T(58),E(66))])
        if j<2: hammer(A,w,T(59)+0.3,E(59))
    ow2=P(M,'ow2_','owen',-32,120,yaw=90); top.append(ow2); vis(A,ow2,[(T(58),E(66))]); talk(A,ow2,T(63),E(63))
    lookB=lambda g,t0,t1: look(A,g,t0,t1,(0,-35,0))
    lookB(ow2,T(62),E(62))
    ln=P(M,'ln_','lena',-24,44,yaw=90); top.append(ln); vis(A,ln,[(T(61),E(66))]); A.add(find(ln,'ln_body'),'rotation',[(0,(0,0,10))]); talk(A,ln,T(62),E(62)); talk(A,ln,T(64),E(64))
    # 75 먼지 뒤집어쓴 그림스 (증기차 옆에 서서 멀어지는 기차를 봄)
    gr3=P(M,'gr3_','grimes',-200,-230,yaw=0); top.append(gr3); vis(A,gr3,[(T(75),T(76))])
    # 30~34 폭풍 밤: 레나가 문을 두드림, 오웬이 문을 엶
    ln0=P(M,'ln0_','lena',-34,146,yaw=-90); top.append(ln0); vis(A,ln0,[(T(31),E(34))])
    arm1(A,ln0,'R',[(T(31),(0,0,0)),(T(31)+0.3,(-100,0,0)),(T(31)+0.6,(-70,0,0)),(T(31)+0.9,(-100,0,0)),(T(31)+1.2,(-70,0,0)),(T(31)+1.6,(0,0,0))],)
    bag=M.group('bag',[-40,10,146],[M.cube('bag',[-42,6,140],[-38,13,145],'leather')]); top.append(bag); vis(A,bag,[(T(31),E(34))])
    ow3=P(M,'ow3_','owen',-18,146,yaw=90); top.append(ow3); vis(A,ow3,[(T(32)+0.8,E(34))])
    door=find(tr,'tr_car0');
    A.bake(top); flip_yaw(A); M.save(f'{OUT}/A_종착역.bbmodel',top,[A.json()],name='A'); return {}

# =====================================================================
#  B : 객차 안 (여관 방).  방 x -60~60 · z -120~120, 뒷벽 x 60 (창), 카메라는 -x 쪽(벽 없음)
# =====================================================================
def room(M, night=False):
    k=[M.cube('fl',[-70,-4,-130],[70,0,130],'timber_d'), M.cube('wall_b',[60,0,-130],[66,80,130],'car_g'), M.cube('wall_n',[-70,0,-136],[66,80,-130],'car_g'),
       M.cube('wall_s',[-70,0,130],[66,80,136],'car_g'), M.cube('ceil',[-70,80,-136],[66,84,136],'car_gd'),
       M.cube('trim',[59.5,34,-130],[60,36,130],'brass2'), M.cube('wains',[59.4,0,-130],[60,34,130],'timber')]
    for zz in (-90,-10,70):
        k+= [M.cube('win',[59.2,42,zz-14],[59.8,64,zz+14],'window_dk' if night else 'window_lit'), M.cube('winf',[58.8,41,zz-15],[59.2,65,zz-13],'brass2'), M.cube('winf',[58.8,41,zz+13],[59.2,65,zz+15],'brass2'),
              M.cube('winf',[58.8,52,zz-14],[59.2,53,zz+14],'brass2')]
    return k
def set_B():
    M=mk(); A=Anim(L); top=[]
    day=M.group('room_day',[0,0,0],room(M,False)); night=M.group('room_night',[0,0,0],room(M,True)); top+= [day,night]
    NIGHTS=[(T(21),E(28)),(T(31),E(41))]
    vis(A,night,NIGHTS); vis(A,day,[(0,T(21)-0.05),(E(28)+0.05,T(31)-0.05),(E(41)+0.05,L)])
    # 침대 둘 (뒷벽 쪽 북쪽)
    for i,zz in enumerate((-110,-60)):
        top.append(M.group(f'bed{i}',[45,0,zz+20],[M.cube('bedf',[30,0,zz],[58,10,zz+38],'timber_d'),M.cube('matt',[31,10,zz+1],[57,14,zz+37],'sheet'),
                   M.cube('blk',[31,14,zz+12],[57,15,zz+37],'blanket'),M.cube('pil',[46,14,zz+2],[56,17,zz+10],'sheet'),M.cube('head',[56,0,zz],[58,26,zz+38],'timber')]))
    # 침대보 펴기(5): 흰 천이 접혔다 펴짐
    cloth=M.group('cloth',[44,15,-60],[M.cube('clo',[31,15,-73],[57,15.6,-48],'sheet')]); top.append(cloth)
    A.add(cloth,'scale',[(0,(1,1,1)),(T(5)-0.02,(1,1,1)),(T(5),(0.3,1,1)),(E(5)-0.5,(1,1,1))],'catmullrom')
    # 계산대·찻잔 (남쪽)
    top+= [M.cube('cnt',[-10,0,70],[30,26,84],'timber_d'), M.cube('cnt_t',[-12,26,68],[32,28,86],'brass2')]
    for j in range(3): top.append(M.cube('cup',[-4+j*8,28,74],[0+j*8,32,78],'sheet'))
    # 난로 + 찻주전자 (남동 구석)
    top+= [M.cube('stove',[36,0,96],[56,22,118],'loco_d'), M.cube('stove_d',[35.6,4,100],[36,14,112],'glow'), M.cube('stpipe',[44,22,104],[48,80,108],'loco_d')]
    top+= [M.cube('kettle',[38,22,98],[46,30,106],'copper2'), M.cube('ket_sp',[35,26,101],[38,28,103],'copper2')]
    top+= puffs(M,A,'ket',36,28,102,[(T(35),E(35)),(T(8),E(8))],per=1.0,n=4,size=4,rise=20)
    # 식탁 + 의자 (가운데)
    top+= [M.cube('tbl',[-6,18,-12],[26,20,22],'timber'), M.cube('tbl_l',[8,0,3],[12,18,7],'timber_d'),
           M.cube('ch1',[-22,0,-2],[-10,10,12],'timber_d'), M.cube('ch1b',[-22,10,-2],[-20,26,12],'timber_d'), M.cube('ch2',[30,0,-2],[42,10,12],'timber_d'), M.cube('ch2b',[40,10,-2],[42,26,12],'timber_d')]
    top+= [M.cube('lamp',[8,64,3],[12,80,7],'brass2'), M.cube('lampb',[4,58,-1],[16,64,11],'lamp')]
    # 사진 액자 (뒷벽): 마리
    top+= [M.cube('frame',[58.6,22,96],[59.4,34,112],'brass2'), M.cube('photo',[58.3,23,97],[58.6,33,111],'sepia_wall'), M.cube('ph_p',[58.2,24,102],[58.3,31,106],'mari_coat')]
    soup=M.group('soup',[10,20,5],[M.cube('bowl',[6,20,1],[14,23,9],'sheet'),M.cube('soupc',[7,23,2],[13,23.3,8],'copper2')]); top.append(soup); vis(A,soup,[(T(36)+1.6,E(38))])
    top+= puffs(M,A,'soupst',10,23,5,[(T(36)+1.6,E(38))],per=1.2,n=3,size=3,rise=14)
    album=M.group('album',[10,20,5],[M.cube('alb_l',[2,20,-3],[10,21.5,12],'book'),M.cube('alb_r',[10,20,-3],[18,21.5,12],'book'),M.cube('alb_p',[3,21.5,-2],[17,21.8,11],'page'),
                 M.cube('alb_ph',[11,21.8,0],[16,22,6],'sepia_wall'),M.cube('alb_ph2',[12.5,22,1.5],[14.5,22.1,4.5],'mari_coat')]); top.append(album); vis(A,album,[(T(21)+1,E(28))])
    paper=M.group('paper',[10,28,77],[M.cube('ppr',[5,28.2,73],[15,28.5,81],'sheet'),M.cube('ppr_i',[6,28.5,74],[14,28.6,75],'ink'),M.cube('ppr_i2',[6,28.5,77],[12,28.6,78],'ink')]); top.append(paper)
    vis(A,paper,[(T(14)+1.0,E(16))]); A.add(paper,'position',[(0,(0,0,0)),(T(14)+1.0,(0,18,-12)),(T(14)+1.5,(0,0,0))])
    gauge_b=gauge(M,'gaugeB',14,21.5,6,r=3,face=-1); top.append(gauge_b); vis(A,gauge_b,[(T(39)+2,E(41))]); A.add(gauge_b,'rotation',[(0,(-90,0,0))])
    # ---- 사람 ----
    # 4~5 오웬 침대보, 7 오웬 창밖, 9 창밖 끊긴 철길
    ow=P(M,'owB_','owen',24,-60,yaw=-90); top.append(ow); vis(A,ow,[(T(4),E(5))])
    arms(A,ow,[(T(5),(0,0,0)),(T(5)+0.5,(-65,0,0)),(E(5)-0.5,(-65,0,0)),(E(5),(-20,0,0))])
    ow1=P(M,'owB1_','owen',44,-10,yaw=-90); top.append(ow1); vis(A,ow1,[(T(7),E(7)),(T(9),E(9))])
    # 6·8 톡 계산대 위 찻잔 닦기
    tk=tok(M,'tkB_',10,28,78,s=0.9); top.append(tk); vis(A,tk,[(T(6),E(8)),(T(35),E(35))])
    tp=[(T(6),(0,0,0))]; t=T(6)
    while t<E(8): tp+= [(t+0.3,(-60,0,20)),(t+0.6,(-60,0,-10))]; t+=0.6
    A.add(find(tk,'tkB_arm_l'),'rotation',tp,'catmullrom'); A.add(find(tk,'tkB_arm_r'),'rotation',[(T(6),(-50,0,0)),(E(8),(-50,0,0))])
    cupT=M.group('cupT',[12,36,73],[M.cube('cupt',[11,34,71],[15,38,75],'sheet')]); top.append(cupT); vis(A,cupT,[(T(6),E(8))])
    A.add(find(tk,'tkB_root'),'position',[(0,(0,0,0)),(T(8),(0,0,0)),(T(8)+0.3,(0,3,0)),(T(8)+0.6,(0,0,0))])
    A.add(tk,'position',[(0,(0,0,0)),(T(35),(0,0,0)),(T(35)+0.4,(0,4,0)),(T(35)+0.8,(0,0,0)),(T(35)+1.2,(0,4,0)),(T(35)+1.6,(0,0,0)),(T(35)+2.0,(0,4,0)),(T(35)+2.4,(0,0,0))])
    # 13~16 그림스(문 쪽에서) ↔ 오웬 (계산대 안쪽)
    gr=P(M,'grB_','grimes',10,50,yaw=180); top.append(gr); vis(A,gr,[(T(13),E(16))])
    talk(A,gr,T(13),E(13),amp=-50); talk(A,gr,T(15),E(15),amp=-50)
    arm1(A,gr,'R',[(T(14),(0,0,0)),(T(14)+0.5,(-80,0,0)),(T(14)+1.0,(-40,0,0)),(T(14)+1.4,(0,0,0))])
    ow2=P(M,'owB2_','owen',10,100,yaw=0); top.append(ow2); vis(A,ow2,[(T(13),E(16))])
    tr=[(T(16),(-30,0,0))]+[(T(16)+0.15*k,(-30+(4 if k%2 else -4),0,0)) for k in range(1,14)]
    A.add(find(ow2,'owB2_arm_left'),'rotation',[(0,(0,0,0)),(T(16)-0.3,(0,0,0))]+tr+[(E(16)+0.2,(0,0,0))])
    # 21~28 밤, 사진첩 (식탁에 앉음)
    ow3=P(M,'owB3_','owen',-16,5,yaw=-90,y=-2); top.append(ow3); vis(A,ow3,[(T(21),E(28))])
    for leg in ('leg_left','leg_right'): A.add(find(ow3,'owB3_'+leg),'rotation',[(0,(-90,0,0))])
    A.add(find(ow3,'owB3_body'),'position',[(0,(0,-2,0))]); arms(A,ow3,[(T(21),(-55,0,0)),(E(28),(-55,0,0))])
    A.add(find(ow3,'owB3_head'),'rotation',[(0,(25,0,0)),(T(28),(25,0,0)),(T(28)+1,(0,-50,0)),(E(28),(0,-50,0))],'catmullrom')
    # 31~41 폭풍 밤, 레나는 식탁에 앉고 오웬이 수프를 내옴
    ln=P(M,'lnB_','lena',-16,5,yaw=-90,y=-2); top.append(ln); vis(A,ln,[(T(36),E(41))])
    for leg in ('leg_left','leg_right'): A.add(find(ln,'lnB_'+leg),'rotation',[(0,(-90,0,0))])
    arms(A,ln,[(T(36),(-45,0,0)),(T(38),(-45,0,0)),(T(38)+0.5,(-80,0,0)),(T(38)+1.0,(-45,0,0)),(T(39),(-45,0,0)),(T(39)+1,(-70,0,0)),(E(41),(-70,0,0))])
    A.add(find(ln,'lnB_head'),'rotation',[(0,(0,0,0)),(T(38)+1.2,(0,0,0)),(T(38)+1.6,(-12,0,0)),(E(38),(-12,0,0)),(E(38)+0.4,(0,0,0))])
    talk(A,ln,T(40),E(40),amp=-75)
    ow4=P(M,'owB4_','owen',40,5,yaw=90); top.append(ow4); vis(A,ow4,[(T(36),E(41))])
    A.add(ow4,'position',[(0,X(0,0,40)),(T(36),X(0,0,40)),(T(36)+1.4,X(-8))]); walk_cycle(A,ow4,T(36),T(36)+1.4,amp=20,period=0.7)
    arms(A,ow4,[(T(36),(-60,0,0)),(T(36)+1.6,(-60,0,0)),(T(36)+2.0,(0,0,0))]); talk(A,ow4,T(37),E(37)); shake(A,ow4,T(41)+0.3)
    A.bake(top); flip_yaw(A); M.save(f'{OUT}/B_객실.bbmodel',top,[A.json()],name='B'); return {}

# =====================================================================
#  C : 기관실 안.  바닥 x -40~40 · z -40~40, 앞(-z) = 보일러 뒷면(화실 문·계기판), 뒤(+z) = 석탄 통, 왼쪽(-x) = 문, 창 x ±40
# =====================================================================
def set_C():
    M=mk(); A=Anim(L); top=[M.cube('cfl',[-44,-4,-44],[44,0,50],'loco_d'), M.cube('cfl2',[-40,0,-40],[40,0.4,46],'timber_d')]
    top+= [M.cube('boil_back',[-40,0,-48],[40,70,-40],'loco'), M.cube('boil_rim',[-26,8,-40.6],[26,62,-40],'loco_d'),
           M.cube('fire_door',[-12,8,-41.2],[12,26,-40.4],'loco_d'), M.cube('fire_h',[-2,16,-42.4],[8,18,-41.2],'brass2')]
    glow=M.group('glow',[0,17,-40],[M.cube('glowi',[-10,10,-40.3],[10,24,-40.0],'glow')]); top.append(glow)
    vis(A,glow,[(T(55)+1.0,E(56)),(T(68),E(70)),(T(77),E(79)),(T(82),E(90))])
    for j,gx in enumerate((-20,-7,7,20)): top.append(gauge(M,f'gC{j}',gx,48,-40.2,r=5))
    top+= [M.cube('pipeC',[-38,30,-40],[-34,70,-36],'copper2'), M.cube('pipeC2',[-38,64,-36],[38,68,-32],'copper2'), M.cube('pipeC3',[34,20,-40],[38,64,-36],'copper2'),
           M.cube('valve',[-40,40,-38],[-32,46,-34],'lacquer'), M.cube('valve2',[32,36,-38],[40,42,-34],'lacquer')]
    lever=M.group('lever',[26,6,-30],[M.cube('lev_b',[24,0,-34],[30,8,-26],'loco_d'),M.cube('lev',[26,8,-31],[28,38,-29],'brass2'),M.cube('lev_h',[24,36,-32],[30,40,-28],'lacquer')]); top.append(lever)
    A.add(lever,'rotation',[(0,(-25,0,0)),(T(70),(-25,0,0)),(T(70)+1.0,(35,0,0)),(L,(35,0,0))],'catmullrom')
    top+= [M.cube('coal_bin',[-30,0,32],[30,20,48],'loco_d'), M.cube('coal',[-28,20,34],[28,26,46],'coal')]
    for zz,xx in ((-36,40),(-36,-44)): pass
    top+= [M.cube('roofC',[-46,74,-48],[46,78,50],'loco_d'), M.cube('cwall_r',[40,0,-40],[44,74,46],'car_gd'), M.cube('cwall_l1',[-44,0,-40],[-40,74,-10],'car_gd'), M.cube('cwall_l2',[-44,0,24],[-40,74,46],'car_gd'),
           M.cube('cwall_l3',[-44,60,-10],[-40,74,24],'car_gd')]
    wday=M.group('winC_day',[0,0,0],[M.cube('wr',[39.6,36,-30],[40,58,10],'window_lit'),M.cube('wl',[-40,36,-36],[-39.6,56,-14],'window_lit')])
    wnight=M.group('winC_night',[0,0,0],[M.cube('wr',[39.6,36,-30],[40,58,10],'window_dk'),M.cube('wl',[-40,36,-36],[-39.6,56,-14],'window_dk')]); top+= [wday,wnight]
    vis(A,wnight,[(T(81),L)]); vis(A,wday,[(0,T(81)-0.05)])
    # 압력계 (큰 것): 82~84 오웬이 들여다봄 — 계기판 앞 작은 선반
    big=gauge(M,'gBig',0,40,-36,r=7); top.append(big); vis(A,big,[(T(52),L)])
    shelf=M.cube('shelf',[-10,30,-40],[10,32,-32],'timber_d'); top.append(shelf)
    name=M.group('name',[0,33.4,-37],[M.cube('nm1',[-3,32.6,-37.4],[-1,33.2,-37.2],'ink'),M.cube('nm2',[0,32.6,-37.4],[3,33.2,-37.2],'ink')]); top.append(name); vis(A,name,[(T(52),L)])
    # 김 (56·77 기관이 울 때, 관 사이로)
    top+= puffs(M,A,'stC',-36,64,-34,[(T(56),E(56)),(T(71),E(71)),(T(77),E(77))],per=0.9,n=4,size=5,rise=16,drift=(20,0,10))
    # ---- 사람 ----
    # 44~52 레나 수리 (보일러 앞, 쪼그려 망치질 / 관 조이기)
    ln=P(M,'lnC_','lena',-6,-26,yaw=0); top.append(ln); vis(A,ln,[(T(44),E(54))])
    hammer(A,ln,T(44),E(44),per=0.5); talk(A,ln,T(46),E(46)); hammer(A,ln,T(47),E(47),per=0.8)
    A.add(find(ln,'lnC_head'),'rotation',[(0,(0,0,0)),(T(51),(0,0,0)),(T(51)+0.4,(0,140,0)),(E(51),(0,140,0)),(E(51)+0.4,(0,0,0))],'catmullrom')
    arm1(A,ln,'L',[(T(51),(0,0,0)),(T(51)+0.4,(-150,0,20)),(T(51)+1.2,(-150,0,-20)),(T(51)+1.6,(0,0,0))])
    arms(A,ln,[(T(52),(0,0,0)),(T(52)+0.5,(-95,0,0)),(E(52),(-95,0,0)),(E(52)+0.3,(0,0,0))])
    tkC=tok(M,'tkC_',14,0,-22,s=0.9); top.append(tkC); vis(A,tkC,[(T(48),E(48)),(T(55),E(56))]); A.add(tkC,'rotation',[(0,(0,90,0))])
    A.add(find(tkC,'tkC_arm_r'),'rotation',[(T(48),(0,0,0)),(T(48)+0.4,(-90,0,0)),(E(48),(-90,0,0))])
    top+= puffs(M,A,'tkCp',16,20,-22,[(T(48),E(48))],per=0.8,n=3,size=3,rise=12)
    # 49~50 오웬 문간 (왼쪽 문 x -40, z 0~24)
    ow=P(M,'owC_','owen',-46,8,yaw=-90); top.append(ow); vis(A,ow,[(T(49),E(50))]); talk(A,ow,T(50),E(50))
    # 53~54 오웬이 들어와 관을 가리킴
    ow2=P(M,'owC2_','owen',-46,8,yaw=-90); top.append(ow2); vis(A,ow2,[(T(53),E(56))])
    A.add(ow2,'position',[(0,X(0)),(T(53)+1,X(0)),(E(53),X(30,0,-14))]); walk_cycle(A,ow2,T(53)+1,E(53),amp=22,period=0.8)
    A.add(ow2,'rotation',[(0,(0,-90,0)),(E(53)-0.5,(0,-90,0)),(E(53),(0,-30,0))])
    arm1(A,ow2,'R',[(T(54),(0,0,0)),(T(54)+0.4,(-110,0,0)),(E(54),(-110,0,0)),(E(54)+0.3,(0,0,0))])
    ln2=P(M,'lnC2_','lena',-6,-26,yaw=0); top.append(ln2); vis(A,ln2,[(T(55),E(56))]); look(A,ln2,T(56),E(56),(-10,0,0))
    # 68~70 출발: 오웬 외침, 톡 석탄 삽질, 레나 손잡이
    ow3=P(M,'owC3_','owen',-20,10,yaw=0); top.append(ow3); vis(A,ow3,[(T(68),E(70)),(T(77),E(79))])
    arm1(A,ow3,'R',[(T(68),(0,0,0)),(T(68)+0.3,(-140,0,0)),(E(68),(-140,0,0)),(E(68)+0.3,(0,0,0))])
    A.add(find(ow3,'owC3_head'),'rotation',[(0,(0,0,0)),(T(79),(0,0,0)),(T(79)+0.4,(0,-70,0)),(E(79),(0,-70,0))],'catmullrom')
    tk3=tok(M,'tkC3_',0,0,30,s=0.9); top.append(tk3); vis(A,tk3,[(T(69),E(70))])
    A.add(tk3,'position',[(0,(0,0,0)),(T(69),(0,0,0)),(T(69)+1.5,(0,0,-44))]); A.add(tk3,'rotation',[(0,(0,180,0)),(T(69)+1.5,(0,180,0)),(T(69)+1.8,(0,0,0))])
    sh=[(T(69),(0,0,0))]; t=T(69)+1.8
    while t<E(70): sh+= [(t,(-100,0,0)),(t+0.35,(-20,0,0))]; t+=0.7
    for a in ('arm_l','arm_r'): A.add(find(tk3,'tkC3_'+a),'rotation',sh,'catmullrom')
    shovel=M.group('shovel',[0,10,30],[M.cube('shv',[-1,8,22],[1,10,30],'timber_d'),M.cube('shvb',[-3,7,18],[3,9,22],'loco')]); top.append(shovel); vis(A,shovel,[(T(69),E(70))])
    A.add(shovel,'position',[(0,(0,0,0)),(T(69),(0,0,0)),(T(69)+1.5,(0,0,-44))])
    ln3=P(M,'lnC3_','lena',22,-18,yaw=0); top.append(ln3); vis(A,ln3,[(T(70),E(70)),(T(77),E(79))])
    arm1(A,ln3,'R',[(T(70),(-60,0,0)),(T(70)+0.3,(-80,0,0)),(T(70)+1.1,(-40,0,0)),(E(70),(-40,0,0))])
    arms(A,ln3,[(T(77),(-60,0,0)),(T(77)+1,(-80,0,0)),(E(77),(-80,0,0)),(E(77)+0.3,(0,0,0))]); talk(A,ln3,T(78),E(78))
    A.add(find(ln3,'lnC3_head'),'rotation',[(0,(0,0,0)),(T(78),(0,0,0)),(T(78)+0.4,(0,-60,0)),(E(79),(0,-60,0))],'catmullrom')
    # 82~90 밤: 오웬이 압력계를 들고, 레나가 이야기
    ow4=P(M,'owC4_','owen',-12,-14,yaw=0); top.append(ow4); vis(A,ow4,[(T(82),E(90))])
    A.add(find(ow4,'owC4_head'),'rotation',[(0,(20,0,0)),(T(84),(20,0,0)),(T(84)+0.4,(0,-80,0)),(E(90),(0,-80,0))],'catmullrom')
    arms(A,ow4,[(T(82),(-70,0,0)),(T(84),(-70,0,0)),(T(84)+0.5,(-30,0,0)),(E(90),(-30,0,0))])
    gh=gauge(M,'gHand',-12,20,-24,r=2.5); top.append(gh); vis(A,gh,[(T(82),T(84)+0.4)])
    ln4=P(M,'lnC4_','lena',20,-14,yaw=90); top.append(ln4); vis(A,ln4,[(T(82),E(90))])
    for i in (86,87,88,89): talk(A,ln4,T(i),E(i),amp=-30)
    A.add(find(ln4,'lnC4_head'),'rotation',[(0,(0,0,0)),(T(85),(0,0,0)),(T(85)+0.4,(-8,0,0)),(E(85),(-8,0,0)),(E(85)+0.3,(0,0,0))])
    widen(M,A,top,1.5); A.bake(top); flip_yaw(A); M.save(f'{OUT}/C_기관실.bbmodel',top,[A.json()],name='C'); return {}

# =====================================================================
#  D : 협곡 철교 — 철교 z -420~420 (위 y 0), 협곡 바닥 y -220, 양쪽 고원 y 0.  76~77 낮, 81 밤 언덕
# =====================================================================
def set_D():
    M=mk(); A=Anim(L); top=[M.cube('farD',[-5000,-300,-5000],[5000,-295,5000],'rock_rd')]
    top+= [M.cube('plat_s',[-900,-240,440],[900,0,2600],'sand'), M.cube('plat_n',[-900,-240,-2600],[900,0,-440],'sand_d'),
           M.cube('cany_f',[-900,-260,-440],[900,-220,440],'rock_rd')]
    for i in range(6):
        x=-900+i*300; top.append(M.cube('cwall',[x,-220,-440],[x+300,-120+(i%3)*30,-400+(i%2)*20],'rock_r'))
        top.append(M.cube('cwall',[x,-220,400-(i%2)*20],[x+300,-130+(i%2)*40,440],'rock_r'))
    tb=trestle(M,'trestle',0,-440,440,H=220); move(M,tb,0,-220,0); top.append(tb)
    top.append(track(M,'trackD',0,-2600,2600))
    top+= [mesa(M,'mD1',-600,-1200,320,200,260), mesa(M,'mD2',650,-1600,280,160,240), mesa(M,'mD3',-700,1200,260,140,200)]
    tr,_=inn_train(M,'trD_',0,0); top.append(tr)
    A.add(tr,'position',[(0,(0,0,900)),(T(76),(0,0,900)),(E(77),(0,0,-700)),(T(81)-0.05,(0,0,-700)),(T(81),(0,0,1000)),(E(81),(0,0,-100)),(L,(0,0,-100))])
    train_wheels(A,tr,'trD_',T(76),E(81),-300)
    top+= puffs(M,A,'stD',0,72,-45,[(T(76),E(77)),(T(81),E(81))],per=0.9,n=5,size=8,drift=(0,0,50))
    A.bake(top); flip_yaw(A); M.save(f'{OUT}/D_철교.bbmodel',top,[A.json()],name='D'); return {}

# =====================================================================
#  E : 바닷가 마지막 역 — 철길 끝 z -70 (막이), 바다 z < -260, 등대 (-260, -160) 언덕 위, 승강장 x -60~-25
# =====================================================================
def set_E():
    M=mk(); A=Anim(L); top=[M.cube('seaE',[-3000,-30,-3000],[3000,-24,-240],'sea')]
    top+= [M.cube('landE',[-1200,-40,-240],[1200,0,2600],'sand'), M.cube('grassE',[-1200,0,200],[1200,1,2600],'grass')]
    top+= [M.cube('cliff',[-1200,-40,-260],[1200,-2,-240],'rock_r')]
    top.append(M.cube('hillE',[-360,0,-230],[-160,30,-80],'grass_d'))
    lh=lighthouse(M,'lh_',-260,-160,H=170); move(M,lh,0,30,0); top.append(lh)
    lamp=find(lh,'lh_lamp'); vis(A,lamp,[(T(95)+2.2,L)])
    beam=M.group('beam',[-260,200,-160],[M.cube('bm',[-252,193,-164],[-60,197,-156],'lamp')]); top.append(beam); vis(A,beam,[(T(95)+2.2,L)])
    A.add(beam,'rotation',[(0,(0,0,0)),(T(95)+2.2,(0,0,0)),(L,(0,-(L-T(95))*40,0))])
    top.append(track(M,'trackE',0,-75,2600))
    top.append(M.group('bufE',[0,0,-72],[M.cube('buf',[-18,0,-80],[18,22,-66],'lacquer')]))
    top+= [M.cube('platE',[-70,0,40],[-24,8,330],'stone_l'), M.cube('stn',[-170,0,300],[-120,40,380],'lh_w'), M.cube('stn_r',[-176,40,294],[-114,48,386],'lh_r'),
           M.cube('stn_d',[-120,0,330],[-119.4,24,346],'timber_d')]
    tr,_=inn_train(M,'trE_',0,0); top.append(tr)
    A.add(tr,'position',[(0,(0,0,1300)),(T(92),(0,0,1300)),(E(92)+0.3,(0,0,0)),(L,(0,0,0))],'catmullrom')
    train_wheels(A,tr,'trE_',T(92),E(92)+0.3,-200)
    top+= puffs(M,A,'stE',0,72,-45,[(T(92),E(92)),(T(96),L)],per=1.6,n=5,size=7)
    # 비행선 (97~): 바다 위 높은 곳에서 등대 쪽으로 천천히 내려옴
    ash=airship(M,'as_',0,90,0); move(M,ash,-150,0,-500); top.append(ash)
    A.add(ash,'position',[(0,(0,500,-900)),(T(97),X(250,320,-700)),(E(97),X(80,90,-150)),(E(98),X(60,40,30)),(L,X(60,40,40))],'catmullrom')
    A.add(ash,'scale',[(0,(0,0,0)),(T(97)-0.02,(0,0,0)),(T(97),(1,1,1))])
    spin_x(A,find(ash,'as_prop'),T(97),L,0); A.add(find(ash,'as_prop'),'rotation',[(0,(0,0,0)),(T(97),(0,0,0)),(L,(0,0,(L-T(97))*360))])
    # ---- 사람 ----
    ow=P(M,'owE_','owen',-240,-110,yaw=180,y=30); top.append(ow); vis(A,ow,[(T(95),E(95))])
    arms(A,ow,[(T(95)+0.5,(0,0,0)),(T(95)+1.2,(-140,0,0)),(E(95),(-140,0,0))])
    tk=tok(M,'tkE_',-28,8,150,s=0.9); top.append(tk); vis(A,tk,[(T(96),E(98))]); A.add(tk,'rotation',[(0,(0,-90,0))])
    A.add(find(tk,'tkE_arm_l'),'rotation',[(T(96),(0,0,0)),(T(96)+0.5,(-150,0,0)),(T(96)+2,(-150,0,0)),(T(96)+2.4,(0,0,0))])
    sign=M.group('signE',[-15.5,32,146],[M.cube('sgn',[-16.2,28,138],[-15.6,36,154],'sign'),M.cube('sgn_i',[-16.4,31,140],[-16.2,33,152],'ink')]); top.append(sign); vis(A,sign,[(T(96)+2,L)])
    ln=P(M,'lnE_','lena',-24,44,yaw=90,y=8); top.append(ln); vis(A,ln,[(T(96),E(96))])   # 기관차 위(보일러 위)
    gst=P(M,'gsE_','trav',0,0); move(M,gst,-150,52,-500); top.append(gst)
    A.add(gst,'position',[(0,(0,500,-900)),(T(97),X(250,320,-700)),(E(97),X(80,90,-150)),(E(98),X(60,40,30)),(L,X(60,40,40))],'catmullrom')
    vis(A,gst,[(T(97),L)]); arm1(A,gst,'R',[(T(98),(0,0,0)),(T(98)+0.5,(-150,0,0)),(T(98)+1.2,(-120,0,0)),(T(98)+1.7,(-150,0,0)),(E(98),(0,0,0))])
    ow2=P(M,'owE2_','owen',-36,152,yaw=90,y=8); top.append(ow2); vis(A,ow2,[(T(99),L)])
    A.add(ow2,'rotation',[(0,(0,90,0)),(T(101),(0,90,0)),(T(101)+0.5,(0,20,0)),(E(101),(0,20,0)),(E(101)+0.4,(0,90,0))],'catmullrom')
    arms(A,ow2,[(T(101)+0.5,(0,0,0)),(T(101)+1.2,(-140,0,0)),(E(101)-0.5,(-140,0,0)),(E(101),(0,0,0))])
    arm1(A,ow2,'L',[(T(102),(0,0,0)),(T(102)+0.5,(-170,0,0)),(T(102)+1.5,(-170,0,0)),(T(102)+2,(0,0,0))])
    talk(A,ow2,T(103),E(103))
    ln2=P(M,'lnE2_','lena',-40,128,yaw=90,y=8); top.append(ln2); vis(A,ln2,[(T(99),L)])
    A.add(ln2,'position',[(0,(0,0,-60)),(T(99),(0,0,-60)),(E(99)-0.5,(0,0,0))]); walk_cycle(A,ln2,T(99),E(99)-0.5,amp=22,period=0.8)
    A.add(ln2,'rotation',[(0,(0,180,0)),(E(99)-0.5,(0,180,0)),(E(99),(0,90,0)),(T(100),(0,90,0)),(T(100)+0.4,(0,160,0)),(E(101),(0,160,0)),(E(101)+0.4,(0,90,0))],'catmullrom')
    arms(A,ln2,[(T(99),(0,0,0)),(T(99)+0.5,(-60,0,0)),(T(99)+1.5,(-60,0,0)),(T(99)+2,(0,0,0))]); talk(A,ln2,T(100),E(100))
    cap=M.group('capE',[-40,42,128],[M.cube('cap',[-44.4,37.5,123.6],[-35.6,42,132.4],'cap_e'),M.cube('capb',[-47.5,37.5,123.6],[-44.2,38.3,132.4],'cap_e'),M.cube('capbd',[-44.5,37.6,123.5],[-35.5,38.6,132.5],'brass')])
    top.append(cap); vis(A,cap,[(T(101)+1.5,L)])
    A.add(cap,'position',[(0,(0,10,0)),(T(101)+1.5,(0,10,0)),(E(101)-0.4,(0,1.2,0)),(L,(0,1.2,0))])
    A.bake(top); flip_yaw(A); M.save(f'{OUT}/E_바닷가.bbmodel',top,[A.json()],name='E'); return {}

if __name__=='__main__':
    which=sys.argv[1:] or ['A','B','C','D','E']
    info={}
    for k in which: info[k]=globals()['set_'+k]()
    p=f'{OUT}/세트정보.json'; old=json.load(open(p,encoding='utf-8')) if os.path.exists(p) else {}
    old.update(info)
    for k in old: old[k].setdefault('ropes',[])
    json.dump(old,open(p,'w',encoding='utf-8'),ensure_ascii=False,indent=1)
    json.dump(numbers(),open(f'{ROOT}/숫자.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
    for f in sorted(os.listdir(OUT)):
        if f.endswith('.bbmodel'): print(f, len(json.load(open(f'{OUT}/{f}',encoding='utf-8'))['elements']),'cubes')
