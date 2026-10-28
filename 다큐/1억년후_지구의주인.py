"""과학 다큐 '1억 년 후, 지구의 주인은 누구일까' — 대본 + 컷별 그림 계획
python 다큐/1억년후_지구의주인.py job <저장폴더>   → 그림 주문서(klein_worker 용) job.json
python 다큐/1억년후_지구의주인.py project <그림폴더> → 프로젝트 파일(render_project 용) 다큐/1억년후_지구의주인.json
  영상은 render_project.py <프로젝트> --대본그대로 (손으로 쓴 오프닝·챕터 예고를 AI 가 고쳐 쓰지 않게)
대본의 {컷번호} 자리에 그 컷 그림이 들어감. 1억 년 뒤 모습은 사진이 없으므로 모두 AI 그림(과학 예측을 그대로)
사실 근거: 대륙 이동 속도(아프리카 연 2~3cm 북상·호주 연 약 7cm 북상), 달이 멀어지는 속도(연 3.8cm, 아폴로 반사경 측정),
  하루가 길어지는 속도(100년에 약 2밀리초), 태양 밝기(1억 년에 약 1%), 포유류 한 종의 평균 수명(화석 기록상 약 100만 년)"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TITLE = "1억 년 후, 지구의 주인은 누구일까"
GENRE = "지구의 역사와 대멸종"
STYLE = ("scientific documentary illustration, detailed digital painting like a National Geographic or science magazine illustration, "
         "natural realistic colors, clear readable composition, soft cinematic lighting, high detail")

# (컷번호, 그림 설명(영어), 화면 설명(한국어))
CUTS = [
    ("c01", "the Earth seen from orbit, a single globe filling the frame against black space, unfamiliar continent shapes, a mountain range where the Mediterranean Sea used to be, sunrise glow on the horizon", "1억 년 후의 지구"),
    ("c02", "a lush prehistoric Cretaceous landscape with long-necked dinosaurs grazing beside a river under a hazy sky", "1억 년 전, 공룡의 지구"),
    ("c03", "a strange future forest at dusk with unfamiliar alien-looking but plausible plants and small unknown animals silhouetted, mysterious atmosphere, no humans", "주인이 바뀐 미래의 숲"),
    ("c04", "a towering canyon wall of countless colorful rock layers seen from below, representing billions of years of deep time, sunlight on the strata, a tiny hiker at the bottom for scale", "지구 46억 년의 달력"),
    ("c05", "close-up of the very top of a huge cliff of rock layers: only the thin topmost layer of soil holds a single small human footprint, dramatic scale, warm evening light", "달력 마지막 34분의 인류"),
    ("c06", "mid-Cretaceous Earth seen from space 100 million years ago, India as an island in the ocean, a narrow young Atlantic Ocean", "1억 년 전의 대륙"),
    ("c07", "cross-section illustration of Earth's tectonic plates floating on the glowing mantle, arrows of slow movement shown only by shapes, no text", "천천히 움직이는 판"),
    ("c08", "close-up of a human hand with fingernails beside a cracked rock fault line, symbolic comparison of slow growth, soft light", "손톱이 자라는 속도"),
    ("c09", "the African continent slowly pushing north into Europe, the Mediterranean Sea shrinking, satellite view of the future Earth", "유럽으로 밀고 올라가는 아프리카"),
    ("c10", "a colossal new mountain range rising where the Mediterranean Sea once was, snow-capped peaks, ancient ruined stone city half buried in the foothills", "지중해 자리에 솟은 거대한 산맥"),
    ("c11", "the Australian continent drifting north and colliding with Southeast Asian islands, mountains forming at the collision, satellite view", "아시아와 부딪히는 호주"),
    ("c12", "a much wider Atlantic Ocean between America and Africa seen from orbit, vast blue ocean, future Earth", "더 넓어진 대서양"),
    ("c13", "the Korean peninsula and the Japanese islands seen from space in the far future, coastlines slightly changed, the East Sea narrower, mysterious", "한반도 주변의 미래"),
    ("c14", "an artist's view of a future supercontinent forming on Earth seen from space, continents merging together, dramatic lighting", "다시 하나로 모이는 대륙"),
    ("c15", "the Moon rising over a calm ocean, appearing slightly smaller than usual, silver light on the water, night", "조금 작아진 달"),
    ("c16", "Apollo laser reflector panel sitting on the gray lunar surface, a thin green laser beam arriving from distant Earth in the black sky", "달에 놓인 레이저 반사경"),
    ("c17", "a sundial and long shadows at the end of a very long golden sunset, symbolic of a longer day, peaceful landscape", "길어진 하루"),
    ("c18", "the Sun shining slightly brighter and whiter over a hot dry savanna landscape, heat haze, future Earth", "1% 밝아진 태양"),
    ("c19", "a vast ice age landscape with huge glaciers covering northern plains, woolly animals in the distance, cold blue light", "다시 찾아오는 빙하기"),
    ("c20", "a hot humid tropical world: shallow warm sea water flooding low coastal plains and forests, half-drowned palm trees, humid haze, aerial view", "물에 잠긴 해안 평야"),
    ("c21", "a blazing fireball streaking down across the sky toward the horizon above a prehistoric plain, dinosaurs looking up, long fiery trail, the only object in the sky", "공룡을 끝낸 소행성"),
    ("c22", "five layered rock strata in a canyon wall, each layer slightly different color, dramatic geological cross section, no text", "다섯 번의 대멸종이 남긴 지층"),
    ("c23", "a large dark asteroid approaching Earth in space, sunlight on its cratered surface, ominous", "다시 다가올 수 있는 소행성"),
    ("c24", "small shrew-like early mammals hiding among ferns and roots at night while a dinosaur passes in the background", "공룡 시대를 버틴 작은 포유류"),
    ("c25", "a group of brown rats in a ruined overgrown city street, curious and alert, realistic animals, soft morning light", "어디서나 살아남는 쥐"),
    ("c26", "a speculative future rodent descendant, larger and long-legged, running across an open grassland, realistic plausible animal", "쥐의 후손이 커진다면"),
    ("c27", "a flock of colorful birds flying over a strange future landscape, and a large flightless bird walking on the ground, realistic", "공룡의 후손, 새"),
    ("c28", "macro view of insects: ants carrying leaves and a beetle on a branch, rich detail, realistic", "곤충의 끈질긴 생명력"),
    ("c29", "wildlife photograph style: a real common octopus on the sandy sea floor near a coral reef, carrying two halves of a coconut shell with its arms, natural mottled skin, deep blue water with sun rays", "바다의 영리한 문어"),
    ("c30", "scientific microscope image style: rod-shaped and round bacteria cells and green algae cells floating in water, soft translucent colors, electron-microscope-like detail", "35억 년 지구를 지킨 미생물"),
    ("c31", "a deep sea hydrothermal vent with tube worms and microbial mats, black smoke rising, dark blue ocean depths", "가장 깊은 곳의 생명"),
    ("c32", "a lone human figure standing on a hill looking at a city skyline at dusk, seen from behind, contemplative", "인류는 어디에 있을까"),
    ("c33", "fossil skulls of early human species arranged in a row on a museum table, soft light, scientific display without labels", "사라진 인류의 친척들"),
    ("c34", "a cross section of rock layers deep underground with a thin dark layer containing fragments of plastic, concrete, glass and small bones, geology illustration", "땅속에 남을 인류의 얇은 지층"),
    ("c35", "a ruined skyscraper completely overgrown by forest and vines, collapsing into the earth, far future", "숲에 묻혀 가는 도시"),
    ("c36", "NASA Voyager space probe in deep space: a large white parabolic dish antenna facing forward, a small ten-sided body behind it, long thin booms sticking out, a small gold disc mounted on the side, distant stars, accurate historical spacecraft", "우주를 떠도는 보이저호"),
    ("c37", "close-up of a plain shiny gold disc like a gramophone record with fine circular grooves, glinting in starlight against black space, smooth surface", "금빛 레코드"),
    ("c38", "a gentle intelligent furry animal descended from rodents, standing upright with small hands, carefully brushing dirt from a rock layer and holding up a faded piece of old plastic, curious soft eyes, warm sunset light, natural wildlife look", "우리 흔적을 발견할 미래의 누군가"),
    ("c39", "planet Earth seen from space with unfamiliar continents and a bright blue ocean, life glowing green on the land, hopeful", "여전히 살아 있는 지구"),
    ("c40", "a sunrise over a strange but beautiful future landscape with new forests and rivers, warm golden light, no humans", "1억 년 후의 새벽"),
]

STORY = """{c01}

