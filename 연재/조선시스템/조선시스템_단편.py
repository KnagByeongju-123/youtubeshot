"""「조선에 떨어진 미래 의사」 3부작 (수묵 담채) — 컷별 그림 계획
python 연재/조선시스템/조선시스템_단편.py job <부> <저장폴더> [컷번호 ...]  → klein_worker 그림 주문서 job.json
python 연재/조선시스템/조선시스템_단편.py project <부> <그림폴더>         → 그 부 프로젝트 파일에 [사진] 줄을 넣음
  - 인물 기준 그림 = 시트 앞모습 + 그 사람 모자를 위에 얹은 한 장 (캐릭터시트/_앞_<인물>_모자.png, 수묵담채화.md 모자 규칙)
    임금 = 익선관(_모자_익선관.png), 판서 = 사모(_모자_사모.png), 현 = 갓. 방 안에 누운 현은 맨머리 상투(_앞_현.png)
  - 시트 없는 조연(박 수령·관찰사)은 사모 앞모습(등장인물/조선/_관모/사모_앞.png)만 넣고 외모를 글로
  - 시스템 창 = 글자 없는 푸른빛 창 (글자가 그려지지 않게)
  - 인물·고을·관직 이름은 모두 지어낸 것"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SHEETS = os.path.join(HERE, "캐릭터시트")
CAPS = os.path.join(ROOT, "등장인물", "조선", "_관모")

STYLE = ("traditional East Asian ink wash painting with light color washes: expressive black ink brush outlines, "
         "rich clear colors applied as transparent watercolor washes, rice paper texture, historically accurate Joseon Korean costumes "
         "and architecture, Korean Joseon dynasty hanbok - NOT Chinese hanfu, NOT Japanese kimono, no red seal stamp, no calligraphy")
STYLE_2045 = ("traditional East Asian ink wash painting with light color washes: expressive black ink brush outlines, "
              "rich clear colors applied as transparent watercolor washes, rice paper texture, a modern 2045 research laboratory, no red seal stamp, no calligraphy")
CAP_LINE = "Each person and the cap shown above him in his reference image are one: he always wears exactly that cap. "
SAMO = "black brimless two-tiered samo cap with two flat oval wings sticking out to the left and right"
LOOK = {
    "현": "a 20-year-old slim Korean young man, a poor fallen-noble scholar, young clean-shaven face, calm intelligent eyes, black gat hat with a wide flat round brim and a tall narrow crown, a faded light gray-white dopo robe with small patches, thin dark cord belt, straw sandals",
    "현_맨머리": "a 20-year-old slim Korean young man, young clean-shaven face, calm intelligent eyes, bareheaded with his black hair in a small topknot and a thin black headband, a plain white undergarment jeogori",
    "어머니": "a 45-year-old thin Korean woman, gentle tired face, black hair in a low bun with a plain wooden hairpin, a faded beige jeogori jacket and a dark navy chima skirt",
    "판서": "a 56-year-old heavy-set Korean high minister with a round belly, gray mustache and short gray beard, narrow greedy eyes, a dark crimson official robe with one square crane badge on the chest, " + SAMO,
    "임금": "a 40-year-old Korean king, tall, calm dignified face, neat short black beard, a bright red royal robe with golden round dragon badges on the chest and shoulders, the same black ikseongwan cap with the same shape as in the reference image, jade belt",
    "도현": "a 54-year-old Korean scientist, short neat gray-black hair, thin rimless glasses, kind tired eyes, a white lab coat over a light blue shirt",
    "수령": "a 35-year-old thin Korean magistrate with a thin black mustache and sly narrow eyes, a dark blue official robe with a square badge on the chest, " + SAMO,
    "관찰사": "a 60-year-old dignified Korean governor with a long white beard and stern wise eyes, a dark green official robe, " + SAMO,
}
REF = {
    "현": "_앞_현_모자.png", "현_맨머리": "_앞_현.png", "어머니": "_앞_어머니.png", "판서": "_앞_판서_모자.png",
    "임금": "_앞_임금_모자.png", "도현": "_앞_도현.png",
    "수령": "_앞_수령_모자.png", "관찰사": "_앞_관찰사_모자.png",
}
CAPPED = {"현", "판서", "임금", "수령", "관찰사"}

LAB = "a modern infectious disease research laboratory in Seoul in the year 2045 at night, glass test tubes, a microscope, cold white lights"
ROOM = "inside a small poor thatched-roof Joseon house room, paper lattice door, worn straw mat floor, a thin old quilt"
YARD = "the dirt yard of a small poor thatched-roof Joseon house with a brushwood gate and a low stone wall"
VILLAGE = "a poor Joseon farming village of thatched-roof houses with stone wells and dirt paths, early spring"
ENTRY = "the entrance of a poor Joseon village with a dirt road, a big old tree and thatched houses behind"
FENCE = "a dirt road outside a Joseon village blocked by a rough wooden barricade fence"
STORE = "a large wooden storehouse behind a Joseon county government office, heavy wooden doors"
MANSION = "a grand Joseon tiled-roof mansion room in Hanyang at night, a low lacquered table, folding screen, candlelight"
PANEL = "a glowing translucent blue rectangular window of light floating in the air, filled only with soft light and thin abstract lines, completely blank with no letters, no numbers, no symbols"
VILLAGERS = "Other people are poor Joseon commoners in plain white and beige hanbok, men with small topknots and headbands, women with hair in buns, who look clearly different from the main characters. None of the villagers wear a gat hat: only the young scholar wears the tall black gat. "
CLERKS = "Other people are county clerks in plain black-gray hanbok with small black hats, who look clearly different from the main characters. "

# 부마다 (컷, 문단 번호들, 나오는 인물, 다른 사람 문장(없으면 ""), 장소, 장면(영어), 화면 설명)
CUTS = {1: [
    ("c01", [1], ["도현"], "", LAB, "the scientist working late at night at a lab bench, carefully holding a small glass vial and looking into a microscope, tired but focused", "2045년 감염병 연구소"),
    ("c02", [2], ["도현"], "", LAB, "a glass tube shattering on the lab bench with bright sparks and a blinding white flash of light; the scientist falling backward, arm raised against the light", "깨진 유리관과 하얀 빛"),
    ("c03", [3], ["현_맨머리"], "", ROOM + ", cold early morning light through the paper door", "the young man lying on a thin old quilt on the floor, just opening his eyes, confused, looking at the low ceiling", "초가집에서 눈을 뜨다"),
    ("c04", [4], ["현_맨머리"], "", ROOM, "the young man sitting up on the quilt and staring at his own two smooth young hands raised in front of him, astonished; in the air before him " + PANEL, "스무 살의 손과 푸른 창"),
    ("c05", [5], ["현_맨머리"], "", ROOM, "close view: the young man's astonished face lit by blue light from " + PANEL + " floating in front of him", "시스템이 시작됩니다"),
    ("c06", [6], ["현_맨머리"], "", ROOM, "the young man gazing at " + PANEL + " with one thin glowing red line of light at its bottom edge, his face serious", "첫 번째 임무, 어머니를 살리십시오"),
    ("c07", [7], ["어머니", "현_맨머리"], "", ROOM, "the thin mother lying on a mat in the corner of the room with a fever, coughing, sweat on her forehead; the young man turning toward her in alarm", "열에 들뜬 어머니"),
    ("c08", [8], ["현_맨머리"], "", ROOM + ", shown as a faded memory with a soft sepia tint", "the young man sitting alone in the bare poor room at a small low wooden writing desk with one ink brush and a black inkstone on it, the room nearly empty, a lonely quiet mood", "삼대째 벼슬을 못 한 집안"),
    ("c09", [9], ["현"], VILLAGERS, YARD, "worried villagers standing outside the brushwood gate shaking their heads and covering their mouths; the young man standing in the yard facing them", "괴질이었습니다"),
    ("c10", [10], ["현"], "", YARD + ", with a faint translucent ghost image of a modern laboratory in the sky behind him like a memory", "the young man standing in thought with a sharp determined look, remembering", "콜레라와 똑같은 병"),
    ("c11", [11], ["현"], "", YARD, "the young man boiling well water in a big black iron pot over a wood fire, adding a handful of salt from a small bowl, a small clay honey jar beside him, steam rising", "끓인 물에 소금과 꿀"),
    ("c12", [12, 13], ["현_맨머리", "어머니"], "", ROOM + ", night, a small oil lamp dish glowing", "only two people: the sick mother (reference image 2) lying on her back on the mat under a thin quilt with her eyes closed, and the young man (reference image 1) dressed all in white kneeling beside her alone, gently giving her water from a wooden spoon, keeping watch through the night; nobody else is in the room", "밤새 어머니 곁을"),
    ("c13", [14, 15], ["어머니", "현_맨머리"], "", ROOM + ", soft morning light", "the mother sitting up weakly and eating porridge from a small bowl, the young man smiling with relief beside her; behind him softly glows " + PANEL, "어머니가 죽을 받아 넘기다"),
    ("c14", [16], [], "", VILLAGE + ", wide view from a small hill", "a quiet village where a strange reddish mist rises like smoke above three of the stone wells, an eerie mood", "우물 위의 붉은 안개"),
    ("c15", [17], ["현"], "", VILLAGE, "the young man standing on a dirt path looking at the village with determination, " + PANEL + " glowing beside him", "마을을 살리십시오"),
    ("c16", [18, 19], ["현"], VILLAGERS, ENTRY, "the young man standing under the big tree shouting earnestly to a crowd of villagers, one arm raised pointing toward a well", "끓여서 마셔야 합니다"),
    ("c17", [20], [], VILLAGERS, ENTRY, "a few villagers whispering to each other doubtfully with suspicious faces, glancing to the side. No main characters", "의원 흉내를 낸다고"),
    ("c18", [21], ["수령"], CLERKS, ENTRY + ", dust on the road", "the thin magistrate riding a brown horse arriving on the road with several clerks walking behind him, an arrogant face, the magistrate wearing a black samo cap with two flat oval wings sticking out to the left and right", "박 수령이 나타나다"),
    ("c19", [22], ["수령"], CLERKS, ENTRY, "the thin magistrate on his horse pointing coldly with a fan, ordering the clerks to block the roads", "길을 모두 막아라"),
    ("c20", [23], [], CLERKS, FENCE, "clerks putting up a rough wooden barricade fence across the road, while an ox cart loaded with plain brown wooden medicine chests and straw-wrapped bundles turns away from the village. No main characters", "막힌 길, 돌아가는 약재 수레"),
    ("c21", [24, 25], ["수령", "현"], "", FENCE, "the young scholar stepping in front of the magistrate's brown horse with his arms spread, blocking its way; the magistrate on the horse smirking", "수령의 말 앞을 막아서다"),
    ("c22", [26, 27], ["현", "수령"], "", FENCE, "the young scholar standing and pleading earnestly; the magistrate looking down at him from the horse with a mocking sneer", "말 위에서 비웃는 수령"),
    ("c23", [28, 29], ["현"], CLERKS, FENCE, "the young scholar has just been pushed down and is sitting fallen on the dirt road, propped on one hand, dust flying, his gat hat still on his head; a clerk in black-gray hanbok stands over him with his hand still pushed out. The young scholar appears only once, only on the ground", "흙바닥에 넘어진 이현"),
    ("c24", [30], ["현"], "", FENCE, "the young scholar half-lying on the dirt road propped on one arm, looking up at " + PANEL + " showing a faint picture of a locked wooden storehouse", "숨겨진 사실이 보입니다"),
    ("c25", [31], ["현"], VILLAGERS, VILLAGE + ", night", "the young scholar and a few villagers hanging big black iron pots over wood fires beside a stone well at night, flames and steam", "우물마다 솥을 걸다"),
    ("c26", [32], ["현"], VILLAGERS, VILLAGE + ", daytime", "a recovered little village boy standing up smiling and an old man getting up, villagers gathering around the steaming pots, the young scholar ladling boiled water into bowls", "하나둘 솥 앞에 모여들다"),
    ("c27", [33], [], VILLAGERS, VILLAGE + ", bright morning", "the village in clear morning light, the last thin wisps of reddish mist fading away above the wells, villagers going about their work. No main characters", "걷혀 가는 붉은 안개"),
    ("c28", [34], [], "Other people are a Joseon governor's procession: soldiers in dark blue uniforms with spears and black felt hats walking beside a man on a horse. ", FENCE + ", seen from a distance", "a governor's procession passing along the road outside the wooden barricade, smoke from steaming pots rising beyond the fence in the village", "관찰사의 행렬"),
    ("c29", [35], ["관찰사"], "Other people are soldiers in dark blue uniforms with spears and black felt hats, standing behind the governor. ", FENCE, "the governor on a brown horse stopping and looking over the wooden barricade with a puzzled stern face", "어찌 사람들이 저리 일을"),
    ("c30", [36], ["현"], "", FENCE, "the young scholar stepping in front of the wooden barricade and bowing deeply with both hands together", "울타리 앞에 나선 이현"),
    ("c31", [37], ["현", "관찰사"], "", FENCE, "the young scholar standing straight and speaking firmly toward the governor on his horse, pointing toward a distant storehouse", "창고를 열어 보시옵소서"),
    ("c32", [38], ["관찰사"], "Other people are soldiers in dark blue uniforms with spears and black felt hats. ", FENCE, "the governor on his horse giving an order with a raised hand; soldiers bowing and setting off", "군졸들에게 명하다"),
    ("c33", [39], [], "Other people are soldiers in dark blue uniforms with black felt hats. ", STORE + ", evening torchlight", "the heavy storehouse doors thrown open by soldiers, revealing many wooden carts piled high with locked medicine boxes inside. No main characters", "창고 안의 약재 수레 서른 대"),
    ("c34", [40, 41], ["수령", "관찰사"], "", STORE + ", evening torchlight", "the thin magistrate kneeling with a pale terrified face; the governor standing over him holding out his hand sternly to take the magistrate's seal", "수령의 관인을 거두다"),
    ("c35", [42], ["어머니"], VILLAGERS, ENTRY + ", sunset", "villagers joyfully pulling down the wooden barricade; in the foreground the mother standing at a brushwood gate wiping tears with her sleeve, smiling", "울타리를 걷어 내는 마을 사람들"),
    ("c36", [43, 44], ["현_맨머리"], "", ROOM + ", night, a small oil lamp dish glowing", "the young man sitting at a low wooden table with an open thread-bound book, looking up at " + PANEL + " with one glowing red line at its bottom", "세 번째 임무, 장원 급제"),
    ("c37", [45], ["판서"], "", MANSION, "the heavy-set minister sitting at the low lacquered table, slowly putting down a white porcelain teacup, listening to news with a cold face", "한양의 김 판서"),
    ("c38", [46, 47], ["판서"], "", MANSION, "close view of the heavy-set minister's face narrowing his eyes with a cold dangerous look, candlelight flickering", "김 판서의 눈이 가늘어지다"),
]}


def proj_of(part):
    return os.path.join(HERE, f"조선시스템_{part}부_프로젝트.json")


def paragraphs(story):
    return [p.strip() for p in re.split(r"\n\s*\n", story) if p.strip() and not p.strip().startswith("[사진")]


def ref_of(nm):
    r = REF[nm]
    return r if os.path.isabs(r) else os.path.join(SHEETS, r)


def prompt(cut):
    cid, _, who, others, place, desc, _ = cut
    p = (STYLE_2045 if "도현" in who else STYLE) + ". "
    if who:
        p += "In the scene: " + "; ".join(f"character from reference image {k + 1}: {LOOK[nm]}" for k, nm in enumerate(who)) + ". "
        if any(nm in CAPPED for nm in who):
            p += CAP_LINE
        p += "Each character appears only once, exactly two arms and two legs and five fingers on each hand, head and face turned the same direction as the body. "
    else:
        p += "No main characters. "
    if others:
        p += others
    else:
        p += "No other people besides those described in the scene. "
        if len(who) == 1:
            p += "Exactly one person in the whole image, no twin, no copy. "
    p += f"Scene: {desc}. Setting: {place}. "
    p += "Cinematic composition, full-bleed image, no border, no frame, no paper edges. No speech bubbles, no readable text, no letters, no signs with writing."
    return p


def main():
    cmd, part, folder = sys.argv[1], int(sys.argv[2]), sys.argv[3]
    cuts = CUTS[part]
    if cmd == "job":
        only = set(sys.argv[4:])
        items = [{"id": c[0], "width": 1024, "height": 576, "seed": 2100 + part * 100 + k, "prompt": prompt(c), "refs": [ref_of(nm) for nm in c[2]]}
                 for k, c in enumerate(cuts) if not only or c[0] in only]
        os.makedirs(folder, exist_ok=True)
        out = os.path.join(folder, "job.json")
        json.dump({"items": items, "crop_border": True}, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(out, len(items), "cuts")
    elif cmd == "project":
        pj = proj_of(part)
        p = json.load(open(pj, encoding="utf-8"))
        paras = paragraphs(p["story"])
        first = {c[1][0]: c for c in cuts}
        assert sorted(n for c in cuts for n in c[1]) == list(range(1, len(paras) + 1)), "문단 번호가 대본과 안 맞음"
        out = []
        for i, para in enumerate(paras, 1):
            if i in first:
                c = first[i]
                out.append(f"[사진: {os.path.join(folder, c[0] + '.png')} | {c[6]} | AI 생성 그림 (FLUX.2 klein) | ]")
            out.append(para)
        p["story"] = "\n\n".join(out)
        p["autophoto"] = False
        json.dump(p, open(pj, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(pj, len(cuts), "cuts")


if __name__ == "__main__":
    main()
