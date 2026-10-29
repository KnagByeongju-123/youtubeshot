"""회차 .py 의 마당 제목마다 영상 속 시작 시각 — 업로드 글 차례용 (render_project 와 같은 나레이션 캐시로 계산)
xvfb-run -a .supertonic_venv/bin/python -X utf8 차례_시각.py <프로젝트.json> <회차.py>"""
import sys, os, json, runpy, importlib.util
os.chdir("/home/user/youtubeshot"); sys.path.insert(0, "/home/user/youtubeshot")
proj, epy = sys.argv[1], sys.argv[2]
sys.argv = ["x"]
g = runpy.run_path(epy, run_name="lib")
spec = importlib.util.spec_from_file_location("snm", "shorts_novel_maker_supertonic.py"); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
app = m.App(); app.withdraw()
c = json.load(open(proj, encoding="utf-8")); app.apply_cfg(c)
m.set_dialog_voices(c.get("dialogue") or [], c.get("cast") or [])
s = app.get_settings(); story = app.get_story()
m._YP.vary_settings(s, app.title_var.get().strip(), lambda *a: None)
story, _ = m.polite_fix("", story, lambda *a: None, None)
m.set_tts_cfg(s)
narr = app.narration_for(story, s, lambda *a: None, None)
r = m.make_renderer(app.title_var.get().strip(), story, s, narr)
paras = [x for x in g["STORY_TXT"].split("\n\n") if x.strip()]
heads = [(k, p[3:].strip()) for k, p in enumerate(paras) if p.startswith("## ")]
for k, h in heads:
    first = paras[k + 1].strip()[:20]
    t = next((sg["t0"] for sg in r.segs if sg.get("kind") == "text" and sg["text"].strip().startswith(first)), None)
    if t is not None:
        t = 0 if k == 0 else t
        print(f"{int(t // 60)}:{int(t % 60):02d} {h}")
print("총", round(r.duration / 60, 2), "분")
