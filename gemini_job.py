"""Claude + Gemini 그림 작업 도우미 (Tk 없이 명령줄로)

프로그램의 「🤖 Claude 작업 만들기」가 output/그림작업/<제목>/작업.json 을 만들고, Claude 가 오른쪽 내장 브라우저로
Gemini 에서 한 장씩 그려 다운로드하면 이 도구로 모아서 프로젝트에 넣는다.

  py -3.11 -X utf8 gemini_job.py new   <프로젝트.json> [--target Gemini|ChatGPT] [--style "화풍 설명"] [--every 45] [--replace]
                                                                     대본에서 그림 자리(나레이션 약 every 초마다, 사진이 있으면 그 자리)를 골라 작업 폴더를 만듦 → 'JOB <폴더>'
                                                                     각 slot 의 prompt 는 비어 있음 → Claude 가 para(그림 바로 뒤 문단)를 보고 채워 작업.json 에 저장
  py -3.11 -X utf8 gemini_job.py put   <작업폴더> <번호> [그림파일]   다운로드 폴더의 새 Gemini 그림(또는 지정 파일)을 <번호>.png 로 옮김
  py -3.11 -X utf8 gemini_job.py status <작업폴더>                     받은 번호·남은 번호
  py -3.11 -X utf8 gemini_job.py check  <작업폴더>                     등장인물 외모(cast) 등록·프롬프트 반영 확인
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
    born = os.path.getmtime(os.path.join(job_dir, "작업.json"))   # 작업을 만든 뒤에 받은 그림만 (예전 다운로드 제외)
    t0 = time.time()
    while not src and time.time() - t0 < wait:
        cands = [p for p in glob.glob(os.path.join(DL, "Gemini_Generated_Image_*.*")) + glob.glob(os.path.join(DL, "ChatGPT Image*.png"))
                 if p not in seen and p.lower().endswith((".png", ".jpg", ".jpeg", ".webp")) and os.path.getmtime(p) >= born - 5]
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


def new(a):
    """프로젝트 → 작업 폴더(작업.json). 사진 자리가 있으면(또는 --replace) 그 자리를 바꾸고, 없으면 나레이션 every 초마다 문단 앞에 넣음"""
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("--target", default="Gemini", choices=["Gemini", "ChatGPT"])
    ap.add_argument("--style", default="")
    ap.add_argument("--every", type=float, default=45)
    ap.add_argument("--replace", action="store_true")
    o = ap.parse_args(a)
    proj = json.load(open(o.project, encoding="utf-8"))
    paras = [x.strip() for x in re.split(r"\n\s*\n", (proj.get("story") or "").strip()) if x.strip()]
    marks = [i for i, x in enumerate(paras) if MARK.match(x)]
    text_of = lambda x: not MARK.match(x) and not x.startswith("#")
    slots = []
    if marks:                                # 이미 사진이 있으면 그 자리마다 새 그림으로 바꿈
        for i in marks:
            nxt = next((q for q in paras[i + 1:] if text_of(q)), "")
            cap = (MARK.match(paras[i]).group(2) or "").strip()
            slots.append({"n": len(slots) + 1, "mode": "replace", "pi": i, "para": nxt, "ko": cap, "prompt": ""})
    else:                                    # 나레이션 약 every 초(1분 ≈ 420자)마다 한 장, 첫 문단부터
        per = 420 * o.every / 60
        acc = per
        for i, x in enumerate(paras):
            if not text_of(x):
                continue
            if acc >= per:
                slots.append({"n": len(slots) + 1, "mode": "insert", "pi": None, "para": x, "ko": "", "prompt": ""})
                acc = 0
            acc += len(x)
    title = re.sub(r'[\\/:*?"<>|]', " ", proj.get("title") or "그림").strip()[:40].rstrip(" .")
    jd = os.path.join(BASE, "output", "그림작업", f"{title}_{o.target}" + time.strftime("_%m%d_%H%M"))
    os.makedirs(jd, exist_ok=True)
    cast = [{"name": c.get("name", ""), "look": c.get("look_ko") or c.get("look", "")} for c in (proj.get("cast") or []) if isinstance(c, dict) and c.get("name")]
    for sl in slots:
        sl["chars"] = []
    json.dump({"target": o.target, "style": o.style, "cast": cast, "project": proj, "slots": slots}, open(os.path.join(jd, "작업.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(f"그림 자리 {len(slots)}곳 ({'기존 사진 자리 바꾸기' if marks else f'약 {o.every:g}초마다 문단 앞'})")
    if cast:
        print("등장인물 외모 " + str(len(cast)) + "명 (대본을 쓸 때 정한 것): " + ", ".join(c["name"] for c in cast))
    print("JOB " + jd)
    return 0


LOOK_PARTS = {   # 외모 설명에 꼭 들어갈 것 (한국어·영어 둘 다 인정)
    "얼굴형": ("얼굴", "face"),
    "머리": ("머리", "hair", "bald", "대머리"),
    "체형·키": ("체형", "체격", "키", "마른", "통통", "날씬", "건장", "slim", "tall", "short", "build", "height", "stocky", "petite", "chubby"),
    "안경": ("안경", "glasses", "spectacles"),
    "수염(남성)": ("수염", "콧수염", "턱수염", "면도", "beard", "mustache", "moustache", "stubble", "clean-shaven", "shaven", "goatee", "sideburns"),
    "옷": ("옷", "셔츠", "니트", "정장", "블라우스", "조끼", "교복", "한복", "원피스", "재킷", "코트", "uniform", "shirt", "suit", "dress", "jacket", "sweater", "coat"),
}


def parse_cast(v):
    """cast: [{"name","look"}] 목록 또는 예전 형식의 글('이름: 외모' / '이름(외모)' 줄)"""
    if isinstance(v, list):
        return [c for c in v if isinstance(c, dict) and c.get("name") and c.get("look")]
    out = []
    for ln in str(v or "").splitlines():
        ln = ln.strip(" -•\t")
        if ":" in ln:
            nm, lk = ln.split(":", 1)
        elif "(" in ln and ln.endswith(")"):
            nm, lk = ln.split("(", 1)
            lk = lk[:-1]
        else:
            continue
        nm = re.sub(r"\s+(대리|주임|사원|팀장|과장|부장|대표|씨)$", "", nm.strip())
        if nm and lk.strip():
            out.append({"name": nm.strip(), "look": lk.strip()})
    return out


def check(job_dir):
    """등장인물 외모가 등록됐는지, 얼굴형·머리·체형·옷이 다 들어갔는지, 인물이 나오는 장면 프롬프트에 외모가 그대로 들어갔는지"""
    j = load(job_dir)
    cast = parse_cast(j.get("cast"))
    probs = []
    if not cast:
        probs.append("cast 가 비어 있음 - 두 장 이상 나오는 인물이 있으면 먼저 외모를 등록할 것")
    for c in cast:
        male = any(w in c["look"].lower() for w in ("남성", "남자", "할아버지", "소년", "아저씨", " man", "boy", "male", "gentleman"))
        miss = [k for k, ws in LOOK_PARTS.items() if not any(w in c["look"].lower() for w in ws) and not (k.startswith("수염") and not male)]
        if miss:
            probs.append(f"외모 항목 부족 - {c['name']}: {', '.join(miss)} 없음")
    base = {c["name"]: re.split(r"[(\[]", c["name"])[0].strip() for c in cast}
    for sl in j["slots"]:
        p = str(sl.get("prompt") or "")
        if not p:
            probs.append(f"{sl['n']}번: prompt 비어 있음")
            continue
        names = [n for n in (sl.get("chars") or []) if n in base]
        for nm in [x for x in sl.get("chars") or [] if x not in base]:
            probs.append(f"{sl['n']}번: chars 의 '{nm}' 이(가) cast 에 없음")
        got = {base[x] for x in names}
        txt = str(sl.get("para", "")) + " " + p
        for b in dict.fromkeys(base.values()):          # 이름(성 포함) 또는 '이름+조사'가 나오는데 chars 에 없는 인물
            if not b or b in got:
                continue
            given = b[1:] if len(b) >= 3 else ""
            hit = b in txt or (given and re.search(re.escape(given) + r"(은|는|이가|이는|이를|이의|이에게|이와|씨|에게|와|과|의|가|를|이)(?=\s|[,.!?]|$)", str(sl.get("para", ""))))
            if not hit:
                continue
            same = [x for x in base if base[x] == b]
            if len(same) == 1:
                names.append(same[0])
            else:
                probs.append(f"{sl['n']}번: '{b}' 가 나오는데 어느 시기 외모인지 chars 에 없음")
        for nm in names:
            look = next(c["look"] for c in cast if c["name"] == nm)
            if look[:20] not in p:
                probs.append(f"{sl['n']}번: {nm} 의 외모 설명이 prompt 에 그대로 들어가 있지 않음")
    if probs:
        print("확인 필요 " + str(len(probs)) + "건:\n- " + "\n- ".join(probs))
        return 1
    print(f"OK 등장인물 {len(cast)}명 외모 등록·{len(j['slots'])}장 프롬프트 반영 확인")
    return 0


def main(a):
    if a and a[0] == "new" and len(a) > 1:
        return new(a[1:])
    if len(a) == 2 and a[0] == "check":
        return check(os.path.abspath(a[1]))
    if len(a) < 2 or a[0] not in ("put", "status", "apply"):
        print(__doc__)
        return 2
    d = os.path.abspath(a[1])
    if a[0] == "put":
        return put(d, a[2], a[3] if len(a) > 3 else None)
    return status(d) if a[0] == "status" else apply(d)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
