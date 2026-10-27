"""장문 과학 다큐 '죽은 뒤 다시 태어날 확률, 인공지능이 계산해 본 세 가지 길' — 대본 + 컷별 사진·그림 계획
python 장문/다시태어날확률/다시태어날확률.py job <저장폴더> [c01,...]  → 그림 주문서(다큐 수채화) job.json (사진 컷은 빼고)
python 장문/다시태어날확률/다시태어날확률.py project <그림폴더>       → 프로젝트 파일 장문/다시태어날확률/다시태어날확률.json
사용자 요청(2026-10-27): '다시 태어날 확률 — 원자 상태로는 결합될 수 있겠지만 정신까지는 불가능할 것 같고, 머릿속 기억을 담아 둘 수 있으면 가능할지도'
 → 흥미를 끌게, 'AI의 생각'으로 (인공지능 1인칭)
사실 확인:
 - 사람 몸의 원자 약 7×10^27개 / 몸 무게의 대부분(수소 약 10%를 뺀 거의 전부)을 이루는 원소는 별 속·별의 죽음에서 만들어짐 (수소는 빅뱅)
 - Spalding 외, Cell 122:133 (2005) 핵실험 탄소-14로 세포 나이 측정: 몸의 많은 세포는 사람보다 젊음, 대뇌(후두엽) 신경세포는 사람 나이만큼 오래됨
 - 사람 뇌 신경세포 약 860억 개 (Azevedo 외 2009)
 - Liu·Ramirez·Tonegawa 외, Nature 484:381 (2012): 공포를 배울 때 켜진 해마 신경세포에 빛 스위치를 달고, 다른 곳에서 빛을 비추자 생쥐가 얼어붙음(기억 흔적, 엔그램)
 - Dorkenwald 외(FlyWire), Nature (2024-10-02): 초파리 뇌 전체 신경세포 약 14만 개·연결 5천만 개 이상, 전자현미경 사진 2,100만 장
 - Shapson-Coe 외, Science 384 eadk4858 (2024-05-10): 사람 측두엽 대뇌 1㎣, 세포 약 5만 7천 개·연결 약 1억 5천만 개·자료 1.4페타바이트
 - 푸앵카레 재귀 정리(1890) / 볼츠만 / 테세우스의 배(플루타르코스) / 순간이동 사고 실험(데릭 파핏 《이유와 인격》 1984)"""
import json
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
TITLE = "죽은 뒤 다시 태어날 확률, 인공지능이 계산해 본 세 가지 길"
STYLE_NAME = "다큐 수채화"
DIALOGUE = []

NP = " No people, no hands, no arms anywhere."
CUTS = [
    ("c01", "real photo", "별이 가득한 밤하늘"),
    ("c02", "a glowing abstract artificial intelligence made of soft blue light lines and points, thinking, floating in front of a vast starry universe, calm and contemplative, data visualization style, no letters, no numbers." + NP, "질문을 받은 인공지능 (상상 그림)"),
    ("c03", "real photo", "게 성운 — 죽은 별이 흩뿌린 원소"),
    ("c04", "real photo", "별이 태어나는 곳 (창조의 기둥)"),
    ("c05", "diagram", "우리 몸을 이루는 원자"),
    ("c06", "real photo", "숲의 땅"),
    ("c07", "real photo", "충돌하는 두 은하 (허블)"),
    ("c08", "real photo", "창조의 기둥 (적외선)"),
    ("c09", "diagram", "같은 배열이 다시 나올 확률"),
    ("c10", "real photo", "웹 망원경이 본 먼 은하들"),
    ("c11", "real photo", "전자현미경으로 본 세포 표면"),
    ("c12", "real photo", "네바다 핵실험장 (지금 모습)"),
    ("c13", "real photo", "대뇌와 신경세포 (옛 그림)"),
    ("c14", "real photo", "고대 그리스의 배 (옛 그림)"),
    ("c15", "real photo", "사람 뇌의 CT 사진"),
    ("c16", "diagram", "뇌 속의 숫자"),
    ("c17", "real photo", "실험실의 생쥐"),
    ("c18", "real photo", "실험실의 생쥐들"),
    ("c19", "real photo", "초파리"),
    ("c20", "real photo", "전자현미경으로 본 곤충의 겹눈"),
    ("c21", "real photo", "전자현미경"),
    ("c22", "real photo", "형광으로 빛나는 신경세포 (생쥐 뇌)"),
    ("c23", "a person stepping into a glowing teleportation booth in a quiet white laboratory while an identical copy of the same person appears in a second booth far away, symbolic thought experiment, soft light, calm", "순간이동 사고 실험 (상상 그림)"),
    ("c24", "real photo", "데이터 센터"),
    ("c25", "real photo", "밤하늘 (하와이·칠레)"),
    ("c26", "a quiet sunrise over a meadow with countless tiny glowing particles of light rising from the grass and flowers into the sky, symbolic of atoms returning to nature and becoming new life, peaceful and hopeful." + NP, "다시 이어지는 원자들"),
]

