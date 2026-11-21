"""모양만 있는 3D 사람(GLB, 예: 메시 AI)에 앞·뒤·왼쪽·오른쪽 그림을 비춰 섞은 뒤, 피부 그림(텍스처) 한 장으로 구움 (블렌더 Cycles bake)
→ 구운 뒤에는 어느 카메라에서 찍어도 색이 모양에 붙어 있음 (정면 비추기만 하면 옆·뒤가 번지고 원근 카메라에서 손 색이 어긋남)

1) 준비: 점 줄이기 + 펼친 지도(UV) + 네 방향 윤곽 찍기
   .bpy_venv/bin/python -I 실사3D/텍스처_굽기.py 준비 <모델.glb> <폴더>
   → <폴더>/base.blend, sil_앞·뒤·왼쪽·오른쪽.png (그림 크기 832×1248, 정면·평행 카메라)
2) 맞추기 (cv2 가 있는 파이썬, 예: models/ditto/.venv)
   python 실사3D/텍스처_굽기.py 맞추기 <폴더> 앞=<그림> 뒤=<그림> 왼쪽=<그림> 오른쪽=<그림>
   → 그림 속 사람 상자를 윤곽 상자에 맞춰 늘리고 옮김 + 흰 배경을 사람 색으로 번지게 → fit_<방향>.png
   (왼쪽 = 사람의 왼쪽에서 본 옆모습, 그림에서 사람이 왼쪽을 봄 / 오른쪽 = 반대)
3) 굽기
   .bpy_venv/bin/python -I 실사3D/텍스처_굽기.py 굽기 <폴더> [--크기 2048]
   → <폴더>/텍스처.png, 완성.blend, 완성.glb, 확인_앞·45도·옆·뒤.png
"""
import json
import math
import os
import sys

VIEWS = {  # 이름: (카메라 위치 방향, 표면이 이 방향을 볼 때 이 그림을 씀)
    "앞": (0, -1, 0), "뒤": (0, 1, 0), "왼쪽": (1, 0, 0), "오른쪽": (-1, 0, 0)}
IW, IH = 832, 1248
OSCALE = 2.1                      # 정면·평행 카메라가 담는 높이(세로가 긴 그림이라 높이 기준)
PRIORITY = {"앞": 2.0, "뒤": 1.0, "왼쪽": 0.8, "오른쪽": 0.8}   # 앞 그림(원본)이 가장 정확 → 많이 씀


def opt(a, k, d):
    return a[a.index(k) + 1] if k in a else d


def cams(bpy, mathutils, sc, center):
    out = {}
    for nm, d in VIEWS.items():
        c = bpy.data.objects.new("cam_" + nm, bpy.data.cameras.new("cam_" + nm))
        sc.collection.objects.link(c)
        c.data.type = 'ORTHO'
        c.data.ortho_scale = OSCALE
        c.location = center + mathutils.Vector(d) * 5
        c.rotation_euler = (center - c.location).to_track_quat('-Z', 'Y').to_euler()
        out[nm] = c
    return out


def prep(a):
    import bpy
    import mathutils
    glb, folder = a[0], os.path.abspath(a[1])
    os.makedirs(folder, exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=glb)
    sc = bpy.context.scene
    ob = next(o for o in sc.objects if o.type == 'MESH')
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    n0 = len(ob.data.vertices)
    if n0 > 80000:
        md = ob.modifiers.new("dec", 'DECIMATE')
        md.ratio = 70000 / n0
        bpy.ops.object.modifier_apply(modifier="dec")
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.003)
    bpy.ops.object.mode_set(mode='OBJECT')
    ob.data.uv_layers[0].name = "bake"
    pts = [ob.matrix_world @ mathutils.Vector(c) for c in ob.bound_box]
    center = sum(pts, mathutils.Vector()) / 8
    cm = cams(bpy, mathutils, sc, center)
    sc.render.engine = 'BLENDER_WORKBENCH'
    sc.render.film_transparent = True
    sc.render.resolution_x, sc.render.resolution_y = IW, IH
    for nm, c in cm.items():
        sc.camera = c
        sc.render.filepath = os.path.join(folder, f"sil_{nm}.png")
        bpy.ops.render.render(write_still=True)
    json.dump({"center": list(center)}, open(os.path.join(folder, "info.json"), "w"))
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(folder, "base.blend"))
    print("준비 끝: 점", n0, "→", len(ob.data.vertices))


