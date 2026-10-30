"""그림 간격 보강 — 영상에서 그림 한 장이 '초' 이상 화면에 머무는 곳을 찾아 그림을 더 그려 넣음 (규칙: 그림 한 장은 8초 미만)

  python -X utf8 그림_간격_보강.py <프로젝트.json> [--초 8] [--측정만]
  (화면 부품 때문에 서버에서는 xvfb-run -a 로 실행)

  1) 나레이션(이미 녹음한 캐시)으로 영상과 똑같이 시간을 재서, 그림마다 화면에 나오는 시간을 구함
     (문단 앞에 그림이 여러 장 연달아 있으면 그 문단 시간을 나눠 차례로 보여줌 — 영상 그리는 쪽과 같은 규칙)
  2) '초'의 90% 를 넘는 곳마다 그 문단 바로 앞에 새 그림 자리를 더함 (문단·나레이션은 그대로 → 다시 녹음 없음)
  3) 새 자리마다 그 문단 글에 맞는 그림을 프로젝트의 그림 스타일로 그림 (챕터마다 한 번에, 결함 검사·다시 그리기 포함)
  4) 프로젝트 파일에 저장 (원래 파일은 _보강전.json 으로 남김) → render_project.py --대본그대로 --길이고정 --형식고정 으로 영상 다시
"""
import importlib.util
import json
import math
import os
import re
import shutil
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)
T0 = time.time()


def log(x):
    print(f"[{time.strftime('%H:%M')} · {(time.time() - T0) / 60:5.1f}분] {x}", flush=True)


def shown_runs(r):
    """그림이 바뀔 때마다 [(그림 번호, 시작, 끝)] (같은 그림이 이어지면 합침)"""
    out = []
    for im_, t0, t1 in r._img_pieces(r.duration - r.he):
        if out and out[-1][0] == im_:
            out[-1][2] = t1
        else:
            out.append([im_, t0, t1])
    return out


