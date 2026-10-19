"""
유튜브 과학 미스터리 다큐(약 10분) 소재 탐색기
- 세계 주요 과학저널 + 과학/고고학 뉴스에서 "풀리지 않던 수수께끼"류 연구를 찾고
- 해결 상태(해결 근거 / 가설 제안 / 미해결 / 확인 필요)를 구분하고
- 내 채널에 이미 다룬 주제는 빼고
- 유튜브 검색 표본으로 수요(유사 영상 조회수)와 경쟁(최근 12개월 유사 영상 수)을 확인해
- 인기 가능성이 높은 소재를 골라 상태에 맞는 훅 제목 초안과 함께 리포트로 저장합니다.

필요: Python 3.9+ (표준 라이브러리만 사용)
비용: 무료. 유료 API 를 쓰지 않습니다 (OpenAlex, RSS, 유튜브 공개 페이지,
      무료 번역 MyMemory → 실패 시 Google 무료 엔드포인트). 번역은 output/translate_cache.json 에 캐시.
      훅 제목은 규칙 기반 틀로 만들고, 채널 중복은 channel_exclude.txt 키워드로 판별합니다.

사용 예
  python topic_finder.py                          # 기본: 최근 180일, 20개 선정
  python topic_finder.py --days 365 --pick 30     # 1년치에서 30개
  python topic_finder.py --no-youtube             # 유튜브 확인 생략 (빠름)
  python topic_finder.py --bg-dir 내사진폴더       # 내 사진을 썸네일 배경으로
  python topic_finder.py --bg-commons             # 위키미디어 공용 자유 이용 사진을 배경으로 (켤 때만, 출처 자동 기록)
  python topic_finder.py --from-raw output/raw_날짜.json
                                                  # 저장본으로 오프라인 재현 (네트워크 사용 안 함)

결과: output/topics_날짜.md (리포트, 한국어 번역 포함), .csv (엑셀용), raw_날짜.json (재현용 저장본)
"""

import argparse
import csv
import json
import math
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from html import unescape

HERE = os.path.dirname(os.path.abspath(__file__))
CHANNEL_URL = "https://www.youtube.com/@dream_art_kang"
EXCLUDE_FILE = os.path.join(HERE, "channel_exclude.txt")
UA_BOT = "ScienceMysteryTopicFinder/3.0 (personal research script)"
UA_WEB = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"

# 세계 주요 저널 (ISSN) - OpenAlex 로 검색
JOURNALS = {
    "0028-0836": "Nature", "0036-8075": "Science", "0027-8424": "PNAS",
    "2375-2548": "Science Advances", "2041-1723": "Nature Communications",
    "0092-8674": "Cell", "0960-9822": "Current Biology",
    "2397-3374": "Nature Human Behaviour", "2397-334X": "Nature Ecology & Evolution",
    "2397-3366": "Nature Astronomy", "1752-0894": "Nature Geoscience",
    "0305-4403": "Journal of Archaeological Science", "0003-598X": "Antiquity",
    "0047-2484": "Journal of Human Evolution", "0003-813X": "Archaeometry",
}
JOURNAL_SEARCHES = [
    "mystery", "enigma", "puzzle", "long-standing question", "unexplained",
    "decipher", "solves", "resolves", "origin of", "ancient DNA",
    "archaeological", "lost civilization",
]
# --mode 발견: 수수께끼가 아니어도 '새로 밝혀진 사실'(첫 증거·가장 오래된·상식을 뒤집은 발견)을 찾음
DISCOVERY_SEARCHES = [
    "discovery", "first evidence", "earliest", "oldest known", "new species", "unexpected",
    "surprising", "overturns", "first ever", "never before seen", "solves", "resolves",
]

# 과학/고고학 뉴스 RSS ("발행처 세부" 형식: 같은 발행처의 여러 피드는 독립 보도로 세지 않음)
NEWS_FEEDS = {
    "Phys.org 고고학": "https://phys.org/rss-feed/science-news/archaeology-fossils/",
    "Phys.org": "https://phys.org/rss-feed/",
    "ScienceDaily 고고학": "https://www.sciencedaily.com/rss/fossils_ruins/archaeology.xml",
    "ScienceDaily 화석": "https://www.sciencedaily.com/rss/fossils_ruins.xml",
    "ScienceDaily": "https://www.sciencedaily.com/rss/all.xml",
    "Science News": "https://www.science.org/rss/news_current.xml",
    "Nature": "https://www.nature.com/nature.rss",
    "Smithsonian": "https://www.smithsonianmag.com/rss/science-nature/",
    "New Scientist 인류": "https://www.newscientist.com/subject/humans/feed/",
    "Live Science": "https://www.livescience.com/feeds/all",
    "Science Alert": "https://www.sciencealert.com/feed",
    "Popular Science": "https://www.popsci.com/feed/",
}

# 신호 사전: (정규식, 가중치). 단어 경계(\b)로 매칭해서 "unsolved" 가 "solved" 로 잡히지 않게 함.
# 같은 뜻의 변형은 한 패턴으로 묶어 중첩 가산을 막음.
SOLVED_PATTERNS = [
    (r"\bsolv(?:e|es|ed|ing)\b", 4), (r"\bresolv(?:e|es|ed|ing)\b", 4),
    (r"\bcrack(?:s|ed)\b", 4), (r"\bdeciph(?:er|ers|ered|ering)\b", 4),
    (r"\bdecod(?:e|es|ed|ing)\b", 4), (r"\bexplain(?:s|ed)?\b|\bexplanation\b", 3),
    (r"\bfinally\b", 3), (r"\bdebunk(?:s|ed)?\b", 3), (r"\banswer(?:s|ed)?\b", 2),
    (r"\breveal(?:s|ed)?\b|\buncover(?:s|ed)\b", 2), (r"\bidentif(?:y|ies|ied)\b", 2),
    (r"\bconfirm(?:s|ed)?\b", 2), (r"\bpinpoint(?:s|ed)?\b", 2), (r"\btrac(?:e|es|ed)\b", 2),
    (r"\bfirst time\b|\bbreakthrough\b", 2),
]
MYSTERY_PATTERNS = [
    (r"\bmyster(?:y|ies|ious)\b", 4), (r"\benigma(?:tic)?\b", 4), (r"\briddle\b", 4),
    (r"\bpuzzl(?:e|es|ed|ing)\b", 3), (r"\bbaffl\w*", 4), (r"\bunexplained\b", 4),
    (r"\bparadox\w*", 3), (r"\bbizarre\b", 3), (r"\bstrange\b|\bweird\b", 2),
    (r"\bsecrets?\b", 2), (r"\banomal\w*", 2), (r"\bunknown\b", 1),
    (r"\b(?:decades|century|centuries|millennia)[- ]old\b|\bcenturies\b|\bmillennia\b", 3),
    (r"\blong-?standing\b", 3), (r"\blost\b|\bmissing\b|\bhidden\b", 2),
    (r"\bdebat\w*|\bcontrovers\w*", 2), (r"\borigins?\b", 1),
]
DISCOVERY_PATTERNS = [   # --mode 발견 에서만 점수에 들어감
    (r"\bdiscover(?:y|ies|ed|s)?\b", 3), (r"\bfirst (?:ever|evidence|time|known|direct)\b", 4),
    (r"\bearliest\b|\boldest\b", 3), (r"\bnew(?:ly)? (?:species|found|discovered|identified)\b", 3),
    (r"\bunexpected(?:ly)?\b|\bsurpris\w*", 3), (r"\bnever (?:before )?seen\b|\bunprecedented\b", 3),
    (r"\boverturn\w*|\brewrit\w*|\bchalleng(?:e|es|ed) (?:the )?(?:long-held|textbook|conventional)\b", 4),
]
# 아직 풀리지 않았다는 표현 (해결 신호보다 우선해서 상태 판단)
OPEN_PATTERNS = re.compile(
    r"\bun(?:solved|resolved|explained|answered|clear)\b|\bremains? (?:a )?(?:mystery|unknown|debated|elusive)\b|"
    r"\bstill (?:unknown|unclear|debated|a mystery)\b|\bno consensus\b|\bopen questions?\b|"
    r"\bpoorly understood\b|\byet to be\b|\bnot (?:yet )?(?:known|understood)\b", re.I)
# 확정이 아니라 제안/추정이라는 표현
HEDGE_PATTERNS = re.compile(
    r"\bmay(?: have)?\b|\bmight\b|\bcould\b|\bsuggests?\b|\bsuggesting\b|\bpossibl[ey]\b|"
    r"\blikely\b|\bhints?\b|\bpropos(?:e|es|ed)\b|\bnarrows?\b|\bpoints? to\b|"
    r"\bappears? to\b|\bclues?\b|\bopportunit\w*|\bchance to\b|\bare solving\b|\bworking to\b", re.I)

