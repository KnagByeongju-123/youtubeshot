"""국악기 연주 녹음을 재서 합성 소리를 맞출 숫자를 뽑음 (진짜 연주와 우리 합성 샘플을 같은 방법으로 재서 비교)

재는 것
  - 음역: 음 높이 분포 (MIDI 5%·50%·95%)
  - 농현(떨림): 빠르기(1초에 몇 번), 깊이(센트, 100 = 반음), 음 앞부분과 뒷부분의 깊이 차이
  - 퇴성·추성: 소리 끝 0.3초 동안 내려간 정도, 시작 0.2초 동안 올라온 정도 (반음)
  - 음 길이, 음 사이 미끄러짐 시간, 쉼 길이
  - 음색: 배음(1~12번째) 세기(dB, 바탕음 기준), 밝기(무게중심 Hz), 배음 사이 잡음 비율, 세기 떨림(거친 정도)

사용: .sd_venv/bin/python -X utf8 전통악기/연주분석.py <소리파일> [<소리파일> ...] [--초 N] [--json 결과.json]
  (librosa 필요 → .sd_venv. 앞에서 N초만 잼, 기본 240)
"""
import argparse
import json
import os
import sys

import numpy as np

SR = 22050
HOP = 220            # 0.01초


def runs(mask):
    """True 가 이어진 구간들 [(시작, 끝)]"""
    out, s = [], None
    for i, v in enumerate(mask):
        if v and s is None:
            s = i
        if not v and s is not None:
            out.append((s, i))
            s = None
    if s is not None:
        out.append((s, len(mask)))
    return out


def movavg(x, w):
    w = max(1, int(w))
    pad = np.concatenate([np.full(w, x[0]), x, np.full(w, x[-1])])
    return np.convolve(pad, np.ones(w) / w, "same")[w:w + len(x)]


