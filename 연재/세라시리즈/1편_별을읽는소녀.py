"""세라 시리즈 1편 '별을 읽는 소녀' — 대본 + 컷별 그림 계획
python 연재/세라시리즈/1편_별을읽는소녀.py job <저장폴더>   → 그림 주문서(klein_worker 용) job.json (768×432 작게, A 화풍)
python 연재/세라시리즈/1편_별을읽는소녀.py project <그림폴더> → 프로젝트 파일(render_project 용) 연재/세라시리즈/1편_별을읽는소녀.json
python 연재/세라시리즈/1편_별을읽는소녀.py txt <파일>        → 사용자 확인용 대본(그림 자리는 [그림 NN: 설명])
대본의 {컷번호} 자리에 그 컷 그림이 들어감. who = 그 컷에 나오는 인물·종족·우주선(등장인물.json 의 시트를 기준 그림으로 넣음, 최대 3개)
세계관·결정은 기획.md"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TITLE = "세라 시리즈 1편 - 별을 읽는 소녀"
STYLE = ("nostalgic 1980s Japanese TV cartoon cel animation, bright saturated cheerful colors, clean bold outlines, flat vivid cel shading, "
         "attractive appealing character design, steampunk space adventure")

# 대사 → 말하는 인물 (기록용. 1편은 나레이션 1명이 대사까지 모두 읽음 — 사용자 결정)
DIALOGUE = [
    ("이루! 갑판 닦으랬지, 별 구경하랬냐!", "레오"),
    ("언젠가 내가 이 배로 별 끝까지 날아갈 거야!", "이루"),
    ("별 끝은 무슨, 엔진부터 고치자.", "미오"),
    ("견습생이 꿈도 크네. 먼저 하늘부터 날아 봐.", "카이"),
    ("누, 누구야!", "이루"),
    ("쉿! 제발 소리 내지 마세요.", "세라"),
    ("이걸 빼앗기면 안 돼요. 절대로요.", "세라"),
    ("나침반 목걸이를 한 소녀를 찾는다. 숨기는 자는 제국의 적이다.", "제논"),
    ("못 봤어요. 여긴 화물뿐이에요.", "이루"),
    ("다들 꽉 잡아! 출항한다!", "레오"),
    ("저게… 제국 기함이야?", "노아"),
    ("핍핍네 시장으로 간다. 거기라면 숨을 데가 있어.", "레오"),
    ("어서 옵쇼! 숨을 곳도, 비밀도, 뭐든 팝니다요!", "핍핍"),
    ("그 목걸이, 팔 생각 없수? 값은 두둑이 쳐 드립죠.", "핍핍"),
    ("레오 형!", "이루"),
    ("이루, 네가 몰아.", "레오"),
    ("내가요? 저 소행성 지대를요?", "이루"),
    ("제가 길을 읽을게요. 당신은 믿고 날기만 하면 돼요.", "세라"),
    ("왼쪽으로 크게! 이제 아래로!", "세라"),
    ("간다아!", "이루"),
    ("너, 진짜 별을 읽는구나.", "이루"),
    ("당신도 진짜 날 줄 아네요.", "세라"),
    ("이 지도는 제국이 다음에 그물을 칠 별을 알려 줘요. 그리고 다음은… 지구예요.", "세라"),
    ("달의 공주를 만나야 해요.", "세라"),
    ("좋아. 별 끝까지는 아니어도, 달까지는 데려다줄게.", "이루"),
    ("놓쳤다고 생각하겠지.", "제논"),
]

# (컷번호, 나오는 인물·종족·우주선, 그림 설명(영어), 화면 설명(한국어))
CUTS = [
    ("c01", [], "deep space with a bright warm yellow star shining among colorful nebulae, peaceful and beautiful", "우주 저편의 별"),
    ("c02", ["베스페라의 나방왕실선"], "a huge rainbow-colored glowing web of light spreading around the star like a net, a fleet of elegant moth-winged alien ships weaving it", "별을 감싸는 빛의 그물"),
    ("c03", [], "the star turning gray and dim inside the glowing web, its light being sucked away in streams toward the alien ships, eerie", "빛을 빼앗기는 별"),
    ("c04", ["루미나의 해파리함"], "several glowing pink jellyfish-shaped alien ships fleeing into dark space away from a dimmed gray star, sad mood", "달아나는 해파리족의 배들"),
    ("c05", ["베스페라"], "an elegant moth-winged alien noble with golden eyes standing on the bridge of a silver ship, watching the dead star with a calm smile", "베스페라 제국의 귀족"),
    ("c06", [], "the beautiful blue planet Earth seen from space, sunlight on its oceans, peaceful", "다음 별, 지구"),
    ("c07", [], "a lively steampunk sky harbor on Earth on a sunny morning, brass docks floating among clouds, many small steam airships and spaceships, colorful flags, steam and gears", "지구의 하늘 항구"),
    ("c08", ["황동고래호 주인공배"], "the chubby whale-shaped brass cargo spaceship docked at a sky harbor pier, steam rising, morning sunlight", "황동고래호"),
    ("c09", ["이루"], "the young man scrubbing the brass deck of a cargo ship with a mop and bucket, looking up at the sky dreamily, sunny", "갑판을 닦는 견습생 이루"),
    ("c10", ["레오", "이루"], "a big muscular engineer with a red bandana shouting with a laugh at the young man who is startled holding a mop, on a brass ship deck", "기관장 레오의 호통"),
    ("c11", ["이루"], "the young man standing on the ship railing with one fist raised to the sky, big confident grin, clouds and sun behind", "이루의 꿈"),
    ("c12", ["미오"], "a cheerful young woman mechanic with pink twin tails and orange overalls popping her head out of an open engine hatch with a wrench, oil on her cheek", "정비사 미오"),
    ("c13", ["노아"], "a young genius inventor with curly hair and round glasses tinkering at a cluttered workbench with a small brass robot owl on his shoulder", "발명가 노아와 로봇 부엉이"),
    ("c14", ["카이의 전투기"], "a sleek white and gold racing fighter spaceship zooming low over the sky harbor, leaving a trail, wind blowing flags", "머리 위를 스치는 전투기"),
    ("c15", ["카이"], "a handsome blond ace pilot in a white flight coat and red scarf leaning out of a fighter cockpit, smirking and waving two fingers", "라이벌 카이"),
    ("c16", ["이루"], "the young man shaking his fist at the sky in frustration, hair blown by the wind of a passing fighter, comic expression", "약 오른 이루"),
    ("c17", [], "inside a dim cargo hold of a brass spaceship, stacked wooden crates and barrels, a beam of light from a hatch, mysterious", "출항 직전의 화물칸"),
    ("c18", ["이루"], "the young man startled, stepping back, pointing a flashlight at a dark corner between crates", "누군가 숨어 있다"),
    ("c19", ["세라"], "a beautiful young woman with long silver-blue hair crouching between cargo crates, finger on her lips, frightened violet eyes, light from a flashlight on her", "숨어 있던 소녀 세라"),
    ("c20", ["세라"], "close-up of the young woman clutching a glowing brass compass pendant on her chest with both hands, determined eyes", "나침반 목걸이"),
    ("c21", ["제논", "스칼"], "a cold silver-haired imperial commander in a black uniform and cape marching onto the sky harbor pier, followed by a scarred green lizard bounty hunter with a steam blaster, soldiers behind", "부두에 나타난 제논과 스칼"),
    ("c22", ["제논"], "the cold silver-haired commander with red eyes holding up a glowing wanted poster image without text, speaking coldly, dock workers backing away", "제논의 경고"),
    ("c23", ["스칼"], "the lizard bounty hunter sniffing the air near the cargo ship with a sly grin, yellow slit eyes", "냄새를 맡는 스칼"),
    ("c24", ["이루"], "the young man standing at the cargo hatch with arms spread, nervously smiling, blocking the way, sweat on his face", "세라를 숨겨 준 이루"),
    ("c25", ["레오"], "the big engineer pulling a large brass lever in a steamy engine room, shouting, gauges spinning", "급히 출항하는 황동고래호"),
    ("c26", ["황동고래호 주인공배"], "the whale-shaped brass spaceship blasting off from the sky harbor with blue engine flames, steam clouds, dock workers looking up", "하늘 항구를 떠나다"),
    ("c27", ["제국 소형전투기"], "a squadron of small black imperial fighters with red round cockpits chasing through the clouds", "뒤쫓는 제국 전투기들"),
    ("c28", ["황동고래호 주인공배", "제국 소형전투기"], "the whale-shaped brass spaceship climbing through the upper sky into space with small black fighters shooting red bolts behind it", "하늘을 벗어나는 추격전"),
    ("c29", ["제논의 제국기함"], "a gigantic black angular imperial flagship floating above the blue Earth, red lights, menacing, a small whale-shaped brass ship in front for scale", "지구 위의 제국 기함"),
    ("c30", ["노아"], "the young inventor with round glasses pressing his face against a porthole, mouth open in shock, robot owl hiding behind his head", "놀란 노아"),
    ("c31", ["레오"], "the big engineer at the ship's wheel turning hard, determined grin, sparks from the console", "핍핍의 시장으로"),
    ("c32", ["핍핍의 잡화상선"], "a floating space bazaar made of many patchwork trader ships tied together with ropes and lanterns, colorful umbrellas, crowded and cheerful, in space", "떠다니는 우주 시장"),
    ("c33", ["핍핍"], "a tiny round fluffy teal alien trader with huge ears and goggles standing on a pile of crates, arms wide open in welcome, big grin", "상인족 핍핍"),
    ("c34", ["핍핍", "세라"], "the tiny fluffy alien trader pointing slyly at the young woman's glowing compass pendant, she pulls it away with a wary look", "목걸이를 노리는 핍핍"),
    ("c35", ["스칼의 현상금사냥선"], "a sleek green lizard-skull-shaped bounty hunter ship with glowing yellow windows emerging behind the space bazaar", "따라온 현상금 사냥선"),
    ("c36", ["레오"], "inside the ship, the big engineer holding his injured arm after an explosion, sparks and smoke around him", "다친 레오"),
    ("c37", ["이루", "레오"], "the big injured engineer handing his brass pilot goggles to the young man, serious faces, smoke in the cockpit", "조종간을 넘기다"),
    ("c38", ["이루"], "the young man in the pilot seat gripping the controls with both hands, sweating, a huge asteroid field visible through the cockpit window", "처음 잡은 조종간"),
    ("c39", [], "a dangerous asteroid field in space with tumbling rocks of all sizes, glowing dust, a narrow path between them", "소행성 지대"),
    ("c40", ["세라"], "the young woman opening her brass compass pendant, a beautiful glowing hologram star map with golden lines unfolding in the air around her", "떠오르는 별 지도"),
    ("c41", ["세라", "이루"], "the young woman standing behind the pilot seat pointing at the glowing star map lines, the young man at the controls, both focused", "별을 읽는 세라"),
    ("c42", ["황동고래호 주인공배"], "the whale-shaped brass spaceship banking sharply between two huge asteroids, sparks, dynamic angle", "소행성 사이로"),
    ("c43", ["스칼의 현상금사냥선"], "the lizard-skull bounty hunter ship crashing into an asteroid and getting stuck in the rocks, smoke", "바위에 걸린 사냥선"),
    ("c44", ["스칼"], "the lizard bounty hunter inside his cockpit shaking his fist angrily, alarms flashing red", "분한 스칼"),
    ("c45", ["이루"], "the young man shouting with excitement at the controls, hair flying, flying out of the asteroid field into open stars", "탈출 성공"),
    ("c46", ["이루", "세라"], "the young man and the young woman laughing together in the cockpit for the first time, warm light, relieved faces", "처음 함께 웃다"),
    ("c47", ["미오", "노아"], "the pink-haired mechanic and the young inventor cheering and hugging in the engine room, robot owl flapping", "환호하는 동료들"),
    ("c48", [], "quiet calm space with the blue Earth glowing far away through a large round observation window, stars", "고요해진 우주"),
    ("c49", ["세라"], "the young woman looking down at the open compass pendant in her hands, serious and sad expression, soft blue light", "세라의 고백"),
    ("c50", [], "a glowing hologram star map showing a rainbow web of light slowly closing around a small blue planet, ominous", "다음 그물의 자리, 지구"),
    ("c51", ["이루"], "the young man with a shocked face, eyes wide, in the ship's observation room", "놀란 이루"),
    ("c52", [], "the glowing star map pointing to the bright Moon with a golden line, the Moon shining beautifully", "달을 가리키는 지도"),
    ("c53", ["루나"], "a silhouette of an elegant princess with long black hair and a crescent tiara standing in a palace window on the Moon, seen from far away, mysterious", "달의 공주"),
    ("c54", ["이루", "세라"], "the young man giving a thumbs up and a confident grin to the young woman who smiles back, in front of the observation window", "이루의 약속"),
    ("c55", ["제논"], "the silver-haired commander standing in a dark flagship bridge, smiling coldly at a screen showing a small whale-shaped ship heading to the Moon", "제논의 미소"),
    ("c56", ["황동고래호 주인공배"], "the whale-shaped brass spaceship flying toward the big bright Moon among stars, hopeful, warm light", "달을 향해"),
]

STORY = """{c01}

