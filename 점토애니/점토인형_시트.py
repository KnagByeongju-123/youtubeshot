# -*- coding: utf-8 -*-
"""점토 인형 4장(앞·옆·옆·뒤, 투명 배경)을 흰 배경 한 장으로 나란히 붙임.
쓰는 법: python 점토애니/점토인형_시트.py <view 폴더> <결과.png>
"""
import sys, os
from PIL import Image

src, out = sys.argv[1], sys.argv[2]
views = [Image.open(os.path.join(src, f"view_{i}.png")).convert("RGBA") for i in range(4)]
w, h = views[0].size
sheet = Image.new("RGB", (w * 4, h), "white")
for i, v in enumerate(views):
    sheet.paste(v, (i * w, 0), v)
sheet.save(out)
print("시트:", out)
