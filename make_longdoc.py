"""장문(긴 나레이션 다큐) 자동 제작: 대본 → 나레이션 → MP4 → 썸네일·업로드 문구
- 설정은 '장문_설정.json' (처음 실행하면 기본값으로 만들어짐 - 주제·길이·배경음 크기를 고쳐서 쓰세요)
- 일시정지: 장문_일시정지.bat (출근 전) / 재개: 장문_재개.bat
- 창을 닫거나 PC를 꺼도: 장문_만들기.bat 을 다시 실행하면 끝난 단계(조사·구성안·챕터·나레이션 문단·영상 5분 구간)는 건너뛰고 이어서 함
- 프로그램 설정 파일(shorts_novel_config.json)은 바꾸지 않음
"""
import importlib.util
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
CFG = os.path.join(HERE, "장문_설정.json")
PAUSE = os.path.join(HERE, "장문_일시정지중.flag")
DEFAULT = {
    "주제": "수심 1만 미터, 마리아나 해구 바닥에는 무엇이 살고 있을까?",
    "소재": "심해의 세계",
    "길이_분": 10,
    "배경음": "심해",
    "배경음_크기": 0.2,
    "웹조사": True,
    "챕터별_사진": True,
    "사진_간격_초": 15,
    "영상_구간_분": 2,
}
MORE_PHOTOS = "--more-photos" in sys.argv
SEG_SEC = 120

T0 = time.time()
LOG_FILE = os.path.join(HERE, "장문_진행기록.txt")


