"""GLB 인물의 옆으로 튀어나온 곁머리 조각을 지움 (사용자 2026-11-28 '곁머리 튀어나온 것 제거')
   머리카락 조각(opacity 재질, 높이 폭 3cm 이상) 중 머리 가운데에서 옆으로 --옆 m 넘게 나간 점이 있는 조각,
   또는 머리 겉(가장 가까운 얼굴·두피 점)에서 --뜸 m 넘게 떠 있는 점이 --뜸비율 넘는 조각을 지움. 뒤 머리(가운데 뒤, |x|<0.03)는 그대로
   사용: .bpy_venv/bin/python -I 애니3D/곁머리정리.py <입력.glb> <출력.glb> [--옆 0.108] [--뜸 0.03] [--뜸비율 0.4] [--보기]"""
import sys
import bpy, bmesh
import numpy as np
from mathutils.kdtree import KDTree

a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
src, dst = a[0], a[1]
def opt(k, d): return float(a[a.index(k) + 1]) if k in a else d
XS, FL, FR = opt("--옆", 0.108), opt("--뜸", 0.03), opt("--뜸비율", 0.4)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
o = max((o for o in bpy.data.objects if o.type == "MESH"), key=lambda o: len(o.data.vertices))
me = o.data; M = np.array(o.matrix_world)
W = np.array([v.co for v in me.vertices]) @ M[:3, :3].T + M[:3, 3]
opac = {i for i, s in enumerate(o.material_slots) if s.material and "opacity" in s.material.name}
headm = {i for i, s in enumerate(o.material_slots) if s.material and "head" in s.material.name}
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
opv = np.zeros(len(W), bool); hv = np.zeros(len(W), bool)
for f in bm.faces:
    for v in f.verts:
        if f.material_index in opac: opv[v.index] = True
        if f.material_index in headm: hv[v.index] = True
hid = np.where(hv & (W[:, 2] > 1.45))[0]
kd = KDTree(len(hid))
for i in hid: kd.insert(tuple(W[i]), int(i))
kd.balance()
cx = np.median(W[hid, 0])
seen = np.zeros(len(W), bool); kill = []
for v in bm.verts:
    if not opv[v.index] or seen[v.index]: continue
    st = [v]; c = []; seen[v.index] = True
    while st:
        x = st.pop(); c.append(x)
        for e in x.link_edges:
            y = e.other_vert(x)
            if opv[y.index] and not seen[y.index]: seen[y.index] = True; st.append(y)
    idx = [x.index for x in c]; P = W[idx]
    if np.ptp(P[:, 2]) < 0.03: continue
    side = np.abs(P[:, 0] - cx).max()
    fl = np.mean([kd.find(tuple(p))[2] > FL for p in P])
    if np.abs(P[:, 0] - cx).max() < 0.03: continue
    if side > XS or fl > FR:
        kill += c
        print("지움: 점 %d, 옆 %.3f, 뜬 비율 %.2f, 높이 %.2f~%.2f" % (len(c), side, fl, P[:, 2].min(), P[:, 2].max()))
bmesh.ops.delete(bm, geom=list(set(kill)), context="VERTS"); bm.to_mesh(me); bm.free(); me.update()
bpy.ops.export_scene.gltf(filepath=dst, export_format="GLB", export_morph=True, export_skins=True, export_animations=False, export_image_format="AUTO")
print("→", dst)
