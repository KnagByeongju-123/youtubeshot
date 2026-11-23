"""실사풍 3D 배경: 뉴스 스튜디오 (블렌더 Cycles, 그래픽카드 없이)
   - 뒤: 휘어진 큰 화면에 도시 야경 (Poly Haven 'shanghai_bund' 사진, CC0)
   - 바닥: 광택 대리석 (Poly Haven 'marble_01', CC0) — 조명·화면이 비침
   - 앵커 책상: 흰 상판 + 남색 앞판 + 파란 빛줄(LED), 옆 벽: 남색 판 + 세로 빛줄
   - 조명: 방송 3점 조명(앞 왼쪽 주광·오른쪽 보조광·뒤 윤곽광) + 주변 반사용 HDRI
   사용: .bpy_venv/bin/python -I 실사3D/뉴스스튜디오.py <결과.png> [--인물 <사람.glb>] [--키 1.62] [--샘플 48]
                                                        [--카메라 정면|넓게|비스듬] [--영상 <프레임폴더> <장수>]
     --인물: GLB 사람을 책상 뒤 가운데에 세움 (키 --키 m 로 맞춤)
     --영상: 카메라가 천천히 다가가는 장면을 장수만큼 찍음 (24장 = 1초)
   자료 받기(처음 한 번): models/polyhaven/_studio/ 에 shanghai_bund.jpg·shanghai_bund_1k.hdr·marble_01_*.jpg (파일 아래 받기 함수)
   (사용자 결정 2026-11-23: 3D 배경 실사풍)"""
import math, os, sys
import bpy

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
A = os.path.join(ROOT, "models", "polyhaven", "_studio")
args = sys.argv[1:]
out = args[0]
opt = {"--인물": None, "--키": "1.62", "--샘플": "48", "--카메라": "정면"}
for k in list(opt):
    if k in args: opt[k] = args[args.index(k) + 1]
video = None
if "--영상" in args: i = args.index("--영상"); video = (args[i + 1], int(args[i + 2]))


def fetch():
    """Poly Haven 자료가 없으면 받기 (CC0, 프로그램 이름 없으면 403 이라 이름을 붙임)"""
    import json, urllib.request
    need = ["shanghai_bund.jpg", "shanghai_bund_1k.hdr", "marble_01_Diffuse.jpg", "marble_01_Rough.jpg", "marble_01_nor_gl.jpg"]
    if all(os.path.exists(os.path.join(A, n)) for n in need): return
    os.makedirs(A, exist_ok=True)
    o = urllib.request.build_opener(); o.addheaders = [("User-Agent", "asset-fetcher/1.0")]; urllib.request.install_opener(o)
    f = json.load(urllib.request.urlopen("https://api.polyhaven.com/files/shanghai_bund"))
    urllib.request.urlretrieve(f["tonemapped"]["url"], os.path.join(A, "shanghai_bund.jpg"))
    urllib.request.urlretrieve(f["hdri"]["1k"]["hdr"]["url"], os.path.join(A, "shanghai_bund_1k.hdr"))
    t = json.load(urllib.request.urlopen("https://api.polyhaven.com/files/marble_01"))
    for k in ("Diffuse", "Rough", "nor_gl"): urllib.request.urlretrieve(t[k]["1k"]["jpg"]["url"], os.path.join(A, f"marble_01_{k}.jpg"))


fetch()
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"; sc.cycles.samples = int(opt["--샘플"]); sc.cycles.use_denoising = True
sc.render.resolution_x, sc.render.resolution_y = 1280, 720
sc.view_settings.view_transform = "Standard"; sc.view_settings.look = "None"
sc.cycles.max_bounces = 6


