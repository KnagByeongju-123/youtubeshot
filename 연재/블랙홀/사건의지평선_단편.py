"""「사건의 지평선 너머, 마지막 인간」 단편 (약 10분, 판타지 설정화풍 — 블랙홀 내부 세계, 한 편으로 끝남) — 대본 + 컷별 그림 계획
python 연재/블랙홀/사건의지평선_단편.py job <저장폴더>   → 그림 주문서(klein_worker 용) job.json
python 연재/블랙홀/사건의지평선_단편.py project <그림폴더> → 프로젝트 파일 연재/블랙홀/사건의지평선_단편.json
  영상은 render_project.py <프로젝트> --대본그대로 --길이고정 --형식고정
나레이션 한 명(남자 성우 4 · 정상 속도 · 톤 -1.5)이 대사까지 모두 읽음. 세계관·종족은 기획.md, 참고 그림 참고그림/"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TITLE = "사건의 지평선 너머, 마지막 인간"

STYLE = ("Fantasy concept art illustration, hand-drawn ink pen lines with soft watercolor washes, painterly, "
         "muted violet, teal and amber palette, glowing crystals, detailed environment")
# 장소 (그림마다 꼭 적음 — CLAUDE.md 6장 단편 그림 주문 요령)
VALLEY = ("Setting: a crystal valley inside a black hole, purple and teal glowing crystal clusters on dark rocks, "
          "a violet sky full of swirling distorted galaxies, a huge glowing white vortex (the singularity core) far above")
ARCH = ("Setting: a road of floating rock arches bent into rings in the air (gravity-warped arches) covered in purple crystals, "
        "floating rock islands, swirling galaxies in a violet sky, the glowing singularity vortex far above")
STORM = ("Setting: a violent gravity storm inside the black hole, the singularity vortex roaring with white light, "
         "rocks and crystal shards ripped into the air and swirling, purple lightning")
FOREST = ("Setting: the time-frozen planet, a forest of pale glowing teal trees with leaves frozen still in the air, "
          "soft light, floating motes that do not move, the violet galaxy sky above")
BORDER = ("Setting: the time-frozen planet where a sharp glowing line divides a frozen teal forest on one side from a golden sand desert "
          "with half-buried ancient ruins on the other side, violet galaxy sky")
SPACE = "Setting: outer space near a giant black hole with a bright orange accretion disk swirling around a perfect black sphere"

# (컷번호, 나오는 인물, 그림 설명(영어), 화면 설명(한국어), 장소)
CUTS = [
    ("c01", [], "a giant black hole in deep space, a glowing orange ring of matter spinning around a perfect black sphere, a tiny white exploration spaceship approaching it", "블랙홀로 다가가는 탐사선", SPACE),
    ("c02", ["서하"], "inside a cramped spaceship cockpit, the woman astronaut at a control panel looking out the window at the black hole, red warning lights", "탐사선 새벽호의 서하", ""),
    ("c03", [], "the small white spaceship being stretched and pulled into the black sphere, streaks of light bending around it", "사건의 지평선", SPACE),
    ("c04", ["서하"], "the woman astronaut floating unconscious in the dark, surrounded by bending streams of starlight, falling", "빛이 휘어지는 어둠", "Setting: a dark tunnel of bending starlight inside a black hole"),
    ("c05", ["서하"], "the woman astronaut lying on dark rocks among glowing crystals, slowly opening her eyes, her cracked helmet beside her", "눈을 뜬 서하", VALLEY),
    ("c06", [], "wide view of the crystal valley under a violet sky with twisted galaxies, floating rock islands, no people", "블랙홀 속 세계", VALLEY),
    ("c07", ["서하"], "close-up of the woman astronaut looking at the small glowing blue device on her wrist, a puzzled worried face", "손목 장치", VALLEY),
    ("c08", ["서하"], "the woman astronaut standing small in the vast valley, looking up at the huge glowing vortex in the sky, back view", "특이점 핵", VALLEY),
    ("c09", ["서하"], "the woman astronaut walking alone across glowing crystal rocks, calling out with a hand at her mouth", "동료를 찾는 서하", VALLEY),
    ("c10", ["고르"], "a huge stone golem standing still under a giant floating rock arch, like a statue, its orange cracks glowing faintly", "아치 아래의 바위", ARCH),
    ("c11", ["서하", "고르"], "the stone golem opening its glowing orange eyes and turning its huge head toward the small woman astronaut, who steps back in fear", "움직이는 바위", ARCH),
    ("c12", ["고르"], "close-up of the stone golem's heavy rock face, the ground around its feet vibrating with small floating pebbles", "땅을 울리는 목소리", ARCH),
    ("c13", ["서하"], "close-up of the woman astronaut's wrist device glowing with blue sound wave patterns, her surprised face", "번역되는 울림", ARCH),
    ("c14", ["서하", "고르"], "the stone golem crouching down to look at the small astronaut at eye level, the astronaut looking up, calmer now", "바위족 문지기 고르", ARCH),
    ("c15", ["고르"], "the stone golem pointing one huge stone finger up at the glowing vortex in the sky", "핵의 포효", ARCH),
    ("c16", [], "far away, the singularity vortex flashing brighter, a ring of white light pulsing outward across the violet sky", "다가오는 중력 폭풍", ARCH),
    ("c17", ["서하", "고르"], "the stone golem and the small astronaut walking together onto a narrow stone path along the curve of a floating rock arch", "아치를 건너는 길", ARCH),
    ("c18", ["서하"], "the astronaut walking upside down along the inner curve of the ring-shaped arch, her hair floating, amazed face", "거꾸로 걷는 길", ARCH),
    ("c19", ["빛해파리"], "a large glowing jellyfish creature floating down from above the arch, its tentacles shining blue and pink", "빛해파리족", ARCH),
    ("c20", ["서하", "빛해파리"], "the glowing jellyfish creature circling around the astronaut, light patterns rippling across its bell", "빛으로 하는 말", ARCH),
    ("c21", ["서하", "빛해파리"], "the jellyfish creature gently touching the astronaut's helmet with one glowing tentacle, a vision of light flowing between them", "빛해파리의 경고", ARCH),
    ("c22", [], "a white shockwave of gravity racing across the sky toward the arches, crystals shattering", "폭풍이 시작되다", STORM),
    ("c23", ["서하", "고르"], "the stone golem grabbing the astronaut and holding her close to its chest as rocks fly past", "서하를 감싸는 고르", STORM),
    ("c24", ["고르"], "the stone golem crouched like a boulder shield, flying crystal shards hitting its back and cracking it, orange light leaking from cracks", "갈라지는 고르의 등", STORM),
    ("c25", ["서하"], "the astronaut curled up safely in the shelter of a huge rock body, holding her breath, light flashing outside", "바위 품속에서", STORM),
    ("c26", [], "the storm calming, the vortex dimming, broken crystals slowly drifting in the quiet air", "폭풍이 지나가고", ARCH),
    ("c27", ["서하", "고르"], "the astronaut touching a deep glowing crack on the stone golem's arm with worry, the golem calm", "괜찮아, 바위는 다시 붙는다", ARCH),
    ("c28", ["서하", "고르"], "the stone golem and the astronaut standing at the end of the last arch, looking down at a planet below that is half frozen forest and half golden desert", "시간이 멈춘 행성", ARCH),
    ("c29", [], "a planet floating inside the black hole, split in two halves: one half a glowing teal frozen forest, the other half a golden desert with ancient ruins", "반은 숲, 반은 사막", "Setting: inside a black hole, violet galaxy sky"),
    ("c30", ["서하"], "the astronaut walking into a forest where falling leaves are frozen in the air, she touches a frozen leaf with one finger", "멈춘 나뭇잎", FOREST),
    ("c31", ["리아"], "a slender plant girl stepping out from behind a glowing tree, her leaf crown shining softly, watching curiously", "숲족 리아", FOREST),
    ("c32", ["서하", "리아"], "the plant girl and the astronaut facing each other in the frozen forest, the plant girl holding out an open hand", "처음 보는 얼굴", FOREST),
    ("c33", ["리아"], "the plant girl pressing her palm against the trunk of a huge glowing tree, light flowing up through its roots and branches", "기억을 담는 나무", FOREST),
    ("c34", ["서하", "리아"], "glowing memory images appearing as light shapes in the leaves above the plant girl and the astronaut, who look up in wonder", "나무의 기억", FOREST),
    ("c35", [], "a memory scene: a planet of grey stone mountains being pulled apart and swallowed into a black hole, shown in glowing amber light inside tree leaves", "고르의 고향", FOREST),
    ("c36", [], "a memory scene: a green planet with giant trees sinking into a swirl of light, shown in glowing teal light inside tree leaves", "리아의 고향", FOREST),
    ("c37", [], "a memory scene: a huge gas giant planet with floating jellyfish creatures being pulled into darkness, shown in glowing pink light", "빛해파리의 고향", FOREST),
    ("c38", ["서하"], "close-up of the astronaut realizing something, eyes wide, glowing memory lights reflected on her face", "모두 떨어져 온 이들", FOREST),
    ("c39", ["리아"], "the plant girl smiling gently and touching another glowing tree, a new memory light appearing", "마지막 기억", FOREST),
    ("c40", ["한도윤"], "a memory scene shown in glowing white light: an old man in a faded space suit and a leaf cloak planting a small tree sapling in the forest", "흰 옷을 입은 노인", FOREST),
    ("c41", ["서하"], "close-up of the astronaut gasping, a hand over her mouth, tears forming", "함장님?", FOREST),
    ("c42", ["서하"], "the astronaut looking at her wrist device showing two glowing clocks with very different numbers, abstract symbols, no readable text", "서로 다른 두 시계", FOREST),
    ("c43", [], "a diagram-like fantasy illustration: a tiny spaceship falling into a black hole while a long ribbon of years stretches out inside, sand flowing like an hourglass", "몇 초와 수십 년", SPACE),
    ("c44", ["한도윤"], "a memory scene: the old man sitting with a stone golem and a plant person around a small fire, teaching them, everyone calm", "종족들 사이의 노인", FOREST),
    ("c45", ["한도윤"], "a memory scene: the old man standing on a cliff at the border line of the frozen forest and the desert, raising his staff between two groups of creatures facing each other", "싸움을 멈춘 날", BORDER),
    ("c46", ["서하", "리아"], "the plant girl leading the astronaut by the hand along the glowing line between the forest and the desert", "숲과 사막의 경계", BORDER),
    ("c47", [], "a tall smooth standing stone at the border line with a carved simple picture of a small spaceship and a sun, no letters, flowers around it", "새겨진 돌", BORDER),
    ("c48", ["서하"], "the astronaut kneeling before the standing stone, touching the carving, her wrist device glowing as a hidden message plays", "남겨진 목소리", BORDER),
    ("c49", ["한도윤"], "a glowing hologram of the old man projected from a small device on the stone, smiling warmly as he speaks", "함장의 마지막 말", BORDER),
    ("c50", ["한도윤"], "close-up of the hologram old man's kind face, eyes wet, nodding", "늦게 와도 괜찮다", BORDER),
    ("c51", ["서하"], "the astronaut crying with a small smile, holding the old cracked helmet against her chest", "울고 웃는 서하", BORDER),
    ("c52", [], "five small trees of different kinds planted in a row next to the standing stone, each with a small round stone in front", "다섯 그루의 나무", BORDER),
    ("c53", ["서하", "리아"], "the plant girl handing the astronaut a small glowing tree sapling with both hands", "여섯 번째 나무", BORDER),
    ("c54", ["서하", "고르", "리아"], "the astronaut, the stone golem and the plant girl planting the small sapling together next to the other five trees", "함께 심는 나무", BORDER),
    ("c55", ["빛해파리"], "the glowing jellyfish creature floating above the new tree, sprinkling glowing spores like a blessing", "빛의 축복", BORDER),
    ("c56", ["서하"], "the astronaut taking off the wrist device and placing it on the standing stone, a peaceful decision on her face", "보내지 않을 신호", BORDER),
    ("c57", ["서하", "고르", "리아", "빛해파리"], "the astronaut, the stone golem, the plant girl and the jellyfish creature sitting together on a hill watching the glowing vortex calmly", "새로운 이웃들", FOREST),
    ("c58", ["서하"], "the astronaut standing on a cliff looking up at the twisted galaxies in the violet sky, back view, a gentle smile", "밖으로 나갈 수 없는 하늘", ARCH),
    ("c59", [], "wide view of the whole world inside the black hole: the glowing vortex, ring arches, the half forest half desert planet, crystals, peaceful", "특이점의 요람", VALLEY),
]

STORY = """{c01}

