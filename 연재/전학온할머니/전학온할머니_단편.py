"""《전학 온 할머니》 단편 (약 30분, 미니드라마 스타일 애니 — 한 편으로 끝남) — 대본 + 컷별 그림 계획
python 연재/전학온할머니/전학온할머니_단편.py job <저장폴더>   → 그림 주문서(klein_worker 용) job.json
python 연재/전학온할머니/전학온할머니_단편.py project <그림폴더> → 프로젝트 파일(render_project 용) 연재/전학온할머니/전학온할머니_단편.json
  영상은 render_project.py <프로젝트> --대본그대로 (오프닝·대본을 프로그램이 고쳐 쓰지 않게)
대본의 {컷번호} 자리에 그 컷 그림이 들어감. chars = 그 컷에 나오는 인물(캐릭터 시트를 기준 그림으로 넣음)
나레이션 한 명(남자 성우 2)이 대사까지 모두 읽음 (사용자 결정) → DIALOGUE 없음"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TITLE = "전학 온 할머니"

# 화풍: 일본 애니풍 캐릭터 (사용자 결정, 화풍샘플/사용자_캐릭터스타일.png)
STYLE = ("Japanese anime style scene, TV anime screenshot, clean crisp line art, anime cel shading with soft shadows, "
         "realistic human proportions, natural colors, detailed anime background art")

MARKET = "wearing a rubber fish-market apron over a faded purple padded vest, rubber arm sleeves and black rubber boots instead of the school uniform"
NO_UNIFORM = ("instead of the school uniform", "flashback", "home blouse", "graduation gown")   # 이런 컷은 교복 묘사를 붙이지 않음

# (컷번호, 나오는 인물, 그림 설명(영어), 화면 설명(한국어)) — 인물 옷을 바꿀 땐 설명에 적음
CUTS = [
    # 오프닝
    ("c001", ["오정희"], "inside a school meeting room, the glamorous woman in a cream tweed suit raising her hand high as if to slap someone, furious face, other adults gasping in the background, dramatic", "손을 치켜든 학부모회장"),
    ("c002", ["말순"], "the small elderly grandmother in the school uniform standing still without flinching, calm face, eyes closed, in a school meeting room, tense", "눈 하나 깜짝 않는 할머니"),
    ("c003", ["장학관"], "the tall dignified man in a navy suit bursting through the double doors of a school meeting room, backlit by the hallway light, serious face", "문을 열고 들어온 장학관"),
    # 1. 칠십 년 걸린 교복
    ("c004", [], "a busy Korean traditional fish market at 4 a.m. before dawn, wet floor, ice boxes full of fish, yellow hanging bulbs, steam, distant vendors", "새벽 4시 생선 시장"),
    ("c005", ["말순"], f"the elderly grandmother {MARKET}, gutting a big mackerel on a wet wooden board at her small fish stall under a hanging bulb before dawn", "생선을 손질하는 할머니"),
    ("c006", [], "close-up of an old woman's rough cracked hands with bandaged fingertips holding a fish knife, wet wooden board, warm bulb light", "터지고 갈라진 손"),
    ("c007", [], "faded sepia-toned flashback: a poor 1960s Korean village, a thin little girl of nine in old patched clothes carrying her baby brother on her back, looking longingly through a wooden fence at children entering a small country school", "학교 담장 너머를 바라보던 아홉 살 말순"),
    ("c008", [], "faded sepia-toned flashback: the same thin little girl crouching under a school window outside, quietly singing along, eyes closed, sunlight", "창문 밑에서 노래를 따라 부르던 말순"),
    ("c009", [], "faded sepia-toned flashback: a young Korean woman in the 1970s carrying a large basin of fish on her head through a crowded market, three small children following her", "생선 대야를 이고 아이 셋을 키우던 젊은 날"),
    ("c010", ["말순"], f"a small Korean funeral altar room with white chrysanthemums and a framed photo of an old man, the elderly grandmother in a plain black hanbok mourning dress instead of the school uniform, sitting alone and looking at the photo", "남편을 먼저 보내던 날"),
    ("c011", ["말순"], f"the elderly grandmother wearing a plain home blouse, sitting alone at a small kitchen table at night studying an old textbook with a pencil under a dim lamp, reading glasses on her nose", "밤마다 공부하던 할머니"),
    ("c012", ["말순"], "the elderly grandmother wearing a plain home blouse holding a letter and crying with joy in a small old room, morning light", "검정고시 합격 통지서"),
    ("c013", [], "a family dinner table in a modern Korean apartment, a middle-aged man in a business shirt frowning and arguing, his wife looking uncomfortable, food on the table", "반대하는 큰아들"),
    ("c014", ["말순"], "in a small old bedroom at dawn, the elderly grandmother wearing a plain home blouse hugging a brand-new navy school uniform blazer on a hanger against her chest in front of an old wooden wardrobe, eyes glistening, smiling", "새 교복을 안은 할머니"),
    ("c015", ["말순"], "the elderly grandmother in the school uniform standing in front of an old mirror tying her red ribbon tie, proud shy smile, morning light", "거울 앞에서 리본을 매는 할머니"),
    # 2. 경로당은 저쪽입니다
    ("c016", ["말순"], "wide shot: the small elderly grandmother in the school uniform walking alone through a big Korean high school front gate in the morning, many teenage students staring, cherry blossom trees", "교문을 들어서는 할머니"),
    ("c017", [], "several Korean high school students in navy uniforms laughing and pointing while filming with their smartphones near a school gate, morning", "휴대폰으로 찍으며 웃는 학생들"),
    ("c018", ["말순"], "the elderly grandmother in the school uniform bowing politely in front of a group of laughing students in a school courtyard", "고개 숙여 인사하는 할머니"),
    ("c019", ["박 담임", "말순"], "a Korean high school classroom, the stern male teacher with silver glasses standing at the front holding a clipboard, looking coldly at the small elderly grandmother standing beside the teacher's desk, students seated watching", "할머니를 소개하는 박 담임"),
    ("c020", ["박 담임"], "close-up of the stern male teacher with silver glasses pushing up his glasses, cold expression, classroom blackboard behind", "\"학교는 경로당이 아닙니다\""),
    ("c021", ["말순"], "the elderly grandmother in the school uniform sitting alone at the last desk in the back corner by the window, empty desks around her, students in front whispering and glancing back", "맨 뒷자리에 혼자 앉은 할머니"),
    ("c022", ["태오"], "the tall arrogant boy with an open blazer leaning back on his chair with his feet on the desk, two grinning boys beside him, looking toward the back of the classroom with a sneer", "교실의 왕, 강태오"),
    ("c023", [], "close-up of a yellow sticky note stuck on an old brown cloth school bag hanging on a desk, the note has only scribbled lines and an arrow drawing, no readable letters", "가방에 붙은 쪽지"),
    ("c024", ["하린", "말순"], "the small timid girl with round glasses quietly peeling a sticky note off the elderly grandmother's cloth bag and handing it to her, the grandmother looking at the girl with a warm smile, classroom back row", "몰래 쪽지를 떼어 주는 하린"),
    ("c025", ["하린"], "the small timid girl with round glasses sitting alone at her desk during break time, head down, other students chatting in groups away from her", "늘 혼자인 하린"),
    # 3. 첫 수학 시간
    ("c026", ["박 담임"], "the stern male teacher with silver glasses writing a long math word problem with numbers on a classroom blackboard, chalk dust, the writing is just abstract chalk marks", "칠판에 문제를 적는 박 담임"),
    ("c027", ["박 담임", "말순"], "the stern male teacher pointing chalk toward the back of the classroom at the elderly grandmother in the school uniform, students turning around to look at her, smirking", "할머니를 지목하는 박 담임"),
    ("c028", ["태오"], "the tall arrogant boy laughing loudly and clapping his hands mockingly at his desk, his friends laughing too", "킥킥대는 태오 무리"),
    ("c029", ["말순"], "the elderly grandmother in the school uniform standing up at her desk with her eyes half closed, moving her fingers in the air as if counting on an invisible abacus, calm focused face", "손가락으로 셈을 하는 할머니"),
    ("c030", [], "faded sepia-toned flashback: a fish market stall, an old wooden abacus and a pile of coins and paper money on a wet counter, a hand quickly counting", "오십 년 시장 셈"),
    ("c031", ["박 담임"], "the stern male teacher with silver glasses staring with wide surprised eyes, chalk falling from his fingers, classroom", "분필을 떨어뜨린 박 담임"),
    ("c032", [], "Korean high school students in a classroom with open mouths and wide eyes, stunned, some clapping hesitantly", "놀란 반 아이들"),
    ("c033", ["말순", "하린"], "the elderly grandmother in the school uniform sitting back down calmly, the small girl with glasses at the next desk looking at her with sparkling admiring eyes", "반짝이는 하린의 눈"),
    # 4. 엎어진 도시락
    ("c034", [], "a Korean high school classroom at lunchtime, students eating lunchboxes at desks pushed together, sunlight through windows, noisy cheerful atmosphere", "점심시간의 교실"),
    ("c035", ["하린"], "the small girl with glasses opening a pink lunchbox at her desk alone, neat rice and rolled omelet inside, a small hopeful smile", "도시락을 여는 하린"),
    ("c036", ["태오", "하린"], "the tall arrogant boy knocking a pink lunchbox off the desk of the small girl with glasses, rice and side dishes flying onto the classroom floor, the girl flinching in shock", "도시락을 엎는 태오"),
    ("c037", ["하린"], "the small girl with glasses kneeling on the classroom floor picking up spilled rice with trembling hands, tears in her eyes, shadows of tall boys standing over her", "무릎 꿇고 밥을 줍는 하린"),
    ("c038", ["태오"], "the tall arrogant boy holding up a smartphone to film downward, smirking coldly, classroom background", "그 모습을 찍는 태오"),
    ("c039", [], "Korean high school students at their desks looking away, pretending not to see, some staring at their phones, uncomfortable silence", "모른 척하는 반 아이들"),
    ("c040", ["말순", "태오"], "the small elderly grandmother in the school uniform walking toward the tall arrogant boy in the classroom aisle, the boy turning and looking down at her with a mocking smirk, big height difference", "다가가는 할머니"),
    ("c041", ["태오"], "close-up of the tall boy's left wrist with a dark purple bruise as he holds a smartphone, his sleeve pulled back slightly", "태오 손목의 멍"),
    ("c042", ["태오"], "the tall boy alone in a convenience store late at night, standing at the window counter eating a triangle kimbap by himself, cold fluorescent light, lonely", "밤마다 혼자 끼니를 때우는 태오"),
    ("c043", ["말순", "하린"], "the elderly grandmother in the school uniform crouching next to the crying small girl with glasses on the classroom floor, gently putting spilled side dishes back into the pink lunchbox with her own hands", "손수 반찬을 주워 담는 할머니"),
    ("c044", ["말순"], "medium close-up of the elderly grandmother in the school uniform crouching on the classroom floor and looking up with a calm serious face, speaking quietly but firmly, light from the window", "조용히 입을 여는 할머니"),
    ("c045", ["태오"], "the tall arrogant boy frowning and shouting defiantly, one hand in his pocket, classroom", "\"그래서 뭐요?\""),
    ("c046", ["말순", "태오"], "the small elderly grandmother in the school uniform standing straight and looking up directly into the eyes of the tall boy, the boy's mocking smile fading into shock, tense standoff in a classroom", "태오를 올려다보는 할머니"),
    ("c047", ["태오"], "evening in a traditional market back alley, the tall boy in his school uniform standing alone behind stacked crates, wiping tears with his sleeve, warm yellow lights, nobody else", "시장 골목에서 혼자 울던 태오"),
    ("c048", ["태오"], "close-up of the tall boy's face, eyes wide and trembling, speechless, slowly lowering his smartphone", "말을 잃은 태오"),
    ("c049", [], "a silent Korean high school classroom, all students staring toward the back of the room in shock, frozen, sunlight", "숨죽인 교실"),
    ("c050", ["말순"], "the elderly grandmother in the school uniform holding up three fingers with a warm gentle smile, classroom", "도시락 세 개의 약속"),
    # 5. 도시락 세 개
    ("c051", ["박 담임"], "the stern male teacher with silver glasses standing in the school hallway, watching through the classroom door window, his cold face softening in surprise", "복도에서 지켜본 박 담임"),
    ("c052", ["박 담임"], "the male teacher with silver glasses sitting alone at a desk in a teachers' office in the evening, watching videos on a smartphone with a grim face, a report paper beside him", "영상을 확인하는 박 담임"),
    ("c053", ["말순"], "the elderly grandmother wearing a plain home blouse cooking rolled omelets in a small old kitchen before dawn, three lunchboxes lined up on the counter, steam", "새벽에 도시락 세 개를 싸는 할머니"),
    ("c054", [], "close-up of a crumpled note with messy scribbled handwriting (no readable letters) on an empty school desk next to an old brown cloth bag, morning sunlight", "책상 위의 서툰 쪽지"),
    ("c055", ["말순", "하린"], "morning in a classroom, the elderly grandmother in the school uniform placing three lunchboxes wrapped in colorful cloth on her desk, the small girl with glasses beside her smiling shyly", "보자기에 싼 도시락 세 개"),
    ("c056", ["태오"], "the tall boy sitting alone on a rooftop of a school at lunchtime, eating from a lunchbox wrapped in colorful cloth, eyes red, chewing slowly", "옥상에서 몰래 도시락을 먹는 태오"),
    ("c057", ["박 담임", "말순"], "the male teacher with silver glasses bowing his head to the small elderly grandmother in the school uniform in a quiet school hallway after class, the grandmother smiling kindly", "사과하는 박 담임"),
    ("c058", ["말순", "하린"], "the elderly grandmother in the school uniform and the small girl with glasses walking home together along a street at sunset, laughing, cherry blossom petals falling", "함께 하교하는 할머니와 하린"),
    # 6. 학부모회장
    ("c059", ["오정희"], "the glamorous woman in a cream tweed suit slamming open the door of a school principal's office, angry face, designer handbag on her arm", "교장실에 들이닥친 학부모회장"),
    ("c060", ["최 교감", "오정희"], "in a school principal's office, the short chubby balding vice principal in a brown suit bowing and rubbing his hands obsequiously in front of the glamorous woman in a cream tweed suit sitting on a sofa", "굽실거리는 최 교감"),
    ("c061", ["최 교감"], "close-up of the short chubby balding vice principal with a sly greasy smile, small narrow eyes, holding a thick envelope behind his back", "능글맞은 교감의 미소"),
    ("c062", [], "close-up of a smartphone screen showing a group chat with many message bubbles, the text is only abstract blurred lines, no readable letters, dark room", "학부모 단톡방"),
    ("c063", ["말순"], "the elderly grandmother in the school uniform walking down a school hallway, parents and students in the hallway whispering and looking at her coldly", "수군거리는 사람들"),
    ("c064", ["오정희", "말순"], f"daytime at a traditional fish market stall, the glamorous woman in a cream tweed suit standing in front of the stall pointing and yelling, the elderly grandmother {MARKET} standing behind her fish stall quietly, other vendors watching", "시장까지 찾아온 오정희"),
    ("c065", ["오정희"], "close-up of the glamorous woman in a cream tweed suit covering her nose with a handkerchief in disgust at a fish market, sneering", "코를 막고 비웃는 오정희"),
    ("c066", [], "a group of middle-aged Korean market vendors in aprons glaring angrily, one old man rolling up his sleeves, fish market background", "화가 난 시장 상인들"),
    ("c067", ["말순"], f"the elderly grandmother {MARKET}, raising one hand calmly to stop the angry vendors behind her, gentle firm face, fish market", "상인들을 말리는 할머니"),
    ("c068", ["태오"], "the tall boy hiding behind a market pillar watching from a distance, face pale, clenched fists", "숨어서 지켜보는 태오"),
    ("c069", ["태오", "오정희"], "night in a big luxurious empty Korean apartment living room, the glamorous woman in a cream tweed suit gripping the tall boy's left wrist hard and scolding him, the boy looking down, cold blue light", "태오의 손목을 붙잡는 엄마"),
    ("c070", ["태오"], "the tall boy alone in a dark huge bedroom sitting on the floor against the bed, hugging his knees, a colorful lunchbox cloth on the floor beside him, moonlight", "불 꺼진 방의 태오"),
    ("c071", [], "close-up of an official school notice paper on a bulletin board with a red stamp, the text is only abstract lines, no readable letters", "선도위원회 소집 통지문"),
    ("c072", ["하린", "말순"], "the small girl with glasses crying and holding the elderly grandmother's hand in an empty classroom after school, the grandmother in the school uniform patting her head", "울먹이는 하린"),
    ("c073", ["말순"], "the elderly grandmother wearing a plain home blouse sitting alone on a small old wooden porch at night, looking up at the moon, holding her folded school uniform on her lap, quiet resolve", "달을 보며 생각에 잠긴 할머니"),
    ("c074", ["말순"], "the elderly grandmother wearing a plain home blouse taking out an old yellowed photograph from a small wooden box at night, looking at it with a soft smile", "낡은 사진 한 장"),
    ("c075", [], "faded sepia-toned old photograph from the 1980s: a group of skinny teenage boys in gray uniforms sitting at a long table in a plain dormitory eating rice and soup, one boy with a small scar on his eyebrow looking at the camera", "40년 전의 사진"),
    # 7. 선도위원회
    ("c076", [], "a formal school meeting room with a long table, name plates with no readable letters, chairs facing each other, gray rainy daylight through the windows", "선도위원회가 열린 회의실"),
    ("c077", ["최 교감", "오정희"], "in a school meeting room, the short chubby balding vice principal sitting at the head of a long table reading a document, the glamorous woman in a cream tweed suit sitting beside him with crossed arms and a victorious smirk", "교감 옆에 앉은 오정희"),
    ("c078", ["말순"], "the small elderly grandmother in the school uniform sitting alone on a single chair facing a long table of stern adults, hands folded on her knees, back straight", "홀로 앉은 할머니"),
    ("c079", ["최 교감"], "the short chubby balding vice principal standing and reading accusations from a paper with a fake serious face, adjusting his gold tie pin", "죄목을 읽는 최 교감"),
    ("c080", ["오정희"], "the glamorous woman in a cream tweed suit standing and pointing her finger across the meeting table, shouting with a cruel expression", "\"노인네가 애를 협박했어요\""),
    ("c081", ["말순"], "close-up of the elderly grandmother in the school uniform listening quietly with her eyes lowered, calm, a faint sad smile", "말없이 듣는 할머니"),
    ("c082", ["하린"], "the small girl with glasses bursting through the meeting room door, out of breath, trembling but determined face, holding a smartphone tightly", "문을 열고 들어온 하린"),
    ("c083", ["하린"], "the small girl with glasses standing in a meeting room speaking with tears streaming but chin raised, holding up a smartphone, brave", "용기를 낸 하린"),
    ("c084", [], "many Korean high school students in uniforms crowded at the meeting room door and hallway, holding up their smartphones together, determined faces", "따라 들어온 반 아이들"),
    ("c085", ["박 담임"], "the male teacher with silver glasses stepping forward in the meeting room and placing a thick report document on the long table firmly", "보고서를 내려놓는 박 담임"),
    ("c086", ["최 교감"], "the short chubby balding vice principal sweating and slamming his palm on the table, red angry face", "탁자를 내리치는 교감"),
    ("c087", ["태오"], "the tall boy standing at the meeting room doorway, soaked from the rain, holding his school bag, staring at his mother with a determined face", "문 앞에 선 태오"),
    ("c088", ["태오"], "the tall boy in the meeting room pulling up his left sleeve to show the dark bruise on his wrist, eyes full of tears, speaking", "멍을 보여 주는 태오"),
    ("c089", ["오정희"], "the glamorous woman in a cream tweed suit frozen in shock, face pale, her hand trembling on her designer handbag", "얼어붙은 오정희"),
    ("c090", ["오정희"], "the glamorous woman in a cream tweed suit raising her hand high as if to slap someone, furious face, meeting room, dramatic angle", "다시 손을 치켜든 오정희"),
    ("c091", ["말순", "태오"], "the small elderly grandmother in the school uniform stepping in front of the tall boy to shield him with her arms spread out, eyes calm, meeting room", "태오 앞을 막아선 할머니"),
    # 8. 어머니
    ("c092", ["장학관"], "the tall dignified man in a navy suit standing at the opened double doors of a school meeting room holding a thin black document folder, two officials behind him, serious face", "교육청 장학관"),
    ("c093", ["최 교감"], "the short chubby balding vice principal jumping up from his chair in panic, face pale, bowing deeply and nervously", "새파랗게 질린 교감"),
    ("c094", ["장학관", "말순"], "the tall man in a navy suit walking past everyone straight to the small elderly grandmother in the school uniform, looking down at her with trembling eyes, meeting room", "할머니 앞에 선 장학관"),
    ("c095", ["장학관", "말순"], "the tall man in a navy suit bowing deeply at ninety degrees in front of the small elderly grandmother in the school uniform, the grandmother looking up at him in surprise, meeting room, everyone in the background shocked", "\"어머니\""),
    ("c096", [], "faded sepia-toned flashback: 1980s winter night, a skinny teenage boy with a scar on his eyebrow in a thin gray uniform shivering behind a fish market stall, snow falling", "40년 전 겨울, 시장의 소년"),
    ("c097", [], "faded sepia-toned flashback: a young Korean woman in her thirties in a market apron handing a steaming bowl of rice soup to a skinny teenage boy sitting on an upside-down crate, snow falling, warm bulb light", "국밥을 건네던 젊은 말순"),
    ("c098", [], "faded sepia-toned flashback: the same young woman in a market apron carrying two big pots through a gate of a plain juvenile detention dormitory, teenage boys running to her happily", "소년원에 밥을 해 나르던 날들"),
    ("c099", ["장학관", "말순"], "the tall man in a navy suit kneeling on one knee and holding the elderly grandmother's rough hands with both hands, tears in his eyes, the grandmother smiling with tears, meeting room", "할머니 손을 잡은 장학관"),
    ("c100", ["장학관", "최 교감"], "the tall man in a navy suit standing and opening a black document folder in front of the short chubby balding vice principal who is trembling, official papers inside with no readable letters", "서류철을 펼치는 장학관"),
    ("c101", ["최 교감", "오정희"], "the short chubby balding vice principal and the glamorous woman in a cream tweed suit both looking down in shame and panic, the woman clutching her handbag, meeting room", "고개를 떨군 교감과 오정희"),
    ("c102", ["오정희", "태오"], "the glamorous woman with her makeup smeared by tears looking at her tall son, the boy standing with tears, the woman reaching out her hand gently this time, meeting room", "아들을 바라보는 오정희"),
    ("c103", ["말순", "오정희"], "the small elderly grandmother in the school uniform gently holding the hand of the crying glamorous woman in a cream tweed suit, meeting room, soft light after rain", "오정희의 손을 잡아 주는 할머니"),
    # 9. 졸업식
    ("c104", [], "a Korean high school campus through the seasons as a montage: summer green trees, autumn red leaves, winter snow on the school field, no people in focus", "흘러간 세 번의 계절"),
    ("c105", ["말순", "하린", "태오"], "a school cafeteria table, the elderly grandmother in the school uniform, the small girl with glasses and the tall boy eating from three colorful cloth-wrapped lunchboxes together, laughing", "셋이 함께 먹는 도시락"),
    ("c106", [], "a Korean high school graduation ceremony in a gymnasium decorated with flowers, many students in uniforms with flower bouquets, families clapping", "졸업식"),
    ("c107", ["말순"], "the elderly grandmother in the school uniform holding a big flower bouquet, standing at the bottom of a stage in a school gymnasium, nervous happy face", "졸업식장의 할머니"),
    ("c108", ["말순", "하린", "태오"], "the small girl with glasses and the tall boy each holding one of the elderly grandmother's hands and walking her up the stage stairs, many students following behind, school gymnasium", "할머니 손을 잡고 단상에 오르는 아이들"),
    ("c109", ["말순", "장학관"], "the tall man in a navy suit on a stage handing a diploma with both hands to the small elderly grandmother in the school uniform, the grandmother receiving it with both hands, crying and smiling, school gymnasium", "칠십삼 년 만의 졸업장"),
    ("c110", ["말순"], "close-up of the elderly grandmother in the school uniform hugging a diploma to her chest with closed eyes and happy tears, flower petals in the air", "졸업장을 안은 할머니"),
    ("c111", [], "a Korean high school front gate at sunset with cherry blossoms falling, no people, warm golden light, peaceful", "벚꽃 지는 교문"),
]

STORY = """{c001}

