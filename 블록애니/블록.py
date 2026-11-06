"""블록 애니 — 블렌더(무료·오픈소스, GPL)로 블록 인형을 직접 만들고 움직여 진짜 애니메이션을 그림 (사용자 결정 2026-11-06: 움직이는 애니메이션)
로블록스·마인크래프트 캐릭터를 따라 하지 않은 우리만의 블록 인형 (머리·몸·팔·다리가 네모 블록, 얼굴은 작은 블록 눈·눈썹·입).

  blender -b -P 블록애니/블록.py -- 시트 <인물이름> <결과.png>      → 캐릭터 시트 (앞·옆·옆·뒤 4장 나란히, 흰 배경)
  다른 스크립트에서: exec(open('블록애니/블록.py').read()) 뒤 make_person(...), walk(...), etc.
"""
import bpy, bmesh, math, sys, os

CAST = {
    # 이름: 피부, 머리색, 머리 모양, 옷 위, 옷 아래, 신발, 키 배율, 수염, 안경
    "만수": dict(skin=(0.86, 0.66, 0.52), hair=(0.82, 0.82, 0.80), hair_style="short", top=(0.30, 0.40, 0.48), top2=(0.85, 0.82, 0.72),
                 bottom=(0.36, 0.30, 0.24), shoes=(0.18, 0.14, 0.12), height=1.0, beard=(0.62, 0.62, 0.60), glasses=False, bend=4),
    "서연": dict(skin=(0.95, 0.78, 0.66), hair=(0.12, 0.09, 0.08), hair_style="bob", top=(0.80, 0.55, 0.35), top2=(0.95, 0.93, 0.88),
                 bottom=(0.20, 0.22, 0.30), shoes=(0.30, 0.20, 0.16), height=0.94, beard=None, glasses=False, bend=0),
}


import random as _rnd


def _pixel_tex(name, rgb, var=0.07, edge=0.80, n=16, seed=0):
    """블록 무늬: 16×16 픽셀, 칸마다 밝기를 조금씩 다르게 + 가장자리 1픽셀을 어둡게 (블록 사이 선이 보이게)"""
    img = bpy.data.images.get(name)
    if img:
        return img
    img = bpy.data.images.new(name, n, n, alpha=False)
    r = _rnd.Random(hash(name) & 0xffff ^ seed)
    px = []
    for y in range(n):
        for x in range(n):
            k = 1 + r.uniform(-var, var)
            if x in (0, n - 1) or y in (0, n - 1):
                k *= edge
            px += [min(1, rgb[0] * k), min(1, rgb[1] * k), min(1, rgb[2] * k), 1]
    img.pixels = px
    img.pack()
    return img


def mat(name, rgb, rough=0.85, emit=0.0, tex=True, var=0.07, edge=0.80):
    """재질. tex=True 면 픽셀 블록 무늬(참고: 사용자가 보낸 피라미드 장면처럼 블록마다 결과 테두리가 보임)"""
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    b.inputs["Roughness"].default_value = rough
    if tex:
        t = nt.nodes.new("ShaderNodeTexImage")
        t.image = _pixel_tex("tex_" + name, rgb, var, edge)
        t.interpolation = "Closest"
        nt.links.new(t.outputs["Color"], b.inputs["Base Color"])
    else:
        b.inputs["Base Color"].default_value = (*rgb, 1)
    if emit:
        b.inputs["Emission Color"].default_value = (*rgb, 1)
        b.inputs["Emission Strength"].default_value = emit
    return m


def box(name, size, loc, m, parent=None, bevel=0.0, tile=False):
    """네모 블록. tile=True 면 무늬가 1칸(1m)마다 되풀이 (땅·벽처럼 큰 블록), 아니면 면마다 무늬 한 장 (인형 부품)"""
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bm.loops.layers.uv.new("UVMap")
    bmesh.ops.create_cube(bm, size=1.0, calc_uvs=True)
    for v in bm.verts:
        v.co.x *= size[0]; v.co.y *= size[1]; v.co.z *= size[2]
    if tile:
        uv = bm.loops.layers.uv.active
        for f in bm.faces:
            nx, ny, nz = (abs(c) for c in f.normal)
            for lp in f.loops:
                co = lp.vert.co + __import__("mathutils").Vector(loc)
                if nz >= nx and nz >= ny:
                    lp[uv].uv = (co.x + 0.5, co.y + 0.5)
                elif nx >= ny:
                    lp[uv].uv = (co.y + 0.5, co.z + 0.5)
                else:
                    lp[uv].uv = (co.x + 0.5, co.z + 0.5)
    if bevel:
        bmesh.ops.bevel(bm, geom=list(bm.edges), offset=bevel, segments=1, affect="EDGES")
    bm.to_mesh(me); bm.free()
    me.materials.append(m)
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    if parent:
        o.parent = parent
    o.location = loc
    return o


