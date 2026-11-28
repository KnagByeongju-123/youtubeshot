"""3D 립싱크가 LatentSync(선생님)의 입 움직임을 배움 (사용자 결정 2026-11-28: 'LatentSync 가 나음 → 3D 가 계속 학습')
같은 인물·같은 카메라·같은 소리로 만든 두 영상에서 1/25초마다 입 벌림·너비를 MediaPipe 얼굴 점으로 재서(실사3D/입모양_학습.py 재기와 같은 방법)
  ① 시간 어긋남(3D 가 늦거나 빠른 정도) ② 전체 크기 ③ 모음별(아 어 오 우 으 이 에)·입 닫음 크기 를 비교하고,
3D 가 쓰는 입 모양 표(실사3D/입모양표_LS.json)의 모음별 값(open_3d·wide_3d)·앞당김·세기를 선생님 쪽으로 고침. 문장이 늘수록 쌓여서 정확해짐.

학습 기록(다른 세션과 나눔, 깃에 올림): 실사3D/립싱크학습/<번호>/ = 문장.txt · 시각.json · 선생.json(LatentSync 입 곡선 숫자, 1/25초)
  · 선생_입술점.json(입술 둘레 40점 위치, 장마다 — 나중에 입술 모양까지 배울 때)
  → 선생님 영상(LatentSync, 1초에 약 25분)은 한 번만 만들고, 다른 세션은 선생.json 만 읽어 3D 를 다시 맞춤 (영상·소리 파일은 깃에 안 올림)
사용 (LatentSync 환경의 파이썬 — MediaPipe 가 들어 있음):
  models/latentsync/.venv/bin/python 실사3D/립싱크_학습.py <선생님.mp4 또는 -> <3D.mp4> <음절시각.json 또는 -> --기록 실사3D/립싱크학습/<번호>
      [--표 실사3D/입모양표_LS.json] [--보고 <폴더>] [--배우기 0.7] [--소리 <소리.wav> (없으면 기록 폴더의 소리.wav — 시간 어긋남을 소리 기준으로 잼)]
    선생님 자리에 - 를 주면 기록의 선생.json, 음절시각 자리에 - 를 주면 기록의 시각.json 을 씀
    음절시각.json = 실사3D/발음시각.py 결과(소리 시작 = 영상 0초), 3D 는 립싱크.py --시작 0 으로 찍은 것
    --배우기: 한 번에 고치는 정도(0~1, 1 이면 차이를 한 번에 다 고침) / --재기만: 표를 고치지 않고 비교만
결과: 표를 고쳐 저장 + <보고>/비교.png(두 곡선) + 비교.txt
3D 에 쓰기: 립싱크.py ... --표 실사3D/입모양표_LS.json (표에 적힌 앞당김·세기도 씀)"""
import json, os, subprocess, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
FPS = 25
a = sys.argv[1:]
def opt(k, d): return a[a.index(k) + 1] if k in a else d
if a and a[0] == "--모으기":     # 영상 없이 모든 기록의 제안.json 으로 표만 다시 만듦
    a = ["-", "-", "-"] + a; MODE_COLLECT = True
else:
    MODE_COLLECT = False
TEACH, STU, SYL = a[0], a[1], a[2]
REC = opt("--기록", None)
if REC: os.makedirs(REC, exist_ok=True)
if SYL == "-" and REC: SYL = os.path.join(REC, "시각.json")
TABLE = opt("--표", os.path.join(HERE, "입모양표_LS.json")); REP = opt("--보고", os.path.dirname(os.path.abspath(STU)))
RATE = float(opt("--배우기", "0.7")); ONLY = "--재기만" in a
os.makedirs(REP, exist_ok=True)

# 학습 시작값 = 3D 가 지금까지 쓰던 값 (입모양_프레임.py 가 실사3D/입모양표.json 에서 만든 벌림)
OPEN0 = {"아": 1.0, "에": 0.87, "이": 0.66, "어": 0.5, "으": 0.46, "오": 0.17, "우": 0.12}
WIDE0 = {"아": 0.15, "에": 0.5, "이": 0.8, "어": 0.0, "으": 0.45, "오": 0.0, "우": 0.0}
LEAD0, GAIN0 = 0.2, 1.0


