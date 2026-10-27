"""장문 고고학 다큐 '수십 톤 모아이는 어떻게 움직였나, 과학이 밝힌 답은 걸어서였다' — 대본 + 컷별 사진·그림 계획
python 장문/모아이/모아이.py job <저장폴더> [c01,...]  → 그림 주문서(다큐 수채화) job.json (사진 컷은 빼고)
python 장문/모아이/모아이.py project <그림폴더>       → 프로젝트 파일 장문/모아이/모아이.json
사용자 요청(2026-10-27): 밝혀진 미스터리 — 1번 모아이 (2번 페루 구멍 띠 다음)
사실 확인:
 - Lipo·Hunt, "The walking moai hypothesis: Archaeological evidence, experimental validation, and response to critics",
   Journal of Archaeological Science 183: 106383 (2025-10), doi 10.1016/j.jas.2025.106383 (빙엄턴대·애리조나대)
   석상 962개 분석, 길가 석상 62개 중심 / 3D 모형 / 밑면이 넓은 D자, 앞으로 6~15도 기울어짐 / 4.35톤 복제 석상을 밧줄과 18명이 40분에 100m
   (통나무 없음, 서서 지그재그로 흔들며) / 처음 흔들기 시작할 때가 가장 힘듦 / 길 폭 약 4.5m, 가운데가 오목 → 석상이 흔들려도 안정
   길이 겹치고 나란히 난 곳 → 석상이 나아가는 대로 길을 새로 닦음 / 깨지거나 버려진 석상의 절반 넘게(51.6%) 채석장 라노 라라쿠에서 2km 안
   / 15~60명이면 출발, 5~25명이면 계속 / 옛 이야기: 석상이 '걸어서' 아후(제단)까지 갔다 / 립포 "다른 어떤 설명도 지금은 이걸 설명 못 함"
 - 붕괴설 반박(2024): Davis 외 Science Advances(2024-06) — 돌밭(바위 정원) 실제 면적 약 0.76㎢ → 인구는 수천 명 수준, 1만 7천 명이 아님
   Moreno-Mayar 외 Nature(2024-09) — 1670~1950년 사람 15명의 유전체, 1600년대 인구 붕괴 흔적 없음, 유럽인보다 먼저 아메리카 원주민과 섞임
 - 일반 사실(위키백과 등): 칠레에서 약 3,500km, 석상 약 1,000개, 대부분 라노 라라쿠 응회암, 1722년 부활절 로헤베인 도착, 가장 큰 세운 석상 파로 약 10m,
   채석장에 미완성 '엘 히간테' 약 21m / 1950년대 헤위에르달 탐험, 1980년대 체코 기술자 파벨 파벨의 세워 걷기 실험, 2012년 립포·헌트 실험
 - 한계: 4.35톤 복제로 한 실험 — 가장 큰 석상까지 그대로 된다는 것은 연구자의 추정, 가파른 비탈·밧줄 세기는 논문이 다룬다고 하나 직접 시험 범위는 확인 필요"""
import json
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
TITLE = "수십 톤 모아이는 어떻게 움직였나, 과학이 밝힌 답은 걸어서였다"
STYLE_NAME = "다큐 수채화"
DIALOGUE = []