우주 저편, 한 별이 따뜻하게 빛나고 있었습니다.

{c02}

그런데 그날, 별 둘레로 무지갯빛 그물이 펼쳐졌습니다. 나방 날개 돛을 단 배들이 별을 천천히 감싸 갔습니다.

{c03}

그물이 조여들자 별빛이 실처럼 빨려 나갔습니다. 따뜻하던 별은 잿빛으로 식어 갔습니다.

{c04}

그 별의 빛 아래 살던 해파리족의 배들이, 어둠 속으로 뿔뿔이 흩어졌습니다. 돌아갈 고향은 이제 없었습니다.

{c05}

빛을 먹고 사는 종족, 베스페라 제국. 그들은 우아한 나방 날개와 부드러운 목소리로 다가와, 이렇게 별을 하나씩 삼키며 세력을 넓혀 왔습니다. 그물이 지나간 자리에는 빛도, 노래도, 아무것도 남지 않았습니다.

{c06}

그리고 그들이 다음으로 고른 별은, 바로 우리의 지구였습니다.

## 1. 황동고래호의 견습생

{c07}

증기와 황동의 시대. 지구의 하늘 항구는 오늘도 시끌벅적했습니다. 구름 사이 부두마다 증기 우주선들이 오르내렸습니다.

{c08}

