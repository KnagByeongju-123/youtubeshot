"""《서툰 아빠의 머리 묶기》 블록 부품: 딸(머리 3가지)·아빠(리본)·털실 인형(머리 2가지) + 빗·의자·거울 등.
   블록인물.py 의 Model·Anim 을 그대로 씀.  앞 = -z.  아빠 키 32, 딸 키 32*0.62 ≈ 20, 인형 키 32*0.28 ≈ 9
   묶음 이름은 다른 블록 인물과 같음: root·body·head·arm_left/right·leg_left/right·hand_l/r
   머리 묶음: hair_loose·hair_messy·hair_neat (크기 0/1 로 바꿔 보임), 아빠 리본 dad_ribbon"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 블록인물 import Model, Anim

SKIN=(240,200,165); HAIR=(30,26,28); YARN=(150,90,50)

def palette(M):
    M.swatch('mskin',SKIN,3); M.swatch('m_hair',HAIR,3); M.swatch('m_yarn',lambda x,y:(150,90,50) if (x+y)%3 else (125,72,40),3)
    M.swatch('dress',(250,210,70),5); M.swatch('dress_d',(225,180,45),4); M.swatch('tights',(250,250,250),2); M.swatch('shoe_p',(240,140,170),3)
    M.swatch('shirt_w',(246,246,246),2); M.swatch('tie',(40,55,105),3); M.swatch('trouser',(110,112,120),4); M.swatch('shoe_k',(40,38,40),2)
    M.swatch('ribbon',(225,45,60),3); M.swatch('ribbon_d',(185,30,45),3); M.swatch('band',(225,45,60),2)
    M.swatch('doll_c',(130,190,230),4); M.swatch('doll_s',(250,230,210),3); M.swatch('m_sole',(150,150,155),2)
    def face(name,hc,cheek=(245,150,135),button=False):
        def fn(d,x,y):
            d.rectangle([x,y,x+15,y+15],fill=SKIN if not button else (250,230,210))
            for ex in (3,9):
                if button: d.rectangle([x+ex+1,y+6,x+ex+2,y+8],fill=(30,30,30)); continue
                d.rectangle([x+ex,y+6,x+ex+3,y+9],fill=(255,255,255)); d.rectangle([x+ex+1,y+6,x+ex+2,y+9],fill=(25,20,20))
                d.rectangle([x+ex,y+5,x+ex+3,y+5],fill=hc)
            if not button: d.rectangle([x+7,y+10,x+8,y+10],fill=(215,165,130))
            d.rectangle([x+6,y+12,x+9,y+12],fill=(175,85,75))
            d.rectangle([x+2,y+11,x+3,y+11],fill=cheek); d.rectangle([x+12,y+11,x+13,y+11],fill=cheek)
        M.paint(name,fn)
    face('mf_girl',HAIR); face('mf_dad',HAIR,cheek=SKIN); face('mf_doll',HAIR,button=True)
    # 소품
    M.swatch('comb',(230,120,150),2); M.swatch('wood_f',(175,125,80),5); M.swatch('wood_d',(140,95,60),5)
    M.swatch('mirror',(200,225,240),2); M.swatch('lamp',(255,235,160),2); M.swatch('lamp_s',(70,70,75),2)

def hair_sets(M, c, hc, tie='band', neat_bow=True, only=None):
    """긴 머리 3가지 묶음(머리 묶음 좌표, 머리 중심 기준).  돌려주는 값: (loose, messy, neat) 상자 목록"""
    base=[c('hb',[-4.5,25.5,1.2],[4.5,32.2,4.5],hc), c('ht',[-4.25,31.2,-4.25],[4.25,32.6,4.25],hc),
          c('hsl',[3.95,28,-1],[4.3,32,3.9],hc), c('hsr',[-4.3,28,-1],[-3.95,32,3.9],hc), c('bang',[-4.1,30,-4.35],[4.1,31.3,-4.15],hc)]
    want=lambda k: only in (None,k)
    loose=[] if not want('loose') else [c('lb',[-4.3,19,4.2],[4.3,31.8,4.9],hc), c('ll',[4.3,21,-1.5],[4.9,31.8,4.9],hc), c('lr',[-4.9,21,-1.5],[-4.3,31.8,4.9],hc)]
    messy=[] if not want('messy') else [c('mk',[2.6,30.5,0.5],[6.2,33.6,3.6],hc), c('mband',[3.8,30.2,1.3],[5.2,31.2,2.8],tie),     # 한쪽 위로 삐뚤어진 꽁지
           c('mt',[4.2,24.5,1.5],[7.2,30.6,3.4],hc),
           c('ms1',[0.5,32.6,-1.5],[1.5,34.6,-0.5],hc), c('ms2',[-3.2,32.6,1],[-2.2,34,2],hc),          # 삐죽 튀어나온 머리카락
           c('ms3',[-5.3,27,0.2],[-4.3,29.4,1.4],hc), c('ms4',[-5,24,3],[-4.3,27,4.3],hc), c('ms5',[-2,24.6,4.2],[0.5,27.5,5.2],hc)]
    if not want('neat'): return base,loose,messy,[]
    neat=[c('nt_l',[4.3,22,0.8],[6.1,28.5,3.0],hc), c('nt_r',[-6.1,22,0.8],[-4.3,28.5,3.0],hc)]
    if neat_bow:
        neat+= [c('bow_l',[4.2,28.5,-0.2],[6.6,30.6,3.8],'ribbon'), c('knot_l',[6.6,29.1,1.2],[7.0,30.0,2.4],'ribbon_d'),
                c('bow_r',[-6.6,28.5,-0.2],[-4.2,30.6,3.8],'ribbon'), c('knot_r',[-7.0,29.1,1.2],[-6.6,30.0,2.4],'ribbon_d')]
    else:
        neat+= [c('nband_l',[4.2,28.5,0.6],[6.2,29.4,3.2],tie), c('nband_r',[-6.2,28.5,0.6],[-4.2,29.4,3.2],tie)]
    return base,loose,messy,neat

def girl(M, tag, s=0.62, doll=False, only=None):
    """딸 (doll=True 면 털실 인형: 하늘색 옷, 단추 눈, 털실 머리, 리본 대신 빨간 고무줄)"""
    c=lambda name,fr,to,col,**f: M.cube(name,[v*s for v in fr],[v*s for v in to],col,**f)
    O=lambda v:[x*s for x in v]
    top,topd,leg_c,shoe=('doll_c','doll_c','doll_s','doll_c') if doll else ('dress','dress_d','tights','shoe_p')
    skin='doll_s' if doll else 'mskin'
    def leg(side):
        x0,x1=(0,4) if side>0 else (-4,0)
        k=[c('leg',[x0+0.05,1.6,-1.95],[x1-0.05,10,1.95],leg_c),
           c('shoe',[x0+(0.05 if side>0 else -0.1),0,-2.8],[x1+(0.1 if side>0 else -0.05),1.6,2.2],shoe,down='m_sole')]
        return M.group(tag+('leg_left' if side>0 else 'leg_right'),O([2*side,12,0]),k)
    def arm(side):
        a,b=(4.2,8.2) if side>0 else (-8.2,-4.2)
        k=[c('sleeve',[a,20,-2.2],[b,24,2.2],top), c('arm',[a+0.2,14,-1.9],[b-0.2,20,1.9],skin), c('hand',[a+0.4,12,-1.6],[b-0.4,14,1.6],skin)]
        h=M.group(tag+('hand_l' if side>0 else 'hand_r'),O([6*side,12.5,0]),[])
        return M.group(tag+('arm_left' if side>0 else 'arm_right'),O([6*side,22,0]),k+[h])
    body=[c('torso',[-4.2,13,-2.2],[4.2,24,2.2],top), c('skirt',[-5.2,9,-3.0],[5.2,13.4,3.0],top), c('skirt_hem',[-5.25,8.95,-3.05],[5.25,9.8,3.05],topd)]
    hc='m_yarn' if doll else 'm_hair'
    base,loose,messy,neat=hair_sets(M,c,hc,neat_bow=not doll,only=only)
    hk=[c('head',[-4,24,-4],[4,32,4],skin,north='mf_doll' if doll else 'mf_girl',up=hc,south=hc)]+base
    gl=M.group(tag+'hair_loose',O([0,28,0]),loose); gm=M.group(tag+'hair_messy',O([0,28,0]),messy); gn=M.group(tag+'hair_neat',O([0,28,0]),neat)
    head=M.group(tag+'head',O([0,24,0]),hk+[gl,gm,gn])
    bod=M.group(tag+'body',O([0,12,0]),body+[head,arm(1),arm(-1)])
    return M.group(tag+'root',[0,0,0],[bod,leg(1),leg(-1)])

def dad(M, tag, s=1.0, ribbon=True):
    c=lambda name,fr,to,col,**f: M.cube(name,[v*s for v in fr],[v*s for v in to],col,**f)
    O=lambda v:[x*s for x in v]
    def leg(side):
        x0,x1=(0,4) if side>0 else (-4,0)
        k=[c('trouser',[x0,1.4,-2],[x1,12,2],'trouser'),
           c('shoe',[x0+(0.05 if side>0 else -0.1),0,-2.9],[x1+(0.1 if side>0 else -0.05),1.4,2.2],'shoe_k',down='m_sole')]
        return M.group(tag+('leg_left' if side>0 else 'leg_right'),O([2*side,12,0]),k)
    def arm(side):
        a,b=(4.2,8.2) if side>0 else (-8.2,-4.2)
        k=[c('sleeve',[a,14,-2.2],[b,24,2.2],'shirt_w'), c('hand',[a+0.4,12,-1.6],[b-0.4,14,1.6],'mskin')]
        h=M.group(tag+('hand_l' if side>0 else 'hand_r'),O([6*side,12.5,0]),[])
        return M.group(tag+('arm_left' if side>0 else 'arm_right'),O([6*side,22,0]),k+[h])
    body=[c('torso',[-4.2,12,-2.2],[4.2,24,2.2],'shirt_w'), c('tie',[-0.7,15,-2.45],[0.7,23.6,-2.25],'tie'),
          c('tie_k',[-1,22.6,-2.6],[1,23.8,-2.32],'tie'), c('belt',[-4.3,11.95,-2.35],[4.3,13.1,2.35],'shoe_k')]
    hk=[c('head',[-4,24,-4],[4,32,4],'mskin',north='mf_dad',up='m_hair',south='m_hair'),
        c('hb',[-4.2,27,1.2],[4.2,32.2,4.2],'m_hair'), c('ht',[-4.25,31.2,-4.25],[4.25,32.8,4.25],'m_hair'),
        c('hsl',[3.95,29,-1],[4.3,32,3.9],'m_hair'), c('hsr',[-4.3,29,-1],[-3.95,32,3.9],'m_hair'),
        c('bang',[-4.1,30.6,-4.35],[4.1,31.3,-4.15],'m_hair')]
    rib=M.group(tag+'dad_ribbon',O([2.5,33,0]),[c('rb',[0.8,32.6,-1.6],[4.2,34.6,1.6],'ribbon'), c('rk',[2.0,32.4,-0.6],[3.0,35.0,0.6],'ribbon_d')] if ribbon else [])
    head=M.group(tag+'head',O([0,24,0]),hk+[rib])
    bod=M.group(tag+'body',O([0,12,0]),body+[head,arm(1),arm(-1)])
    return M.group(tag+'root',[0,0,0],[bod,leg(1),leg(-1)])

def comb(M, tag):
    """분홍 빗 (손잡이 + 빗살).  원점 = 손잡이 끝"""
    k=[M.cube('comb_h',[-0.4,0,-0.3],[0.4,3,0.3],'comb'), M.cube('comb_b',[-1.6,3,-0.3],[1.6,4,0.3],'comb')]
    for i in range(5): k.append(M.cube('tooth',[-1.5+i*0.7,4,-0.15],[-1.1+i*0.7,5.2,0.15],'comb'))
    return M.group(tag+'root',[0,0,0],k)
