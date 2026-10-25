"""장문 미스터리 다큐 '2천 년 전 바닷속 컴퓨터, 안티키테라 기계' — 대본 + 컷별 그림 계획
python 장문/안티키테라/안티키테라_기계.py job <저장폴더> [c01,c02,...]  → 그림 주문서(klein_worker 용, 유화 복원도) job.json
python 장문/안티키테라/안티키테라_기계.py project <그림폴더>          → 프로젝트 파일(render_project 용) 장문/안티키테라/안티키테라_기계.json
대본의 {컷번호} 자리에 그 컷 그림이 들어감. 장문은 실제 사진 위주(사용자 결정): PHOTOS 의 컷은 위키미디어 공용 사진(사진/<컷>.jpg, 출처·라이선스 표시),
나머지는 AI 복원 그림(유화풍) — 실제 유물 사진이 아님을 화면 설명에 밝힘. 사진 후보 받기: 사진_찾기.py
사실 확인: 위키백과(영어) Antikythera mechanism, Nature(2006·2008), Scientific Reports(2021, UCL), Horological Journal(2024, 글래스고대)"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
TITLE = "2천 년 전 바닷속 컴퓨터, 안티키테라 기계의 수수께끼"
STYLE_NAME = "유화(붓터치)"
DIALOGUE = []     # 다큐라 인물 대사 없음 (나레이션만)

# (컷번호, 그림 설명(영어), 화면 설명(한국어))
CUTS = [
    ("c01", "a corroded green bronze lump with tiny ancient gear wheels visible inside, lying on dark sand at the bottom of the sea, rays of light from above", "바닷속 녹슨 청동 덩어리"),
    ("c02", "a stormy Aegean sea in 1900, a small Greek sponge-diving sailing boat struggling in huge waves near a rocky island", "폭풍 속 해면잡이 배"),
    ("c03", "an ancient Greek bronze astronomical device with dials and gears glowing softly on a dark table, imagined reconstruction", "상상 복원한 고대의 기계"),
    ("c04", "a modern museum display case with corroded bronze gear fragments in dim light, visitors' silhouettes", "박물관 진열장 속 조각들"),
    ("c05", "Greek sponge divers in 1900 with heavy copper diving helmets and canvas suits on the deck of a small wooden boat, sunlight", "1900년 해면잡이 잠수부들"),
    ("c06", "a diver in an old copper helmet underwater discovering bronze and marble statues scattered on the seabed among broken amphorae", "바닷속에서 발견된 조각상들"),
    ("c07", "a frightened diver climbing back onto a boat, pulling off his copper helmet, his face pale, other sailors staring at him", "겁에 질려 올라온 잠수부"),
    ("c08", "Greek navy ship and divers in 1901 lifting a large bronze statue of a young man out of the sea with ropes", "1901년 인양 작업"),
    ("c09", "a dusty storeroom of the National Archaeological Museum in Athens around 1901, crates and shapeless corroded bronze lumps on shelves", "창고에 놓인 덩어리"),
    ("c10", "an archaeologist in 1902 with a mustache and a magnifying glass bending over a cracked bronze lump, noticing a small gear wheel inside, lamplight", "1902년, 톱니바퀴를 본 고고학자"),
    ("c11", "close-up of a tiny triangular-toothed bronze gear wheel embedded in green corroded stone", "돌 속의 톱니바퀴"),
    ("c12", "scholars in early 20th century suits arguing around a table in a museum office, one shaking his head in disbelief", "믿지 않은 학자들"),
    ("c13", "a historian of science in the 1950s with glasses studying black-and-white photographs and X-ray films of gear fragments on a light box", "사진과 엑스선 필름을 연구하는 학자"),
    ("c14", "hand-drawn technical diagram sketches of interlocking gear trains spread on a desk with a pencil and compass, 1970s", "톱니바퀴 설계도 스케치"),
    ("c15", "a museum engineer in a workshop carefully assembling a brass reconstruction of an ancient gear mechanism with tiny tools", "청동 복원 모형을 만드는 기술자"),
    ("c16", "a huge industrial X-ray CT scanner machine being wheeled into an old museum hall at night, scientists in lab coats, 2005", "박물관에 들어온 8톤 스캐너"),
    ("c17", "glowing blue X-ray cross-section images of hidden gears inside a corroded bronze fragment on computer screens in a dark room", "엑스선 단층 사진 속 숨은 톱니"),
    ("c18", "tiny faint ancient Greek letters engraved on corroded bronze, revealed by raking light, extreme close-up", "드러난 깨알 같은 글자"),
    ("c19", "a large bronze gear with many teeth turning, behind it a dark sky with a solar eclipse, symbolic composition", "223개의 톱니와 일식"),
    ("c20", "a reconstructed ancient bronze device seen from the front with a big circular dial showing zodiac signs and a golden sun pointer and a silver moon pointer", "앞면 큰 원판, 해와 달"),
    ("c21", "a small sphere half silver half black rotating inside a bronze dial to show the phases of the moon, close-up", "달의 모양을 보여 주는 공"),
    ("c22", "two interlocking bronze gears connected by a small pin sliding in a slot, mechanical detail, warm light", "핀과 홈, 달의 빠르기 장치"),
    ("c23", "the back of a reconstructed bronze device with two large spiral dials and small subsidiary dials, engraved scales", "뒷면 나선 눈금판"),
    ("c24", "ancient Olympic games in a stadium, runners racing, crowd watching, golden afternoon light", "고대 올림픽 경기"),
    ("c25", "five small colored beads (planets) moving on concentric rings around a golden sun on a bronze dial, cosmos model", "다섯 행성을 담은 원판"),
    ("c26", "Archimedes as an old Greek scholar in Syracuse drawing circles in sand, a bronze celestial sphere beside him", "시라쿠사의 아르키메데스"),
    ("c27", "Roman soldiers carrying a bronze celestial sphere through the streets of Rome as war loot, 212 BC", "로마로 옮겨진 천구"),
    ("c28", "the Greek astronomer Hipparchus on the island of Rhodes observing the night sky with an ancient sighting instrument on a terrace", "로도스섬의 히파르코스"),
    ("c29", "an ancient Greek bronze workshop, a craftsman filing small gear teeth by hand with a file, oil lamp, apprentices", "고대 그리스 청동 공방"),
    ("c30", "a Roman merchant ship loaded with statues and amphorae sinking in a storm off a rocky island, around 60 BC", "폭풍에 가라앉는 로마 상선"),
    ("c31", "bronze objects being melted down in a medieval furnace, molten metal pouring, sparks", "녹여져 사라진 청동 기계들"),
    ("c32", "a giant medieval astronomical clock on a European town hall tower in the 14th-15th century, crowd looking up", "1,400년 뒤에 나타난 천문시계"),
    ("c33", "a statistical diagram of a broken circular ring with evenly spaced holes, a scientist pointing at it on a screen, 2024", "구멍 수를 세는 연구"),
    ("c34", "modern divers with lights exploring the Antikythera shipwreck site underwater, finding small bronze fragments in the sand", "지금도 계속되는 수중 발굴"),
    ("c35", "a complete imagined reconstruction of the ancient bronze mechanism with all dials, standing in a beam of light like a treasure", "온전한 모습을 상상한 기계"),
    ("c36", "a starry night sky over the Aegean sea and the island of Antikythera, the Milky Way, calm water reflecting stars", "안티키테라섬 위의 밤하늘"),
]

STORY = """{c01}