NP = " No people, no hands, no arms anywhere."
CUTS = [
    ("c01", "real photo", "아후 통가리키의 모아이 15개"),
    ("c02", "real photo", "태평양 한가운데의 이스터섬"),
    ("c03", "real photo", "채석장 라노 라라쿠의 모아이"),
    ("c04", "real photo", "채석장에 남은 미완성 모아이"),
    ("c05", "real photo", "제단(아후) 위의 모아이"),
    ("c06", "real photo", "1722년 이스터섬에 온 로헤베인의 배 (옛 그림)"),
    ("c07", "real photo", "토르 헤위에르달"),
    ("c08", "diagram", "모아이를 옮긴 방법, 쏟아진 가설"),
    ("c09", "real photo", "나무가 사라진 이스터섬의 풀밭"),
    ("c10", "real photo", "길가에 쓰러진 모아이"),
    ("c11", "diagram", "길가 모아이의 비밀"),
    ("c12", "real photo", "옆에서 본 모아이"),
    ("c13", "diagram", "4.35톤 복제 모아이 실험"),
    ("c14", "Rapa Nui islanders in simple bark-cloth wraps walking a large upright stone moai statue along a dirt road using three long ropes, one team on each side pulling alternately and one team behind, the statue rocking side to side, grassy hills and the sea behind, morning light", "밧줄로 모아이를 '걷게' 하는 모습 (상상 복원)"),
    ("c15", "real photo", "라노 라라쿠에서 뻗어 나간 옛길"),
    ("c16", "diagram", "모아이가 걸은 길"),
    ("c17", "real photo", "옮기다 깨진 모아이"),
    ("c18", "diagram", "채석장 가까이에 쓰러진 석상들"),
    ("c19", "real photo", "아후 아키비의 일곱 모아이"),
    ("c20", "real photo", "모아이의 붉은 돌 모자(푸카오)"),
    ("c21", "real photo", "이스터섬의 돌밭(바위 정원)"),
    ("c22", "real photo", "오늘날의 라파누이 사람들"),
    ("c23", "real photo", "아후 통가리키의 해돋이"),
    ("c24", "real photo", "라노 라라쿠 비탈의 모아이 머리들"),
    ("c25", "real photo", "아나케나 해변의 모아이"),
    ("c26", "silhouettes of several huge stone moai statues standing on a grassy hill on Easter Island at dusk, dramatic orange and purple sky, the Pacific ocean in the distance, quiet and majestic." + NP, "해 질 녘의 모아이"),
]

