"""자동 리깅 GLB 를 다시 리깅 — 뼈 위치 바로잡기 + 손가락 뼈 추가 + 무게(점마다 따라갈 뼈) 새로 입힘
   AI 로 만든 3D 모델 + 자동 리깅은 ① 팔·다리 뼈가 실제 팔·다리 가운데에서 몇 cm 벗어나 있고(팔꿈치·무릎이 이상하게 굽음)
   ② 손가락 뼈가 없고 ③ 손가락·소매·신발 조각이 엉덩이·등뼈에 붙어 있어, 움직이면 조각이 남아 길게 늘어남.
   → ① 팔꿈치·손목·엉덩관절·무릎·발목을 그 높이 단면의 가운데로 옮김
     ② 손 모양에서 손가락 다섯 개를 찾아 손가락마다 뼈 3개(엄지: Thumb1~3, 나머지: Index·Middle·Ring·Little 1~3)를 더함
     ③ 머리 아래 모든 점을 가까운 뼈 마디 두 개에 거리로 나눠 붙임(관절이 부드럽게). 규칙:
        · 허리 아래 몸통 폭 안쪽(재킷 밑단·치마)은 몸통에만, 바깥(소매·손)은 팔에만
        · 치마 끝 아래는 다리에만, 왼·오른쪽은 가르는 선으로(두 신발이 맞닿아 있으면 그 빈틈 자리)
        · 손가락이 갈라지는 곳(손가락 뿌리) 아래는 그 손가락에만
     ④ 서로 떨어져야 할 곳(왼발↔오른발, 손↔치마·몸통, 손가락↔다른 손가락)을 잇는 삼각형을 없앰
   사용: python 애니3D/glb_다시리깅.py <원본.glb> <결과.glb> [--치마끝 -0.33] [--머리 0.6] [--몸통폭 0.215] [--허리 0.15]
                                                          [--발높이 -0.78] [--발가름 0.006] [--확인 <그림.png>]
   · 몸통폭: 허리 아래에서 몸통과 소매 사이 빈틈(가운데에서 떨어진 x). 단면을 찍어 보고 정함 — 이 모델은 몸통 끝 0.19, 소매 시작 0.24
   · 발가름: 두 신발이 맞닿은 곳에서 점이 가장 적은 x. 이 모델은 +0.006
   · --확인: 손가락 뼈를 손 그림 위에 그려 저장(손가락을 제대로 찾았는지 눈으로 확인)
   뼈 이름: Root Hips Spine Chest Neck Head Jaw, UpperArm.L ForeArm.L Hand.L, UpperLeg.L LowerLeg.L Foot.L (R 도). 모델 좌표(원본) 기준.
   뼈는 회전 없이 위치만 있는 모델을 가정 (자동 리깅 GLB 가 대개 그러함)
   (사용자 결정 2026-11-22: 아나운서 모델 — 완벽해질 때까지 리깅, 뼈가 없으면 추가, 팔·손가락 움직임 확인)"""
import json, struct, sys
import numpy as np

a = sys.argv[1:]
opt = {"--치마끝": -0.33, "--머리": 0.6, "--몸통폭": 0.215, "--허리": 0.15, "--발높이": -0.78, "--발가름": 0.006}
check = None
if "--확인" in a: i = a.index("--확인"); check = a[i + 1]; del a[i:i + 2]
for k in list(opt):
    if k in a: i = a.index(k); opt[k] = float(a[i + 1]); del a[i:i + 2]
SKIRT, HEAD, TORSO, WAIST, FEET_Y, FEET_X = (opt[k] for k in ("--치마끝", "--머리", "--몸통폭", "--허리", "--발높이", "--발가름"))
src, dst = a[0], a[1]

# ── GLB 읽기 ──
raw = open(src, "rb").read()
n = struct.unpack("<I", raw[12:16])[0]; j = json.loads(raw[20:20 + n]); bin0 = 20 + n + 8
binlen = struct.unpack("<I", raw[20 + n:24 + n])[0]; BIN = raw[bin0:bin0 + binlen]
COMP = {5126: np.float32, 5125: np.uint32, 5123: np.uint16, 5121: np.uint8}; K = {"VEC3": 3, "VEC4": 4, "SCALAR": 1, "MAT4": 16}
views = [BIN[v.get("byteOffset", 0):v.get("byteOffset", 0) + v["byteLength"]] for v in j["bufferViews"]]


