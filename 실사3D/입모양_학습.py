"""아나운서 발음 연습 — 한국어로 말하는 실제 영상에서 '발음별 입술 움직임 표'를 배움 (숫자만 씀, 영상 속 얼굴은 결과물에 안 들어감)
쓸 영상: CC BY·CC0·공공누리 1유형·직접 찍은 영상만 (실사3D.md '아나운서 발음 연습')

1) 입술 움직임 뽑기 (Ditto 실행 환경, 1분에 약 3~6분)
   models/ditto/.venv/bin/python 실사3D/입모양_학습.py 추출 <영상.mp4> <움직임.npz> [--시작 0] [--길이 300] [--자르기 w:h:x:y]
   (얼굴이 작으면 --자르기 로 얼굴 둘레만: 화면 높이의 절반 넘게 얼굴이 차지하면 잘 찾음)
   → 1초 25장마다 Ditto 움직임 분석기(motion_extractor)의 표정 값(exp, 21점×3) — 얼굴 위치는 MediaPipe 로 처음 찾고 그 뒤는 따라감
2) 음절 시각 (받아쓰기 모델, 대본 없이 들리는 대로)
   .sd_venv/bin/python -X utf8 실사3D/발음시각.py <영상.mp4> - <받아쓰기.json>
3) 표 만들기
   .supertonic_venv/bin/python 실사3D/입모양_학습.py 표 <움직임.npz> <받아쓰기.json> <입모양표.json> [--이름 출처]
   → 모음 묶음(아 어 오 우 으 이 에)·입 닫음(ㅁㅂㅍ) 마다 입술 6점(6·12·14·17·19·20)의 평균 움직임 (그 사람의 쉬는 입 대비)
   여러 영상의 표는 `표` 에 npz·json 을 여러 쌍 주면 합쳐서 평균
4) 쓰기: ditto_말하기.py --입모양표 <입모양표.json>
"""
import json
import os
import subprocess
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
LIP = [6, 12, 14, 17, 19, 20]
FPS = 25


def opt(a, k, d):
    return a[a.index(k) + 1] if k in a else d


def extract(a):
    import importlib.util
    video, out = a[0], a[1]
    t0, dur = float(opt(a, "--시작", 0)), float(opt(a, "--길이", 300))
    crop = opt(a, "--자르기", "")          # 얼굴이 작은 영상: 얼굴 둘레만 잘라 키움 (w:h:x:y, ffmpeg crop)
    spec = importlib.util.spec_from_file_location("ditto_말하기", os.path.join(HERE, "ditto_말하기.py"))
    D = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(D)            # MediaPipe 얼굴 찾기·cpu 바꿔 끼우기가 여기서 적용됨
    ck = os.path.join(D.DITTO, "checkpoints")
    cfgs = D.C.parse_cfg(os.path.join(ck, "ditto_cfg", "v0.4_hubert_cfg_pytorch.pkl"), os.path.join(ck, "ditto_pytorch"))
    s2i = D.S.Source2Info(**cfgs[0])
    W = 640
    probe = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
                            "-of", "csv=p=0", video], capture_output=True, text=True).stdout.strip().split(",")
    w0, h0 = int(probe[0]), int(probe[1])
    if crop:
        w0, h0 = int(crop.split(":")[0]), int(crop.split(":")[1])
    H = int(round(h0 * W / w0 / 2) * 2)
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", str(t0), "-t", str(dur), "-i", video, "-vf", (f"crop={crop}," if crop else "") + f"fps={FPS},scale={W}:{H}",
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    exps, poses, ok = [], [], []
    last = None
    n = 0
    while True:
        buf = p.stdout.read(W * H * 3)
        if len(buf) < W * H * 3:
            break
        img = np.frombuffer(buf, np.uint8).reshape(H, W, 3).copy()
        try:
            img_crop, M_c2o, lmk = s2i._crop(img, last_lmk=last)
            kp = s2i._get_kp_info(s2i._img_crop_to_bchw256(img_crop))
            exps.append(np.asarray(kp["exp"]).reshape(21, 3))
            poses.append([float(np.asarray(kp[k]).reshape(-1).argmax()) for k in ("pitch", "yaw", "roll")])
            ok.append(1)
            last = lmk
        except Exception:
            exps.append(np.zeros((21, 3), np.float32))
            poses.append([0, 0, 0])
            ok.append(0)
            last = None                      # 얼굴을 놓치면 다음 장에서 다시 찾음
        n += 1
        if n % 250 == 0:
            print(f"  {n}장 ({n / FPS:.0f}초), 얼굴 찾음 {sum(ok)}", flush=True)
    np.savez_compressed(out, exp=np.array(exps, np.float32), pose=np.array(poses, np.float32), ok=np.array(ok, np.int8), t0=t0)
    print("움직임", n, "장 →", out)


