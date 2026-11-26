"""GLB 사람 모델의 손(손목부터)을 다른 GLB 사람의 손으로 바꿈 (사용자 2026-11-26 '여자아나운서A 손목만 B 것으로 교체 테스트')
   - 두 모델의 뼈 이름이 같아야 함(Hand.L·Index1.L … — 여자아나운서A·B 모두 이 이름)
   - 손 맞추기: 손목(Hand 뼈 머리) 자리, 손목→중지 뿌리 방향, 검지→새끼 뿌리 방향으로 '손 틀'을 만들어 B 손을 A 손 자리로 돌려 옮김,
     크기는 손목→중지 끝마디 길이 비율 (--크기 로 더 곱함)
   - A: 손목에서 --자르기(m, 손 쪽 +) 넘어가고 손·손가락 뼈 무게가 반 넘는 점을 지움 (치마처럼 손 옆 다른 부분은 그대로)
     B: 손목에서 --겹침(m) 만큼 팔 쪽까지 포함해 떼어 옴 → 소매·손목 안으로 살짝 들어가 틈이 없게
   - A 의 손가락 뼈는 옮겨 온 B 손가락 자리로 옮김(굽힘이 새 손가락에 맞게). 새 손은 B 의 피부 그림을 그대로 쓰는 따로 된 부품(Hand_B)
   - --밝기 r,g,b : 새 손 피부 그림 색에 곱함(A 피부와 맞추기)
   사용: .bpy_venv/bin/python -I 애니3D/glb_손바꾸기.py <A.glb> <B.glb> <결과.glb> [--자르기 0.0] [--겹침 0.012] [--크기 1.0] [--밝기 1,1,1] [--어두움 0.18 (이보다 어두운 그림 면 = 소매, 뺌)]
         [--겹침 0.012] [--손목굵기 1.0 (A 손목 굵기에 맞춘 뒤 더 곱함, 0 = 안 맞춤)] [--이음 0.035 (손 쪽으로 이만큼 가며 원래 굵기로)] [--손목최대 1.4 (굵게 하는 최대 배율 — 너무 굵으면 손목이 퉁퉁해 보임)]"""
import sys

import bpy
import bmesh
from mathutils import Matrix, Vector

a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
def opt(k, d):
    return a[a.index(k) + 1] if k in a else d
SRC_A, SRC_B, DST = a[0], a[1], a[2]
CUT, OVER, SC = float(opt("--자르기", 0.0)), float(opt("--겹침", 0.012)), float(opt("--크기", 1.0))
TINT = [float(x) for x in opt("--밝기", "1,1,1").split(",")]
FING = ["Thumb", "Index", "Middle", "Ring", "Little"]

bpy.ops.wm.read_factory_settings(use_empty=True)
def load(p):
    before = set(bpy.data.objects); bpy.ops.import_scene.gltf(filepath=p)
    new = [o for o in bpy.data.objects if o not in before]
    return [o for o in new if o.type == "ARMATURE"][0], new
armA, newA = load(SRC_A)
armB, newB = load(SRC_B)
bodyA = max((o for o in newA if o.type == "MESH" and o.vertex_groups), key=lambda o: len(o.data.vertices))
bodyB = max((o for o in newB if o.type == "MESH" and o.vertex_groups), key=lambda o: len(o.data.vertices))

def head(arm, n): return arm.matrix_world @ arm.data.bones[n].head_local
def frame(arm, s):
    H = head(arm, f"Hand.{s}"); M1 = head(arm, f"Middle1.{s}")
    x = (M1 - H).normalized(); side = (head(arm, f"Index1.{s}") - head(arm, f"Little1.{s}")).normalized()
    z = x.cross(side).normalized(); y = z.cross(x).normalized()
    R = Matrix((x, y, z)).transposed()          # 열 = 축
    L = (head(arm, f"Middle3.{s}") - H).length
    d = (H - head(arm, f"ForeArm.{s}")).normalized()
    return H, R, L, d

hand_groups = lambda s: {f"Hand.{s}"} | {f"{f}{k}.{s}" for f in FING for k in (1, 2, 3)}