안티키테라섬 앞바다에서 2천 년 전의 컴퓨터가 나왔습니다. 녹슨 청동 덩어리 하나. 그 안에는 손톱보다 작은 톱니바퀴 수십 개가 맞물려 있었습니다.

{c02}

1900년 봄, 폭풍을 피해 작은 섬에 숨어든 해면잡이 배 한 척. 잠수부들은 그날 바닷속에서 무엇을 건져 올릴지 몰랐습니다.

{c03}

그리고 120년이 넘게 흐른 지금도, 과학자들은 이 기계를 완전히 풀지 못했습니다. 누가 만들었는지, 왜 이런 기술이 사라졌는지도요.

{c04}

끝까지 보시면, 이 작은 상자가 왜 '역사상 가장 이상한 유물'이라 불리는지 알게 되실 겁니다.

## 1. 폭풍이 데려간 섬

{c05}

1900년 봄, 그리스 시미섬의 해면잡이 잠수부들이 바다로 나섰습니다. 선장 디미트리오스 콘토스의 배였습니다.

그들은 아프리카 쪽 바다로 해면을 따러 가던 길이었습니다. 그런데 거센 폭풍이 몰아쳤습니다. 배는 크레타섬과 그리스 본토 사이의 작은 섬, 안티키테라 앞바다에 몸을 숨겼습니다.

