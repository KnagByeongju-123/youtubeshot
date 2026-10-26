"""장문 미스터리 다큐 '51년 만에 풀린 조디악 살인마의 암호' — 대본 + 컷별 사진·그림 계획
python 장문/조디악/조디악_암호.py job <저장폴더> [c01,...]  → 그림 주문서(다큐 수채화) job.json (사진·도표 컷은 빼고)
python 장문/조디악/조디악_암호.py project <그림폴더>       → 프로젝트 파일 장문/조디악/조디악_암호.json
사실 확인: Blake·Oranchak·Van Eycke 'Solving the Zodiac 340 cipher'(arXiv 2403.17350, 2024), FBI 성명(2020-12-11),
Vice·The Register(2020-12) 보도. 실제 범죄·피해자가 있는 사건 → 자극적인 묘사 없이 암호와 해독 과정 중심 (주제 기록 규칙)
정확히 말할 것: 340 암호를 푼 것은 'AI'가 아니라 사람 3명 + 컴퓨터 탐색 프로그램(AZdecrypt)"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
TITLE = "51년 만에 풀린 조디악 살인마의 암호"
STYLE_NAME = "다큐 수채화"
DIALOGUE = []

NP = " No people, no hands, no arms anywhere."
# (컷번호, 그림 설명(영어), 화면 설명(한국어))
CUTS = [
    ("c01", "Zodiac 340 cipher original (real image)", "1969년 11월 신문사에 온 340 암호"),
    ("c02", "a 1969 San Francisco newspaper newsroom at night, a single envelope and a sheet of strange handwritten symbols lying on a cluttered desk under a desk lamp, typewriters around, empty room." + NP, "1969년 신문사 편집국"),
    ("c03", "San Francisco skyline in 1960s (real photo)", "1960년대 샌프란시스코"),
    ("c04", "Zodiac 340 cipher close-up (diagram)", "51년 동안 아무도 읽지 못한 기호"),
    ("c05", "San Francisco Bay Area foggy night road near Vallejo, empty two-lane country road with a single street lamp, 1960s mood, eerie." + NP, "베이 에어리어의 밤길"),
    ("c06", "Zodiac killer police composite sketch 1969 (real image)", "경찰이 공개한 몽타주 (1969)"),
    ("c07", "Zodiac letter with crossed circle symbol (real image)", "조디악의 편지와 십자 원 표시"),
    ("c08", "three 1969 American newspapers stacked on a wooden table, front pages with large blurry headline blocks and rows of strange symbols, no readable words." + NP, "세 신문사에 나뉘어 온 첫 암호 (발레이오 타임스-헤럴드 조각)"),
    ("c09", "Zodiac 408 cipher (real image)", "408 암호 (1969년 7월)"),
    ("c10", "a middle-aged schoolteacher and his wife sitting at a 1960s kitchen table at night, working together on sheets of paper covered with symbols, pencils, coffee cups, warm lamp light", "부엌 식탁에서 암호를 푼 부부"),
    ("c11", "Zodiac 408 cipher part (real image)", "408 암호 (크로니클 조각, 확대)"),
    ("c12", "San Francisco Chronicle building (real photo)", "샌프란시스코 크로니클 건물 장식"),
    ("c13", "Zodiac 340 cipher full (real image)", "340 암호 — 20줄 17칸"),
    ("c14", "a 1970s government codebreaking office with large early computers, tape reels and printouts of symbol grids pinned on a wall, empty room." + NP, "정부 암호 전문가들의 시도"),
    ("c15", "Zodiac 340 symbol count (diagram)", "기호 63가지"),
    ("c16", "a desk in a modern home office at night, a computer monitor glowing with a grid of colorful abstract symbols, notebooks with scribbles, coffee mug, no readable text." + NP, "50년 동안 이어진 도전"),
    ("c17", "Zodiac 340 cipher key (real image)", "세 사람이 밝혀낸 340 암호의 기호표"),
    ("c18", "a world map watercolor with three glowing points in the eastern United States, Australia and Belgium connected by thin light lines, no text, no letters, no labels." + NP, "미국·호주·벨기에의 세 사람"),
    ("c19", "Zodiac 340 diagonal reading (diagram)", "대각선으로 읽는 순서"),
    ("c20", "a computer screen in a dark room showing thousands of small grids rearranging in waves, glowing blue and green, abstract visualization, no text." + NP, "65만 가지 읽는 순서를 시험한 컴퓨터"),
    ("c21", "Zodiac 340 three sections (diagram)", "세 부분으로 나뉜 암호"),
    ("c22", "a man seen from behind sitting in front of a computer monitor late at night, leaning forward in surprise, room lit only by the screen, the screen shows a blurry grid of letters", "처음 문장이 보인 순간"),
    ("c23", "1969 television studio with a talk show set, a vintage telephone on the desk, studio cameras, empty chairs." + NP, "1969년 아침 TV 토크쇼"),
    ("c24", "Zodiac 340 solution text (diagram)", "340 암호에 적힌 말"),
    ("c25", "San Quentin State Prison (real photo)", "샌 퀜틴 교도소 (가스실이 있던 곳)"),
    ("c26", "FBI headquarters building (real photo)", "FBI 본부"),
    ("c27", "FBI seal (real image)", "FBI 확인 (2020년 12월)"),
    ("c28", "a single sheet of old paper with a short row of thirteen strange symbols under the words written in a scribbled hand, lying on a dark desk, mysterious, no readable text." + NP, "아직 풀리지 않은 13글자 암호"),
    ("c29", "Mount Diablo California (real photo)", "디아블로산"),
    ("c30", "Zodiac 32 cipher (real image)", "32 암호 (1970년 6월)"),
    ("c31", "a stack of old case files and evidence envelopes tied with string in a dim police archive room, dust in light beams." + NP, "50년 넘게 쌓인 수사 기록"),
    ("c32", "Paul Stine crime scene area Presidio Heights San Francisco street (real photo)", "샌프란시스코 프레시디오 하이츠"),
    ("c33", "a magnifying glass over an old handwritten envelope with a stamp, forensic lab table, DNA swab beside it." + NP, "봉투에서 찾은 DNA"),
    ("c34", "a glowing abstract network of nodes and lines over a dark grid of symbols, computer pattern search visualization, no text." + NP, "컴퓨터 탐색과 사람의 직관"),
    ("c35", "Golden Gate Bridge in fog (real photo)", "안개 속 금문교"),
    ("c36", "an old lamp-lit desk at night with a blank sheet of paper and a pencil, a single unanswered envelope, quiet and mysterious closing image." + NP, "아직 끝나지 않은 이야기"),
]

STORY = """{c01}

