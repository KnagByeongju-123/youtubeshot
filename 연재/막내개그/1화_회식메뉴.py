"""막내 개그 카툰 1화 '회식 메뉴' — 대본 + 컷 계획 (사람 = Open Peeps 표정, 배경·소품 = AI 같은 그림체)
python 연재/막내개그/1화_회식메뉴.py txt <파일>   → 사용자 확인용 대본
(컷 만들기·영상은 대본 확인 뒤에 붙임)
나레이션 1명(남자 성우 2)이 해설과 대사를 모두 읽음. 1~2분, 8컷, 마지막 컷 반전"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

TITLE = "막내 1화 - 회식 메뉴"

# 컷: (컷번호, 배경, [(인물, 표정, 자리)], 소품·효과, 화면 설명)
#   표정 = Open Peeps face (smileBig·cute·tired·hectic·suspicious·contempt·blank·concerned·smileLOL·rage …), 자리 = 왼·가운데·오른
PANELS = [
    ("p1", "사무실", [("부장님", "smileBig", "가운데"), ("팀장님", "smile", "왼"), ("이대리", "smile", "오른")], "박수 효과", "회식 발표"),
    ("p2", "사무실", [("막내", "awe", "가운데")], "반짝이 효과", "감동한 막내"),
    ("p3", "사무실", [("막내", "smileBig", "왼"), ("부장님", "cheeky", "오른")], "초밥 그림", "초밥?"),
    ("p4", "사무실", [("막내", "concerned", "왼"), ("팀장님", "blank", "오른")], "파스타 그림", "파스타?"),
    ("p5", "사무실", [("막내", "hectic", "왼"), ("이대리", "contempt", "오른")], "고기 그림", "고기?"),
    ("p6", "사무실", [("막내", "tired", "가운데")], "땀방울", "지쳐 가는 막내"),
    ("p7", "사무실", [("부장님", "smileLOL", "가운데"), ("팀장님", "smileBig", "왼"), ("이대리", "smileBig", "오른")], "박수 효과·순댓국 그림", "늘 가던 순댓국집"),
    ("p8", "순댓국집", [("막내", "blank", "왼"), ("박사원", "concerned", "오른")], "생각 풍선", "반전: 제가 언제…"),
]

STORY = """{p1}

금요일 오후, 부장님이 기분 좋게 외쳤습니다.

"오늘 회식은 막내가 먹고 싶은 걸로 하자!"

모두가 박수를 쳤습니다.

{p2}

입사 석 달 차 막내는 감동했습니다. 드디어 회사가 막내의 말을 들어 주는 날이 온 것입니다.

"정말요? 그럼… 초밥이요!"

{p3}

"초밥? 좋지. 근데 날것은 배탈 나."

부장님이 사람 좋게 웃었습니다.

{p4}

"그럼… 파스타요!"

"부장님 밀가루 안 드셔."

팀장님이 모니터에서 눈도 떼지 않고 말했습니다.

{p5}

"그, 그럼… 고기는요?"

"부장님 어제 고기 드셨어."

이 대리가 얄밉게 웃었습니다.

{p6}

막내의 머릿속 메뉴판이 하나씩 지워져 갔습니다. 막내는 조금씩 지쳐 가고 있었습니다.

{p7}

그때 부장님이 무릎을 탁 쳤습니다.

"그래, 막내 말대로 하자! 우리 늘 가던 그 순댓국집!"

모두가 다시 박수를 쳤습니다.

{p8}

그날 저녁, 순댓국집. 막내는 생각했습니다. 제가 언제 순댓국이라고 했죠?

동기 박 사원이 조용히 막내의 어깨를 두드렸습니다. 다음 회식 메뉴도, 아마 순댓국일 겁니다."""


def main():
    cmd, out = sys.argv[1], sys.argv[2]
    if cmd == "txt":
        story = STORY
        for cid, bg, who, prop, cap in PANELS:
            people = ", ".join(f"{n}({f})" for n, f, _ in who)
            story = story.replace("{" + cid + "}", f"[컷 {cid[1:]}: {cap} — 배경 {bg} / {people} / {prop}]")
        open(out, "w", encoding="utf-8").write(f"{TITLE}\n\n{story}\n")
        print(out, len(STORY), "chars")
    elif cmd == "project":                     # out = 컷 그림 폴더 (p1.png …)
        story = STORY
        for cid, bg, who, prop, cap in PANELS:
            story = story.replace("{" + cid + "}", f"[사진: {os.path.join(out, cid + '.png')} | {cap} | 그림: Open Peeps(CC0)·AI 생성 배경 | ]")
        proj = {"ver": 7, "category": "장문", "genre": "[이야기] 코믹 일상 장편 썰", "topic": "막내 개그 카툰", "title": TITLE,
                "story": story, "sources": [], "notes": "개그 카툰 1화", "autophoto": False, "img_source": "그림: 카툰",
                "settings": {"format": "롱폼 가로(1920×1080)", "narration": "on",
                             "narr_voice": "Supertonic M2 (남성, 무료 로컬) [supertonic:M2]",
                             "layout": "자막형(큰 제목+사진+자막)", "img_fill": "전체 화면(글자가 사진 위에)",
                             "img_motion": "없음", "img_depth": "off", "fps": "24", "reveal_hit": "off", "reveal_fx": "off",
                             "head_show": "안 보임(제목 카드만)", "sub_split": "한 줄씩(문장·쉼표로 나눠 차례로)", "img_label": "on"}}
        dst = os.path.join(HERE, "1화_회식메뉴.json")
        json.dump(proj, open(dst, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(dst)


if __name__ == "__main__":
    main()
