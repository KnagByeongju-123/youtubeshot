"""《전학 온 할머니》 1화 '교복 입은 할머니' — 대본 + 컷별 그림 계획 (사이다 연재)
python 연재/전학온할머니/1화_교복입은할머니.py job <저장폴더>   → 그림 주문서(klein_worker 용) job.json
python 연재/전학온할머니/1화_교복입은할머니.py project <그림폴더> → 프로젝트 파일(render_project 용) 연재/전학온할머니/1화_교복입은할머니.json
  영상은 render_project.py <프로젝트> --대본그대로 (오프닝·대본을 프로그램이 고쳐 쓰지 않게)
대본의 {컷번호} 자리에 그 컷 그림이 들어감. chars = 그 컷에 나오는 인물(캐릭터 시트를 기준 그림으로 넣음)
나레이션 한 명(남자 성우 2)이 대사까지 모두 읽음 (사용자 결정) → DIALOGUE 없음"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TITLE = "전학 온 할머니 1화 - 교복 입은 할머니"

# 화풍: 사용자가 보낸 캐릭터 그림(화풍샘플/사용자_캐릭터스타일.png)처럼 — 사람 비율의 깔끔한 웹툰
STYLE = ("Korean webtoon illustration, semi-realistic proportions, clean crisp black outlines, flat cel shading with soft shadows, "
         "natural muted realistic colors, detailed backgrounds, simple neat anime-style faces")

MARKET = "wearing a rubber fish-market apron over a faded purple padded vest, rubber arm sleeves and black rubber boots instead of the school uniform"

# (컷번호, 나오는 인물, 그림 설명(영어), 화면 설명(한국어)) — 인물 옷을 바꿀 땐 설명에 적음
CUTS = [
    ("c01", ["말순"], f"inside a high school classroom at lunchtime, the small elderly grandmother crouching on the floor calmly picking up spilled rice and side dishes with her bare hands, tall students standing around her in a circle, tense silence, dramatic low angle", "교실 바닥에 쏟아진 도시락을 줍는 할머니"),
    ("c02", ["태오"], "close-up of the tall arrogant high school boy holding up a smartphone to film, smirking coldly, classroom background blurred", "휴대폰으로 찍으며 비웃는 태오"),
    ("c03", ["말순"], "close-up of the elderly grandmother's face looking up, calm but with sharp wise eyes, a faint determined smile, classroom light", "고개를 드는 할머니의 눈빛"),
    ("c04", [], "a busy Korean traditional fish market at 4 a.m. before dawn, wet floor, ice boxes full of fish, yellow hanging bulbs, steam, no people in focus", "새벽 4시 생선 시장"),
    ("c05", ["말순"], f"the elderly grandmother {MARKET}, gutting a big fish on a wet wooden board at her small fish stall under a hanging bulb before dawn, cracked rough hands", "생선을 손질하는 할머니"),
    ("c06", ["말순"], "close-up of an old woman's rough cracked hands with bandaged fingertips resting on her knees, soft lamp light, realistic", "터지고 갈라진 할머니의 손"),
    ("c07", [], "faded sepia-toned style flashback memory: a poor 1960s Korean village, a thin little girl in old patched clothes carrying her baby brother on her back, looking longingly through a fence at children going into a small country school", "학교 담장 너머를 바라보던 어린 말순"),
    ("c08", ["말순"], f"the elderly grandmother {MARKET.replace(' instead of the school uniform', '')}, sitting alone at a small kitchen table at night studying with an old textbook and a pencil under a dim lamp, reading glasses on her nose", "밤마다 검정고시 공부를 하던 할머니"),
    ("c09", ["말순"], "in a small old Korean bedroom at dawn, the elderly grandmother in a plain home blouse holding a brand-new navy high school uniform blazer on a hanger against her chest in front of an old wooden wardrobe, eyes glistening, smiling", "새 교복을 가슴에 대 보는 할머니"),
    ("c10", ["말순"], "the elderly grandmother in the school uniform standing in front of an old mirror, straightening her red ribbon tie, proud shy smile, morning light", "거울 앞에서 리본을 매는 할머니"),
    ("c11", ["말순"], "wide shot: the small elderly grandmother in the school uniform walking alone through a big Korean high school front gate in the morning, many teenage students staring at her and holding up phones, cherry blossoms", "교문을 들어서는 할머니"),
    ("c12", [], "several Korean high school students in navy uniforms laughing and pointing while filming with their smartphones in front of a school gate, morning", "휴대폰으로 찍으며 웃는 학생들"),
    ("c13", ["말순"], "the elderly grandmother in the school uniform bowing politely with both hands together in front of a group of laughing students, school courtyard", "고개 숙여 인사하는 할머니"),
    ("c14", ["박 담임", "말순"], "a Korean high school classroom, the stern male teacher with silver glasses standing at the front holding a clipboard and looking coldly at the small elderly grandmother in the school uniform standing beside the teacher's desk, students seated watching", "할머니를 소개하는 차가운 박 담임"),
    ("c15", ["말순"], "the elderly grandmother in the school uniform sitting alone at the last desk in the back corner of a classroom by the window, empty desks around her, students in front whispering and glancing back", "맨 뒷자리에 혼자 앉은 할머니"),
    ("c16", ["태오"], "the tall arrogant boy with an open blazer leaning back on his chair with his feet on the desk in a classroom, surrounded by two grinning boys, looking toward the back of the room with a sneer", "뒤를 돌아보며 웃는 태오 무리"),
    ("c17", [], "close-up of a yellow sticky note stuck on an old brown cloth school bag hanging on a desk, the note has only scribbled lines and an arrow drawing, no readable letters", "할머니 가방에 붙은 쪽지"),
    ("c18", ["하린", "말순"], "the small timid girl with round glasses quietly peeling a sticky note off the elderly grandmother's cloth bag and handing it to her, the grandmother looking at the girl with a warm smile, classroom back row", "몰래 쪽지를 떼어 주는 하린"),
    ("c19", ["하린"], "the small timid girl with round glasses sitting alone at her desk in a classroom, head down, holding a small pink lunchbox in both hands, a few students in background ignoring her", "늘 혼자인 하린"),
    ("c20", [], "a Korean high school classroom at lunchtime, students eating at desks pushed together, sunlight through windows, noisy cheerful atmosphere", "점심시간의 교실"),
    ("c21", ["태오", "하린"], "the tall arrogant boy knocking a pink lunchbox off the desk of the small girl with glasses, rice and side dishes flying and spilling onto the classroom floor, the girl flinching in shock", "하린의 도시락을 엎는 태오"),
    ("c22", ["하린"], "the small girl with glasses kneeling on the classroom floor picking up spilled rice with trembling hands, tears in her eyes, shadows of tall boys standing over her", "무릎 꿇고 밥을 줍는 하린"),
    ("c23", [], "Korean high school students sitting at their desks looking away, pretending not to see, some looking at their phones, uncomfortable silence, classroom", "모른 척하는 반 아이들"),
    ("c24", ["말순", "태오"], "the small elderly grandmother in the school uniform walking toward the tall arrogant boy in the classroom aisle, the boy turning and looking down at her with a mocking smirk, height difference emphasized", "다가가는 할머니와 비웃는 태오"),
    ("c25", ["태오"], "close-up of the tall boy's left wrist with a dark bruise as he holds a smartphone, his sleeve pulled back slightly", "태오 손목의 멍"),
    ("c26", ["태오"], "the tall boy alone in a convenience store at night, standing at the window counter eating a triangle kimbap by himself, cold fluorescent light, lonely", "밤마다 편의점에서 혼자 끼니를 때우는 태오"),
    ("c27", ["말순", "하린"], "the elderly grandmother in the school uniform crouching down next to the small crying girl with glasses on the classroom floor, gently putting the spilled side dishes back into the pink lunchbox with her own hands", "손수 반찬을 주워 담는 할머니"),
    ("c28", ["말순"], "medium close-up of the elderly grandmother in the school uniform crouching on the classroom floor and looking up with a calm serious face, speaking quietly but firmly, dramatic light from the window", "조용히 입을 여는 할머니"),
    ("c29", ["태오"], "the tall arrogant boy frowning and shouting defiantly, one hand in his pocket, classroom background", "\"그래서 뭐요?\" 소리치는 태오"),
    ("c30", ["말순", "태오"], "the small elderly grandmother in the school uniform standing up straight and looking up directly into the eyes of the tall boy, the boy's mocking smile fading into shock, classroom, tense standoff", "태오를 똑바로 올려다보는 할머니"),
    ("c31", ["태오"], f"evening in a traditional fish market alley, the tall boy in his school uniform standing alone behind a stall, wiping tears from his eyes with his sleeve, warm yellow lights, nobody else around", "시장 골목에서 혼자 울던 태오"),
    ("c32", ["태오"], "close-up of the tall boy's face, eyes wide and trembling, speechless, slowly lowering his smartphone, classroom", "말을 잃은 태오"),
    ("c33", [], "a silent Korean high school classroom, all the students staring toward the back of the room in shock, frozen, sunlight", "숨죽인 교실"),
    ("c34", ["말순"], "the elderly grandmother in the school uniform holding up three fingers with a warm gentle smile, classroom", "도시락 세 개를 약속하는 할머니"),
    ("c35", ["박 담임"], "the stern male teacher with silver glasses standing in the school hallway outside the classroom door, watching through the door window, his cold face softening in surprise", "복도에서 모든 걸 지켜본 박 담임"),
    ("c36", ["박 담임", "말순"], "the stern male teacher with silver glasses bowing his head slightly to the small elderly grandmother in the school uniform in a quiet school hallway after class, the grandmother smiling kindly", "처음으로 고개를 숙이는 박 담임"),
    ("c37", [], "close-up of a crumpled note with messy handwriting scribbles (no readable letters) placed on an empty school desk next to an old brown cloth bag, soft morning sunlight", "할머니 책상 위의 서툰 쪽지"),
    ("c38", ["말순", "하린"], "morning in a classroom: the elderly grandmother in the school uniform placing three wrapped lunchboxes on her desk, the small girl with glasses beside her smiling shyly for the first time, warm sunlight", "도시락 세 개를 꺼내는 할머니"),
    ("c39", ["오정희"], "the glamorous arrogant woman in a cream tweed suit and pearl necklace slamming open the door of a school principal's office, angry face, designer handbag on her arm, dramatic", "교장실에 들이닥친 학부모회장"),
]

STORY = """{c01}

