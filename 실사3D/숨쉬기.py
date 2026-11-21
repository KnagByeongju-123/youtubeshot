"""Ditto 영상에 몸의 '살아 있는 느낌' 더하기 — Ditto 는 얼굴·고개만 움직이고 목 아래는 사진 그대로 굳어 있음 (사용자 지적 2026-11-21)
  ① 숨쉬기: 목 아래가 약 4초에 한 번 아주 살짝 위로 늘어났다 돌아옴 (어깨·가슴이 올라가는 느낌)
  ② 상체 흔들림: 목 아래가 좌우로 아주 조금 천천히
  ③ 카메라: 화면 전체가 천천히 다가가며 살짝 옆으로 (--카메라 off 로 끔)
목 경계는 부드럽게 이어 붙여 얼굴(Ditto 가 움직인 곳)과 끊기지 않게 함
사용: models/ditto/.venv/bin/python 실사3D/숨쉬기.py <Ditto영상.mp4> <결과.mp4> --목 <목 y 픽셀> [--숨 1.0] [--카메라 on]
  --목: 턱 바로 아래 높이(사진 픽셀). 상반신 1024×576 아나운서 D ≈ 330, 반신 ≈ 200
  --숨: 숨쉬기·흔들림 세기 배율 (1 = 기본, 너무 크면 몸이 고무처럼 보임)
"""
import subprocess
import sys

import cv2
import numpy as np


def opt(a, k, d):
    return a[a.index(k) + 1] if k in a else d


def main():
    a = sys.argv[1:]
    src, out = a[0], a[1]
    neck, amp, cam = int(opt(a, "--목", 330)), float(opt(a, "--숨", 1.0)), opt(a, "--카메라", "on") != "off"
    info = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height,r_frame_rate",
                           "-of", "csv=p=0", src], capture_output=True, text=True).stdout.strip().split(",")
    W, H = int(info[0]), int(info[1])
    num, den = info[2].split("/")
    fps = float(num) / float(den)
    rd = subprocess.Popen(["ffmpeg", "-v", "error", "-i", src, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    wr = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(fps), "-i", "-",
                           "-i", src, "-map", "0:v", "-map", "1:a?", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-c:a", "copy", out],
                          stdin=subprocess.PIPE)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    ramp = np.clip((yy - neck) / 60.0, 0, 1)              # 목에서 60픽셀에 걸쳐 0→1 (얼굴은 그대로)
    below = np.clip((yy - neck) / max(1, H - neck), 0, 1)  # 아래로 갈수록 1
    n = 0
    while True:
        buf = rd.stdout.read(W * H * 3)
        if len(buf) < W * H * 3:
            break
        f = np.frombuffer(buf, np.uint8).reshape(H, W, 3)
        t = n / fps
        br = (0.5 - 0.5 * np.cos(2 * np.pi * t / 4.2)) * amp        # 숨: 0→1→0 (4.2초)
        sw = np.sin(2 * np.pi * t / 6.7) * amp                       # 흔들림: -1~1 (6.7초)
        # 어깨·가슴이 위로 최대 약 2.5픽셀 (목 근처는 덜, 아래는 많이 늘어나는 게 아니라 '들리는' 느낌), 좌우 최대 약 1.5픽셀
        dy = ramp * (2.5 * br * (1 - 0.5 * below))
        dx = ramp * (1.5 * sw * (0.4 + 0.6 * below))
        g = cv2.remap(f, (xx - dx).astype(np.float32), (yy + dy).astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        if cam:                                                      # 천천히 다가감(1.00→1.04) + 살짝 옆으로
            z = 1.0 + 0.04 * min(1.0, t / 12.0)
            cx, cy = W / 2 + 6 * np.sin(2 * np.pi * t / 9.0), H * 0.45
            M = np.float32([[z, 0, (1 - z) * cx], [0, z, (1 - z) * cy]])
            g = cv2.warpAffine(g, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        wr.stdin.write(np.ascontiguousarray(g).tobytes())
        n += 1
    wr.stdin.close()
    wr.wait()
    print("만듦", out, n, "장")


if __name__ == "__main__":
    main()
