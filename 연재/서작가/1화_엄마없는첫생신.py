"""《엄마의 텃밭》 1화 '엄마 없는 첫 생신' — 대본 + 컷별 그림 계획 (서작가 에세이 각색)
python 연재/서작가/1화_엄마없는첫생신.py job <저장폴더>   → 그림 주문서(klein_worker 용) job.json
python 연재/서작가/1화_엄마없는첫생신.py project <그림폴더> → 프로젝트 파일(render_project 용) 연재/서작가/1화_엄마없는첫생신.json
  영상은 render_project.py <프로젝트> --대본그대로 (에세이라 오프닝·대본을 프로그램이 고쳐 쓰지 않게)
대본의 {컷번호} 자리에 그 컷 그림이 들어감. chars = 그 컷에 나오는 인물(캐릭터 시트를 기준 그림으로 넣음)
원문 문장은 그대로 살리고(존댓말로만 바꿈), 그 사이 장면·어린 시절 추억은 각색으로 덧붙임"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TITLE = "엄마의 텃밭 1화 - 엄마 없는 첫 생신"

# 대사 → 말하는 인물 (그 인물 목소리로 읽음, 목소리는 등장인물.json 의 voice. 나레이션은 남자 성우 2)
DIALOGUE = [
    ("엄마, 저 왔어요.", "나"),
    ("왔구나. 길 많이 막혔지? 어서 들어와.", "오빠"),
    ("너 그거 기억나? 엄마 생신날, 우리가 미역국 끓인다고 부엌 다 태울 뻔한 거.", "언니"),
    ("아이고, 우리 딸들이 끓인 미역국이 세상에서 제일 맛있네.", "젊은 엄마"),
    ("엄마, 나도 업어 줘.", "어린 나"),
    ("엄마가 심어 놓은 감나무다. 올해도 잊지 않고 열렸다.", "오빠"),
    ("엄마, 나 저 꼭대기 감도 딸 수 있어!", "어린 오빠"),
    ("얼른 내려와, 이 녀석아! 감보다 네가 더 귀하다.", "젊은 엄마"),
    ("막내야, 불 좀 봐라. 시래기는 은근한 불에 오래 삶아야 맛있단다.", "엄마"),
    ("엄마... 보고 싶어요.", "나"),
    ("울어도 괜찮아. 엄마도 오늘은 여기 와 계실 거야.", "언니"),
    ("엄마, 생신 축하드려요.", "나"),
]

# (컷번호, 나오는 인물, 그림 설명(영어), 화면 설명(한국어))
CUTS = [
    ("c01", [], "close-up of crackling firewood burning inside a traditional Korean agungi: a low arched fire opening at the bottom of a whitewashed clay-and-stone kitchen wall, with a big black iron cauldron (gamasot) set into the clay stove above it, glowing orange flames and embers, dark warm surroundings, evening", "타닥타닥 타오르는 아궁이 장작불"),
    ("c02", ["나"], "the woman crouching alone in an old earthen-floored Korean kitchen in front of a traditional Korean agungi: a low arched fire opening at the bottom of a whitewashed clay-and-stone kitchen wall, with a big black iron cauldron (gamasot) set into the clay stove above it, orange firelight on her calm, quietly sad face, looking into the flames, evening", "장작불을 바라보는 나"),
    ("c03", [], "full-frame warm orange and gold flames and sparks filling the whole image, within the flames the faint translucent gentle smiling face of an elderly Korean grandmother with white hair in a bun, dreamy, no empty white background", "불꽃 속에 아른거리는 엄마의 얼굴"),
    ("c04", [], "an old traditional Korean countryside house with a tiled roof in autumn, a persimmon tree heavy with orange fruit beside it, golden afternoon light", "가을의 고향집"),
    ("c05", ["나"], "the woman sitting by a bus window looking out at autumn rice fields and mountains, quiet thoughtful face, holding a small bag on her lap", "고향으로 가는 길"),
    ("c06", [], "a small framed photo of a smiling elderly Korean grandmother standing on a wooden shelf beside a small vase of pink cosmos flowers, autumn sunlight through a window, no calendar, no writing", "달력에 동그라미 친 엄마의 생신"),
    ("c07", ["엄마", "나", "언니", "오빠"], "last year's birthday in a traditional Korean room: the elderly grandmother sitting on the floor at a low table blowing out candles on a small cake, exactly four people in the room (the grandmother, the petite woman, the plump woman, the big man without his hat), all clapping and smiling, no children, warm lamp light", "작년 생신, 촛불을 끄던 엄마"),
    ("c08", ["나", "오빠"], "the woman arriving at the gate of an old Korean countryside house, her big tall older brother in a straw hat greeting her with a gentle smile", "대문 앞에서 맞아 주는 오빠"),
    ("c09", ["언니"], "the plump cheerful woman laughing and carrying a big plastic container of side dishes into a traditional Korean house yard, other relatives and children in the background", "반찬통을 들고 들어오는 언니"),
    ("c10", [], "a warm traditional Korean room (ondol floor) full of family members sitting around a low wooden table with many dishes, children playing, cozy evening light", "오랜만에 한자리에 모인 친정 식구들"),
    ("c11", [], "a framed photograph of a smiling old Korean grandmother placed on a low table with a small birthday cake, a bowl of seaweed soup and autumn fruits in front of it", "엄마 사진 앞에 차린 생신상"),
    ("c12", ["나"], "medium close-up of one single woman alone, sitting on the floor and gently touching a framed photograph of her elderly mother standing on a low table, eyes glistening, soft lamp light, only one person in the image", "엄마 사진을 쓰다듬는 나"),
    ("c13", ["언니", "나"], "the plump cheerful woman and the petite quiet woman sitting side by side on the floor, the cheerful one laughing and telling a story with hand gestures, the quiet one smiling", "이야기꽃을 피우는 언니와 나"),
    ("c14", ["어린 언니", "어린 나"], "an old 1980s rural Korean kitchen (bueok) with an earthen floor, a clay stove with a black iron cauldron, firewood, no modern appliances, two little sisters cooking seaweed soup at dawn, steam and a little smoke, the younger one holding a ladle nervously", "엄마 생신날 미역국을 끓이는 어린 자매"),
    ("c15", ["젊은 엄마"], "the mother in a white towel headscarf sitting at a small low table eating a bowl of soup with a big happy smile, morning light in an old Korean room", "탄 미역국을 맛있게 먹는 젊은 엄마"),
    ("c16", [], "an old open photo album with faded family photographs, pages slowly turning, soft warm light, nostalgic", "책장처럼 넘어가는 옛 사진첩"),
    ("c17", ["젊은 엄마", "어린 나"], "side view: the mother in a white towel headscarf bent slightly forward walking along a country dirt road at sunset, giving her small daughter a piggyback ride, the little girl riding on the mother's back with her arms around the mother's neck and her feet off the ground, the mother's hands holding the girl's legs behind her, golden rice fields", "엄마 등에 업혀 가던 저녁 길"),
    ("c18", ["젊은 엄마"], "a rainy afternoon in the 1980s, the mother in a white towel headscarf standing in front of a small country school gate holding a big umbrella and a second folded umbrella, her clothes wet", "비 오는 날 학교 앞에서 기다리던 엄마"),
    ("c19", ["젊은 엄마"], "the mother rolling kimbap on a wooden board at dawn by a dim lamp in an old Korean kitchen, lunch boxes lined up", "새벽에 소풍 김밥을 싸는 엄마"),
    ("c20", ["어린 오빠", "어린 언니", "어린 나"], "three Korean children in 1980s clothes running happily along a narrow path between green rice paddies with school bags", "논둑길을 뛰어가는 어린 삼 남매"),
    ("c21", [], "a small vegetable garden behind an old Korean house in autumn, rows of tall elongated Korean napa cabbages (baechu) and Korean white radishes growing in the soil with only their green leafy tops and the upper white part showing, soft sunlight", "무럭무럭 자란 텃밭의 배추와 무"),
    ("c22", ["나"], "the woman crouching in the vegetable garden, touching a big napa cabbage leaf gently with her hand, thoughtful", "배추 잎을 만져 보는 나"),
    ("c23", ["젊은 엄마"], "the mother in a white towel headscarf squatting low in a vegetable garden with both feet flat on the ground, tying a tall napa cabbage with straw rope, soil on her hands, exactly two legs and two feet, side view", "배추를 묶던 엄마"),
    ("c24", [], "kimchi-making day in a 1980s Korean yard, huge piles of salted cabbages in big rubber basins, women working together, red pepper paste", "온 동네가 모이던 김장날"),
    ("c25", [], "a small hillside orchard field in autumn with no people: persimmon trees heavy with orange persimmons, apple trees with red apples, a pomegranate tree with cracked-open fruit showing red seeds hanging on its branches, the tiled roof of a traditional Korean house far in the background", "뒷밭의 단감·사과·석류"),
    ("c26", [], "botanical close-up of ripe pomegranates hanging on a branch, one split open showing glistening red seeds, autumn sunlight, realistic fruit", "탐스럽게 입을 벌린 석류"),
    ("c27", ["오빠"], "the big tall man in a straw hat standing under a persimmon tree, holding a basket full of orange persimmons, proud quiet smile", "단감 바구니를 든 오빠"),
    ("c28", ["어린 오빠"], "a mischievous Korean boy in a black school uniform climbing high up a persimmon tree, reaching for an orange persimmon at the top", "감나무 꼭대기에 올라간 어린 오빠"),
    ("c29", ["젊은 엄마"], "one single woman alone: the mother in a white towel headscarf standing under a tall persimmon tree, looking up and shouting with a worried angry face, one hand on her hip and the other hand raised, only one person in the image", "놀라 소리치는 젊은 엄마"),
    ("c30", [], "the outside kitchen of a lower annex room of an old Korean house: a traditional Korean agungi (a low arched fire opening at the bottom of a whitewashed clay-and-stone kitchen wall, with a big black iron cauldron set into the clay stove above it), the cauldron steaming, firewood stacked nearby, autumn evening", "아랫방 아궁이와 가마솥"),
    ("c31", [], "close-up of dark green-brown dried radish greens (siraegi) boiling in a big black iron cauldron set into a clay stove, thick white steam rising, warm firelight from below, realistic food", "시래기를 삶는 가마솥"),
    ("c32", [], "outside view: many bundles of green radish leaves (only the leaves and stems, no radish roots) tied with straw rope and hanging in a row to dry from a pole under the tiled eaves of an old Korean house, late autumn sunlight, realistic", "처마 밑에 걸어 말리던 시래기"),
    ("c33", ["엄마"], "the elderly grandmother sitting on a low stool on an earthen kitchen floor in front of a traditional Korean agungi (a low arched fire opening at the bottom of a whitewashed clay-and-stone kitchen wall, with a big black iron cauldron set into the clay stove above it), feeding a log into the fire, gentle smile, warm firelight", "아궁이 불을 보던 엄마"),
    ("c34", ["어린 나", "젊은 엄마"], "winter night, the small girl and her mother sitting close together on low stools in front of a traditional Korean agungi (a low arched fire opening at the bottom of a whitewashed clay-and-stone kitchen wall, with a big black iron cauldron set into the clay stove above it), the mother handing her a roasted sweet potato, warm glow", "아궁이 앞에서 군고구마를 건네주던 엄마"),
    ("c35", [], "close-up of the arched fire opening of a traditional Korean agungi (a low arched fire opening at the bottom of a whitewashed clay-and-stone kitchen wall, with a big black iron cauldron set into the clay stove above it): glowing embers and burning firewood, a few sparks flying up, dark warm night surroundings", "타닥타닥 튀는 불티"),
    ("c36", ["나"], "medium close-up of the woman alone sitting in front of a traditional Korean agungi (a low arched fire opening at the bottom of a whitewashed clay-and-stone kitchen wall, with a big black iron cauldron set into the clay stove above it) at night, a single tear running down her cheek, orange firelight on her face", "끝내 흐르는 눈물"),
    ("c37", ["언니", "나"], "the plump woman gently putting her arm around the small quiet woman's shoulders as they sit side by side on low stools in front of a traditional Korean agungi (a low arched fire opening at the bottom of a whitewashed clay-and-stone kitchen wall, with a big black iron cauldron set into the clay stove above it) at night, both with teary eyes and gentle sad smiles, not laughing", "어깨를 감싸 주는 언니"),
    ("c38", ["오빠", "언니", "나"], "night scene: the big man (no hat), the plump woman and the small woman sitting side by side on the wooden porch (maru) of a traditional Korean house, looking up quietly at the starry night sky, warm lamp light from the room behind them, calm and moved expressions", "마루에 나란히 앉은 삼 남매"),
    ("c39", [], "a starry night sky over a quiet traditional Korean hanok house with a curved tiled roof in the countryside, soft white smoke rising from the low chimney, no people, realistic building", "별이 뜬 고향집의 밤"),
    ("c40", [], "an empty vegetable garden with rows of napa cabbages and a persimmon tree at dawn, no people at all, soft pink and gold morning light, a gentle peaceful mood", "엄마의 손길이 머물던 텃밭의 새벽"),
]

STORY = """{c01}

