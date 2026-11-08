r"""Blender 안에서 실행되는 장면 만들기 (블렌더_효과.py 가 부름 — 직접 부르지 않음)
blender -b --factory-startup -P 블렌더_장면.py -- <설정.json>

설정.json:
  kind   : "입체사진"(사진 + 깊이 지도 → 앞뒤가 다르게 움직임) | "로우폴리"(손으로 만든 각진 3D 장면)
  scene  : 로우폴리 장면 이름 (거리_물감놀이 · 모닥불_밤 · 크리슈나_라다 · 꽃_물감)
  move   : "시간정지"(모두 공중에서 멈춤, 카메라가 3~4곳으로 순간이동하며 천천히 흐름) | "FPV"(드론이 빠르게 앞으로, 좌우로 기울고 흔들림) | "천천히"
  sec, fps, w, h, samples, out(프레임 폴더), seed
  photo, depth(npy) : 입체사진일 때
"""
import json
import math
import os
import random
import sys

import bpy
from mathutils import Vector

ARGS = json.load(open(sys.argv[sys.argv.index("--") + 1], encoding="utf-8"))
RNG = random.Random(int(ARGS.get("seed", 7)))
SC = bpy.context.scene
FPS = int(ARGS.get("fps", 24))
NF = max(2, int(round(float(ARGS.get("sec", 8)) * FPS)))


# ───────── 공통 ─────────
def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    global SC
    SC = bpy.context.scene
    SC.render.engine = "CYCLES"
    SC.cycles.device = "CPU"
    SC.cycles.samples = int(ARGS.get("samples", 12))
    SC.cycles.use_denoising = True
    SC.cycles.max_bounces = 3
    SC.cycles.diffuse_bounces = 2
    SC.cycles.glossy_bounces = 1
    SC.cycles.transparent_max_bounces = 8
    SC.render.resolution_x = int(ARGS.get("w", 960))
    SC.render.resolution_y = int(ARGS.get("h", 540))
    SC.render.resolution_percentage = 100
    SC.render.fps = FPS
    SC.frame_start, SC.frame_end = 1, NF
    SC.render.image_settings.file_format = "JPEG"
    SC.render.image_settings.quality = 92
    SC.view_settings.view_transform = "AgX"
    SC.view_settings.look = "AgX - Medium High Contrast"
    SC.render.threads_mode = "AUTO"


def mat(name, color, rough=0.8, emit=0.0, alpha=1.0, emit_color=None):
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    if emit:
        b.inputs["Emission Color"].default_value = (*(emit_color or color), 1)
        b.inputs["Emission Strength"].default_value = emit
    if alpha < 1:
        b.inputs["Alpha"].default_value = alpha
        m.blend_method = "BLEND"
    return m


def srgb(h):
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)


def flat(o):
    for p in o.data.polygons:
        p.use_smooth = False


def add(kind, loc=(0, 0, 0), scale=(1, 1, 1), rot=(0, 0, 0), m=None, **kw):
    f = {"cube": bpy.ops.mesh.primitive_cube_add, "cyl": bpy.ops.mesh.primitive_cylinder_add,
         "cone": bpy.ops.mesh.primitive_cone_add, "ico": bpy.ops.mesh.primitive_ico_sphere_add,
         "plane": bpy.ops.mesh.primitive_plane_add}[kind]
    f(location=loc, rotation=rot, **kw)
    o = bpy.context.active_object
    o.scale = scale
    if m is not None:
        o.data.materials.append(m)
    flat(o)
    return o


def limb(a, b, r, m, verts=6):
    """a→b 사이 각진 원기둥 (팔·다리)"""
    a, b = Vector(a), Vector(b)
    d = b - a
    o = add("cyl", loc=(a + b) / 2, m=m, vertices=verts, radius=r, depth=d.length)
    o.rotation_mode = "QUATERNION"
    o.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(d.normalized())
    return o


CAM_KEEP = []          # 카메라가 설 자리 (그 근처 1m 안에는 사람·물건을 두지 않음 → 카메라가 몸 속에 들어가지 않게)


def free(x, y, r=1.1):
    return all((x - c[0]) ** 2 + (y - c[1]) ** 2 > r * r for c in CAM_KEEP)


PALETTE = ["#ff2d6f", "#ffd21f", "#21c45d", "#2f8cff", "#a845ff", "#ff7a1a", "#ff4fd8", "#19d3c5"]
SKIN = ["#8d5a3b", "#a86b45", "#7a4a2e", "#b97c52", "#6b3f26"]


