"""세미나 3D 장면 공통 도구 (Blender 4.2, Workbench 렌더)
솔리드·불투명·재질 색, 자동 스무스 30°, 상형 펀치 파랑 / 하형 다이 초록 / 판재 주황"""
import bpy, bmesh, math, os, sys, json, glob
from mathutils import Vector, Euler
HERE=os.path.dirname(os.path.abspath(__file__))
FPS=24
FONT_B='/usr/share/fonts/truetype/nanum/NanumGothicExtraBold.ttf'
FONT_R='/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf'
DIE='/home/user/mold_sold/parts/TEST_BEARING_SEAL_430/die_set'
COL=dict(punch=(0.18,0.42,0.92),die=(0.20,0.68,0.32),sheet=(1.0,0.50,0.10),plate=(0.62,0.65,0.70),plate2=(0.48,0.52,0.58),
         shoe=(0.36,0.40,0.46),post=(0.85,0.86,0.88),spring=(0.95,0.78,0.20),white=(0.95,0.95,0.96),paper=(0.97,0.97,0.95),
         ink=(0.08,0.10,0.14),accent=(1.0,0.78,0.20),red=(0.92,0.22,0.20),sky=(0.35,0.75,1.0),dark=(0.13,0.16,0.21),purple=(0.62,0.42,0.95))
ARGS=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []

def setup(bg=(0.055,0.07,0.10), res=(1920,1080), texture=False, outline=True):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc=bpy.context.scene; sc.render.engine='BLENDER_WORKBENCH'
    sc.render.resolution_x,sc.render.resolution_y=res; sc.render.resolution_percentage=100; sc.render.fps=FPS
    sh=sc.display.shading; sh.light='STUDIO'; sh.color_type='TEXTURE' if texture else 'MATERIAL'
    sh.show_shadows=True; sh.shadow_intensity=0.35; sh.show_cavity=True; sh.cavity_type='WORLD'; sh.cavity_ridge_factor=0.6; sh.cavity_valley_factor=0.8
    sh.show_specular_highlight=False; sh.show_object_outline=outline; sh.object_outline_color=(0.02,0.02,0.03); sh.show_xray=False
    sc.display.shadow_focus=0.6; sc.display.light_direction=(0.45,-0.35,0.82)
    sc.display.render_aa='5'
    w=bpy.data.worlds.new('W'); sc.world=w; w.color=bg
    sc.render.image_settings.file_format='PNG'; sc.render.image_settings.color_mode='RGB'
    sc.view_settings.view_transform='Standard'
    return sc

_mats={}
def mat(rgb,name=None):
    key=(name or '')+str(rgb)
    if key in _mats: return _mats[key]
    m=bpy.data.materials.new(name or 'm'); m.diffuse_color=(*rgb,1); m.blend_method='OPAQUE'
    m.roughness=1.0; m.metallic=0.0; m.specular_intensity=0.0; _mats[key]=m; return m
def paint(o,rgb):
    o.data.materials.clear(); o.data.materials.append(mat(rgb)); return o
def smooth(o,ang=30):
    """각진 모서리(30° 넘게 꺾인 곳)는 날카롭게, 둥근 면만 부드럽게: 모든 면 smooth + Edge Split 30°"""
    if o.type!='MESH': return o
    for p in o.data.polygons: p.use_smooth=True
    if 'es' not in o.modifiers:
        m=o.modifiers.new('es','EDGE_SPLIT'); m.split_angle=math.radians(ang); m.use_edge_sharp=True
    return o
def link(o,parent=None):
    bpy.context.scene.collection.objects.link(o)
    if parent: o.parent=parent
    return o
def empty(name='E',loc=(0,0,0)):
    e=bpy.data.objects.new(name,None); e.location=loc; return link(e)

