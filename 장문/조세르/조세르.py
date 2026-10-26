"""장문 고고학 다큐 '외계인이 아니었다, 4,700년 전 피라미드를 들어 올린 물의 힘' — 대본 + 컷별 사진·그림 계획
python 장문/조세르/조세르.py job <저장폴더> [c01,...]  → 그림 주문서(다큐 수채화) job.json (사진 컷은 빼고)
python 장문/조세르/조세르.py project <그림폴더>       → 프로젝트 파일 장문/조세르/조세르.json
사용자 요청(2026-10-26): 최신 논문 기반 고고학 미스터리 1번 — 조세르 피라미드 '수압 엘리베이터'
사실 확인: Landreau·Piton·Morin·Bartout·Touchart 외, "On the possible use of hydraulic force to assist with building the step pyramid of Saqqara",
 PLOS ONE 19(8): e0306690 (2024-08-05, CC BY 4.0) — 기스르 엘 무디르 360×620m = 사방댐, 깊은 도랑(Deep Trench) 칸 = 침전·저류·정수,
 북쪽 수직 통로 ≈28m 깊이·한 변 7m, 남쪽 통로와 약 200m 땅속 통로로 이어짐(라트비아 조사단 2007), 물에 뜬 받침으로 돌을 '화산처럼' 가운데서 올렸을 수 있음(가설)
 피라미드 약 60m, 석회암 230만 개 이상(평균 300kg), 부피 약 33만 ㎥ / 기원전 2670년 무렵(약 4,700년 전)
 / 와디 알 자르프 파피루스(메레르 일지, 2013 피에르 탈레) / 하트누브 채석장 경사로(2018, 이집트 동방고고학연구소·리버풀대)
 / Ghoneim 외, Communications Earth & Environment 5:233 (2024, CC BY) 아흐라마트 지류 약 64km, 피라미드 31개"""
import json
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
TITLE = "외계인이 아니었다, 4,700년 전 피라미드를 들어 올린 물의 힘"
STYLE_NAME = "다큐 수채화"
DIALOGUE = []

NP = " No people, no hands, no arms anywhere."
CUTS = [
    ("c01", "real photo", "조세르의 계단식 피라미드 (사카라)"),
    ("c02", "Pyramid of Djoser (real photo)", "조세르의 계단식 피라미드"),
    ("c03", "real photo", "사카라 — 카이로 남쪽 약 20km"),
    ("c04", "real photo", "높이 약 60m, 여섯 단의 계단"),
    ("c05", "Imhotep statuette (real photo)", "임호텝 (후대의 청동상)"),
    ("c06", "paper figure", "피라미드 아래의 두 수직 통로 (논문 그림)"),
    ("c07", "paper figure", "기스르 엘 무디르 — 위성 사진 (논문 그림)"),
    ("c08", "paper figure", "사카라의 지형과 물길 (논문 그림)"),
    ("c09", "Djoser complex wall (real photo)", "조세르 피라미드 단지의 돌담"),
    ("c10", "real photo", "조세르 피라미드 단지의 돌담과 입구"),
    ("c11", "paper figure", "기스르 엘 무디르 = 사방댐? (논문 그림)"),
    ("c12", "paper figure", "깊은 도랑 — 가라앉히고·모으고·거르는 칸 (논문 그림)"),
    ("c13", "paper figure", "깊은 도랑의 정수 시설 — 연구팀 해석 (논문 그림)"),
    ("c14", "diagram", "물로 돌을 들어 올리는 원리 (연구팀 가설)"),
    ("c15", "paper figure", "가운데서 솟아오르듯 쌓는 '화산식' 건설 (논문 그림)"),
    ("c16", "diagram", "물의 길 (연구팀 가설)"),
    ("c17", "real photo", "조세르 단지 남쪽 무덤의 수직 통로"),
    ("c18", "real photo", "남쪽 무덤 통로 속"),
    ("c19", "Nile felucca (real photo)", "나일강"),
    ("c20", "real photo", "기자의 피라미드들 — 쿠푸 왕 시대"),
    ("c21", "real photo", "대피라미드의 겉돌 — 투라 석회암 (영국박물관)"),
    ("c22", "real photo", "하트누브 채석장 일대"),
    ("c23", "paper figure", "사라진 나일강 지류 '아흐라마트' (논문 그림)"),
    ("c24", "real photo", "다흐슈르의 붉은 피라미드 (옛 사진)"),
    ("c25", "real photo", "기자 피라미드 (1904년 기구에서 찍은 사진)"),
    ("c26", "Giza pyramids (real photo)", "사람이 지은 피라미드"),
    ("c27", "paper figure", "깊은 도랑 첫째 칸 — 깊이 약 27m (논문 그림, 1943년 사진)"),
    ("c28", "Meketre model boat (real photo)", "고대 이집트의 배 모형 (메케트레 무덤)"),
    ("c29", "real photo", "조세르의 계단식 피라미드"),
]

