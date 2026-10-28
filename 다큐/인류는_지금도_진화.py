"""과학 다큐 '인류는 지금도 진화하고 있다' — 대본 + 컷별 그림 계획
python 다큐/인류는_지금도_진화.py job <저장폴더>   → 그림 주문서(klein_worker 용) job.json
python 다큐/인류는_지금도_진화.py project <그림폴더> → 프로젝트 파일(render_project 용) 다큐/인류는_지금도_진화.json
python 다큐/인류는_지금도_진화.py txt <파일>        → 사용자 확인용 대본(그림 자리는 [그림: 설명])
  영상은 render_project.py <프로젝트> --대본그대로
사실 근거: 아크바리·라이크 외 2026 Nature "Ancient DNA reveals pervasive directional selection across West Eurasia"
  (새 옛사람 유전체 10,016명 + 기존 5,820명 + 현대 6,438명, 지난 약 1만 년, 강하게 선택된 변이 479개, 이전 연구는 약 21곳,
   유전자 빈도 변화 중 방향성 선택은 약 2%, 농경 이후 선택 가속, 밝은 피부·빨간 머리·B형·글루텐 민감·나병·HIV 저항, 결핵·다발성경화증 변이는 늘었다 줄어듦,
   연구진 경고: 유럽인이 더 똑똑·건강해졌다는 뜻 아님, 서유라시아만),
  클렁크 외 2022 Nature(흑사병과 ERAP2), 에버셰드 외 2022 Nature(우유 소화 능력 확산과 기근·전염병),
  카베로프 외 2013 Cell(동아시아 EDAR, 약 3만 년 전), 우에르타-산체스 외 2014 Nature(티베트 EPAS1, 데니소바인)"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TITLE = "인류는 지금도 진화하고 있다"
GENRE = "고대 인류"
STYLE = ("scientific documentary illustration, detailed digital painting like a National Geographic or science magazine illustration, "
         "natural realistic colors, clear readable composition, soft cinematic lighting, high detail")
PEOPLE = ("ancient people in period-appropriate simple clothing, a mixed group of men and women, "
          "each person with exactly two arms and two legs, natural anatomy")   # 옛 사람이 나오는 컷에 붙임 (팔다리 수 규칙)
NOW = "modern-day people in contemporary clothing, each person with exactly two arms and two legs, natural anatomy"   # 오늘날 사람 컷

# (컷번호, 그림 설명(영어), 화면 설명(한국어), 사람이 나오는 컷인지: True=옛 사람, "now"=오늘날 사람)
CUTS = [
    ("c01", "a long line of human silhouettes walking across a vast landscape from left to right at sunrise, from ancient hunters in hides to farmers to modern people in today's clothes, symbolic", "이어지는 인류의 걸음", True),
    ("c02", "a modern city crosswalk seen from above with many people of different appearances crossing in all directions, sunny day", "오늘을 사는 우리", "now"),
    ("c03", "rows of ancient human skulls and bones carefully laid out on white trays in a bright modern laboratory storage room, labels blank, scientific atmosphere", "1만 6천 명의 옛사람", False),
    ("c04", "a softly glowing DNA double helix rising out of an ancient bone fragment lying on dark soil, concept art", "뼈 속에 남은 DNA", False),
    ("c05", "close-up of a small dense human inner-ear bone (petrous bone) held with tweezers by a gloved hand in a clean laboratory, blue-white light", "가장 단단한 뼈, 귀 속 뼈", "now"),
    ("c06", "a scientist in a full white clean suit, mask and gloves drilling a tiny sample from an ancient bone inside a clean air hood, blue-white light", "옛 DNA를 꺼내는 연구실", "now"),
    ("c07", "three layers of soil in an archaeological cross-section, each layer containing ancient human remains and tools from a different era, deeper is older, concept illustration", "1만 년 전, 5천 년 전, 오늘", False),
    ("c08", "a huge tree of colored threads branching and merging over time, symbolic of genes passing through generations, soft glowing background, concept art", "세대를 따라 흐르는 유전자", False),
    ("c09", "a long chain of hands of different generations holding each other, from an old wrinkled hand to a baby's hand, warm light, symbolic", "약 400세대의 이어달리기", True),
    ("c10", "a group of hunter-gatherers about 10,000 years ago at the end of the Ice Age walking through a cold forest with spears, wearing furs, Europe", "빙하기가 끝날 무렵의 사냥꾼들", True),
    ("c11", "early Neolithic farmers about 8,000 years ago sowing wheat seeds by hand in a small field next to timber longhouses with thatched roofs, Europe, morning light", "농사를 시작한 사람들", True),
    ("c12", "a golden field of ancient einkorn wheat with a small Neolithic village of thatched longhouses in the background, warm light", "밀밭과 마을", False),
    ("c13", "a Neolithic woman kneeling and grinding wheat grains into flour on a flat saddle quern stone with a round hand stone, inside a timber house, firelight", "밀가루를 빻는 손", True),
    ("c14", "close-up of a loaf of rough ancient flatbread and scattered wheat grains on a wooden board, soft light", "빵과 글루텐", False),
    ("c15", "a farmer in simple linen clothing working in a field under a pale northern sky with weak winter sunlight, Neolithic Europe", "햇빛이 약한 북쪽 땅", True),
    ("c16", "a crowded Bronze Age village with many houses packed close together, livestock pens beside homes, smoke from many fires, people and animals together", "모여 살기 시작한 사람과 가축", True),
    ("c17", "microscope view of various bacteria and virus particles floating in a dark background, colorful scientific illustration", "늘어난 전염병", False),
    ("c18", "an ancient healer caring for a sick person lying on a straw bed inside a dim timber house, oil lamp light, compassionate mood", "병과 싸운 사람들", True),
    ("c19", "a medieval European town street in the 1340s, quiet and empty, closed wooden doors, gray overcast sky, somber mood, no bodies", "1346년, 흑사병", False),
    ("c20", "medieval people in long cloaks walking through a foggy town square, some covering their mouths with cloth, somber mood", "살아남은 사람들", True),
    ("c21", "a symbolic illustration of immune cells as glowing shields surrounding a cell against dark invading particles, concept art", "면역 유전자의 변화", False),
    ("c22", "a small glass test tube rack holding blood sample tubes with A, B, O shown only as different colored caps, laboratory bench, soft light, no text", "혈액형 B형", False),
    ("c23", "a herd of ancient cattle grazing near a Bronze Age village at dawn, a herder with a staff watching them", "소를 기르기 시작한 사람들", True),
    ("c24", "a woman in Bronze Age clothing milking a cow into a clay pot beside a wooden fence, morning light", "우유를 짜는 사람", True),
    ("c25", "clay pottery jars and bowls from the Bronze Age with traces of milk residue on a museum table, soft light", "토기에 남은 우유 흔적", False),
    ("c26", "a dry cracked field with withered crops and a thin cow under a harsh sun, a worried farming family standing nearby, famine", "굶주림의 시대", True),
    ("c27", "a mother giving a small bowl of milk to her child inside a simple Bronze Age house, warm light, tender mood", "우유가 생명을 살린 때", True),
    ("c28", "a vast map-like painted view of Europe and western Asia from high above with soft clouds, realistic earth colors", "이번 연구가 다룬 땅, 서유라시아", False),
    ("c29", "a painted view of East Asia from high above: China, the Korean peninsula and Japan, soft morning clouds, realistic earth colors", "동아시아는 아직", False),
    ("c30", "close-up of thick straight black hair of an East Asian person in soft light, macro detail, shallow depth of field", "굵고 곧은 머리카락", "now"),
    ("c31", "the high Tibetan plateau with snowy mountains, a Tibetan herder in thick traditional clothing walking with yaks, thin bright air", "높은 땅에 사는 티베트 사람들", True),
    ("c32", "the entrance of a cave in high Siberian mountains in snow, mysterious atmosphere, no people", "데니소바인의 동굴", False),
    ("c33", "two different ancient human groups meeting near a cave in snowy mountains, cautious but peaceful, wearing furs", "만남이 남긴 유전자", True),
    ("c34", "a modern geneticist seen from behind looking at a large screen showing colorful abstract DNA sequence patterns without letters, dark lab", "숫자보다 조심스러운 해석", "now"),
    ("c35", "a balance scale holding a small DNA model on one side and a stack of closed history books on the other side, soft light, symbolic", "유전자와 환경", False),
    ("c36", "diverse modern people of many ethnicities standing together in a sunny park, smiling, seen from the front at a distance", "더 나은 사람은 없다", "now"),
    ("c37", "a modern hospital laboratory with blood samples and a microscope, a doctor in a white coat seen from behind, bright light", "오늘의 병과 옛날의 이유", "now"),
    ("c38", "a newborn baby sleeping peacefully in a parent's arms, warm soft window light", "지금 태어나는 아이", "now"),
    ("c39", "a long road stretching to the horizon through green hills at sunset, symbolic of the future, no people", "1만 년 뒤의 인류", False),
    ("c40", "the Earth seen from space at sunrise with a thin glowing atmosphere, peaceful", "계속되는 이야기", False),
]

# 누끼를 깊이 대신 정해 준 덩어리로 할 컷, 또는 검수에서 끌 컷 ({"off": True}). 아직 없음
CUTOUT = {}

STORY = """{c01}

