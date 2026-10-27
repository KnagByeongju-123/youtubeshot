r"""한국사 미스터리 소재 탐색 (무료, 열쇠 없이) → 리포트·기획메모, 원하면 실화\주제목록.txt 에 추가

  py -3.11 -X utf8 한국사_소재탐색.py                    # 최근 365일 한국어 뉴스·해외 논문 + 유튜브 인기 조사 → 리포트
  py -3.11 -X utf8 한국사_소재탐색.py --days 730 --편수 20
  py -3.11 -X utf8 한국사_소재탐색.py --주제목록 3         # 상위 3개를 '[실화] 한국사 미스터리' 로 실화\주제목록.txt 에 추가
  py -3.11 -X utf8 한국사_소재탐색.py --no-youtube        # 유튜브 조사 생략 (빠름)

흐름 (실화_소재탐색.py 의 부품 소재탐색/topic_finder.py 를 그대로 씀: 인터넷 받기·유튜브 검색·조회수 읽기·번역)
  1) 구글 뉴스 RSS 를 한국어 검색어(발굴·출토·판독·인골 분석·실록 기록…)로 → 최근 발굴·연구 기사
  2) OpenAlex(공개 논문 DB)를 영어 낱말(Silla, Goguryeo, Korean ancient DNA…)로 → 해외 논문, 제목은 무료 번역
  3) 같은 소식을 다룬 기사는 하나로 묶고(보도한 언론사 수 = 화제성), 수수께끼·최초·판독 같은 낱말과 한국사 낱말로 점수
  4) 유튜브: '한국사 미스터리' 같은 말로 많이 본 영상 → 인기 낱말 순위 / 후보마다 같은 소재 영상의 최고 조회수·최근 12개월 개수
  5) 내 채널 영상 제목과 겹치면 표시
  결과: output\장문\_소재탐색\<날짜>_한국사\한국사_소재리포트.md (+ 소재별 기획메모 폴더, 수집 원본 json)
KCI(국내 논문)·한국고전종합DB(실록 원문)는 공개 API 신청(열쇠)이 필요해 아직 안 붙임"""
import argparse
import json
import math
import os
import re
import sys
import time
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)
sys.path.insert(0, os.path.join(HERE, "소재탐색"))
import topic_finder as tf  # noqa: E402

GENRE = "[실화] 한국사 미스터리"
SEED = os.path.join(HERE, "실화", "주제목록.txt")
LOG_FILE = os.path.join(HERE, "장문_진행기록.txt")
TR_CACHE = os.path.join(HERE, "소재탐색", "output", "translate_cache.json")

# 구글 뉴스 검색어 (한국어). 'when:<일>d' 로 기간을 붙임
NEWS_QUERIES = [
    "발굴 최초 확인", "고분 발굴 출토", "유적 발굴 수수께끼", "국가유산청 발굴조사 성과", "삼국시대 인골 분석",
    "신라 고분 발굴", "가야 고분 출토", "백제 유적 발견", "고구려 유적", "발해 유적 발굴", "고려 수중발굴",
    "조선왕조실록 기록 새로", "목간 판독", "암각화 연대", "고대 DNA 한반도", "고문서 발견 처음", "비석 판독 새로",
]
# OpenAlex 검색어 (영어). 결과 중 한국 관련 낱말이 있는 것만 남김
PAPER_QUERIES = [
    "Silla", "Goguryeo", "Baekje", "Gaya confederacy", "Balhae", "Goryeo dynasty", "Joseon dynasty",
    "Korean peninsula archaeology", "Korean ancient DNA", "Three Kingdoms Korea tomb", "Mumun Korea", "Korean Neolithic",
]
PAPER_KOREA = re.compile(r"\bkorea|silla|goguryeo|koguryo|baekje|paekche|gaya|kaya|balhae|parhae|goryeo|koryo|joseon|"
                         r"choson|gyeongju|gimhae|mumun|chulmun|jeju", re.I)
