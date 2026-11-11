"""《돌아온 새》 블록 부품: 등대 할머니·파랑새·새끼 새·등대·오두막·둥지 상자.
   블록인물.py 의 Model·move·Anim·find 를 그대로 씀.  앞 = -z.  할머니 키 약 30, 새 길이 약 7"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 블록인물 import Model, move, anchor, Anim, find, U

SKIN=(238,200,170); WHITE_HAIR=(232,230,226)

def palette(M):
    M.swatch('skin',SKIN,3); M.swatch('hair_w',WHITE_HAIR,4)
    M.swatch('cardigan',(170,140,200),5); M.swatch('cardigan_d',(140,112,170),4)
    M.swatch('skirt',(50,60,105),5); M.swatch('shoe',(90,60,45),4); M.swatch('stock',(205,195,185),3)
    M.swatch('apron',(245,240,225),3)
    M.swatch('bird',(55,120,215),5); M.swatch('bird_d',(40,90,170),4); M.swatch('belly',(245,245,240),3)
    M.swatch('beak',(250,190,40),3); M.swatch('leg',(235,150,60),3); M.swatch('chick',(160,205,240),5)
    M.swatch('bandage',(255,255,255),2); M.swatch('eye',(20,20,25),2)
    M.swatch('wood',(140,95,55),6); M.swatch('wood_d',(105,70,40),5); M.swatch('straw',(215,185,110),8)
    M.swatch('lh_white',(240,240,236),4); M.swatch('lh_red',(200,50,45),5); M.swatch('lh_glass',(250,235,150),3)
    M.swatch('lh_dark',(60,60,66),4); M.swatch('wall',(240,236,225),4); M.swatch('roof_b',(60,95,150),6)
    M.swatch('win',(150,195,225),3); M.swatch('frame',(250,250,250),2); M.swatch('door',(120,80,50),5)
    def face(d,x,y):
        d.rectangle([x,y,x+15,y+15],fill=SKIN)
        for ex in (2,9):   # 얇은 동그란 안경테 (안은 살색) + 작은 눈동자
            d.line([x+ex,y+5,x+ex+3,y+5],fill=(110,85,70)); d.line([x+ex,y+9,x+ex+3,y+9],fill=(110,85,70))
            d.line([x+ex-1,y+6,x+ex-1,y+8],fill=(110,85,70)); d.line([x+ex+4,y+6,x+ex+4,y+8],fill=(110,85,70))
            d.rectangle([x+ex+1,y+6,x+ex+2,y+8],fill=(30,25,25))
        d.line([x+6,y+6,x+8,y+6],fill=(110,85,70))
        d.rectangle([x+7,y+11,x+8,y+11],fill=(215,165,135))
        d.rectangle([x+5,y+13,x+10,y+13],fill=(185,95,90)); d.point((x+4,y+12),fill=(185,95,90)); d.point((x+11,y+12),fill=(185,95,90))
        d.rectangle([x+2,y+11,x+3,y+11],fill=(245,160,150)); d.rectangle([x+12,y+11,x+13,y+11],fill=(245,160,150))
    M.paint('f_grandma',face)

def grandma(M, tag, s=1.0):
    """등대 할머니 (키 약 30).  손 끝 묶음 hand_l / hand_r (+x 쪽 = 왼, -x 쪽 = 오른 이름), 어깨 자리 shoulder_l"""
    c=lambda name,fr,to,col,**f: M.cube(name,[v*s for v in fr],[v*s for v in to],col,**f)
    O=lambda v:[x*s for x in v]
    legL=M.group(tag+'leg_left',O([2,10,0]),[c('leg',[0.5,1.4,-1.6],[3.5,10,1.6],'stock'), c('shoe',[0.3,0,-2.6],[3.7,1.4,1.8],'shoe')])
    legR=M.group(tag+'leg_right',O([-2,10,0]),[c('leg',[-3.5,1.4,-1.6],[-0.5,10,1.6],'stock'), c('shoe',[-3.7,0,-2.6],[-0.3,1.4,1.8],'shoe')])
    armL_k=[c('sleeve',[4,13,-2],[7.8,22,2],'cardigan'), c('hand',[4.5,10.5,-1.5],[7.3,13,1.5],'skin')]
    armR_k=[c('sleeve',[-7.8,13,-2],[-4,22,2],'cardigan'), c('hand',[-7.3,10.5,-1.5],[-4.5,13,1.5],'skin')]
    hl=M.group(tag+'hand_l',O([5.9,10.5,0]),[]); hr=M.group(tag+'hand_r',O([-5.9,10.5,0]),[])
    armL=M.group(tag+'arm_left',O([5.9,21,0]),armL_k+[hl]); armR=M.group(tag+'arm_right',O([-5.9,21,0]),armR_k+[hr])
    body=[c('torso',[-4,12,-2.2],[4,22,2.2],'cardigan'), c('skirt',[-4.6,3,-2.8],[4.6,13,2.8],'skirt'),
          c('apron',[-3,4,-2.95],[3,12,-2.8],'apron'), c('btn1',[-0.5,19,-2.4],[0.5,20,-2.2],'cardigan_d'), c('btn2',[-0.5,16,-2.4],[0.5,17,-2.2],'cardigan_d')]
    sh=M.group(tag+'shoulder_l',O([6,22.2,0]),[])
    hk=[c('head',[-3.8,22,-3.8],[3.8,29.6,3.8],'skin',north='f_grandma',up='hair_w',south='hair_w'),
        c('hair_back',[-4,23.5,1],[4,29.8,4],'hair_w'), c('hair_top',[-4,29,-4],[4,30.2,4],'hair_w'),
        c('hair_side_l',[3.7,25,-1.5],[4,29.8,4],'hair_w'), c('hair_side_r',[-4,25,-1.5],[-3.7,29.8,4],'hair_w'),
        c('bun',[-2,26,3.8],[2,30,6.5],'hair_w')]
    head=M.group(tag+'head',O([0,22,0]),hk)
    bod=M.group(tag+'body',O([0,10,0]),body+[head,armL,armR,sh])
    return M.group(tag+'root',[0,0,0],[bod,legL,legR])

def bird(M, tag, s=1.0, chick=False, bandage=True):
    """파랑새 (앞 = -z, 길이 약 7*s).  묶음: body / head / wing_l(+x) wing_r(-x) / tail / bandage(날개 붕대)
       날개 펴기: wing_l(+x) z 회전 +, wing_r(-x) z 회전 - 가 바깥으로 (시트로 확인함)"""
    c=lambda name,fr,to,col,**f: M.cube(name,[v*s for v in fr],[v*s for v in to],col,**f)
    O=lambda v:[x*s for x in v]
    top='chick' if chick else 'bird'; topd='chick' if chick else 'bird_d'
    legs=[c('leg_l',[0.5,0,-0.3],[1.0,1.4,0.3],'leg'), c('leg_r',[-1.0,0,-0.3],[-0.5,1.4,0.3],'leg')]
    bk=[c('torso',[-1.6,1.4,-2.2],[1.6,4.4,2.2],top,down='belly',north='belly'), c('belly',[-1.3,1.3,-2.4],[1.3,3.6,0.5],'belly')]
    wl=M.group(tag+'wing_l',O([1.6,4.2,0]),[c('wing',[1.6,1.4,-2.0],[2.1,4.3,3.2],topd)]+
               ([M.group(tag+'bandage',O([1.85,3.1,0.2]),[c('band',[1.5,2.6,-0.6],[2.3,3.6,1.0],'bandage')])] if bandage else []))
    wr=M.group(tag+'wing_r',O([-1.6,4.2,0]),[c('wing',[-2.1,1.4,-2.0],[-1.6,4.3,3.2],topd)])
    tail=M.group(tag+'tail',O([0,3.4,2.2]),[c('tail',[-1.0,2.8,2.2],[1.0,3.4,5.2],topd)])
    hk=[c('head',[-1.4,3.8,-3.6],[1.4,6.4,-0.8],top,north=top), c('eye_l',[1.35,5.1,-3.0],[1.5,5.7,-2.4],'eye'),
        c('eye_r',[-1.5,5.1,-3.0],[-1.35,5.7,-2.4],'eye'), c('beak',[-0.45,4.6,-4.6],[0.45,5.3,-3.6],'beak'),
        c('cheek',[-1.2,3.9,-3.65],[1.2,4.6,-3.55],'belly')]
    head=M.group(tag+'head',O([0,4.6,-1.6]),hk)
    body=M.group(tag+'body',O([0,2.8,0]),bk+[head,wl,wr,tail])
    return M.group(tag+'root',[0,0,0],[body]+legs)

def nest_box(M, tag):
    """창가 나무 둥지 상자 (짚이 깔림, 앞이 열려 있음).  폭 12"""
    k=[M.cube('nb_base',[-6,0,-4],[6,1,4],'wood_d'), M.cube('nb_back',[-6,1,3],[6,6,4],'wood'),
       M.cube('nb_l',[5,1,-4],[6,6,4],'wood'), M.cube('nb_r',[-6,1,-4],[-5,6,4],'wood'),
       M.cube('nb_front',[-6,1,-4],[6,2.5,-3],'wood'), M.cube('nb_roof',[-7,6,-5],[7,7,5],'wood_d'),
       M.cube('nb_straw',[-5,1,-3],[5,2,3],'straw')]
    return M.group(tag+'root',[0,0,0],k)

def lighthouse(M, tag, H=110):
    """빨강·흰 줄무늬 등대 (아래 폭 28 → 위 18), 꼭대기 불빛 방 + 빨간 지붕, 아래 문.  앞 = -z"""
    k=[]; n=6; seg=H/n
    for i in range(n):
        w=28-10*i/n; col='lh_red' if i%2 else 'lh_white'
        k.append(M.cube('lh_seg',[-w/2,i*seg,-w/2],[w/2,(i+1)*seg,w/2],col))
    k+= [M.cube('lh_balcony',[-13,H,-13],[13,H+2,13],'lh_dark'),
         M.cube('lh_glass',[-8,H+2,-8],[8,H+14,8],'lh_glass'),
         M.cube('lh_frame1',[-8.4,H+2,-8.4],[-7,H+14,-7],'lh_dark'), M.cube('lh_frame2',[7,H+2,-8.4],[8.4,H+14,-7],'lh_dark'),
         M.cube('lh_frame3',[-8.4,H+2,7],[-7,H+14,8.4],'lh_dark'), M.cube('lh_frame4',[7,H+2,7],[8.4,H+14,8.4],'lh_dark'),
         M.cube('lh_roof1',[-10,H+14,-10],[10,H+17,10],'lh_red'), M.cube('lh_roof2',[-6,H+17,-6],[6,H+20,6],'lh_red'),
         M.cube('lh_roof3',[-2,H+20,-2],[2,H+24,2],'lh_dark'),
         M.cube('lh_door',[-4,0,-14.3],[4,14,-13.8],'door'), M.cube('lh_win',[-2.5,48,-12.6],[2.5,56,-12.1],'win')]
    return M.group(tag+'root',[0,0,0],k)

def cottage(M, tag):
    """작은 오두막 (폭 50, 깊이 36), 앞(-z)에 문과 창 2개, 오른쪽 창 아래 둥지 자리 = 묶음 nest_spot"""
    k=[M.cube('ct_wall',[-25,0,0],[25,26,36],'wall')]
    for i in range(4): k.append(M.cube('ct_roof',[-28+i*5,26+i*5,-3],[28-i*5,26+(i+1)*5,39],'roof_b'))
    k+= [M.cube('ct_door',[-5,0,-0.5],[5,18,0],'door'), M.cube('ct_knob',[2.5,8,-0.9],[3.5,9,-0.5],'lh_dark')]
    for wx in (-18,10):
        k+= [M.cube('ct_wf',[wx-1,9,-0.6],[wx+9,19,0],'frame'), M.cube('ct_w',[wx,10,-0.8],[wx+8,18,-0.6],'win'),
             M.cube('ct_sill',[wx-2,8,-4],[wx+10,9,0],'wood')]
    spot=M.group(tag+'nest_spot',[14,9,-2],[])
    return M.group(tag+'root',[0,0,0],k+[spot])
