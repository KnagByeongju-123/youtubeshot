r"""사진 한 장 → Blender 진짜 3D 카메라 움직임 영상 (사용자 결정 2026-11-08: '블렌더 활용', '새로운 카메라 무빙 규칙 참조', '작은 화질')
깊이 AI(depth_worker.py, Depth Anything V2)로 만든 깊이 지도대로 사진을 입체 판으로 세우고,
Blender 카메라가 움직이며 찍어 앞뒤가 다른 속도로 움직이는(시차) 영상을 만든다.

사용 (Blender 안에서 실행):
  blender -b -noaudio --factory-startup -P 블렌더_사진3D.py -- <사진> <깊이.npy> <결과.mp4> [초=8] [가로=960] [세로=540] [움직임=right] [세기=1.0]
움직임 (장문다큐.md 7장 카메라 규칙과 같은 이름, 사진 한 장 입체 판에 맞게 폭을 줄임):
  right·left = 옆으로 흐르며 살짝 다가감 / push = 가장 가까운 대상(깊이 최대 자리)을 향해 곧장 파고듦(갈수록 빨라짐)
  orbit = 그 대상을 중심으로 좌우로 돌기 / zoomout = 대상에 바짝 붙었다가 뒤로 빠지며 전체 / drone = 위에서 내려다보며 앞으로 날기
  fpv = 1인칭 드론(좌우로 기울고 잘게 흔들리며 빠르게 파고듦) / freeze = 멈춘 사진 속 순간이동(4자리, 자리마다 살짝 흐름)
- 화면이 판 밖(빈 곳)을 보지 않게 프레임마다 검사해 넘으면 렌즈를 당겨(확대) 막음
- 작은 화질(기본 960×540) Workbench·FXAA → 사진 색 그대로, 그래픽카드 없이 빠름. 영상 프로그램이 1920×1080 으로 키워 씀
- 결과는 고정 길이 영상: 프로그램이 장면 길이에 맞춰 시간 비율로 프레임을 골라 씀
"""
import os
import sys
import math
import numpy as np
import bpy
from mathutils import Vector, Euler

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
img_path, depth_path, out_path = argv[0], argv[1], argv[2]
SEC = float(argv[3]) if len(argv) > 3 else 8.0
W = int(argv[4]) if len(argv) > 4 else 960
H = int(argv[5]) if len(argv) > 5 else 540
MOVE = argv[6] if len(argv) > 6 else "right"
if MOVE.isdigit():                                   # 예전 번호 방식 호환
    MOVE = ["right", "left", "drone", "zoomout"][int(MOVE) % 4]
AMT = float(argv[7]) if len(argv) > 7 and not argv[7].startswith("--") else 1.0
def _opt(name):
    return argv[argv.index(name) + 1] if name in argv else ""
FG, BG, MASK = _opt("--fg"), _opt("--bg"), _opt("--mask")      # 사진_앞층.py 가 오려 낸 앞층·메운 배경 (없으면 깊이 판 하나)
FOCUS = [float(x) for x in _opt("--focus").split(",")] if _opt("--focus") else None   # 꼭 보여야 하는 곳 [x0,y0,x1,y1] 0~1 (사진_초점.py·Claude)
LAYERED = bool(FG and BG and MASK and os.path.exists(FG) and os.path.exists(BG))
FPS = 24
AA = os.environ.get("BL_AA", "FXAA")

bpy.ops.wm.read_factory_settings(use_empty=True)
scn = bpy.context.scene

# ── 사진·깊이 ──
img = bpy.data.images.load(BG if LAYERED else img_path)
iw, ih = img.size
aspect_img = iw / ih
d = np.load(depth_path).astype(np.float32)
d = (d - d.min()) / max(1e-6, float(d.max() - d.min()))
for _ in range(3):                                   # 깊이를 부드럽게 (경계가 고무처럼 늘어나는 것을 줄임)
    p = np.pad(d, 2, mode="edge")
    d = sum(p[i:i + d.shape[0], j:j + d.shape[1]] for i in range(5) for j in range(5)) / 25.0
