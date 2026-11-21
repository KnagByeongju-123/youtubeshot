"""3D 아나운서(MPFB2)가 서서 손짓하며 말하는 영상 (블렌더 Cycles, 그래픽카드 없이)
먼저: 인물_만들기.py 로 만든 <인물.blend>, 나레이션 wav(16k), 발음시각.py 결과 json
사용: BLENDER_USER_RESOURCES=$PWD/models/blender_user .bpy_venv/bin/python -I 실사3D/리포터_3D.py \
        <인물.blend> <나레이션.wav> <발음시각.json> <프레임폴더> '{"sec":5,"samples":16}'
  → <폴더>/f0001.png … → ffmpeg -framerate 24 -i <폴더>/f%04d.png -i 나레이션 -t 5 -c:v libx264 -pix_fmt yuv420p -c:a aac 결과.mp4
  옵션: sec(앞부분 초), size "1024x576", samples 16, still(그 장 한 장만), gestures [[시작초, 끝초, "오른손"|"왼손"], ...]
입: 발음 시각대로 모음 → 입 모양(visemes01), 소리 크기 = 벌림, 받침·첫소리 ㅁㅂㅍ = 다문 입, 0.2초 앞당김 (입모양_학습 결과)
손짓(뼈대 rig default, 2026-11-21 시험): 위팔 upperarm01 Z=±32 팔 내림(기본), 아래팔 lowerarm01 X+70 = 손을 가슴 높이로 듦(설명하는 손짓),
  아래팔 Z+60 = 손이 배 앞으로, 아래팔 Y = 손목 돌림
"""
import bpy, sys, json, math, wave, addon_utils, mathutils
import numpy as np
addon_utils.enable('bl_ext.user_default.mpfb', default_set=True)
from bl_ext.user_default.mpfb.services.faceservice import FaceService

blend, wav, timing_path, out = sys.argv[1:5]
opt = json.loads(sys.argv[5]) if len(sys.argv) > 5 else {}
FPS = 24
SEC = float(opt.get("sec", 5))
bpy.ops.wm.open_mainfile(filepath=blend)
sc = bpy.context.scene
body = [o for o in bpy.data.objects if o.name.endswith('.body')][0]
FaceService.load_targets(body, load_microsoft_visemes=True, load_arkit_faceunits=True)
FaceService.interpolate_targets(body)
objs = [o for o in bpy.data.objects if o.type == 'MESH' and o.data.shape_keys]
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
N = int(SEC * FPS)

# --- 소리 크기
w = wave.open(wav); sr = w.getframerate()
a = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
hop = sr // FPS
rms = np.array([np.sqrt(np.mean(a[i * hop:(i + 1) * hop] ** 2) + 1e-12) if i * hop < len(a) else 0 for i in range(N)])
rms = np.convolve(rms, [0.25, 0.5, 0.25], 'same'); peak = np.percentile(rms, 95) + 1e-9

# --- 발음 시각 → 입 모양
VOW = {0: 'aa_02', 2: 'aa_02', 9: 'aa_02', 4: 'aa_ah_ax_01', 6: 'aa_ah_ax_01', 14: 'aa_ah_ax_01', 1: 'ey_eh_uh_04', 3: 'ey_eh_uh_04',
       5: 'ey_eh_uh_04', 7: 'ey_eh_uh_04', 10: 'ey_eh_uh_04', 11: 'ey_eh_uh_04', 15: 'ey_eh_uh_04', 8: 'ow_08', 12: 'ow_08',
       13: 'w_uw_07', 16: 'w_uw_07', 17: 'w_uw_07', 18: 'y_iy_ih_ix_06', 19: 'y_iy_ih_ix_06', 20: 'y_iy_ih_ix_06'}
OPEN = {'aa_02': 1.36, 'aa_ah_ax_01': 0.95, 'ey_eh_uh_04': 1.2, 'ow_08': 0.67, 'w_uw_07': 0.63, 'y_iy_ih_ix_06': 0.9}  # 입모양표(배움)
LAG = -0.2
plan = {}
for ch, s0, e0 in json.load(open(timing_path, encoding='utf-8')):
    v = ord(ch) - 0xAC00; cho, jung, jong = v // 588, (v % 588) // 28, v % 28
    f0, f1 = int((s0 + LAG) * FPS), int(round((e0 + LAG) * FPS))
    fr = [f for f in range(f0, max(f1, f0 + 1)) if 0 <= f < N]
    for k, f in enumerate(fr):
        t = k / max(len(fr), 1)
        if (cho in (6, 7, 8, 17) and t < 0.25) or (jong in (16, 17, 26) and t > (0.15 if jung in (18, 19, 20) else 0.4)):
            plan[f] = ('p_b_m_21', 1.0)
        else:
            plan[f] = (VOW[jung], OPEN[VOW[jung]] * 0.75)
    if jong in (16, 17, 26) and fr and fr[-1] + 1 < N:
        plan[fr[-1] + 1] = ('p_b_m_21', 1.0)
USED = sorted(set(k for k, _ in plan.values()))
for f in range(N):
    key, wt = plan.get(f, (None, 0)); lvl = 1.0 if key == 'p_b_m_21' else min(1.0, rms[f] / peak * 1.2)
    for o in objs:
        kb = o.data.shape_keys.key_blocks
        for k in USED:
            if k in kb:
                kb[k].value = (wt * lvl if k == key else 0.0); kb[k].keyframe_insert('value', frame=f + 1)
# 살짝 웃는 얼굴 + 눈 깜빡임
for o in objs:
    kb = o.data.shape_keys.key_blocks
    for k, v in (('mouthSmileLeft', 0.3), ('mouthSmileRight', 0.3)):
        if k in kb: kb[k].value = v
    for b in ('eyeBlinkLeft', 'eyeBlinkRight'):
        if b in kb:
            for s in np.arange(1.0, SEC, 2.8):
                f0 = int(s * FPS)
                for df, vv in ((0, 0), (2, 1), (4, 0)): kb[b].value = vv; kb[b].keyframe_insert('value', frame=f0 + df)


