"""막내 개그 만화 인물 — Lorelei(리사 비쇼프스키, CC0 1.0)를 DiceBear 로 받아 흑백 선화 그대로 씀 (사용자 결정 2026-11-06: 한국 웹툰 같은 얼굴)
python 연재/막내개그/로렐라이_인물.py 시트 <저장폴더>   → 인물마다 표정 모음 + 전체 모음
  - CAST: 인물마다 머리·얼굴형·코·안경 고정 → 어느 컷에서나 같은 사람
  - FACES: 표정 이름 → (눈, 눈썹, 입). 말할 때 입(TALK), 깜빡일 때 눈(BLINK)을 바꿔 끼워 움직임"""
import io
import os
import sys
import time
import urllib.parse
import urllib.request

API = "https://api.dicebear.com/9.x/lorelei/png"
CAST = {
    "막내": {"hair": "variant20", "head": "variant01", "nose": "variant01", "설명": "25살 신입, 덥수룩한 머리, 늘 피곤"},
    "부장님": {"hair": "variant25", "head": "variant02", "nose": "variant04", "glasses": "variant03", "glassesProbability": 100, "설명": "55살, 벗어진 머리, 안경, 뿌듯"},
    "팀장님": {"hair": "variant19", "head": "variant03", "nose": "variant02", "glasses": "variant01", "glassesProbability": 100, "설명": "42살 여성, 단발 앞머리, 안경, 빈틈없음"},
    "이대리": {"hair": "variant08", "head": "variant01", "nose": "variant03", "설명": "30살, 올린 머리, 얄미운 선배"},
    "박사원": {"hair": "variant14", "head": "variant04", "nose": "variant05", "설명": "25살 여성 동기, 묶은 머리, 밝고 눈치 빠름"},
}
# 표정: (눈, 눈썹, 입) — Open Peeps 표정 이름을 그대로 받아 씀 (1화 대본 PANELS 의 표정 이름)
FACES = {
    "smile": ("variant12", "variant01", "happy01"), "smileBig": ("variant19", "variant01", "happy05"), "smileLOL": ("variant19", "variant02", "happy16"),
    "awe": ("variant09", "variant05", "sad01"), "hectic": ("variant07", "variant10", "sad06"), "concerned": ("variant13", "variant12", "sad03"),
    "tired": ("variant03", "variant01", "sad05"), "blank": ("variant16", "variant01", "sad09"), "contempt": ("variant08", "variant11", "happy14"),
    "cheeky": ("variant08", "variant11", "happy09"), "suspicious": ("variant03", "variant13", "sad04"), "rage": ("variant07", "variant13", "sad06"),
    "cute": ("variant19", "variant01", "happy03"),
}
TALK = {"happy": "happy05", "sad": "sad01"}     # 말할 때 벌린 입
BLINK = "variant19"                            # 감은 눈
_CACHE = {}


def get(name, face="smile", size=512, talk=False, blink=False):
    eyes, brows, mouth = FACES.get(face, FACES["smile"])
    if talk:
        mouth = TALK["happy" if mouth.startswith("happy") else "sad"] if mouth not in ("happy05", "sad01") else ("happy01" if mouth == "happy05" else "sad05")
    if blink:
        eyes = BLINK
    c = {k: str(v) for k, v in CAST[name].items() if k != "설명"}
    p = dict(c, seed=name, eyes=eyes, eyebrows=brows, mouth=mouth, size=str(size), beardProbability="0", earringsProbability="0",
             frecklesProbability="0", hairAccessoriesProbability="0")
    p.setdefault("glassesProbability", "0")
    url = API + "?" + urllib.parse.urlencode(p)
    if url in _CACHE:
        return _CACHE[url]
    for k in range(3):
        try:
            data = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "youtubeshot/1.0"}), timeout=60).read()
            _CACHE[url] = data
            return data
        except Exception:
            if k == 2:
                raise
            time.sleep(2)


def main(a):
    from PIL import Image, ImageDraw, ImageFont
    out = a[1]
    os.makedirs(out, exist_ok=True)
    font = ImageFont.truetype("/usr/share/fonts/truetype/nanum/NanumSquare_acEB.ttf", 22)
    faces = ["smile", "smileBig", "smileLOL", "awe", "hectic", "concerned", "tired", "blank", "contempt", "suspicious"]
    rows = []
    for name in CAST:
        sh = Image.new("RGB", (220 * len(faces), 260), "white")
        d = ImageDraw.Draw(sh)
        d.text((8, 4), f"{name} — {CAST[name]['설명']}", fill="black", font=font)
        for k, f in enumerate(faces):
            im = Image.open(io.BytesIO(get(name, f, 220))).convert("RGBA")
            sh.paste(im, (k * 220, 30), im)
            d.text((k * 220 + 8, 234), f, fill=(200, 0, 0), font=font)
        rows.append(sh)
        print(name)
    all_ = Image.new("RGB", (rows[0].width, 260 * len(rows)), "white")
    for k, r in enumerate(rows):
        all_.paste(r, (0, 260 * k))
    all_.save(os.path.join(out, "로렐라이_인물_표정_모음.jpg"), quality=88)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
