"""입체 블록 장면(블록장면3D 의 .json)을 Blender 로 그림 — 진짜 햇빛·그림자·하늘빛 (그래픽카드 없이)

쓰는 법 (Blender 파이썬 = .bl_venv, 파이썬 3.11 + bpy):
  xvfb-run -a .bl_venv/bin/python -X utf8 블록_블렌더.py <장면.json> <초> <결과.png> [--길이 8] [--엔진 eevee|cycles]
  xvfb-run -a .bl_venv/bin/python -X utf8 블록_블렌더.py --일꾼     ← 영상 프로그램이 한 줄씩 주문: {"scene","t","dur","out"} → "ok"

좌표: 블록 엔진은 y 가 위, Blender 는 z 가 위 → (x, y, z) → (x, -z, y)
색: 상자마다 색(그대로), 스스로 빛나는 상자(emit)는 빛을 냄. 바깥 선 대신 햇빛 그림자·주변광 가림(AO)으로 블록이 또렷하게
"""
import json
import math
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import importlib.util

import bpy

_sp = importlib.util.spec_from_file_location("bs3", os.path.join(HERE, "블록장면3D.py"))
S3 = importlib.util.module_from_spec(_sp)
_sp.loader.exec_module(S3)
E = S3.E
from PIL import Image

W, H = 1920, 1080
SCALE = int(os.environ.get("BL_SCALE", "100"))   # 그리는 크기 % (50 = 960×540 로 그리고 1920×1080 으로 키움 — 4배 빠름)
FACES = np.array(E.FACES)          # 상자 한 개의 면 6개 (꼭짓점 번호 4개씩)


def yup(v):
    """블록 좌표(y 위) → Blender 좌표(z 위)"""
    v = np.asarray(v, float)
    return np.stack([v[..., 0], -v[..., 2], v[..., 1]], -1)


def srgb2lin(c):
    c = np.asarray(c, float) / 255.0
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


_STATE = {}


