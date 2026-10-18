"""프로젝트 파일(.json) 하나를 바로 MP4 로 (장문 연속 제작과 같은 순서: 나레이션 → 영상 → 썸네일·타임스탬프)

  py -3.11 -X utf8 render_project.py <프로젝트.json> [--kit] [--vi]

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
    try:
        cfg = json.load(open(os.path.join(HERE, "장문_설정.json"), encoding="utf-8"))
    except Exception:
        cfg = {}
    genre = c.get("genre") or ""
    bgm = m.SOUND_BY_TOPIC.get(genre, "잔잔한 패드")
    app.vars["bgm_mode"].set("자동생성")
    app.vars["bgm_volume"].set(str(cfg.get("배경음_크기", 25)))
    app.vars["target_sec"].set("0")
    app.update()
    s = app.get_settings()
    title, story = app.title_var.get().strip() or "제목 없음", app.get_story()
    out_root = os.path.join(s["out_dir"], "장문")
    work = os.path.join(out_root, "_작업_" + m.safe_name(title)[:40])
    os.makedirs(work, exist_ok=True)
    m.SCRIPT_ENGINE["s"] = s
    m.PHOTO_PLAN.update(sub=True, n=0)
    m.HIT_CTX["category"] = c.get("category") or m.DOC_CATEGORY
    m.set_tts_cfg(s)
    gate = m.PauseGate(os.path.join(HERE, "장문_일시정지중.flag"), app.cancel, log)
    app.cancel = gate
    log(f"▶ 프로젝트로 영상 만들기: {title} ({genre}) · 사진 {len(m.photo_credits(story))}장 · 배경음 {bgm}")
    base = os.path.join(out_root, m.safe_name(title))
    m.atomic_write_text(base + "_프로젝트.json", json.dumps(app.project_dict(), ensure_ascii=False, indent=1))

    log("🎙 나레이션 만드는 중... (이미 만든 문단은 건너뜀)")
    if hasattr(m, "ensure_depth_maps") and str(s.get("img_depth", "off")) == "on":
        m.ensure_depth_maps(m.story_photo_paths(story), log)
    narr = app.narration_for(story, s, lambda x: None, gate)
    log(f"나레이션 완성: {len(narr)}문단 · {sum(d for _, _, d in narr) / 60:.1f}분")

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
            "sub_size", "sub_layout", "sub_dialog", "sub_anim", "sub_split", "style_preset", "text_color", "sub_box_alpha", "font_path", "title_font_path", "bgm_volume", "sub_trans", "sub2_above")
    key = hashlib.md5((story + "|" + getattr(m, "RENDER_VER", "") + "|" + json.dumps({k: s.get(k) for k in keys}, ensure_ascii=False) + "|" + title).encode("utf-8")).hexdigest()
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
    try:
        app.destroy()
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