def get(i):
    ac = j["accessors"][i]; v = j["bufferViews"][ac["bufferView"]]
    assert not v.get("byteStride"), "띄엄띄엄 저장된(stride) 자료는 아직 못 고침"
    dt = np.dtype(COMP[ac["componentType"]]); k = K[ac["type"]]
    return np.frombuffer(views[ac["bufferView"]], dt, ac["count"] * k, ac.get("byteOffset", 0)).reshape(-1, k).copy()


def put(i, arr):
    """접근자 i 의 자료를 arr 로 바꿈 (그 bufferView 를 통째로 새로 씀 — 한 접근자만 쓰는 view 라고 가정)"""
    ac = j["accessors"][i]; dt = np.dtype(COMP[ac["componentType"]])
    assert ac.get("byteOffset", 0) == 0
    k = K[ac["type"]]; arr = np.asarray(arr).reshape(-1, k)
    views[ac["bufferView"]] = arr.astype(dt).tobytes(); ac["count"] = len(arr)


nodes = j["nodes"]
for nd in nodes:
    assert "rotation" not in nd and "matrix" not in nd and "scale" not in nd, "회전·크기가 있는 뼈는 아직 못 다룸"
parent = {c: i for i, nd in enumerate(nodes) for c in nd.get("children", [])}
NI = {nd.get("name"): i for i, nd in enumerate(nodes)}


def wpos(i):
    p = np.array(nodes[i].get("translation", [0, 0, 0]), float)
    while i in parent: i = parent[i]; p = p + np.array(nodes[i].get("translation", [0, 0, 0]), float)
    return p


W = {nm: wpos(i) for nm, i in NI.items() if nm}          # 뼈 세계 위치 (지금)
body = j["meshes"][0]["primitives"][0]
P = get(body["attributes"]["POSITION"])[:, :3].astype(float)


# 겨드랑이 아래 몸통↔팔 빈틈: 높이 1cm 마다 x 로 정렬해 가장 큰 틈(1.2cm 넘음)의 가운데 = 가르는 선. 틈이 없어지는 높이 = 겨드랑이
GAP = {}
for s_, sg_ in (("L", 1), ("R", -1)):
    ys_, bd_ = [], []
    arm_low = P[(P[:, 0] * sg_ > W[f"Hand.{s_}"][0] * sg_ - 0.03)][:, 1].min()     # 손가락 끝 높이 (팔이 있는 가장 낮은 곳)
    for yy in np.arange(arm_low + 0.005, W[f"UpperArm.{s_}"][1], 0.01):
        xs = np.sort(P[(np.abs(P[:, 1] - yy) < 0.004) & (P[:, 0] * sg_ > 0.08)][:, 0] * sg_)
        xs = xs[(xs > 0.1) & (xs < W[f"UpperArm.{s_}"][0] * sg_ + 0.25)]
        if len(xs) < 2: continue
        g = np.diff(xs); big = np.where(g >= 0.012)[0]
        if not len(big):
            if ys_ and yy > WAIST: break          # 허리 위에서 틈이 사라짐 = 겨드랑이
            continue
        i = int(big[-1])                          # 가장 바깥 틈 = 팔 바로 안쪽 (재킷 주머니·치마 사이 틈이 아님)
        ys_.append(yy); bd_.append((xs[i] + xs[i + 1]) / 2)
    bd_ = np.array(bd_); med = np.array([np.median(bd_[max(0, i - 3):i + 4]) for i in range(len(bd_))])
    bd_ = np.where(np.abs(bd_ - med) > 0.015, med, bd_)     # 소매 안쪽 빈 곳 같은 엉뚱한 틈은 이웃 높이 값으로
    GAP[s_] = (np.array(ys_), bd_)
    print(f"  {s_} 몸통·팔 가르는 선 (높이:x) " + " ".join(f"{a_:.2f}:{b_:.3f}" for a_, b_ in zip(ys_[::3], bd_[::3])) + f" … 겨드랑이 {ys_[-1]:.2f}")



# ── ① 관절을 팔·다리 가운데로 ──
def center_at(sel, y, band=0.012):
    m = sel & (np.abs(P[:, 1] - y) < band)
    if m.sum() < 30: return None
    q = P[m]; return np.array([(q[:, 0].min() + q[:, 0].max()) / 2, y, (q[:, 2].min() + q[:, 2].max()) / 2])