def main(a):
    if not a or not a[0].lower().endswith(".json"):
        print(__doc__)
        return 2
    lim = float(a[a.index("--초") + 1]) if "--초" in a else 8.0
    L = lim * 0.9                     # 여유 있게 (8초면 7.2초 안쪽)
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
    gate = m.PauseGate(os.path.join(HERE, "장문_일시정지중.flag"), app.cancel, log)
    narr = app.narration_for(story, s, lambda x: None, gate)
    r = m.make_renderer(title, story, s, narr)
    runs = shown_runs(r)
    long_ = [x for x in runs if x[2] - x[1] >= lim]
    durs = sorted(x[2] - x[1] for x in runs)
    log(f"화면에 나오는 그림 {len(runs)}번 (그림 파일 {len(r.images)}장) · 가장 김 {durs[-1]:.1f}초 · 중간 {durs[len(durs) // 2]:.1f}초 · {lim:g}초 이상 {len(long_)}곳")
    for im_, t0, t1 in long_:
        log(f"   {m.hms(t0)} 그림 {im_ + 1}: {t1 - t0:.1f}초")
    if "--측정만" in a or not long_:
        app.destroy()
        return 0

    # ---- 문단(구간)마다 앞에 더할 그림 수: 영상과 같은 규칙으로 흉내 내며 L 을 넘는 곳에 ----
    lines = [p.strip() for p in story.replace("\r", "").split("\n") if p.strip()]
    seg_line, stack_n, n_seg, run_imgs = {}, {}, 0, 0
    for li, p in enumerate(lines):     # 영상 그리는 쪽(make_renderer)과 같은 순서로 구간 번호 ↔ 줄 번호
        if m.parse_media(p):
            run_imgs += 1
            continue
        if m.SFX_RE.match(p) or m.PH_RE.match(p) or (not m.HOLD_RE.match(p) and not m.PH_INLINE_RE.sub("", p).strip()):
            continue
        if p.startswith("♪"):
            raise SystemExit("가사(♪) 문단이 있는 대본은 아직 지원하지 않음")
        seg_line[n_seg], stack_n[n_seg] = li, run_imgs
        run_imgs = 0
        n_seg += 1
    assert n_seg == len(r.segs), (n_seg, len(r.segs))
    add = {}
    acc = 0.0
    for k, sg in enumerate(r.segs):
        t1 = r.segs[k + 1]["t0"] if k + 1 < len(r.segs) else r.duration - r.he
        d = t1 - sg["t0"]
        s_k = stack_n[k] if k else max(1, stack_n[k])
        if sg["kind"] == "chapter" or sg["kind"] == "hold":     # 장 제목·쉼 앞에는 그림을 더하지 않음 (짧음)
            acc = d / s_k if s_k else acc + d
            continue
        if s_k:
            n_add = max(0, math.ceil(d / L) - s_k)
            acc = d / (s_k + n_add)
        elif acc + d < L:
            n_add, acc = 0, acc + d
        else:
            n_add = max(1, math.ceil(d / L))
            acc = d / n_add
        if n_add:
            add[k] = n_add
    n_new = sum(add.values())
    log(f"새 그림 {n_new}장 필요 (문단 {len(add)}곳)")

    # ---- 그리기: 챕터마다 한 번에 ----
    out_root = os.path.join(s["out_dir"], "장문")
    for d_ in [os.path.join(os.path.dirname(proj), n) for n in os.listdir(os.path.dirname(proj)) if n.startswith("_작업_")]:
        p_ = os.path.join(d_, "대본.json")
        if os.path.exists(p_) and json.load(open(p_, encoding="utf-8")).get("title") == title:
            m.IMAGE_CAST["chars"] = list(json.load(open(p_, encoding="utf-8")).get("cast") or [])
    media = os.path.join(out_root, "media")
    for ch in m.IMAGE_CAST.get("chars") or []:     # 이미 그린 캐릭터 시트를 그대로 (같은 얼굴·옷)
        sh = os.path.join(media, "_cast", m.safe_name(ch.get("name", ""))[:40] + ".png")
        if os.path.exists(sh):
            ch["sheet"] = sh
    log(f"등장인물 {len(m.IMAGE_CAST.get('chars') or [])}명 (캐릭터 시트 {sum(1 for c_ in m.IMAGE_CAST.get('chars') or [] if c_.get('sheet'))}장)")
    m.SCRIPT_ENGINE["s"] = s
    draw_s = dict(s, fiction_image="로컬 그림 생성(무료 · 이 PC · 느림)")
    if "--스타일" in a:
        draw_s["image_style_preset"] = m.IMG_SOURCE_PRESET.get(a[a.index("--스타일") + 1], a[a.index("--스타일") + 1])
    log(f"그림 스타일: {draw_s.get('image_style_preset')}")
    model = app.model_var.get().strip()
    chap_of, chap = {}, "오프닝"
    for li, p in enumerate(lines):
        if p.startswith("## "):
            chap = p[3:].strip()
        chap_of[li] = chap
    slots = []        # (구간 번호, 그 문단 안 몇 번째 새 그림, 모두 몇 장)
    for k in sorted(add):
        for j in range(add[k]):
            slots.append((k, j, add[k]))
    groups = []
    for sl in slots:
        ch = chap_of[seg_line[sl[0]]]
        if not groups or groups[-1][0] != ch:
            groups.append((ch, []))
        groups[-1][1].append(sl)
    pics = {}
    for ch, sls in groups:
        text = "\n\n".join(f"[그림 {n + 1}번] " + (f"(이 문단 그림 {tot}장 중 {j + 1}번째 → 문단의 {'앞' if j == 0 and tot > 1 else '뒤' if j == tot - 1 and tot > 1 else ''} 부분 장면) " if tot > 1 else "")
                           + lines[seg_line[k]] for n, (k, j, tot) in enumerate(sls))
        log(f"🖌 '{ch}' 새 그림 {len(sls)}장")
        got = m.make_ai_images(model, m.DOC_CATEGORY, f"{title} - {ch}",
                               f"아래 [그림 N번] 마다 그림 한 장씩, 번호 순서대로 모두 {len(sls)}장. 각 그림은 그 번호 뒤 글의 장면:\n\n" + text,
                               len(sls), draw_s, media, log, gate)
        for n, sl in enumerate(sls):
            if n < len(got):
                pics[sl] = got[n]
        log(f"   {len(got)}/{len(sls)}장 완성")
    new_lines = []
    for li, p in enumerate(lines):
        k = next((k_ for k_, l_ in seg_line.items() if l_ == li), None)
        if k is not None and k in add:
            for j in range(add[k]):
                ph = pics.get((k, j, add[k]))
                if ph:
                    new_lines.append(m.make_marker(ph["path"], ph.get("caption"), ph.get("credit"), ph.get("page")))
        new_lines.append(p)
    bak = proj[:-5] + "_보강전.json"
    if not os.path.exists(bak):
        shutil.copy(proj, bak)
    app.set_story("\n\n".join(new_lines))
    d_ = app.project_dict()
    d_["settings"] = {k: v for k, v in d_["settings"].items() if k not in m.SECRET_KEYS}
    m.atomic_write_text(proj, json.dumps(d_, ensure_ascii=False, indent=1))
    log(f"✅ 새 그림 {len(pics)}장을 넣어 프로젝트 저장 (원래 것: {os.path.basename(bak)})")
    app.destroy()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
