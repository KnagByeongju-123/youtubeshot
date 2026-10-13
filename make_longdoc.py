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
    "길이_분": 30,
    "배경음": "심해",
    "배경음_크기": 0.2,
    "웹조사": True,
    "챕터별_사진": True,
}

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
    m.export_mp4_resumable(r, base + ".mp4", prog, gate, audio, work_dir=os.path.join(work, "영상구간"), seg_sec=300, log=log)
    del audio
    r.thumbnail().save(base + "_썸네일.png")
    ch = r.chapter_times()
    with open(base + "_타임스탬프.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(f"{m.hms(t)} {n}" for t, n in [(0, "오프닝")] + ch))
    log("MP4 완성: " + base + ".mp4")

    # 4) 업로드 문구
    body = m.story_text_only(story)
    heads = [p for p in m.split_paras(body) if p.startswith("## ")]
    user = (f"콘텐츠 종류: 장문 지식 다큐 ({len(body)}자)\n소재: {c['소재']}\n[지금 제목] {title}\n\n[챕터]\n" + "\n".join(heads)
            + "\n\n[본문 앞부분]\n" + body[:4000])
    try:
        pkg = m.ask_script_json(model, m.DOC_PACKAGE_SYSTEM, user)
    except Exception as e:
        log("업로드 문구 실패(나중에 프로그램에서 다시 만들 수 있어요): " + str(e)[:100])
        pkg = {"titles": [title], "description": "", "hashtags": "", "pinned_comment": ""}
    pkg.update(sources=res.get("sources") or [], chapters=ch, notes=res.get("notes", ""))
    m.write_package(base, title, story, pkg)
    log("업로드 문구 저장: " + base + "_업로드문구.txt")
    app.destroy()
    log("✅ 전부 완료 → " + out_root)


if __name__ == "__main__":
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