moved = []
for s, sg in (("L", 1), ("R", -1)):
    arm = P[:, 0] * sg > TORSO                                # 팔꿈치·손목 높이: 몸통 바깥 = 팔
    for nm, y in ((f"ForeArm.{s}", W[f"ForeArm.{s}"][1]), (f"Hand.{s}", W[f"Hand.{s}"][1] + 0.03)):
        c = center_at(arm, y)
        if c is not None: moved.append((nm, W[nm].copy(), c)); W[nm] = c
    side = (P[:, 0] > FEET_X) if s == "L" else (P[:, 0] <= FEET_X)
    # 다리 굵기(높이 1cm 마다 앞뒤 깊이 + 옆 폭)로 관절 높이 찾기 — 자동 리깅은 무릎을 종아리 한가운데, 발목을 신발 안에 둠
    #   발목 = 아래쪽에서 가장 가는 곳, 종아리 = 그 위 가장 굵은 곳, 무릎 = 치마 끝~종아리 사이 가장 얕은 곳
    #   엉덩관절 = 무릎 + 정강이 길이의 1.2배 (허벅지가 정강이보다 조금 김 — 치마에 가려 직접 못 잼)
    floor_y = P[:, 1].min(); prof = []
    for yy in np.arange(SKIRT - 0.01, floor_y + 0.06, -0.01):
        q = P[side & (np.abs(P[:, 1] - yy) < 0.004)]
        if len(q) > 20: prof.append((yy, q[:, 0].max() - q[:, 0].min(), q[:, 2].max() - q[:, 2].min()))
    prof = np.array(prof); ys2, wx, dz = prof[:, 0], prof[:, 1], prof[:, 2]
    lowp = ys2 < floor_y + 0.45 * (SKIRT - floor_y)
    ank = ys2[lowp][np.argmin((wx + dz)[lowp])]
    up = (ys2 > ank + 0.08) & (ys2 < ank + 0.6 * (SKIRT - ank))        # 종아리는 발목 위 아래쪽 60% 안 (위쪽 굵은 곳은 허벅지)
    calf = ys2[up][np.argmax(dz[up])]
    kn = (ys2 > calf + 0.02) & (ys2 < SKIRT - 0.005)
    knee = ys2[kn][np.argmin(dz[kn])] if kn.sum() >= 2 else calf + 0.07
    hip = knee + 1.2 * (knee - ank)
    print(f"  다리 {s}: 무릎 높이 {knee:.2f} · 종아리 {calf:.2f} · 발목 {ank:.2f} → 엉덩관절 {hip:.2f}")
    for nm, y in ((f"LowerLeg.{s}", knee), (f"Foot.{s}", ank)):
        c = center_at(side & (P[:, 1] < SKIRT), y)
        if c is not None: moved.append((nm, W[nm].copy(), c)); W[nm] = c
    c = center_at(side & (P[:, 1] < SKIRT), SKIRT - 0.06)     # 치마 바로 아래 허벅지 가운데 → 엉덩관절 x·z
    if c is not None:
        nm = f"UpperLeg.{s}"; new = np.array([c[0], hip, c[2]]); moved.append((nm, W[nm].copy(), new)); W[nm] = new
if W["Hips"][1] < min(W["UpperLeg.L"][1], W["UpperLeg.R"][1]):      # 골반 뼈는 엉덩관절보다 조금 위
    nm = "Hips"; new = W[nm].copy(); new[1] = max(W["UpperLeg.L"][1], W["UpperLeg.R"][1]) + 0.03
    moved.append((nm, W[nm].copy(), new)); W[nm] = new
# 어깨 관절: 자동 리깅은 어깨 바깥 끝·꼭대기에 둠(팔이 몸에서 떨어져 돌아 옷이 찢어짐) → 사람 비율로
#   높이 = 겨드랑이 + 키의 6.8%(어른 겨드랑이~어깨 관절 약 11cm), 옆 = 그 높이 몸 바깥 끝 - 위팔 반지름, 앞뒤 = 위팔 단면 가운데
HEIGHT = P[:, 1].max() - P[:, 1].min()
for s, sg in (("L", 1), ("R", -1)):
    ys_, bd_ = GAP[s]
    arm_y = ys_[-1] - 0.05                                     # 겨드랑이 조금 아래 위팔 단면
    q = P[(np.abs(P[:, 1] - arm_y) < 0.005) & (P[:, 0] * sg > np.interp(arm_y, ys_, bd_) + 0.003) & (P[:, 0] * sg < 0.5)]
    rad = (q[:, 0].max() - q[:, 0].min()) * sg * sg / 2
    zc = (q[:, 2].min() + q[:, 2].max()) / 2
    y_s = ys_[-1] + 0.068 * HEIGHT
    edge = (P[(np.abs(P[:, 1] - y_s) < 0.005) & (np.abs(P[:, 2] - zc) < 0.06)][:, 0] * sg).max()
    nm = f"UpperArm.{s}"; new = np.array([sg * (edge - rad), y_s, zc])
    moved.append((nm, W[nm].copy(), new)); W[nm] = new
