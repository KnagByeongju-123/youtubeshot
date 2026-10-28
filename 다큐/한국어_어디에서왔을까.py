"""과학 다큐 '한국어는 어디에서 왔을까' — 대본 + 컷별 그림 계획
python 다큐/한국어_어디에서왔을까.py job <저장폴더>   → 그림 주문서(klein_worker 용) job.json
python 다큐/한국어_어디에서왔을까.py project <그림폴더> → 프로젝트 파일(render_project 용) 다큐/한국어_어디에서왔을까.json
python 다큐/한국어_어디에서왔을까.py txt <파일>        → 사용자 확인용 대본(그림 자리는 [그림: 설명])
  영상은 render_project.py <프로젝트> --대본그대로
사실 근거(기원은 모두 가설·논쟁으로 말함): 람스테트(핀란드, 1920년대 일본 주재 외교관, 한국어 알타이 기원설),
  알타이 가설의 근거(어순·교착·모음조화·두음 제약)와 비판(기초 낱말·규칙적 소리 대응 부족), 계림유사(1103 송나라 손목, 天曰漢捺),
  향가(삼국유사 14수·균여전 11수), 훈민정음(1443 창제·1446 반포), 중세 국어 'ᄡᆞᆯ'(찹쌀·좁쌀·햅쌀), ㅎ 끝소리 낱말(암탉·수캐·안팎·살코기),
  삼국사기 지리지 고구려 땅이름의 숫자(密=3·于次=5·難隱=7·德=10, 일본어 mi·itsu·nana·tō 와 닮음, 해석 논쟁),
  롭비츠 연구팀 2021 Nature 트랜스유라시아 농경 확산 가설(랴오허강 유역 기장 농부, 약 9천 년 전)과 반론, 한국어족(한국어·제주어)"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TITLE = "한국어는 어디에서 왔을까"
GENRE = "고대 인류"
STYLE = ("scientific documentary illustration, detailed digital painting like a National Geographic or science magazine illustration, "
         "natural realistic colors, clear readable composition, soft cinematic lighting, high detail")
PEOPLE = ("ancient East Asian people with black hair wearing simple period clothing, a mixed group of men and women, "
          "each person with exactly two arms and two legs, natural anatomy")   # 옛 사람이 나오는 컷에 붙임 (팔다리 수 규칙)
NOW = "modern-day people in contemporary clothing, each person with exactly two arms and two legs, natural anatomy"   # 오늘날 사람 컷

# (컷번호, 그림 설명(영어), 화면 설명(한국어), 사람이 나오는 컷인지: True=옛 사람, "now"=오늘날 사람)
CUTS = [
    ("c01", "people chatting in small groups on the grassy riverside park of the Han River in Seoul at dusk, a long bridge with blurred lights in the background, warm evening light", "오늘도 한국어로 말하는 사람들", "now"),
    ("c02", "a lone old tree standing on a wide open plain at sunrise, no other trees around it, symbolic and calm", "친척이 보이지 않는 외로운 언어", False),
    ("c03", "a misty sunrise seen from a mountain peak in Korea, endless layers of blue mountain ridges fading into the distance, golden light, no people", "한국어는 어디에서 왔을까", False),
    ("c04", "a quiet 1920s study room with a tall window: a wooden desk with a fountain pen, an ink bottle, stacks of closed old books and a globe, warm lamp light, no people", "1920년대 람스테트의 서재", False),
    ("c05", "a vast steppe landscape of Mongolia and Central Asia with rolling grassland, distant mountains and a few nomad felt tents, golden light", "알타이 산맥에서 이어진 초원", False),
    ("c06", "three groups of people from different Asian steppe and forest cultures in traditional clothing standing apart on a grassland, talking among themselves, distant mountains", "닮은 말을 쓰는 이웃들", True),
    ("c07", "a large tree with many branches drawn as a glowing family tree shape over a soft gradient background, some branches fading away, concept art, no text", "언어의 족보", False),
    ("c08", "two separate old trees standing side by side, their branches intertwined and touching in the middle, meadow, soft light, symbolic", "닮았다고 친척은 아니다", False),
    ("c09", "a classroom in the 1980s Korea seen from the back of the room: wooden desks, students' backs, a blackboard with only chalk lines and simple shapes, warm afternoon light", "교과서 속 알타이어족", "now"),
    ("c10", "a Song dynasty Chinese envoy seen from behind wearing a red official robe and a black hat with two long thin horizontal wings sticking out sideways, walking into the courtyard of a Goryeo palace with attendants, 12th century", "1103년 고려에 온 송나라 사신", True),
    ("c11", "close-up of a calligraphy brush, an ink stone and a sheet of paper with faint blurred brush strokes on a wooden desk, candle light", "고려 말을 받아 적다", False),
    ("c12", "a wide clear blue sky over Korean mountains and rooftops of an old Goryeo town, bright day", "하늘을 이르는 말", False),
    ("c13", "a Silla Buddhist monk with a cleanly shaved head in gray robes standing alone on a hill under a moonlit night sky, singing with his eyes closed and palms together, ancient Gyeongju tiled rooftops below", "신라 사람들의 노래, 향가", True),
    ("c14", "King Sejong's era scholars in Joseon dynasty robes seen from behind, working at low wooden tables in a palace hall, brushes and paper, warm light", "1443년, 훈민정음", True),
    ("c15", "a bowl of glistening cooked white rice and small heaps of sticky rice, millet and new rice grains on a wooden table, warm kitchen light", "찹쌀·좁쌀·햅쌀", False),
    ("c16", "golden rice paddies at harvest time in the Korean countryside, mountains behind, warm evening light", "말 속에 남은 옛 소리", False),
    ("c17", "a brown hen with a very small comb sitting on straw and a big colorful rooster with a tall red comb standing next to her, in a traditional Korean farmyard with a thatched house and a stone wall, morning light", "암탉과 수탉", False),
    ("c18", "a smooth weathered old boulder covered in green moss, half buried in the ground in a quiet forest, soft beams of light, symbolic of deep time", "낱말 속 화석", False),
    ("c19", "an ancient Goguryeo fortress wall of stacked stone on a misty mountain ridge in northern Korea, dawn", "고구려의 땅", False),
    ("c20", "an old Korean history book with a plain brown cover lying closed on a wooden table next to a candle, a map-like painted landscape of mountains and rivers faint in the background, no text", "삼국사기 지리지", False),
    ("c21", "river valleys and hills of the central Korean peninsula seen from above at sunrise, a few small ancient villages along the river", "땅이름에 남은 숫자", False),
    ("c22", "a calm sea between the southern Korean coast and the Japanese island of Kyushu at dawn, a small wooden sailing boat crossing, islands", "바다 건너 일본어", True),
    ("c23", "two ancient village communities on opposite sides of a river in the Korean peninsula, smoke rising from thatched huts, people working in fields, misty morning", "한반도에 함께 살았던 두 말?", True),
    ("c24", "a broad river valley in northeastern China with loess hills and early Neolithic fields of millet, golden light", "랴오허강 유역", False),
    ("c25", "a Neolithic village about 9000 years ago at harvest time: a golden field of foxtail millet with drooping bushy heads, round semi-subterranean houses with conical thatched roofs, villagers carrying woven baskets full of millet heads, warm light", "기장을 기르던 농부들", True),
    ("c26", "close-up of two cupped hands holding a bundle of drooping bushy golden foxtail millet heads, tiny round grains, soft warm light", "기장 이삭", True),
    ("c27", "a long line of Neolithic farming families migrating east carrying baskets of seeds and tools across hills toward distant mountains, sunrise", "농사와 함께 퍼진 말?", True),
    ("c28", "one laboratory table holding a microscope next to an ancient tooth, several old pottery shards and a closed old leather book, warm lab light", "언어학·고고학·유전학", False),
    ("c29", "a diverse group of modern East Asian and European linguists, men and women, discussing around a seminar table with papers and laptops, seen from the side, plain wall behind", "엇갈리는 학자들의 의견", "now"),
    ("c30", "a balance scale on a wooden table with a small heap of grain on one side and a stack of closed old books on the other, perfectly level, soft light", "아직 결론은 없다", False),
    ("c31", "Jeju island coast with black volcanic rocks and a low black stone wall, an orange haenyeo float bobbing on the blue sea, in the far distance a very wide low gently rounded dome mountain under clouds, bright day, no people", "제주의 말", False),
    ("c32", "two small saplings growing side by side from the same root in rich soil, close-up, morning dew, soft light", "한국어족: 한국어와 제주어", False),
    ("c33", "the night side of the Earth seen from orbit, glowing golden city lights spread across East Asia, a thin blue line of atmosphere on the curved horizon", "세계의 수많은 언어", False),
    ("c34", "the Basque countryside with green hills and a stone farmhouse in northern Spain, misty morning, no people", "홀로 서 있는 다른 언어들", False),
    ("c35", "a long caravan of people from many eras walking through northeast Asia over thousands of years: Neolithic farmers, bronze age villagers, ancient kingdom people, along a river valley, symbolic, sunset", "수천 년의 이동과 만남", True),
    ("c36", "a family of three generations in modern Korea, a grandmother, a mother and a child, laughing and talking together at a dinner table, warm home light", "할머니에게서 아이에게로", "now"),
    ("c37", "over-the-shoulder view of a young child in a modern classroom holding a pencil and writing in a notebook, the page out of focus and blurred, warm soft light, shallow depth of field", "오늘 쓰는 한글", "now"),
    ("c38", "an old tree with deep roots spreading through the soil shown in cross-section, the roots fading into darkness, concept art", "보이지 않는 깊은 뿌리", False),
    ("c39", "a sunrise over the Korean peninsula seen from high above, mountains and rivers lit in gold, peaceful", "말이 이어 온 땅", False),
    ("c40", "a wide warm sunset over a Korean village with people walking home along a path, talking together, peaceful", "우리말이 걸어온 길", "now"),
]

# 누끼를 깊이 대신 정해 준 덩어리로 할 컷 (연기·구름 등). 이 편은 없음
CUTOUT = {}

STORY = """{c01}

