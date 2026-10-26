"""장문 미스터리 다큐 '얼음 속에 사라진 129명, 프랭클린 원정대' — 대본 + 컷별 사진·그림 계획
python 장문/프랭클린/프랭클린_원정대.py job <저장폴더> [c01,...]  → 그림 주문서(다큐 수채화) job.json (사진 컷은 빼고)
python 장문/프랭클린/프랭클린_원정대.py project <그림폴더>       → 프로젝트 파일 장문/프랭클린/프랭클린_원정대.json
사실 확인: Wikipedia 'Franklin's lost expedition'(출발 1845-05-19, 129명, 1845년 7월 말 배핀만 고래잡이배, 비치섬 세 무덤,
빅토리 포인트 쪽지 1847-05-28·1848-04-25, 프랭클린 1847-06-11 사망, 장교 9·선원 15 사망, 1848-04-22 배를 버림, 105명,
레이 1854, 매클린톡 1859, 비티 1984, 2016 하트넬 손톱 연구, 에레버스 2014-09 11m, 테러 2016-09 24m),
Smithsonian 2024-09-26(피츠제임스 DNA, 스텐턴·파크, 워털루대), ExplorersWeb 2026-05-07(네 명 더: 오렌·영·브리전스·페글러, 모두 여섯 명)"""
import json
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
TITLE = "얼음 속에 사라진 129명, 프랭클린 원정대"
STYLE_NAME = "다큐 수채화"
DIALOGUE = []

NP = " No people, no hands, no arms anywhere."
SHIP = ("two 1840s British Royal Navy bomb vessels, three-masted wooden sailing ships with black hulls and a broad pale stripe, "
        "bows reinforced with iron plating")
CUTS = [
    ("c01", f"{SHIP}, locked in endless pack ice under a pale twilight Arctic sky, snow on the rigging, vast frozen silence." + NP, "얼음에 갇힌 두 척의 배"),
    ("c02", "HMS Erebus and Terror painting (real image)", "1845년 출발한 에레버스호와 테러호 (당시 신문 그림)"),
    ("c03", "Sir John Franklin portrait (real image)", "존 프랭클린 경 (1786~1847)"),
    ("c04", "Northwest Passage map (real image)", "북서 항로 (지도)"),
    ("c05", "rows of 1840s hand-soldered tin food cans with plain paper labels stacked on wooden shelves in the dim storeroom of a wooden sailing ship, lantern light, no readable text." + NP, "배에 실은 수천 개의 통조림"),
    ("c06", f"seen from far away across calm grey Arctic water with drifting icebergs, {SHIP}, tiny on the horizon under a midnight sun." + NP, "배핀만, 마지막으로 목격된 모습"),
    ("c07", "Beechey Island graves (real photo)", "비치섬의 세 무덤"),
    ("c08", "Beechey Island landscape (real photo)", "비치섬"),
    ("c09", "HMS Terror trapped in ice painting (real image)", "얼음에 밀려 올라간 테러호 (1837년 다른 탐험 때, 옛 그림)"),
    ("c10", "Victory Point note (real image)", "빅토리 포인트 쪽지의 내용"),
    ("c11", "Francis Crozier portrait (real image)", "테러호 선장 프랜시스 크로지어"),
    ("c12", "John Rae portrait (real image)", "탐험가 존 레이"),
    ("c13", "Lady Jane Franklin portrait (real image)", "제인 프랭클린 (옛 판화)"),
    ("c14", "McClintock Fox ship (real image)", "매클린톡의 수색선 폭스호"),
    ("c15", "They forced the last link painting (real image)", "얼음을 깨며 나아가는 테러호 선원들 (1837년, 옛 그림)"),
    ("c16", "a lonely Arctic gravel beach with three weathered wooden grave markers under a low grey sky, snow patches, cold wind, 1980s research tents in the far distance." + NP, "1984년, 비치섬 조사"),
    ("c17", "Franklin expedition relics (real photo)", "뼈 속 납의 양 (1981년 조사)"),
    ("c18", "a scientist's laboratory bench with a microscope, small labelled sample vials and a printed graph, soft lab light, modern research." + NP, "손톱 속 기록을 읽다"),
    ("c19", "an inuksuk stone landmark on a rocky Arctic shore of King William Island, low tundra, distant sea ice, soft golden light." + NP, "이누이트의 기억"),
    ("c20", "HMS Erebus wreck (real image)", "에레버스호 난파선 위의 캐나다 조사선"),
    ("c21", f"fully underwater scene deep below the sea surface: one single sunken 1840s wooden sailing ship hull resting upright on the muddy sea floor, its masts broken off into short stumps, covered with a little seaweed, small fish, dim cold blue-green water all around, faint light rays from far above. Only one ship." + NP, "테러베이 바닷속의 테러호"),
    ("c22", "a modern ancient-DNA laboratory, a scientist in a white lab coat, face mask, hair net and blue gloves carefully holds a small old molar tooth with tweezers over a clean bench, pipettes and sample tubes, bright clean light", "뼈에서 DNA를 꺼내다"),
    ("c23", "James Fitzjames daguerreotype (real image)", "에레버스호 선장 제임스 피츠제임스 (1845년 사진)"),
    ("c24", "King William Island (real photo)", "원정대 장교 (1845년 출발 직전 사진)"),
    ("c25", "a bleak flat gravel shore of King William Island in the Arctic, scattered pale stones and a broken wooden sledge runner half buried in snow, grey sea ice beyond, low overcast sky." + NP, "얼음 위의 마지막 길"),
    ("c26", "Franklin memorial (real photo)", "원정대 장교 (1845년 출발 직전 사진)"),
    ("c28", "Franklin expedition officers daguerreotypes (real image)", "출발 직전 사진 속 존 프랭클린 (1845년)"),
    ("c27", f"{SHIP}, frozen in ice at dawn, the first warm light touching the ice, a single lantern glowing on deck, hopeful and sad closing image." + NP, "아직 돌아오지 못한 사람들"),
]

