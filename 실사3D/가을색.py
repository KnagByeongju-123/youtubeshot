"""360° 사진(HDRI)을 가을 분위기로: 초록 잎을 노랑·주황·붉은 단풍색으로 바꾸고 전체를 따뜻하게 (사용자 2026-11-25 '가을 분위기')
   카메라에 보이는 사진(.jpg)과 빛을 주는 HDR(_1k.hdr) 둘 다 바꿔서 '<장소>_가을' 이름으로 저장 → 야외_오르빗.py --장소 <장소>_가을
   잎마다 색이 조금씩 다르게(위치에 따라 노랑~주황~붉은색이 섞임), 하늘·돌·사람 색은 그대로, 초록 정도에 따라 부드럽게 바뀜
   사용: python 실사3D/가을색.py <장소> [--세기 1.0] [--따뜻함 0.08]"""
import os, sys
import numpy as np
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
a = sys.argv[1:]
place = a[0]
ST = float(a[a.index("--세기") + 1]) if "--세기" in a else 1.0
WARM = float(a[a.index("--따뜻함") + 1]) if "--따뜻함" in a else 0.08
A = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "models", "polyhaven", "_hdri")


def autumn(rgb, lin=False):
    """rgb: float 0~1 (lin=True 이면 HDR 선형값, 밝기는 그대로 두고 색만)"""
    x = rgb.astype(np.float32)
    mx = x.max(-1); mn = x.min(-1); d = mx - mn + 1e-6
    r, g, b = x[..., 0], x[..., 1], x[..., 2]
    h = np.where(mx == r, ((g - b) / d) % 6, np.where(mx == g, (b - r) / d + 2, (r - g) / d + 4)) * 60     # 색상(도)
    s = d / (mx + 1e-6)
    green = np.clip(1 - np.abs(h - 95) / 60, 0, 1) ** 0.5 * np.clip((s - 0.08) / 0.12, 0, 1) * ST          # 초록(약 50~150°)일수록 1
    H_, W_ = x.shape[:2]
    yy, xx = np.mgrid[0:H_, 0:W_].astype(np.float32)
    noise = (np.sin(xx * 0.013) * np.sin(yy * 0.017) + np.sin(xx * 0.0041 + yy * 0.0057)) * 0.5        # 나무마다 다른 단풍색
    nh = 30 + 16 * noise                                                                                # 14°(붉음) ~ 46°(노랑)
    v = mx * 1.08; ns = np.clip(s * 1.3 + 0.18, 0, 1)
    # 새 색상으로 다시 칠함 (밝기 v 는 그대로)
    hh = nh / 60; c = v * ns; xq = c * (1 - np.abs(hh % 2 - 1)); m = v - c
    nr = np.where(hh < 1, c, xq) + m; ng = np.where(hh < 1, xq, c) + m; nb = m
    new = np.stack([nr, ng, nb], -1)
    out = x * (1 - green[..., None]) + new * green[..., None]
    # 전체를 따뜻하게 (빨강↑, 파랑↓)
    out = out * np.array([1 + WARM, 1 + WARM * 0.3, 1 - WARM], np.float32)
    return out if lin else np.clip(out, 0, 1)


jp = os.path.join(A, f"{place}.jpg"); im = np.asarray(Image.open(jp).convert("RGB")).astype(np.float32) / 255
out = np.empty_like(im)
for y0 in range(0, im.shape[0], 512):                                                                     # 큰 사진은 나눠서
    sl = autumn(im[y0:y0 + 512])
    # 위치 무늬가 조각마다 이어지게 y 를 보정
    out[y0:y0 + 512] = sl
Image.fromarray((out * 255).astype(np.uint8)).save(os.path.join(A, f"{place}_가을.jpg"), quality=93)
# HDR(Radiance .hdr, RGBE) 직접 읽고 쓰기 — 따로 설치할 것 없이
def read_hdr(path):
    raw = open(path, "rb").read(); i = raw.index(b"\n\n") + 2; j = raw.index(b"\n", i)
    dims = raw[i:j].split(); H_, W_ = int(dims[1]), int(dims[3]); p = j + 1; out = np.zeros((H_, W_, 4), np.uint8)
    for y in range(H_):
        if raw[p] == 2 and raw[p + 1] == 2:                                   # 새 RLE
            p += 4
            for c in range(4):
                x = 0
                while x < W_:
                    n = raw[p]; p += 1
                    if n > 128: n -= 128; out[y, x:x + n, c] = raw[p]; p += 1
                    else: out[y, x:x + n, c] = np.frombuffer(raw[p:p + n], np.uint8); p += n
                    x += n
        else:
            out[y] = np.frombuffer(raw[p:p + W_ * 4], np.uint8).reshape(W_, 4); p += W_ * 4
    e = out[..., 3].astype(np.int32)
    f = np.where(e > 0, np.ldexp(1.0, e - 136), 0.0).astype(np.float32)
    return out[..., :3].astype(np.float32) * f[..., None]


def write_hdr(path, img):
    H_, W_ = img.shape[:2]; mx = img.max(-1)
    m, e = np.frexp(mx); sc = np.where(mx > 1e-32, m * 256.0 / np.maximum(mx, 1e-32), 0)
    rgbe = np.zeros((H_, W_, 4), np.uint8)
    rgbe[..., :3] = np.clip(img * sc[..., None], 0, 255).astype(np.uint8); rgbe[..., 3] = np.where(mx > 1e-32, e + 128, 0).astype(np.uint8)
    with open(path, "wb") as fo:
        fo.write(b"#?RADIANCE\nFORMAT=32-bit_rle_rgbe\n\n" + f"-Y {H_} +X {W_}\n".encode()); fo.write(rgbe.tobytes())


hdr = read_hdr(os.path.join(A, f"{place}_1k.hdr"))
sc = np.maximum(hdr.max(-1, keepdims=True), 1.0); base = hdr / sc                                     # 1 넘는 밝은 곳(해)은 색 비율만 바꿈
write_hdr(os.path.join(A, f"{place}_가을_1k.hdr"), (autumn(np.clip(base, 0, 1), lin=True) * sc).astype(np.float32))
print("→", os.path.join(A, f"{place}_가을.jpg"))
