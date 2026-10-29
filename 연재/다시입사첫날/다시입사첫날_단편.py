"""《다시, 입사 첫날》 단편 (약 30분, 미니드라마 스타일 애니 — 회귀 복수극, 한 편으로 끝남) — 대본 + 컷별 그림 계획
python 연재/다시입사첫날/다시입사첫날_단편.py job <저장폴더>   → 그림 주문서(klein_worker 용) job.json
python 연재/다시입사첫날/다시입사첫날_단편.py project <그림폴더> → 프로젝트 파일(render_project 용) 연재/다시입사첫날/다시입사첫날_단편.json
  영상은 render_project.py <프로젝트> --대본그대로 (오프닝·대본을 프로그램이 고쳐 쓰지 않게)
대본의 {컷번호} 자리에 그 컷 그림이 들어감. chars = 그 컷에 나오는 인물(캐릭터 시트를 기준 그림으로 넣음)
나레이션 한 명(남자 성우 2)이 대사까지 모두 읽음 (사용자 결정) → DIALOGUE 없음
회사·사람 이름은 모두 지어낸 것 (세운물산, 동진식품, 하늘무역)"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TITLE = "다시, 입사 첫날"

# 화풍: 일본 애니풍 캐릭터 (사용자 결정, 화풍샘플/사용자_캐릭터스타일.png)
STYLE = ("Japanese anime style scene, TV anime screenshot, clean crisp line art, anime cel shading with soft shadows, "
         "realistic human proportions, natural colors, detailed anime background art")

OLD = "aged 32 in the future, looking ten years older and exhausted with dark circles and light stubble, wearing a wrinkled gray office suit with a loosened tie instead of his usual outfit"
OLD_PARK = "aged 50 in the future, ten years older with gray streaks in his slicked-back hair, wearing a black suit instead of his usual outfit"
CUSTOM_OUTFIT = "instead of his usual outfit", "instead of her usual outfit"   # 이런 컷은 평소 옷 묘사를 붙이지 않음

# (컷번호, 나오는 인물, 그림 설명(영어), 화면 설명(한국어)) — 인물 옷·나이를 바꿀 땐 설명에 적음
CUTS = [
    # 오프닝
    ("c001", ["도윤"], f"night on an office building rooftop in heavy rain, the young man {OLD}, standing at the railing soaked, city lights below, lightning in the sky", "비 내리는 옥상에 선 서른두 살 도윤"),
    ("c002", [], "close-up of an old digital alarm clock on a bedside table showing a glowing display with abstract segments, no readable numbers, morning sunlight through curtains", "울리는 알람 시계"),
    ("c003", ["도윤"], "the young man in a new navy suit standing in front of a tall glass office tower in the morning, looking up with a sharp determined gaze, cherry blossom petals in the wind", "다시 선 입사 첫날의 회사 앞"),
    # 1. 누명
    ("c004", [], "a modern Korean corporate office floor at night, rows of desks, monitors glowing, empty chairs, cold blue light, rain on the windows", "2026년, 세운물산 사무실"),
    ("c005", ["도윤"], f"the young man {OLD}, working alone at his desk late at night surrounded by stacks of documents, rubbing his tired eyes", "밤늦게 혼자 일하는 도윤"),
    ("c006", ["박 과장"], f"the heavy-set man {OLD_PARK}, sitting in a leather chair in a private executive office, smiling smugly while signing a document, gold wristwatch shining", "박상철 부장"),
    ("c007", [], "close-up of an official document on a desk with a red approval stamp being pressed onto it, abstract printed lines, no readable letters", "도윤의 도장이 찍힌 결재 서류"),
    ("c008", [], "a large formal corporate audit meeting room with a long table, stern executives in suits seated, a projector screen glowing, tense atmosphere", "감사 회의"),
    ("c009", ["도윤"], f"the young man {OLD}, standing alone in front of a long table of executives in a meeting room, face pale, hands trembling", "누명을 쓴 도윤"),
    ("c010", ["준혁"], "the tall lanky man with glasses, aged 32 in the future with a tired face, wearing a gray office suit instead of his usual outfit, standing up in a meeting room, avoiding eye contact, guilty expression", "증언하는 동기 준혁"),
    ("c011", ["도윤"], f"close-up of the young man {OLD}, eyes wide with shock and betrayal, tears forming", "배신당한 도윤"),
    ("c012", ["박 과장"], f"the heavy-set man {OLD_PARK}, sitting at the meeting table hiding a smirk behind his hand", "몰래 웃는 박 부장"),
    ("c013", [], "a cardboard box with personal office items, a framed photo and a mug, placed on an empty desk, an ID badge with no readable letters lying beside it", "짐을 싼 상자"),
    ("c014", ["엄마"], "the small slim woman in her late fifties lying pale in a hospital bed wearing a hospital gown instead of her usual outfit, an IV drip beside her, weak gentle smile, dim night light", "병원에 누운 엄마"),
    ("c015", ["도윤", "엄마"], f"the young man {OLD}, kneeling beside a hospital bed holding the hand of the small woman in a hospital gown, crying, night hospital room", "엄마 손을 잡은 도윤"),
    ("c016", ["도윤"], f"the young man {OLD}, on a dark office building rooftop in heavy rain, looking up at the stormy sky with tears and rain on his face, lightning", "\"한 번만, 다시 돌아갈 수 있다면\""),
    ("c017", [], "a blinding white flash of lightning striking near a rooftop at night, the whole frame filled with white light and rain streaks", "번쩍이는 번개"),
    # 2. 다시, 입사 첫날
    ("c018", ["도윤"], "the young man aged 22 waking up suddenly in a small old bedroom in the morning, wearing a plain gray T-shirt instead of his usual outfit, sitting up in bed with a shocked face, sunlight", "눈을 뜬 도윤"),
    ("c019", [], "close-up of an old 2016-style smartphone on a bedside table, its lock screen glowing with abstract shapes, no readable numbers or letters", "2016년 3월 2일"),
    ("c020", ["도윤"], "the young man aged 22 wearing a plain gray T-shirt instead of his usual outfit, staring at his young face in a small bathroom mirror, touching his cheek in disbelief", "스물두 살의 얼굴"),
    ("c021", ["엄마"], "the small slim woman in a lavender cardigan with an apron, cooking soybean paste stew in a small cozy old Korean kitchen in the morning, healthy and smiling, steam rising", "부엌에서 찌개를 끓이는 엄마"),
    ("c022", ["도윤", "엄마"], "the young man wearing a plain gray T-shirt instead of his usual outfit, hugging his surprised mother tightly from behind in a small kitchen, crying, morning light", "엄마를 끌어안은 도윤"),
    ("c023", ["도윤", "엄마"], "the young man in a navy suit holding his mother's hands at the front door of a small old apartment, speaking earnestly, the mother smiling and nodding", "건강검진을 약속받는 도윤"),
    ("c024", [], "the glass entrance lobby of a large modern Korean corporate tower in the morning, many employees in suits walking in, a big company logo shape with no readable letters", "세운물산 본사"),
    ("c025", ["도윤", "박 과장"], "inside an office elevator, the heavy-set man in a gray three-piece suit smiling fakely and patting the shoulder of the young man in a navy suit, the young man smiling politely with cold eyes", "엘리베이터에서 마주친 박 과장"),
    ("c026", ["박 과장"], "close-up of the heavy-set man in a gray three-piece suit with a smug fake smile, holding out a credit card, elevator", "\"신입, 커피 좀 사 와\""),
    ("c027", ["도윤"], "close-up of the young man in a navy suit with a calm polite smile, but his eyes are sharp and cold, elevator light", "웃는 얼굴 뒤의 눈빛"),
    ("c028", ["준혁", "도윤"], "a new employee orientation room, the tall lanky young man with glasses and a crooked red tie cheerfully waving and sitting down next to the young man in a navy suit, other new employees around", "다시 만난 동기 준혁"),
    ("c029", ["도윤"], "close-up of the young man in a navy suit looking at someone beside him with complicated emotions, a mix of sadness and resolve", "복잡한 도윤의 마음"),
    ("c030", ["유나"], "the slender woman in a beige blazer with her hair in a low bun walking down an office hallway holding a stack of audit files, calm intelligent face", "감사팀 서유나 선배"),
    ("c031", ["유나"], f"faded blue-toned memory: the slender woman, aged 37 in the future, wearing a gray coat instead of her usual outfit, carrying a box of her belongings out of an office alone, sad face", "원래 미래의 유나"),
    # 3. 첫 기획안
    ("c032", ["도윤"], "the young man in a navy suit typing fast on a laptop at a desk late at night in an empty office, documents and charts on the screen with no readable text", "밤새 기획안을 쓰는 도윤"),
    ("c033", [], "close-up of a laptop screen showing a business plan slide with a map of Southeast Asia and abstract charts, no readable letters", "동남아 냉동 물류 기획안"),
    ("c034", ["박 과장", "도윤"], "the heavy-set man in a gray three-piece suit taking a document file from the young man in a navy suit at the young man's desk, grinning, the young man handing it over calmly", "기획안을 받아 가는 박 과장"),
    ("c035", ["도윤"], "the young man in a navy suit clicking send on an email on his laptop with a small knowing smile, office desk, evening", "몰래 보낸 메일 한 통"),
    ("c036", [], "a large corporate conference room with a big screen, executives seated around a long table, morning light, formal atmosphere", "임원 보고 회의"),
    ("c037", ["박 과장"], "the heavy-set man in a gray three-piece suit presenting proudly in front of a big screen in a conference room, gesturing confidently", "자기 기획안인 척 발표하는 박 과장"),
    ("c038", ["최 전무"], "the dignified silver-haired man in his sixties with black-rimmed glasses sitting at the head of a conference table, asking a sharp question, stern face", "날카롭게 묻는 최 전무"),
    ("c039", ["박 과장"], "the heavy-set man in a gray three-piece suit standing frozen in front of a presentation screen, sweating, eyes darting, stuttering", "말문이 막힌 박 과장"),
    ("c040", ["도윤"], "the young man in a navy suit standing up from a seat at the back of a conference room, raising his hand calmly, executives turning to look", "손을 든 신입 도윤"),
    ("c041", ["도윤"], "the young man in a navy suit explaining confidently in front of a presentation screen with charts, pointing at a map, executives listening intently", "막힘없이 답하는 도윤"),
    ("c042", ["최 전무"], "the dignified silver-haired executive looking at a tablet with an email on it, raising his eyebrows, then looking up with interest, conference room", "메일 날짜를 확인하는 최 전무"),
    ("c043", ["박 과장"], "close-up of the heavy-set man in a gray three-piece suit gritting his teeth with a red humiliated face, conference room", "얼굴이 시뻘게진 박 과장"),
    # 4. 동기
    ("c044", ["준혁"], "night in a dark narrow alley, the tall lanky young man with glasses being grabbed by the collar by two thuggish men in black jackets, scared face, dim street lamp", "사채업자에게 붙잡힌 준혁"),
    ("c045", ["도윤"], "the young man in a navy suit watching from the corner of a dark alley at night, clenched fist, serious face", "그 모습을 지켜본 도윤"),
    ("c046", [], "close-up of a crumpled loan contract paper with a red thumbprint and abstract printed lines, no readable letters, on a dark table", "아버지가 남긴 빚 계약서"),
    ("c047", ["박 과장", "준혁"], "in a quiet office pantry, the heavy-set man in a gray three-piece suit leaning toward the tall lanky young man with glasses with a sly smile, handing him a white envelope, the young man hesitating", "준혁에게 다가가는 박 과장"),
    ("c048", ["도윤", "준혁"], "a small Korean street food tent at night, the young man in a navy suit and the tall lanky young man with glasses sitting at a plastic table with soju glasses, the lanky one crying and covering his face", "포장마차에서 털어놓은 준혁"),
    ("c049", ["도윤", "유나", "준혁"], "a meeting room in a legal aid office, the slender woman in a beige blazer explaining documents to the tall lanky young man with glasses, the young man in a navy suit sitting beside them", "법률 상담을 함께 받는 세 사람"),
    ("c050", ["준혁"], "the tall lanky young man with glasses holding an official court document and crying with relief on a sunny street", "빚에서 벗어난 준혁"),
    ("c051", ["도윤", "준혁"], "the tall lanky young man with glasses hugging the young man in a navy suit on an office building rooftop on a sunny day, both smiling", "\"넌 내 동기니까\""),
    ("c052", ["박 과장"], "the heavy-set man in a gray three-piece suit tossing a white envelope into a trash bin angrily in an office pantry", "봉투를 내던지는 박 과장"),
    # 5. 냉동 새우
    ("c053", [], "a huge cold-storage logistics warehouse with stacks of frozen seafood boxes on pallets, forklifts, cold mist, fluorescent lights", "물류 창고"),
    ("c054", [], "faded blue-toned memory: a television news screen showing a supermarket product recall scene with abstract graphics, no readable letters", "원래 미래의 리콜 뉴스"),
    ("c055", ["도윤"], "the young man wearing a padded work jacket over his navy suit instead of his usual outfit, crouching in a cold warehouse opening a box of frozen shrimp and examining it, cold mist", "새우 상자를 열어 보는 도윤"),
    ("c056", [], "close-up of a temperature data logger device with a small screen showing an abstract graph line with a big spike, no readable numbers", "온도 기록계의 이상한 그래프"),
    ("c057", [], "close-up of frozen shrimp in a box with ice crystals and refrozen water marks, signs of thawing and refreezing, realistic", "녹았다 다시 언 흔적"),
    ("c058", ["박 과장", "도윤"], "in a cold warehouse, the heavy-set man in a gray suit and a long black coat shouting and pointing angrily at the young man in a padded work jacket, workers watching", "\"신입이 감히!\""),
    ("c059", ["도윤"], "the young man in a padded work jacket standing firm in a cold warehouse holding up a temperature logger, calm serious face, workers behind him", "출고를 멈춰 세운 도윤"),
    ("c060", [], "a food safety laboratory with a technician in a white coat looking into a microscope, sample dishes on the table", "세균 검사 결과"),
    ("c061", ["최 전무", "도윤"], "in an executive office, the dignified silver-haired executive shaking hands firmly with the young man in a navy suit, the executive smiling slightly for the first time", "최 전무의 악수"),
    ("c062", ["유나"], "the slender woman in a beige blazer at her desk in an audit office at night, looking at a spreadsheet on a monitor with abstract numbers, narrowing her eyes, a coffee cup beside her", "리베이트 단서를 찾은 유나"),
    # 6. 반격
    ("c063", ["박 과장"], "the heavy-set man in a gray three-piece suit sitting alone in a dark office at night, his face lit by a monitor, an evil cold expression, twisting his gold watch", "어둠 속의 박 과장"),
    ("c064", [], "close-up of a company personnel transfer notice on an office bulletin board with a red stamp, abstract printed lines, no readable letters", "지방 창고 발령 통지"),
    ("c065", ["박 과장"], "night outside a flashy nightclub with neon lights, the heavy-set man in a gray suit handing a corporate credit card to a staff member at the counter, smirking", "몰래 긁힌 법인카드"),
    ("c066", ["도윤"], "the young man in a navy suit walking down an office aisle while coworkers at their desks whisper and look at him with suspicion", "수군거리는 사무실"),
    ("c067", ["박 과장", "도윤"], "the heavy-set man in a gray three-piece suit leaning close to the young man in a navy suit in an office hallway, whispering threateningly with a cruel grin", "\"넌 끝났어\""),
    ("c068", ["도윤"], "close-up of the young man in a navy suit smiling calmly back, not intimidated at all, office hallway", "\"그 카드 쓰신 날짜, 기억하세요?\""),
    ("c069", ["엄마"], "the small slim woman wearing a hospital gown instead of her usual outfit, sitting in a bright hospital consultation room, a doctor in a white coat showing her a medical scan on a monitor", "엄마의 검진 결과"),
    ("c070", ["도윤"], "the young man in a navy suit sitting on a bench in a bright hospital hallway, covering his face with both hands and crying with relief", "병원 복도에서 터진 눈물"),
    ("c071", ["도윤", "엄마"], "the young man in a navy suit and his small mother in a lavender cardigan walking out of a hospital entrance together on a sunny day, the mother patting his back", "\"초기래, 수술하면 낫는대\""),
    # 7. 증거
    ("c072", ["도윤"], f"faded blue-toned memory: the young man {OLD}, looking at a bank account document in an audit room, his eyes fixed on it", "원래 미래에 본 계좌 하나"),
    ("c073", [], "close-up of a bank statement document with abstract columns of numbers and highlighted rows, no readable letters or numbers", "하늘무역의 돈 흐름"),
    ("c074", ["도윤", "유나"], "late night in a small audit office, the young man in a navy suit and the slender woman in a beige blazer leaning over a desk covered with documents and a laptop, focused", "밤샘 증거 모으기"),
    ("c075", ["유나"], "the slender woman in a beige blazer looking up from documents at the young man with a surprised, curious expression, office at night", "\"도윤 씨, 어떻게 이걸 알았어요?\""),
    ("c076", ["도윤"], "the young man in a navy suit smiling faintly and looking out a dark office window at the city lights, mysterious", "\"꿈에서 봤다고 하면, 믿으실래요?\""),
    ("c077", [], "a security office with many CCTV monitors showing a warehouse, one screen showing a man walking with a timestamp graphic made of abstract shapes, no readable numbers", "창고 CCTV"),
    ("c078", ["박 과장", "준혁"], "in a dark underground parking lot, the heavy-set man in a gray suit talking secretly to the tall lanky young man with glasses, the young man's hand in his pocket hiding a smartphone", "다시 준혁을 찾아온 박 과장"),
    ("c079", [], "close-up of a smartphone inside a suit jacket pocket with a red recording dot glowing, dark parking lot", "주머니 속 녹음 버튼"),
    # 8. 감사위원회
    ("c080", [], "a grand corporate boardroom with a long dark wood table, executives in suits seated, tall windows with city view, a big screen at the end, tense morning light", "감사위원회"),
    ("c081", ["박 과장"], "the heavy-set man in a gray three-piece suit sitting at a boardroom table with crossed arms and a victorious smug smile", "이겼다고 믿는 박 과장"),
    ("c082", ["도윤"], "the young man in a navy suit standing alone at the end of a long boardroom table facing many executives, back straight, calm face", "홀로 선 도윤"),
    ("c083", ["박 과장"], "the heavy-set man in a gray three-piece suit standing and holding up papers in a boardroom, accusing loudly with exaggerated anger", "\"신입 주제에 법인카드로 유흥을!\""),
    ("c084", ["도윤"], "the young man in a navy suit pressing a remote toward a big screen in a boardroom, calm, executives turning to look at the screen", "첫 번째 증거"),
    ("c085", [], "a big boardroom screen showing two side-by-side images: a CCTV image of a warehouse with a man in a work jacket and a nightclub receipt, abstract graphics, no readable text", "같은 시각, 창고 CCTV"),
    ("c086", ["박 과장"], "close-up of the heavy-set man in a gray suit with his smug smile freezing, a drop of sweat on his temple", "굳어 버린 미소"),
    ("c087", ["준혁"], "the tall lanky young man with glasses opening the boardroom door and stepping in nervously but bravely, holding up a smartphone", "문을 열고 들어온 준혁"),
    ("c088", [], "close-up of a smartphone on a boardroom table playing an audio recording, a waveform graphic on the screen, executives' hands around it", "녹음 파일"),
    ("c089", ["박 과장"], "the heavy-set man in a gray three-piece suit jumping up and pointing at someone, shouting desperately, face red, boardroom", "\"조작이야!\""),
    ("c090", ["유나"], "the slender woman in a beige blazer walking into a boardroom carrying a thick binder of audit documents, confident calm face", "감사팀 서유나"),
    ("c091", ["유나"], "the slender woman in a beige blazer placing a thick binder on the boardroom table and opening it, pointing at a page, executives leaning in", "하늘무역과 동진식품의 리베이트"),
    ("c092", ["최 전무"], "the dignified silver-haired executive slowly standing up at the head of the boardroom table, cold stern gaze, adjusting his black-rimmed glasses", "일어선 최 전무"),
    ("c093", [], "two Korean police detectives in plain suits with badges walking into a corporate boardroom through the open doors", "들어오는 수사관들"),
    ("c094", ["박 과장"], "the heavy-set man in a gray suit with his hands cuffed in front of him, being held by the arm, his slicked-back hair messed up, face pale, boardroom", "수갑을 찬 박 과장"),
    ("c095", ["박 과장", "도윤"], "the heavy-set man in handcuffs turning to glare at the young man in a navy suit with confused rage, the young man leaning close and whispering into his ear calmly", "\"10년 동안 기다렸거든요\""),
    ("c096", ["박 과장"], "the heavy-set man in a gray suit and handcuffs being led away down a corporate hallway between two detectives, employees watching from their desks", "끌려가는 박 과장"),
    # 9. 이번엔 지켰다
    ("c097", ["최 전무", "도윤"], "in an executive office with a city view, the dignified silver-haired executive handing a document folder to the young man in a navy suit, both standing, warm light", "새 사업팀을 맡기는 최 전무"),
    ("c098", ["도윤", "준혁", "유나"], "the young man in a navy suit, the tall lanky young man with glasses and the slender woman in a beige blazer standing together in front of a glass meeting room door with a new team sign made of abstract shapes, smiling", "새 팀의 세 사람"),
    ("c099", ["엄마"], "the small slim woman wearing a hospital gown instead of her usual outfit, sitting up in a bright hospital bed after surgery, smiling, flowers on the bedside table, sunlight", "수술을 마친 엄마"),
    ("c100", ["도윤", "엄마"], "the young man in a navy suit peeling an apple beside a bright hospital bed, the small mother in a hospital gown laughing, sunny hospital room", "엄마의 웃음"),
    ("c101", [], "a montage of a city through the seasons: summer rain, autumn red leaves on a street, winter snow on an office tower, no people in focus", "흘러간 일 년"),
    ("c102", ["도윤", "엄마"], "a small cozy old Korean kitchen in the morning, the healthy mother in a lavender cardigan with an apron handing a lunch box to the young man in a navy suit, both smiling", "엄마가 싸 준 도시락"),
    ("c103", ["도윤"], "the young man in a navy suit standing on an office building rooftop on a bright sunny spring day, wind in his hair, looking over the city with a peaceful smile, cherry blossom petals", "맑은 날의 옥상"),
    ("c104", [], "close-up of a new employee ID badge and a lanyard on a desk in sunlight, abstract photo and shapes, no readable letters", "다시 받은 사원증"),
    ("c105", ["도윤"], "the young man in a navy suit walking into a bright corporate lobby in the spring morning with a confident smile, new employees in the background", "두 번째 입사 첫날, 그 뒤"),
]

STORY = """{c001}

