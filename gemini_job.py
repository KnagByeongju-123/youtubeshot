"""Claude + Gemini 그림 작업 도우미 (Tk 없이 명령줄로)

프로그램의 「🤖 Claude 작업 만들기」가 output/그림작업/<제목>/작업.json 을 만들고, Claude 가 오른쪽 내장 브라우저로
Gemini 에서 한 장씩 그려 다운로드하면 이 도구로 모아서 프로젝트에 넣는다.

  py -3.11 -X utf8 gemini_job.py put   <작업폴더> <번호> [그림파일]   다운로드 폴더의 새 Gemini 그림(또는 지정 파일)을 <번호>.png 로 옮김
  py -3.11 -X utf8 gemini_job.py status <작업폴더>                     받은 번호·남은 번호
  py -3.11 -X utf8 gemini_job.py apply <작업폴더>                      받은 그림을 대본에 넣어 <제목>_Gemini.json 프로젝트로 저장
"""
import glob
import json
import os
import re
import shutil
import sys
import time

BASE = os.path.dirname(os.path.abspath(__file__))
DL = os.path.join(os.path.expanduser("~"), "Downloads")
MARK = re.compile(r"^\[사진:\s*([^|\]]+?)\s*(?:\|([^|\]]*))?(?:\|([^|\]]*))?(?:\|([^\]]*))?\]$")


def load(job_dir):
    return json.load(open(os.path.join(job_dir, "작업.json"), encoding="utf-8"))


def img_path(job_dir, n):
    return os.path.join(job_dir, f"{int(n):02d}.png")


def put(job_dir, n, src=None, wait=180):
    """새 그림을 <번호>.png 로. src 가 없으면 다운로드 폴더에 새로 생긴 Gemini 그림을 기다림(다 받아질 때까지)"""
    seen_f = os.path.join(job_dir, ".받은파일.txt")
    seen = set(open(seen_f, encoding="utf-8").read().splitlines()) if os.path.exists(seen_f) else set()
    t0 = time.time()
    while not src and time.time() - t0 < wait:
        cands = [p for p in glob.glob(os.path.join(DL, "Gemini_Generated_Image_*.*")) + glob.glob(os.path.join(DL, "ChatGPT Image*.png"))
                 if p not in seen and p.lower().endswith((".png", ".jpg", ".jpeg", ".webp"))]
        for p in sorted(cands, key=os.path.getmtime):
            s1 = os.path.getsize(p)
            time.sleep(1)
            if s1 > 10000 and os.path.getsize(p) == s1:
                src = p
                break
        if not src:
            time.sleep(1)
    if not src:
        print("NO FILE - 다운로드 폴더에 새 그림이 없어요 (저장 창에서 '저장'을 눌렀는지 확인)")
        return 1
    with open(seen_f, "a", encoding="utf-8") as f:
        f.write(src + "\n")
    shutil.move(src, img_path(job_dir, n)) if os.path.dirname(os.path.abspath(src)) == os.path.abspath(DL) else shutil.copy(src, img_path(job_dir, n))
    print(f"OK {int(n)} {os.path.getsize(img_path(job_dir, n)):,} bytes")
    return 0


def status(job_dir):
    j = load(job_dir)
    got = [s["n"] for s in j["slots"] if os.path.exists(img_path(job_dir, s["n"]))]
    left = [s["n"] for s in j["slots"] if s["n"] not in got]
    print(f"받음 {len(got)}/{len(j['slots'])}: {got}\n남음: {left}")
    return 0


def save_media(src, stem):
    from PIL import Image
    md = os.path.join(BASE, "output", "media")
    os.makedirs(md, exist_ok=True)
    im = Image.open(src).convert("RGB")
    im.thumbnail((1920, 1920))
    p = os.path.join(md, stem + ".jpg")
    im.save(p, quality=92)
    return os.path.relpath(p, BASE).replace("\\", "/")


def apply(job_dir):
    j = load(job_dir)
    proj = j["project"]
    paras = [x.strip() for x in re.split(r"\n\s*\n", (proj.get("story") or "").strip()) if x.strip()]
    who = j.get("target", "Gemini")
    done, stamp = 0, time.strftime("%Y%m%d_%H%M%S")
    # 뒤에서부터 넣어야 앞 번호가 밀리지 않음
    for s in sorted(j["slots"], key=lambda s: -(s.get("pi") if s.get("pi") is not None else 10 ** 6)):
        src = img_path(job_dir, s["n"])
        if not os.path.exists(src):
            continue
        rel = save_media(src, f"gemimg_{stamp}_{s['n']:02d}")
        cap = re.sub(r"[|\]\[]", " ", str(s.get("ko") or "장면"))[:40]
        marker = f"[사진: {rel} | {cap} | AI 생성 이미지 ({who}) | ]"
        if s.get("mode") == "replace" and s.get("pi") is not None and s["pi"] < len(paras) and MARK.match(paras[s["pi"]]):
            paras[s["pi"]] = marker
        else:
            try:
                k = paras.index(s["para"])
            except ValueError:
                print(f"  {s['n']}번: 문단을 찾지 못해 건너뜀")
                continue
            if k >= 1 and MARK.match(paras[k - 1]) and "AI 생성 이미지" in paras[k - 1]:
                paras[k - 1] = marker
            else:
                paras.insert(k, marker)
        done += 1
    proj["story"] = "\n\n".join(paras)
    out = os.path.join(job_dir, re.sub(r'[\\/:*?"<>|]', " ", proj.get("title") or "그림").strip()[:60].rstrip(" .") + f"_{who}.json")
    json.dump(proj, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"DONE 그림 {done}/{len(j['slots'])}장 넣음 → 프로젝트: {out}\n프로그램에서 「프로젝트 열기」로 이 파일을 여세요.")
    return 0


def main(a):
    if len(a) < 2 or a[0] not in ("put", "status", "apply"):
        print(__doc__)
        return 2
    d = os.path.abspath(a[1])
    if a[0] == "put":
        return put(d, a[2], a[3] if len(a) > 3 else None)
    return status(d) if a[0] == "status" else apply(d)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
