"""블록 영상: 「제주도는 어떻게 만들어졌을까」 — 문단(장면) 13개, 블록이 때맞춰 나타나고 사라지는 애니메이션 (블록영상.md)
사용: blender -b -P 블렌더/블록_제주_영상.py -- <결과 폴더> --scene <0~12> --frames <장 수> [--size 1280x720] [--test]
  블록마다 (나타나는 때, 사라지는 때) 를 0~1(장면 안 비율)로 적고 → 같은 때·같은 재료끼리 한 물체로 묶어 렌더 숨김을 키프레임
  --test : 장면의 처음·가운데·끝 3장만"""
import math
import os
import random
import sys

import bpy

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = argv[0]
SCENE = int(argv[argv.index("--scene") + 1])
FRAMES = int(argv[argv.index("--frames") + 1]) if "--frames" in argv else 120
W, H = (int(v) for v in (argv[argv.index("--size") + 1] if "--size" in argv else "1280x720").split("x"))
TEST = "--test" in argv
INF = 9.0

COL = {"바닥": (0.30, 0.29, 0.30), "현무암": (0.19, 0.19, 0.21), "새현무암": (0.27, 0.25, 0.25), "응회암": (0.66, 0.52, 0.34),
       "화산재": (0.42, 0.38, 0.34), "모래층": (0.76, 0.68, 0.50), "조개": (0.96, 0.94, 0.88), "풀": (0.25, 0.45, 0.16),
       "숲": (0.12, 0.30, 0.12), "모래": (0.82, 0.74, 0.54), "오름": (0.52, 0.58, 0.24), "붉은송이": (0.50, 0.22, 0.14),
       "용암": (1.0, 0.36, 0.05), "마그마": (1.0, 0.18, 0.02), "물": (0.10, 0.36, 0.62), "호수": (0.16, 0.48, 0.66), "김": (0.93, 0.93, 0.93),
       "절벽1": (0.55, 0.47, 0.36), "절벽2": (0.36, 0.33, 0.30), "절벽3": (0.70, 0.62, 0.46)}
EMIT = {"용암": 5.0, "마그마": 7.0}
ALPHA = {"물": 0.5, "김": 0.45, "호수": 0.8}
SEA = 0
rnd = random.Random(5)
B = {}          # (x,y,z) → [재료, 나타남(0~1), 사라짐(0~1)]


EX = []         # 같은 자리에 겹쳐 있다가 바뀌는 블록 (예: 용암 → 식은 현무암): (x,y,z,재료,나타남,사라짐)


def put(x, y, z, mat, on=0.0, off=INF):
    """같은 자리에 이미 더 일찍 나타나는 블록이 있으면 그대로 둠 (자라는 섬이 앞 단계 블록을 지우지 않게). 물은 언제나 덮어씀"""
    old = B.get((x, y, z))
    if old is not None and old[0] not in ALPHA and old[1] <= on:
        return
    B[(x, y, z)] = [mat, on, off]


def disk(R, z0, z1, mat, on=0.0):
    for x in range(-R, R + 1):
        for y in range(-R, R + 1):
            if math.hypot(x, y) <= R + 0.3:
                for z in range(z0, z1):
                    put(x, y, z, mat, on)


def sea(R, cut=False, bottom=-12):
    disk(R, bottom - 3, bottom, "바닥")
    for x in range(-R, R + 1):
        for y in range(-R, R + 1):
            if math.hypot(x, y) > R + 0.3 or (cut and y < 0):
                continue
            for z in range(bottom, SEA):
                if (x, y, z) not in B:
                    put(x, y, z, "물")


def shield_h(x, y, top=11, R=23):
    d = math.hypot(x, y * 1.35)          # 제주처럼 동서로 긴 타원
    if d > R:
        return None
    return int(round(top * (1 - (d / R) ** 1.25) + 0.6 * math.sin(x * 0.7) * math.cos(y * 0.6)))


def island(on=0.0, top=11, R=23, green=True, bottom=-12):
    for x in range(-R - 1, R + 2):
        for y in range(-R, R + 1):
            h = shield_h(x, y, top, R)
            if h is None:
                continue
            if green and h >= SEA:
                put(x, y, h, "숲" if h >= top - 3 else ("모래" if h <= 1 else "풀"), on)
            for z in range(bottom, h + 1):
                put(x, y, z, "현무암", on)


