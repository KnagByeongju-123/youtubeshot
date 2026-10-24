r"""영어 번역 키트 - 규칙: 영상은 그대로 두고 유튜브 '번역' 기능으로 덧붙일 영어 제목·설명란·자막(SRT)을 만듦
  (원래 언어는 한국어 그대로 → 국내 조회수는 그대로, 영어권 시청자에게는 영어 제목·설명·자막이 보이고 조회수는 한 영상으로 합쳐짐)

  py -3.11 -X utf8 영어_번역.py "output\장문\0012_<제목>" [영어,일본어,한국어]   (콘텐츠 폴더 또는 <제목>_프로젝트.json, 언어를 안 쓰면 영어)
  render_project.py 에 --영어 (= 영어) 또는 --자막언어 영어,일본어 를 붙이면 영상 완성 뒤 자동으로

  결과 (영상과 같은 폴더)
   - <제목>_영어_제목설명.txt : 영어 제목(100자 이내) + 영어 설명란(5,000바이트 이내, 챕터 시간은 한국어판과 같음)
   - <제목>_영어자막.srt      : 영어 자막. 시간은 완성된 영상 소리를 Whisper 로 받아 적어 맞춤, 글은 원래 대본을 보고 번역
   - 일본어도 같은 모양(<제목>_일본어_제목설명.txt, <제목>_일본어자막.srt), 한국어는 <제목>_한국어자막.srt 만 (대본 그대로의 정확한 자막)
  올리는 법: 유튜브 스튜디오 → 영상 → 자막 → 언어 추가 '영어' → 제목·설명 '추가'(붙여넣기), 자막 '추가' → 파일 업로드(.srt)
"""
import glob
import json
import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
FFMPEG_GLOB = os.path.join(os.path.dirname(sys.executable), "Lib", "site-packages", "imageio_ffmpeg", "binaries", "ffmpeg*.exe")
SUB_MAX_SEC, SUB_MIN_SEC = 6.5, 1.2       # 자막 한 줄이 화면에 머무는 시간 (너무 길면 나눔)

LANGS = {   # 코드: (파일 이름에 붙일 말, 번역 지시에 쓸 언어 설명)
    "en": ("영어", "natural American English. Romanize Korean names with Revised Romanization, the same spelling every time (e.g. 한별 → Hanbyeol, 서린 → Seorin, 강무진 → Kang Mu-jin)"),
    "ja": ("일본어", "natural Japanese (です/ます for narration, natural spoken Japanese for dialogue). Write Korean names in katakana from the Korean pronunciation, the same every time (e.g. 한별 → ハンビョル, 서린 → ソリン)"),
    "ko": ("한국어", "Korean. Do not translate: rewrite each chunk in correct Korean using the ORIGINAL script wording (fix speech-recognition mishearings and spacing only)"),
}

META_SYSTEM = """You are the {lang_name} editor of a Korean YouTube channel (documentaries and fictional story series). Translate the Korean title and description into {lang} for YouTube's 'translations' feature (the video itself stays Korean; these viewers will see the translated title, description and subtitles).
- title: max 100 characters, natural and curious, same meaning as the Korean title, no clickbait, no ALL CAPS, no emojis.
- description: keep the same structure as the Korean one (short hook, summary, chapter list, sources, notes/disclaimers, hashtags). Chapter lines must keep EXACTLY the same timestamps (e.g. 00:00, 01:23) with translated chapter names. Keep every URL exactly. Keep disclaimers (AI voice / AI illustration not a real photo / not medical advice / research is preliminary) translated faithfully. Add one line saying subtitles in this language are available (CC) and the original narration is Korean.
- Facts, numbers, names and hedges must match the Korean text exactly; do not add facts. Use the real published names of papers/journals/places.
- The whole description must stay under 4,800 bytes (UTF-8).
Output JSON only: {{"title": "...", "description": "..."}}"""

