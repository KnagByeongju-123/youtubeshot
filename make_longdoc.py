"""장문(긴 나레이션 다큐) 자동 제작: 대본 → 나레이션 → MP4 → 썸네일·업로드 문구
- 설정은 '장문_설정.json' (처음 실행하면 기본값으로 만들어짐 - 주제·길이·배경음 크기를 고쳐서 쓰세요)
- 일시정지: 장문_일시정지.bat (출근 전) / 재개: 장문_재개.bat (만들기 창이 꺼져 있으면 새로 띄워서 이어서 함)
- 끄기 전: 장문_끄기전_정리.bat (지금 단계가 끝나면 멈추고 저장 → PC 끄기/절전 선택)
- 창을 닫거나 PC를 꺼도: 장문_만들기.bat(또는 장문_재개.bat)을 다시 실행하면 끝난 단계(조사·구성안·챕터·나레이션 문단·영상 구간)는 건너뛰고 이어서 함
- 주의: 웹 조사·챕터 집필처럼 AI가 답하는 동안(최대 15분)은 중간 저장이 없음 → 그 사이 끄면 그 단계 하나만 다시 함
- 연속 제작: 장문_연속제작.bat → AI가 인기 주제를 골라 '연속_편수' 편을 차례로 만듦 (소재는 '연속_소재' 목록을 돌아가며, 비우면 기본 목록)
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
    "연속_편수": 5,
    "연속_소재": [],
}
# 연속 제작 때 '연속_소재'가 비어 있으면 이 소재들을 돌아가며 씀 (10분 롱폼으로 반응 좋은 묶음)
BATCH_GENRES = ["세계의 축제", "신기한 풍속과 전통", "역사를 바꾼 결정적 순간", "세계의 외딴 마을과 작은 나라", "고고학 발굴 이야기",
                "세계의 음식 문화", "대형 사고에서 배운 교훈", "도시 하나 깊이 보기", "발명과 우연한 발견", "세계의 신화와 민담 여행",
                "심해의 세계", "세계의 신기한 법과 예절", "미라와 무덤의 비밀", "세계의 명절과 새해 풍습", "최신 고고학 발견"]
BATCH = "--batch" in sys.argv
MORE_PHOTOS = "--more-photos" in sys.argv
SEG_SEC = 120

T0 = time.time()
LOG_FILE = os.path.join(HERE, "장문_진행기록.txt")


def log(x):
    line = f"[{time.strftime('%H:%M')} · {(time.time() - T0) / 60:5.1f}분] {x}"
    print(line, flush=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def made_topics(m, out_root):
    """이미 만든(만들기 시작한) 장문 주제들 - 연속 제작 때 같은 주제를 피하려고"""
    if not os.path.isdir(out_root):
        return []
    return [n[len("_작업_"):] for n in os.listdir(out_root) if n.startswith("_작업_")]


def pick_topic(m, app, genre, seen, log):
    """연속 제작: AI(웹 검색)가 이 소재로 지금 반응 좋을 10분 다큐 주제 하나를 고름"""
    topics = m.cat_info(m.DOC_CATEGORY)[1]
    formula = topics.get(genre, ("(사용자가 직접 정한 소재)", ""))[0]
    user = (f"콘텐츠 종류: {m.DOC_CATEGORY} (실제 사건·사실만)\n소재: {genre}\n소재 공식: {formula}\n"
            f"이 소재로 10분 나레이션 다큐로 풀 수 있는, 지금 유튜브에서 반응 좋을 주제 5개를 만들어줘 (제목처럼 궁금증을 부르는 질문·반전형, 35자 이내). "
            f"오늘({time.strftime('%Y년 %m월')}) 기준 최근 1~2년 화제·새 발견과 이어진 것을 먼저, 나머지는 꾸준히 인기 있는 것으로.\n"
            "[웹 검색 모드] WebSearch 로 최근 화제가 된 사건·발견·현상을 찾아 그중에서 고른다. 실제로 존재하는 것만. "
            "유튜브에서 비슷한 주제의 긴 영상이 반응이 좋았는지, 아직 덜 다뤄진 틈새인지도 살핀다.")
    if seen:
        user += "\n\n[이미 만든 주제 - 같은 것은 물론 비슷한 것(같은 대상·같은 질문)도 피하고 새로운 대상·각도로]\n- " + "\n- ".join(seen[-60:])
    user += '\n출력: {"ideas": ["..."], "why": ["..."]} (반응이 좋을 순서대로)'
    d = m.ask_json_alive(app.model_var.get().strip(), m.IDEA_SYSTEM, user, tools=m.WEB_TOOLS, log=log, label="인기 주제 고르기")
    ideas = [str(x).strip() for x in (d.get("ideas") or []) if str(x).strip()]
    ideas = [x for x in ideas if x not in seen] or ideas
    if not ideas:
        raise RuntimeError("주제를 고르지 못했습니다")
    why = (d.get("why") or [""])[0] if isinstance(d.get("why"), list) else ""
    log(f"🎯 고른 주제: {ideas[0]}" + (f"  ({str(why)[:80]})" if why else ""))
    return ideas[0]


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
    gate = m.PauseGate(PAUSE, app.cancel, log)
    app.cancel = gate          # 대본 작성도 일시정지를 따르게
    if not BATCH:
        run_doc(m, app, c, gate)
        app.destroy()
        return
    # ---- 연속 제작: 소재를 돌아가며 AI가 주제를 고르고 한 편씩 끝까지 ----
    n = int(c.get("연속_편수") or 5)
    genres = [g_ for g_ in (c.get("연속_소재") or []) if g_ in m.cat_info(m.DOC_CATEGORY)[1]] or BATCH_GENRES
    out_root = os.path.join(app.get_settings()["out_dir"], "장문")
    os.makedirs(out_root, exist_ok=True)
    state_p = os.path.join(out_root, "_연속제작_진행.json")
    st = {}
    try:
        st = json.load(open(state_p, encoding="utf-8"))
    except Exception:
        pass
    done_list = list(st.get("done") or [])
    cur = st.get("current")      # 꺼졌다 켜면 만들던 편부터 이어서
    log(f"🔁 연속 제작 시작: {n}편 · {c['길이_분']}분 · 소재 {len(genres)}개 돌아가며 (끝난 편 {len(done_list)}개)")
    k = len(done_list)
    while k < n:
        if cur and cur.get("주제"):
            ci = dict(c, 주제=cur["주제"], 소재=cur.get("소재") or c["소재"])
            log(f"▶ {k + 1}/{n}편 이어서: {ci['주제']} ({ci['소재']})")
        else:
            genre = genres[(k + int(st.get("offset") or 0)) % len(genres)]
            log(f"🔎 {k + 1}/{n}편 주제 고르는 중... 소재: {genre}")
            seen = made_topics(m, out_root) + [d_.get("주제", "") for d_ in done_list]
            topic = pick_topic(m, app, genre, seen, log)
            cur = {"주제": topic, "소재": genre, "시작": time.strftime("%Y-%m-%d %H:%M")}
            m.atomic_write_text(state_p, json.dumps({"done": done_list, "current": cur, "offset": st.get("offset", 0)}, ensure_ascii=False, indent=1))
            ci = dict(c, 주제=topic, 소재=genre)
        ci["배경음"] = m.SOUND_BY_TOPIC.get(ci["소재"], c.get("배경음") or "잔잔한 패드")
        res = run_doc(m, app, ci, gate)
        done_list.append({"주제": ci["주제"], "소재": ci["소재"], "제목": res.get("title", ""), "완료": time.strftime("%Y-%m-%d %H:%M")})
        cur = None
        k += 1
        m.atomic_write_text(state_p, json.dumps({"done": done_list, "current": None, "offset": st.get("offset", 0)}, ensure_ascii=False, indent=1))
        log(f"✅ {k}/{n}편 완료")
    log(f"🏁 연속 제작 {n}편 모두 완료 → {out_root}  (더 만들려면 '연속_편수'를 늘리거나 {os.path.basename(state_p)} 을 지우세요)")
    app.destroy()


def run_doc(m, app, c, gate):
    """한 편 끝까지: 대본 → 사진 → 나레이션 → MP4 → 업로드 문구. 결과 res(dict) 돌려줌"""
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
    if MORE_PHOTOS and not BATCH and not os.path.exists(done_flag):
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
    log("✅ 전부 완료 → " + out_root)
    return res


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
            print("   (AI가 조사·집필 중이면 그 답이 올 때까지 최대 15분 걸릴 수 있어요. 기다리기 싫으면 이 창을 닫고 그냥 꺼도 되고,")
            print("    그러면 그 단계 하나만 다시 하게 됩니다. 끝난 단계는 모두 저장되어 있습니다)")
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
        import subprocess
        was_paused = os.path.exists(PAUSE)
        if was_paused:
            os.remove(PAUSE)
        if _job_procs():
            print("▶ 재개했습니다. 만들기 창에서 이어서 진행됩니다." if was_paused else "이미 만들기가 돌아가고 있어요. (일시정지 상태 아님)")
        else:
            # 만들기 창이 없음(끄기 전 정리로 멈췄거나 PC를 껐다 켠 경우) → 만들기를 새 창으로 띄워 저장된 곳부터 이어서
            print("만들기 창이 꺼져 있어 새로 띄웁니다. 끝난 단계는 건너뛰고 멈춘 곳부터 이어서 합니다.")
            bat = os.path.join(HERE, "장문_만들기.bat")
            if os.path.exists(bat):
                subprocess.Popen(f'start "" "{bat}"', shell=True, cwd=HERE)
            else:
                subprocess.Popen([sys.executable, "-X", "utf8", os.path.abspath(__file__)], cwd=HERE,
                                 creationflags=getattr(subprocess, "CREATE_NEW_CONSOLE", 0))
        sys.exit(0)
    if os.path.exists(PAUSE):        # 일시정지된 채로 PC를 껐다 켠 경우: 다시 만들기를 누르면 바로 진행
        os.remove(PAUSE)
    try:
        main()
    except Exception as e:
        log("❌ 멈춤: " + str(e)[:300])
        log("   장문_만들기.bat 을 다시 실행하면 끝난 단계는 건너뛰고 이어서 합니다.")
        sys.exit(1)
