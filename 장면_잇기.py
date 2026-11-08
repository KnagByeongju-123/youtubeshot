"""장면 잇기 — 장면 영상들을 '물감 뿌리기 전환'(채널 시그니처, 사용자 결정 2026-11-08)으로 이어 붙이고 나레이션·자막을 넣음

  python -X utf8 장면_잇기.py <목록.json> <결과.mp4> [--전환 0.4] [--전환종류 섞기|paint|zoom|warp_in|warp_out]
  전환종류(사용자 결정 2026-11-08): zoom = 끝까지 줌인했다가 다음 장면이 줌아웃되며 / warp_in = 광속 워프가 끝날 때처럼 새 장면이 바깥에서 안쪽으로 모이며
           warp_out = 광속 워프가 시작할 때처럼 새 장면이 안쪽에서 바깥으로 퍼지며 / paint = 흩어뿌리기 물감. 기본 '섞기' = 이 넷을 돌아가며 [--물감색 200,30,40] [--나레이션 소리.wav] [--자막 자막.ass] [--배경음 소리.wav]
  목록.json = ["장면1.mp4", "장면2.mp4", ...]  (장면마다 길이 = 그 장면 몫 + 전환 길이. 앞 장면 끝과 다음 장면 앞이 전환 길이만큼 겹침)
  전환: 물감을 흩어뿌리듯 크고 작은 방울이 부드럽게 내려앉아 번지며 다음 장면이 드러남(사용자 결정 2026-11-08: 부드럽게), 젖은 자리에 옅은 물감색이 잠깐
  물감전환_마스크(n, w, h, seed) 는 다른 프로그램에서도 씀 (0~1 마스크 n장)"""
import argparse, json, subprocess, sys
import numpy as np
import cv2


def 물감전환_마스크(n, w, h, seed=0, small=(480, 270)):
    """흩어뿌리기 전환(사용자 결정 2026-11-08: 부드럽게): 크고 작은 물감 방울 수백 개가 흩뿌려지듯 차례로 내려앉아
    번지며 다음 장면이 드러남. 방울 가장자리는 부드럽게, 물감색은 옅게 잠깐만. 끝 장은 화면 전체"""
    rng = np.random.default_rng(seed)
    sw, sh = small
    yy, xx = np.mgrid[0:sh, 0:sw].astype(np.float32)
    # 바탕 순서: 부드러운 큰 얼룩 무늬(낮은 주파수 잡음) → 어느 곳이 먼저 젖을지
    base = np.zeros((sh, sw), np.float32)
    for f, a_ in ((2, 1.0), (4, .5), (8, .25)):
        g = rng.normal(size=(f + 1, f + 1)).astype(np.float32)
        base += a_ * cv2.resize(g, (sw, sh), interpolation=cv2.INTER_CUBIC)
    base = (base - base.min()) / (base.max() - base.min() + 1e-6)
    T = 0.55 + 0.5 * base                                     # 방울이 없는 곳도 끝에는 젖음
    # 흩뿌린 방울: 뿌린 방향(두세 곳)에서 퍼지듯, 큰 방울은 일찍·작은 방울은 촘촘히
    centers = [(rng.uniform(.1, .9) * sw, rng.uniform(.1, .9) * sh) for _ in range(rng.integers(2, 4))]
    for k in range(rng.integers(260, 380)):
        cx0, cy0 = centers[k % len(centers)]
        r_ = abs(rng.normal(0, .45)) * sw
        ang = rng.uniform(0, 2 * np.pi)
        cx, cy = cx0 + r_ * np.cos(ang), cy0 + r_ * .7 * np.sin(ang)
        rad = rng.uniform(2, 7) if rng.random() < .75 else rng.uniform(8, 22)
        t0 = rng.uniform(0, .7) * (0.7 if rad > 8 else 1.0)
        grow = rng.uniform(.12, .3) * sw                       # 내려앉은 뒤 천천히 번짐
        d = np.hypot(xx - cx, yy - cy)
        T = np.minimum(T, t0 + np.maximum(d - rad, 0) / grow)
    T = cv2.GaussianBlur(T, (0, 0), 1.6)
    T = cv2.resize(T, (w, h), interpolation=cv2.INTER_CUBIC)
    out = []
    for i in range(n):
        t = (i + 1) / n * 0.86          # 마지막 장까지 고르게 번지도록
        m = np.clip((t - T) * 16 + 0.5, 0, 1)                   # 아주 부드러운 가장자리
        rim = np.clip(1 - (t - T) / 0.10, 0, 1) * m * (t < 1.0) * 0.45   # 젖은 자리에 옅은 물감색이 잠깐
        out.append((m.astype(np.float32), rim.astype(np.float32)))
    out[-1] = (np.ones((h, w), np.float32), np.zeros((h, w), np.float32))
    return out


