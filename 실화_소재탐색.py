r"""실화 소재 탐색 → 주제 목록·기획메모·썸네일을 장문 제작(make_longdoc.py --실화)의 시작 단계로 넘김 (무료)

  py -3.11 -X utf8 실화_소재탐색.py                       # 최근 180일 저널·뉴스에서 5편 고르고 실화_주제목록.txt 에 추가
  py -3.11 -X utf8 실화_소재탐색.py --편수 3 --days 365     # 1년치에서 3편
  py -3.11 -X utf8 실화_소재탐색.py --발견                 # 최신 발견 모드: 최근 90일, 수수께끼가 아니어도 새로 밝혀진 사실 (실화_최신발견탐색.bat)
  py -3.11 -X utf8 실화_소재탐색.py --bg-commons           # 썸네일 배경에 위키미디어 공용 자유 이용 사진 사용 (켤 때만, 출처 자동 기록)
  py -3.11 -X utf8 실화_소재탐색.py --목록만               # 실화_주제목록.txt 는 건드리지 않고 기획메모·리포트만 만듦
  py -3.11 -X utf8 실화_소재탐색.py --규칙제목             # Claude Code 로 한국어 주제 다듬기 생략 (규칙 기반 제목)

흐름
  1) 소재탐색/topic_finder.py 가 주요 과학저널(OpenAlex)·과학/고고학 뉴스에서 '풀리지 않던 수수께끼' 연구를 모아
     해결 상태(해결 근거/가설 제안/미해결)를 나누고, 내 채널 중복을 빼고, 유튜브 수요·경쟁을 보고 순위를 매김
  2) 상위 N편의 한국어 주제(35자 이내, 질문·반전형)를 정함 — Claude Code 가 있으면 다듬고, 없으면 규칙 기반
  3) 소재별 폴더 output\장문\_소재탐색\<날짜>\NN_이름\ 에 기획메모.md(근거 링크·해결 상태·⚠주의·훅·해시태그·구성)·썸네일 3안·해시태그 저장
  4) 실화_주제목록.txt 끝에 '소재 | 주제 | 기획메모 폴더' 줄을 추가 → 실화_연속제작.bat 이 순서대로 만들 때
     기획메모가 대본 AI의 최우선 참고자료로 들어가고, 영상 완성 뒤 썸네일 3안이 _썸네일_후보 폴더에 외부 후보로 들어감

비용: 무료 (OpenAlex·RSS·유튜브 공개 페이지·무료 번역·위키미디어 공용). 한국어 주제 다듬기만 이 PC의 Claude Code 를 씀(선택).
"""
import argparse
import importlib.util
import json
import os
import re
import shutil
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)
TF_DIR = os.path.join(HERE, "소재탐색")
sys.path.insert(0, TF_DIR)
SEED = os.path.join(HERE, "실화_주제목록.txt")
GENRE = "[실화] 과학이 밝혀낸 미스터리"
DISCOVERY_GENRE = "[실화] 최근 밝혀진 과학 발견"   # --발견: 수수께끼가 아니어도 최근 새로 밝혀진 사실
HISTORY = os.path.join(HERE, "output", "장문", "_소재탐색", "넘긴_소재_기록.json")
LOG_FILE = os.path.join(HERE, "장문_진행기록.txt")

STATUS_RULE = {
    "해결 근거": "최근 연구가 답을 제시한 소재. 그래도 '완전히 끝났다'식 단정은 피하고 남은 의문을 마지막에 둘 것.",
    "가설 제안": "⚠ 아직 '유력한 가설' 단계. 제목·대본·설명란에서 '밝혀졌다/풀렸다'로 단정하지 말고 '~일까?', '유력한 답' 수준으로. 반론·한계를 반드시 한 챕터 이상.",
    "미해결": "⚠ 아직 풀리지 않은 수수께끼. 경쟁 가설 2~3개를 비교하고 '왜 아직 못 풀었나'를 중심으로. 해결됐다는 표현 금지.",
    "확인 필요": "⚠ 해결 상태를 자동으로 판정하지 못함. 웹 조사에서 먼저 확인하고 구성을 정할 것.",
}