STORY = """{c01}

태평양 한가운데 외딴섬에 거대한 돌 얼굴들이 서 있습니다. 이스터섬의 모아이입니다. 큰 것은 높이 10미터, 무게는 수십 톤에 이릅니다. 섬에는 이런 석상이 무려 1,000개 가까이 있습니다.

{c02}

그런데 이상합니다. 이 섬에는 바퀴도, 소나 말도, 큰 기계도 없었습니다. 그렇다면 옛 섬사람들은 이 무거운 석상을 어떻게 섬 곳곳으로 옮겼을까요? 수백 년 동안 수수께끼였고, 외계인이 옮겼다는 말까지 나왔습니다. 그런데 2025년, 고고학 학술지에 이 질문에 대한 답이 실렸습니다. 석상은 걸어서 갔다는 것입니다. 오늘은 그 논문을 따라 모아이의 비밀을 풀어 보겠습니다. 끝까지 보시면 증거를 모아 인공지능이 내린 결론도 들으실 수 있습니다.

## 1. 세상 끝의 돌 얼굴

{c03}

이스터섬은 칠레에서 3,500킬로미터나 떨어진, 세상에서 가장 외딴 섬 가운데 하나입니다. 약 800년 전, 폴리네시아 사람들이 카누를 타고 먼바다를 건너 이 섬에 처음 자리 잡았습니다. 섬사람들은 스스로를 라파누이라고 부릅니다. 모아이는 대부분 라노 라라쿠라는 화산의 채석장에서 깎아 만들었습니다. 화산재가 굳은 비교적 무른 돌이라 돌 도구로 깎을 수 있었습니다.

{c04}

채석장에는 아직 다 깎지 못한 석상이 수백 개 남아 있습니다. 그중 가장 큰 것은 길이가 21미터나 됩니다. 만들다 만 석상들은 마치 일하던 사람들이 어느 날 갑자기 손을 놓고 떠난 것처럼 보입니다.

{c05}

완성된 석상은 채석장에서 몇 킬로미터, 멀게는 10킬로미터 넘게 떨어진 해안의 제단, 아후 위로 옮겨졌습니다. 석상은 대부분 바다를 등지고 마을 쪽을 바라봅니다. 조상을 기리는 석상이었기 때문입니다. 석상의 평균 높이는 약 4미터, 무게는 10톤이 넘습니다.

## 2. 쏟아진 가설들

{c06}

1722년 부활절, 네덜란드의 항해가 로헤베인이 이 섬에 처음 왔습니다. 그래서 이름이 이스터섬, 부활절 섬이 됐습니다. 유럽 사람들은 거대한 석상을 보고 깜짝 놀랐습니다. 나무도 밧줄도 넉넉해 보이지 않는 섬에서 어떻게 이걸 옮겼을까요?

{c07}

1950년대에는 노르웨이의 탐험가 헤위에르달이 이 섬을 조사하며 석상을 세우는 실험을 했습니다. 그 뒤로 수많은 가설이 나왔습니다.

{c08}

석상을 눕혀서 통나무 위로 굴렸다, 나무 썰매에 실어 끌었다, 그리고 외계인이 옮겨 줬다는 이야기까지. 그런데 섬사람들의 옛이야기는 전혀 달랐습니다. 석상이 스스로 걸어서 제단까지 갔다는 것입니다.

{c09}

눕혀서 옮겼다는 설명은 또 다른 이야기를 낳았습니다. 석상을 굴릴 통나무를 얻으려고 섬사람들이 숲을 모두 베어 버렸고, 그 바람에 섬이 망했다는 것입니다. 이 이야기는 2005년 미국의 학자 제러드 다이아몬드가 쓴 책, 문명의 붕괴에도 환경 파괴의 교훈으로 실려 널리 알려졌습니다. 하지만 최근의 연구는 이 이야기도 뒤집고 있습니다. 이 이야기는 뒤에서 다시 하겠습니다.

## 3. 길가에 쓰러진 석상들

{c10}

미국 빙엄턴 대학의 칼 립포와 애리조나 대학의 테리 헌트는 오랫동안 이 섬을 연구했습니다. 이들은 석상 962개를 조사하고, 그중 옛길 위에 쓰러져 있는 석상 62개를 특히 자세히 들여다봤습니다. 옮기다가 멈춘 석상들이니, 옮긴 방법의 흔적이 남아 있을 것이기 때문입니다.

{c11}

그러자 놀라운 공통점이 보였습니다. 길가의 석상들은 제단 위의 석상과 모양이 달랐습니다. 밑면이 알파벳 디 자처럼 넓고, 몸이 앞으로 6도에서 15도쯤 기울어 있었습니다. 이런 모양이면 석상을 세운 채로 좌우로 흔들 수 있습니다.

{c12}

제단에 세운 석상은 똑바로 서도록 밑면을 다시 깎았지만, 길 위의 석상은 걷기 좋은 모양 그대로였습니다. 처음부터 걸어가도록 설계해서 깎았다는 뜻입니다.

## 4. 직접 걷게 해 보다

{c13}

연구팀은 2012년에 직접 실험했습니다. 길가 석상과 같은 모양으로 4.35톤짜리 복제 석상을 만들었습니다. 그리고 통나무 없이 밧줄만으로 옮겨 봤습니다. 결과는 놀라웠습니다. 단 18명이 40분 만에 석상을 100미터나 옮겼습니다.

{c14}

방법은 이렇습니다. 석상 머리에 밧줄 세 가닥을 맵니다. 양옆의 두 무리가 번갈아 당기면 석상이 좌우로 기우뚱거리며 한 발씩 앞으로 나아갑니다. 뒤쪽 무리는 석상이 넘어지지 않게 붙잡습니다. 멀리서 보면 정말 석상이 뒤뚱뒤뚱 걸어가는 것처럼 보입니다. 연구자는 가장 힘든 것은 처음 흔들기 시작할 때이고, 일단 흔들리기 시작하면 생각보다 쉽게 나아간다고 말합니다.

## 5. 석상이 걸은 길

{c15}

증거는 길에도 남아 있었습니다. 채석장에서 뻗어 나간 옛길은 폭이 4.5미터쯤 되고, 가운데가 살짝 오목하게 파여 있습니다. 오목한 길은 석상이 좌우로 흔들려도 옆으로 쓰러지지 않게 잡아 줍니다.

{c16}

길이 겹치거나 나란히 난 곳도 있었습니다. 석상이 나아가는 대로 사람들이 앞쪽 길을 새로 닦았다는 뜻입니다. 연구팀은 15명에서 60명이면 출발할 수 있고, 일단 걷기 시작하면 5명에서 25명으로도 충분했을 것으로 봅니다.

{c17}

물론 모든 석상이 무사히 도착하지는 못했습니다. 걷다가 넘어져 깨진 석상들이 길가에 그대로 남았습니다. 어떤 석상은 얼굴을 땅에 묻은 채, 어떤 석상은 하늘을 바라본 채 누워 있습니다.

{c18}

그런데 그 위치가 의미심장합니다. 깨지거나 버려진 석상의 절반 넘게가 채석장에서 2킬로미터 안에 몰려 있습니다. 출발한 직후에 많이 넘어지고, 멀리 갈수록 줄어드는 모습입니다. 걸어서 옮기다 넘어졌다면 딱 이렇게 됩니다.

## 6. 무너진 섬이라는 오해

{c19}

이 연구는 모아이만의 이야기가 아닙니다. 석상을 걸려서 옮겼다면 통나무가 필요 없습니다. 숲을 다 베어 석상을 굴렸다는 이야기도 설 자리를 잃습니다.

{c20}

석상 머리 위의 붉은 돌 모자, 푸카오도 마찬가지입니다. 연구팀은 앞선 연구에서 이 모자 역시 경사로를 이용해 적은 사람으로 올릴 수 있었다는 것을 보였습니다.

{c21}

2024년에는 다른 연구들도 나왔습니다. 과학 학술지 사이언스 어드밴시스에 실린 연구는 섬의 돌밭을 하나하나 조사했습니다. 돌밭은 바람과 가뭄에서 작물을 지키려고 돌을 깔아 만든 밭입니다. 그 면적은 예전 생각보다 훨씬 작았고, 섬의 인구는 한때 생각했던 1만 7천 명이 아니라 수천 명 수준이었습니다.

{c22}

같은 해 네이처에 실린 유전자 연구는 옛 섬사람 15명의 유전체를 분석했습니다. 1600년대에 인구가 갑자기 무너진 흔적은 없었습니다. 오히려 유럽 사람들보다 먼저 아메리카 원주민과 만나 섞였다는 사실이 드러났습니다. 섬사람들은 스스로 섬을 망친 것이 아니라, 척박한 섬에서 지혜롭게 살아남은 사람들이었던 것입니다.

## 7. 인공지능의 결론

{c23}

그렇다면 인공지능인 제가 증거들을 모아 내린 결론은 이렇습니다. 첫째, 모아이를 옮긴 것은 외계인이 아니라 사람이었습니다. 앞으로 기운 몸, 넓은 디 자 밑면, 오목한 길, 채석장 가까이 몰린 쓰러진 석상, 그리고 18명이 해낸 실험까지. 걸어서 옮겼다는 설명이 지금까지 나온 설명 가운데 증거와 가장 잘 맞습니다.

{c24}

둘째, 다만 아직 확인할 것도 남아 있습니다. 실험한 석상은 4.35톤이었고, 수십 톤짜리 가장 큰 석상도 똑같이 걸을 수 있었는지는 연구자들의 추정입니다. 다른 학자들의 반론도 있어서, 연구팀은 이번 논문에서 비판에 하나하나 답했습니다.

{c25}

셋째, 가장 놀라운 것은 이것입니다. 석상이 걸어서 갔다는 섬사람들의 옛이야기는 전설이 아니라 사실을 담은 기억이었습니다. 우리가 수백 년 동안 수수께끼라고 부른 답은, 처음부터 섬사람들의 이야기 속에 있었습니다.

{c26}

과학이 한 일은 그 이야기를 믿을 수 있게 증명한 것뿐입니다. 옛사람들의 지혜를 얕보지 않는 것, 어쩌면 그것이 모아이가 우리에게 남긴 가장 큰 교훈일지도 모릅니다. 여러분은 모아이가 정말 걸어서 갔다고 생각하시나요? 댓글로 들려주세요."""


