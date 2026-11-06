"""애니 그림 한 장을 부위별로 움직이기 시험 (라이브2D 느낌, 약 10초) — 사용자 요청 2026-11-06 '애니풍인데 움직여야 해'
python -X utf8 평면애니/애니_움직이기_시험.py <그림> <결과.mp4>
움직이는 것: 눈 깜빡임 · 말하듯 입 열고 닫기 · 머리카락 흔들림 · 로봇 손 떨림 · 로봇 눈빛 깜빡임 · 떠다니는 먼지 빛 · 아주 느린 확대
(부위 자리는 「두 번째 새벽」 c34 그림 기준으로 손으로 적음 — 다른 그림이면 자리만 바꿈)"""
import math
import subprocess
import sys

import cv2
import numpy as np

SRC, OUT = sys.argv[1], sys.argv[2]
FPS, SEC, OW, OH = 24, 10.0, 1920, 1080
img = cv2.cvtColor(cv2.imread(SRC), cv2.COLOR_BGR2RGB).astype(np.float32)
H, W = img.shape[:2]
SKIN = img[388:392, 310:314].reshape(-1, 3).mean(0)          # 볼 피부색
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)


def soft_mask(x0, y0, x1, y1, feather=12):
    m = np.zeros((H, W), np.float32)
    m[y0:y1, x0:x1] = 1
    return cv2.GaussianBlur(m, (0, 0), feather)


# 부위 자리 (원본 1024×576 기준)
HAIR = soft_mask(40, 430, 250, 576, 25) * np.clip((xx - 40) / 1, 0, 1)
HAIR *= np.clip((576 - yy) / 140, 0.2, 1.0) * 0 + np.clip((yy - 420) / 150, 0, 1)     # 머리끝(아래)일수록 많이 흔들림
HAND = soft_mask(405, 345, 505, 435, 14)
EYES = [((288, 383), 15, 13, -25), ((331, 358), 11, 11, -25)]   # (가운데, 가로 반지름, 세로 반지름, 기울기°)
MOUTH = ((337, 409), 7, 7)
REYE = (597, 95)
rng = np.random.default_rng(4)
DUST = [(rng.uniform(0, W), rng.uniform(0, H), rng.uniform(0.6, 2.2), rng.uniform(4, 14), rng.uniform(0, 6.28)) for _ in range(45)]


def blink_amount(t):
    """0 = 뜬 눈, 1 = 감은 눈 (2.2초·5.6초·8.4초에 깜빡)"""
    a = 0.0
    for tb in (2.2, 5.6, 8.4):
        d = abs(t - tb)
        if d < 0.12:
            a = max(a, 1 - d / 0.12)
    return a


def talking(t):
    """말하듯 입: 3~7초 사이에 열렸다 닫힘"""
    if 3.0 <= t <= 7.0:
        return 0.5 + 0.5 * math.sin(t * 17) * math.sin(t * 5.3)
    return 1.0                                                  # 원래 그림은 놀라서 입을 벌린 모습