ARCH_WORDS = [
    "archaeolog", "ancient", "tomb", "burial", "skeleton", "pyramid", "temple",
    "civiliz", "inscription", "script", "manuscript", "papyrus", "artifact",
    "artefact", "ruins", "mummy", "mummies", "neolithic", "bronze age", "iron age",
    "roman", "egypt", "maya", "viking", "pharaoh", "shipwreck", "cave art",
    "rock art", "ancient dna", "radiocarbon", "excavat", "medieval", "prehistoric",
    "stonehenge", "hominin", "neanderthal", "denisovan", "homo ", "fossil",
]
ARCH_STRONG = [  # 이 단어가 있으면 바로 고고학/인류 분야
    "archaeolog", "tomb", "burial", "pyramid", "inscription", "mummy", "mummies",
    "excavat", "civiliz", "neanderthal", "hominin", "denisovan", "skeleton", "shipwreck",
    "cave art", "rock art", "manuscript", "papyrus", "stonehenge", "pharaoh",
]
TECH_WORDS = {  # "과학기술로 풀었다" 신호 -> 한국어 표기
    "ancient dna": "고대 DNA", "dna": "DNA", "genom": "유전체 분석", "ct scan": "CT",
    "x-ray": "X선", "lidar": "라이다", "satellite": "위성", "machine learning": "AI",
    "artificial intelligence": "AI", "isotope": "동위원소 분석", "radiocarbon": "방사성탄소 연대측정",
    "laser": "레이저", "synchrotron": "방사광가속기", "simulation": "시뮬레이션",
    "protein": "단백질 분석", "spectro": "분광 분석", "drone": "드론",
    "neural network": "AI", "microscop": "현미경", "pollen": "꽃가루 분석",
    "network science": "네트워크 과학", "morpholog": "형태 분석",
}
# 일반 시청자가 알아듣기 어려운 전문 논문 신호 (저널 원문에만 적용)
JARGON = re.compile(
    r"\b(mediat\w*|biosynthes\w*|conformation\w*|glycogen|titin|rnase|cryo-em|"
    r"\w+ase\b|\w+ome\b|\w+osis\b|\w+cyte\w*|genom\w* (?:of|origins?)|"
    r"single-cell|transcript\w*|ligand|receptor|kinase|peptide|protein sorting|"
    r"in vivo|in vitro|mouse model|cohort|pathway|assembl\w*|lineage|\w+ylation|"
    r"cytokine\w*|signal(?:l)?ing|lithospher\w*|discontinuit\w*|grain-size)\b", re.I)
NOISE_TITLES = re.compile(r"daily briefing|books in brief|correction|retraction|"
                          r"podcast|editorial|erratum|reply to|news in brief|"
                          r"this week|quiz|crossword", re.I)

STOPWORDS = set("""a an the of in on at to for and or with from by as is are was were be been
its it this that these those new study studies scientists researchers find finds found
may might could how why what who when where reveal reveals revealed after into over
than about more most first their they them our we finally solve solved mystery
mysterious decades centuries old year years have has had not but all can""".split())
# 유튜브 검색어에서 빼는 일반 단어 (구체적 대상이 묻히지 않게)
GENERIC = set("""research traces trace origins origin impact evidence discovery discovered
reveal reveals hidden ancient human humans people world lost strange weird secret secrets
largest biggest oldest rare surprising surprise shows show suggests long-standing question
questions answer clues clue scientist archaeologists astronomers experts nearly almost
million billion thousand through using inside behind finally truth""".split())


# ------------------------------------------------------------------ 공통

def log(msg):
    print(msg, file=sys.stderr, flush=True)


def http_get(url, ua=UA_BOT, timeout=25, retries=3, data=None, headers=None):
    h = {"User-Agent": ua, "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8"}
    h.update(headers or {})
    req = urllib.request.Request(url, data=data, headers=h)
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503) and attempt < retries:
                time.sleep(min(int(e.headers.get("Retry-After") or 0) or 2 ** (attempt + 1), 30))
                continue
            raise
        except urllib.error.URLError:
            if attempt < retries:
                time.sleep(2)
                continue
            raise


def clean(text):
    text = re.sub(r"<[^>]+>", " ", text or "")
    return re.sub(r"\s+", " ", unescape(text)).strip()


def pattern_score(text, patterns):
    hits, total = [], 0
    for pat, w in patterns:
        m = re.search(pat, text, re.I)
        if m:
            hits.append(m.group(0).lower())
            total += w
    return total, hits


def count_hits(text, words):
    t = text.lower()
    return [w.strip() for w in words if w in t]


def parse_date(s):
    if not s:
        return None
    s = s.strip()
    try:
        d = parsedate_to_datetime(s)
    except (TypeError, ValueError):
        try:
            d = datetime.fromisoformat(s.replace("Z", "+00:00"))
        except ValueError:
            return None
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def norm_url(u):
    """같은 문서를 가리키는 URL 을 하나로 (DOI 는 소문자 DOI 로)."""
    u = (u or "").strip()
    m = re.search(r"(10\.\d{4,9}/[^\s?#]+)", u)
    if m:
        return "doi:" + m.group(1).lower().rstrip("/.")
    p = urllib.parse.urlsplit(u)
    host = p.netloc.lower().removeprefix("www.")
    return f"{host}{p.path.rstrip('/')}".lower()


def title_key(t):
    return re.sub(r"[^a-z0-9]", "", t.lower())[:60]


def publisher(source):
    return source.split()[0] if source else ""


# ------------------------------------------------------------------ 1. 저널 (OpenAlex)

def openalex_abstract(inv):
    if not inv:
        return ""
    pos = {}
    for word, idxs in inv.items():
        for i in idxs:
            pos[i] = word
    return " ".join(pos[i] for i in sorted(pos))


def collect_journals(days, mailto="", searches=None):
    """OpenAlex 는 무료지만 요청 한도가 있음. mailto(이메일)를 붙이면 더 넉넉한 'polite pool' 한도를 줌 (선택)."""
    log("[1/5] 주요 과학저널 검색 중 (OpenAlex)...")
    since = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")
    issn = "|".join(JOURNALS)
    items, failed = [], []

    def one(term):
        params = {
            "search": term,
            "filter": f"primary_location.source.issn:{issn},from_publication_date:{since}",
            "per-page": "50", "sort": "relevance_score:desc",
            "select": "id,title,publication_date,primary_location,cited_by_count,doi,abstract_inverted_index,type",
        }
        if mailto:
            params["mailto"] = mailto
        if limited:   # 이미 요청 한도(429)에 걸렸으면 나머지 검색어는 기다리지 않고 건너뜀
            failed.append(f"{term}: 건너뜀 (앞선 요청이 429 요청 한도 초과)")
            return []
        try:
            return json.loads(http_get("https://api.openalex.org/works?" + urllib.parse.urlencode(params), retries=1))["results"]
        except urllib.error.HTTPError as e:
            if e.code == 429:
                limited.append(term)
            failed.append(f"{term}: {e}")
            return []
        except Exception as e:
            failed.append(f"{term}: {e}")
            return []

    limited = []

    with ThreadPoolExecutor(2 if not mailto else 4) as ex:   # 한도 때문에 동시 요청을 줄임 (mailto 있으면 4)
        searches = searches or JOURNAL_SEARCHES
        for term, res in zip(searches, ex.map(one, searches)):
            log(f"  - '{term}': {len(res)}건")
            for w in res:
                title = clean(w.get("title") or "")
                if not title or NOISE_TITLES.search(title):
                    continue
                src = ((w.get("primary_location") or {}).get("source") or {}).get("display_name", "")
                items.append({
                    "origin": "논문", "source": src, "title": title,
                    "summary": openalex_abstract(w.get("abstract_inverted_index"))[:600],
                    "url": w.get("doi") or w.get("id"), "doi": w.get("doi") or "",
                    "date": w.get("publication_date", ""), "journal": src,
                    "work_type": w.get("type", ""), "cited": w.get("cited_by_count", 0),
                })
    for f in failed:
        log(f"  ! 저널 검색 실패 {f}")
    return items, failed


# ------------------------------------------------------------------ 2. 뉴스 RSS