def empty(name, loc, parent=None):
    o = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(o)
    if parent:
        o.parent = parent
    o.location = loc
    return o


def make_person(nm, loc=(0, 0, 0), facing=0.0):
    """블록 인형 하나. 돌아가는 부분(머리·팔·다리)은 빈 축에 매달아 회전으로 움직임. 정면 = -y 쪽"""
    c = CAST[nm]
    k = c["height"]
    p = nm + "_"
    root = empty(p + "root", loc)
    root.rotation_euler = (0, 0, facing)
    torso = empty(p + "torso", (0, 0, 0.75 * k), root)          # 엉덩이 높이 (몸통 숙이기)
    torso.rotation_euler = (math.radians(c["bend"]), 0, 0)
    box(p + "body", (0.52, 0.30, 0.62 * k), (0, 0, 0.31 * k), mat(p + "top", c["top"]), torso, 0.02)
    box(p + "collar", (0.30, 0.31, 0.14), (0, -0.005, 0.56 * k), mat(p + "top2", c["top2"]), torso)
    neck = empty(p + "neck", (0, 0, 0.62 * k), torso)
    head = empty(p + "head", (0, 0, 0), neck)
    skin = mat(p + "skin", c["skin"])
    box(p + "skull", (0.50, 0.50, 0.50), (0, 0, 0.26), skin, head, 0.03)
    hair = mat(p + "hair", c["hair"])
    if c["hair_style"] == "short":
        box(p + "hair_top", (0.53, 0.53, 0.10), (0, 0.01, 0.53), hair, head)
        box(p + "hair_back", (0.53, 0.12, 0.30), (0, 0.22, 0.38), hair, head)
    else:   # 단발: 옆과 뒤를 덮고 앞머리
        box(p + "hair_top", (0.55, 0.55, 0.11), (0, 0.0, 0.54), hair, head)
        box(p + "hair_back", (0.56, 0.14, 0.50), (0, 0.22, 0.27), hair, head)
        box(p + "hair_L", (0.07, 0.48, 0.42), (-0.28, 0.03, 0.30), hair, head)
        box(p + "hair_R", (0.07, 0.48, 0.42), (0.28, 0.03, 0.30), hair, head)
        box(p + "bangs", (0.50, 0.06, 0.10), (0, -0.25, 0.47), hair, head)
    eye = mat("eye", (0.05, 0.04, 0.04), 0.3, tex=False)
    white = mat("eye_white", (0.97, 0.97, 0.97), 0.3, tex=False)
    brow = mat(p + "brow", tuple(x * 0.7 for x in c["hair"]) if c["hair_style"] == "short" else c["hair"])
    face = empty(p + "face", (0, -0.251, 0.26), head)
    for sx in (-0.11, 0.11):
        box(p + f"ew{sx}", (0.10, 0.01, 0.09), (sx, 0, 0.02), white, face)
        box(p + f"e{sx}", (0.055, 0.012, 0.07), (sx + (0.012 if sx > 0 else -0.012), -0.002, 0.015), eye, face)
        box(p + f"b{sx}", (0.12, 0.012, 0.025), (sx, -0.002, 0.10), brow, face)
    box(p + "mouth", (0.12, 0.012, 0.022), (0, -0.002, -0.12), mat("mouth", (0.45, 0.20, 0.18), tex=False), face)
    if c["beard"]:
                box(p + "mustache", (0.22, 0.03, 0.04), (0, -0.01, -0.075), mat(p + "beardm", c["beard"]), face)
    arms = {}
    for side, sx in (("L", -0.36), ("R", 0.36)):
        a = empty(p + "arm" + side, (sx, 0, 0.55 * k), torso)
        box(p + "sleeve" + side, (0.19, 0.20, 0.32 * k), (0, 0, -0.14 * k), mat(p + "top", c["top"]), a)
        box(p + "hand" + side, (0.17, 0.18, 0.26 * k), (0, 0, -0.42 * k), skin, a)
        arms[side] = a
    legs = {}
    for side, sx in (("L", -0.13), ("R", 0.13)):
        l = empty(p + "leg" + side, (sx, 0, 0.75 * k), root)
        box(p + "pant" + side, (0.24, 0.26, 0.64 * k), (0, 0, -0.32 * k), mat(p + "bottom", c["bottom"]), l)
        box(p + "shoe" + side, (0.25, 0.32, 0.11), (0, -0.03, -0.70 * k), mat(p + "shoes", c["shoes"]), l)
        legs[side] = l
    return dict(root=root, torso=torso, neck=neck, head=head, arms=arms, legs=legs, k=k)


