"""장문 미스터리 다큐 '손가락뼈 하나로 발견된 인류, 데니소바인의 수수께끼' — 대본 + 컷별 사진·그림 계획
python 장문/데니소바/데니소바인.py job <저장폴더> [c01,c02,...]  → 그림 주문서(klein_worker 용, 다큐 수채화) job.json (사진 컷은 빼고)
python 장문/데니소바/데니소바인.py project <그림폴더>          → 프로젝트 파일(render_project 용) 장문/데니소바/데니소바인.json
사실 주제 → 실제 사진 최대한(사용자 결정): PHOTOS 의 컷은 위키미디어 공용 사진(사진/<컷>.jpg, 출처·라이선스 표시),
사진이 있을 수 없는 장면(수만 년 전 모습·상상 복원)만 AI 그림(다큐 수채화). 실제 유물·장소는 REFS 의 사진을 기준 그림으로
사실 확인: Krause 외(Nature 2010, 손가락뼈 mtDNA), Reich 외(Nature 2010, 게놈), Slon 외(Nature 2018, '데니'),
Huerta-Sánchez 외(Nature 2014, EPAS1), Chen 외(Nature 2019, 바이시야 동굴 턱뼈), Tsutaya 외(Science 2025, 펑후 1호),
Fu 외(Cell·Science 2025, 하얼빈 두개골), UC Berkeley(2026, 유령 조상 두 무리), 런던 자연사박물관 데니소바인 해설"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
TITLE = "손가락뼈 하나로 발견된 인류, 데니소바인의 수수께끼"
STYLE_NAME = "다큐 수채화"   # 사용자 결정 2026-10-25: 장문은 수채화
DIALOGUE = []     # 다큐라 인물 대사 없음 (나레이션만)

# (컷번호, 그림 설명(영어), 화면 설명(한국어))
CUTS = [
    ("c01", "a tiny fragment of an ancient pinky finger bone lying on a dark laboratory tray under a bright lamp, tweezers beside it. No people, no hands, no arms anywhere.", "손가락뼈 한 조각"),
    ("c02", "Denisova Cave entrance in the Altai Mountains of Siberia (real photo)", "시베리아 데니소바 동굴"),
    ("c03", "a scientist in a clean-room suit and mask looking at a glowing DNA sequence on a computer screen in a dark ancient-DNA laboratory, no text", "DNA를 읽는 연구실"),
    ("c04", "a misty prehistoric Asian mountain landscape at dawn with silhouettes of a small group of ancient humans walking along a ridge, far away", "사라진 인류"),
    ("c05", "the Altai Mountains landscape in Siberia (real photo)", "알타이산맥"),
    ("c06", "inside a deep limestone cave in Siberia with archaeologists' lamps lighting excavation layers and small square digging pits, no people visible. No people, no hands, no arms anywhere.", "동굴 속 발굴 층"),
    ("c07", "Svante Paabo, Swedish geneticist (real photo)", "스반테 페보 강연 (2022 노벨상)"),
    ("c08", "an ancient-DNA clean laboratory with white suits hanging and sterile benches, UV light, no text. No people, no hands, no arms anywhere.", "고대 DNA 청정 실험실"),
    ("c09", "Neanderthal skull (real photo)", "네안데르탈인 두개골"),
    ("c10", "a simple watercolor of one bare tree trunk splitting into three thick branches against a plain sky, a symbolic family tree, no labels, no text, no letters. No people, no hands, no arms anywhere.", "세 갈래로 갈라진 인류"),
    ("c11", "a large ancient human molar tooth beside a small modern human tooth on a black museum cloth, comparison. No people, no hands, no arms anywhere.", "유난히 큰 어금니"),
    ("c12", "a prehistoric campfire in a Siberian cave, two ancient humans of different looks sitting together, one with a heavier brow, warm firelight, peaceful", "두 인류의 만남"),
    ("c13", "a tiny ancient bone fragment glowing softly with two strands of DNA drawn as colored threads twisting above it, symbolic. No people, no hands, no arms anywhere.", "부모가 다른 아이, 데니"),
    ("c14", "Tibetan Plateau landscape high mountains (real photo)", "티베트 고원"),
    ("c15", "a Tibetan Buddhist monk at Baishiya Karst Cave entrance in the high plateau, prayer flags, wide view", "바이시야 동굴과 수도승"),
    ("c16", "Xiahe mandible Denisovan jaw (real photo)", "티베트에서 나온 턱뼈"),
    ("c17", "Tibetan people herding yaks on a high plateau at 4,000 meters, thin air, bright sun, snowy peaks, wide view", "높은 산에 사는 사람들"),
    ("c18", "a fishing boat with a trawling net on the Penghu Channel between Taiwan and China at dusk, waves, nets full of mud and shells", "대만 해협의 어선"),
    ("c19", "Penghu 1 mandible fossil (real photo)", "펑후 1호 턱뼈"),
    ("c20", "a scientist extracting ancient proteins from a fossil jaw with a fine drill in a lab, mass spectrometer in background, no text", "뼈 속 단백질을 읽다"),
    ("c21", "Harbin skull Homo longi Dragon Man (real photo)", "하얼빈 '드래건맨' 두개골 (옆모습 그림)"),
    ("c22", "a bridge construction site over a frozen river in Harbin China in the 1930s, workers in winter coats, old sepia mood", "1933년 하얼빈 다리 공사"),
    ("c23", "a man in the 1930s secretly hiding a wrapped skull at the bottom of an old village well at night, lantern light, tense", "우물 속에 숨긴 두개골"),
    ("c24", "dental calculus scraped from an ancient tooth under a microscope, magnified mineral crust, scientific illustration. No people, no hands, no arms anywhere.", "이빨 치석에서 나온 DNA"),
    ("c25", "a tightly cropped head-and-shoulders watercolor portrait reconstruction of an archaic Denisovan man, not a modern human: very wide flat face, massive protruding brow ridge, low sloping forehead, very wide nose, huge jaw with no chin, large teeth, short dark hair and beard, rough animal-hide collar, dark eyes, serious expression, plain muted background, hands not visible", "하얼빈 두개골로 복원한 데니소바인의 얼굴"),
    ("c26", "Cobra Cave Laos or limestone karst landscape in Laos (real photo)", "라오스 석회암 동굴 지대"),
    ("c27", "a map-like watercolor showing only the continent of Asia (no Africa, no Europe, no Americas), five soft glowing dots in Siberia, Tibet, China, Laos and Taiwan, no text, no letters, no labels. No people, no hands, no arms anywhere.", "아시아 곳곳에 남은 흔적"),
    ("c28", "people of Papua New Guinea highlands in traditional dress (real photo)", "파푸아뉴기니 사람들"),
    ("c29", "colorful DNA double helix with a few highlighted segments glowing in a different color, symbolic watercolor. No people, no hands, no arms anywhere.", "우리 몸속 데니소바인 유전자"),
    ("c30", "a dark starry night over the Altai mountains with a faint shadowy group of ancient humans fading into mist, mysterious, no faces visible", "유령 조상"),
    ("c31", "a scientist seen from behind looking at a huge glowing wall of plain colored vertical stripes like a DNA barcode, two dark empty gaps glowing among the stripes, dark room, the stripes are plain color only, no text, no letters, no numbers, no symbols", "DNA 속 빈칸 두 개"),
    ("c32", "an aerial watercolor view of a wide river delta with many streams splitting and merging again across green land, no trees in the foreground, no text. No people, no hands, no arms anywhere.", "갈라지고 다시 만난 강줄기"),
    ("c33", "Homo sapiens skull and Neanderthal skull comparison (real photo)", "사피엔스와 네안데르탈인 두개골 비교"),
    ("c34", "a modern Asian city crosswalk seen from high above at dusk, small figures of people walking, warm street lights, wide view, plain blank shop fronts with no signs, no text, no letters, no billboards", "오늘을 사는 우리"),
    ("c35", "Denisova Cave interior excavation (real photo)", "데니소바 동굴 입구 — 지금도 계속되는 발굴"),
    ("c36", "a single small finger bone fragment glowing on a dark velvet cloth, surrounded by darkness, mysterious closing image. No people, no hands, no arms anywhere.", "아직 끝나지 않은 이야기"),
    ("c37", "road sign to Denisova Cave in the Altai (real photo)", "데니소바 동굴 가는 길"),
    ("c38", "Denisova Cave green stone bracelet (real photo)", "데니소바 동굴의 녹색 돌 팔찌 (복원 그림)"),
    ("c39", "Denisova 3 finger bone in its 2008 bag (real photo)", "2008년 발굴 당시의 손가락뼈 봉투"),
    ("c40", "Lake Ximencuo on the Tibetan Plateau (real photo)", "티베트 고원의 호수"),
    ("c41", "Tibetan pilgrim lighting butter lamps (real photo)", "티베트 사람"),
    ("c42", "people in Mount Piora, Papua New Guinea (real photo)", "파푸아뉴기니 고산 마을"),
]

STORY = """{c01}

