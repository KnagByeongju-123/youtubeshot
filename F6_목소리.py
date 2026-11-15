"""목소리 색깔을 입힌 성우 F7·M7·M6·F8~F10·M8~M10 — 공개 한국어 녹음 자료의 목소리 색깔을 Supertonic 바탕 성우에 입힘
  · F8·F9·F10 / M8·M9·M10 (사용자 결정 2026-11-15, 나레이션 기본 = 남 M10·여 F8):
    Zeroth-Korean(CC BY 4.0 → 수익 영상 가능, 설명란에 출처 표시) 사람 번호 105·121·147 → F1 바탕, 104·149·118 → M1 바탕
    출처 문구: "목소리: Zeroth-Korean 음성 자료(Lucas Jo·Wonkyum Lee, CC BY 4.0)와 OpenVoice V2(MIT)로 만든 AI 성우"
  · KSS: 전문 여자 성우가 TTS 용으로 녹음해 공개한 자료 (Kyubyong Park, CC BY-NC-SA 4.0 → 비상업용만)
  · OpenVoice V2 목소리 색깔 바꾸기(tone color converter, MyShell, MIT)
  · F7 = F1 + KSS, M7 = M1 + KSS (비상업용만. 예전 이름 F6 → F7, 사용자 결정 2026-11-15)
  · M6 = 원래 M1 목소리 그대로 (상업 사용 가능)
  · 순서: Supertonic 바탕 성우(F7=F1, M7=M1)로 읽음 → OpenVoice 로 목소리 색깔만 KSS 쪽으로 바꿈 (말·속도·억양은 그대로)

  .sd_venv/bin/python -X utf8 F6_목소리.py 준비          # 한 번: KSS·Zeroth·OpenVoice 받기 + 목소리 특징(F6_se.pth) 만들기 (약 2분)
  .sd_venv/bin/python -X utf8 F6_목소리.py 바탕 F3                # F7 바탕 성우 바꾸기 (models/openvoice/F6.json, 기본 F1)
  .sd_venv/bin/python -X utf8 F6_목소리.py 바탕 M7 M2             # M7 바탕 성우 바꾸기 (기본 M1)
  .sd_venv/bin/python -X utf8 F6_목소리.py 바꾸기 <들어감.wav> <나옴.wav>
  .sd_venv/bin/python -X utf8 F6_목소리.py --worker       # supertonic_local_worker 가 색깔 입힌 성우일 때 띄움 (한 줄 JSON 주고받기)

※ KSS 가 비상업용이라 F7·M7 로 만든 소리는 수익 나는 유튜브 영상에 쓰지 않음 (혼자 듣기·연습용)
"""
import json
import os
import subprocess
import sys
import types

HERE = os.path.dirname(os.path.abspath(__file__))
OV = os.path.join(HERE, "models", "openvoice")
KSS = os.path.join(HERE, "models", "kss")
SE_PATH = os.path.join(OV, "F6_se.pth")
F6_BASE = "F1"          # 바탕으로 읽을 Supertonic 성우 (샘플 비교로 고름)
TAU = 0.3
HF = "https://huggingface.co"
SAMPLE_TEXTS = [
    "오늘은 조금 특별한 책 한 권을 함께 읽어 보려고 합니다.",
    "아침 햇살이 창문으로 들어오면, 저는 늘 커피 한 잔을 내립니다.",
    "그때 저는 아무것도 할 수 없을 것 같은 마음이었어요.",
    "작은 습관 하나가 삶을 조금씩 바꾸어 놓았습니다.",
    "이 문장을 읽고, 한참 동안 책장을 넘기지 못했습니다.",
    "여러분은 지금 어떤 시간을 견디고 계신가요.",
    "바람이 불어도 나무는 뿌리를 놓지 않습니다.",
    "그래서 저는 이 이야기를 꼭 들려드리고 싶었어요.",
]


