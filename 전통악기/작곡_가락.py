"""권역별 '노래처럼 들리는' 창작 가락 — 나레이션 배경음용 60초 (사용자가 보낸 예시 두 곡을 본떠, 2026-11-05)
예시 분석: ① 45초 · 약 46bpm · 단조(G 단조, 가운데 음 A) · 활 현이 끊김 없이 미끄러지며 노래 + 밑에서 뜯는 현이 박마다 화음을 펼침
           ② 50초 · 약 67bpm · 장조 오음계(A) · 뜯는 현의 맑은 가락이 4마디(약 7초)마다 숨을 쉼 + 펼친 화음
→ 두 가지 풍:  '활'  = ①처럼 애잔한 활 현 가락(미끄러짐·떨림) + 뜯는 현 펼친 화음
               '뜯음' = ②처럼 맑은 뜯는 현 가락(동기 되풀이·4마디 숨) + 펼친 화음 + 아주 작은 활 현 받침
가락은 '동기(한 마디 무늬)'를 만들어 되풀이·옮기기·끝맺기로 이어 붙여 노래처럼 기억에 남게 함 (무작위 걷기 X).
실제 노래를 베끼지 않은 창작 → 저작권 걱정 없음. 타악 없음.
사용: python -X utf8 전통악기/작곡_가락.py <결과 폴더> [권역:풍[:음계] ...]   예) 한국:활 중국:뜯음:궁조   (안 쓰면 7권역 × 2풍)"""
import importlib.util
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np  # noqa: E402
import 공통 as K  # noqa: E402
from 작곡_배경음 import STYLE, _modes  # noqa: E402

SR = K.SR

# 권역별 활 현 소리(몸통 울림 띠, 떨림 빠르기·깊이, 콧소리) · 풍마다 기본 음계
BOW = {"한국": ((700, 3600), 4.5, 0.016, 1.0, "해금"), "중국": ((600, 3200), 5.3, 0.010, 0.8, "얼후"),
       "일본": ((500, 3000), 5.0, 0.010, 0.6, "코큐"), "중동": ((500, 3200), 5.5, 0.012, 0.9, "레바브"),
       "인도": ((400, 3000), 5.2, 0.012, 0.85, "사랑기"), "몽골": ((250, 2400), 4.0, 0.012, 0.7, "마두금"),
       "중세유럽": ((400, 2600), 4.8, 0.007, 0.5, "비올")}
PLUCK_NAME = {"한국": "가야금", "중국": "고쟁", "일본": "고토", "중동": "우드", "인도": "시타르", "몽골": "톱쇼르", "중세유럽": "류트"}
MODE = {"활": {"한국": "계면조", "중국": "우조", "일본": "미야코부시", "중동": "바야티", "인도": "카피", "몽골": "초원단조", "중세유럽": "에올리안"},
        "뜯음": {"한국": "평조", "중국": "궁조", "일본": "요음계", "중동": "라스트", "인도": "야만", "몽골": "초원장조", "중세유럽": "믹솔리디안"}}
BPM = {"활": 48, "뜯음": 66}
METER = {"한국": 3, "중세유럽": 3}          # 나머지 4박


def legato(notes, band, vib_rate, vib, nasal, glide=0.09):
    """활 현이 끊지 않고 한 숨에 켜는 가락: notes=[(midi, 초)] → 음 사이를 미끄러지고(glide), 긴 음은 떨고, 활 바꿀 때 살짝 작아짐"""
    from scipy.signal import butter, lfilter
    total = sum(d for _, d in notes) + 0.6
    n = int(total * SR)
    f = np.zeros(n)
    amp = np.ones(n)
    t0, prev = 0, None
    for m, d in notes:
        a, b = int(t0 * SR), int((t0 + d) * SR)
        hz = K.hz(m)
        seg = np.full(b - a, hz)
        if prev is not None:
            g = min(b - a, int(glide * SR))
            seg[:g] = np.exp(np.linspace(np.log(prev), np.log(hz), g))
            amp[a:a + int(0.12 * SR)] *= np.linspace(0.72, 1, len(amp[a:a + int(0.12 * SR)]))   # 활 바꾸는 곳
        tt = np.arange(b - a) / SR
        seg = seg * (1 + vib * np.sin(2 * np.pi * vib_rate * tt) * np.clip((tt - 0.35) / 0.5, 0, 1))
        f[a:b] = seg
        prev, t0 = hz, t0 + d
    f[int(t0 * SR):] = prev
    ph = np.cumsum(2 * np.pi * f / SR)
    saw = (2 * ((ph / (2 * np.pi)) % 1) - 1)
    bb, aa = butter(2, [band[0] / (SR / 2), band[1] / (SR / 2)], "band")
    y = lfilter(bb, aa, saw) * nasal + lfilter(*butter(1, 900 / (SR / 2)), saw) * 0.35
    t = np.arange(n) / SR
    y = y * amp * np.clip(t / 0.4, 0, 1) * np.clip((total - t) / 0.7, 0, 1)
    return (y / (np.abs(y).max() + 1e-6)).astype(np.float32)


