"""물감 튀김 전환 — 채널 시그니처 (사용자 제안 2026-11-08: '다음 장면이 물감이 튀듯 나타나고, 가장자리는 빨간 물감')
.supertonic_venv/bin/python -X utf8 페인트전환.py <앞 장면> <뒤 장면> <결과.mp4> [--초 1.0] [--앞초 2] [--뒤초 2] [--색 c8102e] [--seed 7] [--크기 1280x720]
  - 장면은 그림(jpg·png) 또는 영상(mp4). 영상이면 앞 장면은 끝부분, 뒤 장면은 처음부터 씀
  - 물감 덩어리 6~8개가 차례로 '퍽' 하고 튀어 커지며(가장자리는 울퉁불퉁 + 작은 방울·튄 줄기) 뒤 장면이 그 구멍으로 드러남, 마지막엔 화면 전체
  - 구멍 가장자리에 빨간 물감 띠(젖은 물감처럼 안쪽은 진하고 바깥은 살짝 밝게) — 전환이 끝나면 띠도 사라짐
  - 결과 = 앞초(앞 장면) + 전환 + 뒤초(뒤 장면), 24fps H.264"""
import os
import subprocess
import sys

import cv2
import numpy as np

a = sys.argv[1:] if __name__ == "__main__" else []
A, B, OUT = (a + [None, None, None])[:3]
opt = lambda k, d: (a[a.index(k) + 1] if k in a else d)
SEC = float(opt("--초", 1.0))
PRE, POST = float(opt("--앞초", 2.0)), float(opt("--뒤초", 2.0))
COL = opt("--색", "c8102e")
SEED = int(opt("--seed", 7))
W, H = [int(v) for v in opt("--크기", "1280x720").split("x")]
FPS = 24
RED = np.array([int(COL[4:6], 16), int(COL[2:4], 16), int(COL[0:2], 16)], np.float32)   # BGR


def fit(img):
    h, w = img.shape[:2]
    s = max(W / w, H / h)
    img = cv2.resize(img, (int(w * s + 0.5), int(h * s + 0.5)), interpolation=cv2.INTER_AREA)
    y, x = (img.shape[0] - H) // 2, (img.shape[1] - W) // 2
    return img[y:y + H, x:x + W]


def frames_of(path, n, tail):
    """그림이면 같은 장면 n장, 영상이면 끝(tail)이나 처음 n장"""
    if path.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
        im = fit(cv2.imread(path))
        return [im] * n
    cap = cv2.VideoCapture(path)
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if tail:
        cap.set(cv2.CAP_PROP_POS_FRAMES, max(0, total - n))
    out = []
    while len(out) < n:
        ok, fr = cap.read()
        if not ok:
            break
        out.append(fit(fr))
    while len(out) < n:
        out.append(out[-1])
    return out


