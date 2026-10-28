"""과학 다큐 '7만 년 전, 인류가 사라질 뻔한 날' (토바 화산) — 대본 + 컷별 그림 계획
python 다큐/토바_인류가사라질뻔한날.py job <저장폴더>   → 그림 주문서(klein_worker 용) job.json
python 다큐/토바_인류가사라질뻔한날.py project <그림폴더> → 프로젝트 파일(render_project 용) 다큐/토바_인류가사라질뻔한날.json
python 다큐/토바_인류가사라질뻔한날.py txt <파일>        → 사용자 확인용 대본(그림 자리는 [그림: 설명])
  영상은 render_project.py <프로젝트> --대본그대로
사실 근거(숫자는 모두 추정치로 말함): 폭발 약 7만 4천 년 전·화산폭발지수 8·분출량 약 2,800km³(암석 환산, 더 크게 보는 연구도 있음),
  세인트헬렌스 1980 약 1km³, 토바 호수 길이 약 100km, 화산 겨울 가설(램피노·셀프 1992, 앰브로즈 1998 병목),
  인도 줄라푸람(페트라글리아 연구팀 2007, Science), 말라위 호수 퇴적층(레인 연구팀 2013, PNAS),
  남아프리카 피너클 포인트(스미스 연구팀 2018, Nature), 에티오피아 신파-메테마 1(카펠먼 연구팀 2024, Nature),
  옐로스톤 마지막 거대 폭발 약 64만 년 전·미국 지질조사국 연간 확률 약 73만 분의 1"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TITLE = "7만 년 전, 인류가 사라질 뻔한 날"
GENRE = "고대 인류"
STYLE = ("scientific documentary illustration, detailed digital painting like a National Geographic or science magazine illustration, "
         "natural realistic colors, clear readable composition, soft cinematic lighting, high detail")
PEOPLE = ("Paleolithic modern humans with dark skin wearing simple animal-hide clothing, each person with exactly two arms and two legs, "
          "natural anatomy")   # 옛 사람이 나오는 컷에 붙임 (팔다리 수 규칙)
NOW = "modern-day people in contemporary clothing, each person with exactly two arms and two legs, natural anatomy"   # 오늘날 사람 컷 (과학자 등)

# (컷번호, 그림 설명(영어), 화면 설명(한국어), 사람이 나오는 컷인지: True=옛 사람, "now"=오늘날 사람)
CUTS = [
    ("c01", "a colossal volcanic eruption on a tropical island seen from far away, a gigantic ash column rising into the stratosphere and spreading into an umbrella cloud, lightning inside the ash, jungle in the foreground", "7만 4천 년 전 토바 화산", False),
    ("c02", "a small group of people standing on a hilltop at dusk looking at a dark sky full of falling gray ash, seen from behind", "하늘을 덮은 화산재", True),
    ("c03", "a vast gray landscape covered in thick volcanic ash, dead trees, a single small human footprint trail crossing it, dim sunlight through haze", "인류는 정말 사라질 뻔했을까", False),
    ("c04", "satellite view from orbit of a very long narrow green tropical island stretching diagonally across the frame from upper left to lower right, a volcanic mountain chain along its length, the Indian Ocean around it, scattered clouds, realistic Earth photography style", "인도네시아 수마트라섬", False),
    ("c05", "aerial view of a huge long caldera lake filling the frame, deep blue water surrounded by steep green mountain walls, a large green island in the middle of the lake, morning mist", "지금의 토바 호수", False),
    ("c06", "pyroclastic flows of glowing gray ash racing down mountain slopes and across a forested valley, enormous scale, dark sky", "산을 덮친 화산 쇄설류", False),
    ("c07", "a tiny volcano with a thin small ash plume in the foreground, completely dwarfed by a colossal wall of ash cloud behind it that fills the entire sky from horizon to top of frame, dramatic sense of scale", "세인트헬렌스와 비교한 크기", False),
    ("c08", "view from very high in the stratosphere: a vast brown-gray layer of volcanic ash cloud spreading flat over the ocean for thousands of kilometers, the curved horizon of the Earth, sunlight on the top of the ash layer", "바람을 타고 퍼진 화산재", False),
    ("c09", "an exposed riverbank cliff in India showing a thick flat pale gray-white layer of volcanic ash sandwiched between brown soil layers, one modern geologist in a field shirt and hat kneeling beside it with a small trowel for scale", "인도 땅속의 두꺼운 화산재층", "now"),
    ("c10", "a coastal village landscape in the early 1800s under a dim yellow hazy sky, ruined crops in cold fields, gloomy summer", "1816년, 여름이 없던 해", False),
    ("c11", "the upper atmosphere seen from high above the Earth, a thin hazy veil of sulfuric aerosol spread around the planet dimming the sunlight, cold blue tones", "햇빛을 가린 얇은 막", False),
    ("c12", "a tropical forest turned cold and gray, leafless trees dusted with ash, a weak pale sun behind thick haze, frost on the ground", "화산 겨울", False),
    ("c13", "close-up of two hands holding a small glass jar of gray volcanic ash above a wooden desk with open books and a few stone tools, a 1990s university office softly blurred behind, warm lamp light, no face visible", "1998년, 앰브로즈의 가설", "now"),
    ("c14", "a lonely small band of a few people walking across a cold bleak plain under a dark sky, carrying spears and bundles, wind blowing ash", "수천 명으로 줄었다는 인류", True),
    ("c15", "an hourglass shape made of glowing particles: many particles at the top, very few passing through the narrow middle, many again at the bottom, dark background, scientific concept art", "유전자 '병목'", False),
    ("c16", "a family group of chimpanzees in a lush African forest, sitting together on branches and the ground, realistic wildlife photography style", "숲 하나의 침팬지 무리", False),
    ("c17", "a crowd of diverse modern people from many ethnic backgrounds walking in a busy city square, seen from above, daylight", "생각보다 서로 닮은 인류", "now"),
    ("c18", "a dry rocky river valley in southern India under hot sunlight, low scrub, red earth, an archaeological excavation trench with string grid lines", "인도 줄라푸람 유적", False),
    ("c19", "modern archaeologists in sun hats and field clothes in a deep excavation trench carefully brushing soil next to a pale volcanic ash layer, layered soil walls, bright daylight", "화산재층을 파는 고고학자들", "now"),
    ("c20", "close-up of several Middle Paleolithic stone tools: sharp flint flakes and pointed Levallois points with clear chipped knapping scars and sharp edges, laid on a cloth in two rows, museum lighting", "재 아래와 위의 비슷한 석기", False),
    ("c21", "a small group of men and women sitting beside a river in a dry Indian landscape, knapping stone tools by striking a stone core with a round hand-held hammerstone, no handles, sun shining through light haze", "폭발 뒤에도 살았던 사람들", True),
    ("c22", "modern scientists on a small research boat on a vast calm African lake with mountains on the far shore, scientists lowering a long sediment core tube into the water, morning light", "말라위 호수의 퇴적층 조사", "now"),
    ("c23", "a long half-cylinder lake sediment core lying in a plastic tray on a laboratory table, showing many fine thin layers of brown, olive and gray mud, a microscope beside it, clean lab lighting", "호수 바닥 진흙 속 기록", False),
    ("c24", "microscope view of tiny sharp glassy volcanic ash shards, transparent and curved, on a dark background, scientific microscope image", "눈에 안 보이는 화산 유리 조각", False),
    ("c25", "a rugged rocky coastline in South Africa with sea caves in the cliffs, ocean waves crashing, golden afternoon light", "남아프리카 피너클 포인트", False),
    ("c26", "inside a sea cave rock shelter on the coast, a family group of men, women and children, everyone including the children dressed only in animal hides, sitting around a small fire, roasting mussels on hot stones at the edge of the fire, the ocean visible through the cave mouth", "바닷가 동굴에서 산 사람들", True),
    ("c27", "people gathering mussels and shellfish on rocky tidal pools at low tide, coastline, bright day", "바다가 준 먹을거리", True),
    ("c28", "a dry savanna landscape in northwestern Ethiopia with a seasonal river that has shrunk into a chain of small pools, acacia trees, hot dry season", "에티오피아 신파-메테마 유적", False),
    ("c29", "people catching fish by hand and with simple baskets in a shallow shrinking river pool during the dry season, savanna around them", "마른 계절, 웅덩이의 물고기", True),
    ("c30", "a small group of people walking along a riverbank in a line through a dry savanna, following the river, long shadows, evening", "강을 따라 옮겨 간 사람들", True),
    ("c31", "close-up of a few small triangular stone points on a dark cloth, tiny and finely made, museum lighting", "작은 돌 화살촉", False),
    ("c32", "a small band of men, women and children standing on a dry coastal hill at dawn, looking across a narrow blue sea strait toward a distant desert coastline, seen from behind", "아프리카를 떠난 작은 무리", True),
    ("c33", "a small group of men and women kneeling on a simple raft made of lashed logs, paddling across a narrow strait at dawn, a distant coastline ahead, calm sea", "작은 무리에서 퍼져 나간 인류", True),
    ("c34", "a softly glowing DNA double helix floating in darkness above an ancient human skull resting on sand, scientific concept art", "아직 끝나지 않은 논쟁", False),
    ("c35", "a band of men, women, children and elders, all dark-skinned and all wearing animal hides, sharing roasted meat by hand around a campfire at night under a starry sky, warm firelight", "서로 나눈 사람들", True),
    ("c36", "close view of two hands pressing a pointed antler tool against the edge of a gray flint stone blade to flake it, small stone chips falling, firelight", "도구를 만든 손", True),
    ("c37", "a long line of people migrating across a wide landscape at sunrise, carrying belongings, a river and distant hills ahead, hopeful", "옮겨 다니며 버틴 인류", True),
    ("c38", "aerial view of Yellowstone geothermal landscape: a colorful hot spring with orange and blue rings, steam rising, forest around", "옐로스톤의 지금", False),
    ("c39", "scientists in a modern volcano monitoring room seen from behind, monitors showing only simple wavy line graphs, through the window a calm quiet green forested volcano with no smoke under a clear blue sky", "화산을 지켜보는 과학자들", "now"),
    ("c40", "a calm sunrise over the huge caldera lake with green mountains around it, peaceful fishing boats on the water, warm golden light", "다시 평화로운 토바 호수", False),
]

# 누끼를 깊이(가까운 인물) 대신 정해 준 덩어리로: 화산 연기는 오려서 분화구(anchor)에서 부풀어 오르게 (사용자 결정)
# box = 오릴 곳 [왼, 위, 오른, 아래], anchor = 커지는 기준점, zoom = 장면 동안 커지는 정도 (그림 비율 0~1)
CUTOUT = {
    "c01": {"box": [0.07, 0.0, 0.93, 0.72], "anchor": [0.5, 0.68], "zoom": 0.08},
    "c06": {"box": [0.07, 0.0, 0.64, 0.72], "anchor": [0.4, 0.62], "zoom": 0.07},
    "c07": {"box": [0.33, 0.03, 0.8, 0.76], "anchor": [0.52, 0.75], "zoom": 0.08},
}

STORY = """{c01}

