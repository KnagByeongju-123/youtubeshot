"""그림 간격 맞추기 — 그림 한 장이 화면에 '최소'~'최대' 초 머물게 그림 자리를 다시 짜고, 모자란 자리는 새로 그림
(규칙: 그림 한 장 5~15초 — 나레이션 동안 그림이 그려지는 효과로 볼거리를 줌, 사용자 결정 2026-10-30)

  python -X utf8 그림_간격_보강.py <프로젝트.json> [--최소 5] [--최대 15] [--측정만 | --계획만]
  (화면 부품 때문에 서버에서는 xvfb-run -a 로 실행)

  1) 나레이션(이미 녹음한 캐시)으로 영상과 똑같이 시간을 재서 그림마다 화면에 나오는 시간을 구함
  2) 그림 자리를 새로 정함: 문단 사이에서 (최소+최대)/2 초에 가까운 곳마다 한 장. 문단 하나가 '최대'보다 길면 그 문단 앞에
     그림을 여러 장 겹쳐 놓아 문단 시간을 나눠 보여줌 (영상 그리는 쪽 규칙). 문단·나레이션은 그대로 → 다시 녹음 없음
  3) 이미 그린 그림을 원래 나오던 시각에 가까운 자리에 순서 그대로 다시 배치 (남는 그림은 빼고 목록만 남김)
  4) 맞는 그림이 없는 자리만 그 부분 글에 맞춰 새로 그림 (챕터마다 한 번에, 결함 검사·다시 그리기 포함)
  5) 프로젝트 파일에 저장 (처음 파일은 _보강전.json 으로 남김) → render_project.py <프로젝트.json> --대본그대로 --길이고정 --형식고정
"""
import importlib.util
import json
import os
import shutil
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)
T0 = time.time()
NEW_COST = float(next((sys.argv[i + 1] for i, x in enumerate(sys.argv[:-1]) if x == "--옮김"), 15.0))      # 새로 그리는 대신 이미 그린 그림을 이 초보다 멀리 옮기지는 않음 (내용이 어긋나지 않게)


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


def map_segs(m, lines):
    """영상 그리는 쪽(make_renderer)과 같은 순서로 구간 번호 → 줄 번호"""
    seg_line, n_seg = {}, 0
    for li, p in enumerate(lines):
        if m.parse_media(p):
            continue
        if m.SFX_RE.match(p) or m.PH_RE.match(p) or (not m.HOLD_RE.match(p) and not m.PH_INLINE_RE.sub("", p).strip()):
            continue
        if p.startswith("♪"):
            raise SystemExit("가사(♪) 문단이 있는 대본은 아직 지원하지 않음")
        seg_line[n_seg] = li
        n_seg += 1
    return seg_line


def make_slots(r, lo, hi, end_t):
    """그림 자리 [(구간 번호, 시작, 끝)]: 문단 사이에서 목표 간격에 가까운 곳, 긴 문단은 같은 구간 번호로 여러 자리(겹침)"""
    T = (lo + hi) / 2
    starts = [(k, sg["t0"]) for k, sg in enumerate(r.segs) if sg["kind"] in ("text", "chapter")]
    slots, k_cur, t_cur = [], 0, r.segs[0]["t0"]
    while True:
        cand = [(k, t) for k, t in starts if t_cur + lo <= t <= t_cur + hi and k > k_cur]
        if cand:
            k, t = min(cand, key=lambda x: abs(x[1] - (t_cur + T)))
            slots.append((k_cur, t_cur, t))
            k_cur, t_cur = k, t
            continue
        nxt = next(((k, t) for k, t in starts if t > t_cur + hi and k > k_cur), None)
        t_end = nxt[1] if nxt else end_t
        span = t_end - t_cur
        if not nxt and span < lo and slots:            # 끝에 짧게 남으면 앞 자리에 붙임
            k0, a0, _ = slots[-1]
            slots[-1] = (k0, a0, end_t)
            break
        # 장 수: 범위(lo~hi)에서 가장 덜 벗어나는 수 (예: 19초 문단 → 1장 19초보다 2장 9.6초)
        n = min(range(1, max(2, int(span / lo) + 2)), key=lambda n_: (max(0, lo - span / n_) + max(0, span / n_ - hi), abs(span / n_ - T)))
        for j in range(n):
            slots.append((k_cur, t_cur + span * j / n, t_cur + span * (j + 1) / n))
        if not nxt:
            break
        k_cur, t_cur = nxt
    return slots


