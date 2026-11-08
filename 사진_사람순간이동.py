"""사람이 나오는 실제 사진 → '사람 사이 순간이동' 영상 (사용자 결정 2026-11-08)
  사람이 나오는 실제 사진은 입체로 만들지 않고 진짜 사진 그대로 → 넓은 화면에서 머물다 사람 얼굴 클로즈업으로 순간 이동(컷), 다른 사람으로 또 순간 이동, 머물 때마다 천천히 흘러감
  얼굴은 자동으로 찾음: OpenCV YuNet (MIT, models/face_detection_yunet_2023mar.onnx)
.supertonic_venv/bin/python -X utf8 사진_사람순간이동.py <사진> <결과.mp4> [--초 10] [--보기 <확인.jpg>]
  - 얼굴 찾기: 원래 크기 + 640px 로 줄인 크기 두 번(큰 얼굴·작은 얼굴 모두), 사진 너비의 2.5% 넘는 얼굴만
  - 장면: ① 넓은 화면(전체, 천천히 3% 다가감, 전체 시간의 40%) → ② 얼굴 1 → ③ 얼굴 2 → ④ 얼굴 3 (큰 얼굴부터, 서로 떨어진 것, 장면마다 1.8초 이상)
  - 클로즈업 = 얼굴 높이의 3.4배(머리·어깨)를 16:9 로, 사진 높이의 30%보다 작게는 안 당김(너무 확대하면 흐려짐), 사진 밖으로 안 나가게
  - 클로즈업은 머무는 동안 4% 다가가며 옆으로 조금 흐름(장면마다 방향 바꿈)
  - 얼굴이 없으면 'NOFACE' 를 출력하고 끝 (사진_입체영상.py 가 입체로 처리)"""
import os
import subprocess
import sys

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
MODEL = os.path.join(HERE, "models", "face_detection_yunet_2023mar.onnx")
MODEL_URL = "https://media.githubusercontent.com/media/opencv/opencv_zoo/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx"
W, H, FPS = 1920, 1080, 24


def ensure_model():
    if not os.path.exists(MODEL) or os.path.getsize(MODEL) < 100000:
        subprocess.run(["curl", "-sSL", "-o", MODEL, MODEL_URL], check=True)


def faces_of(img):
    """[(x, y, w, h, 점수)] — 큰 얼굴부터"""
    ensure_model()
    h0, w0 = img.shape[:2]
    det = cv2.FaceDetectorYN.create(MODEL, "", (320, 320), 0.75, 0.3, 5000)
    found = []
    for sc in (1.0, 640.0 / max(w0, h0)):
        if sc > 1.0:
            continue
        im = img if sc == 1.0 else cv2.resize(img, (int(w0 * sc), int(h0 * sc)), interpolation=cv2.INTER_AREA)
        det.setInputSize((im.shape[1], im.shape[0]))
        _, f = det.detect(im)
        for x in ([] if f is None else f):
            found.append((x[0] / sc, x[1] / sc, x[2] / sc, x[3] / sc, float(x[14])))
    found = [f for f in found if f[2] > w0 * 0.025]
    found.sort(key=lambda f: -f[2])
    keep = []
    for f in found:                                  # 겹치는 얼굴(두 크기에서 같은 얼굴) 하나만
        cx, cy = f[0] + f[2] / 2, f[1] + f[3] / 2
        if all(abs(cx - (k[0] + k[2] / 2)) > max(f[2], k[2]) * 0.8 or abs(cy - (k[1] + k[3] / 2)) > max(f[3], k[3]) * 0.8 for k in keep):
            keep.append(f)
    return keep


def close_box(f, iw, ih):
    """얼굴 f 의 클로즈업 상자 (16:9, 사진 안)"""
    x, y, w, h, _ = f
    bh = max(h * 3.4, ih * 0.30)
    if bh >= ih * 0.8:                                 # 얼굴이 사진을 거의 채우면(초상) 더 당겨 눈·코 중심으로
        bh = max(h * 1.5, ih * 0.30)
    bw = bh * 16 / 9
    if bw > iw:
        bw, bh = iw, iw * 9 / 16
    if bh > ih:
        bh, bw = ih, ih * 16 / 9
    cx, cy = x + w / 2, y + h / 2 + (h * 0.55 if bh > h * 2 else h * 0.05)   # 얼굴을 위쪽 1/3 쯤에 (어깨가 보이게)
    l = min(max(0, cx - bw / 2), iw - bw)
    t = min(max(0, cy - bh / 2), ih - bh)
    return [l, t, bw, bh]