def _get(url, path):
    if not os.path.exists(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        subprocess.run(["curl", "-sSL", "--fail", "-o", path + ".part", url], check=True)
        os.replace(path + ".part", path)


def download():
    _get(f"{HF}/myshell-ai/OpenVoiceV2/resolve/main/converter/config.json", os.path.join(OV, "config.json"))
    _get(f"{HF}/myshell-ai/OpenVoiceV2/resolve/main/converter/checkpoint.pth", os.path.join(OV, "checkpoint.pth"))
    if not os.path.isdir(os.path.join(OV, "openvoice")):
        tmp = os.path.join(OV, "_src")
        subprocess.run(["git", "clone", "--depth", "1", "https://github.com/myshell-ai/OpenVoice.git", tmp], check=True)
        import shutil
        shutil.copytree(os.path.join(tmp, "openvoice"), os.path.join(OV, "openvoice"))
        shutil.copy(os.path.join(tmp, "LICENSE"), os.path.join(OV, "LICENSE"))
        shutil.rmtree(tmp, ignore_errors=True)
    _get(f"{HF}/datasets/Bingsu/KSS_Dataset/resolve/main/data/train-00000-of-00007.parquet",
         os.path.join(KSS, "train0.parquet"))


def converter():
    """OpenVoice 목소리 색깔 바꾸개 (글자 읽기 부분은 쓰지 않으니 빈 모듈로)"""
    sys.path.insert(0, OV)
    import openvoice                                         # noqa: F401
    txt = types.ModuleType("openvoice.text")
    txt.text_to_sequence = None
    sys.modules["openvoice.text"] = txt
    from openvoice.api import ToneColorConverter
    c = ToneColorConverter(os.path.join(OV, "config.json"), device="cpu")
    c.load_ckpt(os.path.join(OV, "checkpoint.pth"))
    return c


def kss_clips(n=80):
    """KSS 녹음 중 3~8초짜리 n개를 wav 로 꺼냄"""
    out = os.path.join(KSS, "clips")
    have = sorted(f for f in os.listdir(out) if f.endswith(".wav")) if os.path.isdir(out) else []
    if len(have) >= n:
        return [os.path.join(out, f) for f in have[:n]]
    os.makedirs(out, exist_ok=True)
    import pyarrow.parquet as pq
    t = pq.read_table(os.path.join(KSS, "train0.parquet"), columns=["audio", "duration"]).to_pylist()
    picked = [r for r in t if 3.0 <= r["duration"] <= 8.0][:: max(1, len([r for r in t if 3.0 <= r["duration"] <= 8.0]) // n)][:n]
    paths = []
    for i, r in enumerate(picked):
        p = os.path.join(out, f"kss_{i:03d}.wav")
        with open(p, "wb") as f:
            f.write(r["audio"]["bytes"])
        paths.append(p)
    return paths


def base_clips(base):
    """바탕 성우(Supertonic)로 같은 문장들을 읽혀 바탕 목소리 특징을 잼"""
    out = os.path.join(OV, f"base_{base}")
    os.makedirs(out, exist_ok=True)
    py = os.path.join(HERE, ".supertonic_venv", "bin", "python")
    w = subprocess.Popen([py, "-X", "utf8", "-u", os.path.join(HERE, "supertonic_local_worker.py"),
                          "--model-dir", os.path.join(HERE, "supertonic_assets")],
                         stdin=subprocess.PIPE, stdout=subprocess.PIPE, encoding="utf-8", bufsize=1,
                         env=dict(os.environ, PYTHONUTF8="1", F6_NO_WORKER="1"))
    json.loads(w.stdout.readline())
    paths = []
    for i, t in enumerate(SAMPLE_TEXTS):
        p = os.path.join(out, f"{i:02d}.wav")
        if not os.path.exists(p):
            w.stdin.write(json.dumps({"text": t, "voice": base, "out": p}, ensure_ascii=False) + "\n")
            r = json.loads(w.stdout.readline())
            if not r.get("ok"):
                raise RuntimeError(r)
        paths.append(p)
    w.stdin.close()
    w.wait()
    return paths


ZEROTH_SPEAKERS = (105, 121, 147, 104, 149, 118)     # F8 F9 F10 M8 M9 M10


def prepare(bases=("F1", "F2", "F3", "F4", "F5", "M1")):
    import torch
    download()
    c = converter()
    se = {"tgt": c.extract_se(kss_clips())}
    for b in bases:
        se[b] = c.extract_se(base_clips(b))
    old = torch.load(SE_PATH) if os.path.exists(SE_PATH) else {}
    old.update(se)
    torch.save(old, SE_PATH)
    zeroth_se(ZEROTH_SPEAKERS)
    print("목소리 특징 저장:", SE_PATH, sorted(torch.load(SE_PATH)))


ZEROTH = os.path.join(HERE, "models", "zeroth")


def zeroth_se(speakers):
    """Zeroth-Korean(CC BY 4.0, 상업 사용 가능·출처 표시) 시험 묶음에서 사람 번호별 목소리 특징 → 'zeroth_<번호>'"""
    import io
    import pyarrow.parquet as pq
    import soundfile
    import torch
    _get(f"{HF}/datasets/kresnik/zeroth_korean/resolve/main/data/test-00000-of-00001.parquet",
         os.path.join(ZEROTH, "k_test.parquet"))
    rows = pq.read_table(os.path.join(ZEROTH, "k_test.parquet"), columns=["speaker_id", "audio"]).to_pylist()
    c = converter()
    se = torch.load(SE_PATH) if os.path.exists(SE_PATH) else {}
    for spk in speakers:
        d = os.path.join(ZEROTH, "clips", str(spk))
        os.makedirs(d, exist_ok=True)
        paths = []
        for i, r in enumerate(x for x in rows if x["speaker_id"] == int(spk)):
            p = os.path.join(d, f"{i:03d}.wav")
            a, sr = soundfile.read(io.BytesIO(r["audio"]["bytes"]), dtype="float32")
            soundfile.write(p, a, sr)
            paths.append(p)
        se[f"zeroth_{spk}"] = c.extract_se(paths)
        print("목소리 특징:", spk, len(paths), "개", flush=True)
    torch.save(se, SE_PATH)


class F6:
    def __init__(self):
        import torch
        self.c = converter()
        self.se = torch.load(SE_PATH)

    def convert(self, src, dst, base=None, tau=TAU, tgt="tgt"):
        """바탕 소리 → F6. 크기(소리 세기)·표본 주파수는 바탕 소리와 같게 맞춤"""
        import librosa
        import numpy as np
        import soundfile
        base = base or chosen_base()
        x, sr = soundfile.read(src, dtype="float32")
        a = self.c.convert(src, self.se[base], self.se[tgt], tau=tau)
        a = librosa.resample(a, orig_sr=self.c.hps.data.sampling_rate, target_sr=sr)
        rx, ra = np.sqrt(np.mean(x ** 2)), np.sqrt(np.mean(a ** 2))
        if ra > 1e-6:
            a = a * (rx / ra)
        a = np.clip(a, -0.99, 0.99)
        soundfile.write(dst, a, sr)


BASES = {"F7": "F1", "M7": "M1"}     # KSS 목소리 색깔을 입히는 성우 → 기본 바탕 성우


def _conf():
    try:
        d = json.load(open(os.path.join(OV, "F6.json"), encoding="utf-8"))
    except Exception:
        d = {}
    if "base" in d:                       # 예전 형식 {"base": "F1"}
        d.setdefault("F7", d.pop("base"))
    return {**BASES, **d}


def chosen_base(voice="F7"):
    return _conf()[voice]


def set_base(voice, b):
    d = _conf()
    d[voice] = b
    with open(os.path.join(OV, "F6.json"), "w", encoding="utf-8") as f:
        json.dump(d, f)
    print(voice, "바탕 성우 =", b)


def worker():
    """한 줄 JSON 주고받기. 모델이 찍는 글은 stderr 로 돌려 답장 줄을 깨끗하게"""
    import contextlib
    out = sys.stdout

    def say(d):
        out.write(json.dumps(d, ensure_ascii=False) + "\n")
        out.flush()

    with contextlib.redirect_stdout(sys.stderr):
        f6 = F6()
    say({"ok": True, "status": "ready"})
    for line in sys.stdin:
        try:
            r = json.loads(line)
            with contextlib.redirect_stdout(sys.stderr):
                f6.convert(r["src"], r["out"], r.get("base"), float(r.get("tau", TAU)), r.get("tgt", "tgt"))
            say({"ok": True})
        except Exception as e:
            say({"ok": False, "error": f"{type(e).__name__}: {e}"})


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[:1] == ["--worker"]:
        worker()
    elif a[:1] == ["준비"]:
        prepare(*([tuple(a[1:])] if a[1:] else []))
    elif a[:1] == ["바꾸기"] and len(a) >= 3:         # 바꾸기 in out [바탕] [목표: tgt(KSS)·zeroth_104]
        F6().convert(a[1], a[2], a[3] if len(a) > 3 else None, TAU, a[4] if len(a) > 4 else "tgt")
    elif a[:1] == ["제로스"] and len(a) >= 2:
        zeroth_se(a[1:])
    elif a[:1] == ["바탕"] and len(a) in (2, 3):         # 바탕 F3  /  바탕 M6 M2
        set_base(*(a[1].upper(), a[2].upper()) if len(a) == 3 else ("F7", a[1].upper()))
    else:
        print(__doc__)