# 유튜브 인기 조사 검색어
YT_TREND_QUERIES = ["한국사 미스터리", "한국사 미스터리 풀리지 않은", "조선 미스터리", "삼국시대 미스터리",
                    "고대 한국 미스터리", "역사 미스터리 한국", "발굴 미스터리 한국", "조선왕조실록 기이한 기록"]

# 한국사 낱말 (점수·검색어·인기 낱말 세기에 씀). 앞쪽일수록 '시대·나라'
ERA = ["고조선", "부여", "고구려", "백제", "신라", "가야", "발해", "통일신라", "고려", "조선", "삼국시대", "삼한", "마한", "진한",
       "변한", "탐라", "옥저", "동예", "구석기", "신석기", "청동기", "철기", "대한제국", "일제강점기"]
THINGS = ["고분", "왕릉", "금관", "고인돌", "암각화", "목간", "토기", "인골", "순장", "산성", "사찰", "석탑", "불상", "난파선",
          "보물선", "실록", "승정원일기", "비석", "비문", "벽화", "청자", "백자", "적석총", "패총", "수중", "금동", "향로", "칼",
          "갑옷", "왕관", "무덤", "궁궐", "도성", "문자", "이두", "향가", "지도", "천문", "혜성", "운석", "UFO", "괴물", "귀신"]
PEOPLE = ["단군", "주몽", "광개토", "장수왕", "을지문덕", "연개소문", "근초고왕", "무령왕", "의자왕", "계백", "김유신", "선덕여왕",
          "문무왕", "김춘추", "원효", "의상", "최치원", "장보고", "대조영", "왕건", "강감찬", "서희", "최무선", "이성계", "정도전",
          "세종", "장영실", "연산군", "광해군", "사도세자", "정조", "이순신", "허준", "정약용", "김정호", "흥선대원군", "명성황후",
          "고종", "처용", "삼별초", "화랑", "궁예", "견훤", "문순득", "하멜"]
HIST_TERMS = ERA + THINGS + PEOPLE
MYSTERY_KO = [(r"수수께끼|미스터리|미스테리|미궁", 4), (r"비밀", 2), (r"정체", 3), (r"베일", 3), (r"최초|처음|첫 ", 3),
              (r"가장 오래된|最古", 3), (r"밝혀|규명|드러나|드러났", 3), (r"풀렸|풀어|해독|판독", 4), (r"논란|논쟁", 2),
              (r"의문|미스터리", 2), (r"유일|국내 첫|세계 최초", 3), (r"DNA|유전체|인골 분석|연대 측정", 3),
              (r"뒤집|새로 쓰|다시 써", 4), (r"사라진|실종|행방", 3), (r"기이한|괴이", 3)]
NOISE_KO = re.compile(r"축제|관광|공연|입장료|채용|모집|할인|분양|선거|주가|드라마|예능|맛집|체험 프로그램|기념품|굿즈|"
                      r"개관 기념|입찰|공모전|이벤트|날씨|부고|인사\]|게임|웹툰|뮤지컬|콘서트|여행|떠나는|나들이|물결|꽃|해바라기|단풍|야경|"
                      r"성료|프로그램|강좌|강연|특강|교육생|아카데미|홍보|캠페인|협약|업무협약|MOU|예산|국비|착공|준공|정비사업")
# 외국 이야기 (한국사 낱말이 없으면 뺌: '인도네시아 암각화' 같은 것)
FOREIGN = re.compile(r"인도네시아|이집트|페루|멕시코|그리스|로마|튀르키예|터키|이스라엘|영국|프랑스|독일|스페인|이탈리아|"
                     r"미국|호주|아프리카|인도|몽골|베트남|캄보디아|남미|유럽|중동|시베리아")
