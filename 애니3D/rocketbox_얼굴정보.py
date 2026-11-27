"""Rocketbox 인물(_facial.fbx)의 세모(3D 자리·UV·재질)와 그림 경로를 꺼내 저장 — 사진 얼굴 입히기(`애니3D/사진얼굴입히기.py`)의 1단계
   (사용자 2026-11-27 'Rocketbox 원래 머리에 사진 얼굴 입히기'). 정면 그림 찍기는 그래픽카드가 없어도 되게 사진얼굴입히기.py 가 numpy 로 직접 함.
   결과: <출력폴더>/tris.npz (xyz: 세모×3×3, uv: 세모×3×2, mat: 재질 번호) + info.json (재질 이름·색 그림 경로)
   사용: .bpy_venv/bin/python -I 애니3D/rocketbox_얼굴정보.py <인물 폴더(…/Sports_Female_02)> <출력폴더>"""
import os, sys, json
import bpy
import numpy as np

a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
folder, out = a[0].rstrip("/"), a[1]
nm = os.path.basename(folder)
os.makedirs(out, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=os.path.join(folder, "Export", f"{nm}_facial.fbx"))
mesh_o = next(o for o in bpy.data.objects if o.type == "MESH")
texdir = os.path.join(folder, "Textures")
mats = []
for m in mesh_o.data.materials:
    col = None
    if m and m.node_tree:
        for n in m.node_tree.nodes:
            if n.type == "TEX_IMAGE" and n.image and "color" in n.image.filepath:
                f = os.path.join(texdir, os.path.basename(n.image.filepath.replace("\\", "/")))
                if os.path.exists(f): col = f
    mats.append({"name": m.name if m else None, "color": col})
dg = bpy.context.evaluated_depsgraph_get()
me = mesh_o.evaluated_get(dg).to_mesh(); me.calc_loop_triangles()
mw = np.array(mesh_o.matrix_world)
V = np.array([v.co for v in me.vertices]); V = V @ mw[:3, :3].T + mw[:3, 3]
uvl = me.uv_layers.active.data
lt = me.loop_triangles
xyz = np.array([[V[me.loops[l].vertex_index] for l in t.loops] for t in lt], np.float32)
uv = np.array([[uvl[l].uv[:] for l in t.loops] for t in lt], np.float32)
mat = np.array([t.material_index for t in lt], np.int16)
np.savez(os.path.join(out, "tris.npz"), xyz=xyz, uv=uv, mat=mat)
json.dump({"materials": mats}, open(os.path.join(out, "info.json"), "w"), ensure_ascii=False, indent=1)
print("세모", len(lt), "재질", mats, "→", out)
