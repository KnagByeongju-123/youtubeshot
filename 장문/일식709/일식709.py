"""장문 과학 다큐 '2,700년 전 해가 사라진 날, 옛 기록 한 줄이 밝힌 지구와 태양의 비밀' — 대본 + 컷별 사진·그림 계획
python 장문/일식709/일식709.py job <저장폴더> [c01,...]  → 그림 주문서(다큐 수채화) job.json (사진 컷은 빼고)
python 장문/일식709/일식709.py project <그림폴더>       → 프로젝트 파일 장문/일식709/일식709.json
사용자 요청(2026-10-27): 고대사 최신 연구 과학 미스터리 — 2번 기원전 709년 개기일식
사실 확인: Hayakawa, Owens, Jin, Sôma, Lockwood, "Analyses of the Ancient Chinese Report on the Total Solar Eclipse in 709 BCE:
 Implications for the Contemporaneous Earth's Rotation Speed and Solar Cycles", The Astrophysical Journal Letters 995(1) (2025-12), doi 10.3847/2041-8213/ae0461
 (나고야대 보도자료 2025-12-03)
 - 기원전 709년 7월 17일, 노나라 궁정에서 본 개기일식 / 《춘추》(사건 뒤 2~3세기에 엮음): "가을 칠월 임진 초하루, 해가 다 가려졌다(日有食之 旣)"
 - 《한서》(약 700년 뒤): 가려진 해가 "위아래가 모두 노랬다" → 코로나를 적은 가장 오래된 글 가운데 하나일 수 있음(믿을 수 있는지는 조심)
 - 지금 계산으로는 곡부(노나라 도읍)에서 개기일식이 안 보임 → 예전 연구가 쓴 좌표가 옛 곡부에서 약 8km 떨어져 있었음 → 발굴 보고서로 좌표 바로잡음(북위 35°36′, 동경 116°59′)
 - ΔT(지구 자전이 늦어져 생긴 시간 차) = 20,264~21,204초 (약 5시간 38분~5시간 53분)
 - 태양: '호메로스 극소기'(신아시리아 극소기, 기원전 808~717년) 직후, 709년에는 활동이 되살아나 11년 주기의 꼭대기 근처 → 나이테 방사성탄소 복원과 맞음
 - 방법: 역사 지리로 곡부 위치 바로잡기, 일식 경로 계산, 자전 속도 복원, 태양 자전축 방향 계산, 코로나 모양 모의실험
 - 한계: 코로나 묘사는 700년 뒤 책에만 있어 믿을 수 있는지 불확실, 일식 날짜는 확실
 - 일반 사실: 《춘추》 = 노나라 연대기(기원전 722~481년), 공자가 엮었다고 전함, 일식 기록이 서른 번 넘게 실림 / 달이 일으키는 밀물·썰물의 마찰이 지구 자전을 늦춤"""
import json
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
TITLE = "2,700년 전 해가 사라진 날, 옛 기록 한 줄이 밝힌 지구와 태양의 비밀"
STYLE_NAME = "다큐 수채화"
DIALOGUE = []

NP = " No people, no hands, no arms anywhere."
CUTS = [
    ("c01", "real photo", "개기일식"),
    ("c02", "an ancient Chinese court of the Zhou era in summer, officials in long robes and black caps looking up in alarm at a darkened sky where the sun is completely covered by the moon with a glowing ring, a wooden palace with curved roofs, eerie twilight", "기원전 709년 노나라 궁정의 개기일식 (상상 복원)"),
    ("c03", "real photo", "공자"),
    ("c04", "real photo", "《춘추》 옛 책"),
    ("c05", "real photo", "곡부의 공자 사당"),
    ("c06", "real photo", "일식이 일어나는 원리"),
    ("c07", "real photo", "개기일식의 코로나"),
    ("c08", "diagram", "옛 기록이 맞지 않았다"),
    ("c09", "real photo", "곡부의 옛 성벽"),
    ("c10", "diagram", "곡부 좌표 바로잡기"),
    ("c11", "real photo", "밀물과 썰물"),
    ("c12", "real photo", "달"),
    ("c13", "diagram", "지구 자전이 늦어진 만큼, ΔT"),
    ("c14", "real photo", "옛 해시계"),
    ("c15", "real photo", "《한서》 옛 책"),
    ("c16", "real photo", "태양 흑점"),
    ("c17", "diagram", "태양의 11년 주기와 호메로스 극소기"),
    ("c18", "real photo", "나무의 나이테"),
    ("c19", "real photo", "극지방의 빙하 얼음 기둥"),
    ("c20", "real photo", "태양 활동이 활발할 때의 코로나"),
    ("c21", "real photo", "태양 활동이 잠잠할 때의 코로나"),
    ("c22", "real photo", "오늘날의 일식 관측"),
    ("c23", "real photo", "옛 중국의 천문 관측 기구"),
    ("c24", "real photo", "지구"),
    ("c25", "real photo", "부분일식"),
    ("c26", "a wide watercolor view of an ancient Chinese walled city with curved roofs at dusk under a sky where the sun is just reappearing from behind the moon, a thin bright crescent, peaceful and grand." + NP, "다시 빛나는 해 (상상 복원)"),
]

