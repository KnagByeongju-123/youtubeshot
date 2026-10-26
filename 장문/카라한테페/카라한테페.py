"""장문 고고학 다큐 '괴베클리 테페는 시작에 불과했다, 1만 1천 년 전 돌에 새긴 이야기' — 대본 + 컷별 사진·그림 계획
python 장문/카라한테페/카라한테페.py job <저장폴더> [c01,...]  → 그림 주문서(다큐 수채화) job.json (사진 컷은 빼고)
python 장문/카라한테페/카라한테페.py project <그림폴더>       → 프로젝트 파일 장문/카라한테페/카라한테페.json
사용자 요청(2026-10-26): 최신 논문 기반 고고학 미스터리 2번 — 카라한 테페
사실 확인(사용자 원문의 '지름 17m 원형 극장'은 확인되는 자료가 없어 쓰지 않음):
 - 1997년 하란대학 바하틴 첼리크가 발견, 괴베클리 테페 동쪽 약 46km, 2019년부터 이스탄불대 네즈미 카룰 교수팀 본격 발굴, 타시 테펠레르(돌 언덕들) 계획의 하나
 - 기원전 약 9,750~9,400년 무렵(약 1만 1천 년 전 이상), 바위를 깎아 만든 건물, T자 기둥 266개 넘게 관찰(2000년 기준), 넓이 약 10헥타르
 - 2021년 발표: 한 건물에서 남근 모양 기둥 11개와 벽에서 튀어나온 사람 머리 조각, 다른 건물에 뱀·여우 조각
 - 2023년 9월: 높이 약 2.3m 앉은 남자 석상(갈비뼈 표시, 의자에 붙어 있음)과 독수리 석상 (괴베클리 테페에서는 색칠된 멧돼지 석상)
 - 2025년: 큰 돌그릇 안 작은 그릇 속에 멧돼지·독수리·여우 작은 조각(약 4cm) 머리를 각각 돌 고리에 넣어 놓은 '가장 오래된 입체 이야기'(카룰, 아키올로지 매거진 2025 10대 발견),
   얼굴을 입체로 새긴 T자 기둥(높이 약 1.3m), 바위를 파서 만든 집 30채 이상
 - 사냥·채집민이 정착(주변에 수백 개의 사냥 함정), 약 1,500년 뒤 농사·가축 흔적 / 괴베클리 테페: 1995년부터 클라우스 슈미트, 2018 유네스코 세계유산"""
import json
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
TITLE = "괴베클리 테페는 시작에 불과했다, 1만 1천 년 전 돌에 새긴 이야기"
STYLE_NAME = "다큐 수채화"
DIALOGUE = []

NP = " No people, no hands, no arms anywhere."
CUTS = [
    ("c01", "real photo", "카라한 테페 — 바위를 깎아 만든 기둥들"),
    ("c02", "real photo", "괴베클리 테페"),
    ("c03", "real photo", "괴베클리 테페의 T자 기둥"),
    ("c04", "real photo", "괴베클리 테페 기둥의 동물 조각"),
    ("c05", "real photo", "튀르키예 샨르우르파 일대"),
    ("c06", "real photo", "카라한 테페 발굴 현장"),
    ("c07", "Neolithic hunter-gatherers carving a T-shaped stone pillar out of limestone bedrock with flint tools on a hill in southeastern Anatolia, around 11,000 years ago, warm evening light, animal skins clothing, realistic", "1만 1천 년 전, 바위를 깎는 사람들 (상상 복원)"),
    ("c08", "real photo", "남근 모양 기둥들과 벽에서 튀어나온 사람 머리"),
    ("c09", "real photo", "기둥들이 서 있는 방"),
    ("c10", "real photo", "카라한 테페의 뱀 조각"),
    ("c11", "real photo", "앉은 남자 석상 (2023년 발견)"),
    ("c12", "real photo", "우르파 사람 — 1993년에 발견된 석상"),
    ("c13", "real photo", "샨르우르파 고고학 박물관"),
    ("c14", "real photo", "멧돼지 조각 (괴베클리 테페)"),
    ("c15", "real photo", "독수리 조각 (괴베클리 테페 '독수리 돌')"),
    ("c16", "real photo", "여우 조각"),
    ("c17", "three tiny carved stone animal figurines, a wild boar, a vulture and a fox, about four centimetres tall, each with its head placed through a small stone ring, sitting inside a small stone bowl nested inside a larger stone vessel, archaeological find on dusty soil, soft museum light, close-up." + NP, "멧돼지·독수리·여우 — 돌 고리에 머리를 넣은 작은 조각 (설명 그림)"),
    ("c18", "a group of Neolithic people sitting on stone benches around a fire inside a round stone building at night, an elder telling a story with raised hands, T-shaped pillars carved with animals glowing in firelight, children listening, mysterious and warm", "이야기를 나누던 사람들 (상상 복원)"),
    ("c19", "real photo", "T자 기둥에 새긴 얼굴 (2025년 발견)"),
    ("c20", "real photo", "사람을 닮은 T자 기둥 — 팔과 손이 새겨진 기둥"),
    ("c21", "real photo", "바위를 파서 만든 집터"),
    ("c22", "real photo", "가젤 — 이들의 주된 사냥감"),
    ("c23", "real photo", "사막연"),
    ("c24", "real photo", "야생 밀"),
    ("c25", "real photo", "괴베클리 테페를 덮은 지붕"),
    ("c26", "real photo", "타시 테펠레르 — 돌 언덕들"),
    ("c27", "real photo", "괴베클리 테페 전경"),
    ("c28", "an ancient T-shaped stone pillar carved with a fox, a boar and a vulture standing on a quiet hill under a starry night sky, distant fading campfire glow, timeless and contemplative." + NP, "돌에 남은 이야기"),
]

