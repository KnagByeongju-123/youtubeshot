"""《두 번째 새벽》 3화 '숲의 눈' — 대본 + 컷별 그림 계획
python 연재/두번째새벽/3화_숲의눈.py job <저장폴더> [애니] [c01,c06,...]   → 그림 주문서(klein_worker 용) job.json
  (애니 = 애니 일러스트 화풍 + 캐릭터시트_애니, 컷번호를 적으면 그 컷만)
python 연재/두번째새벽/3화_숲의눈.py project <그림폴더> [애니] → 프로젝트 파일(render_project 용) 연재/두번째새벽/3화_숲의눈.json
대본의 {컷번호} 자리에 그 컷 그림이 들어감. chars = 그 컷에 나오는 인물(캐릭터 시트를 기준 그림으로 넣음)
[마을] 하누족 숲 마을 '잎새골' · [과학] 자갈·모래·숯 거름장치와 끓이기 (시도 → 실패 → 깨달음 → 성공)
[비밀 단서] 우물 바닥 옛 관에 새겨진 탑과 검은 공 표시 — 어머니가 옛날 물길까지 관리했다 / [동료 목록] 아홉 → 잎새골
[절벽 엔딩] 숲 가장자리에서 오르는 불길 (4화 정화의 불로 이어짐)"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TITLE = "두 번째 새벽 3화 - 숲의 눈"

# 대사 → 말하는 인물 (그 인물 목소리로 읽음, 목소리는 등장인물.json 의 voice)
DIALOGUE = [
    ("한 걸음이라도 움직이면, 이 지팡이가 먼저 움직인다.", "카룬"),
    ("위협. 낮음. 보호... 대기.", "아홉"),
    ("기사들이 오고 있어. 우리를 데려가. 네 마을의 법으로 판단해.", "한별"),
    ("하늘에서 온 인간, 그리고 쇠귀신이라.", "잎새 할머니"),
    ("물. 오염. 눈에 보이지 않는 작은 생물. 위험.", "아홉"),
    ("고칠 수 있어.", "한별"),
    ("모래만으로는 안 돼. 큰 것부터 작은 것까지, 차례로 걸러야 해.", "한별"),
    ("층. 자갈. 모래. 숯. 옛 기록과 일치.", "아홉"),
    ("맑아졌잖아. 이제 마셔도 되지?", "도토리"),
    ("아직이야. 한 번 끓여야 해.", "한별"),
    ("형, 이 물은 냄새가 안 나.", "도토리"),
    ("왜 우리를 돕지? 우린 너희를 가뒀는데.", "카룬"),
    ("고장 난 건 버리지 말고 고치라고 배웠거든. 마을도 마찬가지야.", "한별"),
    ("오늘부터 잎새골은 너희에게 문을 닫지 않겠다.", "잎새 할머니"),
    ("수원지. 관리자... 어머니.", "아홉"),
    ("숲을 태워라. 쇠귀신이 숨을 곳을 남기지 마라.", "강무진 경"),
]

# (컷번호, 나오는 인물, 그림 설명(영어), 화면 설명(한국어))
CUTS = [
    ("c01", ["한별", "카룬"], "inside an abandoned old workshop at dawn, misty light through a broken window, the chimpanzee warrior pointing the tip of his staff at the startled girl who just woke up on a workbench under her cloak", "한별을 겨눈 지팡이"),
    ("c02", ["아홉"], "inside an abandoned old workshop at dawn, the tall skull-faced robot rising to its full height in the doorway, its single blue eye glowing, one long arm half raised, dust in the light beams", "일어선 아홉"),
    ("c03", [], "a line of medieval knights with torches and red banners marching through misty ruins at dawn toward an old workshop, seen from far away", "다가오는 기사들의 횃불"),
    ("c04", ["카룬"], "the chimpanzee warrior turning his head sharply toward a broken window, listening, his ears alert, torchlight glowing far outside in the mist", "횃불 소리를 듣는 카룬"),
    ("c05", ["한별", "카룬"], "the girl standing up and speaking firmly to the chimpanzee warrior in a dusty workshop, holding out both open hands, morning mist outside", "법으로 판단해 달라는 한별"),
    ("c06", ["아홉", "카룬"], "the chimpanzee warrior binding the tall robot's wrists together with thick green vines, the robot standing still and letting him, in front of a ruined workshop at dawn", "덩굴로 묶이는 아홉"),
    ("c07", ["한별", "아홉", "카룬"], "the chimpanzee warrior leading the girl and the tall robot with vine-bound wrists past warning totems with hanging broken robot heads into a huge misty forest", "경고 표식을 지나 숲으로"),
    ("c08", [], "a hidden village of the evolved ape people built high in gigantic ancient trees, wooden huts on huge branches, rope bridges and ladders, smoke from a small forge, morning sunlight through leaves", "나무 위의 마을, 잎새골"),
    ("c09", [], "many evolved chimpanzee and orangutan villagers in bark and leather clothes on rope bridges and branches looking down angrily, some holding stones and spears, a forest village in giant trees", "몰려든 잎새골 사람들"),
    ("c10", ["아홉"], "the tall robot standing still with vine-bound wrists while small stones bounce off its rusty shoulder, it does not fight back, its blue eye dim, forest village", "돌을 맞는 아홉"),
    ("c11", ["잎새 할머니"], "the old orangutan village elder sitting on a carved wooden seat under a huge tree on a high platform, holding her cane, looking down with wise stern eyes, warm sunlight through leaves", "잎새골의 촌장, 잎새 할머니"),
    ("c12", ["한별", "아홉"], "the girl and the tall robot locked inside a big wooden cage made of thick branches hanging in a forest village, the girl gripping the bars, evening light", "나무 우리에 갇힌 둘"),
    ("c13", ["카룬"], "the chimpanzee warrior sitting alone on a high branch at dusk, looking down at a wooden cage below, his staff across his knees, thoughtful and troubled", "우리를 내려다보는 카룬"),
    ("c14", [], "inside a dim treehouse sickroom, small young ape children lying on straw mats with damp cloths on their foreheads, an old ape healer grinding herbs in a stone bowl, candlelight", "앓아누운 아이들"),
    ("c15", ["도토리"], "the small chimpanzee child lying on a straw mat with a fever, holding his stomach, eyes half closed, a wet cloth on his forehead, dim candlelight", "열이 나는 도토리"),
    ("c16", [], "an old stone well at the root of a giant tree in a forest village, close-up of a wooden bucket of cloudy brownish murky water with floating dirt, a rusty old metal pipe sticking out of the well wall", "흐려진 우물물"),
    ("c17", ["아홉"], "the tall robot inside a wooden cage pointing its single blue eye toward a bucket of murky water outside the bars, a thin scanning beam of blue light shining on the water", "물을 살피는 아홉의 눈"),
    ("c18", ["한별", "잎새 할머니"], "at night in a forest village, the girl inside a wooden branch cage speaking earnestly through the bars to the old orangutan elder holding a lantern and a cane outside the cage", "할머니와 약속하는 한별"),
    ("c19", ["한별"], "the girl outside in a forest village pouring murky water through a cloth sack filled only with sand into a clay pot, the water coming out still cloudy and brown, disappointed face", "모래만 넣은 첫 번째 시도"),
    ("c20", [], "ape villagers in a forest village laughing and shaking their heads, pointing at a clay pot of cloudy water on a wooden table", "웃음을 터뜨린 마을 사람들"),
    ("c21", ["아홉"], "the tall robot drawing a simple diagram in the dirt with one long metal finger: layers stacked inside a tall container, its single blue eye glowing, forest village", "땅에 층을 그리는 아홉"),
    ("c22", ["카룬"], "the chimpanzee warrior carrying a heavy woven basket full of black charcoal pieces from a small village forge with glowing embers behind him", "숯을 가져온 카룬"),
    ("c23", ["한별", "아홉"], "the girl and the tall robot building a water filter in a big hollow log standing upright: layers of large gravel, small gravel, sand and black charcoal visible through a cut-away side, a cloth at the bottom over a clay pot", "자갈·모래·숯을 쌓은 거름 통"),
    ("c24", [], "close-up of clear clean water trickling from the bottom of a hollow log filter through a cloth into a clay pot, sunlight sparkling in the water drops", "맑게 흘러나온 물"),
    ("c25", ["한별", "도토리"], "the girl gently stopping the small chimpanzee child from drinking from a bowl of clear water, kneeling to his eye level, a large pot of water boiling over a fire behind them", "끓여야 한다고 말리는 한별"),
    ("c26", [], "several big clay pots of water boiling over open fires in a forest village at dusk, steam rising, ape villagers carrying firewood", "물을 끓이는 마을"),
    ("c27", ["아홉"], "the tall robot carrying heavy wooden buckets of water up a long rope ladder in a giant tree at night under the moon, its blue eye glowing, sleeping village around", "밤새 물을 나르는 아홉"),
    ("c28", ["도토리"], "the small chimpanzee child sitting up on his straw mat with a bright smile, drinking from a wooden cup of clear water, morning sunlight through the treehouse window", "다시 웃는 도토리"),
    ("c29", ["한별", "카룬"], "the chimpanzee warrior and the girl standing face to face on a rope bridge high in giant trees at sunset, he lowers his staff, she smiles calmly", "지팡이를 내린 카룬"),
    ("c30", ["잎새 할머니"], "the old orangutan elder opening the door of an empty wooden branch cage in a forest village, warm morning light, villagers watching quietly", "우리 문을 연 할머니"),
    ("c31", ["도토리", "한별"], "the small chimpanzee child shyly giving the girl a small carved wooden leaf token on a string, the girl kneeling to receive it with both hands, forest village", "나뭇잎 표식을 건네는 도토리"),
    ("c32", ["아홉"], "the tall robot kneeling at the bottom of an old drained stone well, its blue eye lighting a rusty old metal pipe engraved with a faded symbol of a tall tower with a dark sphere on top", "우물 바닥 옛 관의 표시"),
    ("c33", ["서린"], "the priestess standing alone in an empty ruined workshop holding a pair of old brass goggles, looking out of a broken window toward a huge dark forest, worried", "빈 작업장에 남은 서린"),
    ("c34", ["강무진 경"], "the knight commander at night at a forest edge giving an order, pointing his sword at the dark forest, knights behind him lighting torches", "숲을 가리키는 강무진"),
    ("c35", [], "at night, orange flames and thick smoke rising at the edge of a vast dark forest under the stars, seen from the treetops far away", "숲 가장자리의 불길"),
    ("c36", ["한별", "카룬"], "at night on a high tree platform, the chimpanzee warrior and the girl staring in shock at a distant orange glow of fire on the horizon, wind blowing leaves", "불길을 바라보는 한별과 카룬"),
]

STORY = """{c01}

