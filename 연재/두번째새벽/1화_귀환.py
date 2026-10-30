"""《두 번째 새벽》 1화 '귀환' — 대본 + 컷별 그림 계획
python 연재/두번째새벽/1화_귀환.py job <저장폴더>   → 그림 주문서(klein_worker 용) job.json
python 연재/두번째새벽/1화_귀환.py project <그림폴더> → 프로젝트 파일(render_project 용) 연재/두번째새벽/1화_귀환.json
대본의 {컷번호} 자리에 그 컷 그림이 들어감. chars = 그 컷에 나오는 인물(캐릭터 시트를 기준 그림으로 넣음)"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TITLE = "두 번째 새벽 1화 - 귀환"

# 대사 → 말하는 인물 (그 인물 목소리로 읽음, 목소리는 등장인물.json 의 voice)
DIALOGUE = [
    ("언젠가 저기에 가 볼 거야.", "한별"),
    ("우리는 지구로 돌아간다.", "선장"),
    ("지구는 원래 우리 땅입니다. 무엇이 기다리든, 되찾으면 됩니다.", "강무진 경"),
    ("아버지, 지구에 누가 살고 있으면요?", "서린"),
    ("그럼 그들이 비켜야겠지.", "강무진 경"),
    ("딱 한 번만. 진짜 땅을 밟아 보기만 하면 돼.", "한별"),
    ("오늘부터 이 땅은 다시 인간의 것이다.", "강무진 경"),
    ("멈춰라. 뭔가 있다.", "강무진 경"),
    ("쇠가... 깨어났다.", "강무진 경"),
]

# (컷번호, 나오는 인물, 그림 설명(영어), 화면 설명(한국어))
CUTS = [
    ("c01", [], "a burning Earth seen from orbit, nuclear mushroom clouds on the continents, a huge ark starship escaping into dark space", "핵전쟁으로 불타는 지구를 떠나는 방주선"),
    ("c02", [], "inside a vast old ark starship corridor, patched metal walls, hanging cloth banners with a red sun-and-flame emblem, people in medieval patched clothes", "수백 년이 흐른 방주선 안"),
    ("c03", ["한별"], "the girl working in a cramped engine room full of pipes and gauges, holding a wrench, sparks flying, oil on her cheek", "기관실의 정비공 견습 한별"),
    ("c04", ["한별"], "the girl pressing her hand against a round porthole window, looking at a small blue-green planet far away in space, wonder in her eyes", "창밖의 작은 파란 별을 바라보는 한별"),
    ("c05", [], "empty grain storage room in a starship, last few sacks, dim flickering lamps, rationing scale", "바닥을 드러낸 식량 창고"),
    ("c06", [], "a grand starship hall like a medieval throne room, an old captain sitting on a metal throne, knights in armor standing in rows, crowd of commoners", "선장의 대전"),
    ("c07", ["강무진 경"], "the knight commander standing before the throne, hand on his sword hilt, stern face, red cape", "기사단장 강무진 경"),
    ("c08", ["서린"], "the young priestess with a silver circlet holding a small candle, praying with closed eyes in a chapel with a red sun emblem on the wall", "기도하는 견습 사제 서린"),
    ("c09", ["서린", "강무진 경"], "the knight commander and the young priestess, his adopted daughter, talking quietly in a dim corridor, she looks worried, he looks away", "양녀 서린과 강무진"),
    ("c10", ["한별"], "the girl secretly reading a glowing old machine manual with strange letters by candlelight under a blanket", "몰래 옛 기계 글자를 읽는 한별"),
    ("c11", [], "a small old-fashioned landing shuttle in a hangar bay, knights loading crates and weapons, steam and lights", "착륙선에 짐을 싣는 기사들"),
    ("c12", ["한별"], "the girl sneaking between crates in a shuttle cargo hold, finger to her lips, mischievous determined face", "착륙선 화물칸에 숨어드는 한별"),
    ("c13", ["강무진 경"], "the knight commander strapped in a seat inside a shaking shuttle cockpit, looking out the window at a glowing atmosphere", "지구로 내려가는 착륙선"),
    ("c14", [], "a small shuttle falling through clouds over a vast green and gray land with ruined skyscrapers covered in forest", "구름을 뚫고 내려가는 착륙선"),
    ("c15", [], "a shuttle landed in a clearing among ruins overgrown with giant trees, dust settling, knights stepping out with shields", "폐허 숲에 내린 착륙선"),
    ("c16", ["강무진 경"], "the knight commander planting a banner with a red sun-and-flame emblem into the ground, knights kneeling behind him", "깃발을 꽂는 강무진"),
    ("c17", ["한별"], "the girl climbing out of a crate, eyes wide, touching real grass for the first time, sunlight on her face", "처음으로 흙과 풀을 만지는 한별"),
    ("c18", ["한별"], "the girl looking up at an enormous sky with real clouds and birds, cloak blowing in the wind, overwhelmed", "처음 보는 진짜 하늘"),
    ("c19", [], "giant ruined city overgrown with vines and trees, collapsed highway bridges, rusted cars buried in moss, eerie quiet", "숲에 삼켜진 옛 도시"),
    ("c20", ["한별"], "the girl walking alone through a ruined street, looking at faded old signs and a rusted traffic light", "폐허 거리를 홀로 걷는 한별"),
    ("c21", [], "strange giant claw marks scratched into a concrete wall, broken metal arm lying on the ground", "벽에 남은 거대한 긁힌 자국"),
    ("c22", [], "dense dark forest edge, several pairs of glowing amber eyes watching from the shadows between leaves", "숲속에서 지켜보는 눈들"),
    ("c23", ["강무진 경"], "the knight commander raising his fist to stop his troop, knights drawing swords, tense, looking at the forest", "멈추라는 강무진"),
    ("c24", ["서린"], "the young priestess at the shuttle door holding a medical satchel, worried, looking toward the forest", "착륙선에 남은 서린"),
    ("c25", ["한별"], "the girl hiding behind a rusted car, peeking out, a broken metal thing glinting in the grass nearby", "녹슨 차 뒤에 숨은 한별"),
    ("c26", ["한별"], "close-up of the girl's hand picking up an old cracked circuit board with a faded painted number 9", "숫자 9가 적힌 부품"),
    ("c27", [], "a dark collapsed subway entrance in the ruins, stairs going down into blackness, a faint blue glow deep inside", "어둠 속 희미한 파란 빛"),
    ("c28", ["한별"], "the girl stepping carefully down dark stairs with a small hand lamp, cobwebs and dripping water", "지하로 내려가는 한별"),
    ("c29", [], "an old underground maintenance hall full of broken robots slumped against walls, covered in moss and dust", "잠든 로봇들의 무덤"),
    ("c30", ["한별"], "the girl's face lit by her lamp, frightened but curious, looking at rows of broken robots", "숨을 죽인 한별"),
    ("c31", ["아홉"], "in the darkness a single round blue eye suddenly lights up on a skull-like metal face of a robot slumped against the wall", "켜지는 파란 외눈"),
    ("c32", ["한별"], "the girl falling backward in shock, lamp swinging, mouth open in a scream", "놀라 넘어지는 한별"),
    ("c33", ["아홉"], "the tall rusted skull-faced robot slowly standing up in the dark, moss falling from its body, number 9 on its chest", "천천히 일어서는 로봇"),
    ("c34", ["한별", "아홉"], "the tall skull-faced robot looming over the girl lying on the floor, its blue eye glowing, extending one long mechanical hand toward her", "한별에게 손을 뻗는 아홉"),
    ("c35", ["강무진 경"], "far above in the forest, the knight commander looking at a distant column of blue light rising from the ruins", "폐허에서 솟는 파란 빛을 본 강무진"),
    ("c36", [], "a huge ark starship hanging in orbit above Earth at dawn, the sun rising over the planet's edge", "지구 위 두 번째 새벽"),
]

STORY = """{c01}