STORY = """{c01}

얼음 속에 사라진 129명, 프랭클린 원정대의 이야기는 1845년 5월 영국 템스강 어귀에서 시작됩니다. 최신 장비를 갖춘 두 척의 배가 북극으로 떠났습니다.

{c02}

배에 탄 사람은 모두 129명. 그리고 그 가운데 누구도 돌아오지 못했습니다.

{c28}

배의 이름은 에레버스와 테러. 170년 가까이 지나서야, 바닷속 배와 얼음 위의 뼈가 하나씩 이야기를 꺼내기 시작했습니다. 끝까지 보시면, 과학이 되찾아 준 선원들의 이름을 만나게 됩니다.

## 1. 북서 항로를 찾아서

{c03}

지휘관은 59살의 존 프랭클린 경이었습니다. 이미 북극 탐험을 여러 번 다녀온 노련한 탐험가였습니다. 젊은 시절 북극 육로 탐험에서는 굶주림 끝에 가죽 장화까지 먹으며 살아 돌아와, 장화를 먹은 사람이라고 불리기도 했습니다.

{c04}

목표는 북서 항로. 북아메리카 북쪽의 얼어붙은 바다를 지나 대서양에서 태평양으로 가는 뱃길이었습니다. 많은 탐험가가 도전했지만, 아무도 끝까지 가지 못한 길이었습니다.

{c05}

두 배의 뱃머리는 얼음을 깨도록 철판으로 덧대었고, 기차에 쓰던 증기 기관도 실었습니다. 배에는 난방 장치와 그리고 3년 치 식량이 실려 있었습니다. 수천 개의 통조림도 있었습니다. 당시로서는 가장 잘 준비된 탐험대였습니다.

{c06}

1845년 7월 말, 그린란드 서쪽 배핀만에서 고래잡이배 두 척이 이들을 보았습니다. 그것이 유럽인이 본 마지막 모습이었습니다. 이어서, 그들이 남긴 첫 흔적을 따라가 보겠습니다.

## 2. 얼음에 갇히다

{c07}

첫 겨울을 보낸 곳은 비치섬이었습니다. 이곳에서 세 사람이 숨졌고, 나무 묘비 아래 묻혔습니다. 존 토링턴, 존 하트넬, 윌리엄 브레인. 가장 먼저 숨진 토링턴은 스무 살이었습니다.

{c08}

1846년 여름, 배들은 다시 남쪽으로 나아갔습니다. 그리고 9월, 킹윌리엄섬 앞바다에서 얼음에 갇혔습니다.

{c09}

다음 해 여름이 와도 얼음은 풀리지 않았습니다. 배는 두 번의 겨울을 얼음 속에서 보냈습니다. 그런데 곧, 그들이 남긴 단 한 장의 기록이 발견됩니다.

## 3. 돌무더기 속 쪽지

{c10}

1859년, 수색대는 킹윌리엄섬의 돌무더기 속에서 쪽지 한 장을 찾아냈습니다. 첫 기록은 1847년 5월, 모두 무사하다는 내용이었습니다.

{c10}

하지만 1년 뒤 쪽지 가장자리에 덧붙인 글은 전혀 달랐습니다. 프랭클린은 1847년 6월 11일에 숨졌고, 장교 9명과 선원 15명이 목숨을 잃었다는 것. 그리고 1848년 4월 22일, 배를 버렸다는 것이었습니다.

{c11}

남은 105명은 테러호의 선장 프랜시스 크로지어와 에레버스호의 선장 제임스 피츠제임스를 따라 남쪽 본토의 강을 향해 걷기 시작했습니다. 무거운 보트를 썰매에 싣고, 얼음과 자갈 위를 끌고 가는 길이었습니다. 그러나 이어서, 그들은 하나둘 얼음 위에 쓰러집니다.

## 4. 이누이트가 전한 이야기

{c12}

1854년, 탐험가 존 레이는 이누이트 사람들에게서 충격적인 이야기를 들었습니다. 수십 명의 백인이 굶주림 속에 쓰러졌고, 마지막에는 살아남으려 죽은 동료의 몸에 손을 댔다는 것이었습니다.

{c13}

영국 사회는 이 이야기를 믿으려 하지 않았습니다. 프랭클린의 아내 제인 프랭클린은 직접 돈을 모아 수색대를 보냈습니다. 영국 정부도 큰 상금을 내걸었고, 수십 척의 배가 북극을 누볐습니다. 그 덕분에 북극의 지도가 크게 넓어졌습니다.

{c14}

그 수색대가 바로 쪽지와 함께 보트 한 척과 해골들을 찾아낸 매클린톡 탐험대였습니다. 이누이트의 기억은 그 뒤에도 원정대의 마지막을 알려 주는 가장 중요한 단서가 되었습니다.

{c15}

수많은 수색에도 살아 돌아온 사람은 한 명도 없었습니다. 그렇다면 이들은 왜 이렇게 무너졌을까요? 곧, 과학이 이 질문에 처음 손을 댑니다.

## 5. 납 중독일까

{c16}

1984년, 캐나다의 인류학자 오언 비티 연구팀은 비치섬의 무덤을 조사했습니다. 얼어붙은 땅 속에서 140년 가까이 지난 시신은 놀랄 만큼 잘 보존되어 있었습니다.

{c17}

뼈와 머리카락에서는 많은 양의 납이 나왔습니다. 연구팀은 납땜한 통조림이나 배의 물 공급 장치가 원인일 수 있다고 보았습니다.

{c18}

하지만 이후 연구에서는 다른 결과도 나왔습니다. 2016년 존 하트넬의 손톱을 분석한 연구는, 납 수치가 마지막 몇 주 전까지는 정상이었고 아연 부족과 결핵이 더 큰 원인이었을 수 있다고 보았습니다. 추위와 굶주림, 괴혈병과 병이 한꺼번에 덮쳤을 가능성이 큽니다. 이어서, 바닷속에서 나타난 배의 이야기입니다.

## 6. 바닷속에서 나타난 배

{c19}

배를 찾는 열쇠도 이누이트의 기억이었습니다. 이누이트 역사가 루이 카무칵은 조상들에게서 전해 들은 이야기를 모아 수색에 힘을 보탰습니다.

{c20}

2014년 9월, 캐나다 수색대는 킹윌리엄섬 남쪽 바다 11미터 아래에서 에레버스호를 찾아냈습니다. 가장 먼저 건져 올린 유물은 배의 종이었습니다.

{c21}

2016년에는 테러베이라는 만의 24미터 바닷속에서 테러호가 발견되었습니다. 배는 놀랄 만큼 온전한 모습이었습니다. 창문 유리와 선반 위의 접시까지 그대로 남아 있었습니다. 그리고 곧, 얼음 위에 남은 뼈들도 이름을 되찾기 시작합니다.

## 7. DNA가 찾아 준 이름

{c22}

워털루대학의 더글러스 스텐턴과 로버트 파크 연구팀은 킹윌리엄섬에서 나온 뼈의 DNA를 원정대원 후손들이 보내 준 DNA와 하나하나 비교했습니다. 영국과 캐나다, 오스트레일리아 등에 사는 후손 수십 명이 힘을 보탰습니다.

{c23}

2024년, 한 턱뼈의 어금니에서 꺼낸 DNA가 제임스 피츠제임스 집안 후손의 DNA와 맞았습니다. 에레버스호의 선장이었습니다. 출발 직전 사진 속에서 자신감 넘쳐 보이던 서른두 살의 장교였습니다. 그의 뼈에는 죽은 뒤에 생긴 칼자국이 남아 있었습니다. 스텐턴은 마지막 순간에는 계급도 지위도 사람들을 지켜 주지 못했다고 말했습니다.

{c24}

이미 2021년에 에레버스호의 기관사 존 그레고리가 확인되었고, 그 뒤 네 사람이 더 이름을 찾았습니다. 그 가운데에는 열여섯에서 열여덟 살쯤 된 소년 수병 데이비드 영도 있었습니다. 그리고 이어서, 마지막 한 사람의 이야기입니다.

{c25}

테러호의 돛과 밧줄을 맡았던 스물한 살의 해리 페글러도 있었습니다. 1859년 수색대가 처음 발견한 해골 가운데 하나가, 160여 년 만에 제 이름을 찾은 것입니다. 이어서, 아직 끝나지 않은 이야기로 가 보겠습니다.

## 8. 아직 돌아오지 못한 사람들

{c26}

지금까지 이름을 찾은 사람은 129명 가운데 여섯 명. 연구팀은 지금도 원정대원의 후손을 찾고 있습니다. 후손의 DNA 한 방울이 또 한 사람의 이름을 되찾아 줄 수 있기 때문입니다. 두 배가 잠든 바다는 지금 캐나다의 국립 사적지가 되어, 이누이트와 함께 지키고 있습니다.

{c27}

얼음 속에 사라진 129명. 여러분은 그들의 마지막 길이 어땠을 거라고 생각하시나요? 댓글로 여러분의 생각을 들려주세요. 보고 나면 가벼운 지식이 남는 이야기, 이 채널에서 계속 이어집니다."""