def person(x, y, face=0.0, h=1.0, skin=None, cloth="#f4f1ea", pants="#e9e4d8", hair="#1d1410",
           pose="서기", splat=True, woman=False, crown=False):
    """각진 로우폴리 사람 (팔 2·다리 2). face: 바라보는 방향(도). pose: 서기 · 던지기 · 두팔 · 칠하기"""
    skin = skin or RNG.choice(SKIN)
    ms, mc, mp, mh = mat("skin" + skin, srgb(skin), 0.6), mat("cl" + cloth, srgb(cloth), 0.9), mat("pa" + pants, srgb(pants), 0.9), mat("hair" + hair, srgb(hair), 0.7)
    parts = []
    s = h
    hip = 0.92 * s
    # 다리 2
    for sx in (-0.11, 0.11):
        parts.append(limb((sx * s, 0, 0.06 * s), (sx * 0.8 * s, 0, hip), 0.075 * s, mp))
        parts.append(add("cube", loc=(sx * s, 0.05 * s, 0.035 * s), scale=(0.06 * s, 0.12 * s, 0.035 * s), m=mat("shoe", srgb("#3a2a20"))))
    # 몸통 (쿠르타·사리: 아래로 넓게)
    tor = add("cyl", loc=(0, 0, hip + 0.18 * s if not woman else hip + 0.05 * s), m=mc, vertices=7,
              radius=0.21 * s, depth=(0.72 if not woman else 0.98) * s)
    tor.scale = (1.0, 0.68, 1)
    for v in tor.data.vertices:                       # 위는 좁게(어깨), 아래는 넓게(옷자락)
        k = 0.78 if v.co.z > 0 else 1.18
        v.co.x *= k
        v.co.y *= k
    parts.append(tor)
    sh_z = hip + 0.52 * s
    # 머리·목·머리카락
    parts.append(add("cyl", loc=(0, 0, sh_z + 0.05 * s), m=ms, vertices=6, radius=0.05 * s, depth=0.12 * s))
    head = add("ico", loc=(0, 0.01 * s, sh_z + 0.2 * s), m=ms, subdivisions=1, radius=0.12 * s)
    head.scale = (0.92, 1.0, 1.12)
    parts.append(head)
    hr = add("ico", loc=(0, -0.025 * s, sh_z + 0.25 * s), m=mh, subdivisions=1, radius=0.125 * s)
    hr.scale = (0.98, 0.98, 0.8 if not woman else 1.05)
    parts.append(hr)
    if woman:   # 땋은 머리
        parts.append(limb((0, -0.11 * s, sh_z + 0.2 * s), (0, -0.16 * s, sh_z - 0.18 * s), 0.04 * s, mh, 5))
    if crown:   # 공작 깃털 왕관 (크리슈나)
        parts.append(add("cone", loc=(0, -0.01 * s, sh_z + 0.37 * s), m=mat("gold", srgb("#e8b021"), 0.3), vertices=6, radius1=0.09 * s, radius2=0.05 * s, depth=0.1 * s))
        f = add("ico", loc=(0, -0.03 * s, sh_z + 0.48 * s), m=mat("peacock", srgb("#127a6a"), 0.4), subdivisions=1, radius=0.05 * s)
        f.scale = (0.6, 0.3, 1.6)
        parts.append(f)
    # 팔 2 (어깨 → 팔꿈치 → 손)
    poses = {"서기": [((-0.05, 0, -0.27), (-0.02, 0.03, -0.53)), ((0.05, 0, -0.27), (0.02, 0.03, -0.53))],
             "던지기": [((-0.12, 0.05, -0.2), (-0.1, 0.25, -0.35)), ((0.15, 0.1, 0.2), (0.12, 0.35, 0.42))],
             "두팔": [((-0.16, 0.05, 0.2), (-0.26, 0.1, 0.45)), ((0.16, 0.05, 0.2), (0.26, 0.1, 0.45))],
             "칠하기": [((-0.06, 0.08, -0.25), (-0.02, 0.15, -0.45)), ((0.08, 0.22, -0.05), (0.04, 0.42, 0.08))]}[pose]
    hands = []
    for (sx, (el, hd)) in zip((-0.24, 0.24), poses):
        shp = Vector((sx * s, 0, sh_z - 0.02 * s))
        elb = shp + Vector(el) * s
        hnd = shp + Vector(hd) * s
        parts.append(limb(shp, elb, 0.055 * s, mc))
        parts.append(limb(elb, hnd, 0.045 * s, ms))
        parts.append(add("ico", loc=hnd, m=ms, subdivisions=1, radius=0.045 * s))
        hands.append(hnd)
    if splat:   # 옷에 묻은 물감 얼룩
        for _ in range(RNG.randint(3, 7)):
            c = RNG.choice(PALETTE)
            a = RNG.uniform(0, 2 * math.pi)
            z = RNG.uniform(hip - 0.25 * s, sh_z)
            o = add("ico", loc=(math.cos(a) * 0.17 * s, math.sin(a) * 0.12 * s, z), m=mat("pw" + c, srgb(c), 0.95),
                    subdivisions=1, radius=RNG.uniform(0.05, 0.09) * s)
            o.scale = (1, 1, 0.5)
            parts.append(o)
    bpy.ops.object.select_all(action="DESELECT")
    for p in parts:
        p.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.join()
    o = bpy.context.active_object
    SC.cursor.location = (0, 0, 0)
    bpy.ops.object.origin_set(type="ORIGIN_CURSOR")      # 발밑을 기준점으로 (돌리고 옮겨도 제자리)
    o.rotation_mode = "XYZ"
    o.rotation_euler = (0, 0, math.radians(face))
    o.location = (x, y, 0)
    rot = o.rotation_euler.to_matrix()
    return o, [Vector((x, y, 0)) + rot @ hnd for hnd in hands], Vector((x, y, sh_z + 0.2 * s))