def rebuild(table_path):
    """실사3D/립싱크학습/*/제안.json 을 모두 모아 표를 새로 만듦"""
    import glob
    S_ = [(os.path.basename(os.path.dirname(f)), json.load(open(f, encoding="utf-8"))) for f in sorted(glob.glob(os.path.join(HERE, "립싱크학습", "*", "제안.json")))]
    def wmean(vals, geo=False):
        vals = [(v, w) for v, w in vals if v is not None and w > 0]
        if not vals: return None
        v, w = np.array([x[0] for x in vals], float), np.array([x[1] for x in vals], float)
        return float(np.exp((np.log(np.maximum(v, 1e-3)) * w).sum() / w.sum())) if geo else float((v * w).sum() / w.sum())
    lead = wmean([(x["lead"], 1) for _, x in S_]); gain = wmean([(x["gain"], 1) for _, x in S_], geo=True)
    tab = {"source": "LatentSync 1.6 (여자아나운서1 사진) 선생님 → 3D 립싱크. 3D 는 학습 전 기본값으로 찍고 번호마다 제안.json, 표 = 제안의 평균 (실사3D/립싱크_학습.py --모으기)",
           "lead": round(float(np.clip(lead if lead is not None else LEAD0, -0.3, 0.45)), 3),   # 음수 = 입을 소리보다 늦게(받아쓰기 시각이 이미 이른 경우)
           "gain": round(float(np.clip(gain if gain is not None else GAIN0, 0.4, 2.5)), 3), "open_3d": {}, "wide_3d": {},
           "records": [k for k, _ in S_]}
    g_ = tab["gain"]
    for c in OPEN0:
        # 한 가지 묶음 번호(세기 제안 없음)의 벌림 제안은 전체 크기까지 담은 값 → 표의 세기로 나눠 맞춤 (세기가 두 번 곱해지지 않게, 세션 A 2026-11-28)
        o = wmean([((x["open"].get(c) / g_ if x.get("gain") is None else x["open"].get(c)) if x["open"].get(c) is not None else None,
                    x["n"].get(c, 0)) for _, x in S_], geo=True)
        w_ = wmean([(x["wide"].get(c), x["n"].get(c, 0)) for _, x in S_])
        tab["open_3d"][c] = round(float(np.clip(o if o is not None else OPEN0[c], 0.05, 1.3)), 3)
        tab["wide_3d"][c] = round(float(np.clip(w_ if w_ is not None else WIDE0[c], 0.0, 1.0)), 3)
    json.dump(tab, open(table_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return tab



if MODE_COLLECT:
    t_ = rebuild(TABLE); print(f"표 새로 모음({len(t_['records'])}개 번호):", json.dumps(t_, ensure_ascii=False)); sys.exit(0)
VOWEL = {0: "아", 2: "아", 9: "아", 4: "어", 6: "어", 14: "어", 8: "오", 12: "오", 10: "오", 11: "오",
         13: "우", 17: "우", 15: "우", 16: "우", 18: "으", 19: "으", 20: "이", 1: "에", 3: "에", 5: "에", 7: "에"}
CLOSE_CHO = (6, 7, 8, 17)


LIP_PTS = [61, 146, 91, 181, 84, 17, 314, 405, 321, 375, 291, 185, 40, 39, 37, 0, 267, 269, 270, 409,
           78, 95, 88, 178, 87, 14, 317, 402, 318, 324, 308, 191, 80, 81, 82, 13, 312, 311, 310, 415]   # MediaPipe 입술 바깥 20 + 안쪽 20
PTS = []


def measure(video):
    import mediapipe as mp
    from mediapipe.tasks.python import vision, BaseOptions
    task = os.path.join(ROOT, "models", "ditto", "checkpoints", "ditto_pytorch", "aux_models", "face_landmarker.task")
    det = vision.FaceLandmarker.create_from_options(vision.FaceLandmarkerOptions(base_options=BaseOptions(model_asset_path=task), num_faces=1))
    w, h = (int(v) for v in subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
                                            "-of", "csv=p=0", video], capture_output=True, text=True).stdout.strip().split(","))
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", video, "-vf", f"fps={FPS}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    rows = []; PTS.clear()
    while True:
        buf = p.stdout.read(w * h * 3)
        if len(buf) < w * h * 3: break
        r = det.detect(mp.Image(image_format=mp.ImageFormat.SRGB, data=np.frombuffer(buf, np.uint8).reshape(h, w, 3).copy()))
        if not r.face_landmarks: rows.append([np.nan, np.nan]); PTS.append(None); continue
        q = np.array([[l.x * w, l.y * h] for l in r.face_landmarks[0]])
        eye = np.linalg.norm(q[33] - q[263]) + 1e-6
        # 입술 점(나중에 입술 모양까지 배울 때 씀): 두 눈꼬리 가운데를 0, 눈꼬리 사이를 1, 눈 선을 가로로 맞춘 좌표
        c = (q[33] + q[263]) / 2; ex = (q[263] - q[33]) / eye; R = np.array([ex, [-ex[1], ex[0]]])
        PTS.append(np.round((q[LIP_PTS] - c) @ R.T / eye, 4).tolist())
        rows.append([np.linalg.norm(q[13] - q[14]) / eye, np.linalg.norm(q[61] - q[291]) / eye])
    r = np.array(rows, np.float64)
    for k in range(2):                                     # 못 찾은 장은 앞뒤로 메움
        bad = np.isnan(r[:, k])
        if bad.any() and (~bad).any(): r[bad, k] = np.interp(np.flatnonzero(bad), np.flatnonzero(~bad), r[~bad, k])
    return r


