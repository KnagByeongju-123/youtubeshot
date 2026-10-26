"""장문 고고학 다큐 '신화가 아니었다, 공항 공사장에서 나온 4천 년 전 크레타 미궁' — 대본 + 컷별 사진·그림 계획
python 장문/크레타미궁/크레타미궁.py job <저장폴더> [c01,...]  → 그림 주문서(다큐 수채화) job.json (사진 컷은 빼고)
python 장문/크레타미궁/크레타미궁.py project <그림폴더>       → 프로젝트 파일 장문/크레타미궁/크레타미궁.json
사용자 요청(2026-10-26): 최신 논문 기반 고고학 미스터리 3번 — 크레타 파푸라 언덕 원형 구조물
사실 확인: 그리스 문화부 발표(2024-06-12), AP(2024-06-11), 위키백과 'Papoura Hill Circular Structure'
 - 2024년 6월 카스텔리 새 헤라클리온 국제공항의 레이더 공사 중 파푸라 언덕 꼭대기(해발 약 494m)에서 발견
 - 지름 약 48m, 넓이 약 1,800㎡, 돌로 쌓은 고리 8겹(평균 두께 1.4m, 남은 높이 최대 1.7m)
 - 가운데 '구역 A' 지름 약 15m 원형 건물(안쪽 9m, 네 칸), 바깥 '구역 B' 너비 6.9m 고리를 방사형 벽이 나눔, 좁은 통로로 이어져 '거의 미로 같은 구조'
 - 기원전 2000~1700년 무렵 주로 사용(원궁전 시대), 뒤 시대 토기도 나옴, 동물 뼈 많음 → 제물·잔치 등 공동체 의식 장소로 추정, 용도는 아직 모름
 - 문화부·교통부가 공항보다 유적 보존을 먼저 하기로 함 / 크레타에 같은 시대 비슷한 건물 없음
 - 신화: 미노스 왕, 다이달로스가 지은 미궁, 미노타우로스, 테세우스·아리아드네의 실 / 아서 에번스 1900년 크노소스 발굴
 - 선문자 B 점토판(크노소스)에 '미궁의 여주인'에게 꿀 한 항아리를 바친 기록(da-pu-ri-to-jo po-ti-ni-ja)
 - '라비린토스'가 양날 도끼 '라브리스'에서 왔다는 설(확정 아님) / 2025년 미노아 궁전 유적들 유네스코 세계유산"""
import json
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
TITLE = "신화가 아니었다, 공항 공사장에서 나온 4천 년 전 크레타 미궁"
STYLE_NAME = "다큐 수채화"
DIALOGUE = []

NP = " No people, no hands, no arms anywhere."
CUTS = [
    ("c01", "real photo", "크레타섬"),
    ("c02", "real photo", "테세우스와 미노타우로스 (고대 그리스 잔 그림)"),
    ("c03", "real photo", "크노소스 궁전의 북쪽 입구"),
    ("c04", "real photo", "테세우스와 미노타우로스 (고대 그리스 잔 그림)"),
    ("c05", "real photo", "테세우스와 아리아드네 (빌럼 스트레이커르 그림)"),
    ("c06", "real photo", "미궁 무늬가 새겨진 크노소스 은화"),
    ("c07", "real photo", "아서 에번스 (1907년 초상화)"),
    ("c08", "real photo", "에번스가 다시 세운 크노소스의 기둥"),
    ("c09", "real photo", "크노소스의 돌고래 벽화"),
    ("c10", "real photo", "미노아의 청동 양날 도끼 (아르칼로호리 동굴)"),
    ("c11", "real photo", "선문자 B 점토판"),
    ("c12", "real photo", "헤라클리온 남쪽의 마을"),
    ("c13", "real photo", "카스텔리 공항 부지 일대"),
    ("c14", "real photo", "카스텔리 새 공항 공사 현장"),
    ("c15", "diagram", "지름 약 48m, 돌 고리 8겹"),
    ("c16", "real photo", "미노아 시대의 돌벽과 좁은 공간 (크노소스)"),
    ("c17", "real photo", "크노소스 벽화 '잔을 든 사람'"),
    ("c18", "Minoan people in simple Bronze Age clothing gathered at a large circular stone building on a hilltop at dusk, holding pottery cups and bowls, a fire and an animal offering, a priestess raising her arms, ritual feast, mysterious atmosphere", "산꼭대기의 의식 (상상 복원)"),
    ("c19", "real photo", "황소 머리의 미노타우로스 (고대 그리스 잔 그림)"),
    ("c20", "real photo", "크레타의 미노아 유적"),
    ("c21", "real photo", "크노소스의 옛 돌길"),
    ("c22", "real photo", "공사 중인 카스텔리 공항"),
    ("c23", "real photo", "미궁 무늬 모자이크 (폼페이)"),
    ("c24", "real photo", "크레타의 들판"),
    ("c25", "real photo", "테세우스와 미노타우로스 모자이크 (폼페이)"),
    ("c26", "real photo", "크레타의 바다와 산"),
]