수백 년 만의 귀환이었습니다. 핵전쟁으로 불타는 지구를 버리고 떠났던 사람들이, 다시 그 별로 돌아가려 하고 있었습니다.

모든 것은 그날 밤 시작됐습니다. 하늘이 불탔고, 도시가 사라지고, 바다가 끓었습니다. 거대한 배 한 척만이 불타는 지구를 떠났습니다. 사람들은 그 배를 방주선이라 불렀습니다. 다시는 돌아오지 못할 거라 믿으면서요.

그리고 수백 년 뒤, 방주선 맨 아래 기관실에서 자란 열일곱 살 소녀 한별이 아무도 몰래 지구로 내려가는 착륙선에 몸을 숨깁니다. 그 땅에서 무엇이 깨어나고 있는지도 모른 채로요.

끝까지 보시면, 인류가 맞이한 두 번째 새벽이 어떤 얼굴을 하고 있었는지 알게 되실 겁니다.

## 1. 별에서 태어난 아이

{c02}

수백 년이 흘렀습니다. 방주선 안의 세상은 옛날로 돌아가 있었습니다. 선장은 왕이 되었고, 칼을 찬 기사들이 복도를 지켰습니다. 사람들은 기운 옷을 입고, 고칠 수 없는 기계 앞에서 기도를 올렸습니다.

