"""--mode 해독 확인 (네트워크 없음). 문자·비문·암호 이야기만 남고, 다른 모드 결과는 그대로여야 함."""
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

NOW = datetime(2026, 10, 30, tzinfo=timezone.utc)
def item(title, summary="", days_ago=10, **kw):
    d = (NOW - timedelta(days=days_ago)).strftime("%a, %d %b %Y %H:%M:%S +0000")
    it = {"title": title, "summary": summary, "origin": "뉴스", "links": [("뉴스", "x", "u1"), ("뉴스", "y", "u2")],
          "date": d, "cited": 0, "coverage": 2}
    it.update(kw)
    return it

script = item("Researchers decipher a 2,000-year-old inscription in an unknown script", "The mystery writing system was read for the first time.")
scroll = item("AI reads the first words of a burnt Herculaneum scroll", "Charred papyrus read for the first time, solving a long-standing puzzle.")
starfish = item("Long-standing mystery of sea star wasting finally solved", "Researchers explain the puzzle.")
mrna = item("A protein that regulates mRNA decoding can itself be regulated", "Researchers decode a long-standing puzzle in cells.")
letters = item("Mystery of the lost letters of a medieval monk solved", "Researchers found the letters in an archive.")
def titles(res):
    return [x["title"] for x in res]

r = tf.score_items([script, scroll, starfish, letters, mrna], 365, "고고학", NOW, mode="해독")
check("해독 모드: 문자 해독 기사 포함", script["title"] in titles(r), True)
check("해독 모드: 두루마리 판독 기사 포함", scroll["title"] in titles(r), True)
check("해독 모드: 문자와 상관없는 수수께끼는 제외", starfish["title"] in titles(r), False)
check("해독 모드: '편지'라는 말만 있는 기사는 제외", letters["title"] in titles(r), False)
check("해독 모드: 'mRNA 해독' 같은 생물학 기사는 제외", mrna["title"] in titles(r), False)
sig = next(x for x in r if x["title"] == script["title"])["signals"]
check("해독 신호가 signals 에 기록", "decipher" in sig.lower(), True)

a = tf.score_items([dict(script)], 365, "고고학", NOW)[0]["base_score"]
b = tf.score_items([dict(script)], 365, "고고학", NOW, mode="해독")[0]["base_score"]
check("해독 모드가 같은 기사 점수를 더 높게", b > a, True)
check("미스터리 모드에서 문자와 상관없는 수수께끼는 계속 포함", starfish["title"] in titles(tf.score_items([starfish], 180, "고고학", NOW)), True)

print(f"\n실패 {fails} 건")
sys.exit(1 if fails else 0)
