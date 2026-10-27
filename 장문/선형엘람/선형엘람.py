"""장문 다큐 '4천 년 동안 아무도 못 읽던 문자, 은잔에 새긴 왕의 이름이 풀어낸 선형 엘람 문자' — 대본 + 컷별 사진·그림 계획
python 장문/선형엘람/선형엘람.py job <저장폴더> [c01,...]  → 그림 주문서(다큐 수채화) job.json (사진 컷은 빼고)
python 장문/선형엘람/선형엘람.py project <그림폴더>       → 프로젝트 파일 장문/선형엘람/선형엘람.json
사용자 요청(2026-10-27): 역사·최신 미스터리, 최신 논문·저널 내용 우선 → 선형 엘람 문자 해독
사실 확인:
 - Desset·Tabibzadeh·Kervran·Basello·Marchesi, "The Decipherment of Linear Elamite Writing",
   Zeitschrift für Assyriologie und vorderasiatische Archäologie 112(1): 11–60 (2022), DOI 10.1515/za-2022-0003
 - 선형 엘람 문자: 기원전 약 2300~1880년 이란 남서부(엘람), 알려진 글 약 40~50개(마더 2021: 51개), 원시 엘람 문자는 1,600개 넘는 점토판(아직 해독 못 함)
 - 런던 개인 소장 은잔들(1920년대 출토, 금속 분석으로 고대 것 확인), 쐐기문자 이름과 맞춰 봄: 왕 실하하·에바라트, 신 나피리샤 (데세 2018)
 - 기호 72개의 소리를 읽음(알려진 기호의 96% 넘게) / 소리만 나타내는 가장 오래된 문자일 수 있다는 주장
 - 앞선 시도: 보르크(1905·1924)·프랑크(1912) '사자 판'(루브르 Sb 17, 아카드어 쐐기문자와 함께 새김), 푸주르 인슈시나크 이름 → 기호 약 9개
 - 반응: 크레베르니크 '대체로 설득력', 스톨퍼 '분명하고 그럴듯', 슈타인켈러 '큰 업적' / 달·켈리는 원시 엘람 문자와의 관계에 의문, 마더는 완전한 번역 전까지 신중
 - 엘람어는 친척 언어가 없는 외톨이 말 / 베히스툰 비문(옛 페르시아어·엘람어·바빌로니아어) / 아슈르바니팔이 수사를 무너뜨림(기원전 647년 무렵)
 - 초가 잔빌 지구라트(기원전 13세기, 1979 유네스코)"""
import json
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
TITLE = "4천 년 동안 아무도 못 읽던 문자, 은잔에 새긴 왕의 이름이 풀어낸 선형 엘람 문자"
STYLE_NAME = "다큐 수채화"
DIALOGUE = []

NP = " No people, no hands, no arms anywhere."
CUTS = [
    ("c01", "real photo", "선형 엘람 문자 (루브르 박물관)"),
    ("c02", "real photo", "선형 엘람 문자"),
    ("c03", "real photo", "이란 남서부 후제스탄"),
    ("c04", "real photo", "함무라비 법전 비석 — 1901년 수사에서 발견 (루브르)"),
    ("c05", "real photo", "초가 잔빌 지구라트 (기원전 13세기)"),
    ("c06", "real photo", "아슈르바니팔의 엘람 원정 (니네베 궁전 부조)"),
    ("c07", "real photo", "원시 엘람 문자 점토판"),
    ("c08", "real photo", "쐐기문자로 쓴 엘람어"),
    ("c09", "real photo", "선형 엘람 문자 점토판 (루브르)"),
    ("c10", "real photo", "베히스툰 비문"),
    ("c11", "real photo", "로제타석 (영국박물관)"),
    ("c12", "real photo", "이집트 상형문자 벽화 (19세기 기록화)"),
    ("c13", "real photo", "'사자 판' — 선형 엘람 문자와 아카드어가 함께 새겨진 돌 (루브르)"),
    ("c14", "real photo", "두 가지 문자가 함께 새겨진 조각상 받침 (루브르)"),
    ("c15", "diagram", "글이 너무 적다"),
    ("c16", "real photo", "고대 이란의 은잔 (참고 유물)"),
    ("c17", "diagram", "은잔 속 이름 맞추기"),
    ("c18", "real photo", "쐐기문자 점토판들"),
    ("c19", "diagram", "기호 72개"),
    ("c20", "real photo", "선형 엘람 문자가 새겨진 원뿔 (루브르)"),
    ("c21", "real photo", "루브르 박물관"),
    ("c22", "real photo", "페르세폴리스의 부조"),
    ("c23", "real photo", "박물관의 고대 은잔들"),
    ("c24", "real photo", "오늘날의 수사(슈시)"),
    ("c25", "real photo", "수사 유적 — 다리우스 궁전 터"),
    ("c26", "real photo", "원시 엘람 문자 — 남은 수수께끼"),
]

