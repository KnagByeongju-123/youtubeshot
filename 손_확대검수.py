"""손·발 확대 검수 — 사람마다 손·발을 찾아 크게 잘라 한 장에 모음 (손가락·팔·다리·발 수를 세기 쉽게) (.sd_venv 에서 실행)

  .sd_venv/bin/python 손_확대검수.py <결과폴더> <그림1.png> [그림2.png ...]   → <결과폴더>/<그림이름>_손.jpg + 경고 목록

- 1) 사람 찾기 DWPose(rtmlib Wholebody, 무료·오픈소스): 사람마다 몸·손·발 관절을 잡아 → 사람마다 왼손·오른손·왼발·오른발을 크게 자름
- 2) 손 찾기 YOLO(hand_yolov8n, ADetailer 가 쓰는 AI 그림용 모델): AI 그림 속 손을 네모로 찾음.
     DWPose 손과 겹치지 않는 손은 '남는 손'으로 따로 보여 줌 → 사람 수×2 보다 손이 많으면 ⚠ 경고 (팔·손이 하나 더 그려진 그림)
- 3) 그림을 2×3 칸으로 나눠 2배로 키운 조각도 붙임 (도구가 놓친 손·발·다리도 보이게)
- 찾기는 손가락 수를 판정하지 못함(늘 5개로 가정) → 잘라 준 조각을 보고 손가락 5개·손 2개·발 2개를 셈. 아니면 불합격
- 사용자 결정(2026-10-25): 손가락·발 검수는 전체를 줄여 보지 말고 확대해서 셈
"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
YOLO_HAND = os.path.join(HERE, "models", "hand_yolov8n.pt")
FONT = "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf"
_WB = None
_YO = None


def people_parts(path):
    """DWPose: 사람마다 {이름: 상자} (왼손·오른손·왼발·오른발). 반환 (목록, 사람 수)"""
    global _WB
    try:
        import cv2
        from rtmlib import Wholebody
        if _WB is None:
            _WB = Wholebody(mode="balanced", backend="onnxruntime", device="cpu")
        img = cv2.imread(path)
        kps, sc = _WB(img)
    except Exception as e:
        print("  사람 찾기 건너뜀:", str(e)[:80])
        return [], 0
    H, W = img.shape[:2]
    out, n = [], 0
    for k, s in zip(kps, sc):
        if float(np.mean(s[:17])) < 0.3:              # 사람이 아닌 것(약한 검출)은 뺌
            continue
        n += 1
        groups = {"왼손": list(range(91, 112)), "오른손": list(range(112, 133)),
                  "왼발": [15, 17, 18, 19], "오른발": [16, 20, 21, 22]}
        for name, idx in groups.items():
            pts = [k[j] for j in idx if s[j] > 0.3]
            if len(pts) < 2:
                continue
            pts = np.array(pts)
            cx, cy = pts[:, 0].mean(), pts[:, 1].mean()
            r = max(np.ptp(pts[:, 0]), np.ptp(pts[:, 1]), W * 0.03) * 0.9 + W * 0.02
            out.append((f"사람{n} {name}", (int(cx - r), int(cy - r), int(cx + r), int(cy + r))))
    return out, n


def yolo_hands(path):
    global _YO
    try:
        from ultralytics import YOLO
        if _YO is None:
            _YO = YOLO(YOLO_HAND)
        r = _YO(path, verbose=False, conf=0.3)[0]
        return [tuple(int(v) for v in b) for b in r.boxes.xyxy.tolist()]
    except Exception as e:
        print("  손 찾기(YOLO) 건너뜀:", str(e)[:80])
        return []


def overlap(a, b):
    ix = max(0, min(a[2], b[2]) - max(a[0], b[0]))
    iy = max(0, min(a[3], b[3]) - max(a[1], b[1]))
    sb = max(1, (b[2] - b[0]) * (b[3] - b[1]))
    return ix * iy / sb


def sheet(path, out_dir):
    im = Image.open(path).convert("RGB")
    W, H = im.size
    f = ImageFont.truetype(FONT, 26) if os.path.exists(FONT) else None
    parts, n_people = people_parts(path)
    yh = yolo_hands(path)
    hand_boxes = [b for name, b in parts if "손" in name]
    extra = [b for b in yh if all(overlap(h, b) < 0.3 for h in hand_boxes)]
    crops = [(name, b) for name, b in parts] + [(f"남는 손 {i + 1} (YOLO)", b) for i, b in enumerate(extra)]
    warn = []
    if n_people and len(yh) > 2 * n_people:
        warn.append(f"⚠ 손이 사람 수×2 보다 많음 (사람 {n_people}명, 손 {len(yh)}개)")
    if extra and n_people:
        warn.append(f"⚠ 사람에 안 붙은 손 {len(extra)}개 — 확인")
    tiles = []
    for r in range(2):
        for q in range(3):
            box = (int(W * q / 3 - W * 0.04), int(H * r / 2 - H * 0.05), int(W * (q + 1) / 3 + W * 0.04), int(H * (r + 1) / 2 + H * 0.05))
            box = (max(0, box[0]), max(0, box[1]), min(W, box[2]), min(H, box[3]))
            c = im.crop(box)
            tiles.append((c.resize((c.width * 2, c.height * 2), Image.LANCZOS), f"칸 {r * 3 + q + 1}"))
    tw = max(t.width for t, _ in tiles)
    th = max(t.height for t, _ in tiles)
    cw = 3 * tw
    cell = cw // 4
    rows = (len(crops) + 3) // 4
    head = 60
    out = Image.new("RGB", (cw, head + rows * (cell + 10) + 2 * th + 10), (30, 30, 30))
    d = ImageDraw.Draw(out)
    d.text((10, 12), f"사람 {n_people}명 · YOLO 손 {len(yh)}개   " + ("  ".join(warn) if warn else "경고 없음 — 그래도 조각마다 손가락·발을 셈"),
           fill="orange" if warn else "lightgreen", font=f)
    for i, (name, (x0, y0, x1, y1)) in enumerate(crops):
        c = im.crop((max(0, x0), max(0, y0), min(W, x1), min(H, y1)))
        k = cell / max(c.size)
        c = c.resize((max(1, int(c.width * k)), max(1, int(c.height * k))), Image.LANCZOS)
        x, y = (i % 4) * cell, head + (i // 4) * (cell + 10)
        out.paste(c, (x, y))
        d.text((x + 6, y + 4), name, fill="yellow" if "남는" not in name else "red", font=f, stroke_width=2, stroke_fill="black")
    y0 = head + rows * (cell + 10) + 10
    for i, (c, lab) in enumerate(tiles):
        x, y = (i % 3) * tw, y0 + (i // 3) * th
        out.paste(c, (x, y))
        d.text((x + 6, y + 4), lab, fill="cyan", font=f, stroke_width=2, stroke_fill="black")
    os.makedirs(out_dir, exist_ok=True)
    dst = os.path.join(out_dir, os.path.splitext(os.path.basename(path))[0] + "_손.jpg")
    out.thumbnail((2600, 5000))
    out.save(dst, quality=88)
    print(f"{os.path.basename(path)}: 사람 {n_people}명 · 손·발 조각 {len(parts)}개 · YOLO 손 {len(yh)}개 {' '.join(warn)} → {dst}")
    return dst, warn


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    for p in sys.argv[2:]:
        sheet(p, sys.argv[1])