for b_ in ("UpperArm", "ForeArm", "Hand", "UpperLeg", "LowerLeg", "Foot"):     # 왼·오른쪽 똑같이 (모델이 조금 비뚤어도 사람 뼈대는 대칭)
    l_, r_ = W[f"{b_}.L"], W[f"{b_}.R"]; m_ = (np.abs(l_) + np.abs(r_)) / 2
    W[f"{b_}.L"] = np.array([m_[0], (l_[1] + r_[1]) / 2, (l_[2] + r_[2]) / 2]); W[f"{b_}.R"] = np.array([-m_[0], (l_[1] + r_[1]) / 2, (l_[2] + r_[2]) / 2])
moved = [(nm, o, W[nm]) for nm, o, _ in moved]
for nm, o, c in moved: print(f"  {nm}: {np.round(o, 3)} → {np.round(c, 3)}")


# ── ② 손가락 찾기 ──
FINGERS = ["Thumb", "Index", "Middle", "Ring", "Little"]


def find_fingers(s, sg):
    """손 점들에서 손가락 다섯 개의 마디 위치(뿌리·가운데·끝마디·끝)를 찾음. 손은 아래(-y)로 늘어진 A 자세, 엄지가 앞(+z)이라고 가정"""
    wr = W[f"Hand.{s}"]
    H = P[(P[:, 0] * sg > TORSO + 0.06) & (P[:, 1] < wr[1])]

    # 손가락 뿌리 높이 ≈ 손목에서 가장 긴 손가락 끝까지의 46% (손 모양 비율)
    tip_y = H[:, 1].min(); knuckle = wr[1] + 0.46 * (tip_y - wr[1])
    # 뿌리 아래 점을 앞뒤(z)로 5 묶음(1차원 k-평균): 뒤에서부터 새끼·약지·중지·검지, 가장 앞 = 엄지
    zz = H[H[:, 1] < knuckle][:, 2]
    cen = np.quantile(zz, [0.08, 0.3, 0.5, 0.7, 0.95])
    for _ in range(50):
        lab = np.argmin(np.abs(zz[:, None] - cen[None]), axis=1)
        cen = np.array([zz[lab == c].mean() if (lab == c).any() else cen[c] for c in range(5)])
    cen = np.sort(cen)
    edges = [zz.min() - 0.01] + [(cen[c] + cen[c + 1]) / 2 for c in range(4)] + [zz.max() + 0.01]
    low = H[H[:, 1] < knuckle]
    out = {}
    for k, nm in enumerate(["Little", "Ring", "Middle", "Index"]):
        # 손가락 따라가기: 뿌리에서 3mm 씩 내려가며, 그 높이 단면에서 바로 앞 가운데와 가까운(8mm 안) 점들의 가운데로 이동
        #   단면을 손가락 사이 빈틈(1.5mm 넘는 z 틈)으로 덩어리로 나누고, 지금 자리가 든 덩어리의 가운데로 (한 걸음 0.6mm 까지).
        #   두 손가락이 붙어 한 덩어리(폭 2.2cm 넘음)면 자리를 그대로 둠
        zc = cen[k]; xc = None; path = []
        for yy in np.arange(knuckle - 0.004, tip_y - 0.01, -0.003):
            sl = low[np.abs(low[:, 1] - yy) < 0.002]
            if xc is not None: sl = sl[np.abs(sl[:, 0] - xc) < 0.015]
            if len(sl) < 4: break
            o_ = np.argsort(sl[:, 2]); zs = sl[o_, 2]; cut_ = np.where(np.diff(zs) > 0.0015)[0] + 1
            bl = [(sl[o_][a_:b_]) for a_, b_ in zip(np.r_[0, cut_], np.r_[cut_, len(zs)]) if b_ - a_ >= 3]
            if not bl: break
            dist = [0 if q_[:, 2].min() <= zc <= q_[:, 2].max() else min(abs(q_[:, 2].min() - zc), abs(q_[:, 2].max() - zc)) for q_ in bl]
            bi = int(np.argmin(dist))
            if dist[bi] > 0.005: break                       # 가까운 덩어리가 없음 = 손가락 끝을 지남
            q_ = bl[bi]; wdt = q_[:, 2].max() - q_[:, 2].min()
            if wdt < 0.022: zc += float(np.clip((q_[:, 2].min() + q_[:, 2].max()) / 2 - zc, -0.0006, 0.0006))
            near = q_[np.abs(q_[:, 2] - zc) < 0.007]
            xm = float(np.median((near if len(near) else q_)[:, 0])); xc = xm if xc is None else xc + float(np.clip(xm - xc, -0.003, 0.003))
            path.append((xc, yy, zc))
        tipc = np.array(path[-1]); q = low[(low[:, 2] > edges[k]) & (low[:, 2] <= edges[k + 1])]
        top = q[q[:, 1] > knuckle - 0.008]
        root = np.array([top[:, 0].mean(), knuckle, (edges[k] + edges[k + 1]) / 2])
        d = tipc - root; L = np.linalg.norm(d); u = d / L
        root = root - u * L * 0.2                    # 손가락 관절은 갈라지는 곳보다 조금 안쪽(손바닥)
        L = np.linalg.norm(tipc - root); u = (tipc - root) / L
        out[nm] = [root, root + u * L * 0.45, root + u * L * 0.73, tipc]        # 마디 길이 비율 45:28:27
    # 엄지: 검지 덩어리보다 앞(z 큰 쪽)에 있는 점
    T = H[(H[:, 2] > edges[4]) & (H[:, 1] < wr[1] - 0.015)]
    tip = T[np.argmin(T[:, 1] - 0.8 * T[:, 2])]             # 아래·앞으로 가장 먼 점 = 엄지 끝
    tipc = T[np.linalg.norm(T - tip, axis=1) < 0.008].mean(0)
    base = np.array([W[f"Hand.{s}"][0] + 0.004 * sg, wr[1] - 0.02, edges[4] - 0.006])
    print(f"    손 {s} 앞뒤 가름선 z:", np.round(edges[1:5], 3), "엄지 끝", np.round(tipc, 3))
    L = np.linalg.norm(tipc - base); u = (tipc - base) / L
    out["Thumb"] = [base, base + u * L * 0.4, base + u * L * 0.72, tipc]
    return out, knuckle