def _scale(img, s):
    """가운데 기준 s 배 확대 (s >= 1)"""
    if s <= 1.001: return img
    h, w = img.shape[:2]; cw, ch = int(w / s), int(h / s)
    x0, y0 = (w - cw) // 2, (h - ch) // 2
    return cv2.resize(img[y0:y0 + ch, x0:x0 + cw], (w, h), interpolation=cv2.INTER_LINEAR)


def _zoom_blur(img, k, n=7):
    """가운데에서 바깥으로 뻗는 빛줄기 흐림(광속 워프 느낌). k = 늘어나는 정도"""
    if k <= 0.01: return img.astype(np.float32)
    acc = np.zeros(img.shape, np.float32)
    for j in range(n):
        acc += _scale(img, 1 + k * j / (n - 1)).astype(np.float32)
    return acc / n


_RAD = {}
def _radius(w, h):
    if (w, h) not in _RAD:
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        _RAD[(w, h)] = (np.hypot((xx - w / 2) / (w / 2), (yy - h / 2) / (h / 2)) / np.sqrt(2))[..., None]   # 가운데 0 ~ 모서리 1
    return _RAD[(w, h)]


def 전환_장면(kind, A, B, p, w, h, paint=None, mask=None):
    """A(앞 장면) → B(뒤 장면), p = 0~1 진행. kind: paint / zoom / warp_in / warp_out (사용자 결정 2026-11-08)"""
    A = A.astype(np.float32); B = B.astype(np.float32)
    if kind == "zoom":                     # 앞 장면 끝까지 줌인 → 뒤 장면이 바짝 붙은 채로 나타나 줌아웃
        if p < 0.5:
            q = p / 0.5; return _zoom_blur(_scale(A.astype(np.uint8), 1 + 2.2 * q * q), 0.22 * q)
        q = (1 - p) / 0.5; return _zoom_blur(_scale(B.astype(np.uint8), 1 + 2.2 * q * q), 0.22 * q)
    R = _radius(w, h)
    if kind == "warp_in":                  # 광속 워프가 끝날 때: 새 장면이 바깥에서 안쪽으로 모이며 드러남
        e = 1 - p
        Bs = _zoom_blur(_scale(B.astype(np.uint8), 1 + 0.6 * e), 0.5 * e)
        As = _zoom_blur(A.astype(np.uint8), 0.6 * p)
        m = np.clip((R - (1 - p) * 1.05) / 0.12 + 0.5, 0, 1)    # 가장자리부터 안쪽으로
        o = As * (1 - m) + Bs * m
        return o + 255 * 0.25 * np.clip(1 - np.abs(R - (1 - p)) / 0.06, 0, 1) * (p < 0.98)   # 모이는 경계에 옅은 빛
    if kind == "warp_out":                 # 광속 워프가 시작할 때: 새 장면이 가운데에서 바깥쪽으로 퍼지며 드러남
        As = _zoom_blur(A.astype(np.uint8), 0.7 * p)              # 앞 장면은 빛줄기로 늘어남
        Bs = _zoom_blur(B.astype(np.uint8), 0.45 * (1 - p))
        m = np.clip((p * 1.08 - R) / 0.12 + 0.5, 0, 1)            # 가운데부터 바깥으로
        o = As * (1 - m) + Bs * m
        return o + 255 * 0.3 * np.clip(1 - np.abs(R - p * 1.08) / 0.06, 0, 1) * (p < 0.98)
    m, rim = mask                          # paint: 흩어뿌리기 물감
    o = A * (1 - m[..., None]) + B * m[..., None]
    return o * (1 - rim[..., None] * .92) + paint * rim[..., None] * .92


