"""장문 고고학 다큐 '외계인 흔적이라던 페루의 구멍 5,200개, 과학이 밝힌 정체는 장부였다' — 대본 + 컷별 사진·그림 계획
python 장문/구멍띠/구멍띠.py job <저장폴더> [c01,...]  → 그림 주문서(다큐 수채화) job.json (사진 컷은 빼고)
python 장문/구멍띠/구멍띠.py project <그림폴더>       → 프로젝트 파일 장문/구멍띠/구멍띠.json
사용자 요청(2026-10-27): 밝혀진 미스터리 — 2번 페루 '구멍 띠'(몬테 시에르페), 다음은 1번 모아이
사실 확인: Bongers, Kiahtipes, Beresford-Jones, Osborn, Medrano, Dumitru, Bergmann, Román, Tavera Medina, Tantaleán, Huamán Mesía, Stanish,
 "Indigenous accounting and exchange at Monte Sierpe ('Band of Holes') in the Pisco Valley, Peru", Antiquity 100(409): 145–163
 (2025-11-10 온라인, CC BY 4.0 — 논문 그림 써도 됨, 출처 표시), doi 10.15184/aqy.2025.10237
 - 페루 남부 피스코 계곡, 바다에서 35km, 골짜기 바닥에서 언덕 위로 능선을 따라 약 1.5km, 폭 14~22m(평균 약 19m)
 - 구멍 약 5,200개, 지름 1~2m, 깊이 0.5~1m, 일부는 돌로 벽을 쌓음 / 빈 틈으로 나뉜 구역 60개 이상
 - 구역 예: 8개씩 9줄 이상 / 7개씩 6줄 + 8개 1줄 = 50개 / 7개·8개가 번갈아 12줄 이상
 - 숯 1점 방사성탄소 연대 1320~1405년(95.4%), 겉에서 후기 중간기·잉카 시대 토기 → 후기 중간기에 만들고 잉카 때까지 씀
 - 흙 시료 21개(구멍 19 + 비교 2): 꽃가루 27종 이상, 옥수수 꽃가루 6곳 이상, 부들 꽃가루 거의 모든 곳(보통 50~100m 밖에 못 날아감 →
   구멍 바닥에 깔았거나 부들로 묶은 짐을 옮김), 버드나무(바구니 재료), 호박 녹말, 목화·고추·고구마일 수 있는 무리
 - 잉카식 키푸 VA 16135(베를린 민족학 박물관, 1900년 무렵 피스코 근처에서 출토): 줄 묶음 80개, 대개 10~12가닥 — 구멍 구역과 닮은 구조(암시)
 - 친차 왕국(1000~1400년): 세금 내는 남자 3만 명 이상 → 인구 10만 명 이상, 어부 1만·농부 1만·장인과 상인 6천, 새똥 거름(구아노)
 - 위치: 옛길이 만나는 곳, 잉카 행정 중심지 탐보 콜로라도와 리마 라 비에하 사이, 바닷가와 산지 사이(차우피융가)
 - 옛 가설: 방어·물 모으기·안개 모으기·무덤·광산·텃밭·지상화·저장(Hyslop 1984)·회계와 임시 저장(Stanish·Tantaleán 2015), 외계인설은 논문이 분명히 부정
 - 1930년대 초 셔피-존슨 항공 탐사 사진을 1933년 내셔널 지오그래픽이 실음
 - 한계: 연대는 숯 1점뿐, 구역 경계는 일부 주관적, 먼 곳 물건은 아직 없음(시장이었다면 지역 시장), 지상화일 가능성은 못 뺌, 발굴 필요"""
import json
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
TITLE = "외계인 흔적이라던 페루의 구멍 5,200개, 과학이 밝힌 정체는 장부였다"
STYLE_NAME = "다큐 수채화"
DIALOGUE = []

