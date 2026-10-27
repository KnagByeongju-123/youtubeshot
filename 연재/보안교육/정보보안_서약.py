"""정보보안 교육 영상 '정보보안 서약, 이렇게 지켜요' — 대본 + 컷별 그림 계획 (사내 정보보안 서약서 8개 항목 + 관리자 추가 서약)
python 연재/보안교육/정보보안_서약.py job <저장폴더>   → 그림 주문서(klein_worker 용) job.json
python 연재/보안교육/정보보안_서약.py project <그림폴더> → 프로젝트 파일(render_project 용) 연재/보안교육/정보보안_서약.json
  영상은 render_project.py <프로젝트> --대본그대로 --길이고정 (교육 영상이라 5분 그대로, 오프닝을 고쳐 쓰지 않게)
회사·고객사 이름은 넣지 않고 '우리 회사'로 (사용자 결정)
대본의 {컷번호} 자리에 그 컷 그림이 들어감. chars = 그 컷에 나오는 인물(캐릭터 시트를 기준 그림으로 넣음)"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TITLE = "정보보안 서약, 이렇게 지켜요"

# 대사 → 말하는 인물 (그 인물 목소리로 읽음, 목소리는 등장인물.json 의 voice)
DIALOGUE = [
    ("민수 씨, 입사를 축하해요. 일을 시작하기 전에 이 서약서부터 같이 읽어 볼까요?", "박 팀장"),
    ("서약서요? 그냥 사인만 하면 되는 거 아니에요?", "민수"),
    ("이 도면, 친구한테 살짝 보여 줘도 되죠? 우리 회사 기술이 이렇게 대단하다고요.", "민수"),
    ("민수 씨, 비밀번호는 머릿속에만 두세요. 화면에 붙여 두면 누구나 볼 수 있어요.", "박 팀장"),
    ("민수 씨, 내 아이디로 잠깐 들어가서 그 자료 좀 봐 줄래요?", "옆자리 선배"),
    ("죄송해요, 선배님. 아이디는 빌려 드릴 수가 없어요.", "민수"),
    ("집에서 마저 보려고 화면을 찍어 두려는데요.", "민수"),
    ("잠깐만요. 회사 자료는 사진도, 개인 메일도, USB 도 안 돼요.", "박 팀장"),
    ("택배 배송 조회? 저 택배 시킨 적 없는데...", "민수"),
    ("팀장님, 이상한 메일을 열어 버린 것 같아요!", "민수"),
    ("잘했어요. 바로 알려 준 게 제일 중요해요. 랜선부터 뽑아 둘게요.", "박 팀장"),
    ("이 게임 프로그램, 잠깐만 깔아도 되겠죠?", "민수"),
    ("그동안 쓰던 자료와 노트북, 모두 반납합니다.", "민수"),
    ("이제 알겠어요. 서약서는 사인하는 종이가 아니라, 매일 지키는 약속이네요.", "민수"),
    ("맞아요. 그 약속이 우리 회사와 우리 모두를 지켜 줍니다.", "박 팀장"),
]

# (컷번호, 나오는 인물, 그림 설명(영어), 화면 설명(한국어))
CUTS = [
    ("c01", [], "a modern bright Korean corporate office building with glass windows in the morning sunlight, blue sky, trees in front, no people", "아침의 회사 건물"),
    ("c02", ["민수"], "the young man sitting at his new office desk on his first day, excited nervous smile, a new computer monitor and keyboard in front of him, bright open-plan office", "첫 출근한 신입 사원 민수"),
    ("c03", ["박 팀장", "민수"], "the woman manager with glasses standing beside the young man's desk with a kind smile, handing him a single sheet of paper document, he looks up at her curiously, bright office", "서약서를 건네는 박 팀장"),
    ("c04", ["민수"], "the young man at his desk looking at a big monitor showing a detailed mechanical engineering blueprint drawing of a car part, impressed face", "회사의 기술 도면을 보는 민수"),
    ("c05", [], "a neat stack of technical engineering drawings, blueprints and documents on an office desk with a big golden padlock and a chain lying on top, soft light, no people", "자물쇠로 지켜야 할 기술 정보"),
    ("c06", ["박 팀장", "민수"], "close view of an office computer monitor with yellow sticky notes stuck on its frame, the young man sitting in front of it looking embarrassed and scratching his head, the woman manager with glasses standing behind him pointing at the sticky notes with a gentle frown", "모니터에 붙인 비밀번호 쪽지"),
    ("c07", [], "an empty office desk with an empty chair pushed back, a computer monitor showing a dark lock screen with a big white padlock symbol, a coffee mug beside the keyboard, no people", "자리를 비울 땐 화면 잠금"),
    ("c08", ["민수"], "the young man at his desk politely refusing with both palms raised and an apologetic smile, turned toward an older male coworker in a gray suit leaning over his desk partition, bright office", "아이디를 빌려 달라는 선배를 거절하는 민수"),
    ("c09", [], "a computer screen showing a row of colorful file folders, one big folder marked with a red padlock symbol, office desk, no people", "내 권한 밖의 자료"),
    ("c10", ["민수", "박 팀장"], "the young man holding up his smartphone to take a photo of his computer monitor at his desk, the woman manager with glasses rushing in from the side with one hand raised to stop him, surprised faces", "화면을 찍으려다 멈춘 민수"),
    ("c11", [], "flat lay on an office desk: a USB flash drive, a smartphone, a small paper envelope and a little white cloud-shaped toy, each with a big red X mark over it, clean infographic illustration, no people", "USB·개인 메일·클라우드·메신저 반출 금지"),
    ("c12", [], "an office printer with forgotten printed papers left in its output tray, and beside it a paper shredder cutting documents into thin strips, bright office corner, no people", "출력물은 회수하고 파기"),
    ("c13", [], "a clean modern server room with tall rows of server racks with small blinking blue and green lights, cool blue light, no people", "접속·출력 이력이 남는 서버"),
    ("c14", ["박 팀장"], "the woman manager with glasses standing beside a large wall monitor showing simple bar charts and line graphs, explaining with one open hand, confident kind smile, meeting room", "이력 관리를 설명하는 박 팀장"),
    ("c15", ["민수"], "the young man at his desk staring at a laptop screen showing an email with a big fishing hook symbol and a dark warning envelope icon, confused suspicious face, one hand on the mouse", "의심스러운 피싱 메일"),
    ("c16", ["민수"], "the young man standing up at his desk talking urgently on an office desk phone, worried face, his laptop open beside him", "보안담당자에게 바로 신고"),
    ("c17", ["박 팀장", "민수"], "the woman manager with glasses sitting at the young man's laptop unplugging a network cable from it, the young man standing beside her looking relieved, office", "랜선을 뽑는 박 팀장"),
    ("c18", ["민수"], "the young man at his desk about to click a big colorful game download button on his computer screen with the mouse, sneaky grin, an office desk", "몰래 게임을 깔려는 민수"),
    ("c19", [], "an office computer monitor showing a big glowing green shield symbol with a white check mark, a keyboard and mouse in front, clean desk, no people", "백신과 보안 설정은 켜 둔 채로"),
    ("c20", ["민수", "박 팀장"], "the young man handing a cardboard box of folders and a closed laptop across a desk to the woman manager with glasses, she receives it with a warm smile, moving boxes in the background, office", "자료와 노트북을 반납하는 민수"),
    ("c21", ["박 팀장"], "the woman manager with glasses sitting at her desk reviewing paper approval forms and pressing a red approval stamp on one, focused calm face, office", "승인 기록을 확인하는 관리자"),
    ("c22", ["박 팀장"], "the woman manager with glasses sitting at her desk looking carefully at a monitor showing rows of simple table lines and graphs, holding a pen, serious focused face, evening office", "이력을 점검하는 관리자"),
    ("c23", [], "an external backup hard drive connected by cable to a computer next to a server rack, a small green progress light, tidy IT room, no people", "장애에 대비한 자료 백업"),
    ("c24", [], "a wooden judge's gavel and a golden scale of justice on a desk next to a closed thick law book, soft serious lighting, no people", "위반하면 징계와 법적 책임"),
    ("c25", ["민수"], "close-up of the young man sitting at a desk signing a sheet of paper with a pen, determined small smile", "서약서에 서명하는 민수"),
    ("c26", ["민수", "박 팀장"], "the young man and the woman manager with glasses standing side by side in a bright office both smiling and giving a thumbs up, cheerful", "약속을 지키는 우리"),
    ("c27", [], "a bright modern open-plan office full of employees working happily at their desks, a large translucent glowing blue shield shape softly covering the whole office, warm light", "모두가 지키는 정보보안"),
]

STORY = """{c01}

