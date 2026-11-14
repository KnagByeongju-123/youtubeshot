"""《사라진 강이 피라미드를 세웠다》 블록 장면 → 연재/피라미드강/장면/<세트>.bbmodel + 세트정보.json (시간 = 영상 시간)"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 블록인물 import *
from 모아이_장면 import ropes, walk_cycle
OUT=sys.argv[1] if len(sys.argv)>1 else '/home/user/youtubeshot/연재/피라미드강/장면'
os.makedirs(OUT,exist_ok=True)
L=290.0

def pal(M):
    egypt_palette(M)
    M.swatch('sand',(222,196,140),10); M.swatch('sand_d',(205,178,122),10); M.swatch('field',(110,160,70),12); M.swatch('field2',(140,175,80),12)
    M.swatch('water',lambda x,y:(55,120,175) if (x+2*y)%7 else (90,155,200),6); M.swatch('rockc',(190,180,160),12); M.swatch('rockd',(150,135,115),12)
    M.swatch('dark',(40,34,30),6); M.swatch('palmt',lambda x,y:(120,90,60) if y%4 else (95,70,45),5); M.swatch('palml',(80,140,60),14)
    M.swatch('papyrus_txt',lambda x,y:(60,40,30) if (y%3==1 and 2<x<14) else (225,210,160),2); M.swatch('steel',(120,125,135),6); M.swatch('redst',(170,90,70),10)

def tiles(M,x0,x1,z0,z1,cols=('sand','sand_d'),t=256,y=0):
    out=[]; xs=list(range(x0,x1,t)); zs=list(range(z0,z1,t))
    for i,x in enumerate(xs):
        for j,z in enumerate(zs):
            out.append(M.cube('g',[x,y-16,z],[min(x+t,x1),y,min(z+t,z1)],cols[(i+j)%2]))
    return out

def hide_show(A,g,windows,axis='all'):
    """windows: [(t_on,t_off),...] 보이는 구간. 그 밖은 크기 0"""
    pts=[(0,(0,0,0))]
    for a,b in windows: pts+= [(max(0,a-0.01),(0,0,0)),(a,(1,1,1)),(b,(1,1,1)),(b+0.01,(0,0,0))]
    A.add(g,'scale',pts)

def date_palm(M,tag,x,z,h=70):
    k=[M.cube('t',[x-3,0,z-3],[x+3,h,z+3],'palmt')]
    for dx,dz in [(1,0),(-1,0),(0,1),(0,-1)]:
        k.append(M.cube('l',[x+min(0,dx*26)-(3 if dx==0 else 0),h-5,z+min(0,dz*26)-(3 if dz==0 else 0)],[x+max(0,dx*26)+(3 if dx==0 else 0),h,z+max(0,dz*26)+(3 if dz==0 else 0)],'palml'))
    return M.group(tag,[x,0,z],k)

def wx(dx): return -dx      # 위치 움직임의 x 는 반대로 적용됨

# =====================================================================
#  세트 G : 기자 + 아흐라마트 강 (오늘 / 옛날)
# =====================================================================
def set_G():
    M=Model(256); pal(M); A=Anim(L); top=[]
    top.append(M.cube('base',[-3000,-60,-4000],[3000,-20,3000],'sand_d'))
    top+= tiles(M,-1400,-64,-2600,1200)                       # 서쪽 사막(기자)
    top+= tiles(M,64,900,-2600,1200,cols=('field','field2'))   # 동쪽 밭
    top+= tiles(M,1000,1400,-2600,1200)
    top.append(M.cube('nile_today',[900,-20,-2600],[1000,-3,1200],'water'))    # 오늘의 나일강 (멀리 동쪽)
    # 옛 강(물) / 오늘(모래·밭으로 메워짐)
    water=M.group('river',[0,-16,0],[M.cube('w',[-64,-16,-2600],[64,-3,1200],'water')]); top.append(water)
    fill=M.group('riverfill',[0,-16,0],[M.cube('f',[-64,-16,-2600],[0,0.4,1200],'sand'),M.cube('f2',[0,-16,-2600],[64,0.4,1200],'field')]); top.append(fill)
    dunes=M.group('dunes',[0,0,0],[M.cube('d',[-60+(i%2)*40,-6,-400+i*170],[-10+(i%2)*40,6+(i%3)*4,-300+i*170],'sand') for i in range(8)]); top.append(dunes)
    TODAY=[(0,29.8),(104.5,138.2)]; PAST=[(29.8,104.5),(138.2,L)]
    hide_show(A,fill,TODAY+[(237.5,243.0)]); hide_show(A,water,PAST)
    A.add(water,'scale',[(226.9,(1,1,1)),(237.6,(1,0.05,1)),(243.0,(1,0.05,1)),(243.01,(1,1,1))])  # 마름 (덮어쓰기)
    A.add(fill,'scale',[(138.2,(1,1,1)),(141.0,(0,0,0))])
    hide_show(A,dunes,[(227.0,243.0)]); A.add(dunes,'scale',[(227.0,(1,0.05,1)),(237.5,(1,1,1))])
    # 피라미드들 (북 → 남 = +z → -z)
    gp=pyramid(M,'gp',-560,0,base=460,step=12); top.append(gp)
    top.append(pyramid(M,'menk',-520,420,base=200,step=12))
    kh=pyramid(M,'khafre',-560,-560,base=380,step=12,layers=10,casing=False); top.append(kh)
    top.append(M.group('ramp',[0,0,0],[M.cube('ramp',[-600,0,-1050+i*30],[-520,(i+1)*11.4,-1020+i*30],'rockd') for i in range(10)]))
    top.append(pyramid(M,'abusir',-420,-1200,base=240,step=12))
    top.append(pyramid(M,'saqqara',-450,-1700,base=300,step=26))
    top.append(pyramid(M,'dahshur',-500,-2250,base=380,step=12))
    # 둑길 + 계곡 신전(항구)
    top+= [M.cube('causeway',[-330,0,-12],[-150,5,12],'lime_d'), M.cube('temple',[-150,0,-40],[-90,34,40],'lime_d',up='lime'),
           M.cube('dock',[-90,0,-50],[-60,4,50],'lime_d')]
    for i,(x,z) in enumerate([(-200,140),(-140,-160),(-260,300),(-200,-420),(320,360),(380,-300)]):
        top.append(date_palm(M,f'dp{i}',x,z,64+(i%3)*10))
    # 메레르의 배 (강 위, -z 쪽으로 내려와 항구에 닿음)
    b1=boat(M,'b1_'); mer=person(M,'mer_','merer',1.0,'linen'); move(M,mer,0,9,10); b1['children'].append(mer)
    for j,zz in enumerate([-30,40]):
        r=person(M,f'r{j}_','worker',1.0,'linen'); move(M,r,(-1)**j*10,9,zz); b1['children'].append(r)
        A.add(find(r,f'r{j}_arm_right'),'rotation',[(0,(0,0,0))]+[(t,(-60 if k%2 else -20,0,0)) for k,t in enumerate([x*0.8 for x in range(0,360)])],'catmullrom')
    top.append(b1)
    # 배 위치: 81.5~87.9 강을 따라 내려옴 → 87.9 항구 / 268.8 다시 닿음
    A.add(b1,'position',[(0,(wx(0),0,900)),(81.5,(wx(0),0,700)),(88.0,(wx(-30),0,60)),(104.5,(wx(-30),0,60)),
                          (164.4,(wx(-30),0,500)),(176,(wx(-30),0,60)),(188.3,(wx(-30),0,60)),
                          (266.8,(wx(-30),0,400)),(272.4,(wx(-30),0,60)),(L,(wx(-30),0,60))])
    hide_show(A,b1,PAST)
    for i,(x,z) in enumerate([(30,-500),(-20,-1300)]):
        bb=boat(M,f'bx{i}_'); move(M,bb,x,0,z); top.append(bb); hide_show(A,bb,PAST)
        A.add(bb,'position',[(0,(0,0,0)),(L,(0,0,-300 if i==0 else 250))])
    # 앙크하프 (항구)
    ank=person(M,'ank_','ankhhaf',1.05,'linen'); move(M,ank,-72,4,-40); ank['rotation']=[0,90,0]; top.append(ank)
    hide_show(A,ank,[(87.0,104.5)])
    # 짐 내리는 일꾼 (항구, 176~188 / 272~)
    for j in range(3):
        w=person(M,f'u{j}_',['worker','worker2','worker'][j],1.0,'linen' if j!=1 else 'linen2'); move(M,w,-80,4,-30+j*30); w['rotation']=[0,90,0]; top.append(w)
        hide_show(A,w,[(164.4,216.4),(266.8,L)])
        for arm in ('arm_left','arm_right'):
            A.add(find(w,f'u{j}_{arm}'),'rotation',[(0,(0,0,0))]+[(t,(-90 if k%2 else -40,0,0)) for k,t in enumerate([176+x*0.7 for x in range(18)]+[272+x*0.7 for x in range(20)])],'catmullrom')
    # 썰매 + 돌 + 끄는 사람 6 + 물 붓는 사람 (둑길 위, 항구 → 피라미드 = 세계 -x)
    # 상자 좌표를 썰매 자리로
    sledg=M.group('sled',[-140,5,0],[]); 
    cubes=[M.cube('rail_l',[-156,5,-10],[-124,9,-6],'wood'),M.cube('rail_r',[-156,5,6],[-124,9,10],'wood'),M.cube('blk',[-151,9,-9],[-129,27,9],'lime')]
    sledg['children']=cubes+[Model.group('sl_front',[-156,8,0],[])]; top.append(sledg)
    def sled_x(t):   # 세계 x 이동량 (항구 쪽 → 피라미드 쪽, 음수)
        if t<190.3: return 0
        return -min(90,(t-190.3)*3.6)
    times=[190.3+i*1.0 for i in range(27)]
    A.add(sledg,'position',[(0,(0,0,0)),(190.3,(0,0,0))]+[(t,(wx(sled_x(t)),0,0)) for t in times])
    hide_show(A,sledg,[(188.3,216.4)])
    pul=[]
    for j in range(6):
        x=-180-(j//2)*22; z=-9 if j%2==0 else 9
        g=person(M,f'p{j}_',['worker','worker2'][j%2],1.0,['linen','linen2'][j%2]); move(M,g,x,5,z); g['rotation']=[0,-90,0]; top.append(g); pul.append(g)
        A.add(g,'position',[(0,(0,0,0)),(190.3,(0,0,0))]+[(t,(wx(sled_x(t)),0,0)) for t in times])
        walk_cycle(A,g,190.3,216.4,amp=22,period=1.4); hide_show(A,g,[(188.3,216.4)])
        A.add(find(g,f'p{j}_body'),'rotation',[(0,(0,0,0)),(190.3,(-16,0,0)),(216.4,(-16,0,0))])
        for arm in ('arm_left','arm_right'): A.add(find(g,f'p{j}_{arm}'),'rotation',[(0,(0,0,0)),(190.3,(-150,0,0)),(216.4,(-150,0,0))])
    wp=person(M,'wp_','worker2',0.95,'linen2'); move(M,wp,-166,5,-20); wp['rotation']=[0,-90,0]
    find(wp,'wp_arm_right')['children'].append(M.cube('jar',[-169,9,-26],[-163,17,-20],'jar'))
    top.append(wp); A.add(wp,'position',[(0,(0,0,0)),(190.3,(0,0,0))]+[(t,(wx(sled_x(t)),0,0)) for t in times])
    A.add(find(wp,'wp_arm_right'),'rotation',[(0,(0,0,0)),(194,(0,0,0)),(195,(-80,0,0)),(216.4,(-80,0,0))]); hide_show(A,wp,[(188.3,216.4)])
    wet=M.group('wet',[-166,5,-14],[M.cube('wet',[-176,5.1,-14],[-160,5.4,14],'water')]); top.append(wet)
    A.add(wet,'position',[(0,(0,0,0)),(190.3,(0,0,0))]+[(t,(wx(sled_x(t)),0,0)) for t in times]); hide_show(A,wet,[(195,216.4)])
    # 피라미드 쌓기 (243~266.8): 경사로를 따라 돌을 끌어 올림 (+z, 위로)
    def ry(z): return max(0,(z+1050)/30*11.4)
    zs=[-1040+i*10 for i in range(25)]; tt=[243+i*(23.0/24) for i in range(25)]
    rb=M.group('rblk',[-560,0,-1040],[M.cube('b',[-570,0,-1049],[-550,16,-1031],'lime_d')]); top.append(rb)
    A.add(rb,'position',[(0,(0,0,0))]+[(t,(0,ry(z),z+1040)) for t,z in zip(tt,zs)]); hide_show(A,rb,[(243,266.8)])
    for j,dx in enumerate([-12,12,0]):
        g=person(M,f'rw{j}_',['worker','worker2','worker'][j],1.0,'linen'); move(M,g,-560+dx,0,-1040+(26 if j<2 else 40)); g['rotation']=[0,180,0]; top.append(g)
        z0=-1040+(26 if j<2 else 40)
        A.add(g,'position',[(0,(0,0,0))]+[(t,(0,ry(z+(z0+1040)),z+1040)) for t,z in zip(tt,zs)]); hide_show(A,g,[(243,266.8)])
        walk_cycle(A,g,243,266.8,amp=22,period=1.2)
        if j<2: A.add(find(g,f'rw{j}_body'),'rotation',[(0,(0,0,0)),(243,(-14,0,0)),(266.8,(-14,0,0))])
    # 땅속 조사 (133~140): 시추 탑
    dr=M.group('drill',[120,0,300],[M.cube('tw',[110,0,290],[130,90,310],'steel'),M.cube('core',[116,-40,296],[124,0,304],'redst')]); top.append(dr)
    hide_show(A,dr,[(133.0,141.0)])
    top.append(ropes(M,3))
    A.bake(top); M.save(f'{OUT}/G_기자.bbmodel',top,[A.json()],name='G')
    return {'ropes':[['sl_front','p4_hand_r'],['sl_front','p5_hand_r'],['sl_front','p2_hand_r']]}

# =====================================================================
#  세트 T : 투라 채석장 (강 동쪽 기슭) + 메레르 소개
# =====================================================================
def set_T():
    M=Model(256); pal(M); A=Anim(L); top=[M.cube('base',[-3000,-60,-3000],[3000,-20,3000],'sand_d')]
    top.append(M.cube('river',[-400,-16,-1200],[-60,-3,1200],'water'))
    top+= tiles(M,-60,700,-1200,1200,t=192)
    for i in range(5):  # 하얀 석회암 절벽 (+x 로 올라감)
        x0=160+i*70; top.append(M.cube('cliff',[x0,0,-500],[x0+70,60+i*40,500],'lime' if i%2 else 'lime_d',up='rockc'))
    for i,(x,z) in enumerate([(150,-90),(150,-40),(150,20)]):
        top.append(M.cube('cut',[x,0,z],[x+10,40,z+30],'lime_d'))
    bt=boat(M,'bt_',cargo=1); move(M,bt,-140,0,0); top.append(bt)
    A.add(bt,'position',[(0,(0,0,0)),(76.8,(0,0,0)),(81.5,(0,0,-260))],'catmullrom')
    mer=person(M,'mer_','merer',1.0,'linen'); move(M,mer,0,0,-60); mer['rotation']=[0,-60,0]; top.append(mer)
    A.add(find(mer,'mer_arm_left'),'rotation',[(0,(0,0,0)),(58,(0,0,0)),(59,(-100,0,20)),(62,(-100,0,20)),(63,(0,0,0))],'catmullrom')
    A.add(find(mer,'mer_head'),'rotation',[(0,(0,0,0)),(60.3,(0,0,0)),(61,(-8,0,0)),(62,(4,0,0)),(63,(0,0,0))],'catmullrom')
    # 석공 (절벽 앞에서 돌 깨기)
    for j,(x,z) in enumerate([(130,-80),(130,-10),(130,50)]):
        g=person(M,f'q{j}_',['worker','worker2','worker'][j],1.0,'linen',tool='axe'); move(M,g,x,0,z); g['rotation']=[0,90,0]; top.append(g)
        pts=[(0,(-40,0,0))]; t=52+j*0.2; up=True
        while t<L: pts.append((t,(-140 if up else -50,0,0))); up=not up; t+=0.34
        A.add(find(g,f'q{j}_arm_right'),'rotation',pts,'catmullrom')
    # 돌 나르기 (71.2~76.8): 일꾼 2명이 돌을 강가 배로 (세계 -x)
    blk=M.group('blk',[20,0,40],[M.cube('b',[10,0,31],[30,16,49],'lime')]); top.append(blk)
    A.add(blk,'position',[(0,(0,0,0)),(71.5,(0,0,0)),(76.0,(wx(-150),9,-40)),(76.8,(wx(-150),9,-40)),(81.5,(wx(-150),9,-300))])
    for j,zz in enumerate([26,54]):
        g=person(M,f'c{j}_','worker' if j else 'worker2',1.0,'linen'); move(M,g,32,0,zz); g['rotation']=[0,-90,0]; top.append(g)
        A.add(g,'position',[(0,(0,0,0)),(71.5,(0,0,0)),(76.0,(wx(-120),0,-30)),(L,(wx(-120),0,-30))]); walk_cycle(A,g,71.5,76.0,amp=24,period=0.9)
        for arm in ('arm_left','arm_right'): A.add(find(g,f'c{j}_{arm}'),'rotation',[(0,(0,0,0)),(71.2,(-70,0,0)),(76.0,(-70,0,0)),(76.5,(0,0,0))])
    for i,(x,z) in enumerate([(60,-300),(90,260),(-30,400)]): top.append(date_palm(M,f'tp{i}',x,z,66))
    A.bake(top); M.save(f'{OUT}/T_투라.bbmodel',top,[A.json()],name='T'); return {'ropes':[]}

# =====================================================================
#  세트 C : 와디 알자르프 동굴 (홍해 바닷가)
# =====================================================================
def set_C():
    M=Model(256); pal(M); A=Anim(L); top=[M.cube('sea',[-3000,-40,-3000],[3000,-4,-120],'water'),M.cube('base',[-3000,-60,-120],[3000,-20,3000],'sand_d')]
    top+= tiles(M,-700,700,-120,700,t=200)
    # 바위 언덕 + 동굴 입구(가운데 비움)
    top+= [M.cube('hl',[-320,0,60],[-36,170,420],'rockd',up='rockc'),M.cube('hr',[36,0,60],[320,170,420],'rockd',up='rockc'),
           M.cube('htop',[-36,64,60],[36,170,420],'rockd',up='rockc'),M.cube('floor',[-36,0,60],[36,1,300],'dark'),M.cube('back',[-36,0,300],[36,64,320],'dark')]
    for i,(x,z) in enumerate([(-20,200),(-6,214),(10,206),(22,190)]):
        top.append(M.cube('roll',[x-4,1,z-12],[x+4,9,z+12],'papyrus'))
    top.append(M.cube('sheet',[-14,1.2,150],[14,1.6,180],'papyrus_txt'))
    for i,(x,z) in enumerate([(-450,-60),(380,-40),(500,200)]): top.append(M.cube('rock',[x,0,z],[x+70,40+i*10,z+60],'rockc'))
    A.bake(top); M.save(f'{OUT}/C_동굴.bbmodel',top,[A.json()],name='C'); return {'ropes':[]}

if __name__=='__main__':
    info={'G':set_G(),'T':set_T(),'C':set_C()}
    json.dump(info,open(f'{OUT}/세트정보.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
    for f in sorted(os.listdir(OUT)):
        if f.endswith('.bbmodel'): print(f, len(json.load(open(f'{OUT}/{f}',encoding='utf-8'))['elements']),'cubes')
