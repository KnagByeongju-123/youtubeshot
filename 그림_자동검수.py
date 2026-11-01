"""그림 자동 검수 — 오픈소스 도구가 의심 그림을 먼저 골라 주고, Claude 가 그 그림을 크게 열어 확인 (사용자 결정 2026-10-31)
  .sd_venv/bin/python -X utf8 그림_자동검수.py <프로젝트.json 또는 그림 폴더>
  → <프로젝트 폴더 또는 그림 폴더>/_자동검수.txt (의심 그림 목록 + 이유) 와 _자동검수.json

자동으로 보는 것
  - 글자: RapidOCR(Apache-2.0, 모델이 설치 파일 안에 있음)의 글자 위치 찾기 — 한글·한자·영어 모두 위치는 찾음
    (가로로 긴 글자 상자, 그림 넓이의 0.3% 이상만. 간판·도장·종이 글씨·홀로그램 글자 의심)
  - 세로 그림(가로 영상인데 높이 > 너비), 테두리(가장자리 단색 띠), 같은 그림이 두 번 쓰임
시험해 보고 뺀 것 (2026-11-01): OWLv2(손·얼굴·소품 찾기)는 사진으로 배운 도구라 애니·수묵 그림에서 손·얼굴을 거의 못 찾음(점수 0.02~0.08)
  → 팔·다리·손 수, 얼굴 방향, 복제, 시대 소품은 계속 Claude 가 그림을 크게 열어 셈 (CLAUDE.md 3장 검수 규칙)
결과는 '의심'일 뿐 — 마지막 판정은 Claude 가 그림을 크게 열어 보고 함"""
import json
import os
import re
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
MEDIA_RE = re.compile(r"^\[(?:사진|그림|이미지)\s*[:：]\s*([^|\]]+)")


def images_of(src):
    if os.path.isdir(src):
        return sorted(os.path.join(src, f) for f in os.listdir(src)
                      if f.lower().endswith((".png", ".jpg", ".jpeg")) and not f.startswith("_") and ".인물." not in f), src
    story = json.load(open(src, encoding="utf-8")).get("story", "")
    out = []
    for line in story.split("\n"):
        m = MEDIA_RE.match(line.strip())
        if m:
            p = m.group(1).strip()
            out.append(p if os.path.isabs(p) else os.path.join(HERE, p))
    return out, os.path.dirname(os.path.abspath(src))


def border_band(im):
    a = np.asarray(im.convert("L").resize((320, 180)), np.float32)
    bad = []
    for name, line in (("위", a[:4]), ("아래", a[-4:]), ("왼쪽", a[:, :4]), ("오른쪽", a[:, -4:])):
        if line.std() < 4 and (line.mean() < 25 or line.mean() > 235):
            bad.append(name)
    return bad


def text_boxes(ocr, im):
    r, _ = ocr(np.asarray(im), use_det=True, use_cls=False, use_rec=False)
    w, h = im.size
    out = []
    for b in r or []:
        b = np.array(b)
        bw, bh = np.ptp(b[:, 0]), np.ptp(b[:, 1])
        if bw * bh >= w * h * 0.003 and bw >= bh * 2:
            out.append((int(b[:, 0].min() * 100 / w), int(b[:, 1].min() * 100 / h)))   # 왼쪽 위 위치 (가로·세로 %)
    return out


def main(a):
    if not a:
        print(__doc__)
        return 2
    src = os.path.abspath(a[0])
    paths, out_dir = images_of(src)
    print(f"그림 {len(paths)}장 검사 (글자 위치 RapidOCR · 세로 그림 · 테두리 · 같은 그림 두 번)", flush=True)
    from rapidocr_onnxruntime import RapidOCR
    ocr = RapidOCR()
    seen, report = {}, []
    for k, p in enumerate(paths):
        name = os.path.basename(p)
        why = []
        if p in seen:
            why.append(f"같은 그림이 {seen[p] + 1}번째에 이미 나옴")
        seen.setdefault(p, k)
        try:
            im = Image.open(p).convert("RGB")
        except Exception as e:
            report.append({"n": k + 1, "file": p, "why": [f"열 수 없음: {e}"]})
            continue
        w, h = im.size
        if h > w:
            why.append(f"세로 그림 {w}×{h}")
        bb = border_band(im)
        if bb:
            why.append("테두리·띠: " + ",".join(bb))
        tb = text_boxes(ocr, im)
        if tb:
            why.append("글자 의심 " + ", ".join(f"(가로 {x}%·세로 {y}%)" for x, y in tb[:3]))
        report.append({"n": k + 1, "file": p, "why": why})
        print(f"[{k + 1}/{len(paths)}] {name}: " + ("; ".join(why) if why else "통과"), flush=True)
    sus = [x for x in report if x["why"]]
    lines = [f"그림 자동 검수 — {len(paths)}장 중 의심 {len(sus)}장 (마지막 판정은 그림을 크게 열어 보고)"]
    lines += [f"- {x['n']}번 {os.path.basename(x['file'])}: " + "; ".join(x["why"]) for x in sus]
    open(os.path.join(out_dir, "_자동검수.txt"), "w", encoding="utf-8").write("\n".join(lines))
    json.dump(report, open(os.path.join(out_dir, "_자동검수.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
