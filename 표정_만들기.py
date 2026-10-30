"""표정 바뀌기 만들기 — 감정이 있는 문장에서 그림 속 인물의 표정이 바뀌게 (그림 옆 <그림>.표정.json + <그림>.표정.jpg)

  python -X utf8 표정_만들기.py <프로젝트.json> [--최대 8] [--다시]
  (서버에서는 xvfb-run -a 로 실행)

  1) 대본 AI(Claude)가 그림을 Read 로 열어 보고, 얼굴이 크게 나왔고 그 그림이 나오는 동안 감정(반전·놀람·분노·슬픔)이 있는 장면을 골라
     얼굴 상자 · 바뀔 표정(영어) · 바뀌는 때(그림이 머무는 시간 중 0.55~0.85) 를 정함
  2) klein 이 얼굴 칸만 그 표정으로 다시 그림 (그 인물 캐릭터 시트를 기준 그림으로 → 같은 얼굴)
  3) <그림>.표정.jpg 와 <그림>.표정.json {"image", "at", "expr"} 저장 → 영상에서 그 때부터 0.8초 동안 표정이 바뀜
  4) 확인용: <프로젝트 폴더>/_표정_확인.png (원래 얼굴 | 바뀐 얼굴) — 사람이 크게 열어 검수, 이상한 것은 .표정.json 을 지움
"""
import importlib.util
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)
T0 = time.time()

EXPR_SYSTEM = """너는 역사 다큐 영상 연출가다. 그림이 나오는 동안 읽는 나레이션에 맞춰, 그림 속 인물의 표정이 한 번 바뀌는 장면을 고른다.
- 그림 파일을 Read 로 직접 열어 본다. 얼굴이 크게(그림 높이의 15% 이상) 또렷하게 나온 그림만. 뒷모습·옆으로 작은 얼굴·여러 명이 작게 나온 그림은 고르지 않는다
- 그 그림이 나오는 동안의 나레이션에 감정이 바뀌는 순간(반전, 놀람, 분노, 당황, 슬픔, 자신만만)이 있는 장면만. 최대 {max_n}장, 영상 전체에 고르게
- 바뀔 표정은 지금 그림의 표정과 확실히 다르게, 나레이션과 맞게. 실제 인물을 우스꽝스럽게 만들지 않는다
- face: 얼굴(머리·턱수염 포함, 투구는 빼도 됨) 상자, 그림 너비·높이에 대한 비율 [왼쪽, 위, 오른쪽, 아래]
- who: 등장인물 이름(목록에 있으면 그 이름), expr: 영어로 짧게 (예: "eyes wide open in shock, eyebrows raised, mouth slightly open")
- at: 그림이 머무는 시간 중 표정이 바뀌는 때 0.55~0.85 (나레이션의 그 순간 위치)
반드시 JSON만 출력: {{"scenes": [{{"n": 3, "who": "화웅", "face": [0.5, 0.05, 0.62, 0.33], "expr": "...", "at": 0.7, "why": "한 줄"}}]}}"""


def log(x):
    print(f"[{time.strftime('%H:%M')} · {(time.time() - T0) / 60:5.1f}분] {x}", flush=True)