def fetch_feed(name, url):
    try:
        root = ET.fromstring(http_get(url, ua=UA_WEB))
    except Exception as e:
        return [], f"{name}: {e}"
    atom = "{http://www.w3.org/2005/Atom}"
    out = []
    for it in root.iter():
        if it.tag not in ("item", atom + "entry"):
            continue

        def find(*names):
            for n in names:
                el = it.find(n)
                if el is not None:
                    return el
            return None
        t = find("title", atom + "title")
        l = find("link", atom + "link")
        d = find("description", atom + "summary", atom + "content")
        dt = find("pubDate", atom + "published", atom + "updated",
                  "{http://purl.org/dc/elements/1.1/}date")
        date = parse_date(dt.text if dt is not None else "")
        summary = clean(d.text if d is not None else "")[:600]
        # 기사에 '언급된' 저널명 (논문을 확인한 것은 아님)
        mention = ""
        for j in sorted(set(JOURNALS.values()), key=len, reverse=True):
            if re.search(r"\b" + re.escape(j) + r"\b", summary):
                mention = j
                break
        doi = re.search(r"10\.\d{4,9}/[^\s\"<>]+", summary)
        out.append({
            "origin": "뉴스", "source": name, "title": clean(t.text if t is not None else ""),
            "summary": summary,
            "url": ((l.text or l.get("href", "")) if l is not None else "").strip(),
            "doi": ("https://doi.org/" + doi.group(0).rstrip(".")) if doi else "",
            "date": date.strftime("%Y-%m-%d") if date else "",
            "journal": "", "journal_mention": mention, "cited": 0,
        })
    return out, ""


def collect_news():
    log("[2/5] 과학/고고학 뉴스 수집 중...")
    with ThreadPoolExecutor(6) as ex:
        res = list(ex.map(lambda kv: fetch_feed(*kv), NEWS_FEEDS.items()))
    items, failed = [], []
    for (name, _), (rows, err) in zip(NEWS_FEEDS.items(), res):
        if err:
            failed.append(err)
            log(f"  ! {err}")
        else:
            log(f"  - {name}: {len(rows)}건")
        items += [i for i in rows if i["title"] and not NOISE_TITLES.search(i["title"])]
    return items, failed


# ------------------------------------------------------------------ 병합 + 상태 판정 + 점수

NON_RESEARCH_TYPES = {"editorial", "letter", "review", "erratum", "paratext", "other",
                      "peer-review", "retraction"}


def work_kind(it):
    """자료 유형: 연구 논문 / 저널 뉴스 / 저널 리뷰 등 / 기사"""
    if it["origin"] != "논문":
        return "기사"
    doi = (it.get("doi") or "").lower()
    if "10.1038/d41586-" in doi:  # Nature 뉴스·특집 기사 DOI
        return "저널 뉴스"
    if it.get("work_type") in NON_RESEARCH_TYPES:
        return f"저널 {it['work_type']}"
    return "연구 논문"


