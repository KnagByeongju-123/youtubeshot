"""GLB 인물의 얼굴 모양(정면에서 본 눈 사이·코 너비·턱선·얼굴 길이)을 사진 비율 쪽으로 옮김 (사용자 2026-11-27 'Rocketbox 원래 머리에 사진 얼굴 입히기' — 그림만 바꾸면 얼굴형이 원래 모델 그대로였음)
   - `사진얼굴입히기.py` 가 남긴 shape_lm.npz (모델 표지점 468개 → 사진 비율 목표 자리, 미터)를 씀
   - 얇은 판 휨(TPS)으로 정면 평면(x 좌우, z 위아래)만 옮김 — 앞뒤 깊이는 사진 한 장으로 알 수 없어 그대로
   - 얼굴 앞쪽만(뒤통수·귀·목 아래는 0), 얼굴 둘레 바깥 고리 점은 움직이지 않게 묶어 부드럽게 이어짐
   - 모양 키(입 모양 15가지·표정 52가지)는 같은 만큼 함께 옮김 → 립싱크·눈 깜빡임 그대로
   사용: .bpy_venv/bin/python -I 애니3D/얼굴모양맞추기.py <입력.glb> <shape_lm.npz> <출력.glb> [--세기 1.0] [--최대 0.012] [--앞 0.0,0.06]"""
import sys
import bpy
import numpy as np
from mathutils import Matrix

a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
src, lm_p, dst = a[0], a[1], a[2]
def opt(k, d): return a[a.index(k) + 1] if k in a else d
K = float(opt("--세기", "1.0")); CAP = float(opt("--최대", "0.012"))
Y0, Y1 = (float(v) for v in opt("--앞", "0.0,0.06").split(","))   # y 가 Y0 보다 앞(작음)이면 다 옮기고 Y1 에서 0 (얼굴은 -Y 쪽)
L = np.load(lm_p); S, D, OV = L["src"], L["dst"], L["oval"]
d = (D - S) * K
c0 = OV.mean(0); R = np.linalg.norm(OV - c0, axis=1).max()
ang = np.linspace(0, 2 * np.pi, 40, endpoint=False)
ring = c0 + np.stack([np.cos(ang), np.sin(ang)], 1) * R * 1.35          # 움직이지 않는 고리
C = np.vstack([S, ring]); Dv = np.vstack([d, np.zeros_like(ring)])
def U(r): r = np.maximum(r, 1e-9); return r * r * np.log(r)
n = len(C)
A = np.zeros((n + 3, n + 3)); A[:n, :n] = U(np.linalg.norm(C[:, None] - C[None], axis=2)) + np.eye(n) * 1e-5
A[:n, n] = 1; A[:n, n + 1:] = C; A[n, :n] = 1; A[n + 1:, :n] = C.T
W = np.linalg.solve(A, np.vstack([Dv, np.zeros((3, 2))]))
def field(P):
    out = U(np.linalg.norm(P[:, None] - C[None], axis=2)) @ W[:n] + W[n] + P @ W[n + 1:]
    r = np.linalg.norm(P - c0, axis=1); out *= np.clip((R * 1.5 - r) / (R * 0.3), 0, 1)[:, None]   # 고리 밖은 0 으로
    m = np.linalg.norm(out, axis=1, keepdims=True); return out * np.minimum(1, CAP / (m + 1e-12))
print("표지점 옮김 평균 %.1fmm, 최대 %.1fmm" % (np.linalg.norm(d, axis=1).mean() * 1000, np.linalg.norm(d, axis=1).max() * 1000))

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
for o in [o for o in bpy.data.objects if o.type == "MESH"]:
    me = o.data; mw = np.array(o.matrix_world); inv3 = np.linalg.inv(mw[:3, :3])
    kbs = list(me.shape_keys.key_blocks) if me.shape_keys else []
    co = np.array([v.co for v in me.vertices]); Wd = co @ mw[:3, :3].T + mw[:3, 3]
    wgt = np.clip((Y1 - Wd[:, 1]) / (Y1 - Y0), 0, 1) * np.clip((Wd[:, 2] - (c0[1] - R * 1.6)) / 0.04, 0, 1)
    sel = wgt > 0
    if not sel.any(): continue
    dd = np.zeros((len(co), 3)); f = field(Wd[sel][:, [0, 2]]) * wgt[sel, None]
    dd[sel, 0], dd[sel, 2] = f[:, 0], f[:, 1]
    dl = dd @ inv3.T                                                     # 세상 좌표 → 물체 좌표
    for i, v in enumerate(me.vertices):
        if sel[i]: v.co += type(v.co)(dl[i])
    for kb in kbs:
        arr = np.zeros(len(co) * 3); kb.data.foreach_get("co", arr); arr = arr.reshape(-1, 3) + dl
        kb.data.foreach_set("co", arr.ravel())
    me.update()
    print(o.name, "옮긴 점", int(sel.sum()), "최대 %.1fmm" % (np.linalg.norm(dd, axis=1).max() * 1000))
bpy.ops.export_scene.gltf(filepath=dst, export_format="GLB", export_morph=True, export_skins=True, export_animations=False, export_image_format="AUTO")
print("→", dst)
