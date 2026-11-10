"""《철길 끝 증기 기차 여관》 블록 부품 (스팀펑크): 증기 기관차(둥근 보일러·굴뚝·기관실·붉은 큰 바퀴·쇠 쟁기), 여관 객차 3칸(초록 나무 벽·놋쇠 테·불 켜진 창·작은 굴뚝),
   철길, 증기 로봇 톡, 감독관의 검은 증기차, 쇠 기둥, 협곡 철교, 바닷가 등대, 증기 비행선.  앞 = 기관차가 가는 쪽 -z"""
import os, sys, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 물시계기구 import *

def steam_palette(M):
    M.swatch('loco',(45,48,55),5); M.swatch('loco_d',(30,32,38),4); M.swatch('brass2',(205,165,75),6); M.swatch('copper2',(180,100,60),6)
    M.swatch('wheel_r',(160,40,35),5); M.swatch('rail',(120,110,100),4); M.swatch('sleeper',(110,80,55),5)
    M.swatch('car_g',(55,95,75),5); M.swatch('car_gd',(40,70,55),4); M.swatch('window_lit',(250,215,120),4); M.swatch('window_dk',(40,50,60),3)
    M.swatch('sand',(225,195,140),8); M.swatch('sand_d',(205,175,120),8); M.swatch('rock_r',(170,110,80),10); M.swatch('rock_rd',(140,90,65),8)
    M.swatch('sea',lambda x,y:(50,110,170) if (x+2*y)%7 else (90,150,205),6); M.swatch('lh_w',(235,232,225),3); M.swatch('lh_r',(180,45,40),4); M.swatch('lamp',(255,230,140),3)
    M.swatch('balloon',(190,150,95),6); M.swatch('balloon_d',(150,115,70),5); M.swatch('steam2',(240,242,245),3); M.swatch('glow',(255,140,40),10)

def cyl_x(M, name, x0, x1, cy, cz, r, col, n=8):
    """x 방향 둥근 통 (기울인 판 n 개를 둘러 붙임)"""
    k=[]; s=2*math.pi*r/n+0.8
    for i in range(n):
        a=2*math.pi*(i+0.5)/n; v,u=r*math.cos(a),r*math.sin(a)
        k.append(rcube(M,name,[x0,cy+v-1.5,cz+u-s/2],[x1,cy+v+1.5,cz+u+s/2],col,[x0,cy+v,cz+u],[math.degrees(a),0,0]))
    k.append(M.cube(name+'_core',[x0+0.5,cy-r*0.8,cz-r*0.8],[x1-0.5,cy+r*0.8,cz+r*0.8],col))
    return k

def cyl_z(M, name, z0, z1, cx, cy, r, col, n=8):
    """z 방향 둥근 통"""
    k=[]; s=2*math.pi*r/n+0.8
    for i in range(n):
        a=2*math.pi*(i+0.5)/n; u,v=r*math.cos(a),r*math.sin(a)
        k.append(rcube(M,name,[cx+u-1.5,cy+v-s/2,z0],[cx+u+1.5,cy+v+s/2,z1],col,[cx+u,cy+v,z0],[0,0,math.degrees(a)]))
    k.append(M.cube(name+'_core',[cx-r*0.8,cy-r*0.8,z0+0.5],[cx+r*0.8,cy+r*0.8,z1-0.5],col))
    return k

def driving_wheel(M, tag, cx, cy, cz, r=11, side=1):
    """붉은 큰 바퀴 (바퀴 면 = y-z, 축 = x) + 바퀴살.  묶음 중심 = 축 → x 회전"""
    k=ring(M,'w_rim',cx,cy,cz,r,'x',th=2.5,n=16,col='wheel_r')
    for i in range(8):
        a=math.pi*i/4
        k.append(rcube(M,'w_sp',[cx-0.8,cy-0.8,cz],[cx+0.8,cy+0.8,cz+r-1],'wheel_r',[cx,cy,cz],[-math.degrees(a),0,0]))
    k.append(M.cube('w_hub',[cx-1.5,cy-2.5,cz-2.5],[cx+1.5,cy+2.5,cz+2.5],'brass2'))
    return M.group(tag,[cx,cy,cz],k)

