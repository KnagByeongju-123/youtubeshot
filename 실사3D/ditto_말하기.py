"""Ditto(오픈소스 말하는 얼굴, Apache-2.0) 로 사진 한 장 + 나레이션 → 입·얼굴이 자연스럽게 움직이는 영상 (그래픽카드 없이 CPU)

수익 영상용으로 고친 점 (Ditto 코드는 그대로 두고 이 파일에서 바꿔 끼움):
  - 얼굴 찾기 InsightFace(det_10g·2d106det, 상업 금지)를 **받지도 쓰지도 않음** →
    Ditto 에 들어 있는 MediaPipe 얼굴 점(face_landmarker.task, Apache-2.0) 478개 중 68개를 골라 첫 얼굴 위치로 씀
  - 설정의 device 를 모두 cpu 로
준비(한 번): bash 실사3D/ditto_준비.sh  → models/ditto (코드·.venv·checkpoints)
사용: models/ditto/.venv/bin/python 실사3D/ditto_말하기.py <사진.png> <나레이션.wav|mp3> <결과.mp4> [--단계 50] [--감정 4]
  --단계: 움직임 만들기 단계 수(기본 50, 줄이면 빠르지만 거칠어짐) / --감정: Ditto 감정 번호(기본 4 = 보통)
"""
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


def _crop(self, img, last_lmk=None, **kw):
    if last_lmk is None:
        l478 = self.landmark478(img)
        if l478 is None or len(l478) == 0 or l478.size == 0:
            raise RuntimeError("사진에서 얼굴을 못 찾음 (MediaPipe)")
        pts = l478[0][:, :2].copy()
        if pts.max() <= 1.5:                      # 0~1 비율 → 픽셀
            pts[:, 0] *= img.shape[1]
            pts[:, 1] *= img.shape[0]
        last_lmk = pts[MP68]
    return _orig_crop(self, img, last_lmk=last_lmk, **kw)


S.Source2Info._crop = _crop

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
    SDK = StreamSDK(os.path.join(ck, "ditto_cfg", "v0.4_hubert_cfg_pytorch.pkl"), os.path.join(ck, "ditto_pytorch"))
    run(SDK, audio, src, out, {"setup_kwargs": {"sampling_timesteps": steps, "emo": emo}})
    print("만듦", out)


if __name__ == "__main__":
    main()
