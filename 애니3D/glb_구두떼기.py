"""GLB 사람 모델에서 구두를 '따로 된 물체'로 만들어 내기 (왼·오른 한 켤레)
   AI 로 만든 몸은 두 구두가 붙은 채 만들어져, 리깅으로 떼어 내면 구두 안쪽이 평평한 판으로 남음 (2026-11-24 사용자: '구두부터 정리')
   → 발마다 구두 껍데기(발목 아래 + 겉면 그림이 어두운 곳)의 바깥쪽 반을 골라 그 발 가운데 면에 거울처럼 뒤집어 붙여
     안쪽까지 둥근 완전한 구두 한 짝을 만듦. 몸과 따로 된 물체라 각 발 뼈(Foot.L/R)에 붙이고, 다른 구두로 갈아 끼울 수도 있음
   결과: <폴더>/구두.npz (점·삼각형·겉면 그림 좌표, 모델 좌표 = GLB 그대로) + <폴더>/구두_그림.png
   사용: python 애니3D/glb_구두떼기.py <몸.glb> <결과 폴더> [--높이 0.075] [--키움 1.035] [--확인 <그림.png>]
     --몸 <결과.glb>: 몸에서 구두 높이 아래 발을 모두 빼서 저장 — 새 구두 안에서 겹쳐 삐져나오지 않게. 구두 입구는 살색 '발등 면'으로 막음
     --폭 1.15: 구두 폭만 더 넓힘(가운데 기준)
     --높이: 구두로 볼 높이(키에 대한 비율, 바닥부터). --키움: 원래 몸 구두를 덮도록 살짝 크게
   붙이기: 실사3D/야외_오르빗.py ... --구두 <결과 폴더>"""
import io, json, os, struct, sys
import numpy as np
from PIL import Image

a = sys.argv[1:]
HR, GROW, check, BODY = 0.075, 1.035, None, None
if "--몸" in a: i = a.index("--몸"); BODY = a[i + 1]; del a[i:i + 2]
if "--높이" in a: i = a.index("--높이"); HR = float(a[i + 1]); del a[i:i + 2]
WID = 1.0
if "--폭" in a: i = a.index("--폭"); WID = float(a[i + 1]); del a[i:i + 2]
if "--키움" in a: i = a.index("--키움"); GROW = float(a[i + 1]); del a[i:i + 2]
if "--확인" in a: i = a.index("--확인"); check = a[i + 1]; del a[i:i + 2]
src, out_dir = a
raw = open(src, "rb").read(); n = struct.unpack("<I", raw[12:16])[0]; j = json.loads(raw[20:20 + n]); b0 = 20 + n + 8
BIN = raw[b0:b0 + struct.unpack("<I", raw[20 + n:24 + n])[0]]
views = [BIN[v.get("byteOffset", 0):v.get("byteOffset", 0) + v["byteLength"]] for v in j["bufferViews"]]
COMP = {5126: np.float32, 5125: np.uint32, 5123: np.uint16, 5121: np.uint8}; K = {"VEC2": 2, "VEC3": 3, "VEC4": 4, "SCALAR": 1}


def get(i):
    ac = j["accessors"][i]; dt = np.dtype(COMP[ac["componentType"]])
    return np.frombuffer(views[ac["bufferView"]], dt, ac["count"] * K[ac["type"]], ac.get("byteOffset", 0)).reshape(-1, K[ac["type"]])