def locomotive(M, tag, x=0, z=0):
    """증기 기관차 (앞 = -z).  길이 약 110, 높이 약 70.  묶음: tag+'root', 바퀴 tag+'w0..5', 연기 자리 tag+'stack'"""
    k=[]; W=26
    k.append(M.cube('frame',[x-W/2,10,z-55],[x+W/2,16,z+55],'loco_d'))
    k+= cyl_z(M,'boiler',z-50,z+15,x,32,14,'loco',n=10)
    for zz in (z-40,z-20,z):
        k+= [rcube(M,'band',[x-15,31,zz],[x+15,33,zz+2],'brass2',[x,32,zz],[0,0,0])]
    k+= [M.cube('smokebox',[x-15,16,z-56],[x+15,48,z-48],'loco_d'), M.cube('lamp',[x-4,40,z-58],[x+4,46,z-56],'lamp')]
    k+= [M.cube('stack',[x-5,46,z-50],[x+5,66,z-40],'loco_d'), M.cube('stack_top',[x-7,66,z-52],[x+7,70,z-38],'brass2')]
    k+= [M.cube('dome',[x-6,46,z-15],[x+6,54,z-5],'brass2'), M.cube('whistle',[x-1.5,46,z+5],[x+1.5,56,z+8],'brass2')]
    k+= [M.cube('cab',[x-W/2-2,16,z+15],[x+W/2+2,62,z+50],'car_gd'), M.cube('cab_roof',[x-W/2-5,62,z+12],[x+W/2+5,66,z+53],'loco_d'),
         M.cube('cab_win',[x-W/2-2.4,40,z+20],[x-W/2-1.8,54,z+34],'window_lit'), M.cube('cab_win2',[x+W/2+1.8,40,z+20],[x+W/2+2.4,54,z+34],'window_lit'),
         M.cube('cab_door',[x-W/2-2.3,18,z+38],[x-W/2-1.9,40,z+48],'loco_d')]
    # 쇠 쟁기(앞)
    for j in range(5):
        k.append(M.cube('plow',[x-W/2+j*3,0+j*2,z-62+j*2],[x+W/2-j*3,4+j*2,z-56+j*2],'loco_d'))
    k.append(M.cube('plow_top',[x-W/2,10,z-60],[x+W/2,14,z-55],'brass2'))
    wheels=[]
    for i,zz in enumerate((z-35,z-10,z+15)):
        for sx in (-1,1):
            wg=driving_wheel(M,tag+f'w{i}{"L" if sx<0 else "R"}',x+sx*(W/2+1.5),11,zz,r=11); wheels.append(wg)
    k.append(M.cube('rod_L',[x-W/2-4,10,z-36],[x-W/2-3,12,z+16],'brass2')); k.append(M.cube('rod_R',[x+W/2+3,10,z-36],[x+W/2+4,12,z+16],'brass2'))
    k.append(M.cube('cylinder_L',[x-W/2-6,10,z-50],[x-W/2,18,z-38],'loco')); k.append(M.cube('cylinder_R',[x+W/2,10,z-50],[x+W/2+6,18,z-38],'loco'))
    fire=M.group(tag+'fire',[x,20,z+30],[M.cube('fire',[x-6,18,z+28],[x+6,26,z+32],'glow')]); k.append(fire)
    stackp=anchor(M,tag+'stack',[x,72,z-45])
    return M.group(tag+'root',[x,0,z],k+wheels+[stackp])