{c06}

폭풍이 잦아들자, 한 잠수부가 무거운 구리 투구를 쓰고 물속으로 내려갔습니다. 수심 약 45미터. 그곳에서 그는 이상한 것을 보았습니다. 모래 위에 흩어진 사람의 형상들이었습니다.

{c07}

잠수부는 허겁지겁 배로 올라왔습니다. 바닷속에 시체와 말들이 썩어 가고 있다고 외쳤다는 이야기가 전해집니다. 하지만 그것은 시체가 아니었습니다. 청동과 대리석으로 만든 조각상이었습니다.

{c08}

이듬해인 1901년, 그리스 해군까지 나서서 큰 인양 작업이 벌어졌습니다. 청동 청년상, 대리석 조각, 도자기 항아리들. 2천 년 전 가라앉은 로마 시대 상선의 보물이었습니다.

유리 그릇과 동전, 사람의 뼈까지 나왔습니다. 지금까지 발견된 고대 난파선 가운데 손꼽히게 큰 배였습니다. 그리스의 부자 도시들에서 실은 귀한 물건을 로마로 나르던 길이었던 것으로 보입니다.

{c09}

사람들의 눈은 온통 아름다운 조각상에 쏠렸습니다. 그 틈에, 볼품없는 녹슨 덩어리 몇 개가 박물관 창고로 옮겨졌습니다. 아무도 눈여겨보지 않았습니다. 그런데 곧, 그 덩어리가 스스로 비밀을 드러냅니다.

## 2. 돌 속의 톱니바퀴

{c10}

1902년 5월, 아테네 국립고고학박물관. 고고학자 발레리오스 스타이스가 창고의 덩어리를 들여다보았습니다. 바닷물에 젖어 있던 덩어리가 마르면서 쩍 갈라져 있었습니다.

{c11}

갈라진 틈 사이로 무언가가 보였습니다. 톱니바퀴였습니다. 삼각형 이가 촘촘히 박힌, 아주 작은 청동 톱니바퀴.

{c12}

하지만 학자들 대부분은 믿지 않았습니다. 2천 년 전 사람들이 이런 정밀한 톱니바퀴를 만들었을 리 없다는 것이었죠. 누군가는 훨씬 나중에 떨어진 물건이 섞인 거라고 했습니다.

수천 년 된 배에서, 시계보다 정교한 기계가 나온다는 건 말이 안 됐습니다. 그래서 이 덩어리는 다시 반세기 가까이 잊혔습니다. 잠시 뒤, 한 학자가 이 덩어리에 인생을 겁니다.

## 3. 50년 동안 풀지 못한 퍼즐

{c13}

1951년, 영국의 과학사학자 데릭 드 솔라 프라이스가 이 덩어리에 빠져들었습니다. 그는 사진을 모으고, 조각 하나하나를 재고, 엑스선과 감마선으로 속을 들여다보았습니다.

{c14}

1959년, 그는 과학 잡지에 이렇게 썼습니다. 고대 그리스의 컴퓨터. 그리고 1974년, 20년 넘는 연구를 담은 책 《그리스인의 톱니바퀴》를 펴냈습니다. 이 기계가 해와 달의 움직임을 계산하는 달력 기계라는 것이었습니다.

{c15}

그 뒤를 런던 과학박물관의 기술자 마이클 라이트가 이었습니다. 그는 수십 년 동안 조각을 다시 재고, 직접 청동 모형을 깎아 만들었습니다.

하지만 커다란 벽이 있었습니다. 덩어리는 모두 82개의 조각으로 부서져 있었고, 톱니바퀴들은 녹 속에 겹겹이 숨어 있었습니다. 눈으로는 볼 수 없는 부분이 너무 많았습니다. 이어서, 그 벽을 무너뜨린 8톤짜리 기계가 등장합니다.

## 4. 8톤 스캐너가 읽어 낸 비밀

{c16}

2005년, 영국과 그리스 연구팀이 놀라운 일을 벌였습니다. 무게 8톤의 산업용 엑스선 단층 촬영기를 박물관 안으로 들여온 것입니다. 유물은 박물관 밖으로 나갈 수 없었으니까요.

{c17}

