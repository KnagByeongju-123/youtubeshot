"""GLB 인물의 목 옆·셔츠 깃 사이 어두운 틈(재킷 안쪽이 비쳐 검게 보이는 곳)을 셔츠 흰색으로 칠함 (사용자 2026-11-28 '여기 부분 메워줘', 여자아나운서3)
   칸(세상 좌표, 블렌더: x 좌우, y 앞-·뒤+, z 위)을 --칸 x0,x1,z0,z1 로 주고(양쪽 대칭이면 |x| 기준), 그 안의 얼굴 앞쪽 면 중 겉면 그림이
   어두운(밝기 < --어두움) 면의 그림 칸을 --색 으로 칠함 (그림이 조각조각인 Meshy 모델도 면마다 UV 삼각형을 칠함). --보기 면 빨갛게 칠해 자리 확인
   사용: .bpy_venv/bin/python -I 애니3D/목옆메우기.py <입력.glb> <출력.glb> --칸 0.03,0.08,0.50,0.56 [--앞 0.04] [--어두움 0.25] [--색 236,236,240] [--대칭] [--보기]"""
import sys
import bpy
import numpy as np
import cv2

a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
src, dst = a[0], a[1]
def opt(k, d): return a[a.index(k) + 1] if k in a else d
x0, x1, z0, z1 = (float(v) for v in opt("--칸", "0.03,0.08,0.50,0.56").split(","))
FRONT, DARK = float(opt("--앞", "0.04")), float(opt("--어두움", "0.25"))
COL = np.array([float(v) for v in opt("--색", "236,236,240").split(",")]) / 255
if "--보기" in a: COL = np.array([1.0, 0.0, 0.0])
SYM = "--대칭" in a
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
o = max((o for o in bpy.data.objects if o.type == "MESH"), key=lambda o: len(o.data.vertices))
me = o.data; M = np.array(o.matrix_world)
W = np.array([v.co for v in me.vertices]) @ M[:3, :3].T + M[:3, 3]
mat = o.material_slots[0].material
bs = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
nd = bs.inputs["Base Color"].links[0].from_node
while nd.type != "TEX_IMAGE": nd = next(i.links[0].from_node for i in nd.inputs if i.links)
img = nd.image; w_, h_ = img.size
px = np.zeros(w_ * h_ * 4, np.float32); img.pixels.foreach_get(px); px = px.reshape(h_, w_, 4)
uvl = me.uv_layers.active.data
neck = (np.abs(W[:, 0]) < 0.02) & (W[:, 2] > z0) & (W[:, 2] < z1)
yfront = np.percentile(W[neck, 1], 5) if neck.any() else W[:, 1].min()
mask = np.zeros((h_, w_), np.uint8); n = 0
for p in me.polygons:
    c = W[list(p.vertices)].mean(0)
    xx = abs(c[0]) if SYM else c[0]
    if not (x0 <= xx <= x1 and z0 <= c[2] <= z1 and c[1] < yfront + FRONT): continue
    uv = np.array([[uvl[li].uv[0] * w_, uvl[li].uv[1] * h_] for li in p.loop_indices])
    cc = uv.mean(0).astype(int); cc = np.clip(cc, 0, [w_ - 1, h_ - 1])
    if px[cc[1], cc[0], :3].mean() >= DARK: continue
    cv2.fillConvexPoly(mask, uv.astype(np.int32), 1); n += 1
mask = cv2.dilate(mask, np.ones((3, 3), np.uint8)).astype(bool)
shade = np.clip(px[..., :3].mean(2) / max(1e-3, px[mask, :3].mean()), 0.85, 1.05)[..., None] if "--보기" not in a else 1.0
px[mask, :3] = (COL * (shade if np.ndim(shade) == 0 else shade[mask]))
img.pixels.foreach_set(px.ravel()); img.pack()
print("칠한 면", n, "그림 점", int(mask.sum()), "목 앞 y %.3f" % yfront)
bpy.ops.export_scene.gltf(filepath=dst, export_format="GLB", export_skins=True, export_morph=True, export_animations=False, export_image_format="AUTO")
print("→", dst)
