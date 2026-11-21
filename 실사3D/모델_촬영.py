"""받은 .blend 모델을 사진(한 장) 또는 빙 돌며 보는 영상으로 찍기 (블렌더 Cycles, 그래픽카드 없이)
사용: .bpy_venv/bin/python -I 실사3D/모델_촬영.py <모델.blend> <결과.png>                 → 사진 1280×720
      .bpy_venv/bin/python -I 실사3D/모델_촬영.py <모델.blend> <프레임폴더> --돌려보기 120 → f0000.png …
      옵션 --샘플 64(사진 기본)·16(돌려보기 기본), --크기 1280x720, --부분 0 60 (60장씩 나눠 찍기)
      영상: ffmpeg -framerate 24 -i <폴더>/f%04d.png -c:v libx264 -pix_fmt yuv420p -crf 18 결과.mp4
속도(CPU 4개·AMX 없음): 사진 64샘플 약 30초, 돌려보기 16샘플 한 장 약 12~15초 → 5초(120장) 약 25분
"""
import bpy,sys,math,mathutils
a=sys.argv[1:]; blend,out=a[0],a[1]
def opt(k,d): return a[a.index(k)+1] if k in a else d
N=int(opt("--돌려보기",0)); spp=int(opt("--샘플",16 if N else 64)); W,H=map(int,opt("--크기","1280x720").split("x"))
start,end=(int(a[a.index("--부분")+1]),int(a[a.index("--부분")+2])) if "--부분" in a else (0,N)
bpy.ops.wm.open_mainfile(filepath=blend)
sc=bpy.context.scene
objs=[o for o in sc.objects if o.type=='MESH']
pts=[o.matrix_world@mathutils.Vector(c) for o in objs for c in o.bound_box]
mn=mathutils.Vector([min(p[i] for p in pts) for i in range(3)]);mx=mathutils.Vector([max(p[i] for p in pts) for i in range(3)])
c=(mn+mx)/2; r=(mx-mn).length/2
bpy.ops.mesh.primitive_plane_add(size=r*40,location=(c.x,c.y,mn.z))
fl=bpy.context.object; m=bpy.data.materials.new("바닥"); m.use_nodes=True
m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value=(0.55,0.55,0.58,1); fl.data.materials.append(m)
cam=bpy.data.objects.new("cam",bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera=cam
cam.data.lens=50
# 키 큰 물건(랜턴 등)은 가로 화면에서 위아래가 잘림 → 높이/너비 비율만큼 뒤로
d=r*3.6*max(1.0,(mx.z-mn.z)/max(mx.x-mn.x,mx.y-mn.y)*0.75)
hd=d; z=c.z+d*0.35
w=sc.world or bpy.data.worlds.new("w"); sc.world=w; w.use_nodes=True
w.node_tree.nodes["Background"].inputs[0].default_value=(0.8,0.85,0.95,1); w.node_tree.nodes["Background"].inputs[1].default_value=0.6
L=bpy.data.objects.new("key",bpy.data.lights.new("key","AREA")); L.data.energy=300*r*r*4; L.data.size=r*3
L.location=(c.x-r*3,c.y-r*3,c.z+r*4); L.rotation_euler=(c-L.location).to_track_quat('-Z','Y').to_euler(); sc.collection.objects.link(L)
sc.render.engine='CYCLES'; sc.cycles.device='CPU'; sc.cycles.samples=spp; sc.cycles.use_denoising=True
sc.render.resolution_x=W; sc.render.resolution_y=H
def shoot(t,path):
    cam.location=(c.x+hd*math.sin(t),c.y-hd*math.cos(t),z)
    cam.rotation_euler=(c-cam.location).to_track_quat('-Z','Y').to_euler()
    sc.render.filepath=path; bpy.ops.render.render(write_still=True)
if N:
    for i in range(start,end): shoot(math.radians(35)+2*math.pi*i/N,f"{out}/f{i:04d}.png")
else: shoot(math.radians(35),out)
print("찍음",out)
