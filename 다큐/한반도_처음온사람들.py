"""과학 다큐 '한반도에 처음 온 사람들은 누구였을까' — 대본 + 컷별 그림 계획
python 다큐/한반도_처음온사람들.py job <저장폴더>   → 그림 주문서(klein_worker 용) job.json
python 다큐/한반도_처음온사람들.py project <그림폴더> → 프로젝트 파일(render_project 용) 다큐/한반도_처음온사람들.json
python 다큐/한반도_처음온사람들.py txt <파일>        → 사용자 확인용 대본(그림 자리는 [그림: 설명])
  영상은 render_project.py <프로젝트> --대본그대로
사실 근거(연대는 모두 추정·논쟁으로 말함): 1978 한탄강(연천 전곡리) 미 공군 그렉 보웬의 주먹도끼 발견, 모비우스 라인(할람 모비우스 1940년대),
  중국 바이써 분지 주먹도끼(2000, Science, 약 80만 년 전), 공주 석장리(1964 손보기 교수 연구팀, 남한 첫 구석기 발굴. 북한 웅기 굴포리는 1963),
  마지막 빙하기 해수면 약 120m 낮음(약 2만 년 전 무렵), 함북 화대 장덕리 털코끼리(매머드) 화석,
  청주 두루봉 흥수굴 흥수아이(1982 김흥수 씨가 찾음, 1983 충북대 이융조 교수 연구팀 발굴, 꽃가루·연대 해석 논쟁),
  단양 수양개(1983년부터 발굴, 슴베찌르개·좀돌날), 신석기 사람 뼈 고대 DNA(가덕도 장항·남해 섬 유적 연구: 동북아시아 북쪽 뿌리 + 일부 조몬 계통)"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TITLE = "한반도에 처음 온 사람들은 누구였을까"
GENRE = "고대 인류"
STYLE = ("scientific documentary illustration, detailed digital painting like a National Geographic or science magazine illustration, "
         "natural realistic colors, clear readable composition, soft cinematic lighting, high detail")
PEOPLE = ("Paleolithic East Asian hunter-gatherers, a mixed group of men and women with black hair, wearing fur and animal-hide clothing, "
          "each person with exactly two arms and two legs, natural anatomy")   # 옛 사람이 나오는 컷에 붙임 (팔다리 수 규칙)
NOW = "modern-day people in contemporary clothing, each person with exactly two arms and two legs, natural anatomy"   # 오늘날 사람 컷 (발굴단 등)

# (컷번호, 그림 설명(영어), 화면 설명(한국어), 사람이 나오는 컷인지: True=옛 사람, "now"=오늘날 사람)
CUTS = [
    ("c01", "a winter riverside in Korea in the late 1970s: a wide shallow river with smooth pebbles, low brown hills and leafless trees, a young American airman in a 1970s military field jacket seen from behind crouching at the water's edge picking up a stone, cold morning light", "1978년 한탄강 강가", "now"),
    ("c02", "close-up of a large teardrop-shaped Acheulean hand axe made of pale quartzite resting in two open hands, clear flaked scars on both faces, river pebbles behind, soft daylight", "손에 들린 주먹도끼", "now"),
    ("c03", "a small band of Paleolithic people walking along a wide river valley in Korea with forested granite mountains, early morning mist", "한반도에 처음 온 사람들", True),
    ("c04", "an old 1940s archaeology study room: a large old paper map of Asia pinned on a wall, stone tools on a wooden table, a desk lamp, books, no people", "1940년대의 생각", False),
    ("c05", "two rows of stone tools on a museum cloth: on the left large teardrop-shaped hand axes, on the right rough simple chopping tools made from river cobbles, museum lighting", "주먹도끼와 찍개", False),
    ("c06", "a vast misty East Asian landscape of forested hills and rivers seen from a high viewpoint at dawn, no people", "주먹도끼가 없다고 여겨진 동아시아", False),
    ("c07", "a modern Korean archaeological excavation on a grassy riverside terrace: many neat square pits with string grids, white tents, red soil walls, modern archaeologists in sun hats kneeling and digging", "전곡리 발굴 현장", "now"),
    ("c08", "a modern archaeologist's gloved hands lifting a pale quartzite hand axe out of red-brown soil in a square excavation pit, trowel and brush beside it", "땅속에서 나온 주먹도끼", "now"),
    ("c09", "a tall vertical cross-section wall of a red-brown soil deposit with many thin layers and cracks, a measuring stick standing against it, a small trowel in the soil, daylight", "연대를 알려 주는 흙의 층", False),
    ("c10", "a wide red soil basin in southern China with low green hills, an excavation trench in the foreground, bright tropical light", "중국 남쪽의 주먹도끼", False),
    ("c11", "a riverside hill along a broad river in Gongju, Korea, in the 1960s: a small excavation with simple wooden stakes and string, a few 1960s scholars in white shirts and hats digging, summer", "1964년 공주 석장리", "now"),
    ("c12", "a row of Paleolithic stone tools from Korea laid on a museum cloth: hand axes, choppers, scrapers and sharp flakes made of quartzite and stone, museum lighting", "석장리에서 나온 석기들", False),
    ("c13", "a map-like painted aerial view of the Korean peninsula during the last ice age with the Yellow Sea completely dried into a wide green grassy plain with rivers, connecting Korea and China, cold hazy light", "빙하기, 땅이 된 서해", False),
    ("c14", "a cold ice age steppe landscape with a herd of woolly mammoths walking through tall dry grass, snowy mountains in the distance, overcast sky", "털매머드가 살던 땅", False),
    ("c15", "a frozen ice age river valley at dusk with tall pine trees, a herd of deer and a woolly rhinoceros in the distance, cold blue light", "추운 빙하기의 숲", False),
    ("c16", "a group of Paleolithic people dressed in thick fur clothing sitting around a campfire at the mouth of a limestone cave in winter, snow outside, warm firelight", "동굴 앞의 겨울나기", True),
    ("c17", "the dark entrance of a limestone cave in a forested Korean hillside, partly cut by a quarry, morning light", "청주 두루봉 동굴", False),
    ("c18", "modern archaeologists in a limestone cave carefully uncovering a small human skeleton of a young child lying on a flat stone slab, soft lamp light, respectful mood", "흥수아이를 발굴하는 모습", "now"),
    ("c19", "microscope view of round spiky yellow pollen grains of chrysanthemum flowers floating on a dark background, scientific microscope image", "뼈 둘레에서 나온 꽃가루", False),
    ("c20", "a gentle painted scene inside a cave: Paleolithic people kneeling beside a small child laid on a flat stone slab, scattering small yellow wild chrysanthemum flowers, warm firelight, tender mood", "꽃을 뿌린 장례였을까", True),
    ("c21", "an empty quiet cave floor with a flat stone slab and a few scattered yellow petals, soft beam of light, mysterious atmosphere", "아직 풀리지 않은 질문", False),
    ("c22", "the wide South Han River in Danyang, Korea, flowing between steep green mountains and white limestone cliffs, a riverside flat terrace, summer haze", "단양 수양개", False),
    ("c23", "close-up of several Paleolithic tanged stone points: long narrow pointed stone blades with a short narrow stem at the base for hafting, laid on a dark cloth, museum lighting", "슴베찌르개", False),
    ("c24", "a Paleolithic hunter's hands binding a long narrow stone point with a short stem onto a wooden spear shaft with sinew, firelight", "창끝에 묶은 슴베찌르개", True),
    ("c25", "a small group of Paleolithic people with spears stalking a deer at the edge of a pine forest in a Korean mountain valley, autumn", "사냥하는 사람들", True),
    ("c26", "close-up of a conical stone microblade core with many thin parallel blade scars and a row of tiny sharp thin stone microblades beside it on a dark cloth, museum lighting", "좀돌날몸돌과 좀돌날", False),
    ("c27", "a Paleolithic person sitting on a riverside rock pressing a small pointed antler tool against a small stone core to detach thin tiny blades, river and mountains behind", "작은 날을 떼어 내는 기술", True),
    ("c28", "a painted view of northeast Asia from high above: Siberia, Mongolia, northern China, the Korean peninsula and the Japanese islands under soft clouds, realistic earth colors", "동북아시아로 이어진 길", False),
    ("c29", "a small band of Paleolithic people crossing a snowy mountain pass in a long line, carrying belongings, a vast valley ahead, sunrise", "먼 길을 걸어온 사람들", True),
    ("c30", "a sunny warm landscape after the ice age: green forests and a rising sea flooding a coastal plain, new islands forming, aerial view", "다시 바다가 된 서해", False),
    ("c31", "a Neolithic village by the sea in Korea about 7000 years ago: round pit houses with thatched roofs, people making comb-pattern pottery, fishing boats on the beach", "신석기 바닷가 마을", True),
    ("c32", "close-up of a large Neolithic Korean comb-pattern pottery vessel with a pointed bottom and fine incised diagonal line patterns, museum lighting", "빗살무늬토기", False),
    ("c33", "a modern ancient DNA laboratory: a scientist in a full white clean suit, mask and gloves drilling a tiny sample from an ancient tooth inside a clean hood, blue-white light", "고대 DNA 연구실", "now"),
    ("c34", "a softly glowing DNA double helix floating above a calm coastline with an ancient shell midden, dusk, scientific concept art", "뼈에 남은 기록", False),
    ("c35", "a painted map-like view of northeast Asia with the Amur River region, the Korean peninsula and the Japanese islands, two soft glowing streams of light meeting over the southern Korean coast, artistic, no text", "두 갈래의 뿌리", False),
    ("c36", "a calm sea strait between the southern tip of Korea and the Japanese islands seen from a coastal hill at dawn, small islands, no people", "바다 건너 이어진 사람들", False),
    ("c37", "a long line of people of many eras walking along a Korean mountain ridge from left to right: Paleolithic hunters in fur at the front, then Neolithic villagers, then later farmers, sunset, symbolic", "이어지고 섞여 온 사람들", True),
    ("c38", "the riverside terrace of Jeongok-ri in Korea today: a quiet green park on a basalt cliff above the Hantan river, autumn colors, peaceful", "오늘의 전곡리", False),
    ("c39", "close-up of a pale quartzite hand axe standing in a museum glass case with soft spot lighting, dark background", "박물관의 주먹도끼", False),
    ("c40", "a wide sunrise over Korean mountains and rivers with mist in the valleys, warm golden light, peaceful", "한반도의 새벽", False),
]

# 누끼를 깊이 대신 정해 준 덩어리로 할 컷 (연기·구름 등). 이 편은 없음
CUTOUT = {}

STORY = """{c01}