1969년 11월, 연쇄 살인범 조디악이 미국 샌프란시스코의 한 신문사에 편지를 보냈습니다. 안에는 340개의 이상한 기호가 빼곡히 적혀 있었습니다.

{c02}

그는 신문사에 편지를 보내며 경찰을 조롱하던 범인이었습니다. 이 암호 안에도 자신에 대한 무언가를 숨겼을 거라고 모두가 믿었습니다.

{c04}

FBI도, 국가 암호 기관도, 수많은 전문가들도 이 암호를 읽지 못했습니다. 그렇게 51년이 흘렀습니다.

{c13}

그리고 2020년 12월, 마침내 이 암호가 풀렸습니다. 끝까지 보시면, 그 안에 적힌 말과 아직 아무도 풀지 못한 암호 두 개의 이야기를 알게 되실 겁니다.

## 1. 편지를 보내는 살인범

{c03}

1968년 말부터 1969년까지, 샌프란시스코 만 일대에서 젊은이들이 잇따라 공격을 당했습니다.

{c05}

인적이 드문 밤길과 호숫가, 그리고 도심의 택시 안. 경찰이 확인한 사망자는 다섯 명, 살아남은 사람은 두 명이었습니다.

{c06}

경찰은 목격자들의 말을 바탕으로 몽타주를 만들어 공개했습니다. 하지만 범인은 잡히지 않았습니다.

{c07}

이 사건이 유난히 기억되는 이유가 있습니다. 범인이 신문사에 직접 편지를 보냈기 때문입니다. 편지 끝에는 원 안에 십자가를 그린 표시가 있었습니다. 그는 자신을 조디악이라고 불렀습니다.

