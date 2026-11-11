"""《자격루》 블록 부품: 조선 사람(장영실·막동이·세종·서운관 관원) + 자격루(물 항아리·물통·시보 장치) + 종·북·징.
   신라인물.py 의 person(키 32 ≈ 1.7m → 1m ≈ 19)을 그대로 쓰고, 조선 옷(단령·사모·익선관·목화)을 덧붙임."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 신라인물 import BigModel, silla_palette, person as _person, PEOPLE, SKIN, HAIR, GREY
from 블록인물 import Model, move, anchor, Anim, find, U

def joseon_palette(M):
    silla_palette(M)
    M.swatch('dan_blue',(45,85,110),5); M.swatch('dan_blue_d',(30,60,80),4)      # 장영실 단령 (짙은 청록)
    M.swatch('dan_green',(70,120,80),5); M.swatch('dan_green_d',(50,90,60),4)    # 관원 단령 (녹색)
    M.swatch('dan_red',(180,40,40),5); M.swatch('dan_red_d',(140,28,28),4)       # 세종 곤룡포 (붉은색)
    M.swatch('gold',(215,170,60),6); M.swatch('gakdae',(35,30,30),3)              # 금색 무늬, 각대(검은 띠)
    M.swatch('jo_ochre2',(200,160,90),6); M.swatch('jo_ochre2_d',(165,128,70),5)  # 막동이 저고리
    M.swatch('hat',(20,20,24),3); M.swatch('boot',(25,25,28),3)                   # 사모·익선관, 목화(검은 신)
    M.swatch('bronze',(105,95,62),7); M.swatch('bronze_d',(75,68,45),6); M.swatch('bronze_l',(150,135,85),7)
    M.swatch('copper',(185,105,65),8); M.swatch('iron_ball',(60,62,68),4)
    M.swatch('wood_r',(140,55,40),6); M.swatch('wood_r_d',(105,40,30),5)         # 붉은 칠 나무(장치 상자)
    M.swatch('dan_green_l',(95,150,105),5); M.swatch('paper',(240,230,200),4)
    M.swatch('drum',(190,60,45),5); M.swatch('drum_skin',(230,215,175),4)
    M.swatch('dragon',(70,140,110),8)
    M.swatch('granite',(190,185,175),8); M.swatch('granite_d',(160,155,148),8); M.swatch('dark',(25,22,22),3)
    def face(name,hair,beard=None,young=False,mus=False):
        def fn(d,x,y):
            d.rectangle([x,y,x+15,y+15],fill=SKIN); d.rectangle([x,y,x+15,y+2],fill=hair)
            for ex in (3,9):
                d.rectangle([x+ex,y+6,x+ex+3,y+8],fill=(255,255,255)); d.rectangle([x+ex+1,y+6,x+ex+2,y+8],fill=(25,20,20))
                d.rectangle([x+ex,y+5,x+ex+3,y+5],fill=hair)
            d.rectangle([x+7,y+9,x+8,y+10],fill=(205,160,120))
            if mus: d.rectangle([x+5,y+11,x+10,y+11],fill=beard or hair)
            d.rectangle([x+6,y+12,x+9,y+12],fill=(170,80,70) if not beard else (150,70,60))
            if beard: d.rectangle([x+6,y+14,x+9,y+15],fill=beard)
            if young: d.rectangle([x+2,y+10,x+3,y+10],fill=(240,150,130)); d.rectangle([x+12,y+10,x+13,y+10],fill=(240,150,130))
        M.paint(name,fn)
    face('f_yeongsil',HAIR,beard=HAIR,mus=True); face('f_sejong',HAIR,beard=HAIR,mus=True)
    face('f_gwanwon',HAIR); face('f_makdong',HAIR,young=True)
    def doll_face(d,x,y):   # 나무 인형 얼굴 (둥근 눈, 붉은 볼)
        d.rectangle([x,y,x+15,y+15],fill=(225,200,160)); d.rectangle([x,y,x+15,y+2],fill=(30,26,26))
        for ex in (4,10): d.rectangle([x+ex,y+6,x+ex+1,y+8],fill=(25,20,20))
        d.rectangle([x+2,y+10,x+4,y+11],fill=(230,120,110)); d.rectangle([x+11,y+10,x+13,y+11],fill=(230,120,110))
        d.rectangle([x+6,y+12,x+9,y+12],fill=(160,60,50))
    M.paint('f_doll',doll_face)
    def sign(d,x,y):        # 시패(시각 팻말): 흰 판에 검은 획
        d.rectangle([x,y,x+15,y+15],fill=(240,230,200)); d.rectangle([x+6,y+3,x+9,y+12],fill=(30,30,30)); d.rectangle([x+4,y+6,x+11,y+7],fill=(30,30,30))
    M.paint('sipae',sign)
    for k,v in {'yeongsil':('f_yeongsil','dan_blue','dan_blue_d','dan_blue','gakdae','samo'),
                'gwanwon':('f_gwanwon','dan_green','dan_green_d','dan_green','gakdae','samo'),
                'sejong':('f_sejong','dan_red','dan_red_d','dan_red','gold','ikseon'),
                'makdong':('f_makdong','jo_ochre2','jo_ochre2_d','pants_w','belt_r','braid'),
                'doll':('f_doll','dan_red','dan_red_d','dan_red','gakdae','samo'),
                'doll_g':('f_doll','dan_green','dan_green_d','dan_green','gakdae','samo')}.items():
        PEOPLE[k]=v

def _recolor(M, uid, col):
    for e in M.els:
        if e['uuid']==uid:
            for f in e['faces'].values(): f['uv']=M.sw[col]

def person(M, tag, kind='gwanwon', s=1.0, tool=None):
    """조선 사람.  kind: yeongsil(장영실) / gwanwon(서운관 관원) / sejong(세종) / makdong(막동이) / doll·doll_g(자격루 나무 인형)
       tool: 신라인물과 같음 + 'sipae'(두 손에 시각 팻말) / 'mallet'(종 치는 막대)"""
    t2 = None if tool in ('sipae','mallet') else tool
    g=_person(M, tag, kind, s, t2)
    fc,jo,jod,pt,bt,hair=PEOPLE[kind]
    c=lambda name,fr,to,col,**f: M.cube(name,[v*s for v in fr],[v*s for v in to],col,**f)
    body=find(g,tag+'body'); head=find(g,tag+'head'); aL=find(g,tag+'arm_left'); aR=find(g,tag+'arm_right')
    if kind!='makdong':
        # 단령: 발목까지 내려오는 둥근 깃 옷 + 넓은 소매 + 목화(검은 신)
        body['children']+= [c('robe_low',[-4.7,3,-2.7],[4.7,13,2.7],jo), c('round_collar',[-2.6,22.4,-2.55],[2.6,24,-2.35],jod),
                            c('belt_hang',[-4.6,14.6,-2.65],[4.6,16,2.65],bt)]
        aL['children']+= [c('wide_sleeve',[4,13.2,-3],[9,18.5,3],jo)]
        aR['children']+= [c('wide_sleeve',[-9,13.2,-3],[-4,18.5,3],jo)]
        for leg in ('leg_left','leg_right'):
            lg=find(g,tag+leg)
            for ch in lg['children']:
                if isinstance(ch,str):
                    e=[x for x in M.els if x['uuid']==ch][0]
                    if e['name']=='shoe': _recolor(M,ch,'boot')
        if kind=='sejong':   # 곤룡포 가슴의 금색 둥근 무늬(보)
            body['children']+= [c('bo',[-2.3,16.6,-2.8],[2.3,20.4,-2.6],'gold')]
    if hair=='samo':     # 사모: 둥근 통 + 양옆으로 뻗은 납작한 날개
        head['children']+= [c('samo_base',[-4.4,29.5,-4.4],[4.4,32.4,4.4],'hat'), c('samo_top',[-2.8,32.4,0],[2.8,35,4.2],'hat'),
                            c('samo_wing_l',[2.8,32.8,3.4],[7.6,34.4,3.8],'hat'), c('samo_wing_r',[-7.6,32.8,3.4],[-2.8,34.4,3.8],'hat')]
    if hair=='ikseon':   # 익선관: 둥근 통 + 뒤에서 위로 선 날개 둘
        head['children']+= [c('ik_base',[-4.4,29.5,-4.4],[4.4,32.4,4.4],'hat'), c('ik_top',[-2.8,32.4,0],[2.8,35.4,4.2],'hat'),
                            c('ik_wing_l',[1.6,33.6,3.6],[3.4,37.4,4.0],'hat'), c('ik_wing_r',[-3.4,33.6,3.6],[-1.6,37.4,4.0],'hat')]
    if tool=='sipae':
        # 오른손에 쥔 막대 위로 팻말 (머리 옆, 앞을 봄)
        aR['children']+= [c('sipae_stick',[-6.8,9,-0.7],[-5.4,25,0.7],'wood_d'), c('sipae',[-10.5,24,-0.7],[-1.7,31,0.7],'paper',north='sipae')]
    if tool=='mallet':
        aR['children']+= [c('mallet',[-6.5,12.9,-11],[-5.7,13.9,-1.4],'wood_d'), c('mallet_h',[-7.4,11.6,-13],[-4.8,15.2,-10.6],'wood')]
    return g

# ---------------- 종·북·징 ----------------
def bell(M, tag, x, y, z, S=1.0):
    """시를 알리는 종 (매단 틀 포함). 바닥 중심 (x,y,z)"""
    c=lambda n,fr,to,col: M.cube(n,[x+fr[0]*S,y+fr[1]*S,z+fr[2]*S],[x+to[0]*S,y+to[1]*S,z+to[2]*S],col)
    k=[c('b_post1',[-8,0,-1],[-6.5,20,1],'wood_d'), c('b_post2',[6.5,0,-1],[8,20,1],'wood_d'), c('b_beam',[-8,20,-1],[8,21.5,1],'wood_d'),
       c('b_hook',[-0.5,17,-0.5],[0.5,20,0.5],'iron'), c('b_top',[-2.2,15,-2.2],[2.2,17,2.2],'bronze_d'),
       c('b_body',[-3.4,8,-3.4],[3.4,15,3.4],'bronze'), c('b_lip',[-4.2,6.5,-4.2],[4.2,8.5,4.2],'bronze_l'), c('b_base',[-8,0,-2],[8,1,2],'wood_d')]
    return M.group(tag,[x,y,z],k)

def drum(M, tag, x, y, z, S=1.0):
    """밤의 경(更)을 알리는 북 (받침대 위, 가죽 면이 앞 -z)"""
    c=lambda n,fr,to,col,**f: M.cube(n,[x+fr[0]*S,y+fr[1]*S,z+fr[2]*S],[x+to[0]*S,y+to[1]*S,z+to[2]*S],col,**f)
    k=[c('d_leg1',[-5,0,-1],[-4,9,1],'wood_d'), c('d_leg2',[4,0,-1],[5,9,1],'wood_d'),
       c('d_body',[-5,8,-3.5],[5,17,3.5],'drum',north='drum_skin',south='drum_skin'), c('d_rim',[-5.3,7.6,-3.8],[5.3,8.4,3.8],'gold'),
       c('d_rim2',[-5.3,16.6,-3.8],[5.3,17.4,3.8],'gold')]
    return M.group(tag,[x,y,z],k)

def gong(M, tag, x, y, z, S=1.0):
    """밤의 점(點)을 알리는 징 (틀에 매단 둥근 쇠판, 면이 앞 -z)"""
    c=lambda n,fr,to,col: M.cube(n,[x+fr[0]*S,y+fr[1]*S,z+fr[2]*S],[x+to[0]*S,y+to[1]*S,z+to[2]*S],col)
    k=[c('g_post1',[-7,0,-1],[-5.5,19,1],'wood_d'), c('g_post2',[5.5,0,-1],[7,19,1],'wood_d'), c('g_beam',[-7,19,-1],[7,20.5,1],'wood_d'),
       c('g_cord',[-0.4,15.5,-0.4],[0.4,19,0.4],'belt'),
       c('g_disc',[-4.5,6.5,-0.6],[4.5,15.5,0.6],'bronze_l'), c('g_disc_v',[-3.2,5.2,-0.6],[3.2,16.8,0.6],'bronze_l'),
       c('g_boss',[-1.5,9.5,-1.2],[1.5,12.5,-0.6],'bronze_d'), c('g_base',[-7,0,-2],[7,1,2],'wood_d')]
    return M.group(tag,[x,y,z],k)

# ---------------- 자격루 ----------------
def jar(M, tag, x, y, z, r, h, col='bronze'):
    """둥근 물 항아리를 상자 세 겹으로 (바닥 중심 x,y,z / 반지름 r / 높이 h)"""
    k=[M.cube('jar_base',[x-r*0.7,y,z-r*0.7],[x+r*0.7,y+h*0.15,z+r*0.7],col+'_d' if col=='bronze' else col),
       M.cube('jar_body',[x-r,y+h*0.15,z-r],[x+r,y+h*0.75,z+r],col),
       M.cube('jar_body_x',[x-r*0.75,y+h*0.1,z-r*1.08],[x+r*0.75,y+h*0.8,z+r*1.08],col),
       M.cube('jar_body_z',[x-r*1.08,y+h*0.1,z-r*0.75],[x+r*1.08,y+h*0.8,z+r*0.75],col),
       M.cube('jar_neck',[x-r*0.6,y+h*0.75,z-r*0.6],[x+r*0.6,y+h*0.92,z+r*0.6],'bronze_d'),
       M.cube('jar_rim',[x-r*0.75,y+h*0.92,z-r*0.75],[x+r*0.75,y+h,z+r*0.75],'bronze_l'),
       M.cube('jar_band',[x-r*1.1,y+h*0.45,z-r*1.1],[x+r*1.1,y+h*0.5,z+r*1.1],'dragon')]
    return M.group(tag,[x,y,z],k)

def jagyeongnu(M, tag='j_', S=1.0, rods=True):
    """자격루 전체 (앞 = -z).  왼쪽: 계단 받침 위 파수호 4개(위에서 아래로 작아짐) → 가운데: 수수호 2개(살대) → 오른쪽: 시보 장치 상자
       (위층 = 종·북·징 치는 인형 셋, 가운데층 = 열두 띠 인형이 시패를 들고 나오는 창, 아래 = 구슬 장치 숨김).
       돌아오는 값: (묶음, 부품 사전).  1m ≈ 19.  전체 폭 약 230 (≈ 12m 아님: 화면에 맞춰 줄임 — 사람보다 넉넉히 큼)"""
    parts={}; k=[]
    # 받침 계단 (돌) — 위가 왼쪽 끝
    steps=[(-118,-88,62),(-88,-62,46),(-62,-40,32),(-40,-20,20)]
    for i,(x0,x1,h) in enumerate(steps):
        k.append(M.cube(f'stand{i}',[x0,0,-16],[x1,h,16],'granite',up='granite_d'))
    jars=[]
    for i,((x0,x1,h),r,jh) in enumerate(zip(steps,[13,11,9,7.5],[30,25,20,16])):
        g=jar(M,tag+f'pasu{i}',(x0+x1)/2,h,0,r,jh); jars.append(g); k.append(g)
        # 다음 항아리로 물이 흐르는 관
        if i<3:
            nx=(steps[i+1][0]+steps[i+1][1])/2
            k.append(M.cube(f'pipe{i}',[(x0+x1)/2+r*0.6,h+jh*0.3,-1],[nx,h+jh*0.3+1.6,1],'copper'))
    parts['pasu']=jars
    # 수수호 2개 (길쭉한 통 + 살대)
    susu=[]
    for i,x in enumerate((-8,14)):
        kk=[M.cube('susu_base',[x-8,0,-8],[x+8,4,8],'granite_d'),
            M.cube('susu_body',[x-7,4,-7],[x+7,62,7],'bronze'), M.cube('susu_body_x',[x-5.2,4,-7.6],[x+5.2,62,7.6],'bronze'),
            M.cube('susu_body_z',[x-7.6,4,-5.2],[x+7.6,62,5.2],'bronze'),
            M.cube('susu_dragon',[x-7.8,20,-7.8],[x+7.8,46,-7.6],'dragon'),          # 앞면 용 무늬 띠
            M.cube('susu_rim',[x-8,62,-8],[x+8,65,8],'bronze_l')]
        rod=M.group(tag+f'rod{i}',[x,40,0],[M.cube('rod',[x-1.2,40,-1.2],[x+1.2,86,1.2],'wood',up='paper'),
                                          M.cube('rod_tick',[x-1.3,50,-1.4],[x+1.3,80,-1.2],'paper')]) if rods else None
        g=M.group(tag+f'susu{i}',[x,0,0],kk+([rod] if rod else [])); susu.append(g); k.append(g)
    parts['susu']=susu
    k.append(M.cube('feed_pipe',[-30,22,-1],[-15,23.6,1],'copper'))
    # 구슬 통로 (구리 홈통, 수수호 위 → 시보 장치)
    k.append(M.cube('ball_track',[16,70,-2],[46,72,2],'copper')); k.append(M.cube('ball_track_wall',[16,72,1.2],[46,74,2],'copper'))
    # 시보 장치 상자
    X0,X1=40,112; D=22
    box=[M.cube('cab_low',[X0,0,-D],[X1,48,D],'wood_r',north='wood_r_d'),
         M.cube('cab_mid',[X0,48,-D],[X1,92,D],'wood_r'),
         M.cube('cab_mid_win',[X0+20,58,-D-0.3],[X1-20,84,-D+0.4],'dark'),                 # 열두 띠 인형이 나오는 창
         M.cube('cab_top_floor',[X0-2,92,-D-2],[X1+2,95,D+2],'wood_r_d'),
         M.cube('cab_top_back',[X0,95,D-3],[X1,128,D],'wood_r'),
         M.cube('cab_post_l',[X0,95,-D],[X0+3,128,-D+3],'wood_r_d'), M.cube('cab_post_r',[X1-3,95,-D],[X1,128,-D+3],'wood_r_d'),
         M.cube('cab_roof',[X0-6,128,-D-6],[X1+6,132,D+6],'gat'), M.cube('cab_roof2',[X0,132,-D+2],[X1,136,D-2],'gat'),
         M.cube('cab_band1',[X0-0.5,46,-D-0.5],[X1+0.5,48,D+0.5],'gold'), M.cube('cab_band2',[X0-0.5,88,-D-0.5],[X1+0.5,90,D+0.5],'gold')]
    for j in range(4):   # 아래층 문짝 무늬
        x=X0+6+j*16.5; box.append(M.cube('door',[x,8,-D-0.4],[x+12,40,-D+0.1],'wood_r_d'))
    k+=box
    # 위층: 종·북·징과 인형 셋 (인형은 악기 뒤에서 앞을 봄)
    top=[]
    for i,(fn,nm,xx) in enumerate([(bell,'bell',X0+14),(drum,'drum',(X0+X1)/2),(gong,'gong',X1-14)]):
        inst=fn(M,tag+nm,xx,95,-12,1.0); top.append(inst)
        d=person(M,tag+f'doll{i}_','doll',0.55,'mallet'); move(M,d,xx,95,-2); top.append(d); parts['doll'+str(i)]=d
        parts[nm]=inst
    k+=top
    # 가운데층 창 안: 시패를 든 인형 하나 (나머지 열하나는 안쪽 둥근 판 위에 숨어 있음)
    sp=person(M,tag+'zodiac_','doll_g',0.5,'sipae'); move(M,sp,(X0+X1)/2,60,-14); k.append(sp); parts['zodiac']=sp
    g=M.group(tag+'root',[0,0,0],k); parts['root']=g
    return g, parts
