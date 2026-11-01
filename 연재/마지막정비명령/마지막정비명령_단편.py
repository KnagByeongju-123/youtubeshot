"""「마지막 정비 명령」 단편 (약 10분, 미니드라마 스타일 애니 — 로봇과 인간, 한 편으로 끝남) — 대본 + 컷별 그림 계획
python 연재/마지막정비명령/마지막정비명령_단편.py job <저장폴더>   → 그림 주문서(klein_worker 용) job.json
python 연재/마지막정비명령/마지막정비명령_단편.py project <그림폴더> → 프로젝트 파일(render_project 용) 연재/마지막정비명령/마지막정비명령_단편.json
  영상은 render_project.py <프로젝트> --대본그대로 --형식고정
대본의 {컷번호} 자리에 그 컷 그림이 들어감 (문단마다 한 장 — 문단이 바뀔 때 그림이 바뀜). chars = 그 컷에 나오는 인물(캐릭터 시트를 기준 그림으로 넣음)
나레이션 한 명(남자 성우 4 · 정상 속도 · 톤 -1.5)이 대사까지 모두 읽음 (사용자 결정 2026-10-31) → DIALOGUE 없음
사람·도시 이름은 모두 지어낸 것"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TITLE = "마지막 정비 명령"

STYLE = ("Japanese anime style scene, TV anime screenshot, clean crisp line art, anime cel shading with soft shadows, "
         "realistic human proportions, natural colors, detailed anime background art")
PARK = "an overgrown abandoned city park in a ruined futuristic city, cracked skyscrapers covered in vines in the background, old swings, a small carousel, stone benches and flower beds kept neat and clean"
MEMORY = "shown as a translucent blue hologram memory projected in the air"
NOT_PARK = {"c06", "c08", "c09", "c45"}        # 공원 밖 장면 (나머지는 모두 공원 야외 — 로봇 시트 때문에 공장·연구실 배경이 자꾸 나와서 장소를 꼭 적음)
CROWD = {"c31", "c36", "c45"}                 # 다른 사람이 나와도 되는 장면 (수거단·피난 인파)
PARK_SET = ("Setting: outdoors in the overgrown abandoned city park with trees, grass, flower beds, stone paths and old benches, "
            "ruined skyscrapers far in the background. Not indoors, not a factory, no machines, no pipes, no monitors, no signs")

# (컷번호, 나오는 인물, 그림 설명(영어), 화면 설명(한국어))
CUTS = [
    ("c01", [], f"wide establishing shot at dawn, {PARK}, mist, no people", "300년 동안 아무도 오지 않은 공원"),
    ("c02", ["보리"], f"the robot sweeping fallen leaves with a long broom on a park path at sunrise, {PARK}", "낙엽을 쓰는 로봇"),
    ("c03", ["보리"], "close-up of the robot's three-fingered metal hands carefully tightening a bolt on an old swing chain", "그네를 고치는 손"),
    ("c04", ["보리"], "the robot watering a neat flower bed with a dented metal watering can, colorful flowers among ruins", "꽃에 물 주기"),
    ("c05", ["보리"], "the robot gently wiping a small worn metal plaque on a stone bench with a cloth, the plaque surface blank and weathered with no letters", "벤치의 이름판을 닦는 로봇"),
    ("c06", [], "wide shot of a ruined futuristic city skyline, empty streets, abandoned flying vehicles rusted on the road, birds flying, no people", "사람이 떠난 도시"),
    ("c07", ["보리"], "the robot standing alone in the middle of the empty park at dusk, looking up at the orange sky, lonely silhouette", "혼자 남은 로봇"),
    ("c08", [], "a violent thunderstorm over the ruined city at night, a battered salvage airship struggling in the wind above the skyline", "폭풍 속 고철 수거선"),
    ("c09", ["루미"], "the girl falling and tumbling out of a small cargo hatch of an airship into the dark stormy sky, her raincoat flapping, a frightened face", "떨어지는 소녀"),
    ("c10", ["루미"], "the girl lying unconscious on soft wet grass in the park after the storm, early morning light, broken branches around", "공원에 쓰러진 소녀"),
    ("c11", ["보리", "루미"], "the robot kneeling beside the girl lying on the grass, its blue eyes glowing as it scans her, morning mist", "소녀를 발견한 로봇"),
    ("c12", ["보리", "루미"], "the girl waking up and sitting up startled, staring wide-eyed at the tall robot bending over her", "놀라 깨어난 소녀"),
    ("c13", ["보리"], "close-up of the robot's round head and two glowing blue eyes, polite and calm expression, soft light", "손님을 맞는 로봇"),
    ("c14", ["루미"], "the girl hugging her knees on the grass, looking around the empty park nervously, holding her silver locket", "겁먹은 소녀"),
    ("c15", ["보리", "루미"], "the robot offering a clean folded towel and a bright red apple to the girl sitting on a stone bench", "사과를 건네는 로봇"),
    ("c16", ["루미"], "the girl biting the apple and smiling for the first time, cheeks full, sitting on the bench", "처음 웃는 소녀"),
    ("c17", ["보리", "루미"], "the girl sitting on an old swing while the robot gently pushes it from behind, morning sunlight, flowers around", "그네를 밀어 주는 로봇"),
    ("c18", ["루미"], "close-up of the girl laughing joyfully on the swing, hair flying, sunlight behind her", "웃음소리"),
    ("c19", ["보리"], "close-up of the robot's blue eyes flickering with small light patterns as if surprised, a tiny glowing waveform in its eye", "기록에 없는 소리"),
    ("c20", ["보리", "루미"], "the girl pointing up at the robot and talking cheerfully, the robot tilting its head curiously", "이름을 지어 주는 소녀"),
    ("c21", ["보리", "루미"], "the girl tying her yellow hair ribbon around the robot's arm while the robot stays still, warm afternoon light", "보리라는 이름"),
    ("c22", [], "an old rusted small carousel in the park with faded painted horses, vines on the roof, one horse broken", "멈춘 회전목마"),
    ("c23", ["보리"], "the robot lying under the old carousel fixing gears with tools, sparks, the girl's yellow raincoat visible watching nearby", "회전목마를 고치는 로봇"),
    ("c24", ["보리", "루미"], "the old carousel turning again with soft lights glowing, the girl riding a painted horse with arms raised in joy, the robot standing beside it", "300년 만에 돌아가는 회전목마"),
    ("c25", ["보리", "루미"], "night in the park, the girl and the robot sitting side by side on a bench looking at a sky full of stars over the ruined city", "별을 보는 둘"),
    ("c26", ["루미"], "close-up of the girl's hands opening a small old silver round locket, inside a tiny faded photo of a woman's face, no text", "엄마가 준 목걸이"),
    ("c27", ["보리"], "close-up of the robot's blue eyes reflecting a tiny locket photo, a long pause, light flickering", "멈칫하는 로봇"),
    ("c28", ["루미"], "the girl asleep curled up on the bench under a blanket of big leaves, the robot's green scarf laid over her, moonlight", "잠든 소녀"),
    ("c29", ["보리"], "the robot standing guard beside the sleeping girl at night, watching the dark city, fireflies", "밤을 지키는 로봇"),
    ("c30", [], "morning, a large battered salvage airship with mechanical claws descending onto the edge of the park, blowing leaves and dust", "수거선이 내려옴"),
    ("c31", ["강철수"], "the huge scavenger boss stepping down from the airship ramp, looking around the park greedily, his crew behind him in work gear", "고철 수거단 두목 강철수"),
    ("c32", ["도현"], "the father running down the ramp desperately, looking around the park for his daughter, worried face", "딸을 찾는 아빠"),
    ("c33", ["도현", "루미"], "the father and the girl running to each other and hugging tightly in the park, tears of relief", "다시 만난 부녀"),
    ("c34", ["강철수", "보리"], "the scavenger boss staring at the tall old robot standing near the flower bed, a calculating smirk", "로봇을 노려보는 두목"),
    ("c35", ["강철수"], "close-up of the scavenger boss grinning and tapping the big wrench on his palm", "300년 된 부품값"),
    ("c36", ["보리"], "scavenger crew members throwing steel chains around the robot, the robot standing still without resisting, its eyes dim", "쇠사슬에 묶이는 로봇"),
    ("c37", ["보리"], "the robot pulled down onto its knees by chains on the park path, broom fallen on the ground, leaves scattered", "무릎 꿇린 로봇"),
    ("c38", ["루미", "도현"], "the girl screaming and pulling away from her father's arms, reaching out toward the robot", "막아서려는 루미"),
    ("c39", ["보리"], "close-up of the robot's dim blue eyes looking calmly at the girl, accepting, a sad gentle feeling", "손님을 해치지 말 것"),
    ("c40", ["루미", "강철수"], "the small girl in the yellow raincoat standing with arms spread wide in front of the chained robot, facing the huge scavenger boss", "로봇 앞을 막아선 루미"),
    ("c41", ["보리", "루미"], "the girl's silver locket glowing as it touches the robot's chest panel, a beam of blue light shooting up from the robot", "목걸이에 반응하는 로봇"),
    ("c42", ["윤서"], f"a young woman engineer standing in the same park 300 years ago when it was new and full of flowers, {MEMORY}", "300년 전의 기록"),
    ("c43", ["윤서", "보리"], f"the young woman engineer placing her hand on a brand-new shiny white maintenance robot's chest, speaking gently, {MEMORY}", "윤서의 부탁"),
    ("c44", ["윤서"], f"close-up of the young woman engineer with tears in her eyes but smiling, a silver round locket at her neck, {MEMORY}", "같은 목걸이"),
    ("c45", [], f"crowds of people boarding huge evacuation ships leaving the city under a red sky 300 years ago, {MEMORY}", "모두가 떠나던 날"),
    ("c46", ["도현"], "the father staring at the hologram in shock, slowly taking out an old family photo from his jacket pocket, the photo face blank and faded", "아빠가 알아본 얼굴"),
    ("c47", ["도현", "루미"], "the father kneeling down to the girl's height, both looking at the locket and the hologram, realization on their faces", "고조할머니 윤서"),
    ("c48", ["강철수"], "the scavenger boss stepping back, frowning and confused, crew members lowering the chains", "물러서는 두목"),
    ("c49", ["보리"], "the robot projecting a glowing blue holographic official registry document with an abstract seal symbol and lines, no readable letters", "300년 전 등록 기록"),
    ("c50", ["도현", "강철수"], "the father standing firm facing the scavenger boss, pointing at the hologram document, determined face", "우리 가족의 공원"),
    ("c51", ["강철수"], "the scavenger boss turning away grumbling and walking back to the airship with his crew, dust blowing", "떠나는 수거단"),
    ("c52", ["보리", "루미"], "the girl hugging the robot's leg tightly as the chains fall to the ground, the robot's eyes brightening", "풀려난 보리"),
    ("c53", ["보리"], "close-up of the robot's blue eyes glowing warmly, a gentle bow of its head", "명령 완료"),
    ("c54", ["보리", "루미", "도현"], f"sunset in the park, the girl on the swing laughing, the robot pushing the swing, the father sitting on the bench smiling, {PARK}", "300년 만의 웃음소리"),
    ("c55", [], "wide shot of the park at sunset with the carousel lights on and flowers blooming among the ruined city, warm golden light, hopeful", "다시 열린 공원"),
]

STORY = """{c01}