숲의 눈을 가진 전사가, 잠에서 깬 열일곱 살 한별의 목에 지팡이 끝을 겨누었습니다. 수백 년 동안 쇠귀신과 싸워 온 하누족의 호박색 눈이었습니다.

"한 걸음이라도 움직이면, 이 지팡이가 먼저 움직인다."

{c02}

문 앞에 앉아 있던 아홉이 천천히 일어섰습니다. 키가 전사보다 두 배는 컸습니다. 파란 외눈이 전사를 내려다보았습니다. 수백 년 동안 서로를 부숴 온 두 종족이, 좁은 작업장 안에서 마주 섰습니다.

"위협. 낮음. 보호... 대기."

{c03}

그리고 안개 너머, 기사들의 횃불이 작업장으로 다가오고 있었습니다. 지난 화, 한별은 지하 로봇 무덤에서 깨어난 아홉과 첫 동료가 되었습니다. 이번 화에서 두 사람은 숲 깊은 곳의 마을에 갇히고, 그 마을의 목숨이 걸린 문제와 마주합니다. 끝까지 보시면, 한별이 어떻게 숲의 마음을 열었는지 알게 되실 겁니다.

## 1. 숲의 법

{c04}

전사의 귀가 움찔했습니다. 쇠 발굽 소리. 칼집이 부딪히는 소리. 기사들이 가까이 와 있었습니다.

