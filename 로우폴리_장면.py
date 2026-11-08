"""로우폴리 장면 — 그림 한 장 → '그리는 효과' 뒤 로우폴리 입체 카메라 움직임 영상 (장문 다큐, 사용자 결정 2026-11-08)

  python -X utf8 로우폴리_장면.py <그림> <인물 마스크.png 또는 -> <결과.mp4> --초 9.5 [--움직임 right|left] [--그리는효과 3.5] [--조각 15000,10000]

  1) 인물(동물) 마스크(흰색 = 인물, sam_worker.py 로 만듦)로 인물을 떼어 내고, 빈 자리는 둘레 색으로 메움(로우폴리라 티 안 남)
  2) 배경·인물을 각각 작은 삼각형(기본 1만 5천·1만 개 = 촘촘하게, 깨져 보이지 않게)으로 나누고 삼각형마다 그림 색
  3) Blender(로우폴리_블렌더.py): 인물 층을 앞에 세우고 카메라가 옆으로 움직이며 살짝 다가감 → 앞뒤가 다른 속도로 움직여 입체
  4) 첫 장면에 그리는 효과(그리는효과.py, 흰 종이 → 먹선 → 색칠)를 --그리는효과 초만큼 붙임 (0 이면 없음)
  필요: blender (세션 시작 때 자동 설치), .supertonic_venv (opencv·scipy), xvfb-run
  한 장면 9초 기준 약 2~3분 (CPU 4개)"""
import argparse, json, os, subprocess, sys, tempfile
import numpy as np, cv2
from scipy.spatial import Delaunay

HERE = os.path.dirname(os.path.abspath(__file__))


def _pts(src, region, n, rng):
    """모서리(윤곽선) 위 점 55% + 흩뿌린 점 → 모양이 살아 있는 삼각형"""
    e = (cv2.Canny(cv2.cvtColor(src, cv2.COLOR_RGB2GRAY), 60, 160) > 0) & region
    ys, xs = np.nonzero(e)
    k = min(len(xs), int(n * .55))
    out = []
    if k:
        sel = rng.choice(len(xs), k, replace=False)
        out.append(np.c_[xs[sel], ys[sel]].astype(float))
    ys, xs = np.nonzero(region)
    sel = rng.choice(len(xs), min(len(xs), n - k), replace=False)
    out.append(np.c_[xs[sel], ys[sel]].astype(float))
    return np.vstack(out)


def _colors(src, P, T):
    H, W = src.shape[:2]
    cols = []
    for t in T:
        tri = np.round(P[t]).astype(np.int32)
        x0, y0 = np.clip(tri.min(0), 0, [W - 1, H - 1]); x1, y1 = np.clip(tri.max(0) + 1, 1, [W, H])
        mk = np.zeros((y1 - y0, x1 - x0), np.uint8)
        cv2.fillConvexPoly(mk, tri - [x0, y0], 1)
        sel = src[y0:y1, x0:x1][mk.astype(bool)]
        cols.append((sel.mean(0) if len(sel) else src[min(H - 1, y0), min(W - 1, x0)]) / 255.0)
    return np.array(cols)


