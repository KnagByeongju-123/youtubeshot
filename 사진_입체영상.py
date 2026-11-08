"""장문 다큐 사진 → 블렌더 입체 영상 자동 (사용자 결정 2026-11-07 '자동으로 사용되도록', 규칙 `장문다큐.md` 4장)
xvfb-run -a python -X utf8 사진_입체영상.py <프로젝트.json> [--최대 10] [--통과 2] [--다시] [--보기]
  - 프로젝트의 [사진: 경로 | 설명 | 출처] 마다 화면에 나오는 시간을 재고(영상과 같은 방법),
    입체에 맞는 사진만 골라 '<사진>.입체.mp4' 를 사진 옆에 만듦 → render_project 가 그 사진 자리에 이 영상을 씀(_clip_frame)
  - 고르는 법:
    · 빼는 것: 설명에 지도·도표·그래프·논문·문서·기록·비문·글씨·표·그림 이 있거나, 깊이 차이(위·아래 10% 차)가 0.35 미만(평평한 사진)
    · 인물 사진도 함(사용자 결정 2026-11-07): 전진+오르빗, 공간 통과는 안 함. 세로 사진은 16:9 로 잘라(위쪽 25% 기준, 얼굴) 찍음
    · 카메라: 설명에 탑·첨탑·기둥·미나렛·오벨리스크·등대·종탑 → 좌우 흔들기(sway), 나머지 → 전진+오르빗(orbit 12도)
    · 공간 통과: 설명이 장소·풍경(들판·숲·폭포·산·광장·유적지 …)이고, 앞층(가까운 30%)이 화면의 12~40% 이며 화면 아래 가운데를 다 덮지 않는 사진 중
      깊이 차이가 큰 순으로 --통과(기본 2)장. 사람이 주인공인 사진·인물은 전진+오르빗 (카메라 규칙, 장문다큐.md 4장)
    · 옛 사진·엽서·사진관 사진(스캔한 인쇄물)은 평면
    · 깊이 차이가 큰 순으로 최대 --최대(기본 10)장
  - 한 장에 1~2분 (블렌더 단순 그리기, 영상 길이 = 그 사진이 나오는 시간, 최대 16초 → 넘으면 늘여 씀)
  - 가장자리 까짐 검사(사용자 지적 2026-11-07, 필수): 블렌더가 빈 곳을 투명으로 저장(--key) → 모든 장면에서 빈 곳이 안 보일 만큼 가운데 확대(+3%, 최소 8%)
    → 확대한 화면을 6장마다 다시 검사. 1.32배 넘게 잘라야 하면 카메라를 당겨 다시 → 흔들기로 다시 → 그래도 안 되면 평면(입체 안 씀)
  - --다시: 이미 있는 .입체.mp4 도 다시 만듦, --보기: 고르기만 하고 만들지 않음"""
import json
import math
import os
import re
import shutil
import subprocess
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SKIP_WORDS = ("지도", "도표", "그래프", "논문", "문서", "기록", "비문", "글씨", "표 ", "그림", "삽화", "문자", "편지", "신문", "옛 사진", "엽서", "사진관", "초판", "필사본")
PASS_WORDS = ("들판", "숲", "폭포", "산", "계곡", "정원", "광장", "풍경", "유적지", "평원", "해변", "호수", "골짜기", "사막", "밀림", "성벽")   # 공간 통과는 이런 장소 사진만 (사람이 주인공인 사진은 안 함)
PORTRAIT_WORDS = ("초상", "얼굴", "인물", "사진 속", "모습")   # 인물 사진도 전진+오르빗 (사용자 결정 2026-11-07: '인물사진 오르빗도 좋았어')
THIN_WORDS = ("탑", "첨탑", "기둥", "미나렛", "오벨리스크", "등대", "종탑", "돛대")
DEPTH_MODEL = os.path.join(HERE, "models", "depth_anything_v2_small_fp16.onnx")
DEPTH_URL = "https://huggingface.co/onnx-community/depth-anything-v2-small/resolve/main/onnx/model_fp16.onnx"
SD_PY = os.path.join(HERE, ".sd_venv", "bin", "python")
ST_PY = os.path.join(HERE, ".supertonic_venv", "bin", "python")