SUB_SYSTEM = """You turn Korean narration subtitles into concise subtitles in {lang}.
You get numbered subtitle chunks (from speech recognition, may contain mishearings) and the ORIGINAL Korean script. Use the script to fix mishearings, then write each chunk.
- Return exactly one line for every number, same order, same count. Do not merge or split.
- Each line is what is being said in that chunk only (a sentence may continue in the next chunk — that's fine).
- Keep it short and readable (max ~90 characters, Japanese max ~45 characters). Facts, numbers, names must match the script.
- If the script is a fictional story: keep the tone, translate dialogue as natural speech, keep each character's name spelled the same in every line.
Output JSON only: {{"items": [{{"i": 1, "t": "..."}}, ...]}}"""


def _load_main():
    import importlib.util
    spec = importlib.util.spec_from_file_location("snm", os.path.join(HERE, "shorts_novel_maker_supertonic.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _find(target):
    """콘텐츠 폴더 또는 프로젝트 파일 → (프로젝트.json, 영상.mp4, base 경로). 쇼츠는 건너뜀"""
    if os.path.isdir(target):
        projs = [p for p in glob.glob(os.path.join(target, "*_프로젝트.json")) if "_쇼츠_" not in os.path.basename(p)]
        if not projs:
            raise SystemExit("프로젝트 파일(_프로젝트.json)을 못 찾았어요: " + target)
        proj = projs[0]
    else:
        proj = target
    base = proj[: -len("_프로젝트.json")]
    mp4 = base + ".mp4"
    if not os.path.exists(mp4):
        raise SystemExit("영상(.mp4)을 못 찾았어요: " + mp4)
    return proj, mp4, base


def _read(p):
    try:
        return open(p, encoding="utf-8").read()
    except OSError:
        return ""


def _srt_time(t):
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def transcribe_chunks(mp4, log=print):
    """영상 소리 → Whisper 로 받아 적어 자막 조각 [(시작, 끝, 한국어)] (조각은 6.5초 이내, 문장 끝에서 나눔)"""
    nv = _load_reading("나레이션_검증")
    w = nv.whisper()
    if w is None:
        raise SystemExit("Whisper 를 불러오지 못했어요: " + str(nv._W.get("error")))
    ff = (glob.glob(FFMPEG_GLOB) or ["ffmpeg"])[0]
    with tempfile.TemporaryDirectory() as td:
        wav = os.path.join(td, "a.wav")
        subprocess.run([ff, "-y", "-loglevel", "error", "-i", mp4, "-ac", "1", "-ar", "16000", wav], check=True)
        log("  🎧 영상 소리를 받아 적는 중 (자막 시간 맞추기, 10분 영상이면 5~10분)...")
        segs, _ = w.transcribe(wav, language="ko", word_timestamps=True, vad_filter=True, beam_size=1)
        words = [(x.start, x.end, x.word) for sg in segs for x in (sg.words or [])]
    chunks, cur = [], []
    for wd in words:
        cur.append(wd)
        dur = cur[-1][1] - cur[0][0]
        end_sent = re.search(r"[.?!。…]$|(니다|요|죠|까요)$", wd[2].strip())
        if (dur >= 3.0 and end_sent) or dur >= SUB_MAX_SEC:
            chunks.append(cur)
            cur = []
    if cur:
        chunks.append(cur)
    out = []
    for c in chunks:
        a, b = c[0][0], max(c[-1][1], c[0][0] + SUB_MIN_SEC)
        out.append([a, b, "".join(x[2] for x in c).strip()])
    for i in range(len(out) - 1):                    # 다음 자막과 겹치지 않게
        out[i][1] = min(out[i][1], out[i + 1][0] - 0.02)
    return [tuple(x) for x in out if x[2]]


def _load_reading(name):
    import importlib.util
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, name + ".py"))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def translate_subs(m, chunks, script, log=print, lang="en"):
    """자막 조각을 원래 대본을 보며 그 언어로 (60조각씩 나눠서, 개수가 안 맞으면 한 번 더)"""
    en = []
    system = SUB_SYSTEM.format(lang=LANGS[lang][1])
    body = re.sub(r"\[사진:[^\]]*\]\n*", "", script)
    for k in range(0, len(chunks), 60):
        part = chunks[k:k + 60]
        user = ("[ORIGINAL KOREAN SCRIPT]\n" + body[:9000] + "\n\n[CHUNKS]\n" +
                "\n".join(f"{i + 1}. {c[2]}" for i, c in enumerate(part)))
        got = None
        for _ in range(2):
            d = m.ask_json("", system, user)
            items = {int(x.get("i", 0)): str(x.get("t") or x.get("en") or "").strip() for x in (d.get("items") or []) if isinstance(x, dict)}
            if all(items.get(i + 1) for i in range(len(part))):
                got = [items[i + 1] for i in range(len(part))]
                break
            user += "\n\n[AGAIN] Return exactly one line for EVERY number."
        if got is None:
            raise SystemExit("자막 번역 개수가 맞지 않아 멈췄어요. 다시 실행해 주세요.")
        en += got
        log(f"  🌐 {LANGS[lang][0]} 자막 {min(len(chunks), k + 60)}/{len(chunks)}")
    return en


