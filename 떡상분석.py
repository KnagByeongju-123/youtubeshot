# -*- coding: utf-8 -*-
"""
떡상분석.py — 잘 된(조회수 높은) 영상을 뜯어보는 도구.
Hypit(hypit-ai/hypit) 의 '영상 틀 분석' 아이디어를 이 저장소 도구(받아쓰기 Whisper, 글자 찾기 RapidOCR)로 다시 만든 것.
남의 영상은 **구조(컷 박자·말 빠르기·자막 방식·소리 흐름)만 참고**하고 화면·대사·인물·문구는 가져오지 않는다.

사용법:
  python -X utf8 떡상분석.py <영상.mp4 | 유튜브 주소> [--폴더 결과폴더] [--컷민감도 0.3] [--언어 ko]
                              [--글자읽기 off] [--받아쓰기 off] [--기획 "새 주제"]

  · 유튜브 주소는 yt-dlp 로 받기를 한 번 시도함. 막히면 영상 파일을 직접 올려 그 경로를 줌
  · --기획 "새 주제" : 분석한 틀에 맞춘 새 기획안을 claude -p 로 씀 (<이름>_새기획.md)

결과 (기본 output/떡상분석/<이름>/):
  <이름>_분석.md        요약(길이·컷 수·컷 박자·말 빠르기·첫 3초 훅·화면 글자·소리) + 컷별 시간표
  <이름>_분석.json      같은 내용(다른 도구·기획용)
  <이름>_컷모음_N.jpg   컷마다 한 장, 번호·시간이 붙은 20칸 모음
  <이름>_흐름.png       시간에 따른 소리 크기·컷·말 위치 그래프
"""
import argparse
import json
import os
import re
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
WHISPER_DIR = os.path.join(HERE, "models", "whisper")
WHISPER_SIZE = "small"
SR = 16000


# ───────── 작은 도구 ─────────
def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", **kw)


def tfmt(t):
    m, s = divmod(max(0.0, t), 60)
    return f"{int(m)}:{s:04.1f}"


def font(size):
    for p in ("/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf",
              "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
              "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
              "C:/Windows/Fonts/malgunbd.ttf", "C:/Windows/Fonts/malgun.ttf"):
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def hangul_len(t):
    """말 빠르기용 글자 수 (띄어쓰기·문장부호 빼고)"""
    return len(re.sub(r"[\s\.,!?\"'…·~\-]", "", t or ""))


# ───────── 1. 영상 준비 ─────────
def get_video(src, out_dir):
    if os.path.exists(src):
        return os.path.abspath(src)
    if not re.match(r"https?://", src):
        sys.exit(f"영상 파일을 찾을 수 없음: {src}")
    print("유튜브에서 받는 중…", flush=True)
    tmpl = os.path.join(out_dir, "원본.%(ext)s")
    r = run([sys.executable, "-m", "yt_dlp", "--js-runtimes", "node", "-f", "b[height<=720]/bv*[height<=720]+ba/b",
             "--merge-output-format", "mp4", "-o", tmpl, src])
    for f in os.listdir(out_dir):
        if f.startswith("원본."):
            return os.path.join(out_dir, f)
    tail = "\n".join(r.stderr.strip().splitlines()[-3:])
    sys.exit("유튜브에서 영상을 받지 못했습니다(유튜브가 막음). 영상 파일(mp4)을 직접 올려 그 경로로 다시 실행하세요.\n" + tail)


def probe(path):
    r = run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type,width,height,r_frame_rate",
             "-of", "json", path])
    j = json.loads(r.stdout or "{}")
    info = {"duration": float(j.get("format", {}).get("duration", 0) or 0), "width": 0, "height": 0, "fps": 0,
            "has_audio": False}
    for s in j.get("streams", []):
        if s.get("codec_type") == "video" and not info["width"]:
            info["width"], info["height"] = s.get("width", 0), s.get("height", 0)
            a, _, b = (s.get("r_frame_rate") or "0/1").partition("/")
            info["fps"] = round(float(a) / float(b or 1), 2) if float(b or 1) else 0
        if s.get("codec_type") == "audio":
            info["has_audio"] = True
    return info