인류의 진화는 이미 끝났다는 말, 들어 보신 적 있으신가요? 의학과 문명이 발달하면서 자연선택은 더 이상 사람에게 작용하지 않는다는 것이지요.

{c02}

그런데 2026년 봄, 세계적인 과학 잡지 네이처에 이 생각을 뒤흔드는 연구가 실렸습니다.

{c03}

과학자들이 옛사람 약 1만 6천 명의 DNA를 한꺼번에 분석한 것입니다. 지금까지 이루어진 옛 DNA 연구 가운데 가장 큰 규모입니다. 그 결과는 놀라웠습니다. 인류의 진화는 멈추기는커녕, 지난 1만 년 동안 오히려 더 빨라졌다는 것입니다. 끝까지 보시면, 우리 몸속에 남은 그 진화의 흔적을 하나하나 만나 보실 수 있습니다.

## 1. 뼈 속의 타임머신

{c04}

사람이 세상을 떠나도, 뼈 속에는 그 사람의 DNA가 아주 조금 남아 있습니다. 수천 년이 지나 조각조각 부서졌어도, 과학자들은 이 조각을 모아 다시 읽어 낼 수 있습니다.

{c05}

특히 귀 속 깊은 곳의 작은 뼈는 사람 몸에서 가장 단단한 뼈 가운데 하나입니다. 그래서 오래된 DNA가 비교적 잘 남아 있는 보물 창고로 불립니다. 옛사람의 DNA를 읽는 이 기술을 연 스웨덴의 과학자 스반테 페보는, 2022년 노벨 생리의학상을 받기도 했습니다.