1억 년 후, 지구의 주인은 누구일까요? 1억 년 전 이 별의 주인은 공룡이었습니다. 지금은 우리, 인류입니다.

{c02}

그렇다면 1억 년 뒤에는 어떨까요? 놀랍게도 과학자들은 그때의 지구 모습을 꽤 구체적으로 짐작하고 있습니다. 하루는 더 이상 24시간이 아니고, 지중해는 사라지고, 달은 지금보다 3,800킬로미터 멀어집니다.

{c03}

끝까지 보시면, 1억 년 뒤 지구에 남을 인류의 흔적이 무엇인지, 그리고 다음 주인 후보가 누구인지 알게 되실 겁니다.

## 1. 1억 년이라는 시간

{c04}

먼저 1억 년이 얼마나 긴 시간인지부터 느껴 보겠습니다. 지구가 태어난 지 46억 년, 이 긴 역사를 1년짜리 달력 한 장에 담아 보면 어떨까요. 1월 1일 0시에 지구가 태어나고, 12월 31일 자정이 바로 지금입니다.

{c05}

이 달력에서 1억 년은 약 8일입니다. 그런데 우리 인류, 호모 사피엔스가 나타난 것은 12월 31일 밤 11시 26분쯤입니다. 인류의 역사는 달력의 마지막 34분에 불과합니다. 1억 년은 그 34분을 4천 번 넘게 이어 붙인 시간입니다. 인류가 쌓아 온 모든 역사, 피라미드도, 만리장성도, 스마트폰도 모두 그 짧은 34분 안에 들어 있습니다.

