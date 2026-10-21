r"""콘텐츠 정리 - 규칙: 영상이 완성되면 콘텐츠마다 디렉토리 하나로 모음

  output\장문\0001_<롱폼 제목>\      (맨 앞 4자리 = 콘텐츠 순서 번호. 새 콘텐츠는 다음 번호, 다시 만들어도 번호는 그대로)
      <제목>.mp4, _설명란.txt, _업로드문구.txt, _타임스탬프.txt, _썸네일*.png/jpg, _썸네일_후보\, _썸네일_mp4\,
      _나레이션검증.txt, _프로젝트.json, _성우1 같은 추가 버전
      <쇼츠 제목>_쇼츠.mp4 … (같은 대본에서 만든 쇼츠도 같은 폴더에)

  - render_project.py / make_longdoc.py 가 롱폼(+쇼츠)을 다 만든 뒤 자동으로 부름
  - 이미 만든 것 한꺼번에 정리:  py -3.11 -X utf8 콘텐츠_정리.py
  - 영상(MP4)이 아직 없는 것(만드는 중)은 건드리지 않음. 사진(media)은 여러 콘텐츠가 함께 쓰므로 그대로 둠
  - 이어 만들기용 작업 폴더(_작업_제목, _작업_주제, 쇼츠의 _작업_)도 콘텐츠 폴더 안으로 옮김.
    다시 만들 때는 render_project.py / make_longdoc.py 가 find_work() 로 폴더 안의 작업 폴더를 찾아 이어서 씀
  - 정리된 폴더 안의 프로젝트로 다시 만들면 결과도 그 폴더에 저장됨 (render_project.py)
"""
import glob
import json
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "output", "장문")
SHORTS_DIR = os.path.join(HERE, "실화", "쇼츠")
TAIL = "_프로젝트.json"


def safe_name(s):      # shorts_novel_maker_supertonic.safe_name 과 같은 규칙
    s = re.sub(r'[\\/:*?"<>|\n\r\t]', "", s).strip()
    return s[:40].rstrip(" .") or "short_novel"


NUM_RE = re.compile(r"^(\d{4})_(.+)$")    # 규칙: 콘텐츠 폴더 이름 맨 앞에 순서 번호 0001_, 0002_ …


def content_dir(out_dir, title, create=True):
    """이 제목의 콘텐츠 폴더 경로. 이미 있으면(번호가 붙어 있든 없든) 그 폴더, 없으면 다음 번호를 붙인 새 이름 '0008_제목'"""
    name = safe_name(title)
    nums = []
    for d in os.listdir(out_dir) if os.path.isdir(out_dir) else []:
        if not os.path.isdir(os.path.join(out_dir, d)):
            continue
        m_ = NUM_RE.match(d)
        if m_:
            nums.append(int(m_.group(1)))
            if m_.group(2) == name:
                return os.path.join(out_dir, d)
        elif d == name:                       # 번호 없이 정리된 예전 폴더 → 번호를 붙여 이름을 바꿈
            new = os.path.join(out_dir, f"{(max(nums + _all_nums(out_dir)) if nums or _all_nums(out_dir) else 0) + 1:04d}_{name}")
            if create:
                os.rename(os.path.join(out_dir, d), new)
                return new
            return os.path.join(out_dir, d)
    return os.path.join(out_dir, f"{max(nums + _all_nums(out_dir) + [0]) + 1:04d}_{name}")


LAST_FILE = "_마지막번호.txt"   # 지금까지 쓴 가장 큰 번호 (업로드 후 폴더를 지워도 번호가 다시 쓰이지 않게)


def _all_nums(out_dir):
    nums = [int(m_.group(1)) for d in os.listdir(out_dir) if (m_ := NUM_RE.match(d)) and os.path.isdir(os.path.join(out_dir, d))]
    try:
        nums.append(int(open(os.path.join(out_dir, LAST_FILE), encoding="utf-8").read().strip() or 0))
    except (OSError, ValueError):
        pass
    return nums


def _save_last(out_dir):
    n = max(_all_nums(out_dir) + [0])
    with open(os.path.join(out_dir, LAST_FILE), "w", encoding="utf-8") as f:
        f.write(str(n))


def number_existing(out_dir=OUT, log=print):
    """번호 없이 정리된 콘텐츠 폴더에 만든 순서(영상 파일 시각)대로 번호를 붙임. 이미 번호가 있는 폴더 뒤로 이어서"""
    plain = []
    for d in os.listdir(out_dir):
        p = os.path.join(out_dir, d)
        if not os.path.isdir(p) or d.startswith("_") or d == "media" or NUM_RE.match(d):
            continue
        mp4s = [os.path.join(p, f) for f in os.listdir(p) if f.endswith(".mp4") and "_쇼츠" not in f and "_성우" not in f]
        if not mp4s:
            continue
        plain.append((min(os.path.getmtime(x) for x in mp4s), d))
    nxt = max(_all_nums(out_dir) + [0]) + 1
    for _, d in sorted(plain):
        new = f"{nxt:04d}_{d}"
        os.rename(os.path.join(out_dir, d), os.path.join(out_dir, new))
        _save_last(out_dir)
        log(f"🔢 {d} → {new}")
        nxt += 1
    return nxt - 1


