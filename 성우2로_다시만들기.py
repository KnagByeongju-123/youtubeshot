r"""output\장문 의 영상을 모두 '남자 성우 2'(Supertonic M2) · 배경음 거의 없음으로 다시 만들기

  성우2로_다시만들기.bat   (또는  py -3.11 -X utf8 성우2로_다시만들기.py [--yes] [--only 제목일부])

- output\장문\*_프로젝트.json 마다: 성우 → Supertonic M2, 말할 때 배경음 0.3 으로 고친 뒤 render_project.py 로 다시 만듦
  (고치기 전 원본은 처음 한 번 '<이름>_프로젝트.원본.json' 으로 백업)
- 같은 이름의 MP4·썸네일·타임스탬프를 덮어씀. 업로드 문구·설명란·유튜브 썸네일(_썸네일_유튜브)은 그대로 둠
- --성우 M1 : 프로젝트 파일은 그대로 두고 그 성우로 '추가' 버전을 만듦 → <제목>_성우1.mp4 (원래 영상은 그대로)
- 장문_설정.json 의 배경음_크기를 0.03 으로 (처음 한 번 장문_설정.json.bak 백업)
- 대본·사진은 그대로라 나레이션과 영상만 새로 만듦. 한 편 실패하면 거기서 멈춤 (다시 실행하면 끝난 부분은 건너뜀)
"""
import argparse
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)
OUT = os.path.join(HERE, "output", "장문")
CFG = os.path.join(HERE, "장문_설정.json")
LOG_FILE = os.path.join(HERE, "장문_진행기록.txt")
VOICE = "Supertonic M2 (남성, 무료 로컬) [supertonic:M2]"
DUCK = 0.3      # 말할 때 배경음 크기
BGM = 0.03      # 배경음 크기 (거의 안 들림)
TAIL = "_프로젝트.json"


def log(x):
    line = f"[{time.strftime('%H:%M')}] [성우2] {x}"
    print(line, flush=True)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError:
        pass


def safe_name(s):      # shorts_novel_maker_supertonic.safe_name 과 같은 규칙 (결과 파일 이름)
    s = re.sub(r'[\\/:*?"<>|\n\r\t]', "", s).strip()
    return s[:40].rstrip(" .") or "short_novel"


def find_projects(only=""):
    items, skipped = [], []
    for p in sorted(glob.glob(os.path.join(OUT, "*" + TAIL)) + glob.glob(os.path.join(OUT, "*", "*" + TAIL))):   # 콘텐츠 폴더 안까지
        name = os.path.basename(p)
        try:
            d = json.load(open(p, encoding="utf-8"))
        except Exception as e:
            skipped.append(f"{name}: 읽기 실패 ({str(e)[:60]})")
            continue
        title = str(d.get("title") or "").strip()
        if not title or not str(d.get("story") or "").strip():
            skipped.append(f"{name}: 제목이나 대본이 비어 있음")
            continue
        if only and only not in name and only not in title:
            continue
        stem, base = name[:-len(TAIL)], safe_name(title)
        if re.search(r"_(여성)?성우\d+$", stem):     # --성우 로 만든 추가 버전(_성우1 …)은 원본이 아니므로 건너뜀
            continue
        if stem == base:
            suffix = ""
        elif stem.startswith(base + "_"):
            suffix = stem[len(base) + 1:]          # 예: _쇼츠
        else:
            skipped.append(f"{name}: 파일 이름과 제목이 달라 같은 파일로 덮어쓸 수 없음 (제목: {title})")
            continue
        s = d.get("settings") or {}
        items.append({"path": p, "name": name, "title": title, "category": str(d.get("category") or ""),
                      "suffix": suffix, "voice": str(s.get("narr_voice") or "(기본)")})
    items.sort(key=lambda x: (x["category"] != "장문", x["name"]))     # 롱폼 먼저, 쇼츠 나중
    return items, skipped


def set_bgm_config():
    try:
        c = json.load(open(CFG, encoding="utf-8"))
    except FileNotFoundError:
        c = {}
    except Exception as e:
        log(f"⚠ 장문_설정.json 을 읽지 못해 배경음 크기를 바꾸지 않음: {e}")
        return
    if c.get("배경음_크기") == BGM:
        return
    if os.path.exists(CFG) and not os.path.exists(CFG + ".bak"):
        shutil.copy2(CFG, CFG + ".bak")
    log(f"장문_설정.json 배경음_크기 {c.get('배경음_크기', '(없음)')} → {BGM}")
    c["배경음_크기"] = BGM
    with open(CFG, "w", encoding="utf-8") as f:
        json.dump(c, f, ensure_ascii=False, indent=1)