STORY = """{c01}

4,700년 전, 이집트 사막 한가운데에 인류 최초의 거대한 돌 피라미드가 세워졌습니다. 평균 300킬로그램의 석회암 덩어리를 230만 개 넘게 쌓아 올린 건축물입니다. 기중기도 쇠 도구도 없던 시대에, 사람들은 이 돌을 어떻게 들어 올렸을까요?

{c02}

유튜브에는 외계인이 지었다는 이야기가 넘쳐납니다. 하지만 2024년, 프랑스 연구팀이 전혀 다른 답을 내놓았습니다. 돌을 들어 올린 힘은 외계인이 아니라 물이었을지도 모른다는 것입니다. 오늘은 국제 학술지 플로스 원에 실린 논문과 최신 연구들을 따라, 이 수수께끼를 차근차근 풀어 보겠습니다. 끝까지 보시면 여러 증거를 바탕으로 인공지능이 내린 결론도 들으실 수 있습니다.

## 1. 인류 최초의 피라미드

{c03}

카이로에서 남쪽으로 약 20킬로미터 떨어진 사카라. 이곳에 이집트 제3왕조의 파라오, 조세르의 계단식 피라미드가 서 있습니다. 기원전 2,670년 무렵에 지어진, 세계에서 가장 오래된 거대 석조 건축물 가운데 하나입니다.

{c04}

높이는 약 60미터. 여섯 개의 단이 계단처럼 쌓여 있습니다. 그 전까지 이집트 왕들은 마스타바라는 납작한 무덤에 묻혔습니다. 조세르의 피라미드는 이 납작한 무덤을 돌로 지어 여러 층으로 포갠 모양입니다.

{c05}

설계자로 전해지는 사람은 재상 임호텝입니다. 그는 훗날 의술과 지혜의 신으로까지 받들어졌습니다. 하지만 임호텝이 어떤 방법으로 돌을 들어 올렸는지는 어디에도 기록이 남아 있지 않습니다.

{c06}

피라미드 아래에는 깊이 약 28미터, 한 변이 약 7미터인 거대한 수직 통로가 있습니다. 바닥에는 화강암으로 만든 왕의 무덤방이 있습니다. 남쪽 무덤에도 비슷한 통로가 있는데, 두 통로는 약 200미터 길이의 땅속 통로로 이어져 있습니다. 피라미드 아래에 파인 통로와 방을 모두 이으면 길이가 약 6.8킬로미터에 이릅니다. 바로 이 통로들이 오늘 이야기의 열쇠입니다.

## 2. 사막의 수수께끼 구조물

{c07}

조세르 피라미드 서쪽 사막에는 오래전부터 고고학자들을 괴롭혀 온 구조물이 있습니다. 기스르 엘 무디르, 아랍어로 '우두머리의 울타리'라는 뜻입니다. 가로 약 360미터, 세로 약 620미터의 거대한 직사각형 돌담인데, 피라미드 단지보다도 큽니다. 담에 쓰인 돌의 양만 피라미드의 3분의 1쯤 됩니다.

{c08}

그런데 이 거대한 돌담 안에는 무덤도, 신전도, 집도 거의 없습니다. 이렇게 큰 담을 왜 쌓았는지, 학자들은 수십 년 동안 답을 찾지 못했습니다.

{c09}

조세르 피라미드 단지 둘레에는 '마른 해자'라고 불리는 거대한 도랑도 있습니다. 그 남쪽에는 바위를 깎아 만든 아주 깊은 도랑이 있습니다. 이 도랑 역시 왜 이렇게 깊게 팠는지 분명하지 않았습니다.

{c10}

자비에 란드로 박사가 이끄는 프랑스 연구팀은 이 구조물들을 전혀 다른 눈으로 보았습니다. 무덤이나 의식 공간이 아니라, 물을 다루는 시설일지 모른다고 생각한 것입니다.

## 3. 물로 돌을 들어 올린다

{c11}

연구팀은 위성 사진과 지형 자료, 그리고 옛날 홍수의 흔적을 분석했습니다. 지금은 메마른 사막이지만, 4,700년 전 이 일대는 지금보다 비가 많았고, 이따금 큰비가 내리면 서쪽 골짜기에서 물이 쏟아졌을 것으로 보았습니다. 실제로 약 1만 1천 년 전부터 5천 년 전까지 사하라는 지금보다 훨씬 습해서, 사막이 아니라 풀이 자라는 초원이었다는 연구가 많습니다.

{c12}

연구팀의 해석은 이렇습니다. 기스르 엘 무디르는 골짜기에서 내려오는 물과 흙을 가두는 사방댐이었다는 것입니다. 물이 이곳에 머무는 동안 무거운 모래와 흙이 바닥에 가라앉습니다.

{c13}

그다음 물은 피라미드 남쪽의 깊은 도랑으로 흘러갑니다. 연구팀은 이 도랑의 칸들을 물을 가라앉히고, 모았다가, 깨끗하게 거르는 정수 시설로 보았습니다. 오늘날 정수장과 비슷한 원리입니다. 흙탕물을 그대로 쓰면 통로 바닥에 진흙이 쌓여 장치가 막히기 때문에, 맑은 물이 꼭 필요했을 것이라는 설명입니다.

{c27}

깊은 도랑의 첫째 칸은 깊이가 약 27미터, 너비는 약 3미터입니다. 벽은 회반죽으로 이음매를 메운 돌로 쌓여 있었습니다. 연구팀은 이것을 물이 새지 않게 만든 흔적으로 보았습니다.

{c14}

이렇게 맑아진 물이 피라미드 아래의 수직 통로로 흘러들었다면 어떻게 될까요? 통로 안에 커다란 받침을 띄우고 그 위에 돌을 올립니다. 물을 채우면 받침이 떠오르면서 돌이 위로 올라갑니다. 물을 빼고 다시 채우기를 되풀이하면 돌을 더 높이 올릴 수 있습니다.

{c15}

연구팀은 피라미드가 가운데에서부터 화산이 솟아오르듯 지어졌을 수 있다고 말합니다. 바깥에서 경사로로 돌을 끌어 올린 것이 아니라, 한가운데 통로로 돌을 들어 올려 사방으로 쌓았다는 것입니다.

{c16}

이 생각이 맞다면, 4,700년 전 이집트인들은 이미 댐과 정수 시설, 그리고 물의 힘으로 움직이는 승강기를 함께 쓴 셈입니다. 외계인의 기술이 아니라, 물의 성질을 꿰뚫어 본 사람들의 기술입니다.

## 4. 학자들의 반론

{c17}

하지만 이 논문은 어디까지나 그럴 수 있다는 가설입니다. 연구팀도 논문 제목에 가능성이라는 말을 넣었습니다. 깊은 도랑과 수직 통로가 실제로 이어져 있었다는 증거는 아직 찾지 못했고, 물에 뜨는 받침 같은 장치도 발견되지 않았습니다.

{c18}

많은 이집트 학자들은 고개를 갸웃합니다. 수직 통로 바닥에는 파라오의 무덤방이 있는데, 그곳을 물에 잠기게 했다는 것이 어색하다는 지적입니다. 그 시절 사카라에 공사에 쓸 만큼 비가 자주 내렸는지도 더 따져 보아야 합니다. 결국 물 승강기는 흥미로운 질문을 던졌을 뿐, 아직 정답으로 확정된 것은 아닙니다. 다만 연구팀은 땅속을 더 조사하면 확인할 수 있는 예측을 내놓았습니다. 맞는지 틀리는지 직접 따져 볼 수 있다는 점에서, 외계인 이야기와는 전혀 다른 과학입니다.

## 5. 땅이 남긴 다른 증거들

{c19}

그렇다면 피라미드를 지은 사람들은 정말 물을 잘 다뤘을까요? 다른 연구들은 분명히 그렇다고 말합니다.

{c20}

2013년, 홍해 바닷가의 와디 알 자르프에서 세계에서 가장 오래된 파피루스 문서가 발견되었습니다. 쿠푸 왕 시대의 감독관 메레르가 쓴 업무 일지입니다. 약 4,500년 전, 대피라미드를 짓던 바로 그 시기의 기록입니다.

{c21}

메레르의 일지에는 그의 일꾼들이 투라 채석장에서 석회암을 배에 싣고, 나일강과 운하를 따라 기자로 날랐다는 기록이 적혀 있습니다. 피라미드의 돌은 물길을 따라 움직였던 것입니다.

{c22}

2018년에는 이집트 동부의 하트누브 채석장에서 약 4,500년 전의 가파른 경사로가 발견되었습니다. 경사로 가운데는 돌을 끄는 길이고, 양옆에는 계단과 나무 기둥 구멍이 있어서, 밧줄을 기둥에 걸어 무거운 돌을 끌어 올렸을 것으로 보입니다.

{c23}

2024년에는 위성 레이더와 땅속 흙 조사로 사라진 나일강의 지류가 확인되었습니다. 연구팀이 아흐라마트 지류라고 이름 붙인 이 물길은 길이가 약 64킬로미터로, 그 옆에 피라미드 31개가 늘어서 있었습니다.

{c24}

사카라의 피라미드들도 이 옛 물길을 따라 서 있습니다. 피라미드를 지은 사람들은 강을 고속도로처럼 이용해 돌과 사람, 식량을 실어 날랐던 것입니다.

{c28}

고대 이집트의 무덤에서는 이렇게 짐과 사람을 싣고 나일강을 오가던 배의 모형도 많이 나왔습니다. 그들에게 물은 길이자 힘이었습니다.

{c25}

기자의 피라미드 근처에서는 일꾼들의 마을과 빵 굽는 곳, 그리고 일꾼들의 무덤도 발견되었습니다. 이들은 노예가 아니라 식량을 받으며 일한 숙련된 일꾼들이었다는 해석이 많습니다.

## 6. 인공지능의 결론

{c26}

그렇다면 인공지능인 제가 증거들을 모아 내린 결론은 이렇습니다. 첫째, 피라미드는 외계인이 아니라 사람이 지었다는 증거가 압도적입니다. 채석장과 경사로, 업무 일지, 일꾼 마을이 모두 남아 있기 때문입니다.

{c29}

둘째, 물 승강기 가설은 흥미롭지만 아직 증명되지 않았습니다. 앞으로 깊은 도랑과 수직 통로의 흙을 분석해 물이 흐른 흔적이 나오는지가 승부를 가를 것입니다. 셋째, 이 가설이 틀리더라도 분명한 사실이 하나 있습니다. 고대 이집트인들은 물의 힘을 누구보다 잘 알았고, 강과 운하로 거대한 건축을 가능하게 했습니다. 4,700년 전 사람들의 지혜를 외계인에게 돌리는 것은, 어쩌면 그들에 대한 실례일지도 모릅니다. 여러분은 물 승강기 가설, 믿을 만하다고 보시나요? 댓글로 들려주세요."""


