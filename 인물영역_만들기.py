"""인물 영역 만들기 — 그리는 효과(배경 먼저, 인물 나중)에 쓸 '인물 윤곽 마스크'를 그림마다 만듦

  python -X utf8 인물영역_만들기.py <프로젝트.json> [--다시]
  (서버에서는 xvfb-run -a 로 실행)

  1) 대본 AI(Claude)가 그림을 Read 로 열어 앞쪽 주요 인물의 상자를 딱 맞게 알려 줌 (6장씩)
  2) SAM(sam_worker.py, .sd_venv)이 상자 안 인물 윤곽을 땀
  3) 그림 옆에 <그림>.인물.png(흰색 = 인물) 와 <그림>.인물.json({"boxes", "area"}) 저장 → 영상 그릴 때 그리는 효과가 이것을 씀
     인물이 없거나 윤곽이 이상하면(너무 크거나 작음) 상자 없이 저장 → 그 그림은 배경 전체가 한 번에 그려짐
  4) 확인용 모음: <프로젝트 폴더>/_인물영역_확인_N.png (인물 밖은 어둡게) — 사람이 크게 열어 검수
  이미 만든 그림은 건너뜀 (--다시 면 모두 새로)
"""
import importlib.util
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)
T0 = time.time()

BOX_SYSTEM = """너는 영상 편집자다. 그림 파일을 Read 로 하나씩 직접 열어 보고, 그림에서 '앞쪽에 크게 나온 주요 인물'마다 상자를 정한다.
- 상자는 그 인물(머리끝·손끝·옷자락·발끝까지)에 딱 맞게, 여백은 그림 크기의 2% 이내. 다른 인물·기둥·말 같은 것이 상자에 많이 들어가지 않게
- 말을 탄 인물은 사람과 말을 한 상자로. 인물이 들고 있는 칼·창도 상자 안에
- 멀리 작게 나온 병사 무리·군중, 그림자처럼 흐린 사람은 배경이므로 넣지 않는다. 주요 인물은 최대 4명
- 사람이 없는 그림(풍경·건물·물건·지도)은 빈 목록
- 좌표는 그림 너비·높이에 대한 비율(0~1) [왼쪽, 위, 오른쪽, 아래]
반드시 JSON만 출력: {"images": [{"n": 1, "boxes": [[0.1, 0.05, 0.45, 1.0]]}]}"""


def log(x):
    print(f"[{time.strftime('%H:%M')} · {(time.time() - T0) / 60:5.1f}분] {x}", flush=True)


def main(a):
    if not a or not a[0].lower().endswith(".json"):
        print(__doc__)
        return 2
    proj = os.path.abspath(a[0])
    spec = importlib.util.spec_from_file_location("snm", os.path.join(HERE, "shorts_novel_maker_supertonic.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    c = json.load(open(proj, encoding="utf-8"))
    model = str(c.get("model") or m.DEFAULTS.get("model") or "")
    paths = []
    for line in str(c.get("story") or "").split("\n"):
        md = m.parse_media(line.strip())
        if md:
            p_ = m.resolve_media(md[0]) or md[0]
            if p_ not in paths and os.path.exists(p_):
                paths.append(p_)
    todo = [p_ for p_ in paths if "--다시" in a or not os.path.exists(p_ + ".인물.json")]
    log(f"그림 {len(paths)}장 중 인물 영역을 만들 그림 {len(todo)}장")
    boxes = {}
    for g0 in range(0, len(todo), 6):
        grp = todo[g0:g0 + 6]
        plist = "\n".join(f"그림 {k + 1}: {p_}" for k, p_ in enumerate(grp))
        for tries in range(2):
            try:
                d = m.ask_json(model, BOX_SYSTEM, f"[그림 {len(grp)}장 - Read 로 하나씩 열어 볼 것]\n{plist}", tools=["Read"])
                for r_ in d.get("images") or []:
                    k = int(r_.get("n", 0)) - 1
                    if 0 <= k < len(grp):
                        bx = []
                        for b in r_.get("boxes") or []:
                            try:
                                x0, y0, x1, y1 = [min(1.0, max(0.0, float(v))) for v in b]
                            except (TypeError, ValueError):
                                continue
                            if x1 - x0 > 0.03 and y1 - y0 > 0.05:
                                bx.append([x0, y0, x1, y1])
                        boxes[grp[k]] = bx[:4]
                break
            except Exception as e:
                log(f"  상자 묻기 실패({tries + 1}): {str(e)[:100]}")
        log(f"  상자 {min(len(todo), g0 + 6)}/{len(todo)}")
    job = {"items": [{"id": str(k), "image": p_, "boxes": boxes.get(p_) or [], "out": p_ + ".인물.png"}
                     for k, p_ in enumerate(todo)]}
    jp = os.path.join(os.path.dirname(proj), "_sam_job.json")
    json.dump(job, open(jp, "w", encoding="utf-8"), ensure_ascii=False)
    log("✂ SAM 으로 인물 윤곽 따는 중...")
    pr = subprocess.run([m.SD_PYTHON, "-X", "utf8", "-u", os.path.join(HERE, "sam_worker.py"), jp], capture_output=True, text=True, encoding="utf-8", errors="replace")
    area = {}
    for ln in pr.stdout.splitlines():
        if ln.startswith("OK "):
            _, iid, rest = ln.split(" ", 2)
            area[todo[int(iid)]] = float(rest.rsplit(" ", 1)[1])
        elif ln.startswith("ERR "):
            log("  " + ln[:150])
    os.remove(jp)
    n_ok = 0
    for p_ in todo:
        ar = area.get(p_)
        bx = boxes.get(p_) or []
        if ar is None or not bx or ar < 0.01 or ar > 0.8:      # 인물 없음·실패·이상한 윤곽 → 배경만 (한 번에 그려짐)
            bx, ar = [], 0.0
        else:
            n_ok += 1
        json.dump({"boxes": bx, "area": ar}, open(p_ + ".인물.json", "w", encoding="utf-8"))
    log(f"✅ 인물 영역 {n_ok}장 · 인물 없음(배경만) {len(todo) - n_ok}장")
    # 확인용 모음 (12장씩, 인물 밖은 어둡게)
    import numpy as np
    from PIL import Image, ImageDraw
    sheets = 0
    for g0 in range(0, len(paths), 12):
        sheet = Image.new("RGB", (3 * 640, 4 * 380), "white")
        for k, p_ in enumerate(paths[g0:g0 + 12]):
            im = np.asarray(Image.open(p_).convert("RGB").resize((640, 360))).astype(np.float32)
            info = json.load(open(p_ + ".인물.json", encoding="utf-8")) if os.path.exists(p_ + ".인물.json") else {}
            M = np.zeros((360, 640, 1), np.float32)
            if info.get("boxes") and os.path.exists(p_ + ".인물.png"):
                M = np.asarray(Image.open(p_ + ".인물.png").convert("L").resize((640, 360)), np.float32)[..., None] / 255
            out = Image.fromarray((im * (0.3 + 0.7 * M)).astype(np.uint8))
            ImageDraw.Draw(out).text((8, 6), f"{g0 + k + 1} {'PERSON' if info.get('boxes') else 'BG ONLY'}", fill=(255, 255, 0))
            sheet.paste(out, ((k % 3) * 640, (k // 3) * 380))
        sheets += 1
        sheet.save(os.path.join(os.path.dirname(proj), f"_인물영역_확인_{sheets}.png"))
    log(f"확인용 모음 {sheets}장: {os.path.dirname(proj)}/_인물영역_확인_N.png")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