스캐너는 녹슨 덩어리를 수천 장의 얇은 단면으로 잘라 보듯 찍었습니다. 화면 위로 숨어 있던 톱니바퀴들이 하나둘 떠올랐습니다. 남아 있는 것만 서른 개. 원래는 그보다 훨씬 많았을 것으로 보입니다.

{c18}

더 놀라운 것은 글자였습니다. 청동판 겉과 안쪽에 깨알 같은 그리스 글자가 빼곡히 새겨져 있었습니다. 2천 년 동안 녹 아래 숨어 있던 글자들. 그것은 바로 이 기계의 사용 설명서였습니다.

연구팀은 빛을 여러 방향에서 비춰 찍는 특수 사진 기술까지 동원했습니다. 그렇게 읽어 낸 글자에는 해와 달, 그리고 행성의 이름이 적혀 있었습니다. 2천 년 전 사람이 남긴 설명이, 마침내 다시 읽히기 시작한 것입니다.

{c19}

가장 큰 톱니바퀴의 이는 223개였습니다. 왜 하필 223개일까요? 달이 223번 차고 기우는 동안, 일식과 월식이 거의 같은 순서로 되풀이되기 때문입니다. 바빌로니아 사람들이 알아낸 사로스 주기입니다. 이 기계는 언제 해가 가려질지 미리 알려 주는 기계였습니다. 그리고 곧, 이 상자 안에 하늘 전체가 들어 있다는 사실이 밝혀집니다.

## 5. 하늘을 담은 상자

{c20}

이제 연구자들은 이 기계의 모습을 그려 볼 수 있었습니다. 크기는 신발 상자만 했습니다. 옆에 달린 손잡이를 돌리면, 앞면의 큰 원판 위로 해와 달의 바늘이 움직였습니다.

{c21}

작은 공 하나는 반은 은빛, 반은 검은빛이었습니다. 공이 돌아가며 오늘 밤 달이 초승달인지 보름달인지 보여 주었습니다.

{c22}

놀라운 장치는 또 있었습니다. 달은 하늘에서 늘 같은 빠르기로 움직이지 않습니다. 빨라졌다 느려졌다 하죠. 기계는 이것까지 따라 했습니다. 두 톱니바퀴를 핀과 홈으로 엇갈리게 이어, 달의 빠르기가 저절로 바뀌게 만든 것입니다.

{c23}

뒷면에는 나선 모양의 큰 눈금판 두 개가 있었습니다. 하나는 19년 주기의 달력, 하나는 일식과 월식 예보판이었습니다.

{c24}

그리고 2008년, 작은 눈금판 하나에서 뜻밖의 글자가 읽혔습니다. 올림피아. 4년마다 열리는 고대 올림픽 같은 경기들의 날짜까지 알려 주는 판이었습니다.

{c25}

2021년, 영국 런던대학교 연구팀이 마침내 앞면 전체의 복원안을 내놓았습니다. 앞면에는 해와 달만이 아니라, 맨눈으로 보이는 다섯 행성의 움직임까지 담겨 있었다는 것입니다. 수성, 금성, 화성, 목성, 토성.

연구팀은 글자 속 숫자 462와 442를 실마리로 삼았습니다. 금성과 토성이 하늘의 같은 자리로 돌아오는 햇수였습니다. 손바닥만 한 상자 안에 그들이 아는 우주 전체가 들어 있었던 셈입니다. 그렇다면 이 놀라운 기계를, 대체 누가 만들었을까요? 다음 장에서 용의자들을 만나 보겠습니다.

## 6. 누가 만들었을까

{c26}

첫 번째 용의자는 고대 최고의 발명가, 아르키메데스입니다. 그는 시칠리아섬의 도시 시라쿠사에 살았습니다.

{c27}

로마의 정치가 키케로는 이런 기록을 남겼습니다. 기원전 212년, 로마 장군 마르켈루스가 시라쿠사를 함락한 뒤 아르키메데스가 만든 천체 기계 두 대를 로마로 가져갔다고요. 해와 달과 행성의 움직임을 보여 주는 기계였습니다.

{c28}

두 번째 용의자는 천문학자 히파르코스입니다. 달이 빨라졌다 느려지는 이론을 세운 사람이 바로 그였습니다. 그가 연구하던 로도스섬은 정밀한 천체 기계를 만들던 곳으로도 알려져 있었습니다.

{c29}

