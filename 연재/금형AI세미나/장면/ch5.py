import sys,os; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from s3d import *
T,E,DUR,cs=chapter(5)
sc=setup(texture=True)
floor(extent=2000)
S=4.0
die=revolve(DIE_P,'die',rgb=COL['die'],angle=270); die.scale=(S,)*3; die.rotation_euler=(0,0,math.radians(-45))
ztop=30*S
# 띠로 나눈 판재 (띠마다 색이 바뀜 = 변형 정도)
t=0.6; Ri=15.0; R=1.4; Rh=12.6; Ro=42.0; n=16
L=(Ri+t+R)-Rh
def topline(k,s0,s1,m=3):
    pts=[]
    for j in range(m+1):
        s=s0+(s1-s0)*j/m
        r0=Rh+L*s; z0=0
        d=(1-s)*L; arcL=R*math.pi/2
        if d<=arcL: a=d/R; r1=(Ri+t+R)-R*math.sin(a); z1=-(R-R*math.cos(a))
        else: r1=Ri+t; z1=-R-(d-arcL)
        pts.append((r0+(r1-r0)*k,z0+(z1-z0)*k))
    return pts
def jet(v):
    v=max(0,min(1,v))
    return (max(0,min(1,1.5-abs(4*v-3))),max(0,min(1,1.5-abs(4*v-2))),max(0,min(1,1.5-abs(4*v-1))))
bands=[]
wmat=mat((0.05,0.05,0.07),'wire')
def band(p0,p1,name,strain):
    me=bpy.data.meshes.new(name); bm=bmesh.new()
    vs=[bm.verts.new((r,0,z)) for r,z in p0]
    for a,b in zip(vs,vs[1:]+vs[:1]): bm.edges.new((a,b))
    bm.to_mesh(me); bm.free()
    o=bpy.data.objects.new(name,me); link(o); o.location=(0,0,ztop+t*S); o.scale=(S,)*3; o.rotation_euler=(0,0,math.radians(-45))
    o.shape_key_add(name='Basis'); sk=o.shape_key_add(name='burr')
    for i,(r,z) in enumerate(p1): sk.data[i].co=(r,0,z)
    md=o.modifiers.new('screw','SCREW'); md.axis='Z'; md.angle=math.radians(270); md.steps=72; md.render_steps=72; md.use_merge_vertices=True
    m=bpy.data.materials.new(name); m.diffuse_color=(*COL['sheet'],1); m.roughness=1; m.specular_intensity=0
    o.data.materials.append(m); o.data.materials.append(wmat)
    wf=o.modifiers.new('wf','WIREFRAME'); wf.thickness=0.035; wf.use_replace=False; wf.material_offset=1; wf.use_even_offset=True
    wf.show_render=False; wf.keyframe_insert('show_render',frame=1); wf.show_render=True; wf.keyframe_insert('show_render',frame=F(T(3)+0.3))
    smooth(o); bands.append((o,sk,m,strain)); return o
for i in range(n):
    s0,s1=i/n,(i+1)/n
    e=0.85*max(0,(1-s0*1.6))**2.0
    band(offset_loop(topline(0,s0,s1),t),offset_loop(topline(1,s0,s1),t),'b%d'%i,e)
flat0=[(Rh+L,0)]+[(Rh+L+(Ro-Rh-L)*j/6,0) for j in range(1,7)]
flat1=[(Ri+t+R,0)]+[(Ri+t+R+(Ro-Ri-t-R)*j/6,0) for j in range(1,7)]
band(offset_loop(flat0,t),offset_loop(flat1,t),'flat',0.02)
punch=revolve(PUNCH,'punch',rgb=COL['punch'],angle=270); punch.scale=(S,)*3; punch.rotation_euler=(0,0,math.radians(-45))
zp=ztop+t*S
keyv(punch,'location',[(0,(0,0,zp+200)),(T(1)+0.6,(0,0,zp+200)),(T(1)+2.0,(0,0,zp+2)),(T(3)+2.0,(0,0,zp+2)),(E(3)-0.4,(0,0,zp-5.6*S))])
for o,sk,m,e in bands:
    keyk(sk,[(0,0),(T(3)+2.0,0),(E(3)-0.4,1)])
    m.diffuse_color=(*COL['sheet'],1); m.keyframe_insert('diffuse_color',frame=F(T(4)-0.1))
    m.diffuse_color=(*jet(e/0.85),1); m.keyframe_insert('diffuse_color',frame=F(T(4)+1.2))
t1=text('성형해석',40,(-330,0,ztop+170),rgb=COL['accent']); show(t1,T(2)+0.1,E(3))
t2=text('그물망(격자)으로 나눠 계산',24,(-330,0,ztop+120),rgb=COL['white']); show(t2,T(3)+0.4,E(3)+0.3)
# 색 막대(범례)
lg=empty('legend',(330,0,ztop+20))
for i in range(10):
    b=box((26,6,14),(0,0,i*14),jet(i/9)); b.parent=lg
