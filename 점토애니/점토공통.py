# -*- coding: utf-8 -*-
"""점토 인형 공통 부품 (Blender 안에서 import) — 점토 재질, 덩어리 붙이기, 조명, 4방향 촬영.

점토 느낌 3가지:
  1) 모양을 조금 울퉁불퉁하게 (Displace + 흐린 구름 무늬) — 손으로 빚은 듯
  2) 표면에 손자국·지문 결 (보로노이·노이즈·물결 무늬 범프)
  3) 무광 + 빛이 살짝 스며듦 (거칠기 0.6, 서브서피스 조금)
"""
import bpy, math, os
from mathutils import Vector

ROOT = None
_tex_cache = {}


def new_scene():
    global ROOT
    bpy.ops.wm.read_factory_settings(use_empty=True)
    ROOT = bpy.data.objects.new("인형", None)
    bpy.context.scene.collection.objects.link(ROOT)
    _tex_cache.clear()
    return ROOT


def clay_mat(name, rgb, rough=0.62, sss=0.04, stripe=None):
    """점토 재질. stripe=(축 'X'/'Y'/'Z', 촘촘함, 줄 색, 굵기 0~1) 이면 줄무늬(호랑이)."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    N, L = m.node_tree.nodes, m.node_tree.links
    bsdf = N["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*rgb, 1)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Subsurface Weight"].default_value = sss
    bsdf.inputs["Subsurface Radius"].default_value = (0.3, 0.15, 0.1)
    bsdf.inputs["Subsurface Scale"].default_value = 0.02
    tc = N.new("ShaderNodeTexCoord")

    if stripe:
        axis, scale, scol, width = stripe
        wv = N.new("ShaderNodeTexWave")
        wv.wave_type = "BANDS"
        wv.bands_direction = axis
        wv.inputs["Scale"].default_value = scale
        wv.inputs["Distortion"].default_value = 4.0
        wv.inputs["Detail Scale"].default_value = 1.5
        L.new(tc.outputs["Object"], wv.inputs["Vector"])
        cr = N.new("ShaderNodeValToRGB")
        cr.color_ramp.interpolation = "CONSTANT"
        cr.color_ramp.elements[0].color = (*rgb, 1)
        cr.color_ramp.elements[1].position = 1.0 - width
        cr.color_ramp.elements[1].color = (*scol, 1)
        L.new(wv.outputs["Fac"], cr.inputs["Fac"])
        L.new(cr.outputs["Color"], bsdf.inputs["Base Color"])

    vor = N.new("ShaderNodeTexVoronoi")      # 손가락으로 누른 자국
    vor.inputs["Scale"].default_value = 9.0
    vor.feature = "SMOOTH_F1"
    noi = N.new("ShaderNodeTexNoise")        # 잔결
    noi.inputs["Scale"].default_value = 60.0
    noi.inputs["Detail"].default_value = 6.0
    wav = N.new("ShaderNodeTexWave")         # 지문 같은 줄
    wav.inputs["Scale"].default_value = 28.0
    wav.inputs["Distortion"].default_value = 9.0
    wav.inputs["Detail"].default_value = 3.0
    for t in (vor, noi, wav):
        L.new(tc.outputs["Object"], t.inputs["Vector"])
    prev = None
    for tex, out, st, dist in ((vor, "Distance", 0.4, 0.02), (noi, "Fac", 0.2, 0.005), (wav, "Fac", 0.1, 0.004)):
        b = N.new("ShaderNodeBump")
        b.inputs["Strength"].default_value = st
        b.inputs["Distance"].default_value = dist
        L.new(tex.outputs[out], b.inputs["Height"])
        if prev:
            L.new(prev.outputs["Normal"], b.inputs["Normal"])
        prev = b
    L.new(prev.outputs["Normal"], bsdf.inputs["Normal"])
    return m


def lumpy(obj, strength=0.035, size=0.35, subdiv=3):
    s = obj.modifiers.new("부드럽게", "SUBSURF")
    s.levels = s.render_levels = subdiv
    if size not in _tex_cache:
        t = bpy.data.textures.new(f"덩어리{size}", "CLOUDS")
        t.noise_scale = size
        _tex_cache[size] = t
    d = obj.modifiers.new("울퉁불퉁", "DISPLACE")
    d.texture = _tex_cache[size]
    d.texture_coords = "GLOBAL"
    d.strength = strength
    obj.modifiers.new("매끈", "SMOOTH").factor = 0.3


def part(kind, name, loc, scale, mat, rot=(0, 0, 0), lump=0.035, **kw):
    """덩어리 하나. kind: sphere / cyl / cone / torus. rot 는 도(°)."""
    bevel = kw.pop("bevel", 0.06)
    if kind == "sphere":
        bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, location=loc)
    elif kind == "cyl":
        kw.setdefault("depth", 2)
        bpy.ops.mesh.primitive_cylinder_add(vertices=32, location=loc, **kw)
    elif kind == "cone":
        bpy.ops.mesh.primitive_cone_add(vertices=32, location=loc, **kw)
    elif kind == "torus":
        bpy.ops.mesh.primitive_torus_add(location=loc, **kw)
    o = bpy.context.active_object
    o.name = name
    o.scale = scale
    o.rotation_euler = [math.radians(a) for a in rot]
    o.data.materials.append(mat)
    for p in o.data.polygons:
        p.use_smooth = True
    if kind in ("cyl", "cone"):
        bv = o.modifiers.new("둥근끝", "BEVEL")   # 점토는 모서리가 없음
        bv.width = bevel
        bv.segments = 4
    if lump:
        lumpy(o, strength=lump)
    o.parent = ROOT
    return o


def half_torus(name, loc, mat, major=0.08, minor=0.018, rot=(90, 0, 0), keep="lower"):
    """웃는 입 같은 반달 고리. keep='lower' 면 아래 절반(웃음), 'upper' 면 위 절반."""
    o = part("torus", name, loc, (1, 1, 1), mat, rot=rot, lump=0.0,
             major_radius=major, minor_radius=minor)
    bpy.context.view_layer.objects.active = o
    for e in o.data.edges:
        e.select = False
    for p in o.data.polygons:
        p.select = False
    for v in o.data.vertices:
        v.select = (v.co.y > 0) if keep == "lower" else (v.co.y < 0)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.delete(type="VERT")
    bpy.ops.object.mode_set(mode="OBJECT")
    return o


def bead_chain(name, pts, radius, mat, n=10):
    """점 여러 개를 잇는 곡선 위에 구슬을 놓음 (갓끈·꼬리 등)."""
    out = []
    P = [Vector(p) for p in pts]
    segs = [(P[i], P[i + 1]) for i in range(len(P) - 1)]
    lens = [(b - a).length for a, b in segs]
    total = sum(lens)
    for k in range(n):
        t = total * k / (n - 1)
        for (a, b), ln in zip(segs, lens):
            if t <= ln + 1e-6:
                p = a + (b - a) * (t / ln if ln else 0)
                break
            t -= ln
        out.append(part("sphere", f"{name}{k}", tuple(p), (radius,) * 3, mat, lump=0.0))
    return out


def _bounds():
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    lo = Vector((1e9,) * 3)
    hi = Vector((-1e9,) * 3)
    for o in ROOT.children:
        e = o.evaluated_get(dg)
        for c in e.bound_box:
            w = e.matrix_world @ Vector(c)
            lo = Vector(map(min, lo, w))
            hi = Vector(map(max, hi, w))
    return lo, hi


def studio_and_shoot(out_dir, samples=48, height_px=960, margin=1.15):
    """모형을 가운데로 옮기고, 조명·바닥 그림자·정사영 카메라를 놓고 앞·왼옆·오른옆·뒤 4장."""
    sc = bpy.context.scene
    os.makedirs(out_dir, exist_ok=True)
    lo, hi = _bounds()
    cx, cy = (lo.x + hi.x) / 2, (lo.y + hi.y) / 2
    for o in ROOT.children:            # 돌릴 때 제자리에서 돌도록 가운데로
        o.location.x -= cx
        o.location.y -= cy
    lo, hi = _bounds()
    span_h = max(hi.x - lo.x, hi.y - lo.y)   # 어느 방향에서 봐도 들어가게
    span_v = hi.z

    bpy.ops.mesh.primitive_plane_add(size=40, location=(0, 0, 0))
    bpy.context.active_object.is_shadow_catcher = True

    def area(name, loc, energy, size, rot):
        d = bpy.data.lights.new(name, "AREA")
        d.energy, d.size = energy, size
        o = bpy.data.objects.new(name, d)
        o.location = loc
        o.rotation_euler = [math.radians(a) for a in rot]
        sc.collection.objects.link(o)
    k = max(1.0, span_v / 2.6) ** 2        # 큰 모형은 빛도 조금 세게
    area("주광", (-2.5, -3.5, 4.5), 330 * k, 3.0, (45, 0, -35))
    area("보조광", (3.5, -2.5, 2.5), 110 * k, 4.0, (60, 0, 55))
    area("뒷광", (0, 4, 4), 200 * k, 3.0, (-45, 0, 0))
    w = bpy.data.worlds.new("세상")
    sc.world = w
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs["Color"].default_value = (1, 1, 1, 1)
    w.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.25

    cd = bpy.data.cameras.new("카메라")
    cd.type = "ORTHO"
    cam = bpy.data.objects.new("카메라", cd)
    sc.collection.objects.link(cam)
    sc.camera = cam
    width_px = int(min(1200, max(560, height_px * span_h / span_v * 1.05)))
    sc.render.resolution_x, sc.render.resolution_y = width_px, height_px
    # ortho_scale 은 그림의 긴 쪽 길이
    if width_px >= height_px:
        cd.ortho_scale = max(span_h * 1.08, span_v * margin * width_px / height_px)
    else:
        cd.ortho_scale = max(span_v * margin, span_h * 1.08 * height_px / width_px)
    cam.location = (0, -20, span_v / 2 + 0.02 * span_v)
    cam.rotation_euler = (math.radians(90), 0, 0)

    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = samples
    sc.cycles.use_denoising = False          # Ubuntu 판 Blender 엔 OIDN 이 없음
    sc.cycles.use_adaptive_sampling = True
    sc.cycles.adaptive_threshold = 0.02
    sc.cycles.max_bounces = 6
    sc.render.film_transparent = True
    sc.view_settings.view_transform = "Standard"

    for i, deg in enumerate((0, -90, 90, 180)):
        ROOT.rotation_euler = (0, 0, math.radians(deg))
        sc.render.filepath = os.path.join(out_dir, f"view_{i}.png")
        bpy.ops.render.render(write_still=True)
        print("찍음", sc.render.filepath, flush=True)
