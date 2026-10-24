"""나레이션 겹침 검사 — 성우가 같은 소리를 두 번 읽은 곳('닿을 것만만', '미역국국')을 찾음 (.sd_venv 에서 실행)
python 나레이션_겹침검사.py <영상.mp4> <대본.txt 또는 연재 회차 .py> [결과.txt]
  - Whisper 는 '것만만'을 '것만'으로 고쳐 적어서 못 찾음 → 소리를 글자 그대로 적는 wav2vec2(CTC) 한국어 모델로 받아 적음
    (kresnik/wav2vec2-large-xlsr-korean, Apache 2.0, 처음 한 번 약 1.2GB 받음)
  - 소리를 쉼에서 15초 안쪽 조각으로 나눠 받아 적고, 같은 글자(1~3자)가 연달아 두 번 나오는데 대본에는 그런 곳이 없으면 겹침으로 알림
  - 결과: '분:초 [겹친 글자] | 받아 적은 글' 줄. 찾은 문장은 tts_cache 에서 지우고 다시 만들면 새로 녹음됨 (Supertonic 은 매번 조금씩 다르게 읽음)
  - 받아 적기는 발음대로라 '닿을→다을' 같은 차이는 무시하고 겹침만 봄
  - 대본의 흉내말(무럭무럭·불쑥불쑥)이 발음대로 적혀('물역물역') 걸리기도 함 → 그 줄은 대본과 맞춰 보고 넘김"""
import importlib.util
import json
import os
import re
import subprocess
import sys

import numpy as np

SR = 16000
MODEL = "kresnik/wav2vec2-large-xlsr-korean"


def script_text(path):
    if path.endswith(".py"):
        spec = importlib.util.spec_from_file_location("ep", path)
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        return m.STORY
    return open(path, encoding="utf-8").read()


def chunks(a):
    """쉼(작은 소리 0.3초 이상)에서 끊어 15초 안쪽 조각 [(시작, 끝)]"""
    fr = int(0.02 * SR)
    n = len(a) // fr
    rms = np.sqrt((a[:n * fr].reshape(n, fr) ** 2).mean(1))
    quiet = rms < max(1e-4, np.percentile(rms, 95) * 0.03)
    out, start, k = [], 0, 0
    while k < n:
        if quiet[k]:
            j = k
            while j < n and quiet[j]:
                j += 1
            if j - k >= 15 and (k - start) * 0.02 >= 4:     # 0.3초 이상 쉼, 조각은 4초 이상
                out.append((start * 0.02, k * 0.02))
                start = j
            elif (k - start) * 0.02 >= 15:
                out.append((start * 0.02, k * 0.02))
                start = k
            k = j
        else:
            k += 1
    if n - start > 10:
        out.append((start * 0.02, n * 0.02))
    return out


def main():
    video, script = sys.argv[1], sys.argv[2]
    ref = re.sub(r"[^가-힣]", "", script_text(script))
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", video, "-vn", "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    a = np.frombuffer(raw, np.float32)
    import torch
    from transformers import AutoModelForCTC, AutoProcessor
    torch.set_num_threads(max(1, (os.cpu_count() or 4)))
    p = AutoProcessor.from_pretrained(MODEL)
    m = AutoModelForCTC.from_pretrained(MODEL).eval()
    lines = []
    for t0, t1 in chunks(a):
        x = a[int(max(0, t0 - 0.15) * SR):int((t1 + 0.15) * SR)]
        with torch.no_grad():
            text = p.batch_decode(m(**p(x, sampling_rate=SR, return_tensors="pt")).logits.argmax(-1))[0]
        h = re.sub(r"[^가-힣]", "", text)
        hits = sorted({h[i:i + n] * 2 for n in (1, 2, 3) for i in range(len(h) - 2 * n + 1)
                       if h[i:i + n] == h[i + n:i + 2 * n] and h[i:i + n] * 2 not in ref})
        if hits:
            lines.append(f"{int(t0 // 60)}:{int(t0 % 60):02d} {hits} | {text}")
    msg = "\n".join(lines) if lines else "겹침 없음"
    print(msg)
    if len(sys.argv) > 3:
        open(sys.argv[3], "w", encoding="utf-8").write(msg + "\n")


if __name__ == "__main__":
    main()