# ───────── 2. 컷 찾기 ─────────
def find_cuts(path, dur, th, min_gap=0.35):
    """화면이 확 바뀌는 순간(컷). 장면 변화 값이 th 보다 크거나,
    비슷한 화면끼리 넘어가도 앞뒤 1초보다 6배 넘게 튀면(0.07 이상) 컷"""
    r = run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-an", "-vf",
             "scale=320:-2,select='gte(scene,0)',metadata=print", "-f", "null", "-"])
    ts, sc = [], []
    for t, s in re.findall(r"pts_time:([\d\.]+)[^\n]*\n[^\n]*?scene_score=([\d\.]+)", r.stderr):
        ts.append(float(t))
        sc.append(float(s))
    sc = np.array(sc)
    times = []
    for i, s in enumerate(sc):
        if s >= th:
            times.append(ts[i])
            continue
        if s < 0.07:
            continue
        nb = [sc[j] for j in range(len(sc)) if j != i and abs(ts[j] - ts[i]) <= 1.0]
        if nb and s > 6 * (np.median(nb) + 0.005) and s >= max(nb):
            times.append(ts[i])
    cuts = [0.0]
    for t in times:
        if t - cuts[-1] >= min_gap and dur - t >= min_gap:
            cuts.append(round(t, 2))
    shots = []
    for i, s in enumerate(cuts):
        e = cuts[i + 1] if i + 1 < len(cuts) else dur
        shots.append({"no": i + 1, "start": s, "end": round(e, 2), "len": round(e - s, 2)})
    return shots


def grab_frames(path, shots, fdir):
    os.makedirs(fdir, exist_ok=True)
    for sh in shots:
        t = sh["start"] + min(sh["len"] * 0.5, max(0.2, sh["len"] - 0.1))
        fp = os.path.join(fdir, f"{sh['no']:04d}_{sh['start']:.2f}.jpg")
        if not os.path.exists(fp):
            run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-ss", f"{t:.2f}", "-i", path,
                 "-frames:v", "1", "-vf", "scale='min(720,iw)':-2", "-q:v", "3", fp])
        sh["frame"] = fp if os.path.exists(fp) else ""


# ───────── 3. 화면 글자 ─────────
OCR_KO_DIR = os.path.join(HERE, "models", "ocr_korean")
OCR_KO_URL = "https://huggingface.co/monkt/paddleocr-onnx/resolve/main/languages/korean/"   # PaddleOCR PP-OCRv5 한국어, Apache-2.0


def korean_ocr_model():
    """한국어 글자 읽기 모델(13MB). 없으면 받음. 기본 RapidOCR 모델은 중국어용이라 한글을 못 읽음"""
    os.makedirs(OCR_KO_DIR, exist_ok=True)
    for f in ("rec.onnx", "dict.txt"):
        p = os.path.join(OCR_KO_DIR, f)
        if not os.path.exists(p) or os.path.getsize(p) < 1000:
            import urllib.request
            print(f"  한국어 글자 모델 받는 중: {f}", flush=True)
            urllib.request.urlretrieve(OCR_KO_URL + f, p)
    return os.path.join(OCR_KO_DIR, "rec.onnx"), os.path.join(OCR_KO_DIR, "dict.txt")


def read_text(shots):
    try:
        from rapidocr_onnxruntime import RapidOCR
    except ImportError:
        print("  (RapidOCR 없음 → 화면 글자 읽기 건너뜀. pip install rapidocr_onnxruntime)", flush=True)
        return False
    try:
        rec, keys = korean_ocr_model()
        ocr = RapidOCR(rec_model_path=rec, rec_keys_path=keys, rec_img_shape=[3, 48, 320])
    except Exception as e:
        print(f"  (한국어 글자 모델을 못 받음 → 글자 읽기 건너뜀: {e})", flush=True)
        return False
    for i, sh in enumerate(shots):
        sh["text"], sh["text_pos"], sh["text_size"] = "", "", 0.0
        if not sh.get("frame"):
            continue
        im = Image.open(sh["frame"])
        W, H = im.size
        res, _ = ocr(sh["frame"], use_cls=False)   # 방향 판단은 끔: 바로 선 한글을 뒤집힌 걸로 보고 잘못 읽음('왕의 밥상'→'허움')
        items = []
        for box, txt, conf in (res or []):
            if conf < 0.75 or not txt.strip():
                continue
            ys = [p[1] for p in box]
            items.append((min(ys), max(ys), txt.strip()))
        if not items:
            continue
        items.sort()
        sh["text"] = " / ".join(t for _, _, t in items)[:120]
        cy = np.mean([(a + b) / 2 for a, b, _ in items]) / H
        sh["text_pos"] = "위" if cy < 0.33 else ("가운데" if cy < 0.66 else "아래")
        sh["text_size"] = round(max(b - a for a, b, _ in items) / H * 100, 1)   # 화면 높이 대비 %
        if (i + 1) % 20 == 0:
            print(f"  글자 읽기 {i + 1}/{len(shots)}", flush=True)
    return True