엄마 없는 첫 생신이었습니다. 엄마가 먼 하늘나라로 떠나시고 처음 맞은 그날, 우리 형제들은 아궁이 앞에서 엄마를 다시 만났습니다.

{c02}

타닥타닥, 장작불이 타오르는 소리를 듣고 있으면 지금도 그 밤이 떠오릅니다. 쉰을 훌쩍 넘긴 막내딸은 그 불 앞에서 오래도록 앉아 있었습니다.

{c03}

불꽃 속에서 엄마가 웃고 계신 것 같았습니다. 손을 뻗으면 닿을 것만 같았습니다.

엄마가 안 계신 그날이, 어떻게 엄마와 가장 가까운 날이 되었을까요.

## 1. 엄마 없는 첫 생신

{c04}

엄마가 먼 하늘나라로 떠나시고, 처음으로 맞이한 생신이었습니다.

{c05}

고향 가는 버스 창밖으로 누렇게 익은 들판이 지나갔습니다. 해마다 이맘때면 엄마는 전화를 걸어 오셨습니다. 바쁘면 안 와도 된다고, 그냥 목소리만 들으면 된다고요. 그래 놓고는 대문 앞에 나와 하루 종일 기다리셨지요. 올해는 그 전화가 오지 않았습니다.

{c06}

