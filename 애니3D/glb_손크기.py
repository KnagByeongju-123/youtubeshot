"""GLB 사람 모델: 손 전체(길이·폭·두께)를 손목을 중심으로 줄임 (사용자 2026-11-27 여자아나운서1 '여자치고는 손이 큼')
   glb_손가늘게.py 는 굵기만 줄임 → 이건 크기 자체를 줄임
   점마다 손·손가락 뼈 무게의 합만큼 손목(Hand 뼈 머리) 쪽으로 당김 → 팔목과 섞인 점은 조금만 움직여 이음매 없음.
   손가락 뼈 자리도 같이 줄여서 자세를 바꿔도 마디가 제자리에서 굽음. 모든 모양 키에도 같은 만큼.
   사용: .bpy_venv/bin/python -I 애니3D/glb_손크기.py <입력.glb> <결과.glb> [--크기 0.88] [--손뼈 Hand]"""
import os, sys
import bpy
import numpy as np

a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
src, dst = a[0], a[1]
S = float(a[a.index("--크기") + 1]) if "--크기" in a else 0.88
HB = a[a.index("--손뼈") + 1] if "--손뼈" in a else "Hand"
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.abspath(src))
arm = next(o for o in bpy.data.objects if o.type == "ARMATURE"); AW = arm.matrix_world
sides = []
for b in arm.data.bones:
    if b.name.split(".")[0] == HB and b.parent and HB not in b.parent.name:
        names = [b.name] + [c.name for c in b.children_recursive]
        sides.append((AW @ b.head_local, names))
print("손", [(n[0], len(n)) for _, n in sides], "크기", S)
for o in bpy.data.objects:
    if o.type != "MESH" or not o.vertex_groups: continue
    mw = o.matrix_world; inv = mw.inverted(); n = len(o.data.vertices)
    gid = {g.index: g.name for g in o.vertex_groups}
    D = np.zeros((n, 3))
    P = np.array([tuple(mw @ v.co) for v in o.data.vertices])
    for piv, names in sides:
        ns = set(names); w = np.zeros(n)
        for v in o.data.vertices:
            w[v.index] = sum(g.weight for g in v.groups if gid.get(g.group) in ns)
        w = np.clip(w, 0, 1); pv = np.array(tuple(piv))
        D += (S - 1) * w[:, None] * (P - pv)
    if not np.abs(D).max() > 0: continue
    L = (np.array(inv.to_3x3()) @ D.T).T                   # 바뀐 만큼을 물체 좌표로
    co = np.empty(n * 3); o.data.vertices.foreach_get("co", co); o.data.vertices.foreach_set("co", (co.reshape(-1, 3) + L).ravel())
    if o.data.shape_keys:
        for k in o.data.shape_keys.key_blocks:
            c = np.empty(n * 3); k.data.foreach_get("co", c); k.data.foreach_set("co", (c.reshape(-1, 3) + L).ravel())
    print(o.name, "움직인 점", int((np.abs(D).sum(1) > 1e-6).sum()))
bpy.context.view_layer.objects.active = arm; bpy.ops.object.mode_set(mode="EDIT"); ai = AW.inverted()
for piv, names in sides:
    pv = ai @ piv
    for nm in names[1:]:
        eb = arm.data.edit_bones[nm]; eb.head = pv + (eb.head - pv) * S; eb.tail = pv + (eb.tail - pv) * S
    eb = arm.data.edit_bones[names[0]]; eb.tail = pv + (eb.tail - pv) * S
bpy.ops.object.mode_set(mode="OBJECT")
for o in list(bpy.data.objects):
    if o.name.startswith("Icosphere"): bpy.data.objects.remove(o)
bpy.ops.export_scene.gltf(filepath=os.path.abspath(dst), export_format="GLB", export_morph=True, export_skins=True, export_animations=False)
print("저장", dst)