lt=text('많이 늘어남',20,(70,0,140),rgb=(1,0.35,0.3),align='LEFT'); lt.parent=lg
lt2=text('거의 그대로',20,(70,0,0),rgb=(0.4,0.6,1),align='LEFT'); lt2.parent=lg
keyv(lg,'scale',[(0,(0,0,0)),(T(4)+0.3,(0,0,0)),(T(4)+0.7,(1,1,1)),(E(6),(1,1,1)),(E(6)+0.3,(0,0,0))])
# 실제 결과 그림
im=image_plane(os.path.join(HERE,'해석_확대.png'),150,(150,-110,ztop+30),rot=(math.radians(90),0,math.radians(20)),name='res')
keyv(im,'scale',[(0,(0,0,0)),(T(5)+0.4,(0,0,0)),(T(5)+0.9,(1,1,1)),(E(6),(1,1,1)),(E(6)+0.3,(0,0,0))])
rt=text('실제 해석 결과 (버링 끝)',10,(150,-112,ztop+82),rot=(math.radians(90),0,math.radians(20)),rgb=COL['white']); show(rt,T(5)+0.6,E(6))
# 최대 얇아짐 10 % 게이지
g=empty('gauge',(0,-60,ztop+260))
bg=box((300,6,24),(0,0,0),(0.2,0.24,0.3)); bg.parent=g
fill=box((100,8,26),(-100,-1,0),(0.95,0.7,0.2)); fill.parent=g
for x,c_,s_ in ((-150+200,COL['accent'],'20 % 주의'),(150,COL['red'],'30 % 찢어짐')):
    mk=box((4,10,40),(x,-2,0),c_); mk.parent=g; tt=text(s_,14,(x,-2,32),rgb=c_); tt.parent=g
gt=text('최대 얇아짐 10.2 %',30,(-50,-4,-44),rgb=(0.4,1,0.5)); gt.parent=g
keyv(g,'scale',[(0,(0,0,0)),(T(6)+0.1,(0,0,0)),(T(6)+0.5,(1,1,1)),(E(6),(1,1,1)),(E(6)+0.3,(0,0,0))])
# 하중 막대
FX=900
bars=[('버링',19.5,COL['sky']),('리스트라이크',78.2,COL['purple'])]
for i,(nm,kn,c_) in enumerate(bars):
    x=FX+i*220; h=kn*4
    bpy.ops.mesh.primitive_cube_add(size=1,location=(x,0,0)); b=bpy.context.object; b.scale=(120,120,h)
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    me=b.data
    for v in me.vertices: v.co.z+=h/2
    paint(b,c_); b.select_set(False)
    keyv(b,'scale',[(0,(1,1,0)),(T(8)+0.2+i*1.6,(1,1,0)),(T(8)+1.4+i*1.6,(1,1,1))])
    tl=text(nm,26,(x,-70,-0),rgb=COL['white']); tl.location=(x,-70,h+70); show(tl,T(8)+1.0+i*1.6)
    tv=text('%.0f kN'%round(kn),34,(x,-70,h+30),rgb=COL['accent']); show(tv,T(8)+1.2+i*1.6)
ft=text('누르는 힘',36,(FX+110,-70,520),rgb=COL['white']); show(ft,T(7)+0.2)
# 프레스 틀
pr=empty('press',(FX+110,0,0))
for x in (-260,260):
    c=box((50,120,560),(x,40,280),(0.36,0.40,0.46)); c.parent=pr