def powder_burst(origin, direction, color, n=26, spread=0.9, size=0.16, dist=2.2):
    """공중에 멈춘 물감 가루 구름 (작은 덩어리들 + 큰 반투명 구름)"""
    d = Vector(direction).normalized()
    m = mat("dust" + color, srgb(color), 1.0, emit=0.35, alpha=0.62)
    for i in range(n):
        t = (i / n) ** 0.7
        p = Vector(origin) + d * dist * t + Vector((RNG.gauss(0, 1), RNG.gauss(0, 1), RNG.gauss(0, 1))) * spread * t * 0.6
        p.z += 0.4 * math.sin(math.pi * t)
        r = size * (0.5 + 1.8 * t) * RNG.uniform(0.6, 1.3)
        o = add("ico", loc=p, m=m, subdivisions=2 if r > 0.25 else 1, radius=r)
        o.scale = (RNG.uniform(0.7, 1.3), RNG.uniform(0.7, 1.3), RNG.uniform(0.6, 1.0))
    for _ in range(int(n * 1.5)):       # 흩날리는 작은 알갱이
        p = Vector(origin) + d * dist * RNG.uniform(0.1, 1.2) + Vector((RNG.gauss(0, 1), RNG.gauss(0, 1), RNG.gauss(0, 0.7))) * spread
        add("ico", loc=p, m=m, subdivisions=1, radius=RNG.uniform(0.015, 0.04))


def drops(origin, direction, color="#9fd8ff", n=30):
    """공중에 멈춘 물방울 (물총·물풍선)"""
    m = mat("water", srgb(color), 0.05, alpha=0.6)
    d = Vector(direction).normalized()
    for i in range(n):
        t = RNG.uniform(0, 1)
        p = Vector(origin) + d * 3.0 * t + Vector((RNG.gauss(0, .15), RNG.gauss(0, .15), RNG.gauss(0, .15) - 0.6 * t * t))
        o = add("ico", loc=p, m=m, subdivisions=1, radius=RNG.uniform(0.02, 0.06))
        o.scale = (1, 1, 1.4)


