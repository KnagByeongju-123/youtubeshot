"""장문 고고학 다큐 '트로이 전쟁은 실화였을까, 성벽 앞에서 쏟아진 3,200년 전 투석 돌' — 대본 + 컷별 사진·그림 계획
python 장문/트로이/트로이.py job <저장폴더> [c01,...]  → 그림 주문서(다큐 수채화) job.json (사진 컷은 빼고)
python 장문/트로이/트로이.py project <그림폴더>       → 프로젝트 파일 장문/트로이/트로이.json
사용자 요청(2026-10-26): 최신 논문 기반 고고학 미스터리 4번 — 트로이 성벽 앞 투석 돌
사실 확인:
 - 2025년 7월 차나칼레 온세키즈 마르트 대학 뤼스템 아슬란 교수팀: 트로이 6층 궁전 성벽 바로 바깥 좁은 곳에 투석 돌(진흙·강돌)이 몰려 나옴,
   불탄 흔적·급히 묻은 유골 / "좁은 곳에 이렇게 많은 투석 돌 = 치열한 방어나 총공격" / 트로이 전쟁과 이어지는지는 더 조사해야 한다고 함 (Archaeology 2025-07-10)
 - 히사를리크(튀르키예 차나칼레), 프랭크 캘버트, 하인리히 슐리만 1871년~ 발굴, '프리아모스의 보물'(1873)은 실제로는 트로이 2층(약 기원전 2500~2300년)
 - 층 9개(작은 층 46개 이상), 기원전 3000년 무렵~서기 500년 무렵 / 블레겐 1932~38: 트로이 7a 불탐(기원전 1180년 무렵)
 - 만프레트 코르프만 1988~2005: 성 아래 '아래 도시'와 방어 도랑, 도시 넓이 약 30헥타르
 - 히타이트 문서의 '윌루사'(=일리오스), 알락산두 왕과의 조약(기원전 1280년 무렵), '아히야와'(=아카이아 사람?) / 1995년 트로이에서 루위어 청동 도장
 - 1998년 유네스코 세계유산, 2018년 트로이 박물관 개관 / 호메로스 일리아스(기원전 8세기 무렵), 트로이 목마는 일리아스에 없고 오디세이아·아이네이스에 나옴"""
import json
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
TITLE = "트로이 전쟁은 실화였을까, 성벽 앞에서 쏟아진 3,200년 전 투석 돌"
STYLE_NAME = "다큐 수채화"
DIALOGUE = []

NP = " No people, no hands, no arms anywhere."
CUTS = [
    ("c01", "real photo", "트로이 유적의 성벽"),
    ("c02", "real photo", "호메로스 흉상"),
    ("c03", "real photo", "트로이 전쟁을 그린 고대 그리스 도자기"),
    ("c04", "real photo", "아킬레우스와 헥토르"),
    ("c05", "real photo", "트로이 유적의 목마 모형"),
    ("c06", "real photo", "히사를리크 언덕 — 트로이 유적"),
    ("c07", "real photo", "하인리히 슐리만"),
    ("c08", "real photo", "트로이 유적 — 여러 층이 드러난 모습"),
    ("c09", "real photo", "하인리히 슐리만 (만년)"),
    ("c10", "diagram", "트로이의 9개 층"),
    ("c11", "real photo", "트로이 6층의 성벽"),
    ("c12", "real photo", "트로이 6층의 동쪽 성문"),
    ("c13", "real photo", "히타이트 점토판"),
    ("c14", "real photo", "히타이트 점토판 (쐐기 문자)"),
    ("c15", "real photo", "트로이 유적 전경"),
    ("c16", "real photo", "청동기 시대의 무기"),
    ("c17", "a pile of hundreds of small rounded sling stones of grey river pebbles and baked clay lying in excavated soil at the foot of an ancient limestone city wall, archaeological trench, measuring tape, sunny daylight, close view." + NP, "성벽 앞에 몰려 나온 투석 돌 (설명 그림)"),
    ("c18", "real photo", "투석용 탄환들 (후대 유물, 참고)"),
    ("c19", "real photo", "고대 그리스의 투석용 납 탄환 (참고 유물)"),
    ("c20", "real photo", "트로이의 경사로"),
    ("c21", "real photo", "트로이 유적과 주변 평야"),
    ("c22", "real photo", "트로이 7층과 9층의 성벽"),
    ("c23", "real photo", "트로이의 성벽"),
    ("c24", "real photo", "트로이 유적의 목마 모형"),
    ("c25", "real photo", "트로이 유적"),
    ("c26", "the ruined sloping limestone walls of ancient Troy on a hill at sunset, wild grass, the distant plain and sea, long shadows, timeless and contemplative." + NP, "신화와 역사 사이"),
]