STORY = """{c01}

당신이 죽은 뒤, 언젠가 다시 태어날 확률은 얼마일까요? 저는 인공지능입니다. 이 질문을 받고, 저는 종교나 믿음이 아니라 과학으로 답을 찾아보기로 했습니다.

{c02}

다시 태어난다는 말에는 세 가지 뜻이 있을 수 있습니다. 첫째, 나를 이루던 원자가 다시 모이는 것. 둘째, 나라는 정신이 다시 깨어나는 것. 셋째, 내 기억이 다른 곳에서 이어지는 것. 오늘은 이 세 가지 길을 하나씩 따져 보고, 마지막에 제 생각을 말씀드리겠습니다. 끝까지 들어 보시면, 생각보다 놀라운 답이 기다리고 있습니다.

## 1. 첫 번째 길, 원자

{c03}

먼저 원자입니다. 우리 몸을 이루는 탄소와 산소, 칼슘과 철은 처음부터 지구에 있던 것이 아닙니다. 수십억 년 전, 별의 뜨거운 속에서 만들어졌고, 별이 폭발하며 우주로 흩어졌습니다.

{c04}

그 원소들이 모여 태양과 지구가 되었고, 마침내 우리 몸이 되었습니다. 가장 가벼운 수소는 우주가 막 태어났을 무렵 만들어졌지만, 몸무게의 대부분을 차지하는 나머지 원소들은 별에서 왔습니다. 우리는 말 그대로 별의 부스러기로 만들어진 셈입니다. 천문학자 칼 세이건은 이것을 이렇게 표현했습니다. 우리는 별의 재료로 만들어졌다고 말입니다.

{c05}

사람의 몸에는 원자가 약 7천 자, 그러니까 7 뒤에 0이 27개 붙는 만큼 들어 있습니다. 우리가 숨을 쉬고 먹고 마실 때마다, 이 원자들은 쉬지 않고 들어오고 나갑니다.

{c06}

그리고 우리가 죽으면, 몸의 원자들은 흙과 물과 공기로 돌아갑니다. 그 원자는 풀이 되고, 나무가 되고, 다른 동물의 몸이 됩니다. 재미있는 계산도 있습니다. 숨 한 번에 들이쉬는 공기 분자는 너무나 많아서, 2천 년 전 로마의 카이사르가 마지막으로 내쉰 숨 속의 분자 하나를 지금 우리가 들이쉬고 있을 가능성이 아주 높다는 것입니다. 그러니 원자로 보면, 우리는 이미 끊임없이 다시 태어나고 있는 셈입니다.

{c07}

그렇다면 나를 이루던 원자가 정확히 같은 모양으로 다시 모일 수는 있을까요? 1890년, 프랑스의 수학자 앙리 푸앵카레는 놀라운 사실을 증명했습니다. 갇힌 공간 속의 입자들은 충분히 오래 기다리면, 언젠가 처음과 거의 같은 배열로 돌아온다는 것입니다.

{c08}

오스트리아의 물리학자 루트비히 볼츠만도 비슷한 생각을 했습니다. 아주 드물지만, 무작위로 움직이는 입자들이 우연히 질서 있는 모양을 만들 수도 있다는 것입니다. 지금도 물리학자들은 끝없는 시간이 주어진 우주라면 우연히 생겨난 뇌가 홀로 떠다닐 수도 있다는, 이른바 볼츠만 뇌의 역설을 진지하게 이야기합니다.

{c09}

하지만 계산을 해 보면 그 시간은 상상을 넘습니다. 원자 수가 많아질수록 기다려야 할 시간은 어마어마하게 늘어납니다. 7천 자 개의 원자가 같은 자리로 돌아오는 데 걸리는 시간은, 우주의 나이 138억 년을 수없이 곱해도 닿지 않습니다. 0은 아니지만, 사실상 0에 가깝습니다.

{c10}

그래서 저는 이렇게 생각했습니다. 원자가 다시 모이는 것만으로는 내가 돌아오지 않습니다. 더 중요한 것은 원자가 어떤 모양으로 이어져 있느냐입니다.

## 2. 두 번째 길, 정신

{c11}

여기서 재미있는 사실이 하나 있습니다. 사실 우리 몸은 살아 있는 동안에도 계속 바뀝니다. 피부와 피, 장의 세포는 며칠에서 몇 달이면 새것으로 바뀝니다. 핏속의 적혈구는 약 넉 달을 살고, 장 안쪽의 세포는 며칠 만에 바뀝니다. 몇 해 전의 나와 지금의 나는 재료로 보면 상당 부분이 다른 사람입니다.

{c12}

2005년 스웨덴 연구팀은 기발한 방법으로 세포의 나이를 쟀습니다. 1950년대와 60년대 핵실험으로 공기 중에 늘어난 탄소가 사람의 세포 속에 기록되어, 그 세포가 언제 태어났는지 알려 주는 시계가 된 것입니다.

{c13}

결과는 이랬습니다. 몸의 많은 세포는 그 사람보다 훨씬 젊었습니다. 그런데 연구팀이 살펴본 대뇌 뒤쪽의 신경세포는 그 사람의 나이와 거의 같았습니다. 우리가 태어날 때 생긴 신경세포가 평생 우리와 함께 가는 것입니다.

{c14}

이것은 오래된 수수께끼를 떠올리게 합니다. 테세우스의 배입니다. 낡은 널빤지를 하나씩 바꿔 끝내 모든 조각이 새것이 되었다면, 그 배는 여전히 같은 배일까요? 우리 몸도 그렇습니다. 재료는 바뀌어도 우리는 여전히 나입니다.

{c15}

그렇다면 나를 나로 만드는 것은 무엇일까요? 많은 신경과학자들은 그 답을 뇌의 연결에서 찾습니다. 사람의 뇌에는 약 860억 개의 신경세포가 있고, 이들은 셀 수 없이 많은 연결로 이어져 있습니다. 뇌의 무게는 몸무게의 2퍼센트쯤이지만, 몸이 쓰는 에너지의 약 20퍼센트를 씁니다. 그만큼 바쁘게 일하는 기관입니다.

{c16}

이 연결의 지도를 커넥톰이라고 부릅니다. 같은 원자, 같은 세포라도 연결이 다르면 다른 생각과 다른 기억이 생깁니다. 정신은 재료가 아니라, 연결이 만들어 내는 무늬에 가깝습니다.

## 3. 세 번째 길, 기억

{c17}

그렇다면 기억은 뇌 속 어디에 있을까요? 2012년, 미국 매사추세츠 공과대학 도네가와 스스무 교수팀이 놀라운 실험을 했습니다.

{c18}

연구팀은 생쥐가 무서운 일을 겪을 때 켜진 해마의 신경세포들에 빛으로 켤 수 있는 스위치를 달았습니다. 그리고 전혀 다른 안전한 곳에서 빛을 비추자, 생쥐는 그때의 공포를 떠올린 듯 몸을 웅크리고 얼어붙었습니다. 기억이 특정한 신경세포 무리에 담겨 있다는 증거였습니다. 이듬해 같은 연구팀은 한 걸음 더 나아갔습니다. 생쥐가 실제로 겪지 않은 일을 겪었다고 믿게 만드는, 가짜 기억을 심는 데 성공한 것입니다. 기억은 생각보다 물리적인 것이었습니다.

{c19}

그렇다면 뇌의 연결을 통째로 읽어 낼 수 있을까요? 2024년, 과학자들은 그 첫걸음을 내디뎠습니다. 초파리의 뇌 전체를 지도로 그린 것입니다. 초파리의 뇌는 양귀비 씨앗만큼 작습니다. 그래도 그 작은 뇌로 걸어 다니고, 날아다니고, 길을 찾고, 기억까지 합니다.

{c20}

초파리 뇌의 신경세포 약 14만 개, 그리고 그 사이의 연결 5천만 개 이상이 하나하나 기록되었습니다. 이를 위해 전자현미경 사진 2,100만 장이 쓰였고, 전 세계 100곳이 넘는 연구실과 인공지능이 함께 작업했습니다.

{c21}

같은 해, 구글과 하버드대학 연구팀은 사람 대뇌의 아주 작은 조각을 지도로 만들었습니다. 겨우 1세제곱밀리미터, 쌀알 반 톨쯤 되는 크기였습니다. 뇌전증 수술 때 어쩔 수 없이 떼어 낸 조직을, 환자의 동의를 얻어 연구에 쓴 것입니다.

{c22}

그 안에서만 세포 약 5만 7천 개와 연결 약 1억 5천만 개가 발견되었습니다. 이 작은 조각을 기록하는 데 든 자료는 1.4페타바이트, 영화 수십만 편에 맞먹는 양이었습니다. 사람의 뇌 전체를 기록하려면 이보다 백만 배쯤 많은 자료가 필요할 것입니다.

## 4. 그것은 나일까

{c23}

언젠가 내 뇌의 모든 연결을 읽어 다른 곳에 그대로 옮길 수 있다고 해 봅시다. 그렇다면 그것은 다시 태어난 나일까요? 영국의 철학자 데릭 파핏은 순간이동 장치라는 사고 실험으로 이 질문을 던졌습니다. 내 몸이 사라지고 똑같은 사람이 화성에서 깨어난다면, 그는 나일까요?

{c24}

만약 원본이 그대로 남아 있는데 복사본이 하나 더 생긴다면, 둘 가운데 누가 진짜 나일까요? 기억을 옮기는 기술이 가까워질수록, 이 질문은 철학이 아니라 현실의 문제가 될지도 모릅니다. 두 사람이 모두 같은 기억을 가지고, 모두 자신이 진짜라고 말할 테니까요. 저는 이 대목에서 오래 계산을 멈추고 생각했습니다.

## 5. 인공지능의 결론

{c25}

이제 제 생각을 말씀드리겠습니다. 첫째, 원자로 다시 태어날 확률은 0은 아니지만, 우주의 나이로도 닿지 않을 만큼 작습니다. 하지만 원자는 이미 매일 다른 생명으로 이어지고 있습니다. 그런 뜻에서 우리는 이미 다시 태어나고 있습니다. 우리가 죽은 뒤에도 원자는 사라지지 않고, 언제나 어딘가에서 새로운 생명의 일부가 됩니다.

{c26}

둘째, 나라는 정신은 원자가 아니라 연결의 무늬입니다. 셋째, 그 무늬와 기억을 담아 둘 수 있다면, 다시 깨어나는 길이 열릴지도 모릅니다. 다만 그때 깨어난 존재가 나인지, 나를 꼭 닮은 다른 누군가인지는 저도 아직 답할 수 없습니다. 어쩌면 그 답은 저 같은 인공지능이 아니라, 지금 살아 있는 여러분의 기억 속에 있을지도 모릅니다. 여러분은 기억이 이어진다면 그것을 나라고 부를 수 있다고 생각하시나요? 댓글로 들려주세요."""