def fit(a):
    import cv2
    import numpy as np
    folder = a[0]
    for kv in a[1:]:
        nm, path = kv.split("=", 1)
        sil = cv2.imread(os.path.join(folder, f"sil_{nm}.png"), cv2.IMREAD_UNCHANGED)[..., 3] > 128
        im = cv2.imread(path)
        g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
        fg = (g < 225).astype(np.uint8)
        fg = cv2.morphologyEx(fg, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))   # 점·워터마크 같은 작은 것 빼기

        def box(m):
            ys = np.where(m.sum(1) > 3)[0]
            xs = np.where(m.sum(0) > 3)[0]
            return xs.min(), ys.min(), xs.max(), ys.max()
        sx0, sy0, sx1, sy1 = box(sil)
        ix0, iy0, ix1, iy1 = box(fg)
        kx, ky = (sx1 - sx0) / max(1, ix1 - ix0), (sy1 - sy0) / max(1, iy1 - iy0)
        M = np.float32([[kx, 0, sx0 - ix0 * kx], [0, ky, sy0 - iy0 * ky]])
        warp = cv2.warpAffine(im, M, (IW, IH), flags=cv2.INTER_LINEAR, borderValue=(255, 255, 255))
        m = cv2.warpAffine(fg * 255, M, (IW, IH)) > 128
        m = cv2.erode(m.astype(np.uint8), np.ones((3, 3), np.uint8))
        out = warp.copy()
        for _ in range(80):                                   # 사람 색을 바깥으로 번지게 (흰 테두리 막기)
            s = cv2.blur((out * m[..., None]).astype(np.float32), (3, 3))
            w = cv2.blur(m.astype(np.float32), (3, 3))[..., None]
            dm = cv2.dilate(m, np.ones((3, 3), np.uint8))
            new = (dm == 1) & (m == 0)
            out[new] = (s[new] / np.maximum(w[new], 1e-6)).astype(np.uint8)
            m = dm
        cv2.imwrite(os.path.join(folder, f"fit_{nm}.png"), out)
        print(nm, "맞춤: 가로", round(kx, 3), "세로", round(ky, 3))


