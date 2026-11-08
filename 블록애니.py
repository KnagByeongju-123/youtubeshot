# -*- coding: utf-8 -*-
"""블록애니 — Blender(bpy, 오픈소스 GPL)로 블록 캐릭터를 만들고 움직여 영상으로 뽑는 도구.

준비(한 번): python3.11 -m venv .blender_venv && .blender_venv/bin/pip install bpy pillow
실행은 반드시 가상 화면 위에서 (그래픽카드가 없어서 xvfb 의 소프트웨어 그래픽을 씀):

  # 캐릭터 시트(앞·옆·옆·뒤 4장, 한 사람당 한 줄)
  xvfb-run -a .blender_venv/bin/python 블록애니.py 시트 블록애니/캐릭터.json 결과.png [--이름 도윤,강철]

  # 장면 영상(장면 파일에 인물·동작·카메라를 적음 — 아래 '장면 파일' 참고)
  xvfb-run -a .blender_venv/bin/python 블록애니.py 장면 블록애니/장면_예시.json 결과.mp4 [--고급]

  기본 촬영은 Workbench(한 장 1초 안팎, 만화처럼 검은 테두리). --고급 은 EEVEE(그림자·빛, 한 장 수십 초).

캐릭터 파일(JSON) — 이름마다:
  피부·머리·윗옷·바지·신발·눈: 색("#rrggbb")
  머리모양: 짧은 | 삐죽 | 긴 | 대머리 | 후드     소매: 긴 | 짧은
  빛나는눈: true (눈동자가 스스로 빛남, 강자·악당)   수염: true   벨트: 색   망토: 색   모자: 색
  손에: 검 | 없음   검색: 색   키: 1.0(기본) — 몸 전체 크기 배율   표정: 보통 | 화남 | 웃음 | 놀람

장면 파일(JSON):
  {"캐릭터": "캐릭터.json", "초": 6, "fps": 24, "크기": [1920,1080], "배경": "풀밭" | "밤" | "흰",
   "인물": [{"이름": "도윤", "위치": [x,y], "방향": 0,
             "동작": [{"초": 0, "자세": "서기"}, {"초": 1, "자세": "걷기", "위치": [x,y]}, ...]}],
   "카메라": [{"초": 0, "위치": [x,y,z], "보는곳": [x,y,z], "렌즈": 35}, ...]}
  위치 [x, y, 높이] 처럼 세 번째 값을 주면 그 높이(발판 위)에 섬.
  픽셀(옛날 게임) 모드: "픽셀": 6, "꼬마": 1.5, "배경": "레트로", "무대": {"바닥": [-12,12], "발판": [[x0,x1,높이]],
    "사다리": [[x, 아래, 위]]}, 카메라에 "직교": 14 (옆에서 평평하게, 화면 가로 14m)
  자세: 서기 | 걷기 | 달리기 | 주먹 | 가리키기 | 놀람 | 팔짱 | 쓰러짐
  방향: 도(°). 0 = 카메라 쪽(-Y)을 봄, 90 = 오른쪽(+X)을 봄. 위치는 m (캐릭터 키 약 2m).
  동작 사이의 위치는 부드럽게 이어짐(걷기·달리기는 그동안 다리를 움직임).
"""
import json
import math
import os
import subprocess
import sys
import tempfile

import bpy
from mathutils import Vector

U = 1.0 / 16.0  # 블록 한 칸 = 1/16 m → 캐릭터 키 32칸 = 2 m

# ───────────────────────── 기본 도구 ─────────────────────────
_MATS = {}


def _hex(c):
    c = c.lstrip("#")
    return tuple(int(c[i:i + 2], 16) / 255.0 for i in (0, 2, 4))


def _lin(v):  # 화면 색(sRGB) → Blender 계산 색(linear)
    return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4


def mat(color, glow=0.0):
    key = (color, glow)
    if key in _MATS:
        return _MATS[key]
    r, g, b = (_lin(v) for v in _hex(color))
    m = bpy.data.materials.new(f"색{len(_MATS)}")
    m.diffuse_color = (r, g, b, 1.0)
    m.use_nodes = True
    p = m.node_tree.nodes.get("Principled BSDF")
    if p:
        p.inputs["Base Color"].default_value = (r, g, b, 1.0)
        p.inputs["Roughness"].default_value = 0.8
        if glow:
            p.inputs["Emission Color"].default_value = (r, g, b, 1.0)
            p.inputs["Emission Strength"].default_value = glow
    _MATS[key] = m
    return m


