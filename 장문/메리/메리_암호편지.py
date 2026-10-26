"""장문 미스터리 다큐 '메리 스튜어트 여왕의 잃어버린 암호 편지' — 대본 + 컷별 사진·그림 계획
python 장문/메리/메리_암호편지.py job <저장폴더> [c01,...]  → 그림 주문서(다큐 수채화) job.json (사진 컷은 빼고)
python 장문/메리/메리_암호편지.py project <그림폴더>       → 프로젝트 파일 장문/메리/메리_암호편지.json
사실 확인: Lasry·Biermann·Tomokiyo 'Deciphering Mary Stuart's lost letters from 1578-1584'(Cryptologia, 2023-02-08),
CNN·NPR·Scientific American 보도(2023-02). 해독은 컴퓨터 + 사람 손 작업(어느 쪽이 얼마나 했는지는 말하지 않음)"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
TITLE = "메리 스튜어트 여왕의 잃어버린 암호 편지"
STYLE_NAME = "다큐 수채화"
DIALOGUE = []

NP = " No people, no hands, no arms anywhere."
CUTS = [
    ("c01", "a dim archive reading room in Paris with tall shelves of old bound manuscripts, one open folder on a wooden table showing a sheet of handwriting made of strange symbols, soft window light." + NP, "프랑스 국립도서관의 옛 문서"),
    ("c02", "Mary Queen of Scots portrait (real image)", "메리 스튜어트 (1542~1587)"),
    ("c03", "an old sixteenth century letter written entirely in strange cipher symbols in brown ink on yellowed paper, close-up, wax seal beside it, no readable words." + NP, "기호로 가득한 편지"),
    ("c04", "Linlithgow Palace (real photo)", "린리스고 궁전 — 메리가 태어난 곳"),
    ("c05", "Mary Queen of Scots as a child or young queen in France (real image)", "프랑스에서 자란 어린 여왕"),
    ("c06", "Mary in white mourning (real image)", "남편을 잃고 흰 상복을 입은 메리 (옛 판화)"),
    ("c07", "Holyrood Palace Edinburgh (real photo)", "에든버러 홀리루드 궁전"),
    ("c08", "Lochleven Castle (real photo)", "로클레븐 성 — 갇혔다가 탈출한 곳"),
    ("c09", "Elizabeth I portrait (real image)", "잉글랜드 여왕 엘리자베스 1세"),
    ("c10", "Tutbury Castle (real photo)", "터트버리 성 — 메리가 갇혔던 곳"),
    ("c11", "Sheffield Castle or Sheffield Manor Lodge (real photo)", "셰필드 — 15년 가까이 갇혀 지낸 곳"),
    ("c12", "a sixteenth century woman's writing desk by a narrow castle window at night, quill, inkpot, candle, sheets of paper with rows of symbols, dark stone walls." + NP, "갇힌 방의 책상"),
    ("c13", "Bibliotheque nationale de France Richelieu (real photo)", "프랑스 국립도서관"),
    ("c14", "an old leather folder labelled only with a faded tag lying among Italian documents in an archive box, sixteenth century papers, no readable text." + NP, "이탈리아 문서로 잘못 분류된 편지"),
    ("c15", "three people in different countries working on laptops at home desks at night, split into three panels side by side, papers with symbols beside each laptop, warm lamps", "프랑스·독일·일본의 세 사람"),
    ("c16", "a computer screen in a dark room showing columns of strange symbols turning into rows of letters, glowing, abstract decoding visualization, no readable words." + NP, "기호를 글자로 바꾸는 컴퓨터"),
    ("c17", "Francis Walsingham portrait (real image)", "프랜시스 월싱엄"),
    ("c18", "Michel de Castelnau portrait or French embassy London (real image)", "프랑스 대사 미셸 드 카스텔노"),
    ("c19", "a stack of folded sixteenth century letters tied with ribbon on a dark wooden table beside a candle, secret correspondence, no readable text." + NP, "57통의 편지"),
    ("c20", "James VI of Scotland as a young king (real image)", "아들 제임스 6세"),
    ("c21", "The National Archives Kew building (real photo)", "영국 국립기록보관소"),
    ("c22", "Chartley Castle or Chartley Hall (real photo)", "차틀리 — 마지막으로 갇힌 곳"),
    ("c23", "a wooden beer barrel in a sixteenth century cellar with a small hidden leather pouch tucked into its stopper, candle light, secret." + NP, "맥주 통 마개 속 편지"),
    ("c24", "a sixteenth century secret letter in cipher symbols with a short added postscript at the bottom in different ink, lying on a desk beside a broken wax seal, candle light, no readable words." + NP, "배빙턴 음모의 암호 편지"),
    ("c25", "a sixteenth century clerk seen from behind at a desk copying a letter by candlelight, forging handwriting, quill, wax seals", "가짜 추신"),
    ("c26", "Fotheringhay Castle site (real photo)", "포더링헤이 성터"),
    ("c27", "execution of Mary Queen of Scots historical illustration (real image)", "1587년 2월 8일 (옛 그림)"),
    ("c28", "Mary Queen of Scots engraving (real image)", "메리 스튜어트 (옛 판화)"),
    ("c29", "an old archive with endless shelves of boxed manuscripts fading into darkness, a single lamp, many unopened folders." + NP, "아직 읽지 않은 암호 문서들"),
    ("c30", "a single folded old letter with a red wax seal lying on a dark velvet cloth under a soft beam of light, quiet mysterious closing image." + NP, "아직 끝나지 않은 이야기"),
]

STORY = """{c01}