{c03}

그는 1974년까지 신문사에 스무 통이 넘는 편지를 보냈고, 자신이 죽인 사람이 37명이라고 주장했습니다. 하지만 경찰이 확인한 피해자는 일곱 명이었습니다.

{c08}

1969년 7월, 그는 세 신문사에 암호를 세 조각으로 나누어 보냈습니다. 이 암호를 신문 1면에 싣지 않으면 또 사람을 해치겠다고 위협했습니다. 신문들은 결국 암호를 실었습니다. 그런데 곧, 뜻밖의 사람들이 이 암호를 풀어냅니다.

## 2. 일주일 만에 풀린 첫 암호

{c09}

408개의 기호로 된 첫 번째 암호. 세 조각은 각각 136개의 기호였습니다. 신문에 실리자 수많은 독자가 풀이에 뛰어들었습니다.

{c10}

일주일쯤 뒤, 캘리포니아의 한 고등학교 교사 도널드 하든과 아내 베티가 이 암호를 풀었습니다. 부엌 식탁에 앉아서였습니다.

{c11}

베티는 범인이 자기 자랑을 좋아할 것이라 보고, 문장이 '나'로 시작하고 '죽이다'라는 낱말이 들어 있을 거라고 짐작했습니다. 이 짐작이 맞아떨어졌습니다. 한 글자를 여러 기호로 바꿔 쓰는 방식이었습니다.

{c09}

풀린 내용은 섬뜩한 자기 자랑이었습니다. 하지만 그의 이름은 어디에도 없었습니다. 마지막 18글자는 지금도 정확한 뜻을 알 수 없습니다. 그리고 곧, 훨씬 더 어려운 두 번째 암호가 도착합니다.

## 3. 340개의 기호

{c12}

1969년 11월 8일, 샌프란시스코 크로니클에 새 암호가 도착했습니다. 이번에는 340개의 기호였습니다.

{c13}

가로 17칸, 세로 20줄. 기호의 종류는 63가지였습니다. 첫 번째 암호와 같은 방법으로 풀어 보려 했지만, 아무리 해도 말이 되는 문장이 나오지 않았습니다.

{c14}

FBI와 국가 암호 기관의 전문가들도 매달렸습니다. 컴퓨터가 막 쓰이기 시작하던 시절이었습니다. 하지만 아무도 풀지 못했습니다.

{c15}

이후 수십 년 동안 '내가 풀었다'는 사람이 수없이 나타났습니다. 하지만 모두 틀린 답이었습니다. 340 암호는 세계에서 가장 유명한 미해결 암호 가운데 하나가 되었습니다.

{c04}

기호를 글자로 바꾸는 경우의 수는 우주의 별보다도 많습니다. 하나하나 다 시험해 보는 것은 컴퓨터로도 불가능했습니다.

{c16}

그런데 2006년, 한 사람이 이 암호에 도전하기 시작합니다. 이어서, 14년 뒤 답에 닿은 그 사람을 만나 보겠습니다.

## 4. 세 나라의 세 사람

{c17}

미국 버지니아의 소프트웨어 개발자 데이비드 오랜착. 그는 14년 동안 이 암호를 연구하며, 그 과정을 유튜브 영상으로 꾸준히 남겼습니다.

{c18}

그에게는 동료가 두 명 있었습니다. 호주의 수학자 샘 블레이크, 그리고 벨기에의 프로그래머 잘 반 에이크입니다.

{c20}

반 에이크는 암호를 푸는 프로그램, AZdecrypt를 직접 만든 사람이었습니다. 이 프로그램은 기호를 글자로 바꾸는 수많은 경우를 빠르게 시험해, 영어 문장에 가장 가까운 답을 찾아냅니다.

{c16}

영어에서 자주 붙어 나오는 글자 조합에 점수를 매기고, 기호와 글자의 짝을 조금씩 바꿔 가며 점수가 높아지는 쪽으로 계속 고쳐 나가는 방식입니다.

{c19}

