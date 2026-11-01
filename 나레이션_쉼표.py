"""나레이션 쉼표 넣기 — 긴 문장을 성우가 숨 쉬듯 끊어 읽게, 연결어미 뒤에 쉼표를 넣음 (사용자 결정 2026-10-31)
python 나레이션_쉼표.py <프로젝트.json 또는 대본.txt> [--보기]
  - 한국어 형태소 분석기 Kiwi(kiwipiepy, 오픈소스)로 문장을 쪼개서 연결어미(~고 ~며 ~면서 ~지만 ~는데 ~니까 ~어서 ~으나 ~다가 ~면)를 찾음
  - 쉼표가 없는 긴 문장(25자 이상)만: 앞뒤 조각이 너무 짧지 않은(앞 10자·뒤 8자 이상) 연결어미 중 문장 가운데에 가까운 곳 뒤에 쉼표.
    그래도 한 조각이 35자를 넘으면 그 조각에서 한 번 더
  - 보조용언 앞(~어 보다, ~고 있다, ~게 하다)·따옴표 안 대사·챕터 제목(##)·[사진…] 같은 표시 줄은 건드리지 않음
  - 낱말 끝과 다음 낱말 시작이 같거나 비슷한 소리('공물함 함께', '검사 사관')면 그 사이에도 쉼표 (boundary_commas, 성우가 겹쳐 읽지 않게)
  - 글자는 바꾸지 않고 쉼표만 더함 → 자막에도 같은 쉼표가 들어감
  - --보기 : 고칠 곳만 보여 주고 저장하지 않음. 프로젝트면 처음 것을 <이름>_쉼표전.json 으로 남기고 story 를 고침
  - make_longdoc 이 대본 완성 뒤 나레이션 녹음 전에 자동으로 부름 (add_pauses)"""
import json
import os
import re
import shutil
import sys

EC_OK = {"고", "며", "으며", "면서", "으면서", "지만", "는데", "은데", "ㄴ데", "던데", "니까", "으니까", "어서", "아서", "여서", "으나", "나", "다가", "면", "으면", "는데도", "지마는"}
MIN_LEN, MAX_PART, MIN_LEFT, MIN_RIGHT = 25, 35, 10, 8
_KIWI = None


def kiwi():
    global _KIWI
    if _KIWI is None:
        from kiwipiepy import Kiwi
        _KIWI = Kiwi()
    return _KIWI


def cut_points(s):
    """문장 s 안에서 쉼표를 넣을 수 있는 자리(글자 위치, 어절 끝) 목록"""
    toks = kiwi().tokenize(s)
    out = []
    for i, t in enumerate(toks):
        if t.tag != "EC" or t.form not in EC_OK:
            continue
        end = t.start + t.len
        if end >= len(s) or s[end] != " ":            # 어절 끝에 붙은 연결어미만
            continue
        nxt = toks[i + 1] if i + 1 < len(toks) else None
        if nxt is not None and nxt.tag in ("VX", "XSV") :   # ~어 보다, ~고 있다 같은 보조용언 앞은 끊지 않음
            continue
        if s.count('"', 0, end) % 2 or s.count("“", 0, end) > s.count("”", 0, end):   # 따옴표 안
            continue
        out.append(end)
    return out


def add_commas_sentence(s):
    if "," in s or len(s) < MIN_LEN:
        return s
    pts = [p for p in cut_points(s) if p >= MIN_LEFT and len(s) - p >= MIN_RIGHT]
    if not pts:
        return s
    p = min(pts, key=lambda x: abs(x - len(s) / 2))
    left, right = s[:p], s[p:]
    if len(left) > MAX_PART:
        left = add_commas_sentence(left)
    if len(right) > MAX_PART:
        right = " " + add_commas_sentence(right.lstrip())
    return left + "," + right


