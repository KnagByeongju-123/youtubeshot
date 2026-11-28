"""GLB 안의 한 재질 색 그림을 파일 그림으로 바꿔 끼움 — 처음부터 다시 만들지 않고 그림만 고칠 때 (2026-11-28 입술 분홍)
   사용: .bpy_venv/bin/python -I 애니3D/glb_그림바꾸기.py <입력.glb> <출력.glb> <재질 이름 글자(f003_head)> <그림.tga|png>  → 그다음 glb_금속끄기.py"""
import sys
import bpy
a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
src, dst, key, pic = a[:4]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
new = bpy.data.images.load(pic)
for m in bpy.data.materials:
    if key not in m.name or not m.node_tree: continue
    bs = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    nd = bs.inputs["Base Color"].links[0].from_node
    while nd.type != "TEX_IMAGE": nd = next(i.links[0].from_node for i in nd.inputs if i.links)
    nd.image = new; print("그림 바꿈:", m.name, "←", pic)
bpy.ops.export_scene.gltf(filepath=dst, export_format="GLB", export_morph=True, export_skins=True, export_animations=False, export_image_format="AUTO")
print("→", dst)
