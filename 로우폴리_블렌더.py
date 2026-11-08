"""로우폴리_장면.py 가 부르는 Blender 쪽 스크립트 (직접 쓸 일은 거의 없음)
로우폴리 자료(JSON: 배경·인물 층의 삼각형과 색) → Blender 장면 + 카메라 움직임 → mp4
  xvfb-run -a blender -b -P 로우폴리_블렌더.py -- <자료.json> <결과.mp4> [초=6] [가로=1920] [세로=1080] [움직임] [앞층거리] [기준점x] [기준점y]
  움직임(사용자 결정 2026-11-08, 영상미): right·left = 옆으로 흐르며 살짝 다가감 / push = 앞층(토마토·인물) 사이 틈으로 곧장 날아 통과(직진 통과)
           orbit = 기준점을 중심으로 빙 돌기 / zoomout = 기준점에 바짝 붙었다가 뒤로 빠지며 전체 / drone = 높은 곳에서 내려다보며 앞으로 날기
  기준점 = 그림 안 비율(0~1): push 는 통과할 틈, orbit·zoomout 은 주인공 가운데
- 인물 층은 배경보다 앞(카메라 쪽)에 세우고, 카메라 시작점에서 그림과 똑같이 겹치게 줄여 둠 → 카메라가 옆으로 움직이며 다가가면 앞뒤가 다른 속도로 움직여 입체로 보임
- 삼각형마다 그림 색 + 아주 약한 면 밝기 차이(깨져 보이지 않게, 사용자 결정 2026-11-08), Workbench 엔진(그래픽카드 없이 빠름)"""
import bpy, json, sys, math, random
a = sys.argv[sys.argv.index("--") + 1:]
data = json.load(open(a[0])); out = a[1]
sec = float(a[2]) if len(a) > 2 else 6; RW = int(a[3]) if len(a) > 3 else 1920; RH = int(a[4]) if len(a) > 4 else 1080
move = a[5] if len(a) > 5 else "right"
FZ = float(a[6]) if len(a) > 6 else (8.0 if move == "push" else 2.6)      # 앞층(인물·토마토)이 배경에서 떨어진 거리. push 는 멀리 띄워야 지나간 뒤 배경이 덜 커짐
PU = float(a[7]) if len(a) > 7 else 0.5; PV = float(a[8]) if len(a) > 8 else 0.5
FPS = 24; W, H = data["W"], data["H"]; SW, SH = 16.0, 9.0; D = 20.0
random.seed(3)
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
cam0 = {"right": (-0.35, 0.0), "left": (0.35, 0.0)}.get(move, (0.0, 0.0))   # 이 자리에서 볼 때 앞층이 그림과 똑같이 겹침
PX, PY = (PU - .5) * SW, -(PV - .5) * SH
for L in data["layers"]:
    fg = L["name"] == "fg"
    zbase = FZ if fg else 0.0
    verts = []
    for x, y in L["pts"]:
        X, Y = (x / W - .5) * SW, -(y / H - .5) * SH
        jit = random.uniform(-.04, .04) if not fg else random.uniform(-.03, .03)
        z = zbase + jit
        if not fg:
            z += max(0.0, (y / H - .62)) * 2.2          # 바닥은 앞으로 (살짝 원근)
        k = (D - z) / D                                  # 앞 레이어는 카메라 시작점 기준으로 줄여서 처음엔 그림과 똑같이 겹침
        verts.append((cam0[0] + (X - cam0[0]) * k, cam0[1] + (Y - cam0[1]) * k, z))
    me = bpy.data.meshes.new(L["name"]); me.from_pydata(verts, [], [tuple(t) for t in L["tris"]]); me.update()
    col = me.color_attributes.new("Col", "FLOAT_COLOR", "CORNER")
    lx, ly, lz = (-0.45, 0.55, 0.70)                    # 왼쪽 위에서 오는 빛: 삼각형마다 조금 밝게·어둡게 (로우폴리 면이 보이게)
    for poly, c in zip(me.polygons, L["cols"]):
        nx, ny, nz = poly.normal
        if nz < 0: nx, ny, nz = -nx, -ny, -nz
        sh_ = 0.95 + 0.09 * max(0.0, nx * lx + ny * ly + nz * lz) ** 3   # 면 밝기 차이를 작게 (깨져 보이지 않게)
        for li in poly.loop_indices:
            col.data[li].color = (min(1, c[0] * sh_) ** 2.2, min(1, c[1] * sh_) ** 2.2, min(1, c[2] * sh_) ** 2.2, 1.0)   # 그림 색(sRGB) → 선형
    me.color_attributes.active_color = col
    ob = bpy.data.objects.new(L["name"], me); sc.collection.objects.link(ob)