회사의 기술과 정보, 누가 지키고 있을까요? 바로 오늘 출근한 여러분입니다. 지금부터 정보보안 서약서의 약속들을, 신입 사원 민수 씨와 함께 하나씩 알아보겠습니다.

{c02}

오늘은 민수 씨의 첫 출근 날입니다. 새 자리, 새 컴퓨터. 모든 것이 설레기만 합니다.

{c03}

"민수 씨, 입사를 축하해요. 일을 시작하기 전에 이 서약서부터 같이 읽어 볼까요?"

"서약서요? 그냥 사인만 하면 되는 거 아니에요?"

보안 담당 박 팀장은 웃으며 고개를 저었습니다. 서약서에는 우리가 매일 지켜야 할 여덟 가지 약속이 담겨 있습니다.

## 1. 비밀유지

{c04}

"이 도면, 친구한테 살짝 보여 줘도 되죠? 우리 회사 기술이 이렇게 대단하다고요."

{c05}

안 됩니다. 회사와 고객사의 기술 정보, 도면, 품질 자료, 단가, 그리고 임직원의 개인정보는 모두 지켜야 할 비밀입니다. 다니는 동안은 물론이고, 회사를 그만둔 뒤에도 밖으로 알리거나 업무 말고 다른 곳에 쓰면 안 됩니다.