지금 이 순간에도 약 8천만 명이 한국어로 말하고 있습니다. 세계에서 사용자가 많은 언어 가운데 하나입니다.

{c02}

그런데 이렇게 많은 사람이 쓰는 한국어에게는 이상한 점이 하나 있습니다. 가까운 친척 언어가 분명하지 않다는 것입니다. 영어와 독일어는 형제 언어이고, 스페인어와 이탈리아어는 사촌 언어입니다. 그런데 한국어의 형제나 사촌이 누구인지는, 아직 아무도 확실히 말하지 못합니다.

{c03}

한국어는 도대체 어디에서 왔을까요? 끝까지 보시면, 교과서에 실렸던 생각과 최근의 새로운 연구, 그리고 우리가 매일 쓰는 낱말 속에 숨어 있는 옛 소리까지 알게 되실 겁니다.

## 1. 알타이어족 가설

{c04}

1920년대, 일본에 외교관으로 와 있던 핀란드의 언어학자 람스테트는 한국어를 깊이 공부하기 시작했습니다. 그리고 한국어가 몽골어, 만주어, 터키어 같은 언어들과 한 가족이라는 주장을 내놓았습니다.

{c05}

이 언어들이 알타이 산맥 둘레의 넓은 초원에서 퍼져 나갔다고 보아, 알타이어족이라고 불렀습니다.

