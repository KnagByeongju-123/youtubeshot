"""레이어 움직임(2.5D 모션 코믹) — 배경은 천천히, 누끼 딴 인물·사물 레이어는 내용에 맞게 따로 움직이는 짧은 영상 (애니메이션 연재 전용)

  python 레이어_움직임.py <배경.png> <결과.mp4> <레이어.png>=<움직임> [<레이어2.png>=<움직임> ...] [--초 6] [--배경 확대|축소|왼쪽|오른쪽|고정]

- 배경: 인물을 빼고 빈자리를 채운 그림 (그림 크기 그대로). 레이어: 같은 크기의 투명 png (누끼 딴 것만 남김)
- 움직임: 날아감(오른쪽 위로 멀어지며 작아짐) · 다가옴(커지며 앞으로) · 떨어짐 · 솟아오름 · 확대(천천히 커짐) · 흔들림 · 둥실(위아래로 살짝)
  '날아감:dx,dy,크기' 처럼 직접 줄 수도 있음 (dx·dy 는 그림 폭·높이에 대한 비율, 크기는 끝 배율)  예) 날아감:0.25,-0.18,0.55
- 결과는 1920×1080 · 24fps (ffmpeg). 규칙(사용자 결정): 이 기능은 애니메이션(연재 애니판)에서만 씀, 다큐·실사에는 쓰지 않음
"""
import math
import subprocess
import sys

import numpy as np
from PIL import Image

W, H, FPS = 1920, 1080, 24
PRESET = {   # (끝 위치 이동 dx, dy(비율), 끝 크기, 회전(도), 흔들림)
    "날아감": (0.22, -0.16, 0.6, -4, 0),
    "다가옴": (0.0, 0.04, 1.35, 0, 0),
    "떨어짐": (0.0, 0.25, 1.0, 6, 0),
    "솟아오름": (0.0, -0.12, 1.08, 0, 0),
    "확대": (0.0, 0.0, 1.15, 0, 0),
    "흔들림": (0.0, 0.0, 1.0, 0, 1),
    "둥실": (0.0, 0.0, 1.0, 0, 2),
}


def ease(t):
    return t * t * (3 - 2 * t)


def parse(spec):
    name, _, nums = spec.partition(":")
    dx, dy, sc, rot, shake = PRESET.get(name, PRESET["확대"])
    if nums:
        v = [float(x) for x in nums.split(",")]
        dx, dy, sc = (v + [dx, dy, sc][len(v):])[:3]
    return dx, dy, sc, rot, shake


def edge_safe(bb, size, mv, tol=3):
    """누끼가 그림 가장자리에서 잘린 채(가장자리에 닿음) 움직이다가 잘린 단면이 화면 안으로 들어오면 → 확대로 바꿈
    (사용자 규칙 2026-10-25: 아랫부분이 잘린 누끼를 위로 올리면 잘린 곳이 보임 — 빼거나 확대)
    움직이는 동안(이동·크기·회전·흔들림)의 가장자리 위치를 계산해, 닿아 있던 쪽 가장자리가 2px 넘게 안쪽으로 들어오는지 봄
    bb: 누끼 테두리 상자 (x0,y0,x1,y1), size: 그림 (폭,높이), mv: parse() 결과 → (mv, 바꿨으면 드러나는 쪽 이름 / 아니면 "")"""
    W, H = size
    dx, dy, sc, rot, shake = mv
    ow, oh = bb[2] - bb[0], bb[3] - bb[1]
    ox, oy = (bb[0] + bb[2]) / 2, (bb[1] + bb[3]) / 2
    jx, jy = {1: (6, 5), 2: (0, 10)}.get(shake, (0, 0))      # 흔들림 최대 폭(px)
    touch = {"아래": bb[3] >= H - tol, "위": bb[1] <= tol, "왼쪽": bb[0] <= tol, "오른쪽": bb[2] >= W - tol}
    bad = set()
    for i in range(21):
        e = i / 20
        k = 1 + (sc - 1) * e
        a = math.radians(rot * e)
        w, h = ow * k, oh * k
        cx, cy = ox + dx * W * e, oy + dy * H * e
        ry = h / 2 * math.cos(a) - w / 2 * abs(math.sin(a))      # 회전하면 모서리가 들려 단면이 드러남
        rx = w / 2 * math.cos(a) - h / 2 * abs(math.sin(a))
        if touch["아래"] and cy + ry - jy < bb[3] - 2:
            bad.add("아래")
        if touch["위"] and cy - ry + jy > bb[1] + 2:
            bad.add("위")
        if touch["왼쪽"] and cx - rx + jx > bb[0] + 2:
            bad.add("왼쪽")
        if touch["오른쪽"] and cx + rx - jx < bb[2] - 2:
            bad.add("오른쪽")
    if bad:
        return PRESET["확대"], "·".join(sorted(bad))
    return mv, ""


