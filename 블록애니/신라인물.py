"""《분황사 탑은 원래 몇 층이었을까》 블록 부품: 신라 사람들 + 분황사 모전석탑(층수 바꿔 쌓기) + 사자·사리함 등.
   블록인물.py 의 Model·move·Anim·find 를 그대로 씀.
   크기 기준: 사람 키 32 (≈1.7m) → 1m ≈ 19.  탑 3층(지금) ≈ 185 (≈9.7m)"""
import os, sys, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 블록인물 import Model, move, anchor, Anim, find, U

# ---------------- 큰 무늬 칸 (16px 보다 큰 그림: 벽돌 벽) ----------------
class BigModel(Model):
    """16px 칸은 위쪽 절반, 큰 무늬(벽돌 벽)는 아래쪽 절반에 둠"""
    def __init__(self, tex_size=512, seed=3):
        super().__init__(tex_size, seed); self._bx=0; self._by=tex_size//2; self._bh=0
    def big(self, name, w, h, fn):
        if self._bx+w>self.T: self._bx=0; self._by+=self._bh; self._bh=0
        x,y=self._bx,self._by; fn(self.im,x,y,w,h); self.sw[name]=[x,y,x+w,y+h]
        self._bx+=w; self._bh=max(self._bh,h); return name
    def _next(self):
        i=self.slot; self.slot+=1; n=self.T//16
        if i>=n*(self.T//32): raise RuntimeError('16px 칸이 모자람')
        return (i%n)*16,(i//n)*16

def brick_wall(base=(78,76,74), joint=(52,50,48), bw=8, bh=4, jit=12):
    """벽돌을 엇갈려 쌓은 벽 무늬 (돌 벽돌마다 밝기가 조금씩 다름)"""
    def fn(im,x0,y0,w,h):
        for row in range(0,h,bh):
            off=(bw//2) if (row//bh)%2 else 0
            for col in range(-off,w,bw):
                r=random.randint(-jit,jit); c=tuple(max(0,min(255,v+r)) for v in base)
                for yy in range(row,min(h,row+bh)):
                    for xx in range(max(0,col),min(w,col+bw)):
                        edge=(yy==row) or (xx==col)
                        cc=joint if edge else tuple(max(0,min(255,v+random.randint(-3,3))) for v in c)
                        im.putpixel((x0+xx,y0+yy),cc+(255,))
    return fn

# ---------------- 색 ----------------
SKIN=(232,192,152); HAIR=(30,26,26); GREY=(210,210,205)
def silla_palette(M):
    M.swatch('skin',SKIN,3); M.swatch('skin_d',(210,168,128),3)
    M.swatch('hair',HAIR,3); M.swatch('grey',GREY,4)
    M.swatch('jo_brown',(150,105,70),6); M.swatch('jo_brown_d',(120,82,55),5)      # 덕보 저고리
    M.swatch('jo_blue',(95,120,150),6); M.swatch('jo_blue_d',(75,95,120),5)        # 바우 저고리
    M.swatch('jo_beige',(215,200,170),6); M.swatch('jo_beige_d',(185,170,140),5)   # 석공
    M.swatch('jo_ochre',(190,150,80),6)
    M.swatch('pants_w',(235,230,215),4); M.swatch('pants_g',(140,135,120),5)
    M.swatch('belt',(60,45,35),4); M.swatch('belt_r',(160,50,40),4)
    M.swatch('straw',(200,175,110),6)                                               # 짚신
    M.swatch('cloth',(120,95,70),5)                                                 # 두건
    M.swatch('monk',(130,130,128),5); M.swatch('monk_d',(105,105,103),5); M.swatch('kasa',(150,70,45),5)
    M.swatch('robe_w',(232,232,225),4); M.swatch('gat',(25,25,28),3)
    M.swatch('iron',(70,72,78),5); M.swatch('wood',(130,90,55),6); M.swatch('wood_d',(95,65,40),5)
    def face(name,hair,beard=None,young=False,brow=None,bald=False):
        def fn(d,x,y):
            d.rectangle([x,y,x+15,y+15],fill=SKIN)
            if not bald: d.rectangle([x,y,x+15,y+2],fill=hair)
            for ex in (3,9):
                d.rectangle([x+ex,y+6,x+ex+3,y+8],fill=(255,255,255)); d.rectangle([x+ex+1,y+6,x+ex+2,y+8],fill=(25,20,20))
                d.rectangle([x+ex,y+5,x+ex+3,y+5],fill=brow or hair)
            d.rectangle([x+7,y+9,x+8,y+10],fill=(205,160,120))
            if beard: d.rectangle([x+3,y+11,x+12,y+15],fill=beard); d.rectangle([x+6,y+12,x+9,y+12],fill=(150,70,60))
            else: d.rectangle([x+6,y+12,x+9,y+12],fill=(170,80,70))
            if young: d.rectangle([x+2,y+10,x+3,y+10],fill=(240,150,130)); d.rectangle([x+12,y+10,x+13,y+10],fill=(240,150,130))
        M.paint(name,fn)
    face('f_bau',HAIR,young=True); face('f_bau_old',HAIR,beard=(45,38,35)); face('f_deokbo',GREY,beard=GREY,brow=GREY)
    face('f_man',HAIR); face('f_man2',HAIR,beard=HAIR); face('f_monk',HAIR,bald=True); face('f_seonbi',HAIR,beard=HAIR)

PEOPLE={  # kind: (얼굴, 저고리, 저고리 어두운, 바지, 띠, 머리)
 'bau':('f_bau','jo_blue','jo_blue_d','pants_w','belt','braid'),
 'bau_old':('f_bau_old','jo_blue','jo_blue_d','pants_w','belt','topknot'),
 'deokbo':('f_deokbo','jo_brown','jo_brown_d','pants_g','belt','dugeon_grey'),
 'man':('f_man','jo_beige','jo_beige_d','pants_g','belt','dugeon'),
 'man2':('f_man2','jo_ochre','jo_beige_d','pants_w','belt_r','topknot'),
 'monk':('f_monk','monk','monk_d','monk','monk_d','bald'),
 'seonbi':('f_seonbi','robe_w','robe_w','robe_w','gat','gat'),
}

def person(M, tag, kind='man', s=1.0, tool=None):
    """신라 사람 블록 (키 32*s). 앞 = -z.  tool: 'chisel'(오른손 망치·왼손 정) / 'staff'(지팡이) / 'brick'(두 손에 벽돌)"""
    c=lambda name,fr,to,col,**f: M.cube(name,[v*s for v in fr],[v*s for v in to],col,**f)
    O=lambda v:[x*s for x in v]
    fc,jo,jod,pt,bt,hair=PEOPLE[kind]
    hc='grey' if kind=='deokbo' else 'hair'
    legL=M.group(tag+'leg_left',O([2,12,0]),[c('leg',[0,1.6,-2],[4,12,2],pt), c('shoe',[-0.2,0,-2.8],[4.2,1.6,2.2],'straw')])
    legR=M.group(tag+'leg_right',O([-2,12,0]),[c('leg',[-4,1.6,-2],[0,12,2],pt), c('shoe',[-4.2,0,-2.8],[0.2,1.6,2.2],'straw')])
    long_robe = kind in ('monk','seonbi')
    armL_k=[c('sleeve',[4,15,-2.2],[8.2,24,2.2],jo), c('hand',[4.6,12,-1.6],[7.6,15,1.6],'skin')]
    armR_k=[c('sleeve',[-8.2,15,-2.2],[-4,24,2.2],jo), c('hand',[-7.6,12,-1.6],[-4.6,15,1.6],'skin')]
    hl=M.group(tag+'hand_l',O([6,12.5,0]),[]); hr=M.group(tag+'hand_r',O([-6,12.5,0]),[])
    if tool=='chisel':
        armR_k+= [c('hammer_h',[-6.6,10,-7],[-5.4,13,0],'wood'), c('hammer_s',[-7.8,9.5,-9.5],[-4.2,13.5,-6.5],'iron')]
        armL_k+= [c('chisel',[5.5,11,-6],[6.7,13,-1],'iron')]
    if tool=='staff':
        armR_k+= [c('staff',[-7,-1.5,-4],[-5,26,-2],'wood_d')]
    if tool=='brick':
        armL_k+= [c('brick',[-6,12.5,-9],[6,15.5,-3],'stone')] if 'stone' in M.sw else []
    armL=M.group(tag+'arm_left',O([6,22,0]),armL_k+[hl]); armR=M.group(tag+'arm_right',O([-6,22,0]),armR_k+[hr])
    # 몸: 저고리(엉덩이까지) + 띠, 승복·도포는 무릎 아래까지
    body=[c('torso',[-4.2,12,-2.2],[4.2,24,2.2],jo,north=jo), c('belt',[-4.4,15,-2.4],[4.4,16.4,2.4],bt)]
    body+= [c('collar',[-1.2,20,-2.5],[1.2,24,-2.3],jod)]            # 깃 (가운데 여밈)
    if long_robe:
        body+= [c('robe_low',[-4.6,4,-2.6],[4.6,13,2.6],jo)]
        if kind=='monk': body+= [c('kasa',[-4.5,13,-2.5],[1,23,2.5],'kasa')]
    else:
        body+= [c('jo_low',[-4.4,11,-2.4],[4.4,13.5,2.4],jo)]
    hk=[c('head',[-4,24,-4],[4,32,4],'skin',north=fc,up=hc if hair!='bald' else 'skin',south=hc if hair!='bald' else 'skin')]
    if hair!='bald':
        hk+= [c('hair_back',[-4.2,25.5,1.2],[4.2,32.2,4.2],hc), c('hair_top',[-4.2,31.2,-4.2],[4.2,32.4,4.2],hc),
              c('hair_side_l',[3.9,28,-1],[4.2,32,4],hc), c('hair_side_r',[-4.2,28,-1],[-3.9,32,4],hc)]
    if hair=='braid':      # 아이: 뒤로 땋아 내린 머리
        hk+= [c('braid',[-1,16,4],[1,26,5.4],'hair'), c('braid_tie',[-1.3,18,3.9],[1.3,19.2,5.7],'belt_r')]
    if hair=='topknot':
        hk+= [c('topknot',[-1.5,32,-0.5],[1.5,35.5,2.5],hc), c('band',[-4.3,29.5,-4.3],[4.3,30.6,4.3],'belt')]
    if hair in ('dugeon','dugeon_grey'):   # 두건: 머리를 감싼 천 + 뒤로 늘어진 끈
        hk+= [c('dugeon',[-4.4,29,-4.4],[4.4,33,4.4],'cloth'), c('dugeon_tail',[-1.5,23,4.2],[1.5,29,5],'cloth')]
        if kind=='deokbo': hk+= [c('beard_long',[-3,20,-4.6],[3,25,-3.8],'grey')]
    if hair=='gat':        # 갓: 넓고 납작한 챙 + 좁고 높은 통
        hk+= [c('topknot',[-1.5,32,-0.5],[1.5,34,2.5],'hair'), c('gat_brim',[-9,31.6,-9],[9,32.4,9],'gat'), c('gat_crown',[-3.4,32.4,-3.4],[3.4,38,3.4],'gat')]
    if kind=='bau_old':    # 수염 조금
        hk+= [c('beard_s',[-2.5,23,-4.4],[2.5,25,-3.8],'hair')]
    head=M.group(tag+'head',O([0,24,0]),hk)
    bod=M.group(tag+'body',O([0,12,0]),body+[head,armL,armR])
    return M.group(tag+'root',[0,0,0],[bod,legL,legR])

# ---------------- 탑 ----------------
def pagoda_palette(M):
    M.swatch('stone',(92,88,84),10); M.swatch('stone_d',(70,67,64),8); M.swatch('stone_l',(118,113,106),10)
    M.swatch('granite',(190,185,175),8); M.swatch('granite_d',(160,155,148),8)
    M.swatch('rock',(140,132,118),14); M.swatch('rock_d',(112,105,94),12); M.swatch('dark',(25,22,22),3)
    M.swatch('ghost',(150,200,240),4); M.swatch('ghost_d',(120,170,215),4)
    M.swatch('relief',(110,104,96),6); M.swatch('relief_l',(130,124,115),6)
    M.big('wall', 128, 64, brick_wall(base=(92,88,84),joint=(62,59,56)))
    M.big('wall_l', 128, 64, brick_wall(base=(96,93,90),joint=(62,60,58)))
    M.big('course', 128, 8, brick_wall(base=(92,88,84),joint=(62,59,56),bw=8,bh=4))
    M.big('wall_c', 128, 64, brick_wall(base=(170,105,70),joint=(120,75,50)))
    M.big('course_c', 128, 8, brick_wall(base=(170,105,70),joint=(120,75,50),bw=8,bh=4))
    M.big('wall_g', 128, 64, brick_wall(base=(160,205,240),joint=(115,160,205),jit=6))
    M.big('course_g', 128, 8, brick_wall(base=(160,205,240),joint=(115,160,205),bw=8,bh=4,jit=6))

def floor_dims(n, i):
    """층 i(0 부터)의 몸 폭·몸 높이·지붕 내밀기.  1층은 크고, 위로 갈수록 좁아지고 낮아짐"""
    if i==0: return 128, 56, 14
    w=112*(0.93**(i-1)); h=24*(0.95**(i-1)); return w, h, 11*(0.95**(i-1))

def roof(M, cx, y, cz, w, out, ghost=False, name='roof', col=None):
    """계단 지붕: 아랫면 내어쌓기(바깥으로 한 줄씩) → 윗면 들여쌓기(안으로).  돌아오는 값: (상자들, 윗면 높이, 윗면 폭)"""
    col=col or ('course_g' if ghost else 'course'); k=[]; step=2.0
    n_out=max(3,int(round(out/2.3))); dw=out/n_out
    for j in range(n_out):     # 아랫면: 거꾸로 선 계단
        hw=w/2+dw*(j+1)
        k.append(M.cube(name+'_o',[cx-hw,y,cz-hw],[cx+hw,y+step,cz+hw],col)); y+=step
    top_w=w*0.86; n_in=max(4,int(round((w/2+out-top_w/2)/3.2))); din=(w/2+out-top_w/2)/n_in
    for j in range(n_in):      # 윗면: 안으로 들이며 좁혀 감
        hw=w/2+out-din*(j+1)
        k.append(M.cube(name+'_i',[cx-hw,y,cz-hw],[cx+hw,y+step*0.8,cz+hw],col)); y+=step*0.8
    return k, y, top_w

def lion(M, tag, x, y, z, yaw=0, S=1.0):
    """기단 귀퉁이 돌사자 (화강암, 앉은 모습).  앞 = -z"""
    c=lambda n,fr,to,col: M.cube(n,[x+v*S for v in fr[:1]]+[y+fr[1]*S]+[z+fr[2]*S],[x+to[0]*S,y+to[1]*S,z+to[2]*S],col)
    k=[c('l_body',[-5,0,-3],[5,9,9],'granite'), c('l_chest',[-5,0,-7],[5,13,-2],'granite'),
       c('l_head',[-5.5,11,-10],[5.5,20,-1],'granite_d'), c('l_mane',[-6.5,10,-4],[6.5,21,0],'granite_d'),
       c('l_nose',[-2,13,-11.5],[2,16,-10],'granite'), c('l_eye1',[-4,16.5,-10.3],[-2,18,-10],'dark'), c('l_eye2',[2,16.5,-10.3],[4,18,-10],'dark'),
       c('l_leg1',[-5,0,-9],[-2,4,-6],'granite'), c('l_leg2',[2,0,-9],[5,4,-6],'granite'), c('l_tail',[-1,6,9],[1,12,11],'granite_d')]
    return M.group(tag,[x,y,z],k,rotation=(0,yaw,0))

def guardian(M, cx, cy, cz, face, S=1.0):
    """금강역사 부조 (벽에서 살짝 튀어나온 힘센 장사).  face: 벽이 보는 방향 'n','s','e','w'"""
    k=[]
    def box(n,a,b,col):   # a,b = (가로, 세로, 튀어나옴) 지역 좌표 → 벽 방향에 맞춰
        (u0,v0,d0),(u1,v1,d1)=a,b
        if face=='n': fr=[cx+u0,cy+v0,cz-d1]; to=[cx+u1,cy+v1,cz-d0]
        elif face=='s': fr=[cx-u1,cy+v0,cz+d0]; to=[cx-u0,cy+v1,cz+d1]
        elif face=='e': fr=[cx+d0,cy+v0,cz+u0]; to=[cx+d1,cy+v1,cz+u1]
        else: fr=[cx-d1,cy+v0,cz-u1]; to=[cx-d0,cy+v1,cz-u0]
        k.append(M.cube(n,fr,to,col))
    s=S
    box('g_leg1',(-3.4*s,0,0),(-0.6*s,9*s,1.4),'relief'); box('g_leg2',(0.6*s,0,0),(3.4*s,9*s,1.4),'relief')
    box('g_skirt',(-3.8*s,7*s,0),(3.8*s,11*s,1.7),'relief_l')
    box('g_body',(-3.6*s,11*s,0),(3.6*s,19*s,1.8),'relief')
    box('g_arm1',(-6*s,11*s,0),(-3.6*s,18*s,2.0),'relief')                       # 한 팔은 아래로 주먹
    box('g_arm2u',(3.6*s,16*s,0),(6*s,19*s,2.0),'relief'); box('g_arm2',(5*s,19*s,0),(7.4*s,24*s,2.0),'relief')   # 한 팔은 위로 꺾어 듦
    box('g_fist',(4.6*s,23.5*s,0),(7.8*s,26*s,2.3),'relief_l')
    box('g_head',(-2.4*s,19*s,0),(2.4*s,24*s,2.0),'relief_l')
    box('g_eye1',(-1.8*s,21.6*s,2.0),(-0.6*s,22.6*s,2.2),'dark'); box('g_eye2',(0.6*s,21.6*s,2.0),(1.8*s,22.6*s,2.2),'dark')
    box('g_hair',(-2.6*s,24*s,0),(2.6*s,25.5*s,1.8),'relief')
    return k

def pagoda(M, tag, floors=3, ghost_from=None, base=True, doors=True, lions=True, finial=True, base_w=250, style='stone'):
    """분황사 모전석탑.  floors: 층 수.  ghost_from: 이 층부터는 하늘색(상상으로 그려 본 층).
       돌아오는 값: (묶음, 층 묶음 목록, 꼭대기 높이).  층 묶음은 따로 크기 0/1 로 숨겼다 보였다 할 수 있음"""
    top=[]; y=0
    if base:
        bk=[M.cube('base',[-base_w/2,0,-base_w/2],[base_w/2,19,base_w/2],'rock',up='rock')]
        for j,(x,z) in enumerate([(-1,-1),(1,-1),(-1,1),(1,1)]):   # 큰 자연석 테두리
            bk.append(M.cube('base_edge',[-base_w/2-2 if x<0 else base_w/2-10,0,-base_w/2-2 if z<0 else base_w/2-10],
                                         [-base_w/2+10 if x<0 else base_w/2+2,21,-base_w/2+10 if z<0 else base_w/2+2],'rock_d'))
        if lions:
            for j,(x,z,yaw) in enumerate([(-1,-1,45),(1,-1,-45),(-1,1,135),(1,1,-135)]):
                bk.append(lion(M,tag+f'lion{j}',x*(base_w/2-14),19,z*(base_w/2-14),yaw))
        top.append(M.group(tag+'base',[0,0,0],bk)); y=19
    fl=[]
    for i in range(floors):
        w,h,out=floor_dims(floors,i); g=(ghost_from is not None and i>=ghost_from); y0=y
        wall='wall_g' if g else {'stone':'wall','clay':'wall_c'}[style]
        k=[M.cube('body',[-w/2,y,-w/2],[w/2,y+h,w/2],wall)]
        if i==0 and doors:   # 1층 네 면: 돌문(감실) + 양옆 금강역사
            dw,dh=26,32
            for f in 'nsew':
                if f=='n': fr,to=[-dw/2,y+6,-w/2-0.6],[dw/2,y+6+dh,-w/2+0.2]
                elif f=='s': fr,to=[-dw/2,y+6,w/2-0.2],[dw/2,y+6+dh,w/2+0.6]
                elif f=='e': fr,to=[w/2-0.2,y+6,-dw/2],[w/2+0.6,y+6+dh,dw/2]
                else: fr,to=[-w/2-0.6,y+6,-dw/2],[-w/2+0.2,y+6+dh,dw/2]
                k.append(M.cube('door_frame',fr,to,'granite'))
                inset=lambda a,b: (a,b)
                if f in 'ns':
                    zz=-w/2-0.9 if f=='n' else w/2+0.9; sg=-1 if f=='n' else 1
                    k.append(M.cube('door_l',[-dw/2+2,y+8,min(zz,zz-sg*0.0)-0.3],[-0.4,y+4+dh,max(zz,zz)+0.3],'granite_d'))
                    k.append(M.cube('door_r',[0.4,y+8,min(zz,zz)-0.3],[dw/2-2,y+4+dh,max(zz,zz)+0.3],'granite_d'))
                else:
                    xx=w/2+0.9 if f=='e' else -w/2-0.9
                    k.append(M.cube('door_l',[xx-0.3,y+8,-dw/2+2],[xx+0.3,y+4+dh,-0.4],'granite_d'))
                    k.append(M.cube('door_r',[xx-0.3,y+8,0.4],[xx+0.3,y+4+dh,dw/2-2],'granite_d'))
                for side in (-1,1):   # 금강역사 두 분
                    off=side*(dw/2+13)
                    if f=='n': k+= guardian(M,off,y+4,-w/2,'n',1.0)
                    elif f=='s': k+= guardian(M,-off,y+4,w/2,'s',1.0)
                    elif f=='e': k+= guardian(M,w/2,y+4,off,'e',1.0)
                    else: k+= guardian(M,-w/2,y+4,-off,'w',1.0)
        y+=h
        rk,y,_=roof(M,0,y,0,w,out,ghost=g,col=('course_c' if style=='clay' and not g else None))
        k+=rk
        gr=M.group(tag+f'floor{i+1}',[0,y0,0],k); fl.append(gr)
    if finial:   # 3층(맨 위) 지붕 위 화강암 꽃 장식
        fk=[M.cube('fin_base',[-14,y,-14],[14,y+4,14],'granite_d'), M.cube('fin_bud',[-8,y+4,-8],[8,y+12,8],'granite'),
            M.cube('fin_top',[-3,y+12,-3],[3,y+16,3],'granite_d')]
        for dx,dz in [(-1,0),(1,0),(0,-1),(0,1)]:
            fk.append(M.cube('fin_petal',[dx*9-3+min(0,dx)*2,y+4,dz*9-3+min(0,dz)*2],[dx*9+3+max(0,dx)*2,y+9,dz*9+3+max(0,dz)*2],'granite'))
        fin=M.group(tag+'finial',[0,y,0],fk); fl.append(fin); y+=16
    top+= fl
    return M.group(tag+'root',[0,0,0],top), fl, y

def stone_pile(M, tag, x, z, n=40, r=30, seed=1, ghost=False):
    """벽돌 모양 돌 더미 (깎아 둔 돌 / 무너진 돌)"""
    rnd=random.Random(seed); k=[]
    for i in range(n):
        a=rnd.uniform(0,6.283); d=rnd.uniform(0,r)*(1-i/n*0.5); lvl=int(i/n*4)
        px=x+d*__import__('math').cos(a); pz=z+d*__import__('math').sin(a); py=lvl*2.8
        if rnd.random()<0.5: k.append(M.cube('st',[px-4,py,pz-1.5],[px+4,py+2.6,pz+1.5],'stone_l' if rnd.random()<0.4 else 'stone'))
        else: k.append(M.cube('st',[px-1.5,py,pz-4],[px+1.5,py+2.6,pz+4],'stone_l' if rnd.random()<0.4 else 'stone'))
    return M.group(tag,[x,0,z],k)

def brick(M, tag, x, y, z, along='x', col='stone'):
    """돌 벽돌 하나 (길이 8, 높이 2.6, 폭 3)"""
    if along=='x': return M.group(tag,[x,y,z],[M.cube('b',[x-4,y,z-1.5],[x+4,y+2.6,z+1.5],col)])
    return M.group(tag,[x,y,z],[M.cube('b',[x-1.5,y,z-4],[x+1.5,y+2.6,z+4],col)])
