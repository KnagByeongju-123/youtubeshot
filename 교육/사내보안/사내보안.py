"""사내 보안교육 영상 '태진다이텍 정보보안 서약, 꼭 지켜야 할 8가지' — 대본 + 컷별 도표·그림 계획
python 교육/사내보안/사내보안.py job <저장폴더> [c01,...]  → 그림 주문서 job.json (도표 컷은 빼고)
python 교육/사내보안/사내보안.py project <그림폴더>       → 프로젝트 파일 교육/사내보안/사내보안.json
사용자 요청(2026-10-27): (주)태진다이텍 '통합업무시스템(태진포탈) 및 회사 PC·네트워크' 정보보안 서약서 내용으로 사내 보안교육 영상
 - 서약서 순서 그대로: 서약 8가지 → 관리자 추가 서약 4가지 → 위반 시 책임(부정경쟁방지 및 영업비밀보호에 관한 법률, 개인정보 보호법) → 개인정보 수집·이용 동의
 - 사용자 결정: smtec_main2(ESG Smart Factory) 화면·기능과는 별개로 — 실제 시스템 화면 대신 관련 그림을 새로 그림
 - 나레이션: 성우 샘플 2번 (Supertonic M1, 속도 -3%, 톤 0)"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
TITLE = "태진다이텍 정보보안 서약, 꼭 지켜야 할 8가지"
STYLE = ("clean modern Korean webtoon illustration, clean outlines, soft cel shading, bright calm colors, "
         "friendly corporate training look")
WORKER = "a Korean factory office worker in a light gray work jacket"

NP = " No people, no hands, no arms anywhere."
# (컷, 그림 설명 | "diagram", 화면 설명) — 서약서 순서 그대로
CUTS = [
    ("c01", f"morning at a clean Korean precision press factory, rows of metal stamping presses, {WORKER} holding a tablet and walking along the line, soft sunlight", "아침의 생산 현장"),
    ("c02", "a bright modern factory office with several desktop computers connected by glowing network lines to a small server cabinet, an integrated business system feeling." + NP, "통합업무시스템과 회사 PC·네트워크"),
    ("c03", f"{WORKER} sitting at an office desk signing a one-page paper form with a pen, calm and serious, blurred office background", "정보보안 서약서에 서명"),
    ("c04", "an office desk with rolled engineering drawings, a quality inspection sheet, a caliper and shiny metal bearing seal parts, a laptop beside them, blank paper without readable text." + NP, "기술정보·도면·품질 자료·단가"),
    ("c05", f"{WORKER} leaving the office building on the last day carrying only a small potted plant, sunset, calm mood", "퇴직한 뒤에도 비밀은 지킴"),
    ("c06", f"{WORKER} typing on a keyboard at a computer, the monitor shows a simple login window with two empty input boxes and a padlock icon, office", "아이디와 비밀번호"),
    ("c07", f"two Korean office workers at a desk, one colleague asking something with a sheepish smile, {WORKER} politely refusing with an open palm gesture", "계정은 빌려주지 않음"),
    ("c08", "a computer monitor on a desk showing a big padlock icon with circular refresh arrows around it, a calendar on the wall beside it, clean office." + NP, "비밀번호는 정기적으로 변경"),
    ("c09", "an empty office chair pushed in at a desk, the computer monitor shows a dark lock screen with a single padlock icon, a coffee mug, the worker has stepped away." + NP, "자리를 비울 땐 로그아웃·화면 잠금"),
    ("c10", "a computer screen showing a grid of folder icons, some folders open and glowing green, others closed with padlock icons, office desk." + NP, "받은 권한 범위 안에서만"),
    ("c11", f"{WORKER} hesitating at a computer while holding a colleague's employee ID card with a different photo, then putting it down, uneasy expression", "다른 사람의 계정은 쓰지 않음"),
    ("c12", f"{WORKER} about to take a photo of a computer monitor with a smartphone, a large semi-transparent red warning circle-slash sign floating in front of the phone", "승인 없이 촬영·복사 금지"),
    ("c13", "a laptop on a desk with a USB flash drive, a smartphone showing a chat messenger bubble, an email envelope icon and a cloud upload icon floating above, each crossed by a red warning sign, cautionary mood." + NP, "외부 메일·USB·개인 클라우드·메신저 반출 금지"),
    ("c14", f"{WORKER} collecting printed papers from an office printer tray and feeding them into a paper shredder beside it", "출력물은 회수해서 파기"),
    ("c15", "diagram", "회사가 남기는 접속·조회·출력 기록"),
    ("c16", "a computer monitor showing an email with a glowing suspicious attachment icon and a fishing hook symbol hanging over it, dark ominous office at night." + NP, "출처가 의심스러운 메일의 첨부파일·링크"),
    ("c17", f"{WORKER} urgently explaining something to a middle-aged team leader, both looking at a laptop screen together, serious but calm", "의심되면 즉시 부서장에게"),
    ("c18", "diagram", "보안사고 신고 순서"),
    ("c19", "a computer screen showing a software install window with a big shield icon and a warning symbol, an antivirus shield glowing in the corner of the screen, office desk." + NP, "승인 안 된 프로그램 설치·백신 해제 금지"),
    ("c20", f"{WORKER} handing over a stack of document folders and a laptop to a team leader at a tidy desk, cardboard box nearby, polite handover", "퇴직·전보 때 자료 반납과 계정 회수"),
    ("c21", "diagram", "관리자 추가 서약 4가지"),
    ("c22", "a Korean IT administrator in a light gray work jacket checking a small server rack and external backup drives in a clean server room, blinking green lights", "대체 작업 방법과 자료 백업"),
    ("c23", "diagram", "위반하면"),
    ("c26", "a signed paper form being placed into a locked gray filing cabinet drawer in a tidy office, a small padlock on the drawer, calm and secure mood." + NP, "개인정보 수집·이용 동의"),
    ("c24", "evening at the Korean precision press factory, workers in light gray jackets walking out together, warm lights, peaceful and proud mood", "작은 습관이 회사를 지킵니다"),
    ("c25", "diagram", "꼭 지켜야 할 8가지"),
]

STORY = """{c01}

