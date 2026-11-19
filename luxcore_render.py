"""
사실적 렌더링 (사진 같은 정지 그림) — LuxCoreRender (오픈소스, Apache 2.0)
=====================================================================
빛이 실제로 튀고 퍼지는 것을 계산해 그림자 · 반사 · 은은한 바닥 빛이 사진처럼 나옵니다.
보고서 · PPT · 썸네일 같은 '정지 그림'용 (한 장에 CPU 4개 기준 2~5분). 카메라가 움직이는 영상은 블렌더 EEVEE.

설치 (한 번):  python3.12 -m venv .lux_venv && .lux_venv/bin/pip install pyluxcore numpy   (youtubeshot: .supertonic_venv 에 pip install pyluxcore)
사용:         .lux_venv/bin/python -I luxcore_render.py <장면.json> <결과.png> [--초 240] [--크기 1600x1200]

장면.json 예:
{
  "units": "mm",                              # 모델 단위 (mm 또는 m)
  "parts": [
    {"file": "stl/seat.stl",  "material": "wood_h"},
    {"file": "stl/legs.stl",  "material": "wood_v"},
    {"file": "stl/cushion.stl", "material": "fabric:#14403f"},
    {"file": "punch.stl", "material": "punch"},  # 금형 색: punch(파랑) · die(초록) · sheet(주황), 모두 무광
    {"file": "frame.stl", "material": "matte:#9aa3ad"}
  ],
  "camera": {"view": "front_left", "elevation": 22, "fov": 29},   # 생략하면 자동 (모델 크기에 맞춰 3/4 정면)
  "background": "#a39e97"                     # 스튜디오 배경 색 (바닥이 뒤 벽으로 둥글게 이어짐)
}
파일 경로는 장면.json 위치 기준. 모델은 z 가 위쪽.

재질: wood_v / wood_h (나무 결 세로 · 가로), wood_dark_v / wood_dark_h (월넛),
      fabric:#색 (거친 천), matte:#색 (무광 도장), plastic:#색 (살짝 광택), metal (무광 강철), metal_satin (은은한 금속),
      punch · die · sheet (금형 색 규칙, 무광), glass
"""
import json
import os
import struct
import sys
import time

import numpy as np
import pyluxcore


def hex_rgb(h, gamma=True):
    h = h.lstrip("#")
    c = np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)])
    return c ** 2.2 if gamma else c          # 화면 색(sRGB) → 계산용 선형 색


def read_mesh(p):
    """STL(바이너리 · 텍스트) 또는 PLY → 삼각형 (n, 3, 3)"""
    if p.lower().endswith(".ply"):
        return None
    b = open(p, "rb").read()
    if b[:5] == b"solid" and b"facet" in b[:400]:
        v = np.array([[float(x) for x in ln.split()[1:4]] for ln in b.decode(errors="ignore").splitlines()
                      if ln.strip().startswith("vertex")])
    else:
        n = struct.unpack("<I", b[80:84])[0]
        a = np.frombuffer(b[84:84 + n * 50], dtype=np.dtype([("n", "<3f4"), ("v", "<9f4"), ("a", "<u2")]))
        v = a["v"].reshape(-1, 3).astype(np.float64)
    return v.reshape(-1, 3, 3)


def write_ply(path, V, F, N=None):
    with open(path, "wb") as f:
        hdr = f"ply\nformat binary_little_endian 1.0\nelement vertex {len(V)}\nproperty float x\nproperty float y\nproperty float z\n"
        if N is not None:
            hdr += "property float nx\nproperty float ny\nproperty float nz\n"
        hdr += f"element face {len(F)}\nproperty list uchar int vertex_indices\nend_header\n"
        f.write(hdr.encode())
        f.write((np.hstack([V, N]) if N is not None else np.asarray(V)).astype("<f4").tobytes())
        rows = np.zeros(len(F), dtype=[("c", "u1"), ("i", "<3i4")]); rows["c"] = 3; rows["i"] = F
        f.write(rows.tobytes())