{c06}

이 주장에는 여러 가지 근거가 있었습니다. 이 언어들은 모두 주어, 목적어, 동사의 순서로 말합니다. 낱말 뒤에 은, 는, 을, 를 같은 조사를 붙여 뜻을 만듭니다. 옛 한국어에는 밝은 모음은 밝은 모음끼리, 어두운 모음은 어두운 모음끼리 어울리는 모음조화도 뚜렷했습니다. 지금도 퐁당퐁당과 풍덩풍덩, 알록달록과 얼룩덜룩 같은 말에 그 흔적이 남아 있지요. 또 낱말 첫머리에 리을 소리가 잘 오지 않는다는 점도 닮았습니다.

{c07}

언어학자들은 언어도 사람처럼 족보가 있다고 봅니다. 하나의 조상 언어가 오랜 시간 동안 여러 갈래로 나뉘어 지금의 언어들이 되었다는 것입니다.

{c08}

그런데 시간이 흐르며 이 가설에 의문이 커졌습니다. 친척 언어라면 하나, 둘, 셋 같은 숫자나 눈, 코, 손 같은 몸 이름처럼 아주 기본적인 낱말에서 규칙적으로 닮은 소리가 나와야 합니다. 그런데 한국어와 몽골어, 터키어 사이에서는 그런 짝을 찾기가 어려웠습니다. 말의 순서나 조사가 닮은 것은, 오랫동안 이웃해 살면서 서로 영향을 주고받아 생겼을 수도 있습니다. 두 나무가 나란히 자라 가지가 얽혔다고 해서 같은 뿌리라고 할 수는 없는 것이지요.

