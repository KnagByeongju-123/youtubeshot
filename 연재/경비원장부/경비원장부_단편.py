"""「경비원 장부」 단편 (일본 애니풍 미니드라마) — 컷별 그림 계획 (만드는 법은 「이름 없는 보고서」와 같음)
python 연재/경비원장부/경비원장부_단편.py job <저장폴더> [컷번호 ...]  → klein_worker 그림 주문서 job.json
python 연재/경비원장부/경비원장부_단편.py project <그림폴더>         → 프로젝트 파일에 [사진] 줄을 넣음 (나레이션 문단은 그대로)
  - 그림은 문단마다 한 장, 짧은 대사 문단은 앞뒤 문단과 묶음 / 인물은 캐릭터 시트(캐릭터시트/)를 기준 그림으로
  - 아파트·사람 이름은 모두 지어낸 것"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SHEETS = os.path.join(HERE, "캐릭터시트")
PROJ = os.path.join(HERE, "경비원장부_프로젝트.json")

STYLE = ("Japanese anime style scene, TV anime screenshot, clean crisp line art, anime cel shading with soft shadows, "
         "realistic human proportions, natural colors, detailed anime background art, modern Korean apartment complex drama")
LOOK = {
    "경비원": "a 63-year-old Korean man, short and slim apartment security guard with short white-gray hair, kind wrinkled face, navy blue guard uniform jacket and trousers with a round badge, light blue shirt, navy necktie, navy peaked guard cap",
    "대표": "a 54-year-old Korean man, tall and heavy-set with a big belly, short slicked-back black hair, thin gold-rimmed glasses, arrogant face, white polo shirt under a dark green quilted vest, beige trousers, gold wristwatch",
    "서연": "a 34-year-old Korean woman with black hair in a low neat ponytail, calm intelligent eyes, no glasses, beige trench coat over a white blouse, dark gray slacks",
    "할머니": "an 81-year-old Korean grandmother, very short and slightly hunched, curly permed short gray hair, kind wrinkled face, purple flower-pattern quilted vest over a cream sweater, dark brown trousers, wooden walking cane",
}
BOSS = ""
BOOTH = "a small Korean apartment security guard booth at the complex entrance: a desk by a big window, an old monitor, a key board on the wall, an electric fan, a thermos, neat stacks of papers"
COMPLEX = "the grounds of a quiet Korean apartment complex with tall cream-colored apartment buildings, trees, a playground and walking paths"
BASEMENT = "an underground parking garage of a Korean apartment complex with concrete pillars, parked cars, fluorescent lights and a metal storage room door"
HALL = "a community meeting hall inside a Korean apartment complex, rows of folding chairs filled with residents, a projector screen at the front"
LOBBY = "the ground floor lobby of a Korean apartment building with mailboxes and an elevator"
NOTE = "the notebook pages are covered in tiny neat handwriting that is too small and blurry to read"

# (컷, 문단 번호들, 나오는 인물(시트), 사장님(안 씀), 다른 사람 나와도 됨, 장소, 장면(영어), 화면 설명)
CUTS = [
    ("c01", [1], ["경비원"], False, False, BOOTH + ", before dawn, dark blue sky outside, one desk lamp on", "a single old security guard sitting alone at the desk under a desk lamp, opening a worn old notebook with a faded cover; he is the only person in the booth", "새벽 다섯 시 경비실"),
    ("c02", [2], [], False, False, "on the desk in the guard booth under a desk lamp", "close-up of a worn old notebook with a faded cardboard cover and bent corners, a ballpoint pen beside it, the cover writing is blurry and unreadable. No people", "장부라고 쓴 공책"),
    ("c03", [3], ["경비원"], False, False, BOOTH + ", early morning", "close-up of the old guard's wrinkled hand writing carefully in the open notebook with a ballpoint pen, " + NOTE, "이십 년 동안 적어 온 하루"),
    ("c04", [4, 5], ["경비원", "할머니"], False, False, "in front of the guard booth window at the apartment entrance, morning light", "the small hunched grandmother with a cane holding out a warm bottle of soy milk through the booth window, the old guard taking off his cap and bowing his head gratefully", "두유를 건네는 할머니"),
    ("c05", [6], ["경비원", "할머니"], False, False, COMPLEX + ", morning", "the old guard gently helping the hunched grandmother toward the building entrance, pointing to the elevator, she smiles", "할머니를 챙기는 만수 씨"),
    ("c06", [7], ["경비원"], False, True, COMPLEX + ", sunny morning", "the old guard (only one guard in the whole image) standing by the path smiling and waving back at two children with school backpacks, a woman carrying a parcel smiles at him, a warm peaceful neighborhood", "인사하는 주민들"),
    ("c07", [8], ["대표"], False, False, COMPLEX + ", spring with cherry blossoms", "the heavy-set man in a green vest and gold glasses standing proudly in front of an apartment building, arms crossed, smug face", "새 입주자 대표 강태호"),
    ("c08", [9, 10], ["대표", "경비원"], False, False, BOOTH + ", an air conditioner on the wall", "the heavy-set man in a green vest pointing rudely at the air conditioner on the guard booth wall, the old guard standing stiffly beside the desk", "에어컨을 가리키는 대표"),
    ("c09", [11], ["경비원"], False, False, BOOTH + ", hot summer day, an empty spot on the wall where the air conditioner was removed", "the old guard sweating in the heat, wiping his forehead with a towel, a small electric fan blowing beside him", "선풍기 한 대로 버틴 여름"),
    ("c10", [12, 13], ["대표", "경비원"], False, False, BASEMENT, "the heavy-set man in a green vest yelling and jabbing a finger at the old guard next to a black luxury sedan, the guard bowing his head", "반말로 소리치는 대표"),
    ("c11", [14], ["경비원"], False, False, BOOTH + ", night, dark window", "the old guard alone in the booth at night, quietly opening his notebook under the desk lamp, tired but calm face", "그날 밤에도 장부를"),
    ("c12", [15, 16], [], False, True, COMPLEX + ", summer", "a group of residents gathered in front of a bulletin board with a notice poster about exterior wall painting, frowning and whispering, the poster text blurry and unreadable. No main characters", "외벽 도색 공사 공고"),
    ("c13", [17, 18], ["대표"], False, True, HALL + ", a small residents' meeting with a few people", "the heavy-set man in a green vest standing and speaking firmly at a meeting table, chopping the air with one hand, residents seated listening", "경비원을 줄이자는 대표"),
    ("c14", [19], [], False, False, BASEMENT + ", the storage room door wide open", "an empty dusty storage room in the basement with bare shelves and outlines where boxes and a machine used to be, the door open. No people", "텅 빈 지하 창고"),
    ("c15", [20, 21], ["대표", "경비원"], False, False, BOOTH, "the heavy-set man in a green vest bursting through the guard booth door shouting with an angry red face, the old guard startled at his desk", "경비실 문을 벌컥 연 대표"),
    ("c16", [22, 23], ["경비원"], False, False, BOOTH, "close-up of the old guard's trembling hands holding his cap, his worried face, trying to explain", "떨리는 손"),
    ("c17", [24], ["대표"], False, False, BOOTH, "low angle close-up of the heavy-set man in gold glasses glaring down, pointing a finger, threatening", "계약 연장은 없다"),
    ("c18", [25], ["경비원"], False, False, BOOTH + ", late night, only the desk lamp on", "the old guard turning the pages of his notebook late at night, his finger stopping on one page, eyes narrowing in realization, " + NOTE, "어느 날짜에서 멈춘 손가락"),
    ("c19", [26], ["서연", "경비원"], False, False, "in front of the guard booth window, morning", "the young woman in a beige trench coat holding a utility bill paper, talking to the old guard through the booth window", "고지서를 들고 온 서연 씨"),
    ("c20", [27], ["서연"], False, False, "in front of the guard booth, morning", "the young woman in a beige trench coat frowning thoughtfully while pointing at numbers on a bill, the paper text blurry", "이상한 공사비"),
    ("c21", [28, 29], ["경비원"], False, False, BOOTH, "the old guard hesitantly taking the worn notebook out of a desk drawer, holding it out with both hands", "서랍에서 꺼낸 장부"),
    ("c22", [30], ["서연"], False, False, BOOTH, "the young woman in a beige trench coat reading the open notebook, eyes wide in shock, holding her breath, " + NOTE, "숨을 멈춘 서연 씨"),
    ("c23", [31], [], False, False, BASEMENT + ", late at night, dim lights", "a black luxury sedan with its trunk open parked in front of the storage room, three cardboard boxes and a small generator beside it, shown as a memory with a soft blue tint. No people", "시월 칠일 밤 지하 주차장"),
    ("c24", [32, 33], ["경비원", "서연"], False, False, BOOTH, "the old guard speaking quietly with a humble sad smile, the young woman in a beige trench coat listening seriously, the notebook on the desk between them", "적어는 둬야지요"),
    ("c25", [34], ["서연"], False, False, "a small apartment living room at night with a desk lamp", "the young woman at home at night comparing papers and bills on a desk with a laptop and calculator, focused, " + NOTE, "밤마다 맞춰 본 서류"),
    ("c26", [35], ["대표"], False, True, HALL, "wide shot of the packed meeting hall, the heavy-set man in a green vest standing at the very front holding a microphone, residents filling every chair", "주민 총회 날"),
    ("c27", [36], ["대표"], False, True, HALL, "the heavy-set man in a green vest speaking confidently into the microphone, raising two fingers, the projector screen behind him blank", "안건은 둘입니다"),
    ("c28", [37], ["경비원"], False, True, HALL + ", seen from the corner of the room", "the old guard standing alone in the corner of the hall holding his cap in both hands with his head bowed, residents turning to look at him", "구석에 선 만수 씨"),
    ("c29", [38, 39], ["할머니"], False, True, HALL, "the small hunched grandmother standing up from the front row leaning on her cane, scolding angrily with a raised hand", "지팡이 짚고 일어난 할머니"),
    ("c30", [40], ["대표"], False, True, HALL, "the heavy-set man in a green vest waving his hand dismissively with a sneer, holding the microphone", "증거가 더 필요하냐는 대표"),
    ("c31", [41, 42], ["서연"], False, True, HALL + ", seen from the front", "the young woman in a beige trench coat raising her hand calmly from the back row of the hall, determined eyes", "손을 든 서연 씨"),
    ("c32", [43], ["서연"], False, True, HALL, "the young woman connecting a laptop to the projector, the big screen showing two documents side by side: a printed bill on the left and a photo of a handwritten notebook page on the right, all text blurry and unreadable", "청구서와 장부를 나란히"),
    ("c33", [44], ["서연"], False, True, HALL, "the young woman in a beige trench coat explaining calmly, pointing at the projector screen with an open hand, residents leaning forward", "이틀만 온 트럭"),
    ("c34", [45, 46], ["대표"], False, True, HALL, "the heavy-set man in gold glasses red-faced and furious, shouting with veins on his forehead, residents murmuring", "얼굴이 붉어진 대표"),
    ("c35", [47, 48], ["서연"], False, True, HALL, "the young woman clicking to the next slide, the screen showing two blurred business documents with a circled matching name, unreadable text", "처남과 같은 이름"),
    ("c36", [49], ["대표"], False, False, HALL, "close-up of the heavy-set man in gold glasses with his mouth half open, frozen speechless, cold sweat", "말문이 막힌 대표"),
    ("c37", [50, 51], ["대표"], False, True, HALL, "the heavy-set man in a green vest slamming his hand on the table and shouting a denial, panicked eyes", "그날 집에 있었다고"),
    ("c38", [52, 53], ["경비원"], False, True, HALL, "the old guard raising his head for the first time and speaking firmly, eyes steady and calm, holding his cap at his chest", "처음으로 고개를 든 만수 씨"),
    ("c39", [54], ["경비원"], False, False, HALL, "close-up of the old guard's face, calm dignified eyes, soft light from the window", "떨리지 않는 목소리"),
    ("c40", [55], [], False, False, HALL, "the projector screen showing a table of parking gate entry and exit times with one row highlighted in yellow, all text blurry and unreadable. No people", "차단기 기록"),
    ("c41", [56], ["대표"], False, True, HALL, "the heavy-set man in a green vest standing frozen and pale while every resident in the hall stares at him", "모든 눈길이 대표에게"),
    ("c42", [57], [], False, True, HALL, "many residents in the meeting hall raising their hands to vote, a sea of raised hands. No main characters", "손을 든 주민들"),
    ("c43", [58], ["대표"], False, True, COMPLEX + ", evening", "the heavy-set man in a green vest walking away with his head down, two police officers beside him, residents watching from a distance", "물러난 대표"),
    ("c44", [59, 60], ["경비원"], False, False, BOOTH + ", a brand-new air conditioner on the wall", "the old guard looking up at a brand-new air conditioner on the booth wall with a touched smile, cool air blowing", "다시 달린 에어컨"),
    ("c45", [61, 62], ["할머니", "경비원"], False, False, "in front of the guard booth, warm afternoon", "the hunched grandmother handing a small gift box to the old guard, inside is a new notebook with a dark brown leather cover", "할머니의 선물"),
    ("c46", [63], [], False, False, "on the desk in the guard booth, warm light", "close-up of the first page of a new leather notebook with one line of handwriting in many different handwritings, all blurry and unreadable, a few small flower petals on the desk. No people", "주민들이 쓴 한 줄"),
    ("c47", [64, 65], ["경비원"], False, False, BOOTH + ", clear morning sunlight through the window", "the old guard smiling gently as he writes the first line in the new leather notebook, sunlight on his face, peaceful", "오늘도, 아무 일 없음"),
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
        p += "No other people besides those described in the scene. "
        if len(who) == 1 and not boss:
            p += "Exactly one person in the whole image, no twin, no copy, no reflection of him or her. "
    else:
        p += "Other people are ordinary background office workers who look clearly different from the main characters; each main character appears only once, nobody else has the same hair or suit. "
    p += f"Scene: {desc}. Setting: {place}. "
    p += "Cinematic composition, full-bleed image, no border, no frame, no paper edges. No speech bubbles, no readable text, no letters, no logos, no signboards with writing."
    return p


def main():
    cmd, folder = sys.argv[1], sys.argv[2]
    if cmd == "job":
        only = set(sys.argv[3:])
        items = [{"id": c[0], "width": 1024, "height": 576, "seed": 300 + k, "prompt": prompt(c),
                  "refs": [os.path.join(SHEETS, ("_앞_" if os.environ.get("FRONT") else "") + nm + ".png") for nm in c[2]]}
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