def frames(path, w, h):
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", path, "-vf", f"scale={w}:{h},fps=24", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    sz = w * h * 3
    while True:
        b = p.stdout.read(sz)
        if len(b) < sz: break
        yield np.frombuffer(b, np.uint8).reshape(h, w, 3)


def nframes(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-count_packets", "-select_streams", "v:0", "-show_entries", "stream=nb_read_packets", "-of", "csv=p=0", path], capture_output=True, text=True)
    return int(r.stdout.strip() or 0)


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("list"); ap.add_argument("out")
    ap.add_argument("--전환", type=float, default=0.4); ap.add_argument("--물감색", default="200,30,40")
    ap.add_argument("--나레이션", default=""); ap.add_argument("--자막", default=""); ap.add_argument("--배경음", default="")
    ap.add_argument("--크기", default="1920x1080")
    ap.add_argument("--전환종류", default="섞기", help="섞기(줌·워프 끝·워프 시작·물감을 돌아가며) 또는 paint/zoom/warp_in/warp_out 하나")
    a = ap.parse_args(argv)
    W, H = (int(x) for x in a.크기.split("x"))
    shots = json.load(open(a.list, encoding="utf-8"))
    paint = np.array([float(x) for x in a.물감색.split(",")], np.float32)
    X = max(1, round(a.전환 * 24))
    vf = [f"ass={a.자막}:fontsdir=/usr/share/fonts/truetype/nanum"] if a.자막 else []
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", "24", "-i", "-"]
    amix = []
    if a.나레이션: cmd += ["-i", a.나레이션]; amix.append("[1:a]volume=1.0[n]")
    if a.배경음: cmd += ["-i", a.배경음]
    fc = []
    if vf: fc.append("[0:v]" + ",".join(vf) + "[v]")
    if a.나레이션 and a.배경음: fc.append("[1:a][2:a]amix=inputs=2:duration=first:normalize=0[a]")
    elif a.나레이션: fc.append("[1:a]anull[a]")
    if fc: cmd += ["-filter_complex", ";".join(fc)]
    cmd += ["-map", "[v]" if vf else "0:v"] + (["-map", "[a]"] if a.나레이션 else [])
    cmd += ["-c:v", "libx264", "-crf", "20", "-preset", "medium", "-pix_fmt", "yuv420p"] + (["-c:a", "aac", "-b:a", "160k", "-shortest"] if a.나레이션 else []) + [a.out]
    enc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    prev = []                                                   # 앞 장면의 마지막 X 장 (이번 장면 앞부분과 겹침)
    for si, path in enumerate(shots):
        n = nframes(path); last = si == len(shots) - 1
        kinds = ["zoom", "warp_in", "warp_out", "paint"] if a.전환종류 == "섞기" else [a.전환종류]
        kind = kinds[(si - 1) % len(kinds)] if si else "paint"
        masks = 물감전환_마스크(X, W, H, seed=si) if prev and kind == "paint" else None
        keep = []
        for fi, fr in enumerate(frames(path, W, H)):
            if prev and fi < len(prev):                         # 물감 전환: 뒤 장면이 물감 자국 모양으로 드러남
                o = 전환_장면(kind, prev[fi], fr, (fi + 1) / (len(prev) + 1), W, H, paint, masks[fi] if masks else None)
                enc.stdin.write(o.clip(0, 255).astype(np.uint8).tobytes())
            elif not last and fi >= n - X:                      # 다음 장면과 겹칠 끝부분은 보관
                keep.append(fr.copy())
            else:
                enc.stdin.write(fr.tobytes())
        prev = keep
        print(f"장면 {si + 1}/{len(shots)}", flush=True)
    enc.stdin.close(); enc.wait()
    print("OK", a.out)


if __name__ == "__main__":
    main(sys.argv[1:])