{c05}

한별은 두 손을 펼쳐 보였습니다. 손에는 아무것도 없었습니다.

"기사들이 오고 있어. 우리를 데려가. 네 마을의 법으로 판단해."

전사는 한별을 한참 노려보았습니다. 하늘에서 온 인간에게 잡힐 바에야, 숲의 법을 따르겠다는 아이였습니다.

{c06}

전사는 질긴 덩굴로 아홉의 두 손목을 묶었습니다. 아홉은 가만히 손을 내밀었습니다. 마음만 먹으면 덩굴쯤은 단숨에 끊을 수 있었습니다. 하지만 아홉은 그러지 않았습니다.

{c07}

셋은 기사들이 닿기 직전에 숲으로 들어갔습니다. 부서진 로봇 머리가 매달린 경고 표식을 지나자, 나무들이 하늘을 덮을 만큼 커졌습니다. 전사의 이름은 카룬이었습니다. 그리고 곧, 숲은 사람들의 진짜 집을 보여 줍니다.

## 2. 잎새골

{c08}

거대한 나무 위에 마을이 있었습니다. 굵은 가지마다 오두막이 얹혀 있었고, 밧줄 다리가 나무와 나무를 이었습니다. 대장간 굴뚝에서는 연기가 피어올랐습니다. 하누족의 숲 마을, 잎새골이었습니다.