300년 동안, 아무도 오지 않은 공원이 있었습니다. 그리고 그 공원을, 매일 아침 쓸고 닦는 로봇이 하나 있었습니다.

{c02}

정비 로봇 칠호. 해가 뜨면 낙엽을 쓸고, 길에 떨어진 돌을 치웠습니다.

{c03}

녹슨 그네 줄을 조이고, 삐걱거리는 경첩에 기름을 쳤습니다. 아무도 타지 않는 그네였습니다.

{c04}

꽃밭에는 물을 주었습니다. 무너진 빌딩 숲 한가운데, 이 공원의 꽃만은 300년 동안 한 번도 시들지 않았습니다.

{c05}

그리고 마지막으로, 벤치에 붙은 작은 이름판을 닦았습니다. 글자는 오래전에 닳아 없어졌지만, 칠호는 하루도 빠뜨리지 않았습니다.

{c06}

사람들은 300년 전, 이 도시를 떠났습니다. 큰 재난이 닥쳤고, 모두 하늘 위의 도시로 옮겨 갔습니다.

{c07}

남은 것은 칠호 하나. 칠호의 기억 장치에는, 단 하나의 명령만 남아 있었습니다. 공원을 지켜라.

{c08}

그러던 어느 밤, 도시 위로 큰 폭풍이 몰아쳤습니다. 낡은 고철 수거선 한 척이, 바람에 이리저리 흔들렸습니다.