약 7만 4천 년 전, 지금의 인도네시아 수마트라섬에서 땅이 터져 나갔습니다. 최근 200만 년 사이, 지구에서 가장 큰 화산 폭발 가운데 하나였습니다.

{c02}

검은 재가 하늘을 덮고, 그 재는 바다 건너 수천 킬로미터 떨어진 인도까지 날아가 쌓였습니다. 그리고 오랫동안 이런 이야기가 전해졌습니다. 이 폭발 때문에 지구가 얼어붙었고, 인류가 겨우 수천 명만 남아 멸종 직전까지 갔다는 이야기입니다.

{c03}

정말 그랬을까요? 최근 20여 년 동안 땅속에서 나온 새로운 증거들은 전혀 다른 이야기를 들려주고 있습니다. 끝까지 보시면, 우리 조상이 그 재 속에서 어떻게 살아남았는지 알게 되실 겁니다.

## 1. 슈퍼 화산 토바

{c04}

이야기의 무대는 적도 바로 위, 수마트라섬 북쪽입니다. 이곳에는 토바라는 거대한 화산이 있었습니다. 인도네시아는 땅속의 판들이 서로 부딪치는 곳이어서, 지금도 백 개가 넘는 활화산이 줄지어 있는 화산의 나라입니다.

{c05}