세 번째 단서는 기계 속 글자에 있었습니다. 달력에 적힌 달 이름이 코린토스와 그 식민 도시들이 쓰던 이름이었던 것입니다. 이 기계가 그리스 북서쪽의 누군가를 위해 주문 제작되었다는 주장도 있습니다.

어쩌면 한 명의 천재가 아니라, 여러 세대에 걸친 장인들의 공방이 있었는지도 모릅니다. 확실한 것은 하나. 이 기계는 결코 처음 만든 물건이 아니었다는 것입니다. 이렇게 정교하려면, 그 전에 수많은 연습작이 있었어야 합니다. 그런데 바로 여기서, 더 큰 수수께끼가 시작됩니다.

## 7. 사라진 1,400년

{c30}

기원전 70년에서 60년 무렵, 조각상과 이 기계를 실은 로마 상선이 안티키테라 앞바다에서 가라앉았습니다. 그리고 이 기술도 함께 바닷속으로 사라진 것처럼 보입니다.

{c31}

그렇게 많은 연습작이 있었다면, 왜 하나도 남지 않았을까요? 가장 그럴듯한 답은 청동입니다. 청동은 귀한 금속이었습니다. 쓸모를 다한 청동 기계는 녹여져 칼이나 동전이 되었을 것입니다. 바닷속에 가라앉은 덕분에, 이 하나만 살아남은 것이죠.

{c32}

이만큼 복잡한 톱니바퀴 기계가 다시 나타난 것은 14세기, 유럽 성당과 시청에 천문시계가 세워지면서부터였습니다. 무려 1,400년 가까운 공백입니다.

물론 불씨가 완전히 꺼진 것은 아니었습니다. 6세기 무렵 비잔틴 제국에서 만든 톱니바퀴 해시계 달력이 남아 있고, 11세기 페르시아의 학자 알비루니는 톱니바퀴로 달의 모양을 보여 주는 달력 기계를 글로 남겼습니다. 하지만 안티키테라 기계만큼 복잡한 것은 어디에도 없었습니다.

인류는 한 번 손에 쥐었던 지식을, 천 년 넘게 잃어버렸던 것입니다. 잠시 뒤, 이 기계가 아직도 숨기고 있는 비밀을 알아보겠습니다.

## 8. 아직 남은 수수께끼

{c33}

2024년, 영국 글래스고대학교 연구팀은 중력파를 찾을 때 쓰는 통계 방법으로 부서진 달력 고리의 구멍 수를 계산했습니다. 결과는 354개 안팎. 1년이 354일인 달의 달력과 거의 꼭 맞는 숫자였습니다. 이 기계는 해가 아니라 달을 기준으로 날짜를 셌을지도 모릅니다.

{c34}

지금도 잠수부들은 안티키테라 바다 밑을 뒤지고 있습니다. 기계의 사라진 조각이 아직 그 모래 속에 묻혀 있을지도 모르기 때문입니다. 실제로 1976년에도, 2005년에도 새로운 조각이 발견되었습니다.

{c35}

언제 처음 맞춰졌는지, 누가 만들었는지, 얼마나 많은 톱니가 들어 있었는지. 우리는 여전히 이 기계의 절반만 알고 있습니다.

기계가 처음 날짜를 맞춘 해를 두고도 의견이 갈립니다. 일식 예보판을 거꾸로 계산해 기원전 205년이라는 학자도 있고, 기원전 178년 12월이라는 학자도 있습니다. 같은 유물을 보고도, 아직 답이 하나로 모이지 않은 것입니다.

{c36}

2천 년 전 어느 밤, 누군가 이 섬 위의 하늘을 올려다보았습니다. 그리고 그 하늘을 손바닥만 한 상자에 담았습니다. 우리가 그 사람의 이름을 알게 되는 날이 올까요?

