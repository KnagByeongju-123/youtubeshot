"""《모아이는 걸어갔다》 블록 장면 모형 만들기 → 연재/모아이걷기/장면/<세트>.bbmodel + 샷목록.json
   시간은 모두 '영상 시간(초)' 그대로 (연재/모아이걷기/모아이걷기_시간.json 기준)"""
import sys, os, json, random, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 블록인물 import *
OUT=sys.argv[1] if len(sys.argv)>1 else '/home/user/youtubeshot/연재/모아이걷기/장면'
os.makedirs(OUT,exist_ok=True)
L=310.0

def world_palette(M):
    M.swatch('grass',(105,160,75),12); M.swatch('grass_d',(90,140,65),12)
    M.swatch('dirt',(140,100,65),10); M.swatch('road',(165,125,85),10); M.swatch('road_d',(140,105,70),10)
    M.swatch('rock',(110,95,85),14); M.swatch('rock_d',(85,72,65),12); M.swatch('rock_l',(140,125,110),12)
    M.swatch('water',lambda x,y:(55,120,190) if (x+2*y)%7 else (90,155,215),6); M.swatch('sand',(225,205,160),8)
    M.swatch('trunk',lambda x,y:(120,90,60) if y%4 else (95,70,45),5); M.swatch('palm',(70,140,60),14)
    M.swatch('thatch',lambda x,y:(190,160,90) if (x+y)%4 else (150,120,60),6); M.swatch('stone_w',(130,125,120),12)
    M.swatch('log',lambda x,y:(150,110,70) if x%5 else (110,80,50),5)