def log(x):
    line = f"[{time.strftime('%H:%M')} · {(time.time() - T0) / 60:5.1f}분] {x}"
    print(line, flush=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def main():
    if not os.path.exists(CFG):
        json.dump(DEFAULT, open(CFG, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    c = dict(DEFAULT, **json.load(open(CFG, encoding="utf-8")))
    spec = importlib.util.spec_from_file_location("snm", os.path.join(HERE, "shorts_novel_maker_supertonic.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    global SEG_SEC
    m.DOC_PHOTO_SEC = max(10, float(c.get("사진_간격_초", 15)))
    SEG_SEC = int(max(1, float(c.get("영상_구간_분", 2))) * 60)

    app = m.App()
    app.withdraw()
    app.update()
    app.cat_var.set(m.DOC_CATEGORY)
    app.on_category()
    if c["소재"] in m.cat_info(m.DOC_CATEGORY)[1]:
        app.genre_var.set(c["소재"])
        app.on_genre()
    app.topic_var.set(c["주제"])
    app.vars["bgm_mode"].set("자동생성")
    app.vars["bgm_volume"].set(str(c["배경음_크기"]))
    s = app.get_settings()
    out_root = os.path.join(s["out_dir"], "장문")
    work = os.path.join(out_root, "_작업_" + m.safe_name(c["주제"])[:40])
    os.makedirs(work, exist_ok=True)
    m.SCRIPT_ENGINE["s"] = s
    m.PHOTO_PLAN.update(sub=True, n=0)
    m.HIT_CTX["category"] = m.DOC_CATEGORY
    m.set_tts_cfg(s)
    gate = m.PauseGate(PAUSE, app.cancel, log)
    app.cancel = gate          # 대본 작성도 일시정지를 따르게
    model = app.model_var.get().strip()
    log(f"▶ 시작: {c['주제']} ({c['소재']}, {c['길이_분']}분) · 배경음 {c['배경음']} 크기 {c['배경음_크기']} · {s['fps']}fps")

    # 1) 대본 (조사·구성안·챕터마다 저장)
    script_json = os.path.join(work, "대본.json")
    res = None
    if os.path.exists(script_json):
        try:
            res = json.load(open(script_json, encoding="utf-8"))
            log("대본: 이미 완성됨 → " + res["title"])
        except Exception:
            log("대본 파일이 깨져 있어 진행 기록에서 다시 합칩니다")
    if res is None:
        res = app.generate_longdoc(model, c["주제"], c["소재"], c["길이_분"], log, research=c["웹조사"], autophoto=c["챕터별_사진"],
                                   reference="", media_dir=os.path.join(out_root, "media"),
                                   state_path=os.path.join(work, "대본_진행.json"), gate=gate)
        m.atomic_write_text(script_json, json.dumps(res, ensure_ascii=False, indent=1))
        log(f"대본 완성: {res['title']} | {res['note']}")
    title, story = res["title"], res["story"]
    # 사진 보강 (장문_사진보강.bat): 이미 만든 대본에 사진을 더 넣고 영상만 다시 만듦
    done_flag = os.path.join(work, "사진보강_완료.txt")
    req_flag = os.path.join(work, "사진보강_요청.txt")      # 보강 중에 꺼져도 장문_만들기.bat 으로 이어지게
    if MORE_PHOTOS and not os.path.exists(done_flag):
        m.atomic_write_text(req_flag, time.strftime("%Y-%m-%d %H:%M"))
    if os.path.exists(req_flag) and not os.path.exists(done_flag):
        bak = os.path.join(work, "대본_사진보강전.json")
        if not os.path.exists(bak):
            m.atomic_write_text(bak, json.dumps(res, ensure_ascii=False, indent=1))
        before = len(m.photo_credits(story))
        log(f"📷 사진 보강 시작: 지금 {before}장 → 나레이션 {m.DOC_PHOTO_SEC}초에 한 장 목표")
        story, n_add = m.doc_add_photos(model, title, story, os.path.join(out_root, "media"), log, gate,
                                        fiction=m.doc_is_fiction(c["소재"]))
        res["story"] = story
        m.atomic_write_text(script_json, json.dumps(res, ensure_ascii=False, indent=1))
        m.atomic_write_text(done_flag, f"{before} -> {before + n_add}")
        log(f"📷 사진 보강 완료: {n_add}장 추가 (총 {len(m.photo_credits(story))}장)")
    # 전원이 꺼지며 깨진 사진이 있으면 그 사진 줄만 뺌
    from PIL import Image
    keep, dropped = [], 0
    for line in story.split("\n"):
        md = m.parse_media(line)
        if md:
            p_ = md[0] if os.path.isabs(md[0]) else os.path.join(m.BASE, md[0])
            try:
                with Image.open(p_) as im:
                    im.load()
            except Exception:
                dropped += 1
                continue
        keep.append(line)
    if dropped:
        story = "\n".join(keep)
        log(f"깨진 사진 {dropped}장을 빼고 진행합니다")
    base = os.path.join(out_root, m.safe_name(title))
    app.title_var.set(title)
    app.set_story(story)
    app.set_sources(res.get("sources"), res.get("notes"))
    app.vars["target_sec"].set("0")
    m.atomic_write_text(base + "_프로젝트.json", json.dumps(app.project_dict(), ensure_ascii=False, indent=1))
    s = app.get_settings()

    # 2) 나레이션 (문단마다 저장 → 이어서)
    log("🎙 나레이션 만드는 중... (이미 만든 문단은 건너뜀)")
    if hasattr(m, "ensure_depth_maps") and str(s.get("img_depth", "off")) == "on":
        m.ensure_depth_maps(m.story_photo_paths(story), log)
    narr = app.narration_for(story, s, lambda x: None, gate)
    log(f"나레이션 완성: {len(narr)}문단 · {sum(d for _, _, d in narr) / 60:.1f}분")

    # 3) 영상 (5분 구간마다 저장 → 이어서)
    r = m.make_renderer(title, story, s, narr)
    log(f"영상 길이 {m.hms(r.duration)} · 챕터 {len(r.chapter_times())}개 · 사진 {len(m.photo_credits(story))}장")
    audio = m.build_audio(r, s, c["배경음"])
    last = [0]

    def prog(i, n):
        p = int(i * 100 / max(1, n))
        if p >= last[0] + 5:
            last[0] = p
            log(f"  MP4 {p}%")
    import hashlib
    key = hashlib.md5((story + "|" + json.dumps({k: s.get(k) for k in ("fps", "format", "layout", "img_fill", "img_motion", "head_style", "sub_style",
                                                                         "font_path", "title_font_path", "bgm_volume")}, ensure_ascii=False)
                       + "|" + title).encode("utf-8")).hexdigest()
    m.export_mp4_resumable(r, base + ".mp4", prog, gate, audio, work_dir=os.path.join(work, "영상구간"), seg_sec=SEG_SEC, log=log, key=key)
    del audio
    r.thumbnail().save(base + "_썸네일.png")
    ch = r.chapter_times()
    with open(base + "_타임스탬프.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(f"{m.hms(t)} {n}" for t, n in [(0, "오프닝")] + ch))
    log("MP4 완성: " + base + ".mp4")

    # 4) 업로드 문구 + 설명란 완성본 + 유튜브 썸네일
    log("📝 업로드 문구·설명란·유튜브 썸네일 만드는 중...")
    m.publish_kit(model, base, title, story, m.DOC_CATEGORY, c["소재"], s, ch, res.get("sources") or [], res.get("notes", ""), log)
    app.destroy()
    log("✅ 전부 완료 → " + out_root)


def _job_procs():
    """지금 돌고 있는 장문 만들기 작업(파이썬·그 창)의 프로세스 번호들"""
    import subprocess
    ps = ("Get-CimInstance Win32_Process | Where-Object { ($_.CommandLine -like '*make_longdoc.py*' -and $_.CommandLine -notlike '*--safe-stop*' "
          "-and $_.CommandLine -notlike '*--pause*' -and $_.CommandLine -notlike '*--resume*') } "
          "| ForEach-Object { $_.ProcessId }")
    out = subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, text=True).stdout
    return [int(x) for x in out.split() if x.strip().isdigit() and int(x) != os.getpid()]


def _paused_in_log(since=0):
    """진행 기록에서 since 바이트 이후(또는 마지막 시작 이후)에 '일시정지 중'이 찍히고 그 뒤 '재개'가 없으면 True"""
    try:
        with open(LOG_FILE, "rb") as f:
            f.seek(since)
            lines = f.read().decode("utf-8", "ignore").splitlines()
    except OSError:
        return False
    st = -1
    for i, ln in enumerate(lines):
        if "⏸ 일시정지 중" in ln:
            st = i
        elif "▶ 재개" in ln or "▶ 시작" in ln:
            st = -1
    return st >= 0


def safe_stop():
    """장문_끄기전_정리.bat: 일시정지 → 실제로 멈출 때까지 기다림 → 작업 종료 → (선택) PC 끄기"""
    import subprocess
    procs = _job_procs()
    if not procs:
        print("지금 돌고 있는 장문 작업이 없어요. 그냥 전원을 꺼도 됩니다.")
    else:
        size = os.path.getsize(LOG_FILE) if os.path.exists(LOG_FILE) else 0
        already = os.path.exists(PAUSE) and _paused_in_log(0)
        open(PAUSE, "w").close()
        if not already:
            print("⏸ 일시정지를 요청했어요. 지금 하던 작은 단계가 끝날 때까지 기다립니다...")
            print("   (AI가 글이나 사진을 찾는 중이면 몇 분 걸릴 수 있어요. 기다리기 싫으면 이 창을 닫고 그냥 꺼도 저장된 곳부터 이어집니다)")
            t0 = time.time()
            while not _paused_in_log(size):
                if not _job_procs():
                    break
                if time.time() - t0 > 20 * 60:
                    print("   20분이 지나도 멈추지 않아 지금 상태로 정리합니다 (하던 단계 하나만 다시 하게 돼요).")
                    break
                time.sleep(3)
                print(f"\r   기다리는 중... {int(time.time() - t0)}초", end="", flush=True)
            print()
        for pid in procs:
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)], capture_output=True)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{time.strftime('%H:%M')}] ⏹ 끄기 전 정리로 작업을 멈춤 - 다시 켠 뒤 장문_만들기.bat 을 실행하면 이어서 합니다\n")
        print("✅ 안전하게 멈췄어요. 이제 전원을 꺼도 됩니다.")
        print("   다시 켠 뒤 '장문_만들기.bat' 을 실행하면 멈춘 곳부터 이어서 만듭니다.")
    print()
    print("  1 = 지금 PC 끄기 (시스템 종료)")
    print("  2 = 최대 절전 모드 (열려 있던 창이 그대로 남음)")
    print("  그 외 = 아무것도 안 하고 닫기")
    try:
        ans = input("선택: ").strip()
    except EOFError:
        ans = ""
    if ans == "1":
        subprocess.run(["shutdown", "/s", "/t", "5"])
        print("5초 뒤에 꺼집니다. (취소: 명령 프롬프트에서 shutdown /a)")
    elif ans == "2":
        subprocess.run(["shutdown", "/h"])


if __name__ == "__main__":
    if "--safe-stop" in sys.argv:    # 장문_끄기전_정리.bat
        safe_stop()
        sys.exit(0)
    if "--pause" in sys.argv:        # 장문_일시정지.bat
        open(PAUSE, "w").close()
        print("⏸ 일시정지 요청함. 지금 하던 작은 단계(문단 하나·장면 하나·AI 답변 하나)가 끝나면 멈춥니다.")
        print("   다시 하려면 장문_재개.bat 을 누르세요. (PC를 꺼도 장문_만들기.bat 으로 이어서 할 수 있어요)")
        sys.exit(0)
    if "--resume" in sys.argv:       # 장문_재개.bat
        if os.path.exists(PAUSE):
            os.remove(PAUSE)
            print("▶ 재개했습니다. 만들기 창에서 이어서 진행됩니다.")
        else:
            print("일시정지 상태가 아니에요. (꺼진 상태라면 장문_만들기.bat 을 실행하세요)")
        sys.exit(0)
    if os.path.exists(PAUSE):        # 일시정지된 채로 PC를 껐다 켠 경우: 다시 만들기를 누르면 바로 진행
        os.remove(PAUSE)
    try:
        main()
    except Exception as e:
        log("❌ 멈춤: " + str(e)[:300])
        log("   장문_만들기.bat 을 다시 실행하면 끝난 단계는 건너뛰고 이어서 합니다.")
        sys.exit(1)
