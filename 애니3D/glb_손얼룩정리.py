"""GLB 사람 모델: 손에 묻은 검은·갈색 얼룩 없애기
   AI 로 만든 3D 사람의 겉면 그림은 손등·엄지 뿌리에 머리카락·옷 색이 잘못 칠해져 검은 얼룩처럼 보이는 일이 있음
   (여자 아나운서 오른손 엄지 뿌리, 2026-11-23 손가락 검사에서 찾음)
   → 손 높이·손 자리(어깨 바깥) 삼각형 중 겉면 그림이 어두운(밝기 < 90) 것을, 그 삼각형 자리만 겉면 그림에서 둘레 손 살색으로 칠함.
     다른 곳(얼굴·몸)이 같은 그림 칸을 쓰면 그 칸은 건드리지 않음 (겹침 검사)
   사용: python 애니3D/glb_손얼룩정리.py <입력.glb> <결과.glb> [--확인 <그림.png>]"""
import io, json, struct, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

a = sys.argv[1:]
check = None
if "--확인" in a: i = a.index("--확인"); check = a[i + 1]; del a[i:i + 2]
src, dst = a
raw = open(src, "rb").read()
n = struct.unpack("<I", raw[12:16])[0]; j = json.loads(raw[20:20 + n]); bin0 = 20 + n + 8
binlen = struct.unpack("<I", raw[20 + n:24 + n])[0]; BIN = raw[bin0:bin0 + binlen]
views = [BIN[v.get("byteOffset", 0):v.get("byteOffset", 0) + v["byteLength"]] for v in j["bufferViews"]]
COMP = {5126: np.float32, 5125: np.uint32, 5123: np.uint16, 5121: np.uint8}; K = {"VEC2": 2, "VEC3": 3, "SCALAR": 1}


def get(i):
    ac = j["accessors"][i]; dt = np.dtype(COMP[ac["componentType"]])
    return np.frombuffer(views[ac["bufferView"]], dt, ac["count"] * K[ac["type"]], ac.get("byteOffset", 0)).reshape(-1, K[ac["type"]]).astype(float)


pr = j["meshes"][0]["primitives"][0]
P = get(pr["attributes"]["POSITION"]); UV = get(pr["attributes"]["TEXCOORD_0"]); I = get(pr["indices"]).reshape(-1, 3).astype(np.int64)
mat = j["materials"][pr["material"]]; img = j["images"][j["textures"][mat["pbrMetallicRoughness"]["baseColorTexture"]["index"]]["source"]]
TEX = np.asarray(Image.open(io.BytesIO(views[img["bufferView"]])).convert("RGB")).astype(float); th, tw = TEX.shape[:2]
# 손 자리: 스킨의 손 뼈(Hand.L/R) 무게가 큰 점 (손가락 뼈 포함)
sk = j["skins"][0]; names = [j["nodes"][q]["name"] for q in sk["joints"]]
Jt = get(pr["attributes"]["JOINTS_0"]) if False else None
ac = j["accessors"][pr["attributes"]["JOINTS_0"]]; Jt = np.frombuffer(views[ac["bufferView"]], np.dtype(COMP[ac["componentType"]]), ac["count"] * 4, ac.get("byteOffset", 0)).reshape(-1, 4)
ac = j["accessors"][pr["attributes"]["WEIGHTS_0"]]; Wt = np.frombuffer(views[ac["bufferView"]], np.dtype(COMP[ac["componentType"]]), ac["count"] * 4, ac.get("byteOffset", 0)).reshape(-1, 4).astype(float)
if Wt.max() > 1.5: Wt /= 255 if Wt.max() <= 255 else 65535
hand_ids = [k for k, nm in enumerate(names) if any(nm.startswith(p) for p in ("Hand", "Thumb", "Index", "Middle", "Ring", "Little", "LeftHand", "RightHand"))]
hw = sum(((Jt == k) * Wt).sum(1) for k in hand_ids)
is_hand = hw > 0.5
uvc = UV[I].mean(1)
col = TEX[np.clip((uvc[:, 1] * th).astype(int), 0, th - 1), np.clip((uvc[:, 0] * tw).astype(int), 0, tw - 1)]
lum = col.mean(1)
htri = is_hand[I].all(1) & (I[:, 0] != I[:, 1])
# 소매 끝(정장 색)은 손 뼈 무게가 있어도 빼기: 손목 관절에서 손가락 쪽으로 1.5cm 넘게 나간 삼각형만
ibm = np.frombuffer(views[j["accessors"][sk["inverseBindMatrices"]]["bufferView"]], np.float32, len(names) * 16,
                    j["accessors"][sk["inverseBindMatrices"]].get("byteOffset", 0)).reshape(-1, 4, 4)