def _near(scale, target):
    return min(scale, key=lambda s: abs(s - target))


def compose(region, kind, mode, rng):
    """동기 → 노래 형식. 반환: 소절 목록 [(이름, [(midi|None, 박)], 마디별 화음 뿌리 midi)]"""
    pen, root, _ = _modes(region)[mode]
    meter = METER.get(region, 4)
    lo, hi = root + 12, root + 29
    scale = [root + o * 12 + p for o in range(0, 4) for p in pen if lo <= root + o * 12 + p <= hi]
    idx = {s: i for i, s in enumerate(scale)}
    tonic, fifth = root + 12, _near(scale, root + 19)
    # 화음 뿌리 진행 (음계 안의 음으로): 단조풍 i–VI–iv–v / 장조풍 I–IV–V–I (없으면 가까운 음)
    prog = ([0, 8, 5, 7] if kind == "활" else [0, 5, 7, 0])
    roots = [_near([root + p for p in pen] + [root + 12], root + p) for p in prog]
    rhythms = ({3: [[1.5, 0.5, 1], [2, 1], [1, 1, 1]], 4: [[1.5, 0.5, 2], [2, 1, 1], [1, 1, 2], [3, 1]]} if kind == "활" else
               {3: [[1, 0.5, 0.5, 1], [1, 1, 1], [0.5, 0.5, 1, 1]], 4: [[1, 0.5, 0.5, 1, 1], [0.5, 0.5, 1, 2], [1, 1, 0.5, 0.5, 1], [1, 1, 2]]})[meter]
    motif_r = rhythms[int(rng.integers(len(rhythms)))]
    steps = [int(rng.choice([-1, 1, 2, -2, 0], p=[0.3, 0.3, 0.15, 0.15, 0.1])) for _ in motif_r]   # 동기의 오르내림 (칸 수)

    def bar(start, shift=0, rhy=None, end=None):
        rhy = rhy or motif_r
        k = idx[_near(scale, start)] + shift
        out = []
        for i, b in enumerate(rhy):
            k = int(np.clip(k + (steps[i % len(steps)] if i else 0), 0, len(scale) - 1))
            out.append([scale[k], b])
        if end is not None:
            out[-1][0] = end
        return out

    def phrase(start, cadence, var=0):
        p = bar(start)                                       # 1마디: 동기
        p += bar(p[-1][0], shift=-1 + var)                   # 2마디: 동기를 한 칸 아래로(옮기기)
        p += bar(p[-1][0], shift=1, rhy=rhythms[(rhythms.index(motif_r) + 1 + var) % len(rhythms)])   # 3마디: 무늬를 바꿔 이어 감
        p += [[cadence, meter - (0.5 if kind == "뜯음" else 0)]] + ([[None, 0.5]] if kind == "뜯음" else [])   # 4마디: 끝맺음 + (뜯음은 숨)
        return p

    A = phrase(tonic + (3 if kind == "활" else 0), fifth)           # 열림 (5도)
    A2 = phrase(tonic + (3 if kind == "활" else 0), tonic, var=1)   # 닫힘 (으뜸음)
    B = phrase(_near(scale, tonic + 9), fifth, var=2)              # 조금 높게
    secs = [("A", A), ("A'", A2), ("B", B), ("A''", A2)]
    return secs, roots, root, meter, scale


