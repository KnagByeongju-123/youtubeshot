#!/bin/bash
# 클라우드(폰에서 쓰는 Claude Code) 세션이 시작될 때 영상 제작 준비를 자동으로 함
#  - 한글 글꼴, 화면 부품(tkinter), 가상 모니터(xvfb)
#  - .supertonic_venv : 파이썬 3.12 실행 환경 (프로그램 + Supertonic 성우)
#  - supertonic_assets : Supertonic 3 목소리 모델 (기본 성우 = 남자 성우 2, M2)
# PC(윈도우)에서는 실행되지 않음. 여러 번 실행해도 이미 된 것은 건너뜀.
set -euo pipefail

if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

cd "$CLAUDE_PROJECT_DIR"

# 1) 시스템 부품: 파이썬 3.12 화면 부품 · 한글 글꼴 · 가상 모니터
need=()
python3.12 -c "import tkinter" 2>/dev/null || need+=(python3-tk)
[ -f /usr/share/fonts/truetype/nanum/NanumGothicBold.ttf ] || need+=(fonts-nanum fonts-nanum-extra)
[ -f /usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc ] || need+=(fonts-noto-cjk)
command -v xvfb-run >/dev/null || need+=(xvfb)
command -v ffmpeg >/dev/null || need+=(ffmpeg)
if [ ${#need[@]} -gt 0 ]; then
  export DEBIAN_FRONTEND=noninteractive
  apt-get update -q >/dev/null
  apt-get install -y -q "${need[@]}" >/dev/null
fi

# 2) 파이썬 실행 환경 (프로그램이 성우 담당으로 .supertonic_venv/bin/python 을 찾음)
VENV=.supertonic_venv
[ -x "$VENV/bin/python" ] || python3.12 -m venv "$VENV"
if ! "$VENV/bin/python" -c "import supertonic, numpy, PIL, cv2, imageio_ffmpeg, rembg, faster_whisper, huggingface_hub" 2>/dev/null; then
  "$VENV/bin/python" -m pip install -q --disable-pip-version-check --upgrade pip
  "$VENV/bin/python" -m pip install -q --disable-pip-version-check \
    numpy pillow supertonic opencv-python-headless imageio-ffmpeg "rembg[cpu]" faster-whisper huggingface_hub
fi

# 3) 목소리 모델 (huggingface 가 잠깐 막으면(429) 기다렸다 다시)
if [ ! -d supertonic_assets/onnx ] || [ ! -f supertonic_assets/voice_styles/M2.json ]; then
  for i in 1 2 3 4; do
    if "$VENV/bin/python" -c "from huggingface_hub import snapshot_download; snapshot_download('Supertone/supertonic-3', local_dir='supertonic_assets', ignore_patterns=['audio_samples/*'])"; then
      break
    fi
    sleep $((i * 30))
  done
fi

# 4) 이 세션에서 python = 위 실행 환경
if [ -n "${CLAUDE_ENV_FILE:-}" ]; then
  echo "export PATH=\"$CLAUDE_PROJECT_DIR/$VENV/bin:\$PATH\"" >> "$CLAUDE_ENV_FILE"
fi
