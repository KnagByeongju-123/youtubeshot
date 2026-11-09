"""《물로 움직인 900년 전 시계탑》 블록 부품: 소송의 수운의상대(3층 시계탑), 물레바퀴(물통 36개)·저울 걸쇠(탈진기)·물탱크·물줄기,
   퍼 올리는 바퀴, 하늘 사다리(사슬), 큰 톱니바퀴, 혼의(고리 관측기)·혼상(별 공), 시간 알림 오 층 탑과 인형, 종·북·징, 책"""
import os, sys, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 찹쌀기구 import *

def clock_palette(M):
    M.swatch('bronze',(170,120,60),8); M.swatch('bronze_d',(130,90,45),6); M.swatch('verdigris',(80,140,120),6)
    M.swatch('lacquer',(150,40,35),5); M.swatch('lacquer_d',(110,30,28),4); M.swatch('timber',(150,110,70),6); M.swatch('timber_d',(105,75,45),5)
    M.swatch('star',(255,240,170),3); M.swatch('night',(25,35,70),4); M.swatch('globe',(40,60,110),6); M.swatch('jack',(200,50,45),4); M.swatch('jack_face',(235,200,160),3)
    M.swatch('bell',(190,150,60),6); M.swatch('drum',(170,60,45),5); M.swatch('drumhead',(230,215,180),4); M.swatch('plaque',(240,230,200),3)
    M.swatch('water2',(80,150,220),4); M.swatch('roof_g',(60,90,80),5)

def rcube(M, name, fr, to, col, origin, rot):
    """기울인 상자: origin 을 중심으로 rot(도) 만큼 돌린 상자"""
    u=M.cube(name,fr,to,col); e=[e for e in M.els if e['uuid']==u][0]
    e['origin']=[round(v,3) for v in origin]; e['rotation']=[round(v,3) for v in rot]; return u

def ring(M, name, cx, cy, cz, r, axis='z', th=2.0, n=20, col='bronze'):
    """고리: 기울인 상자 n 개를 이어 붙인 원 (빈틈 없음).  axis = 고리 면에 수직인 축"""
    k=[]; s=2*math.pi*r/n+0.6
    for i in range(n):
        a=2*math.pi*(i+0.5)/n; u,v=r*math.cos(a),r*math.sin(a); deg=math.degrees(a)
        if axis=='z':
            k.append(rcube(M,name,[cx+u-th/2,cy+v-s/2,cz-th/2],[cx+u+th/2,cy+v+s/2,cz+th/2],col,[cx+u,cy+v,cz],[0,0,deg]))
        elif axis=='x':   # 고리 면 = y-z
            k.append(rcube(M,name,[cx-th/2,cy+v-s/2,cz+u-th/2],[cx+th/2,cy+v+s/2,cz+u+th/2],col,[cx,cy+v,cz+u],[-deg,0,0]))
        else:             # 고리 면 = x-z
            k.append(rcube(M,name,[cx+u-th/2,cy-th/2,cz+v-s/2],[cx+u+th/2,cy+th/2,cz+v+s/2],col,[cx+u,cy,cz+v],[0,-deg,0]))
    return k

def armillary(M, tag, x, y, z, r=22):
    """혼의: 받침 + 고리 셋(바깥 고정 둘, 안쪽 도는 묶음 tag+'inner')"""
    k=[M.cube('arm_base',[x-14,y,z-14],[x+14,y+6,z+14],'bronze_d'), M.cube('arm_post',[x-3,y+6,z-3],[x+3,y+r,z+3],'bronze_d'),
       M.cube('dragon',[x-6,y+6,z-6],[x+6,y+14,z+6],'verdigris')]
    k+= ring(M,'ring_m',x,y+r+8,z,r,'z',col='bronze')+ring(M,'ring_h',x,y+r+8,z,r,'y',col='bronze_d')
    inner=M.group(tag+'inner',[x,y+r+8,z],ring(M,'ring_i',x,y+r+8,z,r*0.8,'x',col='verdigris')+[M.cube('tube',[x-1,y+r+8-r*0.8,z-1],[x+1,y+r+8+r*0.8,z+1],'bronze')])
    return M.group(tag+'root',[x,y,z],k+[inner])

