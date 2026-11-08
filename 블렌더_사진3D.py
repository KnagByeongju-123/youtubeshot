r"""사진 한 장 → Blender 진짜 3D 카메라 움직임 영상 (사용자 결정 2026-11-08: '블렌더 활용')
깊이 AI(depth_worker.py, Depth Anything V2)로 만든 깊이 지도대로 사진을 입체 판으로 세우고,
Blender 카메라가 천천히 다가가며 옆으로 살짝 돌아 앞뒤가 다르게 움직이는(시차) 영상을 만든다.

사용 (Blender 안에서 실행):
  blender -b -noaudio --factory-startup -P 블렌더_사진3D.py -- <사진> <깊이.npy> <결과.mp4> [초=10] [가로=1920] [세로=1080] [방향=0~3] [세기=1.0]
- 방향: 0 오른쪽으로 돌며 다가감, 1 왼쪽, 2 위로, 3 뒤로 물러남 (사진마다 돌아가며 써서 단조롭지 않게)
- 렌더는 Workbench(텍스처 그대로·빛 없음) → 사진 색이 바뀌지 않고, 그래픽카드 없이도 빠름
- 결과는 고정 길이 영상: 프로그램(render)이 장면 길이에 맞춰 시간 비율로 프레임을 골라 씀
"""
import sys
import math
import numpy as np
import bpy

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
img_path, depth_path, out_path = argv[0], argv[1], argv[2]
SEC = float(argv[3]) if len(argv) > 3 else 10.0
W = int(argv[4]) if len(argv) > 4 else 1920
H = int(argv[5]) if len(argv) > 5 else 1080
MOVE = int(argv[6]) if len(argv) > 6 else 0
AMT = float(argv[7]) if len(argv) > 7 else 1.0
FPS = 24
import os
AA = os.environ.get("BL_AA", "FXAA")

# ── 장면 비우기 ──
bpy.ops.wm.read_factory_settings(use_empty=True)
scn = bpy.context.scene

# ── 사진·깊이 ──
img = bpy.data.images.load(img_path)
iw, ih = img.size
aspect_img = iw / ih
d = np.load(depth_path).astype(np.float32)
d = (d - d.min()) / max(1e-6, float(d.max() - d.min()))
# 깊이를 부드럽게 (경계에서 고무처럼 늘어나는 것을 줄임): 간단한 상자 흐림 3번
for _ in range(3):
    p = np.pad(d, 2, mode="edge")
    d = sum(p[i:i + d.shape[0], j:j + d.shape[1]] for i in range(5) for j in range(5)) / 25.0
dh, dw = d.shape

# ── 판(그리드) 만들기: 너비 2, 높이 2/aspect ──
PW, PH = 2.0, 2.0 / aspect_img
nx = 240
ny = max(8, int(round(nx / aspect_img)))
bpy.ops.mesh.primitive_grid_add(x_subdivisions=nx, y_subdivisions=ny, size=1.0, calc_uvs=True)
ob = bpy.context.active_object
me = ob.data
DEPTH_AMP = 0.10 * AMT * PW        # 가장 가까운 곳이 판 너비의 10% 앞으로
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
bsdf = nt.nodes.get("Principled BSDF")
nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
me.materials.append(mat)

# ── 카메라: 화면(16:9)이 판 안에 '꽉 차게' + 움직일 여유 ──
aspect_out = W / H
cam_data = bpy.data.cameras.new("cam")
cam_data.sensor_fit = "HORIZONTAL"
cam_data.lens = 50
cam_data.sensor_width = 36
cam = bpy.data.objects.new("cam", cam_data)
scn.collection.objects.link(cam)
scn.camera = cam
fov_h = 2 * math.atan(cam_data.sensor_width / 2 / cam_data.lens)
# 판에서 보이는 가로 폭: 사진이 화면보다 가로로 길면 높이에 맞추고, 아니면 너비에 맞춤 (cover)
view_w = min(PW, PH * aspect_out) * 0.86        # 14% 여유 (움직여도 가장자리가 안 보이게)
dist0 = (view_w / 2) / math.tan(fov_h / 2)
MARGIN = (min(PW, PH * aspect_out) - view_w) / 2

def cam_at(t):
    """t: 0~1 → (x, y, z) 카메라 위치, 바라보는 점은 판 가운데 근처"""
    e = 0.5 - 0.5 * math.cos(math.pi * t)          # 처음·끝 부드럽게
    side = MARGIN * 0.55 * AMT
    if MOVE == 0:   x, y, z = -side + 2 * side * e, 0.0, dist0 * (1.0 - 0.10 * e)
    elif MOVE == 1: x, y, z = side - 2 * side * e, 0.0, dist0 * (1.0 - 0.10 * e)
    elif MOVE == 2: x, y, z = 0.0, -side * 0.6 + 1.2 * side * 0.6 * e, dist0 * (1.0 - 0.10 * e)
    else:           x, y, z = side * 0.5 * (1 - 2 * e), 0.0, dist0 * (0.90 + 0.10 * e)
    return x, y, z

N = int(round(SEC * FPS))
scn.frame_start, scn.frame_end = 1, N
scn.render.fps = FPS
for f in range(N):
    t = f / max(1, N - 1)
    x, y, z = cam_at(t)
    cam.location = (x, y, z)
    # 카메라는 판 가운데(조금 따라감)를 바라봄 → 옆으로 돌 때 진짜 시차가 생김
    tx, ty = x * 0.35, y * 0.35
    dx, dy, dz = tx - x, ty - y, 0.0 - z
    cam.rotation_euler = (math.atan2(dy, -dz), -math.atan2(dx, -dz), 0.0)   # 기본 카메라는 -Z 를 봄
    cam.keyframe_insert("location", frame=f + 1)
    cam.keyframe_insert("rotation_euler", frame=f + 1)

# ── 렌더 설정: Workbench, 텍스처 그대로, 빛·그림자 없음 ──
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
print("OK", out_path, flush=True)