def look(scn, sun_rgb=(1.0, 0.92, 0.80), sun_e=3.0, sky=(0.20, 0.48, 0.85), horizon=(0.85, 0.85, 0.80), sky_e=1.0, white_bg=False):
    """조명·하늘·색 관리 (Standard + 약간 진하게)"""
    sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN"))
    scn.collection.objects.link(sun)
    sun.data.energy = sun_e; sun.data.color = sun_rgb; sun.data.angle = math.radians(3)
    sun.rotation_euler = (math.radians(50), 0, math.radians(35))
    w = bpy.data.worlds.new("w"); scn.world = w; w.use_nodes = True
    nt = w.node_tree
    bg = nt.nodes["Background"]
    if white_bg:
        bg.inputs[0].default_value = (1, 1, 1, 1); bg.inputs[1].default_value = 0.35
    else:   # 하늘: 지평선은 옅게, 위로 갈수록 파랗게 (참고 장면)
        tc = nt.nodes.new("ShaderNodeTexCoord"); sep = nt.nodes.new("ShaderNodeSeparateXYZ")
        ramp = nt.nodes.new("ShaderNodeValToRGB")
        nt.links.new(tc.outputs["Generated"], sep.inputs[0]); nt.links.new(sep.outputs["Z"], ramp.inputs["Fac"])
        ramp.color_ramp.elements[0].position = 0.0; ramp.color_ramp.elements[0].color = (*horizon, 1)
        ramp.color_ramp.elements[1].position = 0.45; ramp.color_ramp.elements[1].color = (*sky, 1)
        nt.links.new(ramp.outputs["Color"], bg.inputs[0]); bg.inputs[1].default_value = sky_e
    scn.view_settings.view_transform = "Standard"
    scn.view_settings.look = "Medium High Contrast" if not white_bg else "None"
    scn.eevee.use_gtao = True; scn.eevee.gtao_distance = 0.6
    scn.eevee.use_soft_shadows = True
    scn.eevee.shadow_cube_size = "1024"; scn.eevee.shadow_cascade_size = "2048"
    scn.eevee.taa_render_samples = 24
    return sun


def camera(scn, loc, target, lens=40):
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
    scn.collection.objects.link(cam); scn.camera = cam
    cam.location = loc; cam.data.lens = lens
    t = empty("cam_target", target)
    con = cam.constraints.new("TRACK_TO"); con.target = t; con.track_axis = "TRACK_NEGATIVE_Z"; con.up_axis = "UP_Y"
    return cam, t


def clear():
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o)


def sheet(nm, out):
    """캐릭터 시트: 앞·옆(왼)·옆(오)·뒤 4장 나란히, 전신, 흰 배경 (CLAUDE.md 3장 시트 모양)"""
    scn = bpy.context.scene
    clear()
    for i, ang in enumerate((0, 90, -90, 180)):
        make_person(nm, ((i - 1.5) * 1.6, 0, 0), math.radians(ang))
    box("floor", (40, 40, 0.01), (0, 0, -0.005), mat("floor", (1, 1, 1), 1.0, tex=False))
    look(scn, sun_e=1.6, white_bg=True)
    box("bgwall", (60, 0.1, 30), (0, 6, 5), mat("bgwall", (1, 1, 1), 1.0, emit=1.0, tex=False))
    cam, _ = camera(scn, (0, -14, 1.0), (0, 0, 0.85), lens=50)
    r = scn.render
    r.engine = "BLENDER_EEVEE"; r.resolution_x = 2048; r.resolution_y = 768; r.film_transparent = False
    r.filepath = out
    bpy.ops.render.render(write_still=True)


if __name__ == "__main__" and "--" in sys.argv:
    a = sys.argv[sys.argv.index("--") + 1:]
    if a and a[0] == "시트":
        sheet(a[1], a[2])