finger = {}
for s, sg in (("L", 1), ("R", -1)):
    f, kn = find_fingers(s, sg); finger[s] = f
    print(f"  손 {s}: 손가락 뿌리 높이 {kn:.3f}, " + ", ".join(f"{k} {np.linalg.norm(v[3] - v[0]) * 100:.1f}cm" for k, v in f.items()))

# ── 뼈대 새로 쓰기: 위치만 바꾸고(번역 = 내 세계 위치 - 부모 세계 위치), 손가락 뼈 노드 추가 ──
skin = j["skins"][0]
for s in "LR":
    par = None
    for fn in FINGERS:
        par = NI[f"Hand.{s}"]
        for k in range(3):
            nm = f"{fn}{k + 1}.{s}"; W[nm] = finger[s][fn][k]
            nodes.append({"name": nm, "translation": [0, 0, 0]}); ni = len(nodes) - 1; NI[nm] = ni
            nodes[par].setdefault("children", []).append(ni); parent[ni] = par
            skin["joints"].append(ni); par = ni
for nm, i in NI.items():
    if nm in W and i in parent:
        nodes[i]["translation"] = [float(v) for v in (W[nm] - W[nodes[parent[i]]["name"]])]
ibm = np.zeros((len(skin["joints"]), 16), np.float32)
for k, ni in enumerate(skin["joints"]):
    m = np.eye(4); m[:3, 3] = -W[nodes[ni]["name"]]; ibm[k] = m.T.reshape(-1)      # 열 우선
put(skin["inverseBindMatrices"], ibm)
J_OF = {nodes[ni]["name"]: k for k, ni in enumerate(skin["joints"])}

# ── ③ 무게 ──
SEG = [("Hips", W["Hips"], W["Spine"], "body"), ("Spine", W["Spine"], W["Chest"], "body"),
       ("Chest", W["Chest"], W["Neck"], "body"), ("Neck", W["Neck"], W["Head"], "body")]
for s in "LR":
    ua, fa, hd = W[f"UpperArm.{s}"], W[f"ForeArm.{s}"], W[f"Hand.{s}"]
    ul, ll, ft = W[f"UpperLeg.{s}"], W[f"LowerLeg.{s}"], W[f"Foot.{s}"]
    shin = np.linalg.norm(ll - ft)
    knuck = np.mean([finger[s][f][0] for f in FINGERS[1:]], axis=0)
    SEG += [(f"UpperArm.{s}", ua, fa, "arm" + s), (f"ForeArm.{s}", fa, hd, "arm" + s), (f"Hand.{s}", hd, knuck, "palm" + s),
            (f"UpperLeg.{s}", ul, ll, "leg" + s), (f"LowerLeg.{s}", ll, ft, "leg" + s),
            (f"Foot.{s}", ft, ft + np.array([0, -0.06, 0.12]) * shin / 0.28, "leg" + s)]
    for fn in FINGERS:
        c = finger[s][fn]
        for k in range(3): SEG.append((f"{fn}{k + 1}.{s}", c[k], c[k + 1], f"f{fn}{s}"))
