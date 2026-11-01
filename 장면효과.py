"""장면 효과 — 멈춘 그림(스틸)에 움직임을 더하는 효과 모음 (그리는효과.py 와 함께 쓰는 후보, 2026-11-01 시험)

  python -X utf8 장면효과.py <그림> <결과.mp4> [--효과 꽃잎,빛줄기,비,수채번짐,반딧불] [--초 5] [--fps 24] [--인물 <인물.png>]
  → 효과마다 --초 길이로 이어 붙인 샘플 영상 (왼쪽 위에 효과 이름)

효과 (모두 직접 계산, 외부 모델 없음)
  꽃잎    : 꽃잎·나뭇잎이 바람에 흔들리며 천천히 떨어짐 (공원·숲 장면)
  먼지    : 빛 속에 떠다니는 작은 먼지·포자 (실내·폐허·햇살)
  빛줄기  : 위에서 비스듬히 내려오는 빛줄기가 천천히 일렁임 + 빛 한 번 쓸고 지나감 (감동·발견 장면)
  비      : 가는 빗줄기 + 화면이 살짝 어두워짐 (슬픔·긴장)
  눈      : 크고 작은 눈송이가 깊이감 있게 내림
  반딧불  : 부드럽게 깜빡이며 떠도는 작은 빛 (밤·기억·마법)
  수채번짐: 그림이 물감 번지듯 가운데에서 바깥으로 퍼지며 나타남 (그리는 효과 대신 쓸 수 있는 다른 등장)
  숨쉬기  : 인물 영역만 아주 조금 커졌다 작아졌다 (--인물 마스크가 있을 때, 살아 있는 느낌)
"""
import os
import subprocess
import sys

import cv2
import numpy as np

W, H = 1920, 1080


def load(p):
    im = cv2.cvtColor(cv2.imread(p), cv2.COLOR_BGR2RGB)
    return cv2.resize(im, (W, H), interpolation=cv2.INTER_AREA).astype(np.float32)


def slow_zoom(img, t, dur):
    k = 1.0 + 0.06 * t / dur
    M = cv2.getRotationMatrix2D((W / 2, H / 2), 0, k)
    return cv2.warpAffine(img, M, (W, H), borderMode=cv2.BORDER_REFLECT)


class Particles:
    def __init__(self, kind, n, seed=1):
        r = np.random.default_rng(seed)
        self.kind = kind
        self.x, self.y = r.random(n) * W, r.random(n) * H
        self.z = r.random(n) * 0.8 + 0.2                    # 깊이: 가까울수록 크고 빠름
        self.ph = r.random(n) * 6.28
        self.col = r.random(n)

    def draw(self, f, t):
        ov = np.zeros((H, W, 3), np.float32)
        a = np.zeros((H, W), np.float32)
        for i in range(len(self.x)):
            z = self.z[i]
            if self.kind == "꽃잎":
                y = (self.y[i] + t * 60 * z) % (H + 60) - 30
                x = (self.x[i] + t * 35 * z + 40 * np.sin(t * 1.3 + self.ph[i])) % (W + 60) - 30
                ang = (t * 90 + self.ph[i] * 57) % 360
                col = (255, 182 + 40 * self.col[i], 200) if self.col[i] > 0.4 else (250, 220, 120)
                cv2.ellipse(ov, (int(x), int(y)), (int(16 * z) + 6, int(7 * z) + 3), ang, 0, 360, col, -1, cv2.LINE_AA)
                cv2.ellipse(a, (int(x), int(y)), (int(16 * z) + 6, int(7 * z) + 3), ang, 0, 360, 0.95, -1, cv2.LINE_AA)
            elif self.kind in ("먼지", "반딧불"):
                x = (self.x[i] + 18 * np.sin(t * 0.5 + self.ph[i]) + t * 8 * z) % W
                y = (self.y[i] + 14 * np.cos(t * 0.4 + self.ph[i]) - t * 6 * z) % H
                if self.kind == "반딧불":
                    b = 0.5 + 0.5 * np.sin(t * 2.2 + self.ph[i] * 3)
                    cv2.circle(ov, (int(x), int(y)), int(7 * z) + 3, (255, 240, 140), -1, cv2.LINE_AA)
                    cv2.circle(a, (int(x), int(y)), int(7 * z) + 3, float(b), -1, cv2.LINE_AA)
                else:
                    cv2.circle(ov, (int(x), int(y)), int(4 * z) + 2, (255, 248, 225), -1, cv2.LINE_AA)
                    cv2.circle(a, (int(x), int(y)), int(4 * z) + 2, 0.8 * z, -1, cv2.LINE_AA)
            elif self.kind == "눈":
                y = (self.y[i] + t * 70 * z) % (H + 20) - 10
                x = (self.x[i] + 20 * np.sin(t * 0.8 + self.ph[i])) % W
                cv2.circle(ov, (int(x), int(y)), int(5 * z) + 1, (255, 255, 255), -1, cv2.LINE_AA)
                cv2.circle(a, (int(x), int(y)), int(5 * z) + 1, 0.9, -1, cv2.LINE_AA)
            elif self.kind == "비":
                y = (self.y[i] + t * 1400 * z) % (H + 80) - 40
                x = (self.x[i] - t * 200 * z) % W
                L = 30 * z + 10
                cv2.line(ov, (int(x), int(y)), (int(x - L * 0.25), int(y + L)), (220, 230, 245), 2, cv2.LINE_AA)
                cv2.line(a, (int(x), int(y)), (int(x - L * 0.25), int(y + L)), 0.75 * z, 2, cv2.LINE_AA)
        blur = 1.6 if self.kind == "반딧불" else (0.6 if self.kind != "비" else 0)
        if blur:
            glow = cv2.GaussianBlur(a, (0, 0), 6) * (1.2 if self.kind == "반딧불" else 0)
            a = np.clip(cv2.GaussianBlur(a, (0, 0), blur) + glow, 0, 1)
        return f * (1 - a[..., None]) + ov * a[..., None]


