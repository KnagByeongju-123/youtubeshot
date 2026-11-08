"""로우폴리_장면.py 가 부르는 Blender 쪽 스크립트 (직접 쓸 일은 거의 없음)
로우폴리 자료(JSON: 배경·인물 층의 삼각형과 색) → Blender 장면 + 카메라 움직임 → mp4
  xvfb-run -a blender -b -P 로우폴리_블렌더.py -- <자료.json> <결과.mp4> [초=6] [가로=1920] [세로=1080] [움직임=right|left]
- 인물 층은 배경보다 앞(카메라 쪽)에 세우고, 카메라 시작점에서 그림과 똑같이 겹치게 줄여 둠 → 카메라가 옆으로 움직이며 다가가면 앞뒤가 다른 속도로 움직여 입체로 보임
- 삼각형마다 그림 색 + 아주 약한 면 밝기 차이(깨져 보이지 않게, 사용자 결정 2026-11-08), Workbench 엔진(그래픽카드 없이 빠름)"""
import bpy, json, sys, math, random
a = sys.argv[sys.argv.index("--") + 1:]
data = json.load(open(a[0])); out = a[1]
sec = float(a[2]) if len(a) > 2 else 6; RW = int(a[3]) if len(a) > 3 else 1920; RH = int(a[4]) if len(a) > 4 else 1080
move = a[5] if len(a) > 5 else "right"
FPS = 24; W, H = data["W"], data["H"]; SW, SH = 16.0, 9.0; D = 20.0
random.seed(3)
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
cam0 = (-0.35 if move == "right" else 0.35, 0.0)
for L in data["layers"]:
    fg = L["name"] == "fg"
    zbase = 2.6 if fg else 0.0
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
cd = bpy.data.cameras.new("cam"); cd.lens = 36 * D / (SW * .94); cd.sensor_width = 36
cam = bpy.data.objects.new("cam", cd); sc.collection.objects.link(cam); sc.camera = cam
n = int(sec * FPS); sc.frame_start, sc.frame_end = 1, n
x1 = -cam0[0]
for f, (x, z, rz) in ((1, (cam0[0], D, -0.6)), (n, (x1, D - 1.6, 0.6))):
    cam.location = (x, 0.15 if f == 1 else -0.1, z); cam.rotation_euler = (0, 0, math.radians(rz)); 
    cam.keyframe_insert("location", frame=f); cam.keyframe_insert("rotation_euler", frame=f)
for fc in cam.animation_data.action.fcurves:
    for kp in fc.keyframe_points:
        kp.interpolation = "BEZIER"; kp.easing = "EASE_IN_OUT"
r = sc.render; r.engine = "BLENDER_WORKBENCH"; r.resolution_x, r.resolution_y = RW, RH; r.fps = FPS
sh = sc.display.shading; sh.light = "FLAT"; sh.color_type = "VERTEX"; sh.show_specular_highlight = False
sc.display_settings.display_device = "sRGB"; sc.view_settings.view_transform = "Standard"
sc.world = bpy.data.worlds.new("w")
r.image_settings.file_format = "FFMPEG"; r.ffmpeg.format = "MPEG4"; r.ffmpeg.codec = "H264"; r.ffmpeg.constant_rate_factor = "HIGH"
r.filepath = out
bpy.ops.render.render(animation=True)
print("DONE", out)
