"""사진 → 두 층 입체 영상 (사용자 결정 2026-11-08)
  ① 사진 앞쪽의 주인공(사람·인형·성 …)을 rembg(MIT, 무료, models/rembg 의 isnet-general-use)로 저절로 오려 냄 → 앞층
  ② 배경의 빈자리는 둘레 색으로 메움(OpenCV inpaint) → 뒤층
  ③ 블렌더가 앞층을 배경 앞에 세우고 카메라를 움직여 찍음 → 가까운 앞층과 먼 배경이 다른 빠르기로 움직여 입체
  ④ 가장자리 빈 곳 검사(투명으로 찍어 확대해 잘라 냄), 1인칭(FPV)은 볼록 렌즈·모서리 어둡게
.supertonic_venv/bin/python -X utf8 사진_층입체.py <사진> <결과.mp4> --움직임 직진 [--초 10] [--보기 <층확인.jpg>]
  움직임 = 직진·오르빗·줌아웃·순간이동·드론·옆으로·1인칭·반대쪽 (장면마다 이 차례로 돌아가며 — 사진_입체영상.py 가 정함)
  주인공이 너무 작거나(사진의 3% 미만) 너무 크면(85% 넘게) 'NOSUBJECT' 를 출력하고 끝"""
import math
import os
import shutil
import subprocess
import sys

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
MOVES = ["직진", "오르빗", "줌아웃", "순간이동", "드론", "옆으로", "1인칭", "반대쪽"]


_SESS = {}


def cut(img_bgr, model=None):
    """주인공 알파(0~255). rembg (기본 bria-rmbg, 없으면 isnet-general-use)"""
    os.environ.setdefault("U2NET_HOME", os.path.join(HERE, "models", "rembg", "models"))
    from rembg import new_session, remove
    from PIL import Image
    model = model or os.environ.get("LAYER_MODEL", "bria-rmbg")
    if model not in _SESS:
        _SESS[model] = new_session(model)
    sess = _SESS[model]
    rgb = Image.fromarray(cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB))
    out = remove(rgb, session=sess, only_mask=True)
    return np.array(out)


def layers(src, work):
    img = cv2.imread(src)
    h, w = img.shape[:2]
    a = cut(img)
    m = (a > 128).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(m)               # 작은 조각은 버림
    keep = np.zeros_like(m)
    for k in range(1, n):
        if st[k, 4] > h * w * 0.004:
            keep[lab == k] = 1
    frac = float(keep.mean())
    big = max([st[k, 4] for k in range(1, n)] or [0])
    if frac and big / (keep.sum() + 1) < 0.8:                          # 조각조각 오려지면(주인공이 끊김) 쓰지 않음
        return None, frac
    if frac < 0.03 or frac > 0.85:
        return None, frac
    a = (a.astype(np.float32) * keep).astype(np.uint8)
    fg = np.dstack([img, a])
    grow = cv2.dilate(keep, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (25, 25)))   # 오려 낸 자리보다 조금 넓게 메움 (주인공 테두리가 배경에 남지 않게)
    bg = fill(img, grow)
    os.makedirs(work, exist_ok=True)
    pf, pb = os.path.join(work, "앞층.png"), os.path.join(work, "뒤층.png")
    cv2.imwrite(pf, fg)
    cv2.imwrite(pb, bg)
    return (pf, pb), frac


