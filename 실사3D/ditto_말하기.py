"""Ditto(오픈소스 말하는 얼굴, Apache-2.0) 로 사진 한 장 + 나레이션 → 입·얼굴이 자연스럽게 움직이는 영상 (그래픽카드 없이 CPU)

수익 영상용으로 고친 점 (Ditto 코드는 그대로 두고 이 파일에서 바꿔 끼움):
  - 얼굴 찾기 InsightFace(det_10g·2d106det, 상업 금지)를 **받지도 쓰지도 않음** →
    Ditto 에 들어 있는 MediaPipe 얼굴 점(face_landmarker.task, Apache-2.0) 478개 중 68개를 골라 첫 얼굴 위치로 씀
  - 설정의 device 를 모두 cpu 로
준비(한 번): bash 실사3D/ditto_준비.sh  → models/ditto (코드·.venv·checkpoints)
사용: models/ditto/.venv/bin/python 실사3D/ditto_말하기.py <사진.png> <나레이션.wav|mp3> <결과.mp4> [--대본 <대본.txt 또는 "글">] [--시각 <발음시각.json>] [--입모양표 <표.json>] [--단계 50] [--감정 4]
  --대본: 주면 한국어 입 모양 보정(아래 3번). 사진은 입을 다문 옅은 미소여야 함
  --입모양표: 입모양_학습.py 로 배운 표(--시각 필요). 아래 3번의 손으로 정한 배율 대신 실제 한국어 화자에게서 배운 배율 + 0.2초 앞당김
  --단계: 움직임 만들기 단계 수(기본 50, 줄이면 빠르지만 거칠어짐) / --감정: Ditto 감정 번호(기본 4 = 보통)
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DITTO = os.path.join(HERE, "..", "models", "ditto")
sys.path.insert(0, DITTO)

import numpy as np  # noqa: E402

import core.atomic_components.cfg as C  # noqa: E402
import core.atomic_components.source2info as S  # noqa: E402

# 1) 모든 device → cpu
_orig_load = C.load_pkl


def _cpu(o):
    if isinstance(o, dict):
        return {k: ("cpu" if k == "device" else _cpu(v)) for k, v in o.items()}
    if isinstance(o, list):
        return [_cpu(x) for x in o]
    return o


C.load_pkl = lambda p: _cpu(_orig_load(p))

# 움직임 모델(LMDM)은 설정의 device 를 안 받고 기본값 'cuda' 를 씀 → cpu 로 고정
from core.models.modules import LMDM as _LMDM  # noqa: E402  (모듈이 아니라 클래스)
_orig_lmdm_init = _LMDM.__init__


def _lmdm_init(self, *a, **k):
    k["device"] = "cpu"
    _orig_lmdm_init(self, *a, **k)


_LMDM.__init__ = _lmdm_init


# 2) InsightFace 대신 MediaPipe 478점 → 68점 (dlib 68점 순서에 맞춘 널리 쓰는 대응표)
class _NoInsightFace:
    def __init__(self, *a, **k):
        pass


S.InsightFaceDet = _NoInsightFace
S.Landmark106 = _NoInsightFace
MP68 = [162, 234, 93, 58, 172, 136, 149, 148, 152, 377, 378, 365, 397, 288, 323, 454, 389,
        71, 63, 105, 66, 107, 336, 296, 334, 293, 301,
        168, 197, 5, 4, 75, 97, 2, 326, 305,
        33, 160, 158, 133, 153, 144, 362, 385, 387, 263, 373, 380,
        61, 39, 37, 0, 267, 269, 291, 405, 314, 17, 84, 181, 78, 82, 13, 312, 308, 317, 14, 87]
_orig_crop = S.Source2Info._crop


def _find_face(self, img):
    """MediaPipe 얼굴 점 478개(픽셀). 반신·전신처럼 얼굴이 작으면 전체에서 못 찾음 →
    위쪽 가운데·격자 칸을 잘라 얼굴을 크게 보이게 해서 다시 찾고, 좌표를 원래 사진으로 되돌림 (사용자 요청 2026-11-21: 반신 리포터)"""
    H, W = img.shape[:2]
    wins = [(0, 0, W, H), (W // 4, 0, W * 3 // 4, H * 3 // 5), (W // 3, 0, W * 2 // 3, H * 2 // 5)]
    for gy in range(3):
        for gx in range(4):
            wins.append((gx * W // 5, gy * H // 4, gx * W // 5 + W * 2 // 5, gy * H // 4 + H // 2))
    for x0, y0, x1, y1 in wins:
        sub = np.ascontiguousarray(img[y0:y1, x0:x1])
        l478 = self.landmark478(sub)
        if l478 is None or len(l478) == 0 or l478.size == 0:
            continue
        pts = l478[0][:, :2].copy()
        if pts.max() <= 1.5:                      # 0~1 비율 → 픽셀
            pts[:, 0] *= sub.shape[1]
            pts[:, 1] *= sub.shape[0]
        pts[:, 0] += x0
        pts[:, 1] += y0
        return pts
    raise RuntimeError("사진에서 얼굴을 못 찾음 (MediaPipe, 잘라서도 못 찾음)")


def _crop(self, img, last_lmk=None, **kw):
    if last_lmk is None:
        last_lmk = _find_face(self, img)[MP68]
    return _orig_crop(self, img, last_lmk=last_lmk, **kw)


S.Source2Info._crop = _crop

# 3) 한국어 입 모양 보정 (--대본 을 주면): Ditto 의 소리 해석은 주로 중국어·영어로 배워 한국어 입 모양이 약함 →
#    사진아나운서.py 와 같은 음절 분석(소리 크기 + 모음)으로 프레임마다 입술 키포인트(6·12·14·17·19·20)의 움직임을
#    아=1.5배·오=1.3배·이=1.05배로 키우고, 쉼·ㅁ·ㅂ 은 원래 사진(입 다문 얼굴) 쪽으로 당겨 입을 닫음.
#    → 원래 사진은 입을 다문 옅은 미소여야 함 (이를 드러낸 웃음이면 닫을 수 없음)
import core.atomic_components.motion_stitch as MS  # noqa: E402
LIP = [6, 12, 14, 17, 19, 20]
KO = {"plan": None, "i": 0}
GAIN = {"아": 1.5, "오": 1.3, "이": 1.05, "다문입": 0.25}
_orig_fix = MS._fix_exp_for_x_d_info_v2


def _fix_ko(x_d_info, x_s_info, *a):
    x_d_info = _orig_fix(x_d_info, x_s_info, *a)
    plan = KO["plan"]
    if plan is not None:
        g = plan[min(KO["i"], len(plan) - 1)]
        KO["i"] += 1
        e, s = x_d_info["exp"], x_s_info["exp"]
        e3, s3 = e.reshape(-1, 21, 3), s.reshape(-1, 21, 3)
        e3[:, LIP] = s3[:, LIP] + g * (e3[:, LIP] - s3[:, LIP])
        x_d_info["exp"] = e3.reshape(e.shape)
    return x_d_info


MS._fix_exp_for_x_d_info_v2 = _fix_ko


def table_plan(table_path, timing, n_frames, fps=25):
    """배운 입모양표(입모양_학습.py, 실제 한국어 화자 영상) → 프레임마다 입술 움직임 배율.
    배율 = 그 발음의 평균 입 벌림 / 말할 때 평균 (아 1.36 … 오 0.67·우 0.63), ㅁㅂ·쉼 = 0.25 (사진의 다문 입 쪽).
    받아쓰기 시각은 실제 입보다 약 0.2초 늦음 → 표의 lag_frames(-5) 만큼 앞당김"""
    t = json.load(open(table_path, encoding="utf-8"))
    gain, lag = t["gain"], int(t.get("lag_frames", -5))
    VOW = {0: "아", 2: "아", 9: "아", 4: "어", 6: "어", 14: "어", 8: "오", 12: "오", 10: "오", 11: "오",
           13: "우", 17: "우", 15: "우", 16: "우", 18: "으", 19: "으", 20: "이", 1: "에", 3: "에", 5: "에", 7: "에"}
    g = np.full(n_frames, 0.25, np.float32)               # 쉬는 곳: 다문 입
    shut = np.zeros(n_frames, bool)                       # 입술을 꼭 다무는 장면 (섞지 않음)
    for ch, s0, e0 in timing:
        v = ord(ch) - 0xAC00
        cho, jung, jong = v // 588, (v % 588) // 28, v % 28
        f0, f1 = int(s0 * fps) + lag, int(round(e0 * fps)) + lag
        fr = [f for f in range(f0, max(f1, f0 + 1)) if 0 <= f < n_frames]
        for k, f in enumerate(fr):
            tt = k / max(len(fr), 1)
            c = "닫음" if ((cho in (6, 7, 8, 17) and tt < 0.25) or (jong in (16, 17, 26) and tt > (0.15 if jung in (18, 19, 20) else 0.4))) else VOW.get(jung)   # 받침 ㅁㅂㅍ 은 일찍 입을 닫음(습니다=슴니다, 사용자 지적)
            g[f] = gain.get(c, 1.0)
            if c == "닫음":
                shut[f] = True
        if jong in (16, 17, 26) and fr and fr[-1] + 1 < n_frames:
            shut[fr[-1] + 1] = True                       # 받침 ㅁㅂㅍ: 다음 음절 첫 장면까지 다문 입 ([슴니다])
    g = np.convolve(np.pad(g, 1, mode="edge"), [0.25, 0.5, 0.25], "valid")
    g[shut] = 0.0                                         # 꼭 다문 입 = 사진(입 다문 얼굴) 그대로, 앞뒤와 섞지 않음 (사용자 지적 2026-11-21 '습')
    return g


def korean_plan(wav, text, n_frames, fps=25, timing=None):
    import importlib.util
    spec = importlib.util.spec_from_file_location("사진아나운서", os.path.join(HERE, "사진아나운서.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    m.FPS = fps
    shapes = m.plan_shapes(wav, text, n_frames, timing)
    g = np.array([GAIN[s] for s in shapes], np.float32)
    g = np.convolve(np.pad(g, 1, mode="edge"), [0.25, 0.5, 0.25], "valid")   # 갑자기 바뀌지 않게
    return g

from inference import run  # noqa: E402
from stream_pipeline_offline import StreamSDK  # noqa: E402


def main():
    a = sys.argv[1:]
    src, audio, out = a[0], a[1], os.path.abspath(a[2])

    def opt(k, d):
        return a[a.index(k) + 1] if k in a else d
    steps, emo = int(opt("--단계", 50)), int(opt("--감정", 4))
    ck = os.path.join(DITTO, "checkpoints")
    if audio.lower().endswith(".mp3"):                # Ditto 는 wav 를 librosa 로 읽음 → 16k wav 로
        wav = out + ".16k.wav"
        os.system(f'ffmpeg -loglevel error -y -i "{audio}" -ac 1 -ar 16000 "{wav}"')
        audio = wav
    text = opt("--대본", None)
    if text:
        if os.path.exists(text):
            text = open(text, encoding="utf-8").read()
        import math
        import wave
        if not audio.lower().endswith(".wav") or wave.open(audio).getframerate() != 16000:
            wav = out + ".16k.wav"
            os.system(f'ffmpeg -loglevel error -y -i "{audio}" -ac 1 -ar 16000 "{wav}"')
            audio = wav
        w = wave.open(audio)
        n = math.ceil(w.getnframes() / w.getframerate() * 25)
        tf = opt("--시각", None)
        tb = opt("--입모양표", None)
        if tb and tf:
            KO["plan"] = table_plan(tb, json.load(open(tf, encoding="utf-8")), n)
            print("배운 입모양표 사용:", tb)
        else:
            KO["plan"] = korean_plan(audio, text, n, timing=json.load(open(tf, encoding="utf-8")) if tf else None)
        print("한국어 입 모양 보정:", n, "장")
    SDK = StreamSDK(os.path.join(ck, "ditto_cfg", "v0.4_hubert_cfg_pytorch.pkl"), os.path.join(ck, "ditto_pytorch"))
    run(SDK, audio, src, out, {"setup_kwargs": {"sampling_timesteps": steps, "emo": emo}})
    print("만듦", out)


if __name__ == "__main__":
    main()
