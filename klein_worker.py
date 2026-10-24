"""FLUX.2 klein 4B 그림 워커 (.sd_venv 에서 실행, Apache 2.0 · 그래픽카드 없이 CPU 로)
사용: python klein_worker.py <모델폴더> <작업.json> <저장폴더>
작업.json:
  {"items": [{"id": "c01", "prompt": "...", "refs": ["캐릭터시트.png", ...], "width": 1024, "height": 576, "seed": 1, "steps": 4}],
   "fixes": [{"id": "c01_손", "image": "c01.png", "box": [x0, y0, x1, y1], "prompt": "...", "refs": ["캐릭터시트.png"], "seed": 1}],
   "ref_max_area": 115000, "crop_border": true}
  - items : 새 그림. refs 에 캐릭터 시트(또는 앞모습)를 넣으면 그 인물 그대로 그림 (최대 5명 권장)
  - fixes : 부분 수정. 그림의 box 칸 둘레를 조금 넓혀 잘라 그 조각을 기준 그림으로 다시 그린 뒤 box 만 부드럽게 붙임
            (손가락·얼굴·옷 고치기). refs 에 캐릭터 시트를 더 넣으면 얼굴을 등록한 모습으로 맞춤. 결과는 image 를 덮어씀
  - ref_max_area : 기준 그림을 이 넓이(픽셀)까지 줄여서 넣음. 기준 그림이 크면 계산이 몇 배로 느려짐 (기본 약 256×448)
  - crop_border : 새 그림(items)의 종이 여백·검은 만화 테두리를 찾아 잘라내고 원래 크기로 (기본 켬. 영상에서 그림이 줄어들 때 테두리가 안 보이게)
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


def border_box(im):
    """옛날 만화책 그림의 바깥 종이 여백·검은 테두리선을 찾아 그 안쪽 상자 (x0, y0, x1, y1). 테두리가 없으면 그림 전체"""
    import numpy as np
    g = np.asarray(im.convert("L"), np.float32)
    h, w = g.shape

    def edge(lines, n):           # lines: 가장자리부터 안쪽으로 가는 줄들의 밝기 평균
        start_lim, line_max = int(n * 0.07), max(3, int(n * 0.025))
        i = 0
        while i < start_lim and lines[i] > 150:      # 바깥 종이 여백(밝음)
            i += 1
        if i >= start_lim:
            return 0
        if lines[i] < 110:                           # 검은 테두리선: 얇게(최대 2.5%)만
            k = i
            while k < i + line_max and k < n and lines[k] < 130:
                k += 1
            return k + 3
        return i + 2 if i else 0                     # 선 없이 여백만
    rows, cols = slice(int(h * .2), int(h * .8)), slice(int(w * .2), int(w * .8))
    l_, r_ = edge(g[rows, :].mean(0), w), edge(g[rows, ::-1].mean(0), w)
    t_, b_ = edge(g[:, cols].mean(1), h), edge(g[::-1, cols].mean(1), h)
    return l_, t_, w - r_, h - b_


def crop_border(im):
    """테두리를 잘라내고(남은 얇은 선까지 1.5% 더) 원래 비율·크기로. 테두리가 없으면 그대로"""
    from PIL import Image
    w, h = im.size
    x0, y0, x1, y1 = border_box(im)
    if (x0, y0, x1, y1) == (0, 0, w, h):
        return im
    mx, my = int(w * 0.015), int(h * 0.015)
    x0, y0, x1, y1 = x0 + mx, y0 + my, x1 - mx, y1 - my
    cw, ch = x1 - x0, y1 - y0
    if cw / ch > w / h:           # 남은 상자 가운데를 원래 비율로
        nw = int(ch * w / h)
        x0 += (cw - nw) // 2
        x1 = x0 + nw
    else:
        nh = int(cw * h / w)
        y0 += (ch - nh) // 2
        y1 = y0 + nh
    return im.crop((x0, y0, x1, y1)).resize((w, h), Image.LANCZOS)


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
            if job.get("crop_border", True) and it.get("crop_border", True):
                im = crop_border(im)
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
