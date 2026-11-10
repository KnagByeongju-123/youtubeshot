"""《13층 아래》 배경 부품: 연구소 층(복도 껍데기·무늬 벽·문·층 번호판)·소품(유리관·조작판·상자·배관·경보등) · 엘리베이터 통로 · 지상(풀밭·고물 더미·건물)
   상자 수를 줄이려고 벽·바닥의 자잘한 무늬(판·리벳·줄무늬·배관·사다리)는 큰 무늬 칸에 그려 넣음.  카메라는 -z 에서 +z 를 봄, 복도는 z 방향"""
import os, sys, math, random, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import ImageDraw, ImageFont
from 블록인물 import Model, move, anchor, Anim, find, U
from 신라인물 import BigModel
from 탈출인물 import *

_FONT=None
def font(sz):
    return ImageFont.truetype(glob.glob('/usr/share/fonts/**/NanumGothicExtraBold.ttf',recursive=True)[0],sz)
def _noise(im,x,y,w,h,amt,seed=0):
    r=random.Random(seed); px=im.load()
    for yy in range(y,y+h):
        for xx in range(x,x+w):
            c=px[xx,yy]; d=r.randint(-amt,amt); px[xx,yy]=(max(0,min(255,c[0]+d)),max(0,min(255,c[1]+d)),max(0,min(255,c[2]+d)),255)

