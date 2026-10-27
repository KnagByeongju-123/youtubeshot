"""나레이션 겹침 검사 — 성우가 같은 소리를 두 번 읽은 곳('닿을 것만만', '미역국국')을 찾아 그 문장을 다시 녹음하게 함 (.sd_venv 에서 실행)
python 나레이션_겹침검사.py <영상.mp4> <회차.py 또는 대본.txt> [--고치기 <프로젝트.json>] [--결과 <결과.txt>]
  - Whisper 는 '것만만'을 '것만'으로 고쳐 적어서 못 찾음 → 소리를 글자 그대로 적는 wav2vec2(CTC) 한국어 모델로 받아 적음
    (kresnik/wav2vec2-large-xlsr-korean, 처음 한 번 약 1.2GB 받음. 검사에만 쓰고 영상에는 안 들어감)
  - 찾는 규칙
    1) 소리를 쉼에서 15초 안쪽 조각으로 나눠 받아 적음
    2) 같은 글자 1~3자가 연달아 두 번 나오면(띄어쓰기 무시: '것만 만', '국국') 후보
    3) 받아 적은 조각과 가장 비슷한 대본 문장을 찾아, 그 문장에 원래 같은 길이의 반복(무럭무럭·불쑥불쑥·타닥타닥)이 있으면 흉내말로 보고 넘김
       반복된 글자가 대본 어딘가에 그대로 있으면('단단히'·'쓸쓸해') 문장을 잘못 맞춘 오탐으로 보고 넘김
    4) 대본 문장과 한 글자씩 맞춰 봐서 반복 자리에 글자가 '더 들어갔을' 때만 겹침 ('것만→것만만'). 글자 수가 같으면 발음 차이로 봄
       ('하늘나라→하늘라라', '닿을→다을')
  - 갑자기 빨라진 곳도 찾음: 쉼과 쉼 사이 한 마디씩 1초당 글자 수를 재서 영상 전체 마디의 중간값보다 25% 넘게 빠른 마디 (대사는 인물마다 빠르기가 달라 뺌)
  - --고치기 <프로젝트.json> : 겹친 문장(과 그 문단)의 녹음 캐시를 output/tts_cache 에서 지움 → render_project 를 다시 돌리면 그 문장만 새로 녹음.
    빨라진 문장은 알리기만 하고 고치지 않음(사용자 결정: 늘린 녹음이 너무 느려 어색함). --빠름고치기 를 붙이면 보통 빠르기로 늘림
    (Supertonic 은 매번 조금씩 다르게 읽어서 보통 한 번에 고쳐짐. 다시 만든 영상도 검사해서 '겹침 없음'이 나올 때까지, 최대 3번)
  - 결과: '분:초 [겹친 글자] 대본: <문장> | 들림: <받아 적은 글>'
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


def cho(c):
    """한글 글자의 첫소리(초성) 번호"""
    return (ord(c) - 0xAC00) // 588 if "가" <= c <= "힣" else -1


TENSE = {1: 0, 4: 3, 8: 7, 10: 9, 13: 12}          # 된소리 첫소리 → 예사소리 (ㄲ→ㄱ, ㄸ→ㄷ, ㅃ→ㅂ, ㅆ→ㅅ, ㅉ→ㅈ)


def cho_like(a, b):
    """두 글자의 첫소리가 같거나 된소리·예사소리 짝인가 ('들'과 '때')"""
    x, y = cho(a), cho(b)
    return x >= 0 and TENSE.get(x, x) == TENSE.get(y, y)


def word_end_stutters(h, sents, k_):
    """뒷말 더듬 (사용자 지적 2026-10-27 '처음 생길 때'를 '생길 때때로'): 낱말과 낱말 사이에 대본에 없는 글자 1~2개가 끼었고,
    그 글자가 앞 낱말의 끝 글자와 같거나('때 때'), 첫소리가 앞 낱말 끝 글자·뒤 낱말 첫 글자와 같은 짝('생길 들 때')이면 더듬으로 봄.
    반환: [(앞 끝 글자+끼어든 글자+뒤 첫 글자, 문장)]"""
    ctx = sents[max(0, k_ - 1):k_ + 2]
    ref, starts, mixed = "", set(), set()
    for _, s in ctx:
        for w in s.split():
            hw = hangul(w)
            if re.search(r"[0-9A-Za-z]", w):
                mixed.update(range(len(ref), len(ref) + len(hw) + 1))
            if hw:
                starts.add(len(ref))
                ref += hw
    out = []
    sm = difflib.SequenceMatcher(None, ref, h, autojunk=False)
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op != "insert" or not 1 <= j2 - j1 <= 2 or i1 not in starts or i1 in mixed or not 0 < i1 < len(ref):
            continue
        prev, nxt, ins = ref[i1 - 1], ref[i1], h[j1:j2]
        if ins[0] == prev or any(cho_like(c, prev) or cho_like(c, nxt) for c in ins):
            s_ = next((s for p, s in ctx if hangul(ref[max(0, i1 - 3):i1 + 2]) in hangul(s)), sents[k_][1])
            out.append((prev + ins + nxt, s_))
    return out


def word_start_stutters(h, sents, k_):
    """단어 첫머리 더듬 (사용자 지적 2026-10-26 '단어 시작 때 더듬음'): 같은 글자 반복('게다다가')이 아니라
    첫소리만 내다 다시 시작해 '브바닷속'·'그게다가'처럼 들리는 곳 — 대본에 없는 글자 하나가 낱말 바로 앞에 끼었고
    그 글자의 첫소리가 다음 글자(낱말 첫 글자)의 첫소리와 같으면 더듬으로 봄. 반환: [(끼어든 글자+낱말 첫 글자, 문장)]"""
    ctx = sents[max(0, k_ - 1):k_ + 2]
    ref, starts, mixed = "", set(), set()
    for _, s in ctx:
        for w in s.split():
            hw = hangul(w)
            if re.search(r"[0-9A-Za-z]", w):          # 숫자·영어가 섞인 낱말('2억'·'AI의')은 소리로 읽혀 글자가 달라짐 → 오탐이라 뺌
                mixed.update(range(len(ref), len(ref) + len(hw) + 1))
            if hw:
                starts.add(len(ref))
                ref += hw
    out = []
    sm = difflib.SequenceMatcher(None, ref, h, autojunk=False)
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == "insert" and j2 - j1 == 1 and i1 in starts and i1 not in mixed and i1 < len(ref) and j2 < len(h):
            c, nxt = h[j1], h[j2]
            if c != nxt and cho(c) == cho(nxt) and nxt == ref[i1]:
                s_ = next((s for p, s in ctx if hangul(ref[i1:i1 + 4]) in hangul(s)), sents[k_][1])
                out.append((c + nxt, s_))
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


def best_sentence_part(h, sents):
    """긴 문장이 쉼에서 잘려 조각에 반쪽만 들어온 경우 — 조각 글자가 문장에 얼마나 들어 있나로 맞춤 (2026-10-27 '처음 생길 될 때'를 놓쳤음)"""
    best, score = None, 0.0
    for par, s in sents:
        sh = hangul(s)
        if len(sh) < 8 or len(h) < 8:
            continue
        sm = difflib.SequenceMatcher(None, sh, h, autojunk=False)
        hit = sum(b.size for b in sm.get_matching_blocks()) / len(h)
        if hit > score:
            best, score = (par, s), hit
    return best if score >= 0.7 else None


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


def detect(video, script):
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
    found, sylls = [], []          # sylls: (글자, 시각초) - 말 빠르기 재기용
    blank = p.tokenizer.pad_token_id
    all_text = hangul(" ".join(x[1] for x in sents))
    for t0, t1 in chunks(a):
        off = max(0, t0 - 0.15)
        x = a[int(off * SR):int((t1 + 0.15) * SR)]
        with torch.no_grad():
            ids = m(**p(x, sampling_rate=SR, return_tensors="pt")).logits.argmax(-1)
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
        for n in (1, 2, 3):
            for dd in sorted(doubles(h, n)):
                i = h.find(dd)
                ctx = h[max(0, i - 8):i + 2 * n + 8]                 # 반복 자리 앞뒤
                ps = best_sentence(ctx, sents) or best_sentence(h, sents) or best_sentence_part(h, sents)
                if ps is None:
                    continue
                sh = hangul(ps[1])
                k_ = sents.index(ps)
                near = hangul(" ".join(x[1] for x in sents[max(0, k_ - 1):k_ + 2]))   # 앞뒤 문장까지 (조각이 문장 경계에 걸침)
                if doubles(sh, n) or dd in near:      # 규칙 3: 대본에 원래 같은 반복(흉내말 '줄줄이·무럭무럭')이 있음
                    continue
                if dd in all_text:                    # 규칙 3-2: 대본 어딘가에 그대로 있는 낱말('단단히·쓸쓸해') — 문장을 잘못 맞춘 오탐
                    continue
                if not extra_syllables(sh, ctx, ctx.find(dd), len(dd)):   # 규칙 4: 대본보다 글자가 늘어난 자리여야 겹침
                    continue
                found.append({"t": t0, "dd": dd, "sentence": ps[1], "paragraph": ps[0], "heard": text})
        ps = best_sentence(h, sents) or best_sentence_part(h, sents)    # 규칙 5: 단어 첫머리 더듬 ('브바닷속')
        if ps is not None:
            k_ = sents.index(ps)
            for dd, s_ in word_start_stutters(h, sents, k_):
                par = next((p for p, s in sents if s == s_), ps[0])
                found.append({"t": t0, "dd": "첫머리 더듬 " + dd, "sentence": s_, "paragraph": par, "heard": text})
            for dd, s_ in word_end_stutters(h, sents, k_):     # 규칙 6: 뒷말 더듬 ('생길 때 때', '생길 들 때')
                par = next((p for p, s in sents if s == s_), ps[0])
                found.append({"t": t0, "dd": "뒷말 더듬 " + dd, "sentence": s_, "paragraph": par, "heard": text})
    try:
        json.dump(sylls, open(os.path.join(tempfile.gettempdir(), "겹침_글자시각.json"), "w", encoding="utf-8"), ensure_ascii=False)
    except OSError:
        pass
    found += fast_spots(sylls, sents)
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
    fast = [it for it in items if it.get("speed")]
    items = [it for it in items if not it.get("speed")]
    if fast:
        slow_down(m, fast, st, cache, pitch, steps)
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
    lines = [f"{int(f['t'] // 60)}:{int(f['t'] % 60):02d} [{f['dd']}] 대본: {f['sentence']} | 들림: {f['heard']}" for f in items]
    msg = "\n".join(lines) if lines else "겹침·빨라진 곳 없음"
    print(msg)
    if "--결과" in a:
        open(a[a.index("--결과") + 1], "w", encoding="utf-8").write(msg + "\n")
    # 규칙(사용자 결정 2026-10-25): 빨라진 곳은 알리기만 하고 고치지 않음 (늘린 녹음이 너무 느려 어색했음). --빠름고치기 면 예전처럼 늘림
    fix = items if "--빠름고치기" in a else [it for it in items if not it.get("speed")]
    if fix and "--고치기" in a:
        tmp = os.path.join(tempfile.gettempdir(), "겹침목록.json")
        json.dump(fix, open(tmp, "w", encoding="utf-8"), ensure_ascii=False)
        py = os.path.join(HERE, ".supertonic_venv", "Scripts" if os.name == "nt" else "bin", "python.exe" if os.name == "nt" else "python")
        subprocess.run([py, "-X", "utf8", os.path.abspath(__file__), "--지우기", tmp, a[a.index("--고치기") + 1]], check=True)
        print("→ render_project.py 를 다시 돌리면 이 문장들만 새로 녹음됩니다")
    return 1 if fix else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