dh, dw = d.shape
if LAYERED:                                          # 배경 판의 깊이에서 앞층 자리는 둘레 깊이로 메움 (앞층은 따로 세움)
    from PIL import Image as _PI
    mk = np.asarray(_PI.open(MASK).convert("L").resize((dw, dh)), np.float32) / 255.0
    hole = mk > 0.05
    if hole.any() and (~hole).any():
        ring = np.zeros_like(hole)                       # 앞층 바로 둘레의 깊이
        for dy_ in (-4, 0, 4):
            for dx_ in (-4, 0, 4):
                ring |= np.roll(np.roll(hole, dy_, 0), dx_, 1)
        ring &= ~hole
        fillv = float(np.median(d[ring])) if ring.any() else float(np.median(d[~hole]))
        d = np.where(hole, fillv, d)
        for _ in range(4):
            p = np.pad(d, 3, mode="edge")
            d = sum(p[i:i + dh, j:j + dw] for i in range(7) for j in range(7)) / 49.0

# 주인공 자리 = 가까운 곳(깊이 상위 8%)의 가운데, 가장자리 쪽이면 안으로 당김
thr = np.quantile(d, 0.92)
ys, xs = np.nonzero(d >= thr)
PU = float(np.clip(xs.mean() / dw if len(xs) else 0.5, 0.3, 0.7))
PV = float(np.clip(ys.mean() / dh if len(ys) else 0.5, 0.3, 0.7))

# ── 판(그리드): 너비 2, 높이 2/aspect ──
PW, PH = 2.0, 2.0 / aspect_img
nx = 240
ny = max(8, int(round(nx / aspect_img)))
bpy.ops.mesh.primitive_grid_add(x_subdivisions=nx, y_subdivisions=ny, size=1.0, calc_uvs=True)
ob = bpy.context.active_object
me = ob.data
DEPTH_AMP = 0.10 * AMT * PW
uv = me.uv_layers.active.data
vuv = {}
for poly in me.polygons:
    for li in poly.loop_indices:
        vuv[me.loops[li].vertex_index] = uv[li].uv[:]
for v in me.vertices:
    u, w = vuv.get(v.index, (0.5, 0.5))
    x = min(dw - 1, max(0, int(u * (dw - 1))))
    y = min(dh - 1, max(0, int((1 - w) * (dh - 1))))
    v.co.x = (u - 0.5) * PW
    v.co.y = (w - 0.5) * PH
    v.co.z = float(d[y, x]) * DEPTH_AMP

mat = bpy.data.materials.new("photo")
mat.use_nodes = True
nt = mat.node_tree
tex = nt.nodes.new("ShaderNodeTexImage")
tex.image = img
tex.extension = "EXTEND"
nt.links.new(tex.outputs["Color"], nt.nodes.get("Principled BSDF").inputs["Base Color"])
me.materials.append(mat)

# ── 카메라 ──
aspect_out = W / H
cd = bpy.data.cameras.new("cam")
cd.sensor_fit = "HORIZONTAL"
cd.sensor_width = 36
BASE_LENS = 50.0
cam = bpy.data.objects.new("cam", cd)
scn.collection.objects.link(cam)
scn.camera = cam
fit_w = min(PW, PH * aspect_out)                     # 판을 화면에 '꽉 차게'(cover) 볼 때의 가로 폭
D0 = (fit_w * 0.90 / 2) / (cd.sensor_width / 2 / BASE_LENS)   # 10% 여유를 둔 기본 거리
VW, VH = fit_w * 0.90, fit_w * 0.90 / aspect_out
TX, TY = (PU - 0.5) * PW, (0.5 - PV) * PH            # 주인공 자리 (판 좌표)
if FOCUS:                                            # 사진 밖(빈 곳)을 보여 줄 수는 없으니, 상자는 '꽉 차게 볼 수 있는 범위' 안으로 줄임
    hx_, hy_ = (fit_w / PW) / 2 * 0.97, (fit_w / aspect_out / PH) / 2 * 0.97
    FOCUS = [max(FOCUS[0], 0.5 - hx_), max(FOCUS[1], 0.5 - hy_), min(FOCUS[2], 0.5 + hx_), min(FOCUS[3], 0.5 + hy_)]
