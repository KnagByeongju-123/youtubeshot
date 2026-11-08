"""사진(그림) 한 장 → 로우폴리 입체 (사용자 요청 2026-11-07 '사진을 블렌더로 로우폴리 렌더링해서 입체로 만들기 테스트')
1) 깊이: .supertonic_venv/bin/python -X utf8 depth_worker.py models/depth_anything_v2_small_fp16.onnx <폴더> <그림.png>
   (Depth Anything V2 Small, Apache-2.0 → <폴더>/<키>.npy, 0=멀다 1=가깝다)
2) 렌더: xvfb-run -a -s "-screen 0 1920x1080x24" blender -b -P 블렌더/사진_로우폴리입체.py -- <그림.png> <깊이.npy> <결과폴더>
        [--grid 120] [--depth 3.2] [--frames 240] [--size 1280x720] [--still]
  - 그림을 가로 grid 칸짜리 삼각형 그물로 나누고, 꼭짓점을 깊이만큼 앞으로 밀어 올림 → 삼각형마다 그 자리 그림 색 한 가지 (각진 로우폴리)
  - 앞으로 튀어나온 사람과 뒤 배경 사이에 늘어난 삼각형은 깊이 차가 크면 지움(구멍 대신 뒤쪽 배경판이 보임)
  - 카메라: 정면에서 시작해 좌우로 천천히 흔들며(±18도) 조금 다가감
  - --smooth : 삼각형 없이 사진을 그대로 입힌 부드러운 입체 (장문 다큐 실제 사진용), --zoom 0.86 : 카메라 거리
  - 결과: <폴더>/frame_####.png, --still 이면 정면·왼쪽·오른쪽 세 장
  - 마무리(사용자 제안 2026-11-07): 렌더 뒤 가운데 기준으로 114%→120% 천천히 확대 → 가장자리 빈 곳이 안 보이고 다가가는 움직임이 더해짐
    ffmpeg -i in.mp4 -vf "scale=-2:720,zoompan=z='1.14+0.06*on/<장수>':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=1280x720:fps=24" out.mp4"""
import math
import os
import sys

import bpy
import numpy as np

argv = sys.argv[sys.argv.index("--") + 1:]
IMG, NPY, OUT = [os.path.abspath(a) for a in argv[:3]]
opt = lambda k, d: (argv[argv.index(k) + 1] if k in argv else d)
GRID = int(opt("--grid", 120))
DEPTH = float(opt("--depth", 3.2))
FRAMES = int(opt("--frames", 240))
W, H = [int(v) for v in opt("--size", "1280x720").split("x")]
STILL = "--still" in argv
ZOOM = float(opt("--zoom", 1.0))          # 카메라 거리 배율 (작을수록 가까이 → 가장자리 빈 곳 안 보임)
SMOOTH = "--smooth" in argv
KEY = "--key" in argv                     # 빈 곳(배경·뒤판)을 자홍색으로 → 사진_입체영상.py 가 가장자리 까짐을 찾아 잘라 냄
CAM = opt("--cam", "sway")                # sway = 좌우로 흔들기 / orbit = 앞으로 다가가며 한쪽으로 돌아감 (사용자 제안 2026-11-07)
ARC = float(opt("--arc", 22))             # orbit 때 도는 각도(도)               # 삼각형 대신 사진을 그대로 입힌 부드러운 입체 (다큐용)
os.makedirs(OUT, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
scn = bpy.context.scene

def block_mean(a, by, bx):        # 칸마다 평균 색 (먹선 때문에 삼각형이 얼룩덜룩해지지 않게)
    h, w = a.shape[:2]
    ys = np.linspace(0, h, by + 1).astype(int)
    xs = np.linspace(0, w, bx + 1).astype(int)
    out = np.zeros((by, bx) + a.shape[2:], np.float32)
    for j in range(by):
        for i in range(bx):
            out[j, i] = a[ys[j]:ys[j + 1], xs[i]:xs[i + 1]].reshape(-1, a.shape[-1]).mean(0)
    return out


# ── 그림·깊이 읽기 ──
img = bpy.data.images.load(IMG)
iw, ih = img.size
px = np.array(img.pixels[:], dtype=np.float32).reshape(ih, iw, 4)[::-1]   # 위→아래 순서로
px = np.where(px <= 0.04045, px / 12.92, ((px + 0.055) / 1.055) ** 2.4)      # 그림 색(sRGB) → 블렌더 꼭짓점 색(선형), 안 하면 색이 바램
dep = np.load(NPY).astype(np.float32)
dh, dw = dep.shape
gx, gy = GRID, max(2, round(GRID * ih / iw))
px = block_mean(px, gy * 2, gx * 2)
PW = 16.0
PH = PW * ih / iw


def sample(arr, u, v):             # u,v 0~1 (v 0 = 위)
    h, w = arr.shape[:2]
    return arr[min(h - 1, int(v * (h - 1) + 0.5)), min(w - 1, int(u * (w - 1) + 0.5))]


# 꼭짓점 (가로 줄마다 반 칸씩 엇갈려 삼각형이 고르게)
verts, dz = [], []
for j in range(gy + 1):
    for i in range(gx + 1):
        u = min(1.0, max(0.0, (i + (0.5 if j % 2 else 0.0)) / gx))
        v = j / gy
        d = float(sample(dep, u, v))
        dz.append(d)
        verts.append(((u - 0.5) * PW, -d * DEPTH, (0.5 - v) * PH))
faces, cols = [], []
idx = lambda i, j: j * (gx + 1) + i
for j in range(gy):
    for i in range(gx):
        a, b, c, d = idx(i, j), idx(i + 1, j), idx(i, j + 1), idx(i + 1, j + 1)
        tris = ((a, c, b), (b, c, d)) if j % 2 == 0 else ((a, c, d), (a, d, b))
        for t in tris:
            zs = [dz[k] for k in t]
            if max(zs) - min(zs) > 9:      # 지우지 않고 늘여서 이음 (구멍 대신 옆면처럼 보임)       # 사람 테두리에서 크게 늘어난 삼각형은 버림
                continue
            faces.append(t)
            cu = sum((verts[k][0] / PW + 0.5) for k in t) / 3
            cv = sum((0.5 - verts[k][2] / PH) for k in t) / 3
            cols.append(sample(px, cu, cv))

me = bpy.data.meshes.new("입체")
me.from_pydata(verts, [], faces)
me.update()
attr = me.color_attributes.new("색", "FLOAT_COLOR", "CORNER")
for p, col in zip(me.polygons, cols):
    for li in p.loop_indices:
        attr.data[li].color = (col[0], col[1], col[2], 1.0)
if SMOOTH:
    uv = me.uv_layers.new(name="UV")
    for p in me.polygons:
        for li in p.loop_indices:
            vx = verts[me.loops[li].vertex_index]
            uv.data[li].uv = (vx[0] / PW + 0.5, vx[2] / PH + 0.5)
    for p in me.polygons:
        p.use_smooth = True
    sm_ = bpy.data.materials.new("사진")
    sm_.use_nodes = True
    tx = sm_.node_tree.nodes.new("ShaderNodeTexImage")
    tx.image = img
    sm_.node_tree.links.new(tx.outputs["Color"], sm_.node_tree.nodes["Principled BSDF"].inputs["Base Color"])
    me.materials.append(sm_)
ob = bpy.data.objects.new("입체", me)
scn.collection.objects.link(ob)

# 뒤 배경판 (구멍 난 곳 뒤로 보이는 흐린 그림)
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, DEPTH * 0.02 + 0.3, 0), rotation=(math.pi / 2, 0, 0))
bg = bpy.context.object
bg.hide_render = KEY                      # 검사 모드: 뒤판 없이 빈 곳은 배경(자홍)으로
bg.scale = (PW * 2.5, PH * 2.5, 1)
bc = (1.0, 0.0, 1.0) if KEY else px.reshape(-1, 4).mean(0)
ca = bg.data.color_attributes.new("색", "FLOAT_COLOR", "CORNER")
for d_ in ca.data:
    d_.color = (bc[0], bc[1], bc[2], 1.0)

