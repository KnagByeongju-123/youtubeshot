r"""나레이션 검증 모듈 - 문단마다 성우 소리를 만든 뒤 바로 검사

  1) 기본 검사 (항상)
     - 성우에게 넘긴 글에 아라비아 숫자·영어가 남았는지 (남으면 성우가 엉뚱하게 읽기 쉬움)
     - 소리가 비었거나(무음) 글 길이에 비해 너무 짧거나 길지 않은지 (건너뛰기·되풀이·늘어짐)
     - 문장 가운데 긴 무음(1.5초 넘게)이 없는지
  2) 듣기 검사 (Whisper 음성 인식이 깔려 있으면)
     - 성우 소리를 글로 받아 적어 대본과 비교. 'AI → 에이'처럼 다르게 읽은 낱말을 찾음
  걸리면 한 번 다시 녹음(Supertonic 은 다듬기 단계를 바꿔서)하고, 더 나은 쪽을 씀.
  그래도 걸리면 기록만 남기고 계속 (영상 만들기는 멈추지 않음) → <영상이름>_나레이션검증.txt

  설정: '나레이션 검증' (on / 기본만 / off), 기본 on
  Whisper 설치:  py -3.11 -m pip install faster-whisper   (모델은 처음 쓸 때 models\whisper 에 받음, 약 500MB)
"""
import difflib
import hashlib
import json
import os
import re
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
WHISPER_SIZE = "small"
WHISPER_DIR = os.path.join(HERE, "models", "whisper")
PASS_SIMILAR = 0.80         # 듣기 검사: 대본과 받아 적은 글이 이만큼(80%) 비슷하면 통과
SPEED_RANGE = (2.5, 11.0)   # 1초에 읽는 글자 수(한글) 정상 범위
LONG_SILENCE = 1.5          # 문장 가운데 무음이 이보다 길면 문제
CHECK_FILE = "나레이션검증.json"   # tts_cache 안: 이미 검사한 소리는 다시 검사하지 않음

_W = {"model": None, "tried": False, "error": ""}
_DONE = {}


def _kr():
    m = sys.modules.get("한국어_읽기")
    if m is None:
        import importlib.util
        spec = importlib.util.spec_from_file_location("한국어_읽기", os.path.join(HERE, "한국어_읽기.py"))
        m = importlib.util.module_from_spec(spec)
        sys.modules["한국어_읽기"] = m
        spec.loader.exec_module(m)
    return m


def whisper():
    """Whisper 모델 (없으면 None). 처음 한 번만 불러옴"""
    if not _W["tried"]:
        _W["tried"] = True
        try:
            from faster_whisper import WhisperModel
            os.makedirs(WHISPER_DIR, exist_ok=True)
            _W["model"] = WhisperModel(WHISPER_SIZE, device="cpu", compute_type="int8", download_root=WHISPER_DIR)
        except Exception as e:
            _W["error"] = str(e).splitlines()[0][:120] if str(e) else type(e).__name__
    return _W["model"]


def listen(audio, sr):
    """성우 소리 → 받아 적은 글"""
    w = whisper()
    if w is None:
        return None
    a = np.asarray(audio, np.float32)
    if a.ndim > 1:
        a = a.mean(axis=1)
    if sr != 16000:                     # Whisper 는 16kHz
        n = int(len(a) * 16000 / sr)
        a = np.interp(np.linspace(0, len(a) - 1, n), np.arange(len(a)), a).astype(np.float32)
    segs, _ = w.transcribe(a, language="ko", beam_size=1, condition_on_previous_text=False, vad_filter=False)
    return " ".join(s_.text.strip() for s_ in segs).strip()


def _norm(t):
    """비교용: 숫자·영어를 읽는 소리로 바꾸고 띄어쓰기·문장부호는 뺌"""
    kr = _kr()
    t = kr.builtin_read(t or "")
    if re.search(r"[가-힣]", t):
        t = kr.read_korean(t)
    return re.sub(r"[^가-힣A-Za-z]", "", t)