def mat(name, color=(0.8, 0.8, 0.8), rough=0.4, metal=0.0, emit=None, strength=0.0, img=None, img_emit=False, uv_scale=None, rough_img=None, nor_img=None):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1); b.inputs["Roughness"].default_value = rough; b.inputs["Metallic"].default_value = metal
    def tex(path, non_color=False):
        t = nt.nodes.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(path)
        if non_color: t.image.colorspace_settings.name = "Non-Color"
        if uv_scale:
            mp = nt.nodes.new("ShaderNodeMapping"); tc = nt.nodes.new("ShaderNodeTexCoord")
            mp.inputs["Scale"].default_value = (uv_scale, uv_scale, 1); nt.links.new(tc.outputs["UV"], mp.inputs["Vector"]); nt.links.new(mp.outputs["Vector"], t.inputs["Vector"])
        return t
    if img:
        t = tex(img)
        if img_emit:
            nt.links.new(t.outputs["Color"], b.inputs["Emission Color"]); b.inputs["Emission Strength"].default_value = strength
            b.inputs["Base Color"].default_value = (0, 0, 0, 1)
        else: nt.links.new(t.outputs["Color"], b.inputs["Base Color"])
    if rough_img: nt.links.new(tex(rough_img, True).outputs["Color"], b.inputs["Roughness"])
    if nor_img:
        nm = nt.nodes.new("ShaderNodeNormalMap"); nm.inputs["Strength"].default_value = 0.3
        nt.links.new(tex(nor_img, True).outputs["Color"], nm.inputs["Color"]); nt.links.new(nm.outputs["Normal"], b.inputs["Normal"])
    if emit is not None:
        b.inputs["Emission Color"].default_value = (*emit, 1); b.inputs["Emission Strength"].default_value = strength
    return m