STORY = """{c01}

그리스 신화에는 한 번 들어가면 다시는 나올 수 없는 미궁이 나옵니다. 그 안에는 사람의 몸에 황소의 머리를 한 괴물, 미노타우로스가 갇혀 있었습니다. 수천 년 동안 이 미궁은 상상 속 이야기로만 여겨졌습니다. 그 무대는 지중해 한가운데, 그리스에서 가장 큰 섬인 크레타입니다.

{c02}

그런데 2024년 6월, 크레타섬의 한 언덕에서 새 공항의 레이더 시설을 짓던 중, 4천 년 전의 거대한 원형 돌 구조물이 모습을 드러냈습니다. 안쪽은 좁은 통로로 이어진 방들이 겹겹이 둘러싼, 거의 미로 같은 구조였습니다. 오늘은 그리스 문화부의 발표와 최신 연구를 따라, 신화와 고고학이 만나는 이 수수께끼를 풀어 보겠습니다. 끝까지 보시면 여러 증거를 바탕으로 인공지능이 내린 결론도 들으실 수 있습니다.

## 1. 미궁의 전설

{c03}

신화 속 크레타의 왕 미노스는 바다의 신 포세이돈에게 받은 황소를 제물로 바치지 않았습니다. 화가 난 신은 왕비가 황소를 사랑하게 만들었고, 그렇게 태어난 것이 미노타우로스였습니다.

{c04}

미노스 왕은 뛰어난 장인 다이달로스에게 괴물을 가둘 곳을 만들게 했습니다. 그것이 바로 라비린토스, 미궁입니다. 너무 복잡해서 만든 다이달로스조차 겨우 빠져나왔다고 전해집니다.

{c05}

아테네는 해마다 젊은이들을 제물로 바쳐야 했습니다. 그러다 영웅 테세우스가 스스로 제물이 되어 크레타로 갑니다. 미노스 왕의 딸 아리아드네는 그에게 실타래를 주었고, 테세우스는 실을 풀며 미궁에 들어가 괴물을 물리치고, 실을 따라 다시 빠져나왔습니다. 어려운 문제를 푸는 실마리를 뜻하는 '아리아드네의 실'이라는 말이 여기서 나왔습니다.

{c06}

이 이야기는 크레타 사람들에게도 자랑이었습니다. 고대 크레타의 도시 크노소스는 미궁 무늬를 새긴 동전을 만들기도 했습니다.

## 2. 크노소스, 미궁의 후보

{c07}

1900년, 영국의 고고학자 아서 에번스가 크레타의 크노소스를 발굴하기 시작했습니다. 땅 밑에서 나온 것은 방이 천 개가 넘는다고 할 만큼 복잡한 거대한 궁전이었습니다. 에번스는 땅을 사들여 수십 년 동안 발굴했고, 무너진 기둥과 벽 일부를 콘크리트로 다시 세우기까지 했습니다. 이 복원은 지금도 논란이 됩니다.

{c08}

에번스는 이 궁전을 전설의 왕 미노스의 이름을 따 미노아 문명이라고 불렀습니다. 미노아 문명은 기원전 3천 년 무렵부터 크레타에서 꽃핀 유럽 최초의 문명 가운데 하나입니다. 그러나 기원전 1600년 무렵 근처 산토리니섬의 거대한 화산 폭발을 겪고, 기원전 1450년 무렵부터 궁전들이 잇따라 무너지며 쇠퇴했습니다.

{c09}

궁전의 벽에는 황소와 돌고래, 꽃과 사람들이 화려하게 그려져 있었습니다. 다만 지금 볼 수 있는 벽화 가운데 상당 부분은 작은 조각들을 바탕으로 에번스 시대에 다시 그려 넣은 것입니다. 복도와 계단, 작은 방들이 얽힌 이 궁전을 보고, 많은 사람들은 옛 그리스인들이 이 궁전을 미궁으로 기억한 것이라고 생각했습니다.

{c10}

궁전 곳곳에서는 양날 도끼 그림도 많이 나왔습니다. 이 도끼를 라브리스라고 하는데, 그래서 라비린토스가 '양날 도끼의 집'이라는 뜻이라는 주장도 나왔습니다. 다만 이것은 아직 확정되지 않은 설입니다.

{c11}

더 흥미로운 증거도 있습니다. 크노소스에서 나온 3천 년도 더 된 점토판에, 미궁의 여주인에게 꿀 한 항아리를 바쳤다는 기록이 적혀 있습니다. 이런 점토판들은 원래 굽지 않은 진흙이었는데, 궁전이 불탈 때 함께 구워지는 바람에 오히려 오늘날까지 남을 수 있었습니다. 미궁이라는 말은 신화가 생기기 훨씬 전부터 크레타에 있었던 것입니다. 이 점토판의 글자는 선문자 B라고 하는데, 1952년 영국의 건축가 마이클 벤트리스가 해독해 아주 옛 그리스어라는 것을 밝혀냈습니다. 반면 미노아 사람들이 처음 쓴 선문자 A는 지금까지도 아무도 읽지 못했습니다.

## 3. 공항 공사장의 발견

{c12}

크레타섬의 가장 큰 도시 헤라클리온에서 남동쪽으로 떨어진 카스텔리. 이곳에서는 지금 크레타의 새 국제공항을 짓고 있습니다.

{c13}

2024년 6월, 공항의 레이더 기지를 세우려던 파푸라 언덕 꼭대기에서 공사가 멈췄습니다. 땅속에서 거대한 돌 구조물이 나왔기 때문입니다. 언덕의 높이는 해발 약 494미터. 주변이 훤히 내려다보이는 자리입니다.

{c14}

발굴해 보니 지름이 약 48미터, 넓이는 약 1,800제곱미터에 이르는 원형 구조물이었습니다. 축구장의 4분의 1쯤 되는 크기입니다.

{c15}

구조물은 돌로 쌓은 고리 여덟 겹으로 이루어져 있었습니다. 벽 두께는 평균 1.4미터. 지금 남아 있는 가장 높은 곳은 1.7미터입니다. 가운데에는 지름 약 15미터의 둥근 건물이 있고, 그 안은 네 칸으로 나뉘어 있었습니다.

{c16}

바깥쪽 고리들 사이는 바퀴살처럼 뻗은 벽들이 작은 방으로 나누고 있었습니다. 방들은 좁은 틈으로만 서로 이어져 있었습니다. 그리스 문화부는 이것을 '거의 미로 같은 구조'라고 표현했습니다.

## 4. 이곳은 무엇이었을까

{c17}

구조물은 기원전 2000년에서 1700년 무렵에 주로 쓰였던 것으로 보입니다. 크노소스 같은 첫 궁전들이 세워지던 바로 그 시기입니다. 그 뒤 시대의 토기도 나와, 오랫동안 쓰였다는 것도 알 수 있습니다. 이 무렵 미노아 사람들은 달걀 껍데기처럼 얇고 화려한 토기를 만들 만큼 솜씨가 뛰어났습니다.

{c18}

안에서는 동물 뼈가 많이 나왔습니다. 발굴팀은 이곳이 제물을 바치고, 함께 먹고 마시며 의식을 치르던 공동체의 장소였을 것으로 봅니다. 산꼭대기의 미로 같은 건물에서 사람들은 무엇을 기렸을까요?

{c19}

놀라운 점은 크레타 안에서 같은 시대에 이와 비슷한 건물이 하나도 없다는 것입니다. 원래 지붕이 있었는지, 얼마나 높았는지도 아직 모릅니다. 미노아 사람들에게 황소는 아주 특별한 동물이었습니다. 크노소스 벽화에는 젊은이들이 달려드는 황소의 등을 뛰어넘는 장면까지 그려져 있습니다. 황소 머리의 괴물 이야기가 크레타에서 나온 것은 우연이 아닐지도 모릅니다. 발굴팀은 위로 갈수록 좁아지는 원뿔 모양이나 둥근 지붕이었을 가능성을 이야기합니다.

{c20}

학자들은 크레타 남부의 둥근 돌무덤, 그리고 그리스 본토의 옛 무덤 언덕과 닮은 점이 있다고 말합니다. 오히려 같은 시기 중동 지역의 원형 건물들과 더 닮았다는 분석도 있습니다.

{c21}

그리스 본토 티린스에도 커다란 원형 돌 건물이 있습니다. 바다를 건너 여러 문명이 생각과 기술을 주고받았다는 단서일지도 모릅니다.

## 5. 공항보다 유적

{c22}

발견 직후 그리스 문화부와 교통부는 현장에서 만나 결정을 내렸습니다. 공항 공사보다 이 유적을 발굴하고 지키는 일을 먼저 하기로 한 것입니다. 이 발견은 그해 이탈리아 파에스툼에서 열린 국제 고고학 행사에서 2024년 최고의 고고학 발견으로 상을 받았습니다.

{c23}

그렇다면 이 구조물이 신화 속 미궁이었을까요? 신화에서 미궁은 크노소스에 있었고, 이 구조물은 그보다 수십 킬로미터 떨어진 산꼭대기에 있습니다. 미노타우로스를 가둔 감옥이었다는 증거도 없습니다.

{c24}

하지만 신화는 종종 실제 기억 위에 자랍니다. 좁은 통로와 겹겹의 방, 제물과 의식. 이런 건물들이 크레타 곳곳에 있었다면, 바다 건너 그리스 사람들에게 크레타는 미로의 섬으로 기억되었을지도 모릅니다.

## 6. 인공지능의 결론

{c25}

그렇다면 인공지능인 제가 증거들을 모아 내린 결론은 이렇습니다. 첫째, 파푸라 언덕의 구조물은 신화 속 미궁 그 자체라는 증거는 없습니다. 미노타우로스도, 갇힌 괴물도 없었습니다.

{c26}

둘째, 그러나 4천 년 전 크레타에 미로 같은 구조와 의식이 실제로 있었다는 사실은 분명해졌습니다. 미궁 이야기는 이런 건물과 의식에 대한 오래된 기억이 부풀려진 것일 가능성이 큽니다. 셋째, 이 유적은 이제 막 발굴되기 시작했습니다. 2025년에는 크노소스를 비롯한 미노아 궁전 유적들이 유네스코 세계유산이 되었습니다. 앞으로 지붕의 모양과 쓰임새가 밝혀지면, 신화와 역사 사이의 실타래가 조금 더 풀릴 것입니다. 여러분은 이곳이 미궁 전설의 뿌리였다고 생각하시나요? 댓글로 들려주세요."""


