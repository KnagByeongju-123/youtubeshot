"""《자격루》 블록 장면 모형 → 연재/자격루/장면/<세트>_<이름>.bbmodel + 세트정보.json + 숫자.json
   시간은 모두 '영상 시간(초)': 연재/자격루/자격루_시간.json 의 문단 시작(T)·끝(E)
   세트: A 궁궐(경복궁) / B 밤의 옛 물시계 / C 장영실 공방 / D 자격루 속(보루각 안, 2007 박물관)
   움직임 위치(position)는 x 가 반대로 적용됨 → PX() 로 부호를 뒤집어 넣음"""
import sys, os, json, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 조선인물 import *
ROOT='/home/user/youtubeshot/연재/자격루'
OUT=f'{ROOT}/장면'; os.makedirs(OUT,exist_ok=True)
TIM=json.load(open(f'{ROOT}/자격루_시간.json',encoding='utf-8')); SEG=TIM['segs']; L=round(TIM['duration']+1,2)
T=lambda i: SEG[i]['t0']
E=lambda i: SEG[i]['t0']+SEG[i]['dur']
PX=lambda dx,dy=0,dz=0: (-dx,dy,dz)

# ---------------- 공용 ----------------
def world_palette(M):
    M.swatch('grass',(110,160,80),12); M.swatch('grass_d',(96,145,70),12); M.swatch('dirt',(170,150,115),8); M.swatch('dirt_d',(150,132,100),8)
    M.swatch('pine',(55,105,60),12); M.swatch('pine_d',(45,88,50),10); M.swatch('trunk',(110,80,55),6)
    M.swatch('hill',(85,130,75),10); M.swatch('hill_d',(70,112,64),10)
    M.swatch('tile',(62,64,70),6); M.swatch('tile_d',(48,50,55),5); M.swatch('pillar',(150,60,45),6); M.swatch('wall_w',(225,215,190),5)
    M.swatch('green_eave',(70,130,110),6); M.swatch('stone',(165,160,150),8); M.swatch('stone_d',(135,130,122),8); M.swatch('pave',(190,185,172),6)
    M.swatch('water',lambda x,y:(55,115,175) if (x+2*y)%7 else (90,150,205),6); M.swatch('water_c',(70,140,200),5)
    M.swatch('plank',lambda x,y:(160,120,80) if y%4 else (125,90,58),6); M.swatch('plank_d',(120,88,58),6)
    M.swatch('lamp',(255,215,120),6); M.swatch('moon',(245,240,210),3); M.swatch('ring',(255,240,170),3)
    M.swatch('museum',(70,72,78),4); M.swatch('museum_f',(200,200,198),4); M.swatch('glass',(190,220,235),3)
    M.swatch('bucket',(120,85,55),6); M.swatch('paper_w',(245,240,225),3)