그 부두 끝에, 고래를 닮은 둥근 화물선 한 척이 서 있었습니다. 이름은 황동고래호. 여기저기 덧댄 철판에 둥근 창이 반짝이는, 낡았지만 튼튼한 배였습니다. 이 배는 지구와 달 사이를 오가며 짐을 나르는 작은 화물선이었습니다.

{c09}

스무 살 이루는 이 배의 견습 조종사입니다. 말이 조종사지, 하는 일은 갑판 닦기가 전부였습니다. 조종간을 잡아 본 적은 아직 한 번도 없었습니다. 그래도 이루의 눈은 언제나 걸레가 아니라 하늘을 보고 있었습니다. 저 하늘 너머, 아무도 가 보지 못한 별 끝을요.

{c10}

"이루! 갑판 닦으랬지, 별 구경하랬냐!"

기관장 레오의 목소리가 부두에 쩌렁쩌렁 울렸습니다.

{c11}

"언젠가 내가 이 배로 별 끝까지 날아갈 거야!"

{c12}

"별 끝은 무슨, 엔진부터 고치자."

엔진 구멍에서 정비사 미오가 기름 묻은 얼굴을 내밀었습니다.

{c13}

배 한쪽에서는 열여덟 살 발명가 노아가 작은 로봇 부엉이와 함께 알 수 없는 기계를 만지고 있었습니다. 노아가 만든 물건은 절반은 터지고, 절반은 놀라운 일을 해냈습니다. 황동고래호는 늘 이렇게 시끄럽고, 따뜻한 배였습니다. 가족이 없는 이루에게는, 이 배가 곧 집이었습니다.

