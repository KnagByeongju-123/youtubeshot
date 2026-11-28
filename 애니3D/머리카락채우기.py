"""GLB 인물의 머리카락 빈곳 채우기 (사용자 2026-11-28 '머리카락 빈곳을 채워줘' — 양옆 긴 머리가 얇은 띠로 갈라져 사이로 배경·목이 보였음)
   ① 넓히기: 머리카락 조각(opacity 재질, 높이 폭 3cm 이상)마다 길이 방향(주성분)은 두고 폭 방향만 --넓히기 배 → 띠 사이 틈이 메워짐
   ② 속층: 머리카락을 한 벌 더 복사해 머리 가운데 쪽으로 오므림(가로 --속층 배, 뒤로 --뒤로 m) → 바깥 띠 뒤에 한 겹 더 (목 뒤 그늘처럼 빈 곳이 어두워짐)
   뼈 무게·모양 키는 복사본도 그대로 가짐
   사용: .bpy_venv/bin/python -I 애니3D/머리카락채우기.py <입력.glb> <출력.glb> [--넓히기 1.5] [--속층 0.88] [--뒤로 0.01] [--속층없음] [--넓힐높이 1.56]"""
import sys
import bpy, bmesh
import numpy as np

a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
src, dst = a[0], a[1]
def opt(k, d): return float(a[a.index(k) + 1]) if k in a else d
WID, INN, BACK = opt("--넓히기", 1.5), opt("--속층", 0.88), opt("--뒤로", 0.01)
ZW = opt("--넓힐높이", 1.56); XW = opt("--넓힐옆", 0.075); YW = opt("--넓힐앞", 0.06)       # 이 높이 아래부터 점점 넓힘
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
o = max((o for o in bpy.data.objects if o.type == "MESH"), key=lambda o: len(o.data.vertices))
me = o.data; M = np.array(o.matrix_world); Mi3 = np.linalg.inv(M[:3, :3])
opac = {i for i, s in enumerate(o.material_slots) if s.material and "opacity" in s.material.name}
arm = next(x for x in bpy.data.objects if x.type == "ARMATURE")
head = np.array(arm.matrix_world @ arm.data.bones["Head"].head_local)

def hair_comps(bm, W):
    opv = np.zeros(len(W), bool)
    for f in bm.faces:
        if f.material_index in opac:
            for v in f.verts: opv[v.index] = True
    seen = np.zeros(len(W), bool); out = []
    for v in bm.verts:
        if not opv[v.index] or seen[v.index]: continue
        st = [v]; c = []; seen[v.index] = True
        while st:
            x = st.pop(); c.append(x.index)
            for e in x.link_edges:
                y = e.other_vert(x)
                if opv[y.index] and not seen[y.index]: seen[y.index] = True; st.append(y)
        if np.ptp(W[c, 2]) >= 0.03: out.append(np.array(c))
    return out

def all_co(): c = np.zeros(len(me.vertices) * 3); me.vertices.foreach_get("co", c); return c.reshape(-1, 3)
kbs = list(me.shape_keys.key_blocks) if me.shape_keys else []

# ② 속층 (먼저 복사 — 그다음 넓히기는 바깥·속층 모두에)
if "--속층없음" not in a:
    bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
    W = all_co() @ M[:3, :3].T + M[:3, 3]
    comps = hair_comps(bm, W)
    hv = set(np.concatenate(comps).tolist())
    faces = [f for f in bm.faces if f.material_index in opac and all(v.index in hv for v in f.verts) and min(W[v.index, 2] for v in f.verts) < ZW and max(W[v.index, 1] for v in f.verts) < 0.10]   # 귀 아래 옆·앞 머리만 속층
    n0 = len(bm.verts)
    ret = bmesh.ops.duplicate(bm, geom=faces)
    newv = [g for g in ret["geom"] if isinstance(g, bmesh.types.BMVert)]
    bm.verts.index_update(); ids = np.array([v.index for v in newv])
    bm.to_mesh(me); bm.free(); me.update()
    # 복사본 점을 머리 가운데(세로축) 쪽으로: x 는 INN 배, y 는 머리 중심 쪽으로 + 뒤로
    for blk in [None] + kbs:
        arr = all_co() if blk is None else np.array([d.co for d in blk.data])
        Wb = arr @ M[:3, :3].T + M[:3, 3]
        P = Wb[ids].copy()
        P[:, 0] = head[0] + (P[:, 0] - head[0]) * INN
        P[:, 1] = head[1] + (P[:, 1] - head[1]) * INN + BACK
        Wb[ids] = P
        nb = (Wb - M[:3, 3]) @ Mi3.T
        if blk is None: me.vertices.foreach_set("co", nb.ravel())
        else: blk.data.foreach_set("co", nb.ravel())
    me.update()
    print("속층 추가: 점", len(ids), "면", len(faces))

# ① 넓히기
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
base = all_co(); W = base @ M[:3, :3].T + M[:3, 3]
comps = hair_comps(bm, W); bm.free()
blocks = [base] + [np.array([d.co for d in kb.data]) for kb in kbs]
for c in comps:
    P = W[c]; cen = P.mean(0)
    if cen[1] > YW or np.ptp(P[:, 1]) > 0.08: continue          # 뒤 머리·크게 휜 조각은 그대로 (넓히면 날개처럼 뻗었음)
    _, _, Vt = np.linalg.svd(P - cen, full_matrices=False)
    ax = Vt[0]                                                  # 길이 방향
    for arr in blocks:
        Wb = arr[c] @ M[:3, :3].T + M[:3, 3]
        d = Wb - cen; along = (d @ ax)[:, None] * ax
        side = d - along
        side_h = side - (side @ np.array([0, 0, 1.0]))[:, None] * np.array([0, 0, 1.0]) * 0   # 폭(옆) 성분
        zr = np.maximum(np.clip((ZW - Wb[:, 2]) / 0.06, 0, 1), np.clip((np.abs(Wb[:, 0]) - XW) / 0.015, 0, 1) * (Wb[:, 1] > -0.04) * (Wb[:, 1] < YW))[:, None]   # + 관자놀이 옆 가닥     # 귀 아래 늘어진 머리만 넓힘 (앞머리·정수리는 그대로 — 넓히면 이마가 지저분했음)
        Wn = cen + along + side * (1 + (WID - 1) * zr)
        arr[c] = (Wn - M[:3, 3]) @ Mi3.T
me.vertices.foreach_set("co", blocks[0].ravel())
for kb, arr in zip(kbs, blocks[1:]): kb.data.foreach_set("co", arr.ravel())
me.update()
print("넓힌 머리카락 조각", len(comps), "배율", WID)
bpy.ops.export_scene.gltf(filepath=dst, export_format="GLB", export_morph=True, export_skins=True, export_animations=False, export_image_format="AUTO")
print("→", dst)
