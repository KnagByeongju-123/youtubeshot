"""사진 장면 — 장문 다큐의 실제 사진 장면 영상 (오른쪽 위 설명 상자 + 오른쪽 아래 출처, 사용자 결정 2026-11-01·08)

  python -X utf8 사진_장면.py <작업폴더>
  작업폴더/script.json = [{"t": 문단, "k": "photo"|"draw", "file": 사진, "label": 설명, "credit": "사진 · 작가 · 라이선스", "move": "auto"|"zoom"}, ...]
  작업폴더/durs.json = 문단마다 나레이션 길이(초) → 장면 길이 = 길이 + 0.7(쉼) + 0.4(물감 전환 겹침)
  결과: 작업폴더/shots/<문단번호>.mp4
  - 기본: 천천히 확대·축소(번갈아)
  - 사람이 여럿 또렷이 나온 사진(얼굴 2개 이상, 5초 넘는 장면): 전체 → 얼굴 → 얼굴 순간이동(자리마다 살짝 흐름, 사용자 결정 2026-11-08)
    얼굴 찾기 = YuNet(OpenCV Zoo, Apache-2.0) models/yunet/ — 세션 시작 때 자동으로 받음. move 를 "zoom" 으로 주면 순간이동 없이 확대만
  - 설명 상자: 빨간 세로줄 + 어두운 상자 + 흰 글자(Noto Sans CJK), 출처: 검은 바탕 흰 글자"""
import json, subprocess, sys
from PIL import Image, ImageDraw, ImageFont
T = sys.argv[1]
L = json.load(open(T + "/script.json")); D = json.load(open(T + "/durs.json"))
FB = ImageFont.truetype("/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc", 40)
FS = ImageFont.truetype("/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc", 22)
def overlay(label, credit, out):
    im = Image.new("RGBA", (1920, 1080), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    tw = d.textlength(label, font=FB); x1 = 1920 - 60; x0 = x1 - tw - 56
    d.rectangle([x0, 60, x1, 140], fill=(0, 0, 0, 165)); d.rectangle([x0, 60, x0 + 9, 140], fill=(224, 48, 48, 255))
    d.text((x0 + 32, 100), label, font=FB, fill="white", anchor="lm")
    cw = d.textlength(credit, font=FS); d.rectangle([1920 - cw - 44, 1080 - 58, 1920 - 20, 1080 - 22], fill=(0, 0, 0, 190))
    d.text((1920 - cw - 32, 1080 - 40), credit, font=FS, fill="white", anchor="lm")
    im.save(out)
import cv2, numpy as np
YUNET = "models/yunet/face_detection_yunet_2023mar.onnx"   # 얼굴 찾기 YuNet (OpenCV Zoo, Apache-2.0)
def faces(path):
    """사진 속 또렷한 얼굴 자리(비율) — 큰 것부터 3개, 서로 겹치지 않게"""
    im = cv2.imread(path); h, w = im.shape[:2]
    d = cv2.FaceDetectorYN.create(YUNET, "", (w, h), 0.75)
    _, f = d.detect(im)
    if f is None: return []
    f = sorted([x for x in f if x[2] >= w / 22], key=lambda x: -x[2])
    out = []
    for x in f:
        c = ((x[0] + x[2] / 2) / w, (x[1] + x[3] * 0.9) / h)
        if all(abs(c[0] - o[0]) > .18 or abs(c[1] - o[1]) > .2 for o in out): out.append(c)
        if len(out) == 3: break
    return out
def seg(path, out, N, cx, cy, z0, z1):
    """사진 한 자리: 확대 z0→z1 로 천천히 흐름 (cx,cy = 비율)"""
    vf = (f"scale=3840:2160:force_original_aspect_ratio=increase,crop=3840:2160,"
          f"zoompan=z='{z0}+({z1}-{z0})*on/{N}':x='max(0,min(iw-iw/zoom,{cx}*iw-iw/zoom/2))':y='max(0,min(ih-ih/zoom,{cy}*ih-ih/zoom/2))':d={N}:s=1920x1080:fps=24")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-loop", "1", "-i", path, "-vf", vf, "-frames:v", str(N), "-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p", out], check=True)
k = 0
for i, x in enumerate(L):
    if x["k"] != "photo": continue
    dur = D[i] + 0.7 + 0.4; N = int(round(dur * 24)); k += 1
    z0, z1 = (1.0, 1.12) if k % 2 else (1.12, 1.0)
    ov = f"{T}/shots/{i+1:02d}_ov.png"; overlay(x["label"], x["credit"], ov)
    fc = faces(x["file"]) if x.get("move", "auto") != "zoom" else []
    if len(fc) >= 2 and dur >= 5:                           # 사람이 여럿 나온 사진: 전체 → 얼굴 → 얼굴 순간이동 (자리마다 살짝 흐름, 사용자 결정 2026-11-08)
        spots = [(0.5, 0.5, 1.0, 1.06)] + [(fx, fy, 1.75, 1.85) for fx, fy in fc[:3]]
        n_ = len(spots); parts = []
        for j, (cx, cy, z0, z1) in enumerate(spots):
            Nj = N // n_ + (1 if j < N % n_ else 0); pf = f"{T}/shots/{i+1:02d}_p{j}.mp4"; seg(x["file"], pf, Nj, cx, cy, z0, z1); parts.append(pf)
        lst = f"{T}/shots/{i+1:02d}_l.txt"; open(lst, "w").write("".join(f"file '{p_}'\n" for p_ in parts))
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-i", ov, "-filter_complex", "[0:v][1:v]overlay=0:0,format=yuv420p[v]", "-map", "[v]",
                        "-c:v", "libx264", "-crf", "18", f"{T}/shots/{i+1:02d}.mp4"], check=True)
        print("OK", i + 1, "순간이동", len(fc), flush=True); continue
    vf = (f"[0:v]scale=3840:2160:force_original_aspect_ratio=increase,crop=3840:2160,"
          f"zoompan=z='{z0}+({z1}-{z0})*on/{N}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={N}:s=1920x1080:fps=24[b];[b][1:v]overlay=0:0,format=yuv420p[v]")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-loop", "1", "-i", x["file"], "-i", ov, "-filter_complex", vf, "-map", "[v]", "-frames:v", str(N), "-c:v", "libx264", "-crf", "18", f"{T}/shots/{i+1:02d}.mp4"], check=True)
    print("OK", i + 1, flush=True)