점심시간, 교실 바닥에 밥알이 흩어져 있었습니다. 그 앞에 일흔한 살 할머니가 쪼그리고 앉아, 맨손으로 반찬을 한 점 한 점 줍고 있었습니다.

{c02}

학교에서 제일 무서운 아이, 강태오는 휴대폰으로 그 모습을 찍으며 웃었습니다. 할머니는 빠지세요, 허리 다쳐요.

{c03}

그런데 할머니가 고개를 든 순간, 교실이 얼어붙었습니다. 교복을 입은 이 할머니는 대체 누구였을까요.

## 1. 칠십 년 걸린 교복

{c04}

새벽 네 시, 아직 해가 뜨려면 한참 남은 시간. 생선 시장에는 벌써 불이 켜져 있었습니다.

{c05}

김말순 할머니는 오늘도 그 자리에 있었습니다. 시장 맨 끝, 전구 하나가 달린 작은 생선 가게. 할머니는 이 자리에서 오십 년 동안 생선을 팔았습니다. 칼질 몇 번이면 고등어 한 마리가 깨끗하게 손질되었습니다. 단골들은 말순 할머니 생선이 제일 싱싱하다고 했습니다.

{c06}

얼음물에 젖고, 칼에 베이고, 찬 바람에 터진 손. 할머니의 손가락 끝에는 반창고가 마를 날이 없었습니다. 그 손으로 자식 셋을 대학에 보냈습니다. 그런데 정작 할머니는 학교 문턱을 넘어 본 적이 없었습니다.

