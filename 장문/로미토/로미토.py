"""장문 과학 다큐 '1만 2천 년 전 꼭 껴안고 묻힌 두 사람, DNA가 밝힌 엄마와 딸의 비밀' — 대본 + 컷별 사진·그림 계획
python 장문/로미토/로미토.py job <저장폴더> [c01,...]  → 그림 주문서(다큐 수채화) job.json (사진 컷은 빼고)
python 장문/로미토/로미토.py project <그림폴더>       → 프로젝트 파일 장문/로미토/로미토.json
사용자 요청(2026-10-27): 고대사 최신 연구 과학 미스터리 — 3번 1만 2천 년 전 이중 매장의 희귀 성장 장애
사실 확인: Fernandes, Llanos-Lizcano, Brück, Oberreiter, Özdoğan, Cheronet, Lucci, Beckers, Pétrossians, Coppa, Pinhasi, Daly,
 "A 12,000-Year-Old Case of NPR2-Related Acromesomelic Dysplasia", New England Journal of Medicine 394(5): 513 (2026-01-29), doi 10.1056/NEJMc2513616
 (빈 대학·리에주 대학병원 보도자료, ScienceDaily 2026-02-17, Popular Archaeology)
 - 이탈리아 남부 로미토 동굴(그로타 델 로미토), 후기 구석기, 1963년 발견, 두 사람이 껴안은 채 묻힘(로미토 2가 로미토 1의 품에), 다친 흔적 없음
 - 로미토 2: 키 약 110cm, 팔다리가 뚜렷하게 짧음, 청소년(어른이 됐을 수도), 예전엔 남자로 여김 → 여자
 - 로미토 1: 키 약 145cm(그 시대 평균보다 작음), 어른 여자로 여김 / 둘 다 여자, 1촌 친척 → 엄마와 딸일 가능성이 가장 큼
 - 오랜 논쟁: 성별, 관계, 둘이 작은 까닭이 같은지 / 뼈만으로는 진단 못 함
 - 측두골 추체부(귀 안쪽의 단단한 뼈)에서 고대 DNA → 뼈 성장 유전자 조사 → 오늘날 환자 자료와 비교
 - 로미토 2: NPR2 유전자 변이 두 벌(동형) → 마로토형 선단중간지 이형성증(acromesomelic dysplasia, Maroteaux type) — 아주 드문 유전병, 팔다리가 크게 짧아짐
 - 로미토 1: 같은 변이 한 벌(이형) → 조금 작은 키 / 사람의 유전병을 유전자로 진단한 가장 오래된 사례
 - 무리의 돌봄: 로미토 2가 살아남은 건 먹을 것·이동을 오래 도와준 덕분으로 보임(해석) — 코파
 - 한계: 두 사람뿐, 엄마와 딸은 '가장 그럴듯함', 엄마의 작은 키는 '아마도' 변이 한 벌 때문
 - 일반 사실: 로미토 동굴은 칼라브리아주 파파시데로, 폴리노 산지 / 큰 바위에 새긴 오록스(야생 소) 그림으로 유명 /
   변이 두 벌이면 부모 양쪽에서 하나씩 받음 → 아버지도 한 벌을 가졌을 것(추정)"""
import json
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
TITLE = "1만 2천 년 전 꼭 껴안고 묻힌 두 사람, DNA가 밝힌 엄마와 딸의 비밀"
STYLE_NAME = "다큐 수채화"
DIALOGUE = []

