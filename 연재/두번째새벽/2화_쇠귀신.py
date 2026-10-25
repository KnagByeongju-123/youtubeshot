"""《두 번째 새벽》 2화 '쇠귀신' — 대본 + 컷별 그림 계획
python 연재/두번째새벽/2화_쇠귀신.py job <저장폴더> [애니] [c01,c06,...]   → 그림 주문서(klein_worker 용) job.json
  (애니 = 애니 일러스트 화풍 + 캐릭터시트_애니, 컷번호를 적으면 그 컷만)
python 연재/두번째새벽/2화_쇠귀신.py project <그림폴더> [애니] → 프로젝트 파일(render_project 용) 연재/두번째새벽/2화_쇠귀신.json
대본의 {컷번호} 자리에 그 컷 그림이 들어감. chars = 그 컷에 나오는 인물(캐릭터 시트를 기준 그림으로 넣음)"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TITLE = "두 번째 새벽 2화 - 쇠귀신"

# 대사 → 말하는 인물 (그 인물 목소리로 읽음, 목소리는 등장인물.json 의 voice)
DIALOGUE = [
    ("정비 대상... 확인.", "아홉"),
    ("너... 나를 고치는 거야?", "한별"),
    ("손상. 왼쪽 발목. 정비를 시작합니다.", "아홉"),
    ("아홉. 네 이름은 이제 아홉이야.", "한별"),
    ("아버지, 착륙선에 누가 숨어 탔어요. 기관실 아이예요.", "서린"),
    ("날이 밝으면 그 지하로 간다. 움직이는 쇠는 모조리 부숴라.", "강무진 경"),
    ("위험. 숲. 보호.", "아홉"),
    ("이 로봇들은... 누군가를 기다리다 잠든 것 같아요.", "서린"),
    ("괜찮아. 이번엔 내가 고쳐 줄게.", "한별"),
    ("어머니... 신호... 없음.", "아홉"),
    ("쇠귀신과 함께 다니는 인간이라니.", "카룬"),
]

# (컷번호, 나오는 인물, 그림 설명(영어), 화면 설명(한국어))
CUTS = [
    ("c01", ["한별", "아홉"], "in a dark underground hall full of broken robots, the tall skull-faced robot with one glowing blue eye bending over the frightened girl lying on the floor, a dropped hand lamp beside her", "한별에게 손을 뻗은 쇠귀신"),
    ("c02", [], "a column of blue light rising from the ruins of an overgrown city at dusk, seen from far away across a dark forest", "폐허에서 솟은 파란 빛기둥"),
    ("c03", ["카룬"], "the chimpanzee warrior standing on a broken highway bridge at dusk, seen from behind, holding his staff, watching a distant blue light over the ruins", "빛을 바라보는 숲의 전사"),
    ("c04", ["한별", "아홉"], "the tall robot kneeling and gently touching the girl's ankle with its long thin metal fingers, the girl flinching with her eyes squeezed shut, lamp light on the floor", "한별의 발목에 닿은 쇠 손가락"),
    ("c05", ["한별"], "close-up of the girl lying on a dusty floor slowly opening one eye, tears on her cheeks, confused and scared, soft blue light on her face", "살며시 눈을 뜬 한별"),
    ("c06", ["아홉"], "the robot kneeling in the dark, its single blue eye casting a soft scanning beam of light downward, moss on its shoulders", "파란 눈으로 살피는 로봇"),
    ("c07", ["한별"], "the girl sitting on the floor holding her swollen left ankle with both hands, wincing in pain, her goggles fallen beside her", "발목을 다친 한별"),
    ("c08", ["아홉"], "close-up of the robot's forearm opening like a rusty toolbox, tiny old tools unfolding from its long fingers, sparks of dust", "팔 속에서 나온 작은 공구들"),
    ("c09", ["한별", "아홉"], "the robot carefully splinting the girl's ankle with thin metal strips and strips of cloth, the girl sitting and watching in amazement", "다리를 정비해 주는 로봇"),
    ("c10", ["한별"], "the girl leaning close with her lamp, tracing faded old engraved symbols on a rusted metal chest plate with her finger, fascinated", "로봇 가슴판의 옛 글자"),
    ("c11", ["아홉"], "close-up of the robot's skull-like face tilted to one side, its blue eye flickering, the other eye socket broken and dark, curious", "고개를 갸웃하는 로봇"),
    ("c12", ["한별", "아홉"], "the girl holding out her own small wrench to the robot with a shy smile, the robot looking down at it, warm lamp light between them", "공구를 건네는 한별"),
    ("c13", [], "a night camp around a landed shuttle in a forest clearing among ruins, a wooden palisade, campfires and torches, knights on guard", "착륙선 둘레의 밤 야영지"),
    ("c14", ["서린"], "the priestess kneeling beside an opened empty wooden crate in a shuttle cargo hold at night, holding a small oily rag, surprised", "빈 상자를 찾은 서린"),
    ("c15", ["서린", "강무진 경"], "the priestess speaking urgently to the knight commander beside a campfire at night, he frowns with his arms crossed", "아버지에게 알리는 서린"),
    ("c16", ["강무진 경"], "the knight commander pointing at an old paper map on a wooden table in a tent, candlelight, his face hard", "지도를 짚는 강무진"),
    ("c17", ["한별", "아홉"], "the tall robot carrying the girl on its back, climbing up dark broken stairs toward moonlight at the top", "한별을 업고 계단을 오르는 로봇"),
    ("c18", [], "an overgrown ruined city at night under a huge full moon, vines on collapsed towers, fireflies drifting over the street", "달빛 아래 폐허 도시"),
    ("c19", ["한별", "아홉"], "the girl sitting on the tall robot's shoulder as it walks through moonlit ruins, she points at the stars with a small smile", "로봇의 어깨에 탄 한별"),
    ("c20", ["아홉"], "the robot stopping in a moonlit street and gently touching the head of an old fallen robot half-buried in grass", "쓰러진 로봇 앞에 멈춘 아홉"),
    ("c21", [], "a faded cracked old painted mural on a ruined wall showing a friendly robot holding hands with a small child, vines over it, moonlight", "벽에 남은 옛 그림"),
    ("c22", ["카룬"], "the chimpanzee warrior crouching on a high tree branch in moonlight, holding his staff, amber eyes narrowed, watching something below", "나무 위에서 지켜보는 카룬"),
    ("c23", [], "warning totems at a dark forest edge, broken robot heads and rusty metal parts hanging from ropes on wooden poles, moonlight and mist", "숲 가장자리의 경고 표식"),
    ("c24", ["한별", "아홉"], "the tall robot suddenly stepping in front of the girl and shielding her with one long arm, looking up at the dark trees, the girl behind it", "한별을 막아서는 아홉"),
    ("c25", ["아홉"], "close-up of the robot's shoulder plate covered with old dents and scratches, a broken stone spear tip stuck in the rusted metal", "어깨에 박힌 오래된 창끝"),
    ("c26", ["강무진 경"], "the knight commander leading knights with torches down broken stairs into a dark underground hall, swords drawn", "지하로 내려가는 기사들"),
    ("c27", [], "knights in armor smashing old broken robots with war hammers in a dark underground hall, sparks flying in torchlight", "로봇을 부수는 기사들"),
    ("c28", ["서린"], "the priestess in a dark underground hall picking up a small dropped hand lamp from the floor, worried, torchlight behind her", "한별의 등불을 주운 서린"),
    ("c29", ["서린"], "the priestess kneeling and touching the mossy hand of a broken robot, hesitant, doubt on her gentle face", "로봇의 손을 만지는 서린"),
    ("c30", ["한별", "아홉"], "inside an abandoned old workshop at night, the girl repairing the robot's broken face with small tools by lamplight, the robot sitting still", "아홉을 고쳐 주는 한별"),
    ("c31", ["아홉"], "a faint blue hologram projected from the robot's single eye in a dark workshop, showing a gigantic ruined tower with a dark sphere at its top", "아홉의 눈이 비춘 옛 탑"),
    ("c32", ["한별"], "the girl's face lit by soft blue hologram light in the dark, eyes wide with awe", "푸른 빛을 바라보는 한별"),
    ("c33", ["한별", "아홉"], "dawn light through a broken window, the girl asleep under her cloak on a workbench, the tall robot sitting on guard by the doorway", "잠든 한별을 지키는 아홉"),
    ("c34", ["카룬"], "the chimpanzee warrior stepping out of morning mist among ruins, pointing his staff forward, fierce amber eyes", "안개 속에서 나타난 카룬"),
    ("c35", ["강무진 경"], "the knight commander on a hill at dawn looking over the ruined city, gripping his sword hilt, his red cape blowing", "새벽 언덕의 강무진"),
    ("c36", [], "dawn over a vast forest swallowing a ruined city, a red banner on one hill, a tribal totem on another, a tall robot silhouette in between", "세 갈래 길 위의 새벽"),
]

STORY = """{c01}

