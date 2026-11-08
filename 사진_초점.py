r"""사진의 '꼭 보여야 하는 곳'(초점 상자) 찾기 (사용자 결정 2026-11-08: 확대해도 문맥상 중요한 날짜·글자가 화면 밖으로 나가면 안 됨)
- 사진 옆에 <사진>.focus.json 을 만듦: {"box": [x0, y0, x1, y1] (0~1 비율), "why": "...", "auto": true}
- 자동: RapidOCR(Apache-2.0)로 사진 속 글자(날짜·비문·간판…)를 찾아 그 둘레를 상자로. 아주 작은 글자(사진 높이 2% 미만)는 무시
- Claude 가 문맥(나레이션이 가리키는 곳)을 보고 직접 적은 파일("auto" 가 없거나 false)은 덮어쓰지 않음
- 영상(shorts_novel_maker_supertonic: 사진 확대·이동, 블렌더_사진3D.py: 3D 카메라)은 이 상자가 화면 밖으로 나가지 않게 움직임
사용: python 사진_초점.py <사진1> <사진2> ...   (결과: 'BOX 사진 x0 y0 x1 y1' / 'NONE 사진')"""
import json
import os
import sys


def main():
    from rapidocr_onnxruntime import RapidOCR
    from PIL import Image
    ocr = None
    for p in sys.argv[1:]:
        f = p + ".focus.json"
        try:
            if os.path.exists(f):
                d = json.load(open(f, encoding="utf-8"))
                print(("BOX " + p + " " + " ".join(f"{v:.3f}" for v in d["box"])) if d.get("box") else "NONE " + p, flush=True)
                continue          # 한 번 만든 것(자동)·Claude 가 적은 것은 그대로
            if ocr is None:
                ocr = RapidOCR()
            with Image.open(p) as im:
                W, H = im.size
            res, _ = ocr(p)
            boxes = []
            for pts, txt, conf in res or []:
                xs, ys = [q[0] for q in pts], [q[1] for q in pts]
                if float(conf) < 0.6 or (max(ys) - min(ys)) < 0.02 * H or len(str(txt).strip()) < 2:
                    continue
                boxes.append((min(xs) / W, min(ys) / H, max(xs) / W, max(ys) / H))
            if boxes:
                b = [min(x[0] for x in boxes), min(x[1] for x in boxes), max(x[2] for x in boxes), max(x[3] for x in boxes)]
                pad = 0.03
                b = [max(0.0, b[0] - pad), max(0.0, b[1] - pad), min(1.0, b[2] + pad), min(1.0, b[3] + pad)]
                json.dump({"box": b, "why": "사진 속 글자(자동)", "auto": True}, open(f, "w", encoding="utf-8"), ensure_ascii=False)
                print("BOX " + p + " " + " ".join(f"{v:.3f}" for v in b), flush=True)
            else:
                json.dump({"box": None, "why": "글자 없음(자동)", "auto": True}, open(f, "w", encoding="utf-8"), ensure_ascii=False)
                print("NONE " + p, flush=True)
        except Exception as e:
            print("ERR " + p + " " + str(e)[:150], flush=True)


if __name__ == "__main__":
    main()
