"""손 확대 검수 — 그림 속 손을 찾아 크게 잘라 한 장에 모음 (손가락·손 수를 세기 쉽게) (.sd_venv 에서 실행)

  .sd_venv/bin/python 손_확대검수.py <결과폴더> <그림1.png> [그림2.png ...]   → <결과폴더>/<그림이름>_손.jpg

- 1) 손 찾기(MediaPipe Hand Landmarker, models/hand_landmarker.task): 찾은 손마다 넉넉히 잘라 3배 가까이 키움 (왼손·오른손 표시)
- 2) 손 찾기는 그림(특히 수채화·유화)에서 손을 놓치기도 함 → 그림을 2×3 칸으로 나눠 2배로 키운 조각도 함께 붙임 (놓친 손도 보이게)
- 사용자 결정(2026-10-25): 손가락 검수는 전체를 줄여 보지 말고 좌우 손을 확대해서 셈. 손가락 5개가 아니면 불합격
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
MODEL = os.path.join(HERE, "models", "hand_landmarker.task")
FONT = "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf"


def hand_boxes(path):
    """찾은 손마다 (x0,y0,x1,y1, '왼손'/'오른손') — 못 쓰면 빈 목록"""
    try:
        import mediapipe as mp
        from mediapipe.tasks import python as mpt
        from mediapipe.tasks.python import vision
        opt = vision.HandLandmarkerOptions(base_options=mpt.BaseOptions(model_asset_path=MODEL), num_hands=16,
                                           min_hand_detection_confidence=0.15, min_hand_presence_confidence=0.15)
        det = vision.HandLandmarker.create_from_options(opt)
        im = mp.Image.create_from_file(path)
        r = det.detect(im)
        W, H = im.width, im.height
        out = []
        for lm, hd in zip(r.hand_landmarks, r.handedness):
            xs, ys = [p.x * W for p in lm], [p.y * H for p in lm]
            cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
            s = max(max(xs) - min(xs), max(ys) - min(ys), 40) * 1.25           # 손보다 넉넉하게
            name = "오른손" if hd[0].category_name == "Left" else "왼손"         # 그림 속 사람 기준(거울상 보정)
            out.append((int(cx - s), int(cy - s), int(cx + s), int(cy + s), name))
        return out
    except Exception as e:
        print("  손 찾기 건너뜀:", str(e)[:80])
        return []


def sheet(path, out_dir):
    im = Image.open(path).convert("RGB")
    W, H = im.size
    f = ImageFont.truetype(FONT, 26) if os.path.exists(FONT) else None
    crops = []
    for i, (x0, y0, x1, y1, name) in enumerate(hand_boxes(path)):
        c = im.crop((max(0, x0), max(0, y0), min(W, x1), min(H, y1)))
        k = 640 / max(c.size)
        crops.append((c.resize((max(1, int(c.width * k)), max(1, int(c.height * k))), Image.LANCZOS), f"손 {i + 1} ({name})"))
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
    hand_rows = (len(crops) + 2) // 3
    out = Image.new("RGB", (cw, hand_rows * 660 + 2 * th + 10), (30, 30, 30))
    d = ImageDraw.Draw(out)
    for i, (c, lab) in enumerate(crops):
        x, y = (i % 3) * (cw // 3), (i // 3) * 660
        out.paste(c, (x, y))
        d.text((x + 6, y + 4), lab, fill="yellow", font=f, stroke_width=2, stroke_fill="black")
    y0 = hand_rows * 660 + 10
    for i, (c, lab) in enumerate(tiles):
        x, y = (i % 3) * tw, y0 + (i // 3) * th
        out.paste(c, (x, y))
        d.text((x + 6, y + 4), lab, fill="cyan", font=f, stroke_width=2, stroke_fill="black")
    os.makedirs(out_dir, exist_ok=True)
    dst = os.path.join(out_dir, os.path.splitext(os.path.basename(path))[0] + "_손.jpg")
    out.thumbnail((2600, 4000))
    out.save(dst, quality=88)
    print(f"{os.path.basename(path)}: 찾은 손 {len(crops)}개 → {dst}")
    return dst


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    for p in sys.argv[2:]:
        sheet(p, sys.argv[1])