{c06}

이번 연구는 미국 하버드 의대 데이비드 라이크 교수 연구팀이 이끌었습니다. 연구팀은 새로 1만 명이 넘는 옛사람의 유전체를 읽고, 이미 알려진 옛사람 5천8백여 명, 그리고 오늘날 사람 6천4백여 명의 유전체와 함께 비교했습니다.

{c07}

원리는 간단합니다. 같은 땅에 살았던 1만 년 전 사람, 5천 년 전 사람, 그리고 오늘날 사람의 유전자를 나란히 놓고 봅니다. 어떤 유전자 변이가 시간이 갈수록 꾸준히 늘었다면, 그 변이가 살아남는 데 유리했다는 신호입니다.

{c08}

물론 유전자는 다른 이유로도 바뀝니다. 다른 지역 사람들이 이주해 오거나, 그냥 우연히 늘었다 줄었다 하기도 하지요. 연구팀은 새로운 계산 방법으로 이런 변화를 걸러 내고, 자연선택의 흔적만 골라냈습니다.

{c09}

1만 년은 사람의 세대로 치면 약 4백 세대입니다. 할머니에게서 어머니로, 어머니에게서 아이로 이어진 4백 번의 이어달리기 속에서, 몸은 조금씩 바뀌어 왔습니다.