## 2. 계정 관리

{c06}

모니터에 비밀번호를 적은 쪽지가 붙어 있네요.

"민수 씨, 비밀번호는 머릿속에만 두세요. 화면에 붙여 두면 누구나 볼 수 있어요."

내 아이디와 비밀번호는 다른 사람과 나누거나 빌려주지 않고, 정해진 때마다 바꿉니다.

{c07}

그리고 자리를 비울 때는 꼭 로그아웃하거나 화면을 잠급니다. 잠깐 커피를 뜨러 가는 순간에도요.

## 3. 권한 내 사용

{c08}

"민수 씨, 내 아이디로 잠깐 들어가서 그 자료 좀 봐 줄래요?"

"죄송해요, 선배님. 아이디는 빌려 드릴 수가 없어요."

{c09}

시스템은 나에게 주어진 권한 안에서, 업무를 위해서만 씁니다. 다른 사람의 계정을 쓰거나, 내 권한 밖의 정보를 들여다보거나 바꾸면 안 됩니다.

## 4. 출력·반출 금지

{c10}

"집에서 마저 보려고 화면을 찍어 두려는데요."

"잠깐만요. 회사 자료는 사진도, 개인 메일도, USB 도 안 돼요."

{c11}

시스템 화면과 출력물, 파일은 승인 없이 촬영하거나 복사하지 않습니다. 외부 메일, USB, 개인 클라우드, 메신저로 밖에 보내는 것도 금지입니다.

{c12}

프린터에 두고 온 종이 한 장도 정보 유출이 될 수 있습니다. 출력물은 바로 가져오고, 일이 끝나면 파쇄기로 파기합니다.

## 5. 사용 이력 기록

{c13}

회사는 보안을 위해 누가, 언제, 어디서 시스템에 접속하고 무엇을 조회하고 출력했는지 기록합니다.

{c14}

이 기록은 사고가 났을 때 원인을 찾고, 성실하게 일한 여러분을 지켜 주는 증거가 됩니다. 서약서에 서명하는 것은 이 기록과 점검에 동의한다는 뜻입니다.

## 6. 보안사고 신고

{c15}

"택배 배송 조회? 저 택배 시킨 적 없는데..."

{c16}

보낸 사람이 의심스러운 메일의 첨부파일과 링크는 열지 않습니다. 그래도 실수로 열었다면, 숨기지 말고 바로 알려야 합니다.

"팀장님, 이상한 메일을 열어 버린 것 같아요!"

{c17}

"잘했어요. 바로 알려 준 게 제일 중요해요. 랜선부터 뽑아 둘게요."

피싱 메일, 악성코드 감염, 계정 도용, 정보 유출이 의심되면 즉시 부서장과 보안 담당자에게 알립니다. 빨리 알릴수록 피해는 작아집니다.

## 7. PC 보안

{c18}

"이 게임 프로그램, 잠깐만 깔아도 되겠죠?"

{c19}

회사가 승인하지 않은 프로그램은 설치하지 않습니다. 백신과 보안 설정도 마음대로 끄거나 바꾸지 않습니다. 편하자고 연 작은 틈으로 악성코드가 들어올 수 있으니까요.

## 8. 퇴직·전보 시 반납

{c20}

시간이 흘러 민수 씨가 다른 부서로 옮기게 되었습니다.

"그동안 쓰던 자료와 노트북, 모두 반납합니다."

퇴직하거나 부서를 옮길 때는 가지고 있던 업무 자료를 반납하거나 삭제하고, 시스템 계정 회수에도 협조합니다.

## 관리자의 추가 약속

{c21}

시스템 관리자에게는 약속이 더 있습니다. 계정과 권한은 부서장의 요청과 승인 기록이 있을 때만 주거나 바꾸고, 업무에 꼭 필요한 만큼만 줍니다.

{c22}

퇴직하거나 부서를 옮긴 사람의 계정은 바로 회수하고, 접속과 출력 이력을 정기적으로 점검해 결과를 보고합니다. 관리자 권한으로 알게 된 정보도 관리 목적 말고는 열어 보지 않습니다.

{c23}

전산 장애가 생겨도 일이 멈추지 않도록, 대신 쓸 작업 방법과 자료 백업 상태를 늘 준비해 둡니다.

