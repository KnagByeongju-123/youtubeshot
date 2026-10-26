"""장문 다큐 사진 후보를 여러 곳에서 받기 (자유 이용 사진만, 출처·저작권 기록)
  python 장문/사진_여러곳.py <주제 사진_찾기.py> <저장폴더> [컷들] [--곳 commons,openverse,loc]

찾는 곳 (사용자 규칙: 위키미디어에서 모자라면 다른 곳에서도 — 프로그램 doc_add_photos 의 '보충 검색'과 같은 생각)
  commons   위키미디어 공용 (../안티키테라/사진_찾기.py, 1280px, 요청 사이 쉼)
  openverse Openverse — 플리커·박물관·도서관의 CC 사진 모음 (상업 이용·수정 가능한 것만: CC0·PDM·BY·BY-SA)
  loc       미국 의회도서관 사진 (권리 '알려진 제한 없음'만)
결과: <저장폴더>/<컷>_<n>.jpg (commons), <컷>_o<n>.jpg (openverse), <컷>_l<n>.jpg (loc) + 후보.json
      후보.json 에 source 칸(Wikimedia Commons / Flickr via Openverse / Library of Congress)을 적어 화면 출처 줄에 씀
주제 사진_찾기.py 의 Q(컷 → 검색어)를 그대로 씀. 이미 받은 컷의 같은 곳 후보는 건너뜀"""
import importlib.util
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

UA = {"User-Agent": "youtubeshot-doc/1.0 (educational documentary; contact via github KnagByeongju-123)"}
HERE = os.path.dirname(os.path.abspath(__file__))


def get(url, js=True, tries=4):
    for k in range(tries):
        try:
            r = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40).read()
            return json.loads(r) if js else r
        except Exception as e:
            if k == tries - 1:
                print("   실패", url[:80], e)
            time.sleep(10 * (k + 1))
    return None


def openverse(q, n=4):
    d = get("https://api.openverse.org/v1/images/?" + urllib.parse.urlencode(
        {"q": q, "page_size": 12, "license_type": "commercial,modification", "mature": "false"})) or {}
    out = []
    for r in d.get("results", []):
        if (r.get("width") or 1000) < 600:
            continue
        url = r["url"]
        if "staticflickr.com" in url:                                  # 플리커는 큰 크기(_b, 1024px)부터
            url = re.sub(r"(_[a-z])?\.jpg$", "_b.jpg", url)
        out.append({"url": url, "fallback": r["url"], "title": r.get("title") or q, "artist": (r.get("creator") or "")[:80],
                    "license": f"CC {r['license'].upper()} {r.get('license_version') or ''}".replace("CC CC0", "CC0").replace("CC PDM", "Public domain").strip(),
                    "page": r.get("foreign_landing_url") or r.get("url"), "source": f"{(r.get('source') or 'openverse').title()} via Openverse"})
        if len(out) >= n:
            break
    return out


def loc(q, n=3):
    d = get("https://www.loc.gov/photos/?" + urllib.parse.urlencode({"q": q, "fo": "json", "c": 15})) or {}
    out = []
    for r in d.get("results", []):
        rights = " ".join(r.get("rights_advisory") or r.get("rights") or []) if isinstance(r.get("rights_advisory") or r.get("rights"), list) else str(r.get("rights_advisory") or r.get("rights") or "")
        imgs = [u for u in (r.get("image_url") or []) if u.split("#")[0].endswith((".jpg", ".jpeg"))]
        if not imgs or not re.search(r"no known restrictions|public domain", rights, re.I):
            continue
        out.append({"url": imgs[-1].split("#")[0], "title": r.get("title") or q, "artist": "Library of Congress",
                    "license": "No known restrictions", "page": r.get("url") or r.get("id"), "source": "Library of Congress"})
        if len(out) >= n:
            break
    return out


def main():
    a = [x for x in sys.argv[1:]]
    places = ["commons", "openverse", "loc"]
    if "--곳" in a:
        i = a.index("--곳"); places = a[i + 1].split(","); del a[i:i + 2]
    spec = importlib.util.spec_from_file_location("topic_photos", a[0]); T = importlib.util.module_from_spec(spec); spec.loader.exec_module(T)
    F = T.F                                                            # 주제 파일이 고친 위키미디어 찾기(검색어 Q 포함)
    out = a[1]
    only = a[2].split(",") if len(a) > 2 else list(F.Q)
    os.makedirs(out, exist_ok=True)
    meta_p = os.path.join(out, "후보.json")
    if "commons" in places:
        F.main.__globals__["sys"].argv = ["x", out, ",".join(only)]
        F.main()
    meta = json.load(open(meta_p, encoding="utf-8")) if os.path.exists(meta_p) else {}
    for c in only:
        for place, fn, tag in (("openverse", openverse, "o"), ("loc", loc, "l")):
            if place not in places or any(k.startswith(f"{c}_{tag}") for k in meta):
                continue
            got = 0
            for it in fn(F.Q[c]):
                data = get(it["url"], js=False, tries=2) or (get(it["fallback"], js=False, tries=2) if it.get("fallback") else None)
                if not data or len(data) < 20000:
                    continue
                got += 1
                f = os.path.join(out, f"{c}_{tag}{got}.jpg")
                open(f, "wb").write(data)
                meta[f"{c}_{tag}{got}"] = {k: it[k] for k in ("title", "artist", "license", "page", "source")} | {"file": os.path.basename(f)}
                time.sleep(2)
            print(c, place, F.Q[c], "→", got, "장")
            json.dump(meta, open(meta_p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
            time.sleep(2)


if __name__ == "__main__":
    main()
