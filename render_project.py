"""프로젝트 파일(.json) 하나를 바로 MP4 로 (장문 연속 제작과 같은 순서: 나레이션 → 영상 → 썸네일·타임스탬프)

  py -3.11 -X utf8 render_project.py <프로젝트.json> [--kit] [--vi] [--소재프로필] [--사진 [초]]

  - --소재프로필 : 손으로 쓴 대본을 그 소재의 기본 스타일(다큐 자막·제목 위치·근거 사진·웹 조사)로 맞춤
  - --사진 [초] : 대본에 사진이 적으면 웹에서 근거 사진을 자동으로 찾아 넣음 (나레이션 '초'마다 한 장, 기본 8초 - 관련 사진을 최대한 많이).
                  넣은 뒤 프로젝트 파일에 저장 → 다시 실행하면 사진은 건너뜀
  - --suffix 이름 : 결과 파일 이름 끝에 _이름 (같은 제목으로 덧붙일 부분을 따로 만들 때. 화면 제목은 그대로)
  - --썸네일만 : 영상은 만들지 않고 썸네일 후보만 새로 (디자인 16가지 + 영상 장면 실사 편집). 지금 유튜브 썸네일은 그대로
  - --대본그대로 : 손으로 쓴 대본의 오프닝(30초 후크·'끝까지 보시면')과 챕터 끝 예고를 AI 가 고쳐 쓰지 않음 (에세이처럼 원문 분위기를 지킬 때. 존댓말 고치기는 그대로)
  - --길이고정 : 롱폼 길이 규칙(10~15분, 짧으면 내용을 더해 늘림)을 건너뜀
  - --영어 : 영상 완성 뒤 영어 제목·설명란·자막(SRT)도 만듦 (유튜브 '번역'으로 덧붙이는 용도, 영어_번역.py)
  - --자막언어 영어,일본어,한국어 : 고른 언어마다 자막(SRT)과 제목·설명란 번역 (--영어 는 '영어'만과 같음)
  - --쇼츠 : 롱폼 완성 뒤 40~50초 세로 쇼츠도 함께 만듦 (기본은 쇼츠를 안 만듦, 쇼츠_자동.py)
  - --성우프리셋 "이름" : 🎤 성우 선택 창에서 '⭐ 새 성우로 저장'한 목소리(성우·속도·톤·감정·쉼)로 (장문_설정.json "성우_프리셋" 도 같음)
  - --성우 M1 : 프로젝트 파일은 그대로 두고 이번만 이 Supertonic 성우로 (보통 --suffix 성우1 과 같이)
  - --vi : 한글 자막 위에 베트남어 자막을 함께 (자막 조각마다 번역해 프로젝트 파일에 저장, 다시 만들 때는 저장된 번역을 씀)
           결과 파일 이름 끝에 _베트남어자막

  - 결과: output/장문/<제목>.mp4 (+ _썸네일.png, _타임스탬프.txt, --kit 이면 업로드 문구·설명란·유튜브 썸네일도)
  - 중간에 꺼져도 다시 실행하면 나레이션(문단마다)·영상(2분 구간마다)을 이어서 만든다.
  - 배경음은 장문 연속 제작처럼 소재에 맞는 자동 생성 (장문_설정.json 의 배경음_크기)
"""
import hashlib
import importlib.util
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)
T0 = time.time()
LOG_FILE = os.path.join(HERE, "장문_진행기록.txt")