def log(x):
    line = f"[{time.strftime('%H:%M')}] [소재탐색] {x}"
    print(line, flush=True)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError:
        pass


# ------------------------------------------------------------------ 한국어 주제 (35자 이내)

def rule_topic(it):
    """규칙 기반 한국어 주제: 소재명 + 해결 상태에 맞는 어미."""
    name = (it.get("topic_name") or "").strip() or re.split(r"[,.?!:·—-]", it.get("title_ko") or "")[0][:16]
    st = it.get("status", "")
    if st == "해결 근거":
        t = f"{name}, 마침내 풀린 수수께끼의 답은?"
    elif st == "가설 제안":
        t = f"{name}, 드디어 풀렸을까?"
    elif st == "미해결":
        t = f"{name}, 아직 아무도 풀지 못한 이유는?"
    else:
        t = f"{name}, 과학이 새로 찾은 단서는?"
    return t[:35]


AI_TOPIC_SYSTEM = """너는 한국 유튜브 10분 지식 다큐 채널의 기획자다. 영어 연구/기사 정보를 보고 한국어 '주제(제목)'를 정한다.
규칙: (1) 35자 이내, 궁금증을 부르는 질문·반전형 (2) status 가 '해결 근거'일 때만 '풀렸다/밝혀졌다' 같은 단정 허용,
'가설 제안'은 의문형이나 '유력한 답', '미해결'은 아직 풀리지 않았음이 드러나게 (3) 원문에 없는 숫자·연도·기관을 지어내지 않는다
(4) 소재명은 자연스러운 한국어로(기계번역 티 제거). 반드시 JSON만: {"topics": [{"id": 0, "topic": "...", "memo": "대본 작가에게 한 줄 조언"}]}"""


def ai_topics(items, m):
    """Claude Code(이 PC)로 한국어 주제를 다듬음. 실패하면 None."""
    payload = [{"id": i, "title": it["title"], "title_ko": it.get("title_ko", ""), "summary": it.get("summary", "")[:400],
                "status": it["status"], "topic_name": it.get("topic_name", "")} for i, it in enumerate(items)]
    try:
        d = m.ask_json("opus", AI_TOPIC_SYSTEM, "[후보]\n" + json.dumps(payload, ensure_ascii=False))
    except Exception as e:
        log("Claude Code 주제 다듬기 실패 → 규칙 기반 제목 사용: " + str(e).splitlines()[0][:120])
        return None
    out = {}
    for t in (d.get("topics") or []) if isinstance(d, dict) else []:
        try:
            i, topic = int(t.get("id")), str(t.get("topic", "")).strip()
        except (TypeError, ValueError):
            continue
        if topic:
            out[i] = {"topic": topic[:35], "memo": str(t.get("memo", "")).strip()}
    return out or None


# ------------------------------------------------------------------ 기획메모

