"""블록(복셀) 스타일 장면: 2,300년 전 메사피아 돌방 무덤 발굴 현장 — 카메라가 한 바퀴 도는 10초 영상
사용: blender -b -P 블렌더/블록_무덤.py -- <결과 폴더> [--frames 240] [--size 1920x1080] [--engine EEVEE|CYCLES] [--test]
(마인크래프트 그림·이름은 쓰지 않은 '우리만의' 블록 세상: 색·모양 모두 직접 정함)"""
import math
import os
import random
import sys

import bpy

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = argv[0] if argv else "/tmp/블록_무덤"
FRAMES = int(argv[argv.index("--frames") + 1]) if "--frames" in argv else 240
W, H = (int(v) for v in (argv[argv.index("--size") + 1] if "--size" in argv else "1920x1080").split("x"))
ENGINE = argv[argv.index("--engine") + 1] if "--engine" in argv else "EEVEE"
TEST = "--test" in argv
random.seed(7)

# ── 블록 종류: 색(RGB 0~1), 거칠기 ──
BLOCKS = {
    "풀": ((0.22, 0.42, 0.12), 0.9), "흙": ((0.36, 0.22, 0.12), 0.95), "파낸흙": ((0.48, 0.32, 0.18), 0.95),
    "응회암": ((0.78, 0.64, 0.40), 0.85), "덮개돌": ((0.70, 0.58, 0.38), 0.8), "어두운돌": ((0.42, 0.38, 0.33), 0.9),
    "글씨": ((0.55, 0.16, 0.10), 0.8), "토기": ((0.72, 0.36, 0.20), 0.7), "검은토기": ((0.12, 0.11, 0.10), 0.5),
    "나무줄기": ((0.36, 0.26, 0.17), 0.9), "올리브잎": ((0.28, 0.38, 0.20), 0.9), "사다리": ((0.55, 0.40, 0.24), 0.8),
    "자갈": ((0.62, 0.60, 0.56), 0.9), "천": ((0.85, 0.82, 0.74), 0.9),
}
world = {}      # (x,y,z) → 블록 이름 (크기 1)
small = []      # (x,y,z,크기,블록) — 토기처럼 작은 블록


def put(x, y, z, b):
    world[(x, y, z)] = b


def box(x0, x1, y0, y1, z0, z1, b, hollow=False):
    for x in range(x0, x1 + 1):
        for y in range(y0, y1 + 1):
            for z in range(z0, z1 + 1):
                if hollow and x0 < x < x1 and y0 < y < y1 and z0 < z:
                    continue
                put(x, y, z, b)


# 땅: 동그란 미니어처 섬 (반지름 18칸), 옆면은 흙·돌층이 보이게 아래로 8칸
R = 18
for x in range(-R, R + 1):
    for y in range(-R, R + 1):
        d = math.hypot(x, y)
        if d > R + 0.3:
            continue
        top = 0 if d < R - 2 else (0 if random.random() < 0.7 else -1)
        for z in range(-9, top):
            put(x, y, z, "어두운돌" if z < -7 else "흙")
        put(x, y, top, "풀")

# 발굴 구덩이: 가운데를 파냄 (바닥 z=-6), 가장자리에 파낸 흙 더미
for x in range(-8, 9):
    for y in range(-6, 7):
        for z in range(-5, 1):
            world.pop((x, y, z), None)
for x in range(-8, 9):
    for y in range(-6, 7):
        put(x, y, -6, "파낸흙")
for (cx, cy) in ((11, -9), (12, -8), (11, -8), (10, -9), (12, -9), (11, -10)):
    for z in range(1, 1 + random.randint(1, 3)):
        put(cx, cy, z, "파낸흙")

# 돌방 무덤: 응회암 상자 (바깥 9×5, 높이 4), 안은 비어 있음
box(-4, 4, -2, 2, -5, -2, "응회암", hollow=True)
for x in range(-3, 4):                       # 안쪽 바닥
    for y in range(-1, 2):
        put(x, y, -5, "어두운돌")
# 덮개돌: 동쪽 한 장만 남기고, 두 장은 들어 올려 구덩이 옆에 눕혀 둠 → 안이 보임
for x in range(2, 5):
    for y in range(-2, 3):
        put(x, y, -1, "덮개돌")
for x in range(-4, -1):
    for y in range(-2, 3):
        put(x - 1, y + 9, 1, "덮개돌")
for x in range(-1, 2):
    for y in range(-2, 3):
        put(x + 3, y + 9, 1, "덮개돌")
        if x == 1:
            put(x + 3, y + 9, 2, "덮개돌")
# 안쪽 벽의 두 줄 글씨 (붉은 띠, 글자 모양은 넣지 않음)
for x in range(-2, 3):
    put(x, 2, -3, "글씨") if x % 2 == 0 else None
    put(x, 2, -4, "글씨") if x % 2 == 1 else None
