"""「이름 없는 보고서」 단편 (일본 애니풍 미니드라마) — 컷별 그림 계획
python 연재/이름없는보고서/이름없는보고서_단편.py job <저장폴더> [컷번호 ...]  → klein_worker 그림 주문서 job.json (번호를 주면 그 컷만)
python 연재/이름없는보고서/이름없는보고서_단편.py project <그림폴더>         → 프로젝트 파일에 [사진] 줄을 넣음 (나레이션 문단은 그대로 → 다시 녹음 없음)
  - 그림은 문단마다 한 장, 5초보다 짧은 대사 문단은 앞뒤 문단과 묶음 (규칙: 한 장 5~15초)
  - 인물은 캐릭터 시트(연재/막내개그/캐릭터시트/)를 기준 그림으로 넣고 외모를 다시 적음. 사장님은 시트 없이 글로만
  - 회사·사람 이름은 모두 지어낸 것"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SHEETS = os.path.join(ROOT, "연재", "막내개그", "캐릭터시트")
PROJ = os.path.join(HERE, "이름없는보고서_프로젝트.json")

STYLE = ("Japanese anime style scene, TV anime screenshot, clean crisp line art, anime cel shading with soft shadows, "
         "realistic human proportions, natural colors, detailed anime background art, modern Korean office drama")
LOOK = {
    "막내": "a 25-year-old Korean young man with messy fluffy black curly hair, tired eyes, slim build, white dress shirt with sleeves rolled once, loose navy necktie, navy slacks, black sneakers, an ID card on a blue lanyard",
    "부장님": "a 55-year-old Korean man, balding on top with short gray-black hair on the sides, thick black-rimmed glasses, round face, round belly, dark gray suit, white shirt, dark red necktie",
    "팀장님": "a 42-year-old Korean woman with a straight black chin-length bob and blunt bangs, thin silver-rimmed glasses, calm sharp expression, light gray blazer over a white blouse, black trousers",
    "이대리": "a 30-year-old Korean man with black hair styled up and back in a neat pompadour, sly smirk, slim navy blue suit, light blue shirt with open collar and no necktie",
    "박사원": "a 25-year-old Korean young woman with black hair in a high ponytail with see-through bangs, bright eyes, beige knit cardigan over a white t-shirt, light blue jeans, an ID card on a blue lanyard",
}
BOSS = ("the company president (no reference image): a dignified Korean man in his sixties with neat silver-white hair combed back, "
        "clean-shaven, calm sharp eyes, charcoal black suit, white shirt, navy necktie")
OFFICE = "a bright modern Korean corporate office of a food company planning team, rows of white desks with monitors, potted plants, large windows"
MEETING = "a large modern corporate meeting room with a long table, office chairs and a big presentation screen on the wall"
CHIEF_ROOM = "a small private office of a department head with a wooden desk, a leather chair, bookshelves and a window"
HALL = "a long bright office hallway with glass walls and gray carpet"
ROOF = "a company building rooftop garden with benches, plants and a city skyline under a blue sky at noon"
SHOP = "a small cozy Korean side-dish shop (banchan shop) with glass display trays of colorful side dishes, warm lights, evening"
NIGHT_OFFICE = "the same office late at night, all lights off except one desk lamp and a glowing monitor, dark windows with city lights"

# (컷, 문단 번호들, 나오는 인물(시트), 사장님 나옴, 다른 사람 나와도 됨, 장소, 장면(영어), 화면 설명)
CUTS = [
    ("c01", [1], ["부장님"], False, True, OFFICE, "Monday morning, wide shot of the office, the department head standing at the front of the room speaking loudly to the team seated at their desks, coffee cups on desks", "월요일 아침 기획팀"),
    ("c02", [2], ["부장님"], False, False, OFFICE, "medium shot of the department head raising one finger and announcing something important with a big confident voice", "신사업 보고서를 말하는 부장님"),
    ("c03", [3], ["막내", "이대리"], False, True, OFFICE, "office workers lowering their heads to avoid eye contact at their desks, only the curly-haired young man sits up straight looking forward with interest", "모두 고개를 숙인 가운데 막내만"),
    ("c04", [4], ["막내"], False, False, OFFICE, "the curly-haired young man at his desk taking out a small black pocket notebook, his eyes shining with excitement for the first time", "수첩을 꺼내는 지후"),
    ("c05", [5], ["막내"], False, True, SHOP, "the curly-haired young man standing at the counter politely asking the middle-aged female shop owner questions while taking notes in his pocket notebook", "반찬 가게를 도는 지후"),
    ("c06", [6], [], False, True, SHOP, "a tired middle-aged Korean woman shop owner in an apron behind the side-dish display, sighing as she looks at leftover side dishes at closing time. No main characters", "남는 반찬이 아깝다는 사장님"),
    ("c07", [7], ["막내"], False, False, NIGHT_OFFICE, "the curly-haired young man working late at his desk with a calculator, his open notebook and colorful bar charts on the monitor", "숫자로 바꾸는 지후"),
    ("c08", [8], [], False, False, "on an office desk under a desk lamp at night", "close-up of the last page of a printed report with one small neat table of numbers and handwritten-style notes in the margin, the text too small and blurry to read", "마지막 장의 작은 표"),
    ("c09", [9], ["막내", "이대리"], False, False, NIGHT_OFFICE, "the curly-haired young man at his desk clicking to upload a file on the monitor, the pompadour man in a navy suit standing behind him tapping his shoulder", "어깨를 툭 치는 이 대리"),
    ("c10", [10], ["이대리"], False, False, NIGHT_OFFICE, "close-up of the pompadour man in a navy suit leaning down with a friendly but sly smile, offering to help", "봐 주겠다는 이 대리"),
    ("c11", [11], ["막내"], False, False, NIGHT_OFFICE, "the curly-haired young man standing up from his chair and bowing his head gratefully with an innocent smile", "고맙다고 고개 숙이는 지후"),
    ("c12", [12], [], False, False, CHIEF_ROOM + ", morning sunlight", "close-up of a printed report lying on a wooden desk, the cover page has a title and one name line but the letters are blurry and unreadable. No people", "부장님 책상 위 보고서"),
    ("c13", [13], ["부장님", "이대리"], False, False, CHIEF_ROOM, "the department head laughing happily while holding the report, praising the pompadour man in a navy suit who stands in front of the desk", "이 대리를 칭찬하는 부장님"),
    ("c14", [14, 15], ["이대리"], False, False, CHIEF_ROOM, "the pompadour man in a navy suit scratching the back of his head, pretending to be shy and humble with a smug smile", "쑥스러운 척하는 이 대리"),
    ("c15", [16], ["막내", "이대리"], False, False, OFFICE, "foreground: the curly-haired young man's hands trembling into fists, shocked face; background: the pompadour man in a navy suit glancing back at him and winking", "눈을 찡긋하는 이 대리"),
    ("c16", [17, 18], ["막내", "박사원"], False, False, ROOF, "the ponytail young woman in a beige cardigan sitting down next to the curly-haired young man on a rooftop bench, talking to him with concern", "옥상의 지후와 서아"),
    ("c17", [19], ["막내"], False, False, ROOF, "the curly-haired young man sitting on the rooftop bench looking down sadly at a paper cup of coffee, shoulders slumped", "말해 봤자 소용없다는 지후"),
    ("c18", [20, 21], ["막내", "박사원"], False, False, ROOF, "the ponytail young woman holding out her smartphone to the curly-haired young man, the phone screen shows a small photo of him smiling with a notebook in front of a lit shop", "서아가 보여 준 사진"),
    ("c19", [22], ["이대리", "부장님"], False, True, MEETING, "a team meeting, the pompadour man in a navy suit talking proudly with gestures while the department head nods approvingly", "회의마다 보고서 자랑"),
    ("c20", [23], ["막내"], False, False, HALL, "the curly-haired young man standing in front of a closed wooden office door, hand raised to knock, hesitating nervously", "부장님 방 앞에서 망설이는 지후"),
    ("c21", [24], ["막내", "부장님"], False, False, CHIEF_ROOM, "the curly-haired young man standing in front of the desk speaking nervously, the department head sitting behind the desk", "사실을 말하려는 지후"),
    ("c22", [25], ["부장님"], False, False, CHIEF_ROOM, "the department head sitting at his desk laughing and talking cheerfully, not listening, waving one hand", "말을 끊는 부장님"),
    ("c23", [26], ["부장님"], False, False, CHIEF_ROOM, "the department head answering a ringing desk phone and making a shooing gesture with his other hand toward the door", "손짓으로 나가라는 부장님"),
    ("c24", [27], ["이대리"], False, False, HALL, "the pompadour man in a navy suit standing at the end of the hallway with his arms crossed, smirking", "복도 끝의 이 대리"),
    ("c25", [28], ["이대리", "막내"], False, False, HALL, "the pompadour man in a navy suit talking down to the curly-haired young man with a condescending grin, the young man looking down", "회사는 원래 그렇다는 이 대리"),
    ("c26", [29], ["막내"], False, False, NIGHT_OFFICE, "the curly-haired young man staring in disbelief at his glowing smartphone screen in the dark office, the screen shows a chat message bubble with blurred unreadable text", "밤에 온 메시지"),
    ("c27", [30], ["막내"], False, False, NIGHT_OFFICE, "the curly-haired young man alone in the empty dark office making presentation slides on the monitor, tired but focused, the clock shows past midnight", "빈 사무실에서 자료를 만드는 지후"),
    ("c28", [31], ["막내"], False, False, "the copy room of the office at night with a big photocopier", "the curly-haired young man standing at a large photocopier as stacks of printed pages come out, lonely face", "복사기를 돌리는 지후"),
    ("c29", [32], ["팀장님"], False, False, "a dim office at night seen through a glass partition", "the woman with a black bob and silver glasses quietly watching from behind a glass partition, arms folded, thoughtful expression", "조용히 보고 있던 윤 팀장"),
    ("c30", [33], ["이대리"], True, True, MEETING, "presentation day morning, executives seated at the long table including the president at the head, the pompadour man in a navy suit standing confidently in front of the big screen", "발표 날 회의실"),
    ("c31", [34], ["이대리"], False, True, MEETING, "the pompadour man in a navy suit presenting smoothly, pointing at colorful charts on the big screen with one hand", "매끄러운 발표"),
    ("c32", [35], ["막내"], False, False, MEETING + ", seen from the back of the room near the door", "the curly-haired young man standing by the door at the back of the room holding his notebook to his chest, watching with a bitter quiet face", "문 옆에서 지켜보는 지후"),
    ("c33", [36], [], True, False, MEETING, "the president seated at the table turning the pages of a printed report and stopping at the last page, his finger on a small table", "마지막 장에서 멈춘 사장님"),
    ("c34", [37], [], True, False, MEETING, "close-up of the president looking up from the report with calm sharp eyes, asking a question", "숫자의 근거를 묻는 사장님"),
    ("c35", [38, 39, 40], ["이대리"], False, False, MEETING, "close-up of the pompadour man in a navy suit sweating nervously, forced smile, eyes darting sideways", "대답 못 하는 이 대리"),
    ("c36", [41], ["막내"], False, True, SHOP, "flashback in warm sepia-tinted light: the curly-haired young man crouching beside a kitchen scale weighing a tray of leftover side dishes, writing in his notebook", "직접 재서 계산한 숫자"),
    ("c37", [42, 43], ["이대리"], False, False, MEETING, "the pompadour man in a navy suit laughing awkwardly and pointing with his whole arm toward the back of the room, shifting the blame", "막내 탓으로 돌리는 이 대리"),
    ("c38", [44], ["막내"], False, True, MEETING + ", seen from the back of the room near the door", "the curly-haired young man by the door frozen in shock as everyone at the table turns to stare at him", "막내에게 쏠린 눈"),
    ("c39", [45, 46], ["팀장님"], False, False, MEETING, "the woman with a black bob and silver glasses calmly opening a laptop at the meeting table, composed expression", "노트북을 여는 윤 팀장"),
    ("c40", [47], [], False, False, MEETING, "the big screen on the wall showing a file information window with a document icon and several rows of details, all text blurry and unreadable. No people", "보고서 파일의 정보"),
    ("c41", [48], [], False, False, "close-up of a laptop screen in a meeting room", "a long timeline list of file edit history entries with small moon icons for night time, the text blurry and unreadable. No people", "고친 기록 마흔세 번"),
    ("c42", [49], ["이대리"], False, False, MEETING, "close-up of the pompadour man in a navy suit going pale with shock, eyes wide, cold sweat", "얼어붙은 이 대리"),
    ("c43", [50], ["팀장님"], False, False, MEETING, "the woman with a black bob and silver glasses holding up her smartphone toward the president, the screen showing a chat message with blurred text", "메시지를 보여 주는 윤 팀장"),
    ("c44", [51], ["팀장님"], False, False, MEETING, "side view of the woman with a black bob and silver glasses standing straight and speaking calmly, no anger, soft window light", "끝까지 차분한 팀장님"),
    ("c45", [52], ["부장님", "이대리"], False, False, MEETING, "the department head with a stiff frozen face, beside him the pompadour man in a navy suit hanging his head low", "굳은 부장님, 고개 숙인 이 대리"),
    ("c46", [53], [], True, False, MEETING, "the president turning his head to look toward the far end of the room with a curious gentle expression", "회의실 끝을 보는 사장님"),
    ("c47", [54], [], True, False, MEETING, "the president gesturing with an open palm, kindly inviting someone to speak", "설명해 보라는 사장님"),
    ("c48", [55], ["막내"], False, False, MEETING, "the curly-haired young man taking a deep breath and stepping forward from the door with determination", "앞으로 걸어 나오는 지후"),
    ("c49", [56], ["막내"], False, False, MEETING, "the curly-haired young man standing in front of the big screen explaining confidently with one hand open, bar charts on the screen", "숫자를 설명하는 지후"),
    ("c50", [57], ["막내"], False, False, MEETING, "close-up of the curly-haired young man's hands opening his worn pocket notebook, pages densely filled with handwriting too small to read", "빼곡한 수첩"),
    ("c51", [58], ["막내"], False, False, MEETING, "the curly-haired young man speaking sincerely with warm eyes, a soft glowing memory of side-dish shop owners behind him", "아깝다는 말"),
    ("c52", [59], ["막내"], True, True, MEETING, "wide shot of the quiet meeting room in warm light, everyone at the table listening to the curly-haired young man", "편안한 조용함"),
    ("c53", [60], ["부장님"], True, False, MEETING, "the president clapping slowly with a smile, the department head beside him clapping a beat late awkwardly", "박수 치는 사장님과 부장님"),
    ("c54", [61, 62, 63], ["이대리"], True, False, MEETING, "the president speaking firmly, in the foreground the pompadour man in a navy suit bowing his head in shame", "읽는 것부터 다시 배우게"),
    ("c55", [64], ["막내"], False, False, OFFICE + ", afternoon sunlight", "the curly-haired young man looking at a new blank name plate and a small potted flower on his desk, moved, smiling softly", "새 이름표"),
    ("c56", [65], ["이대리"], False, False, "a small office pantry with a coffee machine and a counter", "the pompadour man in a navy suit alone making coffee, ten paper cups lined up on the counter, sulky face", "탕비실의 이 대리"),
    ("c57", [66, 67], ["팀장님", "막내"], False, False, "an office building elevator lobby in the evening with polished floors", "the woman with a black bob and silver glasses talking to the curly-haired young man in front of the elevators, a small kind smile", "엘리베이터 앞의 팀장님"),
    ("c58", [68], ["막내", "팀장님"], False, False, "an office building elevator lobby in the evening with polished floors", "the curly-haired young man bowing deeply to the woman with a black bob and silver glasses", "고개 숙이는 지후"),
    ("c59", [69, 70], ["박사원"], False, True, "a crosswalk in front of a tall office building at sunset, city street", "the ponytail young woman in a beige cardigan running across the crosswalk waving her hand happily", "손 흔들며 뛰어오는 서아"),
    ("c60", [71, 72], ["막내"], False, False, "a city street in front of an office building at sunset", "the curly-haired young man laughing brightly with his head held high, golden sunset light", "고개를 들고 웃는 지후"),
    ("c61", [73], ["막내", "박사원"], False, True, "an evening city street with warm streetlights and small shops", "seen from behind, the curly-haired young man and the ponytail young woman walking side by side laughing down the street", "저녁 거리로 퍼지는 웃음"),
]


def paragraphs(story):
    return [p.strip() for p in re.split(r"\n\s*\n", story) if p.strip() and not p.strip().startswith("[사진")]


def prompt(cut):
    cid, _, who, boss, crowd, place, desc, _ = cut
    looks = [f"person {k + 1} (the character from reference image {k + 1}): {LOOK[nm]}" for k, nm in enumerate(who)]
    if boss:
        looks.append(BOSS)
    p = f"{STYLE}. "
    if looks:
        p += "Characters: " + "; ".join(looks) + ". Each person appears only once, exactly two arms and two legs, head and face turned the same direction as the body. "
    else:
        p += "No main characters. "
    if not crowd:
        p += "No other people in the scene. "
    else:
        p += "Other people are ordinary background office workers who look different from the main characters. "
    p += f"Scene: {desc}. Setting: {place}. "
    p += "Cinematic composition, full-bleed image, no border, no frame, no paper edges. No speech bubbles, no readable text, no letters, no logos."
    return p


def main():
    cmd, folder = sys.argv[1], sys.argv[2]
    if cmd == "job":
        only = set(sys.argv[3:])
        items = [{"id": c[0], "width": 1024, "height": 576, "seed": 300 + k, "prompt": prompt(c),
                  "refs": [os.path.join(SHEETS, nm + ".png") for nm in c[2]]}
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
