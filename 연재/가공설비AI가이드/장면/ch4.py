import sys,os; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from g3d import *
T,E,DUR,cs=chapter(4)
sc=setup(texture=True); floor(extent=2600)
# 1) 도면 접수 → 글자 읽기(스캔 막대)
dw=image_plane(os.path.join(HERE,'도면_1_버링펀치.png'),520,(-650,40,260),name='dw'); show(dw,T(1)-0.2,base=(1,1,1))
sb=box((540,6,8),(-650,30,440),(0.4,1,0.5),name='scanbar')
keyv(sb,'location',[(0,(-650,30,-300)),(T(2)-0.05,(-650,30,-300)),(T(2),(-650,30,440)),(T(2)+2.2,(-650,30,80)),(T(2)+2.3,(-650,30,-300))])
tb=table((-50,-60,380),['부품','치수','공차'],[['버링 펀치','Ø30','h6'],['버링 펀치','R7','±0.05'],['버링 다이','Ø31.2','H7'],['?','읽기 어려움','질문']],[-200,-40,110],w=420,t0=T(2)+1.2,dt=0.45)
keyv(tb,'scale',[(0,(0,0,0)),(T(2)+0.8,(0,0,0)),(T(2)+1.1,(1,1,1))])
# 2) 치수 표 → 입체 모델 + 부피 확인
MX=600; S=2.4
pu=revolve(PUNCH,'pu',rgb=COL['punch'],angle=0.1,loc=(MX,0,10)); pu.scale=(S,)*3
md=pu.modifiers['screw']; md.angle=math.radians(0.1); md.keyframe_insert('angle',frame=F(T(3)+0.3)); md.angle=math.radians(360); md.keyframe_insert('angle',frame=F(T(3)+2.0))
vt=text('부피: 모델 = 손 계산',22,(MX,-80,230),rgb=(0.4,1,0.5)); show(vt,T(3)+2.4,E(3)+0.4)
# 3) 공정표 (열처리 전/후 · 설비)
GX=1350
bars=[('선반 · 외형',0,2,(0.6,0.62,0.68)),('구멍 가공',2,2,COL['punch']),('열처리',4,2,(0.95,0.45,0.25)),('연삭',6,1.5,(0.85,0.85,0.8)),('와이어',7.5,2.5,COL['die'])]
for i,(nm,a,w,c) in enumerate(bars):
    b=box((w*45,30,32),(GX-200+(a+w/2)*45,0,330-i*45),c,bevel=3); show(b,T(4)+0.3+i*0.35)
    o=text(nm,16,(GX-230,-20,330-i*45),rgb=COL['white'],align='RIGHT'); show(o,T(4)+0.3+i*0.35)
ln=box((4,40,260),(GX-200+4*45,-5,240),COL['red']); show(ln,T(4)+2.2)
lt=text('열처리 전 | 후',16,(GX-200+4*45,-25,390),rgb=COL['red']); show(lt,T(4)+2.3)
# 4) 같은 표 → 모델 · NC · 지시서 (숫자 같음)
src=card('치수 표','숫자는 한 곳에',(GX+700,-60,380),COL['accent'],w=200,h=90,tsize=26)
keyv(src,'scale',[(0,(0,0,0)),(T(5)-0.1,(0,0,0)),(T(5)+0.2,(1,1,1))])
for i,(nm,c) in enumerate((('입체 모델',COL['punch']),('NC',(0.4,1,0.5)),('작업지시서',COL['white']))):
    x=GX+460+i*240
    g=card(nm,'Ø30',(x,-60,170),c,w=170,h=80,tsize=22)
    keyv(g,'scale',[(0,(0,0,0)),(T(5)+0.6+i*0.4,(0,0,0)),(T(5)+0.9+i*0.4,(1,1,1))])
    l=curve_line([(GX+700,-60,330),(x,-60,215)],bevel=2.5,rgb=COL['accent']); show(l,T(5)+0.5+i*0.4)
# 5) 프롬프트 → 한 번에 정리
pc=box((820,8,160),(GX+700,-220,560),(0.08,0.10,0.15),bevel=6,name='prompt'); show(pc,T(6)-0.2)
p1=text(' ',18,(GX+310,-225,590),rgb=COL['white'],bold=False,align='LEFT'); typewriter(p1,'"경도 HRC60 기준, 사내 설비에 맞춰',T(6)+0.3,T(6)+2.4); show(p1,T(6)-0.1,base=(1,1,1))
p2=text(' ',18,(GX+310,-225,550),rgb=COL['accent'],bold=False,align='LEFT'); typewriter(p2,' 공정표와 작업지시서 초안을 만들어 줘."',T(6)+2.4,T(6)+4.4); show(p2,T(6)-0.1,base=(1,1,1))
for i,nm in enumerate(('설비 배정','공정 순서','원점 · 공구 · 조건 표')):
    o=card(nm,'',(GX+460+i*240,-220,420),(0.4,1,0.5),w=210,h=60,tsize=18)
    keyv(o,'scale',[(0,(0,0,0)),(T(7)+0.3+i*0.5,(0,0,0)),(T(7)+0.6+i*0.5,(1,1,1))])
cam,tgt=camera(35)
cam_keys(cam,tgt,[(0,(-650,-1100,420),(-500,0,260)),(T(2)+0.5,(-400,-1250,380),(-330,0,290)),(E(2),(-350,-1220,370),(-300,0,290))])
cam_keys(cam,tgt,[(T(3)+0.4,(MX,-650,260),(MX,0,90)),(E(3),(MX+60,-620,250),(MX,0,90))]); sfx(T(3)+0.1,'whoosh',0.7)
cam_keys(cam,tgt,[(T(4)+0.5,(GX,-850,330),(GX,0,250)),(E(4),(GX+40,-820,320),(GX,0,250))])
cam_keys(cam,tgt,[(T(5)+0.5,(GX+700,-900,330),(GX+700,0,260)),(E(5),(GX+720,-880,340),(GX+700,0,270))])
cam_keys(cam,tgt,[(T(6)+0.5,(GX+700,-1100,520),(GX+700,-200,470)),(DUR,(GX+720,-1150,520),(GX+700,-200,470))])
handheld(cam,0.5)
finish('ch4',DUR)
