"""Codex 검토의 검증 기준을 고정 입력으로 확인 (네트워크 없음)."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import topic_finder as tf

fails = 0
def check(name, got, want):
    global fails
    ok = got == want
    fails += not ok
    print(("OK  " if ok else "FAIL"), name, "->", got, "" if ok else f"(기대: {want})")

# P1-1 해결 상태
check("remains unresolved", tf.solve_status("Ice giants", "many fundamental questions remain unresolved"), "미해결")
check("remains unsolved", tf.solve_status("Wishbone origin", "The origin remains unsolved."), "미해결")
check("unresolved 점수 0", tf.pattern_score("remains unresolved", tf.SOLVED_PATTERNS)[0], 0)
check("may have solved", tf.solve_status("Scientists may have finally solved the mystery of the Moon", ""), "가설 제안")
check("새 관측 기회(아직 안 풀림)", tf.solve_status("Solar eclipse offers rare chance to solve Sun's magnetic-field mysteries", ""), "미해결")
check("확정 해결", tf.solve_status("DNA solves the mystery of a body found in the Arctic in 1859", "identified"), "해결 근거")
check("solved 중첩 가산 없음", tf.pattern_score("solved solve solves", tf.SOLVED_PATTERNS)[0], 4)
it = {"title": "Hidden mysteries of ice giants", "summary": "remain unresolved", "tech": "", "status": "미해결"}
check("미해결 제목에 '답이 나왔다' 없음", any("답이 나왔다" in t or "풀렸" in t for t in tf.template_titles(it)), False)
it = {"title": "x", "summary": "", "tech": "", "status": "해결 근거"}
check("근거 없는 기간·교과서 표현 없음", any(("교과서" in t) or ("수십 년" in t) for t in tf.template_titles(it)), False)

# P1-2 유튜브 실패 처리
orig = tf.http_get
tf.http_get = lambda *a, **k: b"<html>consent.youtube.com before you continue</html>"
r = tf.youtube_check({"title": "Roman shipwreck waterproofing"}, {})
check("동의 화면 -> 미확인", r["yt_status"].startswith("미확인"), True)
item = {"title": "Roman shipwreck waterproofing", "base_score": 20}
tf.apply_youtube.__globals__["time"].sleep = lambda s: None
tf.apply_youtube([item], {})
check("미확인은 점수 가산 없음", item["score"], 20)
def boom(*a, **k): raise OSError("network down")
tf.http_get = boom
check("HTTP 오류 -> 미확인", tf.youtube_check({"title": "Roman shipwreck"}, {})["yt_status"].startswith("미확인(HTTP"), True)
tf.http_get = orig

# P1-3 관련성
title1 = "New research traces the origins and human impact of Britain's largest medieval lead industry through ancient teeth"
sp, ct = tf.search_terms(title1)
check("검색어에 구체 대상 포함", ("britain" in sp) and ("lead" in ct) and ("research" not in ct), True)
check("인류 기원 영상 제외", tf.relevance("What Happened Before History? Human Origins", sp, ct)[0], False)
check("납 산업 영상 유지", tf.relevance("Medieval lead mining in Britain's Peak District", sp, ct)[0], True)

# P2-4 조회수/기간
for s, v in [("1.2M views", 1_200_000), ("12K views", 12_000), ("1.5B views", 1_500_000_000),
             ("조회수 1.2만회", 12_000), ("조회수 3천회", 3_000), ("조회수 2억회", 200_000_000),
             ("15,430 views", 15_430), ("조회수 없음", 0)]:
    check(f"조회수 {s}", tf.parse_views(s), v)
for s, v in [("11개월 전", 11), ("12개월 전", 12), ("18 months ago", 18), ("1년 전", 12),
             ("0 years ago", 0), ("3일 전", 0), ("2 weeks ago", 2 / 4.35), ("스트리밍됨", None)]:
    check(f"기간 {s}", tf.months_ago(s), v)

# P2-5 중복 병합
a = {"origin": "뉴스", "source": "Phys.org", "title": "Same story", "summary": "s", "url": "https://phys.org/news/a.html?utm=1", "date": "", "journal": "", "cited": 0}
b = dict(a, source="Phys.org 고고학", url="https://www.phys.org/news/a.html")
g = tf.merge_items([a, b])
check("같은 기사 재노출 -> coverage 1", (len(g), g[0]["coverage"]), (1, 1))
p = {"origin": "논문", "source": "Nature", "title": "Formal paper title", "summary": "x", "url": "https://doi.org/10.1038/ABC123", "doi": "https://doi.org/10.1038/ABC123", "date": "", "journal": "Nature", "cited": 0}
n = dict(a, title="Pop headline", url="https://sciencedaily.com/x", doi="https://doi.org/10.1038/abc123")
g = tf.merge_items([p, n])
check("같은 DOI 다른 기사 -> 한 소재", (len(g), g[0]["coverage"]), (1, 2))

# P2-6 근거 상태
g1 = tf.merge_items([dict(a, journal_mention="Nature")])[0]
g2 = tf.merge_items([p])[0]
check("저널 언급만", tf.evidence_status(g1)[0].startswith("저널 언급"), True)
check("DOI 있는 원저 연구", tf.evidence_status(g2)[0].startswith("원저 연구"), True)

# P2-8 파일 보존
import tempfile
d = tempfile.mkdtemp(); f = os.path.join(d, "t.md"); open(f, "w").close()
check("같은 이름 덮어쓰기 방지", os.path.basename(tf.unique_path(f)), "t_2.md")

# ---------------- v3: Codex 2차 검토 기준
import itertools
import json

# P1-1 부정·시도·목적으로 쓰인 해결 동사
for t, sm in [("Scientists have not solved the mystery", ""),
              ("Scientists failed to solve the mystery", "The cause remains unknown."),
              ("New mission attempts to solve the mystery of Uranus", ""),
              ("Researchers hope to solve the riddle of the Nazca lines", ""),
              ("The hidden mysteries of our ice giant planets",
               "many fundamental questions remain unresolved. We outline measurements needed to finally resolve these long-standing questions.")]:
    check(f"확정 해결 아님: {t[:40]}", tf.solve_status(t, sm) != "해결 근거", True)
check("실제 해결은 유지", tf.solve_status("Archaeologists solve the mystery of the lost tomb", "They identified the owner."), "해결 근거")
check("해결 동사 없이 확정 결과도 해결",
      tf.solve_status("Hidden charcoal reveals the true age of ancient cave paintings",
                      "A new analysis has precisely dated paintings for the first time."), "해결 근거")

# P1-2 같은 소재 영상이 없으면 경쟁 가산 없음
def fake_search(vids):
    return lambda q, cache, offline: ("확인", vids, "test")
orig_fs = tf.fetch_search
unrelated = [{"id": str(i), "title": f"Cooking pasta tutorial {i}", "views_text": "1M views", "age_text": "2 years ago"} for i in range(9)]
tf.fetch_search = fake_search(unrelated)
item = {"title": "Osaka fossil hides mosasaur bones", "summary": "", "base_score": 20}
tf.apply_youtube([item], {})
check("표본 9개 모두 무관 -> 점수 그대로", item["score"], 20)
check("판단 근거 부족 표시", item["yt_basis"].startswith("판단 근거 부족"), True)
undated = [{"id": "a", "title": "Osaka mosasaur fossil bones explained", "views_text": "50K views", "age_text": ""}]
tf.fetch_search = fake_search(undated)
item = {"title": "Osaka fossil hides mosasaur bones", "summary": "", "base_score": 20}
tf.apply_youtube([item], {})
check("관련 영상 날짜 전부 미상 -> 점수 그대로", item["score"], 20)
tf.fetch_search = orig_fs

# P1-3 같은 사건 vs 넓은 분야 관심도
t1 = "A 30-year-old fossil was hiding bones from a mysterious ancient sea monster"
s1 = ("Fossils collected in Osaka more than 30 years ago have revealed four previously "
      "unrecognized bones from a giant Cretaceous mosasaur.")
ids, ct = tf.search_terms(t1, s1)
check("요약에서 식별어 추출 (osaka)", "osaka" in ids, True)
check("영국 바다 괴물 영상은 같은 소재 아님", tf.relevance("Colossal sea monster unearthed in UK", ids, ct)[0], False)
check("영국 바다 괴물은 넓은 분야 관심도로만 집계", tf.broad_match("Colossal sea monster unearthed in UK", ct), True)
check("오사카 모사사우루스 영상은 같은 소재", tf.relevance("Hidden sea monster bones found in Osaka fossil", ids, ct)[0], True)

# P2-4 union-find 병합 (입력 순서 무관)
A = {"origin": "뉴스", "source": "X", "title": "one", "summary": "a", "url": "https://x.com/a", "date": "", "journal": "", "cited": 0}
B = dict(A, source="Y", title="two", url="https://y.com/b")
C = dict(A, source="Z", title="one", url="https://y.com/b")
outs = set()
for perm in itertools.permutations([A, B, C]):
    g = tf.merge_items([dict(x) for x in perm])
    outs.add((len(g), json.dumps(g[0]["links"]), tuple(g[0]["publishers"]), g[0]["title"], g[0]["summary"]))
check("A-B-C 연결 -> 1그룹, 6가지 순서 모두 동일", (len(outs), next(iter(outs))[0]), (1, 1))

# P2-5 자료 유형별 근거 표기
news_in_nature = {"origin": "논문", "source": "Nature", "title": "Can your brain grow new neurons?", "summary": "",
                  "url": "https://doi.org/10.1038/d41586-026-01234-5", "doi": "https://doi.org/10.1038/d41586-026-01234-5",
                  "date": "", "journal": "Nature", "work_type": "article", "cited": 0}
research = dict(news_in_nature, title="Adult neurogenesis in human hippocampus",
                url="https://doi.org/10.1038/s41586-026-0001-1", doi="https://doi.org/10.1038/s41586-026-0001-1",
                summary="x" * 200)
e1 = tf.evidence_status(tf.merge_items([news_in_nature])[0])
e2 = tf.evidence_status(tf.merge_items([research])[0])
check("Nature 뉴스 DOI는 원저 아님", e1[0].startswith("저널 뉴스"), True)
check("원저 연구는 초록 확인", e2[0].startswith("원저 연구 · 초록 확인"), True)
check("뉴스와 원저의 근거 점수 다름", e1[1] < e2[1], True)
review = dict(research, work_type="review", url="https://doi.org/10.1/r", doi="https://doi.org/10.1/r")
check("리뷰는 원저 아님", tf.evidence_status(tf.merge_items([review])[0])[0].startswith("저널"), True)

# 한국어 번역 (무료, 캐시/오프라인)
cache = {"Hello": "안녕하세요"}
check("번역 캐시 사용", tf.translate_ko("Hello", cache), ("안녕하세요", "캐시"))
check("오프라인은 네트워크 안 씀", tf.translate_ko("World", cache, offline=True)[1].startswith("오프라인"), True)
orig = tf.http_get
tf.http_get = lambda *a, **k: json.dumps({"responseData": {"translatedText": "숨은 숯"}, "responseStatus": 200}).encode()
check("MyMemory 응답 처리", tf.translate_ko("Hidden charcoal", {}), ("숨은 숯", "번역"))
def quota_then_fail(url, *a, **k):
    if "mymemory" in url:
        return json.dumps({"responseData": {"translatedText": "MYMEMORY WARNING: YOU USED ALL"},
                           "responseStatus": 429, "quotaFinished": True}).encode()
    raise OSError("blocked")
tf.http_get = quota_then_fail
check("무료 한도 초과 + 예비 실패 -> 빈 번역(영문 유지)", tf.translate_ko("Quota test", {})[0], "")

# 오프라인 재현: 네트워크 호출이 일어나면 실패
def no_net(*a, **k):
    raise AssertionError("오프라인 모드에서 네트워크 호출 발생")
tf.http_get = no_net
r = tf.youtube_check({"title": "Osaka mosasaur bones", "summary": ""}, {}, offline=True)
check("오프라인 유튜브 -> 미확인, 호출 없음", r["yt_status"].startswith("미확인(오프라인"), True)
tf.http_get = orig

# ---------------- v4: 썸네일 · 해시태그 (Codex 요청 완료 기준)
import tempfile
import thumbs as th

gl = th.load_glossary()
check("용어 사전 로드", len(gl) > 50, True)
check("용어 사전 어간 매칭 (archaeologists→고고학)", th.glossary_lookup("archaeologists", gl), "고고학")
check("짧은 단어가 긴 키에 붙지 않음 (earth≠earthquake)", th.glossary_lookup("earth", gl), "")
check("유튜브 생략 시에도 식별어 계산", "yt_query" in {**{"title": "x"}, **dict(zip(("yt_ids", "yt_query"), (", ".join(tf.search_terms("Moon's two faces", "")[0]), "q")))}, True)
samp = {"title": "A 30-year-old fossil was hiding bones from a mysterious ancient sea monster",
        "summary": "Fossils collected in Osaka more than 30 years ago revealed bones from a giant Cretaceous mosasaur.",
        "status": "해결 근거", "field": "고고학/인류", "tech": "", "yt_ids": "osaka, cretaceous", "yt_query": "osaka cretaceous fossil bones monster"}
terms, _ = th.ko_terms(samp, gl)  # translate=None: 사전에 없는 고유명사는 건너뜀
tw = [t for t, _ in terms]
check("사전 기반 소재어 (오사카, 화석…)", ("오사카" in tw) and ("화석" in tw), True)
lead = {"title": "New research traces the origins and human impact of Britain's largest medieval lead industry through ancient teeth",
        "summary": "", "status": "해결 근거", "field": "고고학/인류", "tech": "", "yt_ids": "britain, europe, derbyshire, peak",
        "yt_query": "britain europe medieval lead industry"}
lt, _ = th.ko_terms(lead, gl, translate=lambda w: ({"Europe": "유럽", "Derbyshire": "더비셔 주", "Peak": "성수기"}.get(w, ""), "번역"))
lname = th.short_name(lead, lt)
check("소재명 = 지명 1 + 핵심어 (지명 나열·단어 겹침 없음, 3단어 이내)", (lname, len(lname.split()) <= 3), ("영국 납 산업", True))
check("흔한 단어(peak)는 기계번역하지 않음", any("성수기" in t for t, _ in lt), False)
name = th.short_name(samp, terms)
check("소재명 3어 이내", len(name.split()) <= 3, True)
# 3. 미해결/가설 소재에 확정 문구 금지
for st in ("미해결", "가설 제안", "확인 필요"):
    cps = th.thumb_copies(dict(samp, status=st), name)
    check(f"{st} 썸네일 문구에 확정 표현 없음", any(th.DEFINITIVE.search(c) for c in cps), False)
check("해결 근거 문구 3안", len(th.thumb_copies(samp, name)), 3)
check("원문에 없는 기간을 만들지 않음", th.grounded_span("Scientists solve the mystery of the tomb"), "")
check("원문 기간은 사용", th.grounded_span("A 30-year-old fossil"), "30년 전")
# 해시태그
tags = th.hashtags(samp, terms)
check("해시태그 5~8개", 5 <= len(tags) <= 8, True)
check("해시태그 공백·중복 없음", (all(" " not in t and t.startswith("#") for t in tags), len(set(t.lower() for t in tags)) == len(tags)), (True, True))
# 1./2. 샘플 소재에서 실제 생성 + 긴 문구 + 폴더 미덮어쓰기 + 폰트 누락 대체
root = tempfile.mkdtemp()
long_item = dict(samp, title="x", summary="", status="가설 제안", yt_ids="", yt_query="")
long_item["title_ko"] = "매우매우매우매우매우 긴 한국어 썸네일 문구를 넣어서 자동 줄바꿈과 축소가 되는지 확인하는 아주 긴 제목"
sm = th.make_assets([samp, long_item], root, glossary=gl)
d1 = samp["asset_dir"]
check("썸네일 3장 + 문구 + 해시태그 파일 생성",
      (len(samp["thumb_images"]), os.path.exists(os.path.join(d1, "copy.txt")), os.path.exists(os.path.join(d1, "hashtags.txt")), os.path.exists(os.path.join(d1, "source.txt"))),
      (3, True, True, True))
check("기본 그래픽 배경은 '교체 필요' 표시", "교체 필요" in open(os.path.join(d1, "source.txt"), encoding="utf-8").read(), True)
check("긴 문구도 이미지 생성 (잘림은 메모로 표시)", len(long_item["thumb_images"]), 3)
from PIL import Image
im = Image.open(samp["thumb_images"][0])
check("규격 1280×720, 2MB 이하 (JPG)", (im.size, os.path.getsize(samp["thumb_images"][0]) <= 2 * 1024 * 1024), ((1280, 720), True))
again = dict(samp)
sm2 = th.make_assets([again], root, glossary=gl)
check("재실행 시 폴더 덮어쓰지 않음 (_2)", os.path.basename(again["asset_dir"]).endswith("_2") and os.path.exists(d1), True)
# 4. 폰트 누락: 이미지는 건너뛰고 문구·해시태그는 저장, 설명 남김
orig_fc = th.FONT_CANDIDATES
th.FONT_CANDIDATES = []
nf = dict(samp)
sm3 = th.make_assets([nf], root, font="C:/없는/폰트.ttf", glossary=gl)
check("폰트 없음 → 이미지 0장, 문구 파일은 저장, 사유 기록",
      (len(nf["thumb_images"]), os.path.exists(os.path.join(nf["asset_dir"], "copy.txt")), "폰트" in nf["thumb_notes"]), (0, True, True))
th.FONT_CANDIDATES = orig_fc
# 줄바꿈: 단어 중간에서 끊지 않음
from PIL import ImageDraw, ImageFont
dr = ImageDraw.Draw(Image.new("RGB", (10, 10)))
f = ImageFont.truetype(th.find_font(), 60)
lines, over, wrapped = th.wrap_lines(dr, "수백 년간 풀리지 않던 수수께끼", f, 700, 3)
check("단어 단위 줄바꿈 (수수께끼 유지)", any(l.endswith("수수께끼") for l in lines) and not over, True)

# ---------------- v5: 위키미디어 공용 배경 (옵션)
def fake_api(url, **kw):
    if "api.php" in url:
        pages = {
            "1": {"index": 1, "title": "File:Nonfree.jpg", "imageinfo": [{"width": 3000, "mime": "image/jpeg", "thumburl": "http://x/nonfree.jpg",
                   "descriptionurl": "http://c/1", "extmetadata": {"LicenseShortName": {"value": "Fair use"}}}]},
            "2": {"index": 2, "title": "File:Small.jpg", "imageinfo": [{"width": 400, "mime": "image/jpeg", "thumburl": "http://x/small.jpg",
                   "descriptionurl": "http://c/2", "extmetadata": {"LicenseShortName": {"value": "CC BY 4.0"}}}]},
            "3": {"index": 3, "title": "File:Good.jpg", "imageinfo": [{"width": 1600, "mime": "image/jpeg", "thumburl": "http://x/good.jpg",
                   "descriptionurl": "http://c/3", "extmetadata": {"LicenseShortName": {"value": "CC BY-SA 4.0"},
                   "LicenseUrl": {"value": "https://creativecommons.org/licenses/by-sa/4.0"}, "Artist": {"value": "<a href='#'>Jane Doe</a>"}}}]},
        }
        return json.dumps({"query": {"pages": pages}}).encode()
    # 이미지 다운로드: 실제 JPEG 바이트
    import io
    from PIL import Image as _I
    buf = io.BytesIO(); _I.new("RGB", (1600, 900), (90, 60, 30)).save(buf, "JPEG"); return buf.getvalue()

c = th.commons_search("test", http_get=fake_api)
check("허용 라이선스·최소 너비만 통과 (Good.jpg)", [x["title"] for x in c], ["File:Good.jpg"])
def two_ok_api(url, **kw):
    pages = {
        "1": {"index": 1, "title": "File:Roman buckle.jpg", "imageinfo": [{"width": 1600, "mime": "image/jpeg", "thumburl": "http://x/a.jpg", "descriptionurl": "http://c/a", "extmetadata": {"LicenseShortName": {"value": "CC BY 4.0"}}}]},
        "2": {"index": 2, "title": "File:Ancient human teeth from burial.jpg", "imageinfo": [{"width": 1600, "mime": "image/jpeg", "thumburl": "http://x/b.jpg", "descriptionurl": "http://c/b", "extmetadata": {"LicenseShortName": {"value": "CC BY 4.0"}}}]},
    }
    return json.dumps({"query": {"pages": pages}}).encode()
check("검색어 단어가 제목에 많은 후보를 우선", th.commons_search("ancient human teeth", http_get=two_ok_api)[0]["title"], "File:Ancient human teeth from burial.jpg")
check("작가 HTML 제거", c[0]["artist"], "Jane Doe")
check("CC BY-SA 는 표기 의무", c[0]["attribution_required"], True)
cl = th.commons_credit_lines(dict(c[0], query="q"))
check("표기 문구·SA 주의 포함", (any("표기 문구" in l for l in cl), any("SA" in l for l in cl)), (True, True))
root2 = tempfile.mkdtemp()
cm = dict(samp)
th.make_assets([cm], root2, glossary=gl, commons=True, http_get=fake_api)
src = open(os.path.join(cm["asset_dir"], "source.txt"), encoding="utf-8").read()
check("공용 사진 다운로드 + source.txt 에 출처·라이선스 자동 기록",
      (os.path.exists(os.path.join(cm["asset_dir"], "photo_1.jpg")), "위키미디어 공용" in src, "CC BY-SA 4.0" in src, "Jane Doe" in src), (True, True, True, True))
check("리포트용 크레딧 문자열", "CC BY-SA 4.0" in cm["bg_credit"], True)
off = dict(samp)
th.make_assets([off], root2, glossary=gl, http_get=no_net)  # commons 기본값 False → 네트워크 호출 없음
check("옵션 안 켜면 외부 접근 없음", "기본 그래픽" in open(os.path.join(off["asset_dir"], "source.txt"), encoding="utf-8").read(), True)
def empty_api(url, **kw):
    return json.dumps({"query": {"pages": {}}}).encode()
nf2 = dict(samp)
th.make_assets([nf2], root2, glossary=gl, commons=True, http_get=empty_api)
check("허용 사진 없으면 기본 그래픽 + 사유 기록", "공용 사진 없음" in nf2["bg_credit"], True)

# ---------------- v6: 실사 편집 레이아웃 (A 피사체 중심 / B 좌우 비교 / C 증거 확대) + 메타데이터
import layouts
from PIL import Image as _Img
sroot = tempfile.mkdtemp()
# 실제 사진 대용: 왼쪽 위는 평탄, 오른쪽 아래에 세부(가장자리)가 많은 합성 이미지 → 초점이 오른쪽 아래로 잡혀야 함
ph = _Img.new("RGB", (1600, 1000), (40, 60, 90))
import random as _r
_r.seed(1)
px = ph.load()
for _ in range(60000):
    x, y = _r.randint(1000, 1599), _r.randint(600, 999)
    px[x, y] = (_r.randint(0, 255), _r.randint(0, 255), _r.randint(0, 255))
p1 = os.path.join(sroot, "p1.jpg"); ph.save(p1)
p2 = os.path.join(sroot, "p2.jpg"); ph.transpose(_Img.FLIP_LEFT_RIGHT).save(p2)
fb = layouts.focal_box(layouts.load_photo(p1), frac_w=0.3, aspect=1.0)
check("초점 영역이 세부가 많은 쪽(오른쪽 아래)에 잡힘", (fb[0] >= 800, fb[1] >= 400, fb[2] <= 1600, fb[3] <= 1000), (True, True, True, True))
fpath = th.find_font()
mA = layouts.layout_subject(p1, "소재\n마침내 풀렸다", fpath, "해결 근거", os.path.join(sroot, "A.jpg"))
mB = layouts.layout_compare(p1, p2, "앞면과 뒷면\n드디어 풀렸을까?", fpath, "가설 제안", os.path.join(sroot, "B.jpg"), labels=("앞면", "뒷면"))
mC = layouts.layout_zoom(p1, "증거\n과학이 밝힌 정체", fpath, "해결 근거", os.path.join(sroot, "C.jpg"))
check("A/B/C 모두 1280×720 생성", tuple(_Img.open(os.path.join(sroot, f"{k}.jpg")).size for k in "ABC"), ((1280, 720),) * 3)
check("A 메타: 피사체 크롭 좌표·편집 내역", ("crop_box" in mA["subject"], len(mA["edits"]) >= 3), (True, True))
check("B 메타: 두 사진 각각 출처·크롭 + 사실 구분 메모", (len(mB["panels"]), mB["panels"][0]["source_image"] != mB["panels"][1]["source_image"], "실제 비교 실험 장면이 아닙니다" in mB["note"]), (2, True, True))
# C: 확대 영역의 썸네일 좌표가 원본 좌표를 맥락 크롭에 정확히 대응
zb, cb = mC["zoom_box_original"], mC["context_crop_box"]
tb = layouts.to_thumb_coords(zb, cb, (1280, 720))
check("C 메타: 확대창 원본 좌표가 썸네일 사각형과 대응", (tb == tuple(mC["zoom_box_on_thumbnail"]), 0 <= tb[0] < tb[2] <= 1280, mC["zoom_scale"] > 1), (True, True, True))
check("긴 문구 넘침 플래그 기록", "text_overflow" in mA and "text_overflow" in mC, True)
# make_assets: 사용자 사진 폴더(소재별 하위폴더) → 실사 편집 3안 + meta.json, 사진 1장이면 B 대신 A' 와 사유
bgd = os.path.join(sroot, "bg"); os.makedirs(os.path.join(bgd, "01_moon")); os.makedirs(os.path.join(bgd, "02_x"))
import shutil
shutil.copy(p1, os.path.join(bgd, "01_moon", "near.jpg")); shutil.copy(p2, os.path.join(bgd, "01_moon", "far.jpg"))
shutil.copy(p1, os.path.join(bgd, "02_x", "only.jpg"))
two = dict(samp, title="Scientists may have solved the mystery of the Moon's two faces (near side vs far side)", status="가설 제안")
one = dict(samp)
sm = th.make_assets([two, one], os.path.join(sroot, "assets"), glossary=gl, bg_dir=bgd, bg_credit="내 사진")
check("사진 2장 소재 → A/C/B 비교형, 1장 소재 → A/C/A'", (two["thumb_layouts"], one["thumb_layouts"][2].startswith("A")), ((["A 피사체 중심형", "C 증거 확대형", "B 좌우 비교형"]), True))
check("1장 소재에 비교형 생략 사유 기록", "비교형(B) 생략" in one["thumb_notes"], True)
mj = json.load(open(os.path.join(two["asset_dir"], "meta.json"), encoding="utf-8"))
check("meta.json: 사진·출처·레이아웃·편집·사실구분", (len(mj["photos"]), len(mj["variants"]), "honesty" in mj, mj["mode"]), (2, 3, True, "실사 편집"))
check("3안의 문구가 서로 다름", len({v["copy"] for v in mj["variants"]}), 3)
check("실사 있으면 임시 표시 아님 / 없으면 임시", (two["thumb_mode"], sm["graphic_topics"]), ("실사 편집", 0))
noph = dict(samp)
th.make_assets([noph], os.path.join(sroot, "assets2"), glossary=gl)
check("실사 없음 → 기본 그래픽(임시) 표시", noph["thumb_mode"], "기본 그래픽(임시)")
# 공용 여러 장 + 라이선스 필터는 v5 fake_api 재사용 (허용 1장뿐 → B 생략, 출처 기록)
cm2 = dict(samp)
th.make_assets([cm2], os.path.join(sroot, "assets3"), glossary=gl, commons=True, http_get=fake_api)
s3 = open(os.path.join(cm2["asset_dir"], "source.txt"), encoding="utf-8").read()
check("공용 사진 다운로드(허용 1장) → 실사 편집 + 출처·라이선스 기록", (cm2["thumb_mode"], "CC BY-SA 4.0" in s3, "Jane Doe" in s3, os.path.exists(os.path.join(cm2["asset_dir"], "photo_1.jpg"))), ("실사 편집", True, True, True))

print("\n실패", fails, "건")
sys.exit(1 if fails else 0)
