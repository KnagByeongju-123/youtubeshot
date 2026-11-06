"""비스듬한 방향에서 본 모아보기 그림 (시트 확인용 보조)
xvfb-run -a ../.blender_venv/bin/python 모아보기.py <결과.png> <이름> [이름 ...]  — 왼쪽부터 나란히, 크기는 실제 비율"""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, 블록, 사람, 바다생물
M = {"서진": 사람.서진, "서진_젊은": lambda: 사람.서진(True), "하린": 사람.하린, "정우": 사람.정우, **바다생물.MODELS}
out, names = sys.argv[1], sys.argv[2:]
sc = 블록.new_scene("#f4f4f2", 1600, 900)
x = 0.0; depth = 0.0; lo_all = [1e9] * 3; hi_all = [-1e9] * 3
for n in names:
    m = M[n](); lo, hi = m.bounds(); w = hi[0] - lo[0]
    long_ = (hi[1] - lo[1]) > w * 1.5          # 긴 동물은 옆으로 눕혀 비스듬히 보이게 (머리가 오른쪽)
    if long_:
        w = hi[1] - lo[1]
        root, _ = 블록.build(m, location=(x + w / 2, 0, -lo[2]))
        root.rotation_euler = (0, 0, math.radians(-70))
    else:
        depth = max(depth, hi[1] - lo[1])
        root, _ = 블록.build(m, location=(x - lo[0], -lo[1] - (hi[1] - lo[1]) / 2, -lo[2]))
    
    x += w + max(0.4, w * 0.25)
    for i in range(3):
        lo_all[i] = min(lo_all[i], (x if i == 0 else lo[i])); hi_all[i] = max(hi_all[i], hi[i] - lo[i])
cam = bpy.data.cameras.new("c"); cam.lens = 50; co = bpy.data.objects.new("c", cam); sc.collection.objects.link(co); sc.camera = co
W = x; H = hi_all[2]
d = max(W, depth * 0.9, H * 1.8) * 1.15
co.location = (W / 2 + d * 0.35, -d, H * 0.5 + d * 0.32)
tg = bpy.data.objects.new("t", None); sc.collection.objects.link(tg); tg.location = (W / 2 - W * 0.02, 0, H * 0.42)
c = co.constraints.new("TRACK_TO"); c.target = tg
sc.render.filepath = out
bpy.ops.render.render(write_still=True)