def spans(proj):
    """사진 경로 → 화면에 나오는 (처음, 끝) 초 — 배경음_구간.times 와 같은 방법(영상과 같은 시간)"""
    import importlib.util
    sys.argv = [sys.argv[0]]
    spec = importlib.util.spec_from_file_location("gap", os.path.join(HERE, "그림_간격_보강.py"))
    g = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(g)
    m = g.importlib.util.module_from_spec(g.importlib.util.spec_from_file_location("snm", os.path.join(HERE, "shorts_novel_maker_supertonic.py")))
    m.__spec__.loader.exec_module(m)
    app = m.App()
    app.withdraw()
    c = json.load(open(proj, encoding="utf-8"))
    cur = app.get_settings()
    st = dict(c.get("settings") or {})
    orig = dict(st)
    for k in m.KEEP_KEYS:
        if not str(st.get(k, "")).strip() or k in m.SECRET_KEYS:
            st[k] = cur.get(k, m.DEFAULTS.get(k, ""))
    c["settings"] = st
    app.apply_cfg(c)
    app.update()
    for k_, v_ in orig.items():
        if k_ in app.vars and k_ not in ("format", "style_preset", "color_preset") and k_ not in m.SECRET_KEYS and k_ not in m.KEEP_KEYS:
            app.vars[k_].set(str(v_))
    app.update()
    s = app.get_settings()
    m.set_tts_cfg(s)
    story = app.get_story()
    gate = m.PauseGate(os.path.join(HERE, "장문_일시정지중.flag"), app.cancel, print)
    narr = app.narration_for(story, s, lambda x: None, gate)
    r = m.make_renderer(app.title_var.get().strip(), story, s, narr)
    out = {}
    for im_, t0, t1 in g.shown_runs(r):
        p = r.img_paths[im_]
        a, z = out.get(p, (t0, t1))
        out[p] = (min(a, t0), max(z, t1))
    app.destroy()
    return out


def photos(proj):
    c = json.load(open(proj, encoding="utf-8"))
    res = []
    for line in c.get("story", "").splitlines():
        m = re.match(r"\s*\[사진:\s*([^|\]]+)\|?([^|\]]*)\|?([^\]]*)\]", line)
        if m:
            res.append((m.group(1).strip(), m.group(2).strip()))
    return res


def ensure_model():
    if not os.path.exists(DEPTH_MODEL):
        os.makedirs(os.path.dirname(DEPTH_MODEL), exist_ok=True)
        subprocess.run(["curl", "-sSL", "-o", DEPTH_MODEL, DEPTH_URL], check=True)


def depth_of(path, work):
    out = subprocess.run([ST_PY, "-X", "utf8", os.path.join(HERE, "depth_worker.py"), DEPTH_MODEL, work, path],
                         capture_output=True, text=True).stdout
    for ln in out.splitlines():
        if ln.startswith("OK "):
            return ln.split()[-1]
    return None


def fg_ok(npy):
    d = np.load(npy).astype(np.float32)
    thr = np.quantile(d, 0.7)
    m = d >= thr
    h, w = m.shape
    bottom_center = m[int(h * 0.75):, int(w * 0.3):int(w * 0.7)].mean()
    return 0.12 <= m.mean() <= 0.40 and bottom_center < 0.7


def key_mask(fr):
    """빈 곳 픽셀 (블렌더 --key 는 빈 곳을 투명으로 저장)"""
    return fr[..., 3] < 200


def need_crop(fr_dir):
    """모든 장면에서 빈 곳(자홍)이 화면에 안 들어오게 하는 가운데 확대 배율 (1.0 = 그대로). 가운데까지 비면 큰 수"""
    from PIL import Image
    need = 1.0
    files = sorted(f for f in os.listdir(fr_dir) if f.endswith(".png"))
    for f in files:
        fr = np.asarray(Image.open(os.path.join(fr_dir, f)).convert("RGBA").resize((320, 180)))
        m = key_mask(fr)
        if not m.any():
            continue
        ys, xs = np.nonzero(m)
        dx = np.abs(xs + 0.5 - 160) / 160
        dy = np.abs(ys + 0.5 - 90) / 90
        need = max(need, float((1.0 / np.maximum(np.maximum(dx, dy), 1e-3)).max()))
    return need