def setup(engine="eevee", samples=None):
    """빈 장면 + 재료 + 해 + 카메라 (한 번만)"""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = W, H, SCALE
    sc.render.image_settings.file_format = "PNG"
    sc.view_settings.view_transform = "Standard"     # 색이 블록 엔진 색 그대로 나오게 (Filmic·AgX 는 색이 바램)
    sc.view_settings.look = "None"
    if engine == "cycles":
        sc.render.engine = "CYCLES"
        sc.cycles.device = "CPU"
        sc.cycles.samples = samples or 24
        sc.cycles.use_denoising = True
        for k, v in (("denoiser", "OPENIMAGEDENOISE"), ("denoising_prefilter", "FAST"), ("denoising_quality", "FAST"), ("denoising_input_passes", "RGB_ALBEDO")):
            if hasattr(sc.cycles, k):
                try:
                    setattr(sc.cycles, k, v)
                except Exception:  # noqa
                    pass
        sc.cycles.max_bounces = 2
        sc.cycles.diffuse_bounces, sc.cycles.glossy_bounces, sc.cycles.transmission_bounces = 2, 0, 0
        sc.cycles.caustics_reflective = sc.cycles.caustics_refractive = False
        sc.cycles.use_adaptive_sampling = True
        sc.render.use_persistent_data = True
        th = int(os.environ.get("BL_THREADS", "0"))     # 일꾼 여럿을 동시에 돌릴 때 CPU 를 나눠 씀
        sc.render.threads_mode = "FIXED" if th else "AUTO"
        if th:
            sc.render.threads = th
    else:
        sc.render.engine = "BLENDER_EEVEE_NEXT"
        ee = sc.eevee
        ee.taa_render_samples = samples or 16
        for k, v in (("use_shadows", True), ("use_gtao", True), ("gtao_distance", 1.2), ("shadow_ray_count", 1), ("shadow_step_count", 6)):
            if hasattr(ee, k):
                setattr(ee, k, v)
    # 재료: 상자 색(꼭짓점 색 'col') + 알파 칸에 빛남 정도
    m = bpy.data.materials.new("blok")
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    at = nt.nodes.new("ShaderNodeAttribute"); at.attribute_name = "col"; at.attribute_type = "GEOMETRY"
    bs = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bs.inputs["Roughness"].default_value = 0.85
    if "Specular IOR Level" in bs.inputs:
        bs.inputs["Specular IOR Level"].default_value = 0.15
    nt.links.new(at.outputs["Color"], bs.inputs["Base Color"])
    nt.links.new(at.outputs["Color"], bs.inputs["Emission Color"])
    mul = nt.nodes.new("ShaderNodeMath"); mul.operation = "MULTIPLY"; mul.inputs[1].default_value = 2.5
    nt.links.new(at.outputs["Alpha"], mul.inputs[0])
    nt.links.new(mul.outputs[0], bs.inputs["Emission Strength"])
    nt.links.new(bs.outputs[0], out.inputs[0])
    if hasattr(m, "cycles") and hasattr(m.cycles, "emission_sampling"):
        m.cycles.emission_sampling = "NONE"     # 빛나는 상자는 보이기만, 둘레를 비추는 빛으로 세지 않음 (모든 면을 빛으로 세면 몇 배 느림)
    me = bpy.data.meshes.new("blok")
    ob = bpy.data.objects.new("blok", me)
    sc.collection.objects.link(ob)
    me.materials.append(m)
    # 해
    sun = bpy.data.lights.new("sun", "SUN")
    sun.energy, sun.angle = 3.2, math.radians(4)
    so = bpy.data.objects.new("sun", sun)
    sc.collection.objects.link(so)
    # 카메라
    cd = bpy.data.cameras.new("cam")
    cd.sensor_fit = "VERTICAL"
    cd.clip_start, cd.clip_end = 0.1, 2000
    co = bpy.data.objects.new("cam", cd)
    sc.collection.objects.link(co)
    sc.camera = co
    # 하늘: 카메라에 보이는 배경 = 위→아래 색, 땅을 비추는 빛 = 하늘색 약하게
    w = bpy.data.worlds.new("sky")
    sc.world = w
    w.use_nodes = True
    wn = w.node_tree
    for n in list(wn.nodes):
        wn.nodes.remove(n)
    wo = wn.nodes.new("ShaderNodeOutputWorld")
    lp = wn.nodes.new("ShaderNodeLightPath")
    tc = wn.nodes.new("ShaderNodeTexCoord")
    sep = wn.nodes.new("ShaderNodeSeparateXYZ")
    wn.links.new(tc.outputs["Generated"], sep.inputs[0])
    ramp = wn.nodes.new("ShaderNodeValToRGB")
    mr = wn.nodes.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value, mr.inputs["From Max"].default_value = -0.05, 0.45
    wn.links.new(sep.outputs["Z"], mr.inputs["Value"])
    wn.links.new(mr.outputs["Result"], ramp.inputs["Fac"])
    bg_cam = wn.nodes.new("ShaderNodeBackground")
    wn.links.new(ramp.outputs["Color"], bg_cam.inputs["Color"])
    bg_amb = wn.nodes.new("ShaderNodeBackground")
    bg_amb.inputs["Strength"].default_value = 0.9
    mix = wn.nodes.new("ShaderNodeMixShader")
    wn.links.new(lp.outputs["Is Camera Ray"], mix.inputs["Fac"])
    wn.links.new(bg_amb.outputs[0], mix.inputs[1])
    wn.links.new(bg_cam.outputs[0], mix.inputs[2])
    wn.links.new(mix.outputs[0], wo.inputs[0])
    _STATE.update(sc=sc, me=me, ob=ob, sun=so, cam=co, ramp=ramp, amb=bg_amb, engine=engine)


def set_sky(top, bottom, tint=None):
    ramp = _STATE["ramp"].color_ramp
    lt, lb = srgb2lin(top), srgb2lin(bottom)
    ramp.elements[0].color = (*lb, 1)      # 지평선 쪽
    ramp.elements[1].color = (*lt, 1)      # 하늘 위
    amb = (lt * 0.6 + lb * 0.4)
    _STATE["amb"].inputs["Color"].default_value = (*amb, 1)


def load_boxes(boxes):
    """상자 목록 → 한 덩어리 메쉬 (상자마다 꼭짓점 8, 면 6)"""
    me = _STATE["me"]
    me.clear_geometry()
    n = len(boxes)
    if n == 0:
        return
    V = np.empty((n, 8, 3))
    C = np.empty((n, 4))
    for i, b in enumerate(boxes):
        V[i] = b.corners()
        c = srgb2lin(np.clip(b.col, 0, 255))
        C[i, :3], C[i, 3] = c, (1.0 if b.emit else 0.0)
    verts = yup(V).reshape(-1, 3)
    faces = (FACES[None, :, :] + (np.arange(n) * 8)[:, None, None]).reshape(-1, 4)
    me.vertices.add(len(verts))
    me.vertices.foreach_set("co", verts.astype(np.float32).ravel())
    me.loops.add(len(faces) * 4)
    me.loops.foreach_set("vertex_index", faces.astype(np.int32).ravel())
    me.polygons.add(len(faces))
    me.polygons.foreach_set("loop_start", (np.arange(len(faces)) * 4).astype(np.int32))
    me.update(calc_edges=True)
    # 면 방향: 블록 엔진의 면 순서가 바깥을 보게 되어 있지 않을 수도 있음 → 법선을 바깥쪽으로 맞춤
    if not _STATE.get("flip_checked"):
        _STATE["flip"] = _need_flip(verts, faces)
        _STATE["flip_checked"] = True
    if _STATE["flip"]:
        me.flip_normals()
    ca = me.color_attributes.new("col", "FLOAT_COLOR", "CORNER")
    cc = np.repeat(np.repeat(C, 6, 0), 4, 0)
    ca.data.foreach_set("color", cc.astype(np.float32).ravel())