우주에서 가장 무거운 별의 무덤, 블랙홀. 빛조차 빠져나올 수 없는 그곳으로, 작은 탐사선 한 척이 다가가고 있었습니다. 블랙홀 바로 바깥을 돌며 관측만 하고 돌아오는, 3년짜리 임무였습니다. 그런데 이 이야기는, 그 배가 돌아오지 못한 날부터 시작됩니다.

{c02}

탐사선 새벽호. 여섯 명의 대원 가운데 막내는, 스물여덟 살 항법사 서하였습니다. 서하는 언제나 마지막까지 계기판을 들여다보는 사람이었습니다. 그리고 그날, 계기판의 숫자들이 하나둘 미쳐 가는 것을 가장 먼저 본 사람도 서하였습니다.

{c03}

그런데 엔진이 멈췄습니다. 계산보다 훨씬 강한 힘이 배를 끌어당겼고, 새벽호는 결국 경계선을 넘었습니다. 사람들은 그 선을, 사건의 지평선이라고 부릅니다. 한 번 넘으면, 빛도 소리도 다시는 나오지 못하는 선이죠. 새벽호의 마지막 교신은, 이 한마디였습니다. "모두, 서로를 꼭 붙잡아."

{c04}

서하의 기억은, 휘어진 별빛 속에서 끊어졌습니다.