우리 회사의 도면, 품질 자료, 단가, 그리고 고객사 정보. 이 모든 것은 매일 우리가 쓰는 시스템과 컴퓨터 안에 담겨 있습니다. 한 번 밖으로 새어 나간 정보는 다시 주워 담을 수 없습니다.

{c02}

오늘은 통합업무시스템인 태진포탈과 회사 피시, 네트워크를 쓰는 모든 임직원이 지켜야 할 정보보안 서약을 순서대로 알아보겠습니다. 어렵지 않습니다. 매일의 작은 습관입니다.

{c03}

보안 서약서는 태진다이텍의 임직원으로서 회사 정보자산을 안전하게 쓰겠다는 약속입니다. 사용자는 여덟 가지를, 관리자는 여기에 네 가지를 더 지킵니다.

## 1. 비밀유지

{c04}

첫째, 비밀유지입니다. 회사와 고객사의 기술정보, 도면, 품질 자료, 단가, 그리고 임직원의 개인정보는 업무에만 씁니다. 현대자동차와 기아, 에스케이에프 같은 고객사의 자료는 특히 조심해야 합니다.

{c05}

이 약속은 회사에 다니는 동안은 물론, 퇴직한 뒤에도 이어집니다. 회사에서 알게 된 정보를 밖에 알리거나 업무 밖의 목적으로 써서는 안 됩니다.

## 2. 계정 관리

{c06}

둘째, 계정 관리입니다. 회사에서 받은 아이디와 비밀번호는 나만 쓰는 열쇠입니다.

{c07}

동료가 잠깐만 빌려 달라고 해도 알려 주지 않습니다. 남이 내 계정으로 들어가면, 그 기록은 모두 내 이름으로 남습니다.

