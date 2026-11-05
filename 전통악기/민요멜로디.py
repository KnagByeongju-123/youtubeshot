"""권역별 '전통 노래 멜로디' 배경음 (현악 위주, 30초) — 사용자 요청 2026-11-05
뜯는 현(가야금·고쟁·고토·우드·류트)이 실제 전통 민요 가락을 연주하고, 활로 켜는 현(해금·얼후·코큐·레바브·비올)이 긴 음을 받쳐 줌.
저작권: 모두 작곡가를 알 수 없는 옛 민요(퍼블릭 도메인)이고, 소리는 프로그램이 직접 합성 → 음원 저작권 없음.
사용: python -X utf8 전통악기/민요멜로디.py <결과 폴더> [곡 이름 ...]   (곡을 안 쓰면 전부)"""
import importlib.util
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np  # noqa: E402
import 공통 as K  # noqa: E402

_spec = importlib.util.spec_from_file_location("china_strings", os.path.join(os.path.dirname(HERE), "중국현악.py"))
_cs = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_cs)

NOTE = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}


def parse(text):
    out = []
    for tok in text.split():
        n, _, b = tok.partition(":")
        b = float(b) if b else 1.0
        if n.upper() == "R":
            out.append((None, b))
            continue
        m = re.match(r"([A-G])([#b]?)(\d)", n)
        out.append((12 * (int(m.group(3)) + 1) + NOTE[m.group(1)] + (1 if m.group(2) == "#" else -1 if m.group(2) == "b" else 0), b))
    return out


def _pl(damp, bright, buzz=0.0, vib=0.004):
    return lambda f, d, rng, last: K.pluck(f, d, damp=damp, bright=bright, bend=0.03 if last else 0.0, vib=0.012 if last else vib, buzz=buzz, rng=rng)