def inn_car(M, tag, x=0, z=0, L=90, lit=True, chimney=True):
    """여관 객차 (초록 나무 벽 + 놋쇠 테 + 창 + 지붕 + 작은 굴뚝).  중심 z, 길이 L (z 방향)"""
    W=30; k=[M.cube('c_frame',[x-W/2,10,z-L/2],[x+W/2,14,z+L/2],'loco_d'),
             M.cube('c_body',[x-W/2,14,z-L/2],[x+W/2,52,z+L/2],'car_g'), M.cube('c_trim',[x-W/2-0.5,30,z-L/2],[x+W/2+0.5,32,z+L/2],'brass2'),
             M.cube('c_roof',[x-W/2-3,52,z-L/2-2],[x+W/2+3,56,z+L/2+2],'loco_d'), M.cube('c_roof2',[x-W/2+3,56,z-L/2+2],[x+W/2-3,59,z+L/2-2],'car_gd')]
    n=int(L//22)
    for i in range(n):
        zz=z-L/2+11+i*22
        for sx in (-1,1):
            k.append(M.cube('c_win',[x+sx*(W/2)-0.6 if sx>0 else x-W/2-0.6,34,zz-6],[x+sx*(W/2)+0.6 if sx>0 else x-W/2+0.6,46,zz+6],'window_lit' if lit else 'window_dk'))
    if chimney: k+= [M.cube('c_chim',[x+6,56,z-L/4],[x+12,70,z-L/4+6],'copper2'), M.cube('c_chim_t',[x+5,70,z-L/4-1],[x+13,72,z-L/4+7],'brass2')]
    k+= [M.cube('c_door',[x-W/2-0.6,14,z+L/2-14],[x-W/2+0.2,44,z+L/2-4],'car_gd'), M.cube('c_step',[x-W/2-6,6,z+L/2-14],[x-W/2,9,z+L/2-4],'loco_d')]
    for zz in (z-L/2+12,z+L/2-12):
        for sx in (-1,1): k.append(M.cube('c_wheel',[x+sx*(W/2+0.5)-1.5,4,zz-6],[x+sx*(W/2+0.5)+1.5,16,zz+6],'loco_d'))
    return M.group(tag,[x,0,z],k)

def inn_train(M, tag, x=0, z=0):
    """기관차 + 객차 3칸 (뒤로 +z).  돌아오는 값: (묶음, 기관차 묶음)"""
    lo=locomotive(M,tag+'loco_',x,z)
    cars=[inn_car(M,tag+f'car{i}',x,z+110+i*96) for i in range(3)]
    return M.group(tag+'root',[x,0,z],[lo]+cars), lo

def track(M, tag, x, z0, z1, gauge=26):
    k=[M.cube('rail',[x-gauge/2-1.5,0,z0],[x-gauge/2+1.5,3,z1],'rail'), M.cube('rail',[x+gauge/2-1.5,0,z0],[x+gauge/2+1.5,3,z1],'rail')]
    zz=z0
    while zz<z1: k.append(M.cube('sleeper',[x-gauge/2-8,-1,zz],[x+gauge/2+8,1,zz+6],'sleeper')); zz+=16
    return M.group(tag,[x,0,(z0+z1)/2],k)

def tok(M, tag, x, y, z, s=1.0):
    """증기 로봇 톡: 주전자 같은 놋쇠 몸통 + 둥근 렌즈 눈 + 작은 굴뚝 + 팔다리.  묶음: tag+'root', 팔 tag+'arm_l/r', 다리 tag+'leg_l/r'"""
    c=lambda n,a,b,col: M.cube(n,[x+a[0]*s,y+a[1]*s,z+a[2]*s],[x+b[0]*s,y+b[1]*s,z+b[2]*s],col)
    body=[c('t_body',[-5,5,-4],[5,14,4],'brass2'), c('t_belly',[-5.5,7,-4.5],[5.5,11,4.5],'copper2'), c('t_head',[-4,14,-3.5],[4,19,3.5],'brass2'),
          c('t_eye',[-2,15.5,-4],[2,18,-3.4],'lens'), c('t_pupil',[-0.8,16.2,-4.2],[0.8,17.4,-3.9],'dark'),
          c('t_chim',[1.5,19,-1],[3.5,23,1],'copper2'), c('t_spout',[-8,9,-1],[-5,11,1],'brass2'), c('t_handle',[5,8,-1],[7,13,1],'copper2')]
    al=M.group(tag+'arm_l',[x+5.5*s,12*s+y,z],[c('t_al',[5,6,-1],[6.5,12,1],'copper2')])
    ar=M.group(tag+'arm_r',[x-5.5*s,12*s+y,z],[c('t_ar',[-6.5,6,-1],[-5,12,1],'copper2')])
    ll=M.group(tag+'leg_l',[x+2.5*s,5*s+y,z],[c('t_ll',[1.5,0,-1.5],[3.5,5,1.5],'loco_d')])
    lr=M.group(tag+'leg_r',[x-2.5*s,5*s+y,z],[c('t_lr',[-3.5,0,-1.5],[-1.5,5,1.5],'loco_d')])
    puff=M.group(tag+'puff',[x+2.5*s,y+25*s,z],[c('t_puff',[1,24,-2],[4,27,1],'steam2'),c('t_puff2',[0,27,-1.5],[3,30,1.5],'steam2')])
    return M.group(tag+'root',[x,y,z],body+[al,ar,ll,lr,puff])

def steam_car(M, tag, x, z):
    """감독관의 검은 증기차 (앞 = -z)"""
    k=[M.cube('sc_body',[x-14,8,z-26],[x+14,24,z+26],'coat_blk'), M.cube('sc_cab',[x-12,24,z-2],[x+12,40,z+22],'coat_blk'),
       M.cube('sc_win',[x-12.4,28,z+2],[x-11.8,36,z+18],'window_dk'), M.cube('sc_boiler',[x-6,24,z-24],[x+6,34,z-6],'brass2'),
       M.cube('sc_stack',[x-2,34,z-20],[x+2,46,z-16],'loco_d')]
    for zz in (z-18,z+18):
        for sx in (-1,1): k.append(M.cube('sc_wh',[x+sx*15-2,0,zz-7],[x+sx*15+2,14,zz+7],'loco_d'))
    return M.group(tag,[x,0,z],k)

def iron_post(M, tag, x, z):
    return M.group(tag,[x,0,z],[M.cube('post',[x-3,0,z-3],[x+3,40,z+3],'loco_d'),M.cube('post_cap',[x-5,40,z-5],[x+5,44,z+5],'rail')])

def trestle(M, tag, x, z0, z1, H=120):
    """협곡 위 나무 철교 (z 방향): 다리 기둥 X 자 + 위 철길"""
    k=[M.cube('deck',[x-22,H-6,z0],[x+22,H,z1],'sleeper')]
    zz=z0
    while zz<=z1:
        for sx in (-1,1): k.append(M.cube('tpost',[x+sx*18-2,0,zz-2],[x+sx*18+2,H-6,zz+2],'timber_d'))
        k.append(rcube(M,'xbr',[x-20,H/2-1.5,zz-1],[x+20,H/2+1.5,zz+1],'timber',[x,H/2,zz],[0,0,35]))
        k.append(rcube(M,'xbr',[x-20,H/2-1.5,zz-1],[x+20,H/2+1.5,zz+1],'timber',[x,H/2,zz],[0,0,-35]))
        zz+=40
    return M.group(tag,[x,0,(z0+z1)/2],k)

def lighthouse(M, tag, x, z, H=170):
    k=[]
    for j in range(6):
        r=22-j*2; y0=j*H/7
        k.append(M.cube('lh',[x-r,y0,z-r],[x+r,y0+H/7,z+r],'lh_w' if j%2==0 else 'lh_r'))
    y=6*H/7
    k+= [M.cube('lh_deck',[x-16,y,z-16],[x+16,y+4,z+16],'loco_d'), M.cube('lh_room',[x-10,y+4,z-10],[x+10,y+22,z+10],'window_dk'), M.cube('lh_roof',[x-13,y+22,z-13],[x+13,y+28,z+13],'lh_r')]
    lamp=M.group(tag+'lamp',[x,y+12,z],[M.cube('lh_lamp',[x-10.6,y+5,z-10.6],[x+10.6,y+21,z+10.6],'lamp')])
    return M.group(tag,[x,0,z],k+[lamp])

def airship(M, tag, x, y, z, L=160):
    """증기 비행선: 긴 기구(풍선) + 아래 배 + 프로펠러.  묶음 중심 = 가운데"""
    k=[]; N=11
    for j in range(N):
        f=math.sin(math.pi*(j+0.5)/N)**0.7; r=24*f+3; zz=z-L/2+j*L/N; col='balloon' if j%2 else 'balloon_d'
        k.append(M.cube('env',[x-r,y-r*0.55,zz],[x+r,y+r*0.55,zz+L/N+0.5],col))     # 넓고 납작
        k.append(M.cube('env',[x-r*0.55,y-r,zz],[x+r*0.55,y+r,zz+L/N+0.5],col))     # 좁고 높게 → 둥글게
        k.append(M.cube('env',[x-r*0.85,y-r*0.85,zz],[x+r*0.85,y+r*0.85,zz+L/N+0.5],col))
        if j in (2,5,8): k.append(M.cube('band',[x-r*0.86-0.3,y-r*0.86-0.3,zz+L/N/2-1],[x+r*0.86+0.3,y+r*0.86+0.3,zz+L/N/2+1],'brass2'))
    k+= [M.cube('gondola',[x-10,y-40,z-24],[x+10,y-28,z+24],'timber_d'), M.cube('g_rail',[x-11,y-28,z-25],[x+11,y-26,z+25],'brass2'), M.cube('g_win',[x-10.4,y-37,z-18],[x-9.8,y-31,z+18],'window_lit'),
         M.cube('strut',[x-1,y-26,z-20],[x+1,y-18,z-18],'rail'), M.cube('strut',[x-1,y-26,z+18],[x+1,y-18,z+20],'rail'),
         M.cube('fin',[x-1,y-10,z+L/2-8],[x+1,y+22,z+L/2+8],'copper2'), M.cube('fin2',[x-22,y-1,z+L/2-8],[x+22,y+1,z+L/2+8],'copper2')]
    prop=M.group(tag+'prop',[x,y-33,z+27],[M.cube('pb',[x-10,y-34,z+26],[x+10,y-32,z+28],'brass2'),M.cube('pb2',[x-1,y-43,z+26],[x+1,y-23,z+28],'brass2')])
    return M.group(tag,[x,y,z],k+[prop])

def desert(M, x0,x1,z0,z1,tile=64):
    return [M.cube('d',[x,-16,z],[x+tile,0,z+tile],'sand' if (x//tile+z//tile)%2 else 'sand_d') for x in range(x0,x1,tile) for z in range(z0,z1,tile)]

def mesa(M, tag, x, z, w=200, h=140, d=160):
    k=[]
    for j in range(4):
        f=1-j*0.12; k.append(M.cube('mesa',[x-w*f/2,j*h/4,z-d*f/2],[x+w*f/2,(j+1)*h/4,z+d*f/2],'rock_r' if j%2 else 'rock_rd'))
    return M.group(tag,[x,0,z],k)

def walker_leg(M, tag, hx, hy, hz, side):
    """쇠다리 하나: 엉덩이 관절(tag) → 허벅지 + 피스톤 → 무릎 관절(tag+'_knee') → 정강이 + 발.  x 회전으로 걸음"""
    o=side*4
    kz=hz; ky=hy-26
    shin=[M.cube('shin',[hx-2.5,ky-24,kz-2.5],[hx+2.5,ky,kz+2.5],'loco'), M.cube('shin_pl',[hx-3,ky-20,kz-3],[hx+3,ky-16,kz+3],'brass2'),
          M.cube('foot',[hx-6,ky-28,kz-8],[hx+6,ky-24,kz+7],'loco_d'), M.cube('toe',[hx-5,ky-28,kz-11],[hx+5,ky-25,kz-8],'loco_d'),
          M.cube('heel',[hx-1.5,ky-28,kz+7],[hx+1.5,ky-25,kz+10],'loco_d'),
          M.cube('spring',[hx+o*0.6-1,ky-14,kz+2.5],[hx+o*0.6+1,ky-4,kz+4.5],'copper2')]
    knee=M.group(tag+'_knee',[hx,ky,kz],shin+[M.cube('knee_j',[hx-3.5,ky-3.5,kz-3.5],[hx+3.5,ky+3.5,kz+3.5],'brass2')])
    thigh=[M.cube('thigh',[hx-3,ky,hz-3],[hx+3,hy,hz+3],'loco'), M.cube('hip_j',[hx-4.5,hy-4.5,hz-4.5],[hx+4.5,hy+4.5,hz+4.5],'brass2'),
           M.cube('piston',[hx+o-1.2,ky+4,hz-5],[hx+o+1.2,hy-2,hz-3],'brass2'), M.cube('pist_cyl',[hx+o-2,hy-14,hz-6],[hx+o+2,hy-2,hz-2],'copper2'),
           M.cube('hose',[hx-1,hy-10,hz+3],[hx+1,hy,hz+5],'rail')]
    return M.group(tag,[hx,hy,hz],thigh+[knee])

def walking_car(M, tag, x, z):
    """감독관의 걷는 증기차 (앞 = -z): 검은 기관실 + 놋쇠 보일러 통 + 굴뚝 둘 + 관·계기·톱니 + 쇠다리 넷.
       묶음: tag+'root'(몸통+다리), tag+'body'(몸통, 위아래 흔들림), 다리 tag+'leg0..3'(0 왼앞,1 오른앞,2 왼뒤,3 오른뒤)+'_knee', 톱니 tag+'gear', 연기 자리 tag+'stack'"""
    by=52   # 몸통 바닥 높이
    b=[M.cube('wc_belly',[x-16,by,z-28],[x+16,by+8,z+28],'loco_d'),
       M.cube('wc_cab',[x-15,by+8,z-6],[x+15,by+34,z+26],'coat_blk'), M.cube('wc_roof',[x-17,by+34,z-8],[x+17,by+37,z+28],'loco_d'),
       M.cube('wc_roof_t',[x-12,by+37,z-4],[x+12,by+39,z+24],'brass2'),
       M.cube('wc_win_f',[x-11,by+20,z-6.6],[x+11,by+30,z-6],'window_lit'),
       M.cube('wc_win_l',[x-15.6,by+20,z],[x-15,by+30,z+20],'window_lit'), M.cube('wc_win_r',[x+15,by+20,z],[x+15.6,by+30,z+20],'window_lit'),
       M.cube('wc_door',[x-15.5,by+8,z+20],[x-15,by+28,z+25],'loco_d'), M.cube('wc_ladder',[x-17,by-10,z+21],[x-16,by+8,z+24],'brass2'),
       M.cube('wc_rivets',[x-15.3,by+12,z-6],[x+15.3,by+13,z+26],'brass2'),
       M.cube('wc_lamp',[x-4,by+3,z-31],[x+4,by+9,z-28],'lamp')]
    b+= cyl_z(M,'wc_boiler',z-30,z-6,x,by+20,11,'brass2',n=10)
    b+= [M.cube('wc_bband',[x-12,by+8,z-24],[x+12,by+32,z-22],'copper2'), M.cube('wc_bband',[x-12,by+8,z-14],[x+12,by+32,z-12],'copper2'),
         M.cube('wc_stack1',[x-9,by+30,z-22],[x-3,by+52,z-16],'loco_d'), M.cube('wc_stack1t',[x-10,by+52,z-23],[x-2,by+55,z-15],'brass2'),
         M.cube('wc_stack2',[x+4,by+30,z-14],[x+8,by+44,z-10],'loco_d'), M.cube('wc_stack2t',[x+3,by+44,z-15],[x+9,by+46,z-9],'brass2'),
         M.cube('wc_whistle',[x+10,by+32,z-26],[x+12,by+40,z-24],'brass2')]
    # 관(파이프): 보일러 → 기관실 → 다리 쪽
    for sx in (-1,1):
        b+= [M.cube('wc_pipe',[x+sx*13-1,by+14,z-26],[x+sx*13+1,by+16,z+24],'copper2'),
             M.cube('wc_pipe2',[x+sx*12-1,by-2,z-24],[x+sx*12+1,by+14,z-22],'copper2'), M.cube('wc_pipe2',[x+sx*12-1,by-2,z+20],[x+sx*12+1,by+14,z+22],'copper2'),
             M.cube('wc_gauge',[x+sx*15.2-0.3 if sx>0 else x-15.8,by+12,z+4],[x+sx*15.2+0.3+0.3 if sx>0 else x-15.2,by+17,z+9],'plaque')]
    b+= [M.cube('wc_tank',[x-10,by+8,z+26],[x+10,by+26,z+32],'copper2'), M.cube('wc_tank_v',[x-2,by+26,z+28],[x+2,by+30,z+30],'brass2')]
    # 옆 큰 톱니 (오른쪽, 축 x)
    gk=ring(M,'wc_gear',x+16.5,by+22,z+12,7,'x',th=2,n=12,col='brass2')
    for i in range(12):
        a=2*math.pi*i/12; gk.append(rcube(M,'wc_tooth',[x+15.5,by+22-1,z+12+7],[x+17.5,by+22+1,z+12+9.5],'brass2',[x+16.5,by+22,z+12],[-math.degrees(a),0,0]))
    gk.append(M.cube('wc_ghub',[x+15.5,by+20,z+10],[x+18,by+24,z+14],'copper2'))
    gear=M.group(tag+'gear',[x+16.5,by+22,z+12],gk)
    stack=anchor(M,tag+'stack',[x-6,by+57,z-19])
    body=M.group(tag+'body',[x,by,z],b+[gear,stack])
    legs=[walker_leg(M,tag+f'leg{i}',x+sx*14,by+2,z+sz*20,sx) for i,(sx,sz) in enumerate([(-1,-1),(1,-1),(-1,1),(1,1)])]
    return M.group(tag+'root',[x,0,z],[body]+legs)
