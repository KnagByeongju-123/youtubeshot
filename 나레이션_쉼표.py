"""나레이션 쉼표 넣기 — 한국어 형태소 분석기 Kiwi(kiwipiepy, LGPL-3.0 오픈소스)로 문장을 나눠 보고
성우가 숨 쉴 자리에 쉼표를 넣음 (사용자 결정 2026-10-31: 짧은 문장을 몰아서 빨리 읽는 일을 줄임 — 속도를 억지로 바꾸지 않고 쉼표로 자연스럽게)

  python -X utf8 나레이션_쉼표.py <프로젝트.json>            → 바꿀 곳만 보여 줌
  python -X utf8 나레이션_쉼표.py <프로젝트.json> --적용     → 프로젝트 대본에 넣음 (처음 파일은 _쉼표전.json)
  python -X utf8 나레이션_쉼표.py --문장 "다시 본문으로 돌아가 보겠습니다."

규칙 (보수적으로: 문장 하나에 쉼표가 너무 많아지지 않게)
  1) 문장 첫머리 이음말(접속부사·담화부사: 그리고·다만·그런데·하지만·다시·결국·물론·사실·정작 …) 뒤
  2) 앞뒤가 둘 다 충분히 긴 이어지는 말끝(-는데·-지만·-면서·-니까·-아서/어서·-는지 …) 뒤 — 한 문장에 한 곳
  3) 짧은 문장(빠르게 읽히기 쉬움, --짧게 일 때)은 1)의 이음말이 없어도 첫 어절이 부사면 그 뒤
  따옴표 안(인용·대사), 그림·효과 줄([사진: …]·[효과: …]), 장 제목(##)은 건드리지 않음
"""
import json
import os
import re
import shutil
import sys

LEAD_WORDS = {"그리고", "그러나", "하지만", "그런데", "그래서", "그러니까", "그러면", "그렇다면", "그러자", "게다가", "다만", "다시",
              "결국", "물론", "사실", "정작", "즉", "또", "또한", "이어서", "먼저", "이제", "여기서", "그렇게", "반면", "한편", "드디어",
              "마침내", "솔직히", "어쩌면", "아마", "오히려", "심지어", "특히", "무엇보다", "그러니", "따라서", "그럼", "바로", "실제로"}
CONNECT = ("는데", "은데", "ㄴ데", "지만", "면서", "으면서", "니까", "으니까", "아서", "어서", "고서", "다가", "는지", "은지", "ㄴ지", "든지")
_KIWI = None


def kiwi():
    global _KIWI
    if _KIWI is None:
        from kiwipiepy import Kiwi
        _KIWI = Kiwi()
    return _KIWI


def _quoted(s):
    """따옴표 안 글자 위치 집합"""
    inside, q, out = False, None, set()
    pairs = {'"': '"', "“": "”", "'": "'", "‘": "’", "「": "」", "『": "』"}
    for i, ch in enumerate(s):
        if not inside and ch in pairs:
            inside, q = True, pairs[ch]
        elif inside and ch == q:
            inside = False
        elif inside:
            out.add(i)
    return out


def comma_sentence(s, short=False):
    """문장 하나 → (쉼표 넣은 문장, 넣은 위치 수)"""
    if not s.strip() or len(s) < 8:
        return s, 0
    toks = kiwi().tokenize(s)
    qpos = _quoted(s)
    adds = []
    # 1) 첫머리 이음말
    first = next((t for t in toks if t.tag not in ("SS", "SO", "SW")), None)
    if first is not None and first.start not in qpos:
        end = first.start + first.len
        word_end = s.find(" ", first.start)
        lead = s[first.start:word_end] if word_end > 0 else ""
        if word_end > 0 and s[word_end - 1] not in ",.!?…" and (
                lead in LEAD_WORDS or first.tag == "MAJ" or (short and first.tag in ("MAG", "MAJ") and end == word_end)):
            adds.append(word_end)
    # 2) 이어지는 말끝: 앞 12자·뒤 10자 이상, 한 곳만
    for t in toks:
        if t.tag != "EC" or t.form not in CONNECT:
            continue
        end = t.start + t.len
        if end >= len(s) or s[end] != " " or end in qpos or (end - 1) in qpos:
            continue
        if s[end - 1] in ",.!?…":
            continue
        before = len(s[:end].strip())
        after = len(s[end:].strip())
        if before >= (5 if short else 12) and after >= (6 if short else 10) and not any(abs(end - a) < 8 for a in adds):
            adds.append(end)
            break
    if not adds:
        return s, 0
    out = s
    for p in sorted(set(adds), reverse=True):
        out = out[:p] + "," + out[p:]
    return out, len(set(adds))


def split_sentences(par):
    """문단 → 문장들 (마침표·물음표·느낌표 뒤 공백 기준, 따옴표 닫힘 포함)"""
    return [m_.group(0).strip() for m_ in re.finditer(r".+?(?:[.?!…][\"'”’」』)]*(?=\s|$)|$)", par) if m_.group(0).strip()]


def comma_paragraph(par, short_chars=22):
    s_ = par.strip()
    if not s_ or s_.startswith(("[", "#", "♪")):
        return par, 0
    n = 0
    out = []
    for se in split_sentences(s_):
        new, k = comma_sentence(se, short=len(se) <= short_chars)
        out.append(new)
        n += k
    return " ".join(out), n


def comma_story(story):
    """대본 전체 → (새 대본, 바뀐 문장 목록[(전, 후)])"""
    lines, changes = [], []
    for line in story.split("\n"):
        new, n = comma_paragraph(line)
        if n:
            changes.append((line.strip(), new))
            lines.append(new)
        else:
            lines.append(line)
    return "\n".join(lines), changes


def main(a):
    if not a:
        print(__doc__)
        return 2
    if a[0] == "--문장":
        print(comma_sentence(a[1], short=len(a[1]) <= 22)[0])
        return 0
    proj = a[0]
    d = json.load(open(proj, encoding="utf-8"))
    new, changes = comma_story(d.get("story", ""))
    for b, n in changes:
        print("-", b[:90])
        print("+", n[:90])
    print(f"쉼표 넣을 문단 {len(changes)}개")
    if "--적용" in a and changes:
        bak = proj[:-5] + "_쉼표전.json"
        if not os.path.exists(bak):
            shutil.copy(proj, bak)
        d["story"] = new
        tmp = proj + ".tmp"
        json.dump(d, open(tmp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        os.replace(tmp, proj)
        print("적용함 (처음 파일: " + os.path.basename(bak) + ")")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