학부모회장의 손이 허공으로 높이 올라갔습니다. 그 손이 향한 곳은, 교복을 입은 일흔한 살 할머니의 뺨이었습니다.

{c002}

할머니는 피하지 않았습니다. 눈을 감고, 그 자리에 가만히 서 있었습니다.

{c003}

바로 그 순간, 회의실 문이 활짝 열렸습니다. 교육청에서 온 장학관이었습니다. 그리고 그 장학관이 할머니 앞에서 한 첫마디에, 회의실에 있던 모든 사람이 얼어붙었습니다. 시장에서 생선을 팔던 이 할머니는, 대체 누구였을까요.

## 1. 칠십 년 걸린 교복

{c004}

새벽 네 시. 해가 뜨려면 한참 남은 시간인데, 생선 시장에는 벌써 불이 켜져 있었습니다. 얼음 깨는 소리, 경매꾼의 외침, 트럭이 들어오는 소리로 시장은 이미 한낮처럼 시끄러웠습니다.

{c005}

김말순 할머니는 오늘도 그 자리에 있었습니다. 시장 맨 끝, 전구 하나가 달린 작은 생선 가게. 할머니는 이 자리에서 오십 년 동안 생선을 팔았습니다. 칼질 몇 번이면 고등어 한 마리가 깨끗하게 손질되었습니다. 단골들은 말순 할머니 생선이 시장에서 제일 싱싱하다고 했습니다. 할머니는 손님 얼굴만 봐도 오늘 무슨 생선이 필요한지 알았습니다.