def build_mesh(img_rgb, bg_rgb, mask, n_bg, n_fg, seed=1):
    rng = np.random.default_rng(seed)
    H, W = img_rgb.shape[:2]
    border = [(x, 0) for x in np.linspace(0, W - 1, 24)] + [(x, H - 1) for x in np.linspace(0, W - 1, 24)] \
           + [(0, y) for y in np.linspace(0, H - 1, 14)] + [(W - 1, y) for y in np.linspace(0, H - 1, 14)]
    P = np.vstack([np.array(border, float), _pts(bg_rgb, np.ones((H, W), bool), n_bg, rng)])
    T = Delaunay(P).simplices
    layers = [{"name": "bg", "pts": P.tolist(), "tris": T.tolist(), "cols": _colors(bg_rgb, P, T).tolist()}]
    if mask is not None and mask.any():
        er = cv2.erode(mask.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool)
        cs, _ = cv2.findContours(mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        cp = [c[::6, 0, :] for c in cs if len(c) > 30]
        P = np.vstack(([np.vstack(cp).astype(float)] if cp else []) + [_pts(img_rgb, er, n_fg, rng)])
        T = Delaunay(P).simplices

        def inside(q):
            return mask[np.clip(q[:, 1].astype(int), 0, H - 1), np.clip(q[:, 0].astype(int), 0, W - 1)]
        tp = P[T]          # 가운데와 세 변의 가운데가 모두 인물 안 (윤곽 밖으로 걸친 조각 빼기 — 말 귀 사이 삼각형, 2026-11-08)
        T = T[inside(tp.mean(1)) & inside((tp[:, 0] + tp[:, 1]) / 2) & inside((tp[:, 1] + tp[:, 2]) / 2) & inside((tp[:, 0] + tp[:, 2]) / 2)]
        layers.append({"name": "fg", "pts": P.tolist(), "tris": T.tolist(), "cols": _colors(img_rgb, P, T).tolist()})
    return {"W": W, "H": H, "layers": layers}


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("image"); ap.add_argument("mask"); ap.add_argument("out")
    ap.add_argument("--초", type=float, default=9.0); ap.add_argument("--움직임", default="right")
    ap.add_argument("--그리는효과", type=float, default=3.5); ap.add_argument("--조각", default="15000,10000")
    ap.add_argument("--크기", default="1920x1080")
    a = ap.parse_args(argv)
    RW, RH = (int(x) for x in a.크기.split("x"))
    n_bg, n_fg = (int(x) for x in a.조각.split(","))
    im = cv2.cvtColor(cv2.imread(a.image), cv2.COLOR_BGR2RGB)
    m = None if a.mask == "-" else cv2.resize(cv2.imread(a.mask, 0), (im.shape[1], im.shape[0])) > 127
    bg = im
    if m is not None and m.any():
        big = cv2.dilate(m.astype(np.uint8) * 255, np.ones((31, 31), np.uint8))
        bg = cv2.inpaint(im, big, 12, cv2.INPAINT_TELEA)
    work = tempfile.mkdtemp(prefix="lowpoly_")
    js = os.path.join(work, "mesh.json")
    json.dump(build_mesh(im, bg, m, n_bg, n_fg), open(js, "w"))
    draw = max(0.0, min(a.그리는효과, a.초 - 1.0))
    move = os.path.join(work, "move.mp4")
    r = subprocess.run(["xvfb-run", "-a", "blender", "-b", "-P", os.path.join(HERE, "로우폴리_블렌더.py"), "--", js, move,
                        f"{a.초 - draw:.2f}", str(RW), str(RH), a.움직임], capture_output=True, text=True)
    if "DONE" not in r.stdout:
        sys.exit("블렌더 실패: " + (r.stdout + r.stderr)[-800:])
    if draw <= 0:
        os.replace(move, a.out); print("OK", a.out); return
    f0 = os.path.join(work, "f0.png"); m1 = os.path.join(work, "m.png"); dr = os.path.join(work, "draw.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", move, "-frames:v", "1", f0], check=True)
    cv2.imwrite(m1, cv2.resize(m.astype(np.uint8) * 255, (RW, RH)) if m is not None else np.zeros((RH, RW), np.uint8))
    subprocess.run([sys.executable, "-X", "utf8", os.path.join(HERE, "그리는효과.py"), f0, m1 if m is not None else "-", dr,
                    "--초", f"{draw:.2f}", "--fps", "24"], check=True, capture_output=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", dr, "-i", move, "-filter_complex",
                    "[0:v]fps=24,format=yuv420p,setsar=1[a];[1:v]fps=24,format=yuv420p,setsar=1[b];[a][b]concat=n=2:v=1[v]",
                    "-map", "[v]", "-c:v", "libx264", "-crf", "18", a.out], check=True)
    print("OK", a.out)


if __name__ == "__main__":
    main(sys.argv[1:])