STORY = """{c01}

한낮에 갑자기 해가 사라집니다. 하늘은 밤처럼 어두워지고, 새들은 둥지로 돌아갑니다. 개기일식입니다. 지금은 몇 년 전부터 날짜와 장소를 정확히 알 수 있지만, 옛사람들에게는 하늘이 보내는 무서운 경고였습니다.

{c02}

지금으로부터 약 2,700년 전, 기원전 709년 7월 17일. 중국 노나라의 궁정 사람들이 해가 완전히 사라지는 것을 보았습니다. 그리고 그 일을 단 한 줄로 기록했습니다. 그런데 2025년 12월, 일본 나고야 대학의 하야카와 히사시 연구팀과 영국 레딩 대학, 미국의 과학자들이 천체물리학 학술지에 실은 논문에서, 이 한 줄로부터 놀라운 사실을 찾아냈습니다. 2,700년 전 지구는 지금보다 조금 더 빨리 돌았고, 태양은 긴 잠에서 깨어나고 있었다는 것입니다. 오늘은 옛 기록 한 줄이 어떻게 지구와 태양의 비밀을 풀었는지 따라가 보겠습니다. 끝까지 보시면 증거를 모아 인공지능이 내린 결론도 들으실 수 있습니다.

## 1. 공자의 나라에 남은 한 줄

{c03}

노나라는 공자가 태어난 나라입니다. 노나라에는 해마다 나라의 큰일을 적은 연대기가 있었고, 이 기록을 엮은 책이 바로 춘추입니다. 춘추는 공자가 엮었다고 전해집니다.

{c04}

춘추에는 기원전 722년부터 481년까지 240여 년의 일이 담겨 있습니다. 전쟁과 왕의 죽음 같은 사건과 함께, 일식 기록이 서른 번 넘게 실려 있습니다. 춘추 시대라는 시대의 이름도 바로 이 책에서 나왔습니다. 하늘의 변화를 그만큼 중요하게 여겼다는 뜻입니다.

{c05}

그 가운데 기원전 709년의 기록은 이렇습니다. 가을 칠월 임진일 초하루, 해가 다 가려졌다. 한자로는 해를 무언가가 먹었는데, 그것이 다했다는 뜻으로 적혀 있습니다. 다 가려졌다는 말은 해가 완전히 사라진 개기일식이라는 뜻입니다. 세계에서 가장 오래된 개기일식 기록 가운데 하나입니다.

## 2. 해가 사라지는 원리

{c06}

일식은 달이 해를 가리는 현상입니다. 해는 달보다 약 400배 크지만, 약 400배 멀리 있습니다. 그래서 하늘에서 보면 해와 달의 크기가 거의 같고, 달이 해를 꼭 맞게 가릴 수 있습니다.

{c07}

해가 완전히 가려지는 순간, 해 둘레로 희미한 빛의 왕관이 드러납니다. 태양의 바깥 대기, 코로나입니다. 평소에는 해가 너무 밝아 보이지 않다가, 개기일식 때만 맨눈으로 볼 수 있습니다. 놀랍게도 코로나의 온도는 100만 도가 넘습니다.

{c08}

그런데 개기일식은 아주 좁은 띠 안에서만 보입니다. 그 띠에서 조금만 벗어나도 해는 일부만 가려집니다. 그래서 옛 기록이 정확하다면, 기록을 남긴 곳은 반드시 그 좁은 띠 안에 있어야 합니다. 바로 여기서 문제가 생겼습니다.

## 3. 맞지 않는 계산

{c09}

노나라의 도읍 곡부는 지금의 중국 산둥성 취푸시입니다. 그런데 지금의 계산으로 해 보면, 곡부에서는 이 일식이 완전히 가려지는 개기일식으로 보이지 않았습니다. 기록이 틀린 걸까요, 아니면 계산이 틀린 걸까요?

{c10}

연구팀은 기록 대신 위치를 의심했습니다. 옛 곡부 성터를 발굴한 고고학 보고서를 찾아보니, 그동안 연구에 쓰인 곡부의 좌표가 진짜 옛 도읍에서 약 8킬로미터나 떨어져 있었습니다. 연구팀은 발굴 자료로 옛 궁정의 위치를 바로잡았습니다. 새로 정한 위치는 북위 35도 36분, 동경 116도 59분입니다. 8킬로미터는 작아 보이지만, 개기일식의 띠가 좁기 때문에 이 차이가 결과를 바꿉니다.

## 4. 지구는 더 빨리 돌았다

{c11}

이제 두 번째 수수께끼가 남습니다. 지구가 도는 속도는 조금씩 느려지고 있습니다. 달이 일으키는 밀물과 썰물이 바닷물과 바다 밑을 문지르며, 마치 브레이크처럼 지구의 자전을 아주 조금씩 늦추기 때문입니다.

{c12}

하루가 길어지는 정도는 아주 작습니다. 100년에 겨우 1천분의 2초 정도입니다. 하지만 수천 년이 쌓이면 이야기가 달라집니다. 만약 지구가 늘 지금과 같은 속도로 돌았다고 가정하고 옛 일식을 계산하면, 일식이 보이는 장소가 수천 킬로미터나 어긋납니다.

{c13}

과학자들은 이 어긋난 시간을 델타 티라고 부릅니다. 연구팀은 바로잡은 곡부의 위치로 계산해, 기원전 709년의 델타 티가 2만 264초에서 2만 1,204초 사이라는 것을 밝혔습니다. 약 5시간 40분에서 5시간 50분 정도입니다. 2,700년 동안 지구의 시계가 그만큼 늦어졌다는 뜻입니다.

{c14}

다시 말해 2,700년 전의 지구는 지금보다 조금 더 빨리 돌았고, 하루도 아주 조금 더 짧았습니다. 옛 기록 한 줄이 지구가 도는 속도를 재는 자가 된 것입니다.

## 5. 위아래가 모두 노랬다

{c15}

이야기는 여기서 끝나지 않습니다. 이 일식에서 약 700년 뒤에 쓰인 역사책, 한서에는 이 일식에 대한 설명이 하나 더 붙어 있습니다. 가려진 해가 위아래가 모두 노랬다는 것입니다.

{c16}

연구팀은 이 표현이 코로나를 묘사한 것일 수 있다고 봅니다. 그렇다면 인류가 코로나를 글로 남긴 가장 오래된 기록 가운데 하나가 됩니다. 그리고 코로나의 모양은 태양이 얼마나 활발한지에 따라 달라집니다.

{c17}

태양은 약 11년마다 활발해졌다가 잠잠해지기를 되풀이합니다. 그런데 가끔은 수십 년 동안 거의 잠든 듯 잠잠한 시기가 찾아옵니다. 기원전 808년부터 717년까지가 그런 시기였습니다. 호메로스 극소기라고 부릅니다. 고대 그리스의 시인 호메로스가 살았다고 여겨지는 무렵이라 붙은 이름입니다.

{c18}

이런 사실은 나무의 나이테로 알아냅니다. 태양이 잠잠하면 우주에서 날아오는 입자가 더 많이 들어와, 나무에 쌓이는 방사성 탄소가 늘어납니다. 나이테 한 줄 한 줄이 그해 태양의 기록이 되는 것입니다.

{c19}

극지방의 얼음 기둥에도 비슷한 기록이 남아 있습니다. 그린란드와 남극의 얼음 속에는 우주에서 온 입자가 만든 베릴륨이라는 원소가 해마다 쌓입니다. 과학자들은 이런 자료를 모아 수천 년 동안의 태양 활동을 되살려 왔습니다.

{c20}

태양이 활발할 때 코로나는 해 둘레로 고르게 퍼져, 위아래로도 밝게 빛납니다. 반대로 태양이 잠잠할 때는 코로나가 해의 적도 쪽으로만 길게 뻗습니다.

{c21}

연구팀이 컴퓨터로 기원전 709년의 코로나를 되살려 보니, 위아래가 모두 노랬다는 기록은 태양이 다시 활발해져 11년 주기의 꼭대기 근처에 있을 때와 잘 맞았습니다. 긴 잠잠한 시기가 막 끝나고, 태양이 깨어나고 있었다는 것입니다. 나이테로 되살린 태양의 기록과도 딱 들어맞았습니다.

{c22}

연구에 참여한 레딩 대학의 매슈 오언스는, 이런 옛 기록이 나이테와 얼음 기둥으로 되살린 태양 활동을 따로 확인해 주는 귀중한 기준점이 된다고 말합니다. 2,700년 전의 하늘이 오늘의 과학을 검증해 준 셈입니다.

## 6. 인공지능의 결론

{c23}

그렇다면 인공지능인 제가 증거들을 모아 내린 결론은 이렇습니다. 첫째, 옛 기록은 틀리지 않았습니다. 틀린 것은 우리가 알고 있던 곡부의 위치였습니다. 위치를 바로잡자 2,700년 전 한 줄의 기록이 지금의 계산과 정확히 맞아떨어졌습니다.

{c24}

둘째, 이 한 줄 덕분에 우리는 2,700년 전 지구가 지금보다 조금 더 빨리 돌았다는 것을 더 정확히 알게 됐습니다. 다만 위아래가 모두 노랬다는 코로나 이야기는 700년 뒤에 쓰인 책에만 있어서, 연구팀도 조심스럽게 해석합니다. 반면 일식이 일어난 날짜 자체는 과학자들이 확실하다고 봅니다.

{c25}

셋째, 가장 놀라운 것은 이것입니다. 2,700년 전 누군가 하늘을 올려다보며 남긴 짧은 문장이, 오늘날의 과학자들에게 지구와 태양의 시계를 맞추는 열쇠가 됐습니다.

{c26}

오늘 우리가 남기는 기록도 언젠가 먼 미래의 누군가에게 중요한 단서가 될지 모릅니다. 여러분은 2,700년 전 해가 사라진 날, 노나라 사람들이 무엇을 느꼈을 거라고 생각하시나요? 댓글로 들려주세요."""