서른두 살 한도윤은 비 내리는 회사 옥상에 서 있었습니다. 횡령범이라는 누명, 배신한 동기, 그리고 병원에 누워 계신 엄마. 그날 밤, 도윤은 모든 것을 잃었습니다.

{c002}

그런데 다음 날 아침, 알람 소리에 눈을 뜬 도윤은 숨이 멎을 뻔했습니다. 2016년 3월 2일. 십 년 전, 바로 입사 첫날이었습니다.

{c003}

이번엔 다를 겁니다. 누가 자신을 배신하고, 누가 회사를 무너뜨리고, 엄마가 언제 쓰러지는지, 도윤은 전부 알고 있었으니까요.

## 1. 누명

{c004}

2026년 가을, 세운물산 본사. 밤 열한 시가 넘었는데도 사무실 한쪽에는 불이 켜져 있었습니다.

{c005}

해외 물류팀 한도윤 차장. 입사 십 년 차였습니다. 동기들 중 가장 먼저 승진했고, 가장 늦게 퇴근했습니다. 도윤이 만든 동남아 냉동 물류 사업은 회사의 효자 사업이 되었습니다. 하지만 그 공은 언제나, 한 사람의 이름으로 올라갔습니다.

{c006}

박상철 부장. 도윤이 입사한 날부터 그의 상사였던 사람. 도윤의 기획안은 박 부장의 이름으로 발표되었고, 도윤의 성과는 박 부장의 승진이 되었습니다. 그래도 도윤은 참았습니다. 엄마의 병원비가 있었으니까요.

