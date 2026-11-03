"""나레이션 겹침 검사 — 성우가 같은 소리를 두 번 읽은 곳('닿을 것만만', '미역국국')을 찾아 그 문장을 다시 녹음하게 함 (.sd_venv 에서 실행)
python 나레이션_겹침검사.py <영상.mp4> <회차.py 또는 대본.txt> [--고치기 <프로젝트.json>] [--결과 <결과.txt>]
  - Whisper 는 '것만만'을 '것만'으로 고쳐 적어서 못 찾음 → 소리를 글자 그대로 적는 wav2vec2(CTC) 한국어 모델로 받아 적음
    (kresnik/wav2vec2-large-xlsr-korean, 처음 한 번 약 1.2GB 받음. 검사에만 쓰고 영상에는 안 들어감)
  - 찾는 규칙
    1) 소리를 쉼에서 15초 안쪽 조각으로 나눠 받아 적음
    2) 같은 글자 1~3자가 연달아 두 번 나오면(띄어쓰기 무시: '것만 만', '국국') 후보
    3) 받아 적은 조각과 가장 비슷한 대본 문장을 찾아, 그 문장에 원래 같은 길이의 반복(무럭무럭·불쑥불쑥·타닥타닥)이 있으면 흉내말로 보고 넘김
    5) 글자 하나가 끼어든 말더듬('유적→유저적'): 대본 문장 안쪽에 끼어든 한 글자가 바로 앞·뒤 글자와 같은 소리(받침만 다름 포함)면 겹침 (2026-11-01)
    4) 대본 문장과 한 글자씩 맞춰 봐서 반복 자리에 글자가 '더 들어갔을' 때만 겹침 ('것만→것만만'). 글자 수가 같으면 발음 차이로 봄
       ('하늘나라→하늘라라', '닿을→다을')
  - (--빠르기 를 붙일 때만, 기본은 겹침만 — 사용자 결정 2026-10-31) 갑자기 빨라진 곳도 찾음: 쉼과 쉼 사이 한 마디씩 1초당 글자 수를 재서 영상 전체 마디의 중간값보다 25% 넘게 빠른 마디 (대사는 인물마다 빠르기가 달라 뺌)
  - --고치기 <프로젝트.json> : 겹친 문장(과 그 문단)의 녹음 캐시를 output/tts_cache 에서 지움 → render_project 를 다시 돌리면 그 문장만 새로 녹음.
    빨라진 문장도 다시 녹음만 함 (늘리면 소리가 늘어져 들려서 속도는 조절하지 않음, 사용자 결정 2026-10-31)
    (Supertonic 은 매번 조금씩 다르게 읽어서 보통 한 번에 고쳐짐. 다시 만든 영상도 검사해서 '겹침 없음'이 나올 때까지, 최대 3번)
  - 빠진 말 검사(기본으로 함, 사용자 결정 2026-11-01: 성우 M1이 짧은 문장을 빼먹은 적이 있음): 받아 적은 글 전체를 대본 전체와 한 글자씩 맞춰 봐서
    대본 문장 글자의 45% 미만만 들린 문장(한글 6자 이상)을 '빠짐'으로 → --고치기 면 그 문장도 다시 녹음. 끄려면 --빠짐끔
  - 결과: '분:초 [겹친 글자 또는 빠짐] 대본: <문장> | 들림: <받아 적은 글>'
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
    elif path.endswith(".json"):                       # 프로젝트 파일이면 대본(story)만 (예전엔 JSON 글자 전체를 한 문단으로 읽어 맞춰 보기가 엉터리였음, 2026-11-01)
        text = json.load(open(path, encoding="utf-8")).get("story", "")
    else:
        text = open(path, encoding="utf-8").read()
    pars = [p.strip() for p in re.split(r"\n\s*\n", text)
            if p.strip() and not re.match(r"^(\{c\d+\}|\[사진:|#)", p.strip())]
    try:          # 숫자는 성우가 읽는 대로 한글로 ('10월 2일' → '시월 이 일') — 안 바꾸면 숫자 자리가 '끼어든 글자'로 잘못 걸림 (2026-11-01)
        spec_ = importlib.util.spec_from_file_location("ko_read", os.path.join(HERE, "한국어_읽기.py"))
        kr_ = importlib.util.module_from_spec(spec_)
        spec_.loader.exec_module(kr_)
        pars = [kr_.read_korean(p) for p in pars]
    except Exception:
        pass
    return pars


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
    quiet = rms < max(1e-4, np.percentile(rms, 95) * 0.03, np.percentile(rms, 15) * 1.3)   # 배경음이 깔려 완전한 쉼이 없어도(bgm_peak, 2026-11-01) 말 사이를 쉼으로
    out, start, k = [], 0, 0
    while k < n:
        if (k - start) * 0.02 >= 15:                        # 쉼을 못 찾아도 15초가 되면 가장 조용한 곳에서 끊음 (한 조각이 몇 분이 되면 메모리가 넘침)
            lo = start + int(10 / 0.02)
            cut = lo + int(np.argmin(rms[lo:k + 1]))
            out.append((start * 0.02, cut * 0.02))
            start = k = cut + 1
            continue
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


def _cv(ch):
    """한글 한 글자 → (초성, 중성). 아니면 None"""
    c = ord(ch) - 0xAC00 if ch else -1
    return (c // 588, (c % 588) // 28) if 0 <= c < 11172 else None


def stutter_inserts(ref, heard):
    """대본 문장 안쪽에 글자 하나가 끼어들었고, 그 글자가 바로 앞·뒤 대본 글자와 같은 소리(같은 글자 또는 받침만 다름)면 말더듬
    ('유적→유저적', '국→구국'). 사용자 결정 2026-11-01: 같은 글자가 바로 두 번 나오는 것만 찾던 검사가 '유저적'을 놓쳤음"""
    out = []
    sm = difflib.SequenceMatcher(None, ref, heard, autojunk=False)
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if not (0 < i1 < len(ref)):                          # 문장 바깥(앞뒤 다른 문장)에 붙은 글은 보지 않음
            continue
        if op == "insert" and j2 - j1 == 1:
            extra = heard[j1]
        elif op == "replace" and (j2 - j1) == (i2 - i1) + 1:
            extra = heard[j1]
        else:
            continue
        nb = [ref[k] for k in (i1 - 1, i1) if 0 <= k < len(ref)]
        if any(extra == c or (_cv(extra) and _cv(extra) == _cv(c)) for c in nb):
            out.append(heard[max(0, j1 - 2):j2 + 2])
    return out


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


def soft(t):
    """받침을 뗀 글자(초성+중성)로 — 받아쓰기가 받침을 자주 틀려서('줌→중', '모를→몰을') 빠진 말 검사는 받침 없이 맞춤"""
    return "".join(chr(0xAC00 + (ord(c) - 0xAC00) // 28 * 28) for c in hangul(t))


def missing_spots(heard_all, sents, ratio=0.45, min_len=6):
    """빠진 문장: 받아 적은 글 전체와 대본 전체를 한 글자씩(받침 빼고) 맞춰, 문장 글자 중 들린 비율이 ratio 미만인 문장"""
    ref, owner = "", []
    for k, (_, s_) in enumerate(sents):
        sh = soft(s_)
        ref += sh
        owner += [k] * len(sh)
    hyp, tpos = "", []
    for t0, text in heard_all:
        h = soft(text)
        hyp += h
        tpos += [t0] * len(h)
    if not ref or not hyp:
        return []
    hit = [0] * len(sents)
    first_t = [None] * len(sents)
    for b in difflib.SequenceMatcher(None, ref, hyp, autojunk=False).get_matching_blocks():
        for j in range(b.size):
            k = owner[b.a + j]
            hit[k] += 1
            if first_t[k] is None:
                first_t[k] = tpos[b.b + j]
    out, last_t = [], 0.0
    for k, (par, s_) in enumerate(sents):
        n = len(hangul(s_))
        if first_t[k] is not None:
            last_t = first_t[k]
        if n >= min_len and hit[k] / n < ratio:
            # 전체 맞춤이 어긋났을 수 있음 → 그 자리 앞뒤 조각(±3)에서 문장만 따로 맞춰 봐서 들렸으면 넘김
            ci = max([i for i, (t0, _) in enumerate(heard_all) if t0 <= last_t] or [0])
            near = "".join(soft(x) for _, x in heard_all[max(0, ci - 2):ci + 4])
            sh = soft(s_)
            loc = sum(b_.size for b_ in difflib.SequenceMatcher(None, sh, near, autojunk=False).get_matching_blocks())
            if loc / n >= ratio:
                continue
            out.append({"t": last_t, "dd": f"빠짐 {hit[k]}/{n}자 들림", "missing": True, "sentence": s_, "paragraph": par, "heard": ""})
    return out


def detect(video, script):
    import numpy as np
    import torch
    from transformers import AutoModelForCTC, AutoProcessor
    pars = script_paragraphs(script)
    sents = [(p, s) for p in pars for s in sentences(p)]
    all_h = hangul(" ".join(s for _, s in sents))      # 대본 전체(한글만) - 규칙 3-1
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", video, "-vn", "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    a = np.frombuffer(raw, np.float32)
    torch.set_num_threads(max(1, os.cpu_count() or 4))
    p = AutoProcessor.from_pretrained(MODEL)
    m = AutoModelForCTC.from_pretrained(MODEL).eval()
    found, sylls, heard_all = [], [], []          # sylls: (글자, 시각초) - 말 빠르기 재기용, heard_all: (시작초, 받아 적은 글)
    blank = p.tokenizer.pad_token_id
    for t0, t1 in chunks(a):
        off = max(0, t0 - 0.15)
        x = a[int(off * SR):int((t1 + 0.15) * SR)]
        with torch.no_grad():
            ids = m(**p(x, sampling_rate=SR, return_tensors="pt")).logits.argmax(-1)
        text = p.batch_decode(ids)[0]
        h = hangul(text)
        heard_all.append((t0, text))
        seq = ids[0].tolist()
        step = len(x) / SR / max(1, len(seq))       # 한 칸(약 0.02초)
        prev = None
        for k, tid in enumerate(seq):               # 글자가 처음 나온 칸 = 그 글자를 말한 시각
            if tid != prev and tid != blank:
                ch = p.tokenizer.convert_ids_to_tokens(tid)
                if re.fullmatch(r"[가-힣]", ch or ""):
                    sylls.append((ch, off + k * step))
            prev = tid
        for n in (1, 2, 3):
            for dd in sorted(doubles(h, n)):
                i = h.find(dd)
                ctx = h[max(0, i - 8):i + 2 * n + 8]                 # 반복 자리 앞뒤
                ps = best_sentence(ctx, sents) or best_sentence(h, sents)
                if ps is None:
                    continue
                sh = hangul(ps[1])
                k_ = sents.index(ps)
                near = hangul(" ".join(x[1] for x in sents[max(0, k_ - 1):k_ + 2]))   # 앞뒤 문장까지 (조각이 문장 경계에 걸침)
                if doubles(sh, n) or dd in near:      # 규칙 3: 대본에 원래 같은 반복(흉내말 '줄줄이·무럭무럭')이 있음
                    continue
                # 규칙 3-1 (2026-11-03, '고고학'을 엉뚱한 문장에 맞춰 겹침으로 봄): 반복 + 앞이나 뒤 글자 하나가
                # 대본 어딘가에 그대로 있으면 원래 낱말('고고학'·'다다음') → 넘김. 진짜 겹침('것만만')은 대본에 없음
                if any(w_ in all_h for w_ in (h[max(0, i - 1):i + 2 * n], h[i:i + 2 * n + 1]) if len(w_) > 2 * n):
                    continue
                if not extra_syllables(sh, ctx, ctx.find(dd), len(dd)):   # 규칙 4: 대본보다 글자가 늘어난 자리여야 겹침
                    continue
                found.append({"t": t0, "dd": dd, "sentence": ps[1], "paragraph": ps[0], "heard": text})
        for par_, s_ in sents:                                 # 글자 하나 끼어든 말더듬 ('유적→유저적')
            sh_ = hangul(s_)
            if len(sh_) < 6 or difflib.SequenceMatcher(None, sh_, h, autojunk=False).find_longest_match(0, len(sh_), 0, len(h)).size < 5:
                continue
            sm_ = difflib.SequenceMatcher(None, sh_, h, autojunk=False)
            if sum(b.size for b in sm_.get_matching_blocks()) / len(sh_) < 0.8:   # 이 조각에 그 문장이 거의 다 들어 있을 때만
                continue
            for ex in stutter_inserts(sh_, h):
                found.append({"t": t0, "dd": "끼어듦 " + ex, "sentence": s_, "paragraph": par_, "heard": text})
    try:
        json.dump(sylls, open(os.path.join(tempfile.gettempdir(), "겹침_글자시각.json"), "w", encoding="utf-8"), ensure_ascii=False)
        json.dump(heard_all, open(os.path.join(tempfile.gettempdir(), "받아쓰기_조각.json"), "w", encoding="utf-8"), ensure_ascii=False)
    except OSError:
        pass
    found += fast_spots(sylls, sents)
    found += missing_spots(heard_all, sents)
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
    # 빨라진 문장도 늘리지 않고 다시 녹음만 함 (사용자 결정 2026-10-31: 늘린 소리는 늘어져 들려서 나레이션 속도는 조절하지 않음. slow_down 은 쓰지 않음)
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


def slow_down(m, fast, st, cache, pitch, steps):
    """빨라진 문장: 다시 녹음해도 짧은 문장은 또 빨라서 → 그 문장 녹음을 보통 빠르기로 늘림 (ffmpeg atempo, 목소리 높이는 그대로).
    문단 녹음은 지워서 늘린 문장으로 다시 이어 붙게 함"""
    import numpy as np
    vname = st.get("narr_voice", "")
    vc, rate = m.voice_code(vname), float(st.get("narr_rate", 5) or 0)
    moods = ["차분"] if str(st.get("st_emotion", "")) == "차분" else MOODS
    key = lambda t, mood: os.path.join(cache, m.tts_key(vc, rate, pitch, m.supertonic_cache_text(t, mood, steps)) + ".npy")
    for it in fast:
        sent = m.tts_clean(m.spoken_src(it["sentence"]))
        f = next((key(sent, md) for md in moods if os.path.exists(key(sent, md))), None)
        if f is None:                                     # 캐시가 없으면 먼저 녹음
            m._tts_clip(sent, vname, rate, cache, pitch, moods[0], steps)
            f = next((key(sent, md) for md in moods if os.path.exists(key(sent, md))), None)
        if f is None:
            print("  늘릴 녹음을 못 찾음:", it["sentence"])
            continue
        tempo = max(0.7, min(1.0, 1.05 / float(it["speed"])))     # 보통보다 5% 빠른 정도까지
        a = np.load(f).astype(np.float32)
        r = subprocess.run(["ffmpeg", "-v", "error", "-f", "f32le", "-ar", str(m.SR), "-ac", "1", "-i", "-", "-af", f"atempo={tempo:.4f}",
                            "-f", "f32le", "-ar", str(m.SR), "-ac", "1", "-"], input=a.tobytes(), capture_output=True, check=True)
        np.save(f, np.frombuffer(r.stdout, np.float32))
        print(f"  늦춤 x{tempo:.2f}: {it['sentence']}")
        par = m.tts_clean(m.spoken_src(it["paragraph"]))
        if par != sent:
            for md in moods:
                if os.path.exists(key(par, md)):
                    os.remove(key(par, md))


def main(a):
    if a and a[0] == "--지우기":
        delete_caches(json.load(open(a[1], encoding="utf-8")), a[2])
        return 0
    if len(a) < 2:
        print(__doc__)
        return 2
    video, script = a[0], a[1]
    items = detect(video, script)
    if "--빠르기" not in a:     # 규칙(사용자 결정 2026-10-31): 겹침만 검사. 빨라진 곳은 --빠르기 를 붙일 때만
        items = [it for it in items if not it.get("speed")]
    if "--빠짐끔" in a:
        items = [it for it in items if not it.get("missing")]
    lines = [f"{int(f['t'] // 60)}:{int(f['t'] % 60):02d} [{f['dd']}] 대본: {f['sentence']} | 들림: {f['heard']}" for f in items]
    msg = "\n".join(lines) if lines else ("겹침·빠짐·빨라진 곳 없음" if "--빠르기" in a else "겹침·빠짐 없음")
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