def set_voice(path):
    bak = path[:-len(".json")] + ".원본.json"
    if not os.path.exists(bak):
        shutil.copy2(path, bak)
    d = json.load(open(path, encoding="utf-8"))
    s = d.setdefault("settings", {})
    s.update(narr_voice=VOICE, narr_duck=DUCK, bgm_volume=BGM)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=1)


def main():
    ap = argparse.ArgumentParser(description="output\\장문 영상을 모두 남자 성우 2로 다시 만들기")
    ap.add_argument("--yes", action="store_true", help="묻지 않고 바로 시작")
    ap.add_argument("--only", default="", help="파일 이름이나 제목에 이 글자가 들어간 것만 (예: 인더스)")
    ap.add_argument("--성우", dest="voice", default="", help="추가 버전 성우 (예: M1 → <제목>_성우1.mp4, 원래 영상·프로젝트는 그대로)")
    a = ap.parse_args()

    src = open(os.path.join(HERE, "shorts_novel_maker_supertonic.py"), encoding="utf-8").read()
    if "DEFAULT_VOICE" not in src or "def tts_edge" in src:
        print("프로그램이 예전 버전입니다(마이크로소프트 음성이 남아 있음). 먼저 깃허브_최신받기.bat 을 실행하세요.")
        return 2
    items, skipped = find_projects(a.only)
    print("=" * 70)
    extra = a.voice.strip().upper()
    if extra and not re.fullmatch(r"[MF][1-5]", extra):
        print("--성우 는 M1~M5 또는 F1~F5 로 적어 주세요.")
        return 2
    tag = (f"성우{extra[1]}" if extra[0] == "M" else f"여성성우{extra[1]}") if extra else ""
    print(f"🎙 {'Supertonic ' + extra + ' 추가 버전(_' + tag + ')으로' if extra else '남자 성우 2로 다시'} 만들 영상: {len(items)}개  (output\장문)")
    for i, it in enumerate(items, 1):
        kind = "롱폼" if it["category"] == "장문" else "쇼츠/기타"
        print(f"  {i:2}. [{kind}] {it['title']}" + (f"  (_{it['suffix']})" if it["suffix"] else "") + f"   · 지금 성우: {it['voice']}")
    for s_ in skipped:
        print("  - 건너뜀: " + s_)
    print("=" * 70)
    if not items:
        print("다시 만들 영상이 없습니다.")
        return 0
    print(f"원래 영상은 그대로 두고 '_{tag}' 이 붙은 새 파일로 만듭니다." if extra else
          "같은 이름의 MP4·썸네일·타임스탬프를 덮어씁니다 (업로드 문구·설명란·유튜브 썸네일은 그대로).")
    print("한 편에 영상 1분당 약 3~5분 걸립니다. 중간에 멈춰도 다시 실행하면 이어서 합니다.")
    if not a.yes:
        try:
            ok = input("시작할까요? (y = 시작 / 그 외 = 취소) : ").strip().lower()
        except EOFError:
            ok = ""
        if ok not in ("y", "yes", "ㅇ", "예", "네"):
            print("취소했습니다.")
            return 0
    set_bgm_config()
    t0 = time.time()
    for i, it in enumerate(items, 1):
        log(f"▶ {i}/{len(items)} {it['title']} " + (f"(추가 버전 · Supertonic {extra})" if extra else f"(성우 {it['voice']} → 남자 성우 2)"))
        if not extra:
            set_voice(it["path"])
        cmd = [sys.executable, "-X", "utf8", os.path.join(HERE, "render_project.py"), it["path"]]
        if it["category"] == "장문":
            cmd.append("--소재프로필")      # 장문은 가로 화면·다큐 스타일 (저장된 화면 형식 칸이 '쇼츠 세로'로 남은 파일도 가로로)
        suffix = "_".join(x for x in (it["suffix"], tag) if x)
        if suffix:
            cmd += ["--suffix", suffix]
        if extra:
            cmd += ["--성우", extra]
        r = subprocess.run(cmd, cwd=HERE)
        if r.returncode != 0:
            log(f"❌ {it['title']} 에서 멈춤 (위 오류 확인). 다시 실행하면 끝난 영상·구간은 건너뛰고 이어서 합니다.")
            return 1
        log(f"✅ {i}/{len(items)} 완료 · 지금까지 {(time.time() - t0) / 60:.0f}분")
    log(f"🏁 모두 " + (f"Supertonic {extra} 추가 버전(_{tag})으로 만들었습니다" if extra else "남자 성우 2로 다시 만들었습니다") + f" ({len(items)}개, {(time.time() - t0) / 60:.0f}분)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
