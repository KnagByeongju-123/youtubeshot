"""지글거림 검사: 연속 세 장(f0, f1, f2)에서 같은 화소가 밝아졌다 → 어두워졌다(또는 반대)를 되풀이하면 지글거림
(카메라·물체 움직임은 한 방향으로만 바뀜). 화소 수 비율이 기준을 넘는 장면을 표시하고 확대 그림을 남김
사용: python 지글거림검사.py <_frames 폴더> <결과 폴더> [--간격 6] [--기준 0.0015]"""
import sys, os, glob, json
import numpy as np
from PIL import Image
src, out = sys.argv[1], sys.argv[2]
step = int(sys.argv[sys.argv.index('--간격') + 1]) if '--간격' in sys.argv else 6
lim = float(sys.argv[sys.argv.index('--기준') + 1]) if '--기준' in sys.argv else 0.0015
os.makedirs(out, exist_ok=True)
def g(p): return np.asarray(Image.open(p).convert('L').resize((960, 540)), dtype=np.int16)
res = []
for d in sorted(glob.glob(os.path.join(src, 'ch*'))):
    fs = sorted(glob.glob(os.path.join(d, 'f*.png')))
    for i in range(1, len(fs) - 1, step):
        a, b, c = g(fs[i - 1]), g(fs[i]), g(fs[i + 1])
        d1, d2 = b - a, c - b
        # 깜빡임: 가운데 장만 다른 색이고 앞뒤 장은 같은 색 (면 겹침 · 얇은 면). 카메라가 방향을 바꿀 때의 테두리는
        #   앞뒤 장이 같지 않으므로 대부분 빠짐. 테두리(밝기 차가 큰 곳) 바로 옆도 뺌
        ed = np.zeros_like(b, dtype=bool); gx = np.abs(np.diff(b, axis=1)) > 40; gy = np.abs(np.diff(b, axis=0)) > 40
        ed[:, 1:] |= gx; ed[:, :-1] |= gx; ed[1:, :] |= gy; ed[:-1, :] |= gy
        osc = (d1 * d2 < 0) & (np.abs(d1) > 18) & (np.abs(d2) > 18) & (np.abs(c - a) < 10) & ~ed
        r = osc.mean()
        res.append((r, os.path.basename(d), os.path.basename(fs[i])))
        if r > lim:
            m = np.stack([b.astype(np.uint8)] * 3, -1).copy(); m[osc] = (255, 0, 0)
            Image.fromarray(m).save(os.path.join(out, '%s_%s' % (os.path.basename(d), os.path.basename(fs[i]))))
res.sort(reverse=True)
bad = [x for x in res if x[0] > lim]
with open(os.path.join(out, '결과.txt'), 'w', encoding='utf-8') as f:
    f.write('검사 %d 곳, 기준 %.4f 넘음 %d 곳\n' % (len(res), lim, len(bad)))
    for r, c, fn in res[:40]: f.write('%.5f %s %s\n' % (r, c, fn))
print('검사', len(res), '곳 · 지글거림 의심', len(bad), '곳'); print('\n'.join('%.5f %s %s' % x for x in res[:10]))