숲속 사람들은 그것을 쇠귀신이라 불렀습니다. 수백 년 동안 수많은 생명을 앗아 간 무서운 기계였죠. 그런데 그 쇠귀신이, 열일곱 살 소녀 앞에 무릎을 꿇었습니다.

{c02}

지난 이야기. 방주선 정비공 견습 한별은 몰래 착륙선을 타고 지구로 내려왔습니다. 그리고 폐허 깊은 지하, 로봇들의 무덤에서 해골 얼굴의 로봇을 깨우고 말았습니다.

{c03}

그날 밤, 폐허에서 솟은 파란 빛을 본 것은 인간들만이 아니었습니다. 무너진 다리 위에서, 누군가 그 빛을 오래도록 지켜보고 있었습니다.

끝까지 보시면, 그 로봇이 왜 한별을 해치지 않았는지 알게 되실 겁니다.

## 1. 쇠 손가락

{c04}

차가운 쇠 손가락이 한별의 발목에 닿았습니다. 한별은 눈을 질끈 감았습니다. 이제 끝이라고 생각했습니다.

{c05}

그런데 아무 일도 일어나지 않았습니다. 한별은 살며시 한쪽 눈을 떴습니다. 로봇은 한별을 해치지 않았습니다. 그저 가만히, 한별의 다리를 내려다보고 있었습니다.

