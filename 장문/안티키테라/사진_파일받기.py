"""파일 이름을 알 때: python 사진_파일받기.py <저장폴더> c01_9="File:NAMA Machine d'Anticythère 1.jpg" ..."""
import json, os, sys, time, urllib.parse, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 사진_찾기 import UA, api, strip
out = sys.argv[1]; meta_p = os.path.join(out, "후보.json"); meta = json.load(open(meta_p, encoding="utf-8"))
for arg in sys.argv[2:]:
    k, _, title = arg.partition("=")
    d = api({"action": "query", "titles": title, "prop": "imageinfo", "iiprop": "url|size|extmetadata|mime", "iiurlwidth": 1280})
    p = next(iter(d["query"]["pages"].values())); ii = p["imageinfo"][0]; em = ii.get("extmetadata") or {}
    open(os.path.join(out, k + ".jpg"), "wb").write(urllib.request.urlopen(urllib.request.Request(ii["thumburl"], headers=UA), timeout=60).read())
    meta[k] = {"title": title, "artist": strip((em.get("Artist") or {}).get("value"))[:80], "license": strip((em.get("LicenseShortName") or {}).get("value")),
               "page": ii.get("descriptionurl"), "file": k + ".jpg"}
    print(k, meta[k]["license"], meta[k]["artist"][:40]); json.dump(meta, open(meta_p, "w", encoding="utf-8"), ensure_ascii=False, indent=1); time.sleep(12)
json.dump(meta, open(meta_p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