def analyze(path, sec=240):
    import librosa
    y, _ = librosa.load(path, sr=SR, mono=True, duration=sec)
    f0, voiced, prob = librosa.pyin(y, fmin=55, fmax=900, sr=SR, frame_length=2048, hop_length=HOP)
    voiced = voiced & (prob > 0.15) & np.isfinite(f0)
    midi = np.where(voiced, 69 + 12 * np.log2(np.where(voiced, f0, 440) / 440), np.nan)
    r = {"파일": os.path.basename(path), "길이초": round(len(y) / SR, 1), "소리난비율": round(float(voiced.mean()), 2)}
    vm = midi[voiced]
    r["음역_MIDI_5_50_95"] = [round(float(np.percentile(vm, q)), 1) for q in (5, 50, 95)]

    vib_rate, vib_depth, early, late, falls, pushes, note_lens, glides, pauses = [], [], [], [], [], [], [], [], []
    segs = [(a, b) for a, b in runs(voiced) if b - a >= 40]          # 0.4초 넘게 이어진 소리
    for a, b in runs(~voiced):
        if 15 <= b - a <= 400 and a > 0:
            pauses.append((b - a) / 100)
    for a, b in segs:
        m = midi[a:b]
        trend = movavg(m, 60)                                          # 0.6초 평균 = 음 자체 (3Hz 넘는 떨림은 지워짐, 큰 떨림도)
        short = movavg(m, 10)                                          # 0.1초 평균 (미끄러짐 시간 재기용)
        res = (m - trend) * 100                                        # 떨림 (센트)
        slope = np.abs(np.gradient(trend)) * 100                       # 1초당 반음 (떨림은 지워진 곡선으로)
        moving = slope > 4                                             # 1초에 4반음 넘게 움직임 = 다음 음으로 미끄러짐
        for ga, gb in runs(moving):
            gb = min(gb, len(m) - 1)
            step = trend[gb] - trend[ga]
            if gb - ga >= 3 and abs(step) > 0.7:                       # 0.1초 곡선이 10%→90% 가는 시간
                u = (short[ga:gb] - short[ga]) / step
                i1, i2 = np.argmax(u > 0.1), np.argmax(u > 0.9)
                if i2 > i1:
                    glides.append((i2 - i1) / 100)
        for na, nb in runs(~moving):
            if nb - na < 25:
                continue
            note_lens.append((nb - na) / 100)
            rr = res[na:nb]
            if nb - na >= 50:                                          # 0.5초 넘는 음에서 떨림
                x = rr - rr.mean()
                ac = np.correlate(x, x, "full")[len(x) - 1:]
                lo, hi = 100 // 9, 100 // 2                            # 2~9Hz
                if ac[0] > 0 and len(ac) > hi:
                    k = lo + int(np.argmax(ac[lo:hi]))
                    if ac[k] > 0.2 * ac[0]:
                        vib_rate.append(100 / k)
                    vib_depth.append(float(np.std(x) * np.sqrt(2)))
                    h = (nb - na) // 3
                    early.append(float(np.std(rr[:h]) * np.sqrt(2)))
                    late.append(float(np.std(rr[-h:]) * np.sqrt(2)))
        if b - a >= 60:                                                # 소리 끝·시작 (떨림 한 번보다 긴 창의 가운데값)
            falls.append(float(np.nanmedian(m[-15:]) - np.nanmedian(m[-60:-35])))
            pushes.append(float(np.nanmedian(m[25:40]) - np.nanmedian(m[:8])))

    def st(v, nd=2):
        return [round(float(np.percentile(v, q)), nd) for q in (25, 50, 75)] if len(v) else None
    r["농현_빠르기Hz_25_50_75"] = st(vib_rate)
    r["농현_깊이센트_25_50_75"] = st(vib_depth, 0)
    r["농현_앞부분_뒷부분_센트"] = [round(float(np.median(early)), 0), round(float(np.median(late)), 0)] if early else None
    r["퇴성_끝0.3초_반음_25_50_75"] = st(falls)
    r["퇴성_1반음넘게_내린비율"] = round(float(np.mean(np.array(falls) < -1)), 2) if falls else None
    r["추성_시작_반음_50"] = round(float(np.median(pushes)), 2) if pushes else None
    r["추성_1반음넘게_올린비율"] = round(float(np.mean(np.array(pushes) > 1)), 2) if pushes else None
    r["음길이초_25_50_75"] = st(note_lens)
    r["미끄러짐초_25_50_75"] = st(glides)
    r["쉼초_25_50_75"] = st(pauses)

    # 음색: 소리 난 곳에서 배음 세기
    S = np.abs(librosa.stft(y, n_fft=4096, hop_length=HOP))
    freqs = librosa.fft_frequencies(sr=SR, n_fft=4096)
    harm, noise_r, cent = [], [], []
    idx = np.where(voiced)[0][::5]
    for i in idx:
        if i >= S.shape[1]:
            continue
        col, f = S[:, i], f0[i]
        hs = []
        mask = np.zeros(len(freqs), bool)
        for h in range(1, 13):
            if h * f > SR / 2 - 200:
                hs.append(np.nan)
                continue
            band = np.abs(freqs - h * f) < f * 0.12
            hs.append(col[band].max())
            mask |= np.abs(freqs - h * f) < f * 0.2
        hs = np.array(hs)
        if hs[0] > 0:
            harm.append(20 * np.log10(hs / (np.nanmax(hs[:3]) + 1e-9) + 1e-9))
        band_all = (freqs > f * 0.8) & (freqs < min(8000, 13 * f))
        e = col[band_all] ** 2
        noise_r.append(float(e[~mask[band_all]].sum() / (e.sum() + 1e-12)))
        cent.append(float((freqs * col).sum() / (col.sum() + 1e-12)))
    r["배음세기dB_1_12"] = [round(float(v), 1) for v in np.nanmedian(np.array(harm), 0)]
    r["밝기_무게중심Hz"] = round(float(np.median(cent)), 0)
    r["잡음비율"] = round(float(np.median(noise_r)), 3)
    rms = librosa.feature.rms(y=y, frame_length=512, hop_length=110)[0]
    fast = rms / (movavg(rms, 10) + 1e-9) - 1                          # 0.05초보다 빠른 세기 떨림 = 거친 결
    vv = np.repeat(voiced, 2)[: len(fast)]
    r["세기_빠른떨림"] = round(float(np.std(fast[vv[: len(fast)]])), 3)
    return r


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--초", type=float, default=240)
    ap.add_argument("--json")
    a = ap.parse_args()
    res = []
    for f in a.files:
        r = analyze(f, a.초)
        res.append(r)
        print(json.dumps(r, ensure_ascii=False))
        sys.stdout.flush()
    if a.json:
        with open(a.json, "w", encoding="utf-8") as fp:
            json.dump(res, fp, ensure_ascii=False, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