지금 그 자리에 가 보면 산이 아니라 호수가 있습니다. 길이 약 100킬로미터, 세계에서 가장 큰 화산 호수인 토바 호수입니다. 호수 한가운데에는 서울보다 큰 섬이 떠 있습니다. 이 거대한 호수 자체가, 폭발로 땅속이 텅 비면서 무너져 내린 구덩이입니다.

{c06}

과학자들은 화산 폭발의 크기를 0부터 8까지 등급으로 나눕니다. 토바는 가장 높은 8등급, 이른바 슈퍼 화산 폭발이었습니다. 뜨거운 화산재와 가스가 산비탈을 따라 쏟아져 내려, 주변 수천 제곱킬로미터를 덮어 버렸습니다. 이 흐름이 식어 굳은 바위는 곳곳에서 수백 미터 두께로 남아 있습니다. 폭발은 길어야 몇 주 안에 끝났을 것으로 보지만, 그 짧은 시간에 땅의 모양이 완전히 바뀌었습니다.

{c07}

뿜어낸 양은 약 2,800세제곱킬로미터로 추정됩니다. 1980년 미국의 세인트헬렌스 화산 폭발과 비교하면 수천 배에 이르는 양입니다. 한반도 전체를 10미터 넘는 두께로 덮을 수 있는 양이지요.

