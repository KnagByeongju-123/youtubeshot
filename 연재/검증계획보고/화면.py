"""PPT 슬라이드 그림 → 나레이션 시간에 맞춘 영상 (문장마다 확대 위치 · 강조 상자, 슬라이드 바뀔 때 겹쳐 바뀜)
사용: python 화면.py --미리보기   (문장마다 한 장씩 _미리보기/ 에)
      python 화면.py --영상       (검증계획보고_화면.mp4, 소리 없음)
확대 위치 F = (가운데 x, 가운데 y, 너비) — 슬라이드 크기에 대한 비율, 높이는 16:9 로 자동
강조 상자 H = (x0, y0, x1, y1) 비율, 상자 밖은 살짝 어둡게"""
import json, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw

H = os.path.dirname(os.path.abspath(__file__))
W_, H_ = 1920, 1080
FULL = (0.5, 0.5, 1.0)
R = lambda a, b: (0.04, a, 0.97, b)          # noqa: E731  표의 가로줄 강조

# (슬라이드, 확대, 강조) — 대본 문장 순서대로 (장 제목 줄 제외)
SHOTS = [
    (1, FULL, None),
    (1, (0.42, 0.38, 0.85), (0.05, 0.44, 0.80, 0.52)),
    (1, (0.42, 0.38, 0.85), (0.48, 0.44, 0.80, 0.52)),
    (2, (0.62, 0.50, 0.84), (0.35, 0.10, 0.96, 0.86)),
    (3, (0.27, 0.35, 0.60), (0.04, 0.23, 0.47, 0.41)),
    (3, (0.27, 0.35, 0.60), (0.04, 0.23, 0.47, 0.41)),
    (3, (0.27, 0.50, 0.60), (0.04, 0.42, 0.22, 0.69)),
    (3, (0.27, 0.50, 0.60), (0.24, 0.42, 0.45, 0.69)),
    (3, (0.71, 0.45, 0.55), (0.47, 0.29, 0.95, 0.53)),
    (3, (0.71, 0.45, 0.55), (0.47, 0.53, 0.95, 0.68)),
    (3, (0.50, 0.72, 0.95), (0.04, 0.72, 0.97, 0.91)),
    (4, (0.32, 0.50, 0.70), (0.04, 0.24, 0.31, 0.38)),
    (4, (0.32, 0.50, 0.70), (0.04, 0.38, 0.31, 0.79)),
    (4, (0.64, 0.45, 0.65), (0.33, 0.23, 0.95, 0.70)),
    (4, (0.60, 0.72, 0.75), (0.33, 0.73, 0.95, 0.92)),
    (4, (0.60, 0.72, 0.75), (0.33, 0.73, 0.95, 0.92)),
    (5, (0.50, 0.45, 0.92), R(0.285, 0.565)),
    (5, (0.50, 0.45, 0.92), R(0.285, 0.425)),
    (5, (0.50, 0.45, 0.92), R(0.495, 0.565)),
    (5, (0.50, 0.62, 0.92), R(0.565, 0.845)),
    (5, (0.50, 0.62, 0.92), R(0.635, 0.775)),
    (6, (0.50, 0.45, 0.92), R(0.285, 0.555)),
    (6, (0.50, 0.45, 0.92), R(0.375, 0.465)),
    (6, (0.50, 0.62, 0.92), R(0.555, 0.815)),
    (6, (0.50, 0.62, 0.92), (0.03, 0.84, 0.97, 0.90)),
    (7, (0.50, 0.45, 0.92), R(0.29, 0.535)),
    (7, (0.50, 0.55, 0.92), R(0.535, 0.70)),
    (7, (0.50, 0.62, 0.92), R(0.70, 0.91)),
    (8, (0.32, 0.55, 0.62), (0.04, 0.25, 0.57, 0.83)),
    (8, (0.32, 0.55, 0.62), (0.04, 0.25, 0.57, 0.83)),
    (8, (0.77, 0.40, 0.45), (0.58, 0.22, 0.96, 0.52)),
    (8, (0.77, 0.70, 0.45), (0.58, 0.54, 0.96, 0.91)),
    (8, (0.77, 0.70, 0.45), (0.58, 0.54, 0.96, 0.91)),
    (8, (0.50, 0.62, 0.95), (0.03, 0.85, 0.80, 0.90)),
    (9, (0.30, 0.48, 0.55), (0.04, 0.22, 0.50, 0.73)),
    (9, (0.73, 0.38, 0.50), (0.50, 0.23, 0.97, 0.48)),
    (9, (0.73, 0.38, 0.50), (0.50, 0.23, 0.97, 0.48)),
    (9, (0.73, 0.55, 0.50), (0.50, 0.48, 0.97, 0.71)),
    (9, (0.50, 0.80, 0.95), (0.03, 0.75, 0.97, 0.96)),
    (9, (0.50, 0.80, 0.95), (0.03, 0.75, 0.97, 0.96)),
    (9, (0.50, 0.80, 0.95), (0.03, 0.75, 0.97, 0.96)),
    (9, FULL, None),
]
CH_SLIDE = [1, 2, 3, 4, 5, 8, 9]       # 장 제목 줄이 보이는 동안의 슬라이드 (전체)
ACC = (232, 140, 40)

