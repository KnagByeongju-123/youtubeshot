"""GLB 인물의 기본 얼굴에 표정을 굳힘 — 모양 키 값을 섞은 얼굴을 새 바탕으로 하고, 다른 키(입 모양·표정)는 새 바탕 기준으로 다시 계산
   (사용자 2026-11-26 '기본 표정(살짝 미소)을 저장': 다른 프로그램에서 열어도 처음부터 미소)
   사용: .bpy_venv/bin/python -I 애니3D/표정굳히기.py <입력.glb> <출력.glb> HB_07_MouthSmile=0.45 AU_06_CheekRaiser=0.3 [--절대 Blink,AK_09_EyeBlinkLeft,…]"""
import os, sys
import bpy
import numpy as np

a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
src, dst = a[0], a[1]
ABS = set(a[a.index("--절대") + 1].split(",")) if "--절대" in a else set()   # 이 키들은 '끝 모양'을 그대로(눈 감기: 눈을 가늘게 굳혀도 딱 감기게, 더 내려가 겹치지 않게)
kvs = [x for i, x in enumerate(a[2:], 2) if "=" in x and a[i - 1] != "--절대"]
vals = {kv.split("=")[0]: float(kv.split("=")[1]) for kv in kvs}
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
        d = co(k) - basis
        if k.name in ABS:                                        # 움직이는 점은 원래 끝 모양 그대로, 나머지는 새 바탕
            mv = np.repeat(np.abs(d.reshape(-1, 3)).max(1) > 1e-6, 3)
            k.data.foreach_set("co", np.where(mv, co(k), mix + d))
        else:
            k.data.foreach_set("co", mix + d)
        k.value = 0.0
    kb[0].data.foreach_set("co", mix); o.data.update()
    print("표정 굳힘:", o.name, {k.name: vals[k.name] for k in use})
bpy.ops.export_scene.gltf(filepath=os.path.abspath(dst), export_format="GLB", export_morph=True, export_skins=True, export_animations=False, export_image_format="AUTO")
print("→", dst, os.path.getsize(dst) // 1024, "KB")