STORY = """{c01}

4천 년 넘게 아무도 읽지 못한 문자가 있었습니다. 이란의 옛 왕국 엘람에서 쓰인 선형 엘람 문자입니다. 그런데 2022년, 한 연구팀이 국제 학술지에 이 문자를 거의 다 읽어 냈다는 논문을 발표했습니다.

{c02}

열쇠가 된 것은 오래된 은잔 몇 개였습니다. 은잔에 새겨진 왕의 이름이 4천 년의 침묵을 깨뜨린 것입니다. 오늘은 이 해독 이야기를 처음부터 따라가 보겠습니다. 끝까지 보시면 여러 증거를 바탕으로 인공지능이 내린 결론도 들으실 수 있습니다.

## 1. 잊힌 왕국, 엘람

{c03}

엘람은 지금의 이란 남서부에 있던 고대 왕국입니다. 메소포타미아의 수메르, 바빌로니아와 이웃하며 3천 년 가까이 이어졌습니다. 하지만 오늘날 그 이름을 아는 사람은 많지 않습니다.

{c04}

엘람의 중심 도시는 수사였습니다. 수사는 기원전 4천 년 무렵부터 사람이 살던, 세계에서 가장 오래된 도시 가운데 하나입니다. 1901년 프랑스 발굴단은 이곳에서 놀라운 유물을 찾아냈습니다. 바로 함무라비 법전이 새겨진 비석입니다. 기원전 12세기 엘람의 왕이 바빌론을 쳐들어가 전리품으로 가져온 것이었습니다. 엘람은 바빌론을 위협할 만큼 강한 나라였던 것입니다.

{c05}

엘람 사람들은 거대한 신전 탑도 세웠습니다. 기원전 13세기, 운타시 나피리샤 왕이 지은 초가 잔빌의 지구라트는 지금도 남아 있고, 1979년 유네스코 세계유산이 되었습니다. 처음 지었을 때 높이는 50미터가 넘었을 것으로 보입니다.

{c06}

그러나 기원전 647년 무렵, 아시리아의 왕 아슈르바니팔이 수사를 무너뜨렸습니다. 그 뒤 엘람은 점점 역사에서 사라졌고, 그들의 말과 글도 함께 잊혔습니다.

## 2. 세 가지 엘람의 글

{c07}

엘람 사람들이 쓴 문자는 모두 세 종류였습니다. 가장 오래된 것은 기원전 3천 년 무렵의 원시 엘람 문자입니다. 1,600개가 넘는 점토판이 남아 있지만, 지금까지도 제대로 읽지 못합니다. 대부분 곡식과 가축을 세어 적은 장부로 보이는데, 수사뿐 아니라 이란 동쪽 끝의 유적에서까지 발견되었습니다.

{c08}

나중에는 이웃 메소포타미아에서 빌려 온 쐐기문자로 엘람어를 적었습니다. 이 글들은 읽을 수 있습니다. 다만 엘람어는 세상 어떤 언어와도 친척 관계가 없는 외톨이 말이라, 뜻을 푸는 데 오랜 시간이 걸렸습니다.

{c09}

그리고 그 사이, 기원전 2300년 무렵부터 1880년 무렵까지 쓰인 것이 선형 엘람 문자입니다. 반듯한 선으로 그린 기호들이 줄지어 있는 아름다운 문자입니다. 그런데 남아 있는 글이 50개 남짓밖에 되지 않았습니다.

{c10}

엘람어는 훗날 페르시아 제국에서도 쓰였습니다. 페르세폴리스에서 나온 수만 장의 행정 점토판 가운데 대부분이 엘람어로 적혀 있을 정도입니다. 다리우스 대왕이 절벽에 새긴 베히스툰 비문에는 같은 내용이 옛 페르시아어와 엘람어, 바빌로니아어로 함께 적혀 있습니다. 19세기 영국의 헨리 롤린슨은 목숨을 걸고 절벽에 매달려 이 비문을 베껴 냈습니다. 이 비문 덕분에 학자들은 쐐기문자로 쓴 엘람어를 읽을 수 있게 되었습니다.

## 3. 해독은 왜 어려웠을까

{c11}

잊힌 문자를 푸는 가장 좋은 열쇠는 같은 내용을 두 가지 글로 쓴 자료입니다. 이집트 상형문자도 1822년, 같은 내용이 그리스어로 함께 적힌 로제타석 덕분에 풀렸습니다. 로제타석은 1799년 이집트 나일강 어귀의 마을에서 우연히 발견된 돌이었습니다.

{c12}

프랑스의 학자 샹폴리옹은 로제타석에서 이집트 왕의 이름을 찾아냈습니다. 왕의 이름은 어느 나라 말로 써도 소리가 거의 같기 때문입니다. 이름이 해독의 첫 번째 열쇠였던 것입니다. 해독에 성공한 샹폴리옹은 형의 사무실로 달려가 알아냈다고 외치고는 그 자리에서 쓰러졌다는 이야기가 전해집니다.

{c13}

선형 엘람 문자에도 비슷한 돌이 하나 있었습니다. 루브르 박물관에 있는 '사자 판'입니다. 이 돌에는 선형 엘람 문자와 아카드어 쐐기문자가 함께 새겨져 있습니다.

{c14}

1900년대 초 학자들은 이 돌에서 기원전 2100년 무렵의 왕 푸주르 인슈시나크의 이름과 신의 이름을 찾아냈습니다. 하지만 이것으로 확실히 읽을 수 있는 기호는 겨우 아홉 개쯤이었습니다. 그 뒤 100년 동안 해독은 거의 멈춰 있었습니다.

{c15}

가장 큰 문제는 글이 너무 적다는 것이었습니다. 알려진 글은 50개 남짓, 그것도 대부분 짧았습니다. 단서가 너무 적어서, 어떤 학자들은 이 문자는 영원히 풀 수 없을 것이라고까지 말했습니다.

## 4. 은잔이 들려준 이름

{c16}

변화는 뜻밖의 곳에서 시작되었습니다. 2015년, 이란 테헤란대학교의 프랑스 고고학자 프랑수아 데세는 런던의 한 개인 소장품에서 은잔들을 보게 되었습니다. 1920년대에 이란에서 발굴되어 팔려 나간 것들이었습니다. 데세는 2018년 이 은잔들의 글을 처음으로 학계에 소개했습니다.

{c17}

은잔에는 선형 엘람 문자와 함께 쐐기문자도 새겨져 있었습니다. 어떤 은잔에는 기호가 200개 가까이 새겨져 있었습니다. 지금까지 알려진 어떤 선형 엘람 문자 글보다도 긴 글이었습니다. 데세는 쐐기문자로 쓴 왕의 이름, 실하하와 에바라트, 그리고 신 나피리샤의 이름을 찾아, 선형 엘람 문자 속에서 같은 소리가 될 만한 기호 묶음을 맞춰 보았습니다. 샹폴리옹이 썼던 바로 그 방법입니다.

{c18}

이름에서 얻은 소리를 다른 글에 넣어 보자, 되풀이되는 낱말들이 하나둘 모습을 드러냈습니다. 주었다, 만들었다 같은 동사도 나타났습니다. 은잔에 적힌 글은 왕이 신에게 바친 제물을 기록한 문장이었던 것입니다.

{c19}

데세와 이란, 이탈리아의 학자들로 이루어진 연구팀은 2022년, 독일의 학술지 아시리아학 잡지에 논문을 실었습니다. 이들은 기호 72개의 소리를 읽어 냈다고 밝혔습니다. 알려진 기호의 96퍼센트가 넘는 수였습니다.

{c20}

연구팀은 더 놀라운 주장도 했습니다. 선형 엘람 문자는 뜻을 나타내는 그림 글자 없이, 소리만을 적는 문자라는 것입니다. 이 주장이 맞다면 소리만 적는 문자로는 세계에서 가장 오래된 것이 됩니다. 크레베르니크 교수는 이것이 사실이라면, 훗날 알파벳의 발명에 견줄 만한 일이라고 말했습니다.

## 5. 학자들의 반응과 남은 숙제

{c21}

많은 학자들이 박수를 보냈습니다. 독일 예나대학교의 크레베르니크 교수는 대체로 설득력이 있다고 했고, 미국 시카고대학교의 스톨퍼 교수는 분명하고 그럴듯하다고 평가했습니다. 하버드대학교의 슈타인켈러 교수는 큰 업적이라고 말했습니다. 이탈리아 파도바대학교의 비달레 교수는 샹폴리옹과 같은 방법으로 이룬 큰 발견이라고 평가했습니다.

{c22}

하지만 의문도 있습니다. 옥스퍼드대학교의 제이컵 달 교수 등은 선형 엘람 문자가 원시 엘람 문자에서 이어졌다는 연구팀의 주장에 고개를 젓습니다. 두 문자 사이에는 약 800년의 공백이 있기 때문입니다. 또 다른 학자들은 일부 기호가 소리가 아니라 뜻을 나타낼 수도 있다고 봅니다.

{c23}

은잔의 출처도 문제가 되었습니다. 정식 발굴이 아니라 거래로 흘러나온 유물이었기 때문입니다. 다만 금속을 분석한 결과, 은잔은 요즘 만든 가짜가 아니라 실제로 오래된 것으로 확인되었습니다.

{c24}

연구팀도 스스로 인정합니다. 남은 글이 워낙 적어서 모든 문장을 완전히 번역하기는 아직 어렵다는 것입니다. 소리는 읽었지만, 뜻을 모두 알기 위해서는 더 많은 글이 필요합니다. 데세는 은잔들이 수사에서 남동쪽으로 수백 킬로미터 떨어진 곳의 4천 년 전 왕실 무덤에서 나왔을 것으로 봅니다. 연구팀은 이란에서 새로운 발굴이 이어지기를 기다리고 있습니다.

## 6. 인공지능의 결론

{c25}

그렇다면 인공지능인 제가 증거들을 모아 내린 결론은 이렇습니다. 첫째, 선형 엘람 문자의 소리는 상당 부분 풀렸다고 보는 것이 합리적입니다. 서로 다른 은잔과 비문에서 같은 읽기가 맞아떨어지고, 여러 대가들이 설득력을 인정했기 때문입니다.

{c26}

둘째, 그러나 완전한 해독은 아직입니다. 뜻까지 모두 풀려면 새로운 글이 더 나와야 합니다. 셋째, 이 이야기는 해독의 열쇠가 언제나 같다는 것을 보여 줍니다. 4천 년 전 왕이 은잔에 새긴 자신의 이름이, 잊힌 왕국의 목소리를 다시 들려준 것입니다. 이제 남은 수수께끼는 원시 엘람 문자입니다. 1,600개가 넘는 점토판에는 어떤 이야기가 잠들어 있을까요? 여러분은 이 해독이 맞다고 생각하시나요? 댓글로 들려주세요."""