세 사람은 한 가지를 의심했습니다. 혹시 이 암호는 왼쪽에서 오른쪽으로 읽는 게 아니라, 기호의 순서까지 뒤섞어 놓은 것은 아닐까. 이어서, 그 의심이 어떻게 답이 되었는지 보겠습니다.

## 5. 65만 가지 읽는 순서

{c20}

블레이크는 암호를 읽을 수 있는 순서를 약 65만 가지나 만들었습니다. 위에서 아래로, 대각선으로, 거꾸로. 그리고 그 하나하나를 반 에이크의 프로그램에 넣어 시험했습니다.

{c21}

2020년 12월 초, 오랜착의 화면에 낯익은 낱말들이 떠올랐습니다. '나를 잡으려고', '가스실', '천국'. 수십 년 동안 한 번도 나온 적 없는 말들이었습니다.

{c19}

비밀은 읽는 순서에 있었습니다. 암호는 위의 9줄, 가운데 9줄, 아래 2줄, 세 부분으로 나뉘어 있었습니다. 그리고 앞의 두 부분은 한 줄 내려갈 때마다 두 칸씩 옆으로 건너뛰는 대각선 순서로 읽어야 했습니다.

{c22}

범인은 글자 몇 개를 틀리게 쓰기도 했습니다. 그래서 더 풀기 어려웠습니다. 세 사람은 틀린 곳을 하나씩 바로잡으며 문장을 이어 갔습니다. 그리고 곧, 51년 만에 그 문장 전체가 모습을 드러냅니다.

## 6. 암호 속의 문장

{c24}

풀린 문장은 이렇습니다. '나를 잡으려고 무척 즐거운 시간을 보내고 있기를 바란다. TV 프로그램에 나온 건 내가 아니었다.'

{c23}

이 말에는 사연이 있었습니다. 1969년 10월, 샌프란시스코의 아침 TV 토크쇼에 자신이 조디악이라는 남자가 전화를 걸었습니다. 하지만 그는 진짜가 아니었습니다. 범인은 그걸 바로잡고 싶었던 겁니다.

{c25}

문장은 이렇게 이어집니다. '나는 가스실이 두렵지 않다. 나를 더 빨리 천국으로 보내 줄 테니까.' 그리고 자신이 죽인 사람들이 천국에서 노예가 될 것이라는 말이 뒤따릅니다.

{c24}

이름도, 주소도, 단서가 될 만한 고백도 없었습니다. 오랜착은 이 문장을 두고, 관심을 끌려는 늘 하던 헛소리라고 말했습니다. 이어서, 이 답을 받은 FBI의 반응을 보겠습니다.

## 7. FBI의 확인

{c26}

세 사람은 답을 FBI에 보냈습니다. 그리고 2020년 12월 11일, FBI는 공식 성명을 냈습니다.

{c27}

민간인들이 340 암호를 풀었다는 사실을 확인한다. 하지만 이 사건은 여전히 수사 중이다. 51년 동안 풀리지 않던 암호가 정말로 풀린 순간이었습니다.

{c21}

2024년, 세 사람은 해독 과정을 정리한 논문을 공개했습니다. 누구든 같은 방법으로 답을 확인할 수 있게 된 것입니다. 하지만 이것으로 모든 수수께끼가 끝난 것은 아닙니다. 조디악의 암호는 아직 두 개가 더 남아 있습니다. 이어서, 그 두 암호를 보겠습니다.

## 8. 아직 풀리지 않은 두 암호

{c28}

1970년 4월, 조디악은 짧은 암호를 하나 더 보냈습니다. '내 이름은'이라는 말 뒤에, 기호 13개가 적혀 있었습니다.

{c29}

같은 해 6월에는 기호 32개로 된 암호를 지도와 함께 보냈습니다. 디아블로산 근처에 폭탄을 숨겼다는 내용이었습니다.

{c30}

이 두 암호는 지금도 풀리지 않았습니다. 기호가 너무 적어서, 말이 되는 답이 수없이 많이 나오기 때문입니다. 어느 답이 진짜인지 가려낼 수가 없는 것입니다.

{c31}

