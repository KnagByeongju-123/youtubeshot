"""GLB 사람 모델: 머리카락 가장자리의 살색 '버(가시)' 없애기
   AI 로 만든 3D 사람의 겉면 그림은 머리카락이 얼굴과 만나는 곳(관자놀이 머리선, 볼 옆으로 내려온 머리 안쪽)에
   살색 띠가 칠해져 있어, 머리 가장자리에 하얀 가시처럼 보임 (여자 아나운서 2026-11-23 사용자 지적, 원본 모델에도 있음).
   → 머리 높이의 삼각형마다 겉면 그림 밝기를 재서, 밝은(살색) 삼각형인데 둘레 2칸 이웃의 대부분이 어두운 머리카락이면
     '머리카락 위 살색 조각'으로 보고 그 삼각형을 겉면 그림에서 둘레 머리카락 색으로 칠함 (2번 반복해 조각이 이어진 띠도)
   사용: python 애니3D/glb_머리경계정리.py <입력.glb> <결과.glb> [--확인 <그림.png>] [--칠칸 u0,u1,v0,v1 ...]
   얼굴 가운데(눈·코·입이 있는 앞면)는 건드리지 않음: 얼굴 가운데에서 옆으로 5cm 넘는 곳만"""
import io, json, struct, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

a = sys.argv[1:]
check = None
if "--확인" in a: i = a.index("--확인"); check = a[i + 1]; del a[i:i + 2]
while "--칠칸" in a: i = a.index("--칠칸"); del a[i:i + 2]
src, dst = a
raw = open(src, "rb").read()
n = struct.unpack("<I", raw[12:16])[0]; j = json.loads(raw[20:20 + n]); bin0 = 20 + n + 8
binlen = struct.unpack("<I", raw[20 + n:24 + n])[0]; BIN = raw[bin0:bin0 + binlen]
views = [BIN[v.get("byteOffset", 0):v.get("byteOffset", 0) + v["byteLength"]] for v in j["bufferViews"]]
COMP = {5126: np.float32, 5125: np.uint32, 5123: np.uint16, 5121: np.uint8}; K = {"VEC2": 2, "VEC3": 3, "SCALAR": 1}


def get(i):
    ac = j["accessors"][i]; dt = np.dtype(COMP[ac["componentType"]])
    return np.frombuffer(views[ac["bufferView"]], dt, ac["count"] * K[ac["type"]], ac.get("byteOffset", 0)).reshape(-1, K[ac["type"]]).astype(float)


mesh = j["meshes"][0]; pr = mesh["primitives"][0]
P = get(pr["attributes"]["POSITION"]); UV = get(pr["attributes"]["TEXCOORD_0"]); I = get(pr["indices"]).reshape(-1, 3).astype(np.int64)
mat = j["materials"][pr["material"]]; img = j["images"][j["textures"][mat["pbrMetallicRoughness"]["baseColorTexture"]["index"]]["source"]]
TEX = np.asarray(Image.open(io.BytesIO(views[img["bufferView"]])).convert("RGB")).astype(float); th, tw = TEX.shape[:2]


def tri_color(t):
    """삼각형 세 꼭짓점 + 가운데의 겉면 그림 색 평균"""
    uv = UV[t]; pts = np.concatenate([uv, uv.mean(1, keepdims=True)], 1)       # (n,4,2)
    px = np.clip((pts[..., 0] * tw).astype(int), 0, tw - 1); py = np.clip((pts[..., 1] * th).astype(int), 0, th - 1)
    return TEX[py, px].mean(1)


ok = I[:, 0] != I[:, 1]
top = P[:, 1].max(); H_ = top - P[:, 1].min()
x, y = P[:, 0], P[:, 1]
cx = np.median(x[(y > top - 0.12 * H_) & (y < top - 0.05 * H_)])                     # 머리 가운데 x
reg_v = (y > top - 0.22 * H_) & (y < top - 0.02 * H_) & (np.abs(x - cx) > 0.05)    # 머리 높이, 얼굴 가운데에서 5cm 넘게 옆
tri = np.where(ok & reg_v[I].all(1))[0]
col = tri_color(I[tri]); lum = col.mean(1)
# 이웃: 꼭짓점을 같은 자리끼리 묶어 삼각형 이웃 찾기
_, gid = np.unique(np.round(P * 2e4).astype(np.int64), axis=0, return_inverse=True); gid = gid.reshape(-1)
G = gid[I[tri]]
from collections import defaultdict
by_v = defaultdict(list)
for k_, g3 in enumerate(G):
    for g in g3: by_v[g].append(k_)