{c06}

1억 년 전으로 돌아가 보면, 그 시간이 얼마나 많은 것을 바꾸는지 알 수 있습니다. 그때 인도는 바다 한가운데 떠 있는 커다란 섬이었고, 대서양은 지금보다 훨씬 좁은 바다였습니다. 그렇다면 앞으로 1억 년 동안에는 땅이 어떻게 바뀔까요? 바로 다음 장에서 보여 드리겠습니다.

## 2. 움직이는 대륙

{c07}

우리가 딛고 선 땅은 사실 움직이고 있습니다. 지구의 겉껍질은 여러 조각의 판으로 나뉘어 있고, 그 판들은 뜨거운 맨틀 위에 떠서 아주 천천히 흘러갑니다.

{c08}

그 속도는 1년에 고작 몇 센티미터, 우리 손톱이 자라는 속도와 비슷합니다. 하지만 1억 년이 쌓이면 이야기가 달라집니다. 1년에 3센티미터씩만 움직여도, 1억 년이면 3천 킬로미터를 갑니다.

{c09}

가장 큰 변화가 일어날 곳은 지중해입니다. 아프리카 대륙은 지금도 1년에 2에서 3센티미터씩 북쪽의 유럽을 향해 밀고 올라가고 있습니다. 과학자들은 앞으로 수천만 년 안에 지중해가 거의 닫혀 버릴 것으로 봅니다.

{c10}

바다가 사라진 자리에는 두 대륙이 부딪치며 거대한 산맥이 솟아오릅니다. 인도가 아시아와 부딪쳐 히말라야를 만든 것과 같은 일입니다. 로마와 아테네가 있던 땅은 높은 산줄기 아래에 묻히게 됩니다.

{c11}

남쪽에서는 호주가 움직입니다. 호주는 1년에 약 7센티미터씩, 대륙 가운데서 가장 빠르게 북쪽으로 달리고 있습니다. 1억 년 뒤에는 동남아시아의 섬들과 부딪쳐 새로운 산맥을 만들 것으로 예상됩니다.

{c12}

반대로 대서양은 계속 넓어집니다. 아메리카와 유럽, 아프리카 사이의 바다는 지금보다 수천 킬로미터 더 벌어질 수 있습니다.

{c13}

