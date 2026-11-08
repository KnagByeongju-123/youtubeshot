"""《수원 화성》 블록 부품: 거중기·녹로·유형거(기구), 화성 성벽(여장)·팔달문, 화강암 큰 돌, 무덤(봉분).
   신라인물.py 의 BigModel·person 과 함께 씀.  사람 키 32 (≈1.7m) → 1m ≈ 19"""
import os, sys, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 신라인물 import *

def stone_wall_tex(base=(178,172,160), joint=(110,104,96), seed=7):
    """크고 작은 화강암 돌을 엇갈려 쌓은 성벽 무늬 (아래 큰 돌, 위 작은 돌)"""
    def fn(im,x0,y0,w,h):
        rnd=random.Random(seed); y=h
        while y>0:
            rh=rnd.choice([10,12,14]) if y>h*0.5 else rnd.choice([7,8,10]); y0r=max(0,y-rh); x=-rnd.randint(0,12)
            while x<w:
                rw=rnd.randint(14,26); d_=rnd.randint(-16,16); c=tuple(max(0,min(255,v+d_)) for v in base)
                for yy in range(y0r,y):
                    for xx in range(max(0,x),min(w,x+rw)):
                        edge=(yy==y0r) or (xx==x) or (xx==x+rw-1)
                        e_=rnd.randint(-4,4); im.putpixel((x0+xx,y0+yy),(joint if edge else tuple(max(0,min(255,v+e_)) for v in c))+(255,))
                x+=rw
            y=y0r
    return fn

def hwaseong_palette(M):
    M.swatch('granite_b',(186,180,168),10); M.swatch('granite_bd',(160,154,142),8)
    M.swatch('rope',(196,170,118),5); M.swatch('wood',(140,98,60),6); M.swatch('wood_d',(100,70,42),5)
    M.swatch('pulley',(80,60,40),4); M.swatch('dark',(28,24,24),3); M.swatch('tile',(72,74,80),5); M.swatch('tile_d',(55,57,62),4)
    M.swatch('pillar',(160,58,42),5); M.swatch('dancheong',(70,140,120),6); M.swatch('wall_w',(228,220,198),4)
    M.swatch('brick_g',(120,118,115),8); M.swatch('mound',(105,150,80),10); M.swatch('clay',(170,105,70),10)
    M.swatch('fire',(250,140,40),20); M.swatch('fire_y',(255,215,80),15); M.swatch('smoke',(150,148,145),8)
    M.big('swall', 128, 64, stone_wall_tex())
    M.big('swall_d', 128, 64, stone_wall_tex(base=(150,145,135),joint=(95,90,84)))
    for i in range(4): M.big(f'swall_row{i}', 128, 12, stone_wall_tex(base=(178-i%2*12,172-i%2*12,160-i%2*12),joint=(108,102,95),seed=11+i*5))
    M.big('parapet', 128, 16, brick_wall(base=(125,122,118),joint=(85,82,80),bw=10,bh=5,jit=6))

def wheel(M, tag, cx, cy, cz, r=10, w=3, axis='x', col='wood'):
    """블록 바퀴 (축 방향 axis).  가운데 묶음 중심 = 축 → 'rotation' 으로 굴림"""
    k=[]
    for j in range(-r, r+1, 2):
        hw=math.sqrt(max(0,r*r-j*j))
        if axis=='x':
            k.append(M.cube('wh',[cx-w/2,cy+j-1,cz-hw],[cx+w/2,cy+j+1,cz+hw],col))
        else:
            k.append(M.cube('wh',[cx-hw,cy+j-1,cz-w/2],[cx+hw,cy+j+1,cz+w/2],col))
    if axis=='x': k.append(M.cube('hub',[cx-w/2-0.6,cy-2,cz-2],[cx+w/2+0.6,cy+2,cz+2],'wood_d'))
    else: k.append(M.cube('hub',[cx-2,cy-2,cz-w/2-0.6],[cx+2,cy+2,cz+w/2+0.6],'wood_d'))
    return M.group(tag,[cx,cy,cz],k)

def stone_block(M, tag, x, y, z, sx=22, sy=14, sz=16, col='granite_b'):
    return M.group(tag,[x,y,z],[M.cube('st',[x-sx/2,y,z-sz/2],[x+sx/2,y+sy,z+sz/2],col)])

