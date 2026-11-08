"""완성 영상의 정해진 시각(챕터가 바뀌는 곳)에 물감 튀김 전환을 넣음 — 채널 시그니처 (사용자 제안 2026-11-08)
.supertonic_venv/bin/python -X utf8 영상_페인트전환.py <영상.mp4> <결과.mp4> --시각 62.5,140.2,... [--앞 0.45] [--뒤 0.75] [--색 c8102e]
  또는 --타임스탬프 <영상_타임스탬프.txt> : '00:00 오프닝' 줄을 뺀 나머지 챕터 시각을 씀
  - 시각 T 마다 [T-앞, T+뒤] 구간을 바꿈: 앞 장면 = T-앞 의 화면을 멈춰 둠, 뒤 장면 = T+뒤 화면부터(그 전은 그 화면에서 멈춤)
    → 물감 덩어리가 튀며 뒤 장면이 드러나고 빨간 물감 테두리 (페인트전환.py 와 같은 무늬, 시각마다 다른 seed)
  - 소리는 그대로 복사(길이 같음), 그림만 다시 씀"""
import importlib.util
import os
import re
import subprocess
import sys

import cv2

HERE = os.path.dirname(os.path.abspath(__file__))


def main(a):
    src, out = a[0], a[1]
    pre = float(a[a.index("--앞") + 1]) if "--앞" in a else 0.45
    post = float(a[a.index("--뒤") + 1]) if "--뒤" in a else 0.75
    col = a[a.index("--색") + 1] if "--색" in a else "c8102e"
    if "--시각" in a:
        times = [float(x) for x in a[a.index("--시각") + 1].split(",") if x.strip()]
    else:
        times = []
        for ln in open(a[a.index("--타임스탬프") + 1], encoding="utf-8"):
            m = re.match(r"\s*(?:(\d+):)?(\d+):(\d+)\s+(.*)", ln)
            if m:
                h, mi, se = int(m.group(1) or 0), int(m.group(2)), int(m.group(3))
                tt = h * 3600 + mi * 60 + se
                if tt > 1:
                    times.append(float(tt))
    spec = importlib.util.spec_from_file_location("paint", os.path.join(HERE, "페인트전환.py"))
    pm = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pm)
    cap = cv2.VideoCapture(src)
    fps = cap.get(cv2.CAP_PROP_FPS) or 24
    W, H = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    wins = []
    for k, T in enumerate(sorted(times)):
        f0, f1 = int(round((T - pre) * fps)), int(round((T + post) * fps))
        if 0 < f0 < f1 < n:
            wins.append((f0, f1, k))
    print("전환", len(wins), "곳:", ", ".join(f"{f0 / fps:.1f}초" for f0, _, _ in wins))
    p = subprocess.Popen(["ffmpeg", "-nostdin", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", str(fps),
                          "-i", "-", "-i", src, "-map", "0:v", "-map", "1:a?", "-c:a", "copy",          # 소리는 원본에서 바로 (파일을 한 번만 씀 — 디스크 절약)
                          "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", "-preset", "veryfast", out], stdin=subprocess.PIPE)
    i, wi = 0, 0
    buf = None
    while True:
        ok, fr = cap.read()
        if not ok:
            break
        if wi < len(wins) and i == wins[wi][0]:          # 구간 시작: 앞 장면(멈춤)·뒤 장면 프레임을 모음
            f0, f1, k = wins[wi]
            a_frame = fr
            frames = [fr]
            while len(frames) < f1 - f0 + 1:
                ok2, fr2 = cap.read()
                if not ok2:
                    break
                frames.append(fr2)
            b_frame = frames[-1]
            pm.init(W, H, 11 + k * 7, col)
            m = len(frames)
            for j in range(m):
                pr = (j + 1) / m
                bj = b_frame                               # 뒤 장면은 T+뒤 화면 (그 전엔 멈춤)
                p.stdin.write(pm.blend(a_frame, bj, min(1.0, pr)).tobytes())
            i += m
            wi += 1
            continue
        p.stdin.write(fr.tobytes())
        i += 1
    p.stdin.close()
    p.wait()
    print("OK", out)


if __name__ == "__main__":
    main(sys.argv[1:])