{c09}

마을 사람들이 밧줄 다리 위로 몰려들었습니다. 그들의 눈이 아홉에게 꽂혔습니다. 쇠귀신이 마을 한가운데까지 들어온 것은 처음이었습니다.

{c10}

누군가 돌을 던졌습니다. 또 하나, 또 하나. 돌멩이가 아홉의 녹슨 어깨에 맞고 튀었습니다. 아홉은 피하지도, 막지도 않았습니다. 묶인 손으로 그저 서 있었습니다.

{c11}

그때 높은 단 위에서 지팡이 소리가 울렸습니다. 마을이 조용해졌습니다. 잎새골의 촌장, 잎새 할머니였습니다.

"하늘에서 온 인간, 그리고 쇠귀신이라."

할머니는 오래 생각한 끝에 말했습니다. 둘을 가두어 두고, 사흘 뒤 마을 사람들이 함께 판단하겠다고.

{c12}

한별과 아홉은 굵은 나뭇가지로 엮은 우리에 갇혔습니다. 우리는 큰 나무 아래 매달려 바람에 흔들렸습니다.

{c13}

카룬은 높은 가지 위에 앉아 그 우리를 오래 내려다보았습니다. 쇠귀신은 왜 덩굴을 끊지 않았을까요? 그 질문이 머릿속을 떠나지 않았습니다. 카룬이 아직 어렸을 때, 어머니는 숲 가장자리에서 쇠귀신에게 목숨을 잃었습니다. 그날부터 카룬에게 쇠는 모두 원수였습니다. 그런데 곧, 그날 밤 마을에서 아이 우는 소리가 들려옵니다.

## 3. 앓는 아이들

{c14}

마을의 한 오두막에는 아이들이 나란히 누워 있었습니다. 모두 열이 펄펄 끓었고, 배를 움켜쥐고 앓았습니다. 늙은 치유사는 약초를 빻고 또 빻았습니다. 하지만 아이들은 나아지지 않았습니다.

{c15}

그중에는 카룬의 어린 동생, 도토리도 있었습니다. 늘 형 뒤를 졸졸 따라다니던 아이가, 이제는 눈도 제대로 뜨지 못했습니다.

{c16}

한별은 우리 안에서 사람들이 길어 오는 물을 보았습니다. 우물물이 흐리고 누랬습니다. 마을 사람들은 지난 큰비 뒤로 물맛이 이상해졌다고 수군거렸습니다. 우물 벽에는 녹슨 옛 관 하나가 튀어나와 있었습니다.

{c17}

아홉의 외눈에서 가는 빛줄기가 나와 물동이를 훑었습니다.

"물. 오염. 눈에 보이지 않는 작은 생물. 위험."

아이들을 앓게 한 것은 저주가 아니었습니다. 물속의, 눈에 보이지 않는 아주 작은 생물들이었습니다.

{c18}

한별은 우리 창살을 붙잡고 등불을 든 잎새 할머니를 불렀습니다.

"고칠 수 있어."

물을 맑게 해 보겠다고, 대신 아이들이 나으면 아홉을 믿어 달라고. 할머니는 한참 한별의 눈을 들여다보았습니다. 그리고 우리 문의 매듭을 풀었습니다. 단, 하루 안에 해내야 했습니다. 잠시 뒤, 한별의 첫 번째 시도가 시작됩니다.

