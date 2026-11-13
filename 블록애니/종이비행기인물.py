"""《창문 너머 종이비행기》 블록 부품: 아이 4가지(도윤 환자복·도윤 퇴원·하은·새 아이) + 종이비행기·그림 종이.
   블록인물.py 의 Model·Anim 을 그대로 씀.  앞 = -z.  아이 키 32*s (s≈0.7 → 약 22)
   묶음 이름은 다른 블록 인물과 같음: root·body·head·arm_left/right·leg_left/right·hand_l/r"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 블록인물 import Model, Anim

SKIN=(240,200,165); HAIR=(32,28,28); BROWN=(95,60,35)

def stripes(c1,c2):
    return lambda x,y: c1 if (y//3)%2 else c2

def palette(M):
    M.swatch('pskin',SKIN,3); M.swatch('pwhite',(248,248,245),2); M.swatch('psole',(150,150,155),2)
    M.swatch('pj_blue',stripes((150,200,235),(235,245,252)),2); M.swatch('pj_blue_d',(120,170,210),3)
    M.swatch('pj_pink',stripes((240,170,195),(252,236,242)),2); M.swatch('pj_pink_d',(215,140,168),3)
    M.swatch('hat_y',(250,200,50),5); M.swatch('hat_y_d',(220,165,30),5)
    M.swatch('hat_b',(120,185,235),5); M.swatch('hat_b_d',(90,155,210),5)
    M.swatch('hoodie',(40,55,100),5); M.swatch('hoodie_d',(30,42,80),4); M.swatch('pgrey',(130,130,138),4)
    M.swatch('bag',(205,50,45),4); M.swatch('bag_d',(160,35,32),3)
    M.swatch('orange',(245,140,50),5); M.swatch('orange_d',(210,110,35),4); M.swatch('denim',(80,120,180),5)
    M.swatch('h_black',HAIR,3); M.swatch('h_brown',BROWN,3); M.swatch('tie_y',(250,215,60),3)
    M.swatch('paper',(252,252,250),1); M.swatch('paper_d',(228,228,225),1)
    def face(name,hc,cheek=(245,150,135)):
        def fn(d,x,y):
            d.rectangle([x,y,x+15,y+15],fill=SKIN)
            for ex in (3,9):
                d.rectangle([x+ex,y+6,x+ex+3,y+9],fill=(255,255,255)); d.rectangle([x+ex+1,y+6,x+ex+2,y+9],fill=(25,20,20))
                d.rectangle([x+ex,y+5,x+ex+3,y+5],fill=hc)
            d.rectangle([x+7,y+10,x+8,y+10],fill=(215,165,130))
            d.rectangle([x+6,y+12,x+9,y+12],fill=(175,85,75))
            d.rectangle([x+2,y+11,x+3,y+11],fill=cheek); d.rectangle([x+12,y+11,x+13,y+11],fill=cheek)
        M.paint(name,fn)
    face('pf_doyun',HAIR,(235,175,160)); face('pf_haeun',BROWN); face('pf_new',HAIR)
    def drawing(d,x,y):   # 그림 종이: 노란 해 + 웃는 얼굴 (글자 없음)
        d.rectangle([x,y,x+15,y+15],fill=(252,252,250))
        d.ellipse([x+1,y+1,x+5,y+5],fill=(250,200,40))
        d.ellipse([x+6,y+6,x+14,y+14],outline=(60,120,210)); d.point((x+8,y+9),fill=(60,120,210)); d.point((x+12,y+9),fill=(60,120,210))
        d.line([x+8,y+12,x+12,y+12],fill=(220,60,60))
    M.paint('drawing',drawing)

LOOK={
 'doyun':  dict(top='pj_blue',top_d='pj_blue_d',pants='pj_blue',long_top=True,long_pants=True,shoe='pwhite',hc='h_black',hat=('hat_y','hat_y_d'),face='pf_doyun',slipper=True),
 'doyun2': dict(top='hoodie',top_d='hoodie_d',pants='pgrey',long_top=True,long_pants=True,shoe='pwhite',hc='h_black',hat=('hat_y','hat_y_d'),face='pf_doyun',bag=True,hood=True),
 'haeun':  dict(top='orange',top_d='orange_d',pants='denim',long_top=False,long_pants=False,shoe='pwhite',hc='h_brown',hair='pigtail',face='pf_haeun'),
 'new':    dict(top='pj_pink',top_d='pj_pink_d',pants='pj_pink',long_top=True,long_pants=True,shoe='pwhite',hc='h_black',hat=('hat_b','hat_b_d'),hair='long',face='pf_new',slipper=True),
}

def child(M, tag, who='doyun', s=0.7):
    K=LOOK[who]; top,topd,pt,hc=K['top'],K['top_d'],K['pants'],K['hc']
    c=lambda name,fr,to,col,**f: M.cube(name,[v*s for v in fr],[v*s for v in to],col,**f)
    O=lambda v:[x*s for x in v]
    def leg(side):
        x0,x1=(0,4) if side>0 else (-4,0)
        sh=1.0 if K.get('slipper') else 1.6
        if K['long_pants']: k=[c('pants',[x0,sh,-2],[x1,12,2],pt)]
        else: k=[c('shorts',[x0,8,-2],[x1,12,2],pt), c('knee',[x0+0.05,3.4,-1.95],[x1-0.05,8,1.95],'pskin'),
                 c('sock',[x0,1.6,-2],[x1,3.4,2],'pwhite')]
        k.append(c('shoe',[x0+(0.05 if side>0 else -0.1),0,-2.8],[x1+(0.1 if side>0 else -0.05),sh,2.2],K['shoe'],down='psole'))
        return M.group(tag+('leg_left' if side>0 else 'leg_right'),O([2*side,12,0]),k)
    def arm(side):
        a,b=(4.2,8.2) if side>0 else (-8.2,-4.2)
        if K['long_top']: k=[c('sleeve',[a,14,-2.2],[b,24,2.2],top), c('hand',[a+0.4,12,-1.6],[b-0.4,14,1.6],'pskin')]
        else: k=[c('sleeve',[a,19,-2.2],[b,24,2.2],top), c('arm',[a+0.2,14,-1.9],[b-0.2,19,1.9],'pskin'),
                 c('hand',[a+0.4,12,-1.6],[b-0.4,14,1.6],'pskin')]
        h=M.group(tag+('hand_l' if side>0 else 'hand_r'),O([6*side,12.5,0]),[])
        return M.group(tag+('arm_left' if side>0 else 'arm_right'),O([6*side,22,0]),k+[h])
    body=[c('torso',[-4.2,12,-2.2],[4.2,24,2.2],top), c('hem',[-4.25,11.6,-2.25],[4.25,12.6,2.25],topd)]
    if K['long_top'] and not K.get('hood'): body+= [c('btn1',[-0.5,20,-2.4],[0.5,21,-2.25],topd), c('btn2',[-0.5,16,-2.4],[0.5,17,-2.25],topd)]
    if K.get('hood'): body+= [c('hood',[-3.4,20.5,2.25],[3.4,24.2,3.6],topd), c('pocket',[-2.6,13.5,-2.38],[2.6,16.5,-2.25],topd)]
    if K.get('bag'): body+= [c('bag',[-3.4,13.5,3.65],[3.4,22.5,6.2],'bag'), c('bag_flap',[-3.45,19.5,6.2],[3.45,22.6,6.5],'bag_d'),
                             c('strap_l',[2,15,-2.4],[3,24.05,-2.25],'bag_d'), c('strap_r',[-3,15,-2.4],[-2,24.05,-2.25],'bag_d')]
    hk=[c('head',[-4,24,-4],[4,32,4],'pskin',north=K['face'],up=hc,south=hc),
        c('hair_back',[-4.2,25.5,1.2],[4.2,32.2,4.2],hc),
        c('hair_side_l',[3.95,28,-1],[4.3,32,3.9],hc), c('hair_side_r',[-4.3,28,-1],[-3.95,32,3.9],hc)]
    if K.get('hat'):   # 털모자: 머리 위를 덮고 아래 접힌 단 + 꼭대기 방울
        h1,h2=K['hat']
        hk+= [c('hat',[-4.4,29.6,-4.4],[4.4,33.4,4.4],h1), c('hat_fold',[-4.6,28.6,-4.6],[4.6,30.2,4.6],h2),
              c('pom',[-1.1,33.4,-1.1],[1.1,35.2,1.1],h2)]
    else:
        hk+= [c('hair_top',[-4.25,31.2,-4.25],[4.25,32.6,4.25],hc), c('bang',[-4.1,30.2,-4.35],[4.1,31.3,-4.15],hc)]
    H=K.get('hair')
    if H=='pigtail':   # 양갈래: 귀 뒤 양옆에 늘어진 머리 + 노란 머리끈
        hk+= [c('tail_l',[4.3,23.5,0.6],[5.8,28.4,2.8],hc), c('tie_l',[4.25,28.4,0.5],[5.9,29.6,2.9],'tie_y'),
              c('tail_r',[-5.8,23.5,0.6],[-4.3,28.4,2.8],hc), c('tie_r',[-5.9,28.4,0.5],[-4.25,29.6,2.9],'tie_y')]
    elif H=='long':    # 어깨까지 오는 머리 (모자 아래로)
        hk+= [c('long_l',[4.3,23.6,-2],[4.9,28.6,4.5],hc), c('long_r',[-4.9,23.6,-2],[-4.3,28.6,4.5],hc),
              c('long_b',[-4.3,23.6,4.2],[4.3,28.6,4.8],hc)]
    head=M.group(tag+'head',O([0,24,0]),hk)
    bod=M.group(tag+'body',O([0,12,0]),body+[head,arm(1),arm(-1)])
    return M.group(tag+'root',[0,0,0],[bod,leg(1),leg(-1)])

def plane(M, tag, s=1.5):
    """하얀 종이비행기 (앞 = -z, 길이 5*s).  계단식 세모 날개 — 칸마다 높이를 조금씩 달리해 면이 겹치지 않게"""
    c=lambda n,fr,to,col: M.cube(n,[v*s for v in fr],[v*s for v in to],col)
    k=[c('keel',[-0.25,-0.5,-2.5],[0.25,0.25,2.6],'paper_d'),
       c('wing1',[-0.9,0.25,-1.6],[0.9,0.4,2.55],'paper'), c('wing2',[-1.7,0.2,-0.3],[1.7,0.35,2.5],'paper'),
       c('wing3',[-2.5,0.15,1.1],[2.5,0.3,2.45],'paper')]
    return M.group(tag+'root',[0,0,0],k)

def sheet(M, tag, s=1.0):
    """그림 종이 (세워 든 모양, +z 쪽 면에 그림).  가운데가 묶음 원점"""
    return M.group(tag+'root',[0,0,0],[M.cube('sheet',[-2.6*s,-2*s,-0.05],[2.6*s,2*s,0.05],'paper',south='drawing')])
