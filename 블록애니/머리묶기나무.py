"""《서툰 아빠의 머리 묶기》 나무 인형판 부품 (사용자 결정 2026-11-13: 블록 인물 대신 나무 인형).
   나무인형.py 의 doll2(원통·공 메시, 팔·다리 통째로 흔들기)에 머리 모양 묶음을 더함.  앞 = -z
   · 아빠 dad_w (s=1.15, 키 약 37): 흰 셔츠·남색 넥타이·회색 바지·검은 구두·짧은 검은 머리, 리본 묶음 dad_ribbon
   · 딸 girl_w (s=0.68, 키 약 22): 노란 원피스·흰 타이츠·분홍 신발, 검은 머리 — 묶음 hair_loose / hair_messy / hair_neat(+ bow_right)
   · 연습 인형 yarn_w (s=0.3): 하늘색 원피스, 갈색 털실 머리 — hair_messy / hair_neat"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 나무인형 import Model, Anim, cyl, sphere, wood_fn, palette as wood_palette, doll2, find

def palette(M):
    wood_palette(M)
    M.swatch('p_white',wood_fn((244,242,236),(220,216,208),21),2); M.swatch('p_tie',wood_fn((45,60,110),(32,44,85),22),2)
    M.swatch('p_grey',wood_fn((115,117,125),(90,92,100),23),2); M.swatch('p_black',(45,42,44),2)
    M.swatch('p_yellow',wood_fn((250,208,70),(222,178,45),24),3); M.swatch('p_tights',(250,250,248),2); M.swatch('p_pink',wood_fn((240,140,170),(215,115,145),25),2)
    M.swatch('h_black',wood_fn((48,40,40),(28,22,22),26),2); M.swatch('p_red',(222,48,60),2); M.swatch('p_red_d',(180,32,45),2)
    M.swatch('p_sky',wood_fn((140,195,232),(110,165,205),27),2); M.swatch('yarn',lambda x,y:(165,100,55) if (x+2*y)%4 else (130,75,40),2)

def hair_groups(M, tag, s, hc, bow='p_red', only=None):
    """긴 머리 3가지 (머리 묶음 안에 넣음).  only='loose'|'messy'|'neat' 이면 그것만"""
    S=lambda p:[x*s for x in p]
    def C(n,a,b,r0,r1,col,seg=8): return cyl(M,n,S(a),S(b),r0*s,r1*s,col,seg)
    def B(n,c,r,col,**k): return sphere(M,n,S(c),r*s,col,**k)
    G=lambda n,ch: M.group(tag+n,S([0,28,0]),ch)
    out=[]
    if only in (None,'loose'):
        out.append(G('hair_loose',[B('lb',[0,25.4,2.4],3.7,hc,seg=14,rings=8,sy=1.55,sz=0.62),
                                   B('lsl',[3.4,25.6,0.9],1.3,hc,seg=10,rings=6,sx=0.6,sy=2.0), B('lsr',[-3.4,25.6,0.9],1.3,hc,seg=10,rings=6,sx=0.6,sy=2.0)]))
    if only in (None,'messy'):   # 한쪽 위로 삐뚤어진 꽁지 + 삐죽 튀어나온 머리카락
        out.append(G('hair_messy',[B('knot',[3.0,31.8,0.9],1.75,hc,seg=10,rings=8), B('mtail',[4.9,29.0,1.5],1.25,hc,seg=10,rings=6,sy=1.7),
                                   B('mband',[3.9,30.6,1.2],0.75,bow,seg=8,rings=6),
                                   C('st1',[0.4,32.6,-0.6],[1.2,35.0,-1.2],0.5,0.12,hc), C('st2',[-2.1,32.3,1.4],[-3.6,34.3,2.4],0.5,0.12,hc),
                                   C('st3',[-3.9,28.8,0.4],[-5.8,30.0,0.0],0.45,0.1,hc), C('st4',[-1.4,27.0,3.6],[-2.6,25.2,5.6],0.5,0.12,hc),
                                   C('st5',[1.8,26.4,3.4],[3.2,24.2,5.0],0.45,0.1,hc)]))
    if only in (None,'neat'):    # 예쁜 양갈래 + 리본 (오른쪽 리본은 따로 묶음 bow_right)
        br=M.group(tag+'bow_right',S([-4.3,29.4,1.0]),[B('bow_r1',[-4.3,29.4,0.0],0.95,bow,seg=8,rings=6,sx=0.7,sy=0.9,sz=1.3),
                                                       B('bow_r2',[-4.3,29.4,2.0],0.95,bow,seg=8,rings=6,sx=0.7,sy=0.9,sz=1.3),
                                                       B('bow_rk',[-4.6,29.4,1.0],0.55,'p_red_d',seg=8,rings=6)])
        out.append(G('hair_neat',[B('nt_l',[4.7,26.4,1.0],1.5,hc,seg=10,rings=6,sy=1.75), B('nt_r',[-4.7,26.4,1.0],1.5,hc,seg=10,rings=6,sy=1.75),
                                  B('bow_l1',[4.3,29.4,0.0],0.95,bow,seg=8,rings=6,sx=0.7,sy=0.9,sz=1.3), B('bow_l2',[4.3,29.4,2.0],0.95,bow,seg=8,rings=6,sx=0.7,sy=0.9,sz=1.3),
                                  B('bow_lk',[4.6,29.4,1.0],0.55,'p_red_d',seg=8,rings=6), br]))
    return out

def _head(root, tag): return find(root, tag+'head')

def girl_w(M, tag, s=0.68, only=None):
    g=doll2(M,tag,s,{'shirt':'p_yellow','bottom':'skirt','bottom_col':'p_yellow','leg_col':'p_tights','shoe':'p_pink','hair':'short','hair_col':'h_black'})
    _head(g,tag)['children']+= hair_groups(M,tag,s,'h_black',only=only)
    return g

def yarn_w(M, tag, s=0.3, only=None):
    g=doll2(M,tag,s,{'shirt':'p_sky','bottom':'skirt','bottom_col':'p_sky','leg_col':'wood','shoe':'p_sky','hair':'short','hair_col':'yarn'})
    _head(g,tag)['children']+= hair_groups(M,tag,s,'yarn',bow='p_red',only=only if only else None) if only!='none' else []
    return g

def dad_w(M, tag, s=1.15, ribbon=True):
    d=doll2(M,tag,s,{'shirt':'p_white','bottom':'pants','bottom_col':'p_grey','shoe':'p_black','hair':'short','hair_col':'h_black'})
    S=lambda p:[x*s for x in p]
    body=find(d,tag+'body')
    body['children']+= [cyl(M,'tie',S([0,21.6,-3.95]),S([0,15.8,-4.05]),0.55*s,0.75*s,'p_tie',seg=8), sphere(M,'tie_k',S([0,21.8,-3.9]),0.6*s,'p_tie',seg=8,rings=6)]
    rib=M.group(tag+'dad_ribbon',S([1.6,32.4,0]),[sphere(M,'drb1',S([0.9,32.4,0]),0.95*s,'p_red',seg=8,rings=6,sx=1.3,sy=0.9,sz=0.7),
                                                 sphere(M,'drb2',S([2.9,32.2,0]),0.95*s,'p_red',seg=8,rings=6,sx=1.3,sy=0.9,sz=0.7),
                                                 sphere(M,'drbk',S([1.9,32.6,0]),0.55*s,'p_red_d',seg=8,rings=6)] if ribbon else [])
    _head(d,tag)['children'].append(rib)
    return d

def comb_w(M, tag):
    """분홍 빗 (나무).  원점 = 손잡이 끝"""
    k=[M.cube('comb_h',[-0.4,0,-0.3],[0.4,3,0.3],'p_pink'), M.cube('comb_b',[-1.6,3,-0.3],[1.6,4,0.3],'p_pink')]
    for i in range(5): k.append(M.cube('tooth',[-1.5+i*0.7,4,-0.15],[-1.1+i*0.7,5.2,0.15],'p_pink'))
    return M.group(tag+'root',[0,0,0],k)