NP = " No people, no hands, no arms anywhere."
CUTS = [
    ("c01", "real photo", "이탈리아 남부 로미토 동굴"),
    ("c02", "an ice age cave shelter under a huge rock overhang in the mountains of southern Italy at dusk, a small campfire, animal-skin tents, misty forested valley below, quiet and ancient." + NP, "1만 2천 년 전 로미토 동굴 (상상 복원)"),
    ("c03", "real photo", "폴리노 산지"),
    ("c04", "real photo", "로미토 동굴 바위의 야생 소 그림"),
    ("c05", "real photo", "후기 구석기 시대의 석기"),
    ("c06", "real photo", "빙하기의 사냥감, 붉은사슴"),
    ("c07", "real photo", "로미토 동굴 유적"),
    ("c08", "real photo", "구석기 시대 무덤에서 나온 물건들 (시베리아 말타)"),
    ("c09", "diagram", "두 사람, 로미토 1과 로미토 2"),
    ("c10", "real photo", "뼈가 자라는 성장판 (현미경 사진)"),
    ("c11", "diagram", "60년 동안의 수수께끼"),
    ("c12", "real photo", "귀 안쪽의 단단한 뼈 (측두골)"),
    ("c13", "real photo", "고대 DNA 실험실"),
    ("c14", "real photo", "DNA 이중 나선"),
    ("c15", "diagram", "DNA가 밝힌 답"),
    ("c16", "real photo", "사람의 염색체"),
    ("c17", "diagram", "변이 두 벌과 한 벌"),
    ("c18", "real photo", "사람의 염색체 46개"),
    ("c19", "Ice Age hunter-gatherers about 12,000 years ago sitting around a campfire under a rock shelter, everyone wears only simple animal fur and hide wraps (no buttons, no pockets, no shirts, no trousers, no boots, bare feet or hide wrappings), a short adult woman gently hugging her teenage daughter of about fifteen who is very small with notably short arms and legs (not a baby, not a toddler), two other women and a man sharing roasted meat on sticks with them, warm firelight, tender mood. Every person has exactly two arms and two legs", "함께 살아간 가족 (상상 복원)"),
    ("c20", "real photo", "빙하기 사람들이 오르내렸을 폴리노 산지"),
    ("c21", "real photo", "샤니다르 동굴"),
    ("c22", "real photo", "사람의 염색체 (현미경 사진)"),
    ("c23", "real photo", "칼라브리아의 산과 계곡"),
    ("c24", "real photo", "선사 시대의 조개 장신구"),
    ("c25", "real photo", "로미토 동굴 가까운 마을, 파파시데로"),
    ("c26", "a quiet rock shelter in the mountains at dawn, soft golden light falling on the stone floor where two small bunches of wild flowers lie, peaceful and tender, no bones, no skeletons." + NP, "1만 2천 년의 품 (상상 복원)"),
]