# --- 손짓·고개·몸
def key_bone(name, f, rot):
    b = rig.pose.bones.get(name)
    if b is None: return
    b.rotation_mode = 'XYZ'; b.rotation_euler = [math.radians(x) for x in rot]; b.keyframe_insert('rotation_euler', frame=f)


REST = {'upperarm01.R': (0, 0, 32), 'upperarm01.L': (0, 0, -32), 'lowerarm01.R': (10, 0, 0), 'lowerarm01.L': (10, 0, 0)}
UP = {'R': {'upperarm01.R': (22, 0, 30), 'lowerarm01.R': (72, -25, 0)}, 'L': {'upperarm01.L': (22, 0, -30), 'lowerarm01.L': (72, 25, 0)}}
for bn, r in REST.items(): key_bone(bn, 1, r)
for g0, g1, side in opt.get('gestures', [[1.3, 3.6, '오른손']]):
    sd = 'R' if side == '오른손' else 'L'
    f0, f1 = int(g0 * FPS) + 1, int(g1 * FPS) + 1
    for bn, r in REST.items():
        if bn.endswith('.' + sd): key_bone(bn, f0, r)
    up = UP[sd]
    key_bone('upperarm01.' + sd, f0 + 10, up['upperarm01.' + sd])
    key_bone('lowerarm01.' + sd, f0 + 10, up['lowerarm01.' + sd])
    for k_, fm in enumerate(range(f0 + 16, f1 - 10, 9)):                 # 말에 맞춰 손을 살짝 흔들어 강조
        dx = 8 if k_ % 2 == 0 else -2
        lo = up['lowerarm01.' + sd]; key_bone('lowerarm01.' + sd, fm, (lo[0] + dx, lo[1], lo[2]))
    key_bone('upperarm01.' + sd, f1 - 10, up['upperarm01.' + sd]); key_bone('lowerarm01.' + sd, f1 - 10, up['lowerarm01.' + sd])
    for bn, r in REST.items():
        if bn.endswith('.' + sd): key_bone(bn, f1 + 4, r)
for f in range(1, N + 1, 4):                                              # 고개 끄덕임·몸 살짝 흔들림
    t = f / FPS
    key_bone('head', f, (1.5 * math.sin(t * 1.9) + 0.8 * math.sin(t * 3.3), 1.0 * math.sin(t * 0.9), 1.2 * math.sin(t * 0.7)))
    key_bone('spine01', f, (0.6 * math.sin(t * 1.3), 0, 0.8 * math.sin(t * 0.6)))

# --- 스튜디오·카메라 (머리~무릎, 천천히 다가감)
for o in list(bpy.data.objects):
    if o.type in ('CAMERA', 'LIGHT'): bpy.data.objects.remove(o)
sc.render.film_transparent = False
wd = sc.world; bg = wd.node_tree.nodes["Background"]; bg.inputs[0].default_value = (0.02, 0.04, 0.09, 1); bg.inputs[1].default_value = 1.0
hb = mathutils.Vector(rig.matrix_world @ rig.pose.bones['head'].head)
bpy.ops.mesh.primitive_plane_add(size=12, location=(0, 2.5, 1.5), rotation=(math.radians(90), 0, 0))
m = bpy.data.materials.new("벽"); m.use_nodes = True; p = m.node_tree.nodes["Principled BSDF"]
p.inputs["Base Color"].default_value = (0.03, 0.08, 0.2, 1); bpy.context.object.data.materials.append(m)
bpy.ops.mesh.primitive_plane_add(size=12, location=(0, 0, 0))
m2 = bpy.data.materials.new("바닥"); m2.use_nodes = True; m2.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.05, 0.06, 0.09, 1)
bpy.context.object.data.materials.append(m2)


def light(nm, loc, en, size, col=(1, 1, 1)):
    L = bpy.data.objects.new(nm, bpy.data.lights.new(nm, "AREA")); L.data.energy = en; L.data.size = size; L.data.color = col; L.location = loc
    L.rotation_euler = (mathutils.Vector((0, 0, hb.z - 0.3)) - L.location).to_track_quat('-Z', 'Y').to_euler(); sc.collection.objects.link(L)


light("key", (-1.5, -2.5, 2.4), 260, 2.0); light("fill", (1.8, -2.2, 1.6), 110, 2.5); light("rim", (0.8, 1.5, 2.2), 160, 1.2, (0.8, 0.9, 1))
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam
cam.data.lens = 50
tgt = mathutils.Vector((0, 0, hb.z * 0.72))
for f, d in ((1, 3.4), (N, 3.0)):
    cam.location = tgt + mathutils.Vector((0.15 * (1 if f == 1 else -1), -d, 0.05)); cam.keyframe_insert('location', frame=f)
cam.rotation_euler = (tgt - (tgt + mathutils.Vector((0, -3.2, 0.05)))).to_track_quat('-Z', 'Y').to_euler()
sc.frame_start, sc.frame_end, sc.render.fps = 1, N, FPS
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = int(opt.get('samples', 16)); sc.cycles.use_denoising = True
rx, ry = map(int, opt.get('size', '1024x576').split('x')); sc.render.resolution_x = rx; sc.render.resolution_y = ry
if opt.get('still'):
    sc.frame_set(int(opt['still'])); sc.render.filepath = out + "/still.png"; bpy.ops.render.render(write_still=True)
else:
    sc.render.filepath = out + "/f"; bpy.ops.render.render(animation=True)
print("DONE", N, USED)
