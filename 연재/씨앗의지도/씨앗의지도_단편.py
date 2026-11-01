"""「씨앗의 지도」 단편 (약 10분, 일본 애니풍 — 「마지막 정비 명령」 후속 모험, 한 편으로 끝남) — 대본 + 컷별 그림 계획
python 연재/씨앗의지도/씨앗의지도_단편.py job <저장폴더>   → 그림 주문서(klein_worker 용) job.json
python 연재/씨앗의지도/씨앗의지도_단편.py project <그림폴더> → 프로젝트 파일 연재/씨앗의지도/씨앗의지도_단편.json
  영상은 render_project.py <프로젝트> --대본그대로 --길이고정 --형식고정
나레이션 한 명(남자 성우 4 · 정상 속도 · 톤 -1.5)이 대사까지 모두 읽음. 이야기·인물은 모두 지어낸 것"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TITLE = "씨앗의 지도"

STYLE = ("Japanese anime style scene, TV anime screenshot, clean crisp line art, anime cel shading with soft shadows, "
         "realistic human proportions, natural colors, detailed anime background art")
# 장소 (그림마다 꼭 적음)
PARK = ("Setting: outdoors in an overgrown abandoned city park with trees, flower beds, stone paths, old swings and a small carousel, "
        "ruined skyscrapers covered in vines far in the background. Not indoors, no factory")
SEA = ("Setting: a flooded ruined coastal town, half-sunken buildings and rusty rooftops sticking out of calm blue sea water, "
       "wooden plank walkways between rooftops, seagulls, bright sky")
SKY = ("Setting: Arka, a gleaming white city built on a huge floating rock island high above the clouds, white towers and glass domes, "
       "airships docked at its edges, clean and cold")
INSIDE = ("Setting: inside the white sky city, a long clean white corridor with tall windows showing clouds outside, cold blue lights")
OCEAN_SKY = "Setting: high in a wide blue sky above a sea of clouds"
VAULT = ("Setting: inside a huge underground seed vault carved into a mountain, rows of tall shelves holding thousands of small glass seed jars, "
         "warm lights slowly turning on, dust in the air")
MOUNTAIN = "Setting: a rocky mountainside above the ruined city, a huge round steel vault door half buried in the cliff, grass and wild flowers"
AIRSHIP = "Setting: inside the cabin of a battered old salvage airship, rusty metal walls, round windows, ropes and tools"

# (컷번호, 나오는 인물, 그림 설명(영어), 화면 설명(한국어), 장소)
CUTS = [
    ("c01", [], "wide view of the park at sunrise, flowers blooming, the carousel lights glowing, birds flying", "다시 열린 공원", PARK),
    ("c02", ["보리", "루미"], "the robot sweeping leaves on the path while the girl runs beside it laughing, holding a small basket", "보리와 루미의 아침", PARK),
    ("c03", ["도현"], "the father sitting on a bench repairing an old radio with small tools, smiling", "도현의 라디오", PARK),
    ("c04", ["루미"], "close-up of the girl holding her small silver round locket up to the morning light, it glows faintly blue", "빛나는 은빛 목걸이", PARK),
    ("c05", ["보리"], "close-up of the robot's blue eyes flickering with small lines of light, as if reading something hidden", "보리의 기억 장치", PARK),
    ("c06", [], "a huge white airship with silver fins appearing through the clouds above the park, its shadow covering the flowers", "하늘에서 내려온 그림자", PARK),
    ("c07", ["백도진"], "the tall commander in a white coat stepping down from a white airship ramp onto the park path, guards in white armor behind him", "하늘 도시 사령관 백도진", PARK),
    ("c08", ["백도진", "보리"], "the commander looking up coldly at the tall old robot, holding out a small glowing scanner", "300년 된 기억", PARK),
    ("c09", ["백도진"], "close-up of the commander's cold grey eyes, a faint thin smile", "지도를 찾았다", PARK),
    ("c10", ["루미"], "white-armored guards grabbing the girl by the arms as she struggles, her yellow raincoat flapping, no other civilians", "끌려가는 루미", PARK),
    ("c11", ["도현"], "the father being pushed down onto the ground by a guard, reaching out with one hand, shouting", "막지 못한 도현", PARK),
    ("c12", ["보리"], "the robot running toward the airship, its green scarf flying, as the ramp closes", "달려가는 보리", PARK),
    ("c13", [], "the white airship rising into the sky and disappearing into the clouds above the ruined city", "멀어지는 비행선", PARK),
    ("c14", ["보리"], "the robot standing alone at the park gate, looking out at the road leading away from the park, a long pause", "처음 나서는 공원 밖", PARK),
    ("c15", ["보리", "도현"], "the robot and the father walking side by side on a cracked road out of the ruined city toward the sea, morning light", "바다 쪽으로", "Setting: a cracked empty highway leading out of a ruined city toward the sea, grass growing through the asphalt"),
    ("c16", [], "wide view of the flooded coastal town, rooftops and plank walkways over calm water", "물에 잠긴 바다 마을", SEA),
    ("c17", ["다온"], "the boy running along a plank walkway between rooftops, jumping a gap with a coil of rope on his shoulder", "고철 줍는 소년 다온", SEA),
    ("c18", ["다온"], "the boy proudly standing beside a homemade glider made of scrap metal, canvas and bicycle parts, on a rooftop", "손으로 만든 글라이더", SEA),
    ("c19", ["다온", "보리"], "the boy stepping back in surprise as the tall robot appears on the rooftop, the boy holding up a wrench", "로봇과 소년", SEA),
    ("c20", ["다온"], "the boy standing on a rooftop walkway with arms crossed, listening seriously to someone off-screen, frowning, thinking", "하늘 도시 아르카", SEA),
    ("c21", ["다온"], "close-up of the boy pointing up at the sky, eyes bright with determination", "내 글라이더면 갈 수 있어", SEA),
    ("c22", ["강철수"], "the huge bald scavenger boss in a black leather coat appearing at the edge of the rooftop, arms crossed, frowning", "다시 나타난 강철수", SEA),
    ("c23", ["강철수", "도현"], "the scavenger boss and the father facing each other on a rooftop, tense", "빚을 갚으러 왔다", SEA),
    ("c24", [], "a battered old salvage airship with mechanical claws floating above the flooded town, its engines starting", "수거선의 시동", SEA),
    ("c25", ["강철수"], "the scavenger boss at the wheel of the airship cabin, grinning, steering hard", "하늘로", AIRSHIP),
    ("c26", [], "the battered salvage airship flying up through thick white clouds, the homemade glider tied on its back", "구름을 뚫고", OCEAN_SKY),
    ("c27", [], "the floating white sky city Arka appearing above the clouds, huge and shining", "하늘 도시 아르카", SKY),
    ("c28", ["루미"], "the girl sitting alone in a white room with a tall window full of clouds, hugging her knees, her locket glowing", "갇힌 루미", INSIDE),
    ("c29", ["백도진", "루미"], "the commander holding the girl's silver locket up to a glowing blue screen showing an abstract map with lines, no letters", "목걸이 속 지도", INSIDE),
    ("c30", ["백도진"], "the commander standing at a huge window looking down at the brown ruined earth below the clouds, hands behind his back", "땅을 내려다보는 사령관", INSIDE),
    ("c31", ["다온"], "the boy and his homemade glider leaping off the back of the salvage airship into the open sky", "글라이더 출격", OCEAN_SKY),
    ("c32", ["다온", "보리"], "the boy flying the homemade glider with the tall robot clinging to its frame, wind in their faces, clouds rushing past", "보리를 매단 글라이더", OCEAN_SKY),
    ("c33", [], "white guard airships with searchlights chasing a tiny glider through the clouds", "추격", OCEAN_SKY),
    ("c34", ["다온"], "close-up of the boy gritting his teeth and pulling the glider into a steep dive, goggles down", "급강하", OCEAN_SKY),
    ("c35", [], "wide shot in the sky: a battered rusty round-hulled salvage airship swinging its big mechanical claw arm and hitting a sleek white guard airship, sparks flying, the white ship tilting away, clouds below", "강철수의 집게발", OCEAN_SKY),
    ("c36", ["다온", "보리"], "the glider crash-landing on a white terrace of the sky city, the boy rolling and the robot landing on its feet", "아르카 착륙", SKY),
    ("c37", ["보리"], "the robot running down the long white corridor, its blue eyes scanning, guards falling behind", "루미를 찾아", INSIDE),
    ("c38", ["루미", "보리"], "the white door opening and the girl running into the robot's arms, the robot kneeling to catch her", "다시 만난 둘", INSIDE),
    ("c39", ["백도진"], "the commander standing in the doorway with guards, holding the glowing locket, calm and cold", "가로막는 사령관", INSIDE),
    ("c40", ["백도진", "보리"], "the commander speaking to the robot across the corridor, the robot standing in front of the girl protectively", "무기 창고가 아니다", INSIDE),
    ("c41", ["보리"], "the robot projecting a blue hologram of a young woman engineer in a white coat from its chest, light filling the corridor", "윤서의 마지막 기록", INSIDE),
    ("c42", [], "a hologram memory: a mountain vault being filled with thousands of glass seed jars by people 300 years ago, shown in translucent blue light", "300년 전의 씨앗 창고", INSIDE),
    ("c43", ["백도진"], "close-up of the commander's face, his cold eyes widening in shock, the blue hologram light on his face", "흔들리는 사령관", INSIDE),
    ("c44", ["백도진"], "the commander lowering the hand holding the locket, looking down at it silently", "땅을 버린 사람들", INSIDE),
    ("c45", ["백도진", "루미"], "the commander kneeling down and handing the silver locket back to the girl with his white glove", "돌려준 목걸이", INSIDE),
    ("c46", [], "the white airship, the salvage airship and the glider flying together down through the clouds toward a mountain", "함께 내려가는 하늘", OCEAN_SKY),
    ("c47", [], "a huge round steel vault door half buried in the mountain cliff, covered in vines", "산속의 문", MOUNTAIN),
    ("c48", ["루미"], "the girl pressing her glowing locket into a round slot in the center of the vault door, blue light spreading in circles", "열쇠가 된 목걸이", MOUNTAIN),
    ("c49", [], "the giant round vault door rolling open with dust and light pouring out", "300년 만에 열린 문", MOUNTAIN),
    ("c50", ["루미", "보리", "다온"], "the girl, the robot and the boy stepping into the huge seed vault, looking up in awe at endless shelves of glowing seed jars", "씨앗 창고", VAULT),
    ("c51", ["루미"], "close-up of the girl holding a small glass jar full of seeds in both hands, eyes shining", "씨앗 한 병", VAULT),
    ("c52", ["보리"], "the robot touching a shelf where a small worn plaque with a carved flower symbol hangs, no letters", "윤서의 꽃", VAULT),
    ("c53", ["강철수", "도현"], "the scavenger boss and the father carrying boxes of seed jars out of the vault together, laughing", "함께 나르는 씨앗", MOUNTAIN),
    ("c54", ["백도진"], "the commander taking off his white gloves and kneeling to touch the soil on the mountainside for the first time", "처음 만지는 흙", MOUNTAIN),
    ("c55", ["다온", "루미"], "the boy and the girl planting seeds in a row in dark soil at the edge of the park, dirt on their hands, smiling", "첫 씨앗", PARK),
    ("c56", ["보리"], "the robot watering the new seed rows with a green garden hose, gentle arc of water", "보리의 새 일", PARK),
    ("c57", [], "small green sprouts coming up from the soil in neat rows, morning dew", "돋아난 새싹", PARK),
    ("c58", ["보리", "루미", "다온"], "sunset in the park, the robot, the girl and the boy sitting on a bench looking at the fields of new sprouts beyond the park", "넓어진 공원", PARK),
    ("c59", [], "wide view of the ruined city with green fields spreading around the park, airships landing on the ground, hopeful golden light", "다시 푸르러지는 땅", PARK),
]

STORY = """{c01}

