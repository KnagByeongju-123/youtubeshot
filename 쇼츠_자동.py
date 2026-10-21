r"""쇼츠 자동 만들기 - 규칙: 롱폼(장문) 영상이 완성되면 같은 대본에서 가장 놀라운 장면으로 40~50초 세로 쇼츠 대본을 쓰고 쇼츠 영상까지 자동으로 만듦

  흐름 (render_project.py / make_longdoc.py 가 롱폼 완성 직후 호출)
   1) 롱폼 대본(사진 줄 제외)을 AI에게 주고 → 40~50초 세로 쇼츠 대본 (존댓말, 첫 3초 후크, 마지막 줄 "전체 이야기는 채널의 긴 영상에서")
   2) 실화\쇼츠\<제목>.json 으로 저장 (화면 세로, 남자 성우 2, 배경음 0.03, 나레이션 검증 켬)
   3) render_project.py <쇼츠.json> --사진 8 --kit --suffix 쇼츠   (롱폼 스타일(--소재프로필)은 안 씀)
      → output\장문\<쇼츠 제목>_쇼츠.mp4 (+ 썸네일·설명란)
  끄기: render_project.py 에 --쇼츠없음 을 붙이면 쇼츠를 만들지 않음
  따로 만들기: py -3.11 -X utf8 쇼츠_자동.py "output\장문\<제목>_프로젝트.json"
"""
import json
import os
import re
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
SHORTS_DIR = os.path.join(HERE, "실화", "쇼츠")
SHORTS_CATEGORY = "과학 사실"
SHORTS_SYSTEM = """너는 구독자 100만 유튜브 쇼츠 채널의 작가다. 아래 롱폼 다큐 대본에서 '가장 놀라운 장면 하나'를 골라 40~50초짜리 세로 쇼츠 나레이션을 쓴다.
- 길이: 읽는 시간 40~50초 (한글 180~230자). 짧은 문단 5~8개, 문단 사이 빈 줄.
- 첫 문장(3초 안)은 가장 충격적인 숫자·사실·질문으로 바로 시작. 인사말·배경 설명 금지.
- 롱폼 대본에 실제로 있는 사실·숫자만 쓴다. 지어내지 않는다. 가설은 가설로('~라고 봅니다', '아직 검증 중').
- 끝맺음은 모두 존댓말('~습니다', '~죠', '~일까요?'). 반말 끝맺음('~다.') 금지.
- 마지막 문단은 정확히 이 한 줄: 전체 이야기는 채널의 긴 영상에서 확인하세요.
- title: 쇼츠 제목 12~20자, 궁금증 유발, 낚시 금지.
- genre: 아래 [소재 목록] 중 내용에 가장 맞는 것 하나 (이름 그대로).
반드시 JSON만 출력: {"title": "...", "genre": "...", "story": "나레이션 전체"}"""


def _log(log, x):
    (log or print)(x)


def write_shorts_script(m, model, title, story, notes, log=None):
    """롱폼 대본 → 쇼츠 대본 dict {title, genre, story}. 규칙에 안 맞으면 한 번 다시 요청"""
    body = re.sub(r"\[사진:[^\]]*\]\n*", "", story or "").strip()
    genres = list(m.cat_info(SHORTS_CATEGORY)[1].keys())
    user = (f"[롱폼 제목] {title}\n\n[롱폼 대본]\n{body[:6000]}\n\n[사실 확인 메모]\n{notes or '(없음)'}\n\n[소재 목록]\n" + "\n".join(genres))
    last = None
    for attempt in range(2):
        d = m.ask_script_json(model, SHORTS_SYSTEM, user if attempt == 0 else user + "\n\n[다시] 길이 180~230자, 존댓말, 마지막 줄 규칙을 꼭 지켜서 다시 써줘.")
        st = str(d.get("story") or "").strip().replace("\r\n", "\n")
        st = re.sub(r"\n{3,}", "\n\n", st)
        n = len(re.findall(r"[가-힣]", st))
        plain = [ln for ln in st.split("\n") if ln.strip() and m._plain_sentences(ln)]
        ok = 140 <= n <= 300 and "전체 이야기는 채널의 긴 영상에서" in st and not plain
        last = {"title": str(d.get("title") or title)[:40].strip(), "genre": d.get("genre") if d.get("genre") in genres else genres[0], "story": st}
        _log(log, f"  ✂ 쇼츠 대본 {n}자 · 문단 {st.count(chr(10) + chr(10)) + 1}개" + ("" if ok else f" → 규칙 미달({'반말 ' + str(len(plain)) + '문단' if plain else '길이·마지막 줄'}), " + ("다시 씀" if attempt == 0 else "그대로 진행")))
        if ok:
            break
    if "전체 이야기는 채널의 긴 영상에서" not in last["story"]:
        last["story"] = last["story"].rstrip() + "\n\n전체 이야기는 채널의 긴 영상에서 확인하세요."
    return last