pr = j["meshes"][0]["primitives"][0]
P = get(pr["attributes"]["POSITION"]).astype(float); UV = get(pr["attributes"]["TEXCOORD_0"]).astype(float)
I = get(pr["indices"]).reshape(-1, 3).astype(np.int64)
mat = j["materials"][pr["material"]]; img = j["images"][j["textures"][mat["pbrMetallicRoughness"]["baseColorTexture"]["index"]]["source"]]
TEXIMG = Image.open(io.BytesIO(views[img["bufferView"]])).convert("RGB"); TEX = np.asarray(TEXIMG).astype(float); th, tw = TEX.shape[:2]
ok = (I[:, 0] != I[:, 1]) & (I[:, 1] != I[:, 2])
ymin, ymax = P[:, 1].min(), P[:, 1].max(); ytop = ymin + HR * (ymax - ymin)
cen = P[I].mean(1)
lum = TEX[np.clip((UV[I, 1] * th).astype(int), 0, th - 1), np.clip((UV[I, 0] * tw).astype(int), 0, tw - 1)].mean(2)   # (n,3)
shell = ok & (P[I][:, :, 1].max(1) < ytop) & (lum.max(1) < 90)          # 세 점 모두 구두 높이 아래 + 모두 어두움(구두)
outP, outUV, outI, side_ = [], [], [], []; capS = []
base = 0
for sd, sgn in (("L", 1), ("R", -1)):
    m = shell & (cen[:, 0] * sgn > 0.004)
    if m.sum() < 50: print(f"{sd}: 구두 삼각형이 너무 적음"); continue
    xs = P[I[m]].reshape(-1, 3)[:, 0] * sgn
    outer, inner = np.percentile(xs, 99.5), np.percentile(xs, 0.5)
    xc = (outer + inner) / 2                                             # 이 발 구두의 가운데 면 (x = sgn*xc)
    keep = m & (cen[:, 0] * sgn >= xc)                                    # 바깥쪽 반
    T = I[keep]; vid, inv = np.unique(T, return_inverse=True); T2 = inv.reshape(-1, 3)
    Q = P[vid].copy(); U = UV[vid].copy()
    q = Q[:, 0] * sgn; q = np.maximum(q, xc); Q[:, 0] = q * sgn              # 가운데를 넘은 점은 가운데 면에 맞춤
    Qm = Q.copy(); Qm[:, 0] = (2 * xc - Q[:, 0] * sgn) * sgn                  # 거울: 안쪽 반
    Pall = np.concatenate([Q, Qm]); Uall = np.concatenate([U, U])
    Tall = np.concatenate([T2, T2[:, ::-1] + len(Q)])                    # 거울 쪽은 삼각형 방향을 뒤집어 겉면이 바깥을 보게
    # 원래 몸 구두를 덮도록 구두 가운데 기준으로 살짝 키움 (바닥 높이는 그대로)
    c0 = np.array([xc * sgn, ymin, Pall[:, 2].mean()])
    Pall = c0 + (Pall - c0) * GROW
    Pall[:, 0] = c0[0] + (Pall[:, 0] - c0[0]) * WID                       # 폭만 더 넓힘 (발 안쪽이 구두 밖으로 나오지 않게)
    # 발등 면: 구두 입구(가장 긴 열린 고리)를 살색으로 막음 — 고리 점들 평균 높이보다 살짝 아래로 오목하게
    from collections import Counter, defaultdict
    key = np.round(Pall * 2e4).astype(np.int64); _, gg = np.unique(key, axis=0, return_inverse=True); gg = gg.reshape(-1)
    cnt = Counter(); dirE = {}
    for t in Tall:
        for k in range(3):
            x_, y_ = gg[t[k]], gg[t[(k + 1) % 3]]; cnt[(min(x_, y_), max(x_, y_))] += 1; dirE[(x_, y_)] = (t[k], t[(k + 1) % 3])
    nxt = defaultdict(list); rep = {}
    for (x_, y_), c in cnt.items():
        if c != 1: continue
        u, v = (x_, y_) if (x_, y_) in dirE else (y_, x_); ru, rv = dirE[(u, v)]; rep[u] = ru; rep[v] = rv; nxt[v].append(u)
    loops = []; used = set()
    for s0 in list(nxt):
        if s0 in used: continue
        lp = [s0]; cur = s0
        while True:
            cand = [c_ for c_ in nxt[cur] if c_ not in used and c_ not in lp[1:]]
            if not cand: break
            cur = cand[0]
            if cur == s0: break
            lp.append(cur)
        used.update(lp)
        if len(lp) > 8: loops.append(lp)
    capP, capT = [], []
    if loops:
        lp = max(loops, key=len); ids = [rep[v] for v in lp]; R_ = Pall[ids]; cc = R_.mean(0)
        top_ = R_[:, 1].mean(); cen_ = np.array([cc[0], min(top_, cc[1]) - 0.012, cc[2]])   # 가운데는 입구보다 1.2cm 아래 (발등이 들어간 모양)
        capP = [cen_]; m_ = len(ids)
        for k in range(m_): capT.append((0, k + 1, (k + 1) % m_ + 1))
        capP = np.concatenate([np.array(capP), R_]); capT = np.array(capT)
        nr = np.cross(capP[capT[:, 1]] - capP[capT[:, 0]], capP[capT[:, 2]] - capP[capT[:, 0]]).sum(0)
        if nr[1] < 0: capT = capT[:, ::-1]                                    # 위를 보게
        print(f"   {sd} 발등 면: 입구 고리 점 {m_}개")
    outP.append(Pall); outUV.append(Uall); outI.append(Tall + base); side_.append(np.full(len(Pall), 0 if sd == "L" else 1)); base += len(Pall)
    if len(capT):
        capS.append((np.array(capP), capT, 0 if sd == "L" else 1))
    print(f"{sd} 구두: 바깥쪽 반 삼각형 {len(T2)}개 → 한 짝 {len(Tall)}개, 가운데 x={xc * sgn:+.3f}, 폭 {(outer - inner) * GROW * WID:.3f}")