{c08}

화산재는 바람을 타고 서쪽으로 날아가 인도양과 남아시아를 뒤덮었습니다. 멀리 아프리카의 호수 바닥에서도 토바에서 날아온 아주 작은 유리 조각이 발견됩니다.

{c09}

인도의 여러 곳에서는 지금도 땅을 파면, 그때 쌓인 하얀 화산재층이 나옵니다. 그런데 이렇게 큰 폭발은 하늘에도 무언가를 남깁니다. 바로 그것이 인류 멸종설의 시작이었습니다. 이 이야기는 다음 장에서 이어 가겠습니다.

## 2. 화산 겨울 가설

{c10}

큰 화산이 날씨를 바꾼 기록은 실제로 있습니다. 1815년 인도네시아의 탐보라 화산이 폭발한 다음 해, 유럽과 북아메리카에서는 여름에도 서리가 내렸습니다. 사람들은 그해를 여름이 없던 해라고 불렀습니다. 그런데 토바는 탐보라보다 열 배 넘게 큰 폭발이었습니다.

{c11}

화산은 재와 함께 엄청난 양의 황 가스를 뿜어냅니다. 이 가스는 하늘 높은 곳에서 아주 작은 물방울이 되어 지구를 얇은 막처럼 감쌉니다. 그러면 햇빛이 땅까지 닿지 못하고 되돌아갑니다.

{c12}

1990년대 초, 일부 과학자들은 토바 폭발 뒤 몇 년 동안 지구 기온이 크게 떨어졌을 것이라고 계산했습니다. 열대의 숲이 시들고, 먹을 것이 사라지는 화산 겨울이 찾아왔다는 것입니다.

{c13}