def assign(slots, img_t):
    """자리마다 이미 그린 그림을 순서를 지키며 배정 (시각 차이 합이 가장 작게, 너무 멀면 '새로 그림'=None)"""
    N, M = len(slots), len(img_t)
    INF = float("inf")
    D = [[INF] * (M + 1) for _ in range(N + 1)]
    B = [[None] * (M + 1) for _ in range(N + 1)]
    for j in range(M + 1):
        D[0][j] = 0.0
    for i in range(1, N + 1):
        mid = (slots[i - 1][1] + slots[i - 1][2]) / 2
        for j in range(M + 1):
            best, how = D[i - 1][j] + NEW_COST, ("new", j)          # 이 자리는 새로 그림
            if j and D[i][j - 1] < best:                             # 그림 j 는 버림
                best, how = D[i][j - 1], ("skip", j - 1)
            if j:
                c = D[i - 1][j - 1] + abs(img_t[j - 1] - mid)
                if c < best and abs(img_t[j - 1] - mid) < NEW_COST:
                    best, how = c, ("use", j - 1)
            D[i][j], B[i][j] = best, how
    out, i, j = [None] * N, N, M
    while i > 0:
        kind, jj = B[i][j]
        if kind == "use":
            out[i - 1] = jj
            i, j = i - 1, jj
        elif kind == "new":
            i -= 1
        else:
            j = jj
    return out


