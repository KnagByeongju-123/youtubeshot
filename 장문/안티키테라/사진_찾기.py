"""위키미디어 공용(Commons)에서 컷마다 실제 사진 후보 받기 (자유 이용 사진만, 출처·저작권 기록)

  python 사진_찾기.py <저장폴더> [컷들]      → <저장폴더>/<컷>_<n>.jpg + 후보.json (제목·작가·라이선스·주소)
"""
import json, os, re, sys, time, urllib.parse, urllib.request

UA = {"User-Agent": "youtubeshot-doc/1.0 (educational documentary; contact via github KnagByeongju-123)"}
Q = {   # 컷 → 검색어 (영어, Commons 파일 검색)
    "c01": "Antikythera Fragment A", "c04": "Antikythera mechanism National Archaeological Museum display",
    "c05": "sponge divers", "c06": "Antikythera wreck", "c08": "Antikythera 1901",
    "c09": "National Archaeological Museum Athens", "c10": "Valerios Stais", "c11": "Antikythera mechanism gear close up",
    "c13": "Derek de Solla Price", "c15": "Antikythera mechanism reconstruction model", "c17": "Antikythera mechanism X-ray CT",
    "c18": "Antikythera mechanism inscription", "c20": "Antikythera mechanism frontview",
    "c22": "Antikythera mechanism pin and slot gears", "c23": "Antikythera mechanism back view",
    "c24": "ancient Greek vase runners Panathenaic amphora", "c26": "Archimedes painting", "c28": "Hipparchus astronomer",
    "c32": "Prague astronomical clock Orloj", "c34": "Antikythera shipwreck", "c36": "Antikythera island",
    "c06b": "Antikythera Ephebe", "c06c": "Antikythera philosopher head bronze",
}


def api(params):
    url = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode({**params, "format": "json"})
    for k in range(4):
        try:
            return json.load(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30))
        except Exception as e:
            time.sleep(3 * (k + 1))
    return {}


def strip(h):
    return re.sub(r"<[^>]+>", "", h or "").strip()


def main():
    out = sys.argv[1]
    only = sys.argv[2].split(",") if len(sys.argv) > 2 else list(Q)
    os.makedirs(out, exist_ok=True)
    meta_p = os.path.join(out, "후보.json")
    meta = json.load(open(meta_p, encoding="utf-8")) if os.path.exists(meta_p) else {}
    for c in only:
        d = api({"action": "query", "generator": "search", "gsrsearch": Q[c] + " filetype:bitmap", "gsrnamespace": 6, "gsrlimit": 8,
                 "prop": "imageinfo", "iiprop": "url|size|extmetadata|mime", "iiurlwidth": 1280})
        pages = sorted((d.get("query") or {}).get("pages", {}).values(), key=lambda p: p.get("index", 99))
        n = 0
        for p in pages:
            ii = (p.get("imageinfo") or [{}])[0]
            if ii.get("mime") not in ("image/jpeg", "image/png", "image/webp") or ii.get("width", 0) < 900:
                continue
            em = ii.get("extmetadata") or {}
            lic = strip((em.get("LicenseShortName") or {}).get("value"))
            if not re.search(r"public domain|cc0|cc by|cc-by|pd", lic, re.I) or re.search(r"nd|nc", lic.replace("CC BY-SA", ""), re.I) and "ND" in lic.upper():
                continue
            n += 1
            f = os.path.join(out, f"{c}_{n}.jpg")
            try:
                data = urllib.request.urlopen(urllib.request.Request(ii["thumburl"], headers=UA), timeout=60).read()
                open(f, "wb").write(data)
            except Exception as e:
                print("  받기 실패", c, e)
                n -= 1
                continue
            meta[f"{c}_{n}"] = {"title": p["title"], "artist": strip((em.get("Artist") or {}).get("value"))[:80], "license": lic,
                                "page": ii.get("descriptionurl"), "file": os.path.basename(f)}
            time.sleep(4)
            if n >= 4:
                break
        print(c, Q[c], "→", n, "장")
        json.dump(meta, open(meta_p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        time.sleep(1)


if __name__ == "__main__":
    main()
