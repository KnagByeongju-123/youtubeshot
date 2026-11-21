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
        k = (sy1 - sy0) / max(1, iy1 - iy0)                  # 가로세로 같은 배율 (그림이 찌그러지지 않게)

        def mid(m, y0, y1):                                  # 몸통 띠(서류·팔 말고 가운데 몸)의 가로 가운데
            band = m[int(y0 + (y1 - y0) * 0.35):int(y0 + (y1 - y0) * 0.6)]
            xs = np.where(band.any(0))[0]
            cols = band.sum(0)
            return float((np.arange(len(cols)) * cols).sum() / max(1, cols.sum()))
        cs, ci = mid(sil, sy0, sy1), mid(fg, iy0, iy1)
        kx = ky = k
        M = np.float32([[k, 0, cs - ci * k], [0, k, sy0 - iy0 * k]])
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
    """방향마다 ① 그 그림을 비춘 색(P) ② 그 방향에서 실제로 보이는 정도(M: 그 방향 햇빛의 직접광, 가려진 곳은 0)를 따로 구운 뒤
    색 = Σ M^3·우선순위·P / Σ ... 로 섞음 → 서류 뒤·허벅지 안쪽처럼 그 방향에서 안 보이는 곳에 앞의 색이 묻지 않음"""
    import bpy
    import mathutils
    import numpy as np
    folder = os.path.abspath(a[0])
    size = int(opt(a, "--크기", 2048))
    bpy.ops.wm.open_mainfile(filepath=os.path.join(folder, "base.blend"))
    sc = bpy.context.scene
    sc.render.film_transparent = False
    ob = next(o for o in sc.objects if o.type == 'MESH')
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    for o in [o for o in sc.objects if o.type == 'LIGHT']:
        bpy.data.objects.remove(o)
    w0 = bpy.data.worlds.new("검정")
    sc.world = w0
    w0.use_nodes = True
    w0.node_tree.nodes["Background"].inputs[1].default_value = 0.0
    sc.render.engine = 'CYCLES'
    sc.cycles.device = 'CPU'
    sc.cycles.samples = 4
    sc.render.bake.margin = 0
    names = [nm for nm in VIEWS if os.path.exists(os.path.join(folder, f"fit_{nm}.png"))]

    def target_mat(make_surface):
        m = bpy.data.materials.new("tmp")
        m.use_nodes = True
        nt = m.node_tree
        nt.nodes.clear()
        outn = nt.nodes.new('ShaderNodeOutputMaterial')
        make_surface(nt, outn)
        img = bpy.data.images.new("t", size, size, float_buffer=True)
        tgt = nt.nodes.new('ShaderNodeTexImage')
        tgt.image = img
        nt.nodes.active = tgt
        ob.data.materials.clear()
        ob.data.materials.append(m)
        ob.data.uv_layers.active = ob.data.uv_layers["bake"]
        return img

    def pix(img):
        a_ = np.empty(size * size * 4, np.float32)
        img.pixels.foreach_get(a_)
        return a_.reshape(size, size, 4)

    acc = np.zeros((size, size, 3), np.float32)
    accw = np.zeros((size, size), np.float32)
    for nm in names:
        uvname = "p_" + nm
        if uvname not in ob.data.uv_layers:
            ob.data.uv_layers.new(name=uvname)
        for md in list(ob.modifiers):
            ob.modifiers.remove(md)
        md = ob.modifiers.new("uvp", 'UV_PROJECT')
        md.uv_layer = uvname
        md.projector_count = 1
        md.projectors[0].object = bpy.data.objects["cam_" + nm]
        md.aspect_x, md.aspect_y = IW, IH

        def col(nt, outn, nm=nm, uvname=uvname):
            emit = nt.nodes.new('ShaderNodeEmission')
            tex = nt.nodes.new('ShaderNodeTexImage')
            tex.image = bpy.data.images.load(os.path.join(folder, f"fit_{nm}.png"))
            tex.extension = 'EXTEND'
            uv = nt.nodes.new('ShaderNodeUVMap')
            uv.uv_map = uvname
            nt.links.new(uv.outputs[0], tex.inputs[0])
            nt.links.new(tex.outputs['Color'], emit.inputs['Color'])
            nt.links.new(emit.outputs[0], outn.inputs['Surface'])
        img = target_mat(col)
        bpy.ops.object.bake(type='EMIT')
        P = pix(img)[..., :3]

        def vis(nt, outn):
            d = nt.nodes.new('ShaderNodeBsdfDiffuse')
            d.inputs['Color'].default_value = (1, 1, 1, 1)
            nt.links.new(d.outputs[0], outn.inputs['Surface'])
        img2 = target_mat(vis)
        sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN"))
        sun.data.energy = 3.14159
        sun.data.angle = math.radians(2)
        sun.rotation_euler = mathutils.Vector(VIEWS[nm]).to_track_quat('Z', 'Y').to_euler()   # 해가 카메라 쪽에서 비춤
        sc.collection.objects.link(sun)
        sc.render.bake.use_pass_direct, sc.render.bake.use_pass_indirect, sc.render.bake.use_pass_color = True, False, False
        bpy.ops.object.bake(type='DIFFUSE', pass_filter={'DIRECT'})
        bpy.data.objects.remove(sun)
        Mv = np.clip(pix(img2)[..., 0], 0, 1)
        wgt = (Mv ** 3) * PRIORITY[nm]
        acc += P * wgt[..., None]
        accw += wgt
        print(nm, "보이는 칸", int((Mv > 0.05).sum()))
    for md in list(ob.modifiers):
        ob.modifiers.remove(md)
    for nm in names:
        if "p_" + nm in ob.data.uv_layers:
            ob.data.uv_layers.remove(ob.data.uv_layers["p_" + nm])
    out = acc / np.maximum(accw, 1e-6)[..., None]
    hole = accw < 1e-3                                       # 어느 방향에서도 안 보인 곳: 주변 색으로 채움
    filled = out.copy()
    known = ~hole
    for _ in range(64):
        if known.all():
            break
        sh = [np.roll(filled * known[..., None], (dy, dx), (0, 1)) for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1))]
        kn = [np.roll(known, (dy, dx), (0, 1)) for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1))]
        ssum = sum(sh)
        ksum = sum(k_.astype(np.float32) for k_ in kn)
        newk = (~known) & (ksum > 0)
        filled[newk] = ssum[newk] / ksum[newk][..., None]
        known = known | newk
    tex_img = bpy.data.images.new("텍스처", size, size, float_buffer=True)
    rgba = np.concatenate([filled, np.ones((size, size, 1), np.float32)], -1)
    tex_img.pixels.foreach_set(rgba.ravel())
    tpath = os.path.join(folder, "텍스처.png")
    tex_img.filepath_raw = tpath
    tex_img.file_format = 'PNG'
    tex_img.save()
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
    w.node_tree.nodes["Background"].inputs[1].default_value = 0.7
    for nm_, loc, en in (("key", (-1.5, -2.5, 1.5), 120), ("fill", (1.8, -1.5, 0.8), 50), ("back", (0.5, 2.5, 1.5), 60)):
        L = bpy.data.objects.new(nm_, bpy.data.lights.new(nm_, "AREA"))
        L.data.energy = en
        L.data.size = 2
        L.location = center + mathutils.Vector(loc)
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