{c14}

그때 하얀 전투기 한 대가 항구 위를 낮게 스쳐 지나갔습니다. 깃발들이 한꺼번에 펄럭였습니다.

{c15}

"견습생이 꿈도 크네. 먼저 하늘부터 날아 봐."

항구 최고의 조종사, 카이였습니다.

{c16}

이루는 사라지는 전투기를 향해 주먹을 흔들었습니다. 하지만 그날, 이루는 진짜로 하늘을 날게 됩니다. 생각보다 훨씬 빨리요.

## 2. 숨어든 소녀

{c17}

출항을 앞둔 저녁, 이루는 화물칸을 살피러 내려갔습니다. 그런데 상자들 사이에서 무언가 움직였습니다.

{c18}

"누, 누구야!"

{c19}

손전등 불빛 속에, 은빛 머리카락의 소녀가 웅크리고 있었습니다.

"쉿! 제발 소리 내지 마세요."

{c20}

소녀의 이름은 세라였습니다. 세라는 목에 건 황동 나침반을 두 손으로 꼭 쥐고 있었습니다.

"이걸 빼앗기면 안 돼요. 절대로요."

{c21}

바로 그때, 부두가 술렁였습니다. 검은 망토를 두른 제국의 사령관 제논이 병사들을 이끌고 나타난 것입니다. 그 곁에는 도마뱀 얼굴의 현상금 사냥꾼, 스칼이 따르고 있었습니다.

