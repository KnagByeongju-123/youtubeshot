"""GLB 인물의 입 모양 키에서 '앞으로 튀어나오는' 움직임만 줄임 — 말할 때 입술이 부리처럼 앞으로 나와 보이는 것 (사용자 2026-11-28 '입이 좀 튀어나옴', 여자아나운서3)
   모든 입 모양 키(이름에 Blink·Eye 가 없는 키)의 움직임 중 얼굴 앞쪽(블렌더 -Y) 성분을 --앞 배로 (뒤로 가는 것은 그대로), 위아래·옆은 그대로
   사용: .bpy_venv/bin/python -I 애니3D/입앞으로줄이기.py <입력.glb> <출력.glb> [--앞 0.3]"""
import sys
import bpy
import numpy as np

a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
src, dst = a[0], a[1]
K = float(a[a.index("--앞") + 1]) if "--앞" in a else 0.3
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
for o in [o for o in bpy.data.objects if o.type == "MESH" and o.data.shape_keys]:
    me = o.data; M = np.array(o.matrix_world)[:3, :3]; Mi = np.linalg.inv(M)
    kb = me.shape_keys.key_blocks; n = len(me.vertices)
    base = np.zeros(n * 3); kb[0].data.foreach_get("co", base); base = base.reshape(-1, 3)
    for k in kb[1:]:
        if "Blink" in k.name or "Eye" in k.name: continue
        arr = np.zeros(n * 3); k.data.foreach_get("co", arr); d = arr.reshape(-1, 3) - base
        dw = d @ M.T
        fw = dw[:, 1] < 0                                  # 앞으로(-Y) 가는 점
        dw[fw, 1] *= K
        k.data.foreach_set("co", (base + dw @ Mi.T).ravel())
    print(o.name, "입 모양 키 앞으로 움직임 ×", K)
bpy.ops.export_scene.gltf(filepath=dst, export_format="GLB", export_skins=True, export_morph=True, export_animations=False, export_image_format="AUTO")
print("→", dst)