if FOCUS:                                            # 주인공 자리 = 꼭 보여야 하는 곳의 가운데
    PU, PV = (FOCUS[0] + FOCUS[2]) / 2, (FOCUS[1] + FOCUS[3]) / 2
    TX, TY = (PU - 0.5) * PW, (0.5 - PV) * PH
TZ = float(d[int(PV * (dh - 1)), int(PU * (dw - 1))]) * DEPTH_AMP
A = AMT


def ease(t):
    return 0.5 - 0.5 * math.cos(math.pi * t)


def look(loc, tgt, roll=0.0):
    dx, dy, dz = tgt[0] - loc[0], tgt[1] - loc[1], loc[2] - tgt[2]
    return Euler((math.atan2(dy, dz), -math.atan2(dx, math.hypot(dy, dz)), roll), "XYZ")


def pose(t):
    """t 0~1 → (위치, 바라보는 점, 기울기, 렌즈 배율)"""
    e = ease(t)
    if MOVE in ("right", "left"):
        s = (1 if MOVE == "right" else -1) * VW * 0.06 * A
        return (-s + 2 * s * e, VH * 0.02 * (1 - 2 * e), D0 * (1 - 0.10 * e)), (-s * 0.6 + 1.2 * s * 0.6 * e, 0, 0), 0.0, 1.0
    if MOVE == "push":                               # 갈수록 빨라지며 주인공 쪽으로 파고듦
        q = t * t
        return (TX * 0.8 * q, TY * 0.8 * q, D0 * (1 - 0.45 * q * A)), (TX * q, TY * q, TZ * q), 0.0, 1.0
    if MOVE == "orbit":
        ang = math.radians((-10 + 20 * e) * A)
        r_ = D0 * 0.85
        return ((TX * 0.5) + r_ * math.sin(ang), TY * 0.5 + VH * 0.02 * math.sin(math.pi * t), TZ + r_ * math.cos(ang)), (TX * 0.5, TY * 0.5, TZ), 0.0, 1.15
    if MOVE == "zoomout":
        z0 = D0 * (1 - 0.42 * A)
        return (TX * 0.8 * (1 - e), TY * 0.8 * (1 - e), z0 + (D0 - z0) * e), (TX * 0.8 * (1 - e), TY * 0.8 * (1 - e), 0), 0.0, 1.0
    if MOVE == "drone":                              # 위(사진 아래쪽에서 위를 향해 비스듬히)에서 내려다보며 앞으로
        return (0, -VH * 0.22 + VH * 0.16 * e, D0 * (0.98 - 0.16 * e * A)), (0, VH * 0.06 + VH * 0.10 * e, 0), 0.0, 1.12
    if MOVE == "fpv":
        q = t * t
        x = TX * 0.7 * q + VW * 0.025 * math.sin(t * 9.0)
        y = -VH * 0.05 * (1 - t) + TY * 0.7 * q + VH * 0.012 * math.sin(t * 23.0)
        return (x, y, D0 * (1 - 0.40 * q * A)), (x * 1.1, y * 1.1 + VH * 0.02, 0), math.radians(6 * math.sin(t * 5.5) * A), 1.12
    if MOVE == "freeze":                             # 순간이동: 4자리, 자리 안에서는 살짝 흐름
        spots = [((0, 0, D0), (0, 0, 0), 1.0),
                 ((TX * 0.5 + VW * 0.10, TY * 0.5 + VH * 0.05, D0 * 0.80), (TX * 0.7, TY * 0.7, TZ * 0.5), 1.25),
                 ((TX * 0.5 - VW * 0.10, TY * 0.5 - VH * 0.04, D0 * 0.70), (TX * 0.7, TY * 0.7, TZ * 0.5), 1.25),
                 ((TX * 0.8, TY * 0.8, D0 * 0.62), (TX * 0.8, TY * 0.8, 0), 1.0)]
        k = min(3, int(t * 4))
        f = t * 4 - k
        loc, tgt, lm = spots[k]
        return (loc[0] + VW * 0.03 * f, loc[1] + VH * 0.01 * f, loc[2] - D0 * 0.03 * f), tgt, 0.0, lm
    if MOVE == "crane":                              # 크레인 업: 낮은 데서 올라가며 내려다봄 (장면을 여는 샷)
        return (TX * 0.3 * e, -VH * 0.24 * (1 - e), D0 * (0.80 + 0.18 * e)), (TX * 0.3 * e, VH * 0.10 * (1 - e), 0), 0.0, 1.1
    if MOVE == "tilt":                               # 틸트 업: 제자리에서 아래 → 위로 훑음
        return (TX * 0.2, -VH * 0.04, D0 * 0.90), (TX * 0.2, -VH * 0.16 + VH * 0.32 * e, 0), 0.0, 1.18
    if MOVE == "dollyzoom":                          # 돌리 줌(현기증): 물러나며 확대 — 주인공 크기는 그대로, 배경만 당겨짐
        z0, z1 = D0 * 0.68, D0 * 1.0
        z = z0 + (z1 - z0) * e
        return (TX * 0.4, TY * 0.4, z), (TX * 0.4, TY * 0.4, TZ), 0.0, (z - TZ) / (z0 - TZ)
    return (0, 0, D0 * (1 - 0.1 * e)), (0, 0, 0), 0.0, 1.0


