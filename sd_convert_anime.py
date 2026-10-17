"""애니·만화 전용 모델 준비 (한 번만): Counterfeit-V3.0 단일 파일 + LCM-LoRA → diffusers 폴더(models/Counterfeit_V3_lcm)로 저장
실행: .sd_venv\\Scripts\\python.exe sd_convert_anime.py  (로컬그림_모델받기.bat 이 자동으로 부름)"""
import os
import sys
import torch
from diffusers import StableDiffusionPipeline, LCMScheduler

HERE = os.path.dirname(os.path.abspath(__file__))
CKPT = os.path.join(HERE, "models", "_dl", "Counterfeit-V3.0_fix_fp16.safetensors")
LORA = os.path.join(HERE, "models", "lcm-lora-sdv1-5")
REF = os.path.join(HERE, "models", "LCM_Dreamshaper_v7")      # SD1.5 구조 설정 참고용
OUT = os.path.join(HERE, "models", "Counterfeit_V3_lcm")


def main():
    if os.path.exists(os.path.join(OUT, "model_index.json")):
        print("already converted:", OUT)
        return
    pipe = StableDiffusionPipeline.from_single_file(CKPT, config=REF, torch_dtype=torch.float32, safety_checker=None, requires_safety_checker=False, low_cpu_mem_usage=False,
                                                    load_safety_checker=False)
    pipe.load_lora_weights(LORA)
    pipe.fuse_lora(lora_scale=1.0)
    pipe.unload_lora_weights()
    pipe.scheduler = LCMScheduler.from_config(pipe.scheduler.config)
    pipe.save_pretrained(OUT, safe_serialization=True)
    print("converted:", OUT)


if __name__ == "__main__":
    main()
