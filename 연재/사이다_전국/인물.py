"""「전국시대에 떨어진 낙제생」 등장인물 생김새(영어) — 캐릭터 시트와 장면 그림에서 같은 말을 씀
python 연재/사이다_전국/인물.py job <저장폴더> [이름 ...]   → 캐릭터 시트 주문서 (klein_worker, 1024×512, 앞·왼·오른·뒤 4면)
python 연재/사이다_전국/인물.py split <저장폴더>          → 시트_<이름>.png 를 흰 틈으로 잘라 앞_·왼_·오른_·뒤_<이름>.png (장면 기준 그림)
여자 인물은 매력적으로 (사용자 요청 2026-10-29: 또렷한 큰 눈·고운 피부·윤기 나는 머리·몸에 맞는 옷, 노출 없이 웹툰 여주인공 느낌)"""
import json
import os
import sys

STYLE = "Korean webtoon drama style, clean digital line art, soft cel shading, cinematic dramatic lighting, rich colors"
PRETTY = "very beautiful, big clear sparkling eyes with long lashes, flawless fair skin, glossy hair, elegant slim figure, charming webtoon heroine look"
UNIFORM_M = "a Japanese high school uniform: navy blazer with a small gold school emblem, white shirt, dark red striped tie, gray trousers, brown loafers"
CAST = {
    "한도윤": f"a 17-year-old Korean boy, slim, neat short black hair with soft bangs, kind bright dark eyes, a clean earnest face, wearing {UNIFORM_M}",
    "미나미": f"a 17-year-old Japanese girl, {PRETTY}, waist-length straight black hair with see-through bangs, a gentle warm smile, "
             "wearing a Japanese high school uniform: navy blazer with a small gold school emblem, white shirt, red ribbon bow, navy pleated knee-length skirt, "
             "navy knee socks, brown loafers",
    "유키": f"a 17-year-old Japanese princess of the 1560 Sengoku era, {PRETTY}, the same face as a modern schoolgirl, very long straight black hair reaching down to her waist "
           "with see-through bangs, the long hair loosely tied at the back of her waist with a white ribbon, "
           "a small silver cherry blossom hairpin, wearing a light pink silk kimono with a small cherry blossom pattern, a deep crimson hakama skirt, "
           "a brown leather archery arm guard on her left forearm, white tabi socks and straw sandals",
    "사쿠라": f"a 20-year-old Japanese female ninja (kunoichi) of the 1560 Sengoku era, {PRETTY}, sharp elegant almond eyes, a high ponytail of glossy black hair, "
             "athletic, wearing a fitted black ninja outfit with a dark purple sash, her whole face uncovered and clearly visible with no mask over her mouth or nose, a black scarf loosely around her neck, "
             "black arm wraps, black tabi boots, a short sword strapped on her back",
    "타쿠야": f"a 17-year-old Japanese boy, tall, styled light brown dyed hair, a smug handsome face with a sneer, wearing {UNIFORM_M} worn loosely with the tie loosened, "
             "an expensive silver wristwatch",
    "스기모토": "a 55-year-old Japanese samurai castle lord of the 1560 Sengoku era, a stern dignified face, gray-streaked black hair in a samurai topknot, a short gray beard, "
             "wearing a dark blue haori jacket with a white family crest, gray hakama, a katana at his waist",
    "쿠로다": "a 45-year-old Japanese samurai retainer of the 1560 Sengoku era, thin, narrow sly eyes, a thin mustache, black hair in a samurai topknot, "
            "wearing a dark brown haori jacket over a black kimono, black hakama, a katana at his waist",
    "야마다선생님": "a 40-year-old Japanese woman high school history teacher, shoulder-length black hair, thin rimmed glasses, a kind intelligent face, "
               "wearing a beige cardigan over a white blouse, a navy knee-length skirt, low black shoes",
    "할아버지": "a 75-year-old Korean grandfather, short white hair, a warm wrinkled smiling face, wearing a gray knit cardigan over a white shirt, brown trousers",
    "신관": "a 75-year-old Japanese Shinto priest, white hair and a white beard, a gentle wise face, wearing a white kariginu priest robe, pale blue hakama "
          "and a tall black eboshi hat",
}
VIEWS = ("앞", "왼", "오른", "뒤")    # 시트 왼쪽부터: 앞모습, 왼쪽을 보는 옆모습, 오른쪽을 보는 옆모습, 뒷모습


def main():
    cmd, out = sys.argv[1], sys.argv[2]
    names = sys.argv[3:] or list(CAST)
    if cmd == "job":
        items = [{"id": f"시트_{n}", "width": 1024, "height": 512, "seed": 6000 + list(CAST).index(n),
                  "prompt": f"{STYLE}. Character turnaround model sheet of ONE character shown exactly four times in a row, evenly spaced with white gaps, "
                            f"from left to right: front view, side view facing left, side view facing right, back view. Full body standing, head to toe visible, "
                            f"plain pure white background. Character: {CAST[n]}. Same face, hair and clothes in all four views. "
                            "Exactly two arms and two legs in each view. No text, no labels."}
                 for n in names]
        os.makedirs(out, exist_ok=True)
        json.dump({"items": items, "crop_border": False}, open(os.path.join(out, "job.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(len(items))
    elif cmd == "split":
        import numpy as np
        from PIL import Image
        for n in names:
            f = os.path.join(out, f"시트_{n}.png")
            if not os.path.exists(f):
                continue
            im = Image.open(f).convert("RGB")
            a = np.asarray(im).astype(int)
            ink = ((255 - a).sum(axis=2) > 60).sum(axis=0) > 2      # 세로줄마다 그림이 있는지
            runs, start = [], None
            for x, v in enumerate(list(ink) + [False]):
                if v and start is None:
                    start = x
                elif not v and start is not None:
                    if x - start > 25:
                        runs.append((start, x))
                    start = None
            if len(runs) != 4:
                print(n, "나누기 실패: 모습", len(runs), "개 → 직접 확인")
                continue
            # 셋째 모습은 오른쪽 옆모습 대신 비스듬한 앞모습으로 그려지는 일이 많아 쓰지 않음 → 오른 = 왼쪽 옆모습을 좌우로 뒤집음
            cut = [im.crop((max(0, x0 - 6), 0, min(im.width, x1 + 6), im.height)) for x0, x1 in runs]
            for v, c in (("앞", cut[0]), ("왼", cut[1]), ("오른", cut[1].transpose(Image.FLIP_LEFT_RIGHT)), ("뒤", cut[3])):
                c.save(os.path.join(out, f"{v}_{n}.png"))
            print(n, "4면 저장")


if __name__ == "__main__":
    main()