1978년 겨울, 경기도 연천의 한탄강 강가. 한 미군 병사가 강가에서 이상하게 생긴 돌 하나를 주웠습니다. 그의 이름은 그렉 보웬, 대학에서 고고학을 공부했던 사람이었습니다.

{c02}

그 돌은 한쪽 끝이 뾰족하고, 양쪽 면을 고르게 떼어 내 다듬은 돌 도구였습니다. 바로 주먹도끼였습니다. 보웬은 이 돌을 서울대학교 김원용 교수에게 알렸고, 곧 학자들이 한탄강으로 모여들었습니다. 이 작은 돌 하나가, 세계 고고학의 오래된 생각을 흔들어 놓게 됩니다.

{c03}

그렇다면 이 땅에 처음 발을 디딘 사람들은 누구였을까요? 언제, 어디에서 왔고, 어떻게 살았을까요? 끝까지 보시면, 땅속의 돌과 뼈, 그리고 유전자가 들려주는 한반도 첫 사람들의 이야기를 알게 되실 겁니다.

## 1. 모비우스 라인

{c04}

1940년대, 미국의 고고학자 할람 모비우스는 지도 위에 보이지 않는 선 하나를 그었습니다. 사람들은 이 선을 모비우스 라인이라고 불렀습니다.

{c05}

