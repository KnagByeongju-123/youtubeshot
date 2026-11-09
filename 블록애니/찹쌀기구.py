"""《600년 성벽을 붙인 찹쌀죽의 비밀》 블록 부품: 난징 성벽(큰 회색 벽돌·여장), 벽돌 가마, 가마솥(김), 석회 통·반죽 통,
   이름 새긴 벽돌, 녹말 사슬(아밀로스·아밀로펙틴), 탄산칼슘 알갱이(큰/작은), 실험실 탁자·누르는 기계, 돌 무지개다리, 불도저·무덤"""
import os, sys, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 화성기구 import *

def chapssal_palette(M):
    M.swatch('nbrick',(132,130,128),8); M.swatch('nbrick_d',(108,106,104),6); M.swatch('mortar',(205,200,188),5)
    M.swatch('iron_pot',(48,46,46),4); M.swatch('porridge',(238,234,220),4); M.swatch('steam',(240,242,245),3); M.swatch('lime',(244,244,240),3)
    M.swatch('stove',(150,95,70),8); M.swatch('chain_a',(240,190,70),6); M.swatch('chain_b',(90,170,220),6); M.swatch('crystal',(225,228,232),6); M.swatch('crystal_d',(185,190,198),6)
    M.swatch('table',(170,150,120),5); M.swatch('glass',(170,215,230),4); M.swatch('steel',(150,155,162),5); M.swatch('yellow',(235,190,40),6)
    M.swatch('water',lambda x,y:(60,120,180) if (x+2*y)%7 else (95,155,210),6)
    M.big('nwall', 128, 64, brick_wall(base=(130,128,126),joint=(196,192,182),bw=16,bh=6,jit=10))
    M.big('nwall_row', 128, 12, brick_wall(base=(130,128,126),joint=(196,192,182),bw=16,bh=6,jit=10))

def nanjing_wall(M, tag, x0, x1, z, H=150, T=60, rows=10):
    """난징 성벽 한 토막: 큰 회색 벽돌 줄 + 위에 톱니 여장"""
    out=[]; rh=H/rows
    for j in range(rows):
        out.append(M.group(f'{tag}row{j}',[(x0+x1)/2,j*rh,z],[M.cube('nrow',[x0,j*rh,z],[x1,(j+1)*rh,z+T],'nwall_row')]))
    pk=[]; seg=24; xs=x0
    while xs<x1-4:
        xe=min(x1,xs+14); pk.append(M.cube('merlon',[xs,H,z],[xe,H+16,z+8],'nbrick')); xs+=seg
    pk.append(M.cube('walk',[x0,H-1,z+8],[x1,H+1,z+T],'nbrick_d'))
    out.append(M.group(f'{tag}top',[(x0+x1)/2,H,z],pk))
    return out

def kiln(M, tag, x, z):
    k=[M.cube('k_base',[x-40,0,z-40],[x+40,30,z+40],'clay')]
    for j in range(5):
        r=40-j*7; k.append(M.cube('k_dome',[x-r,30+j*8,z-r],[x+r,38+j*8,z+r],'clay'))
    k+= [M.cube('k_door',[x-12,0,z-41],[x+12,22,z-39],'dark'), M.cube('k_fire',[x-9,2,z-41.5],[x+9,14,z-40.5],'fire'),
         M.cube('k_chim',[x-6,70,z-6],[x+6,90,z+6],'clay')]
    return M.group(tag,[x,0,z],k)

def cauldron(M, tag, x, z, r=16):
    """가마솥 + 아궁이 + 하얀 죽.  김 묶음 tag+'steam' (위로 흔들림)"""
    k=[M.cube('stove',[x-r-6,0,z-r-6],[x+r+6,14,z+r+6],'stove'), M.cube('stove_hole',[x-6,2,z-r-6.4],[x+6,10,z-r-5.6],'dark'),
       M.cube('stove_fire',[x-4,3,z-r-6.8],[x+4,8,z-r-6.2],'fire')]
    for j in range(4):
        rr=r-j*2.5; k.append(M.cube('pot',[x-rr,14-j*3,z-rr],[x+rr,17-j*3,z+rr],'iron_pot'))
    k+= [M.cube('pot_rim',[x-r-2,16,z-r-2],[x+r+2,18,z+r+2],'iron_pot'), M.cube('porridge',[x-r+1,16.5,z-r+1],[x+r-1,17.6,z+r-1],'porridge')]
    st=M.group(tag+'steam',[x,30,z],[M.cube('steam',[x-6+(j%2)*5,22+j*9,z-5+(j%3)*3],[x+4+(j%2)*5,29+j*9,z+5+(j%3)*3],'steam') for j in range(4)])
    return M.group(tag+'root',[x,0,z],k+[st])