nb = [set(k2 for g in g3 for k2 in by_v[g]) - {k_} for k_, g3 in enumerate(G)]
DARK, PALE = 95, 150
fixed = np.zeros(len(tri), bool); newcol = col.copy()
for rnd in range(3):
    dark = (lum < DARK) | fixed
    cand = []
    for k_ in np.where((lum >= PALE) & ~fixed)[0]:
        ring = set(nb[k_]); ring2 = set(k3 for k2 in ring for k3 in nb[k2]) - {k_}
        r = list(ring | ring2)
        if len(r) < 6: continue
        if dark[r].mean() >= 0.7: cand.append((k_, r))
    if not cand: break
    for k_, r in cand:
        dr = [k2 for k2 in r if dark[k2]]
        newcol[k_] = np.median(newcol[dr], 0); fixed[k_] = True
    print(f"  {rnd + 1}번째: 머리카락 위 살색 조각 {len(cand)}개")
# ② --칠칸 u0,u1,v0,v1 (여러 번 가능): 겉면 그림의 그 칸 안 밝은(살색) 점만 같은 칸의 머리색으로 — 자동으로 못 찾는 큰 살색 띠용
#    (여자 아나운서 왼쪽 볼 옆 '버' = u .130~.152, v .905~.95 — 그 칸은 그 자리에서만 쓰여 안전. 칸을 정하기 전에 그 칸을 쓰는 점이
#     다른 곳에 없는지 꼭 확인: 이 모델은 왼·오른 얼굴이 같은 그림 칸을 쓰는 곳이 있어, 넓게 칠하면 반대쪽 볼까지 칠해졌음)
TEX2 = None
args_ = sys.argv[1:]
for k_, a_ in enumerate(args_):
    if a_ == "--칠칸":
        u0, u1, v0, v1 = (float(v) for v in args_[k_ + 1].split(","))
        if TEX2 is None: TEX2 = TEX.copy()
        sub = TEX2[int(v0 * th):int(v1 * th), int(u0 * tw):int(u1 * tw)]
        lum2 = sub.mean(2); hair2 = np.median(sub[lum2 < DARK], 0)
        pale = (lum2 > 110).astype(float)
        pm = np.asarray(Image.fromarray((pale * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.GaussianBlur(1)), float)[:, :, None] / 255
        sub[:] = sub * (1 - pm) + hair2 * pm
        print(f"  칠칸 u{u0}~{u1} v{v0}~{v1}: 밝은 점 {int(pale.sum())}개 → 머리색 {hair2.astype(int)}")
if TEX2 is not None: TEX = TEX2
# 겉면 그림에 칠하기
al = Image.new("L", (tw, th), 0); cl = Image.new("RGB", (tw, th)); da = ImageDraw.Draw(al); dc = ImageDraw.Draw(cl)
for k_ in np.where(fixed)[0]:
    uv = [(float(UV[v, 0] * tw), float(UV[v, 1] * th)) for v in I[tri[k_]]]
    us_, vs_ = [q[0] for q in uv], [q[1] for q in uv]
    if max(us_) - min(us_) > 60 or max(vs_) - min(vs_) > 60: continue
    da.polygon(uv, fill=255); dc.polygon(uv, fill=tuple(int(v) for v in newcol[k_]))
alpha = np.asarray(al.filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.GaussianBlur(1)), float)[:, :, None] / 255
colr = np.asarray(cl.filter(ImageFilter.MaxFilter(3)), float)
out_t = TEX * (1 - alpha) + colr * alpha
bio = io.BytesIO(); Image.fromarray(np.clip(out_t, 0, 255).astype(np.uint8)).save(bio, "JPEG" if img.get("mimeType") == "image/jpeg" else "PNG", quality=95)
views[img["bufferView"]] = bio.getvalue()
print(f"머리카락 가장자리 살색 조각 {int(fixed.sum())}개를 둘레 머리색으로 칠함")
if check:
    sm = Image.fromarray(np.clip(out_t, 0, 255).astype(np.uint8)).resize((1024, 1024))
    m_ = Image.fromarray((alpha[:, :, 0] * 255).astype(np.uint8)).resize((1024, 1024))
    sm.paste((255, 0, 0), mask=m_.point(lambda v: 160 if v > 30 else 0)); sm.save(check); print("확인 그림:", check)

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