def blend_render(path, npy, mode, frames, fr_dir, work, zoom):
    shutil.rmtree(fr_dir, ignore_errors=True)
    blender = ["xvfb-run", "-a", "-s", "-screen 0 1920x1080x24", "blender", "-b", "-P"]
    if mode == "통과":
        lay = os.path.join(work, "층")
        if not os.path.exists(os.path.join(lay, "뒤층.png")):
            subprocess.run([SD_PY, "-X", "utf8", os.path.join(HERE, "사진_층나누기.py"), path, npy, lay, "--앞비율", "0.3"], check=True,
                           stdout=subprocess.DEVNULL)
        cmd = blender + [os.path.join(HERE, "블렌더", "사진_공간통과.py"), "--", path, npy, lay, fr_dir, "--push", "0.6",
                         "--frames", str(frames), "--key"]
    else:
        cmd = blender + [os.path.join(HERE, "블렌더", "사진_로우폴리입체.py"), "--", path, npy, fr_dir, "--smooth", "--grid", "260",
                         "--frames", str(frames), "--key", "--zoom", str(zoom)]
        cmd += ["--cam", "orbit", "--arc", "12"] if mode == "오르빗" else ["--cam", "sway"]
    subprocess.run(cmd, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def render(path, npy, mode, secs, work, out=None):
    """블렌더로 찍고 → 빈 곳(자홍) 검사 → 안 보일 만큼 가운데 확대 → 다시 검사. 너무 많이 비면 카메라를 당겨 다시, 그래도 안 되면 흔들기, 마지막엔 포기(평면)"""
    from PIL import Image
    frames = max(48, min(16 * 24, int(math.ceil(secs * 24))))
    fr_dir = os.path.join(work, "frames")
    out = out or path + ".입체.mp4"
    tries = [(mode, 0.8 if mode == "오르빗" else 0.86), (mode, 0.68 if mode != "통과" else 0.0), ("흔들기", 0.72)]
    for md, zoom in tries:
        if md == "통과" and zoom == 0.0:
            continue
        blend_render(path, npy, md, frames, fr_dir, work, zoom)
        if not os.path.exists(os.path.join(fr_dir, "frame_0001.png")):
            continue
        c = need_crop(fr_dir)
        print(f"    {md} 카메라 {zoom}: 빈 곳을 없애려면 {c:.2f}배 확대")
        if c > 1.32:                      # 너무 크게 잘라야 하면 화질이 떨어지므로 다른 방법으로
            continue
        c = max(1.08, c * 1.03)           # 여유 3%, 최소 8% (테두리 계단 무늬까지 안 보이게)
        if md == "흔들기":                 # 흔들기는 천천히 다가가는 확대를 더함
            vf = f"zoompan=z='{c:.4f}+0.05*on/{frames}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=1280x720:fps=24"
        else:
            vf = f"crop=iw/{c:.4f}:ih/{c:.4f},scale=1280:720"
        subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-framerate", "24", "-i", os.path.join(fr_dir, "frame_%04d.png"),
                        "-vf", vf, "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "19", out], check=True)
        bad = 0                                       # 확대한 뒤 다시 검사: 잘린 화면 안에 빈 곳이 남았는지 장면마다 확인
        for f in sorted(os.listdir(fr_dir))[::6]:
            fr = np.asarray(Image.open(os.path.join(fr_dir, f)).convert("RGBA"))
            h_, w_ = fr.shape[:2]
            cz = c + (0.05 if md == "흔들기" else 0)
            ch_, cw_ = int(h_ / c / 2), int(w_ / c / 2)
            bad += int(key_mask(fr[h_ // 2 - ch_:h_ // 2 + ch_, w_ // 2 - cw_:w_ // 2 + cw_]).sum() > 20)
        shutil.rmtree(fr_dir, ignore_errors=True)
        if bad == 0:
            return md
        print(f"    완성 영상에 빈 곳 {bad}장 → 다시")
        os.remove(out)
    shutil.rmtree(fr_dir, ignore_errors=True)
    return None


def main(a):
    if not a:
        print(__doc__)
        return 2
    proj = os.path.abspath(a[0])
    most = int(a[a.index("--최대") + 1]) if "--최대" in a else 10
    n_pass = int(a[a.index("--통과") + 1]) if "--통과" in a else 2
    redo, look = "--다시" in a, "--보기" in a
    from PIL import Image
    ensure_model()
    work = os.path.join(os.path.dirname(proj), "_입체작업")
    os.makedirs(work, exist_ok=True)
    lock = os.path.join(work, ".잠금")              # 같은 프로젝트를 두 번 동시에 돌리면 작업 폴더를 서로 지움 (2026-11-08 엘 콜라초)
    if os.path.exists(lock):
        try:
            os.kill(int(open(lock).read().strip()), 0)
            print("⚠ 이미 같은 프로젝트의 입체 영상을 만드는 중 (잠금", lock, ") — 끝난 뒤 다시")
            return 1
        except (OSError, ValueError):
            pass
    open(lock, "w").write(str(os.getpid()))
    print("🎥 사진이 나오는 시간 재는 중...")
    sp = spans(proj)
    cands = []
    for p, cap in photos(proj):
        ap = p if os.path.isabs(p) else os.path.join(os.path.dirname(proj), p)
        if not os.path.exists(ap) or ap.lower().endswith((".mp4", ".gif")):
            continue
        key = next((k for k in sp if os.path.abspath(k) == os.path.abspath(ap)), None)
        if key is None:
            continue
        if any(w in cap for w in SKIP_WORDS):
            print("  평면 (설명)", os.path.basename(ap), cap)
            continue
        im_ = Image.open(ap).convert("RGB")
        w_, h_ = im_.size
        src = ap
        if h_ > w_ * 0.95:                 # 세로 사진(인물 등): 16:9 로 잘라 따로 저장 (얼굴이 있는 위쪽 25% 기준)
            th = int(w_ * 9 / 16)
            top = int((h_ - th) * 0.25)
            src = os.path.join(work, "세로_" + os.path.splitext(os.path.basename(ap))[0] + ".jpg")
            im_.crop((0, top, w_, top + th)).save(src, quality=95)
        npy = depth_of(src, work)
        if not npy:
            continue
        d = np.load(npy).astype(np.float32)
        spread = float(np.quantile(d, 0.9) - np.quantile(d, 0.1))
        if spread < 0.35:
            print("  평면 (깊이 차이 %.2f)" % spread, os.path.basename(ap))
            continue
        mode = "흔들기" if any(w in cap for w in THIN_WORDS) else "오르빗"
        cands.append({"src": src, "portrait": any(w in cap for w in PORTRAIT_WORDS) or src != ap, "path": ap, "cap": cap, "npy": npy, "spread": spread, "mode": mode,
                      "secs": sp[key][1] - sp[key][0], "fg": fg_ok(npy)})
    cands.sort(key=lambda c: -c["spread"])
    pick = cands[:most]
    k = 0
    for c in pick:
        if k < n_pass and c["mode"] == "오르빗" and c["fg"] and not c["portrait"] and any(w in c["cap"] for w in PASS_WORDS):
            c["mode"] = "통과"
            k += 1
    print(f"✅ 입체로 만들 사진 {len(pick)}장 (후보 {len(cands)}장)")
    for c in pick:
        print(f"  {c['mode']:4s} {c['secs']:5.1f}초 깊이차 {c['spread']:.2f}  {os.path.basename(c['path'])}  {c['cap']}")
    if look:
        return 0
    for i, c in enumerate(pick, 1):
        if os.path.exists(c["path"] + ".입체.mp4") and not redo:
            continue
        shutil.rmtree(os.path.join(work, "층"), ignore_errors=True)
        md = render(c["src"], c["npy"], c["mode"], c["secs"], work, out=c["path"] + ".입체.mp4")
        if md:
            print(f"  [{i}/{len(pick)}] 완성 ({md}) {os.path.basename(c['path'])}.입체.mp4 — 가장자리 빈 곳 검사 통과")
        else:
            print(f"  [{i}/{len(pick)}] 빈 곳을 없앨 수 없어 평면으로 둠 {os.path.basename(c['path'])}")
    shutil.rmtree(work, ignore_errors=True)
    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