STOP_KO = set("""있다 했다 밝혔다 위해 대한 통해 관련 이번 지난 오는 올해 최근 등을 등의 함께 따르면 것으로 있는 없는 하는 된다
이다 에서 으로 까지 부터 처럼 보다 한국 국내 연구 연구팀 발표 결과 확인 조사 사업 진행 개최 예정 기자 뉴스 사진 영상 단독
속보 종합 전문가 교수 박사 대표 위원회 시 군 구 도 년 월 일""".split())


def log(x):
    line = f"[{time.strftime('%H:%M')}] [한국사 소재탐색] {x}"
    print(line, flush=True)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError:
        pass


def hist_hits(text):
    return [w for w in HIST_TERMS if w in text]


def nouns(text):
    """한글 낱말(2자 이상) — 조사 떼고, 흔한 말 빼고"""
    out = []
    for w in re.findall(r"[가-힣A-Za-z0-9]{2,}", text):
        w = re.sub(r"(에서|으로|에게|까지|부터|처럼|보다|이다|이며|하고|했다|한다|된|된다|되어|에|의|을|를|이|가|은|는|과|와|도|로|서)$", "", w)
        if len(w) >= 2 and w not in STOP_KO and not w.isdigit():
            out.append(w)
    return list(dict.fromkeys(out))


# ------------------------------------------------------------------ 1. 한국어 뉴스 (구글 뉴스 RSS)

def collect_news(days):
    log(f"[1/5] 한국어 뉴스 수집 (구글 뉴스, 최근 {days}일, 검색어 {len(NEWS_QUERIES)}개)...")

    def one(q):
        url = ("https://news.google.com/rss/search?" + urllib.parse.urlencode(
            {"q": f"{q} when:{days}d", "hl": "ko", "gl": "KR", "ceid": "KR:ko"}))
        rows, err = tf.fetch_feed("구글뉴스:" + q, url)
        time.sleep(0.5)
        return q, rows, err

    items, failed = [], []
    with ThreadPoolExecutor(4) as ex:
        for q, rows, err in ex.map(one, NEWS_QUERIES):
            if err:
                failed.append(err)
                log("  ! " + err[:120])
                continue
            n = 0
            for r in rows:
                title = r["title"]
                outlet = ""
                m = re.match(r"(.+?)\s+-\s+([^-]+)$", title)    # '제목 - 언론사'
                if m:
                    title, outlet = m.group(1).strip(), m.group(2).strip()
                title = re.sub(r"^[^-]{2,15}\s-\s", "", title)      # 앞에 붙은 '코리아넷뉴스 - ' 같은 이름
                if not title or NOISE_KO.search(title) or not hist_hits(title):
                    continue
                if FOREIGN.search(title) and not any(w in title for w in ERA + PEOPLE + ["대한제국", "한국", "한반도", "우리"]):
                    continue
                items.append({"origin": "뉴스", "title": title, "title_ko": title, "outlet": outlet, "url": r["url"],
                              "date": r["date"], "summary": "", "query": q})
                n += 1
            log(f"  - '{q}': {n}건")
    return items, failed


# ------------------------------------------------------------------ 2. 해외 논문 (OpenAlex)

