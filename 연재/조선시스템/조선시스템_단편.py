"""「조선에 떨어진 미래 의사」 3부작 (수묵 담채) — 컷별 그림 계획
python 연재/조선시스템/조선시스템_단편.py job <부> <저장폴더> [컷번호 ...]  → klein_worker 그림 주문서 job.json
python 연재/조선시스템/조선시스템_단편.py project <부> <그림폴더>         → 그 부 프로젝트 파일에 [사진] 줄을 넣음
  - 인물 기준 그림 = 시트 앞모습 + 그 사람 모자를 위에 얹은 한 장 (캐릭터시트/_앞_<인물>_모자.png, 수묵담채화.md 모자 규칙)
    임금 = 익선관(_모자_익선관.png), 판서 = 사모(_모자_사모.png), 현 = 갓. 방 안에 누운 현은 맨머리 상투(_앞_현.png)
  - 시트 없는 조연(박 수령·관찰사)은 사모 앞모습(등장인물/조선/_관모/사모_앞.png)만 넣고 외모를 글로
  - 시스템 창 = 글자 없는 푸른빛 창 (글자가 그려지지 않게)
  - 인물·고을·관직 이름은 모두 지어낸 것"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SHEETS = os.path.join(HERE, "캐릭터시트")
CAPS = os.path.join(ROOT, "등장인물", "조선", "_관모")

STYLE = ("traditional East Asian ink wash painting with light color washes: expressive black ink brush outlines, "
         "rich clear colors applied as transparent watercolor washes, rice paper texture, historically accurate Joseon Korean costumes "
         "and architecture, Korean Joseon dynasty hanbok - NOT Chinese hanfu, NOT Japanese kimono, no red seal stamp, no calligraphy")
STYLE_2045 = ("traditional East Asian ink wash painting with light color washes: expressive black ink brush outlines, "
              "rich clear colors applied as transparent watercolor washes, rice paper texture, a modern 2045 research laboratory, no red seal stamp, no calligraphy")
CAP_LINE = "Each person and the cap shown above him in his reference image are one: he always wears exactly that cap. "
SAMO = "black samo cap: a small rounded black cap fitted close to the head with a higher back part, and two thin flat oval mesh wings attached only at the back of the cap that stick straight out to the left and right like ears; the sides of the cap above the ears are bare"
LOOK = {
    "현": "a 20-year-old slim Korean young man, a poor fallen-noble scholar, young clean-shaven face, calm intelligent eyes, black gat hat with a wide flat round brim and a tall narrow cylindrical crown whose top is completely flat with nothing on top, a faded light gray-white dopo robe with small patches, thin dark cord belt, straw sandals",
    "현_맨머리": "a 20-year-old slim Korean young man, young clean-shaven face, calm intelligent eyes, full thick black hair combed back from a normal hairline and tied in a small topknot and a thin black headband, a plain white undergarment jeogori",
    "어머니": "a 45-year-old thin Korean woman, gentle tired face, black hair in a low bun with a plain wooden hairpin, a faded beige jeogori jacket and a dark navy chima skirt",
    "판서": "a 56-year-old heavy-set Korean high minister with a round belly, gray mustache and short gray beard, narrow greedy eyes, a dark crimson official robe with one square crane badge on the chest, " + SAMO,
    "임금": "a 40-year-old Korean king, tall, calm dignified face, neat short black beard, a bright red royal robe with golden round dragon badges on the chest and shoulders, the same black ikseongwan cap with the same shape as in the reference image: a rounded black cap with two rounded lobes rising straight upward at the back of its top, the sides of the cap close and smooth, jade belt",
    "도현": "a 54-year-old Korean scientist, short neat gray-black hair, thin rimless glasses, kind tired eyes, a white lab coat over a light blue shirt",
    "수령": "a 35-year-old thin Korean magistrate with a thin black mustache and sly narrow eyes, a dark blue official robe with a square badge on the chest, " + SAMO,
    "민호": "a 22-year-old plump Korean young noble with a soft face, small arrogant eyes and a thin black mustache, a fine black gat hat with a long string of amber beads under the chin, a shiny light jade-green silk dopo robe with a fine gold pattern, a red silk cord belt",
    "시험관": "a 50-year-old thin nervous Korean exam official with a thin gray beard, a dark teal blue official robe with a square crane badge, " + SAMO,
    "아이": "a 10-year-old thin poor Korean village boy with full thick black hair on his whole head, parted in the middle and combed back into one long braid down his back tied with a red ribbon, a worn beige jeogori and baggy beige trousers, straw sandals",
    "의원": "a 65-year-old thin Korean royal court physician with a long white beard and white eyebrows, a proud stubborn face, a dark olive green official robe with a square crane badge, " + SAMO,
    "관찰사": "a 60-year-old dignified Korean governor with a long white beard and stern wise eyes, a dark green official robe, " + SAMO,
}
# 임금은 앞모습만: 모자 띠(옆·뒤)를 얹으면 익선관 뒤 봉우리를 옆 날개로 그림 (2026-11-07)
REF = {
    "현": "_앞_현_모자.png", "현_맨머리": "_앞_현_맨머리.png", "어머니": "_앞_어머니.png", "판서": "_앞_판서_모자.png",
    "임금": "_앞_임금.png", "도현": "_앞_도현.png",
    "수령": "_앞_수령_모자.png", "민호": "_앞_민호_모자.png", "시험관": "_앞_시험관_모자.png", "아이": "_앞_아이.png", "의원": "_앞_의원_모자.png", "관찰사": "_앞_관찰사_모자.png",
}
CAPPED = {"현", "판서", "임금", "수령", "관찰사", "민호", "시험관", "의원"}

LAB = "a modern infectious disease research laboratory in Seoul in the year 2045 at night, glass test tubes, a microscope, cold white lights"
ROOM = "inside a small poor thatched-roof Joseon house room, paper lattice door, worn straw mat floor, a thin old quilt; light comes only from a small open clay oil dish with one burning wick"
YARD = "the dirt yard of a small poor thatched-roof Joseon house with a brushwood gate and a low stone wall"
VILLAGE = "a poor Joseon farming village of thatched-roof houses with stone wells and dirt paths, early spring"
ENTRY = "the entrance of a poor Joseon village with a dirt road, a big old tree and thatched houses behind"
FENCE = "a dirt road outside a Joseon village blocked by a rough wooden barricade fence"
STORE = "a large wooden storehouse behind a Joseon county government office, heavy wooden doors"
MANSION = "a grand Joseon tiled-roof mansion room in Hanyang at night, a low lacquered table, folding screen, candlelight"
EXAM = "a wide stone-paved courtyard in front of a Joseon royal palace gate on exam day, hundreds of scholars in white dopo robes and black gat hats sitting in rows on straw mats with low writing boards, a tall wooden frame at the front"
PALACE = "a Joseon king's private study room in the palace at night, red-lacquered pillars, a low lacquered desk with paper rolls, one ink brush and a black inkstone, candlelight, folding screen with painted peonies"
GATE = "the big wooden gate of a Joseon royal palace with a tiled roof"
HANYANG = "a street of Hanyang, the Joseon capital, with tiled-roof houses"
SCHOLARS = "Other people are Joseon scholars in plain white or light gray dopo robes and black gat hats, who look clearly different from the main characters. "
COURT = "Other people are Joseon court officials in red and blue official robes and black samo caps, and palace servants. "
NAEUI = "the Joseon royal pharmacy hall inside the palace with walls of many small wooden herb drawers, dried herbs hanging from beams, low tables with bronze herb grinders"
THRONE = "a Joseon palace throne hall with red pillars and a painted folding screen of sun, moon and five peaks behind a raised wooden dais"
COURTYARD = "the stone-paved courtyard in front of a Joseon palace hall, red pillars and a tiled roof"
PRISON = "a dark Joseon prison cell with thick wooden bars and straw on the dirt floor, a little moonlight through a small window"
QUAR = "a big quarantine house made in an empty wooden storehouse outside the capital walls, rows of straw mats with sick people lying under thin quilts, steaming pots"
SEA = "a misty gray seashore with a small old wooden boat and a far lonely island"
MARKET = "a busy Hanyang market street with tiled-roof shops, straw mats of goods and wooden stalls"
PHYS = "Other people are old Joseon royal physicians in dark olive green official robes and black samo caps, who look clearly different from the main characters. "
CHILDREN = "Other people are seven thin Joseon village children in plain beige and white hanbok. "
PANEL = "a glowing translucent blue rectangular window of light floating in the air, filled only with soft light and thin abstract lines, completely blank with no letters, no numbers, no symbols"
VILLAGERS = "Other people are poor Joseon commoners in plain white and beige hanbok, men with small topknots and headbands, women with hair in buns, who look clearly different from the main characters. None of the villagers wear any hat: every villager is bareheaded with a small topknot and a thin headband or a bun; only the young scholar wears the tall black gat. "
SOLDIERS = "Other people are Joseon foot soldiers who all wear exactly the uniform of the soldier in the LAST reference image: black felt jeonrip hat with a wide round brim and a red tassel, sleeveless dark navy jeonbok vest over red sleeves, red sash, white baggy trousers, black cloth boots, holding long wooden spears. "
CLERKS = SOLDIERS   # 수령이 거느린 사람들도 조선 군졸 차림 (검은 둥근 모자가 서양 모자처럼 나와서, 2026-11-07)

# 부마다 (컷, 문단 번호들, 나오는 인물, 다른 사람 문장(없으면 ""), 장소, 장면(영어), 화면 설명)
CUTS = {1: [
    ("c01", [1], ["도현"], "", LAB, "the scientist working late at night at a lab bench, carefully holding a small glass vial and looking into a microscope, tired but focused", "2045년 감염병 연구소"),
    ("c02", [2], ["도현"], "", LAB, "a glass tube shattering on the lab bench with bright sparks and a blinding white flash of light; the scientist falling backward, arm raised against the light", "깨진 유리관과 하얀 빛"),
    ("c03", [3], ["현_맨머리"], "", ROOM + ", cold early morning light through the paper door", "the young man lying on a thin old quilt on the floor, just opening his eyes, confused, looking at the low ceiling", "초가집에서 눈을 뜨다"),
    ("c04", [4], ["현_맨머리"], "", ROOM, "the young man sitting up on the quilt and staring at his own two smooth young hands raised in front of him, astonished; in the air before him " + PANEL, "스무 살의 손과 푸른 창"),
    ("c05", [5], ["현_맨머리"], "", ROOM, "close view: the young man's astonished face lit by blue light from " + PANEL + " floating in front of him", "시스템이 시작됩니다"),
    ("c06", [6], ["현_맨머리"], "", ROOM, "the young man gazing at " + PANEL + " with one thin glowing red line of light at its bottom edge, his face serious", "첫 번째 임무, 어머니를 살리십시오"),
    ("c07", [7], ["어머니", "현_맨머리"], "", ROOM, "the thin mother lying on a mat in the corner of the room with a fever, coughing, sweat on her forehead; the young man turning toward her in alarm", "열에 들뜬 어머니"),
    ("c08", [8], ["현_맨머리"], "", ROOM + ", shown as a faded memory with a soft sepia tint", "the young man sitting alone in the bare poor room at a small low wooden writing desk with one ink brush and a black inkstone on it, the room nearly empty, a lonely quiet mood", "삼대째 벼슬을 못 한 집안"),
    ("c09", [9], ["현"], VILLAGERS, YARD, "worried villagers standing outside the brushwood gate shaking their heads and covering their mouths; the young man standing in the yard facing them", "괴질이었습니다"),
    ("c10", [10], ["현"], "", YARD + ", with a faint translucent ghost image of a modern laboratory in the sky behind him like a memory", "the young man standing in thought with a sharp determined look, remembering", "콜레라와 똑같은 병"),
    ("c11", [11], ["현"], "", YARD, "the young man boiling well water in a big black iron pot over a wood fire, adding a handful of salt from a small bowl, a small clay honey jar beside him, steam rising", "끓인 물에 소금과 꿀"),
    ("c12", [12, 13], ["현_맨머리", "어머니"], "", ROOM + ", night", "only two people: the sick mother (reference image 2) lying on her back on the mat under a thin quilt with her eyes closed, and the young man (reference image 1) dressed all in white kneeling beside her alone, gently giving her water from a wooden spoon, keeping watch through the night; nobody else is in the room", "밤새 어머니 곁을"),
    ("c13", [14, 15], ["어머니", "현_맨머리"], "", ROOM + ", soft morning light", "the mother sitting up weakly and eating porridge from a small bowl, the young man smiling with relief beside her; behind him softly glows " + PANEL, "어머니가 죽을 받아 넘기다"),
    ("c14", [16], [], "", VILLAGE + ", wide view from a small hill", "a quiet village where a strange reddish mist rises like smoke above three of the stone wells, an eerie mood", "우물 위의 붉은 안개"),
    ("c15", [17], ["현"], "", VILLAGE, "the young man standing on a dirt path looking at the village with determination, " + PANEL + " glowing beside him", "마을을 살리십시오"),
    ("c16", [18, 19], ["현"], VILLAGERS, ENTRY, "the young man standing under the big tree shouting earnestly to a crowd of villagers, one arm raised pointing toward a well", "끓여서 마셔야 합니다"),
    ("c17", [20], [], VILLAGERS, ENTRY, "a few villagers whispering to each other doubtfully with suspicious faces, glancing to the side. No main characters", "의원 흉내를 낸다고"),
    ("c18", [21], ["수령"], CLERKS, ENTRY + ", dust on the road", "the thin magistrate riding a brown horse arriving on the road with several soldiers walking behind him, an arrogant face, the magistrate wearing a black samo cap with two flat oval wings sticking out to the left and right", "박 수령이 나타나다"),
    ("c19", [22], ["수령"], CLERKS, ENTRY, "the thin magistrate on his horse pointing coldly with a fan, ordering the soldiers to block the roads", "길을 모두 막아라"),
    ("c20", [23], [], CLERKS, FENCE, "soldiers putting up a rough wooden barricade fence across the road, while an ox cart loaded with plain brown wooden medicine chests and straw-wrapped bundles turns away from the village. No main characters", "막힌 길, 돌아가는 약재 수레"),
    ("c21", [24, 25], ["수령", "현"], "", FENCE, "the young scholar stepping in front of the magistrate's brown horse with his arms spread, blocking its way; the magistrate on the horse smirking", "수령의 말 앞을 막아서다"),
    ("c22", [26, 27], ["현", "수령"], "", FENCE, "the magistrate sitting high on his brown horse and looking down with a mocking sneer; the young scholar standing on the ground below, pleading earnestly", "말 위에서 비웃는 수령"),
    ("c23", [28, 29], ["현"], CLERKS, FENCE, "the young scholar has just been pushed down and is sitting fallen on the dirt road, propped on one hand, dust flying, his gat hat still on his head; a Joseon foot soldier stands two steps away sneering, his arm still stretched out from the push, their hands far apart; the young scholar's two legs are in white trousers with straw sandals. The young scholar appears only once, only on the ground", "흙바닥에 넘어진 이현"),
    ("c24", [30], ["현"], "", FENCE, "the young scholar half-lying on the dirt road propped on one arm, looking up at " + PANEL + " showing a faint picture of a locked wooden storehouse", "숨겨진 사실이 보입니다"),
    ("c25", [31], ["현"], VILLAGERS, VILLAGE + ", night", "the young scholar and a few villagers hanging big black iron pots over wood fires beside a stone well at night, flames and steam", "우물마다 솥을 걸다"),
    ("c26", [32], [], VILLAGERS, VILLAGE + ", daytime", "a recovered little village boy standing up smiling and a white-haired old man getting up from a straw mat, villagers gathering around the steaming iron pots with bowls. No main characters", "하나둘 솥 앞에 모여들다"),
    ("c27", [33], [], VILLAGERS, VILLAGE + ", bright morning", "the village in clear morning light, the last thin wisps of reddish mist fading away above the wells, villagers going about their work. No main characters", "걷혀 가는 붉은 안개"),
    ("c28", [34], [], SOLDIERS, FENCE + ", seen from a distance", "a governor's procession passing along the road outside the wooden barricade, smoke from steaming pots rising beyond the fence in the village", "관찰사의 행렬"),
    ("c29", [35], ["관찰사"], SOLDIERS, FENCE, "the governor on a brown horse stopping and looking over the wooden barricade with a puzzled stern face", "어찌 사람들이 저리 일을"),
    ("c30", [36], ["현"], "", FENCE, "the young scholar stepping in front of the wooden barricade and bowing deeply with both hands together", "울타리 앞에 나선 이현"),
    ("c31", [37], ["현", "관찰사"], "", FENCE, "the young scholar standing straight and speaking firmly toward the governor on his horse, pointing toward a distant storehouse", "창고를 열어 보시옵소서"),
    ("c32", [38], ["관찰사"], SOLDIERS, FENCE, "the governor standing on the ground with both feet, holding the reins of his brown horse beside him with one hand and raising the other hand to give an order; soldiers bowing and setting off", "군졸들에게 명하다"),
    ("c33", [39], [], SOLDIERS, STORE + ", evening torchlight", "the heavy storehouse doors thrown open by soldiers, revealing many old wooden carts piled high with plain brown wooden medicine chests with iron locks and straw-wrapped bundles inside, lit by burning torches held by the soldiers. No main characters", "창고 안의 약재 수레 서른 대"),
    ("c34", [40, 41], ["수령", "관찰사"], "", STORE + ", evening torchlight", "the thin magistrate kneeling with a pale terrified face; the governor standing over him holding out his hand sternly to take the magistrate's seal", "수령의 관인을 거두다"),
    ("c35", [42], ["어머니"], VILLAGERS, ENTRY + ", sunset", "villagers joyfully pulling down the wooden barricade; in the foreground the mother standing at a brushwood gate wiping tears with her sleeve, smiling", "울타리를 걷어 내는 마을 사람들"),
    ("c36", [43, 44], ["현_맨머리"], "", ROOM + ", night", "the young man sitting at a low wooden table with a few loose sheets of rough paper, an ink brush and a black inkstone on it, looking up at " + PANEL + " with one glowing red line at its bottom", "세 번째 임무, 장원 급제"),
    ("c37", [45], ["판서"], "", MANSION, "the heavy-set minister sitting on a floor cushion at the low lacquered table, slowly putting down a white porcelain teacup, listening to news with a cold face", "한양의 김 판서"),
    ("c38", [46, 47], ["판서"], "", MANSION, "close view of the heavy-set minister's face narrowing his eyes with a cold dangerous look, candlelight flickering", "김 판서의 눈이 가늘어지다"),
],
2: [
    ("c01", [1], ["현"], VILLAGERS, VILLAGE + ", spring with blossoming trees", "the young scholar standing in the peaceful spring village, looking up at " + PANEL + " with one glowing red line at its bottom", "세 번째 임무, 장원 급제"),
    ("c02", [2], ["현"], "", "a dirt road leading out of a Joseon village toward far blue mountains, spring", "the young scholar standing on the road seen from behind, looking toward the far road to the capital with resolve", "몰락 양반이 일어설 단 하나의 길"),
    ("c03", [3], ["현_맨머리"], "", ROOM + ", night", "the young man reading an old book at a low wooden desk under the oil lamp, " + PANEL + " glowing softly beside him", "등잔 아래서"),
    ("c04", [4], ["현_맨머리"], "", ROOM + ", night", "the young man writing carefully with an ink brush on sheets of rough paper at the low desk, a hand-drawn map of a village with wells beside him, focused", "열흘의 기록"),
    ("c05", [5, 6], ["판서", "민호"], "", MANSION, "the heavy-set minister sitting on a floor cushion and speaking seriously; his son, a grown-up adult man of 22 as tall as an adult with a thin black mustache, kneeling in front of him, listening with a sly smile", "아들을 부른 김 판서"),
    ("c06", [7], ["판서", "시험관"], "", MANSION + ", secretly, the doors closed", "the heavy-set minister pushing a small cloth bundle of silver ingots across the low table toward the nervous exam official, who glances around anxiously", "은덩이 열 개"),
    ("c07", [8], ["판서", "시험관"], "", MANSION, "the heavy-set minister leaning close and whispering coldly into the ear of the nervous exam official, who nods with a pale face", "그자의 답안은 떨어뜨리게"),
    ("c08", [9], ["민호"], SCHOLARS, EXAM, "the plump young noble in a shiny jade-green silk robe sitting proudly in the front row choosing a brush at leisure, rows of scholars behind him", "과거 시험 날"),
    ("c09", [10, 11], ["민호", "현"], SCHOLARS, EXAM, "the plump young noble in the shiny jade-green silk robe sneering and pointing with his fan at the young scholar in a worn patched gray-white robe who is walking in quietly", "코웃음 친 김민호"),
    ("c10", [12], [], SCHOLARS, EXAM, "a big blank white paper scroll being hung up on the tall wooden frame at the front of the courtyard by two officials while rows of scholars look up. No main characters", "시험 문제가 걸리다"),
    ("c11", [13], ["민호"], SCHOLARS, EXAM, "close view: the plump young noble in the jade-green silk robe writing quickly and smugly with a brush on a long sheet of paper", "막힘없이 써 내려간 글"),
    ("c12", [14], ["현"], SCHOLARS, EXAM, "the young scholar in the worn patched robe putting down his brush and rising from his straw mat, a short finished sheet in his hand, calm and quick", "한 시진도 안 되어 일어나다"),
    ("c13", [15], ["현"], SCHOLARS, EXAM, "the whole courtyard of seated scholars turning their heads in surprise toward the young scholar standing alone", "술렁이는 마당"),
    ("c14", [16, 17, 18], ["민호"], SCHOLARS, EXAM, "the plump young noble in the jade-green silk robe laughing loudly with his head thrown back, pointing; scholars around him snickering", "백지를 낸 거 아니야?"),
    ("c15", [19], ["현", "아이"], "", GATE + ", outside the exam courtyard", "the young scholar coming out of the gate; a thin village boy with a long braid waiting for him, panting and sweaty from running", "시험장 문 앞의 아이"),
    ("c16", [20], ["아이", "현"], "", GATE, "close view: the thin village boy with a long braid looking up and pleading with tearful eyes; the young scholar bending down to listen", "도령님만 찾아요"),
    ("c17", [21], ["현"], "", "a long dirt road running away from Hanyang's walls toward the countryside", "the young scholar running fast along the road with both empty hands swinging, his robe flapping, the city wall far behind", "고향 쪽으로 달려가다"),
    ("c18", [22], ["현"], VILLAGERS, VILLAGE + ", night", "the young scholar stirring a big iron pot of boiling water over a fire in a dark village at night, villagers carrying bowls, a well covered with boards", "이웃 마을에서 다시 솥을"),
    ("c19", [23], [], "Other people are Joseon commoners of the capital in plain hanbok, some sick and lying on mats, palace physicians in green robes shaking their heads. ", HANYANG + ", gloomy gray day", "a gloomy capital street where sick people lie on straw mats by the walls while worried physicians in green robes stand helpless. No main characters", "한양에 번진 괴질"),
    ("c20", [24], ["임금"], "", PALACE, "the king sitting alone at the low desk late at night, rubbing his tired eyes, piles of rolled exam papers beside him", "잠 못 이룬 임금"),
    ("c21", [25], ["임금"], "", PALACE, "the king seated at the low desk reaching out to take a few rolled exam papers held out toward him by two hands in dark teal sleeves coming in from the left edge of the picture; only the hands and sleeves of that person are visible", "장원 후보 답안"),
    ("c22", [26], ["임금"], "", PALACE, "the king reading a long sheet of exam paper and frowning deeply with suspicion", "어디선가 본 글"),
    ("c23", [27, 28], ["임금"], "", PALACE, "the king standing and pointing sternly toward the left edge of the picture with a cold face, a thick bundle of tied exam papers being held up by trembling hands in dark teal sleeves at the left edge; only those hands are visible", "떨어진 답안들도 가져오너라"),
    ("c24", [29], ["임금"], "", PALACE, "the king pulling out one short sheet from the bottom of a big pile of papers on the desk, looking at it with interest", "맨 아래의 짧은 답안"),
    ("c25", [30], [], "", PALACE + ", close-up on the desk", "close-up of a short sheet of rough paper on the desk filled with neat columns of brush strokes too small to read, with tiny ink drawings of a well, a steaming pot and a bowl. No people", "괴질을 막는 방법"),
    ("c26", [31], ["현"], VILLAGERS, VILLAGE + ", shown as a memory with a soft golden tint", "memory: the young scholar boiling water in a pot, villagers putting boards over a well, a sick villager lying alone in a separate room, a woman stirring salt and honey into water", "끓이고, 막고, 나누고, 채우고"),
    ("c27", [32], ["현_맨머리"], "", ROOM + ", night, shown as a memory with a soft golden tint", "memory: the young man writing records late at night by the oil lamp, many pages stacked neatly beside him", "열흘 동안 해 본 기록"),
    ("c28", [33], ["임금"], "", PALACE, "the king holding the short paper with both hands, deeply moved, eyes shining in the candlelight", "백성이 살아 있게 하는 것"),
    ("c29", [34, 35], ["임금"], "", PALACE, "the king standing and looking down coldly at the floor; at the bottom edge of the picture only the trembling back and dark teal sleeves of a man lying face down are visible", "엎드린 시험관"),
    ("c30", [36], ["시험관"], "", PALACE, "close view of the exam official lying prostrate on the floor, his face pale with fear, sweat on his forehead", "김 판서 대감께서"),
    ("c31", [37], ["임금"], "", PALACE, "the king with cold eyes dipping a brush and writing a name at the top of a sheet of paper", "장원 자리에 적은 이름"),
    ("c32", [38], ["임금"], COURT, GATE + ", night", "the king leaving the palace at night with retainers holding burning torches around him, walking quickly", "횃불을 든 신하들과 함께"),
    ("c33", [39], ["현", "아이"], VILLAGERS, ENTRY + ", night, a small fire", "the young scholar in his dirty sweaty patched robe kneeling and carefully giving salt water from a bowl to the sick village boy lying on a mat at the village entrance", "아이에게 소금물을 먹이다"),
    ("c34", [40], ["임금", "현"], VILLAGERS, ENTRY + ", night, torchlight", "torches lighting up the bright red royal robe of the king arriving; all villagers bowing down to the ground; the young scholar quickly kneeling", "붉은 곤룡포"),
    ("c35", [41, 42], ["임금", "현"], "", ENTRY + ", night, torchlight", "the king standing and looking down kindly at the young scholar kneeling before him, who looks up and answers firmly", "사람은 다시 살릴 수 없사옵니다"),
    ("c36", [43, 44], ["임금", "현"], "", ENTRY + ", night, torchlight", "the king bending down and placing both of his hands on the shoulders of the young scholar, lifting him up from kneeling; the young scholar half-rising in surprise; burning torches held by unseen retainers light the scene", "올해 과거의 장원은, 너다"),
    ("c37", [45], ["현"], "", ENTRY + ", night", "the young scholar standing, his face lit brightly by " + PANEL + " shining strongly in front of him, amazed", "세 번째 임무 완료"),
    ("c38", [46], [], SCHOLARS, GATE + ", morning", "a crowd of scholars gathered in front of the palace gate looking at a long white paper list hung on the wall, its writing too small to read, some cheering, some sighing. No main characters", "합격자 방이 붙다"),
    ("c39", [47], ["민호"], SOLDIERS, GATE + ", morning", "the plump young noble in the jade-green silk robe being dragged away by soldiers, shouting in panic", "자격을 잃은 김민호"),
    ("c40", [48], ["판서"], COURT, "a Joseon palace hall with red pillars", "the heavy-set minister standing calmly among court officials with a slight cold smile, hands folded in his sleeves", "벌을 피한 김 판서"),
    ("c41", [49, 50], ["판서"], "", MANSION + ", alone", "the heavy-set minister sitting alone in the dark room by one candle, smiling slyly with narrow eyes", "내 손바닥 안이다"),
    ("c42", [51], ["현_맨머리"], "", ROOM + ", night", "the young man startled, looking at " + PANEL + " flashing with a glowing red warning light at its edges", "위험, 궁궐 안에 적이 있습니다"),
],
3: [
    ("c01", [1], ["현"], COURT, GATE + ", gloomy day", "the young scholar, now the top exam passer, walking in through the big palace gate with a serious face, court officials watching him", "궁궐에 들어선 장원"),
    ("c02", [2], ["임금"], "", THRONE, "the king seated on the raised dais, holding out his hand with a firm trusting face as if giving an order", "내의원을 맡기다"),
    ("c03", [3], ["의원"], PHYS, NAEUI, "the old royal physician with a long white beard sneering with his arms folded, other old physicians behind him whispering coldly", "의술은 글로 배우는 것이 아니다"),
    ("c04", [4], ["현"], PHYS, NAEUI, "the young scholar standing alone in the middle of the pharmacy hall while old physicians turn their backs on him; in the doorway far behind stands the dark shadow of a heavy-set man", "대놓고 무시한 늙은 의원들"),
    ("c05", [5], ["현"], "", NAEUI + ", evening", "the young scholar looking up at " + PANEL + " with one glowing red line at its bottom", "네 번째 임무, 한양을 구하십시오"),
    ("c06", [6], ["현"], "", NAEUI + ", night", "the young scholar kneeling over a big hand-drawn map of the capital spread on the floor, three red mist marks glowing above three wells on the map", "우물 세 곳의 붉은 안개"),
    ("c07", [7], ["현"], COURT, THRONE, "the young scholar kneeling on the floor of the throne hall and speaking firmly upward toward the throne, court officials lined up on both sides", "우물을 막아야 하옵니다"),
    ("c08", [8, 9], ["판서"], COURT, THRONE, "the heavy-set minister in his dark crimson red official robe stepping forward from the line of officials and bowing toward the throne while speaking with a scornful face", "젊은 장원의 헛된 말이옵니다"),
    ("c09", [10], ["현"], "", NAEUI, "the young scholar showing a hand-drawn plan of a big quarantine house and a few lumps of homemade soap on a wooden board, explaining eagerly", "두 번째 혁신, 병막과 비누"),
    ("c10", [11], [], "", NAEUI + ", close-up", "close-up of rough brown lumps of homemade lye soap on a wooden board, white foam bubbles on a wet hand-sized lump, a small clay bowl of water. No people", "처음 보는 물건, 비누"),
    ("c11", [12], [], VILLAGERS, HANYANG + ", sunny day", "a capital street where wells are covered with wooden boards, big iron pots of water boil over fires on every corner, and people wash their hands with foaming soap in basins. No main characters", "막힌 우물, 거리마다 솥"),
    ("c12", [13], ["현"], VILLAGERS, QUAR + ", daytime", "the young scholar walking between the straw mats smiling with relief as patients sit up and drink from bowls", "절반으로 줄다"),
    ("c13", [14], [], CHILDREN, QUAR + ", night, dim lamplight", "seven thin children lying collapsed on straw mats in the quarantine house at night, women crying beside them, a scene of sudden alarm. No main characters", "쓰러진 아이 일곱 명"),
    ("c14", [15, 16], ["판서"], COURT, THRONE + ", night, candlelight", "the heavy-set minister kneeling in the throne hall and pointing back angrily as he accuses, his face full of false anger", "약에 독이 들었사옵니다"),
    ("c15", [17], ["현"], SOLDIERS, GATE + ", night", "the young scholar being dragged away by two soldiers through the palace gate at night, looking back calmly", "의금부로 끌려가다"),
    ("c16", [17], ["어머니"], "", GATE + ", night, cold moonlight", "the thin mother kneeling and bowing down on the stone ground in front of the closed palace gate at night, crying and calling out", "궁궐 문 앞의 어머니"),
    ("c17", [18], ["현_맨머리"], "", PRISON, "the young man sitting on the straw floor of the prison cell, looking up at " + PANEL + " glowing in the dark", "숨겨진 사실이 보입니다"),
    ("c18", [19], [], "", "a storehouse, shown as a memory with a soft sepia tint", "close-up of a stack of wooden medicine chests, each branded with the same small round burnt mark of a plum flower. No people", "상자에 찍힌 표시"),
    ("c19", [20], ["현_맨머리"], "", PRISON, "the young man in the dark cell surrounded by many glowing translucent blue pages of an account book floating in the air around him, too small to read", "기록을 되살립니다"),
    ("c20", [21], ["판서"], "", "a dark storehouse at night, shown as a memory with a soft sepia tint", "the heavy-set minister secretly watching servants swap bags of fresh good herbs for bags of rotten black herbs in wooden chests by lamplight", "빼돌린 좋은 약재"),
    ("c21", [22], ["현"], SOLDIERS, COURTYARD, "the young scholar kneeling in the middle of the stone courtyard for the final trial, raising his head with calm determined eyes, soldiers standing around", "마지막 심문"),
    ("c22", [23], ["현"], "", COURTYARD, "close view: the young scholar kneeling and speaking firmly with a steady gaze", "직접 보시옵소서"),
    ("c23", [24], ["임금"], "", THRONE, "the king standing on the dais and giving an order sternly with one hand raised", "창고와 장부를 가져오너라"),
    ("c24", [24], ["판서"], COURT, THRONE, "close view of the heavy-set minister's face starting to tremble, sweat on his brow, eyes darting", "처음으로 흔들린 얼굴"),
    ("c25", [25], [], SOLDIERS, COURTYARD, "soldiers opening many wooden medicine chests in the courtyard, every chest branded with the same small round plum flower mark, officials holding up thick account books. No main characters", "모두 같은 표시"),
    ("c26", [26], [], "", COURTYARD + ", close-up", "close-up of the last page of an old thread-bound account book filled with tiny brush strokes too small to read, a big square red seal stamp impression at the bottom of the page. No people", "김 판서의 도장"),
    ("c27", [27], ["판서"], "", COURTYARD, "the heavy-set minister kneeling on the stone ground, pale, raising both hands and pleading desperately", "이것은 모함이옵니다"),
    ("c28", [28, 29], ["판서"], "", COURTYARD, "an old thread-bound account book thrown down landing open on the stone ground right in front of the kneeling heavy-set minister, who stares at it in horror", "발 앞에 던진 장부"),
    ("c29", [30], ["판서"], SOLDIERS, SEA, "the heavy-set man, now in plain white clothes with no official cap, his black hair in a topknot, being led by soldiers onto a small wooden boat toward a far island, head hanging", "먼 섬으로 귀양"),
    ("c30", [31], ["현"], CHILDREN, QUAR + ", morning light", "seven recovered children sitting up and smiling, the young scholar kneeling and giving them bowls of warm water, mothers crying with joy", "다시 일어난 아이들"),
    ("c31", [32], [], VILLAGERS, MARKET + ", bright sunny day", "a lively market where merchants sell lumps of soap on straw mats, people carry pots of boiled water, children laughing. No main characters", "장원 비누"),
    ("c32", [33, 34], ["의원", "현"], PHYS, NAEUI, "the old royal physicians with white beards bowing their heads respectfully to the young scholar", "우리가 배우겠소"),
    ("c33", [35, 36], ["현"], "", NAEUI, "close view: the young scholar smiling warmly and gently shaking his head", "백성들이 함께 해낸 것"),
    ("c34", [37, 38], ["임금"], "", PALACE, "the king sitting at the low desk at night, looking forward with a warm curious smile, as if asking a question", "다른 세상에서 온 사람 같구나"),
    ("c35", [39, 40], ["현"], "", PALACE, "the young scholar kneeling in the candlelit room, answering quietly with a gentle, slightly sad smile", "사람을 살리는 일을 오래 해 온 사람"),
    ("c36", [41], ["어머니", "현_맨머리"], CHILDREN, YARD + ", late spring, warm afternoon", "the mother and the young man sitting together on the wooden porch of the thatched house smiling; in the yard children blow soap bubbles and run; the well is covered with a new wooden lid", "고향 초가집 마당"),
    ("c37", [42, 43], ["현_맨머리"], "", YARD + ", golden evening light", "the young man looking at " + PANEL + " glowing softly golden-white for the last time, a peaceful touched expression", "이제, 당신의 삶을 사십시오"),
    ("c38", [44], [], "", YARD + ", golden evening light, close-up", "close-up of two hands only: a young man's hand gently holding an older woman's thin hand on a worn beige skirt, warm evening light. Only these two hands", "어머니의 손"),
]}


def proj_of(part):
    return os.path.join(HERE, f"조선시스템_{part}부_프로젝트.json")


def paragraphs(story):
    return [p.strip() for p in re.split(r"\n\s*\n", story) if p.strip() and not p.strip().startswith("[사진")]


def ref_of(nm):
    r = REF[nm]
    return r if os.path.isabs(r) else os.path.join(SHEETS, r)


def prompt(cut):
    cid, _, who, others, place, desc, _ = cut
    p = (STYLE_2045 if "도현" in who else STYLE) + ". "
    if who:
        p += "In the scene: " + "; ".join(f"character from reference image {k + 1}: {LOOK[nm]}" for k, nm in enumerate(who)) + ". "
        if any(nm in CAPPED for nm in who):
            p += CAP_LINE
        p += "Each character appears only once, exactly two arms and two legs and five fingers on each hand, head and face turned the same direction as the body. "
    else:
        p += "No main characters. "
    if others:
        p += others
    else:
        p += "No other people besides those described in the scene. "
        if len(who) == 1:
            p += "Exactly one person in the whole image, no twin, no copy. "
    p += f"Scene: {desc}. Setting: {place}. "
    p += "Cinematic composition, full-bleed image, no border, no frame, no paper edges. No speech bubbles, no readable text, no letters, no signs with writing."
    return p


def main():
    cmd, part, folder = sys.argv[1], int(sys.argv[2]), sys.argv[3]
    cuts = CUTS[part]
    if cmd == "job":
        only = set(sys.argv[4:])
        items = [{"id": c[0], "width": 1024, "height": 576, "seed": 2100 + part * 100 + k, "prompt": prompt(c), "refs": [ref_of(nm) for nm in c[2]] + ([os.path.join(SHEETS, "_앞_군졸.png")] if c[3] is SOLDIERS else [])}
                 for k, c in enumerate(cuts) if not only or c[0] in only]
        os.makedirs(folder, exist_ok=True)
        out = os.path.join(folder, "job.json")
        json.dump({"items": items, "crop_border": True}, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(out, len(items), "cuts")
    elif cmd == "project":
        pj = proj_of(part)
        p = json.load(open(pj, encoding="utf-8"))
        paras = paragraphs(p["story"])
        first = {}
        for c in cuts:      # 한 문단에 그림 여러 장이면 차례로 (그 문단 시간을 나눠 보여 줌)
            first.setdefault(c[1][0], []).append(c)
        assert sorted(set(n for c in cuts for n in c[1])) == list(range(1, len(paras) + 1)), "문단 번호가 대본과 안 맞음"
        out = []
        for i, para in enumerate(paras, 1):
            for c in first.get(i, []):
                out.append(f"[사진: {os.path.join(folder, c[0] + '.png')} | {c[6]} | AI 생성 그림 (FLUX.2 klein) | ]")
            out.append(para)
        p["story"] = "\n\n".join(out)
        p["autophoto"] = False
        json.dump(p, open(pj, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(pj, len(cuts), "cuts")


if __name__ == "__main__":
    main()