def brief_markdown(it, topic, ai_memo=""):
    L = [f"# 기획메모 — {topic}", "",
         f"- 원문 제목: {it['title']}",
         f"- 기계번역 제목: {it.get('title_ko', '')}" if it.get("title_ko") else "",
         f"- 해결 상태(자동 판정): **{it['status']}** — {STATUS_RULE.get(it['status'], '')}",
         f"- 근거 수준: {it.get('evidence', '')} · 분야: {it.get('field', '')}" + (f" · 분석기술: {it['tech']}" if it.get("tech") else ""),
         f"- 게재일: {it.get('date', '')}",
         ""]
    if ai_memo:
        L += [f"- 기획자 조언: {ai_memo}", ""]
    L += ["## 출처 (대본 전에 반드시 원문 확인)"]
    for s, u, k in it.get("links", []):
        L.append(f"- {k} ({s}): {u}")
    for p in it.get("papers", []):
        if all(p != u for _, u, _ in it.get("links", [])):
            L.append(f"- DOI (기사 본문에서 찾음, 미검증): {p}")
    L += ["", "## 요약"]
    if it.get("summary_ko"):
        L.append(f"- (기계번역) {it['summary_ko']}")
    if it.get("summary"):
        L.append(f"- (원문) {it['summary'][:600]}")
    L += ["", "## 구성 방향 (해결 상태 기준)", f"- {it.get('structure', '')}" if it.get("structure") else ""]
    L += ["", "## 제목 후보 (규칙 기반 틀 — [소재] 자리에 소재명)"] + [f"- {h}" for h in it.get("hooks", [])]
    L += ["", "## 썸네일 문구 3안"] + [f"- [{l}] {c.replace(chr(10), ' / ')}" for l, c in zip("ABC", it.get("thumb_copies", []))]
    if it.get("thumb_images"):
        L += [f"- 썸네일 이미지: " + ", ".join(os.path.basename(p) for p in it["thumb_images"]) + " (이 폴더) · " + it.get("bg_credit", "")]
    L += ["", "## 해시태그", "- " + " ".join(it.get("hashtags", []))]
    if it.get("yt_query"):
        L += ["", "## 유튜브 수요·경쟁 (검색 표본)", f"- {it.get('yt_status', '')} · 같은 소재 최고 {it.get('yt_top_views', 0):,}회 · "
              f"최근 12개월 {it.get('yt_recent', 0)}개 · 판단: {it.get('yt_basis', '')}"]
        for v in it.get("yt_related_list", [])[:3]:
            L.append(f"  - {v['title'][:60]} ({v['views']:,}회) {v['url']}")
    L += ["", "---", "_이 메모는 소재탐색기(topic_finder)가 자동으로 만든 참고자료입니다. 사실은 대본 단계의 웹 조사로 다시 확인하세요._"]
    return "\n".join(x for x in L if x is not None)