{c05}

그리고 눈을 떴을 때, 서하는 차가운 돌바닥에 누워 있었습니다. 깨진 헬멧이 곁에 굴러 있었고, 숨은 쉴 수 있었습니다. 공기에서는, 비 온 뒤의 돌 냄새가 났습니다.

{c06}

블랙홀 안쪽에, 세상이 있었습니다. 보랏빛 수정이 자라는 골짜기, 공중에 떠 있는 바위섬, 그리고 일그러진 채 빙빙 도는 하늘의 은하들.

{c07}

손목 장치는 아무 신호도 잡지 못했습니다. 다른 대원 다섯 명의 위치도, 새벽호의 위치도 없었습니다. 화면에는 단 하나의 글자만 깜빡였습니다. 신호 없음.

{c08}

하늘 한가운데에는, 눈부신 소용돌이가 있었습니다. 모든 것을 삼킨 블랙홀의 심장, 특이점 핵이었습니다. 별 수천 개를 한데 녹인 것 같은 빛이, 숨을 쉬듯 천천히 밝아졌다 어두워졌다 했습니다.

{c09}

"함장님! 누구 없어요?" 서하의 목소리만, 수정 골짜기에 메아리쳤습니다. 대답은 돌아오지 않았습니다. 서하는 깨진 헬멧을 허리에 걸고, 일단 걷기로 했습니다.