{c07}

전쟁이 끝나고 모두가 가난하던 시절이었습니다. 어린 말순은 아홉 살에 학교를 그만두었습니다. 등에는 갓난 동생을 업고, 학교 담장 너머로 공부하는 아이들을 바라보았습니다. 종소리가 들리면 담장 밑에 쪼그려 앉아 노래를 따라 불렀습니다. 그것이 말순이 아는 학교의 전부였습니다.

{c08}

남편을 먼저 보내던 해, 할머니는 결심했습니다. 죽기 전에 교복 한 번 입어 보겠다고요. 장사를 마친 밤마다 돋보기를 쓰고 책을 폈습니다. 손가락으로 글자를 짚어 가며, 모르는 건 손주에게 물어 가며 공부했습니다. 그렇게 삼 년, 할머니는 검정고시에 붙었습니다. 그리고 만학도 특별 전형으로, 동네 고등학교 1학년이 되었습니다.

{c09}

입학식 날 새벽, 할머니는 장롱 문을 열었습니다. 비닐도 뜯지 않은 새 교복이 걸려 있었습니다. 할머니는 교복을 가슴에 꼭 안았습니다.

"칠십 년 걸렸네. 칠십 년."

{c10}

거울 앞에서 빨간 리본을 맸습니다. 손이 떨려서 몇 번이나 다시 맸습니다. 거울 속에는 주름진 얼굴에 교복을 입은 할머니가 서 있었습니다. 할머니는 그 모습이 조금 우스우면서도, 세상에서 제일 자랑스러웠습니다.

