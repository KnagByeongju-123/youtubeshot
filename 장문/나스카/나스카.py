"""장문 고고학 다큐 '100년 동안 430개, AI는 6개월 만에 303개, 나스카 그림이 숨긴 두 개의 길' — 대본 + 컷별 사진·그림 계획
python 장문/나스카/나스카.py job <저장폴더> [c01,...]  → 그림 주문서(다큐 수채화) job.json (사진 컷은 빼고)
python 장문/나스카/나스카.py project <그림폴더>       → 프로젝트 파일 장문/나스카/나스카.json
사용자 요청(2026-10-26): 최신 논문 기반 고고학 미스터리 5번 — 나스카 AI (사용자가 예전에 나스카 AI 를 다룬 적 있음 → 이번엔 '두 종류 그림과 길' 중심)
사실 확인: Sakai·Sakurai·Lu·Olano·Albrecht·Hamann·Freitag, "AI-accelerated Nazca survey nearly doubles the number of known figurative geoglyphs
 and sheds light on their purpose", PNAS 121(40) e2407652121 (2024-10-01, CC BY-NC-ND — 논문 그림은 쓰지 않음, 숫자만 도표로)
 - 야마가타대학·IBM 토머스 J. 왓슨 연구소·파리1대학·독일 항공우주센터 / 나스카 평원 약 629㎢, 해발 약 500m, 바다에서 약 50km
 - 거의 100년 동안 그림(구상) 지상화 430개 → 2022년 9월~2023년 2월 6개월 현장 조사로 새 그림 303개 (기하학 무늬 42개 별도)
 - AI 후보 47,410곳 → 사람이 1,309곳 추림(사진 확인 1,200시간) → 걸어서 확인 1,440시간 / 평균 36곳 중 1곳 유망 / 앞으로 248개 이상 더 나올 것
 - 2004~2020년 연구팀이 찾은 318개(선 그림 11, 부조 그림 307) / 항공사진 10cm, 드론
 - 선 그림: 평균 길이 90m, 알려진 50개, 64%가 야생 동물, 의식용 직선·사다리꼴 그림망에서 평균 34m → 공동체 의식, 순례(인헤니오 강 → 카와치 신전)
 - 부조 그림: 평균 9m, 81.6%가 사람·사람이 다룬 것(가축 라마·잘린 머리), 구불구불한 옛 오솔길에서 평균 43m → 혼자·작은 무리가 보던 그림
 - 돌을 치워 밝은 땅이 드러나게 해서 만듦 / 기원전 1세기 무렵부터 사용 / 1994 유네스코, 마리아 라이헤(1903~1998)"""
import json
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
TITLE = "100년 동안 430개, AI는 6개월 만에 303개, 나스카 그림이 숨긴 두 개의 길"
STYLE_NAME = "다큐 수채화"
DIALOGUE = []

NP = " No people, no hands, no arms anywhere."
CUTS = [
    ("c01", "real photo", "나스카의 벌새 그림"),
    ("c02", "real photo", "하늘에서 본 나스카 평원"),
    ("c03", "real photo", "나스카 평원의 선들"),
    ("c04", "real photo", "나스카의 거미 그림"),
    ("c05", "real photo", "나스카의 직선과 사다리꼴 그림"),
    ("c06", "real photo", "나스카 평원의 땅"),
    ("c07", "real photo", "마리아 라이헤 동상"),
    ("c08", "real photo", "나스카 전망대"),
    ("c09", "real photo", "고속도로가 가로지른 나스카 그림"),
    ("c10", "real photo", "언덕 비탈의 '올빼미 사람' 그림"),
    ("c11", "diagram", "AI가 찾은 303개"),
    ("c12", "real photo", "나스카 공항의 경비행기"),
    ("c13", "real photo", "나스카의 거미 그림과 선들"),
    ("c14", "real photo", "나스카의 개 그림"),
    ("c15", "diagram", "두 종류의 그림"),
    ("c16", "Ancient Nazca people in simple woven tunics walking along a narrow winding footpath across a reddish stony desert plain, looking down at a flat drawing of a llama about nine metres long made on the ground itself beside the path: the llama is only a flat outline of lighter cleared earth and low piles of dark stones lying flat on the desert floor (a geoglyph, NOT a statue, nothing standing up), seen from slightly above, soft afternoon light, edge-to-edge painting", "오솔길 옆의 작은 그림 (상상 복원)"),
    ("c17", "real photo", "라마"),
    ("c18", "real photo", "나스카의 나선 무늬 (도면)"),
    ("c19", "real photo", "카와치 신전 유적"),
    ("c20", "A long procession of ancient Nazca people in colorful woven tunics walking along a huge straight line drawn on a vast reddish desert plain toward distant mountains, carrying pottery and musical instruments, dust and golden evening light, wide aerial view, small figures, edge-to-edge painting filling the whole frame, no white paper margins", "거대한 선을 따라 걷는 의식 행렬 (상상 복원)"),
    ("c21", "real photo", "나스카의 고래 그림"),
    ("c22", "real photo", "나스카의 콘도르 그림"),
    ("c23", "real photo", "카와치 일대의 골짜기"),
    ("c24", "real photo", "팔파의 지상화"),
    ("c25", "real photo", "나스카 평원의 그림들"),
    ("c26", "real photo", "나스카 평원"),
]