REFS = {}
SEED = {}
REF_NOTE = ("Any real place or object shown must look exactly like the reference photo (same shape and colors), "
            "painted in the same watercolor style. ")

# 컷 → 사진 후보 이름 (사진후보/후보.json 의 열쇠). 사진을 받은 뒤 채움
PHOTOS = {}


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
        proj = {"ver": 7, "category": "장문", "genre": "[다큐] 과학", "topic": "기원전 709년 개기일식", "title": TITLE,
                "story": story, "sources": ["https://doi.org/10.3847/2041-8213/ae0461", "https://en.nagoya-u.ac.jp/?p=7070"],
                "notes": "고고학 장문 다큐(최신 논문) (실제 사진·논문 그림 위주 + 사진이 없는 장면은 AI 그림)", "autophoto": False, "img_source": "그림: 수채화",
                "settings": {"format": "롱폼 가로(1920×1080)", "narration": "on",
                             "layout": "자막형(큰 제목+사진+자막)", "img_fill": "전체 화면(글자가 사진 위에)",
                             "img_motion": "천천히 확대만", "scene_trans": "전진(확대하며 다음 장면)",   # 계속 앞으로 나아가는 느낌(사용자 요청 2026-10-26)
                             "head_show": "안 보임(제목 카드만)", "sub_split": "한 줄씩(문장·쉼표로 나눠 차례로)", "img_label": "on",
                             "narr_voice": "Supertonic M2 (남성, 무료 로컬) [supertonic:M2]", "narr_rate": -8, "narr_tone_m": -1}}   # 장문 다큐 성우(사용자 결정 2026-10-26 오후: 샘플 2번 — 전에는 3번)
        out = os.path.join(HERE, "일식709.json")
        json.dump(proj, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(out, len(story), "chars")


if __name__ == "__main__":
    main()