{c08}

생일이나 같은 숫자처럼 쉬운 비밀번호는 피하고, 정기적으로 바꿔 주세요.

{c09}

자리를 비울 때는 로그아웃하거나 화면을 잠급니다. 잠깐 커피를 가지러 가는 사이에도 열린 화면은 누구나 볼 수 있습니다.

## 3. 권한 내 사용

{c10}

셋째, 받은 권한 범위 안에서, 업무 목적으로만 시스템을 씁니다. 사람마다 맡은 일이 다르기 때문에 볼 수 있는 정보도 다릅니다.

{c11}

다른 사람의 계정을 쓰거나, 내 권한 밖의 정보를 들여다보거나 바꾸려고 해서는 안 됩니다.

## 4. 출력과 반출 금지

{c12}

넷째, 시스템 화면과 출력물, 파일을 승인 없이 휴대폰으로 찍거나 복사하지 않습니다. 사진 한 장으로도 도면과 단가가 통째로 밖에 나갈 수 있습니다.

{c13}

외부 메일, 유에스비, 개인 클라우드, 메신저로 회사 자료를 내보내는 것도 안 됩니다. 꼭 필요하면 먼저 승인을 받습니다.

{c14}

업무가 끝난 출력물은 프린터에 두고 가지 말고 바로 회수해서 파기합니다. 출력물이 쌓인 프린터는 생각보다 쉬운 정보 유출 통로입니다.

## 5. 사용 이력 기록

{c15}

다섯째, 회사는 보안 관리를 위해 시스템에 누가, 언제, 어디에서 들어와 무엇을 조회하고 출력했는지 기록하고 점검합니다. 우리는 서약으로 이것에 동의합니다. 기록은 감시가 아니라, 문제가 생겼을 때 나를 지켜 주는 증거입니다.

## 6. 보안사고 신고

{c16}

여섯째, 보낸 사람이 의심스러운 메일의 첨부파일이나 링크는 열지 않습니다. 택배, 세금, 급여처럼 급하게 누르게 만드는 메일이 가장 위험합니다.

{c17}

피싱 메일을 받았거나, 악성코드에 감염된 것 같거나, 계정이 도용되거나 정보가 새어 나간 것 같으면 혼자 해결하려 하지 말고 바로 부서장과 보안담당자에게 알립니다.

{c18}

빨리 알릴수록 피해는 작아집니다. 실수로 열었더라도 숨기지 말고 바로 알리는 것이 가장 좋은 대처입니다.

## 7. 피시 보안

{c19}

일곱째, 회사가 승인하지 않은 프로그램은 설치하지 않습니다. 백신이 느리다고 끄거나, 보안 설정을 마음대로 바꾸지 않습니다. 무료 프로그램 하나가 회사 전체 네트워크를 위험하게 만들 수 있습니다.

## 8. 퇴직과 전보 시 반납

{c20}

여덟째, 퇴직하거나 부서를 옮길 때는 가지고 있던 업무 자료를 반납하거나 삭제하고, 시스템 계정을 회수하는 데 협조합니다. 쓰지 않는 계정은 누군가에게 열린 문이 될 수 있습니다.

## 관리자 추가 서약

{c21}

권한 구분이 관리자라면 네 가지를 더 지킵니다. 첫째, 계정과 권한은 부서장의 요청과 승인 기록이 있을 때만 주고 바꾸며, 업무에 꼭 필요한 만큼만 줍니다. 둘째, 퇴직하거나 부서를 옮긴 사람의 계정은 바로 회수하고, 접속과 출력 기록을 정기적으로 점검해 그 결과를 보고합니다. 셋째, 관리자 권한으로 알게 된 정보는 관리 목적 밖에서 보거나 쓰지 않습니다.

{c22}

넷째, 전산 장애가 생겨도 일이 멈추지 않도록, 대신 일할 방법과 자료 백업 상태를 늘 유지합니다.

