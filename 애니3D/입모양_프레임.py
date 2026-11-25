"""음절 발음 시각(실사3D/발음시각.py 결과) → 장면에서 쓸 입 모양 값(1/24초마다 open·wide·round)
   사용: python 애니3D/입모양_프레임.py <시각.json> <결과.json> [--소리 <나레이션.mp3>] [--표 <입모양표.json>]
                                        [--앞당김 0.2] [--fps 24] [--시작 0] [--세기 1]
   정교하게 (사용자 2026-11-22 "입모양을 좀더 정교하게"):
   - 벌림 크기는 실제 한국어 화자에게서 배운 표(실사3D/입모양표.json: 아 > 에 > 이 > 어 > 으 > 오 > 우)로 — 표가 없으면 기본값
   - 옆으로(wide)·오므림(round)은 모음 모양으로: ㅣㅔㅐ 옆으로, ㅗㅜ 오므림, 이중모음(ㅘㅝㅟㅢㅑㅕㅛㅠ)은 앞 모양 → 뒤 모양으로 음절 안에서 바뀜
   - 소리 크기(--소리): 음절마다 크게 말하면 더 벌리고 작게 말하면 덜 (0.7~1.25배)
   - 이어 말하기: 음절 끝 25% 는 다음 음절 모양으로 미리 옮겨 감 (뚝뚝 끊기지 않게)
   - 첫소리 ㅁㅂㅃㅍ = 입술을 꼭 다묾(조금 눌러 오므림 0), 받침 ㅁㅂㅍ = 끝에서 다묾, 받침 ㄴㄷㄹ·ㅇ 은 조금 덜 벌림. 0.15초 넘는 쉼은 닫음
   - 받아쓰기 모델의 글자 시각은 실제 입보다 약 0.2초 늦음 → --앞당김 (실사3D 사용자 확인 2026-11-21)
   - --시작: 영상에서 소리가 시작하는 초 (그만큼 뒤로 밀어 둠), --세기: 전체 벌림 배율
   결과: {"fps":24, "frames":[[open, wide, round, aa, ih, ou, ee, oh], ...]}  (앞 셋 = GLB 모양 키, 뒤 다섯 = VRM 입 모양)  → 장면_입검사.html ?lip=<결과.json>"""
import json, os, subprocess, sys
import numpy as np

a = sys.argv[1:]
opt = {"--앞당김": 0.2, "--fps": 24.0, "--시작": 0.0, "--세기": 1.0}
sound = table = None
if "--소리" in a: i = a.index("--소리"); sound = a[i + 1]; del a[i:i + 2]
if "--표" in a: i = a.index("--표"); table = a[i + 1]; del a[i:i + 2]
for k in list(opt):
    if k in a: i = a.index(k); opt[k] = float(a[i + 1]); del a[i:i + 2]
LEAD, FPS, START, GAIN = opt["--앞당김"], opt["--fps"], opt["--시작"], opt["--세기"]
syl = json.load(open(a[0], encoding="utf-8"))

# 모음 무리별 벌림 (표의 open 비율 → 0~1: 아 1.0 … 우 0.1)
OPEN = {"아": 1.0, "에": 0.8, "이": 0.45, "어": 0.55, "으": 0.25, "오": 0.3, "우": 0.12}
if table and os.path.exists(table):
    cl = json.load(open(table, encoding="utf-8"))["classes"]
    lo, hi = cl["우"]["open"], cl["아"]["open"]
    OPEN = {k: float(np.clip(0.12 + 0.88 * (cl[k]["open"] - lo) / (hi - lo), 0.1, 1.0)) for k in OPEN if k in cl}
    print("배운 표의 벌림:", {k: round(v, 2) for k, v in OPEN.items()})
WIDE = {"아": 0.15, "에": 0.5, "이": 0.8, "어": 0.0, "으": 0.45, "오": 0.0, "우": 0.0}
ROUND = {"아": 0.0, "에": 0.0, "이": 0.0, "어": 0.25, "으": 0.0, "오": 0.75, "우": 1.0}
# 중성 → (앞 모양, 뒤 모양)  (단모음은 같은 것 둘)
J = {"ㅏ": "아아", "ㅐ": "에에", "ㅑ": "이아", "ㅒ": "이에", "ㅓ": "어어", "ㅔ": "에에", "ㅕ": "이어", "ㅖ": "이에", "ㅗ": "오오", "ㅘ": "오아",
     "ㅙ": "오에", "ㅚ": "오에", "ㅛ": "이오", "ㅜ": "우우", "ㅝ": "우어", "ㅞ": "우에", "ㅟ": "우이", "ㅠ": "이우", "ㅡ": "으으", "ㅢ": "으이", "ㅣ": "이이"}