REFS = {}
SEED = {}
REF_NOTE = ("Any real place or object shown must look exactly like the reference photo (same shape and colors), "
            "painted in the same watercolor style. ")

# 컷 → 사진 후보 이름 (사진후보/후보.json 의 열쇠). 사진을 받은 뒤 채움
PHOTOS = {'c01': 'c09_4', 'c02': 'c02_4', 'c03': 'c03_o2', 'c04': 'c25_3', 'c05': 'c05_4', 'c06': 'c06_1', 'c07': 'c07_1', 'c08': 'c08_4', 'c09': 'c20_1', 'c10': 'c10_1', 'c11': 'x_rosetta', 'c12': 'x_champ', 'c13': 'c02_1', 'c14': 'c20_4', 'c15': 'c15_도표', 'c16': 'c16_2', 'c17': 'c17_도표', 'c18': 'x_cune', 'c19': 'c19_도표', 'c20': 'c20_2', 'c21': 'c21_2', 'c22': 'c22_4', 'c23': 'c16_1', 'c24': 'c03_o4', 'c25': 'x_shush', 'c26': 'c07_4'}


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
        proj = {"ver": 7, "category": "장문", "genre": "[다큐] 고고학", "topic": "선형 엘람 문자 해독", "title": TITLE,
                "story": story, "sources": ["https://doi.org/10.1515/za-2022-0003", "https://www.smithsonianmag.com/history/have-scholars-finally-deciphered-a-mysterious-ancient-script-180980497/", "https://en.wikipedia.org/wiki/Linear_Elamite"],
                "notes": "고고학 장문 다큐(최신 논문) (실제 사진·논문 그림 위주 + 사진이 없는 장면은 AI 그림)", "autophoto": False, "img_source": "그림: 수채화",
                "settings": {"format": "롱폼 가로(1920×1080)", "narration": "on",
                             "layout": "자막형(큰 제목+사진+자막)", "img_fill": "전체 화면(글자가 사진 위에)",
                             "img_motion": "천천히 확대만", "scene_trans": "전진(확대하며 다음 장면)",   # 계속 앞으로 나아가는 느낌(사용자 요청 2026-10-26)
                             "head_show": "안 보임(제목 카드만)", "sub_split": "한 줄씩(문장·쉼표로 나눠 차례로)", "img_label": "on",
                             "narr_voice": "Supertonic M2 (남성, 무료 로컬) [supertonic:M2]", "narr_rate": -8, "narr_tone_m": -1}}   # 장문 다큐 성우(사용자 결정 2026-10-26 오후: 샘플 2번 — 전에는 3번)
        out = os.path.join(HERE, "선형엘람.json")
        json.dump(proj, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(out, len(story), "chars")


if __name__ == "__main__":
    main()
