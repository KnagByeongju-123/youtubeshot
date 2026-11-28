"""GLB 인물의 머리카락을 단정한 단발로 자름 (사용자 2026-11-28 '머리카락은 단정하게 짧게' — 턱 선 높이)
   머리카락 조각(opacity 재질, 높이 폭 3cm 이상)의 점 중 --높이 아래는 위로 접어 올림: z' = 높이 - (높이 - z)·--접기
   → 끝이 높이 근처에 모여 가지런한 끝선. 뒤쪽은 --뒤더 만큼 조금 더 길게(뒤가 살짝 긴 단발). 모양 키도 같은 방식
   사용: .bpy_venv/bin/python -I 애니3D/머리카락자르기.py <입력.glb> <출력.glb> [--높이 1.47] [--접기 0.08] [--뒤더 0.02]"""
import sys
import bpy, bmesh
import numpy as np

a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
src, dst = a[0], a[1]
def opt(k, d): return float(a[a.index(k) + 1]) if k in a else d
ZC, FOLD, BACK = opt("--높이", 1.47), opt("--접기", 0.08), opt("--뒤더", 0.02)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
o = max((o for o in bpy.data.objects if o.type == "MESH"), key=lambda o: len(o.data.vertices))
me = o.data; M = np.array(o.matrix_world); Mi3 = np.linalg.inv(M[:3, :3])
opac = {i for i, s in enumerate(o.material_slots) if s.material and "opacity" in s.material.name}
co = np.zeros(len(me.vertices) * 3); me.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
W = co @ M[:3, :3].T + M[:3, 3]
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
opv = np.zeros(len(W), bool)
for f in bm.faces:
    if f.material_index in opac:
        for v in f.verts: opv[v.index] = True
seen = np.zeros(len(W), bool); hair = []
for v in bm.verts:
    if not opv[v.index] or seen[v.index]: continue
    st = [v]; c = []; seen[v.index] = True
    while st:
        x = st.pop(); c.append(x.index)
        for e in x.link_edges:
            y = e.other_vert(x)
            if opv[y.index] and not seen[y.index]: seen[y.index] = True; st.append(y)
    if np.ptp(W[c, 2]) >= 0.03: hair += c
# 얼굴 재질 안의 '머리카락이 그려진 껍데기'(뒤·옆 목을 덮는 판, 그림이 검은 곳)도 같이 접음 — 안 접으면 잘린 머리 밑으로 검은 판이 남음
if "--껍데기그대로" not in a:
    uvl = me.uv_layers.active.data
    img = None
    for i, sl in enumerate(o.material_slots):
        if sl.material and "head" in sl.material.name:
            hm = i
            bsdf = next(n for n in sl.material.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
            ln = bsdf.inputs["Base Color"].links
            if ln:
                nd = ln[0].from_node
                while nd.type != "TEX_IMAGE" and nd.inputs and any(i.links for i in nd.inputs):
                    nd = next(i.links[0].from_node for i in nd.inputs if i.links)
                if nd.type == "TEX_IMAGE": img = nd.image                     # 색 그림 (노멀 그림 말고)
    if img is not None:
        w_, h_ = img.size; px = np.zeros(w_ * h_ * 4, np.float32); img.pixels.foreach_get(px); px = px.reshape(h_, w_, 4)
        lum = px[..., :3].mean(2)
        dark = {}
        for poly in me.polygons:
            if poly.material_index != hm: continue
            for li in poly.loop_indices:
                vi = me.loops[li].vertex_index; u, v = uvl[li].uv
                l = lum[int(np.clip(v, 0, 0.9999) * h_), int(np.clip(u % 1, 0, 0.9999) * w_)]
                dark[vi] = min(dark.get(vi, 1.0), l)
        shell = [vi for vi, l in dark.items() if l < float(opt("--껍데기밝기", 0.3)) and W[vi, 2] < ZC + 0.03]
        print("머리 그림 껍데기 점", len(shell))
        hair = list(set(hair) | set(shell))
bm.free()
H = np.array(hair)
def cut(Wb):
    zc = ZC - BACK * np.clip((Wb[H, 1] - 0.0) / 0.1, 0, 1)          # 뒤(+y)는 조금 더 길게
    z = Wb[H, 2]; low = z < zc
    Wb[H[low], 2] = zc[low] - (zc[low] - z[low]) * FOLD
    return Wb
kbs = list(me.shape_keys.key_blocks) if me.shape_keys else []
newW = cut(W.copy())
me.vertices.foreach_set("co", ((newW - M[:3, 3]) @ Mi3.T).ravel())
for kb in kbs:
    arr = np.array([d.co for d in kb.data]); Wk = arr @ M[:3, :3].T + M[:3, 3]
    kb.data.foreach_set("co", ((cut(Wk) - M[:3, 3]) @ Mi3.T).ravel())
me.update()
print("머리카락 점", len(H), "자른 점", int((W[H, 2] < ZC).sum()), "끝 높이 %.3f" % ZC)
bpy.ops.export_scene.gltf(filepath=dst, export_format="GLB", export_morph=True, export_skins=True, export_animations=False, export_image_format="AUTO")
print("→", dst)
