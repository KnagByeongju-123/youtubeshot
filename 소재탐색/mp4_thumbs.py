r"""
완성된 MP4 에서 장면을 뽑아 썸네일 후보를 만듦 (무료, 로컬)

  python mp4_thumbs.py <영상.mp4> [--문구 "윗줄\n아랫줄"] [--소재명 "달의 두 얼굴"] [--상태 "가설 제안"]
                      [--간격 5] [--장면 4] [--위 0.12] [--아래 0.22] [--후보폴더] [--ffmpeg 경로]

흐름
  1) ffmpeg 로 --간격 초마다 프레임 추출 (인트로·아웃트로 각 3% 제외)
  2) 프레임 점수: 선명도(가장자리 분산) + 밝기(너무 어둡거나 밝으면 감점) + 색감 + 중복(지문) 제거
     → 시간대가 서로 다른 상위 --장면 개 선택.  자막·제목이 구워진 위/아래 띠는 --위/--아래 비율만큼 잘라냄
  3) layouts.py 로 후보 생성: A 피사체 중심형(1위 장면) · C 증거 확대형(1위) · B 좌우 비교형(1위+2위) · A'(2위, 왼쪽 배치) · C'(3위)
     + 한눈에 보는 모음표(후보_모음표.jpg) + meta.json(장면 시각·점수·크롭 좌표·문구)
  4) 결과: <영상 폴더>\<영상이름>_썸네일_mp4\   (--후보폴더: 같은 자리의 <영상이름>_썸네일_후보\ 에 '외부_mp4_' 이름으로도 복사)

문구: --문구 를 주면 그대로, 없으면 thumbs.thumb_copies 의 상태별 틀에 --소재명(없으면 제목 앞부분)을 넣음.
      --상태 는 해결 근거 / 가설 제안 / 미해결 / 확인 필요 (기본 '확인 필요' = 단정 표현 없음)
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)


def find_ffmpeg(explicit=None):
    if explicit and os.path.exists(explicit):
        return explicit
    p = shutil.which("ffmpeg")
    if p:
        return p
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return ""


def video_duration(ffmpeg, path):
    r = subprocess.run([ffmpeg, "-i", path], capture_output=True, text=True, errors="ignore")
    m = re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", r.stderr or "")
    if not m:
        return 0.0
    return int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))


def extract_frames(ffmpeg, path, out_dir, every=5.0, skip_ratio=0.03, max_frames=150):
    """every 초마다 프레임을 JPG 로. 반환: [(초, 경로)]"""
    dur = video_duration(ffmpeg, path)
    if dur <= 0:
        raise RuntimeError("영상 길이를 읽지 못했습니다 (ffmpeg 가 파일을 열지 못함)")
    start, end = dur * skip_ratio, dur * (1 - skip_ratio)
    every = max(every, (end - start) / max_frames)
    os.makedirs(out_dir, exist_ok=True)
    pattern = os.path.join(out_dir, "f%04d.jpg")
    cmd = [ffmpeg, "-y", "-loglevel", "error", "-ss", f"{start:.2f}", "-to", f"{end:.2f}", "-i", path,
           "-vf", f"fps=1/{every:.3f},scale='min(1920,iw)':-2", "-q:v", "3", pattern]
    subprocess.run(cmd, check=True, capture_output=True)
    frames = sorted(f for f in os.listdir(out_dir) if f.startswith("f") and f.endswith(".jpg"))
    return [(start + i * every, os.path.join(out_dir, f)) for i, f in enumerate(frames)], dur


# ------------------------------------------------------------------ 장면 점수

def dhash(img, size=8):
    g = img.convert("L").resize((size + 1, size))
    px = g.load()
    bits = 0
    for y in range(size):
        for x in range(size):
            bits = (bits << 1) | (px[x, y] > px[x + 1, y])
    return bits


def hamming(a, b):
    return bin(a ^ b).count("1")


def score_frame(img, top=0.12, bottom=0.22):
    """자막·제목 띠를 뺀 영역의 선명도·밝기·색감 점수 (0~100 근처)"""
    from PIL import ImageFilter, ImageStat
    w, h = img.size
    core = img.crop((0, int(h * top), w, int(h * (1 - bottom))))
    small = core.resize((320, max(1, int(320 * core.height / core.width))))
    g = small.convert("L")
    edges = g.filter(ImageFilter.FIND_EDGES)
    sharp = ImageStat.Stat(edges).stddev[0]                      # 0~60 정도
    bright = ImageStat.Stat(g).mean[0]                            # 0~255
    hsv = small.convert("HSV")
    sat = ImageStat.Stat(hsv.split()[1]).mean[0]                   # 0~255
    contrast = ImageStat.Stat(g).stddev[0]
    s = min(sharp, 40) * 1.2 + min(contrast, 70) * 0.5 + min(sat, 120) * 0.15
    if bright < 45:
        s -= (45 - bright) * 0.8          # 너무 어두움
    elif bright > 200:
        s -= (bright - 200) * 0.8         # 너무 밝음(흰 화면)
    return round(s, 1), {"sharp": round(sharp, 1), "bright": round(bright, 1), "sat": round(sat, 1), "contrast": round(contrast, 1)}


def pick_scenes(frames, n=4, top=0.12, bottom=0.22, min_gap=20.0, min_hash_dist=10):
    """점수 높은 순으로, 시간 간격·화면 지문이 충분히 다른 장면 n개"""
    from PIL import Image
    scored = []
    for t, p in frames:
        try:
            with Image.open(p) as im:
                im = im.convert("RGB")
                s, parts = score_frame(im, top, bottom)
                scored.append({"t": t, "path": p, "score": s, "parts": parts, "hash": dhash(im)})
        except Exception:
            continue
    scored.sort(key=lambda x: -x["score"])
    picked = []
    for c in scored:
        if any(abs(c["t"] - p["t"]) < min_gap or hamming(c["hash"], p["hash"]) < min_hash_dist for p in picked):
            continue
        picked.append(c)
        if len(picked) >= n:
            break
    return picked, scored


def detect_bands(frames, max_frames=48, cap=0.42):
    """구워진 자막 상자·제목 막대가 차지하는 위/아래 띠를 찾음 (영상마다 레이아웃이 달라 고정 비율 대신 감지).
    두 신호를 합침: (1) 시간에 따라 거의 변하지 않는 픽셀(제목 글자·색 막대·상자 테두리)의 행별 비율
                    (2) 평균 밝기가 화면 가운데보다 꾸준히 어두운 행(반투명 자막 상자)
    반환: (위 비율, 아래 비율, 진단 dict). 못 찾으면 (0, 0, …)."""
    from PIL import Image
    W, Hh = 160, 90
    step = max(1, len(frames) // max_frames)
    grids = []
    for _, p in frames[::step]:
        try:
            with Image.open(p) as im:
                grids.append(im.convert("L").resize((W, Hh)).tobytes())   # bytes 인덱싱 = 0~255 정수
        except Exception:
            continue
    n = len(grids)
    if n < 6:
        return 0.0, 0.0, {"reason": "프레임 부족"}
    static_frac, mean_row = [], []
    for y in range(Hh):
        static = 0
        row_sum = 0.0
        for x in range(W):
            i = y * W + x
            col = [g[i] for g in grids]
            mu = sum(col) / n
            var = sum((v - mu) ** 2 for v in col) / n
            static += var < 36            # 표준편차 6 미만 = 거의 안 변함
            row_sum += mu
        static_frac.append(static / W)
        mean_row.append(row_sum / W)
    mid = sorted(mean_row[int(Hh * 0.25):int(Hh * 0.7)])
    mid_bright = mid[len(mid) // 2] if mid else 128.0
    overall_static = sum(static_frac) / Hh
    if overall_static > 0.6:               # 거의 정지 화면 영상 → 신호 무의미
        return 0.0, 0.0, {"reason": "화면 변화가 적어 판정 불가", "static": round(overall_static, 2)}

    def is_band(y, region):
        dark = mean_row[y] < mid_bright * 0.62
        return static_frac[y] > max(0.10, overall_static * 2.5) or (region == "bottom" and dark)

    # 아래: 맨 아래 행부터 위로, 띠 행이 아닌 구간이 4행 이상 이어지면 멈춤
    bottom_rows, gap, last = 0, 0, -1
    for k in range(int(Hh * cap)):
        y = Hh - 1 - k
        if is_band(y, "bottom"):
            last, gap = k, 0
        else:
            gap += 1
            if gap > 4:
                break
    bottom_rows = last + 1 if last >= 2 else 0
    top_rows, gap, last = 0, 0, -1
    for y in range(int(Hh * cap)):
        if is_band(y, "top"):
            last, gap = y, 0
        else:
            gap += 1
            if gap > 4:
                break
    top_rows = last + 1 if last >= 2 else 0
    diag = {"static_overall": round(overall_static, 2), "mid_brightness": round(mid_bright, 1),
            "bottom_rows": bottom_rows, "top_rows": top_rows}
    return (round(min((top_rows + 1) / Hh, cap), 3) if top_rows else 0.0,
            round(min((bottom_rows + 1) / Hh, cap), 3) if bottom_rows else 0.0, diag)


def bands_from_project(video):
    """영상 옆 <이름>_프로젝트.json 의 자막 레이아웃·제목 위치로 띠 기본값 추정 (감지가 실패했을 때 대비책)."""
    p = os.path.splitext(video)[0] + "_프로젝트.json"
    if not os.path.exists(p):
        return None
    try:
        s = json.load(open(p, encoding="utf-8")).get("settings", {})
    except Exception:
        return None
    lay = str(s.get("sub_layout") or s.get("style_preset") or "")
    head = str(s.get("head_pos") or "")
    bottom = 0.32 if "뉴스" in lay else 0.24 if "시네마" in lay else 0.22
    top = 0.0 if "숨김" in head or str(s.get("head_show", "")).lower() in ("0", "false", "off") else \
        0.18 if "가운데" in head else 0.10
    if "시네마" in lay:
        top = max(top, 0.12)
    return top, bottom, {"from": os.path.basename(p), "sub_layout": lay, "head_pos": head}


def trim_bands(src, dst, top=0.12, bottom=0.22):
    """자막·제목 띠를 잘라낸 사진 저장 (레이아웃 입력용)"""
    from PIL import Image
    with Image.open(src) as im:
        w, h = im.size
        im.convert("RGB").crop((0, int(h * top), w, int(h * (1 - bottom)))).save(dst, "JPEG", quality=95)
    return dst


# ------------------------------------------------------------------ 후보 생성

def hms(t):
    return f"{int(t // 60):02d}:{int(t % 60):02d}"


def make_candidates(scenes, copies, font_path, status, out_dir, title):
    import layouts
    from PIL import Image, ImageDraw, ImageFont
    cands, metas = [], []
    c = copies + copies  # 부족하면 돌려 씀
    plan = [("01_A_피사체", lambda o: layouts.layout_subject(scenes[0]["cut"], c[0], font_path, status, o, side="right", frac=0.55), [0]),
            ("02_C_확대", lambda o: layouts.layout_zoom(scenes[0]["cut"], c[1], font_path, status, o), [0])]
    if len(scenes) >= 2:
        plan.append(("03_B_비교", lambda o: layouts.layout_compare(scenes[0]["cut"], scenes[1]["cut"], c[2], font_path, status, o,
                                                                 labels=("장면 1", "장면 2")), [0, 1]))
        plan.append(("04_A_피사체_장면2", lambda o: layouts.layout_subject(scenes[1]["cut"], c[2], font_path, status, o, side="left", frac=0.45), [1]))
    if len(scenes) >= 3:
        plan.append(("05_C_확대_장면3", lambda o: layouts.layout_zoom(scenes[2]["cut"], c[0], font_path, status, o), [2]))
    for name, fn, used in plan:
        out = os.path.join(out_dir, name + ".jpg")
        try:
            meta = fn(out)
        except Exception as e:
            metas.append({"file": name + ".jpg", "error": str(e)})
            continue
        meta.update({"file": name + ".jpg", "scenes": [{"t": hms(scenes[i]["t"]), "seconds": round(scenes[i]["t"], 1),
                                                       "score": scenes[i]["score"]} for i in used]})
        cands.append(out)
        metas.append(meta)
    # 모음표
    if cands:
        tw, th = 426, 240
        cols = 3
        rows = (len(cands) + cols - 1) // cols
        sheet = Image.new("RGB", (tw * cols + 8 * (cols + 1), (th + 30) * rows + 8), "#202020")
        dr = ImageDraw.Draw(sheet)
        try:
            fnt = ImageFont.truetype(font_path, 15)
        except Exception:
            fnt = ImageFont.load_default()
        for i, p in enumerate(cands):
            x, y = 8 + (i % cols) * (tw + 8), 8 + (i // cols) * (th + 30)
            with Image.open(p) as im:
                sheet.paste(im.convert("RGB").resize((tw, th), Image.LANCZOS), (x, y))
            dr.text((x + 2, y + th + 6), f"{i + 1}. {os.path.basename(p)[:-4]}", font=fnt, fill="white")
        sheet.save(os.path.join(out_dir, "후보_모음표.jpg"), "JPEG", quality=88)
    return cands, metas


def main(argv=None):
    ap = argparse.ArgumentParser(description="완성된 MP4 에서 썸네일 후보 만들기")
    ap.add_argument("video")
    ap.add_argument("--문구", action="append", help="썸네일 문구 (줄바꿈은 \\n). 여러 번 주면 안마다 다르게")
    ap.add_argument("--소재명", default="", help="문구 틀의 [소재] 자리 (기본: 제목 앞부분)")
    ap.add_argument("--제목", default="", help="영상 제목 (기본: 파일 이름)")
    ap.add_argument("--상태", default="확인 필요", choices=["해결 근거", "가설 제안", "미해결", "확인 필요"])
    ap.add_argument("--간격", type=float, default=5.0, help="프레임 추출 간격(초), 기본 5")
    ap.add_argument("--장면", type=int, default=4, help="고를 장면 수, 기본 4")
    ap.add_argument("--위", type=float, default=None, help="잘라낼 위쪽 띠 비율(제목). 기본: 자동 감지")
    ap.add_argument("--아래", type=float, default=None, help="잘라낼 아래쪽 띠 비율(자막). 기본: 자동 감지")
    ap.add_argument("--후보폴더", action="store_true", help="<영상이름>_썸네일_후보\\ 에도 '외부_mp4_' 이름으로 복사")
    ap.add_argument("--썸네일선택", default="수동", choices=["자동", "수동", "없음"],
                    help="후보 중 최종 1장 고르기: 자동(점수) / 수동(클릭 창, 기본) / 없음")
    ap.add_argument("--최종적용", action="store_true",
                    help="고른 썸네일을 <영상이름>_썸네일_유튜브.jpg 로 저장 (기존 파일은 _이전.jpg 로 보관)")
    ap.add_argument("--ffmpeg", default="")
    ap.add_argument("--out", default="", help="결과 폴더 (기본: <영상 폴더>\\<영상이름>_썸네일_mp4)")
    a = ap.parse_args(argv)
    import thumbs

    video = os.path.abspath(a.video)
    if not os.path.exists(video):
        ap.error(f"영상 파일이 없습니다: {video}")
    ffmpeg = find_ffmpeg(a.ffmpeg)
    if not ffmpeg:
        ap.error("ffmpeg 를 찾지 못했습니다 (--ffmpeg 경로 지정, 또는 pip install imageio-ffmpeg)")
    font_path = thumbs.find_font()
    if not font_path:
        ap.error("한국어 폰트를 찾지 못했습니다")
    stem = os.path.splitext(os.path.basename(video))[0]
    title = a.제목 or stem
    out_dir = a.out or os.path.join(os.path.dirname(video), stem + "_썸네일_mp4")
    os.makedirs(out_dir, exist_ok=True)
    stamp = time.strftime("%Y%m%d_%H%M%S")

    t0 = time.time()
    with tempfile.TemporaryDirectory() as tmp:
        frames, dur = extract_frames(ffmpeg, video, tmp, every=a.간격)
        auto_top, auto_bottom, diag = detect_bands(frames)
        proj = bands_from_project(video)
        src = "자동 감지"
        if auto_bottom == 0 and auto_top == 0 and proj:
            auto_top, auto_bottom, src = proj[0], proj[1], f"프로젝트 설정({proj[2]['sub_layout'] or '기본'} · 제목 {proj[2]['head_pos'] or '?'})"
        elif proj and auto_bottom < proj[1] * 0.7:   # 감지가 너무 얕으면 설정 기준으로 보정
            auto_bottom, src = proj[1], "자동 감지 + 프로젝트 설정 보정"
        top = a.위 if a.위 is not None else auto_top
        bottom = a.아래 if a.아래 is not None else auto_bottom
        band_note = (f"자막·제목 띠: 위 {top:.0%} · 아래 {bottom:.0%} ({src}"
                     + ("; 수동 지정값 우선" if (a.위 is not None or a.아래 is not None) else "") + f") {diag}")
        print(band_note)
        a.위, a.아래 = top, bottom
        scenes, scored = pick_scenes(frames, n=a.장면, top=top, bottom=bottom)
        if not scenes:
            print("쓸 만한 장면을 찾지 못했습니다")
            return 1
        scene_dir = os.path.join(out_dir, "장면")
        os.makedirs(scene_dir, exist_ok=True)
        for i, sc in enumerate(scenes, 1):
            full = os.path.join(scene_dir, f"{i:02d}_{hms(sc['t']).replace(':', 'm')}s_원본.jpg")
            shutil.copy(sc["path"], full)
            sc["full"] = full
            sc["cut"] = trim_bands(full, os.path.join(scene_dir, f"{i:02d}_{hms(sc['t']).replace(':', 'm')}s.jpg"), a.위, a.아래)
    print(f"영상 {hms(dur)} · 프레임 {len(frames)}장 분석 → 장면 {len(scenes)}개 선택 ({time.time() - t0:.0f}초)")
    for i, sc in enumerate(scenes, 1):
        print(f"  장면 {i}: {hms(sc['t'])}  점수 {sc['score']}  {sc['parts']}")

    # 문구
    if a.문구:
        copies = [c.replace("\\n", "\n") for c in a.문구]
    else:
        name = a.소재명 or re.split(r"[,.?!:·—\-–]", title)[0].strip()[:14] or title[:14]
        item = {"status": a.상태, "title": title, "summary": "", "tech": ""}
        copies = thumbs.thumb_copies(item, name)
    while len(copies) < 3:
        copies.append(copies[-1])

    cands, metas = make_candidates(scenes, copies, font_path, a.상태, out_dir, title)
    meta = {"video": video, "title": title, "duration": hms(dur), "made": stamp, "status": a.상태,
            "bands_trimmed": {"top": a.위, "bottom": a.아래, "detected": {"top": auto_top, "bottom": auto_bottom}},
            "frame_interval_sec": a.간격,
            "scenes": [{"rank": i + 1, "t": hms(sc["t"]), "seconds": round(sc["t"], 1), "score": sc["score"], "parts": sc["parts"],
                        "full_frame": sc["full"], "trimmed": sc["cut"]} for i, sc in enumerate(scenes)],
            "copies": copies, "candidates": metas,
            "note": "장면은 영상 자체에서 뽑은 프레임이며 자막·제목 띠만 잘라냈습니다. 명암·색감·선명도 보정 외 내용 변형 없음."}
    with open(os.path.join(out_dir, "meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2, default=str)
    if a.후보폴더 and cands:
        cdir = os.path.join(os.path.dirname(video), stem + "_썸네일_후보")
        os.makedirs(cdir, exist_ok=True)
        for p in cands:
            shutil.copy(p, os.path.join(cdir, "외부_mp4_" + os.path.basename(p)))
        print(f"후보 폴더에도 복사: {cdir}\\외부_mp4_*.jpg")
    print(f"완료: 후보 {len(cands)}장 → {out_dir}\n  모음표: {os.path.join(out_dir, '후보_모음표.jpg')}")
    # ---- 최종 1장 고르기 (자동 / 수동 / 없음)
    if cands and a.썸네일선택 != "없음":
        import thumb_pick
        final, msg = thumb_pick.pick(out_dir, a.썸네일선택, title=title)
        print("  " + msg)
        if final and a.최종적용:
            dest = os.path.join(os.path.dirname(video), stem + "_썸네일_유튜브.jpg")
            if os.path.exists(dest):
                shutil.copy(dest, os.path.splitext(dest)[0] + "_이전.jpg")
            shutil.copy(final, dest)
            print(f"  유튜브 썸네일로 적용: {dest} (기존 파일은 _이전.jpg 로 보관)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