def log(x):
    line = f"[{time.strftime('%H:%M')} · {(time.time() - T0) / 60:5.1f}분] {x}"
    print(line, flush=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def main(a):
    if not a or not a[0].lower().endswith(".json"):
        print(__doc__)
        return 2
    proj_path = os.path.abspath(a[0])
    spec = importlib.util.spec_from_file_location("snm", os.path.join(HERE, "shorts_novel_maker_supertonic.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    app = m.App()
    app.withdraw()
    c = json.load(open(proj_path, encoding="utf-8"))
    cur = app.get_settings()
    st = dict(c.get("settings") or {})
    for k in m.KEEP_KEYS:                       # 내 키·AI 엔진 설정은 지금 PC 것 그대로
        if not str(st.get(k, "")).strip() or k in m.SECRET_KEYS:
            st[k] = cur.get(k, m.DEFAULTS.get(k, ""))
    c["settings"] = st
    app.apply_cfg(c)
    for k_, v_ in st.items():                  # 프로젝트에 적힌 값이 이김 (자막 스타일 묶음이 위 제목·제목 위치 등을 기본값으로 되돌리지 않게)
        if k_ in app.vars and k_ != "format" and k_ not in m.SECRET_KEYS and k_ not in m.KEEP_KEYS:
            app.vars[k_].set(str(v_))
    n_dlg = m.set_dialog_voices(c.get("dialogue") or [], c.get("cast") or [])   # 인물 대사는 그 인물 목소리로 (프로젝트 dialogue + cast 의 voice)
    if n_dlg:
        log(f"🎭 인물별 대사 목소리 {n_dlg}줄: " + ", ".join(sorted({v['who'] for v in m.DIALOG_VOICES.values()})))
    try:
        cfg = json.load(open(os.path.join(HERE, "장문_설정.json"), encoding="utf-8"))
    except Exception:
        cfg = {}
    genre = c.get("genre") or ""
    if "--소재프로필" in a and genre:          # 손으로 쓴 대본을 소재 기본 스타일(다큐 자막·제목·근거 사진)로
        app.cat_var.set(c.get("category") or m.DOC_CATEGORY)
        app.on_category()
        if app.cat_var.get() == m.DOC_CATEGORY:     # on_category 는 화면 크기만 가로로 바꾸므로 설정 칸도 맞춤 (저장된 파일을 다시 열어도 가로)
            app.vars["format"].set("롱폼 가로(1920×1080)")
        if genre in m.cat_info(app.cat_var.get())[1]:
            app.genre_var.set(genre)
            app.on_genre()
            app.apply_genre_profile(genre, quiet=True, sync=True)
        app.update()
    bgm = str((c.get("settings") or {}).get("bgm_style") or "").strip() or m.SOUND_BY_TOPIC.get(genre, "잔잔한 패드")   # 프로젝트에 정한 배경음 우선
    app.vars["bgm_mode"].set("자동생성")
    try:
        bgm_vol = float(cfg.get("배경음_크기", 0.03))
    except (TypeError, ValueError):
        bgm_vol = 0.03
    if bgm_vol > 2:          # 25 처럼 퍼센트로 적었으면 0.25 로 (0~2 범위가 아니면 배경음이 목소리를 덮음)
        bgm_vol /= 100
    app.vars["bgm_volume"].set(str(max(0.0, min(2.0, bgm_vol))))
    app.vars["target_sec"].set("0")
    # 저장한 성우(⭐ 새 성우로 저장): --성우프리셋 "이름" 또는 장문_설정.json 의 "성우_프리셋" (비우면 기본 성우 그대로)
    vp = a[a.index("--성우프리셋") + 1].strip() if "--성우프리셋" in a and a.index("--성우프리셋") + 1 < len(a) else str(cfg.get("성우_프리셋") or "").strip()
    if vp:
        tmp = {}
        if m.apply_voice_preset(tmp, vp, log):
            for k_, v_ in tmp.items():
                if k_ in app.vars:
                    app.vars[k_].set(str(v_))
    if "--성우" in a and a.index("--성우") + 1 < len(a):    # 프로젝트 파일은 그대로 두고 이번만 다른 성우로 (예: --성우 M1)
        code = a[a.index("--성우") + 1].strip()
        app.vars["narr_voice"].set(f"Supertonic {code} (남성, 무료 로컬) [supertonic:{code}]" if code[:1] == "M"
                                   else f"Supertonic {code} (여성, 무료 로컬) [supertonic:{code}]")
    app.update()
    s = app.get_settings()
    title, story = app.title_var.get().strip() or "제목 없음", app.get_story()
    if "--형식고정" not in a:    # 규칙: 영상마다 강조색·자막 효과·배경음을 다르게 (유튜브 '대량 생산 콘텐츠' 정책, 유튜브_정책.py)
        ch_ = m._YP.vary_settings(s, title, log)
        if not bgm or bgm.startswith("자동"):
            bgm = ch_["bgm_style"]
    out_root = os.path.join(s["out_dir"], "장문")
    suf = ("_" + a[a.index("--suffix") + 1]) if "--suffix" in a and a.index("--suffix") + 1 < len(a) else ""
    work = m._load_korean_reading("콘텐츠_정리").find_work(out_root, m.safe_name(title)[:40] + suf, title)   # 정리된 콘텐츠면 그 폴더 안의 작업 폴더
    os.makedirs(work, exist_ok=True)
    m.SCRIPT_ENGINE["s"] = s
    m.PHOTO_PLAN.update(sub=True, n=0)
    m.HIT_CTX["category"] = c.get("category") or m.DOC_CATEGORY
    m.set_tts_cfg(s)
    gate = m.PauseGate(os.path.join(HERE, "장문_일시정지중.flag"), app.cancel, log)
    app.cancel = gate
    is_long = (c.get("category") or m.DOC_CATEGORY) == m.DOC_CATEGORY and not suf and "세로" not in str(s.get("format", ""))
    if is_long and "--길이고정" not in a:    # 규칙: 롱폼은 10~15분. 짧으면 사진을 찾기 전에 내용을 더해 늘리고 프로젝트에 저장
        story, longer = m.length_fix(app.model_var.get().strip(), story, c.get("notes", ""), c.get("sources") or [], log, gate)
        if longer:
            app.set_story(story)
            d_ = app.project_dict()
            d_["settings"] = {k: v for k, v in d_["settings"].items() if k not in m.SECRET_KEYS}
            m.atomic_write_text(proj_path, json.dumps(d_, ensure_ascii=False, indent=1))
            log("⏱ 늘린 대본을 프로젝트에 저장 (다시 실행하면 이 대본으로)")
    if "--사진" in a:          # 대본에 사진이 적으면 웹에서 근거 사진을 자동으로 찾아 넣음
        os.makedirs(os.path.join(out_root, "media"), exist_ok=True)
        try:
            i_ = a.index("--사진")
            if i_ + 1 < len(a) and a[i_ + 1].replace(".", "", 1).isdigit():
                m.DOC_PHOTO_SEC = max(5, float(a[i_ + 1]))
        except ValueError:
            pass
        before = len(m.photo_credits(story))
        log(f"📷 사진 자동 넣기: 지금 {before}장 → 나레이션 {m.DOC_PHOTO_SEC:g}초마다 한 장 목표 (웹 조사)")
        story, n_add = m.doc_add_photos(app.model_var.get().strip(), title, story, os.path.join(out_root, "media"), log, gate, fiction=m.doc_is_fiction(genre),
                                         sources=c.get("sources") or [])
        app.set_story(story)
        d_ = app.project_dict()
        d_["settings"] = {k: v for k, v in d_["settings"].items() if k not in m.SECRET_KEYS}   # 저장소에 올라가는 파일이라 API 키는 빼고 저장
        m.atomic_write_text(proj_path, json.dumps(d_, ensure_ascii=False, indent=1))
        log(f"📷 사진 {n_add}장 추가 (총 {len(m.photo_credits(story))}장) → 프로젝트에 저장")
    hooked = False
    if "--대본그대로" not in a:      # 규칙: 30초 후크 + 첫 5초 = 제목·썸네일 약속 (--대본그대로 면 손으로 쓴 오프닝 그대로)
        story, hooked = m.hook_fix(app.model_var.get().strip(), story, log, gate, title=title if is_long else "")
    n_ret = 0
    if is_long and "--형식고정" not in a and "--대본그대로" not in a:     # 규칙(1위 영상 분석): 챕터 끝 예고 + 마무리 시리즈 한 줄
        story, n_ret = m.retention_fix(app.model_var.get().strip(), story, title, log, gate)
    story, n_pol = m.polite_fix(app.model_var.get().strip(), story, log, gate)   # 규칙: 모든 나레이션은 존댓말 (자막·성우 함께)
    if hooked or n_ret or n_pol:
        app.set_story(story)
    log(f"▶ 프로젝트로 영상 만들기: {title} ({genre}) · 사진 {len(m.photo_credits(story))}장 · 배경음 {bgm}")
    proj_dir = os.path.dirname(proj_path)        # 콘텐츠 폴더(output\장문\<제목>\) 안의 프로젝트면 결과도 그 폴더에
    in_folder = os.path.normcase(os.path.dirname(proj_dir)) == os.path.normcase(os.path.abspath(out_root))
    base = os.path.join(proj_dir if in_folder else out_root, m.safe_name(title) + suf)
    m.atomic_write_text(base + "_프로젝트.json", json.dumps(app.project_dict(), ensure_ascii=False, indent=1))
    open(base + ".만드는중", "w").close()      # 콘텐츠 정리가 만드는 중인 것을 건드리지 않게 (끝나면 지움)

    if "--썸네일만" in a:       # 영상은 그대로 두고 썸네일 후보만 새로 (디자인 16가지 + 영상 장면). 지금 유튜브 썸네일은 그대로
        log("🖼 썸네일 후보만 만드는 중...")
        m.make_thumbnails(app.model_var.get().strip(), base, title, story, c.get("category") or m.DOC_CATEGORY, s, log, keep_final=True)
        log("✅ 썸네일 후보 완료 → " + base + "_썸네일_후보")
        try:
            app.destroy()
        except Exception:
            pass
        return 0
    log("🎙 나레이션 만드는 중... (이미 만든 문단은 건너뜀)")
    if hasattr(m, "ensure_depth_maps") and str(s.get("img_depth", "off")) == "on":
        m.ensure_depth_maps(m.story_photo_paths(story), log)
    narr = app.narration_for(story, s, log, gate)
    log(f"나레이션 완성: {len(narr)}문단 · {sum(d for _, _, d in narr) / 60:.1f}분")
    if getattr(m, "_NV", None) is not None and m._NV.REPORT:     # 문단별 나레이션 검증 기록
        m.atomic_write_text(base + "_나레이션검증.txt", m._NV.report_text(title))
        n_bad = sum(1 for r_ in m._NV.REPORT if not r_[2]["ok"])
        log(f"🔎 나레이션 검증: {len(m._NV.REPORT)}문단 중 문제 {n_bad}개" + (f" → {os.path.basename(base)}_나레이션검증.txt 확인" if n_bad else " (모두 통과)"))

    if getattr(m, "is_trad", lambda x: False)(bgm):
        s["chapter_hold"] = 4.2               # 챕터 제목 동안 나레이션을 쉬고 고쟁 연주
    r = m.make_renderer(title, story, s, narr)
    vdir = "영상구간"
    if "--vi" in a:     # 한글 자막 위에 베트남어 자막
        vi = dict(c.get("sub_trans") or {})
        texts = []
        for sg in r.segs:
            if sg["kind"] == "chapter":
                texts.append("— " + sg["text"] + " —")
            elif sg["kind"] == "text":
                texts += [x.strip() for x in r._chunks(sg)]
                texts.append(r._dialog_text(sg["text"])[0].strip())
        m.ppt_translate_vi(app.model_var.get().strip(), [t for t in texts if t], vi, log, gate)
        c["sub_trans"] = vi
        with open(proj_path, "w", encoding="utf-8") as f_:          # 번역을 프로젝트에 저장 (다음에 다시 번역하지 않음)
            json.dump(c, f_, ensure_ascii=False, indent=1)
        s.update(sub_trans=vi, sub_font2=m.VI_FONT, sub2_scale=float(c.get("vi_scale", 1.0) or 1.0), sub2_above="on")
        r = m.make_renderer(title, story, s, narr)
        base += "_베트남어자막"
        vdir = "영상구간_베트남어"
        log(f"🇻🇳 베트남어 자막 {len(vi)}줄 (한글 자막 위)")
    log(f"영상 길이 {m.hms(r.duration)} · 챕터 {len(r.chapter_times())}개 · 사진 {len(m.photo_credits(story))}장")
    audio = m.build_audio(r, s, bgm)
    last = [0]

    def prog(i, n):
        p = int(i * 100 / max(1, n))
        if p >= last[0] + 5:
            last[0] = p
            log(f"  MP4 {p}%")
    keys = ("fps", "format", "layout", "img_fill", "img_motion", "img_depth", "img_depth_amt", "head_style", "head_pos", "head_size", "head_show", "sub_style",
            "sub_size", "sub_layout", "sub_dialog", "sub_anim", "sub_split", "sub_hide", "style_preset", "text_color", "sub_box_alpha", "font_path", "title_font_path", "bgm_volume", "intro_sec", "outro_sec", "outro_text", "img_filter", "motion_count", "motion_chart", "motion_icon", "motion_lower", "motion_popup", "sub_trans", "sub2_above")
    key = hashlib.md5((story + "|" + getattr(m, "RENDER_VER", "") + "|" + json.dumps({k: s.get(k) for k in keys}, ensure_ascii=False) + "|" + title + "|" + ",".join(f"{d_:.3f}" for _, _, d_ in narr) + "|" + ",".join(f"{sg_['t0']:.2f}" for sg_ in getattr(r, "segs", [])) + f"|{r.duration:.2f}" + getattr(r, "fx_sig", "")).encode("utf-8")).hexdigest()   # 나레이션이 바뀌면(발음 수정 등) 영상 구간도 새로
    m.export_mp4_resumable(r, base + ".mp4", prog, gate, audio, work_dir=os.path.join(work, vdir), seg_sec=120, log=log, key=key)
    del audio
    r.thumbnail().save(base + "_썸네일.png")
    ch = r.chapter_times()
    with open(base + "_타임스탬프.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(f"{m.hms(t)} {n}" for t, n in [(0, "오프닝")] + ch))
    log("MP4 완성: " + base + ".mp4")
    if "--kit" in a:
        log("📝 업로드 문구·설명란·유튜브 썸네일 만드는 중...")
        m.publish_kit(app.model_var.get().strip(), base, title, story, c.get("category") or m.DOC_CATEGORY, genre, s, ch,
                      c.get("sources") or [], c.get("notes", ""), log)
    log("✅ 전부 완료 → " + base + ".mp4")
    # 규칙: 쇼츠는 기본적으로 만들지 않음. --쇼츠 를 붙일 때만 롱폼 완성 뒤 40~50초 세로 쇼츠를 만듦 (쇼츠_자동.py). (예전 --쇼츠없음 은 그대로 둬도 됨)
    if (c.get("category") or m.DOC_CATEGORY) == m.DOC_CATEGORY and "--쇼츠" in a and "--쇼츠없음" not in a and suf != "_쇼츠":
        try:
            m._load_korean_reading("쇼츠_자동").make_shorts(m, app.model_var.get().strip(), base + "_프로젝트.json", log)
        except Exception as e:
            log("⚠ 쇼츠 자동 만들기 실패(롱폼은 완성됨): " + (str(e).splitlines() or [type(e).__name__])[0][:120])
    # 규칙: --영어 / --자막언어 영어,일본어 면 유튜브 '번역' 기능에 붙일 언어별 자막(SRT)·제목·설명란도 (영어_번역.py). 영상·국내 조회수는 그대로
    langs = a[a.index("--자막언어") + 1].split(",") if "--자막언어" in a and a.index("--자막언어") + 1 < len(a) else []
    if "--영어" in a and "영어" not in langs:
        langs.append("영어")
    if langs and suf != "_쇼츠":
        try:
            tr = m._load_korean_reading("영어_번역")
            tr.make_translations(base + "_프로젝트.json", [tr.LANG_KO[x.strip()] for x in langs if x.strip() in tr.LANG_KO], log)
        except BaseException as e:
            log("⚠ 자막·번역 키트 실패(영상은 완성됨): " + (str(e).splitlines() or [type(e).__name__])[0][:120])
    try:
        os.remove(base + ".만드는중")
    except OSError:
        pass
    # 규칙: 다 만들면 콘텐츠(롱폼 + 쇼츠)를 output\장문\<제목>\ 폴더 하나로 정리 (콘텐츠_정리.py). 쇼츠 단독 실행은 롱폼 쪽에서 함께 정리
    if (c.get("category") or m.DOC_CATEGORY) == m.DOC_CATEGORY and suf != "_쇼츠":
        try:
            m._load_korean_reading("콘텐츠_정리").organize(base + "_프로젝트.json", log, os.path.abspath(out_root))
        except Exception as e:
            log("⚠ 콘텐츠 폴더 정리 실패(파일은 그대로): " + (str(e).splitlines() or [type(e).__name__])[0][:120])
    try:
        app.destroy()
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