def collect_papers(days, mailto, tr_cache, translate=True):
    log(f"[2/5] 해외 논문 검색 (OpenAlex, 최근 {days}일)...")
    since = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")
    items, failed = [], []
    for q in PAPER_QUERIES:
        params = {"search": q, "filter": f"from_publication_date:{since},type:article", "per-page": "25",
                  "sort": "relevance_score:desc",
                  "select": "id,title,publication_date,primary_location,cited_by_count,doi,abstract_inverted_index"}
        if mailto:
            params["mailto"] = mailto
        try:
            res = json.loads(tf.http_get("https://api.openalex.org/works?" + urllib.parse.urlencode(params), retries=0))["results"]
        except Exception as e:
            failed.append(f"{q}: {e}")
            log(f"  ! '{q}': {e}")
            if "429" in str(e):      # 요청 한도 초과면 나머지는 기다리지 않고 건너뜀 (--mailto 이메일을 주면 한도가 넉넉해짐)
                log("  ! OpenAlex 요청 한도 초과 → 논문 검색은 건너뜀 (잠시 뒤 다시 하거나 --mailto 이메일 지정)")
                break
            continue
        n = 0
        for w in res:
            title = tf.clean(w.get("title") or "")
            abstract = tf.openalex_abstract(w.get("abstract_inverted_index"))[:600]
            if not title or not PAPER_KOREA.search(title + " " + abstract):
                continue
            src = ((w.get("primary_location") or {}).get("source") or {}).get("display_name", "")
            items.append({"origin": "논문", "title": title, "title_ko": "", "outlet": src, "url": w.get("doi") or w.get("id"),
                          "date": w.get("publication_date", ""), "summary": abstract, "cited": w.get("cited_by_count", 0),
                          "query": q})
            n += 1
        log(f"  - '{q}': {n}건")
        time.sleep(0.3)
    if translate:
        for it in items:
            it["title_ko"] = tf.translate_ko(it["title"], tr_cache)[0]
    return items, failed


# ------------------------------------------------------------------ 3. 묶기 + 점수

def keyset(it):
    t = it.get("title_ko") or it["title"]
    return set(hist_hits(t)) | set(nouns(t))


def merge(items):
    """같은 소식(낱말이 절반 이상 겹침)은 하나로 — 보도한 곳 수를 셈"""
    groups = []
    for it in sorted(items, key=lambda x: x.get("date", ""), reverse=True):
        ks = keyset(it)
        for g in groups:
            inter = len(ks & g["keys"])
            if ks and inter >= 2 and inter / min(len(ks), len(g["keys"])) >= 0.5:
                g["items"].append(it)
                g["keys"] |= ks
                break
        else:
            groups.append({"items": [it], "keys": ks})
    out = []
    for g in groups:
        head = max(g["items"], key=lambda x: (x["origin"] == "논문", len(x.get("title_ko") or "")))
        outlets = {x.get("outlet") for x in g["items"] if x.get("outlet")}
        out.append({**head, "links": [(x.get("outlet", ""), x["url"], x["origin"]) for x in g["items"]][:8],
                    "coverage": max(1, len(outlets)), "keys": sorted(g["keys"])})
    return out


def score(groups, now):
    for g in groups:
        text = (g.get("title_ko") or "") + " " + g["title"] + " " + (g.get("summary_ko") or "")
        ms, hits = 0, []
        for pat, w in MYSTERY_KO:
            m = re.search(pat, text)
            if m:
                ms += w
                hits.append(m.group(0))
        hh = hist_hits(text)
        age = None
        try:
            age = (now - datetime.fromisoformat(g["date"]).replace(tzinfo=timezone.utc)).days if g.get("date") else None
        except ValueError:
            pass
        rec = 3 if age is not None and age <= 90 else (1 if age is not None and age <= 365 else 0)
        paper = (2 + min(3, math.log10(g.get("cited", 0) + 1) * 2)) if g["origin"] == "논문" else 0
        g["mystery_hits"], g["hist"] = hits, hh
        g["base_score"] = round(ms + min(8, 2 * len(hh)) + min(4, g["coverage"] - 1) * 1.5 + rec + paper, 1)
        g["score"] = g["base_score"]
    return sorted(groups, key=lambda x: -x["base_score"])


# ------------------------------------------------------------------ 4. 유튜브

def yt_query(g):
    hh = [w for w in hist_hits(g.get("title_ko") or g["title"])]
    rest = [w for w in nouns(g.get("title_ko") or "") if w not in hh and not any(w in h or h in w for h in hh)]
    return " ".join((hh[:2] + rest)[:3]), (hh[:2] + rest)[:4]


def yt_rows(raw):
    return [{**v, "views": tf.parse_views(v["views_text"]), "months": tf.months_ago(v["age_text"]),
             "url": f"https://www.youtube.com/watch?v={v['id']}"} for v in raw]