cd = bpy.data.cameras.new("cam"); cd.sensor_width = 36; base_lens = 36 * D / (SW * .94)
cam = bpy.data.objects.new("cam", cd); sc.collection.objects.link(cam); sc.camera = cam
n = int(sec * FPS); sc.frame_start, sc.frame_end = 1, n
def key(f, loc, tgt, lens):
    """카메라를 loc 에 두고 tgt 을 바라보게 (기본 방향 = -Z, 위 = +Y). 바라보기 제약은 정면일 때 뒤틀려서 각도를 직접 계산"""
    dx, dy, dz = tgt[0] - loc[0], tgt[1] - loc[1], loc[2] - tgt[2]
    cam.location = loc; cam.rotation_euler = (math.atan2(dy, dz), -math.atan2(dx, math.hypot(dy, dz)), 0); cd.lens = lens
    cam.keyframe_insert("location", frame=f); cam.keyframe_insert("rotation_euler", frame=f); cd.keyframe_insert("lens", frame=f)
if move in ("right", "left"):
    x0 = cam0[0]
    for f, (x, y, z, rz) in ((1, (x0, 0.15, D, -0.6)), (n, (-x0, -0.1, D - 1.6, 0.6))):
        cam.location = (x, y, z); cam.rotation_euler = (0, 0, math.radians(rz)); cd.lens = base_lens
        cam.keyframe_insert("location", frame=f); cam.keyframe_insert("rotation_euler", frame=f)
elif move == "push":                        # 틈(PX,PY)으로 곧장 날아가 앞층을 지나감 — 갈수록 빨라짐
    ze = FZ - 1.2                                         # 앞층을 지난 자리. 화면이 그림 밖으로 나가지 않게 x·y 를 가둠
    hw, hh = (SW * .94 / 2) * ze / D, (SH * .94 / 2) * ze / D
    ex = max(-(SW / 2 - hw), min(SW / 2 - hw, PX)); ey = max(-(SH / 2 - hh), min(SH / 2 - hh, PY))
    key(1, (0, 0, D), (0, 0, 0), base_lens)
    key(n, (ex, ey, ze), (ex, ey, 0), base_lens)
elif move == "orbit":                       # 주인공을 중심으로 좌우로 돌기 (가장자리가 보이지 않게 당겨 찍음)
    r_ = D - FZ * 0.5; steps = 6
    for i in range(steps + 1):
        t = i / steps; ang = math.radians(-9 + 18 * t)
        key(1 + round((n - 1) * t), (PX * .5 + r_ * math.sin(ang) * 0.45, PY * .5 + 0.2 * math.sin(math.pi * t), FZ * 0.5 + r_ * math.cos(ang) - 1.0 * t),
            (PX * .5, PY * .5, FZ * 0.5), base_lens * 1.5)
elif move == "zoomout":                     # 주인공에 바짝 붙었다가 뒤로 빠지며 그림 전체
    key(1, (PX * .85, PY * .85, FZ + (D - FZ) * 0.42), (PX * .85, PY * .85, 0), base_lens)
    key(n, (0, 0, D), (0, 0, 0), base_lens)
else:                                       # drone: 위에서 내려다보며 앞으로 날다 내려옴
    key(1, (0, 1.6, D + 1.0), (0, -1.0, 0), base_lens * 1.45)
    key(n, (0, 0.2, D - 3.5), (0, -0.3, 0), base_lens * 1.45)
for dat in (cam, cd):
    if dat.animation_data and dat.animation_data.action:
        for fc in dat.animation_data.action.fcurves:
            for kp in fc.keyframe_points:
                if move == "push": kp.interpolation = "QUAD"; kp.easing = "EASE_IN"
                else: kp.interpolation = "BEZIER"; kp.easing = "EASE_IN_OUT"
r = sc.render; r.engine = "BLENDER_WORKBENCH"; r.resolution_x, r.resolution_y = RW, RH; r.fps = FPS
sh = sc.display.shading; sh.light = "FLAT"; sh.color_type = "VERTEX"; sh.show_specular_highlight = False
sc.display_settings.display_device = "sRGB"; sc.view_settings.view_transform = "Standard"
sc.world = bpy.data.worlds.new("w")
r.image_settings.file_format = "FFMPEG"; r.ffmpeg.format = "MPEG4"; r.ffmpeg.codec = "H264"; r.ffmpeg.constant_rate_factor = "HIGH"
r.filepath = out
bpy.ops.render.render(animation=True)
print("DONE", out)