NP = " No people, no hands, no arms anywhere."
CUTS = [
    ("c01", "real photo", "하늘에서 본 몬테 시에르페 '구멍 띠'"),
    ("c02", "real photo", "페루 남부 피스코 계곡"),
    ("c03", "a 1930s single-engine propeller airplane flying low over barren desert hills in southern Peru, far below on a ridge a long faint band of many small round pits climbs the hill like a snake, hazy morning light, sense of discovery." + NP, "1930년대 항공 탐사 (상상 복원)"),
    ("c04", "real photo", "구멍 띠를 가까이에서"),
    ("c05", "diagram", "구멍 띠의 크기"),
    ("c06", "diagram", "쏟아진 가설들"),
    ("c07", "real photo", "잉카의 창고(콜카)"),
    ("c08", "real photo", "피스코 근처 파라카스의 '촛대' 지상화"),
    ("c09", "paper figure", "하늘에서 본 구멍 띠의 구역"),
    ("c10", "paper figure", "구역마다 줄을 맞춘 구멍 (숫자 = 줄마다 구멍 수)"),
    ("c11", "real photo", "잉카 행정 중심지 탐보 콜로라도"),
    ("c12", "paper figure", "구멍 띠가 놓인 자리 (2 = 몬테 시에르페)"),
    ("c13", "paper figure", "구멍 흙에서 나온 꽃가루 (d = 옥수수, c = 부들)"),
    ("c14", "real photo", "부들"),
    ("c15", "real photo", "안데스 시장의 바구니와 농작물"),
    ("c16", "real photo", "안데스의 호박과 고추"),
    ("c17", "a busy open-air barter gathering on a dry desert ridge in southern Peru around 1350, Indigenous Chincha people in plain ancient Andean cotton tunics, bare heads with long black hair, kneeling and placing woven baskets of maize, squash and cotton down into rows of shallow round pits dug into the bare ground (holes in the earth, not raised), the pits lined with reeds at the bottom, a long band of pits stretching up the hill, warm afternoon light. Every person has exactly two arms and two legs", "구멍 띠의 물물교환 (상상 복원)"),
    ("c18", "paper figure", "구멍 띠 주변의 친차 양식 토기 조각"),
    ("c19", "real photo", "새똥 거름이 쌓인 바예스타스 섬"),
    ("c20", "real photo", "잉카의 매듭 기록, 키푸"),
    ("c21", "real photo", "키푸로 숫자를 읽는 법 (1923년 그림)"),
    ("c22", "an Inca official in an ancient Andean tunic with a geometric pattern and no hat, standing beside rows of shallow round pits dug into a desert ridge, holding up a khipu: one thick main cord with dozens of thin colored strings hanging down from it, each string tied with small knots, workers in plain ancient tunics with bare heads carrying bundles of goods wrapped in reeds into the pits, mountains behind, clear morning light, no modern clothes, no hats, no shorts", "잉카 관리가 세금을 세는 모습 (상상 복원)"),
    ("c23", "real photo", "잉카의 길, 카팍 냔"),
    ("c24", "real photo", "잉카의 키푸 장부를 든 관리 (옛 그림)"),
    ("c25", "real photo", "피스코 계곡의 사막 언덕"),
    ("c26", "a long band of thousands of shallow round pits running up a barren desert ridge in southern Peru at sunset, long shadows inside every pit, quiet and mysterious, wide aerial view." + NP, "해 질 녘의 구멍 띠"),
]

