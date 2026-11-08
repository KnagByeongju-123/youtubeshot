# -*- coding: utf-8 -*-
"""블록애니 — Blender(bpy, 오픈소스 GPL)로 블록 캐릭터를 만들고 움직여 영상으로 뽑는 도구.

준비(한 번): python3.11 -m venv .blender_venv && .blender_venv/bin/pip install bpy pillow
실행은 반드시 가상 화면 위에서 (그래픽카드가 없어서 xvfb 의 소프트웨어 그래픽을 씀):

  # 캐릭터 시트(앞·옆·옆·뒤 4장, 한 사람당 한 줄)
  xvfb-run -a .blender_venv/bin/python 블록애니.py 시트 블록애니/캐릭터.json 결과.png [--이름 도윤,강철]

  # 장면 영상(장면 파일에 인물·동작·카메라를 적음 — 아래 '장면 파일' 참고)
  xvfb-run -a .blender_venv/bin/python 블록애니.py 장면 블록애니/장면_예시.json 결과.mp4 [--고급]

  # 판 영상 합치기(차례로 이어 붙임)
  .blender_venv/bin/python 블록애니.py 합치기 전체.mp4 1판.mp4 2판.mp4

  기본 촬영은 Workbench(한 장 1초 안팎, 만화처럼 검은 테두리). --고급 은 EEVEE(그림자·빛, 한 장 수십 초).

캐릭터 파일(JSON) — 이름마다:
  피부·머리·윗옷·바지·신발·눈: 색("#rrggbb")
  머리모양: 짧은 | 삐죽 | 긴 | 대머리 | 후드     소매: 긴 | 짧은
  빛나는눈: true (눈동자가 스스로 빛남, 강자·악당)   수염: true   벨트: 색   망토: 색   모자: 색
  손에: 검 | 활 | 없음   검색·활색: 색   화살통: 색(등에 화살통)
  괴물용: 외눈: true(가운데 큰 눈)   더듬이: 색   더듬이끝: 색   이빨: true   머리크기: 배율   키: 1.0(기본) — 몸 전체 크기 배율   표정: 보통 | 화남 | 웃음 | 놀람

장면 파일(JSON):
  {"캐릭터": "캐릭터.json", "초": 6, "fps": 24, "크기": [1920,1080], "배경": "풀밭" | "밤" | "흰",
   "인물": [{"이름": "도윤", "위치": [x,y], "방향": 0,
             "동작": [{"초": 0, "자세": "서기"}, {"초": 1, "자세": "걷기", "위치": [x,y]}, ...]}],
   "카메라": [{"초": 0, "위치": [x,y,z], "보는곳": [x,y,z], "렌즈": 35}, ...]}
  위치 [x, y, 높이] 처럼 세 번째 값을 주면 그 높이(발판 위)에 섬.
  픽셀(옛날 게임) 모드: "픽셀": 6, "꼬마": 1.5, "배경": "레트로", "무대": {"바닥": [-12,12], "발판": [[x0,x1,높이]] 또는 [[x0,x1,왼쪽높이,오른쪽높이]](기울어진 바닥),
    "사다리": [[x, 아래, 위]]}, 카메라에 "직교": 14 (옆에서 평평하게, 화면 가로 14m)
  자세: 서기 | 걷기 | 달리기 | 주먹 | 가리키기 | 놀람 | 팔짱 | 쓰러짐 | 활쏘기 | 위로쏘기 | 맞음 | 만세 | 광선 | 점프
  소리(자동, 레트로소리.py): 화살 → 활·맞음, 광선 → 광선(맞히면 "맞힘": true), 점프·놀람·쓰러짐 동작 → 그 소리.
    더 넣기: "효과음": [{"초": 1.0, "소리": "착지"}, {"초": 7, "소리": "승리"}]
    (착지 놀람 활 맞음 광선 점프 쓰러짐 승리 동전 주먹), 배경음: "배경음": {"곡": "레트로전투", "크기": 0.35, "끝": 6.9}
    (끝 = 그 초에 배경음이 줄어들며 멈춤), 소리를 빼려면 "소리": false
  벌: {"모양": "벌", "크기": 1.6, "맞은초": 2.0, "왕관": true, "눈색": "#ff2020"(빛나는 눈), "동작": [...]} — 맞은초부터 빙글 돌며 떨어짐(그 뒤 키로 떨어질 곳을 적음),
    날아올 때 '윙윙', 맞으면 '띠링'(점수). 글자: {"모양": "글자", "내용": "+100", "동작": [...], "바뀜": [[초, 내용], ...]} (한글 됨, 바뀜 = 점수판처럼 바뀌는 글자)
  통나무: {"모양": "통나무", "반지름": 0.5, "동작": [...], "쿵": [떨어져 닿는 초...]} — 같은 빠르기로 굴러 돎, '데굴데굴' 소리.
    "등속": true 를 주면 다른 물체도 같은 빠르기로 움직임
  운석: {"모양": "운석", "쿵": [닿는 초]} — 불꼬리, 가는 쪽을 봄. 무대 "별": 개수, "행성": [x, 높이, 반지름, 색] (우주 배경)
  딱정벌레: 바닥을 기어 다니는 적(위치 = 바닥 높이), 불덩이: {"모양": "불덩이", "반지름": 0.45} 빛나며 돎.
  돌: {"모양": "돌", "반지름": 0.5, "쿵": [땅에 닿는 초], "휘익": true(떨어지는 소리)} — 떨어지는 동안 돎. 조각: 부서진 작은 돌.
  감옥: {"모양": "감옥", "너비": 2.8, "높이": 2.6} — 위로 올리는 키를 주면 열림. 하트: {"모양": "하트", "크기": 0.18}
  인물 "바꿈": {"키": 1.0} — 이 장면에서만 캐릭터 값을 바꿈. 캐릭터 "치마": 색, "왕관": 색. 자세 "오르기"(사다리)
  긴장 장치: "슬로": [[시작초, 끝초, 0.3]] (느리게), "번쩍": [[초, 길이, "#7a0000"]] (배경 번쩍임),
    "배경음": {..., "빠르기": [[초, BPM], ...]} (점점 빨라지는 음악), "미리보기": {"초": [a, b], "글자": "..."} (맨 앞에 붙임),
    물체 "화면고정": true — 점수·시간·목숨처럼 카메라가 확대해도 화면의 같은 자리·크기(직교 카메라)
  날아가는 물체: "물체": [{"모양": "화살" | "광선" | "벌" | "글자" | "통나무" | "돌" | "조각" | "감옥" | "하트" | "딱정벌레" | "불덩이" | "운석", "색": 색, "동작": [{"초": 3, "위치": [x,y,z]}, {"초": 3.5, "위치": [...]}]}]
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


def cyl(name, r, y0, y1, color, parent, sides=20, outline=True):
    """Y 방향으로 누운 둥근 원통(칸 단위, 부모 중심 기준). 앞면(y0)이 화면 쪽."""
    me = bpy.data.meshes.new(name)
    v = []
    for y in (y0, y1):
        for i in range(sides):
            a = 2 * math.pi * i / sides
            v.append((r * math.cos(a) * U, y * U, r * math.sin(a) * U))
    f = [(i, sides + i, sides + (i + 1) % sides, (i + 1) % sides) for i in range(sides)]  # 바깥을 보는 옆면
    f.append(tuple(range(sides)))  # 앞 뚜껑(-Y)
    f.append(tuple(range(2 * sides - 1, sides - 1, -1)))  # 뒤 뚜껑(+Y)
    me.from_pydata(v, [], f)
    me.update()
    me.materials.append(mat(color))
    ob = bpy.data.objects.new(name, me)
    if outline and OUTLINE > 0:
        me.materials.append(_outline_mat())
        md = ob.modifiers.new("테두리", "SOLIDIFY")
        md.thickness = OUTLINE * U
        md.offset = 1.0
        md.use_flip_normals = True
        md.material_offset = 1
        md.use_rim = False
    bpy.context.scene.collection.objects.link(ob)
    ob.parent = parent
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

    def j(nm, origin, par=None):  # 관절(빈 물체) — 여기를 돌리면 팔·다리·머리가 움직임
        e = bpy.data.objects.new(f"{name}_{nm}", None)
        bpy.context.scene.collection.objects.link(e)
        e.parent = par or root
        po = (par or root).get("origin", (0, 0, 0))
        e.location = (Vector(origin) - Vector(po)) * U
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
    if s.get("치마"):  # 긴 치마(다리를 덮음, 아래로 갈수록 넓게)
        box(f"{name}_치마위", (-4.4, -2.4, 9), (4.4, 2.4, 15), s["치마"], body, (0, 0, 12))
        box(f"{name}_치마아래", (-5.4, -3.2, 2.5), (5.4, 3.2, 9.2), s["치마"], body, (0, 0, 12))
        box(f"{name}_치마단", (-5.6, -3.4, 2.2), (5.6, 3.4, 3.2), s.get("치마단", "#ffffff"), body, (0, 0, 12))
    # 팔(어깨 관절) — 소매 + 손
    arms = {}
    sleeve_bot = 15 if s["소매"] == "긴" else 19
    for side, x in (("왼팔", 6), ("오른팔", -6)):
        o = (x, 0, 22)
        jt = j(side, o, body)
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
    if s.get("손에") == "활":  # 왼손에 활(팔을 앞으로 뻗으면 활이 세로로 섬)
        a = arms["왼팔"]
        o2 = a["origin"]
        bc = s.get("활색", "#8b5a2b")
        box(f"{name}_활손잡이", (5.4, -1.5, 10.5), (6.6, 1.5, 12), bc, a, o2)
        box(f"{name}_활위", (5.5, -8, 11.2), (6.5, -1.5, 12.2), bc, a, o2, rot=None)
        box(f"{name}_활아래", (5.5, 1.5, 11.2), (6.5, 8, 12.2), bc, a, o2)
        box(f"{name}_활끝1", (5.5, -9, 12.2), (6.5, -7.5, 14.2), bc, a, o2)
        box(f"{name}_활끝2", (5.5, 7.5, 12.2), (6.5, 9, 14.2), bc, a, o2)
        box(f"{name}_활시위", (5.8, -8.5, 14.0), (6.2, 8.5, 14.4), "#f5f5f5", a, o2, outline=False)
    if s.get("화살통"):
        box(f"{name}_화살통", (-2.5, 2.1, 15), (0.5, 4.2, 24), s["화살통"], body, (0, 0, 12))
        for i, x in enumerate((-2, -0.8)):
            box(f"{name}_깃{i}", (x, 2.6, 24), (x + 1, 3.6, 26.5), "#f5f5f5", body, (0, 0, 12))
    # 머리(목 관절)
    o = (0, 0, 24)
    head = j("머리", o, body)
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
    if s.get("왕관"):  # 금색 왕관 + 빨간 보석
        g = s["왕관"]
        box(f"{name}_왕관띠", (-3.4, -3.4, 32.2), (3.4, 3.4, 33.6), g, head, o)
        for k, (x, y) in enumerate([(-3.4, -3.4), (-0.6, -3.4), (2.2, -3.4), (-3.4, 2.2), (2.2, 2.2)]):
            box(f"{name}_왕관꼭지{k}", (x, y, 33.6), (x + 1.2, y + 1.2, 35.2), g, head, o)
        box(f"{name}_왕관보석", (-0.6, -3.55, 32.5), (0.6, -3.4, 33.3), "#ff2040", head, o, outline=False)
    if s.get("모자"):
        box(f"{name}_모자", (-4.6, -4.6, 31.5), (4.6, 4.6, 34), s["모자"], head, o)
        box(f"{name}_모자챙", (-4.6, -7, 31.5), (4.6, -4.6, 32.2), s["모자"], head, o)
    # 얼굴: 눈(흰자+눈동자), 눈썹, 입
    glow = 4.0 if s.get("빛나는눈") else 0.0
    ex = s.get("표정", "보통")
    eye_sides = () if s.get("외눈") else (-1, 1)
    if s.get("외눈"):  # 가운데 큰 눈 하나
        box(f"{name}_큰흰자", (-2.2, F - 0.05, 26.6), (2.2, F + 0.06, 29.4), "#ffffff" if not glow else "#1a1a1a", head, o, outline=False)
        box(f"{name}_큰눈동자", (-1.0, F - 0.12, 27.2), (1.0, F, 28.8), s["눈"], head, o, glow=glow, outline=False)
        tilt = {"화남": 12}.get(ex, 0)
        for sx in (-1, 1):
            box(f"{name}_눈썹{sx}", (min(0, sx * 2.6), F - 0.12, 29.8), (max(0, sx * 2.6), F, 30.4), "#2a2a2a", head,
                (sx * 1.3, F, 30.1), rot=(0, tilt * sx, 0), outline=False)
    if s.get("더듬이"):
        for sx in (-1, 1):
            box(f"{name}_더듬이{sx}", (sx * 2 - 0.4, -0.4, 32), (sx * 2 + 0.4, 0.4, 36), s["더듬이"], head, (sx * 2, 0, 32),
                rot=(0, -20 * sx, 0))
            box(f"{name}_더듬이끝{sx}", (sx * 3.4 - 1, -1, 35.4), (sx * 3.4 + 1, 1, 37.4), s.get("더듬이끝", "#7CFF4F"), head, o, glow=3.0)
    for sx in eye_sides:
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
    if s.get("이빨"):  # 괴물 입: 어두운 입 + 흰 이빨
        box(f"{name}_입", (-3, F - 0.1, 24.6), (3, F, 26.2), "#2a0a12", head, o, outline=False)
        for i, x in enumerate((-2.6, -1.0, 0.6, 2.0)):
            box(f"{name}_이{i}", (x, F - 0.16, 25.4), (x + 0.6, F - 0.08, 26.2), "#ffffff", head, o, outline=False)
    else:
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
    # 옆모습에서도 보이게 팔을 '앞쪽 위'로 듦(옆으로 벌리면 화면 안쪽이라 큰 머리에 가려짐)
    "놀람": {"오른팔": (-125, -15, 0), "왼팔": (-125, 15, 0), "몸": (-8, 0, 0)},
    "팔짱": {"오른팔": (-60, 0, -55), "왼팔": (-60, 0, 55)},
    "쓰러짐": {"몸": (0, 0, 0)},
    "위로쏘기": {"왼팔": (-125, 0, 0), "오른팔": (-125, 0, -35), "머리": (-15, 0, 0), "왼다리": (-12, 0, 0), "오른다리": (12, 0, 0)},
    "활쏘기": {"왼팔": (-90, 0, 0), "오른팔": (-90, 0, -35), "머리": (0, 0, 0), "왼다리": (-12, 0, 0), "오른다리": (12, 0, 0)},
    "맞음": {"몸": (-22, 0, 0), "왼팔": (-40, 0, 25), "오른팔": (-40, 0, -25), "머리": (-15, 0, 0)},
    "만세": {"왼팔": (-160, 15, 0), "오른팔": (-160, -15, 0), "머리": (-10, 0, 0)},
    "광선": {"오른팔": (-90, 0, 0), "왼팔": (-90, 0, 0), "몸": (8, 0, 0)},
    "점프": {"왼다리": (-35, 0, 0), "오른다리": (20, 0, 0), "왼팔": (0, 60, 0), "오른팔": (0, -60, 0)},
}


def apply_pose(rig, pose, phase=0.0, amp=1.0):
    """자세를 관절에 넣음. 걷기·달리기는 phase(0~1 반복)에 따라 다리를 흔듦."""
    for k in ("머리", "몸", "왼팔", "오른팔", "왼다리", "오른다리"):
        rig[k].rotation_euler = (0, 0, 0)
    if pose == "오르기":  # 사다리: 팔을 위로 번갈아, 다리도 번갈아
        w = math.sin(phase * 2 * math.pi)
        rig["왼팔"].rotation_euler = (math.radians(-150 - 25 * w), 0, 0)
        rig["오른팔"].rotation_euler = (math.radians(-150 + 25 * w), 0, 0)
        rig["왼다리"].rotation_euler = (math.radians(-35 * max(0, w)), 0, 0)
        rig["오른다리"].rotation_euler = (math.radians(-35 * max(0, -w)), 0, 0)
        return
    if pose in ("걷기", "달리기"):
        a = (30 if pose == "걷기" else 55) * amp
        w = math.sin(phase * 2 * math.pi)
        rig["왼다리"].rotation_euler = (math.radians(a * w), 0, 0)
        rig["오른다리"].rotation_euler = (math.radians(-a * w), 0, 0)
        rig["왼팔"].rotation_euler = (math.radians(-a * w), 0, 0)
        rig["오른팔"].rotation_euler = (math.radians(a * w), 0, 0)
        if pose == "달리기":
            rig["몸"].rotation_euler = (math.radians(12), 0, 0)  # 앞으로 숙임
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

    def bricks(x0, x1, ztop, rows=2, ztop1=None):
        """ztop1 을 주면 x0 에서 ztop, x1 에서 ztop1 로 기울어진 바닥(벽돌마다 높이를 조금씩 다르게)."""
        n = 0
        for r in range(rows):
            off = 0 if r % 2 == 0 else 8
            x = x0 * 16 - off
            while x < x1 * 16:
                lo = max(x, x0 * 16)
                hi = min(x + 16, x1 * 16)
                zt = ztop
                if ztop1 is not None and x1 > x0:
                    xc = (lo + hi) / 2 / 16
                    zt = ztop + (ztop1 - ztop) * (xc - x0) / (x1 - x0)
                z = zt * 16 - (r + 1) * 8
                box(f"벽돌{n}_{x}_{z}", (lo, -8, z), (hi, 8, z + 8), c1 if (n + r) % 3 else c2)
                x += 16
                n += 1

    x0, x1 = stage.get("바닥", [-12, 12])
    bricks(x0, x1, 0, rows=3)
    for i, fl in enumerate(stage.get("발판", [])):  # [x0, x1, 높이] 또는 [x0, x1, x0높이, x1높이](기울어짐)
        bricks(fl[0], fl[1], fl[2], rows=1, ztop1=fl[3] if len(fl) > 3 else None)
    lc = stage.get("사다리색", "#4fc3f7")
    for i, (x, za, zb) in enumerate(stage.get("사다리", [])):
        for sx in (-6, 6):
            box(f"사다리{i}_{sx}", (x * 16 + sx - 1, 9, za * 16), (x * 16 + sx + 1, 10, zb * 16), lc)
        z = za * 16 + 4
        while z < zb * 16:
            box(f"가로대{i}_{z}", (x * 16 - 6, 9, z), (x * 16 + 6, 10, z + 1.2), lc)
            z += 6
    if stage.get("별"):  # 우주 배경: 작은 별들(뒤쪽)
        import random
        rg = random.Random(5)
        sx0, sx1, sz0, sz1 = stage.get("별범위", [-17, 17, -1, 18])
        for k in range(int(stage["별"])):
            x, z = rg.uniform(sx0, sx1) * 16, rg.uniform(sz0, sz1) * 16
            a = rg.choice([0.5, 0.5, 0.8, 1.2])
            box(f"별{k}", (x - a, 120, z - a), (x + a, 121, z + a), rg.choice(["#ffffff", "#fff3b0", "#b0d8ff"]), outline=False)
    if stage.get("행성"):  # [x, 높이, 반지름, 색] — 뒤쪽의 둥근 행성(+ 고리)
        px_, pz_, pr_, pc_ = stage["행성"]
        root = bpy.data.objects.new("행성", None)
        bpy.context.scene.collection.objects.link(root)
        root.location = (px_, 8.0, pz_)
        root["origin"] = (0, 0, 0)
        cyl("행성몸", pr_ / U, -1, 1, pc_, root, sides=28)
        cyl("행성무늬", pr_ / U * 0.75, -1.4, -1.2, stage.get("행성무늬", "#7f8fff"), root, sides=24, outline=False)
        rb = box("행성고리", (-pr_ / U * 1.7, -1.6, -0.8), (pr_ / U * 1.7, -1.4, 0.8), stage.get("고리색", "#e8c27a"), root,
                 outline=False)
        rb.rotation_euler = (0, math.radians(-15), 0)


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


def _track(keys, t, field, default, linear=False):
    """keys(초 순서)에서 t 초의 값. 이전 키 → 다음 키 사이를 부드럽게(linear=True 면 같은 빠르기로)."""
    sm = (lambda u: u) if linear else _smooth
    pts = [(k["초"], k[field]) for k in keys if field in k]
    if not pts:
        return default
    if t <= pts[0][0]:
        return pts[0][1]
    for (t0, v0), (t1, v1) in zip(pts, pts[1:]):
        if t0 <= t <= t1:
            u = 0 if t1 == t0 else (t - t0) / (t1 - t0)
            if isinstance(v0, (int, float)):
                return v0 + (v1 - v0) * sm(u)
            return _lerp(v0, v1, sm(u))
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
        spec.update(a.get("바꿈", {}))  # 이 장면에서만 바꿀 값(예: {"키": 1.0})
        if S.get("꼬마"):
            spec.setdefault("머리크기", float(S["꼬마"]) if not isinstance(S["꼬마"], bool) else 1.5)
        rig = build_character(a["이름"], spec)
        keys = sorted(a.get("동작", []), key=lambda k: k["초"])
        actors.append((a, rig, keys))
    props = []  # 날아가는 물체(화살·광선): 첫 키 ~ 마지막 키 사이에만 보임
    for i, pr in enumerate(S.get("물체", [])):
        root = bpy.data.objects.new(f"물체{i}", None)
        bpy.context.scene.collection.objects.link(root)
        root["origin"] = (0, 0, 0)
        kind = pr.get("모양", "화살")
        if kind == "화살":
            box(f"화살대{i}", (-7, -0.3, -0.3), (5, 0.3, 0.3), "#8b5a2b", root)
            box(f"화살촉{i}", (5, -0.8, -0.8), (8, 0.8, 0.8), "#cfd8dc", root)
            box(f"화살깃{i}", (-8, -0.2, -1.2), (-5, 0.2, 1.2), "#f5f5f5", root)
        elif kind == "벌":  # 머리가 +X 쪽, 날개가 파닥임
            box(f"벌몸{i}", (-4, -2.5, -2.5), (4, 2.5, 2.5), pr.get("색", "#ffd21f"), root)
            for sx in (-1.6, 1.4):
                box(f"벌줄{i}_{sx}", (sx, -2.65, -2.65), (sx + 1.0, 2.65, 2.65), "#1e1e1e", root, outline=False)
            box(f"벌머리{i}", (4, -2, -2), (7, 2, 2), "#2a2a2a", root)
            for side in (-1, 1):  # 눈은 양쪽 옆에(왼쪽으로 날면 몸이 반 바퀴 돌아 반대쪽이 보임)
                y0, y1 = (-2.15, -2.0) if side < 0 else (2.0, 2.15)
                if pr.get("눈색"):  # 크고 빛나는 눈 + 화난 눈썹(여왕벌)
                    box(f"벌눈{i}{side}", (4.7, y0, -0.6), (6.7, y1, 1.2), pr["눈색"], root, glow=4.0, outline=False)
                    box(f"벌눈썹{i}{side}", (4.3, y0 - 0.05 * side, 1.3), (7.0, y1 - 0.05 * side + 0.1, 2.0), "#000000",
                        root, (5.6, 0, 1.6), rot=(0, -25, 0), outline=False)
                else:
                    box(f"벌눈{i}{side}", (5.2, y0, 0), (6.4, y1, 1.2), "#ffffff", root, outline=False)
            if pr.get("왕관"):  # 금색 왕관: 띠 + 뾰족한 꼭지 3개 + 빨간 보석
                gold = pr.get("왕관색", "#ffcc00")
                box(f"왕관띠{i}", (4.0, -2.1, 2.0), (7.0, 2.1, 3.0), gold, root)
                for k, x in enumerate((4.2, 5.15, 6.1)):
                    box(f"왕관꼭지{i}_{k}", (x, -1.2, 3.0), (x + 0.7, 1.2, 4.3 if k == 1 else 3.8), gold, root)
                for side, (y0, y1) in ((-1, (-2.25, -2.1)), (1, (2.1, 2.25))):
                    box(f"왕관보석{i}{side}", (5.1, y0, 2.2), (5.9, y1, 2.8), "#ff2040", root, glow=3.0, outline=False)
            box(f"벌침{i}", (-6.5, -0.5, -0.7), (-4, 0.5, 0.3), "#1e1e1e", root)
            for wy in (-1.2, 1.2):
                w = box(f"벌날개{i}_{wy}", (-3, wy - 0.2, 2.5), (1.5, wy + 0.2, 7), "#dff4ff", root, (-1, wy, 2.5))
                w["날개"] = 1 if wy < 0 else -1
        elif kind == "통나무":  # 끝면(나이테)이 화면 쪽, 옆으로 굴러감. 반지름 = "반지름"(m)
            r = float(pr.get("반지름", 0.6)) / U
            L = float(pr.get("길이", 0.9)) / U
            cyl(f"통껍질{i}", r, -L, L, pr.get("색", "#7a4a22"), root)
            cyl(f"나이테{i}", r * 0.8, -L - 0.08, -L + 0.5, "#e0b070", root, outline=False)
            cyl(f"속나이테{i}", r * 0.42, -L - 0.14, -L + 0.5, "#b98447", root, outline=False)
            a = r
            box(f"나이테줄{i}", (-0.35, -L - 0.2, 0), (0.35, -L - 0.1, a * 0.75), "#6b3d17", root, outline=False)  # 도는 게 보이게
            root["반지름"] = r * U
        elif kind == "돌":  # 울퉁불퉁한 돌(상자 3개), 떨어지며 돎
            a = float(pr.get("반지름", 0.5)) / U * 0.8
            c = pr.get("색", "#8d8d8d")
            box(f"돌{i}", (-a, -a, -a), (a, a, a * 0.85), c, root)
            box(f"돌위{i}", (-a * 0.7, -a * 0.9, a * 0.5), (a * 0.6, a * 0.9, a * 1.1), pr.get("색2", "#a9a9a9"), root)
            box(f"돌옆{i}", (a * 0.4, -a * 0.8, -a * 0.9), (a * 1.25, a * 0.8, a * 0.3), pr.get("색3", "#6f6f6f"), root)
            box(f"돌왼{i}", (-a * 1.2, -a * 0.75, -a * 0.6), (-a * 0.3, a * 0.75, a * 0.55), pr.get("색2", "#a9a9a9"), root)
            box(f"돌밑{i}", (-a * 0.6, -a * 0.85, -a * 1.15), (a * 0.7, a * 0.85, -a * 0.3), pr.get("색3", "#6f6f6f"), root)
            box(f"돌꼭대기{i}", (-a * 0.25, -a * 0.6, a * 0.9), (a * 0.35, a * 0.6, a * 1.3), pr.get("색3", "#6f6f6f"), root)
            root["돌기"] = float(pr.get("돌기", 6.0))
        elif kind == "딱정벌레":  # 바닥을 기어 다니는 적(바닥이 기준, 머리가 +X), 다리를 번갈아 움직임
            sc = pr.get("색", "#b3202a")
            box(f"벌레등{i}", (-5, -3.5, 2), (4, 3.5, 7), sc, root)
            box(f"벌레등줄{i}", (-0.3, -3.6, 2.5), (0.3, 3.6, 7.05), "#1e1e1e", root, outline=False)
            for k, (x, z) in enumerate([(-3, 5), (2, 4.5), (-1.5, 3)]):
                box(f"벌레점{i}_{k}", (x, -3.7, z), (x + 1.2, -3.55, z + 1.2), "#1e1e1e", root, outline=False)
                box(f"벌레점뒤{i}_{k}", (x, 3.55, z), (x + 1.2, 3.7, z + 1.2), "#1e1e1e", root, outline=False)
            box(f"벌레머리{i}", (4, -2.2, 2.2), (7, 2.2, 5.5), "#262626", root)
            for sy, (y0, y1) in ((-1, (-2.35, -2.2)), (1, (2.2, 2.35))):
                box(f"벌레눈{i}{sy}", (5.3, y0, 3.8), (6.3, y1, 4.8), "#ffffff", root, outline=False)
            for k, x in enumerate((-3.5, -0.5, 2.5)):
                for sy in (-1, 1):
                    lg = box(f"벌레다리{i}_{k}{sy}", (x - 0.4, sy * 3.2 - 0.4, 0), (x + 0.4, sy * 3.2 + 0.4, 2.5), "#1e1e1e", root,
                             (x, sy * 3.2, 2.5))
                    lg["다리"] = 1 if (k % 2 == 0) == (sy > 0) else -1
        elif kind == "불덩이":  # 빛나는 불덩이(빙글 돎)
            a = float(pr.get("반지름", 0.45)) / U
            box(f"불겉{i}", (-a, -a, -a), (a, a, a), "#ff5a1f", root, glow=3.0)
            box(f"불속{i}", (-a * 0.6, -a * 1.05, -a * 0.6), (a * 0.6, -a * 0.95, a * 0.6), "#ffe14d", root, glow=4.0, outline=False)
            box(f"불꼬리{i}", (-a * 0.5, -a * 0.5, a), (a * 0.5, a * 0.5, a * 1.7), "#ff9a1f", root, glow=3.0)
            root["돌기"] = float(pr.get("돌기", 9.0))
        elif kind == "운석":  # 불꼬리 달린 운석(꼬리는 날아온 쪽, 가는 방향 = +X)
            a = float(pr.get("반지름", 0.55)) / U * 0.8
            box(f"운석{i}", (-a, -a, -a), (a, a, a), pr.get("색", "#6b4a3a"), root)
            box(f"운석위{i}", (-a * 0.6, -a * 0.9, a * 0.5), (a * 0.7, a * 0.9, a * 1.15), "#8a6450", root)
            box(f"운석빛{i}", (a * 0.2, -a * 1.05, -a * 0.6), (a * 1.05, -a * 0.95, a * 0.6), "#ffb347", root, glow=3.0, outline=False)
            for k, (l0, l1, w, c) in enumerate([(-a * 1.0, -a * 3.0, a * 0.85, "#ff5a1f"), (-a * 2.6, -a * 5.0, a * 0.55, "#ff9a1f"),
                                                (-a * 4.6, -a * 6.8, a * 0.3, "#ffe14d")]):
                box(f"운석꼬리{i}_{k}", (l1, -w, -w), (l0, w, w), c, root, glow=3.0, outline=False)
        elif kind == "조각":  # 부서진 돌 조각
            a = float(pr.get("반지름", 0.12)) / U
            box(f"조각{i}", (-a, -a, -a), (a, a, a), pr.get("색", "#8d8d8d"), root)
            root["돌기"] = float(pr.get("돌기", 12.0))
        elif kind == "감옥":  # 앞쪽 창살 + 위·아래 틀(바닥 가운데가 기준). 위로 올리면 열림
            w, h = float(pr.get("너비", 2.8)) / U / 2, float(pr.get("높이", 2.6)) / U
            c = pr.get("색", "#5b5f73")
            box(f"감옥위{i}", (-w, -9, h - 1.5), (w, 9, h), c, root)
            box(f"감옥아래{i}", (-w, -9, 0), (w, 9, 1.0), c, root)
            for sx in (-1, 1):
                box(f"감옥기둥{i}{sx}", (sx * w - 1, -9, 0), (sx * w + 1, -7.5, h), c, root)
            x = -w + 4
            k = 0
            while x < w - 2:
                box(f"창살{i}_{k}", (x - 0.5, -9, 1.0), (x + 0.5, -8.2, h - 1.5), c, root)
                x += 4
                k += 1
        elif kind == "하트":  # 픽셀 하트
            pat = [".XX.XX.", "XXXXXXX", "XXXXXXX", ".XXXXX.", "..XXX..", "...X..."]
            px_ = float(pr.get("크기", 0.18)) / U
            for r_, row in enumerate(pat):
                for c_, ch_ in enumerate(row):
                    if ch_ == "X":
                        x0 = (c_ - 3.5) * px_
                        z0 = (len(pat) - r_) * px_
                        box(f"하트{i}_{r_}_{c_}", (x0, -0.5, z0), (x0 + px_, 0.5, z0 + px_), pr.get("색", "#ff3366"), root,
                            outline=False)
        elif kind == "글자":  # 점수 같은 글자(숫자·영어)
            cu = bpy.data.curves.new(f"글자{i}", "FONT")
            cu.body = pr.get("내용", "+100")
            fp = pr.get("글꼴", "/usr/share/fonts/truetype/nanum/NanumSquareB.ttf")  # 한글 되는 글꼴
            if os.path.exists(fp):
                cu.font = bpy.data.fonts.load(fp)
            cu.align_x = "CENTER"
            cu.size = pr.get("글자크기", 0.8)
            cu.extrude = 0.03
            tx = bpy.data.objects.new(f"글자{i}", cu)
            tx.data.materials.append(mat(pr.get("색", "#ffe14d")))
            tx.parent = root
            tx.rotation_euler = (math.radians(90), 0, 0)
            bpy.context.scene.collection.objects.link(tx)
        else:  # 광선 덩어리
            c = pr.get("색", "#7CFF4F")
            box(f"광선{i}", (-4, -2, -2), (4, 2, 2), c, root, glow=4.0)
            box(f"광선꼬리{i}", (4, -1, -1), (9, 1, 1), "#c8ffb0", root, glow=4.0)
        k = 1.0 if kind == "하트" else float(pr.get("크기", 1.0))  # 하트는 '크기'가 점 크기(두 번 곱하지 않음)
        root.scale = (k, k, k)
        root["기본크기"] = k
        root["화면고정"] = int(bool(pr.get("화면고정", False)))
        keys = sorted(pr["동작"], key=lambda k: k["초"])
        root["모양"] = kind
        root["맞은초"] = float(pr.get("맞은초", 1e9))
        root["등속"] = int(bool(pr.get("등속", kind == "통나무")))  # 통나무는 같은 빠르기로 굴러감
        if kind == "글자" and pr.get("바뀜"):  # [[초, 내용], ...] — 점수판처럼 시간마다 글자가 바뀜
            root["바뀜"] = json.dumps(pr["바뀜"], ensure_ascii=False)
        props.append((root, keys))
    cams = sorted(S.get("카메라", [{"초": 0, "위치": [0, -8, 2], "보는곳": [0, 0, 1]}]), key=lambda k: k["초"])
    cam = add_camera(cams[0]["위치"], cams[0]["보는곳"], cams[0].get("렌즈", 35), ortho=cams[0].get("직교"))
    tmpd = tempfile.mkdtemp()
    # 슬로모션: [[시작초, 끝초, 빠르기]] — 그 구간은 장면 시간이 천천히 흐름(0.3 = 세 배 느리게)
    slow = S.get("슬로", [])

    def rate(tt):
        for s0, s1, rr in slow:
            if s0 <= tt < s1:
                return float(rr)
        return 1.0
    times = []
    tt = 0.0
    while tt < sec - 1e-9:
        times.append(tt)
        tt += rate(tt) / fps
    n = len(times)
    import bisect

    def tau(ts):  # 장면 시각 → 영상 시각(슬로모션 때문에 늘어남)
        return bisect.bisect_left(times, ts) / fps
    flashes = S.get("번쩍", [])  # [[초, 길이, 색]] — 배경이 잠깐 그 색으로(맞았을 때 빨강)
    sky_lin = tuple(bpy.context.scene.world.color)
    walk_phase = {}
    for f, t in enumerate(times):
        dt = rate(t) / fps
        fc = None
        for ft, fd, fcol in flashes:
            if ft <= t < ft + fd:
                fc = tuple(_lin(v) for v in _hex(fcol))
        bpy.context.scene.world.color = fc or sky_lin
        for a, rig, keys in actors:
            pos = _track(keys, t, "위치", a.get("위치", [0, 0]))
            pos = _track([{"초": -1, "위치": a.get("위치", [0, 0])}] + keys, t, "위치", pos)
            yaw = _track([{"초": -1, "방향": a.get("방향", 0)}] + keys, t, "방향", a.get("방향", 0))
            pose = _pose_at(keys, t)
            ph = walk_phase.get(a["이름"], 0.0)
            if pose in ("걷기", "달리기", "오르기"):
                ph += {"걷기": 1.0, "달리기": 1.6, "오르기": 1.8}[pose] * dt
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
        # 화면 고정(점수·시간·목숨): 확대해도 화면의 같은 자리·같은 크기
        base_look = cams[0]["보는곳"]
        ratio = (cam.data.ortho_scale / cams[0]["직교"]) if cams[0].get("직교") else 1.0
        for root, keys in props:
            vis = keys[0]["초"] <= t <= keys[-1]["초"]
            for ch in [root] + list(root.children):
                ch.hide_render = not vis
            if vis:
                lin = bool(root.get("등속", 0))
                p = _track(keys, t, "위치", keys[0]["위치"], lin)
                p2 = _track(keys, min(t + 0.02, keys[-1]["초"]), "위치", p, lin)
                root.location = p
                if root.get("화면고정"):
                    root.location = (ck[0] + (p[0] - base_look[0]) * ratio, p[1], ck[2] + (p[2] - base_look[2]) * ratio)
                    kk = root["기본크기"] * ratio
                    root.scale = (kk, kk, kk)
                kind = root["모양"]
                if kind == "벌":  # 가는 쪽을 봄, 날개는 한 장면씩 위·아래(옛날 게임식), 맞으면 빙글 돌며 떨어짐
                    dead = t >= root["맞은초"]
                    face = math.pi if p2[0] - p[0] < -1e-6 else 0.0
                    if abs(p2[0] - p[0]) > 1e-6 and t + 0.05 < root["맞은초"]:  # 맞은 뒤엔 방향 그대로
                        root["face"] = face
                    spin = (t - root["맞은초"]) * 14 if dead else 0.0
                    root.rotation_euler = (spin, 0, root.get("face", math.pi))
                    for ch in root.children:
                        if "날개" in ch:
                            ang = 0 if dead else (45 if f % 2 else -15)
                            ch.rotation_euler = (math.radians(ang * ch["날개"]), 0, 0)
                elif kind == "딱정벌레":  # 가는 쪽을 봄, 다리를 번갈아
                    if abs(p2[0] - p[0]) > 1e-6:
                        root["face"] = math.pi if p2[0] - p[0] < 0 else 0.0
                    root.rotation_euler = (0, 0, root.get("face", 0.0))
                    for ch in root.children:
                        if "다리" in ch:
                            ch.rotation_euler = (0, math.radians(25 * ch["다리"] * (1 if (f // 2) % 2 else -1)), 0)
                elif kind == "불덩이":  # 굴러가는 쪽으로 돎(불꼬리는 위로 가게 몸통만)
                    root["각"] = root.get("각", 0.0) + root["돌기"] * dt
                    root.rotation_euler = (0, root["각"], 0)
                elif kind in ("돌", "조각"):  # 떨어지는 동안만 돎(땅에 닿으면 멈춤)
                    moving = abs(p2[2] - p[2]) > 1e-6 or abs(p2[0] - p[0]) > 1e-6
                    if moving:
                        root["각"] = root.get("각", 0.0) + root["돌기"] * dt
                    elif kind == "돌":  # 땅에 닿으면 가장 가까운 평평한 면으로 놓임(모서리로 서 있지 않게)
                        root["각"] = round(root.get("각", 0.0) / (math.pi / 2)) * (math.pi / 2)
                    root.rotation_euler = (0.3 if moving or kind == "조각" else 0.0, root.get("각", 0.0), 0)
                elif kind == "통나무":  # 간 거리만큼 굴러 돎
                    root.rotation_euler = (0, -(keys[0]["위치"][0] - p[0]) / root["반지름"], 0)
                elif kind == "글자":
                    if "바뀜" in root:
                        body = None
                        for tt, txt in json.loads(root["바뀜"]):
                            if tt <= t:
                                body = txt
                        if body is not None:
                            for ch in root.children:
                                ch.data.body = body
                elif abs(p2[0] - p[0]) > 1e-6 or abs(p2[2] - p[2]) > 1e-6:
                    root.rotation_euler = (0, -math.atan2(p2[2] - p[2], p2[0] - p[0]), 0)
        bpy.context.scene.render.filepath = os.path.join(tmpd, f"{f:05d}.png")
        bpy.ops.render.render(write_still=True)
        if f % fps == 0:
            print(f"  {f}/{n} 장", flush=True)
    # 소리: 날아가는 물체·동작에서 자동 효과음 + 장면 파일의 "효과음" + 8비트 배경음 (레트로소리.py)
    audio = None
    if S.get("소리", True):
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import 레트로소리 as RS
        ev = [(float(e["초"]), e["소리"]) for e in S.get("효과음", [])]
        if S.get("자동효과음", True):
            for pr in S.get("물체", []):
                ks = sorted(pr["동작"], key=lambda k: k["초"])
                kind = pr.get("모양", "화살")
                if kind == "벌":
                    ev.append((ks[0]["초"], "윙윙"))
                    if "맞은초" in pr:
                        ev.append((float(pr["맞은초"]) + 0.05, "동전"))
                    continue
                if kind == "글자":
                    continue
                if kind in ("돌", "조각", "운석"):
                    if pr.get("휘익"):
                        ev.append((ks[0]["초"], "휘익"))
                    for tb in pr.get("쿵", []):
                        ev.append((float(tb), "착지"))
                        ev.append((float(tb) + 0.03, "부서짐"))
                    continue
                if kind == "통나무":
                    ev.append((ks[0]["초"], "데굴데굴"))
                    for tb in pr.get("쿵", []):  # 떨어져 닿는 시각
                        ev.append((float(tb), "착지"))
                    continue
                ev.append((ks[0]["초"], "활" if kind == "화살" else "광선"))
                if pr.get("맞힘", kind == "화살"):
                    ev.append((ks[-1]["초"], "맞음"))
            auto = {"점프": "점프", "쓰러짐": "쓰러짐", "놀람": "놀람"}
            for a, rig, keys in actors:
                prev = "서기"
                for k in keys:
                    if "자세" in k:
                        if k["자세"] in auto and k["자세"] != prev and k["초"] > 0:
                            ev.append((k["초"], auto[k["자세"]]))
                        prev = k["자세"]
        bg = S.get("배경음", {"곡": "레트로전투"})
        ev = [(tau(t_), nm) for t_, nm in ev]  # 슬로모션만큼 효과음 시각도 옮김
        tempo = [(tau(a_), b_) for a_, b_ in (bg.get("빠르기", []) if bg else [])]
        x = RS.mix(n / fps, ev, music=bg.get("곡") if bg else None, music_vol=float(bg.get("크기", 0.35)) if bg else 0,
                   music_end=tau(bg["끝"]) if bg and bg.get("끝") is not None else None, tempo=tempo)
        audio = os.path.join(tmpd, "소리.wav")
        RS.write_wav(audio, x)
        print("  효과음:", ", ".join(f"{t:.1f}초 {n}" for t, n in sorted(ev)))
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(fps), "-i", os.path.join(tmpd, "%05d.png")]
    if audio:  # 입력(그림·소리)을 먼저, 그다음 출력 설정
        cmd += ["-i", audio, "-map", "0:v", "-map", "1:a", "-c:a", "aac", "-b:a", "192k", "-shortest"]
    if px:
        cmd += ["-vf", f"scale=iw*{px}:ih*{px}:flags=neighbor"]
    cmd += ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "12", "-tune", "animation", out]
    subprocess.run(cmd, check=True)
    pv = S.get("미리보기")  # {"초": [시작, 끝], "글자": "..."} — 그 구간을 맨 앞에 한 번 더(자막과 함께)
    if pv:
        a_, b_ = tau(pv["초"][0]), tau(pv["초"][1])
        main_ = out + ".본편.mp4"
        os.replace(out, main_)
        font = "/usr/share/fonts/truetype/nanum/NanumSquareB.ttf"
        txt = pv.get("글자", "").replace(":", "\\:").replace("'", "")
        fil = (f"[0:v]trim={a_}:{b_},setpts=PTS-STARTPTS,"
               f"drawtext=fontfile={font}:text='{txt}':fontsize=84:fontcolor=white:borderw=6:bordercolor=black:"
               f"x=(w-text_w)/2:y=h*0.42[pv];"
               f"[0:a]atrim={a_}:{b_},asetpts=PTS-STARTPTS[pa];"
               f"[pv][pa][0:v][0:a]concat=n=2:v=1:a=1[v][a]")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", main_, "-filter_complex", fil, "-map", "[v]", "-map", "[a]",
                        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "12", "-tune", "animation", "-c:a", "aac",
                        "-b:a", "192k", out], check=True)
        os.remove(main_)
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
    if cmd == "합치기":  # 합치기 결과.mp4 1판.mp4 2판.mp4 … — 판 영상들을 차례로 이어 붙임
        ins = argv[2:]
        args = ["ffmpeg", "-y", "-loglevel", "error"]
        for f in ins:
            args += ["-i", f]
        fil = "".join(f"[{i}:v][{i}:a]" for i in range(len(ins))) + f"concat=n={len(ins)}:v=1:a=1[v][a]"
        args += ["-filter_complex", fil, "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                 "-crf", "12", "-tune", "animation", "-c:a", "aac", "-b:a", "192k", argv[1]]
        subprocess.run(args, check=True)
        print("합친 영상:", argv[1])
        return
    if cmd == "시트":
        cmd_sheet(argv[1], argv[2], names)
    elif cmd == "장면":
        cmd_scene(argv[1], argv[2], fancy)
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
