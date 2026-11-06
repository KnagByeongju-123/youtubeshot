"""블록 장면: 제주도는 어떻게 만들어졌을까 — 단계별 시험 그림 (블록영상.md)
사용: blender -b -P 블렌더/블록_제주.py -- <결과 폴더> [--stages 1,2,3,4] [--size 960x540]
  1 바닷속 화산 분출  2 섬이 바다 위로  3 한라산(방패 화산)과 오름  4 바닷가 주상절리(용암이 식으며 갈라진 돌기둥)"""
import math
import os
import random
import sys

import bpy

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = argv[0] if argv else "/tmp/블록_제주"
STAGES = [int(x) for x in (argv[argv.index("--stages") + 1] if "--stages" in argv else "1,2,3,4").split(",")]
W, H = (int(v) for v in (argv[argv.index("--size") + 1] if "--size" in argv else "960x540").split("x"))

BLOCKS = {"바닥": (0.30, 0.30, 0.33), "현무암": (0.20, 0.20, 0.22), "새현무암": (0.28, 0.26, 0.26), "응회암": (0.62, 0.50, 0.36),
          "풀": (0.25, 0.45, 0.16), "숲": (0.13, 0.30, 0.12), "모래": (0.80, 0.72, 0.52), "눈": (0.92, 0.94, 0.97),
          "용암": (1.0, 0.35, 0.05), "물": (0.10, 0.35, 0.60), "호수": (0.15, 0.45, 0.62), "김": (0.92, 0.92, 0.92)}
EMIT = {"용암": 6.0}
ALPHA = {"물": 0.55, "김": 0.35, "호수": 0.8}
SEA = 0          # 바다 높이 (z < SEA 는 물)


def build_world(stage):
    random.seed(3)
    w = {}
    R = 22
    for x in range(-R, R + 1):
        for y in range(-R, R + 1):
            if math.hypot(x, y) > R + 0.3:
                continue
            for z in range(-14, -10):
                w[(x, y, z)] = "바닥"
    def cone(cx, cy, base_r, top_z, bottom_z, mat, slope=1.0, crater=0, top_mat=None):
        for x in range(cx - base_r - 1, cx + base_r + 2):
            for y in range(cy - base_r - 1, cy + base_r + 2):
                d = math.hypot(x - cx, y - cy)
                h = int(round(top_z - d * slope + random.uniform(-0.4, 0.4)))
                if d > base_r:
                    continue
                if crater and d < crater:
                    h = top_z - 1
                for z in range(bottom_z, h + 1):
                    w[(x, y, z)] = mat
                if top_mat and h >= SEA:
                    w[(x, y, h)] = top_mat
    if stage == 1:          # 바닷속에서 작은 화산이 자라는 중
        cone(0, 0, 7, -4, -10, "새현무암", slope=0.9, crater=2)
        for (x, y) in ((0, 0), (1, 0), (0, 1), (1, 1)):
            w[(x, y, -4)] = "용암"
        for i, z in enumerate(range(-3, 0)):
            w[(random.randint(-1, 1), random.randint(-1, 1), z)] = "김"
    elif stage == 2:        # 섬이 바다 위로 고개를 내밂 (물과 만나 터지는 수성 화산 → 응회암 고리)
        cone(0, 0, 11, 3, -10, "새현무암", slope=0.75, crater=3)
        cone(0, 0, 5, 4, 0, "응회암", slope=0.5, crater=3)
        for (x, y) in ((0, 0), (1, 0), (0, 1), (-1, 0), (0, -1)):
            w[(x, y, 3)] = "용암"
        for z in range(5, 10):
            for _ in range(3):
                w[(random.randint(-2, 2), random.randint(-2, 2), z)] = "김"
    else:                   # 한라산: 완만한 방패 모양 + 꼭대기 호수(백록담) + 둘레의 작은 오름들
        cone(0, 0, 19, 12, -10, "현무암", slope=0.62, crater=2, top_mat="풀")
        for x in range(-2, 3):
            for y in range(-2, 3):
                if math.hypot(x, y) < 1.8:
                    w[(x, y, 11)] = "호수"
                    w.pop((x, y, 12), None)
        for (ox, oy) in ((9, 5), (-10, 3), (5, -11), (-6, -9), (12, -4), (-3, 12), (8, 10)):
            base_h = max(z for (xx, yy, z) in w if xx == ox and yy == oy) if (ox, oy, -10) in w else 0
            cone(ox, oy, 2, base_h + 3, base_h, "숲", slope=1.2)
        for (x, y, z), b in list(w.items()):           # 높은 곳은 숲, 해안은 모래
            if b == "풀" and z >= 8:
                w[(x, y, z)] = "숲"
            if b == "풀" and z <= 1:
                w[(x, y, z)] = "모래"
        if stage == 4:      # 남쪽 바닷가 주상절리: 높이가 조금씩 다른 돌기둥이 벽처럼 늘어섬
            for x in range(-6, 7):
                for y in range(-19, -16):
                    for z in list(range(-10, 6)):
                        w.pop((x, y, z), None)
                    h = 2 + (x * 7 + y * 3) % 3 + (1 if (x + y) % 2 else 0)
                    for z in range(-10, h):
                        w[(x, y, z)] = "현무암" if (x + y) % 2 else "새현무암"
    # 바다: 땅이 없는 곳을 수면까지 채움 (보이는 윗면만 남게)
    for x in range(-22, 23):
        for y in range(-22, 23):
            if math.hypot(x, y) > 22.3:
                continue
            for z in range(-10, SEA):
                if (x, y, z) not in w:
                    w[(x, y, z)] = "물"
    return w