# ───────── 4. 소리 ─────────
def load_audio(path):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", path, "-vn", "-ac", "1", "-ar", str(SR),
                        "-f", "f32le", "-"], capture_output=True)
    return np.frombuffer(r.stdout, np.float32)


def loudness(a, step=0.25):
    n = int(SR * step)
    k = len(a) // n
    if k == 0:
        return np.array([]), step
    rms = np.sqrt((a[:k * n].reshape(k, n) ** 2).mean(axis=1) + 1e-10)
    return 20 * np.log10(rms + 1e-10), step


def transcribe(a, lang):
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        print("  (faster-whisper 없음 → 받아쓰기 건너뜀)", flush=True)
        return []
    os.makedirs(WHISPER_DIR, exist_ok=True)
    w = WhisperModel(WHISPER_SIZE, device="cpu", compute_type="int8", download_root=WHISPER_DIR)
    segs, _ = w.transcribe(a, language=lang or None, beam_size=1, vad_filter=True, word_timestamps=True,
                           condition_on_previous_text=False)
    out = []
    for s in segs:
        words = [(round(x.start, 2), round(x.end, 2), x.word) for x in (s.words or [])]
        if not words:
            words = [(round(s.start, 2), round(s.end, 2), s.text)]
        cur = []
        for w in words:                       # 문장 끝(. ? !)에서 나눔
            cur.append(w)
            if re.search(r"[\.\?!。]\s*$", w[2]):
                out.append(_sent(cur))
                cur = []
        if cur:
            out.append(_sent(cur))
        print(f"  받아쓰기 {tfmt(s.end)}  {s.text.strip()[:40]}", flush=True)
    return out


def _sent(ws):
    return {"start": ws[0][0], "end": ws[-1][1], "text": "".join(w[2] for w in ws).strip(), "words": ws}


def sound_events(db, step, speech):
    """갑자기 커지는 소리(효과음 후보)와 말 없는 곳의 소리 크기(배경음 추정)"""
    if len(db) == 0:
        return [], None
    ev, last = [], -9
    for i in range(4, len(db)):
        base = np.median(db[max(0, i - 8):i])
        if db[i] - base > 9 and db[i] > -35 and i * step - last > 1.0:
            ev.append(round(i * step, 2))
            last = i * step
    talk = np.zeros(len(db), bool)
    for s in speech:
        talk[int(s["start"] / step):int(s["end"] / step) + 1] = True
    quiet = db[~talk]
    bgm = float(np.median(quiet)) if len(quiet) > 4 else None
    return ev, bgm


# ───────── 5. 정리 ─────────
def attach(shots, speech, events):
    words = [w for s in speech for w in s["words"]] or [(s["start"], s["end"], s["text"]) for s in speech]
    for sh in shots:
        said = [w[2] for w in words if sh["start"] <= (w[0] + w[1]) / 2 < sh["end"]]
        sh["said"] = "".join(said).strip() if words and words[0] is not None else ""
        sh["sfx"] = [t for t in events if sh["start"] <= t < sh["end"]]