def main(a):
    if not a or not a[0].lower().endswith(".json"):
        print(__doc__)
        return 2
    max_n = int(a[a.index("--최대") + 1]) if "--최대" in a else 8
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
    r = m.make_renderer(title, story, s, app.narration_for(story, s, lambda x: None, None))
    paths = getattr(r, "img_paths", [])
    rows = []
    for im_, a_, b_ in r._img_pieces(r.duration):
        if im_ >= len(paths) or "--다시" not in a and os.path.exists(paths[im_] + ".표정.json"):
            continue
        txt = " ".join(sg["text"] for k, sg in enumerate(r.segs) if sg["kind"] == "text" and sg["t0"] < b_ - 0.3 and
                       (r.segs[k + 1]["t0"] if k + 1 < len(r.segs) else r.duration) > a_ + 0.3)
        rows.append((paths[im_], txt))
    # 등장인물과 캐릭터 시트
    cast = []
    for d_ in [os.path.join(os.path.dirname(proj), n) for n in os.listdir(os.path.dirname(proj)) if n.startswith("_작업_")]:
        p_ = os.path.join(d_, "대본.json")
        if os.path.exists(p_):
            cast = list(json.load(open(p_, encoding="utf-8")).get("cast") or [])
    media = os.path.join(s["out_dir"], "장문", "media")
    sheets = {ch_["name"]: os.path.join(media, "_cast", m.safe_name(ch_["name"])[:40] + ".png") for ch_ in cast if ch_.get("name")}
    sheets = {k: v for k, v in sheets.items() if os.path.exists(v)}
    log(f"그림 {len(rows)}장 중 표정 바꿀 장면 고르는 중 (최대 {max_n}장) · 캐릭터 시트 {len(sheets)}명")
    body = "\n".join(f"그림 {n + 1}: {p_}\n   나레이션: {t_[:260]}" for n, (p_, t_) in enumerate(rows))
    d = m.ask_json(app.model_var.get().strip(), EXPR_SYSTEM.format(max_n=max_n),
                   f"[영상 제목] {title}\n[등장인물] {', '.join(sheets) or '없음'}\n[그림 {len(rows)}장, 나오는 순서대로 - Read 로 열어 볼 것]\n{body}",
                   tools=["Read"])
    picks = []
    for x in (d.get("scenes") or [])[:max_n]:
        try:
            n = int(x.get("n", 0)) - 1
            x0, y0, x1, y1 = [min(1.0, max(0.0, float(v))) for v in x.get("face")]
        except (TypeError, ValueError):
            continue
        if 0 <= n < len(rows) and x1 - x0 > 0.03 and y1 - y0 > 0.05 and x.get("expr"):
            picks.append((rows[n][0], [x0, y0, x1, y1], str(x["expr"]), min(0.85, max(0.55, float(x.get("at") or 0.7))),
                          str(x.get("who") or ""), str(x.get("why") or "")))
    for p_, _, ex, at, who, why in picks:
        log(f"  🎭 {os.path.basename(p_)} {who}: {ex[:60]} ({why[:50]})")
    if not picks:
        log("고른 장면이 없음")
        return 0
    from PIL import Image
    fixes = []
    for k, (p_, fb, ex, at, who, _) in enumerate(picks):
        W_, H_ = Image.open(p_).size
        pad_x, pad_y = (fb[2] - fb[0]) * 0.15, (fb[3] - fb[1]) * 0.1       # 머리카락·턱 둘레까지 조금 넉넉히
        box = [int(max(0, fb[0] - pad_x) * W_), int(max(0, fb[1] - pad_y) * H_), int(min(1, fb[2] + pad_x) * W_), int(min(1, fb[3] + pad_y) * H_)]
        fixes.append({"id": f"e{k}", "image": p_, "out": p_ + ".표정.jpg", "box": box, "seed": 7 + k,
                      "refs": [sheets[who]] if who in sheets else [],
                      "prompt": (f"Close-up of the same person's face, same face shape, same hair, beard, headwear and same ink wash painting style. "
                                 f"Change only the facial expression: {ex}. No text, no seal stamp.")})
    jp = os.path.join(os.path.dirname(proj), "_표정_job.json")
    json.dump({"items": [], "fixes": fixes}, open(jp, "w", encoding="utf-8"), ensure_ascii=False)
    log(f"🖌 표정 그림 {len(fixes)}장 그리는 중 (한 장 약 1분 20초)...")
    pr = subprocess.run([m.SD_PYTHON, "-X", "utf8", "-u", os.path.join(HERE, "klein_worker.py"), m.KLEIN_DIR, jp, os.path.join(media, "_sd")],
                        capture_output=True, text=True, encoding="utf-8", errors="replace")
    os.remove(jp)
    ok = {ln.split(" ")[1] for ln in pr.stdout.splitlines() if ln.startswith("OK ")}
    tiles = []
    for k, (p_, fb, ex, at, who, why) in enumerate(picks):
        if f"e{k}" not in ok:
            log(f"  실패: {os.path.basename(p_)}")
            continue
        json.dump({"image": p_ + ".표정.jpg", "at": at, "expr": ex, "who": who, "why": why}, open(p_ + ".표정.json", "w", encoding="utf-8"), ensure_ascii=False)
        tiles.append((p_, fixes[k]["box"]))
    # 확인용 (원래 얼굴 | 바뀐 얼굴)
    if tiles:
        sheet = Image.new("RGB", (2 * 420, len(tiles) * 420), "white")
        for i, (p_, bx) in enumerate(tiles):
            for j, src in enumerate((p_, p_ + ".표정.jpg")):
                im = Image.open(src).convert("RGB").crop(bx)
                im.thumbnail((410, 410))
                sheet.paste(im, (j * 420 + 5, i * 420 + 5))
        sheet.save(os.path.join(os.path.dirname(proj), "_표정_확인.png"))
    log(f"✅ 표정 바뀌기 {len(tiles)}장 · 확인용: _표정_확인.png")
    app.destroy()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
