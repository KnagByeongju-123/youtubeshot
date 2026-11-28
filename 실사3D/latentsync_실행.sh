#!/bin/bash
# LatentSync 1.6 CPU 실행. guidance 1.0 (1.5 는 메모리 15GB 서버에서 넘침), 다른 무거운 일과 동시에 돌리지 않음
# 사용: bash 실사3D/latentsync_실행.sh <영상.mp4> <소리.wav> <결과.mp4>
set -e
R="$(cd "$(dirname "$0")/.." && pwd)"; V=$(realpath "$1"); A=$(realpath "$2"); O=$(realpath -m "$3")
cd "$R/models/latentsync/code"
MALLOC_MMAP_THRESHOLD_=131072 MALLOC_TRIM_THRESHOLD_=0 MALLOC_ARENA_MAX=2 ../.venv/bin/python -m scripts.inference \
  --unet_config_path configs/unet/stage2_512.yaml --inference_ckpt_path checkpoints/latentsync_unet.pt \
  --inference_steps 20 --guidance_scale 1.0 --enable_deepcache --video_path "$V" --audio_path "$A" --video_out_path "$O" --temp_dir "$(dirname "$O")/ls_temp"
