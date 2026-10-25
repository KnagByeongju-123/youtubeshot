"""나레이션 다시 녹음 — 영상을 듣다가 이상한 곳의 시각만 적으면 그 자리 문장을 찾아 녹음 캐시를 지움 (.sd_venv 에서 실행)

  python 나레이션_다시녹음.py <영상.mp4> <회차.py> <프로젝트.json> 1:00 1:19 1:25 ... [--보기만]

- 시각마다 앞뒤 3초를 받아 적기(wav2vec2) → 대본에서 그 소리와 가장 잘 맞는 문장(1~2개)을 고름
- 그 문장·문단의 녹음 캐시를 지움(나레이션_겹침검사.py --지우기 와 같은 방법) → render_project 다시 돌리면
  장면별 만들기라서 그 문장이 든 장면만 새로 녹음·새로 만들고 나머지는 그대로 씀
- 성우(Supertonic)는 매번 조금씩 다르게 읽으므로 다시 녹음하면 대개 고쳐짐. 그래도 이상하면 같은 시각으로 한 번 더
- 사용자 결정(2026-10-25): 나레이션 손보기는 영상을 다 합친 뒤 한 번에 (사용자가 들어 보고 시각 목록을 줌)
"""
import difflib
import importlib.util
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
_sp = importlib.util.spec_from_file_location("ov", os.path.join(HERE, "나레이션_겹침검사.py"))
OV = importlib.util.module_from_spec(_sp)
_sp.loader.exec_module(OV)


def secs(t):
    p = [float(x) for x in t.replace("분", ":").replace("초", "").split(":")]
    return p[0] * 60 + p[1] if len(p) == 2 else p[0]


def cover(sent, heard):
    """문장 글자 중 들린 소리에 들어 있는 비율 (0~1)"""
    if not sent:
        return 0.0
    bl = difflib.SequenceMatcher(None, sent, heard, autojunk=False).get_matching_blocks()
    return sum(b.size for b in bl) / len(sent)


def main(a):
    if len(a) < 4:
        print(__doc__)
        return 2
    video, script, project = a[0], a[1], a[2]
    times = [secs(x) for x in a[3:] if not x.startswith("--")]
    import numpy as np
    import torch
    from transformers import AutoModelForCTC, AutoProcessor
    sents = [(p, s) for p in OV.script_paragraphs(script) for s in OV.sentences(p)]
    p = AutoProcessor.from_pretrained(OV.MODEL)
    m = AutoModelForCTC.from_pretrained(OV.MODEL).eval()
    items = []
    for t in times:
        raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(max(0, t - 3)), "-t", "6", "-i", video, "-vn", "-ac", "1",
                              "-ar", str(OV.SR), "-f", "f32le", "-"], capture_output=True, check=True).stdout
        x = np.frombuffer(raw, np.float32)
        with torch.no_grad():
            heard = OV.hangul(p.batch_decode(m(**p(x, sampling_rate=OV.SR, return_tensors="pt")).logits.argmax(-1))[0])
        # 가장 잘 맞는 긴 문장(짧은 '정비.' 같은 건 어디에나 맞아 보여서 뺌)을 찾고, 그 앞뒤 문장 중 들린 것만 더함
        sc = [(cover(OV.hangul(s), heard) * min(1.0, len(OV.hangul(s)) / 8), k) for k, (_, s) in enumerate(sents)]
        best = max(sc)[1]
        pick = [k for k in range(best - 2, best + 3) if 0 <= k < len(sents) and (k == best or sc[k][0] >= 0.5)]
        print(f"{int(t // 60)}:{int(t % 60):02d}  들림: {heard}")
        for k in sorted(pick):
            print(f"    → 다시 녹음: {sents[k][1]}")
            items.append({"t": t, "sentence": sents[k][1], "paragraph": sents[k][0]})
    if "--보기만" in a or not items:
        return 0
    tmp = os.path.join(tempfile.gettempdir(), "다시녹음목록.json")
    json.dump(items, open(tmp, "w", encoding="utf-8"), ensure_ascii=False)
    py = os.path.join(HERE, ".supertonic_venv", "bin", "python")
    subprocess.run([py, "-X", "utf8", os.path.join(HERE, "나레이션_겹침검사.py"), "--지우기", tmp, project], check=True)
    print("→ render_project.py 를 다시 돌리면 이 문장이 든 장면만 새로 녹음·새로 만듭니다")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