def ground(M, x0,x1,z0,z1, tile=64, col='grass', y=0):
    out=[]; i=0
    for x in range(x0,x1,tile):
        for z in range(z0,z1,tile):
            c=col if col!='grass' else ('grass' if (x//tile+z//tile)%2 else 'grass_d')
            out.append(M.cube('g',[x,y-16,z],[x+tile,y,z+tile],c))
    return out

def road(M, xc, z0, z1, w=72, seg=32):
    """가운데가 오목한 길 (폭 w), z 방향"""
    out=[]
    for z in range(z0,z1,seg):
        out+= [M.cube('road_l',[xc-w/2,-4,z],[xc-w/6,2.5,z+seg],'road'),
               M.cube('road_c',[xc-w/6,-4,z],[xc+w/6,0.8,z+seg],'road_d'),
               M.cube('road_r',[xc+w/6,-4,z],[xc+w/2,2.5,z+seg],'road')]
    return out

def palm(M,tag,x,z,h=90):
    k=[M.cube('trunk',[x-3,0,z-3],[x+3,h,z+3],'trunk')]
    for dx,dz in [(1,0),(-1,0),(0,1),(0,-1)]:
        k.append(M.cube('leaf',[x+min(0,dx*34)-(4 if dx==0 else 0),h-6,z+min(0,dz*34)-(4 if dz==0 else 0)],
                              [x+max(0,dx*34)+(4 if dx==0 else 0),h-1,z+max(0,dz*34)+(4 if dz==0 else 0)],'palm'))
    k.append(M.cube('crown',[x-7,h-8,z-7],[x+7,h+4,z+7],'palm'))
    return M.group(tag,[x,0,z],k)

def ocean(M):
    return M.cube('ocean',[-3000,-40,-3000],[3000,-6,3000],'water')

def ropes(M,n):
    """밧줄 n 개 (촬영 때 끝점 사이로 늘려 붙임). 길이 1 짜리 상자, z 방향"""
    return M.group('ropes',[0,0,0],[M.cube(f'rope_{i}',[-0.7,-0.7,0],[0.7,0.7,1],'rope') for i in range(n)])

def walk_cycle(A, p, t0, t1, amp=28, period=1.0):
    """사람 p(root 묶음)에 걷기 팔다리 흔들기"""
    legL,legR,armL,armR=[find(p,p['name'].replace('root',n)) for n in ('leg_left','leg_right','arm_left','arm_right')]
    t=t0; s=1; pts=[]
    while t<t1-1e-6: pts.append((t,s)); t+=period/2; s=-s
    for g,sg in ((legL,1),(legR,-1),(armL,-1),(armR,1)):
        A.add(g,'rotation',[(t0-0.01,(0,0,0))]+[(tt,(sg*ss*amp,0,0)) for tt,ss in pts]+[(t1,(0,0,0))],'catmullrom')

# =====================================================================
#  세트 E : 석상 걷기 (길 + 석상 + 밧줄 무리 3 + 아투·마타) / 전설 장면용 석상
# =====================================================================
def set_E():
    M=Model(256); world_palette(M); islander_palette(M); moai_palette(M); M.swatch('rope',(200,170,110),6)
    A=Anim(L); top=[]
    top+= [ocean(M)]+ground(M,-480,480,-560,400)
    top+= road(M,0,-560,400)
    for i,(x,z) in enumerate([(-200,-300),(220,-150),(-260,120),(240,260),(-180,330),(300,-420),(-330,-480)]):
        top.append(palm(M,f'palm{i}',x,z,80+(i%3)*14))
    mo=moai(M,'m_',road=True); top.append(mo)
    # --- 걷기: 영상 시간 T0 부터, 반걸음마다 좌우로 기울며 앞으로(-z) ---
    Z0=150; T0=178.0; P=1.5; DZ=7; T1=256.0
    tilt=[]; pos=[]; t=T0; k=0; z=Z0
    pre=[(0,(0,0,0)),(T0-0.6,(0,0,0))]
    while t<T1:
        s=1 if k%2==0 else -1
        tilt+= [(t+P*0.45,(0,s*9,s*7)),(t+P,(0,0,0))]
        pos += [(t,(0,0,z)),(t+P*0.45,(0,1.2,z-DZ*0.5)),(t+P,(0,0,z-DZ))]
        z-=DZ; t+=P; k+=1
    A.add(mo,'rotation',pre+tilt,'catmullrom'); A.add(mo,'position',[(0,(0,0,Z0)),(T0,(0,0,Z0))]+pos,'linear')
    def mz(tt):  # 석상의 z (영상 시간 tt)
        return Z0 if tt<T0 else Z0-DZ*min((tt-T0)/P,(T1-T0)/P)
    # --- 밧줄 무리: 왼쪽(x-) 3명, 오른쪽(x+) 3명, 뒤 3명 ---
    crews={'L':[],'R':[],'B':[]}
    lay={'L':[(-60,-30),(-82,-42),(-104,-54)],'R':[(60,-30),(82,-42),(104,-54)],'B':[(0,62),(0,84),(0,106)]}
    kinds=['man','man2','man']
    for side in 'LRB':
        for j,(px,pz) in enumerate(lay[side]):
            g=person(M,f'c{side}{j}_',kinds[(j+(side=='R'))%3],1.0,['tapa2','tapa3','tapa'][j]); move(M,g,px,0,pz+Z0)
            g['rotation']=[0,{'L':90,'R':-90,'B':0}[side],0]   # 석상 쪽을 봄 (방향은 시험 촬영으로 확인)
            top.append(g); crews[side].append(g)
            # 따라 움직이기 (석상과 같은 z 이동)
            A.add(g,'position',[(0,(0,0,0)),(T0,(0,0,0))]+[(tt,(0,0,mz(tt)-Z0)) for tt in [T0+i*P for i in range(int((T1-T0)/P)+1)]])
            # 팔은 앞으로 (밧줄 잡기) — 166초부터
            for arm in ('arm_left','arm_right'):
                A.add(find(g,g['name'].replace('root',arm)),'rotation',[(0,(0,0,0)),(166,(0,0,0)),(168,(-75,0,0)),(T1,(-75,0,0))])
            # 자기 쪽으로 기울 때 몸을 뒤로 젖힘
            if side in 'LR':
                want=1 if side=='L' else -1; pts=[(0,(0,0,0)),(T0,(0,0,0))]; t=T0; kk=0
                while t<T1:
                    s=1 if kk%2==0 else -1
                    pts+= [(t+P*0.35,(14 if s==want else 0,0,0)),(t+P,(0,0,0))]; t+=P; kk+=1
                A.add(find(g,g['name'].replace('root','body')),'rotation',pts,'catmullrom')
            # 발 옮기기 (걷는 동안)
            walk_cycle(A,g,T0,T1,amp=14,period=P*2)
    # --- 아투·마타 (구경, 오른쪽 뒤에서 따라감) ---
    atu=person(M,'atu_','atu',0.8,'tapa'); move(M,atu,95,0,60+Z0); atu['rotation']=[0,-40,0]; top.append(atu)
    mata=person(M,'mata_','mata',1.0,'tapa2'); move(M,mata,120,0,85+Z0); mata['rotation']=[0,-40,0]; top.append(mata)
    for g in (atu,mata):
        A.add(g,'position',[(0,(0,0,0)),(T0,(0,0,0))]+[(tt,(0,0,mz(tt)-Z0)) for tt in [T0+i*P for i in range(int((T1-T0)/P)+1)]])
        walk_cycle(A,g,T0,T1,amp=20,period=1.0)
    # 아투 놀람(204.9~): 고개 들고 두 팔 살짝
    A.add(find(atu,'atu_head'),'rotation',[(0,(0,0,0)),(204.5,(0,0,0)),(205.3,(-18,0,0)),(209,(-18,0,0)),(210,(0,0,0))])
    # --- 전설 장면 (32.4~43.1): 사람 없이 혼자 걷는 석상, 다른 길 ---
    lg=moai(M,'lg_',road=True); move(M,lg,0,0,0); top.append(lg)
    LX=0; LZ=-420
    # 전설 석상은 평소엔 땅속에 숨김(크기 0) → 32~43초만 보임. 본 석상·사람은 그동안 크기 0
    tl=[];pl=[]; t=31.0; k=0; z=LZ
    while t<44:
        s=1 if k%2==0 else -1
        tl+= [(t+0.55,(0,s*9,s*7)),(t+1.2,(0,0,0))]; pl+= [(t,(0,0,z)),(t+0.55,(0,1.2,z-3)),(t+1.2,(0,0,z-6))]; z-=6; t+=1.2; k+=1
    A.add(lg,'rotation',[(0,(0,0,0))]+tl,'catmullrom'); A.add(lg,'position',[(0,(0,0,LZ))]+pl)
    A.add(lg,'scale',[(0,(0,0,0)),(31.9,(0,0,0)),(32.0,(1,1,1)),(43.6,(1,1,1)),(43.7,(0,0,0))])
    hide=[mo,atu,mata]+crews['L']+crews['R']+crews['B']
    for g in hide: A.add(g,'scale',[(0,(1,1,1)),(31.9,(1,1,1)),(32.0,(0,0,0)),(43.6,(0,0,0)),(43.7,(1,1,1))])
    top.append(ropes(M,3))
    A.bake(top)
    M.save(f'{OUT}/E_걷기.bbmodel',top,[A.json()],name='E')
    rp=[['m_rope_L',crews['L'][2]['name'].replace('root','hand_r')],['m_rope_R',crews['R'][2]['name'].replace('root','hand_r')],['m_rope_B',crews['B'][2]['name'].replace('root','hand_r')]]
    return {'ropes':rp,'mz':(Z0,T0,P,DZ,T1)}


def moai_walk(A,g,t0,t1,z0,P=1.4,DZ=6,lean=0):
    tl=[(0,(lean,0,0)),(t0-0.01,(lean,0,0))];pl=[(0,(0,0,z0)),(t0-0.01,(0,0,z0))]; t=t0;k=0;z=z0
    while t<t1-1e-6:
        s_=1 if k%2==0 else -1
        tl+= [(t+P*0.45,(lean,s_*9,s_*7)),(t+P,(lean,0,0))]; pl+= [(t,(0,0,z)),(t+P*0.45,(0,1.2,z-DZ/2)),(t+P,(0,0,z-DZ))]; z-=DZ;t+=P;k+=1
    A.add(g,'rotation',tl,'catmullrom'); A.add(g,'position',pl); return z

def hut(M,tag,x,z,L=110):
    """하레 파앙가 (배 모양 초가)"""
    k=[M.cube('base',[x-L/2,0,z-14],[x+L/2,3,z+14],'stone_w')]
    for i,(w,h) in enumerate([(26,8),(22,8),(16,8),(9,7)]):
        k.append(M.cube('th',[x-L/2+i*6,3+i*8,z-w/2],[x+L/2-i*6,3+i*8+h,z+w/2],'thatch'))
    k.append(M.cube('door',[x-6,3,z-14.5],[x+6,13,z-13.5],'rock_d'))
    return M.group(tag,[x,0,z],k)

def pukao(M,g,S=1.0):
    head=find(g,g['name'].replace('root','head'))
    head['children'].append(M.cube('pukao',[-8*S,80*S,-7*S],[8*S,92*S,7*S],'pukao'))

# =====================================================================
#  세트 A : 바닷가 제단(아후)·마을·마지막 장면
# =====================================================================
def set_A():
    M=Model(256); world_palette(M); islander_palette(M); moai_palette(M)
    A=Anim(L); top=[ocean(M)]
    top+= ground(M,-384,384,-320,256)
    top+= [M.cube('sand',[-384,-10,256],[384,-1,320],'sand')]
    top+= [M.cube('ahu',[-170,0,196],[250,16,240],'stone_w'), M.cube('ahu_ramp',[-170,0,180],[250,6,196],'stone_w')]
    row=[]
    for i,x in enumerate([-130,-65,0,65,130]):
        g=moai(M,f'a{i}_',road=False,eyes=True)
        if i in (1,3): pukao(M,g)
        move(M,g,x,16,212)
        top.append(g); row.append(g)
    for i,(x,z) in enumerate([(-300,-60),(300,-40),(-240,150),(330,160),(-340,-250),(200,-280)]):
        top.append(palm(M,f'pa{i}',x,z,85+(i%3)*12))
    top+= [hut(M,'hut1',-230,-150), hut(M,'hut2',-230,-220,90)]
    # 마을 사람 (26.3~32.4 걷기, 바구니)
    for j,(x,z0) in enumerate([(-150,-60),(-120,-20),(-175,20)]):
        g=person(M,f'v{j}_',['man','man2','man'][j],1.0,['tapa2','tapa3','tapa'][j]); move(M,g,x,0,z0)
        head=find(g,f'v{j}_head'); head['children'].append(M.cube('basket',[-5,32,-5],[5,37,5],'thatch'))
        A.add(g,'position',[(0,(0,0,0)),(26.0,(0,0,0)),(33.0,(0,0,-90))]); walk_cycle(A,g,26.0,33.0,amp=26,period=1.0)
        top.append(g)
    # 아투 (키 비교 21.9~26.3: 제단 앞), 마지막 장면엔 오른쪽
    atu=person(M,'atu_','atu',0.8,'tapa'); move(M,atu,0,0,165); top.append(atu)
    A.add(atu,'position',[(0,(0,0,0)),(277,(0,0,0)),(277.1,(-120,0,-15)),(L,(-120,0,-15))])    # 끝 장면: 새 석상 앞 (위치 x 는 반대)
    A.add(atu,'rotation',[(0,(0,180,0))])
    # 제단 앞에서 뒤돌아 석상을 올려다봄 (그 전 장면들에선 석상 쪽을 봄 = 뒤돌아섬 180)
    A.add(find(atu,'atu_head'),'rotation',[(0,(0,0,0)),(21.5,(0,0,0)),(23,(22,0,0)),(27,(22,0,0)),(27.5,(0,0,0)),(288.5,(0,0,0)),(289.5,(22,0,0)),(L,(22,0,0))])
    mata=person(M,'mata_','mata',1.0,'tapa2'); move(M,mata,150,0,110); top.append(mata)
    A.add(mata,'scale',[(0,(0,0,0)),(277,(0,0,0)),(277.1,(1,1,1)),(L,(1,1,1))])
    # 끝 장면 새 석상 (x=190): 279.7 걸어 들어옴 → 284~288 제단 위로 세움 → 287~289 눈
    nm=moai(M,'nm_',road=True,eyes=True); move(M,nm,190,0,0); top.append(nm)
    A.add(nm,'scale',[(0,(0,0,0)),(277,(0,0,0)),(277.1,(1,1,1)),(L,(1,1,1))])
    zend=moai_walk(A,nm,277.7,284.0,150,P=1.4,DZ=-6,lean=8)   # +z (제단 쪽)으로
    A.add(nm,'position',[(284.2,(0,0,zend)),(286.5,(0,16,212)),(L,(0,16,212))])
    A.add(nm,'rotation',[(284.2,(8,0,0)),(286.5,(0,0,0)),(L,(0,0,0))],'catmullrom')
    eyes=[c for c in find(nm,'nm_head')['children'] if isinstance(c,str)]
    eg=M.group('nm_eyes',[190,66,-6],[]); 
    hd=find(nm,'nm_head'); byid={e['uuid']:e for e in M.els}
    ev=[c for c in hd['children'] if isinstance(c,str) and byid[c]['name'] in('eye_w','eye_k')]
    for c in ev: hd['children'].remove(c)
    eg['children']=ev; hd['children'].append(eg)
    A.add(eg,'scale',[(0,(0,0,0)),(287.0,(0,0,0)),(288.6,(1,1,1)),(L,(1,1,1))])
    # 마을 사람 둘 (끝 장면 구경)
    for j,(x,z) in enumerate([(110,120),(250,125)]):
        g=person(M,f'w{j}_',['man2','man'][j],1.0,'tapa3'); move(M,g,x,0,z); top.append(g)
        A.add(g,'scale',[(0,(0,0,0)),(277,(0,0,0)),(277.1,(1,1,1)),(L,(1,1,1))])
        A.add(g,'rotation',[(0,(0,180,0))])
    A.add(mata,'rotation',[(0,(0,180,0))])
    A.bake(top); M.save(f'{OUT}/A_바닷가.bbmodel',top,[A.json()],name='A'); return {'ropes':[]}

# =====================================================================
#  세트 B : 채석장 (라노 라라쿠)
# =====================================================================
def set_B():
    M=Model(256); world_palette(M); islander_palette(M); moai_palette(M)
    A=Anim(L); top=[ocean(M)]+ground(M,-384,384,-320,128)
    top.append(M.cube('terrace',[-384,-30,100],[384,28,240],'rock',up='rock_l'))
    for i in range(1,6):   # 계단처럼 올라가는 화산 비탈 (+z)
        z0=240+(i-1)*40; y=28+i*28
        top.append(M.cube('slope',[-384,y-60,z0],[384,y,z0+40],'rock' if i%2 else 'rock_d',up='grass_d' if i>3 else 'rock_l'))
    top.append(M.cube('back',[-384,0,440],[384,200,520],'rock_d',up='grass'))
    # 비탈에 새겨진 미완성 석상들 (반듯이 누움, 바위에서 반쯤 나옴)
    for i,(x,yy,zz) in enumerate([(-170,93,250),(150,121,290),(-60,149,330)]):
        g=moai(M,f'u{i}_',road=False); move(M,g,x,yy,zz); g['rotation']=[-84,0,0]; top.append(g)
    q=moai(M,'q_',road=True); move(M,q,0,37,112); q['rotation']=[-84,0,0]; top.append(q)
    A.add(q,'position',[(0,(0,0,0)),(60.0,(0,0,0)),(61.0,(0,2,-4)),(62,(0,1,-10)),(L,(0,1,-10))],'catmullrom')
    A.add(q,'rotation',[(0,(0,0,0)),(60.0,(0,0,0)),(61,(2,0,1.5)),(62,(4,0,0)),(L,(4,0,0))],'catmullrom')
    # 석공들 (단 위, 도끼질 46~63)
    for j,(x,z,yaw) in enumerate([(-30,130,90),(30,148,-90),(-28,172,90),(28,190,-90)]):
        g=person(M,f'k{j}_',['man','man2','man','man2'][j],1.0,['tapa2','tapa3','tapa','tapa3'][j],tool='axe'); move(M,g,x,28,z); g['rotation']=[0,yaw,0]; top.append(g)
        arm=find(g,f'k{j}_arm_right'); pts=[(0,(-40,0,0))]; t=46+j*0.17; up=True
        while t<63: pts.append((t,(-140 if up else -50,0,0))); up=not up; t+=0.32
        pts.append((63.5,(-40,0,0))); A.add(arm,'rotation',pts,'catmullrom')
    # 아투: 45~52 걸어 들어옴(+z), 64 부터 할아버지를 봄
    atu=person(M,'atu_','atu',0.8,'tapa'); move(M,atu,0,0,-60); top.append(atu)
    A.add(atu,'position',[(0,(0,0,0)),(45.5,(0,0,0)),(52.5,(0,0,95)),(L,(0,0,95))]); walk_cycle(A,atu,45.5,52.5,amp=28,period=0.9)
    A.add(atu,'rotation',[(0,(0,180,0)),(64.0,(0,180,0)),(64.6,(0,90,0)),(L,(0,90,0))])
    ah=find(atu,'atu_head'); A.add(ah,'rotation',[(0,(0,0,0)),(56,(0,0,0)),(57,(18,0,0)),(63,(18,0,0)),(64,(0,0,0)),(68.5,(0,0,0)),(69,(12,0,0)),(72,(12,0,8)),(73.5,(12,0,-8)),(74.5,(8,0,0)),(L,(8,0,0))],'catmullrom')
    mata=person(M,'mata_','mata',1.0,'tapa2'); move(M,mata,38,0,35); top.append(mata)
    A.add(mata,'rotation',[(0,(0,-90,0))])
    mh=find(mata,'mata_head'); A.add(mh,'rotation',[(0,(0,0,0)),(74.5,(0,0,0)),(75,(-10,0,0)),(75.5,(0,0,0)),(76,(-10,0,0)),(76.5,(0,0,0))],'catmullrom')
    ma=find(mata,'mata_arm_left'); A.add(ma,'rotation',[(0,(0,0,0)),(77,(0,0,0)),(78,(-100,0,30)),(80.3,(-100,0,30))],'catmullrom')
    A.bake(top); M.save(f'{OUT}/B_채석장.bbmodel',top,[A.json()],name='B'); return {'ropes':[]}

# =====================================================================
#  세트 C : 옛 생각(눕혀서 썰매·통나무) + 나무 베기
# =====================================================================
def set_C():
    M=Model(256); world_palette(M); islander_palette(M); moai_palette(M); M.swatch('rope',(200,170,110),6)
    A=Anim(L); top=[ocean(M)]+ground(M,-384,384,-448,320)
    sl_parts=[M.cube('rail_l',[-14,4,-12],[-8,9,92],'log'),M.cube('rail_r',[8,4,-12],[14,9,92],'log'),M.cube('cross',[-14,4,-14],[14,9,-8],'log'),
              anchor(M,'sl_front',[0,8,-14])]
    mo=moai(M,'s_',road=False); move(M,mo,0,16,0); mo['rotation']=[-90,0,0]   # 반듯이 누움, 머리는 +z
    sl=M.group('sl_root',[0,0,0],sl_parts+[mo]); top.append(sl)
    logs=[]
    for i,z in enumerate([-4,22,48,74]):
        lg=M.group(f'log{i}',[0,3,z+3],[M.cube('log',[-20,0,z],[20,6,z+6],'log')]); top.append(lg); logs.append(lg)
        A.add(lg,'rotation',[(0,(0,0,0)),(80.3,(0,0,0)),(99.6,(-720,0,0))])
        A.add(lg,'position',[(0,(0,0,0)),(80.3,(0,0,0)),(99.6,(0,0,-60))])
    A.add(sl,'position',[(0,(0,0,0)),(80.3,(0,0,0)),(99.6,(0,0,-60))])
    pull=[]
    for j in range(8):
        x=-16 if j%2==0 else 16; z=-45-(j//2)*24
        g=person(M,f'p{j}_',['man','man2'][j%2],1.0,['tapa2','tapa3','tapa'][j%3]); move(M,g,x,0,z); top.append(g); pull.append(g)
        A.add(g,'position',[(0,(0,0,0)),(80.3,(0,0,0)),(99.6,(0,0,-60))]); walk_cycle(A,g,80.3,99.6,amp=22,period=1.6)
        A.add(find(g,f'p{j}_body'),'rotation',[(0,(0,0,0)),(80.3,(-18,0,0)),(99.6,(-18,0,0))])
        for arm in ('arm_left','arm_right'): A.add(find(g,f'p{j}_{arm}'),'rotation',[(0,(0,0,0)),(80.3,(-150,0,0)),(99.6,(-150,0,0))])
    trees=[]
    for i,(x,z) in enumerate([(-120,-200),(-60,-260),(10,-230),(80,-270),(140,-210),(-170,-120),(190,-140),(-220,60),(220,40),(-150,150),(160,170)]):
        t=palm(M,f'tr{i}',x,z,80+(i%3)*14); top.append(t); trees.append(t)
    for i,t in enumerate(trees[:7]):
        ts=100.0+i*0.95
        A.add(t,'rotation',[(0,(0,0,0)),(ts,(0,0,0)),(ts+1.1,(86,0,0)),(L,(86,0,0))],'catmullrom')
    top.append(ropes(M,2))
    A.bake(top); M.save(f'{OUT}/C_옛생각.bbmodel',top,[A.json()],name='C')
    return {'ropes':[['sl_front','p6__hand_r'.replace('__','_')],['sl_front','p7_hand_r']]}

# =====================================================================
#  세트 D : 옛길 + 쓰러진 석상 + 서 있는 길 석상(가까이·3차원)
# =====================================================================
def set_D():
    M=Model(256); world_palette(M); islander_palette(M); moai_palette(M)
    A=Anim(L); top=[ocean(M)]+ground(M,-320,320,-1216,256)+road(M,0,-1216,256)
    for i,(x,z,yaw) in enumerate([(-30,-80,15),(34,-330,-20),(-40,-560,160),(30,-820,-10),(-26,-1050,25)]):
        g=moai(M,f'f{i}_',road=True); move(M,g,x,0,z); g['rotation']=[86 if i%2==0 else -86,yaw,0]; top.append(g)
    sd=moai(M,'sd_',road=True); move(M,sd,150,0,-200); top.append(sd)
    for i,(x,z) in enumerate([(-200,-150),(220,-450),(-240,-700),(200,-950),(-180,100),(260,60)]):
        top.append(palm(M,f'pd{i}',x,z,80+(i%3)*14))
    A.add(sd,'rotation',[(0,(0,0,0))])
    A.bake(top); M.save(f'{OUT}/D_옛길.bbmodel',top,[A.json()],name='D'); return {'ropes':[]}

if __name__=='__main__':
    info={'A':set_A(),'B':set_B(),'C':set_C(),'D':set_D(),'E':set_E()}
    json.dump(info,open(f'{OUT}/세트정보.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
    for f in sorted(os.listdir(OUT)):
        if f.endswith('.bbmodel'): print(f, len(json.load(open(f'{OUT}/{f}',encoding='utf-8'))['elements']),'cubes')