def cone(cx, cy, r, base, height, mat, on=0.0, crater=True, top_mat=None):
    for x in range(cx - r - 1, cx + r + 2):
        for y in range(cy - r - 1, cy + r + 2):
            d = math.hypot(x - cx, y - cy)
            if d > r + 0.2:
                continue
            h = base + int(round(height * (1 - d / (r + 0.5))))
            if crater and d < r * 0.35:
                h -= 1
            for z in range(base, h + 1):
                put(x, y, z, mat, on)
            if top_mat:
                put(x, y, h, top_mat, on)


def steam(cx, cy, z0, on, off, n=6, spread=2):
    for i in range(n):
        put(cx + rnd.randint(-spread, spread), cy + rnd.randint(-spread, spread), z0 + i // 2, "김", on + i * 0.01, off)


def summit(on=0.0, lake=None):
    """한라산 꼭대기: 둥근 봉우리 + 가운데 분화구(백록담). lake=(가운데 고이는 때, 가득 차는 때) 또는 None(처음부터 물)"""
    cone(0, 0, 4, 10, 6, "숲", on, crater=False)
    for x in range(-3, 4):
        for y in range(-3, 4):
            if math.hypot(x, y) <= 2.2:
                for z in range(12, 18):
                    B.pop((x, y, z), None)
                B[(x, y, 11)] = ["현무암", on, INF]
                t = 0.0 if lake is None else (lake[0] if math.hypot(x, y) < 1.2 else lake[1])
                B[(x, y, 12)] = ["호수", t, INF]


# ── 장면마다: 블록 + 카메라 길 [(비율, 위치, 보는 곳, 렌즈)] + 빛 ──
CAM, LAVA_LIGHT = [], []
S = SCENE
if S == 0:                       # 180만 년 전, 끝없이 펼쳐진 얕은 바다
    sea(24)
    CAM = [(0, (44, -34, 30), (0, 0, -4), 32), (1, (36, -40, 18), (0, 0, -6), 32)]
elif S == 1:                     # 바다 밑에서 마그마가 올라와 바닷물과 만나 펑 (단면)
    sea(22, cut=True)
    for i, z in enumerate(range(-15, -11)):
        for x in (0, 1):
            for y in (0, 1):
                put(x, y, z, "마그마", 0.05 + i * 0.08)
    for k in range(4):                                   # 바다 밑에 작은 화산이 자람
        cone(0, 0, 3 + k * 2, -12, 2 + k, "새현무암", 0.35 + k * 0.12)
    for b in range(3):                                   # 물과 만나 터짐 → 김이 솟았다 사라짐
        steam(0, 1, -6 + b, 0.55 + b * 0.13, 0.55 + b * 0.13 + 0.12, n=10, spread=3)
    for (x, y) in ((0, 0), (1, 0), (0, 1), (1, 1)):
        put(x, y, -12 + 6, "용암", 0.78)
    for k in list(B):                                    # 단면: 앞쪽 절반을 잘라 속이 보이게
        if k[1] < 0:
            B.pop(k)
    LAVA_LIGHT = [((0.5, 0.5, -8), 0.3, 1.0, 700)]
    CAM = [(0, (0, -40, -4), (0.5, 0.5, -9), 32), (1, (14, -34, 2), (0.5, 0.5, -8), 32)]
elif S == 2:                     # 화산재와 조개 섞인 모래가 번갈아 쌓임 (단면 가까이)
    sea(16, cut=True, bottom=-12)
    for i in range(8):
        mat = "화산재" if i % 2 == 0 else "모래층"
        for x in range(-12, 13):
            for y in range(0, 10):
                put(x, y, -12 + i, mat, 0.08 + i * 0.1)
                if mat == "모래층" and rnd.random() < 0.08:
                    put(x, y, -12 + i, "조개", 0.08 + i * 0.1)
    for k in list(B):
        if k[1] < 0:
            B.pop(k)
    CAM = [(0, (16, -24, -8), (0, 3, -9), 30), (1, (-12, -22, -4), (0, 3, -8), 30)]
elif S == 3:                     # 서귀포 바닷가 절벽의 줄무늬 지층과 조개 화석
    sea(22, bottom=-8)
    for x in range(-18, 19):
        for y in range(0, 14):
            for z in range(-8, 9):
                lay = (z + 8) // 2
                mat = ("절벽1", "절벽2", "절벽3", "화산재")[lay % 4]
                if mat == "절벽3" and rnd.random() < 0.06:
                    mat = "조개"
                put(x, y, z, mat)
            put(x, y, 9, "풀")
    CAM = [(0, (-14, -22, 2), (-6, 0, 2), 34), (1, (14, -22, 3), (6, 0, 2), 34)]
elif S == 4:                     # 바다 위로 올라온 화산에서 묽은 용암이 넓게 퍼짐
    sea(26)
    cone(0, 0, 6, -12, 14, "새현무암", 0.0)
    for ring in range(1, 9):
        for x in range(-ring * 2 - 2, ring * 2 + 3):
            for y in range(-ring * 2 - 2, ring * 2 + 3):
                d = math.hypot(x, y)
                if ring * 2 - 2 < d <= ring * 2 and (x, y, 2) not in B:
                    t = 0.1 + ring * 0.09
                    put(x, y, 1, "용암", t, t + 0.25)
                    if (x, y, 0) not in B or B[(x, y, 0)][0] == "물":
                        B.pop((x, y, 0), None)
                    put(x, y, 0, "현무암", t + 0.25)
                    put(x, y, 1, "현무암", t + 0.25) if False else None
    LAVA_LIGHT = [((0.5, 0.5, 6), 0.0, 1.0, 1200)]
    CAM = [(0, (40, -36, 30), (0, 0, 0), 30), (1, (30, -40, 22), (0, 0, 0), 30)]
elif S == 5:                     # 흘러나오고 굳기를 거듭하며 섬이 넓어지고 높아짐 (타임랩스)
    sea(28)
    for k in range(7):
        island(0.05 + k * 0.13, top=2 + k * 2, R=8 + k * 2, green=False)
    LAVA_LIGHT = [((0.5, 0.5, 14), 0.0, 1.0, 600)]
    CAM = [(0, (44, -40, 26), (0, 0, 2), 30), (1, (48, -26, 32), (0, 0, 4), 30)]
elif S == 6:                     # 방패 화산 — 가운데 한라산
    sea(28)
    island(0.0)
    summit()
    CAM = [(0, (46, -30, 24), (0, 0, 6), 30), (0.5, (10, -52, 28), (0, 0, 6), 30), (1, (-40, -36, 22), (0, 0, 6), 30)]
elif S == 7:                     # 오름이 하나씩 터져 오름
    sea(28)
    island(0.0)
    summit()
    spots = [(10, 4), (-12, 2), (5, -10), (-7, -8), (14, -3), (-3, 11), (8, 9), (-15, -4), (16, 6), (-9, 9), (2, -13), (12, -9)]
    for i, (ox, oy) in enumerate(spots):
        hb = shield_h(ox, oy) or 0
        t = 0.08 + i * 0.07
        cone(ox, oy, 3, hb, 4, "오름", t)
        EX.append((ox, oy, hb + 4, "용암", t, t + 0.07))
        steam(ox, oy, hb + 5, t, t + 0.08, n=4, spread=1)
    CAM = [(0, (40, -40, 34), (0, 0, 4), 30), (1, (24, -46, 30), (0, 0, 4), 30)]
elif S == 8:                     # 한라산 꼭대기 백록담에 빗물이 고임
    sea(28)
    island(0.0)
    summit(lake=(0.3, 0.6))
    CAM = [(0, (18, -18, 26), (0.5, 0.5, 12), 34), (1, (10, -12, 20), (0.5, 0.5, 12), 34)]
elif S == 9:                     # 바닷가 성산일출봉: 세 번의 폭발로 쌓인 화산재 고리
    sea(26)
    island(0.0, top=8, R=14)
    for k in range(3):
        r = 7 - k
        for x in range(-r - 1, r + 2):
            for y in range(-r - 1, r + 2):
                d = math.hypot(x, y)
                if r - 2.2 <= d <= r:
                    for z in range(0, 3 + k * 3):
                        put(x + 18, y - 6, z, "응회암", 0.12 + k * 0.28)
        steam(18, -6, 4 + k * 3, 0.1 + k * 0.28, 0.24 + k * 0.28, n=10, spread=3)
    for x in range(14, 23):
        for y in range(-10, -1):
            if math.hypot(x - 18, y + 6) < 3.5:
                put(x, y, 1, "풀", 0.9)
    CAM = [(0, (40, -30, 16), (18, -6, 3), 32), (1, (34, -24, 12), (18, -6, 4), 32)]
elif S == 10:                    # 중문 바닷가: 용암이 식으며 갈라져 돌기둥(주상절리)
    sea(22, bottom=-8)
    for x in range(-14, 15):
        for y in range(4, 16):
            for z in range(-8, 6):
                put(x, y, z, "현무암")
            put(x, y, 6, "풀")
    for x in range(-12, 13):
        for y in range(-2, 4):
            h = 2 + (x * 5 + y * 3) % 3
            tc_ = 0.3 + abs(x) * 0.02
            crack = (x % 3 == 0) or (y % 3 == 0)               # 식으며 생긴 틈 (거북 등처럼)
            for z in range(-8, h + 1):
                EX.append((x, y, z, "용암", 0.0, tc_))
                if not crack:
                    put(x, y, z, "현무암" if (x // 3 + y // 3) % 2 else "새현무암", tc_)
    LAVA_LIGHT = [((0, -4, 2), 0.0, 0.5, 900)]
    CAM = [(0, (-6, -30, 6), (0, 1, 1), 36), (1, (8, -28, 5), (0, 1, 1), 36)]
elif S == 11:                    # 다시 보기: 바다 → 섬 → 한라산 → 오름 (빠른 타임랩스)
    sea(28)
    cone(0, 0, 5, -12, 9, "새현무암", 0.05, crater=True)
    for k in range(4):
        island(0.2 + k * 0.12, top=5 + k * 3, R=12 + k * 3, green=(k == 3))
    for i, (ox, oy) in enumerate([(10, 4), (-12, 2), (5, -10), (-7, -8), (14, -3), (-3, 11), (8, 9)]):
        hb = shield_h(ox, oy) or 0
        cone(ox, oy, 3, hb, 4, "오름", 0.72 + i * 0.03)
    CAM = [(0, (46, -38, 28), (0, 0, 2), 30), (1, (40, -44, 32), (0, 0, 4), 30)]
else:                            # 마무리: 지금의 제주를 크게 한 바퀴
    sea(28)
    island(0.0)
    summit()
    for (ox, oy) in [(10, 4), (-12, 2), (5, -10), (-7, -8), (14, -3), (-3, 11), (8, 9), (-15, -4), (16, 6), (-9, 9)]:
        hb = shield_h(ox, oy) or 0
        cone(ox, oy, 3, hb, 4, "오름", 0.0)
    CAM = [(0, (50, 0, 30), (0, 0, 4), 30), (0.5, (0, -50, 30), (0, 0, 4), 30), (1, (-50, 0, 30), (0, 0, 4), 30)]

# ── 메시: (재료, 나타남, 사라짐) 묶음마다 한 물체, 보이는 면만 ──
FACES = [((1, 0, 0), [(1, 0, 0), (1, 1, 0), (1, 1, 1), (1, 0, 1)]), ((-1, 0, 0), [(0, 1, 0), (0, 0, 0), (0, 0, 1), (0, 1, 1)]),
         ((0, 1, 0), [(1, 1, 0), (0, 1, 0), (0, 1, 1), (1, 1, 1)]), ((0, -1, 0), [(0, 0, 0), (1, 0, 0), (1, 0, 1), (0, 0, 1)]),
         ((0, 0, 1), [(0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)]), ((0, 0, -1), [(0, 1, 0), (1, 1, 0), (1, 0, 0), (0, 0, 0)])]
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
groups = {}
for (x, y, z), (mat, on, off) in B.items():
    j = rnd.uniform(-0.07, 0.07)
    for (dx, dy, dz), quad in FACES:
        nb = B.get((x + dx, y + dy, z + dz))
        if nb is not None:
            nmat, non, noff = nb
            if mat in ALPHA:
                if nmat == mat or nmat not in ALPHA and non <= on and noff >= off:
                    continue
            elif nmat not in ALPHA and non <= on and noff >= off:
                continue
        groups.setdefault((mat, on, off), []).append(([(x + a, y + b, z + c) for a, b, c in quad], j))
for (x, y, z, mat, on, off) in EX:
    j = rnd.uniform(-0.07, 0.07)
    for (dx, dy, dz), quad in FACES:
        if any(e[:3] == (x + dx, y + dy, z + dz) and e[3] == mat for e in ()):
            continue
        groups.setdefault((mat, on, off), []).append(([(x + a, y + b, z + c) for a, b, c in quad], j))
mats = {}
for mat_name in COL:
    mt = bpy.data.materials.new(mat_name)
    mt.use_nodes = True
    nt = mt.node_tree
    bs = nt.nodes["Principled BSDF"]
    vc = nt.nodes.new("ShaderNodeVertexColor")
    vc.layer_name = "tint"
    nt.links.new(vc.outputs["Color"], bs.inputs["Base Color"])
    bs.inputs["Roughness"].default_value = 0.45 if mat_name in ("물", "호수") else 0.9
    if mat_name in ("물", "호수"):
        bs.inputs["Specular IOR Level"].default_value = 0.15
    if mat_name in EMIT:
        nt.links.new(vc.outputs["Color"], bs.inputs["Emission Color"])
        bs.inputs["Emission Strength"].default_value = EMIT[mat_name]
    if mat_name in ALPHA:
        bs.inputs["Alpha"].default_value = ALPHA[mat_name]
        mt.blend_method = "BLEND"
        mt.shadow_method = "NONE"
        mt.show_transparent_back = False
    mats[mat_name] = mt
for (mat, on, off), quads in groups.items():
    verts, faces = [], []
    for q, _ in quads:
        faces.append([len(verts) + i for i in range(4)])
        verts += q
    me = bpy.data.meshes.new(mat)
    me.from_pydata(verts, [], faces)
    col = me.color_attributes.new("tint", "FLOAT_COLOR", "CORNER")
    for fi, (q, j) in enumerate(quads):
        c = tuple(max(0, min(1, v * (1 + j))) for v in COL[mat]) + (1.0,)
        for li in me.polygons[fi].loop_indices:
            col.data[li].color = c
    me.materials.append(mats[mat])
    ob = bpy.data.objects.new(f"{mat}_{on:.2f}_{off:.2f}", me)
    sc.collection.objects.link(ob)
    f_on, f_off = 1 + on * (FRAMES - 1), 1 + off * (FRAMES - 1)
    if on > 0:
        ob.hide_render = True
        ob.keyframe_insert("hide_render", frame=1)
        ob.hide_render = False
        ob.keyframe_insert("hide_render", frame=max(2, int(round(f_on))))
    if off < INF:
        ob.hide_render = False
        if on <= 0:
            ob.keyframe_insert("hide_render", frame=1)
        ob.hide_render = True
        ob.keyframe_insert("hide_render", frame=max(2, int(round(f_off))))

# ── 빛·하늘 ──
wd = bpy.data.worlds.new("하늘")
sc.world = wd
wd.use_nodes = True
nt = wd.node_tree
bg = nt.nodes["Background"]
lp = nt.nodes.new("ShaderNodeLightPath")
amb = nt.nodes.new("ShaderNodeBackground")
amb.inputs["Color"].default_value = (0.56, 0.58, 0.62, 1)
amb.inputs["Strength"].default_value = 0.6
bg.inputs["Color"].default_value = (0.05, 0.07, 0.12, 1)
mix = nt.nodes.new("ShaderNodeMixShader")
nt.links.new(lp.outputs["Is Camera Ray"], mix.inputs["Fac"])
nt.links.new(amb.outputs["Background"], mix.inputs[1])
nt.links.new(bg.outputs["Background"], mix.inputs[2])
nt.links.new(mix.outputs["Shader"], nt.nodes["World Output"].inputs["Surface"])
sun = bpy.data.objects.new("해", bpy.data.lights.new("해", "SUN"))
sun.data.energy = 3.0 if S < 12 else 2.6
sun.data.color = (1.0, 0.9, 0.78) if S < 12 else (1.0, 0.78, 0.58)
sun.rotation_euler = (math.radians(55), 0, math.radians(210))
sc.collection.objects.link(sun)
for (loc, a, b, e) in LAVA_LIGHT:
    li = bpy.data.objects.new("용암빛", bpy.data.lights.new("용암빛", "POINT"))
    li.data.color = (1.0, 0.45, 0.15)
    li.location = loc
    sc.collection.objects.link(li)
    for f, en in ((1, 0 if a > 0 else e), (1 + a * (FRAMES - 1), e), (1 + b * (FRAMES - 1), e if b >= 1 else 0)):
        li.data.energy = en
        li.data.keyframe_insert("energy", frame=f)

# ── 카메라 ──
cam = bpy.data.objects.new("카메라", bpy.data.cameras.new("카메라"))
tgt = bpy.data.objects.new("보는곳", None)
sc.collection.objects.link(cam)
sc.collection.objects.link(tgt)
cam.data.clip_start = 0.1
cam.data.clip_end = 400
tc = cam.constraints.new("TRACK_TO")
tc.target = tgt
tc.track_axis = "TRACK_NEGATIVE_Z"
tc.up_axis = "UP_Y"
sc.camera = cam
for (u, loc, look, lens) in CAM:
    f = 1 + u * (FRAMES - 1)
    cam.location = loc
    cam.keyframe_insert("location", frame=f)
    tgt.location = look
    tgt.keyframe_insert("location", frame=f)
    cam.data.lens = lens
    cam.data.keyframe_insert("lens", frame=f)

ENGINE = argv[argv.index("--engine") + 1] if "--engine" in argv else "EEVEE"
if ENGINE == "WORKBENCH":      # 빠른 단순 그리기: 빛·그림자 단순, 블록 색은 그대로 (블록영상.md)
    sc.render.engine = "BLENDER_WORKBENCH"
    sh = sc.display.shading
    sh.light = "STUDIO"
    sh.color_type = "VERTEX"
    sh.show_shadows = True
    sh.shadow_intensity = 0.45
    sh.show_cavity = True
    sh.cavity_type = "BOTH"
    sh.show_specular_highlight = False
    sc.display.render_aa = "8"
    sc.display.shading.background_type = "WORLD" if False else sh.background_type
    sc.world.color = (0.05, 0.07, 0.12)
    sh.color_type = "MATERIAL"                  # 물을 비쳐 보이게 하려면 재료 색(투명도 포함)을 써야 함
    for nm, mt in mats.items():
        a_ = ALPHA.get(nm, 1.0)
        c_ = COL[nm] if nm not in EMIT else (1.0, 0.55, 0.15)
        mt.diffuse_color = (c_[0], c_[1], c_[2], a_)
sc.render.engine = "BLENDER_EEVEE" if ENGINE == "EEVEE" else sc.render.engine
sc.eevee.use_gtao = True
sc.eevee.use_bloom = True
sc.eevee.bloom_intensity = 0.04
sc.eevee.use_soft_shadows = True
sc.eevee.shadow_cascade_size = "2048"
sc.eevee.taa_render_samples = 12
sc.view_settings.view_transform = "Standard"
sc.render.resolution_x, sc.render.resolution_y = W, H
sc.render.fps = 24
sc.frame_start, sc.frame_end = 1, FRAMES
os.makedirs(OUT, exist_ok=True)
print("장면", S, "블록", len(B), "물체", len(groups))
if TEST:
    for f in (1, FRAMES // 2, FRAMES):
        sc.frame_set(f)
        sc.render.filepath = os.path.join(OUT, f"s{S:02d}_test_{f:04d}.png")
        bpy.ops.render.render(write_still=True)
else:
    sc.render.filepath = os.path.join(OUT, f"s{S:02d}_")
    sc.render.image_settings.file_format = "JPEG"
    sc.render.image_settings.quality = 92
    bpy.ops.render.render(animation=True)
