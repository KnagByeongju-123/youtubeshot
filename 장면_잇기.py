"""장면 잇기 — 장면 영상들을 '물감 뿌리기 전환'(채널 시그니처, 사용자 결정 2026-11-08)으로 이어 붙이고 나레이션·자막을 넣음

  python -X utf8 장면_잇기.py <목록.json> <결과.mp4> [--전환 0.4] [--물감색 200,30,40] [--나레이션 소리.wav] [--자막 자막.ass] [--배경음 소리.wav]
  목록.json = ["장면1.mp4", "장면2.mp4", ...]  (장면마다 길이 = 그 장면 몫 + 전환 길이. 앞 장면 끝과 다음 장면 앞이 전환 길이만큼 겹침)
  전환: 화면 여러 곳에 물감이 '퍽' 하고 튀어 번지며 다음 장면이 드러남 — 물감이 닿은 곳은 잠깐 물감색이었다가 다음 장면으로 바뀜, 작은 물방울도 튐
  물감전환_마스크(n, w, h, seed) 는 다른 프로그램에서도 씀 (0~1 마스크 n장)"""
import argparse, json, subprocess, sys
import numpy as np
import cv2


def 물감전환_마스크(n, w, h, seed=0, small=(480, 270)):
    """물감이 튀어 번지는 순서(도착 시간) 지도를 한 번 만들고, 시간마다 잘라 마스크 n장. 끝 장은 화면 전체"""
    rng = np.random.default_rng(seed)
    sw, sh = small
    yy, xx = np.mgrid[0:sh, 0:sw].astype(np.float32)
    T = np.full((sh, sw), 9.0, np.float32)
    for k in range(rng.integers(6, 10)):                      # 큰 물감 덩어리: 늦게 뿌린 것일수록 늦게 시작
        cx, cy = rng.uniform(-.05, 1.05) * sw, rng.uniform(-.05, 1.05) * sh
        t0 = rng.uniform(0, .45); speed = rng.uniform(.55, .9) * sw
        ang = np.arctan2(yy - cy, xx - cx)
        wob = np.zeros_like(ang)
        for f in (3, 5, 7, 11, 17):                            # 가장자리 울퉁불퉁 (물감 튄 모양)
            wob += rng.uniform(.04, .16) / (f / 3) * np.sin(f * ang + rng.uniform(0, 6.3))
        spikes = rng.uniform(.25, .6) * np.clip(np.sin(rng.integers(9, 16) * ang + rng.uniform(0, 6.3)), 0, 1) ** 8   # 뾰족하게 튄 줄기
        d = np.hypot(xx - cx, yy - cy) / (1 + wob + spikes)
        T = np.minimum(T, t0 + d / speed)
    for k in range(rng.integers(25, 45)):                     # 작은 물방울: 일찍 '톡톡' 찍힘
        cx, cy, r = rng.uniform(0, sw), rng.uniform(0, sh), rng.uniform(2, 9)
        t0 = rng.uniform(.02, .5)
        T = np.where(np.hypot(xx - cx, yy - cy) < r, np.minimum(T, t0), T)
    T = cv2.GaussianBlur(T, (0, 0), 0.8)
    T = cv2.resize(T, (w, h), interpolation=cv2.INTER_LINEAR)
    out = []
    for i in range(n):
        t = (i + 1) / n * 1.02
        m = np.clip((t - T) * 40 + 0.5, 0, 1)                  # 부드러운 가장자리 (몇 화소)
        rim = np.clip(1 - (t - T) / 0.16, 0, 1) * m * (t < 1.0)   # 막 물감이 닿은 곳은 잠깐 물감색 → 다음 장면으로 바뀜
        out.append((m, rim))
    out[-1] = (np.ones((h, w), np.float32), np.zeros((h, w), np.float32))
    return out


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
        masks = 물감전환_마스크(X, W, H, seed=si) if prev else None
        keep = []
        for fi, fr in enumerate(frames(path, W, H)):
            if prev and fi < len(prev):                         # 물감 전환: 뒤 장면이 물감 자국 모양으로 드러남
                m, rim = masks[fi]
                o = prev[fi].astype(np.float32) * (1 - m[..., None]) + fr.astype(np.float32) * m[..., None]
                o = o * (1 - rim[..., None] * .92) + paint * rim[..., None] * .92
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
