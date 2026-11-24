"""GLB 사람 모델: 리깅으로 생긴 열린 틈(구멍) 막기
   glb_다시리깅.py 는 두 다리·손가락끼리 붙은 삼각형을 없애 따로 움직이게 하는데, 그 자리가 열린 틈으로 남아
   안쪽(뒷면)이 검은 줄처럼 보임 (여자 아나운서 왼발 안쪽 '갈라짐', 2026-11-23 걷기 오르빗 첫 장면에서 사용자 지적)
   → 열린 모서리를 이어 고리를 찾고, 고리마다 그 고리의 점들로 삼각형을 채워 막음 (새 점을 만들지 않아
     무게·모양 키·겉면 그림 좌표는 둘레 점 것을 그대로 씀 → 막은 면도 그쪽 다리·손가락을 따라 움직임)
   사용: python 애니3D/glb_구멍막기.py <입력.glb> <결과.glb> [--높이 -0.25] [--손]
     --높이: 이 높이(모델 좌표 y)보다 아래 틈만 (기본 -0.25 = 다리·발. 입 안 주머니 같은 일부러 연 곳은 건드리지 않음)
     --손: 손가락 사이 틈도 막음"""
import json, struct, sys
from collections import Counter, defaultdict
import numpy as np

a = sys.argv[1:]
YMAX = -0.25; HAND = False; INNER = 0.012; SLAB = 0.012; MAIN_CHANGED = [False]
if "--높이" in a: i = a.index("--높이"); YMAX = float(a[i + 1]); del a[i:i + 2]
if "--손" in a: a.remove("--손"); HAND = True
if "--안쪽" in a: i = a.index("--안쪽"); INNER = float(a[i + 1]); del a[i:i + 2]
src, dst = a
raw = open(src, "rb").read(); n = struct.unpack("<I", raw[12:16])[0]; j = json.loads(raw[20:20 + n]); b0 = 20 + n + 8
bl = struct.unpack("<I", raw[20 + n:24 + n])[0]; BIN = raw[b0:b0 + bl]
views = [BIN[v.get("byteOffset", 0):v.get("byteOffset", 0) + v["byteLength"]] for v in j["bufferViews"]]
COMP = {5126: np.float32, 5125: np.uint32, 5123: np.uint16, 5121: np.uint8}; K = {"VEC2": 2, "VEC3": 3, "VEC4": 4, "SCALAR": 1}


def get(i):
    ac = j["accessors"][i]; dt = np.dtype(COMP[ac["componentType"]])
    return np.frombuffer(views[ac["bufferView"]], dt, ac["count"] * K[ac["type"]], ac.get("byteOffset", 0)).reshape(-1, K[ac["type"]])


pr = j["meshes"][0]["primitives"][0]; iac = j["accessors"][pr["indices"]]
P = get(pr["attributes"]["POSITION"]).astype(float); I = get(pr["indices"]).reshape(-1, 3).astype(np.int64).copy()
_, g = np.unique(np.round(P * 2e4).astype(np.int64), axis=0, return_inverse=True); g = g.reshape(-1)
rep = {}                                                     # 같은 자리 점 묶음 → 대표 점 번호 (틈 둘레 삼각형이 쓰는 점)
G = g[I]; ok = (G[:, 0] != G[:, 1]) & (G[:, 1] != G[:, 2]) & (G[:, 0] != G[:, 2])
cnt = Counter(); dire = {}
for t in np.where(ok)[0]:
    for k in range(3):
        x, y = G[t, k], G[t, (k + 1) % 3]; cnt[(min(x, y), max(x, y))] += 1; dire[(x, y)] = (I[t, k], I[t, (k + 1) % 3])
nxt = defaultdict(list)
for (x, y), c in cnt.items():
    if c != 1: continue
    if (x, y) in dire: u, v = x, y
    else: u, v = y, x
    ru, rv = dire[(u, v)]; rep.setdefault(u, ru); rep.setdefault(v, rv)
    nxt[v].append(u)                                         # 막는 면은 둘레 삼각형과 반대 방향으로 돌아야 겉면이 바깥을 향함
