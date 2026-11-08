"""사진 두 층(앞 주인공 + 뒤 배경) 입체 — 블렌더 카메라 움직임 (사용자 결정 2026-11-08)
xvfb-run -a -s "-screen 0 1920x1080x24" blender -b -P 블렌더/사진_층입체.py -- <앞층.png(투명 배경)> <뒤층.png> <결과폴더>
      --cam 직진|오르빗|줌아웃|순간이동|드론|옆으로|1인칭|반대쪽 [--frames 240] [--size 1920x1080] [--gap 2.2] [--zoom 1.0] [--key] [--still]
  - 뒤층(빈자리를 둘레 색으로 메운 사진)은 판 하나로 뒤에, 앞층(오려 낸 주인공, 투명한 곳은 판을 만들지 않음)은 gap 만큼 앞에 세움
    → 카메라가 움직이면 가까운 앞층과 먼 배경이 다른 빠르기로 움직여 입체로 보임. 앞층은 원근에 맞게 줄여 정면에서는 원래 사진과 똑같이 보임
  - --key : 빈 곳을 투명으로 (가장자리 빈 곳 검사용, 사진_층입체.py 가 확대해 잘라 냄)"""
import math
import os
import sys

import bpy
import numpy as np

argv = sys.argv[sys.argv.index("--") + 1:]
FG, BG, OUT = [os.path.abspath(x) for x in argv[:3]]
opt = lambda k, d: (argv[argv.index(k) + 1] if k in argv else d)
CAM = opt("--cam", "직진")
FRAMES = int(opt("--frames", 240))
W, H = [int(v) for v in opt("--size", "1920x1080").split("x")]
GAP = float(opt("--gap", 2.2))
ZOOM = float(opt("--zoom", 1.0))
KEY = "--key" in argv
STILL = "--still" in argv
os.makedirs(OUT, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
scn = bpy.context.scene

bg_img = bpy.data.images.load(BG)
fg_img = bpy.data.images.load(FG)
iw, ih = bg_img.size
PW = 16.0
PH = PW * ih / iw
LENS = 35.0
D0 = (PW / 2) / math.tan(math.atan(36 / (2 * LENS))) * ZOOM          # 정면에서 뒤층이 화면을 꼭 채우는 거리


def tex_mat(name, img, alpha=False):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    tx = m.node_tree.nodes.new("ShaderNodeTexImage")
    tx.image = img
    bsdf = m.node_tree.nodes["Principled BSDF"]
    m.node_tree.links.new(tx.outputs["Color"], bsdf.inputs["Base Color"])
    if alpha:                                                          # 앞층 테두리는 그림의 투명도로 부드럽게 (모눈 칸 계단 없음)
        m.node_tree.links.new(tx.outputs["Alpha"], bsdf.inputs["Alpha"])
        for k, v in (("blend_method", "BLEND"), ("surface_render_method", "BLENDED")):
            try:
                setattr(m, k, v)
            except Exception:
                pass
    return m


def plane(name, img, y, scale, mask=None, grid=180):
    """y 위치에 그림 판. mask(위→아래 순서 numpy bool)가 있으면 그 칸만 면을 만듦"""
    gx, gy = grid, max(2, round(grid * ih / iw))
    verts, uvs, faces = [], [], []
    for j in range(gy + 1):
        for i in range(gx + 1):
            u, v = i / gx, j / gy
            verts.append(((u - 0.5) * PW * scale, y, (0.5 - v) * PH * scale))
            uvs.append((u, 1 - v))
    idx = lambda i, j: j * (gx + 1) + i
    for j in range(gy):
        for i in range(gx):
            if mask is not None:
                mh, mw = mask.shape
                if not mask[min(mh - 1, int((j + 0.5) / gy * mh)), min(mw - 1, int((i + 0.5) / gx * mw))]:
                    continue
            faces.append((idx(i, j), idx(i, j + 1), idx(i + 1, j + 1), idx(i + 1, j)))
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    uv = me.uv_layers.new(name="UV")
    for p in me.polygons:
        for li in p.loop_indices:
            uv.data[li].uv = uvs[me.loops[li].vertex_index]
    me.materials.append(tex_mat(name, img, alpha=mask is not None))
    ob = bpy.data.objects.new(name, me)
    scn.collection.objects.link(ob)
    return ob


fa = np.array(fg_img.pixels[:], dtype=np.float32).reshape(ih, iw, 4)[::-1][..., 3] > 0.02
try:                                                                   # 면은 주인공보다 조금 넓게 (가장자리 투명 부분까지 덮게)
    import cv2
    fa = cv2.dilate(fa.astype(np.uint8), np.ones((9, 9), np.uint8)) > 0
except Exception:
    pad = np.zeros_like(fa)
    for dy in range(-4, 5, 2):
        for dx in range(-4, 5, 2):
            pad |= np.roll(np.roll(fa, dy, 0), dx, 1)
    fa = pad
plane("뒤층", bg_img, 0.0, 1.0)
s_fg = (D0 - GAP) / D0                                              # 원근 보정: 정면에서 원래 사진과 같은 크기로 보이게
plane("앞층", fg_img, -GAP, s_fg, mask=fa, grid=360)

cam = bpy.data.objects.new("카메라", bpy.data.cameras.new("카메라"))
cam.data.lens = LENS
cam.data.clip_start = 0.05
scn.collection.objects.link(cam)
scn.camera = cam
tgt = bpy.data.objects.new("목표", None)
scn.collection.objects.link(tgt)
tc = cam.constraints.new("TRACK_TO")
tc.target = tgt
tc.track_axis = "TRACK_NEGATIVE_Z"
tc.up_axis = "UP_Y"


def ease(x):
    return x * x * (3 - 2 * x)


def shake(t, seed, amp):
    return amp * (math.sin(t * 37.1 + seed) * 0.5 + math.sin(t * 61.7 + seed * 2.3) * 0.3 + math.sin(t * 97.3 + seed * 4.1) * 0.2)


TELE = [(0.0, 0.0, 1.0), (-0.22, 0.08, 0.72), (0.2, -0.05, 0.7), (0.0, 0.12, 0.85)]   # (보는 곳 가로·세로, 거리) — 순간이동 자리


def cam_at(t):
    """t 0~1. 장면마다 돌아가며 쓰는 8가지 카메라 (사용자 결정 2026-11-08)"""
    e = ease(t)
    tc.mute = False
    tgt.location = (0, 0, 0)
    if CAM == "직진":          # 앞으로 곧게 다가감
        cam.location = (0, -D0 * (1 - 0.30 * e), 0)
    elif CAM == "오르빗":       # 다가가며 한쪽으로 돎
        a = math.radians(14) * (2 * e - 1)
        r = D0 * (1 - 0.18 * e)
        cam.location = (r * math.sin(a), -r * math.cos(a), 0.4 * (1 - e))
    elif CAM == "줌아웃":       # 가까이에서 시작해 뒤로 물러남
        cam.location = (0, -D0 * (0.7 + 0.3 * e), 0.2 * e)
    elif CAM == "순간이동":     # 3~4 자리를 순간적으로 옮겨 가며 자리마다 천천히 흐름
        n = len(TELE)
        k = min(n - 1, int(t * n))
        u = t * n - k
        tx, tz, d = TELE[k]
        tgt.location = (tx * PW, 0, tz * PH)
        a = math.radians(4 * (2 * u - 1) * (1 if k % 2 == 0 else -1))
        r = D0 * d * (1 - 0.04 * u)
        cam.location = (tx * PW + r * math.sin(a), -r * math.cos(a), tz * PH + 0.1 * u)
    elif CAM == "드론":         # 위에서 내려다보며 앞으로 날다 내려옴
        cam.location = (0, -D0 * (1 - 0.22 * e), PH * 0.22 * (1 - e) + 0.05)
        tgt.location = (0, 0, -PH * 0.08 * (1 - e))
    elif CAM == "옆으로":       # 왼쪽에서 오른쪽으로 미끄러짐 (보는 곳도 같이)
        x = PW * 0.07 * (2 * e - 1)
        cam.location = (x, -D0 * 0.92, 0)
        tgt.location = (x * 0.6, 0, 0)
    elif CAM == "반대쪽":       # 오른쪽에서 왼쪽으로 돎 (오르빗 반대)
        a = math.radians(14) * (1 - 2 * e)
        r = D0 * (1 - 0.15 * e)
        cam.location = (r * math.sin(a), -r * math.cos(a), -0.3 * e + 0.15)
    elif CAM == "1인칭":        # FPV 드론: 빠르게 앞으로, 좌우로 기울고 잔떨림 (렌즈 볼록·모서리 어둡게는 뒤에서)
        tc.mute = True
        y = -D0 * (1 - 0.22 * t)
        x = 0.5 * math.sin(2 * math.pi * t * 0.8) + shake(t, 1, 0.04)
        z = 0.25 * math.sin(2 * math.pi * t * 0.5 + 1) + shake(t, 2, 0.03)
        roll = math.radians(6) * math.sin(2 * math.pi * t * 0.8 + 0.6) + shake(t, 3, math.radians(0.8))
        yaw = -math.radians(3) * math.sin(2 * math.pi * t * 0.8) + shake(t, 4, math.radians(0.4))
        cam.location = (x, y, z)
        cam.rotation_euler = (math.radians(90) + shake(t, 5, math.radians(0.5)), roll, yaw)
    else:
        cam.location = (0, -D0, 0)


scn.render.engine = "BLENDER_WORKBENCH"
scn.view_settings.view_transform = "Standard"
sh = scn.display.shading
sh.light = "FLAT"
sh.color_type = "TEXTURE"
sh.background_type = "VIEWPORT"
sh.background_color = (0.0, 0.0, 0.0)
scn.display.render_aa = "8"
scn.render.resolution_x, scn.render.resolution_y = W, H
scn.render.image_settings.file_format = "PNG"
if KEY:
    scn.render.film_transparent = True
    scn.render.image_settings.color_mode = "RGBA"
if STILL:
    for nm, t in (("처음", 0.0), ("가운데", 0.5), ("끝", 1.0)):
        cam_at(t)
        scn.render.filepath = os.path.join(OUT, nm + ".png")
        bpy.ops.render.render(write_still=True)
else:
    for f in range(FRAMES):
        cam_at(f / max(1, FRAMES - 1))
        scn.render.filepath = os.path.join(OUT, "frame_%04d.png" % (f + 1))
        bpy.ops.render.render(write_still=True)
print("OK", OUT)
