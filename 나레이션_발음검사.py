"""나레이션 발음 검사 — 성우가 한국어 대신 영어처럼(외국어 억양으로) 읽은 곳 찾기 (.sd_venv 에서 실행)

  python 나레이션_발음검사.py <영상.mp4> <회차.py> [--기준 0.55] [--결과 <결과.txt>]

- 겹침 검사와 같은 한국어 받아 적기(wav2vec2)로 쉼마다 끊어 받아 적고, 가장 비슷한 대본 문장과 글자가 얼마나 맞는지(0~1) 잼
- 영어처럼 읽힌 곳은 한국어 모델이 엉뚱하게 받아 적어서 맞는 정도가 크게 떨어짐 → 기준보다 낮은 곳을 낮은 순서로 보여 줌
  (짧은 조각·대사·배경음만 있는 곳은 뺌). 결과를 듣고 정말 이상하면 그 문장 녹음 캐시를 지우고 다시 만듦
"""
import difflib
import importlib.util
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
_sp = importlib.util.spec_from_file_location("ov", os.path.join(HERE, "나레이션_겹침검사.py"))
OV = importlib.util.module_from_spec(_sp)
_sp.loader.exec_module(OV)


def main(a):
    if len(a) < 2:
        print(__doc__)
        return 2
    video, script = a[0], a[1]
    lim = float(a[a.index("--기준") + 1]) if "--기준" in a else 0.55
    import numpy as np
    import torch
    from transformers import AutoModelForCTC, AutoProcessor
    pars = OV.script_paragraphs(script)
    sents = [OV.hangul(s) for p in pars for s in OV.sentences(p)]
    full = "".join(sents)
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", video, "-vn", "-ac", "1", "-ar", str(OV.SR), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    x_all = np.frombuffer(raw, np.float32)
    torch.set_num_threads(max(1, os.cpu_count() or 4))
    p = AutoProcessor.from_pretrained(OV.MODEL)
    m = AutoModelForCTC.from_pretrained(OV.MODEL).eval()
    rows = []
    for t0, t1 in OV.chunks(x_all):
        x = x_all[int(max(0, t0 - 0.1) * OV.SR):int((t1 + 0.1) * OV.SR)]
        with torch.no_grad():
            ids = m(**p(x, sampling_rate=OV.SR, return_tensors="pt")).logits.argmax(-1)
        h = OV.hangul(p.batch_decode(ids)[0])
        if len(h) < 6:
            continue
        # 대본 전체에서 이 조각과 가장 잘 맞는 같은 길이 구간을 찾아 맞는 정도를 잼
        best, where = 0.0, ""
        L = len(h)
        for i in range(0, max(1, len(full) - L + 1), 2):
            seg = full[i:i + L]
            r = difflib.SequenceMatcher(None, h, seg, autojunk=False).ratio()
            if r > best:
                best, where = r, seg
        rows.append((best, t0, h, where))
    bad = sorted([r for r in rows if r[0] < lim])
    lines = [f"{int(t // 60)}:{int(t % 60):02d} 맞음 {r:.2f} | 들림: {h} | 대본: {w}" for r, t, h, w in bad]
    msg = "\n".join(lines) if lines else f"발음이 크게 어긋난 곳 없음 (조각 {len(rows)}개, 기준 {lim})"
    print(f"조각 {len(rows)}개 중 기준({lim}) 미만 {len(bad)}개\n" + msg)
    if "--결과" in a:
        open(a[a.index("--결과") + 1], "w", encoding="utf-8").write(msg + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