{c09}

그리고 화물칸 문이 덜컹 열리며, 작은 아이 하나가 어둠 속으로 떨어졌습니다.

{c10}

다음 날 아침. 젖은 풀밭 위에, 노란 비옷을 입은 소녀가 쓰러져 있었습니다.

{c11}

칠호가 다가가 소녀를 살폈습니다. 심장은 고르게 뛰고 있었고, 몸은 조금 차가웠습니다. 다친 곳은 없었습니다.

{c12}

눈을 뜬 소녀가 비명을 질렀습니다. 키가 두 배나 큰 쇠붙이가, 자기를 내려다보고 있었으니까요.

{c13}

"놀라게 해서 죄송합니다. 공원에 오신 것을 환영합니다. 이용 시간은, 해가 질 때까지입니다."

{c14}

소녀의 이름은 루미, 열 살이었습니다. 아빠와 함께 고철 수거선을 타고 다니다, 폭풍에 떨어진 것이었습니다.

{c15}

칠호는 깨끗한 수건과 빨간 사과 하나를 내밀었습니다. 공원 뒤편 사과나무에서, 300년 동안 혼자 따 모은 것이었습니다.

{c16}

루미는 망설이다 사과를 한 입 베어 물었습니다. 그리고 처음으로, 웃었습니다.

