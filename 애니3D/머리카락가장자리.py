"""머리카락 그림(opacity_color, 투명도)의 가장자리를 부드럽게 — 판 모양 머리카락의 칼로 자른 듯한 경계를 가닥처럼 흐리게 (사용자 2026-11-28 '머리카락 가장자리는 부드럽게, 머리가 단정해 보이게')
   - 불투명한 곳 안쪽으로 --폭 px 동안 투명도를 0→1 로 (거리 변환), 가장자리엔 가는 가닥 무늬(한 방향으로 늘인 잡음)를 곱해 끝이 가닥처럼
   - 그림만 바꿈. GLB 에 바로 넣으려면 --glb <입력.glb> <출력.glb> (재질 이름에 --재질 글자가 든 그림을 바꿔 끼움)
   사용: python 애니3D/머리카락가장자리.py <opacity.tga> <출력.tga> [--폭 14] [--가닥 0.6]
         .bpy_venv/bin/python -I 애니3D/머리카락가장자리.py --glb <입력.glb> <출력.glb> --재질 f008_opacity,f003_opacity [--폭 14]"""
import sys
import numpy as np, cv2

a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
def opt(k, d): return a[a.index(k) + 1] if k in a else d
WID, STR = float(opt("--폭", "14")), float(opt("--가닥", "0.6"))

def soften(rgba):
    """rgba: H×W×4 float 0~1 (Blender 순서: 아래가 0행) → 가장자리 부드럽게"""
    al = rgba[..., 3]
    solid = (al > 0.5).astype(np.uint8)
    dist = cv2.distanceTransform(solid, cv2.DIST_L2, 5)
    ramp = np.clip(dist / WID, 0, 1)
    rng = np.random.default_rng(7)
    nz = rng.random(al.shape).astype(np.float32)
    nz = np.maximum(cv2.GaussianBlur(nz, (0, 0), sigmaX=0.6, sigmaY=6), cv2.GaussianBlur(nz, (0, 0), sigmaX=6, sigmaY=0.6))  # 가는 가닥 무늬(세로·가로)
    nz = (nz - nz.min()) / (np.ptp(nz) + 1e-6)
    edge = 1 - ramp
    strand = np.clip(ramp + edge * (nz * 1.6 - 0.3) * STR + edge * (1 - STR) * ramp, 0, 1)
    new = al * np.where(solid > 0, np.clip(ramp ** 0.8 * (1 - STR) + strand * STR, 0, 1), 1.0)
    new = cv2.GaussianBlur(new, (0, 0), 0.8)
    out = rgba.copy(); out[..., 3] = np.minimum(al, new)
    # 가장자리 색은 살짝 짙게(빛에 하얗게 뜨지 않게)
    out[..., :3] *= (0.85 + 0.15 * ramp)[..., None]
    return out

if "--glb" in a:
    import bpy
    i = a.index("--glb"); src, dst = a[i + 1], a[i + 2]
    mats = opt("--재질", "opacity").split(",")
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=src)
    done = set()
    for m in bpy.data.materials:
        if not any(k in m.name for k in mats) or not m.node_tree: continue
        bs = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        nd = bs.inputs["Base Color"].links[0].from_node if bs.inputs["Base Color"].links else None
        while nd is not None and nd.type != "TEX_IMAGE":
            nd = next((i.links[0].from_node for i in nd.inputs if i.links), None)
        if nd is None or nd.image.name in done: continue
        img = nd.image; w, h = img.size
        px = np.zeros(w * h * 4, np.float32); img.pixels.foreach_get(px)
        img.pixels.foreach_set(soften(px.reshape(h, w, 4)).ravel()); img.pack(); done.add(img.name)
        print("가장자리 부드럽게:", m.name, img.name)
    bpy.ops.export_scene.gltf(filepath=dst, export_format="GLB", export_morph=True, export_skins=True, export_animations=False, export_image_format="AUTO")
    print("→", dst)
else:
    from PIL import Image
    src, dst = a[0], a[1]
    im = np.array(Image.open(src)).astype(np.float32) / 255
    out = soften(im[::-1])[::-1]
    Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8)).save(dst)
    print("→", dst)