def _diff_words(said, heard):
    """대본과 다르게 들린 부분 → ['에이아이 → 에이', ...]"""
    a, b = _norm(said), _norm(heard)
    out = []
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if op != "equal":
            out.append(f"{a[i1:i2] or '(없음)'} → {b[j1:j2] or '(빠짐)'}")
    return out


def similarity(said, heard):
    a, b = _norm(said), _norm(heard)
    if not a:
        return 1.0
    return difflib.SequenceMatcher(None, a, b, autojunk=False).ratio()


def key_words_missed(said, heard, original=""):
    """읽기사전 낱말(에이아이·쓰리디 …)이 대본에 나온 만큼 들렸는지 → 덜 들린 낱말 목록 ('에이아이'를 '에이'로 읽은 것 찾기)
    original(자막 글)이 있으면 그 글에 실제로 나온 영어 낱말만 확인 (B=비 와 '비석'을 헷갈리지 않게)"""
    a, b = _norm(said), _norm(heard)
    out = []
    for src, v in _kr().read_dict():
        if original and not re.search(r"(?<![A-Za-z0-9])" + re.escape(src) + r"(?![A-Za-z])", original):
            continue
        say_ = re.sub(r"[^가-힣A-Za-z]", "", v)
        if say_ and say_ not in out and a.count(say_) > b.count(say_):
            out.append(say_)
    return out


def _longest_silence(a, sr):
    a = np.asarray(a, np.float32)
    if a.ndim > 1:
        a = a.mean(axis=1)
    win = max(1, int(sr * 0.05))
    n = len(a) // win
    if n < 3:
        return 0.0
    rms = np.sqrt(np.mean(a[:n * win].reshape(n, win) ** 2, axis=1))
    quiet = rms < max(1e-4, float(np.percentile(rms, 90)) * 0.03)
    idx = np.nonzero(~quiet)[0]
    if len(idx) == 0:
        return n * 0.05
    inner = quiet[idx[0]:idx[-1] + 1]     # 앞뒤 무음은 빼고 가운데만
    best = run = 0
    for q in inner:
        run = run + 1 if q else 0
        best = max(best, run)
    return best * 0.05


def basic_check(spoken, audio, dur, sr, rate_pct=0.0):
    """기본 검사 → 문제 목록 (빈 목록 = 통과)"""
    issues = []
    left = re.findall(r"[0-9]+|[A-Za-z]{2,}", spoken or "")
    if left:
        issues.append("한글로 못 바꾼 글자: " + ", ".join(dict.fromkeys(left)))
    a = np.asarray(audio, np.float32)
    if len(a) < 10 or float(np.abs(a).max()) < 0.01:
        return issues + ["소리가 비어 있음"]
    syl = len(re.findall(r"[가-힣]", spoken or ""))
    if syl >= 8 and dur > 0:
        sp = syl / dur / (1 + float(rate_pct or 0) / 100)
        if sp < SPEED_RANGE[0]:
            issues.append(f"글에 비해 너무 김 (1초 {sp:.1f}자) - 늘어지거나 되풀이했을 수 있음")
        elif sp > SPEED_RANGE[1]:
            issues.append(f"글에 비해 너무 짧음 (1초 {sp:.1f}자) - 건너뛰었을 수 있음")
    gap = _longest_silence(a, sr)
    if gap > LONG_SILENCE:
        issues.append(f"가운데 긴 무음 {gap:.1f}초")
    return issues


def _load(cache_dir):
    if cache_dir not in _DONE:
        try:
            _DONE[cache_dir] = json.load(open(os.path.join(cache_dir, CHECK_FILE), encoding="utf-8"))
        except (OSError, ValueError):
            _DONE[cache_dir] = {}
    return _DONE[cache_dir]


def _save(cache_dir):
    try:
        p = os.path.join(cache_dir, CHECK_FILE)
        with open(p + ".tmp", "w", encoding="utf-8") as f:
            json.dump(_DONE.get(cache_dir, {}), f, ensure_ascii=False, indent=0)
        os.replace(p + ".tmp", p)
    except OSError:
        pass


