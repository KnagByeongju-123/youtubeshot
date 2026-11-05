"""「꺼진 등불 — 플래넌 섬의 마지막 밤」 단편 (약 10분, 미스터리 상상 애니 — 코드로 그린 움직이는 카툰)
python 연재/플래넌등대/플래넌등대_단편.py project   → 프로젝트 파일 연재/플래넌등대/플래넌등대_단편.json (대본.md 를 읽음)
python 연재/플래넌등대/플래넌등대_단편.py stills    → 장면/cNN.png (장면마다 멈춘 그림 1장 = 영상 프로그램이 시간을 재는 자리)
  - 그림 자리 장면/cNN.png 옆에 cNN.json(장면 설정)이 있으면 영상 프로그램이 그 장면을 움직이는 카툰으로 그림 (카툰장면.py)
나레이션 한 명(남자 성우 1 · 정상 속도 · 톤 -1.5)이 대사까지 모두 읽음. 실제 사건에 상상을 더한 이야기"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
TITLE = "꺼진 등불 — 플래넌 섬의 마지막 밤"
SCN = os.path.join(HERE, "장면")
# 5분 시험판에 남기는 장면 (나머지 문단은 뺌)
SHORT5 = ["c01", "c02", "c04", "c05", "c06", "c07", "c08", "c09", "c11", "c12", "c13", "c14", "c18", "c19", "c26", "c27",
          "c30", "c31", "c32", "c33", "c34", "c36", "c37", "c38", "c39", "c40", "c41", "c46", "c48", "c50", "c51"]


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
            st = st.replace("{" + cid + "}", f"[사진: {os.path.join(SCN, cid + '.png')} | {cap} | 코드로 그린 카툰 | ]")
        cast = json.load(open(os.path.join(HERE, "등장인물_카툰.json"), encoding="utf-8"))["chars"]
        proj = {"ver": 7, "category": "장문", "genre": "[이야기] 미스터리", "topic": TITLE, "title": TITLE,
                "story": st, "sources": [], "notes": "실제 미스터리 사건(1900 플래넌 섬 등대지기 실종)에 상상을 더한 카툰 애니 (약 10분)",
                "autophoto": False, "img_source": "그림: 코드 카툰",
                "cast": [{"name": c["name"], "look": "", "look_ko": "", "sheet": os.path.join(HERE, "캐릭터시트", c["name"] + ".png")} for c in cast],
                "settings": {"format": "롱폼 가로(1920×1080)", "narration": "on",
                             "layout": "자막형(큰 제목+사진+자막)", "img_fill": "전체 화면(글자가 사진 위에)",
                             "img_motion": "영상처럼(확대·이동·전환)", "fps": "24", "img_depth": "off",
                             "head_show": "안 보임(제목 카드만)", "head_pos": "숨김", "sub_split": "한 줄씩(문장·쉼표로 나눠 차례로)",
                             "img_label": "off", "img_credit": "off", "sub_hide": "off", "bgm_mode": "자동생성", "bgm_style": "잔잔한 패드",
                             "narr_voice": "Supertonic M1 (남성, 무료 로컬) [supertonic:M1]", "narr_rate": "0", "narr_tone_m": -1.5}}
        out = os.path.join(HERE, "플래넌등대_단편.json")
        json.dump(proj, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(out, len(story), "chars", len(cuts), "cuts")
    elif cmd == "project5":   # 5분 시험판 (사용자 결정 2026-11-05): 문단을 빼기만 함 → 이미 녹음한 문장을 그대로 씀
        full = json.load(open(os.path.join(HERE, "플래넌등대_단편.json"), encoding="utf-8"))
        blocks = re.split(r"(?=\[사진: [^\]]*?/(c\d+)\.png)", full["story"])
        keep, out_ = set(SHORT5), []
        for b in blocks:
            m = re.match(r"\[사진: [^\]]*?/(c\d+)\.png", b)
            if m and m.group(1) in keep:
                out_.append(b.strip())
        proj = dict(full, story="\n\n".join(out_), title=TITLE, notes=full["notes"] + " — 5분 시험판")
        out = os.path.join(HERE, "플래넌등대_5분.json")
        json.dump(proj, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        body = re.sub(r"\[사진:[^\]]*\]", "", proj["story"])
        print(out, len(out_), "cuts", len(re.sub(r"\n+", "\n", body).strip()), "chars")
    elif cmd == "stills":
        import importlib.util
        import cairosvg
        sp = importlib.util.spec_from_file_location("kscene", os.path.join(ROOT, "카툰장면.py"))
        K = importlib.util.module_from_spec(sp)
        sp.loader.exec_module(K)
        cast = {c["name"]: c for c in json.load(open(os.path.join(HERE, "등장인물_카툰.json"), encoding="utf-8"))["chars"]}
        os.makedirs(SCN, exist_ok=True)
        for cid in cuts:
            js = os.path.join(SCN, cid + ".json")
            if not os.path.exists(js):
                print("장면 설정 없음:", cid)
                continue
            scene = json.load(open(js, encoding="utf-8"))
            cairosvg.svg2png(bytestring=K.frame_svg(scene, cast, 0.5).encode(), write_to=os.path.join(SCN, cid + ".png"))
        print("멈춘 그림 완료")


if __name__ == "__main__":
    main()
