"""사진 아나운서 말하기 — 그림 AI(klein)로 그린 아나운서 사진 한 장 + 입 모양 사진으로 말하는 영상 (라이선스 걱정 없음, 몇 초면 만듦)

1) 입 모양 요청서 만들기 (입·눈 상자는 사진에서 입·두 눈을 넉넉히 감싸는 칸, x0,y0,x1,y1)
   .supertonic_venv/bin/python -X utf8 실사3D/사진아나운서.py 준비 <아나운서.png> <폴더> --입 440,282,610,372 --눈 400,165,650,232
   → <폴더>/기본.png, 다문입·아·오·이·눈감음.png(사진 복사), job.json, 상자.json
2) 입 모양 그리기 (약 3분)
   .sd_venv/bin/python -X utf8 klein_worker.py models/FLUX2_klein_4B <폴더>/job.json <폴더>
   → 다섯 장을 크게 열어 확인: 입 말고 얼굴이 바뀌었으면 그 장만 seed 를 바꿔 다시
3) 영상 (나레이션은 겹침·받아쓰기 검사를 통과한 것)
   .supertonic_venv/bin/python -X utf8 실사3D/사진아나운서.py 영상 <폴더> <나레이션.mp3> <대본.txt 또는 "글"> <결과.mp4> [--크기 1920x1080] [--시각 <발음시각.json>]
방법: 1/24초마다 소리 크기 → 작으면 다문 입, 크면 대본 음절의 모음대로 아(ㅏㅓ)·오(ㅗㅜ)·이(ㅔㅐㅣㅡ), 첫소리 ㅁㅂㅍ·받침 ㅁㅂ = 다문 입.
      입·눈 칸만 부드러운 테두리로 바꿔 끼우고 2장에 걸쳐 섞음(뚝뚝 끊기지 않게). 눈 깜빡임 약 3초마다, 화면은 천천히 다가가며 살짝 흔들림
"""
import json
import os
import shutil
import subprocess
import sys

import numpy as np
from PIL import Image, ImageFilter

FPS = 24
SHAPES = ["다문입", "아", "오", "이"]
COMMON = ", same woman, same lips color and skin, photorealistic, natural, keep everything else identical"
PROMPTS = {
    "다문입": "her lips gently closed in a soft closed-mouth smile, no teeth visible",
    "아": "her mouth open naturally while speaking the vowel 'ah', jaw slightly dropped, upper teeth and a little tongue visible",
    "오": "her lips rounded and pushed slightly forward in a small 'o' shape while speaking, small round opening",
    "이": "her mouth slightly open and wide while speaking the vowel 'ee', upper and lower teeth slightly apart",
    "눈감음": "her eyes gently closed in a natural blink, eyelashes down, relaxed eyelids, same eyebrows",
}


def box(s):
    return [int(v) for v in s.split(",")]


def opt(a, k, d=None):
    return a[a.index(k) + 1] if k in a else d


def prepare(a):
    src, out = a[0], os.path.abspath(a[1])
    mb, eb = box(opt(a, "--입")), box(opt(a, "--눈"))
    os.makedirs(out, exist_ok=True)
    shutil.copy(src, os.path.join(out, "기본.png"))
    fixes = []
    for n in SHAPES + ["눈감음"]:
        p = os.path.join(out, n + ".png")
        shutil.copy(src, p)
        fixes.append({"id": n, "image": p, "box": eb if n == "눈감음" else mb, "prompt": PROMPTS[n] + COMMON, "seed": 3})
    json.dump({"fixes": fixes}, open(os.path.join(out, "job.json"), "w"), ensure_ascii=False, indent=1)
    json.dump({"입": mb, "눈": eb}, open(os.path.join(out, "상자.json"), "w"))
    print("준비 끝:", out)