def check(spoken, audio, dur, sr, cache_dir, rate_pct=0.0, listen_on=True, original=""):
    """문단 하나 검사 → {"ok": bool, "issues": [...], "heard": 받아 적은 글, "score": 비슷한 정도}
    같은 소리는 결과를 저장해 두고 다시 검사하지 않음"""
    a = np.asarray(audio, np.float32)
    key = hashlib.md5(a.tobytes() + (spoken or "").encode("utf-8") + (b"L" if listen_on else b"B") + original.encode("utf-8")).hexdigest()
    done = _load(cache_dir)
    if key in done:
        return done[key]
    issues = basic_check(spoken, a, dur, sr, rate_pct)
    heard, score = None, None
    if listen_on and "소리가 비어 있음" not in issues:
        try:
            heard = listen(a, sr)
        except Exception as e:
            heard = None
            _W["error"] = "듣기 실패: " + str(e)[:80]
        if heard is not None:
            score = round(similarity(spoken, heard), 3)
            if score < PASS_SIMILAR:
                issues.append(f"들은 글이 대본과 다름 ({score * 100:.0f}%): " + " / ".join(_diff_words(spoken, heard)[:6]))
            sigh = re.match(r"\s*(휴+|후우*|하아+|흐음*|흠+|에휴|아휴|쓰읍)[\s.,~…!]", heard or "")
            if sigh and not re.match(r"\s*" + re.escape(sigh.group(1)), spoken or ""):   # 규칙: 말 시작에 한숨 소리가 나오면 안 됨
                issues.append(f"시작에 한숨·숨소리('{sigh.group(1)}')")
            missed = key_words_missed(spoken, heard, original)
            if missed:      # 긴 문단에서 한 낱말만 틀리면 비슷한 정도는 높게 나오므로 읽기사전 낱말은 따로 확인
                issues.append("읽기사전 낱말을 다르게 읽음: " + ", ".join(missed))
    res = {"ok": not issues, "issues": issues, "heard": heard, "score": score}
    done[key] = res
    _save(cache_dir)
    return res


def mode_of(s):
    v = str((s or {}).get("narr_check", "on")).strip()
    return {"on": "on", "기본만": "basic", "off": "off"}.get(v, "on")


REPORT = []     # 마지막 나레이션의 검증 기록 [(문단번호, 대본, 결과)] - render_project 가 파일로 저장


def report_text(title=""):
    bad = [r for r in REPORT if not r[2]["ok"]]
    lines = [f"나레이션 검증 기록 - {title}", f"검사한 문단 {len(REPORT)}개 · 문제 남은 문단 {len(bad)}개",
             "(문제가 남은 문단은 한 번 다시 녹음한 뒤에도 걸린 것. 들어 보고 이상하면 읽기사전.txt 에 읽는 법을 적어 다시 만드세요)", ""]
    if _W["error"]:
        lines.append("※ 듣기 검사를 못 함: " + _W["error"] + "  (기본 검사만 했어요)\n")
    for k, text, r in REPORT:
        if r["ok"]:
            continue
        lines.append(f"[{k + 1}번째 문단] {text[:80]}")
        for it in r["issues"]:
            lines.append("   - " + it)
        if r.get("heard"):
            lines.append("   들린 글: " + r["heard"][:120])
        lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":      # 시험: py -3.11 -X utf8 나레이션_검증.py 소리.wav "대본 문장"
    import wave
    with wave.open(sys.argv[1], "rb") as w:
        sr_, ch_ = w.getframerate(), w.getnchannels()
        x = np.frombuffer(w.readframes(w.getnframes()), "<i2").astype(np.float32) / 32768
    x = x.reshape(-1, ch_).mean(axis=1)
    print(json.dumps(check(sys.argv[2], x, len(x) / sr_, sr_, os.path.join(HERE, "output", "tts_cache")), ensure_ascii=False, indent=1))
