"""교육 영상 내용(내용.json) → 녹음용 프로젝트.json (나레이션_배경음만.py·나레이션_겹침검사.py·블록애니/시간표_만들기.py 가 읽는 형식)
   내용.json = {"제목", "회사", "장": [장 이름...], "장면": [{"장": 번호(-1 = 장 없음: 시작·마무리), "제목", "카드": [...], "문단": [{"말", "강조": [카드, 낱말], "확대": 카드, "동작"}]}]}
   - 문단의 '말' 하나가 대본 문단 하나 (순서 그대로), 장이 바뀌면 '## N. 장 이름' 줄
   - 설정: 성우 F7(사용자 결정 2026-11-25, 사내 교육) 정상 속도, 24fps, 가로 1920×1080, 자막 한 줄씩, 배경음은 합칠 때 교육/피아노연주곡.py 로 따로
   사용: python 교육/교육_프로젝트만들기.py <내용.json> [<결과 프로젝트.json>]"""
import json
import os
import sys

src = sys.argv[1]
d = json.load(open(src, encoding="utf-8"))
out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(src), "교육_프로젝트.json")
lines, cur = [], None
for sc in d["장면"]:
    ch = sc.get("장", -1)
    if ch >= 0 and ch != cur:
        lines.append(f"## {ch + 1}. {d['장'][ch]}")
        cur = ch
    for pa in sc["문단"]:
        lines.append(pa["말"])
settings = {
    "narration": "on", "narr_voice": "Supertonic F7 (여성, KSS·비상업용만) [supertonic:F7]", "narr_rate": 0.0,
    "format": "롱폼 가로(1920×1080)", "fps": 24, "layout": "자막형(큰 제목+사진+자막)",
    "img_fill": "전체 화면(글자가 사진 위에)", "img_motion": "영상처럼(확대·이동·전환)", "img_depth": "off",
    "head_show": "안 보임(제목 카드만)", "head_pos": "숨김", "sub_hide": "off", "sub_split": "한 줄씩(문장·쉼표로 나눠 차례로)",
    "img_label": "off", "img_credit": "off", "bgm_style": "은은한 멜로디", "bgm_peak": 0.35, "bgm_mul": 0.5,
}
pj = {"title": d["제목"] + " - " + d.get("회사", ""), "category": "교육", "story": "\n\n".join(lines), "settings": settings}
json.dump(pj, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("프로젝트:", out, "| 문단", sum(1 for l in lines if not l.startswith("## ")), "| 장", sum(1 for l in lines if l.startswith("## ")))
