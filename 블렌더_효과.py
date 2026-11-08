r"""Blender 로 만드는 영상 효과 (사용자 결정 2026-11-08, 홀리 편)

사용:
  python 블렌더_효과.py 장면 <장면이름> <움직임> <저장할 그림.jpg> [--초 10] [--크게]
      장면이름: 거리_물감놀이 · 모닥불_밤 · 크리슈나_라다 · 꽃_물감 (블렌더_장면.py 의 SCENES)
      움직임 : 시간정지(공중에 멈춘 순간, 카메라가 3~4곳으로 순간이동하며 천천히 흐름) · FPV(드론 고글 화면) · 천천히
      → <그림.jpg>(대표 한 장, 대본의 [사진] 자리에 넣음) + <그림.jpg>.clip/ (영상 프레임, 영상 만들 때 이 그림 대신 재생)
  python 블렌더_효과.py 입체사진 <사진> [--초 10] [--크게]
      사람이 없는 사진만: 깊이 AI 로 앞뒤를 나눠 Blender 판으로 만들고 카메라가 천천히 다가감 → <사진>.clip/
      사람 얼굴이 보이면 하지 않고 얼굴 순간이동(<사진>.얼굴.json)을 만듦 (사용자 결정: 사람 사진은 진짜 사진 그대로)
  python 블렌더_효과.py 얼굴 <사진>...           얼굴 찾기만 → <사진>.얼굴.json (OpenCV YuNet, Apache-2.0)
  python 블렌더_효과.py 프로젝트 <프로젝트.json> [--크게]
      프로젝트의 모든 실제 사진에서 얼굴 찾기 → 얼굴.json. 입체사진은 자동으로 만들지 않음:
      얼굴을 못 찾은 사진에도 사람(뒷모습·가루에 가린 얼굴)이 있을 수 있어, Claude 가 눈으로 '사람 없음'을 확인한 사진만 '입체사진' 으로

--크게 가 없으면 작은 화질(960×540, 적은 샘플)로 먼저 만들어 검토 (사용자 결정 2026-11-08: 작은 화질 먼저 → 검토 → 크게)
"""
import json
import os
import shutil
import subprocess
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
BLENDER = os.environ.get("BLENDER") or next((p for p in (os.path.expanduser("~/tools/blender-4.2.23-linux-x64/blender"),
                                                           shutil.which("blender") or "") if p and os.path.exists(p)), "blender")
FACE_MODEL = os.path.join(HERE, "models", "face_detection_yunet_2023mar.onnx")
DEPTH_MODEL = os.path.join(HERE, "models", "depth_anything_v2_small_fp16.onnx")
DEPTH_DIR = os.path.join(HERE, "output", "_깊이")
FPS = 24


def opt(name, default=None):
    if name in sys.argv:
        i = sys.argv.index(name)
        return sys.argv[i + 1] if i + 1 < len(sys.argv) else default
    return default


BIG = "--크게" in sys.argv
SIZE = (1920, 1080) if BIG else (960, 540)


def run_blender(cfg):
    p = os.path.join(cfg["out"] + "_설정.json")
    os.makedirs(os.path.dirname(p) or ".", exist_ok=True)
    json.dump(cfg, open(p, "w", encoding="utf-8"), ensure_ascii=False)
    r = subprocess.run([BLENDER, "-b", "--factory-startup", "-noaudio", "-P", os.path.join(HERE, "블렌더_장면.py"), "--", p],
                       capture_output=True, text=True)
    if r.returncode or "Error" in r.stdout[-3000:]:
        print(r.stdout[-3000:], r.stderr[-2000:])
        raise SystemExit("Blender 실패")
    os.remove(p)


