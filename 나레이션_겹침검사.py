"""나레이션 겹침 검사 — 성우가 같은 소리를 두 번 읽은 곳('닿을 것만만', '미역국국')을 찾아 그 문장을 다시 녹음하게 함 (.sd_venv 에서 실행)
python 나레이션_겹침검사.py <영상.mp4> <회차.py 또는 대본.txt> [--고치기 <프로젝트.json>] [--결과 <결과.txt>]
  - Whisper 는 '것만만'을 '것만'으로 고쳐 적어서 못 찾음 → 소리를 글자 그대로 적는 wav2vec2(CTC) 한국어 모델로 받아 적음
    (kresnik/wav2vec2-large-xlsr-korean, 처음 한 번 약 1.2GB 받음. 검사에만 쓰고 영상에는 안 들어감)
  - 찾는 규칙
    1) 소리를 쉼에서 15초 안쪽 조각으로 나눠 받아 적음
    2) 같은 글자 1~3자가 연달아 두 번 나오면(띄어쓰기 무시: '것만 만', '국국') 후보
    3) 반복 바로 앞 글자들과 가장 비슷한 대본 문장을 찾아(숫자가 든 문장은 '1월 1일→일월 일일'처럼 원래 반복이 생겨서 뺌), 그 문장에 원래 같은 길이의 반복(무럭무럭·불쑥불쑥·타닥타닥)이 있으면 흉내말로 보고 넘김
    4) 대본 문장과 한 글자씩 맞춰 봐서 반복 자리에 글자가 '더 들어갔을' 때만 겹침 ('것만→것만만'). 글자 수가 같으면 발음 차이로 봄
       ('하늘나라→하늘라라', '닿을→다을')
  - 갑자기 빨라진 곳도 찾음: 쉼과 쉼 사이 한 마디씩 1초당 글자 수를 재서 영상 전체 마디의 중간값보다 25% 넘게 빠른 마디 (대사는 인물마다 빠르기가 달라 뺌)
  - --고치기 <프로젝트.json> : 겹친 문장(과 그 문단)의 녹음 캐시를 output/tts_cache 에서 지움 → render_project 를 다시 돌리면 그 문장만 새로 녹음.
    빨라진 문장도 캐시를 지워 다시 녹음만 함. 녹음을 억지로 늘리지 않음(늘어져 들림) — 영상 길이가 나레이션에 맞춰짐
    (Supertonic 은 매번 조금씩 다르게 읽어서 보통 한 번에 고쳐짐. 다시 만든 영상도 검사해서 '겹침 없음'이 나올 때까지, 최대 3번)
  - 결과: '분:초 [겹친 글자] 대본: <문장> | 들림: <받아 적은 글>'
  - 늘어진 곳(강제 정렬): 대본 글자(성우가 읽은 글)를 소리에 한 글자씩 맞춰(CTC 비터비 정렬, torchaudio forced_align 과 같은 방법)
    글자 하나가 보통 글자의 3배·0.4초 넘게 소리를 끄는 곳 ('다아아')
  - 어색한 문장(UTMOS): 문장마다 말소리 자연스러움 점수(오픈소스 SpeechMOS UTMOS22, MIT, 외부도구/speechmos)를 매겨 중간값보다 0.7점 넘게 낮고 3점 아래인 문장
    (가중치 models/utmos22_strong_step7459_v1.pt 가 없으면 건너뜀). --고치기 면 둘 다 그 문장을 다시 녹음
  - --프로젝트 <프로젝트.json> : 고치지 않고 검사만 할 때도 읽기 설정(숫자 읽기 등)을 맞춤 (--고치기 면 자동)
(내부용) python 나레이션_겹침검사.py --지우기 <목록.json> <프로젝트.json>  ← .supertonic_venv 로 실행, 캐시 이름 계산·삭제"""
import difflib
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SR = 16000
MODEL = "kresnik/wav2vec2-large-xlsr-korean"
MOODS = ["차분", "공포·긴장", "슬픔·감동", "놀람·반전", "분노·갈등", "밝음·유머"]


def hangul(t):
    return re.sub(r"[^가-힣]", "", t)


def script_paragraphs(path):
    """대본에서 읽는 문단만 (그림 자리·장 제목 빼고)"""
    if path.endswith(".py"):
        spec = importlib.util.spec_from_file_location("ep", path)
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        text = m.STORY
    else:
        text = open(path, encoding="utf-8").read()
    return [p.strip() for p in re.split(r"\n\s*\n", text)
            if p.strip() and not re.match(r"^(\{c\d+\}|\[사진:|#)", p.strip())]


