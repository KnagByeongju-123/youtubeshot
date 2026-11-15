import sys,os; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from s3d import *
T,E,DUR,cs=chapter(1)
sc=setup(texture=True)
floor(extent=1600)
# --- 작은 프레스: 펀치(파랑) · 판(주황) · 다이(초록) ---
PX=-700
S=3.0
die=revolve(DIE_P,'die',rgb=COL['die'],loc=(PX,0,0),angle=270); die.rotation_euler=(0,0,math.radians(-45)); die.scale=(S,)*3
sheet,sk=burr_sheet(Ro=40,Rh=12.6,loc=(PX,0,30*S+0.6*S),scale=S); cut(sheet,270); sheet.rotation_euler=(0,0,math.radians(-45))
punch=revolve(PUNCH,'punch',rgb=COL['punch'],loc=(PX,0,0),angle=270); punch.rotation_euler=(0,0,math.radians(-45)); punch.scale=(S,)*3
ztop=30*S+0.6*S
keyv(punch,'location',[(0,(PX,0,ztop+90)),(T(1)+0.5,(PX,0,ztop+90)),(T(1)+2.0,(PX,0,ztop+2)),(T(2)+0.3,(PX,0,ztop+2)),(T(2)+3.3,(PX,0,ztop-5.6*S)),(E(2)-0.3,(PX,0,ztop-5.6*S)),(E(2)+1.2,(PX,0,ztop+90))])
keyk(sk,[(0,0),(T(2)+0.3,0),(T(2)+3.3,1)])
lab1=text('펀치',22,(PX-150,0,ztop+150),rgb=COL['sky']); show(lab1,T(1)+0.6,E(2))
lab2=text('판재',20,(PX-200,0,ztop+5),rgb=COL['sheet']); show(lab2,T(1)+1.2,E(2))
lab3=text('다이',20,(PX-150,0,45),rgb=COL['die']); show(lab3,T(1)+1.6,E(2))
lab4=text('버링: 구멍 가장자리를 아래로 세움',20,(PX,0,ztop+210),rgb=COL['accent']); show(lab4,T(2)+0.5,E(2))
# --- 대화창 (프롬프트) → 코드 창 ---
CX=0
chat=empty('chatG',(CX,0,240)); code=empty('codeG',(CX,0,240))
pn=panel(600,320,(0,25,0),name='chat'); pn.parent=chat
hd=text('AI 에게 부탁하기',24,(-270,15,125),rgb=COL['accent'],align='LEFT'); hd.parent=chat
lines=['지름 30 mm 의 버링 펀치를 그려 줘.','끝은 둥글게(R7),','위쪽에는 고정용 턱(Ø36)을 붙여 줘.','전체 길이 60 mm, 재질 SKD11.']
for i,l in enumerate(lines):
    o=text(' ',22,(-270,15,65-i*44),rgb=COL['white'],bold=False,align='LEFT'); o.parent=chat
    a_=T(4)+0.6+i*1.7; typewriter(o,l,a_,a_+1.5)
keyv(chat,'scale',[(0,(0,0,0)),(T(3)-0.4,(0,0,0)),(T(3)+0.1,(1.05,1.05,1.05)),(T(3)+0.4,(1,1,1)),(T(5)-0.2,(1,1,1)),(T(5)+0.4,(0,0,0))])
cp=panel(640,340,(0,25,0),rgb=(0.07,0.08,0.11),name='codep'); cp.parent=code
ct=text('AI 가 쓴 파이썬 프로그램',22,(-290,15,135),rgb=COL['accent'],align='LEFT'); ct.parent=code
src=['import ezdxf','doc = ezdxf.new()','msp = doc.modelspace()','profile = [(0,0), (8,0), ..., (18,60)]','msp.add_lwpolyline(profile)','add_dims(msp, "Ø30 h6", "R7", "60")','doc.saveas("burring_punch.dxf")']
for i,l in enumerate(src):
    o=text(' ',18,(-290,15,85-i*34),rgb=(0.55,0.95,0.6) if i<3 else COL['white'],bold=False,align='LEFT'); o.parent=code
    a_=T(5)+0.5+i*0.65; typewriter(o,l,a_,a_+0.6)
