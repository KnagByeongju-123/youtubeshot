"""GLB 사람 모델의 아랫입술을 얇게 — 아랫입술 아래 가장자리를 입술선 쪽으로 올리고, 앞으로 도톰한 것을 뒤로 조금 (사용자 2026-11-28 '아랫입술이 좀 도톰한 것 같아', 여자아나운서5)
   - 입술선 높이·입 가운데·입 반너비: 얼굴 앞 점들의 겉면 색(붉은 정도)으로 찾음 (그림이 조각조각인 Meshy 모델도 점마다 UV 로 색을 읽음)
   - 입술선 아래 --폭 m 띠의 점을 입술선 쪽으로 (1-높이) 배 당기고(턱 쪽으로 갈수록 덜), 앞으로 나온 것은 --뒤로 배만큼 뒤로. 입꼬리로 갈수록 0(타원)
   - 모든 모양 키(입 모양·눈 감기)도 같은 양만큼 → 립싱크 그대로
   사용: .bpy_venv/bin/python -I 애니3D/아랫입술얇게.py <입력.glb> <출력.glb> [--높이 0.8] [--뒤로 0.4] [--폭 0.016]"""
import sys
import bpy
import numpy as np

a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
src, dst = a[0], a[1]
def opt(k, d): return float(a[a.index(k) + 1]) if k in a else d
KZ, KB, BAND = opt("--높이", 0.8), opt("--뒤로", 0.4), opt("--폭", 0.016)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
o = max((o for o in bpy.data.objects if o.type == "MESH"), key=lambda o: len(o.data.vertices))
me = o.data; M = np.array(o.matrix_world); Mi3 = np.linalg.inv(M[:3, :3])
co = np.zeros(len(me.vertices) * 3); me.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
W = co @ M[:3, :3].T + M[:3, 3]            # 블렌더 세상: x 좌우, y 앞(-)뒤(+), z 위
mat = o.material_slots[0].material
bs = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
nd = bs.inputs["Base Color"].links[0].from_node
while nd.type != "TEX_IMAGE": nd = next(i.links[0].from_node for i in nd.inputs if i.links)
img = nd.image; w_, h_ = img.size
px = np.zeros(w_ * h_ * 4, np.float32); img.pixels.foreach_get(px); px = px.reshape(h_, w_, 4)[..., :3]
uvl = me.uv_layers.active.data
col = np.zeros((len(W), 3)); cnt = np.zeros(len(W))
for p in me.polygons:
    for li in p.loop_indices:
        vi = me.loops[li].vertex_index; u, v = uvl[li].uv
        col[vi] += px[int(np.clip(v, 0, 0.9999) * h_), int(np.clip(u % 1, 0, 0.9999) * w_)]; cnt[vi] += 1
col /= np.maximum(cnt, 1)[:, None]
red = col[:, 0] - (col[:, 1] + col[:, 2]) / 2                        # 붉은 정도(입술)
# 얼굴 앞, 코 아래·턱 위 띠에서 붉은 점 = 입술
head = (W[:, 2] > W[:, 2].max() - 0.32) & (W[:, 2] < W[:, 2].max() - 0.18)    # 코 아래~턱 높이 띠
hc = head & (np.abs(W[:, 0]) < 0.03)
front = W[:, 1] < np.percentile(W[hc, 1], 3) + 0.02
cand = front & head & (np.abs(W[:, 0]) < 0.05)
lip = cand & (red > np.percentile(red[cand], 85))
zl = W[lip, 2]; zc = np.median(zl)
lip &= np.abs(W[:, 2] - zc) < 0.02
xs = W[lip, 0]; cx = (np.percentile(xs, 2) + np.percentile(xs, 98)) / 2; hw = (np.percentile(xs, 98) - np.percentile(xs, 2)) / 2
# 입술선 = 입술 점 중 가운데 띠에서 가장 어두운(붉고 어두운) 높이
mid = lip & (np.abs(W[:, 0] - cx) < hw * 0.5)
dark = col[:, :].mean(1)
zz = W[mid, 2]; order = np.argsort(dark[mid])
zline = np.median(zz[order[:max(5, len(order) // 8)]])
lower = lip & (W[:, 2] < zline)
zbot = np.percentile(W[lower, 2], 5)
print("입 가운데 x %.4f 반너비 %.4f, 입술선 z %.4f, 아랫입술 아래 z %.4f (두께 %.1fmm)" % (cx, hw, zline, zbot, (zline - zbot) * 1000))
y0 = np.percentile(W[lower, 1], 50)                                    # 아랫입술 앞면
def move(P):
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    e = np.clip(1 - ((x - cx) / (hw * 1.15)) ** 2, 0, 1)               # 입꼬리 0 → 가운데 1
    t = np.clip((zline - z) / (zline - zbot), 0, None)                 # 입술선 0 → 아랫입술 끝 1 → 그 아래
    fall = np.where(t <= 1, 1.0, np.clip(1 - (t - 1) / ((BAND) / max(1e-4, zline - zbot)), 0, 1))
    dz = np.where(z < zline, (zline - z) * (1 - KZ) * np.minimum(t, 1) * 0 + (zline - zbot) * (1 - KZ) * np.minimum(t, 1), 0) * fall * e
    dyb = np.clip(y0 + 0.002 - y, 0, None) * KB * (z < zline) * fall * e    # 앞으로 도톰한 만큼 뒤로
    Q = P.copy(); Q[:, 2] = z + dz; Q[:, 1] = y + dyb
    return Q
sel = front & head & (np.abs(W[:, 0] - cx) < hw * 1.3) & (W[:, 2] < zline + 0.002) & (W[:, 2] > zbot - BAND - 0.01)
def apply(arr):
    Wd = arr @ M[:3, :3].T + M[:3, 3]; Wn = Wd.copy(); Wn[sel] = move(Wd[sel])
    return (Wn - M[:3, 3]) @ Mi3.T
nb = apply(co)
for kb in (me.shape_keys.key_blocks if me.shape_keys else []):
    arr = np.zeros(len(co) * 3); kb.data.foreach_get("co", arr); kb.data.foreach_set("co", apply(arr.reshape(-1, 3)).ravel())
me.vertices.foreach_set("co", nb.ravel()); me.update()
print("옮긴 점", int(sel.sum()), "최대 %.1fmm" % (np.linalg.norm(nb - co, axis=1).max() * 1000))
bpy.ops.export_scene.gltf(filepath=dst, export_format="GLB", export_skins=True, export_morph=True, export_animations=False, export_image_format="AUTO")
print("→", dst)