def sentences(par):
    return [s.strip() for s in re.split(r"(?<=[.!?…])\s+", par) if s.strip()]


def doubles(h, n):
    return {h[i:i + n] * 2 for i in range(len(h) - 2 * n + 1) if h[i:i + n] == h[i + n:i + 2 * n]}


def chunks(a):
    """쉼(작은 소리 0.3초 이상)에서 끊어 15초 안쪽 조각 [(시작, 끝)]"""
    import numpy as np
    fr = int(0.02 * SR)
    n = len(a) // fr
    rms = np.sqrt((a[:n * fr].reshape(n, fr) ** 2).mean(1))
    quiet = rms < max(1e-4, np.percentile(rms, 95) * 0.03)
    out, start, k = [], 0, 0
    while k < n:
        if quiet[k]:
            j = k
            while j < n and quiet[j]:
                j += 1
            if j - k >= 15 and (k - start) * 0.02 >= 4:     # 0.3초 이상 쉼, 조각은 4초 이상
                out.append((start * 0.02, k * 0.02))
                start = j
            elif (k - start) * 0.02 >= 15:
                out.append((start * 0.02, k * 0.02))
                start = k
            k = j
        else:
            k += 1
    if n - start > 10:
        out.append((start * 0.02, n * 0.02))
    return out


def extra_syllables(ref, heard, i, n):
    """heard[i:i+n](반복 자리)에서 대본보다 글자가 더 들어갔나 — '것만→것만만'은 예, '나라→라라'(발음)·'역국→욕욕'은 아니오"""
    sm = difflib.SequenceMatcher(None, ref, heard, autojunk=False)
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if j2 <= i or j1 >= i + n:
            continue
        if op == "insert" or (op == "replace" and (j2 - j1) > (i2 - i1)):
            return True
    return False


def sentence_of(piece, sents):
    """짧은 조각(반복 바로 앞 글자들)이 어느 대본 문장 속에 들어 있나 — 조각 글자가 문장에 얼마나 맞나로 고름"""
    best, score = None, 0.0
    for par, s in sents:
        sm = difflib.SequenceMatcher(None, hangul(s), piece, autojunk=False)
        hit = sum(b.size for b in sm.get_matching_blocks()) / max(1, len(piece))
        if hit > score:
            best, score = (par, s), hit
    return best if score >= 0.6 else None


def best_sentence(h, sents):
    """받아 적은 조각(한글만)이 들어 있는 대본 문장 — 반복 글자 자리에 가장 잘 맞는 문장 하나"""
    best, score = None, 0.0
    for par, s in sents:
        sh = hangul(s)
        if len(sh) < 5:          # '엄마...' 같은 아주 짧은 문장은 어디에나 맞아 버림
            continue
        sm = difflib.SequenceMatcher(None, sh, h, autojunk=False)
        hit = sum(b.size for b in sm.get_matching_blocks()) / len(sh)      # 문장 글자가 조각에 얼마나 들어 있나
        if hit > score:
            best, score = (par, s), hit
    return best if score >= 0.55 else None


def fast_spots(sylls, sents, ratio=1.25, gap=0.3, min_syl=8):
    """갑자기 빨라진 곳: 쉼(0.3초 넘는 틈) 사이 한 마디씩 1초당 글자 수를 재서, 영상 전체 마디의 중간값보다 25% 넘게 빠른 마디.
    (1화에서 '잠시 뒤, 그 이야기를 들려 드릴게요'가 43% 빨랐음 — 짧은 문장을 서둘러 읽는 일이 있음) 대사(따옴표)는 인물마다 빠르기가 달라 뺌"""
    import numpy as np
    phrases, cur = [], [sylls[0]] if sylls else []
    for a_, b_ in zip(sylls, sylls[1:]):
        if b_[1] - a_[1] > gap:
            phrases.append(cur)
            cur = [b_]
        else:
            cur.append(b_)
    if cur:
        phrases.append(cur)
    rated = [(ph, (len(ph) - 1) / (ph[-1][1] - ph[0][1])) for ph in phrases if len(ph) >= min_syl and ph[-1][1] > ph[0][1]]
    if len(rated) < 10:
        return []
    med = float(np.median([r for _, r in rated]))
    out = []
    for ph, r in rated:
        if r <= med * ratio:
            continue
        h = "".join(c for c, _ in ph)
        ps = best_sentence(h, sents)
        if ps is None or ps[1].lstrip().startswith(('"', '“')):
            continue
        out.append({"t": ph[0][1], "speed": r / med, "dd": f"빠름 {r:.1f}자/초(보통 {med:.1f}, +{(r / med - 1) * 100:.0f}%)",
                    "sentence": ps[1], "paragraph": ps[0], "heard": h})
    return out


