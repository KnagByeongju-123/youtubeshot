"""《마지막 잎새》 장면 모형 + 움직임 (세트 A, 0~45초) → 연재/마지막잎새/장면/A_잎새.bbmodel, 세트정보.json
   나무 인형. 실제 세계 좌표, 위치 움직임은 x 를 뒤집어 넣음(P 가 처리).  yaw: 0 = -z, +90 = +x, 180 = +z
   방: 바닥 x -32..32, z -26..26, 오른쪽 벽(x 32) 창문(z -8..8, y 20..38), 왼쪽 벽 앞쪽이 열린 문. 침대 x -6..20 (머리 쪽 -x)
   골목: x 34..70, 건너편 벽돌 벽 앞면 x = 70 (담쟁이 잎은 이 벽에)"""
import sys, os, json, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 잎새인물 import *
OUT=sys.argv[1] if len(sys.argv)>1 else '/home/user/youtubeshot/연재/마지막잎새/장면'
os.makedirs(OUT,exist_ok=True)
L=45.0; random.seed(7)
M=Model(512); palette_all(M)
def brick_fn(base,mortar):
    def fn(x,y):
        if y%4==3: return mortar
        off=0 if (y//4)%2==0 else 4
        return mortar if (x+off)%8==7 else base
    return fn
M.swatch('brick',brick_fn((168,82,62),(200,190,175)),6); M.swatch('cobble',lambda x,y:(150,145,140) if (x//4+y//4)%2 else (132,128,124),6)
M.swatch('snow',(246,248,252),3); M.swatch('wallpaper',lambda x,y:(238,226,200) if x%6 else (226,210,180),3)
M.swatch('floor',wood_fn((175,128,82),(140,100,62),71),4); M.swatch('frame',wood_fn((120,82,52),(92,62,38),72),3)
M.swatch('blanket',(222,150,140),5); M.swatch('sheet',(246,244,238),3)
M.swatch('ext',(214,200,178),5); M.swatch('roof',(120,70,58),5); M.swatch('vine',(98,72,50),3)
M.swatch('canvas',(250,248,240),2); M.swatch('rug',(150,70,60),4); M.swatch('far',(170,160,150),3)
M.swatch('l_leaf2',(95,160,70),3); M.swatch('l_leaf_r',(200,90,50),3); M.swatch('l_leaf_young',(150,200,90),3); M.swatch('petal',(235,90,110),2)
A=Anim(L); top=[]
X=lambda n,fr,to,col,**f: M.cube(n,fr,to,col,**f)

def P(g, pts, interp='linear'): A.add(g,'position',[(t,(-v[0],v[1],v[2])) for t,v in pts],interp)
def R(g, pts, interp='linear'): A.add(g,'rotation',pts,interp)
def show(g, spans, eps=0.02):
    pts=[(0,0)]
    for a,b in spans: pts+= [(max(0,a-eps),0),(a,1),(b,1),(b+eps,0)]
    A.add(g,'scale',[(t,(v,v,v)) for t,v in pts])
def grow(g, t0, t1, t_end=45):
    """그려지며 커짐 (0 → 1)"""
    A.add(g,'scale',[(0,(0,0,0)),(t0,(0,0,0)),(t0+(t1-t0)*0.5,(0.6,0.6,0.6)),(t1,(1,1,1)),(t_end,(1,1,1))])
def yaw(g, pts, interp='linear'): R(g,[(t,(0,y,0)) for t,y in pts],interp)
def part(g, name): return find(g, g['name'].replace('root',name))
def walk(p, t0, t1, amp=26, period=0.6, arms=(True,True)):
    legL,legR,armL,armR=[part(p,n) for n in ('leg_left','leg_right','arm_left','arm_right')]
    t=t0; s=1; pts=[]
    while t<t1-1e-6: pts.append((t+period/4,s)); t+=period/2; s=-s
    gs=[(legL,1),(legR,-1)]+([(armL,-1)] if arms[0] else [])+([(armR,1)] if arms[1] else [])
    for g,sg in gs:
        R(g,[(t0,(0,0,0))]+[(tt,(sg*ss*amp,0,0)) for tt,ss in pts if tt<t1]+[(t1,(0,0,0))],'catmullrom')

# ---------------- 바닥·방 ----------------
W=[X('far',[-3000,-20,-3000],[3000,-0.4,3000],'far'),
   X('floor',[-32,-0.4,-26],[32,0.1,26],'floor'), X('rug',[-20,0.1,-16],[-4,0.3,-4],'rug'),
   X('back',[-33.9,0.05,26],[33.9,49.95,28],'wallpaper'),   # 옆벽·바닥·천장과 같은 자리 면이 없게 (지글거림)
   X('left',[-34,0,-10],[-32,50,27.9],'wallpaper'), X('left_top',[-34,32,-26],[-32,50,-10],'wallpaper'),
   X('ceil',[-34,50,-26],[34,52,28],'ext'),
   # 오른쪽 벽 (창문 구멍 z -8..8, y 20..38)
   X('r_lo',[32,0,-26],[34,20,28],'wallpaper'), X('r_hi',[32,38,-26],[34,50,28],'wallpaper'),
   X('r_f',[32,20,-26],[34,38,-8],'wallpaper'), X('r_b',[32,20,8],[34,38,28],'wallpaper'),
   # 창틀: 벽 구멍보다 조금 크게·안쪽으로 나와서 벽 면과 같은 자리에 겹치지 않게 (사용자 지적 2026-11-15: 창문틀 지글거림)
   X('win_sill',[30,18.8,-9.3],[37,20.2,9.3],'frame'), X('win_top',[31.4,37.8,-9.2],[36,39.3,9.2],'frame'),
   X('win_l',[31.6,19.9,-9.1],[34.6,38.1,-7.85],'frame'), X('win_r',[31.6,19.9,7.85],[34.6,38.1,9.1],'frame'),
   ]
# 침대 (머리 쪽 -x, 다리 쪽 +x 창문 쪽)
W+= [X('head_b',[-8,0,-7.5],[-6,18,7.5],'frame'), X('foot_b',[19,0,-7.5],[21,11,7.5],'frame'),
     X('bed_frame',[-6,3,-7.5],[19,7,7.5],'frame'), X('mattress',[-6,7,-7],[19,9,7],'sheet'),
     X('pillow',[-6,9,-4.5],[-2.5,12.5,4.5],'sheet'), X('blanket',[-0.5,9,-7.2],[17,13.8,7.2],'blanket'),
     X('table',[-15,0,9],[-9,10,15],'frame'), X('cup',[-13,10,11],[-11,12.5,13],'canvas')]
# 화가의 집: 이젤 + 그림, 벽에 걸린 그림
W+= [X('easel_l',[-26,0,16],[-25,26,17],'frame'), X('easel_r',[-19,0,16],[-18,26,17],'frame'), X('easel_b',[-22.8,0,19],[-22.2,24,20],'frame'),
     X('canvas',[-27,12,15],[-17,24,15.8],'canvas'), X('canvas_sun',[-24,18,14.6],[-21,21,15],'l_yellow'), X('canvas_hill',[-26,13,14.6],[-18,16,15],'l_leaf'),
     X('pic_f',[-12,26,25.4],[4,38,26],'frame'), X('pic',[-11,27,25.2],[3,37,25.4],'l_blue'), X('pic2',[-9,28,25.0],[-2,32,25.2],'l_leaf2')]
# ---------------- 골목 ----------------
for zz in range(-120,120,12):     # 돌바닥: 작은 조각으로 (무늬가 한 장으로 늘어나지 않게)
    for xx in (34,46,58): W.append(X('cob',[xx,-0.3,zz],[xx+12,0.05,zz+12],'cobble'))
W+= [X('alley',[34,-0.6,-200],[70,-0.3,200],'cobble'),
     X('bld_f',[32,0,-200],[34,50,-26],'ext'), X('bld_b',[32,0,28],[34,50,200],'ext'), X('bld_top',[30,50.1,-200],[36,53,200],'roof'),
     ]
W+= [X('brick_core',[70.4,0,-200],[74,90,200],'brick'), X('brick_top',[69,90,-200],[75,92,200],'roof')]
for zz in range(-104,104,16):      # 벽돌 벽 앞면: 16x16 조각 (벽돌 하나 8x4)
    for yy in range(0,90,16): W.append(X('brk',[70,yy,zz],[70.4,min(yy+16,90),zz+16],'brick'))
top.append(M.group('world',[0,0,0],W))

# 눈 (겨울에만): 골목 바닥 + 창턱
snow=M.group('snow',[0,0,0],[X('snow_g',[34,0.05,-200],[70,0.7,200],'snow'), X('snow_sill',[34.6,20.1,-9.0],[36.9,20.9,9.0],'snow'), X('snow_top',[69,92,-200],[75,93.5,200],'snow')])
top.append(snow); show(snow,[(0,23.97),(31.8,45)])

# ---------------- 담쟁이 (벽 앞면 x=70) ----------------
WX=69.7
def leafx(name, y, z, col, s=1.0, flat=False):
    """벽(x=70)에 붙은 담쟁이 잎 하나 (세 갈래).  묶음 원점 = 잎 가운데"""
    sx=0.10 if flat else 0.28; x=WX+(0.15 if flat else 0)
    k=[sphere(M,name+'_m',[x,y+0.6*s,z],1.25*s,col,seg=10,rings=6,sx=sx), sphere(M,name+'_l',[x,y-0.1*s,z-1.0*s],0.9*s,col,seg=8,rings=6,sx=sx),
       sphere(M,name+'_r',[x,y-0.1*s,z+1.0*s],0.9*s,col,seg=8,rings=6,sx=sx)]
    if not flat: k.append(cyl(M,name+'_st',[x+0.1,y-0.6*s,z],[WX+0.25,y-1.8*s,z],0.13*s,0.1*s,'vine',seg=6))
    return M.group(name,[x,y,z],k)
# 줄기 (늘 있음)
V=[]
for i,(a,b) in enumerate([((0,-22),(14,-16)),((14,-16),(30,-8)),((30,-8),(44,2)),((44,2),(56,-4)),((30,-8),(38,-18)),((22,-12),(34,8)),((34,8),(46,12)),
                          ((0,14),(16,10)),((16,10),(28,4)),((28,4),(36,0)),((38,-18),(50,-14)),((44,2),(48,14))]):
    V.append(cyl(M,f'vine{i}',[WX+0.15,a[0],a[1]],[WX+0.15,b[0],b[1]],0.2,0.17,'vine',seg=6))
top.append(M.group('vines',[0,0,0],V))

def fall(g, t0, dy, dz, dur=2.2, spin=1):
    """떨어지는 잎: t0 에 벽에서 떨어져 흔들리며 내려옴 → 땅에서 사라짐"""
    pts=[(0,(0,0,0)),(t0-0.08,(0,0,0)),(t0,(0,0,0))]; n=8   # 떨어지기 전엔 꼼짝 않게 (곡선이 미리 휘지 않게)
    for i in range(1,n+1):
        f=i/n; pts.append((t0+dur*f,(-3-6*f, -dy*f, dz*f+2.2*math.sin(f*7))))
    P(g,pts,'catmullrom')
    R(g,[(0,(0,0,0)),(t0-0.08,(0,0,0)),(t0,(0,0,0))]+[(t0+dur*i/n,(25*math.sin(i*1.3)*spin, 0, 40*i*spin)) for i in range(1,n+1)],'catmullrom')
    return t0+dur
# 첫 겨울 잎 넷 (마지막 잎 = W4, 폭풍에 떨어짐)
W1=leafx('W1',40,-6,'l_leaf_y',1.15); W2=leafx('W2',31,7,'l_leaf_y',1.1); W3=leafx('W3',44,6,'l_leaf_y',1.1); W4=leafx('W4',36,0,'l_leaf',1.3)
top+= [W1,W2,W3,W4]
e1=fall(W1,1.6,38,4); e2=fall(W2,4.3,29,-3); e3=fall(W3,9.4,42,-2)
show(W1,[(0,e1)]); show(W2,[(0,e2)]); show(W3,[(0,e3)])
# W4: 바람에 떨다가 12.6 에 날아감
tr=[(11.0,(0,0,0))]+[(11.0+i*0.12,(0,0,(14 if i%2 else -14)*(1+i*0.06))) for i in range(1,14)]
R(W4,[(0,(0,0,0)),(10.9,(0,0,0))]+tr+[(12.6,(0,0,20)),(13.4,(160,40,420))],'catmullrom')
P(W4,[(0,(0,0,0)),(12.5,(0,0,0)),(12.6,(0,0,0)),(13.4,(-16,6,-26))],'catmullrom'); show(W4,[(0,13.4)])
# 그린 잎 P1 (할아버지, 16.4~18.4 에 그려짐) — W4 자리
P1=leafx('P1',36,0,'l_leaf_paint',1.3,flat=True); top.append(P1); grow(P1,16.4,18.4)
# 두 번째 겨울 잎 (33~)
W5=leafx('W5',41,-5,'l_leaf_y',1.1); W6=leafx('W6',30,6,'l_leaf_y',1.1); top+= [W5,W6]
e5=fall(W5,34.4,39,3); e6=fall(W6,37.2,28,-2); show(W5,[(31.8,e5)]); show(W6,[(31.8,e6)])
# 그린 잎 P2 (어른 소녀, 39.7~40.9) — P1 옆
P2=leafx('P2',36,-6,'l_leaf_paint',1.3,flat=True); top.append(P2); grow(P2,39.7,40.9)
# 그린 꽃 (봄, 소녀가 할아버지와 함께) — 아래쪽
FL=M.group('flower',[WX+0.2,15,-6],[cyl(M,'f_stem',[WX+0.2,9,-6],[WX+0.2,15,-6],0.25,0.25,'l_leaf_paint',seg=6)]+
     [sphere(M,f'f_p{i}',[WX+0.2,15+1.3*math.cos(i*1.2566),-6+1.3*math.sin(i*1.2566)],0.9,'petal',seg=8,rings=6,sx=0.12) for i in range(5)]+
     [sphere(M,'f_c',[WX+0.1,15,-6],0.6,'l_yellow',seg=8,rings=6,sx=0.15), sphere(M,'f_leaf',[WX+0.2,11,-4.8],0.8,'l_leaf_paint',seg=8,rings=6,sx=0.12,sy=0.5)])
top.append(FL); grow(FL,26.4,28.4)
# 계절 잎: 봄(어린 잎) 24~29, 여름(무성) 29~30.4, 가을(노랑·빨강) 30.4~31.8
rnd=random.Random(11)
def leafset(name, n, cols, s0, s1):
    k=[]
    for i in range(n):
        for _ in range(40):
            y=rnd.uniform(8,56); z=rnd.uniform(-26,24)
            if not (abs(y-36)<4 and -10<z<4) and not (abs(y-15)<5 and -10<z<-2): break   # 그린 잎·꽃은 가리지 않게
        k.append(leafx(f'{name}{i}',y,z,rnd.choice(cols),rnd.uniform(s0,s1)))
    return M.group(name,[0,0,0],k)
SP=leafset('sp',16,['l_leaf_young'],0.7,0.95); SU=leafset('su',30,['l_leaf','l_leaf2'],1.0,1.35); AU=leafset('au',22,['l_leaf_y','l_leaf_r','l_leaf_y'],1.0,1.3)
top+= [SP,SU,AU]; show(SP,[(24.0,29.0)]); show(SU,[(29.0,30.4)]); show(AU,[(30.4,31.8)])

# ---------------- 사다리·등불 (밤) ----------------
LB=(46.0,0.0); LT=(68.6,40.0)       # 사다리 밑(x,y) → 위(x,y), 벽에 기댐
def lx(h): return LB[0]+(LT[0]-LB[0])*h/LT[1]
LD=[]
for zz in (-6.5,6.5): LD.append(cyl(M,'rail',[LB[0],0,zz],[LT[0],LT[1],zz],0.6,0.6,'l_ladder',seg=6))
for h in range(5,40,5): LD.append(cyl(M,'rung',[lx(h),h,-6.5],[lx(h),h,6.5],0.45,0.45,'l_ladder',seg=6))
lad=M.group('ladder',[LB[0],0,0],LD); top.append(lad); show(lad,[(13.4,19.37),(38.0,41.17)])
lp=lamp(M,'n1_',[52,0,-11],1.6); top.append(lp); show(lp,[(13.4,19.37)])
lp2=lamp(M,'n2_',[52,0.7,-11],1.6); top.append(lp2); show(lp2,[(38.0,41.17)])

# ---------------- 인물 ----------------
GS=0.72
girl=person(M,'gl_','girl',GS); gp=person(M,'gp_','grandpa',1.0); go=person(M,'go_','grandpa_old',1.0); wm=person(M,'wm_','woman',1.0)
top+= [girl,gp,go,wm]
def brush_down(M, tag, hand, s=1.0):
    """붓을 손 끝에서 아래로 (팔을 앞으로 들면 붓끝이 벽을 향함)"""
    x,y,z=hand
    return M.group(tag+'brushd',[x,y,z],[cyl(M,'bd_stick',[x,y+0.6*s,z],[x,y-3.4*s,z],0.3*s,0.3*s,'wood_dk',seg=8),
           cyl(M,'bd_fer',[x,y-3.4*s,z],[x,y-4.0*s,z],0.34*s,0.34*s,'l_metal',seg=8), cyl(M,'bd_tip',[x,y-4.0*s,z],[x,y-5.2*s,z],0.38*s,0.05*s,'l_leaf_paint',seg=8)])
GPR=part(gp,'arm_right'); WMR=part(wm,'arm_right'); GLR=part(girl,'arm_right')
bg=brush_down(M,'gp_',[-5.4,11.0,0],1.0); find(gp,'gp_hand_r')['children'].append(bg); show(bg,[(13.4,19.4),(24.0,25.6)])
bw=brush_down(M,'wm_',[-5.4,11.0,0],1.0); find(wm,'wm_hand_r')['children'].append(bw); show(bw,[(38.0,41.2)])
bgl=brush_down(M,'gl_',[-5.4*GS,11.0*GS,0],GS); find(girl,'gl_hand_r')['children'].append(bgl); show(bgl,[(25.6,29.0)])

def sit(p, s, t0, t1, x=0.0):
    """침대에 기대앉음 (다리는 이불 속, 창문 +x 를 봄)"""
    y=9.0-12*s+1.4
    P(p,[(t0,(x,y,0)),(t1,(x,y,0))]); yaw(p,[(t0,90),(t1,90)])
    for lg in (part(p,'leg_left'),part(p,'leg_right')): R(lg,[(t0,(-84,0,0)),(t1,(-84,0,0))])
    return y
def unsit(p, t):
    for lg in (part(p,'leg_left'),part(p,'leg_right')): R(lg,[(t,(0,0,0))])
def climb(p, t0, t1, h=15, x_off=-1.4):
    """사다리 오르기: 밑(t0) → 높이 h (t1).  몸은 사다리 앞(벽 반대쪽)에"""
    n=int(h//5); pts=[(t0,(lx(0)+x_off,0,0))]
    for i in range(1,n+1): pts.append((t0+(t1-t0)*i/n,(lx(5*i)+x_off,5*i,0)))
    P(p,pts,'linear'); yaw(p,[(t0,90),(t1,90)])
    LL,LR,AL,AR=[part(p,n_) for n_ in ('leg_left','leg_right','arm_left','arm_right')]
    k=[]; ka=[]
    for i in range(n*2+1):
        tt=t0+(t1-t0)*i/(n*2); s_=1 if i%2 else -1
        k.append((tt,s_));
    R(LL,[(tt,(-40*(s_>0),0,0)) for tt,s_ in k],'catmullrom'); R(LR,[(tt,(-40*(s_<0),0,0)) for tt,s_ in k],'catmullrom')
    R(AL,[(tt,(-125-15*s_,0,0)) for tt,s_ in k],'catmullrom'); R(AR,[(tt,(-125+15*s_,0,0)) for tt,s_ in k],'catmullrom')
    return lx(h)+x_off
def paint(arm, t0, t1, base=-88):
    pts=[(t0,(base,0,0))]; t=t0+0.18; s_=1
    while t<t1-0.1: pts.append((t,(base+7*s_,0,9*s_))); t+=0.28; s_=-s_
    R(arm,pts+[(t1,(base,0,0))],'catmullrom')

# ===== 꼬마 소녀 =====
GLH,GLB,GLL=part(girl,'head'),part(girl,'body'),part(girl,'arm_left')
sit(girl,GS,0,20.99)
R(GLB,[(0,(-8,0,0)),(6.8,(-8,0,0)),(7.0,(2,0,0)),(7.25,(-6,0,0)),(7.5,(4,0,0)),(7.8,(-8,0,0)),(20.99,(-8,0,0))],'catmullrom')   # 기침(어깨 들썩)
R(GLH,[(0,(-14,0,0)),(1.6,(-14,0,0)),(2.6,(4,0,0)),(3.6,(-12,0,0)),(4.3,(-12,0,0)),(5.4,(4,0,0)),(6.4,(-10,0,0)),(9.4,(-12,0,0)),(10.6,(6,0,0)),(20.99,(2,0,0))],'catmullrom')
R(GLL,[(0,(-30,0,0)),(20.99,(-30,0,0))]); R(GLR,[(0,(-30,0,0)),(20.99,(-30,0,0))])   # 이불 위에 손
# 21~24 아침: 그대로 남은 잎을 보고 몸을 일으켜 손을 뻗음
sit(girl,GS,21.0,23.99)
R(GLB,[(21.0,(-8,0,0)),(21.8,(-8,0,0)),(22.6,(14,0,0)),(23.99,(14,0,0))],'catmullrom')
R(GLH,[(21.0,(2,0,0)),(21.6,(-16,0,0)),(23.99,(-20,0,0))],'catmullrom')
R(GLR,[(21.0,(-30,0,0)),(22.4,(-30,0,0)),(23.2,(-95,0,6)),(23.99,(-95,0,6))],'catmullrom'); R(GLL,[(21.0,(-30,0,0)),(23.99,(-30,0,0))])
unsit(girl,24.0)
# 24~29 봄 골목: 할아버지에게 붓을 받아 벽에 꽃을 그림
GX=59.6
P(girl,[(24.0,(GX,0,-6)),(28.99,(GX,0,-6))])
yaw(girl,[(24.0,90),(24.9,90),(25.2,-149),(25.9,-149),(26.2,90),(28.4,90),(28.8,-149),(28.99,-149)])
R(GLB,[(24.0,(0,0,0)),(28.99,(0,0,0))])
R(GLH,[(24.0,(-30,0,0)),(24.8,(-30,0,0)),(25.2,(-8,0,0)),(26.2,(0,0,0)),(28.4,(4,0,0)),(28.8,(-8,0,0))],'catmullrom')
R(GLR,[(24.0,(0,0,0)),(25.2,(0,0,0)),(25.45,(-55,0,0)),(25.75,(-55,0,0)),(26.1,(-20,0,0)),(26.3,(-88,0,0))],'catmullrom')
paint(GLR,26.3,28.4,-88); R(GLR,[(28.6,(0,0,0)),(28.99,(0,0,0))]); R(GLL,[(24.0,(0,0,0)),(28.99,(0,0,0))])
show(girl,[(0,28.98)])

# ===== 화가 할아버지 =====
GPH,GPB,GPL=part(gp,'head'),part(gp,'body'),part(gp,'arm_left')
# 6~11 방에 들어와 소녀를 보고, 창밖 잎을 올려다봄
P(gp,[(6.0,(-46,0,-17)),(7.6,(-19,0,-16)),(10.99,(-19,0,-16))],'linear'); yaw(gp,[(6.0,90),(7.6,90),(8.0,75),(10.99,75)])
walk(gp,6.0,7.6,amp=22,period=0.62)
R(GPH,[(6.0,(0,0,0)),(7.6,(0,0,0)),(8.0,(8,8,0)),(9.0,(8,8,0)),(9.5,(-22,-6,0)),(10.4,(-22,-6,0)),(10.9,(12,0,0))],'catmullrom')
R(GPB,[(9.5,(0,0,0)),(10.4,(0,0,0)),(10.9,(8,0,0)),(10.99,(8,0,0)),(11.0,(0,0,0))])
# 13.4~19.4 비바람 밤: 사다리를 오르고 벽에 잎을 그림
P(gp,[(13.4,(39,0,-15)),(14.4,(lx(0)-1.4,0,0))]); yaw(gp,[(13.4,55),(14.3,90)])
walk(gp,13.4,14.4,amp=22,period=0.5)
R(GPB,[(11.0,(0,0,0)),(14.4,(0,0,0))])
px=climb(gp,14.4,15.9,15)
P(gp,[(15.9,(px,15,0)),(19.4,(px,15,0))])
R(part(gp,'leg_left'),[(15.9,(0,0,0)),(19.4,(0,0,0))]); R(part(gp,'leg_right'),[(15.9,(0,0,0)),(19.4,(0,0,0))])
R(GPL,[(15.9,(-125,0,0)),(19.4,(-125,0,0))])          # 왼손은 사다리를 잡음
R(GPR,[(15.9,(-110,0,0)),(16.3,(-88,0,0))],'catmullrom'); paint(GPR,16.3,18.5,-88); R(GPR,[(19.0,(-110,0,0)),(19.4,(-110,0,0))])
R(GPH,[(13.4,(0,0,0)),(14.4,(-20,0,0)),(15.9,(-10,0,0)),(16.3,(0,0,0)),(18.6,(0,0,0)),(19.0,(10,-10,0)),(19.4,(10,-10,0))],'catmullrom')
# 24~29 봄 골목: 소녀에게 붓을 건넴
P(gp,[(24.0,(53.5,0,4)),(28.99,(53.5,0,4))])
yaw(gp,[(24.0,90),(24.9,90),(25.2,31),(28.99,31)])
R(GPH,[(24.0,(-30,0,0)),(24.8,(-30,0,0)),(25.2,(10,0,0)),(26.2,(12,0,0)),(28.4,(12,0,0)),(28.8,(0,0,0))],'catmullrom')
R(GPB,[(24.0,(0,0,0)),(25.2,(0,0,0)),(25.4,(10,0,0)),(25.9,(10,0,0)),(26.2,(0,0,0)),(28.99,(0,0,0))])
R(GPR,[(24.0,(0,0,0)),(25.1,(0,0,0)),(25.4,(-58,0,0)),(25.7,(-58,0,0)),(26.0,(0,0,0)),(28.99,(0,0,0))],'catmullrom')
R(GPL,[(24.0,(0,0,0)),(26.4,(0,0,0)),(27.0,(-25,0,-25)),(28.99,(-25,0,-25))],'catmullrom')   # 소녀 쪽으로 손을 살짝
for lg in (part(gp,'leg_left'),part(gp,'leg_right')): R(lg,[(24.0,(0,0,0)),(28.99,(0,0,0))])
show(gp,[(6.0,10.98),(13.4,19.37),(24.0,28.98)])

# ===== 늙은 할아버지 (33~45, 침대) =====
GOH,GOB=part(go,'head'),part(go,'body')
sit(go,1.0,33.0,45)
R(GOB,[(33.0,(-8,0,0)),(45,(-8,0,0))])
R(part(go,'arm_left'),[(33.0,(-30,0,0)),(45,(-30,0,0))]); R(part(go,'arm_right'),[(33.0,(-30,0,0)),(45,(-30,0,0))])
R(GOH,[(33.0,(-12,0,0)),(34.4,(-12,0,0)),(35.4,(4,0,0)),(36.4,(-10,0,0)),(37.2,(-10,0,0)),(38.2,(4,0,0)),
       (41.0,(-14,0,0)),(42.6,(-16,0,0)),(43.3,(-4,42,0)),(45,(-4,42,0))],'catmullrom')
show(go,[(33.0,45)])

# ===== 어른 소녀 =====
WMH,WMB,WML=part(wm,'head'),part(wm,'body'),part(wm,'arm_left')
P(wm,[(35.4,(-46,0,-17)),(36.8,(-19,0,-16)),(37.99,(-19,0,-16))]); yaw(wm,[(35.4,90),(36.8,90),(37.1,75),(37.99,75)])
walk(wm,35.4,36.8,amp=22,period=0.62)
for g_ in ('arm_left','arm_right','leg_left','leg_right'): R(part(wm,g_),[(37.99,(0,0,0)),(38.0,(0,0,0))])
R(WMH,[(35.4,(0,0,0)),(36.8,(0,0,0)),(37.1,(6,8,0)),(37.5,(-20,-6,0)),(37.99,(-20,-6,0))],'catmullrom')
# 38~41.2 눈 오는 밤: 사다리를 오르고 옛 잎 옆에 새 잎을 그림
P(wm,[(38.0,(lx(0)-1.4,0,-8)),(38.4,(lx(0)-1.4,0,0))]); yaw(wm,[(38.0,90),(38.4,90)])
R(WMH,[(38.0,(-20,0,0)),(38.4,(-20,0,0))])
px2=climb(wm,38.4,39.4,15)
P(wm,[(39.4,(px2,15,0)),(41.19,(px2,15,0))])
R(part(wm,'leg_left'),[(39.4,(0,0,0)),(41.19,(0,0,0))]); R(part(wm,'leg_right'),[(39.4,(0,0,0)),(41.19,(0,0,0))])
R(WML,[(39.4,(-125,0,0)),(41.19,(-125,0,0))])
R(WMR,[(39.4,(-110,0,0)),(39.65,(-88,0,0))],'catmullrom'); paint(WMR,39.65,40.95,-88)
R(WMH,[(39.4,(-6,0,0)),(39.7,(0,0,0)),(40.95,(0,0,0)),(41.19,(0,0,0))])
# 41.2~45 아침: 침대 옆 (+z 쪽) 에서 할아버지를 봄
P(wm,[(41.2,(9,0,13)),(45,(9,0,13))]); yaw(wm,[(41.2,-34),(45,-34)])
for g_ in (WML,WMR,part(wm,'leg_left'),part(wm,'leg_right')): R(g_,[(41.2,(0,0,0)),(45,(0,0,0))])
R(WMB,[(41.2,(6,0,0)),(45,(6,0,0))]); R(WMH,[(41.2,(10,-10,0)),(43.0,(10,-10,0)),(43.6,(14,-14,0)),(45,(14,-14,0))],'catmullrom')
R(WML,[(43.2,(0,0,0)),(43.9,(-40,0,-10)),(45,(-40,0,-10))],'catmullrom')   # 할아버지 쪽으로 손을 뻗음
show(wm,[(35.4,45)])

A.bake(top)
M.save(f'{OUT}/A_잎새.bbmodel',top,[A.json()],name='A')
json.dump({'A':{'ropes':[]}},open(f'{OUT}/세트정보.json','w',encoding='utf-8'))
print('ok',len(M.els),'parts')