메리 스튜어트 여왕의 잃어버린 편지는 400여 년 동안 프랑스 국립도서관에 숨어 있었습니다. 그것을 디지털 문서 보관소에서 찾아낸 것은 세 사람의 암호 연구가였습니다.

{c03}

편지는 처음부터 끝까지 알 수 없는 기호로 쓰여 있었습니다. 도서관 목록에는 16세기 전반의 이탈리아 문서라고 적혀 있었습니다.

{c02}

하지만 이 편지를 쓴 사람은 이탈리아인이 아니었습니다. 메리 스튜어트, 스코틀랜드의 여왕이었습니다. 끝까지 보시면, 사형대에 오르기 전 그녀가 기호 속에 숨겨 둔 목소리를 듣게 되실 겁니다.

## 1. 태어난 지 엿새 만에 여왕이 된 아이

{c04}

1542년 12월, 스코틀랜드 린리스고 궁전에서 메리가 태어났습니다. 그리고 엿새 뒤, 아버지가 세상을 떠났습니다. 메리는 태어난 지 엿새 만에 여왕이 되었습니다.

{c05}

다섯 살에 프랑스로 건너간 메리는 프랑스 궁정에서 자랐습니다.

{c06}

열다섯 살에는 프랑스 왕세자와 결혼했고, 이듬해 프랑스의 왕비가 되었습니다. 하지만 남편은 2년도 안 되어 세상을 떠났습니다.

{c07}

열여덟 살의 메리는 스코틀랜드로 돌아왔습니다. 그러나 이어서, 그녀의 삶은 걷잡을 수 없이 흔들리기 시작합니다.

## 2. 19년 동안 갇힌 여왕

{c08}

1567년, 반란을 일으킨 귀족들은 메리를 성에 가두고 왕위에서 물러나게 했습니다. 메리는 성을 탈출해 잉글랜드로 도망쳤습니다.

{c09}

잉글랜드의 여왕은 사촌인 엘리자베스 1세였습니다. 하지만 메리는 잉글랜드 왕위를 이을 수도 있는 사람이었습니다. 엘리자베스에게 메리는 손님이 아니라 위험한 경쟁자였습니다.

{c10}

메리는 이 성에서 저 성으로 옮겨 다니며 갇혀 지냈습니다. 그 세월이 19년이었습니다. 그중 15년 가까이는 슈루즈버리 백작의 감시 아래 셰필드에서 보냈습니다.

{c11}

감시는 갈수록 심해졌습니다. 메리가 바깥과 이야기할 방법은 오직 하나, 몰래 주고받는 편지뿐이었습니다. 그리고 그 편지는 반드시 암호로 써야 했습니다.

{c12}

갇힌 방에서 쓴 수많은 편지. 그런데 그 편지들은 어디로 사라졌을까요? 그 답은 곧, 400여 년 뒤 파리에서 나옵니다.

## 3. 이탈리아 문서 속 낯선 기호

{c13}

프랑스 국립도서관에는 수백 년 된 암호 문서가 많이 남아 있습니다. 세 사람은 이런 옛 암호를 찾아 푸는 연구 모임에서 함께 활동하고 있었습니다.

{c15}

프랑스의 컴퓨터 과학자 조르주 라스리, 독일의 피아니스트이자 음악 교수 노르베르트 비어만, 일본의 물리학자 도모키요 사토시. 모두 취미로 옛 암호를 풀어 온 사람들이었습니다.

{c14}

이들이 찾은 편지 묶음은 이탈리아 문서들 사이에 섞여 있었습니다. 수백 년 동안 아무도 제대로 들여다보지 않은 것입니다. 이어서, 세 사람이 기호를 어떻게 글자로 바꿨는지 보겠습니다.

