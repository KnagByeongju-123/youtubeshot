"""「경비실의 김 씨」 등장인물 생김새(영어) — 캐릭터 시트와 장면 그림에서 같은 말을 씀
python 연재/사이다_경비/인물.py job <저장폴더>   → 캐릭터 시트 주문서 (klein_worker, 768×432)"""
import json
import os
import sys

STYLE = "Korean webtoon drama style, clean digital line art, soft cel shading, cinematic dramatic lighting, rich colors"
CAST = {
    "김만석": "a 65-year-old Korean man with short neat gray hair, a calm wise face with gentle wrinkles and kind dark eyes, slim and upright, "
             "wearing a dark navy security guard uniform jacket with silver buttons and a small silver name badge, navy trousers, black shoes, a navy guard cap",
    "강민혁": "a 32-year-old Korean man with glossy black hair swept back, a sharp handsome arrogant face, wearing an expensive slim navy designer suit, "
             "white shirt, dark navy tie, a gold wristwatch, polished brown leather shoes",
    "오소장": "a 50-year-old Korean man, slightly chubby, thinning black hair combed over, round wire glasses, wearing a beige short-sleeved dress shirt "
             "with a brown tie, gray slacks, an ID card on a blue lanyard",
    "한서윤": "a 34-year-old Korean woman with shoulder-length straight black hair, a smart confident face, wearing a light gray blazer over a white blouse, "
             "black slacks, black low heels",
    "윤채린": "a 29-year-old Korean woman with long black hair in a low ponytail, a gentle kind face, wearing a beige knit cardigan over a light blue blouse, "
             "blue jeans, white sneakers",
    "차유나": "a 26-year-old beautiful Korean woman pop singer with long wavy chestnut brown hair, bright big eyes, wearing a pastel pink knit sweater, "
             "white wide-leg pants, white sneakers",
    "강회장": "a 60-year-old Korean man with neatly combed silver-white hair, a dignified stern face, wearing a black three-piece suit with a dark gray tie, "
             "black leather shoes",
    "박군": "a 24-year-old Korean young man with short messy black hair and a friendly face, wearing the same dark navy security guard uniform jacket "
           "with silver buttons, navy trousers, black shoes, a navy guard cap",
}


def main():
    cmd, out = sys.argv[1], sys.argv[2]
    if cmd == "job":
        items = [{"id": f"시트_{n}", "width": 768, "height": 432, "seed": 3000 + k,
                  "prompt": f"{STYLE}. Character model sheet of one character shown three times side by side: front view, side view, back view, "
                            f"full body standing, plain pure white background. Character: {d}. Same face, hair and clothes in all three views. "
                            "Exactly two arms and two legs in each view. No text, no labels."}
                 for k, (n, d) in enumerate(CAST.items())]
        os.makedirs(out, exist_ok=True)
        json.dump({"items": items, "crop_border": False}, open(os.path.join(out, "job.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(len(items))


if __name__ == "__main__":
    main()