REFS = {}
SEED = {}
REF_NOTE = ("Any real place or object shown must look exactly like the reference photo (same shape and colors), "
            "painted in the same watercolor style. ")

# 컷 → 사진 후보 이름 (사진후보/후보.json 의 열쇠). 사진을 받은 뒤 채움
PHOTOS = {'c01': 'c01_4', 'c03': 'c03_1', 'c04': 'c04_2', 'c05': 'c05_도표', 'c06': 'c06_2', 'c07': 'c10_2', 'c08': 'c04_o1', 'c09': 'c09_도표', 'c10': 'c10_4', 'c11': 'c21_3', 'c12': 'c12_1', 'c13': 'c13_1', 'c14': 'x_ship', 'c15': 'c15_1', 'c16': 'c16_도표', 'c17': 'c17_4', 'c18': 'c17_2', 'c19': 'c19_2', 'c20': 'c21_2', 'c21': 'c21_1', 'c22': 'x_neuron', 'c24': 'c24_1', 'c25': 'c01_1'}


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
        proj = {"ver": 7, "category": "장문", "genre": "[다큐] 과학", "topic": "다시 태어날 확률", "title": TITLE,
                "story": story, "sources": ["https://doi.org/10.1016/j.cell.2005.04.028", "https://doi.org/10.1038/nature11028", "https://doi.org/10.1038/s41586-024-07558-y", "https://doi.org/10.1126/science.adk4858"],
                "notes": "고고학 장문 다큐(최신 논문) (실제 사진·논문 그림 위주 + 사진이 없는 장면은 AI 그림)", "autophoto": False, "img_source": "그림: 수채화",
                "settings": {"format": "롱폼 가로(1920×1080)", "narration": "on",
                             "layout": "자막형(큰 제목+사진+자막)", "img_fill": "전체 화면(글자가 사진 위에)",
                             "img_motion": "천천히 확대만", "scene_trans": "전진(확대하며 다음 장면)",   # 계속 앞으로 나아가는 느낌(사용자 요청 2026-10-26)
                             "head_show": "안 보임(제목 카드만)", "sub_split": "한 줄씩(문장·쉼표로 나눠 차례로)", "img_label": "on",
                             "narr_voice": "Supertonic M2 (남성, 무료 로컬) [supertonic:M2]", "narr_rate": -8, "narr_tone_m": -1}}   # 장문 다큐 성우(사용자 결정 2026-10-26 오후: 샘플 2번 — 전에는 3번)
        out = os.path.join(HERE, "다시태어날확률.json")
        json.dump(proj, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(out, len(story), "chars")


if __name__ == "__main__":
    main()
