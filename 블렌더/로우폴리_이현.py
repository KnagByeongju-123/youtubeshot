"""로우폴리(점토 인형 느낌) 3D 인물 시험 — 「조선에 떨어진 미래 의사」 이현 (사용자 요청 2026-11-07 '② 간단한 로우폴리로 이현 테스트')
xvfb-run -a -s "-screen 0 1920x1080x24" blender -b -P 블렌더/로우폴리_이현.py -- <결과 폴더> [--size 1280x720] [--frames 240] [--engine WORKBENCH|EEVEE] [--still]
  - 기본 도형(원기둥·원뿔·공)을 코드로 쌓아 인물을 만듦: 해진 흰 도포, 검은 끈 띠, 갓(윗면 납작한 원통 + 넓은 반투명 챙 + 턱끈), 상투 머리, 짚신
  - 카메라가 인물 둘레를 한 바퀴 돎 (24fps, 기본 240장 = 10초). --still 이면 앞·옆·뒤 세 장만
  - 결과: <폴더>/frame_####.png (+ --still 이면 앞.png·옆.png·뒤.png)"""
import math
import os
import sys

import bpy

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = os.path.abspath(argv[0] if argv else "블렌더_이현")
W, H = [int(v) for v in (argv[argv.index("--size") + 1] if "--size" in argv else "1280x720").split("x")]
FRAMES = int(argv[argv.index("--frames") + 1]) if "--frames" in argv else 240
ENGINE = argv[argv.index("--engine") + 1] if "--engine" in argv else "WORKBENCH"
STILL = "--still" in argv
os.makedirs(OUT, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
scn = bpy.context.scene


def mat(name, rgb, alpha=1.0, rough=0.7):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*rgb, alpha)          # 단순 그리기(Workbench)가 쓰는 색
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*rgb, 1)
    b.inputs["Roughness"].default_value = rough
    if alpha < 1:
        b.inputs["Alpha"].default_value = alpha
        m.blend_method = "BLEND"
    return m


SKIN = mat("피부", (0.93, 0.74, 0.60))
ROBE = mat("도포", (0.86, 0.86, 0.83))
ROBE_D = mat("도포그늘", (0.74, 0.75, 0.73))
PATCH = mat("기운곳", (0.70, 0.68, 0.62))
BLACK = mat("검정", (0.04, 0.04, 0.05), rough=0.4)
HAIR = mat("머리", (0.05, 0.05, 0.06), rough=0.35)
BRIM = mat("갓챙", (0.03, 0.03, 0.04), alpha=0.72, rough=0.3)
PANTS = mat("바지", (0.95, 0.95, 0.93))
STRAW = mat("짚신", (0.78, 0.62, 0.36))
LIP = mat("입", (0.70, 0.36, 0.33))
GROUND = mat("바닥", (0.90, 0.86, 0.77))


def smooth(o, level=1):
    for p in o.data.polygons:
        p.use_smooth = True
    if level:
        mod = o.modifiers.new("부드럽게", "SUBSURF")
        mod.levels = mod.render_levels = level
    return o


def put(o, m, name):
    o.name = name
    o.data.materials.append(m)
    return o


def cone(name, m, r1, r2, depth, loc, rot=(0, 0, 0), verts=24, sm=1, scale=(1, 1, 1)):
    bpy.ops.mesh.primitive_cone_add(vertices=verts, radius1=r1, radius2=r2, depth=depth, location=loc, rotation=rot)
    o = bpy.context.object
    o.scale = scale
    return smooth(put(o, m, name), sm)


def ball(name, m, r, loc, scale=(1, 1, 1), sm=1, seg=24):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=seg // 2, radius=r, location=loc)
    o = bpy.context.object
    o.scale = scale
    return smooth(put(o, m, name), sm)


