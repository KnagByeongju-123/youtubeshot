"""MPFB(MakeHuman for Blender, CC0 재료)로 동양 여성 아나운서 만들기 → 우리 촬영 도구용 GLB (사용자 2026-11-26 'MPFB로 동양 여성 아나운서 만들어줘')
   준비(한 번): MPFB 추가 기능 설치 + 재료 묶음(makehuman_system_assets, visemes01, faceunits01, 옷 묶음)을
               ~/.config/blender/5.0/extensions/.user/user_default/mpfb/data 에 풂 (실사3D.md 'MPFB' 참고)
   하는 일: 몸(여성·동양·나이·키 등) → 피부·눈·눈썹·속눈썹·이·혀·머리·옷·신발 → 게임 엔진 뼈대 →
           말하기 입 모양(마이크로소프트 15가지) + 얼굴 표정(ARKit 52가지) → 숨은 도움 정점·옷에 가려진 몸 정점 지우기 →
           뼈 이름을 야외_오르빗.py 이름으로(upperarm_l → UpperArm.L …), 모양 키 MouthOpen/Wide/Round·Blink → GLB
   사용: .bpy_venv/bin/python -I 애니3D/mpfb_아나운서.py <출력.glb> [--설정 설정.json]
   설정(json, 없으면 기본): {"phenotype": {...}, "skin": "young_asian_female", "hair": "bob01", "clothes": [...], "eyebrows": ...}"""
import json, os, sys
import bpy, bmesh

a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
dst = a[0]
cfg = json.load(open(a[a.index("--설정") + 1], encoding="utf-8")) if "--설정" in a else {}
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.preferences.addon_enable(module="bl_ext.user_default.mpfb")
import importlib
M = "bl_ext.user_default.mpfb.services."
HumanService = importlib.import_module(M + "humanservice").HumanService
FaceService = importlib.import_module(M + "faceservice").FaceService

ph = {"gender": 0.0, "age": 0.43, "muscle": 0.45, "weight": 0.42, "proportions": 0.75, "height": 0.45, "cupsize": 0.45, "firmness": 0.55,
      "race": {"asian": 1.0, "caucasian": 0.0, "african": 0.0}}           # 여성(0)·나이 0.43(약 28세)·동양 100%
ph.update(cfg.get("phenotype", {}))
hi = HumanService._create_default_human_info_dict()
hi.update({"name": "아나운서", "phenotype": ph, "rig": cfg.get("rig", "game_engine"),
           "eyes": "high-poly/high-poly.mhclo", "eyebrows": f"{cfg.get('eyebrows', 'eyebrow010')}/{cfg.get('eyebrows', 'eyebrow010')}.mhclo",
           "eyelashes": "eyelashes01/eyelashes01.mhclo", "teeth": "teeth_base/teeth_base.mhclo", "tongue": "tongue01/tongue01.mhclo",
           "hair": f"{cfg.get('hair', 'bob01')}/{cfg.get('hair', 'bob01')}.mhclo",
           "skin_mhmat": f"{cfg.get('skin', 'young_asian_female')}/{cfg.get('skin', 'young_asian_female')}.mhmat", "skin_material_type": "ENHANCED",
           "clothes": [f"{c}/{c}.mhclo" if "/" not in c else c for c in cfg.get("clothes", ["female_elegantsuit01", "shoes06"])],
           "alternative_materials": {}})
st = HumanService.get_default_deserialization_settings(); st["subdiv_levels"] = 0
basemesh = HumanService.deserialize_from_dict(hi, st)
FaceService.load_targets(basemesh, load_microsoft_visemes=True, load_meta_visemes=False, load_arkit_faceunits=True)
print("몸 만듦:", basemesh.name, len(basemesh.data.vertices), "모양 키", len(basemesh.data.shape_keys.key_blocks) if basemesh.data.shape_keys else 0)

