"""블렌더 평면 그리기(Grease Pencil) 시험: 한산도 대첩 학익진 (약 15초) — 손으로 그린 듯한 선·면
사용: blender -b -P 평면애니/한산도_그리스펜슬.py -- <장면 그림 폴더> [--size 1920x1080]
  → <폴더>/f_0001.png … (자막·이름표는 합칠 때 ffmpeg 로 얹음: 평면애니/한산도_합치기.sh)
흐름: 일본 수군이 좁은 견내량을 빠져나와 조선 유인선을 쫓음 → 한산도 앞 넓은 바다에서 조선 수군이 학 날개처럼 펼침
     → 날개 선이 펜으로 그려지듯 → 포를 쏨 → 일본 배가 회색으로 가라앉음"""
import math
import os
import sys

import bpy

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = argv[0]
W, H = (int(v) for v in (argv[argv.index("--size") + 1] if "--size" in argv else "1920x1080").split("x"))
FPS, SEC = 24, 15.0
NF = int(SEC * FPS)
U = 0.01          # 그림 좌표(1920×1080 화소) → 블렌더 단위


def P(x, y, z=0.0):
    return (x * U, -y * U, z)


def ease(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def lerp(a, b, u):
    return a + (b - a) * u


bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = "BLENDER_EEVEE"
sc.eevee.taa_render_samples = 8
sc.render.resolution_x, sc.render.resolution_y = W, H
sc.render.fps = FPS
sc.frame_start, sc.frame_end = 1, NF
sc.view_settings.view_transform = "Standard"
sc.render.film_transparent = False
wd = bpy.data.worlds.new("w")
sc.world = wd
wd.color = (0.35, 0.6, 0.78)

MATS = {}


def gmat(name, stroke, fill=None, stroke_on=True):
    if name in MATS:
        return MATS[name]
    m = bpy.data.materials.new(name)
    bpy.data.materials.create_gpencil_data(m)
    g = m.grease_pencil
    g.show_stroke = stroke_on
    g.color = (*stroke, 1.0)
    if fill:
        g.show_fill = True
        g.fill_color = (*fill, 1.0)
    else:
        g.show_fill = False
    MATS[name] = m
    return m


def srgb(c):
    return tuple(((v / 255) ** 2.2) for v in c)


def gp_object(name, z=0.0):
    gd = bpy.data.grease_pencils.new(name)
    ob = bpy.data.objects.new(name, gd)
    sc.collection.objects.link(ob)
    ob.location.z = z
    lay = gd.layers.new("선")
    fr = lay.frames.new(1)
    return ob, gd, fr


def add_stroke(ob, fr, pts, mat_name, width=60, cyclic=True, pressure=1.0):
    m = MATS[mat_name]
    if m.name not in [s.name for s in ob.data.materials if s]:
        ob.data.materials.append(m)
    idx = [s.name for s in ob.data.materials].index(m.name)
    st = fr.strokes.new()
    st.material_index = idx
    st.line_width = width
    st.use_cyclic = cyclic
    st.display_mode = "3DSPACE"
    st.points.add(len(pts))
    for i, (x, y, z) in enumerate(pts):
        st.points[i].co = (x, y, z)
        st.points[i].pressure = pressure
        st.points[i].strength = 1.0
    return st


def wobble(ob, f=0.25, seed=1):
    md = ob.grease_pencil_modifiers.new("손떨림", "GP_NOISE")
    md.factor, md.factor_strength, md.factor_thickness = f, 0.0, 0.3
    md.noise_scale, md.seed = 0.6, seed
    if hasattr(md, "use_random"):
        md.use_random = False


SEA, LAND, LAND2, EDGE = srgb((88, 152, 196)), srgb((214, 200, 150)), srgb((150, 176, 110)), srgb((60, 70, 60))
BLUE, BLUE2, RED, RED2, BLACK = srgb((40, 90, 200)), srgb((15, 35, 100)), srgb((210, 60, 50)), srgb((110, 25, 20)), srgb((35, 35, 45))
gmat("바다", SEA, SEA, stroke_on=False)
gmat("물결", srgb((150, 195, 225)))
gmat("땅", EDGE, LAND)
gmat("풀", LAND2, LAND2, stroke_on=False)
gmat("조선", BLUE2, BLUE)
gmat("거북선", srgb((15, 15, 20)), BLACK)
gmat("일본", RED2, RED)
gmat("포탄", srgb((120, 80, 0)), srgb((255, 215, 70)))
gmat("날개", srgb((255, 255, 255)))

# ── 바다·물결·땅 ──
ob, gd, fr = gp_object("바다", z=-0.3)
add_stroke(ob, fr, [P(-20, -20), P(1940, -20), P(1940, 1100), P(-20, 1100)], "바다", width=10)
ob, gd, fr = gp_object("물결", z=-0.2)
for i, y in enumerate(range(60, 1080, 90)):
    pts = [P(x, y + 10 * math.sin(x / 70 + i), 0) for x in range(0, 1960, 40)]
    add_stroke(ob, fr, pts, "물결", width=25, cyclic=False)
wobble(ob, 0.4, 3)
LANDS = [
    [(0, 0), (820, 0), (860, 120), (830, 260), (700, 330), (520, 360), (300, 420), (120, 470), (0, 480)],
    [(980, 0), (1920, 0), (1920, 760), (1760, 700), (1600, 560), (1400, 430), (1180, 330), (1010, 230), (960, 110)],
    [(1280, 860), (1400, 800), (1540, 820), (1600, 900), (1560, 990), (1420, 1030), (1300, 990), (1240, 930)],
]
ob, gd, fr = gp_object("땅", z=-0.1)
for poly in LANDS:
    add_stroke(ob, fr, [P(x, y) for x, y in poly], "땅", width=90)
    cx, cy = sum(p[0] for p in poly) / len(poly), sum(p[1] for p in poly) / len(poly)
    add_stroke(ob, fr, [P(cx + 90 * math.cos(a / 12 * 6.283), cy + 50 * math.sin(a / 12 * 6.283)) for a in range(12)], "풀", width=10)
wobble(ob, 0.5, 7)

# ── 배 움직임 (평면애니/한산도_시험.py 와 같은 길) ──
JP = [(i % 5, i // 5) for i in range(20)]
CENTER, R_WING = (1180, 700), 330


def jp_pos(k, t):
    col, row = JP[k]
    sx, sy = 900 + (col - 2) * 34, 40 + row * 46
    ex, ey = 1180 + (col - 2) * 58 + (row - 1.5) * 10, 600 + row * 42 + abs(col - 2) * 10   # 학익진 'U' 안쪽
    u = ease((t - 1.5) / 7.0)
    return lerp(sx, ex, u), lerp(sy, ey, u), math.atan2(ey - sy, ex - sx)


def decoy_pos(k, t):
    sx, sy, ex, ey = 900 + (k - 1.5) * 50, 330, 1180 + (k - 1.5) * 70, 960      # 날개 뒤로 빠짐
    u = ease((t - 1.0) / 6.0)
    return lerp(sx, ex, u), lerp(sy, ey, u), math.atan2(ey - sy, ex - sx)


def kr_pos(k, t, n=18):
    sx, sy = 1500 + (k % 6) * 24, 760 + (k // 6) * 40
    a = math.radians(160 - 140 * k / (n - 1))                     # 아래로 볼록한 'U' — 열린 쪽이 적(위쪽 견내량)을 향함
    ex, ey = CENTER[0] + R_WING * math.cos(a) * 1.25, CENTER[1] + R_WING * math.sin(a) * 0.9 - 140
    u = ease((t - 4.0) / 3.5)
    x, y = lerp(sx, ex, u), lerp(sy, ey, u)
    face = math.atan2(CENTER[1] - y, CENTER[0] - x)
    move = math.atan2(ey - sy, ex - sx)
    return x, y, lerp(move, face, ease((u - 0.7) / 0.3)) if u > 0.7 else move


SHIP = [(0.62, 0), (0.28, -0.2), (-0.45, -0.2), (-0.5, 0), (-0.45, 0.2), (0.28, 0.2)]


def make_ship(name, mat, scale=1.0):
    ob, gd, fr = gp_object(name, z=0.0)
    L = 46 * scale
    add_stroke(ob, fr, [(px * L * U, -py * L * 2.2 * U, 0) for px, py in SHIP], mat, width=40)
    add_stroke(ob, fr, [(-0.3 * L * U, 0, 0.001), (0.2 * L * U, 0, 0.001)], mat, width=30, cyclic=False)
    wobble(ob, 0.15, hash(name) % 50)
    return ob


def animate(ob, fn, step=4, extra=None):
    prev = None
    for f in list(range(1, NF + 1, step)) + [NF]:
        t = (f - 1) / FPS
        x, y, a = fn(t)
        ob.location = (x * U, -y * U, ob.location.z)
        rz = -a
        if prev is not None:                                     # 돌 때 반 바퀴 넘게 튀지 않게
            while rz - prev > math.pi:
                rz -= 2 * math.pi
            while rz - prev < -math.pi:
                rz += 2 * math.pi
        prev = rz
        ob.rotation_euler = (0, 0, rz)
        ob.keyframe_insert("location", frame=f)
        ob.keyframe_insert("rotation_euler", frame=f)
        if extra:
            extra(ob, t, f)


def sink(ob, k):
    tint = ob.grease_pencil_modifiers.new("가라앉음", "GP_TINT")
    tint.color = (0.25, 0.25, 0.25)
    op = ob.grease_pencil_modifiers.new("흐려짐", "GP_OPACITY")
    hit = 1.0 if (k * 7) % 10 < 8 else 0.25
    for t_, fac in ((10.0, 0.0), (13.0, hit)):
        f = 1 + int(t_ * FPS)
        tint.factor = fac
        tint.keyframe_insert("factor", frame=f)
        op.factor = 1 - 0.7 * fac
        op.keyframe_insert("factor", frame=f)
        ob.scale = (1 - 0.35 * fac,) * 3
        ob.keyframe_insert("scale", frame=f)


for k in range(20):
    o = make_ship(f"일본{k}", "일본")
    animate(o, lambda t, k=k: jp_pos(k, t))
    sink(o, k)
for k in range(4):
    o = make_ship(f"유인{k}", "조선")
    animate(o, lambda t, k=k: decoy_pos(k, t))
KR = []
for k in range(18):
    o = make_ship(f"조선{k}", "거북선" if k == 8 else "조선", 1.1 if k == 8 else 1.0)
    animate(o, lambda t, k=k: kr_pos(k, t))
    KR.append(o)

# ── 학익진 날개 선: 펜으로 그리듯 (Build) ──
ob, gd, fr = gp_object("날개", z=0.05)
ends = [kr_pos(k, 8.0) for k in range(18)]
add_stroke(ob, fr, [P(x, y) for x, y, _ in ends], "날개", width=55, cyclic=False)
bd = ob.grease_pencil_modifiers.new("그려짐", "GP_BUILD")
bd.mode, bd.transition = "SEQUENTIAL", "GROW"
bd.use_restrict_frame_range = True
bd.frame_start, bd.frame_end = int(6.5 * FPS), int(8.0 * FPS)
for f_, v in ((1, True), (int(6.4 * FPS), True), (int(6.5 * FPS), False), (int(12.5 * FPS), False), (int(12.6 * FPS), True)):
    ob.hide_render = v
    ob.keyframe_insert("hide_render", frame=f_)
wobble(ob, 0.3, 11)

# ── 포탄: 8~12.5초 동안 조선 배에서 일본 배로 ──
for k in range(18):
    for n in range(3):
        t0 = 8.0 + n * 1.4 + (k % 6) * 0.18
        t1 = t0 + 0.5
        ob, gd, fr = gp_object(f"포탄{k}_{n}", z=0.1)
        add_stroke(ob, fr, [(6 * U * math.cos(a / 8 * 6.283), 6 * U * math.sin(a / 8 * 6.283), 0) for a in range(8)], "포탄", width=30)
        tgt = (k * 3 + n * 5) % 20
        for f_, vis in ((1, True), (int(t0 * FPS), False), (int(t1 * FPS) + 1, True)):
            ob.hide_render = vis
            ob.keyframe_insert("hide_render", frame=f_)
        for t_ in (t0, t1):
            sx, sy, _ = kr_pos(k, t_)
            tx, ty, _ = jp_pos(tgt, t_)
            u = 0.0 if t_ == t0 else 1.0
            ob.location = (lerp(sx, tx, u) * U, -lerp(sy, ty, u) * U, 0.1)
            ob.keyframe_insert("location", frame=int(t_ * FPS))

# ── 카메라: 위에서 수직으로 (직교) ──
cam = bpy.data.objects.new("카메라", bpy.data.cameras.new("카메라"))
cam.data.type = "ORTHO"
cam.data.ortho_scale = 1920 * U
cam.location = (960 * U, -540 * U, 10)
sc.collection.objects.link(cam)
sc.camera = cam
os.makedirs(OUT, exist_ok=True)
sc.render.filepath = os.path.join(OUT, "f_")
sc.render.image_settings.file_format = "PNG"
if "--test" in argv:
    for f_ in (24, 120, 200, 260, 330):
        sc.frame_set(f_)
        sc.render.filepath = os.path.join(OUT, f"test_{f_:04d}.png")
        bpy.ops.render.render(write_still=True)
else:
    bpy.ops.render.render(animation=True)