def youtube_candidate(g, cache):
    q, terms = yt_query(g)
    g["yt_query"] = q
    if not q:
        g["yt_status"] = "검색어 없음"
        return
    st, raw, _ = tf.fetch_search(q, cache, False)
    if st != "확인":
        g["yt_status"] = st
        return
    rel = [v for v in yt_rows(raw) if sum(t in v["title"] for t in terms) >= min(2, len(terms))]
    recent = [v for v in rel if v["months"] is not None and v["months"] < 12]
    top = max(rel, key=lambda v: v["views"]) if rel else None
    g.update(yt_status=f"확인(표본 {len(raw)}개)", yt_related=len(rel), yt_recent=len(recent),
             yt_top_views=top["views"] if top else 0, yt_top_title=top["title"] if top else "",
             yt_top_url=top["url"] if top else "", yt_list=[{k: v[k] for k in ("title", "views", "url")} for v in
                                                            sorted(rel, key=lambda v: -v["views"])[:3]])
    if top:
        demand = math.log10(top["views"] + 1) * 2
        gap = 6 if len(recent) == 0 else (3 if len(recent) <= 2 else -3)
        g["yt_note"] = "같은 소재 영상 있음" + (" · 최근 1년 새 영상 없음(빈자리)" if not recent else f" · 최근 1년 {len(recent)}개")
    else:
        demand, gap = 0, 4
        g["yt_note"] = "같은 소재 영상 없음 (빈자리지만 수요도 미상)"
    g["score"] = round(g["base_score"] + demand + gap, 1)


def youtube_trend(cache):
    log(f"[4/5] 유튜브 인기 한국사 미스터리 조사 (검색어 {len(YT_TREND_QUERIES)}개)...")
    vids = {}
    for q in YT_TREND_QUERIES:
        st, raw, _ = tf.fetch_search(q, cache, False)
        log(f"  - '{q}': {st} {len(raw)}개")
        for v in yt_rows(raw):
            if v["id"]:
                vids.setdefault(v["id"], v)
    vids = sorted(vids.values(), key=lambda v: -v["views"])
    weight = {}
    for v in vids:
        for w in hist_hits(v["title"]):
            weight.setdefault(w, [0.0, 0])
            weight[w][0] += math.log10(v["views"] + 10)
            weight[w][1] += 1
    terms = sorted(((w, round(s, 1), n) for w, (s, n) in weight.items()), key=lambda x: -x[1])
    return vids, terms


# ------------------------------------------------------------------ 5. 리포트

def memo_md(g, topic):
    L = [f"# 기획메모 — {topic}", "", f"- 소재: {GENRE}", f"- 원래 제목: {g['title']}",
         f"- 번역 제목: {g['title_ko']}" if g["origin"] == "논문" and g.get("title_ko") else "",
         f"- 날짜: {g.get('date', '')} · 보도한 곳 {g['coverage']}곳 · 점수 {g['score']}",
         f"- 한국사 낱말: {', '.join(g['hist'])} · 단서 낱말: {', '.join(g['mystery_hits']) or '-'}", "",
         "## 출처 (대본 전에 반드시 원문 확인)"]
    L += [f"- {k} ({s}): {u}" for s, u, k in g["links"]]
    if g.get("summary"):
        L += ["", "## 논문 요약 (원문)", g["summary"][:600]]
    if g.get("yt_query"):
        L += ["", "## 유튜브 경쟁", f"- 검색어 '{g['yt_query']}' · {g.get('yt_note', g.get('yt_status', ''))}"
              + (f" · 같은 소재 최고 {g.get('yt_top_views', 0):,}회" if g.get("yt_top_views") else "")]
        L += [f"  - {v['title'][:60]} ({v['views']:,}회) {v['url']}" for v in g.get("yt_list", [])]
    L += ["", "## 대본 작가에게", "- 뉴스 한 건으로 시작한 소재. 발굴 기관 발표·논문·『삼국사기』『실록』 같은 원 기록으로 사실을 다시 확인할 것.",
          "- 확정된 사실과 학자들의 해석(가설)을 나눠 말하고, 정설이 없으면 그렇다고 밝힐 것."]
    return "\n".join(x for x in L if x != "")