def weight_in(obj, v, names):
    t = 0.0
    for g in v.groups:
        if obj.vertex_groups[g.group].name in names: t += g.weight
    return t

DARK = float(opt("--어두움", 0.18))
WIDEN, BLEND, WMAX = float(opt("--손목굵기", 1.0)), float(opt("--이음", 0.035)), float(opt("--손목최대", 1.4))
_px = {}
def skin_px(obj, mi):
    """재질 mi 의 바탕색 그림 점들(RGBA 평평한 목록), 없으면 None"""
    if mi >= len(obj.material_slots) or not obj.material_slots[mi].material: return None
    m = obj.material_slots[mi].material
    if m.name in _px: return _px[m.name]
    r = None
    if m.use_nodes:
        bs = next((n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
        lk = bs.inputs["Base Color"].links if bs else None
        n = lk[0].from_node if lk else None
        while n is not None and n.type != "TEX_IMAGE":
            ins = [i for i in n.inputs if i.links]; n = ins[0].links[0].from_node if ins else None
        if n is not None and n.image: r = (list(n.image.pixels[:]), n.image.size[0], n.image.size[1])
    _px[m.name] = r; return r

new_parts = []
for s in ("L", "R"):
    HA, RA, LA, dA = frame(armA, s); HB, RB, LB, dB = frame(armB, s)
    k = LA / LB * SC
    T = lambda p: HA + k * (RA @ (RB.transposed() @ (p - HB)))
    print(f"손 {s}: A 길이 {LA:.3f} B 길이 {LB:.3f} → 크기 {k:.3f}")
    # ── A 손 지우기
    names = hand_groups(s); mw = bodyA.matrix_world
    bm = bmesh.new(); bm.from_mesh(bodyA.data); bm.verts.ensure_lookup_table()
    me = bodyA.data
    # A 손목 굵기(자르는 자리 바로 앞 1cm 점들의 팔 축에서 평균 거리)
    def radial(p, H, d): q = p - H; return (q - d * q.dot(d)).length
    ring = [radial(mw @ v.co, HA, dA) for v in me.vertices if CUT - 0.012 < (mw @ v.co - HA).dot(dA) <= CUT and weight_in(bodyA, v, names | {f"ForeArm.{s}"}) > 0.5]
    rA = sorted(ring)[len(ring) // 2] if ring else None
    kill = [bm.verts[i] for i, v in enumerate(me.vertices)
            if (mw @ v.co - HA).dot(dA) > CUT and weight_in(bodyA, v, names) > 0.5]
    print(f"  A 에서 지운 점 {len(kill)}")
    bmesh.ops.delete(bm, geom=kill, context="VERTS"); bm.to_mesh(me); bm.free()
    # ── B 손 떼어 오기
    bpy.ops.object.select_all(action="DESELECT"); bodyB.select_set(True); bpy.context.view_layer.objects.active = bodyB
    bpy.ops.object.duplicate(); h = bpy.context.active_object
    if h.data.shape_keys: h.shape_key_clear()
    for m in list(h.modifiers): h.modifiers.remove(m)
    W = h.matrix_world.copy(); h.parent = None; h.matrix_world = Matrix.Identity(4)
    namesB = hand_groups(s)
    bm = bmesh.new(); bm.from_mesh(h.data); bm.verts.ensure_lookup_table()
    keep = [(W @ v.co - HB).dot(dB) > -OVER / k and weight_in(h, v, namesB | {f"ForeArm.{s}"}) > 0.5 for v in h.data.vertices]
    # 팔뚝 무게만 있는 점은 손목 근처(겹침 범위)만
    for i, v in enumerate(h.data.vertices):
        if keep[i] and weight_in(h, v, namesB) < 0.2 and (W @ v.co - HB).dot(dB) < -OVER / k: keep[i] = False
    bmesh.ops.delete(bm, geom=[bm.verts[i] for i in range(len(keep)) if not keep[i]], context="VERTS")
    # 피부만: 면 가운데 그림 색이 어두우면(검은 소매 끝) 뺌
    uvl = bm.loops.layers.uv.active; dark = []
    for fc in bm.faces:
        px = skin_px(h, fc.material_index)
        if px is None or uvl is None: continue
        img, w_, h_ = px
        u = sum(l[uvl].uv.x for l in fc.loops) / len(fc.loops); vv = sum(l[uvl].uv.y for l in fc.loops) / len(fc.loops)
        x_ = int((u % 1) * (w_ - 1)); y_ = int((vv % 1) * (h_ - 1)); k4 = (y_ * w_ + x_) * 4
        if 0.3 * img[k4] + 0.59 * img[k4 + 1] + 0.11 * img[k4 + 2] < DARK: dark.append(fc)
    bmesh.ops.delete(bm, geom=dark, context="FACES")
    loose = [v for v in bm.verts if not v.link_faces]; bmesh.ops.delete(bm, geom=loose, context="VERTS")
    print(f"  어두운(소매) 면 뺌 {len(dark)}")
    for v in bm.verts: v.co = T(W @ v.co)
    # 손목 굵기를 A 에 맞춤(소매 구멍이 비어 보이지 않게): 손목 자리 뒤쪽은 다, 손 쪽 --이음 거리까지 점점 약하게
    near = [radial(v.co, HA, dA) for v in bm.verts if -0.006 < (v.co - HA).dot(dA) <= CUT + 0.004]
    rB = sorted(near)[len(near) // 2] if near else None
    if rA and rB and WIDEN:
        f = min(rA / rB * WIDEN, WMAX); print(f"  손목 굵기 A {rA*100:.2f}cm B {rB*100:.2f}cm → {f:.2f}배")
        for v in bm.verts:
            t = (v.co - HA).dot(dA); w = 1.0 if t <= CUT else max(0.0, 1 - (t - CUT) / BLEND)
            if w <= 0: continue
            q = v.co - HA; ax = dA * q.dot(dA); rad = q - ax
            v.co = HA + ax + rad * (1 + (f - 1) * w * w * (3 - 2 * w))
    bm.to_mesh(h.data); bm.free()
    h.data.update(); h.name = f"Hand_B_{s}"
    print(f"  B 에서 가져온 점 {len(h.data.vertices)}")
    h.parent = armA; h.matrix_parent_inverse = armA.matrix_world.inverted()
    md = h.modifiers.new("Armature", "ARMATURE"); md.object = armA
    new_parts.append(h)
    # ── A 손가락 뼈를 새 손가락 자리로
    bpy.ops.object.select_all(action="DESELECT"); armA.select_set(True); bpy.context.view_layer.objects.active = armA
    bpy.ops.object.mode_set(mode="EDIT")
    inv = armA.matrix_world.inverted(); eb = armA.data.edit_bones
    for f in FING:
        hs = [T(head(armB, f"{f}{i}.{s}")) for i in (1, 2, 3)]
        tip = hs[2] + (hs[2] - hs[1]) * 0.8
        pts = hs + [tip]
        for i in range(3):
            b = eb[f"{f}{i + 1}.{s}"]; ln = (b.tail - b.head).length
            b.head = inv @ pts[i]; b.tail = inv @ pts[i + 1]
    bpy.ops.object.mode_set(mode="OBJECT")

# 새 손 피부 그림 색 맞추기
if TINT != [1, 1, 1]:
    for h in new_parts:
        for ms in h.material_slots:
            m = ms.material
            if not m or not m.use_nodes: continue
            m = m.copy(); ms.material = m; nt = m.node_tree
            bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED"); link = bsdf.inputs["Base Color"].links
            if link:
                src = link[0].from_socket; mix = nt.nodes.new("ShaderNodeMix"); mix.data_type = "RGBA"; mix.blend_type = "MULTIPLY"
                mix.inputs["Factor"].default_value = 1.0; mix.inputs["B"].default_value = (*TINT, 1)
                nt.links.new(src, mix.inputs["A"]); nt.links.new(mix.outputs["Result"], bsdf.inputs["Base Color"])
# 새 손 부품만 남기고 B 지우기
for o in newB:
    if o.name in bpy.data.objects: bpy.data.objects.remove(o, do_unlink=True)
bpy.ops.export_scene.gltf(filepath=DST, export_format="GLB", export_morph=True, export_skins=True, export_animations=False, export_image_format="AUTO")
print("저장:", DST)