달력에 빨갛게 동그라미를 친 날. 엄마의 생신이었습니다. 엄마가 계시지 않아도, 그날은 여전히 엄마의 날이었습니다.

{c07}

꼭 일 년 전, 바로 그 방에서 엄마는 케이크 촛불을 끄셨습니다. 숨이 차서 세 번이나 나누어 부셨지요. 우리는 손뼉을 치며 웃었고, 엄마는 쑥스럽게 손사래를 치셨습니다. 그러고는 내년에도 이렇게 다 같이 모이자고 하셨습니다. 그 약속을 지키러, 우리는 엄마 없이 모였습니다.

{c08}

대문을 들어서는데, 엄마 대신 오빠가 마당에 서 있었습니다.

"엄마, 저 왔어요."

저도 모르게 그 말이 먼저 나왔습니다. 오빠는 못 들은 척 웃으며 제 가방을 받아 들었습니다. 그새 오빠 머리에도 흰 눈이 내려앉아 있었습니다.

"왔구나. 길 많이 막혔지? 어서 들어와."

{c09}

곧이어 언니가 커다란 반찬통을 들고 들어왔습니다. 올케와 조카들, 사위들까지 하나둘 모여들었습니다.

{c10}

오랜만에 친정 식구들이 한자리에 모였습니다. 작은 방이 금세 사람으로 가득 찼습니다. 아이들 웃음소리가 마당까지 흘러넘쳤습니다. 엄마가 계셨다면 얼마나 좋아하셨을까요. 엄마는 식구들이 모이는 날이면 며칠 전부터 장을 보고, 전을 부치고, 이불을 볕에 내다 말리셨습니다. 그 많은 이불이 다 필요하냐고 물으면, 자고 가라는 뜻이라고 웃으셨지요.

