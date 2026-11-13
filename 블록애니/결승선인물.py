"""《같이 들어온 결승선》 블록 부품: 아이 5명(하준·서연·빨강·파랑·보라) + 결승 기둥·테이프 + 만국기 줄.
   블록인물.py 의 Model·Anim 을 그대로 씀.  앞 = -z.  아이 키 32*s (s≈0.7 → 약 22)
   묶음 이름은 다른 블록 인물과 같음: root·body·head·arm_left/right·leg_left/right·hand_l/r"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 블록인물 import Model, Anim

SKIN=(240,200,165); HAIR=(32,28,28); BROWN=(95,60,35)

# 아이마다: 티셔츠 색, 바지 색, 머리 모양, 머리 색
KIDS={
 'hajun': dict(top=(250,205,45), top_d=(215,170,30), pants=(40,55,100), hair='short', hc=HAIR, brace=True),
 'seoyeon': dict(top=(80,165,85), top_d=(60,130,65), pants=(35,35,40), hair='pony', hc=BROWN),
 'red':   dict(top=(210,55,50), top_d=(170,40,38), pants=(40,55,100), hair='short', hc=HAIR),
 'blue':  dict(top=(60,120,210), top_d=(45,95,170), pants=(35,35,40), hair='round', hc=(55,40,30)),
 'purple': dict(top=(150,95,190), top_d=(120,75,155), pants=(40,55,100), hair='bob', hc=HAIR),
}

def palette(M):
    M.swatch('skin',SKIN,3); M.swatch('skin_d',(220,178,140),3)
    M.swatch('sock',(248,248,245),2); M.swatch('shoe',(245,245,240),2); M.swatch('sole',(150,150,155),2)
    M.swatch('silver',(195,200,208),4); M.swatch('strap',(30,45,90),3); M.swatch('tie',(215,40,45),3)
    for k,v in KIDS.items():
        M.swatch('top_'+k,v['top'],5); M.swatch('topd_'+k,v['top_d'],4); M.swatch('pants_'+k,v['pants'],4)
        M.swatch('hair_'+k,v['hc'],3); M.swatch('shoe_'+k,v['top_d'],3)
    # 소품
    M.swatch('pole',(235,235,235),3); M.swatch('pole_r',(210,50,45),3); M.swatch('tape',(252,252,252),1)
    M.swatch('rope',(90,80,70),2)
    for i,c in enumerate([(220,60,55),(245,190,40),(70,150,220),(80,170,90),(240,240,240),(160,95,200)]):
        M.swatch(f'flag{i}',c,3)
    def face(name,hc,cheek=True,glasses=False):
        def fn(d,x,y):
            d.rectangle([x,y,x+15,y+15],fill=SKIN)
            if glasses:   # 얇은 갈색 안경테 + 연한 하늘색 알 (눈은 그 위에)
                for ex in (2,8):
                    d.rectangle([x+ex,y+5,x+ex+5,y+10],fill=(215,232,245),outline=(90,55,35))
            for ex in (3,9):
                d.rectangle([x+ex,y+6,x+ex+3,y+9],fill=(255,255,255)); d.rectangle([x+ex+1,y+6,x+ex+2,y+9],fill=(25,20,20))
                if not glasses: d.rectangle([x+ex,y+5,x+ex+3,y+5],fill=hc)
            d.rectangle([x+7,y+10,x+8,y+10],fill=(215,165,130))
            d.rectangle([x+6,y+12,x+9,y+12],fill=(175,85,75))
            if cheek: d.rectangle([x+2,y+11,x+3,y+11],fill=(245,150,135)); d.rectangle([x+12,y+11,x+13,y+11],fill=(245,150,135))
        M.paint(name,fn)
    for k,v in KIDS.items(): face('f_'+k,v['hc'],glasses=(k=='blue'))

def kid(M, tag, who='hajun', s=0.7):
    """아이 한 명.  반팔 티 + 반바지 + 흰 양말·운동화.  hajun 은 오른다리(-x)에 은색 보조기"""
    K=KIDS[who]; top,topd,pt,hc='top_'+who,'topd_'+who,'pants_'+who,'hair_'+who
    c=lambda name,fr,to,col,**f: M.cube(name,[v*s for v in fr],[v*s for v in to],col,**f)
    O=lambda v:[x*s for x in v]
    def leg(side):
        x0,x1=(0,4) if side>0 else (-4,0)
        k=[c('shorts',[x0,8,-2],[x1,12,2],pt), c('knee',[x0+0.05,4,-1.95],[x1-0.05,8,1.95],'skin'),
           c('sock',[x0,1.6,-2],[x1,4,2],'sock'), c('shoe',[x0+(0.05 if side>0 else -0.1),0,-2.8],[x1+(0.1 if side>0 else -0.05),1.6,2.2],'shoe_'+who,down='sole')]
        if side<0 and K.get('brace'):   # 보조기: 바깥 막대 + 띠 2개 (허벅지 아래·종아리)
            k+= [c('brace_bar',[-4.45,2.2,-0.6],[-3.98,9.6,0.6],'silver'),
                 c('brace_s1',[-4.25,7.6,-2.2],[-0.15,8.6,2.2],'strap'),
                 c('brace_s2',[-4.25,3.6,-2.2],[-0.15,4.6,2.2],'strap')]
        n='leg_left' if side>0 else 'leg_right'
        return M.group(tag+n,O([2*side,12,0]),k)
    def arm(side):
        a,b=(4.2,8.2) if side>0 else (-8.2,-4.2)
        k=[c('sleeve',[a,19,-2.2],[b,24,2.2],top), c('arm',[a+0.2,14,-1.9],[b-0.2,19,1.9],'skin'),
           c('hand',[a+0.4,12,-1.6],[b-0.4,14,1.6],'skin')]
        h=M.group(tag+('hand_l' if side>0 else 'hand_r'),O([6*side,12.5,0]),[])
        return M.group(tag+('arm_left' if side>0 else 'arm_right'),O([6*side,22,0]),k+[h])
    body=[c('torso',[-4.2,12,-2.2],[4.2,24,2.2],top), c('neck_band',[-2,23.2,-2.4],[2,24,-2.25],topd),
          c('hem',[-4.25,11.6,-2.25],[4.25,12.6,2.25],topd)]
    fc='f_'+who
    hk=[c('head',[-4,24,-4],[4,32,4],'skin',north=fc,up=hc,south=hc),
        c('hair_back',[-4.2,25.5,1.2],[4.2,32.2,4.2],hc), c('hair_top',[-4.25,31.2,-4.25],[4.25,32.6,4.25],hc),
        c('hair_side_l',[3.95,28,-1],[4.3,32,3.9],hc), c('hair_side_r',[-4.3,28,-1],[-3.95,32,3.9],hc)]
    H=K['hair']
    if H=='short':
        hk+= [c('bang',[-4.1,30.4,-4.35],[4.1,31.3,-4.15],hc)]
    elif H=='round':   # 둥근 머리: 앞머리 두껍게 + 옆이 조금 부풂
        hk+= [c('bang',[-4.1,29.6,-4.35],[4.1,31.3,-4.15],hc), c('puff_l',[4.3,26.5,-2],[4.8,32,3.6],hc), c('puff_r',[-4.8,26.5,-2],[-4.3,32,3.6],hc)]
    elif H=='bob':     # 단발: 귀밑까지 옆·뒤 + 앞머리
        hk+= [c('bang',[-4.1,29.8,-4.35],[4.1,31.3,-4.15],hc), c('bob_l',[4.3,24.8,-2.6],[4.9,32,4.8],hc),
              c('bob_r',[-4.9,24.8,-2.6],[-4.3,32,4.8],hc), c('bob_b',[-4.3,24.8,4.2],[4.3,31.9,4.8],hc)]
    elif H=='pony':    # 꽁지머리: 뒤통수에 빨간 머리끈 + 아래로 내려온 꽁지
        hk+= [c('bang',[-4.1,30.2,-4.35],[4.1,31.3,-4.15],hc), c('tie',[-1.1,28.6,4.15],[1.1,30.6,4.9],'tie'),
              c('pony',[-1.3,22.5,4.5],[1.3,29.4,6.4],hc)]
    head=M.group(tag+'head',O([0,24,0]),hk)
    bod=M.group(tag+'body',O([0,12,0]),body+[head,arm(1),arm(-1)])
    return M.group(tag+'root',[0,0,0],[bod,leg(1),leg(-1)])

def finish_line(M, tag, w=60, h=26):
    """결승 기둥 둘(흰·빨강 줄무늬) + 흰 테이프 (반쪽씩 묶음 tape_l·tape_r: 끊길 때 기둥 쪽으로 늘어짐)"""
    k=[]
    for x in (-w/2, w/2):
        for i in range(0,h,4):
            k.append(M.cube('pole',[x-0.8,i,-0.8],[x+0.8,min(i+4,h),0.8],'pole' if (i//4)%2==0 else 'pole_r'))
        k.append(M.cube('pole_top',[x-1.1,h,-1.1],[x+1.1,h+1.2,1.1],'pole_r'))
    ty=h*0.55
    tl=M.group(tag+'tape_l',[w/2,ty,0],[M.cube('tape',[0,ty-0.4,-0.1],[w/2-0.8,ty+0.4,0.1],'tape')])
    tr=M.group(tag+'tape_r',[-w/2,ty,0],[M.cube('tape',[-w/2+0.8,ty-0.4,-0.1],[0,ty+0.4,0.1],'tape')])
    return M.group(tag+'root',[0,0,0],k+[tl,tr])

def flags(M, tag, x0, x1, y, z, n=None):
    """만국기 줄: x0→x1 사이 줄 + 색 깃발(아래로 늘어진 네모, 글자 없음).  묶음 하나 → 크기 0 으로 숨김"""
    L=abs(x1-x0); n=n or int(L/5)
    k=[M.cube('rope',[min(x0,x1),y-0.15,z-0.15],[max(x0,x1),y+0.15,z+0.15],'rope')]
    for i in range(n):
        x=min(x0,x1)+(i+0.5)*L/n
        k.append(M.cube('flag',[x-1.4,y-3.4,z-0.05],[x+1.4,y-0.15,z+0.05],f'flag{i%6}'))
    return M.group(tag+'root',[0,0,0],k)
