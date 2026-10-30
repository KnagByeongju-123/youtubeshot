r"""한국어 읽기 모듈 - 성우(TTS)가 읽을 글을 만드는 규칙을 한곳에 모음

자막은 맞춤법대로(2026년, 42%, AI) 두고, 성우에게 넘기는 글만 소리 나는 대로 바꿉니다.
  - 낱말 규칙: 읽기사전.txt 에  AI=에이아이  처럼 한 줄씩 적으면 다음 문장부터 바로 적용 (프로그램을 다시 켤 필요 없음)
  - 숫자 규칙: 아래 ko_numbers (2026년 → 이천이십육 년, 3개 → 세 개, 341곳 → 삼백사십한 곳 …)
  - 건 → 껀, 전화번호는 한 자리씩, 낱말 '사번' → '사원번호'

미리 들어 보기 전에 글로 확인:  py -3.11 -X utf8 한국어_읽기.py "AI가 만든 3D 지도 341곳"
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DICT_FILE = os.path.join(HERE, "읽기사전.txt")
DEFAULT_DICT = """# 읽기 사전 - 성우가 읽을 때만 바꿀 낱말 (자막은 그대로)
# 한 줄에 하나씩:  원래 글자=읽을 소리
# 영어 낱말은 낱말째로만 바뀜 (AI 는 바뀌지만 OpenAI 안의 AI 는 안 바뀜). 뒤에 붙은 조사(은/는, 이/가, 을/를, 과/와)는 알아서 맞춤
# '#' 으로 시작하는 줄과 빈 줄은 무시. 이 파일을 고치면 다음 문장부터 바로 적용됩니다.
AI=에이아이
3D=쓰리디
3d=쓰리디
2D=투디
2d=투디
"""


def josa(word, j):
    """바꾼 말 받침에 맞춰 조사 고치기 (로트+과 → 로트와)"""
    if not j:
        return ""
    ch = word[-1] if word else ""
    batchim = "가" <= ch <= "힣" and (ord(ch) - 0xAC00) % 28 != 0
    pair = {"은": ("은", "는"), "는": ("은", "는"), "이": ("이", "가"), "가": ("이", "가"),
            "을": ("을", "를"), "를": ("을", "를"), "과": ("과", "와"), "와": ("과", "와")}[j]
    return pair[0] if batchim else pair[1]


def apply_read(t, pairs):
    for a, b in pairs:
        pre = r"(?<![A-Za-z0-9])" if re.match(r"[A-Za-z0-9]", a) else ""
        post = r"(?![A-Za-z])" if re.search(r"[A-Za-z]$", a) else ""
        t = re.sub(pre + re.escape(a) + post + r"(?:(은|는|이|가|을|를|과|와)(?=[\s,.!?·)]|$))?",
                   lambda _m, b=b: b + josa(b, _m.group(1)), t)
    return t


_DICT = {"mtime": None, "pairs": []}


def read_dict():
    """읽기사전.txt → [(원래, 읽을 소리)] (긴 것부터). 파일이 없으면 기본 사전으로 새로 만듦. 고치면 바로 다시 읽음"""
    try:
        if not os.path.exists(DICT_FILE):
            with open(DICT_FILE, "w", encoding="utf-8") as f:
                f.write(DEFAULT_DICT)
        mt = os.path.getmtime(DICT_FILE)
        if mt != _DICT["mtime"]:
            text = open(DICT_FILE, encoding="utf-8-sig").read()
            _DICT.update(mtime=mt, pairs=parse_dict(text))
    except OSError:
        if _DICT["mtime"] is None:
            _DICT["pairs"] = parse_dict(DEFAULT_DICT)
    return _DICT["pairs"]


def parse_dict(text):
    out = []
    for line in str(text or "").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        m_ = re.match(r"(.+?)\s*(?:->|→|=)\s*(.+)$", line)
        if m_:
            out.append((m_.group(1).strip(), m_.group(2).strip()))
    return sorted(out, key=lambda x: -len(x[0]))


def builtin_read(t):
    """읽기사전.txt 의 낱말 규칙 적용 (AI → 에이아이)"""
    return apply_read(t, read_dict())


_KO_DIG = "영일이삼사오육칠팔구"
_KO_NATIVE = {1: "한", 2: "두", 3: "세", 4: "네", 5: "다섯", 6: "여섯", 7: "일곱", 8: "여덟", 9: "아홉"}
_KO_NATIVE_TENS = {1: "열", 2: "스물", 3: "서른", 4: "마흔", 5: "쉰", 6: "예순", 7: "일흔", 8: "여든", 9: "아흔"}
# 고유어로 읽는 단위 (1~99): 세 명, 두 마리, 다섯 살, 세 시
_KO_NATIVE_UNITS = ("마리", "사람", "시간", "살", "시", "번", "권", "잔", "그루", "송이", "척", "달", "가지", "군데", "걸음",
                    "켤레", "곳", "쌍", "방울", "바퀴", "명", "개", "채", "벌", "줄", "알", "배",
                    "자리", "장", "통", "차례", "겹", "갈래", "마디", "모금", "포기", "자루", "그릇", "봉지", "덩이", "곡",
                    "자")    # 글자 수: 27자 → 스물일곱 자, 341자 → 삼백사십한 자 (사용자 규칙, 2026-10-22)
_KO_UNIT_WORDS = [("km²", "제곱킬로미터"), ("m²", "제곱미터"), ("km/h", "킬로미터"), ("km", "킬로미터"), ("cm", "센티미터"),
                  ("mm", "밀리미터"), ("kg", "킬로그램"), ("mg", "밀리그램"), ("ml", "밀리리터"), ("mL", "밀리리터"), ("°C", "도"),
                  ("℃", "도"), ("°", "도"), ("%", " 퍼센트"), ("hPa", "헥토파스칼"), ("bar", "바"), ("atm", "기압"), ("m", "미터"), ("g", "그램"), ("L", "리터")]


def ko_sino(n):
    """정수 → 한자어 수사 (1960 → 천구백육십, 10000 → 만, 13800000000 → 백삼십팔억)"""
    if n == 0:
        return "영"
    out = []
    for i, big in enumerate(["", "만", "억", "조", "경"]):
        k = n % 10000
        n //= 10000
        if k:
            s = ""
            for d, small in ((k // 1000, "천"), (k // 100 % 10, "백"), (k // 10 % 10, "십"), (k % 10, "")):
                if d:
                    s += ("" if d == 1 and small else _KO_DIG[d]) + small
            if big == "만" and k == 1:
                s = ""          # '일만' 대신 '만'
            out.append(s + big)
        if not n:
            break
    return "".join(reversed(out))


def ko_native(n):
    """1~99 → 고유어 관형형 (3 → 세, 20 → 스무, 21 → 스물한)"""
    if n == 20:
        return "스무"
    return _KO_NATIVE_TENS.get(n // 10, "") + _KO_NATIVE.get(n % 10, "")


def ko_numbers(text):
    """나레이션용: 아라비아 숫자·기호를 한글 읽기로 (자막은 숫자 그대로 두고 성우에게 넘기는 글만 바꿈).
    TTS(특히 Supertonic)가 숫자를 잘못 읽거나 오류를 내는 것을 막음"""
    t = text
    t = re.sub(r"(?<=\d),(?=\d{3}(?!\d))", "", t)                         # 12,000 → 12000
    t = re.sub(r"(\d)\s*[~～∼]\s*(?=\d)", r"\1에서 ", t)                  # 10~20 → 10에서 20
    t = re.sub(r"(?<![\w.])-(?=\d)", "마이너스 ", t)
    t = re.sub(r"(?<![\d.])(시속\s*)?(\d+(?:\.\d+)?)\s*km/h", r"시속 \2km", t)   # 100km/h → 시속 100km (시속 100km/h 처럼 이미 있으면 두 번 붙이지 않음)
    for a, b in _KO_UNIT_WORDS:                                         # 10km → 10킬로미터 (숫자 바로 뒤의 단위만)
        t = re.sub(r"(\d)\s*" + re.escape(a) + r"(?![A-Za-z])", r"\1" + b, t)

    def one(m_):
        num, frac, after = m_.group(1), m_.group(2), m_.string[m_.end():m_.end() + 3]
        try:
            n = int(num)
        except ValueError:
            return m_.group(0)
        if frac:                                                        # 3.14 → 삼 점 일사
            return ko_sino(n) + " 점 " + "".join(_KO_DIG[int(c)] for c in frac[1:])
        if n == 1 and after.startswith("만"):                             # 1만 → 만 (일만 X)
            return ""
        if after.startswith("월") and 1 <= n <= 12:                     # 6월 → 유월, 10월 → 시월
            return {6: "유", 10: "시"}.get(n, ko_sino(n))
        before = m_.string[max(0, m_.start() - 1):m_.start()]
        counter = before != "제" and after.startswith(_KO_NATIVE_UNITS) and not after.startswith(
            ("시대", "시즌", "개월", "번째", "가지고", "달러", "개국", "배터", "배우", "시청", "장관", "장면", "장소", "장군", "통계", "곡선",
             "자 회", "자회담", "자 대", "자대면", "자간", "자택", "자동"))   # 3자 회담·3자 대면은 '삼자'
        if 1 <= n <= 99 and counter and not (after.startswith("시간") and n >= 20):
            return ko_native(n)
        if n >= 100 and n % 10 and counter and not after.startswith(("시", "번", "배")):
            return ko_sino(n - n % 10) + ko_native(n % 10)   # 341곳 → 삼백사십한 곳 (끝자리만 고유어, 끝자리 0이면 아래에서 한자어)
        if n == 4 and after.startswith("번") and not after.startswith(("번째", "번이나", "번만", "번씩", "번도", "번을", "번 더")):
            return "네"          # '사 번'은 '사번(사원번호)'처럼 들림 → 네 번
        if (n % 10 == 4 and after.startswith("일") and not after.startswith(("일본", "일반", "일단", "일정", "일상", "일종", "일으", "일어", "일자", "일하"))
                and not (after.startswith("일부") and not after.startswith("일부터"))):
            return ko_sino(n) + " "   # 4일 → '사 일' (붙여 쓰면 성우가 '싸일'로 읽음)
        if n >= 1 and after.startswith("번째"):
            return "첫" if n == 1 else ko_native(n) if n <= 99 else ko_sino(n)
        if len(num) > 16:                                               # 너무 긴 숫자(전화번호 등)는 한 자리씩
            return " ".join(_KO_DIG[int(c)] for c in num)
        if len(num) > 1 and num.startswith("0"):                       # 007 같은 번호
            return " ".join(_KO_DIG[int(c)] for c in num)
        return ko_sino(n)
    t = re.sub(r"(\d+)(\.\d+)?", one, t)
    t = t.replace("&", " 앤 ").replace("+", " 플러스 ").replace("×", " 곱하기 ").replace("=", " 는 ")
    t = re.sub(r"[·ㆍ/]", " ", t)
    return t


_GEON_FOLLOW = r"(?!물|강|설|축|조|배|전|국|립|너|넌|넜|드|져|장|실|방|투|빵|반|평|재|망|들|달|성|초|기|의하|의했|의서|의사|의를)"   # 세는 말 '건' 뒤 (건물·건강·건너 등은 제외)
_GEON_WORD = r"(?:[일이삼사오육칠팔구십백천만억]{2,}|[십백천만]|수십|수백|수천|수만)"             # 한자 수: 붙여 써도 수량 (사백사십칠건)
_GEON_NATIVE = r"(?:한|두|세|네|다섯|여섯|일곱|여덟|아홉|열|스무|몇)"                          # 고유어 수: 띄어 쓴 '두 건'만 수량 ('두건'은 머리에 쓰는 천)


def geon_kkeon(t):
    """세는 말 '건'(件)은 숫자 뒤에서 [껀]으로 읽음: 1건 → 한 껀, 29건 → 스물아홉 껀, 447건 → 사백사십일곱 껀, 네 건 → 네 껀 ('이 건(이것)'·건물·건강·두건(머리에 쓰는 천)은 그대로)"""
    t = re.sub(r"(?<![\d.,])([1-9]\d?)\s?건" + _GEON_FOLLOW, lambda m_: ko_native(int(m_.group(1))) + " 껀", t)   # 1~99건 → 한 껀 … 스물아홉 껀 … 아흔아홉 껀
    def big_(m_):
        n = int(m_.group(1).replace(",", ""))
        return (ko_sino(n - n % 10) + ko_native(n % 10) if n % 10 else ko_sino(n)) + " 껀"
    t = re.sub(r"(?<![\d.])(\d{1,3}(?:,\d{3})+|[1-9]\d{2,})\s?건" + _GEON_FOLLOW, big_, t)   # 447건 → 사백사십일곱 껀
    t = re.sub(r"(\d)\s?건" + _GEON_FOLLOW, r"\1 껀", t)
    t = re.sub(r"(?<![가-힣])(" + _GEON_NATIVE + r")\s+건" + _GEON_FOLLOW, r"\1 껀", t)
    return re.sub(r"(?<![가-힣])(" + _GEON_WORD + r")\s?건" + _GEON_FOLLOW, r"\1 껀", t)


def read_korean(t):
    """한국어 문장의 건→껀, 전화번호, 낱말 '사번', 숫자를 한글 읽기로 (자막 글은 건드리지 않고 성우가 읽을 글만)"""
    t = geon_kkeon(t)                # 447건 → 447 껀 (숫자로 읽기 전에), 사백사십칠 건 → 사백사십칠 껀
    t = re.sub(r"(?<![\d])(\d{2,4})-(\d{3,4})(?:-(\d{4}))?(?!\d)",          # 전화번호 → 한 자리씩 (1833-6972 → 일팔삼삼 육구칠이)
               lambda m_: " ".join("".join(_KO_DIG[int(c)] for c in g) for g in m_.groups() if g), t)
    t = re.sub(r"(국번\s*없이|전화|번호는?|신고센터|콜센터)(\s*)(\d{3,4})(?=번|\s|[,.)]|$)",     # 국번 없이 118 → 일일팔
               lambda m_: m_.group(1) + m_.group(2) + "".join(_KO_DIG[int(c)] for c in m_.group(3)), t)
    t = re.sub(r"(?<![0-9가-힣])사번(은|이|을|과)?(?=[\s,.!?·:]|[도만의에처보까부]|$)",              # 낱말 '사번' ↔ 숫자 '4번' 구분
               lambda m_: "사원번호" + {"은": "는", "이": "가", "을": "를", "과": "와"}.get(m_.group(1) or "", ""), t)
    if re.search(r"\d", t):
        t = ko_numbers(t)
    return t


def say(text):
    """대본 한 줄 → 성우가 읽을 글 (미리 보기용: 사전 → 한국어 규칙)"""
    t = builtin_read(str(text or ""))
    return re.sub(r"\s+", " ", read_korean(t) if re.search(r"[가-힣]", t) else t).strip()


if __name__ == "__main__":
    if sys.argv[1:] or not sys.stdin.isatty():
        for line in sys.argv[1:] or [l for l in sys.stdin.read().splitlines() if l.strip()]:
            print(line, "\n  →", say(line))
    else:                               # 읽기_미리보기.bat: 문장을 넣을 때마다 성우가 읽을 글을 보여줌 (빈 줄 = 끝)
        print("대본 문장을 넣으면 성우가 읽을 글을 보여줍니다. 그냥 Enter = 끝. (읽기사전.txt 를 고치면 바로 반영)\n")
        while True:
            try:
                line = input("대본> ").strip()
            except EOFError:
                break
            if not line:
                break
            print("성우> " + say(line) + "\n")
