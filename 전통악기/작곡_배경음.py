"""권역별 '민요풍' 창작 멜로디 — 나레이션 배경음용 60초 (사용자 요청 2026-11-05)
실제 민요를 베끼지 않고, 그 지역 음계·장단·꾸밈(농현·미끄러짐)을 따라 새 가락을 지음 → 저작권 걱정 없음.
나레이션 밑에 깔리도록: 가운데 음역, 느린 빠르기, 쉼을 넉넉히, 타악 없음. 줄을 뜯는 현이 가락, 활로 켜는 현이 긴 음을 받침.
형식: A(열림→닫힘) · B(조금 높게) · A'(닫힘) · 꼬리(으뜸음 길게) → 처음과 끝이 이어져 되풀이해도 자연스러움.
사용: python -X utf8 전통악기/작곡_배경음.py <결과 폴더> [권역:음계 ...]   예) 한국:계면조 중동:바야티   (안 쓰면 권역마다 기본 음계)"""
import importlib.util
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np  # noqa: E402
import 공통 as K  # noqa: E402


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_cs = _load("china_strings", os.path.join(os.path.dirname(HERE), "중국현악.py"))


def _pl(damp, bright, buzz=0.0, bend=0.03):
    return lambda f, d, rng, last: K.pluck(f, d, damp=damp, bright=bright, bend=bend if last else bend * 0.3, vib=0.012 if last else 0.004, buzz=buzz, rng=rng)


def _bw(band, vib_rate, vib, nasal, attack=0.35):
    return lambda f, d, rng=None, last=False: K.bowed(f, d, band=band, vib_rate=vib_rate, vib=vib, nasal=nasal, attack=attack)


# 권역: 악기·빠르기·박자·장단 무늬(마디 안 박 길이)·드론
STYLE = {
    "한국": dict(inst="가야금 + 해금", lead=_pl(0.994, 0.35, bend=0.05), bow=_bw((700, 3600), 4.5, 0.014, 1.0), bpm=60, meter=3,
               rhythms=[[1.5, 0.5, 1], [2, 1], [1, 1, 1], [3], [1, 2]], drone=None, mode="평조",
               note="세마치(3박) 장단 느낌, 긴 음 끝을 흔드는 농현"),
    "중국": dict(inst="고쟁 + 얼후", lead=lambda f, d, rng, last: _cs.guzheng(f, d, bend=0.03 if last else 0.0, rng=rng),
               bow=lambda f, d, rng=None, last=False: _cs.erhu(f, d), bpm=66, meter=4,
               rhythms=[[1, 0.5, 0.5, 2], [2, 1, 1], [1, 1, 2], [0.5, 0.5, 1, 2], [4]], drone=None, mode="상조", gliss=True,
               note="오음계 가락, 마디 첫머리 고쟁 훑기, 얼후가 긴 음을 따라 부름"),
    "일본": dict(inst="고토 + 코큐", lead=_pl(0.992, 0.75), bow=_bw((500, 3000), 5.0, 0.01, 0.6), bpm=54, meter=4,
               rhythms=[[1, 1, 2], [2, 2], [1, 1, 1, 1], [4], [3, 1]], drone=None, mode="미야코부시",
               note="미야코부시 음계, 느리고 쉼이 많은 가락"),
    "중동": dict(inst="우드 + 레바브", lead=_pl(0.993, 0.45, buzz=0.1, bend=0.025), bow=_bw((500, 3200), 5.5, 0.012, 0.9), bpm=66, meter=4,
               rhythms=[[1, 0.5, 0.5, 2], [0.5, 0.5, 1, 2], [1.5, 0.5, 2], [2, 2], [1, 1, 1, 1]], drone="bowed", mode="히자즈",
               note="마캄 히자즈, 우드 가락 + 낮은 드론"),
    "인도": dict(inst="시타르 + 탄푸라", lead=_pl(0.996, 0.6, buzz=0.45, bend=0.05), bow=_bw((400, 2600), 5.0, 0.01, 0.8), bpm=56, meter=4,
               rhythms=[[2, 1, 1], [1, 1, 2], [3, 1], [4], [1, 0.5, 0.5, 2]], drone="pluck", mode="야만",
               note="라가 야만, 탄푸라 드론 위에 미끄러지는 시타르"),
    "몽골": dict(inst="마두금 + 톱쇼르", lead=_bw((250, 2400), 4.0, 0.012, 0.7, attack=0.5), bow=None, bass=_pl(0.99, 0.3), bpm=50, meter=4,
               rhythms=[[3, 1], [4], [2, 2], [1, 3]], drone="bowed", mode="초원장조", legato=True,
               note="긴 노래(오르팅 도) 느낌, 활로 켜는 마두금이 가락을 길게 끌고 톱쇼르가 낮은 음을 뜯음"),
    "중세유럽": dict(inst="류트 + 비올", lead=_pl(0.993, 0.4), bow=_bw((400, 2600), 4.8, 0.006, 0.5), bpm=66, meter=3,
                 rhythms=[[2, 1], [1, 1, 1], [1.5, 0.5, 1], [3]], drone="bowed", mode="도리안",
                 note="도리안 선법, 3박 춤곡풍 류트 가락 + 비올"),
}