주먹도끼는 약 170만 년 전 아프리카에서 처음 나타난 것으로 보는 오래된 돌 도구입니다. 자르고, 찍고, 땅을 파는 데 두루 쓰여서, 옛사람들의 만능 도구라고도 불립니다. 선의 서쪽인 아프리카와 유럽, 서아시아에서는 이렇게 정성껏 다듬은 주먹도끼가 많이 나옵니다. 그런데 선의 동쪽, 동아시아에서는 강자갈을 몇 번 떼어 낸 단순한 찍개만 나온다는 것이었습니다.

{c06}

그래서 동아시아의 옛사람들은 주먹도끼를 만드는 기술이 없었다는 생각이 오랫동안 이어졌습니다. 일부에서는 이것을 동아시아가 뒤처졌다는 뜻으로 읽기도 했습니다.

## 2. 전곡리의 주먹도끼

{c07}

그런데 1978년, 한탄강 강가에서 그 주먹도끼가 나온 것입니다. 이듬해부터 전곡리에서는 본격적인 발굴이 시작되었고, 지금까지 수십 차례 발굴이 이어졌습니다.

{c08}

땅속에서는 주먹도끼를 비롯해 수많은 돌 도구가 쏟아져 나왔습니다. 양쪽 면을 고르게 다듬은 모양은, 유럽과 아프리카의 주먹도끼와 견주어도 손색이 없었습니다. 동아시아에서도 주먹도끼를 만든 사람들이 있었다는 사실이 세상에 알려진 것입니다.

