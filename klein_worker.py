"""FLUX.2 klein 4B 그림 워커 (.sd_venv 에서 실행, Apache 2.0 · 그래픽카드 없이 CPU 로)
사용: python klein_worker.py <모델폴더> <작업.json> <저장폴더>
작업.json:
  {"items": [{"id": "c01", "prompt": "...", "refs": ["캐릭터시트.png", ...], "width": 1024, "height": 576, "seed": 1, "steps": 4}],
   "fixes": [{"id": "c01_손", "image": "c01.png", "box": [x0, y0, x1, y1], "prompt": "...", "refs": ["캐릭터시트.png"], "seed": 1}],
   "ref_max_area": 115000}
  - items : 새 그림. refs 에 캐릭터 시트(또는 앞모습)를 넣으면 그 인물 그대로 그림 (최대 5명 권장)
  - fixes : 부분 수정. 그림의 box 칸 둘레를 조금 넓혀 잘라 그 조각을 기준 그림으로 다시 그린 뒤 box 만 부드럽게 붙임
            (손가락·얼굴·옷 고치기). refs 에 캐릭터 시트를 더 넣으면 얼굴을 등록한 모습으로 맞춤. 결과는 image 를 덮어씀
  - ref_max_area : 기준 그림을 이 넓이(픽셀)까지 줄여서 넣음. 기준 그림이 크면 계산이 몇 배로 느려짐 (기본 약 256×448)
메모리를 아끼려고 글 해석기로 모든 글을 먼저 읽고 지운 뒤 그림 모델을 올림 (RAM 16GB 에서도 됨)
출력: 'OK id 경로 초', 실패는 'ERR id 이유', 진행은 'PROG k/n'"""
import gc
import json
import os
import sys
import time


def shrink(im, max_area):
    w, h = im.size
    if w * h > max_area:
        s = (max_area / (w * h)) ** 0.5
        im = im.resize((max(16, int(w * s)), max(16, int(h * s))))
    return im


def main():
    model_dir, job_path, out_dir = sys.argv[1], sys.argv[2], sys.argv[3]
    job = json.load(open(job_path, encoding="utf-8"))
    items, fixes = job.get("items") or [], job.get("fixes") or []
    max_area = int(job.get("ref_max_area") or 115000)
    os.makedirs(out_dir, exist_ok=True)
    import torch
    from PIL import Image, ImageDraw, ImageFilter
    from diffusers import Flux2KleinPipeline
    torch.set_num_threads(max(1, os.cpu_count() or 4))
    t0 = time.time()
    enc = Flux2KleinPipeline.from_pretrained(model_dir, transformer=None, vae=None, torch_dtype=torch.bfloat16)
    embs = {}
    with torch.no_grad():
        for k, it in enumerate(items + fixes):
            e = enc.encode_prompt(str(it.get("prompt") or ""), device="cpu")
            embs[k] = e[0] if isinstance(e, tuple) else e
    del enc
    gc.collect()
    pipe = Flux2KleinPipeline.from_pretrained(model_dir, text_encoder=None, tokenizer=None, torch_dtype=torch.bfloat16)
    pipe.set_progress_bar_config(disable=True)
    print(f"LOADED {time.time() - t0:.1f}s", flush=True)

    def draw(k, it, refs, w, h):
        g = torch.Generator(device="cpu").manual_seed(int(it.get("seed") or (k + 1)))
        with torch.no_grad():
            return pipe(image=refs or None, prompt_embeds=embs[k], width=w // 16 * 16, height=h // 16 * 16,
                        num_inference_steps=int(it.get("steps") or 4), guidance_scale=1.0, generator=g).images[0]

    def refs_of(it):
        return [shrink(Image.open(p).convert("RGB"), max_area) for p in (it.get("refs") or []) if os.path.exists(p)]

    total = len(items) + len(fixes)
    for k, it in enumerate(items):
        iid = it.get("id") or k
        try:
            t1 = time.time()
            im = draw(k, it, refs_of(it), int(it.get("width") or 1024), int(it.get("height") or 576))
            path = os.path.join(out_dir, f"{iid}.png")
            im.save(path)
            print(f"OK {iid} {path} {time.time() - t1:.1f}s", flush=True)
        except Exception as e:
            print(f"ERR {iid} {str(e)[:200]}", flush=True)
        print(f"PROG {k + 1}/{total}", flush=True)
    for j, fx in enumerate(fixes):
        k = len(items) + j
        fid = fx.get("id") or k
        try:
            t1 = time.time()
            img = Image.open(fx["image"]).convert("RGB")
            W, H = img.size
            x0, y0, x1, y1 = [int(v) for v in fx["box"]]
            x0, y0, x1, y1 = max(0, min(x0, x1)), max(0, min(y0, y1)), min(W, max(x0, x1)), min(H, max(y0, y1))
            pad = max(16, int(max(x1 - x0, y1 - y0) * 0.25))      # 둘레를 넓혀 잘라야 주변과 이어지게 그림
            cx0, cy0, cx1, cy1 = max(0, x0 - pad), max(0, y0 - pad), min(W, x1 + pad), min(H, y1 + pad)
            crop = img.crop((cx0, cy0, cx1, cy1))
            cw, ch = crop.size
            sc = 512 / max(cw, ch)
            tw, th = max(256, int(cw * sc)) // 16 * 16, max(256, int(ch * sc)) // 16 * 16
            out = draw(k, fx, [crop.resize((tw, th), Image.LANCZOS)] + refs_of(fx), tw, th).resize((cw, ch), Image.LANCZOS)
            mask = Image.new("L", (cw, ch), 0)
            ImageDraw.Draw(mask).rectangle((x0 - cx0, y0 - cy0, x1 - cx0, y1 - cy0), fill=255)
            mask = mask.filter(ImageFilter.GaussianBlur(max(4, int(min(x1 - x0, y1 - y0) * 0.1))))
            img.paste(Image.composite(out, crop, mask), (cx0, cy0))   # box 칸만, 가장자리는 부드럽게 섞어서
            path = fx.get("out") or fx["image"]
            img.save(path)
            print(f"OK {fid} {path} {time.time() - t1:.1f}s", flush=True)
        except Exception as e:
            print(f"ERR {fid} {str(e)[:200]}", flush=True)
        print(f"PROG {k + 1}/{total}", flush=True)


if __name__ == "__main__":
    main()
