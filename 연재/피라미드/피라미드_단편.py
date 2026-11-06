"""「피라미드는 어떻게 쌓았을까」 단편 (약 5분, 온 가족 입체 블록 애니)
python 연재/피라미드/피라미드_단편.py project   → 프로젝트 파일 연재/피라미드/피라미드_단편.json (대본.md 를 읽음)
  - 그림 자리 장면3D/cNN.png 옆의 cNN.json(입체 장면 설정, 장면3D_설정.py)을 영상 프로그램이 움직이는 입체 블록으로 그림
나레이션 한 명(남자 성우 1 · 정상 속도 · 톤 -1.5)이 대사까지 모두 읽음. 실제 사건에 상상을 더한 이야기"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
TITLE = "피라미드는 어떻게 쌓았을까"
SCN = os.path.join(HERE, "장면3D")


def read_script():
    t = open(os.path.join(HERE, "대본.md"), encoding="utf-8").read()
    story, table = t.split("## 컷 목록")
    story = story.split("## 대본", 1)[1].strip()
    cuts = {}
    for m in re.finditer(r"^\| (c\d+) \| ([^|]*) \| ([^|]*) \|", table, re.M):
        cuts[m.group(1)] = ([w.strip() for w in m.group(2).split(",") if w.strip() not in ("–", "")], m.group(3).strip())
    return story, cuts


def main():
    cmd = sys.argv[1]
    story, cuts = read_script()
    if cmd == "project":
        st = story
        for cid, (_, cap) in cuts.items():
            st = st.replace("{" + cid + "}", f"[사진: {os.path.join(SCN, cid + '.png')} | {cap} | 입체 블록 | ]")
        cast = json.load(open(os.path.join(HERE, "등장인물.json"), encoding="utf-8"))["chars"]
        proj = {"ver": 7, "category": "장문", "genre": "[이야기] 온 가족 미스터리", "topic": TITLE, "title": TITLE,
                "story": st, "sources": [], "notes": "실제 수수께끼(이집트 피라미드 쌓기)에 상상을 더한 온 가족 입체 블록 애니 (약 5분)",
                "autophoto": False, "img_source": "그림: 입체 블록",
                "cast": [{"name": c["name"], "look": "", "look_ko": "", "sheet": os.path.join(HERE, "캐릭터시트", c["name"] + ".png")} for c in cast],
                "settings": {"format": "롱폼 가로(1920×1080)", "narration": "on",
                             "layout": "자막형(큰 제목+사진+자막)", "img_fill": "전체 화면(글자가 사진 위에)",
                             "img_motion": "영상처럼(확대·이동·전환)", "fps": "24", "img_depth": "off",
                             "head_show": "안 보임(제목 카드만)", "head_pos": "숨김", "sub_split": "한 줄씩(문장·쉼표로 나눠 차례로)",
                             "img_label": "off", "img_credit": "off", "sub_hide": "off", "bgm_mode": "자동생성", "bgm_style": "잔잔한 패드",
                             "narr_voice": "Supertonic M1 (남성, 무료 로컬) [supertonic:M1]", "narr_rate": "0", "narr_tone_m": -1.5}}
        out = os.path.join(HERE, "피라미드_단편.json")
        json.dump(proj, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(out, len(story), "chars", len(cuts), "cuts")


if __name__ == "__main__":
    main()