tp=box((570,140,70),(0,40,595),(0.36,0.40,0.46)); tp.parent=pr
bs=box((570,160,30),(0,40,15),(0.30,0.34,0.40)); bs.parent=pr
keyv(pr,'location',[(0,(FX+110,0,-900)),(T(9)+0.1,(FX+110,0,-900)),(T(9)+1.0,(FX+110,0,0))])
pt=text('프레스 크기 · 금형 강도 확인',26,(FX+110,-90,690),rgb=COL['accent']); show(pt,T(9)+1.2)
# 카메라
cam,tgt=camera(35)
cam_keys(cam,tgt,[(0,(-300,-700,420),(0,0,ztop)),(T(1)+2,(-260,-620,300),(0,0,ztop))])
orbit(cam,tgt,T(1)+2,E(3),(0,0,ztop+20),640,200,-115,-80,n=6)
cam_keys(cam,tgt,[(T(4)+0.8,(-40,-700,330),(0,0,ztop+40)),(E(4),(0,-680,320),(0,0,ztop+40))])
cam_keys(cam,tgt,[(T(5)+1.0,(-30,-370,ztop+60),(40,-64,ztop+5)),(E(5),(-10,-360,ztop+55),(45,-64,ztop+5))])
cam_keys(cam,tgt,[(T(6)+0.6,(-40,-700,ztop+260),(0,0,ztop+150)),(E(6),(-20,-680,ztop+250),(0,0,ztop+150))])
cam_keys(cam,tgt,[(T(7)+0.9,(FX+110,-1150,300),(FX+110,0,230)),(E(8),(FX+130,-1100,400),(FX+110,0,260))])
cam_keys(cam,tgt,[(T(9)+0.8,(FX+110,-1500,560),(FX+110,0,330)),(E(9),(FX+130,-1550,580),(FX+110,0,330))])
# 설계에 해석 쓰기: 다이 모서리 R 키우기 → 재해석 → 얇아짐 줄어듦 (예시)
DX_=-1300; SD=5.0
def die_prof(R):
    return [(15.6+R,0+0),(24,0),(24,30)]+[(15.6+R-R*math.sin(a),30-R+R*math.cos(a)) for a in [math.radians(90*k/8) for k in range(9)]][::-1][:-1]+[(15.6,30-R)] if False else \
           [(15.6,0),(24,0),(24,30)]+[(15.6+R+R*math.cos(math.radians(90+90*k/8)),30-R+R*math.sin(math.radians(90+90*k/8))) for k in range(9)]
dA=die_prof(0.8); dB=die_prof(2.5)
dd=loop_obj(dA,'rdie',COL['die'],angle=270,seg=96,loc=(DX_,0,0),scale=SD)
kR=add_key(dd,'R',dB)
keyk(kR,[(0,0),(T(10)+1.6,0),(T(10)+3.2,1)])
show(dd,T(10)-0.3,base=(SD,SD,SD))
# 판 꺾이는 곳 표시 고리: 빨강 → 노랑 → 초록
bpy.ops.mesh.primitive_torus_add(major_radius=16.2*SD,minor_radius=0.9*SD,location=(DX_,0,30*SD+0.3*SD)); hot=bpy.context.object; hot.name='hot'; hot.select_set(False)
hm_=bpy.data.materials.new('hot'); hm_.diffuse_color=(0.95,0.2,0.15,1); hot.data.materials.append(hm_)
hot.rotation_euler=(0,0,0)
show(hot,T(10)+0.2,base=(1,1,1))
for t_,c_ in ((T(10)+0.3,(0.95,0.2,0.15)),(T(10)+1.6,(0.95,0.2,0.15)),(T(10)+3.4,(1,0.85,0.2)),(T(10)+4.6,(0.3,0.9,0.4))):
    hm_.diffuse_color=(*c_,1); hm_.keyframe_insert('diffuse_color',frame=F(t_))
rt_=text(' ',30,(DX_,-180,260),rgb=COL['accent']); text_seq(rt_,[(T(10)+0.4,'다이 모서리 R 0.8'),(T(10)+2.4,'다이 모서리 R 0.8 → 2.5'),(DUR+1,' ')])
ex=text('(예시)',16,(DX_+230,-180,260),rgb=(0.7,0.75,0.85)); show(ex,T(10)+0.4)
lp_=text('해석 → 설계 수정 → 재해석',24,(DX_,-180,215),rgb=COL['white']); show(lp_,T(10)+1.2)
th_=text(' ',22,(DX_,-180,175),rgb=(0.4,1,0.5)); text_seq(th_,[(T(10)+3.6,'얇아짐 줄어듦 → 설계 확정'),(DUR+1,' ')])
cyc=empty('cyc',(DX_+260,-120,120))
for k in range(3):
    a0_=k*2*math.pi/3
    arc_=curve_line([(70*math.cos(a0_+j*0.08),0,70*math.sin(a0_+j*0.08)) for j in range(22)],bevel=3,rgb=COL['accent']); arc_.parent=cyc
keyv(cyc,'scale',[(0,(0,0,0)),(T(10)+1.2,(0,0,0)),(T(10)+1.5,(1,1,1))])
keyv(cyc,'rotation_euler',[(T(10)+1.2,(0,0,0)),(DUR,(0,math.radians(-540),0))])
cam_keys(cam,tgt,[(T(10)+0.6,(DX_-40,-980,330),(DX_+90,0,180)),(T(10)+2.6,(DX_-60,-900,300),(DX_+70,0,170)),(DUR,(DX_-20,-950,320),(DX_+90,0,180))])
sfx(T(10)+0.2,'whoosh',0.9); sfx(T(10)+3.6,'pop',0.8)
sfx(T(5)+0.4,'whoosh',0.8); sfx(T(7)+0.3,'whoosh',0.8); sfx(T(9)+0.9,'click',1.0)
handheld(cam,0.5)
finish('ch5',DUR)