사람들이 떠난 도시에, 꽃이 지지 않는 공원이 하나 있습니다. 300년 동안 그 공원을 혼자 지킨 낡은 정비 로봇에게는, 이제 이름이 있습니다. 보리. 그리고 매일 아침, 손님이 찾아옵니다.

{c02}

열 살 소녀 루미였습니다. 루미는 바구니를 들고 보리 곁을 졸졸 따라다니며, 떨어진 열매를 주웠습니다. 사과 세 알, 이름 모를 빨간 열매 한 줌. 보리는 그 숫자를 하나도 빠뜨리지 않고 기록했습니다. 손님이 생긴 뒤로, 보리의 기록은 날마다 길어졌습니다.

{c03}

루미의 아빠 도현은 벤치에 앉아, 고장 난 라디오를 고쳤습니다. 도시 밖으로 나간 고철 수거단이 남기고 간 물건이었습니다.

{c04}

그런데 그날 아침, 루미의 은빛 목걸이가 이상하게 빛났습니다. 해에 비추자, 목걸이 안쪽에서 푸른빛이 새어 나왔습니다.

{c05}

보리의 눈도 함께 깜빡였습니다. 목걸이의 빛에 대답이라도 하듯이요. 300년 동안 한 번도 열리지 않던 기억 장치 한 칸이, 조용히 열리고 있었습니다.

