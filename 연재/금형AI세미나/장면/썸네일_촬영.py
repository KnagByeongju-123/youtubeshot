"""썸네일용 금형 화면 (글자 없이): 와이어 · 엑스레이 · 금형 안
blender -b -P ch2.py -P 썸네일_촬영.py -- --sfx"""
import bpy, math, os
from mathutils import Vector
sc=bpy.context.scene; HERE=os.path.dirname(os.path.abspath(bpy.data.filepath)) if bpy.data.filepath else os.path.join('/home/user/youtubeshot/연재/금형AI세미나/장면')
for o in sc.objects:
    if o.type=='FONT': o.hide_render=True
cam=sc.camera; tgt=[o for o in sc.objects if o.name.startswith('CamTarget')][0]
cam.animation_data_clear(); tgt.animation_data_clear(); cam.data.animation_data_clear()
for fc in []: pass
for m in cam.modifiers if hasattr(cam,'modifiers') else []: pass
sc.display.render_aa='16'
DX=1500; tv_wire=None
shots=[('wire',1395,(DX-520,-760,420),(DX,0,190),30),('xray',1500,(DX+420,-800,380),(DX,0,190),30),('inside',1255,(DX-108-60,-90,145+50),(DX-108+30,0,145+30),18)]
for name,f,cp,tp,lens in shots:
    sc.frame_set(f); cam.location=cp; tgt.location=tp; cam.data.lens=lens
    sc.render.filepath=os.path.join('/home/user/youtubeshot/연재/금형AI세미나/장면','_thumb_%s.png'%name)
    bpy.ops.render.render(write_still=True)
print('THUMB_OK')
