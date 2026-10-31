"""나레이션 + 배경음만 mp3 로 (그림·영상 없이) — 프로젝트.json 의 대본·설정 그대로
python 나레이션_배경음만.py <프로젝트.json> <결과.mp3> [--배경음배율 0.5]
  - --배경음배율 : 배경음(챕터 사이 한 소절 포함)만 이 배율로 (0.5 = 50% 작게). 나레이션 크기는 그대로
  - 나레이션은 output/tts_cache 의 녹음을 다시 씀 (없는 문단만 새로 녹음) → 나레이션_겹침검사.py --고치기 뒤에 다시 돌리면 그 문장만 새로
  - 배경음은 프로젝트 settings 의 bgm_style (전통악기면 챕터 제목 4.2초 동안 나레이션을 쉬고 한 소절), 말할 땐 음악을 줄임
  - 겹침 검사는 mp4 를 받으므로: ffmpeg -f lavfi -i color=black:s=320x180:r=5 -i <결과.mp3> -shortest <검사용.mp4>"""
import json
import numpy as np
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
os.chdir(HERE)
import shorts_novel_maker_supertonic as m

pj_path, out_mp3 = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
bgm_mul = float(sys.argv[sys.argv.index("--배경음배율") + 1]) if "--배경음배율" in sys.argv else 1.0
pj = json.load(open(pj_path, encoding="utf-8"))
app = m.App()
app.withdraw()
app.update()
s = app.get_settings()
s.update(pj.get("settings", {}))
s["narration"] = "on"
story, title = pj.get("story", ""), pj.get("title", "")
style = s.get("bgm_style")
if m.is_trad(style):
    s["chapter_hold"] = 4.2
print("배경음:", style, "| 성우:", s.get("narr_voice"))
narr = app.narration_for(story, s, print)
r = m.make_renderer(title, story, s, narr)
print("전체 길이", m.hms(r.duration))
wav = out_mp3[:-4] + ".wav"
if bgm_mul == 1.0:
    audio = m.build_audio(r, s, style)
else:      # 배경음만 따로 만들어(나레이션 크기 0, 말할 때 줄이기는 그대로) 배율을 곱한 뒤 나레이션을 얹음
    vol = max(0, float(s.get("narr_volume", 1.0)))
    audio = m.build_audio(r, dict(s, narr_volume=0), style) * bgm_mul
    for st, clip in getattr(r, "narr_at", []):
        i0 = int(st * m.SR)
        seg = clip[: max(0, len(audio) - i0)]
        audio[i0:i0 + len(seg)] += (seg[:, None] if seg.ndim == 1 else seg) * vol
    peak = float(np.abs(audio).max())
    if peak > 0.95:
        audio *= 0.95 / peak
    print(f"배경음 x{bgm_mul}")
m.write_wav(wav, audio)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", wav, "-b:a", "192k", out_mp3], check=True)
os.remove(wav)
print("OK", out_mp3)