def _modes(region):
    if region == "중국":
        return _cs.MODES
    return _load("trad_" + region, os.path.join(HERE, region + ".py")).REGION.modes


def _walk(rng, scale, k, beats, end_k, last_long=True):
    """마디 무늬대로 한 소절: 대부분 한 칸씩 움직이고 가끔 두 칸, 마지막 음은 end_k (열림=5도, 닫힘=으뜸음)"""
    out = []
    for i, b in enumerate(beats):
        if i == len(beats) - 1 and end_k is not None:
            k = end_k
        else:
            k = int(np.clip(k + rng.choice([-1, 1, -1, 1, -2, 2, 0], p=[0.2, 0.2, 0.12, 0.12, 0.1, 0.1, 0.16]), 0, len(scale) - 1))
        out.append([scale[k], b])
    return out, k


def compose(region, mode, rng):
    st = STYLE[region]
    pen, root, _ = _modes(region)[mode]
    scale = [root + o * 12 + p for o in (0, 1, 2) for p in pen if root + 7 <= root + o * 12 + p <= root + 26]
    tonic_k = scale.index(root + 12)
    fifth_k = min(range(len(scale)), key=lambda i: abs(scale[i] - (root + 19)))
    low_fifth = min(range(len(scale)), key=lambda i: abs(scale[i] - (root + 7)))

    def phrase(start_k, end_k, bars=4):
        notes, k = [], start_k
        for j in range(bars):
            beats = list(st["rhythms"][int(rng.integers(len(st["rhythms"])))])
            seg, k = _walk(rng, scale, k, beats, end_k if j == bars - 1 else None)
            notes += seg
        notes[-1][1] = st["meter"]           # 소절 끝은 한 마디 길게
        return notes

    a = phrase(tonic_k, fifth_k)                         # 열림
    a2 = [n[:] for n in a[:-3]] + phrase(scale.index(a[-4][0]) if a[-4][0] in scale else tonic_k, tonic_k, 1)[-3:]   # 같은 머리, 으뜸음으로 닫힘
    b = phrase(min(len(scale) - 1, tonic_k + 2), fifth_k)   # 조금 높게
    a3 = [n[:] for n in a2]
    a3[-1][1] = st["meter"] * 2                          # 마지막은 두 마디 길게
    return [("A", a), ("A'", a2), ("B", b), ("A''", a3)], root, low_fifth, scale