데니소바인은 새끼손가락뼈 한 조각으로 세상에 처음 알려진 인류입니다. 쌀알 두 개만 한 뼈였습니다.

{c02}

2010년, 시베리아의 한 동굴에서 나온 이 작은 뼈가 인류의 족보를 통째로 흔들었습니다.

{c03}

과학자들이 그 뼈의 DNA를 읽어 보니, 우리도 아니고 네안데르탈인도 아니었습니다. 지금까지 아무도 몰랐던 인류였습니다.

{c04}

뼈는 거의 없는데 유전자만 남은 사람들. 끝까지 보시면, 지금 우리 몸속에 왜 그들의 흔적이 남아 있는지 알게 되실 겁니다.

## 1. 동굴 속 작은 뼈

{c05}

러시아 시베리아 남쪽, 알타이산맥. 겨울이면 영하 40도까지 내려가는 곳입니다.

{c06}

이곳의 데니소바 동굴에서는 오래전부터 발굴이 이어졌습니다. 흙을 한 층씩 걷어 낼 때마다 수만 년 전의 시간이 드러났습니다.

{c37}

동굴 이름은 18세기에 이곳에 살았던 은둔 수도사 데니스의 이름에서 왔다고 전해집니다. 동굴 안은 일 년 내내 서늘해서, 오래된 뼈 속 DNA가 다 부서지지 않고 남을 수 있었습니다.

