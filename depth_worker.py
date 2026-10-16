"""사진 깊이 추정 (Depth Anything V2 Small, ONNX) - Supertonic 가상환경의 onnxruntime 으로 실행.
사용: python depth_worker.py <모델.onnx> <저장폴더> <사진1> <사진2> ...
사진마다 <저장폴더>/<이름>.npy (float16, 0=멀다 ~ 1=가깝다, 긴 변 518px) 를 쓰고 'OK 사진경로 npy경로' 한 줄씩 출력"""
import sys, os, hashlib
import numpy as np
from PIL import Image


def key_for(path):
    st = os.stat(path)
    return hashlib.md5(f"{os.path.abspath(path)}|{st.st_size}|{int(st.st_mtime)}".encode("utf-8")).hexdigest()[:20]


def main():
    model, out_dir, paths = sys.argv[1], sys.argv[2], sys.argv[3:]
    os.makedirs(out_dir, exist_ok=True)
    import onnxruntime as ort
    so = ort.SessionOptions()
    so.intra_op_num_threads = max(1, (os.cpu_count() or 4) - 1)
    sess = ort.InferenceSession(model, so, providers=["CPUExecutionProvider"])
    inp = sess.get_inputs()[0].name
    mean = np.array([0.485, 0.456, 0.406], np.float32).reshape(1, 3, 1, 1)
    std = np.array([0.229, 0.224, 0.225], np.float32).reshape(1, 3, 1, 1)
    for p in paths:
        try:
            npy = os.path.join(out_dir, key_for(p) + ".npy")
            if os.path.exists(npy):
                print("OK", p, npy, flush=True)
                continue
            im = Image.open(p).convert("RGB")
            w, h = im.size
            k = 518 / max(w, h)
            nw, nh = max(14, int(round(w * k / 14)) * 14), max(14, int(round(h * k / 14)) * 14)
            x = np.asarray(im.resize((nw, nh), Image.BICUBIC), np.float32) / 255.0
            x = (x.transpose(2, 0, 1)[None] - mean) / std
            d = sess.run(None, {inp: x.astype(np.float32)})[0][0]          # 상대 역깊이 (클수록 가까움)
            lo, hi = np.percentile(d, 1), np.percentile(d, 99)
            d = np.clip((d - lo) / max(1e-6, hi - lo), 0, 1).astype(np.float16)
            tmp = npy + ".tmp.npy"
            np.save(tmp, d)
            os.replace(tmp, npy)
            print("OK", p, npy, flush=True)
        except Exception as e:
            print("ERR", p, str(e)[:120], flush=True)


if __name__ == "__main__":
    main()
