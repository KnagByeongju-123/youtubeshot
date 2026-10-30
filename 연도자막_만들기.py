"""연도 자막 만들기 — 그림마다 '언제 일인지'(큰 연도) + 한 줄 설명을 정해 그림 옆 <그림>.연도.json 에 저장
(영상에서는 앞 그림과 연도가 다를 때만, 그림이 나타난 뒤 4초 동안 화면 위쪽 가운데에 보임 — VGraphs 쇼츠 참고)

  python -X utf8 연도자막_만들기.py <프로젝트.json> [--다시]
  (서버에서는 xvfb-run -a 로 실행)
  - 대본 AI 가 그림마다 그 그림이 나오는 동안 읽는 나레이션을 보고 정함. 대본·출처에 없는 연도는 지어내지 않음(모르면 비움)
  - 이미 만든 그림은 건너뜀 (--다시 면 모두 새로)
"""
import importlib.util
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)
T0 = time.time()

YEAR_SYSTEM = """너는 역사 다큐 영상 편집자다. 그림마다 화면에 띄울 '연도 자막'을 정한다.
- year: 그 그림이 보여 주는 장면이 일어난 때. 예: "191년", "280년대", "1300년대", "2009년", "오늘". 나레이션·대본에 나온 연도만 쓴다(지어내지 않음)
  · 장면이 특정한 때가 아니거나(개념·비유) 나레이션에서 알 수 없으면 ""
  · 같은 사건의 연속 장면은 같은 year 를 그대로 (영상은 year 가 바뀔 때만 자막을 띄움)
- label: 그 때에 무슨 일인지 한 줄, 14자 이내, 명사형 (예: "양인 전투", "진수, 『삼국지』를 쓰다", "나관중 『삼국지연의』"). year 가 "" 이면 ""
반드시 JSON만 출력: {"images": [{"n": 1, "year": "191년", "label": "양인 전투"}]}"""


def log(x):
    print(f"[{time.strftime('%H:%M')} · {(time.time() - T0) / 60:5.1f}분] {x}", flush=True)


def main(a):
    if not a or not a[0].lower().endswith(".json"):
        print(__doc__)
        return 2
    proj = os.path.abspath(a[0])
    spec = importlib.util.spec_from_file_location("snm", os.path.join(HERE, "shorts_novel_maker_supertonic.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    app = m.App()
    app.withdraw()
    c = json.load(open(proj, encoding="utf-8"))
    cur = app.get_settings()
    st = dict(c.get("settings") or {})
    for k in m.KEEP_KEYS:
        if not str(st.get(k, "")).strip() or k in m.SECRET_KEYS:
            st[k] = cur.get(k, m.DEFAULTS.get(k, ""))
    c["settings"] = st
    app.apply_cfg(c)
    app.update()
    s = app.get_settings()
    m.set_tts_cfg(s)
    title, story = app.title_var.get().strip(), app.get_story()
    narr = app.narration_for(story, s, lambda x: None, None)
    r = m.make_renderer(title, story, s, narr)
    paths = getattr(r, "img_paths", [])
    pieces = r._img_pieces(r.duration)
    rows = []
    for im_, a_, b_ in pieces:
        txt = " ".join(sg["text"] for k, sg in enumerate(r.segs) if sg["kind"] in ("text", "chapter") and sg["t0"] < b_ - 0.3 and
                       (r.segs[k + 1]["t0"] if k + 1 < len(r.segs) else r.duration) > a_ + 0.3)
        cap = r.images[im_][1] if im_ < len(r.images) else ""
        rows.append((paths[im_] if im_ < len(paths) else "", cap, txt))
    todo = [i for i, (p_, _, _) in enumerate(rows) if p_ and ("--다시" in a or not os.path.exists(p_ + ".연도.json"))]
    log(f"그림 {len(rows)}장 중 연도 자막을 정할 그림 {len(todo)}장")
    model = app.model_var.get().strip()
    for g0 in range(0, len(todo), 30):
        grp = todo[g0:g0 + 30]
        body = "\n".join(f"그림 {n + 1} (그림 설명: {rows[i][1]}) 나레이션: {rows[i][2][:300]}" for n, i in enumerate(grp))
        d = m.ask_json(model, YEAR_SYSTEM, f"[영상 제목] {title}\n[그림 {len(grp)}장, 나오는 순서대로]\n{body}")
        got = {int(x.get("n", 0)) - 1: x for x in d.get("images") or [] if isinstance(x, dict)}
        for n, i in enumerate(grp):
            x = got.get(n) or {}
            json.dump({"year": str(x.get("year") or "").strip()[:12], "label": str(x.get("label") or "").strip()[:20]},
                      open(rows[i][0] + ".연도.json", "w", encoding="utf-8"), ensure_ascii=False)
        log(f"  {min(len(todo), g0 + 30)}/{len(todo)}")
    shown, last = [], None
    for p_, _, _ in rows:
        try:
            info = json.load(open(p_ + ".연도.json", encoding="utf-8"))
        except Exception:
            continue
        if info.get("year") and info["year"] != last:
            shown.append(f"{info['year']} · {info.get('label', '')}")
        last = info.get("year") or last
    log(f"✅ 화면에 뜨는 연도 자막 {len(shown)}번: " + " → ".join(shown))
    app.destroy()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