SEG_G = np.array([s_[3] for s_ in SEG])


def body_side(Q, s, sg):
    """그 쪽 팔과 몸통을 가름: 1 = 몸통 쪽, 0 = 팔 쪽, -1 = 겨드랑이 위(가르지 않음)"""
    ys_, bd_ = GAP[s]; y = Q[:, 1]
    b = np.interp(y, ys_, bd_, left=bd_[0], right=bd_[-1])
    r = np.where(Q[:, 0] * sg < b, 1, 0)
    return np.where(y > ys_[-1], -1, r)


def allowed(Q):
    x, y = Q[:, 0], Q[:, 1]
    bsL, bsR = body_side(Q, "L", 1), body_side(Q, "R", -1)
    bs = np.where(x > 0, bsL, bsR)                 # 1 몸통 쪽, 0 팔 쪽, -1 겨드랑이 위
    ok = {"body": (y >= SKIRT) & (bs != 0)}
    for s, sg in (("L", 1), ("R", -1)):
        ok["arm" + s] = (sg * x > 0) & (bs != 1) & (y > SKIRT)
        ok["palm" + s] = ok["arm" + s]
        cut = np.where(y < FEET_Y, FEET_X, 0.0)
        ok["leg" + s] = ((x > cut) if s == "L" else (x <= cut)) & (y < SKIRT)
        f = finger[s]; kn_y = np.mean([f[n][0][1] for n in FINGERS[1:]])
        idx_z = max(f[n][3][2] for n in FINGERS[1:])
        for fn in FINGERS:
            if fn == "Thumb":     # 엄지: 손바닥보다 앞(검지 앞쪽)이면서 엄지 뿌리 아래
                ok[f"f{fn}{s}"] = ok["arm" + s] & (Q[:, 2] > f["Index"][1][2] + 0.008) & (y < f[fn][0][1] + 0.004)
            else:                 # 네 손가락: 손가락 뿌리(갈라지는 곳) 조금 위부터 아래
                ok[f"f{fn}{s}"] = ok["arm" + s] & (y < kn_y + 0.01)
    return ok


def reskin(Q):
    ok = allowed(Q)
    D = np.full((len(Q), len(SEG)), np.inf)
    for c, (nm, p0, p1, grp) in enumerate(SEG):
        v = p1 - p0; t = np.clip(((Q - p0) @ v) / (v @ v), 0, 1)
        D[:, c] = np.where(ok[grp], np.linalg.norm(Q - (p0 + t[:, None] * v), axis=1), np.inf)
    o = np.argsort(D, axis=1)[:, :2]
    d1, d2 = D[np.arange(len(Q)), o[:, 0]], D[np.arange(len(Q)), o[:, 1]]
    w1 = 1 / np.maximum(d1, 1e-4) ** 4; w2 = np.where(np.isfinite(d2) & (d2 < d1 * 1.6), 1 / np.maximum(d2, 1e-4) ** 4, 0)
    g1, g2 = SEG_G[o[:, 0]], SEG_G[o[:, 1]]
    f1, f2 = np.char.startswith(g1, "f"), np.char.startswith(g2, "f")
    w2 = np.where(f1 & f2 & (g1 != g2), 0, w2)       # 다른 손가락끼리는 섞지 않음 (손가락 사이가 늘어나지 않게)
    tot = w1 + w2; jid = np.array([J_OF[s_[0]] for s_ in SEG])
    j1, j2, w1, w2 = jid[o[:, 0]], jid[o[:, 1]], w1 / tot, w2 / tot
    # 어깨(겨드랑이 위 ~ 어깨 위 10cm): 가슴과 위팔 사이를 가운데에서 바깥으로 갈수록 위팔 쪽으로 부드럽게
    for s, sg in (("L", 1), ("R", -1)):
        ax_ = Q[:, 0] * sg; sh = W[f"UpperArm.{s}"]
        m = (Q[:, 1] > GAP[s][0][-1]) & (Q[:, 1] < sh[1] + 0.1) & (ax_ > 0.12) & (ax_ < sh[0] * sg + 0.04) \
            & np.isin(SEG_G[o[:, 0]], ["body", "arm" + s])
        u = np.clip((ax_[m] - 0.13) / (sh[0] * sg + 0.03 - 0.13), 0, 1); u = u * u * (3 - 2 * u)
        j1[m] = J_OF[f"UpperArm.{s}"]; j2[m] = J_OF["Chest"]; w1[m] = u; w2[m] = 1 - u
    return j1, j2, w1, w2