FACES = [((1, 0, 0), [(1, 0, 0), (1, 1, 0), (1, 1, 1), (1, 0, 1)]), ((-1, 0, 0), [(0, 1, 0), (0, 0, 0), (0, 0, 1), (0, 1, 1)]),
         ((0, 1, 0), [(1, 1, 0), (0, 1, 0), (0, 1, 1), (1, 1, 1)]), ((0, -1, 0), [(0, 0, 0), (1, 0, 0), (1, 0, 1), (0, 0, 1)]),
         ((0, 0, 1), [(0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)]), ((0, 0, -1), [(0, 1, 0), (1, 1, 0), (1, 0, 0), (0, 0, 0)])]


def mesh_world(w):
    groups = {}
    for (x, y, z), b in w.items():
        j = random.uniform(-0.07, 0.07)
        for (dx, dy, dz), quad in FACES:
            nb = w.get((x + dx, y + dy, z + dz))
            if nb is not None and (nb == b or (nb not in ALPHA and b not in ALPHA)) and not (b in ALPHA and nb not in ALPHA and nb is not None and False):
                if not (b in ALPHA) or nb == b:
                    continue
            if b not in ALPHA and nb is not None and nb not in ALPHA:
                continue
            groups.setdefault(b, []).append(([(x + a, y + c, z + e) for a, c, e in quad], j))
    for b, quads in groups.items():
        verts, faces = [], []
        for q, _ in quads:
            faces.append([len(verts) + i for i in range(4)])
            verts += q
        me = bpy.data.meshes.new(b)
        me.from_pydata(verts, [], faces)
        col = me.color_attributes.new("tint", "FLOAT_COLOR", "CORNER")
        for fi, (q, j) in enumerate(quads):
            c = tuple(max(0, min(1, v * (1 + j))) for v in BLOCKS[b]) + (1.0,)
            for li in me.polygons[fi].loop_indices:
                col.data[li].color = c
        ob = bpy.data.objects.new(b, me)
        bpy.context.scene.collection.objects.link(ob)
        mat = bpy.data.materials.new(b)
        mat.use_nodes = True
        nt = mat.node_tree
        bsdf = nt.nodes["Principled BSDF"]
        vc = nt.nodes.new("ShaderNodeVertexColor")
        vc.layer_name = "tint"
        nt.links.new(vc.outputs["Color"], bsdf.inputs["Base Color"])
        bsdf.inputs["Roughness"].default_value = 0.15 if b in ("물", "호수") else 0.9
        if b in EMIT:
            nt.links.new(vc.outputs["Color"], bsdf.inputs["Emission Color"])
            bsdf.inputs["Emission Strength"].default_value = EMIT[b]
        if b in ALPHA:
            bsdf.inputs["Alpha"].default_value = ALPHA[b]
            mat.blend_method = "BLEND"
            mat.shadow_method = "NONE"
            mat.show_transparent_back = False
        me.materials.append(mat)


def scene_setup(stage):
    sc = bpy.context.scene
    wd = bpy.data.worlds.new("하늘")
    sc.world = wd
    wd.use_nodes = True
    nt = wd.node_tree
    bg = nt.nodes["Background"]
    lp = nt.nodes.new("ShaderNodeLightPath")
    amb = nt.nodes.new("ShaderNodeBackground")
    amb.inputs["Color"].default_value = (0.55, 0.58, 0.62, 1)
    amb.inputs["Strength"].default_value = 0.6
    bg.inputs["Color"].default_value = (0.05, 0.07, 0.12, 1)
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(lp.outputs["Is Camera Ray"], mix.inputs["Fac"])
    nt.links.new(amb.outputs["Background"], mix.inputs[1])
    nt.links.new(bg.outputs["Background"], mix.inputs[2])
    nt.links.new(mix.outputs["Shader"], nt.nodes["World Output"].inputs["Surface"])
    sun = bpy.data.objects.new("해", bpy.data.lights.new("해", "SUN"))
    sun.data.energy = 3.0
    sun.data.color = (1.0, 0.9, 0.78)
    sun.rotation_euler = (math.radians(55), 0, math.radians(210))
    sc.collection.objects.link(sun)
    if stage <= 2:
        glow = bpy.data.objects.new("용암빛", bpy.data.lights.new("용암빛", "POINT"))
        glow.data.energy = 900
        glow.data.color = (1.0, 0.45, 0.15)
        glow.location = (0.5, 0.5, -3 if stage == 1 else 5)
        sc.collection.objects.link(glow)
    cam = bpy.data.objects.new("카메라", bpy.data.cameras.new("카메라"))
    tgt = bpy.data.objects.new("가운데", None)
    sc.collection.objects.link(tgt)
    if stage == 4:
        cam.location, tgt.location, cam.data.lens = (6, -38, 6), (0.5, -18, 2), 40
    else:
        cam.location, tgt.location, cam.data.lens = (40, -30, 26), (0.5, 0.5, -3 if stage == 1 else 0), 30
    sc.collection.objects.link(cam)
    tc = cam.constraints.new("TRACK_TO")
    tc.target = tgt
    tc.track_axis = "TRACK_NEGATIVE_Z"
    tc.up_axis = "UP_Y"
    sc.camera = cam
    sc.render.engine = "BLENDER_EEVEE"
    sc.eevee.use_gtao = True
    sc.eevee.use_bloom = True
    sc.eevee.use_soft_shadows = True
    sc.eevee.taa_render_samples = 16
    sc.view_settings.view_transform = "Standard"
    sc.render.resolution_x, sc.render.resolution_y = W, H


os.makedirs(OUT, exist_ok=True)
for st in STAGES:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    random.seed(11)
    mesh_world(build_world(st))
    scene_setup(st)
    bpy.context.scene.render.filepath = os.path.join(OUT, f"제주_{st}.png")
    bpy.ops.render.render(write_still=True)
    print("OK", st)
