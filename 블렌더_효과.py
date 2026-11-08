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
      프로젝트의 모든 실제 사진을 앞뒤 두 층으로(사용자 결정 2026-11-08): rembg 로 주인공(사람·인형·성 …)을 오려 앞층,
      빈자리를 둘레 색으로 메운 뒤층 → Blender 카메라가 움직이면 앞뒤가 다른 속도로 움직여 입체로 보임.
      카메라 움직임은 사진마다 차례로: 직진 → 오르빗 → 줌아웃 → 순간이동(얼굴이 있으면 얼굴로) → 드론 → 옆으로 → 1인칭드론 → 반대쪽
      오림이 조각조각 깨지면(군중 사진) 사진 한 장 판으로 같은 움직임

--크게 가 없으면 작은 화질(640×360, 적은 샘플)로 먼저 만들어 검토 (사용자 결정 2026-11-08: 작은 화질 먼저 → 검토 → 크게)
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
SIZE = (1920, 1080) if BIG else (640, 360)       # 작은 화질(검토용)은 640×360 — 이 서버(CPU 4개)에서 그리는 시간 때문


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


# ───────── 앞뒤 두 층 (사용자 결정 2026-11-08) ─────────
_REMBG = {}


def cut_layers(path, model="isnet-general-use"):
    """사진 앞쪽의 주인공(사람·인형·성 …)을 rembg(MIT)로 오려 앞층(RGBA png), 빈자리를 둘레 색으로 메운 뒤층(jpg)을 만듦.
    결과: <사진>.앞층.png, <사진>.뒤층.jpg (이미 있으면 그대로). 주인공이 너무 작거나(2%↓) 거의 전부(85%↑)면 None"""
    import cv2
    fg_p, bg_p = path + ".앞층.png", path + ".뒤층.jpg"
    if os.path.exists(path + ".앞층.json"):
        if not json.load(open(path + ".앞층.json")).get("ok"):
            return None
        if os.path.exists(fg_p) and os.path.exists(bg_p):
            return fg_p, bg_p
    from rembg import new_session, remove
    if model not in _REMBG:
        _REMBG[model] = new_session(model)
    im = Image.open(path).convert("RGB")
    k = min(1.0, 1600 / max(im.size))
    if k < 1:
        im = im.resize((round(im.width * k), round(im.height * k)), Image.LANCZOS)
    m = np.asarray(remove(im, session=_REMBG[model], only_mask=True, post_process_mask=True).convert("L"), np.float32) / 255
    # 작은 조각(사진의 0.4%↓)은 버림, 조각조각 깨진 오림(큰 덩어리가 전체의 60% 미만이거나 큰 조각이 4개 넘음)은 쓰지 않음
    bm = (m > 0.5).astype(np.uint8)
    n_, lab, st, _ = cv2.connectedComponentsWithStats(bm, 8)
    areas = st[1:, cv2.CC_STAT_AREA] if n_ > 1 else np.array([0])
    keep = [i + 1 for i, a_ in enumerate(areas) if a_ >= bm.size * 0.004]
    m = m * np.isin(lab, keep)
    frac = float((m > 0.5).mean())
    big = sorted((areas[i - 1] for i in keep), reverse=True)
    meta = {"frac": round(frac, 3), "pieces": len(keep), "main": round(float(big[0] / max(1, sum(big))), 2) if big else 0}
    if frac < 0.02 or frac > 0.85 or not big or meta["main"] < 0.6 and len(keep) > 2 or len(keep) > 4:
        json.dump(dict(meta, ok=False), open(path + ".앞층.json", "w"))
        return None
    ys, xs = np.nonzero(m > 0.5)
    meta.update(ok=True, box=[round(xs.min() / m.shape[1], 3), round(ys.min() / m.shape[0], 3), round(xs.max() / m.shape[1], 3), round(ys.max() / m.shape[0], 3)])
    json.dump(meta, open(path + ".앞층.json", "w"))
    m = cv2.GaussianBlur(m, (0, 0), 1.2)                       # 가장자리를 살짝 부드럽게
    rgb = np.asarray(im)
    Image.fromarray(np.dstack([rgb, (np.clip(m, 0, 1) * 255).astype(np.uint8)]), "RGBA").save(fg_p)
    # 뒤층: 주인공 자리(넉넉히 넓힌 것)를 둘레 색으로 메움 — 작게 줄여 메운 뒤 키우고, 둘레와 부드럽게 섞음
    hole = (m > 0.2).astype(np.uint8)
    hole = cv2.dilate(hole, np.ones((3, 3), np.uint8), iterations=max(3, im.width // 120))
    s = 0.25
    small = cv2.resize(rgb, None, fx=s, fy=s, interpolation=cv2.INTER_AREA)
    hs = cv2.resize(hole, (small.shape[1], small.shape[0]), interpolation=cv2.INTER_NEAREST)
    fill = cv2.inpaint(cv2.cvtColor(small, cv2.COLOR_RGB2BGR), hs * 255, 9, cv2.INPAINT_TELEA)
    fill = cv2.cvtColor(cv2.resize(fill, (im.width, im.height), interpolation=cv2.INTER_CUBIC), cv2.COLOR_BGR2RGB)
    fill = cv2.GaussianBlur(fill, (0, 0), 6)
    a = cv2.GaussianBlur(hole.astype(np.float32), (0, 0), 4)[..., None]
    out = rgb * (1 - a) + fill * a
    Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).save(bg_p, quality=93)
    return fg_p, bg_p


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


MOVES = ["직진", "오르빗", "줌아웃", "순간이동", "드론", "옆으로", "1인칭드론", "반대쪽"]   # 장면마다 차례로 (사용자 결정 2026-11-08)


def layers3d(path, sec, move):
    """사진 → 앞층(오려 낸 주인공)·뒤층(빈자리 메움) → Blender 카메라 움직임. 오림이 깨지면 사진 한 장 판으로 같은 움직임"""
    clip = path + ".clip"
    shutil.rmtree(clip, ignore_errors=True)
    r = cut_layers(path)
    meta = json.load(open(path + ".앞층.json")) if os.path.exists(path + ".앞층.json") else {}
    fs = []
    if os.path.exists(path + ".얼굴.json"):
        fs = [f_["box"] for f_ in json.load(open(path + ".얼굴.json", encoding="utf-8")).get("faces", []) if f_["box"][3] - f_["box"][1] >= 0.035]
    cfg = dict(kind="앞뒤층", bg=os.path.abspath(r[1] if r else path), fg=os.path.abspath(r[0]) if r else "",
               box=meta.get("box") or (fs[0] if fs else None), faces=fs, move=move, sec=sec, fps=FPS,
               w=SIZE[0], h=SIZE[1], samples=8 if BIG else 4, out=clip, step=STEP)
    run_blender(cfg)
    n = finish_clip(clip, None, fpv=(move == "1인칭드론"))
    json.dump(dict(json.load(open(os.path.join(clip, "clip.json"))), move=move, layers=bool(r)), open(os.path.join(clip, "clip.json"), "w"))
    print("OK", path, n, "프레임", move, "앞뒤층" if r else "한 장")


def project(pj_path, only_missing=True):
    """프로젝트의 모든 실제 사진(블렌더 장면 그림 제외)을 대본 순서대로: 얼굴 찾기 → 앞뒤층 → 움직임은 MOVES 를 차례로 돌아가며.
    클립 길이 = 그 사진이 보이는 시간(문단 글자 수로 어림, 넉넉히 +25%)"""
    import re
    pj = json.load(open(pj_path, encoding="utf-8"))
    base = os.path.dirname(os.path.abspath(pj_path))
    story = pj.get("story", "")
    paras = [p_.strip() for p_ in re.split(r"\n\s*\n", story) if p_.strip()]
    sec_per_char = float(opt("--초당글자", 0)) or 1 / 7.6       # 이 편: 4,400자 ≈ 9.6분
    groups, cur = [], None                                     # [(사진들, 글자 수)]
    for p_ in paras:
        if p_.startswith("[사진"):
            if cur is None or cur[1] > 0:
                cur = [[], 0]
                groups.append(cur)
            m = re.match(r"\[사진:\s*([^|\]]+?\.(?:jpe?g|png|webp))\s*[|\]]", p_, re.I)
            if m:
                cur[0].append(m.group(1).strip())
        elif cur is not None and not p_.startswith("#"):
            cur[1] += len(p_)
    todo = []
    for imgs, chars in groups:
        for im in imgs:
            todo.append((im, max(6.0, chars * sec_per_char / len(imgs) * 1.25)))
    k = 0
    for im, sec in todo:
        p = im if os.path.isabs(im) else (os.path.join(HERE, im) if os.path.exists(os.path.join(HERE, im)) else os.path.join(base, im))
        if not os.path.exists(p) or os.path.basename(p).startswith("blender_"):
            continue
        move = MOVES[k % len(MOVES)]
        k += 1
        if only_missing and os.path.exists(os.path.join(p + ".clip", "clip.json")):
            continue
        if not os.path.exists(p + ".얼굴.json"):
            save_faces(p)
        layers3d(p, round(sec, 1), move)


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