SL = {i: Image.open(os.path.join(H, '슬라이드', 's-%d.png' % i)).convert('RGB') for i in range(1, 10)}
SW, SH = SL[1].size


def clampF(f):
    cx, cy, w = f
    h = w                                   # 슬라이드가 16:9 라 높이 비율 = 너비 비율
    cx = min(max(cx, w / 2), 1 - w / 2); cy = min(max(cy, h / 2), 1 - h / 2)
    return (cx, cy, w)


def ease(u):
    u = min(max(u, 0.0), 1.0)
    return u * u * (3 - 2 * u)


def view(slide, f, hl, hl_a):
    cx, cy, w = f
    x0, y0 = (cx - w / 2) * SW, (cy - w / 2) * SH
    im = SL[slide].resize((W_, H_), Image.BILINEAR, box=(x0, y0, x0 + w * SW, y0 + w * SH))
    if hl is not None and hl_a > 0.01:
        a = np.asarray(im).astype(np.float32)
        X0 = int((hl[0] - (cx - w / 2)) / w * W_); X1 = int((hl[2] - (cx - w / 2)) / w * W_)
        Y0 = int((hl[1] - (cy - w / 2)) / w * H_); Y1 = int((hl[3] - (cy - w / 2)) / w * H_)
        m = np.ones((H_, W_), np.float32) * (1 - 0.32 * hl_a)
        m[max(0, Y0):max(0, Y1), max(0, X0):max(0, X1)] = 1.0
        a *= m[..., None]
        im = Image.fromarray(a.clip(0, 255).astype(np.uint8))
        d = ImageDraw.Draw(im)
        col = tuple(int(255 + (c - 255) * hl_a) if False else c for c in ACC)
        if hl_a > 0.5:
            d.rounded_rectangle((X0 - 6, Y0 - 6, X1 + 6, Y1 + 6), radius=14, outline=col, width=5)
    return im


def timeline():
    tim = json.load(open(os.path.join(H, '검증계획보고_시간.json'), encoding='utf-8'))
    segs, ch, k, out = tim['segs'], 0, 0, []
    for s in segs:
        if s['kind'] == 'chapter':
            out.append((s['t0'], (CH_SLIDE[ch], FULL, None))); ch += 1
        else:
            out.append((s['t0'], SHOTS[k])); k += 1
    assert k == len(SHOTS), (k, len(SHOTS))
    out[0] = (0.0, out[0][1])
    return out, tim['duration']


def frame_at(t, tl):
    i = max(j for j in range(len(tl)) if tl[j][0] <= t + 1e-9)
    t0, (sl, f, hl) = tl[i]
    f = clampF(f)
    if i > 0:
        _, (psl, pf, phl) = tl[i - 1]; pf = clampF(pf)
    else:
        psl, pf, phl = sl, f, None
    u = (t - t0)
    if psl == sl:                                       # 같은 슬라이드: 확대 위치를 0.7초에 부드럽게 옮김
        e = ease(u / 0.7)
        cf = tuple(pf[j] + (f[j] - pf[j]) * e for j in range(3))
        drift = 1 - 0.015 * ease((u - 0.7) / 8.0)       # 머무는 동안 아주 천천히 다가감
        cf = (cf[0], cf[1], cf[2] * drift); cf = clampF(cf)
        return view(sl, cf, hl, ease((u - 0.35) / 0.4))
    e = ease(u / 0.6)                                   # 슬라이드가 바뀜: 겹쳐 바뀜
    a = view(psl, pf, phl, 1 - e)
    b = view(sl, f, hl, ease((u - 0.5) / 0.4))
    return Image.blend(a, b, e) if e < 1 else b


if __name__ == '__main__':
    if '--미리보기' in sys.argv:
        od = os.path.join(H, '_미리보기'); os.makedirs(od, exist_ok=True)
        for k, (sl, f, hl) in enumerate(SHOTS):
            view(sl, clampF(f), hl, 1.0).resize((960, 540)).save(os.path.join(od, '%02d.png' % (k + 1)))
        print(len(SHOTS), '장')
    if '--영상' in sys.argv:
        tl, dur = timeline()
        out = os.path.join(H, '검증계획보고_화면.mp4')
        p = subprocess.Popen(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', '%dx%d' % (W_, H_),
                              '-r', '24', '-i', '-', '-c:v', 'libx264', '-crf', '18', '-preset', 'medium', '-pix_fmt', 'yuv420p', out],
                             stdin=subprocess.PIPE)
        n = int(dur * 24) + 1
        for fr in range(n):
            p.stdin.write(frame_at(fr / 24.0, tl).tobytes())
            if fr % 600 == 0: print(fr, '/', n, flush=True)
        p.stdin.close(); p.wait(); print('OK', out)
