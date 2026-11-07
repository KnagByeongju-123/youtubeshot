"""「붕어빵 엄마의 빌딩」 자수성가 단편 (일본 애니풍) — 컷별 그림 계획 (만드는 법은 「새벽 네 시 떡집」과 같음)
python 연재/붕어빵엄마/붕어빵엄마_단편.py job <저장폴더> [컷번호 ...]  → klein_worker 그림 주문서 job.json
python 연재/붕어빵엄마/붕어빵엄마_단편.py project <그림폴더>         → 프로젝트 파일에 [사진] 줄을 넣음
  - 인물 기준 그림은 앞모습 조각(캐릭터시트/_앞_<인물>.png). 12년 뒤 엄마는 같은 시트 + '흰머리 조금'
  - 떡집 편에서 배운 것: 두 사람 얼굴이 크게 나오는 '손 건네기'는 같은 주인공이 둘로 → 손만 크게 / '손을 감싸 잡기'는 악수로 나옴
  - 학교·가게·사람 이름은 모두 지어낸 것"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SHEETS = os.path.join(HERE, "캐릭터시트")
PROJ = os.path.join(HERE, "붕어빵엄마_프로젝트.json")

STYLE = ("Japanese anime style scene, TV anime screenshot, clean crisp line art, anime cel shading with soft shadows, "
         "realistic human proportions, natural colors, detailed anime background art, warm modern Korean neighborhood drama in winter. Bungeoppang are small hand-sized fish-shaped pastries; never draw a large fish, never a real fish")
LOOK = {
    "엄마": "a 40-year-old slim Korean woman with black hair in a simple low bun, kind tired eyes, no makeup, faded pink padded vest over a gray hooded sweatshirt, dark red cloth apron with pockets, black work pants, gray sneakers",
    "엄마12": "a 52-year-old slim Korean woman with black hair streaked with a little gray in a simple low bun, kind calm eyes, faint wrinkles, faded pink padded vest over a gray hooded sweatshirt, dark red cloth apron, black work pants",
    "준호": "a 10-year-old Korean boy with short neat black hair, navy winter puffer jacket over a light blue hoodie, beige trousers, white sneakers, a small red backpack",
    "청년준호": "a 22-year-old tall slim Korean young man with short neat black hair, calm warm eyes, light gray knit sweater with long sleeves over a white collared shirt, dark navy slacks, brown leather shoes",
    "회장": "a 42-year-old tall Korean woman with glossy wavy brown shoulder-length hair, heavy makeup, red lipstick, haughty face, cream white wool coat over a black turtleneck, black slim trousers, black heeled boots",
    "회장12": "a 54-year-old Korean woman with wavy brown shoulder-length hair, red lipstick, tired worried face with wrinkles, a worn beige coat over a black turtleneck, black trousers",
}
CART = "a small old Korean street food cart with a flat black griddle holding rows of many small palm-sized golden fish-shaped pastries (bungeoppang, each the size of a hand), steam rising, a stack of small paper bags, in front of a Korean elementary school gate on a cold winter morning, bare trees, light snow on the ground"
CORNER = "a windy narrow alley corner near a Korean elementary school in winter, a small old street food cart with a flat griddle holding rows of many small palm-sized golden fish-shaped pastries"
SHOP = "a small cozy Korean bungeoppang shop with a counter, rows of small palm-sized fish-shaped pastry molds, warm lights, a window to a snowy school street"
NEWSHOP = "the ground floor bungeoppang shop of a new five-story building in front of a Korean elementary school, bright and clean, rows of small palm-sized fish-shaped pastry molds behind a counter, a small box by the door"
HOME = "a tiny modest Korean one-room apartment at night with a low table, a small lamp and a thin mattress on the floor"
FRONT = "in front of a new modern five-story building across from a Korean elementary school in winter morning"

# (컷, 문단 번호들, 나오는 인물, (안 씀), 다른 사람 나와도 됨, 장소, 장면(영어), 화면 설명)
CUTS = [
    ("c01", [1], [], False, False, CART, "wide shot of the steaming little street cart in front of the school gate at 7 a.m., warm light, steam. No people", "겨울 아침 학교 앞 손수레"),
    ("c02", [2], ["엄마"], False, False, CART, "the woman pouring batter into the hot fish-shaped bread mold with a calm tired face, steam rising", "붕어빵을 굽는 미숙 씨"),
    ("c03", [3], ["엄마"], False, False, HOME + ", shown as a memory with a soft blue tint", "the woman sitting alone on the floor of the tiny room holding a small framed photo of her late husband to her chest, quiet tears", "남편을 잃은 엄마"),
    ("c04", [4], ["엄마"], False, False, CART, "the woman pushing an old wooden street cart with both hands toward the school gate at dawn, determined face", "남편이 남긴 손수레"),
    ("c05", [5, 6], ["준호", "엄마"], False, False, CART, "the little boy (only he wears the red backpack; his mother wears no backpack) hugging his mother around the waist and burying his face in her apron; she strokes his head with one hand and holds a small warm fish-shaped pastry in the other, soft smile", "엄마 앞치마에 얼굴을 묻은 준호"),
    ("c06", [7, 8], ["회장", "엄마"], False, False, CART, "the tall woman in a cream white coat standing in front of the cart with her arms folded, frowning down with contempt; the cart woman behind the cart lowers her head", "기름 냄새가 나잖아요"),
    ("c07", [9, 10], ["회장"], False, True, "in front of a Korean elementary school gate in winter", "the woman in a cream white coat glancing back at a group of other mothers in winter coats and smirking behind her hand", "다른 엄마들을 돌아보며"),
    ("c08", [11, 12], ["준호", "엄마"], False, False, CART + ", afternoon", "the little boy crying with tears, holding his red backpack in front of him with both hands (he is NOT wearing any backpack, only one backpack in the whole image), childish fish doodles drawn on it in marker; his mother kneels beside him with one hand on his shoulder", "놀림받은 준호"),
    ("c09", [13, 14], ["엄마"], False, True, CART, "two district officers in navy uniforms with clipboards standing at the cart and warning sternly; the cart woman listens with a pale worried face", "구청 단속반"),
    ("c10", [15], ["엄마"], False, False, CORNER, "the woman pushing her heavy cart alone into the cold windy alley corner, her hair blown by the wind, lonely", "바람 부는 골목 모퉁이"),
    ("c11", [16], ["엄마"], False, False, CORNER + ", at night, dark", "the woman crouching beside her cart covered with a tarp at night, face buried in her hands, crying", "처음으로 운 밤"),
    ("c12", [17, 18], ["엄마"], False, False, HOME + ", before dawn", "the woman mixing batter in a big bowl at a small kitchen counter with sweet potatoes and a pumpkin and a bowl of red beans beside her, focused", "남편의 그 맛"),
    ("c13", [19], [], False, False, CORNER, "close-up of a small cardboard box next to the street cart holding a few warm fish-shaped breads wrapped in paper, a handwritten note card taped to it with unreadable writing. No people", "돈이 없는 아이는 그냥 가져가요"),
    ("c14", [20], [], False, True, CORNER, "a skinny 5th-grade boy in an old thin jacket holding a fish-shaped bread from the box and bowing his head politely toward the cart. No main characters", "꾸벅 고개를 숙인 아이"),
    ("c15", [21, 22], ["엄마"], False, True, CORNER, "several children and their mothers lining up happily at the street cart, the cart woman handing out paper bags with a warm smile", "하나둘 모여든 손님"),
    ("c16", [23, 24], ["엄마"], False, False, CORNER + ", freezing cold with snow falling", "the woman wearing two layers of work gloves pouring batter into the mold in the falling snow, breath steaming, red cracked cheeks, enduring", "영하 십오 도의 아침"),
    ("c17", [25], ["엄마", "준호"], False, False, HOME + ", at night", "the boy asleep on the thin mattress; his mother sitting at the low table under a small lamp looking at an open bank passbook with a faint hopeful smile, text unreadable", "멈추지 않고 늘어난 통장"),
    ("c18", [26, 27], ["준호"], False, False, "in front of a small new bungeoppang shop with a plain wooden signboard (no readable letters) on a snowy school street", "the boy with a red backpack standing in front of the little shop looking up at its signboard with shining proud eyes", "준호네 붕어빵"),
    ("c19", [28, 29], [], False, True, FRONT, "wide shot of a new modern five-story building across from the elementary school, a small bungeoppang shop on the ground floor and academy and clinic windows above, plain signs with no readable letters", "십이 년 뒤 학교 앞 오 층 건물"),
    ("c20", [30, 31], ["회장12"], False, False, FRONT, "the middle-aged woman in a worn beige coat shouting into her phone in front of the building, anxious and stressed", "월세가 밀린 백 씨"),
    ("c21", [32, 33, 34], ["회장12"], False, True, FRONT, "the woman in a worn beige coat speaking urgently to a building manager in a gray uniform, who points toward the bungeoppang shop on the ground floor", "건물주님은 저기 계십니다"),
    ("c22", [35, 36], ["엄마12"], False, False, NEWSHOP, "the woman with a little gray in her hair pouring batter into the fish-shaped bread molds behind the counter in her dark red apron, calm", "붕어빵 틀 앞의 건물주"),
    ("c23", [37], ["회장12"], False, False, NEWSHOP, "close-up of the woman in a worn beige coat frozen in shock at the shop door, eyes wide, her phone slipping from her hand", "설마, 준호 어머니가"),
    ("c24", [38, 39], ["엄마12"], False, False, NEWSHOP, "the woman taking off her work gloves slowly and raising her head with a calm dignified face", "십이 년 동안 붕어빵 팔아서"),
    ("c25", [40, 41], ["회장12"], False, False, NEWSHOP, "the woman in a worn beige coat bowing her head low in shame and speaking in a small voice", "그때는 정말 몰랐어요"),
    ("c26", [42, 43], ["청년준호"], False, False, NEWSHOP, "the tall young man in a gray sweater opening the shop door and walking in with a bright smile, holding a certificate folder", "스물두 살 준호"),
    ("c27", [44], ["청년준호", "엄마12"], False, False, NEWSHOP, "the young man proudly showing an open scholarship certificate to his mother behind the counter, she covers her mouth with joy", "의과대학 장학금"),
    ("c28", [45, 46], ["청년준호"], False, False, NEWSHOP, "the young man bowing his head politely in a quiet greeting with a calm face, no anger", "미움이 아니었습니다"),
    ("c29", [47, 48], ["엄마12"], False, False, NEWSHOP, "the woman behind the counter holding out a warm paper bag of fish-shaped bread with a gentle firm face", "제 조건이에요"),
    ("c30", [49], ["회장12"], False, False, NEWSHOP, "the woman in a worn beige coat holding the paper bag of fish-shaped bread with both hands against her chest, head bowed, eyes wet", "고개를 들지 못한 백 씨"),
    ("c31", [50], [], False, False, NEWSHOP + ", afternoon", "close-up of the small box by the shop door with warm fish-shaped breads and a handwritten note card with unreadable writing. No people", "여전히 그 상자"),
    ("c32", [51], [], False, True, NEWSHOP + ", afternoon", "a small elementary school child in a winter jacket picking up a fish-shaped bread from the box and bowing politely. No main characters", "꾸벅 숙인 아이"),
    ("c33", [52], ["엄마12"], False, True, NEWSHOP + ", afternoon", "the woman crouching down to slip one more warm fish-shaped bread into a small child's jacket pocket with a tender smile", "하나 더 넣어 준 붕어빵"),
    ("c34", [53], [], False, True, "a snowy winter street in front of a Korean elementary school at sunset, the new building with the warm bungeoppang shop on the ground floor", "wide shot of the warm glowing shop with steam rising into the cold air, children walking home, snow falling softly. No main characters", "십이 년이었습니다"),
]


def paragraphs(story):
    return [p.strip() for p in re.split(r"\n\s*\n", story) if p.strip() and not p.strip().startswith("[사진")]


def ref_of(nm):
    return os.path.join(SHEETS, "_앞_" + nm.replace("12", "") + ".png")


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
        p += "Other people are ordinary Korean parents, children and passers-by in everyday clothes who look clearly different from the main characters. "
    p += f"Scene: {desc}. Setting: {place}. "
    p += "Cinematic composition, full-bleed image, no border, no frame, no paper edges. No speech bubbles, no readable text, no letters, no logos, no signs with writing."
    return p


def main():
    cmd, folder = sys.argv[1], sys.argv[2]
    if cmd == "job":
        only = set(sys.argv[3:])
        items = [{"id": c[0], "width": 1024, "height": 576, "seed": 900 + k, "prompt": prompt(c), "refs": [ref_of(nm) for nm in c[2]]}
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