범인의 정체도 여전히 밝혀지지 않았습니다. 가장 유력한 용의자로 꼽힌 남자가 있었지만, 그는 1992년에 세상을 떠났습니다.

{c33}

훗날 편지 봉투에서 얻은 DNA 일부와 그의 DNA를 비교했지만, 일치하지 않았습니다. 2021년에는 한 민간 조사팀이 범인을 찾았다고 주장했지만, FBI는 이를 인정하지 않았습니다. 그렇다면 340 암호는 정말 무엇이 풀었을까요? 곧, 그 답을 짚어 보겠습니다.

## 9. 컴퓨터와 사람

{c34}

340 암호를 푼 것은 스스로 생각하는 인공지능이 아니었습니다. 엄청난 경우의 수를 빠르게 시험하는 컴퓨터 프로그램과, 어떤 순서를 시험할지 끈질기게 고민한 세 사람이었습니다.

{c32}

컴퓨터는 사람이 10년 걸려도 못 할 계산을 며칠 만에 해냈습니다. 하지만 '읽는 순서가 뒤섞였을지 모른다'는 생각은 사람에게서 나왔습니다.

{c35}

오늘날 과학자들은 인공지능으로 오래된 문서와 깨진 비문을 읽어 내고 있습니다. 언젠가는 13개의 기호에 숨은 이름도 밝혀질지 모릅니다.

{c36}

51년 만에 입을 연 340개의 기호. 하지만 그 기호를 쓴 사람은 아직 어둠 속에 있습니다. 여러분은 조디악의 마지막 두 암호가 언젠가 풀릴 거라고 생각하시나요? 댓글로 여러분의 생각을 들려주세요. 보고 나면 가벼운 지식이 남는 이야기, 이 채널에서 계속 이어집니다."""

REFS = {}
REF_NOTE = ("Any real place or object shown must look exactly like the reference photo (same shape and colors), "
            "painted in the same watercolor style. ")

# 컷 → 사진 후보 이름 (사진후보/후보.json 의 열쇠). 사진·도표를 만든 뒤 채움
PHOTOS = {'c01': 'c13_1', 'c13': 'c13_1', 'c03': 'c03_1', 'c06': 'c06_1', 'c07': 'c07_1', 'c09': 'c09_2', 'c11': 'c11_확대', 'c08': 'c08_1', 'c12': 'c12_4', 'c17': 'c01_1', 'c25': 'c25_1', 'c26': 'c26_1', 'c27': 'c27_2', 'c29': 'c29_2', 'c30': 'c30_1', 'c32': 'c32_2', 'c35': 'c35_2', 'c04': 'c04_도표', 'c15': 'c15_도표', 'c19': 'c19_도표', 'c21': 'c21_도표', 'c24': 'c24_도표', 'c18': 'c18_도표'}


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
        proj = {"ver": 7, "category": "장문", "genre": "[다큐] 역사·미스터리", "topic": "조디악 340 암호", "title": TITLE,
                "story": story, "sources": ["https://arxiv.org/abs/2403.17350", "https://www.fbi.gov/contact-us/field-offices/sanfrancisco/news/press-releases/fbi-statement-on-zodiac-killer-cipher"],
                "notes": "미제 사건 암호 해독 장문 다큐 (실제 사진·암호 원본 위주 + 사진이 없는 장면은 AI 그림)", "autophoto": False, "img_source": "그림: 수채화",
                "settings": {"format": "롱폼 가로(1920×1080)", "narration": "on",
                             "layout": "자막형(큰 제목+사진+자막)", "img_fill": "전체 화면(글자가 사진 위에)",
                             "img_motion": "영상처럼(확대·이동·전환)",
                             "head_show": "안 보임(제목 카드만)", "sub_split": "한 줄씩(문장·쉼표로 나눠 차례로)", "img_label": "on",
                             "narr_voice": "Supertonic M1 (남성, 무료 로컬) [supertonic:M1]", "narr_rate": -8, "narr_tone_m": -2}}   # 장문 다큐 성우(사용자 결정 2026-10-26: 샘플 3번)
        out = os.path.join(HERE, "조디악_암호.json")
        json.dump(proj, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(out, len(story), "chars")


if __name__ == "__main__":
    main()