{c006}

얼음물에 젖고, 칼에 베이고, 찬 바람에 터진 손. 할머니의 손가락 끝에는 반창고가 마를 날이 없었습니다. 그 손으로 자식 셋을 대학에 보냈습니다. 그런데 정작 할머니는, 학교 문턱을 넘어 본 적이 없었습니다.

{c007}

전쟁이 끝나고 모두가 가난하던 시절이었습니다. 어린 말순은 아홉 살에 학교를 그만두었습니다. 아버지는 일찍 돌아가셨고, 어머니 혼자서는 동생 넷을 먹일 수 없었습니다. 말순은 등에 갓난 동생을 업고, 학교 담장 너머로 공부하는 아이들을 바라보았습니다.

{c008}

종소리가 들리면 교실 창문 밑에 쪼그려 앉았습니다. 안에서 들려오는 노래를 따라 불렀고, 선생님이 읽어 주는 글을 따라 외웠습니다. 그것이 말순이 아는 학교의 전부였습니다. 어느 날 선생님에게 들켜 쫓겨난 뒤로는, 그마저도 할 수 없었습니다.

{c009}

열여덟에 시집을 갔고, 스물다섯에 남편이 사고로 다리를 다쳤습니다. 그날부터 말순은 생선 대야를 머리에 이고 시장에 나갔습니다. 아이 셋이 졸졸 따라왔습니다. 말순은 다짐했습니다. 나는 못 배웠어도, 내 새끼들만큼은 끝까지 가르치겠다고요. 그리고 그 약속을 지켰습니다. 큰아들은 회사원이 되었고, 둘째 딸은 간호사가, 막내는 선생님이 되었습니다.

