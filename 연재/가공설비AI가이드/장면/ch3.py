import sys,os; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from g3d import *
T,E,DUR,cs=chapter(3)
sc=setup(texture=True); floor(extent=2600)
# 1) 제품도 → 단면
pd=image_plane(os.path.join(HERE,'제품도.png'),520,(-700,40,260),name='pd'); show(pd,T(1)-0.2,base=(1,1,1))
S=9.0
prof=curve_line([(-700+r*S-120,-10,90+z*S) for r,z in seal_profile()]+[(-700+seal_profile()[0][0]*S-120,-10,90+seal_profile()[0][1]*S)],bevel=1.6,rgb=COL['accent'],name='sec')
draw_on(prof,T(2)+0.6,T(2)+3.0)
for i,(s_,z) in enumerate((('두께 0.6',380),('R 0.8 · 1.4',350),('높이 4',320),('지름 52',290))):
    o=text(s_,18,(-380,-20,z),rgb=COL['white'],align='LEFT'); show(o,T(2)+0.8+i*0.4,E(2)+0.3)
# 2) 공정안 A·B·C + 해석 색
PX=200
plans=[('A',3),('B',2),('C',1)]
for i,(nm,ns) in enumerate(plans):
    x=PX+i*330
    pedestal((x,0,0),r=120,h=10)
    t=text('공정안 '+nm+f' ({ns}공정)',24,(x,-60,300),rgb=COL['white']); show(t,T(3)+0.3+i*0.3)
    for k in range(ns):
        s_=revolve(seal_profile(H=1.5+2.5*(k+1)/ns),'pl%d%d'%(i,k),seg=64,rgb=COL['sheet']); s_.scale=(2.2,)*3; s_.location=(x-60*(ns-1)/2+k*60*0+0,0,30+k*60)
        show(s_,T(3)+0.5+i*0.3+k*0.15,base=(2.2,2.2,2.2))
        m=s_.data.materials[0]
        thin=[0.25,0.45,0.95][i] if k==ns-1 else 0.2
        jc=(max(0,min(1,1.5-abs(4*thin-3))),max(0,min(1,1.5-abs(4*thin-2))),max(0,min(1,1.5-abs(4*thin-1))))
        m.diffuse_color=(*COL['sheet'],1); m.keyframe_insert('diffuse_color',frame=F(T(3)+2.2)); m.diffuse_color=(*jc,1); m.keyframe_insert('diffuse_color',frame=F(T(3)+3.2))
an=text('성형해석: 세 안을 한꺼번에',28,(PX+330,-60,380),rgb=COL['accent']); show(an,T(3)+2.2,E(3)+0.3)
x_=mark(False,(PX+660,-80,200),70); show(x_,T(4)+0.4,E(4)+0.4); sfx(T(4)+0.4,'pop',0.6)
xt=text('두께 감소 기준 초과',18,(PX+660,-80,140),rgb=COL['red']); show(xt,T(4)+0.6,E(4)+0.4)
ok_=mark(True,(PX+330,-80,200),70); show(ok_,T(4)+2.0,E(4)+0.4)
ot=text('기준 안 · 공정 수 최소',18,(PX+330,-80,140),rgb=(0.35,1,0.45)); show(ot,T(4)+2.2,E(4)+0.4)
# 3) 펀치 · 다이 · 스트립 · 입체
QX=1500; SS=3.0
die=revolve(DIE_P,'die',rgb=COL['die'],angle=270); die.scale=(SS,)*3; die.rotation_euler=(0,0,math.radians(-45)); die.location=(QX,0,0)
pun=revolve(PUNCH,'pun',rgb=COL['punch'],angle=270); pun.scale=(SS,)*3; pun.rotation_euler=(0,0,math.radians(-45))
keyv(pun,'location',[(0,(QX,0,600)),(T(5)+0.3,(QX,0,600)),(T(5)+1.3,(QX,0,30*SS+30))])
keyv(die,'location',[(0,(QX,0,-400)),(T(5)+0.1,(QX,0,-400)),(T(5)+1.0,(QX,0,0))])
strip=empty('strip',(QX+520,0,40))
for f in [os.path.join(DIE,'strip.stl')]+sorted(glob.glob(os.path.join(DIE,'strip_part_*.stl'))):
    o=stl(f,COL['sheet'],os.path.basename(f)[:-4]); o.parent=strip
strip.scale=(1.0,1.0,1.0); strip.rotation_euler=(0,0,math.radians(90))
keyv(strip,'scale',[(0,(0,0,0)),(T(5)+1.6,(0,0,0)),(T(5)+2.1,(1,1,1))])
for i,s_ in enumerate(('펀치 · 다이 지름','틈','스트립 배치')):
    o=text(s_,22,(QX+180,-80,360-i*34),rgb=COL['white'],align='LEFT'); show(o,T(5)+0.8+i*0.6,E(5)+0.3)
# 4) 프롬프트 카드
pc=box((760,8,170),(QX+250,-200,300),(0.08,0.10,0.15),bevel=6,name='prompt'); show(pc,T(6)-0.2,E(6)+0.3)
pt=text(' ',20,(QX-110,-205,330),rgb=COL['white'],bold=False,align='LEFT'); typewriter(pt,'"치수가 분명하지 않으면 추측하지 말고,',T(6)+0.2,T(6)+2.0); show(pt,T(6)-0.1,E(6)+0.3,base=(1,1,1))
pt2=text(' ',20,(QX-110,-205,290),rgb=COL['accent'],bold=False,align='LEFT'); typewriter(pt2,' 질문 목록으로 적어 줘."',T(6)+2.0,T(6)+3.2); show(pt2,T(6)-0.1,E(6)+0.3,base=(1,1,1))
# 5) 비교표
tb=table((QX+250,-200,330),['항목','계산','실제 금형','차이'],[['펀치 지름','30.00','30.00','0'],['다이 구멍','31.20','31.15','0.05'],['피치','54.0','54.0','0']],[-330,-150,30,220],w=700,t0=T(7)+0.4,dt=0.5)
keyv(tb,'scale',[(0,(0,0,0)),(T(7)-0.1,(0,0,0)),(T(7)+0.2,(1,1,1))])
ex=text('(예시 값)',14,(QX+560,-205,355),rgb=(0.7,0.75,0.85)); show(ex,T(7)+0.2)
ds=person((QX-200,-150,0),(0.62,0.42,0.95),name='designer',scale=1.3); keyv(ds,'scale',[(0,(0,0,0)),(T(8)-0.2,(0,0,0)),(T(8)+0.2,(1.3,1.3,1.3))])
dc=text('설계자 결정',40,(QX+250,-220,450),rgb=COL['accent']); show(dc,T(8)+0.4); sfx(T(8)+0.4,'click',0.9)
cam,tgt=camera(35)
cam_keys(cam,tgt,[(0,(-700,-1100,450),(-700,40,260)),(T(2)+0.4,(-650,-900,330),(-580,0,240)),(E(2),(-600,-860,320),(-560,0,240))])
cam_keys(cam,tgt,[(T(3)+0.6,(PX+330,-1250,520),(PX+330,0,170)),(E(4),(PX+400,-1150,480),(PX+330,0,170))])
cam_keys(cam,tgt,[(T(5)+0.6,(QX+150,-900,420),(QX+200,0,170)),(E(5),(QX+250,-880,400),(QX+250,0,180))])
cam_keys(cam,tgt,[(T(6)+0.3,(QX+250,-850,330),(QX+250,-200,300)),(E(8),(QX+230,-1000,380),(QX+230,-200,320))])
handheld(cam,0.5)
finish('ch3',DUR)
