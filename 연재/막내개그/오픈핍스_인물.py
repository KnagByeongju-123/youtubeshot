"""막내 개그 만화 인물 — Open Peeps(파블로 스탠리, CC0)를 DiceBear(MIT)로 받아 표정만 바꿔 씀 (AI 그림 없이 1초에 한 장)
python 연재/막내개그/오픈핍스_인물.py 시트 <저장폴더>        → 인물마다 표정 8가지 모음 (<이름>_표정.png) + 전체 모음
python 연재/막내개그/오픈핍스_인물.py 한장 <이름> <표정> <파일> → 그 인물·표정 한 장 (투명 배경 PNG, 컷 합성용)
  표정(face): tired·hectic·rage·smileLOL·concerned·blank·suspicious·contempt·cute·awe·fear·eyesClosed·smileBig·solemn 등 30가지
  인물 생김새는 아래 CAST 에 고정 (머리·머리색·피부·옷색·안경·수염) → 어느 컷에서도 같은 사람"""
import io
import json
import os
import sys
import time
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
API = "https://api.dicebear.com/9.x/open-peeps/png"
CAST = {
    "막내": {"head": "longCurly", "headContrastColor": "2c1b18", "skinColor": "edb98a", "clothingColor": "ffffff",
             "accessoriesProbability": 0, "facialHairProbability": 0, "설명": "주인공, 25살 신입, 미역 같은 덥수룩한 곱슬머리, 늘 피곤"},
    "부장님": {"head": "noHair2", "headContrastColor": "4a312c", "skinColor": "ffdbb4", "clothingColor": "8fa7df",
              "accessories": "glasses4", "accessoriesProbability": 100, "facialHair": "moustache3", "facialHairProbability": 100,
              "설명": "55살, 대머리, 뿔테 안경, 콧수염, 뿌듯"},
    "팀장님": {"head": "bangs2", "headContrastColor": "2c1b18", "skinColor": "ffdbb4", "clothingColor": "e78276",
              "accessories": "glasses2", "accessoriesProbability": 100, "facialHairProbability": 0, "설명": "42살 여성, 단발 앞머리, 안경, 빈틈없음"},
    "이대리": {"head": "pomp", "headContrastColor": "724133", "skinColor": "edb98a", "clothingColor": "78e185",
              "accessoriesProbability": 0, "facialHairProbability": 0, "설명": "30살, 올린 머리, 얄미운 선배"},
    "박사원": {"head": "bun", "headContrastColor": "a55728", "skinColor": "ffdbb4", "clothingColor": "ffcf77",
              "accessoriesProbability": 0, "facialHairProbability": 0, "설명": "25살 여성 동기, 묶은 머리, 밝고 눈치 빠름"},
}
FACES = ["tired", "hectic", "rage", "smileLOL", "concerned", "blank", "suspicious", "cute"]


def get(name, face, size=512, fmt="png", **extra):
    c = {k: v for k, v in CAST[name].items() if k != "설명"}
    p = dict(c, seed=name, face=face, size=str(size), **{k: str(v) for k, v in extra.items()})
    for k in ("accessoriesProbability", "facialHairProbability"):
        p[k] = str(p[k])
    url = (API.replace("/png", "/svg") if fmt == "svg" else API) + "?" + urllib.parse.urlencode(p)
    for k in range(3):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "youtubeshot/1.0"})
            return urllib.request.urlopen(req, timeout=60).read()
        except Exception:
            if k == 2:
                raise
            time.sleep(2)


def main(a):
    from PIL import Image, ImageDraw, ImageFont
    if not a:
        print(__doc__)
        return 2
    if a[0] == "한장":
        open(a[3], "wb").write(get(a[1], a[2]))
        return 0
    out = a[1]
    os.makedirs(out, exist_ok=True)
    font = ImageFont.truetype("/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf", 22)
    rows = []
    for name in CAST:
        sheet = Image.new("RGB", (256 * len(FACES), 290), "white")
        d = ImageDraw.Draw(sheet)
        for k, f in enumerate(FACES):
            im = Image.open(io.BytesIO(get(name, f, 256))).convert("RGBA")
            sheet.paste(im, (k * 256, 34), im)
            d.text((k * 256 + 8, 262), f, fill="black", font=font)
        d.text((8, 4), f"{name} — {CAST[name]['설명']}", fill="black", font=font)
        sheet.save(os.path.join(out, f"{name}_표정.png"))
        rows.append(sheet)
        print(name)
    all_ = Image.new("RGB", (rows[0].width, 290 * len(rows)), "white")
    for k, r in enumerate(rows):
        all_.paste(r, (0, 290 * k))
    all_.save(os.path.join(out, "인물_표정_모음.jpg"), quality=88)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
