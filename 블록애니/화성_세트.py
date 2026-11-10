"""《화성의 오디세이》 배경 부품 (세트를 꽉 채우는 것들) — 화성_장면.py 가 씀.
   땅·모래 언덕·절벽(메사)·바위·구덩이·화성 식물·운하 나무·진흙 언덕 도시·피라미드·로켓·별·화성 공·전시실·굴 속 방
   크기 기준: 사람 키 32 (≈1.8m) → 1m ≈ 18.  카메라는 -z 에서 +z 를 봄 (먼 배경은 +z 쪽에 둠)"""
import os, sys, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import ImageDraw
from 블록인물 import Model, move, anchor, Anim, find, U
from 신라인물 import BigModel, brick_wall
from 화성인물 import *

def world_palette(M):
    S=M.swatch
    S('o1',(214,140,84),8); S('o2',(203,128,74),8); S('o3',(226,156,98),8); S('o_d',(170,100,58),8); S('o_dd',(140,80,48),8)      # 주황 사막
    S('g1',(150,146,150),7); S('g2',(138,134,140),7); S('g3',(165,160,162),7); S('g_d',(108,104,112),7)                          # 잿빛 평원
    S('cl1',(176,96,60),9); S('cl2',(150,78,50),9); S('cl3',(198,120,76),9); S('cl4',(118,62,44),9)                              # 절벽 지층
    S('rk',(128,84,62),10); S('rk_d',(98,64,50),9); S('rk_g',(110,108,116),9)
    S('pl1',(70,130,140),8); S('pl2',(96,80,140),8); S('pl3',(150,90,130),8); S('pl_s',(88,74,70),6); S('bulb',(210,170,90),8)   # 화성 식물
    S('gr',(96,150,96),10); S('gr2',(120,170,90),10)                                                                             # 걸어 다니는 풀
    S('rub',(40,112,108),8); S('rub2',(60,140,120),8); S('rub_t',(92,70,96),6)                                                    # 운하 고무 나무
    S('mud',(150,104,74),8); S('mud2',(132,90,64),8); S('mud3',(168,120,86),8); S('mud_d',(84,56,42),6)                           # 진흙 언덕
    S('canal',(120,110,70),6); S('wat',lambda x,y:(196,170,70) if (x+2*y)%7 else (220,198,100),5)                                  # 누런 물
    S('road',(118,82,60),6)
    S('star',(255,250,235),2); S('star_b',(190,215,255),2); S('earth',(110,235,150),3); S('moon',(225,215,200),6)
    S('hull',(232,232,236),4); S('hull_d',(190,192,200),4); S('hull_r',(196,52,48),5); S('win',(120,200,235),3); S('jet',(60,62,70),4)
    S('fl1',(255,210,80),14); S('fl2',(255,140,40),16); S('fl3',(255,245,200),6); S('smoke',(120,116,114),10); S('smoke_l',(200,196,190),8)
    S('fire_w',(92,60,40),6); S('ember',(250,120,40),14)
    S('tile_a',(58,52,70),4); S('tile_b',(74,66,88),4); S('wall_h',(96,78,104),5); S('wall_hd',(72,58,82),5); S('pil',(205,190,160),5)
    S('gold_f',(214,172,70),5); S('ped',(222,216,204),4); S('ped_d',(180,174,164),4); S('carpet',(150,36,44),5); S('rope_r',(190,40,50),4)
    S('lamp',(255,236,170),3); S('paper',(240,232,210),4); S('ink',(40,36,44),3); S('book1',(150,60,50),6); S('book2',(60,96,140),6); S('book3',(70,120,80),6); S('book4',(190,150,70),6)
    S('wood',(120,82,52),6); S('wood_d',(88,60,40),5)
    S('cave',(104,74,58),8); S('cave2',(92,64,50),8); S('cave_d',(60,42,36),6); S('cave_l',(128,94,72),8); S('rod',(26,24,28),3)
    S('m_g',(120,196,170),5); S('m_b',(100,140,200),5)
    S('mars1',(205,110,66),10); S('mars2',(170,84,52),10); S('mars3',(224,150,100),8); S('mars_ice',(240,238,232),4); S('mark',(255,235,120),3)
    S('th',(250,250,252),3); S('ny',(110,120,150),6); S('ny_w',(250,225,130),4)
    M.big('bw_sil',128,64,brick_wall(base=(196,188,172),joint=(128,120,108),bw=32,bh=16,jit=10))        # 피라미드 벽 (새 것)
    M.big('bw_old',128,64,brick_wall(base=(176,164,146),joint=(118,108,96),bw=32,bh=16,jit=22))         # 오래된 것