{c03}

열일곱 살 한별은 방주선 맨 아래, 기관실에서 일하는 정비공 견습입니다. 손에서 기름 냄새가 빠질 날이 없었습니다. 하지만 한별은 이 일이 좋았습니다. 쇠는 정직했으니까요. 고친 만큼 움직였습니다.

{c04}

일이 끝나면 한별은 늘 같은 창가로 갔습니다. 동그란 창 너머, 아주 멀리 작은 파란 별 하나가 떠 있었습니다. 어른들은 그 별을 '지구'라고 불렀습니다. 우리가 버리고 떠난 곳이었습니다.

"언젠가 저기에 가 볼 거야."

한별이 혼잣말을 할 때마다, 친구들은 웃었습니다. 지구는 죽은 별이라고요. 거기엔 아무것도 없다고요.

한별에게는 부모가 없었습니다. 기억나는 건 기관실의 따뜻한 쇳소리뿐이었습니다. 한별을 키운 건 늙은 정비사들이었고, 그들이 가르쳐 준 건 단 하나였습니다. '고장 난 건 버리지 말고, 고쳐라.' 한별은 가끔 생각했습니다. 그럼 지구도, 고칠 수 있지 않을까요? 그런데 잠시 뒤, 방주선 전체를 뒤흔드는 소식이 찾아옵니다.

## 2. 바닥난 창고

{c05}

그런데 그해, 방주선의 식량 창고가 바닥을 드러냈습니다. 마지막 곡식 자루를 세던 관리인의 손이 떨렸습니다. 이대로라면 한 해를 버티지 못합니다.

배급은 하루 두 끼에서 한 끼로 줄었습니다. 아이들이 먼저 야위었습니다. 기관실 사람들도 말이 없어졌습니다. 방주선 전체가 천천히, 소리 없이 죽어 가고 있었습니다.

{c06}

선장의 대전에 모두가 모였습니다. 늙은 선장이 무겁게 입을 열었습니다.

"우리는 지구로 돌아간다."

대전이 술렁였습니다. 수백 년 동안 아무도 입에 올리지 않던 말이었습니다.

{c07}

기사단장 강무진 경이 앞으로 나섰습니다. 왼뺨에 긴 흉터가 있는 남자였습니다. 그는 칼자루에 손을 얹고 말했습니다.

"지구는 원래 우리 땅입니다. 무엇이 기다리든, 되찾으면 됩니다."

그 말을 가장 조용히 듣고 있던 사람이 있었습니다. 이어서, 그녀의 이야기입니다.

