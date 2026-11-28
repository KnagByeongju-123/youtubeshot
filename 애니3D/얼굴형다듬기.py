"""GLB 인물의 아래 얼굴(코밑~턱)을 짧게·턱을 갸름하게 (사용자 2026-11-28 '얼굴형이 좀 길어서 둔해 보임')
   - 코밑 높이(zn) 아래 점: 코밑~턱 거리를 --줄임 비율만큼 줄여 턱을 올림 (턱 아래 목 쪽은 같은 양만큼 올렸다가 4cm 아래로 갈수록 0)
   - 턱 쪽으로 갈수록 가로를 --갸름 비율만큼 좁힘 (입 높이 0 → 턱 끝 1)
   - 머리 뼈(Head 와 그 아래 뼈) 무게만큼만 → 옷·목 아래는 그대로. 모양 키(입 모양·표정)와 턱·혀 뼈 자리도 같이
   높이는 얼굴 표지점 파일(grid npz 의 dst: [x,z], 2 = 코밑, 152 = 턱 끝)에서
   사용: .bpy_venv/bin/python -I 애니3D/얼굴형다듬기.py <입력.glb> <grid.npz> <출력.glb> [--줄임 0.08] [--갸름 0.06]"""
import sys
import bpy
import numpy as np

a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
src, lm_p, dst = a[0], a[1], a[2]
def opt(k, d): return float(a[a.index(k) + 1]) if k in a else d
K, NAR = opt("--줄임", 0.08), opt("--갸름", 0.06)
L = np.load(lm_p)["dst"]
zn, zm, zc = L[2, 1], L[[13, 14], 1].mean(), L[152, 1]
cx = L[:, 0].mean()
dz = (zn - zc) * K
print("코밑 %.3f 입 %.3f 턱 %.3f → 턱 %.1fmm 올림, 갸름 %.0f%%" % (zn, zm, zc, dz * 1000, NAR * 100))

def move(P):
    """세상 좌표 점들 → 옮긴 자리"""
    x, z = P[:, 0], P[:, 2]
    up = np.where(z >= zn, 0, np.where(z >= zc, (zn - z) * K, dz * np.clip(1 - (zc - z) / 0.04, 0, 1)))
    t = np.clip((zm - z) / (zm - zc), 0, 1) * np.clip(1 - (zc - z) / 0.04, 0, 1) * (z < zm)
    Q = P.copy(); Q[:, 2] = z + up; Q[:, 0] = cx + (x - cx) * (1 - NAR * t)
    return Q

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
arm = next(o for o in bpy.data.objects if o.type == "ARMATURE")
hb = arm.data.bones["Head"]; names = {hb.name} | {c.name for c in hb.children_recursive}
for o in [o for o in bpy.data.objects if o.type == "MESH"]:
    me = o.data; M = np.array(o.matrix_world); Mi3 = np.linalg.inv(M[:3, :3])
    gid = {g.index for g in o.vertex_groups if g.name in names}
    w = np.array([min(1.0, sum(g.weight for g in v.groups if g.group in gid)) for v in me.vertices])
    if not (w > 0.01).any(): continue
    def apply(arr):
        Wd = arr @ M[:3, :3].T + M[:3, 3]
        Wn = Wd + (move(Wd) - Wd) * w[:, None]
        return (Wn - M[:3, 3]) @ Mi3.T
    co = np.zeros(len(me.vertices) * 3); me.vertices.foreach_get("co", co)
    base = co.reshape(-1, 3); nb = apply(base)
    for kb in (me.shape_keys.key_blocks if me.shape_keys else []):
        arr = np.zeros(len(me.vertices) * 3); kb.data.foreach_get("co", arr); arr = arr.reshape(-1, 3)
        kb.data.foreach_set("co", (nb + (apply(arr) - nb) * 0 + (arr - base)).ravel() if False else apply(arr).ravel())
    me.vertices.foreach_set("co", nb.ravel()); me.update()
    print(o.name, "옮긴 점", int(((nb - base) ** 2).sum(1).__gt__(1e-12).sum()))
bpy.context.view_layer.objects.active = arm; bpy.ops.object.mode_set(mode="EDIT")
Ma = np.array(arm.matrix_world); Mai = np.linalg.inv(Ma)
for eb in arm.data.edit_bones:
    if eb.name not in names: continue
    for end in ("head", "tail"):
        p = Ma[:3, :3] @ np.array(getattr(eb, end)) + Ma[:3, 3]
        q = move(p[None])[0]
        setattr(eb, end, type(getattr(eb, end))(Mai[:3, :3] @ (q - Ma[:3, 3])))
bpy.ops.object.mode_set(mode="OBJECT")
bpy.ops.export_scene.gltf(filepath=dst, export_format="GLB", export_morph=True, export_skins=True, export_animations=False, export_image_format="AUTO")
print("→", dst)