JUNG = "ㅏㅐㅑㅒㅓㅔㅕㅖㅗㅘㅙㅚㅛㅜㅝㅞㅟㅠㅡㅢㅣ"
CLOSE_CHO = {6, 7, 8, 17}                  # ㅁ ㅂ ㅃ ㅍ
CLOSE_JONG = {16, 17, 18, 26, 10, 11, 14}  # ㅁ ㅂ ㅄ ㅍ ㄻ ㄼ ㄿ
SOFT_JONG = {4, 7, 8, 21}                  # ㄴ ㄷ ㄹ ㅇ : 끝에서 조금 덜 벌림


# VRM(VRoid) 캐릭터용 다섯 입 모양 aa(아)·ih(이)·ou(우)·ee(에)·oh(오) 섞는 양 — VRoid 입 모양은 벌림이 이미 들어 있음
VIS = {"아": [1, 0, 0, 0, 0], "이": [0, 1, 0, 0, 0], "우": [0, 0, 1, 0, 0], "에": [0, 0, 0, 1, 0], "오": [0, 0, 0, 0, 1],
       "어": [0.55, 0, 0, 0, 0.35], "으": [0, 0.45, 0.15, 0, 0]}


def shape(v, k=1.0): return np.array([OPEN[v] * k, WIDE[v], ROUND[v]] + [w_ * min(k, 1.15) * 0.9 for w_ in VIS[v]])


# 소리 크기: 음절 구간의 소리 세기(RMS)를 중간값 대비로
loud = None
if sound:
    SR = 16000
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", sound, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True).stdout
    wav = np.frombuffer(raw, np.float32)
    def rms(t0, t1):
        seg = wav[int(max(0, t0) * SR):int(max(t0 + 0.02, t1) * SR)]
        return float(np.sqrt((seg ** 2).mean())) if len(seg) else 0.0
    loud = np.array([rms(t0, t1) for _, t0, t1 in syl]); med = np.median(loud[loud > 0]) if (loud > 0).any() else 1
    loud = np.clip(0.7 + 0.45 * (loud / med - 0.6), 0.7, 1.25)

items = []        # (t0, t1, 첫소리 다묾, 받침 종류, 앞 모양, 뒤 모양)
for k, (ch, t0, t1) in enumerate(syl):
    if not ("가" <= ch <= "힣"): continue
    c = ord(ch) - 0xAC00; cho, jung, jong = c // 588, (c % 588) // 28, c % 28
    v1, v2 = J[JUNG[jung]]
    g = GAIN * (loud[k] if loud is not None else 1.0)
    if jong in SOFT_JONG: g2 = g * 0.8
    else: g2 = g
    items.append((t0 + START - LEAD, t1 + START - LEAD, cho in CLOSE_CHO, jong, shape(v1, g), shape(v2, g2)))

Z = np.zeros(8)
keys = [(0.0, Z)]
for n_, (t0, t1, close0, jong, s1, s2) in enumerate(items):
    d = max(t1 - t0, 0.06)
    prev_end = items[n_ - 1][1] if n_ else None
    if prev_end is not None and t0 - prev_end > 0.15:                      # 쉼: 닫음
        keys += [(prev_end + 0.09, Z), (t0 - 0.03, Z)]
    if close0: keys += [(t0, Z), (t0 + 0.03, Z), (t0 + 0.4 * d, s1)]       # ㅁㅂㅍ: 입술 꼭 다물었다가 열림
    else: keys += [(t0 + 0.3 * min(d, 0.25), s1)]
    if not np.allclose(s1, s2): keys += [(t0 + 0.7 * d, s2)]                # 이중모음: 뒤 모양으로
    if jong in CLOSE_JONG: keys += [(t1 - 0.28 * min(d, 0.2), s2 * 0.9), (t1, Z)]
    else:
        nxt = items[n_ + 1] if n_ + 1 < len(items) else None
        end = s2 * 0.85
        if nxt and nxt[0] - t1 < 0.1 and not nxt[2]: end = 0.75 * s2 + 0.25 * nxt[4]     # 다음 음절 모양으로 미리
        keys += [(t1 - 0.2 * min(d, 0.2), end)]
last = items[-1][1]
keys += [(last + 0.12, Z)]
keys.sort(key=lambda k: k[0])
ts = np.array([k[0] for k in keys]); vs = np.array([k[1] for k in keys], float)
n = int(np.ceil((ts[-1] + 0.5) * FPS)); tt = np.arange(n) / FPS
fr = np.stack([np.interp(tt, ts, vs[:, j]) for j in range(vs.shape[1])], 1)
ker = np.array([1, 2, 1]) / 4.0
fr = np.stack([np.convolve(np.pad(fr[:, j], 1, mode="edge"), ker, "valid") for j in range(fr.shape[1])], 1)
fr = np.clip(fr, 0, 1.2)
json.dump({"fps": FPS, "frames": np.round(fr, 3).tolist()}, open(a[1], "w"))
print(f"입 모양 {n}장 ({n / FPS:.1f}초), 음절 {len(items)}개, 앞당김 {LEAD}초{', 소리 크기 반영' if loud is not None else ''} → {a[1]}")