{c22}

"나침반 목걸이를 한 소녀를 찾는다. 숨기는 자는 제국의 적이다."

제논은 인간이었지만, 베스페라 제국의 편에 선 사람이었습니다. 제국에 지구의 문을 열어 주는 대가로, 지구를 다스릴 자리를 약속받았다는 소문이 돌았습니다. 부두의 사람들은 하나둘 고개를 숙이고 물러났습니다.

{c23}

스칼이 코를 킁킁거리며 황동고래호 쪽으로 다가왔습니다.

{c24}

이루는 잠깐 망설였습니다. 제국에 맞서면 배도, 동료들도 위험해질 수 있었습니다. 하지만 상자 사이에서 떨고 있던 세라의 눈이 자꾸만 떠올랐습니다. 이루는 화물칸 문 앞을 가로막고 섰습니다.

"못 봤어요. 여긴 화물뿐이에요."

## 3. 제국의 추격

{c25}

"다들 꽉 잡아! 출항한다!"

레오가 커다란 손잡이를 힘껏 당겼습니다.

{c26}

황동고래호가 파란 불꽃을 뿜으며 하늘 항구를 박차고 올랐습니다.

{c27}

곧바로 제국의 검은 전투기들이 구름을 가르며 뒤쫓아 왔습니다.

{c28}

붉은 빛줄기가 배 옆을 스쳤습니다. 황동고래호는 덜컹거리며 하늘을 벗어나, 우주로 날아올랐습니다.

{c29}

그리고 우주로 나온 순간, 모두 숨을 멈췄습니다. 지구 하늘 위에, 칼날처럼 생긴 거대한 검은 배가 떠 있었습니다.

{c30}

"저게… 제국 기함이야?"

노아의 목소리가 떨렸습니다. 제국은 이미, 지구 바로 위까지 와 있었던 것입니다.

{c31}

"핍핍네 시장으로 간다. 거기라면 숨을 데가 있어."

## 4. 떠다니는 시장

{c32}