if TEACH == "-":
    T = np.array(json.load(open(os.path.join(REC, "선생.json"), encoding="utf-8"))["curve"], np.float64)
else:
    T = measure(TEACH)
    if REC:
        json.dump({"fps": FPS, "teacher": "LatentSync 1.6, guidance 1.0, 여자아나운서1 정면 사진(1024x576, 카메라 0,-0.75,1.47,0,0,1.45,50)",
                   "cols": ["open/eye", "width/eye"], "curve": np.round(T, 4).tolist()}, open(os.path.join(REC, "선생.json"), "w", encoding="utf-8"))
        json.dump({"fps": FPS, "mediapipe_index": LIP_PTS, "coord": "눈꼬리 가운데=0, 눈꼬리 사이=1, 눈 선 가로", "frames": PTS},
                  open(os.path.join(REC, "선생_입술점.json"), "w", encoding="utf-8"))
        if os.path.abspath(SYL) != os.path.abspath(os.path.join(REC, "시각.json")):
            import shutil; shutil.copy(SYL, os.path.join(REC, "시각.json"))
S = np.array(json.load(open(os.path.join(REC, "3D.json"), encoding="utf-8"))["curve"], np.float64) if STU == "-" else measure(STU)   # - = 기록의 3D.json
n = min(len(T), len(S)); T, S = T[:n], S[:n]
syl = sorted(json.load(open(SYL, encoding="utf-8")), key=lambda x: x[1])
syl = [s for s in syl if 0 <= ord(s[0]) - 0xAC00 < 11172]
f_on = max(0, int(syl[0][1] * FPS) - 3); f_off = min(n, int((syl[-1][2] if len(syl[-1]) > 2 else syl[-1][1] + 0.3) * FPS) + 6)
# 다문 입 = 영상 전체에서 가장 작게 다문 값(아래 5%) — 앞 몇 장은 이미 말이 시작돼 입이 벌어져 있을 수 있음(01번: 앞 0.021, 실제 다문 입 0.003, 2026-11-28)
rest_T, rest_S = np.percentile(T[:, 0], 5), np.percentile(S[:, 0], 5)
oT, oS = T[:, 0] - rest_T, S[:, 0] - rest_S

# ① 시간 어긋남: 3D 곡선을 몇 장 밀면 선생님과 가장 닮는지 (+ = 3D 가 늦음 → 더 앞당겨야 함)
seg = slice(f_on, f_off)
def corr(k):
    s = np.roll(oS, -k)[seg]; t = oT[seg]
    return float(np.corrcoef(s, t)[0, 1]) if s.std() > 1e-6 and t.std() > 1e-6 else -1
lags = {k: corr(k) for k in range(-8, 9)}
lag = max(lags, key=lags.get)
# 소리를 기준으로 각각 시간을 잼(2026-11-28, 01번): 선생님·3D 를 직접 맞대면 모양이 달라 닮음이 낮게 나옴(0.11) →
#   소리 크기(1/25초)와 가장 닮게 밀리는 장 수를 선생님·3D 따로 구해 그 차이를 시간 어긋남으로 씀 (선생님은 소리보다 약 2장 먼저 = 사람과 같음)
AUD = opt("--소리", os.path.join(REC, "소리.wav") if REC else None)
lag_src = "선생님과 직접"
if AUD and os.path.exists(AUD):
    import wave
    w = wave.open(AUD); sr = w.getframerate(); y = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float64)
    if w.getnchannels() > 1: y = y.reshape(-1, w.getnchannels()).mean(1)
    hop = sr // FPS; env = np.array([np.sqrt(np.mean(y[i * hop:(i + 1) * hop] ** 2)) for i in range(len(y) // hop)])
    m = min(n, len(env)); env = np.pad(env, (0, max(0, n - len(env))))[:n]
    def best(x):
        c = {k: np.corrcoef(np.roll(x, -k)[:m], env[:m])[0, 1] for k in range(-10, 11)}
        k = max(c, key=c.get); return k, c[k]
    kT, cT = best(oT); kS, cS = best(oS)
    if min(cT, cS) >= 0.25:
        lag = kS - kT; lags[lag] = max(lags.get(lag, -1), min(cT, cS)); lag_src = f"소리 기준(선생님 {kT:+d}장 닮음 {cT:.2f}, 3D {kS:+d}장 닮음 {cS:.2f})"
