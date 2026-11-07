"""「7분 늦게 사는 남자」 타임슬립 단편 (일본 애니풍) — 컷별 그림 계획 (만드는 법은 「붕어빵 엄마의 빌딩」과 같음)
python 연재/7분늦은남자/7분늦은남자_단편.py job <저장폴더> [컷번호 ...]  → klein_worker 그림 주문서 job.json
python 연재/7분늦은남자/7분늦은남자_단편.py project <그림폴더>         → 프로젝트 파일에 [사진] 줄을 넣음
  - 인물 기준 그림은 앞모습 조각(캐릭터시트/_앞_<인물>.png)
  - 다리가 무너지는 '미리 본 장면'은 푸른빛·물결 같은 환영으로 (실제 장면과 구분)
  - 회사·다리·사람 이름은 모두 지어낸 것"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SHEETS = os.path.join(HERE, "캐릭터시트")
PROJ = os.path.join(HERE, "7분늦은남자_프로젝트.json")

STYLE = ("Japanese anime style scene, TV anime screenshot, clean crisp line art, anime cel shading with soft shadows, "
         "realistic human proportions, natural colors, detailed anime background art, modern Korean city drama with a quiet mystery")
LOOK = {
    "기사": "a 52-year-old Korean man taxi driver with short black hair graying at the sides, tired gentle eyes, light gray zip-up work jacket with long sleeves over a navy collared shirt, dark brown trousers, an old silver wristwatch on his left wrist",
    "딸": "a 24-year-old slim Korean woman bus driver with a short black bob, bright brave eyes, sky-blue uniform shirt with a navy vest and navy tie, navy trousers",
    "사장": "a 50-year-old heavy-set Korean man with slicked-back black hair, gold-rimmed sunglasses pushed up on his head, smug face, shiny maroon leather jacket over a black shirt, thick gold necklace, black trousers, white loafers",
    "형사": "a 40-year-old tall Korean woman police detective with black hair in a low ponytail, sharp kind eyes, knee-length beige trench coat with a black belt over a white shirt, black trousers",
}
TAXI = "inside a Korean taxi cab, driver's seat, dashboard with a small dashcam, city street through the windshield"
GARAGE = "a Korean taxi company garage with rows of yellow-orange taxis and a small office"
OFFICE = "a flashy taxi company boss's office with a big desk, leather sofa and a window at night"
BRIDGE = "a long concrete river bridge in a modern Korean city in the morning, a wide river below, city skyline"
VISION = ", shown as a sudden premonition vision with a translucent bluish tint and rippling edges"
HOME = "a small modest Korean apartment living room in the evening"
HOSP = "a hospital room at night with rain on the window"

# (컷, 문단 번호들, 나오는 인물, (안 씀), 다른 사람 나와도 됨, 장소, 장면(영어), 화면 설명)
CUTS = [
    ("c01", [1], ["기사"], False, False, TAXI, "close-up of the man's left wrist on the steering wheel with an old silver wristwatch; the man looks at it quietly", "칠 분 늦게 가는 손목시계"),
    ("c02", [2], ["기사"], False, False, HOSP + ", shown as a memory with a soft blue tint", "the man lying in a hospital bed with a bandage on his head, slowly opening his eyes, confused", "칠 년 전 비 오는 밤의 사고"),
    ("c03", [3], ["기사"], False, True, "a busy Korean city crosswalk", "the man standing still at a crosswalk while people around him have already started walking, he looks slightly lost; the traffic light glows", "칠 분씩 늦게 보이는 세상"),
    ("c04", [4], ["기사"], False, False, "a small quiet hospital doctor's office", "only two people: a doctor in a white coat sitting at a desk pointing at a brain scan on a monitor, and the taxi driver sitting in a chair across the desk listening quietly with a worried face. No other people", "머릿속 시계가 고장 났다"),
    ("c05", [5, 6], ["기사"], False, False, TAXI + ", early morning", "the man driving his taxi carefully along an empty morning road, calm and focused, the same route", "매일 같은 길, 같은 시간"),
    ("c06", [7, 8], ["사장", "기사"], False, False, GARAGE, "the heavy-set man in a maroon leather jacket sneering and jabbing a finger at the taxi driver standing by his taxi, who smiles awkwardly", "매출이 꼴찌야"),
    ("c07", [9], ["기사"], False, True, GARAGE, "other taxi drivers whispering and smirking in a group while the man quietly wipes his taxi alone", "굼뜬 오 씨"),
    ("c08", [10, 11], ["딸", "기사"], False, False, HOME, "the young woman in a sky-blue bus driver uniform proudly showing her new ID card to her father, who smiles warmly", "첫 출근을 앞둔 딸"),
    ("c09", [12], ["기사", "딸"], False, False, HOME, "the father resting one hand gently on his daughter's shoulder while she smiles up at him, both smiling, warm evening light; no hand-holding", "딸의 어깨에 얹은 손"),
    ("c10", [13, 14], ["사장", "기사"], False, False, OFFICE, "the heavy-set man in a maroon leather jacket leaning back in his chair coldly telling the taxi driver standing in front of the desk that he is fired", "내일부터 나올 필요 없어"),
    ("c11", [15, 16], ["사장"], False, False, OFFICE, "the heavy-set man in a maroon leather jacket talking secretly on his phone by the window at night, a sly greedy grin, covering his mouth with his hand", "철근 반만 넣었어"),
    ("c12", [17], ["기사"], False, False, "a dark corridor outside an office at night", "the taxi driver frozen in the corridor with cold sweat, eyes wide in horror, having overheard something", "등에 흐른 식은땀"),
    ("c13", [18], ["기사"], False, False, TAXI + ", morning, heading toward a long river bridge", "the man driving toward a long bridge in the morning, tense face, gripping the wheel", "마지막 운행"),
    ("c14", [19], [], False, False, BRIDGE + VISION, "the middle of the long bridge collapsing with broken concrete falling into the river and a blue city bus tilting toward the water. No main characters", "미리 본 장면"),
    ("c15", [20], ["기사"], False, False, TAXI + ", morning, stopped near the bridge entrance", "the man blinking in shock, the bridge outside the windshield now perfectly intact and calm, the dashboard clock glowing with no readable numbers", "멀쩡한 다리"),
    ("c16", [21, 22], ["기사"], False, False, TAXI, "close-up of the man's face with eyes widening in realization, soft glowing light around him, as if time is rippling", "칠 분 먼저 보는 사람"),
    ("c17", [23, 24], ["기사"], False, False, "a quiet abstract memory space with floating translucent clock faces and city scenes", "the man standing among floating translucent memory scenes of his past days, all slightly ahead in time, calm understanding", "칠 년의 비밀"),
    ("c18", [25], ["기사"], False, False, BRIDGE + ", road toward the bridge entrance", "a plain yellow-orange taxi with no brand emblem speeding toward the bridge entrance, motion lines; only one person in the car, the man alone at the wheel with a determined face, the passenger seat empty", "다리 입구로 내달리다"),
    ("c19", [26], ["기사"], False, False, BRIDGE + ", the bridge entrance, morning", "the man's own plain yellow-orange taxi (no emblem) stopped sideways across the bridge entrance road with its orange hazard lights blinking; the man stands in front of it with both arms spread wide to block the road. No police car, no other people", "두 팔을 벌려 막아선 아빠"),
    ("c20", [27, 28], ["딸"], False, False, "inside the driver's seat of a blue city bus", "the young woman bus driver gripping the wheel in shock, staring through the windshield", "운전석의 하늘이"),
    ("c21", [29], ["기사"], False, False, BRIDGE + ", the bridge entrance", "close-up of the man shouting urgently toward the bus with one arm raised, desperate", "다리가 무너진다"),
    ("c22", [30, 31, 32], ["딸"], False, True, "inside a blue city bus at the bridge entrance", "the young woman bus driver standing up and shouting to the passengers with the doors open, passengers rising from their seats", "모두 내려 주세요"),
    ("c23", [33], ["기사"], False, True, BRIDGE + ", the bridge entrance", "many passengers hurrying back off the bridge, the man waving both arms to stop the cars behind", "서른두 명의 승객"),
    ("c24", [34], [], False, True, BRIDGE, "the middle of the bridge collapsing with a huge roar, concrete and dust falling into the river, seen from the entrance; people at the entrance in the foreground watching in shock. No main characters", "무너진 은빛대교"),
    ("c25", [35], [], False, True, BRIDGE + ", after the collapse, dust settling", "an empty bridge entrance with a blue city bus stopped safely and a taxi parked sideways in front of it, dust clearing. No main characters", "멈춰 선 버스와 택시"),
    ("c26", [36, 37], ["형사", "기사"], False, True, BRIDGE + ", rescue vehicles around", "the woman detective in a beige trench coat listening seriously and taking notes while the man explains", "형사에게 전한 말"),
    ("c27", [38, 39], ["형사"], False, False, "a police station office with documents on a desk", "the woman detective in a beige trench coat studying documents and a company chart pinned on a board, realizing something, the papers unreadable", "껍데기 회사"),
    ("c28", [40, 41], ["사장"], False, True, OFFICE + ", daytime", "the heavy-set man in a maroon leather jacket frantically tearing papers at his desk as police officers burst through the door", "들이닥친 경찰"),
    ("c29", [42, 43], ["형사"], False, False, OFFICE + ", daytime", "the woman detective in a beige trench coat holding up her smartphone showing a dashcam video, calm and firm", "블랙박스 영상"),
    ("c30", [44], ["사장"], False, False, OFFICE + ", daytime", "the heavy-set man in a maroon leather jacket slumping down to the floor in defeat, pale and speechless", "주저앉은 탁 대표"),
    ("c31", [45, 46], ["딸"], False, False, HOME + ", evening", "the young woman looking closely at an old silver wristwatch in her hands, curious and warm", "칠 분 늦은 시계"),
    ("c32", [47, 48], ["기사"], False, False, HOME + ", evening", "the man smiling gently and shaking his head, his daughter's hand on his shoulder, warm light", "네 칠 분을 지킬 수 있었으니까"),
    ("c33", [49, 50], ["기사"], False, False, TAXI + ", bright morning", "the man driving his taxi along the same morning road with a peaceful smile, the old wristwatch visible on his wrist, sunlight", "칠 분을 지킨 남자"),
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
        p += "Other people are ordinary Korean city people, passengers and drivers in everyday clothes who look clearly different from the main characters. "
    p += f"Scene: {desc}. Setting: {place}. "
    p += "Cinematic composition, full-bleed image, no border, no frame, no paper edges. No speech bubbles, no readable text, no letters, no logos, no signs with writing."
    return p


def main():
    cmd, folder = sys.argv[1], sys.argv[2]
    if cmd == "job":
        only = set(sys.argv[3:])
        items = [{"id": c[0], "width": 1024, "height": 576, "seed": 1300 + k, "prompt": prompt(c), "refs": [ref_of(nm) for nm in c[2]]}
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