## 4. 기호를 글자로

{c16}

편지에는 알파벳보다 훨씬 많은 종류의 기호가 쓰였습니다. 한 글자를 여러 기호로 바꿔 쓰고, 자주 나오는 낱말이나 사람 이름은 기호 하나로 대신하는 방식이었습니다.

{c03}

세 사람은 컴퓨터 프로그램과 사람의 손을 함께 써서 기호와 글자의 짝을 하나씩 찾아 나갔습니다. 그러자 놀랍게도, 이탈리아어가 아니라 프랑스어 문장이 나타났습니다. 실마리가 잡히자, 나머지 기호의 뜻도 앞뒤 문맥으로 하나씩 맞혀 나갔습니다.

{c17}

문장 속에는 여성형으로 쓰인 낱말, 갇혀 지낸다는 이야기, 그리고 한 사람의 이름이 있었습니다. 엘리자베스의 비밀 정보 책임자, 프랜시스 월싱엄. 그 순간 세 사람은 깨달았습니다. 이 편지를 쓴 사람은 메리 스튜어트였습니다. 그렇다면 곧, 그 편지에는 무엇이 적혀 있었을까요?

## 5. 편지 속 여왕의 목소리

{c18}

편지의 대부분은 런던에 있던 프랑스 대사 미셸 드 카스텔노에게 보낸 것이었습니다. 1578년부터 1584년 사이에 쓰였습니다.

{c19}

해독된 편지는 모두 57통, 5만 단어가 넘는 분량이었습니다. 메리는 갇힌 생활의 괴로움과 나빠지는 건강, 그리고 풀려나기 위한 협상을 이야기했습니다.

{c20}

1582년, 어린 아들 제임스가 스코틀랜드 귀족들에게 납치되듯 붙잡혔을 때, 메리는 깊은 슬픔과 걱정을 털어놓았습니다. 이 아들은 훗날 잉글랜드의 왕 제임스 1세가 됩니다.

{c21}

이 가운데 7통은 당시 월싱엄의 정보망이 이미 가로채 해독해 둔 사본이 영국 국립기록보관소에 남아 있었습니다. 세 사람은 이 사본과 비교해 자신들의 해독이 맞다는 것을 확인했습니다. 그리고 이어서, 월싱엄의 정보망이 결국 메리를 어떻게 무너뜨렸는지 보겠습니다.

## 6. 월싱엄의 덫

{c22}

1586년, 메리는 차틀리라는 곳에 갇혀 있었습니다. 바깥과의 편지는 모두 끊긴 상태였습니다.

{c23}

그런데 새로운 길이 열렸습니다. 성에 들어오는 맥주 통의 마개 속에 편지를 숨겨 주고받는 방법이었습니다. 하지만 이 길은 처음부터 월싱엄이 만든 덫이었습니다.

{c24}

젊은 귀족 앤서니 배빙턴은 엘리자베스를 몰아내고 메리를 구하려는 계획을 메리에게 알렸습니다. 메리는 암호 편지로 답했습니다. 그 편지는 모두 월싱엄의 손을 거쳐 해독되었습니다.

{c23}

편지를 전하던 길버트 기퍼드는 사실 월싱엄을 위해 일하는 이중 첩자였습니다. 암호는 월싱엄 밑의 해독 전문가 토머스 펠리페스가 풀었습니다.

{c25}

월싱엄 쪽은 메리의 편지에 가짜 추신까지 덧붙여, 함께한 사람들의 이름을 알아내려 했습니다. 이 편지들이 결국 메리를 재판에 세웠습니다. 그리고 곧, 마지막 아침이 찾아옵니다.

## 7. 포더링헤이의 마지막 아침

{c26}

1587년 2월 8일, 잉글랜드 포더링헤이 성. 메리는 44살이었습니다. 넉 달 전 열린 재판에서 그녀는 반역을 꾀했다는 판결을 받았고, 엘리자베스는 오랫동안 망설이다 사형 집행 명령서에 서명했습니다.

{c27}

메리는 붉은 옷을 입고 사형대에 올랐다고 전해집니다. 그녀를 무너뜨린 것은 암호였고, 400여 년 뒤 그녀의 목소리를 되살린 것도 암호였습니다.

{c28}

메리의 아들 제임스는 훗날 잉글랜드의 왕이 되었고, 어머니의 무덤을 웨스트민스터 사원으로 옮겼습니다. 엘리자베스와 메리는 지금 같은 사원에 잠들어 있습니다. 그리고 이어서, 다시 400여 년 뒤의 이야기로 돌아가 보겠습니다.

