"""가공 설비 영상 전용 부품: 사람·카드·표·OK/X·고속가공기·와이어커팅기·AI 구슬"""
from s3d import *
def person(loc,col=(0.62,0.42,0.95),name='person',scale=1.0):
    g=empty(name,loc); g.scale=(scale,)*3
    b=cyl(22,90,(0,0,45),col,seg=24); b.parent=g
    h=sphere(20,(0,0,112),(0.95,0.82,0.70)); h.parent=g
    hat=cyl(21,8,(0,0,128),col,seg=24); hat.parent=g
    for sx in (-1,1):
        a=box((10,10,60),(sx*28,0,60),col); a.parent=g
    return g
def ai_orb(loc,r=50,name='ai'):
    g=empty(name,loc); s=sphere(r,(0,0,0),COL['sky']); s.parent=g
    for k,ang in enumerate((0,60,120)):
        bpy.ops.mesh.primitive_torus_add(major_radius=r*1.55,minor_radius=r*0.05,location=(0,0,0),rotation=(math.radians(90),math.radians(ang),0))
        t=bpy.context.object; paint(t,COL['accent']); t.parent=g; t.select_set(False)
    tx=text('AI',r*0.75,(0,-r*1.05,0),rgb=COL['ink']); tx.parent=g
    return g
def card(title,sub,loc,col=COL['accent'],w=150,h=90,name='card',tsize=24,ssize=12,face=None):
    g=empty(name,loc)
    b=box((w,6,h),(0,0,0),(0.10,0.13,0.18),bevel=4); b.parent=g
    st=box((w,7,12),(0,-0.5,h/2-6),col); st.parent=g
    t1=text(title,tsize,(0,-5,h*0.08),rgb=col); t1.parent=g
    if sub:
        t2=text(sub,ssize,(0,-5,-h*0.28),rgb=COL['white'],bold=False); t2.parent=g
    g['h']=h
    if face is not None:
        tr=g.constraints.new('TRACK_TO'); tr.target=face; tr.track_axis='TRACK_NEGATIVE_Y'; tr.up_axis='UP_Z'
    return g
def table(loc,cols,rows,colx,w=700,rh=30,head=(0.16,0.22,0.34),name='tbl',size=13,t0=0,dt=0.4,hdr_t=None):
    g=empty(name,loc)
    n=len(rows); H=rh*(n+1)+20
    bg=box((w+20,8,H),(0,8,-H/2+rh),(0.08,0.10,0.15),bevel=4); bg.parent=g
    hb=box((w,9,rh-4),(0,2,0),head); hb.parent=g
    for c,x in zip(cols,colx):
        o=text(c,size,(x,-4,0),rgb=(0.85,0.9,1.0),align='LEFT'); o.parent=g
    objs=[]
    for i,r in enumerate(rows):
        z=-(i+1)*rh
        rb=box((w,9,rh-4),(0,2,z),(0.93,0.95,0.98) if i%2==0 else (0.85,0.89,0.95)); rb.parent=g
        line=[rb]
        for c,x in zip(r,colx):
            o=text(c,size,(x,-4,z),rgb=COL['ink'],bold=False,align='LEFT'); o.parent=g; line.append(o)
        for o in line:
            s0=tuple(o.scale); keyv(o,'scale',[(0,(0,0,0)),(t0+i*dt-0.05,(0,0,0)),(t0+i*dt+0.2,s0)])
        objs.append(line)
    return g
def mark(ok,loc,size=40,name='mark'):
    return text('OK' if ok else 'X',size,loc,rgb=(0.35,1,0.45) if ok else COL['red'],name=name)
def vmc(loc,name='vmc'):
    """고속가공기(머시닝센터) 모형 → (묶음, 주축 머리 empty, 테이블 위 높이)"""
    g=empty(name,loc)
    base=box((520,360,120),(0,0,60),(0.42,0.46,0.52),bevel=6); base.parent=g
    col=box((220,160,560),(0,140,400),(0.46,0.50,0.56),bevel=6); col.parent=g
    tbl=box((420,240,30),(0,-20,135),(0.30,0.33,0.38),bevel=2); tbl.parent=g
    head=empty(name+'_head',(0,-10,380)); head.parent=g
    hb=box((140,140,180),(0,40,60),(0.95,0.95,0.97),bevel=8); hb.parent=head
    sp=cyl(30,70,(0,0,-30),(0.55,0.58,0.64)); sp.parent=head
    return g,head,150
def wire_edm(loc,name='wedm'):
    """와이어커팅기 모형 → (묶음, 위 가이드 empty, 작업 높이)"""
    g=empty(name,loc)
    base=box((560,380,140),(0,0,70),(0.40,0.44,0.50),bevel=6); base.parent=g
    tank=box((420,300,60),(0,-10,170),(0.25,0.45,0.60),bevel=4); tank.parent=g
    arm_l=box((80,80,120),(0,150,200),(0.46,0.50,0.56)); arm_l.parent=g
    col=box((120,120,500),(0,190,390),(0.46,0.50,0.56),bevel=6); col.parent=g
    up=empty(name+'_up',(0,0,470)); up.parent=g
    ua=box((90,190,60),(0,95,0),(0.95,0.95,0.97),bevel=6); ua.parent=up
    return g,up,200
