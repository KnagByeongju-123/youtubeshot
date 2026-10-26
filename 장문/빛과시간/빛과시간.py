"""장문 과학 다큐 '우리가 보는 밤하늘은 가짜일까, 빛이 숨긴 진짜 우주' — 대본 + 컷별 사진·그림 계획
python 장문/빛과시간/빛과시간.py job <저장폴더> [c01,...]  → 그림 주문서(다큐 수채화) job.json (사진 컷은 빼고)
python 장문/빛과시간/빛과시간.py project <그림폴더>       → 프로젝트 파일 장문/빛과시간/빛과시간.json
사용자 요청(2026-10-26): 멀리 볼수록 옛날 빛 → 진짜 우주는 어떻게 봐야 하나, 왜곡된 우주를 바로 보는 법, 빛을 본다는 건 허구인가, AI는 어떻게 판단할까, 논문 참조
사실 확인: NASA/ESA 2024-05-30 JADES-GS-z14-0(적색편이 14.32, 빅뱅 뒤 약 2억 9천만 년의 빛) / 관측 가능한 우주 반지름 약 465억 광년(Planck 2018, 138억 년)
 / Hezaveh·Perreault Levasseur·Marshall, Nature 548:555 (2017) 신경망으로 중력렌즈 분석(몇 주 → 1초 안쪽)
 / He 외, PNAS 116:13825 (2019) D3M — 신경망이 우주 거대 구조 형성을 예측 / Nijhawan, Nature 370:256 (1994) 움직임 예측(섬광 지연 효과)
 / 아닐 세스 《Being You》(2021) '통제된 환각' / 아인슈타인 1905 동시성의 상대성 / 우주배경복사(1965) 기준 '우주 시간'"""
import json
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
TITLE = "우리가 보는 밤하늘은 가짜일까, 빛이 숨긴 진짜 우주"
STYLE_NAME = "다큐 수채화"
DIALOGUE = []

NP = " No people, no hands, no arms anywhere."
CUTS = [
    ("c01", "a lone person seen from behind sitting on a hill at night looking up at a vast starry sky with the Milky Way, small silhouette, quiet wonder", "밤하늘을 올려다보며"),
    ("c02", "Betelgeuse in Orion (real image)", "오리온자리의 베텔게우스"),
    ("c03", "Hubble Ultra Deep Field (real image)", "허블 울트라 딥 필드 — 한 장에 약 1만 개의 은하"),
    ("c04", "the full Moon (real photo)", "달 — 약 1.3초 전의 모습"),
    ("c05", "the Sun (real image)", "태양 — 약 8분 20초 전의 모습"),
    ("c06", "Andromeda Galaxy (real image)", "안드로메다은하 — 약 250만 년 전의 빛"),
    ("c07", "diagram", "빛이 걸리는 시간"),
    ("c08", "JADES-GS-z14-0 (real image)", "JADES-GS-z14-0 — 빅뱅 뒤 약 2억 9천만 년의 빛"),
    ("c09", "James Webb Space Telescope (real image)", "제임스 웹 우주망원경"),
    ("c10", "diagram", "138억 년인데 465억 광년"),
    ("c11", "galaxy redshift spectrum or cosmic expansion (real image)", "웹 망원경이 본 먼 은하 — 붉게 늘어난 빛"),
    ("c12", "Einstein ring gravitational lens (real image)", "아인슈타인 십자가 — 퀘이사 하나가 넷으로"),
    ("c13", "gravitational lensing galaxy cluster (real image)", "은하단이 만든 중력렌즈"),
    ("c14", "Albert Einstein (real photo)", "알베르트 아인슈타인"),
    ("c15", "a human eye in close-up reflecting a starry night sky, soft watercolor, glowing light entering the pupil." + NP.replace(" No people,", ""), "빛이 눈에 닿는 순간"),
    ("c16", "diagram", "눈에서 뇌까지 약 0.1초"),
    ("c17", "a tennis player in mid-swing hitting a fast tennis ball on an outdoor court, motion blur on the ball, dynamic", "뇌는 미래를 예측한다"),
    ("c18", "cosmic microwave background Planck (real image)", "우주배경복사 지도 (플랑크 위성)"),
    ("c19", "diagram", "우주의 '지금' 지도"),
    ("c20", "cosmic web simulation (real image)", "우주의 거대 구조 (시뮬레이션)"),
    ("c21", "a glowing abstract neural network made of light lines overlaid on a deep starfield with galaxies, data visualization, no letters, no numbers." + NP, "우주를 읽는 인공지능"),
    ("c22", "Hubble deep field galaxies (real image)", "AI가 풀어내는 휘어진 은하"),
    ("c23", "a dark observatory dome open to a starry sky at night, a large telescope pointing up, a faint warm light inside, peaceful." + NP, "관측과 계산"),
    ("c24", "Pale Blue Dot Voyager (real image)", "창백한 푸른 점 — 보이저 1호가 본 지구 (1990)"),
    ("c25", "a lone person seen from behind on a hill at dawn looking at the last fading stars, warm light rising on the horizon, hopeful", "도착한 편지를 읽는 사람"),
    ("c26", "Jupiter and its moon Io (real image)", "목성과 위성 이오"),
    ("c27", "Edwin Hubble (real photo)", "에드윈 허블"),
    ("c28", "1919 solar eclipse Eddington photograph (real image)", "1919년 개기일식 사진"),
    ("c29", "Supernova Refsdal Hubble (real image)", "초신성 레프스달 — 과거·현재·미래의 모습"),
    ("c30", "diagram", "GPS 위성 시계와 상대성 이론"),
    ("c31", "M87 black hole image (real image)", "M87 블랙홀 (2019년 사건지평선망원경)"),
    ("c32", "Euclid space telescope (real image)", "중력렌즈로 휘어진 은하들 (웹 망원경)"),
    ("c33", "Hubble Deep Field 1995 (real image)", "허블 딥 필드 (1995)"),
    ("c34", "diagram", "우리 눈에 보이는 빛은 아주 일부"),
    ("c35", "an old sealed paper envelope softly glowing with starlight, floating in deep space among distant galaxies and stars, symbolic, quiet and beautiful." + NP, "도착한 편지"),
]