## 3. 기도하는 사람

{c08}

같은 시각, 작은 기도실. 견습 사제 서린이 촛불 앞에 무릎을 꿇고 있었습니다. 정화교의 가르침은 단순했습니다. 생각하는 쇠는 죄입니다. 세상을 불태운 것은 사람이 아니라, 사람이 만든 기계였습니다.

{c09}

서린은 강무진 경의 양녀였습니다. 전쟁고아였던 그녀를 거둬 키운 사람이 바로 그였습니다.

"아버지, 지구에 누가 살고 있으면요?"

강무진은 대답 대신 고개를 돌렸습니다.

"그럼 그들이 비켜야겠지."

서린은 그 말이 오래도록 마음에 걸렸습니다.

{c10}

그날 밤, 한별은 이불 속에서 몰래 낡은 기계 설명서를 펼쳤습니다. 아무도 읽지 못하는 옛 글자로 쓰인 책이었습니다. 하지만 한별은 조금씩, 아주 조금씩 그 글자를 알아보기 시작했습니다. 들키면 큰일 날 비밀이었죠. 그리고 곧 그 비밀이, 한별을 아무도 가 보지 못한 곳으로 이끕니다.

## 4. 몰래 탄 착륙선

{c11}

며칠 뒤, 첫 착륙선이 출발 준비를 마쳤습니다. 기사들이 무기와 상자를 실었습니다. 정찰대였습니다. 지구에 먼저 내려가 땅을 살피는 일이었죠.

{c12}

한별은 이 기회를 놓칠 수 없었습니다. 기관실 열쇠로 화물칸 문을 열고, 상자 사이로 몸을 숨겼습니다. 심장이 터질 것 같았습니다.

'딱 한 번만. 진짜 땅을 밟아 보기만 하면 돼.'

{c13}

착륙선이 덜컹거리며 방주선을 떠났습니다. 조종석의 강무진 경은 창밖을 노려보았습니다. 붉게 달아오른 공기가 창을 핥았습니다.

{c14}

구름이 걷히자 아래로 땅이 보였습니다. 죽은 별이라던 지구는, 온통 초록이었습니다. 무너진 탑 같은 건물들 사이로 거대한 나무들이 하늘을 찌르고 있었습니다.

화물칸의 한별은 상자 틈으로 그 모습을 훔쳐보았습니다. 숨이 막혔습니다. 어른들이 수백 년 동안 말해 온 것은 거짓이었습니다. 지구는 죽지 않았습니다. 다만, 우리 없이 살아왔을 뿐이었습니다. 잠시 뒤, 한별은 처음으로 그 땅을 밟습니다.

## 5. 처음 밟은 땅

{c15}

착륙선이 폐허 한가운데 숲속 공터에 내려앉았습니다. 먼지가 가라앉자, 방패를 든 기사들이 하나둘 땅에 발을 디뎠습니다.

{c16}

강무진 경이 깃발을 땅에 꽂았습니다. 붉은 태양과 불꽃. 정화교의 문장이었습니다.

"오늘부터 이 땅은 다시 인간의 것이다."

기사들이 무릎을 꿇었습니다.

{c17}

그 순간, 화물칸의 상자 하나가 조용히 열렸습니다. 한별이었습니다. 한별은 떨리는 손으로 풀을 만졌습니다. 차갑고, 축축하고, 살아 있었습니다.

{c18}

고개를 들자 하늘이 있었습니다. 진짜 하늘. 끝이 없었습니다. 구름이 흘렀고, 새가 날았습니다. 바람이 망토를 흔들었습니다. 한별은 자기도 모르게 울고 있었습니다. 하지만 이 고요함 뒤에 무엇이 숨어 있는지, 곧 알게 됩니다.

## 6. 숲에 삼켜진 도시

{c19}

착륙선 너머로 옛 도시가 펼쳐져 있었습니다. 무너진 다리, 이끼에 묻힌 녹슨 자동차들. 숲이 도시를 천천히 삼키고 있었습니다. 너무 조용했습니다.