def box(name, m, size, loc, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = bpy.context.object
    o.scale = size
    return put(o, m, name)


def rod(name, m, p0, p1, r):
    """두 점을 잇는 가는 원기둥 (끈·팔)"""
    x0, y0, z0 = p0
    x1, y1, z1 = p1
    dx, dy, dz = x1 - x0, y1 - y0, z1 - z0
    L = math.sqrt(dx * dx + dy * dy + dz * dz)
    bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=r, depth=L, location=((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))
    o = bpy.context.object
    o.rotation_euler = (0, math.acos(dz / L), math.atan2(dy, dx))
    return smooth(put(o, m, name), 0)


# ── 인물 (키 약 1.75, 앞 = -Y 방향) ──
YS = 0.82                                    # 도포 앞뒤 납작함


def robe_r(z):                               # 높이 z 에서 도포 반지름 (밑단 0.32 → 어깨 0.2)
    return 0.32 - (z - 0.22) / 1.12 * 0.12


def front(z, out=0.006, x=0.0):              # 그 높이·가로 위치 x 의 도포 앞면 y
    r = robe_r(z)
    return -(YS * math.sqrt(max(r * r - x * x, 0)) + out)


for s in (-1, 1):
    box("짚신", STRAW, (0.09, 0.2, 0.035), (s * 0.08, -0.03, 0.02))
    cone("바짓단", PANTS, 0.06, 0.07, 0.22, (s * 0.08, 0, 0.13), sm=0)
cone("도포", ROBE, 0.32, 0.2, 1.12, (0, 0, 0.78), scale=(1, YS, 1), sm=0, verts=40)
ball("어깨", ROBE, 0.2, (0, 0, 1.33), scale=(1.12, YS, 0.42))
cone("도포밑단", ROBE_D, 0.325, 0.322, 0.04, (0, 0, 0.24), scale=(1, YS, 1), sm=0, verts=40)
for (x, z) in ((0.15, 0.5), (-0.11, 0.82), (0.07, 0.62)):
    box("기운곳", PATCH, (0.07, 0.01, 0.06), (x, front(z, 0.004, x), z), rot=(0, 0, math.atan2(x, robe_r(z)) * 0.8))
for s in (-1, 1):
    box("깃", PANTS, (0.04, 0.012, 0.24), (s * 0.05, -0.178, 1.27), rot=(0, s * -0.55, 0))
box("섶선", ROBE_D, (0.012, 0.01, 0.9), (0.06, front(0.72, 0.003, 0.06), 0.72), rot=(math.atan(0.12 * YS / 1.12), 0, 0))
cone("띠", BLACK, robe_r(1.04) * 1.04, robe_r(1.04) * 1.04, 0.025, (0, 0, 1.04), scale=(1, YS, 1), sm=0, verts=40)
fy = front(1.04, 0.012)
ball("매듭", BLACK, 0.02, (0.05, fy, 1.035))
rod("띠끈1", BLACK, (0.04, fy, 1.03), (0.035, front(0.7, 0.01), 0.7), 0.008)
rod("띠끈2", BLACK, (0.06, fy, 1.03), (0.075, front(0.74, 0.01), 0.74), 0.008)
for s in (-1, 1):
    cone("소매", ROBE, 0.12, 0.075, 0.48, (s * 0.255, 0, 1.11), rot=(0, s * -0.16, 0), sm=0)
    ball("손", SKIN, 0.042, (s * 0.295, -0.01, 0.84), scale=(0.8, 0.9, 1.1))
cone("목", SKIN, 0.045, 0.05, 0.1, (0, 0, 1.44), sm=0)
ball("머리", SKIN, 0.105, (0, 0, 1.575), scale=(0.92, 0.95, 1.12))
ball("머리카락", HAIR, 0.106, (0, 0.022, 1.612), scale=(0.95, 0.93, 0.98))
ball("상투", HAIR, 0.033, (0, 0.012, 1.71))
for s in (-1, 1):
    ball("눈", BLACK, 0.011, (s * 0.034, -0.095, 1.578), scale=(1, 0.6, 1.25), sm=0, seg=12)
    box("눈썹", HAIR, (0.034, 0.008, 0.007), (s * 0.036, -0.094, 1.606), rot=(0, s * -0.12, 0))
    ball("귀", SKIN, 0.022, (s * 0.096, 0, 1.57), scale=(0.5, 0.8, 1.2), sm=0, seg=12)
ball("코", SKIN, 0.013, (0, -0.104, 1.552), scale=(0.8, 1, 1.2), sm=0, seg=12)
box("입", LIP, (0.028, 0.006, 0.006), (0, -0.097, 1.522))
cone("망건", BLACK, 0.101, 0.098, 0.02, (0, 0.012, 1.628), scale=(0.95, 0.97, 1), sm=0, verts=32)
# 갓: 모자집(윗면 납작한 원통) + 넓은 반투명 챙 + 턱끈 — 윗면에 꼭지 없음 (사용자 지적 2026-11-07)
cone("갓모자집", BLACK, 0.082, 0.076, 0.17, (0, 0.01, 1.74), verts=32, sm=0)
cone("갓챙", BRIM, 0.27, 0.27, 0.008, (0, 0.01, 1.66), verts=48, sm=0)
for s in (-1, 1):
    rod("갓끈", BLACK, (s * 0.085, -0.01, 1.655), (s * 0.03, -0.075, 1.47), 0.004)

# ── 바닥·배경·빛 ──
bpy.ops.mesh.primitive_plane_add(size=12, location=(0, 0, 0))
put(bpy.context.object, GROUND, "바닥")
world = bpy.data.worlds.new("세상")
scn.world = world
world.color = (0.93, 0.9, 0.84)

# ── 카메라 (인물 둘레를 돎) ──
target = bpy.data.objects.new("목표", None)
target.location = (0, 0, 0.9)
scn.collection.objects.link(target)
cam_data = bpy.data.cameras.new("카메라")
cam_data.lens = 50
cam = bpy.data.objects.new("카메라", cam_data)
scn.collection.objects.link(cam)
scn.camera = cam
tc = cam.constraints.new("TRACK_TO")
tc.target = target
tc.track_axis = "TRACK_NEGATIVE_Z"
tc.up_axis = "UP_Y"
R, CZ = 4.8, 1.15


def cam_at(angle):     # angle 0 = 정면(-Y 쪽에서 봄)
    cam.location = (R * math.sin(angle), -R * math.cos(angle), CZ)


# ── 렌더 설정 ──
scn.view_settings.view_transform = "Standard"      # 색이 바래지 않게
scn.render.resolution_x, scn.render.resolution_y = W, H
scn.render.fps = 24
scn.render.image_settings.file_format = "PNG"
if ENGINE == "EEVEE":
    scn.render.engine = "BLENDER_EEVEE"
    sun = bpy.data.objects.new("해", bpy.data.lights.new("해", "SUN"))
    sun.data.energy = 3.5
    sun.rotation_euler = (math.radians(50), 0, math.radians(30))
    scn.collection.objects.link(sun)
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.93, 0.9, 0.84, 1)
    scn.eevee.use_soft_shadows = True
else:
    scn.render.engine = "BLENDER_WORKBENCH"
    sh = scn.display.shading
    sh.light = "STUDIO"
    sh.color_type = "MATERIAL"
    sh.show_shadows = True
    sh.shadow_intensity = 0.35
    sh.show_cavity = True
    sh.cavity_type = "BOTH"
    sh.show_object_outline = True        # 먹선처럼 외곽선
    sh.object_outline_color = (0.08, 0.07, 0.07)
    sh.background_type = "WORLD"
    scn.display.render_aa = "8"

if STILL:
    for nm, a in (("앞", 0), ("옆", math.pi / 2), ("뒤", math.pi), ("비스듬", math.pi / 5)):
        cam_at(a)
        scn.render.filepath = os.path.join(OUT, nm + ".png")
        bpy.ops.render.render(write_still=True)
else:
    for f in range(FRAMES):
        cam_at(2 * math.pi * f / FRAMES)
        scn.render.filepath = os.path.join(OUT, "frame_%04d.png" % (f + 1))
        bpy.ops.render.render(write_still=True)
print("OK", OUT)