{c09}

다만 전곡리 주먹도끼가 언제 만들어졌는지는 아직 논쟁 중입니다. 흙의 층과 그 아래 현무암의 나이를 재는 방법에 따라, 30만 년 전쯤으로 보는 의견부터 그보다 훨씬 늦게 보는 의견까지 서로 다릅니다.

{c10}

그 뒤 중국 남쪽의 바이써 분지에서도 약 80만 년 전으로 보는 주먹도끼가 나왔습니다. 동아시아에는 주먹도끼가 없다는 생각은, 이렇게 조금씩 무너져 갔습니다.

## 3. 처음 땅을 판 사람들

{c11}

사실 그보다 앞서, 남한에서 처음으로 체계적인 구석기 발굴이 이루어진 곳이 있습니다. 1964년, 충청남도 공주의 석장리입니다. 북한에서는 한 해 앞선 1963년, 함경북도의 굴포리 유적에서 구석기 발굴이 이루어졌습니다.

{c12}

연세대학교 손보기 교수 연구팀은 금강 가의 언덕을 여러 해에 걸쳐 파 내려가며, 오래된 층부터 새로운 층까지 여러 시기의 돌 도구를 찾아냈습니다. 그 전까지는 우리 땅에 구석기 시대가 있었는지조차 확실하지 않았습니다. 석장리 발굴로, 한반도에도 아주 오래전부터 사람이 살았다는 사실이 분명해졌습니다.

## 4. 빙하기의 한반도

{c13}

그렇다면 그때 한반도는 어떤 모습이었을까요? 마지막 빙하기가 가장 추웠던 약 2만 년 전 무렵, 바닷물이 얼음이 되어 해수면은 지금보다 100미터 넘게 낮았습니다. 지금의 서해는 바다가 아니라 넓은 풀밭과 강이 흐르는 평원이었습니다.

{c14}

걸어서 중국까지 갈 수 있는 땅이었던 셈입니다. 북쪽 함경북도에서는 털코끼리, 곧 매머드의 화석이 발견되기도 했습니다.

{c15}

겨울은 지금보다 훨씬 길고 추웠습니다. 숲에는 사슴과 들소, 털코뿔소 같은 큰 짐승들이 살았고, 사람들은 이 짐승들을 따라 움직이며 살았습니다.

{c16}

추위를 피하기에 좋은 곳은 동굴이었습니다. 석회암이 많은 충청북도와 강원도의 산에는 크고 작은 동굴이 많았고, 그 동굴들은 지금 우리에게 귀한 기록을 남겨 주었습니다.

## 5. 흥수아이

{c17}

1982년, 충청북도 청주의 두루봉 동굴에서 광산 일을 하던 김흥수 씨가 동굴 안에서 뼈를 발견했습니다.

{c18}