def box(name, loc, size, m, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(location=loc); o = bpy.context.object; o.name = name; o.scale = (size[0] / 2, size[1] / 2, size[2] / 2)
    bpy.ops.object.transform_apply(scale=True)
    if bevel:
        bv = o.modifiers.new("bevel", "BEVEL"); bv.width = bevel; bv.segments = 4
    o.data.materials.append(m); return o


# ── 바닥: 광택 대리석 (조금 어둡게 — 방송 스튜디오 바닥) ──
bpy.ops.mesh.primitive_plane_add(size=24, location=(0, 0, 0)); floor = bpy.context.object
floor.data.materials.append(mat("바닥", rough=0.06, img=os.path.join(A, "marble_01_Diffuse.jpg"), uv_scale=6,
                                rough_img=os.path.join(A, "marble_01_Rough.jpg"), nor_img=os.path.join(A, "marble_01_nor_gl.jpg")))
fb = floor.data.materials[0].node_tree.nodes["Principled BSDF"]
mix = floor.data.materials[0].node_tree.nodes.new("ShaderNodeMixRGB"); mix.blend_type = "MULTIPLY"; mix.inputs["Fac"].default_value = 1.0
mix.inputs["Color2"].default_value = (0.07, 0.08, 0.11, 1)      # 어두운 대리석
tex_n = [n for n in floor.data.materials[0].node_tree.nodes if n.type == "TEX_IMAGE" and "Diffuse" in n.image.name][0]
floor.data.materials[0].node_tree.links.new(tex_n.outputs["Color"], mix.inputs["Color1"]); floor.data.materials[0].node_tree.links.new(mix.outputs["Color"], fb.inputs["Base Color"])

# ── 뒤 휘어진 큰 화면: 도시 야경 ──
R, ANG, HGT, BACK = 7.0, math.radians(84), 3.6, 4.2
bpy.ops.mesh.primitive_cylinder_add(vertices=96, radius=R, depth=HGT, location=(0, BACK - R, HGT / 2 + 0.25)); cyl = bpy.context.object
me = cyl.data
import bmesh
bm = bmesh.new(); bm.from_mesh(me)
kill = [f for f in bm.faces if abs(math.atan2(f.calc_center_median().x, f.calc_center_median().y)) > ANG / 2 or abs(f.normal.z) > 0.5]
bmesh.ops.delete(bm, geom=kill, context="FACES")
uv = bm.loops.layers.uv.verify()          # 기본 uv 층에 씀 (새 층을 만들면 재질이 안 씀)
for f in bm.faces:
    for l in f.loops:
        a_ = math.atan2(l.vert.co.x, l.vert.co.y); l[uv].uv = (0.59 + a_ / ANG * 0.36, 0.595 + l.vert.co.z / HGT * 0.19)   # 사진의 푸둥 야경(가로 41~77%, 지평선이 화면 아래쪽)
bm.to_mesh(me); bm.free()
for p in me.polygons: p.use_smooth = True
screen = mat("화면", img=os.path.join(A, "shanghai_bund.jpg"), img_emit=True, strength=0.55, rough=0.7)
me.materials.append(screen)
# 화면 테두리(어두운 틀)
box("화면틀_위", (0, BACK + 0.05, HGT + 0.3), (11.5, 0.3, 0.12), mat("틀", (0.02, 0.025, 0.035), 0.35, 0.6))
box("화면틀_아래", (0, BACK + 0.05, 0.2), (11.5, 0.3, 0.4), mat("틀2", (0.02, 0.025, 0.035), 0.35, 0.6))

# ── 옆 벽: 남색 광택 판 + 세로 빛줄 ──
panel = mat("옆판", (0.02, 0.04, 0.1), 0.2, 0.3)
led = mat("빛줄", emit=(0.25, 0.6, 1.0), strength=8)
for sx in (-1, 1):
    for k_ in range(3):
        x_ = sx * (4.2 + k_ * 0.95); y_ = BACK - 1.0 - k_ * 1.1
        p = box(f"옆판{sx}{k_}", (x_, y_, 2.0), (1.0, 0.12, 4.0), panel, bevel=0.02)
        p.rotation_euler[2] = sx * math.radians(-35)
        l_ = box(f"빛줄{sx}{k_}", (x_ - sx * 0.52 * math.cos(math.radians(35)), y_ - 0.0, 2.0), (0.04, 0.14, 3.8), led)
        l_.rotation_euler[2] = sx * math.radians(-35)

# ── 앵커 책상 ──
top_m = mat("상판", (0.75, 0.77, 0.8), 0.1)
front_m = mat("앞판", (0.012, 0.025, 0.07), 0.15, 0.5)
DESK_Y, DESK_H = 0.9, 1.02
box("상판", (0, DESK_Y, DESK_H), (2.6, 0.85, 0.05), top_m, bevel=0.02)
box("앞판", (0, DESK_Y - 0.32, DESK_H / 2), (2.45, 0.08, DESK_H - 0.04), front_m, bevel=0.015)
box("옆판L", (-1.2, DESK_Y, DESK_H / 2), (0.08, 0.7, DESK_H - 0.04), front_m, bevel=0.015)
box("옆판R", (1.2, DESK_Y, DESK_H / 2), (0.08, 0.7, DESK_H - 0.04), front_m, bevel=0.015)
box("책상빛줄", (0, DESK_Y - 0.37, DESK_H - 0.14), (2.35, 0.02, 0.03), mat("책상빛", emit=(0.3, 0.65, 1.0), strength=6))
box("책상빛줄2", (0, DESK_Y - 0.37, 0.06), (2.35, 0.02, 0.02), mat("책상빛2", emit=(0.3, 0.65, 1.0), strength=4))
box("로고판", (0, DESK_Y - 0.37, DESK_H * 0.5), (0.7, 0.015, 0.16), mat("로고", (0.05, 0.1, 0.25), 0.2, emit=(0.35, 0.6, 1.0), strength=0.8))

# ── 사람 (GLB) ──
if opt["--인물"]:
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=os.path.abspath(opt["--인물"]))
    objs = [o for o in bpy.data.objects if o not in before]
    roots = [o for o in objs if o.parent is None]
    bpy.context.view_layer.update()
    pts = []
    for o in objs:
        if o.type == "MESH":
            for c in o.bound_box: pts.append(o.matrix_world @ __import__("mathutils").Vector(c))
    zmin = min(p.z for p in pts); zmax = max(p.z for p in pts)
    k = float(opt["--키"]) / (zmax - zmin)
    for r in roots:
        r.scale = (r.scale[0] * k, r.scale[1] * k, r.scale[2] * k)
    bpy.context.view_layer.update()
    pts = [o.matrix_world @ __import__("mathutils").Vector(c) for o in objs if o.type == "MESH" for c in o.bound_box]
    zmin = min(p.z for p in pts); cxp = (min(p.x for p in pts) + max(p.x for p in pts)) / 2; cyp = (min(p.y for p in pts) + max(p.y for p in pts)) / 2
    for r in roots: r.location.x -= cxp; r.location.y += (DESK_Y + 0.75) - cyp; r.location.z -= zmin
    print("인물:", len(objs), "개 물체, 키", opt["--키"], "m, 책상 뒤에 세움")