STORY = """{c01}

1만 1천 년 전, 아직 농사도, 글자도, 바퀴도 없던 시대. 그런데 튀르키예 남동부의 한 언덕에서는 사람들이 바위를 깎아 거대한 기둥을 세우고, 동물과 사람을 조각하고 있었습니다.

{c02}

많은 분들이 괴베클리 테페라는 이름을 들어 보셨을 겁니다. 인류 최초의 신전이라고 불리는 곳입니다. 그런데 최근 고고학자들은 이렇게 말합니다. 괴베클리 테페는 시작에 불과했다고 말입니다. 오늘은 그 자매 유적, 카라한 테페에서 나온 최신 발견을 따라가 보겠습니다. 끝까지 보시면 여러 증거를 바탕으로 인공지능이 내린 결론도 들으실 수 있습니다.

## 1. 괴베클리 테페의 충격

{c03}

괴베클리 테페는 1995년부터 독일 고고학자 클라우스 슈미트가 본격적으로 발굴했습니다. 높이 5미터가 넘는 T자 모양의 돌기둥들이 둥글게 서 있었고, 그 나이는 무려 1만 1천 년이 넘었습니다. 영국의 스톤헨지보다 6천 년쯤 앞섭니다.

{c04}

기둥에는 여우와 멧돼지, 뱀과 독수리 같은 동물들이 새겨져 있었습니다. 학자들은 큰 충격을 받았습니다. 그때까지는 사람들이 농사를 지어 한곳에 모여 살게 된 뒤에야 큰 건축물을 지었다고 생각했기 때문입니다. 그런데 괴베클리 테페는 농사가 시작되기도 전에 사냥과 채집으로 살던 사람들이 지은 것이었습니다. 슈미트는 이렇게 말했습니다. 먼저 신전이 있었고, 그다음에 도시가 생겼다고 말입니다.

{c05}

괴베클리 테페는 2018년 유네스코 세계유산이 되었습니다. 그런데 이 일대에는 비슷한 유적이 열 곳 넘게 흩어져 있습니다. 튀르키예는 이곳들을 묶어 타시 테펠레르, 우리말로 돌 언덕들이라고 부르며 대규모 발굴을 시작했습니다.

## 2. 자매 유적, 카라한 테페

{c06}

카라한 테페는 괴베클리 테페에서 동쪽으로 약 46킬로미터 떨어진 언덕에 있습니다. 1997년에 처음 알려졌지만, 본격적인 발굴은 2019년 무렵부터 이스탄불대학교 네즈미 카룰 교수팀이 맡았습니다.

{c07}

지금까지 밝혀진 건설 시기는 기원전 9,700년 무렵입니다. 괴베클리 테페와 비슷하거나 더 이를 수도 있습니다. 유적의 넓이는 약 10헥타르. 그런데 지금까지 발굴된 곳은 그중 몇 퍼센트에 불과합니다. 땅 위로 머리를 내민 T자 기둥만 해도 260개가 넘게 확인되었습니다.

{c08}

2021년, 발굴팀은 놀라운 방을 공개했습니다. 바위를 통째로 깎아 만든 방 안에 기둥 11개가 솟아 있었고, 벽 한쪽에서는 사람의 머리 조각이 튀어나와 방 안을 내려다보고 있었습니다.

{c09}

기둥들은 따로 세운 것이 아니라 바닥의 바위를 깎아 남긴 것이었습니다. 1만 1천 년 전 사람들이 금속 도구 하나 없이, 돌로 돌을 깎아 이런 공간을 만들었다는 뜻입니다.

{c10}

다른 건물에서는 뱀과 여우 조각도 나왔습니다. 그리고 이 건물들은 어느 순간 흙과 돌로 일부러 메워졌습니다. 왜 묻었는지는 아직 수수께끼입니다. 다만 그 덕분에 조각들이 1만 년 넘게 고스란히 남을 수 있었습니다.

## 3. 돌로 만든 사람

{c11}

2023년 9월에는 높이 약 2.3미터의 커다란 남자 석상이 나왔습니다. 의자 같은 돌에 앉아 있는 모습인데, 얼굴은 사실적이고, 갈비뼈와 어깨뼈가 깊게 새겨져 있습니다. 석상 옆 낮은 돌 턱에는 돌 접시들과 독수리 석상이 함께 놓여 있었습니다. 이 방이 특별한 의식에 쓰였다는 단서입니다.

{c12}

이 석상은 1993년 샨르우르파 시내에서 발견된 우르파 사람이라는 석상과 비슷합니다. 높이 약 1.8미터의 이 석상은 지금까지 알려진 가장 오래된 실물 크기의 사람 조각으로 꼽힙니다. 학자들은 갈비뼈를 강조한 모습이 죽음을, 앉은 자세와 살아 있는 듯한 얼굴은 산 사람을 떠올리게 한다고 말합니다. 삶과 죽음 사이의 누군가, 어쩌면 조상을 표현한 것일지도 모릅니다.

{c13}

같은 해 괴베클리 테페에서는 색이 칠해진 실물 크기의 멧돼지 석상도 나왔습니다. 1만 1천 년 전 조각에 붉은색과 검은색, 흰색 물감이 남아 있었습니다. 이들은 돌을 깎을 뿐 아니라 색으로 꾸미기까지 했던 것입니다.

## 4. 가장 오래된 입체 이야기

{c14}

그리고 2025년, 카라한 테페에서 세계 고고학계를 놀라게 한 발견이 나왔습니다. 한 건물의 의자 밑을 파 보니, 큰 돌그릇 안에 작은 돌그릇이 들어 있었습니다.

{c17}

작은 그릇 안에는 높이 약 4센티미터의 작은 동물 조각 세 개가 있었습니다. 멧돼지와 독수리, 그리고 여우입니다. 놀랍게도 세 동물은 모두 머리를 작은 돌 고리 안에 넣은 채 놓여 있었습니다.

{c15}

카룰 교수는 이 세 동물이 아무렇게나 놓인 것이 아니라, 일부러 순서를 정해 배치되었다고 봅니다. 그리고 이 세 동물은 기둥에 새겨진 그림에도 자주 나오는 동물들입니다. 같은 자리에서는 독수리와 표범, 여우의 뼈도 함께 나왔습니다. 그 동물들이 이 사람들에게 특별한 의미였다는 뜻입니다.

{c16}

그래서 발굴팀은 이것을 사람이 물건을 배치해 이야기를 전한 가장 오래된 입체 이야기라고 부릅니다. 미국 고고학 잡지 아키올로지는 이 발견을 2025년 세계 10대 고고학 발견의 하나로 꼽았습니다.

{c18}

글자가 없던 시대, 사람들은 이야기를 어떻게 전했을까요? 아마도 모닥불 앞에서 이야기꾼이 들려주었을 것입니다. 카룰 교수는 이런 이야기가 많은 사람을 한데 묶어 주는 힘이었을 것이라고 말합니다. 이 작은 조각들은 그렇게 사라진 신화의 한 장면일지도 모릅니다.

## 5. 기둥은 사람이었다

{c19}

같은 해, 또 하나의 발견이 있었습니다. 높이 약 1.3미터의 T자 기둥에 사람의 얼굴이 입체로 새겨져 있었던 것입니다. 이런 기둥은 처음입니다.

{c20}

사실 괴베클리 테페의 큰 기둥 가운데에는 팔과 손, 허리띠가 새겨진 것들이 있습니다. 그래서 학자들은 T자 기둥의 윗부분이 머리, 기둥이 몸을 나타낸다고 생각해 왔습니다. 얼굴이 새겨진 기둥은 이 생각을 더욱 굳혀 주었습니다. 기둥들은 사람, 어쩌면 조상이나 신을 나타낸 것이었습니다.

{c21}

카라한 테페 주변에서는 바위를 파서 만든 집터도 30채 넘게 나왔습니다. 지름 3미터에서 6미터쯤 되는 둥근 집들로, 화덕과 돌바닥, 저장 공간까지 있었습니다. 이곳은 가끔 모이는 제사터가 아니라, 사람들이 실제로 모여 살던 마을이었던 것입니다.

## 6. 농사보다 먼저 온 것

{c22}

이들은 무엇을 먹고 살았을까요? 뼈와 씨앗을 분석해 보니, 주로 가젤을 사냥하고 콩 종류를 모아 먹었습니다. 유적 주변에서는 짐승을 몰아넣던 함정도 수백 개 발견되었습니다.

{c23}

카룰 교수는 이들이 여전히 사냥과 채집으로 살면서도 한곳에 머물기로 선택한 사람들이었다고 말합니다. 짐승을 쫓아 떠돌지 않고, 함정으로 짐승을 관리하며 정착한 것입니다.

{c24}

그리고 약 1,500년이 지나자 같은 마을에서 농사를 짓고 가축을 기른 흔적이 나타납니다. 이 일대는 세계에서 가장 먼저 밀을 재배한 곳 가운데 하나로도 알려져 있습니다. 1997년 사이언스에 실린 유전자 연구는 오늘날 재배하는 외알밀의 조상이 바로 근처 카라자다으 산의 야생 밀이라는 것을 밝혀냈습니다.

{c25}

그렇다면 순서가 거꾸로였을지도 모릅니다. 사람들이 농사를 지어서 모인 것이 아니라, 먼저 함께 모여 기둥을 세우고 이야기를 나누다가, 많은 사람을 먹이기 위해 농사를 시작했을 수 있다는 것입니다.

## 7. 인공지능의 결론

{c26}

그렇다면 인공지능인 제가 증거들을 모아 내린 결론은 이렇습니다. 첫째, 문명은 농사에서 시작되었다는 오래된 생각은 다시 써야 합니다. 거대한 건축과 예술, 그리고 함께 나누는 이야기가 농사보다 먼저 있었습니다.

{c27}

둘째, 이 발굴은 이제 막 시작되었습니다. 카라한 테페는 겨우 몇 퍼센트만 파냈고, 지금 이 일대 열 곳 가까운 유적에서 약 220명이 발굴하고 있고, 발굴팀은 조사에 50년에서 100년이 걸릴 것이라고 말합니다. 여름에는 기온이 50도를 넘어 새벽 4시부터 일을 시작한다고 합니다. 앞으로 우리가 알고 있는 인류의 역사는 몇 번 더 바뀔지 모릅니다.

{c28}

셋째, 1만 1천 년 전 사람들도 우리와 똑같이 이야기를 사랑했습니다. 글자는 없었지만, 그들은 돌에 이야기를 새겼습니다. 멧돼지와 독수리와 여우가 들려주던 그 이야기는 무엇이었을까요? 여러분은 어떤 이야기였을 것 같나요? 댓글로 들려주세요."""