## 4. 첫 번째 실패

{c19}

한별은 천 자루에 고운 모래를 가득 담고 흐린 물을 부었습니다. 모래 사이를 지나면 흙이 걸러질 것이라 생각했습니다. 하지만 아래로 떨어진 물은 여전히 누렇게 흐렸습니다.

{c20}

지켜보던 마을 사람들이 웃음을 터뜨렸습니다. 하늘에서 온 인간도 별수 없다는 웃음이었습니다. 한별의 얼굴이 붉어졌습니다.

{c21}

그때 아홉이 긴 손가락으로 땅에 그림을 그렸습니다. 길쭉한 통 하나, 그 안에 여러 겹의 층.

"층. 자갈. 모래. 숯. 옛 기록과 일치."

한별의 눈이 커졌습니다.

"모래만으로는 안 돼. 큰 것부터 작은 것까지, 차례로 걸러야 해."

굵은 자갈은 나뭇잎과 큰 흙덩이를 막습니다. 잔자갈과 모래는 더 작은 흙 알갱이를 붙잡습니다. 그리고 숯에는 눈에 안 보이는 작은 구멍이 아주 많아서, 냄새와 누런 빛을 빨아들입니다.

{c22}

숯은 어디서 구할까요? 한별이 고개를 들었을 때, 카룬이 이미 대장간에서 숯 바구니를 짊어지고 오고 있었습니다. 카룬은 아무 말도 하지 않았습니다.

{c23}

둘은 속이 빈 커다란 통나무를 세우고, 바닥에 천을 댔습니다. 그 위로 숯, 모래, 잔자갈, 굵은 자갈을 차례로 쌓았습니다. 맨 위에 흐린 우물물을 부었습니다. 마을 전체가 숨을 죽였습니다. 그리고 이어서, 통나무 아래로 첫 물방울이 떨어집니다.

## 5. 물을 끓여라

{c24}

통나무 아래로 흘러나온 물은 투명했습니다. 햇빛이 물방울 속에서 반짝였습니다. 마을 사람들이 술렁였습니다.

{c25}

도토리가 비틀거리며 다가와 물그릇을 들었습니다.

"맑아졌잖아. 이제 마셔도 되지?"

한별은 도토리의 손을 살며시 붙잡았습니다.

"아직이야. 한 번 끓여야 해."

거름장치는 흙과 냄새를 걸러 주지만, 눈에 보이지 않는 작은 생물까지 모두 잡지는 못합니다. 그 작은 생물들은 펄펄 끓는 물속에서 살아남지 못합니다. 그래서 거르고, 끓여서, 식혀 마셔야 합니다.

{c26}

마을 곳곳에 불이 피워지고, 커다란 항아리마다 물이 끓었습니다. 하누족 아이들이 장작을 날랐습니다. 처음으로, 한별과 마을 사람들이 같은 일을 하고 있었습니다.

{c27}

그날 밤, 아홉은 쉬지 않고 물동이를 날랐습니다. 묶였던 손목에는 아직 덩굴 자국이 남아 있었습니다. 기다란 밧줄 사다리를 오르내리는 쇠귀신을, 마을 사람들은 처음으로 다른 눈으로 바라보았습니다. 그리고 곧, 사흘이 지납니다.

## 6. 카룬의 망설임

{c28}

사흘째 아침, 도토리가 자리에서 일어나 앉았습니다. 열이 내린 것이었습니다. 다른 아이들도 하나둘 미음을 넘기기 시작했습니다.

"형, 이 물은 냄새가 안 나."

카룬은 동생을 끌어안고 한참 동안 아무 말도 하지 못했습니다. 어머니를 잃은 날처럼, 또 하나를 잃을까 봐 사흘 밤을 한숨도 자지 못했던 것입니다.

{c29}

해 질 녘, 카룬은 밧줄 다리 위에서 한별을 불러 세웠습니다. 손에 쥔 지팡이 끝은 이제 땅을 향하고 있었습니다.

"왜 우리를 돕지? 우린 너희를 가뒀는데."

"고장 난 건 버리지 말고 고치라고 배웠거든. 마을도 마찬가지야."