def plan_shapes(wav, text, n_frames, timing=None):
    """프레임마다 입 모양. 소리 크기 + 음절 모음. timing(발음시각.py 결과 [[음절, 시작, 끝]...])이 있으면 그 시각대로, 없으면 음절을 소리 난 구간에 고르게"""
    import wave
    w = wave.open(wav)
    sr = w.getframerate()
    a = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    hop = sr // FPS
    rms = np.array([np.sqrt(np.mean(a[i * hop:(i + 1) * hop + hop // 2] ** 2) + 1e-12) for i in range(n_frames)])
    rms = np.convolve(rms, [0.25, 0.5, 0.25], "same")
    peak = np.percentile(rms, 95)
    voiced = [i for i in range(n_frames) if rms[i] > peak * 0.12]
    VOW = {0: "아", 2: "아", 9: "아", 4: "아", 6: "아", 14: "아", 8: "오", 12: "오", 13: "오", 16: "오", 17: "오"}
    syl = [c for c in text if 0xAC00 <= ord(c) <= 0xD7A3]
    plan = {}
    per = len(voiced) / max(len(syl), 1)
    if timing:
        syl = [t[0] for t in timing]
    for j, ch in enumerate(syl):
        v = ord(ch) - 0xAC00
        cho, jung, jong = v // 588, (v % 588) // 28, v % 28
        if timing:
            f0, f1 = int(timing[j][1] * FPS), int(round(timing[j][2] * FPS))
            fr = list(range(f0, max(f1, f0 + 1)))
        else:
            fr = voiced[int(j * per):max(int((j + 1) * per), int(j * per) + 1)]
        for k, f in enumerate(fr):
            t = k / max(len(fr), 1)
            if (cho in (6, 7, 8, 17) and t < 0.3) or (jong in (16, 17, 26) and t > (0.15 if jung in (18, 19, 20) else 0.4)):   # 받침 ㅁㅂㅍ 은 일찍 닫음(습니다)
                plan[f] = "다문입"
            else:
                plan[f] = VOW.get(jung, "이")
    out = []
    for f in range(n_frames):
        lvl = min(1.0, rms[f] / peak * 1.2)
        s = plan.get(f, "다문입")
        if lvl < 0.22:
            s = "다문입"
        out.append(s)
    return out


def soft_mask(size, b, feather):
    m = Image.new("L", size, 0)
    m.paste(255, (b[0] + feather, b[1] + feather, b[2] - feather, b[3] - feather))
    return np.asarray(m.filter(ImageFilter.GaussianBlur(feather)), np.float32)[..., None] / 255


def video(a):
    folder, mp3, text, out = a[0], a[1], a[2], a[3]
    W, H = map(int, opt(a, "--크기", "1920x1080").split("x"))
    if os.path.exists(text):
        text = open(text, encoding="utf-8").read()
    bx = json.load(open(os.path.join(folder, "상자.json")))
    base = Image.open(os.path.join(folder, "기본.png")).convert("RGB")
    img = {n: np.asarray(Image.open(os.path.join(folder, n + ".png")).convert("RGB"), np.float32) for n in SHAPES + ["눈감음"]}
    B = np.asarray(base, np.float32)
    mm, em = soft_mask(base.size, bx["입"], 10), soft_mask(base.size, bx["눈"], 8)
    tmp = out + ".tmp.wav"
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", mp3, "-ac", "1", "-ar", "16000", tmp], check=True)
    import wave
    w = wave.open(tmp)
    dur = w.getnframes() / w.getframerate()
    N = int(dur * FPS) + 1
    tf = opt(a, "--시각")
    shapes = plan_shapes(tmp, text, N, json.load(open(tf, encoding="utf-8")) if tf else None)
    # 2장에 걸쳐 섞기: 입 칸 = 현재 모양 0.6 + 앞 모양 0.4 (바뀌는 순간만)
    bl_w = {}
    for s in np.arange(1.0, dur, 3.1):
        f0 = int(s * FPS)
        bl_w.update({f0: 1.0, f0 + 1: 1.0, f0 + 2: 1.0})   # 섞으면 뜬 눈·감은 눈이 겹쳐 유령처럼 보임 → 통째로 3장
    ff = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                           "-i", "-", "-i", mp3, "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-c:a", "aac", "-b:a", "192k",
                           "-shortest", out], stdin=subprocess.PIPE)
    sw, sh = base.size
    prev = "다문입"
    for f in range(N):
        cur = shapes[f]
        mouth = img[cur] if cur == prev else img[cur] * 0.6 + img[prev] * 0.4
        prev = cur
        fr = B * (1 - mm) + mouth * mm
        if f in bl_w:
            fr = fr * (1 - em * bl_w[f]) + img["눈감음"] * em * bl_w[f]
        im = Image.fromarray(np.clip(fr, 0, 255).astype(np.uint8))
        # 카메라: 천천히 다가감(1.0→1.05) + 살짝 흔들림
        t = f / FPS
        z = 1.0 + 0.05 * f / max(N - 1, 1)
        cw, ch = sw / z, sh / z
        cx = sw / 2 + 4 * np.sin(t * 0.7)
        cy = sh / 2 - 6 * (z - 1) * 10 + 3 * np.sin(t * 0.9)
        im = im.rotate(0.35 * np.sin(t * 0.6), resample=Image.BICUBIC, center=(sw / 2, sh * 0.45))
        im = im.crop((int(cx - cw / 2), int(cy - ch / 2), int(cx + cw / 2), int(cy + ch / 2))).resize((W, H), Image.LANCZOS)
        ff.stdin.write(im.tobytes())
    ff.stdin.close()
    ff.wait()
    os.remove(tmp)
    print("만듦", out, f"{dur:.1f}초", "입 모양:", {s: shapes.count(s) for s in SHAPES})


if __name__ == "__main__":
    cmd, rest = sys.argv[1], sys.argv[2:]
    {"준비": prepare, "영상": video}[cmd](rest)
