#!/bin/bash
# 배경음악 AI ACE-Step 1.5 준비 (클라우드 서버용, 필요할 때만 한 번): bash 배경음_준비.sh
#  - .acestep (github ace-step/ACE-Step-1.5) + .acestep_venv (CPU torch) + models/ACE-Step1.5 → 약 7GB, 2~3분
#  - 큰 언어모델(1.7B, 3.5GB)은 안 씀 → 받지 않음. 이미 된 것은 건너뜀
#  - 다 되면 .acestep_venv/bin/python 배경음_만들기.py ... 로 곡을 만듦
set -euo pipefail
cd "$(dirname "$0")"
ACE_REV=ca1e85fe9430179831e6bc6be790c332190a3866     # 시험해 본 판 (2026-10)
if [ ! -f .acestep/acestep/handler.py ]; then
  rm -rf .acestep && git clone -q https://github.com/ace-step/ACE-Step-1.5.git .acestep && git -C .acestep checkout -q "$ACE_REV"
fi
AV=.acestep_venv
[ -x "$AV/bin/python" ] || python3.12 -m venv "$AV"
if ! "$AV/bin/python" -c "import torch, transformers, diffusers, loguru, vector_quantize_pytorch, torchao" 2>/dev/null; then
  "$AV/bin/python" -m pip install -q --no-cache-dir --disable-pip-version-check torch==2.10.0 torchaudio==2.10.0 torchvision==0.25.0 --index-url https://download.pytorch.org/whl/cpu
  "$AV/bin/python" -m pip install -q --no-cache-dir --disable-pip-version-check "transformers>=4.51.0,<4.58.0" "diffusers>=0.37.0" \
    scipy soundfile loguru einops "accelerate>=1.12.0" diskcache numba vector-quantize-pytorch "torchao>=0.16.0,<0.17.0" toml \
    modelscope typer-slim pytorch-wavelets pywavelets "setuptools<72" huggingface_hub matplotlib peft python-dotenv
fi
if [ ! -f models/ACE-Step1.5/acestep-v15-turbo/model.safetensors ] || [ ! -f models/ACE-Step1.5/vae/diffusion_pytorch_model.safetensors ]; then
  for i in 1 2 3 4; do
    if "$AV/bin/python" -c "from huggingface_hub import snapshot_download; snapshot_download('ACE-Step/Ace-Step1.5', local_dir='models/ACE-Step1.5', ignore_patterns=['acestep-5Hz-lm-1.7B/*'])"; then
      break
    fi
    sleep $((i * 30))
  done
fi
rm -rf /root/.cache/pip /root/.cache/huggingface/hub 2>/dev/null || true
df -h . | tail -1 | awk '{print "준비 끝 · 남은 저장 공간 " $4}'