이듬해 충북대학교 이융조 교수 연구팀이 조사해 보니, 그것은 다섯 살 안팎의 어린아이 뼈였습니다. 아이는 납작한 돌 위에 반듯하게 누워 있었습니다. 처음 발견한 사람의 이름을 따서, 이 아이는 흥수아이라고 불리게 되었습니다.

{c19}

더 놀라운 것은 뼈 둘레의 흙에서 국화 무리의 꽃가루가 나왔다는 사실입니다.

{c20}

그래서 사람들이 세상을 떠난 아이 위에 꽃을 뿌려 장례를 치렀을 것이라는 해석이 나왔습니다. 수만 년 전에도 가족을 잃은 슬픔은 지금과 같았을지 모릅니다.

{c21}

다만 이 해석에는 조심스러운 의견도 많습니다. 꽃가루는 바람이나 동물을 타고 들어올 수도 있기 때문입니다. 아이가 살았던 때도 처음에는 구석기 시대로 보았지만, 그보다 늦은 시기일 수 있다는 의견이 나와 다시 확인이 필요합니다. 흥수아이는 아직 풀리지 않은 질문을 품고 있습니다.

## 6. 수양개의 사냥꾼들

{c22}

충청북도 단양의 남한강 가에는 수양개라는 유적이 있습니다. 1983년부터 이어진 발굴에서, 이곳은 돌 도구를 만들던 큰 작업장이었다는 것이 밝혀졌습니다.

{c23}

이곳에서 많이 나온 도구 가운데 하나가 슴베찌르개입니다. 슴베는 칼이나 창끝의 뿌리 부분을 말합니다. 뾰족한 돌날 아래쪽을 좁고 짧게 다듬어 손잡이에 끼울 수 있게 만든 것이지요.

{c24}

이 돌을 나무 자루에 끼우고 짐승의 힘줄로 단단히 묶으면, 멀리서도 짐승을 잡을 수 있는 날카로운 창이 됩니다. 날카로운 창 덕분에 사람들은 사슴이나 멧돼지처럼 빠른 짐승도 사냥할 수 있게 되었습니다.

{c25}

슴베찌르개는 약 4만 년 전 무렵부터 한반도 곳곳에 나타납니다. 많은 학자들은 이 무렵부터 우리와 같은 현생 인류가 이 땅에 본격적으로 살았다고 봅니다.

{c26}

수양개에서는 좀돌날몸돌도 많이 나왔습니다. 돌덩이 하나에서 손가락보다 가늘고 작은 돌날을 수십 개씩 떼어 내는 기술입니다.

{c27}

이 작은 날들은 나무나 뼈로 만든 자루에 줄지어 박아 칼이나 창으로 썼습니다. 날 하나가 부러지면 그것만 갈아 끼우면 되었지요. 적은 돌로 많은 도구를 만드는, 추운 빙하기에 꼭 맞는 똑똑한 기술이었습니다.

{c28}

비슷한 슴베찌르개와 좀돌날은 시베리아와 중국 북부, 그리고 바다 건너 일본에서도 나옵니다. 한반도의 사냥꾼들이 넓은 동북아시아 사람들과 기술을 주고받으며 이어져 있었다는 뜻입니다.

{c29}

어쩌면 그들은 짐승을 따라, 계절을 따라, 수천 킬로미터를 걸어 이 땅에 닿았을 것입니다. 그리고 빙하기의 혹독한 추위 속에서도 불을 피우고, 도구를 고쳐 쓰며, 서로 기대어 살아남았습니다.

## 7. 뼈에 남은 유전자

{c30}

약 1만 년 전 빙하기가 끝나자, 얼음이 녹으며 바닷물이 다시 차올랐습니다. 서해의 평원은 바다 밑으로 가라앉았고, 한반도는 지금과 비슷한 모습이 되었습니다.

{c31}

그리고 사람들은 바닷가와 강가에 마을을 이루고 살기 시작했습니다. 신석기 시대입니다.

{c32}

이들은 흙으로 그릇을 빚고, 겉에 빗살 같은 줄무늬를 새겼습니다. 바로 빗살무늬토기입니다.