{c38}

땅속 층을 조사해 보니, 데니소바인은 약 20만 년 전부터 이 동굴을 드나들었고, 네안데르탈인도 시기를 달리하며 이곳에 살았습니다. 같은 동굴에서는 녹색 돌을 갈아 만든 팔찌 조각도 나왔습니다. 누가 만들었는지는 아직 논란이지만, 구멍을 뚫고 매끈하게 다듬은 솜씨는 놀랍습니다.

{c01}

2008년, 발굴단은 작은 뼛조각 하나를 찾았습니다. 어린 소녀의 새끼손가락 끝마디였습니다. 너무 작아서 누구의 뼈인지 알 수 없었습니다.

{c39}

그래서 봉투에는 처음에, 그냥 우리와 같은 '호모 사피엔스'라고 적혔습니다. 이 뼈는 곧, 아무도 예상하지 못한 답을 내놓습니다.

## 2. DNA가 말한 이름 없는 사람

{c07}

뼈는 독일의 막스 플랑크 연구소로 보내졌습니다. 그곳에는 고대 DNA 연구의 선구자, 스반테 페보가 있었습니다. 그는 이 연구로 2022년 노벨상을 받게 됩니다.

{c08}

수만 년 된 DNA는 아주 작은 조각으로 부서져 있습니다. 연구팀은 먼지 하나 들어가지 않는 실험실에서, 그 조각들을 하나씩 이어 붙였습니다. 연구자의 손이나 숨에서 나온 DNA 한 가닥만 섞여도 결과가 틀어지기 때문에, 모두 우주복 같은 옷을 입고 일했습니다.

{c09}

결과는 놀라웠습니다. 이 뼈의 주인은 네안데르탈인과 가까웠지만, 네안데르탈인은 아니었습니다.

{c01}

처음 읽은 미토콘드리아 DNA는 이들이 약 100만 년 전에 우리 조상과 갈라졌다고 말했습니다. 이어서 읽은 전체 유전자는, 이들이 네안데르탈인의 형제 같은 무리라는 것을 보여 주었습니다. 2012년에는 새로운 방법으로, 쌀알만 한 이 뼈에서 지금 사람의 유전자만큼 정밀한 유전자 지도까지 만들어 냈습니다.

{c10}

인류의 족보에 새 가지가 하나 생긴 것입니다. 과학자들은 동굴 이름을 따서 이들을 데니소바인이라고 불렀습니다. 뼈의 모습보다 유전자가 먼저 발견된 첫 번째 인류였습니다.