def revolve(profile,name='rev',seg=96,angle=360.0,rgb=COL['punch'],loc=(0,0,0),closed=None):
    if closed is None: closed=profile[0][0]>0.01 and profile[-1][0]>0.01
    """profile = [(r,z)...] 반쪽 단면 (열린 선) → Z축 회전체. 같은 메쉬에 Screw 수정자(angle 키 가능)"""
    me=bpy.data.meshes.new(name); bm=bmesh.new()
    vs=[bm.verts.new((r,0,z)) for r,z in profile]
    for a,b in zip(vs,vs[1:]): bm.edges.new((a,b))
    if closed: bm.edges.new((vs[-1],vs[0]))
    bm.to_mesh(me); bm.free()
    o=bpy.data.objects.new(name,me); link(o); o.location=loc
    m=o.modifiers.new('screw','SCREW'); m.axis='Z'; m.angle=math.radians(angle); m.steps=seg; m.render_steps=seg
    m.use_merge_vertices=True; m.merge_threshold=0.01; m.use_normal_calculate=True; m.use_smooth_shade=False
    paint(o,rgb); smooth(o)
    if 89<angle<359: cut(o,angle)
    return o
def apply_mods(o):
    dg=bpy.context.evaluated_depsgraph_get(); me=bpy.data.meshes.new_from_object(o.evaluated_get(dg))
    o.modifiers.clear(); o.data=me; smooth(o); return o

def stl(path,rgb,name=None):
    bpy.ops.wm.stl_import(filepath=path); o=bpy.context.selected_objects[0]
    if name: o.name=name
    paint(o,rgb); smooth(o); o.select_set(False); return o

def text(s,size=10,loc=(0,0,0),rot=(math.radians(90),0,0),rgb=COL['white'],bold=True,align='CENTER',extrude=0.0,name='T'):
    cu=bpy.data.curves.new(name,'FONT'); cu.body=s; cu.font=bpy.data.fonts.load(FONT_B if bold else FONT_R,check_existing=True)
    cu.size=size; cu.align_x=align; cu.align_y='CENTER'; cu.extrude=extrude
    o=bpy.data.objects.new(name,cu); link(o); o.location=loc; o.rotation_euler=rot
    o.data.materials.append(mat(rgb)); return o
def box(size,loc=(0,0,0),rgb=COL['plate'],name='box',bevel=0):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc); o=bpy.context.object; o.name=name; o.scale=size
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    if bevel: m=o.modifiers.new('bv','BEVEL'); m.width=bevel; m.segments=3
    paint(o,rgb); o.select_set(False); return o
def cyl(r,h,loc=(0,0,0),rgb=COL['plate'],seg=64,name='cyl',rot=(0,0,0)):
    bpy.ops.mesh.primitive_cylinder_add(radius=r,depth=h,vertices=seg,location=loc,rotation=rot); o=bpy.context.object; o.name=name
    paint(o,rgb); smooth(o); o.select_set(False); return o
def sphere(r,loc=(0,0,0),rgb=COL['accent'],name='sph'):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r,location=loc,segments=24,ring_count=12); o=bpy.context.object; o.name=name
    paint(o,rgb); smooth(o); o.select_set(False); return o
def image_plane(path,width,loc=(0,0,0),rot=(math.radians(90),0,0),name='img'):
    img=bpy.data.images.load(path); w,h=img.size
    bpy.ops.mesh.primitive_plane_add(size=1,location=loc,rotation=rot); o=bpy.context.object; o.name=name
    o.scale=(width,width*h/w,1); bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    m=bpy.data.materials.new(name); m.use_nodes=True; nt=m.node_tree; bsdf=nt.nodes['Principled BSDF']
    tex=nt.nodes.new('ShaderNodeTexImage'); tex.image=img; nt.links.new(tex.outputs['Color'],bsdf.inputs['Base Color'])
    m.diffuse_color=(1,1,1,1); o.data.materials.append(m); o.select_set(False); return o