# 곡: (권역, 곡 이름, 뜯는 현, 켜는 현, 템포 bpm, 멜로디, 으뜸음 MIDI(드론), 설명)
SONGS = {
    "한국_아리랑": ("한국", "아리랑", _pl(0.994, 0.35), lambda f, d: K.bowed(f, d, band=(700, 3600), vib_rate=4.5, vib=0.014, nasal=1.0), 66,
                 "C4:2.5 D4:0.5 C4 D4:0.5 F4:2.5 G4:0.5 F4 G4:0.5 A4:1.5 G4:0.5 A4:0.5 G4:0.5 F4 D4:0.5 C4:2.5 D4:0.5 C4:0.5 "
                 "D4:0.5 R:0.5 F4:2.5 G4:0.5 F4 G4:0.5 A4 G4:0.5 F4 D4:0.5 C4 D4:0.5 F4:2.5 G4:0.5 F4:1.5 F4:3 R:1.5 C5:3 C5:1.5 "
                 "C5:1.5 A4:1.5 G4:1.5 A4:1.5 G4 A4:0.5 F4 D4:0.5 C4:2.5 D4:0.5 C4:0.5 D4:0.5 R:0.5 F4:2.5 G4:0.5 F4 G4:0.5 A4 "
                 "G4:0.5 F4 D4:0.5 C4 D4:0.5 F4:2.5 G4:0.5 F4:1.5 F4:3 R:1.5", 41, "가야금 + 해금 · 한국 민요 아리랑 (3/4 세마치 느낌)"),
    "한국_도라지타령": ("한국", "도라지 타령", _pl(0.994, 0.35), lambda f, d: K.bowed(f, d, band=(700, 3600), vib_rate=4.5, vib=0.014, nasal=1.0), 72,
                   "B4 B4 B4 B4:1.5 A4:0.5 G4 D5:2 E5:0.5 D5:0.5 B4:1.5 A4:0.5 G4 A4:0.5 B4:0.5 B4:2 A4:0.5 B4:0.5 A4:0.5 G4:0.5 "
                   "E4:0.5 D4:0.5 E4 G4:1.5 E4:0.5 D4:3 B4 B4:2 B4 B4 A4:0.5 B4:0.5 D5:2 E5:0.5 D5:0.5 B4:1.5 A4:0.5 G4 A4:0.5 "
                   "B4:0.5 B4:0.5 B4:0.5 B4 A4:0.5 B4:0.5 A4:0.5 G4:0.5 E4:0.5 D4:0.5 E4 G4:1.5 E4:0.5 D4:3", 43, "가야금 + 해금 · 한국 민요 도라지 타령"),
    "중국_모리화": ("중국", "모리화(茉莉花)", lambda f, d, rng, last: _cs.guzheng(f, d, bend=0.03 if last else 0.0, rng=rng), lambda f, d: _cs.erhu(f, d), 72,
                "A4:0.5 A4:0.5 C5:0.5 D5:0.5 F5:0.5 F5:0.5 D5:0.5 C5:0.5 C5:1 D5:0.5 C5:0.5 C5:2 "
                "A4:0.5 A4:0.5 C5:0.5 D5:0.5 F5:0.5 F5:0.5 D5:0.5 C5:0.5 C5:1 D5:0.5 C5:0.5 C5:2 "
                "C5:1 C5:1 C5:1 A4:0.5 C5:0.5 D5:1 D5:1 C5:2 A4:1 G4:0.5 A4:0.5 C5:1 A4:0.5 G4:0.5 F4:1 F4:0.5 G4:0.5 F4:2 R:1", 41,
                "고쟁 + 얼후 · 중국 강남 민요 모리화"),
    "일본_사쿠라": ("일본", "사쿠라 사쿠라(さくらさくら)", _pl(0.992, 0.75), lambda f, d: K.bowed(f, d, band=(500, 3000), vib_rate=5.0, vib=0.01, nasal=0.6), 60,
                "A4 A4 B4:2 A4 A4 B4:2 A4 B4 C5 B4 A4 B4:0.5 A4:0.5 F4:2 E4 C4 E4 F4 E4 E4:0.5 C4:0.5 B3:2 "
                "A4 B4 C5 B4 A4 B4:0.5 A4:0.5 F4:2 E4 C4 E4 F4 E4 E4:0.5 C4:0.5 B3:2 A4 A4 B4:2 A4 A4 B4:2 E4 F4 B4:0.5 A4:0.5 F4 E4:4", 40,
                "고토 + 코큐(활로 켜는 현) · 일본 옛 노래 사쿠라 사쿠라 (미야코부시 음계)"),
    "중동_야밀아바야": ("중동", "야밀 아바야(Yammil Abaya)", _pl(0.993, 0.45, buzz=0.1), lambda f, d: K.bowed(f, d, band=(500, 3200), vib_rate=5.5, vib=0.012, nasal=0.9), 60,
                   "D5 C5:0.5 B4:0.5 B4:0.5 G#4:0.5 B4:0.5 G#4:0.5 G4:1.5 G#4:0.5 G4:0.5 F4:0.5 G4 F4 F4:0.5 E4:0.5 F4 G4 G4:3 R "
                   "A#4 A#4:0.5 A4:0.5 A4:0.5 G4:0.5 G4:0.5 F4:0.5 F4:0.5 E4 F4:0.5 E4:0.5 D4:0.5 E4 G4 F4 E4:0.5 C#4:0.5 E4:0.5 "
                   "C#4:0.5 C4:4", 36, "우드 + 레바브(활로 켜는 현) · 이라크 민요 야밀 아바야 (히자즈)"),
    "중세유럽_그린슬리브스": ("중세유럽", "그린슬리브스(Greensleeves)", _pl(0.993, 0.4), lambda f, d: K.bowed(f, d, band=(400, 2600), vib_rate=4.8, vib=0.006, nasal=0.5), 76,
                      "E4 G4:2 A4 B4:1.5 C5:0.5 B4 A4:2 F#4 D4:1.5 E4:0.5 F#4 G4:2 E4 E4:1.5 D#4:0.5 E4 F#4:2 D#4 B3:2 E4 G4:2 A4 "
                      "B4:1.5 C5:0.5 B4 A4:2 F#4 D4:1.5 E4:0.5 F#4 G4:1.5 F#4:0.5 E4 D#4:1.5 C#4:0.5 D#4 E4:4 R R", 40,
                      "류트 + 비올(활로 켜는 현) · 16세기 영국 노래 그린슬리브스"),
    "중세유럽_스카버러페어": ("중세유럽", "스카버러 페어(Scarborough Fair)", _pl(0.993, 0.4), lambda f, d: K.bowed(f, d, band=(400, 2600), vib_rate=4.8, vib=0.006, nasal=0.5), 76,
                      "D4:2 D4 A4:2 A4 E4:1.5 F4:0.5 E4 D4:4 A4 C5 D5:2 C5 A4 B4 G4 A4:4 R D5 D5:2 D5 C5:2 A4 A4 G4 F4 E4 C4:4 R D4:2 "
                      "A4 G4:2 F4 E4 D4 C4 D4:4 R:2", 38, "류트 + 비올 · 영국 옛 민요 스카버러 페어 (도리안)"),
}