def light_rays(f, t, dur):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d = (xx * 0.8 + yy * 0.6) / 140.0
    rays = np.clip(np.sin(d + 0.4 * np.sin(t * 0.7)) * 0.5 + 0.5, 0, 1) ** 6
    fade = np.clip(1 - yy / H, 0, 1) ** 1.5
    lum = rays * fade * 0.35
    sweep = np.exp(-((xx - (t / dur) * (W + 800) + 400) / 220.0) ** 2) * 0.25      # 빛 한 번 쓸고 지나감
    add = (lum + sweep)[..., None] * np.array([255, 236, 190], np.float32)
    return np.clip(f + add, 0, 255)


def watercolor_reveal(img, t, dur, seed=3):
    p = min(1.0, t / (dur * 0.7))
    r = np.random.default_rng(seed)
    n = cv2.GaussianBlur(cv2.resize(r.random((H // 40, W // 40)).astype(np.float32), (W, H), interpolation=cv2.INTER_CUBIC), (0, 0), 25)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    dist = np.sqrt(((xx - W / 2) / W) ** 2 + ((yy - H / 2) / H) ** 2) / 0.71
    field = dist * 0.75 + n * 0.45
    m = np.clip((p * 1.25 - field) / 0.12, 0, 1)
    edge = np.clip(1 - np.abs(p * 1.25 - field) / 0.05, 0, 1)                   # 번지는 가장자리가 짙게
    paper = np.full_like(img, 250)
    out = paper * (1 - m[..., None]) + img * m[..., None]
    return np.clip(out - edge[..., None] * 40, 0, 255)


def breathe(img, mask, t):
    k = 1 + 0.012 * np.sin(t * 1.6)
    ys, xs = np.nonzero(mask > 128)
    cx, cy = (xs.mean(), ys.max()) if len(xs) else (W / 2, H)
    M = cv2.getRotationMatrix2D((float(cx), float(cy)), 0, k)
    big = cv2.warpAffine(img, M, (W, H), borderMode=cv2.BORDER_REFLECT)
    mm = cv2.GaussianBlur(cv2.warpAffine(mask, M, (W, H)).astype(np.float32) / 255, (0, 0), 3)[..., None]
    return img * (1 - mm) + big * mm


def label(f, txt):
    from PIL import Image, ImageDraw, ImageFont
    im = Image.fromarray(np.clip(f, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(im)
    font = ImageFont.truetype("/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf", 54)
    d.rounded_rectangle([30, 26, 60 + d.textlength(txt, font=font), 106], 16, fill=(0, 0, 0))
    d.text((45, 34), txt, font=font, fill=(255, 225, 90))
    return np.asarray(im)


def main(a):
    if len(a) < 2:
        print(__doc__)
        return 2
    img = load(a[0])
    out = a[1]
    kinds = (a[a.index("--효과") + 1] if "--효과" in a else "꽃잎,먼지,빛줄기,비,눈,반딧불,수채번짐").split(",")
    dur = float(a[a.index("--초") + 1]) if "--초" in a else 5.0
    fps = int(a[a.index("--fps") + 1]) if "--fps" in a else 24
    mask = cv2.resize(cv2.imread(a[a.index("--인물") + 1], 0), (W, H)) if "--인물" in a else None
    if mask is not None and "숨쉬기" not in kinds:
        kinds.append("숨쉬기")
    ff = os.path.join(os.path.dirname(sys.executable), "..", "lib")
    import imageio_ffmpeg
    p = subprocess.Popen([imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(fps),
                          "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", out], stdin=subprocess.PIPE)
    for kind in kinds:
        parts = Particles(kind, {"꽃잎": 110, "먼지": 220, "비": 700, "눈": 260, "반딧불": 45}.get(kind, 0)) if kind in ("꽃잎", "먼지", "비", "눈", "반딧불") else None
        for k in range(int(dur * fps)):
            t = k / fps
            f = slow_zoom(img, t, dur)
            if kind == "수채번짐":
                f = watercolor_reveal(f, t, dur)
            elif kind == "빛줄기":
                f = light_rays(f, t, dur)
            elif kind == "숨쉬기" and mask is not None:
                f = breathe(f, mask, t)
            elif kind == "비":
                f = f * 0.82
            if parts:
                f = parts.draw(f, t)
            p.stdin.write(label(f, kind).tobytes())
        print("효과", kind, flush=True)
    p.stdin.close()
    p.wait()
    print("OK", out)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