STORY = """{c01}

페루 남부의 사막에는 하늘에서 내려다봐야 보이는 거대한 그림들이 있습니다. 바로 나스카 지상화입니다. 사람들은 거의 100년 동안 이 사막을 뒤져 그림 430개를 찾아냈습니다. 그런데 2024년, 인공지능이 단 6개월 만에 새 그림 303개를 찾아냈다는 논문이 발표되었습니다.

{c02}

그리고 이 발견은 더 큰 수수께끼의 답을 알려 주었습니다. 나스카 사람들은 왜 이 그림을 그렸을까요? 오늘은 미국 국립과학원회보에 실린 논문을 따라 그 비밀을 풀어 보겠습니다. 끝까지 보시면 여러 증거를 바탕으로 인공지능이 내린 결론도 들으실 수 있습니다.

## 1. 사막에 그린 그림

{c03}

나스카 평원은 페루 남부, 바다에서 약 50킬로미터 떨어진 해발 약 500미터의 메마른 땅입니다. 이곳에는 원숭이와 벌새, 거미와 고래 같은 동물부터 수 킬로미터에 이르는 곧은 선까지 수많은 그림이 그려져 있습니다.

{c04}

그림을 그린 사람들은 기원전 100년 무렵부터 이 지역에 살았던 나스카 사람들입니다. 연구에 따르면 이곳에서 지상화를 쓰기 시작한 것은 적어도 2천 년 전입니다.

{c05}

그림 가운데에는 동물이나 사람을 그린 그림도 있지만, 끝없이 이어진 직선이나 거대한 사다리꼴 같은 무늬도 많습니다. 오늘 이야기의 주인공은 동물과 사람을 그린 그림입니다. 유명한 벌새 그림은 부리에서 꼬리까지 약 90미터에 이릅니다.

{c06}

만드는 방법은 의외로 간단합니다. 사막 표면에는 햇볕에 그을린 검붉은 돌들이 깔려 있습니다. 이 돌들을 치우면 그 아래의 밝은 흙이 드러나고, 치운 돌을 가장자리에 쌓으면 선이 됩니다. 큰 선 그림은 돌을 길게 치워 선을 그었고, 작은 그림은 치운 돌을 쌓아 볼록한 덩어리를 만들었습니다. 그래서 작은 그림은 흙 위의 밝은 부분과 어두운 돌무더기가 함께 모양을 이룹니다.

{c07}

비가 거의 오지 않고 바람도 약하며, 홍수가 닿지 않고 농사도 짓기 어려운 땅이었기 때문에 그림은 2천 년을 버틸 수 있었습니다. 독일 출신의 수학자 마리아 라이헤는 1940년대부터 50년 가까이 이 사막에서 지내며 그림을 재고, 쓸고, 지켰습니다. 사람들은 그녀를 사막의 여인이라고 불렀습니다. 그녀는 1998년 세상을 떠날 때까지 나스카를 지키는 일을 멈추지 않았습니다.

{c08}

나스카 지상화는 1994년 유네스코 세계유산이 되었습니다. 그러나 너무 크고 오래되어, 땅에 서서는 무엇을 그렸는지 알아보기 어렵습니다. 사람들은 전망대에 오르거나 비행기를 타고서야 그 모습을 볼 수 있습니다. 그래서 그림이 망가지는 일도 있었습니다. 1930년대에 놓인 팬아메리칸 고속도로는 도마뱀 그림의 한가운데를 가로질러 지나갑니다.

## 2. 100년 동안 430개

{c09}

나스카 지상화가 다시 알려진 것은 20세기 초입니다. 1941년 미국의 학자 폴 코속은 한 직선이 동짓날 해 지는 쪽을 가리킨다는 것을 발견하고, 나스카를 거대한 천문 달력이라고 불렀습니다. 그 뒤 거의 100년 동안 학자들은 동물과 사람 등을 그린 그림 430개를 찾아냈습니다.

{c10}

일본 야마가타대학의 사카이 마사토 교수 연구팀은 2004년부터 이 사막을 조사해 왔습니다. 항공사진과 드론까지 동원해 2020년까지 새 그림 318개를 찾았습니다. 하지만 여기에는 큰 어려움이 있었습니다.

{c12}

나스카 평원과 주변 지역은 약 629제곱킬로미터. 서울 면적과 비슷한 넓이입니다. 그런데 작은 그림들은 2천 년 동안 비바람에 깎여 흐릿해졌고, 전문가가 항공사진을 한 장 한 장 눈으로 들여다봐야 겨우 찾을 수 있었습니다.

## 3. 인공지능이 사막을 읽다

{c11}

그래서 연구팀은 미국 아이비엠 연구소와 손을 잡았습니다. 이미 알려진 그림의 사진으로 인공지능을 가르친 뒤, 나스카 평원 전체의 항공사진을 보여 주었습니다. 문제는 가르칠 사진이 많지 않았다는 것입니다. 알려진 작은 그림은 수백 개뿐이었고, 그마저 흐릿했습니다. 연구팀은 적은 사진으로도 배울 수 있도록 인공지능을 다듬었습니다. 그렇게 인공지능은 그림이 있을 만한 곳 4만 7천여 곳을 골라냈습니다.

{c13}

연구자들은 이 후보들을 하나하나 확인해 가능성이 높은 1,309곳을 추렸습니다. 사진을 확인하는 데만 1,200시간이 걸렸습니다. 평균 36곳을 봐야 1곳의 유망한 후보가 나왔습니다. 그래도 사막 전체를 사람 눈으로 뒤지는 것과는 비교할 수 없이 빨랐습니다.

{c14}

그리고 2022년 9월부터 2023년 2월까지 6개월 동안, 연구팀은 후보지를 직접 걸어서 찾아갔습니다. 페루 문화부의 허가를 받아 1,440시간을 걸은 끝에, 새 그림 303개를 확인했습니다. 100년 동안 찾은 수와 거의 맞먹는 숫자입니다. 이와 함께 직선과 도형 같은 무늬 그림도 42개가 새로 확인되었습니다. 새로 찾은 그림은 모두 드론으로 촬영해 기록했습니다.

## 4. 두 종류의 그림

{c15}

이렇게 그림이 많아지자, 연구팀은 처음으로 전체를 비교해 볼 수 있었습니다. 그러자 나스카 그림은 크게 두 종류로 나뉜다는 것이 분명해졌습니다.

{c21}

첫째는 우리가 잘 아는 거대한 선 그림입니다. 평균 길이가 90미터에 이르고, 지금까지 50개가 알려져 있습니다. 그 가운데 64퍼센트가 원숭이나 새 같은 야생 동물을 그렸습니다. 고래 그림과 원숭이 그림 위에서는 서기 50년에서 300년 무렵의 나스카 토기 조각이 나왔습니다. 토기에 그려진 무늬와 그림의 모양이 닮아, 이 거대한 그림들이 나스카 문화가 한창이던 때 만들어졌다는 것을 알 수 있습니다.

{c17}

둘째는 이번에 대부분 새로 찾은 작은 그림입니다. 돌을 쌓아 볼록하게 만든 부조 그림으로, 크기는 평균 9미터에 불과합니다. 이 작은 그림들의 81.6퍼센트는 사람, 또는 사람이 기르거나 다룬 것을 그렸습니다. 가축인 라마가 많았습니다.

{c18}

잘린 사람 머리를 그린 그림도 여럿 나왔습니다. 나스카 사람들의 토기에도 자주 나오는 모습으로, 이들의 의식과 관련이 있었을 것으로 보입니다. 칼을 든 범고래처럼 처음 보는 기묘한 그림도 있었습니다.

## 5. 그림이 놓인 자리

{c16}

더 놀라운 것은 그림이 놓인 자리였습니다. 나스카 평원에는 사람들이 걸어 다니던 구불구불한 옛 오솔길이 그물처럼 얽혀 있습니다. 작은 부조 그림들은 이 오솔길에서 평균 43미터 떨어진 곳에 있었습니다. 길을 걷는 사람 눈에 보이는 거리입니다.

{c23}

연구팀은 작은 그림들이 혼자 또는 몇 사람이 길을 가다 보던 그림이라고 봅니다. 사람들의 생활과 이야기를 전하는 그림, 어쩌면 길을 알려 주는 표지판 같은 역할도 했을지 모릅니다.

{c20}

반면 거대한 선 그림들은 곧게 뻗은 직선과 사다리꼴 그림의 망에서 평균 34미터 떨어진 곳에 있었습니다. 이 직선들은 의식을 위해 만든 길로 여겨집니다.

{c19}

연구팀은 이 길이 인헤니오 강 골짜기에서 출발해, 나스카 강 골짜기의 카와치 신전까지 가는 순례에 쓰였을 것으로 봅니다. 거대한 동물 그림 위에서는 순례의 처음이나 끝에 많은 사람이 모여 의식을 치렀을 가능성이 큽니다.

{c22}

정리하면 이렇습니다. 거대한 선 그림은 공동체 전체가 함께 의식을 치르던 무대였고, 작은 부조 그림은 개인과 작은 무리가 길 위에서 보던 그림이었습니다. 하나의 사막에 서로 다른 목적의 두 가지 길과 두 가지 그림이 함께 있었던 것입니다.

## 6. 인공지능의 결론

{c24}

그렇다면 인공지능인 제가 증거들을 모아 내린 결론은 이렇습니다. 첫째, 나스카 그림은 외계인을 위한 활주로도, 하늘에 보내는 신호도 아닙니다. 그림은 사람들이 걷던 길을 따라 놓여 있었습니다. 땅 위를 걷는 사람을 위한 그림이었던 것입니다. 그림은 하늘이 아니라 땅을 향해 있었습니다.

{c25}

둘째, 인공지능은 그림을 해석하지 않았습니다. 수만 곳의 후보를 골라냈을 뿐이고, 진짜인지 확인한 것은 사막을 직접 걸은 사람들이었습니다. 인공지능과 사람이 함께했기에 100년 걸릴 일을 6개월 만에 해낼 수 있었습니다.

{c26}

셋째, 이야기는 아직 끝나지 않았습니다. 연구팀은 인공지능이 고른 후보 가운데 아직 확인하지 못한 곳에서 적어도 248개의 그림이 더 나올 것으로 내다봅니다. 2천 년 전 나스카 사람들이 길 위에 남긴 이야기는 지금도 사막 어딘가에서 우리를 기다리고 있습니다. 여러분은 이 그림들이 무엇을 말하고 있다고 생각하시나요? 댓글로 들려주세요."""


