# -*- coding: utf-8 -*-
"""쇼츠 스크롤 영상 메이커용 격리 Supertonic 3 음성 합성 워커.

JSON-lines stdio: ready message, then request -> response. Used only with localhost
private subprocess; nothing sent to an external API after model assets are installed.
"""
import argparse
import contextlib
import json
import os
from pathlib import Path
import sys
import traceback

os.environ.setdefault("OMP_NUM_THREADS", "2")


def reply(ok, **data):
    sys.stdout.write(json.dumps({"ok": bool(ok), **data}, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def main():
    arg = argparse.ArgumentParser()
    arg.add_argument("--model-dir", type=Path, required=True)
    args = arg.parse_args()
    model_dir = args.model_dir.resolve()
    if not (model_dir / 'onnx').is_dir() or not (model_dir / 'voice_styles').is_dir():
        reply(False, error=f"모델 폴더 없음: {model_dir}")
        return 2
    try:
        # Third-party SDK may log; keep stdout strictly JSON.
        with contextlib.redirect_stdout(sys.stderr):
            from supertonic import TTS
            tts = TTS(model="supertonic-3", model_dir=model_dir,
                      auto_download=False, intra_op_num_threads=2, inter_op_num_threads=2)
        reply(True, status="ready")
    except Exception as ex:
        traceback.print_exc(file=sys.stderr)
        reply(False, error=f"초기화 실패: {type(ex).__name__}: {ex}")
        return 2

    for line in sys.stdin:
        try:
            req = json.loads(line)
            text = str(req.get("text", "")).strip()
            voice = str(req.get("voice", "M1"))
            if voice not in {f"M{i}" for i in range(1,6)} | {f"F{i}" for i in range(1,6)}:
                raise ValueError("잘못된 성우 ID: " + voice)
            if not text:
                raise ValueError("빈 나레이션")
            path = Path(req["out"]).resolve()
            path.parent.mkdir(parents=True, exist_ok=True)
            with contextlib.redirect_stdout(sys.stderr):
                style = tts.get_voice_style(voice_name=voice)
                audio, duration = tts.synthesize(text=text, voice_style=style,
                                                 lang=str(req.get("lang", "ko")),
                                                 speed=max(.70, min(2.0, float(req.get("speed", 1.0)))),
                                                 total_steps=max(2, min(12, int(req.get("steps", 5)))),
                                                 verbose=False)
                tts.save_audio(audio, str(path))
            reply(True, status="generated", file=str(path))
        except Exception as ex:
            traceback.print_exc(file=sys.stderr)
            reply(False, error=f"{type(ex).__name__}: {ex}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
