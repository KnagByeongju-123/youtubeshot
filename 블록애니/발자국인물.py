"""《눈 위 발자국》 블록 부품: 아빠(젊을 때·늙었을 때)·꼬마 아들·어른 아들·발자국.
   블록인물.py 의 Model·move·Anim·find 를 씀.  앞 = -z.  어른 키 32(모자 빼고), 꼬마 약 22 (s=0.68)
   면 겹침 막기(블록애니.md): 소매는 몸통 옆에서 시작, 옆머리는 뒷머리보다 바깥, 모자는 머리·옆머리보다 바깥"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 블록인물 import Model, move, anchor, Anim, find, U

SKIN=(240,202,170); SKIN_OLD=(232,192,160)
def palette(M):
    M.swatch('skin',SKIN,3); M.swatch('skin_o',SKIN_OLD,3)
    M.swatch('hair_b',(95,65,40),4); M.swatch('hair_w',(235,233,228),4); M.swatch('hair_k',(45,35,30),3)
    M.swatch('coat_g',(120,122,128),5); M.swatch('coat_go',(132,132,134),6); M.swatch('scarf_g',(60,140,85),5); M.swatch('scarf_gd',(45,110,65),4)
    M.swatch('boot_k',(45,40,40),3); M.swatch('pants_k',(70,70,78),4); M.swatch('btn',(40,40,45),2)
    M.swatch('hat_r',(215,50,55),6); M.swatch('hat_rd',(175,35,45),4); M.swatch('pom',(250,250,248),4)
    M.swatch('pad_y',(250,200,50),5); M.swatch('pad_yd',(225,170,35),4); M.swatch('mit_b',(60,120,210),4); M.swatch('boot_r',(220,55,55),4)
    M.swatch('pad_n',(45,60,100),5); M.swatch('pad_nd',(32,45,78),4); M.swatch('jeans',(70,100,150),5); M.swatch('boot_br',(120,80,50),4)
    M.swatch('wood',(130,85,50),5); M.swatch('snow',(245,248,252),3); M.swatch('print',(200,212,228),4); M.swatch('print_d',(178,192,212),4)
    def face(name, skin, brow, mustache=None, cheek=False, wrinkle=False):
        def fn(d,x,y):
            d.rectangle([x,y,x+15,y+15],fill=skin)
            for ex in (3,9):
                d.rectangle([x+ex,y+6,x+ex+3,y+9],fill=(255,255,255)); d.rectangle([x+ex+1,y+6,x+ex+2,y+9],fill=(30,25,25))
                d.rectangle([x+ex,y+5,x+ex+3,y+5],fill=brow)
            d.rectangle([x+7,y+10,x+8,y+10],fill=(205,155,125))
            if mustache: d.rectangle([x+5,y+11,x+10,y+12],fill=mustache); d.rectangle([x+6,y+13,x+9,y+13],fill=(165,85,75))
            else: d.rectangle([x+6,y+12,x+9,y+12],fill=(185,90,85))
            if cheek: d.rectangle([x+2,y+10,x+3,y+11],fill=(250,150,150)); d.rectangle([x+12,y+10,x+13,y+11],fill=(250,150,150))
            if wrinkle: d.line([x+2,y+4,x+4,y+4],fill=(200,160,130)); d.line([x+11,y+4,x+13,y+4],fill=(200,160,130))
        M.paint(name,fn)
    face('f_dad',SKIN,(80,55,35))
    face('f_dado',SKIN_OLD,(230,230,225),mustache=(235,233,228),wrinkle=True)
    face('f_kid',SKIN,(80,55,35),cheek=True)
    face('f_son',SKIN,(70,50,35))   # 어른은 볼 빨강 없음

def person(M, tag, kind='dad', s=1.0):
    """kind: dad(아빠) / dad_old(늙은 아빠, 지팡이) / kid(꼬마 아들) / son(어른 아들).
       묶음: body·head·arm_left(+x)·arm_right(-x)·leg_*·hand_l·hand_r (블록 인물과 같은 이름 → 걷기·손 흔들기 그대로)"""
    c=lambda name,fr,to,col,**f: M.cube(name,[v*s for v in fr],[v*s for v in to],col,**f)
    O=lambda v:[x*s for x in v]
    if kind in ('dad','dad_old'):
        old=kind=='dad_old'
        top=sleeve='coat_go' if old else 'coat_g'; pt,sh='pants_k','boot_k'; fc='f_dado' if old else 'f_dad'
        hair='hair_w' if old else 'hair_b'; skin='skin_o' if old else 'skin'; hand=skin
    elif kind=='kid': top,sleeve,pt,sh,fc,hair,skin,hand='pad_y','pad_y','pants_k','boot_r','f_kid','hair_k','skin','mit_b'
    else:             top,sleeve,pt,sh,fc,hair,skin,hand='pad_n','pad_n','jeans','boot_br','f_son','hair_k','skin','skin'
    boot_h=4
    legL=M.group(tag+'leg_left',O([2,12,0]),[c('leg',[0,boot_h,-2],[4,12,2],pt), c('shoe',[0.02,0,-2.8],[4.2,boot_h,2.2],sh)])
    legR=M.group(tag+'leg_right',O([-2,12,0]),[c('leg',[-4,boot_h,-2],[0,12,2],pt), c('shoe',[-4.2,0,-2.8],[-0.02,boot_h,2.2],sh)])
    def arm(side):
        x0,x1=(4.2,8.2) if side>0 else (-8.2,-4.2); hx0,hx1=(4.7,7.7) if side>0 else (-7.7,-4.7)
        k=[c('sleeve',[x0,15,-2.2],[x1,24,2.2],sleeve), c('hand',[hx0,12,-1.6],[hx1,15,1.6],hand)]
        hg=M.group(tag+('hand_l' if side>0 else 'hand_r'),O([6.2*side,12.5,0]),[])
        return M.group(tag+('arm_left' if side>0 else 'arm_right'),O([6.2*side,22,0]),k+[hg])
    armL,armR=arm(1),arm(-1)
    body=[c('torso',[-4.2,12,-2.2],[4.2,24,2.2],top)]
    if kind in ('dad','dad_old'):   # 무릎까지 오는 겨울 코트 + 초록 목도리
        body+= [c('coat_low',[-4.5,7,-2.5],[4.5,13,2.5],top), c('cbtn1',[-0.6,18,-2.38],[0.6,19.2,-2.25],'btn'),
                c('cbtn2',[-0.6,14,-2.38],[0.6,15.2,-2.25],'btn'), c('cbtn3',[-0.6,9.5,-2.68],[0.6,10.7,-2.55],'btn'),
                c('scarf',[-4.4,22,-2.6],[4.4,24.3,2.6],'scarf_g'), c('scarf_tail',[-3,15,-2.85],[-1,22,-2.55],'scarf_gd')]
    if kind=='kid':     # 볼록한 패딩 (가로 줄)
        body+= [c('pad_low',[-4.5,9,-2.5],[4.5,13,2.5],top),
                c('pline1',[-4.3,20,-2.3],[4.3,20.7,2.3],'pad_yd'), c('pline2',[-4.3,16.5,-2.3],[4.3,17.2,2.3],'pad_yd'),
                c('zip',[-0.35,9.5,-2.62],[0.35,23.5,-2.25],'pad_yd')]
    if kind=='son':
        body+= [c('pad_low',[-4.5,8,-2.5],[4.5,13,2.5],top),
                c('pline1',[-4.3,20,-2.3],[4.3,20.7,2.3],'pad_nd'), c('pline2',[-4.3,16,-2.3],[4.3,16.7,2.3],'pad_nd'),
                c('zip',[-0.35,8.5,-2.62],[0.35,23.5,-2.25],'pad_nd'), c('collar',[-4.4,22.6,-2.6],[4.4,24.2,2.6],'pad_nd')]
    hk=[c('head',[-4,24,-4],[4,32,4],skin,north=fc,up=hair,south=hair),
        c('hair_back',[-4.2,25.5,1.2],[4.2,32.2,4.2],hair), c('hair_top',[-4.25,31.2,-4.25],[4.25,32.4,4.25],hair),
        c('hair_side_l',[3.95,28,-1],[4.3,32,3.9],hair), c('hair_side_r',[-4.3,28,-1],[-3.95,32,3.9],hair)]
    if kind in ('kid','son'):   # 빨간 털모자 + 흰 방울 (어릴 때와 커서 같은 모자)
        hk+= [c('hat',[-4.5,30.4,-4.5],[4.5,34,4.5],'hat_r'), c('hat_band',[-4.65,29.6,-4.65],[4.65,31.2,4.65],'hat_rd'),
              c('hat_top',[-3.2,34,-3.2],[3.2,35,3.2],'hat_r'), c('pom',[-1.4,35,-1.4],[1.4,37.6,1.4],'pom')]
    if kind=='dad_old':   # 지팡이 (오른손)
        armR['children'].append(M.group(tag+'cane',O([-6.2,12.5,0]),[c('cane',[-6.8,-9,-3.4],[-5.6,13,-2.2],'wood'), c('cane_h',[-6.9,11.8,-3.5],[-5.5,13.1,0],'wood')]))
    head=M.group(tag+'head',O([0,24,0]),hk)
    bod=M.group(tag+'body',O([0,12,0]),body+[head,armL,armR])
    return M.group(tag+'root',[0,0,0],[bod,legL,legR])

def footprint(M, tag, big=True):
    """눈 위 발자국 하나 (앞 = -z). 바닥 눈 높이 y=0 바로 위에 얇게. big=어른(장화 길이 7), 작은 것 = 꼬마(길이 4.8)"""
    s=1.0 if big else 0.68
    c=lambda n,fr,to,col: M.cube(n,[v*s for v in fr],[v*s for v in to],col)
    return M.group(tag+'root',[0,0,0],[c('fp_sole',[-2.1,0.04,-3.6],[2.1,0.16,1.0],'print'),
                                       c('fp_heel',[-1.8,0.04,1.4],[1.8,0.16,3.4],'print'),
                                       c('fp_toe',[-1.6,0.17,-3.3],[1.6,0.22,-1.6],'print_d')])