def far_ground(M,col='grass'): return M.cube('far_ground',[-4000,-20,-4000],[4000,-15,4000],col)
def ground(M,x0,x1,z0,z1,tile=80,a='grass',b='grass_d',y=0):
    return [M.cube('g',[x,y-16,z],[x+tile,y,z+tile],a if (x//tile+z//tile)%2 else b) for x in range(x0,x1,tile) for z in range(z0,z1,tile)]
def hills(M,z=2600):
    return [M.cube('hill',[x-w/2,-10,z+(i%3)*140],[x+w/2,h,z+(i%3)*140+300],'hill' if i%2 else 'hill_d')
            for i,(x,w,h) in enumerate([(-1800,1100,260),(-700,1000,320),(400,1100,300),(1500,1000,240),(-1200,800,180),(900,900,200)])]
def pine(M,tag,x,z,h=70):
    k=[M.cube('trunk',[x-3,0,z-3],[x+3,h*0.45,z+3],'trunk')]
    for j,(w,y0) in enumerate([(34,h*0.3),(26,h*0.55),(16,h*0.78)]):
        k.append(M.cube('pine',[x-w/2,y0,z-w/2],[x+w/2,y0+h*0.22,z+w/2],'pine' if j%2 else 'pine_d'))
    return M.group(tag,[x,0,z],k)

def roof(M,x,y,z,w,d,tiers=5,over=18,step=5,col='tile'):
    k=[M.cube('eave',[x-w/2-over,y,z-d/2-over],[x+w/2+over,y+2,z+d/2+over],'green_eave')]
    for j in range(tiers):
        e=over-j*(over/tiers)*1.6
        k.append(M.cube('roof',[x-w/2-e,y+2+j*step,z-d/2-e],[x+w/2+e,y+2+(j+1)*step,z+d/2+e],col if j%2==0 else 'tile_d'))
    k.append(M.cube('ridge',[x-w/2+4,y+2+tiers*step,z-2],[x+w/2-4,y+5+tiers*step,z+2],'tile_d'))
    return k

def hall(M,tag,x,z,w=150,d=90,h=48,base=8,cols=4,front_open=False,roofed=True):
    """나무 집 (붉은 기둥·흰 벽·기와).  돌아오는 값: 묶음"""
    k=[M.cube('h_base',[x-w/2-6,0,z-d/2-6],[x+w/2+6,base,z+d/2+6],'stone')]
    for i in range(cols):
        px=-w/2+i*(w-6)/(cols-1)
        for pz in (-d/2,d/2-6): k.append(M.cube('h_pillar',[x+px,base,z+pz],[x+px+6,base+h,z+pz+6],'pillar'))
    k.append(M.cube('h_wall_b',[x-w/2+3,base,z+d/2-5],[x+w/2-3,base+h,z+d/2-3],'wall_w'))
    k.append(M.cube('h_wall_l',[x-w/2+1,base,z-d/2+3],[x-w/2+3,base+h,z+d/2-3],'wall_w'))
    k.append(M.cube('h_wall_r',[x+w/2-3,base,z-d/2+3],[x+w/2-1,base+h,z+d/2-3],'wall_w'))
    if not front_open:
        for i in range(cols-1):
            x0=x-w/2+6+i*(w-6)/(cols-1); x1=x-w/2+(i+1)*(w-6)/(cols-1)
            k.append(M.cube('h_door',[x0,base,z-d/2+1],[x1,base+h-6,z-d/2+2.5],'wall_w'))
            k.append(M.cube('h_lattice',[x0+3,base+10,z-d/2+0.6],[x1-3,base+h-12,z-d/2+1],'plank_d'))
    k.append(M.cube('h_beam',[x-w/2,base+h-6,z-d/2],[x+w/2,base+h,z+d/2],'green_eave'))
    if roofed: k+= roof(M,x,base+h,z,w,d)
    return M.group(tag,[x,0,z],k)

def gate(M,tag,x,z,w=150,d=50,h=40,arches=3,upper=True):
    """돌 축대 + 무지개 문(어두운 구멍) + 위 누각"""
    k=[M.cube('gt_base',[x-w/2,0,z-d/2],[x+w/2,h,z+d/2],'stone',north='stone_d')]
    aw=w/(arches*2+1)
    for i in range(arches):
        ax=x-w/2+aw*(2*i+1)
        k.append(M.cube('gt_arch',[ax,0,z-d/2-0.4],[ax+aw,h*0.62,z+d/2+0.4],'dark'))
    if upper:
        uw=w*0.78; ud=d*0.8; uh=26
        for i in range(5):
            px=-uw/2+i*(uw-5)/4
            for pz in (-ud/2,ud/2-5): k.append(M.cube('gt_pillar',[x+px,h,z+pz],[x+px+5,h+uh,z+pz+5],'pillar'))
        k.append(M.cube('gt_beam',[x-uw/2,h+uh-5,z-ud/2],[x+uw/2,h+uh,z+ud/2],'green_eave'))
        k+= roof(M,x,h+uh,z,uw,ud,tiers=5,over=16,step=5)
    return M.group(tag,[x,0,z],k)

def wall(M,x0,z0,x1,z1,h=26,t=8):
    if abs(x1-x0)>abs(z1-z0): fr,to=[min(x0,x1),0,z0-t/2],[max(x0,x1),h,z0+t/2]
    else: fr,to=[x0-t/2,0,min(z0,z1)],[x0+t/2,h,max(z0,z1)]
    return [M.cube('wall',fr,to,'wall_w',up='tile'), M.cube('wall_cap',[fr[0]-2,h,fr[2]-2],[to[0]+2,h+4,to[2]+2],'tile')]

def vis(A,g,spans):
    """spans=[(켜짐,꺼짐),...] 그 사이에만 보임"""
    spans=sorted(spans); on0=bool(spans) and spans[0][0]<=0.02
    pts=[(0,(1,1,1) if on0 else (0,0,0))]
    for a,b in spans:
        if a>0.02: pts+= [(a-0.02,(0,0,0)),(a,(1,1,1))]
        pts+= [(b,(1,1,1)),(b+0.02,(0,0,0))]
    A.add(g,'scale',pts)

def walk_cycle(A,p,t0,t1,amp=26,period=1.0):
    n=p['name'][:-4]
    parts=[(find(p,n+'leg_left'),1),(find(p,n+'leg_right'),-1),(find(p,n+'arm_left'),-1),(find(p,n+'arm_right'),1)]
    t=t0; s=1; pts=[]
    while t<t1-1e-6: pts.append((t,s)); t+=period/2; s=-s
    for g,sg in parts: A.add(g,'rotation',[(max(0,t0-0.01),(0,0,0))]+[(tt,(sg*ss*amp,0,0)) for tt,ss in pts]+[(t1,(0,0,0))],'catmullrom')

def hammer(A,p,t0,t1,per=0.5):
    n=p['name'][:-4]; ar=find(p,n+'arm_right')
    pts=[(max(0,t0-0.01),(-30,0,0))]; t=t0; up=True
    while t<t1: pts.append((t,(-95 if up else -45,0,0))); up=not up; t+=per/2
    pts.append((t1+0.2,(-30,0,0))); A.add(ar,'rotation',pts,'catmullrom')

def P(M,tag,kind,x,z,yaw=0,s=1.0,tool=None,y=0):
    g=person(M,tag,kind,s,tool); move(M,g,x,y,z); g['rotation']=[0,yaw,0]; return g

def ring(M,tag,x,y,z,r=10):
    """소리 퍼지는 고리 (납작한 네모 테두리) — 크기 키워 퍼지게"""
    k=[M.cube('ring',[x-r,y,z-r],[x+r,y+1.2,z-r+2],'ring'), M.cube('ring',[x-r,y,z+r-2],[x+r,y+1.2,z+r],'ring'),
       M.cube('ring',[x-r,y,z-r],[x-r+2,y+1.2,z+r],'ring'), M.cube('ring',[x+r-2,y,z-r],[x+r,y+1.2,z+r],'ring')]
    return M.group(tag,[x,y,z],k)

def pulse(A,g,times,grow_to=6,dur=0.9):
    pts=[(0,(0,0,0))]
    for t in times: pts+= [(t-0.02,(0,0,0)),(t,(0.3,1,0.3)),(t+dur,(grow_to,1,grow_to)),(t+dur+0.02,(0,0,0))]
    A.add(g,'scale',pts)

def strike(A,doll,times,amp=-40):
    """나무 인형이 막대로 침 (오른팔 들었다 내림)"""
    n=doll['name'][:-4]; ar=find(doll,n+'arm_right'); pts=[(0,(0,0,0))]
    for t in times: pts+= [(t-0.45,(0,0,0)),(t-0.2,(amp,0,0)),(t,(6,0,0)),(t+0.25,(0,0,0))]
    A.add(ar,'rotation',pts,'catmullrom')

def shake(A,g,times,amp=5):
    pts=[(0,(0,0,0))]
    for t in times: pts+= [(t,(0,0,0)),(t+0.08,(0,0,amp)),(t+0.2,(0,0,-amp*0.6)),(t+0.35,(0,0,amp*0.3)),(t+0.5,(0,0,0))]
    A.add(g,'rotation',pts,'catmullrom')

def night(M, keep=('lamp','moon','ring','paper_w')):
    """밤: 그림(색 견본)을 어둡고 푸르게. 등불·달은 그대로"""
    im=M.im; px=im.load(); keep_boxes=[M.sw[k] for k in keep if k in M.sw]
    for y in range(im.height):
        for x in range(im.width):
            if any(b[0]<=x<b[2] and b[1]<=y<b[3] for b in keep_boxes): continue
            r,g,b,a=px[x,y]
            if a: px[x,y]=(int(r*0.42),int(g*0.47),int(b*0.68),a)

def save(M,A,top,name):
    A.bake(top); M.save(f'{OUT}/{name}.bbmodel',top,[A.json()],name=name.split('_')[0])

# =====================================================================
#  A : 궁궐 — 드론 날아들기(1), 보루각(47~48), 궁궐 문 소리 잇기(49~51), 가마(53~55), 끝(63)
# =====================================================================
def set_A():
    M=BigModel(512); joseon_palette(M); world_palette(M); A=Anim(L)
    top=[far_ground(M,'grass')]+hills(M)
    top.append(M.cube('court',[-620,-15,-760],[620,0.4,420],'dirt'))
    top.append(M.cube('pave_main',[-40,-15,-760],[40,0.8,-150],'pave'))
    # 광화문·담
    top.append(gate(M,'gwanghwamun',0,-700,170,56,44))
    top+= wall(M,-620,-700,-85,-700)+wall(M,85,-700,620,-700)
    # 근정문·안쪽 담
    top.append(gate(M,'geunjeongmun',0,-400,130,44,30))
    top+= wall(M,-280,-400,-65,-400)+wall(M,65,-400,280,-400)+wall(M,-280,-400,-280,260)+wall(M,280,-400,280,260)+wall(M,-280,260,280,260)
    # 근정전 (두 단 돌 기단 + 큰 집)
    top.append(M.cube('gj_base1',[-150,0,-220],[150,10,40],'stone')); top.append(M.cube('gj_base2',[-120,10,-190],[120,20,20],'stone'))
    top.append(hall(M,'geunjeongjeon',0,-85,200,130,62,base=20,cols=6))
    # 경회루: 연못 + 돌기둥 + 누각
    px,pz=-450,-120
    top.append(M.cube('pond',[px-150,-15,pz-120],[px+150,-3,pz+120],'water'))
    top.append(M.cube('pond_edge',[px-156,-15,pz-126],[px+156,-2,pz+126],'stone_d'))
    gk=[M.cube('gh_isle',[px-95,-3,pz-60],[px+95,4,pz+60],'stone')]
    for i in range(6):
        for j in range(4):
            gx=px-80+i*32; gz=pz-48+j*32; gk.append(M.cube('gh_col',[gx-3,4,gz-3],[gx+3,40,gz+3],'stone'))
    gk.append(M.cube('gh_floor',[px-88,40,pz-56],[px+88,46,pz+56],'plank_d'))
    for i in range(6):
        for j in (0,3):
            gx=px-80+i*32; gz=pz-48+j*32; gk.append(M.cube('gh_pil',[gx-3,46,gz-3],[gx+3,72,gz+3],'pillar'))
    gk+= roof(M,px,72,pz,176,112,tiers=6,over=22,step=6)
    gk.append(M.cube('gh_bridge',[px-12,-2,pz+60],[px+12,4,pz+126],'stone'))
    top.append(M.group('gyeonghoeru',[px,0,pz],gk))
    top+= wall(M,-610,-300,-300,-300)+wall(M,-610,-300,-610,260)+wall(M,-610,260,-300,260)
    top.append(gate(M,'gyeonghoeru_gate',-450,-300,70,24,22,arches=1,upper=False))
    top.append(M.group('ggate_roof',[-450,22,-300],roof(M,-450,22,-300,64,22,tiers=3,over=10,step=4)))
    # 보루각 (궁궐 안 서쪽, 세 칸) — 앞이 -z
    bx,bz=-200,140
    top.append(hall(M,'borugak',bx,bz,96,56,40,base=8,cols=4))
    for i,(x,z) in enumerate([(-560,-560),(560,-560),(-520,330),(520,320),(-200,-560),(200,-560),(380,-200),(400,120),(-140,330)]):
        top.append(pine(M,f'pine{i}',x,z,64+(i%3)*14))
    # 북·종 치는 관원 (보루각·경회루 남문·근정문·광화문 앞) + 소리 고리
    relay=[(bx,bz-50,'보루각'),(-450,-330,'경회루남문'),(0,-430,'근정문'),(0,-735,'광화문')]
    s49=T(49)+0.6; tt=[s49, s49+1.4, T(50)+0.6, T(50)+2.2]
    for k,((x,z,nm),t) in enumerate(zip(relay,tt)):
        d=drum(M,f'rdrum{k}',x+14,0,z,1.4); top.append(d)
        m=P(M,f'rman{k}_','gwanwon',x-2,z+6,yaw=0,tool='mallet'); top.append(m)
        strike(A,m,[t,t+0.6]); shake(A,d,[t,t+0.6],3)
        r=ring(M,f'ring{k}',x+14,26,z,12); top.append(r); pulse(A,r,[t,t+0.6],7,1.0)
        vis(A,m,[(T(46),E(51))]); vis(A,d,[(T(46),E(51))])
    # 1442 가마 (근정전 앞뜰) — 54 에서 부서짐
    gx,gz=0,-260
    pole_l=M.group('pole_l',[gx-9,14,gz],[M.cube('pole',[gx-10,13,gz-40],[gx-8,15,gz+40],'wood')])
    pole_r=M.group('pole_r',[gx+9,14,gz],[M.cube('pole',[gx+8,13,gz-40],[gx+10,15,gz+40],'wood')])
    box=M.group('gama',[gx,15,gz],[M.cube('gama_box',[gx-9,15,gz-12],[gx+9,38,gz+12],'dan_red',north='wood_r_d'),
        M.cube('gama_roof',[gx-11,38,gz-14],[gx+11,41,gz+14],'gold'), M.cube('gama_top',[gx-3,41,gz-3],[gx+3,45,gz+3],'gold')])
    top+= [pole_l,pole_r,box]
    bearers=[]
    for k,(dx,dz) in enumerate([(-15,-32),(15,-32),(-15,32),(15,32)]):
        b=P(M,f'bear{k}_','man',gx+dx,gz+dz,yaw=180 if dz<0 else 180); top.append(b); bearers.append(b)
    tb=T(54)+1.2
    A.add(pole_r,'rotation',[(0,(0,0,0)),(tb,(0,0,0)),(tb+0.3,(0,0,-14)),(tb+0.6,(0,0,-22))],'catmullrom')
    A.add(pole_r,'position',[(0,(0,0,0)),(tb,(0,0,0)),(tb+0.6,PX(0,-9,0))])
    A.add(box,'rotation',[(0,(0,0,0)),(tb+0.1,(0,0,0)),(tb+0.5,(0,0,-18)),(tb+0.8,(0,0,-24))],'catmullrom')
    A.add(box,'position',[(0,(0,0,0)),(tb+0.1,(0,0,0)),(tb+0.8,PX(4,-8,0))],'catmullrom')
    for b in bearers+[pole_l,pole_r,box]: vis(A,b,[(T(52),E(54))])
    # 장영실: 54 고개 숙임 → 55 궁궐 밖으로 걸어 나감 (-z)
    ys=P(M,'ysil_','yeongsil',40,-290,yaw=0); top.append(ys)
    hd=find(ys,'ysil_head'); A.add(hd,'rotation',[(0,(0,0,0)),(T(54)+2.0,(0,0,0)),(T(54)+2.8,(22,0,0))])
    A.add(ys,'rotation',[(0,(0,180,0)),(T(55)-0.1,(0,180,0)),(T(55)+0.4,(0,0,0))],'catmullrom')
    A.add(ys,'position',[(0,(0,0,0)),(T(55)+0.2,(0,0,0)),(E(55)+1.0,(0,0,-110))])
    walk_cycle(A,ys,T(55)+0.2,E(55)+1.0,20,1.1)
    vis(A,ys,[(T(52),E(55)+1.2)])
    save(M,A,top,'A_궁궐')
    return {'borugak':[bx,bz],'relay':relay,'gama':[gx,gz]}

# =====================================================================
#  B : 밤의 옛 물시계 (7~11) — 관원이 졸다가 시각을 놓침, 세종의 걱정
# =====================================================================
def set_B():
    M=BigModel(512); joseon_palette(M); world_palette(M); A=Anim(L)
    top=[far_ground(M,'dirt')]+ground(M,-480,480,-480,480,a='dirt',b='dirt_d')+hills(M)
    top.append(M.cube('moon',[-500,520,1600],[-400,620,1620],'moon'))
    # 물시계 정자 (기둥 넷 + 지붕)
    k=[M.cube('pv_base',[-50,0,-40],[50,6,40],'stone')]
    for x in (-46,40):
        for z in (-36,30): k.append(M.cube('pv_pil',[x,6,z],[x+6,60,z+6],'pillar'))
    k+= roof(M,0,60,0,100,80,tiers=4,over=14,step=5)
    top.append(M.group('pavilion',[0,0,0],k))
    # 옛 물시계: 받침 위 항아리 → 물받이 통 + 눈금 막대
    top.append(M.cube('oc_stand',[-30,6,-6],[-12,34,12],'stone_d')); top.append(jar(M,'oc_jar',-21,34,3,8,16))
    top.append(M.cube('oc_pipe',[-15,40,2],[2,41.5,4],'copper'))
    top.append(M.cube('oc_vessel',[0,6,-6],[14,40,8],'bronze')); top.append(M.cube('oc_rim',[-1,40,-7],[15,42,9],'bronze_l'))
    rod=M.group('oc_rod',[7,42,1],[M.cube('oc_rodc',[5.8,30,0],[8.2,62,2.4],'wood',north='paper')]); top.append(rod)
    A.add(rod,'position',[(0,(0,0,0)),(T(8),(0,0,0)),(E(10),(0,9,0))])
    # 북·징 + 등불
    dr=drum(M,'b_drum',30,6,-14,1.0); gg=gong(M,'b_gong',30,6,18,1.0); top+= [dr,gg]
    for x,z in ((-44,-34),(42,-34)):
        top.append(M.cube('lamp_post',[x,6,z],[x+2,30,z+2],'wood_d')); top.append(M.cube('lamp',[x-3,30,z-3],[x+5,40,z+5],'lamp'))
    # 관원: 서서 졸다 (8: 눈 비빔, 10: 고개 푹)
    gw=P(M,'gw_','gwanwon',12,-26,yaw=0); top.append(gw)
    hd=find(gw,'gw_head'); ar=find(gw,'gw_arm_right')
    A.add(ar,'rotation',[(0,(0,0,0)),(T(8)+0.4,(0,0,0)),(T(8)+1.0,(-150,0,-20)),(T(8)+1.4,(-140,0,-30)),(T(8)+1.8,(-150,0,-20)),(T(8)+2.2,(-140,0,-30)),(T(8)+2.8,(0,0,0))],'catmullrom')
    nod=[(0,(0,0,0)),(T(9)+0.5,(0,0,0)),(T(9)+1.3,(18,0,0)),(T(9)+1.6,(2,0,0)),(T(9)+2.6,(22,0,0)),(T(9)+2.9,(0,0,0)),
         (T(10)+0.3,(0,0,0)),(T(10)+1.2,(24,0,0)),(E(10),(24,0,0)),(E(10)+0.4,(0,0,0))]
    A.add(hd,'rotation',nod,'catmullrom')
    # 세종: 오른쪽 집 마루에서 바라봄 (11)
    top.append(hall(M,'b_hall',190,150,150,70,46,base=10,cols=4,front_open=True))
    for x in (140,240): top.append(M.cube('lamp',[x-4,40,108],[x+4,50,116],'lamp'))
    sj=P(M,'sj_','sejong',190,128,yaw=-40,y=10); top.append(sj)
    for i,(x,z) in enumerate([(-300,-250),(320,-260),(-330,240),(-200,330)]): top.append(pine(M,f'pine{i}',x,z,70))
    night(M); save(M,A,top,'B_밤물시계'); return {}

# =====================================================================
#  C : 장영실 공방 (12~19, 59~60)
# =====================================================================
def set_C():
    M=BigModel(512); joseon_palette(M); world_palette(M); A=Anim(L)
    top=[far_ground(M,'grass')]+ground(M,-400,400,-400,400,a='dirt',b='dirt_d')+hills(M)
    top.append(M.cube('floor',[-110,0,-80],[110,3,90],'plank'))
    top.append(M.cube('back_wall',[-110,3,84],[110,70,90],'wall_w'))
    top+= [M.cube('left_wall',[104,3,-5],[110,70,90],'wall_w'), M.cube('left_wall2',[104,3,-80],[110,70,-55],'wall_w'), M.cube('door_top',[104,56,-55],[110,70,-5],'wall_w'),
           M.cube('right_wall',[-116,3,-80],[-110,70,90],'wall_w')]
    for i,(x,z) in enumerate([(-260,-200),(260,-220),(-300,200),(300,180),(200,-320)]): top.append(pine(M,f'pine{i}',x,z,70))
    for x in (-110,-40,30,104): top.append(M.cube('pil',[x,3,84],[x+6,72,90],'pillar'))
    top.append(M.cube('beam',[-110,64,84],[110,72,90],'green_eave'))
    # 작업대 + 연장 + 만들다 만 물건들
    top.append(M.cube('bench',[-30,3,-6],[40,20,22],'plank_d')); top.append(M.cube('bench_top',[-32,20,-8],[42,23,24],'plank'))
    top.append(jar(M,'c_jar',30,23,10,5,10)); top.append(M.cube('c_tube',[36,23,8],[41,38,16],'bronze'))
    top.append(M.cube('c_plate',[-28,23,14],[-26,38,20],'copper'))
    for i in range(4): top.append(M.cube('c_ball',[-22+i*4,23,2],[-19.4+i*4,25.6,4.6],'copper'))
    top.append(M.cube('c_saw',[24,23,14],[38,24,17],'iron'))
    top.append(M.cube('shelf',[-100,3,60],[-40,50,80],'plank_d'))
    for i in range(3): top.append(jar(M,f'sh_jar{i}',-90+i*20,22,70,6,12))
    top.append(M.cube('wood_pile',[60,3,40],[96,14,70],'wood'))
    # 장영실 (작업대 앞, 앞=-z → 작업대 보려면 +z 를 봐야 함: yaw 180)
    ys=P(M,'ys_','yeongsil',5,-22,yaw=0,tool='chisel'); top.append(ys)
    A.add(ys,'rotation',[(0,(0,180,0)),(T(18)+0.6,(0,180,0)),(T(18)+1.4,(0,90,0)),(E(19)+1,(0,90,0)),(T(59),(0,180,0))],'catmullrom')
    hammer(A,ys,T(13)+0.5,E(16)); hammer(A,ys,T(60),E(60))
    hy=find(ys,'ys_head'); A.add(hy,'rotation',[(0,(0,0,0)),(T(19),(0,0,0)),(T(19)+0.4,(-8,0,0)),(T(19)+0.9,(4,0,0)),(T(19)+1.3,(0,0,0))],'catmullrom')
    # 막동이: 물동이를 들고 왼쪽(+x)에서 걸어옴(17) → 멈춰 물음(18)
    mk=P(M,'mk_','makdong',90,-30,yaw=0,s=0.75); top.append(mk)
    bk=M.group('bucket',[0,0,0],[M.cube('bucket',[-3,6,-8],[3,12,-2],'bucket'), M.cube('bucket_w',[-2.4,11.6,-7.4],[2.4,12.2,-2.6],'water_c')])
    move(M,bk,90-4.5,0,-30); find(mk,'mk_hand_r')['children'].append(bk) if False else top.append(bk)
    A.add(mk,'rotation',[(0,(0,-90,0)),(T(18)+0.2,(0,-90,0)),(T(18)+0.8,(0,-90,0))])
    A.add(mk,'position',[(0,PX(0)),(T(17),PX(0)),(T(17)+3.2,PX(-55))])
    A.add(bk,'position',[(0,PX(0)),(T(17),PX(0)),(T(17)+3.2,PX(-55))])
    walk_cycle(A,mk,T(17),T(17)+3.2,24,0.8)
    hm=find(mk,'mk_head'); A.add(hm,'rotation',[(0,(0,0,0)),(T(18),(0,0,0)),(T(18)+0.4,(-10,0,0)),(E(18),(-10,0,0)),(E(18)+0.4,(0,0,0))],'catmullrom')
    vis(A,mk,[(T(17),E(19)+2),(T(59),L)]); vis(A,bk,[(T(17),E(19)+2)])
    save(M,A,top,'C_공방'); return {}

# =====================================================================
#  D : 자격루 속 (보루각 안) — 2~5 소개, 21~45 원리·인형·세종, 57~58 박물관, 60~63 다시 한 번
# =====================================================================
WR=56   # 물통 물 높이 범위
def ramp(M,name,xa,ya,xb,yb,z,r,col='copper',n=None,w=6):
    """구슬 중심 (xa,ya)→(xb,yb) 를 따라 계단식 홈통 (구슬 아래에 놓임)"""
    n=n or max(4,int(abs(xb-xa)/4)); k=[]
    for i in range(n):
        x0=xa+(xb-xa)*i/n; x1=xa+(xb-xa)*(i+1)/n; y=ya+(yb-ya)*(i+0.5)/n-r
        k.append(M.cube(name,[min(x0,x1),y-1.4,z-w/2],[max(x0,x1),y,z+w/2],col))
        k.append(M.cube(name+'_wall',[min(x0,x1),y,z+w/2-0.6],[max(x0,x1),y+1.6,z+w/2],col))
    return k

def set_D():
    M=BigModel(512); joseon_palette(M); world_palette(M); A=Anim(L)
    top=[far_ground(M,'grass')]
    # 보루각 안 (마루·뒷벽·기둥) / 2007 박물관 (회색 바닥·검은 벽)
    hk=[M.cube('floor',[-260,-2,-260],[260,0,120],'plank'), M.cube('back_wall',[-260,0,100],[260,170,110],'wall_w')]
    for x in (-260,-130,0,130,254): hk.append(M.cube('pil',[x,0,94],[x+6,170,100],'pillar'))
    hk.append(M.cube('beam',[-260,160,94],[260,170,110],'green_eave'))
    hk.append(M.cube('side_l',[-266,0,-260],[-260,170,110],'wall_w')); hk.append(M.cube('side_r',[260,0,-260],[266,170,110],'wall_w'))
    hallg=M.group('hall',[0,0,0],hk); top.append(hallg)
    mk_=[M.cube('m_floor',[-260,-1.8,-260],[260,0.4,120],'museum_f'), M.cube('m_wall',[-260,0,100],[260,170,110],'museum'),
         M.cube('m_rail',[-150,0,-60],[150,10,-58],'glass'), M.cube('m_side_l',[-266,0,-260],[-260,170,110],'museum'), M.cube('m_side_r',[260,0,-260],[266,170,110],'museum'), M.cube('m_rail2',[-150,10,-60.4],[150,12,-57.6],'iron')]
    museum=M.group('museum',[0,0,0],mk_); top.append(museum)
    t_mus=(T(57),E(58)+0.1); vis(A,hallg,[(0,t_mus[0]),(t_mus[1],L)]); vis(A,museum,[t_mus])
    # --- 파수호 4개 (높은 계단 위) + 물줄기
    steps=[(-118,-90,120),(-90,-64,100),(-64,-42,82),(-42,-22,66)]; rr=[12,10,8.5,7]; hh=[26,22,18,15]
    for i,(x0,x1,h) in enumerate(steps): top.append(M.cube(f'stand{i}',[x0,0,-16],[x1,h,16],'granite',up='granite_d'))
    t_flow=[(T(23),E(26)),(T(62),T(62)+2.2)]
    for i,((x0,x1,h),r,jh) in enumerate(zip(steps,rr,hh)):
        cx=(x0+x1)/2; top.append(jar(M,f'pasu{i}',cx,h,0,r,jh))
        py=h+jh*0.3
        nx=(steps[i+1][0]+steps[i+1][1])/2 if i<3 else -8
        ny=steps[i+1][2]+hh[i+1] if i<3 else 65
        top.append(M.cube(f'pipe{i}',[cx+r*0.6,py,-1],[nx+1,py+1.6,1],'copper'))
        sg=M.group(f'stream{i}',[nx,py,0],[M.cube('stream',[nx-0.6,ny-1,-0.6],[nx+0.6,py,0.6],'water_c')]); top.append(sg); vis(A,sg,t_flow)
    # --- 수수호 2개: 속이 보이게 (앞벽은 따로 = 닫힘/열림)
    opened=[(T(21),T(39)),(T(60),L)]; closed=[(0,T(21)),(T(39),T(60))]
    fronts=[]
    def level_keys():
        s0=0.3
        return [(0,s0),(T(24),s0),(T(30)+0.6,0.8),(T(59),0.8),(T(59)+0.05,s0),(T(62),s0),(T(62)+1.8,0.8)]
    for i,x in enumerate((-8,14)):
        top.append(M.cube(f'susu_base{i}',[x-8,0,-8],[x+8,4,8],'granite_d'))
        top+= [M.cube('susu_back',[x-7,4,6],[x+7,62,7.4],'bronze'), M.cube('susu_l',[x-7.4,4,-7],[x-6,62,7],'bronze'),
               M.cube('susu_r',[x+6,4,-7],[x+7.4,62,7],'bronze'), M.cube('susu_rim',[x-8,62,-8],[x+8,65,8],'bronze_l')]
        fr=M.group(f'susu_front{i}',[x,4,-7],[M.cube('susu_front',[x-7,4,-7.4],[x+7,62,-6],'bronze'),
                                             M.cube('susu_dragon',[x-7.2,20,-7.7],[x+7.2,46,-7.3],'dragon')])
        top.append(fr); fronts.append(fr)
        wg=M.group(f'water{i}',[x,4,0],[M.cube('water',[x-6,4,-6],[x+6,4+WR,6],'water_c')]); top.append(wg)
        lk=level_keys() if i==0 else [(0,0.55)]
        A.add(wg,'scale',[(t,(1,s,1)) for t,s in lk])
        # 살대: 물 위에 뜬 나무 받침 + 긴 막대 (물 높이만큼 오르내림)
        y0=4+WR*0.3
        rod=M.group(f'rod{i}',[x,y0,0],[M.cube('float',[x-5,y0-2,-5],[x+5,y0,5],'wood'),
                                      M.cube('rod',[x-1.2,y0,-1.2],[x+1.2,y0+72,1.2],'wood',up='paper'),
                                      M.cube('rod_tick',[x-1.3,y0+20,-1.45],[x+1.3,y0+66,-1.25],'paper')])
        top.append(rod)
        if i==0: A.add(rod,'position',[(t,(0,WR*(s-0.3),0)) for t,s in lk])
        else: A.add(rod,'position',[(0,(0,WR*0.25,0))])
    # --- 동판(구리판)과 작은 구슬 (살대0 오른쪽 옆)
    top.append(M.cube('plate',[-4.6,66,-3],[-3,124,3],'copper'))
    for j in range(7):
        hy=72+j*7.5; top.append(M.cube('hole',[-4.8,hy,-1],[-4.4,hy+2,1],'dark'))
        if j>=5: top.append(M.cube('sball_rest',[-4.4,hy-0.6,-1.2],[-2,hy+1.8,1.2],'copper'))
    sball=M.group('sball',[-3,118.6,0],[M.cube('sball',[-4.2,117.4,-1.2],[-1.8,119.8,1.2],'bronze_l')]); top.append(sball)
    # 작은 구슬 길: 동판 → 상자 입구 (40, 92)
    top+= ramp(M,'s_track',-1,117,40,93,0,1.2,w=4)
    # --- 시보 장치 상자 (속 보이게 / 앞판은 따로)
    X0,X1,D=40,112,22
    top+= [M.cube('cab_back',[X0,0,D-3],[X1,92,D],'wood_r'), M.cube('cab_l',[X0,0,-D],[X0+3,92,D],'wood_r'),
           M.cube('cab_r',[X1-3,0,-D],[X1,92,D],'wood_r'), M.cube('cab_floor',[X0-2,92,-D-2],[X1+2,95,D+2],'wood_r_d'),
           M.cube('cab_mid',[X0+3,52,-2],[X1-3,54,D-3],'wood_r_d'),
           M.cube('cab_top_back',[X0,95,D-3],[X1,128,D],'wood_r'),
           M.cube('cab_post_l',[X0,95,-D],[X0+3,128,-D+3],'wood_r_d'), M.cube('cab_post_r',[X1-3,95,-D],[X1,128,-D+3],'wood_r_d'),
           M.cube('cab_roof',[X0-6,128,-D-6],[X1+6,132,D+6],'gat'), M.cube('cab_roof2',[X0,132,-D+2],[X1,136,D-2],'gat'),
           M.cube('cab_band',[X0-0.5,88,-D-0.5],[X1+0.5,90,D+0.5],'gold')]
        # 입구 구멍 (왼쪽 벽 위)
    top.append(M.cube('cab_in',[X0-0.4,90,-2],[X0+3.4,94,2],'dark'))
    fk=[M.cube('cab_front',[X0,0,-D-0.6],[X1,88,-D+0.4],'wood_r',north='wood_r_d'),
        M.cube('cab_win',[X0+20,58,-D-1],[X1-20,84,-D-0.5],'dark')]
    for j in range(4): x=X0+6+j*16.5; fk.append(M.cube('door',[x,8,-D-1],[x+12,40,-D-0.5],'wood_r_d'))
    cf=M.group('cab_front',[X0,0,-D],fk); top.append(cf); fronts.append(cf)
    for f in fronts: vis(A,f,closed)
    # 받침 컵(작은 구슬이 떨어지는 곳) + 쇠구슬 막는 빗장 + 비탈 4개 + 지렛대 + 미는 막대
    cup=M.group('cup',[47,86,-14],[M.cube('cup',[44,84,-17],[50,86,-11],'copper'), M.cube('cup_w',[44,86,-17],[45,89,-11],'copper')]); top.append(cup)
    top.append(M.cube('chute_in',[40,88.5,-15],[46,89.5,1],'copper'))
    gatebar=M.group('gatebar',[57,86,-14],[M.cube('gatebar',[56.5,84,-18],[57.5,92,-10],'iron')]); top.append(gatebar)
    br=2.5
    R=[((54,86),(102,73)),((104,65),(56,53)),((54,45),(102,33)),((104,25),(58,13))]
    for j,((xa,ya),(xb,yb)) in enumerate(R): top+= ramp(M,f'ramp{j}',xa,ya,xb,yb,-14,br,'wood',w=8)
    top.append(M.cube('rack',[50,82,-18],[56,83.5,-10],'wood'))
    lever=M.group('lever',[52,10,-14],[M.cube('lever',[46,9,-15],[58,11,-13],'iron'), M.cube('lever_pin',[51,7,-16],[53,10,-12],'iron')]); top.append(lever)
    push=M.group('push',[48,12,-14],[M.cube('push',[47,12,-15],[49,95,-13],'iron')]); top.append(push)
    bball=M.group('bball',[54,86,-14],[M.cube('bball',[51.5,83.5,-16.5],[56.5,88.5,-11.5],'iron_ball')]); top.append(bball)
    # --- 위층: 종·북·징 + 인형 셋
    bell_=bell(M,'bell',50,95,-12,1.0); drum_=drum(M,'drum',72,95,-12,1.0); gong_=gong(M,'gong',94,95,-12,1.0)
    top+= [bell_,drum_,gong_]
    dolls=[]
    for i,xx in enumerate([50,72,94]):   # 악기 오른쪽(+x)에 서서 악기(-x)를 봄 → 앞에서 보면 옆모습으로 침
        d=person(M,f'doll{i}_','doll',0.55,'mallet'); move(M,d,xx+11,95,-12); d['rotation']=[0,-90,0]; top.append(d); dolls.append(d)
    # --- 가운데층: 열두 띠 인형 둥근 판 (뒤쪽) + 창 앞에 나오는 인형
    wcx,wcz=(X0+X1)/2,8
    wk=[M.cube('wheel',[wcx-14,54,wcz-14],[wcx+14,56,wcz+14],'wood_r_d'), M.cube('wheel_x',[wcx-10,54,wcz-16],[wcx+10,56,wcz+16],'wood_r_d')]
    for j in range(12):
        a=j*30*math.pi/180; x=wcx+math.sin(a)*11; z=wcz-math.cos(a)*11
        d=person(M,f'z{j}_','doll_g',0.3,None); move(M,d,x,56,z); d['rotation']=[0,-j*30,0]; wk.append(d)
    wheel=M.group('wheel',[wcx,56,wcz],wk); top.append(wheel)
    zd=person(M,'zshow_','doll_g',0.45,'sipae'); move(M,zd,wcx,56,-8); top.append(zd)
    # ================= 움직임 =================
    tr=T(30)+0.6                                  # 살대 끝이 구멍에 닿는 때
    def small_path(t0,t_end):
        pts=[(-3,118.6),(-1,117),(40,93),(42,91),(47,87)]
        tt=[t0,t0+0.25,t0+0.25+(t_end-t0-0.6),t_end-0.3,t_end]
        return list(zip(tt,pts))
    def big_path(t0,t1,hit):
        pts=[(54,86),(102,73),(104,65),(56,53),(54,45),(102,33),(104,25),(58,13),(52,13)]
        segs=[48,8,48,8,48,8,46,6]; tot=sum(segs); out=[]; t=t0
        for (p,sgl) in zip(pts,[0]+segs): t+= (t1-t0)*sgl/tot; out.append((t,p))
        out[-1]=(hit,pts[-1]); return out
    def kfs_pos(group,base,paths):
        pts=[(0,(0,0,0))]
        for path,reset in paths:
            for t,(x,y) in path: pts.append((t,PX(x-base[0],y-base[1],0)))
            if reset: pts+= [(reset,PX(path[-1][1][0]-base[0],path[-1][1][1]-base[1],0)),(reset+0.02,(0,0,0))]
        A.add(group,'position',pts)
    # 1차 (설명): 작은 구슬 30~31 / 쇠구슬 32~35 / 인형 35~36 / 열두 띠 38
    # 2차 (다시 한 번, 62)
    t62=T(62); r2=t62+1.9
    sp1=small_path(tr,T(31)+1.8); sp2=small_path(r2,r2+1.3)
    kfs_pos(sball,(-3,118.6),[(sp1,T(59)),(sp2,None)])
    vis(A,sball,[(0,sp1[-1][0]+0.3),(T(59)+0.05,sp2[-1][0]+0.3)])
    A.add(cup,'rotation',[(0,(0,0,0)),(sp1[-1][0],(0,0,0)),(sp1[-1][0]+0.25,(0,0,-25)),(sp1[-1][0]+0.8,(0,0,0)),
                          (sp2[-1][0],(0,0,0)),(sp2[-1][0]+0.2,(0,0,-25)),(sp2[-1][0]+0.6,(0,0,0))],'catmullrom')
    g1=T(32)+0.3; g2=sp2[-1][0]+0.25
    A.add(gatebar,'position',[(0,(0,0,0)),(g1-0.3,(0,0,0)),(g1,(0,8,0)),(g1+1.2,(0,8,0)),(g1+1.6,(0,0,0)),
                              (g2-0.1,(0,0,0)),(g2+0.1,(0,8,0)),(g2+0.8,(0,8,0)),(g2+1.0,(0,0,0))])
    hit1=T(35)+0.4; hit2=t62+5.2
    bp1=big_path(g1,E(33)-0.2,hit1); bp2=big_path(g2+0.05,hit2-0.15,hit2)
    kfs_pos(bball,(54,86),[(bp1,T(59)),(bp2,None)])
    A.add(lever,'rotation',[(0,(0,0,0)),(hit1,(0,0,0)),(hit1+0.15,(0,0,-14)),(hit1+1.2,(0,0,-14)),(hit1+1.6,(0,0,0)),
                            (hit2,(0,0,0)),(hit2+0.12,(0,0,-14)),(hit2+1.0,(0,0,0))],'catmullrom')
    A.add(push,'position',[(0,(0,0,0)),(hit1,(0,0,0)),(hit1+0.2,(0,3,0)),(hit1+1.2,(0,3,0)),(hit1+1.6,(0,0,0)),
                           (hit2,(0,0,0)),(hit2+0.15,(0,3,0)),(hit2+1.0,(0,0,0))])
    # 종 (시): 들어가며 3, 1차 35, 박물관 58, 다시 62, 끝 63
    bt=[T(3)+1.2,T(3)+2.2, hit1+0.35,hit1+1.2,hit1+2.1, T(58)+1.4,T(58)+2.3, hit2+0.3, T(63)+0.8]
    strike(A,dolls[0],bt); shake(A,bell_,bt,5)
    dt=[T(36)+1.6,T(36)+2.3]; strike(A,dolls[1],dt); shake(A,drum_,dt,3)
    gt=[T(36)+3.0,T(36)+3.7]; strike(A,dolls[2],gt); shake(A,gong_,gt,6)
    # 열두 띠 판 돌기 + 창 앞 인형 올라옴 (38), 1차 뒤 39 에도 다시 한 번
    A.add(wheel,'rotation',[(0,(0,0,0)),(T(38)+0.2,(0,0,0)),(T(38)+1.6,(0,-30,0)),(T(59),(0,-30,0)),(T(59)+0.05,(0,0,0))],'catmullrom')
    A.add(zd,'position',[(0,(0,-8,0)),(T(38)+1.4,(0,-8,0)),(T(38)+2.4,(0,0,0))],'catmullrom'); vis(A,zd,[(T(38)+1.4,T(59))])
    # --- 사람들: 막동이(21 걸어 들어옴, 40 놀람), 장영실(40·42~45), 세종(42~45)
    mk=P(M,'mk_','makdong',-40,-80,yaw=0,s=0.75); top.append(mk)
    A.add(mk,'rotation',[(0,(0,180,0))])
    A.add(mk,'position',[(0,(0,0,-170)),(T(21)+0.1,(0,0,-170)),(E(21)+0.3,(0,0,0))])
    walk_cycle(A,mk,T(21)+0.1,E(21)+0.3,22,0.8)
    hm=find(mk,'mk_head'); A.add(hm,'rotation',[(0,(0,0,0)),(T(40),(0,0,0)),(T(40)+0.5,(-22,0,0)),(E(40),(-22,0,0)),(E(40)+0.5,(0,0,0))],'catmullrom')
    armL=find(mk,'mk_arm_left'); armR=find(mk,'mk_arm_right')
    for a_,sg in ((armL,1),(armR,-1)): A.add(a_,'rotation',[(0,(0,0,0)),(T(40)+0.2,(0,0,0)),(T(40)+0.6,(-150,0,sg*20)),(E(40),(-150,0,sg*20)),(E(40)+0.4,(0,0,0))],'catmullrom')
    vis(A,mk,[(T(20),E(22)),(T(40),E(40))])
    ys=P(M,'ys_','yeongsil',-12,-80,yaw=0); top.append(ys)
    A.add(ys,'rotation',[(0,(0,180,0)),(T(43)+0.2,(0,180,0)),(T(43)+1.0,(0,-90,0)),(T(44)+0.5,(0,-90,0))],'catmullrom')
    bd=find(ys,'ys_body'); A.add(bd,'rotation',[(0,(0,0,0)),(T(44)+0.8,(0,0,0)),(T(44)+1.6,(0,0,30)),(T(44)+3.2,(0,0,30)),(T(44)+4.0,(0,0,0))],'catmullrom')
    vis(A,ys,[(T(40),E(45)+0.2)])
    sj=P(M,'sj_','sejong',-44,-80,yaw=0); top.append(sj)
    A.add(sj,'rotation',[(0,(0,180,0)),(T(43)+0.2,(0,180,0)),(T(43)+1.0,(0,90,0))],'catmullrom')
    hs=find(sj,'sj_head'); A.add(hs,'rotation',[(0,(0,0,0)),(T(42)+0.2,(-12,0,0)),(T(42)+1.0,(-12,0,0)),(T(42)+1.4,(0,0,0))],'catmullrom')
    vis(A,sj,[(T(41),E(45)+0.2)])
    save(M,A,top,'D_자격루'); return {'X0':X0,'X1':X1}

def numbers():
    return [
     {'seg':1,'text':'1434년 (세종 16년)'},
     {'seg':4,'text':'자격루(自擊漏) = 스스로 치는 물시계'},
     {'seg':15,'text':'『세종실록』 1433년 9월 16일 기사'},
     {'seg':22,'text':'파수호(물 항아리) 4개'},
     {'seg':24,'text':'수수호(물받이 통) 2개'},
     {'seg':29,'text':'작은 구리 구슬 · 탄알만 한 크기'},
     {'seg':32,'text':'쇠구슬 · 달걀만 한 크기'},
     {'seg':36,'text':'종 = 시(時) · 북 = 경(更) · 징 = 점(點)'},
     {'seg':44,'text':'호군 = 정4품 무관 벼슬'},
     {'seg':47,'text':'보루각(報漏閣) · 경복궁 서쪽'},
     {'seg':48,'text':'『세종실록』 1434년 7월 1일(음력) 기사'},
     {'seg':54,'text':'1442년 (세종 24년)'},
     {'seg':56,'text':'남은 물통 · 1536년(중종 31년) · 국보'},
     {'seg':57,'text':'2007년 · 국립고궁박물관 복원 공개'},
    ]

if __name__=='__main__':
    only=sys.argv[1:] or ['A','B','C','D']
    info_p=f'{OUT}/세트정보.json'; info=json.load(open(info_p,encoding='utf-8')) if os.path.exists(info_p) else {}
    fn={'A':set_A,'B':set_B,'C':set_C,'D':set_D}
    for k in only: info[k]=fn[k](); info[k].setdefault('ropes',[])
    json.dump(info,open(info_p,'w',encoding='utf-8'),ensure_ascii=False,indent=1)
    json.dump(numbers(),open(f'{ROOT}/숫자.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
    for f in sorted(os.listdir(OUT)):
        if f.endswith('.bbmodel'): print(f, len(json.load(open(f'{OUT}/{f}',encoding='utf-8'))['elements']),'cubes')