{c17}

그날 오후, 칠호는 처음으로 그네에 탄 손님을 밀어 주었습니다.

{c18}

까르르. 공원 가득 웃음소리가 퍼졌습니다.

{c19}

칠호의 눈이 깜빡였습니다. 기록에 없는 소리였습니다. 300년 동안, 이 공원에서 한 번도 들어 본 적 없는 소리.

{c20}

"너는 이름이 뭐야?" "정비 로봇 칠호입니다." "에이, 그건 이름이 아니잖아."

{c21}

루미는 자기 노란 리본을 칠호의 팔에 묶어 주었습니다. "오늘부터 너는 보리야. 우리 집 강아지 이름이었는데, 너한테 줄게."

{c22}

공원 한쪽에는, 멈춰 버린 회전목마가 있었습니다. 칠호가 아무리 고쳐도, 돌아가지 않던 기계였습니다.

{c23}

"이거 돌아가면 좋겠다." 루미의 한마디에, 보리는 밤새 회전목마 밑에 들어가 톱니를 갈아 끼웠습니다.

{c24}

다음 날 아침. 300년 만에, 회전목마에 불이 들어왔습니다. 루미는 말 위에서 두 팔을 번쩍 들었습니다.

{c25}

그날 밤, 둘은 벤치에 나란히 앉아 별을 보았습니다. 루미가 물었습니다. "보리야, 넌 왜 혼자 여기 있어?"

{c26}

"공원을 지키라는 명령을 받았습니다." 루미는 목에 건 작은 은 목걸이를 열었습니다. 안에는, 빛바랜 여자의 사진이 들어 있었습니다. "엄마가 준 거야. 우리 집에 아주 오래전부터 내려온 거래."

{c27}

보리의 눈이, 아주 잠깐 멈추었습니다. 그리고 아무 말도 하지 않았습니다.

{c28}

루미는 보리의 초록 목도리를 덮고 잠이 들었습니다.