def tiles(M,x0,x1,z0,z1,tile=64,cols=('o1','o2','o3'),y=0,seed=1):
    """땅: 세 가지 색을 섞은 칸 (한 가지 색 평면이 아니게)"""
    r=random.Random(seed); k=[]
    for x in range(x0,x1,tile):
        for z in range(z0,z1,tile):
            k.append(M.cube('g',[x,y-16,z],[x+tile,y,z+tile],cols[(x//tile*3+z//tile*5+r.randint(0,1))%len(cols)]))
    return k
def far_ground(M,col='o2'): return M.cube('far_ground',[-6000,-20,-6000],[6000,-15,6000],col)

def dune(M,x,z,w,d,h,cols=('o3','o1','o2')):
    """모래 언덕: 넓은 판을 계단처럼 쌓음"""
    k=[]; n=max(2,int(h/7))
    for i in range(n):
        f=1-i/n*0.85; k.append(M.cube('dune',[x-w/2*f,i*h/n,z-d/2*f+i*d*0.04],[x+w/2*f,(i+1)*h/n,z+d/2*f+i*d*0.04],cols[i%len(cols)]))
    return k
def mesa(M,x,z,w,d,h,seed=0,cols=('cl1','cl2','cl3','cl4')):
    """절벽 덩어리: 지층 띠 + 들쭉날쭉한 꼭대기"""
    r=random.Random(seed); k=[]; y=0; i=0
    while y<h:
        hh=min(h-y,r.choice([18,24,30,36])); inset=i*r.uniform(1.5,4)
        k.append(M.cube('mesa',[x-w/2+inset,y,z-d/2+inset],[x+w/2-inset,y+hh,z+d/2-inset],cols[(i+seed)%len(cols)])); y+=hh; i+=1
    for j in range(3):
        ww=w*r.uniform(0.18,0.35); xx=x+r.uniform(-w/2+ww,w/2-ww)
        k.append(M.cube('mesa_top',[xx-ww/2,h,z-d/3],[xx+ww/2,h+r.uniform(10,34),z+d/3],cols[(j+seed+1)%len(cols)]))
    return k
def cliff_line(M,z,x0,x1,h,seed=0,d=260,step=220):
    """먼 절벽 줄 (지평선을 채움)"""
    r=random.Random(seed); k=[]; x=x0; i=0
    while x<x1:
        w=step*r.uniform(0.8,1.3); k+=mesa(M,x+w/2,z+r.uniform(-60,60),w+20,d,h*r.uniform(0.75,1.25),seed+i); x+=w; i+=1
    return k
def rock(M,x,z,s=10,col='rk',seed=0):
    r=random.Random(seed*7+int(x)+int(z))
    k=[M.cube('rock',[x-s,0,z-s*0.8],[x+s,s*1.1,z+s*0.8],col), M.cube('rock',[x-s*0.5,s*0.9,z-s*0.5],[x+s*0.6,s*1.7,z+s*0.4],col+'_d' if col=='rk' else col)]
    if r.random()<0.6: k.append(M.cube('rock',[x+s*0.7,0,z+s*0.3],[x+s*1.5,s*0.6,z+s*1.1],'rk_d'))
    return k
def pebbles(M,x0,x1,z0,z1,n,seed=0,cols=('rk','rk_d','o_d')):
    r=random.Random(seed); k=[]
    for i in range(n):
        x=r.uniform(x0,x1); z=r.uniform(z0,z1); s=r.uniform(1.5,4)
        k.append(M.cube('peb',[x-s,0,z-s],[x+s,s*r.uniform(0.6,1.2),z+s],cols[i%len(cols)]))
    return k
def patches(M,x0,x1,z0,z1,n,col='o_d',seed=0):
    """땅 위 얼룩 (색이 다른 납작한 판)"""
    r=random.Random(seed); k=[]
    for i in range(n):
        x=r.uniform(x0,x1); z=r.uniform(z0,z1); w=r.uniform(20,70); d=r.uniform(14,50)
        k.append(M.cube('patch',[x-w/2,0,z-d/2],[x+w/2,0.5+(i%3)*0.3,z+d/2],col))
    return k
def crater(M,x,z,r_,col='o_d',rim='o3'):
    k=[M.cube('cr_in',[x-r_*0.7,0,z-r_*0.7],[x+r_*0.7,0.6,z+r_*0.7],col)]
    for i in range(8):
        a=i/8*6.283; cx=x+r_*math.cos(a); cz=z+r_*math.sin(a); s=r_*0.42
        k.append(M.cube('cr_rim',[cx-s,0,cz-s],[cx+s,r_*0.22,cz+s],rim))
    return k
def stump(M,x,z,h=30,seed=0):
    """잎 없는 화성 식물: 줄기 + 짧은 가지 끝에 혹"""
    r=random.Random(seed*13+int(x)*3+int(z)); c=r.choice(['pl1','pl2','pl3']); t=max(1.2,h/14)
    k=[M.cube('stump',[x-t,0,z-t],[x+t,h,z+t],'pl_s')]
    for i in range(r.randint(2,4)):
        yy=h*r.uniform(0.35,0.95); sx=r.choice([-1,1]); L=h*r.uniform(0.25,0.5)
        if r.random()<0.5: k+= [M.cube('br',[min(x,x+sx*L),yy,z-t*0.7],[max(x,x+sx*L),yy+t*1.2,z+t*0.7],'pl_s'), M.cube('bulb',[x+sx*L-t*1.6,yy+t*0.6,z-t*1.6],[x+sx*L+t*1.6,yy+t*3.6,z+t*1.6],c)]
        else: k+= [M.cube('br',[x-t*0.7,yy,min(z,z+sx*L)],[x+t*0.7,yy+t*1.2,max(z,z+sx*L)],'pl_s'), M.cube('bulb',[x-t*1.6,yy+t*0.6,z+sx*L-t*1.6],[x+t*1.6,yy+t*3.6,z+sx*L+t*1.6],c)]
    k.append(M.cube('bulb',[x-t*1.8,h,z-t*1.8],[x+t*1.8,h+t*3,z+t*1.8],c))
    return k
def stumps(M,x0,x1,z0,z1,n,seed=0,hmin=14,hmax=44,avoid=()):
    r=random.Random(seed); k=[]; i=0; tries=0
    while i<n and tries<n*20:
        tries+=1; x=r.uniform(x0,x1); z=r.uniform(z0,z1)
        if any(abs(x-ax)<aw and abs(z-az)<ad for ax,az,aw,ad in avoid): continue
        k+=stump(M,x,z,r.uniform(hmin,hmax),seed+i); i+=1
    return k
def grass(M,x0,x1,z0,z1,n,seed=0,avoid=()):
    """걸어 다니는 풀 (손가락만 한 초록 잎)"""
    r=random.Random(seed); k=[]; i=0; tries=0
    while i<n and tries<n*20:
        tries+=1; x=r.uniform(x0,x1); z=r.uniform(z0,z1)
        if any(abs(x-ax)<aw and abs(z-az)<ad for ax,az,aw,ad in avoid): continue
        k.append(M.cube('grass',[x-0.6,0,z-0.6],[x+0.6,r.uniform(2,4.5),z+0.6],'gr' if i%2 else 'gr2')); i+=1
    return k
def rubber_tree(M,x,z,h=70,seed=0):
    """운하 가의 고무 같은 나무: 굵은 줄기 + 우산 모양 덩어리"""
    r=random.Random(seed+int(x)); t=h/11; k=[M.cube('rtrunk',[x-t,0,z-t],[x+t,h*0.62,z+t],'rub_t'), M.cube('rtrunk',[x-t*1.5,0,z-t*1.5],[x+t*1.5,h*0.1,z+t*1.5],'rub_t')]
    for i,(w,y0,hh) in enumerate([(h*0.62,h*0.55,h*0.14),(h*0.46,h*0.69,h*0.14),(h*0.26,h*0.83,h*0.12)]):
        k.append(M.cube('rleaf',[x-w/2,y0,z-w/2],[x+w/2,y0+hh,z+w/2],'rub' if (i+seed)%2 else 'rub2'))
    for i in range(3):
        a=r.uniform(0,6.28); L=h*0.3; k.append(M.cube('rvine',[x+L*math.cos(a)-1,h*0.3,z+L*math.sin(a)-1],[x+L*math.cos(a)+1,h*0.57,z+L*math.sin(a)+1],'rub2'))
    return k
def mound(M,x,z,w,h,door=None,seed=0):
    """진흙 언덕 (도시의 집 하나): 줄어드는 판을 쌓음 + 어두운 구멍. door='n' 이면 -z 쪽에 큰 입구"""
    r=random.Random(seed); k=[]; n=max(3,int(h/14))
    for i in range(n):
        f=1-(i/n)**1.5*0.8; k.append(M.cube('mound',[x-w/2*f,i*h/n,z-w/2*f],[x+w/2*f,(i+1)*h/n,z+w/2*f],['mud','mud2','mud3'][(i+seed)%3]))
    for i in range(r.randint(2,4)):      # 작은 구멍(창)
        yy=h*r.uniform(0.25,0.6); xx=x+r.uniform(-w*0.25,w*0.25); f=1-((yy/h)**1.5)*0.8
        k.append(M.cube('mhole',[xx-4,yy,z-w/2*f-0.6],[xx+4,yy+7,z-w/2*f+0.4],'mud_d'))
    if door=='n':
        k+= [M.cube('mdoor',[x-20,0,z-w/2-1],[x+20,34,z-w/2+6],'hole'), M.cube('mdoor_f',[x-25,0,z-w/2-4],[x-20,38,z-w/2+2],'mud3'),
             M.cube('mdoor_f',[x+20,0,z-w/2-4],[x+25,38,z-w/2+2],'mud3'), M.cube('mdoor_f',[x-25,34,z-w/2-4],[x+25,40,z-w/2+2],'mud3')]
    return k
def pyramid(M,tag,x,z,H,capped=False,old=False,layers=5):
    """벽돌 피라미드 (속이 빈·꼭대기가 열린). H=높이. 층마다 묶음(tag_L0..) → 꼭대기 층을 따로 움직일 수 있음. 묶음을 돌려줌"""
    tex='bw_old' if old else 'bw_sil'; W=H*1.25; lh=H/layers; ls=[]
    for i in range(layers):
        w=W*(1-i/layers*0.78)
        c=M.cube('pyr',[x-w/2,i*lh,z-w/2],[x+w/2,(i+1)*lh,z+w/2],tex,up='brick',down='brick')
        ls.append(M.group(f'{tag}L{i}',[x,i*lh,z],[c]))
    wt=W*(1-(layers-1)/layers*0.78)
    if not capped: ls.append(M.group(f'{tag}hole',[x,H,z],[M.cube('pyr_hole',[x-wt*0.36,H-0.3,z-wt*0.36],[x+wt*0.36,H+0.15,z+wt*0.36],'hole')]))
    return M.group(tag+'root',[x,0,z],ls)

def aux_rocket(M,tag):
    """보조 로켓 (작은 날개 로켓, 앞 = -z, 길이 약 90). 불꽃 묶음 tag_flame, 아래 분사 tag_under"""
    c=M.cube
    k=[c('body',[-9,8,-30],[9,26,34],'hull'), c('nose1',[-7,10,-40],[7,24,-30],'hull'), c('nose2',[-4,13,-47],[4,21,-40],'hull_r'),
       c('stripe',[-9.3,15,-12],[9.3,19,-6],'hull_r'), c('cab',[-6,26,-22],[6,31,-4],'hull_d'), c('win_f',[-5,26.5,-23],[5,30.5,-21.6],'win'),
       c('win_l',[6,26.5,-20],[6.6,30.5,-8],'win'), c('win_r',[-6.6,26.5,-20],[-6,30.5,-8],'win'),
       c('wing_l',[9,13,-6],[40,16,22],'hull_d'), c('wing_r',[-40,13,-6],[-9,16,22],'hull_d'), c('tip_l',[38,13,6],[42,22,22],'hull_r'), c('tip_r',[-42,13,6],[-38,22,22],'hull_r'),
       c('fin',[-1.5,26,18],[1.5,42,34],'hull_r'), c('noz',[-6,10,34],[6,24,40],'jet'), c('ujet_l',[4,5,-8],[8,8,-2],'jet'), c('ujet_r',[-8,5,-8],[-4,8,-2],'jet'),
       c('gear_f',[-1.5,0,-22],[1.5,8,-19],'jet'), c('gear_l',[5,0,14],[8,8,17],'jet'), c('gear_r',[-8,0,14],[-5,8,17],'jet')]
    fl=M.group(tag+'flame',[0,17,40],[c('fl',[-5,11,40],[5,23,56],'fl2'), c('fl',[-3,13,54],[3,21,72],'fl1'), c('fl',[-1.5,15,70],[1.5,19,84],'fl3')])
    un=M.group(tag+'under',[0,5,-5],[c('ufl',[4.5,-10,-7.5],[7.5,5,-2.5],'fl1'), c('ufl',[-7.5,-10,-7.5],[-4.5,5,-2.5],'fl1'), c('ufl',[5,-22,-7],[7,-10,-3],'fl3'), c('ufl',[-7,-22,-7],[-5,-10,-3],'fl3')])
    return M.group(tag+'root',[0,0,0],k+[fl,un])
def ares(M,tag,x=0,z=0):
    """탐사선 아레스호: 곧게 선 큰 로켓 (높이 약 330). 문·사다리·창·날개 다리"""
    c=lambda n,fr,to,col: M.cube(n,[fr[0]+x,fr[1],fr[2]+z],[to[0]+x,to[1],to[2]+z],col)
    k=[c('body',[-34,40,-34],[34,230,34],'hull'), c('belly',[-38,70,-38],[38,170,38],'hull'), c('band1',[-38.5,170,-38.5],[38.5,178,38.5],'hull_r'), c('band2',[-38.5,62,-38.5],[38.5,70,38.5],'hull_r'),
       c('sh1',[-28,230,-28],[28,262,28],'hull'), c('sh2',[-20,262,-20],[20,290,20],'hull_d'), c('sh3',[-11,290,-11],[11,314,11],'hull_r'), c('tip',[-3,314,-3],[3,336,3],'jet'),
       c('skirt',[-30,22,-30],[30,40,30],'hull_d'), c('noz',[-18,6,-18],[18,22,18],'jet'),
       c('door',[-9,44,-38.8],[9,78,-37.8],'hull_d'), c('door_w',[-4,62,-39.2],[4,72,-38.6],'win'), c('ramp',[-10,0,-78],[10,3,-38],'hull_d'), c('ramp2',[-10,3,-58],[10,22,-38],'hull_d'), c('ramp3',[-10,22,-46],[10,44,-38],'hull_d')]
    for i,yy in enumerate((110,140,196)):
        for xx in (-18,0,18): k.append(c('port',[xx-5,yy,-38.9],[xx+5,yy+10,-37.9],'win'))
        k.append(c('port_s',[38,yy,-5],[38.9,yy+10,5],'win')); k.append(c('port_s',[-38.9,yy,-5],[-38,yy+10,5],'win'))
    for sx,sz in ((1,1),(1,-1),(-1,1),(-1,-1)):
        k+= [c('leg',[sx*30-5,0,sz*30-5],[sx*30+5,60,sz*30+5],'hull_r') , c('legfin',[min(sx*34,sx*62),0,sz*34-3],[max(sx*34,sx*62),70,sz*34+3],'hull_r'), c('pad',[sx*56-9,0,sz*34-9],[sx*56+9,4,sz*34+9],'jet')]
    k.append(c('antenna',[-1,336,-1],[1,360,1],'jet')); k.append(c('dish',[10,300,-3],[22,304,3],'hull_d'))
    return M.group(tag+'root',[x,0,z],k)

def stars(M,tag,n=140,seed=5,zfar=2600,spread=3200,ymin=250,ymax=2200):
    """밤하늘 별 (먼 벽에 흩뿌린 작은 상자) — 묶음. 밤 장면에만 vis"""
    r=random.Random(seed); k=[]
    for i in range(n):
        x=r.uniform(-spread,spread); y=r.uniform(ymin,ymax); s=r.choice([5,5,6,8,11]); z=zfar+r.uniform(-100,100)
        k.append(M.cube('star',[x-s,y-s,z],[x+s,y+s,z+4],'star' if i%4 else 'star_b'))
    return M.group(tag,[0,0,0],k)
def moons(M,tag,zfar=2500):
    k=[M.cube('phobos',[-700,900,zfar],[-640,950,zfar+20],'moon'), M.cube('phobos2',[-690,950,zfar],[-655,962,zfar+20],'moon'), M.cube('deimos',[900,1300,zfar],[928,1326,zfar+20],'moon')]
    return M.group(tag,[0,0,0],k)
def globe(M,tag,cx,cy,cz,R,cols=('mars1','mars2','mars3'),ice=True,seed=2,step=None):
    """블록 공 (행성): 얇은 판을 원 모양으로 쌓음 + 얼룩"""
    r=random.Random(seed); step=step or R/9; k=[]; y=-R; i=0
    while y<R-1e-6:
        ym=y+step/2; w=math.sqrt(max(0,R*R-ym*ym)); col=cols[(i//3)%2]
        if ice and (ym>R*0.82 or ym<-R*0.86): col='mars_ice'
        k.append(M.cube('globe',[cx-w,cy+y,cz-w*0.72],[cx+w,cy+y+step,cz+w*0.72],col))
        k.append(M.cube('globe',[cx-w*0.72,cy+y,cz-w],[cx+w*0.72,cy+y+step,cz+w],col)); y+=step; i+=1
    for j in range(10):     # 얼룩 (앞면 -z)
        yy=r.uniform(-R*0.6,R*0.6); w=math.sqrt(R*R-yy*yy); xx=r.uniform(-w*0.6,w*0.6); s=R*r.uniform(0.08,0.2)
        k.append(M.cube('spot',[cx+xx-s,cy+yy-s*0.5,cz-w-1.5],[cx+xx+s,cy+yy+s*0.5,cz-w+3],cols[2] if j%2 else 'o_dd'))
    return M.group(tag,[cx,cy,cz],k)

def campfire(M,tag,x,z):
    k=[M.cube('log',[x-7,0,z-1.5],[x+7,3,z+1.5],'fire_w'), M.cube('log',[x-1.5,0,z-7],[x+1.5,3,z+7],'fire_w'), M.cube('log',[x-5,2,z-5],[x+5,4,z+5],'fire_w')]
    fl=M.group(tag+'flame',[x,3,z],[M.cube('fl',[x-4,3,z-4],[x+4,10,z+4],'fl2'), M.cube('fl',[x-2.5,9,z-2.5],[x+2.5,16,z+2.5],'fl1'), M.cube('fl',[x-1,15,z-1],[x+1,21,z+1],'fl3')])
    return M.group(tag+'root',[x,0,z],k+[fl]), fl

# ---------------- 전시실 (들어가며·숨은 뜻) ----------------
def cover_art(im,x,y,w,h):
    """잡지 표지 그림 (직접 그린 것): 붉은 행성 + 로켓 + 띠"""
    d=ImageDraw.Draw(im); d.rectangle([x,y,x+w-1,y+h-1],fill=(24,28,60))
    r=random.Random(4)
    for i in range(40): sx=x+r.randint(2,w-3); sy=y+r.randint(22,h-26); d.point((sx,sy),fill=(255,250,220))
    d.rectangle([x,y,x+w-1,y+20],fill=(210,60,50)); d.rectangle([x+8,y+6,x+w-9,y+9],fill=(255,235,150)); d.rectangle([x+8,y+12,x+w-30,y+14],fill=(255,235,150))
    d.ellipse([x+w*0.38,y+h*0.42,x+w*1.05,y+h*0.98],fill=(205,110,66)); d.ellipse([x+w*0.52,y+h*0.56,x+w*0.72,y+h*0.68],fill=(170,84,52)); d.ellipse([x+w*0.7,y+h*0.74,x+w*0.86,y+h*0.82],fill=(224,150,100))
    d.polygon([(x+w*0.18,y+h*0.72),(x+w*0.3,y+h*0.34),(x+w*0.4,y+h*0.72)],fill=(235,235,240)); d.rectangle([x+w*0.25,y+h*0.5,x+w*0.33,y+h*0.56],fill=(120,200,235))
    d.polygon([(x+w*0.12,y+h*0.8),(x+w*0.2,y+h*0.66),(x+w*0.24,y+h*0.8)],fill=(196,52,48)); d.polygon([(x+w*0.34,y+h*0.8),(x+w*0.38,y+h*0.66),(x+w*0.46,y+h*0.8)],fill=(196,52,48))
    d.polygon([(x+w*0.24,y+h*0.74),(x+w*0.29,y+h*0.92),(x+w*0.35,y+h*0.74)],fill=(255,190,60))
    d.rectangle([x,y+h-14,x+w-1,y+h-1],fill=(240,232,210)); d.rectangle([x+6,y+h-10,x+w*0.6,y+h-8],fill=(40,36,44)); d.rectangle([x+6,y+h-6,x+w*0.4,y+h-5],fill=(40,36,44))
def magazine(M,tag,x,z,s=1.0,y=0):
    """받침대(이젤) 위의 큰 잡지. 표지는 -z 를 봄"""
    c=lambda n,fr,to,col,**f: M.cube(n,[x+fr[0]*s,y+fr[1]*s,z+fr[2]*s],[x+to[0]*s,y+to[1]*s,z+to[2]*s],col,**f)
    k=[c('mag',[-24,30,-2],[24,94,1],'paper',north='cover'), c('spine',[-25,30,-2.2],[-24,94,1.2],'hull_r'),
       c('leg_l',[-22,0,0],[-19,34,3],'wood'), c('leg_r',[19,0,0],[22,34,3],'wood'), c('leg_b',[-1.5,0,10],[1.5,60,13],'wood_d'), c('shelf',[-26,27,-5],[26,30,3],'wood_d')]
    return M.group(tag+'root',[x,y,z],k)
def pedestal(M,x,z,w=44,h=14,name='ped'):
    return [M.cube(name,[x-w/2,0,z-w/2],[x+w/2,h-3,z+w/2],'ped'), M.cube(name,[x-w/2-3,h-3,z-w/2-3],[x+w/2+3,h,z+w/2+3],'ped_d'), M.cube(name,[x-w/2-3,0,z-w/2-3],[x+w/2+3,3,z+w/2+3],'ped_d')]
def hall(M,W=760,D=520,H=300):
    """전시실: 바둑판 바닥·벽·기둥·액자·책장·천장 등·붉은 융단·줄 울타리"""
    k=[]; t=40
    for x in range(-W//2,W//2,t):
        for z in range(-D//2-200,D//2,t): k.append(M.cube('floor',[x,-8,z],[x+t,0,z+t],'tile_a' if (x//t+z//t)%2 else 'tile_b'))
    k+= [M.cube('wall_b',[-W/2,0,D/2],[W/2,H,D/2+20],'wall_h'), M.cube('wall_l',[W/2,0,-D/2-200],[W/2+20,H,D/2],'wall_hd'), M.cube('wall_r',[-W/2-20,0,-D/2-200],[-W/2,H,D/2],'wall_hd'),
         M.cube('skirt',[-W/2,0,D/2-3],[W/2,14,D/2],'wood_d'), M.cube('cornice',[-W/2,H-22,D/2-8],[W/2,H,D/2],'gold_f'), M.cube('ceil',[-W/2-20,H,-D/2-200],[W/2+20,H+12,D/2+20],'wall_hd')]
    for i,x in enumerate(range(-W//2+40,W//2,136)):      # 기둥 + 사이 액자
        k+= [M.cube('pillar',[x-11,0,D/2-18],[x+11,H-22,D/2],'pil'), M.cube('pil_base',[x-15,0,D/2-22],[x+15,12,D/2],'ped_d'), M.cube('pil_cap',[x-15,H-34,D/2-22],[x+15,H-22,D/2],'gold_f')]
        fx=x+68
        if fx<W/2-30:
            col=['m_g','m_b','mars1','pl2','bulb'][i%5]
            k+= [M.cube('frame',[fx-36,120,D/2-5],[fx+36,220,D/2],'gold_f'), M.cube('pic',[fx-31,125,D/2-6],[fx+31,215,D/2-4],col),
                 M.cube('pic_a',[fx-20,135,D/2-7],[fx+4,170,D/2-5],'ink'), M.cube('pic_b',[fx-2,150,D/2-8.2],[fx+24,205,D/2-5],'star'), M.cube('plate',[fx-12,104,D/2-4],[fx+12,112,D/2],'gold_f')]
    for sx in (-1,1):       # 옆벽 책장
        for j,z in enumerate(range(-D//2-120,D//2-60,150)):
            xw=sx*(W/2); k.append(M.cube('shelf',[min(xw,xw-sx*18),0,z],[max(xw,xw-sx*18),190,z+110],'wood_d'))
            for row in range(4):
                for b in range(9):
                    bx=xw-sx*19; bh=28+((b*7+row*3+j)%4)*4
                    k.append(M.cube('book',[min(bx,bx-sx*2),14+row*44,z+6+b*11],[max(bx,bx-sx*2),14+row*44+bh,z+15+b*11],['book1','book2','book3','book4'][(b+row+j)%4]))
    for x in (-250,0,250):  # 천장 등
        for z in (-240,60): k+= [M.cube('lamp_rod',[x-1.5,H-50,z-1.5],[x+1.5,H,z+1.5],'rod'), M.cube('lamp',[x-16,H-64,z-16],[x+16,H-50,z+16],'lamp'), M.cube('lamp_s',[x-22,H-52,z-22],[x+22,H-48,z+22],'gold_f')]
    k.append(M.cube('carpet',[-70,0,-D/2-200],[70,0.6,D/2-60],'carpet')); k.append(M.cube('carpet_e',[-76,0,-D/2-200],[-70,0.7,D/2-60],'gold_f')); k.append(M.cube('carpet_e',[70,0,-D/2-200],[76,0.7,D/2-60],'gold_f'))
    return k
def barrier(M,x0,x1,z):
    k=[]; n=int(abs(x1-x0)//60)+1
    for i in range(n+1):
        x=x0+(x1-x0)*i/n; k+= [M.cube('post',[x-2,0,z-2],[x+2,26,z+2],'gold_f'), M.cube('post_b',[x-4,0,z-4],[x+4,2,z+4],'gold_f')]
        if i<n: k.append(M.cube('rope_bar',[x,21,z-1],[x+(x1-x0)/n,23.5,z+1],'rope_r'))
    return k

# ---------------- 굴 속 (진흙 도시 안) ----------------
def cave_light(M,x,y,z,side):
    """벽에 박힌 검은 막대 전등"""
    return [M.cube('rod',[min(x,x+side*10),y,z-1.5],[max(x,x+side*10),y+3,z+1.5],'rod'), M.cube('glow',[x+side*8-3,y-2,z-3],[x+side*8+3,y+5,z+3],'lamp'),
            M.cube('glow_w',[x-side*0.6,y-14,z-12],[x+side*0.4,y+18,z+12],'cave_l')]
def idle_machine(M,tag,x,z):
    """아무 일도 안 하는 듯 돌기만 하는 기계 (바퀴 묶음 tag_w 를 돌림)"""
    k=[M.cube('mbase',[x-16,0,z-10],[x+16,10,z+10],'steel_d'), M.cube('mpost',[x-3,10,z-3],[x+3,34,z+3],'steel')]
    w=M.group(tag+'w',[x,34,z],[M.cube('mw',[x-14,31,z-4.5],[x+14,37,z-2.5],'copper'), M.cube('mw',[x-3,20,z-4.5],[x+3,48,z-2.5],'copper'), M.cube('mhub',[x-4,30,z-5.5],[x+4,38,z-1.5],'copper_d')])
    return k,w
def big_wheel(M,tag,x,y,z,R=70,width=60):
    """곡식 찧는 물레처럼 천천히 도는 거대한 바퀴 (축은 x 방향). 묶음을 x 축으로 돌림"""
    k=[M.cube('spoke',[x-width/2,y-R,z-9],[x+width/2,y+R,z+9],'steel_d'), M.cube('spoke',[x-width/2,y-9,z-R],[x+width/2,y+9,z+R],'steel_d'),
       M.cube('pad',[x-width/2-3,y+R-12,z-22],[x+width/2+3,y+R,z+22],'steel'), M.cube('pad',[x-width/2-3,y-R,z-22],[x+width/2+3,y-R+12,z+22],'steel'),
       M.cube('pad',[x-width/2-3,y-22,z+R-12],[x+width/2+3,y+22,z+R],'steel'), M.cube('pad',[x-width/2-3,y-22,z-R],[x+width/2+3,y+22,z-R+12],'steel'),
       M.cube('disc',[x-width/2+6,y-R*0.6,z-R*0.6],[x+width/2-6,y+R*0.6,z+R*0.6],'copper_d'), M.cube('hub',[x-width/2-8,y-12,z-12],[x+width/2+8,y+12,z+12],'copper')]
    return M.group(tag,[x,y,z],k)