{c09}

그래서 오랫동안 교과서에 실렸던 알타이어족 가설은, 지금은 많은 언어학자가 증명되지 않은 가설로 봅니다. 그렇다면 옛날의 한국어는 어떤 모습이었을까요? 이번에는 옛 기록 속으로 천천히 들어가 보겠습니다.

## 2. 기록 속의 옛 한국어

{c10}

1103년, 송나라의 사신 손목이 고려에 왔습니다. 그는 고려 사람들이 쓰는 말을 한자로 받아 적어 책으로 남겼습니다. 그 책이 계림유사입니다.

{c11}

한자의 소리를 빌려 고려 말 약 350개를 적어 놓았는데, 지금 읽어 보아도 알아들을 수 있는 말이 많습니다.

{c12}

예를 들어 하늘은 한날이라고 소리 나는 한자로 적었습니다. 9백 년 전 고려 사람들도 하늘을 지금과 거의 같은 소리로 불렀던 것입니다.

{c13}

이보다 더 오래된 기록도 있습니다. 신라 사람들이 부르던 노래, 향가입니다. 한자의 뜻과 소리를 빌려 우리말을 적은 이 노래는 삼국유사와 균여전에 모두 25수가 전합니다. 다만 한자로 우리말을 적다 보니, 정확히 어떻게 읽었는지는 학자마다 풀이가 조금씩 다릅니다.

{c14}

그리고 1443년, 세종대왕이 훈민정음을 만들면서 드디어 우리말을 소리 그대로 적을 수 있게 되었습니다. 처음 만든 글자는 모두 스물여덟 자였습니다. 덕분에 5백여 년 전 한국어의 소리와 모습이 아주 자세히 남게 되었고, 그 기록은 지금 한국어의 뿌리를 찾는 데 가장 중요한 단서가 되었습니다.

## 3. 낱말 속에 남은 화석

{c15}

그런데 옛 한국어의 흔적은 옛 책 속에만 있는 것이 아닙니다. 우리가 지금 쓰는 말 속에도 숨어 있습니다. 찹쌀, 좁쌀, 햅쌀을 떠올려 보세요. 찰과 쌀, 조와 쌀, 해와 쌀이 만났는데, 왜 사이에 비읍 받침이 생겼을까요?

{c16}

훈민정음 시대에 쌀은 첫소리에 비읍과 시옷을 함께 쓴 소리였습니다. 쌀 앞에 다른 말이 붙으면, 숨어 있던 그 비읍이 앞 글자의 받침으로 살아난 것입니다. 수백 년 전 사라진 소리가, 낱말 속에 화석처럼 남아 있는 셈이지요. 볍씨도 같습니다. 옛날에는 씨앗의 씨도 첫소리에 비읍을 함께 썼기 때문에, 벼와 씨가 만나 볍씨가 되었습니다.

