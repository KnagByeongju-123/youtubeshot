"""《빈 밥그릇》 블록 부품: 꼬마·아빠·강아지·파란 밥그릇·이삿짐 트럭·상자.
   블록인물.py 의 Model·move·Anim·find 를 그대로 씀.  앞 = -z.
   크기 기준: 아빠 키 32, 꼬마 약 22 (s=0.7), 강아지 등 높이 약 9"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 블록인물 import Model, move, anchor, Anim, find, U

SKIN=(240,200,165); HAIR=(32,28,28)

def palette(M):
    M.swatch('skin',SKIN,3); M.swatch('skin_d',(220,178,140),3); M.swatch('hair',HAIR,3)
    # 꼬마: 빨간 모자, 노란 비옷, 초록 바지, 빨간 장화
    M.swatch('cap',(205,45,40),5); M.swatch('cap_d',(165,35,30),4)
    M.swatch('coat',(250,205,40),5); M.swatch('coat_d',(215,170,25),4)
    M.swatch('pants_g',(70,140,75),5); M.swatch('boot',(185,40,35),4)
    # 아빠: 남색 셔츠, 회색 바지, 갈색 신발
    M.swatch('shirt',(45,65,115),5); M.swatch('shirt_d',(35,50,90),4)
    M.swatch('pants',(120,120,125),5); M.swatch('shoe',(90,60,40),4)
    # 강아지: 흰 몸, 갈색 귀·등 무늬, 검은 코
    M.swatch('dog',(245,242,235),4); M.swatch('dog_d',(225,220,210),4)
    M.swatch('dog_b',(165,105,60),5); M.swatch('nose',(30,25,25),2); M.swatch('tongue',(230,110,120),3)
    # 소품
    M.swatch('bowl',(50,120,210),4); M.swatch('bowl_d',(35,90,165),3); M.swatch('food',(185,130,70),10)
    M.swatch('truck',(70,140,200),5); M.swatch('truck_d',(50,105,155),4); M.swatch('glass',(170,215,235),3)
    M.swatch('tire',(35,35,38),3); M.swatch('hub',(170,170,175),3); M.swatch('light',(255,235,150),3)
    M.swatch('box',(200,155,95),8); M.swatch('box_t',(170,125,70),5)
    M.swatch('white',(250,250,250),2)
    def face(name,cheek=False,brow=HAIR):
        def fn(d,x,y):
            d.rectangle([x,y,x+15,y+15],fill=SKIN)
            for ex in (3,9):
                d.rectangle([x+ex,y+6,x+ex+3,y+9],fill=(255,255,255)); d.rectangle([x+ex+1,y+6,x+ex+2,y+9],fill=(25,20,20))
                d.rectangle([x+ex,y+5,x+ex+3,y+5],fill=brow)
            d.rectangle([x+7,y+10,x+8,y+10],fill=(215,165,130))
            d.rectangle([x+6,y+12,x+9,y+12],fill=(175,85,75))
            if cheek: d.rectangle([x+2,y+11,x+3,y+11],fill=(245,150,135)); d.rectangle([x+12,y+11,x+13,y+11],fill=(245,150,135))
        M.paint(name,fn)
    face('f_kid',cheek=True); face('f_dad')
    def dogface(d,x,y):
        d.rectangle([x,y,x+15,y+15],fill=(245,242,235))
        for ex in (3,10):
            d.rectangle([x+ex,y+5,x+ex+2,y+7],fill=(25,20,20)); d.point((x+ex,y+5),fill=(255,255,255))
    M.paint('f_dog',dogface)

def person(M, tag, kind='kid', s=1.0):
    """kind: kid(꼬마) / dad(아빠).  키 32*s.  손 끝 묶음 hand_l / hand_r"""
    c=lambda name,fr,to,col,**f: M.cube(name,[v*s for v in fr],[v*s for v in to],col,**f)
    O=lambda v:[x*s for x in v]
    if kind=='kid': top,top_d,pt,sh,fc='coat','coat_d','pants_g','boot','f_kid'
    else:           top,top_d,pt,sh,fc='shirt','shirt_d','pants','shoe','f_dad'
    legL=M.group(tag+'leg_left',O([2,12,0]),[c('leg',[0,2,-2],[4,12,2],pt), c('shoe',[-0.2,0,-2.8],[4.2,2.4 if kind=='kid' else 1.6,2.2],sh)])
    legR=M.group(tag+'leg_right',O([-2,12,0]),[c('leg',[-4,2,-2],[0,12,2],pt), c('shoe',[-4.2,0,-2.8],[0.2,2.4 if kind=='kid' else 1.6,2.2],sh)])
    armL_k=[c('sleeve',[4,15,-2.2],[8.2,24,2.2],top), c('hand',[4.6,12,-1.6],[7.6,15,1.6],'skin')]
    armR_k=[c('sleeve',[-8.2,15,-2.2],[-4,24,2.2],top), c('hand',[-7.6,12,-1.6],[-4.6,15,1.6],'skin')]
    hl=M.group(tag+'hand_l',O([6,12.5,0]),[]); hr=M.group(tag+'hand_r',O([-6,12.5,0]),[])
    armL=M.group(tag+'arm_left',O([6,22,0]),armL_k+[hl]); armR=M.group(tag+'arm_right',O([-6,22,0]),armR_k+[hr])
    body=[c('torso',[-4.2,12,-2.2],[4.2,24,2.2],top)]
    if kind=='kid':   # 비옷: 엉덩이 아래까지 + 단추
        body+= [c('coat_low',[-4.5,9,-2.5],[4.5,13,2.5],top), c('btn1',[-0.6,20,-2.5],[0.6,21.2,-2.3],'coat_d'),
                c('btn2',[-0.6,16,-2.5],[0.6,17.2,-2.3],'coat_d'), c('btn3',[-0.6,12,-2.7],[0.6,13.2,-2.5],'coat_d')]
    else:             # 셔츠 깃 + 허리띠
        body+= [c('collar',[-2,22.6,-2.5],[2,24,-2.3],'white'), c('belt',[-4.4,12,-2.4],[4.4,13.2,2.4],'shoe')]
    hk=[c('head',[-4,24,-4],[4,32,4],'skin',north=fc,up='hair',south='hair'),
        c('hair_back',[-4.2,25.5,1.2],[4.2,32.2,4.2],'hair'), c('hair_top',[-4.2,31.2,-4.2],[4.2,32.4,4.2],'hair'),
        c('hair_side_l',[3.9,28,-1],[4.2,32,4],'hair'), c('hair_side_r',[-4.2,28,-1],[-3.9,32,4],'hair')]
    if kind=='kid':   # 빨간 야구 모자 (챙은 앞으로)
        hk+= [c('cap',[-4.4,30,-4.4],[4.4,33.4,4.4],'cap'), c('cap_brim',[-4.2,30,-8],[4.2,30.8,-4.4],'cap_d')]
    head=M.group(tag+'head',O([0,24,0]),hk)
    bod=M.group(tag+'body',O([0,12,0]),body+[head,armL,armR])
    return M.group(tag+'root',[0,0,0],[bod,legL,legR])

def dog(M, tag, s=1.0, with_bowl=False):
    """강아지 (앞 = -z).  묶음: body / head(입 = mouth 점) / leg_fl·fr·bl·br / tail / ear_l·ear_r"""
    c=lambda name,fr,to,col,**f: M.cube(name,[v*s for v in fr],[v*s for v in to],col,**f)
    O=lambda v:[x*s for x in v]
    def leg(n,x,z):
        return M.group(tag+n,O([x,4,z]),[c('leg',[x-1.2,0,z-1.2],[x+1.2,4,z+1.2],'dog',down='dog_d'),
                                         c('paw',[x-1.4,0,z-1.6],[x+1.4,0.9,z+1.2],'dog_d')])
    legs=[leg('leg_fl',2,-4.5),leg('leg_fr',-2,-4.5),leg('leg_bl',2,4.5),leg('leg_br',-2,4.5)]
    bk=[c('torso',[-3.2,4,-6.5],[3.2,9.5,6.5],'dog',down='dog_d'), c('spot',[-3.3,7.5,0],[3.3,9.7,5],'dog_b'),
        c('chest',[-2.6,6,-8],[2.6,10.5,-5],'dog')]
    tail=M.group(tag+'tail',O([0,8.5,6.5]),[c('tail',[-0.7,8.5,6.5],[0.7,12.5,7.9],'dog')])
    # 늘어진 귀: 머리 양옆에 붙어 아래로
    earL=M.group(tag+'ear_l',O([3.2,15.5,-9]),[c('ear',[3,10.5,-10],[3.9,15.5,-7.5],'dog_b')])      # 갈색 귀(한쪽)
    earR=M.group(tag+'ear_r',O([-3.2,15.5,-9]),[c('ear',[-3.9,10.5,-10],[-3,15.5,-7.5],'dog_d')])
    hk=[c('head',[-3,10,-12],[3,16,-6.5],'dog',north='f_dog'), c('muzzle',[-1.8,10.2,-14.6],[1.8,12.8,-12],'dog'),
        c('nose',[-0.8,11.4,-15],[0.8,12.5,-14.4],'nose'), c('patch',[1.5,13,-12.1],[3.1,16.1,-8],'dog_b')]
    mouth=M.group(tag+'mouth',O([0,10.6,-14.8]),[])
    if with_bowl:   # 입에 문 그릇 (묶음 mbowl: 크기 0 으로 숨겼다 보였다)
        hk+= [M.group(tag+'mbowl',O([0,10.4,-15.9]),bowl_cubes(M,0,9.4*s,-15.9*s,0.7*s,food=False))]
    head=M.group(tag+'head',O([0,11,-7]),hk+[earL,earR,mouth])
    body=M.group(tag+'body',O([0,6.5,0]),bk+[head,tail])
    return M.group(tag+'root',[0,0,0],[body]+legs)

def bowl_cubes(M, x, y, z, s=1.0, food=True):
    c=lambda n,fr,to,col: M.cube(n,[x+fr[0]*s,y+fr[1]*s,z+fr[2]*s],[x+to[0]*s,y+to[1]*s,z+to[2]*s],col)
    k=[c('bowl_base',[-2.5,0,-2.5],[2.5,0.6,2.5],'bowl_d'), c('bowl_n',[-3.5,0.6,-3.5],[3.5,3,-2.7],'bowl'),
       c('bowl_s',[-3.5,0.6,2.7],[3.5,3,3.5],'bowl'), c('bowl_e',[2.7,0.6,-2.7],[3.5,3,2.7],'bowl'),
       c('bowl_w',[-3.5,0.6,-2.7],[-2.7,3,2.7],'bowl'), c('bowl_in',[-2.7,0.6,-2.7],[2.7,1,2.7],'bowl_d')]
    if food: k.append(c('food',[-2.6,1,-2.6],[2.6,2.4,2.6],'food'))
    return k

def bowl(M, tag, s=1.0, food=True):
    """파란 밥그릇 (폭 7, 높이 3).  food: 사료 위 칸 (빈 그릇이면 False → 이름 food 상자 크기 0 으로도 숨길 수 있음)"""
    return M.group(tag+'root',[0,0,0],bowl_cubes(M,0,0,0,s,food))

def box(M, tag, w=10, h=8, d=10):
    k=[M.cube('box',[-w/2,0,-d/2],[w/2,h,d/2],'box',up='box_t'), M.cube('tape',[-1,h,-d/2-0.05],[1,h+0.1,d/2+0.05],'box_t')]
    return M.group(tag+'root',[0,0,0],k)

def truck(M, tag):
    """작은 파란 트럭 (앞 = -z).  길이 약 70, 운전칸(앞) + 짐칸(뒤, 상자 3개).  옆 문 묶음 door_l (+x 쪽, 꼬마 자리)"""
    k=[M.cube('chassis',[-13,5,-35],[13,9,35],'truck_d'),
       # 운전칸: 아래 몸통 + 기둥 4개 + 지붕 (창문은 뚫려 있어 안의 사람이 보임)
       M.cube('cab_low',[-13,9,-35],[13,19,-12],'truck'), M.cube('cab_roof',[-13.4,29,-35.4],[13.4,31.5,-12],'truck_d'),
       M.cube('cab_back',[-13,19,-14],[13,29,-12],'truck'), M.cube('back_window',[-9,21,-12.1],[9,27,-11.7],'glass'),
       M.cube('pillar_fl',[11,19,-35],[13,29,-33],'truck'), M.cube('pillar_fr',[-13,19,-35],[-11,29,-33],'truck'),
       M.cube('pillar_m',[-1,19,-35],[1,29,-34],'truck_d'),
       M.cube('seat',[-11,9,-22],[11,15,-15],'tire'), M.cube('dash',[-11,15,-34],[11,18,-31],'tire'),
       M.cube('light_l',[7,11,-35.4],[11,14,-35],'light'), M.cube('light_r',[-11,11,-35.4],[-7,14,-35],'light'),
       M.cube('bumper',[-13.5,5,-36.5],[13.5,8,-35],'tire'),
       M.cube('bed',[-13,9,-11],[13,10,35],'truck_d'),
       M.cube('bed_l',[12,10,-11],[13,17,35],'truck'), M.cube('bed_r',[-13,10,-11],[-12,17,35],'truck'),
       M.cube('bed_back',[-13,10,34],[13,17,35],'truck'), M.cube('bed_front',[-13,10,-12],[13,19,-11],'truck')]
    for z in (-24,22):
        for x,(a,b) in ((1,(12.5,15.5)),(-1,(-15.5,-12.5))):
            k+= [M.cube('tire',[a,0,z-5],[b,10,z+5],'tire',east='hub' if x>0 else 'tire',west='hub' if x<0 else 'tire')]
    # 짐칸 상자
    for i,(x,z,w,h) in enumerate([(-6,0,10,9),(5,2,9,8),(-4,18,11,10),(5,20,8,7)]):
        k+= [M.cube('cargo',[x-w/2,10,z-w/2],[x+w/2,10+h,z+w/2],'box',up='box_t')]
    door=M.group(tag+'door_l',[13,9,-30],[M.cube('door',[13,9,-30],[13.4,19,-17],'truck'),
                                         M.cube('handle',[13.4,16,-21],[13.9,17,-19],'tire')])
    seat=M.group(tag+'seat_l',[6,12,-23],[])     # 꼬마가 앉을 자리 (조수석, +x)
    seatd=M.group(tag+'seat_r',[-6,12,-23],[])   # 아빠 운전석
    return M.group(tag+'root',[0,0,0],k+[door,seat,seatd])