VOWEL = {0: "아", 2: "아", 9: "아", 4: "어", 6: "어", 14: "어", 8: "오", 12: "오", 10: "오", 11: "오",
         13: "우", 17: "우", 15: "우", 16: "우", 18: "으", 19: "으", 20: "이", 1: "에", 3: "에", 5: "에", 7: "에"}
CLOSE_CHO = (6, 7, 8, 17)        # ㅁ ㅂ ㅃ ㅍ
CLOSE_JONG = (16, 17)            # 받침 ㅁ ㅂ


def table(a):
    pairs, name, out = [], opt(a, "--이름", ""), None
    files = [x for x in a if not x.startswith("--") and x != name]
    out = files[-1]
    for i in range(0, len(files) - 1, 2):
        pairs.append((files[i], files[i + 1]))
    acc = {}
    for npz, js in pairs:
        z = np.load(npz)
        exp, ok, t0 = z["exp"], z["ok"].astype(bool), float(z["t0"])
        heard = sorted(json.load(open(js, encoding="utf-8")), key=lambda h: h[1])
        # 받아쓰기는 글자를 한 칸(0.02초)에만 찍음 → 음절은 다음 음절이 시작될 때까지 (최대 0.35초)
        heard = [[c, s_, min(heard[i + 1][1] if i + 1 < len(heard) else s_ + 0.25, s_ + 0.35)] for i, (c, s_, e_) in enumerate(heard)]
        n = len(exp)
        cls = [None] * n
        for ch, s, e in heard:
            v = ord(ch) - 0xAC00
            if not (0 <= v < 11172):
                continue
            cho, jung, jong = v // 588, (v % 588) // 28, v % 28
            f0, f1 = int((s - t0) * FPS), int(round((e - t0) * FPS))
            fr = [f for f in range(f0, max(f1, f0 + 1)) if 0 <= f < n]
            for k, f in enumerate(fr):
                t = k / max(len(fr), 1)
                if (cho in CLOSE_CHO and t < 0.25) or (jong in CLOSE_JONG and t > 0.8):
                    cls[f] = "닫음"
                elif 0.3 <= t <= 0.8:
                    cls[f] = VOWEL.get(jung)
        lips = exp[:, LIP, :]
        rest_idx = [f for f in range(n) if ok[f] and cls[f] is None]
        rest = np.median(lips[rest_idx], 0) if len(rest_idx) > 20 else np.median(lips[ok], 0)
        for f in range(n):
            if ok[f] and cls[f]:
                acc.setdefault(cls[f], []).append(lips[f] - rest)
    res = {"lip_index": LIP, "source": name, "classes": {}}
    for c, arr in acc.items():
        arr = np.array(arr)
        res["classes"][c] = {"mean": np.mean(arr, 0).round(5).tolist(), "n": len(arr)}
    json.dump(res, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("입모양표:", {c: v["n"] for c, v in res["classes"].items()}, "→", out)


if __name__ == "__main__":
    {"추출": extract, "표": table}[sys.argv[1]](sys.argv[2:])
