#!/bin/bash
# 클라우드(폰에서 쓰는 Claude Code) 세션이 시작될 때 영상 제작 준비를 자동으로 함
#  - 한글 글꼴, 화면 부품(tkinter), 가상 모니터(xvfb)
#  - .supertonic_venv : 파이썬 3.12 실행 환경 (프로그램 + Supertonic 성우)
#  - supertonic_assets : Supertonic 3 목소리 모델 (기본 성우 = 남자 성우 2, M2)
#  - .sd_venv + models/FLUX2_klein_4B : 만화·그림 장면을 그리는 그림 모델 (캐릭터 시트 기준·부분 수정)
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
if ! "$VENV/bin/python" -c "import supertonic, numpy, PIL, cv2, imageio_ffmpeg, rembg, faster_whisper, huggingface_hub, kiwipiepy" 2>/dev/null; then
  "$VENV/bin/python" -m pip install -q --disable-pip-version-check --upgrade pip
  "$VENV/bin/python" -m pip install -q --disable-pip-version-check \
    numpy pillow supertonic opencv-python-headless imageio-ffmpeg "rembg[cpu]" faster-whisper huggingface_hub kiwipiepy   # kiwipiepy: 나레이션 쉼표(나레이션_쉼표.py)
fi
# 나레이션 쉼표 넣기(나레이션_쉼표.py)용 한국어 형태소 분석기 Kiwi (kiwipiepy, LGPL-3.0)
"$VENV/bin/python" -c "import kiwipiepy" 2>/dev/null || "$VENV/bin/python" -m pip install -q --disable-pip-version-check kiwipiepy || true

# 3) 목소리 모델 (huggingface 가 잠깐 막으면(429) 기다렸다 다시)
if [ ! -d supertonic_assets/onnx ] || [ ! -f supertonic_assets/voice_styles/M2.json ]; then
  for i in 1 2 3 4; do
    if "$VENV/bin/python" -c "from huggingface_hub import snapshot_download; snapshot_download('Supertone/supertonic-3', local_dir='supertonic_assets', ignore_patterns=['audio_samples/*'])"; then
      break
    fi
    sleep $((i * 30))
  done
fi

# 4) 만화·그림 장면을 그리는 FLUX.2 klein 4B (Apache 2.0, .sd_venv + models/FLUX2_klein_4B, 약 16GB · 처음 한 번 5~10분)
#    캐릭터 시트를 기준 그림으로 넣으면 같은 인물 그대로, 부분 수정(손·얼굴)도 됨 → klein_worker.py
#    (예전 SD1.5 모델은 저장 공간 때문에 클라우드에서는 받지 않음. PC 는 로컬그림_모델받기.bat 그대로)
SDV=.sd_venv
[ -x "$SDV/bin/python" ] || python3.12 -m venv "$SDV"
if ! "$SDV/bin/python" -c "import torch, transformers, accelerate, safetensors, huggingface_hub; from diffusers import Flux2KleinPipeline" 2>/dev/null; then
  "$SDV/bin/python" -m pip install -q --disable-pip-version-check --upgrade pip
  "$SDV/bin/python" -m pip install -q --disable-pip-version-check torch --index-url https://download.pytorch.org/whl/cpu
  "$SDV/bin/python" -m pip install -q --disable-pip-version-check "diffusers>=0.42" transformers accelerate safetensors huggingface_hub peft pillow numpy
fi
if [ ! -f models/FLUX2_klein_4B/transformer/diffusion_pytorch_model.safetensors ] || [ ! -f models/FLUX2_klein_4B/text_encoder/model-00002-of-00002.safetensors ]; then
  for i in 1 2 3 4; do
    if "$SDV/bin/python" -c "from huggingface_hub import snapshot_download; snapshot_download('black-forest-labs/FLUX.2-klein-4B', local_dir='models/FLUX2_klein_4B', ignore_patterns=['flux-2-klein-4b.safetensors', '*.md', 'assets/*'])"; then
      break
    fi
    sleep $((i * 30))
  done
fi
# Hugging Face 에서 못 받았으면 구글 드라이브 사본에서 (폴더가 '링크가 있는 모든 사용자' 공유일 때만 됨)
KLEIN_GDRIVE_FOLDER="${KLEIN_GDRIVE_FOLDER:-1gbBT9DOVF0sVoyaUpNPBwP0FQaA9d_EE}"    # 내 드라이브/AI모델/FLUX2_klein_4B
if [ ! -f models/FLUX2_klein_4B/transformer/diffusion_pytorch_model.safetensors ] && [ -n "$KLEIN_GDRIVE_FOLDER" ]; then
  "$SDV/bin/python" -m pip install -q --disable-pip-version-check gdown || true
# 그림 자동 검수(그림_자동검수.py): 글자 위치 찾기 RapidOCR (Apache-2.0, 모델이 설치 파일 안에 있음)
"$SDV/bin/python" -c "import rapidocr_onnxruntime" 2>/dev/null || "$SDV/bin/python" -m pip install -q --disable-pip-version-check rapidocr_onnxruntime || true
  "$SDV/bin/python" -m gdown "https://drive.google.com/drive/folders/$KLEIN_GDRIVE_FOLDER" -O models/FLUX2_klein_4B \
    || echo "구글 드라이브에서도 못 받음 (폴더 공유 설정 확인)" >&2
fi
rm -rf /root/.cache/pip /root/.cache/huggingface/hub 2>/dev/null || true     # 받은 뒤 남는 임시 파일(수 GB)은 지움

# 4-2) Blender 효과(블렌더_효과.py, 사용자 결정 2026-11-08): 장문 다큐의 사진 3D(앞뒤 두 층)·로우폴리 장면
#      Blender 4.2 LTS(GPL, 약 350MB) → ~/tools, 얼굴 찾기 YuNet(Apache-2.0), 주인공 오리기 rembg isnet(MIT) 모델
BL=~/tools/blender-4.2.23-linux-x64/blender
if [ ! -x "$BL" ]; then
  mkdir -p ~/tools
  (cd ~/tools && curl -sSfL -o b.tar.xz https://download.blender.org/release/Blender4.2/blender-4.2.23-linux-x64.tar.xz \
     && tar xf b.tar.xz && rm -f b.tar.xz) || echo "Blender 를 못 받음 (블렌더 효과 없이 평면 사진으로 만들어짐)" >&2
fi
mkdir -p models
[ -f models/face_detection_yunet_2023mar.onnx ] || curl -sSfL -o models/face_detection_yunet_2023mar.onnx \
  https://huggingface.co/opencv/face_detection_yunet/resolve/main/face_detection_yunet_2023mar.onnx || true
[ -f ~/.rembg/models/isnet-general-use/isnet-general-use.onnx ] || \
  "$VENV/bin/python" -c "from rembg import new_session; new_session('isnet-general-use')" >/dev/null 2>&1 || true

# 5) 이 세션에서 python = 위 실행 환경
if [ -n "${CLAUDE_ENV_FILE:-}" ]; then
  echo "export PATH=\"$CLAUDE_PROJECT_DIR/$VENV/bin:\$PATH\"" >> "$CLAUDE_ENV_FILE"
fi