def focus_in(loc, rot, lens):
    """꼭 보여야 하는 상자의 네 귀퉁이가 화면 안(가장자리 4% 안쪽)에 있는지"""
    if not FOCUS:
        return True
    m = rot.to_matrix().transposed()
    half_w = cd.sensor_width / 2 / lens
    half_h = half_w / aspect_out
    for u, v in ((FOCUS[0], FOCUS[1]), (FOCUS[2], FOCUS[1]), (FOCUS[0], FOCUS[3]), (FOCUS[2], FOCUS[3])):
        P = Vector(((u - 0.5) * PW, (0.5 - v) * PH, 0.0)) - Vector(loc)
        c = m @ P
        if c.z >= -1e-6:
            return False
        if abs(c.x / -c.z) > half_w * 0.99 or abs(c.y / -c.z) > half_h * 0.99:
            return False
    return True


def covered(loc, rot, lens):
    """화면 네 귀퉁이가 판(z=0) 안을 보는지"""
    m = rot.to_matrix()
    half_w = cd.sensor_width / 2 / lens
    half_h = half_w / aspect_out
    for sx, sy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        ray = m @ Vector((sx * half_w, sy * half_h, -1.0))
        if ray.z >= -1e-6:
            return False
        k = -loc[2] / ray.z
        x, y = loc[0] + ray.x * k, loc[1] + ray.y * k
        if abs(x) > PW / 2 * 0.95 or abs(y) > PH / 2 * 0.95:
            return False
    return True


