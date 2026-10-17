"""대본만 만들어 프로젝트 파일로 저장 (그림은 넣지 않음 → Gemini·ChatGPT 그림 작업용)

  py -3.11 -X utf8 make_script.py --genre "[교육] 개인정보보호" --topic "주제" --minutes 15 [--category 장문] [--research] [--seconds 60]

  - 장문(--category 장문, 기본): --minutes 분 길이, 챕터로 나눠 씀
  - 다른 종류(쇼츠 등): --seconds 초 길이
  - 끝에 'PROJECT <경로>' 를 출력. 이 파일을 gemini_job.py new 와 render_project.py 에 넘김
  - '⚠ 확인 필요' 줄은 대본 AI 가 사실 확인이 필요하다고 표시한 내용
"""
import argparse
import importlib.util
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)
LOG = os.path.join(HERE, "장문_진행기록.txt")


def log(x):
    line = f"[{time.strftime('%H:%M')}] [대본] {x}"
    print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--category", default="장문")
    ap.add_argument("--genre", required=True)
    ap.add_argument("--topic", default="")
    ap.add_argument("--minutes", type=float, default=10)
    ap.add_argument("--seconds", type=float, default=60)
    ap.add_argument("--research", action="store_true")
    a = ap.parse_args()
    spec = importlib.util.spec_from_file_location("snm", os.path.join(HERE, "shorts_novel_maker_supertonic.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    m.App.save_cfg = lambda self, *x, **k: None          # 사용자의 설정 파일은 건드리지 않음
    app = m.App()
    app.withdraw()
    cat = a.category if a.category in m.CATEGORIES else m.DOC_CATEGORY
    doc = cat == m.DOC_CATEGORY
    if a.genre not in m.cat_info(cat)[1]:
        print(f"소재 '{a.genre}' 가 '{cat}' 종류에 없습니다. 있는 소재: " + ", ".join(m.cat_info(cat)[1]))
        return 2
    app.cat_var.set(cat)
    app.update()
    app.genre_var.set(a.genre)
    app.topic_var.set(a.topic)
    if doc:
        app.apply_genre_profile(a.genre, quiet=True, sync=True)
    app.update()
    s = app.get_settings()
    m.SCRIPT_ENGINE["s"] = s
    m.PHOTO_PLAN.update(sub=True, n=0)
    m.HIT_CTX["category"] = cat
    model = app.model_var.get().strip()
    name = m.safe_name(a.topic or a.genre)[:40] or "대본"
    work = os.path.join(s["out_dir"], "장문" if doc else "대본", "_작업_" + name)
    os.makedirs(work, exist_ok=True)
    media = os.path.join(s["out_dir"], "장문" if doc else "", "media")
    log(f"▶ 대본 시작: {a.topic or '(주제 자동)'} · {a.genre} · " + (f"{a.minutes:g}분" if doc else f"{a.seconds:g}초") + (" · 웹 조사" if a.research else ""))
    if doc:
        res = app.generate_longdoc(model, a.topic, a.genre, a.minutes, log, research=a.research, autophoto=False, reference="",
                                   media_dir=media, state_path=os.path.join(work, "대본_진행.json"))
    else:
        res = app.generate_story(model, cat, a.topic, a.genre, a.seconds, False, log, a.research, False, "", media)
    json.dump(res, open(os.path.join(work, "대본.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    app.title_var.set(res["title"])
    app.set_story(res["story"])
    app.set_sources(res.get("sources"), res.get("notes"))
    if doc:
        app.vars["target_sec"].set("0")
    d = app.project_dict()
    d["settings"] = {k: v for k, v in d["settings"].items() if k not in m.SECRET_KEYS}
    p = os.path.join(work, m.safe_name(res["title"])[:60] + "_프로젝트.json")
    json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    log(f"대본 완성: {res['title']} | {res.get('note', '')}")
    if res.get("notes"):
        log("⚠ 확인 필요: " + str(res["notes"])[:1500])
    print("PROJECT " + p, flush=True)
    try:
        app.destroy()
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