## 위반 시 책임

{c23}

이 서약을 어기면 회사 규정에 따른 징계와 함께, 부정경쟁방지 및 영업비밀보호에 관한 법률과 개인정보 보호법 같은 관계 법령에 따라 민사와 형사 책임까지 질 수 있습니다.

{c26}

끝으로, 서약서에 적는 성명과 사번, 소속, 직위, 서명은 서약 이력을 관리하는 데에만 쓰이고, 퇴직한 뒤 정해진 기간 동안 보관됩니다. 서약할 때 이 개인정보 수집과 이용에 동의하는지도 함께 표시합니다.

## 꼭 기억하세요

{c24}

보안은 어려운 기술이 아닙니다. 비밀번호를 지키고, 자리를 비울 때 잠그고, 수상하면 알리는 것. 작은 습관 하나가 우리 회사의 기술과 동료를 지킵니다.

{c25}

오늘 배운 여덟 가지를 다시 한번 떠올려 보세요. 비밀유지, 계정 관리, 권한 내 사용, 출력과 반출 금지, 사용 이력 기록, 보안사고 신고, 피시 보안, 그리고 퇴직과 전보 시 반납. 함께 지켜 주셔서 감사합니다."""

SEED = {}


def main():
    cmd, folder = sys.argv[1], sys.argv[2]
    only = sys.argv[3].split(",") if len(sys.argv) > 3 else None
    if cmd == "job":
        items = []
        for cid, desc, _ in CUTS:
            if (only and cid not in only) or desc == "diagram":
                continue
            hands = "" if "no people" in desc.lower() else ("Every person has exactly two arms, two hands with five fingers each and two legs, "
                                                             "hands simple and relaxed (partly hidden is fine). ")
            items.append({"id": cid, "width": 1024, "height": 576, "seed": SEED.get(cid, 500 + int(cid[1:])), "refs": [],
                          "prompt": f"{STYLE}. Scene: {desc}. {hands}No company logos, no brand names. "
                                    "Cinematic composition, full-bleed image, no border, no frame, no paper edges, no panels. "
                                    "No text, no letters, no captions, no numbers on screens."})
        os.makedirs(folder, exist_ok=True)
        json.dump({"items": items, "skip_done": True}, open(os.path.join(folder, "job.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(len(items), "cuts")
    elif cmd == "project":
        story = STORY
        for cid, desc, cap in CUTS:
            if desc == "diagram":
                img = os.path.join(HERE, "도표", cid + ".png")
            else:
                img = next((os.path.join(folder, cid + e) for e in (".jpg", ".png") if os.path.exists(os.path.join(folder, cid + e))),
                           os.path.join(folder, cid + ".png"))
            story = story.replace("{" + cid + "}", f"[사진: {img} | {cap} | | ]")
        proj = {"ver": 7, "category": "장문", "genre": "[교육] 사내 보안", "topic": "사내 정보보안 서약", "title": TITLE,
                "story": story, "sources": [], "notes": "사내 보안교육 (도표 + 웹툰풍 그림, 성우 샘플 2번 M1 -3%)",
                "autophoto": False, "img_source": "그림: 웹툰",
                "settings": {"format": "롱폼 가로(1920×1080)", "narration": "on",
                             "layout": "자막형(큰 제목+사진+자막)", "img_fill": "전체 화면(글자가 사진 위에)",
                             "img_motion": "천천히 확대만", "scene_trans": "전진(확대하며 다음 장면)",
                             "head_show": "안 보임(제목 카드만)", "sub_split": "한 줄씩(문장·쉼표로 나눠 차례로)", "img_label": "off",
                             "narr_voice": "Supertonic M1 (남성, 무료 로컬) [supertonic:M1]", "narr_rate": -3, "narr_tone_m": 0}}
        out = os.path.join(HERE, "사내보안.json")
        json.dump(proj, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(out, len(story), "chars")


if __name__ == "__main__":
    main()
