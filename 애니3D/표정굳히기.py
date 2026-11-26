"""GLB 인물의 기본 얼굴에 표정을 굳힘 — 모양 키 값을 섞은 얼굴을 새 바탕으로 하고, 다른 키(입 모양·표정)는 새 바탕 기준으로 다시 계산
   (사용자 2026-11-26 '기본 표정(살짝 미소)을 저장': 다른 프로그램에서 열어도 처음부터 미소)
   사용: .bpy_venv/bin/python -I 애니3D/표정굳히기.py <입력.glb> <출력.glb> HB_07_MouthSmile=0.45 AU_06_CheekRaiser=0.3"""
import os, sys
import bpy
import numpy as np

a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
src, dst = a[0], a[1]; vals = {kv.split("=")[0]: float(kv.split("=")[1]) for kv in a[2:]}
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.abspath(src))
for o in bpy.data.objects:
    if o.animation_data: o.animation_data_clear()
    if o.type != "MESH" or not o.data.shape_keys: continue
    sk = o.data.shape_keys
    if sk.animation_data: sk.animation_data_clear()
    kb = sk.key_blocks; nv = len(o.data.vertices)
    use = [k for k in kb[1:] if k.name in vals]
    if not use: continue
    def co(k): arr = np.zeros(nv * 3, np.float32); k.data.foreach_get("co", arr); return arr
    basis = co(kb[0]); mix = basis.copy()
    for k in use: mix += (co(k) - basis) * vals[k.name]
    for k in kb[1:]:
        k.data.foreach_set("co", mix + (co(k) - basis)); k.value = 0.0
    kb[0].data.foreach_set("co", mix); o.data.update()
    print("표정 굳힘:", o.name, {k.name: vals[k.name] for k in use})
bpy.ops.export_scene.gltf(filepath=os.path.abspath(dst), export_format="GLB", export_morph=True, export_skins=True, export_animations=False, export_image_format="AUTO")
print("→", dst, os.path.getsize(dst) // 1024, "KB")