{c10}

얼마나 걸었을까요. 공중에 고리처럼 휜 바위 다리 아래, 거대한 바위 하나가 서 있었습니다.

{c11}

그런데 그 바위가, 눈을 떴습니다. 주황빛 눈이 천천히 서하를 내려다보았습니다.

{c12}

땅이 낮게 울렸습니다. 말소리가 아니라, 발밑의 돌들이 떨리는 울림이었습니다.

{c13}

그 순간, 서하의 손목 장치가 빛나며 울림을 글로 바꾸기 시작했습니다. "또, 하나, 떨어졌군."

{c14}

바위의 이름은 고르. 이 바위 다리를 지키는 바위족 문지기였습니다. "겁내지 마라, 작은 것아. 여기서는 모두가 떨어져 온 이들이다." 서하는 그 말의 뜻을, 아직 알지 못했습니다.

{c15}

고르는 하늘의 소용돌이를 가리켰습니다. "핵이 곧 포효한다. 그 전에, 저 아치들을 건너야 한다. 아치 너머에는, 폭풍이 닿지 않는 곳이 있다."

{c16}

멀리서, 소용돌이가 한 번 번쩍였습니다. 하늘 끝까지, 하얀 고리 같은 빛이 퍼져 나갔습니다.

{c17}

둘은 고리처럼 휜 바위 다리, 중력 왜곡 아치 위로 올라섰습니다.