{c11}

상 한가운데에는 엄마 사진을 놓았습니다. 사진 앞에는 작은 케이크와 미역국 한 그릇, 그리고 오빠가 딴 과일을 올렸습니다.

{c12}

사진 속 엄마는 늘 그렇듯 웃고 계셨습니다. 그 웃음을 보는데 이상하게 목이 메었습니다. 그런데 그 미역국 한 그릇이, 잊고 있던 어린 날의 이야기를 불러냈습니다. 잠시 뒤, 그 이야기를 들려 드릴게요.

## 2. 책장을 넘기듯

{c13}

자연스레 엄마와의 추억을 되살리며 이야기꽃을 피웠습니다. 먼저 말을 꺼낸 건 언니였습니다.

"너 그거 기억나? 엄마 생신날, 우리가 미역국 끓인다고 부엌 다 태울 뻔한 거."

{c14}

열 살 언니와 일곱 살 저는, 엄마 몰래 새벽에 일어나 미역국을 끓였습니다. 미역을 너무 많이 불려 솥이 넘쳤고, 간장을 붓다 보니 국은 시커멓게 변했습니다. 부엌에는 탄 냄새가 가득했지요.

{c15}

그런데 엄마는 그 국을 한 숟가락도 남기지 않고 다 드셨습니다.