def group_of(nm):
    s = "L" if nm.endswith(".L") else "R" if nm.endswith(".R") else ""
    for fn in FINGERS:
        if nm.startswith(fn): return "f" + fn + s
    if "Leg" in nm or "Foot" in nm: return "leg" + s
    if "Hand" in nm or "ForeArm" in nm: return "hand" + s
    if "UpperArm" in nm: return "uarm" + s
    return "lower" if nm in ("Hips", "Root") else "upper"


GR = {k: group_of(nm) for nm, k in J_OF.items()}
BAD = {frozenset(p) for p in [("legL", "legR"), ("handL", "lower"), ("handR", "lower"), ("handL", "legL"), ("handL", "legR"),
                               ("handR", "legL"), ("handR", "legR"), ("handL", "handR"), ("handL", "upper"), ("handR", "upper")]}
for s in "LR":       # 손가락끼리, 손가락↔몸통·치마·다리
    fs = ["f" + f + s for f in FINGERS]
    for i_, x_ in enumerate(fs):
        for y_ in fs[i_ + 1:]: BAD.add(frozenset((x_, y_)))
        for o_ in ("lower", "upper", "legL", "legR"): BAD.add(frozenset((x_, o_)))
n_v = n_cut = 0
for mesh in j["meshes"]:
    for pr in mesh["primitives"]:
        at = pr["attributes"]
        if "JOINTS_0" not in at: continue
        Q = get(at["POSITION"])[:, :3].astype(float); J = get(at["JOINTS_0"]).astype(np.int64)
        wac = j["accessors"][at["WEIGHTS_0"]]; Wt = get(at["WEIGHTS_0"]).astype(np.float64)
        if wac["componentType"] == 5121: Wt /= 255
        elif wac["componentType"] == 5123: Wt /= 65535
        sel = Q[:, 1] < HEAD; sk = np.zeros(len(Q), bool)
        if sel.any():
            j1, j2, w1, w2 = reskin(Q[sel])
            J[sel] = 0; Wt[sel] = 0; J[sel, 0] = j1; J[sel, 1] = np.where(w2 > 0, j2, 0); Wt[sel, 0] = w1; Wt[sel, 1] = w2
            # 치마(엉덩관절 높이 ~ 치마 끝, 몸통 폭 안): 허벅지를 조금씩 따라가게 — 위는 0, 치마 끝은 100%.
            #   가운데 솔기 근처는 왼·오른 허벅지를 섞어 한쪽 다리만 들어도 가운데가 찢어지지 않게 (나머지는 골반)
            hip_y = W["UpperLeg.L"][1]; Qs = Q
            sk = sel & (Qs[:, 1] < hip_y) & (Qs[:, 1] >= SKIRT) & (np.abs(Qs[:, 0]) < TORSO)
            f_ = np.clip((hip_y - Qs[sk, 1]) / (hip_y - SKIRT), 0, 1); f_ = f_ * f_ * (3 - 2 * f_)
            lr = np.clip(0.5 + Qs[sk, 0] / 0.08, 0, 1)                      # 1 = 왼다리 쪽
            J[sk, 0] = J_OF["Hips"]; J[sk, 1] = J_OF["UpperLeg.L"]; J[sk, 2] = J_OF["UpperLeg.R"]; J[sk, 3] = 0
            Wt[sk, 0] = 1 - f_; Wt[sk, 1] = f_ * lr; Wt[sk, 2] = f_ * (1 - lr); Wt[sk, 3] = 0
        n_v += int(sel.sum())
        if wac["componentType"] == 5121: Wq = np.round(Wt * 255); Wq[:, 0] += 255 - Wq.sum(1)
        elif wac["componentType"] == 5123: Wq = np.round(Wt * 65535); Wq[:, 0] += 65535 - Wq.sum(1)
        else: Wq = Wt
        put(at["JOINTS_0"], J); put(at["WEIGHTS_0"], Wq)
        if "indices" in pr:
            I = get(pr["indices"]).reshape(-1, 3)
            g = np.array([GR.get(int(x), "upper") for x in J[np.arange(len(J)), Wt.argmax(1)]])
            g[sk] = "lower"                       # 치마는 다리를 섞어 따라가도 '골반' 무리 (가운데 솔기를 자르지 않게)
            gt = g[I]; kill = np.zeros(len(I), bool)
            for a_, b_ in ((0, 1), (1, 2), (0, 2)):
                kill |= np.fromiter((frozenset((x, y)) in BAD for x, y in zip(gt[:, a_], gt[:, b_])), bool, len(I))
            I[kill] = I[kill][:, :1]; n_cut += int(kill.sum()); put(pr["indices"], I.reshape(-1, 1))