os.makedirs(out_dir, exist_ok=True)
np.savez(os.path.join(out_dir, "구두.npz"), P=np.concatenate(outP).astype(np.float32), UV=np.concatenate(outUV).astype(np.float32),
         I=np.concatenate(outI).astype(np.int32), side=np.concatenate(side_).astype(np.int8),
         capP=np.concatenate([c[0] for c in capS]).astype(np.float32) if capS else np.zeros((0, 3), np.float32),
         capI=np.concatenate([c[1] + sum(len(q[0]) for q in capS[:k]) for k, c in enumerate(capS)]).astype(np.int32) if capS else np.zeros((0, 3), np.int32),
         capSide=np.concatenate([np.full(len(c[0]), c[2]) for c in capS]).astype(np.int8) if capS else np.zeros(0, np.int8),
         skin=np.median(TEX[(TEX.mean(2) > 150)], 0).astype(np.float32) / 255)
TEXIMG.save(os.path.join(out_dir, "구두_그림.png"))
print("→", out_dir)
if check:      # 위·옆에서 본 점 그림
    from PIL import ImageDraw
    Pa = np.concatenate(outP); im = Image.new("RGB", (900, 450), "white"); d = ImageDraw.Draw(im)
    for k_, (ax0, ax1) in enumerate(((0, 2), (2, 1))):
        X = Pa[:, ax0]; Y = Pa[:, ax1]; sx = 400 / (X.max() - X.min() + 1e-9); sy = 400 / (Y.max() - Y.min() + 1e-9); s_ = min(sx, sy)
        for x_, y_ in zip(X[::3], Y[::3]): d.point((25 + 450 * k_ + (x_ - X.min()) * s_, 425 - (y_ - Y.min()) * s_), fill="black")
    im.save(check); print("확인 그림:", check)

if BODY:
    # 몸에서 원래 구두 빼기: ① 본래 조각: 구두 껍데기(shell) + 구두 높이 아래 x≈0 안쪽 벽  ② 틈 막은 조각(틈막음_*): 구두 높이 아래 전부
    n_rm = 0
    for pi, prm in enumerate(j["meshes"][0]["primitives"]):
        iac = j["accessors"][prm["indices"]]; Ii = get(prm["indices"]).reshape(-1, 3).astype(np.int64).copy()
        below = P[Ii][:, :, 1].max(1) < ytop
        mname = j["materials"][prm["material"]].get("name", "") if "material" in prm else ""
        rm = below.copy()                                                  # 구두 높이 아래 발은 모두 뺌 (새 구두 + 발등 면이 대신함)
        rm &= Ii[:, 0] != Ii[:, 1]
        Ii[rm] = Ii[rm][:, :1]; n_rm += int(rm.sum())
        dt = np.dtype(COMP[iac["componentType"]]); nb = Ii.reshape(-1).astype(dt).tobytes(); vi = iac["bufferView"]; o_ = iac.get("byteOffset", 0)
        bb = bytearray(views[vi]); bb[o_:o_ + len(nb)] = nb; views[vi] = bytes(bb)
    out = bytearray()
    for i, v in enumerate(j["bufferViews"]):
        while len(out) % 4: out += b"\0"
        v["byteOffset"] = len(out); v["byteLength"] = len(views[i]); out += views[i]
    while len(out) % 4: out += b"\0"
    j["buffers"][0]["byteLength"] = len(out)
    js = json.dumps(j, ensure_ascii=False, separators=(",", ":")).encode()
    while len(js) % 4: js += b" "
    open(BODY, "wb").write(struct.pack("<III", 0x46546C67, 2, 28 + len(js) + len(out)) + struct.pack("<II", len(js), 0x4E4F534A) + js
                           + struct.pack("<II", len(out), 0x004E4942) + bytes(out))
    print(f"몸에서 원래 구두 면 {n_rm}개 뺌 → {BODY}")
