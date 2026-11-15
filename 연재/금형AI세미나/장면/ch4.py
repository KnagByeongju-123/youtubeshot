import sys,os; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from s3d import *
T,E,DUR,cs=chapter(4)
sc=setup(texture=True)
floor(extent=2000)
S=2.2; R=18*S; H=60*S
pu=revolve(PUNCH,'punch',rgb=COL['punch']); pu.scale=(S,)*3; pu.location=(0,0,10)
full=PUNCH+[(-r,z) for r,z in reversed(PUNCH)]
def rect(pts,rgb,parent,b=1.0):
    o=curve_line(pts+[pts[0]],bevel=b,rgb=rgb); o.parent=parent; return o
# 투영 틀 3개 (앞·위·옆) — 경첩에 매단 묶음
Y0=-120; X1=120; Z1=170; Z0=-5
front=empty('front',(0,0,0))
rect([(-120,Y0,Z0),(120,Y0,Z0),(120,Y0,Z1),(-120,Y0,Z1)],COL['sky'],front,1.4)
fo=curve_line([(r*S,Y0,10+z*S) for r,z in full],bevel=1.3,rgb=COL['white'],closed=True); fo.parent=front
top=empty('top',(0,Y0,Z1))       # 경첩: 앞 틀 윗변
rect([(-120,0,0),(120,0,0),(120,240,0),(-120,240,0)],COL['sky'],top,1.4)
for rr in (18,15):
    pts=[(rr*S*math.cos(a*math.pi/36),120+rr*S*math.sin(a*math.pi/36),0) for a in range(72)]
    c=curve_line(pts,bevel=1.3,rgb=COL['white'],closed=True); c.parent=top
side=empty('side',(X1,Y0,0))     # 경첩: 앞 틀 오른쪽 변
rect([(0,0,Z0),(0,240,Z0),(0,240,Z1),(0,0,Z1)],COL['sky'],side,1.4)
so=curve_line([(0,120+r*S,10+z*S) for r,z in full],bevel=1.3,rgb=COL['white'],closed=True); so.parent=side
for g,tt in ((front,T(2)+0.2),(top,T(2)+0.9),(side,T(2)+1.6)):
    keyv(g,'scale',[(0,(0,0,0)),(tt-0.01,(0,0,0)),(tt+0.4,(1,1,1))])
# 투영선 (물체 → 틀) 깜빡
for a,b_ in (((R,0,10+H*0.6),(R,Y0,10+H*0.6)),((0,0,10+H),(0,0,Z1)),((R,0,10+H*0.3),(X1,0,10+H*0.3))):
    l=curve_line([a,b_],bevel=0.6,rgb=COL['accent']); show(l,T(2)+0.4,T(2)+3.0,grow=0.2)
# 펼치기
keyv(top,'rotation_euler',[(T(2)+3.0,(0,0,0)),(T(2)+4.6,(math.radians(90),0,0))])
keyv(side,'rotation_euler',[(T(2)+3.4,(0,0,0)),(T(2)+5.0,(0,0,math.radians(-90)))])
keyv(pu,'scale',[(0,(S,S,S)),(T(2)+4.4,(S,S,S)),(T(2)+5.0,(0,0,0))])
lb=[('정면도',(0,Y0-5,190)),('평면도',(0,Y0-5,Z1+260)),('측면도',(X1+120,Y0-5,190))]
for s_,p_ in lb: o=text(s_,18,p_,rgb=COL['sky']); show(o,T(2)+5.0,E(2)+0.5)
# 도면 종이(표제란 포함)로 바뀜
dwg=image_plane(os.path.join(HERE,'도면_1_버링펀치.png'),620,(60,Y0+40,240),name='dwg')
keyv(dwg,'scale',[(0,(0,0,0)),(T(3)-0.2,(0,0,0)),(T(3)+0.4,(1,1,1))])
for g in (front,top,side): keyv(g,'scale',[(T(3)-0.2,(1,1,1)),(T(3)+0.2,(0,0,0))])
# 표제란 강조
tb=curve_line([(116,Y0+30,34),(358,Y0+30,34),(358,Y0+30,108),(116,Y0+30,108),(116,Y0+30,34)],bevel=2.2,rgb=COL['red'])
draw_on(tb,T(3)+1.2,T(3)+2.4)
t3=text('표제란: 품명 · 재질 · 경도 · 수량 · 척도',22,(60,Y0+20,485),rgb=COL['accent']); show(t3,T(3)+1.4,E(4)+0.3)
for i,s_ in enumerate(['품명 · 버링 펀치 Ø30','도면 번호 · SMP-P-001','날짜 · 2026-11-14']):
    o=text(' ',18,(60+380,Y0+20,110-i*34),rgb=COL['white'],bold=False,align='LEFT'); typewriter(o,s_,T(4)+0.3+i*1.0,T(4)+1.2+i*1.0)
    show(o,T(4)+0.2,E(4)+0.4,base=(1,1,1))