def bake(a):
    import bpy
    import mathutils
    folder = os.path.abspath(a[0])
    size = int(opt(a, "--크기", 2048))
    bpy.ops.wm.open_mainfile(filepath=os.path.join(folder, "base.blend"))
    sc = bpy.context.scene
    ob = next(o for o in sc.objects if o.type == 'MESH')
    names = [nm for nm in VIEWS if os.path.exists(os.path.join(folder, f"fit_{nm}.png"))]
    m = bpy.data.materials.new("구움")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    outn = nt.nodes.new('ShaderNodeOutputMaterial')
    emit = nt.nodes.new('ShaderNodeEmission')
    nt.links.new(emit.outputs[0], outn.inputs['Surface'])
    geo = nt.nodes.new('ShaderNodeNewGeometry')
    acc_c, acc_w = None, None
    for nm in names:
        uvname = "p_" + nm
        if uvname not in ob.data.uv_layers:
            ob.data.uv_layers.new(name=uvname)
        md = ob.modifiers.new("uvp_" + nm, 'UV_PROJECT')
        md.uv_layer = uvname
        md.projector_count = 1
        md.projectors[0].object = bpy.data.objects["cam_" + nm]
        md.aspect_x, md.aspect_y = IW, IH
        tex = nt.nodes.new('ShaderNodeTexImage')
        tex.image = bpy.data.images.load(os.path.join(folder, f"fit_{nm}.png"))
        tex.extension = 'EXTEND'
        uv = nt.nodes.new('ShaderNodeUVMap')
        uv.uv_map = uvname
        nt.links.new(uv.outputs[0], tex.inputs[0])
        dot = nt.nodes.new('ShaderNodeVectorMath')
        dot.operation = 'DOT_PRODUCT'
        nt.links.new(geo.outputs['Normal'], dot.inputs[0])
        dot.inputs[1].default_value = VIEWS[nm]                      # 표면이 이 카메라 쪽을 볼수록 큼
        mx = nt.nodes.new('ShaderNodeMath')
        mx.operation = 'MAXIMUM'
        mx.inputs[1].default_value = 0.0
        nt.links.new(dot.outputs['Value'], mx.inputs[0])
        pw = nt.nodes.new('ShaderNodeMath')
        pw.operation = 'POWER'
        pw.inputs[1].default_value = 4.0                              # 비스듬한 면은 덜 (번짐 줄이기)
        nt.links.new(mx.outputs[0], pw.inputs[0])
        wt = nt.nodes.new('ShaderNodeMath')
        wt.operation = 'MULTIPLY'
        wt.inputs[1].default_value = PRIORITY[nm]
        nt.links.new(pw.outputs[0], wt.inputs[0])
        cw = nt.nodes.new('ShaderNodeMix')
        cw.data_type = 'RGBA'
        cw.blend_type = 'MULTIPLY'
        cw.inputs['Factor'].default_value = 1.0
        nt.links.new(tex.outputs['Color'], cw.inputs[6])
        cmb = nt.nodes.new('ShaderNodeCombineColor')
        for i in range(3):
            nt.links.new(wt.outputs[0], cmb.inputs[i])
        nt.links.new(cmb.outputs[0], cw.inputs[7])
        if acc_c is None:
            acc_c, acc_w = cw.outputs[2], wt.outputs[0]
        else:
            ac = nt.nodes.new('ShaderNodeMix')
            ac.data_type = 'RGBA'
            ac.blend_type = 'ADD'
            ac.inputs['Factor'].default_value = 1.0
            nt.links.new(acc_c, ac.inputs[6])
            nt.links.new(cw.outputs[2], ac.inputs[7])
            aw = nt.nodes.new('ShaderNodeMath')
            aw.operation = 'ADD'
            nt.links.new(acc_w, aw.inputs[0])
            nt.links.new(wt.outputs[0], aw.inputs[1])
            acc_c, acc_w = ac.outputs[2], aw.outputs[0]
    eps = nt.nodes.new('ShaderNodeMath')
    eps.operation = 'MAXIMUM'
    eps.inputs[1].default_value = 1e-4
    nt.links.new(acc_w, eps.inputs[0])
    dv = nt.nodes.new('ShaderNodeMix')
    dv.data_type = 'RGBA'
    dv.blend_type = 'DIVIDE'
    dv.inputs['Factor'].default_value = 1.0
    nt.links.new(acc_c, dv.inputs[6])
    cmb = nt.nodes.new('ShaderNodeCombineColor')
    for i in range(3):
        nt.links.new(eps.outputs[0], cmb.inputs[i])
    nt.links.new(cmb.outputs[0], dv.inputs[7])
    nt.links.new(dv.outputs[2], emit.inputs['Color'])
    img = bpy.data.images.new("텍스처", size, size)
    tgt = nt.nodes.new('ShaderNodeTexImage')
    tgt.image = img
    nt.nodes.active = tgt
    ob.data.materials.clear()
    ob.data.materials.append(m)
    ob.data.uv_layers.active = ob.data.uv_layers["bake"]
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    sc.render.engine = 'CYCLES'
    sc.cycles.device = 'CPU'
    sc.cycles.samples = 1
    sc.render.bake.margin = 8
    bpy.ops.object.bake(type='EMIT')
    tpath = os.path.join(folder, "텍스처.png")
    img.filepath_raw = tpath
    img.file_format = 'PNG'
    img.save()
    # 완성 재질: 구운 그림 하나
    for md in list(ob.modifiers):
        ob.modifiers.remove(md)
    for nm in names:
        ob.data.uv_layers.remove(ob.data.uv_layers["p_" + nm])
    f = bpy.data.materials.new("피부")
    f.use_nodes = True
    b = f.node_tree.nodes["Principled BSDF"]
    t = f.node_tree.nodes.new('ShaderNodeTexImage')
    t.image = bpy.data.images.load(tpath)
    f.node_tree.links.new(t.outputs['Color'], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.7
    ob.data.materials.clear()
    ob.data.materials.append(f)
    # 확인 사진 (원근 카메라, 4방향)
    for o in [o for o in sc.objects if o.type == 'CAMERA']:
        bpy.data.objects.remove(o)
    center = mathutils.Vector(json.load(open(os.path.join(folder, "info.json")))["center"])
    w = bpy.data.worlds.new("w")
    sc.world = w
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (0.85, 0.86, 0.9, 1)
    w.node_tree.nodes["Background"].inputs[1].default_value = 0.9
    L = bpy.data.objects.new("key", bpy.data.lights.new("key", "AREA"))
    L.data.energy = 150
    L.data.size = 2
    L.location = center + mathutils.Vector((-1.5, -2.5, 1.5))
    L.rotation_euler = (center - L.location).to_track_quat('-Z', 'Y').to_euler()
    sc.collection.objects.link(L)
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
    sc.collection.objects.link(cam)
    sc.camera = cam
    cam.data.lens = 50
    sc.cycles.samples = 24
    sc.cycles.use_denoising = True
    sc.view_settings.view_transform = 'Standard'
    sc.render.resolution_x, sc.render.resolution_y = 400, 800
    for nm, ang in (("앞", 0), ("45도", 45), ("옆", 90), ("뒤", 180)):
        t_ = math.radians(ang)
        cam.location = center + mathutils.Vector((5.5 * math.sin(t_), -5.5 * math.cos(t_), 0.1))
        cam.rotation_euler = (center - cam.location).to_track_quat('-Z', 'Y').to_euler()
        sc.render.filepath = os.path.join(folder, f"확인_{nm}.png")
        bpy.ops.render.render(write_still=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(folder, "완성.blend"))
    bpy.ops.export_scene.gltf(filepath=os.path.join(folder, "완성.glb"), use_selection=False)
    print("굽기 끝:", tpath)


if __name__ == "__main__":
    {"준비": prep, "맞추기": fit, "굽기": bake}[sys.argv[1]](sys.argv[2:])