def tub(M, tag, x, z, fill='lime', w=30, d=22, h=12):
    k=[M.cube('tub_b',[x-w/2,0,z-d/2],[x+w/2,2,z+d/2],'wood_d')]
    for (a,b,c_,e) in [(-w/2,-d/2,w/2,-d/2+2),(-w/2,d/2-2,w/2,d/2),(-w/2,-d/2,-w/2+2,d/2),(w/2-2,-d/2,w/2,d/2)]:
        k.append(M.cube('tub_w',[x+a,0,z+b],[x+c_,h,z+e],'wood'))
    fl=M.group(tag+'fill',[x,2,z],[M.cube('fill',[x-w/2+2,2,z-d/2+2],[x+w/2-2,h-2,z+d/2-2],fill)])
    return M.group(tag+'root',[x,0,z],k+[fl])

def name_brick(M, tag, x, y, z, S=1.0):
    """옆면에 글자(어두운 획)를 새긴 큰 벽돌 (길이 40, 높이 10, 폭 20 × S)"""
    c=lambda n,a,b,col: M.cube(n,[x+a[0]*S,y+a[1]*S,z+a[2]*S],[x+b[0]*S,y+b[1]*S,z+b[2]*S],col)
    k=[c('nb',[-20,0,-10],[20,10,10],'nbrick')]
    for i in range(5):   # 한자처럼 보이는 짧은 획들 (앞면 -z)
        xx=-16+i*7
        k+= [c('ch',[xx,6,-10.3],[xx+4,7,-10.05],'dark'), c('ch',[xx+1.5,3,-10.3],[xx+2.5,8,-10.05],'dark'), c('ch',[xx,3,-10.3],[xx+4,4,-10.05],'dark')]
    return M.group(tag,[x,y,z],k)