WORK = "_작업_"


def find_work(out_dir, key, title=""):
    """이어 만들기용 작업 폴더 위치: 바깥(만드는 중) → 콘텐츠 폴더 안(정리된 뒤) → 이 제목의 콘텐츠 폴더가 있으면 그 안 → 없으면 바깥에 새로"""
    name = WORK + key
    root = os.path.join(out_dir, name)
    if os.path.isdir(root):
        return root
    for d in os.listdir(out_dir) if os.path.isdir(out_dir) else []:
        q = os.path.join(out_dir, d, name)
        if not d.startswith("_") and os.path.isdir(q):
            return q
    if title:
        cd = content_dir(out_dir, title, create=False)
        if os.path.isdir(cd):
            return os.path.join(cd, name)
    return root


MADE_FILE = "_만든주제.txt"     # 업로드 후 지운 콘텐츠의 제목·주제 기록 (같은 주제를 다시 고르지 않게)


def record_made(out_dir, names):
    """지우기 전에 제목·주제를 _만든주제.txt 에 남김"""
    p = os.path.join(out_dir, MADE_FILE)
    have = set(open(p, encoding="utf-8").read().splitlines()) if os.path.exists(p) else set()
    new = [n for n in dict.fromkeys(x.strip() for x in names if x and x.strip()) if n not in have]
    if new:
        with open(p, "a", encoding="utf-8") as f:
            f.write("\n".join(new) + "\n")
    return new


def all_work_names(out_dir):
    """만든(만들기 시작한) 콘텐츠의 작업 폴더 이름들 (바깥 + 콘텐츠 폴더 안) + 지운 콘텐츠 기록 - 같은 주제를 다시 고르지 않게"""
    out = []
    if not os.path.isdir(out_dir):
        return out
    mf = os.path.join(out_dir, MADE_FILE)
    if os.path.exists(mf):
        out += [x for x in open(mf, encoding="utf-8").read().splitlines() if x.strip()]
    for d in os.listdir(out_dir):
        if d.startswith(WORK):
            out.append(d[len(WORK):])
        elif not d.startswith("_") and os.path.isdir(os.path.join(out_dir, d)):
            out += [x[len(WORK):] for x in os.listdir(os.path.join(out_dir, d)) if x.startswith(WORK)]
    return out


def _belongs(name, base):
    """파일·폴더 이름이 이 콘텐츠(base) 것인지: base 바로 뒤가 '.' 또는 '_' (다른 제목의 앞부분과 헷갈리지 않게)"""
    return name == base or (name.startswith(base) and name[len(base):len(base) + 1] in (".", "_"))


def shorts_base_for(long_title):
    """같은 대본에서 만든 쇼츠의 파일 이름 앞부분 (실화\\쇼츠\\<롱폼 제목>.json 의 title + '_쇼츠')"""
    cands = [os.path.join(SHORTS_DIR, safe_name(long_title) + ".json")]
    cands += [p for p in glob.glob(os.path.join(SHORTS_DIR, "*.json")) if p not in cands]
    for p in cands:
        try:
            d = json.load(open(p, encoding="utf-8"))
        except Exception:
            continue
        if os.path.basename(p) == safe_name(long_title) + ".json" or str(d.get("topic") or "").strip() == long_title.strip():
            t = str(d.get("title") or "").strip()
            if t:
                return safe_name(t) + "_쇼츠"
    return ""