{c06}

로봇의 파란 눈에서 희미한 빛줄기가 흘러나왔습니다. 빛은 한별의 다리를 천천히 훑었습니다. 그리고 낮게 갈라진 목소리가 울렸습니다.

"정비 대상... 확인."

{c07}

그제야 한별은 통증을 느꼈습니다. 넘어지면서 왼쪽 발목을 접질린 것이었습니다. 발목은 벌써 퉁퉁 부어 있었습니다. 이대로는 걸을 수 없었습니다. 그런데 곧, 로봇은 아무도 예상하지 못한 일을 시작합니다.

## 2. 정비 명령

{c08}

로봇의 팔뚝이 낡은 공구함처럼 열렸습니다. 길고 가는 손가락 끝에서 작은 공구들이 하나둘 펼쳐졌습니다. 기관실에서 보던 것과 똑같은 공구들이었습니다.

"너... 나를 고치는 거야?"

"손상. 왼쪽 발목. 정비를 시작합니다."

{c09}

로봇은 얇은 쇠판과 천 조각으로 한별의 발목을 단단히 감쌌습니다. 손길은 놀랄 만큼 조심스러웠습니다. 기관실의 늙은 정비사들처럼요. 한별은 아픔도 잊고 그 손을 바라보았습니다.

정화교 사제들은 말했습니다. 생각하는 쇠는 사람을 해치려고만 한다고. 그런데 지금 이 쇠는, 다친 사람을 고치고 있었습니다. 한별은 머릿속이 어지러웠습니다. 어른들이 말해 준 것 가운데, 대체 무엇이 진짜였을까요?

{c10}

한별은 등불을 들어 로봇의 가슴판을 비춰 보았습니다. 바랜 숫자 9 아래로 옛 글자가 새겨져 있었습니다. 이불 속에서 몰래 읽던, 그 글자였습니다. 한별은 손가락으로 한 자씩 더듬었습니다. 정비. 보조. 아홉 번째.

{c11}

로봇이 고개를 갸웃했습니다. 깨진 눈구멍 옆에서 파란 외눈이 깜빡였습니다. 무섭기만 하던 해골 얼굴이, 이상하게도 조금은 어리둥절해 보였습니다.

{c12}

한별은 허리춤에서 자기 렌치를 꺼내 내밀었습니다. 정비공끼리의 인사였습니다.

"아홉. 네 이름은 이제 아홉이야."

로봇은 한참 동안 렌치를 내려다보았습니다. 수백 년 만에 처음 불린 이름이었습니다. 한편 그 시각, 착륙선에서는 한 사람이 한별의 흔적을 찾아냅니다.

## 3. 착륙 기지의 밤

{c13}

