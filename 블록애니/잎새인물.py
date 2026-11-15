"""《마지막 잎새》 나무 인형 인물·소품 (doll2 옷 설정 + 베레모·물감 앞치마) + 색.
   인물: girl(꼬마 소녀, 하늘색 잠옷) / grandpa(화가 할아버지) / woman(어른 소녀, 화가) / grandpa_old(늙은 할아버지, 잠옷)
   앞 = -z.  묶음 이름은 블록 인물과 같음 (팔·다리 통째로)"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 나무인형 import *

def palette_all(M):
    palette(M)
    M.swatch('l_pj',wood_fn((165,200,230),(135,172,205),51),3)          # 하늘색 잠옷
    M.swatch('l_cream',wood_fn((232,222,196),(205,192,165),52),3)       # 크림 셔츠
    M.swatch('l_apron',wood_fn((150,105,68),(118,80,50),53),3)          # 갈색 앞치마
    M.swatch('l_beret',wood_fn((45,58,98),(32,42,74),54),3)             # 남색 베레모
    M.swatch('l_grey',wood_fn((150,150,150),(120,120,120),55),3); M.swatch('l_white',wood_fn((238,236,230),(208,205,198),56),3)
    M.swatch('l_pants',wood_fn((105,105,110),(80,80,86),57),3); M.swatch('l_shoe',wood_fn((90,62,42),(65,44,30),58),3)
    M.swatch('l_green',wood_fn((95,140,95),(72,112,72),59),3); M.swatch('l_skirt',wood_fn((125,88,60),(98,68,46),60),3)
    M.swatch('l_slipper',(245,242,235),2)
    M.swatch('l_red',(205,60,55),2); M.swatch('l_blue',(70,110,190),2); M.swatch('l_yellow',(245,200,60),2)
    M.swatch('l_leaf',(70,135,60),3); M.swatch('l_leaf_y',(205,165,55),3); M.swatch('l_leaf_paint',(80,150,70),2)
    M.swatch('l_lamp_glass',(255,225,140),2); M.swatch('l_metal',(60,60,64),3); M.swatch('l_ladder',wood_fn((170,125,80),(135,95,60),61),3)

GIRL =dict(shirt='l_pj',belt='l_pj',bottom='pants',bottom_col='l_pj',shoe='l_slipper',hair='pigtails')
GP   =dict(shirt='l_cream',bottom='pants',bottom_col='l_pants',shoe='l_shoe',hair='none',hair_col='l_grey',beard='l_white',mustache='l_white')
GPO  =dict(shirt='l_pj',belt='l_pj',bottom='pants',bottom_col='l_pj',shoe='l_slipper',hair='none',hair_col='l_white',beard='l_white',mustache='l_white')
WOMAN=dict(shirt='l_green',bottom='coat',bottom_col='l_skirt',shoe='l_shoe',leg_col='wood',hair='ponytail')

def _add(g, tag, name, items):
    grp=find(g, tag+name); grp['children']+= items

def person(M, tag, kind='grandpa', s=1.0, beret=None, apron=None):
    """beret·apron 을 따로 주지 않으면 인물에 맞게 (할아버지 둘 = 베레모, 할아버지·어른 소녀 = 앞치마)"""
    o={'girl':GIRL,'grandpa':GP,'grandpa_old':GPO,'woman':WOMAN}[kind]
    g=doll2(M,tag,s,o)
    if beret is None: beret = kind in ('grandpa','grandpa_old')
    if apron is None: apron = kind in ('grandpa','woman')
    S=lambda p:[x*s for x in p]
    B=lambda n,c,r,col,**k: sphere(M,n,S(c),r*s,col,**k)
    if kind in ('grandpa','grandpa_old'):   # 베레모 밑으로 살짝 보이는 짧은 머리 (귀 뒤·뒤통수, 작게)
        hc=o['hair_col']
        _add(g,tag,'head',[B('hair_back',[0,28.9,2.9],3.3,hc,seg=14,rings=6,sy=0.42,sz=0.42),
                           B('hair_l',[3.55,28.4,1.4],0.75,hc,seg=8,rings=6,sx=0.6,sz=1.2), B('hair_r',[-3.55,28.4,1.4],0.75,hc,seg=8,rings=6,sx=0.6,sz=1.2)])
    if kind=='woman':   # 어릴 때와 같은 노란 리본 (묶은 머리 위, 뒤에서 잘 보이게 크게)
        _add(g,tag,'head',[B('bow_l',[1.3,29.2,4.6],1.1,'paint_ribbon',seg=10,rings=6,sx=1.1,sz=0.6), B('bow_r',[-1.3,29.2,4.6],1.1,'paint_ribbon',seg=10,rings=6,sx=1.1,sz=0.6),
                           B('bow_c',[0,29.2,4.75],0.6,'paint_ribbon',seg=8,rings=6,sz=0.6)])
    if beret:   # 납작한 베레모, 오른쪽으로 살짝 기울어 + 꼭지
        _add(g,tag,'head',[B('beret',[0.5,31.3,0.3],4.45,'l_beret',seg=16,rings=8,sy=0.34), B('beret_tip',[0.5,32.9,0.3],0.45,'l_beret',seg=8,rings=6)])
    if apron:   # 물감 묻은 앞치마 (치마 위에선 조금 더 앞으로)
        zf = -4.55 if kind=='woman' else -4.25; yb = 9.4 if kind=='woman' else 8.6
        it=[M.cube('apron',S([-2.9,yb,zf]),S([2.9,19.5,zf+0.4]),'l_apron'),
            M.cube('strap_l',S([1.6,19.4,-4.1]),S([2.4,21.8,-3.6]),'l_apron'), M.cube('strap_r',S([-2.4,19.4,-4.1]),S([-1.6,21.8,-3.6]),'l_apron'),
            M.cube('pocket',S([-1.6,12.4,zf-0.2]),S([1.6,14.4,zf]),'wood_dk')]
        for i,(x,y,col) in enumerate([(1.6,17.6,'l_red'),(-1.4,16.2,'l_blue'),(0.6,15.2,'l_yellow'),(-2.0,11.0,'l_leaf_paint'),(1.9,10.4,'l_red')]):
            if y>yb+0.5: it.append(B(f'paint{i}',[x,y,zf-0.05],0.42,col,seg=8,rings=6,sz=0.35))
        _add(g,tag,'body',it)
    return g

# ---------------- 소품 ----------------
def brush(M, tag, base, s=1.0):
    """붓: base(손 자리)에서 위로 (손에 쥘 땐 hand_r/hand_l 묶음에 넣음)"""
    x,y,z=base
    return M.group(tag+'brush',[x,y,z],[cyl(M,'brush_stick',[x,y-1.0*s,z-1.2*s],[x,y+5.0*s,z-1.2*s],0.3*s,0.3*s,'wood_dk',seg=8),
           cyl(M,'brush_ferrule',[x,y+5.0*s,z-1.2*s],[x,y+5.8*s,z-1.2*s],0.34*s,0.34*s,'l_metal',seg=8),
           cyl(M,'brush_tip',[x,y+5.8*s,z-1.2*s],[x,y+7.2*s,z-1.2*s],0.38*s,0.05*s,'l_leaf_paint',seg=8)])

def lamp(M, tag, base, s=1.0):
    """등불(바닥에 놓는 손등): base = 바닥 가운데"""
    x,y,z=base; S=s
    return M.group(tag+'lamp',[x,y,z],[M.cube('lamp_base',[x-1.6*S,y,z-1.6*S],[x+1.6*S,y+0.6*S,z+1.6*S],'l_metal'),
           cyl(M,'lamp_glass',[x,y+0.6*S,z],[x,y+4.2*S,z],1.3*S,1.1*S,'l_lamp_glass',seg=12),
           M.cube('lamp_top',[x-1.5*S,y+4.2*S,z-1.5*S],[x+1.5*S,y+4.9*S,z+1.5*S],'l_metal'),
           cyl(M,'lamp_handle',[x-1.1*S,y+5.6*S,z],[x+1.1*S,y+5.6*S,z],0.22*S,0.22*S,'l_metal',seg=6),
           cyl(M,'lamp_post_l',[x-1.1*S,y+4.9*S,z],[x-1.1*S,y+5.7*S,z],0.22*S,0.22*S,'l_metal',seg=6),
           cyl(M,'lamp_post_r',[x+1.1*S,y+4.9*S,z],[x+1.1*S,y+5.7*S,z],0.22*S,0.22*S,'l_metal',seg=6)])

def ladder(M, tag, base, h=34, w=6.0, lean=0.0):
    """사다리: base = 바닥 가운데 (x 방향 폭 w, 위로 h). lean = 벽 쪽(+z)으로 기운 거리"""
    x,y,z=base; k=[]
    for sx in (-1,1): k.append(M.cube('rail',[x+sx*w/2-0.5,y,z-0.5],[x+sx*w/2+0.5,y+h,z+0.5],'l_ladder'))
    for i in range(1,int(h//5)+1): k.append(M.cube('rung',[x-w/2,y+i*5-0.35,z-0.35],[x+w/2,y+i*5+0.35,z+0.35],'l_ladder'))
    return M.group(tag+'ladder',[x,y,z],k)

def leaf(M, name, c, col='l_leaf', s=1.0, flat=False):
    """담쟁이 잎 하나 (세 갈래 둥근 잎, 벽에 붙음: 벽 = +z 쪽, 앞면 -z).  flat=True 면 벽에 그린 잎(더 납작)"""
    sz=0.12 if flat else 0.3
    return [sphere(M,name+'_m',[c[0],c[1]+0.5*s,c[2]],1.15*s,col,seg=10,rings=6,sz=sz),
            sphere(M,name+'_l',[c[0]-0.9*s,c[1],c[2]],0.85*s,col,seg=8,rings=6,sz=sz),
            sphere(M,name+'_r',[c[0]+0.9*s,c[1],c[2]],0.85*s,col,seg=8,rings=6,sz=sz),
            cyl(M,name+'_st',[c[0],c[1]-0.4*s,c[2]],[c[0],c[1]-1.6*s,c[2]],0.12*s,0.1*s,'wood_dk',seg=6)]