{c29}

보리는 밤새 그 옆을 지켰습니다. 그날 밤, 보리의 기록에는 이런 줄이 하나 늘었습니다. 손님, 한 명.

{c30}

다음 날 아침. 거대한 집게발을 단 고철 수거선이, 공원 끝자락에 내려앉았습니다.

{c31}

맨 앞에 선 사람은 수거단 두목, 강철수였습니다. 버려진 도시에서 쓸 만한 쇠붙이를 뜯어 파는 사람이었습니다.

{c32}

그 뒤에서, 한 남자가 정신없이 뛰어 내려왔습니다. "루미야! 루미야!"

{c33}

루미의 아빠, 도현이었습니다. 부녀는 공원 한가운데서, 서로를 꼭 끌어안았습니다.

{c34}

그런데 강철수의 눈은, 다른 곳에 꽂혀 있었습니다. 꽃밭 옆에 선, 키 큰 로봇이었습니다.

{c35}

"이야, 300년 된 정비 로봇이라. 이 정도면, 부품값만 해도 꽤 나오겠는데?"

{c36}

수거단이 쇠사슬을 던졌습니다. 보리는 피하지 않았습니다. 손님을 해치지 말 것. 그것이 보리의 두 번째 명령이었습니다.

{c37}

쇠사슬에 끌려, 보리는 무릎을 꿇었습니다. 손에서 놓친 빗자루가, 낙엽 위로 굴렀습니다.

{c38}

"안 돼! 보리 데려가지 마!" 루미가 아빠의 품을 뿌리치고 뛰어나갔습니다.

{c39}

보리는 조용히 루미를 바라보았습니다. 괜찮다는 듯이. 300년 동안 혼자였으니, 이제는 괜찮다는 듯이.

{c40}

하지만 루미는 물러서지 않았습니다. 작은 노란 비옷이, 거대한 강철수 앞을 막아섰습니다.

{c41}

그 순간이었습니다. 루미의 은 목걸이가 보리의 가슴판에 닿자, 보리의 몸에서 파란빛이 솟아올랐습니다.

{c42}

공중에, 오래된 기록이 떠올랐습니다. 꽃이 가득 핀 300년 전의 공원. 그리고 흰 옷을 입은 젊은 여자 한 명.

{c43}

여자는 새것처럼 반짝이는 로봇의 가슴에 손을 얹고 말했습니다. "칠호야, 우리는 모두 떠나야 해. 하지만 언젠가, 우리 아이들이, 아이들의 아이들이 돌아올 거야."

{c44}

"그때, 아이들이 놀 곳을 지켜 줘. 이게, 내 마지막 부탁이야." 여자의 목에는, 루미의 것과 똑같은 은 목걸이가 걸려 있었습니다.

{c45}

그리고 그날, 사람들은 모두 떠났습니다. 칠호 혼자만 남겨 둔 채.

{c46}

도현은 떨리는 손으로 주머니에서 낡은 가족사진을 꺼냈습니다. 대대로 집안에 내려온 사진이었습니다.

{c47}

"윤서… 할머니." 사진 뒤에 적힌 이름, 루미네 고조할머니였습니다. 이 공원을 만든 기술자, 그리고 칠호를 만든 사람.

{c48}

강철수가 한 걸음 물러섰습니다. 수거단의 손에서, 쇠사슬이 느슨해졌습니다.

{c49}

보리의 눈에서 또 하나의 기록이 펼쳐졌습니다. 300년 전에 남긴 공원 등록 문서. 주인의 이름, 윤서. 그리고 상속인, 윤서의 자손.

{c50}

도현이 강철수 앞에 섰습니다. "들으셨죠. 이 공원도, 이 로봇도, 우리 가족 거요. 손대지 마십시오."

{c51}

강철수는 한참을 노려보다가, 혀를 차며 돌아섰습니다. 수거선은 먼지를 일으키며, 하늘로 떠났습니다.

{c52}

쇠사슬이 풀려 바닥에 떨어졌습니다. 루미는 보리의 다리를 꼭 끌어안았습니다.