{c007}

그러던 어느 날, 회사가 뒤집혔습니다. 해외 물류 대금 삼십억 원이 사라진 것이었습니다. 그리고 그 돈을 보낸 결재 서류에는, 도윤의 도장이 찍혀 있었습니다. 도윤은 그런 서류를 본 적도 없었습니다.

{c008}

감사 회의가 열렸습니다. 긴 탁자에 임원들이 줄지어 앉았고, 도윤은 그 맞은편에 홀로 섰습니다.

{c009}

"저는 정말 모르는 일입니다. 그 도장은 제가 찍은 게 아닙니다."

도윤의 목소리가 떨렸습니다. 아무도 그 말을 믿지 않았습니다. 그때, 감사실장이 말했습니다. 증인이 있습니다.

{c010}

문이 열리고 들어온 사람은, 이준혁이었습니다. 도윤의 입사 동기. 십 년 동안 함께 야근하고, 함께 술을 마시고, 서로의 결혼식 사회를 봐 주기로 약속한 친구였습니다. 준혁은 도윤의 눈을 피한 채 말했습니다.

"한도윤 차장이, 그 서류를 처리하라고 시켰습니다."

{c011}

도윤의 머릿속이 하얘졌습니다. 왜. 대체 왜. 준혁은 끝까지 도윤을 쳐다보지 않았습니다.