def wide_box(iw, ih):
    """사진 전체에서 16:9 로 가장 크게 (가운데, 세로 사진은 위쪽 30%)"""
    if iw / ih > 16 / 9:
        bw, bh = ih * 16 / 9, ih
        return [(iw - bw) / 2, 0, bw, bh]
    bw, bh = iw, iw * 9 / 16
    return [0, (ih - bh) * 0.3, bw, bh]


def shots(img, secs):
    ih, iw = img.shape[:2]
    fs = faces_of(img)
    if not fs:
        return None, fs
    pick = []
    for f in fs:                                       # 서로 떨어진 얼굴 3개까지
        if all(abs((f[0] + f[2] / 2) - (p[0] + p[2] / 2)) > iw * 0.12 or abs((f[1] + f[3] / 2) - (p[1] + p[3] / 2)) > ih * 0.15 for p in pick):
            pick.append(f)
        if len(pick) == 3:
            break
    wide_t = secs * 0.4
    n = max(1, min(len(pick), int((secs - wide_t) // 1.8)))
    pick = pick[:n]
    each = (secs - wide_t) / n
    out = [("넓게", wide_box(iw, ih), wide_t, 0)]
    for i, f in enumerate(pick):
        out.append((f"얼굴{i + 1}", close_box(f, iw, ih), each, 1 if i % 2 == 0 else -1))
    return out, fs


def render(img, plan, out_path):
    ih, iw = img.shape[:2]
    p = subprocess.Popen(["ffmpeg", "-nostdin", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", str(FPS),
                          "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "19", out_path], stdin=subprocess.PIPE)
    for name, (l, t, bw, bh), secs, sgn in plan:
        n = max(1, int(round(secs * FPS)))
        for k in range(n):
            q = k / max(1, n - 1)
            q = q * q * (3 - 2 * q)
            z = 1 + (0.03 if name == "넓게" else 0.045) * q          # 천천히 다가감
            dx = (0 if name == "넓게" else sgn * bw * 0.035 * (q - 0.5))  # 옆으로 조금 흐름
            w2, h2 = bw / z, bh / z
            cx, cy = l + bw / 2 + dx, t + bh / 2
            x0 = min(max(0, cx - w2 / 2), iw - w2)
            y0 = min(max(0, cy - h2 / 2), ih - h2)
            M = np.array([[w2 / W, 0, x0], [0, h2 / H, y0]], np.float64)
            fr = cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_CUBIC | cv2.WARP_INVERSE_MAP, borderMode=cv2.BORDER_REFLECT)
            p.stdin.write(fr.tobytes())
    p.stdin.close()
    p.wait()


def main(a):
    if len(a) < 2:
        print(__doc__)
        return 2
    src, out = a[0], a[1]
    secs = float(a[a.index("--초") + 1]) if "--초" in a else 10.0
    img = cv2.imread(src)
    plan, fs = shots(img, secs)
    if "--보기" in a:
        v = img.copy()
        for f in fs:
            cv2.rectangle(v, (int(f[0]), int(f[1])), (int(f[0] + f[2]), int(f[1] + f[3])), (0, 255, 255), 3)
        for name, (l, t, bw, bh), _, _ in (plan or []):
            cv2.rectangle(v, (int(l), int(t)), (int(l + bw), int(t + bh)), (0, 0, 255), 5)
            cv2.putText(v, name, (int(l) + 10, int(t) + 50), cv2.FONT_HERSHEY_SIMPLEX, 1.6, (0, 0, 255), 4)
        cv2.imwrite(a[a.index("--보기") + 1], v)
    if not plan:
        print("NOFACE")
        return 0
    render(img, plan, out)
    print("OK", out, " / ".join(f"{n} {s:.1f}초" for n, _, s, _ in plan))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