{c53}

보리의 눈이, 따뜻하게 빛났습니다. "명령, 완료. 아이들이, 돌아왔습니다."

{c54}

그날 저녁, 300년 만에 공원에 웃음소리가 가득했습니다. 보리는 그네를 밀고, 도현은 벤치에 앉아 그 모습을 바라보았습니다.

{c55}

버려진 도시 한가운데, 꽃이 시들지 않는 공원이 하나 있습니다. 그리고 그 공원에는, 이제 매일 손님이 찾아옵니다. 마지막 명령을 끝까지 지킨, 키 큰 로봇을 만나러.
"""


def main():
    cmd, folder = sys.argv[1], sys.argv[2]
    chars = {c["name"]: c for c in json.load(open(os.path.join(HERE, "등장인물.json"), encoding="utf-8"))["chars"]}
    if cmd == "job":
        items = []
        for cid, who, desc, _ in CUTS:
            looks = "; ".join(f"person {k + 1} (the character from reference image {k + 1}): {chars[nm]['look']}"
                              + ("" if "hologram memory" in desc and nm == "보리" else ", " + chars[nm]["outfit"])
                              for k, nm in enumerate(who))   # 한글 이름은 그림에 글자로 나올 수 있어 번호로
            items.append({"id": cid, "width": 1024, "height": 576, "seed": 200 + len(items),
                          "refs": [os.path.join(HERE, chars[nm]["face"]) for nm in who if chars[nm].get("face")],
                          "prompt": f"{STYLE}, science fiction drama. "
                                    + (f"Characters: {looks}. Each person appears only once, exactly two arms and two legs, head and face turned the same direction as the body. " if looks else "No main characters. ")
                                    + ("The robot is exactly the slender white rusty humanoid robot from the reference sheet with a green scarf, not a different robot. " if "보리" in who else "")
                                    + ("" if cid in CROWD else "No other people in the scene. ")
                                    + f"Scene: {desc}. " + ("" if cid in NOT_PARK else PARK_SET + ". ")
                                    + "Cinematic composition, full-bleed image, no border, no frame, no paper edges. No speech bubbles, no text, no letters."})
        os.makedirs(folder, exist_ok=True)
        json.dump({"items": items}, open(os.path.join(folder, "job.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(len(items), "cuts")
    elif cmd == "project":
        story = STORY
        for cid, _, _, cap in CUTS:
            story = story.replace("{" + cid + "}", f"[사진: {os.path.join(folder, cid + '.png')} | {cap} | AI 생성 그림 (FLUX.2 klein) | ]")
        proj = {"ver": 7, "category": "장문", "genre": "[이야기] SF 드라마", "topic": TITLE, "title": TITLE,
                "story": story, "sources": [], "notes": "로봇과 인간 단편 「마지막 정비 명령」 (약 10분, 일본 애니풍)", "autophoto": False, "img_source": "그림: 애니 일러스트",
                "cast": [{"name": nm, "look": c["look"], "look_ko": c["look_ko"],
                          **({"sheet": os.path.join(HERE, c["face"])} if c.get("face") else {})} for nm, c in chars.items()],
                "settings": {"format": "롱폼 가로(1920×1080)", "narration": "on",
                             "layout": "자막형(큰 제목+사진+자막)", "img_fill": "전체 화면(글자가 사진 위에)",
                             "img_motion": "영상처럼(확대·이동·전환)", "fps": "24", "img_depth": "off",
                             "head_show": "안 보임(제목 카드만)", "head_pos": "숨김", "sub_split": "한 줄씩(문장·쉼표로 나눠 차례로)",
                             "img_label": "off", "sub_hide": "off",
                             "narr_voice": "Supertonic M4 (남성, 무료 로컬) [supertonic:M4]",   # 사용자 결정 2026-10-31
                             "narr_rate": "0", "narr_tone_m": -1.5}}
        out = os.path.join(HERE, "마지막정비명령_단편.json")
        json.dump(proj, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(out, len(story), "chars")


if __name__ == "__main__":
    main()