{c18}

이상한 길이었습니다. 아치의 안쪽 면을 따라 걷는데도 떨어지지 않았습니다. 서하는 하늘을 머리 위가 아니라 발아래에 두고 걸었습니다. 고르는 아무렇지 않게 성큼성큼 앞서 걸었습니다. 이 세계에서는, 위와 아래도 여러 개였습니다.

{c19}

그때, 위쪽에서 빛나는 무언가가 천천히 내려왔습니다. 커다란 해파리처럼 생긴 생명체였습니다.

{c20}

빛해파리족은 말을 하지 않았습니다. 대신 몸에 빛의 무늬를 흘려 보냈고, 손목 장치가 그것을 읽었습니다. "서둘러라. 서둘러라."

{c21}

빛해파리는 촉수 하나로 서하의 헬멧을 살짝 건드렸습니다. 그러자 머릿속에 장면 하나가 스쳤습니다. 하얗게 부서지는 수정들.

{c22}

그리고 정말로, 폭풍이 왔습니다. 핵이 포효하자, 하얀 중력의 물결이 하늘을 가르며 달려왔습니다.

{c23}

고르가 서하를 낚아채 가슴에 품었습니다. 바위와 수정 조각이 그들 곁을 스치며 날아갔습니다.

{c24}

고르는 커다란 바위처럼 몸을 웅크렸습니다. 날아온 조각들이 등을 때릴 때마다, 갈라진 틈에서 주황빛이 새어 나왔습니다.

{c25}

서하는 바위의 품속에서 숨을 죽였습니다. 밖에서는, 세상이 무너지는 소리가 들렸습니다. 쿵, 쿵. 바위 가슴 속에서는, 무언가 느리고 깊은 박동이 울리고 있었습니다. 고르의 심장 소리였습니다.

{c26}

얼마 뒤, 폭풍이 지나갔습니다. 부서진 수정 조각들만, 고요한 공기 속을 천천히 떠다녔습니다.

{c27}

서하가 고르의 팔에 생긴 깊은 틈을 만졌습니다. "다쳤잖아요." 고르가 낮게 울렸습니다. "괜찮다. 바위는, 다시 붙는다." 그리고 처음으로, 고르가 물었습니다. "작은 것아, 네 이름은 무엇이냐." "서하요." "서하. 좋은 울림이다."

{c28}

마지막 아치 끝에 다다르자, 아래로 행성 하나가 보였습니다.

{c29}

이상한 행성이었습니다. 반쪽은 푸르게 빛나는 숲, 나머지 반쪽은 황금빛 사막. 고르는 그곳을, 시간이 멈춘 행성이라고 불렀습니다.

{c30}

숲으로 들어서자, 떨어지던 나뭇잎이 공중에 그대로 멈춰 있었습니다. 서하가 손가락으로 건드려도, 잎은 꼼짝하지 않았습니다. 바람도, 물소리도, 새소리도 없었습니다. 마치 그림 속을 걷는 것 같았습니다.

{c31}

빛나는 나무 뒤에서, 누군가 고개를 내밀었습니다. 나무껍질 같은 피부에, 머리 대신 보랏빛 잎사귀를 단 소녀였습니다.

{c32}

숲족 소녀 리아였습니다. 리아는 서하를 오래 바라보더니, 손을 내밀었습니다. "오랜만에 보는 얼굴이야."

{c33}

리아가 커다란 나무에 손바닥을 댔습니다. 그러자 뿌리에서부터 가지 끝까지, 빛이 차오르기 시작했습니다.

{c34}

"이 숲의 나무들은, 기억을 담아. 이곳에 떨어진 모든 이들의 기억을."

{c35}