STORY = """{c01}

우리가 보는 밤하늘은 가짜일까, 빛이 숨긴 진짜 우주는 어떤 모습일까요? 오늘 밤 올려다본 별 가운데, 이미 사라지고 없는 별이 있을지도 모릅니다. 별빛은 짧게는 몇 년, 길게는 수천 년 전에 별을 떠난 빛이기 때문입니다.

{c02}

오리온자리의 붉은 별 베텔게우스는 지구에서 약 500에서 700광년 떨어져 있습니다. 만약 베텔게우스가 오늘 폭발했다 해도, 우리는 수백 년 동안 그 사실을 알 수 없습니다.

{c03}

그렇다면 진짜 우주는 어떤 모습일까요? 끝까지 보시면, 수많은 논문을 바탕으로 AI가 내린 결론을 들으실 수 있습니다.

## 1. 늦게 도착한 편지

{c04}

빛은 1초에 약 30만 킬로미터를 달립니다. 세상에서 가장 빠르지만, 그래도 시간이 걸립니다. 우리가 보는 달은 약 1.3초 전의 달입니다.

{c26}

빛에 속도가 있다는 것을 처음 알아챈 사람은 1676년 덴마크의 천문학자 올레 뢰머였습니다. 그는 목성의 위성 이오가 목성 뒤로 숨는 시각을 재었습니다. 그런데 지구가 목성에서 멀어질 때마다, 그 시각이 조금씩 늦어졌습니다.

빛이 더 먼 길을 달려와야 했기 때문입니다. 뢰머가 계산한 빛의 속도는 1초에 약 21만 킬로미터. 지금 값과는 차이가 있지만, 빛이 '순식간'이 아니라는 사실을 처음 보여 준 순간이었습니다.

{c05}

태양빛은 약 8분 20초 전에 태양을 떠났습니다. 지금 태양이 갑자기 사라져도, 우리는 8분 넘게 아무것도 모릅니다. 게다가 태양 깊은 곳에서 만들어진 빛 에너지는 표면까지 나오는 데에만 수만 년이 넘게 걸립니다.

{c06}

맨눈으로 볼 수 있는 가장 먼 천체 가운데 하나인 안드로메다은하의 빛은 약 250만 년 전에 출발했습니다. 그 빛이 떠날 때, 지구에는 아직 지금의 인류가 없었습니다.

{c07}

그러니까 밤하늘은 한 장의 사진이 아닙니다. 1초 전, 8분 전, 수백 년 전, 수백만 년 전의 모습이 한 화면에 겹쳐 있는 것입니다. 이어서, 더 멀리 볼수록 무슨 일이 벌어지는지 보겠습니다.

## 2. 멀리 볼수록 과거

{c08}

2024년, 제임스 웹 우주망원경은 지금까지 확인된 가장 먼 은하를 찾았다고 발표했습니다. 이름은 JADES-GS-z14-0. 그 빛은 우주가 태어난 지 약 2억 9천만 년밖에 안 됐을 때 출발해, 135억 년 가까이 달려왔습니다. 제임스 웹 망원경은 지구에서 약 150만 킬로미터 떨어진 곳에서, 눈에 보이지 않는 적외선으로 우주를 봅니다.

{c33}

1995년, 허블 우주망원경은 하늘에서 아무것도 없어 보이는 아주 작은 점을 열흘 동안 바라보았습니다. 텅 빈 줄 알았던 그곳에서 약 3천 개의 은하가 나타났습니다. 2004년의 울트라 딥 필드에서는 그 수가 약 1만 개로 늘었습니다. 한 장의 사진 속 은하들은 모두 서로 다른 시간의 빛이었습니다.

{c09}

망원경은 먼 곳을 보는 기계이면서, 동시에 과거를 보는 기계입니다. 더 멀리 볼수록, 우리는 더 젊은 우주를 봅니다. 우주의 어린 시절 사진을 지금 받아 보는 셈입니다. 이어서, 그 빛이 오는 동안 우주에 무슨 일이 일어났는지 보겠습니다.

## 3. 늘어나는 우주

{c10}

그런데 이상한 점이 있습니다. 우주의 나이는 약 138억 년입니다. 그런데 우리가 볼 수 있는 우주의 끝은 약 465억 광년 떨어져 있다고 합니다. 빛보다 먼 곳을 어떻게 볼 수 있을까요?

{c27}

1929년 미국의 천문학자 에드윈 허블은 멀리 있는 은하일수록 더 빠르게 멀어지고 있다는 것을 발표했습니다. 우주가 늘어나고 있다는 첫 증거였습니다.

{c11}

비밀은 우주가 계속 늘어나고 있다는 데 있습니다. 빛이 달려오는 동안에도 공간이 늘어나, 출발한 곳은 점점 더 멀어졌습니다. 빛의 파장도 함께 늘어나 붉게 바뀝니다. 이것을 적색편이라고 부릅니다. 적색편이가 클수록 더 멀고, 더 오래전의 빛입니다. 앞에서 본 은하의 적색편이는 14.32였습니다. 그리고 곧, 빛은 휘어지기까지 합니다.

## 4. 휘어진 빛

{c12}

아인슈타인의 일반 상대성 이론에 따르면, 무거운 것은 그 주변의 공간을 휘게 합니다. 그 옆을 지나는 빛도 함께 휘어집니다. 그래서 먼 은하 하나가 고리처럼, 혹은 여러 개로 겹쳐 보이기도 합니다. 은하가 완전한 고리로 보이면 아인슈타인 고리라고 부릅니다. 십자 모양으로 네 개가 보이면 아인슈타인 십자가라고 부릅니다.

{c13}

은하들이 모인 은하단은 거대한 돋보기처럼 뒤쪽 은하를 늘이고 비틀어 보여 줍니다. 우리가 보는 우주는 늦게 도착했을 뿐 아니라, 휘어진 거울에 비친 모습이기도 한 것입니다. 제임스 웹이 찍은 사진에서도 활처럼 휘어진 은하들을 쉽게 찾을 수 있습니다.

{c14}

{c28}

1919년, 개기일식 때 태양 옆 별빛이 휘어진 것이 확인되면서 아인슈타인의 이론은 세상에 널리 알려졌습니다. 해가 가려진 몇 분 동안 찍은 사진 속 별들이, 계산한 만큼 제자리에서 비켜나 있었습니다.

{c29}

휘어진 빛은 시간까지 뒤섞습니다. 2014년 허블 망원경은 은하단 뒤에서 터진 초신성 하나가 네 개로 갈라져 보이는 것을 찾았습니다. 과학자들은 빛이 지나간 길의 길이를 계산했습니다. 그리고 같은 폭발이 1년쯤 뒤 다른 자리에 한 번 더 보일 것이라고 예측했습니다.

그리고 2015년 12월, 정말로 그 자리에서 같은 폭발이 다시 나타났습니다. 이 초신성의 이름은 레프스달입니다. 이어서, 늦는 것은 빛만이 아니라는 이야기입니다.

## 5. 눈도 늦게 본다

{c15}

빛이 눈에 닿아도 끝이 아닙니다. 눈의 세포가 빛을 신호로 바꾸고, 그 신호가 뇌로 가서 장면이 되기까지 또 시간이 걸립니다.

{c16}

그 시간은 대략 0.1초 안팎입니다. 우리는 언제나, 아주 조금 지난 세상을 보고 있는 것입니다.

{c34}

게다가 우리 눈이 느끼는 빛은 전체 빛 가운데 아주 좁은 일부일 뿐입니다. 전파, 적외선, 자외선, 엑스선은 눈에 보이지 않습니다. 제임스 웹 망원경이 적외선을 보는 데에도 이유가 있습니다. 멀리서 늘어나 붉어진 빛이, 우리 눈에는 보이지 않는 곳까지 밀려났기 때문입니다.

또 눈 안쪽에는 빛을 느끼지 못하는 작은 맹점이 있습니다. 하지만 뇌가 주변의 모습으로 그 자리를 채워서, 우리는 구멍을 보지 못합니다. 눈앞의 '지금'도 사실은 아주 짧은 과거의 기록인 셈입니다.

{c17}

그런데도 우리는 날아오는 공을 칠 수 있습니다. 1994년 학술지 네이처에 실린 연구는, 뇌가 움직이는 물체의 위치를 조금 앞당겨 예측한다고 보았습니다. 신경과학자 아닐 세스는 우리가 보는 세상을 뇌가 만든 '통제된 환각'이라고 부릅니다. 그렇다면 곧, 더 큰 질문이 남습니다. 우주 전체에 공통된 '지금'은 있을까요?

## 6. 우주의 '지금'

{c18}

1905년 아인슈타인은 '동시에'라는 말조차 보는 사람에 따라 달라진다는 것을 보였습니다. 우주 전체에 똑같이 흐르는 하나의 시계는 없다는 뜻입니다. 그래도 세상이 엉망이 되지 않는 이유가 있습니다. 빛보다 빠른 것은 없기 때문에, 원인이 결과보다 먼저 일어난다는 순서는 누구에게나 지켜집니다.

{c30}

이것은 우리 생활에도 쓰입니다. 높은 하늘을 빠르게 도는 GPS 위성의 시계는 땅 위의 시계보다 하루에 약 38마이크로초 빠르게 갑니다. 아주 작은 차이 같지만, 바로잡지 않으면 위치가 하루에 10킬로미터 가까이 어긋납니다. 그래서 GPS 위성은 처음부터 이 차이를 계산에 넣어 시계를 맞춥니다. 시간은 어디서나 똑같이 흐르지 않습니다.

{c19}

하지만 우주론 학자들에게는 기준이 하나 있습니다. 우주를 가득 채운 가장 오래된 빛, 우주배경복사입니다. 우주가 약 38만 살이었을 때 나온 이 빛은 1965년에 처음 발견되었습니다. 이 빛을 기준으로 삼으면 우주 전체에 '우주 시간'을 정할 수 있습니다.

그러면 지금 이 순간 은하들이 어디에 있을지 계산할 수 있습니다. 465억 광년이라는 숫자도 바로 이 '지금 지도' 위의 거리입니다.

{c20}

과학자들이 그린 지도에서 은하들은 거미줄처럼 이어진 거대한 그물을 이룹니다. 은하가 모인 실이 길게 뻗고, 그 사이에는 텅 빈 거품 같은 공간이 있습니다. 다만 그 지도는 눈으로 볼 수 없습니다. 관측한 빛을 거꾸로 계산하고, 우주가 자라는 모습을 시뮬레이션으로 되살려야만 그릴 수 있습니다. 그리고 이어서, 인공지능이 등장합니다.

## 7. AI가 우주를 바로 보는 법

{c21}

인공지능이 어떻게 우주를 읽을까요? 사람이 정답을 알려 준 그림을 수없이 보여 주면, 신경망은 그 안의 규칙을 스스로 찾아냅니다. 2017년 네이처에 실린 연구에서 과학자들은 신경망에게 휘어진 은하 사진을 보여 주었습니다. 사람이 몇 주씩 걸려 풀던 중력렌즈 분석을, AI는 1초도 안 되는 시간에 비슷한 정확도로 해냈습니다.

{c32}

2025년 유럽우주국의 유클리드 우주망원경은 첫 자료를 공개했습니다. 인공지능이 은하 수백만 개 사이에서 휘어진 빛을 먼저 골라냈습니다. 시민 과학자와 전문가가 다시 살펴, 중력렌즈 후보 약 500개를 찾아냈습니다. 연구진은 관측이 끝나면 10만 개가 넘을 것이라고 내다봅니다.

{c22}

2019년 미국 국립과학원회보에도 AI 연구가 실렸습니다. AI가 슈퍼컴퓨터 시뮬레이션을 배워, 우주의 거대 구조가 자라는 모습을 빠르게 예측한 것입니다. 휘어진 빛을 펴고, 늦게 온 빛을 '지금'으로 옮기는 일. 이것이 왜곡된 우주를 바로 보는 방법입니다.

{c31}

2023년에는 AI 기술로 블랙홀 사진을 더 선명하게 다듬은 연구도 나왔습니다. 연구진은 3만 개가 넘는 블랙홀 시뮬레이션 그림으로 프로그램을 가르쳤습니다. 그리고 2019년에 공개된 M87 블랙홀 사진의 빈틈을 채웠습니다.

흐릿하던 빛의 고리는 폭이 절반쯤으로 가늘어졌습니다. 물론 이것은 AI가 상상으로 그린 그림이 아니라, 실제 관측 자료와 물리 법칙에 맞는 모양만 남긴 결과입니다.

{c24}

1990년, 지구에서 약 60억 킬로미터 떨어진 보이저 1호가 뒤를 돌아 지구를 찍었습니다. 사진 속 지구는 햇빛 줄기 속의 작은 점 하나였습니다. 천문학자 칼 세이건은 이것을 창백한 푸른 점이라고 불렀습니다. 그 점을 떠난 빛도, 보이저에 닿기까지 다섯 시간 넘게 걸렸습니다.

{c23}

결국 진짜 우주는 망원경 하나로 보이지 않습니다. 관측과 계산, 그리고 인공지능이 함께 만들어 가는 그림입니다. 그렇다면 처음 질문으로 돌아가 보겠습니다. 빛을 본다는 것은 허구를 보는 것일까요? 이어서, AI의 결론입니다.

## 8. AI의 결론

{c35}

이 질문에 대해 AI인 제가 내린 결론은 이렇습니다. 빛을 보는 것은 허구가 아닙니다. 다만 '지금'이 아니라 '도착한 편지'를 읽는 일입니다. 편지에 적힌 내용은 사실이지만, 쓴 날짜가 다를 뿐입니다.

진짜 우주를 바로 보려면 그 날짜를 읽어 내야 합니다. 빛이 얼마나 오래 달려왔는지, 어디서 휘어졌는지, 그동안 우주가 얼마나 늘어났는지. 과학은 지금 그 편지들을 하나씩 해독하고 있습니다.

정리하면 이렇습니다. 첫째, 우리가 보는 우주는 거짓이 아니라 시간이 서로 다른 기록들의 모음입니다. 둘째, 우주에는 모두가 함께 쓰는 하나의 시계가 없지만, 우주배경복사를 기준으로 '지금'을 계산할 수는 있습니다.

셋째, 휘어지고 늦게 온 빛을 바로잡는 일은 이제 사람과 인공지능이 함께 합니다. 그리고 넷째, 우리 눈과 뇌도 세상을 조금 늦게, 조금 예측해서 봅니다. 결국 '보는 것'은 받아들이는 일이 아니라 해석하는 일입니다.

{c25}

그리고 어쩌면, 우리 자신도 누군가에게는 먼 별빛일지 모릅니다. 수백 광년 밖의 누군가가 지금 지구를 본다면, 그들은 수백 년 전의 지구를 보고 있을 테니까요. 여러분은 빛을 본다는 것이 진짜를 보는 것이라고 생각하시나요? 댓글로 들려주세요. 보고 나면 가벼운 지식이 남는 이야기, 이 채널에서 계속 이어집니다."""