{c010}

삼 년 전, 평생 곁을 지켜 준 남편이 먼저 떠났습니다. 장례식장에서 혼자 남편 사진을 보던 밤, 할머니는 이상하게도 아홉 살의 그 담장이 떠올랐습니다. 그리고 결심했습니다. 죽기 전에, 교복 한 번 입어 보겠다고요.

{c011}

그날부터 할머니는 장사를 마친 밤마다 돋보기를 쓰고 책을 폈습니다. 한글은 겨우 읽었지만 영어는 알파벳부터 시작이었습니다. 손가락으로 글자를 짚어 가며, 모르는 건 초등학생 손주에게 물어 가며 공부했습니다. 졸다가 책상에 이마를 찧은 날도 많았습니다. 그래도 할머니는 책을 덮지 않았습니다.

{c012}

그렇게 삼 년. 할머니는 초등, 중학 검정고시에 차례로 붙었습니다. 그리고 만학도 특별 전형으로, 동네 고등학교 1학년 입학 허가를 받았습니다. 합격 통지서를 받던 날, 할머니는 그 종이를 가슴에 대고 한참을 울었습니다.

{c013}

하지만 모두가 기뻐한 건 아니었습니다. 큰아들은 저녁 식탁에서 언성을 높였습니다.

"어머니, 그 나이에 고등학교라니요. 애들이 뭐라고 하겠어요. 동네 사람들은요. 창피해서 제가 못 살겠습니다."

할머니는 숟가락을 내려놓고 조용히 말했습니다.

"아들아. 나는 평생 창피한 줄 모르고 생선을 팔았다. 너희 학비 대려고. 이제는 나를 위해서, 한 번만 창피해 보련다."

큰아들은 더 이상 아무 말도 하지 못했습니다.

{c014}

입학식 날 새벽, 할머니는 장롱 문을 열었습니다. 비닐도 뜯지 않은 새 교복이 걸려 있었습니다. 할머니는 교복을 가슴에 꼭 안았습니다.

"칠십 년 걸렸네. 칠십 년."

{c015}

거울 앞에서 빨간 리본을 맸습니다. 손이 떨려서 몇 번이나 다시 맸습니다. 거울 속에는 주름진 얼굴에 교복을 입은 할머니가 서 있었습니다. 조금 우스우면서도, 세상에서 제일 자랑스러운 모습이었습니다.

## 2. 경로당은 저쪽입니다

{c016}

교문에 들어서자, 아이들의 시선이 한꺼번에 쏟아졌습니다. 벚꽃이 흩날리는 운동장 한가운데를, 작은 할머니가 천가방을 메고 걸어갔습니다.

{c017}

"야, 저거 봐. 누구 할머니야?"
"교복 코스프레 하시나 봐."
"대박, 찍어, 찍어. 이거 올리면 조회 수 터진다."

휴대폰 카메라가 여기저기서 할머니를 향했습니다. 웃음소리가 등 뒤를 졸졸 따라왔습니다.

{c018}

할머니는 화를 내지 않았습니다. 오히려 아이들에게 고개를 숙여 인사했습니다.

"잘 부탁해요. 나도 오늘부터 여기 학생이에요."

아이들은 더 크게 웃었습니다. 하지만 시장 바닥에서 오십 년을 버틴 할머니에게, 그 정도 웃음은 아무것도 아니었습니다.

{c019}

1학년 3반 담임은 수학을 가르치는 박진수 선생님이었습니다. 성적만 보기로 유명한, 학교에서 가장 차가운 선생님이었지요. 박 선생님은 할머니를 교탁 옆에 세워 두고, 출석부를 내려다보며 말했습니다.

{c020}

"교육청 특별 전형이라 받긴 했습니다만, 분명히 말씀드리겠습니다. 학교는 경로당이 아닙니다. 수업에 방해가 되시면 바로 학교에 말씀드리겠습니다."

교실 여기저기서 킥킥거리는 소리가 새어 나왔습니다.

{c021}

할머니의 자리는 창가 맨 뒷자리였습니다. 양옆 책상은 비어 있었습니다. 아무도 할머니 옆에 앉으려 하지 않았습니다. 할머니는 새 공책을 꺼내 첫 장에 또박또박 이름을 적었습니다. 김말순. 칠십 년 만에 처음으로, 학생이 되어 적어 보는 이름이었습니다.

{c022}

교실 한가운데에는 의자를 뒤로 젖히고 책상에 발을 올린 아이가 있었습니다. 강태오. 키가 백팔십이 넘는 덩치에, 아버지는 건설 회사 사장, 어머니는 학교 학부모회장이었습니다. 선생님들도 태오에게는 함부로 말을 못 했습니다. 태오가 친구들에게 무언가를 속삭이자, 무리가 일제히 할머니를 돌아보며 웃었습니다.

{c023}

쉬는 시간이 끝나고 돌아오니, 할머니 가방에 노란 쪽지가 붙어 있었습니다. 경로당은 저쪽입니다. 친절하게 화살표까지 그려져 있었습니다. 태오 무리가 배를 잡고 웃었습니다.

{c024}

그때, 앞자리의 작은 여자아이가 조용히 다가와 쪽지를 떼어 주었습니다. 동그란 안경을 쓴 아이였습니다.

"신경 쓰지 마세요, 할머니. 쟤들 원래 그래요."

할머니는 아이의 손을 가만히 잡았습니다. "고마워요. 이름이 뭐예요?" 아이는 작은 목소리로 대답했습니다. 윤하린이요.

{c025}

하린이도 늘 혼자였습니다. 쉬는 시간에도, 점심시간에도. 다른 아이들은 하린이 근처에 가지 않았습니다. 할머니는 그 이유를 아직 몰랐습니다. 그리고 며칠 뒤, 그 이유를 알게 되었습니다.

## 3. 첫 수학 시간

{c026}

입학 사흘째, 첫 수학 시간이었습니다. 박 선생님은 칠판 가득 긴 문제를 적었습니다. 시장에서 물건을 사고팔며 남는 이익을 계산하는, 꽤 까다로운 응용문제였습니다.