REFS = {"c01": ["c02_3"], "c29": ["c02_3"]}
SEED = {"c01": 911, "c29": 929}
REF_NOTE = ("Any real place or object shown must look exactly like the reference photo (same shape and colors), "
            "painted in the same watercolor style. ")

# 컷 → 사진 후보 이름 (사진후보/후보.json 의 열쇠). 사진을 받은 뒤 채움
PHOTOS = {'c01': 'c02_1', 'c02': 'c02_3', 'c03': 'c02_4', 'c04': 'c07_1', 'c05': 'c05_1', 'c06': 'c06_논문', 'c07': 'c07_논문', 'c08': 'c08_논문', 'c09': 'c09_논문', 'c10': 'c08_1', 'c11': 'c11_논문', 'c12': 'c12_논문', 'c13': 'c13_논문', 'c14': 'c14_도표', 'c15': 'c15_논문', 'c16': 'c16_도표', 'c17': 'c17_3', 'c18': 'c17_1', 'c19': 'c19_2', 'c20': 'c26_4', 'c21': 'c21_1', 'c22': 'x_hatnub', 'c23': 'c23_논문', 'c24': 'c24_1', 'c25': 'c26_3', 'c26': 'c26_1', 'c27': 'c27_논문', 'c28': 'c28_1', 'c29': 'c04_1'}


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
        proj = {"ver": 7, "category": "장문", "genre": "[다큐] 고고학", "topic": "조세르 피라미드 물 승강기", "title": TITLE,
                "story": story, "sources": ["https://doi.org/10.1371/journal.pone.0306690", "https://doi.org/10.1038/s43247-024-01379-7", "https://en.wikipedia.org/wiki/Diary_of_Merer", "https://en.wikipedia.org/wiki/Pyramid_of_Djoser", "https://en.wikipedia.org/wiki/Gisr_el-Mudir"],
                "notes": "고고학 장문 다큐(최신 논문) (실제 사진·논문 그림 위주 + 사진이 없는 장면은 AI 그림)", "autophoto": False, "img_source": "그림: 수채화",
                "settings": {"format": "롱폼 가로(1920×1080)", "narration": "on",
                             "layout": "자막형(큰 제목+사진+자막)", "img_fill": "전체 화면(글자가 사진 위에)",
                             "img_motion": "천천히 확대만", "scene_trans": "전진(확대하며 다음 장면)",   # 계속 앞으로 나아가는 느낌(사용자 요청 2026-10-26)
                             "head_show": "안 보임(제목 카드만)", "sub_split": "한 줄씩(문장·쉼표로 나눠 차례로)", "img_label": "on",
                             "narr_voice": "Supertonic M2 (남성, 무료 로컬) [supertonic:M2]", "narr_rate": -8, "narr_tone_m": -1}}   # 장문 다큐 성우(사용자 결정 2026-10-26 오후: 샘플 2번 — 전에는 3번)
        out = os.path.join(HERE, "조세르.json")
        json.dump(proj, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(out, len(story), "chars")


if __name__ == "__main__":
    main()