## 2. 경로당은 저쪽입니다

{c11}

교문에 들어서자, 아이들의 시선이 한꺼번에 쏟아졌습니다.

{c12}

"야, 저거 봐. 누구 할머니야?"
"교복 코스프레 하시나 봐."
"대박, 찍어, 찍어."

휴대폰 카메라가 여기저기서 할머니를 향했습니다. 웃음소리가 등 뒤를 따라왔습니다.

{c13}

할머니는 화를 내지 않았습니다. 오히려 아이들에게 고개를 숙여 인사했습니다.

"잘 부탁해요. 나도 오늘부터 여기 학생이에요."

아이들은 더 크게 웃었습니다. 시장 바닥에서 오십 년을 버틴 할머니에게, 그 정도 웃음은 아무것도 아니었습니다.

{c14}

1학년 3반 담임은 수학을 가르치는 박진수 선생님이었습니다. 성적만 보기로 유명한, 학교에서 가장 차가운 선생님이었지요. 박 선생님은 출석부를 내려다보며 말했습니다.

"특별 전형이라 받긴 했습니다만, 학교는 경로당이 아닙니다. 수업에 방해가 되시면 바로 말씀드리겠습니다."

{c15}

할머니의 자리는 창가 맨 뒷자리였습니다. 양옆 책상은 비어 있었습니다. 아무도 할머니 옆에 앉으려 하지 않았습니다.

{c16}

그리고 교실 한가운데, 의자를 뒤로 젖히고 책상에 발을 올린 아이가 있었습니다. 강태오. 키가 백팔십이 넘는 덩치에, 아버지는 건설 회사 사장, 어머니는 학부모회장이었습니다. 선생님들도 태오에게는 함부로 말을 못 했습니다. 태오가 친구들에게 무언가를 속삭이자, 무리가 일제히 할머니를 돌아보며 웃었습니다.

{c17}

쉬는 시간이 끝나고 돌아오니, 할머니 가방에 노란 쪽지가 붙어 있었습니다. 경로당은 저쪽입니다. 화살표까지 그려져 있었습니다.

{c18}

그때, 앞자리의 작은 여자아이가 조용히 다가와 쪽지를 떼어 주었습니다. 동그란 안경을 쓴 아이였습니다.

"신경 쓰지 마세요, 할머니. 쟤들 원래 그래요."

할머니는 아이의 손을 가만히 잡았습니다. "고마워요. 이름이 뭐예요?" 아이는 작은 목소리로 대답했습니다. 윤하린이요.

{c19}

하린이도 늘 혼자였습니다. 쉬는 시간에도, 점심시간에도. 할머니는 그 아이가 고개를 숙이고 다니는 이유를, 그날 점심시간에 알게 되었습니다.

## 3. 엎어진 도시락

{c20}

점심시간이 되자 교실이 시끌벅적해졌습니다. 아이들은 책상을 붙이고 도시락을 꺼냈습니다.

{c21}

하린이가 분홍색 도시락 뚜껑을 여는 순간이었습니다. 태오가 지나가며 손등으로 도시락을 툭 쳤습니다. 도시락이 날아가 바닥에 엎어졌습니다. 밥알과 반찬이 교실 바닥에 흩어졌습니다.

"아, 미안. 손이 미끄러졌네."

{c22}

태오의 친구들이 낄낄 웃었습니다. "야, 주워 먹어. 아깝잖아." 하린이는 떨리는 손으로 무릎을 꿇고 밥알을 줍기 시작했습니다. 태오는 그 모습을 휴대폰으로 찍었습니다. 한두 번 있는 일이 아니었습니다.

{c23}