1998년, 미국의 인류학자 스탠리 앰브로즈는 여기서 한 걸음 더 나아갔습니다. 이 화산 겨울 때문에 당시 인류가 크게 줄어, 많아야 1만 명, 어쩌면 수천 명 정도만 살아남았을 수 있다는 가설을 내놓았습니다.

{c14}

지금 지구에는 80억 명이 살고 있습니다. 그런데 그 모두가 겨우 수천 명의 후손이라는 이야기입니다. 이 가설은 큰 관심을 받았고, 토바 재앙 이론이라는 이름으로 널리 퍼졌습니다. 교과서와 다큐멘터리에도 자주 소개되었지요. 다만 여기서 말하는 숫자는 모두 짐작으로 낸 값이라는 점을 기억해 두셔야 합니다.

{c15}

이 가설을 뒷받침한 근거는 바로 우리 몸속 유전자였습니다. 병의 좁은 목처럼, 무리의 숫자가 아주 적었던 시기를 지나면 유전자의 다양함도 함께 줄어듭니다. 과학자들은 이것을 병목 현상이라고 부릅니다.

{c16}

실제로 인류의 유전자는 놀랄 만큼 서로 비슷합니다. 아프리카 숲 한 곳에 사는 침팬지 무리가, 전 세계 80억 인류보다 유전자가 더 다양하다는 연구도 있습니다.

{c17}

겉모습은 이렇게 달라 보여도, 우리는 유전자로 보면 아주 가까운 한 가족입니다. 그렇다면 그 이유는 정말 토바였을까요? 이 질문에 답하기 위해, 과학자들은 직접 땅을 파기 시작했습니다.

## 3. 인도의 증거

{c18}

첫 번째 증거는 화산재가 가장 두껍게 쌓인 인도에서 나왔습니다. 인도 남부의 줄라푸람이라는 곳입니다.

{c19}

2007년, 마이클 페트라글리아가 이끄는 연구팀은 이곳에서 토바 화산재층을 사이에 두고 그 아래와 위를 차례로 파 내려갔습니다. 폭발 전과 폭발 뒤의 흔적을 직접 비교하려는 것이었습니다.

{c20}

결과는 놀라웠습니다. 화산재 아래에서도, 화산재 위에서도 거의 같은 방식으로 만든 돌 도구가 나왔습니다. 돌을 떼어 내는 순서와 모양, 크기까지 비슷했습니다. 만약 화산 겨울로 이 지역 사람들이 모두 사라졌다면, 재 위에서는 도구가 끊기거나 전혀 다른 도구가 나왔어야 합니다.

{c21}

이것은 폭발 뒤에도 비슷한 사람들이 그 땅에 계속 살았을 수 있다는 뜻입니다. 다만 그 도구를 만든 사람이 우리와 같은 현생 인류였는지는 아직 확실하지 않습니다. 사람의 뼈가 함께 나오지 않았기 때문입니다.

## 4. 아프리카의 증거

{c22}

그렇다면 인류의 고향, 아프리카는 어땠을까요? 2013년, 과학자들은 동아프리카 말라위 호수의 바닥에서 긴 진흙 기둥을 뽑아 올렸습니다.

{c23}

호수 바닥에는 해마다 진흙이 얇게 쌓입니다. 그 층 하나하나에는 당시의 날씨와 식물의 흔적이 기록되어 있습니다.

{c24}

연구팀은 그 진흙 속에서 눈에 보이지 않을 만큼 작은 토바의 화산 유리 조각을 찾아냈습니다. 그래서 폭발이 일어난 바로 그 시점을 정확히 짚을 수 있었습니다. 그런데 그 앞뒤의 층에서는, 몇 해 동안 숲이 망가질 만큼 큰 추위의 흔적이 뚜렷하게 보이지 않았습니다.

{c25}

2018년에는 남아프리카의 바닷가에서 더 놀라운 소식이 나왔습니다. 피너클 포인트라는 바닷가 절벽의 동굴 유적입니다.