# ── 카메라 ──
cam = bpy.data.objects.new("카메라", bpy.data.cameras.new("카메라"))
cam.data.lens = 35
scn.collection.objects.link(cam)
scn.camera = cam
tgt = bpy.data.objects.new("목표", None)
tgt.location = (0, -DEPTH * 0.4, 0)
scn.collection.objects.link(tgt)
tc = cam.constraints.new("TRACK_TO")
tc.target = tgt
tc.track_axis = "TRACK_NEGATIVE_Z"
tc.up_axis = "UP_Y"
R0 = PW * 1.06 * ZOOM


def ease(x):
    return x * x * (3 - 2 * x)


def cam_at(t):        # t 0~1
    if CAM == "orbit":     # 전진 + 오르빗: 왼쪽에서 시작해 오른쪽으로 돌면서 거리 25% 줄이고 살짝 내려옴
        e = ease(t)
        ang = math.radians(ARC) * (e - 0.5) * 2
        r = R0 * (1.0 - 0.25 * e)
        cam.location = (r * math.sin(ang), -DEPTH * 0.4 - r * math.cos(ang), 0.9 * (1 - e) - 0.2)
        return
    ang = math.radians(10) * math.sin(2 * math.pi * t)
    r = R0 * (1 - 0.06 * t)
    cam.location = (r * math.sin(ang), -DEPTH * 0.4 - r * math.cos(ang), 0.6 * math.sin(math.pi * t))


# ── 렌더 (단순 그리기 + 꼭짓점 색, 평평한 면 → 각진 로우폴리) ──
scn.render.engine = "BLENDER_WORKBENCH"
scn.view_settings.view_transform = "Standard"
sh = scn.display.shading
sh.light = "FLAT"
sh.color_type = "TEXTURE" if SMOOTH else "VERTEX"
sh.show_object_outline = False
sh.background_type = "VIEWPORT"
sh.background_color = (1.0, 0.0, 1.0) if KEY else (0.95, 0.93, 0.88)
scn.display.render_aa = "8"
scn.render.resolution_x, scn.render.resolution_y = W, H
scn.render.image_settings.file_format = "PNG"
if KEY:                                      # 검사 모드: 빈 곳은 투명(알파 0) → 사진_입체영상.py 가 찾아 잘라 냄
    scn.render.film_transparent = True
    scn.render.image_settings.color_mode = "RGBA"
if STILL:
    for nm, t in (("정면", 0.0), ("왼쪽", 0.25), ("오른쪽", 0.75)):
        cam_at(t)
        scn.render.filepath = os.path.join(OUT, nm + ".png")
        bpy.ops.render.render(write_still=True)
else:
    for f in range(FRAMES):
        cam_at(f / FRAMES)
        scn.render.filepath = os.path.join(OUT, "frame_%04d.png" % (f + 1))
        bpy.ops.render.render(write_still=True)
print("OK", OUT, len(faces), "faces")