{c20}

한별은 기사들 몰래 폐허 거리로 들어섰습니다. 빛바랜 간판, 녹슨 신호등. 수백 년 전 사람들이 살던 흔적이 그대로 남아 있었습니다.

{c21}

그런데 이상한 게 눈에 띄었습니다. 콘크리트 벽에 새겨진 거대한 긁힌 자국. 그리고 그 아래 떨어진, 부러진 쇠 팔 하나.

뭔가가 여기서 싸웠습니다. 그것도 아주 최근에요.

한별은 부러진 쇠 팔을 내려다보았습니다. 이음새, 나사, 전선. 기관실에서 매일 보던 것들과 닮아 있었습니다. 하지만 이건 사람이 만든 기계가 아니라, 스스로 움직이던 무언가의 팔이었습니다. 등골이 서늘해졌습니다.

{c22}

그때였습니다. 숲 그늘 속에서 호박색 눈 여러 쌍이 반짝였습니다. 누군가 인간들을 지켜보고 있었습니다.

{c23}

강무진 경이 주먹을 들어 올렸습니다. 기사들이 일제히 칼을 뽑았습니다.

"멈춰라. 뭔가 있다."

{c24}

착륙선 문 앞에서 그 모습을 보던 서린이 약초 주머니를 꽉 쥐었습니다. 아버지는 싸울 준비를 하고 있었습니다. 하지만 서린은 생각했습니다. 저 눈들은 어쩌면, 우리를 두려워하는 건 아닐까요? 다음 장에서, 한별은 홀로 지하로 내려갑니다.

## 7. 숫자 9

{c25}

한편 한별은 녹슨 자동차 뒤에 몸을 숨기고 있었습니다. 기사들 쪽으로 돌아갈 길이 끊겼습니다. 그때, 풀숲에서 뭔가가 반짝였습니다.

{c26}

깨진 기계 부품이었습니다. 그 위에 빛바랜 숫자 하나가 적혀 있었습니다. 9.

{c27}

고개를 드니, 무너진 지하 계단이 보였습니다. 아래는 칠흑같이 어두웠습니다. 그런데 그 어둠 깊은 곳에서, 희미한 파란 빛이 깜빡이고 있었습니다.

{c28}

한별은 작은 손등불을 켜고 계단을 내려갔습니다. 물방울이 떨어지는 소리, 거미줄. 돌아가야 한다는 걸 알았습니다. 그런데 발이 멈추지 않았습니다.

{c29}

지하 끝에는 넓은 방이 있었습니다. 그리고 그곳에는, 수십 대의 로봇이 벽에 기대 쓰러져 있었습니다. 이끼와 먼지에 덮인 채로. 로봇들의 무덤이었습니다.

{c30}

한별은 숨을 죽였습니다. 정화교가 말하던 죄악. 생각하는 쇠. 그 앞에 한별이 서 있었습니다.

무서웠습니다. 그런데 이상하게도, 한별의 눈에는 그 로봇들이 괴물처럼 보이지 않았습니다. 고칠 사람이 없어 버려진 기계들. 기관실 구석에 쌓여 있던 고장 난 부품들처럼, 그저 쓸쓸해 보였습니다. 그런데 바로 다음 순간, 무덤 같던 방의 어둠 속에서 무언가가 눈을 떴습니다.

## 8. 깨어난 쇠귀신

{c31}

그 순간, 한 로봇의 얼굴에서 파란 눈 하나가 켜졌습니다. 해골 같은 쇠 얼굴. 깨진 눈구멍 옆에서, 외눈 하나가 한별을 똑바로 보고 있었습니다.

{c32}

한별은 비명을 지르며 뒤로 넘어졌습니다. 손등불이 바닥을 굴렀습니다.

{c33}

끼익, 쇠가 갈리는 소리. 로봇이 천천히 몸을 일으켰습니다. 몸에서 이끼가 우수수 떨어졌습니다. 가슴판에 바랜 숫자가 보였습니다. 9.