{c06}

그때였습니다. 구름을 뚫고, 하얀 비행선 한 척이 공원 위로 내려왔습니다. 커다란 그림자가 꽃밭을 덮었습니다.

{c07}

비행선에서 내린 사람은, 흰 제복을 입은 남자였습니다. 구름 위에 떠 있는 하늘 도시, 아르카의 사령관 백도진이었습니다.

{c08}

백도진은 보리를 올려다보며, 작은 기계를 들이댔습니다. "역시. 300년 된 정비 로봇의 기억 장치. 신호가 여기서 나왔군."

{c09}

사령관의 입가에, 얇은 웃음이 걸렸습니다. "땅 위 어딘가에 숨겨진 창고. 그 지도가, 이 로봇과 저 목걸이 안에 있다."

{c10}

흰 갑옷의 병사들이 루미의 팔을 붙잡았습니다. "놔! 놔 주세요!" 노란 비옷이 버둥거렸습니다.

{c11}

도현이 달려들었지만, 병사의 손에 밀려 땅에 쓰러졌습니다. "루미야!"

{c12}

보리가 비행선을 향해 달렸습니다. 하지만 계단이 닫히는 것이, 조금 더 빨랐습니다.

{c13}

하얀 비행선은 하늘로 떠올라, 구름 속으로 사라졌습니다. 공원에는 꽃잎만 흩날렸습니다. 도현은 주먹으로 땅을 내리쳤습니다. 하늘 위의 도시까지 쫓아갈 방법은, 아무것도 없어 보였습니다.