def fill(img, hole):
    """빈자리를 둘레 색으로 메움: 작게 줄여 가며 둘레 색을 모으고(밀어 올리기) 다시 키우며 채움 → 얼룩·네모 없이 부드럽게 번짐"""
    known = (hole == 0).astype(np.float32)
    col = img.astype(np.float32) * known[..., None]
    pyr = [(col, known)]
    while min(pyr[-1][1].shape) > 4:
        c, k = pyr[-1]
        pyr.append((cv2.resize(c, None, fx=0.5, fy=0.5, interpolation=cv2.INTER_AREA), cv2.resize(k, None, fx=0.5, fy=0.5, interpolation=cv2.INTER_AREA)))
    c, k = pyr[-1]
    est = c / np.maximum(k, 1e-4)[..., None]
    for c, k in reversed(pyr[:-1]):
        up = cv2.GaussianBlur(cv2.resize(est, (k.shape[1], k.shape[0]), interpolation=cv2.INTER_LINEAR), (0, 0), 1.0)
        mine = c / np.maximum(k, 1e-4)[..., None]
        wgt = np.clip(k, 0, 1)[..., None]
        est = mine * wgt + up * (1 - wgt)
    out = np.where(hole[..., None] > 0, est, img.astype(np.float32))
    return np.clip(out, 0, 255).astype(np.uint8)


def need_crop(fr_dir):
    from PIL import Image
    need = 1.0
    for f in sorted(os.listdir(fr_dir)):
        if not f.endswith(".png"):
            continue
        fr = np.asarray(Image.open(os.path.join(fr_dir, f)).convert("RGBA").resize((320, 180)))
        m = fr[..., 3] < 200
        if not m.any():
            continue
        ys, xs = np.nonzero(m)
        dx = np.abs(xs + 0.5 - 160) / 160
        dy = np.abs(ys + 0.5 - 90) / 90
        need = max(need, float((1.0 / np.maximum(np.maximum(dx, dy), 1e-3)).max()))
    return need


def render(src, out, move, secs, work):
    lay, frac = layers(src, work)
    if not lay:
        return None, frac
    frames = max(48, min(16 * 24, int(math.ceil(secs * 24))))
    fr = os.path.join(work, "frames")
    for zoom in (1.0, 0.9, 0.8):
        shutil.rmtree(fr, ignore_errors=True)
        subprocess.run(["xvfb-run", "-a", "-s", "-screen 0 1920x1080x24", "blender", "-b", "-P", os.path.join(HERE, "블렌더", "사진_층입체.py"), "--",
                        lay[0], lay[1], fr, "--cam", move, "--frames", str(frames), "--key", "--zoom", str(zoom)],
                       stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if not os.path.exists(os.path.join(fr, "frame_0001.png")):
            continue
        c = need_crop(fr)
        if c <= 1.3:
            break
    else:
        return None, frac
    c = max(1.04, c * 1.03)
    vf = f"crop=iw/{c:.4f}:ih/{c:.4f},scale=1920:1080"
    if move == "1인칭":
        vf += ",lenscorrection=k1=-0.22:k2=-0.05,vignette=angle=PI/4.2"
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-framerate", "24", "-i", os.path.join(fr, "frame_%04d.png"), "-vf", vf,
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "19", out], check=True)
    shutil.rmtree(fr, ignore_errors=True)
    return c, frac


def main(a):
    if len(a) < 2:
        print(__doc__)
        return 2
    src, out = a[0], a[1]
    move = a[a.index("--움직임") + 1] if "--움직임" in a else "직진"
    secs = float(a[a.index("--초") + 1]) if "--초" in a else 10.0
    work = out + ".작업"
    if "--보기" in a:
        lay, frac = layers(src, work)
        if lay:
            f, b = cv2.imread(lay[0], cv2.IMREAD_UNCHANGED), cv2.imread(lay[1])
            chk = np.full_like(b, 255)
            alpha = f[..., 3:4].astype(np.float32) / 255
            show = (f[..., :3] * alpha + chk * (1 - alpha)).astype(np.uint8)
            cv2.imwrite(a[a.index("--보기") + 1], np.hstack([cv2.imread(src), show, b]))
        print("주인공 넓이 %.1f%%" % (frac * 100))
        shutil.rmtree(work, ignore_errors=True)
        return 0
    c, frac = render(src, out, move, secs, work)
    shutil.rmtree(work, ignore_errors=True)
    if c is None:
        print("NOSUBJECT %.3f" % frac)
        return 0
    print(f"OK {out} 움직임 {move} 확대 {c:.2f} 주인공 {frac * 100:.0f}%")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