pos = np.zeros((g.max() + 1, 3)); pos[g] = P
# 손 자리 (손 뼈 위치 둘레)
hand_c = []
if HAND:
    sk = j["skins"][0]; names = [j["nodes"][q]["name"] for q in sk["joints"]]
    ibm = get(sk["inverseBindMatrices"]).reshape(-1, 4, 4).astype(float) if False else np.frombuffer(views[j["accessors"][sk["inverseBindMatrices"]]["bufferView"]], np.float32, len(names) * 16, j["accessors"][sk["inverseBindMatrices"]].get("byteOffset", 0)).reshape(-1, 4, 4).astype(float)
    hand_c = [np.linalg.inv(m.T)[:3, 3] for nm, m in zip(names, ibm) if nm.startswith("Hand")]
used = set(); new = []; n_loop = 0; skipped = 0; FLAT = {}
for s in list(nxt):
    if s in used or not nxt[s]: continue
    loop = [s]; cur = s; ok_ = True
    while True:
        cand = [c for c in nxt[cur] if c not in used and c not in loop[1:]]
        if not cand: ok_ = False; break
        cur = cand[0]
        if cur == s: break
        loop.append(cur)
        if len(loop) > 400: ok_ = False; break
    if not ok_ or len(loop) < 3: skipped += 1; continue
    used.update(loop)
    c = pos[loop].mean(0)
    want = c[1] < YMAX or any(np.linalg.norm(c - h) < 0.15 for h in hand_c)
    if not want: continue
    # 지퍼 잇기: 다리·손가락 사이 틈은 길쭉한 고리 → 고리의 긴 방향(주성분)으로 양 끝을 찾아 두 줄로 나누고,
    #   두 줄을 그 방향 순서대로 번갈아 이어 삼각형 띠를 만듦 (귀 자르기는 꼬인 고리에서 부채꼴 술처럼 삐져나왔음)
    L = [rep[v] for v in loop]; Q = pos[loop]; m_ = len(L)
    nrm = np.zeros(3)
    for k in range(m_): nrm += np.cross(Q[k] - c, Q[(k + 1) % m_] - c)
    # 다리 안쪽 틈(고리가 옆(x)을 봄): 잘린 가장자리 점들이 x 로 들쭉날쭉해 막은 면이 지느러미처럼 삐져나옴 → 고리 점들을 한 평면(x = 가운데값)에 맞춤
    if c[1] < YMAX and abs(nrm[0]) > 0.7 * np.linalg.norm(nrm):
        xm = float(np.median(Q[:, 0]))
        for gv in loop: FLAT[gv] = xm
        Q = Q.copy(); Q[:, 0] = xm
    w_, V_ = np.linalg.eigh(np.cov((Q - c).T)); ax = V_[:, -1]
    tpos = (Q - c) @ ax; i_lo, i_hi = int(np.argmin(tpos)), int(np.argmax(tpos))
    chainA = [(i_lo + k) % m_ for k in range((i_hi - i_lo) % m_ + 1)]            # lo → hi (고리 방향)
    chainB = [(i_lo - k) % m_ for k in range((i_lo - i_hi) % m_ + 1)]            # lo → hi (반대 방향)
    a_, b_ = 0, 0; tris = []
    while a_ < len(chainA) - 1 or b_ < len(chainB) - 1:
        if b_ >= len(chainB) - 1 or (a_ < len(chainA) - 1 and tpos[chainA[a_ + 1]] <= tpos[chainB[b_ + 1]]):
            tris.append((chainA[a_], chainA[a_ + 1], chainB[b_])); a_ += 1
        else:
            tris.append((chainA[a_], chainB[b_ + 1], chainB[b_])); b_ += 1
    for t3 in tris:
        if len(set(t3)) < 3: continue
        q0, q1, q2 = Q[list(t3)]
        tri = (L[t3[0]], L[t3[1]], L[t3[2]])
        if np.cross(q1 - q0, q2 - q0) @ nrm < 0: tri = (tri[0], tri[2], tri[1])   # 고리 방향과 같은 쪽을 보게
        new.append(tri)
    n_loop += 1
