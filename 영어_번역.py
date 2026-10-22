r"""영어 번역 키트 - 규칙: 영상은 그대로 두고 유튜브 '번역' 기능으로 덧붙일 영어 제목·설명란·자막(SRT)을 만듦
  (원래 언어는 한국어 그대로 → 국내 조회수는 그대로, 영어권 시청자에게는 영어 제목·설명·자막이 보이고 조회수는 한 영상으로 합쳐짐)

  py -3.11 -X utf8 영어_번역.py "output\장문\0012_<제목>"          (콘텐츠 폴더 또는 <제목>_프로젝트.json)
  render_project.py 에 --영어 를 붙이면 영상 완성 뒤 자동으로

  결과 (영상과 같은 폴더)
   - <제목>_영어_제목설명.txt : 영어 제목(100자 이내) + 영어 설명란(5,000바이트 이내, 챕터 시간은 한국어판과 같음)
   - <제목>_영어자막.srt      : 영어 자막. 시간은 완성된 영상 소리를 Whisper 로 받아 적어 맞춤, 글은 원래 대본을 보고 번역
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

META_SYSTEM = """You are the English-language editor of a Korean YouTube documentary channel. Translate the Korean title and description into natural American English for YouTube's 'translations' feature (the video itself stays Korean; English viewers will see these and English subtitles).
- title: max 100 characters, natural and curious, same meaning as the Korean title, no clickbait, no ALL CAPS, no emojis.
- description: keep the same structure as the Korean one (short hook, summary, chapter list, sources, notes/disclaimers, hashtags). Chapter lines must keep EXACTLY the same timestamps (e.g. 00:00, 01:23) with translated chapter names. Keep every URL exactly. Keep disclaimers (AI voice / AI illustration not a real photo / not medical advice / research is preliminary) translated faithfully. Add one line: "English subtitles available (CC). Original narration in Korean."
- Facts, numbers, names and hedges must match the Korean text exactly; do not add facts. Use standard English spellings of names (e.g. Herculaneum, Vesuvius) and English titles of papers/journals as they really are.
- The whole description must stay under 4,800 bytes (UTF-8).
Output JSON only: {"title": "...", "description": "..."}"""

SUB_SYSTEM = """You translate Korean documentary subtitles into natural, concise American English subtitles.
You get numbered subtitle chunks (from speech recognition, may contain mishearings) and the ORIGINAL Korean script. Use the script to fix mishearings, then translate each chunk.
- Return exactly one English line for every number, same order, same count. Do not merge or split.
- Each line is what is being said in that chunk only (a sentence may continue in the next chunk — that's fine).
- Keep it short and readable (max ~90 characters). Facts, numbers, names must match the script. Standard English spellings of names.
Output JSON only: {"items": [{"i": 1, "en": "..."}, ...]}"""


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


def translate_subs(m, chunks, script, log=print):
    """자막 조각을 원래 대본을 보며 영어로 (60조각씩 나눠서, 개수가 안 맞으면 한 번 더)"""
    en = []
    body = re.sub(r"\[사진:[^\]]*\]\n*", "", script)
    for k in range(0, len(chunks), 60):
        part = chunks[k:k + 60]
        user = ("[ORIGINAL KOREAN SCRIPT]\n" + body[:9000] + "\n\n[CHUNKS]\n" +
                "\n".join(f"{i + 1}. {c[2]}" for i, c in enumerate(part)))
        got = None
        for _ in range(2):
            d = m.ask_json("", SUB_SYSTEM, user)
            items = {int(x.get("i", 0)): str(x.get("en") or "").strip() for x in (d.get("items") or []) if isinstance(x, dict)}
            if all(items.get(i + 1) for i in range(len(part))):
                got = [items[i + 1] for i in range(len(part))]
                break
            user += "\n\n[AGAIN] Return exactly one line for EVERY number."
        if got is None:
            raise SystemExit("자막 번역 개수가 맞지 않아 멈췄어요. 다시 실행해 주세요.")
        en += got
        log(f"  🌐 자막 번역 {min(len(chunks), k + 60)}/{len(chunks)}")
    return en


def make_meta(m, title, desc_ko, notes, log=print):
    d = m.ask_json("", META_SYSTEM, f"[KOREAN TITLE]\n{title}\n\n[KOREAN DESCRIPTION]\n{desc_ko}\n\n[FACT-CHECK NOTES]\n{notes or '(none)'}")
    t, ds = str(d.get("title") or "").strip()[:100], str(d.get("description") or "").strip()
    ds = ds.replace("<", "(").replace(">", ")")                     # 유튜브 설명란은 < > 를 못 씀
    while len(ds.encode("utf-8")) > 4900 and "\n" in ds:            # 5,000바이트 규칙: 넘치면 해시태그·끝줄부터 줄임
        ds = ds.rsplit("\n", 1)[0].rstrip()
    return t, ds


def make_english(target, log=print):
    proj, mp4, base = _find(target)
    c = json.load(open(proj, encoding="utf-8"))
    m = _load_main()
    title = str(c.get("title") or "").strip()
    log(f"🌐 영어 번역 키트: {title}")
    desc_ko = _read(base + "_설명란.txt")
    t_en, d_en = make_meta(m, title, desc_ko, c.get("notes", ""), log)
    meta = base + "_영어_제목설명.txt"
    m.atomic_write_text(meta, f"[영어 제목]\n{t_en}\n\n[영어 설명란]  ({len(d_en.encode('utf-8')):,}바이트 / 5,000)\n{d_en}\n")
    log(f"  🌐 영어 제목: {t_en}")
    chunks = transcribe_chunks(mp4, log)
    en = translate_subs(m, chunks, str(c.get("story") or ""), log)
    srt = "\n".join(f"{i + 1}\n{_srt_time(a)} --> {_srt_time(b)}\n{e}\n" for i, ((a, b, _), e) in enumerate(zip(chunks, en)))
    m.atomic_write_text(base + "_영어자막.srt", srt)
    log(f"✅ 영어 번역 키트 완성: {os.path.basename(meta)} · {os.path.basename(base)}_영어자막.srt (자막 {len(en)}줄)")
    return meta


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    os.chdir(HERE)
    make_english(os.path.abspath(sys.argv[1]))
