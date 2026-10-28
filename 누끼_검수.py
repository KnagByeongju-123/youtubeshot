"""누끼 검수 그림 만들기 — 누끼(앞 인물을 오려 따로 움직임)가 가장 많이 다가온 순간을 그림마다 크게 저장 (.supertonic_venv 에서 실행)
python 누끼_검수.py <프로젝트.json> <저장폴더>
  - 규칙(CLAUDE.md '배경이 완벽하게 메워질 때만 누끼'): 저장된 그림을 크게 열어 인물 둘레에 번진 자국·흐린 띠·겹친 팔다리·잘린 몸이 보이면
    그 컷을 회차 .py 의 CUTOUT 에 {"off": True} 로 적고 project 를 다시 만듦
  - 결과: <저장폴더>/누끼_cNN.jpg (왼쪽 = 원래 그림, 오른쪽 = 가장 많이 다가온 순간), 누끼가 안 걸리는 그림(앞이 너무 작거나 큼·실제 사진)은 건너뜀
  - 깊이 지도가 없으면 먼저 만듦 (models/depth_anything_v2_small_fp16.onnx 필요)"""
import importlib.util
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def main(a):
    if len(a) < 2:
        print(__doc__)
        return 2
    import numpy as np
    from PIL import Image
    spec = importlib.util.spec_from_file_location("snm", os.path.join(HERE, "shorts_novel_maker_supertonic.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    proj = json.load(open(a[0], encoding="utf-8"))
    out = a[1]
    os.makedirs(out, exist_ok=True)
    meds = [m.parse_media(ln.strip()) for ln in proj["story"].split("\n")]
    meds = [x for x in meds if x]
    m.ensure_depth_maps([x[0] for x in meds], print)
    W, H = 1280, 720
    bw, bh = int(W * 1.32), int(H * 1.32)        # 영상과 같은 넉넉한 크기 (1.32배)
    n = 0
    for path, cap, credit, _ in meds:
        cid = os.path.splitext(os.path.basename(path))[0]
        if not __import__("re").search(r"AI|생성", str(credit or "")):
            continue
        side = path + ".누끼.json"
        sp = json.load(open(side, encoding="utf-8")) if os.path.exists(side) else {}
        if sp.get("off"):
            continue
        d = m.load_depth(path)
        if d is None and not sp.get("box"):
            continue
        arr = np.asarray(Image.open(path).convert("RGB").resize((bw, bh), Image.LANCZOS))
        dbig = m._cv2.resize((d * 255.0).astype(np.float32), (bw, bh)) if d is not None else None
        fg, bg = m.cutout_layers(arr, dbig, sp)
        if fg is None:
            continue
        anc = sp.get("anchor")
        box = ((bw - W) / 2, (bh - H) / 2, W, H)
        end = m.cutout_frame(arr, bg, fg, box, 1.0, (W, H), 1.0, zoom=float(sp.get("zoom", 0.03)),
                             anchor=(anc[0] * bw, anc[1] * bh) if anc else None)
        start = arr[int(box[1]):int(box[1]) + H, int(box[0]):int(box[0]) + W]
        sheet = Image.new("RGB", (W * 2, H))
        sheet.paste(Image.fromarray(np.ascontiguousarray(start)), (0, 0))
        sheet.paste(Image.fromarray(end), (W, 0))
        sheet.save(os.path.join(out, f"누끼_{cid}.jpg"), quality=90)
        n += 1
        print("누끼", cid, cap)
    print(f"누끼 검수 그림 {n}장 → {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