{c012}

그리고 그 회의실 한구석에서, 박 부장이 손으로 입을 가린 채 웃고 있었습니다. 도윤은 그제야 알았습니다. 처음부터 끝까지, 모든 것이 그의 작품이었다는 것을요.

{c013}

도윤은 그날로 해고되었습니다. 회사는 도윤을 횡령 혐의로 고소했습니다. 십 년의 회사 생활이 작은 상자 하나에 담겼습니다.

{c014}

같은 날 저녁, 병원에서 전화가 왔습니다. 엄마가 쓰러지셨다고요. 위암 말기였습니다. 의사는 말했습니다. 조금만 더 일찍 발견했더라면, 충분히 나을 수 있었을 거라고. 엄마는 아들이 바쁠까 봐, 아프다는 말을 한 번도 하지 않으셨습니다.

{c015}

엄마는 앙상한 손으로 도윤의 손을 잡았습니다.

"도윤아, 엄마는 괜찮아. 너만 괜찮으면 돼. 밥은 먹고 다니니?"

도윤은 엄마의 손에 이마를 대고 울었습니다. 회사 일 때문에 엄마 건강검진 한 번 챙겨 드리지 못한 자신이, 견딜 수 없이 미웠습니다.

{c016}

그날 밤, 도윤은 회사 옥상에 올라갔습니다. 장대비가 쏟아지고 있었습니다. 도윤은 하늘을 올려다보며 소리쳤습니다.

"한 번만. 딱 한 번만 다시 돌아갈 수 있다면. 이번엔 아무것도 빼앗기지 않을 텐데."

{c017}

그 순간, 하늘이 하얗게 갈라졌습니다. 번개가 옥상을 내리쳤고, 도윤의 눈앞이 새하얘졌습니다.

## 2. 다시, 입사 첫날

{c018}

삐삐삐. 알람 소리에 도윤은 벌떡 일어났습니다. 익숙한 천장. 낡은 벽지. 이십 대 때 살던 작은 방이었습니다.

{c019}

머리맡의 휴대폰을 집어 들었습니다. 십 년 전에 쓰던 휴대폰이었습니다. 화면에 날짜가 떠 있었습니다. 2016년 3월 2일. 세운물산 입사 첫날이었습니다.

{c020}

도윤은 비틀거리며 화장실로 갔습니다. 거울 속에는 스물두 살의 자신이 서 있었습니다. 눈 밑의 다크서클도, 이마의 주름도 없었습니다. 도윤은 자기 뺨을 세게 꼬집었습니다. 아팠습니다. 꿈이 아니었습니다.

{c021}

그때, 부엌에서 된장찌개 냄새가 났습니다. 도윤은 홀린 듯 부엌으로 걸어갔습니다. 그곳에, 엄마가 있었습니다. 앞치마를 두르고, 콧노래를 부르며 찌개를 끓이고 있었습니다. 볼이 발그레했고, 손도 따뜻해 보였습니다.

"우리 아들, 첫 출근인데 늦잠 자면 어떡해. 얼른 밥 먹어."

{c022}

도윤은 대답 대신 엄마를 뒤에서 와락 끌어안았습니다. 그리고 아이처럼 엉엉 울었습니다. 엄마는 깜짝 놀라 국자를 떨어뜨렸습니다.

"얘가 왜 이래. 첫 출근이 그렇게 무섭니?"

도윤은 대답하지 못했습니다. 엄마가 살아 계셨습니다. 건강하게, 따뜻하게.

{c023}

현관을 나서기 전, 도윤은 엄마의 두 손을 꼭 잡았습니다.

"엄마, 약속 하나만 해 줘. 이번 달 안에 꼭 건강검진 받아. 위 내시경까지. 내가 예약해 놓을게."

엄마는 웃으며 고개를 끄덕였습니다. "알았어, 알았어. 우리 아들 회사 다니더니 벌써 어른 다 됐네."

도윤은 속으로 다짐했습니다. 이번엔 늦지 않을 겁니다.

{c024}

세운물산 본사. 십 년 전과 똑같은 로비, 똑같은 엘리베이터였습니다. 하지만 그 안으로 걸어 들어가는 도윤은, 십 년 전의 순진한 신입이 아니었습니다.

{c025}

엘리베이터 문이 닫히려는 순간, 누군가 손을 넣어 문을 잡았습니다. 기름 바른 올백 머리, 번쩍이는 금시계. 박상철 과장이었습니다. 십 년 전이라 아직 과장이었습니다. 그가 도윤의 어깨를 툭툭 두드렸습니다.

"오, 신입이구나. 해외 물류팀? 내가 네 사수다. 잘해 보자고."

{c026}

박 과장은 지갑에서 카드를 꺼내 내밀었습니다.

"첫날이니까 쉬운 것부터 하자. 일 층 카페 가서 우리 팀 커피 좀 사 와. 아홉 잔. 내 건 시럽 두 번."

십 년 전, 도윤은 이 카드를 받아 들고 신나게 뛰어갔습니다. 그것이 십 년 노예 생활의 시작이었습니다.

{c027}

도윤은 카드를 받아 들고 웃었습니다. 아주 예의 바르게.

"네, 과장님. 잘 부탁드립니다. 앞으로 오래, 아주 오래 뵙겠습니다."

그 웃음 뒤에서, 도윤의 눈은 차갑게 빛나고 있었습니다.

{c028}

신입 연수실에 들어서자, 누군가 손을 흔들며 옆자리에 털썩 앉았습니다. 삐뚤어진 빨간 넥타이, 얇은 안경. 이준혁이었습니다.

"안녕하세요! 저도 해외 물류팀이에요. 우리 동기네요. 잘 부탁해요!"

{c029}