{c17}

암탉과 수탉도 그렇습니다. 옛말에서 암과 수는 끝에 히읗 소리를 가진 낱말이었습니다. 그래서 닭과 만나 탉이 되고, 개와 만나 수캐가 되었습니다. 안팎, 살코기도 같은 이유로 생긴 말입니다.

{c18}

이렇게 말은 수백 년, 수천 년에 걸쳐 조금씩 바뀌면서도 옛 모습을 곳곳에 남깁니다. 언어학자들은 이런 흔적을 하나하나 모아 아주 먼 옛날의 한국어를 다시 그려 보려고 합니다.

## 4. 고구려 땅이름의 수수께끼

{c19}

그런데 삼국 시대로 거슬러 올라가면 이상한 수수께끼 하나를 만나게 됩니다.

{c20}

고려 때 쓰인 역사책 삼국사기에는, 옛 고구려 땅의 이름을 한자로 바꾸기 전의 원래 이름이 함께 적혀 있습니다.

{c21}

그 가운데 숫자가 들어간 땅이름이 있습니다. 셋은 밀, 다섯은 우차, 일곱은 난은, 열은 덕과 비슷한 소리로 적혀 있었습니다.

{c22}

놀랍게도 이 소리들은 일본어의 숫자와 닮았습니다. 일본어로 셋은 미, 다섯은 이츠, 일곱은 나나, 열은 토라고 합니다.

{c23}

그래서 아주 옛날 한반도 가운데 지역에 일본어의 조상 말을 쓰는 사람들이 살았다는 주장이 나왔습니다. 그 사람들이 나중에 바다를 건너 일본으로 갔다는 것입니다. 하지만 땅이름 몇 개만으로는 확실히 말하기 어렵다는 반론도 많아서, 이 문제는 지금도 활발한 논쟁거리입니다.

## 5. 농부가 퍼뜨린 말?

{c24}

2021년, 세계적인 과학 잡지 네이처에 한국어의 기원에 대한 큰 연구가 실렸습니다. 독일 막스플랑크 연구소의 언어학자 롭비츠가 이끄는 국제 연구팀의 연구입니다.

{c25}

연구팀은 약 9천 년 전, 지금의 중국 동북부 랴오허강 유역에서 기장을 기르던 농부들에 주목했습니다.

{c26}

이들이 쓰던 말이 한국어, 일본어, 몽골어, 만주어, 터키어 같은 언어들의 먼 조상이라는 것입니다. 연구팀은 이 큰 무리를 트랜스유라시아 언어라고 불렀습니다.

{c27}

농사가 퍼지면서 사람들이 움직였고, 그와 함께 말도 퍼져 나갔다고 보았습니다. 그 가운데 한 갈래가 수천 년에 걸쳐 한반도로 들어와 한국어의 조상이 되었다는 것입니다.

{c28}

이 연구는 낱말을 견주는 언어학, 땅속 유물을 살피는 고고학, 그리고 옛사람의 뼈에서 뽑은 DNA까지 세 가지 방법을 함께 썼다는 점에서 큰 관심을 받았습니다.

{c29}

하지만 반대 의견도 만만치 않습니다. 많은 언어학자는 이 언어들이 한 가족이라는 것부터가 아직 증명되지 않았다고 봅니다. 농사와 사람과 말이 늘 함께 움직였는지도 다시 따져 봐야 한다는 것입니다. 옛사람의 DNA가 보여 주는 것은 사람이 어디에서 왔는지이지, 그 사람이 어떤 말을 했는지는 아니기 때문입니다.

{c30}

결국 한국어가 다른 어떤 언어와 친척인지는, 아직 아무도 증명하지 못했습니다. 그렇다면 지금 학자들은 한국어를 어떻게 보고 있을까요?

