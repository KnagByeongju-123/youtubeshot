"""「청소부 출신 사장님」 자수성가 단편 (일본 애니풍) — 컷별 그림 계획 (만드는 법은 「붕어빵 엄마의 빌딩」과 같음)
python 연재/청소부사장/청소부사장_단편.py job <저장폴더> [컷번호 ...]  → klein_worker 그림 주문서 job.json
python 연재/청소부사장/청소부사장_단편.py project <그림폴더>         → 프로젝트 파일에 [사진] 줄을 넣음
  - 인물 기준 그림은 앞모습 조각(캐릭터시트/_앞_<인물>.png). 10년 뒤 은주는 따로 그린 시트(은주사장), 10년 뒤 지배인은 같은 시트 + 흰머리
  - 붕어빵 편에서 배운 것: 나이 든 같은 인물은 'the same man as the reference (only one of him)', 옷은 'clean', 상처·얼룩 없이
  - 호텔·사람 이름은 모두 지어낸 것"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SHEETS = os.path.join(HERE, "캐릭터시트")
PROJ = os.path.join(HERE, "청소부사장_프로젝트.json")

STYLE = ("Japanese anime style scene, TV anime screenshot, clean crisp line art, anime cel shading with soft shadows, "
         "realistic human proportions, natural colors, detailed anime background art, modern Korean luxury hotel drama")
LOOK = {
    "은주": "a 32-year-old slim Korean woman hotel cleaner with black hair in a low ponytail under a small white cap, plain kind face, light mint-green short-sleeve housekeeping uniform dress with a white collar and a white apron, black flat shoes",
    "은주사장": "a 42-year-old slim Korean woman with black hair in a sleek low bun, calm confident eyes, light makeup, tailored navy blue pantsuit with a white blouse and a small silver brooch",
    "지배인": "a 48-year-old tall thin Korean man with slicked-back black hair graying at the temples, a thin mustache, narrow cold eyes, black three-piece suit, burgundy tie, small gold badge with no letters",
    "지배인10": "the same thin Korean man as the reference (only one of him), about 58, slicked-back hair now mostly gray, thin gray mustache, humble tired eyes, a plain clean dark gray suit with no tie",
    "회장": "a 70-year-old short Korean man with neat white hair, round silver glasses, gentle smile, long-sleeved beige knit cardigan over a white shirt, gray trousers, a wooden cane",
}
HOTEL = "a luxury Korean hotel"
CORR = "a long elegant hotel guest-room corridor with carpet, warm wall lamps and numbered doors with no readable numbers"
ROOM = "a clean elegant hotel guest room with a large bed, white sheets, a window with city view, warm light"
OFFICE = "a hotel general manager's office with a dark wooden desk, leather chair and a window"
LOCKER = "a small plain staff locker room in a hotel basement with gray lockers and a bench"
STAIRS = "a narrow concrete emergency staircase inside a hotel, fluorescent lights"
LOBBY = "a grand bright hotel lobby with marble floors, a chandelier and tall windows"
HANOK = "a small cozy traditional Korean hanok guesthouse with wooden beams, paper doors, a small courtyard and warm lamps"
HOME = "a tiny modest Korean one-room apartment at night with a small desk and a lamp"
NOTE = "the paper pages are covered in tiny handwriting too small and blurry to read"

# (컷, 문단 번호들, 나오는 인물, (안 씀), 다른 사람 나와도 됨, 장소, 장면(영어), 화면 설명)
CUTS = [
    ("c01", [1], ["은주"], False, False, "a hotel basement laundry room at dawn with big washing machines and stacks of white towels", "the woman cleaner carrying a big stack of white towels in the early morning, tired but steady", "새벽 다섯 시 반 세탁실"),
    ("c02", [2], ["은주"], False, False, ROOM, "the woman cleaner smoothing a fresh white sheet on a large hotel bed, focused and careful", "하루 열여섯 개의 방"),
    ("c03", [3, 4], ["은주"], False, False, ROOM, "the woman cleaner picking up a small handwritten note card left on a nightstand and reading it, the writing blurry and unreadable", "손님이 남긴 쪽지"),
    ("c04", [5], ["은주"], False, False, HOME, "the woman at a small desk at night copying notes from many small paper cards into a thick notebook, desk lamp, " + NOTE, "공책에 옮겨 적은 쪽지"),
    ("c05", [6], ["지배인"], False, True, LOBBY, "the tall thin man in a black three-piece suit smiling politely and bowing to rich guests at the front desk", "손님 앞에서만 웃는 총지배인"),
    ("c06", [7, 8], ["지배인", "은주"], False, False, CORR, "the man in a black suit pushing a cleaning cart away with his foot and pointing at the stairs coldly; the woman cleaner stands stiffly with her head down", "엘리베이터는 손님용이야"),
    ("c07", [9], ["은주"], False, False, STAIRS, "the woman cleaner carrying a heavy cleaning cart up the concrete stairs with both arms, sweating, struggling", "십이 층까지 계단으로"),
    ("c08", [10, 11], ["은주", "지배인"], False, False, OFFICE, "the woman cleaner standing in front of the desk holding out a thick notebook with both hands, hopeful; the man in a black suit sits behind the desk", "공책을 내민 은주 씨"),
    ("c09", [12, 13], ["지배인"], False, False, OFFICE, "the man in a black suit pushing the notebook off to the side of his desk without opening it, sneering", "펼쳐 보지도 않고 밀어 버린 공책"),
    ("c10", [14], ["은주"], False, False, LOCKER + ", evening", "the woman cleaner sitting alone on a bench in the locker room crying quietly, holding her notebook against her chest", "탈의실에서 혼자 운 저녁"),
    ("c11", [15, 16], ["회장"], False, False, CORR, "the elderly man in a beige cardigan walking slowly down the corridor with his wooden cane, gentle smile", "칠 층 끝 방의 단골 노인"),
    ("c12", [17, 18], ["회장", "은주"], False, False, ROOM, "the elderly man sitting in an armchair by the window speaking kindly to the woman cleaner who stands holding a cleaning cloth", "그 공책은 뭔가"),
    ("c13", [19, 20, 21], ["회장"], False, False, ROOM, "the elderly man with reading glasses slowly turning pages of a thick handwritten notebook in an armchair by the window, impressed, " + NOTE, "오 년 동안 모은 공책"),
    ("c14", [22], ["회장", "은주"], False, False, ROOM, "the elderly man closing the notebook and looking warmly at the woman cleaner, nodding silently", "고개를 끄덕인 노인"),
    ("c15", [23], [], False, True, LOBBY + ", in winter, half empty", "an almost empty gloomy hotel lobby in winter with few guests and a worried front desk clerk. No main characters", "빈방이 늘어난 호텔"),
    ("c16", [24, 25], ["지배인"], False, True, "a hotel staff meeting room", "the man in a black suit shouting angrily at a group of staff in uniforms, pointing his finger", "청소부 다섯 명 내보낸다"),
    ("c17", [26], ["은주"], False, False, ROOM, "the woman cleaner gently placing a small folded note card on the pillow of the made bed, sad farewell face", "그동안 고마웠습니다"),
    ("c18", [27], ["은주"], False, False, HANOK, "the woman in a plain apron sweeping the small courtyard of the old hanok guesthouse, a fresh start, morning light", "작은 한옥 게스트하우스"),
    ("c19", [28], ["은주"], False, False, HANOK, "the woman placing a small handwritten welcome card and two different pillows on a neat guest bed in a hanok room, smiling", "공책대로 하나씩"),
    ("c20", [29], ["은주"], False, True, HANOK, "happy guests with suitcases thanking the woman at the guesthouse gate, the courtyard full of people", "동네 일 등 게스트하우스"),
    ("c21", [30, 31], ["회장", "은주"], False, False, HANOK, "the elderly man with a wooden cane standing at the hanok guesthouse gate smiling; the woman looks surprised and moved", "찾아온 서 노인"),
    ("c22", [32], ["회장"], False, False, HANOK, "close-up of the elderly man holding out a business card with both hands, the card text blurry and unreadable, a dignified smile", "하늘 그룹 회장"),
    ("c23", [33, 34], ["은주"], False, False, HANOK, "the woman holding a business card in both hands and slowly nodding with determined shining eyes", "이번에는 경영자로"),
    ("c24", [35, 36], ["은주사장"], False, True, LOBBY, "the woman in a navy pantsuit standing on a small stage in the grand lobby giving a speech, staff applauding", "새 대표 취임식"),
    ("c25", [37], [], False, True, ROOM, "a guest room with two kinds of pillows, a window draft seal and a small welcome card on the bed, a happy guest family. No main characters", "쪽지 하나하나가 바꾼 호텔"),
    ("c26", [38, 39], ["은주사장"], False, False, "a hotel interview room with a table and two chairs", "the woman in a navy pantsuit sitting at the interview table looking at a resume paper with unreadable text, calm", "객실 관리 팀장 면접"),
    ("c27", [40, 41], ["지배인10"], False, False, "a hotel interview room with a table and two chairs", "the thin gray-haired man in a plain gray suit sitting at the interview table, looking up and freezing in shock", "얼어붙은 마 씨"),
    ("c28", [42, 43], ["은주사장"], False, False, "a hotel interview room with a table", "the woman in a navy pantsuit placing an old worn thick notebook on the table, calm firm face", "그 공책, 기억하세요?"),
    ("c29", [44, 45], ["지배인10"], False, False, "a hotel interview room with a table", "close-up of the thin gray-haired man with cold sweat on his forehead, unable to speak, staring at the old notebook", "식은땀"),
    ("c30", [46, 47], ["은주사장"], False, False, "a hotel interview room with a table", "the woman in a navy pantsuit pushing the notebook across the table and speaking firmly with a gentle dignity", "청소하는 사람도 엘리베이터를 탑니다"),
    ("c31", [48, 49], ["지배인10"], False, False, "a hotel interview room with a table", "the thin gray-haired man bowing his head deeply over the table in humble acceptance", "처음부터 다시 배우겠습니다"),
    ("c32", [50, 51], ["은주사장"], False, False, ROOM + ", evening", "the woman in a navy pantsuit picking up a small note card left on the bed of the room, smiling warmly, the note text unreadable", "오늘도 방이 참 깨끗했습니다"),
    ("c33", [52], [], False, False, "on a desk under a warm lamp", "close-up of a new notebook's first page with a small old note card taped on it and one line of handwriting below, " + NOTE + ". No people", "청소하는 손이 호텔을 만든다"),
]


def paragraphs(story):
    return [p.strip() for p in re.split(r"\n\s*\n", story) if p.strip() and not p.strip().startswith("[사진")]


def ref_of(nm):
    return os.path.join(SHEETS, "_앞_" + nm.replace("10", "") + ".png")


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
        p += "Other people are ordinary hotel guests and staff in everyday clothes who look clearly different from the main characters. "
    p += f"Scene: {desc}. Setting: {place}. "
    p += "Cinematic composition, full-bleed image, no border, no frame, no paper edges. No speech bubbles, no readable text, no letters, no logos, no signs with writing."
    return p


def main():
    cmd, folder = sys.argv[1], sys.argv[2]
    if cmd == "job":
        only = set(sys.argv[3:])
        items = [{"id": c[0], "width": 1024, "height": 576, "seed": 1100 + k, "prompt": prompt(c), "refs": [ref_of(nm) for nm in c[2]]}
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
