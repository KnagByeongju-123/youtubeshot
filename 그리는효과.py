"""그리는 효과 — 그림이 붓으로 그려지듯 나타남 (흰 종이 → 배경·인물 먹선 → 배경 색칠 → 인물 색칠(붓 획))

인물은 굵은 붓이 위에서 아래로 한 획씩(지그재그) 지나가며 드러남 (brush_fields, 사용자 결정 2026-10-31: 한꺼번에 나타나지 않게)
영상 프로그램(shorts_novel_maker_supertonic.py)이 그림이 처음 나타날 때 이 효과를 씀:
  그림 옆에 <그림>.인물.json 이 있으면 켜짐 (인물영역_만들기.py 가 만듦). <그림>.인물.png = 인물 윤곽(흰색)
  인물이 없으면(상자 없음) 배경 전체가 먹선 → 색칠 두 단계로

혼자 시험: python -X utf8 그리는효과.py <그림> <인물 마스크.png 또는 '-'> <결과.mp4> [--초 10] [--fps 24] [--붓없이]
  - 효과 길이는 영상 안에서는 그림이 머무는 시간의 65% (3~7.5초), 나머지는 완성 그림
"""
import sys

import cv2
import numpy as np

PAPER = np.array([255, 255, 255], np.float32)   # 흰 바탕 (사용자 결정: 연한 세피아보다 깔끔)
INK = np.array([28, 26, 30], np.float32)
_FIELDS = {}


def ink_lines(rgb):
    """먹선 세기 0~1: 둘레(흐리게 한 그림)보다 어두운 정도 + 아주 어두운 곳"""
    g = cv2.cvtColor(rgb.astype(np.uint8), cv2.COLOR_RGB2GRAY).astype(np.float32)
    local = cv2.GaussianBlur(g, (0, 0), 6)
    a = np.clip((local - g - 6) / 30, 0, 1)
    a = np.maximum(a, np.clip((70 - g) / 50, 0, 1) * 0.9)
    return cv2.GaussianBlur(a, (0, 0), 0.8)