def report(path, picks, vids, terms, checks, channel_hits):
    L = [f"# 한국사 미스터리 소재 탐색 — {time.strftime('%Y-%m-%d %H:%M')}", "", "## 확인 상태"]
    L += [f"- {k}: {v}" for k, v in checks.items()]
    L += ["", "## 추천 소재 (점수 순)", "", "| # | 점수 | 소재 | 날짜 | 보도 | 유튜브 경쟁 | 출처 |", "|---|---|---|---|---|---|---|"]
    for i, g in enumerate(picks, 1):
        t = (g.get("title_ko") or g["title"]).replace("|", "/")
        mark = " ⚠채널에 비슷한 영상" if g["key"] in channel_hits else ""
        yt = g.get("yt_note") or g.get("yt_status", "-")
        if g.get("yt_top_views"):
            yt += f" (최고 {g['yt_top_views']:,}회)"
        L.append(f"| {i} | {g['score']} | {t[:60]}{mark} | {g.get('date', '')} | {g['origin']} {g['coverage']}곳 | {yt} | [{g['links'][0][0] or '링크'}]({g['links'][0][1]}) |")
    if terms:
        L += ["", "## 유튜브에서 많이 보는 한국사 미스터리 낱말", "(조회수가 클수록 무겁게 센 값. 이 낱말이 들어간 소재는 사람들이 많이 찾음)", ""]
        L += [f"- **{w}** — 점수 {s} · 영상 {n}개" for w, s, n in terms[:25]]
    if vids:
        L += ["", "## 유튜브 인기 영상 (한국사 미스터리 검색, 조회수 순)", ""]
        L += [f"- {v['views']:,}회 · {v['age_text'] or '-'} · [{v['title'][:70]}]({v['url']})" for v in vids[:30]]
    L += ["", "---", "_자동으로 모은 참고자료입니다. 점수는 '단서 낱말·한국사 낱말·보도 수·최신성·유튜브 빈자리'를 더한 값이고, 사실 확인은 대본 단계에서 다시 합니다._"]
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")


def safe(s):
    return re.sub(r"[\\/:*?\"<>|\s]+", "_", s).strip("_")[:30] or "topic"