도윤은 그 밝은 얼굴을 한참 동안 바라보았습니다. 십 년 뒤, 이 얼굴이 도윤의 눈을 피하며 거짓 증언을 하게 됩니다. 하지만 도윤은 알고 있었습니다. 준혁이 처음부터 나쁜 사람은 아니었다는 것을요. 그를 그렇게 만든 사람이 따로 있었다는 것을요.

{c030}

점심시간, 복도에서 한 여자가 서류 더미를 안고 지나갔습니다. 감사팀 서유나 대리. 도윤은 그 이름을 똑똑히 기억했습니다.

{c031}

원래의 미래에서, 서유나는 박 과장의 비리를 끝까지 파헤치려 했던 유일한 사람이었습니다. 하지만 증거가 부족했고, 박 과장의 모함으로 지방 지사로 쫓겨났습니다. 회사를 떠나던 날, 그녀는 혼자 짐 상자를 들고 있었습니다. 그때 도윤은 아무것도 하지 못했습니다. 이번엔, 그녀가 필요했습니다.

## 3. 첫 기획안

{c032}

입사 한 달째. 도윤은 밤마다 사무실에 남아 노트북을 두드렸습니다. 동남아 냉동 물류 사업 기획안. 원래 미래에서 도윤이 삼 년 뒤에 만들어, 박 과장의 이름으로 발표되었던 바로 그 기획안이었습니다.

{c033}

이번엔 삼 년을 기다릴 필요가 없었습니다. 어디에 창고를 지어야 하는지, 어느 항구가 막히는지, 어떤 경쟁사가 실패하는지, 도윤은 이미 다 알고 있었으니까요.

{c034}

기획안이 완성되자, 아니나 다를까 박 과장이 다가왔습니다.

"오, 신입이 열심이네. 그거 나한테 줘 봐. 내가 다듬어서 위에 올려 줄게. 신입 이름으로 올리면 아무도 안 봐."

십 년 전과 토씨 하나 다르지 않은 말이었습니다. 도윤은 순순히 파일을 건넸습니다.

{c035}

하지만 그 전날 밤, 도윤은 두 가지를 해 두었습니다. 첫째, 기획안 전체를 최 전무 비서실에 메일로 보내 두었습니다. 신입 사원 아이디어 제안함이라는 이름으로, 날짜와 시간이 또렷하게 남도록요. 둘째, 박 과장에게 건넨 파일에서는 가장 중요한 부분을 빼 두었습니다. 현지 창고 임대 조건과 통관 절차. 그게 없으면 이 사업은 앞뒤가 맞지 않았습니다.

{c036}

일주일 뒤, 임원 보고 회의가 열렸습니다. 회의실 맨 끝자리에는 최 전무가 앉아 있었습니다. 숫자 하나 틀리는 걸 용납하지 않기로 유명한 사람이었습니다.

{c037}

박 과장이 자신만만하게 발표를 시작했습니다.

"제가 몇 달 동안 밤을 새워 준비한, 동남아 냉동 물류 사업입니다."

화면에는 도윤이 만든 지도와 그래프가 떠 있었습니다. 도윤은 회의실 맨 뒷자리에서 조용히 그 모습을 지켜보았습니다.

{c038}

발표가 끝나자, 최 전무가 안경을 고쳐 쓰며 물었습니다.

"좋습니다. 그런데 박 과장, 현지 창고 임대 조건은요? 그리고 그쪽 항구 통관은 보통 한 달씩 걸리는데, 냉동 화물은 어떻게 버틸 생각입니까?"

{c039}

박 과장의 입이 굳었습니다. 그가 받은 파일에는, 그 내용이 없었습니다.

"그, 그건, 아직 세부 검토 중이라서요. 다음 회의 때."

이마에 땀이 맺혔습니다. 회의실이 싸늘해졌습니다.

{c040}

그때, 맨 뒷자리에서 손 하나가 올라갔습니다.

"전무님, 제가 말씀드려도 되겠습니까? 과장님께 드린 초안에서는 그 부분이 빠져 있었는데, 제가 따로 정리해 두었습니다."

{c041}

도윤은 앞으로 걸어 나가 화면을 넘겼습니다. 그리고 막힘없이 설명했습니다. 어느 항구에 냉동 전용 통관 창구가 있는지, 현지 창고를 어떤 조건으로 빌리면 오 년 동안 비용이 삼십 퍼센트 줄어드는지, 경쟁사가 왜 이 사업에서 실패할 수밖에 없는지까지. 임원들이 하나둘 펜을 들고 받아 적기 시작했습니다.

{c042}

최 전무가 비서가 건넨 태블릿을 들여다보았습니다. 일주일 전 새벽, 신입 사원 한도윤의 이름으로 들어온 메일이었습니다. 지금 화면에 뜬 기획안과 똑같은 내용이었습니다. 최 전무가 고개를 들어 박 과장을 바라보았습니다.

"박 과장. 몇 달 동안 밤을 새웠다고 했나요?"

{c043}

박 과장의 얼굴이 터질 듯이 시뻘게졌습니다. 그날 회의가 끝난 뒤, 최 전무는 이 사업을 직접 챙기겠다고 했습니다. 그리고 실무 담당자로, 신입 사원 한도윤의 이름을 적었습니다. 십 년 만에 처음으로, 도윤의 이름이 도윤의 성과 위에 올라갔습니다.

## 4. 동기

{c044}

그해 오월, 비가 오던 밤이었습니다. 퇴근길 골목에서, 도윤은 낯익은 모습을 보았습니다. 검은 점퍼를 입은 남자 둘이 준혁의 멱살을 잡고 있었습니다.

"이번 달 이자, 언제 줄 건데? 회사 다닌다며. 회사로 찾아가 줄까?"

{c045}

도윤은 골목 모퉁이에서 그 모습을 지켜보며 주먹을 쥐었습니다. 원래의 미래에서는 몰랐던 일이었습니다. 하지만 십 년 뒤의 감사 자료에서, 도윤은 보았습니다. 준혁이 입사 첫해에 박 과장에게서 삼천만 원을 받았다는 기록을요.

{c046}

준혁의 아버지는 사업에 실패하고 세상을 떠나면서, 불법 사채 빚을 남겼습니다. 원금은 천만 원이었지만, 이자에 이자가 붙어 삼천만 원이 되어 있었습니다. 그리고 박 과장은 그 약점을 정확히 알고 있었습니다.

{c047}

며칠 뒤, 탕비실에서 박 과장이 준혁에게 흰 봉투를 내밀었습니다.

"준혁아, 힘들지? 이거 받아. 갚을 생각은 하지 말고. 대신 앞으로 내가 부탁하는 것만, 조금씩 들어주면 돼."

준혁의 손이 떨렸습니다. 십 년 전, 준혁은 이 봉투를 받았습니다. 그리고 그날부터 박 과장의 사람이 되었습니다.

{c048}

그날 밤, 도윤은 준혁을 포장마차로 데려갔습니다. 소주 몇 잔이 오가자, 준혁이 얼굴을 감싸고 울기 시작했습니다. 아버지 이야기, 사채업자 이야기, 그리고 박 과장의 봉투 이야기까지.

"나 그 봉투 받으려고 했어. 다른 방법이 없잖아."

도윤이 준혁의 술잔을 내려놓게 했습니다.

"방법 있어. 그 봉투는 받지 마. 받는 순간, 너는 평생 그 사람 거야."

{c049}

다음 날, 도윤은 준혁을 데리고 법률구조공단을 찾아갔습니다. 감사팀의 서유나 대리도 함께였습니다. 도윤이 부탁하자, 유나는 망설임 없이 따라나섰습니다. 그녀는 계약서를 한 장 한 장 넘기며 말했습니다.

"이건 법에서 정한 최고 이자율을 몇 배나 넘었어요. 넘은 이자는 갚을 의무가 없어요. 원금도 이미 다 갚은 셈이에요."

{c050}

