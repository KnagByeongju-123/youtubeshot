"""「바다를 아는 아이」 등장인물 생김새(영어) — 캐릭터 시트와 장면 그림에서 같은 말을 씀
python 연재/사이다_한산/인물.py job <저장폴더> [이름 ...]   → 캐릭터 시트 주문서 (klein_worker, 1024×512, 앞·왼·오른·뒤 4면)
python 연재/사이다_한산/인물.py split <저장폴더>          → 시트_<이름>.png 를 흰 틈으로 잘라 앞_·왼_·오른_·뒤_<이름>.png (오른 = 왼쪽 옆모습을 뒤집음)
여자 인물은 매력적으로 (사용자 요청: 또렷한 큰 눈·고운 피부·윤기 나는 머리·몸에 맞는 옷, 노출 없이 웹툰 여주인공 느낌)
조선 인물은 1592년 조선 옷 (일본 옷과 섞이지 않게 'Korean Joseon' 을 꼭 적음)"""
import json
import os
import sys

STYLE = "Korean webtoon drama style, clean digital line art, soft cel shading, cinematic dramatic lighting, rich colors"
PRETTY = "very beautiful, big clear sparkling eyes with long lashes, flawless skin, glossy hair, elegant slim figure, charming webtoon heroine look"
TRACK = "a navy blue Korean high school tracksuit (zip-up jacket with two white stripes on the sleeves, matching track pants) and white sneakers"
CAST = {
    "이서진": f"an 18-year-old Korean girl, {PRETTY}, a lightly sun-tanned healthy face, a high ponytail of glossy black hair, bright determined eyes, wearing {TRACK}",
    "태윤": f"an 18-year-old Korean boy, tall, neat short black hair with a side part, a smug clever face, wearing {TRACK}, a black smartwatch",
    "연화": f"a 22-year-old Korean woman archer of the Joseon dynasty in 1592, {PRETTY}, sharp elegant eyes, long black hair in one thick braid down her back "
           "tied with an indigo ribbon, wearing a white Korean hanbok jeogori top and an indigo-blue hanbok skirt tied up at the knees for moving, "
           "white cloth leggings, straw shoes, a leather arm guard on her left forearm, a quiver of arrows on her back",
    "돌쇠": "a 13-year-old skinny Korean boy of the Joseon dynasty in 1592, a sun-tanned cheeky face, short messy black hair tied in a small topknot with a cloth strip, "
           "wearing a patched faded beige hemp jeogori top and knee-length hemp trousers, barefoot",
    "이순신": "a 47-year-old Korean Joseon dynasty naval admiral in 1592, a calm dignified wise face with a neat black mustache and a short beard, "
             "wearing a dark red Joseon military robe with traditional Korean lamellar armor plates, a black wide-brimmed Joseon military hat with a red tassel, "
             "a long Korean sword at his waist, black boots",
    "최역관": "a 45-year-old Korean Joseon dynasty interpreter in 1592, plump, small shifty eyes, a thin mustache, "
             "wearing a fine pale green silk Korean hanbok robe (durumagi) and a black horsehair gat hat",
    "할머니": "a 75-year-old Korean grandmother from a seaside town, short permed gray hair, a warm deeply wrinkled sun-tanned face, "
             "wearing a lavender knit cardigan over a flowered blouse, loose dark trousers, rubber slippers",
    "김천손": "a 60-year-old Korean Joseon dynasty cattle herder in 1592, a kind weathered sunburned face, a gray beard, "
             "wearing a worn white hemp jeogori and trousers, a straw hat hanging on his back, straw shoes, holding a wooden staff",
}
VIEWS = ("앞", "왼", "오른", "뒤")


def main():
    cmd, out = sys.argv[1], sys.argv[2]
    names = sys.argv[3:] or list(CAST)
    if cmd == "job":
        items = [{"id": f"시트_{n}", "width": 1024, "height": 512, "seed": 8000 + list(CAST).index(n),
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
