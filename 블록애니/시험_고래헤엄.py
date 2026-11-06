import bpy, sys, time, math, random
OUT=sys.argv[-2]; NF=int(sys.argv[-1])
bpy.ops.wm.read_factory_settings(use_empty=True)
sc=bpy.context.scene; col=sc.collection
def mat(name,rgb,rough=0.6,emit=0):
    m=bpy.data.materials.new(name); m.use_nodes=True; b=m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value=(*rgb,1); b.inputs["Roughness"].default_value=rough
    if emit: b.inputs["Emission Color"].default_value=(*rgb,1); b.inputs["Emission Strength"].default_value=emit
    m.diffuse_color=(*rgb,1)
    return m
M={"dark":mat("dark",(0.05,0.09,0.16)),"belly":mat("belly",(0.55,0.62,0.68)),"eye":mat("eye",(0.01,0.01,0.01),0.2),
   "sand":mat("sand",(0.35,0.32,0.25),0.9)}
# 블록 하나(공유 메시) + 재질별 메시
meshes={}
for k,m in M.items():
    bpy.ops.mesh.primitive_cube_add(size=0.96); o=bpy.context.object; o.data.materials.append(m); meshes[k]=o.data; bpy.data.objects.remove(o)
def block(k,loc,parent):
    o=bpy.data.objects.new("b",meshes[k]); col.objects.link(o); o.parent=parent; o.location=loc; return o
# 고래: 길이 24블록, 마디 6개
L=24; segs=[]; prev=None
for s in range(6):
    e=bpy.data.objects.new(f"seg{s}",None); col.objects.link(e)
    if prev: e.parent=prev; e.location=(-4,0,0)
    segs.append(e); prev=e
def radius(x):  # x 0(머리)~L(꼬리)
    t=x/L
    return max(0.6, 3.2*math.sin(math.pi*min(1,t*1.15+0.08))**0.8) if t<0.85 else 0.6
for x in range(L):
    s=min(5,x//4); lx=-(x-s*4)
    r=radius(x)
    for y in range(-int(r),int(r)+1):
        for z in range(-int(r),int(r)+1):
            if y*y+(z*1.1)**2<=r*r+0.3:
                surf = r<1.5 or y*y+(z*1.1)**2 > (r-1.1)**2
                if not surf: continue
                k="belly" if z<-r*0.35 else "dark"
                if x==3 and abs(y)==int(r) and z==0: k="eye"
                block(k,(lx,y,z),segs[s])
# 가슴지느러미
for i in range(5):
    for side in (-1,1): block("dark",(-6-i*0.3, side*(3.5+i), -1.5-i*0.4), segs[1])
# 꼬리지느러미(가로로 넓게)
for i in range(-6,7):
    for j in range(2): block("dark",(-2-j-abs(i)*0.4, i, 0), segs[5])
root=segs[0]; root.location=(0,0,6)
# 헤엄: 위아래 물결(고래는 꼬리를 위아래로)
for f in range(1,NF+1):
    ph=f/24*2*math.pi*0.5
    root.location=(f*0.12,0,6+0.4*math.sin(ph)); root.keyframe_insert("location",frame=f)
    for i,e in enumerate(segs[1:],1):
        e.rotation_euler=(0,0.045*i*math.sin(ph-i*0.7),0); e.keyframe_insert("rotation_euler",frame=f)
# 바닥 모래 블록
random.seed(1)
for x in range(-30,40,2):
    for y in range(-20,20,2):
        o=bpy.data.objects.new("s",meshes["sand"]); col.objects.link(o); o.scale=(2,2,1); o.location=(x,y,-4+random.choice([0,0,0.5]))
# 카메라·빛·물빛 배경·안개
cam=bpy.data.cameras.new("c"); cam.lens=28; co=bpy.data.objects.new("c",cam); col.objects.link(co); sc.camera=co
tgt=bpy.data.objects.new("t",None); col.objects.link(tgt); tgt.parent=root; tgt.location=(-10,0,0)
tc=co.constraints.new("TRACK_TO"); tc.target=tgt
for f in (1,NF):
    co.location=(-4+f*0.12,-30,4); co.keyframe_insert("location",frame=f)
sun=bpy.data.lights.new("s","SUN"); sun.energy=4; sun.color=(0.7,0.9,1); so=bpy.data.objects.new("s",sun); col.objects.link(so); so.rotation_euler=(0.3,0.2,0)
w=bpy.data.worlds.new("w"); sc.world=w; w.use_nodes=True; w.node_tree.nodes["Background"].inputs[0].default_value=(0.01,0.12,0.25,1); w.node_tree.nodes["Background"].inputs[1].default_value=1.0
# 물속 안개: 볼륨 대신 월드 볼륨(가벼움)
vol=w.node_tree.nodes.new("ShaderNodeVolumeScatter"); vol.inputs["Density"].default_value=0.012; vol.inputs["Color"].default_value=(0.3,0.7,1,1)
#w.node_tree.links.new(vol.outputs[0], w.node_tree.nodes["World Output"].inputs["Volume"])
r=sc.render; r.engine="BLENDER_WORKBENCH"; sc.display.shading.light="STUDIO"; sc.display.shading.color_type="MATERIAL"; sc.display.shading.show_shadows=True; sc.display.render_aa="8"; sc.cycles.device="CPU"; sc.cycles.samples=12; sc.cycles.use_denoising=True
sc.cycles.volume_step_rate=4; sc.cycles.max_bounces=3
r.resolution_x=1280; r.resolution_y=720; r.fps=24; sc.frame_start=1; sc.frame_end=NF
w.color=(0.02,0.16,0.30)
sh=sc.display.shading; sh.show_cavity=True; sh.cavity_type="BOTH"; sh.curvature_ridge_factor=1.2; sh.show_specular_highlight=False
sc.view_layers[0].use_pass_z=True
ng=bpy.data.node_groups.new("C","CompositorNodeTree"); sc.compositing_node_group=ng
ng.interface.new_socket("Image",in_out="OUTPUT",socket_type="NodeSocketColor")
N=ng.nodes; Lk=ng.links
rl=N.new("CompositorNodeRLayers"); go=N.new("NodeGroupOutput")
mr=N.new("ShaderNodeMapRange"); mr.inputs[1].default_value=15; mr.inputs[2].default_value=90; mr.inputs[3].default_value=0; mr.inputs[4].default_value=0.9
mx=N.new("ShaderNodeMix"); mx.data_type="RGBA"; mx.inputs[7].default_value=(0.02,0.16,0.30,1)
Lk.new(rl.outputs["Depth"],mr.inputs[0]); Lk.new(mr.outputs[0],mx.inputs[0]); Lk.new(rl.outputs["Image"],mx.inputs[6]); Lk.new(mx.outputs[2],go.inputs[0])
r.image_settings.file_format="PNG"; r.filepath=OUT
t=time.time(); bpy.ops.render.render(animation=True); print("TIME",(time.time()-t)/NF,"per frame")