def curve_line(pts,bevel=0.4,rgb=COL['ink'],name='ln',closed=False):
    cu=bpy.data.curves.new(name,'CURVE'); cu.dimensions='3D'; cu.bevel_depth=bevel; cu.bevel_resolution=2
    sp=cu.splines.new('POLY'); sp.points.add(len(pts)-1)
    for p,c in zip(sp.points,pts): p.co=(*c,1)
    sp.use_cyclic_u=closed
    o=bpy.data.objects.new(name,cu); link(o); o.data.materials.append(mat(rgb)); return o

# ---------- 시간·키 ----------
def F(t): return int(round(t*FPS))+1
def key(o,attr,t,val,interp=None):
    setattr(o,attr,val) if not isinstance(val,(tuple,list)) else setattr(o,attr,type(getattr(o,attr))(val) if not hasattr(getattr(o,attr),'__len__') else val)
    o.keyframe_insert(attr,frame=F(t))
    if interp:
        ad=o.animation_data
        for fc in ad.action.fcurves:
            if fc.data_path==attr:
                for kp in fc.keyframe_points:
                    if abs(kp.co.x-F(t))<0.5: kp.interpolation=interp
def keyv(o,attr,keys,interp=None):
    for t,v in keys: key(o,attr,t,v,interp)
def show(o,t_in,t_out=None,grow=0.35,base=None):
    """나타남: 크기 0 → 원래(조금 튀는 게임식), 사라짐: 원래 → 0"""
    s=tuple(base or o.scale)
    key(o,'scale',0,(0,0,0)); key(o,'scale',max(0,t_in-0.001),(0,0,0))
    key(o,'scale',t_in+grow*0.7,tuple(v*1.08 for v in s)); key(o,'scale',t_in+grow,s)
    if t_out is not None:
        key(o,'scale',t_out,s); key(o,'scale',t_out+grow,(0,0,0))
def typewriter(o,full,t0,t1,keep_until=None):
    st=bpy.context.scene
    def h(scene,*a):
        t=(scene.frame_current-1)/FPS
        n=0 if t<t0 else len(full) if t>=t1 else int(len(full)*(t-t0)/max(1e-6,t1-t0))
        o.data.body=full[:n] if n>0 else ' '
    bpy.app.handlers.frame_change_pre.append(h)

# ---------- 카메라 (게임식: 부드러운 가감속 + 살짝 흔들림) ----------
def camera(lens=35,name='Cam'):
    c=bpy.data.cameras.new(name); c.lens=lens; c.clip_start=1; c.clip_end=20000
    o=bpy.data.objects.new(name,c); link(o); bpy.context.scene.camera=o
    tgt=empty('CamTarget'); tr=o.constraints.new('TRACK_TO'); tr.target=tgt; tr.track_axis='TRACK_NEGATIVE_Z'; tr.up_axis='UP_Y'
    return o,tgt
def cam_keys(cam,tgt,keys):
    """keys = [(t, (x,y,z) 카메라, (x,y,z) 바라볼 곳, lens 또는 None)]"""
    for k in keys:
        t,p,q=k[:3]; key(cam,'location',t,p); key(tgt,'location',t,q)
        if len(k)>3 and k[3]: cam.data.lens=k[3]; cam.data.keyframe_insert('lens',frame=F(t))
def orbit(cam,tgt,t0,t1,center,radius,h,a0,a1,n=12,lens=None):
    for i in range(n+1):
        a=math.radians(a0+(a1-a0)*i/n); t=t0+(t1-t0)*i/n
        key(cam,'location',t,(center[0]+radius*math.cos(a),center[1]+radius*math.sin(a),center[2]+h))
    key(tgt,'location',t0,center); key(tgt,'location',t1,center)
    if n:
        for fc in cam.animation_data.action.fcurves:
            for kp in fc.keyframe_points:
                if F(t0)<kp.co.x<F(t1): kp.interpolation='LINEAR'
def handheld(cam,amp=0.4):
    for fc in cam.animation_data.action.fcurves:
        if fc.data_path=='location':
            m=fc.modifiers.new('NOISE'); m.scale=60; m.strength=amp; m.phase=fc.array_index*7.3

