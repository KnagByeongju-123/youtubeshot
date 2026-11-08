"""사진 한 장으로 '공간 통과' 영상 — 앞층(가까운 나무·바위)을 카메라가 지나 안쪽으로 들어감 (사용자 제안 2026-11-07)
1) 깊이: depth_worker.py → <깊이.npy>
2) 층: .sd_venv/bin/python -X utf8 사진_층나누기.py <사진> <깊이.npy> <층폴더> [--앞비율 0.3]
3) 렌더: xvfb-run -a -s "-screen 0 1920x1080x24" blender -b -P 블렌더/사진_공간통과.py -- <사진> <깊이.npy> <층폴더> <결과폴더>
        [--frames 168] [--size 1280x720] [--push 0.75] [--grid 260] [--still]
  - 뒤층(앞층을 지우고 채운 배경) 판 + 앞층(가까운 것만) 판 두 장을 깊이대로 세움
  - 카메라가 정면에서 앞으로 push(기본 카메라 거리의 75%)만큼 들어가며 살짝 내려감 → 앞층이 화면 밖으로 지나가고 그 뒤 공간이 열림
  - 카메라 바로 앞(가까운 자르기 거리 안)의 것은 그리지 않으므로 앞층을 '뚫고' 지나가는 것처럼 보임"""
import math
import os
import sys

import bpy
import numpy as np

argv = sys.argv[sys.argv.index("--") + 1:]
IMG, NPY, LAY, OUT = [os.path.abspath(a) for a in argv[:4]]
opt = lambda k, d: (argv[argv.index(k) + 1] if k in argv else d)
FRAMES = int(opt("--frames", 168))
W, H = [int(v) for v in opt("--size", "1280x720").split("x")]
PUSH = float(opt("--push", 0.75))
GRID = int(opt("--grid", 260))
DEPTH = float(opt("--depth", 6.0))
STILL = "--still" in argv
KEY = "--key" in argv                     # 빈 곳을 자홍색으로 (가장자리 까짐 검사용)
os.makedirs(OUT, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
scn = bpy.context.scene


def load_px(path):
    im = bpy.data.images.load(path)
    return im, np.array(im.pixels[:], dtype=np.float32).reshape(im.size[1], im.size[0], 4)[::-1]


img, _ = load_px(IMG)
bgimg, _ = load_px(os.path.join(LAY, "뒤층.png"))
_, mask = load_px(os.path.join(LAY, "앞층_mask.png"))
mask = mask[..., 0] > 0.5
iw, ih = img.size
PW = 16.0
PH = PW * ih / iw
gx, gy = GRID, max(2, round(GRID * ih / iw))


def sample(arr, u, v):
    h, w = arr.shape[:2]
    return arr[min(h - 1, int(v * (h - 1) + 0.5)), min(w - 1, int(u * (w - 1) + 0.5))]


def z_of(d):            # 깊이 0~1 → 카메라 쪽(-Y)으로 얼마나 나오나 (가까울수록 더 크게)
    return -(d ** 1.6) * DEPTH


def build(name, depth, image, keep=None):
    verts, uvs = [], []
    for j in range(gy + 1):
        for i in range(gx + 1):
            u, v = i / gx, j / gy
            d = float(sample(depth, u, v))
            verts.append(((u - 0.5) * PW * (1 + 0.0), z_of(d), (0.5 - v) * PH))
            uvs.append((u, 1 - v))
    faces = []
    idx = lambda i, j: j * (gx + 1) + i
    for j in range(gy):
        for i in range(gx):
            q = (idx(i, j), idx(i, j + 1), idx(i + 1, j + 1), idx(i + 1, j))
            if keep is not None and not sample(keep, (i + 0.5) / gx, (j + 0.5) / gy):
                continue
            faces.append(q)
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    uv = me.uv_layers.new(name="UV")
    for p in me.polygons:
        p.use_smooth = True
        for li in p.loop_indices:
            uv.data[li].uv = uvs[me.loops[li].vertex_index]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    tx = m.node_tree.nodes.new("ShaderNodeTexImage")
    tx.image = image
    m.node_tree.links.new(tx.outputs["Color"], m.node_tree.nodes["Principled BSDF"].inputs["Base Color"])
    me.materials.append(m)
    ob = bpy.data.objects.new(name, me)
    scn.collection.objects.link(ob)
    return ob


dep = np.load(NPY).astype(np.float32)
bdep = np.load(os.path.join(LAY, "뒤층_깊이.npy")).astype(np.float32)
build("뒤층", bdep, bgimg)
build("앞층", dep, img, keep=mask)

cam = bpy.data.objects.new("카메라", bpy.data.cameras.new("카메라"))
cam.data.lens = 32
cam.data.clip_start = 0.6          # 카메라 바로 앞은 그리지 않음 → 앞층을 뚫고 지나감
scn.collection.objects.link(cam)
scn.camera = cam
R0 = PW * 0.9


def ease(x):
    return x * x * (3 - 2 * x)


def cam_at(t):
    e = ease(t)
    y = -R0 + R0 * PUSH * e
    cam.location = (0.0, y, 0.5 - 0.9 * e)
    cam.rotation_euler = (math.radians(90 - 2 * e), 0, 0)


scn.render.engine = "BLENDER_WORKBENCH"
scn.view_settings.view_transform = "Standard"
sh = scn.display.shading
sh.light = "FLAT"
sh.color_type = "TEXTURE"
sh.background_type = "VIEWPORT"
sh.background_color = (1.0, 0.0, 1.0) if KEY else (0.9, 0.92, 0.9)
scn.display.render_aa = "8"
scn.render.resolution_x, scn.render.resolution_y = W, H
scn.render.image_settings.file_format = "PNG"
if KEY:                                      # 검사 모드: 빈 곳은 투명(알파 0) → 사진_입체영상.py 가 찾아 잘라 냄
    scn.render.film_transparent = True
    scn.render.image_settings.color_mode = "RGBA"
if STILL:
    for nm, t in (("처음", 0.0), ("가운데", 0.5), ("끝", 1.0)):
        cam_at(t)
        scn.render.filepath = os.path.join(OUT, nm + ".png")
        bpy.ops.render.render(write_still=True)
else:
    for f in range(FRAMES):
        cam_at(f / (FRAMES - 1))
        scn.render.filepath = os.path.join(OUT, "frame_%04d.png" % (f + 1))
        bpy.ops.render.render(write_still=True)
print("OK", OUT)
