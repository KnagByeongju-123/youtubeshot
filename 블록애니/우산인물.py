"""《할아버지의 우산》 블록 부품: 할아버지(젊을 때·늙었을 때)·꼬마 손녀·어른 손녀·파란 우산(펼친·접은)·노란 버스·정류장.
   블록인물.py 의 Model·move·Anim·find 를 씀.  앞 = -z.  어른 키 32, 꼬마 약 22 (s=0.68)
   면 겹침 막기(블록애니.md): 소매는 몸통 옆에서 시작, 옆머리는 뒷머리보다 바깥, 얼굴 위에 붙는 판은 깊이를 다르게"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 블록인물 import Model, move, anchor, Anim, find, U

SKIN=(240,202,170); SKIN_OLD=(232,192,160)
def palette(M):
    M.swatch('skin',SKIN,3); M.swatch('skin_o',SKIN_OLD,3)
    M.swatch('hair_g',(150,150,150),5); M.swatch('hair_w',(235,233,228),4); M.swatch('hair_b',(70,45,30),4); M.swatch('hair_k',(35,28,26),3)
    M.swatch('shirt',(235,225,200),4); M.swatch('shirt_wet',(185,175,150),4)
    M.swatch('vest',(125,85,55),5); M.swatch('pants_bg',(190,170,135),5); M.swatch('shoe',(80,55,40),4)
    M.swatch('rain_p',(245,140,175),5); M.swatch('rain_pd',(215,110,145),4); M.swatch('boot_y',(250,205,45),4); M.swatch('leg_w',(240,240,240),3)
    M.swatch('coat',(45,60,100),5); M.swatch('coat_wet',(28,38,66),4); M.swatch('scarf',(245,140,175),5); M.swatch('boot_k',(45,40,40),3); M.swatch('tights',(60,55,60),3)
    M.swatch('umb',(55,120,215),5); M.swatch('umb_d',(40,90,170),4); M.swatch('umb_old',(80,125,190),8); M.swatch('wood',(130,85,50),5); M.swatch('metal',(170,170,175),3)
    M.swatch('bus',(250,200,40),5); M.swatch('bus_d',(215,165,30),4); M.swatch('glass',(170,210,230),3); M.swatch('tire',(35,35,38),3); M.swatch('stripe',(30,30,30),3)
    M.swatch('sign',(40,110,200),3); M.swatch('sign_w',(250,250,250),2); M.swatch('pole',(120,120,125),3); M.swatch('bench',(150,100,60),5)
    def face(name, skin, brow, mustache=None, cheek=False, wrinkle=False, lash=False):
        def fn(d,x,y):
            d.rectangle([x,y,x+15,y+15],fill=skin)
            for ex in (3,9):
                d.rectangle([x+ex,y+6,x+ex+3,y+9],fill=(255,255,255)); d.rectangle([x+ex+1,y+6,x+ex+2,y+9],fill=(30,25,25))
                d.rectangle([x+ex,y+5,x+ex+3,y+5],fill=brow)
                if lash: d.point((x+ex+3,y+6),fill=(30,25,25))
            d.rectangle([x+7,y+10,x+8,y+10],fill=(205,155,125))
            if mustache: d.rectangle([x+5,y+11,x+10,y+12],fill=mustache); d.rectangle([x+6,y+13,x+9,y+13],fill=(165,85,75))
            else: d.rectangle([x+6,y+12,x+9,y+12],fill=(185,90,85))
            if cheek: d.rectangle([x+2,y+10,x+3,y+11],fill=(250,150,150)); d.rectangle([x+12,y+10,x+13,y+11],fill=(250,150,150))
            if wrinkle: d.line([x+2,y+4,x+4,y+4],fill=(200,160,130)); d.line([x+11,y+4,x+13,y+4],fill=(200,160,130))
        M.paint(name,fn)
    face('f_gp',SKIN,(110,110,110),mustache=(150,150,150))
    face('f_gpo',SKIN_OLD,(230,230,225),mustache=(235,233,228),wrinkle=True)
    face('f_girl',SKIN,(70,45,30),cheek=True,lash=True)
    face('f_woman',SKIN,(70,45,30),cheek=True,lash=True)

def person(M, tag, kind='grandpa', s=1.0):
    """kind: grandpa(할아버지) / grandpa_old(늙은 할아버지, 지팡이) / girl(꼬마 손녀) / woman(어른 손녀).
       묶음: body·head·arm_left(+x)·arm_right(-x)·leg_*·hand_l·hand_r, 어깨 젖은 자국 wet_l / wet_r (크기 0/1)"""
    c=lambda name,fr,to,col,**f: M.cube(name,[v*s for v in fr],[v*s for v in to],col,**f)
    O=lambda v:[x*s for x in v]
    if kind in ('grandpa','grandpa_old'):
        top,sleeve,wet,pt,sh,fc=('vest','shirt','shirt_wet','pants_bg','shoe','f_gp' if kind=='grandpa' else 'f_gpo')
        hair='hair_g' if kind=='grandpa' else 'hair_w'; skin='skin' if kind=='grandpa' else 'skin_o'
    elif kind=='girl': top,sleeve,wet,pt,sh,fc,hair,skin='rain_p','rain_p','rain_pd','leg_w','boot_y','f_girl','hair_b','skin'
    else: top,sleeve,wet,pt,sh,fc,hair,skin='coat','coat','coat_wet','tights','boot_k','f_woman','hair_b','skin'
    boot_h=4 if kind in ('girl','woman') else 1.6
    legL=M.group(tag+'leg_left',O([2,12,0]),[c('leg',[0,boot_h,-2],[4,12,2],pt), c('shoe',[0.02,0,-2.8],[4.2,boot_h,2.2],sh)])
    legR=M.group(tag+'leg_right',O([-2,12,0]),[c('leg',[-4,boot_h,-2],[0,12,2],pt), c('shoe',[-4.2,0,-2.8],[-0.02,boot_h,2.2],sh)])
    def arm(side):
        x0,x1=(4.2,8.2) if side>0 else (-8.2,-4.2); hx0,hx1=(4.7,7.7) if side>0 else (-7.7,-4.7)
        k=[c('sleeve',[x0,15,-2.2],[x1,24,2.2],sleeve), c('hand',[hx0,12,-1.6],[hx1,15,1.6],skin)]
        wg=M.group(tag+('wet_l' if side>0 else 'wet_r'),O([6.2*side,24,0]),[c('wet',[x0-0.06,19,-2.27],[x1+0.06,24.08,2.27],wet)])
        hg=M.group(tag+('hand_l' if side>0 else 'hand_r'),O([6.2*side,12.5,0]),[])
        return M.group(tag+('arm_left' if side>0 else 'arm_right'),O([6.2*side,22,0]),k+[wg,hg])
    armL,armR=arm(1),arm(-1)
    body=[c('torso',[-4.2,12,-2.2],[4.2,24,2.2],top)]
    if kind in ('grandpa','grandpa_old'):
        body+= [c('shirt_v',[-1.4,17,-2.35],[1.4,24,-2.25],'shirt'), c('belt',[-4.3,12.05,-2.3],[4.3,13.2,2.3],'shoe'),
                c('pocket',[1.8,15,-2.38],[3.6,16.6,-2.25],'shoe')]
    if kind=='girl':
        body+= [c('coat_low',[-4.5,8,-2.5],[4.5,13,2.5],top), c('hood',[-3.6,20,2.25],[3.6,24.5,3.9],'rain_pd'),
                c('btn1',[-0.6,19,-2.38],[0.6,20.2,-2.25],'boot_y'), c('btn2',[-0.6,15,-2.38],[0.6,16.2,-2.25],'boot_y'), c('btn3',[-0.6,10.5,-2.68],[0.6,11.7,-2.55],'boot_y')]
    if kind=='woman':
        body+= [c('coat_low',[-4.5,6,-2.5],[4.5,13,2.5],top), c('scarf',[-4.4,22,-2.6],[4.4,24.3,2.6],'scarf'), c('scarf_tail',[1,16,-2.85],[3,22,-2.55],'scarf'),
                c('cbtn1',[-0.6,18,-2.38],[0.6,19.2,-2.25],'stripe'), c('cbtn2',[-0.6,14,-2.38],[0.6,15.2,-2.25],'stripe')]
    hk=[c('head',[-4,24,-4],[4,32,4],skin,north=fc,up=hair,south=hair),
        c('hair_back',[-4.2,25.5,1.2],[4.2,32.2,4.2],hair), c('hair_top',[-4.25,31.2,-4.25],[4.25,32.4,4.25],hair),
        c('hair_side_l',[3.95,28,-1],[4.3,32,3.9],hair), c('hair_side_r',[-4.3,28,-1],[-3.95,32,3.9],hair)]
    if kind=='girl':   # 양갈래 머리
        hk+= [c('tail_l',[4.3,23,0.5],[6,28,2.5],hair), c('tail_r',[-6,23,0.5],[-4.3,28,2.5],hair),
              c('tie_l',[4.3,27.2,0.4],[5.2,28.2,2.6],'boot_y'), c('tie_r',[-5.2,27.2,0.4],[-4.3,28.2,2.6],'boot_y')]
    if kind=='woman':  # 긴 머리 한 갈래로 묶음
        hk+= [c('ponytail',[-1.5,18,4.2],[1.5,29,6],hair), c('ptie',[-1.7,27.5,4.1],[1.7,28.6,6.1],'scarf')]
    if kind=='grandpa_old':   # 지팡이 (오른손)
        armR['children'].append(M.group(tag+'cane',O([-6.2,12.5,0]),[c('cane',[-6.8,-9,-3.4],[-5.6,13,-2.2],'wood'), c('cane_h',[-6.8,12,-3.4],[-5.6,13.2,0],'wood')]))
    head=M.group(tag+'head',O([0,24,0]),hk)
    bod=M.group(tag+'body',O([0,12,0]),body+[head,armL,armR])
    return M.group(tag+'root',[0,0,0],[bod,legL,legR])

def umbrella(M, tag, old=False, s=1.0):
    """펼친 파란 우산. 손잡이(잡는 곳) = 묶음 중심(0,0,0), 대가 위로 22, 우산 지름 30 (두 사람이 함께 쓸 크기)"""
    c=lambda n,fr,to,col: M.cube(n,[v*s for v in fr],[v*s for v in to],col)
    col='umb_old' if old else 'umb'
    k=[c('u_handle',[-0.6,-1,-0.6],[0.6,3,0.6],'wood'), c('u_hook',[-0.55,-1.6,-2.4],[0.55,-0.6,0.55],'wood'),
       c('u_pole',[-0.4,3,-0.4],[0.4,24,0.4],'metal')]
    for i,(w,h) in enumerate([(30,1.2),(24,1.6),(16,1.6),(8,1.4)]):
        y=20+i*1.3
        k.append(c('u_can',[-w/2,y,-w/2],[w/2,y+h,w/2],col if i%2==0 else ('umb_d' if not old else col)))
    k+= [c('u_tip',[-0.5,25.5,-0.5],[0.5,27,0.5],'metal')]
    for dx,dz in ((1,1),(1,-1),(-1,1),(-1,-1)):   # 우산살 끝
        k.append(c('u_rib',[dx*14.5-0.5,19.6,dz*14.5-0.5],[dx*14.5+0.5,20.1,dz*14.5+0.5],'metal'))
    return M.group(tag+'root',[0,0,0],k)

def umbrella_closed(M, tag):
    """접은 파란 우산 (세워 둔 것). 바닥 끝 = (0,0,0), 길이 30"""
    k=[M.cube('cu_tip',[-0.4,0,-0.4],[0.4,2,0.4],'metal'), M.cube('cu_body',[-1.6,2,-1.6],[1.6,18,1.6],'umb'),
       M.cube('cu_band',[-1.7,12,-1.7],[1.7,13,1.7],'umb_d'), M.cube('cu_pole',[-0.4,18,-0.4],[0.4,26,0.4],'metal'),
       M.cube('cu_handle',[-0.7,26,-0.7],[0.7,29,0.7],'wood'), M.cube('cu_hook',[-0.7,29,-3],[0.7,30,0.7],'wood')]
    return M.group(tag+'root',[0,0,0],k)

def bus(M, tag):
    """노란 작은 버스 (앞 = -z, 길이 70, 높이 34). 옆 창문은 판 깊이를 다르게"""
    k=[M.cube('bus_body',[-13,5,-35],[13,32,35],'bus'), M.cube('bus_roof',[-13.4,32,-34],[13.4,34,34],'bus_d'),
       M.cube('bus_stripe_l',[13,13,-35],[13.3,15,35],'stripe'), M.cube('bus_stripe_r',[-13.3,13,-35],[-13,15,35],'stripe'),
       M.cube('bus_wind',[-11,18,-35.3],[11,29,-35],'glass'), M.cube('bus_bumper',[-13.5,5,-36.4],[13.5,8,-35],'tire'),
       M.cube('bus_light_l',[8,10,-35.4],[11,13,-35],'sign_w'), M.cube('bus_light_r',[-11,10,-35.4],[-8,13,-35],'sign_w'),
       M.cube('bus_door',[13,5,-30],[13.35,28,-20],'glass')]
    for z in range(-15,32,12):
        k+= [M.cube('bus_win_l',[13,18,z],[13.35,27,z+9],'glass'), M.cube('bus_win_r',[-13.35,18,z],[-13,27,z+9],'glass')]
    for z in (-24,22):
        k+= [M.cube('bus_tire_l',[12.6,0,z-5],[15.6,10,z+5],'tire'), M.cube('bus_tire_r',[-15.6,0,z-5],[-12.6,10,z+5],'tire')]
    return M.group(tag+'root',[0,0,0],k)

def bus_stop(M, tag):
    """정류장: 둥근 표지판 기둥 + 나무 벤치 (지붕 없음 — 비를 맞는 곳)"""
    k=[M.cube('bs_pole',[-0.8,0,-0.8],[0.8,44,0.8],'pole'), M.cube('bs_sign',[-6,38,-0.6],[6,50,0.6],'sign'),
       M.cube('bs_mark',[-3,41,-0.85],[3,47,-0.6],'sign_w'), M.cube('bs_mark2',[-3,41,0.6],[3,47,0.85],'sign_w'),
       M.cube('bs_seat',[4,6,-3],[26,7,3],'bench'), M.cube('bs_back',[4,7,2],[26,13,3],'bench'),
       M.cube('bs_l1',[5,0,-2.5],[7,6,2.5],'wood'), M.cube('bs_l2',[23,0,-2.5],[25,6,2.5],'wood')]
    return M.group(tag+'root',[0,0,0],k)
