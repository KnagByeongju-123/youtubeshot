"""「화성 3호기 정비반장」 SF 단편 (일본 애니풍) — 컷별 그림 계획 (만드는 법은 「경비원 장부」와 같음)
python 연재/화성정비반장/화성정비반장_단편.py job <저장폴더> [컷번호 ...]  → klein_worker 그림 주문서 job.json
python 연재/화성정비반장/화성정비반장_단편.py project <그림폴더>         → 프로젝트 파일에 [사진] 줄을 넣음 (나레이션 문단은 그대로)
  - 인물 기준 그림은 앞모습 조각(캐릭터시트/_앞_<인물>.png) — 네 칸 시트를 넣으면 같은 사람이 두 번 그려졌음(경비원 장부에서 배움)
  - '귀환선' = 사용자가 준 함대 설계도의 지구 전투순양함(참고/귀환선_기준.png)을 지구 귀환선으로 씀 (사용자 2026-11-06 "이것도 활용해")
  - 기지·사람 이름은 모두 지어낸 것"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SHEETS = os.path.join(HERE, "캐릭터시트")
SHIP = os.path.join(HERE, "참고", "귀환선_기준.png")
PROJ = os.path.join(HERE, "화성정비반장_프로젝트.json")

STYLE = ("Japanese anime style scene, TV anime screenshot, clean crisp line art, anime cel shading with soft shadows, "
         "realistic human proportions, natural colors, detailed anime background art, near-future science fiction on Mars")
LOOK = {
    "반장": "a 62-year-old Korean man, short and sturdy maintenance chief with gray buzz-cut hair, short gray stubble beard, deep wrinkles, worn faded orange mechanic jumpsuit with short sleeves and patched knees, brown leather tool belt, scratched wristwatch, dark brown work boots",
    "관리자": "a 38-year-old Korean man, tall and slim with neatly side-parted black hair, sharp cold eyes, clean-shaven, sleek white high-collar futuristic uniform jacket with thin light-blue trim, white trousers, white boots",
    "유나": "a 28-year-old Korean young woman with shoulder-length wavy dark brown hair, a few freckles, bright determined eyes, orange mechanic jumpsuit with rolled sleeves over a white t-shirt, gray tool belt, black boots",
    "로봇": "a human-sized humanoid maintenance robot made of glossy silver-gray metal panels with dark gray joints, an angular bald metal head with one horizontal glowing blue light visor instead of a face, no hair, three-fingered metal hands",
    "귀환선": "the large gray armored Earth spaceship from the reference image (a long blocky battlecruiser hull with blue engine glow), used as the Earth return ship",
}
EXT = "outside a domed Mars colony base with metal modules and glass domes on the red rocky Martian desert, dusty orange sky"
PORT = "the spaceport landing pad of a Mars colony base on the red desert, dusty orange sky"
WORK = "the maintenance workshop inside a Mars base: metal walls, pipes, tool racks, workbenches, warm work lamps, a small round window showing the red Martian desert"
OXY = "the oxygen plant room of a Mars base: large cylindrical oxygen generator tanks, pumps, thick pipes and valves, metal grating floor"
STORE = "a cramped storage room in a Mars base: metal shelves stacked with parts boxes, a small work table with a desk lamp"
CTRL = "the control room of a Mars base: curved desks with many floating holographic screens, a big window to the red Martian landscape"
MESS = "a Mars base cafeteria with metal tables and crew members in jumpsuits eating"
CORR = "a corridor inside a Mars base with metal walls, pipes and ceiling lights"
OFFICE = "the manager's office in a Mars base: clean white walls, a white desk with a holographic screen, a window to the red desert"
DARK = ", the power is out, only red emergency lights, dust in the air"
NOTE = "the paper pages are covered in tiny handwriting too small and blurry to read"

# (컷, 문단 번호들, 나오는 인물, (안 씀), 다른 사람 나와도 됨, 장소, 장면(영어), 화면 설명)
CUTS = [
    ("c01", [1], [], False, False, EXT + ", early morning with a pale sun", "wide establishing shot of the Mars colony base in the morning, red dust blowing gently. No people", "화성 개척 기지 삼호기"),
    ("c02", [2], ["반장"], False, False, OXY, "the old maintenance chief tightening a big bolt on an oxygen pump with a long wrench, a small worn paper notebook sticking out of his chest pocket", "정비반장 노병철"),
    ("c03", [3], ["반장"], False, False, WORK, "close-up of the old chief's rough hand writing in a worn paper notebook with a pencil on a workbench, " + NOTE, "손으로 적는 수첩"),
    ("c04", [4, 5], ["유나", "반장"], False, False, WORK, "the young woman mechanic smiling and teasing, the old chief closing his small notebook calmly", "또 적으세요?"),
    ("c05", [6], ["반장"], False, False, WORK, "medium close-up of the old chief speaking wisely with a faint smile, holding his closed notebook", "기계 소리는 사람이 적는다"),
    ("c06", [7], ["관리자", "귀환선"], False, False, PORT, "the big gray Earth spaceship landed on the pad behind, the slim man in a white uniform walking down the ramp toward the base with a cold confident face", "지구에서 온 새 운영관리자"),
    ("c07", [8, 9], ["관리자", "반장"], False, False, WORK, "the man in the white uniform standing in the workshop doorway and announcing coldly with one hand raised, the old chief listening with a stiff face", "모든 정비는 로봇이 합니다"),
    ("c08", [10], ["로봇"], False, True, WORK, "a neat row of many identical silver-gray maintenance robots of the same design standing in the workshop, an old battered toolbox being pushed away into a dark corner. No people", "은빛 로봇 열 대"),
    ("c09", [11], ["관리자", "반장"], False, False, WORK, "the man in the white uniform standing with his arms folded, looking down at the old chief with a cold dismissive smirk; the old chief stands silently with his hands at his sides and a hurt stiff face; they do not touch, no handshake", "구형 방식은 필요 없다"),
    ("c10", [12], ["반장"], False, False, STORE, "the old chief alone in the storage room counting parts boxes on a shelf with a clipboard, lonely silent face", "창고로 밀려난 반장"),
    ("c11", [13], ["반장"], False, True, MESS, "young crew members at a table whispering and laughing while glancing toward the old chief, who eats alone at a far table", "식당의 수군거림"),
    ("c12", [14, 15], ["로봇", "반장"], False, False, STORE + ", night", "one silver-gray robot standing quietly at the open storage room door at night, its blue visor glowing, looking at the old chief who sits at the work table", "밤마다 찾아오는 엠세븐"),
    ("c13", [16], ["반장", "로봇"], False, False, STORE + ", night", "the old chief holding up a small worn metal bearing part toward the robot, the robot's blue visor flickering with curiosity", "닳은 부품을 보여 주는 반장"),
    ("c14", [17], ["반장", "유나"], False, False, STORE + ", evening", "the old chief showing his open notebook to the young woman mechanic at the work table, she listens eagerly, " + NOTE, "기계 소리를 듣는 법"),
    ("c15", [18, 19], ["반장"], False, False, OXY + ", night with dim blue lights", "the old chief stopping in front of a large oxygen pump, leaning his ear close to the metal casing to listen, serious face", "삼 번 펌프의 쇳소리"),
    ("c16", [20, 21], ["관리자", "반장"], False, False, OFFICE, "the man in the white uniform seated at his desk pointing at a holographic screen showing a green check mark, not looking at the old chief who stands in front of the desk", "헬리오스 판정은 정상"),
    ("c17", [22, 23, 24], ["유나", "관리자"], False, False, OFFICE, "the young woman mechanic pleading earnestly with both hands clasped, the man in the white uniform answering sternly with a cold glare", "신입이 할 일은 규정"),
    ("c18", [25], [], False, True, CTRL + ", red alarm lights flashing", "crew members in the control room looking up in alarm at a big holographic map of Mars showing a giant swirling dust storm, no text. No main characters", "기록에 없던 모래폭풍"),
    ("c19", [26], ["관리자"], False, True, CTRL, "the man in the white uniform standing confidently in front of the holographic screens, calmly raising one hand to calm the worried crew", "피해 확률 삼 퍼센트"),
    ("c20", [27], ["반장"], False, False, STORE, "the old chief flipping through the old pages of his notebook and stopping at one page, eyes narrowing with worry, " + NOTE, "이천사십일 년의 기록"),
    ("c21", [28], ["반장"], False, False, STORE + ", late night under a desk lamp", "the old chief alone filing and shaping a small round metal bearing by hand at the work table, metal shavings, focused", "손으로 깎는 베어링"),
    ("c22", [29], [], False, False, EXT, "a gigantic dark red dust storm wall swallowing the domed Mars base, the sky turning dark crimson, wind and sand. No people", "기지를 덮친 폭풍"),
    ("c23", [30], ["로봇"], False, True, WORK + DARK, "a bright blue electric spark bursting from a wall panel, all screens going black, several identical silver-gray robots frozen motionless with their visors turned dark. No people", "멈춰 버린 헬리오스와 로봇"),
    ("c24", [31, 32], [], False, True, CTRL + DARK, "the dark control room lit by red emergency lights, a large red warning symbol and a draining oxygen gauge bar flashing on a screen, no text, worried crew members. No main characters", "남은 산소 여섯 시간"),
    ("c25", [33, 34], ["관리자"], False, True, CTRL + DARK, "the man in the white uniform panicking, shouting with sweat on his face while tapping dead black screens", "설명서가 없다"),
    ("c26", [35, 36], ["유나"], False, False, CORR + DARK, "the young woman mechanic running down the dark corridor with a flashlight beam cutting through the dust, then pounding on a metal door", "창고로 달려간 유나"),
    ("c27", [37], ["반장"], False, False, STORE + DARK, "the old chief already in his orange jumpsuit, standing ready and determined, holding a small metal bearing in one hand and his worn notebook in the other", "이미 준비한 반장"),
    ("c28", [38, 39], ["관리자", "반장"], False, False, CTRL + DARK, "at the control room door, the man in the white uniform bowing his head deeply to the old chief, humbled", "부탁드립니다"),
    ("c29", [40, 41], ["반장", "유나"], False, False, OXY + DARK, "the old chief opening his notebook to a page while the young woman mechanic holds a flashlight over it, both serious, " + NOTE, "수동 재가동 열두 단계"),
    ("c30", [42], ["반장"], False, False, OXY + DARK, "close-up of the old chief's gloved hands unscrewing bolts on a pump casing in a flashlight beam, a cracked broken bearing visible inside, dust floating", "반쯤 부서진 베어링"),
    ("c31", [43], ["반장"], False, False, OXY + DARK, "the old chief gripping a large rusty manual crank wheel with both hands and turning it with all his strength, gritted teeth", "수동 손잡이를 돌리다"),
    ("c32", [44], [], False, False, OXY, "the big oxygen generator coming back to life, its indicator lights turning on one by one in green, a soft stream of air from vents, dust swirling. No people", "다시 숨을 쉬는 산소 공장"),
    ("c33", [45], [], False, False, CTRL, "close-up of a holographic gauge in the control room, the oxygen bar rising back up and glowing green, no text, no numbers. No people", "올라가는 산소"),
    ("c34", [46], ["반장", "유나"], False, True, CTRL, "crew members clapping with relief, the young woman mechanic holding a flashlight and hugging the old chief, who smiles awkwardly", "숨죽였던 박수"),
    ("c35", [47], [], False, False, EXT + ", after the storm with a clear pale sky", "the Mars base standing safe after the storm, red sand piled against the domes, calm and quiet. No people", "폭풍이 지나간 기지"),
    ("c36", [48, 49], ["관리자"], False, False, OFFICE + ", shown as a memory with a soft blue tint", "the man in the white uniform alone at his desk secretly sliding a holographic settings slider upward with one finger, a sly look, no text", "몰래 높인 경고 기준"),
    ("c37", [50], ["로봇"], False, False, WORK + ", quiet light", "one silver-gray robot standing alone and still, its blue visor glowing dimly, as if it knew but stayed silent", "말하지 않았던 인공지능"),
    ("c38", [51], ["관리자"], False, False, OFFICE, "the man in the white uniform reading a holographic message at his desk, his face going pale, frozen", "본사의 결정"),
    ("c39", [52, 53], ["관리자", "반장", "귀환선"], False, False, PORT, "the big gray Earth spaceship waiting on the pad behind, the man in the white uniform with a small travel bag speaking quietly and humbly to the old chief", "떠나는 날의 사과"),
    ("c40", [54, 55], ["반장", "관리자"], False, False, PORT, "the old chief patting the man in the white uniform on the shoulder with a gentle steady face", "숫자를 누가 정했는지"),
    ("c41", [56], ["반장", "로봇"], False, False, WORK, "the old chief's battered toolbox back on the workbench, the old chief and one silver-gray robot working side by side at the bench", "돌아온 공구함"),
    ("c42", [57], ["반장", "로봇"], False, False, WORK, "the silver-gray robot leaning in to look at the old chief's open notebook while the chief smiles and holds a pump part up to its head to let it hear, " + NOTE, "로봇에게 들려주는 펌프 소리"),
    ("c43", [58], ["반장", "유나"], False, False, WORK, "the old chief handing a brand-new paper notebook to the young woman mechanic with both hands, she receives it with a moved smile", "새 수첩"),
    ("c44", [59], ["귀환선"], False, False, EXT + ", Martian sunset with a beautiful blue glow around the small setting sun", "the famous blue sunset of Mars over the domed base, the gray Earth spaceship rising far away in the sky as a small silhouette. No people", "화성의 푸른 노을"),
    ("c45", [60], ["반장"], False, False, WORK + ", blue sunset light through the round window", "the old chief sitting by the round window writing the last line in his notebook, peaceful smile, blue light on his face", "오늘도, 기지는 숨을 쉰다"),
]


def paragraphs(story):
    return [p.strip() for p in re.split(r"\n\s*\n", story) if p.strip() and not p.strip().startswith("[사진")]


def ref_of(nm):
    return SHIP if nm == "귀환선" else os.path.join(SHEETS, "_앞_" + nm + ".png")


def prompt(cut):
    cid, _, who, _, crowd, place, desc, _ = cut
    people = [nm for nm in who if nm != "귀환선"]
    looks = [f"{'the subject' if nm == '귀환선' else 'character'} from reference image {k + 1}: {LOOK[nm]}" for k, nm in enumerate(who)]
    p = f"{STYLE}. "
    if looks:
        p += "In the scene: " + "; ".join(looks) + ". "
    if people:
        p += "Each character appears only once, exactly two arms and two legs and five fingers on each hand, head and face turned the same direction as the body. "
    if "로봇" in people:
        p += "The robot is exactly the silver-gray robot design from its reference, with no hair and no clothes. "
    if not people:
        p += "No main characters. "
    if not crowd:
        p += "No other people besides those described in the scene. "
        if len(people) == 1:
            p += "Exactly one person in the whole image, no twin, no copy, no reflection. "
    else:
        p += "Other people are ordinary base crew in plain gray or blue jumpsuits who look clearly different from the main characters. "
    p += f"Scene: {desc}. Setting: {place}. "
    p += "Cinematic composition, full-bleed image, no border, no frame, no paper edges. No speech bubbles, no readable text, no letters, no logos, no signs with writing."
    return p


def main():
    cmd, folder = sys.argv[1], sys.argv[2]
    if cmd == "job":
        only = set(sys.argv[3:])
        items = [{"id": c[0], "width": 1024, "height": 576, "seed": 500 + k, "prompt": prompt(c), "refs": [ref_of(nm) for nm in c[2]]}
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
        p["cast"] = [{"name": nm, "look": LOOK[nm], "sheet": os.path.join(SHEETS, nm + ".png")} for nm in LOOK if nm != "귀환선"]
        json.dump(p, open(PROJ, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(PROJ, len(CUTS), "cuts")


if __name__ == "__main__":
    main()