{c14}

보리는 공원 정문 앞에 멈춰 섰습니다. 300년 동안, 단 한 번도 넘어 본 적 없는 문이었습니다. 공원을 지켜라. 그것이 보리의 명령이었습니다.

{c15}

하지만 보리는, 문을 넘었습니다. 지킬 것은 공원이 아니라, 공원에서 웃던 아이라는 것을 이제는 알았으니까요. 도현과 보리는 바다 쪽으로 걸었습니다.

{c16}

도시 끝에는, 물에 잠긴 바다 마을이 있었습니다. 지붕들만 물 위로 솟아 있었고, 그 사이를 나무다리가 잇고 있었습니다. 수거단조차 잘 오지 않는, 잊힌 마을이었습니다.

{c17}

그 나무다리 위를, 한 소년이 날듯이 뛰어다니고 있었습니다. 어깨에 밧줄을 멘, 열두 살 다온이었습니다.

{c18}

다온은 이 마을에서 혼자 고철을 주우며 살았습니다. 그리고 그 쇠붙이로, 아무도 만든 적 없는 것을 만들었습니다. 하늘을 나는 글라이더였습니다. 자전거 바퀴, 낡은 돛, 녹슨 파이프. 다온은 그것을 타고 바다 위를 날아다녔습니다. 언젠가 구름 위까지 가 보는 것이, 다온의 꿈이었습니다.