def main():
    ap = argparse.ArgumentParser(description="한국사 미스터리 소재 탐색 (무료)")
    ap.add_argument("--days", type=int, default=365, help="뉴스·논문 기간(일), 기본 365")
    ap.add_argument("--편수", type=int, default=15, help="리포트에 올릴 추천 소재 수, 기본 15")
    ap.add_argument("--pool", type=int, default=30, help="유튜브로 경쟁을 확인할 후보 수, 기본 30")
    ap.add_argument("--주제목록", type=int, default=0, help="상위 N개를 실화\\주제목록.txt 에 추가 (기본 0 = 추가 안 함)")
    ap.add_argument("--no-youtube", action="store_true", help="유튜브 조사 생략")
    ap.add_argument("--no-papers", action="store_true", help="해외 논문 검색 생략")
    ap.add_argument("--mailto", default=os.environ.get("OPENALEX_MAILTO", ""), help="OpenAlex 요청에 붙일 이메일 (선택)")
    a = ap.parse_args()
    stamp = time.strftime("%Y%m%d_%H%M%S")
    out = os.path.join(HERE, "output", "장문", "_소재탐색", stamp + "_한국사")
    os.makedirs(out, exist_ok=True)
    tr_cache = tf.load_json(TR_CACHE, {})
    checks = {}

    news, nf = collect_news(a.days)
    checks["한국어 뉴스"] = f"{len(news)}건 (검색어 {len(NEWS_QUERIES)}개 중 실패 {len(nf)}개)"
    papers, pf = ([], []) if a.no_papers else collect_papers(a.days, a.mailto, tr_cache)
    checks["해외 논문"] = "생략" if a.no_papers else f"{len(papers)}건 (실패 {len(pf)}개)"
    log("[3/5] 같은 소식 묶기 · 점수...")
    groups = score(merge(news + papers), datetime.now(timezone.utc))
    for g in groups:
        g["key"] = re.sub(r"[^가-힣a-z0-9]", "", (g.get("title_ko") or g["title"]).lower())[:40]
    checks["후보"] = f"원본 {len(news) + len(papers)}건 → 묶은 뒤 {len(groups)}개"

    channel_hits = set()
    try:
        titles = tf.channel_titles(tf.CHANNEL_URL)
        for g in groups:
            ks = [k for k in g["hist"] + nouns(g.get("title_ko") or "")[:4] if len(k) >= 2]
            if any(sum(k in t for k in ks) >= 2 for t in titles):
                channel_hits.add(g["key"])
        checks["내 채널"] = f"영상 {len(titles)}개와 비교 · 비슷한 소재 {len(channel_hits)}개 표시"
    except Exception as e:
        checks["내 채널"] = f"확인 실패 ({e})"

    pool = [g for g in groups if g["key"] not in channel_hits][: a.pool]
    vids, terms, yt_cache = [], [], {}
    if a.no_youtube:
        checks["유튜브"] = "생략"
    else:
        vids, terms = youtube_trend(yt_cache)
        log(f"[5/5] 후보 {len(pool)}개 유튜브 경쟁 확인...")
        for g in pool:
            youtube_candidate(g, yt_cache)
        top_terms = {w for w, _, _ in terms[:10]}
        for g in pool:      # 사람들이 많이 보는 낱말이 들어간 소재는 조금 더
            g["score"] = round(g["score"] + 2 * len(top_terms & set(g["hist"])), 1)
        checks["유튜브"] = f"인기 영상 {len(vids)}개 · 후보 {len(pool)}개 경쟁 확인"
    pool.sort(key=lambda g: -g["score"])
    picks = pool[: a.편수]

    lines = []
    for i, g in enumerate(picks, 1):
        topic = (g.get("title_ko") or g["title"]).strip()
        d = os.path.join(out, f"{i:02d}_{safe(topic)}")
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "기획메모.md"), "w", encoding="utf-8") as f:
            f.write(memo_md(g, topic))
        g["folder"] = d
        if i <= a.주제목록:
            lines.append(f"{GENRE} | {topic[:35]} | {d}")
    rp = os.path.join(out, "한국사_소재리포트.md")
    report(rp, picks, vids, terms, checks, channel_hits)
    with open(os.path.join(out, "수집원본.json"), "w", encoding="utf-8") as f:
        json.dump({"checks": checks, "groups": groups, "trend_videos": vids[:100], "trend_terms": terms}, f, ensure_ascii=False, indent=1)
    os.makedirs(os.path.dirname(TR_CACHE), exist_ok=True)
    with open(TR_CACHE, "w", encoding="utf-8") as f:
        json.dump(tr_cache, f, ensure_ascii=False)
    if lines:
        with open(SEED, "a", encoding="utf-8") as f:
            f.write(f"\n# ── 한국사 소재탐색 자동 추가 {time.strftime('%Y-%m-%d %H:%M')} (제목은 기사 제목 그대로 — 질문형으로 다듬어 쓰세요) ──\n"
                    + "\n".join(lines) + "\n")
        log(f"📑 실화\\주제목록.txt 에 {len(lines)}줄 추가")
    log(f"✅ 완료 → {rp}")
    for i, g in enumerate(picks, 1):
        print(f"{i:2}. [{g['score']:5}] {(g.get('title_ko') or g['title'])[:60]}  ({g.get('yt_note', '')})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