def spoken_script(sents, project):
    """대본 문장마다 성우가 실제로 읽는 글(숫자 → 한글 읽기, 읽기 사전)을 한글만 이어 붙임 + 글자마다 몇 번째 문장인지.
    읽는 글 바꾸기는 프로그램(.supertonic_venv)에 있어서 그쪽으로 물어봄. 안 되면 대본 글자 그대로"""
    texts = [s_ for _, s_ in sents]
    tmp = os.path.join(tempfile.gettempdir(), "겹침_말소리.json")
    try:
        json.dump(texts, open(tmp, "w", encoding="utf-8"), ensure_ascii=False)
        r = subprocess.run([PY_ST, "-X", "utf8", os.path.abspath(__file__), "--말소리", tmp] + ([project] if project else []),
                           capture_output=True, check=True, timeout=600)
        spoken = json.load(open(tmp, encoding="utf-8"))
    except Exception:
        spoken = texts
    all_, owner = [], []
    for k, t in enumerate(spoken):
        h = hangul(t)
        all_.append(h)
        owner += [k] * len(h)
    return "".join(all_), owner


def ctc_align(lp, tokens, blank):
    """CTC 강제 정렬(비터비) — torchaudio.functional.forced_align 과 같은 방법. lp: (칸, 낱말표) 로그 확률.
    반환: 칸마다 몇 번째 글자인지(-1 = 빈칸) 또는 None(칸이 모자람)"""
    import numpy as np
    T, L = lp.shape[0], len(tokens)
    if L == 0 or T < L:
        return None
    ext = [blank]
    for t_ in tokens:
        ext += [t_, blank]
    ext = np.array(ext)
    S, NEG = len(ext), -1e30
    emit = lp[:, ext]
    skip = np.zeros(S, bool)
    skip[2:] = (ext[2:] != blank) & (ext[2:] != ext[:-2])
    dp = np.full(S, NEG)
    dp[0], dp[1] = emit[0, 0], emit[0, 1]
    bp = np.zeros((T, S), np.int8)
    for t in range(1, T):
        one = np.concatenate([[NEG], dp[:-1]])
        two = np.concatenate([[NEG, NEG], dp[:-2]])
        two[~skip] = NEG
        st = np.stack([dp, one, two])
        arg = st.argmax(0)
        dp = st[arg, np.arange(S)] + emit[t]
        bp[t] = arg
    s_ = S - 1 if dp[S - 1] >= dp[S - 2] else S - 2
    path = np.zeros(T, int)
    for t in range(T - 1, -1, -1):
        path[t] = (s_ - 1) // 2 if s_ % 2 else -1
        s_ -= int(bp[t, s_])
    return path


def syllable_spans(tf, qs, spoken_all, owner, x, off, step):
    """정렬 결과로 글자마다 (시작 시각, 길이, 그동안 소리가 난 비율, 문장 번호)"""
    import numpy as np
    fr_ = max(1, int(0.02 * SR))
    n_ = len(x) // fr_
    rms_ = np.sqrt((x[:n_ * fr_].reshape(n_, fr_) ** 2).mean(1)) if n_ else np.zeros(1)
    loud = max(1e-4, float(np.percentile(rms_, 90)) * 0.12)
    first = {}
    for k, ti in enumerate(tf):
        if ti >= 0 and ti not in first:
            first[ti] = k
    out = []
    for ti in range(len(qs)):
        if ti not in first:
            continue
        k0 = first[ti]
        k1 = first.get(ti + 1, max([k for k, t_ in enumerate(tf) if t_ == ti]) + 1)
        a0 = int(k0 * step / 0.02)
        a1 = max(a0 + 1, int(k1 * step / 0.02))
        seg_ = rms_[a0:a1]
        out.append({"ch": spoken_all[qs[ti]], "t": off + k0 * step, "dur": (k1 - k0) * step,
                    "voiced": float((seg_ > loud).mean()) if len(seg_) else 0.0, "sent": owner[qs[ti]],
                    "end": off + (max([k for k, t_ in enumerate(tf) if t_ == ti]) + 1) * step})
    return out