def summarize(info, shots, speech, events, bgm, db, step):
    D = info["duration"] or 1
    lens = [s["len"] for s in shots]
    third = D / 3
    part = lambda a, b: sum(1 for s in shots if a <= s["start"] < b)
    talk_t = sum(s["end"] - s["start"] for s in speech)
    chars = sum(hangul_len(s["text"]) for s in speech)
    rates = [hangul_len(s["text"]) / max(0.3, s["end"] - s["start"]) for s in speech if s["end"] - s["start"] > 0.8]
    first = speech[0] if speech else None
    with_text = [s for s in shots if s.get("text")]
    pos = {}
    for s in with_text:
        pos[s["text_pos"]] = pos.get(s["text_pos"], 0) + 1
    w, h = info["width"], info["height"]
    return {
        "형식": f"{'세로(쇼츠)' if h > w else '가로'} {w}×{h}, {info['fps']}fps",
        "길이초": round(D, 1),
        "컷수": len(shots),
        "평균컷초": round(float(np.mean(lens)), 2) if lens else 0,
        "가장짧은컷초": round(min(lens), 2) if lens else 0,
        "가장긴컷초": round(max(lens), 2) if lens else 0,
        "분당컷": round(len(shots) / D * 60, 1),
        "첫3초컷수": part(0, 3),
        "컷박자_처음중간끝": [round(part(0, third) / third * 60, 1), round(part(third, 2 * third) / third * 60, 1),
                       round(part(2 * third, D + 1) / third * 60, 1)],
        "첫말시작초": round(first["start"], 2) if first else None,
        "첫문장": first["text"] if first else "",
        "말비율%": round(talk_t / D * 100),
        "말빠르기_초당글자": round(chars / talk_t, 1) if talk_t else 0,
        "말빠르기_문장중간값": round(float(np.median(rates)), 1) if rates else 0,
        "문장수": len(speech),
        "문장평균초": round(talk_t / len(speech), 1) if speech else 0,
        "화면글자컷%": round(len(with_text) / max(1, len(shots)) * 100),
        "화면글자위치": pos,
        "화면글자크기중간값%": round(float(np.median([s["text_size"] for s in with_text])), 1) if with_text else 0,
        "효과음후보수": len(events),
        "말없는곳소리dB": round(bgm, 1) if bgm is not None else None,
        "전체소리dB중간값": round(float(np.median(db)), 1) if len(db) else None,
    }


def bgm_word(bgm, mid):
    if bgm is None:
        return "알 수 없음"
    if bgm < -50:
        return "거의 없음(말 사이가 조용함)"
    if mid is not None and bgm > mid - 8:
        return "크게 깔림(말 사이에도 소리가 큼)"
    return "작게 깔림"


def write_md(md_path, name, src, S, shots, speech, events, sheets, graph):
    L = [f"# 떡상 영상 분석 — {name}", "", f"- 원본: {src}",
         "- ⚠️ 구조만 참고. 화면·대사·인물·브랜드·문구는 가져오지 않고 새로 만든다", "",
         "## 한눈에 보기", "",
         f"| 항목 | 값 |", "|---|---|",
         f"| 형식 | {S['형식']} |",
         f"| 길이 | {tfmt(S['길이초'])} ({S['길이초']}초) |",
         f"| 컷 수 | {S['컷수']}개 — 평균 {S['평균컷초']}초 (가장 짧은 {S['가장짧은컷초']}초 · 가장 긴 {S['가장긴컷초']}초) |",
         f"| 컷 박자 | 1분에 {S['분당컷']}번 바뀜 · 처음/중간/끝 1분당 {S['컷박자_처음중간끝'][0]} / {S['컷박자_처음중간끝'][1]} / {S['컷박자_처음중간끝'][2]} |",
         f"| 첫 3초 | 컷 {S['첫3초컷수']}개, 말 시작 {S['첫말시작초']}초 |",
         f"| 첫 문장(훅) | {S['첫문장']} |",
         f"| 말 | 영상의 {S['말비율%']}% 동안 말함 · 1초에 {S['말빠르기_초당글자']}글자 · 문장 {S['문장수']}개(평균 {S['문장평균초']}초) |",
         f"| 화면 글자 | 컷의 {S['화면글자컷%']}%에 글자 · 위치 {S['화면글자위치']} · 크기 화면 높이의 {S['화면글자크기중간값%']}% |",
         f"| 배경음 | {bgm_word(S['말없는곳소리dB'], S['전체소리dB중간값'])} (말 없는 곳 {S['말없는곳소리dB']} dB) |",
         f"| 효과음 후보 | {S['효과음후보수']}곳 (갑자기 커지는 소리) |", "",
         "참고: 우리 F8 나레이션은 보통 1초에 약 8글자(1분 ≈ 490자). 말빠르기가 이보다 빠르면 대본을 짧게 끊는다.", "",
         "## 그림", "", f"- 흐름 그래프: `{os.path.basename(graph)}` (회색=소리 크기, 빨간 줄=컷, 파란 띠=말, 주황 점=효과음 후보)"]
    L += [f"- 컷 모음: `{os.path.basename(p)}`" for p in sheets]
    L += ["", "## 컷별 시간표", "", "| # | 시간 | 길이 | 그동안 말 | 화면 글자(위치) | 효과음 |", "|---|---|---|---|---|---|"]
    for s in shots:
        tx = f"{s.get('text', '')} ({s['text_pos']})" if s.get("text") else ""
        L.append(f"| {s['no']} | {tfmt(s['start'])}~{tfmt(s['end'])} | {s['len']}초 | {s.get('said', '')[:60]} | "
                 f"{tx.replace('|', '/')[:60]} | {'●' * len(s.get('sfx', []))} |")
    L += ["", "## 받아쓴 대사(문장별 시간)", ""]
    L += [f"- {tfmt(s['start'])}~{tfmt(s['end'])}  {s['text']}" for s in speech]
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")