반 아이들은 아무도 나서지 않았습니다. 고개를 돌리거나, 휴대폰을 보거나, 못 본 척했습니다. 태오에게 찍히면 다음 차례는 자기라는 걸 모두 알고 있었으니까요.

{c24}

그때, 맨 뒷자리에서 할머니가 일어섰습니다. 할머니가 다가오자 태오가 피식 웃었습니다.

"할머니는 빠지세요. 허리 다쳐요."

친구들이 와 하고 웃었습니다. 할머니는 대답 대신, 태오를 가만히 바라보았습니다.

{c25}

할머니의 눈에 들어온 것은 휴대폰을 든 태오의 왼쪽 손목이었습니다. 소매 밑으로 시퍼런 멍이 보였습니다. 넘어져서 생긴 멍이 아니었습니다. 누군가에게 세게 붙잡힌 자국이었습니다.

{c26}

그리고 할머니는 알고 있었습니다. 시장 앞 편의점에서, 밤 열한 시만 되면 혼자 삼각김밥을 먹는 키 큰 아이를. 할머니는 오십 년 동안 시장에서 사람을 보았습니다. 사람 보는 눈만큼은, 누구에게도 지지 않았습니다.

## 4. 밥은 던지는 게 아니에요

{c27}

할머니는 하린이 옆에 쪼그리고 앉았습니다. 그리고 바닥에 흩어진 반찬을, 맨손으로 한 점 한 점 도시락에 주워 담았습니다. 하린이가 울먹이며 말렸지만, 할머니는 멈추지 않았습니다.

{c28}

마지막 계란말이 한 조각까지 주워 담은 뒤, 할머니가 조용히 입을 열었습니다.

"얘야. 밥은 던지는 게 아니에요. 나는 그 밥 한 그릇이 없어서, 학교를 못 다녔어요."

교실이 조금 조용해졌습니다.

{c29}

태오가 코웃음을 쳤습니다.

"그래서 뭐요? 그게 저랑 무슨 상관인데요?"

{c30}

할머니가 천천히 일어섰습니다. 태오의 가슴께에도 닿지 않는 작은 키였습니다. 그런데 할머니는 고개를 들어 태오의 눈을 똑바로 바라보았습니다. 목소리는 크지 않았지만, 교실 끝까지 또렷하게 들렸습니다.

"상관이 있지요. 어제 저녁, 시장 골목에서 네가 우는 걸 봤거든."

{c31}

태오의 얼굴이 굳었습니다. 어제 저녁, 시장 뒷골목. 아무도 없는 줄 알았던 그곳에서, 태오는 교복 소매로 눈물을 훔치고 있었습니다. 할머니의 가게는 바로 그 골목 끝에 있었습니다.

"밤마다 불 꺼진 빈집에 들어가는 애가, 왜 남의 밥을 엎는지. 할미는 알아요. 배가 고픈 게 아니라, 마음이 고픈 거지."

{c32}

태오는 아무 말도 하지 못했습니다. 늘 비웃음을 달고 있던 입이 굳게 닫혔습니다. 휴대폰을 든 손이 천천히, 아래로 내려갔습니다.

{c33}

교실에는 숨소리 하나 들리지 않았습니다. 학교에서 아무도 건드리지 못하던 강태오가, 일흔한 살 할머니 앞에서 처음으로 고개를 떨군 것이었습니다.

{c34}

할머니가 손가락 세 개를 펴 보이며 빙그레 웃었습니다.

"내일부터 할미가 도시락을 세 개 싸 올게요. 하나는 하린이 것, 하나는 내 것. 그리고 하나는, 네 것이다."

## 5. 다음 날 아침

{c35}

그 모든 장면을, 교실 문밖에서 지켜본 사람이 있었습니다. 담임 박진수 선생님이었습니다. 박 선생님은 그날 오후, 태오 무리가 찍어 온 영상들을 모두 확인하고 학교에 정식으로 보고했습니다. 몇 달 동안 아무도 하지 못한 일이었습니다.

{c36}

수업이 끝난 복도에서, 박 선생님이 할머니 앞에 섰습니다. 그리고 처음으로 고개를 숙였습니다.

"아침에 드린 말씀, 사과드립니다. 제가 학생을 잘못 봤습니다."

할머니는 손사래를 치며 웃었습니다. "선생님도 오늘부터 내 도시락 하나 드실래요?"

{c37}

