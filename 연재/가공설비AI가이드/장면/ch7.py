import sys,os; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from g3d import *
T,E,DUR,cs=chapter(7)
sc=setup(texture=True); floor(extent=2600)
cam,tgt=camera(35)
# 1) 쓰는 오픈소스 (원형으로 떠 있는 카드)
USE=[('Python','계산 · 자동화'),('CadQuery','입체 솔리드'),('ezdxf','도면 파일'),('Blender','보여 주는 화면'),('shapely','2D 도형 검사'),('matplotlib','도면 · 그림')]
for i,(nm,ds) in enumerate(USE):
    a=math.radians(90+i*60); p=(380*math.cos(a),380*math.sin(a),220+(i%2)*90)
    g=card(nm,ds,p,(0.4,1,0.5),w=200,h=90,tsize=24,ssize=13,face=cam)
    keyv(g,'scale',[(0,(0,0,0)),(T(1)+0.2+i*0.4,(0,0,0)),(T(1)+0.4+i*0.4,(1.1,1.1,1.1)),(T(1)+0.6+i*0.4,(1,1,1))])
    tag=text('사용 중',14,(0,-6,-60),rot=(0,0,0),rgb=(0.4,1,0.5)); tag.parent=g; tag.rotation_euler=(math.radians(90),0,0)
REV=[('OCR','글자 읽기'),('CAMotics','가공 시뮬레이션'),('pandas','측정 통계')]
for i,(nm,ds) in enumerate(REV):
    p=(-300+i*300,-420,120)
    g=card(nm,ds,p,COL['accent'],w=220,h=90,tsize=24,ssize=13,face=cam)
    keyv(g,'scale',[(0,(0,0,0)),(T(2)+0.3+i*0.5,(0,0,0)),(T(2)+0.6+i*0.5,(1,1,1))])
rv=text('도입 검토',30,(0,-430,250),rgb=COL['accent']); show(rv,T(2)+0.2)
core=ai_orb((0,0,260),55); spin(core,0,DUR,2); show(core,0.2,base=(1,1,1))
# 2) 숫자는 표 한 곳 → 모델 · NC · 지시서
QX=1400
src=card('치수 표','숫자는 한 곳에',(QX,0,420),COL['accent'],w=220,h=90,tsize=26)
keyv(src,'scale',[(0,(0,0,0)),(T(3)-0.1,(0,0,0)),(T(3)+0.2,(1,1,1))])
for i,(nm,c) in enumerate((('입체 모델',COL['punch']),('NC',(0.4,1,0.5)),('작업지시서',COL['white']))):
    x=QX-260+i*260; g=card(nm,'같은 값',(x,0,180),c,w=190,h=80,tsize=22)
    keyv(g,'scale',[(0,(0,0,0)),(T(3)+0.5+i*0.4,(0,0,0)),(T(3)+0.8+i*0.4,(1,1,1))])
    l=curve_line([(QX,0,370),(x,0,225)],bevel=3,rgb=COL['accent']); show(l,T(3)+0.4+i*0.4)
# 3) 다시 읽어 검사 + 비공개 저장소(금고)
vx=QX+700
safe=box((200,180,200),(vx,0,100),(0.35,0.38,0.44),bevel=8,name='safe'); show(safe,T(4)+0.8)
door=cyl(60,10,(vx,-92,110),(0.55,0.58,0.64),seg=48,rot=(math.radians(90),0,0)); show(door,T(4)+0.9)
lk=text('비공개 저장소',24,(vx,-100,240),rgb=COL['white']); show(lk,T(4)+1.0)
dw=image_plane(os.path.join(HERE,'도면_1_버링펀치.png'),120,(vx-250,-40,150),name='dwg')
keyv(dw,'location',[(0,(vx-250,-40,150)),(T(4)+1.6,(vx-250,-40,150)),(T(4)+2.6,(vx,-40,110))]); keyv(dw,'scale',[(0,(0,0,0)),(T(4)+0.9,(0,0,0)),(T(4)+1.1,(1,1,1)),(T(4)+2.4,(1,1,1)),(T(4)+2.6,(0,0,0))])
rc=text('AI 결과는 다시 읽어 검사',26,(QX,-100,560),rgb=(0.4,1,0.5)); show(rc,T(4)+0.2)
# 4) 사람이 꼭 하는 일
px=QX+300
pp=person((px-480,-150,0),(0.62,0.42,0.95),name='human',scale=1.5); keyv(pp,'scale',[(0,(0,0,0)),(T(5)-0.1,(0,0,0)),(T(5)+0.3,(1.5,1.5,1.5))])
for i,s_ in enumerate(('가공 조건 확정','시뮬레이션 · 드라이런','첫 가공품 승인')):
    g=card(s_,'',(px+i*0,-150,330-i*90),COL['accent'],w=300,h=70,tsize=22)
    keyv(g,'scale',[(0,(0,0,0)),(T(5)+0.5+i*0.6,(0,0,0)),(T(5)+0.8+i*0.6,(1,1,1))])
    ok=mark(True,(px+190,-160,330-i*90),26); show(ok,T(5)+1.0+i*0.6)
cam_keys(cam,tgt,[(0,(0,-1300,700),(0,0,260))])
orbit(cam,tgt,0.3,E(2),(0,0,230),1150,380,-90,-40,n=10)
cam_keys(cam,tgt,[(T(3)+0.5,(QX,-1000,380),(QX,0,300)),(E(3),(QX+60,-980,370),(QX,0,300))]); sfx(T(3)+0.1,'whoosh',0.8)
cam_keys(cam,tgt,[(T(4)+0.5,(QX+350,-1100,420),(QX+350,0,250)),(E(4),(QX+420,-1050,400),(QX+380,0,220))])
cam_keys(cam,tgt,[(T(5)+0.4,(px-100,-950,380),(px-100,-150,230)),(DUR,(px-60,-980,390),(px-100,-150,230))])
handheld(cam,0.5)
finish('ch7',DUR)
