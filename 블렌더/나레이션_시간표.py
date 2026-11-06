"""블록 영상용: 프로젝트.json 의 나레이션(+배경음)을 wav 로 만들고, 문단마다 시작·끝 시간을 json 으로 (블록영상.md)
python -X utf8 블렌더/나레이션_시간표.py <프로젝트.json> <결과 폴더>  →  <폴더>/소리.wav, <폴더>/시간표.json
(나레이션은 output/tts_cache 의 녹음을 다시 씀 → 나레이션_배경음만.py 로 녹음·검사를 먼저 끝낸 뒤에 실행)"""
import json
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
os.chdir(HERE)
import shorts_novel_maker_supertonic as m  # noqa: E402

pj_path, out = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
os.makedirs(out, exist_ok=True)
pj = json.load(open(pj_path, encoding="utf-8"))
app = m.App()
app.withdraw()
app.update()
s = app.get_settings()
s.update(pj.get("settings", {}))
s["narration"] = "on"
story, title = pj.get("story", ""), pj.get("title", "")
m.set_tts_cfg(s)
narr = app.narration_for(story, s, print)
r = m.make_renderer(title, story, s, narr)
audio = m.build_audio(r, s, s.get("bgm_style"))
m.write_wav(os.path.join(out, "소리.wav"), audio)
segs = [{"kind": sg["kind"], "t0": round(sg["t0"], 3), "t1": round(sg["t0"] + sg["dur"], 3), "text": sg["text"]} for sg in r.segs]
json.dump({"duration": round(r.duration, 3), "segs": segs}, open(os.path.join(out, "시간표.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("길이", m.hms(r.duration), "· 문단", len(segs))