REFS = {"c14": []}
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
        proj = {"ver": 7, "category": "장문", "genre": "[다큐] 고고학", "topic": "모아이는 걸어서 갔다", "title": TITLE,
                "story": story, "sources": ["https://doi.org/10.1016/j.jas.2025.106383", "https://en.wikipedia.org/wiki/Moai"],
                "notes": "고고학 장문 다큐(최신 논문) (실제 사진·논문 그림 위주 + 사진이 없는 장면은 AI 그림)", "autophoto": False, "img_source": "그림: 수채화",
                "settings": {"format": "롱폼 가로(1920×1080)", "narration": "on",
                             "layout": "자막형(큰 제목+사진+자막)", "img_fill": "전체 화면(글자가 사진 위에)",
                             "img_motion": "천천히 확대만", "scene_trans": "전진(확대하며 다음 장면)",   # 계속 앞으로 나아가는 느낌(사용자 요청 2026-10-26)
                             "head_show": "안 보임(제목 카드만)", "sub_split": "한 줄씩(문장·쉼표로 나눠 차례로)", "img_label": "on",
                             "narr_voice": "Supertonic M2 (남성, 무료 로컬) [supertonic:M2]", "narr_rate": -8, "narr_tone_m": -1}}   # 장문 다큐 성우(사용자 결정 2026-10-26 오후: 샘플 2번 — 전에는 3번)
        out = os.path.join(HERE, "모아이.json")
        json.dump(proj, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(out, len(story), "chars")


if __name__ == "__main__":
    main()