나뭇잎 사이로 장면 하나가 떠올랐습니다. 회색 돌산으로 가득한 행성이, 소용돌이 속으로 빨려 들어가고 있었습니다. 고르의 고향이었습니다.

{c36}

다음은 거대한 나무들이 자라는 초록 행성. 리아 조상들의 별이었습니다.

{c37}

그다음은 해파리들이 떠다니던 거대한 가스 행성.

{c38}

서하는 그제야 알았습니다. 이 세계의 종족들은 모두, 아주 오래전 블랙홀에 빨려 들어온 다른 별의 생명들이었습니다. 돌아갈 수 없게 된 이들이, 이곳을 새 고향으로 삼은 것이었습니다. 바위족도, 숲족도, 빛해파리족도. 그리고 이제, 서하도.

{c39}

리아가 다른 나무에 손을 얹었습니다. "그리고 이건, 가장 최근의 기억이야."

{c40}

빛 속에, 흰 옷을 입은 노인이 나타났습니다. 노인은 숲에 작은 나무를 심고 있었습니다. 낡고 빛바랜 우주복. 어깨의 주황색 줄무늬.

{c41}

서하의 숨이 멎었습니다. 주름진 얼굴이었지만, 분명히 알아볼 수 있었습니다. "함장님?"

{c42}

서하는 손목 장치를 보았습니다. 두 개의 시계가 있었습니다. 블랙홀 밖의 시간으로는, 새벽호가 경계를 넘은 지 겨우 몇 초. 그런데 이 안의 시간은, 전혀 다른 숫자를 가리키고 있었습니다.

{c43}

블랙홀 가까이에서는, 시간이 다르게 흐릅니다. 같은 순간에 경계를 넘었어도, 먼저 떨어진 사람과 나중에 떨어진 사람이 생길 수 있었습니다. 서하가 몇 초 늦은 사이, 동료들은 이곳에서 평생을 산 것이었습니다.

{c44}

기억은 계속 이어졌습니다. 함장 한도윤은 바위족과 숲족 사이에 앉아, 무언가를 가르치고 있었습니다.

{c45}

그리고 어느 날, 서로 싸우던 종족들 사이에 지팡이를 들고 섰습니다. 그날 이후, 숲과 사막의 종족들은 다시 싸우지 않았습니다.

{c46}

리아가 서하의 손을 잡고, 숲과 사막의 경계선으로 데려갔습니다.

{c47}

그곳에는 매끈한 돌기둥 하나가 서 있었습니다. 작은 우주선과 해가 새겨진 돌이었습니다.

{c48}

서하가 무릎을 꿇고 그림을 만지자, 손목 장치가 반응했습니다. 돌 속에, 새벽호의 신호가 숨어 있었습니다.

{c49}

빛으로 된 함장의 모습이 나타났습니다. "서하야. 이 말을 듣는다면, 결국 너도 왔구나. 넌 늘, 마지막까지 계기판을 확인하던 아이였지."

{c50}

"우리는 먼저 와서, 여기서 오래 살았다. 외롭지 않았다. 그러니 너도, 너무 슬퍼하지 마라. 늦게 와도, 괜찮다."

{c51}

서하는 울면서 웃었습니다. 깨진 헬멧을 가슴에 꼭 끌어안았습니다. 몇 초 늦었을 뿐인데, 다시는 만날 수 없는 사람들. 하지만 그들은, 이곳에서 행복했다고 말하고 있었습니다.

{c52}

돌기둥 곁에는 나무 다섯 그루가 나란히 서 있었습니다. 먼저 온 다섯 대원이 하나씩 남긴 나무였습니다.

{c53}

리아가 작은 묘목 하나를 두 손으로 건넸습니다. "여섯 번째 자리는, 계속 비어 있었어."

{c54}

서하와 고르와 리아가, 함께 흙을 덮었습니다. 바위 손과 나무 손과 사람 손이, 한 나무를 심었습니다.

{c55}

빛해파리가 그 위로 떠올라, 빛나는 포자를 흩뿌렸습니다. 이 세계의 방식으로 하는, 환영 인사였습니다.

{c56}

서하는 손목 장치를 풀어 돌기둥 위에 올려놓았습니다. 이제, 밖으로 보낼 신호는 필요 없었습니다.