{c33}

최근에는 이 시대 사람 뼈에서 아주 오래된 DNA를 뽑아내는 연구도 이루어지고 있습니다. 부산 가덕도의 장항 유적과 남해안 섬의 유적에서 나온 신석기 사람 뼈가 그 주인공입니다.

{c34}

연구 결과, 이 사람들의 뿌리는 주로 아무르강 유역 같은 동북아시아 북쪽 사람들과 이어져 있었습니다.

{c35}

그런데 일부 사람들에게서는 일본의 옛사람인 조몬 사람과 이어지는 흔적도 함께 나왔습니다.

{c36}

바다를 사이에 두고도, 사람들은 배를 타고 오가며 만나고 섞였던 것입니다. 실제로 남해안의 신석기 유적에서는 일본 규슈에서 온 흑요석 같은 돌도 나와, 두 지역이 서로 오갔다는 것을 보여 줍니다. 다만 아직 분석한 사람 뼈가 많지 않아서, 앞으로 더 많은 연구가 필요합니다.

{c37}

그렇다면 구석기 시대의 첫 사람들이 지금 우리의 직접적인 조상일까요? 이 질문에는 아직 답이 없습니다. 빙하기의 사냥꾼들이 이 땅에 계속 남았는지, 아니면 새로 온 사람들과 섞이거나 바뀌었는지는, 구석기 사람의 뼈가 거의 남아 있지 않아 알기 어렵습니다. 분명한 것은 한반도의 사람들이 오랜 세월 여러 갈래에서 오고, 만나고, 섞이며 이어져 왔다는 사실입니다.

## 마무리. 돌 하나가 들려준 이야기

{c38}

1978년 한 병사가 주운 돌 하나에서 시작된 이야기는, 지금도 한반도 곳곳의 땅속에서 이어지고 있습니다.

{c39}

주먹도끼를 쥐었던 손, 동굴에서 아이를 떠나보낸 사람들, 작은 돌날로 창을 만든 사냥꾼들. 그들은 이름도 남기지 않았지만, 이 땅에서 살아간 첫 이웃들이었습니다.

{c40}

여러분은 한반도에 처음 온 사람들이 어떤 모습이었을 거라고 생각하시나요? 댓글로 여러분의 생각을 들려주세요. 우리 조상의 놀라운 이야기는 이 채널에서 계속 이어집니다."""


def main():
    cmd, folder = sys.argv[1], sys.argv[2]
    if cmd == "job":
        items = [{"id": cid, "width": 1024, "height": 576, "seed": 700 + int(cid[1:]),
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
        proj = {"ver": 7, "category": "장문", "genre": GENRE, "topic": "한반도의 첫 사람들", "title": TITLE,
                "story": story, "sources": [], "notes": "과학 다큐. 유적·유물은 실제 사진 대신 AI 그림", "autophoto": False, "img_source": "그림: 사실묘사",
                "settings": {"format": "롱폼 가로(1920×1080)", "narration": "on",
                             "narr_voice": "Supertonic M2 (남성, 무료 로컬) [supertonic:M2]",
                             "layout": "자막형(큰 제목+사진+자막)", "img_fill": "전체 화면(글자가 사진 위에)",
                             "img_motion": "영상처럼(확대·이동·전환)", "fps": "24", "reveal_hit": "off", "reveal_fx": "off",
                             "head_show": "안 보임(제목 카드만)", "sub_split": "한 줄씩(문장·쉼표로 나눠 차례로)", "img_label": "off",
                             "img_depth": "on", "img_depth_amt": "누끼(앞 인물 따로)"}}   # 그림 속 앞 인물을 오려 따로 움직임 (사용자 결정)
        for cid, spec in CUTOUT.items():           # 그림 옆에 누끼 설정 파일 (영상 프로그램이 읽음)
            json.dump(spec, open(os.path.join(folder, cid + ".png.누끼.json"), "w", encoding="utf-8"))
        out = os.path.join(HERE, "한반도_처음온사람들.json")
        json.dump(proj, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(out, len(story), "chars")


if __name__ == "__main__":
    main()