## 6. 지금의 결론

{c31}

현재 많은 학자들은 한국어를 한국어족이라는 작은 가족으로 봅니다. 그리고 이 가족에는 또 하나의 식구가 있습니다. 바로 제주어입니다.

{c32}

어서 오세요를 제주에서는 혼저 옵서예라고 합니다. 이렇게 제주어는 육지 사람이 알아듣기 어려울 만큼 다른 점이 많아서, 따로 된 언어로 보는 학자들이 많습니다. 제주어에는 훈민정음 시대의 아래아 소리도 아직 남아 있습니다. 유네스코는 2010년 제주어를 사라질 위기에 놓인 언어로 정하기도 했습니다.

{c33}

세계에는 7천 개가 넘는 언어가 있습니다. 그 가운데에는 가까운 친척을 찾지 못한 언어가 적지 않습니다.

{c34}

스페인과 프랑스 사이의 바스크어도 그런 언어입니다. 한국어가 외롭다는 것은, 그만큼 오래되고 독특한 길을 걸어왔다는 뜻이기도 합니다.

## 마무리. 우리말이 걸어온 길

{c35}

한국어의 뿌리가 어디에 닿아 있는지는 아직 모릅니다. 하지만 분명한 것은, 수천 년 동안 수많은 사람들이 이 땅으로 오고, 만나고, 섞이면서 지금의 우리말을 만들어 왔다는 사실입니다.

{c36}

할머니가 어머니에게, 어머니가 아이에게 전해 준 말 한마디 한마디에, 그 오랜 이동과 만남의 이야기가 담겨 있습니다.

{c37}

그리고 우리는 지금 그 말을, 세종대왕이 만든 글자로 적고 있습니다.

{c38}

땅속 깊이 뻗은 나무뿌리처럼, 한국어의 뿌리도 아직 우리 눈에 다 보이지 않습니다.

{c39}

언젠가 새로운 기록이나 연구가 그 뿌리를 조금 더 비춰 줄지도 모릅니다.

{c40}

여러분은 한국어가 어디에서 왔다고 생각하시나요? 댓글로 여러분의 생각을 들려주세요. 우리 조상의 놀라운 이야기는 이 채널에서 계속 이어집니다."""


def main():
    cmd, folder = sys.argv[1], sys.argv[2]
    if cmd == "job":
        items = [{"id": cid, "width": 1024, "height": 576, "seed": 600 + int(cid[1:]),
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
        proj = {"ver": 7, "category": "장문", "genre": GENRE, "topic": "한국어의 기원", "title": TITLE,
                "story": story, "sources": [], "notes": "과학 다큐. 기원은 가설·논쟁으로. 그림은 AI 그림", "autophoto": False, "img_source": "그림: 사실묘사",
                "settings": {"format": "롱폼 가로(1920×1080)", "narration": "on",
                             "narr_voice": "Supertonic M2 (남성, 무료 로컬) [supertonic:M2]",
                             "layout": "자막형(큰 제목+사진+자막)", "img_fill": "전체 화면(글자가 사진 위에)",
                             "img_motion": "영상처럼(확대·이동·전환)", "fps": "24", "reveal_hit": "off", "reveal_fx": "off",
                             "head_show": "안 보임(제목 카드만)", "sub_split": "한 줄씩(문장·쉼표로 나눠 차례로)", "img_label": "off",
                             "img_depth": "on", "img_depth_amt": "누끼(앞 인물 따로)"}}   # 그림 속 앞 인물을 오려 따로 움직임 (사용자 결정)
        for cid, spec in CUTOUT.items():           # 그림 옆에 누끼 설정 파일 (영상 프로그램이 읽음)
            json.dump(spec, open(os.path.join(folder, cid + ".png.누끼.json"), "w", encoding="utf-8"))
        out = os.path.join(HERE, "한국어_어디에서왔을까.json")
        json.dump(proj, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(out, len(story), "chars")


if __name__ == "__main__":
    main()
