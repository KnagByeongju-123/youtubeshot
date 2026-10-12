# -*- coding: utf-8 -*-
"""Supertonic 3 무료 한국어 감정형 나레이션 비교 테스트.

필수: Python 3.11, supertonic, ONNX 모델 파일(별도 다운로드).
원본 쇼츠 프로그램은 변경하지 않습니다.

실행 예:
    python supertonic_voice_test.py
    python supertonic_voice_test.py --voices F1 M1 --moods neutral sad horror surprise
    python supertonic_voice_test.py --model-dir C:\\TTS\\assets --steps 5

출처: https://github.com/supertone-oss-archive/supertonic
모델은 OpenRAIL-M, 예제 코드는 MIT 라이선스입니다.
"""
from __future__ import annotations
import argparse
import os
from pathlib import Path
import sys

# 저사양 CPU에서 병렬 스레드가 과하게 생성되지 않도록 제한
os.environ.setdefault("OMP_NUM_THREADS", "2")

SAMPLES = {
    "neutral": "그날 밤 열한 시, 오래된 기차역에는 아무도 없었습니다.",
    "sad": "어머니가 남긴 마지막 편지를 읽는 순간, 눈물이 조용히 흘러내렸습니다.",
    "surprise": "그런데 바로 그때, 십 년 전에 사라진 사람이 문 앞에 서 있었습니다!",
    "horror": "문 밖에서 발소리가 들렸습니다. 하지만 이 집에는 나 혼자 살고 있었습니다.",
    "angry": "당신이 어떻게 그럴 수 있어요? 이제 더는 참지 않겠어요!",
}
# 모델에서 제공하는 표현 태그를 사용하는 예시입니다.
# 한국어에서의 감정 강도와 태그 반응은 문장과 목소리에 따라 달라집니다.
PREFIX = {
    "neutral": "",
    "sad": "<sad> ",
    "surprise": "<surprise> ",
    "horror": "<breath> ",  # 전용 fear 태그가 없으므로 낮은 속도와 호흡으로 표현 시도
    "angry": "<angry> ",
}
RATE_MULTIPLIER = {"neutral": 1.0, "sad": 0.92, "surprise": 1.02, "horror": 0.89, "angry": 1.0}


def main() -> int:
    ap = argparse.ArgumentParser(description="Supertonic 3 한국어 감정 나레이션 비교")
    ap.add_argument("--model-dir", type=Path, default=Path(__file__).resolve().parent / "supertonic_assets",
                    help="다운로드한 모델 폴더(onnx/, voice_styles/ 포함)")
    ap.add_argument("--out-dir", type=Path, default=Path(__file__).resolve().parent / "voice_samples")
    ap.add_argument("--voices", nargs="+", default=["M1"], choices=[*(f"M{i}" for i in range(1, 6)), *(f"F{i}" for i in range(1, 6))])
    ap.add_argument("--moods", nargs="+", default=["neutral", "sad", "surprise", "horror"], choices=list(SAMPLES))
    ap.add_argument("--steps", type=int, default=6, help="합성 단계: 5~12 (기본 6, 품질 우선이면 8)")
    args = ap.parse_args()
    model_dir = args.model_dir.expanduser().resolve()
    if not (model_dir / "onnx").exists() or not (model_dir / "voice_styles").exists():
        print(f"[안내] 모델 파일이 없습니다: {model_dir}")
        print("모델 다운로드: hf download supertone-oss-archive/supertonic-3 --local-dir supertonic_assets")
        return 2
    try:
        from supertonic import TTS
    except ImportError:
        print("[안내] Python 패키지가 없습니다. 'python -m pip install supertonic' 실행 후 다시 시도하세요.")
        return 2

    args.out_dir.mkdir(parents=True, exist_ok=True)
    print("로컬 AI 성우 로딩 중 (CPU)")
    engine = TTS(model="supertonic-3", model_dir=model_dir, auto_download=False)
    steps = max(5, min(12, args.steps))
    for voice in args.voices:
        style = engine.get_voice_style(voice_name=voice)
        for mood in args.moods:
            prompt = PREFIX[mood] + SAMPLES[mood]
            wave, duration = engine.synthesize(
                text=prompt, lang="ko", voice_style=style,
                total_steps=steps, speed=RATE_MULTIPLIER[mood],
                verbose=False,
            )
            dest = args.out_dir / f"{voice}_{mood}.wav"
            engine.save_audio(wave, str(dest))
            secs = float(duration[0]) if hasattr(duration, "__len__") else float(duration)
            print(f"[완료] {dest.name} (음성 {secs:.1f}초)")
    print("결과 WAV 폴더:", args.out_dir.resolve())
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(f"[실패] {type(exc).__name__}: {exc}")
        print("모델 다운로드 및 설치 상태를 확인하세요. 오류가 반복되면 전체 출력 내용을 보관하세요.")
        sys.exit(1)