def render(key, sec=30.0, seed=7):
    region, title, pluck, bow, bpm, mel, tonic, _ = SONGS[key]
    rng = np.random.default_rng(seed)
    notes = parse(mel)
    beat = 60.0 / bpm
    n = int((sec + 3) * K.SR)
    buf = np.zeros((n, 2), np.float32)
    t = 0.6
    while t < sec - 1.0:                                   # 멜로디를 30초가 찰 때까지 되풀이
        for i, (m, b) in enumerate(notes):
            d = b * beat
            if t > sec - 0.8:
                break
            if m is not None:
                last = i == len(notes) - 1 or (i + 1 < len(notes) and notes[i + 1][0] is None)
                K.place(buf, pluck(K.hz(m), max(1.2, d + 0.8), rng, last), t, 0.55, pan=0.15)
                if d >= 1.4 * beat or last:                # 긴 음은 활 현이 받쳐 줌 (한 옥타브 아래, 작게)
                    K.place(buf, bow(K.hz(m - 12), d + 0.6), t + 0.05, 0.20, pan=-0.2)
                elif d >= 1.9 * beat * 0.5 and rng.random() < 0.25:
                    K.place(buf, pluck(K.hz(m - 12), d + 0.5, rng, False), t, 0.18, pan=-0.25)
            t += d
        t += beat
    dr = K.drone([K.hz(tonic), K.hz(tonic + 7)], n, rng, "bowed")   # 으뜸음 드론 (아주 작게)
    buf[:, 0] += dr * 0.10
    buf[:, 1] += dr * 0.10
    out = K.reverb(buf, rng, wet=0.33)[: int(sec * K.SR)]
    f = int(2.5 * K.SR)                                     # 끝 2.5초 서서히 줄임
    out[-f:] *= np.linspace(1, 0, f)[:, None]
    out[: int(0.3 * K.SR)] *= np.linspace(0, 1, int(0.3 * K.SR))[:, None]
    return out / (np.abs(out).max() + 1e-6) * 0.9


def main(a):
    if not a:
        print(__doc__)
        return 2
    out_dir, names = a[0], a[1:] or list(SONGS)
    os.makedirs(out_dir, exist_ok=True)
    for i, k in enumerate(names, 1):
        wp = os.path.join(out_dir, f"{i:02d}_{k}.wav")
        K.write_wav(wp, render(k))
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", wp, "-b:a", "192k", wp[:-4] + ".mp3"], check=True)
        os.remove(wp)
        print("OK", os.path.basename(wp[:-4] + ".mp3"), "·", SONGS[k][7])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