# ───────── 6. 그림 ─────────
def contact_sheets(shots, base, per=20, cols=5):
    paths, f, fs = [], font(26), font(20)
    for k in range(0, len(shots), per):
        grp = [s for s in shots[k:k + per] if s.get("frame")]
        if not grp:
            continue
        im0 = Image.open(grp[0]["frame"])
        cw = 360
        ch = int(cw * im0.height / im0.width)
        rows = (len(grp) + cols - 1) // cols
        sheet = Image.new("RGB", (cols * cw, rows * (ch + 34)), "white")
        d = ImageDraw.Draw(sheet)
        for j, s in enumerate(grp):
            x, y = (j % cols) * cw, (j // cols) * (ch + 34)
            sheet.paste(Image.open(s["frame"]).convert("RGB").resize((cw, ch)), (x, y + 34))
            d.text((x + 6, y + 3), f"#{s['no']}  {tfmt(s['start'])}", fill="black", font=f)
            d.text((x + cw - 80, y + 7), f"{s['len']}초", fill=(200, 0, 0), font=fs)
        p = f"{base}_컷모음_{k // per + 1}.jpg"
        sheet.save(p, quality=85)
        paths.append(p)
    return paths


def flow_graph(path, D, db, step, shots, speech, events):
    W, H, pad = 1600, 360, 50
    im = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(im)
    X = lambda t: pad + (W - 2 * pad) * t / max(D, 0.1)
    Y = lambda v: H - pad - (H - 2 * pad) * (min(0, max(-60, v)) + 60) / 60
    for s in speech:
        d.rectangle([X(s["start"]), H - pad + 6, X(s["end"]), H - pad + 18], fill=(80, 130, 230))
    pts = [(X(i * step), Y(v)) for i, v in enumerate(db)]
    if len(pts) > 1:
        d.line(pts, fill=(120, 120, 120), width=2)
    for s in shots[1:]:
        d.line([X(s["start"]), pad - 10, X(s["start"]), H - pad], fill=(230, 30, 30), width=3)
    for t in events:
        d.ellipse([X(t) - 5, pad - 25, X(t) + 5, pad - 15], fill=(240, 140, 0))
    d.line([pad, H - pad, W - pad, H - pad], fill="black")
    f = font(18)
    step_lbl = 5 if D <= 90 else (30 if D <= 900 else 60)
    t = 0
    while t <= D:
        d.text((X(t) - 12, H - pad + 22), tfmt(t)[:-2], fill="black", font=f)
        t += step_lbl
    d.text((W - pad - 560, 8), "회색=소리 크기  빨간 줄=컷  파란 띠=말  주황 점=효과음 후보", fill="black", font=f)
    im.save(path)


# ───────── 7. 새 기획 (claude -p) ─────────
def make_plan(md_path, topic, out_path):
    with open(md_path, encoding="utf-8") as f:
        analysis = f.read()[:30000]
    prompt = f"""아래는 조회수가 높은 영상 하나를 뜯어본 결과(컷 박자·말 빠르기·첫 3초·화면 글자·소리)다.
이 영상의 **구조만** 빌려 새 영상 기획안을 써라. 새 주제: {topic}

규칙:
- 원본의 대사·문구·인물·브랜드·화면은 쓰지 않는다. 구조(훅 위치, 컷 길이 박자, 문장 길이, 반전·정리 위치, 글자 넣는 방식)만 따른다.
- 우리 제작 방식: 나레이션 성우 F8(1초에 약 8글자, 1분 ≈ 490자), 그림은 이 저장소 도구(klein 그림 또는 Blockbench 블록 애니), 자막 한 줄씩, 24fps.
- 원본 말 빠르기가 1초 8글자보다 빠르면 대본 글자 수를 줄여 같은 길이에 맞춘다.
- 겹쳐 읽히는 말(앞 낱말 끝 글자와 다음 낱말 첫 글자가 같은 소리), '유적', '~음' 메모 말투는 피한다.

출력(한국어 마크다운):
1. 원본 구조 요약 (구간별: 몇 초~몇 초에 무엇을 하는지, 한 줄씩)
2. 새 영상 제목 후보 3개
3. 장면표: | # | 시간 | 나레이션 대본 | 화면(그림 주문, 장소 포함) | 화면 글자 | 효과음 |
   — 원본 컷 박자와 비슷한 길이로
4. 전체 나레이션 대본 (그대로 녹음할 글)

분석 결과:
{analysis}
"""
    r = run(["claude", "-p", prompt], timeout=900)
    if r.returncode != 0 or not r.stdout.strip():
        print("기획안을 만들지 못함:", r.stderr.strip()[-300:])
        return False
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(f"# 새 기획 — {topic}\n\n(떡상분석: {os.path.basename(md_path)} 의 구조를 빌림)\n\n" + r.stdout.strip() + "\n")
    return True


# ───────── 실행 ─────────
def main():
    ap = argparse.ArgumentParser(description="잘 된 영상의 구조(컷·말·자막·소리) 뜯어보기")
    ap.add_argument("src")
    ap.add_argument("--폴더", dest="out")
    ap.add_argument("--컷민감도", dest="th", type=float, default=0.3, help="작을수록 컷을 더 많이 찾음 (0.2~0.5)")
    ap.add_argument("--언어", dest="lang", default="ko")
    ap.add_argument("--글자읽기", dest="ocr", default="on")
    ap.add_argument("--받아쓰기", dest="stt", default="on")
    ap.add_argument("--기획", dest="topic")
    a = ap.parse_args()

    name = os.path.splitext(os.path.basename(a.src))[0] if os.path.exists(a.src) else \
        (re.search(r"(?:v=|youtu\.be/|shorts/)([\w-]{6,})", a.src) or [None, "유튜브영상"])[1]
    out = a.out or os.path.join(HERE, "output", "떡상분석", name)
    os.makedirs(out, exist_ok=True)
    base = os.path.join(out, name)

    video = get_video(a.src, out)
    info = probe(video)
    print(f"영상: {info['width']}×{info['height']} {info['duration']:.1f}초", flush=True)

    print("① 컷 찾는 중…", flush=True)
    shots = find_cuts(video, info["duration"], a.th)
    grab_frames(video, shots, os.path.join(out, "_컷"))
    print(f"   컷 {len(shots)}개", flush=True)

    if a.ocr != "off":
        print("② 화면 글자 읽는 중…", flush=True)
        read_text(shots)

    speech, db, step, events, bgm = [], np.array([]), 0.25, [], None
    if info["has_audio"]:
        audio = load_audio(video)
        db, step = loudness(audio)
        if a.stt != "off":
            print("③ 대사 받아쓰는 중…", flush=True)
            speech = transcribe(audio, a.lang)
        events, bgm = sound_events(db, step, speech)
    attach(shots, speech, events)

    S = summarize(info, shots, speech, events, bgm, db, step)
    sheets = contact_sheets(shots, base)
    graph = base + "_흐름.png"
    flow_graph(graph, info["duration"], db, step, shots, speech, events)
    md = base + "_분석.md"
    write_md(md, name, a.src, S, shots, speech, events, sheets, graph)
    with open(base + "_분석.json", "w", encoding="utf-8") as f:
        json.dump({"요약": S, "컷": [{k: v for k, v in s.items() if k != "frame"} for s in shots],
                   "대사": [{k: v for k, v in s.items() if k != "words"} for s in speech], "효과음후보": events},
                  f, ensure_ascii=False, indent=1)
    print(f"\n분석 완료 → {md}", flush=True)
    for k, v in S.items():
        print(f"  {k}: {v}")

    if a.topic:
        print(f"\n④ 새 기획안 쓰는 중… ({a.topic})", flush=True)
        if make_plan(md, a.topic, base + "_새기획.md"):
            print(f"  → {base}_새기획.md")


if __name__ == "__main__":
    main()
