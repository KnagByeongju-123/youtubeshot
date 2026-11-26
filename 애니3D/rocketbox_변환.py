"""Microsoft Rocketbox 인물(MIT 라이선스, github.com/microsoft/Microsoft-Rocketbox) → 우리 촬영 도구용 GLB (사용자 2026-11-26 'Rocketbox 인물 하나 받아서 시험 촬영')
   - <이름>_facial.fbx 를 불러옴 (입 모양 15가지 AA_VI_*, 얼굴 표정 52가지 AK_* 포함)
   - 뼈 이름: 3ds Max 'Bip01 L UpperArm' → 'UpperArm.L' 처럼 야외_오르빗.py 가 쓰는 이름으로
     (Clavicle→Shoulder, Forearm→ForeArm, Finger0/01/02→Thumb1/2/3, Finger1x→Index, 2x→Middle, 3x→Ring, 4x→Little,
      Pelvis→Hips, Spine2→Chest, Thigh→UpperLeg, Calf→LowerLeg)
   - 모양 키: AA_VI_10_aa→MouthOpen, AA_VI_12_I→MouthWide, AA_VI_14_U→MouthRound, 두 눈 깜빡임 합쳐 Blink
   - 그림: FBX 안의 경로(D:/temp/...)가 틀려 Textures 폴더의 tga 로 다시 연결, 반사(specular) 그림은 뺌
   --그림폴더 <폴더> : 다시 칠한 그림(rocketbox_옷칠하기.py 결과)을 씀, --부품지우기 x,y,z[;…] : 그 자리 가장 가까운 작은 따로 떨어진 부품(점 120개 미만, 예: 입술 피어싱)을 지움
   사용: .bpy_venv/bin/python -I 애니3D/rocketbox_변환.py <인물 폴더(…/Business_Female_03)> <출력.glb> [--그림폴더 …] [--부품지우기 …]"""
import os, re, sys
import bpy

a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
folder, dst = a[0], a[1]
nm = os.path.basename(folder.rstrip("/"))
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=os.path.join(folder, "Export", f"{nm}_facial.fbx"))
arm = next(o for o in bpy.data.objects if o.type == "ARMATURE")
FING = {"0": "Thumb", "1": "Index", "2": "Middle", "3": "Ring", "4": "Little"}
def newname(b):
    m = re.match(r"Bip01 ([LR]) (\w+)$", b)
    if m:
        sd, part = m.groups()
        f = re.match(r"Finger(\d)(\d?)$", part)
        if f: return f"{FING[f.group(1)]}{int(f.group(2) or 0) + 1}.{sd}"
        return {"Clavicle": "Shoulder", "UpperArm": "UpperArm", "Forearm": "ForeArm", "Hand": "Hand",
                "Thigh": "UpperLeg", "Calf": "LowerLeg", "Foot": "Foot", "Toe0": "Toes"}.get(part, part) + f".{sd}"
    return {"Bip01 Pelvis": "Hips", "Bip01 Spine": "Spine", "Bip01 Spine1": "Spine1", "Bip01 Spine2": "Chest",
            "Bip01 Neck": "Neck", "Bip01 Head": "Head", "Bip01 MJaw": "Jaw"}.get(b, b)
ren = {}
for b in arm.data.bones:
    n2 = newname(b.name)
    if n2 != b.name: ren[b.name] = n2
for o in bpy.data.objects:                                    # 정점 그룹 이름도 같이 (블렌더는 뼈 이름을 바꾸면 자동으로 바꿈 — 그래도 확인)
    if o.type == "MESH":
        for g in o.vertex_groups:
            if g.name in ren: g.name = ren[g.name]
for b in arm.data.bones:
    if b.name in ren: b.name = ren[b.name]
print("뼈 이름 바꿈", len(ren))
if "--부품지우기" in a:                                        # 작은 따로 떨어진 부품(피어싱 등) 지우기
    import bmesh, mathutils
    o = next(x for x in bpy.data.objects if x.type == "MESH"); M = o.matrix_world
    bm = bmesh.new(); bm.from_mesh(o.data); bm.verts.ensure_lookup_table(); seen = set(); parts = []
    for v in bm.verts:
        if v.index in seen: continue
        st = [v]; comp = []; seen.add(v.index)
        while st:
            x = st.pop(); comp.append(x)
            for e in x.link_edges:
                y = e.other_vert(x)
                if y.index not in seen: seen.add(y.index); st.append(y)
        if len(comp) < 120: parts.append(comp)
    kill = []
    for p_ in a[a.index("--부품지우기") + 1].split(";"):
        tgt = mathutils.Vector([float(t) for t in p_.split(",")])
        best = min(parts, key=lambda c: ((sum((M @ v.co for v in c), mathutils.Vector()) / len(c)) - tgt).length)
        kill += best; print("부품 지움: 점", len(best))
    bmesh.ops.delete(bm, geom=list(set(kill)), context="VERTS"); bm.to_mesh(o.data); bm.free()
tex = a[a.index("--그림폴더") + 1] if "--그림폴더" in a else os.path.join(folder, "Textures")
for im in bpy.data.images:
    base = os.path.basename(im.filepath.replace("\\", "/"))
    if os.path.exists(os.path.join(tex, base)): im.filepath = os.path.join(tex, base); im.reload()
for o in bpy.data.objects:
    if o.type != "MESH": continue
    for m in o.data.materials:
        nt = m.node_tree
        for n in list(nt.nodes):
            if n.type == "TEX_IMAGE" and n.image and "specular" in n.image.filepath: nt.nodes.remove(n)
        if "opacity" in m.name:                                # 머리카락·속눈썹: 그림의 투명도를 씀
            bs = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
            ti = next((n for n in nt.nodes if n.type == "TEX_IMAGE" and n.image and "color" in n.image.filepath), None)
            if ti: nt.links.new(ti.outputs["Alpha"], bs.inputs["Alpha"])
            m.blend_method = "HASHED" if hasattr(m, "blend_method") else None
    kb = o.data.shape_keys.key_blocks if o.data.shape_keys else {}
    for old, new in (("AA_VI_10_aa", "MouthOpen"), ("AA_VI_12_I", "MouthWide"), ("AA_VI_14_U", "MouthRound")):
        if old in kb: kb[old].name = new
    l, r = kb.get("AK_09_EyeBlinkLeft"), kb.get("AK_10_EyeBlinkRight")
    if l and r:
        for k in kb: k.value = 0.0
        l.value = r.value = 1.0
        bl = o.shape_key_add(name="Blink", from_mix=True); l.value = r.value = 0.0
    print("모양 키", o.name, len(kb))
bpy.ops.export_scene.gltf(filepath=dst, export_format="GLB", export_morph=True, export_skins=True, export_animations=False, export_image_format="AUTO")
print("→", dst, os.path.getsize(dst) // 1024, "KB")
