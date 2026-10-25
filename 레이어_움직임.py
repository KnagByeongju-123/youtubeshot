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
        lay.append((obj, ((bb[0] + bb[2]) / 2, (bb[1] + bb[3]) / 2), parse(mv)))
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
