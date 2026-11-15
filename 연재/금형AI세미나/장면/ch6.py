import sys,os; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from s3d import *
T,E,DUR,cs=chapter(6)
sc=setup(texture=True)
floor(extent=2400)
t=0.6
IT=json.load(open('/home/user/mold_sold/parts/TEST_BEARING_SEAL_430/reverse/die_design.json'))['pierce_iterations']
# 1) 제품 → 거꾸로 금형
seal=loop_obj(seal_profile(),'seal',COL['sheet'],angle=360,seg=128,loc=(450,0,60),scale=4.0); spin(seal,0,DUR,turns=0.3)
show(seal,T(1)-0.1,E(2)+0.6,base=(4,4,4))
flat=loop_obj(burr_top_pts(12.6,1,k=0),'flat',COL['sheet'],angle=360,loc=(-450,0,60),scale=4.0); show(flat,T(1)+1.6,E(2)+0.6,base=(4,4,4))
q=text('?',90,(-450,-30,90),rgb=COL['accent']); show(q,T(1)+2.0,E(2)+0.6)
ar=curve_line([(300,-40,150),(-300,-40,150)],bevel=6,rgb=COL['accent']); show(ar,T(1)+0.8,E(2)+0.6)
ah=cyl(18,40,(-310,-40,150),COL['accent'],seg=4,rot=(0,math.radians(-90),0)); show(ah,T(1)+0.8,E(2)+0.6)
t1=text('완성 제품 → 거꾸로 → 금형',32,(0,-60,260),rgb=COL['white']); show(t1,T(1)+0.5,E(1)+0.3)
pd=image_plane('/home/user/mold_sold/parts/TEST_BEARING_SEAL_430/product_drawing.png',460,(0,80,360),name='pd'); show(pd,T(2)+0.2,E(2)+0.6,base=(1,1,1))
t2=text('처음 구멍 지름 = ?',34,(-450,-60,250),rgb=COL['accent']); show(t2,T(2)+2.0,E(2)+0.6)
# 2) 작은 구멍 / 큰 구멍 비교
S=13.0; ZC=150
for i,(Rh,dep,lab,c_) in enumerate(((11.0,6.0,'구멍 작음 → 너무 높게',COL['red']),(13.8,2.4,'구멍 큼 → 너무 낮게',COL['sky']))):
    x=-330+i*660
    o=loop_obj(burr_top_pts(Rh,dep,Ro=22),'cmp%d'%i,COL['sheet'],loc=(x,0,ZC),scale=S)
    keyv(o,'scale',[(0,(0,0,0)),(T(3)-0.1,(0,0,0)),(T(3)+0.4,(S,S,S)),(E(3)+0.2,(S,S,S)),(E(3)+0.5,(0,0,0))])
    yz=-16*S*0.7071
    tg=curve_line([(x-260,yz,ZC-(4.0-t)*S),(x+260,yz,ZC-(4.0-t)*S)],bevel=1.6,rgb=(0.4,1,0.5)); show(tg,T(3)+0.5,E(3)+0.2)
    tl=text(lab,28,(x,-200,ZC+130),rgb=c_); show(tl,T(3)+0.6+i*2.2,E(3)+0.2)
tg2=text('초록 선 = 목표 높이 4.0',22,(0,-200,ZC-90),rgb=(0.4,1,0.5)); show(tg2,T(3)+0.6,E(3)+0.2)
# 3) 반복: 구멍 → 해석 → 높이 비교 → 고침
MX=0; MS=15.0
it_o=loop_obj(burr_top_pts(IT[0]['pierce_dia']/2,1,k=0,Ro=24),'iter',COL['sheet'],loc=(MX,0,150),scale=MS)
keys=[]
for it in IT:
    keys.append((add_key(it_o,'f%d'%it['iter'],burr_top_pts(it['pierce_dia']/2,1,k=0,Ro=24)),add_key(it_o,'b%d'%it['iter'],burr_top_pts(it['pierce_dia']/2,it['flange_height']-t,k=1,Ro=24))))