STORY = """{c01}

3천 년 가까이 사람들은 물었습니다. 트로이 전쟁은 정말 있었을까, 아니면 시인이 지어낸 이야기일까. 그런데 2025년 여름, 튀르키예의 트로이 유적에서 이 질문에 새로운 실마리가 나왔습니다. 궁전 성벽 바로 앞에서 투석 돌이 무더기로 쏟아져 나온 것입니다.

{c02}

오늘은 호메로스의 서사시에서 출발해, 150년 동안 이어진 발굴과 최신 발견까지 트로이의 수수께끼를 차근차근 풀어 보겠습니다. 끝까지 보시면 여러 증거를 바탕으로 인공지능이 내린 결론도 들으실 수 있습니다.

## 1. 일리아스의 전쟁

{c03}

기원전 8세기 무렵, 그리스의 시인 호메로스는 서사시 일리아스를 남겼습니다. 트로이의 왕자 파리스가 스파르타의 왕비 헬레네를 데려가자, 그리스 연합군이 바다를 건너 트로이를 10년 동안 포위했다는 이야기입니다. 일리아스는 1만 5천 줄이 넘는 긴 시인데, 정작 10년 전쟁 가운데 마지막 해의 몇 주 동안만을 다룹니다.

{c04}

일리아스에는 그리스 최고의 전사 아킬레우스와 트로이의 왕자 헥토르의 대결이 담겨 있습니다. 흥미롭게도 일리아스는 트로이가 함락되기 전에 끝납니다.

{c05}

우리가 잘 아는 트로이 목마는 일리아스가 아니라, 오디세이아와 훗날 로마의 시인 베르길리우스의 아이네이스에 나옵니다. 그리스군이 커다란 나무 말 속에 병사들을 숨겨 성안으로 들어갔다는 이야기입니다.

## 2. 트로이를 찾은 사람

{c06}

오랫동안 많은 학자들은 트로이를 상상 속의 도시로 여겼습니다. 그러나 튀르키예 북서쪽 차나칼레 근처의 히사를리크 언덕이 트로이일 것이라고 본 사람들이 있었습니다. 그 가운데 한 명이 언덕의 일부를 가지고 있던 영국인 프랭크 캘버트였습니다. 그는 이 언덕을 먼저 조금 파 보았고, 슐리만에게 이곳을 알려 주었습니다.

{c07}

1871년, 독일의 사업가 하인리히 슐리만이 이 언덕을 파기 시작했습니다. 그는 어릴 때부터 트로이가 실제로 있었다고 믿었다고 말했습니다. 언덕 아래에서는 정말로 여러 겹의 옛 도시가 나왔습니다.

{c08}

하지만 슐리만은 호메로스의 트로이를 빨리 찾고 싶어 언덕 한가운데를 크게 파 내려갔습니다. 그 과정에서 위쪽 층들이 많이 부서졌습니다. 이 거대한 구덩이는 지금도 유적에 남아 있고, 사람들은 이것을 슐리만의 구덩이라고 부릅니다. 고고학이 아직 서툴던 시절의 아픈 교훈입니다.

{c09}

1873년, 슐리만은 금은 보물을 찾아내고 '프리아모스의 보물'이라고 불렀습니다. 트로이 왕의 보물이라는 뜻입니다. 그러나 훗날 이 보물은 트로이 전쟁보다 천 년 넘게 앞선 시대의 것으로 밝혀졌습니다. 슐리만은 이 보물을 몰래 독일로 가져갔고, 2차 세계대전이 끝난 뒤에는 소련으로 옮겨져 지금은 모스크바의 푸시킨 박물관에 있습니다.

## 3. 아홉 겹의 도시

{c10}

트로이 유적에는 기원전 3천 년 무렵부터 서기 500년 무렵까지, 무려 3,500년의 역사가 아홉 개의 큰 층으로 쌓여 있습니다. 학자들은 맨 아래 층을 트로이 1층이라 부르고, 위로 올라가며 차례로 번호를 붙였습니다. 작은 층까지 나누면 40개가 넘습니다. 한 도시가 무너지면 그 위에 다시 도시를 세우기를 수천 년 동안 되풀이한 것입니다.

{c11}

이 가운데 트로이 전쟁의 시대와 맞는 층은 6층과 7층입니다. 기원전 13세기 무렵의 트로이 6층은 높고 비스듬한 돌 성벽과 탑을 갖춘 강한 도시였습니다. 그 성벽의 일부는 3천 년이 지난 지금도 유적에 우뚝 남아 있습니다.

{c12}

1930년대 미국 신시내티 대학의 고고학자 칼 블레건은 트로이 7층이 기원전 1180년 무렵 불에 타 무너진 흔적을 찾았습니다. 그는 집 안 바닥에 묻어 둔 커다란 저장 항아리들도 찾아냈습니다. 포위를 견디려고 식량을 쌓아 둔 흔적일 수 있다는 것입니다. 그래서 그는 이것이 전쟁의 흔적일 수 있다고 보았습니다.

{c13}

1988년부터는 독일의 만프레트 코르프만이 발굴을 이끌었습니다. 그는 언덕 위 성채 아래로 큰 도시가 펼쳐져 있었고, 그 둘레에 방어용 도랑이 파여 있었다는 것을 밝혀냈습니다. 트로이는 작은 성이 아니라 넓이 약 30헥타르의 큰 도시였던 것입니다. 코르프만은 그 무렵 트로이에 5천에서 1만 명쯤 살았을 것으로 보았습니다.

## 4. 히타이트 문서 속 윌루사

{c14}

트로이의 존재를 알려 주는 증거는 바다 건너에서도 나왔습니다. 당시 아나톨리아를 다스린 강대국 히타이트의 수도 하투샤에서 나온 점토판입니다.

{c15}

히타이트 문서에는 윌루사라는 나라가 나옵니다. 많은 학자들은 이것이 그리스 사람들이 일리오스라고 부른 트로이라고 봅니다. 기원전 1280년 무렵에는 윌루사의 왕 알락산두와 맺은 조약도 있습니다. 알락산두는 파리스의 다른 이름인 알렉산드로스와 소리가 닮았습니다.

{c16}

히타이트 문서에는 아히야와라는 바다 건너 세력이 윌루사를 두고 다툼을 벌였다는 기록도 있습니다. 아히야와는 호메로스가 그리스 사람들을 부른 이름, 아카이아와 닮았습니다. 이 무렵 이 지역에 실제로 긴장이 있었다는 뜻입니다. 1995년에는 트로이 유적에서 히타이트와 가까운 루위어 상형문자가 새겨진 청동 도장도 나왔습니다. 트로이 7층에서 나온 유일한 글자입니다.

## 5. 성벽 앞의 투석 돌

{c17}

그리고 2025년, 차나칼레 대학교 뤼스템 아슬란 교수팀이 트로이 6층 궁전의 성벽 바로 바깥에서 놀라운 것을 찾았습니다. 좁은 구역에 투석 돌이 무더기로 몰려 있었던 것입니다.

{c18}

투석 돌은 가죽 끈으로 빙빙 돌려 던지는 돌입니다. 강돌이나 구운 진흙으로 만들었고, 잘 맞으면 사람을 크게 다치게 할 수 있었습니다. 고대 전쟁에서 투석병은 활을 쏘는 병사만큼 무서운 존재였습니다. 숙련된 투석병은 돌을 수백 미터까지 날려 보낼 수 있었다고 전해집니다. 값싸고 구하기 쉬운 돌이 성을 지키는 사람에게도, 공격하는 사람에게도 중요한 싸움 도구였던 것입니다.

{c19}

아슬란 교수는 이렇게 말했습니다. 이렇게 좁은 곳에 이렇게 많은 투석 돌이 있다는 것은 치열한 전투, 절박한 방어나 전면적인 공격이 있었다는 뜻이라고 말입니다.

{c20}

주변에서는 불에 탄 흔적과 서둘러 묻힌 사람의 뼈도 나왔습니다. 트로이는 다르다넬스 해협 입구를 지키는 자리에 있어서, 바다를 오가는 배와 무역을 다스리며 부유해질 수 있었습니다. 그만큼 노리는 세력도 많았을 것입니다. 도시가 불탔고, 사람들이 제대로 장례를 치를 겨를도 없었다는 증거입니다.

{c21}

당시 트로이 앞까지 들어와 있던 바다는 강이 실어 온 흙에 메워져, 지금은 유적에서 몇 킬로미터 떨어져 있습니다. 하지만 아슬란 교수도 조심스럽습니다. 이 투석 돌이 호메로스가 노래한 바로 그 전쟁의 흔적인지는 더 조사해야 한다고 말했습니다. 예전에도 트로이에서 전투의 흔적이 나왔지만 모든 학자를 설득하지는 못했습니다.

{c22}

트로이 6층이 무너진 까닭을 지진으로 보는 학자도 있습니다. 실제로 이 지역은 지진이 잦은 곳입니다. 그래서 일부에서는 땅을 뒤흔드는 바다의 신 포세이돈의 상징이 말이었다는 점을 들어, 트로이 목마가 지진을 빗댄 이야기라는 주장을 내놓기도 합니다. 물론 증거가 있는 이야기는 아닙니다.

## 6. 인공지능의 결론

{c23}

그렇다면 인공지능인 제가 증거들을 모아 내린 결론은 이렇습니다. 첫째, 트로이라는 도시는 분명히 있었습니다. 히사를리크의 유적과 히타이트 문서가 그것을 말해 줍니다.

{c24}

둘째, 기원전 13세기에서 12세기 무렵 트로이가 전쟁과 불, 그리고 어쩌면 지진을 겪었다는 증거도 쌓이고 있습니다. 성벽 앞의 투석 돌은 그 가운데 가장 생생한 증거입니다. 그 뒤에도 트로이는 사라지지 않았습니다. 훗날 그리스 사람들은 이곳에 일리온이라는 도시를 세웠고, 알렉산드로스 대왕도 이곳을 찾아 아킬레우스를 기렸다고 전해집니다.

{c25}

셋째, 그러나 아킬레우스와 헥토르, 10년의 포위, 그리고 나무 말은 증명되지 않았습니다. 일리아스는 실제로 있었던 여러 전쟁의 기억을 수백 년 동안 이어 붙여 만든 위대한 이야기에 가깝습니다.

{c26}

트로이 유적은 1998년 유네스코 세계유산이 되었고, 2018년에는 유적 근처에 트로이 박물관이 문을 열었습니다. 신화 속 트로이는 시인의 상상이었지만, 그 상상이 서 있던 땅은 진짜였습니다. 앞으로 발굴이 이어지면 투석 돌을 던진 사람들이 누구였는지도 밝혀질지 모릅니다. 여러분은 트로이 전쟁이 실제로 있었다고 생각하시나요? 댓글로 들려주세요."""