{c57}

그날 밤, 서하는 새로운 이웃들과 언덕에 나란히 앉아, 하늘의 소용돌이를 바라보았습니다. 이제 그 빛이, 무섭지 않았습니다. 고르는 낮게 울리며 옛날이야기를 들려주었고, 리아는 서하의 어깨에 기대어 잠이 들었습니다.

{c58}

일그러진 은하들이 흐르는 하늘. 다시는 나갈 수 없는 하늘이었지만, 서하는 더 이상 출구를 찾지 않았습니다.

{c59}

빛조차 빠져나오지 못한다는 블랙홀. 그 안에서는 지금도, 떨어져 온 이들이 서로의 이웃이 되어 살고 있습니다. 새벽호의 마지막 대원, 서하처럼요.
"""


def main():
    cmd, folder = sys.argv[1], sys.argv[2]
    chars = {c["name"]: c for c in json.load(open(os.path.join(HERE, "등장인물.json"), encoding="utf-8"))["chars"]}
    if cmd == "job":
        items = []
        for cid, who, desc, _, place in CUTS:
            looks = "; ".join(f"character {k + 1} (exactly as in reference image {k + 1}): {chars[nm]['look']}, {chars[nm]['outfit']}"
                              for k, nm in enumerate(who))
            nonhuman = [nm for nm in who if nm in ("고르", "리아", "빛해파리")]
            items.append({"id": cid, "width": 1024, "height": 576, "seed": 300 + len(items),
                          "refs": [os.path.join(HERE, chars[nm]["face"]) for nm in who],
                          "prompt": f"{STYLE}. "
                                    + (f"Characters: {looks}. Each character appears only once. " if looks else "No characters, no people. ")
                                    + ("Humans have exactly two arms and two legs, head and face turned the same direction as the body. " if any(n in ("서하", "한도윤") for n in who) else "")
                                    + (f"The non-human creatures look exactly like their reference sheets, not human. " if nonhuman else "")
                                    + ("" if len(who) > 1 else "No other people or creatures in the scene. ")
                                    + f"Scene: {desc}. " + (place + ". " if place else "")
                                    + "Cinematic composition, full-bleed image, no border, no frame, no paper edges. No text, no letters, no labels."})
        os.makedirs(folder, exist_ok=True)
        json.dump({"items": items}, open(os.path.join(folder, "job.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(len(items), "cuts")
    elif cmd == "project":
        story = STORY
        for cid, _, _, cap, _ in CUTS:
            story = story.replace("{" + cid + "}", f"[사진: {os.path.join(folder, cid + '.png')} | {cap} | AI 생성 그림 (FLUX.2 klein) | ]")
        proj = {"ver": 7, "category": "장문", "genre": "[이야기] SF 판타지", "topic": TITLE, "title": TITLE,
                "story": story, "sources": [], "notes": "블랙홀 내부 세계 단편 (약 10분, 판타지 설정화풍)", "autophoto": False, "img_source": "그림: 애니 일러스트",
                "cast": [{"name": nm, "look": c["look"], "look_ko": c["look_ko"], "sheet": os.path.join(HERE, c["face"])} for nm, c in chars.items()],
                "settings": {"format": "롱폼 가로(1920×1080)", "narration": "on",
                             "layout": "자막형(큰 제목+사진+자막)", "img_fill": "전체 화면(글자가 사진 위에)",
                             "img_motion": "영상처럼(확대·이동·전환)", "fps": "24", "img_depth": "off",
                             "head_show": "안 보임(제목 카드만)", "head_pos": "숨김", "sub_split": "한 줄씩(문장·쉼표로 나눠 차례로)",
                             "img_label": "off", "sub_hide": "off", "bgm_mode": "자동생성", "bgm_style": "우주",
                             "narr_voice": "Supertonic M4 (남성, 무료 로컬) [supertonic:M4]", "narr_rate": "0", "narr_tone_m": -1.5}}
        out = os.path.join(HERE, "사건의지평선_단편.json")
        json.dump(proj, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(out, len(story), "chars")


if __name__ == "__main__":
    main()