print(f"틈 고리 {n_loop}개 막음 (삼각형 {len(new)}개 추가){', 못 이은 고리 ' + str(skipped) + '개' if skipped else ''}")
# 두 구두가 붙어 있던 가운데 덩어리(x≈0, 폭 2cm): 리깅에서 한쪽 발(오른발)에 통째로 붙어, 걸을 때 그 구두 옆에 검은 판(버)처럼 따라다님
#   (2026-11-24 사용자 지적 '걸을 때 오른쪽 구두에 버') → 발 높이에서 가운데를 넘어온 점을 그 발 안쪽 면(x = ±SLAB)으로 납작하게 눌러 붙임
SQ = {}
try:
    sk_ = j["skins"][0]; nm_ = [j["nodes"][q]["name"] for q in sk_["joints"]]
    Jt_ = get(pr["attributes"]["JOINTS_0"]).astype(np.int64); Wt_ = get(pr["attributes"]["WEIGHTS_0"]).astype(float)
    domn = np.array([nm_[k] for k in Jt_[np.arange(len(Jt_)), Wt_.argmax(1)]])
    lowf = P[:, 1] < P[:, 1].min() + 0.095 * (P[:, 1].max() - P[:, 1].min())        # 발목 아래 (키의 9.5%)
    for suf, sgn in ((".R", -1), (".L", 1)):
        side = np.char.endswith(domn, suf) & lowf
        if side.sum() < 50 or np.median(P[side, 0]) * sgn <= 0: continue
        m = side & (P[:, 0] * sgn < SLAB)
        for v in np.where(m)[0]: SQ[v] = sgn * SLAB
    if SQ: print(f"  구두 사이 가운데 덩어리 점 {len(SQ)}개를 각 구두 안쪽 면으로 눌러 붙임 (버 없애기)")
except KeyError:
    pass
if FLAT or SQ:
    pac = j["accessors"][pr["attributes"]["POSITION"]]; P2 = P.astype(np.float32).copy()
    for gv, xm in FLAT.items(): P2[g == gv, 0] = xm
    for v, xv in SQ.items(): P2[v, 0] = xv
    pb_ = P2.reshape(-1).tobytes(); vi_ = pac["bufferView"]; o_ = pac.get("byteOffset", 0)
    assert j["bufferViews"][vi_].get("byteStride") in (None, 12)
    bb = bytearray(views[vi_]); bb[o_:o_ + len(pb_)] = pb_; views[vi_] = bytes(bb)
    pac["min"] = [float(v) for v in P2.min(0)]; pac["max"] = [float(v) for v in P2.max(0)]
    if FLAT: print(f"  다리 안쪽 잘린 가장자리 점 {sum(int((g == gv).sum()) for gv in FLAT)}개를 평평하게")
