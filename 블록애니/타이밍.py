"""블록 애니: 프로젝트.json 의 나레이션을 녹음하고(캐시 재사용) 문단(장면)마다 시작·끝 시각을 json 으로 저장 + 나레이션·배경음 mp3
python 블록애니/타이밍.py <프로젝트.json> <타이밍.json> [<소리.mp3>]"""
import json, os, sys, subprocess
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE); os.chdir(HERE)
import shorts_novel_maker_supertonic as m
pj = json.load(open(sys.argv[1], encoding="utf-8"))
app = m.App(); app.withdraw(); app.update()
s = app.get_settings(); s.update(pj.get("settings", {})); s["narration"] = "on"
m.set_tts_cfg(s)
narr = app.narration_for(pj["story"], s, print)
r = m.make_renderer(pj["title"], pj["story"], s, narr)
shots = [dict(img=os.path.basename(r.images[sh["img"]][1]) if len(r.images[sh["img"]]) > 1 else sh["img"], i=sh["img"], t0=round(sh["t0"], 3), t1=round(sh["t1"], 3)) for sh in r.shots]
json.dump(dict(duration=r.duration, shots=shots, intro=getattr(r, "intro", 0)), open(sys.argv[2], "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("길이", m.hms(r.duration), "장면", len(shots))
if len(sys.argv) > 3:
    wav = sys.argv[3][:-4] + ".wav"
    m.write_wav(wav, m.build_audio(r, s, s.get("bgm_style")))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", wav, "-b:a", "192k", sys.argv[3]], check=True); os.remove(wav)
