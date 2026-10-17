"""로컬 그림 생성 워커 (별도 가상환경 .sd_venv 에서 실행): LCM Dreamshaper v7 (MIT) · CPU 전용
사용: python sd_worker.py <모델폴더> <작업.json> <저장폴더>
작업.json: {"items": [{"id": "a1", "prompt": "...", "negative": "...", "width": 768, "height": 432, "seed": 1}], "steps": 4, "guidance": 8.0,
           "lora": {"path": "models/lora_watercolor/....safetensors", "scale": 0.7}}  (lora 는 없어도 됨)
출력: 그림마다 'OK id 경로' 한 줄, 실패는 'ERR id 이유', 진행은 'PROG k/n'"""
import json
import os
import sys
import time


def main():
    model_dir, job_path, out_dir = sys.argv[1], sys.argv[2], sys.argv[3]
    job = json.load(open(job_path, encoding="utf-8"))
    items = job.get("items") or []
    os.makedirs(out_dir, exist_ok=True)
    import torch
    torch.set_num_threads(max(1, os.cpu_count() or 4))
    from diffusers import DiffusionPipeline, LCMScheduler
    t0 = time.time()
    pipe = DiffusionPipeline.from_pretrained(model_dir, torch_dtype=torch.float32, safety_checker=None, requires_safety_checker=False)
    pipe.scheduler = LCMScheduler.from_config(pipe.scheduler.config)
    pipe.set_progress_bar_config(disable=True)
    pipe.to("cpu")
    lora = job.get("lora") or {}
    if lora.get("path") and os.path.exists(lora["path"]):   # 화풍 보조 파일(LoRA): 예) 수채화
        try:
            pipe.load_lora_weights(os.path.dirname(lora["path"]), weight_name=os.path.basename(lora["path"]), adapter_name="style")
            pipe.set_adapters(["style"], adapter_weights=[float(lora.get("scale", 0.7))])
            print(f"LORA {os.path.basename(lora['path'])} x{float(lora.get('scale', 0.7)):.2f}", flush=True)
        except Exception as e:
            print(f"WARN LoRA 적용 실패(보조 없이 그림): {str(e)[:160]}", flush=True)
    print(f"LOADED {time.time() - t0:.1f}s", flush=True)
    steps = int(job.get("steps") or 4)
    guidance = float(job.get("guidance") or 8.0)
    for k, it in enumerate(items):
        try:
            w = int(it.get("width") or 768)
            h = int(it.get("height") or 432)
            w, h = max(256, w // 8 * 8), max(256, h // 8 * 8)
            g = torch.Generator(device="cpu").manual_seed(int(it.get("seed") or (k + 1)))
            t1 = time.time()
            im = pipe(prompt=str(it.get("prompt") or ""), negative_prompt=str(it.get("negative") or ""), num_inference_steps=steps,
                      guidance_scale=guidance, width=w, height=h, generator=g).images[0]
            path = os.path.join(out_dir, f"{it.get('id') or k}.png")
            im.save(path)
            print(f"OK {it.get('id') or k} {path} {time.time() - t1:.1f}s", flush=True)
        except Exception as e:
            print(f"ERR {it.get('id') or k} {str(e)[:200]}", flush=True)
        print(f"PROG {k + 1}/{len(items)}", flush=True)


if __name__ == "__main__":
    main()