def globe(M, tag, x, y, z, r=18):
    """혼상: 블록으로 쌓은 둥근 공(짙은 파랑) + 별(노란 점).  묶음 중심 = 공 중심 → y 회전"""
    k=[]; rnd=random.Random(5)
    for j in range(-int(r),int(r)+1,3):
        rr=math.sqrt(max(0,r*r-j*j))
        k.append(M.cube('gl',[x-rr,y+r+j-1.5,z-rr],[x+rr,y+r+j+1.5,z+rr],'globe'))
        if rr>4:
            for s in range(3):
                a=rnd.uniform(0,6.28); k.append(M.cube('st',[x+rr*math.cos(a)-1,y+r+j-0.8,z+rr*math.sin(a)-1],[x+rr*math.cos(a)+1,y+r+j+0.8,z+rr*math.sin(a)+1],'star'))
    k.append(M.cube('gl_stand',[x-12,y-10,z-12],[x+12,y,z+12],'lacquer_d'))
    return M.group(tag,[x,y+r,z],k)

def waterwheel(M, tag, x, y, z, r=36, n=12, scoops=True, w=10):
    """물레바퀴 (바퀴 면 = x-y, 축 = z).  묶음 tag (중심 = 축) 을 z 회전.  n = 보이는 물통 수"""
    k=[M.cube('hub',[x-5,y-5,z-w/2-2],[x+5,y+5,z+w/2+2],'timber_d')]
    for i in range(n):
        a=2*math.pi*i/n; ex,ey=math.cos(a)*r,math.sin(a)*r; deg=math.degrees(a)
        # 바퀴살: 축에서 테두리까지 한 줄 (기울인 상자)
        k.append(rcube(M,'spoke',[x,y-1.5,z-1.5],[x+r-6,y+1.5,z+1.5],'timber',[x,y,z],[0,0,deg]))
        if scoops:   # 물통: 테두리 바깥, 바퀴 방향으로 기울임
            k.append(rcube(M,'scoop',[x+ex-5,y+ey-4,z-w/2],[x+ex+5,y+ey+4,z+w/2],'timber_d',[x+ex,y+ey,z],[0,0,deg]))
            k.append(rcube(M,'scoop_w',[x+ex-4,y+ey-3,z-w/2+1],[x+ex+4,y+ey+1,z+w/2-1],'water2',[x+ex,y+ey,z],[0,0,deg]))
    k+= ring(M,'rim',x,y,z,r-6,'z',th=3,n=24,col='timber')
    return M.group(tag,[x,y,z],k)

def escapement(M, tag, x, y, z):
    """저울 걸쇠(탈진기): 받침 기둥 + 지렛대(tag+'lever', 끝에 추) + 걸쇠(tag+'catch')"""
    k=[M.cube('esc_post',[x-2,y-30,z-3],[x+2,y,z+3],'timber_d')]
    lever=M.group(tag+'lever',[x,y,z],[M.cube('lever',[x-22,y-1,z-1.5],[x+22,y+1.5,z+1.5],'timber'),M.cube('weight',[x+16,y-8,z-4],[x+24,y,z+4],'iron')])
    catch=M.group(tag+'catch',[x-20,y+30,z],[M.cube('catch',[x-22,y+20,z-1.5],[x-18,y+34,z+1.5],'iron')])
    return M.group(tag+'root',[x,y,z],k+[lever,catch])

def tank(M, tag, x, y, z, w=30):
    k=[M.cube('tk',[x-w/2,y,z-w/2],[x+w/2,y+18,z+w/2],'timber_d'), M.cube('tk_w',[x-w/2+2,y+14,z-w/2+2],[x+w/2-2,y+17,z+w/2-2],'water2'),
       M.cube('spout',[x-w/2-8,y+2,z-1.5],[x-w/2,y+5,z+1.5],'bronze_d')]
    return M.group(tag,[x,y,z],k)

def stream(M, tag, x, y0, y1, z):
    return M.group(tag,[x,y1,z],[M.cube('stream',[x-0.8,y1,z-0.8],[x+0.8,y0,z+0.8],'water2')])

def gear(M, tag, x, y, z, r=30, teeth=24, axis='z'):
    k=ring(M,'gear',x,y,z,r,axis,th=4,n=teeth,col='bronze_d')
    for i in range(teeth):
        a=2*math.pi*i/teeth; u,v=(r+3)*math.cos(a),(r+3)*math.sin(a)
        if axis=='z': k.append(M.cube('tooth',[x+u-1.5,y+v-1.5,z-2],[x+u+1.5,y+v+1.5,z+2],'bronze'))
        else: k.append(M.cube('tooth',[x+u-1.5,y-2,z+v-1.5],[x+u+1.5,y+2,z+v+1.5],'bronze'))
    k.append(M.cube('g_hub',[x-4,y-4,z-4],[x+4,y+4,z+4],'bronze_d'))
    for i in range(4):
        a=math.pi*i/2
        for f in (0.35,0.7):
            u,v=r*f*math.cos(a),r*f*math.sin(a)
            k.append(M.cube('g_sp',[x+u-1.5,y+v-1.5,z-1.5],[x+u+1.5,y+v+1.5,z+1.5],'bronze_d') if axis=='z' else M.cube('g_sp',[x+u-1.5,y-1.5,z+v-1.5],[x+u+1.5,y+1.5,z+v+1.5],'bronze_d'))
    return M.group(tag,[x,y,z],k)

