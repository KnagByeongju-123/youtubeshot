"""그림 간격 보강 — 영상에서 그림 한 장이 '최대' 초 이상 화면에 머무는 곳을 찾아 그림을 더 그려 넣음 (규칙: 그림 한 장은 5~10초)

  python -X utf8 그림_간격_보강.py <프로젝트.json> [--최대 10] [--최소 5] [--측정만]
  (화면 부품 때문에 서버에서는 xvfb-run -a 로 실행)

  1) 나레이션(이미 녹음한 캐시)으로 영상과 똑같이 시간을 재서, 그림마다 화면에 나오는 시간을 구함
     (그림이 여러 장 연달아 있으면 다음 그림까지의 시간을 나눠 차례로 보여줌 — 영상 그리는 쪽과 같은 규칙)
  2) '최대' 이상인 곳은 약 (최소+최대)/2 초마다 한 장이 되게 새 그림 자리를 더함: 되도록 문단 사이에, 문단 하나가 길면 그 문단 앞에 겹쳐
     (문단·나레이션은 그대로 → 다시 녹음 없음)
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


def map_segs(m, lines):
    """영상 그리는 쪽(make_renderer)과 같은 순서로 구간 번호 → 줄 번호, 그 구간 바로 앞에 연달아 놓인 그림 수"""
    seg_line, stack_n, n_seg, run_imgs = {}, {}, 0, 0
    for li, p in enumerate(lines):
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
    return seg_line, stack_n


def rebalance(m, r, lines, lo, lim):
    """그림이 너무 짧게(lo 미만) 지나가는 묶음(짧은 문단에 그림이 몰린 곳)의 그림을 앞·뒤 묶음으로 한 장씩 옮김 (순서는 그대로).
    반환: (새 줄 목록, 옮긴 수)"""
    seg_line, _ = map_segs(m, lines)
    line_dur = {}
    end_t = r.duration - r.he
    for k, li in seg_line.items():
        t1 = r.segs[k + 1]["t0"] if k + 1 < len(r.segs) else end_t
        line_dur[li] = t1 - r.segs[k]["t0"]
    blocks = [{"media": [], "body": []}]          # 그림 줄들 + 다음 그림 줄 전까지의 글
    for li, p in enumerate(lines):
        if m.parse_media(p):
            if blocks[-1]["body"] and any(x in line_dur for x in blocks[-1]["body"]):
                blocks.append({"media": [], "body": []})
            blocks[-1]["media"].append(li)
        else:
            blocks[-1]["body"].append(li)

    def span(b):
        return sum(line_dur.get(x, 0) for x in b["body"])

    def per(b, extra=0):
        n = len(b["media"]) + extra
        return span(b) / n if n else 1e9
    moved = 0
    for _ in range(3):
        for i, b in enumerate(blocks):
            while len(b["media"]) > 1 and per(b) < lo:
                prv = blocks[i - 1] if i > 0 and blocks[i - 1]["media"] else None
                nxt = blocks[i + 1] if i + 1 < len(blocks) else None
                opts = []
                if prv and per(prv, 1) >= lo:
                    opts.append((per(prv, 1), "prev"))
                if nxt and per(nxt, 1) >= lo:
                    opts.append((per(nxt, 1), "next"))
                if not opts:
                    break
                _, where = max(opts)          # 더 여유 있는 쪽으로
                if where == "prev":
                    prv["media"].append(b["media"].pop(0))
                else:
                    nxt["media"].insert(0, b["media"].pop())
                moved += 1
    out = []
    for b in blocks:
        out += [lines[x] for x in b["media"]] + [lines[x] for x in b["body"]]
    return out, moved


def main(a):
    if not a or not a[0].lower().endswith(".json"):
        print(__doc__)
        return 2
    lim = float(a[a.index("--최대") + 1]) if "--최대" in a else 10.0
    lo = float(a[a.index("--최소") + 1]) if "--최소" in a else 5.0
    T = (lo + lim) / 2                # 새로 나눌 때 목표 간격 (5~10초면 7.5초)
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
    short_ = [x for x in runs[1:-1] if x[2] - x[1] < lo]
    durs = sorted(x[2] - x[1] for x in runs)
    log(f"화면에 나오는 그림 {len(runs)}번 (그림 파일 {len(r.images)}장) · 가장 김 {durs[-1]:.1f}초 · 가장 짧음 {durs[0]:.1f}초 · 중간 {durs[len(durs) // 2]:.1f}초"
        f" · {lim:g}초 이상 {len(long_)}곳 · {lo:g}초 미만 {len(short_)}곳")
    for im_, t0, t1 in long_:
        log(f"   길다 {m.hms(t0)} 그림 {im_ + 1}: {t1 - t0:.1f}초")
    for im_, t0, t1 in short_:
        log(f"   짧다 {m.hms(t0)} 그림 {im_ + 1}: {t1 - t0:.1f}초")
    if "--측정만" in a or not (long_ or short_):
        app.destroy()
        return 0
    bak = proj[:-5] + "_보강전.json"
    if not os.path.exists(bak):
        shutil.copy(proj, bak)
    lines = [p.strip() for p in story.replace("\r", "").split("\n") if p.strip()]
    lines, n_mv = rebalance(m, r, lines, lo, lim)
    if n_mv:     # 몰려 있던 그림을 옮긴 뒤 다시 잼
        story = "\n\n".join(lines)
        r = m.make_renderer(title, story, s, app.narration_for(story, s, lambda x: None, gate))
        runs = shown_runs(r)
        log(f"몰린 그림 {n_mv}장을 앞뒤로 옮김 → {lim:g}초 이상 {sum(1 for x in runs if x[2] - x[1] >= lim)}곳 · "
            f"{lo:g}초 미만 {sum(1 for x in runs[1:-1] if x[2] - x[1] < lo)}곳")

    # ---- 문단(구간)마다 앞에 더할 그림 수: 영상과 같은 규칙으로 흉내 내며 L 을 넘는 곳에 ----
    seg_line, stack_n = map_segs(m, lines)
    assert len(seg_line) == len(r.segs), (len(seg_line), len(r.segs))
    # 그림 묶음: 그림 줄이 있는 문단부터 다음 그림 줄 문단 전까지 (영상과 같은 규칙)
    end_t = r.duration - r.he
    groups_t = []
    for k, sg in enumerate(r.segs):
        if k == 0 or stack_n[k]:
            groups_t.append([k, max(1, stack_n[k])])
    add = {}
    for g_i, (k0, n0) in enumerate(groups_t):
        k1 = groups_t[g_i + 1][0] if g_i + 1 < len(groups_t) else len(r.segs)
        t0 = r.segs[k0]["t0"]
        t1 = r.segs[k1]["t0"] if k1 < len(r.segs) else end_t
        span = t1 - t0
        if span / n0 < lim:
            continue
        N = max(n0, math.ceil(span / T))
        # 문단 사이 자리(장 제목·쉼 앞은 뺌) 중 이상적인 자르는 시각에 가까운 곳
        bounds = [k for k in range(k0 + 1, k1) if r.segs[k]["kind"] == "text"]
        cuts = []
        for i_ in range(1, N - n0 + 1):
            want = t0 + span * (n0 + i_ - 1) / N + span / N        # 원래 그림 n0 장이 앞쪽 n0/N 을 맡음
            b = min((k for k in bounds if k not in cuts), key=lambda k: abs(r.segs[k]["t0"] - want), default=None)
            if b is not None and abs(r.segs[b]["t0"] - want) < span / N / 2:
                cuts.append(b)
        cuts.sort()
        edges = [k0] + cuts + [k1]
        for e_i in range(len(edges) - 1):
            ka, kb = edges[e_i], edges[e_i + 1]
            ta = r.segs[ka]["t0"]
            tb = r.segs[kb]["t0"] if kb < len(r.segs) else end_t
            have = n0 if e_i == 0 else 0
            need = max(have, 1, round((tb - ta) / T))
            while (tb - ta) / need >= lim:
                need += 1
            if need > have:
                add[ka] = add.get(ka, 0) + need - have
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
    app.set_story("\n\n".join(new_lines))
    d_ = app.project_dict()
    d_["settings"] = {k: v for k, v in d_["settings"].items() if k not in m.SECRET_KEYS}
    m.atomic_write_text(proj, json.dumps(d_, ensure_ascii=False, indent=1))
    log(f"✅ 새 그림 {len(pics)}장을 넣어 프로젝트 저장 (원래 것: {os.path.basename(bak)})")
    app.destroy()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