{c11}

같은 동굴에서 나온 어금니도 이 사람들의 것이었습니다. 우리 어금니보다 훨씬 컸습니다. 유전자로 짐작해 보면, 그들은 어두운 피부와 갈색 머리카락, 갈색 눈을 가졌을 가능성이 큽니다. 그런데 이어서, 더 이상한 뼈가 나옵니다.

## 3. 부모가 다른 아이

{c12}

2018년, 같은 동굴에서 나온 또 다른 뼛조각의 DNA가 읽혔습니다. 약 9만 년 전에 살았던 열세 살쯤의 소녀였습니다.

{c13}

이 소녀의 어머니는 네안데르탈인, 아버지는 데니소바인이었습니다. 서로 다른 두 인류 사이에서 태어난 아이였던 것입니다. 연구자들은 소녀에게 데니라는 별명을 붙였습니다. 더 놀라운 것은, 데니의 아버지 쪽 조상에도 네안데르탈인의 피가 조금 섞여 있었다는 점입니다.

{c09}

두 인류의 만남은 한 번뿐인 우연이 아니었습니다. 여러 번, 오랜 세월에 걸쳐 일어났던 것입니다.

{c12}

두 인류는 서로를 만났고, 함께 가족을 이루었습니다. 그렇다면 데니소바인은 시베리아에만 살았을까요? 답은 곧, 해발 3천 미터 위에서 나옵니다.

## 4. 티베트 동굴의 턱뼈

{c14}

중국 티베트 고원. 공기가 희박해 오래 걷기만 해도 숨이 찬 곳입니다.

{c15}

1980년, 이곳의 바이시야 동굴에서 한 수도승이 기도를 하다가 사람의 턱뼈를 발견했습니다.

{c16}

턱뼈는 수십 년 동안 정체를 몰랐습니다. 2019년, 과학자들은 뼈에 남은 단백질을 읽었습니다.

{c40}

DNA는 따뜻한 곳에서 금방 부서지지만, 단백질은 훨씬 오래 버팁니다. 그래서 DNA가 사라진 뼈도 단백질로 주인을 알아낼 수 있습니다. 데니소바인의 것이었습니다. 적어도 16만 년 전, 그들은 이미 이 높은 고원에 살고 있었습니다.

{c15}

2020년에는 뼈가 아니라 동굴 바닥의 흙에서 데니소바인의 DNA가 나왔습니다. 흙 속에 남은 아주 작은 흔적만으로도, 그들이 이 동굴에 머물렀다는 것이 확인되었습니다. 함께 나온 짐승 뼈를 보면, 그들은 야생 양과 야크, 마멋, 새까지 사냥해 먹으며 이 높은 곳의 추위를 견뎠습니다.

{c17}

그리고 놀랍게도, 지금의 티베트 사람들 몸에 그 흔적이 남아 있었습니다.

{c41}

높은 곳에서도 숨을 잘 쉬게 돕는 유전자, EPAS1. 이 유전자가 데니소바인에게서 온 것이었습니다. 산소가 적은 곳에서도 피 속 적혈구가 지나치게 늘지 않게 해서, 피가 끈적해지는 것을 막아 줍니다. 이어서, 데니소바인의 흔적은 바다 밑에서도 나옵니다.

## 5. 바다 밑에서 건진 턱뼈

{c18}

대만과 중국 사이의 바다, 펑후 해협. 빙하기에는 이곳이 바다가 아니라 육지였습니다.

{c19}

어부들의 그물에 오래된 동물 뼈가 자주 걸려 올라왔습니다. 그중 하나가 튼튼한 사람의 턱뼈였습니다. 펑후 1호라고 불립니다.

{c20}

2025년, 연구팀은 이 턱뼈의 이빨에서 단백질을 읽어 냈습니다. 데니소바인 남성의 턱이었습니다. 시베리아에서 수천 킬로미터 떨어진 남쪽 바다에서 나온 것입니다. 그리고 곧, 같은 해에 데니소바인의 얼굴이 드러납니다.

## 6. 우물 속의 두개골

{c21}

중국 하얼빈에서 나온 거의 완전한 두개골, '드래건맨'입니다.

{c22}

