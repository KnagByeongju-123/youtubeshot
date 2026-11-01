"""그림판 자르기 — 제미나이 등에서 받은 '여러 장면이 한 장에 칸칸이 든 그림'을 칸마다 잘라 장면 그림으로 (사용자 결정 2026-11-01)

  python -X utf8 그림판_자르기.py <그림판.png> <저장폴더> --칸 8x5 [--시작 1] [--이름 c] [--다시그리기 <주문서.json>]
  - --칸 가로x세로 (예: 8x5 = 40칸). 칸 사이 흰 줄·검은 줄(여백)은 자동으로 찾아 빼고 자름 (못 찾으면 똑같이 나눔)
  - 칸 순서: 왼쪽 위부터 오른쪽으로, 줄이 끝나면 다음 줄 → c01, c02 … (--시작 으로 번호 시작, --이름 으로 앞글자)
  - 자른 그림은 16:9 로 가운데 맞춰 1600×900 으로 키워 저장 (작은 칸은 흐릿함)
  - --다시그리기 <주문서.json>: 자른 칸을 '구도 기준 그림'으로 넣어 FLUX.2 klein 으로 1024×576 고화질로 다시 그리는 주문서를 만듦
      (장면 설명은 <저장폴더>/설명.txt 에 한 줄씩 'c01 설명' 으로 적어 두면 붙임, 캐릭터 시트는 --시트 경로1,경로2)
      → .sd_venv/bin/python klein_worker.py models/FLUX2_klein_4B <주문서.json> <저장폴더>
"""
import json
import os
import sys

import numpy as np
from PIL import Image


def gutters(profile, n, size):
    """한 방향 밝기 줄(평균)에서 칸 경계 n-1 개를 찾음. 여백 줄(아주 밝거나 아주 어둡고 고른 곳) 가운데를 경계로, 못 찾으면 등분"""
    cuts = []
    for k in range(1, n):
        guess = size * k / n
        lo, hi = int(guess - size / n * 0.25), int(guess + size / n * 0.25)
        seg = profile[lo:hi]
        flat = np.where((seg["std"] < 12) & ((seg["mean"] > 225) | (seg["mean"] < 30)))[0]
        if len(flat):
            runs, start = [], flat[0]
            for a, b in zip(flat, flat[1:]):
                if b != a + 1:
                    runs.append((start, a))
                    start = b
            runs.append((start, flat[-1]))
            s, e = min(runs, key=lambda r: abs((r[0] + r[1]) / 2 + lo - guess))
            cuts.append((lo + s, lo + e + 1))
        else:
            g = int(round(guess))
            cuts.append((g, g))
    bounds, prev = [], 0
    for s, e in cuts:
        bounds.append((prev, s))
        prev = e
    bounds.append((prev, size))
    return bounds


def trim(im):
    """칸 가장자리에 남은 흰·검은 여백 줄을 깎음"""
    a = np.asarray(im.convert("L"), np.float32)
    def flat(v):
        return v.std() < 10 and (v.mean() > 225 or v.mean() < 30)
    t_, b_, l_, r_ = 0, a.shape[0], 0, a.shape[1]
    while t_ < b_ - 10 and flat(a[t_, l_:r_]):
        t_ += 1
    while b_ > t_ + 10 and flat(a[b_ - 1, l_:r_]):
        b_ -= 1
    while l_ < r_ - 10 and flat(a[t_:b_, l_]):
        l_ += 1
    while r_ > l_ + 10 and flat(a[t_:b_, r_ - 1]):
        r_ -= 1
    return im.crop((l_, t_, r_, b_))


def fit169(im, w=1600, h=900):
    im = trim(im)
    iw, ih = im.size
    if iw / ih > w / h:
        nw = int(ih * w / h)
        im = im.crop(((iw - nw) // 2, 0, (iw - nw) // 2 + nw, ih))
    else:
        nh = int(iw * h / w)
        im = im.crop((0, (ih - nh) // 2, iw, (ih - nh) // 2 + nh))
    return im.resize((w, h), Image.LANCZOS)


def main(a):
    if len(a) < 2 or "--칸" not in a:
        print(__doc__)
        return 2
    src, out = a[0], a[1]
    cols, rows = map(int, a[a.index("--칸") + 1].lower().split("x"))
    start = int(a[a.index("--시작") + 1]) if "--시작" in a else 1
    pre = a[a.index("--이름") + 1] if "--이름" in a else "c"
    os.makedirs(out, exist_ok=True)
    im = Image.open(src).convert("RGB")
    g = np.asarray(im.convert("L"), np.float32)
    H, W = g.shape
    colp = np.zeros(W, dtype=[("mean", "f4"), ("std", "f4")])
    colp["mean"], colp["std"] = g.mean(0), g.std(0)
    rowp = np.zeros(H, dtype=[("mean", "f4"), ("std", "f4")])
    rowp["mean"], rowp["std"] = g.mean(1), g.std(1)
    xs, ys = gutters(colp, cols, W), gutters(rowp, rows, H)
    names = []
    for r, (y0, y1) in enumerate(ys):
        for c, (x0, x1) in enumerate(xs):
            n = start + r * cols + c
            name = f"{pre}{n:02d}"
            pad = 2
            piece = im.crop((x0 + pad, y0 + pad, x1 - pad, y1 - pad))
            fit169(piece).save(os.path.join(out, name + ".png"))
            names.append((name, piece.size))
    print(f"{len(names)}칸 → {out}  (한 칸 원래 크기 약 {names[0][1][0]}×{names[0][1][1]})")
    if "--다시그리기" in a:
        job = a[a.index("--다시그리기") + 1]
        desc = {}
        dp = os.path.join(out, "설명.txt")
        if os.path.exists(dp):
            for line in open(dp, encoding="utf-8"):
                if line.strip() and " " in line:
                    k, v = line.strip().split(" ", 1)
                    desc[k] = v
        sheets = a[a.index("--시트") + 1].split(",") if "--시트" in a else []
        style = a[a.index("--화풍") + 1] if "--화풍" in a else "clean 2D illustration, crisp line art, soft cel shading, natural colors"
        items = []
        for name, _ in names:
            items.append({"id": name, "width": 1024, "height": 576, "seed": 900 + len(items),
                          "refs": [os.path.abspath(os.path.join(out, name + ".png"))] + [os.path.abspath(s) for s in sheets],
                          "prompt": f"{style}. Redraw reference image 1 at high quality, keeping exactly the same composition, camera angle, characters, poses and colors"
                                    + (", characters look exactly like the character sheets in the other reference images" if sheets else "")
                                    + (f". Scene: {desc[name]}" if name in desc else "")
                                    + ". Exactly two arms and two legs per person. Full-bleed image, no border, no text, no letters."})
        json.dump({"items": items, "ref_max_area": 230000}, open(job, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("다시그리기 주문서:", job, len(items), "장")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
