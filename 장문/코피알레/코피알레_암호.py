"""장문 미스터리 다큐 '컴퓨터가 풀어낸 비밀결사의 암호 책, 코피알레 암호' — 대본 + 컷별 사진·그림 계획
python 장문/코피알레/코피알레_암호.py job <저장폴더> [c01,...]  → 그림 주문서(다큐 수채화) job.json (사진 컷은 빼고)
python 장문/코피알레/코피알레_암호.py project <그림폴더>       → 프로젝트 파일 장문/코피알레/코피알레_암호.json
사실 확인: Knight·Megyesi·Schaefer 'The Copiale Cipher'(BUCC 2011, ACL Anthology W11-1202 — 해독 과정·첫 부분 원문),
USC 발표·NPR·Wikipedia(입회 의식의 빈 종이·안경·눈 씻기·눈썹, 볼펜뷔텔 안과의사 결사, 펠트하임 백작, 클레멘스 12세 금지령),
Önnerfors(자연권). 보르그 암호: Aldarrab·Knight·Megyesi (바티칸 도서관 Borg.lat.898, 17세기 라틴어 의학서)"""
import json
import os
import shutil
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
TITLE = "컴퓨터가 풀어낸 비밀결사의 암호 책, 코피알레 암호"
STYLE_NAME = "다큐 수채화"
DIALOGUE = []

NP = " No people, no hands, no arms anywhere."
CUTS = [
    ("c01", "a dim old academy archive room with tall wooden shelves, on a table lies a single old book bound in green and gold brocade paper, closed, soft dusty window light." + NP, "옛 동베를린 학술원의 기록 보관소"),
    ("c02", "Copiale cipher page (real image)", "코피알레 암호 책의 한 쪽"),
    ("c03", "Copiale cipher pages (real image)", "띄어쓰기 없이 이어진 기호들"),
    ("c04", "Academy of Sciences of the GDR building (real photo)", "베를린-브란덴부르크 학술원 (베를린)"),
    ("c05", "diagram on real Copiale page", "105쪽 · 7만 5천 자 · 기호 약 90가지"),
    ("c06", "Information Sciences Institute (real photo)", "기계 번역을 돌리는 컴퓨터 (참고 사진)"),
    ("c07", "Uppsala University (real photo)", "스웨덴 웁살라대학"),
    ("c08", "diagram", "첫 번째 생각: 로마자만 진짜?"),
    ("c09", "diagram", "40개가 넘는 언어로 시험 → 실패"),
    ("c10", "diagram", "왜 독일어였을까"),
    ("c11", "diagram", "C 뒤에는 거의 언제나 H"),
    ("c12", "diagram", "로마자는 띄어쓰기였다"),
    ("c13", "diagram", "쌍점 = 앞 자음 한 번 더 · 한 기호 = SCH"),
    ("c14", "diagram on real Copiale page", "풀려난 첫 문장"),
    ("c15", "Wolfenbuettel (real photo)", "독일 볼펜뷔텔 성"),
    ("c16", "an eighteenth century candlelit lodge room, a doorman, an adult man in a plain grey 1740s coat with white stockings and a short powdered wig tied at the back, leads the candidate, an adult man in his thirties wearing a brown 1740s frock coat, knee breeches and a powdered wig, by the hand through a doorway toward a long table, both men seen from behind and side, both clearly grown men, shadows on panelled walls, no modern objects", "입회 의식의 시작"),
    ("c17", "an older master of a secret society in a 1740s black coat with a white cravat (no bow tie) and a black tricorn hat over a powdered wig sits behind a table with two candles and an open book, facing the candidate, an adult man in his thirties wearing a brown 1740s frock coat, knee breeches and a powdered wig, standing before him, both clearly grown men, solemn questioning, panelled room, no modern objects", "세 가지 질문"),
    ("c18", "a single blank sheet of old paper lying on a dark wooden table beside a pair of round eighteenth century spectacles and a folded linen cloth, candle light, nothing written on the paper." + NP, "아무것도 쓰여 있지 않은 종이"),
    ("c19", "a single small pair of plain antique steel tweezers (two thin straight arms joined at one end) lying alone on a dark velvet cloth, a pair of round eighteenth century spectacles lying separately a hand's width away, the two objects not touching, candle light, close-up still life." + NP, "족집게와 눈썹 한 올"),
    ("c20", "eighteenth century eye surgery engraving (real image)", "옛 백내장 수술 (판화)"),
    ("c21", "Pope Clement XII portrait (real image)", "교황 클레멘스 12세"),
    ("c22", "Freemasons initiation engraving (real image)", "프리메이슨 입회 의식 (옛 판화)"),
    ("c23", "an open old handwritten cipher book on a desk, pages filled with rows of tiny strange symbols, a few symbols drawn much larger than the rest, candle light, no readable words." + NP, "끝내 풀리지 않은 큰 기호 8개"),
    ("c24", "salon of Madame Geoffrin painting (real image)", "계몽주의 시대의 모임 (옛 그림)"),
    ("c25", "Lower Saxony State Archive Wolfenbuettel (real photo)", "볼펜뷔텔 기록 보관소 (니더작센 주)"),
    ("c26", "Borg cipher page (real image)", "바티칸 도서관의 옛 필사본 (참고 사진)"),
    ("c27", "an old book bound in green and gold brocade paper lying closed on a dark table under a single soft beam of light, a pair of round spectacles resting on it, quiet mysterious closing image." + NP, "기호 속에 숨은 목소리"),
]

