# -*- coding: utf-8 -*-
"""중간 장면 메우기 (RIFE v4.26, MIT) — 1초 12장으로 찍은 장면 사이에 한 장씩 만들어 24장으로.

쓰는 법 (.sd_venv 의 파이썬 = torch 가 있음):
  .sd_venv/bin/python -X utf8 블록애니/중간장면.py <찍은 폴더> <결과 폴더>      # f00000.png … → 두 배
  .sd_venv/bin/python -X utf8 블록애니/중간장면.py --시험 <24장으로 찍은 폴더>   # 짝수 장만 써서 홀수 장을 맞혀 봄(점수·시간)

모델: models/RIFE/RIFEv4.26_0921/ (flownet.pkl, IFNet_HDv3.py) — 없으면
  https://huggingface.co/hzwer/RIFE/resolve/main/RIFEv4.26_0921.zip 을 받아 풂.
규칙: 장면이 바뀌는 곳(컷)을 넘어서 메우지 않음 — 샷 폴더마다 따로 돌림.
"""
import os, sys, time, types, glob
import numpy as np
import torch, torch.nn.functional as F
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MDIR = os.path.join(ROOT, 'models', 'RIFE', 'RIFEv4.26_0921')
_grid = {}


def warp(x, flow):
    k = (str(flow.device), tuple(flow.shape))
    if k not in _grid:
        _, _, h, w = flow.shape
        gx = torch.linspace(-1.0, 1.0, w).view(1, 1, 1, w).expand(flow.shape[0], -1, h, -1)
        gy = torch.linspace(-1.0, 1.0, h).view(1, 1, h, 1).expand(flow.shape[0], -1, -1, w)
        _grid[k] = torch.cat([gx, gy], 1)
    fl = torch.cat([flow[:, 0:1] / ((x.shape[3] - 1.0) / 2.0), flow[:, 1:2] / ((x.shape[2] - 1.0) / 2.0)], 1)
    g = (_grid[k] + fl).permute(0, 2, 3, 1)
    return F.grid_sample(x, g, mode='bilinear', padding_mode='border', align_corners=True)


_net = None


def net():
    global _net
    if _net is None:
        m = types.ModuleType('model'); w = types.ModuleType('model.warplayer'); w.warp = warp
        sys.modules['model'] = m; sys.modules['model.warplayer'] = w
        sys.path.insert(0, MDIR)
        from IFNet_HDv3 import IFNet
        n = IFNet()
        sd = torch.load(os.path.join(MDIR, 'flownet.pkl'), map_location='cpu', weights_only=True)  # 받은 파일은 숫자(가중치)만 읽음
        n.load_state_dict({k.replace('module.', ''): v for k, v in sd.items()}, strict=False)
        _net = n.eval()
    return _net


def _t(im):
    return torch.from_numpy(np.asarray(im.convert('RGB'), dtype=np.float32) / 255.).permute(2, 0, 1)[None]


@torch.no_grad()
def middle(a, b, t=0.5, scale=1.0):
    """PIL 그림 a, b 사이의 그림. scale 0.5 = 큰 움직임에 강함(조금 흐림)"""
    w, h = a.size
    x = torch.cat([_t(a), _t(b)], 1)
    ph, pw = (-h) % 64, (-w) % 64
    x = F.pad(x, (0, pw, 0, ph), mode='replicate')
    sl = [16 / scale, 8 / scale, 4 / scale, 2 / scale, 1 / scale]
    out = net()(x, t, sl)[2][-1][0, :, :h, :w]
    return Image.fromarray((out.clamp(0, 1).permute(1, 2, 0).numpy() * 255 + .5).astype(np.uint8))


def diff(a, b):
    """두 그림이 얼마나 다른지 (0~255 평균) — 컷·순간 번쩍임 찾기"""
    x = np.asarray(a.convert('L').resize((160, 90)), dtype=np.float32)
    y = np.asarray(b.convert('L').resize((160, 90)), dtype=np.float32)
    return float(np.abs(x - y).mean())


def fill(src, dst, cut=45.0, scale=1.0, log=True):
    """src 의 f*.png (12장/초) → dst 에 두 배(24장/초). 두 장이 cut 넘게 다르면(컷·번쩍) 앞 장을 그대로 둠"""
    fs = sorted(glob.glob(os.path.join(src, 'f*.png')))
    os.makedirs(dst, exist_ok=True)
    t0 = time.time(); n = 0
    prev = None
    for i, f in enumerate(fs):
        cur = Image.open(f).convert('RGB')
        if prev is not None:
            o = os.path.join(dst, f'f{2*i-1:05d}.png')
            if not os.path.exists(o):
                (prev if diff(prev, cur) > cut else middle(prev, cur, scale=scale)).save(o); n += 1
        o = os.path.join(dst, f'f{2*i:05d}.png')
        if not os.path.exists(o): cur.save(o)
        prev = cur
    if prev is not None:
        o = os.path.join(dst, f'f{2*len(fs)-1:05d}.png')
        if not os.path.exists(o): prev.save(o)
    if log: print(f'{os.path.basename(src)}: {len(fs)}장 → {2*len(fs)}장, 새로 만든 {n}장 {time.time()-t0:.0f}초', flush=True)
    return n


def trial(src, scale=1.0):
    fs = sorted(glob.glob(os.path.join(src, 'f*.png')))
    ps = []; t0 = time.time()
    for i in range(1, len(fs) - 1, 2):
        a, b, g = [Image.open(fs[j]).convert('RGB') for j in (i - 1, i + 1, i)]
        m = middle(a, b, scale=scale)
        e = ((np.asarray(m, dtype=np.float32) - np.asarray(g, dtype=np.float32)) ** 2).mean()
        ps.append(10 * np.log10(255 ** 2 / max(e, 1e-6)))
    dt = (time.time() - t0) / max(1, len(ps))
    ps = np.array(ps)
    print(f'{os.path.basename(src)}: {len(ps)}장  한 장 {dt:.2f}초  닮은 정도 평균 {ps.mean():.1f} / 가장 낮음 {ps.min():.1f} (장 {1+2*int(ps.argmin())})', flush=True)
    return ps, dt


if __name__ == '__main__':
    torch.set_num_threads(int(os.environ.get('RIFE_THREADS', os.cpu_count() or 4)))
    a = sys.argv[1:]
    sc = 1.0
    if '--배율' in a: i = a.index('--배율'); sc = float(a[i + 1]); del a[i:i + 2]
    if a and a[0] == '--시험':
        for d in a[1:]: trial(d, sc)
    else:
        fill(a[0], a[1], scale=sc)