oS2 = np.roll(oS, -lag)
# ② 전체 크기 (말하는 동안 벌림 평균)
amp = float(np.mean(np.clip(oT[seg], 0, None)) / max(np.mean(np.clip(oS2[seg], 0, None)), 1e-6))
# ③ 모음별: 음절 가운데 장들의 평균 벌림·너비
cls = {}
for k, s in enumerate(syl):
    v = ord(s[0]) - 0xAC00; cho, jung = v // 588, (v % 588) // 28
    s0 = s[1]; e0 = min(syl[k + 1][1] if k + 1 < len(syl) else s0 + 0.25, s0 + 0.35)
    f0, f1 = int(s0 * FPS) - 5, int(round(e0 * FPS)) - 5              # 받아쓰기 글자 시각은 실제 입보다 약 0.2초 늦음(입모양표 lag -5)
    fr = [f for f in range(f0, max(f1, f0 + 1)) if 0 <= f < n]
    if not fr: continue
    c = "닫음" if cho in CLOSE_CHO else VOWEL.get(jung)
    ks = fr[:max(1, len(fr) // 4)] if c == "닫음" else fr[len(fr) // 3:max(len(fr) // 3 + 1, len(fr) * 4 // 5)]
    d = cls.setdefault(c, {"T": [], "S": [], "Tw": [], "Sw": []})
    d["T"] += [oT[f] for f in ks]; d["S"] += [oS2[f] for f in ks]; d["Tw"] += [T[f, 1] for f in ks]; d["Sw"] += [S[(f + lag) % n, 1] for f in ks]

lines = [f"선생님 {TEACH}", f"3D {STU}", f"장 수 {n} (1/25초), 말하는 구간 {f_on/FPS:.2f}~{f_off/FPS:.2f}초",
         f"다문 입 벌림: 선생님 {rest_T:.3f}, 3D {rest_S:.3f}",
         f"① 시간: 3D 가 {lag:+d}장({lag/FPS:+.2f}초) {'늦음' if lag > 0 else '빠름' if lag < 0 else '맞음'} (닮음 {lags[lag]:.2f}, 밀기 전 {lags[0]:.2f}, {lag_src})",
         f"② 전체 벌림: 선생님이 3D 의 {amp:.2f} 배", "③ 모음별 (벌림 선생님/3D, 너비 선생님/3D, 장 수):"]
for c, d in sorted(cls.items(), key=lambda x: -np.mean(x[1]["T"])):
    lines.append(f"   {c}: 벌림 {np.mean(d['T']):.3f}/{np.mean(d['S']):.3f}  너비 {np.mean(d['Tw']):.3f}/{np.mean(d['Sw']):.3f}  ({len(d['T'])})")

# 표 만들기 (2026-11-28 바꿈 — 세션 I 지적: 차례로 곱해 고치면 3D 를 찍은 뒤 다른 세션이 표를 바꿨을 때 두 번 셈):
#  3D 는 늘 '학습 전 기본값'(립싱크.py 에 --표 없이)으로 찍고, 이 번호가 본 '맞는 값 제안'을 기록 폴더의 제안.json 에 남김 →
#  표 = 모든 번호의 제안을 장 수로 무게를 둔 평균 (순서·겹침과 상관없이 늘 같은 결과)
# 한 가지 묶음(13~20번): 모음끼리만 비교해 한 모음이 80% 넘거나(ㅁㅂ 이 섞여도 됨 — 19번 '메뉴·제비'), '닫음'이 40% 넘으면(20번) 세기는 안 고침
vn = {c: len(d["T"]) for c, d in cls.items() if c in OPEN0}
# 낱말 묶음(쉼표로 이은 짧은 낱말 4개 이상, 13~20번)은 50% 넘으면 그 모음 묶음 — 15번 '오리·모자' 처럼 다른 모음이 섞여 54% 인데 세기를 0.25 로 줄이자고 했음 (세션 E)
_txt = open(os.path.join(REC, "문장.txt"), encoding="utf-8").read().strip().rstrip(".") if REC and os.path.exists(os.path.join(REC, "문장.txt")) else ""
_words = [w.strip(" .") for w in _txt.replace(".", ",").split(",") if w.strip(" .")]
word_list = len(_words) >= 4 and all(len(w) <= 3 and " " not in w for w in _words)
one = max(vn, key=vn.get) if vn and max(vn.values()) >= (0.5 if word_list else 0.8) * sum(vn.values()) else None
close_group = "닫음" in cls and len(cls["닫음"]["T"]) >= 0.4 * sum(len(d["T"]) for d in cls.values())
timing_ok = lags[lag] >= 0.5 or lag_src.startswith("소리 기준")
sug = {"lead": round(LEAD0 + lag / FPS, 3) if timing_ok else None,
       "gain": round(GAIN0 * amp, 3) if not (one or close_group) else None, "open": {}, "wide": {}, "n": {}}
for c, d in cls.items():
    if c not in OPEN0 or len(d["T"]) < 2: continue
    r = (np.mean(d["T"]) + 0.02) / (np.mean(d["S"]) + 0.02)      # 모음별 차이
    if c == one: r = amp
    elif sug["gain"] is not None: r /= amp    # 세기를 고칠 때만 전체 크기를 뺌 (세기를 안 고치는 묶음은 --모으기 가 표 세기로 나눔, 세션 E)
    wr = np.mean(d["Tw"]) / max(np.mean(d["Sw"]), 1e-6)
    sug["open"][c] = round(float(OPEN0[c] * r), 3); sug["wide"][c] = round(float(np.clip(WIDE0[c] + (wr - 1) * 4, 0, 1)), 3); sug["n"][c] = len(d["T"])
if "닫음" in cls:
    sug["close"] = {"teacher": round(float(np.mean(cls["닫음"]["T"])), 4), "3d": round(float(np.mean(cls["닫음"]["S"])), 4), "n": len(cls["닫음"]["T"])}
sug["corr"] = round(float(lags[lag]), 3); sug["lag_frames"] = lag; sug["amp"] = round(amp, 3)
lines.append(f"→ 이 번호의 제안: 앞당김 {sug['lead']}, 세기 {sug['gain']}, 벌림 {sug['open']}, 옆으로 {sug['wide']}")
if REC and not ONLY:
    json.dump(sug, open(os.path.join(REC, "제안.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    # 3D(학습 전 기본값으로 찍은 것) 입 곡선도 남김 → 나중에 계산 방법을 바꿔도 영상 없이 다시 계산 가능
    json.dump({"fps": FPS, "3d": "학습 전 기본값(립싱크.py --표 없이), 여자아나운서1, 카메라 0,-0.75,1.47,0,0,1.45,50, 1024x576",
               "cols": ["open/eye", "width/eye"], "curve": np.round(S, 4).tolist()}, open(os.path.join(REC, "3D.json"), "w", encoding="utf-8"))


if not ONLY:
    tab = rebuild(TABLE)
    lines.append(f"→ 표 새로 모음({len(tab['records'])}개 번호) {TABLE}: 앞당김 {tab['lead']}초, 세기 {tab['gain']}, 벌림 {tab['open_3d']}, 옆으로 {tab['wide_3d']}")
open(os.path.join(REP, "비교.txt"), "w", encoding="utf-8").write("\n".join(lines) + "\n")
print("\n".join(lines))

try:
    import cv2
    W, H = 1000, 360; img = np.full((H, W, 3), 255, np.uint8); x = lambda i: int(40 + (W - 60) * i / max(n - 1, 1))
    top = max(oT.max(), oS.max(), 1e-3); y = lambda v: int(H - 40 - (H - 80) * max(v, -0.1 * top) / top)
    for arr, col in ((oT, (40, 40, 220)), (oS, (200, 120, 30))):
        for i in range(n - 1): cv2.line(img, (x(i), y(arr[i])), (x(i + 1), y(arr[i + 1])), col, 2)
    for s in syl: cv2.line(img, (x(s[1] * FPS), H - 30), (x(s[1] * FPS), H - 20), (0, 0, 0), 1)
    cv2.putText(img, "red=LatentSync  blue=3D  (mouth open)", (40, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)
    cv2.imwrite(os.path.join(REP, "비교.png"), img)
except Exception as e:
    print("그래프 못 그림:", e)