우주 한가운데, 수많은 배를 밧줄로 엮어 만든 시장이 떠 있었습니다. 등불과 파라솔이 반짝이는 이곳은, 온갖 종족이 모여드는 장터였습니다. 바위 등껍질의 거인들, 빛나는 해파리족, 그리고 고향을 잃고 떠도는 이들까지. 제국의 그물을 피해 온 사람들이 여기서 하루하루를 버티고 있었습니다.

{c33}

"어서 옵쇼! 숨을 곳도, 비밀도, 뭐든 팝니다요!"

털복숭이 상인족 핍핍이 두 팔을 벌려 일행을 맞았습니다.

{c34}

그런데 핍핍의 커다란 눈이 세라의 목걸이에 멈췄습니다.

"그 목걸이, 팔 생각 없수? 값은 두둑이 쳐 드립죠."

세라는 목걸이를 꼭 감추었습니다. 핍핍은 제국과도, 해적과도 거래하는 상인이었습니다. 누구의 편인지는 아무도 몰랐습니다. 그리고 그 사이, 누군가 이미 일행의 위치를 알리고 있었습니다.

{c35}

그때, 시장 뒤편으로 도마뱀 해골을 닮은 배가 미끄러지듯 다가왔습니다. 스칼이었습니다.

{c36}

쾅. 황동고래호가 크게 흔들렸습니다. 불꽃이 튀고, 레오가 팔을 붙잡고 쓰러졌습니다.

"레오 형!"

## 5. 첫 비행

{c37}

레오는 이마의 고글을 벗어 이루에게 내밀었습니다.

"이루, 네가 몰아."

{c38}

"내가요? 저 소행성 지대를요?"

창밖에는 거대한 바위들이 끝도 없이 떠다니고 있었습니다.

{c39}

한 번 부딪히면 끝인 곳. 노련한 조종사들도 피해 가는 길이었습니다. 이루의 손이 떨렸습니다. 꿈에서는 수백 번 날아 본 하늘이었지만, 진짜는 처음이었습니다.

{c40}

그때 세라가 나침반 목걸이를 열었습니다. 황금빛 별 지도가 배 안 가득 펼쳐졌습니다.

"제가 길을 읽을게요. 당신은 믿고 날기만 하면 돼요."

{c41}

세라는 별 지도의 빛줄기를 따라 손가락으로 길을 가리켰습니다.

"왼쪽으로 크게! 이제 아래로!"

{c42}

"간다아!"

이루는 눈을 질끈 감았다 뜨고, 조종간을 힘껏 꺾었습니다. 황동고래호가 두 바위 사이를 아슬아슬하게 빠져나갔습니다.

{c43}

뒤따라오던 스칼의 배는 바위에 부딪혀 그대로 끼어 버렸습니다.

{c44}

스칼은 조종석에서 분한 듯 주먹을 휘둘렀습니다.

{c45}

마지막 바위를 지나자, 눈앞에 탁 트인 별바다가 펼쳐졌습니다.

{c46}

"너, 진짜 별을 읽는구나."

"당신도 진짜 날 줄 아네요."

두 사람은 처음으로 마주 보고 웃었습니다.

{c47}

기관실에서는 미오와 노아가 서로 끌어안고 환호했습니다.

## 6. 별 지도의 비밀

{c48}

우주는 다시 고요해졌습니다. 둥근 창 너머로, 멀리 푸른 지구가 빛나고 있었습니다.

{c49}

세라는 한참 말없이 목걸이를 바라보다가, 조용히 입을 열었습니다.

{c50}

"이 지도는 제국이 다음에 그물을 칠 별을 알려 줘요. 그리고 다음은… 지구예요."

{c51}

이루는 아무 말도 하지 못했습니다. 방금 떠나온 그 푸른 별이, 잿빛으로 식어 가는 모습이 떠올랐습니다.

{c52}

별 지도의 빛줄기 하나가 달을 가리키고 있었습니다.

"달의 공주를 만나야 해요."

{c53}

달에는 오래전부터 별빛을 지켜 온 왕국이 있다고 했습니다. 세라의 목걸이도 원래 그 왕국에서 만들어진 것이었습니다. 그리고 그 왕국의 공주라면, 그물을 막을 방법을 알지도 몰랐습니다.

