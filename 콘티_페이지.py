r"""장면 무빙 콘티 페이지 만들기 (사용자 결정 2026-11-08) — 장면마다 카메라 무빙·장면 전환을 드롭다운(직접 입력 포함)으로 고르는 웹 페이지(HTML)
사용: xvfb-run -a python -X utf8 콘티_페이지.py <프로젝트.json> <결과.html>
  번호 = 작은 영상 왼쪽 위 #번호 = 사진 점검표 번호. 자동 추천은 <제목>_카메라무빙.txt 에서 읽음 (영상을 한 번 만든 뒤에 만들면 추천이 보임)
  Claude 가 Artifact 로 올리고(capabilities db), 사용자가 고른 값은 ArtifactData 로 받아 콘티_반영.py 로 _카메라무빙.txt 에 반영 → 작은 영상
"""
import json, glob, re, io, base64, sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from PIL import Image
PJ, OUT = sys.argv[1], sys.argv[2]
D = os.path.dirname(os.path.abspath(PJ))
pj = json.load(open(PJ, encoding="utf-8"))
plan = {}
pf = [PJ[:-len("_프로젝트.json")] + "_카메라무빙.txt"] if os.path.exists(PJ[:-len("_프로젝트.json")] + "_카메라무빙.txt") else []
if pf:
    for ln in open(pf[0], encoding="utf-8").read().splitlines():
        p = [x.strip() for x in ln.split("|")]
        if len(p) >= 4 and p[0].isdigit():
            if len(p) >= 6:
                plan[int(p[0])] = {"move": p[1], "trans": p[2], "layer": p[3], "why": p[5]}
            elif len(p) >= 5:
                plan[int(p[0])] = {"move": p[1], "trans": p[2], "why": p[4]}
            else:
                plan[int(p[0])] = {"move": p[1], "trans": "자동:물감", "why": p[3]}
lines = [l.strip() for l in pj["story"].split("\n") if l.strip()]
scenes, pend = [], []
for l in lines:
    m = re.match(r"^\[사진\s*:\s*(.+?)\]\s*$", l)
    if m:
        parts = [x.strip() for x in m.group(1).split("|")]
        path = parts[0] if os.path.isabs(parts[0]) else os.path.join(HERE, parts[0])
        try:
            im = Image.open(path).convert("RGB")
        except Exception:
            continue
        w, h = im.size; tw, th = 192, 108
        s = max(tw / w, th / h); im = im.resize((max(tw, int(w * s) + 1), max(th, int(h * s) + 1)))
        l0, t0 = (im.width - tw) // 2, (im.height - th) // 2
        im = im.crop((l0, t0, l0 + tw, t0 + th)); b = io.BytesIO(); im.save(b, "JPEG", quality=62)
        n = len(scenes) + 1
        pl = plan.get(n, {})
        scenes.append({"n": n, "cap": parts[1] if len(parts) > 1 else "", "thumb": "data:image/jpeg;base64," + base64.b64encode(b.getvalue()).decode(),
                       "auto": pl.get("move", "-"), "autoTrans": pl.get("trans", "자동:물감"), "autoLayer": pl.get("layer", "-"), "why": pl.get("why", ""), "text": ""})
        pend.append(len(scenes) - 1)
        continue
    if l.startswith("#"):
        continue
    for i in pend:
        scenes[i]["text"] = l[:90]
    pend = []
import shorts_novel_maker_supertonic as m0
data = {"title": pj["title"], "moves": m0.CAMERA_MOVES, "trans": m0.SCENE_TRANSITIONS, "scenes": scenes}
tpl = open(os.path.join(HERE, "콘티_페이지_틀.html"), encoding="utf-8").read()
open(OUT, "w", encoding="utf-8").write(tpl.replace("__DATA__", json.dumps(data, ensure_ascii=False).replace("</", "<\\/")))
print(len(scenes), sum(len(s["thumb"]) for s in scenes) // 1024, "KB")
