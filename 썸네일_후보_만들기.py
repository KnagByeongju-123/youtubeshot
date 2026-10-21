r"""output\장문 의 영상마다 썸네일 후보를 새로 만들기 (영상은 다시 만들지 않음)

  썸네일_후보_만들기.bat   (또는  py -3.11 -X utf8 썸네일_후보_만들기.py [--only 제목일부])

- 디자인 16가지(기본·반분할·노랑 패널·시네마 띠·뉴스 속보·미스터리 다크·빨간 강조·파스텔 하단 띠·상단 큰 질문·좌측 세로 띠·하단 그라데이션·메모지 + 사진 오려 붙이기·콜라주 3장·원형 컷 2장·폴라로이드 콜라주)
  + 완성된 MP4 장면으로 만든 실사 편집 후보(A 피사체 중심 · B 좌우 비교 · C 증거 확대)를 <제목>_썸네일_후보\ 에 만듦
- 지금 쓰는 유튜브 썸네일(_썸네일_유튜브.jpg)은 그대로. 예전 후보는 후보 폴더 안 '이전_날짜' 폴더로 옮겨 둠
- 고르기: 프로그램의 🖼 썸네일 고르기 버튼, 또는 후보 폴더를 썸네일_고르기.bat 위에 끌어다 놓기
- '_성우1' 같은 추가 버전은 원본과 같은 썸네일을 쓰므로 건너뜀
"""
import argparse
import glob
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "output", "장문")
TAIL = "_프로젝트.json"


def safe_name(s):      # shorts_novel_maker_supertonic.safe_name 과 같은 규칙 (결과 파일 이름)
    s = re.sub(r'[\\/:*?"<>|\n\r\t]', "", s).strip()
    return s[:40].rstrip(" .") or "short_novel"


def main():
    ap = argparse.ArgumentParser(description="output\\장문 영상마다 썸네일 후보 새로 만들기")
    ap.add_argument("--only", default="", help="파일 이름이나 제목에 이 글자가 들어간 것만")
    a = ap.parse_args()
    items = []
    for p in sorted(glob.glob(os.path.join(OUT, "*" + TAIL)) + glob.glob(os.path.join(OUT, "*", "*" + TAIL))):   # 콘텐츠 폴더 안까지
        stem = os.path.basename(p)[:-len(TAIL)]
        if re.search(r"_(여성)?성우\d+$", stem) or not os.path.exists(os.path.join(os.path.dirname(p), stem + ".mp4")):
            continue
        try:
            d = json.load(open(p, encoding="utf-8"))
        except Exception:
            continue
        title = str(d.get("title") or "")
        if a.only and a.only not in stem and a.only not in title:
            continue
        base = safe_name(title)
        suffix = stem[len(base) + 1:] if stem != base and stem.startswith(base + "_") else ""   # 예: _쇼츠
        items.append((p, stem, str(d.get("category") or ""), suffix))
    print(f"🖼 썸네일 후보를 만들 영상: {len(items)}개 (영상은 그대로, 지금 유튜브 썸네일도 그대로)")
    bad = []
    for i, (p, stem, cat, suffix) in enumerate(items, 1):
        print(f"\n▶ {i}/{len(items)} {stem}", flush=True)
        cmd = [sys.executable, "-X", "utf8", os.path.join(HERE, "render_project.py"), p, "--썸네일만"]
        if cat == "장문":
            cmd.append("--소재프로필")
        if suffix:
            cmd += ["--suffix", suffix]
        if subprocess.run(cmd, cwd=HERE).returncode != 0:
            bad.append(stem)
    print("\n" + ("🏁 모두 완료" if not bad else "⚠ 실패: " + ", ".join(bad)))
    print("고르기: 프로그램의 🖼 썸네일 고르기 버튼, 또는 <제목>_썸네일_후보 폴더를 썸네일_고르기.bat 위에 끌어다 놓기")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