def tri_to_ply(tri, dst, crease=35):
    """같은 점은 합쳐 부드럽게, crease 도 넘게 꺾인 모서리는 날카롭게 (법선 분리)"""
    fn = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    ok = np.linalg.norm(fn, axis=1) > 1e-14
    tri, fn = tri[ok], fn[ok]
    fn /= np.linalg.norm(fn, axis=1, keepdims=True)
    key = np.round(tri.reshape(-1, 3) / 1e-6).astype(np.int64)
    _, inv = np.unique(key, axis=0, return_inverse=True)
    inv = inv.reshape(-1, 3)
    # 꼭짓점 각도만큼 가중 (가늘고 긴 삼각형이 많은 원통 옆면에서 줄무늬 음영이 생기지 않게)
    ang = np.zeros((len(tri), 3))
    for k in range(3):
        e1 = tri[:, (k + 1) % 3] - tri[:, k]; e2 = tri[:, (k + 2) % 3] - tri[:, k]
        c = np.einsum("ij,ij->i", e1, e2) / np.maximum(np.linalg.norm(e1, axis=1) * np.linalg.norm(e2, axis=1), 1e-18)
        ang[:, k] = np.arccos(np.clip(c, -1, 1))
    acc = np.zeros((inv.max() + 1, 3))
    np.add.at(acc, inv.ravel(), (fn[:, None, :] * ang[:, :, None]).reshape(-1, 3))
    avg = acc / np.maximum(np.linalg.norm(acc, axis=1, keepdims=True), 1e-12)
    cosc = np.cos(np.radians(crease))
    V, N, F, idx = [], [], [], {}
    for t in range(len(tri)):
        face = []
        for k in range(3):
            g = inv[t, k]
            smooth = np.dot(avg[g], fn[t]) > cosc
            kk = (g, None) if smooth else (g, t)
            if kk not in idx:
                idx[kk] = len(V); V.append(tri[t, k]); N.append(avg[g] if smooth else fn[t])
            face.append(idx[kk])
        F.append(face)
    write_ply(dst, np.array(V), np.array(F), np.array(N))


def backdrop(path, cx, cy, z0, w, depth, back_y, r, h, seg=32):
    """스튜디오 배경: 바닥(z0)이 back_y 에서 반지름 r 로 휘어 뒤 벽으로 이어짐"""
    prof = [(cy - depth, z0), (back_y - r, z0)]
    for i in range(1, seg + 1):
        a = np.pi / 2 * i / seg
        prof.append((back_y - r + r * np.sin(a), z0 + r - r * np.cos(a)))
    prof.append((back_y, z0 + h))
    V = [(x, y, z) for x in (cx - w / 2, cx + w / 2) for y, z in prof]
    n = len(prof)
    F = [f for i in range(n - 1) for f in ((i, n + i + 1, i + 1), (i, n + i, n + i + 1))]
    write_ply(path, np.array(V), np.array(F))