착륙선 둘레에는 나무 울타리가 세워졌습니다. 기사들은 모닥불을 피우고 밤새 숲을 노려보았습니다. 낮에 본 호박색 눈들이 아직 그 어둠 어딘가에 있었습니다.

{c14}

서린은 약초를 챙기러 화물칸에 들렀다가 이상한 것을 발견했습니다. 뚜껑이 열린 빈 상자. 그 안에 기름 묻은 걸레 한 장. 방주선 기관실에서만 쓰는 걸레였습니다.

{c15}

서린은 곧장 아버지에게 달려갔습니다.

"아버지, 착륙선에 누가 숨어 탔어요. 기관실 아이예요."

강무진 경의 얼굴이 어두워졌습니다. 아이 하나가 저 숲 어딘가를 헤매고 있다는 뜻이었습니다. 그리고 그 숲에는, 파란 빛을 뿜은 무언가가 있었습니다.

강무진에게 로봇은 그저 기계가 아니었습니다. 수십 년 전 첫 정찰 때, 그는 지구에서 쇠로 된 괴물에게 동료들을 잃었습니다. 혼자 살아 돌아온 그날부터, 그의 왼뺨에는 지워지지 않는 흉터가 남았습니다.

{c16}

강무진은 낡은 지도 위의 폐허 한가운데를 손가락으로 짚었습니다.

"날이 밝으면 그 지하로 간다. 움직이는 쇠는 모조리 부숴라."

기사들은 대답 없이 고개를 숙였습니다. 하지만 그 시각, 한별과 아홉은 이미 무덤을 떠나고 있었습니다.

## 4. 달빛 아래 폐허

{c17}

아홉은 한별을 등에 업고 무너진 계단을 올랐습니다. 쇠 무릎이 삐걱일 때마다 이끼가 떨어졌습니다. 계단 끝에서 달빛이 쏟아졌습니다.

{c18}

밤의 폐허는 낮과 전혀 달랐습니다. 커다란 달 아래, 덩굴에 덮인 탑들이 은빛으로 빛났습니다. 반딧불이가 무너진 거리 위를 떠다녔습니다.

{c19}

한별은 아홉의 어깨 위에 앉아 하늘을 올려다보았습니다. 방주선 창문으로 보던 별들이, 이제는 머리 위 가득 쏟아지고 있었습니다. 무서운 쇠귀신의 어깨 위에서, 한별은 처음으로 웃었습니다.

{c20}

그때 아홉이 걸음을 멈췄습니다. 풀숲에 반쯤 묻힌, 쓰러진 로봇 앞이었습니다. 아홉은 긴 손가락으로 그 로봇의 머리를 가만히 쓰다듬었습니다. 마치 오래된 동료에게 인사하듯이요.

{c21}

그 옆 무너진 벽에는 빛바랜 그림 하나가 남아 있었습니다. 로봇과 어린아이가 손을 잡고 웃는 그림. 한별은 그 앞에서 한참을 서 있었습니다. 옛날에는, 정말 이랬던 걸까요? 그런데 바로 다음 순간, 숲이 움직이기 시작합니다.

## 5. 쇠귀신

{c22}

높은 나뭇가지 위에서 호박색 눈 한 쌍이 그들을 내려다보고 있었습니다. 나무껍질 갑옷을 입고, 구리선을 감은 지팡이를 쥔 젊은 전사였습니다.

{c23}

숲 가장자리에는 기묘한 표식들이 서 있었습니다. 부서진 로봇의 머리와 녹슨 쇳조각들이 밧줄에 매달려 흔들렸습니다. 이 숲의 주인들이 남긴 경고였습니다. 쇠귀신은 들어오지 말라.

{c24}

아홉이 갑자기 한별 앞을 막아섰습니다. 긴 팔을 펼쳐 한별을 뒤로 감쌌습니다. 파란 외눈이 어두운 나무들을 노려보았습니다.

"위험. 숲. 보호."

{c25}

그제야 한별은 보았습니다. 아홉의 어깨에 박힌 오래된 돌 창끝을. 몸 곳곳의 찌그러진 자국들을. 아홉은 수백 년 동안, 이 숲과 싸워 온 것이었습니다.

나무 위의 전사는 창 대신 지팡이를 꽉 쥐었습니다. 그의 부족에게 쇠귀신은 아이들을 해친 괴물이었습니다. 그런데 그 괴물이 인간 아이를 감싸고 있었습니다. 전사는 아무 소리도 내지 않고 어둠 속으로 사라졌습니다. 이어서, 날이 밝은 로봇 무덤으로 가 보겠습니다.

