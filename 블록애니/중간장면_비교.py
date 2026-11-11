# -*- coding: utf-8 -*-
"""중간 장면 비교 그림: 앞 장 | 뒤 장 / 진짜 가운데 장 | RIFE 가 만든 가운데 장
  .sd_venv/bin/python -X utf8 블록애니/중간장면_비교.py <24장으로 찍은 폴더> <가운데 장 번호> <결과.jpg>"""
import sys, glob, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import 중간장면 as R
from PIL import Image
d, i, out = sys.argv[1], int(sys.argv[2]), sys.argv[3]
fs = sorted(glob.glob(os.path.join(d, 'f*.png')))
a, g, b = [Image.open(fs[j]).convert('RGB') for j in (i - 1, i, i + 1)]
m = R.middle(a, b)
print('앞-가운데', round(R.diff(a, g), 1), '가운데-뒤', round(R.diff(g, b), 1), '만든것-가운데', round(R.diff(m, g), 1))
W, H = a.size
c = Image.new('RGB', (W * 2, H * 2))
for im, p in ((a, (0, 0)), (b, (W, 0)), (g, (0, H)), (m, (W, H))): c.paste(im, p)
c.save(out, quality=90)