def panel_light(path, pos, target, sx, sz):
    """target 을 바라보는 사각 조명판 (양면)"""
    pos, target = np.array(pos, float), np.array(target, float)
    d = target - pos; d /= np.linalg.norm(d)
    right = np.cross(d, [0, 0, 1]); right /= max(np.linalg.norm(right), 1e-9)
    up = np.cross(right, d)
    V = [pos + right * a * sx / 2 + up * b * sz / 2 for a, b in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    write_ply(path, np.array(V), np.array([(0, 1, 2), (0, 2, 3), (0, 2, 1), (0, 3, 2)]))


WOOD = {"": ((0.36, 0.19, 0.08), (0.58, 0.35, 0.17)), "dark_": ((0.10, 0.05, 0.03), (0.24, 0.13, 0.07))}


def material_props(name, mat, size):
    """재질 이름 → LuxCore 설정 글. size = 모델 크기(m, 나무 결 굵기 맞춤)"""
    kind, _, col = mat.partition(":")
    s = []
    if kind.startswith("wood"):
        tone = "dark_" if "dark" in kind else ""
        vert = kind.endswith("_v")
        f = 70 * 0.5 / max(size, 1e-3)            # 의자(약 0.5 m) 기준 결 굵기
        tr = f"{f} 0 0 0  0 {f} 0 0  0 0 1.2 0  0 0 0 1" if vert else f"1.2 0 0 0  0 {f} 0 0  0 0 {f} 0  0 0 0 1"
        c1, c2 = WOOD[tone]
        s += [f'scene.textures.{name}_g.type = "blender_wood"', f'scene.textures.{name}_g.woodtype = "ringnoise"',
              f'scene.textures.{name}_g.noisebasis2 = "sin"', f'scene.textures.{name}_g.noisesize = 0.6',
              f'scene.textures.{name}_g.turbulence = 2.2', f'scene.textures.{name}_g.contrast = 0.9',
              f'scene.textures.{name}_g.mapping.type = "globalmapping3d"', f'scene.textures.{name}_g.mapping.transformation = {tr}',
              f'scene.textures.{name}_c.type = "mix"', f'scene.textures.{name}_c.texture1 = {c1[0]} {c1[1]} {c1[2]}',
              f'scene.textures.{name}_c.texture2 = {c2[0]} {c2[1]} {c2[2]}', f'scene.textures.{name}_c.amount = "{name}_g"',
              f'scene.materials.{name}.type = "glossy2"', f'scene.materials.{name}.kd = "{name}_c"',
              f'scene.materials.{name}.ks = 0.035 0.035 0.035', f'scene.materials.{name}.uroughness = 0.28',
              f'scene.materials.{name}.vroughness = 0.28']
        return s
    preset = {"punch": "#5b86c4", "die": "#4f9a6f", "sheet": "#e39a3b"}   # 금형 색 규칙 (상형 펀치 파랑 · 하형 다이 초록 · 판재 주황)
    if kind in preset:
        kind, col = "matte", preset[kind]
    c = hex_rgb(col) if col else np.array([0.6, 0.6, 0.6])
    cs = f"{c[0]:.4f} {c[1]:.4f} {c[2]:.4f}"
    if kind == "fabric":
        s += [f'scene.materials.{name}.type = "roughmatte"', f'scene.materials.{name}.kd = {cs}', f'scene.materials.{name}.sigma = 40']
    elif kind == "matte":
        s += [f'scene.materials.{name}.type = "roughmatte"', f'scene.materials.{name}.kd = {cs}', f'scene.materials.{name}.sigma = 15']
    elif kind == "plastic":
        s += [f'scene.materials.{name}.type = "glossy2"', f'scene.materials.{name}.kd = {cs}',
              f'scene.materials.{name}.ks = 0.05 0.05 0.05', f'scene.materials.{name}.uroughness = 0.15', f'scene.materials.{name}.vroughness = 0.15']
    elif kind in ("metal", "metal_satin"):
        r = 0.45 if kind == "metal" else 0.22
        s += [f'scene.materials.{name}.type = "metal2"', f'scene.materials.{name}.preset = "aluminium"',
              f'scene.materials.{name}.uroughness = {r}', f'scene.materials.{name}.vroughness = {r}']
    elif kind == "glass":
        s += [f'scene.materials.{name}.type = "roughglass"', f'scene.materials.{name}.uroughness = 0.02', f'scene.materials.{name}.vroughness = 0.02']
    else:
        raise SystemExit(f"모르는 재질: {mat}")
    return s


def main(a):
    if len(a) < 2:
        print(__doc__); return 2
    scene_f, out_png = os.path.abspath(a[0]), os.path.abspath(a[1])
    secs = float(a[a.index("--초") + 1]) if "--초" in a else 240
    W, H = map(int, a[a.index("--크기") + 1].split("x")) if "--크기" in a else (1600, 1200)
    cfg = json.load(open(scene_f, encoding="utf-8"))
    base = os.path.dirname(scene_f)
    scale = 0.001 if cfg.get("units", "mm") == "mm" else 1.0
    work = os.path.splitext(out_png)[0] + "_lux"; os.makedirs(work, exist_ok=True)

    # 모델 → PLY, 전체 크기
    lo, hi, objs = np.full(3, 1e9), np.full(3, -1e9), []
    for i, p in enumerate(cfg["parts"]):
        src = os.path.join(base, p["file"])
        tri = read_mesh(src)
        if tri is None:
            raise SystemExit("PLY 는 STL 로 바꿔 넣으세요: " + src)
        tri = tri * scale
        lo, hi = np.minimum(lo, tri.reshape(-1, 3).min(0)), np.maximum(hi, tri.reshape(-1, 3).max(0))
        dst = os.path.join(work, f"p{i}.ply"); tri_to_ply(tri, dst)
        objs.append((f"p{i}", dst, p.get("material", "matte:#9aa3ad")))
    ctr, size = (lo + hi) / 2, hi - lo
    R = float(np.linalg.norm(size)) / 2

    # 카메라: 3/4 정면 위에서 (view: front_left / front_right / front)
    cam = cfg.get("camera", {})
    fov = cam.get("fov", 29)
    az = {"front_left": -36.7, "front_right": 36.7, "front": 0}.get(cam.get("view", "front_left"), -36.7)
    el = np.radians(cam.get("elevation", 20))
    dist = R / np.sin(np.radians(fov) / 2) * cam.get("zoom", 1.0) * (1.25 if W >= H else 1.6)   # 그림 가로 · 세로 중 짧은 쪽에 맞춤
    dirv = np.array([np.sin(np.radians(az)) * np.cos(el), -np.cos(np.radians(az)) * np.cos(el), np.sin(el)])
    target = ctr.copy()
    orig = target + dirv * dist
    if "orig" in cam:
        orig, target = np.array(cam["orig"]), np.array(cam["target"])
        dist = float(np.linalg.norm(orig - target))

    # 배경 · 조명 (모델 크기에 맞춤)
    S = max(size[0], size[1], size[2])
    backdrop(os.path.join(work, "bg.ply"), ctr[0], ctr[1], lo[2], 14 * S, 8 * S, hi[1] + 1.6 * S, 2.4 * S, 7 * S)
    panel_light(os.path.join(work, "key.ply"), ctr + np.array([-3.2, -3.6, 3.0]) * S, ctr, 3.2 * S, 3.2 * S)
    panel_light(os.path.join(work, "rim.ply"), ctr + np.array([3.8, 2.0, 2.4]) * S, ctr, 1.6 * S, 2.4 * S)
    gain = 9.0                                   # 조명판 크기가 모델에 비례하므로 밝기는 그대로

    bg = hex_rgb(cfg.get("background", "#a39e97"))
    scn = [f"scene.camera.type = \"perspective\"",
           f"scene.camera.lookat.orig = {orig[0]} {orig[1]} {orig[2]}",
           f"scene.camera.lookat.target = {target[0]} {target[1]} {target[2]}",
           "scene.camera.up = 0 0 1", f"scene.camera.fieldofview = {fov}",
           f"scene.camera.lensradius = {0.004 * S / 0.9}", f"scene.camera.focaldistance = {dist}",
           'scene.materials.bg.type = "roughmatte"', f"scene.materials.bg.kd = {bg[0]} {bg[1]} {bg[2]}", "scene.materials.bg.sigma = 15",
           'scene.materials.keyl.type = "matte"', "scene.materials.keyl.kd = 0 0 0",
           "scene.materials.keyl.emission = 1.0 0.96 0.90", f"scene.materials.keyl.emission.gain = {gain} {gain} {gain}",
           'scene.materials.riml.type = "matte"', "scene.materials.riml.kd = 0 0 0",
           "scene.materials.riml.emission = 0.90 0.95 1.0", f"scene.materials.riml.emission.gain = {gain * 0.66} {gain * 0.66} {gain * 0.66}",
           'scene.lights.fill.type = "constantinfinite"', "scene.lights.fill.color = 0.85 0.88 0.95", "scene.lights.fill.gain = 0.35 0.35 0.35"]
    mats = {}
    for nm, ply, mat in objs:
        if mat not in mats:
            mats[mat] = f"m{len(mats)}"
            scn += material_props(mats[mat], mat, S)
        scn += [f'scene.shapes.{nm}.type = "mesh"', f'scene.shapes.{nm}.ply = "{ply}"',
                f'scene.objects.{nm}.shape = "{nm}"', f'scene.objects.{nm}.material = "{mats[mat]}"']
    for nm, m in (("bg", "bg"), ("key", "keyl"), ("rim", "riml")):
        scn += [f'scene.shapes.{nm}.type = "mesh"', f'scene.shapes.{nm}.ply = "{os.path.join(work, nm + ".ply")}"',
                f'scene.objects.{nm}.shape = "{nm}"', f'scene.objects.{nm}.material = "{m}"']

    pyluxcore.Init(lambda msg: None)
    props = pyluxcore.Properties(); props.SetFromString("\n".join(scn))
    scene = pyluxcore.Scene(); scene.Parse(props)
    rc = pyluxcore.Properties()
    rc.SetFromString(f"""
renderengine.type = "PATHCPU"
sampler.type = "SOBOL"
path.pathdepth.total = 8
path.pathdepth.diffuse = 4
path.pathdepth.glossy = 4
path.clamping.variance.maxvalue = 10
film.width = {W}
film.height = {H}
film.filter.type = "BLACKMANHARRIS"
film.outputs.0.type = "RGB_IMAGEPIPELINE"
film.outputs.0.filename = "{out_png}"
film.outputs.1.type = "ALBEDO"
film.outputs.1.filename = "{os.path.join(work, 'albedo.exr')}"
film.outputs.2.type = "AVG_SHADING_NORMAL"
film.outputs.2.filename = "{os.path.join(work, 'normal.exr')}"
film.imagepipelines.0.0.type = "INTEL_OIDN"
film.imagepipelines.0.1.type = "TONEMAP_LINEAR"
film.imagepipelines.0.1.scale = 1.0
film.imagepipelines.0.2.type = "GAMMA_CORRECTION"
film.imagepipelines.0.2.value = 2.2
batch.halttime = {secs}
""")
    session = pyluxcore.RenderSession(pyluxcore.RenderConfig(rc, scene))
    t0 = time.time(); session.Start()
    while not session.HasDone():
        time.sleep(10); session.UpdateStats()
        print(f"  {time.time() - t0:4.0f}초 / {secs:g}초", flush=True)
    session.Stop(); session.GetFilm().SaveOutputs()
    print("완료:", out_png)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
