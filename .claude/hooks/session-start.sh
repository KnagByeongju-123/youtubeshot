#!/bin/bash
# 클라우드(폰에서 쓰는 Claude Code) 세션이 시작될 때 영상 제작 준비를 자동으로 함
#  - 한글 글꼴, 화면 부품(tkinter), 가상 모니터(xvfb)
#  - .supertonic_venv : 파이썬 3.12 실행 환경 (프로그램 + Supertonic 성우)
#  - supertonic_assets : Supertonic 3 목소리 모델 (기본 성우 = 남자 성우 2, M2)
#  - .sd_venv + models : 만화·그림 장면을 그리는 로컬 그림 모델
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

# 4) 만화·그림 장면을 직접 그리는 로컬 그림 모델 (.sd_venv + models/, 약 7GB · 처음 한 번 5~10분)
#    일러스트(LCM Dreamshaper v7) + 애니·만화(Counterfeit-V3.0 + LCM-LoRA) + 화풍 보조(수채화·펜화·잉크 등)
SDV=.sd_venv
[ -x "$SDV/bin/python" ] || python3.12 -m venv "$SDV"
if ! "$SDV/bin/python" -c "import torch, diffusers, transformers, accelerate, safetensors, peft, huggingface_hub" 2>/dev/null; then
  "$SDV/bin/python" -m pip install -q --disable-pip-version-check --upgrade pip
  "$SDV/bin/python" -m pip install -q --disable-pip-version-check torch --index-url https://download.pytorch.org/whl/cpu
  "$SDV/bin/python" -m pip install -q --disable-pip-version-check diffusers transformers accelerate safetensors huggingface_hub peft pillow numpy
fi
for i in 1 2 3 4; do
  if "$SDV/bin/python" -X utf8 - <<'PY'
import os
from huggingface_hub import snapshot_download, hf_hub_download
if not os.path.exists("models/LCM_Dreamshaper_v7/unet/diffusion_pytorch_model.safetensors"):
    snapshot_download("SimianLuo/LCM_Dreamshaper_v7", local_dir="models/LCM_Dreamshaper_v7",
                      allow_patterns=["model_index.json", "unet/config.json", "unet/diffusion_pytorch_model.safetensors", "vae/*.json",
                                      "vae/diffusion_pytorch_model.safetensors", "text_encoder/config.json", "text_encoder/model.safetensors",
                                      "tokenizer/*", "scheduler/*", "feature_extractor/*"])
if not os.path.exists("models/Counterfeit_V3_lcm/model_index.json"):
    hf_hub_download("gsdf/Counterfeit-V3.0", "Counterfeit-V3.0_fix_fp16.safetensors", local_dir="models/_dl")
    hf_hub_download("latent-consistency/lcm-lora-sdv1-5", "pytorch_lora_weights.safetensors", local_dir="models/lcm-lora-sdv1-5")
if not os.path.exists("models/lora_watercolor/fladdict-watercolor-sd-1-5.safetensors"):
    hf_hub_download("fladdict/watercolor", "fladdict-watercolor-sd-1-5.safetensors", local_dir="models/lora_watercolor")
for f in ["sd15_oil_paint", "sd15_japanese_woodblock", "sd15_pen_ink_engraving", "sd15_crayon_drawing",
          "sd15_monet_impressionism", "sd15_ink_sketch", "sd15_impressionist_painting"]:
    if not os.path.exists(f"models/lora_styles/{f}.safetensors"):
        hf_hub_download("MRA-Labs/neverending-styles", f + ".safetensors", local_dir="models/lora_styles")
PY
  then
    break
  fi
  sleep $((i * 30))
done
if [ ! -f models/Counterfeit_V3_lcm/model_index.json ] && [ -f models/_dl/Counterfeit-V3.0_fix_fp16.safetensors ]; then
  "$SDV/bin/python" -X utf8 sd_convert_anime.py
fi
[ -f models/Counterfeit_V3_lcm/model_index.json ] && rm -rf models/_dl    # 변환이 끝나면 원본(2GB)은 지움

# 5) 이 세션에서 python = 위 실행 환경
if [ -n "${CLAUDE_ENV_FILE:-}" ]; then
  echo "export PATH=\"$CLAUDE_PROJECT_DIR/$VENV/bin:\$PATH\"" >> "$CLAUDE_ENV_FILE"
fi