def make_meta(m, title, desc_ko, notes, log=print, lang="en"):
    d = m.ask_json("", META_SYSTEM.format(lang=LANGS[lang][1], lang_name=LANGS[lang][0]), f"[KOREAN TITLE]\n{title}\n\n[KOREAN DESCRIPTION]\n{desc_ko}\n\n[FACT-CHECK NOTES]\n{notes or '(none)'}")
    t, ds = str(d.get("title") or "").strip()[:100], str(d.get("description") or "").strip()
    ds = ds.replace("<", "(").replace(">", ")")                     # 유튜브 설명란은 < > 를 못 씀
    while len(ds.encode("utf-8")) > 4900 and "\n" in ds:            # 5,000바이트 규칙: 넘치면 해시태그·끝줄부터 줄임
        ds = ds.rsplit("\n", 1)[0].rstrip()
    return t, ds


def make_translations(target, langs=("en",), log=print):
    """완성된 영상의 언어별 자막(SRT)과 제목·설명란 번역. 소리 받아 적기는 한 번만, 언어마다 번역만 따로.
    langs: "en"(영어)·"ja"(일본어)·"ko"(한국어 자막, 제목 번역 없음)"""
    proj, mp4, base = _find(target)
    c = json.load(open(proj, encoding="utf-8"))
    m = _load_main()
    title = str(c.get("title") or "").strip()
    langs = [x for x in langs if x in LANGS]
    log(f"🌐 자막·번역 키트 ({', '.join(LANGS[x][0] for x in langs)}): {title}")
    desc_ko = _read(base + "_설명란.txt")
    chunks = transcribe_chunks(mp4, log)
    for lang in langs:
        name = LANGS[lang][0]
        if lang != "ko":
            t_, d_ = make_meta(m, title, desc_ko, c.get("notes", ""), log, lang)
            m.atomic_write_text(base + f"_{name}_제목설명.txt",
                                f"[{name} 제목]\n{t_}\n\n[{name} 설명란]  ({len(d_.encode('utf-8')):,}바이트 / 5,000)\n{d_}\n")
            log(f"  🌐 {name} 제목: {t_}")
        lines = translate_subs(m, chunks, str(c.get("story") or ""), log, lang)
        srt = "\n".join(f"{i + 1}\n{_srt_time(a)} --> {_srt_time(b)}\n{e}\n" for i, ((a, b, _), e) in enumerate(zip(chunks, lines)))
        m.atomic_write_text(base + f"_{name}자막.srt", srt)
        log(f"✅ {name} 자막 완성: {os.path.basename(base)}_{name}자막.srt (자막 {len(lines)}줄)")
    return base


def make_english(target, log=print):
    return make_translations(target, ("en",), log)


LANG_KO = {"영어": "en", "일본어": "ja", "한국어": "ko", "en": "en", "ja": "ja", "ko": "ko"}


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    os.chdir(HERE)
    langs = [LANG_KO[x] for x in (sys.argv[2].split(",") if len(sys.argv) > 2 else ["영어"]) if x in LANG_KO]
    make_translations(os.path.abspath(sys.argv[1]), langs)
