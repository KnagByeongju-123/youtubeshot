"""손목 접힘 자리 바로잡기 (사용자 2026-11-25 '팔목 접힘이 위치가 안 맞는 것 같음')
   잰 것: 손(Hand)·아래팔(ForeArm) 무게가 손목 관절 6cm 앞(소매)부터 손바닥 2cm 안까지 고르게 섞여 있었음
          (관절 자리에서도 손 0.5) → 손목을 꺾으면 소매 끝부터 손바닥까지 8cm 가 함께 휘어 접히는 곳이 관절과 안 맞음.
   고침: 점마다 (손+아래팔) 무게 합은 그대로 두고, 아래팔 축을 따라 관절에서의 거리 d 로 손 몫을 다시 나눔
         d < 시작 → 아래팔만(소매 끝은 팔에 붙음), 시작~끝 → 부드럽게(smoothstep), d > 끝 → 손만. 손가락 무게는 그대로.
   팔꿈치도(사용자 2026-11-25 '여기가 움푹 패인 듯'): 위팔·아래팔이 관절 앞뒤 7cm(모두 14cm)에 걸쳐 섞여, 팔을 90° 넘게 굽히면 그 넓은 곳이 안쪽으로 꺼짐
         → --관절 팔꿈치 --시작 -0.035 --끝 0.035 로 좁힘
   사용: python 애니3D/glb_손목무게.py <입력.glb> <출력.glb> [--관절 손목|팔꿈치] [--시작 -0.010] [--끝 0.015]   (거리 단위 = GLB 단위)"""
import json, struct, sys
import numpy as np

a = sys.argv[1:]; src, dst = a[0], a[1]
D0 = float(a[a.index("--시작") + 1]) if "--시작" in a else -0.010
D1 = float(a[a.index("--끝") + 1]) if "--끝" in a else 0.015
raw = open(src, "rb").read()
jl = struct.unpack("<I", raw[12:16])[0]; g = json.loads(raw[20:20 + jl])
bo = 20 + jl; bl = struct.unpack("<I", raw[bo:bo + 4])[0]; binb = bytearray(raw[bo + 8:bo + 8 + bl])
CT = {5121: np.uint8, 5123: np.uint16, 5126: np.float32}; NC = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}
def view(ai):
    acc = g["accessors"][ai]; bv = g["bufferViews"][acc["bufferView"]]; dt = np.dtype(CT[acc["componentType"]]); n = NC[acc["type"]]
    off = bv.get("byteOffset", 0) + acc.get("byteOffset", 0); st = bv.get("byteStride", dt.itemsize * n)
    arr = np.ndarray((acc["count"], n), dt, buffer=binb, offset=off, strides=(st, dt.itemsize))
    return arr
skin = g["skins"][0]; joints = skin["joints"]; name = {k: g["nodes"][j]["name"] for k, j in enumerate(joints)}
ibm = view(skin["inverseBindMatrices"]).reshape(-1, 4, 4).transpose(0, 2, 1)       # 열 우선 → 행렬
pos = {name[k]: np.linalg.inv(ibm[k].astype(np.float64))[:3, 3] for k in name}    # 뼈 머리 자리(묶을 때 자세)
idx = {v: k for k, v in name.items()}
node_skin_meshes = [n["mesh"] for n in g["nodes"] if n.get("skin") == 0 and "mesh" in n]
body = max(node_skin_meshes, key=lambda m: sum(g["accessors"][p["attributes"]["POSITION"]]["count"] for p in g["meshes"][m]["primitives"]))
sm = lambda u: np.where(u <= 0, 0.0, np.where(u >= 1, 1.0, u * u * (3 - 2 * u)))
CH, PA = ("ForeArm", "UpperArm") if "--관절" in a and a[a.index("--관절") + 1] == "팔꿈치" else ("Hand", "ForeArm")
for sd in ("L", "R"):
    jh, jf = idx[f"{CH}.{sd}"], idx[f"{PA}.{sd}"]
    h, f = pos[f"{CH}.{sd}"], pos[f"{PA}.{sd}"]; ax = (h - f) / np.linalg.norm(h - f)
    tot = 0
    for p in g["meshes"][body]["primitives"]:
        P = view(p["attributes"]["POSITION"]).astype(np.float64); J = view(p["attributes"]["JOINTS_0"]); Wv = view(p["attributes"]["WEIGHTS_0"])
        norm = Wv.dtype == np.uint8; Wf = Wv.astype(np.float64) / (255.0 if norm else 1.0)
        has = ((J == jh) & (Wf > 0)).any(1) | ((J == jf) & (Wf > 0)).any(1)
        for i in np.where(has)[0]:
            w = {}
            for s in range(4):
                if Wf[i, s] > 0: w[int(J[i, s])] = w.get(int(J[i, s]), 0) + Wf[i, s]
            sm_ = w.get(jh, 0) + w.get(jf, 0)
            d = (P[i] - h) @ ax; share = float(sm((d - D0) / (D1 - D0)))
            w[jh] = sm_ * share; w[jf] = sm_ * (1 - share)
            top = sorted(((v, k) for k, v in w.items() if v > 1e-4), reverse=True)[:4]
            s_ = sum(v for v, _ in top); top = [(v / s_, k) for v, k in top] + [(0.0, 0)] * (4 - len(top))
            if norm:
                q = [int(round(v * 255)) for v, _ in top]; q[0] += 255 - sum(q)
                Wv[i] = q
            else:
                Wv[i] = [v for v, _ in top]
            J[i] = [k for _, k in top]; tot += 1
    print(f"{sd} {CH}: 관절 {h.round(3)} 기준 점 {tot}개 다시 나눔 (아래팔만 d<{D0}, 손만 d>{D1})")
out = struct.pack("<4sII", b"glTF", 2, len(raw)) + raw[12:bo] + struct.pack("<I4s", bl, b"BIN\0") + bytes(binb)
open(dst, "wb").write(out)
print("→", dst)