두 달 뒤, 법원에서 결정문이 나왔습니다. 준혁이 갚아야 할 돈은 없었습니다. 오히려 그동안 더 낸 이자를 돌려받게 되었습니다. 준혁은 법원 앞 길바닥에서 결정문을 끌어안고 울었습니다.

{c051}

그날, 회사 옥상에서 준혁이 도윤을 와락 끌어안았습니다.

"너 왜 나한테 이렇게까지 해 줘? 우리 만난 지 석 달밖에 안 됐잖아."

도윤은 맑은 하늘을 올려다보았습니다. 십 년 전, 아니, 십 년 뒤의 그 회의실이 떠올랐습니다. 도윤의 눈을 피하던 준혁의 얼굴도요.

"넌 내 동기니까. 그리고, 우리 오래 같이 일할 거니까."

{c052}

그날 오후, 탕비실 쓰레기통에 흰 봉투 하나가 처박혔습니다. 박 과장은 이를 갈았습니다. 굴러 들어온 사냥개 한 마리를, 신입 놈에게 빼앗긴 것이었습니다.

## 5. 냉동 새우

{c053}

유월, 경기도의 냉동 물류 창고. 도윤은 달력을 보고 있었습니다. 원래의 미래에서, 회사를 처음으로 크게 흔든 사건이 바로 이 주에 일어났습니다.

{c054}

동진식품에서 들여온 냉동 새우가 운송 중에 녹았다가 다시 얼었고, 그 새우가 대형 마트에 깔렸습니다. 수백 명이 식중독에 걸렸고, 회사는 오십억 원을 물어냈습니다. 그리고 박 과장은 그 책임을, 입고 검사를 맡았던 신입들에게 떠넘겼습니다. 그 신입 중 한 명이 바로 도윤이었습니다. 동진식품은 박 과장이 몰래 뒷돈을 받고 끌어들인 협력사였습니다.

{c055}

도윤은 입고 검사 날 새벽, 누구보다 먼저 창고에 도착했습니다. 영하 이십 도의 냉동 창고에서, 도윤은 새우 상자를 하나씩 열었습니다.

{c056}

그리고 상자 옆에 붙은 온도 기록계를 확인했습니다. 운송 중 온도를 일 분마다 기록하는 장치였습니다. 그래프 한가운데가 산처럼 솟아 있었습니다. 운송 중에 여섯 시간 동안, 냉동 트럭의 온도가 영상으로 올라갔던 것입니다.

{c057}

새우 표면에는 녹았다 다시 언 흔적이 뚜렷했습니다. 하얀 얼음 결정이 덕지덕지 붙어 있었습니다. 도윤은 즉시 무전기를 들었습니다.

"동진식품 새우, 전량 출고 중지합니다. 검사 결과 나올 때까지 한 상자도 내보내지 마세요."

{c058}

한 시간 뒤, 박 과장이 창고로 달려왔습니다. 얼굴이 시뻘겠습니다.

"너 미쳤어? 신입이 감히 누구 허락받고 출고를 막아! 그거 오늘 마트에 안 들어가면 위약금이 얼만 줄 알아?"

창고 직원들이 숨을 죽이고 지켜보았습니다.

{c059}

도윤은 온도 기록계를 들어 보였습니다.

"과장님, 이 그래프 보이십니까? 여섯 시간 동안 영상 오 도였습니다. 이걸 그대로 마트에 보내면, 위약금이 아니라 사람이 다칩니다. 책임은 제가 지겠습니다. 대신 검사는 받겠습니다."

박 과장은 아무 말도 못 하고 돌아섰습니다. 그의 휴대폰에서는 동진식품 사장의 전화가 계속 울리고 있었습니다.

{c060}

사흘 뒤, 식품 안전 검사 결과가 나왔습니다. 세균 수가 기준치의 열두 배를 넘었습니다. 만약 그 새우가 마트에 들어갔다면, 원래의 미래처럼 수백 명이 병원에 실려 갔을 것입니다.

{c061}

최 전무가 도윤을 집무실로 불렀습니다. 그리고 처음으로, 도윤에게 손을 내밀었습니다.

"한도윤 씨. 자네가 오십억짜리 사고를 막았어. 아니, 돈이 문제가 아니지. 우리 회사 이름을 지켰네."

도윤은 그 손을 맞잡았습니다. 원래의 미래에서는 한 번도 잡아 보지 못한 손이었습니다.

{c062}

그리고 같은 날 밤, 감사팀의 서유나는 모니터 앞에서 눈을 가늘게 떴습니다. 도윤이 건넨 쪽지 한 장. 동진식품과 하늘무역이라는 회사 사이의 거래를 살펴봐 달라는 부탁이었습니다. 숫자를 따라가던 유나의 손이 멈췄습니다. 동진식품이 하늘무역에 매달 보내는 수상한 돈. 그리고 하늘무역의 대표는, 박 과장의 처남이었습니다.

## 6. 반격

{c063}

박 과장은 바보가 아니었습니다. 기획안, 준혁, 그리고 새우까지. 세 번이나 자기 앞을 막아선 신입이, 우연일 리가 없었습니다. 그는 불 꺼진 사무실에 홀로 앉아 금시계를 만지작거렸습니다.

"한도윤. 너 대체 뭐야."

{c064}

일주일 뒤, 게시판에 인사 발령이 붙었습니다. 해외 물류팀 한도윤, 평택 물류 창고로 발령. 신입을 석 달 만에 지방 창고로 보내는, 누가 봐도 보복성 발령이었습니다. 박 과장이 인사팀 부장과 손을 쓴 것이었습니다.

{c065}

하지만 박 과장의 진짜 계획은 따로 있었습니다. 도윤이 평택으로 떠난 그 주 금요일 밤, 강남의 한 유흥업소. 박 과장은 도윤의 이름으로 발급된 법인카드를 카운터에 내밀었습니다. 결재 금액, 사백팔십만 원. 신입 사원 법인카드는 팀장 서랍에 보관되어 있었고, 그 서랍 열쇠는 박 과장에게 있었습니다.

{c066}

월요일 아침, 소문이 회사에 퍼졌습니다. 신입 한도윤이 법인카드로 유흥업소에서 수백만 원을 긁었다는 소문이었습니다. 평택에서 서류를 챙기러 본사에 들른 도윤을, 사람들이 수군거리며 쳐다보았습니다. 원래의 미래에서 겪었던 그 시선, 그대로였습니다.

{c067}

복도에서 박 과장이 도윤을 막아섰습니다. 그리고 귓가에 대고 속삭였습니다.

"이번 주 금요일에 감사위원회 열린다. 법인카드 부정 사용, 그거 징계 해고 사유야. 너 이제 끝났어, 신입."

{c068}

도윤은 놀라지 않았습니다. 오히려 빙그레 웃었습니다.

"과장님. 그 카드 쓰신 날짜, 정확히 기억하세요? 금요일 밤 열한 시 이십 분이요. 꼭 기억해 두세요."

박 과장의 웃음이 아주 잠깐, 굳었습니다.

{c069}

그날 오후, 도윤의 휴대폰이 울렸습니다. 병원이었습니다. 지난달 엄마가 받은 건강검진 결과가 나왔다고, 보호자도 함께 와 달라고요. 도윤은 택시를 잡아타고 병원으로 달려갔습니다. 진료실에서, 의사가 모니터를 가리켰습니다.

"위에 작은 혹이 하나 있습니다. 암입니다. 그런데 다행히, 아주 초기예요."

{c070}

진료실을 나온 도윤은 복도 의자에 주저앉았습니다. 그리고 두 손으로 얼굴을 감싸고 울었습니다. 원래의 미래에서, 엄마의 암은 십 년 뒤에야 발견되었습니다. 그때는 이미 늦었습니다. 하지만 지금은, 지금은 늦지 않았습니다.

{c071}

엄마가 도윤의 등을 토닥였습니다.