REFS = {}
SEED = {}
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
        proj = {"ver": 7, "category": "장문", "genre": "[다큐] 고고학", "topic": "카라한 테페", "title": TITLE,
                "story": story, "sources": ["https://en.wikipedia.org/wiki/Karahan_Tepe", "https://archaeology.org/issues/january-february-2026/collection/tales-from-the-neolithic/top-10-discoveries-of-2025/", "https://www.thecollector.com/karahantepe-prehistoric-discovery-necmi-karul-interview/", "https://www.smithsonianmag.com/smart-news/a-human-face-was-carved-into-this-stone-pillar-in-turkey-11000-years-ago-180987489/"],
                "notes": "고고학 장문 다큐(최신 논문) (실제 사진·논문 그림 위주 + 사진이 없는 장면은 AI 그림)", "autophoto": False, "img_source": "그림: 수채화",
                "settings": {"format": "롱폼 가로(1920×1080)", "narration": "on",
                             "layout": "자막형(큰 제목+사진+자막)", "img_fill": "전체 화면(글자가 사진 위에)",
                             "img_motion": "천천히 확대만", "scene_trans": "전진(확대하며 다음 장면)",   # 계속 앞으로 나아가는 느낌(사용자 요청 2026-10-26)
                             "head_show": "안 보임(제목 카드만)", "sub_split": "한 줄씩(문장·쉼표로 나눠 차례로)", "img_label": "on",
                             "narr_voice": "Supertonic M2 (남성, 무료 로컬) [supertonic:M2]", "narr_rate": -8, "narr_tone_m": -1}}   # 장문 다큐 성우(사용자 결정 2026-10-26 오후: 샘플 2번 — 전에는 3번)
        out = os.path.join(HERE, "카라한테페.json")
        json.dump(proj, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(out, len(story), "chars")


if __name__ == "__main__":
    main()