# ── GLB 다시 쓰기 (bufferView 를 차례로 4바이트 맞춰 이어 붙임) ──
out = bytearray()
for i, v in enumerate(j["bufferViews"]):
    while len(out) % 4: out += b"\0"
    v["byteOffset"] = len(out); v["byteLength"] = len(views[i]); out += views[i]
while len(out) % 4: out += b"\0"
j["buffers"][0]["byteLength"] = len(out)
js = json.dumps(j, ensure_ascii=False, separators=(",", ":")).encode()
while len(js) % 4: js += b" "
glb = struct.pack("<III", 0x46546C67, 2, 12 + 8 + len(js) + 8 + len(out)) + struct.pack("<II", len(js), 0x4E4F534A) + js \
    + struct.pack("<II", len(out), 0x004E4942) + bytes(out)
open(dst, "wb").write(glb)
print(f"뼈 {len(skin['joints'])}개(손가락 30개 추가) · 머리 아래 점 {n_v}개 무게 새로 · 떨어져야 할 곳 삼각형 {n_cut}개 없앰 → {dst}")

if check:     # 손가락 뼈 확인 그림: 옆(z-y)·앞(x-y)에서 손 점 + 뼈
    from PIL import Image, ImageDraw
    im = Image.new("RGB", (1600, 520), "white"); d = ImageDraw.Draw(im)
    cols = {"Thumb": "red", "Index": "orange", "Middle": "green", "Ring": "blue", "Little": "purple"}
    for col, (s, sg) in enumerate((("L", 1), ("R", -1))):
        wr = W[f"Hand.{s}"]; H = P[(P[:, 0] * sg > TORSO + 0.03) & (P[:, 1] < wr[1] + 0.04)]
        for half, ax in enumerate((2, 0)):
            cx = col * 800 + half * 400 + 200; c0 = wr[ax]; sx = (sg if ax == 0 else 1)
            f = lambda p: (cx + (p[ax] - c0) * 2500 * sx, 30 + (wr[1] + 0.04 - p[1]) * 2500)
            for p in H[::3]: d.point(f(p), fill=(170, 170, 170))
            d.line([f(W[f"ForeArm.{s}"]), f(wr)], fill="black", width=3)
            for fn, pts in finger[s].items():
                for k in range(3): d.line([f(pts[k]), f(pts[k + 1])], fill=cols[fn], width=3)
                for p in pts: d.ellipse([f(p)[0] - 3, f(p)[1] - 3, f(p)[0] + 3, f(p)[1] + 3], fill=cols[fn])
            d.text((cx - 180, 8), f"hand {s} {'side z-y' if ax == 2 else 'front x-y'}", fill="black")
    im.save(check); print("손가락 뼈 확인 그림:", check)
    # 몸 전체 뼈대: 앞(x-y)·옆(z-y) — 관절이 몸 안 알맞은 곳(어깨·팔꿈치·무릎 가운데)에 있는지
    im = Image.new("RGB", (1200, 1000), "white"); d = ImageDraw.Draw(im); sc = 900 / HEIGHT; top = P[:, 1].max()
    for half, ax in enumerate((0, 2)):
        cx = 300 + half * 600
        f = lambda p: (cx + p[ax] * sc, 50 + (top - p[1]) * sc)
        for p in P[::25]: d.point(f(p), fill=(185, 185, 185))
        for nm, i in NI.items():
            if nm in W and i in parent and nodes[parent[i]].get("name") in W and not any(nm.startswith(fn) for fn in FINGERS):
                d.line([f(W[nodes[parent[i]]["name"]]), f(W[nm])], fill="red", width=3)
        for nm in W:
            if not any(nm.startswith(fn) for fn in FINGERS) and nm in NI:
                d.ellipse([f(W[nm])[0] - 4, f(W[nm])[1] - 4, f(W[nm])[0] + 4, f(W[nm])[1] + 4], fill="blue")
        d.text((cx - 250, 15), "front x-y" if ax == 0 else "side z-y", fill="black")
    p2 = check.rsplit(".", 1)[0] + "_뼈대.png"; im.save(p2); print("뼈대 확인 그림:", p2)