이야기는 1933년으로 거슬러 올라갑니다. 하얼빈의 강에 다리를 놓던 한 노동자가 이 두개골을 발견했습니다.

{c23}

당시 하얼빈은 일본군이 점령하고 있었습니다. 그는 두개골을 빼앗길까 봐 오래된 우물 바닥에 숨겼다고 전해집니다. 그리고 85년 동안, 아무도 그 사실을 몰랐습니다. 두개골은 2018년에야 그의 손자를 통해 세상에 나왔습니다.

{c21}

두개골의 뇌 용량은 약 1,420cc로, 지금 우리와 비슷했습니다. 연구자들은 이 두개골에 '호모 롱기'라는 새 이름을 붙였습니다. 하지만 정말 새로운 종일까요?

{c24}

2025년, 연구팀은 이빨에 붙은 치석에서 DNA를 찾아냈습니다. 시베리아 데니소바인과 같은 계통이었습니다. 최소 14만 6천 년 전의 두개골이었습니다.

{c25}

손가락뼈 한 조각으로 시작된 사람들이, 15년 만에 처음으로 얼굴을 갖게 된 것입니다. 넓은 얼굴, 두꺼운 눈썹 뼈, 커다란 턱과 이빨. 그리고 이어서 볼 흔적은, 지금 우리 몸속에 있습니다.

## 7. 우리 몸에 남은 데니소바인

{c26}

라오스의 석회암 동굴에서도 데니소바인의 어금니가 나왔습니다. 13만 년도 더 전에 살았던 어린아이, 아마도 소녀의 이빨로 보입니다. 덥고 습한 열대에서는 뼈가 쉽게 썩기 때문에, 이 이빨 하나도 아주 귀한 증거입니다.

{c27}

시베리아, 티베트, 중국, 라오스, 대만. 데니소바인은 아시아 곳곳에 퍼져 살았습니다.

{c28}

그리고 그들은 우리 조상과 만났습니다. 파푸아뉴기니 같은 오세아니아 사람들은 유전자의 약 4에서 6퍼센트를 데니소바인에게서 물려받았습니다.

{c42}

그중에는 병균과 싸우는 면역 유전자도 있어서, 지금도 그들의 몸을 지키는 데 쓰이고 있습니다. 파푸아뉴기니까지 가려면 빙하기에도 바다를 건너야 했습니다. 그래서 일부 학자들은, 데니소바인이 바다를 건너는 법을 알았을지도 모른다고 봅니다.

{c29}

동아시아 사람들, 그러니까 우리에게도 아주 조금이지만 데니소바인의 유전자가 남아 있습니다.

{c34}

그린란드 이누이트 사람들이 추위를 견디도록 돕는 유전자도, 데니소바인과 가까운 옛 인류에게서 왔을 가능성이 있습니다. 사라진 인류는 사실, 완전히 사라진 것이 아니었습니다. 그런데 곧, 더 이상한 흔적이 발견됩니다.

## 8. 유령 조상

{c30}

과학자들은 데니소바인의 DNA 안에서 또 다른 무언가를 발견했습니다. 지금까지 뼈 한 조각도 나오지 않은, 더 오래된 인류의 흔적이었습니다. 과학자들은 이들을 '유령 집단'이라고 부릅니다. 뼈는 하나도 없고, 유전자 속 흔적만 남아 있기 때문입니다.

{c31}

2026년, 미국 UC 버클리 연구팀은 전 세계 503명의 유전자를 분석했습니다. 그 속에서 이름도 모르는 옛 인류 두 무리의 흔적이 나왔습니다. 하나는 약 80만 년 전에 갈라진 무리였습니다.

{c32}

인류의 역사는 한 줄로 이어진 사다리가 아니었습니다. 여러 갈래로 갈라졌다가 다시 만나는 강줄기에 가까웠습니다.

{c33}

우리, 네안데르탈인, 데니소바인, 그리고 아직 이름 없는 유령 조상들. 그들은 같은 시대를 살며 서로 만나고 섞였습니다. 이제 이어서, 이 이야기가 어디까지 왔는지 보겠습니다.

## 9. 아직 끝나지 않은 이야기

{c34}

오늘을 사는 우리 몸속에는, 수만 년 전 그 만남의 기록이 남아 있습니다.

{c35}

