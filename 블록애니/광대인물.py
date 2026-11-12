"""《줄 끊긴 광대》 부품: 광대 나무 인형(doll2 + 주름 깃·원뿔 모자·볼 화장), 회색 쥐, 인형극 무대(커튼·조종 막대·줄 고리).
   나무인형.py 의 cyl·sphere·doll2 를 씀.  앞 = -z.  줄 고리 묶음: 광대 손목 hand_l/hand_r, 무릎 knee_l/knee_r, 막대 끝 bar_*"""
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 나무인형 import *

def palette_all(M):
    palette(M)
    def diamond(a,b):
        def fn(x,y): return a if ((x//4)+(y//4))%2==0 else b   # 마름모(체크) 무늬
        return fn
    M.swatch('clown_rb',diamond((210,55,50),(245,200,60)),3); M.swatch('clown_br',diamond((60,110,190),(245,240,230)),3)
    M.swatch('ruff',(250,250,245),2); M.swatch('clown_hat',(210,55,50),4); M.swatch('pompom',(245,200,60),3); M.swatch('clown_shoe',(60,110,190),4)
    M.swatch('cheek_red',(230,80,80),2); M.swatch('mouse',(150,150,155),5); M.swatch('mouse_d',(115,115,120),4); M.swatch('mouse_pink',(240,160,170),3)
    M.swatch('curtain',lambda x,y:(170,30,40) if x%4 else (130,20,30),4); M.swatch('stage',wood_fn((150,100,58),(110,70,40),51),4)
    M.swatch('bar',wood_fn((120,80,45),(90,58,32),52),3); M.swatch('rope',(235,230,215),2); M.swatch('gold',(220,180,80),4)

CLOWN=dict(shirt='clown_rb',bottom='pants',bottom_col='clown_br',shoe='clown_shoe',hair='short',hair_col='wood_hair')

def clown(M, tag, s=1.0):
    """광대 인형: doll2 + 주름 깃 + 원뿔 모자(방울) + 둥근 빨간 볼.  줄 고리 묶음 knee_l·knee_r (다리), hand_l·hand_r (손)"""
    g=doll2(M,tag,s,CLOWN)
    S=lambda p:[x*s for x in p]
    body=find(g,tag+'body'); head=find(g,tag+'head')
    body['children']+= [cyl(M,'ruff',S([0,22.2,0]),S([0,23.4,0]),5.2*s,4.4*s,'ruff',seg=18), cyl(M,'ruff2',S([0,21.6,0]),S([0,22.3,0]),4.6*s,5.2*s,'ruff',seg=18)]
    head['children']+= [cyl(M,'hat',S([0,31.4,0.3]),S([0,38.5,0.8]),3.0*s,0.2*s,'clown_hat',seg=14), sphere(M,'pom',S([0,38.8,0.8]),0.9*s,'pompom',seg=8,rings=6),
                        sphere(M,'cheek_big_l',S([2.4,26.7,-3.05]),0.95*s,'cheek_red',seg=8,rings=6,sz=0.4), sphere(M,'cheek_big_r',S([-2.4,26.7,-3.05]),0.95*s,'cheek_red',seg=8,rings=6,sz=0.4)]
    for side,n in ((1,'l'),(-1,'r')):   # 무릎 줄 고리
        lg=find(g,tag+('leg_left' if side>0 else 'leg_right')); lg['children'].append(M.group(tag+'knee_'+n,S([2.1*side,7.4,-1.4]),[]))
    return g

def mouse(M, tag, s=1.0):
    """회색 쥐 (앞 = -z, 몸 길이 약 6).  묶음: body·head·tail·leg_fl/fr/bl/br"""
    S=lambda p:[x*s for x in p]
    def C(n,a,b,r0,r1,col,seg=10): return cyl(M,n,S(a),S(b),r0*s,r1*s,col,seg)
    def B(n,c,r,col,**k): return sphere(M,n,S(c),r*s,col,**k)
    G=lambda n,o,ch: M.group(tag+n,S(o),ch)
    legs=[G(n,[x,1.2,z],[C('leg',[x,1.2,z],[x,0,z],0.3,0.3,'mouse_pink',seg=6)]) for n,x,z in (('leg_fl',0.9,-1.4),('leg_fr',-0.9,-1.4),('leg_bl',0.9,1.4),('leg_br',-0.9,1.4))]
    hk=[B('head',[0,2.4,-3.2],1.25,'mouse',seg=10,rings=8,sz=1.3), B('snout',[0,2.2,-4.6],0.5,'mouse_pink',seg=8,rings=6),
        B('ear_l',[0.9,3.5,-2.8],0.7,'mouse_pink',seg=8,rings=6,sz=0.3), B('ear_r',[-0.9,3.5,-2.8],0.7,'mouse_pink',seg=8,rings=6,sz=0.3),
        B('eye_l',[0.6,2.75,-4.0],0.2,'eye_k',seg=6,rings=4), B('eye_r',[-0.6,2.75,-4.0],0.2,'eye_k',seg=6,rings=4),
        C('whisker',[-1.4,2.2,-4.4],[1.4,2.2,-4.4],0.05,0.05,'eye_k',seg=4)]
    head=G('head',[0,2.2,-2.2],hk)
    tail=G('tail',[0,1.6,2.6],[C('tail',[0,1.6,2.6],[0,2.6,7.0],0.22,0.08,'mouse_pink',seg=6)])
    body=G('body',[0,1.8,0],[B('torso',[0,1.9,0],1.8,'mouse',seg=12,rings=8,sx=0.85,sz=1.5), head, tail])
    return G('root',[0,0,0],[body]+legs)

def stage(M, tag, W=70, D=40, H=8):
    """인형극 무대: 나무 무대(높이 H) + 양옆·위 빨간 커튼 + 조종 막대(십자, 위에 매달림).  광대는 무대 가운데 (0,H,0)"""
    k=[M.cube('st_floor',[-W/2,0,-D/2],[W/2,H,D/2],'stage'), M.cube('st_front',[-W/2-1,0,-D/2-1],[W/2+1,H-0.6,-D/2],'curtain'),
       M.cube('st_cl',[-W/2,H,-D/2],[-W/2+8,H+56,-D/2+3],'curtain'), M.cube('st_cr',[W/2-8,H,-D/2],[W/2,H+56,-D/2+3],'curtain'),
       M.cube('st_top',[-W/2,H+48,-D/2],[W/2,H+58,-D/2+3],'curtain'), M.cube('st_trim',[-W/2,H+47,-D/2-0.3],[W/2,H+48,-D/2+3],'gold'),
       M.cube('st_back',[-W/2,H,D/2-1],[W/2,H+56,D/2],'curtain')]
    return M.group(tag+'root',[0,0,0],k)

def control_bar(M, tag, y, s=1.0):
    """조종 막대 (십자): 줄 끝 고리 bar_hl·bar_hr(손)·bar_kl·bar_kr(무릎).  묶음 중심 (0,y,0)"""
    k=[M.cube('cb_x',[-9*s,y-0.5,-0.6],[9*s,y+0.5,0.6],'bar'), M.cube('cb_z',[-0.6,y-0.5,-6*s],[0.6,y+0.5,6*s],'bar'),
       M.cube('cb_hold',[-0.4,y+0.5,-0.4],[0.4,y+30,0.4],'rope')]
    ends=[M.group(tag+'bar_hl',[8.5*s,y,0],[]), M.group(tag+'bar_hr',[-8.5*s,y,0],[]), M.group(tag+'bar_kl',[2.5*s,y,-5.5*s],[]), M.group(tag+'bar_kr',[-2.5*s,y,-5.5*s],[])]
    return M.group(tag+'root',[0,y,0],k+ends)