def chain_loop(M, tag, x, y0, y1, z, n=14):
    """하늘 사다리: 세로 고리 사슬(양쪽 줄) — 고리 묶음 tag+'links' 를 위로 한 칸씩 옮겨 도는 것처럼"""
    links=[]
    step=(y1-y0)/n
    for i in range(n+2):
        yy=y0+i*step
        links+= [M.cube('lk',[x-6,yy,z-1],[x-3,yy+step*0.7,z+1],'iron'), M.cube('lk',[x+3,yy,z-1],[x+6,yy+step*0.7,z+1],'iron')]
    lg=M.group(tag+'links',[x,y0,z],links)
    k=[M.cube('sproc_b',[x-8,y0-4,z-3],[x+8,y0+4,z+3],'bronze_d'), M.cube('sproc_t',[x-8,y1-4,z-3],[x+8,y1+4,z+3],'bronze_d')]
    return M.group(tag+'root',[x,y0,z],k+[lg]), step

def jack(M, tag, x, y, z, s=0.32):
    """시간 알림 인형 (작은 붉은 옷 사람) — 팔 묶음 tag+'arm'"""
    c=lambda n,a,b,col: M.cube(n,[x+a[0]*s,y+a[1]*s,z+a[2]*s],[x+b[0]*s,y+b[1]*s,z+b[2]*s],col)
    arm=M.group(tag+'arm',[x-6*s,y+22*s,z],[c('jarm',[-8,12,-2],[-4,24,2],'jack')])
    k=[c('jbody',[-4,0,-2.4],[4,24,2.4],'jack'), c('jhead',[-3.5,24,-3.5],[3.5,31,3.5],'jack_face'), c('jhat',[-4,30,-4],[4,33,4],'gat'), c('jarm2',[4,12,-2],[8,24,2],'jack')]
    return M.group(tag,[x,y,z],k+[arm])

def time_pagoda(M, tag, x, y, z, w=70, levels=5):
    """시간 알림 오 층 탑 (앞 = -z): 층마다 가운데 작은 문(어두운 칸).  문 안 인형 자리 좌표 목록을 돌려줌"""
    k=[]; yy=y; doors=[]
    for i in range(levels):
        ww=w*(1-i*0.08); hh=22
        k.append(M.cube('tp_body',[x-ww/2,yy,z-ww/3],[x+ww/2,yy+hh,z+ww/3],'lacquer'))
        k.append(M.cube('tp_door',[x-7,yy+3,z-ww/3-0.4],[x+7,yy+hh-3,z-ww/3+0.2],'dark'))
        doors.append((x,yy+3,z-ww/3-1))
        yy+=hh; k.append(M.cube('tp_roof',[x-ww/2-6,yy,z-ww/3-6],[x+ww/2+6,yy+4,z+ww/3+6],'roof_g')); yy+=4
    return M.group(tag,[x,y,z],k), doors, yy