def main(a):
    if not a or not a[0].lower().endswith(".json"):
        print(__doc__)
        return 2
    hi = float(a[a.index("--최대") + 1]) if "--최대" in a else 15.0   # 사용자 결정 2026-10-31: 15초까지 괜찮음
    lo = float(a[a.index("--최소") + 1]) if "--최소" in a else 5.0
    proj = os.path.abspath(a[0])
    spec = importlib.util.spec_from_file_location("snm", os.path.join(HERE, "shorts_novel_maker_supertonic.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    app = m.App()
    app.withdraw()
    c = json.load(open(proj, encoding="utf-8"))
    cur = app.get_settings()
    st = dict(c.get("settings") or {})
    orig_st = dict(st)                      # 저장할 때 그대로 되돌릴 프로젝트 설정 (fps·위 제목 등이 프로그램 기본값으로 바뀌지 않게)
    for k in m.KEEP_KEYS:
        if not str(st.get(k, "")).strip() or k in m.SECRET_KEYS:
            st[k] = cur.get(k, m.DEFAULTS.get(k, ""))
    c["settings"] = st
    app.apply_cfg(c)
    app.update()                               # 자막 스타일·색 묶음이 늦게(after_idle) 적용되는 것을 먼저 끝냄
    for k_, v_ in orig_st.items():             # 프로젝트에 적힌 값이 이김 (자막 스타일 묶음이 기본값으로 되돌리지 않게)
        if k_ in app.vars and k_ not in ("format", "style_preset", "color_preset") and k_ not in m.SECRET_KEYS and k_ not in m.KEEP_KEYS:
            app.vars[k_].set(str(v_))      # 묶음 이름은 다시 쓰지 않음 (쓰면 묶음이 또 적용돼 위 제목 등이 되돌아감)
    app.update()
    app.update()
    s = app.get_settings()
    m.set_tts_cfg(s)
    title, story = app.title_var.get().strip(), app.get_story()
    gate = m.PauseGate(os.path.join(HERE, "장문_일시정지중.flag"), app.cancel, log)
    narr = app.narration_for(story, s, lambda x: None, gate)
    r = m.make_renderer(title, story, s, narr)
    end_t = r.duration - r.he
    runs = shown_runs(r)
    long_ = [x for x in runs if x[2] - x[1] > hi]
    short_ = [x for x in runs if x[2] - x[1] < lo]
    durs = sorted(x[2] - x[1] for x in runs)
    if durs:
        log(f"화면에 나오는 그림 {len(runs)}번 (그림 파일 {len(r.images)}장) · 가장 김 {durs[-1]:.1f}초 · 가장 짧음 {durs[0]:.1f}초 · 중간 {durs[len(durs) // 2]:.1f}초"
            f" · {hi:g}초 넘음 {len(long_)}곳 · {lo:g}초 미만 {len(short_)}곳")
    else:                                   # 나레이션 먼저 만든 대본(그림 없음): 문단 시간에 맞춰 모든 자리를 새로 그림
        log("그림이 아직 없음 → 나레이션 문단 시간에 맞춰 모든 그림 자리를 새로 그림")
    if "--측정만" in a or not (long_ or short_ or not durs):
        for im_, t0, t1 in long_ + short_:
            log(f"   {m.hms(t0)} 그림 {im_ + 1}: {t1 - t0:.1f}초")
        app.destroy()
        return 0

    lines = [p.strip() for p in story.replace("\r", "").split("\n") if p.strip()]
    seg_line = map_segs(m, lines)
    assert len(seg_line) == len(r.segs), (len(seg_line), len(r.segs))
    media_lines = [p for p in lines if m.parse_media(p)]
    pieces = r._img_pieces(end_t)                 # 그림 순서 = 그림 줄 순서
    img_t = [(p_[1] + p_[2]) / 2 for p_ in pieces]
    if len(img_t) != len(media_lines):
        raise SystemExit(f"그림 줄 {len(media_lines)}개와 화면 그림 {len(img_t)}개가 달라 멈춤 (불러오지 못한 그림이 있음)")
    slots = make_slots(r, lo, hi, end_t)
    pick = assign(slots, img_t)
    used = {j for j in pick if j is not None}
    n_new = sum(1 for j in pick if j is None)
    sd = sorted(b - a_ for _, a_, b in slots)
    log(f"새 그림 자리 {len(slots)}개 (한 장 {sd[0]:.1f}~{sd[-1]:.1f}초) · 이미 그린 그림 {len(used)}장 다시 씀 · "
        f"빼는 그림 {len(media_lines) - len(used)}장 · 새로 그릴 그림 {n_new}장")
    if "--계획만" in a:
        app.destroy()
        return 0

    # ---- 새로 그리기: 챕터마다 한 번에, 자리마다 그 시간 동안 읽는 글에 맞춰 ----
    for d_ in [os.path.join(os.path.dirname(proj), n) for n in os.listdir(os.path.dirname(proj)) if n.startswith("_작업_")]:
        p_ = os.path.join(d_, "대본.json")
        if os.path.exists(p_):
            m.IMAGE_CAST["chars"] = list(json.load(open(p_, encoding="utf-8")).get("cast") or [])
    media = os.path.join(s["out_dir"], "장문", "media")
    for ch in m.IMAGE_CAST.get("chars") or []:     # 이미 그린 캐릭터 시트를 그대로 (같은 얼굴·옷)
        sh = os.path.join(media, "_cast", m.safe_name(ch.get("name", ""))[:40] + ".png")
        if os.path.exists(sh):
            ch["sheet"] = sh
    m.SCRIPT_ENGINE["s"] = s
    draw_s = dict(s, fiction_image="로컬 그림 생성(무료 · 이 PC · 느림)")
    want = a[a.index("--스타일") + 1] if "--스타일" in a else str(c.get("img_source") or "")
    if want not in m.IMG_SOURCE_PRESET and str(c.get("genre") or "").startswith("[실화] 기록으로 보는 진짜 역사"):   # 예전 역사 편: 프로젝트에 스타일 기록이 없음
        try:
            want = json.load(open(os.path.join(HERE, "장문_설정.json"), encoding="utf-8")).get("역사_이미지") or ""
        except Exception:
            want = ""
        want = want or "그림: 역사 수묵 담채"
    if want:
        draw_s["image_style_preset"] = m.IMG_SOURCE_PRESET.get(want, want)
    log(f"그림 스타일: {draw_s.get('image_style_preset')} · 등장인물 {len(m.IMAGE_CAST.get('chars') or [])}명")
    model = app.model_var.get().strip()

    def text_during(t0, t1):
        return " ".join(sg["text"] for sg in r.segs if sg["kind"] == "text" and sg["t0"] < t1 - 0.5 and
                        (r.segs[r.segs.index(sg) + 1]["t0"] if r.segs.index(sg) + 1 < len(r.segs) else end_t) > t0 + 0.5)

    def chap_at(k):
        name = "오프닝"
        for kk in range(k + 1):
            if r.segs[kk]["kind"] == "chapter":
                name = r.segs[kk]["text"]
        return name
    groups = []
    for i, j in enumerate(pick):
        if j is None:
            ch = chap_at(slots[i][0])
            if not groups or groups[-1][0] != ch:
                groups.append((ch, []))
            groups[-1][1].append(i)
    new_pic = {}
    for ch, ids in groups:
        text = "\n\n".join(f"[그림 {n + 1}번] {text_during(slots[i][1], slots[i][2])}" for n, i in enumerate(ids))
        log(f"🖌 '{ch}' 새 그림 {len(ids)}장")
        got = m.make_ai_images(model, m.DOC_CATEGORY, f"{title} - {ch}",
                               f"아래 [그림 N번] 마다 그림 한 장씩, 번호 순서대로 모두 {len(ids)}장. 각 그림은 그 번호 뒤 글(그 그림이 나오는 동안 읽는 나레이션)의 장면:\n\n" + text,
                               len(ids), draw_s, media, log, gate)
        for n, i in enumerate(ids):
            if n < len(got):
                new_pic[i] = m.make_marker(got[n]["path"], got[n].get("caption"), got[n].get("credit"), got[n].get("page"))
        log(f"   {len(got)}/{len(ids)}장 완성")

    # ---- 새 대본: 그림 줄을 모두 빼고 자리마다 다시 넣음 ----
    before = {}
    for i, (k, _, _) in enumerate(slots):
        ln = media_lines[pick[i]] if pick[i] is not None else new_pic.get(i)
        if ln:
            before.setdefault(seg_line[k], []).append(ln)
    out = []
    for li, p in enumerate(lines):
        if m.parse_media(p):
            continue
        out += before.get(li, [])
        out.append(p)
    dropped = [media_lines[j] for j in range(len(media_lines)) if j not in used]
    bak = proj[:-5] + "_보강전.json"
    if not os.path.exists(bak):
        shutil.copy(proj, bak)
    if dropped:
        m.atomic_write_text(proj[:-5] + "_뺀그림.txt", "\n".join(dropped))
    app.set_story("\n\n".join(out))
    d_ = app.project_dict()
    d_["settings"] = {k: v for k, v in dict(d_["settings"], **orig_st).items() if k not in m.SECRET_KEYS}
    m.atomic_write_text(proj, json.dumps(d_, ensure_ascii=False, indent=1))
    log(f"✅ 그림 자리 {len(slots)}개로 저장 (새 그림 {len(new_pic)}장, 뺀 그림 {len(dropped)}장 → _뺀그림.txt) · 처음 것: {os.path.basename(bak)}")
    app.destroy()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