{c34}

키가 큰 로봇이 한별 위로 몸을 숙였습니다. 그리고 길고 가는 쇠 손가락을, 천천히 한별에게 뻗었습니다. 한별은 눈을 질끈 감았습니다.

{c35}

같은 시각, 숲 위의 강무진 경은 보았습니다. 폐허 한가운데서 파란 빛줄기가 하늘로 솟아오르는 것을. 그의 얼굴이 굳었습니다.

"쇠가... 깨어났다."

{c36}

수백 년 만에 지구 위로 해가 떠올랐습니다. 인간에게는 두 번째 새벽이었습니다. 그러나 이 땅이 그들을 반길지는, 아직 아무도 몰랐습니다.

하늘에서 돌아온 사람들, 숲속의 눈들, 그리고 깨어난 쇠. 세 갈래의 운명이 이제 막 만나려 하고 있었습니다.

돌아온 인류는 이번엔 다른 선택을 할 수 있을까요? 《두 번째 새벽》은 이 채널에서 매화 계속 이어집니다.

다음 이야기, 2화 쇠귀신. 로봇은 왜 한별을 해치지 않았을까요?"""


def main():
    cmd, folder = sys.argv[1], sys.argv[2]
    chars = {c["name"]: c for c in json.load(open(os.path.join(HERE, "등장인물.json"), encoding="utf-8"))["chars"]}
    src = open(os.path.join(HERE, "..", "..", "shorts_novel_maker_supertonic.py"), encoding="utf-8").read()
    style = re.search(r'"옛날 만화책\(세피아 펜화\)": "([^"]+)"', src).group(1)
    if cmd == "job":
        items = []
        for cid, who, desc, _ in CUTS:
            looks = "; ".join(f"{nm} (the character from reference image {k + 1}): {chars[nm]['look']}" for k, nm in enumerate(who))
            items.append({"id": cid, "width": 1024, "height": 576, "seed": 100 + int(cid[1:]),
                          "refs": [os.path.join(HERE, chars[nm]["face"]) for nm in who],
                          "prompt": f"{style}, medieval post-apocalyptic science fantasy comic panel. "
                                    + (f"Characters: {looks}. " if looks else "")
                                    + f"Scene: {desc}. Cinematic composition, full-bleed image, no border, no frame, no paper edges. No speech bubbles, no text, no letters."})
        os.makedirs(folder, exist_ok=True)
        json.dump({"items": items}, open(os.path.join(folder, "job.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(len(items), "cuts")
    elif cmd == "project":
        story = STORY
        for cid, _, _, cap in CUTS:
            story = story.replace("{" + cid + "}", f"[사진: {os.path.join(folder, cid + '.png')} | {cap} | AI 생성 그림 (FLUX.2 klein) | ]")
        proj = {"ver": 7, "category": "장문", "genre": "[이야기] SF·디스토피아", "topic": "두 번째 새벽", "title": TITLE,
                "story": story, "sources": [], "notes": "창작 연재 《두 번째 새벽》 1화", "autophoto": False, "img_source": "그림: 옛날 만화책",
                "cast": [{"name": nm, "look": c["look"], "look_ko": c["look_ko"], "voice": c.get("voice"),
                          **({"sheet": os.path.join(HERE, c["face"])} if c.get("face") else {})} for nm, c in chars.items()],
                "dialogue": [],   # 규칙(사용자 결정): 인물 대사도 따로 목소리 없이 모두 나레이션(남자 성우 2)이 읽음 (DIALOGUE 는 누가 한 말인지 기록용)
                "settings": {"format": "롱폼 가로(1920×1080)", "narr_voice": "Supertonic M2 (남성, 무료 로컬) [supertonic:M2]"}}
        out = os.path.join(HERE, "1화_귀환.json")
        json.dump(proj, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(out, len(story), "chars")


if __name__ == "__main__":
    main()