def main():
    a = sys.argv[1:]
    if len(a) < 3:
        sys.exit(__doc__)
    secs = float(a[a.index("--초") + 1]) if "--초" in a else 6.0
    bgmode = a[a.index("--배경") + 1] if "--배경" in a else "확대"
    bg_path, out = a[0], a[1]
    layers = [x for x in a[2:] if "=" in x and not x.startswith("--")]
    bg = Image.open(bg_path).convert("RGB")
    bg = bg.resize((W, H), Image.LANCZOS)
    big = bg.resize((int(W * 1.12), int(H * 1.12)), Image.LANCZOS)    # 배경을 조금 크게 두고 잘라 움직임
    lay = []
    for spec in layers:
        p, _, mv = spec.partition("=")
        im = Image.open(p).convert("RGBA").resize((W, H), Image.LANCZOS)
        bb = im.getbbox() or (0, 0, W, H)
        obj = im.crop(bb)
        m_, cut = edge_safe(bb, (W, H), parse(mv))
        if cut:
            print(f"  {p}: {cut} 가장자리에서 잘린 누끼라 '{mv}' 대신 확대로 움직임")
        lay.append((obj, ((bb[0] + bb[2]) / 2, (bb[1] + bb[3]) / 2), m_))
    n = int(secs * FPS)
    ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                           "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-preset", "medium", out], stdin=subprocess.PIPE)
    BW, BH = big.size
    for f in range(n):
        t = f / max(1, n - 1)
        e = ease(t)
        z = {"확대": 1 + 0.08 * e, "축소": 1.08 - 0.08 * e}.get(bgmode, 1.0)    # 배경 크기(1 = 기본 화면)
        cw, ch = W / z * (BW / W) / 1.12, H / z * (BH / H) / 1.12
        cx = BW / 2 + {"왼쪽": -1, "오른쪽": 1}.get(bgmode, 0) * (BW - cw) / 2 * (e - 0.5) * 2 * 0.9
        frame = big.crop((int(cx - cw / 2), int(BH / 2 - ch / 2), int(cx + cw / 2), int(BH / 2 + ch / 2))).resize((W, H), Image.BILINEAR)
        frame = frame.convert("RGBA")
        for obj, (ox, oy), (dx, dy, sc, rot, shake) in lay:
            s = 1 + (sc - 1) * e
            x = ox + dx * W * e
            y = oy + dy * H * e
            if shake == 1:
                x += math.sin(f * 1.7) * 6 * (1 - t)
                y += math.cos(f * 2.3) * 5 * (1 - t)
            elif shake == 2:
                y += math.sin(t * math.pi * 2) * 10
            o = obj.resize((max(1, int(obj.width * s)), max(1, int(obj.height * s))), Image.BICUBIC)
            if rot:
                o = o.rotate(rot * e, resample=Image.BICUBIC, expand=True)
            frame.alpha_composite(o, (int(x - o.width / 2), int(y - o.height / 2)))
        ff.stdin.write(np.asarray(frame.convert("RGB")).tobytes())
    ff.stdin.close()
    ff.wait()
    print(out, f"{secs}초", "레이어", len(lay))


if __name__ == "__main__":
    main()