## 2. 농사가 바꾼 몸

{c10}

그렇다면 무엇이 진화를 빠르게 만들었을까요? 연구팀이 찾은 가장 큰 열쇠는 바로 농사였습니다.

{c11}

빙하기가 끝나고 사람들은 사냥과 채집을 하던 삶에서, 한곳에 머물며 곡식을 기르는 삶으로 바뀌었습니다. 먹는 음식도, 사는 모습도 완전히 달라졌습니다.

{c12}

예전 연구들은 지난 1만 년 동안 자연선택의 흔적을 스무 곳 남짓 찾았을 뿐이었습니다. 그런데 이번 연구는 강하게 선택된 유전자 변이를 479개나 찾아냈습니다. 그리고 그 선택은 농사를 시작한 뒤에 더 빨라졌습니다.

{c13}

대표적인 예가 밀입니다. 사람들이 밀을 기르고 빵을 먹기 시작한 뒤, 오늘날 글루텐을 잘 소화하지 못하는 병과 관련된 유전자 변이가 오히려 크게 늘었습니다.

{c14}

지금은 병의 위험을 높이는 변이가 왜 그때는 퍼졌을까요? 아직 정확한 이유는 모릅니다. 다만 같은 유전자가 전염병을 막는 데도 관련이 있어서, 그때는 이로운 점이 더 컸을 것이라는 해석이 나옵니다.

{c15}

피부색도 달라졌습니다. 밝은 피부와 관련된 유전자 변이가 이 시기에 크게 늘었습니다. 햇빛이 약한 북쪽 땅에서, 고기와 생선 대신 곡식을 주로 먹게 되면서 몸에서 비타민 D를 더 잘 만들어야 했다는 가설이 유력합니다. 빨간 머리와 관련된 변이가 늘어난 것도 이번 연구에서 확인되었습니다. 실제로 영국에서 발견된 약 1만 년 전 사람의 DNA를 읽어 보니, 피부가 꽤 짙었을 가능성이 높다는 결과가 나오기도 했습니다. 지금 유럽 사람들의 밝은 피부는, 생각보다 최근에 퍼진 특징인 셈입니다.

## 3. 병과의 전쟁

{c16}

농사는 사람들을 한곳에 모여 살게 했습니다. 마을이 커지고, 사람과 가축이 바로 곁에서 함께 살았습니다.

{c17}

그러자 전에 없던 일이 벌어졌습니다. 가축에게서 옮아온 병, 북적이는 마을에서 빠르게 퍼지는 병이 크게 늘어난 것입니다.

{c18}

자연선택이 가장 뚜렷하게 나타난 곳도 바로 병과 싸우는 면역의 유전자였습니다. 이번 연구에서는 나병에 잘 견디는 유전자, 그리고 오늘날 HIV 감염을 막는 것과 관련된 유전자 변이가 늘어난 흔적이 나왔습니다.

{c19}

1346년부터 몇 해 동안 유럽을 휩쓴 흑사병은 그 극적인 예입니다. 당시 유럽 인구의 3분의 1에서 절반 가까이가 목숨을 잃은 것으로 추정됩니다.

{c20}