데니소바 동굴에서는 지금도 발굴이 계속되고 있습니다. 2021년에는 동굴 흙 수백 곳에서 DNA를 모아, 약 25만 년 동안 어느 인류가 언제 이 동굴에 살았는지 시간표를 만들었습니다. 하지만 아직 데니소바인의 온전한 뼈대는 한 번도 나오지 않았습니다.

{c36}

새끼손가락뼈 한 조각에서 시작된 이 이야기는, 아직 끝나지 않았습니다. 여러분은 다음에 어디서 데니소바인의 흔적이 나올 것 같나요? 댓글로 여러분의 생각을 들려주세요. 보고 나면 가벼운 지식이 남는 이야기, 이 채널에서 계속 이어집니다."""

# 실제 사진을 보고 그리는 컷 → 사진후보 이름들 (사진을 받은 뒤 채움)
REFS = {"c25": ["c21_1"], "c13": ["c01_1"], "c36": ["c01_1"]}
REF_NOTE = ("Any real fossil, cave or place shown must look exactly like the reference photo (same shape and colors), "
            "painted in the same watercolor style. ")

# 컷 → 고른 위키미디어 사진 후보 이름 (사진후보/후보.json 의 열쇠). 사진을 받은 뒤 채움
PHOTOS = {"c01": "c01_1", "c09": "c09_4", "c14": "c14_2", "c16": "c16_1", "c19": "c19_1", "c26": "c26_1", "c28": "c28_3", "c02": "c02_4", "c35": "c02_2", "c05": "c05_2", "c07": "c07_1", "c21": "c21_1", "c33": "c33_2", "c37": "c02_3", "c38": "c02_1", "c39": "c01_3", "c40": "c14_4", "c41": "c14_1", "c42": "c28_4", "c27": "c27_모음", "c25": "c25_1"}


def main():
    cmd, folder = sys.argv[1], sys.argv[2]
    main_src = os.path.join(ROOT, "..", "shorts_novel_maker_supertonic.py")      # 작업 가지(메인 저장소)의 최신 화풍 목록이 우선
    src = open(main_src if os.path.exists(main_src) else os.path.join(ROOT, "shorts_novel_maker_supertonic.py"), encoding="utf-8").read()
    style = re.search('"' + re.escape(STYLE_NAME) + '": "([^"]+)"', src).group(1)
    only = sys.argv[3].split(",") if len(sys.argv) > 3 else None
    if cmd == "job":
        items = []
        for cid, desc, _ in CUTS:
            if (only and cid not in only) or cid in PHOTOS:
                continue
            refs = [os.path.join(HERE, "사진후보", k + ".jpg") for k in REFS.get(cid, [])]
            items.append({"id": cid, "width": 1024, "height": 576, "seed": 300 + int(cid[1:]), "refs": refs,
                          "prompt": f"{style}, historical documentary illustration, realistic proportions, museum-quality painting. "
                                    f"Scene: {desc}. {REF_NOTE if refs else ''}{'' if 'no people' in desc.lower() else 'Every person has exactly two arms, two hands with five fingers each and two legs, hands simple and relaxed (partly hidden is fine). '}"
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
            story = story.replace("{" + cid + "}", f"[사진: {img} | {cap} | AI 그림 (FLUX.2 klein, 수채화) | ]")
        proj = {"ver": 7, "category": "장문", "genre": "[다큐] 역사·미스터리", "topic": "데니소바인", "title": TITLE,
                "story": story, "sources": ["https://www.nhm.ac.uk/discover/denisovans.html"],
                "notes": "인류 진화 미스터리 장문 다큐 (실제 화석·장소 사진 위주 + 사진이 없는 장면은 AI 그림)", "autophoto": False, "img_source": "그림: 수채화",
                "settings": {"format": "롱폼 가로(1920×1080)", "narration": "on",
                             "layout": "자막형(큰 제목+사진+자막)", "img_fill": "전체 화면(글자가 사진 위에)",
                             "img_motion": "영상처럼(확대·이동·전환)",
                             "head_show": "안 보임(제목 카드만)", "sub_split": "한 줄씩(문장·쉼표로 나눠 차례로)", "img_label": "on",
                             "narr_voice": "Supertonic M2 (남성, 무료 로컬) [supertonic:M2]"}}
        out = os.path.join(HERE, "데니소바인.json")
        json.dump(proj, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(out, len(story), "chars")


if __name__ == "__main__":
    main()