STORY = """{c01}

이탈리아 남부의 깊은 산속, 커다란 바위 아래 동굴이 있습니다. 1963년, 이 동굴에서 두 사람의 뼈가 발견됐습니다. 한 사람이 다른 한 사람을 꼭 껴안은 채 묻혀 있었습니다. 그리고 품에 안긴 사람은 키가 1미터 남짓, 팔과 다리가 유난히 짧았습니다.

{c02}

두 사람은 누구였을까요? 왜 함께 묻혔고, 왜 이렇게 작았을까요? 60년 넘게 풀리지 않던 이 수수께끼의 답이 2026년 1월, 세계적인 의학 학술지 뉴잉글랜드 저널 오브 메디신에 실렸습니다. 1만 2천 년 된 뼛속 DNA가 두 사람의 정체를 밝혀낸 것입니다. 오늘은 그 연구를 따라 빙하기 끝 무렵의 한 가족 이야기를 들어 보겠습니다. 끝까지 보시면 증거를 모아 인공지능이 내린 결론도 들으실 수 있습니다.

## 1. 빙하기 끝의 동굴

{c03}

이 동굴의 이름은 로미토 동굴입니다. 이탈리아 남부 칼라브리아 지방, 폴리노 산지의 깊은 골짜기에 있습니다. 지금으로부터 약 1만 2천 년 전, 마지막 빙하기가 끝나 가던 무렵 이곳에는 사냥과 채집으로 살아가는 사람들이 머물렀습니다. 동굴 앞 바위 그늘에서는 이 두 사람 말고도 여러 사람의 무덤이 발견됐습니다.

{c04}

로미토 동굴은 바위에 새긴 그림으로도 유명합니다. 커다란 바위에 지금은 멸종한 야생 소, 오록스가 힘찬 선으로 새겨져 있습니다. 유럽 빙하기 미술의 걸작 가운데 하나로 꼽힙니다.

{c05}

이곳 사람들은 돌을 깨뜨려 만든 날카로운 석기로 사냥하고, 고기를 자르고, 가죽을 다듬었습니다. 농사도 마을도 없던 시절, 사람들은 계절을 따라 산과 골짜기를 옮겨 다녔습니다.

{c06}

사슴과 야생 소를 쫓아 가파른 산길을 오르내려야 했습니다. 이 무렵 유럽의 날씨는 따뜻해졌다가 다시 추워지기를 되풀이했습니다. 이런 삶에서는 튼튼한 팔다리가 무엇보다 중요했을 것입니다.

## 2. 껴안은 두 사람

{c07}

1963년, 동굴을 조사하던 고고학자들이 바위 그늘 아래에서 무덤 하나를 찾아냈습니다. 그 안에는 두 사람이 나란히, 아니 한 사람이 다른 사람을 품에 안은 채 누워 있었습니다.

{c08}

두 사람의 뼈에는 다친 흔적이 없었습니다. 사고나 싸움으로 죽은 것은 아니라는 뜻입니다. 누군가 이 두 사람을 정성껏, 서로 껴안은 모습으로 묻어 준 것입니다.

{c09}

연구자들은 두 사람에게 이름을 붙였습니다. 큰 사람은 로미토 1, 품에 안긴 작은 사람은 로미토 2입니다. 로미토 1의 키는 약 145센티미터로, 그 시대 사람들보다 작았습니다. 로미토 2는 약 110센티미터에 불과했습니다.

{c10}

특히 로미토 2는 팔과 다리가 유난히 짧았습니다. 연구자들은 오래전부터 이 아이가 뼈가 제대로 자라지 않는 병을 가졌을 것이라고 짐작했습니다.

## 3. 60년의 수수께끼

{c11}

하지만 풀리지 않는 질문이 많았습니다. 로미토 2는 남자일까요, 여자일까요? 오랫동안 연구자들은 남자아이일 것이라고 생각했습니다. 두 사람은 어떤 사이였을까요? 그리고 둘이 모두 작았던 것은 같은 까닭 때문이었을까요? 뼈의 모양만으로는 어떤 병인지 정확히 말할 수 없었습니다.

{c12}

답을 찾은 열쇠는 귀 안쪽에 있었습니다. 머리뼈 가운데 귀를 감싸는 부분에는 아주 단단하고 촘촘한 뼈가 있습니다. 이 뼈는 수만 년이 지나도 DNA를 비교적 잘 지켜 줍니다. 이 뼈에서 DNA를 뽑는 방법이 2010년대에 널리 쓰이기 시작하면서, 고대 DNA 연구는 크게 달라졌습니다.

{c13}

오스트리아 빈 대학과 벨기에 리에주 대학병원이 이끄는 국제 연구팀은 두 사람의 이 뼈에서 아주 조금씩 DNA를 뽑아냈습니다. 그리고 뼈의 성장에 관련된 유전자들을 하나하나 살펴보고, 오늘날 환자들의 자료와 비교했습니다. 이 연구에는 오스트리아, 벨기에, 이탈리아, 포르투갈의 연구자들이 함께했습니다.

{c14}

DNA는 우리 몸을 만드는 설계도입니다. 설계도의 한 글자만 달라져도 몸이 자라는 방식이 바뀔 수 있습니다. 1만 2천 년 된 설계도를 읽어 내는 일, 불과 얼마 전까지는 상상하기 어려운 일이었습니다. 빈 대학의 론 피나시는 이제 고대 DNA 분석으로 선사 시대 사람에게서 특정한 돌연변이까지 찾아낼 수 있게 됐다고 말합니다.

## 4. DNA가 밝힌 답

{c15}

결과는 놀라웠습니다. 첫째, 두 사람은 모두 여자였습니다. 오랫동안 남자로 알려졌던 로미토 2는 소녀였습니다. 둘째, 두 사람은 1촌 사이, 가장 가까운 가족이었습니다. 연구팀은 엄마와 딸일 가능성이 가장 크다고 봅니다.

{c16}

셋째, 병의 정체도 밝혀졌습니다. 로미토 2는 엔피알 투라는 유전자에 변이가 있었습니다. 이 유전자는 팔다리뼈 끝의 성장판에서 뼈가 길게 자라도록 돕는 아주 중요한 일을 합니다.

{c17}

사람은 모든 유전자를 엄마에게서 한 벌, 아빠에게서 한 벌씩 받습니다. 로미토 2는 고장 난 엔피알 투 유전자를 두 벌 모두 가지고 있었습니다. 그래서 팔과 다리, 특히 아래팔과 종아리, 손발이 크게 짧아지는 아주 드문 유전병을 앓았습니다. 의학에서는 이 병을 처음 보고한 의사의 이름을 따서 마로토형이라고 부릅니다. 엄마인 로미토 1은 같은 변이를 한 벌만 가지고 있었습니다. 변이가 한 벌만 있으면 키가 조금 작아질 수 있습니다. 엄마도 그 시대 사람들보다 작았던 까닭이 바로 이것이었을 것으로 봅니다.

{c18}

딸이 변이를 두 벌 가졌다는 것은 아빠에게서도 한 벌을 받았다는 뜻입니다. 아빠 역시 같은 변이를 하나 가지고 있었을 것으로 추정됩니다. 첫 번째 저자인 포르투갈 코임브라 대학의 다니엘 페르난데스는, 같은 유전자가 엄마와 딸에게 서로 다른 모습으로 나타났다고 설명합니다. 연구팀은 이번 연구가 사람의 유전병을 유전자로 진단한 가장 오래된 사례라고 말합니다.

## 5. 1만 2천 년 전의 돌봄

{c19}

여기서 더 중요한 질문이 남습니다. 팔다리가 짧아 걷고 뛰기가 힘들었을 로미토 2는 어떻게 청소년이 될 때까지 살아남을 수 있었을까요?

{c20}

빙하기 끝의 사냥꾼 무리는 계절마다 험한 산길을 옮겨 다녀야 했습니다. 로미토 2가 혼자 그 길을 따라가기는 어려웠을 것입니다. 연구에 참여한 이탈리아 로마 사피엔차 대학의 알프레도 코파는, 로미토 2가 살아남으려면 무리가 오랫동안 먹을 것과 이동을 도와야 했을 것이라고 말합니다.

{c21}

선사 시대의 돌봄을 보여 주는 흔적은 다른 곳에서도 나왔습니다. 이라크의 샤니다르 동굴에서는 크게 다친 뒤에도 오래 살아남은 네안데르탈인의 뼈가 발견되기도 했습니다. 이 사람은 한쪽 팔을 거의 쓰지 못하고 한쪽 눈도 잘 보이지 않았을 것으로 보이지만, 오랫동안 살았습니다. 아주 먼 옛날부터 사람들은 약한 이를 버리지 않았던 것입니다.

{c22}

연구를 이끈 리에주 대학병원의 에이드리언 데일리는 드문 유전병이 인류의 역사 내내 함께해 왔다고 말합니다. 그리고 옛사람들의 유전병을 연구하면 오늘날의 환자를 알아보는 데도 도움이 될 수 있다고 덧붙입니다.

## 6. 인공지능의 결론

{c23}

그렇다면 인공지능인 제가 증거들을 모아 내린 결론은 이렇습니다. 첫째, 로미토 동굴의 두 사람은 엄마와 딸이었을 가능성이 가장 큽니다. 둘이 작았던 까닭은 같은 유전자의 변이였고, 딸은 두 벌, 엄마는 한 벌을 가졌습니다. 60년 동안의 수수께끼가 DNA로 한꺼번에 풀렸습니다.

{c24}

둘째, 다만 아직 조심할 점도 있습니다. 이 연구는 단 두 사람의 이야기입니다. 엄마와 딸이라는 것도 가장 그럴듯한 해석이고, 무리가 돌봐 주었다는 것도 딸이 살아남았다는 사실에서 나온 추론입니다.

{c25}

셋째, 그래도 분명한 것이 하나 있습니다. 1만 2천 년 전, 누군가 이 두 사람을 서로 껴안은 모습으로 정성껏 묻어 주었습니다. 몸이 남들과 달랐던 딸은 엄마의 품에서, 그리고 무리의 보살핌 속에서 살았습니다.

{c26}

유전자는 병을 남겼지만, 그 무덤은 사랑을 남겼습니다. 여러분은 1만 2천 년 전 이 엄마와 딸이 어떤 삶을 살았을 거라고 생각하시나요? 댓글로 들려주세요."""