def render(region, kind, mode=None, sec=60.0, seed=5):
    mode = mode or MODE[kind][region]
    rng = np.random.default_rng(seed)
    secs, roots, root, meter, scale = compose(region, kind, mode, rng)
    beat = 60.0 / BPM[kind]
    st = STYLE[region]
    pluck = st["bass"] if region == "몽골" else st["lead"]
    band, vr, vb, nas, _ = BOW[region]
    n = int((sec + 6) * SR)
    buf = np.zeros((n, 2), np.float32)
    t = 0.8
    bar_i = 0
    while t < sec - 4:
        for name, notes in secs:
            if t > sec - 4:
                break
            start = t
            dur = sum(b for _, b in notes) * beat
            # 가락
            if kind == "활":
                seg, line = [], []
                for m, b in notes:
                    if m is None:
                        if line:
                            seg.append(line)
                        line = []
                    else:
                        line.append((m, b * beat))
                if line:
                    seg.append(line)
                tt = t
                for line in seg:
                    K.place(buf, legato(line, band, vr, vb * 1.4, nas), tt, 0.34, pan=0.12)
                    tt += sum(d for _, d in line)
            else:
                tt = t
                for i, (m, b) in enumerate(notes):
                    if m is not None:
                        K.place(buf, pluck(K.hz(m), max(1.5, b * beat + 1.0), rng, b >= meter - 0.5), tt, 0.40, pan=0.12)
                    tt += b * beat
                if name in ("B", "A''"):                    # 뒤로 갈수록 활 현이 긴 음을 아주 작게 따라 부름
                    long_ = [(m, b * beat) for m, b in notes if m is not None and b >= 2]
                    tt = t
                    for m, b in notes:
                        if m is not None and b >= 2:
                            K.place(buf, legato([(m - 12, b * beat + 0.5)], band, vr, vb, nas), tt, 0.10, pan=-0.2)
                        tt += b * beat
            # 펼친 화음: 마디마다 뿌리음 – 5도 – 옥타브 – 5도 … (뜯는 현, 박을 둘로 나눠)
            nb = int(round(dur / (meter * beat)))
            for j in range(nb):
                r = roots[(bar_i + j) % len(roots)]
                f5 = _near([s - 12 for s in scale] + scale, r + 7)
                pat = [r - 12, f5 - 12, r, f5 - 12] if meter == 4 else [r - 12, f5 - 12, r]
                bt0 = start + j * meter * beat
                for q in range(meter * 2):
                    nt = bt0 + q * beat * 0.5
                    if nt > sec - 1.5:
                        break
                    K.place(buf, pluck(K.hz(pat[q % len(pat)]), beat * 2.2, rng, False), nt, (0.22 if q == 0 else 0.13), pan=-0.18)
            bar_i += nb
            t += dur
    out = K.reverb(buf, rng, wet=0.36)[: int(sec * SR)]
    f = int(4 * SR)
    out[-f:] *= np.linspace(1, 0, f)[:, None] ** 1.5
    out[: int(0.6 * SR)] *= np.linspace(0, 1, int(0.6 * SR))[:, None]
    return out / (np.abs(out).max() + 1e-6) * 0.9, mode


def main(a):
    if not a:
        print(__doc__)
        return 2
    out_dir = a[0]
    picks = [x.split(":") for x in a[1:]] or [[r, k] for k in ("활", "뜯음") for r in STYLE]
    os.makedirs(out_dir, exist_ok=True)
    for i, p in enumerate(picks, 1):
        region, kind, mode = p[0], p[1], (p[2] if len(p) > 2 else None)
        x, mode = render(region, kind, mode)
        inst = f"{BOW[region][4]} 가락 + {PLUCK_NAME[region]} 화음" if kind == "활" else f"{PLUCK_NAME[region]} 가락 + 화음"
        wp = os.path.join(out_dir, f"{i:02d}_{region}_{kind}_{mode}.wav")
        K.write_wav(wp, x)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", wp, "-b:a", "192k", wp[:-4] + ".mp3"], check=True)
        os.remove(wp)
        print("OK", os.path.basename(wp[:-4] + ".mp3"), "·", inst)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
