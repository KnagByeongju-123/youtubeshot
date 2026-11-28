#!/bin/bash
# LatentSync 1.6 (ByteDance, Apache-2.0) 립싱크 — 그래픽카드 없는 서버(CPU)용으로 고쳐 설치 (2026-11-28 시험)
#  고친 것(latentsync_cpu.patch): 얼굴 찾기 InsightFace(상업 금지) → MediaPipe, cuda → cpu, 주의 계산·VAE 를 나눠 메모리 아낌, 체크포인트 mmap
# 사용: bash 실사3D/latentsync_준비.sh   (모델 약 5GB)
#  실행: bash 실사3D/latentsync_실행.sh <영상.mp4(사진이면 ffmpeg -loop 1 로 만든 것)> <소리.wav> <결과.mp4>
set -e
cd "$(dirname "$0")/.."
D=models/latentsync; mkdir -p $D/ckpt/whisper
[ -d $D/code ] || { git clone -q https://github.com/bytedance/LatentSync.git $D/code; (cd $D/code && git checkout -q a229c3948406bc2cf6eaf4873e662e70c6a04746 && git apply ../../../실사3D/latentsync_cpu.patch); }
ln -sfn ../ckpt $D/code/checkpoints
for f in whisper/tiny.pt latentsync_unet.pt; do [ -s $D/ckpt/$f ] || curl -sL -o $D/ckpt/$f https://huggingface.co/ByteDance/LatentSync-1.6/resolve/main/$f; done
if [ ! -x $D/.venv/bin/python ]; then
  python3.11 -m venv $D/.venv
  $D/.venv/bin/pip install -q torch==2.5.1 torchvision==0.20.1 --index-url https://download.pytorch.org/whl/cpu
  $D/.venv/bin/pip install -q diffusers==0.32.2 transformers==4.48.0 decord==0.6.0 accelerate==0.26.1 einops==0.7.0 omegaconf==2.3.0 \
    opencv-python-headless==4.9.0.80 mediapipe==0.10.11 python_speech_features==0.6 librosa==0.10.1 scenedetect==0.6.1 ffmpeg-python \
    imageio==2.31.1 imageio-ffmpeg==0.5.1 huggingface-hub==0.30.2 numpy==1.26.4 kornia==0.8.0 DeepCache==0.1.1
fi
apt-get install -y -q libegl1 libgles2 libgl1 >/dev/null 2>&1 || true   # MediaPipe
echo "준비 끝"