{c54}

이루가 엄지를 치켜세웠습니다.

"좋아. 별 끝까지는 아니어도, 달까지는 데려다줄게."

{c55}

같은 시각, 제국 기함의 어두운 함교. 제논은 화면 속 작은 고래 배를 바라보며 웃었습니다.

"놓쳤다고 생각하겠지."

{c56}

황동고래호는 달을 향해 날아갔습니다. 별을 읽는 소녀와, 하늘을 꿈꾸던 견습 조종사의 모험은 이제 막 시작되었습니다. 세라 시리즈 2편에서, 달의 왕국 이야기가 이어집니다."""


def cast():
    return {c["name"]: c for c in json.load(open(os.path.join(HERE, "등장인물.json"), encoding="utf-8"))["chars"]}


def main():
    cmd, folder = sys.argv[1], sys.argv[2]
    chars = cast()
    if cmd == "job":
        items = []
        for cid, who, desc, _ in CUTS:
            looks = "; ".join(f"{nm} (from reference image {k + 1}): {chars[nm]['look']}" for k, nm in enumerate(who))
            people = any(chars[nm]["kind"] in ("인물", "외계 종족") for nm in who)
            items.append({"id": cid, "width": 768, "height": 432, "seed": 1000 + int(cid[1:]),
                          "refs": [os.path.join(HERE, chars[nm]["face"]) for nm in who],
                          "prompt": f"{STYLE}. " + (f"{looks}. " if looks else "") + f"Scene: {desc}."
                                    + (" Each person has exactly two arms and two legs." if people else "")
                                    + " Cinematic composition, full-bleed image, no border, no frame. No speech bubbles, no text, no letters."})
        os.makedirs(folder, exist_ok=True)
        json.dump({"items": items}, open(os.path.join(folder, "job.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(len(items), "cuts")
    elif cmd == "txt":
        story = STORY
        for cid, _, _, cap in CUTS:
            story = story.replace("{" + cid + "}", f"[그림 {cid[1:]}: {cap}]")
        open(folder, "w", encoding="utf-8").write(f"{TITLE}\n\n{story}\n")
        print(folder, len(STORY), "chars")
    elif cmd == "project":
        story = STORY
        for cid, _, _, cap in CUTS:
            story = story.replace("{" + cid + "}", f"[사진: {os.path.join(folder, cid + '.png')} | {cap} | AI 생성 그림 (FLUX.2 klein) | ]")
        proj = {"ver": 7, "category": "장문", "genre": "[이야기] SF·디스토피아", "topic": "세라 시리즈", "title": TITLE,
                "story": story, "sources": [], "notes": "창작 애니 단편 세라 시리즈 1편", "autophoto": False, "img_source": "그림: 애니",
                "cast": [{"name": nm, "look": c["look"], "voice": c.get("voice"), "sheet": os.path.join(HERE, c["face"])}
                         for nm, c in chars.items() if c["kind"] in ("인물", "외계 종족")],
                "dialogue": [],   # 나레이션 1명(남자 성우 2)이 대사까지 모두 읽음 (사용자 결정, 2026-10-28). DIALOGUE 는 누가 한 말인지 기록용
                "settings": {"format": "롱폼 가로(1920×1080)", "narration": "on",
                             "narr_voice": "Supertonic M2 (남성, 무료 로컬) [supertonic:M2]",
                             "layout": "자막형(큰 제목+사진+자막)", "img_fill": "전체 화면(글자가 사진 위에)",
                             "img_motion": "없음", "img_depth": "off", "fps": "24", "reveal_hit": "off", "reveal_fx": "off",   # 움직임 없음 = 빠르게 (사용자 결정)
                             "head_show": "안 보임(제목 카드만)", "sub_split": "한 줄씩(문장·쉼표로 나눠 차례로)", "img_label": "on"}}
        out = os.path.join(HERE, "1편_별을읽는소녀.json")
        json.dump(proj, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(out, len(story), "chars")


if __name__ == "__main__":
    main()
