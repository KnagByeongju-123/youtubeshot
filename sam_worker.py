"""SAM(Segment Anything, Meta · Apache 2.0) 인물 윤곽 따기 워커 (.sd_venv 에서 실행, 그래픽카드 없이)
사용: python sam_worker.py <작업.json>
작업.json: {"items": [{"id": "...", "image": "그림.jpg", "boxes": [[x0, y0, x1, y1], ...], "out": "마스크.png"}]}
  - boxes: 그림 크기 대비 비율(0~1). 상자마다 그 안의 물체(인물) 윤곽을 따서 합침 → out 에 흑백 마스크(흰색 = 인물)
  - 모델: facebook/sam-vit-base (처음 한 번 약 375MB 받음)
출력: 'OK id 경로 넓이비율', 실패는 'ERR id 이유'"""
import json
import sys


def main():
    job = json.load(open(sys.argv[1], encoding="utf-8"))
    import numpy as np
    import torch
    from PIL import Image
    from transformers import SamModel, SamProcessor
    torch.set_num_threads(4)
    proc = SamProcessor.from_pretrained("facebook/sam-vit-base")
    model = SamModel.from_pretrained("facebook/sam-vit-base").eval()
    print("LOADED", flush=True)
    for it in job.get("items") or []:
        iid = it.get("id")
        try:
            im = Image.open(it["image"]).convert("RGB")
            W, H = im.size
            boxes = [[b[0] * W, b[1] * H, b[2] * W, b[3] * H] for b in it.get("boxes") or []]
            out = np.zeros((H, W), bool)
            if boxes:
                inp = proc(im, input_boxes=[boxes], return_tensors="pt")
                with torch.no_grad():
                    o = model(**inp, multimask_output=True)
                masks = proc.image_processor.post_process_masks(o.pred_masks, inp["original_sizes"], inp["reshaped_input_sizes"])[0]
                scores = o.iou_scores[0]                     # (상자 수, 3)
                for b in range(masks.shape[0]):
                    k = int(torch.argmax(scores[b]))
                    out |= masks[b, k].numpy().astype(bool)
            Image.fromarray((out * 255).astype(np.uint8)).save(it["out"])
            print(f"OK {iid} {it['out']} {out.mean():.3f}", flush=True)
        except Exception as e:
            print(f"ERR {iid} {str(e)[:200]}", flush=True)


if __name__ == "__main__":
    main()