def load_history():
    try:
        return json.load(open(HISTORY, encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"items": []}


def save_history(h):
    os.makedirs(os.path.dirname(HISTORY), exist_ok=True)
    tmp = HISTORY + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(h, f, ensure_ascii=False, indent=1)
    os.replace(tmp, HISTORY)


def title_key(t):
    return re.sub(r"[^a-z0-9]", "", (t or "").lower())[:60]


def existing_seed_topics():
    out = []
    if os.path.exists(SEED):
        for raw in open(SEED, encoding="utf-8"):
            line = raw.strip().lstrip("#").strip()
            if "|" in line:
                out.append(line.split("|")[1].strip())
    return out


def load_main_module():
    """Claude Code 호출용으로 메인 프로그램 모듈만 불러옴 (창은 만들지 않음). 실패하면 None."""
    try:
        spec = importlib.util.spec_from_file_location("snm", os.path.join(HERE, "shorts_novel_maker_supertonic.py"))
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        if not m.find_claude():
            return None
        return m
    except Exception as e:
        log("메인 프로그램 모듈을 불러오지 못함(규칙 기반 제목 사용): " + str(e).splitlines()[0][:100])
        return None


def main():
    ap = argparse.ArgumentParser(description="실화 소재 탐색 → 주제 목록·기획메모·썸네일")
    ap.add_argument("--편수", type=int, default=5, help="실화_주제목록.txt 에 넘길 편수 (기본 5)")
    ap.add_argument("--days", type=int, default=None, help="검색 기간(일), 기본 180 (--발견 이면 90)")
    ap.add_argument("--발견", action="store_true",
                    help=f"수수께끼가 아니어도 최근 새로 밝혀진 사실을 찾음(최신일수록 우대). 소재 기본값은 '{DISCOVERY_GENRE}'")
    ap.add_argument("--bg-commons", action="store_true", help="썸네일 배경에 위키미디어 공용 자유 이용 사진 사용 (켤 때만)")
    ap.add_argument("--no-youtube", action="store_true", help="유튜브 수요·경쟁 확인 생략 (빠름)")
    ap.add_argument("--no-thumbs", action="store_true", help="썸네일·해시태그 생략")
    ap.add_argument("--목록만", action="store_true", help="실화_주제목록.txt 는 건드리지 않음")
    ap.add_argument("--규칙제목", action="store_true", help="Claude Code 로 한국어 주제 다듬기 생략")
    ap.add_argument("--소재", default=None, help=f"주제 목록에 적을 소재 (기본: {GENRE}, --발견 이면 {DISCOVERY_GENRE})")
    ap.add_argument("--썸네일선택", default="자동", choices=["자동", "없음"],
                    help="소재별 썸네일 3안 중 최종 1장 자동 선택(기본). 직접 고르려면 '없음' 뒤 썸네일_고르기.bat 로 소재 폴더를 열기")
    a = ap.parse_args()
    if a.days is None:
        a.days = 90 if a.발견 else 180
    if a.소재 is None:
        a.소재 = DISCOVERY_GENRE if a.발견 else GENRE
    if a.편수 < 1:
        ap.error("--편수 는 1 이상이어야 합니다.")
    if not os.path.exists(os.path.join(TF_DIR, "topic_finder.py")):
        print(f"소재탐색 모듈이 없습니다: {TF_DIR}\\topic_finder.py")
        return 2
    import topic_finder as tf

    stamp = time.strftime("%Y%m%d_%H%M%S")
    out_root = os.path.join(HERE, "output", "장문", "_소재탐색", stamp)
    os.makedirs(out_root, exist_ok=True)
    pick = max(a.편수 * 2, 10)
    argv = ["--pick", str(pick), "--pool", str(max(45, pick * 2)), "--days", str(a.days),
            "--out", os.path.join(out_root, "탐색결과"), "--assets-out", os.path.join(out_root, "썸네일")]
    if a.bg_commons:
        argv.append("--bg-commons")
    if a.no_youtube:
        argv.append("--no-youtube")
    if a.no_thumbs:
        argv.append("--no-thumbs")
    argv += ["--썸네일선택", a.썸네일선택, "--mode", "발견" if a.발견 else "미스터리"]
    log(f"▶ 소재 탐색 시작: 최근 {a.days}일 · 후보 {pick}개 중 {a.편수}편 선정" + (" · 최신 발견 모드" if a.발견 else "")
        + (" · 공용 사진" if a.bg_commons else ""))
    res = tf.main(argv)
    picks = res["picks"]
    if not picks:
        log("후보를 찾지 못했습니다. --days 를 늘려보세요.")
        return 1

    # ---- 이미 넘긴/만든 소재 제외, 상태 우선순위(해결 근거 > 가설 제안 > 미해결 > 확인 필요)
    hist = load_history()
    seen_keys = {x.get("key") for x in hist["items"] if x.get("seed_written")}   # 실제로 주제 목록에 넣은 것만 제외 (--목록만 시험은 제외 안 함)
    made = []
    doc_root = os.path.join(HERE, "output", "장문")
    if os.path.isdir(doc_root):
        made = [n[len("_작업_"):] for n in os.listdir(doc_root) if n.startswith("_작업_")]
    order = {"해결 근거": 0, "가설 제안": 1, "미해결": 2, "확인 필요": 3}
    cands = [it for it in picks if title_key(it["title"]) not in seen_keys]
    cands.sort(key=lambda it: (order.get(it["status"], 9), -it.get("score", it.get("base_score", 0))))
    chosen = cands[: a.편수]
    if len(chosen) < a.편수:
        log(f"⚠ 새 소재가 {len(chosen)}개뿐입니다 (이미 넘긴 소재 제외). --days 를 늘리거나 넘긴_소재_기록.json 을 확인하세요.")
    for it in chosen:
        it["structure"] = tf.STRUCTURE.get(it["status"], "")

    # ---- 한국어 주제
    ai = None
    if not a.규칙제목:
        m = load_main_module()
        if m:
            log("Claude Code 로 한국어 주제 다듬는 중... (1~3분)")
            ai = ai_topics(chosen, m)
        else:
            log("Claude Code 를 찾지 못해 규칙 기반 제목을 씁니다")
    lines, records = [], []
    for i, it in enumerate(chosen, 1):
        t = (ai or {}).get(i - 1, {})
        topic = t.get("topic") or rule_topic(it)
        for prev in existing_seed_topics() + made:
            if topic == prev:
                topic = (topic[:33] + " ②")[:35]
        d = os.path.join(out_root, f"{i:02d}_" + tf_safe(it.get("topic_name") or it["title"]))
        os.makedirs(d, exist_ok=True)
        # 썸네일·해시태그·출처 복사
        for p in it.get("thumb_images", []):
            try:
                shutil.copy(p, d)
            except OSError:
                pass
        for name in ("hashtags.txt", "source.txt", "meta.json", "copy.txt", "썸네일_최종.jpg", "선택_기록.json"):
            src = os.path.join(it.get("asset_dir") or "", name)
            if it.get("asset_dir") and os.path.exists(src):
                shutil.copy(src, d)
        with open(os.path.join(d, "기획메모.md"), "w", encoding="utf-8") as f:
            f.write(brief_markdown(it, topic, t.get("memo", "")))
        lines.append(f"{a.소재} | {topic} | {d}")
        records.append({"key": title_key(it["title"]), "title": it["title"], "topic": topic, "status": it["status"],
                        "folder": d, "when": stamp, "seed_written": not a.목록만})
        log(f"  {i}. [{it['status']}] {topic}  ← {it['title'][:60]}")

    # ---- 주제 목록에 추가 (기존 줄은 그대로, 날짜 머리말 아래에 덧붙임)
    if not a.목록만:
        header = f"\n# ── 소재탐색 자동 추가 {time.strftime('%Y-%m-%d %H:%M')} (3번째 칸 = 기획메모 폴더 → 대본 AI 참고자료 + 썸네일 후보) ──\n"
        with open(SEED, "a", encoding="utf-8") as f:
            f.write(header + "\n".join(lines) + "\n")
        log(f"📑 실화_주제목록.txt 에 {len(lines)}줄 추가 → 실화_연속제작.bat 을 실행하면 이 순서대로 만듭니다 (연속_편수 확인)")
    else:
        log("📑 --목록만: 실화_주제목록.txt 는 바꾸지 않았습니다. 아래 줄을 직접 붙여 넣으세요:\n" + "\n".join(lines))
    hist["items"] += records
    save_history(hist)
    # ---- 전체 구성안(모음)도 남김
    with open(os.path.join(out_root, "실화_챕터구성안_자동.md"), "w", encoding="utf-8") as f:
        f.write(f"# 실화 소재 탐색 결과 {time.strftime('%Y-%m-%d %H:%M')} — 선정 {len(chosen)}편\n\n")
        f.write(f"탐색 리포트: {res['report_md']}\n\n")
        for i, it in enumerate(chosen, 1):
            f.write(f"## {i}편. {records[i - 1]['topic']}\n\n")
            f.write(open(os.path.join(records[i - 1]['folder'], '기획메모.md'), encoding='utf-8').read().split("\n", 1)[1] + "\n\n---\n\n")
    log(f"✅ 완료 → {out_root}\n   탐색 리포트: {res['report_md']}\n   기획메모·썸네일: 소재별 폴더 (NN_이름)")
    return 0


def tf_safe(s):
    s = re.sub(r"[\\/:*?\"<>|\s]+", "_", str(s)).strip("_")
    return s[:30] or "topic"


if __name__ == "__main__":
    sys.exit(main())