그렇다면 한반도는 어떻게 될까요? 한반도는 커다란 유라시아 판 위에 있어서 비교적 덜 움직입니다. 다만 동쪽의 태평양 쪽 판들이 계속 밀고 들어오기 때문에, 일본 열도와의 거리나 동해의 모양이 달라질 수 있다는 예측도 있습니다. 이 부분은 아직 과학자마다 의견이 갈립니다.

{c14}

그리고 이 움직임은 멈추지 않습니다. 과학자들은 2억 년에서 2억 5천만 년 뒤, 지구의 대륙이 다시 하나로 모여 거대한 초대륙이 될 것으로 봅니다. 1억 년 뒤의 지구는 바로 그 길의 중간쯤에 있습니다. 땅만 바뀌는 것이 아닙니다. 하늘도 달라집니다. 이어서 확인해 보겠습니다.

## 3. 달라진 하늘

{c15}

1억 년 뒤의 밤하늘에서는, 달이 지금보다 조금 작아 보일 겁니다. 달은 1년에 3.8센티미터씩 지구에서 멀어지고 있기 때문입니다.

{c16}

이 숫자는 짐작이 아니라 실제로 잰 값입니다. 아폴로 우주인들이 달에 놓고 온 거울에 지구에서 레이저를 쏘고, 빛이 돌아오는 시간을 재서 알아냈습니다. 1억 년이면 달은 지금보다 약 3,800킬로미터 더 멀리 떨어지게 됩니다.

{c17}

달이 멀어지는 동안, 지구의 하루는 길어집니다. 바닷물을 끌어당기는 달의 힘이 지구의 회전에 브레이크를 걸기 때문입니다. 하루는 100년에 약 2밀리초씩 길어지는데, 이것이 1억 년 쌓이면 하루가 약 24시간 40분이 됩니다. 실제로 7천만 년 전, 공룡이 살던 시절에는 하루가 23시간 반쯤이었다는 사실이 그 시대 조개껍데기에 새겨진 성장선에서 밝혀졌습니다. 하루의 길이는 지금도 아주 조금씩 늘어나고 있는 셈입니다.

{c18}

태양도 조금씩 달라집니다. 태양은 나이를 먹을수록 조금씩 밝아져서, 1억 년 뒤에는 지금보다 약 1퍼센트 더 밝게 빛납니다. 작은 숫자 같지만, 지구의 기후를 바꾸기에는 충분한 차이입니다.

## 4. 기후와 바다

{c19}

그사이 지구의 기후는 여러 번 크게 출렁일 겁니다. 지구는 지난 수백만 년 동안 빙하기와 따뜻한 시기를 번갈아 겪어 왔습니다. 두꺼운 얼음이 대륙을 덮었다가, 다시 녹기를 되풀이했습니다.

{c20}

얼음이 녹으면 바다가 높아지고, 얼면 바다가 낮아집니다. 1억 년 동안 해안선은 수없이 바뀌고, 지금의 많은 해안 도시 자리는 몇 번이고 바닷속에 잠겼다가 다시 드러날 겁니다. 그런데 기후보다 훨씬 갑작스럽게 지구의 주인을 바꾸는 사건이 있습니다. 곧 그 이야기를 해 보겠습니다.

## 5. 주인을 바꾼 대멸종

{c21}

6천6백만 년 전, 지름 10킬로미터가 넘는 소행성 하나가 지금의 멕시코 땅에 떨어졌습니다. 하늘은 먼지로 뒤덮였고, 1억 6천만 년 넘게 지구를 다스리던 공룡은 새의 조상을 빼고 모두 사라졌습니다.

{c22}

이런 대멸종은 지구 역사에 크게 다섯 번 있었습니다. 그때마다 그 시대의 주인이 무너지고, 전혀 다른 생물이 새 주인이 되었습니다. 지구의 주인은 언제나 가장 강한 생물이 아니라, 살아남은 생물이었습니다.

{c23}

앞으로 1억 년 동안에도 이런 일이 일어날 수 있습니다. 공룡을 끝낸 것만큼 큰 소행성은 수천만 년에서 1억 년에 한 번꼴로 지구에 떨어지는 것으로 추정됩니다. 1억 년이라는 시간 안에는, 적어도 한 번쯤 큰 충격이 찾아올 가능성이 있습니다. 그렇다면 그 뒤에 살아남아 새 주인이 될 생물은 누구일까요? 바로 다음 장에서 후보들을 만나 보겠습니다.