# ───────── FPV 고글 화면: 볼록 렌즈 + 어두운 모서리 ─────────
def fpv_look(arr, k=0.16, vig=0.55):
    import cv2
    h, w = arr.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    nx, ny = (xx - w / 2) / (w / 2), (yy - h / 2) / (w / 2)
    r2 = nx * nx + ny * ny
    f = 1 - k * r2 + 0.04 * r2 * r2          # 가운데가 부풀어 보이는 볼록 렌즈 (가장자리는 안으로 당김)
    f /= (1 - k * 0.0)                       # 가운데 그대로
    sx = (nx / f * (1 - k * 0.55)) * (w / 2) + w / 2
    sy = (ny / f * (1 - k * 0.55)) * (w / 2) + h / 2
    out = cv2.remap(arr, sx, sy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    rr = np.sqrt(((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2)
    v = 1 - vig * np.clip((rr - 0.55) / 0.85, 0, 1) ** 1.6
    return np.clip(out * v[..., None], 0, 255).astype(np.uint8)


STEP = int(opt("--간격", 1 if BIG else 2))     # 작은 화질은 두 프레임에 한 장만 그림 (초당 12장, 검토용 · 빠르게)


def finish_clip(frames_dir, still_path, fpv=False):
    fs = sorted(f for f in os.listdir(frames_dir) if f.endswith(".jpg"))
    if fpv:
        for f in fs:
            p = os.path.join(frames_dir, f)
            Image.fromarray(fpv_look(np.asarray(Image.open(p).convert("RGB")))).save(p, quality=92)
    for i, f in enumerate(fs):                      # 0001.jpg … 순서대로 (렌더 이름 f0001.jpg)
        os.replace(os.path.join(frames_dir, f), os.path.join(frames_dir, f"{i + 1:04d}.jpg"))
    mid = os.path.join(frames_dir, f"{max(1, len(fs) // 3):04d}.jpg")
    if still_path and os.path.exists(mid):
        Image.open(mid).convert("RGB").save(still_path, quality=93)
    json.dump({"fps": FPS / STEP, "n": len(fs), "size": SIZE, "fpv": fpv}, open(os.path.join(frames_dir, "clip.json"), "w"))
    return len(fs)


def scene(name, move, still, sec):
    clip = still + ".clip"
    shutil.rmtree(clip, ignore_errors=True)
    cfg = dict(kind="로우폴리", scene=name, move=move, sec=sec, fps=FPS, w=SIZE[0], h=SIZE[1],
               samples=24 if BIG else 10, out=clip, seed=sum(map(ord, name + move)) % 1000, step=STEP)
    run_blender(cfg)
    n = finish_clip(clip, still, fpv=(move == "FPV"))
    print("OK", still, n, "프레임")


# ───────── 얼굴 찾기 ─────────
def faces(path):
    import cv2
    im = cv2.imdecode(np.fromfile(path, np.uint8), cv2.IMREAD_COLOR)
    h, w = im.shape[:2]
    k = min(1.0, 1600 / max(w, h))
    sm = cv2.resize(im, (int(w * k), int(h * k))) if k < 1 else im
    det = cv2.FaceDetectorYN.create(FACE_MODEL, "", (sm.shape[1], sm.shape[0]), 0.72, 0.3, 50)
    _, f = det.detect(sm)
    out = []
    for r in (f if f is not None else []):
        x, y, fw, fh, sc = float(r[0]) / k, float(r[1]) / k, float(r[2]) / k, float(r[3]) / k, float(r[-1])
        x, y = max(0.0, x), max(0.0, y)
        if fw * fh < (w * h) * 0.0009:              # 너무 작은 얼굴(멀리 있는 군중)은 클로즈업하면 흐려서 뺌
            continue
        out.append({"box": [round(x / w, 4), round(y / h, 4), round((x + fw) / w, 4), round((y + fh) / h, 4)], "score": round(sc, 3)})
    out.sort(key=lambda d: -(d["box"][2] - d["box"][0]) * (d["box"][3] - d["box"][1]))
    return out[:4]


def save_faces(path):
    fs = faces(path)
    json.dump({"faces": fs}, open(path + ".얼굴.json", "w", encoding="utf-8"), ensure_ascii=False)
    return fs


# ───────── 입체 사진 ─────────
def depth_of(path):
    sys.path.insert(0, HERE)
    from depth_worker import key_for
    npy = os.path.join(DEPTH_DIR, key_for(path) + ".npy")
    if not os.path.exists(npy):
        py = os.path.join(HERE, ".supertonic_venv", "bin", "python")
        subprocess.run([py if os.path.exists(py) else sys.executable, os.path.join(HERE, "depth_worker.py"), DEPTH_MODEL, DEPTH_DIR, path], check=True)
    return npy


def photo3d(path, sec):
    clip = path + ".clip"
    shutil.rmtree(clip, ignore_errors=True)
    npy = depth_of(path)
    cfg = dict(kind="입체사진", photo=os.path.abspath(path), depth=npy, sec=sec, fps=FPS, w=SIZE[0], h=SIZE[1],
               samples=8 if BIG else 4, out=clip, depth_amt=0.3, step=STEP)
    run_blender(cfg)
    n = finish_clip(clip, None)
    print("OK", path, n, "프레임 (입체)")


def project(pj_path):
    pj = json.load(open(pj_path, encoding="utf-8"))
    base = os.path.dirname(os.path.abspath(pj_path))
    import re
    paths = []
    for m in re.finditer(r"\[사진[^\]]*?\|?\s*([^\]|]+\.(?:jpe?g|png|webp))", pj.get("story", ""), re.I):
        p = m.group(1).strip()
        p = p if os.path.isabs(p) else os.path.join(base, p)
        if os.path.exists(p) and p not in paths:
            paths.append(p)
    print(f"사진 {len(paths)}장")
    for p in paths:
        if os.path.exists(p + ".clip") or os.path.exists(p + ".얼굴.json"):
            continue
        fs = save_faces(p)
        if fs:
            print("얼굴", len(fs), p)
        else:
            os.remove(p + ".얼굴.json")
            print("얼굴 없음 (사람이 없는지 눈으로 확인한 뒤에만 '입체사진' 으로):", p)


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return
    cmd = sys.argv[1]
    sec = float(opt("--초", 10))
    if cmd == "장면":
        scene(sys.argv[2], sys.argv[3], sys.argv[4], sec)
    elif cmd == "입체사진":
        p = sys.argv[2]
        if save_faces(p):
            print("얼굴이 있어 입체로 바꾸지 않음 → 얼굴 순간이동:", p + ".얼굴.json")
        else:
            os.remove(p + ".얼굴.json")
            photo3d(p, sec)
    elif cmd == "얼굴":
        for p in sys.argv[2:]:
            if not p.startswith("--"):
                print(p, save_faces(p))
    elif cmd == "프로젝트":
        project(sys.argv[2])


if __name__ == "__main__":
    main()