"아이고, 우리 딸들이 끓인 미역국이 세상에서 제일 맛있네."

그 말에 우리는 정말 맛있는 줄 알았습니다. 어른이 되어서야 알았습니다. 그 국이 얼마나 짜고 썼을지를요.

{c16}

이야기꽃을 피우다 보니, 우리들의 어린 시절이 책장을 한 장 한 장 넘기듯 생생하게 펼쳐졌습니다.

{c17}

장에 갔다 오던 저녁, 다리가 아프다고 떼를 쓰던 저를 엄마는 말없이 업어 주셨습니다. 머리에는 장 본 보따리를 이고, 등에는 저를 업고 십 리 길을 걸으셨지요.

"엄마, 나도 업어 줘."

그 말 한마디에 엄마는 한 번도 싫다고 하신 적이 없었습니다. 엄마의 등은 언제나 따뜻했습니다. 엄마의 등에서는 늘 햇볕 냄새와 흙냄새가 났습니다. 저는 그 냄새를 맡으며 스르르 잠이 들곤 했습니다.

{c18}

비가 오는 날이면 학교 앞에는 늘 엄마가 서 계셨습니다. 밭일을 하다 말고 달려오셨는지, 바짓단에는 흙이 묻어 있었지요. 우산 하나는 우리에게 씌워 주고, 엄마는 비를 맞으며 걸으셨습니다. 그때는 그게 당연한 줄만 알았습니다.

{c19}

소풍날이면 엄마는 해도 뜨기 전에 일어나 김밥을 마셨습니다. 우리 셋 도시락을 다 싸고 나면, 엄마 몫은 김밥 꽁지 몇 개뿐이었습니다. 엄마는 그게 제일 맛있다고 하셨습니다.

{c20}

우리 삼 남매는 그 도시락을 들고 논둑길을 달렸습니다. 그 길 끝에는 늘 엄마가 서 계실 것만 같았습니다. 그리고 그 길이 시작되는 곳, 집 뒤에는 엄마의 텃밭이 있었습니다. 바로 다음 이야기입니다.

## 3. 엄마의 텃밭

{c21}

고스란히 우리를 지켜 주고 있는 텃밭에는 배추와 무가 무럭무럭 자라고 있었습니다.

{c22}

배추 잎을 가만히 만져 보았습니다. 서늘하고 단단했습니다. 엄마가 떠나신 뒤에도 밭은 쉬지 않았습니다. 오빠가 엄마가 하던 대로 씨를 뿌리고 물을 주었다고 했습니다. 이랑의 간격도, 배추를 심는 날짜도 엄마가 하던 그대로였습니다. 엄마는 떠나셨지만, 엄마가 가르쳐 준 것들은 이렇게 밭에 남아 있었습니다.

{c23}

엄마는 이맘때면 늘 밭에 엎드려 계셨습니다. 배추가 속이 차도록 짚으로 하나하나 묶어 주셨지요. 손톱 밑에는 늘 흙이 끼어 있었습니다. 어린 저는 그 손이 부끄러웠던 적도 있었습니다. 지금은 그 손을 한 번만 더 잡아 보고 싶습니다.

{c24}

김장하는 날이면 온 동네 아주머니들이 우리 마당에 모였습니다. 엄마는 절인 배추에 양념을 버무려, 제일 맛있는 속잎을 돌돌 말아 우리 입에 넣어 주셨습니다. 맵다고 울면서도 우리는 또 입을 벌렸지요. 그런데 텃밭보다 더 놀라운 것은 뒷밭에 있었습니다. 곧 보여 드릴게요.

## 4. 뒷밭의 감나무

{c25}

뒷밭에는 오빠가 정성껏 농사지은 단감과 사과, 석류가 탐스럽게 입을 벌리고 있었습니다.

{c26}

빨간 알이 촘촘히 박힌 석류는 꼭 웃고 있는 입 같았습니다. 엄마도 저렇게 웃으셨는데 싶었습니다. 사과는 볕을 받아 발갛게 익었고, 단감은 가지가 휘도록 매달려 있었습니다. 오빠는 그 나무들을 자식처럼 돌봤다고 했습니다. 엄마가 아끼던 나무였으니까요.

{c27}

