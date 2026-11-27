"""GLB 인물의 머리카락(opacity 재질 조각, 속눈썹 빼고)을 아래로 늘이고, 어깨·재킷에 묻히는 곳은 몸 겉으로 밀어냄 (사용자 2026-11-27 '긴 생머리로' — Rocketbox 긴 머리도 앞·옆은 어깨까지라 사진(가슴까지)보다 짧았음)
   - 늘이기: 높이 --시작 아래 점을 z' = 시작 - (시작 - z)·k. k 는 앞·옆(y < --앞y) = 계산값, 뒤(y > --뒤y) = 1(뒤는 이미 긺), 사이는 섞음
     k = (시작 - 목표끝) / (시작 - 앞·옆 머리 가장 낮은 곳) → 앞·옆 머리 끝이 --끝 높이에 닿음
   - 밀어내기: 몸(머리카락 아닌 면)까지 가장 가까운 점과 법선으로, 겉에서 --띄움 m 안쪽이면 겉으로 (3번 + 머리카락 줄 따라 부드럽게)
   - 모양 키·뼈 무게는 그대로(머리카락은 Head 뼈를 따라감)
   사용: .bpy_venv/bin/python -I 애니3D/머리카락늘이기.py <입력.glb> <출력.glb> [--시작 1.57] [--끝 1.33] [--앞y 0.06] [--뒤y 0.12] [--띄움 0.012] [--어깨 1.50] [--앞으로 0.9]"""
import sys
import bpy, bmesh
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
src, dst = a[0], a[1]
def opt(k, d): return float(a[a.index(k) + 1]) if k in a else d
Z0, ZEND, YF, YB, GAP = opt("--시작", 1.57), opt("--끝", 1.33), opt("--앞y", 0.06), opt("--뒤y", 0.12), opt("--띄움", 0.012)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
o = max((o for o in bpy.data.objects if o.type == "MESH"), key=lambda o: len(o.data.vertices))
me = o.data; M = np.array(o.matrix_world); Minv = np.linalg.inv(M)
opac = {i for i, s in enumerate(o.material_slots) if s.material and "opacity" in s.material.name}
co = np.zeros(len(me.vertices) * 3); me.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
W = co @ M[:3, :3].T + M[:3, 3]
# 머리카락 점 = opacity 면의 점, 조각 높이 폭 3cm 이상(속눈썹 빼기)
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
hairv = np.zeros(len(W), bool); seen = np.zeros(len(W), bool)
opv = np.zeros(len(W), bool)
for f in bm.faces:
    if f.material_index in opac:
        for v in f.verts: opv[v.index] = True
for v in bm.verts:
    if not opv[v.index] or seen[v.index]: continue
    st = [v]; comp = []; seen[v.index] = True
    while st:
        x = st.pop(); comp.append(x.index)
        for e in x.link_edges:
            y = e.other_vert(x)
            if opv[y.index] and not seen[y.index]: seen[y.index] = True; st.append(y)
    z = W[comp, 2]
    if z.max() - z.min() >= 0.03: hairv[comp] = True
H = np.where(hairv)[0]
front = H[(W[H, 1] < YF) & (W[H, 2] < Z0)]
lowest = W[front, 2].min() if len(front) else Z0 - 0.1
K = max(1.0, (Z0 - ZEND) / max(1e-3, Z0 - lowest))
print("머리카락 점 %d, 앞·옆 가장 낮은 곳 %.3f → 늘이는 배율 %.2f" % (len(H), lowest, K))
P = W.copy()
y = W[H, 1]; kk = 1 + (K - 1) * np.clip((YB - y) / (YB - YF), 0, 1)
below = W[H, 2] < Z0
P[H[below], 2] = Z0 - (Z0 - W[H[below], 2]) * kk[below]
# 앞으로 넘기기: 앞·옆 머리(y < 뒤y)의 늘어난 끝은 어깨 앞(가슴 쪽)으로 — 그대로 내리면 어깨 뒤로 떨어져 앞에서 짧아 보였음
ZS, FW = opt("--어깨", 1.50), opt("--앞으로", 0.9)
sel = H[below]; fw = np.clip((YB - W[sel, 1]) / (YB - YF), 0, 1) * (np.abs(W[sel, 0]) > 0.03)
P[sel, 1] -= np.clip(ZS + 0.03 - P[sel, 2], 0, None) * FW * fw
drape = np.zeros(len(W), bool); drape[sel[fw > 0.5]] = True
# 몸(머리카락 아닌 면)으로 밀어내기 판
body_faces = [f for f in bm.faces if f.material_index not in opac]
vs = [Vector(tuple(W[v.index])) for v in bm.verts]
tree = BVHTree.FromPolygons(vs, [[v.index for v in f.verts] for f in body_faces])
nbr = [[] for _ in range(len(W))]
for e in bm.edges:
    i, j = e.verts[0].index, e.verts[1].index
    if hairv[i] and hairv[j]: nbr[i].append(j); nbr[j].append(i)
moved = H[P[H, 2] < Z0 + 0.02]
for it in range(4):
    for i in moved:
        loc, n, fi, d = tree.find_nearest(Vector(tuple(P[i])))
        if loc is None: continue
        loc = np.array(loc); n = np.array(n)
        s = np.dot(P[i] - loc, n)
        if s < GAP: P[i] = P[i] + n * (GAP - s)
        elif P[i, 2] < ZS and drape[i] and s > GAP + 0.015:          # 어깨 아래 앞으로 넘긴 머리는 몸(가슴)에 얹힘 — 허공에 뜨지 않게
            P[i] = P[i] - n * (s - GAP - 0.015)
    D = P - W                                                  # 옮긴 양을 머리카락 줄 따라 부드럽게
    D2 = D.copy()
    for i in moved:
        if nbr[i]: D2[i] = 0.5 * D[i] + 0.5 * D[nbr[i]].mean(0)
    P[moved] = W[moved] + D2[moved]
bm.free()
dl = (P - W) @ np.linalg.inv(M[:3, :3]).T
kbs = list(me.shape_keys.key_blocks) if me.shape_keys else []
me.vertices.foreach_set("co", (co + dl).ravel())
for kb in kbs:
    arr = np.zeros(len(co) * 3); kb.data.foreach_get("co", arr); kb.data.foreach_set("co", (arr.reshape(-1, 3) + dl).ravel())
me.update()
print("가장 낮은 머리카락 %.3f, 옮긴 점 %d" % (P[H, 2].min(), int((np.linalg.norm(P - W, axis=1) > 1e-5).sum())))
bpy.ops.export_scene.gltf(filepath=dst, export_format="GLB", export_morph=True, export_skins=True, export_animations=False, export_image_format="AUTO")
print("→", dst)