def _field(seed, w, h, scale, warp_dir=None):
    """나타나는 순서(0~1): 큰 얼룩 잡음 + (있으면) 붓 가는 방향"""
    rng = np.random.default_rng(seed)
    n = rng.random((h // scale + 2, w // scale + 2)).astype(np.float32)
    n = cv2.resize(n, (w, h), interpolation=cv2.INTER_CUBIC)
    n = cv2.GaussianBlur(n, (0, 0), scale / 3)
    fine = cv2.GaussianBlur(rng.random((h, w)).astype(np.float32), (0, 0), 3)
    f = n * 0.75 + fine * 0.25
    if warp_dir is not None:
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        d = xx * warp_dir[0] + yy * warp_dir[1]
        d = (d - d.min()) / (d.max() - d.min())
        f = d * 0.6 + f * 0.4
    return ((f - f.min()) / (f.max() - f.min()))[..., None]


def fields(w, h, seed=0):
    """화면 크기별 나타나는 순서 4가지 (배경 선·배경 색·인물 선·인물 색). 그림마다 seed 를 바꿔 매번 다르게"""
    key = (w, h, seed % 4)
    if key not in _FIELDS:
        s = (seed % 4) * 10
        dirs = [(0.8, 0.6), (-0.8, 0.6), (0.8, -0.4), (-0.6, -0.8)][seed % 4]
        _FIELDS[key] = (_field(1 + s, w, h, max(40, w // 12), dirs), _field(2 + s, w, h, max(60, w // 9)),
                        _field(3 + s, w, h, max(30, w // 21), (0.3, 1.0)), _field(4 + s, w, h, max(40, w // 13)))
        if len(_FIELDS) > 8:
            _FIELDS.pop(next(iter(_FIELDS)))
    return _FIELDS[key]


def brush_fields(M, seed=0):
    """인물 자리를 굵은 붓 획으로 칠해 나가는 순서 (먹선용, 색칠용) — 각각 0~1 (작을수록 먼저). 인물이 없으면 None
    획: 인물 상자를 위에서 아래로 4~10줄, 줄마다 왼→오·오→왼 번갈아(지그재그), 획 경계는 일렁이고 획 머리는 마른 붓처럼 갈라짐"""
    h, w = M.shape
    ys, xs = np.nonzero(M > 0.1)
    if len(ys) < 50:
        return None
    x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    out = []
    for kind in range(2):
        rng = np.random.default_rng(seed * 7 + kind * 101 + 5)
        sw = max(24.0, w / (13 if kind == 0 else 10))                         # 붓 폭 (색칠 붓이 더 굵음)
        R = int(np.clip(round((y1 - y0) / sw), 3, 10))
        sw = (y1 - y0) / R
        wob = cv2.resize(rng.random((6, 10)).astype(np.float32), (w, h), interpolation=cv2.INTER_CUBIC)
        tilt = rng.uniform(-0.12, 0.12) + (0.18 if kind else 0.0)              # 색칠 획은 조금 비스듬히
        edge = cv2.GaussianBlur(rng.random((h, w)).astype(np.float32), (0, 0), max(2.0, w / 260))   # 획 가장자리 붓 자국
        edge = (edge - edge.min()) / (edge.max() - edge.min() + 1e-6)
        yv = yy + (wob - 0.5) * sw * 0.7 + (edge - 0.5) * sw * 0.9 + tilt * (xx - (x0 + x1) / 2)
        k = np.clip(np.floor((yv - y0) / sw), 0, R - 1)
        u = np.clip((xx - x0) / max(1, x1 - x0), 0, 1)
        u = np.where(k % 2 == (kind % 2), u, 1 - u)                            # 지그재그
        bristle = cv2.GaussianBlur(rng.random((h, w)).astype(np.float32), (0, 0), sigmaX=w / 40, sigmaY=1.2)
        bristle = (bristle - bristle.min()) / (bristle.max() - bristle.min() + 1e-6)
        u = np.clip(u + (bristle - 0.5) * 0.22, 0, 1)                          # 마른 붓 결
        f = (k + u * 0.88) / R
        out.append(np.clip(f, 0, 1).astype(np.float32))
    return out


def empty_plate(full, M, with_fog=False):
    """인물 자리를 둘레 배경으로 자연스럽게 이어 메움 (흐림·안개 없이, 사용자 결정 2026-10-31)
    배경 결을 그대로 이어 그리고(inpaint), 경계는 좁고 부드럽게 섞어서 인물이 드러날 때 하얀 테두리·뿌연 자국이 남지 않게"""
    h, w = M.shape
    hole = (M > 0.05).astype(np.uint8) * 255
    if not hole.any():
        return (full.astype(np.uint8), np.zeros((h, w), np.float32)) if with_fog else full.astype(np.uint8)
    k = 2 if max(h, w) > 1200 else 1                                                   # 큰 그림은 절반 크기로 메운 뒤 키움 (빠르게)
    small = cv2.resize(full.astype(np.uint8), (w // k, h // k))
    r = max(3, int(w / 240))                                                           # 인물 윤곽선(먹선)까지 덮을 만큼만 넓힘
    hs = cv2.dilate(cv2.resize(hole, (w // k, h // k)), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * (r // k) + 1, 2 * (r // k) + 1)))
    fill = cv2.inpaint(small, hs, 7, cv2.INPAINT_TELEA).astype(np.float32)
    fill = cv2.resize(fill, (w, h), interpolation=cv2.INTER_CUBIC)
    fill = cv2.GaussianBlur(fill, (0, 0), 1.2)                                         # 메운 자리의 줄무늬만 살짝 정리 (흐림 아님)
    Mf = cv2.dilate(M.astype(np.float32), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1)))
    Mf = cv2.GaussianBlur(Mf, (0, 0), r * 0.8)[..., None]                              # 좁고 부드러운 경계
    out = (full.astype(np.float32) * (1 - Mf) + fill * Mf).astype(np.uint8)
    return (out, Mf[..., 0]) if with_fog else out


def soft_mask(mask_u8):
    """흑백 마스크(0~255) → 0~1, 가장자리 조금 넓히고 부드럽게"""
    m = (mask_u8 > 127).astype(np.uint8)
    m = cv2.dilate(m, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9)))
    return cv2.GaussianBlur(m.astype(np.float32), (0, 0), 3)


def ease(x):
    x = min(1.0, max(0.0, float(x)))
    return x * x * (3 - 2 * x)


def _reveal(f, p, soft=0.06):
    return np.clip((p * (1 + soft) - f) / soft, 0, 1)


def frame(full, plate, M, prog, seed=0, fog=None, brush=None):
    """그리는 중인 한 장면. full: (h, w, 3) uint8 원래 그림, M: (h, w) 0~1 인물(없으면 None), prog: 0~1 (1 이면 완성 그림)
    순서 (사용자 결정 2026-10-31: 인물 자리가 비거나 흐려 보이지 않게, 실제 수묵화처럼)
      인물 있음: 1) 흰 종이에 배경·인물 먹선 (인물 선은 붓 획 순서) 30% → 2) 배경 색 28% (인물은 먹선 스케치 그대로) → 3) 인물 색 (붓 획) 42%
      인물 없음: 먹선 50% → 색 50%
    plate·fog 는 예전 호환용 (fog 가 있으면 인물 경계를 그 범위로 부드럽게)"""
    if prog >= 1:
        return full
    h, w = full.shape[:2]
    f_bl, f_bc, f_pl, f_pc = fields(w, h, seed)
    full_f = full.astype(np.float32)
    person = M is not None and float(M.max()) > 0.5
    T = [0.30, 0.28, 0.42] if person else [0.5, 0.5, 0.0]
    ed = np.cumsum([0] + T)
    p = [ease((prog - ed[k]) / T[k]) if T[k] else 0.0 for k in range(3)]
    lines = ink_lines(full_f)[..., None]
    if person:
        Mm = np.clip(M, 0, 1)[..., None]
        edge = np.clip(fog, 0, 1)[..., None] if fog is not None else Mm               # 인물 경계 (좁고 부드럽게)
        if brush is not None:
            f_pl, f_pc = brush[0][..., None], brush[1][..., None]
        rl = _reveal(f_bl, p[0]) * (1 - Mm) + _reveal(f_pl, p[0], 0.025 if brush is not None else 0.06) * Mm
    else:
        edge = np.zeros((h, w, 1), np.float32)
        rl = _reveal(f_bl, p[0])
    sketch = PAPER * (1 - lines * rl) + INK * (lines * rl)                       # 1) 먹선 (배경 + 인물)
    if person:                                                                    # 인물 자리 종이에 아주 옅은 바탕색 (하얀 실루엣이 아니게)
        tint = cv2.GaussianBlur(full_f, (0, 0), 8)
        sketch = sketch * (1 - 0.18 * edge * rl) + (tint * (1 - lines) + INK * lines) * (0.18 * edge * rl)
    core = np.clip((Mm - 0.5) * 2.5, 0, 1) if person else edge                       # 배경 색은 인물 윤곽선 바로 앞까지 (하얀 띠가 남지 않게)
    cb = _reveal(f_bc, p[1], 0.15) * (1 - core)
    img = sketch * (1 - cb) + full_f * cb                                         # 2) 배경 색 (인물은 스케치로 남음)
    if person:
        cp = _reveal(f_pc, p[2], 0.03 if brush is not None else 0.15) * edge
        img = img * (1 - cp) + full_f * cp                                        # 3) 인물 색 (붓 획)
    return np.clip(img, 0, 255).astype(np.uint8)


def main(a):
    if len(a) < 3:
        print(__doc__)
        return 2
    W, H = 1920, 1080
    sec = float(a[a.index("--초") + 1]) if "--초" in a else 10.0
    fps = int(a[a.index("--fps") + 1]) if "--fps" in a else 24
    full = cv2.resize(cv2.imread(a[0], cv2.IMREAD_COLOR), (W, H), interpolation=cv2.INTER_LANCZOS4)[..., ::-1].copy()
    M = soft_mask(cv2.resize(cv2.imread(a[1], cv2.IMREAD_GRAYSCALE), (W, H))) if a[1] != "-" else None
    plate, fog = empty_plate(full, M if M is not None else np.zeros((H, W), np.float32), with_fog=True)
    brush = brush_fields(M) if M is not None and "--붓없이" not in a else None
    E = min(7.5, max(3.0, sec * 0.65))
    import imageio_ffmpeg
    wr = imageio_ffmpeg.write_frames(a[2], (W, H), fps=fps, codec="libx264", quality=8, macro_block_size=8)
    wr.send(None)
    for i in range(int(sec * fps)):
        wr.send(np.ascontiguousarray(frame(full, plate, M, i / fps / E, fog=fog, brush=brush)))
    wr.close()
    print("OK", a[2])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