def make_shorts(m, model, long_proj, log=None):
    """롱폼 프로젝트 파일(output\\장문\\<제목>_프로젝트.json) → 쇼츠 대본 저장 + 쇼츠 영상 만들기. 반환: 쇼츠 프로젝트 경로 또는 ''"""
    c = json.load(open(long_proj, encoding="utf-8"))
    title, story = str(c.get("title") or "").strip(), str(c.get("story") or "")
    if not (title and story.strip()):
        return ""
    _log(log, "✂ 쇼츠 자동 만들기: 롱폼 대본에서 가장 놀라운 장면으로 40~50초 세로 쇼츠 대본 쓰는 중...")
    sd = write_shorts_script(m, model, title, story, c.get("notes", ""), log)
    d = dict(c)
    d.update(category=SHORTS_CATEGORY, genre=sd["genre"], topic=title, title=sd["title"], story=sd["story"],
             para_audio={}, img_prompts=[], gem_prompts=[], cast=[], gem_samples=[], sub_trans=None,
             reference="", research=False, autophoto=True, img_source="근거 사진(웹)", length="0")
    s = dict(c.get("settings") or {})
    s.update(format="쇼츠 세로(1080×1920)", narr_voice=m.DEFAULT_VOICE, bgm_volume=0.03, narr_check="on", narr_file="", bg_image="",
             thumb_style="자동(분위기에 맞춰)", target_sec="0", sub_trans=None)
    for k in m.SECRET_KEYS:
        s[k] = ""
    d["settings"] = s
    os.makedirs(SHORTS_DIR, exist_ok=True)
    out = os.path.join(SHORTS_DIR, m.safe_name(title) + ".json")
    m.atomic_write_text(out, json.dumps(d, ensure_ascii=False, indent=1))
    _log(log, f"  ✂ 쇼츠 대본 저장: 실화\\쇼츠\\{os.path.basename(out)} (제목: {sd['title']})")
    cmd = [sys.executable, "-X", "utf8", os.path.join(HERE, "render_project.py"), out, "--사진", "5", "--kit", "--suffix", "쇼츠", "--쇼츠없음"]
    _log(log, "  ✂ 쇼츠 영상 만드는 중 (세로 1080×1920, 사진 5초마다)...")
    t0 = time.time()
    p = subprocess.run(cmd, cwd=HERE)
    if p.returncode == 0:
        _log(log, f"✂ 쇼츠 완성 ({(time.time() - t0) / 60:.0f}분) → output\\장문\\{m.safe_name(sd['title'])}_쇼츠.mp4")
    else:
        _log(log, f"⚠ 쇼츠 영상 만들기 실패 (코드 {p.returncode}). 다시: py -3.11 -X utf8 쇼츠_자동.py \"{long_proj}\"")
    return out


def _load_main():
    import importlib.util
    spec = importlib.util.spec_from_file_location("snm", os.path.join(HERE, "shorts_novel_maker_supertonic.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


if __name__ == "__main__":
    if len(sys.argv) < 2 or not sys.argv[1].lower().endswith(".json"):
        print(__doc__)
        sys.exit(2)
    os.chdir(HERE)
    m = _load_main()
    app = m.App()
    app.withdraw()
    try:
        model = app.model_var.get().strip()
        m.SCRIPT_ENGINE["s"] = app.get_settings()
        r = make_shorts(m, model, os.path.abspath(sys.argv[1]))
    finally:
        try:
            app.destroy()
        except Exception:
            pass
    sys.exit(0 if r else 1)