{c19}

키 큰 로봇이 지붕 위로 올라오자, 다온은 렌치를 번쩍 들었습니다. "수거단이냐? 내 물건엔 손대지 마!"

{c20}

도현은 무릎을 꿇고, 모든 이야기를 들려주었습니다. 다온은 팔짱을 낀 채 듣다가, 하늘을 올려다보았습니다.

{c21}

"아르카? 구름 위에 떠 있는 그 도시? 내 글라이더면, 갈 수 있어."

{c22}

그때 지붕 끝에서, 낮은 목소리가 들렸습니다. "글라이더 혼자서는 구름까지도 못 올라간다." 고철 수거단 두목, 강철수였습니다.

{c23}

도현이 굳은 얼굴로 돌아섰습니다. 보리를 쇠사슬로 묶어 끌고 가려 했던 남자였습니다. 강철수는 머리를 긁었습니다. "그날 빚을 갚으러 왔다. 내 배를 빌려주지."

{c24}

낡은 수거선의 엔진이, 덜컹거리며 깨어났습니다.

{c25}

강철수가 키를 잡고 씩 웃었습니다. "꽉 잡아라. 이 고물은, 위로 가는 건 처음이거든."

{c26}

수거선은 두꺼운 구름을 뚫고 올라갔습니다. 배 등에는, 다온의 글라이더가 묶여 있었습니다.

{c27}

그리고 구름 위에, 하얀 도시가 나타났습니다. 거대한 바위섬 위에 지어진, 차갑게 빛나는 도시 아르카.

{c28}

그 도시의 하얀 방 안에, 루미가 무릎을 끌어안고 앉아 있었습니다. 창밖에는 구름뿐이었습니다. 루미는 목걸이를 꼭 쥐고 속삭였습니다. "보리, 공원 잘 지키고 있어. 금방 갈게." 그런데 목걸이는, 이미 사령관의 손에 넘어간 뒤였습니다.

{c29}

백도진이 루미의 목걸이를 화면에 갖다 댔습니다. 푸른 선이 하나둘 이어지자, 지도 하나가 떠올랐습니다. "300년 전 사람들이 숨겨 둔 창고. 거기엔 땅을 다스릴 힘이 있을 것이다."

{c30}

사령관은 창가에 서서, 구름 아래 갈색 땅을 내려다보았습니다. 아르카 사람들은 300년 동안, 저 땅을 버려진 곳이라고 불렀습니다. 그러나 하늘 도시의 물탱크도, 식량 창고도 바닥나고 있었습니다. 사령관에게 그 창고는, 도시를 지킬 마지막 희망이었습니다.

{c31}

그 시각. 수거선 등 위에서, 다온의 글라이더가 하늘로 뛰어내렸습니다.

{c32}

글라이더 틀에는, 보리가 매달려 있었습니다. 바람이 얼굴을 때렸고, 구름이 눈앞을 스쳐 지나갔습니다.

{c33}

곧 하얀 경비선들이 탐조등을 켜고 쫓아왔습니다. 날카로운 경보음이 구름 사이로 울렸습니다. 작은 글라이더 하나를 잡으려고, 아르카의 배들이 사방에서 몰려들었습니다.

{c34}

다온은 이를 악물고, 글라이더를 아래로 꺾었습니다. "보리, 꽉 잡아!"

{c35}

그 순간, 강철수의 수거선이 커다란 집게발을 휘둘렀습니다. 경비선 한 척이, 불꽃을 튀기며 옆으로 밀려났습니다.

{c36}

