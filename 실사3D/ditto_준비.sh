#!/bin/bash
# Ditto(말하는 얼굴, Apache-2.0) 준비 — 코드·실행 환경·모델 (InsightFace 모델은 받지 않음: 상업 금지)
# 사용: bash 실사3D/ditto_준비.sh   (저장소 맨 위 폴더에서)
set -e
cd "$(dirname "$0")/../models"
[ -d ditto ] || git clone -q --depth 1 https://github.com/antgroup/ditto-talkinghead ditto
cd ditto
if [ ! -x .venv/bin/python ]; then
  python3.11 -m venv .venv
  .venv/bin/pip -q install torch --index-url https://download.pytorch.org/whl/cpu
  .venv/bin/pip -q install librosa tqdm filetype imageio imageio-ffmpeg opencv-python-headless scikit-image cython colored onnxruntime mediapipe "numpy<2.3"
fi
mkdir -p checkpoints && cd checkpoints
for f in ditto_cfg/v0.4_hubert_cfg_pytorch.pkl ditto_pytorch/aux_models/face_landmarker.task ditto_pytorch/aux_models/hubert_streaming_fix_kv.onnx \
         ditto_pytorch/aux_models/landmark203.onnx ditto_pytorch/models/appearance_extractor.pth ditto_pytorch/models/decoder.pth \
         ditto_pytorch/models/lmdm_v0.4_hubert.pth ditto_pytorch/models/motion_extractor.pth ditto_pytorch/models/stitch_network.pth \
         ditto_pytorch/models/warp_network.pth LICENSE; do
  [ -s $f ] || { mkdir -p $(dirname $f); curl -s -L -A asset-fetcher/1.0 -o $f https://huggingface.co/digital-avatar/ditto-talkinghead/resolve/main/$f; }
done
echo "Ditto 준비 끝"
