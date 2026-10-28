"""실제 사진 후보 찾기 — 위키미디어 공용(Wikimedia Commons)에서 자유 이용 허락이 분명한 사진만 골라 내려받음
python 사진_찾기.py <찾을목록.json> <저장폴더> [후보수=4]
  찾을목록.json: {"c05": "petrous bone", "c32": "Denisova Cave", ...}  (영어 검색어가 잘 찾아짐)
  - 허락: 퍼블릭 도메인·CC0·CC BY·CC BY-SA 만 (NC·ND·저작권 표시 없는 사진은 버림)
  - 결과: <저장폴더>/<컷>_<번호>.jpg + 후보.json (컷마다 [{file, title, license, artist, page, credit}])
    credit = 오른쪽 위 설명과 설명란에 그대로 쓸 출처 한 줄 ('작가 / CC BY-SA 4.0 / 위키미디어 공용')
  - 고른 뒤 회차 .py 의 PHOTOS 에 {"c05": {"file": ..., "credit": ...}} 로 적음 (그 컷은 AI 그림 대신 사진, 누끼 안 씀)
  - 후보 모음표: <저장폴더>/후보_모음.jpg (컷마다 한 줄)"""
import html
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

API = "https://commons.wikimedia.org/w/api.php"
UA = "youtubeshot-doc/1.0 (science documentary; photo search with license check)"
OK_LIC = re.compile(r"^(public domain|pd|cc0|cc by(-sa)? ?\d|cc-by(-sa)?-\d)", re.I)


def get(url, tries=3):
    for k in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            return urllib.request.urlopen(req, timeout=60).read()
        except Exception:
            if k + 1 == tries:
                raise
            time.sleep(2 * (k + 1))


def plain(s):
    s = re.sub(r"<[^>]+>", "", html.unescape(str(s or ""))).strip()
    return re.sub(r"\s+", " ", s)[:80]


def search(q, n):
    p = {"action": "query", "format": "json", "generator": "search", "gsrnamespace": "6", "gsrsearch": f"{q} filetype:bitmap",
         "gsrlimit": str(n * 4), "prop": "imageinfo", "iiprop": "url|extmetadata|size", "iiurlwidth": "1600"}
    d = json.loads(get(API + "?" + urllib.parse.urlencode(p)))
    pages = sorted((d.get("query") or {}).get("pages", {}).values(), key=lambda x: x.get("index", 99))
    out = []
    for pg in pages:
        ii = (pg.get("imageinfo") or [{}])[0]
        m = ii.get("extmetadata") or {}
        lic = plain((m.get("LicenseShortName") or {}).get("value"))
        if not OK_LIC.match(lic) or ii.get("width", 0) < 800:
            continue
        artist = plain((m.get("Artist") or {}).get("value")) or "작가 미상"
        out.append({"title": pg["title"], "license": lic, "artist": artist, "page": ii.get("descriptionurl", ""),
                    "url": ii.get("thumburl") or ii.get("url"), "credit": f"{artist} / {lic} / 위키미디어 공용"})
        if len(out) >= n:
            break
    return out


def main(a):
    if len(a) < 2:
        print(__doc__)
        return 2
    want = json.load(open(a[0], encoding="utf-8"))
    out = a[1]
    n = int(a[2]) if len(a) > 2 else 4
    os.makedirs(out, exist_ok=True)
    res = {}
    for cid, q in want.items():
        try:
            cands = search(q, n)
        except Exception as e:
            print("ERR", cid, e)
            continue
        got = []
        for k, c in enumerate(cands):
            f = os.path.join(out, f"{cid}_{k + 1}.jpg")
            try:
                from PIL import Image
                import io
                Image.open(io.BytesIO(get(c["url"]))).convert("RGB").save(f, quality=92)
            except Exception as e:
                print("  내려받기 실패", c["title"], e)
                continue
            c["file"] = f
            got.append(c)
        res[cid] = got
        print(cid, q, "→", len(got), "장")
    json.dump(res, open(os.path.join(out, "후보.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    try:                                       # 모음표: 컷마다 한 줄, 후보 번호 표시
        from PIL import Image, ImageDraw
        rows = [(cid, c) for cid, c in res.items() if c]
        W = 360
        sheet = Image.new("RGB", (W * n, 220 * len(rows)), "black")
        d = ImageDraw.Draw(sheet)
        for r, (cid, cs) in enumerate(rows):
            for k, c in enumerate(cs):
                im = Image.open(c["file"])
                im.thumbnail((W, 200))
                sheet.paste(im, (k * W, r * 220))
                d.rectangle([k * W, r * 220, k * W + 70, r * 220 + 18], fill="black")
                d.text((k * W + 3, r * 220 + 3), f"{cid}_{k + 1}", fill="white")
        sheet.save(os.path.join(out, "후보_모음.jpg"), quality=85)
    except Exception as e:
        print("모음표 실패", e)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