글라이더는 아르카의 하얀 테라스에 거칠게 내려앉았습니다. 다온은 바닥에 나뒹굴었고, 보리는 두 발로 단단히 섰습니다. "루미는 내가 찾을게. 넌 숨어 있어!" 다온은 고개를 저었습니다. "싫어. 여기까지 왔는데."

{c37}

보리는 긴 하얀 복도를 달렸습니다. 푸른 눈으로 벽 너머를 살폈습니다. 루미의 목걸이 신호가, 가까워지고 있었습니다.

{c38}

문이 열리자, 루미가 보리의 품으로 뛰어들었습니다. "보리! 올 줄 알았어!"

{c39}

하지만 문 앞에, 백도진이 병사들과 서 있었습니다. 손에는 루미의 목걸이가 들려 있었습니다.

{c40}

보리가 루미 앞을 막아섰습니다. 그리고 처음으로, 사령관에게 말했습니다. "당신이 찾는 창고는, 무기 창고가 아닙니다."

{c41}

보리의 가슴에서 푸른빛이 솟았습니다. 300년 전 공원을 만든 기술자, 윤서의 모습이 복도에 떠올랐습니다.

{c42}

"우리는 하늘로 떠나지만, 씨앗은 땅에 남긴다. 언젠가, 땅을 다시 푸르게 할 사람에게." 기록 속에서 사람들은, 산속 창고에 씨앗 병을 끝없이 채우고 있었습니다.

{c43}

백도진의 차가운 눈이, 크게 흔들렸습니다.

{c44}

사령관은 목걸이를 쥔 손을 천천히 내렸습니다. 300년 동안 구름 위에서 살아온 사람들. 땅으로 돌아갈 길을, 처음부터 땅이 품고 있었던 것입니다.

{c45}

백도진은 무릎을 꿇고, 흰 장갑 낀 손으로 목걸이를 돌려주었습니다. "이건, 네 것이다."

{c46}

그날 오후, 하얀 비행선과 낡은 수거선과 작은 글라이더가, 나란히 구름 아래로 내려갔습니다.

{c47}

지도에 표시된 곳은, 도시 뒤편의 산이었습니다. 덩굴로 뒤덮인 둥근 쇠문 하나가, 절벽에 반쯤 묻혀 있었습니다.

{c48}

루미가 목걸이를 문 한가운데 홈에 끼웠습니다. 푸른빛이, 물결처럼 동그랗게 퍼져 나갔습니다.

{c49}

그리고 300년 만에, 거대한 문이 굴러 열렸습니다.

{c50}

안에는, 끝이 보이지 않는 선반이 있었습니다. 그리고 그 위에, 수만 개의 작은 유리병이 빛나고 있었습니다.

{c51}

루미가 병 하나를 두 손으로 들었습니다. 그 안에는, 작은 씨앗이 빼곡히 담겨 있었습니다. 밀, 보리, 콩, 사과, 그리고 이름도 모르는 꽃들. 병마다, 300년 전의 날짜가 적혀 있었습니다.

{c52}

보리는 선반에 걸린 작은 판을 쓰다듬었습니다. 꽃 한 송이가 새겨져 있었습니다. 윤서가 제일 좋아하던 꽃이었습니다. 공원 꽃밭에도, 300년 동안 그 꽃이 피어 있었습니다. 보리가 하루도 빠짐없이 물을 준 꽃이었습니다.

{c53}

강철수와 도현은 씨앗 상자를 함께 날랐습니다. 며칠 전까지 서로 노려보던 두 사람이, 같이 웃고 있었습니다.

{c54}

백도진은 흰 장갑을 벗었습니다. 그리고 태어나 처음으로, 맨손으로 흙을 만졌습니다. 흙은, 생각보다 따뜻했습니다.

{c55}

공원 가장자리에서, 다온과 루미가 첫 씨앗을 심었습니다. 손도 얼굴도, 온통 흙투성이였습니다.

{c56}

보리는 호스로 물을 주었습니다. 300년 동안 공원만 지키던 로봇에게, 새로운 일이 생긴 것입니다.

{c57}

며칠 뒤, 땅 위로 작은 새싹들이 줄지어 올라왔습니다.