keyv(it_o,'scale',[(0,(0,0,0)),(T(4)-0.1,(0,0,0)),(T(4)+0.4,(MS,MS,MS))])
tA=T(4)+0.4; tB=E(6)-0.6; step=(tB-tA)/len(IT)
seq=[]; seq2=[]
for i,(kf,kb) in enumerate(keys):
    a=tA+i*step
    for sk_ in (kf,kb): keyk(sk_,[(0,0)])
    keyk(kf,[(a-0.01,0),(a+0.15,1),(a+step*0.25,1),(a+step*0.6,0)])
    keyk(kb,[(a+step*0.25,0),(a+step*0.6,1),(a+step*0.97,1),(a+step*1.0,0)] if i<len(IT)-1 else [(a+step*0.25,0),(a+step*0.6,1)])
    it=IT[i]
    seq.append((a,'반복 %d   구멍 Ø%.2f'%(i+1,it['pierce_dia'])))
    seq2.append((a+step*0.6,'높이 %.2f  (목표와 차이 %+.2f)'%(it['flange_height'],it['dH'])))
    seq2.append((a+step*0.98,' '))
yz=-16*MS*0.7071
tgt=curve_line([(MX-330,yz,150-(4.0-t)*MS),(MX+330,yz,150-(4.0-t)*MS)],bevel=1.8,rgb=(0.4,1,0.5)); show(tgt,T(4)+0.4,E(7))
tt=text('목표 높이 4.0',20,(MX+420,yz,150-(4.0-t)*MS),rgb=(0.4,1,0.5)); show(tt,T(4)+0.5,E(7))
c1=text(' ',30,(MX,-250,370),rgb=COL['white']); text_seq(c1,seq+[(E(6)+0.2,' ')])
c2=text(' ',26,(MX,-250,330),rgb=COL['accent']); text_seq(c2,seq2[:-1]+[(E(7),' ')])
ok=text('높이 차이 0.01 mm 이내 → 확정',30,(MX,-250,290),rgb=(0.4,1,0.5)); show(ok,T(6)+1.8,E(7))
big=text('Ø23.25  →  Ø25.26',60,(MX,-250,410),rgb=COL['accent']); show(big,T(7)+0.3,E(7)+0.3)
# 4) 공정 순서·금형 세트 자동 → 스트립
SX=1700
strip=empty('strip',(SX,0,60))
for f in [os.path.join(DIE,'strip.stl')]+sorted(glob.glob(os.path.join(DIE,'strip_part_*.stl'))):
    o=stl(f,COL['sheet'],os.path.basename(f)[:-4]); o.parent=strip
strip.scale=(1.8,1.8,1.8)
keyv(strip,'location',[(0,(SX,0,-600)),(T(8)-0.1,(SX,0,-600)),(T(8)+0.8,(SX,0,60))])
for i,(nm,x) in enumerate((('피어싱',-216),('버링',-108),('리스트라이크',0),('하프블랭킹',108),('블랭킹',216))):
    o=text(nm,22,(SX+x*1.8,-90,150),rgb=COL['white']); show(o,T(8)+0.9+i*0.35)
st=text('공정 순서 · 금형 세트 자동 생성',34,(SX,-90,260),rgb=COL['accent']); show(st,T(8)+0.5)
# 카메라
cam,tgt_=camera(35)
cam_keys(cam,tgt_,[(0,(0,-1500,600),(0,0,150)),(T(1)+1.5,(0,-1250,420),(0,0,170)),(E(2),(40,-1200,420),(0,0,180))])
cam_keys(cam,tgt_,[(T(3)+0.6,(0,-1450,230),(0,0,170)),(E(3),(-30,-1400,225),(0,0,170))])
cam_keys(cam,tgt_,[(T(4)+0.8,(-80,-820,200),(0,0,170)),(E(6)-0.5,(80,-820,200),(0,0,170))])
cam_keys(cam,tgt_,[(T(7)+0.4,(0,-1000,300),(0,0,270)),(E(7),(0,-980,300),(0,0,270))])
cam_keys(cam,tgt_,[(T(8)+1.0,(SX,-900,420),(SX,0,120)),(DUR,(SX+60,-880,400),(SX,0,120))])
handheld(cam,0.5)
finish('ch6',DUR)
