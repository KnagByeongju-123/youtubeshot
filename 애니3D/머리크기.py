"""GLB 인물의 머리(얼굴·머리카락·눈·이·입속 + 머리 안 뼈)만 키우거나 줄임 — 목 이음매는 부드럽게 (사용자 2026-11-27 '몸 전체 비율에서 얼굴 비율이 샘플에 비해 작음')
   - 점마다 Head 뼈와 그 아래 뼈들(턱·눈·얼굴 뼈)의 무게 합 w 만큼 배율: 1 + (배율-1)·w, 중심 = Head 뼈 뿌리(목 위) → 목 쪽은 섞여 자연스럽게 이어짐
   - 모양 키(입 모양·표정)도 같은 배율, 머리 안 뼈(눈·턱)의 자리도 같이 옮김 → 눈 굴리기·턱 벌리기 그대로
   - --목표비율 0.143 : 머리 높이(머리끝~턱) ÷ 키 를 이 값이 되게 배율을 계산 (턱 높이는 --턱 z, 없으면 --배율 로 직접)
   사용: .bpy_venv/bin/python -I 애니3D/머리크기.py <입력.glb> <출력.glb> (--배율 1.08 | --목표비율 0.143 --턱 1.507) [--머리뼈 Head]"""
import sys
import bpy
import numpy as np
from mathutils import Vector

a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
src, dst = a[0], a[1]
def opt(k, d): return a[a.index(k) + 1] if k in a else d
HB = opt("--머리뼈", "Head")
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
arm = next(o for o in bpy.data.objects if o.type == "ARMATURE")
meshes = [o for o in bpy.data.objects if o.type == "MESH"]
hb = arm.data.bones[HB]
names = {hb.name} | {c.name for c in hb.children_recursive}
piv_w = arm.matrix_world @ hb.head_local
body = max(meshes, key=lambda o: len(o.data.vertices))      # 사람 몸(가장 큰 그물) — 파일에 딸린 작은 공(Icosphere) 등은 키 재기에서 뺌
allW = np.array([body.matrix_world @ v.co for v in body.data.vertices])
top, bot = allW[:, 2].max(), allW[:, 2].min()
if "--목표비율" in a:
    R = float(opt("--목표비율", "0.143")); chin = float(opt("--턱", "1.507")); h = top - chin; H = top - bot
    S = R * (H - h) / (h - R * h)          # (h·S) / (H - h + h·S) = R
else:
    S = float(opt("--배율", "1.08"))
print("머리끝 %.3f 바닥 %.3f, 배율 %.3f, 중심 %s, 머리 뼈 %d개" % (top, bot, S, tuple(round(v, 3) for v in piv_w), len(names)))

for o in meshes:
    me = o.data; mw = o.matrix_world; inv = mw.inverted()
    piv = np.array(inv @ piv_w)
    gid = {g.index for g in o.vertex_groups if g.name in names}
    w = np.zeros(len(me.vertices))
    for v in me.vertices:
        w[v.index] = min(1.0, sum(g.weight for g in v.groups if g.group in gid))
    f = 1 + (S - 1) * w
    def scl(arr): return piv + (arr - piv) * f[:, None]
    kbs = list(me.shape_keys.key_blocks) if me.shape_keys else []
    co = np.zeros(len(me.vertices) * 3); me.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
    me.vertices.foreach_set("co", scl(co).ravel())
    for kb in kbs:
        arr = np.zeros(len(me.vertices) * 3); kb.data.foreach_get("co", arr); kb.data.foreach_set("co", scl(arr.reshape(-1, 3)).ravel())
    me.update()
    print(o.name, "머리에 묶인 점", int((w > 0.01).sum()))

bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode="EDIT")
piv_a = arm.matrix_world.inverted() @ piv_w
for eb in arm.data.edit_bones:
    if eb.name in names:
        eb.head = piv_a + (eb.head - piv_a) * S
        eb.tail = piv_a + (eb.tail - piv_a) * S
bpy.ops.object.mode_set(mode="OBJECT")
bpy.ops.export_scene.gltf(filepath=dst, export_format="GLB", export_morph=True, export_skins=True, export_animations=False, export_image_format="AUTO")
print("→", dst)