def timing(project):
    return json.load(open(project,encoding='utf-8'))
def render(out_dir,f0,f1,step=1):
    sc=bpy.context.scene; os.makedirs(out_dir,exist_ok=True)
    for f in range(f0,f1+1,step):
        p=os.path.join(out_dir,'f%05d.png'%f)
        if os.path.exists(p): continue
        sc.frame_set(f); sc.render.filepath=p; bpy.ops.render.render(write_still=True)

# ---------- 장(챕터) 시간 ----------
PROJ=os.path.join(os.path.dirname(HERE),'금형AI세미나_시간.json')
def chapter(ch):
    tim=json.load(open(PROJ,encoding='utf-8')); segs=tim['segs']
    idx=[i for i,s in enumerate(segs) if s['kind']=='chapter']
    a=idx[ch]; b=idx[ch+1] if ch+1<len(idx) else len(segs)
    cs=segs[a:b]; T0=0.0 if ch==0 else cs[0]['t0']; end=segs[b]['t0'] if b<len(segs) else tim['duration']
    global _T0; _T0=T0
    T=lambda i: cs[i]['t0']-T0
    E=lambda i: cs[i]['t0']+cs[i]['dur']-T0
    return T,E,end-T0,cs
SFX=[]; _T0=0.0
def sfx(t,kind='whoosh',vol=1.0):
    """효과음 자리 (장 안의 시각): whoosh=휙 · slow=불릿 타임 · click=딸깍 · pop=톡"""
    SFX.append({'t':round(_T0+t,3),'kind':kind,'vol':vol})
def finish(name,dur):
    sc=bpy.context.scene; sc.frame_start=1; sc.frame_end=F(dur)
    os.makedirs(os.path.join(HERE,'_sfx'),exist_ok=True)
    json.dump(SFX,open(os.path.join(HERE,'_sfx',name+'.json'),'w'),indent=0)
    if '--sfx' in ARGS: return
    a=ARGS
    if '--save' in a: bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE,name+'.blend'))
    if '--test' in a:
        sc.render.resolution_percentage=50
        ts=[float(x) for x in a[a.index('--test')+1].split(',')] if len(a)>a.index('--test')+1 and a[a.index('--test')+1][0].isdigit() else [dur*k/5 for k in (0.5,1.5,2.5,3.5,4.5)]
        od=os.path.join(HERE,'_test',name); os.makedirs(od,exist_ok=True)
        for t in ts:
            sc.frame_set(F(t)); sc.render.filepath=os.path.join(od,'t%06.1f.png'%t); bpy.ops.render.render(write_still=True)
    if '--render' in a:
        i=a.index('--render'); f0=int(a[i+1]); f1=min(int(a[i+2]),sc.frame_end); step=int(a[i+3]) if len(a)>i+3 and a[i+3].isdigit() else 1
        render(os.path.join(HERE,'_frames',name),f0,f1,step)

# ---------- 공통 모양 ----------
def arcpts(cx,cy,R,a0,a1,n=10):
    return [(cx+R*math.cos(math.radians(a0+(a1-a0)*i/n)),cy+R*math.sin(math.radians(a0+(a1-a0)*i/n))) for i in range(n+1)]