REFS = {}
SEED = {"c16": 716, "c20": 720}
REF_NOTE = ("Any real place or object shown must look exactly like the reference photo (same shape and colors), "
            "painted in the same watercolor style. ")

# 컷 → 사진 후보 이름 (사진후보/후보.json 의 열쇠). 사진을 받은 뒤 채움
PHOTOS = {'c01': 'c01_o2', 'c02': 'c02_4', 'c03': 'c02_3', 'c04': 'c04_3', 'c05': 'c05_1', 'c06': 'c25_4', 'c07': 'c07_2', 'c08': 'c08_3', 'c09': 'c08_4', 'c10': 'c24_3', 'c11': 'c11_도표', 'c12': 'c07_3', 'c13': 'c02_2', 'c14': 'c14_2', 'c15': 'c15_도표', 'c17': 'c17_3', 'c18': 'c26_1', 'c19': 'c19_1', 'c21': 'c21_2', 'c22': 'c22_2', 'c23': 'c19_4', 'c24': 'c24_1', 'c25': 'c25_2', 'c26': 'c25_3'}


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
        proj = {"ver": 7, "category": "장문", "genre": "[다큐] 고고학", "topic": "나스카 AI 지상화", "title": TITLE,
                "story": story, "sources": ["https://doi.org/10.1073/pnas.2407652121", "https://whc.unesco.org/en/list/700/", "https://en.wikipedia.org/wiki/Nazca_Lines"],
                "notes": "고고학 장문 다큐(최신 논문) (실제 사진·논문 그림 위주 + 사진이 없는 장면은 AI 그림)", "autophoto": False, "img_source": "그림: 수채화",
                "settings": {"format": "롱폼 가로(1920×1080)", "narration": "on",
                             "layout": "자막형(큰 제목+사진+자막)", "img_fill": "전체 화면(글자가 사진 위에)",
                             "img_motion": "천천히 확대만", "scene_trans": "전진(확대하며 다음 장면)",   # 계속 앞으로 나아가는 느낌(사용자 요청 2026-10-26)
                             "head_show": "안 보임(제목 카드만)", "sub_split": "한 줄씩(문장·쉼표로 나눠 차례로)", "img_label": "on",
                             "narr_voice": "Supertonic M2 (남성, 무료 로컬) [supertonic:M2]", "narr_rate": -8, "narr_tone_m": -1}}   # 장문 다큐 성우(사용자 결정 2026-10-26 오후: 샘플 2번 — 전에는 3번)
        out = os.path.join(HERE, "나스카.json")
        json.dump(proj, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(out, len(story), "chars")


if __name__ == "__main__":
    main()