# 안에 놓인 토기 (작은 블록 0.5): 항아리 2개, 검은 칠 그릇 1개, 천 덮개
def jar(cx, cy, cz, b):
    for dz, rr in ((0, 0.5), (0.5, 1.0), (1.0, 1.0), (1.5, 0.5), (2.0, 0.5)):
        for dx in (-0.25, 0.25) if rr == 1.0 else (0.0,):
            for dy in (-0.25, 0.25) if rr == 1.0 else (0.0,):
                small.append((cx + dx, cy + dy, cz + dz * 0.5, 0.5, b))
jar(-2, 0, -4.25, "토기")
jar(2, -0.5, -4.25, "토기")
small += [(0.5, 0.5, -4.25, 0.5, "검은토기"), (1.0, 0.5, -4.25, 0.5, "검은토기"), (-0.5, -0.5, -4.25, 0.5, "천"), (0.0, -0.5, -4.25, 0.5, "천")]

# 무덤으로 내려가는 계단 (서쪽), 나무 사다리 (동쪽 구덩이 벽)
for i in range(5):
    for y in range(-1, 2):
        put(-8 + i, y, -6 + (4 - i), "응회암")
for z in range(-5, 1):
    put(8, 4, z, "사다리")

# 올리브 나무 몇 그루: 줄기 3~4칸 + 둥근 잎 덩어리
for (tx, ty) in ((-14, -10), (14, 11), (-12, 13), (15, -14), (-16, 3)):
    h = random.randint(3, 4)
    for z in range(1, h + 1):
        put(tx, ty, z, "나무줄기")
    for dx in range(-2, 3):
        for dy in range(-2, 3):
            for dz in range(0, 3):
                if dx * dx + dy * dy + (dz - 1) ** 2 <= 5 and random.random() < 0.85:
                    put(tx + dx, ty + dy, h + dz, "올리브잎")
# 흩어진 돌
for _ in range(18):
    x, y = random.randint(-R, R), random.randint(-R, R)
    if max(abs(x), abs(y)) > 9 and (x, y, 0) in world:
        small.append((x + 0.25, y + 0.25, 1, 0.5, "자갈"))


# ── 보이는 면만 메시로 (블록 종류마다 한 물체, 면마다 색을 살짝 다르게) ──
def build():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    faces_dir = [((1, 0, 0), [(1, 0, 0), (1, 1, 0), (1, 1, 1), (1, 0, 1)]), ((-1, 0, 0), [(0, 1, 0), (0, 0, 0), (0, 0, 1), (0, 1, 1)]),
                 ((0, 1, 0), [(1, 1, 0), (0, 1, 0), (0, 1, 1), (1, 1, 1)]), ((0, -1, 0), [(0, 0, 0), (1, 0, 0), (1, 0, 1), (0, 0, 1)]),
                 ((0, 0, 1), [(0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)]), ((0, 0, -1), [(0, 1, 0), (1, 1, 0), (1, 0, 0), (0, 0, 0)])]
    groups = {}
    for (x, y, z), b in world.items():
        jitter = random.uniform(-0.07, 0.07)
        for (dx, dy, dz), quad in faces_dir:
            if (x + dx, y + dy, z + dz) in world:
                continue
            groups.setdefault(b, []).append(([(x + qx, y + qy, z + qz) for qx, qy, qz in quad], jitter))
    for (x, y, z, s, b) in small:
        jitter = random.uniform(-0.05, 0.05)
        for _, quad in faces_dir:
            groups.setdefault(b, []).append(([(x + qx * s, y + qy * s, z + qz * s) for qx, qy, qz in quad], jitter))
    for b, quads in groups.items():
        verts, faces = [], []
        for q, _ in quads:
            faces.append([len(verts) + i for i in range(4)])
            verts += q
        me = bpy.data.meshes.new(b)
        me.from_pydata(verts, [], faces)
        col = me.color_attributes.new("tint", "FLOAT_COLOR", "CORNER")
        base, rough = BLOCKS[b]
        for fi, (q, j) in enumerate(quads):
            c = tuple(max(0, min(1, v * (1 + j))) for v in base) + (1.0,)
            for li in me.polygons[fi].loop_indices:
                col.data[li].color = c
        ob = bpy.data.objects.new(b, me)
        bpy.context.scene.collection.objects.link(ob)
        mat = bpy.data.materials.new(b)
        mat.use_nodes = True
        nt = mat.node_tree
        bsdf = nt.nodes["Principled BSDF"]
        att = nt.nodes.new("ShaderNodeVertexColor")
        att.layer_name = "tint"
        nt.links.new(att.outputs["Color"], bsdf.inputs["Base Color"])
        bsdf.inputs["Roughness"].default_value = rough
        me.materials.append(mat)