{c027}

박 선생님이 분필로 교실 맨 뒤를 가리켰습니다.

"김말순 학생. 한번 풀어 보시죠. 특별 전형으로 오셨으니, 이 정도는 하실 수 있겠지요."

반 아이들이 일제히 뒤를 돌아보았습니다. 다들 알고 있었습니다. 선생님이 할머니를 망신 주려 한다는 것을요.

{c028}

태오가 손뼉을 치며 소리쳤습니다. "와, 할머니 파이팅! 계산기 빌려드려요?" 교실이 웃음바다가 되었습니다.

{c029}

할머니는 천천히 일어섰습니다. 그리고 칠판을 한 번 바라보더니, 눈을 반쯤 감았습니다. 허공에서 손가락이 빠르게 움직였습니다. 마치 보이지 않는 주판을 튕기는 것 같았습니다.

{c030}

오십 년 동안, 할머니는 생선을 팔았습니다. 하루에 수백 명의 손님, 수백 번의 거스름돈. 경매에서 얼마에 사서 얼마에 팔아야 남는지, 얼음값과 차비까지 빼면 얼마가 남는지. 할머니는 그 모든 셈을 평생 머릿속으로 해 왔습니다. 계산기 같은 건 필요 없었습니다.

"십이만 칠천오백 원이 남네요. 그런데 선생님, 이 문제는 얼음값을 안 넣으셨어요. 생선 장사는 얼음값 빼면 남는 게 반이에요."

{c031}

박 선생님의 손에서 분필이 툭 떨어졌습니다. 답이 맞았습니다. 그것도 십 초도 걸리지 않았습니다. 박 선생님은 한참 동안 칠판과 할머니를 번갈아 보았습니다.

{c032}

교실이 조용해졌습니다. 그러다 누군가 작게 손뼉을 쳤습니다. 한 명, 두 명, 손뼉 소리가 점점 커졌습니다. 태오만 혀를 차며 고개를 돌렸습니다.

{c033}

할머니는 아무렇지 않은 듯 자리에 앉았습니다. 옆자리로 자리를 옮겨 온 하린이가, 반짝이는 눈으로 할머니를 바라보았습니다.

"할머니, 진짜 멋있어요."

할머니가 빙그레 웃었습니다. "멋있긴요. 먹고살려니 늘었지."

그날 이후, 하린이는 할머니 옆자리를 떠나지 않았습니다. 그리고 그것이, 태오의 눈에 거슬리기 시작했습니다.

## 4. 엎어진 도시락

{c034}

점심시간이었습니다. 아이들은 책상을 붙이고 도시락을 꺼냈습니다. 이 학교는 급식 공사 때문에 한 달 동안 도시락을 싸 와야 했습니다.

{c035}

하린이가 분홍색 도시락 뚜껑을 열었습니다. 하얀 밥 위에 노란 계란말이가 가지런히 놓여 있었습니다. 아침 일찍 출근하는 엄마가 새벽에 싸 준 도시락이었습니다. 하린이는 오늘은 할머니와 같이 먹을 생각에, 조금 들떠 있었습니다.

{c036}

그 순간이었습니다. 태오가 지나가며 손등으로 도시락을 툭 쳤습니다. 도시락이 날아가 바닥에 엎어졌습니다. 밥알과 계란말이가 교실 바닥에 흩어졌습니다.

"아, 미안. 손이 미끄러졌네."

{c037}

태오의 친구들이 낄낄 웃었습니다. "야, 주워 먹어. 아깝잖아." 하린이는 떨리는 손으로 무릎을 꿇고 밥알을 줍기 시작했습니다. 눈물이 뚝뚝 바닥에 떨어졌습니다.

{c038}

태오는 그 모습을 휴대폰으로 찍었습니다. 한두 번 있는 일이 아니었습니다. 태오의 휴대폰에는 이런 영상이 수십 개나 있었습니다. 하린이가 늘 혼자였던 이유였습니다. 하린이 곁에 있으면, 다음 차례는 자기가 될 테니까요.

{c039}

반 아이들은 아무도 나서지 않았습니다. 고개를 돌리거나, 휴대폰을 보거나, 못 본 척했습니다.

{c040}

그때, 할머니가 자리에서 일어섰습니다. 할머니가 다가오자 태오가 피식 웃었습니다.

"할머니는 빠지세요. 허리 다쳐요. 수학 좀 한다고 여기가 시장인 줄 아세요?"

친구들이 와 하고 웃었습니다. 할머니는 대답 대신, 태오를 가만히 바라보았습니다.

{c041}

할머니의 눈에 들어온 것은 휴대폰을 든 태오의 왼쪽 손목이었습니다. 소매 밑으로 시퍼런 멍이 보였습니다. 넘어져서 생긴 멍이 아니었습니다. 누군가에게 아주 세게 붙잡힌 자국이었습니다. 오십 년 장사를 하며, 할머니는 그런 멍을 여러 번 보았습니다.

{c042}

그리고 할머니는 알고 있었습니다. 시장 앞 편의점에서, 밤 열한 시만 되면 혼자 삼각김밥을 먹는 키 큰 아이를. 늘 같은 자리, 늘 같은 삼각김밥, 늘 혼자. 할머니는 그 아이가 누구인지 오늘에야 알았습니다. 사람 보는 눈만큼은, 할머니는 누구에게도 지지 않았습니다.

{c043}

할머니는 하린이 옆에 쪼그리고 앉았습니다. 그리고 바닥에 흩어진 반찬을, 맨손으로 한 점 한 점 도시락에 주워 담았습니다. 하린이가 울먹이며 말렸지만, 할머니는 멈추지 않았습니다.

{c044}

마지막 계란말이 한 조각까지 주워 담은 뒤, 할머니가 조용히 입을 열었습니다.

"얘야. 밥은 던지는 게 아니에요. 나는 그 밥 한 그릇이 없어서, 학교를 못 다녔어요."

교실이 조금 조용해졌습니다.

{c045}

태오가 코웃음을 쳤습니다.

"그래서 뭐요? 그게 저랑 무슨 상관인데요?"

{c046}

할머니가 천천히 일어섰습니다. 태오의 가슴께에도 닿지 않는 작은 키였습니다. 그런데 할머니는 고개를 들어, 태오의 눈을 똑바로 바라보았습니다. 목소리는 크지 않았지만, 교실 끝까지 또렷하게 들렸습니다.

"상관이 있지요. 어제 저녁, 시장 골목에서 네가 우는 걸 봤거든."

{c047}

태오의 얼굴이 굳었습니다. 어제 저녁, 시장 뒷골목. 아무도 없는 줄 알았던 그곳에서, 태오는 교복 소매로 눈물을 훔치고 있었습니다. 할머니의 가게는, 바로 그 골목 끝에 있었습니다.

"밤마다 불 꺼진 빈집에 들어가는 애가, 왜 남의 밥을 엎는지. 할미는 알아요. 배가 고픈 게 아니라, 마음이 고픈 거지."

{c048}

태오는 아무 말도 하지 못했습니다. 늘 비웃음을 달고 있던 입이 굳게 닫혔습니다. 휴대폰을 든 손이 천천히, 아래로 내려갔습니다.

{c049}

교실에는 숨소리 하나 들리지 않았습니다. 학교에서 아무도 건드리지 못하던 강태오가, 일흔한 살 할머니 앞에서 처음으로 고개를 떨군 것이었습니다.

{c050}

할머니가 손가락 세 개를 펴 보이며 빙그레 웃었습니다.

"내일부터 할미가 도시락을 세 개 싸 올게요. 하나는 하린이 것, 하나는 내 것. 그리고 하나는, 네 것이다."

## 5. 도시락 세 개

{c051}

그 모든 장면을, 교실 문밖에서 지켜본 사람이 있었습니다. 담임 박진수 선생님이었습니다. 박 선생님은 오랫동안 그 자리에 서 있었습니다. 교사가 된 지 이십 년. 언제부터 아이들의 성적만 보고, 아이들의 얼굴은 보지 않게 되었는지 생각했습니다.

{c052}

그날 밤, 박 선생님은 교무실에 혼자 남았습니다. 반 아이 하나가 몰래 보내 준 태오 무리의 영상들을 하나하나 확인했습니다. 몇 달 동안 계속된 괴롭힘이었습니다. 박 선생님은 밤늦게까지 보고서를 썼습니다. 그동안 아무도 하지 못한 일이었습니다.

{c053}