{c26}

이곳 연구팀도 흙 속에서 토바의 작은 유리 조각을 찾아, 폭발 시점을 짚었습니다. 그리고 그 뒤의 층에서, 사람들이 오히려 더 많이 모여 살았던 흔적을 발견했습니다. 불을 피운 자리와 돌 도구가 더 늘어난 것입니다.

{c27}

바닷가의 조개와 물고기가 든든한 먹을거리가 되어 주었을 것으로 보입니다. 재앙이 왔다고 해서 모든 곳이 똑같이 무너진 것은 아니었습니다. 날씨가 나빠져도 바다는 쉽게 얼지 않고, 바닷가는 먹을 것이 꾸준히 나오는 피난처가 될 수 있었습니다.

{c28}

그리고 2024년, 에티오피아 북서쪽의 신파-메테마라는 유적에서 또 하나의 이야기가 나왔습니다. 이곳 역시 토바의 유리 조각으로 폭발 시점이 확인된 곳입니다.

{c29}

폭발 뒤 이곳은 비가 적은 마른 계절이 길어졌던 것으로 보입니다. 강물이 줄어 작은 웅덩이들만 남자, 사람들은 그 웅덩이에 갇힌 물고기를 잡아먹었습니다.

{c30}

그리고 물을 따라 움직였습니다. 연구팀은 사람들이 마른 시기에 강을 길 삼아 옮겨 다녔고, 이것이 인류가 아프리카 밖으로 퍼져 나가는 길이 되었을 수도 있다고 보았습니다.

{c31}

이 유적에서는 아주 작은 삼각형 돌촉도 나왔습니다. 연구팀은 이것이 활과 화살에 쓰였을 가능성이 있다고 보고 있습니다. 다만 이 해석은 아직 더 많은 확인이 필요합니다.

## 5. 그럼 유전자의 병목은?

{c32}

그렇다면 처음의 질문으로 다시 돌아가 보겠습니다. 인류의 유전자가 서로 비슷한 이유는 무엇일까요? 여기에는 학자들이 내놓은 다른 설명도 있습니다.

{c33}

아프리카 밖에 사는 사람들의 조상은, 약 5만에서 7만 년 전 무렵 아프리카를 떠난 비교적 작은 무리였던 것으로 보입니다. 작은 무리에서 수많은 후손이 퍼져 나가면, 그 무리가 가진 유전자만 이어지게 됩니다. 이것을 창시자 효과라고 부릅니다.

{c34}

다시 말해 유전자가 비슷한 이유가 꼭 화산 때문만은 아닐 수 있다는 것입니다. 인류가 언제, 얼마나 줄었는지에 대해서는 지금도 여러 연구가 서로 다른 답을 내놓고 있습니다. 이 문제는 아직 결론이 나지 않은 논쟁입니다.

## 6. 인류의 진짜 힘

{c35}

그래도 한 가지는 점점 분명해지고 있습니다. 토바 폭발은 분명 거대한 재앙이었지만, 인류는 그 재 속에서도 버텨 냈다는 사실입니다.

{c36}

비결은 강한 몸이 아니었습니다. 먹을 것을 나누고, 돌을 다듬어 새 도구를 만들고, 바다와 강에서 새로운 먹을거리를 찾아낸 능력이었습니다. 멀리 떨어진 무리끼리 소식을 나누고 서로 도울 수 있었다면, 한 곳이 어려워져도 다른 곳으로 피할 길이 열렸을 것입니다.

{c37}

살기 어려워지면 다른 곳으로 옮겨 갔습니다. 바닷가로, 강을 따라, 그리고 마침내 아프리카 밖 온 세상으로 말입니다. 어쩌면 인류는 사라질 뻔한 종이 아니라, 재앙 속에서 더 단단해진 종이었는지도 모릅니다.

## 마무리. 슈퍼 화산이 다시 깨어난다면