# ---------------- 큰 무늬 ----------------
def t_wall(base,line,stripe=None,vent=True,pipe=None,seed=1):
    """벽 한 칸 (64×96): 판 이음매·리벳·아래 걸레받이·줄무늬 띠·환기 창살·배관"""
    def fn(im,x,y,w,h):
        d=ImageDraw.Draw(im); d.rectangle([x,y,x+w-1,y+h-1],fill=base)
        d.rectangle([x,y+h-10,x+w-1,y+h-1],fill=tuple(int(v*0.6) for v in base))          # 걸레받이
        for xx in (0,w//2): d.line([(x+xx,y),(x+xx,y+h-11)],fill=line)
        d.line([(x,y+30),(x+w-1,y+30)],fill=line); d.line([(x,y+62),(x+w-1,y+62)],fill=line)
        for xx in (3,w//2-4,w//2+3,w-4):
            for yy in (4,26,34,58,66): d.point((x+xx,y+yy),fill=tuple(int(v*0.55) for v in base))
        if stripe: d.rectangle([x,y+40,x+w-1,y+46],fill=stripe)
        if vent:
            for k in range(5): d.line([(x+8,y+10+k*3),(x+24,y+10+k*3)],fill=tuple(int(v*0.45) for v in base))
        if pipe:
            d.rectangle([x,y+70,x+w-1,y+75],fill=pipe); d.line([(x,y+70),(x+w-1,y+70)],fill=tuple(min(255,int(v*1.25)) for v in pipe))
            d.rectangle([x+w//2-2,y+68,x+w//2+2,y+77],fill=tuple(int(v*0.7) for v in pipe))
        _noise(im,x,y,w,h,5,seed)
    return fn
def t_hazard(im,x,y,w,h):
    from PIL import Image
    t=Image.new('RGBA',(w,h),(235,195,40,255)); d=ImageDraw.Draw(t)       # 칸 밖으로 번지지 않게 따로 그려 붙임
    for k in range(-h,w,16): d.polygon([(k,h-1),(k+8,h-1),(k+8+h,0),(k+h,0)],fill=(28,28,32,255))
    im.paste(t,(x,y))
def t_floor(a,b,grid=(0,0,0),seed=2):
    def fn(im,x,y,w,h):
        d=ImageDraw.Draw(im); d.rectangle([x,y,x+w-1,y+h-1],fill=a)
        d.rectangle([x,y,x+w//2-1,y+h//2-1],fill=b); d.rectangle([x+w//2,y+h//2,x+w-1,y+h-1],fill=b)
        d.rectangle([x,y,x+w-1,y+h-1],outline=tuple(int(v*0.7) for v in a)); _noise(im,x,y,w,h,6,seed)
    return fn
def t_grate(im,x,y,w,h):
    d=ImageDraw.Draw(im); d.rectangle([x,y,x+w-1,y+h-1],fill=(58,60,68))
    for k in range(0,w,8): d.line([(x+k,y),(x+k,y+h-1)],fill=(30,31,36)); d.line([(x,y+k),(x+w-1,y+k)],fill=(30,31,36))
    d.rectangle([x,y,x+w-1,y+h-1],outline=(110,112,120)); _noise(im,x,y,w,h,5,3)
def t_ceil(base,lamp):
    def fn(im,x,y,w,h):
        d=ImageDraw.Draw(im); d.rectangle([x,y,x+w-1,y+h-1],fill=base); d.rectangle([x,y,x+w-1,y+h-1],outline=tuple(int(v*0.7) for v in base))
        d.rectangle([x+w//2-6,y+6,x+w//2+6,y+h-7],fill=lamp); _noise(im,x,y,w,h,4,4)
    return fn
def t_door(im,x,y,w,h):
    d=ImageDraw.Draw(im); d.rectangle([x,y,x+w-1,y+h-1],fill=(150,154,164)); d.rectangle([x+2,y+2,x+w-3,y+h-3],outline=(96,100,110))
    d.line([(x+w//2,y),(x+w//2,y+h-1)],fill=(60,62,70),width=2)
    for k in range(4): d.rectangle([x+8,y+14+k*20,x+w//2-6,y+22+k*20],outline=(110,114,124)); d.rectangle([x+w//2+6,y+14+k*20,x+w-9,y+22+k*20],outline=(110,114,124))
    d.rectangle([x,y+h-8,x+w-1,y+h-1],fill=(235,195,40)); _noise(im,x,y,w,h,5,5)
def t_label(txt,fg=(255,220,60),bg=(24,26,32)):
    def fn(im,x,y,w,h):
        d=ImageDraw.Draw(im); d.rectangle([x,y,x+w-1,y+h-1],fill=bg); d.rectangle([x,y,x+w-1,y+h-1],outline=fg)
        f=font(h-6); tw=d.textlength(txt,font=f); d.text((x+(w-tw)/2,y+1),txt,font=f,fill=fg)
    return fn
def t_crate(col,seed=0):
    def fn(im,x,y,w,h):
        d=ImageDraw.Draw(im); d.rectangle([x,y,x+w-1,y+h-1],fill=col); dk=tuple(int(v*0.65) for v in col)
        d.rectangle([x,y,x+w-1,y+h-1],outline=dk,width=2); d.line([(x,y),(x+w-1,y+h-1)],fill=dk,width=2); d.line([(x+w-1,y),(x,y+h-1)],fill=dk,width=2); _noise(im,x,y,w,h,6,seed)
    return fn
def t_screen(col=(60,230,140)):
    def fn(im,x,y,w,h):
        d=ImageDraw.Draw(im); d.rectangle([x,y,x+w-1,y+h-1],fill=(14,22,26)); r=random.Random(w*7+h)
        for k in range(3,h-3,4): d.line([(x+3,y+k),(x+3+r.randint(6,w-8),y+k)],fill=col)
        d.rectangle([x,y,x+w-1,y+h-1],outline=(70,74,84))
    return fn
def t_shaft(im,x,y,w,h):
    """통로 벽 (64×96): 어두운 철판 + X 자 철골 + 굵은 가로 들보"""
    d=ImageDraw.Draw(im); d.rectangle([x,y,x+w-1,y+h-1],fill=(50,52,60))
    d.line([(x,y),(x+w-1,y+h-1)],fill=(78,80,90),width=3); d.line([(x+w-1,y),(x,y+h-1)],fill=(78,80,90),width=3)
    d.rectangle([x,y,x+w-1,y+7],fill=(92,94,104)); d.rectangle([x,y+h-8,x+w-1,y+h-1],fill=(92,94,104))
    d.rectangle([x,y,x+4,y+h-1],fill=(70,72,82)); d.rectangle([x+w-5,y,x+w-1,y+h-1],fill=(70,72,82)); _noise(im,x,y,w,h,5,6)
def t_ladder(im,x,y,w,h):
    d=ImageDraw.Draw(im); d.rectangle([x,y,x+w-1,y+h-1],fill=(0,0,0,0))
    px=im.load()
    for yy in range(y,y+h):
        for xx in range(x,x+w): px[xx,yy]=(0,0,0,0)
    d.rectangle([x+1,y,x+3,y+h-1],fill=(210,180,60)); d.rectangle([x+w-4,y,x+w-2,y+h-1],fill=(210,180,60))
    for k in range(3,h,8): d.rectangle([x+1,y+k,x+w-2,y+k+1],fill=(230,200,80))
def t_grass(im,x,y,w,h):
    d=ImageDraw.Draw(im); d.rectangle([x,y,x+w-1,y+h-1],fill=(92,150,84)); r=random.Random(9)
    for k in range(260): xx=x+r.randint(0,w-1); yy=y+r.randint(0,h-1); d.point((xx,yy),fill=r.choice([(78,132,72),(110,170,96),(124,182,100),(70,120,66)]))
def t_water(im,x,y,w,h):
    d=ImageDraw.Draw(im); d.rectangle([x,y,x+w-1,y+h-1],fill=(46,104,170)); r=random.Random(11)
    for k in range(22): xx=x+r.randint(0,w-12); yy=y+r.randint(0,h-2); d.line([(xx,yy),(xx+r.randint(5,11),yy)],fill=(96,160,214))
def t_window(lit):
    def fn(im,x,y,w,h):
        d=ImageDraw.Draw(im); d.rectangle([x,y,x+w-1,y+h-1],fill=(70,74,84)); r=random.Random(w+h+len(lit))
        for yy in range(4,h-6,10):
            for xx in range(4,w-6,9): d.rectangle([x+xx,y+yy,x+xx+5,y+yy+6],fill=r.choice(lit))
    return fn

def lab_palette(M):
    S=M.swatch
    S('steel',(150,156,165),6); S('steel_d',(105,110,120),5); S('dark',(40,42,50),4); S('black',(14,14,18),2); S('white',(232,234,238),3)
    S('glass',(150,215,235),3); S('glass_d',(96,170,196),3); S('lamp',(255,246,214),2); S('lamp_c',(190,235,255),2); S('red',(240,50,44),3); S('red_d',(150,30,30),3)
    S('laser',(255,40,60),2); S('laser_c',(255,170,180),2); S('yellow',(235,195,40),4); S('orange',(236,140,50),5); S('green_l',(70,230,130),2)
    S('pipe',(170,96,60),6); S('pipe_b',(70,120,170),6); S('conc',(128,128,124),8); S('conc_d',(98,98,96),7); S('rubber',(34,34,38),3)
    S('wood',(150,112,70),6); S('spark',(255,240,150),2); S('steam',(232,236,240),4); S('smoke',(120,118,116),8); S('wat',(46,104,170),5); S('wat_l',(110,170,220),4)
    S('grass_a',(92,150,84),10); S('grass_b',(104,164,92),10); S('grass_c',(82,138,76),10); S('dirt',(140,108,78),8); S('leaf',(60,120,70),10); S('leaf_d',(46,98,58),9); S('trunk',(104,78,56),6)
    S('sun',(255,214,120),3); S('sun_c',(255,244,200),2); S('cloud',(250,236,226),4); S('bld',(86,90,102),6); S('bld_d',(64,66,78),5); S('fence',(120,124,132),5)
    B=M.big
    B('w_lab',64,96,t_wall((214,220,226),(170,176,186),stripe=(60,170,170),seed=1)); B('w_lab2',64,96,t_wall((206,212,220),(160,166,178),stripe=None,vent=False,pipe=(70,120,170),seed=2))
    B('w_dark',64,96,t_wall((84,88,100),(54,56,66),stripe=(235,195,40),seed=3)); B('w_ware',64,96,t_wall((132,126,116),(96,90,84),stripe=None,pipe=(170,96,60),seed=4))
    B('w_conc',64,96,t_wall((124,126,122),(94,96,94),stripe=None,vent=False,pipe=(70,120,170),seed=5)); B('w_sec',64,96,t_wall((52,58,82),(30,34,52),stripe=(230,50,50),seed=6))
    B('w_duct',64,64,t_wall((150,154,160),(104,108,116),stripe=None,vent=False,seed=7))
    B('f_lab',64,64,t_floor((196,200,206),(184,188,196))); B('f_dark',64,64,t_floor((72,74,84),(64,66,76))); B('f_conc',64,64,t_floor((112,112,108),(104,104,100),seed=8)); B('f_grate',64,64,t_grate)
    B('c_lab',64,64,t_ceil((170,174,182),(255,246,214))); B('c_dark',64,64,t_ceil((46,48,56),(255,200,150))); B('c_red',64,64,t_ceil((46,48,56),(255,70,60)))
    B('door',64,96,t_door); B('hazard',64,16,t_hazard); B('shaft',64,96,t_shaft); B('ladder',16,96,t_ladder); B('grassb',64,64,t_grass); B('water',64,64,t_water)
    B('crate_a',32,32,t_crate((176,132,80),1)); B('crate_b',32,32,t_crate((120,140,110),2)); B('crate_c',32,32,t_crate((96,116,150),3))
    B('scr_g',32,24,t_screen((60,230,140))); B('scr_b',32,24,t_screen((90,190,255))); B('scr_r',32,24,t_screen((255,90,80)))
    B('win_n',48,64,t_window([(40,44,56),(40,44,56),(255,214,120),(40,44,56)])); B('win_d',48,64,t_window([(120,150,180),(150,180,205),(96,120,150)]))
    for n in range(1,14): B(f'lbl{n}',48,20,t_label(f'B{n}'))
    B('lbl0',48,20,t_label('G',fg=(120,255,160)))

# ---------------- 층 껍데기 ----------------
def corridor(M,z0,z1,W=200,H=96,wall='w_lab',wall2=None,floor='f_lab',ceil='c_lab',ceiling=True,x0=0):
    """복도 (z 방향). 벽은 64 칸마다 한 장, 바닥은 64×64 칸. wall2 를 주면 벽 무늬를 번갈아 씀"""
    k=[]; nx=int(math.ceil(W/64)); fw=W/nx
    for i,z in enumerate(range(int(z0),int(z1),64)):
        zz=min(z+64,z1); wt=wall2 if (wall2 and i%2) else wall
        k.append(M.cube('wallL',[x0+W/2,0,z],[x0+W/2+8,H,zz],wt)); k.append(M.cube('wallR',[x0-W/2-8,0,z],[x0-W/2,H,zz],wt))
        for j in range(nx):
            k.append(M.cube('floor',[x0-W/2+j*fw,-8,z],[x0-W/2+(j+1)*fw,0,zz],floor))
            if ceiling: k.append(M.cube('ceil',[x0-W/2+j*fw,H,z],[x0-W/2+(j+1)*fw,H+8,zz],ceil))
    return k
def end_wall(M,z,W=200,H=96,wall='w_lab',x0=0,door=None,label=None,facing=-1):
    """복도 끝 벽. door='door' 면 가운데 엘리베이터 문(64 폭) 자리를 비우고 문틀·층 번호판을 붙임. facing=-1: 복도 쪽(-z)을 봄"""
    k=[]; t=8; za,zb=(z,z+t) if facing<0 else (z-t,z)
    if door:
        side=(W-72)/2
        k+= [M.cube('endL',[x0+36,0,za],[x0+W/2,H,zb],wall), M.cube('endR',[x0-W/2,0,za],[x0-36,H,zb],wall), M.cube('endT',[x0-36,84,za],[x0+36,H,zb],'steel_d')]
        zf=za-1.2 if facing<0 else zb+1.2
        k+= [M.cube('frameL',[x0+32,0,min(za,zf)],[x0+38,86,max(za,zf)],'yellow'), M.cube('frameR',[x0-38,0,min(za,zf)],[x0-32,86,max(za,zf)],'yellow'), M.cube('frameT',[x0-38,80,min(za,zf)],[x0+38,86,max(za,zf)],'yellow')]
        if label is not None:
            zl=za-2.2 if facing<0 else zb+2.2
            k.append(M.cube('label',[x0-18,87,min(za,zl)],[x0+18,95.5,max(za,zl)],'dark',**{('north' if facing<0 else 'south'):f'lbl{label}'}))
    else:
        for i,x in enumerate(range(int(x0-W/2),int(x0+W/2),64)): k.append(M.cube('end',[x,0,za],[min(x+64,x0+W/2),H,zb],wall))
    return k
def sliding_door(M,tag,x0,z,facing=-1):
    """엘리베이터 문 두 짝 (묶음 tag_L·tag_R → x 로 밀어 엶)"""
    za,zb=(z+1.5,z+5.5)
    l=M.group(tag+'L',[x0+16,0,z],[M.cube('doorL',[x0,0,za],[x0+32,84,zb],'door')]); r=M.group(tag+'R',[x0-16,0,z],[M.cube('doorR',[x0-32,0,za],[x0,84,zb],'door')])
    return l,r
def big_label(M,x,y,z,n,w=60,face='north'):
    h=w*20/48
    return [M.cube('biglabel',[x-w/2,y,z-1.6],[x+w/2,y+h,z],'dark',**{face:f'lbl{n}'})]
def ceiling_lamps(M,z0,z1,W=200,H=96,col='lamp',step=128):
    return [M.cube('clamp',[-W*0.18,H-2.4,z],[W*0.18,H-0.6,z+20],col) for z in range(int(z0)+40,int(z1)-20,step)]
def alarm_lamp(M,tag,x,y,z):
    """빙글 도는 붉은 경보등 (묶음을 y 로 돌림)"""
    g=M.group(tag,[x,y,z],[M.cube('al_base',[x-4,y+3,z-4],[x+4,y+6,z+4],'dark'), M.cube('al_lamp',[x-3,y-3,z-3],[x+3,y+3,z+3],'red'), M.cube('al_beam',[x-16,y-1.2,z-1.2],[x+16,y+1.2,z+1.2],'laser_c')])
    return g
def pipe_run(M,x,y,z0,z1,col='pipe',r=3):
    k=[M.cube('pipe',[x-r,y-r,z0],[x+r,y+r,z1],col)]
    for z in range(int(z0)+30,int(z1),90): k.append(M.cube('pipe_j',[x-r-1,y-r-1,z-2],[x+r+1,y+r+1,z+2],'steel_d'))
    return k
def crate(M,x,z,s=24,y=0,tex='crate_a',name='crate'):
    return M.cube(name,[x-s/2,y,z-s/2],[x+s/2,y+s,z+s/2],tex)
def crate_stack(M,x,z,n=3,s=24,seed=0):
    r=random.Random(seed*5+int(x)+int(z)); k=[]; t=['crate_a','crate_b','crate_c']
    for i in range(n):
        dx=r.uniform(-3,3) if i else 0; k.append(crate(M,x+dx,z+r.uniform(-2,2) if i else z,s-(i%2)*2,y=sum(s-(j%2)*2 for j in range(i)),tex=t[(i+seed)%3]))
    return k
def console(M,x,z,w=40,screen='scr_g',face='north'):
    """조작판: 받침 + 비스듬한 판 + 화면"""
    return [M.cube('con_base',[x-w/2,0,z-8],[x+w/2,22,z+8],'steel_d'), M.cube('con_top',[x-w/2-1,22,z-10],[x+w/2+1,26,z+9],'dark'),
            M.cube('con_scr',[x-w/2+3,26,z+3],[x+w/2-3,48,z+7],'dark',**{face:screen}), M.cube('con_key',[x-w/2+4,26,z-8],[x+w/2-4,27.2,z+1],'steel'),
            M.cube('con_btn',[x-w/2+6,27.2,z-6],[x-w/2+10,28.4,z-2],'red'), M.cube('con_btn',[x+w/2-10,27.2,z-6],[x+w/2-6,28.4,z-2],'green_l')]
def tube(M,tag,x,z,lit=False,robot=True):
    """유리관 (실험체 보관): 받침·뚜껑·유리(하늘색 판 넷)·안의 작은 로봇 그림자. 유리 묶음 tag_glass (깨질 때 숨김)"""
    k=[M.cube('tb_base',[x-13,0,z-13],[x+13,8,z+13],'steel_d'), M.cube('tb_cap',[x-13,62,z-13],[x+13,70,z+13],'steel_d'), M.cube('tb_light',[x-9,60.5,z-9],[x+9,62,z+9],'lamp_c' if lit else 'glass_d'),
       M.cube('tb_back',[x-11,8,z+9],[x+11,62,z+11],'glass_d'), M.cube('tb_pl',[x-12,8,z-12],[x-10,62,z-10],'steel'), M.cube('tb_pr',[x+10,8,z-12],[x+12,62,z-10],'steel')]
    gl=M.group(tag+'glass',[x,35,z-11],[M.cube('tb_glass',[x-10,8,z-11.6],[x+10,62,z-10.8],'glass'), M.cube('tb_shine',[x-7,14,z-12],[x-5,56,z-11.4],'white')])
    if robot and not lit: k+= [M.cube('tb_bot',[x-4,12,z-3],[x+4,22,z+4],'dark'), M.cube('tb_bot',[x-3,22,z-2],[x+3,27,z+3],'steel_d')]
    return k,gl
def locker_row(M,x,z0,n,side=1):
    k=[]
    for i in range(n):
        z=z0+i*22; k+= [M.cube('locker',[min(x,x+side*14),0,z],[max(x,x+side*14),64,z+20],'steel' if i%2 else 'steel_d'), M.cube('lk_vent',[x+side*14 if side<0 else x-0.6,50,z+4],[x+side*14+0.6 if side<0 else x,58,z+16],'dark')]
    return k
def shelf_unit(M,x,z,w=60,levels=3,seed=0,depth=18):
    r=random.Random(seed); k=[M.cube('sh_l',[x-w/2,0,z],[x-w/2+2.5,levels*26+6,z+depth],'steel_d'), M.cube('sh_r',[x+w/2-2.5,0,z],[x+w/2,levels*26+6,z+depth],'steel_d')]
    for l in range(levels+1):
        y=4+l*26; k.append(M.cube('sh_b',[x-w/2,y,z],[x+w/2,y+2.2,z+depth],'steel'))
        if l<levels:
            xx=x-w/2+6
            while xx<x+w/2-12:
                s=r.choice([10,13,16]); k.append(M.cube('sh_box',[xx,y+2.2,z+2],[xx+s,y+2.2+s,z+2+min(s,depth-3)],r.choice(['crate_a','crate_b','crate_c']))); xx+=s+r.choice([2,4,7])
    return k

# ---------------- 통로 (엘리베이터) ----------------
def shaft(M,levels,W=176,LH=120,first=13):
    """엘리베이터 통로: 네 벽(무늬) + 층마다 문틀·번호판·작은 등 + 사다리(무늬 판) + 굵은 줄 넷. 문은 -z 벽(카메라 쪽)이 아니라 +z 벽에 둠 → 통로 안에서 보임
       층 i 의 바닥 높이 = i*LH (i=0 이 first 층). 돌려줌: 상자들"""
    k=[]; H=levels*LH; h=W/2
    for i in range(levels):
        y=i*LH
        for j,x in enumerate(range(int(-h),int(h),64)):
            xe=min(x+64,h)
            for yy in (y,y+LH/2):
                k.append(M.cube('sw_s',[x,yy,h],[xe,yy+LH/2,h+8],'shaft')) if not (abs((x+xe)/2)<36 and yy==y) else None
                k.append(M.cube('sw_n',[x,yy,-h-8],[xe,yy+LH/2,-h],'shaft'))
                k.append(M.cube('sw_e',[h,yy,x],[h+8,yy+LH/2,xe],'shaft')); k.append(M.cube('sw_w',[-h-8,yy,x],[-h,yy+LH/2,xe],'shaft'))
        n=first-i
        # +z 벽의 문 자리(가운데, 높이 0~LH/2) : 어두운 문 + 노란 틀 + 번호판 + 등
        k+= [M.cube('sd_door',[-32,y,h+1],[32,y+LH/2-4,h+6],'door'), M.cube('sd_fl',[32,y,h-1.4],[38,y+LH/2,h+2],'yellow'), M.cube('sd_fr',[-38,y,h-1.4],[-32,y+LH/2,h+2],'yellow'),
             M.cube('sd_ft',[-38,y+LH/2-5,h-1.4],[38,y+LH/2+1,h+2],'yellow'), M.cube('sd_sill',[-40,y-3,h-14],[40,y,h],'steel_d')]
        if 0<=n<=13: k.append(M.cube('sd_lbl',[-24,y+LH/2+4,h-2.6],[24,y+LH/2+24,h-0.4],'dark',north=f'lbl{n}'))
        k.append(M.cube('sd_lamp',[44,y+LH/2-12,h-3],[50,y+LH/2-6,h-0.2],'lamp_c' if i%2 else 'lamp'))
        k.append(M.cube('sd_beam',[-h,y+LH-6,-h],[h,y+LH-2,-h+6],'steel_d'))
    k.append(M.cube('ladder',[h-30,0,h-3.2],[h-14,H,h-2.2],'dark',north='ladder'))    # 사다리 (그림) — 아래에서 다시 칸마다 붙임
    k.pop()
    for yy in range(0,int(H),96): k.append(M.cube('ladder',[58,yy,h-3.4],[74,min(yy+96,H),h-2.4],'ladder'))
    for cx,cz in ((-30,-40),(30,-40),(-60,20),(60,-10)): k.append(M.cube('cable',[cx-1.2,-200,cz-1.2],[cx+1.2,H+200,cz+1.2],'rubber'))
    k.append(M.cube('rail_l',[h-6,-200,-6],[h-1,H+200,6],'steel_d')); k.append(M.cube('rail_r',[-h+1,-200,-6],[-h+6,H+200,6],'steel_d'))
    k.append(M.cube('pit',[-h,-240,-h],[h,-200,h],'black'))
    return [c for c in k if c]
def elevator_car(M,tag,W=120):
    """엘리베이터 (원점 = 지붕 한가운데 높이 0). 지붕 위에 기계 상자·경광등·난간"""
    h=W/2
    k=[M.cube('car',[-h,-90,-h],[h,0,h],'steel'), M.cube('car_band',[-h-1,-52,-h-1],[h+1,-44,h+1],'yellow'), M.cube('car_roof',[-h-3,0,-h-3],[h+3,3,h+3],'steel_d'),
       M.cube('car_box',[-h+10,3,h-40],[-h+44,22,h-10],'dark'), M.cube('car_box2',[h-40,3,-h+10],[h-14,14,-h+34],'steel_d'), M.cube('car_wheel',[-6,3,-6],[6,16,6],'dark'),
       M.cube('car_hatch',[10,3,10],[40,5,40],'yellow'), M.cube('car_lamp',[-h+18,22,h-30],[-h+26,28,h-22],'red')]
    for sx in (-1,1): k.append(M.cube('car_rail',[sx*(h-2)-1,3,-h+2],[sx*(h-2)+1,18,h-2],'yellow'))
    return M.group(tag+'root',[0,0,0],k)

# ---------------- 지상 ----------------
def field(M,R=704,tile=64,seed=1):
    r=random.Random(seed); k=[M.cube('far_ground',[-5000,-20,-5000],[5000,-15,5000],'grass_a')]
    for x in range(-R,R,tile):
        for z in range(-R,R,tile): k.append(M.cube('g',[x,-16,z],[x+tile,0,z+tile],r.choice(['grass_a','grass_b','grass_c','grassb'])))
    return k
def tree(M,x,z,h=70,seed=0):
    r=random.Random(seed+int(x)); t=h/12
    k=[M.cube('trunk',[x-t,0,z-t],[x+t,h*0.5,z+t],'trunk')]
    for i,(w,y0,hh) in enumerate([(h*0.62,h*0.38,h*0.24),(h*0.46,h*0.6,h*0.22),(h*0.26,h*0.8,h*0.2)]): k.append(M.cube('leaf',[x-w/2,y0,z-w/2],[x+w/2,y0+hh,z+w/2],'leaf' if (i+seed)%2 else 'leaf_d'))
    return k
def tuft(M,x0,x1,z0,z1,n,seed=0,avoid=()):
    r=random.Random(seed); k=[]; i=0; tries=0
    while i<n and tries<n*20:
        tries+=1; x=r.uniform(x0,x1); z=r.uniform(z0,z1)
        if any(abs(x-ax)<aw and abs(z-az)<ad for ax,az,aw,ad in avoid): continue
        if i%7==0: k.append(M.cube('flower',[x-1,0,z-1],[x+1,r.uniform(3,5),z+1],r.choice(['yellow','white','orange','red'])))
        else: k.append(M.cube('tuft',[x-0.8,0,z-0.8],[x+0.8,r.uniform(2.5,6),z+0.8],r.choice(['leaf','grass_b','leaf_d'])))
        i+=1
    return k
def junk_pile(M,x,z,r_=70,n=60,seed=3):
    """고물 더미: 색이 제각각인 로봇 부품·철판·바퀴"""
    r=random.Random(seed); k=[]; cols=['p_or','p_gr','p_pu','p_rd','p_ye','rust','steel','steel_d','frame','joint','teal','tank']
    for i in range(n):
        a=r.uniform(0,6.283); d=r_*r.random()**0.7; s=r.uniform(3,11); hh=(1-d/r_)*r_*0.5
        px=x+d*math.cos(a); pz=z+d*math.sin(a); y=r.uniform(0,max(1,hh))
        k.append(M.cube('junk',[px-s,y,pz-s*r.uniform(0.4,1)],[px+s,y+s*r.uniform(0.4,1.3),pz+s*r.uniform(0.4,1)],r.choice(cols)))
    k.append(M.cube('junk_base',[x-r_*0.8,0,z-r_*0.6],[x+r_*0.8,r_*0.16,z+r_*0.6],'rust'))
    return k
def hatch(M,tag,x,z):
    """지상 출입구: 콘크리트 턱 + 열리는 뚜껑(묶음 tag_lid, 뒤쪽 모서리가 경첩) + 번호판 G"""
    k=[M.cube('h_rim',[x-30,0,z-30],[x+30,10,z+30],'conc'), M.cube('h_hole',[x-22,9.6,z-22],[x+22,10.4,z+22],'black'), M.cube('h_step',[x-36,0,z-40],[x+36,4,z-30],'conc_d'),
       M.cube('h_post',[x+26,10,z+26],[x+30,40,z+30],'yellow'), M.cube('h_sign',[x+14,30,z+25],[x+42,42,z+27],'dark',north='lbl0'), M.cube('h_haz',[x-30,10,z-30.6],[x+30,13,z-30],'hazard')]
    lid=M.group(tag+'lid',[x,10.4,z+24],[M.cube('h_lid',[x-24,10.4,z-24],[x+24,14,z+24],'steel'), M.cube('h_lid_h',[x-6,14,z-18],[x+6,16,z-12],'yellow')])
    return k,lid
def facility(M,x,z):
    """멀리 보이는 연구소 건물 (지상 부분) + 울타리"""
    k=[M.cube('bld',[x-220,0,z],[x+220,150,z+160],'bld'), M.cube('bld2',[x-120,150,z+20],[x+60,230,z+140],'bld_d'), M.cube('bld3',[x+240,0,z+30],[x+420,90,z+150],'bld_d'),
       M.cube('bld_roof',[x-226,150,z-6],[x+226,158,z+166],'bld_d'), M.cube('tower',[x+120,150,z+60],[x+150,300,z+90],'bld_d'), M.cube('tower_l',[x+128,300,z+68],[x+142,312,z+82],'red'),
       M.cube('dish',[x-170,158,z+60],[x-120,170,z+110],'steel')]
    for i in range(6): k.append(M.cube('win',[x-200+i*70,30,z-1.4],[x-152+i*70,94,z],'bld_d',north='win_d'))
    for i in range(3): k.append(M.cube('win2',[x-100+i*56,165,z+18.6],[x-58+i*56,215,z+20],'bld_d',north='win_d'))
    for i,fx in enumerate(range(int(x-520),int(x+520),40)):
        k.append(M.cube('fpost',[fx,0,z-120],[fx+3,34,z-117],'fence'))
    k.append(M.cube('frail',[x-520,26,z-119.4],[x+520,29,z-117.6],'fence')); k.append(M.cube('frail',[x-520,12,z-119.4],[x+520,15,z-117.6],'fence'))
    return k
