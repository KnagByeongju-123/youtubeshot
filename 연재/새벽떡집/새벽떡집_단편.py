"""「새벽 네 시 떡집」 자수성가 단편 (일본 애니풍) — 컷별 그림 계획 (만드는 법은 「화성 3호기 정비반장」과 같음)
python 연재/새벽떡집/새벽떡집_단편.py job <저장폴더> [컷번호 ...]  → klein_worker 그림 주문서 job.json
python 연재/새벽떡집/새벽떡집_단편.py project <그림폴더>         → 프로젝트 파일에 [사진] 줄을 넣음 (나레이션 문단은 그대로)
  - 인물 기준 그림은 앞모습 조각(캐릭터시트/_앞_<인물>.png)
  - 시장·가게·사람 이름은 모두 지어낸 것"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SHEETS = os.path.join(HERE, "캐릭터시트")
PROJ = os.path.join(HERE, "새벽떡집_프로젝트.json")

STYLE = ("Japanese anime style scene, TV anime screenshot, clean crisp line art, anime cel shading with soft shadows, "
         "realistic human proportions, natural colors, detailed anime background art, warm modern Korean traditional market drama")
LOOK = {
    "도윤": "a 45-year-old Korean man with short neat black hair graying at the temples, tired warm eyes, light stubble, white cotton work shirt with rolled sleeves, dark navy canvas apron, dark gray trousers, black rubber kitchen boots",
    "아내": "a 43-year-old Korean woman with black hair tied back in a low ponytail, gentle smile, pale yellow knit cardigan over a white t-shirt, light beige cloth apron, blue jeans",
    "딸": "a 15-year-old Korean girl with a short black bob and straight bangs, navy middle school uniform blazer, white shirt with a small red ribbon tie, navy pleated skirt, black knee socks",
    "건물주": "a 60-year-old short heavy-set Korean man with slicked-back gray hair, a thick gray mustache, narrow sneering eyes, shiny brown leather jacket over a black turtleneck, black slacks, a thick gold chain bracelet",
    "본부장": "a 36-year-old tall Korean woman with long black hair in a low ponytail, sharp confident eyes, light red lipstick, charcoal gray pantsuit with a white silk blouse",
}
SHOP = "inside a small old Korean rice cake shop (tteok shop) in a traditional market: wooden counters, glass display trays of colorful rice cakes, big steaming bamboo steamers, a large wooden pounding board, warm yellow lights"
SHOP_DAWN = SHOP + ", before dawn, dark blue outside the shop window, steam rising"
ALLEY = "a narrow alley of an old Korean traditional market with small shops, shutters, hanging lamps and plastic awnings"
ALLEY_DAWN = ALLEY + ", before dawn, all shops dark and shuttered except one warmly lit little shop at the end"
HOME = "a small modest Korean apartment living room at night with a low table, a sofa and family photos"
NOTE = "the paper pages are covered in tiny handwriting too small and blurry to read"

# (컷, 문단 번호들, 나오는 인물, (안 씀), 다른 사람 나와도 됨, 장소, 장면(영어), 화면 설명)
CUTS = [
    ("c01", [1], [], False, False, ALLEY_DAWN, "wide shot of the dark sleeping market alley at 4 a.m., only one small shop at the end glowing warmly. No people", "새벽 네 시 한빛 시장"),
    ("c02", [2], ["도윤"], False, False, SHOP_DAWN, "the man washing white rice by hand in a huge metal basin full of water, sleeves rolled up, focused", "쌀을 씻는 도윤 씨"),
    ("c03", [3], ["도윤"], False, True, "a gray office building lobby, shown as a memory with a soft cool blue tint", "the man dressed as an office worker in a white dress shirt and a navy necktie, wearing NO apron, carrying a cardboard box of his desk belongings past rows of office desks with computers, defeated face, a few office workers in suits in the background", "문 닫은 회사"),
    ("c04", [4], [], False, False, SHOP + ", dusty and quiet, morning light", "close-up of an old worn wooden rice cake pounding board and a wooden mallet on the counter of the empty dusty shop, a small old notebook beside them. No people", "아버지가 남긴 떡판"),
    ("c05", [5, 6], ["도윤", "아내"], False, False, SHOP + ", dusty and quiet", "the man speaking earnestly to his wife; she quietly holds his right hand gently between both of her hands, eyes moist; his left arm hangs at his side; not a handshake", "우리 떡집 해 보자"),
    ("c06", [7], ["도윤"], False, False, SHOP, "the man alone behind the counter counting a few coins and small bills, the display trays nearly full of unsold rice cakes, worried face", "하루 삼만 원"),
    ("c07", [8], [], False, True, "the entrance of a Korean traditional market with a bright modern franchise rice cake shop with a glowing signboard with no letters", "a long line of customers going into the bright shiny franchise shop at the market entrance. No main characters", "프랜차이즈 가게의 줄"),
    ("c08", [9, 10], ["건물주", "도윤"], False, False, SHOP, "the short heavy-set man in a brown leather jacket and gold bracelet standing in the shop doorway pointing his finger and demanding rent arrogantly, the shop man standing behind the counter with his head lowered", "월세 올리네"),
    ("c09", [11, 12], ["건물주"], False, False, SHOP, "the heavy-set man in the brown leather jacket holding up one rice cake between two fingers and sneering with contempt", "촌스러운 떡"),
    ("c10", [13], ["딸"], False, False, HOME, "the schoolgirl coming home in tears, wiping her eyes with her sleeve, school bag hanging from one shoulder", "울며 들어온 하은이"),
    ("c11", [14], ["도윤"], False, False, HOME + ", a closed bedroom door", "the man standing alone in front of a closed bedroom door with one hand raised but not knocking, sad face", "닫힌 방문 앞"),
    ("c12", [15], ["도윤"], False, False, SHOP + ", late at night under a single lamp", "the man sitting at the counter at night opening his late father's small worn notebook, the first page showing a few lines of clumsy handwriting, " + NOTE, "쌀은 거짓말을 안 한다"),
    ("c13", [16], [], False, False, "on a wooden counter under a warm lamp", "close-up of the open old notebook pages full of dense handwriting and small hand-drawn rice cake sketches, a few grains of rice on the page, " + NOTE + ". No people", "빼곡한 아버지의 수첩"),
    ("c14", [17], ["도윤"], False, False, SHOP_DAWN, "the man tying his navy apron tightly with a determined face, steam rising behind him", "새로운 원칙"),
    ("c15", [18], ["도윤"], False, False, SHOP_DAWN, "the man swinging a big wooden mallet down onto a mound of steamed rice dough on the wooden pounding board, steam and motion, strong and focused", "떡메를 치는 새벽"),
    ("c16", [19], ["도윤"], False, True, ALLEY + ", evening", "the man handing a small paper bag of rice cakes to a hunched elderly woman with a cart of cardboard boxes, a market night guard smiling beside her", "나눠 드리는 떡"),
    ("c17", [20, 21], ["도윤"], False, False, "in front of the rice cake shop counter in the market alley on a rainy morning, the alley empty", "a small hunched elderly Korean grandmother in a worn brown padded jacket, soaked by the rain with no umbrella, standing OUTSIDE in front of the counter; the shop man stands INSIDE behind the counter looking at her with concern. Only these two people in the whole image, no customers, no staff", "비 오는 아침의 할머니"),
    ("c18", [22], ["도윤"], False, False, "the shop counter on a rainy morning", "close-up from behind the counter: an elderly grandmother's wrinkled hand (only her hand and sleeve visible at the edge) holding out three crumpled green Korean paper bills; the shop man takes them with both hands, his eyes red and wet with tears. The shop man appears only once", "꼬깃꼬깃한 천 원 세 장"),
    ("c19", [23], [], False, True, "a hospital nurses' station", "smiling nurses in scrubs sharing boxes of colorful rice cakes at the nurses' station. No main characters", "간호사실의 떡 주문"),
    ("c20", [24], ["도윤", "아내"], False, True, SHOP, "the husband and wife busily packing many boxes of rice cakes together, smiling, phone orders on a notepad", "입에서 입으로"),
    ("c21", [25], ["딸"], False, True, ALLEY + ", early morning", "a long line of customers waiting in front of the little rice cake shop at dawn, the schoolgirl in uniform watching quietly from far away at the corner", "가게 앞의 줄"),
    ("c22", [26, 27], ["건물주", "본부장"], False, False, SHOP, "the heavy-set man in the brown leather jacket walking into the shop with the tall woman in a charcoal pantsuit beside him, smug grin", "본부장과 함께 온 건물주"),
    ("c23", [28, 29], ["본부장", "도윤"], False, False, SHOP, "the tall woman in a charcoal pantsuit holding out a business card with a polite cool smile, the shop man behind the counter", "가게를 비워 주시면"),
    ("c24", [30, 31], ["건물주"], False, False, SHOP, "the heavy-set man in the brown leather jacket leaning in and waving his hand dismissively, urging with a greedy grin", "받을 때 받아"),
    ("c25", [32, 33], ["도윤"], False, False, SHOP, "the shop man calmly placing a plate of fresh soft injeolmi rice cakes covered in golden soybean powder on the counter, steam from the bamboo steamer behind him", "새벽에 만든 인절미"),
    ("c26", [34, 35], ["본부장"], False, False, SHOP, "the tall woman in a charcoal pantsuit taking a bite of a golden injeolmi rice cake, her eyes widening in surprise, frozen mid-bite", "한 입 먹고 멈춘 손"),
    ("c27", [36, 37], ["도윤"], False, False, SHOP, "the shop man answering calmly with an honest steady face, his hands resting on the counter", "하루 삼백 개"),
    ("c28", [38, 39], ["본부장"], False, False, SHOP, "the tall woman in a charcoal pantsuit staring at her smartphone screen with wide eyes, the screen showing a simple bar chart with no readable text", "설문 일등은 새벽떡집"),
    ("c29", [40, 41], ["본부장", "건물주"], False, False, SHOP, "the tall woman in a charcoal pantsuit turning firmly toward the heavy-set man in the brown leather jacket and speaking, he looks startled", "레시피를 사러 왔습니다"),
    ("c30", [42, 43], ["본부장"], False, False, SHOP, "the tall woman in a charcoal pantsuit placing a contract document on the counter with both hands, bowing slightly with respect, the paper text blurry and unreadable", "계약금 일억"),
    ("c31", [44], ["건물주"], False, False, SHOP, "close-up of the heavy-set man in the brown leather jacket with his mouth hanging wide open in shock", "벌어진 입"),
    ("c32", [45, 46], ["도윤"], False, False, SHOP, "the shop man shaking his head slowly and speaking with a firm principled face, one hand on the contract paper", "한 가지 조건"),
    ("c33", [47, 48], ["본부장"], False, False, SHOP, "the tall woman in a charcoal pantsuit smiling warmly and nodding with her eyes closed, respect on her face", "그래서 맛있는 거군요"),
    ("c34", [49, 50], ["건물주"], False, False, SHOP + ", afternoon light", "the heavy-set man in the brown leather jacket alone at the counter, rubbing his hands together with an awkward fawning smile, hiding his gold bracelet under his sleeve", "강 대표님"),
    ("c35", [51, 52], ["도윤"], False, False, SHOP + ", afternoon light", "the shop man holding out a plate of injeolmi rice cakes with a calm gentle smile", "그냥 드시고 가세요"),
    ("c36", [53], ["건물주"], False, False, SHOP + ", afternoon light", "the heavy-set man in the brown leather jacket eating a rice cake and lowering his head in shame, quiet", "고개 숙인 건물주"),
    ("c37", [54], [], False, True, "a bright modern rice cake franchise shop interior", "a clean bright franchise shop counter displaying golden injeolmi rice cakes with a small wooden sign and happy customers buying them, no readable text. No main characters", "전국 백이십 곳"),
    ("c38", [55], [], False, False, ALLEY_DAWN, "the same little rice cake shop at the end of the dark market alley at 4 a.m., its warm light on as always. No people", "변하지 않은 새벽"),
    ("c39", [56, 57], ["딸", "도윤"], False, False, SHOP_DAWN, "the schoolgirl wearing a small apron over her uniform washing rice in the big basin next to her father, both smiling, steam rising", "함께 쌀을 씻는 하은이"),
    ("c40", [58], ["도윤", "딸"], False, False, SHOP_DAWN, "the man handing his late father's old notebook to his daughter with both hands, she receives it carefully with shining eyes", "딸에게 건넨 수첩"),
    ("c41", [59], [], False, False, "on a wooden counter at dawn with soft first sunlight", "close-up of the old notebook's first page with two lines of handwriting in two different handwritings, a plate of golden injeolmi beside it, " + NOTE + ". No people", "새벽도, 거짓말을 안 한다"),
]


def paragraphs(story):
    return [p.strip() for p in re.split(r"\n\s*\n", story) if p.strip() and not p.strip().startswith("[사진")]


def ref_of(nm):
    return os.path.join(SHEETS, "_앞_" + nm + ".png")


def prompt(cut):
    cid, _, who, _, crowd, place, desc, _ = cut
    people = list(who)
    looks = [f"character from reference image {k + 1}: {LOOK[nm]}" for k, nm in enumerate(who)]
    p = f"{STYLE}. "
    if looks:
        p += "In the scene: " + "; ".join(looks) + ". "
    if people:
        p += "Each character appears only once, exactly two arms and two legs and five fingers on each hand, head and face turned the same direction as the body. "
    if not people:
        p += "No main characters. "
    if not crowd:
        p += "No other people besides those described in the scene. "
        if len(people) == 1:
            p += "Exactly one person in the whole image, no twin, no copy, no reflection. "
    else:
        p += "Other people are ordinary Korean market shoppers and passers-by in everyday clothes who look clearly different from the main characters. "
    p += f"Scene: {desc}. Setting: {place}. "
    p += "Cinematic composition, full-bleed image, no border, no frame, no paper edges. No speech bubbles, no readable text, no letters, no logos, no signs with writing."
    return p


def main():
    cmd, folder = sys.argv[1], sys.argv[2]
    if cmd == "job":
        only = set(sys.argv[3:])
        items = [{"id": c[0], "width": 1024, "height": 576, "seed": 700 + k, "prompt": prompt(c), "refs": [ref_of(nm) for nm in c[2]]}
                 for k, c in enumerate(CUTS) if not only or c[0] in only]
        os.makedirs(folder, exist_ok=True)
        out = os.path.join(folder, "job.json")
        json.dump({"items": items, "crop_border": True}, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(out, len(items), "cuts")
    elif cmd == "project":
        p = json.load(open(PROJ, encoding="utf-8"))
        paras = paragraphs(p["story"])
        first = {c[1][0]: c for c in CUTS}
        assert sorted(n for c in CUTS for n in c[1]) == list(range(1, len(paras) + 1)), "문단 번호가 대본과 안 맞음"
        out = []
        for i, para in enumerate(paras, 1):
            if i in first:
                c = first[i]
                out.append(f"[사진: {os.path.join(folder, c[0] + '.png')} | {c[7]} | AI 생성 그림 (FLUX.2 klein) | ]")
            out.append(para)
        p["story"] = "\n\n".join(out)
        p["img_source"] = "그림: 애니 일러스트"
        p["autophoto"] = False
        p["cast"] = [{"name": nm, "look": LOOK[nm], "sheet": os.path.join(SHEETS, nm + ".png")} for nm in LOOK]
        json.dump(p, open(PROJ, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(PROJ, len(CUTS), "cuts")


if __name__ == "__main__":
    main()