PUNCH=[(0,0),(8,0)]+arcpts(8,7,7,-90,0)[1:]+[(15,54),(18,54),(18,59.5),(17.5,60),(0,60)]
DIE_P=[(15.6,0),(24,0),(24,30),(16.6,30),(15.6,29)]
def seal_profile(H=4.0,t=0.6,Ro=26.0,Ri=15.0,R=1.4):
    """베어링 씰 반쪽 단면(닫힌 고리): 바깥 평판(위) + 안쪽으로 아래로 꺾인 플랜지"""
    out=[(Ro,H),(Ri+t+R,H)]+arcpts(Ri+t+R,H-R,R,90,180,8)[1:]+[(Ri+t,0)]
    inn=[(Ri,0)]+[p for p in arcpts(Ri+t+R,H-R,R+t,180,90,8)][1:]+[(Ro,H+t)]
    # 바깥 선: 위면 (Ro,H+t) → 안쪽 아래, 안 선: 아래면
    top=[(Ro,H+t),(Ri+t+R,H+t)]+arcpts(Ri+t+R,H-R,R+t,90,180,8)[1:]+[(Ri,0)]
    bot=[(Ri+t,0)]+arcpts(Ri+t+R,H-R,R,180,90,8)[1:]+[(Ro,H)]
    return top+bot
def burr_sheet_profile(k,H=4.0,t=0.6,Ro=30.0,Rh=12.6,Ri=15.0,R=1.4):
    """k=0 평판(구멍 반지름 Rh) → k=1 버링 끝(플랜지 아래로). 같은 점 수 (모양 키용)"""
    n=24
    pts_top=[];pts_bot=[]
    import math as m
    L=Ri+t+R-Rh       # 꺾이는 길이
    for i in range(n+1):
        s=i/n
        # 평판: r 이 Rh→(Ri+t+R)
        r0=Rh+L*s; z0=H
        # 버링: 꺾인 곡선 (s=1 이 바깥 평판 쪽)
        ang=m.radians(180-90*s) if s>0.35 else None
        if s<=0.35:
            z1=H-R-(H-R)*(1-s/0.35); r1=Ri+t
        else:
            a=m.radians(180-90*(s-0.35)/0.65); r1=Ri+t+R+R*m.cos(a); z1=H-R+R*m.sin(a)
        r=r0+(r1-r0)*k; z=z0+(z1-z0)*k
        pts_top.append((r,z))
    return pts_top

