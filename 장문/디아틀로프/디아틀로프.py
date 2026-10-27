"""장문 다큐 '아홉 명은 왜 텐트를 찢고 나갔나, 과학이 다시 본 디아틀로프 고개의 마지막 밤' — 대본 + 컷별 사진·그림 계획
python 장문/디아틀로프/디아틀로프.py job <저장폴더> [c01,...]  → 그림 주문서(다큐 수채화) job.json (사진 컷은 빼고)
python 장문/디아틀로프/디아틀로프.py project <그림폴더>       → 프로젝트 파일 장문/디아틀로프/디아틀로프.json
사용자 요청(2026-10-27): 역사·최신 미스터리, 최신 논문 우선 → 디아틀로프 고개 사건
사실 확인 (실제 희생자가 있는 사건 — 자극적인 표현·추측성 음모론 강조 없이):
 - 1959년 2월 1~2일 밤, 북부 우랄 홀라트샤흘산 비탈, 우랄 공과대학 학생·졸업생 등 9명 사망, 대장 이고리 디아틀로프(23세), 목표 오토르텐산(약 10km 북쪽)
 - 유리 유딘은 1월 28일 몸이 아파 돌아가 혼자 살아남음(2013년 75세로 세상을 떠남)
 - 텐트는 안쪽에서 찢겨 있었고, 대부분 신발도 제대로 신지 않은 채 약 1.5km 아래 숲 가장자리 삼나무(시베리아 소나무) 쪽으로 내려감
 - 2월에 5명 발견(소나무 근처와 비탈), 5월 4일 나머지 4명을 약 4m 눈 아래 계곡에서 발견 / 6명 저체온증, 3명은 큰 부상(머리 1명, 가슴 2명)
 - 1959년 결론: '저항할 수 없는 자연의 힘', 1959년 5월 수사 종결 / 일기·사진은 2009년 공개
 - 2019년 2월 러시아 검찰 재조사 → 2020년 7월 눈사태(눈판) 결론
 - Gaume·Puzrin, "Mechanisms of slab avalanche release and impact in the Dyatlov Pass incident in 1959",
   Communications Earth & Environment 2: 10 (2021-01-28) — 평균 경사 30도 미만(약 28도), 텐트 자리를 비탈에 깎아 만든 것이 시작,
   활강풍이 텐트 위쪽에 눈을 쌓아 무게가 늘어남, 깎은 뒤 적어도 9시간 지나 무너졌을 수 있음, 약 5m×5m 작은 눈판,
   스키를 깔고 누운 사람에게 떨어지면 가슴·머리 부상이 생길 수 있음(모의실험) / '사건을 다 풀었다고 하지 않는다'(가우메)
 - 반론: 구조대가 눈사태 흔적을 뚜렷하게 보지 못함, 평균 경사가 완만, 텐트로 돌아가지 않은 이유 / 다른 가설: 군사 실험, 초저주파 등"""
import json
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
TITLE = "아홉 명은 왜 텐트를 찢고 나갔나, 과학이 다시 본 디아틀로프 고개의 마지막 밤"
STYLE_NAME = "다큐 수채화"
DIALOGUE = []

