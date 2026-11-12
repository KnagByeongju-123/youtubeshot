# -*- coding: utf-8 -*-
"""점토 인형 시험 — Blender 로 말랑한 점토(클레이) 인형 하나를 만들고 앞·옆·옆·뒤 4장을 찍음.

쓰는 법 (화면 없이):
  blender -b -P 점토애니/점토인형_시험.py -- <결과폴더> [샘플수]
  → <결과폴더>/view_0..3.png (투명 배경) — 시트 합치기는 점토인형_시트.py

점토 느낌을 내는 3가지:
  1) 모양을 조금 울퉁불퉁하게 (Displace 모디파이어 + 흐린 구름 무늬) — 손으로 빚은 듯
  2) 표면에 손자국·지문 결 (노이즈·보로노이 무늬로 범프)
  3) 무광 + 빛이 살짝 스며듦 (거칠기 0.6, 서브서피스 조금)
"""
import bpy, sys, math, os

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = os.path.abspath(argv[0] if argv else "output/점토")
SAMPLES = int(argv[1]) if len(argv) > 1 else 48
os.makedirs(OUT, exist_ok=True)

# ---------- 빈 장면 ----------
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene

ROOT = bpy.data.objects.new("인형", None)
sc.collection.objects.link(ROOT)

_tex_cache = {}


