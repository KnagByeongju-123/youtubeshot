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

# Subprocess pipes on Korean Windows can default to cp949 despite the parent
# writing UTF-8 JSON. Always decode the wire protocol as UTF-8; never allow
# 'surrogateescape' bytes to leak into the Supertonic Unicode tokenizer.
if hasattr(sys.stdin, "reconfigure"):
    sys.stdin.reconfigure(encoding="utf-8", errors="strict")
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="strict")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")


def reply(ok, **data):
    sys.stdout.write(json.dumps({"ok": bool(ok), **data}, ensure_ascii=False) + "\n")
    sys.stdout.flush()


# 섞은 목소리: 목소리·억양(ttl)은 비율대로 섞고, 끊어 읽는 박자(dp)는 따로. steps = 이 목소리의 최소 품질
# F5S = 여성 성우 5 + 여성 성우 2 를 7:3 (표준말 억양, 사용자 결정 2026-11-07: 샘플 비교에서 선택)
BLENDS = {"F5S": {"ttl": {"F5": .7, "F2": .3}, "dp": {"F5": 1.0}, "steps": 10}}


def blend_style(tts, name):
    from supertonic.core import Style
    b = BLENDS[name]
    base = {v: tts.get_voice_style(voice_name=v) for v in set(b["ttl"]) | set(b["dp"])}
    ttl = sum(w * base[v].ttl for v, w in b["ttl"].items())
    dp = sum(w * base[v].dp for v, w in b["dp"].items())
    return Style(ttl.astype("float32"), dp.astype("float32"))


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
            if any(0xD800 <= ord(ch) <= 0xDFFF for ch in text):
                raise ValueError("잘못된 문자 인코딩이 포함되어 있습니다. UTF-8 통신 설정을 확인하세요.")
            voice = str(req.get("voice", "M1"))
            if voice not in {f"M{i}" for i in range(1,6)} | {f"F{i}" for i in range(1,6)} | set(BLENDS):
                raise ValueError("잘못된 성우 ID: " + voice)
            if not text:
                raise ValueError("빈 나레이션")
            path = Path(req["out"]).resolve()
            path.parent.mkdir(parents=True, exist_ok=True)
            with contextlib.redirect_stdout(sys.stderr):
                style = blend_style(tts, voice) if voice in BLENDS else tts.get_voice_style(voice_name=voice)
                steps = max(2, min(12, int(req.get("steps", 5))))
                if voice in BLENDS:
                    steps = max(steps, BLENDS[voice].get("steps", 5))
                audio, duration = tts.synthesize(text=text, voice_style=style,
                                                 lang=str(req.get("lang", "ko")),
                                                 speed=max(.70, min(2.0, float(req.get("speed", 1.0)))),
                                                 total_steps=steps,
                                                 verbose=False)
                tts.save_audio(audio, str(path))
            reply(True, status="generated", file=str(path))
        except Exception as ex:
            traceback.print_exc(file=sys.stderr)
            reply(False, error=f"{type(ex).__name__}: {ex}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