## 6. 정화의 칼

{c26}

새벽이 오기도 전에 강무진 경과 기사들이 횃불을 들고 지하로 내려갔습니다. 칼날에 횃불이 번득였습니다.

{c27}

기사들은 쓰러진 로봇들을 하나씩 망치로 내리쳤습니다. 생각하는 쇠는 죄. 정화교의 가르침이었습니다. 쇳조각이 튈 때마다 지하가 울렸습니다.

{c28}

뒤따라온 서린은 바닥에서 작은 손등불 하나를 주웠습니다. 방주선 기관실의 등불이었습니다. 아이는 분명 여기에 있었습니다. 하지만 지금은 보이지 않았습니다.

{c29}

서린은 망치를 피해 쓰러진 로봇 하나 앞에 무릎을 꿇었습니다. 이끼 덮인 쇠 손을 가만히 만져 보았습니다. 차갑고, 조용했습니다.

"이 로봇들은... 누군가를 기다리다 잠든 것 같아요."

기사 하나가 서린을 이상하다는 듯 쳐다보았습니다. 서린은 입을 다물었습니다. 하지만 마음속 질문은 사라지지 않았습니다. 잠시 뒤, 아홉의 눈이 숨겨 온 기억을 보여 줍니다.

## 7. 숫자 9의 기억

{c30}

한별과 아홉은 버려진 옛 작업장에 몸을 숨겼습니다. 한별은 등불 아래서 아홉의 깨진 얼굴을 들여다보았습니다. 녹슨 나사, 끊어진 전선. 기관실에서 매일 고치던 것들이었습니다.

"괜찮아. 이번엔 내가 고쳐 줄게."

{c31}

끊어진 전선 하나를 이어 붙인 순간, 아홉의 외눈에서 푸른 빛이 퍼져 나왔습니다. 빛은 허공에 그림을 그렸습니다. 하늘을 찌를 듯 거대한 탑. 그리고 그 꼭대기의 검은 공.

"어머니... 신호... 없음."

{c32}

한별은 숨을 삼켰습니다. 어머니. 로봇에게 어머니가 있다니. 아홉은 수백 년 동안, 끊어진 신호를 기다리며 마지막 명령만 지켜 온 것이었습니다. 고장 난 것을 고쳐라. 한별이 배운 것과 똑같은 명령을요.

한별은 아홉의 차가운 손을 꼭 잡았습니다. 방주선에서 한별은 늘 혼자였습니다. 부모도 없이, 기관실의 쇳소리만 듣고 자랐습니다. 그런데 이 낯선 땅에서, 자기와 똑같이 혼자 남겨진 존재를 만난 것이었습니다. 그리고 곧, 새벽이 세 갈래의 그림자를 데려옵니다.

## 8. 세 갈래의 새벽

{c33}

창밖이 밝아 올 무렵, 한별은 망토를 덮고 작업대 위에서 잠이 들었습니다. 아홉은 문 앞에 앉아 밤새 그 곁을 지켰습니다. 정비 대상을 지키는 것도, 정비였으니까요.

{c34}

그때 새벽 안개 속에서 한 그림자가 걸어 나왔습니다. 호박색 눈의 젊은 전사였습니다. 그는 지팡이 끝으로 작업장을 겨누었습니다.

"쇠귀신과 함께 다니는 인간이라니."

{c35}

같은 시각, 언덕 위의 강무진 경은 폐허를 내려다보며 칼자루를 움켜쥐었습니다. 기사들의 횃불이 작업장 쪽으로 움직이기 시작했습니다.

{c36}

수백 년 만의 두 번째 새벽. 하늘에서 온 인간, 숲의 전사, 그리고 쇠귀신. 그 한가운데에, 열일곱 살 정비공 한별이 잠들어 있었습니다.

아홉은 왜 한별을 지켰을까요? 그것이 명령이었을까요, 아니면 다른 무언가였을까요? 《두 번째 새벽》은 이 채널에서 매화 계속 이어집니다.