STORY = """{c01}

옛 동베를린의 한 학술원. 그곳 기록 보관소에 녹색과 금색 무늬 종이로 곱게 싼 책 한 권이 잠들어 있었습니다. 냉전이 끝난 뒤, 이 책은 세상의 관심을 받기 시작했습니다.

{c02}

책을 펼치면 로마자와 그리스 문자, 그리고 처음 보는 기호들이 빽빽하게 이어집니다. 띄어쓰기는 하나도 없습니다. 아무도 단 한 줄을 읽지 못했습니다.

{c03}

이 책의 이름은 코피알레 암호입니다. 2011년, 이 책을 연 것은 컴퓨터의 계산이었습니다. 끝까지 보시면, 수백 년 동안 감춰져 있던 한 비밀결사의 기묘한 의식을 보시게 됩니다.

## 1. 아무도 읽지 못한 책

{c04}

1970년대, 동독 학술원의 학자들은 이 책을 살펴보고 18세기 후반에 만들어진 것으로 보았습니다. 종이는 품질이 좋았고, 글씨는 놀랄 만큼 반듯했으며, 고친 자국도 거의 없었습니다. 하지만 내용은 누구도 풀지 못했습니다.

{c05}

책은 모두 105쪽, 손으로 쓴 글자가 약 7만 5천 개였습니다. 암호가 아닌 글자는 딱 두 군데, '필립 1866'과 '코피알레스 3'뿐이었습니다. 책의 이름은 이 '코피알레스'에서 따왔습니다. 왼쪽 쪽 아래에는 다음 쪽의 첫 글자를 미리 적어 둔 표시도 있었습니다. 옛날 인쇄소에서 쪽 순서를 맞출 때 쓰던 방법입니다. 이어서, 이 책에 도전한 사람들을 만나 보겠습니다.

## 2. 번역 연구자의 도전

{c06}

미국 서던캘리포니아대학의 컴퓨터 과학자 케빈 나이트는 컴퓨터가 한 언어를 다른 언어로 옮기는 기계 번역을 연구했습니다. 그에게 낯선 외국어는 일종의 암호와 같았습니다.

{c07}

스웨덴 웁살라대학의 언어학자 베아타 메기시와 크리스티아네 셰퍼가 함께했습니다. 세 사람은 먼저 책의 16쪽을 컴퓨터가 읽을 수 있게 한 글자씩 옮겨 적었습니다. 1만 840자, 기호의 종류는 약 90가지였습니다.

## 3. 첫 번째 실패

{c08}

컴퓨터는 기호마다 앞뒤에 어떤 기호가 오는지 세어, 비슷하게 쓰이는 것끼리 묶었습니다. 로마자들은 한 무리로 뭉쳤습니다. 그래서 세 사람은 생각했습니다. 진짜 내용은 로마자에 있고, 나머지 기호는 해독을 방해하려고 끼워 넣은 가짜일 것이라고.

{c09}

컴퓨터는 로마자만 뽑아 독일어, 영어, 라틴어, 그리고 40개가 넘는 다른 언어로 차례로 풀어 보았습니다. 결과는 모두 뜻 없는 글자뿐이었습니다. 한 글자를 여러 기호로 바꿔 쓰는 방식이라고 가정하고 다시 풀었습니다. 연습용으로 만든 가짜 암호에서는 잘 통하던 방법이었지만, 이 책에서는 역시 실패였습니다. 그런데 곧, 아주 작은 차이 하나가 길을 엽니다.

## 4. 두 글자에서 시작된 해독

{c10}

여러 언어 가운데 독일어가 아주 조금 더 그럴듯했습니다. 게다가 책은 독일에 있었고, '필립'이라는 이름도 독일식으로 p를 두 번 써 있었습니다. 세 사람은 독일어에 걸기로 했습니다.

{c11}

독일어에서 C 뒤에는 거의 언제나 H가 옵니다. 암호에서도 늘 붙어 다니는 두 기호가 있었습니다. 세 사람은 그 둘을 C와 H로 놓았습니다. 독일어에 흔한 글자 묶음과 맞으면 남기고, 맞지 않으면 버렸습니다. 비슷하게 쓰이는 기호 무리는 같은 글자로 한꺼번에 바꿨습니다. 실마리가 줄줄이 풀렸습니다.

{c12}

그때 한 줄에서 두 낱말이 떠올랐습니다. '체레모니 데어 아우프나메', 입회 의식이라는 뜻의 독일어였습니다. 두 낱말 사이에는 로마자가 하나 끼어 있었습니다. 진짜 내용이라 믿었던 로마자는 띄어쓰기였던 것입니다. 처음 생각과 정반대로, 기묘한 기호들이 거의 모든 내용을 담고 있었습니다.

{c13}

남은 수수께끼도 하나씩 풀렸습니다. 쌍점은 앞의 자음을 한 번 더 쓰라는 표시였고, 한 기호는 세 글자 SCH를 한꺼번에 나타냈습니다. 그렇게 해서 모임이라는 뜻의 '게젤샤프트' 같은 낱말이 하나씩 제 모습을 찾았습니다. 마지막으로 독일어를 모국어로 쓰는 셰퍼가 옛 독일어 문장을 다듬었습니다. 몇 주 만에, 책의 첫 부분이 읽히기 시작했습니다.

## 5. 눈의 결사

{c14}

첫 문장은 이랬습니다. 법전, 비밀 부분, 수습생을 위한 비밀 가르침, 그리고 입회 의식. 메기시는 한 기호가 눈을 뜻한다는 것을 알아챘고, 셰퍼는 이것을 18세기 독일의 한 비밀결사와 연결했습니다.

{c15}

스스로를 드높이 깨우친 안과의사 결사라고 부른 사람들이었습니다. 이 결사는 독일 볼펜뷔텔에 있었고, 펠트하임 백작이 이끈 것으로 알려져 있습니다. 그들에게 눈과 시력은 지식과 깨달음을 뜻했습니다. 그렇다면 이어서, 그들의 입회 의식을 들여다보겠습니다.

## 6. 빈 종이를 읽어라

{c16}

문지기가 주위의 안전을 확인하면, 의식을 이끄는 사람이 모자를 써서 모임의 시작을 알립니다. 젊은 문지기가 다른 방에서 후보자를 데려와, 손을 잡고 탁자 앞으로 이끕니다.

{c17}

의식을 이끄는 사람이 묻습니다. 결사에 들어오기를 원하는가. 규칙을 따르며 수습 기간을 견디겠는가. 결사의 비밀을 지키겠는가. 후보자는 그렇다고 답합니다.

{c18}

이제 후보자는 종이 한 장을 받고 읽어 보라는 말을 듣습니다. 종이에는 아무것도 쓰여 있지 않습니다. 읽을 수 없다고 하면 안경을 씌워 다시 읽게 하고, 천으로 눈을 씻긴 뒤 또 읽게 합니다.

{c19}

그리고 마지막으로 이른바 수술이 이어집니다. 족집게로 후보자의 눈썹 한 올을 뽑는 것입니다.

{c20}

실제 안과 수술을 흉내 낸 이 의식은 낯설고 조금 우스워 보이기도 합니다. 그런데 이들은 왜 이렇게까지 모든 것을 암호로 숨겼을까요? 그 답은 곧 로마에서 나옵니다.

## 7. 금지된 모임

{c21}

1738년, 교황 클레멘스 12세는 비밀결사 프리메이슨을 금지하는 교서를 내렸습니다. 가톨릭 신자는 그 모임에 들어갈 수 없게 되었습니다.

{c22}

연구자들은 안과의사 결사가 금지된 프리메이슨의 의식을 몰래 이어 가려고 만든 모임이었을 수 있다고 봅니다. 펠트하임 백작 역시 프리메이슨이었던 것으로 보입니다.

{c23}

책에는 끝내 글자로 풀리지 않은 큰 기호 여덟 개도 있습니다. 결사의 이름과 높은 사람들을 가리키는 것으로 보이는, 비밀 속의 비밀입니다.

{c24}

스웨덴 역사학자 안드레아스 왼너포르스는 책에서 사람이 타고난 권리, 자연권에 대한 이야기를 찾아냈습니다. 계몽주의 시대의 비밀결사는 왕과 교회 앞에서 꺼내기 어려운 생각을 나누는 곳이기도 했습니다. 그리고 이어서, 해독 그 뒤의 이야기입니다.

## 8. 컴퓨터가 여는 옛 암호

{c25}

볼펜뷔텔의 기록 보관소에는 같은 결사의 다른 문서도 남아 있습니다. 세 사람은 같은 방식으로 쓴 암호 문서가 더 있을 것이라고 말했습니다.

{c26}

코피알레 해독 뒤, 나이트와 메기시는 다른 옛 암호에도 도전했습니다. 바티칸 도서관의 400쪽이 넘는 보르그 암호는 17세기 라틴어 의학 책이었습니다. 여러 병과 증상을 다스리는 방법이 적혀 있었습니다. 메기시가 이끄는 연구 모임은 지금도 유럽 곳곳의 옛 암호 문서를 모아 컴퓨터로 풀고 있습니다.

{c27}

눈썹 한 올을 뽑으며 깨달음을 약속했던 사람들. 그들이 기호 속에 숨긴 목소리는 수백 년 뒤 컴퓨터의 계산으로 다시 들려왔습니다. 여러분이라면 빈 종이 앞에서 뭐라고 답하시겠습니까? 댓글로 들려주세요. 보고 나면 가벼운 지식이 남는 이야기, 이 채널에서 계속 이어집니다."""