# ── 조명 ──
def area(name, loc, rot, power, size, color=(1, 1, 1)):
    bpy.ops.object.light_add(type="AREA", location=loc, rotation=rot); l = bpy.context.object; l.name = name
    l.data.energy = power; l.data.size = size; l.data.color = color; return l
area("주광", (-2.6, -2.6, 3.6), (math.radians(55), 0, math.radians(-40)), 380, 2.0, (1.0, 0.95, 0.88))
area("보조광", (2.8, -2.4, 2.6), (math.radians(65), 0, math.radians(45)), 150, 2.5, (0.92, 0.95, 1.0))
area("윤곽광", (0, 3.2, 3.8), (math.radians(-50), 0, 0), 300, 1.5, (0.8, 0.9, 1.0))
area("천장", (0, 0, 5.5), (0, 0, 0), 120, 6.0)
w = bpy.data.worlds.new("세상"); sc.world = w; w.use_nodes = True
env = w.node_tree.nodes.new("ShaderNodeTexEnvironment"); env.image = bpy.data.images.load(os.path.join(A, "shanghai_bund_1k.hdr"))
bg = w.node_tree.nodes["Background"]; bg.inputs["Strength"].default_value = 0.15
w.cycles_visibility.camera = False          # 바깥(도시 사진)은 카메라에 안 보이게 — 반사·은은한 빛에만 씀
try: pass
except Exception: pass
w.node_tree.links.new(env.outputs["Color"], bg.inputs["Color"])

# ── 카메라 ──
CAMS = {"정면": ((0, -4.6, 1.6), (0, 1.5, 1.35), 32), "넓게": ((0, -6.5, 2.1), (0, 1.8, 1.4), 24), "비스듬": ((-3.0, -4.2, 1.7), (0.3, 1.5, 1.3), 32)}
cp, tp, lens = CAMS[opt["--카메라"]]
bpy.ops.object.camera_add(location=cp); cam = bpy.context.object; sc.camera = cam; cam.data.lens = lens
import mathutils
def aim(c, t): d = mathutils.Vector(t) - c.location; c.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
aim(cam, tp)
if video is None:
    sc.render.filepath = os.path.abspath(out); bpy.ops.render.render(write_still=True); print("찍음:", out)
else:
    folder, n = video; os.makedirs(folder, exist_ok=True)
    c0 = mathutils.Vector(cp); c1 = mathutils.Vector(cp) + (mathutils.Vector(tp) - mathutils.Vector(cp)) * 0.18
    for i in range(n):
        s = i / max(1, n - 1); s = s * s * (3 - 2 * s)
        cam.location = c0.lerp(c1, s); aim(cam, tp)
        sc.render.filepath = os.path.join(os.path.abspath(folder), f"f{i:04d}.png"); bpy.ops.render.render(write_still=True)
    print("찍음:", n, "장 →", folder)