다음 이야기, 3화 숲의 눈. 숲의 전사는 한별을 적으로 볼까요?"""


def main():
    cmd, folder = sys.argv[1], sys.argv[2]
    anime = len(sys.argv) > 3 and sys.argv[3] == "애니"
    chars = {c["name"]: c for c in json.load(open(os.path.join(HERE, "등장인물.json"), encoding="utf-8"))["chars"]}
    src = open(os.path.join(HERE, "..", "..", "shorts_novel_maker_supertonic.py"), encoding="utf-8").read()
    style_name = "애니 일러스트\\(요즘\\)" if anime else "옛날 만화책\\(세피아 펜화\\)"
    style = re.search(f'"{style_name}": "([^"]+)"', src).group(1)
    face, kind = ("face_anime", "anime illustration") if anime else ("face", "comic panel")
    only = sys.argv[4].split(",") if len(sys.argv) > 4 else None
    # 애니 화풍 설명의 눈·볼·머리카락 말 때문에 인물 없는 장면에 엉뚱한 소녀 얼굴이 크게 나옴 → 풍경 장면은 그 말을 빼고 배경 그림으로
    scenery = re.sub(r"large detailed glossy eyes[^,]*, soft blush on cheeks, very fine detailed flowing hair strands with soft shading, ", "", style)
    scenery = scenery.replace("dreamy shallow depth of field with bokeh light particles, soft diffused lighting, delicate pastel color grading",
                              "rich saturated colors, strong contrast, dramatic cinematic lighting that matches the mood of the scene")
    no_face = ("Anime background art, environment and scenery illustration. No main character, no close-up face, no portrait, no girl in the foreground; "
               "any people are small figures in the scene. ")
    if cmd == "job":
        items = []
        for cid, who, desc, _ in CUTS:
            if only and cid not in only:
                continue
            looks = "; ".join(f"{nm} (the character from reference image {k + 1}): {chars[nm]['look']}" for k, nm in enumerate(who))
            items.append({"id": cid, "width": 1024, "height": 576, "seed": 100 + int(cid[1:]),
                          "refs": [os.path.join(HERE, chars[nm][face]) for nm in who],
                          "prompt": f"{style if (who or not anime) else scenery}, medieval post-apocalyptic science fantasy {kind}. "
                                    + (f"Characters: {looks}. Each person has exactly two arms and two legs. Only these characters, no other copies of them. " if looks
                                       else no_face if anime else "")
                                    + f"Scene: {desc}. Cinematic composition, full-bleed image, no border, no frame, no paper edges. No speech bubbles, no text, no letters."})
        os.makedirs(folder, exist_ok=True)
        json.dump({"items": items}, open(os.path.join(folder, "job.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(len(items), "cuts")
    elif cmd == "project":
        story = STORY
        for cid, _, _, cap in CUTS:
            img = next((os.path.join(folder, cid + e) for e in (".png", ".jpg") if os.path.exists(os.path.join(folder, cid + e))), os.path.join(folder, cid + ".png"))
            story = story.replace("{" + cid + "}", f"[사진: {img} | {cap} | AI 생성 그림 (FLUX.2 klein) | ]")
        proj = {"ver": 7, "category": "장문", "genre": "[이야기] SF·디스토피아", "topic": "두 번째 새벽", "title": TITLE,
                "story": story, "sources": [], "notes": "창작 연재 《두 번째 새벽》 2화", "autophoto": False, "img_source": "그림: 애니 일러스트" if anime else "그림: 옛날 만화책",
                "cast": [{"name": nm, "look": c["look"], "look_ko": c["look_ko"], "voice": c.get("voice"),
                          **({"sheet": os.path.join(HERE, c[face])} if c.get(face) else {})} for nm, c in chars.items()],
                "dialogue": [{"text": t, "who": w} for t, w in DIALOGUE],
                "settings": {"format": "롱폼 가로(1920×1080)", "narration": "on",   # 새 서버 기본값(나레이션 꺼짐·스크롤형) 대신
                             "layout": "자막형(큰 제목+사진+자막)", "img_fill": "전체 화면(글자가 사진 위에)",
                             "img_motion": "영상처럼(확대·이동·전환)",
                             "head_show": "안 보임(제목 카드만)", "sub_split": "한 줄씩(문장·쉼표로 나눠 차례로)", "img_label": "off",   # 연재 화면 규칙
                             "narr_voice": "Supertonic M2 (남성, 무료 로컬) [supertonic:M2]"}}
        out = os.path.join(HERE, "2화_쇠귀신.json")
        json.dump(proj, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(out, len(story), "chars")


if __name__ == "__main__":
    main()
