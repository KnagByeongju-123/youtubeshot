"""GLB 재질에 metallicFactor 0 을 적음 (사용자 2026-11-27 '피부색' — Rocketbox 를 블렌더로 내보내면 metallicFactor 가 빠짐 → glTF 기본값 1(금속) → three.js 에서 피부가 회색·얼룩, 눈가·코 그늘이 시커멓게 보였음)
   그림·모양은 그대로, 파일 앞 JSON 만 고침. 이미 metallicFactor 가 있으면 그대로 둠(--모두 를 붙이면 모두 0)
   사용: python 애니3D/glb_금속끄기.py <입력.glb> [<출력.glb>] [--모두]"""
import sys, json, struct

a = sys.argv[1:]; src = a[0]; dst = a[1] if len(a) > 1 and not a[1].startswith("--") else src
d = open(src, "rb").read()
jl = struct.unpack("<I", d[12:16])[0]; j = json.loads(d[20:20 + jl]); rest = d[20 + jl:]
n = 0
for m in j.get("materials", []):
    pbr = m.setdefault("pbrMetallicRoughness", {})
    if "metallicFactor" not in pbr or "--모두" in a: pbr["metallicFactor"] = 0.0; n += 1
js = json.dumps(j, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
js += b" " * ((4 - len(js) % 4) % 4)
out = d[:12] + struct.pack("<I", len(js)) + b"JSON" + js + rest
out = out[:8] + struct.pack("<I", len(out)) + out[12:]
open(dst, "wb").write(out)
print("금속 끔:", n, "재질 →", dst)