오빠가 단감을 한 바구니 따 와서 내밀었습니다.

"엄마가 심어 놓은 감나무다. 올해도 잊지 않고 열렸다."

말수 적은 오빠의 그 한마디에 모두 잠시 말이 없었습니다. 그 감나무에는 오빠의 어린 시절 이야기도 걸려 있었습니다.

{c28}

열세 살 오빠는 동네에서 나무를 제일 잘 탔습니다. 어느 가을, 오빠는 감나무 꼭대기까지 올라가 소리쳤습니다.

"엄마, 나 저 꼭대기 감도 딸 수 있어!"

{c29}

엄마는 얼굴이 하얗게 질려 뛰어나오셨습니다.

"얼른 내려와, 이 녀석아! 감보다 네가 더 귀하다."

그날 오빠는 감 대신 엄마에게 꿀밤을 실컷 맞았습니다. 그래도 그날 저녁상에는 오빠가 딴 홍시가 올라와 있었지요. 그 이야기에 우리는 배를 잡고 웃었습니다. 하지만 그 웃음은 오래가지 못했습니다. 이어서 아랫방 아궁이 이야기를 들려 드릴게요.

## 5. 아랫방 아궁이

{c30}

아랫방 아궁이에는 시래기를 삶아 내는 장작불이 활활 타오르고 있었습니다.

{c31}

가마솥에서 하얀 김이 피어올랐습니다. 구수한 시래기 냄새가 마당 가득 퍼졌습니다. 그 냄새를 맡자마자 우리는 누가 먼저랄 것도 없이 아궁이 앞으로 모여들었습니다. 어릴 적 그랬던 것처럼요.

{c32}

가을이면 엄마는 무청을 엮어 처마 밑에 줄줄이 걸어 두셨습니다. 찬 바람에 바싹 마른 시래기는 겨우내 우리 식구의 국이 되고, 나물이 되었습니다. 엄마가 하던 그 일을, 이제는 오빠가 하고 있었습니다.

{c33}

아궁이 앞에 쪼그리고 앉아 불을 보시던 엄마의 모습이 떠올랐습니다. 엄마는 제가 옆에 앉으면 늘 이렇게 말씀하셨지요.

"막내야, 불 좀 봐라. 시래기는 은근한 불에 오래 삶아야 맛있단다."

{c34}

겨울밤이면 엄마는 아궁이 잿불에 고구마를 묻어 두셨습니다. 껍질이 까맣게 탄 고구마를 호호 불어 제 손에 쥐여 주시던 엄마. 그 고구마보다 엄마의 손이 더 따뜻했습니다.

{c35}

타닥타닥 타오르는 장작불을 바라보다가, 문득 엄마 생각이 났습니다.

그리운 엄마의 모습이 불꽃 속에서 아른거리는 듯했습니다. 그리고 그다음 순간, 꾹 참아 왔던 것이 무너져 내렸습니다.

## 6. 끝내 흘린 눈물

{c36}

가족들과 함께 웃으며 추억을 나누다가도, 불쑥불쑥 밀려오는 그리움에 끝내 눈물이 났습니다.

"엄마... 보고 싶어요."

엄마가 떠나시던 날에도 이렇게 울지는 않았습니다. 장례를 치르고, 짐을 정리하고, 정신없이 하루하루를 보내느라 울 틈이 없었습니다. 그 눈물이 이제야, 엄마의 아궁이 앞에서 터져 나왔습니다.

{c37}

언니가 다가와 말없이 제 어깨를 감싸 안았습니다.

"울어도 괜찮아. 엄마도 오늘은 여기 와 계실 거야."

언니의 눈가도 젖어 있었습니다. 조카들은 영문도 모른 채 고모와 이모를 번갈아 바라보았습니다. 부엌에서 설거지를 하던 오빠의 등도 조금 흔들리는 것 같았습니다. 그날 밤, 우리는 마루에 나란히 앉았습니다. 이제 마지막 이야기입니다.

## 7. 엄마는 여전히

{c38}

엄마는 떠나셨지만, 엄마의 손길이 머물던 텃밭에도, 아궁이의 장작불에도, 우리 형제들의 이야기 속에도 엄마는 여전히 살아 계셨습니다.

{c39}

밤하늘에 별이 가득했습니다. 저는 아무도 모르게 작은 목소리로 말했습니다.

"엄마, 생신 축하드려요."