def noise(rng, scale):
    """부드러운 무작위 지도 (작은 격자를 키움)"""
    g = rng.random((max(2, H // scale), max(2, W // scale))).astype(np.float32)
    return cv2.GaussianBlur(cv2.resize(g, (W, H), interpolation=cv2.INTER_CUBIC), (0, 0), scale * 0.35)


def init(w=None, h=None, seed=None, col=None):
    """물감 덩어리·결 다시 만들기 (다른 프로그램이 크기·무늬를 바꿔 부를 때)"""
    global W, H, SEED, RED, rng, yy, xx, DIAG, n_spl, splats, N1, N2
    if w: W, H = w, h
    if seed is not None: SEED = seed
    if col: RED = np.array([int(col[4:6], 16), int(col[2:4], 16), int(col[0:2], 16)], np.float32)
    rng = np.random.default_rng(SEED)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    DIAG = float(np.hypot(W, H))
    n_spl = int(rng.integers(6, 9))
    splats = []
    for i in range(n_spl):
        cx = W * (0.5 + (rng.random() - 0.5) * 0.85)
        cy = H * (0.5 + (rng.random() - 0.5) * 0.8)
        t0 = 0.6 * i / n_spl + rng.random() * 0.06                    # 차례로 튐
        rmax = DIAG * (0.11 + rng.random() * 0.12)
        ang = np.arctan2(yy - cy, xx - cx)
        k = int(rng.integers(7, 13))                                  # 가장자리 울퉁불퉁 (각도별 반지름 흔들림)
        ph = rng.random(k) * 6.28
        wob = sum(np.sin(ang * (j + 2) + ph[j]) * (0.10 / (j + 1) ** 0.6) for j in range(k))
        spikes = np.clip(np.sin(ang * int(rng.integers(9, 17)) + rng.random() * 6.28), 0, 1) ** 6 * 0.35   # 튄 줄기
        dist = np.hypot(xx - cx, yy - cy)
        drops = []                                                    # 둘레의 작은 방울
        for _ in range(int(rng.integers(8, 16))):
            a_ = rng.random() * 6.28
            dr = 0.9 + rng.random() * 0.7
            drops.append((cx + np.cos(a_) * rmax * dr * 0.6, cy + np.sin(a_) * rmax * dr * 0.6, rmax * (0.03 + rng.random() * 0.05), dr))
        splats.append((t0, rmax, dist, wob, spikes, drops))
    N1 = noise(rng, 24)
    N2 = noise(rng, 7)


init()


def ease_out(x):
    return 1 - (1 - x) ** 3


def mask_at(p):
    """전환 진행 p(0~1) 때 뒤 장면이 보이는 곳 (0~1 부드러운 가장자리)"""
    m = np.zeros((H, W), np.float32)
    edge = (N1 - 0.5) * 0.18 + (N2 - 0.5) * 0.08
    for t0, rmax, dist, wob, spikes, drops in splats:
        q = np.clip((p - t0) / 0.5, 0, 1)
        if q <= 0:
            continue
        r = rmax * ease_out(q) * (1 + 4.0 * max(0.0, p - 0.72) / 0.28)   # 끝무렵엔 화면 전체로 번짐
        f = dist / max(r, 1e-3) - (1 + wob + spikes * min(1, q * 2) + edge)
        m = np.maximum(m, np.clip(-f * r / 3.0, 0, 1))
        for dx, dy, dr_, k_ in drops:
            qq = np.clip((q - 0.15 * k_) / 0.5, 0, 1)
            if qq > 0:
                d2 = np.hypot(xx - dx, yy - dy) / (dr_ * qq) - 1 - edge * 2
                m = np.maximum(m, np.clip(-d2 * dr_ * qq / 2.0, 0, 1))
    if p >= 0.999:
        m[:] = 1
    return m


def blend(fa, fb, p):
    m = mask_at(p)
    mb = (m > 0.5).astype(np.uint8)
    rw = max(4, int(DIAG * 0.022))
    ring = cv2.dilate(mb, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (rw * 2 + 1, rw * 2 + 1))) - mb   # 구멍 바깥 띠
    ring = cv2.GaussianBlur(ring.astype(np.float32), (0, 0), rw * 0.35)
    inner = cv2.GaussianBlur((cv2.dilate(mb, np.ones((3, 3), np.uint8)) - mb).astype(np.float32), (0, 0), 1.2)
    out = fa.astype(np.float32) * (1 - m[..., None]) + fb.astype(np.float32) * m[..., None]
    fade = 1.0 - max(0.0, (p - 0.82) / 0.18)                       # 끝나면 빨간 띠도 사라짐
    shade = 0.75 + 0.5 * N2[..., None]                            # 물감 결 (밝고 어두운 얼룩)
    paint = np.clip(RED[None, None, :] * shade, 0, 255)
    a_ = np.clip(ring * 1.6, 0, 1)[..., None] * fade
    out = out * (1 - a_) + paint * a_
    out = out * (1 - inner[..., None] * 0.6 * fade) + (RED * 0.55)[None, None, :] * inner[..., None] * 0.6 * fade   # 안쪽 진한 선
    return np.clip(out, 0, 255).astype(np.uint8)


if __name__ == "__main__":
    n_pre, n_tr, n_post = int(PRE * FPS), max(2, int(SEC * FPS)), int(POST * FPS)
    fa = frames_of(A, n_pre + n_tr, tail=True)
    fb = frames_of(B, n_tr + n_post, tail=False)
    tmp = OUT + ".frames"
    os.makedirs(tmp, exist_ok=True)
    k = 0
    for i in range(n_pre):
        cv2.imwrite(os.path.join(tmp, "f_%05d.jpg" % k), fa[i], [cv2.IMWRITE_JPEG_QUALITY, 95]); k += 1
    for i in range(n_tr):
        p = (i + 1) / n_tr
        cv2.imwrite(os.path.join(tmp, "f_%05d.jpg" % k), blend(fa[n_pre + i], fb[i], p), [cv2.IMWRITE_JPEG_QUALITY, 95]); k += 1
    for i in range(n_post):
        cv2.imwrite(os.path.join(tmp, "f_%05d.jpg" % k), fb[n_tr + i], [cv2.IMWRITE_JPEG_QUALITY, 95]); k += 1
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-framerate", str(FPS), "-i", os.path.join(tmp, "f_%05d.jpg"),
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "19", OUT], check=True)
    for f in os.listdir(tmp):
        os.remove(os.path.join(tmp, f))
    os.rmdir(tmp)
    print("OK", OUT, k, "장")
