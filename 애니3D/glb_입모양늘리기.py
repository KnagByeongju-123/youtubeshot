"""입 모양 키가 셋(MouthOpen·MouthWide·MouthRound)뿐인 GLB 인물에 립싱크용 입 모양 키를 더 만들어 넣음 (사용자 2026-11-26 '립씽크용 입모양 추가', 여자아나운서3)
   새 키 = 있는 세 키를 섞은 모양(이·입속·이빨 부품도 같은 비율로 → 함께 움직임). 이름은 Rocketbox 와 같게 해서
   실사3D/야외_오르빗.py --입방식 15 (모음 5 + 자음 7 + ㅗ·ㅜ 오므림 + 받침 입 닫기)를 그대로 씀
     AA_VI_11_E  에      = 벌림 0.55 + 옆으로 0.55
     AA_VI_13_O  오      = 벌림 0.45 + 둥글게 0.8
     AA_VI_01_PP ㅁㅂㅍ   = 벌림 -0.12 + 둥글게 0.15   (입술을 꼭 붙여 살짝 누름)
     AU_24_LipPressor    = 벌림 -0.10 + 옆으로 0.10
     AA_VI_04_DD ㄷㅌ     = 벌림 0.30 + 옆으로 0.20,  AA_VI_08_nn ㄴ = 벌림 0.25 + 옆으로 0.15,  AA_VI_09_RR ㄹ = 벌림 0.30 + 둥글게 0.15
     AA_VI_07_SS ㅅ      = 벌림 0.12 + 옆으로 0.45 (이 사이),  AA_VI_06_CH ㅈㅊ = 벌림 0.20 + 둥글게 0.45,  AA_VI_05_KK ㄱㅋ = 벌림 0.40
     AU_18_LipPuckerer ㅜ = 둥글게 1.0 + 옆으로 -0.15,  AU_22_LipFunneler = 둥글게 0.7 + 벌림 0.25,  AK_32_MouthFunnel = 둥글게 0.6 + 벌림 0.3
     HB_07_MouthSmile 미소 = 옆으로 0.45 (오므릴 때 음수로 풀림)
   --표 '이름=벌림,옆으로,둥글게;...' 로 바꾸거나 더할 수 있음
   사용: .bpy_venv/bin/python -I 애니3D/glb_입모양늘리기.py <입력.glb> <결과.glb> [--표 ...] [--키빼기 hipoly] [--덮어쓰기]"""
import os, sys
import bpy

a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
src, dst = a[0], a[1]
R = {"AA_VI_11_E": (0.55, 0.55, 0), "AA_VI_13_O": (0.4, 0, 0.8), "AA_VI_01_PP": (-0.12, 0, 0.15), "AU_24_LipPressor": (-0.10, 0.10, 0),
     "AA_VI_04_DD": (0.30, 0.20, 0), "AA_VI_08_nn": (0.25, 0.15, 0), "AA_VI_09_RR": (0.30, 0, 0.15),
     "AA_VI_07_SS": (0.12, 0.45, 0), "AA_VI_06_CH": (0.20, 0, 0.45), "AA_VI_05_KK": (0.40, 0, 0),
     "AU_18_LipPuckerer": (0.0, -0.15, 1.0), "AU_22_LipFunneler": (0.25, 0, 0.7), "AK_32_MouthFunnel": (0.3, 0, 0.6), "HB_07_MouthSmile": (0, 0.45, 0)}
if "--표" in a:
    for kv in a[a.index("--표") + 1].split(";"):
        nm, v = kv.split("="); R[nm.strip()] = tuple(float(x) for x in v.split(","))
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.abspath(src))
BASE = ("MouthOpen", "MouthWide", "MouthRound")
STRIP = [x for x in (a[a.index("--키빼기") + 1].split(",") if "--키빼기" in a else [])]
for o in bpy.data.objects:     # --키빼기 <이름 일부>: 그 부품의 모양 키를 모두 뺌 (얼굴을 지운 몸에 남은 얼굴 키 177개 — 파일만 큼)
    if o.type == "MESH" and o.data.shape_keys and any(t in o.name for t in STRIP):
        o.shape_key_clear(); print(o.name, "모양 키 모두 뺌")
for o in bpy.data.objects:
    if o.type != "MESH" or not o.data.shape_keys: continue
    kb = o.data.shape_keys.key_blocks
    if "AA_VI_11_E" in kb and "--덮어쓰기" not in a: print(o.name, "이미 입 모양 키가 있어 그대로"); continue
    if not any(b in kb for b in BASE): continue
    basis = kb[0]; n = len(o.data.vertices)
    import numpy as np
    B = np.empty(n * 3); basis.data.foreach_get("co", B)
    D = {}
    for b in BASE:
        if b in kb: c = np.empty(n * 3); kb[b].data.foreach_get("co", c); D[b] = c - B
        else: D[b] = np.zeros(n * 3)
    made = []
    for nm, (wo, ww, wr) in R.items():
        k = kb.get(nm) or o.shape_key_add(name=nm, from_mix=False)
        k.slider_min = -1.0; k.value = 0.0          # 새 키는 꺼 둔 채 저장 (켜진 채면 모든 입 모양이 한꺼번에 걸려 입이 크게 벌어졌음)
        co = B + wo * D["MouthOpen"] + ww * D["MouthWide"] + wr * D["MouthRound"]
        if wr > 0 and ("Teeth" in o.name or "Mouth_In" in o.name):   # 입술을 모으는 모양: 이·입속도 가운데로 좁힘 (이가 입꼬리 밖으로 삐져나왔음, 오·우)
            P = co.reshape(-1, 3); cx = B.reshape(-1, 3)[:, 0].mean(); P[:, 0] = cx + (P[:, 0] - cx) * (1 - min(0.3 * wr, 0.55)); co = P.ravel()
        k.data.foreach_set("co", co); made.append(nm)
    print(o.name, "입 모양 키 더함", len(made))
for o in list(bpy.data.objects):
    if o.name.startswith("Icosphere"): bpy.data.objects.remove(o)
bpy.ops.export_scene.gltf(filepath=os.path.abspath(dst), export_format="GLB", export_morph=True, export_skins=True, export_animations=False)
print("저장", dst)
