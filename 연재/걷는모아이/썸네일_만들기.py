"""모아이 편 썸네일 후보 4개 (입체 블록 장면 + 큰 글자) → output/걷는모아이/썸네일/후보N.png + _썸네일_후보.jpg
python 연재/걷는모아이/썸네일_만들기.py"""
import importlib.util, json, os
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(os.path.dirname(HERE))
sp = importlib.util.spec_from_file_location("b3", os.path.join(ROOT, "블록장면3D.py")); B = importlib.util.module_from_spec(sp); sp.loader.exec_module(B)
OUT = os.path.join(ROOT, "output", "걷는모아이", "썸네일"); os.makedirs(OUT, exist_ok=True)
FB = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
cast = {c["name"]: c for c in json.load(open(os.path.join(HERE, "등장인물.json"), encoding="utf-8"))["chars"]}
H, T, A = "안내자 하람 (14)", "조각가 토키 할아버지 (70대)", "아리 (10)"
R, Bl, G = "섬 사람 빨강 팀", "섬 사람 파랑 팀", "섬 사람 초록 팀"
TEAMS = {"left": [R, R, R], "right": [Bl, Bl, Bl], "back": [G, G]}
WALK = {"start": -14, "end": 0, "mz": 0, "msc": 2.0}

def ch(who, at, face=0, act=None, **k):
    d = {"who": who, "at": at, "face": face, "act": act or ["breath"]}; d.update(k); return d

SC = {
 # 1: 크게 기운 모아이 + 놀라는 하람·아리 (앞)
 1: ({"set": "walk", "opt": {**WALK, "teams": TEAMS, "period": 3.0}, "cam": {"pos": [6, 3.2, 14], "look": [-6, 7, 0], "fov": 62},
      "chars": [ch(H, [2.5, 6.5], 30, ["shout"]), ch(A, [4.6, 5.0], 10, ["shout"])]}, 0.75),
 # 2: 아래에서 올려다본 거대한 모아이 + 작은 하람
 2: ({"set": "field", "extra": {"moai": [[-1, -3, 10, 2.0]]}, "cam": {"pos": [5, 1.0, 9], "look": [-0.5, 8.5, -3], "fov": 72},
      "chars": [ch(H, [3.6, 4.2], 20, ["shout"])]}, 1.0),
 # 3: 줄 세 개로 당기는 장면, 위에서
 3: ({"set": "walk", "opt": {**WALK, "teams": TEAMS, "period": 3.0}, "cam": {"pos": [8, 16, 30], "look": [-7, 5, 0], "fov": 52}}, 0.75),
 # 4: 엉덩방아 하람 + 깔깔
 4: ({"set": "walk", "opt": {**WALK, "walk": False, "teams": TEAMS}, "cam": {"pos": [6, 3.5, 2], "look": [-3, 3.5, -8], "fov": 56},
      "chars": [ch(H, [-1.5, -4.5], 63, ["laugh", "sit"])]}, 1.0),
}
TXT = {1: ("모아이가", "걸었다?!"), 2: ("이 돌을", "어떻게 옮겼을까?"), 3: ("줄 3개의", "비밀"), 4: ("돌이", "걸어갔다고?!")}

def big_text(im, l1, l2):
    d = ImageDraw.Draw(im)
    f1, f2 = ImageFont.truetype(FB, 120), ImageFont.truetype(FB, 170)
    x = 70
    d.text((x, 640), l1, font=f1, fill="#ffffff", stroke_width=12, stroke_fill="#1a1a1a")
    d.text((x, 780), l2, font=f2, fill="#ffd21f", stroke_width=14, stroke_fill="#1a1a1a")
    return im

thumbs = []
for k, (sc, t) in SC.items():
    sc = {"engine": "3d", **sc}
    im = B.frame(sc, cast, t * 8 * 0.5 + 1.0, 8)
    im = ImageEnhance.Color(im).enhance(1.25)
    im = big_text(im, *TXT[k])
    p = os.path.join(OUT, f"후보{k}.png"); im.save(p); thumbs.append(im)
sheet = Image.new("RGB", (1920, 1080 + 30), "white")
for i, im in enumerate(thumbs):
    sheet.paste(im.resize((960, 540)), ((i % 2) * 960, (i // 2) * 555))
dr = ImageDraw.Draw(sheet); f = ImageFont.truetype(FB, 40)
for i in range(4):
    dr.text(((i % 2) * 960 + 14, (i // 2) * 555 + 8), str(i + 1), font=f, fill="#ffffff", stroke_width=5, stroke_fill="#000")
sheet.save(os.path.join(OUT, "_썸네일_후보.jpg"), quality=92); print("ok")
