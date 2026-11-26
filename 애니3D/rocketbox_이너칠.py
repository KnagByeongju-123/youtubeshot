"""Rocketbox 얼굴(재질 1, 목·윗가슴 포함) 그림에서 둥근 목선(U자) 아래 가슴을 흰 이너 색으로 칠함 — 정장 V넥이 깊어 가슴이 많이 보였음 (사용자 2026-11-26 '2번')
   그림 점마다 3D 자리를 구해(면을 그림 좌표로 펼쳐 채움) 높이 z < 목선(가운데 --높이, 옆으로 갈수록 올라감) 이고 앞쪽인 곳만 칠함, 경계는 부드럽게
   정장 몸(재질 0)의 가슴 피부도 칠할 수 있음: --재질 0 --그림 _body_color (가슴 V 사이 피부는 몸 그림에 있었음, Business_Female_04)
   어깨 칠하기: --z최소 1.36 --x최소 0.05 --높이 9 --색 26,26,30 (얼굴을 바꾸면 몸 그림의 어깨 윗부분 피부가 깃 옆으로 비쳤음, Sports_Female_02 + Female_Adult_15)
   사용: .bpy_venv/bin/python -I 애니3D/rocketbox_이너칠.py <인물 폴더> <그림 폴더(없으면 원본 복사, 덮어씀)> [--재질 0|1] [--그림 _body_color|_head_color]
         [--높이 1.375] [--휨 2.0] [--색 236,236,238]"""
import os, sys
import bpy
import numpy as np
from PIL import Image

a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
folder, texdir = a[0].rstrip("/"), a[1]; nm = os.path.basename(folder)
Z0 = float(a[a.index("--높이") + 1]) if "--높이" in a else 1.375
BEND = float(a[a.index("--휨") + 1]) if "--휨" in a else 2.0
ZMIN = float(a[a.index("--z최소") + 1]) if "--z최소" in a else -9.0      # 이 높이보다 위만 (어깨 칠하기용)
XMIN = float(a[a.index("--x최소") + 1]) if "--x최소" in a else -1.0      # 가운데에서 이만큼 옆만
COL = np.array([float(v) for v in (a[a.index("--색") + 1] if "--색" in a else "236,236,238").split(",")]) / 255
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=os.path.join(folder, "Export", f"{nm}_facial.fbx"))
o = next(x for x in bpy.data.objects if x.type == "MESH"); me = o.data; M = o.matrix_world
uvl = me.uv_layers.active.data
MAT = int(a[a.index("--재질") + 1]) if "--재질" in a else 1
KIND = a[a.index("--그림") + 1] if "--그림" in a else "_head_color"
os.makedirs(texdir, exist_ok=True)
src = os.path.join(folder, "Textures"); want = next(f for f in os.listdir(src) if f.endswith(KIND + ".tga"))
if not os.path.exists(os.path.join(texdir, want)):
    import shutil; shutil.copy(os.path.join(src, want), os.path.join(texdir, want))
head = want
img = np.asarray(Image.open(os.path.join(texdir, head)).convert("RGB")).astype(np.float32) / 255; TH, TW = img.shape[:2]
out = img.copy(); SOFT = 0.006; n = 0
me.calc_loop_triangles()
P = [M @ v.co for v in me.vertices]
for t in me.loop_triangles:
    if t.material_index != MAT: continue
    ps = [P[i] for i in t.vertices]
    if min(p.z for p in ps) > Z0 + max(BEND, 0) * 0.2 ** 2 + 0.02 or max(p.y for p in ps) > 0.05 or max(p.z for p in ps) < Z0 - 0.35: continue      # 앞쪽 가슴 근처만
    uv = np.array([tuple(uvl[li].uv) for li in t.loops]) * [TW - 1, TH - 1]; uv[:, 1] = (TH - 1) - uv[:, 1]
    xyz = np.array([tuple(p) for p in ps])
    x0, y0 = np.floor(uv.min(0)).astype(int); x1, y1 = np.ceil(uv.max(0)).astype(int)
    if x1 - x0 > 300 or y1 - y0 > 300: continue
    xs, ys = np.meshgrid(np.arange(x0, x1 + 1), np.arange(y0, y1 + 1)); pts = np.stack([xs.ravel() + 0.5, ys.ravel() + 0.5], 1)
    Tm = np.array([[uv[0, 0] - uv[2, 0], uv[1, 0] - uv[2, 0]], [uv[0, 1] - uv[2, 1], uv[1, 1] - uv[2, 1]]])
    if abs(np.linalg.det(Tm)) < 1e-9: continue
    l12 = np.linalg.solve(Tm, (pts - uv[2]).T).T; L = np.column_stack([l12, 1 - l12.sum(1)]); ins = (L >= -0.02).all(1)
    if not ins.any(): continue
    q = L[ins] @ xyz; zc = Z0 + BEND * q[:, 0] ** 2                         # 둥근 목선: 옆으로 갈수록 높아짐
    p = pts[ins].astype(int); p[:, 0] = p[:, 0].clip(0, TW - 1); p[:, 1] = p[:, 1].clip(0, TH - 1)
    yy, xx = p[:, 1], p[:, 0]; cur = out[yy, xx]
    skin = (cur[:, 0] > cur[:, 1]) & (cur[:, 1] > cur[:, 2]) & (cur[:, 0] - cur[:, 2] > 0.06) & (cur[:, 0] > 0.18)   # 피부만 (재킷 깃은 그대로)
    w = np.clip((zc - q[:, 2]) / SOFT + 0.5, 0, 1) * (q[:, 1] < 0.03) * skin * (q[:, 2] > ZMIN) * (np.abs(q[:, 0]) > XMIN)
    shade = (cur.mean(1, keepdims=True) / max(cur.mean(), 1e-3)) ** 0.3          # 원래 그림자 조금 살림
    out[yy, xx] = cur * (1 - w[:, None]) + np.clip(COL * shade, 0, 1) * w[:, None]; n += int((w > 0).sum())
Image.fromarray((out * 255 + 0.5).clip(0, 255).astype(np.uint8)).save(os.path.join(texdir, head))
print("이너 칠한 그림 점", n, "→", os.path.join(texdir, head))
