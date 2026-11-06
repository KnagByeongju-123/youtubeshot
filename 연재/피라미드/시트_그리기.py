"""입체 블록 캐릭터 시트: 인물마다 앞·옆·옆·뒤 4방향 (원근 없는 카메라, 흰 배경) → 캐릭터시트/<이름>.png + _모두.png
python 연재/피라미드/시트_그리기.py"""
import importlib.util, json, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(os.path.dirname(HERE))
sp = importlib.util.spec_from_file_location("b3", os.path.join(ROOT, "블록3D.py")); E = importlib.util.module_from_spec(sp); sp.loader.exec_module(E)
cast = json.load(open(os.path.join(HERE, "등장인물.json"), encoding="utf-8"))["chars"]
out = os.path.join(HERE, "캐릭터시트"); os.makedirs(out, exist_ok=True)
font = ImageFont.truetype("/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf", 34)
sheets = []
for c in cast:
    tiles = []
    for face in (0, 90, -90, 180):   # 앞 · 오른쪽 옆 · 왼쪽 옆 · 뒤
        bx = E.person(c, (0, 0, 0), face=face, pose={})
        cam = E.Camera((0, 3.0, 40), (0, 3.0, 0), ortho=7.2)
        im = E.render(bx, cam, bg=(255, 255, 255))
        tiles.append(im.crop((W0 := 1920 // 2 - 300, 0, W0 + 600, 1080)).resize((400, 720)))
    sh = Image.new("RGB", (1600, 800), "white")
    for i, tl in enumerate(tiles):
        sh.paste(tl, (i * 400, 70))
    ImageDraw.Draw(sh).text((24, 16), c["name"], fill="#333", font=font)
    sh.save(os.path.join(out, c["name"] + ".png")); sheets.append(sh)
allim = Image.new("RGB", (1600, 800 * len(sheets)), "white")
for i, s in enumerate(sheets):
    allim.paste(s, (0, 800 * i))
allim.save(os.path.join(out, "_모두.png")); print("시트", len(sheets))