def floor(size=30000,z=0,rgb=(0.09,0.11,0.15),grid=True,step=50,gz=0.05,grgb=(0.16,0.19,0.25),extent=None):
    bpy.ops.mesh.primitive_plane_add(size=size,location=(0,0,z)); o=bpy.context.object; o.name='floor'; paint(o,rgb); o.select_set(False)
    if grid:
        e=extent or size/2
        n=int(e//step)
        for i in range(-n,n+1):
            curve_line([(i*step,-e,z+gz),(i*step,e,z+gz)],bevel=0.25,rgb=grgb,name='g')
            curve_line([(-e,i*step,z+gz),(e,i*step,z+gz)],bevel=0.25,rgb=grgb,name='g')
    return o
def pedestal(loc,r=40,h=8,rgb=(0.20,0.24,0.31)):
    o=cyl(r,h,(loc[0],loc[1],loc[2]+h/2),rgb,seg=64,name='ped')
    bpy.ops.mesh.primitive_torus_add(major_radius=r,minor_radius=1.6,location=(loc[0],loc[1],loc[2]+h),major_segments=96)
    t=bpy.context.object; paint(t,COL['accent']); smooth(t); t.select_set(False); return o
def spin(o,t0,t1,turns=1.0,axis=2):
    r=list(o.rotation_euler); a=r[axis]
    r0=list(r); r1=list(r); r1[axis]=a+2*math.pi*turns
    key(o,'rotation_euler',t0,tuple(r0)); key(o,'rotation_euler',t1,tuple(r1))
    for fc in o.animation_data.action.fcurves:
        if fc.data_path=='rotation_euler':
            for kp in fc.keyframe_points: kp.interpolation='LINEAR'

def offset_loop(top,t):
    """윗선(점 목록) → 두께 t 만큼 아래(법선 방향)로 띄운 선을 붙여 닫힌 고리"""
    import math as m
    bot=[]
    n=len(top)
    for i in range(n):
        a=top[max(0,i-1)]; b=top[min(n-1,i+1)]
        dx,dz=b[0]-a[0],b[1]-a[1]; L=m.hypot(dx,dz) or 1
        nx,nz=dz/L,-dx/L      # 진행 방향의 오른쪽(아래) 법선
        bot.append((top[i][0]+nx*t,top[i][1]+nz*t))
    return top+bot[::-1]
def burr_sheet(Ro=60.0,Rh=12.6,H=0.0,t=0.6,Ri=15.0,R=1.4,flange=None,name='sheet',seg=128,rgb=COL['sheet'],loc=(0,0,0),scale=1.0,n=24):
    """구멍 뚫린 평판 → 모양 키 'burr' (0→1) 로 구멍 가장자리가 아래로 서는 판 (Z축 회전체)"""
    import math as m
    L=(Ri+t+R)-Rh; Lf=flange if flange is not None else L
    def top(k):
        pts=[]
        for i in range(n+1):
            s=i/n
            # 평판 상태: 구멍 끝 Rh → Ri+t+R
            r0=Rh+L*s; z0=0
            # 버링 상태: 아래로 선 벽(길이 Lf-R*pi/2) + 둥근 모서리
            wall=max(0.0,Lf-R*m.pi/2); arcL=R*m.pi/2; d=(1-s)*Lf  # 바깥(굽힘 시작)에서 끝까지 거리
            if d<=arcL:
                a=d/R; r1=(Ri+t+R)-R*m.sin(a); z1=-(R-R*m.cos(a))
            else:
                r1=Ri+t; z1=-R-(d-arcL)
            pts.append((r0+(r1-r0)*k,z0+(z1-z0)*k))
        pts.append((Ro,0))
        return pts
    p0=offset_loop(top(0),t); p1=offset_loop(top(1),t)
    me=bpy.data.meshes.new(name); bm=bmesh.new()
    vs=[bm.verts.new((r,0,z)) for r,z in p0]
    for a,b in zip(vs,vs[1:]+vs[:1]): bm.edges.new((a,b))
    bm.to_mesh(me); bm.free()
    o=bpy.data.objects.new(name,me); link(o); o.location=loc; o.scale=(scale,)*3
    o.shape_key_add(name='Basis'); sk=o.shape_key_add(name='burr')
    for i,(r,z) in enumerate(p1): sk.data[i].co=(r,0,z)
    md=o.modifiers.new('screw','SCREW'); md.axis='Z'; md.steps=seg; md.render_steps=seg; md.use_merge_vertices=True; md.merge_threshold=0.001
    paint(o,rgb); smooth(o); return o,sk
def keyk(sk,keys):
    for t,v in keys: sk.value=v; sk.keyframe_insert('value',frame=F(t))
def panel(w,h,loc,rgb=(0.12,0.15,0.2),rot=(math.radians(90),0,0),name='panel',edge=COL['accent']):
    o=box((w,4,h),loc,rgb,bevel=3,name=name); o.rotation_euler=(0,0,rot[2])
    return o

UPPER_KEYS=('upper_shoe','punch_backing','punch_plate','stripper','guide_bush','_punch','pilot_','pilot_pierce')
def die_set(loc=(0,0,0),skip_springs=False,wire=False):
    """시험용 베어링 씰 금형 세트 STL 101개 → (부품 목록[(obj,'upper'|'lower'|'strip')], 상형 묶음 empty)"""
    root=empty('dieset',loc); up=empty('upper',(0,0,0)); up.parent=root
    parts=[]
    for f in sorted(glob.glob(os.path.join(DIE,'*.stl'))):
        n=os.path.basename(f)[:-4]
        if n=='product_out': continue
        if skip_springs and 'spring' in n: continue
        if n=='strip' or n.startswith('strip_part'): rgb=COL['sheet']; g='strip'
        elif 'punch' in n and 'plate' not in n and 'backing' not in n: rgb=COL['punch']; g='upper'
        elif n.endswith('_die') or '_die_' in n or n.endswith('_pad'): rgb=COL['die']; g='lower'
        elif 'shoe' in n or 'parallel' in n: rgb=COL['shoe']; g='upper' if 'upper' in n else 'lower'
        elif 'spring' in n: rgb=COL['spring']; g='upper' if 'stripper' in n else 'lower'
        elif 'guide_post' in n or 'pilot' in n or 'bolt' in n: rgb=COL['post']; g='upper' if ('pilot' in n or 'bolt' in n) else 'lower'
        elif 'bush' in n: rgb=(0.80,0.62,0.30); g='upper'
        elif 'lifter' in n: rgb=COL['sky']; g='lower'
        elif 'backing' in n: rgb=COL['plate2']; g='upper' if 'punch' in n or 'stripper' in n else 'lower'
        else: rgb=COL['plate']; g='upper' if any(k in n for k in ('punch_plate','stripper')) else 'lower'
        o=stl(f,rgb,n); o.parent=up if g=='upper' else root
        if wire and any(k in n for k in ('shoe','plate','backing','parallel')) and 'punch_' not in n.replace('punch_plate','').replace('punch_backing',''):
            me=o.data; bm=bmesh.new(); bm.from_mesh(me)
            bmesh.ops.dissolve_limit(bm,angle_limit=math.radians(1),verts=bm.verts,edges=bm.edges); bm.to_mesh(me); bm.free()
            wm=o.modifiers.new('wire','WIREFRAME'); wm.thickness=1.2; wm.use_replace=True; wm.use_even_offset=True; wm.show_render=False; wm.show_viewport=False
            o['plate']=1
        parts.append((o,g))
    return parts,up,root

def draw_on(o,t0,t1):
    cu=o.data; cu.bevel_factor_end=0.0; cu.keyframe_insert('bevel_factor_end',frame=F(0)); cu.keyframe_insert('bevel_factor_end',frame=F(t0))
    cu.bevel_factor_end=1.0; cu.keyframe_insert('bevel_factor_end',frame=F(t1))
    cu.bevel_factor_mapping_end='SPLINE'

def text_seq(o,seq):
    """seq=[(시각, 글자)...] 시각마다 글자를 바꿈"""
    seq=sorted(seq)
    def h(scene,*a):
        t=(scene.frame_current-1)/FPS; s=' '
        for tt,ss in seq:
            if t>=tt: s=ss
        o.data.body=s
    bpy.app.handlers.frame_change_pre.append(h)
def burr_top_pts(Rh,depth,Ri=15.0,t=0.6,R=1.4,Ro=40.0,n=24,k=1.0):
    """플랜지 끝 깊이 depth 인 버링 판 윗선 (k=0 이면 같은 Rh 의 평판)"""
    Lf=max(0.01,depth-R+R*math.pi/2); L=(Ri+t+R)-Rh
    pts=[]
    for i in range(n+1):
        s=i/n
        r0=Rh+L*s; z0=0
        d=(1-s)*Lf; arcL=R*math.pi/2
        if d<=arcL: a=d/R; r1=(Ri+t+R)-R*math.sin(a); z1=-(R-R*math.cos(a))
        else: r1=Ri+t; z1=-R-(d-arcL)
        pts.append((r0+(r1-r0)*k,z0+(z1-z0)*k))
    pts.append((Ro,0)); return offset_loop(pts,t)
def loop_obj(pts,name,rgb,angle=270,seg=96,loc=(0,0,0),scale=1.0):
    me=bpy.data.meshes.new(name); bm=bmesh.new()
    vs=[bm.verts.new((r,0,z)) for r,z in pts]
    for a,b in zip(vs,vs[1:]+vs[:1]): bm.edges.new((a,b))
    bm.to_mesh(me); bm.free()
    o=bpy.data.objects.new(name,me); link(o); o.location=loc; o.scale=(scale,)*3
    md=o.modifiers.new('screw','SCREW'); md.axis='Z'; md.angle=math.radians(angle); md.steps=seg; md.render_steps=seg; md.use_merge_vertices=True
    paint(o,rgb); smooth(o); o.rotation_euler=(0,0,math.radians(-45))
    if 89<angle<359: cut(o,angle)
    return o
def add_key(o,name,pts):
    if not o.data.shape_keys: o.shape_key_add(name='Basis')
    sk=o.shape_key_add(name=name)
    for i,(r,z) in enumerate(pts): sk.data[i].co=(r,0,z)
    return sk

def view_modes(parts,seq):
    """seq=[(시각,'solid'|'wire'|'xray')...]  와이어 = 판만 1.2 mm 와이어(안쪽 부품은 솔리드), 엑스레이 = 전체 반투명"""
    seq=sorted(seq); plates=[o for o,g in parts if o.get('plate')]
    def h(scene,*a):
        t=(scene.frame_current-1)/FPS; m='solid'
        for tt,mm in seq:
            if t>=tt: m=mm
        for o in plates:
            w=o.modifiers.get('wire')
            if w: w.show_render=w.show_viewport=(m=='wire')
        sh=scene.display.shading; sh.show_xray=(m=='xray'); sh.xray_alpha=0.28
    bpy.app.handlers.frame_change_pre.append(h)

def tile_plane(path,i,j,nx,ny,width,loc,rot=(math.radians(90),0,0),name='tile'):
    """그림을 nx×ny 로 나눈 (i,j) 조각 (i=가로, j=세로 아래부터)"""
    img=bpy.data.images.load(path,check_existing=True); w,h=img.size
    tw=width/nx; th=width*h/w/ny
    bpy.ops.mesh.primitive_plane_add(size=1,location=loc,rotation=rot); o=bpy.context.object; o.name=name
    o.scale=(tw,th,1); bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    uv=o.data.uv_layers.active.data
    for li,lp in enumerate(o.data.loops):
        u,v=uv[li].uv; uv[li].uv=((i+u)/nx,(j+v)/ny)
    mname='tilemat_'+os.path.basename(path)
    m=bpy.data.materials.get(mname)
    if not m:
        m=bpy.data.materials.new(mname); m.use_nodes=True; nt=m.node_tree; bsdf=nt.nodes['Principled BSDF']
        tex=nt.nodes.new('ShaderNodeTexImage'); tex.image=img; nt.links.new(tex.outputs['Color'],bsdf.inputs['Base Color']); m.diffuse_color=(1,1,1,1)
    o.data.materials.append(m); o.select_set(False); return o,tw,th


def cut(o,keep_deg):
    """완전한 회전체(360°)에서 나머지 각도(keep_deg~360°)를 불리언으로 잘라 냄 → 잘린 면이 단면처럼 막힘 (얇은 껍데기 지글거림 방지)"""
    md=o.modifiers.get('screw')
    if md: md.angle=math.radians(360)
    es=o.modifiers.get('es')
    if es: o.modifiers.remove(es)
    L=1000.0; me=bpy.data.meshes.new('cutter'); bm=bmesh.new()
    a0=math.radians(keep_deg); a1=math.radians(360)
    pts=[(0,0)]+[(L*math.cos(a0+(a1-a0)*k/8),L*math.sin(a0+(a1-a0)*k/8)) for k in range(9)]
    vb=[bm.verts.new((x,y,-L)) for x,y in pts]; vt=[bm.verts.new((x,y,L)) for x,y in pts]
    n=len(pts); bm.faces.new(vb[::-1]); bm.faces.new(vt)
    for i in range(n):
        j=(i+1)%n; bm.faces.new((vb[i],vb[j],vt[j],vt[i]))
    bm.normal_update(); bm.to_mesh(me); bm.free()
    c=bpy.data.objects.new(o.name+'_cut',me); link(c); c.parent=o; c.hide_render=True; c.display_type='WIRE'
    b=o.modifiers.new('cut','BOOLEAN'); b.operation='DIFFERENCE'; b.object=c; b.solver='EXACT'
    smooth(o); return o