카룬은 대답하지 않았습니다. 하지만 그의 눈빛이 처음으로 흔들렸습니다. 아버지에게 배운 대로라면, 인간과 쇠귀신은 적이었습니다. 그런데 그 적이, 동생을 살렸습니다.

{c30}

다음 날 아침, 잎새 할머니가 직접 빈 우리의 문을 활짝 열었습니다.

"오늘부터 잎새골은 너희에게 문을 닫지 않겠다."

{c31}

도토리가 쭈뼛거리며 다가와 작은 나무 조각을 내밀었습니다. 나뭇잎 모양으로 깎은 잎새골의 표식이었습니다. 한별은 무릎을 꿇고 두 손으로 그것을 받았습니다. 지구에서 얻은 두 번째 동료, 잎새골이었습니다. 하지만 바로 다음 순간, 우물 바닥에서 아홉이 무언가를 찾아냅니다.

## 7. 우물 속의 표시

{c32}

물을 다 퍼낸 우물 바닥, 녹슨 옛 관에 희미한 표시가 새겨져 있었습니다. 하늘을 찌르는 탑, 그리고 그 꼭대기의 검은 공. 아홉의 눈이 비춘 바로 그 그림이었습니다.

"수원지. 관리자... 어머니."

옛날에는 이 숲의 물길까지 어머니가 돌보았던 것입니다. 어머니가 무너진 뒤, 관은 녹슬고 물은 흐려졌습니다. 한별은 그 표시를 오래 바라보았습니다.

{c33}

같은 시각, 텅 빈 작업장에 서린이 홀로 서 있었습니다. 손에는 한별이 두고 간 낡은 황동 고글이 들려 있었습니다. 서린은 깨진 창 너머 거대한 숲을 바라보았습니다. 그 아이는 저 숲 어딘가에 살아 있을까요? 이어서, 그 숲에 마지막 명령이 떨어집니다.

## 8. 숲의 불

{c34}

밤이 깊어지자, 강무진 경이 숲 가장자리에 섰습니다. 기사들이 하나둘 횃불에 불을 붙였습니다.

"숲을 태워라. 쇠귀신이 숨을 곳을 남기지 마라."

{c35}

마른 덤불에 불이 옮겨붙었습니다. 바람을 탄 불길이 붉게 일어났습니다. 검은 연기가 별빛을 가렸습니다.

{c36}

잎새골의 높은 단 위에서, 한별과 카룬은 지평선 너머의 붉은 빛을 바라보았습니다. 바람은 마을 쪽으로 불고 있었습니다. 카룬이 천천히 한별을 돌아보았습니다. 사흘 만에 쌓은 믿음이, 하룻밤 사이에 다시 무너지려 하고 있었습니다.

한별은 이번에도, 고칠 수 있을까요? 《두 번째 새벽》은 이 채널에서 매화 계속 이어집니다.