def house(x, y, w, d, h, color, face=0):
    m = mat("wall" + color, srgb(color), 0.95)
    o = add("cube", loc=(x, y, h / 2), scale=(w / 2, d / 2, h / 2), m=m, rot=(0, 0, math.radians(face)))
    add("cube", loc=(x, y, h + 0.08), scale=(w / 2 + 0.12, d / 2 + 0.12, 0.08), m=mat("roof", srgb("#d9c7a8")), rot=(0, 0, math.radians(face)))
    dm = mat("door", srgb("#5b3a24"))
    wm = mat("win", srgb("#2b2b33"), 0.4)
    sgn = 1 if y < 0 else -1
    yf = y + sgn * d / 2 + sgn * 0.01
    for k in range(int(w // 1.6)):
        xx = x - w / 2 + 0.8 + k * 1.6
        add("cube", loc=(xx, yf, 1.0 if k % 2 == 0 else 2.2 if h > 3 else 1.6), scale=(0.3, 0.03, 0.4 if k % 2 else 0.9), m=dm if k % 2 == 0 else wm)
        if h > 3.5:
            add("cube", loc=(xx, yf, h - 1.2), scale=(0.32, 0.03, 0.42), m=wm)
    return o


def tree(x, y, s=1.0, flower=None):
    add("cyl", loc=(x, y, 0.9 * s), m=mat("bark", srgb("#5a3d27")), vertices=6, radius=0.12 * s, depth=1.8 * s)
    c = flower or "#2f7d3a"
    for _ in range(3):
        add("ico", loc=(x + RNG.uniform(-.5, .5) * s, y + RNG.uniform(-.5, .5) * s, (2.0 + RNG.uniform(0, .6)) * s),
            m=mat("leaf" + c, srgb(c), 0.9), subdivisions=1, radius=RNG.uniform(0.6, 0.85) * s)


def bunting(a, b, n=14):
    a, b = Vector(a), Vector(b)
    for i in range(n):
        t = (i + 0.5) / n
        p = a.lerp(b, t)
        p.z -= 0.6 * math.sin(math.pi * t)
        c = PALETTE[i % len(PALETTE)]
        o = add("cone", loc=p + Vector((0, 0, -0.15)), m=mat("flag" + c, srgb(c), 0.8), vertices=3, radius1=0.16, depth=0.3, rot=(math.pi, 0, 0))
        o.scale = (1, 0.15, 1)


def ground(color="#c9a77c", size=60):
    add("plane", loc=(0, 0, 0), scale=(size, size, 1), m=mat("ground" + color, srgb(color), 1.0))


def world(top="#8fc6ff", bot="#ffe7c2", strength=1.0):
    w = bpy.data.worlds.new("w")
    SC.world = w
    w.use_nodes = True
    nt = w.node_tree
    bg = nt.nodes["Background"]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (*srgb(bot), 1)
    ramp.color_ramp.elements[1].color = (*srgb(top), 1)
    ramp.color_ramp.elements[0].position = 0.45
    ramp.color_ramp.elements[1].position = 0.75
    mp = nt.nodes.new("ShaderNodeMapRange")
    mp.inputs["From Min"].default_value = -1
    nt.links.new(tc.outputs["Generated"], sep.inputs[0])
    nt.links.new(tc.outputs["Window"], sep.inputs[0])
    nt.links.new(sep.outputs["Y"], ramp.inputs[0])
    nt.links.new(ramp.outputs[0], bg.inputs["Color"])
    bg.inputs["Strength"].default_value = strength


def sun(rot=(50, 0, 30), energy=3.5, color="#fff1d6"):
    bpy.ops.object.light_add(type="SUN", rotation=tuple(math.radians(a) for a in rot))
    l = bpy.context.active_object
    l.data.energy = energy
    l.data.color = srgb(color)
    l.data.angle = math.radians(3)
    return l


def point(loc, energy, color, r=0.3):
    bpy.ops.object.light_add(type="POINT", location=loc)
    l = bpy.context.active_object
    l.data.energy = energy
    l.data.color = srgb(color)
    l.data.shadow_soft_size = r
    return l


# ───────── 장면들 ─────────
def scene_street():
    """좁은 골목에서 사람들이 서로 물감 가루를 던지는 순간 (낮)"""
    world("#9ccfff", "#ffe2b8", 0.9)
    sun((52, 0, 35), 3.8)
    ground("#c7a47a")
    cols = ["#f2c14e", "#e86f5a", "#6fb3d9", "#f29bbb", "#9bd17a", "#f5e6c8", "#d98e4a"]
    x = -16
    while x < 40:
        w = RNG.uniform(3, 5.5)
        house(x + w / 2, -4.6, w, 3, RNG.uniform(3, 6.5), RNG.choice(cols))
        house(x + w / 2 + 1, 4.6, w, 3, RNG.uniform(3, 6.5), RNG.choice(cols))
        x += w + 0.1
    for k in range(-2, 8):
        bunting((k * 5, -3.1, 4.2), (k * 5 + 4, 3.1, 4.4))
    shots = [((-3.5, 0.3, 3.0), (12, 0, 1.0)), ((8.2, -1.9, 1.0), (11.5, 0.4, 1.7)),
             ((12.5, 2.5, 1.5), (12, -1.2, 1.5)), ((15.5, 0.0, 5.6), (10.5, 0, 0.8))]
    CAM_KEEP[:] = [p for p, _ in shots] + [(x_, 0) for x_ in range(-10, 37, 2)]   # FPV 길 위(높이 2.6m)는 머리 위라 괜찮지만 넉넉히
    hands_all = []
    for i in range(60):
        px, py = RNG.uniform(-2, 30), RNG.uniform(-2.5, 2.5)
        if not free(px, py, 1.5):
            continue
        if len(hands_all) > 26:
            break
        pose = RNG.choice(["던지기", "던지기", "두팔", "서기", "칠하기"])
        o, hands, head = person(px, py, face=RNG.uniform(0, 360), h=RNG.uniform(0.85, 1.05), pose=pose,
                                cloth=RNG.choice(["#f4f1ea", "#f4f1ea", "#fff6e0", "#ffe08a", "#f7c6d9"]),
                                woman=RNG.random() < 0.4)
        if pose in ("던지기", "두팔"):
            hands_all.append((hands[1], head))
    for hnd, head in hands_all:
        dirv = Vector((RNG.uniform(-1, 1), RNG.uniform(-1, 1), RNG.uniform(0.2, 0.9)))
        powder_burst(hnd, dirv, RNG.choice(PALETTE), n=RNG.randint(14, 24), dist=RNG.uniform(1.4, 2.6))
    for _ in range(4):
        drops((RNG.uniform(0, 20), RNG.uniform(-2, 2), 1.4), (RNG.uniform(-1, 1), RNG.uniform(-1, 1), 0.5))
    for _ in range(6):                 # 하늘 높이 떠 있는 큰 색 구름
        powder_burst((RNG.uniform(5, 28), RNG.uniform(-2, 2), 3.4), (RNG.uniform(-1, 1), 0, 0.3), RNG.choice(PALETTE), n=18, spread=1.4, size=0.35, dist=2)
    return {"path": [(-10, 0, 2.6), (34, 0, 2.9)], "look": Vector((12, 0, 1.4)), "shots": shots}


def scene_bonfire():
    """홀리 전날 밤 모닥불(홀리카 다한) 둘레에 모인 사람들"""
    world("#0b1030", "#2a1a3a", 0.35)
    ground("#3a2c22")
    lm = mat("log", srgb("#4a2f1c"))
    for i in range(14):
        a = i / 14 * 2 * math.pi
        o = limb((math.cos(a) * 1.3, math.sin(a) * 1.3, 0.1), (math.cos(a) * 0.15, math.sin(a) * 0.15, 2.4), 0.11, lm)
    for k in range(9):
        r = 0.9 - k * 0.08
        add("cone", loc=(RNG.uniform(-.25, .25), RNG.uniform(-.25, .25), 0.8 + k * 0.32),
            m=mat("fire%d" % (k % 3), srgb(["#ff5a1a", "#ffa21f", "#ffe066"][k % 3]), 1, emit=18 - k, alpha=0.9),
            vertices=5, radius1=r, depth=1.4, rot=(0, 0, RNG.uniform(0, 6)))
    point((0, 0, 2.2), 2500, "#ff8a33", 1.0)
    point((0, 0, 0.8), 900, "#ffb05a", 0.6)
    for i in range(18):          # 불티 (공중에 멈춘)
        add("ico", loc=(RNG.gauss(0, .8), RNG.gauss(0, .8), RNG.uniform(3, 6.5)), m=mat("spark", srgb("#ffcf6a"), 1, emit=40), subdivisions=1, radius=0.03)
    shots = [((0, -8.5, 2.2), (0, 0, 2.0)), ((3.4, -3.3, 1.3), (-1.0, 1.0, 1.7)), ((-5.5, 3.6, 1.7), (0, 0, 1.6)), ((0.5, -4.0, 7.0), (0, 0, 0.8))]
    CAM_KEEP[:] = [p for p, _ in shots]
    for i in range(40):
        a = RNG.uniform(0, 2 * math.pi)
        r = RNG.uniform(3.6, 6.5)
        if not free(math.cos(a) * r, math.sin(a) * r):
            continue
        person(math.cos(a) * r, math.sin(a) * r, face=math.degrees(a) + 90, h=RNG.uniform(0.8, 1.02),
               pose=RNG.choice(["서기", "서기", "두팔"]), splat=False, cloth=RNG.choice(["#e9e2d0", "#c94a3a", "#e3a63b", "#3c6fb0"]), woman=RNG.random() < 0.45)
    for i in range(7):
        house(math.cos(i) * 14, math.sin(i) * 14, 4, 3, RNG.uniform(3, 5), "#6b5a4a", face=math.degrees(i))
    return {"path": [(-12, -2, 2.4), (-1.5, -1.0, 4.2)], "look": Vector((0, 0, 1.8)), "shots": shots}


def scene_krishna():
    """전해지는 이야기: 크리슈나(파란 피부)와 라다의 색칠 장난, 브린다반의 정원"""
    world("#a6d4ff", "#ffe9cf", 1.0)
    sun((55, 0, -40), 3.6, "#fff0d0")
    ground("#8fbf5a")
    k, kh, khead = person(-0.45, 0, face=-90, h=1.0, skin="#3f6fd1", cloth="#ffd21f", pants="#ffd21f", pose="칠하기", splat=False, crown=True)
    r, rh, rhead = person(0.45, 0, face=90, h=0.94, skin="#c48a5c", cloth="#ff4f8b", pants="#ff4f8b", pose="두팔", splat=False, woman=True)
    powder_burst(kh[1], (1, 0, 0.3), "#ff2d6f", n=14, dist=0.7, size=0.08, spread=0.3)
    powder_burst(rh[0], (-1, 0, 0.5), "#ffd21f", n=14, dist=0.9, size=0.09, spread=0.4)
    for i in range(10):
        tree(RNG.uniform(-12, 12), RNG.uniform(5, 14), RNG.uniform(0.9, 1.4), flower=RNG.choice(["#2f7d3a", "#ff6a2a", "#2f7d3a"]))
        tree(RNG.uniform(-12, 12), RNG.uniform(-14, -6), RNG.uniform(0.9, 1.4), flower=RNG.choice(["#2f7d3a", "#ff6a2a"]))
    for i in range(14):          # 낮은 꽃덤불
        c = RNG.choice(["#ff6a2a", "#ffd21f", "#ff4f8b"])
        o = add("ico", loc=(RNG.uniform(-5, 5), RNG.uniform(1.5, 5), 0.2), m=mat("bush" + c, srgb(c), 0.9), subdivisions=1, radius=0.35)
        o.scale = (1.3, 1, 0.6)
    shots = [((0, -3.0, 1.45), (0, 0, 1.3)), ((-1.0, -1.3, 1.55), (0.45, 0, 1.5)), ((1.1, -1.25, 1.5), (-0.45, 0, 1.55)), ((2.4, -2.4, 2.7), (0, 0, 1.0))]
    return {"path": [(-3, -4, 1.6), (3, -4, 1.6)], "look": Vector((0, 0, 1.3)), "shots": shots}


def scene_flowers():
    """팔라시(테수) 꽃을 끓여 만든 자연 물감 — 꽃 더미와 색 가루 그릇"""
    world("#ffd9a8", "#fff3e0", 1.0)
    sun((40, 0, 20), 3.2, "#ffe2b5")
    ground("#d8b98a")
    add("cyl", loc=(0, 0, 0.4), m=mat("table", srgb("#7a5233")), vertices=8, radius=2.2, depth=0.08)
    for i, c in enumerate(["#ff2d6f", "#ffd21f", "#21c45d", "#2f8cff", "#ff7a1a", "#a845ff"]):
        a = i / 6 * 2 * math.pi
        x, y = math.cos(a) * 1.3, math.sin(a) * 1.3
        add("cyl", loc=(x, y, 0.55), m=mat("bowl", srgb("#e9dcc6"), 0.6), vertices=8, radius=0.38, depth=0.22)
        o = add("ico", loc=(x, y, 0.66), m=mat("pw" + c, srgb(c), 1.0), subdivisions=2, radius=0.34)
        o.scale = (1, 1, 0.45)
    for _ in range(60):          # 주황 꽃잎 더미
        add("cone", loc=(RNG.gauss(0, .35), RNG.gauss(0, .35), 0.5 + RNG.uniform(0, .25)), m=mat("palash", srgb("#ff6a1a"), 0.7),
            vertices=4, radius1=0.08, depth=0.2, rot=(RNG.uniform(0, 3), RNG.uniform(0, 3), 0))
    for i in range(6):
        tree(math.cos(i) * 7, math.sin(i) * 7 + 3, 1.3, flower="#ff6a1a")
    powder_burst((0, 0, 0.8), (0.2, 0.1, 1), "#ff7a1a", n=16, dist=1.6, size=0.1, spread=0.5)
    shots = [((0, -3.0, 1.8), (0, 0, 0.6)), ((0.9, -1.2, 1.0), (0, 0.1, 0.7)), ((-2.2, 1.6, 1.5), (0, 0, 0.8)), ((0.2, -0.6, 3.6), (0, 0, 0.5))]
    return {"path": [(-3.5, -3.5, 2.2), (3.5, -3.5, 2.2)], "look": Vector((0, 0, 0.6)), "shots": shots}


SCENES = {"거리_물감놀이": scene_street, "모닥불_밤": scene_bonfire, "크리슈나_라다": scene_krishna, "꽃_물감": scene_flowers}


# ───────── 카메라 움직임 ─────────
def camera(lens=28):
    bpy.ops.object.camera_add()
    cam = bpy.context.active_object
    cam.data.lens = lens
    cam.data.clip_end = 400
    SC.camera = cam
    cam.rotation_mode = "XYZ"
    return cam


def look_rot(loc, target, roll=0.0):
    d = (Vector(target) - Vector(loc)).normalized()
    q = d.to_track_quat("-Z", "Y")
    e = q.to_euler()
    e.rotate_axis("Z", roll)
    return e


def key(cam, f, loc, rot, const=False):
    cam.location = loc
    cam.rotation_euler = rot
    cam.keyframe_insert("location", frame=f)
    cam.keyframe_insert("rotation_euler", frame=f)


def move_frozen(cam, info):
    """시간 정지 순간이동: 3~4곳을 번갈아 (컷은 순간, 머무는 동안 천천히 흐름)"""
    tgt = info["look"]
    n = int(ARGS.get("cuts", 4 if NF > 6 * FPS else 3))
    edges = [1 + round(i * (NF - 1) / n) for i in range(n + 1)]
    if info.get("shots"):
        n = min(n, len(info["shots"]))
        edges = [1 + round(i * (NF - 1) / n) for i in range(n + 1)]
        for i in range(n):
            p0, aim = Vector(info["shots"][i][0]), Vector(info["shots"][i][1])
            d = (aim - p0)
            side = Vector((-d.y, d.x, 0)).normalized() * (0.05 * d.length + 0.08)
            p1 = p0 + side * (1 if i % 2 else -1) + d.normalized() * 0.06 * d.length    # 머무는 동안 옆으로 천천히 + 살짝 다가감
            f0, f1 = edges[i], (edges[i + 1] - 1 if i < n - 1 else edges[i + 1])
            key(cam, f0, p0, look_rot(p0, aim))
            key(cam, f1, p1, look_rot(p1, aim + side * 0.4))
        return
    for i in range(n):
        a = RNG.uniform(0, 2 * math.pi) if i else -math.pi / 2 + RNG.uniform(-0.4, 0.4)
        r = [7.5, 3.2, 5.0, 2.4][i % 4] * float(ARGS.get("dist", 1.0))
        z = [1.6, 1.3, 3.2, 1.0][i % 4]
        p0 = tgt + Vector((math.cos(a) * r, math.sin(a) * r, z - tgt.z + RNG.uniform(-.2, .3)))
        side = Vector((-math.sin(a), math.cos(a), 0)) * (0.06 * r)
        p1 = p0 + side + (tgt - p0).normalized() * 0.08 * r
        aim = tgt + Vector((RNG.uniform(-.6, .6), RNG.uniform(-.6, .6), RNG.uniform(-.2, .3)))
        f0, f1 = edges[i], edges[i + 1] - 1 if i < n - 1 else edges[i + 1]
        key(cam, f0, p0, look_rot(p0, aim))
        key(cam, f1, p1, look_rot(p1, aim + side * 0.3))
    for fc in cam.animation_data.action.fcurves:       # 머무는 동안은 일정하게, 컷에서는 끊김 없이 순간이동
        for kp in fc.keyframe_points:
            kp.interpolation = "LINEAR"


def move_fpv(cam, info):
    """FPV 드론: 빠르게 앞으로 + 좌우로 기울기(롤) + 작은 흔들림"""
    (x0, y0, z0), (x1, y1, z1) = info["path"]
    cam.data.lens = 16
    for f in range(1, NF + 1):
        t = (f - 1) / max(1, NF - 1)
        e = t * t * (3 - 2 * t) * 0.25 + t * 0.75
        x = x0 + (x1 - x0) * e
        y = y0 + (y1 - y0) * e + 1.3 * math.sin(t * 2 * math.pi * 1.2)
        z = z0 + (z1 - z0) * e + 0.35 * math.sin(t * 2 * math.pi * 0.7)
        sh = Vector((RNG.gauss(0, 0.02), RNG.gauss(0, 0.02), RNG.gauss(0, 0.015)))
        loc = Vector((x, y, z)) + sh
        ahead = Vector((x + 6, y0 + (y1 - y0) * e + 1.3 * math.sin((t + 0.05) * 2 * math.pi * 1.2), z - 0.6))
        roll = -0.32 * math.cos(t * 2 * math.pi * 1.2) + RNG.gauss(0, 0.012)
        key(cam, f, loc, look_rot(loc, ahead, roll))


def move_slow(cam, info):
    (x0, y0, z0), (x1, y1, z1) = info["path"]
    tgt = info["look"]
    key(cam, 1, Vector((x0, y0, z0)), look_rot((x0, y0, z0), tgt))
    key(cam, NF, Vector((x1, y1, z1)), look_rot((x1, y1, z1), tgt))


# ───────── 입체 사진 ─────────
def build_photo():
    """사진을 깊이 지도대로 앞뒤로 밀어 낸 판 + 천천히 다가가며 옆으로 도는 카메라 (사람 없는 사진만)"""
    import numpy as np
    img = bpy.data.images.load(ARGS["photo"])
    W, H = img.size
    asp = W / H
    d = np.load(ARGS["depth"]).astype(np.float32)          # 0 = 멀다 ~ 1 = 가깝다
    dh, dw = d.shape
    nx, ny = 160, max(2, int(160 / asp))
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=nx, y_subdivisions=ny, size=1)
    g = bpy.context.active_object
    g.scale = (asp, 1, 1)
    bpy.ops.object.transform_apply(scale=True)
    amt = float(ARGS.get("depth_amt", 0.35))
    fov_h = 2 * math.atan(36 / 2 / 50)
    dist = 0.5 * min(asp, 16 / 9) / math.tan(fov_h / 2) * 0.84          # 화면이 사진 안쪽만 보이게 (가장자리 여유)
    uv = g.data.uv_layers.active.data
    vuv = {}
    for poly in g.data.polygons:
        for li in poly.loop_indices:
            vuv[g.data.loops[li].vertex_index] = uv[li].uv[:]
    for v in g.data.vertices:
        u, vv = vuv[v.index]
        px = min(dw - 1, max(0, int(u * (dw - 1))))
        py = min(dh - 1, max(0, int((1 - vv) * (dh - 1))))
        back = (1 - float(d[py, px])) * amt * 4                        # 먼 것은 뒤로
        k = 1 + back / dist                                            # 뒤로 간 만큼 키워 처음 화면에선 원래 사진과 똑같이 보이게
        v.co.x *= k
        v.co.y *= k
        v.co.z = -back
    m = bpy.data.materials.new("photo")
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = img
    tex.extension = "EXTEND"
    em = nt.nodes.new("ShaderNodeEmission")
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(tex.outputs[0], em.inputs[0])
    nt.links.new(em.outputs[0], out.inputs[0])
    g.data.materials.append(m)
    for p in g.data.polygons:
        p.use_smooth = True
    SC.cycles.samples = int(ARGS.get("samples", 6))
    SC.view_settings.view_transform = "Standard"
    SC.view_settings.look = "None"
    cam = camera(lens=50)
    sway = float(ARGS.get("sway", 0.05))
    for f in (1, NF):                                                   # 카메라는 사진을 똑바로 내려다봄(돌리지 않음): 옆으로 살짝 + 앞으로 다가감 → 가까운 것이 더 많이 움직임
        t = (f - 1) / max(1, NF - 1)
        cam.location = (sway * (t - 0.5) * 2 * min(asp, 16 / 9) * 0.5, 0.01 * (t - 0.5), dist * (1 - 0.1 * t))
        cam.rotation_euler = (0, 0, 0)
        cam.keyframe_insert("location", frame=f)
        cam.keyframe_insert("rotation_euler", frame=f)


def main():
    reset()
    if ARGS["kind"] == "입체사진":
        build_photo()
    else:
        info = SCENES[ARGS["scene"]]()
        cam = camera(lens=float(ARGS.get("lens", 28)))
        {"시간정지": move_frozen, "FPV": move_fpv, "천천히": move_slow}[ARGS.get("move", "시간정지")](cam, info)
        if ARGS.get("move") == "시간정지":
            for fc in cam.animation_data.action.fcurves:
                for kp in fc.keyframe_points:
                    kp.interpolation = "LINEAR"
            # 컷마다 순간이동: 앞 장면 끝 키와 다음 장면 첫 키 사이를 CONSTANT 로
            for fc in cam.animation_data.action.fcurves:
                pts = fc.keyframe_points
                for i in range(1, len(pts) - 1, 2):
                    pts[i].interpolation = "CONSTANT"
    out = ARGS["out"]
    os.makedirs(out, exist_ok=True)
    SC.render.filepath = os.path.join(out, "f")
    if ARGS.get("still"):
        SC.frame_set(int(ARGS.get("still_frame", 1)))
        SC.render.filepath = ARGS["still"]
        bpy.ops.render.render(write_still=True)
        return
    step = int(ARGS.get("step", 1))
    SC.frame_step = step
    if ARGS.get("save_blend"):
        bpy.ops.wm.save_as_mainfile(filepath=ARGS["save_blend"])
    bpy.ops.render.render(animation=True)


main()