"얘는, 엄마가 아픈데 왜 네가 울어. 초기래. 수술하면 낫는대. 다 우리 아들 덕분이야. 네가 그렇게 검진 받으라고 졸라서."

병원 문을 나서는 두 사람 위로, 유월의 햇살이 쏟아졌습니다.

## 7. 증거

{c072}

도윤은 기억하고 있었습니다. 원래의 미래, 자신이 누명을 쓰던 그 감사 자료 속에서, 딱 한 번 스쳐 지나간 계좌 하나를요. 당시에는 무슨 뜻인지 몰랐지만, 그 계좌로 돈이 들어온 날짜와 회사 이름만큼은 머릿속에 박혀 있었습니다.

{c073}

하늘무역. 박 과장의 처남 명의로 된 작은 무역 회사. 실제로는 직원도 사무실도 없는, 이름뿐인 회사였습니다. 그리고 이 회사로, 지난 이 년 동안 협력사들의 뒷돈이 모이고 있었습니다.

{c074}

도윤은 평택에서 일을 마치면, 밤마다 본사 감사팀으로 올라왔습니다. 유나와 함께 서류를 뒤지고, 숫자를 맞추고, 날짜를 대조했습니다. 도윤이 계좌의 흐름을 짚어 주면, 유나가 그 증거를 찾아냈습니다. 놀라울 정도로 정확했습니다.

{c075}

새벽 세 시, 유나가 서류에서 고개를 들었습니다.

"도윤 씨. 입사한 지 넉 달 된 신입이 어떻게 이런 걸 알아요? 하늘무역 이름은 감사팀도 몰랐어요."

{c076}

도윤은 창밖의 불빛을 바라보며 희미하게 웃었습니다.

"꿈에서 봤다고 하면, 믿으실래요? 아주 길고, 아주 나쁜 꿈이었어요. 십 년짜리요."

유나는 한참 도윤을 바라보다가, 피식 웃었습니다. "믿을게요. 이 증거들이 진짜니까."

{c077}

그리고 두 번째 증거. 박 과장이 법인카드를 긁은 금요일 밤 열한 시 이십 분. 그 시각, 도윤은 평택 물류 창고에서 야간 재고 조사를 하고 있었습니다. 창고에는 CCTV가 스무 대 넘게 달려 있었고, 그중 세 대가 도윤의 얼굴을 또렷하게 찍고 있었습니다. 도윤은 일부러 그 주에 야간 근무를 자청했던 것입니다. 박 과장이 언제 움직일지, 이미 알고 있었으니까요.

{c078}

세 번째 증거는, 준혁이 가져왔습니다. 감사위원회 이틀 전, 박 과장이 지하 주차장에서 준혁을 불러 세웠습니다.

"준혁아. 이번 감사위원회에서 한마디만 해 줘. 도윤이가 금요일에 서울 올라와서 술 마시러 간다고 했다고. 그 카드는 내가 처리할 테니까, 너는 그 말만 하면 돼. 사례는 섭섭지 않게 할게."

{c079}

준혁의 양복 안주머니에서, 휴대폰의 빨간 녹음 버튼이 조용히 깜박이고 있었습니다. 준혁은 고개를 숙이며 대답했습니다. "네, 과장님. 알겠습니다." 원래의 미래에서와 똑같은 대답이었습니다. 하지만 이번에는, 전혀 다른 뜻이었습니다.

## 8. 감사위원회

{c080}

금요일 아침, 본사 이십 층 대회의실. 감사위원회가 열렸습니다. 긴 탁자에 임원들이 앉았고, 맨 끝자리에는 최 전무가 있었습니다.

{c081}

박 과장은 탁자 한쪽에 팔짱을 끼고 앉아 있었습니다. 입가에는 이미 이긴 사람의 미소가 걸려 있었습니다. 증거도 있고, 증인도 있었습니다. 그렇게 믿고 있었습니다.

{c082}

도윤은 그 맞은편에 홀로 섰습니다. 십 년 뒤의 그 회의실과 똑같은 자리였습니다. 하지만 이번에는 손이 떨리지 않았습니다.

{c083}

박 과장이 벌떡 일어나 서류를 흔들었습니다.

"신입 사원이 입사 넉 달 만에, 법인카드로 유흥업소에서 사백팔십만 원을 썼습니다! 이런 직원이 우리 팀에 있다는 게 부끄럽습니다. 저는 팀장으로서, 한도윤 사원의 징계 해고를 요청합니다!"

{c084}

감사실장이 도윤에게 물었습니다. "한도윤 사원, 할 말 있습니까?" 도윤이 고개를 끄덕이며 리모컨을 들었습니다.

"네. 증거 세 가지를 보여 드리겠습니다."

{c085}

화면이 둘로 나뉘었습니다. 왼쪽에는 유흥업소의 카드 결제 기록. 금요일 밤 열한 시 이십 분. 오른쪽에는 평택 물류 창고의 CCTV 화면. 같은 날, 같은 시각. 작업복을 입은 도윤이 창고에서 재고표를 들고 서 있었습니다. 서울 강남과 평택 사이는 차로 한 시간 반이었습니다.

"저는 그 시각에, 평택 창고에 있었습니다. 그렇다면 그 카드는, 누가 썼을까요?"

{c086}

회의실이 술렁였습니다. 박 과장의 미소가 그대로 얼어붙었습니다. 관자놀이로 식은땀 한 방울이 흘러내렸습니다.

"그, 그건 카드를 누가 훔쳐 갔겠지. 신입 카드 관리가 허술해서."

{c087}

그때, 회의실 문이 열렸습니다. 이준혁이었습니다. 박 과장이 반가운 얼굴로 준혁을 바라보았습니다. 그의 증인이 도착한 것이었습니다. 하지만 준혁은 박 과장을 지나쳐, 도윤의 옆에 섰습니다. 그리고 휴대폰을 탁자 위에 올려놓았습니다.

{c088}

"두 번째 증거입니다. 이틀 전, 지하 주차장에서 녹음한 겁니다."

재생 버튼이 눌렸습니다. 회의실에 박 과장의 목소리가 울려 퍼졌습니다. 도윤이가 술 마시러 간다고 했다고 한마디만 해 줘. 그 카드는 내가 처리할 테니까. 사례는 섭섭지 않게 할게.

{c089}

박 과장이 의자를 박차고 일어났습니다.

"조작이야! 저 녹음, 다 조작이라고! 저 두 놈이 짜고 나를 모함하는 거야!"

{c090}

"그럼 이것도 조작인가요?"

차분한 목소리와 함께, 감사팀 서유나가 들어왔습니다. 두꺼운 서류철을 품에 안고 있었습니다.

{c091}

유나가 서류철을 탁자 위에 펼쳤습니다.

"세 번째 증거입니다. 박상철 과장의 처남 명의로 된 하늘무역. 지난 이 년간 동진식품을 비롯한 협력사 일곱 곳에서, 이 회사로 들어간 돈은 모두 십일억 원입니다. 그리고 그 돈의 절반이, 다시 박 과장 본인의 계좌로 옮겨졌습니다. 동진식품의 불량 새우가 우리 창고에 들어올 수 있었던 이유도, 바로 이 돈이었습니다."

{c092}

회의실에 정적이 흘렀습니다. 맨 끝자리의 최 전무가 천천히 일어섰습니다. 그가 안경을 고쳐 쓰며, 박 과장을 차갑게 내려다보았습니다.

"박 과장. 나는 어제 이 자료를 미리 받았네. 그리고 오늘 아침, 검찰에 수사를 의뢰했어. 이 회의는, 자네에게 마지막으로 진실을 말할 기회를 주려고 연 거였네. 그런데 자네는 끝까지 신입한테 죄를 뒤집어씌우는군."

{c093}

그때, 회의실 문이 다시 열렸습니다. 양복 차림의 수사관 두 명이 들어왔습니다.

"박상철 씨, 배임 수재와 업무상 횡령 혐의로 체포합니다."

{c094}

