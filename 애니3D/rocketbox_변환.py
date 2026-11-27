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
if "--머리" in a:   # 다른 인물의 얼굴·머리카락을 이 인물(몸·옷)에 합침 — Rocketbox 는 뼈대 자리가 모두 같아 그대로 옮겨 붙음 (사용자 2026-11-26 '정장 몸에 합쳐줘')
    import bmesh
    hf = a[a.index("--머리") + 1].rstrip("/"); hn = os.path.basename(hf)
    base = next(o for o in bpy.data.objects if o.type == "MESH")
    def keep_only(o, mats):                                   # 재질 번호(0 몸·옷, 1 얼굴·목, 2 머리카락·속눈썹) 중 mats 만 남김
        bm = bmesh.new(); bm.from_mesh(o.data)
        bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.material_index not in mats], context="FACES")
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS"); bm.to_mesh(o.data); bm.free()
    keep_only(base, {0})
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=os.path.join(hf, "Export", f"{hn}_facial.fbx"))
    new_objs = [o for o in bpy.data.objects if o not in before]
    head = next(o for o in new_objs if o.type == "MESH"); arm2 = next(o for o in new_objs if o.type == "ARMATURE")
    keep_only(head, {1, 2})
    if "--어깨자르기" in a:   # 얼굴 쪽 그물이 어깨까지 내려온 인물(민소매 Sports_Female_02 등): 목에서 옆으로 떨어진 낮은 곳의 면을 지움 (블라우스를 뚫고 살이 비쳤음, 2026-11-26)
        zc, xc = (float(t) for t in a[a.index("--어깨자르기") + 1].split(","))
        Mh = head.matrix_world; bm = bmesh.new(); bm.from_mesh(head.data)
        kill = [f for f in bm.faces if f.material_index == 1 and (lambda c: c.z < zc and abs(c.x) > xc)(Mh @ f.calc_center_median())]
        bmesh.ops.delete(bm, geom=kill, context="FACES"); bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
        bm.to_mesh(head.data); bm.free(); print("어깨 면 지움", len(kill))
    mw = head.matrix_world.copy(); head.parent = arm; head.matrix_world = mw
    for m in head.modifiers:
        if m.type == "ARMATURE": m.object = arm
    bpy.ops.object.select_all(action="DESELECT"); base.select_set(True); head.select_set(True)
    bpy.context.view_layer.objects.active = head; bpy.ops.object.join()          # 얼굴 쪽 모양 키(입 모양·표정)를 살림
    bpy.data.objects.remove(arm2, do_unlink=True)
    print("머리 합침:", hn, "→ 몸", nm)
if "--머리카락" in a:   # [--앞머리포함: 앞머리도 바꿈] 다른 인물의 머리카락 조각(재질 2 중 얼굴 뒤·옆 = 중심 y > -0.015)만 가져오고, 지금 머리카락 조각은 뺌 — 속눈썹·이(얼굴 앞)는 그대로 (사용자 2026-11-26 '긴 머리카락으로')
    import bmesh, mathutils
    hf2 = a[a.index("--머리카락") + 1].rstrip("/"); hn2 = os.path.basename(hf2)
    def hair_parts(o, keep_hair):
        M_ = o.matrix_world; bm = bmesh.new(); bm.from_mesh(o.data); bm.verts.ensure_lookup_table(); seen = set(); kill = []
        for v in bm.verts:
            if v.index in seen: continue
            st = [v]; comp = []; seen.add(v.index)
            while st:
                x = st.pop(); comp.append(x)
                for e in x.link_edges:
                    y = e.other_vert(x)
                    if y.index not in seen: seen.add(y.index); st.append(y)
            mats = {f.material_index for x in comp for f in x.link_faces}
            mat2 = mats == {len(o.material_slots) - 1} or all("opacity" in (o.material_slots[m].material.name if o.material_slots[m].material else "") for m in mats)
            ctr = sum((M_ @ x.co for x in comp), mathutils.Vector()) / len(comp)
            if "--앞머리포함" in a:   # 앞머리까지 통째로 바꿈 — 속눈썹(눈 높이의 얇은 띠: 높이 폭 3cm 미만)만 남김 (사용자 2026-11-27 '긴 생머리', 원래 옆으로 넘긴 앞머리가 남았음)
                zs = [(M_ @ x.co).z for x in comp]
                is_hair = mat2 and len(comp) < 600 and (max(zs) - min(zs) >= 0.03 or ctr.y > -0.015)
            else:
                is_hair = mat2 and len(comp) < 600 and ctr.y > -0.015
            if is_hair != keep_hair: kill += comp
        bmesh.ops.delete(bm, geom=list(set(kill)), context="VERTS"); bm.to_mesh(o.data); bm.free()
    body_o = next(o for o in bpy.data.objects if o.type == "MESH")
    hair_parts(body_o, keep_hair=False)                       # 지금 머리카락(묶은 머리 등) 뺌
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=os.path.join(hf2, "Export", f"{hn2}_facial.fbx"))
    new_objs = [o for o in bpy.data.objects if o not in before]
    hair = next(o for o in new_objs if o.type == "MESH"); arm3 = next(o for o in new_objs if o.type == "ARMATURE")
    hair_parts(hair, keep_hair=True)
    mw = hair.matrix_world.copy(); hair.parent = arm; hair.matrix_world = mw
    for m in hair.modifiers:
        if m.type == "ARMATURE": m.object = arm
    bpy.ops.object.select_all(action="DESELECT"); hair.select_set(True); body_o.select_set(True)
    bpy.context.view_layer.objects.active = body_o; bpy.ops.object.join()
    bpy.data.objects.remove(arm3, do_unlink=True)
    print("머리카락 바꿈:", hn2, "점", len(body_o.data.vertices))
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
texs = [a[a.index("--그림폴더") + 1]] if "--그림폴더" in a else []
texs += [os.path.join(folder, "Textures")] + ([os.path.join(a[a.index("--머리") + 1], "Textures")] if "--머리" in a else []) + ([os.path.join(a[a.index("--머리카락") + 1], "Textures")] if "--머리카락" in a else [])
for im in bpy.data.images:
    base = os.path.basename(im.filepath.replace("\\", "/"))
    for tex in texs:
        if os.path.exists(os.path.join(tex, base)): im.filepath = os.path.join(tex, base); im.reload(); break
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