REFS = {}
SEED = {"c19": 1219, "c20": 1220}
REF_NOTE = ("Any real place or object shown must look exactly like the reference photo (same shape and colors), "
            "painted in the same watercolor style. ")

# 컷 → 사진 후보 이름 (사진후보/후보.json 의 열쇠). 사진을 받은 뒤 채움
PHOTOS = {"c01": "c01_4", "c03": "c03_2", "c04": "c01_1", "c05": "c05_3", "c06": "c06_1", "c07": "c01_3", "c08": "c08_2", "c09": "c09_도표",
          "c11": "c11_도표", "c13": "c13_1", "c14": "c14_1", "c15": "c15_도표", "c10": "c16_1", "c12": "c12_4", "c16": "c18_2", "c22": "c18_3", "c24": "c24_1", "c17": "c17_도표", "c18": "c18_1",
          "c20": "c03_3", "c21": "c21_4", "c23": "c23_1", "c25": "c07_2"}


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
        proj = {"ver": 7, "category": "장문", "genre": "[다큐] 고고학", "topic": "로미토 동굴 이중 매장", "title": TITLE,
                "story": story, "sources": ["https://doi.org/10.1056/NEJMc2513616", "https://www.sciencedaily.com/releases/2026/02/260217005754.htm"],
                "notes": "고고학 장문 다큐(최신 논문) (실제 사진·논문 그림 위주 + 사진이 없는 장면은 AI 그림)", "autophoto": False, "img_source": "그림: 수채화",
                "settings": {"format": "롱폼 가로(1920×1080)", "narration": "on",
                             "layout": "자막형(큰 제목+사진+자막)", "img_fill": "전체 화면(글자가 사진 위에)",
                             "img_motion": "천천히 확대만", "scene_trans": "전진(확대하며 다음 장면)",   # 계속 앞으로 나아가는 느낌(사용자 요청 2026-10-26)
                             "head_show": "안 보임(제목 카드만)", "sub_split": "한 줄씩(문장·쉼표로 나눠 차례로)", "img_label": "on",
                             "narr_voice": "Supertonic M2 (남성, 무료 로컬) [supertonic:M2]", "narr_rate": -8, "narr_tone_m": -1}}   # 장문 다큐 성우(사용자 결정 2026-10-26 오후: 샘플 2번 — 전에는 3번)
        out = os.path.join(HERE, "로미토.json")
        json.dump(proj, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(out, len(story), "chars")


if __name__ == "__main__":
    main()