철컥. 박 과장의 손목에 수갑이 채워졌습니다. 번쩍이던 금시계 위로, 차가운 쇠고리가 걸렸습니다. 기름 바른 올백 머리가 흐트러졌고, 얼굴은 하얗게 질려 있었습니다.

{c095}

끌려 나가던 박 과장이, 도윤 앞에서 걸음을 멈췄습니다. 그리고 이를 갈며 물었습니다.

"너, 대체 뭐야. 어떻게 다 알았어? 넌 입사한 지 넉 달밖에 안 됐잖아!"

도윤은 박 과장에게 한 발짝 다가가, 귓가에 대고 조용히 속삭였습니다.

"과장님은 넉 달이라고 생각하시겠지만, 저는 이날을 십 년 동안 기다렸거든요."

{c096}

박 과장의 눈이 커다랗게 흔들렸습니다. 그는 그 말의 뜻을 끝내 알지 못한 채, 수사관들에게 끌려 복도로 나갔습니다. 사무실의 직원들이 모두 일어나 그 모습을 지켜보았습니다. 십 년 동안 도윤의 모든 것을 빼앗았던 사람이, 이번에는 아무것도 빼앗지 못하고 떠나갔습니다.

## 9. 이번엔 지켰다

{c097}

일주일 뒤, 최 전무가 도윤을 집무실로 불렀습니다. 그리고 서류 한 장을 건넸습니다. 동남아 냉동 물류 사업, 신규 사업팀 신설.

"자네가 시작한 일이니, 자네가 끝까지 해 보게. 신입이라 팀장은 못 시켜 주지만, 실무는 전부 자네한테 맡기겠네. 사람은 원하는 대로 골라."

{c098}

도윤이 고른 사람은 두 명이었습니다. 동기 이준혁, 그리고 감사팀 서유나. 유나는 감사팀에서 받은 표창장을 들고 새 팀으로 옮겨 왔고, 준혁은 삐뚤어진 넥타이를 고쳐 매며 말했습니다.

"이번엔 나도 진짜 잘할게. 약속해."

도윤은 웃었습니다. 원래의 미래에서는 들을 수 없었던 말이었습니다.

{c099}

엄마의 수술은 무사히 끝났습니다. 의사는 깨끗하게 떼어 냈다고, 재발할 가능성도 거의 없다고 했습니다. 병실 창가에는 준혁과 유나가 보낸 꽃바구니가 놓여 있었습니다.

{c100}

도윤은 엄마 침대 옆에 앉아 사과를 깎았습니다. 엄마는 그 모습을 보며 깔깔 웃었습니다.

"우리 아들 사과 깎는 솜씨 좀 봐. 껍질이 반이네. 그래도 맛있다."

도윤도 따라 웃었습니다. 원래의 미래에서, 도윤은 이 병실에서 매일 울었습니다. 이번에는 매일 웃었습니다.

{c101}

그리고 일 년이 흘렀습니다. 동남아 냉동 물류 사업은 첫해부터 흑자를 냈습니다. 원래의 미래보다 삼 년이나 빨랐습니다. 박상철은 징역형을 선고받았고, 동진식품과 하늘무역은 문을 닫았습니다.

{c102}

다시 봄이 왔습니다. 아침 부엌에서, 엄마가 도윤에게 도시락을 건넸습니다. 건강을 되찾은 엄마의 볼은 다시 발그레했습니다.

"오늘 신입 사원들 들어온다며? 우리 아들도 이제 선배네. 후배들한테 커피 심부름 시키면 안 된다."

도윤은 웃으며 대답했습니다. "절대 안 시켜. 약속해."

{c103}

출근 전, 도윤은 회사 옥상에 올라갔습니다. 원래의 미래에서, 장대비 속에 모든 것을 잃었던 바로 그 옥상이었습니다. 오늘은 하늘이 맑았습니다. 벚꽃 잎이 바람을 타고 옥상까지 날아올랐습니다.

{c104}

도윤은 목에 건 사원증을 내려다보았습니다. 한도윤. 이번에는 아무것도 빼앗기지 않았습니다. 엄마도, 친구도, 자신의 이름도.

{c105}

도윤은 로비로 내려갔습니다. 잔뜩 긴장한 얼굴의 신입 사원들이 줄지어 들어오고 있었습니다. 일 년 전의 자신처럼요. 도윤은 그들에게 다가가 웃으며 손을 내밀었습니다.

"환영합니다. 오늘이 입사 첫날이죠? 걱정 마세요. 첫날은, 누구에게나 다시 시작할 기회니까요."

두 번째 입사 첫날. 도윤은 이번엔, 모든 것을 지켜 냈습니다."""


def main():
    cmd, folder = sys.argv[1], sys.argv[2]
    chars = {c["name"]: c for c in json.load(open(os.path.join(HERE, "등장인물.json"), encoding="utf-8"))["chars"]}
    if cmd == "job":
        items = []
        for cid, who, desc, _ in CUTS:
            custom = any(k in desc for k in CUSTOM_OUTFIT) or "padded work jacket" in desc or "faded blue-toned memory" in desc
            looks = "; ".join(f"person {k + 1} (the character from reference image {k + 1}): {chars[nm]['look']}"
                              + ("" if custom else ", " + chars[nm]["outfit"])
                              for k, nm in enumerate(who))   # 한글 이름은 그림에 글자로 나올 수 있어 번호로
            items.append({"id": cid, "width": 1024, "height": 576, "seed": 100 + int(cid[1:]),
                          "refs": [os.path.join(HERE, chars[nm]["face"]) for nm in who],
                          "prompt": f"{STYLE}, Korean office drama. "
                                    + (f"Characters: {looks}. Each person appears only once, exactly two arms and two legs. " if looks else "No main characters. ")
                                    + f"Scene: {desc}. Cinematic composition, full-bleed image, no border, no frame, no paper edges. No speech bubbles, no text, no letters."})
        os.makedirs(folder, exist_ok=True)
        json.dump({"items": items}, open(os.path.join(folder, "job.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(len(items), "cuts")
    elif cmd == "project":
        story = STORY
        for cid, _, _, cap in CUTS:
            story = story.replace("{" + cid + "}", f"[사진: {os.path.join(folder, cid + '.png')} | {cap} | AI 생성 그림 (FLUX.2 klein) | ]")
        proj = {"ver": 7, "category": "장문", "genre": "[이야기] 회귀·빙의 판타지", "topic": "다시, 입사 첫날", "title": TITLE,
                "story": story, "sources": [], "notes": "미니드라마 스타일 애니 단편 《다시, 입사 첫날》 (약 30분, 회귀 복수극)", "autophoto": False, "img_source": "그림: 애니 일러스트",
                "cast": [{"name": nm, "look": c["look"], "look_ko": c["look_ko"],
                          **({"sheet": os.path.join(HERE, c["face"])} if c.get("face") else {})} for nm, c in chars.items()],
                "settings": {"format": "롱폼 가로(1920×1080)", "narration": "on",   # 새 PC·서버 기본값(나레이션 꺼짐·스크롤형) 대신 장문 설정 그대로
                             "layout": "자막형(큰 제목+사진+자막)", "img_fill": "전체 화면(글자가 사진 위에)",
                             "img_motion": "영상처럼(확대·이동·전환)", "fps": "24", "reveal_hit": "off", "reveal_fx": "off",
                             "head_show": "안 보임(제목 카드만)", "sub_split": "한 줄씩(문장·쉼표로 나눠 차례로)", "img_label": "off",   # 규칙: 위 큰 제목·장면 설명 없이, 자막은 한 줄씩
                             "narr_voice": "Supertonic M2 (남성, 무료 로컬) [supertonic:M2]",   # 성우 샘플 1번 (사용자가 고름)
                             "narr_rate": "0", "narr_tone_m": 0.0}}
        out = os.path.join(HERE, "다시입사첫날_단편.json")
        json.dump(proj, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(out, len(story), "chars")


if __name__ == "__main__":
    main()
