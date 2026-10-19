"""--mode 발견 확인 (네트워크 없음). 미스터리 모드 결과는 그대로여야 함."""
import os, sys
from datetime import datetime, timedelta, timezone
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import topic_finder as tf

fails = 0
def check(name, got, want):
    global fails
    ok = got == want
    fails += not ok
    print(("OK  " if ok else "FAIL"), name, "->", got, "" if ok else f"(기대: {want})")

NOW = datetime(2026, 10, 19, tzinfo=timezone.utc)
def item(title, summary="", days_ago=10, **kw):
    d = (NOW - timedelta(days=days_ago)).strftime("%a, %d %b %Y %H:%M:%S +0000")
    it = {"title": title, "summary": summary, "origin": "뉴스", "links": [("뉴스", "x", "u1"), ("뉴스", "y", "u2")],
          "date": d, "cited": 0, "coverage": 2}
    it.update(kw)
    return it

disc = item("Scientists report first evidence of plants communicating with sound", "An unexpected result.")
myst = item("Long-standing mystery of the Moon's tilt finally solved", "Researchers explain the puzzle.")
plain = item("Quarterly update on lab equipment funding", "Routine report.")

def titles(res):
    return [x["title"] for x in res]

r_m = tf.score_items([disc, myst, plain], 180, "고고학", NOW)
r_d = tf.score_items([disc, myst, plain], 90, "고고학", NOW, mode="발견")
check("미스터리 모드: 수수께끼 아닌 발견은 제외", disc["title"] in titles(r_m), False)
check("미스터리 모드: 수수께끼는 포함", myst["title"] in titles(r_m), True)
check("발견 모드: 새 발견 포함", disc["title"] in titles(r_d), True)
check("발견 모드: 수수께끼도 계속 포함", myst["title"] in titles(r_d), True)
check("발견 모드: 일반 기사는 제외", plain["title"] in titles(r_d), False)
sig = next(x for x in r_d if x["title"] == disc["title"])["signals"]
check("발견 신호가 signals 에 기록", "first evidence" in sig.lower(), True)

# 최신일수록 우대: 같은 기사라도 새로 나온 쪽 점수가 높고, 그 차이는 발견 모드에서 더 큼
new_ = item("Oldest known star map found", "first evidence", days_ago=5)
old_ = item("Oldest known star map found ", "first evidence", days_ago=80)
s = {x["title"]: x["base_score"] for x in tf.score_items([new_, old_], 90, "고고학", NOW, mode="발견")}
gap_d = s[new_["title"]] - s[old_["title"]]
check("발견 모드: 최신 기사가 더 높음", gap_d > 0, True)
m1 = item("Mystery of star map solved", "puzzle", days_ago=5)
m2 = item("Mystery of star map solved ", "puzzle", days_ago=80)
s2 = {x["title"]: x["base_score"] for x in tf.score_items([m1, m2], 90, "고고학", NOW)}
gap_m = s2[m1["title"]] - s2[m2["title"]]
check("최신 우대는 발견 모드에서 2배 (점수 반올림 오차 0.2 허용)", abs(gap_d - gap_m * 2) <= 0.2, True)

# 미스터리 모드 점수는 이전 계산식과 같아야 함 (발견 신호가 섞여도 영향 없음)
both = item("Mystery solved: first evidence of ancient tides", "puzzle")
a = tf.score_items([both], 180, "고고학", NOW)[0]["base_score"]
b = tf.score_items([dict(both, title="Mystery solved: of ancient tides")], 180, "고고학", NOW)[0]["base_score"]
check("미스터리 모드는 발견 신호를 점수에 안 넣음", a == b, True)

print(f"\n실패 {fails} 건")
sys.exit(1 if fails else 0)