다음 날 새벽 세 시. 할머니는 시장에 나가기 전, 부엌에 불을 켰습니다. 계란 열 개를 풀어 계란말이를 부치고, 멸치를 볶고, 김치를 썰었습니다. 도시락 세 개가 나란히 놓였습니다. 할머니는 가장 큰 도시락에 계란말이를 두 줄 더 넣었습니다.

{c054}

아침에 교실에 들어서니, 할머니 책상 위에 꼬깃꼬깃 접힌 쪽지가 놓여 있었습니다. 삐뚤빼뚤한 글씨였습니다.

반찬은 계란말이로 해 주세요. 태오.

할머니는 소리 없이 웃었습니다. 이미 넣어 왔으니까요.

{c055}

할머니는 쪽지를 교복 주머니에 소중히 넣었습니다. 그리고 가방에서 알록달록한 보자기에 싼 도시락 세 개를 꺼냈습니다. 하린이가 할머니를 보며 처음으로 환하게 웃었습니다. 가장 큰 도시락 하나는, 아무 말 없이 태오의 사물함 위에 올려 두었습니다.

{c056}

점심시간, 태오는 도시락을 들고 사라졌습니다. 아무도 없는 옥상이었습니다. 태오는 보자기를 풀고 계란말이 하나를 입에 넣었습니다. 따뜻한 맛이었습니다. 엄마가 해 준 밥을 먹어 본 게 언제였는지, 태오는 기억나지 않았습니다. 태오는 계란말이를 꼭꼭 씹으며, 소매로 몇 번이나 눈가를 훔쳤습니다.

{c057}

수업이 끝난 복도에서, 박 선생님이 할머니 앞에 섰습니다. 그리고 처음으로 고개를 숙였습니다.

"첫날 드린 말씀, 사과드립니다. 학교가 경로당이 아니라고 했지요. 오늘 보니, 제가 선생 자격이 없었습니다."

할머니는 손사래를 치며 웃었습니다. "아이고, 선생님. 그런 말 마세요. 내일은 선생님 도시락도 하나 싸 올까요?"

{c058}

그날 저녁, 할머니와 하린이는 나란히 하교했습니다. 벚꽃이 비처럼 떨어지는 길이었습니다. 하린이는 쉬지 않고 재잘거렸고, 할머니는 그 이야기를 하나도 빠짐없이 들어 주었습니다. 칠십 년 만에 생긴, 학교 친구였습니다. 하지만 행복은 오래가지 않았습니다.

## 6. 학부모회장

{c059}

그날 오후, 교장실 문이 거칠게 열렸습니다. 명품 정장에 진주 목걸이를 한 여자. 태오의 어머니이자 학부모회장인 오정희였습니다. 박 선생님의 보고서가 올라갔다는 소식을 들은 것이었습니다.

"우리 애가 학교 폭력이라니요? 그 시장 노인네가 우리 애를 협박했다면서요?"

{c060}

교장은 출장 중이었고, 대신 최 교감이 허리를 굽실거리며 오정희를 맞았습니다.

"아이고, 회장님. 오셨습니까. 제가 다 알아서 처리하겠습니다. 걱정 마십시오."

{c061}

최 교감은 학교에서 오정희와 가장 가까운 사람이었습니다. 오정희가 학교 발전 기금이라며 내는 돈의 상당 부분이, 이상하게도 최 교감의 주머니로 흘러 들어가고 있었습니다. 학교의 오래된 비밀이었습니다. 최 교감은 오정희가 건넨 두툼한 봉투를 등 뒤로 슬쩍 감추며 웃었습니다.

"그 노인네, 원래 받으면 안 되는 학생이었습니다. 이번 기회에 정리하지요."

{c062}

그날 밤, 학부모 단톡방이 시끄러워졌습니다. 오정희가 올린 글이었습니다. 나이 든 학생 때문에 우리 아이들의 학습권이 침해받고 있습니다. 시장 냄새가 나서 수업에 집중이 안 된다고 합니다. 노인이 학생을 협박까지 했습니다. 서명에 동참해 주세요. 서명은 하룻밤 사이에 백 명이 넘었습니다.

{c063}

다음 날부터 학교의 공기가 달라졌습니다. 복도를 지나가면 학부모들이 수군거렸습니다. 다른 반 아이들은 할머니를 피해 돌아갔습니다. 냄새난다며 코를 막는 아이도 있었습니다. 할머니는 그래도 고개를 숙이지 않았습니다. 그저 묵묵히 수업을 들었습니다.

{c064}

토요일 오후, 오정희는 시장까지 찾아왔습니다. 할머니의 생선 가게 앞에서 그녀는 손가락질을 하며 소리쳤습니다.

"여기서 생선이나 파실 분이 왜 남의 애 학교에 와서 난리세요? 나이를 드셨으면 나잇값을 하셔야죠!"

{c065}

오정희는 손수건으로 코를 막고 비웃었습니다.

"아유, 비린내. 이런 냄새를 풍기면서 교실에 앉아 계시니, 애들이 공부가 되겠어요?"

{c066}

시장 상인들이 하나둘 모여들었습니다. 할머니는 이 시장에서 이십 년 동안 상인회장을 지낸 사람이었습니다. 생선 가게 김 씨 할아버지가 소매를 걷어붙였습니다. "이 양반이 누구 앞에서 행패야!" 상인들의 얼굴이 붉어졌습니다.

{c067}

그때, 할머니가 손을 들어 상인들을 말렸습니다.

"됐어요. 손님은 손님이에요. 내 가게 앞에서 싸움 나면, 우리 시장 이름만 버려요."

그리고 오정희에게 고개를 숙였습니다. "어머님 마음, 알아요. 자식 일이니까요. 그런데 한 가지만 물어봅시다. 태오가 저녁을 어디서 먹는지는, 아세요?"

오정희의 얼굴이 순간 굳었습니다. 그녀는 대답 없이 돌아섰습니다.

{c068}

그 모든 것을, 시장 기둥 뒤에 숨어서 지켜본 아이가 있었습니다. 태오였습니다. 태오는 주먹을 꽉 쥐었습니다. 엄마가 할머니에게 소리치는 모습을, 할머니가 엄마에게 고개를 숙이는 모습을, 태오는 다 보고 있었습니다.

{c069}

그날 밤, 넓고 텅 빈 아파트 거실. 오정희는 태오의 왼쪽 손목을 붙잡고 다그쳤습니다.

"너 그 노인네 도시락 먹었다면서? 창피한 줄도 몰라? 너는 내 말만 들으면 돼. 선도위원회에서 그 노인한테 협박당했다고 말해. 알았어?"

태오의 손목에 있던 멍은, 바로 그 손이 만든 것이었습니다. 아버지는 해외 현장에 나가 일 년에 두 번 집에 들어왔고, 엄마는 늘 성적표와 체면만 보았습니다.

{c070}

태오는 불 꺼진 방바닥에 무릎을 끌어안고 앉았습니다. 바닥에는 할머니가 도시락을 쌌던 알록달록한 보자기가 놓여 있었습니다. 태오는 그 보자기를 손에 꼭 쥐고, 밤새 잠들지 못했습니다.

{c071}

월요일 아침, 게시판에 통지문이 붙었습니다. 선도위원회 소집. 대상, 1학년 3반 김말순. 이유, 학생 협박 및 수업 방해. 결과에 따라 퇴학 처분이 내려질 수 있습니다. 태오 무리의 괴롭힘 보고서는, 어디에도 없었습니다. 최 교감이 서랍 속에 넣어 버린 것이었습니다.

{c072}

텅 빈 방과 후 교실에서, 하린이가 할머니 손을 잡고 울었습니다.

"할머니, 저 때문이에요. 저 때문에 할머니가 쫓겨나시면 어떡해요."

할머니는 하린이의 머리를 쓰다듬었습니다. "울지 마요. 할미는 칠십 년 동안, 쫓겨나 본 적은 많아도 도망친 적은 없어요."

{c073}

그날 밤, 할머니는 툇마루에 앉아 달을 보았습니다. 무릎 위에는 곱게 갠 교복이 놓여 있었습니다. 겨우 한 달 입은 교복이었습니다. 할머니는 그 교복을 쓰다듬으며 생각했습니다. 내가 여기서 물러나면, 하린이는 다시 혼자가 된다. 그리고 태오는, 영영 그 빈집에 갇히겠지.

{c074}

할머니는 방에 들어가 낡은 나무 상자를 꺼냈습니다. 그 안에는 누렇게 바랜 사진 한 장이 있었습니다.

{c075}