def merge_items(items):
    """같은 문서(URL/DOI) 또는 같은 제목을 한 소재로 합친다 (union-find, 입력 순서와 무관).
    점수는 병합 후에 계산."""
    parent = list(range(len(items)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    owner = {}
    for i, it in enumerate(items):
        keys = ["u:" + norm_url(it["url"]), "t:" + title_key(it["title"])]
        if it.get("doi"):
            keys.append("u:" + norm_url(it["doi"]))
        for k in keys:
            if k in ("u:", "t:"):
                continue
            if k in owner:
                a, b = find(i), find(owner[k])
                if a != b:
                    parent[max(a, b)] = min(a, b)
            else:
                owner[k] = i
    clusters = {}
    for i in range(len(items)):
        clusters.setdefault(find(i), []).append(items[i])

    groups = []
    for members in clusters.values():
        # 대표 항목: 기사 제목(대중적 표현) 우선, 그다음 요약이 긴 것, 동점이면 제목순
        rep = min(members, key=lambda x: (x["origin"] == "논문", -len(x.get("summary", "")), x["title"]))
        g = dict(rep)
        links = sorted({(m["source"], m["url"], work_kind(m)) for m in members})
        papers = sorted({m.get("doi") or (m["url"] if m["origin"] == "논문" else "") for m in members} - {""})
        research = [m for m in members if work_kind(m) == "연구 논문"]
        jitems = sorted([m for m in members if m["origin"] == "논문"],
                        key=lambda m: (work_kind(m) != "연구 논문", m["journal"]))
        mentions = sorted({m.get("journal_mention") for m in members if m.get("journal_mention")})
        g.update({
            "links": [list(l) for l in links],
            "publishers": sorted({"논문" if m["origin"] == "논문" else publisher(m["source"]) for m in members}),
            "papers": papers,
            "journal": jitems[0]["journal"] if jitems else "",
            "kinds": sorted({work_kind(m) for m in members}),
            "has_research": bool(research),
            "research_abstract": any(len(m.get("summary", "")) > 100 for m in research),
            "cited": max((m.get("cited", 0) for m in members), default=0),
            "journal_mention": mentions[0] if mentions else "",
            "summary": max((m.get("summary", "") for m in members), key=lambda s: (len(s), s)),
        })
        g["coverage"] = len(g["publishers"])  # 서로 다른 발행처 수 (같은 사이트 재노출은 1)
        groups.append(g)
    groups.sort(key=lambda g: g["title"])
    return groups


# 해결 동사가 부정·실패·목적·시도로 쓰인 경우 (해결 성과가 아님)
NEG_SOLVE = re.compile(
    r"\b(?:not|never|no one has|nobody has|failed to|fails? to|unable to|cannot|can't|couldn't|"
    r"attempts? to|attempting to|trying to|tries to|try to|hopes? to|hoping to|aims? to|aiming to|"
    r"seeks? to|seeking to|efforts? to|quest to|yet to|could help|may help|might help|helps? to|"
    r"key to|race to|bid to|chance to|opportunity to|needed to|need to|will|would|to)\s+(?:\w+\s+){0,2}?"
    r"(?:solv|resolv|crack|deciph|decod|explain|answer)\w*", re.I)
STRONG_SOLVED = re.compile(
    r"\b(?:solv(?:e|es|ed)|resolv(?:e|es|ed)|crack(?:s|ed)|decipher(?:s|ed)|decod(?:es|ed))\b", re.I)


def solve_status(title, summary):
    """해결 근거 / 가설 제안 / 미해결 / 확인 필요"""
    text = title + " " + summary
    negated = NEG_SOLVE.search(text)
    clean_text = NEG_SOLVE.sub(" ", text)          # 부정·시도 표현은 해결 신호에서 뺌
    s, _ = pattern_score(clean_text, SOLVED_PATTERNS)
    strong_solved = bool(STRONG_SOLVED.search(clean_text))
    open_ = OPEN_PATTERNS.search(title) or OPEN_PATTERNS.search(summary) or negated
    hedge = HEDGE_PATTERNS.search(title) or HEDGE_PATTERNS.search(summary[:250])
    if open_ and not strong_solved:
        return "미해결"
    if (strong_solved or s >= 4) and not hedge:
        return "해결 근거"
    if s >= 2:
        return "가설 제안"
    return "미해결" if open_ else "확인 필요"


STATUS_BONUS = {"해결 근거": 10, "가설 제안": 6, "미해결": 2, "확인 필요": 0}


def evidence_status(g):
    """연구 근거 표기와 점수. 저널 뉴스/리뷰나 DOI 존재만으로 '연구 확인'으로 보지 않음."""
    if g.get("has_research") and g.get("research_abstract"):
        return f"원저 연구 · 초록 확인 ({g['journal']})", 8
    if g.get("has_research"):
        return f"원저 연구 · 초록 없음, 본문 미검증 ({g['journal']})", 5
    if any(k.startswith("저널") for k in g.get("kinds", [])):
        return f"저널 뉴스/리뷰 ({g['journal']}) · 원저 아님", 3
    if g.get("papers"):
        return "DOI 연결됨 · 본문 미검증", 4
    if g.get("journal_mention"):
        return f"저널 언급({g['journal_mention']}) · 논문 미확인", 3
    return "뉴스만", 0


def score_items(groups, days, focus, now=None, mode="미스터리"):
    now = now or datetime.now(timezone.utc)
    disc = mode == "발견"
    out = []
    for it in groups:
        text = it["title"] + " " + it["summary"]
        m, mh = pattern_score(text, MYSTERY_PATTERNS)
        s, sh = pattern_score(NEG_SOLVE.sub(" ", text), SOLVED_PATTERNS)
        dv, dh = pattern_score(text, DISCOVERY_PATTERNS) if disc else (0, [])
        arch = count_hits(text, ARCH_WORDS)
        strong = count_hits(text, ARCH_STRONG)
        tech = list(dict.fromkeys(TECH_WORDS[k] for k in TECH_WORDS if k in text.lower()))
        if m == 0 and not (arch and s) and not dv:
            continue  # 미스터리 요소(발견 모드면 새 발견 신호도)가 없는 일반 연구는 제외
        if re.match(r"^[A-Z][a-z]+ [A-Z][a-z]+: ", it["title"]):
            continue  # "이름 성: ..." 형식의 인물 인터뷰/프로필 기사
        if it["origin"] == "논문" and len(it["links"]) == 1:
            # 논문 원문만 있는 경우: 미스터리 신호가 충분해야 하고, 전문용어가 많으면 제외
            # ("Deciphering X signaling" 처럼 해결 동사가 방법 설명으로만 쓰인 논문도 거름)
            tm, _ = pattern_score(it["title"], MYSTERY_PATTERNS)
            ts, _ = pattern_score(it["title"], SOLVED_PATTERNS)
            td = pattern_score(it["title"], DISCOVERY_PATTERNS)[0] if disc else 0
            if m + dv < 4 or (tm < 2 and ts < 4 and td < 3) or JARGON.search(it["title"]) \
                    or len(JARGON.findall(text)) >= 3:
                continue
        d = parse_date(it["date"]) if it["date"] else None
        if d and now - d > timedelta(days=days):
            continue
        is_arch = bool(strong) or len(arch) >= 2
        status = solve_status(it["title"], it["summary"])
        ev, ev_pts = evidence_status(it)
        age = (now - d).days if d else days
        score = (
            m * 2.0 + s * 1.5 + dv * 2.0
            + STATUS_BONUS[status]
            + (min(len(arch), 4) * (5 if focus == "고고학" else 3) if is_arch else 0)
            + min(len(tech), 3) * 2
            + ev_pts
            + max(0, 1 - age / max(days, 1)) * (16 if disc else 8)    # 발견 모드는 최신일수록 더 우대
            + min(math.log10(it.get("cited", 0) + 1) * 3, 6)
            + (it["coverage"] - 1) * 4                 # 서로 다른 발행처의 독립 보도
        )
        it.update({
            "signals": ", ".join(mh + sh + dh), "arch": is_arch, "tech": ", ".join(tech),
            "status": status, "evidence": ev, "base_score": round(score, 1),
            "field": "고고학/인류" if is_arch else guess_field(text),
        })
        out.append(it)
    out.sort(key=lambda x: (-x["base_score"], x["title"]))
    return out


def guess_field(text):
    t = text.lower()
    table = {
        "우주/천문": ["galax", "star", "planet", "black hole", "cosmic", "universe", "moon",
                  "solar", "sun", "telescope", "asteroid", "neutrino", "dark matter", "mercury",
                  "uranus", "neptune", "eclipse"],
        "생명/진화": ["dinosaur", "species", "evolution", "animal", "gene", "cell", "mammal",
                  "bacteri", "virus", "bird", "insect", "plant", "whale", "shark", "fossil"],
        "뇌/인체": ["brain", "memory", "sleep", "neuro", "conscious", "disease", "human body"],
        "지구/바다": ["earthquake", "volcano", "ocean", "climate", "ice", "geolog", "deep sea"],
        "물리/화학/수학": ["quantum", "particle", "physic", "chemi", "molecule", "laser", "math"],
    }
    best, n = "기타 과학", 0
    for f, ws in table.items():
        k = sum(w in t for w in ws)
        if k > n:
            best, n = f, k
    return best


# ------------------------------------------------------------------ 3. 내 채널

def yt_initial_data(html):
    m = re.search(r"var ytInitialData = (\{.*?\});</script>", html)
    if not m:
        return None
    try:
        return json.loads(m.group(1))
    except json.JSONDecodeError:
        return None


def walk(o, fn):
    if isinstance(o, dict):
        fn(o)
        for v in o.values():
            walk(v, fn)
    elif isinstance(o, list):
        for v in o:
            walk(v, fn)


def channel_titles(url):
    """채널의 모든 영상 제목 (API 키 없이 공개 페이지에서). 실패하면 예외."""
    html = http_get(url.rstrip("/") + "/videos", ua=UA_WEB).decode("utf-8", "ignore")
    data = yt_initial_data(html)
    if data is None:
        raise RuntimeError("채널 페이지 형식을 읽지 못함 (동의 화면 또는 구조 변경)")
    ver = re.search(r'"INNERTUBE_CLIENT_VERSION":"([^"]+)"', html)
    titles, tokens = [], []

    def grab(o):
        if "lockupViewModel" in o:
            md = o["lockupViewModel"].get("metadata", {}).get("lockupMetadataViewModel", {})
            if md.get("title", {}).get("content"):
                titles.append(md["title"]["content"])
        if "videoRenderer" in o:
            titles.append("".join(r["text"] for r in o["videoRenderer"]["title"]["runs"]))
        if "continuationCommand" in o:
            tokens.append(o["continuationCommand"]["token"])

    walk(data, grab)
    while tokens and ver and len(titles) < 2000:
        body = json.dumps({"context": {"client": {"clientName": "WEB", "clientVersion": ver.group(1), "hl": "ko"}},
                           "continuation": tokens.pop()}).encode()
        walk(json.loads(http_get("https://www.youtube.com/youtubei/v1/browse", ua=UA_WEB, data=body,
                                 headers={"Content-Type": "application/json"})), grab)
    return list(dict.fromkeys(titles))


def load_excludes():
    """channel_exclude.txt: 이미 다룬 주제의 영어 키워드 (한 줄에 하나, 쉼표=AND)."""
    if not os.path.exists(EXCLUDE_FILE):
        return []
    rules = []
    with open(EXCLUDE_FILE, encoding="utf-8") as f:
        for line in f:
            line = line.split("#", 1)[0].strip()
            if line:
                rules.append([w.strip().lower() for w in line.split(",") if w.strip()])
    return rules


def is_covered(item, rules):
    text = (item["title"] + " " + item["summary"]).lower()
    for words in rules:
        if all(re.search(r"\b" + re.escape(w), text) for w in words):
            return "+".join(words)
    return ""


# ------------------------------------------------------------------ 4. 유튜브 수요/경쟁

YT_CACHE_VER = 2  # 캐시에는 검색 원본(영상 목록)만 저장하고 관련성 판정은 매번 다시 계산
CAPS_IGNORE = set("""the this these those their there they our its his her new scientists researchers
researcher scientist university institute professor journal nature science sciences proceedings
academy national communications advances current biology study team january february march april
may june july august september october november december monday tuesday wednesday thursday friday
saturday sunday among although however while when where after before during despite""".split())


def search_terms(title, summary=""):
    """유튜브 검색어와 판정용 단어.
    ids: 소재를 식별하는 고유명사(제목 + 요약 문장 중간의 대문자 단어), content: 구체 명사."""
    words = re.findall(r"[A-Za-z][A-Za-z\-]*(?:'s)?|\d[\d,]*(?:-[a-z]+)*", title)
    ids, content = [], []
    for i, w in enumerate(words):
        lw = w.lower().removesuffix("'s").strip("-")
        if lw in STOPWORDS or lw in GENERIC or lw in CAPS_IGNORE or len(lw) < 3 or re.match(r"\d", lw):
            continue
        if w[0].isupper() and i > 0:
            ids.append(lw)
        elif lw not in content:
            content.append(lw)
    if len(ids) < 2:  # 제목에 고유명사가 부족하면 요약에서 보충 (문장 첫 단어는 제외)
        for sent in re.split(r"(?<=[.!?])\s+", summary[:600]):
            for w in re.findall(r"[A-Za-z][A-Za-z\-]*(?:'s)?", sent)[1:]:
                lw = w.lower().removesuffix("'s")
                if w[0].isupper() and len(lw) >= 3 and lw not in CAPS_IGNORE | STOPWORDS | GENERIC:
                    ids.append(lw)
    ids = list(dict.fromkeys(ids))[:4]
    return ids, [c for c in content if c not in ids]


def term_in(term, tokens):
    stem = term[:5] if len(term) >= 5 else term
    return any(t == term or (len(stem) >= 5 and t.startswith(stem)) for t in tokens)


def relevance(video_title, ids, content):
    """같은 소재(사건) 영상인가. 고유명사가 있으면 1개 이상 일치 + 핵심어 합계 2개 이상.
    고유명사가 없으면 구체 명사 3개 이상 일치해야 인정 (분야만 같은 영상 배제)."""
    tokens = re.findall(r"[a-z][a-z\-]*", video_title.lower())
    sp = [t for t in ids if term_in(t, tokens)]
    ct = [t for t in content[:6] if term_in(t, tokens)]
    if ids:
        if not sp:
            return False, "식별어(고유명사) 불일치"
        if len(sp) + len(ct) < 2:
            return False, "핵심어 1개만 일치"
        return True, "일치: " + ", ".join(sp + ct)
    if len(ct) >= 3:
        return True, "일치(고유명사 없음): " + ", ".join(ct)
    return False, "고유명사 없음 · 구체 명사 3개 미만"


def broad_match(video_title, content):
    """넓은 분야 관심도 (같은 사건은 아님): 구체 명사 2개 이상 일치."""
    tokens = re.findall(r"[a-z][a-z\-]*", video_title.lower())
    return sum(term_in(t, tokens) for t in content[:6]) >= 2


def parse_views(s):
    """'조회수 1.2만회', '1.2M views', '15,430 views', '조회수 없음' -> 정수."""
    s = (s or "").replace(",", "").strip()
    if not s or "없음" in s or s.lower().startswith("no view"):
        return 0
    m = re.search(r"(\d+(?:\.\d+)?)\s*(천|만|억|[KkMmBb])?", s)
    if not m:
        return 0
    mult = {"천": 1e3, "만": 1e4, "억": 1e8, "k": 1e3, "m": 1e6, "b": 1e9}
    return int(float(m.group(1)) * mult.get((m.group(2) or "").lower(), 1))


def months_ago(s):
    """'3개월 전', '1년 전', '18 months ago', '2 weeks ago' -> 개월 수 (모르면 None)."""
    s = (s or "").lower()
    m = re.search(r"(\d+)\s*(초|분|시간|일|주|개월|년)\s*전", s) or \
        re.search(r"(\d+)\s*(second|minute|hour|day|week|month|year)s?\s*ago", s)
    if not m:
        return None
    n, unit = int(m.group(1)), m.group(2)
    if unit in ("초", "분", "시간", "일", "second", "minute", "hour", "day"):
        return 0
    if unit in ("주", "week"):
        return n / 4.35
    if unit in ("개월", "month"):
        return n
    return n * 12


def fetch_search(q, cache, offline):
    """유튜브 검색 원본 (영상 목록). 반환: (상태, 영상목록, 확인시각)"""
    hit = cache.get(q)
    if hit and hit.get("ver") == YT_CACHE_VER:
        return "확인", hit["vids"], hit["fetched"] + " (캐시)"
    if offline:
        return "미확인(오프라인 · 저장된 검색 결과 없음)", [], ""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    try:
        html = http_get("https://www.youtube.com/results?" + urllib.parse.urlencode({"search_query": q}),
                        ua=UA_WEB).decode("utf-8", "ignore")
    except Exception as e:
        return f"미확인(HTTP 오류: {e})", [], now
    finally:
        time.sleep(0.7)  # 유튜브에 부담 주지 않게
    data = yt_initial_data(html)
    if data is None:
        why = "동의 화면" if "consent" in html.lower() else "페이지 형식 변경"
        return f"미확인({why})", [], now
    vids, has_list = [], []

    def grab(o):
        if "itemSectionRenderer" in o:
            has_list.append(1)
        if "videoRenderer" in o:
            v = o["videoRenderer"]
            vids.append({
                "id": v.get("videoId", ""),
                "title": "".join(r["text"] for r in v.get("title", {}).get("runs", [])),
                "views_text": v.get("viewCountText", {}).get("simpleText", ""),
                "age_text": v.get("publishedTimeText", {}).get("simpleText", ""),
            })
    walk(data, grab)
    if not has_list:
        return "미확인(검색 결과 구조를 찾지 못함)", [], now
    cache[q] = {"ver": YT_CACHE_VER, "fetched": now, "vids": vids}
    return "확인", vids, now


def youtube_check(item, cache, offline=False):
    ids, content = search_terms(item["title"], item.get("summary", ""))
    q = " ".join((ids[:2] + content)[:5])
    if not q:
        return {"yt_query": q, "yt_status": "미확인(검색어 없음)"}
    status, raw_vids, when = fetch_search(q, cache, offline)
    res = {"yt_query": q, "yt_ids": ", ".join(ids), "yt_checked": when}
    if status != "확인":
        return {**res, "yt_status": status}
    rel, broad = [], []
    for rv in raw_vids:
        v = {**rv, "views": parse_views(rv["views_text"]), "months": months_ago(rv["age_text"]),
             "url": f"https://www.youtube.com/watch?v={rv['id']}"}
        ok, why = relevance(v["title"], ids, content)
        v["why"] = why
        if ok:
            rel.append(v)
        elif broad_match(v["title"], content):
            broad.append(v)
    dated = [v for v in rel if v["months"] is not None]
    recent = [v for v in dated if v["months"] < 12]
    border = [v for v in dated if 12 <= v["months"] <= 13]
    top = max(rel, key=lambda v: v["views"]) if rel else None
    btop = max(broad, key=lambda v: v["views"]) if broad else None
    if not raw_vids:
        basis = "표본 0건"
    elif not rel:
        basis = "판단 근거 부족 (같은 소재 영상 없음)"
    elif not dated:
        basis = "판단 근거 부족 (관련 영상 날짜 미상)"
    else:
        basis = "판단 가능"
    return {
        **res, "yt_status": f"확인(표본 {len(raw_vids)}개)", "yt_basis": basis,
        "yt_sample": len(raw_vids), "yt_related": len(rel), "yt_recent": len(recent),
        "yt_border": len(border), "yt_date_unknown": len(rel) - len(dated),
        "yt_top_views": top["views"] if top else 0,
        "yt_top_title": top["title"] if top else "", "yt_top_url": top["url"] if top else "",
        "yt_top_why": top["why"] if top else "",
        "yt_related_list": [{"title": v["title"], "url": v["url"], "views": v["views"], "why": v["why"]} for v in rel],
        "yt_broad_views": btop["views"] if btop else 0,
        "yt_broad_title": btop["title"] if btop else "", "yt_broad_url": btop["url"] if btop else "",
    }


def apply_youtube(items, cache, offline=False):
    for it in items:
        yt = youtube_check(it, cache, offline)
        it.update(yt)
        # 같은 소재 영상이 확인된 경우에만 수요·경쟁을 점수에 반영 (넓은 분야 관심도는 참고용)
        if yt.get("yt_basis") != "판단 가능":
            it["score"] = it["base_score"]
            continue
        demand = math.log10(yt["yt_top_views"] + 1) * 3
        gap = 8 if yt["yt_recent"] == 0 else (4 if yt["yt_recent"] <= 2 else -3)
        it["score"] = round(it["base_score"] + demand + gap, 1)


# ------------------------------------------------------------------ 4-1. 한국어 번역 (무료)

def first_sentences(text, limit=220):
    out = ""
    for sent in re.split(r"(?<=[.!?])\s+", text or ""):
        if len(out) + len(sent) > limit:
            break
        out += (" " if out else "") + sent
    return out or (text or "")[:limit]


def translate_ko(text, cache, offline=False):
    """영어 -> 한국어 기계번역 (무료: MyMemory, 실패하면 Google 무료 엔드포인트). 반환: (번역, 상태)"""
    text = (text or "").strip()
    if not text:
        return "", "없음"
    if text in cache:
        return cache[text], "캐시"
    if offline:
        return "", "오프라인 · 저장된 번역 없음"
    q = text[:480]
    try:
        d = json.loads(http_get("https://api.mymemory.translated.net/get?"
                                + urllib.parse.urlencode({"q": q, "langpair": "en|ko"}), retries=1))
        t = unescape(d.get("responseData", {}).get("translatedText") or "")
        if d.get("quotaFinished") or str(d.get("responseStatus")) != "200" or not t \
                or "MYMEMORY WARNING" in t.upper():
            raise RuntimeError(d.get("responseDetails") or "무료 한도 초과")
    except Exception as e1:
        try:
            d = json.loads(http_get("https://translate.googleapis.com/translate_a/single?"
                                    + urllib.parse.urlencode({"client": "gtx", "sl": "en", "tl": "ko",
                                                              "dt": "t", "q": q}), ua=UA_WEB, retries=1))
            t = "".join(x[0] for x in d[0] if x and x[0])
        except Exception as e2:
            return "", f"번역 실패 ({e1}; {e2})"
    finally:
        time.sleep(0.4)
    cache[text] = t
    return t, "번역"


def translate_picks(picks, cache, offline=False):
    ok = fail = 0
    for it in picks:
        it["title_ko"], st1 = translate_ko(it["title"], cache, offline)
        it["summary_ko"], st2 = translate_ko(first_sentences(it["summary"]), cache, offline)
        it["translate_status"] = st1 if st1 == st2 else f"제목 {st1} / 요약 {st2}"
        if it["title_ko"]:
            ok += 1
        else:
            fail += 1
    return ok, fail


# ------------------------------------------------------------------ 5. 훅 제목

def span_phrase(text):
    t = text.lower()
    m = re.search(r"(\d[\d,]*)[- ]year[- ]old", t)
    if m:
        return f"{m.group(1)}년 전"
    m = re.search(r"(\d+)(?:st|nd|rd|th)[- ]century", t)
    if m:
        return f"{m.group(1)}세기"
    m = re.search(r"for (?:nearly |almost |over |more than )?(\d[\d,]*) years", t)
    if m:
        return f"{m.group(1)}년간"
    return ""


def template_titles(it):
    """규칙 기반 제목 틀. [소재] 자리에 한국어 소재명을 넣어 쓰면 됩니다.
    해결 상태에 맞는 표현만 쓰고, 원문에 없는 기간·기술은 넣지 않음."""
    span = span_phrase(it["title"] + " " + it["summary"])
    pre = f"{span} " if span else ""
    tech = it["tech"].split(", ")[0] if it["tech"] else ""
    st = it["status"]
    if st == "해결 근거":
        t = [f"{pre}풀리지 않던 [소재] 수수께끼, 마침내 답이 나왔다",
             f"[소재]의 정체, 과학이 밝혀낸 진실"]
        if tech:
            t.append(f"{tech}로 풀어낸 [소재]의 비밀")
    elif st == "가설 제안":
        t = [f"{pre}[소재]의 수수께끼, 드디어 풀렸을까?",
             f"[소재]에 대한 새로운 답, 과학자들이 내놓은 유력한 가설"]
        if tech:
            t.append(f"{tech}가 찾아낸 [소재]의 새 단서")
    elif st == "미해결":
        t = [f"{pre}아직 아무도 풀지 못한 [소재]의 수수께끼",
             f"과학자들도 답을 모른다, [소재]에 남은 질문들"]
    else:
        t = [f"[소재], 과학자들이 새로 찾아낸 단서",
             f"{pre}[소재]에 숨어 있던 뜻밖의 사실"]
    return t


STRUCTURE = {
    "해결 근거": "훅(이상한 사실) → 미스터리의 역사 → 기존 가설과 한계 → 결정적 증거와 분석 방법 → 의미 → 남은 질문",
    "가설 제안": "훅(질문) → 미스터리의 역사 → 새 가설의 근거 → 반론·한계(아직 확정 아님) → 검증하려면 무엇이 필요한가",
    "미해결": "훅(아무도 모른다) → 무엇이 이상한가 → 경쟁 가설 2~3개 비교 → 왜 아직 못 풀었나 → 앞으로의 관측/탐사",
    "확인 필요": "원문을 읽고 해결 상태부터 확인한 뒤 구성을 정하세요",
}


# ------------------------------------------------------------------ 출력 + 분석

def unique_path(path):
    """같은 이름의 파일이 있으면 _2, _3 ... 을 붙여 덮어쓰기 방지."""
    base, ext = os.path.splitext(path)
    n, p = 1, path
    while os.path.exists(p):
        n += 1
        p = f"{base}_{n}{ext}"
    return p


def fmt_yt(it):
    st = it.get("yt_status", "확인 안 함")
    if not st.startswith("확인("):
        return st
    if it.get("yt_basis") != "판단 가능":
        return f"{it['yt_basis']} · 표본 {it['yt_sample']}개"
    s = f"같은 소재 최고 {it['yt_top_views']:,}회 · 최근12개월 {it['yt_recent']}개"
    if it.get("yt_border"):
        s += f"(+경계 {it['yt_border']})"
    return s + f" · 관련 {it['yt_related']}/{it['yt_sample']}"


def write_report(picks, cands, excluded, checks, args, stamp):
    md_path = unique_path(os.path.join(args.out, f"topics_{stamp}.md"))
    csv_path = unique_path(os.path.join(args.out, f"topics_{stamp}.csv"))

    fields = ["rank", "score", "base_score", "status", "evidence", "field", "title_ko", "summary_ko",
              "hook_1", "hook_2", "hook_3", "title", "journal", "date", "links", "papers", "coverage",
              "yt_status", "yt_basis", "yt_query", "yt_ids", "yt_top_views", "yt_recent", "yt_border",
              "yt_related", "yt_sample", "yt_top_title", "yt_top_url", "yt_top_why",
              "yt_broad_views", "yt_broad_title", "yt_checked", "tech", "signals", "translate_status",
              "topic_name", "thumb_1", "thumb_2", "thumb_3", "hashtags", "asset_dir", "thumb_mode", "thumb_notes", "bg_credit", "bg_page",
              "url", "summary"]
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for i, it in enumerate(picks, 1):
            hooks = it.get("hooks", []) + ["", "", ""]
            th = [c.replace("\n", " / ") for c in it.get("thumb_copies", [])] + ["", "", ""]
            w.writerow({**it, "rank": i, "hook_1": hooks[0], "hook_2": hooks[1], "hook_3": hooks[2],
                        "thumb_1": th[0], "thumb_2": th[1], "thumb_3": th[2],
                        "hashtags": " ".join(it.get("hashtags", [])),
                        "asset_dir": os.path.relpath(it["asset_dir"], HERE) if it.get("asset_dir") else "",
                        "links": " | ".join(f"{k} {s}: {u}" for s, u, k in it["links"]),
                        "papers": " | ".join(it["papers"])})

    L = [f"# 과학 미스터리 다큐 소재 TOP {len(picks)}",
         f"_{datetime.now():%Y-%m-%d %H:%M:%S} · 최근 {checks['_days']}일 · 후보 {len(cands)}개 중 선정 · "
         f"채널 중복 제외 {len(excluded)}개_", "",
         "### 실행 점검", ""]
    L += [f"- {k}: {v}" for k, v in checks.items() if not k.startswith("_")]
    L += ["", "| # | 점수 | 해결 상태 | 분야 | 소재 (한국어 기계번역) | 근거 | 유튜브 검색 표본 |",
          "|---|---|---|---|---|---|---|"]
    for i, it in enumerate(picks, 1):
        name = (it.get("title_ko") or it["title"][:70]).replace("|", "/")
        L.append(f"| {i} | {it.get('score', it['base_score'])} | {it['status']} | {it['field']} | {name} | "
                 f"{it['evidence']} · {it['date']} | {fmt_yt(it)} |")
    L += ["", "## 소재별 상세", ""]
    for i, it in enumerate(picks, 1):
        L.append(f"### {i}. {it.get('title_ko') or it['title']}")
        L.append(f"- 원문 제목: {it['title']}")
        if it.get("summary_ko"):
            L.append(f"- 요약 (기계번역): {it['summary_ko']}")
        L.append(f"- 해결 상태: **{it['status']}** · 근거: {it['evidence']} · 분야: {it['field']}"
                 + (f" · 분석기술: {it['tech']}" if it["tech"] else ""))
        for s, u, k in it["links"]:
            L.append(f"- {k} ({s}): {u}")
        for p in it["papers"]:
            if all(p != u for _, u, _ in it["links"]):
                L.append(f"- DOI (기사 본문에서 찾음, 미검증): {p}")
        if it["summary"]:
            L.append(f"\n> {it['summary'][:350]}\n")
        L.append("훅 제목 틀 ([소재]에 짧은 한국어 소재명을 넣어 쓰세요):")
        L += [f"- {h}" for h in it.get("hooks", [])]
        L.append(f"\n구성 방향: {STRUCTURE[it['status']]}")
        if it.get("thumb_copies"):
            L.append(f"\n썸네일 문구 3안 (소재명 `{it.get('topic_name', '')}`"
                     + (f", 용어 메모: {it['term_notes']}" if it.get("term_notes") else "") + "):")
            for label, c in zip("ABC", it["thumb_copies"]):
                L.append(f"- [{label}] {c.replace(chr(10), ' / ')}")
            rel_dir = os.path.relpath(it["asset_dir"], args.out).replace(os.sep, "/") if it.get("asset_dir") else ""
            imgs = " · ".join(f"[{os.path.basename(p)[:-4]}]({rel_dir}/{os.path.basename(p)})" for p in it.get("thumb_images", []))
            lay = " / ".join(l for l in it.get("thumb_layouts", []) if l)
            L.append(f"- 썸네일 이미지 ({it.get('thumb_mode', '')}{': ' + lay if lay else ''}): {imgs or '생성 안 됨'}"
                     f" (폴더 `{rel_dir}`, 편집 내역 `meta.json`)" + (f" — {it['thumb_notes']}" if it.get("thumb_notes") else ""))
            if it.get("bg_credit"):
                L.append(f"- 배경 사진: {it['bg_credit']}" + (f" — [원본 페이지]({it['bg_page']})" if it.get("bg_page") else ""))
            L.append(f"- 해시태그: {' '.join(it.get('hashtags', []))}")
            if it.get("thumb_final"):
                L.append(f"- 최종 선택(자동): [{os.path.basename(it['thumb_final'])}]({rel_dir}/{os.path.basename(it['thumb_final'])}) — {it.get('pick_note', '')}")
        if it.get("yt_query"):
            L.append(f"\n유튜브 (검색어 `{it['yt_query']}`, 식별어 `{it.get('yt_ids', '')}`, "
                     f"{it.get('yt_checked', '')}): {fmt_yt(it)}")
            for v in it.get("yt_related_list", [])[:3]:
                L.append(f"  - 같은 소재: [{v['title'][:70]}]({v['url']}) {v['views']:,}회 — {v['why']}")
            if it.get("yt_broad_title"):
                L.append(f"  - 참고(넓은 분야 관심도, 점수 미반영): [{it['yt_broad_title'][:70]}]"
                         f"({it['yt_broad_url']}) {it['yt_broad_views']:,}회")
        L.append("")

    # ---- 기록이 끝난 뒤 분석 섹션 추가
    L += ["---", "", "## 분석", ""]
    by, st, ev = {}, {}, {}
    for it in picks:
        by[it["field"]] = by.get(it["field"], 0) + 1
        st[it["status"]] = st.get(it["status"], 0) + 1
        k = it["evidence"].split(" (")[0].split("(")[0]
        ev[k] = ev.get(k, 0) + 1
    L.append("- 분야 분포: " + ", ".join(f"{k} {v}개" for k, v in sorted(by.items(), key=lambda x: -x[1])))
    L.append("- 해결 상태: " + ", ".join(f"{k} {v}개" for k, v in st.items()))
    L.append("- 근거 수준: " + ", ".join(f"{k} {v}개" for k, v in sorted(ev.items(), key=lambda x: -x[1])))
    judged = [it for it in picks if it.get("yt_basis") == "판단 가능"]
    L.append(f"- 유튜브 같은 소재 판단 가능: {len(judged)}/{len(picks)}개 (나머지는 수요·경쟁 점수 미반영)")
    blue = [it for it in judged if it.get("yt_recent") == 0 and it.get("yt_top_views", 0) > 50_000]
    if blue:
        L.append("\n**블루오션 후보 (같은 소재 영상 수요는 있는데 검색 표본 내 최근 영상 없음):**")
        L += [f"- {it.get('title_ko') or it['title']} (같은 소재 최고 {it['yt_top_views']:,}회)" for it in blue]
    red = [it for it in judged if (it.get("yt_recent") or 0) >= 3]
    if red:
        L.append("\n**경쟁 주의 (검색 표본 내 최근 같은 소재 영상 3개 이상 → 차별화 각도 필요):**")
        L += [f"- {it.get('title_ko') or it['title']}" for it in red]
    if excluded:
        L.append("\n**채널에 이미 있어 제외한 소재:**")
        L += [f"- {it['title']} ← {it['covered']}" for it in excluded[:15]]
    if checks["_channel"]:
        L.append(f"\n**채널 기존 영상:** " + " / ".join(checks["_channel"][:30]))
    L += ["", "**참고:** 유튜브 수치는 검색 결과 첫 페이지(표본)만 본 값입니다. 한국어 제목·요약은 무료 기계번역이라 "
          "어색할 수 있으니 영상 제목으로 쓰기 전에 다듬으세요."]

    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")
    return md_path, csv_path


# ------------------------------------------------------------------ main

TR_CACHE_FILE = os.path.join(HERE, "output", "translate_cache.json")


def load_json(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return default


def parse_stamp(s):
    for fmt in ("%Y%m%d_%H%M%S", "%Y-%m-%dT%H:%M:%S%z"):
        try:
            d = datetime.strptime(s, fmt)
            return d if d.tzinfo else d.astimezone(timezone.utc)
        except (ValueError, TypeError):
            pass
    return None


def main(argv=None):
    """명령줄 진입점. 다른 프로그램에서 부를 때는 main(["--pick", "10", ...]) 처럼 호출하면
    {"picks", "candidates", "report_md", "report_csv", "raw", "assets_dir", "checks"} 를 돌려줌."""
    ap = argparse.ArgumentParser(description="과학 미스터리 다큐 소재 탐색기 (무료)")
    ap.add_argument("--days", type=int, default=180, help="검색 기간(일), 기본 180")
    ap.add_argument("--pick", type=int, default=20, help="최종 선정 개수, 기본 20")
    ap.add_argument("--pool", type=int, default=45, help="유튜브로 확인할 후보 수 (pick 이상), 기본 45")
    ap.add_argument("--focus", default="고고학", help="가중치를 더 줄 분야 (기본: 고고학)")
    ap.add_argument("--mode", default="미스터리", choices=["미스터리", "발견"],
                    help="미스터리(기본): 풀린/안 풀린 수수께끼 · 발견: 수수께끼가 아니어도 새로 밝혀진 사실(첫 증거·가장 오래된·상식을 뒤집은 발견), 최신일수록 우대")
    ap.add_argument("--channel", default=CHANNEL_URL, help="중복 확인할 내 채널 주소")
    ap.add_argument("--no-youtube", action="store_true", help="유튜브 수요/경쟁 확인 생략")
    ap.add_argument("--no-translate", action="store_true", help="한국어 번역 생략")
    ap.add_argument("--no-thumbs", action="store_true", help="썸네일·해시태그 생성 생략")
    ap.add_argument("--font", help="썸네일 한국어 폰트 파일 (기본: 맑은 고딕 Bold 등 자동 탐색)")
    ap.add_argument("--bg", help="썸네일 배경 이미지 파일 (모든 소재에 사용)")
    ap.add_argument("--bg-dir", help="썸네일 배경 이미지 폴더 (소재별로 순서대로 사용)")
    ap.add_argument("--bg-credit", default="", help="배경 이미지 출처/이용 조건 메모 (source.txt 에 기록)")
    ap.add_argument("--bg-commons", action="store_true",
                    help="사용자 이미지가 없을 때 위키미디어 공용의 자유 이용 사진을 배경으로 받음 (켤 때만 동작, 출처·라이선스 자동 기록)")
    ap.add_argument("--assets-out", help="썸네일·해시태그 폴더 위치 (기본: output/assets_날짜)")
    ap.add_argument("--썸네일선택", default="없음", choices=["자동", "없음"],
                    help="소재마다 썸네일 3안 중 최종 1장을 자동으로 고름(점수) → 썸네일_최종.jpg. 직접 고르려면 썸네일_고르기.bat 로 폴더별로")
    ap.add_argument("--from-raw", help="저장된 raw_*.json 으로 오프라인 재채점 (네트워크 사용 안 함)")
    ap.add_argument("--mailto", default=os.environ.get("OPENALEX_MAILTO", ""),
                    help="OpenAlex 요청에 붙일 이메일 (선택, 요청 한도가 넉넉해짐; 환경변수 OPENALEX_MAILTO 로도 지정)")
    ap.add_argument("--out", default=os.path.join(HERE, "output"))
    args = ap.parse_args(argv)
    if args.days < 1 or args.days > 3650:
        ap.error("--days 는 1~3650 사이여야 합니다.")
    if args.pick < 1:
        ap.error("--pick 은 1 이상이어야 합니다.")
    if args.pool < args.pick:
        ap.error(f"--pool({args.pool}) 은 --pick({args.pick}) 이상이어야 합니다.")
    os.makedirs(args.out, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    offline = bool(args.from_raw)
    checks = {}

    # ---- 수집 (또는 저장본 불러오기: 오프라인 재현 모드)
    if offline:
        raw = load_json(args.from_raw, None)
        if raw is None:
            ap.error(f"저장본을 읽지 못했습니다: {args.from_raw}")
        items = raw["items"]
        yt_cache, tr_cache = raw.get("yt_cache", {}), raw.get("tr_cache", {})
        now = parse_stamp(raw.get("collected", "")) or datetime.now(timezone.utc)
        settings = raw.get("settings", {})
        days, focus = settings.get("days", raw.get("days", args.days)), settings.get("focus", args.focus)
        mode = settings.get("mode", args.mode)
        channel = raw.get("channel")
        rules = raw.get("exclude_rules")
        checks["수집"] = (f"오프라인 재현 — 저장본 {os.path.basename(args.from_raw)} "
                        f"(기준 시각 {now:%Y-%m-%d %H:%M}, 기간 {days}일, 분야 {focus}), 네트워크 사용 안 함")
        if rules is None:
            rules = load_excludes()
            checks["주의"] = "저장본에 제외 규칙이 없어 현재 channel_exclude.txt 사용 (구버전 저장본)"
        if channel is None:
            channel = []
            checks["채널 영상 목록"] = "저장본에 없음 (구버전 저장본) — 키워드 파일로만 판별"
        else:
            checks["채널 영상 목록"] = f"저장본 사용 {len(channel)}개"
    else:
        now, days, focus, mode = datetime.now(timezone.utc), args.days, args.focus, args.mode
        j_items, j_fail = collect_journals(days, args.mailto, DISCOVERY_SEARCHES if mode == "발견" else None)
        n_items, n_fail = collect_news()
        items, yt_cache = j_items + n_items, {}
        tr_cache = load_json(TR_CACHE_FILE, {})
        checks["논문 검색"] = f"{len(j_items)}건" + (f" · 실패 {len(j_fail)}건" if j_fail else "")
        if j_fail and not j_items:
            why = "요청 한도 초과(429) — 잠시 후 다시 실행하거나 --mailto 이메일을 지정하세요" if any("429" in f for f in j_fail) \
                else j_fail[0][:80]
            checks["논문 검색"] += f" ⚠ 저널 결과 없이 뉴스만으로 진행 ({why})"
        checks["뉴스 RSS"] = f"{len(n_items)}건 / 피드 {len(NEWS_FEEDS)}개 중 실패 {len(n_fail)}개" + \
            (f" ({'; '.join(f.split(':')[0] for f in n_fail)})" if n_fail else "")
        log("[3/5] 내 채널 영상 확인 중...")
        try:
            channel = channel_titles(args.channel)
            checks["채널 영상 목록"] = f"수집 성공 {len(channel)}개"
        except Exception as e:
            channel = []
            checks["채널 영상 목록"] = f"수집 실패 ({e}) — 키워드 파일로만 중복 판별"
        rules = load_excludes()
    checks["_days"], checks["_channel"] = days, channel

    groups = merge_items(items)
    cands = score_items(groups, days, focus, now, mode)
    log(f"  => 원본 {len(items)}건 → 병합 {len(groups)}개 → 미스터리 후보 {len(cands)}개")
    checks["후보"] = f"원본 {len(items)}건 → 중복 병합 {len(groups)}개 → 미스터리 후보 {len(cands)}개"

    # ---- 채널 중복 (키워드)
    checks["중복 키워드 규칙"] = f"{len(rules)}개 적용" if rules else "없음 — 키워드 중복 판별 안 함"
    checks["채널 제목 비교(한국어)"] = "자동 비교 안 함 (무료 모드) — 키워드 규칙에 없는 중복은 직접 확인"
    excluded, fresh = [], []
    for it in cands:
        c = is_covered(it, rules)
        if c:
            it["covered"] = "키워드 " + c
            excluded.append(it)
        else:
            fresh.append(it)

    # 분야가 한쪽으로 쏠리지 않게: focus 분야는 풀의 60%, 나머지 분야는 각 35%까지
    pool, per = [], {}
    for it in fresh:
        cap = args.pool * (0.6 if it["field"].startswith(focus) else 0.35)
        if per.get(it["field"], 0) < cap:
            pool.append(it)
            per[it["field"]] = per.get(it["field"], 0) + 1
        if len(pool) >= args.pool:
            break

    # ---- 식별어(고유명사·핵심어)는 유튜브를 건너뛰어도 계산 (소재명·해시태그·공용 사진 검색에 씀)
    for it in pool:
        if "yt_query" not in it:
            ids, content = search_terms(it["title"], it.get("summary", ""))
            it["yt_ids"], it["yt_query"] = ", ".join(ids), " ".join((ids[:2] + content)[:5])

    # ---- 유튜브
    if args.no_youtube:
        log("[4/5] 유튜브 확인 생략")
        checks["유튜브"] = "생략 (--no-youtube)"
        for it in pool:
            it["score"] = it["base_score"]
    else:
        log(f"[4/5] 유튜브 수요/경쟁 확인 중 ({len(pool)}개){' — 오프라인, 저장된 검색 결과만' if offline else ''}...")
        apply_youtube(pool, yt_cache, offline)
        ok = sum(it["yt_status"].startswith("확인") for it in pool)
        judged = sum(it.get("yt_basis") == "판단 가능" for it in pool)
        checks["유튜브"] = (f"{len(pool)}개 중 검색 확인 {ok}개, 같은 소재 영상으로 판단 가능 {judged}개 "
                         f"(나머지는 수요·경쟁 점수 미반영)")
    pool.sort(key=lambda x: (-x["score"], x["title"]))

    # ---- 선정 + 훅 제목 틀 + 한국어 번역
    log("[5/5] 선정 · 훅 제목 틀 · 한국어 번역...")
    picks = pool[: args.pick]
    for it in picks:
        it["hooks"] = template_titles(it)
    if len(picks) < args.pick:
        checks["선정 부족"] = (f"{args.pick}개 요청, {len(picks)}개 선정 — 중복 제외 후 후보 부족. "
                           f"--days 또는 --pool 을 늘려보세요.")
    checks["훅 제목"] = "규칙 기반 틀 (해결 상태별, [소재] 자리 채워 쓰기)"
    if args.no_translate:
        checks["한국어 번역"] = "생략 (--no-translate)"
    else:
        ok, fail = translate_picks(picks, tr_cache, offline)
        checks["한국어 번역"] = (f"무료 기계번역(MyMemory/Google) {ok}개 성공" + (f", {fail}개 실패" if fail else "")
                             + (" — 오프라인: 저장된 번역만 사용" if offline else ""))
        if not offline:
            os.makedirs(os.path.dirname(TR_CACHE_FILE), exist_ok=True)
            with open(TR_CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(tr_cache, f, ensure_ascii=False)

    # ---- 썸네일 문구 · 이미지 · 해시태그 (무료, 로컬)
    if args.no_thumbs:
        checks["썸네일/해시태그"] = "생략 (--no-thumbs)"
    else:
        try:
            import thumbs
        except ImportError as e:
            thumbs = None
            checks["썸네일/해시태그"] = f"생략 — thumbs.py 를 불러오지 못함 ({e}); 소재 탐색 결과는 그대로 사용 가능"
        if thumbs:
            bgs = [args.bg] if args.bg else []
            if args.bg_dir and os.path.isdir(args.bg_dir):
                bgs += sorted(os.path.join(args.bg_dir, f) for f in os.listdir(args.bg_dir)
                              if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp")))
            assets_root = args.assets_out or os.path.join(args.out, f"assets_{stamp}")
            tr = (lambda w: translate_ko(w, tr_cache, offline)) if not args.no_translate else None
            try:
                use_commons = args.bg_commons and not offline
                if args.bg_commons and offline:
                    checks["위키미디어 공용"] = "오프라인 재현 모드라 건너뜀 (네트워크 사용 안 함)"
                sm = thumbs.make_assets(picks, assets_root, args.font, bgs, args.bg_credit, translate=tr,
                                        commons=use_commons, bg_dir=args.bg_dir, pick_mode=args.썸네일선택)
                if use_commons:
                    checks["위키미디어 공용"] = (f"{sm['commons_ok']}/{sm['topics']}개 소재에 자유 이용 사진 사용 "
                                            f"(출처·라이선스는 각 폴더 source.txt) — 나머지는 기본 그래픽")
                checks["썸네일/해시태그"] = (
                    f"{sm['topics']}개 소재 · 이미지 {sm['images']}장 → {os.path.relpath(assets_root, HERE)} · "
                    f"실사 편집 {sm['photo_topics']}개(비교형 가능 {sm['compare_topics']}개) · 기본 그래픽(임시) {sm['graphic_topics']}개 · "
                    f"사진 출처: {sm['bg']} · 폰트: {os.path.basename(sm['font'])}"
                    + (" · rembg 배경 제거 사용" if sm.get("rembg") else " · rembg 미설치(배경 제거 생략)")
                    + (f" · 최종 자동 선택 {sm.get('auto_picked', 0)}개(썸네일_최종.jpg)" if args.썸네일선택 == "자동"
                       else " · 최종 선택 안 함(썸네일_고르기.bat 로 고르거나 --썸네일선택 자동)")
                    + ("" if sm["pillow"] else " · Pillow 없음(문구·해시태그 텍스트만 저장)")
                    + (" · YAKE 키워드 보조 사용" if sm["yake"] else ""))
            except Exception as e:
                checks["썸네일/해시태그"] = f"실패 ({e}) — 소재 탐색 결과는 그대로 사용 가능"

    # ---- 저장: 수집 원본(재현용 스냅샷) + 리포트
    if not offline:
        raw_path = unique_path(os.path.join(args.out, f"raw_{stamp}.json"))
        with open(raw_path, "w", encoding="utf-8") as f:
            json.dump({"version": 3, "collected": stamp, "settings": {"days": days, "focus": focus, "mode": mode},
                       "channel": channel, "exclude_rules": rules,
                       "items": items, "yt_cache": yt_cache, "tr_cache": tr_cache},
                      f, ensure_ascii=False)
        checks["재현용 저장본"] = os.path.relpath(raw_path, HERE) + " (--from-raw 로 오프라인 재현)"
    md, csv_path = write_report(picks, cands, excluded, checks, args, stamp)
    log(f"\n완료!\n  리포트: {md}\n  CSV:    {csv_path}\n")
    for i, it in enumerate(picks, 1):
        print(f"{i:2}. [{it['score']:5}] {it['status']:<5} {(it.get('title_ko') or it['title'])[:60]}")
    return {"picks": picks, "candidates": cands, "excluded": excluded, "report_md": md, "report_csv": csv_path,
            "raw": checks.get("재현용 저장본", ""), "assets_dir": (picks[0]["asset_dir"] and os.path.dirname(picks[0]["asset_dir"])) if picks and picks[0].get("asset_dir") else "",
            "checks": {k: v for k, v in checks.items() if not k.startswith("_")}}


if __name__ == "__main__":
    main()
