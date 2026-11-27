"""GLB 인물의 속눈썹을 짧고 연하게 (사용자 2026-11-27 '속눈썹 자연스럽게 연하고 짧게' — Rocketbox 속눈썹이 길고 진해 화장한 눈처럼 보였음)
   - 속눈썹 = opacity 재질 조각 중 높이 폭 3cm 미만, 눈 높이·얼굴 앞(y<0)인 것
   - 짧게: 조각마다 뿌리(눈알 중심 = 눈 뼈에 가장 가까운 점들) 쪽으로 점을 당김(위 --위 배율, 아래 --아래 배율). 모양 키(눈 감기 등)마다 같은 방식 → 깜빡임 그대로
   - 연하게: 그 조각들이 쓰는 그림 칸(UV)만 투명도 × --진하기, 색은 짙은 갈색 쪽으로 (--색)
   사용: .bpy_venv/bin/python -I 애니3D/속눈썹다듬기.py <입력.glb> <출력.glb> [--위 0.6] [--아래 0.5] [--진하기 0.6] [--색 40,30,26] [--감을때 0.3] [--감을때뒤집기] [--꺼풀따라] [--눈띠지우기]"""
import sys
import bpy, bmesh
import numpy as np

a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
src, dst = a[0], a[1]
def opt(k, d): return a[a.index(k) + 1] if k in a else d
SU, SL, DEN = float(opt("--위", "0.6")), float(opt("--아래", "0.5")), float(opt("--진하기", "0.6"))
CLOSE = float(opt("--감을때", "0.65")); FLIP = "--감을때뒤집기" in a; FOLLOW = "--꺼풀따라" in a   # 눈 감기 키에서 윗속눈썹 배율 (예: 0.3)
COL = np.array([float(v) for v in opt("--색", "40,30,26").split(",")]) / 255
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
o = max((o for o in bpy.data.objects if o.type == "MESH"), key=lambda o: len(o.data.vertices))
arm = next(x for x in bpy.data.objects if x.type == "ARMATURE")
me = o.data; M = np.array(o.matrix_world)
opac = {i for i, s in enumerate(o.material_slots) if s.material and "opacity" in s.material.name}
eyes = [np.array(arm.matrix_world @ b.head_local) for b in arm.data.bones if b.name.endswith(("LEye", "REye"))]
print("눈 뼈", len(eyes), [tuple(np.round(e, 3)) for e in eyes])
co = np.zeros(len(me.vertices) * 3); me.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
W = co @ M[:3, :3].T + M[:3, 3]
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
opv = np.zeros(len(W), bool)
for f in bm.faces:
    if f.material_index in opac:
        for v in f.verts: opv[v.index] = True
seen = np.zeros(len(W), bool); lashes = []
for v in bm.verts:
    if not opv[v.index] or seen[v.index]: continue
    st = [v]; comp = []; seen[v.index] = True
    while st:
        x = st.pop(); comp.append(x.index)
        for e in x.link_edges:
            y = e.other_vert(x)
            if opv[y.index] and not seen[y.index]: seen[y.index] = True; st.append(y)
    P = W[comp]; ez = np.mean([e[2] for e in eyes])
    if np.ptp(P[:, 2]) < 0.03 and abs(P[:, 2].mean() - ez) < 0.03 and P[:, 1].mean() < 0: lashes.append(np.array(comp))