def chain(M, tag, x, y, z, n=10, step=6, col='chain_a', branch=False, seed=2):
    """녹말 사슬: 작은 구슬(상자) n개를 이은 줄.  branch=True 면 군데군데 가지가 뻗음 (아밀로펙틴)"""
    rnd=random.Random(seed); k=[]
    for i in range(n):
        cx=x+i*step; k.append(M.cube('bead',[cx-2,y-2,z-2],[cx+2,y+2,z+2],col))
        if i: k.append(M.cube('link',[cx-step+2,y-0.6,z-0.6],[cx-2,y+0.6,z+0.6],col))
        if branch and i%3==1:
            dy=1 if (i//3)%2==0 else -1
            for j in range(1,4):
                by=y+dy*j*step; k.append(M.cube('bead',[cx-2,by-2,z-2],[cx+2,by+2,z+2],col))
                k.append(M.cube('link',[cx-0.6,min(by,by-dy*step)+2,z-0.6],[cx+0.6,max(by,by-dy*step)-2,z+0.6],col))
                if j==2:
                    for h in (1,2): bx=cx+h*step; k.append(M.cube('bead',[bx-2,by-2,z-2],[bx+2,by+2,z+2],col))
    return M.group(tag,[x,y,z],k)

def crystals(M, tag, x, y, z, big=True, seed=4, W=80, H=50):
    """탄산칼슘 알갱이 판: big=True 면 크고 들쭉날쭉(틈 많음), False 면 작고 촘촘"""
    rnd=random.Random(seed); k=[]
    if big:
        for i in range(14):
            s=rnd.uniform(8,16); cx=x+rnd.uniform(-W/2+s,W/2-s); cy=y+rnd.uniform(s,H-s)
            k.append(M.cube('cbig',[cx-s/2,cy-s/2,z-s/3],[cx+s/2,cy+s/2,z+s/3],'crystal' if i%2 else 'crystal_d'))
    else:
        s=5
        for ix in range(int(W/s)):
            for iy in range(int(H/s)):
                cx=x-W/2+ix*s+s/2; cy=y+iy*s+s/2
                k.append(M.cube('csmall',[cx-s/2+0.2,cy-s/2+0.2,z-1.5],[cx+s/2-0.2,cy+s/2-0.2,z+1.5],'crystal' if (ix+iy)%2 else 'crystal_d'))
    k.append(M.cube('cframe',[x-W/2-3,y-3,z+2],[x+W/2+3,y+H+3,z+3],'dark'))
    return M.group(tag,[x,y,z],k)

def lab_table(M, tag, x, z):
    k=[M.cube('tbl',[x-60,30,z-25],[x+60,34,z+25],'table')]+[M.cube('leg',[x+a-2,0,z+b-2],[x+a+2,30,z+b+2],'table') for a in (-56,56) for b in (-21,21)]
    for i,bx in enumerate((-40,-25,30,45)):
        k+= [M.cube('beaker',[x+bx-4,34,z-6],[x+bx+4,46,z+2],'glass'), M.cube('liquid',[x+bx-3.5,34.5,z-5.5],[x+bx+3.5,40,z+1.5],'porridge' if i%2 else 'lime')]
    return M.group(tag,[x,0,z],k)

def press(M, tag, x, z):
    """시험 기계: 두 기둥 + 위에서 내려오는 누름판(tag+'ram') + 가운데 시편(tag+'sample')"""
    k=[M.cube('pbase',[x-26,0,z-20],[x+26,10,z+20],'steel'), M.cube('pcol',[x-24,10,z-4],[x-18,90,z+4],'steel'), M.cube('pcol',[x+18,10,z-4],[x+24,90,z+4],'steel'),
       M.cube('ptop',[x-26,90,z-8],[x+26,100,z+8],'yellow'), M.cube('plate',[x-14,10,z-10],[x+14,13,z+10],'steel')]
    ram=M.group(tag+'ram',[x,60,z],[M.cube('rod',[x-2,60,z-2],[x+2,90,z+2],'steel'), M.cube('ramplate',[x-14,57,z-10],[x+14,60,z+10],'steel')])
    smp=M.group(tag+'sample',[x,13,z],[M.cube('smp',[x-7,13,z-7],[x+7,27,z+7],'mortar')])
    return M.group(tag+'root',[x,0,z],k+[ram,smp])

def arch_bridge(M, tag, x, z, L=260, H=60, W=50):
    """돌 무지개다리 (x 방향으로 놓임) — 계단식 아치"""
    k=[]; n=13
    for i in range(n):
        u=(i+0.5)/n; xx=x-L/2+i*L/n; top=H*math.sin(math.pi*u)*0.4+H*0.6
        under=H*0.85*math.sin(math.pi*u) if 0.15<u<0.85 else 0
        k.append(M.cube('bseg',[xx,under,z-W/2],[xx+L/n+0.2,top,z+W/2],'granite_b' if i%2 else 'granite_bd'))
        k.append(M.cube('brail',[xx,top,z-W/2],[xx+L/n+0.2,top+6,z-W/2+4],'granite_bd')); k.append(M.cube('brail',[xx,top,z+W/2-4],[xx+L/n+0.2,top+6,z+W/2],'granite_bd'))
    return M.group(tag,[x,0,z],k)

def bulldozer(M, tag, x, z):
    k=[M.cube('bd_body',[x-30,10,z-20],[x+30,40,z+20],'yellow'), M.cube('bd_cab',[x-5,40,z-15],[x+25,65,z+15],'yellow'), M.cube('bd_win',[x-5.5,46,z-12],[x-4.5,60,z+12],'glass'),
       M.cube('bd_track',[x-34,0,z-24],[x+34,12,z-14],'dark'), M.cube('bd_track',[x-34,0,z+14],[x+34,12,z+24],'dark'),
       M.cube('bd_arm',[x-48,14,z-18],[x-30,20,z-14],'yellow'), M.cube('bd_arm',[x-48,14,z+14],[x-30,20,z+18],'yellow'), M.cube('bd_blade',[x-54,0,z-26],[x-48,30,z+26],'steel')]
    return M.group(tag,[x,0,z],k)