STORY = """{c01}

페루 남부의 메마른 언덕. 산비탈을 따라 이상한 무늬가 길게 이어집니다. 가까이 가 보면 모두 구멍입니다. 사람 키만 한 구멍이 무려 5,200개, 1.5킬로미터에 걸쳐 줄지어 파여 있습니다.

{c02}

누가, 왜 이렇게 많은 구멍을 팠을까요? 100년 가까이 아무도 답하지 못했고, 한때는 외계인의 흔적이라는 말까지 나왔습니다. 그런데 2025년 11월, 국제 고고학 학술지 앤티쿼티에 새로운 답이 실렸습니다. 이 구멍들은 물건을 맞바꾸던 시장이었고, 나중에는 땅 위에 쓴 거대한 장부였다는 것입니다. 오늘은 그 논문을 따라 구멍의 비밀을 하나씩 풀어 보겠습니다. 끝까지 보시면 증거를 모아 인공지능이 내린 결론도 들으실 수 있습니다.

## 1. 하늘에서 발견된 구멍 띠

{c03}

이 구멍들이 세상에 알려진 것은 1930년대 초입니다. 페루 하늘을 날던 항공 탐사대가 사진을 찍었고, 1933년 내셔널 지오그래픽에 실리면서 처음으로 사람들의 눈에 띄었습니다. 현지에서는 이곳을 뱀의 산, 몬테 시에르페라고 부릅니다. 하늘에서 보면 구멍 띠가 언덕을 기어오르는 거대한 뱀처럼 보이기 때문입니다.

{c04}

구멍 하나는 지름이 1미터에서 2미터, 깊이는 50센티미터에서 1미터쯤 됩니다. 어떤 구멍은 안쪽을 돌로 쌓아 벽을 만들었습니다. 띠의 폭은 평균 19미터로, 골짜기 바닥에서 시작해 능선을 따라 언덕 위까지 올라갑니다.

{c05}

바다에서 35킬로미터 떨어진 피스코 계곡. 이곳에 이렇게 큰 공사를 한 사람들은 누구였을까요? 이상하게도 구멍 띠에 대한 옛 기록은 단 한 줄도 남아 있지 않습니다.

## 2. 쏟아진 가설들

{c06}

그래서 온갖 가설이 쏟아졌습니다. 적을 막는 방어 시설이다, 물이나 안개를 모으던 곳이다, 무덤이다, 광산이다, 작은 텃밭이다. 땅에 그린 거대한 그림, 지상화라는 주장도 있었습니다.

{c07}

1984년에는 잉카의 창고였다는 주장이 나왔습니다. 잉카 사람들은 산비탈에 곡식 창고를 줄지어 지었기 때문입니다. 2015년에는 이번 논문의 연구자들이 물건을 세고 잠시 보관하던 회계 장소였을 것이라고 처음 제안했습니다.

{c08}

그리고 인터넷에서는 외계인설이 퍼졌습니다. 근처에 나스카와 파라카스의 거대한 지상화가 있으니, 이 구멍도 외계인이 남긴 것이 아니냐는 것입니다. 하지만 이번 논문은 외계인설을 분명하게 부정합니다. 증거가 가리키는 쪽은 전혀 달랐습니다.

## 3. 드론이 찾아낸 숫자

{c09}

연구팀은 먼저 드론으로 구멍 띠 전체를 아주 자세하게 찍었습니다. 그리고 구멍을 하나하나 세며 지도를 만들었습니다. 그러자 놀라운 사실이 드러났습니다.

{c10}

구멍은 아무렇게나 파인 것이 아니었습니다. 빈 틈을 사이에 두고 60개가 넘는 구역으로 나뉘어 있었고, 구역마다 규칙이 있었습니다. 어떤 구역은 8개씩 9줄, 어떤 구역은 7개씩 6줄에 마지막 줄만 8개여서 꼭 50개였습니다. 7개와 8개가 번갈아 12줄 넘게 이어지는 구역도 있었습니다. 누군가 숫자를 세며 판 것입니다. 구역과 구역 사이의 빈 틈은 사람들이 지나다니던 건널목이었을 수도 있습니다.

{c11}

연대도 확인했습니다. 한 구멍에서 나온 숯을 조사하자 1320년에서 1405년 사이라는 결과가 나왔습니다. 땅 위에서는 잉카 시대 토기 조각도 나왔습니다. 잉카가 오기 전에 만들어져 잉카 시대까지 쓰였다는 뜻입니다.

{c12}

위치도 의미심장했습니다. 구멍 띠는 옛길들이 만나는 곳에 있었습니다. 잉카의 행정 중심지인 탐보 콜로라도와 리마 라 비에하 사이였고, 바닷가와 산지가 만나는 경계였습니다. 바다의 물건과 산의 물건이 오가기에 딱 좋은 자리였던 것입니다. 동쪽으로 1킬로미터쯤 떨어진 곳에는 성벽을 두른 큰 마을 터도 남아 있습니다.

## 4. 구멍 속에 남은 꽃가루

{c13}

결정적인 단서는 구멍 바닥의 흙 속에 있었습니다. 연구팀은 구멍 19개와 비교용 땅 2곳에서 흙을 떠서 현미경으로 들여다봤습니다. 눈에 보이지 않는 꽃가루와 녹말 알갱이를 찾기 위해서였습니다. 그러자 적어도 여섯 곳에서 옥수수 꽃가루가 나왔습니다.

{c14}

더 이상한 것은 부들이었습니다. 물가에서 자라는 풀인 부들의 꽃가루가 거의 모든 구멍에서 나왔습니다. 그런데 부들 꽃가루는 보통 50미터에서 100미터밖에 날아가지 못합니다. 메마른 언덕 위 구멍까지 바람에 실려 왔을 리가 없습니다. 누군가 부들을 구멍 바닥에 깔았거나, 부들로 묶은 짐을 날라 온 것입니다.

{c15}

바구니를 짜는 데 쓰는 버드나무 꽃가루도 나왔습니다. 물건을 바구니에 담고 부들로 묶어 구멍에 넣었다는 그림이 그려집니다.

{c16}

호박의 녹말 알갱이도 나왔고, 목화와 고추, 고구마일 수 있는 식물의 꽃가루도 섞여 있었습니다. 구멍은 비어 있는 구덩이가 아니라, 여러 가지 농작물이 오가던 자리였던 것입니다. 감귤처럼 스페인 사람들이 나중에 들여온 식물의 꽃가루도 두 구멍에서 나왔는데, 연구팀은 이것을 훗날 바람에 섞여 들어온 것으로 봅니다.

## 5. 시장에서 장부로

{c17}

연구팀은 이렇게 해석합니다. 처음 구멍 띠를 만든 것은 이 지역의 친차 왕국이었습니다. 사람들은 저마다 정해진 구멍에 옥수수나 호박, 목화 같은 물건을 담아 와서 서로 맞바꿨습니다. 돈이 없던 시대의 시장이었던 셈입니다.

{c18}

친차 왕국은 생각보다 큰 나라였습니다. 세금을 내는 남자만 3만 명이 넘었고, 인구는 10만 명이 넘었던 것으로 봅니다. 기록에는 어부 1만 명, 농부 1만 명, 장인과 상인 6천 명이 있었다고 전합니다.

{c19}

바닷새의 똥이 쌓인 구아노라는 거름 덕분에 농사도 잘됐습니다. 남는 곡식과 물고기, 바다와 산의 물건을 맞바꿀 장소가 꼭 필요했을 것입니다.

{c20}

그리고 잉카가 이 땅을 차지했습니다. 잉카에는 글자가 없었습니다. 대신 키푸라는 매듭 끈으로 숫자를 기록했습니다. 줄마다 매듭의 위치와 모양으로 숫자를 나타냈고, 이것으로 인구와 세금, 창고의 물건을 셌습니다.

{c21}

놀랍게도 1900년 무렵 바로 이 피스코 근처에서 잉카의 키푸 하나가 나왔습니다. 지금은 독일 베를린의 박물관에 있습니다. 이 키푸는 줄이 80묶음으로 나뉘어 있고, 묶음마다 대개 10가닥에서 12가닥입니다. 구역으로 나뉘고 구역마다 일정한 개수를 가진 구멍 띠와 닮은 구조입니다.

{c22}

연구팀은 잉카 시대에 구멍 띠가 세금으로 걷은 물건을 세고 나누는 장소가 됐다고 봅니다. 각 마을이 정해진 구역의 구멍을 채우면, 관리는 구멍을 세는 것만으로 누가 얼마를 냈는지 한눈에 알 수 있었습니다. 구멍 띠 자체가 땅 위에 쓴 거대한 키푸, 곧 장부였던 것입니다.

{c23}

잉카는 정기적으로 인구를 조사하고, 사람들에게 노동으로 세금을 내게 했습니다. 이런 나라에서 수천 개의 구멍으로 물건을 세는 방법은 아주 쓸모 있었을 것입니다.

## 6. 인공지능의 결론

{c24}

그렇다면 인공지능인 제가 증거들을 모아 내린 결론은 이렇습니다. 첫째, 구멍 띠는 외계인과 아무 관계가 없습니다. 숫자를 세며 판 구역, 길이 만나는 자리, 구멍 속의 옥수수와 부들 꽃가루. 모든 증거가 사람들의 경제 활동을 가리킵니다.

{c25}

둘째, 시장에서 장부로 바뀌었다는 설명이 지금까지 나온 가설 가운데 증거와 가장 잘 맞습니다. 하지만 아직 끝난 이야기는 아닙니다. 연대를 잰 숯은 단 한 점뿐이고, 구역을 나누는 경계도 일부는 연구자의 판단입니다. 먼 지방의 물건은 아직 나오지 않았고, 연구팀도 땅을 직접 파 보는 발굴과 더 많은 연대 측정, 그리고 이 지역에서 나온 다른 키푸에 대한 연구가 더 필요하다고 말합니다.

{c26}

셋째, 이 구멍들이 말해 주는 가장 놀라운 사실은 이것입니다. 글자가 없던 사람들도 땅 위에 숫자를 썼다는 것. 600년 전 사람들은 언덕 하나를 통째로 장부로 만들었습니다. 우리가 외계인의 흔적이라고 오해했던 것은, 사실 사람들의 지혜였습니다. 여러분은 이 구멍 띠의 정체를 어떻게 생각하시나요? 댓글로 들려주세요."""


