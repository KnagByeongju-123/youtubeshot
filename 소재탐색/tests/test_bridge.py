"""실화_소재탐색 ↔ make_longdoc 연결 점검 (네트워크 없음)
  py -3.11 -X utf8 소재탐색\\tests\\test_bridge.py
"""
import importlib.util
import json
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "소재탐색"))

fails = 0


def check(name, got, want):
    global fails
    ok = got == want
    fails += not ok
    print(("OK  " if ok else "FAIL"), name, "->", got, "" if ok else f"(기대: {want})")


# ---- make_longdoc.load_seed_lineup: 3번째 칸(기획메모 폴더/파일/글)
spec = importlib.util.spec_from_file_location("ml", os.path.join(ROOT, "make_longdoc.py"))
ml = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ml)


class FakeM:
    DOC_CATEGORY = "장문"

    @staticmethod
    def cat_info(_):
        return ("", {"[실화] 과학이 밝혀낸 미스터리": ("", ""), "[실화] 미제 사건의 기록": ("", "")})


tmp = tempfile.mkdtemp()
brief_dir = os.path.join(tmp, "01_test")
os.makedirs(brief_dir)
open(os.path.join(brief_dir, "기획메모.md"), "w", encoding="utf-8").write("# 기획메모 — 테스트\n- 해결 상태: 가설 제안")
open(os.path.join(brief_dir, "thumb_A.jpg"), "wb").write(b"x")
memo_file = os.path.join(tmp, "memo.md")
open(memo_file, "w", encoding="utf-8").write("파일 메모")
seed = os.path.join(tmp, "seed.txt")
open(seed, "w", encoding="utf-8").write(
    "# 주석\n"
    "[실화] 과학이 밝혀낸 미스터리 | 기존 형식 주제\n"
    f"[실화] 미제 사건의 기록 | 폴더 메모 주제 | {brief_dir}\n"
    f"[실화] 과학이 밝혀낸 미스터리 | 파일 메모 주제 | {memo_file}\n"
    "[실화] 과학이 밝혀낸 미스터리 | 글 메모 주제 | 그냥 적은 메모\n"
    "소재 없는 줄\n")
ml.SEED = seed
plan = ml.load_seed_lineup(FakeM)
check("줄 수 (주석 제외)", len(plan), 5)
check("기존 형식 그대로 (메모 없음)", (plan[0]["topic"], plan[0]["memo"], plan[0]["folder"]), ("기존 형식 주제", "", ""))
check("폴더 → 기획메모.md 내용 + 폴더 기록", ("가설 제안" in plan[1]["memo"], plan[1]["folder"]), (True, brief_dir))
check("파일 → 내용", "파일 메모" in plan[2]["memo"], True)
check("글 → 그대로", "그냥 적은 메모" in plan[3]["memo"], True)
check("소재 생략 → 기본 소재", plan[4]["genre"], "[실화] 과학이 밝혀낸 미스터리")

# ---- add_external_thumbs: 후보 폴더에 외부_ 이름으로 복사
base = os.path.join(tmp, "영상제목")
logs = []
ml.add_external_thumbs(brief_dir, base, logs.append)
check("외부 썸네일 복사", os.path.exists(os.path.join(base + "_썸네일_후보", "외부_thumb_A.jpg")), True)
ml.add_external_thumbs("", base, logs.append)
ml.add_external_thumbs(os.path.join(tmp, "없음"), base, logs.append)
check("폴더 없으면 조용히 통과", len(logs), 1)

# ---- 실화_소재탐색: 규칙 제목·기획메모 본문 (네트워크 없음)
spec2 = importlib.util.spec_from_file_location("br", os.path.join(ROOT, "실화_소재탐색.py"))
br = importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(br)
it = {"title": "Hidden charcoal reveals the true age of ancient cave paintings", "title_ko": "숨은 숯이 밝힌 동굴벽화의 나이",
      "status": "가설 제안", "evidence": "뉴스만", "field": "고고학/인류", "tech": "방사성탄소 연대측정", "date": "2026-07-28",
      "links": [["ScienceDaily 고고학", "https://example.org/a", "기사"]], "papers": [], "summary": "A new analysis dated paintings.",
      "summary_ko": "새 분석이 벽화의 연대를 측정했다.", "hooks": ["[소재], 드디어 풀렸을까?"], "thumb_copies": ["프랑스 숯\n드디어 풀렸을까?"],
      "thumb_images": ["/x/thumb_A.jpg"], "hashtags": ["#고고학", "#과학다큐"], "topic_name": "프랑스 동굴벽화 숯",
      "yt_query": "", "structure": "훅 → 역사 → 가설 → 반론"}
t = br.rule_topic(it)
check("규칙 제목 35자 이내·가설은 의문형", (len(t) <= 35, t.endswith("?")), (True, True))
check("미해결 규칙 제목에 해결 단정 없음", "풀린" in br.rule_topic(dict(it, status="미해결")), False)
md = br.brief_markdown(it, t, "조언")
check("기획메모에 상태 규칙·출처·해시태그·⚠", ("⚠" in md, "https://example.org/a" in md, "#고고학" in md, "조언" in md), (True, True, True, True))
check("기획메모를 seed_memo 로 읽으면 참고자료 머리말", ml.seed_memo(brief_dir)[0].startswith("[소재탐색 기획메모"), True)

print("\n실패", fails, "건")
sys.exit(1 if fails else 0)
