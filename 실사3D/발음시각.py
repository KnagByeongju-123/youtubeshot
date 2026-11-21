"""나레이션에서 대본 음절마다 실제 발음 시각 찾기 (입 모양 타이밍용)
한국어 받아쓰기 모델(wav2vec2 CTC, 나레이션_겹침검사.py 와 같은 kresnik/wav2vec2-large-xlsr-korean)이 글자를 처음 내는 칸(약 0.02초)을 그 글자의 시각으로 보고,
받아 적은 글자와 대본 음절을 맞춰(difflib) 대본 음절마다 [음절, 시작초, 끝초] 를 적음. 못 맞춘 음절은 앞뒤 사이를 고르게 나눔.
사용: .sd_venv/bin/python -X utf8 실사3D/발음시각.py <나레이션.mp3|wav> <대본.txt 또는 "글"> <결과.json>
→ 사진아나운서.py 영상 --시각 <결과.json>, ditto_말하기.py --시각 <결과.json>
"""
import difflib
import importlib.util
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")


def main():
    audio, text, out = sys.argv[1:4]
    if os.path.exists(text):
        text = open(text, encoding="utf-8").read()
    spec = importlib.util.spec_from_file_location("겹침", os.path.join(ROOT, "나레이션_겹침검사.py"))
    G = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(G)
    import numpy as np
    import torch
    from transformers import AutoModelForCTC, AutoProcessor
    SR = G.SR
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", audio, "-vn", "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    a = np.frombuffer(raw, np.float32)
    dur = len(a) / SR
    torch.set_num_threads(max(1, os.cpu_count() or 4))
    p = AutoProcessor.from_pretrained(G.MODEL)
    m = AutoModelForCTC.from_pretrained(G.MODEL).eval()
    blank = p.tokenizer.pad_token_id
    heard = []                                      # (글자, 시작초, 끝초)
    for t0, t1 in G.chunks(a):
        off = max(0, t0 - 0.15)
        x = a[int(off * SR):int((t1 + 0.15) * SR)]
        with torch.no_grad():
            ids = m(**p(x, sampling_rate=SR, return_tensors="pt")).logits.argmax(-1)[0].tolist()
        step = len(x) / SR / max(1, len(ids))
        k = 0
        while k < len(ids):
            tid = ids[k]
            j = k
            while j + 1 < len(ids) and ids[j + 1] == tid:
                j += 1
            if tid != blank:
                ch = p.tokenizer.convert_ids_to_tokens(tid) or ""
                if "가" <= ch <= "힣" and len(ch) == 1:
                    heard.append([ch, off + k * step, off + (j + 1) * step])
            k = j + 1
    heard.sort(key=lambda h: h[1])
    syl = [c for c in text if "가" <= c <= "힣"]
    hs = "".join(h[0] for h in heard)
    st = [None] * len(syl)
    sm = difflib.SequenceMatcher(None, "".join(syl), hs, autojunk=False)
    for b in sm.get_matching_blocks():
        for i in range(b.size):
            st[b.a + i] = heard[b.b + i][1]
    # 못 맞춘 음절: 앞뒤 맞춘 시각 사이를 고르게
    known = [i for i, v in enumerate(st) if v is not None]
    if not known:
        raise SystemExit("받아 적은 글자와 대본이 하나도 안 맞음")
    for i in range(len(syl)):
        if st[i] is None:
            lo = max([k for k in known if k < i], default=None)
            hi = min([k for k in known if k > i], default=None)
            if lo is None:
                st[i] = max(0.0, st[hi] - 0.12 * (hi - i))
            elif hi is None:
                st[i] = min(dur, st[lo] + 0.12 * (i - lo))
            else:
                st[i] = st[lo] + (st[hi] - st[lo]) * (i - lo) / (hi - lo)
    res = []
    for i, c in enumerate(syl):
        nxt = st[i + 1] if i + 1 < len(syl) else st[i] + 0.25
        res.append([c, round(st[i], 3), round(min(nxt, st[i] + 0.35), 3)])   # 한 음절 최대 0.35초 (뒤는 쉼)
    json.dump(res, open(out, "w", encoding="utf-8"), ensure_ascii=False)
    print(f"음절 {len(syl)}개 중 {len(known)}개를 받아쓰기로 맞춤 →", out)


if __name__ == "__main__":
    main()
