r"""
썸네일 후보 고르기 — 자동(점수) 또는 수동(클릭 창 / 번호 입력)

  python thumb_pick.py <후보 폴더> [--자동 | --수동] [--최종 <저장 경로>] [--선호 "A,B,C"]
    후보 폴더: thumb_*.jpg / NN_*.jpg / 외부_*.jpg / 01.jpg … 가 있는 폴더 (소재탐색 소재 폴더, MP4 썸네일 폴더, _썸네일_후보 폴더 모두 가능)
    기본은 --수동 (창이 안 뜨는 환경이면 번호 입력). 고른 파일은 <후보 폴더>\썸네일_최종.jpg 로 복사 (--최종 으로 바꿀 수 있음)

자동 선택 기준 (무료·로컬, 이유를 선택_기록.json 에 남김)
  1) 레이아웃 선호: A 피사체 중심형 > B 좌우 비교형 > C 증거 확대형 > 기타 (--선호 로 순서 변경)
  2) meta.json 에 문구 넘침(text_overflow)이 기록된 후보 감점
  3) 글자 영역(왼쪽 아래)의 평균 밝기가 너무 밝으면(글자 대비 약함) 감점, 전체가 너무 어둡거나 밝으면 감점
  4) 실사 편집본 > 기본 그래픽(임시)
"""

import argparse
import glob
import json
import os
import re
import shutil
import sys
import time

DEFAULT_PREF = ["A", "B", "C"]


def list_candidates(folder):
    pats = ["thumb_*.jpg", "thumb_*.png", "[0-9][0-9]_*.jpg", "외부_*.jpg", "[0-9][0-9].jpg"]
    seen, out = set(), []
    for p in pats:
        for f in sorted(glob.glob(os.path.join(folder, p))):
            base = os.path.basename(f)
            if base.startswith("썸네일_최종") or base in seen:
                continue
            seen.add(base)
            out.append(f)
    return out


def layout_letter(path, meta_by_file):
    """파일 이름/메타에서 레이아웃 문자(A/B/C) 추출"""
    base = os.path.basename(path)
    m = meta_by_file.get(base) or {}
    lay = str(m.get("layout", ""))
    if lay[:1] in ("A", "B", "C"):
        return lay[:1]
    mm = re.search(r"(?:thumb_|_)([ABC])(?:2|_|\.|$)", base)
    return mm.group(1) if mm else ""


def load_meta(folder):
    """meta.json 의 variants/candidates → {파일명: 메타}"""
    p = os.path.join(folder, "meta.json")
    try:
        d = json.load(open(p, encoding="utf-8"))
    except Exception:
        return {}, {}
    out = {}
    for v in (d.get("variants") or d.get("candidates") or []):
        if isinstance(v, dict) and v.get("file"):
            out[v["file"]] = v
    return out, d


def image_scores(path):
    """글자 영역(왼쪽 아래) 밝기와 전체 밝기 (Pillow). 실패하면 중립값."""
    try:
        from PIL import Image, ImageStat
        with Image.open(path) as im:
            g = im.convert("L")
            w, h = g.size
            text_zone = g.crop((0, int(h * 0.6), int(w * 0.6), h))
            return ImageStat.Stat(text_zone).mean[0], ImageStat.Stat(g).mean[0]
    except Exception:
        return 80.0, 110.0


def auto_pick(cands, folder, pref=None):
    """후보 중 하나를 점수로 고름. 반환: (경로, 이유, 전체 점수표)"""
    pref = pref or DEFAULT_PREF
    meta_by_file, top = load_meta(folder)
    graphic = str(top.get("mode", "")).startswith("기본 그래픽") if top else False
    table = []
    for p in cands:
        base = os.path.basename(p)
        m = meta_by_file.get(base) or {}
        letter = layout_letter(p, meta_by_file)
        s, why = 50.0, []
        if letter in pref:
            bonus = (len(pref) - pref.index(letter)) * 10
            s += bonus
            why.append(f"레이아웃 {letter} +{bonus}")
        if m.get("text_overflow"):
            s -= 25
            why.append("문구 넘침 -25")
        if m.get("error"):
            s -= 100
            why.append("생성 오류")
        tz, overall = image_scores(p)
        if tz > 150:
            s -= 10
            why.append("글자 영역 밝음 -10")
        if overall < 35 or overall > 215:
            s -= 10
            why.append("전체 너무 어둡거나 밝음 -10")
        if graphic or "기본 그래픽" in str(m.get("layout", "")):
            s -= 15
            why.append("기본 그래픽(임시) -15")
        if "외부_mp4" in base:
            why.append("MP4 장면")
        table.append({"file": base, "score": round(s, 1), "why": ", ".join(why) or "기본"})
    if not table:
        return "", "후보 없음", []
    table.sort(key=lambda r: (-r["score"], r["file"]))
    best = table[0]
    return os.path.join(folder, best["file"]), best["why"], table