REFS = {}
SEED = {"c16": 1416, "c17": 1417, "c19": 1419}   # 다시 그린 컷 (어린 소년·19세기 옷·서명 글자, 족집게가 안경에 붙음)
REF_NOTE = ("Any real place or object shown must look exactly like the reference photo (same shape and colors), "
            "painted in the same watercolor style. ")

# 컷 → 사진 후보 이름 (사진후보/후보.json 의 열쇠). 사진을 받은 뒤 채움
PHOTOS = {'c02': 'c02_1', 'c03': 'c03_1', 'c04': 'c04_1', 'c06': 'c06_o1', 'c07': 'c07_2', 'c15': 'c15_4', 'c20': 'c20_o2', 'c21': 'c21_3', 'c22': 'c22_1', 'c24': 'c24_1', 'c25': 'c25_1', 'c26': 'c26_1', 'c05': 'c05_도표', 'c08': 'c08_도표', 'c09': 'c09_도표', 'c10': 'c10_도표', 'c11': 'c11_도표', 'c12': 'c12_도표', 'c13': 'c13_도표', 'c14': 'c14_도표'}


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
        proj = {"ver": 7, "category": "장문", "genre": "[다큐] 역사·미스터리", "topic": "코피알레 암호", "title": TITLE,
                "story": story, "sources": ["https://aclanthology.org/W11-1202/", "https://en.wikipedia.org/wiki/Copiale_cipher", "https://en.wikipedia.org/wiki/Borg_cipher"],
                "notes": "역사 암호 해독 장문 다큐 (실제 사진·암호 원본 위주 + 사진이 없는 장면은 AI 그림)", "autophoto": False, "img_source": "그림: 수채화",
                "settings": {"format": "롱폼 가로(1920×1080)", "narration": "on",
                             "layout": "자막형(큰 제목+사진+자막)", "img_fill": "전체 화면(글자가 사진 위에)",
                             "img_motion": "영상처럼(확대·이동·전환)",
                             "head_show": "안 보임(제목 카드만)", "sub_split": "한 줄씩(문장·쉼표로 나눠 차례로)", "img_label": "on",
                             "narr_voice": "Supertonic M1 (남성, 무료 로컬) [supertonic:M1]", "narr_rate": -8, "narr_tone_m": -2}}   # 장문 다큐 성우(사용자 결정 2026-10-26: 샘플 3번)
        out = os.path.join(HERE, "코피알레_암호.json")
        json.dump(proj, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(out, len(story), "chars")


if __name__ == "__main__":
    main()