여러분이라면 이 기계를 누가 만들었다고 생각하시나요? 댓글로 여러분의 추리를 들려주세요. 보고 나면 가벼운 지식이 남는 이야기, 이 채널에서 계속 이어집니다."""


# 실제 사진을 보고 그리는 컷 (사용자 결정: 실제로 있는 물건·유물은 실제 사진을 기준 그림으로 넣어 그림) → 사진후보 이름들
REFS = {"c03": ["c20_1"], "c21": ["c20_1"], "c25": ["c20_1"], "c35": ["c20_1", "c23_8"],
        "c10": ["c01_8"], "c17": ["c18_3"], "c19": ["c01_9"], "c22": ["c11_1"], "c14": ["c13_1"]}
REF_NOTE = ("The ancient device must look exactly like the reference photo of the real Antikythera mechanism "
            "(a wooden box with a large bronze dial and interlocking bronze gears, corroded green bronze where it is a fragment), "
            "not a clock, not an astrolabe. ")

# 컷 → 고른 위키미디어 사진 후보 이름 (사진후보/후보.json 의 열쇠). 장면에 맞는 자유 이용 사진이 없는 컷만 AI 그림
PHOTOS = {"c01": "c01_8", "c04": "c04_1", "c05": "c05_1", "c06": "c06_1", "c08": "c06_4", "c09": "c09_3", "c11": "c01_9",
          "c13": "c13_1", "c15": "c13_3", "c18": "c18_4", "c20": "c20_1", "c23": "c23_8", "c24": "c24_2", "c26": "c26_3",
          "c28": "c28_1", "c32": "c32_1", "c36": "c36_2"}


def main():
    cmd, folder = sys.argv[1], sys.argv[2]
    src = open(os.path.join(ROOT, "shorts_novel_maker_supertonic.py"), encoding="utf-8").read()
    style = re.search('"' + re.escape(STYLE_NAME) + '": "([^"]+)"', src).group(1)
    only = sys.argv[3].split(",") if len(sys.argv) > 3 else None
    if cmd == "job":
        items = []
        for cid, desc, _ in CUTS:
            if only and cid not in only:
                continue
            refs = [os.path.join(HERE, "사진후보", k + ".jpg") for k in REFS.get(cid, [])]
            items.append({"id": cid, "width": 1024, "height": 576, "seed": 300 + int(cid[1:]), "refs": refs,
                          "prompt": f"{style}, historical documentary illustration, realistic proportions, museum-quality painting. "
                                    f"Scene: {desc}. {REF_NOTE if refs else ''}Any people have exactly two arms and two legs. "
                                    "Cinematic composition, full-bleed image, no border, no frame, no paper edges. No text, no letters, no captions."})
        os.makedirs(folder, exist_ok=True)
        json.dump({"items": items, "skip_done": True}, open(os.path.join(folder, "job.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(len(items), "cuts")
    elif cmd == "project":
        story = STORY
        meta = json.load(open(os.path.join(HERE, "사진후보", "후보.json"), encoding="utf-8"))
        for cid, _, cap in CUTS:
            if cid in PHOTOS:
                m = meta[PHOTOS[cid]]
                img = os.path.join(HERE, "사진", cid + ".jpg")
                credit = f"{m['artist'] or 'Wikimedia Commons'} / {m['license']} / Wikimedia Commons"
                story = story.replace("{" + cid + "}", f"[사진: {img} | {cap} | {credit} | {m['page']}]")
                continue
            img = next((os.path.join(folder, cid + e) for e in (".png", ".jpg") if os.path.exists(os.path.join(folder, cid + e))), os.path.join(folder, cid + ".png"))
            story = story.replace("{" + cid + "}", f"[사진: {img} | {cap} | AI 복원 그림 (FLUX.2 klein) | ]")
        proj = {"ver": 7, "category": "장문", "genre": "[다큐] 역사·미스터리", "topic": "안티키테라 기계", "title": TITLE,
                "story": story, "sources": ["https://en.wikipedia.org/wiki/Antikythera_mechanism"],
                "notes": "역사 미스터리 장문 다큐 (실제 사진 위주 + 사진이 없는 장면은 AI 복원 그림)", "autophoto": False, "img_source": "그림: 유화",
                "settings": {"format": "롱폼 가로(1920×1080)", "narration": "on",
                             "layout": "자막형(큰 제목+사진+자막)", "img_fill": "전체 화면(글자가 사진 위에)",
                             "img_motion": "영상처럼(확대·이동·전환)",
                             "head_show": "안 보임(제목 카드만)", "sub_split": "한 줄씩(문장·쉼표로 나눠 차례로)", "img_label": "off",
                             "narr_voice": "Supertonic M2 (남성, 무료 로컬) [supertonic:M2]"}}
        out = os.path.join(HERE, "안티키테라_기계.json")
        json.dump(proj, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(out, len(story), "chars")


if __name__ == "__main__":
    main()
