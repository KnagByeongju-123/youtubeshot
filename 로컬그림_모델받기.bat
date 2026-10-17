@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo [1/2] Creating .sd_venv and installing torch (CPU) + diffusers ... (about 1GB, 5-10 min)
py -3.11 -m venv .sd_venv
.sd_venv\Scripts\python.exe -m pip install -q --upgrade pip
.sd_venv\Scripts\python.exe -m pip install -q torch --index-url https://download.pytorch.org/whl/cpu
.sd_venv\Scripts\python.exe -m pip install -q diffusers transformers accelerate safetensors huggingface_hub pillow numpy
echo [2/2] Downloading LCM Dreamshaper v7 (MIT license, about 4.3GB) ...
.sd_venv\Scripts\python.exe -X utf8 -c "from huggingface_hub import snapshot_download; snapshot_download('SimianLuo/LCM_Dreamshaper_v7', local_dir=r'models/LCM_Dreamshaper_v7', allow_patterns=['model_index.json','unet/config.json','unet/diffusion_pytorch_model.safetensors','vae/*.json','vae/diffusion_pytorch_model.safetensors','text_encoder/config.json','text_encoder/model.safetensors','tokenizer/*','scheduler/*','feature_extractor/*']); print('OK')"
if errorlevel 1 (echo FAILED - check internet connection) else (echo Done. Story videos can now draw their own illustrations on this PC.)
echo [3/3] Downloading anime/comic model Counterfeit-V3.0 (OpenRAIL-M, 2.1GB) + LCM-LoRA (135MB) and converting ...
.sd_venv\Scripts\python.exe -X utf8 -c "from huggingface_hub import hf_hub_download; hf_hub_download('gsdf/Counterfeit-V3.0', 'Counterfeit-V3.0_fix_fp16.safetensors', local_dir=r'models/_dl'); hf_hub_download('latent-consistency/lcm-lora-sdv1-5', 'pytorch_lora_weights.safetensors', local_dir=r'models/lcm-lora-sdv1-5'); print('OK')"
.sd_venv\Scripts\python.exe -X utf8 sd_convert_anime.py
if errorlevel 1 (echo FAILED anime model - illustration model still works) else (echo Done. Anime/comic styles are now available.)
pause