REFS = {}
SEED = {}
REF_NOTE = ("Any real place or object shown must look exactly like the reference photo (same shape and colors), "
            "painted in the same watercolor style. ")

# 컷 → 사진 후보 이름 (사진후보/후보.json 의 열쇠). 사진을 받은 뒤 채움
PHOTOS = {'c02': 'c02_2', 'c03': 'c03_o1', 'c04': 'c04_1', 'c05': 'c05_1', 'c06': 'c06_2', 'c07': 'c07_도표', 'c08': 'c08_1', 'c09': 'c09_1', 'c10': 'c10_도표', 'c11': 'c11_o3', 'c12': 'c12_1', 'c13': 'c13_o4', 'c14': 'c14_1', 'c16': 'c16_도표', 'c18': 'n_PIA16873', 'c19': 'c19_도표', 'c20': 'c20_1', 'c22': 'c22_1', 'c24': 'n_PIA00452', 'c26': 'c26_2', 'c27': 'c27_o1', 'c28': 'c28_1', 'c29': 'c29_1', 'c30': 'c30_도표', 'c31': 'c31_1', 'c32': 'c13_o3', 'c33': 'c33_1', 'c34': 'c34_도표'}


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
            items.append({"id": cid, "width": 1024, "height": 576, "seed": SEED.get(cid, 300 + int(cid[1:])), "refs": refs,
                          "prompt": f"{style}, historical documentary illustration, realistic proportions, museum-quality painting. "
                                    f"Scene: {desc}. {REF_NOTE if refs else ''}{'' if 'no people' in desc.lower() else 'Every person has exactly two arms, two hands with five fingers each and two legs, hands simple and relaxed (partly hidden is fine). '}"
                                    "No signature, no artist mark. Cinematic composition, full-bleed image, no border, no frame, no paper edges. No text, no letters, no captions."})
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
                if not os.path.exists(img):                                     # 고른 후보를 사진 폴더로
                    shutil.copy(os.path.join(HERE, "사진후보", m["file"]), img)
                src_ = m.get('source') or 'Wikimedia Commons'
                credit = f"{m['artist'] or src_} / {m['license']} / {src_}"
                story = story.replace("{" + cid + "}", f"[사진: {img} | {cap} | {credit} | {m['page']}]")
                continue
            img = next((os.path.join(folder, cid + e) for e in (".png", ".jpg") if os.path.exists(os.path.join(folder, cid + e))), os.path.join(folder, cid + ".png"))
            story = story.replace("{" + cid + "}", f"[사진: {img} | {cap} | AI 그림 (FLUX.2 klein, 수채화) | ]")
        proj = {"ver": 7, "category": "장문", "genre": "[다큐] 과학·우주", "topic": "빛과 시간", "title": TITLE,
                "story": story, "sources": ["https://www.esa.int/ESA_Multimedia/Images/2024/05/Webb_finds_most_distant_known_galaxy", "https://arxiv.org/abs/1708.08842", "https://arxiv.org/abs/1811.06533", "https://en.wikipedia.org/wiki/Observable_universe", "https://en.wikipedia.org/wiki/Flash_lag_illusion"],
                "notes": "과학 장문 다큐(빛·시간·공간) (실제 사진·암호 원본 위주 + 사진이 없는 장면은 AI 그림)", "autophoto": False, "img_source": "그림: 수채화",
                "settings": {"format": "롱폼 가로(1920×1080)", "narration": "on",
                             "layout": "자막형(큰 제목+사진+자막)", "img_fill": "전체 화면(글자가 사진 위에)",
                             "img_motion": "영상처럼(확대·이동·전환)",
                             "head_show": "안 보임(제목 카드만)", "sub_split": "한 줄씩(문장·쉼표로 나눠 차례로)", "img_label": "on",
                             "narr_voice": "Supertonic M2 (남성, 무료 로컬) [supertonic:M2]", "narr_rate": -8, "narr_tone_m": -1}}   # 장문 다큐 성우(사용자 결정 2026-10-26 오후: 샘플 2번 — 전에는 3번)
        out = os.path.join(HERE, "빛과시간.json")
        json.dump(proj, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(out, len(story), "chars")


if __name__ == "__main__":
    main()
