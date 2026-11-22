"""음절 발음 시각(실사3D/발음시각.py 결과) → 장면에서 쓸 입 모양 값(1/24초마다 open·wide·round)
   사용: python 애니3D/입모양_프레임.py <시각.json> <결과.json> [--앞당김 0.2] [--fps 24] [--시작 0]
   - 모음마다 입 모양(벌림 open · 옆으로 wide · 오므림 round, 0~1):
       ㅏㅑㅘ 크게 벌림 · ㅐㅔㅒㅖㅙㅞ 벌리며 옆으로 · ㅓㅕㅝ 벌리고 조금 오므림 · ㅗㅛㅚ 오므림 · ㅜㅠㅟ 많이 오므림 · ㅡㅢ 조금 옆으로 · ㅣ 옆으로
     (실사3D/입모양표.json 에서 배운 순서: 아 > 에 > 이 > 어 > 으 > 오 > 우 — 오·우는 작게 벌림)
   - 첫소리 ㅁㅂㅃㅍ 는 음절 앞쪽에서 입을 다물고, 받침 ㅁㅂㅍ(ㄻㄼㄿㅄ) 은 음절 끝에서 다묾. 0.15초 넘는 쉼은 입을 닫음
   - 받아쓰기 모델의 글자 시각은 실제 입보다 약 0.2초 늦음 → --앞당김 (실사3D 사용자 확인 2026-11-21)
   - --시작: 영상에서 소리가 시작하는 초 (그만큼 뒤로 밀어 둠)
   결과: {"fps":24, "frames":[[open, wide, round], ...]}  → 장면_입검사.html ?lip=<결과.json>"""
import json, sys
import numpy as np

a = sys.argv[1:]
opt = {"--앞당김": 0.2, "--fps": 24.0, "--시작": 0.0}
for k in list(opt):
    if k in a: i = a.index(k); opt[k] = float(a[i + 1]); del a[i:i + 2]
LEAD, FPS, START = opt["--앞당김"], opt["--fps"], opt["--시작"]
syl = json.load(open(a[0], encoding="utf-8"))
JUNG = "ㅏㅐㅑㅒㅓㅔㅕㅖㅗㅘㅙㅚㅛㅜㅝㅞㅟㅠㅡㅢㅣ"
SHAPE = {}
for v in "ㅏㅑㅘ": SHAPE[v] = (0.9, 0.15, 0.0)
for v in "ㅐㅔㅒㅖㅙㅞ": SHAPE[v] = (0.6, 0.5, 0.0)
for v in "ㅓㅕㅝ": SHAPE[v] = (0.6, 0.0, 0.25)
for v in "ㅗㅛㅚ": SHAPE[v] = (0.35, 0.0, 0.75)
for v in "ㅜㅠㅟ": SHAPE[v] = (0.15, 0.0, 1.0)
for v in "ㅡㅢ": SHAPE[v] = (0.15, 0.45, 0.0)
SHAPE["ㅣ"] = (0.2, 0.75, 0.0)
CLOSE_CHO = {6, 7, 8, 17}                 # ㅁ ㅂ ㅃ ㅍ
CLOSE_JONG = {16, 17, 18, 26, 10, 11, 14}  # ㅁ ㅂ ㅄ ㅍ ㄻ ㄼ ㄿ
keys = [(0.0, (0, 0, 0))]                 # (초, 모양)
prev_end = None
for ch, t0, t1 in syl:
    t0 += START - LEAD; t1 += START - LEAD; d = max(t1 - t0, 0.06)
    if not ("가" <= ch <= "힣"):
        continue
    c = ord(ch) - 0xAC00; cho, jung, jong = c // 588, (c % 588) // 28, c % 28
    sh = SHAPE[JUNG[jung]]
    if prev_end is not None and t0 - prev_end > 0.15:          # 쉼: 입 닫음
        keys += [(prev_end + 0.08, (0, 0, 0)), (t0 - 0.02, (0, 0, 0))]
    if cho in CLOSE_CHO: keys += [(t0, (0, 0, 0)), (t0 + 0.35 * d, sh)]
    else: keys += [(t0 + 0.3 * min(d, 0.25), sh)]
    if jong in CLOSE_JONG: keys += [(t1 - 0.25 * min(d, 0.2), sh), (t1, (0, 0, 0))]
    else: keys += [(t1 - 0.2 * min(d, 0.2), tuple(0.85 * v for v in sh))]
    prev_end = t1
keys += [(prev_end + 0.12, (0, 0, 0))]
keys.sort(key=lambda k: k[0])
ts = np.array([k[0] for k in keys]); vs = np.array([k[1] for k in keys], float)
n = int(np.ceil((ts[-1] + 0.5) * FPS))
tt = np.arange(n) / FPS
fr = np.stack([np.interp(tt, ts, vs[:, j]) for j in range(3)], 1)
ker = np.array([1, 2, 1]) / 4.0                                  # 살짝 부드럽게
fr = np.stack([np.convolve(np.pad(fr[:, j], 1, mode="edge"), ker, "valid") for j in range(3)], 1)
json.dump({"fps": FPS, "frames": np.round(fr, 3).tolist()}, open(a[1], "w"))
print(f"입 모양 {n}장 ({n / FPS:.1f}초), 음절 {len(syl)}개, 앞당김 {LEAD}초 → {a[1]}")