# 여러 장 → PDF 한 묶음
PX=1200
book=box((260,60,340),(PX,40,190),(0.75,0.12,0.12),bevel=8,name='book'); show(book,T(5)+0.2)
tp=text('PDF',60,(PX,8,190),rgb=COL['white']); show(tp,T(5)+0.3)
names=['도면_1_버링펀치','도면_2_버링다이','도면_3_펀치고정판']
pages=[]
for i,nm in enumerate(names):
    pg=image_plane(os.path.join(HERE,nm+'.png'),300,(PX-700+i*330,-200,220),name='pg%d'%i)
    keyv(pg,'scale',[(0,(0,0,0)),(T(5)+0.4+i*0.5,(0,0,0)),(T(5)+0.8+i*0.5,(1,1,1))])
    tin=T(5)+3.0+i*0.7
    keyv(pg,'location',[(tin,(PX-700+i*330,-200,220)),(tin+0.8,(PX,-10,190+i*4))])
    keyv(pg,'scale',[(tin+0.6,(1,1,1)),(tin+0.85,(0,0,0))])
    pages.append(pg)
keyv(dwg,'location',[(T(5),(60,Y0+40,240)),(T(5)+0.6,(60,Y0+40,-600))])
# 현장 · 협력업체로
for i,(nm,x,c_) in enumerate((('현장',PX+600,COL['die']),('협력업체',PX+1000,COL['sky']))):
    hs=box((220,160,140),(x,60,70),c_,bevel=6); show(hs,T(6)+0.2+i*0.3)
    rf=box((240,170,20),(x,60,150),(0.3,0.33,0.4)); show(rf,T(6)+0.3+i*0.3)
    t=text(nm,40,(x,-26,75),rgb=COL['ink']); show(t,T(6)+0.4+i*0.3)
    cp=box((70,10,90),(PX,-40,190),(0.9,0.2,0.2),bevel=4)
    keyv(cp,'scale',[(0,(0,0,0)),(T(6)+1.0+i*0.6,(0,0,0)),(T(6)+1.2+i*0.6,(1,1,1))])
    keyv(cp,'location',[(T(6)+1.2+i*0.6,(PX,-40,190)),(T(6)+2.0+i*0.6,(x-100+i*60*0+((i*2-1)*0+0)+0, -40, 420)),(T(6)+2.8+i*0.6,(x,-40,200))])
same=text('어느 컴퓨터에서나 똑같이',26,(PX+800,-40,330),rgb=COL['accent']); show(same,T(6)+2.4,E(6)+0.4)
# 모델 수정 → 도면 다시
MX=-900
p2=revolve(PUNCH,'p2',rgb=COL['punch']); p2.scale=(S,)*3; p2.location=(MX,0,10)
keyv(p2,'scale',[(0,(0,0,0)),(T(7)-0.2,(0,0,0)),(T(7)+0.3,(S,S,S)),(T(7)+1.4,(S,S,S)),(T(7)+2.2,(S,S,S*1.18))])
ar=curve_line([(MX+80,0,140),(MX+260,0,140)],bevel=4,rgb=COL['accent']); show(ar,T(7)+2.4)
d2=image_plane(os.path.join(HERE,'도면_1_버링펀치.png'),300,(MX+460,0,150),name='d2')
keyv(d2,'scale',[(0,(0,0,0)),(T(7)+2.6,(0,0,0)),(T(7)+3.0,(1,1,1))])
nt=text('모델 수정 → 도면 다시 뽑기',28,(MX+220,-20,330),rgb=COL['white']); show(nt,T(7)+0.6)
nt2=text('길이 60 → 70',22,(MX,-60,-25+0),rgb=COL['accent']); nt2.location=(MX,-60,190+20); show(nt2,T(7)+1.6)
# 카메라
cam,tgt=camera(35)
cam_keys(cam,tgt,[(0,(-380,-700,420),(0,0,90)),(T(1)+2,(-300,-640,330),(0,0,90))])
orbit(cam,tgt,T(1)+2,T(2)+3.0,(0,0,90),620,260,-125,-60,n=8)
cam_keys(cam,tgt,[(T(2)+5.0,(120,-1050,260),(120,0,200)),(E(2),(120,-1000,250),(120,0,200))])
cam_keys(cam,tgt,[(T(3)+1.2,(60,-820,260),(60,0,240)),(T(4)+0.3,(380,-720,150),(370,0,110)),(E(4),(390,-700,150),(380,0,110))])
cam_keys(cam,tgt,[(T(5)+0.6,(PX-350,-1400,420),(PX-350,0,200)),(E(5),(PX-100,-1200,380),(PX,0,200))])
cam_keys(cam,tgt,[(T(6)+0.8,(PX+500,-1500,520),(PX+500,0,170)),(E(6),(PX+520,-1450,500),(PX+500,0,170))])
cam_keys(cam,tgt,[(T(7)+1.3,(MX+220,-1000,320),(MX+220,0,150)),(DUR,(MX+200,-950,300),(MX+220,0,150))])
sfx(T(2)+3.0,'whoosh',0.7); sfx(T(5)+3.0,'whoosh',0.7); sfx(T(6)+1.2,'whoosh',0.7); sfx(T(7)+0.4,'whoosh',0.8)
handheld(cam,0.5)
finish('ch4',DUR)