def stretch_spots(aligned, sents, ratio=3.0, min_sec=0.4):
    """늘어진 곳: 강제 정렬로 잰 글자 하나의 길이가 보통 글자의 3배 넘게(그리고 0.4초 넘게) 길고, 그동안 소리가 계속 나는 곳
    ('다아아' 처럼 끄는 소리. 쉼은 소리가 없어서 빠짐)"""
    import numpy as np
    durs = [s_["dur"] for s_ in aligned if s_["dur"] < 0.6]
    if len(durs) < 50:
        return []
    med = float(np.median(durs))
    out = []
    for s_ in aligned:
        if s_["dur"] <= max(min_sec, med * ratio) or s_["voiced"] < 0.8:
            continue
        par, sent = sents[s_["sent"]]
        if sent.lstrip().startswith(('"', '“')):
            continue
        out.append({"t": s_["t"], "dd": f"늘어짐 '{s_['ch']}' {s_['dur']:.2f}초(보통 글자 {med:.2f}초)",
                    "sentence": sent, "paragraph": par, "heard": ""})
    return out


def utmos_spots(a, aligned, sents, drop=0.7, floor=3.0):
    """어색한 문장: 문장마다 UTMOS(말소리 자연스러움 1~5점, 오픈소스 SpeechMOS·MIT)를 매겨,
    영상 전체 문장의 중간값보다 0.7점 넘게 낮고 3.0점 아래인 문장 (기계음·지직거림·이상한 억양). 가중치가 없으면 건너뜀"""
    import numpy as np
    w = os.path.join(HERE, "models", "utmos22_strong_step7459_v1.pt")
    if not os.path.exists(w) or not aligned:
        return []
    import torch
    sys.path.insert(0, os.path.join(HERE, "외부도구"))
    from speechmos.utmos22.strong.model import UTMOS22Strong
    um = UTMOS22Strong()
    um.load_state_dict(torch.load(w, map_location="cpu", weights_only=True))
    um.eval()
    rng = {}
    for s_ in aligned:
        r = rng.setdefault(s_["sent"], [s_["t"], s_["end"]])
        r[0], r[1] = min(r[0], s_["t"]), max(r[1], s_["end"])
    scores = {}
    for k, (t0, t1) in rng.items():
        if t1 - t0 < 1.0:
            continue
        seg_ = a[int(max(0, t0 - 0.05) * SR):int((t1 + 0.15) * SR)].copy()
        with torch.no_grad():
            scores[k] = float(um(torch.tensor(seg_).unsqueeze(0), SR).item())
    if len(scores) < 10:
        return []
    med = float(np.median(list(scores.values())))
    UTMOS_REPORT[:] = [(rng[k][0], v, sents[k][1]) for k, v in sorted(scores.items())]
    out = []
    for k, v in scores.items():
        if v < med - drop and v < floor and not sents[k][1].lstrip().startswith(('"', '“')):
            out.append({"t": rng[k][0], "dd": f"어색함 {v:.2f}점(보통 {med:.2f}점)", "sentence": sents[k][1],
                        "paragraph": sents[k][0], "heard": ""})
    return out


UTMOS_REPORT = []
PY_ST = os.path.join(HERE, ".supertonic_venv", "Scripts" if os.name == "nt" else "bin", "python.exe" if os.name == "nt" else "python")