if LAYERED:                                          # 앞층: 배경보다 카메라 쪽에 세운 투명 판. 시작 자리에서 볼 때 사진과 똑같이 겹치게 줄여 둠
    FZ = 0.22 * PW * AMT
    loc0 = pose(0.0)[0]
    kz = (loc0[2] - FZ) / loc0[2]
    fimg = bpy.data.images.load(FG)
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=2, y_subdivisions=2, size=1.0, calc_uvs=True)
    fo = bpy.context.active_object
    for v in fo.data.vertices:
        X, Y = v.co.x * PW, v.co.y * PH
        v.co.x = loc0[0] + (X - loc0[0]) * kz
        v.co.y = loc0[1] + (Y - loc0[1]) * kz
        v.co.z = FZ
    fm = bpy.data.materials.new("fg")
    fm.use_nodes = True
    fm.blend_method = "CLIP"
    fm.alpha_threshold = 0.5
    fnt = fm.node_tree
    ft = fnt.nodes.new("ShaderNodeTexImage")
    ft.image = fimg
    ft.extension = "CLIP"
    fb = fnt.nodes.get("Principled BSDF")
    fnt.links.new(ft.outputs["Color"], fb.inputs["Base Color"])
    fnt.links.new(ft.outputs["Alpha"], fb.inputs["Alpha"])
    fo.data.materials.append(fm)

N = int(round(SEC * FPS))
scn.frame_start, scn.frame_end = 1, N
scn.render.fps = FPS
for f in range(N):
    t = f / max(1, N - 1)
    loc, tgt, roll, lm = pose(t)
    rot = look(loc, tgt, roll)
    lens = BASE_LENS * lm
    for _ in range(80):                              # 판 밖이 보이면 렌즈를 당기고, 꼭 보여야 하는 곳이 밖으로 나가면 카메라를 뒤로 뺌
        ok_c, ok_f = covered(loc, rot, lens), focus_in(loc, rot, lens)
        if ok_c and ok_f:
            break
        if not ok_f:
            loc = (loc[0] * 0.95, loc[1] * 0.95, min(loc[2] * 1.03, D0 / 0.9))
            lens = max(lens / 1.015, BASE_LENS * 0.9)
            tgt = (tgt[0] * 0.95 + (PU - 0.5) * PW * 0.05, tgt[1] * 0.95 + (0.5 - PV) * PH * 0.05, tgt[2])
            rot = look(loc, tgt, roll)
        else:
            lens *= 1.03
    for _ in range(60):                              # 그래도 판 밖(검은 빈 곳)이 보이면 그건 꼭 막음 (빈 곳이 더 나쁨)
        if covered(loc, rot, lens):
            break
        lens *= 1.03
    cam.location = loc
    cam.rotation_euler = rot
    cd.lens = lens
    cam.keyframe_insert("location", frame=f + 1)
    cam.keyframe_insert("rotation_euler", frame=f + 1)
    cd.keyframe_insert("lens", frame=f + 1)
interp = "CONSTANT" if MOVE == "freeze" else "LINEAR"   # (프레임마다 키를 넣으므로 LINEAR 면 그대로)
for dat in (cam, cd):
    for fc in dat.animation_data.action.fcurves:
        for kp in fc.keyframe_points:
            kp.interpolation = interp

# ── 렌더: Workbench, 텍스처 그대로, 빛·그림자 없음 ──
r = scn.render
r.engine = "BLENDER_WORKBENCH"
r.resolution_x, r.resolution_y, r.resolution_percentage = W, H, 100
sh = scn.display.shading
sh.light = "FLAT"
sh.color_type = "TEXTURE"
sh.show_shadows = False
sh.show_cavity = False
sh.show_object_outline = False
sh.show_specular_highlight = False
scn.display.render_aa = AA
scn.view_settings.view_transform = "Standard"
scn.view_settings.look = "None"
r.image_settings.file_format = "FFMPEG"
r.ffmpeg.format = "MPEG4"
r.ffmpeg.codec = "H264"
r.ffmpeg.constant_rate_factor = "HIGH"
r.ffmpeg.ffmpeg_preset = "GOOD"
r.filepath = out_path
r.use_file_extension = False
bpy.ops.render.render(animation=True)
print("OK", MOVE, out_path, flush=True)
