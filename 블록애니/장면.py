"""블록 애니 장면 하나를 렌더링 (블렌더 안에서 실행)
xvfb-run -a blender -b -t 4 -P 블록애니/장면.py -- <장면목록.json> <번호> <길이초> <결과.mp4> [--미리보기]
  장면목록.json = [{place, time, level, holes, wall, pillar, dock, house, actors:[...], cam:{...}, fx:[...]}, ...]
  --미리보기 = 가운데 한 장만 png 로 (빠른 확인)
움직임은 모두 직접 계산(키프레임): 걷기·들고 걷기·앉기·말하기(고개·손짓)·고개 젓기·끄덕이기·쌓기·눈 깜빡임·숨쉬기, 카메라는 늘 움직임(풍경도 영화처럼, 사용자 결정 2026-11-06)
"""
import bpy, json, math, os, sys, random

HERE = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(HERE, "블록.py"), encoding="utf-8").read().split("if __name__")[0])

FPS = 24


def smooth(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def facing_to(dx, dy):
    return math.atan2(dx, -dy)


# ── 섬: 칸 목록 (언덕 꼭대기에서 먼 칸부터 무너짐) ──
HILL_TOP = (-2, 1)
HILL = {(-2, 1), (-3, 1), (-2, 2), (-1, 1), (-2, 0), (-3, 2), (-1, 2)}
HOUSE = [(x, y) for x in range(1, 4) for y in range(-1, 2)]
PATH = [(2, -2), (1, -2), (0, -2), (0, -3)]
RING = [(-4, 0), (-4, 1), (-4, 2), (-3, 3), (-2, 3), (-1, 3), (0, 2), (0, 1), (0, 0), (-1, -1), (-2, -1), (-3, -1), (-3, 0)]


def island_cells():
    cells = []
    for x in range(-6, 6):
        for y in range(-4, 5):
            if (x + 0.5) ** 2 / 30 + y * y / 14 < 1:
                cells.append((x, y))
    hx, hy = HILL_TOP

    def rank(c):    # 작을수록 오래 남음: 언덕 꼭대기 → 언덕 → 언덕 둘레 벽 → 집·길 → 나머지(먼 곳부터 무너짐)
        d = (c[0] - hx) ** 2 + (c[1] - hy) ** 2
        if c == HILL_TOP:
            return 0
        if c in HILL:
            return 1 + d * 0.01
        if c in RING:
            return 2 + d * 0.01
        if c in HOUSE or c in PATH:
            return 3 + d * 0.01
        return 4 + d
    cells.sort(key=rank)
    return cells          # 앞쪽 = 마지막까지 남음


CELLS = island_cells()


def build_island(sp, M):
    level = min(len(CELLS), int(sp.get("level", len(CELLS))))
    keep = set(CELLS[:level])
    for (x, y) in keep:
        top = 1 if (x, y) in HILL else 0
        if (x, y) == HILL_TOP:
            top = 2 if not sp.get("low") else 0
        for z in range(-2, top):
            m_ = M["grass"] if z == top - 1 else (M["dirt"] if z >= -1 else M["stone"])
            box(f"c{x}_{y}_{z}", (1, 1, 1), (x, y, z + 0.5), m_, tile=True)
    if sp.get("house", True):
        holes = int(sp.get("holes", 0))
        wall = []
        for x in range(1, 4):
            for y in range(-1, 2):
                if (x, y) not in keep:
                    continue
                if x in (1, 3) or y in (-1, 1):
                    for z in range(2):
                        if (x, y, z) == (2, -1, 0):
                            continue        # 문
                        wall.append((x, y, z))
        r = random.Random(7)
        order = wall[:]; r.shuffle(order)
        gone = set(order[:holes])
        for (x, y, z) in wall:
            if (x, y, z) not in gone:
                box(f"w{x}_{y}_{z}", (1, 1, 1), (x, y, z + 0.5), M["wood"], tile=True)
        if all(c in keep for c in HOUSE):
            for x in range(1, 4):
                for y in range(-1, 2):
                    if holes < 14 or (x + y) % 2:
                        box(f"r{x}_{y}", (1, 1, 1), (x, y, 2.5), M["roof"], tile=True)
        if (2, -1) in keep:
            box("door", (0.8, 0.1, 1.6), (2, -1.45, 0.8), M["door"])
    if sp.get("wall"):
        for (x, y) in RING:
            if (x, y) in keep:
                box(f"sw{x}_{y}", (1, 1, 1), (x, y, 0.5 if (x, y) not in HILL else 1.5), M["stone2"], tile=True)
    if sp.get("pillar", True) and HILL_TOP in keep:
        px, py = HILL_TOP[0] + 0.0, HILL_TOP[1] + 0.0
        gz = 0 if sp.get("low") else 2
        pil = box("pillar", (0.45, 0.45, 2.2), (px + 0.2, py - 0.1, gz + 1.1), M["post"])
        marks = sp.get("marks", 15)
        for i in range(marks):
            col = M["mk%d" % (i % 4)]
            box(f"mark{i}", (0.26, 0.03, 0.03), (px + 0.2, py - 0.34, gz + 0.75 + i * 0.065), col)
        if not sp.get("low"):
            box("grave", (0.6, 0.4, 0.8), (px - 0.6, py + 0.3, gz + 0.4), M["stone"])
    if sp.get("dock", True):
        for i in range(4):
            y = -4 - i
            box(f"dock{i}", (1, 1, 0.2), (0, y, -0.1), M["plank"], tile=True)
    box("sea", (300, 300, 1), (0, 0, -0.62), M["sea"], tile=True)
    return keep


def build_office(M):
    for x in range(-5, 6):
        for y in range(-4, 4):
            box(f"f{x}{y}", (1, 1, 1), (x, y, -0.5), M["tile"], tile=True)
    for x in range(-5, 6):
        for z in range(4):
            m_ = M["glass"] if 1 <= z <= 2 and abs(x) < 4 else M["wallw"]
            box(f"bw{x}{z}", (1, 1, 1), (x, 4, z + 0.5), m_, tile=True)
    for z in range(4):
        for y in range(-4, 4):
            box(f"lw{y}{z}", (1, 1, 1), (-6, y, z + 0.5), M["wallw"], tile=True)
    box("table", (5, 2, 0.2), (0, 0.5, 0.75), M["wood"])
    for sx in (-2, 2):
        box(f"tl{sx}", (0.2, 0.2, 0.75), (sx, 0.5, 0.37), M["wood"])
    for i, x in enumerate((-1.5, 0, 1.5)):
        box(f"ch{i}", (0.7, 0.7, 0.45), (x, 2.0, 0.22), M["chair"])
    box("screen", (2.6, 0.1, 1.5), (0, 3.85, 1.8), M["screen"])
    for i in range(6):          # 창밖 빌딩
        box(f"cb{i}", (1.5, 1, 3 + i % 3 * 2), (-4 + i * 1.6, 9, (3 + i % 3 * 2) / 2 - 1), M["bld%d" % (i % 3)], tile=True)


def build_city(M, sp):
    for x in range(-3, 4):
        for y in range(-2, 2):
            box(f"bf{x}{y}", (1, 1, 1), (x, y, -0.5), M["tile"], tile=True)
    for x in range(-3, 4):
        box(f"rail{x}", (1, 0.15, 0.15), (x, -1.9, 1.0), M["rail"])
        box(f"post{x}", (0.12, 0.12, 1.0), (x - 0.45, -1.9, 0.5), M["rail"])
    for x in range(-3, 4):
        for z in range(4):
            box(f"aw{x}{z}", (1, 1, 1), (x, 2, z + 0.5), M["wallw"] if not (z in (1, 2) and x in (-1, 0)) else M["glass"], tile=True)
    r = random.Random(3)
    for i in range(22):
        h = r.randint(4, 14)
        x = r.uniform(-30, 30); y = r.uniform(-40, -12)
        box(f"cbl{i}", (r.choice((2, 3, 4)), r.choice((2, 3)), h), (x, y, h / 2 - 8), M["bld%d" % (i % 3)], tile=True)
    px, py = sp.get("pillar_at", (1.6, 0.8))
    box("pillar", (0.45, 0.45, 2.2), (px, py, 1.1), M["post"])
    for i in range(sp.get("marks", 15)):
        box(f"mark{i}", (0.26, 0.03, 0.03), (px, py - 0.24, 0.75 + i * 0.065), M["mk%d" % (i % 4)])
    if sp.get("newmark"):
        box("newmark", (0.30, 0.04, 0.045), (px, py - 0.245, 1.82), M["mkred"])
    box("pot", (0.6, 0.6, 0.5), (-2.2, 1.0, 0.25), M["pot"])
    box("plant", (0.5, 0.5, 0.6), (-2.2, 1.0, 0.8), M["leaf"])


def build_boat(name, M, loc, rot=0.0, parent=None):
    root = empty(name, loc, parent)
    root.rotation_euler = (0, 0, rot)
    box(name + "_b", (1.4, 3.0, 0.3), (0, 0, 0.15), M["plank"], root)
    for sx in (-0.65, 0.65):
        box(name + f"_s{sx}", (0.15, 3.0, 0.5), (sx, 0, 0.45), M["wood"], root)
    for sy in (-1.45, 1.45):
        box(name + f"_e{sy}", (1.4, 0.15, 0.5), (0, sy, 0.45), M["wood"], root)
    return root


def materials():
    M = {}
    M["grass"] = mat("grass", (0.36, 0.62, 0.25), var=0.12)
    M["dirt"] = mat("dirt", (0.52, 0.36, 0.22), var=0.12)
    M["stone"] = mat("stone", (0.55, 0.55, 0.55), var=0.10)
    M["stone2"] = mat("stone2", (0.62, 0.60, 0.56), var=0.14)
    M["sea"] = mat("sea", (0.10, 0.38, 0.62), rough=0.25, var=0.06, edge=0.92)
    M["wood"] = mat("wood", (0.55, 0.38, 0.22), var=0.15)
    M["plank"] = mat("plank", (0.62, 0.46, 0.28), var=0.12)
    M["roof"] = mat("roof", (0.65, 0.22, 0.18), var=0.10)
    M["door"] = mat("door", (0.35, 0.22, 0.12), var=0.08)
    M["post"] = mat("post", (0.70, 0.55, 0.35), var=0.10)
    for i, c in enumerate(((0.85, 0.25, 0.2), (0.25, 0.45, 0.85), (0.95, 0.8, 0.2), (0.3, 0.7, 0.35))):
        M["mk%d" % i] = mat("mk%d" % i, c, tex=False)
    M["mkred"] = mat("mkred", (0.95, 0.15, 0.15), tex=False, emit=0.6)
    M["tile"] = mat("tile", (0.72, 0.72, 0.70), var=0.05)
    M["wallw"] = mat("wallw", (0.86, 0.84, 0.80), var=0.05)
    M["glass"] = mat("glass", (0.55, 0.75, 0.90), rough=0.1, var=0.03, edge=0.6)
    M["chair"] = mat("chair", (0.25, 0.27, 0.32), var=0.06)
    M["screen"] = mat("screen", (0.15, 0.2, 0.3), tex=False, emit=0.4)
    for i, c in enumerate(((0.55, 0.58, 0.62), (0.70, 0.66, 0.60), (0.45, 0.50, 0.58))):
        M["bld%d" % i] = mat("bld%d" % i, c, var=0.08)
    M["rail"] = mat("rail", (0.3, 0.3, 0.32), tex=False)
    M["pot"] = mat("pot", (0.7, 0.4, 0.25), var=0.08)
    M["leaf"] = mat("leaf", (0.25, 0.55, 0.25), var=0.15)
    M["block"] = mat("block_c", (0.55, 0.38, 0.22), var=0.15)
    M["foam"] = mat("foam", (0.95, 0.97, 1.0), tex=False)
    M["phone"] = mat("phone", (0.08, 0.08, 0.1), tex=False)
    M["moon"] = mat("moon", (1.0, 0.97, 0.85), tex=False, emit=4.0)
    M["bowl"] = mat("bowl", (0.92, 0.90, 0.85), tex=False)
    M["light"] = mat("lamp", (1.0, 0.8, 0.45), tex=False, emit=3.0)
    return M


TIMES = {   # 해 색·세기, 하늘(위), 지평선, 하늘 밝기, 해 높이(도)
    "day": ((1.0, 0.94, 0.84), 3.0, (0.22, 0.50, 0.88), (0.86, 0.88, 0.85), 1.0, 50),
    "sunset": ((1.0, 0.62, 0.38), 2.6, (0.30, 0.32, 0.62), (0.98, 0.62, 0.40), 0.9, 12),
    "night": ((0.55, 0.65, 1.0), 0.55, (0.02, 0.03, 0.10), (0.08, 0.10, 0.22), 0.6, 40),
    "overcast": ((0.85, 0.88, 0.95), 1.2, (0.45, 0.50, 0.58), (0.70, 0.72, 0.74), 0.9, 60),
    "morning": ((1.0, 0.86, 0.70), 2.6, (0.40, 0.60, 0.90), (0.95, 0.85, 0.75), 1.0, 25),
    "indoor": ((1.0, 0.96, 0.90), 2.4, (0.75, 0.82, 0.90), (0.90, 0.90, 0.88), 1.0, 55),
}


class Actor:
    def __init__(self, P, spec):
        self.P, self.sp = P, spec
        self.k = P["k"]

    def blink_eyes(self, f):
        pass


def animate_actor(P, a, n, keep_z):
    """a = {who,pos,face,act,to,speed,start,carry,sit,...}; 프레임마다 위치·회전 키프레임"""
    root, torso, head, neck = P["root"], P["torso"], P["head"], P["neck"]
    arms, legs = P["arms"], P["legs"]
    x0, y0 = a["pos"]
    z0 = a.get("z", keep_z(x0, y0))
    face = a.get("face", 0)
    if isinstance(face, (list, tuple)):
        face = facing_to(face[0] - x0, face[1] - y0)
    else:
        face = math.radians(face)
    act = a.get("act", "idle")
    to = a.get("to")
    start = a.get("start", 0.0)
    dur_walk = None
    if to:
        dist = math.hypot(to[0] - x0, to[1] - y0)
        dur_walk = dist / a.get("speed", 0.9)
        wface = facing_to(to[0] - x0, to[1] - y0)
    carry = a.get("carry", False)
    blk = None
    if carry == "pillar":
        blk = box(a["who"] + "_carry", (0.40, 0.40, 1.8), (0, -0.45, 0.35), bpy.data.materials["post"], torso)
    elif carry:
        blk = box(a["who"] + "_carry", (0.55, 0.55, 0.55), (0, -0.42, 0.25), bpy.data.materials["block_c"], torso)
    if a.get("phone"):
        box(a["who"] + "_phone", (0.08, 0.04, 0.16), (0, -0.1, -0.5), bpy.data.materials["phone"], arms["R"])
    seed = hash(a["who"]) & 0xff
    for f in range(1, n + 1):
        t = (f - 1) / FPS
        x, y, z, rz = x0, y0, z0, face
        walking = False
        if to and t >= start:
            q = min(1.0, (t - start) / max(0.01, dur_walk))
            x = x0 + (to[0] - x0) * q; y = y0 + (to[1] - y0) * q
            z = z0 + (a.get("to_z", keep_z(to[0], to[1])) - z0) * smooth(q) if keep_z else z0
            walking = q < 1.0
            if walking:
                rz = wface
            else:
                tf = a.get("end_face")
                rz = (facing_to(tf[0] - to[0], tf[1] - to[1]) if isinstance(tf, (list, tuple)) else math.radians(tf)) if tf is not None else wface
        ph = math.sin(t * 2 * math.pi * 1.1)
        la = ra = ll = rl = 0.0
        hx = hz = hy = 0.0
        bend = math.radians(CAST[a["who"]]["bend"])
        breathe = 1 + 0.012 * math.sin(t * 2 * math.pi / 3.2 + seed)
        if walking:
            ll, rl = -28 * ph, 28 * ph
            la, ra = 30 * ph, -30 * ph
            z += 0.04 * abs(ph)
        if carry:
            la = ra = -75
        if act == "talk":
            hx = 4 * math.sin(t * 2 * math.pi * 0.9)
            ra = -25 - 15 * (0.5 + 0.5 * math.sin(t * 2 * math.pi * 0.45))
        elif act == "shake":
            hz = 18 * math.sin(t * 2 * math.pi * 0.8) * smooth(t / 0.6)
        elif act == "nod":
            hx = 10 * max(0, math.sin(t * 2 * math.pi * 0.7))
        elif act == "look_down":
            hx = 18
        elif act == "look_up":
            hx = -15
        elif act == "angry":
            la = ra = -20 - 25 * abs(math.sin(t * 2 * math.pi * 0.9))
            hx = -5 * math.sin(t * 2 * math.pi * 1.4)
        elif act == "stack":
            cyc = (t * 0.5) % 1.0
            bend += math.radians(35 * math.sin(math.pi * cyc))
            la = ra = -40 - 40 * math.sin(math.pi * cyc)
        elif act == "laugh":
            hx = -10 - 6 * abs(math.sin(t * 2 * math.pi * 2.0))
        elif act == "reach":
            ra = -85 * smooth((t - a.get("reach_at", 0.5)) / 0.8)
            hx = -8
        elif act == "hand_back":
            ra = -60 * smooth(t / 1.2)
        elif act == "phone":
            ra = -130; hx = 6
        elif act == "lift":     # 기둥을 두 손으로 뽑아 들기
            la = ra = -70 * smooth(t / 1.0)
            bend += math.radians(20 * (1 - smooth(t / 1.5)))
        if a.get("sit"):
            ll = rl = -90
            z -= 0.62 * P["k"]
            la = ra = la if (act in ("stack", "talk", "phone", "reach")) else -35
        hz += a.get("head_turn", 0)
        root.location = (x, y, z); root.rotation_euler = (0, 0, rz)
        root.keyframe_insert("location", frame=f); root.keyframe_insert("rotation_euler", frame=f)
        torso.rotation_euler = (bend, 0, 0); torso.scale = (1, 1, breathe)
        torso.keyframe_insert("rotation_euler", frame=f); torso.keyframe_insert("scale", frame=f)
        head.rotation_euler = (math.radians(hx), math.radians(hy), math.radians(hz)); head.keyframe_insert("rotation_euler", frame=f)
        arms["L"].rotation_euler = (math.radians(la), 0, 0); arms["R"].rotation_euler = (math.radians(ra), 0, 0)
        legs["L"].rotation_euler = (math.radians(ll), 0, 0); legs["R"].rotation_euler = (math.radians(rl), 0, 0)
        for o in (arms["L"], arms["R"], legs["L"], legs["R"]):
            o.keyframe_insert("rotation_euler", frame=f)
    # 눈 깜빡임 (3~5초마다)
    face_o = bpy.data.objects.get(a["who"] + "_face")
    if face_o:
        r = random.Random(seed)
        t = r.uniform(1.0, 3.0)
        face_o.scale = (1, 1, 1); face_o.keyframe_insert("scale", frame=1)
    for o in root.children_recursive:
        if o.animation_data and o.animation_data.action:
            for fc in o.animation_data.action.fcurves:
                for kp in fc.keyframe_points:
                    kp.interpolation = "LINEAR"


def blink(who, n):
    eyes = [o for o in bpy.data.objects if o.name.startswith(who + "_e") and not o.name.startswith(who + "_ew")]
    r = random.Random(hash(who) & 0xffff)
    t = r.uniform(0.8, 2.5)
    for o in eyes:
        o.scale = (1, 1, 1); o.keyframe_insert("scale", frame=1)
    while t * FPS < n:
        f = int(t * FPS)
        for o in eyes:
            o.scale = (1, 1, 1); o.keyframe_insert("scale", frame=f)
            o.scale = (1, 1, 0.1); o.keyframe_insert("scale", frame=f + 2)
            o.scale = (1, 1, 1); o.keyframe_insert("scale", frame=f + 4)
        t += r.uniform(2.8, 5.0)


def camera_move(scn, c, n):
    cam, tgt = camera(scn, tuple(c["from"]), tuple(c.get("target", (0, 0, 1))), lens=c.get("lens", 35))
    typ = c.get("type", "dolly")
    fr, to = c["from"], c.get("to", c["from"])
    tg0, tg1 = c.get("target", (0, 0, 1)), c.get("target_to", c.get("target", (0, 0, 1)))
    for f in range(1, n + 1):
        q = smooth((f - 1) / max(1, n - 1)) if typ != "orbit" else (f - 1) / max(1, n - 1)
        if typ == "orbit":
            cx, cy = tg0[0], tg0[1]
            r0 = math.hypot(fr[0] - cx, fr[1] - cy)
            a0 = math.atan2(fr[1] - cy, fr[0] - cx)
            ang = a0 + math.radians(c.get("deg", 30)) * q
            loc = (cx + r0 * math.cos(ang), cy + r0 * math.sin(ang), fr[2] + (to[2] - fr[2]) * q)
        else:
            loc = tuple(fr[i] + (to[i] - fr[i]) * q for i in range(3))
        cam.location = loc; cam.keyframe_insert("location", frame=f)
        tgt.location = tuple(tg0[i] + (tg1[i] - tg0[i]) * q for i in range(3)); tgt.keyframe_insert("location", frame=f)
    return cam


def fx_fall(M, cell, n, t0=0.5):
    x, y = cell
    o = box("fall", (1, 1, 1), (x, y, -0.5), M["grass"], tile=False)
    foams = []
    for f in range(1, n + 1):
        t = (f - 1) / FPS - t0
        if t < 0:
            o.location = (x, y, -0.5); o.rotation_euler = (0, 0, 0)
        else:
            tilt = min(1.0, t / 0.8)
            o.rotation_euler = (math.radians(-35 * tilt), 0, 0)
            o.location = (x, y - 0.3 * tilt, -0.5 - 4.9 * max(0, t - 0.5) ** 2)
        o.keyframe_insert("location", frame=f); o.keyframe_insert("rotation_euler", frame=f)
    r = random.Random(2)
    for i in range(14):
        fo = box(f"foam{i}", (0.18, 0.18, 0.18), (x, y - 0.4, -0.1), M["foam"])
        vx, vy, vz = r.uniform(-1.2, 1.2), r.uniform(-1.2, 0.4), r.uniform(2.0, 3.5)
        for f in range(1, n + 1):
            t = (f - 1) / FPS - t0 - 1.0
            if t < 0:
                fo.location = (x, y - 0.4, -2.0)
            else:
                fo.location = (x + vx * t, y - 0.4 + vy * t, -0.1 + vz * t - 4.9 * t * t)
                if fo.location.z < -0.4:
                    fo.location = (fo.location.x, fo.location.y, -2.0)
            fo.keyframe_insert("location", frame=f)


def render_scene(spec_all, idx, dur, out, preview=False):
    sp = spec_all[idx]
    scn = bpy.context.scene
    clear()
    M = materials()
    n = max(2, int(round(dur * FPS)))
    place = sp.get("place", "island")
    keep = set()
    if place == "island":
        keep = build_island(sp, M)
    elif place == "office":
        build_office(M)
    elif place == "city":
        build_city(M, sp)
    elif place == "sea":
        box("sea", (300, 300, 1), (0, 0, -0.62), M["sea"], tile=True)
        if sp.get("island_far"):
            sp2 = dict(sp); sp2["level"] = sp.get("level", 40)
            # 먼 섬: 원점 기준 그대로, 배는 먼 곳에
            build_island(dict(sp2, dock=True), M)

    def keep_z(x, y):
        c = (int(round(x)), int(round(y)))
        if place != "island":
            return 0.0
        if c == HILL_TOP:
            return 0.0 if sp.get("low") else 2.0
        return 1.0 if c in HILL else 0.0
    # 움직이지 않는 블록 한 덩어리로 (CPU 빠르게)
    stat = [o for o in scn.objects if o.type == "MESH" and o.parent is None]
    if len(stat) > 1:
        bpy.ops.object.select_all(action="DESELECT")
        for o in stat:
            o.select_set(True)
        bpy.context.view_layer.objects.active = stat[0]
        bpy.ops.object.join()
    # 배
    for bspec in sp.get("boats", []):
        b = build_boat("boat", M, tuple(bspec["pos"]) + (-0.25,), math.radians(bspec.get("rot", 0)))
        bto = bspec.get("to")
        for f in range(1, n + 1):
            t = (f - 1) / FPS
            q = smooth(t / dur) if bto else 0
            p0 = bspec["pos"]
            loc = (p0[0] + ((bto[0] - p0[0]) * q if bto else 0), p0[1] + ((bto[1] - p0[1]) * q if bto else 0), -0.25 + 0.05 * math.sin(t * 2.2))
            b.location = loc; b.rotation_euler = (math.radians(2 * math.sin(t * 1.7)), 0, math.radians(bspec.get("rot", 0)))
            b.keyframe_insert("location", frame=f); b.keyframe_insert("rotation_euler", frame=f)
        for who in bspec.get("riders", []):
            P = make_person(who, (0, 0, 0))
            P["root"].parent = b
            P["root"].location = (0.0, -0.6 if who == "서연" else 0.6, 0.3)
            P["root"].rotation_euler = (0, 0, math.radians(180 if who == "만수" else 0) if not bspec.get("same_face") else 0)
            for s_ in ("L", "R"):
                P["legs"][s_].rotation_euler = (math.radians(-90), 0, 0)
            P["root"].location.z = 0.3 - 0.62 * P["k"] + 0.3
            if bspec.get("pillar"):
                pass
            blink(who, n)
        if bspec.get("pillar"):
            box("bpillar", (0.45, 2.2, 0.45), (0.3, 0.0, 0.5), M["post"], b)
    for a in sp.get("actors", []):
        P = make_person(a["who"], (0, 0, 0))
        animate_actor(P, a, n, keep_z)
        blink(a["who"], n)
    if "fall" in sp.get("fx", []):
        edge = sp.get("fall_cell") or (CELLS[min(len(CELLS), sp.get("level", len(CELLS))) - 1] if place == "island" else (4, -2))
        fx_fall(M, edge, n, sp.get("fall_at", 0.6))
    if "sink" in sp.get("fx", []):
        o = bpy.data.objects.get("pillar")
        last = box("lastcell", (1, 1, 1), (HILL_TOP[0], HILL_TOP[1], 1.5), M["grass"], tile=True)
        for f in range(1, n + 1):
            t = (f - 1) / FPS
            last.location = (HILL_TOP[0], HILL_TOP[1], 1.5 - 3.5 * smooth((t - dur * 0.35) / (dur * 0.5)))
            last.keyframe_insert("location", frame=f)
    tm = TIMES[sp.get("time", "day")]
    sun = look(scn, sun_rgb=tm[0], sun_e=tm[1], sky=tm[2], horizon=tm[3], sky_e=tm[4])
    sun.rotation_euler = (math.radians(90 - tm[5]), 0, math.radians(sp.get("sun_az", 35)))
    if sp.get("time") == "night":
        mo = box("moonb", (3, 3, 3), (-40, 60, 30), M["moon"])
        if place == "island" and sp.get("window_light", True) and sp.get("house", True):
            lamp = bpy.data.objects.new("lamp", bpy.data.lights.new("lamp", "POINT"))
            scn.collection.objects.link(lamp); lamp.location = (2, 0, 1.2); lamp.data.energy = 120; lamp.data.color = (1, 0.75, 0.45)
    camera_move(scn, sp["cam"], n)
    r = scn.render
    r.engine = "BLENDER_EEVEE"; r.fps = FPS
    r.resolution_x, r.resolution_y = (1280, 720)
    scn.eevee.taa_render_samples = 8; scn.eevee.shadow_cube_size = "512"; scn.eevee.shadow_cascade_size = "1024"
    scn.frame_start = 1; scn.frame_end = n
    if preview:
        scn.frame_set(max(1, n // 2))
        r.image_settings.file_format = "PNG"; r.filepath = out
        bpy.ops.render.render(write_still=True)
        return
    r.image_settings.file_format = "FFMPEG"; r.ffmpeg.format = "MPEG4"; r.ffmpeg.codec = "H264"
    r.ffmpeg.constant_rate_factor = "HIGH"; r.ffmpeg.audio_codec = "NONE"
    r.filepath = out
    bpy.ops.render.render(animation=True)


if __name__ == "__main__" and "--" in sys.argv:
    a = sys.argv[sys.argv.index("--") + 1:]
    spec_all = json.load(open(a[0], encoding="utf-8"))
    render_scene(spec_all, int(a[1]), float(a[2]), a[3], preview="--미리보기" in a)