NP = " No people, no hands, no arms anywhere."
CUTS = [
    ("c01", "real photo", "1959년 2월 26일 수색대가 발견한 텐트"),
    ("c02", "real photo", "북부 우랄산맥의 겨울"),
    ("c03", "real photo", "디아틀로프 원정대 (1959년 1월)"),
    ("c04", "real photo", "대장 이고리 디아틀로프"),
    ("c05", "real photo", "원정대의 스키 행군"),
    ("c06", "real photo", "유리 유딘과 작별하는 원정대"),
    ("c07", "real photo", "원정대가 남긴 마지막 사진들"),
    ("c08", "real photo", "홀라트샤흘산 비탈"),
    ("c09", "real photo", "안쪽에서 찢긴 텐트"),
    ("c10", "real photo", "눈 위에 남은 발자국"),
    ("c11", "real photo", "숲 가장자리의 삼나무"),
    ("c12", "real photo", "수색대"),
    ("c13", "real photo", "5월, 눈이 녹은 계곡"),
    ("c14", "real photo", "디아틀로프 고개의 추모비"),
    ("c15", "diagram", "그날 밤의 위치"),
    ("c16", "real photo", "우랄 공과대학"),
    ("c17", "diagram", "수많은 가설"),
    ("c18", "real photo", "눈판 눈사태"),
    ("c19", "real photo", "스위스 로잔 연방공대"),
    ("c20", "diagram", "눈판 눈사태가 일어나는 과정 (연구팀 모형)"),
    ("c21", "real photo", "바람에 쌓인 눈"),
    ("c22", "real photo", "눈 덮인 비탈의 금"),
    ("c23", "the inside of a small canvas tent at night pitched in deep snow on a mountain slope, skis laid on the snow floor as a base under blankets, a dim lantern, heavy snow pressing on the tent wall, quiet and ominous." + NP, "스키를 깐 텐트 바닥 (설명 그림)"),
    ("c24", "real photo", "겨울 산의 밤"),
    ("c25", "real photo", "디아틀로프 고개"),
    ("c26", "a quiet snowy mountain pass in the northern Urals at dawn, a small memorial stone with nine flowers on the snow, soft pink light on the peaks, peaceful and solemn." + NP, "아홉 명을 기억하며"),
]