{c38}

그렇다면 지금 슈퍼 화산이 다시 폭발한다면 어떻게 될까요? 가장 자주 이름이 오르는 곳은 미국의 옐로스톤입니다. 옐로스톤의 마지막 거대 폭발은 약 64만 년 전이었습니다.

{c39}

미국 지질조사국은 옐로스톤에서 이런 거대 폭발이 일어날 가능성을 1년에 약 73만 분의 1 정도로 봅니다. 지금 당장 터질 징후도 없습니다. 과학자들은 전 세계의 큰 화산을 계측 장비로 날마다 지켜보고 있습니다.

{c40}

7만 4천 년 전, 하늘이 잿빛으로 덮였던 날에도 우리 조상은 살아남았습니다. 서로 나누고, 길을 찾고, 끝내 온 세상으로 걸어 나갔습니다. 여러분은 인류가 그 재앙을 이겨 낸 가장 큰 힘이 무엇이었다고 생각하시나요? 댓글로 여러분의 생각을 들려주세요. 우리 조상의 놀라운 이야기는 이 채널에서 계속 이어집니다."""


def main():
    cmd, folder = sys.argv[1], sys.argv[2]
    if cmd == "job":
        items = [{"id": cid, "width": 1024, "height": 576, "seed": 800 + int(cid[1:]),
                  "prompt": f"{STYLE}. Scene: {desc}." + (f" {NOW}." if people == "now" else f" {PEOPLE}." if people else "") +
                            " Cinematic composition, full-bleed image, no border, no frame, no paper edges. No text, no letters, no labels, no numbers."}
                 for cid, desc, _, people in CUTS]
        os.makedirs(folder, exist_ok=True)
        json.dump({"items": items}, open(os.path.join(folder, "job.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(len(items), "cuts")
    elif cmd == "txt":
        story = STORY
        for cid, _, cap, _ in CUTS:
            story = story.replace("{" + cid + "}", f"[그림 {cid[1:]}: {cap}]")
        open(folder, "w", encoding="utf-8").write(f"{TITLE}\n\n{story}\n")
        print(folder, len(STORY), "chars")
    elif cmd == "project":
        story = STORY
        for cid, _, cap, _ in CUTS:
            story = story.replace("{" + cid + "}", f"[사진: {os.path.join(folder, cid + '.png')} | {cap} | AI 생성 그림 (FLUX.2 klein) | ]")
        proj = {"ver": 7, "category": "장문", "genre": GENRE, "topic": "토바 화산과 인류", "title": TITLE,
                "story": story, "sources": [], "notes": "과학 다큐. 유적·유물은 실제 사진 대신 AI 그림", "autophoto": False, "img_source": "그림: 사실묘사",
                "settings": {"format": "롱폼 가로(1920×1080)", "narration": "on",
                             "narr_voice": "Supertonic M2 (남성, 무료 로컬) [supertonic:M2]",
                             "layout": "자막형(큰 제목+사진+자막)", "img_fill": "전체 화면(글자가 사진 위에)",
                             "img_motion": "영상처럼(확대·이동·전환)", "fps": "24", "reveal_hit": "off", "reveal_fx": "off",
                             "head_show": "안 보임(제목 카드만)", "sub_split": "한 줄씩(문장·쉼표로 나눠 차례로)", "img_label": "off",
                             "img_depth": "on", "img_depth_amt": "누끼(앞 인물 따로)"}}   # 그림 속 앞 인물을 오려 따로 움직임 (사용자 결정)
        for cid, spec in CUTOUT.items():           # 그림 옆에 누끼 설정 파일 (영상 프로그램이 읽음)
            json.dump(spec, open(os.path.join(folder, cid + ".png.누끼.json"), "w", encoding="utf-8"))
        out = os.path.join(HERE, "토바_인류가사라질뻔한날.json")
        json.dump(proj, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(out, len(story), "chars")


if __name__ == "__main__":
    main()