2022년 네이처에 실린 다른 연구는, 흑사병 전후에 묻힌 사람들의 DNA를 비교했습니다. 그 결과 특정 면역 유전자를 가진 사람들이 더 잘 살아남았다는 사실을 밝혀냈습니다.

{c21}

그런데 그 유전자는 오늘날 크론병 같은 자가면역 질환과도 관련이 있습니다. 옛날 우리를 지켜 준 유전자가 지금은 다른 병의 위험이 되기도 하는 것입니다.

{c22}

혈액형도 그렇습니다. 이번 연구에서는 B형 혈액형과 관련된 변이가 늘어난 흔적이 나왔습니다. 연구팀은 이것이 어떤 세균이나 바이러스에 견디는 힘과 관련이 있었을 것으로 보고 있습니다. 결핵과 관련된 변이는 오랫동안 늘었다가, 다시 줄어들기도 했습니다. 환경이 바뀌면 유리한 유전자도 바뀌는 것이지요.

## 4. 우유를 마시게 된 어른들

{c23}

진화의 흔적 가운데 가장 유명한 이야기가 있습니다. 바로 우유입니다.

{c24}

원래 사람은 젖을 뗀 뒤에는 우유 속의 젖당을 잘 소화하지 못합니다. 지금도 세계 어른들의 절반이 훨씬 넘게 그렇습니다. 그런데 유럽 북쪽 사람들 가운데에는 어른이 되어서도 우유를 잘 소화하는 사람이 아주 많습니다.

{c25}

2022년 네이처에 실린 연구는 옛 토기에 남은 우유 흔적과 옛사람의 DNA를 함께 살폈습니다. 사람들은 9천 년 가까이 우유를 먹어 왔지만, 우유를 소화하는 유전자는 그보다 훨씬 늦게, 수천 년에 걸쳐 퍼졌습니다.

{c26}

연구팀은 그 열쇠가 굶주림과 전염병이었다고 보았습니다. 평소에는 우유를 소화하지 못해도 조금 배탈이 날 뿐입니다.

{c27}

하지만 먹을 것이 없고 병이 돌던 때에는, 우유를 소화할 수 있느냐 없느냐가 생사를 갈랐을 수 있습니다. 그런 어려운 시기를 거치며 우유를 소화하는 유전자가 빠르게 퍼졌다는 것입니다.

## 5. 동아시아와 우리

{c28}

여기서 꼭 짚고 넘어가야 할 점이 있습니다. 이번 연구는 유럽과 서아시아, 곧 서유라시아 사람들만 다뤘습니다.

{c29}

동아시아 사람들의 지난 1만 년은 아직 이만큼 크게 연구되지 않았습니다. 연구팀도 앞으로 동아시아와 아프리카, 아메리카로 연구를 넓히겠다고 밝혔습니다.

{c30}

다만 동아시아에도 이미 알려진 진화의 흔적이 있습니다. 동아시아 사람들에게 많은 한 유전자 변이는 머리카락을 더 굵게 하고, 땀샘의 수와 앞니의 모양에도 영향을 줍니다. 이 변이는 약 3만 년 전 무렵 동아시아에서 퍼지기 시작한 것으로 추정됩니다.

{c31}

티베트 사람들은 공기가 희박한 높은 땅에서도 잘 살아갑니다. 그 비밀 가운데 하나는 산소가 적은 환경에 맞춰 주는 유전자입니다.

{c32}

놀랍게도 이 유전자는 아주 오래전에 사라진 인류의 친척, 데니소바인에게서 온 것으로 밝혀졌습니다.

{c33}

먼 옛날 서로 다른 인류가 만나 남긴 유전자가, 수만 년 뒤 높은 산에서 살아가는 힘이 된 것입니다.

## 6. 조심해야 할 해석

{c34}