jp = {nm: np.linalg.inv(m.T.astype(float))[:3, 3] for nm, m in zip(names, ibm)}
cen = P[I].mean(1); past = np.zeros(len(I), bool)
for sd in ("L", "R"):
    if f"Hand.{sd}" not in jp or f"Middle1.{sd}" not in jp: continue
    w0 = jp[f"Hand.{sd}"]; dv = jp[f"Middle1.{sd}"] - w0; L = np.linalg.norm(dv); dv /= L
    near = np.linalg.norm(cen - w0, axis=1) < 0.25
    past |= near & ((cen - w0) @ dv > 0.015)
htri &= past
dark = np.where(htri & (lum < 90))[0]
skin = np.median(col[htri & (lum > 150)], 0)
print(f"손 삼각형 {htri.sum()}개 중 어두운 얼룩 {len(dark)}개, 손 살색 {skin.astype(int)}")
al = Image.new("L", (tw, th), 0); da = ImageDraw.Draw(al)
for t in dark:
    uv = [(float(UV[v, 0] * tw), float(UV[v, 1] * th)) for v in I[t]]
    if max(q[0] for q in uv) - min(q[0] for q in uv) > 60 or max(q[1] for q in uv) - min(q[1] for q in uv) > 60: continue
    da.polygon(uv, fill=255)
mask = np.asarray(al.filter(ImageFilter.MaxFilter(5)), float) > 0
# 겹침 검사: 손이 아닌 삼각형이 칠할 칸을 쓰면 그 자리는 빼기
other = np.where(~is_hand[I].any(1))[0]
ox = np.clip((uvc[other, 0] * tw).astype(int), 0, tw - 1); oy = np.clip((uvc[other, 1] * th).astype(int), 0, th - 1)
hit = mask[oy, ox]
if hit.any():
    bl = Image.new("L", (tw, th), 0); db = ImageDraw.Draw(bl)
    for t in other[hit]: db.polygon([(float(UV[v, 0] * tw), float(UV[v, 1] * th)) for v in I[t]], fill=255)
    mask &= ~(np.asarray(bl, float) > 0)
    print(f"  다른 곳과 같은 칸 {hit.sum()}개 → 그 자리는 칠하지 않음")
# 칠할 자리 안의 어두운 점만 살색으로 (밝은 점은 그대로), 가장자리는 부드럽게
pale = TEX.mean(2) < 120
m = (mask & pale).astype(np.uint8) * 255
alpha = np.asarray(Image.fromarray(m).filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.GaussianBlur(1)), float)[:, :, None] / 255
alpha *= mask[:, :, None]
# 살색은 근처 밝은 점 색 (흐리게 퍼뜨려 그림자 결을 살림)
bright = (TEX.mean(2) > 150)[:, :, None]
num = np.asarray(Image.fromarray(np.clip(TEX * bright, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(6)), float)
den = np.asarray(Image.fromarray((bright[:, :, 0] * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(6)), float)[:, :, None] / 255
near = np.where(den > 0.05, num / np.maximum(den, 1e-3), skin)
out_t = TEX * (1 - alpha) + near * alpha
print(f"칠한 점 {int((alpha[:, :, 0] > 0.1).sum())}개")
bio = io.BytesIO(); Image.fromarray(np.clip(out_t, 0, 255).astype(np.uint8)).save(bio, "JPEG" if img.get("mimeType") == "image/jpeg" else "PNG", quality=95)
views[img["bufferView"]] = bio.getvalue()
if check:
    sm = Image.fromarray(np.clip(out_t, 0, 255).astype(np.uint8)); m_ = Image.fromarray((alpha[:, :, 0] * 255).astype(np.uint8))
    sm.paste((255, 0, 0), mask=m_.point(lambda v: 160 if v > 30 else 0)); sm.resize((1024, 1024)).save(check); print("확인 그림:", check)
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