print("속눈썹 조각", len(lashes))
from mathutils.kdtree import KDTree
skin = np.where(~opv)[0]; ez0 = np.mean([e[2] for e in eyes])
skin = skin[np.abs(W[skin, 2] - ez0) < 0.03]
kd = KDTree(len(skin))
for i in skin: kd.insert(tuple(W[i]), int(i))
kd.balance()
kbs = list(me.shape_keys.key_blocks) if me.shape_keys else []
def key_co(kb): arr = np.zeros(len(co) * 3); kb.data.foreach_get("co", arr); return arr.reshape(-1, 3)
blocks = [(None, co)] + [(kb, key_co(kb)) for kb in kbs]
co_orig = co.copy()
lash_faces = []
for comp in lashes:
    eye = min(eyes, key=lambda e: np.linalg.norm(W[comp].mean(0) - e))
    dist = np.array([kd.find(tuple(W[i]))[2] for i in comp])      # 눈꺼풀 피부까지 거리
    root = comp[dist <= dist.min() + 0.0012]                        # 뿌리 = 눈꺼풀에 붙은 줄 (눈 뼈 기준은 반대쪽 끝을 잡기도 했음)
    upper = W[comp, 2].mean() > W[root, 2].mean()
    skin_of_root = np.array([kd.find(tuple(W[i]))[1] for i in root])                   # 뿌리보다 위로 뻗으면 윗속눈썹
    s = SU if upper else SL
    for kb, arr in blocks:
        R = arr[root]
        near = np.argmin(np.linalg.norm(arr[comp][:, None] - R[None], axis=2), axis=1)
        s2 = s
        if upper and kb is not None and any(t in kb.name for t in ("Blink", "EyeClosed")):
            s2 = CLOSE                                              # 눈 감기 모양: 윗속눈썹을 더 짧게 — 감으면 빗살처럼 서서 꺼풀을 덮었음 (2026-11-27)
        if FOLLOW and s2 is CLOSE:                                  # 감기 모양: 윗속눈썹을 눈꺼풀 끝(뿌리에 가장 가까운 피부 점)이 내려간 만큼 같이 내림
            base_c = blocks[0][1]                                   # (이미 줄인) 뜬 눈 자리에서 시작
            Rb = base_c[root]; nb = np.argmin(np.linalg.norm(base_c[comp][:, None] - Rb[None], axis=2), axis=1)
            near_sk = skin[np.linalg.norm(W[skin] - W[root].mean(0), axis=1) < 0.006]
            dsk = arr[near_sk] - co_orig[near_sk]                   # 뿌리 둘레 피부가 움직인 양 — 가장 많이 내려간 피부(눈꺼풀 끝)를 따라감
            mvw = dsk @ M[:3, :3].T
            mv = np.repeat(dsk[[np.argmin(mvw[:, 2])]], len(root), 0)
            arr[comp] = base_c[comp] + mv[0]
            R = arr[root]; near = np.argmin(np.linalg.norm(arr[comp][:, None] - R[None], axis=2), axis=1)
            s2 = 1.0 if CLOSE >= 0.99 else CLOSE / s
        dlt = (arr[comp] - R[near]) * s2
        if FLIP and any(t in (kb.name if kb is not None else "") for t in ("Blink", "EyeClosed")) and upper:                                    # 감은 눈: 위로 서서 꺼풀을 덮던 윗속눈썹을 아래로 뒤집음(실제 감은 눈처럼)
            dl_w = dlt @ M[:3, :3].T                                # 물체 → 세상 방향
            dl_w[:, 2] = -np.abs(dl_w[:, 2])
            dlt = dl_w @ np.linalg.inv(M[:3, :3]).T
        arr[comp] = R[near] + dlt
for f in bm.faces:
    if f.material_index in opac and all(any(v.index in set(c) for c in lashes) for v in f.verts[:1]): lash_faces.append(f.index)
me.vertices.foreach_set("co", blocks[0][1].ravel())
for kb, arr in blocks[1:]: kb.data.foreach_set("co", arr.ravel())
me.update()
# 그림: 속눈썹 면들의 UV 칸만 연하게
uvl = me.uv_layers.active.data
img = None
for idx in opac:
    nt = o.material_slots[idx].material.node_tree
    for n in nt.nodes:
        if n.type == "TEX_IMAGE" and n.image: img = n.image
    if img is None: continue
    w_, h_ = img.size; px = np.zeros(w_ * h_ * 4, np.float32); img.pixels.foreach_get(px); px = px.reshape(h_, w_, 4)
    import cv2
    mask = np.zeros((h_, w_), np.uint8)
    for fi in lash_faces:
        poly = me.polygons[fi]
        if poly.material_index != idx: continue
        pts = np.array([[uvl[li].uv[0] * w_, uvl[li].uv[1] * h_] for li in poly.loop_indices], np.int32)
        cv2.fillConvexPoly(mask, cv2.convexHull(pts), 1)
    mask = cv2.dilate(mask, np.ones((5, 5), np.uint8)).astype(bool)
    px[mask, 3] *= DEN
    px[mask, :3] = px[mask, :3] * 0.6 + COL * 0.4
    img.pixels.foreach_set(px.ravel()); img.pack()
    print("그림", img.name, "속눈썹 칸 %.2f%%" % (mask.mean() * 100))
bm.free()
if "--눈띠지우기" in a:   # 눈가의 작은 얼굴 재질 띠(점 200개 미만, 눈 높이, 얼굴 앞) — 눈 감을 때 안 따라 내려와 빗살 무늬로 남았음 (2026-11-27)
    bm2 = bmesh.new(); bm2.from_mesh(me); bm2.verts.ensure_lookup_table()
    Wn = np.array([v.co for v in me.vertices]) @ M[:3, :3].T + M[:3, 3]
    seen2 = np.zeros(len(Wn), bool); kill = []
    ez0 = np.mean([e[2] for e in eyes])
    for v in bm2.verts:
        if seen2[v.index]: continue
        st = [v]; cp = []; seen2[v.index] = True
        while st:
            x = st.pop(); cp.append(x)
            for e in x.link_edges:
                y = e.other_vert(x)
                if not seen2[y.index]: seen2[y.index] = True; st.append(y)
        idx = [x.index for x in cp]; P = Wn[idx]
        mats = {f.material_index for x in cp for f in x.link_faces}
        if len(cp) < 200 and not (mats & opac) and abs(P[:, 2].mean() - ez0) < 0.02 and P[:, 1].mean() < -0.03:
            kill += cp; print("눈띠 지움: 점", len(cp), "가운데 x %+.3f" % P[:, 0].mean())
    bmesh.ops.delete(bm2, geom=kill, context="VERTS"); bm2.to_mesh(me); bm2.free(); me.update()
bpy.ops.export_scene.gltf(filepath=dst, export_format="GLB", export_morph=True, export_skins=True, export_animations=False, export_image_format="AUTO")
print("→", dst)