사십 년 전 사진이었습니다. 소년원 식당에서 밥을 먹는 까까머리 아이들. 그중 한 아이가 카메라를 보고 있었습니다. 왼쪽 눈썹에 작은 흉터가 있는 아이였습니다. 할머니는 그 아이의 얼굴을 손가락으로 가만히 쓰다듬었습니다. 잘 살고 있으려나.

## 7. 선도위원회

{c076}

선도위원회가 열리는 날, 아침부터 비가 내렸습니다. 회의실에는 긴 탁자가 놓였고, 교사들과 학부모 대표들이 줄지어 앉았습니다.

{c077}

가운데 자리에는 최 교감이 앉았습니다. 그리고 그 옆에는, 학부모 대표 자격으로 오정희가 앉아 있었습니다. 팔짱을 낀 오정희의 입가에는 이미 이긴 사람의 미소가 걸려 있었습니다.

{c078}

할머니는 그들과 마주 보고, 의자 하나에 홀로 앉았습니다. 두 손을 무릎 위에 가지런히 모으고, 허리를 꼿꼿이 폈습니다. 오늘도 빨간 리본을 단정하게 매고 있었습니다.

{c079}

최 교감이 서류를 읽어 내려갔습니다.

"김말순 학생은 같은 반 강태오 학생을 공개적으로 모욕하고 협박하였으며, 학부모 백이십 명이 학습권 침해를 이유로 퇴학을 요청하였습니다. 또한 특별 전형으로 입학한 학생으로서 학교의 명예를 떨어뜨렸습니다."

{c080}

오정희가 벌떡 일어나 손가락질을 했습니다.

"이 노인네가 우리 애를 협박했어요! 애들 앞에서 우리 애 사생활을 떠벌리고, 우리 애가 무서워서 밤에 잠도 못 자요! 당장 내보내 주세요!"

{c081}

할머니는 아무 말도 하지 않았습니다. 그저 눈을 내리깔고, 조용히 듣고 있었습니다. 최 교감이 물었습니다. "김말순 학생, 할 말 있습니까?" 할머니는 고개를 저었습니다.

"없어요. 다만 한 가지만요. 그 도시락 세 개는, 내일도 싸 오고 싶어요."

최 교감이 피식 웃었습니다. "그럼 표결하겠습니다."

{c082}

바로 그때였습니다. 회의실 문이 벌컥 열렸습니다. 숨을 헐떡이며 들어온 아이는, 하린이였습니다. 비에 젖은 안경 너머로, 작은 눈이 떨리고 있었습니다.

{c083}

"잠깐만요! 할머니는 아무 잘못 없어요!"

하린이는 휴대폰을 높이 들었습니다. 목소리가 떨렸지만, 처음으로 고개를 들고 있었습니다.

"저는 석 달 동안 태오한테 괴롭힘을 당했어요. 아무도 안 도와줬어요. 선생님들도요. 할머니만, 할머니만 제 편이 되어 주셨어요. 여기 다 있어요. 태오가 찍은 영상이요."

{c084}

그리고 하린이 뒤로, 1학년 3반 아이들이 하나둘 들어왔습니다. 그동안 모른 척하던 아이들이었습니다. 아이들은 저마다 휴대폰을 들고 있었습니다. 자기들이 몰래 찍어 둔 영상, 받은 메시지, 그리고 할머니가 하린이를 감싸던 그날의 영상이었습니다.

"저희도 증언할게요."
"할머니가 협박한 거 아니에요. 저희가 다 봤어요."

{c085}

박 선생님이 앞으로 나섰습니다. 그리고 두꺼운 서류 뭉치를 탁자 위에 내려놓았습니다.

"제가 한 달 전에 올린 학교 폭력 보고서입니다. 원본은 교감 선생님 서랍에 있을 겁니다. 그래서 사본을 따로 챙겨 두었습니다."

{c086}

최 교감의 얼굴이 시뻘게졌습니다. 그는 탁자를 손바닥으로 내리쳤습니다.

"다들 조용히 하세요! 지금 이게 무슨 짓입니까! 학생들은 당장 나가요! 박 선생, 당신 징계받고 싶어요?"

{c087}

그때, 열린 문 앞에 또 한 사람이 서 있었습니다. 비에 흠뻑 젖은 태오였습니다. 태오는 회의실 한가운데에 앉은 엄마를 똑바로 바라보았습니다.

{c088}

태오가 천천히 왼쪽 소매를 걷어 올렸습니다. 손목의 시퍼런 멍이 모두에게 보였습니다.

"할머니는 저를 협박한 적 없어요. 저한테 도시락을 싸 주셨어요. 하린이를 괴롭힌 건 저예요. 제가 잘못했어요. 그리고, 이 멍은, 엄마가 만든 거예요."

태오의 눈에서 눈물이 쏟아졌습니다.

"엄마, 나 엄마가 해 준 밥 먹고 싶었어. 그냥 그거면 됐는데."

{c089}

오정희의 얼굴이 하얗게 질렸습니다. 명품 가방을 쥔 손이 떨렸습니다. 회의실에 있던 모든 사람의 시선이, 이제 그녀에게 향해 있었습니다.

{c090}

그 순간, 오정희가 이성을 잃었습니다. 그녀는 벌떡 일어나 할머니에게 달려들며 손을 높이 치켜들었습니다.

"다 당신 때문이야! 당신이 우리 애한테 무슨 짓을 한 거야!"

{c091}

할머니는 피하지 않았습니다. 오히려 두 팔을 벌려, 태오의 앞을 막아섰습니다. 그리고 눈을 감았습니다. 일흔한 해를 살며 맞아 본 매는 셀 수도 없었습니다. 한 대쯤 더 맞는 건 아무것도 아니었습니다. 이 아이만 다치지 않는다면요.

## 8. 어머니

{c092}

바로 그 순간, 회의실 양쪽 문이 활짝 열렸습니다. 남색 양복을 입은 키 큰 남자가 서 있었습니다. 손에는 얇은 검은 서류철을 들고 있었고, 뒤에는 직원 두 명이 따라와 있었습니다.

"교육청 장학관 정민호입니다. 이 학교 발전 기금 횡령과 학교 폭력 은폐 신고가 들어와서 왔습니다."

{c093}

최 교감이 의자에서 튕기듯 일어났습니다. 얼굴이 새파랗게 질렸습니다.

"자, 장학관님! 미리 연락이라도 주시지, 어, 어쩐 일로."

{c094}

하지만 장학관은 교감을 쳐다보지도 않았습니다. 그는 곧장 회의실을 가로질러 걸어갔습니다. 그리고 태오 앞을 막아선, 작은 할머니 앞에 멈춰 섰습니다. 장학관의 왼쪽 눈썹에는, 작은 흉터가 있었습니다. 장학관의 눈이 떨렸습니다.

{c095}

그리고 그는, 모두가 보는 앞에서 할머니에게 허리를 깊이 숙였습니다.

"어머니. 저 민호입니다. 시장 생선 가게 뒤에서, 어머니가 국밥 먹여 주던 민호요."

회의실이 얼어붙었습니다. 오정희의 치켜든 손이, 허공에서 멈췄습니다.

{c096}

사십 년 전 겨울이었습니다. 눈이 펑펑 내리던 밤, 시장 생선 가게 뒤에 열다섯 살 소년이 웅크리고 있었습니다. 소년원에서 막 나온 아이였습니다. 갈 곳도, 먹을 것도, 기다려 주는 사람도 없었습니다. 배가 고파 시장에서 생선을 훔치다 붙잡힌 참이었습니다.

{c097}

그 아이를 경찰에 넘기는 대신, 젊은 말순은 따뜻한 국밥 한 그릇을 내밀었습니다.

"먹어라. 훔치는 건 배가 고파서지, 네가 나빠서가 아니다. 배부르면 안 훔친다."

소년은 그날 밤, 울면서 국밥을 먹었습니다. 그리고 그날부터 일 년 동안, 매일 생선 가게 뒤에서 말순이 차려 준 밥을 먹었습니다.

{c098}

젊은 말순은 거기서 멈추지 않았습니다. 장사가 끝나면 커다란 솥 두 개를 들고 소년원을 찾아갔습니다. 아이들에게 밥을 해 먹이고, 이름을 불러 주고, 글을 모르는 자신 대신 아이들에게 책을 읽어 달라고 했습니다. 그 일을 십 년 동안 했습니다. 아무에게도 말하지 않고요. 그 아이들 중 하나가 검정고시를 보고, 대학에 가고, 선생님이 되고, 지금은 교육청 장학관이 되었습니다.

{c099}