build()
sc = bpy.context.scene
# 하늘: 노을빛 그러데이션 (세계 배경색) + 낮은 해
wd = bpy.data.worlds.new("하늘")
sc.world = wd
wd.use_nodes = True
bg = wd.node_tree.nodes["Background"]
nt_ = wd.node_tree
lp = nt_.nodes.new("ShaderNodeLightPath")
amb = nt_.nodes.new("ShaderNodeBackground")
amb.inputs["Color"].default_value = (0.55, 0.50, 0.46, 1)
amb.inputs["Strength"].default_value = 0.55
bg.inputs["Color"].default_value = (0.035, 0.045, 0.08, 1)
bg.inputs["Strength"].default_value = 1.0
mix = nt_.nodes.new("ShaderNodeMixShader")
nt_.links.new(lp.outputs["Is Camera Ray"], mix.inputs["Fac"])
nt_.links.new(amb.outputs["Background"], mix.inputs[1])
nt_.links.new(bg.outputs["Background"], mix.inputs[2])
nt_.links.new(mix.outputs["Shader"], nt_.nodes["World Output"].inputs["Surface"])
sun = bpy.data.objects.new("해", bpy.data.lights.new("해", "SUN"))
sun.data.energy = 3.2
sun.data.color = (1.0, 0.82, 0.62)
sun.data.angle = math.radians(3)
sun.rotation_euler = (math.radians(66), 0, math.radians(225))
sc.collection.objects.link(sun)
fill = bpy.data.objects.new("채움빛", bpy.data.lights.new("채움빛", "SUN"))
fill.data.energy = 0.6
fill.data.color = (0.65, 0.75, 1.0)
fill.data.use_shadow = False
fill.rotation_euler = (math.radians(50), 0, math.radians(45))
sc.collection.objects.link(fill)
# 무덤 안을 비추는 작은 빛 (안이 너무 어둡지 않게)
inner = bpy.data.objects.new("안쪽빛", bpy.data.lights.new("안쪽빛", "POINT"))
inner.data.energy = 120
inner.data.color = (1.0, 0.78, 0.5)
inner.location = (0.5, 0.5, -2.5)
sc.collection.objects.link(inner)

# 카메라: 무덤 가운데를 보며 한 바퀴 (240프레임 = 24fps 10초)
target = bpy.data.objects.new("가운데", None)
target.location = (0.5, 0.5, -3.5)
sc.collection.objects.link(target)
rig = bpy.data.objects.new("회전축", None)
rig.location = (0.5, 0.5, 0)
sc.collection.objects.link(rig)
cam = bpy.data.objects.new("카메라", bpy.data.cameras.new("카메라"))
cam.data.lens = 29
cam.location = (38, 0, 25)
cam.parent = rig
sc.collection.objects.link(cam)
tc = cam.constraints.new("TRACK_TO")
tc.target = target
tc.track_axis = "TRACK_NEGATIVE_Z"
tc.up_axis = "UP_Y"
sc.camera = cam
sc.frame_start, sc.frame_end = 1, FRAMES
rig.rotation_euler = (0, 0, 0)
rig.keyframe_insert("rotation_euler", frame=1)
rig.rotation_euler = (0, 0, math.radians(360) * (FRAMES) / FRAMES)
rig.keyframe_insert("rotation_euler", frame=FRAMES + 1)
for fc in rig.animation_data.action.fcurves:
    for k in fc.keyframe_points:
        k.interpolation = "LINEAR"

# 렌더 설정
sc.render.resolution_x, sc.render.resolution_y = W, H
sc.render.fps = 24
sc.render.image_settings.file_format = "PNG"
sc.view_settings.view_transform = "Standard"
if ENGINE == "CYCLES":
    sc.render.engine = "CYCLES"
    sc.cycles.samples = 24
    sc.cycles.use_denoising = True
    sc.cycles.max_bounces = 4
else:
    sc.render.engine = "BLENDER_EEVEE"
    ee = sc.eevee
    ee.use_gtao = True
    ee.gtao_distance = 2.0
    ee.use_soft_shadows = True
    ee.shadow_cascade_size = "2048"
    ee.taa_render_samples = 16
sc.render.filepath = os.path.join(OUT, "frame_")
os.makedirs(OUT, exist_ok=True)
print("블록 수", len(world), "작은 블록", len(small))
if TEST:
    for f in (1, FRAMES // 4, FRAMES // 2):
        sc.frame_set(f)
        sc.render.filepath = os.path.join(OUT, f"test_{f:03d}.png")
        bpy.ops.render.render(write_still=True)
else:
    bpy.ops.render.render(animation=True)
