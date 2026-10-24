"""그림 부분 수정 워커 (.sd_venv 에서 실행): 그림의 정한 네모 칸만 다시 그림 (손가락·얼굴 고치기, 빈 자리에 인물 넣기)
사용: python sd_fix.py <모델폴더> <작업.json>
작업.json: {"image": "원본.png", "out": "결과.png", "steps": 6, "guidance": 1.5,
           "lora": {"path": "...safetensors", "scale": 0.6},          (없어도 됨)
           "fixes": [{"box": [x0, y0, x1, y1], "prompt": "...", "negative": "...", "strength": 0.6, "seed": 1}]}
  - box 는 원본 그림 기준 픽셀. 그 둘레를 조금 넓혀 잘라 512 크기로 키워 다시 그린 뒤 줄여서 붙임 (작은 손·얼굴도 자세히)
  - strength: 0.3~0.5 = 모양만 다듬기(손가락 수 등), 0.6~0.8 = 크게 바꾸기(얼굴), 1.0 = 새로 그리기(빈 자리에 인물)
  - 경계는 부드럽게 섞어서 붙인 자국이 안 보이게
출력: 고친 칸마다 'OK 번호 초', 실패는 'ERR 번호 이유', 끝나면 'DONE 결과경로'"""
import json
import os
import sys
import time


def main():
    model_dir, job_path = sys.argv[1], sys.argv[2]
    job = json.load(open(job_path, encoding="utf-8"))
    import torch
    from PIL import Image, ImageDraw, ImageFilter
    torch.set_num_threads(max(1, os.cpu_count() or 4))
    from diffusers import StableDiffusionInpaintPipeline, LCMScheduler
    t0 = time.time()
    pipe = StableDiffusionInpaintPipeline.from_pretrained(model_dir, torch_dtype=torch.float32, safety_checker=None,
                                                          requires_safety_checker=False)
    pipe.scheduler = LCMScheduler.from_config(pipe.scheduler.config)
    pipe.set_progress_bar_config(disable=True)
    lora = job.get("lora") or {}
    if lora.get("path") and os.path.exists(lora["path"]):
        try:
            pipe.load_lora_weights(os.path.dirname(lora["path"]), weight_name=os.path.basename(lora["path"]), adapter_name="style")
            pipe.set_adapters(["style"], adapter_weights=[float(lora.get("scale", 0.7))])
        except Exception as e:
            print(f"WARN LoRA 적용 실패(보조 없이 그림): {str(e)[:160]}", flush=True)
    print(f"LOADED {time.time() - t0:.1f}s", flush=True)
    img = Image.open(job["image"]).convert("RGB")
    W, H = img.size
    steps = int(job.get("steps") or 6)
    guidance = float(job.get("guidance") or 1.5)
    for k, fx in enumerate(job.get("fixes") or []):
        try:
            t1 = time.time()
            x0, y0, x1, y1 = [int(v) for v in fx["box"]]
            x0, y0, x1, y1 = max(0, min(x0, x1)), max(0, min(y0, y1)), min(W, max(x0, x1)), min(H, max(y0, y1))
            bw, bh = x1 - x0, y1 - y0
            pad = max(16, int(max(bw, bh) * 0.35))           # 둘레를 넓혀서 잘라야 주변과 이어지게 그림
            cx0, cy0, cx1, cy1 = max(0, x0 - pad), max(0, y0 - pad), min(W, x1 + pad), min(H, y1 + pad)
            crop = img.crop((cx0, cy0, cx1, cy1))
            cw, ch = crop.size
            sc = 512 / max(cw, ch)
            tw, th = max(256, int(cw * sc) // 8 * 8), max(256, int(ch * sc) // 8 * 8)
            big = crop.resize((tw, th), Image.LANCZOS)
            mask = Image.new("L", (cw, ch), 0)
            ImageDraw.Draw(mask).rectangle((x0 - cx0, y0 - cy0, x1 - cx0, y1 - cy0), fill=255)
            feather = max(4, int(min(bw, bh) * 0.12))
            mask = mask.filter(ImageFilter.GaussianBlur(feather))
            g = torch.Generator(device="cpu").manual_seed(int(fx.get("seed") or (k + 1)))
            out = pipe(prompt=str(fx.get("prompt") or ""), negative_prompt=str(fx.get("negative") or ""), image=big,
                       mask_image=mask.resize((tw, th), Image.LANCZOS), width=tw, height=th,
                       strength=max(0.1, min(1.0, float(fx.get("strength", 0.6)))),
                       num_inference_steps=steps, guidance_scale=guidance, generator=g).images[0]
            out = out.resize((cw, ch), Image.LANCZOS)
            img.paste(Image.composite(out, crop, mask), (cx0, cy0))   # 고친 칸만, 가장자리는 부드럽게 섞어서
            print(f"OK {k + 1} {time.time() - t1:.1f}s", flush=True)
        except Exception as e:
            print(f"ERR {k + 1} {str(e)[:200]}", flush=True)
    out_path = job.get("out") or job["image"]
    img.save(out_path)
    print(f"DONE {out_path}", flush=True)


if __name__ == "__main__":
    main()
