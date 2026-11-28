"""GLB 인물의 머리 윤곽(머리가 그려진 머리통 껍데기 + 머리카락 판)을 매끄럽게 — 각진 다각형 윤곽을 둥글고 단정하게 (사용자 2026-11-28 '표시한 부분(머리 양옆 윤곽)을 자연스럽게 단정한 머리카락으로')
   - 고를 점: 얼굴 재질 중 그림이 어두운 곳(머리를 그린 껍데기)과 머리카락 판(opacity), 높이 --아래 위
   - 타우빈 다듬기(λ·μ 번갈아, 부피 줄지 않게) --횟수 번 → 각진 꺾임이 둥글어짐. 피부 점은 움직이지 않음(이음매 고정)
   - 옆으로 --오므림 만큼 머리 가운데 쪽으로 살짝 당겨 붕 뜬 옆머리를 정리. 모양 키도 같은 양만큼
   사용: .bpy_venv/bin/python -I 애니3D/머리윤곽다듬기.py <입력.glb> <출력.glb> [--횟수 12] [--오므림 0.04] [--아래 1.42] [--앞 0.07] [--최대 0.01]"""
import sys
import bpy, bmesh
import numpy as np

a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
src, dst = a[0], a[1]
def opt(k, d): return float(a[a.index(k) + 1]) if k in a else d
IT, PULL, ZL = int(opt("--횟수", 12)), opt("--오므림", 0.04), opt("--아래", 1.42)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
o = max((o for o in bpy.data.objects if o.type == "MESH"), key=lambda o: len(o.data.vertices))
me = o.data; M = np.array(o.matrix_world); Mi3 = np.linalg.inv(M[:3, :3])
co = np.zeros(len(me.vertices) * 3); me.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
W = co @ M[:3, :3].T + M[:3, 3]
opac = {i for i, s in enumerate(o.material_slots) if s.material and "opacity" in s.material.name}
hm = next(i for i, s in enumerate(o.material_slots) if s.material and "head" in s.material.name)
bs = next(n for n in o.material_slots[hm].material.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
nd = bs.inputs["Base Color"].links[0].from_node
while nd.type != "TEX_IMAGE": nd = next(i.links[0].from_node for i in nd.inputs if i.links)
img = nd.image; w_, h_ = img.size
px = np.zeros(w_ * h_ * 4, np.float32); img.pixels.foreach_get(px); lum = px.reshape(h_, w_, 4)[..., :3].mean(2)
uvl = me.uv_layers.active.data
dark = np.ones(len(W)); skin = np.zeros(len(W), bool); hairc = np.zeros(len(W), bool)
for p in me.polygons:
    for li in p.loop_indices:
        vi = me.loops[li].vertex_index
        if p.material_index in opac: hairc[vi] = True; continue
        if p.material_index != hm: skin[vi] = True; continue
        u, v = uvl[li].uv
        l = lum[int(np.clip(v, 0, 0.9999) * h_), int(np.clip(u % 1, 0, 0.9999) * w_)]
        dark[vi] = min(dark[vi], l)
        if l >= 0.3: skin[vi] = True
sel = ((dark < 0.3) | hairc) & ~skin & (W[:, 2] > ZL)
print("다듬을 점", int(sel.sum()))
# 같은 자리 점(그림 이음매에서 갈라진 점)은 하나로 묶어 같이 움직임 — 따로 움직이면 뒤통수가 찢어졌음
key = np.round(W * 4000).astype(np.int64); _, grp = np.unique(key, axis=0, return_inverse=True); grp = grp.ravel(); G = grp.max() + 1
gsel = np.zeros(G, bool); np.logical_or.at(gsel, grp, sel)
gskin = np.zeros(G, bool); np.logical_or.at(gskin, grp, skin & ~sel)
gsel &= ~gskin
GP = np.zeros((G, 3)); np.add.at(GP, grp, W); cnt = np.bincount(grp, minlength=G)[:, None]; GP /= cnt
bm = bmesh.new(); bm.from_mesh(me)
nb = [set() for _ in range(G)]
for e in bm.edges:
    i, j = grp[e.verts[0].index], grp[e.verts[1].index]
    if i != j: nb[i].add(j); nb[j].add(i)
bm.free()
nb = [list(x) for x in nb]
FR = opt("--앞", 0.07)                                          # 이보다 뒤(+y)는 덜 다듬음 (뒤통수는 그대로)
gw = np.clip((FR + 0.03 - GP[:, 1]) / 0.03, 0, 1) * gsel
gids = np.where(gw > 0)[0]
Q = GP.copy()
for it in range(IT):
    for lam in (0.5, -0.53):
        avg = np.array([Q[nb[i]].mean(0) if nb[i] else Q[i] for i in gids])
        Q[gids] = Q[gids] + lam * gw[gids, None] * (avg - Q[gids])
d = Q - GP; n = np.linalg.norm(d, axis=1, keepdims=True); d *= np.minimum(1, opt("--최대", 0.01) / (n + 1e-9))
P = W + d[grp]; ids = np.where(gw[grp] > 0)[0]
# 옆으로 붕 뜬 곳 살짝 오므리기 (머리 가운데 세로축 쪽으로, 아래로 갈수록 더)
cx = np.median(W[sel, 0]); cyy = np.median(W[sel, 1])
t = np.clip((1.70 - P[ids, 2]) / 0.25, 0, 1)
P[ids, 0] = cx + (P[ids, 0] - cx) * (1 - PULL * t)
dl = (P - W) @ Mi3.T
me.vertices.foreach_set("co", (co + dl).ravel())
for kb in (me.shape_keys.key_blocks if me.shape_keys else []):
    arr = np.zeros(len(co) * 3); kb.data.foreach_get("co", arr); kb.data.foreach_set("co", (arr.reshape(-1, 3) + dl).ravel())
me.update()
print("최대 옮김 %.1fmm" % (np.linalg.norm(P - W, axis=1).max() * 1000))
bpy.ops.export_scene.gltf(filepath=dst, export_format="GLB", export_morph=True, export_skins=True, export_animations=False, export_image_format="AUTO")
print("→", dst)