def geojunggi(M, tag, x=0, z=0):
    """거중기: 양쪽 A자 기둥 + 위 들보 + 위 도르래 4 + 아래 도르래 4(돌을 매닮) + 양옆 얼레(물레).
       묶음: tag+'root', tag+'lower'(아래 도르래+돌, 위아래로 움직임), tag+'winchL'/'winchR'(돌림).
       밧줄 고리(보이지 않는 점): tag+'up{i}', tag+'lo{i}' (i=0..3), tag+'drumL'/'drumR'"""
    k=[]; H=96
    for sx in (-1,1):   # A자 기둥 (z 방향으로 벌어짐)
        k+= [M.cube('post',[x+sx*34-2.5,0,z-24],[x+sx*34+2.5,H,z-19],'wood'), M.cube('post',[x+sx*34-2.5,0,z+19],[x+sx*34+2.5,H,z+24],'wood'),
             M.cube('brace',[x+sx*34-2,30,z-22],[x+sx*34+2,34,z+22],'wood_d'), M.cube('foot',[x+sx*34-5,0,z-28],[x+sx*34+5,4,z+28],'wood_d')]
    k+= [M.cube('beam',[x-40,H-2,z-4],[x+40,H+5,z+4],'wood'), M.cube('beam2',[x-40,H-2,z-23],[x+40,H+2,z-19],'wood_d'),
         M.cube('beam3',[x-40,H-2,z+19],[x+40,H+2,z+23],'wood_d')]
    ups=[]
    for i in range(4):   # 위 도르래 4개 (들보에 매닮)
        px=x-15+i*10
        k+= [M.cube('upulley',[px-3,H-12,z-1.5],[px+3,H-4,z+1.5],'pulley'), M.cube('uhang',[px-0.6,H-4,z-0.6],[px+0.6,H-2,z+0.6],'iron')]
        ups.append(anchor(M,tag+f'up{i}',[px,H-12,z]))
    lo=[]; LY=40
    lk=[M.cube('lblock',[x-20,LY,z-3],[x+20,LY+4,z+3],'wood_d')]
    for i in range(4):
        px=x-15+i*10; lk.append(M.cube('lpulley',[px-3,LY+4,z-1.5],[px+3,LY+11,z+1.5],'pulley')); lo.append(anchor(M,tag+f'lo{i}',[px,LY+11,z]))
    lk+= [M.cube('hook',[x-0.8,LY-8,z-0.8],[x+0.8,LY,z+0.8],'iron'), M.cube('sling',[x-12,LY-10,z-0.6],[x+12,LY-8,z+0.6],'rope')]
    lk.append(M.cube('stone',[x-14,LY-26,z-10],[x+14,LY-10,z+10],'granite_b'))
    lower=M.group(tag+'lower',[x,LY,z],lk+lo)
    winches=[]
    for sx,nm in ((-1,'L'),(1,'R')):   # 얼레: 가로 굴대 + 손잡이 살 4개 (굴대 축 = z)
        wx=x+sx*52
        frame=[M.cube('wframe',[wx-3,0,z-14],[wx+3,22,z-11],'wood_d'), M.cube('wframe',[wx-3,0,z+11],[wx+3,22,z+14],'wood_d')]
        dk=[M.cube('drum',[wx-4,14,z-11],[wx+4,22,z+11],'wood')]
        for a in range(4):
            ang=a*math.pi/2; ex,ey=math.cos(ang)*16,math.sin(ang)*16
            dk.append(M.cube('spoke',[wx+min(0,ex)-1,18+min(0,ey)-1,z-13],[wx+max(0,ex)+1,18+max(0,ey)+1,z-11.5],'wood_d'))
        drum=M.group(tag+'winch'+nm,[wx,18,z],dk+[anchor(M,tag+'drum'+nm,[wx,22,z])])
        k+= frame; winches.append(drum)
    root=M.group(tag+'root',[x,0,z],k+ups+[lower]+winches)
    return root

def noklo(M, tag, x=0, z=0, lean=18):
    """녹로: 비스듬히 세운 긴 장대 끝에 도르래, 아래에 얼레.  장대 묶음 tag+'pole' (기울기 = 고정), 고리 tag+'top', tag+'drum'"""
    L=130
    pk=[M.cube('pole',[x-3,0,z-3],[x+3,L,z+3],'wood'), M.cube('ppulley',[x-4,L-6,z-6],[x+4,L+2,z+0],'pulley')]
    pole=M.group(tag+'pole',[x,0,z],pk+[anchor(M,tag+'top',[x,L-6,z-3])],rotation=(-lean,0,0))
    base=[M.cube('nbase',[x-14,0,z-10],[x+14,5,z+10],'wood_d'), M.cube('nprop',[x-2,0,z+8],[x+2,70,z+12],'wood_d')]
    dk=[M.cube('ndrum',[x-12,8,z+18],[x+12,15,z+24],'wood')]
    for a in range(4):
        ang=a*math.pi/2; ey,ez=math.sin(ang)*13,math.cos(ang)*13
        dk.append(M.cube('nspoke',[x+12,11.5+min(0,ey)-1,z+21+min(0,ez)-1],[x+13.5,11.5+max(0,ey)+1,z+21+max(0,ez)+1],'wood_d'))
    drum=M.group(tag+'drum_g',[x,11.5,z+21],dk+[anchor(M,tag+'drum',[x,15,z+21])])
    return M.group(tag+'root',[x,0,z],base+[pole,drum])

