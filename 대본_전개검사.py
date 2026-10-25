"""연재 대본이 인기 웹툰·만화식 전개 규칙을 따르는지 검사 (CLAUDE.md '웹툰식 전개 검사' 규칙)

  python 대본_전개검사.py <회차.py> [--입버릇 "고칠 수 있어"] [--제목낱말 쇠귀신]

회차.py 의 STORY(대본)·DIALOGUE(대사)를 읽어 글자로 셀 수 있는 것만 자동으로 봄 → 통과 못 한 항목은 고친 뒤 다시.
나머지(과학 4단계·감정 고점·떡밥 회수)는 맨 아래 '직접 확인' 목록을 보고 Claude 가 대본을 읽어 판단함.
"""
import importlib.util
import os
import re
import sys

TEASE = r"(잠시 뒤|곧|이어서|다음 장|바로 다음|그리고 곧|그런데 바로|다음 순간|이제 막|그 시각)"


def load(path):
    sp = importlib.util.spec_from_file_location("ep", path)
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


def chapters(story):
    """'## ' 제목으로 나눈 [(제목, 본문)] — 첫 덩어리는 오프닝"""
    parts = re.split(r"^## (.+)$", story, flags=re.M)
    out = [("오프닝", parts[0])]
    out += [(parts[i], parts[i + 1]) for i in range(1, len(parts) - 1, 2)]
    return out


def sentences(text):
    text = re.sub(r"\{c\d+\}", " ", text)
    return [s.strip() for s in re.split(r"(?<=[.?!])\s+|\n+", text) if len(s.strip()) > 1]


def plain(text):
    return re.sub(r"\s", "", re.sub(r"\{c\d+\}", "", text))


def main():
    a = sys.argv[1:]
    if not a:
        sys.exit(__doc__)
    m = load(a[0])
    habit = a[a.index("--입버릇") + 1] if "--입버릇" in a else ""
    title = getattr(m, "TITLE", "")
    word = a[a.index("--제목낱말") + 1] if "--제목낱말" in a else title.split("-")[-1].strip()
    story, dialogue = m.STORY, [d[0] for d in getattr(m, "DIALOGUE", [])]
    chs = chapters(story)
    res = []

    def check(ok, name, why=""):
        res.append((ok, name, why))

    opening = chs[0][1]
    first = sentences(opening)[:3]
    check(bool(first) and word in first[0], f"첫 문장에 제목 낱말 '{word}'", first[0][:40] if first else "")
    check(any(re.search(r"\d|[일이삼사오육칠팔구십백천만]+\s?(년|살|대|명|번째)|수백|수십", s) for s in first), "첫 세 문장에 숫자", "")
    check("끝까지 보시면" in opening, "오프닝에 '끝까지 보시면'", "")
    check(opening.count("{c") >= 3, "오프닝 그림 3장 이상", f"{opening.count('{c')}장")

    # 챕터 끝 예고 (마지막 챕터 제외)
    miss = [t for t, body in chs[1:-1] if not re.search(TEASE, " ".join(sentences(body)[-2:]))]
    check(not miss, "챕터 끝마다 다음 장 예고", "빠짐: " + ", ".join(miss) if miss else "")

    # 절벽 엔딩: 마지막 챕터 끝에 질문 + 다음 화 예고 + 연재 한 줄
    last = " ".join(sentences(chs[-1][1])[-4:])
    check("?" in last, "마지막에 궁금증 질문(절벽 엔딩)", "")
    check(re.search(r"다음 이야기|다음 화|\d+화", last) is not None, "다음 화 예고", "")
    check(re.search(r"이 채널에서.*이어집니다", story) is not None, "연재 한 줄('이 채널에서 … 이어집니다')", "")

    # 템포: 긴 문장·긴 문단·챕터 길이 균형
    sents = sentences(story)
    long_s = [s for s in sents if len(plain(s)) > 45]
    check(len(long_s) <= len(sents) * 0.1, "긴 문장(45자 넘음) 10% 이하", f"{len(long_s)}/{len(sents)}" + (f" 예: {long_s[0][:30]}…" if long_s else ""))
    paras = [p for p in re.split(r"\n\s*\n", story) if plain(p) and not p.strip().startswith("##") and not re.fullmatch(r"\s*\{c\d+\}\s*", p)]
    long_p = [p for p in paras if len(plain(p)) > 160]
    check(not long_p, "한 문단 160자 이하(장면 전환 빠르게)", f"{len(long_p)}개" + (f" 예: {long_p[0].strip()[:30]}…" if long_p else ""))
    lens = [len(plain(b)) for _, b in chs[1:]]
    if lens:
        avg = sum(lens) / len(lens)
        bad = [chs[i + 1][0] for i, L in enumerate(lens) if L > avg * 1.8 or L < avg * 0.4]
        check(not bad, "챕터 길이 고르게(평균의 0.4~1.8배)", ", ".join(bad))

    # 대사 비중·입버릇
    dl = sum(len(plain(d)) for d in dialogue)
    ratio = dl / max(1, len(plain(story)))
    check(ratio >= 0.05, "대사 비중 5% 이상(인물이 말하게)", f"{ratio * 100:.1f}%")
    missing = [d for d in dialogue if d not in story]
    check(not missing, "DIALOGUE 대사가 대본에 그대로 있음", ", ".join(missing))
    if habit:
        check(habit in story, f"입버릇 '{habit}'", "")

    ok_n = sum(1 for r in res if r[0])
    print(f"웹툰식 전개 검사: {title} — {ok_n}/{len(res)} 통과")
    for ok, name, why in res:
        print(f"  {'✅' if ok else '❌'} {name}" + (f"  ({why})" if why else ""))
    print("""
직접 확인 (대본을 읽고 판단):
  - 첫 장면이 그 화에서 가장 긴장되는 순간인가 / 지난 화 절벽 엔딩에서 바로 이어지나
  - 이번 화 안에서 작은 사건 하나가 시작→위기→해결되나 (보고 나서 시원한 순간이 있나)
  - 문제 풀이가 '시도 → 실패 → 깨달음 → 성공' 4단계인가 (실패 한 번은 꼭)
  - 감정이 가장 높은 장면(울컥·소름)이 한 번 있나
  - 지난 떡밥 하나를 조금 풀고, 새 떡밥(세상의 비밀 단서) 하나를 던지나
  - 인물이 화마다 조금 자라나 (기술·관계·동료 목록)
  - 장르에 맞는 인기작 전개와 비교해 늘어지는 곳이 없나 (기획.md 의 참고 작품)""")
    sys.exit(0 if ok_n == len(res) else 1)


if __name__ == "__main__":
    main()