def _jamo(ch):
    """한글 한 글자 → (초성, 중성) 번호. 한글이 아니면 None"""
    c = ord(ch) - 0xAC00
    return (c // 588, (c % 588) // 28) if 0 <= c < 11172 else None


def same_sound(a, b):
    """앞 낱말 끝 글자와 뒤 낱말 첫 글자가 같거나 비슷하게 들리는지 (같은 글자, 또는 받침만 다르고 초성·중성이 같음: 함/하, 국/구)"""
    if a == b:
        return True
    ja, jb = _jamo(a), _jamo(b)
    return bool(ja and jb and ja == jb and ja[0] != 11)   # 초성 ㅇ(이/있, 아/안)은 소리가 약해 겹쳐 들리지 않으므로 같은 글자일 때만


def boundary_commas(s):
    """낱말 끝과 다음 낱말 시작이 같거나 비슷한 소리면 사이에 쉼표 (사용자 결정 2026-11-01: 성우가 '공물함 함께'를 '공물함함'으로 겹쳐 읽음).
    따옴표 안은 그대로. 반환 (고친 문장, 걸린 곳 목록)"""
    words = s.split(" ")
    out, hits = [], []
    try:   # 꾸며 주는 말(그·몇·한·대한·솔직한 …) 뒤는 끊으면 어색해서 뺌: 관형사(MM)·관형형 어미(ETM)·수사로 끝나는 낱말
        toks = kiwi().tokenize(s)
        ends = {t_.start + t_.len: t_.tag for t_ in toks}
    except Exception:
        ends = {}
    pos = 0
    for i, w in enumerate(words):
        out.append(w)
        if i + 1 >= len(words):
            break
        nxt = words[i + 1]
        a = re.sub(r"[^가-힣]+$", "", w)
        b = re.sub(r"^[^가-힣]+", "", nxt)
        quoted = (" ".join(out).count('"') % 2 == 1) or (" ".join(out).count("“") > " ".join(out).count("”"))
        tag = ends.get(pos + len(w), "")
        pos += len(w) + 1
        modifier = tag in ("MM", "ETM", "NR", "SN", "XPN") or len(a) <= 1
        if a and b and w[-1:] not in ",.!?…" and not quoted and not modifier and same_sound(a[-1], b[0]):
            out[-1] = w + ","
            hits.append(f"{a} {b}")
    return " ".join(out), hits


def add_pauses(story):
    """대본 전체 → (고친 대본, 고친 곳 [(전, 후)])"""
    out_lines, changes = [], []
    for line in story.split("\n"):
        t = line.strip()
        if not t or t.startswith("#") or t.startswith("[") or t.startswith("♪"):
            out_lines.append(line)
            continue
        parts = re.split(r"(?<=[.!?…])(\s+)", line)
        new = "".join(boundary_commas(add_commas_sentence(x))[0] if x.strip() else x for x in parts)
        if new != line:
            for a, b in zip(re.split(r"(?<=[.!?…])\s+", line), re.split(r"(?<=[.!?…])\s+", new)):
                if a != b:
                    changes.append((a, b))
        out_lines.append(new)
    return "\n".join(out_lines), changes


def main(a):
    if not a:
        print(__doc__)
        return 2
    src = os.path.abspath(a[0])
    is_proj = src.endswith(".json")
    d = json.load(open(src, encoding="utf-8")) if is_proj else None
    story = d.get("story", "") if is_proj else open(src, encoding="utf-8").read()
    new, changes = add_pauses(story)
    for x, y in changes:
        print(f"- {x}\n+ {y}")
    print(f"쉼표 넣은 문장 {len(changes)}개")
    if "--보기" in a or not changes:
        return 0
    bak = src[:-5] + "_쉼표전.json" if is_proj else src + ".쉼표전"
    if not os.path.exists(bak):
        shutil.copy(src, bak)
    if is_proj:
        d["story"] = new
        json.dump(d, open(src, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    else:
        open(src, "w", encoding="utf-8").write(new)
    print("저장:", src, "(처음 것:", os.path.basename(bak) + ")")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