def frame(t):
    # 1) 머리카락·로봇 손: 부드럽게 휘게(리맵)
    dx = HAIR * (3.2 * np.sin(t * 2.1 + yy / 38.0)) + HAND * (-2.5 + 2.5 * math.sin(t * 1.3))
    dy = HAIR * (1.0 * np.sin(t * 1.7 + xx / 50.0)) + HAND * (1.5 * math.sin(t * 1.3 + 1))
    out = cv2.remap(img, xx - dx, yy - dy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    # 2) 눈 깜빡임: 피부색 눈꺼풀이 위에서 내려오고 가운데 속눈썹 선
    b = blink_amount(t)
    if b > 0:
        for (cx, cy), rx, ry, ang in EYES:
            lid = np.zeros((H, W), np.uint8)
            cv2.ellipse(lid, (cx, cy), (rx + 2, int((ry + 2) * b) + 1), ang, 180, 360, 255, -1)
            cv2.ellipse(lid, (cx, cy), (rx + 2, ry + 2), ang, 0, 360, 255 if b > 0.85 else 0, -1)
            m = cv2.GaussianBlur(lid.astype(np.float32) / 255, (0, 0), 1.2)[..., None]
            out = out * (1 - m) + SKIN * m
            if b > 0.6:
                lash = np.zeros((H, W), np.uint8)
                cv2.ellipse(lash, (cx, cy + int(ry * 0.2)), (rx + 1, int(ry * 0.35)), ang, 10, 170, 255, 2)
                lm = cv2.GaussianBlur(lash.astype(np.float32) / 255, (0, 0), 0.7)[..., None]
                out = out * (1 - lm) + np.array([60, 30, 25], np.float32) * lm
    # 3) 입: 닫히는 만큼 피부색으로 덮고 작은 선
    o = talking(t)
    if o < 0.98:
        (mx, my), mrx, mry = MOUTH
        mm = np.zeros((H, W), np.uint8)
        cv2.ellipse(mm, (mx, my), (mrx + 1, int((mry + 1) * (1 - o)) + 1), -20, 0, 360, 255, -1)
        m = cv2.GaussianBlur(mm.astype(np.float32) / 255, (0, 0), 1.0)[..., None]
        out = out * (1 - m) + SKIN * m
        ln = np.zeros((H, W), np.uint8)
        cv2.line(ln, (mx - mrx, my + 2), (mx + mrx, my - 2), 255, 1)
        lm = cv2.GaussianBlur(ln.astype(np.float32) / 255, (0, 0), 0.6)[..., None] * (1 - o)
        out = out * (1 - lm) + np.array([150, 70, 70], np.float32) * lm
    # 4) 로봇 눈빛: 살아 있는 듯 밝아졌다 어두워짐
    g = 0.5 + 0.5 * math.sin(t * 3.0)
    glow = np.exp(-(((xx - REYE[0]) ** 2 + (yy - REYE[1]) ** 2) / (2 * 16.0 ** 2)))[..., None]
    out = out + glow * np.array([60, 150, 255], np.float32) * (0.25 + 0.55 * g)
    # 5) 떠다니는 먼지 빛
    for (x0, y0, sp, r, ph) in DUST:
        x = (x0 + 6 * math.sin(t * 0.7 + ph)) % W
        y = (y0 - sp * 12 * t) % H
        a = 0.35 + 0.35 * math.sin(t * 2 + ph)
        d2 = (xx[int(max(0, y - 20)):int(min(H, y + 20)), int(max(0, x - 20)):int(min(W, x + 20))] - x) ** 2 + \
             (yy[int(max(0, y - 20)):int(min(H, y + 20)), int(max(0, x - 20)):int(min(W, x + 20))] - y) ** 2
        out[int(max(0, y - 20)):int(min(H, y + 20)), int(max(0, x - 20)):int(min(W, x + 20))] += \
            (np.exp(-d2 / (2 * (r / 3) ** 2)) * 255 * a)[..., None] * np.array([1.0, 0.95, 0.8], np.float32)
    out = np.clip(out, 0, 255)
    # 6) 아주 느린 확대 (1.00 → 1.05), 1920×1080 으로
    z = 1 + 0.05 * (t / SEC)
    cw, ch = W / z, H / z
    x0, y0 = (W - cw) * 0.45, (H - ch) * 0.55
    crop = cv2.getRectSubPix(out, (int(cw), int(ch)), (x0 + cw / 2, y0 + ch / 2))
    return np.clip(cv2.resize(crop, (OW, OH), interpolation=cv2.INTER_LANCZOS4), 0, 255).astype(np.uint8)   # 확대 때 넘친 값 잘라냄(흰·파란 점 방지)


p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{OW}x{OH}", "-r", str(FPS), "-i", "-",
                      "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", "-movflags", "+faststart", OUT], stdin=subprocess.PIPE)
for i in range(int(SEC * FPS)):
    p.stdin.write(frame(i / FPS).tobytes())
p.stdin.close()
p.wait()
print("OK", OUT)