그런데 이런 연구를 볼 때 조심해야 할 점이 있습니다. 연구팀 스스로도 여러 번 강조한 부분입니다. 사실 지난 1만 년 동안의 유전자 변화 가운데, 자연선택으로 설명되는 것은 약 2퍼센트에 불과합니다. 나머지 대부분은 사람들이 옮겨 다니고 서로 섞이면서, 또는 우연히 생긴 변화입니다.

{c35}

어떤 유전자가 오늘날 어떤 특징과 관련이 있다고 해서, 옛날에도 그 특징 때문에 퍼졌다고는 말할 수 없습니다. 유전자 하나가 여러 가지 일에 관여하기도 하고, 정말 중요한 유전자는 그 옆에 숨어 있을 수도 있습니다.

{c36}

연구팀은 이 결과가 어느 집단이 더 똑똑해졌다거나 더 건강해졌다는 뜻이 결코 아니라고 분명히 밝혔습니다. 진화는 더 나은 사람을 만드는 과정이 아니라, 그때그때의 환경에 맞춰 가는 과정이기 때문입니다.

{c37}

오히려 이 연구는 오늘날 우리가 앓는 병을 이해하는 데 실마리를 줍니다. 옛날에는 우리를 지켜 준 유전자가 왜 지금은 병의 원인이 되는지 알게 되면, 새로운 치료법을 찾는 데 도움이 될 수 있습니다.

## 마무리. 진화는 끝나지 않았다

{c38}

지금 이 순간에도 세상에는 새로운 아이들이 태어나고 있습니다. 그리고 그 아이들의 몸속에는 1만 년 동안 이어진 진화의 기록이 고스란히 담겨 있습니다.

{c39}

음식이 바뀌고, 병이 바뀌고, 사는 곳이 바뀌면 인류의 몸도 천천히 따라 바뀝니다. 진화는 끝난 것이 아니라, 지금도 우리 안에서 조용히 계속되고 있습니다.

{c40}

여러분은 1만 년 뒤의 인류가 어떤 모습일 거라고 생각하시나요? 댓글로 여러분의 생각을 들려주세요. 우리 조상의 놀라운 이야기는 이 채널에서 계속 이어집니다."""


def main():
    cmd, folder = sys.argv[1], sys.argv[2]
    if cmd == "job":
        items = [{"id": cid, "width": 1024, "height": 576, "seed": 500 + int(cid[1:]),
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
        proj = {"ver": 7, "category": "장문", "genre": GENRE, "topic": "옛 DNA로 본 인류 진화", "title": TITLE,
                "story": story, "sources": [], "notes": "과학 다큐. 연구 해석은 조심스럽게. 그림은 AI 그림", "autophoto": False, "img_source": "그림: 사실묘사",
                "settings": {"format": "롱폼 가로(1920×1080)", "narration": "on",
                             "narr_voice": "Supertonic M2 (남성, 무료 로컬) [supertonic:M2]",
                             "layout": "자막형(큰 제목+사진+자막)", "img_fill": "전체 화면(글자가 사진 위에)",
                             "img_motion": "영상처럼(확대·이동·전환)", "fps": "24", "reveal_hit": "off", "reveal_fx": "off",
                             "head_show": "안 보임(제목 카드만)", "sub_split": "한 줄씩(문장·쉼표로 나눠 차례로)", "img_label": "on",   # 오른쪽 위 그림 설명은 꼭 보임
                             "img_depth": "on", "img_depth_amt": "누끼(앞 인물 따로)"}}   # 누끼는 검수에서 깔끔한 그림만 (CUTOUT off)
        for cid, spec in CUTOUT.items():           # 그림 옆에 누끼 설정 파일 (영상 프로그램이 읽음)
            json.dump(spec, open(os.path.join(folder, cid + ".png.누끼.json"), "w", encoding="utf-8"))
        out = os.path.join(HERE, "인류는_지금도_진화.json")
        json.dump(proj, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(out, len(story), "chars")


if __name__ == "__main__":
    main()
