"""《남극에 남겨진 타로와 지로》 배경음악 (나레이션 없음, 55초)
   0~33초 슬픈 패드 + 바람 / 33초부터 따뜻한 패드 + 감성 오르골 (2초 겹쳐 바꿈), 끝 3초 줄어듦
   사용: xvfb-run -a python -X utf8 남극_음악.py <결과.wav>"""
import os, sys, numpy as np, subprocess
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, HERE)
import shorts_novel_maker_supertonic as m
out = sys.argv[1]; SR = m.SR; T = 55.0; n = int(T * SR); rng = np.random.default_rng(11)
st = lambda x: x if x.ndim == 2 else np.stack([x, x], 1)
def peak(x, p): x = st(x).astype(np.float32); return x / (np.abs(x).max() + 1e-6) * p
sad = peak(m.gen_pad(n, rng, "sad"), 0.42) + peak(m.gen_wind(n, rng), 0.10)
warm = peak(m.gen_pad(n, rng, "warm"), 0.34) + peak(m.gen_musicbox(n, rng, "sad", 66), 0.30)
t = np.arange(n) / SR
x0, x1 = 32.0, 34.0
a = np.clip((t - x0) / (x1 - x0), 0, 1)[:, None]
mix = sad * (1 - a) + warm * a
mix *= np.clip(t / 1.5, 0, 1)[:, None] * np.clip((T - t) / 3.0, 0, 1)[:, None]
mix = np.clip(mix, -0.98, 0.98).astype(np.float32)
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'f32le', '-ar', str(SR), '-ac', '2', '-i', '-', out], input=mix.tobytes(), check=True)
print('OK', out)
