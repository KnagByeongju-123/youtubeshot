"""캐릭터 시트 모음 그리기 — 목록.json 의 인물·동물·귀신마다 시트(세 방향 전신, 흰 배경)를 klein 으로 그려 목록 폴더에 <name>.png
python 캐릭터시트_만들기.py <목록.json> [--스타일 "역사 수묵 담채"] [--이름 까치호랑이,도깨비] [--다시]
  - kind: person·spirit = 앞·옆·뒤 / animal = 옆·앞·뒤 (네 발 동물은 옆모습이 알아보기 쉬움)
  - 이미 있는 그림은 건너뜀 (--다시 면 새로). 한 장 약 2분 (AMX 서버)
  - 확인한 시트는 등장인물/등장인물.json 에 {name, look, look_ko, face} 로 등록하면 모든 편에서 같은 모습"""
import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
os.chdir(HERE)
import shorts_novel_maker_supertonic as m

a = sys.argv[1:]
lst = os.path.abspath(a[0])
style_name = a[a.index("--스타일") + 1] if "--스타일" in a else "역사 수묵 담채"
only = set(a[a.index("--이름") + 1].split(",")) if "--이름" in a else None
style = m.IMAGE_STYLES.get(style_name, style_name)
out_dir = os.path.dirname(lst)
VIEWS = {"animal": "side view, front view, back view, full body, standing on all its legs",
         "person": "front view, side view, back view, full body, standing",
         "spirit": "front view, side view, back view, full body, standing"}
jobs = []
for c in json.load(open(lst, encoding="utf-8"))["chars"]:
    dst = os.path.join(out_dir, m.safe_name(c["name"])[:40] + ".png")
    if (only and c["name"] not in only) or (os.path.exists(dst) and "--다시" not in a):
        continue
    kind = c.get("kind", "person")
    jobs.append({"id": f"s{len(jobs)}", "name": c["name"], "dst": dst, "width": 1024, "height": 576, "seed": 7,
                 "prompt": f"Character design sheet, {style}. The same {'animal' if kind == 'animal' else 'character'} shown three times side by side "
                           f"on a plain white background: {VIEWS.get(kind, VIEWS['person'])}. {'Animal' if kind == 'animal' else 'Character'}: {c['look']}. "
                           + ("Exactly four legs and one tail. " if kind == "animal" and "nine" not in c["look"] and "fish" not in c["look"] and "bird" not in c["look"] and "crane" not in c["look"] and "rooster" not in c["look"] and "dragon" not in c["look"] else "")
                           + ("Exactly two arms and two legs. " if kind != "animal" else "")
                           + "Consistent design in every view, no close-ups, no other people or animals, no text, no red seal stamp"})
print(f"그릴 시트 {len(jobs)}장: " + ", ".join(j["name"] for j in jobs), flush=True)
if jobs:
    got = m.sd_generate(jobs, os.path.join(out_dir, "_sd"), print, None)
    for j in jobs:
        if got.get(j["id"]):
            shutil.move(got[j["id"]], j["dst"])
            print("저장:", j["dst"], flush=True)
    shutil.rmtree(os.path.join(out_dir, "_sd"), ignore_errors=True)
