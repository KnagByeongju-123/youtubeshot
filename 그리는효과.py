"""그리는 효과 — 그림 한 장이 붓으로 그려지듯 나타나는 짧은 영상 (배경 먹선 → 배경 색칠 → 인물 먹선 → 인물 색칠)

  python -X utf8 그리는효과.py <완성 그림> <빈 배경 그림> <결과.mp4> [--초 10] [--fps 24]
  - 빈 배경 그림: 같은 그림에서 인물만 지운 것 (klein 으로 '인물을 지우고 나머지는 그대로' 고친 그림)
  - 인물 자리 = 완성 그림과 빈 배경이 크게 다른 곳 (가장 큰 덩어리들만). 인물 밖 배경은 완성 그림 그대로 써서 마지막 장면이 원래 그림과 똑같음
  - 먹선 = 그림에서 둘레보다 어두운 가는 선. 종이(화선지 색) 위에 먹선이 붓 가는 방향으로 번져 나타나고, 색은 물감처럼 얼룩지며 퍼짐
  - 결과와 함께 <결과>_인물영역.png (인물로 잡힌 곳 확인용)
"""
import sys

import cv2
import numpy as np

W, H = 1920, 1080
PAPER = np.array([238, 233, 220], np.float32)


def load(p):
    im = cv2.imread(p, cv2.IMREAD_COLOR)
    return cv2.resize(im, (W, H), interpolation=cv2.INTER_LANCZOS4)[..., ::-1].astype(np.float32)


def ink_lines(rgb):
    """먹선 세기 0~1: 둘레(흐리게 한 그림)보다 어두운 정도 + 아주 어두운 곳"""
    g = cv2.cvtColor(rgb.astype(np.uint8), cv2.COLOR_RGB2GRAY).astype(np.float32)
    local = cv2.GaussianBlur(g, (0, 0), 6)
    a = np.clip((local - g - 6) / 30, 0, 1)
    a = np.maximum(a, np.clip((70 - g) / 50, 0, 1) * 0.9)
    return cv2.GaussianBlur(a, (0, 0), 0.8)


def field(seed, scale, warp_dir=None):
    """나타나는 순서(0~1): 큰 얼룩 잡음 + (있으면) 붓 가는 방향"""
    rng = np.random.default_rng(seed)
    n = rng.random((H // scale + 2, W // scale + 2)).astype(np.float32)
    n = cv2.resize(n, (W, H), interpolation=cv2.INTER_CUBIC)
    n = cv2.GaussianBlur(n, (0, 0), scale / 3)
    fine = cv2.GaussianBlur(rng.random((H, W)).astype(np.float32), (0, 0), 3)
    f = n * 0.75 + fine * 0.25
    if warp_dir is not None:
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        d = (xx * warp_dir[0] + yy * warp_dir[1])
        d = (d - d.min()) / (d.max() - d.min())
        f = d * 0.6 + f * 0.4
    return (f - f.min()) / (f.max() - f.min())


def person_mask(full, bg):
    d = np.abs(full - bg).mean(2)
    d = cv2.GaussianBlur(d, (0, 0), 6)
    m = (d > 28).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (41, 41)))
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15)))
    n, lab, stats, _ = cv2.connectedComponentsWithStats(m)
    keep = np.zeros_like(m)
    big = sorted(range(1, n), key=lambda i: -stats[i, cv2.CC_STAT_AREA])
    for i in big[:3]:
        if stats[i, cv2.CC_STAT_AREA] > W * H * 0.01:
            keep[lab == i] = 1
    # 구멍 메우기 (외곽선 안쪽 전부)
    cnts, _ = cv2.findContours(keep, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    fill = np.zeros_like(keep)
    cv2.drawContours(fill, cnts, -1, 1, -1)
    fill = cv2.dilate(fill, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9)))
    return cv2.GaussianBlur(fill.astype(np.float32), (0, 0), 4)


def ease(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


def reveal(f, p, soft=0.06):
    """f 가 진행도 p 보다 작은 곳부터 나타남 (가장자리는 부드럽게)"""
    return np.clip((p * (1 + soft) - f) / soft, 0, 1)


def main(a):
    if len(a) < 3:
        print(__doc__)
        return 2
    sec = float(a[a.index("--초") + 1]) if "--초" in a else 10.0
    fps = int(a[a.index("--fps") + 1]) if "--fps" in a else 24
    full, plate = load(a[0]), load(a[1])
    M = person_mask(full, plate)[..., None]
    cv2.imwrite(a[2][:-4] + "_인물영역.png", (np.concatenate([full * (0.35 + 0.65 * M)], 1)[..., ::-1]).astype(np.uint8))
    bg = full * (1 - M) + plate * M                        # 인물 밖은 원래 그림 그대로
    paper = np.broadcast_to(PAPER, full.shape)
    bl, pl = ink_lines(bg)[..., None], ink_lines(full)[..., None]
    INK = np.array([28, 26, 30], np.float32)
    f_bl, f_bc = field(1, 160, (0.8, 0.6))[..., None], field(2, 220)[..., None]
    f_pl, f_pc = field(3, 90, (0.3, 1.0))[..., None], field(4, 150)[..., None]
    # 시간표 (비율): 배경 먹선 / 배경 색 / 인물 먹선 / 인물 색 / 완성 머묾
    T = np.array([0.24, 0.20, 0.20, 0.20, 0.16]) * sec
    edges = np.concatenate([[0], np.cumsum(T)])
    import imageio_ffmpeg
    wr = imageio_ffmpeg.write_frames(a[2], (W, H), fps=fps, codec="libx264", quality=8, macro_block_size=8,
                                     output_params=["-pix_fmt", "yuv420p"])
    wr.send(None)
    n = int(sec * fps)
    for i in range(n):
        t = i / fps
        p = [ease((t - edges[k]) / T[k]) for k in range(4)]
        # 1) 배경 먹선: 종이 위에 선이 번져 나타남
        rb = reveal(f_bl, p[0])
        img = paper * (1 - bl * rb) + INK * (bl * rb)
        # 2) 배경 색: 물감이 얼룩지며 퍼짐 (먹선은 위에 남았다가 색 그림 속 선으로)
        cb = reveal(f_bc, p[1], 0.15)
        img = img * (1 - cb) + bg * cb
        # 3) 인물 먹선: 배경 위 인물 자리에 종이를 살짝 깔고 선
        rp = reveal(f_pl, p[2]) * M
        lay = img * (1 - 0.55 * rp * (1 - p[3])) + paper * (0.55 * rp * (1 - p[3]))
        img = lay * (1 - pl * rp) + INK * (pl * rp)
        # 4) 인물 색
        cp = reveal(f_pc, p[3], 0.15) * M
        img = img * (1 - cp) + full * cp
        # 5) 완성: 아주 천천히 확대
        if t > edges[4]:
            z = 1 + 0.03 * ease((t - edges[4]) / T[4])
            img = cv2.resize(img, None, fx=z, fy=z)
            y0, x0 = (img.shape[0] - H) // 2, (img.shape[1] - W) // 2
            img = img[y0:y0 + H, x0:x0 + W]
        wr.send(np.ascontiguousarray(np.clip(img, 0, 255).astype(np.uint8)))
    wr.close()
    print("OK", a[2])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
