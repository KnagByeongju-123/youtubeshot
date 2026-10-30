"""그리는 효과 — 그림이 붓으로 그려지듯 나타남 (흰 바탕 → 배경 먹선 → 배경 색칠 → 인물 먹선 → 인물 색칠)

영상 프로그램(shorts_novel_maker_supertonic.py)이 그림이 처음 나타날 때 이 효과를 씀:
  그림 옆에 <그림>.인물.json 이 있으면 켜짐 (인물영역_만들기.py 가 만듦). <그림>.인물.png = 인물 윤곽(흰색)
  인물이 없으면(상자 없음) 배경 전체가 먹선 → 색칠 두 단계로

혼자 시험: python -X utf8 그리는효과.py <그림> <인물 마스크.png 또는 '-'> <결과.mp4> [--초 10] [--fps 24]
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


def empty_plate(full, M, with_fog=False):
    """인물 자리를 둘레 배경색으로 메우고 강하게 흐리게(blur) — 경계도 넓게 번져서 인물 자리가 안개처럼 자연스럽게 비어 보임
    (사용자 결정: 하얗게 비운 구멍보다 흐림 효과처럼)"""
    h, w = M.shape
    hole = (M > 0.05).astype(np.uint8) * 255
    if not hole.any():
        return (full.astype(np.uint8), np.zeros((h, w), np.float32)) if with_fog else full.astype(np.uint8)
    small = cv2.resize(full.astype(np.uint8), (w // 4, h // 4))
    hs = cv2.dilate(cv2.resize(hole, (w // 4, h // 4)), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * (w // 160) + 1, 2 * (w // 160) + 1)))
    fill = cv2.inpaint(small, hs, 15, cv2.INPAINT_TELEA)
    fill = cv2.GaussianBlur(fill.astype(np.float32), (0, 0), max(4, w / 120))          # 둘레 색을 흐리게 번진 배경
    fill = cv2.resize(fill, (w, h), interpolation=cv2.INTER_CUBIC)
    plate = fill * 0.85 + PAPER * 0.15
    r = max(5, int(w / 110))                                                           # 인물 윤곽선(먹선)·빠진 투구 끝까지 완전히 덮고
    Mf = cv2.dilate(M.astype(np.float32), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (4 * r + 1, 4 * r + 1)))
    Mf = cv2.GaussianBlur(Mf, (0, 0), r / 2)[..., None]                                # 그 바깥에서 넓게 번지게 (안개처럼)
    out = (full.astype(np.float32) * (1 - Mf) + plate * Mf).astype(np.uint8)
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


def frame(full, plate, M, prog, seed=0, fog=None):
    """그리는 중인 한 장면. full·plate: (h, w, 3) uint8, M: (h, w) 0~1 인물(없으면 None), prog: 0~1 (1 이면 완성 그림)
    인물이 있으면 배경 선 30% → 배경 색 25% → 인물 선 22% → 인물 색 23%, 없으면 선 50% → 색 50%
    fog: 인물 둘레 안개 범위(empty_plate(with_fog=True)) — 인물 색칠 때 이 범위까지 함께 원래 그림으로 (안개 테두리가 갑자기 바뀌지 않게)"""
    if prog >= 1:
        return full
    h, w = full.shape[:2]
    f_bl, f_bc, f_pl, f_pc = fields(w, h, seed)
    full_f, bg = full.astype(np.float32), plate.astype(np.float32)
    person = M is not None and float(M.max()) > 0.5
    T = [0.30, 0.25, 0.22, 0.23] if person else [0.5, 0.5, 0, 0]
    ed = np.cumsum([0] + T)
    p = [ease((prog - ed[k]) / T[k]) if T[k] else 0.0 for k in range(4)]
    bl = ink_lines(bg)[..., None]
    rb = _reveal(f_bl, p[0])
    img = PAPER * (1 - bl * rb) + INK * (bl * rb)                       # 1) 배경 먹선
    cb = _reveal(f_bc, p[1], 0.15)
    img = img * (1 - cb) + bg * cb                                      # 2) 배경 색
    if person:
        Mm = M[..., None]
        pl = ink_lines(full_f)[..., None]
        rp = _reveal(f_pl, p[2]) * Mm
        k_ = 0.55 * rp * (1 - p[3])
        img = img * (1 - k_) + PAPER * k_
        img = img * (1 - pl * rp) + INK * (pl * rp)                     # 3) 인물 먹선
        cp = _reveal(f_pc, p[3], 0.15) * (np.maximum(Mm, fog[..., None]) if fog is not None else Mm)
        img = img * (1 - cp) + full_f * cp                              # 4) 인물 색
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
    E = min(7.5, max(3.0, sec * 0.65))
    import imageio_ffmpeg
    wr = imageio_ffmpeg.write_frames(a[2], (W, H), fps=fps, codec="libx264", quality=8, macro_block_size=8)
    wr.send(None)
    for i in range(int(sec * fps)):
        wr.send(np.ascontiguousarray(frame(full, plate, M, i / fps / E, fog=fog)))
    wr.close()
    print("OK", a[2])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