장학관이 한쪽 무릎을 꿇고, 할머니의 거친 손을 두 손으로 감쌌습니다.

"어머니가 안 계셨으면, 저는 지금 여기 없습니다. 만학도 특별 전형 명단에서 어머니 이름을 보고, 제 눈을 의심했습니다. 어머니, 글을 배우고 싶으셨으면 저한테 말씀하시지 그러셨어요."

할머니가 눈물이 그렁그렁한 채 웃었습니다.

"민호야. 너 잘 컸구나. 그거면 됐다. 공부는 내가 해야지, 네가 대신 해 주면 그게 공부냐."

{c100}

장학관이 천천히 일어섰습니다. 그리고 최 교감 앞으로 걸어가, 검은 서류철을 펼쳤습니다.

"최 교감님. 지난 오 년간 학교 발전 기금 중 삼억 이천만 원이 교감님 가족 명의 계좌로 들어갔더군요. 그리고 한 달 전 올라온 학교 폭력 보고서를 고의로 숨기셨습니다. 오늘부로 직무에서 물러나 주셔야겠습니다. 조사는 경찰과 함께 진행하겠습니다."

{c101}

최 교감은 털썩 의자에 주저앉았습니다. 오정희의 얼굴에서도 핏기가 사라졌습니다. 그 돈을 건넨 사람이 누구였는지, 서류에 모두 적혀 있었으니까요. 학부모회장 자리도, 백이십 명의 서명도, 이제 아무 소용이 없었습니다.

{c102}

오정희는 아들을 바라보았습니다. 비에 젖은 채 울고 있는 아들. 손목의 멍. 엄마가 해 준 밥이 먹고 싶었다는 말. 그녀의 화장이 눈물로 번졌습니다. 그녀가 천천히, 이번에는 아주 조심스럽게 아들에게 손을 뻗었습니다. 태오의 손목이 아니라, 손을 잡기 위해서였습니다.

{c103}

할머니가 다가가 오정희의 떨리는 손을 가만히 잡았습니다.

"어머님. 늦지 않았어요. 오늘 저녁에 계란말이 하나 부쳐 주세요. 그게 다예요. 애들은 그거 하나면 돼요."

오정희는 할머니의 거친 손을 붙잡고, 아이처럼 소리 내어 울었습니다. 창밖에서는 어느새 비가 그쳐 있었습니다.

## 9. 칠십삼 년 만의 졸업장

{c104}

그날 이후, 학교는 조금씩 달라졌습니다. 최 교감은 학교를 떠났고, 학교 폭력 보고서는 제대로 처리되었습니다. 태오는 하린이에게 진심으로 사과했고, 봉사 활동을 하며 벌을 받았습니다. 그리고 여름이 가고, 가을이 가고, 세 번의 겨울이 지났습니다.

{c105}

그동안 할머니의 도시락은 하루도 빠지지 않았습니다. 하린이 것, 할머니 것, 태오 것. 가끔은 박 선생님 것까지. 태오는 점심시간마다 할머니 옆에서 계란말이를 먹으며, 할머니에게 영어 단어를 가르쳐 주었습니다. 하린이는 반장이 되었고, 태오는 그런 하린이를 제일 먼저 도와주는 친구가 되었습니다. 아이들은 어느새 할머니를 이렇게 불렀습니다. 말순 쌤.

{c106}

그리고 삼 년 뒤, 졸업식 날이 왔습니다. 강당은 꽃다발과 박수 소리로 가득 찼습니다.

{c107}

할머니는 단상 아래에 서 있었습니다. 큰아들이 사 준 커다란 꽃다발을 안고 있었습니다. 객석에는 입학을 반대했던 큰아들이, 손주들과 함께 눈물을 닦고 있었습니다. 할머니의 다리가 조금 떨렸습니다. 일흔네 살. 아홉 살에 담장 너머로 바라보던 학교에서, 마침내 졸업을 하는 날이었습니다.

{c108}

"졸업생 대표, 김말순."

이름이 불리자, 하린이와 태오가 양쪽에서 할머니의 손을 잡았습니다. 그리고 그 뒤로, 3학년 아이들 전부가 따라 일어섰습니다. 아이들은 할머니를 둘러싸고 함께 단상에 올랐습니다. 강당이 박수 소리로 떠나갈 듯했습니다.

{c109}

졸업장을 건넨 사람은 교육청 장학관, 정민호였습니다. 그는 두 손으로 졸업장을 내밀며 말했습니다.

"어머니, 졸업 축하드립니다. 이번엔 제가 밥을 사 드릴게요."

할머니는 두 손으로 졸업장을 받았습니다. 거칠고 갈라진, 오십 년 동안 생선을 손질한 손이었습니다.

{c110}

할머니는 졸업장을 가슴에 꼭 안고 눈을 감았습니다. 아홉 살의 말순이 담장 너머에서 웃고 있는 것만 같았습니다.

"칠십 년 걸렸네. 그래도, 왔다."

{c111}

그날, 교문에는 벚꽃이 비처럼 내렸습니다. 삼 년 전 할머니가 처음 걸어 들어왔던 그 길이었습니다. 배우는 데에는 늦은 나이가 없고, 사람을 품는 데에는 정해진 자리가 없다는 것. 교복 입은 할머니가, 그 학교에 남기고 간 가장 큰 공부였습니다."""


def main():
    cmd, folder = sys.argv[1], sys.argv[2]
    chars = {c["name"]: c for c in json.load(open(os.path.join(HERE, "등장인물.json"), encoding="utf-8"))["chars"]}
    if cmd == "job":
        items = []
        for cid, who, desc, _ in CUTS:
            keep_desc_outfit = any(k in desc for k in NO_UNIFORM)
            looks = "; ".join(f"person {k + 1} (the character from reference image {k + 1}): {chars[nm]['look']}"
                              + ("" if keep_desc_outfit or not chars[nm].get("outfit") else ", " + chars[nm]["outfit"])
                              for k, nm in enumerate(who))   # 한글 이름은 그림에 글자로 나올 수 있어 번호로
            items.append({"id": cid, "width": 1024, "height": 576, "seed": 100 + int(cid[1:]),
                          "refs": [os.path.join(HERE, chars[nm]["face"]) for nm in who],
                          "prompt": f"{STYLE}, Korean high school drama. "
                                    + (f"Characters: {looks}. Each person appears only once, exactly two arms and two legs. " if looks else "No main characters. ")
                                    + f"Scene: {desc}. Cinematic composition, full-bleed image, no border, no frame, no paper edges. No speech bubbles, no text, no letters."})
        os.makedirs(folder, exist_ok=True)
        json.dump({"items": items}, open(os.path.join(folder, "job.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(len(items), "cuts")
    elif cmd == "project":
        story = STORY
        for cid, _, _, cap in CUTS:
            story = story.replace("{" + cid + "}", f"[사진: {os.path.join(folder, cid + '.png')} | {cap} | AI 생성 그림 (FLUX.2 klein) | ]")
        proj = {"ver": 7, "category": "장문", "genre": "[이야기] 미니드라마(복수·반전)", "topic": "전학 온 할머니", "title": TITLE,
                "story": story, "sources": [], "notes": "미니드라마 스타일 애니 단편 《전학 온 할머니》 (약 30분)", "autophoto": False, "img_source": "그림: 애니 일러스트",
                "cast": [{"name": nm, "look": c["look"], "look_ko": c["look_ko"],
                          **({"sheet": os.path.join(HERE, c["face"])} if c.get("face") else {})} for nm, c in chars.items()],
                "settings": {"format": "롱폼 가로(1920×1080)", "narration": "on",   # 새 PC·서버 기본값(나레이션 꺼짐·스크롤형) 대신 장문 설정 그대로
                             "layout": "자막형(큰 제목+사진+자막)", "img_fill": "전체 화면(글자가 사진 위에)",
                             "img_motion": "영상처럼(확대·이동·전환)", "fps": "24", "reveal_hit": "off", "reveal_fx": "off",
                             "head_show": "안 보임(제목 카드만)", "sub_split": "한 줄씩(문장·쉼표로 나눠 차례로)", "img_label": "off",   # 규칙: 위 큰 제목·장면 설명 없이, 자막은 한 줄씩
                             "narr_voice": "Supertonic M2 (남성, 무료 로컬) [supertonic:M2]",   # 성우 샘플 1번 (사용자가 고름)
                             "narr_rate": "0", "narr_tone_m": 0.0}}
        out = os.path.join(HERE, "전학온할머니_단편.json")
        json.dump(proj, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(out, len(story), "chars")


if __name__ == "__main__":
    main()