OUTLINE = float(os.environ.get("블록테두리", "0.35"))  # 검은 테두리 굵기(칸). 0 이면 없음


def _outline_mat():
    if "테두리" not in _MATS:
        m = bpy.data.materials.new("테두리")
        m.diffuse_color = (0.02, 0.02, 0.02, 1.0)
        m.use_backface_culling = True
        _MATS["테두리"] = m
    return _MATS["테두리"]


def box(name, lo, hi, color, parent=None, origin=(0, 0, 0), glow=0.0, rot=None, outline=True):
    """lo~hi(블록 칸 단위, 부모 기준) 상자. origin 은 회전 중심(칸 단위)."""
    ox, oy, oz = origin
    me = bpy.data.meshes.new(name)
    x0, y0, z0 = [(lo[i] - origin[i]) * U for i in range(3)]
    x1, y1, z1 = [(hi[i] - origin[i]) * U for i in range(3)]
    v = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
         (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    me.from_pydata(v, [], f)
    me.update()
    me.materials.append(mat(color, glow))
    ob = bpy.data.objects.new(name, me)
    if outline and OUTLINE > 0:  # 뒤집은 껍질 = 만화 테두리
        me.materials.append(_outline_mat())
        md = ob.modifiers.new("테두리", "SOLIDIFY")
        md.thickness = OUTLINE * U
        md.offset = 1.0
        md.use_flip_normals = True
        md.material_offset = 1
        md.use_rim = False
    bpy.context.scene.collection.objects.link(ob)
    if parent is not None:
        ob.parent = parent
        po = parent.get("origin", (0, 0, 0))
        ob.location = ((ox - po[0]) * U, (oy - po[1]) * U, (oz - po[2]) * U)
    else:
        ob.location = (ox * U, oy * U, oz * U)
    ob["origin"] = origin
    if rot:
        ob.rotation_euler = [math.radians(a) for a in rot]
    return ob


def grow(lo, hi, d):
    return [a - d for a in lo], [b + d for b in hi]


# ───────────────────────── 캐릭터 만들기 ─────────────────────────
DEFAULT = {"피부": "#f2c9a0", "머리": "#3b2a20", "윗옷": "#4a78c2", "바지": "#2f3550",
           "신발": "#2a2a2a", "눈": "#3a2a1a", "머리모양": "짧은", "소매": "긴", "표정": "보통"}


def build_character(name, spec):
    s = dict(DEFAULT)
    s.update(spec)
    root = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(root)
    root["origin"] = (0, 0, 0)
    k = float(s.get("키", 1.0))
    root.scale = (k, k, k)

    def j(nm, origin):  # 관절(빈 물체) — 여기를 돌리면 팔·다리·머리가 움직임
        e = bpy.data.objects.new(f"{name}_{nm}", None)
        bpy.context.scene.collection.objects.link(e)
        e.parent = root
        e.location = Vector(origin) * U
        e["origin"] = origin
        return e

    # 다리(엉덩이 관절) — 신발 2칸 + 바지
    legs = {}
    for side, x in (("왼다리", 2), ("오른다리", -2)):
        o = (x, 0, 12)
        jt = j(side, o)
        box(f"{name}_{side}_바지", (x - 2, -2, 2), (x + 2, 2, 12), s["바지"], jt, o)
        lo, hi = grow((x - 2, -2, 0), (x + 2, 2, 2.2), 0.15)
        box(f"{name}_{side}_신발", lo, hi, s["신발"], jt, o)
        legs[side] = jt
    # 몸통
    body = j("몸", (0, 0, 12))
    box(f"{name}_몸", (-4, -2, 12), (4, 2, 24), s["윗옷"], body, (0, 0, 12))
    if s.get("벨트"):
        lo, hi = grow((-4, -2, 12.5), (4, 2, 14), 0.12)
        box(f"{name}_벨트", lo, hi, s["벨트"], body, (0, 0, 12))
    if s.get("망토"):
        box(f"{name}_망토", (-4.5, 2.1, 6), (4.5, 2.8, 24), s["망토"], body, (0, 0, 12))
    # 팔(어깨 관절) — 소매 + 손
    arms = {}
    sleeve_bot = 15 if s["소매"] == "긴" else 19
    for side, x in (("왼팔", 6), ("오른팔", -6)):
        o = (x, 0, 22)
        jt = j(side, o)
        box(f"{name}_{side}_소매", (x - 2, -2, sleeve_bot), (x + 2, 2, 24), s["윗옷"], jt, o)
        box(f"{name}_{side}_손", (x - 1.9, -1.9, 12), (x + 1.9, 1.9, sleeve_bot), s["피부"], jt, o)
        arms[side] = jt
    if s.get("손에") == "검":
        a = arms["오른팔"]
        o = a["origin"]
        # 검은 팔과 같은 방향(아래)으로 쥠 → 팔을 앞으로 뻗으면 검도 앞을 찌름
        box(f"{name}_검자루", (-6.5, -0.5, 9.6), (-5.5, 0.5, 13.5), "#5a3a20", a, o)
        box(f"{name}_검막이", (-7.8, -1.6, 9.0), (-4.2, 1.6, 9.6), "#8a8a8a", a, o)
        box(f"{name}_검날", (-6.4, -0.45, -1.0), (-5.6, 0.45, 9.0), s.get("검색", "#cfd8dc"), a, o,
            glow=2.0 if s.get("빛나는눈") else 0.0)
    # 머리(목 관절)
    o = (0, 0, 24)
    head = j("머리", o)
    hs = float(s.get("머리크기", 1.0))  # 1.5 쯤 = 꼬마 비율(옛날 게임 느낌)
    head.scale = (hs, hs, hs)
    box(f"{name}_얼굴", (-4, -4, 24), (4, 4, 32), s["피부"], head, o)
    hair, style = s["머리"], s["머리모양"]
    F = -4.06  # 얼굴 앞면 바로 앞
    if style != "대머리" and style != "후드":
        box(f"{name}_머리위", (-4.3, -4.3, 31), (4.3, 4.3, 32.6), hair, head, o)
        box(f"{name}_뒷머리", (-4.3, 4, 24.5 if style == "긴" else 26), (4.3, 4.4, 32), hair, head, o)
        sz = 26 if style == "긴" else 29
        for sx in (-1, 1):
            box(f"{name}_옆머리{sx}", (min(sx * 4, sx * 4.4), -4.2, sz), (max(sx * 4, sx * 4.4), 4.3, 32),
                hair, head, o)
        box(f"{name}_앞머리", (-4.3, -4.4, 30), (4.3, -4, 31.2), hair, head, o)
        if style == "긴":
            box(f"{name}_긴머리", (-4.3, 2.2, 17), (4.3, 4.4, 25), hair, head, o)
        if style == "삐죽":
            for i, (x, y, r) in enumerate([(-3, -2, 25), (0, -1, -10), (3, -2, -30), (-2, 2, 40), (2, 2, -45)]):
                sp = box(f"{name}_삐죽{i}", (x - 1.2, y - 1.2, 32), (x + 1.2, y + 1.2, 35.5), hair, head,
                         (x, y, 32), rot=(r * 0.6, -r, 0))
    if style == "후드":
        hc = s.get("후드색", s["윗옷"])
        box(f"{name}_후드위", (-4.6, -4.4, 32), (4.6, 4.6, 33), hc, head, o)
        box(f"{name}_후드뒤", (-4.6, 4, 23), (4.6, 4.6, 32), hc, head, o)
        for sx in (-1, 1):
            box(f"{name}_후드옆{sx}", (min(sx * 4, sx * 4.6), -4.4, 23.5), (max(sx * 4, sx * 4.6), 4.6, 33),
                hc, head, o)
        box(f"{name}_후드앞", (-4.6, -4.5, 31), (4.6, -4, 32), hc, head, o)
    if s.get("모자"):
        box(f"{name}_모자", (-4.6, -4.6, 31.5), (4.6, 4.6, 34), s["모자"], head, o)
        box(f"{name}_모자챙", (-4.6, -7, 31.5), (4.6, -4.6, 32.2), s["모자"], head, o)
    # 얼굴: 눈(흰자+눈동자), 눈썹, 입
    glow = 4.0 if s.get("빛나는눈") else 0.0
    ex = s.get("표정", "보통")
    for sx in (-1, 1):
        x0, x1 = sorted((sx * 1, sx * 3))
        box(f"{name}_흰자{sx}", (x0, F - 0.05, 27), (x1, F + 0.06, 28.2 if ex != "놀람" else 28.6),
            "#ffffff" if not glow else "#1a1a1a", head, o, outline=False)
        px0, px1 = sorted((sx * 1, sx * 2))
        box(f"{name}_눈동자{sx}", (px0, F - 0.12, 27), (px1, F, 28.2), s["눈"], head, o, glow=glow, outline=False)
        brow_z = 29.0 if ex != "놀람" else 29.6
        tilt = {"화남": 18, "웃음": -8}.get(ex, 0) * sx
        box(f"{name}_눈썹{sx}", (x0 - 0.2, F - 0.12, brow_z), (x1 + 0.2, F, brow_z + 0.6), hair if style not in ("대머리",) else "#5a4030",
            head, ((x0 + x1) / 2, F, brow_z + 0.3), rot=(0, tilt, 0), outline=False)
    mw = {"웃음": 1.6, "놀람": 0.8, "화남": 1.4}.get(ex, 1.2)
    mh = {"놀람": 1.2}.get(ex, 0.45)
    box(f"{name}_입", (-mw, F - 0.12, 25.6), (mw, F, 25.6 + mh), "#7a3b30" if ex != "놀람" else "#3a1a1a", head, o, outline=False)
    if s.get("수염"):
        box(f"{name}_수염", (-4.2, -4.3, 24), (4.2, -3.9, 25.3), hair, head, o)
        for sx in (-1, 1):
            box(f"{name}_구레나룻{sx}", (min(sx * 2.6, sx * 4.2), -4.3, 24), (max(sx * 2.6, sx * 4.2), -3.9, 27), hair, head, o)
    return {"root": root, "머리": head, "몸": body, **arms, **legs}


# ───────────────────────── 자세 ─────────────────────────
# 관절 각도(도, X축 = 앞뒤로 흔들기, Y축 = 옆으로 벌리기). 앞 = -Y 방향 → 팔을 앞으로 들려면 X 를 음수가 아니라
# 양수로 돌리면 아래로 늘어진 팔이 뒤로 감 → 앞으로 들 때는 X 음수.
POSES = {
    "서기": {},
    "주먹": {"오른팔": (-90, 0, 0), "왼팔": (-30, 0, 15), "몸": (0, 0, -15), "왼다리": (-15, 0, 0), "오른다리": (15, 0, 0)},
    "가리키기": {"오른팔": (-90, 0, 10), "머리": (0, 0, 0)},
    "놀람": {"오른팔": (0, -150, 0), "왼팔": (0, 150, 0), "몸": (8, 0, 0)},
    "팔짱": {"오른팔": (-60, 0, -55), "왼팔": (-60, 0, 55)},
    "쓰러짐": {"몸": (0, 0, 0)},
}


def apply_pose(rig, pose, phase=0.0, amp=1.0):
    """자세를 관절에 넣음. 걷기·달리기는 phase(0~1 반복)에 따라 다리를 흔듦."""
    for k in ("머리", "몸", "왼팔", "오른팔", "왼다리", "오른다리"):
        rig[k].rotation_euler = (0, 0, 0)
    if pose in ("걷기", "달리기"):
        a = (30 if pose == "걷기" else 55) * amp
        w = math.sin(phase * 2 * math.pi)
        rig["왼다리"].rotation_euler = (math.radians(a * w), 0, 0)
        rig["오른다리"].rotation_euler = (math.radians(-a * w), 0, 0)
        rig["왼팔"].rotation_euler = (math.radians(-a * w), 0, 0)
        rig["오른팔"].rotation_euler = (math.radians(a * w), 0, 0)
        if pose == "달리기":
            rig["몸"].rotation_euler = (math.radians(-12), 0, 0)
        return
    for k, r in POSES.get(pose, {}).items():
        rig[k].rotation_euler = tuple(math.radians(v) for v in r)


# ───────────────────────── 배경·촬영 설정 ─────────────────────────
def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    _MATS.clear()


def setup_render(w, h, fancy=False, bg="#ffffff", pixel=False):
    sc = bpy.context.scene
    sc.render.resolution_x, sc.render.resolution_y = w, h
    sc.render.resolution_percentage = 100
    world = bpy.data.worlds.new("세상")
    sc.world = world
    r, g, b = (_lin(v) for v in _hex(bg))
    world.color = (r, g, b)
    world.use_nodes = True
    bgn = world.node_tree.nodes.get("Background")
    if bgn:
        bgn.inputs["Color"].default_value = (r, g, b, 1)
        bgn.inputs["Strength"].default_value = 1.0
    sc.view_settings.view_transform = "Standard"
    if fancy:
        sc.render.engine = "BLENDER_EEVEE"
        sun = bpy.data.lights.new("해", "SUN")
        sun.energy = 3.0
        so = bpy.data.objects.new("해", sun)
        so.rotation_euler = (math.radians(50), math.radians(10), math.radians(-30))
        sc.collection.objects.link(so)
    else:
        sc.render.engine = "BLENDER_WORKBENCH"
        sh = sc.display.shading
        sh.light = os.environ.get("블록조명", "FLAT")  # FLAT = 원래 색 그대로(만화), STUDIO = 면마다 밝기 차이
        sh.color_type = "MATERIAL"
        sh.show_object_outline = True
        sh.object_outline_color = (0.05, 0.05, 0.05)
        sh.show_shadows = False
        sh.show_backface_culling = True  # 테두리 껍질의 안쪽 면을 숨김
        sh.show_cavity = False
        sc.display.render_aa = "OFF" if pixel else "16"  # 픽셀 = 다듬지 않은 또렷한 점
    return sc


def add_camera(loc, look, lens=35, ortho=None):
    cam = bpy.data.cameras.new("카메라")
    cam.lens = lens
    if ortho:
        cam.type = "ORTHO"
        cam.ortho_scale = ortho
    ob = bpy.data.objects.new("카메라", cam)
    bpy.context.scene.collection.objects.link(ob)
    bpy.context.scene.camera = ob
    aim(ob, loc, look)
    return ob


def aim(ob, loc, look):
    ob.location = Vector(loc)
    d = Vector(look) - Vector(loc)
    ob.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()


def ground(kind, size=24):
    """블록 땅. 풀밭 = 초록 두 가지 색 바둑판, 밤 = 어두운 돌."""
    cols = {"풀밭": ("#6aa84f", "#5d9944"), "밤": ("#3d4250", "#353a47"), "흰": ("#f4f4f4", "#ececec")}[kind]
    # 칸이 많으면 느려지므로 한 칸 = 1m 블록
    for ix in range(-size // 2, size // 2):
        for iy in range(-size // 2, size // 2):
            c = cols[(ix + iy) % 2]
            box(f"땅{ix}_{iy}", (ix * 16, iy * 16, -16), ((ix + 1) * 16, (iy + 1) * 16, 0), c)


def retro_stage(stage):
    """옛날 오락실 게임 같은 옆모습 무대: 벽돌 바닥, 떠 있는 발판, 사다리.
    stage = {"바닥": [x0, x1], "발판": [[x0, x1, 높이m], ...], "사다리": [[x, 아래m, 위m], ...], "벽돌색": 색}"""
    c1 = stage.get("벽돌색", "#c8502a")
    c2 = stage.get("벽돌색2", "#a63f1f")

    def bricks(x0, x1, ztop, rows=2):
        n = 0
        for r in range(rows):
            off = 0 if r % 2 == 0 else 8
            x = x0 * 16 - off
            while x < x1 * 16:
                lo = max(x, x0 * 16)
                hi = min(x + 16, x1 * 16)
                z = ztop * 16 - (r + 1) * 8
                box(f"벽돌{n}_{x}_{z}", (lo, -8, z), (hi, 8, z + 8), c1 if (n + r) % 3 else c2)
                x += 16
                n += 1

    x0, x1 = stage.get("바닥", [-12, 12])
    bricks(x0, x1, 0, rows=3)
    for i, (a, b, zt) in enumerate(stage.get("발판", [])):
        bricks(a, b, zt, rows=1)
    lc = stage.get("사다리색", "#4fc3f7")
    for i, (x, za, zb) in enumerate(stage.get("사다리", [])):
        for sx in (-6, 6):
            box(f"사다리{i}_{sx}", (x * 16 + sx - 1, 9, za * 16), (x * 16 + sx + 1, 10, zb * 16), lc)
        z = za * 16 + 4
        while z < zb * 16:
            box(f"가로대{i}_{z}", (x * 16 - 6, 9, z), (x * 16 + 6, 10, z + 1.2), lc)
            z += 6


# ───────────────────────── 명령: 시트 ─────────────────────────
def cmd_sheet(char_file, out, names=None):
    from PIL import Image, ImageDraw, ImageFont
    chars = json.load(open(char_file, encoding="utf-8"))
    names = names or list(chars)
    rows = []
    tmpd = tempfile.mkdtemp()
    for nm in names:
        reset_scene()
        setup_render(1600, 600, bg="#ffffff")
        for i, rz in enumerate((0, 90, -90, 180)):  # 앞, 옆(오른쪽 봄), 옆(왼쪽 봄), 뒤
            rig = build_character(f"{nm}{i}", chars[nm])
            rig["root"].location = ((i - 1.5) * 1.6, 0, 0)
            rig["root"].rotation_euler = (0, 0, math.radians(rz))
        add_camera((0, -20, 1.15), (0, 0, 1.15), ortho=6.6)
        p = os.path.join(tmpd, f"{len(rows)}.png")
        bpy.context.scene.render.filepath = p
        bpy.ops.render.render(write_still=True)
        rows.append((nm, p))
    font_path = "/usr/share/fonts/truetype/nanum/NanumSquareB.ttf"
    font = ImageFont.truetype(font_path, 34) if os.path.exists(font_path) else ImageFont.load_default()
    W, H, LH = 1600, 600, 56
    sheet = Image.new("RGB", (W, (H + LH) * len(rows)), "white")
    d = ImageDraw.Draw(sheet)
    for i, (nm, p) in enumerate(rows):
        y = i * (H + LH)
        d.text((16, y + 10), nm, fill="black", font=font)
        sheet.paste(Image.open(p).convert("RGB"), (0, y + LH))
    sheet.save(out)
    print("시트 저장:", out)


# ───────────────────────── 명령: 장면 ─────────────────────────
def _lerp(a, b, t):
    return [x + (y - x) * t for x, y in zip(a, b)]


def _smooth(t):
    return t * t * (3 - 2 * t)


def _track(keys, t, field, default):
    """keys(초 순서)에서 t 초의 값. 이전 키 → 다음 키 사이를 부드럽게."""
    pts = [(k["초"], k[field]) for k in keys if field in k]
    if not pts:
        return default
    if t <= pts[0][0]:
        return pts[0][1]
    for (t0, v0), (t1, v1) in zip(pts, pts[1:]):
        if t0 <= t <= t1:
            u = 0 if t1 == t0 else (t - t0) / (t1 - t0)
            if isinstance(v0, (int, float)):
                return v0 + (v1 - v0) * _smooth(u)
            return _lerp(v0, v1, _smooth(u))
    return pts[-1][1]


def _pose_at(keys, t):
    cur = "서기"
    for k in keys:
        if "자세" in k and k["초"] <= t:
            cur = k["자세"]
    return cur


def cmd_scene(scene_file, out, fancy=False):
    S = json.load(open(scene_file, encoding="utf-8"))
    base = os.path.dirname(os.path.abspath(scene_file))
    cf = S.get("캐릭터", "캐릭터.json")
    chars = json.load(open(cf if os.path.isabs(cf) else os.path.join(base, cf), encoding="utf-8"))
    fps, sec = int(S.get("fps", 24)), float(S.get("초", 5))
    w, h = S.get("크기", [1920, 1080])
    px = int(S.get("픽셀", 0))  # 예: 6 → 320×180 으로 찍고 6배로 키워 도트 그림처럼
    global OUTLINE
    if px:
        OUTLINE = 0.0  # 픽셀에서는 1점짜리 물체 테두리만 씀
    reset_scene()
    bgk = S.get("배경", "풀밭")
    sky = {"풀밭": "#9fd3f0", "밤": "#141826", "흰": "#ffffff", "레트로": "#000000"}.get(bgk, "#9fd3f0")
    setup_render(w // px if px else w, h // px if px else h, fancy=fancy, bg=sky, pixel=bool(px))
    if bgk == "레트로":
        retro_stage(S.get("무대", {}))
    elif bgk != "흰":
        ground(bgk)
    actors = []
    for a in S["인물"]:
        spec = dict(chars[a["이름"]])
        if S.get("꼬마"):
            spec.setdefault("머리크기", float(S["꼬마"]) if not isinstance(S["꼬마"], bool) else 1.5)
        rig = build_character(a["이름"], spec)
        keys = sorted(a.get("동작", []), key=lambda k: k["초"])
        actors.append((a, rig, keys))
    cams = sorted(S.get("카메라", [{"초": 0, "위치": [0, -8, 2], "보는곳": [0, 0, 1]}]), key=lambda k: k["초"])
    cam = add_camera(cams[0]["위치"], cams[0]["보는곳"], cams[0].get("렌즈", 35), ortho=cams[0].get("직교"))
    tmpd = tempfile.mkdtemp()
    n = int(round(sec * fps))
    walk_phase = {}
    for f in range(n):
        t = f / fps
        for a, rig, keys in actors:
            pos = _track(keys, t, "위치", a.get("위치", [0, 0]))
            pos = _track([{"초": -1, "위치": a.get("위치", [0, 0])}] + keys, t, "위치", pos)
            yaw = _track([{"초": -1, "방향": a.get("방향", 0)}] + keys, t, "방향", a.get("방향", 0))
            pose = _pose_at(keys, t)
            ph = walk_phase.get(a["이름"], 0.0)
            if pose in ("걷기", "달리기"):
                ph += (1.0 if pose == "걷기" else 1.6) / fps
            walk_phase[a["이름"]] = ph
            apply_pose(rig, pose, ph)
            z = pos[2] if len(pos) > 2 else 0.0  # 위치에 높이(m)를 주면 발판 위에 섬
            r = rig["root"]
            r.location = (pos[0], pos[1], z)
            r.rotation_euler = (math.radians(-90) if pose == "쓰러짐" else 0, 0, math.radians(yaw))
            if pose == "쓰러짐":
                r.location = (pos[0], pos[1], z + 0.25)
        cl = _track(cams, t, "위치", cams[0]["위치"])
        ck = _track(cams, t, "보는곳", cams[0]["보는곳"])
        cam.data.lens = _track(cams, t, "렌즈", cams[0].get("렌즈", 35))
        if cams[0].get("직교"):
            cam.data.ortho_scale = _track(cams, t, "직교", cams[0]["직교"])
        aim(cam, cl, ck)
        bpy.context.scene.render.filepath = os.path.join(tmpd, f"{f:05d}.png")
        bpy.ops.render.render(write_still=True)
        if f % fps == 0:
            print(f"  {f}/{n} 장", flush=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(fps), "-i",
                    os.path.join(tmpd, "%05d.png")]
                   + (["-vf", f"scale=iw*{px}:ih*{px}:flags=neighbor"] if px else []) + ["-c:v", "libx264", "-pix_fmt", "yuv420p",
                    "-crf", "18", out], check=True)
    print("영상 저장:", out)


def main():
    argv = sys.argv[1:]
    if not argv:
        print(__doc__)
        return
    cmd = argv[0]
    names = None
    if "--이름" in argv:
        i = argv.index("--이름")
        names = argv[i + 1].split(",")
        del argv[i:i + 2]
    fancy = "--고급" in argv
    argv = [a for a in argv if a != "--고급"]
    if cmd == "시트":
        cmd_sheet(argv[1], argv[2], names)
    elif cmd == "장면":
        cmd_scene(argv[1], argv[2], fancy)
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
