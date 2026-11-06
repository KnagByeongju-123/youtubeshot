"""분위기 구간별 배경음 — 장면(그림)마다 곡을 바꿔 이어 붙인 배경음 한 개를 만들어 프로젝트에 넣음 (사용자 결정 2026-11-06: 배경음은 그때그때 분위기 따라)
  xvfb-run -a python -X utf8 배경음_구간.py <프로젝트.json> <결과.mp3> <구간표.json> [--저장]
  구간표.json: [{"from": "c01", "곡": "<mp3 경로>", "이름": "평온"}, {"from": "c09", ...}, ...]
    from = 그 구간이 시작하는 그림 파일 이름(확장자 없이). 첫 구간은 영상 처음부터
  - 나레이션 시간을 영상과 똑같이 재서(그림_간격_보강 과 같은 방법) 그림이 처음 나오는 시각에서 곡을 바꿈
  - 곡이 구간보다 짧으면 반복, 구간 사이는 3초 겹쳐 바꿈(크로스페이드), 곡마다 크기를 고르게(loudnorm)
  - --저장 : 프로젝트 settings 에 bgm_mode 파일, bgm_path 결과.mp3 를 적음 (render_project 가 그대로 씀)"""
import importlib.util
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
XF = 3.0


def times(proj):
    sys.argv = [sys.argv[0]]
    spec = importlib.util.spec_from_file_location("gap", os.path.join(HERE, "그림_간격_보강.py"))
    g = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(g)
    m = g.importlib.util.module_from_spec(g.importlib.util.spec_from_file_location("snm", os.path.join(HERE, "shorts_novel_maker_supertonic.py")))
    m.__spec__.loader.exec_module(m)
    app = m.App()
    app.withdraw()
    c = json.load(open(proj, encoding="utf-8"))
    cur = app.get_settings()
    st = dict(c.get("settings") or {})
    orig = dict(st)
    for k in m.KEEP_KEYS:
        if not str(st.get(k, "")).strip() or k in m.SECRET_KEYS:
            st[k] = cur.get(k, m.DEFAULTS.get(k, ""))
    c["settings"] = st
    app.apply_cfg(c)
    app.update()
    for k_, v_ in orig.items():
        if k_ in app.vars and k_ not in ("format", "style_preset", "color_preset") and k_ not in m.SECRET_KEYS and k_ not in m.KEEP_KEYS:
            app.vars[k_].set(str(v_))
    app.update()
    s = app.get_settings()
    m.set_tts_cfg(s)
    story = app.get_story()
    gate = m.PauseGate(os.path.join(HERE, "장문_일시정지중.flag"), app.cancel, print)
    narr = app.narration_for(story, s, lambda x: None, gate)
    r = m.make_renderer(app.title_var.get().strip(), story, s, narr)
    first = {}
    for im_, t0, _ in g.shown_runs(r):
        name = os.path.splitext(os.path.basename(r.img_paths[im_]))[0]
        first.setdefault(name, t0)
    total = r.duration
    app.destroy()
    return first, total


def main(a):
    if len(a) < 3:
        print(__doc__)
        return 2
    proj, out, table = os.path.abspath(a[0]), os.path.abspath(a[1]), json.load(open(a[2], encoding="utf-8"))
    first, total = times(proj)
    starts = [0.0] + [first[sec["from"]] for sec in table[1:]]
    ends = starts[1:] + [total]
    tmp = out + "_구간"
    os.makedirs(tmp, exist_ok=True)
    parts = []
    for k, (sec, t0, t1) in enumerate(zip(table, starts, ends)):
        length = t1 - t0 + (XF if k < len(table) - 1 else 0)
        p = os.path.join(tmp, f"{k:02d}.wav")
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-stream_loop", "-1", "-i", sec["곡"], "-t", f"{length:.2f}",
                        "-af", f"loudnorm=I=-20:TP=-2:LRA=11,afade=t=in:d=1.5,afade=t=out:st={max(0, length - 2):.2f}:d=2",
                        "-ar", "44100", "-ac", "2", p], check=True)
        parts.append(p)
        print(f"{sec.get('이름', k)}\t{int(t0 // 60)}:{t0 % 60:04.1f} ~ {int(t1 // 60)}:{t1 % 60:04.1f}\t{os.path.basename(sec['곡'])}", flush=True)
    cmd = ["ffmpeg", "-y", "-v", "error"]
    for p in parts:
        cmd += ["-i", p]
    if len(parts) == 1:
        flt, last = "[0:a]anull[o]", "[o]"
    else:
        flt, last = "", "[0:a]"
        for k in range(1, len(parts)):
            flt += f"{last}[{k}:a]acrossfade=d={XF}:c1=tri:c2=tri[x{k}];"
            last = f"[x{k}]"
        flt = flt.rstrip(";")
    cmd += ["-filter_complex", flt, "-map", last, "-c:a", "libmp3lame", "-b:a", "192k", out]
    subprocess.run(cmd, check=True)
    print("OK", out, f"{total:.1f}초")
    if "--저장" in a:
        c = json.load(open(proj, encoding="utf-8"))
        c["settings"]["bgm_mode"] = "파일"
        c["settings"]["bgm_path"] = out
        json.dump(c, open(proj, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("프로젝트에 저장", proj)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
