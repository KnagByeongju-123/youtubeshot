"""《화성의 오디세이》 블록 부품: 탐사대원(자비스·해리슨·푸츠·르루아)·팬시 롱 + 화성 생물 넷
   (트윌 / 피라미드를 쌓는 것 / 꿈을 보여 주는 것 / 수레를 미는 것) + 수레.
   블록인물.py 의 Model·move·Anim·find 를 그대로 씀.  크기 기준: 사람 키 32.  앞 = -z"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 블록인물 import Model, move, anchor, Anim, find, U

SKIN=(232,190,155); 
def mars_palette(M):
    S=M.swatch
    S('skin',SKIN,3); S('skin_d',(205,160,125),3)
    S('h_brown',(95,62,40),4); S('h_black',(28,24,24),3); S('h_blond',(225,190,100),5); S('h_grey',(150,150,150),4)
    S('khaki',(176,150,100),6); S('khaki_d',(140,118,76),5)              # 자비스 탐사복
    S('navy',(45,60,100),5); S('navy_d',(32,42,72),4); S('gold',(225,185,70),4)   # 해리슨
    S('olive',(105,120,95),6); S('olive_d',(80,94,72),5)                 # 푸츠 작업복
    S('white',(238,238,232),3); S('white_d',(205,205,198),3)             # 르루아 흰 겉옷
    S('red',(200,50,55),5); S('red_d',(160,36,42),4)                     # 팬시 롱 옷
    S('boot',(70,48,34),4); S('belt',(48,38,30),3); S('leather',(110,72,44),5)
    S('steel',(150,156,165),6); S('steel_d',(105,110,120),5); S('glass',(150,210,230),3); S('black',(22,22,26),3)
    # 트윌
    S('tw',lambda x,y:(60,150,150) if (x//2+y//3)%3 else (45,125,130),5); S('tw_d',(38,105,112),5); S('tw_l',(120,200,190),5)
    S('tw_leg',(190,160,90),4); S('beak',(235,170,60),4); S('beak_d',(200,135,45),4); S('plume',(245,235,200),5)
    S('eye_k',(15,15,18),2); S('eye_w',(245,245,240),2)
    # 피라미드를 쌓는 것 (은회색 비늘)
    S('scale',lambda x,y:(168,172,178) if ((x+(y//4%2)*2)%4 and y%4) else (118,122,130),5); S('scale_d',(110,114,122),5)
    S('hole',(20,20,24),2); S('brick',lambda x,y:(196,188,172) if (x%16 not in(0,15) and y%16 not in(0,15)) else (140,132,118),6)
    # 꿈을 보여 주는 것
    S('rope',lambda x,y:(26,24,30) if y%4 else (58,40,66),4); S('rope_tip',(120,40,90),5); S('pit',(70,45,32),6)
    # 수레를 미는 것
    S('barrel',lambda x,y:(172,120,82) if x%8 not in(0,) else (120,80,54),6); S('barrel_d',(120,80,54),5)
    S('drum',(225,205,170),4); S('copper',(196,112,62),7); S('copper_d',(150,82,44),6)
    S('sand',(214,140,84),8); S('crystal',(150,245,255),3)
    def face(name,hair,nose=None,mous=None,glasses=False,lips=None,lash=False):
        def fn(d,x,y):
            d.rectangle([x,y,x+15,y+15],fill=SKIN); d.rectangle([x,y,x+15,y+2],fill=hair)
            for ex in (3,9):
                d.rectangle([x+ex,y+6,x+ex+3,y+8],fill=(255,255,255)); d.rectangle([x+ex+1,y+6,x+ex+2,y+8],fill=(25,20,20))
                d.rectangle([x+ex,y+5,x+ex+3,y+5],fill=hair if not lash else (25,20,20))
            if glasses:
                for ex in (2,8): d.rectangle([x+ex,y+4,x+ex+5,y+9],outline=(40,40,45))
            d.rectangle([x+7,y+9,x+8,y+10],fill=nose or (205,160,120))
            if mous: d.rectangle([x+4,y+11,x+11,y+12],fill=mous)
            d.rectangle([x+6,y+13,x+9,y+13],fill=lips or (170,80,70))
        M.paint(name,fn)
    face('f_jarvis',(95,62,40),nose=(225,95,85))            # 얼어서 빨간 코
    face('f_harrison',(150,150,150),mous=(150,150,150)); face('f_putz',(225,190,100)); face('f_leroy',(28,24,24),mous=(28,24,24))
    face('f_fancy',(225,190,100),lips=(210,50,60),lash=True)
    S('gskin',(120,190,110),3)
    def alien(d,x,y):
        d.rectangle([x,y,x+15,y+15],fill=(120,190,110))
        for ex in (2,9): d.rectangle([x+ex,y+5,x+ex+4,y+9],fill=(15,15,20)); d.rectangle([x+ex+1,y+6,x+ex+1,y+6],fill=(255,255,255))
        d.rectangle([x+6,y+12,x+9,y+12],fill=(60,110,60))
    M.paint('f_alien',alien)

PEOPLE={ # kind: (얼굴, 윗옷, 윗옷 어두운, 바지, 신, 머리색)
 'jarvis':('f_jarvis','khaki','khaki_d','khaki_d','boot','h_brown'),
 'harrison':('f_harrison','navy','navy_d','navy_d','black','h_grey'),
 'putz':('f_putz','olive','olive_d','olive','boot','h_blond'),
 'leroy':('f_leroy','white','white_d','navy_d','black','h_black'),
 'fancy':('f_fancy','red','red_d','skin','red_d','h_blond'),
 'alien':('f_alien','steel','steel_d','steel','black','gskin'),   # 옛 소설의 '겉모습만 다른 사람' 외계인 (은빛 옷·초록 얼굴·더듬이)
}
def human(M, tag, kind='jarvis', s=1.0, tank=True, gun=False):
    """탐사대원·팬시 롱 (키 32*s).  자비스: 가죽 모자+고글, 등에 물통(tank), gun=오른손 권총"""
    c=lambda name,fr,to,col,**f: M.cube(name,[v*s for v in fr],[v*s for v in to],col,**f)
    O=lambda v:[x*s for x in v]
    fc,top,topd,pt,sh,hc=PEOPLE[kind]
    sk='gskin' if kind=='alien' else 'skin'
    legL=M.group(tag+'leg_left',O([2,12,0]),[c('leg',[0,3,-2],[4,12,2],pt), c('shoe',[-0.2,0,-2.8],[4.2,3,2.2],sh)])
    legR=M.group(tag+'leg_right',O([-2,12,0]),[c('leg',[-4,3,-2],[0,12,2],pt), c('shoe',[-4.2,0,-2.8],[0.2,3,2.2],sh)])
    short = kind=='fancy'
    aL=[c('sleeve',[4,20 if short else 15,-2.2],[8.2,24,2.2],top), c('hand',[4.6,12,-1.6],[7.6,20 if short else 15,1.6],sk)]
    aR=[c('sleeve',[-8.2,20 if short else 15,-2.2],[-4,24,2.2],top), c('hand',[-7.6,12,-1.6],[-4.6,20 if short else 15,1.6],sk)]
    if gun: aR+= [M.group(tag+'gun',O([-6,12,-2]),[c('gun_grip',[-6.6,10.5,-2.4],[-5.4,13,-1],'black'), c('gun_barrel',[-6.6,12,-6.5],[-5.4,13.4,-1],'steel_d')])]   # 묶음 → 필요할 때만 보이게
    hl=M.group(tag+'hand_l',O([6,12.5,0]),[]); hr=M.group(tag+'hand_r',O([-6,12.5,0]),[])
    armL=M.group(tag+'arm_left',O([6,22,0]),aL+[hl]); armR=M.group(tag+'arm_right',O([-6,22,0]),aR+[hr])
    body=[c('torso',[-4.2,12,-2.2],[4.2,24,2.2],top)]
    if kind=='fancy':
        body+= [c('skirt',[-4.8,5,-3],[4.8,13,3],top), c('sash',[-4.4,13,-2.4],[4.4,14.4,2.4],'red_d')]
    else:
        body+= [c('belt',[-4.4,12,-2.4],[4.4,13.6,2.4],'belt'), c('collar',[-1.2,20,-2.5],[1.2,24,-2.3],topd)]
    if kind=='jarvis':
        body+= [c('strap_l',[1.8,13.6,-2.5],[3,24,-2.3],'leather'), c('strap_r',[-3,13.6,-2.5],[-1.8,24,-2.3],'leather'),
                c('holster',[-5,10,-1.5],[-4.3,13.4,1.5],'leather')]
        if tank: body+= [c('tank',[-3.4,13,2.2],[3.4,25,6.4],'steel'), c('tank_top',[-2.6,25,2.8],[2.6,26.2,5.8],'steel_d'),
                         c('tank_band',[-3.6,18,2.1],[3.6,19.4,6.6],'steel_d')]
    if kind=='harrison':
        body+= [c('btn1',[-0.5,17,-2.5],[0.5,18,-2.3],'gold'), c('btn2',[-0.5,14.6,-2.5],[0.5,15.6,-2.3],'gold'),
                c('ep_l',[4,23.4,-2.3],[7,24.3,2.3],'gold'), c('ep_r',[-7,23.4,-2.3],[-4,24.3,2.3],'gold')]
    if kind=='putz':
        body+= [c('bib',[-3,16,-2.6],[3,22,-2.2],'olive_d'), c('tool',[4.3,11,-1],[5,15,1],'steel_d')]
    if kind=='leroy':
        body+= [c('coat_low',[-4.5,6,-2.5],[4.5,13,2.5],'white'), c('coat_open',[-0.6,6,-2.6],[0.6,20,-2.4],'white_d')]
    hk=[c('head',[-4,24,-4],[4,32,4],sk,north=fc,up=hc,south=hc),
        c('hair_back',[-4.2,25.5,1.2],[4.2,32.2,4.2],hc), c('hair_top',[-4.2,31.2,-4.2],[4.2,32.4,4.2],hc),
        c('hair_side_l',[3.9,28,-1],[4.2,32,4],hc), c('hair_side_r',[-4.2,28,-1],[-3.9,32,4],hc)]
    if kind=='jarvis':     # 가죽 비행 모자 + 이마 위 고글
        hk+= [c('cap',[-4.4,29.4,-4.4],[4.4,32.8,4.4],'leather'), c('cap_ear_l',[3.9,25,-1.5],[4.5,29.4,3],'leather'),
              c('cap_ear_r',[-4.5,25,-1.5],[-3.9,29.4,3],'leather'), c('cap_back',[-4.3,25,3.6],[4.3,29.4,4.5],'leather'),
              c('goggle_l',[0.6,30,-4.9],[3.4,32,-4.3],'glass'), c('goggle_r',[-3.4,30,-4.9],[-0.6,32,-4.3],'glass'),
              c('goggle_band',[-4.5,30.6,-4.5],[4.5,31.4,4.5],'belt'), c('nose',[-0.8,26.2,-4.7],[0.8,27.4,-4],'red')]
    if kind=='harrison':   # 대장 모자
        hk+= [c('cap',[-4.4,31,-4.4],[4.4,34,4.4],'navy'), c('cap_band',[-4.5,31,-4.5],[4.5,32,4.5],'gold'), c('visor',[-4,30.6,-6.4],[4,31.2,-4.2],'black')]
    if kind=='alien':      # 더듬이 둘 + 어깨 장식
        hk=hk[:1]+[c('ant_l',[1.5,32,-0.5],[2.5,37,0.5],'steel'), c('ant_r',[-2.5,32,-0.5],[-1.5,37,0.5],'steel'), c('ant_bl',[1,37,-1],[3,39,1],'red'), c('ant_br',[-3,37,-1],[-1,39,1],'red')]
    if kind=='fancy':      # 어깨 아래까지 내려오는 금발
        hk+= [c('hair_long',[-4.4,19,2],[4.4,26,4.6],hc), c('hair_fl',[3.6,21,-1],[4.6,28,3],hc), c('hair_fr',[-4.6,21,-1],[-3.6,28,3],hc)]
    head=M.group(tag+'head',O([0,24,0]),hk)
    bod=M.group(tag+'body',O([0,12,0]),body+[head,armL,armR])
    return M.group(tag+'root',[0,0,0],[bod,legL,legR])

def tweel(M, tag, s=1.0, bag=True, gun=False):
    """트윌: 둥근 몸·골프채처럼 가는 다리·긴 목·작은 머리·긴 부리(휘는 주둥이), 네 손가락·네 발가락, 목에 검은 가방. 키 약 36"""
    c=lambda name,fr,to,col,**f: M.cube(name,[v*s for v in fr],[v*s for v in to],col,**f)
    O=lambda v:[x*s for x in v]
    def leg(sx):
        x0,x1=(1.8,3.2) if sx>0 else (-3.2,-1.8); m=(x0+x1)/2
        k=[c('leg',[x0,1,-0.7],[x1,15,0.7],'tw_leg'), c('knee',[x0-0.3,8,-1],[x1+0.3,9.6,1],'tw_leg'),
           c('toe_f1',[m-2.2,0,-4],[m-1.2,1,0],'tw_leg'), c('toe_f2',[m-0.5,0,-4.6],[m+0.5,1,0],'tw_leg'),
           c('toe_f3',[m+1.2,0,-4],[m+2.2,1,0],'tw_leg'), c('toe_b',[m-0.5,0,0],[m+0.5,1,2.6],'tw_leg'), c('pad',[m-2.2,0,-1.2],[m+2.2,1.2,0.8],'tw_leg')]
        return M.group(tag+('leg_left' if sx>0 else 'leg_right'),O([m,15,0]),k)
    def arm(sx):
        x0,x1=(6,7.2) if sx>0 else (-7.2,-6); m=(x0+x1)/2
        k=[c('arm',[x0,14,-0.6],[x1,23,0.6],'tw_d'), c('palm',[x0-0.4,12.6,-1.2],[x1+0.4,14,1.2],'tw_leg')]
        for i,dz in enumerate((-1.4,-0.5,0.4,1.1)): k.append(c(f'finger{i}',[m-0.3,10.4,dz],[m+0.3,12.6,dz+0.5],'tw_leg'))
        if gun and sx<0: k+= [M.group(tag+'gun',O([m,12,-2]),[c('gun_grip',[m-0.8,10.6,-2.6],[m+0.8,12.8,-1.2],'glass'), c('gun_barrel',[m-0.5,11.6,-6],[m+0.5,12.6,-1.2],'glass')])]
        k.append(M.group(tag+('hand_l' if sx>0 else 'hand_r'),O([m,11.5,0]),[]))
        return M.group(tag+('arm_left' if sx>0 else 'arm_right'),O([m,23,0]),k)
    beak=M.group(tag+'beak',O([0,34,-1.8]),[c('beak1',[-0.9,33.2,-6.5],[0.9,34.8,-1.8],'beak'),
          c('beak2',[-0.7,32.9,-10],[0.7,34.2,-6.5],'beak'), c('beak_tip',[-0.5,32.4,-12],[0.5,33.5,-10],'beak_d')])
    hk=[c('head',[-1.8,32.2,-1.8],[1.8,35.8,1.8],'tw_l'),
        c('eye_l',[1.7,34,-1.2],[2.1,35,-0.2],'eye_k'), c('eye_r',[-2.1,34,-1.2],[-1.7,35,-0.2],'eye_k'),
        c('whisk_l',[0.9,32.4,-3.4],[2.6,33.2,-1.6],'plume'), c('whisk_r',[-2.6,32.4,-3.4],[-0.9,33.2,-1.6],'plume'),
        c('crest1',[-0.5,35.8,-0.6],[0.5,38,0.4],'plume'), c('crest2',[-0.5,35.8,0.6],[0.5,37.2,1.6],'plume'), beak]
    head=M.group(tag+'head',O([0,32,0]),hk)
    neck=M.group(tag+'neck',O([0,24,-1]),[c('neck',[-1,24,-2],[1,32.4,0],'tw_d'), head])
    bk=[c('body',[-5,14,-5],[5,25,5],'tw'), c('body_w',[-6,16,-4],[6,23,4],'tw'), c('body_f',[-4,16,-6],[4,23,6],'tw'),
        c('belly',[-4,13,-4],[4,14,4],'tw_d'), c('chest',[-3,17,-6.4],[3,22,-5.8],'tw_l'),
        c('tail1',[-2.5,19,6],[2.5,22,9],'plume'), c('tail2',[-1.5,21,8],[1.5,24,11],'plume'), c('tail3',[-0.8,23,10],[0.8,26.5,12.5],'tw_l'),
        c('wingf_l',[6,18,0],[6.6,20,4.5],'tw_l'), c('wingf_r',[-6.6,18,0],[-6,20,4.5],'tw_l')]
    if bag: bk+= [c('bag_strap',[-1.4,23.4,-3.2],[1.4,24.4,-0.6],'black'), c('bag',[-1.6,19.6,-7.6],[1.6,23.2,-6.3],'black'), c('bag_btn',[-0.4,21.6,-7.8],[0.4,22.4,-7.5],'steel')]
    body=M.group(tag+'body',O([0,15,0]),bk+[neck,arm(1),arm(-1)])
    return M.group(tag+'root',[0,0,0],[body,leg(1),leg(-1)])

def pyramid_beast(M, tag, s=1.0):
    """피라미드를 쌓는 것: 은회색 비늘 통 몸, 위쪽에 입 구멍 하나와 팔 하나, 아래에 뾰족한 꼬리. 눈·귀 없음. 키 약 30"""
    c=lambda name,fr,to,col,**f: M.cube(name,[v*s for v in fr],[v*s for v in to],col,**f)
    O=lambda v:[x*s for x in v]
    k=[c('tail_tip',[-1.2,0,-1.2],[1.2,2.5,1.2],'scale_d'), c('tail',[-3,2.5,-3],[3,6,3],'scale_d'),
       c('low',[-5,6,-5],[5,9,5],'scale'), c('cask',[-6.5,9,-6.5],[6.5,24,6.5],'scale'), c('bulge',[-7.3,12,-5.5],[7.3,21,5.5],'scale'),
       c('bulge2',[-5.5,12,-7.3],[5.5,21,7.3],'scale'), c('top',[-5.4,24,-5.4],[5.4,27,5.4],'scale'),
       c('mouth_rim',[-3.6,27,-3.6],[3.6,28,3.6],'scale_d'), c('mouth',[-2.6,27.6,-2.6],[2.6,28.1,2.6],'hole')]
    hand=M.group(tag+'hand',O([10.5,12,0]),[])
    fore=M.group(tag+'forearm',O([10.5,27,0]),[c('forearm',[9.5,13,-1.3],[11.5,27,1.3],'scale_d'),
          c('claw1',[9.3,10.6,-1.5],[10.1,13,-0.5],'scale'), c('claw2',[10.9,10.6,0.5],[11.7,13,1.5],'scale'), hand])
    arm=M.group(tag+'arm',O([6,25.5,0]),[c('upper',[5.4,24.4,-1.5],[11.5,27.6,1.5],'scale'), fore])
    return M.group(tag+'root',[0,0,0],k+[arm])

def brick(M, name, x, y, z, w=4, h=2, d=3):
    return M.cube(name,[x-w/2,y,z-d/2],[x+w/2,y+h,z+d/2],'brick')

def dream_beast(M, tag, s=1.0):
    """꿈을 보여 주는 것: 땅 구멍 속 검은 몸통 + 밧줄 같은 검은 팔 여섯 (끝은 보랏빛)"""
    c=lambda name,fr,to,col,**f: M.cube(name,[v*s for v in fr],[v*s for v in to],col,**f)
    O=lambda v:[x*s for x in v]
    k=[c('pit',[-9,0,-9],[9,1,9],'pit'), c('pit_in',[-7,0.6,-7],[7,1.4,7],'hole'), c('blob',[-4.5,1,-4.5],[4.5,6,4.5],'rope'), c('blob_t',[-3,6,-3],[3,8,3],'rope')]
    dirs=[(1,0),(-1,0),(0,1),(0,-1),(0.7,0.7),(-0.7,-0.7)]; hs=[20,17,22,15,18,21]
    for i,((dx,dz),h) in enumerate(zip(dirs,hs)):
        bx,bz=dx*3.5,dz*3.5; ox,oz=dx*6,dz*6
        seg=[c('a',[bx-0.9,5,bz-0.9],[bx+0.9,h*0.55,bz+0.9],'rope'),
             c('b',[min(bx,bx+ox*0.5)-0.8,h*0.55-0.8,min(bz,bz+oz*0.5)-0.8],[max(bx,bx+ox*0.5)+0.8,h*0.55+0.8,max(bz,bz+oz*0.5)+0.8],'rope'),
             c('c',[bx+ox*0.5-0.7,h*0.55,bz+oz*0.5-0.7],[bx+ox*0.5+0.7,h,bz+oz*0.5+0.7],'rope'),
             c('d',[min(bx+ox*0.5,bx+ox)-0.6,h-0.6,min(bz+oz*0.5,bz+oz)-0.6],[max(bx+ox*0.5,bx+ox)+0.6,h+0.6,max(bz+oz*0.5,bz+oz)+0.6],'rope'),
             c('tip',[bx+ox-0.9,h-2.6,bz+oz-0.9],[bx+ox+0.9,h-0.4,bz+oz+0.9],'rope_tip')]
        k.append(M.group(f'{tag}arm{i}',O([bx,5,bz]),seg))
    return M.group(tag+'root',[0,0,0],k)

def barrel_being(M, tag, s=1.0):
    """수레를 미는 것: 통 몸에 다리 넷·팔 넷, 머리 없음, 몸통 둘레에 눈이 빙 둘러 있고 윗면은 북처럼 팽팽함. 키 약 25"""
    c=lambda name,fr,to,col,**f: M.cube(name,[v*s for v in fr],[v*s for v in to],col,**f)
    O=lambda v:[x*s for x in v]
    k=[c('cask',[-6,8,-6],[6,24,6],'barrel'), c('bulge',[-7,11,-5],[7,21,5],'barrel'), c('bulge2',[-5,11,-7],[5,21,7],'barrel'),
       c('hoop1',[-7.2,12,-7.2],[7.2,13,7.2],'barrel_d'), c('hoop2',[-7.2,19,-7.2],[7.2,20,7.2],'barrel_d'),
       c('rim',[-6.3,24,-6.3],[6.3,25,6.3],'barrel_d'), c('drum',[-5.4,24.6,-5.4],[5.4,25.2,5.4],'drum')]
    for i,x in enumerate((-4,0,4)):     # 눈: 네 면에 세 개씩
        k+= [c(f'eye_n{i}',[x-1,15.4,-7.6],[x+1,17.4,-7.2],'eye_w'), c(f'pup_n{i}',[x-0.4,15.9,-7.8],[x+0.4,16.9,-7.5],'eye_k'),
             c(f'eye_s{i}',[x-1,15.4,7.2],[x+1,17.4,7.6],'eye_w'), c(f'pup_s{i}',[x-0.4,15.9,7.5],[x+0.4,16.9,7.8],'eye_k'),
             c(f'eye_e{i}',[7.2,15.4,x-1],[7.6,17.4,x+1],'eye_w'), c(f'pup_e{i}',[7.5,15.9,x-0.4],[7.8,16.9,x+0.4],'eye_k'),
             c(f'eye_w{i}',[-7.6,15.4,x-1],[-7.2,17.4,x+1],'eye_w'), c(f'pup_w{i}',[-7.8,15.9,x-0.4],[-7.5,16.9,x+0.4],'eye_k')]
    legs=[]
    for nm,(x,z) in {'leg_fl':(4,-4),'leg_fr':(-4,-4),'leg_bl':(4,4),'leg_br':(-4,4)}.items():
        legs.append(M.group(tag+nm,O([x,8,z]),[c('leg',[x-1,1,z-1],[x+1,8,z+1],'barrel_d'), c('foot',[x-1.5,0,z-2],[x+1.5,1,z+1.5],'barrel_d')]))
    arms=[]
    for nm,x in (('arm_fl',3.5),('arm_fr',-3.5)):   # 앞 팔 둘: 앞으로 뻗어 수레를 밂
        arms.append(M.group(tag+nm,O([x,13,-6]),[c('arm',[x-0.7,12.3,-12],[x+0.7,13.7,-6],'barrel_d'), c('nip1',[x-0.9,12.9,-13.6],[x-0.2,13.6,-12],'drum'),
                    c('nip2',[x+0.2,12.4,-13.6],[x+0.9,13.1,-12],'drum'), M.group(tag+nm+'_hand',O([x,13,-12.5]),[])]))
    for nm,sx in (('arm_sl',1),('arm_sr',-1)):      # 옆 팔 둘: 아래로 늘어뜨림
        x0,x1=(7,8.4) if sx>0 else (-8.4,-7)
        arms.append(M.group(tag+nm,O([(x0+x1)/2,21,0]),[c('arm',[x0,10,-0.7],[x1,21,0.7],'barrel_d'), c('nip',[x0-0.2,8.4,-0.9],[x1+0.2,10,0.9],'drum')]))
    body=M.group(tag+'body',O([0,8,0]),k+arms)
    return M.group(tag+'root',[0,0,0],[body]+legs)

def cart(M, tag, s=1.0, load=None):
    """구릿빛 손수레 (앞 = -z, 손잡이는 +z 쪽).  load: None / 'rubble'(돌·모래·풀)"""
    c=lambda name,fr,to,col,**f: M.cube(name,[v*s for v in fr],[v*s for v in to],col,**f)
    k=[c('floor',[-5,3,-7],[5,4,5],'copper_d'), c('wall_l',[5,4,-7],[5.8,9,5],'copper'), c('wall_r',[-5.8,4,-7],[-5,9,5],'copper'),
       c('wall_f',[-5.8,4,-7.8],[5.8,9,-7],'copper'), c('wall_b',[-5.8,4,5],[5.8,9,5.8],'copper'),
       c('wheel_l',[5.8,0,-3.5],[7,5,1.5],'copper_d'), c('wheel_r',[-7,0,-3.5],[-5.8,5,1.5],'copper_d'),
       c('handle_l',[3,8,5.8],[4,9,9.5],'copper_d'), c('handle_r',[-4,8,5.8],[-3,9,9.5],'copper_d'), c('handle',[-4,8,9.5],[4,9,10.3],'copper_d')]
    if load=='rubble':     # 짐은 묶음(tag_load) → 쏟은 뒤 안 보이게 할 수 있음
        k+= [M.group(tag+'load',[0,4*s,0],[c('sandload',[-5,4,-7],[5,8.4,5],'sand'), c('rock1',[-3,8,-4],[0,10.5,-1],'steel_d'), c('rock2',[1,8,0],[4,10,3],'scale_d'), c('weed',[-2,8,1],[-1,12,2],'tw_d')])]
    return M.group(tag+'root',[0,0,0],k)
