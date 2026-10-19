"""프로그램 창의 🔎 소재 탐색 → 실화_소재탐색.py 인자 변환 점검 (창 없이, 네트워크 없음).
  py -3.11 -X utf8 소재탐색\\tests\\test_gui_topic_search.py"""
import importlib.util, os, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

fails = 0
def check(name, got, want):
    global fails
    ok = got == want
    fails += not ok
    print(("OK  " if ok else "FAIL"), name, "->", got, "" if ok else f"(기대: {want})")

spec = importlib.util.spec_from_file_location("snm", os.path.join(ROOT, "shorts_novel_maker_supertonic.py"))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

a = m.topic_search_args("🧩 풀린 수수께끼 찾기")
check("수수께끼 기본: 5편·180일", a, ["--count", "5", "--days", "180"])
b = m.topic_search_args("🆕 최근 밝혀진 발견 찾기", count=3, list_only=True, youtube=False, thumbs=False, commons=True, rule_titles=True)
check("발견+찾기만+옵션", b, ["--discovery", "--count", "3", "--days", "90", "--list-only", "--no-youtube", "--no-thumbs", "--bg-commons", "--rule-titles"])
check("영문 옵션만 (새 명령 창으로 넘겨도 안 깨짐)", all(ord(c) < 128 for c in " ".join(a + b)), True)
c = m.topic_search_args("🆕 최근 밝혀진 발견 찾기", days=365)
check("기간을 직접 적으면 그대로", c[c.index("--days") + 1], "365")
check("편수 0 이하는 1로", m.topic_search_args("🧩 풀린 수수께끼 찾기", count=0)[1], "1")

# 실화_소재탐색.py 가 그 영문 옵션을 실제로 받는지 (argparse 만 확인, 탐색은 안 함)
src = open(os.path.join(ROOT, "실화_소재탐색.py"), encoding="utf-8").read()
for opt in ("--count", "--discovery", "--list-only", "--rule-titles", "--genre", "--no-youtube", "--no-thumbs", "--bg-commons"):
    check(f"실화_소재탐색.py 옵션 {opt}", f'"{opt}"' in src, True)

with tempfile.TemporaryDirectory() as d:
    p = os.path.join(d, "주제목록.txt")
    open(p, "w", encoding="utf-8").write("# 머리말\n\n[실화] 과학이 밝혀낸 미스터리 | 주제 하나\n# [실화] 미제 사건의 기록 | 보류\n[실화] 최근 밝혀진 과학 발견 | 주제 둘 | 폴더\n")
    check("대기 주제 수 ('#'·빈 줄 제외)", m.seed_pending_count(p), 2)
    check("목록 파일 없으면 0", m.seed_pending_count(os.path.join(d, "없음.txt")), 0)
check("주제 목록 위치 = 실화\\주제목록.txt", os.path.relpath(m.SEED_FILE, ROOT).replace("\\", "/"), "실화/주제목록.txt")

print(f"\n실패 {fails} 건")
sys.exit(1 if fails else 0)