## 지키지 않으면

{c24}

이 약속을 어기면 회사 규정에 따른 징계를 받을 수 있습니다. 그리고 부정경쟁방지 및 영업비밀보호에 관한 법률, 개인정보 보호법 같은 법에 따라 민사와 형사 책임까지 질 수 있습니다.

## 매일 지키는 약속

{c25}

민수 씨는 서약서를 다시 한 번 천천히 읽고, 또박또박 서명했습니다.

"이제 알겠어요. 서약서는 사인하는 종이가 아니라, 매일 지키는 약속이네요."

{c26}

"맞아요. 그 약속이 우리 회사와 우리 모두를 지켜 줍니다."

{c27}

비밀은 지키고, 계정은 나만 쓰고, 자료는 밖으로 가져가지 않고, 이상하면 바로 알리기. 작은 습관 하나가 회사의 소중한 정보를 지킵니다. 오늘부터, 여러분이 우리 회사의 보안 담당자입니다."""


def main():
    cmd, folder = sys.argv[1], sys.argv[2]
    chars = {c["name"]: c for c in json.load(open(os.path.join(HERE, "등장인물.json"), encoding="utf-8"))["chars"]}
    src = open(os.path.join(HERE, "..", "..", "shorts_novel_maker_supertonic.py"), encoding="utf-8").read()
    style = re.search(r'"웹툰": "([^"]+)"', src).group(1).replace(", vertical scroll comic look", "")
    if cmd == "job":
        items = []
        for cid, who, desc, _ in CUTS:
            looks = "; ".join(f"person {k + 1} (the character from reference image {k + 1}): {chars[nm]['look']}" for k, nm in enumerate(who))   # 한글 이름은 그림에 글자로 나올 수 있어 번호로
            items.append({"id": cid, "width": 1024, "height": 576, "seed": 300 + int(cid[1:]),
                          "refs": [os.path.join(HERE, chars[nm]["face"]) for nm in who],
                          "prompt": f"{style}, Korean company information security training illustration. "
                                    + (f"Characters: {looks}. Each person appears only once, exactly two arms and two legs. " if looks else "")
                                    + ("" if who else "No people. ")
                                    + f"Scene: {desc}. Cinematic composition, full-bleed image, no border, no frame, no paper edges. No speech bubbles, no text, no letters, no logos."})
        os.makedirs(folder, exist_ok=True)
        json.dump({"items": items}, open(os.path.join(folder, "job.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(len(items), "cuts")
    elif cmd == "project":
        story = STORY
        for cid, _, _, cap in CUTS:
            story = story.replace("{" + cid + "}", f"[사진: {os.path.join(folder, cid + '.png')} | {cap} | AI 생성 그림 (FLUX.2 klein) | ]")
        narr = chars["나레이션"]["voice"]
        proj = {"ver": 7, "category": "장문", "genre": "[정보] 사내 교육", "topic": "정보보안 서약", "title": TITLE,
                "story": story, "sources": [], "notes": "사내 정보보안 서약서 교육 영상 (회사·고객사 이름 없이 '우리 회사')", "autophoto": False, "img_source": "그림: 웹툰",
                "cast": [{"name": nm, "look": c.get("look", ""), "look_ko": c.get("look_ko", ""), "voice": c.get("voice"),
                          **({"sheet": os.path.join(HERE, c["face"])} if c.get("face") else {})} for nm, c in chars.items() if nm != "나레이션"],
                "dialogue": [{"text": t, "who": w} for t, w in DIALOGUE],
                "settings": {"format": "롱폼 가로(1920×1080)", "narration": "on",   # 새 PC·서버 기본값(나레이션 꺼짐·스크롤형) 대신 장문 설정 그대로
                             "layout": "자막형(큰 제목+사진+자막)", "img_fill": "전체 화면(글자가 사진 위에)",
                             "img_motion": "영상처럼(확대·이동·전환)", "fps": "24", "reveal_hit": "off", "reveal_fx": "off",
                             "head_show": "안 보임(제목 카드만)", "sub_split": "한 줄씩(문장·쉼표로 나눠 차례로)", "img_label": "off",   # 규칙: 위 큰 제목·장면 설명 없이, 자막은 한 줄씩
                             "narr_voice": f"Supertonic {narr['code']} ({'남성' if narr['code'].startswith('M') else '여성'}, 무료 로컬) [supertonic:{narr['code']}]",
                             "narr_rate": str(narr.get("rate", 0)), "narr_tone_f": float(narr.get("semis", 0)),
                             "st_emotion": "차분"}}
        out = os.path.join(HERE, "정보보안_서약.json")
        json.dump(proj, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(out, len(story), "chars")


if __name__ == "__main__":
    main()