def yuhyeonggeo(M, tag, x=0, z=0):
    """유형거: 큰 바퀴 두 개 + 낮은 짐칸 + 긴 손잡이 (앞 = -z 로 끎).  바퀴 묶음 tag+'wheelL/R' (축 x)"""
    k=[M.cube('bed',[x-12,10,z-20],[x+12,13,z+20],'wood'), M.cube('rail',[x-13,13,z-20],[x-11,16,z+20],'wood_d'), M.cube('rail',[x+11,13,z-20],[x+13,16,z+20],'wood_d'),
       M.cube('handle',[x-11,12,z-46],[x-8,14.5,z-20],'wood_d'), M.cube('handle',[x+8,12,z-46],[x+11,14.5,z-20],'wood_d'),
       M.cube('crossbar',[x-11,12,z-46],[x+11,14.5,z-43],'wood_d'), M.cube('axle',[x-17,10,z-1],[x+17,12,z+1],'iron')]
    wl=wheel(M,tag+'wheelL',x-16,11,z,r=11,w=3,axis='x'); wr=wheel(M,tag+'wheelR',x+16,11,z,r=11,w=3,axis='x')
    return M.group(tag+'root',[x,0,z],k+[wl,wr])

def hwaseong_wall(M, tag, x0, x1, z, H=100, T=40, rows=10, parapet=True):
    """성벽 한 토막 (x0→x1, 앞면 z).  줄(row) 묶음 목록을 돌려줌 → 아래에서부터 차례로 쌓아 올리기(grow)
       여장: 위에 낮은 벽돌 담 + 총구멍(어두운 칸) + 담 사이 빈틈"""
    out=[]; rh=H/rows
    for j in range(rows):
        g=M.group(f'{tag}row{j}',[(x0+x1)/2,j*rh,z],[M.cube('wrow',[x0,j*rh,z],[x1,(j+1)*rh,z+T],f'swall_row{j%4}')])
        out.append(g)
    if parapet:
        pk=[]; seg=26
        xs=x0
        while xs<x1-4:
            xe=min(x1,xs+seg-4)
            pk.append(M.cube('par',[xs,H,z],[xe,H+16,z+6],'parapet'))
            pk.append(M.cube('par_cap',[xs-0.5,H+16,z-0.5],[xe+0.5,H+18,z+6.5],'tile'))
            mx=(xs+xe)/2; pk.append(M.cube('gunhole',[mx-2,H+5,z-0.3],[mx+2,H+9,z+0.2],'dark'))
            xs+=seg
        pk.append(M.cube('walkway',[x0,H-1,z+6],[x1,H+0.5,z+T],'granite_bd'))
        out.append(M.group(f'{tag}parapet',[(x0+x1)/2,H,z],pk))
    return out

def gate(M, tag, x=0, z=0, W=130, H=70):
    """팔달문 비슷한 성문: 화강암 홍예(무지개) 문 + 2층 문루 (붉은 기둥·검은 기와).  앞 = -z"""
    k=[M.cube('gbase',[x-W/2,0,z-30],[x-16,H,z+30],'granite_b'), M.cube('gbase',[x+16,0,z-30],[x+W/2,H,z+30],'granite_b'),
       M.cube('garch',[x-16,44,z-30],[x+16,H,z+30],'granite_b')]
    for j in range(5):   # 무지개 모양 (계단으로)
        hw=16-j*3.2
        k.append(M.cube('garch_c',[x-16,32+j*2.5,z-30.2],[x-hw,34.5+j*2.5,z+30.2],'granite_bd'))
        k.append(M.cube('garch_c',[x+hw,32+j*2.5,z-30.2],[x+16,34.5+j*2.5,z+30.2],'granite_bd'))
    k.append(M.cube('gdoor',[x-15,0,z-1],[x+15,32,z+1],'wood_d'))
    k.append(M.cube('gdark',[x-16,0,z-30.4],[x+16,30,z-29.8],'dark'))
    y=H
    for fl,(w,h) in enumerate([(100,30),(84,24)]):
        for px in (-w/2,-w/6,w/6-5,w/2-5):
            for pz in (-24,19):
                k.append(M.cube('gpil',[x+px,y,z+pz],[x+px+5,y+h,z+pz+5],'pillar'))
        k.append(M.cube('gwall',[x-w/2+3,y,z-20],[x+w/2-3,y+h*0.3,z+20],'wall_w'))
        k.append(M.cube('gbeam',[x-w/2,y+h-4,z-26],[x+w/2,y+h,z+26],'dancheong'))
        y+=h
        for j in range(4):
            e=20-j*5; k.append(M.cube('groof',[x-w/2-e,y+j*4,z-26-e],[x+w/2+e,y+j*4+4,z+26+e],'tile' if j%2==0 else 'tile_d'))
        y+=16
    return M.group(tag+'root',[x,0,z],k)

def mound(M, tag, x, z, r=60):
    """봉분 (둥근 무덤) — 층층이 줄어드는 초록 상자"""
    k=[]
    for j in range(7):
        rr=r*math.cos(j/7*math.pi/2); k.append(M.cube('mound',[x-rr,j*5,z-rr],[x+rr,j*5+5,z+rr],'mound'))
    k.append(M.cube('mound_base',[x-r-4,0,z-r-4],[x+r+4,4,z+r+4],'granite_b'))
    return M.group(tag,[x,0,z],k)