## 6. 다음 주인 후보들

{c24}

공룡이 사라졌을 때 살아남은 것은 몸집이 작은 동물들이었습니다. 땃쥐만 한 작은 포유류들은 땅속에 숨고, 무엇이든 먹으며 버텼습니다. 그리고 그 후손이 결국 고래와 코끼리, 그리고 우리가 되었습니다.

{c25}

그래서 과학자들이 첫손에 꼽는 후보는 쥐 같은 설치류입니다. 쥐는 작고, 아무거나 먹고, 새끼를 아주 빨리 많이 낳습니다. 사막부터 도시의 하수구까지, 지구 거의 모든 곳에 퍼져 있습니다. 쥐 한 쌍은 좋은 조건에서 1년 만에 수백 마리로 늘어날 수 있습니다. 환경이 바뀌면 그만큼 빨리 적응하고, 빨리 진화할 수 있다는 뜻입니다.

{c26}

큰 동물들이 사라진 세상이라면, 쥐의 후손이 빈자리를 채우며 몸집을 키울 수도 있습니다. 작은 포유류가 6천만 년 만에 고래가 되었듯이, 1억 년은 쥐가 전혀 다른 모습으로 바뀌기에 충분한 시간입니다.

{c27}

두 번째 후보는 새입니다. 새는 사실 대멸종에서 살아남은 공룡의 후손입니다. 한 번 살아남은 경험이 있는 셈이지요. 하늘을 날 수 있어서 멀리 퍼지기도 쉽습니다.

{c28}

세 번째 후보는 곤충입니다. 곤충은 4억 년 가까이 지구에 살며 모든 대멸종을 견뎌 왔습니다. 종류만 해도 수백만 가지에 이릅니다.

{c29}

바다에는 문어가 있습니다. 문어는 도구를 쓰고 미로를 풀 만큼 영리합니다. 다만 수명이 1~2년으로 짧아서, 문명을 만들 만큼 진화할지는 과학자들도 조심스럽게 보고 있습니다.

{c30}

그리고 마지막 후보가 있습니다. 사실 이들은 처음부터 지구의 진짜 주인이었습니다. 바로 눈에 보이지 않는 미생물입니다. 미생물은 35억 년 넘게 지구에 살아왔고, 다섯 번의 대멸종 때도 한 번도 사라지지 않았습니다.

{c31}

햇빛 한 줄기 없는 깊은 바닷속, 끓는 물이 솟는 곳에서도 미생물은 살아갑니다. 1억 년 뒤에도, 그 어떤 재앙이 와도, 미생물은 거의 틀림없이 이 별에 남아 있을 겁니다. 그렇다면 우리 인류는 어떻게 될까요? 이어서 마지막 질문으로 가 보겠습니다.

## 7. 인류는 어디에

{c32}

솔직하게 말하면, 1억 년 뒤에 지금 모습의 인류가 남아 있을 가능성은 낮습니다. 화석 기록을 보면 포유류 한 종은 평균 100만 년 정도 이어지다가 사라지거나 다른 종으로 바뀝니다.

{c33}

실제로 우리와 같은 사람 속에 속했던 네안데르탈인, 데니소바인 같은 친척들은 이미 모두 사라졌습니다. 1억 년 뒤의 인류는 멸종했거나, 우리가 알아볼 수 없을 만큼 다른 존재가 되었거나, 어쩌면 지구를 떠나 다른 별에 살고 있을지도 모릅니다.

{c34}

그렇다면 우리의 흔적은 남을까요? 도시와 건물은 대부분 무너지고 흙에 묻힙니다. 하지만 땅속 깊은 곳에는 아주 얇은 한 겹의 지층이 남을 겁니다. 플라스틱과 콘크리트 조각, 유리, 그리고 엄청나게 많은 닭 뼈가 섞인 이상한 층입니다. 닭 뼈라니 의외지요. 사람들은 해마다 수백억 마리의 닭을 기르고 먹습니다. 그래서 과학자들은 미래의 화석 기록에 가장 흔하게 남을 새가 바로 닭일 거라고 말합니다.

{c35}