REFS = {}
SEED = {}
REF_NOTE = ("Any real place or object shown must look exactly like the reference photo (same shape and colors), "
            "painted in the same watercolor style. ")

# 컷 → 사진 후보 이름 (사진후보/후보.json 의 열쇠). 사진을 받은 뒤 채움
PHOTOS = {'c01': 'c01_1', 'c02': 'c02_1', 'c03': 'c03_o1', 'c04': 'c02_3', 'c05': 'c05_1', 'c06': 'c06_3', 'c07': 'c07_2', 'c08': 'c08_o2', 'c09': 'c09_1', 'c10': 'c10_2', 'c11': 'c11_o1', 'c12': 'c12_3', 'c13': 'c22_2', 'c14': 'c22_3', 'c15': 'c15_도표', 'c16': 'c08_o3', 'c17': 'c03_2', 'c19': 'c02_4', 'c20': 'c07_3', 'c21': 'c03_3', 'c22': 'c22_4', 'c23': 'c25_2', 'c24': 'c12_4', 'c25': 'c25_1', 'c26': 'c01_2'}


def main():
    cmd, folder = sys.argv[1], sys.argv[2]
    main_src = os.path.join(ROOT, "..", "shorts_novel_maker_supertonic.py")      # 작업 가지(메인 저장소)의 최신 화풍 목록이 우선
    src = open(main_src if os.path.exists(main_src) else os.path.join(ROOT, "shorts_novel_maker_supertonic.py"), encoding="utf-8").read()
    style = re.search('"' + re.escape(STYLE_NAME) + '": "([^"]+)"', src).group(1)
    only = sys.argv[3].split(",") if len(sys.argv) > 3 else None
    if cmd == "job":
        items = []
        for cid, desc, _ in CUTS:
            if (only and cid not in only) or cid in PHOTOS or "(real photo)" in desc or desc in ("diagram", "paper figure"):
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
        proj = {"ver": 7, "category": "장문", "genre": "[다큐] 고고학", "topic": "크레타 파푸라 미궁", "title": TITLE,
                "story": story, "sources": ["https://www.culture.gov.gr/el/Information/SitePages/view.aspx?nID=5276", "https://en.wikipedia.org/wiki/Papoura_Hill_Circular_Structure", "https://apnews.com/article/greece-crete-minoan-labyrinth-airport-radar-c0a20cbe6b4e1d2ffe6d5ce4e6ab43c5", "https://en.wikipedia.org/wiki/Labyrinth"],
                "notes": "고고학 장문 다큐(최신 논문) (실제 사진·논문 그림 위주 + 사진이 없는 장면은 AI 그림)", "autophoto": False, "img_source": "그림: 수채화",
                "settings": {"format": "롱폼 가로(1920×1080)", "narration": "on",
                             "layout": "자막형(큰 제목+사진+자막)", "img_fill": "전체 화면(글자가 사진 위에)",
                             "img_motion": "천천히 확대만", "scene_trans": "전진(확대하며 다음 장면)",   # 계속 앞으로 나아가는 느낌(사용자 요청 2026-10-26)
                             "head_show": "안 보임(제목 카드만)", "sub_split": "한 줄씩(문장·쉼표로 나눠 차례로)", "img_label": "on",
                             "narr_voice": "Supertonic M2 (남성, 무료 로컬) [supertonic:M2]", "narr_rate": -8, "narr_tone_m": -1}}   # 장문 다큐 성우(사용자 결정 2026-10-26 오후: 샘플 2번 — 전에는 3번)
        out = os.path.join(HERE, "크레타미궁.json")
        json.dump(proj, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(out, len(story), "chars")


if __name__ == "__main__":
    main()