def _need_flip(verts, faces):
    p = verts[faces[0]]
    n = np.cross(p[1] - p[0], p[3] - p[0])
    ctr = verts[:8].mean(0)
    return float(np.dot(n, p.mean(0) - ctr)) < 0


def set_camera(cam):
    co = _STATE["cam"]
    pos = yup(cam.pos)
    f = yup(cam.f)
    co.location = tuple(pos)
    # 카메라는 -Z 를 바라봄, 위는 +Y → 바라보는 방향 f 와 위(z) 로 회전 만들기
    import mathutils
    d = mathutils.Vector(tuple(f))
    co.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    if cam.ortho:
        co.data.type = "ORTHO"
        co.data.ortho_scale = cam.ortho * W / H
    else:
        co.data.type = "PERSP"
        fov = 2 * math.atan((H * E.SS / 2) / cam.focal)
        co.data.angle = fov


def set_sun():
    L = np.array(E.LIGHT, float)            # 빛이 오는 쪽 (블록 좌표)
    d = -yup(L)                             # 빛이 나아가는 방향
    import mathutils
    _STATE["sun"].rotation_euler = mathutils.Vector(tuple(d)).to_track_quat("-Z", "Y").to_euler()


def frame(scene, cast, t, dur, out):
    B = S3.build(scene, cast, t, dur)
    mood = B["mood"]
    o, fx, pr = B["o"], B["fx"], B["pr"]
    md = S3.MOOD.get(mood)
    if md:
        set_sky(md[0], md[1])
    elif mood == "plain":
        set_sky(o.get("c2", (122, 143, 168)), o.get("c1", (43, 58, 82)))
    else:
        set_sky((40, 36, 34), (40, 36, 34))
    load_boxes(B["boxes"])
    set_camera(B["cam"])
    set_sun()
    sc = _STATE["sc"]
    sc.render.filepath = out
    bpy.ops.render.render(write_still=True)
    # 블록 엔진과 같은 색 효과(밤·과거·빛·처음 어둠에서)
    img = Image.open(out).convert("RGB")
    if img.size != (W, H):
        img = img.resize((W, H), Image.LANCZOS)
    tint = md[4] if md else None
    if o.get("night"):
        tint = (20, 30, 80, 0.35)
    if tint:
        img = Image.blend(img, Image.new("RGB", img.size, tint[:3]), tint[3])
    if "dark" in fx:
        img = Image.blend(img, Image.new("RGB", img.size, (5, 7, 15)), 0.35)
    if "past" in fx:
        img = Image.blend(img, Image.new("RGB", img.size, (200, 168, 120)), 0.25)
    if "glow" in fx:
        img = Image.blend(img, Image.new("RGB", img.size, (255, 246, 208)), min(0.9, pr ** 2 * 1.1))
    if "fade_in" in fx and t < 1.2:
        img = Image.blend(Image.new("RGB", img.size, (0, 0, 0)), img, t / 1.2)
    img.save(out)
    return img


_CACHE = {}


def load(path):
    st = os.stat(path).st_mtime
    k = (path, st)
    if k not in _CACHE:
        _CACHE.clear()
        _CACHE[k] = S3.load(path)
    return _CACHE[k]


def main():
    a = sys.argv[1:]
    eng = "eevee"
    if "--엔진" in a:
        i = a.index("--엔진"); eng = a[i + 1]; del a[i:i + 2]
    smp = None
    if "--샘플" in a:
        i = a.index("--샘플"); smp = int(a[i + 1]); del a[i:i + 2]
    dur = 8.0
    if "--길이" in a:
        i = a.index("--길이"); dur = float(a[i + 1]); del a[i:i + 2]
    setup(eng, smp)
    if a and a[0] == "--일꾼":
        print("ready", flush=True)
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            try:
                q = json.loads(line)
                scene, cast = load(q["scene"])
                frame(scene, cast, float(q["t"]), float(q.get("dur") or dur), q["out"])
                print("ok", flush=True)
            except Exception as e:  # noqa
                print("err " + repr(e).replace("\n", " "), flush=True)
        return
    path, t, out = a[0], float(a[1]), a[2]
    scene, cast = load(path)
    t0 = time.time()
    frame(scene, cast, t, dur, out)
    print(f"{out}  {time.time() - t0:.1f}초", flush=True)


if __name__ == "__main__":
    main()