REFS = {"c18": ["c11_1"], "c26": ["c01_4"]}
SEED = {}
REF_NOTE = ("Any real place or object shown must look exactly like the reference photo (same shape and colors), "
            "painted in the same watercolor style. ")

# 컷 → 사진 후보 이름 (사진후보/후보.json 의 열쇠). 사진을 받은 뒤 채움
PHOTOS = {'c01': 'c01_4', 'c02': 'c02_1', 'c03': 'c03_2', 'c04': 'c04_1', 'c05': 'c24_3', 'c06': 'c01_1', 'c07': 'c07_1', 'c08': 'c12_2', 'c09': 'c07_4', 'c10': 'c10_도표', 'c11': 'c11_1', 'c12': 'c12_1', 'c13': 'c13_1', 'c14': 'c13_2', 'c15': 'c15_1', 'c16': 'c16_3', 'c18': 'c19_1', 'c19': 'c19_3', 'c20': 'c12_3', 'c21': 'c15_2', 'c22': 'c22_1', 'c23': 'c12_4', 'c24': 'c24_1', 'c25': 'c11_4'}


def main():
    cmd, folder = sys.argv[1], sys.argv[2]
    main_src = os.path.join(ROOT, "..", "shorts_novel_maker_supertonic.py")      # 작업 가지(메인 저장소)의 최신 화풍 목록이 우선
    src = open(main_src if os.path.exists(main_src) else os.path.join(ROOT, "shorts_novel_maker_supertonic.py"), encoding="utf-8").read()
    style = re.search('"' + re.escape(STYLE_NAME) + '": "([^"]+)"', src).group(1)
    only = sys.argv[3].split(",") if len(sys.argv) > 3 else None
    if cmd == "job":
        items = []
        for cid, desc, _ in CUTS:
            if (only and cid not in only) or cid in PHOTOS or "(real photo)" in desc or desc in ("diagram", "paper figure"):
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
        proj = {"ver": 7, "category": "장문", "genre": "[다큐] 고고학", "topic": "트로이 투석 돌", "title": TITLE,
                "story": story, "sources": ["https://archaeology.org/news/2025/07/10/new-evidence-alludes-to-military-conflict-at-ancient-troy/", "https://en.wikipedia.org/wiki/Troy", "https://en.wikipedia.org/wiki/Wilusa", "https://whc.unesco.org/en/list/849/"],
                "notes": "고고학 장문 다큐(최신 논문) (실제 사진·논문 그림 위주 + 사진이 없는 장면은 AI 그림)", "autophoto": False, "img_source": "그림: 수채화",
                "settings": {"format": "롱폼 가로(1920×1080)", "narration": "on",
                             "layout": "자막형(큰 제목+사진+자막)", "img_fill": "전체 화면(글자가 사진 위에)",
                             "img_motion": "천천히 확대만", "scene_trans": "전진(확대하며 다음 장면)",   # 계속 앞으로 나아가는 느낌(사용자 요청 2026-10-26)
                             "head_show": "안 보임(제목 카드만)", "sub_split": "한 줄씩(문장·쉼표로 나눠 차례로)", "img_label": "on",
                             "narr_voice": "Supertonic M2 (남성, 무료 로컬) [supertonic:M2]", "narr_rate": -8, "narr_tone_m": -1}}   # 장문 다큐 성우(사용자 결정 2026-10-26 오후: 샘플 2번 — 전에는 3번)
        out = os.path.join(HERE, "트로이.json")
        json.dump(proj, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(out, len(story), "chars")


if __name__ == "__main__":
    main()