어디선가 엄마가 웃으며 대답하시는 것만 같았습니다. 고맙다고, 다들 와 줘서 고맙다고요. 오빠도 언니도 말없이 하늘만 올려다보았습니다. 아마 같은 목소리를 듣고 있었을 겁니다.

{c40}

그렇게 우리는 엄마가 없는 첫 생신을 맞이했지만, 어쩌면 그날만큼은 엄마와 가장 가까이 함께 있었는지도 모릅니다.

여러분에게도 불꽃처럼 문득 떠오르는 그리운 얼굴이 있으신가요. 서작가의 에세이 《엄마의 텃밭》은 이 채널에서 계속 이어집니다."""


def main():
    cmd, folder = sys.argv[1], sys.argv[2]
    chars = {c["name"]: c for c in json.load(open(os.path.join(HERE, "등장인물.json"), encoding="utf-8"))["chars"]}
    src = open(os.path.join(HERE, "..", "..", "shorts_novel_maker_supertonic.py"), encoding="utf-8").read()
    style = re.search(r'"파스텔 감성 일러스트": "([^"]+)"', src).group(1)
    if cmd == "job":
        items = []
        for cid, who, desc, _ in CUTS:
            looks = "; ".join(f"person {k + 1} (the character from reference image {k + 1}): {chars[nm]['look']}" for k, nm in enumerate(who))   # 한글 이름은 그림에 글자로 나올 수 있어 번호로
            st = style if who else style.replace("gentle rosy cheeks, simple cute faces, ", "")
            items.append({"id": cid, "width": 1024, "height": 576, "seed": 100 + int(cid[1:]),
                          "refs": [os.path.join(HERE, chars[nm]["face"]) for nm in who],
                          "prompt": f"{st}, Korean countryside family essay illustration. "
                                    + (f"Characters: {looks}. Each person appears only once, exactly two arms and two legs. " if looks else "")
                                    + ("" if who else "No people. ")
                                    + f"Scene: {desc}. Objects, food, fruit, steam and buildings have no faces. Cinematic composition, full-bleed image, no border, no frame, no paper edges. No speech bubbles, no text, no letters."})
        os.makedirs(folder, exist_ok=True)
        json.dump({"items": items}, open(os.path.join(folder, "job.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(len(items), "cuts")
    elif cmd == "project":
        story = STORY
        for cid, _, _, cap in CUTS:
            story = story.replace("{" + cid + "}", f"[사진: {os.path.join(folder, cid + '.png')} | {cap} | AI 생성 그림 (FLUX.2 klein) | ]")
        proj = {"ver": 7, "category": "장문", "genre": "[이야기] 에세이", "topic": "엄마의 텃밭", "title": TITLE,
                "story": story, "sources": [], "notes": "서작가 에세이 연재 《엄마의 텃밭》 1화", "autophoto": False, "img_source": "그림: 파스텔 감성",
                "cast": [{"name": nm, "look": c["look"], "look_ko": c["look_ko"], "voice": c.get("voice"),
                          **({"sheet": os.path.join(HERE, c["face"])} if c.get("face") else {})} for nm, c in chars.items()],
                "dialogue": [{"text": t, "who": w} for t, w in DIALOGUE],
                "settings": {"format": "롱폼 가로(1920×1080)", "narration": "on",   # 새 PC·서버 기본값(나레이션 꺼짐·스크롤형) 대신 장문 설정 그대로
                             "layout": "자막형(큰 제목+사진+자막)", "img_fill": "전체 화면(글자가 사진 위에)",
                             "img_motion": "영상처럼(확대·이동·전환)", "fps": "24", "reveal_hit": "off", "reveal_fx": "off",
                             "head_show": "안 보임(제목 카드만)", "sub_split": "한 줄씩(문장·쉼표로 나눠 차례로)", "img_label": "off",   # 규칙: 위 큰 제목·장면 설명 없이, 자막은 한 줄씩
                             "narr_voice": "Supertonic M2 (남성, 무료 로컬) [supertonic:M2]",   # 규칙(사용자 결정): 연재 나레이션은 남자 성우 2. '나'의 대사는 '나' 목소리 그대로(dialogue)
                             "st_emotion": "차분"}}   # 샘플로 고른 빠르기 그대로 (감정별 빠르기 조절 없이)
        out = os.path.join(HERE, "1화_엄마없는첫생신.json")
        json.dump(proj, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(out, len(story), "chars")


if __name__ == "__main__":
    main()