STORY = """{c01}

1959년 2월, 소련 우랄산맥의 눈 덮인 비탈에서 수색대가 텐트 하나를 발견했습니다. 텐트는 안쪽에서 칼로 찢겨 있었고, 그 안에는 아무도 없었습니다. 영하 30도가 넘는 밤, 아홉 명의 젊은이들은 왜 텐트를 찢고 어둠 속으로 나갔을까요?

{c02}

60년 넘게 이 사건은 수많은 추측을 낳았습니다. 군사 실험부터 이상한 소리까지, 온갖 가설이 쏟아졌습니다. 그런데 2021년, 스위스의 과학자들이 국제 학술지에 새로운 답을 내놓았습니다. 오늘은 그 논문과 남아 있는 기록을 따라, 그날 밤을 차분히 되짚어 보겠습니다. 끝까지 보시면 여러 증거를 바탕으로 인공지능이 내린 결론도 들으실 수 있습니다.

## 1. 겨울 산으로 떠난 열 명

{c03}

1959년 1월, 우랄 공과대학의 학생과 졸업생들로 이루어진 원정대가 길을 나섰습니다. 목표는 북부 우랄의 오토르텐산. 스키로 눈 덮인 산을 넘는, 당시로서도 가장 어려운 등급의 겨울 산행이었습니다.

{c04}

대장은 스물세 살의 이고리 디아틀로프였습니다. 경험 많은 산악인이었고, 대원들도 대부분 겨울 산행에 익숙한 사람들이었습니다.

{c05}

처음에는 열 명이었습니다. 원정대는 기차와 트럭을 갈아타고 마지막 마을인 비자이까지 간 뒤, 그곳에서부터 스키를 신고 숲과 강을 따라 북쪽으로 나아갔습니다.

{c06}

그러나 1월 28일, 대원 유리 유딘이 몸이 아파 돌아가야 했습니다. 동료들은 그를 배웅하고 다시 길을 떠났습니다. 남은 사람은 아홉 명, 그 가운데 두 명은 여성이었습니다. 이것이 그가 친구들을 본 마지막이었습니다. 유딘은 이 원정대에서 혼자 살아남은 사람이 되었습니다. 그는 2013년 일흔다섯 살로 세상을 떠날 때까지, 그날 밤의 진실을 알지 못했습니다.

{c07}

대원들은 일기를 쓰고 사진을 찍었습니다. 남은 사진 속 그들은 눈 속에서 웃고, 장난치고, 함께 노래를 불렀습니다. 2009년 공개된 이 기록들은 그들이 평범하고 밝은 젊은이들이었다는 것을 보여 줍니다.

## 2. 비탈 위의 텐트

{c08}

2월 1일 오후, 원정대는 홀라트샤흘산의 비탈에 텐트를 쳤습니다. 숲에서 1.5킬로미터쯤 떨어진, 바람이 그대로 부는 곳이었습니다. 이들은 비탈의 눈을 깎아 평평한 자리를 만들고 그 위에 텐트를 세웠습니다.

{c09}

약속한 날이 지나도 연락이 없자 수색이 시작되었습니다. 2월 26일, 수색대는 반쯤 눈에 묻힌 텐트를 찾았습니다. 텐트는 안쪽에서 찢겨 있었습니다. 옷과 신발, 음식은 대부분 그대로 남아 있었습니다.

{c10}

텐트에서 아래쪽 숲을 향해 발자국이 이어져 있었습니다. 많은 대원이 신발도 제대로 신지 않은 채였지만, 발자국은 서두르지 않고 나란히 걸어 내려간 모습이었습니다.

{c11}

숲 가장자리의 커다란 삼나무 아래에서 두 사람이 발견되었고, 그 근처에서 피운 모닥불의 흔적이 나왔습니다. 나무의 가지는 사람 키보다 높은 곳까지 꺾여 있었습니다. 땔감을 구하려고, 또는 텐트 쪽을 살펴보려고 나무에 올랐던 것으로 보입니다. 그리고 나무와 텐트 사이의 비탈에서 대장 디아틀로프를 포함한 세 사람이 발견되었습니다. 텐트로 돌아가려다 쓰러진 것으로 보였습니다.

{c12}

나머지 네 사람은 쉽게 찾지 못했습니다. 수색은 몇 달 동안 이어졌습니다.

{c13}

5월 4일, 눈이 녹기 시작한 계곡에서 마지막 네 사람이 발견되었습니다. 이들은 4미터 가까운 눈 아래에 있었습니다. 그리고 이 가운데 세 사람에게서 큰 부상이 발견되었습니다. 두 사람은 가슴에, 한 사람은 머리에 심한 상처가 있었습니다.

{c14}

조사 결과, 아홉 명 가운데 여섯 명은 추위로 인한 저체온증으로, 세 명은 큰 부상으로 숨졌습니다. 1959년 5월, 당국은 저항할 수 없는 자연의 힘이 원인이라는 짧은 결론을 내리고 수사를 마쳤습니다.

## 3. 60년 동안의 수수께끼

{c15}

하지만 이 결론은 아무것도 설명하지 못했습니다. 경험 많은 산악인들이 왜 한밤중에 따뜻한 옷도 없이 텐트를 찢고 나갔을까? 겉으로 상처가 거의 없는데 어떻게 가슴뼈가 부러졌을까? 젊은 아홉 명의 죽음은 가족과 친구들에게 오랫동안 풀리지 않는 상처로 남았습니다.

{c16}

소련 시절 사건 기록은 오랫동안 공개되지 않았습니다. 그 빈자리를 수많은 추측이 채웠습니다.

{c17}

군사 무기 실험이 있었다는 이야기, 귀에 들리지 않는 낮은 소리가 공포를 일으켰다는 이야기, 심지어 설인이나 외계인 이야기까지 나왔습니다. 하지만 어느 것도 증거로 뒷받침되지 않았습니다.

{c18}

가장 그럴듯한 설명은 눈사태였습니다. 텐트 위로 눈이 덮치자 대원들이 급히 텐트를 찢고 빠져나왔다는 것입니다. 하지만 이 설명에도 문제가 있었습니다. 비탈은 눈사태가 나기에는 완만했고, 구조대는 눈사태의 뚜렷한 흔적을 보지 못했습니다. 그날 밤 눈도 내리지 않았습니다.

{c19}

2019년 러시아 검찰이 사건을 다시 조사했고, 2020년 7월 눈사태가 원인이라고 발표했습니다. 하지만 어떻게 그런 눈사태가 일어났는지에 대한 설명이 부족해, 많은 사람들은 여전히 고개를 저었습니다. 그 고개는 지금 원정대 대장의 이름을 따 디아틀로프 고개라고 불립니다.

## 4. 과학자들의 새로운 답

{c20}

2021년 1월, 스위스 로잔 연방공대의 요한 가우메 교수와 취리히 연방공대의 알렉산더 푸즈린 교수가 학술지 커뮤니케이션스 지구와 환경에 논문을 발표했습니다. 이들은 눈사태 가설의 문제점들을 하나씩 따져 보았습니다.

{c21}

첫 번째 열쇠는 바람이었습니다. 산 위에서 아래로 부는 차갑고 무거운 바람, 활강풍이 눈을 실어 와 텐트 위쪽 비탈에 조금씩 쌓았습니다. 원정대가 알 수 없었던 지형 때문에, 눈은 바로 그 자리에 모였습니다.

{c22}

두 번째 열쇠는 원정대가 깎아 낸 비탈이었습니다. 텐트 자리를 만들려고 눈을 깎자, 그 위의 눈층을 받치던 힘이 약해졌습니다. 거기에 바람에 실려 온 눈의 무게가 천천히 더해졌습니다. 연구팀의 계산으로는 비탈을 깎은 뒤 적어도 9시간쯤 지나 눈판에 금이 가고 무너질 수 있었습니다. 그날 밤 눈이 내리지 않았는데도 눈사태가 날 수 있었던 것입니다.

{c23}

무너진 것은 크기 5미터쯤의 작은 눈판이었을 것으로 보입니다. 작아서 흔적도 적게 남았습니다. 연구팀은 컴퓨터 모의실험으로, 바닥에 스키를 깔고 누운 사람 위로 단단한 눈판이 떨어지면 겉에 큰 상처 없이 가슴과 머리에 심한 부상이 생길 수 있다는 것을 보였습니다.

{c24}

그렇다면 대원들이 텐트를 찢고 나간 이유도 설명됩니다. 한밤중에 텐트가 무너지고 동료들이 다치자, 더 큰 눈사태가 올까 봐 서둘러 빠져나와 숲으로 피한 것입니다. 숲 가장자리에서 불을 피우고 버티려 했지만, 영하 30도의 바람을 이기지 못했습니다.

## 5. 인공지능의 결론

{c25}

그렇다면 인공지능인 제가 증거들을 모아 내린 결론은 이렇습니다. 첫째, 작은 눈판 눈사태는 지금까지 나온 설명 가운데 증거와 가장 잘 맞습니다. 찢긴 텐트, 나란한 발자국, 겉에 상처가 없는 부상, 그리고 눈이 오지 않은 밤까지 하나의 흐름으로 설명할 수 있기 때문입니다.

{c26}

둘째, 그러나 모든 것이 풀린 것은 아닙니다. 왜 텐트로 돌아가지 않았는지, 그날 밤 대원들 사이에 무슨 일이 있었는지는 아무도 알 수 없습니다. 연구자들도 이 사건을 다 풀었다고 말하지 않습니다. 셋째, 이 이야기에서 가장 무서운 것은 괴물이나 비밀 무기가 아니었습니다. 작은 실수 하나와 자연의 힘이 겹친 비극이었습니다. 젊은 아홉 명의 이름이 그 고개에 지금도 남아 있습니다. 여러분은 그날 밤 무슨 일이 있었다고 생각하시나요? 댓글로 들려주세요."""


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
        proj = {"ver": 7, "category": "장문", "genre": "[다큐] 미스터리", "topic": "디아틀로프 고개 사건", "title": TITLE,
                "story": story, "sources": ["https://doi.org/10.1038/s43247-020-00081-8", "https://en.wikipedia.org/wiki/Dyatlov_Pass_incident", "https://www.advancedsciencenews.com/researchers-shed-light-on-the-1959-dyatlov-pass-incident/"],
                "notes": "고고학 장문 다큐(최신 논문) (실제 사진·논문 그림 위주 + 사진이 없는 장면은 AI 그림)", "autophoto": False, "img_source": "그림: 수채화",
                "settings": {"format": "롱폼 가로(1920×1080)", "narration": "on",
                             "layout": "자막형(큰 제목+사진+자막)", "img_fill": "전체 화면(글자가 사진 위에)",
                             "img_motion": "천천히 확대만", "scene_trans": "전진(확대하며 다음 장면)",   # 계속 앞으로 나아가는 느낌(사용자 요청 2026-10-26)
                             "head_show": "안 보임(제목 카드만)", "sub_split": "한 줄씩(문장·쉼표로 나눠 차례로)", "img_label": "on",
                             "narr_voice": "Supertonic M2 (남성, 무료 로컬) [supertonic:M2]", "narr_rate": -8, "narr_tone_m": -1}}   # 장문 다큐 성우(사용자 결정 2026-10-26 오후: 샘플 2번 — 전에는 3번)
        out = os.path.join(HERE, "디아틀로프.json")
        json.dump(proj, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(out, len(story), "chars")


if __name__ == "__main__":
    main()