과학자들은 이 층을 지구 역사에 남을 인류의 표지로 봅니다. 그 두께는 겨우 몇 센티미터에 불과하겠지만, 1억 년 뒤의 누군가가 땅을 파 본다면 이렇게 생각할 겁니다. 여기에 무언가 아주 특별한 생명이, 아주 잠깐 살았구나 하고요.

{c36}

그리고 지구 밖에는 또 하나의 흔적이 있습니다. 1977년에 떠난 우주 탐사선 보이저호입니다. 보이저호는 지금도 태양계 바깥 깊은 우주를 날아가고 있습니다.

{c37}

보이저호에는 금빛 레코드 한 장이 실려 있습니다. 거기에는 지구의 소리와 음악, 그리고 55개 언어로 된 인사말이 담겨 있습니다. 그중에는 우리말 인사도 있습니다. 안녕하세요. 이 레코드는 10억 년을 버티도록 만들어졌습니다. 1억 년 뒤에도, 인류가 남긴 인사는 여전히 우주를 날고 있을 겁니다.

{c38}

어쩌면 1억 년 뒤, 쥐의 후손이든 새의 후손이든, 지구의 새 주인 가운데 누군가가 땅속에서 우리의 얇은 지층을 발견할지도 모릅니다. 그들은 그 플라스틱 조각을 들고, 우리가 어떤 존재였는지 궁금해할까요?

{c39}

1억 년 후, 지구의 주인이 누구일지는 아무도 확실히 말할 수 없습니다. 하지만 한 가지는 분명합니다. 대륙은 움직이고, 하루는 길어지고, 주인은 바뀌어도, 이 푸른 별 위의 생명은 계속 이어질 겁니다.

{c40}

여러분은 1억 년 뒤 지구의 주인이 누구일 거라고 생각하시나요? 댓글로 여러분의 생각을 들려주세요. 지구와 우주의 놀라운 이야기는 이 채널에서 계속 이어집니다."""


def main():
    cmd, folder = sys.argv[1], sys.argv[2]
    if cmd == "job":
        items = [{"id": cid, "width": 1024, "height": 576, "seed": 300 + int(cid[1:]),
                  "prompt": f"{STYLE}. Scene: {desc}. "   # '행성' 같은 낱말을 넣으면 그림에 행성이 떠다님 → 장면에 없는 물건 이름은 쓰지 않음
                            "Cinematic composition, full-bleed image, no border, no frame, no paper edges. No text, no letters, no labels, no numbers."}
                 for cid, desc, _ in CUTS]
        os.makedirs(folder, exist_ok=True)
        json.dump({"items": items}, open(os.path.join(folder, "job.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(len(items), "cuts")
    elif cmd == "project":
        story = STORY
        for cid, _, cap in CUTS:
            story = story.replace("{" + cid + "}", f"[사진: {os.path.join(folder, cid + '.png')} | {cap} | AI 생성 그림 (FLUX.2 klein) | ]")
        proj = {"ver": 7, "category": "장문", "genre": GENRE, "topic": "1억 년 후의 지구", "title": TITLE,
                "story": story, "sources": [], "notes": "과학 예측 다큐. 1억 년 뒤 모습은 AI 그림", "autophoto": False, "img_source": "그림: 사실묘사",
                "settings": {"format": "롱폼 가로(1920×1080)", "narration": "on",   # 새 서버 기본값(나레이션 꺼짐·스크롤형) 대신 장문 설정 그대로
                             "narr_voice": "Supertonic M2 (남성, 무료 로컬) [supertonic:M2]",
                             "layout": "자막형(큰 제목+사진+자막)", "img_fill": "전체 화면(글자가 사진 위에)",
                             "img_motion": "영상처럼(확대·이동·전환)", "fps": "24", "reveal_hit": "off", "reveal_fx": "off",
                             "head_show": "안 보임(제목 카드만)", "sub_split": "한 줄씩(문장·쉼표로 나눠 차례로)", "img_label": "on"}}   # 연재 영상 화면 규칙 (오른쪽 위 그림 설명은 꼭 보임)
        out = os.path.join(HERE, "1억년후_지구의주인.json")
        json.dump(proj, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(out, len(story), "chars")


if __name__ == "__main__":
    main()