def manual_pick(cands, title=""):
    """클릭 창으로 고르기. Tk 를 못 쓰면 번호 입력. 반환: 경로 또는 '' (취소)"""
    try:
        return _tk_pick(cands, title)
    except Exception as e:
        print(f"(창을 띄우지 못해 번호로 고릅니다: {str(e)[:60]})")
        return _console_pick(cands)


def _console_pick(cands, input_fn=input):
    for i, p in enumerate(cands, 1):
        print(f"  {i}. {os.path.basename(p)}")
    while True:
        s = input_fn(f"번호를 입력하세요 (1~{len(cands)}, 엔터=취소): ").strip()
        if not s:
            return ""
        if s.isdigit() and 1 <= int(s) <= len(cands):
            return cands[int(s) - 1]
        print("다시 입력해 주세요.")


def _tk_pick(cands, title=""):
    import tkinter as tk
    from PIL import Image, ImageTk
    root = tk.Tk()
    root.title(f"썸네일 고르기 — {title or os.path.basename(os.path.dirname(cands[0]))}")
    cols = 3 if len(cands) > 4 else 2
    tw, th = (400, 225) if cols == 3 else (520, 292)
    chosen = {"p": ""}
    photos = []
    tk.Label(root, text="마음에 드는 썸네일을 클릭하세요 (창을 닫으면 취소)", font=("Malgun Gothic", 12)).grid(row=0, column=0, columnspan=cols, pady=(8, 4))
    for i, p in enumerate(cands):
        with Image.open(p) as im:
            ph = ImageTk.PhotoImage(im.convert("RGB").resize((tw, th), Image.LANCZOS))
        photos.append(ph)
        f = tk.Frame(root, bd=2, relief="groove", padx=4, pady=4)
        f.grid(row=1 + i // cols * 2, column=i % cols, padx=6, pady=6)
        b = tk.Button(f, image=ph, command=lambda q=p: (chosen.__setitem__("p", q), root.destroy()))
        b.pack()
        tk.Label(f, text=f"{i + 1}. {os.path.basename(p)}", font=("Malgun Gothic", 10)).pack()
    root.update_idletasks()
    sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
    root.geometry(f"+{max(0, (sw - root.winfo_width()) // 2)}+{max(0, (sh - root.winfo_height()) // 2)}")
    root.mainloop()
    return chosen["p"]


def finalize(choice, folder, dest=None, how="", reason="", table=None):
    """고른 후보를 최종 파일로 복사하고 선택_기록.json 에 남김"""
    dest = dest or os.path.join(folder, "썸네일_최종.jpg")
    os.makedirs(os.path.dirname(os.path.abspath(dest)), exist_ok=True)
    shutil.copy(choice, dest)
    rec = {"chosen": os.path.basename(choice), "final": dest, "how": how, "reason": reason,
           "when": time.strftime("%Y-%m-%d %H:%M:%S"), "scores": table or []}
    with open(os.path.join(folder, "선택_기록.json"), "w", encoding="utf-8") as f:
        json.dump(rec, f, ensure_ascii=False, indent=1)
    return dest


def pick(folder, mode="수동", dest=None, pref=None, title=""):
    """mode: 자동 | 수동. 반환: (최종 경로 또는 '', 설명)"""
    cands = list_candidates(folder)
    if not cands:
        return "", f"후보 이미지가 없습니다: {folder}"
    if mode == "자동":
        choice, reason, table = auto_pick(cands, folder, pref)
        if not choice:
            return "", reason
        out = finalize(choice, folder, dest, "자동", reason, table)
        return out, f"자동 선택: {os.path.basename(choice)} ({reason})"
    choice = manual_pick(cands, title)
    if not choice:
        return "", "취소했습니다 (선택 안 함)"
    out = finalize(choice, folder, dest, "수동")
    return out, f"선택: {os.path.basename(choice)}"


def main(argv=None):
    ap = argparse.ArgumentParser(description="썸네일 후보 고르기 (자동/수동)")
    ap.add_argument("folder")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--자동", action="store_true")
    g.add_argument("--수동", action="store_true")
    ap.add_argument("--최종", default="", help="고른 파일을 저장할 경로 (기본: <폴더>\\썸네일_최종.jpg)")
    ap.add_argument("--선호", default=",".join(DEFAULT_PREF), help="자동 선택 레이아웃 선호 순서, 기본 A,B,C")
    a = ap.parse_args(argv)
    folder = os.path.abspath(a.folder)
    if os.path.isfile(folder):
        folder = os.path.dirname(folder)
    if not os.path.isdir(folder):
        ap.error(f"폴더가 없습니다: {folder}")
    mode = "자동" if a.자동 else "수동"
    pref = [x.strip().upper() for x in a.선호.split(",") if x.strip()]
    out, msg = pick(folder, mode, a.최종 or None, pref)
    print(msg)
    if out:
        print("최종:", out)
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