# 숨은 도움 정점·옷에 가려진 몸 정점: 마스크 수정자 대신 정점을 지움 (glTF 로 내보낼 때 모양 키를 지키려고)
bpy.context.view_layer.objects.active = basemesh
for o in [x for x in bpy.data.objects if x.type == "MESH"]:
    masks = [m for m in o.modifiers if m.type == "MASK"]
    if not masks: continue
    vg = {g.name: g.index for g in o.vertex_groups}
    me = o.data; bm = bmesh.new(); bm.from_mesh(me); dl = bm.verts.layers.deform.active
    kill = set()
    for m in masks:
        gi = vg.get(m.vertex_group)
        if gi is None or dl is None: continue
        for v in bm.verts:
            inn = gi in v[dl] and v[dl][gi] > 0.5
            if (inn and m.invert_vertex_group) or (not inn and not m.invert_vertex_group): kill.add(v)
    bmesh.ops.delete(bm, geom=list(kill), context="VERTS"); bm.to_mesh(me); bm.free()
    for m in masks: o.modifiers.remove(m)
    print("정점 지움", o.name, len(kill))
for o in bpy.data.objects:
    for m in list(o.modifiers) if o.type == "MESH" else []:
        if m.type in ("SUBSURF", "CORRECTIVE_SMOOTH"): o.modifiers.remove(m)

# 몸 모양 키($md-… 나이·성별·인종 등)는 바탕에 굳히고, 얼굴 키는 새 바탕 기준으로 다시 계산 (내보낸 GLB 에 몸 키 60여 개가 남지 않게)
import numpy as np
kb = basemesh.data.shape_keys.key_blocks; nv = len(basemesh.data.vertices)
def co(k): arr = np.zeros(nv * 3, np.float32); k.data.foreach_get("co", arr); return arr
basis = co(kb[0]); body = [k for k in kb[1:] if k.name.startswith("$md") or k.name.startswith("$") ]
mix = basis.copy()
for k in body: mix += (co(k) - basis) * k.value
for k in kb[1:]:
    if k in body: continue
    k.data.foreach_set("co", mix + (co(k) - basis))
kb[0].data.foreach_set("co", mix)
for k in body: basemesh.shape_key_remove(k)
basemesh.data.update(); print("몸 키 굳힘", len(body))

# 모양 키 이름 맞추기
kb = basemesh.data.shape_keys.key_blocks
names = [k.name for k in kb]
def find(part): return next((n for n in names if part in n), None)
for part, new in (("aa_02", "MouthOpen"), ("y_iy_ih_ix_06", "MouthWide"), ("w_uw_07", "MouthRound")):
    n = find(part)
    if n: kb[n].name = new
l, r = find("eyeBlinkLeft"), find("eyeBlinkRight")
if l and r:
    for k in kb: k.value = 0.0
    kb[l].value = kb[r].value = 1.0; basemesh.shape_key_add(name="Blink", from_mix=True); kb[l].value = kb[r].value = 0.0
print("모양 키:", [k.name for k in kb][:8], "…", len(kb))

# 뼈 이름: 게임 엔진 뼈대 → 우리 이름
arm = next(o for o in bpy.data.objects if o.type == "ARMATURE")
FING = {"thumb": "Thumb", "index": "Index", "middle": "Middle", "ring": "Ring", "pinky": "Little"}
REN = {"pelvis": "Hips", "spine_01": "Spine", "spine_02": "Spine1", "spine_03": "Chest", "neck_01": "Neck", "head": "Head"}
for b in arm.data.bones:
    n = b.name; new = REN.get(n)
    if new is None and (n.endswith("_l") or n.endswith("_r")):
        sd = n[-1].upper(); base = n[:-2]
        parts = base.split("_")
        if parts[0] in FING: new = f"{FING[parts[0]]}{int(parts[1])}.{sd}"
        else: new = {"clavicle": "Shoulder", "upperarm": "UpperArm", "lowerarm": "ForeArm", "hand": "Hand", "thigh": "UpperLeg",
                     "calf": "LowerLeg", "foot": "Foot", "ball": "Toes"}.get(base, base) + f".{sd}"
    if new and new != n: b.name = new
print("뼈:", [b.name for b in arm.data.bones][:12])
bpy.ops.export_scene.gltf(filepath=dst, export_format="GLB", export_morph=True, export_skins=True, export_animations=False,
                          export_apply=False, export_image_format="AUTO", use_visible=False)
print("→", dst, os.path.getsize(dst) // 1024, "KB")