REFS = {"c17": ["p3d"], "c22": ["p3d"], "c26": ["p3b"]}
SEED = {"c17": 817, "c22": 822}
REF_NOTE = ("Any real place or object shown must look exactly like the reference photo (same shape and colors), "
            "painted in the same watercolor style. ")

# 컷 → 사진 후보 이름 (사진후보/후보.json 의 열쇠). 사진을 받은 뒤 채움
PHOTOS = {}


def main():
    cmd, folder = sys.argv[1], sys.argv[2]
    main_src = os.path.join(ROOT, "..", "shorts_novel_maker_supertonic.py")      # 작업 가지(메인 저장소)의 최신 화풍 목록이 우선
    src = open(main_src if os.path.exists(main_src) else os.path.join(ROOT, "shorts_novel_maker_supertonic.py"), encoding="utf-8").read()
    style = re.search('"' + re.escape(STYLE_NAME) + '": "([^"]+)"', src).group(1)
    only = sys.argv[3].split(",") if len(sys.argv) > 3 else None
    if cmd == "job":
        items = []
        for cid, desc, _ in CUTS:
            if (only and cid not in only) or cid in PHOTOS or "(real photo)" in desc or desc in ("real photo", "diagram", "paper figure"):
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
        proj = {"ver": 7, "category": "장문", "genre": "[다큐] 고고학", "topic": "몬테 시에르페 구멍 띠", "title": TITLE,
                "story": story, "sources": ["https://doi.org/10.15184/aqy.2025.10237", "https://en.wikipedia.org/wiki/Band_of_Holes"],
                "notes": "고고학 장문 다큐(최신 논문) (실제 사진·논문 그림 위주 + 사진이 없는 장면은 AI 그림)", "autophoto": False, "img_source": "그림: 수채화",
                "settings": {"format": "롱폼 가로(1920×1080)", "narration": "on",
                             "layout": "자막형(큰 제목+사진+자막)", "img_fill": "전체 화면(글자가 사진 위에)",
                             "img_motion": "천천히 확대만", "scene_trans": "전진(확대하며 다음 장면)",   # 계속 앞으로 나아가는 느낌(사용자 요청 2026-10-26)
                             "head_show": "안 보임(제목 카드만)", "sub_split": "한 줄씩(문장·쉼표로 나눠 차례로)", "img_label": "on",
                             "narr_voice": "Supertonic M2 (남성, 무료 로컬) [supertonic:M2]", "narr_rate": -8, "narr_tone_m": -1}}   # 장문 다큐 성우(사용자 결정 2026-10-26 오후: 샘플 2번 — 전에는 3번)
        out = os.path.join(HERE, "구멍띠.json")
        json.dump(proj, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(out, len(story), "chars")


if __name__ == "__main__":
    main()