keyv(code,'scale',[(0,(0,0,0)),(T(5)-0.1,(0,0,0)),(T(5)+0.3,(1.05,1.05,1.05)),(T(5)+0.6,(1,1,1)),(E(5),(1,1,1)),(E(5)+0.5,(0,0,0))])
# --- 도면 (정면도+치수) ---
DX=700
dw=image_plane(os.path.join(HERE,'도면_1_버링펀치.png'),520,(DX,0,200),rot=(math.radians(90),0,0),name='dwg')
keyv(dw,'location',[(0,(DX,0,-300)),(T(6)+0.2,(DX,0,-300)),(T(6)+1.4,(DX,0,200))])
# 돋보기
mg=empty('mag',(DX-80,-30,180))
bpy.ops.mesh.primitive_torus_add(major_radius=32,minor_radius=4,location=(0,0,0),rotation=(math.radians(90),0,0)); ring=bpy.context.object; paint(ring,COL['accent']); ring.parent=mg; ring.location=(0,0,0)
hdl=cyl(4,60,(0,0,0),COL['accent'],rot=(0,math.radians(45),0)); hdl.parent=mg; hdl.location=(42,0,-42)
pos=[(DX-112,-30,190),(DX-112,-30,296),(DX-24,-30,85),(DX-112,-30,190)]
keyv(mg,'location',[(0,(DX-300,-30,-200)),(T(7)+0.2,(DX-300,-30,-200)),(T(7)+0.8,pos[0]),(T(8)+0.3,pos[0]),(T(8)+1.6,pos[1]),(T(8)+3.2,pos[2]),(T(8)+4.6,pos[3]),(E(8),pos[3]),(E(8)+0.8,(DX+400,-30,600))])
oks=[('Ø30 OK',(DX+40,-40,190)),('Ø36 OK',(DX+40,-40,296)),('R7 OK',(DX+70,-40,85))]
for i,(s_,p_) in enumerate(oks):
    o=text(s_,18,p_,rgb=(0.35,0.95,0.45)); show(o,T(8)+1.2+i*1.5,E(8)+0.5)
# 주고받기 말풍선
for i in range(4):
    left=i%2==0
    b=box((90,6,40),(DX+(-340 if left else 340),-60,330-i*60),COL['sky'] if left else COL['white'],bevel=10)
    show(b,T(9)+0.4+i*1.0)
done=text('도면 완성',40,(DX,-70,425),rgb=COL['accent']); show(done,T(9)+4.4)
# --- 카메라 ---
cam,tgt=camera(35)
cam_keys(cam,tgt,[(0,(PX-150,-560,ztop+300),(PX,0,ztop)),(T(1)+0.5,(PX-120,-460,ztop+220),(PX,0,ztop))])
orbit(cam,tgt,T(1)+0.5,E(2)-0.5,(PX,0,ztop-10),380,170,-110,-70,n=6)
cam_keys(cam,tgt,[(T(3)+0.4,(CX,-620,250),(CX,0,240)),(T(5)-0.3,(CX-40,-580,245),(CX,0,240)),(T(5)+1,(CX+30,-640,250),(CX,0,240)),(E(5),(CX+60,-600,250),(CX,0,240))])
cam_keys(cam,tgt,[(T(6)+1.2,(DX,-720,230),(DX,0,200)),(E(6),(DX,-680,220),(DX,0,200))])
cam_keys(cam,tgt,[(T(7)+0.6,(DX-60,-430,200),(DX-60,0,190)),(T(8)+1.6,(DX-60,-420,270),(DX-60,0,270)),(T(8)+3.2,(DX-10,-420,120),(DX-10,0,110)),(E(8),(DX-20,-480,210),(DX-20,0,200))])
cam_keys(cam,tgt,[(T(9)+1,(DX,-900,280),(DX,0,240)),(DUR,(DX+50,-980,300),(DX,0,240))])
sfx(T(3)-0.4,'pop',0.6); sfx(T(5)-0.1,'pop',0.6); sfx(T(6)+0.2,'whoosh',0.7); sfx(T(9)+4.4,'pop',0.7)
handheld(cam,0.5)
finish('ch1',DUR)
