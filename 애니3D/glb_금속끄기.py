"""GLB 재질에 metallicFactor 0 을 적음 (사용자 2026-11-27 '피부색' — Rocketbox 를 블렌더로 내보내면 metallicFactor 가 빠짐 → glTF 기본값 1(금속) → three.js 에서 피부가 회색·얼룩, 눈가·코 그늘이 시커멓게 보였음)
   그림·모양은 그대로, 파일 앞 JSON 만 고침. 이미 metallicFactor 가 있으면 그대로 둠(--모두 를 붙이면 모두 0)
   사용: python 애니3D/glb_금속끄기.py <입력.glb> [<출력.glb>] [--모두] [--점색남김]
   점마다 칠한 색(COLOR_0·1)도 기본으로 지움 (three.js 에서 머리카락이 청록색으로 보였음, 2026-11-27)"""
import sys, json, struct

a = sys.argv[1:]; src = a[0]; dst = a[1] if len(a) > 1 and not a[1].startswith("--") else src
d = open(src, "rb").read()
jl = struct.unpack("<I", d[12:16])[0]; j = json.loads(d[20:20 + jl]); rest = d[20 + jl:]
n = 0; nc = 0
if "--점색남김" not in a:      # 점마다 칠한 색(COLOR_0/1, Rocketbox 원본에서 딸려 옴) — three.js 는 이것을 그림 색에 곱해 머리카락이 청록, 피부가 칙칙해졌음 → 지움
    for me in j.get("meshes", []):
        for pr in me["primitives"]:
            for k in [k for k in pr["attributes"] if k.startswith("COLOR_")]: del pr["attributes"][k]; nc += 1
for me_ in j.get("meshes", []):        # 모양 키 기본값을 0 으로 — 블렌더로 빈 키를 더하면 1 로 저장되어 다른 보기 프로그램에서 입이 벌어져 보였음 (2026-11-28 여자아나운서5)
    if any(w != 0 for w in me_.get("weights", [])): me_["weights"] = [0.0] * len(me_["weights"]); print("모양 키 기본값 0:", me_.get("name"))
for m in j.get("materials", []):
    pbr = m.setdefault("pbrMetallicRoughness", {})
    if "metallicFactor" not in pbr or "--모두" in a: pbr["metallicFactor"] = 0.0; n += 1
js = json.dumps(j, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
js += b" " * ((4 - len(js) % 4) % 4)
out = d[:12] + struct.pack("<I", len(js)) + b"JSON" + js + rest
out = out[:8] + struct.pack("<I", len(out)) + out[12:]
open(dst, "wb").write(out)
print("금속 끔:", n, "재질, 점색 지움:", nc, "→", dst)
