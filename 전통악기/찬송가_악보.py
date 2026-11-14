"""찬송가 ABC 악보 읽기 — Open Hymnal(openhymnal.org, 공개 저작물) 4성부 악보에서 성부별 음표를 꺼냄
  read(path) → {"key": "G", "meter": (3, 4), "unit": 0.25, "voices": {"S1V1": [(시작박, 길이박, midi)], …}}
  bars = 멜로디 마디줄 시각(박) — 못갖춘마디(첫 마디줄 전 짧은 시작)를 알 수 있음
  박 = 4분음표 1개. S1V1 = 소프라노(멜로디), S1V2 = 알토, S2V1 = 테너, S2V2 = 베이스
  (이 악보들에 쓰인 문법만: 음표·쉼표·붙임줄·조표·임시표·마디줄. 화음 묶음 [GB] 도 읽음. 도돌이·셋잇단음은 없음)
"""
import re
from fractions import Fraction

BASE = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
SHARPS = "FCGDAEB"
KEY_SIG = {"C": 0, "G": 1, "D": 2, "A": 3, "E": 4, "B": 5, "F#": 6, "F": -1, "Bb": -2, "Eb": -3, "Ab": -4, "Db": -5, "Gb": -6}
NOTE = re.compile(r"(\^\^|\^|__|_|=)?([A-Ga-gzx])([,']*)(\d*)(/*)(\d*)")
CHORD = re.compile(r"\[([^\]:]*)\](-?)")
TOKEN = re.compile(r"![^!]*!|\"[^\"]*\"|\[[A-Za-z]:[^\]]*\]|\[[^\]:]*\]-?|\|\]|\|\||\||[()]|-|(\^\^|\^|__|_|=)?([A-Ga-gzx])([,']*)(\d*)(/*)(\d*)|\S")


def key_acc(key):
    n = KEY_SIG[key]
    acc = {}
    for i in range(abs(n)):
        acc[(SHARPS if n > 0 else SHARPS[::-1])[i]] = 1 if n > 0 else -1
    return acc


def read(path):
    text = open(path, encoding="utf-8", errors="replace").read()
    head = lambda k: re.search(rf"^{k}:\s*([^%\n]*)", text, re.M).group(1).strip()
    key = head("K").split()[0]
    meter = tuple(int(x) for x in head("M").split("/"))
    unit = Fraction(head("L").replace(" ", ""))
    lines = {}
    for line in text.splitlines():
        m = re.match(r"\s*\[V:\s*(\w+)\]\s*(.*)", line)
        if m:
            lines.setdefault(m.group(1), []).append(m.group(2).split("%")[0])
    voices, bars = {}, []
    for v, parts in lines.items():
        sig = key_acc(key)
        bar_acc, t, tie = {}, Fraction(0), False
        top, bot = [], []   # 화음 묶음 [GB] 은 위 음 → top, 아래 음 → bot (홑음은 둘 다 같음)

        def pitch(acc_s, letter, octs):
            up = letter.upper()
            midi = 60 + BASE[up] + (12 if letter.islower() else 0) + 12 * octs.count("'") - 12 * octs.count(",")
            if acc_s:
                bar_acc[(up, midi // 12)] = {"^": 1, "^^": 2, "_": -1, "__": -2, "=": 0}[acc_s]
            return midi + bar_acc.get((up, midi // 12), sig.get(up, 0))

        def length(num, slashes, den):
            L = Fraction(int(num) if num else 1)
            if slashes:
                L /= int(den) if den else 2 ** len(slashes)
            return L * unit * 4   # 4분음표 박 단위

        def add(out, midi, dur):
            if tie and out and out[-1][2] == midi and out[-1][0] + out[-1][1] == t:
                st, d, mm = out[-1]
                out[-1] = (st, d + dur, mm)
            else:
                out.append((t, dur, midi))

        for tok in TOKEN.finditer(" ".join(parts)):
            s = tok.group(0)
            if s.startswith("|"):
                bar_acc = {}
                if v in ("S1V1", "S1") and float(t) not in bars:
                    bars.append(float(t))
                continue
            if s == "-":
                tie = True
                continue
            chord = CHORD.fullmatch(s)
            if chord:
                notes = NOTE.findall(chord.group(1))
                if not notes:
                    continue
                dur = length(*notes[0][3:])
                ms = [pitch(a, l, o) for a, l, o, *_ in notes if l not in "zx"]
                tie_next = chord.group(2) == "-"
            elif tok.group(2):
                acc_s, letter, octs, num, slashes, den = tok.groups()
                dur = length(num, slashes, den)
                ms = [] if letter in "zx" else [pitch(acc_s, letter, octs)]
                tie_next = False
            else:
                continue
            if ms:
                add(top, max(ms), dur)
                add(bot, min(ms), dur)
            tie = tie_next
            t += dur
        conv = lambda out: [(float(a), float(b), c) for a, b, c in out]
        if re.fullmatch(r"S\d", v):   # 두 성부를 한 줄에 화음으로 적은 악보 (S1 = 소프라노+알토, S2 = 테너+베이스)
            voices[v + "V1"], voices[v + "V2"] = conv(top), conv(bot)
        else:
            voices[v] = conv(top)
    return {"key": key, "meter": meter, "unit": float(unit), "voices": voices, "bars": bars}


if __name__ == "__main__":
    import sys
    for p in sys.argv[1:]:
        r = read(p)
        ends = {v: round(n[-1][0] + n[-1][1], 3) for v, n in r["voices"].items()}
        print(p, r["key"], r["meter"], ends)
        print("  멜로디 처음:", " ".join(f"{m}:{d:g}" for _, d, m in r["voices"]["S1V1"][:14]))