다음 날 아침, 할머니 책상 위에 꼬깃꼬깃 접힌 쪽지가 놓여 있었습니다. 삐뚤빼뚤한 글씨였습니다.

반찬은 계란말이로 해 주세요. 태오.

{c38}

할머니는 쪽지를 교복 주머니에 소중히 넣었습니다. 그리고 가방에서 보자기에 싼 도시락 세 개를 꺼냈습니다. 하린이가 할머니를 보며, 처음으로 환하게 웃었습니다. 그날 할머니의 도시락에는 계란말이가 가득 들어 있었습니다.

{c39}

하지만 그날 저녁, 교장실 문이 거칠게 열렸습니다. 명품 정장에 진주 목걸이를 한 여자, 태오의 어머니이자 학부모회장인 오정희였습니다.

"우리 애한테 무슨 짓을 한 거예요? 그 노인네, 당장 내보내세요."

칠십 년 만에 교복을 입은 할머니에게, 진짜 싸움은 이제부터였습니다. 전학 온 할머니, 2화에서 계속됩니다."""


def main():
    cmd, folder = sys.argv[1], sys.argv[2]
    chars = {c["name"]: c for c in json.load(open(os.path.join(HERE, "등장인물.json"), encoding="utf-8"))["chars"]}
    if cmd == "job":
        items = []
        for cid, who, desc, _ in CUTS:
            looks = "; ".join(f"person {k + 1} (the character from reference image {k + 1}): {chars[nm]['look']}"
                              + ("" if "instead of the school uniform" in desc or "home blouse" in desc or "flashback" in desc or not chars[nm].get("outfit")
                                 else ", " + chars[nm]["outfit"])
                              for k, nm in enumerate(who))   # 한글 이름은 그림에 글자로 나올 수 있어 번호로
            items.append({"id": cid, "width": 1024, "height": 576, "seed": 100 + int(cid[1:]),
                          "refs": [os.path.join(HERE, chars[nm]["face"]) for nm in who],
                          "prompt": f"{STYLE}, Korean high school drama webtoon scene. "
                                    + (f"Characters: {looks}. Each person appears only once, exactly two arms and two legs. " if looks else "No main characters. ")
                                    + f"Scene: {desc}. Cinematic composition, full-bleed image, no border, no frame, no paper edges. No speech bubbles, no text, no letters."})
        os.makedirs(folder, exist_ok=True)
        json.dump({"items": items}, open(os.path.join(folder, "job.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(len(items), "cuts")
    elif cmd == "project":
        story = STORY
        for cid, _, _, cap in CUTS:
            story = story.replace("{" + cid + "}", f"[사진: {os.path.join(folder, cid + '.png')} | {cap} | AI 생성 그림 (FLUX.2 klein) | ]")
        proj = {"ver": 7, "category": "장문", "genre": "[이야기] 사이다 웹툰", "topic": "전학 온 할머니", "title": TITLE,
                "story": story, "sources": [], "notes": "사이다 연재 《전학 온 할머니》 1화", "autophoto": False, "img_source": "그림: 애니(웹툰)",
                "cast": [{"name": nm, "look": c["look"], "look_ko": c["look_ko"],
                          **({"sheet": os.path.join(HERE, c["face"])} if c.get("face") else {})} for nm, c in chars.items()],
                "settings": {"format": "롱폼 가로(1920×1080)", "narration": "on",   # 새 PC·서버 기본값(나레이션 꺼짐·스크롤형) 대신 장문 설정 그대로
                             "layout": "자막형(큰 제목+사진+자막)", "img_fill": "전체 화면(글자가 사진 위에)",
                             "img_motion": "영상처럼(확대·이동·전환)", "fps": "24", "reveal_hit": "off", "reveal_fx": "off",
                             "head_show": "안 보임(제목 카드만)", "sub_split": "한 줄씩(문장·쉼표로 나눠 차례로)", "img_label": "off",   # 규칙: 위 큰 제목·장면 설명 없이, 자막은 한 줄씩
                             "narr_voice": "Supertonic M2 (남성, 무료 로컬) [supertonic:M2]",   # 성우 샘플 1번 (사용자가 고름)
                             "narr_rate": "0", "narr_tone_m": 0.0}}
        out = os.path.join(HERE, "1화_교복입은할머니.json")
        json.dump(proj, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(out, len(story), "chars")


if __name__ == "__main__":
    main()