{c58}

해가 질 무렵, 셋은 벤치에 나란히 앉았습니다. 공원 너머로, 초록빛이 조금씩 번져 가고 있었습니다. 다온은 이제 바다 마을과 공원을 글라이더로 오가며, 씨앗을 실어 날랐습니다. "보리, 이제 공원이 엄청 넓어지겠다." 보리의 눈이 따뜻하게 빛났습니다. "그럼, 더 열심히 쓸어야겠네요."

{c59}

꽃이 지지 않는 공원은, 이제 하나가 아닙니다. 구름 위에 살던 사람들도 하나둘 땅으로 내려와, 씨앗을 심기 시작했습니다. 300년 전 누군가가 남긴 약속이, 마침내 싹을 틔운 것입니다.
"""


def main():
    cmd, folder = sys.argv[1], sys.argv[2]
    chars = {c["name"]: c for c in json.load(open(os.path.join(HERE, "등장인물.json"), encoding="utf-8"))["chars"]}
    if cmd == "job":
        items = []
        for cid, who, desc, _, place in CUTS:
            looks = "; ".join(f"person {k + 1} (exactly as in reference image {k + 1}): {chars[nm]['look']}, {chars[nm]['outfit']}"
                              for k, nm in enumerate(who))
            crowd = any(w in desc for w in ("guards", "airships", "people"))
            items.append({"id": cid, "width": 1024, "height": 576, "seed": 500 + len(items),
                          "refs": [os.path.join(HERE, chars[nm]["face"]) for nm in who],
                          "prompt": f"{STYLE}, adventure drama. "
                                    + (f"Characters: {looks}. Each person appears only once, exactly two arms and two legs, head and face turned the same direction as the body. " if looks else "No main characters. ")
                                    + ("The robot is exactly the slender white rusty humanoid robot from the reference sheet with a green scarf, not a different robot. " if "보리" in who else "")
                                    + ("" if crowd else "No other people in the scene. ")
                                    + f"Scene: {desc}. {place}. "
                                    + "Cinematic composition, full-bleed image, no border, no frame, no paper edges. No speech bubbles, no text, no letters."})
        os.makedirs(folder, exist_ok=True)
        json.dump({"items": items}, open(os.path.join(folder, "job.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(len(items), "cuts")
    elif cmd == "project":
        story = STORY
        for cid, _, _, cap, _ in CUTS:
            story = story.replace("{" + cid + "}", f"[사진: {os.path.join(folder, cid + '.png')} | {cap} | AI 생성 그림 (FLUX.2 klein) | ]")
        proj = {"ver": 7, "category": "장문", "genre": "[이야기] SF 드라마", "topic": TITLE, "title": TITLE,
                "story": story, "sources": [], "notes": "「마지막 정비 명령」 후속 모험 단편 (약 10분, 일본 애니풍)", "autophoto": False, "img_source": "그림: 애니 일러스트",
                "cast": [{"name": nm, "look": c["look"], "look_ko": c["look_ko"], "sheet": os.path.join(HERE, c["face"])} for nm, c in chars.items()],
                "settings": {"format": "롱폼 가로(1920×1080)", "narration": "on",
                             "layout": "자막형(큰 제목+사진+자막)", "img_fill": "전체 화면(글자가 사진 위에)",
                             "img_motion": "영상처럼(확대·이동·전환)", "fps": "24", "img_depth": "off",
                             "head_show": "안 보임(제목 카드만)", "head_pos": "숨김", "sub_split": "한 줄씩(문장·쉼표로 나눠 차례로)",
                             "img_label": "off", "sub_hide": "off", "bgm_mode": "자동생성", "bgm_style": "감성 오르골",
                             "narr_voice": "Supertonic M4 (남성, 무료 로컬) [supertonic:M4]", "narr_rate": "0", "narr_tone_m": -1.5}}
        out = os.path.join(HERE, "씨앗의지도_단편.json")
        json.dump(proj, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(out, len(story), "chars")


if __name__ == "__main__":
    main()