## 8. 아직 끝나지 않은 해독

{c29}

세 사람은 2023년 2월 8일, 메리가 처형된 바로 그날에 맞춰 연구 결과를 발표했습니다. 하지만 라스리는 해독은 시작일 뿐이라고 말했습니다. 이제 역사학자들이 편지의 뜻을 하나하나 읽어 낼 차례입니다.

{c13}

세 사람이 속한 DECRYPT라는 국제 연구 모임은 유럽 곳곳의 옛 암호 문서를 모아 디지털로 정리하고 있습니다. 전 세계 도서관에는 아직 아무도 읽지 못한 암호 문서가 수없이 잠들어 있습니다. 그 속에 또 어떤 목소리가 숨어 있을지 모릅니다.

{c30}

사형대에 오르기 전까지 기호 속에 마음을 숨겼던 여왕. 여러분은 다음에 어떤 잃어버린 편지가 발견될 것 같나요? 댓글로 여러분의 생각을 들려주세요. 보고 나면 가벼운 지식이 남는 이야기, 이 채널에서 계속 이어집니다."""

REFS = {}
REF_NOTE = ("Any real place or object shown must look exactly like the reference photo (same shape and colors), "
            "painted in the same watercolor style. ")

# 컷 → 사진 후보 이름 (사진후보/후보.json 의 열쇠). 사진을 받은 뒤 채움
PHOTOS = {'c02': 'c02_2', 'c04': 'c04_1', 'c05': 'c05_1', 'c06': 'c02_3', 'c07': 'c07_1', 'c08': 'c08_2', 'c09': 'c09_3', 'c10': 'c10_1', 'c11': 'c11_3', 'c13': 'c13_4', 'c17': 'c17_1', 'c18': 'c18_1', 'c20': 'c20_1', 'c21': 'c21_2', 'c22': 'c22_2', 'c26': 'c26_1', 'c27': 'c27_1', 'c28': 'c02_4'}


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
            items.append({"id": cid, "width": 1024, "height": 576, "seed": 300 + int(cid[1:]), "refs": refs,
                          "prompt": f"{style}, historical documentary illustration, realistic proportions, museum-quality painting. "
                                    f"Scene: {desc}. {REF_NOTE if refs else ''}{'' if 'no people' in desc.lower() else 'Every person has exactly two arms, two hands with five fingers each and two legs, hands simple and relaxed (partly hidden is fine). '}"
                                    "Cinematic composition, full-bleed image, no border, no frame, no paper edges. No text, no letters, no captions."})
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
                credit = f"{m['artist'] or 'Wikimedia Commons'} / {m['license']} / Wikimedia Commons"
                story = story.replace("{" + cid + "}", f"[사진: {img} | {cap} | {credit} | {m['page']}]")
                continue
            img = next((os.path.join(folder, cid + e) for e in (".png", ".jpg") if os.path.exists(os.path.join(folder, cid + e))), os.path.join(folder, cid + ".png"))
            story = story.replace("{" + cid + "}", f"[사진: {img} | {cap} | AI 그림 (FLUX.2 klein, 수채화) | ]")
        proj = {"ver": 7, "category": "장문", "genre": "[다큐] 역사·미스터리", "topic": "메리 스튜어트 암호 편지", "title": TITLE,
                "story": story, "sources": ["https://www.tandfonline.com/doi/full/10.1080/01611194.2022.2160677", "https://www.npr.org/2023/02/10/1155701113/mary-queen-of-scots-ciphers-prison-letters"],
                "notes": "역사 암호 해독 장문 다큐 (실제 사진·암호 원본 위주 + 사진이 없는 장면은 AI 그림)", "autophoto": False, "img_source": "그림: 수채화",
                "settings": {"format": "롱폼 가로(1920×1080)", "narration": "on",
                             "layout": "자막형(큰 제목+사진+자막)", "img_fill": "전체 화면(글자가 사진 위에)",
                             "img_motion": "영상처럼(확대·이동·전환)",
                             "head_show": "안 보임(제목 카드만)", "sub_split": "한 줄씩(문장·쉼표로 나눠 차례로)", "img_label": "on",
                             "narr_voice": "Supertonic M1 (남성, 무료 로컬) [supertonic:M1]", "narr_rate": -8, "narr_tone_m": -2}}   # 장문 다큐 성우(사용자 결정 2026-10-26: 샘플 3번)
        out = os.path.join(HERE, "메리_암호편지.json")
        json.dump(proj, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(out, len(story), "chars")


if __name__ == "__main__":
    main()