def clay_mat(name, rgb, rough=0.62, sss=0.04):
    """점토 재질: 무광 + 지문 결(범프) + 살짝 스며드는 빛."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    N = nt.nodes
    L = nt.links
    bsdf = N["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*rgb, 1)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Subsurface Weight"].default_value = sss
    bsdf.inputs["Subsurface Radius"].default_value = (0.3, 0.15, 0.1)
    bsdf.inputs["Subsurface Scale"].default_value = 0.02

    tc = N.new("ShaderNodeTexCoord")
    # 큰 결: 손가락으로 누른 자국
    vor = N.new("ShaderNodeTexVoronoi")
    vor.inputs["Scale"].default_value = 9.0
    vor.feature = "SMOOTH_F1"
    # 잔결: 지문·표면 거칠음
    noi = N.new("ShaderNodeTexNoise")
    noi.inputs["Scale"].default_value = 60.0
    noi.inputs["Detail"].default_value = 6.0
    # 줄무늬 지문 (wave 를 노이즈로 흔듦)
    wav = N.new("ShaderNodeTexWave")
    wav.inputs["Scale"].default_value = 28.0
    wav.inputs["Distortion"].default_value = 9.0
    wav.inputs["Detail"].default_value = 3.0
    for t in (vor, noi, wav):
        L.new(tc.outputs["Object"], t.inputs["Vector"])

    b1 = N.new("ShaderNodeBump"); b1.inputs["Strength"].default_value = 0.4; b1.inputs["Distance"].default_value = 0.02
    b2 = N.new("ShaderNodeBump"); b2.inputs["Strength"].default_value = 0.2; b2.inputs["Distance"].default_value = 0.005
    b3 = N.new("ShaderNodeBump"); b3.inputs["Strength"].default_value = 0.1; b3.inputs["Distance"].default_value = 0.004
    L.new(vor.outputs["Distance"], b1.inputs["Height"])
    L.new(noi.outputs["Fac"], b2.inputs["Height"])
    L.new(wav.outputs["Fac"], b3.inputs["Height"])
    L.new(b1.outputs["Normal"], b2.inputs["Normal"])
    L.new(b2.outputs["Normal"], b3.inputs["Normal"])
    L.new(b3.outputs["Normal"], bsdf.inputs["Normal"])
    return m


def lumpy(obj, strength=0.035, size=0.35, subdiv=3):
    """손으로 빚은 듯 모양을 살짝 울퉁불퉁하게."""
    s = obj.modifiers.new("부드럽게", "SUBSURF")
    s.levels = s.render_levels = subdiv
    key = (size,)
    if key not in _tex_cache:
        t = bpy.data.textures.new(f"덩어리{size}", "CLOUDS")
        t.noise_scale = size
        t.noise_depth = 1
        _tex_cache[key] = t
    d = obj.modifiers.new("울퉁불퉁", "DISPLACE")
    d.texture = _tex_cache[key]
    d.texture_coords = "GLOBAL"
    d.strength = strength
    d.mid_level = 0.5
    obj.modifiers.new("매끈", "SMOOTH").factor = 0.3


def shade(obj):
    for p in obj.data.polygons:
        p.use_smooth = True


def part(kind, name, loc, scale, mat, rot=(0, 0, 0), lump=0.035, **kw):
    if kind == "sphere":
        bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, location=loc)
    elif kind == "cyl":
        bpy.ops.mesh.primitive_cylinder_add(vertices=24, location=loc, **kw)
    elif kind == "cone":
        bpy.ops.mesh.primitive_cone_add(vertices=24, location=loc, **kw)
    elif kind == "torus":
        bpy.ops.mesh.primitive_torus_add(location=loc, **kw)
    o = bpy.context.active_object
    o.name = name
    o.scale = scale
    o.rotation_euler = rot
    o.data.materials.append(mat)
    shade(o)
    if kind in ("cyl", "cone"):
        # 끝을 둥글게 (점토는 모서리가 없음)
        bv = o.modifiers.new("둥근끝", "BEVEL")
        bv.width = 0.06
        bv.segments = 4
        bv.affect = "EDGES"
    if lump:
        lumpy(o, strength=lump)
    o.parent = ROOT
    return o


# ---------- 색 ----------
SKIN = clay_mat("살색", (0.88, 0.58, 0.42), sss=0.08)
HAIR = clay_mat("머리", (0.30, 0.16, 0.08))
SHIRT = clay_mat("노란티", (0.95, 0.72, 0.12))
PANTS = clay_mat("파란바지", (0.16, 0.36, 0.72))
SHOE = clay_mat("빨간신", (0.80, 0.14, 0.12))
SOLE = clay_mat("밑창", (0.92, 0.90, 0.85))
EYE = clay_mat("눈", (0.03, 0.03, 0.03), rough=0.15, sss=0.0)
WHITE = clay_mat("눈빛", (1, 1, 1), rough=0.2, sss=0.0)
CHEEK = clay_mat("볼", (0.95, 0.42, 0.42))
MOUTH = clay_mat("입", (0.45, 0.10, 0.10))

# ---------- 몸 (키 약 2.6, 머리가 큰 귀여운 비율) ----------
# 다리
for sx in (-1, 1):
    part("cyl", f"다리{sx}", (0.17 * sx, 0, 0.42), (0.11, 0.11, 0.24), SKIN, lump=0.02, depth=2)
    part("sphere", f"신발{sx}", (0.18 * sx, -0.06, 0.12), (0.15, 0.22, 0.11), SHOE, lump=0.02)
    part("cyl", f"밑창{sx}", (0.18 * sx, -0.06, 0.035), (0.15, 0.22, 0.03), SOLE, lump=0.0, depth=2)
# 반바지
part("cyl", "반바지", (0, 0, 0.78), (0.36, 0.27, 0.16), PANTS, lump=0.03, depth=2)
for sx in (-1, 1):
    part("cyl", f"바짓단{sx}", (0.17 * sx, 0, 0.62), (0.15, 0.15, 0.08), PANTS, lump=0.02, depth=2)
# 몸통(티셔츠) — 아래가 넓은 둥근 통
part("cone", "몸통", (0, 0, 1.13), (1, 0.78, 1), SHIRT, lump=0.035,
     radius1=0.40, radius2=0.28, depth=0.62)
# 팔: 소매 + 팔 + 벙어리장갑 같은 손
for sx in (-1, 1):
    part("sphere", f"소매{sx}", (0.37 * sx, 0, 1.30), (0.15, 0.14, 0.14), SHIRT, lump=0.02)
    part("cyl", f"팔{sx}", (0.45 * sx, 0, 1.08), (0.075, 0.075, 0.2), SKIN,
         rot=(0, math.radians(-14 * sx), 0), lump=0.015, depth=2)
    part("sphere", f"손{sx}", (0.50 * sx, 0, 0.86), (0.10, 0.09, 0.11), SKIN, lump=0.015)
# 목
part("cyl", "목", (0, 0, 1.47), (0.12, 0.12, 0.06), SKIN, lump=0.0, depth=2)
# 머리 (크고 살짝 납작한 공)
HZ = 1.95
part("sphere", "머리", (0, 0, HZ), (0.50, 0.46, 0.47), SKIN, lump=0.03)
# 귀
for sx in (-1, 1):
    part("sphere", f"귀{sx}", (0.49 * sx, 0.02, HZ - 0.02), (0.06, 0.08, 0.10), SKIN, lump=0.0)
# 머리카락: 뒤통수를 덮는 덩어리 + 앞머리 뭉치 3개
# 한 덩어리를 뒤로 기울여 앞은 이마 위, 뒤는 목덜미까지 덮음 (두 덩어리면 이음새가 보임)
part("sphere", "머리카락", (0, 0.07, HZ + 0.02), (0.535, 0.50, 0.50), HAIR,
     rot=(math.radians(-28), 0, 0), lump=0.04)
for i, (x, rz) in enumerate(((-0.22, 20), (0.0, 0), (0.22, -20))):
    part("sphere", f"앞머리{i}", (x, -0.36, HZ + 0.28), (0.17, 0.11, 0.10), HAIR,
         rot=(math.radians(25), 0, math.radians(rz)), lump=0.02)
# 머리 꼭대기 삐친 머리
part("cone", "삐침", (0.04, 0.05, HZ + 0.53), (1, 1, 1), HAIR, rot=(math.radians(-20), math.radians(15), 0),
     lump=0.0, radius1=0.07, radius2=0.0, depth=0.22)
# 얼굴: 동그란 검은 눈 + 하이라이트, 볼, 웃는 입
FY = -0.44
for sx in (-1, 1):
    part("sphere", f"눈{sx}", (0.16 * sx, FY + 0.02, HZ + 0.03), (0.055, 0.03, 0.07), EYE, lump=0.0)
    part("sphere", f"눈빛{sx}", (0.16 * sx + 0.018, FY - 0.008, HZ + 0.06), (0.015, 0.01, 0.018), WHITE, lump=0.0)
    part("sphere", f"볼{sx}", (0.27 * sx, FY + 0.07, HZ - 0.10), (0.075, 0.03, 0.05), CHEEK, lump=0.0)
mouth = part("torus", "입", (0, FY + 0.03, HZ - 0.13), (1, 1, 1), MOUTH, rot=(math.radians(90), 0, 0),
             lump=0.0, major_radius=0.08, minor_radius=0.018)
# 입: 아래 절반만 남겨 웃는 모양
bpy.context.view_layer.objects.active = mouth
bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.select_all(action="DESELECT")
bpy.ops.object.mode_set(mode="OBJECT")
for v in mouth.data.vertices:
    v.select = v.co.y > 0.0  # 회전 후 위쪽 절반(원래 y>0)을 지워 웃는 입
bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.delete(type="VERT")
bpy.ops.object.mode_set(mode="OBJECT")
# 코 (작은 동그라미)
part("sphere", "코", (0, FY - 0.01, HZ - 0.04), (0.04, 0.03, 0.035), SKIN, lump=0.0)

# ---------- 바닥(그림자만 받음) ----------
bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 0, 0))
floor = bpy.context.active_object
floor.is_shadow_catcher = True

# ---------- 빛: 부드러운 스튜디오 ----------
def area(name, loc, energy, size, rot):
    d = bpy.data.lights.new(name, "AREA")
    d.energy = energy
    d.size = size
    o = bpy.data.objects.new(name, d)
    o.location = loc
    o.rotation_euler = rot
    sc.collection.objects.link(o)

area("주광", (-2.5, -3.5, 4.5), 330, 3.0, (math.radians(45), 0, math.radians(-35)))
area("보조광", (3.5, -2.5, 2.5), 110, 4.0, (math.radians(60), 0, math.radians(55)))
area("뒷광", (0, 4, 4), 200, 3.0, (math.radians(-45), 0, 0))
w = bpy.data.worlds.new("세상")
sc.world = w
w.use_nodes = True
w.node_tree.nodes["Background"].inputs["Color"].default_value = (1, 1, 1, 1)
w.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.25

# ---------- 카메라 ----------
cd = bpy.data.cameras.new("카메라")
cd.lens = 85
cam = bpy.data.objects.new("카메라", cd)
sc.collection.objects.link(cam)
sc.camera = cam
DIST = 8.3
cam.location = (0, -DIST, 1.35)
cam.rotation_euler = (math.radians(90), 0, 0)

# ---------- 렌더 설정 ----------
sc.render.engine = "CYCLES"
sc.cycles.device = "CPU"
sc.cycles.samples = SAMPLES
# Ubuntu 판 Blender 는 노이즈 제거(OIDN)가 빠져 있음 → 끄고 샘플 수로 깨끗하게
sc.cycles.use_denoising = False
sc.cycles.use_adaptive_sampling = True
sc.cycles.adaptive_threshold = 0.02
sc.cycles.max_bounces = 6
sc.render.film_transparent = True
sc.render.resolution_x = 640
sc.render.resolution_y = 960
sc.view_settings.view_transform = "Standard"  # AgX 는 색이 바램
sc.view_settings.look = "None"

# 앞, 왼쪽 옆, 오른쪽 옆, 뒤 — 인형을 돌려서 찍음
for i, deg in enumerate((0, -90, 90, 180)):
    ROOT.rotation_euler = (0, 0, math.radians(deg))
    sc.render.filepath = os.path.join(OUT, f"view_{i}.png")
    bpy.ops.render.render(write_still=True)
    print("찍음", sc.render.filepath, flush=True)