def organize(long_proj, log=print, out_dir=OUT):
    """롱폼 프로젝트 하나(+그 쇼츠) → out_dir\\<제목>\\ 로 모음. 반환: 폴더 경로 또는 ''"""
    try:
        d = json.load(open(long_proj, encoding="utf-8"))
    except Exception:
        return ""
    title = str(d.get("title") or "").strip()
    if not title:
        return ""
    base = os.path.basename(long_proj)[:-len(TAIL)] if long_proj.endswith(TAIL) else safe_name(title)
    src_dir = os.path.dirname(os.path.abspath(long_proj))
    dest = content_dir(out_dir, title, create=False)     # 이미 있는 폴더(번호 포함) 또는 다음 번호의 새 폴더
    if os.path.normcase(src_dir) == os.path.normcase(dest):
        src_dir = out_dir                   # 이미 정리된 콘텐츠를 다시 만든 경우: 바깥에 새로 생긴 파일만 모음
    if not os.path.exists(os.path.join(src_dir, base + ".mp4")) and not os.path.exists(os.path.join(dest, base + ".mp4")):
        return ""                           # 아직 영상이 없음 (만드는 중) → 건드리지 않음
    if os.path.exists(os.path.join(src_dir, base + ".만드는중")):
        return ""                           # 영상·업로드 문구·쇼츠를 아직 만드는 중 (render_project.py 가 끝나면 지움)
    mp4 = os.path.join(src_dir, base + ".mp4")
    if os.path.exists(mp4):                 # 다른 프로그램이 영상을 쓰고 있으면(만드는 중) 건드리지 않음
        try:
            os.replace(mp4, mp4 + ".정리확인")
            os.replace(mp4 + ".정리확인", mp4)
        except OSError:
            log(f"⏳ 아직 만드는 중이라 건너뜀: {base}")
            return ""
    bases = [base]
    sb = shorts_base_for(title)
    if sb:
        bases.append(sb)
    os.makedirs(dest, exist_ok=True)
    _save_last(out_dir)                     # 이 번호를 기억 (나중에 폴더를 지워도 같은 번호를 다시 쓰지 않게)
    moved = 0
    works = {WORK + safe_name(title)[:40], WORK + base[:40]} | ({WORK + sb[:-len("_쇼츠")][:40] + "_쇼츠", WORK + sb} if sb else set())
    if str(d.get("topic") or "").strip():                     # make_longdoc.py 는 주제 이름으로 작업 폴더를 만듦
        works.add(WORK + safe_name(str(d.get("topic")))[:40])
    for name in os.listdir(out_dir):
        if name == "media" or (name.startswith("_") and name not in works):
            continue
        p = os.path.join(out_dir, name)
        is_work = name in works
        if os.path.normcase(p) == os.path.normcase(dest) or not (is_work or any(_belongs(name, b) for b in bases)):
            continue
        if os.path.isdir(p) and not is_work and not re.search(r"_썸네일_(후보|mp4)$", name):
            continue                        # 다른 콘텐츠 폴더는 건드리지 않음
        q = os.path.join(dest, name)
        try:
            if os.path.isdir(q):
                shutil.rmtree(q)
            elif os.path.exists(q):
                os.remove(q)
            shutil.move(p, q)
            moved += 1
        except OSError as e:
            log(f"  ⚠ 옮기지 못함(그대로 둠): {name} ({str(e)[:40]})")
    if moved:
        log(f"📁 콘텐츠 정리: {moved}개 파일·폴더 → output\\장문\\{os.path.basename(dest)}\\" + (" (쇼츠 포함)" if sb else ""))
    return dest


def renders_running():
    """영상 만들기(render_project·make_longdoc·쇼츠_자동)가 돌고 있는지 - 돌고 있으면 한꺼번에 정리는 미룸"""
    if os.name != "nt":
        return False
    try:
        import subprocess
        ps = ("(Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | Where-Object { $_.CommandLine -match "
              "'render_project|make_longdoc|쇼츠_자동' } | Measure-Object).Count")
        r = subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, text=True, timeout=60,
                           creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        return int((r.stdout or "0").strip() or 0) > 0
    except Exception:
        return False


def organize_all(log=print):
    """output\\장문 바로 아래 롱폼 프로젝트(쇼츠·추가 버전 제외)를 모두 정리. 영상 만들기가 돌고 있으면 하지 않음
    (만드는 중인 영상의 파일을 옮기면 업로드 문구·쇼츠 단계가 파일을 못 찾음)"""
    if renders_running():
        log("⏳ 지금 영상을 만드는 중이라 한꺼번에 정리는 하지 않습니다. 만들기가 끝난 뒤 다시 실행하세요 "
            "(새로 만드는 영상은 다 만든 뒤 자동으로 정리됩니다).")
        return 0
    n = 0
    for p in find_projects(OUT):            # 바깥 + 이미 정리된 폴더 안 (바깥에 남은 작업 폴더·새 파일도 모음)
        stem = os.path.basename(p)[:-len(TAIL)]
        if re.search(r"_(쇼츠|(여성)?성우\d+)$", stem):
            continue
        try:
            d = json.load(open(p, encoding="utf-8"))
        except Exception:
            continue
        if str(d.get("category") or "") != "장문":
            continue
        try:
            if organize(p, log):
                n += 1
        except Exception as e:
            log(f"⚠ 정리 실패(그대로 둠): {stem} ({str(e)[:60]})")
    for name in os.listdir(OUT):            # 만드는 중이라 건너뛰어 비어 있는 폴더는 지움
        q = os.path.join(OUT, name)
        if os.path.isdir(q) and not name.startswith("_") and name != "media" and not os.listdir(q):
            os.rmdir(q)
    number_existing(OUT, log)               # 번호 없는 콘텐츠 폴더에 순서 번호 붙이기
    return n


def find_projects(out_dir=OUT):
    """정리 전(바로 아래)·정리 후(콘텐츠 폴더 안) 프로젝트 파일을 모두 찾음 - 다른 도구들이 씀"""
    return sorted(glob.glob(os.path.join(out_dir, "*" + TAIL)) + glob.glob(os.path.join(out_dir, "*", "*" + TAIL)))


if __name__ == "__main__":
    os.chdir(HERE)
    print(f"🗂 output\\장문 의 완성된 콘텐츠를 제목별 폴더로 정리합니다 (만드는 중인 것은 건너뜀)")
    k = organize_all()
    print(f"✅ {k}개 콘텐츠 정리 완료")
    sys.exit(0)