# 막은 면은 둘레 점의 겉면 그림 좌표를 그대로 쓰면 살색·구두색이 섞여 엉뚱한 띠가 보임(걷기에서 뒷발 안쪽 살색 판)
#   → 막은 삼각형마다 세 점의 그림 색을 재서 같은 색끼리 묶고, 묶음마다 그 색 한 가지(그림 없는 재질)로 칠한 따로 된 조각으로 넣음
import io
from PIL import Image
mat0 = j["materials"][pr["material"]]; img = j["images"][j["textures"][mat0["pbrMetallicRoughness"]["baseColorTexture"]["index"]]["source"]]
TEX = np.asarray(Image.open(io.BytesIO(views[img["bufferView"]])).convert("RGB")).astype(float); th, tw = TEX.shape[:2]
UV = get(pr["attributes"]["TEXCOORD_0"]).astype(float)
N_ = np.array(new, np.int64).reshape(-1, 3)
if len(N_):
    cols = TEX[np.clip((UV[N_, 1] * th).astype(int), 0, th - 1), np.clip((UV[N_, 0] * tw).astype(int), 0, tw - 1)]   # (n,3,3)
    lum = cols.mean(2); dark = lum.min(1) < 70                      # 한 점이라도 어두우면(구두·옷) 어두운 묶음
    # 발: 구두 윗선 높이로 나눔 (점 색으로 나누면 구두 옆이 살색 판, 발목이 검은 양말처럼 보였음)
    vl = TEX[np.clip((UV[:, 1] * th).astype(int), 0, th - 1), np.clip((UV[:, 0] * tw).astype(int), 0, tw - 1)].mean(1)
    feet = (P[:, 1] < P[:, 1].min() + 0.25 * (P[:, 1].max() - P[:, 1].min()))
    if (feet & (vl < 70)).sum() > 50:
        shoe_top = float(np.percentile(P[feet & (vl < 70), 1], 90))
        cy = P[N_].mean(1)[:, 1]; low = cy < P[:, 1].min() + 0.25 * (P[:, 1].max() - P[:, 1].min())
        dark = np.where(low, cy < shoe_top, dark)
        print(f"  구두 윗선 높이 {shoe_top:.3f}")
        # 두 구두가 붙어 있던 안쪽 면(가운데 x≈0 둘레)은 겉면 그림이 살색이라 걸으면 구두 옆에 살색 판이 보임 → 구두색 묶음으로 옮김
        cen0 = P[I].mean(1); tl = TEX[np.clip((UV[I, 1] * th).astype(int), 0, th - 1), np.clip((UV[I, 0] * tw).astype(int), 0, tw - 1)].mean(2).mean(1)
        inner = (I[:, 0] != I[:, 1]) & (cen0[:, 1] < shoe_top) & (np.abs(cen0[:, 0]) < INNER) & (tl >= 70)
        if inner.any():
            N_ = np.concatenate([N_, I[inner]]); cols = np.concatenate([cols, np.zeros((inner.sum(), 3, 3))]); dark = np.concatenate([dark, np.ones(inner.sum(), bool)])
            I[inner] = I[inner][:, :1]; MAIN_CHANGED[0] = True
            print(f"  구두 안쪽 살색 면 {int(inner.sum())}개를 구두색으로")
    groups = {"어두움": N_[dark], "밝음": N_[~dark]}
    for nm_, T_ in groups.items():
        if not len(T_): continue
        cc = cols[dark] if nm_ == "어두움" else cols[~dark]
        cc = cc.reshape(-1, 3); cc = cc[(cc.mean(1) < 70) & (cc.mean(1) > 1)] if nm_ == "어두움" else cc[(cc.mean(1) >= 70)]
        rgb = np.median(cc, 0) / 255.0 if len(cc) else np.array([0.5, 0.5, 0.5])
        lin = [float(((c + 0.055) / 1.055) ** 2.4 if c > 0.04045 else c / 12.92) for c in rgb]
        j["materials"].append({"name": f"틈막음_{nm_}", "pbrMetallicRoughness": {"baseColorFactor": lin + [1.0], "metallicFactor": 0.0,
                                                                                    "roughnessFactor": 0.35 if nm_ == "어두움" else 0.7}})
        b_ = T_.reshape(-1).astype(np.uint32).tobytes(); views.append(b_); j["bufferViews"].append({"buffer": 0, "byteLength": len(b_), "target": 34963})
        j["accessors"].append({"bufferView": len(j["bufferViews"]) - 1, "componentType": 5125, "count": len(T_) * 3, "type": "SCALAR"})
        np_ = {k: v for k, v in pr.items() if k not in ("indices", "material")}; np_["indices"] = len(j["accessors"]) - 1; np_["material"] = len(j["materials"]) - 1
        j["meshes"][0]["primitives"].append(np_)
        print(f"  막은 면 {nm_}: {len(T_)}개, 색 {(rgb * 255).astype(int)}")
if MAIN_CHANGED[0]:
    dt_ = np.dtype(COMP[iac["componentType"]]); nb_ = I.reshape(-1).astype(dt_).tobytes(); vi_ = iac["bufferView"]; o_ = iac.get("byteOffset", 0)
    bb = bytearray(views[vi_]); bb[o_:o_ + len(nb_)] = nb_; views[vi_] = bytes(bb)
out = bytearray()
for i, v in enumerate(j["bufferViews"]):
    while len(out) % 4: out += b"\0"
    v["byteOffset"] = len(out); v["byteLength"] = len(views[i]); out += views[i]
while len(out) % 4: out += b"\0"
j["buffers"][0]["byteLength"] = len(out)
js = json.dumps(j, ensure_ascii=False, separators=(",", ":")).encode()
while len(js) % 4: js += b" "
open(dst, "wb").write(struct.pack("<III", 0x46546C67, 2, 28 + len(js) + len(out)) + struct.pack("<II", len(js), 0x4E4F534A) + js
                      + struct.pack("<II", len(out), 0x004E4942) + bytes(out))
print("→", dst)