REFS = {"c01": ["c02_3"], "c06": ["c02_3"], "c27": ["c02_3"]}
SEED = {"c21": 1521}   # 다시 그림: 배 두 척·바닷속 아님·종이 테두리
REF_NOTE = ("The two ships must look exactly like HMS Erebus and HMS Terror in the reference painting (same hull shape, colors and three masts), "
            "painted in the same watercolor style. ")

# 컷 → 사진 후보 이름 (사진후보/후보.json 의 열쇠). 사진을 받은 뒤 채움
PHOTOS = {'c02': 'c02_4', 'c03': 'c03_3', 'c04': 'c04_2', 'c07': 'c07_2', 'c08': 'c08_4', 'c09': 'c09_2', 'c10': 'c10_도표', 'c11': 'c11_2', 'c12': 'c12_2', 'c13': 'c13_1', 'c14': 'c14_1', 'c15': 'c09_1', 'c17': 'c17_도표', 'c20': 'c20_1', 'c23': 'c23_1', 'c24': 'c28_3', 'c26': 'c28_4', 'c28': 'c28_1'}


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
        proj = {"ver": 7, "category": "장문", "genre": "[다큐] 역사·미스터리", "topic": "프랭클린 원정대", "title": TITLE,
                "story": story, "sources": ["https://en.wikipedia.org/wiki/Franklin%27s_lost_expedition", "https://www.smithsonianmag.com/smart-news/dna-reveals-identity-of-officer-on-the-lost-franklin-expedition-and-his-remains-show-signs-of-cannibalism-180985154/", "https://explorersweb.com/dna-identifies-four-more-sailors-from-the-franklin-expedition/"],
                "notes": "역사·과학 미스터리 장문 다큐 (실제 사진·암호 원본 위주 + 사진이 없는 장면은 AI 그림)", "autophoto": False, "img_source": "그림: 수채화",
                "settings": {"format": "롱폼 가로(1920×1080)", "narration": "on",
                             "layout": "자막형(큰 제목+사진+자막)", "img_fill": "전체 화면(글자가 사진 위에)",
                             "img_motion": "영상처럼(확대·이동·전환)",
                             "head_show": "안 보임(제목 카드만)", "sub_split": "한 줄씩(문장·쉼표로 나눠 차례로)", "img_label": "on",
                             "narr_voice": "Supertonic M1 (남성, 무료 로컬) [supertonic:M1]", "narr_rate": -8, "narr_tone_m": -2}}   # 장문 다큐 성우(사용자 결정 2026-10-26: 샘플 3번)
        out = os.path.join(HERE, "프랭클린_원정대.json")
        json.dump(proj, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(out, len(story), "chars")


if __name__ == "__main__":
    main()