def render(region, mode=None, sec=60.0, seed=21):
    st = STYLE[region]
    mode = mode or st["mode"]
    rng = np.random.default_rng(seed)
    secs, root, _, _ = compose(region, mode, rng)
    beat = 60.0 / st["bpm"]
    n = int((sec + 4) * K.SR)
    buf = np.zeros((n, 2), np.float32)
    lead, bow, bass = st["lead"], st.get("bow"), st.get("bass") or st["lead"]
    t, rep = 1.0, 0
    while t < sec - 6:
        for name, notes in secs:
            bar_t = t
            if st.get("gliss") and name in ("A", "B"):   # 고쟁 훑기 (위에서 아래로)
                for i, mm in enumerate(sorted({x[0] for x in notes}, reverse=True)[:6]):
                    K.place(buf, lead(K.hz(mm + 12), 1.4, rng, False), t - 0.5 + i * 0.06, 0.16, pan=0.3)
            for i, (m, b) in enumerate(notes):
                d = b * beat
                if t > sec - 2.5:
                    break
                last = i == len(notes) - 1
                if st.get("legato"):
                    K.place(buf, lead(K.hz(m), d + 0.5, rng, last), t, 0.30, pan=0.1)
                else:
                    K.place(buf, lead(K.hz(m), max(1.4, d + 0.9), rng, last), t, 0.42, pan=0.12)
                    if d >= 2 * beat and not last:         # 긴 음: 뜯은 현이 사라질 때 한 번 더 살짝 (가야금·우드식)
                        K.place(buf, lead(K.hz(m), d, rng, True), t + d * 0.55, 0.12, pan=0.12)
                if bow and (d >= 2 * beat or last) and name != "A":   # 활 현이 긴 음을 따라 부름 (A는 뜯는 현만 → 점점 풍성)
                    K.place(buf, bow(K.hz(m - 12), d + 0.8), t + 0.08, 0.15, pan=-0.22)
                t += d
            for bt in np.arange(bar_t, t, st["meter"] * beat):   # 마디 첫 박 낮은 음 (으뜸음·5도 번갈아)
                if bt > sec - 3:
                    break
                lm = root if int((bt - bar_t) / (st["meter"] * beat)) % 2 == 0 else root - 5
                K.place(buf, bass(K.hz(lm), st["meter"] * beat + 1.0, rng, False), bt, 0.20 if not st.get("legato") else 0.24, pan=-0.15)
            t += beat * 0.5                              # 소절 사이 숨
            if t > sec - 6:
                break
        rep += 1
    if st["drone"]:
        dr = K.drone([K.hz(root - 12), K.hz(root - 5)] if st["drone"] == "bowed" else
                     [K.hz(root - 5), K.hz(root), K.hz(root), K.hz(root - 12)], n, rng, st["drone"])
        buf[:, 0] += dr * 0.09
        buf[:, 1] += dr * 0.09
    out = K.reverb(buf, rng, wet=0.38)[: int(sec * K.SR)]
    f = int(4 * K.SR)
    out[-f:] *= np.linspace(1, 0, f)[:, None] ** 1.5
    out[: int(0.8 * K.SR)] *= np.linspace(0, 1, int(0.8 * K.SR))[:, None]
    return out / (np.abs(out).max() + 1e-6) * 0.9, mode


def main(a):
    if not a:
        print(__doc__)
        return 2
    out_dir = a[0]
    picks = [x.split(":") for x in a[1:]] or [[r] for r in STYLE]
    os.makedirs(out_dir, exist_ok=True)
    for i, p in enumerate(picks, 1):
        region, mode = p[0], (p[1] if len(p) > 1 else None)
        x, mode = render(region, mode)
        wp = os.path.join(out_dir, f"{i:02d}_{region}_{mode}_창작.wav")
        K.write_wav(wp, x)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", wp, "-b:a", "192k", wp[:-4] + ".mp3"], check=True)
        os.remove(wp)
        print("OK", os.path.basename(wp[:-4] + ".mp3"), "·", STYLE[region]["inst"], "·", STYLE[region]["note"])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