def clock_tower(M, tag, x=0, z=0):
    """수운의상대: 1층 시간 알림 탑(앞) / 2층 혼상 방 / 3층 혼의 단(지붕 판 tag+'roof' 를 옮겨 열 수 있음) + 오른쪽 물레바퀴 칸(열린 단면).
       돌아오는 값: (묶음, 부품 dict)"""
    parts={}; k=[]
    W=120; D=100; H1=130; H2=60; H3=40
    # 기단
    k.append(M.cube('t_base',[x-W/2-20,0,z-D/2-20],[x+W/2+100,10,z+D/2+20],'granite_b'))
    # 1층 몸통 (나무 기둥·벽)
    for px in (-W/2,W/2-6):
        for pz in (-D/2,D/2-6): k.append(M.cube('t_pil',[x+px,10,z+pz],[x+px+6,10+H1+H2,z+pz+6],'lacquer_d'))
    k.append(M.cube('t_back',[x-W/2,10,z+D/2-4],[x+W/2,10+H1+H2,z+D/2],'timber'))
    k.append(M.cube('t_side',[x-W/2,10,z-D/2],[x-W/2+4,10+H1+H2,z+D/2],'timber'))
    k.append(M.cube('t_floor2',[x-W/2,10+H1,z-D/2],[x+W/2,14+H1,z+D/2],'timber_d'))
    k.append(M.cube('t_floor3',[x-W/2-10,10+H1+H2,z-D/2-10],[x+W/2+10,16+H1+H2,z+D/2+10],'timber_d'))
    # 1층 앞: 시간 알림 탑
    tp,doors,_=time_pagoda(M,tag+'tp',x-10,10,z-D/2+30,w=64); k.append(tp); parts['doors']=doors
    # 2층: 혼상
    gl=globe(M,tag+'globe',x,14+H1,z,r=18); k.append(gl); parts['globe']=gl
    # 3층: 혼의 + 지붕 판
    am=armillary(M,tag+'arm',x,16+H1+H2,z,r=22); k.append(am); parts['arm']=am
    roof=M.group(tag+'roof',[x,16+H1+H2+70,z],[M.cube('roof',[x-W/2-14,16+H1+H2+66,z-D/2-14],[x+W/2+14,16+H1+H2+72,z+D/2+14],'tile'),
                                               M.cube('roof2',[x-W/2,16+H1+H2+72,z-D/2],[x+W/2,16+H1+H2+78,z+D/2],'tile_d')]+
                 [M.cube('rp',[x+px,16+H1+H2,z+pz],[x+px+5,16+H1+H2+66,z+pz+5],'lacquer_d') for px in (-W/2-10,W/2+5) for pz in (-D/2-10,D/2+5)])
    k.append(roof); parts['roof']=roof
    # 오른쪽 물레바퀴 칸 (x W/2 ~ W/2+100): 뒤 벽 + 바퀴 + 탱크 + 물줄기 + 걸쇠 + 사슬
    WX=x+W/2+50; WY=10+70
    k.append(M.cube('w_back',[x+W/2,10,z+D/2-4],[x+W/2+100,10+H1+H2,z+D/2],'wall_w'))
    k.append(M.cube('w_pil',[x+W/2+94,10,z-D/2],[x+W/2+100,10+H1+H2,z-D/2+6],'lacquer_d'))
    ww=waterwheel(M,tag+'wheel',WX,WY,z,r=48,n=12); k.append(ww); parts['wheel']=ww
    tk=tank(M,tag+'tank',WX+10,WY+70,z,w=30); k.append(tk)
    st=stream(M,tag+'stream',WX-10,WY+72,WY+50,z); k.append(st); parts['stream']=st
    es=escapement(M,tag+'esc',WX-60,WY+40,z-14); k.append(es); parts['esc']=es
    ch,step=chain_loop(M,tag+'chain',x+W/2+8,WY,16+H1+H2,z+20); k.append(ch); parts['chain']=ch; parts['chain_step']=step
    k.append(M.cube('lowtank',[WX-40,10,z-30],[WX+40,22,z+30],'timber_d')); k.append(M.cube('lowtank_w',[WX-38,18,z-28],[WX+38,21,z+28],'water2'))
    return M.group(tag+'root',[x,0,z],k), parts

def noria(M, tag, x, z):
    """물을 퍼 올리는 바퀴 (손잡이로 돌림) — 바퀴 묶음 tag+'wheel'"""
    k=[M.cube('n_frame',[x-3,0,z-14],[x+3,60,z-10],'timber_d'), M.cube('n_frame',[x-3,0,z+10],[x+3,60,z+14],'timber_d')]
    wh=waterwheel(M,tag+'wheel',x,36,z,r=24,n=8,w=6)
    return M.group(tag+'root',[x,0,z],k+[wh])

def bell_drum(M, tag, x, y, z):
    k=[M.cube('bell',[x-8,y+10,z-8],[x+8,y+24,z+8],'bell'), M.cube('bell_top',[x-4,y+24,z-4],[x+4,y+28,z+4],'bronze_d'),
       M.cube('drum',[x+18,y,z-10],[x+38,y+20,z+10],'drum'), M.cube('drumhead',[x+17.5,y+2,z-8],[x+18,y+18,z+8],'drumhead'),
       M.cube('gong',[x-34,y+4,z-1],[x-18,y+20,z+1],'bronze')]
    return M.group(tag,[x,y,z],k)