def detect(video, script, project=None):
    import numpy as np
    import torch
    from transformers import AutoModelForCTC, AutoProcessor
    pars = script_paragraphs(script)
    sents = [(p, s) for p in pars for s in sentences(p)]
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", video, "-vn", "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    a = np.frombuffer(raw, np.float32)
    torch.set_num_threads(max(1, os.cpu_count() or 4))
    p = AutoProcessor.from_pretrained(MODEL)
    m = AutoModelForCTC.from_pretrained(MODEL).eval()
    found, sylls, aligned = [], [], []          # sylls: (글자, 시각초) - 말 빠르기 재기용, aligned: 강제 정렬한 글자마다 길이
    blank = p.tokenizer.pad_token_id
    vocab = {k_: v_ for k_, v_ in p.tokenizer.get_vocab().items() if re.fullmatch(r"[가-힣]", k_)}
    spoken_all, owner = spoken_script(sents, project)       # 성우가 실제로 읽은 글(한글만) + 글자마다 몇 번째 문장인지
    pos = 0
    whole = hangul(" ".join(s_ for _, s_ in sents))          # 대본 전체 (반복이 대본 어딘가에 원래 있으면 겹침 아님)
    for t0, t1 in chunks(a):
        off = max(0, t0 - 0.15)
        x = a[int(off * SR):int((t1 + 0.15) * SR)]
        with torch.no_grad():
            logits = m(**p(x, sampling_rate=SR, return_tensors="pt")).logits
        ids = logits.argmax(-1)
        text = p.batch_decode(ids)[0]
        h = hangul(text)
        seq = ids[0].tolist()
        step = len(x) / SR / max(1, len(seq))       # 한 칸(약 0.02초)
        prev = None
        for k, tid in enumerate(seq):               # 글자가 처음 나온 칸 = 그 글자를 말한 시각
            if tid != prev and tid != blank:
                ch = p.tokenizer.convert_ids_to_tokens(tid)
                if re.fullmatch(r"[가-힣]", ch or ""):
                    sylls.append((ch, off + k * step))
            prev = tid
        # 강제 정렬: 이 조각에 해당하는 대본(성우가 실제로 읽은 글, 숫자는 한글 읽기) 글자를 찾아 소리에 한 글자씩 맞춤
        if spoken_all:
            win = spoken_all[pos:pos + int(len(h) * 1.6) + 30]
            sm_ = difflib.SequenceMatcher(None, win, h, autojunk=False)
            blocks = [b_ for b_ in sm_.get_matching_blocks() if b_.size >= 2]
            if h and blocks and sum(b_.size for b_ in blocks) / len(h) >= 0.5:
                g0, g1 = pos + blocks[0].a, pos + blocks[-1].a + blocks[-1].size
                keep = [(q, vocab[spoken_all[q]]) for q in range(g0, g1) if spoken_all[q] in vocab]
                if keep:
                    lp = torch.log_softmax(logits[0], -1).numpy()
                    tf = ctc_align(lp, [t_ for _, t_ in keep], blank)
                    if tf is not None:
                        aligned += syllable_spans(tf, [q for q, _ in keep], spoken_all, owner, x, off, step)
                pos = g1
        for n in (1, 2, 3):
            for dd in sorted(doubles(h, n)):
                i = h.find(dd)
                ctx = h[max(0, i - 8):i + 2 * n + 8]                 # 반복 자리 앞뒤
                before = h[max(0, i - 10):i + n]                      # 반복 바로 앞 글자들 (뒤는 다음 문장에 걸치기 쉬움)
                ps = sentence_of(before, sents) or best_sentence(ctx, sents) or best_sentence(h, sents)
                if ps is None:
                    continue
                if re.search(r"\d", ps[1]):                           # 숫자는 소리로 읽으면 반복이 생김 ('1월 1일' → 일월 일일)
                    continue
                sh = hangul(ps[1])
                k_ = sents.index(ps)
                near = hangul(" ".join(x[1] for x in sents[max(0, k_ - 1):k_ + 2]))   # 앞뒤 문장까지 (조각이 문장 경계에 걸침)
                if doubles(sh, n) or dd in near or dd in whole:   # 규칙 3: 대본에 원래 같은 반복(흉내말 '줄줄이·무럭무럭', '하나하나')이 있음
                    continue
                if not extra_syllables(sh, ctx, ctx.find(dd), len(dd)):   # 규칙 4: 대본보다 글자가 늘어난 자리여야 겹침
                    continue
                found.append({"t": t0, "dd": dd, "sentence": ps[1], "paragraph": ps[0], "heard": text})
    try:
        json.dump(sylls, open(os.path.join(tempfile.gettempdir(), "겹침_글자시각.json"), "w", encoding="utf-8"), ensure_ascii=False)
    except OSError:
        pass
    found += fast_spots(sylls, sents)
    found += stretch_spots(aligned, sents)
    found += utmos_spots(a, aligned, sents)
    uniq, seen = [], set()
    for f in found:
        if f["sentence"] not in seen:
            seen.add(f["sentence"])
            uniq.append(f)
    return uniq