다음 이야기, 4화 정화의 불. 불길은 잎새골까지 닿을까요?"""


def main():
    cmd, folder = sys.argv[1], sys.argv[2]
    anime = len(sys.argv) > 3 and sys.argv[3] == "애니"
    chars = {c["name"]: c for c in json.load(open(os.path.join(HERE, "등장인물.json"), encoding="utf-8"))["chars"]}
    src = open(os.path.join(HERE, "..", "..", "shorts_novel_maker_supertonic.py"), encoding="utf-8").read()
    style_name = "애니 일러스트\\(요즘\\)" if anime else "옛날 만화책\\(세피아 펜화\\)"
    style = re.search(f'"{style_name}": "([^"]+)"', src).group(1)
    face, kind = ("face_anime", "anime illustration") if anime else ("face", "comic panel")
    only = sys.argv[4].split(",") if len(sys.argv) > 4 else None
    # 애니 화풍 설명의 눈·볼·머리카락 말 때문에 인물 없는 장면에 엉뚱한 소녀 얼굴이 크게 나옴 → 풍경 장면은 그 말을 빼고 배경 그림으로
    scenery = re.sub(r"large detailed glossy eyes[^,]*, soft blush on cheeks, very fine detailed flowing hair strands with soft shading, ", "", style)
    scenery = scenery.replace("dreamy shallow depth of field with bokeh light particles, soft diffused lighting, delicate pastel color grading",
                              "rich saturated colors, strong contrast, dramatic cinematic lighting that matches the mood of the scene")
    no_face = ("Anime background art, environment and scenery illustration. No main character, no close-up face, no portrait, no girl in the foreground; "
               "any people are small figures in the scene. ")
    # 같은 인물이 한 그림에 두 번 나오는 일(배경 복제·시트처럼 여러 모습)이 잦아서 사람 수를 못 박음
    SOLO = "Solo: exactly one person in the whole image, no other people, nobody in the background, no reflections, not a character sheet, single view only. "
    GROUP = "Exactly {} people in the image, each appears only once, no duplicates, no extra copies in the background, not a character sheet. "
    NUM = {2: "two", 3: "three", 4: "four", 5: "five"}
    BG = "Detailed background environment that matches the scene, NOT a white or plain background (ignore the white background of the reference sheets). "
    if cmd == "job":
        items = []
        for cid, who, desc, _ in CUTS:
            if only and cid not in only:
                continue
            looks = "; ".join(f"{nm} (the character from reference image {k + 1}): {chars[nm]['look']}" for k, nm in enumerate(who))
            items.append({"id": cid, "width": 1024, "height": 576, "seed": 300 + int(cid[1:]),
                          "refs": [os.path.join(HERE, chars[nm][face]) for nm in who],
                          "prompt": f"{style if (who or not anime) else scenery}, medieval post-apocalyptic science fantasy {kind}. "
                                    + (f"Characters: {looks}. Each person has exactly two arms and two legs. " + (SOLO if len(who) == 1 else GROUP.format(NUM[len(who)])) if looks
                                       else no_face if anime else "")
                                    + f"Scene: {desc}. " + (BG if who else "") + "Cinematic composition, full-bleed image, no border, no frame, no paper edges. No speech bubbles, no text, no letters."})
        os.makedirs(folder, exist_ok=True)
        json.dump({"items": items}, open(os.path.join(folder, "job.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(len(items), "cuts")
    elif cmd == "project":
        story = STORY
        for cid, _, _, cap in CUTS:
            img = next((os.path.join(folder, cid + e) for e in (".png", ".jpg") if os.path.exists(os.path.join(folder, cid + e))), os.path.join(folder, cid + ".png"))
            story = story.replace("{" + cid + "}", f"[사진: {img} | {cap} | AI 생성 그림 (FLUX.2 klein) | ]")
        proj = {"ver": 7, "category": "장문", "genre": "[이야기] SF·디스토피아", "topic": "두 번째 새벽", "title": TITLE,
                "story": story, "sources": [], "notes": "창작 연재 《두 번째 새벽》 3화", "autophoto": False, "img_source": "그림: 애니 일러스트" if anime else "그림: 옛날 만화책",
                "trans_fix": {"ja": {"第二の夜明け": "二度目の夜明け", "二番目の夜明け": "二度目の夜明け", "2番目の夜明け": "二度目の夜明け", "セカンド・ドーン": "二度目の夜明け", "セカンドドーン": "二度目の夜明け"},
                              "en": {"The Second Daybreak": "The Second Dawn"}},   # 연재 이름은 기획.md 에 정한 대로 고정
                "cast": [{"name": nm, "look": c["look"], "look_ko": c["look_ko"], "voice": c.get("voice"),
                          **({"sheet": os.path.join(HERE, c[face])} if c.get(face) else {})} for nm, c in chars.items()],
                "dialogue": [{"text": t, "who": w} for t, w in DIALOGUE],
                "settings": {"format": "롱폼 가로(1920×1080)", "narration": "on",   # 새 서버 기본값(나레이션 꺼짐·스크롤형) 대신
                             "layout": "자막형(큰 제목+사진+자막)", "img_fill": "전체 화면(글자가 사진 위에)",
                             "img_motion": "영상처럼(확대·이동·전환)",
                             "head_show": "안 보임(제목 카드만)", "sub_split": "한 줄씩(문장·쉼표로 나눠 차례로)", "img_label": "off",   # 연재 화면 규칙
                             "narr_voice": "Supertonic M2 (남성, 무료 로컬) [supertonic:M2]"}}
        out = os.path.join(HERE, "3화_숲의눈.json")
        json.dump(proj, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(out, len(story), "chars")


if __name__ == "__main__":
    main()