def delete_caches(items, project):
    """(.supertonic_venv) 겹친 문장·그 문단의 녹음 캐시 이름을 프로그램과 같은 방법으로 계산해 지움"""
    sys.path.insert(0, HERE)
    spec = importlib.util.spec_from_file_location("snm", os.path.join(HERE, "shorts_novel_maker_supertonic.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    proj = json.load(open(project, encoding="utf-8"))
    st = proj.get("settings") or {}
    voices = {(m.voice_code(st.get("narr_voice", "")), float(st.get("narr_rate", 5) or 0))}
    for c in proj.get("cast") or []:                       # 대사는 그 인물 목소리로 녹음됨
        v = c.get("voice") or {}
        if v.get("code"):
            voices.add(("supertonic:" + v["code"], float(v.get("rate", 0) or 0)))
    pitch, steps = float(st.get("narr_pitch", 0) or 0), int(st.get("st_steps", 5) or 5)
    cache = os.path.join(HERE, "output", "tts_cache")
    # 빨라진 문장도 겹친 문장처럼 지우고 다시 녹음만 함. 녹음을 억지로 늘리지 않음 (늘리면 말이 늘어져 들림, 사용자 결정)
    # 영상 길이는 나레이션 길이에 맞춰 정해지므로 다시 녹음한 길이 그대로 씀
    texts = set()
    for it in items:
        for t in (it["sentence"], it["paragraph"]):
            for v in (t, t.strip('"“”'), m.spoken_src(t)):
                texts.add(m.tts_clean(v))
    gone = 0
    for t in texts:
        for vc, rate in voices:
            for mood in MOODS:
                f = os.path.join(cache, m.tts_key(vc, rate, pitch, m.supertonic_cache_text(t, mood, steps)) + ".npy")
                if os.path.exists(f):
                    os.remove(f)
                    gone += 1
    print(f"지운 녹음 캐시 {gone}개")


def main(a):
    if a and a[0] == "--말소리":               # (내부용, .supertonic_venv) 문장마다 성우가 읽는 글로 바꿔 같은 파일에 다시 씀
        sys.path.insert(0, HERE)
        spec = importlib.util.spec_from_file_location("snm", os.path.join(HERE, "shorts_novel_maker_supertonic.py"))
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        if len(a) > 2:
            st = json.load(open(a[2], encoding="utf-8")).get("settings") or {}
            m.set_tts_cfg(st)
        m.spoken_load(os.path.join(HERE, "output", "tts_cache"))
        texts = json.load(open(a[1], encoding="utf-8"))
        json.dump([m.tts_clean(t) for t in texts], open(a[1], "w", encoding="utf-8"), ensure_ascii=False)
        return 0
    if a and a[0] == "--지우기":
        delete_caches(json.load(open(a[1], encoding="utf-8")), a[2])
        return 0
    if len(a) < 2:
        print(__doc__)
        return 2
    video, script = a[0], a[1]
    proj = a[a.index("--고치기") + 1] if "--고치기" in a else (a[a.index("--프로젝트") + 1] if "--프로젝트" in a else None)
    items = detect(video, script, proj)
    lines = [f"{int(f['t'] // 60)}:{int(f['t'] % 60):02d} [{f['dd']}] 대본: {f['sentence']} | 들림: {f['heard']}" for f in items]
    msg = "\n".join(lines) if lines else "겹침·빨라진 곳 없음 (늘어짐·어색함도 없음)"
    if UTMOS_REPORT:
        v_ = sorted(x_[1] for x_ in UTMOS_REPORT)
        msg += f"\n(UTMOS 자연스러움: 문장 {len(v_)}개 · 중간 {v_[len(v_) // 2]:.2f}점 · 가장 낮음 {v_[0]:.2f}점)"
    print(msg)
    if "--결과" in a:
        open(a[a.index("--결과") + 1], "w", encoding="utf-8").write(msg + "\n")
    if items and "--고치기" in a:
        tmp = os.path.join(tempfile.gettempdir(), "겹침목록.json")
        json.dump(items, open(tmp, "w", encoding="utf-8"), ensure_ascii=False)
        py = os.path.join(HERE, ".supertonic_venv", "Scripts" if os.name == "nt" else "bin", "python.exe" if os.name == "nt" else "python")
        subprocess.run([py, "-X", "utf8", os.path.abspath(__file__), "--지우기", tmp, a[a.index("--고치기") + 1]], check=True)
        print("→ render_project.py 를 다시 돌리면 이 문장들만 새로 녹음됩니다")
    return 1 if items else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
