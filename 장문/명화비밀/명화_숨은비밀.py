"""장문 미스터리 다큐 '과학이 밝혀낸 명화 속 숨은 비밀 5가지' — 대본 + 컷별 그림·사진 계획
python 장문/명화비밀/명화_숨은비밀.py job <저장폴더> [c01,c02,...]  → 그림 주문서(klein_worker 용, 유화) job.json (사진 컷은 빼고)
python 장문/명화비밀/명화_숨은비밀.py project <그림폴더>          → 프로젝트 파일(render_project 용) 장문/명화비밀/명화_숨은비밀.json
장문은 실제 사진 위주(사용자 결정): PHOTOS 의 컷은 위키미디어 공용 사진(사진/<컷>.jpg, 출처·라이선스 표시),
나머지는 AI 그림(유화풍) — 실제 그림·장소가 나오면 REFS 의 실제 사진을 기준 그림으로. 사진 후보 받기: ../안티키테라/사진_찾기.py 방식
사실 확인: 프라도·마우리츠하위스·드레스덴 회화관 공개 자료, Heritage Science(2023, 브래드퍼드대), 노트르 프롬 폴란드·CBS(2025),
The Art Newspaper(2019·2020, 클림트), Northwestern Engineering(2026, Hidden Paintings, Layered Histories)"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
TITLE = "과학이 밝혀낸 명화 속 숨은 비밀 5가지"
STYLE_NAME = "다큐 수채화"   # 사용자 결정 2026-10-25: 장문은 수채화 (유화는 손가락·팔이 자주 틀림)
DIALOGUE = []     # 다큐라 인물 대사 없음 (나레이션만)

# (컷번호, 그림 설명(영어), 화면 설명(한국어))
CUTS = [
    ("c01", "a gardener in work clothes pulling ivy off an old museum's outer stone wall and opening a small rusty metal hatch, a dark cavity with a plastic bag inside", "담쟁이 뒤 철문을 연 정원사"),
    ("c02", "Gustav Klimt's portrait of a woman painting (real painting)", "클림트 '여인의 초상'"),
    ("c03", "a conservator in a dark laboratory looking at a glowing X-ray image of a painting on a light box, a hidden second face faintly visible", "엑스선 속 숨은 얼굴"),
    ("c04", "a grand old European art museum gallery at night, famous paintings on the walls lit by soft spotlights, empty and mysterious. No people, no hands, no arms anywhere.", "밤의 미술관"),
    ("c05", "Raphael's Madonna della Rosa painting (real painting)", "라파엘로 '장미의 성모'"),
    ("c06", "the Prado Museum building in Madrid (real photo)", "프라도 미술관"),
    ("c07", "a computer scientist in a modern lab watching large screens that show a Renaissance Madonna painting divided into square patches with colored heat-map overlays, no text", "AI가 붓질을 나눠 보는 장면"),
    ("c08", "close-up of the bearded face of Saint Joseph in a Renaissance painting, a magnifying glass over it, dramatic light", "요셉의 얼굴"),
    ("c09", "a Renaissance painter's workshop in Rome, a master and several young apprentices painting on one large panel together, candlelight", "스승과 제자들의 공방"),
    ("c10", "Rembrandt's The Anatomy Lesson of Dr Nicolaes Tulp painting (real painting)", "렘브란트 '튈프 박사의 해부학 강의'"),
    ("c11", "the Mauritshuis museum building in The Hague by the pond (real photo)", "마우리츠하위스 미술관"),
    ("c12", "a 17th century anatomy theatre in Amsterdam, wooden tiers full of men in black clothes and white collars watching a dissection, candles, no gore visible", "1632년 해부학 강의실"),
    ("c13", "a technician placing a large old painting under an X-ray scanner in a museum conservation studio, glowing screens", "그림을 찍는 엑스선 장비"),
    ("c14", "a grey X-ray image of a painted arm on a light box showing a different shape underneath the paint, mysterious and clinical, no text", "엑스선에 드러난 팔"),
    ("c15", "Pieter Brueghel the Younger style Flemish genre painting of a peasant woman carrying burning embers in one hand and a water bucket in the other (real painting)", "브뤼헐 '불씨를 나르는 여인'"),
    ("c16", "the National Museum in Gdansk building, old Gothic brick monastery (real photo)", "그단스크 국립박물관"),
    ("c17", "a cleaning woman in a 1970s museum accidentally knocking a small framed painting off the wall, the frame falling, shocked face, dim gallery", "1974년, 떨어진 액자"),
    ("c18", "close-up of an old gilded frame lying on the floor with a glossy magazine page cut out and glued inside instead of a real painting. No people, no hands, no arms anywhere.", "액자 속 잡지 사진"),
    ("c19", "a magazine editor at a desk covered with old art magazines and black-and-white photographs, comparing a photo with a museum catalogue, lamp light", "옛 사진을 대조하는 잡지 편집자"),
    ("c20", "a small Dutch town museum with brick gables and a canal in Gouda (real photo)", "네덜란드 하우다 박물관"),
    ("c21", "an art detective in a dark coat standing in front of a small Flemish painting in a museum, studying it closely with a flashlight", "그림을 확인하는 미술 탐정"),
    ("c22", "Johannes Vermeer's Girl Reading a Letter at an Open Window painting before restoration, plain wall (real painting)", "베르메르 '창가에서 편지를 읽는 여인' (복원 전)"),
    ("c23", "the Zwinger palace in Dresden with the Old Masters Picture Gallery (real photo)", "드레스덴 츠빙거 궁전·회화관"),
    ("c24", "a conservator in a white coat bending over an old Dutch painting with a surgical scalpel and a microscope, removing a tiny piece of grey overpaint from the wall area", "덧칠을 벗기는 복원가"),
    ("c25", "Vermeer's Girl Reading a Letter at an Open Window after restoration with the large Cupid painting on the wall behind her (real painting)", "복원 뒤 드러난 큐피드"),
    ("c26", "close-up of a painted Cupid figure with bow, standing on masks, in a 17th century Dutch painting-within-a-painting, soft light", "벽 속 그림의 큐피드"),
    ("c27", "the Ricci Oddi Gallery of Modern Art building in Piacenza, Italy (real photo)", "피아첸차 리치 오디 미술관"),
    ("c28", "night, a thief's gloved hand lowering a fishing line through a museum skylight toward a painting on the wall below, moonlight, tense", "1997년 2월, 사라진 그림"),
    ("c29", "an empty ornate picture frame lying on a flat museum roof at dawn next to a skylight, police officers looking at it", "지붕 위의 빈 액자"),
    ("c30", "Italian police investigators in a 1990s office covered with photographs and notes about a stolen painting, cigarette smoke, files", "22년 동안 풀리지 않은 수사"),
    ("c31", "close-up of a black plastic bag being pulled out of a cavity in an old stone wall covered with ivy, a corner of a painted canvas visible", "벽 속에서 나온 가방"),
    ("c32", "art experts in white gloves examining a portrait painting under ultraviolet light in a laboratory, purple glow, careful", "진짜인지 확인하는 전문가들"),
    ("c33", "a young art student in 1996 comparing two printed images of portraits side by side at a library table, one in old black-and-white, eyes wide with discovery", "두 그림을 겹쳐 본 미술 학도"),
    ("c34", "a ghostly second portrait of a young woman in a hat faintly emerging beneath a painted portrait of a woman, like two layers, mysterious. No people, no hands, no arms anywhere.", "그림 밑의 또 다른 여인"),
    ("c35", "a scientist in a modern lab with an AI separating an X-ray image of a painting into several glowing translucent layers floating in the air, no text", "층을 나눠 보는 AI"),
    ("c36", "a quiet museum hall at closing time, a single spotlight on an old painting, a visitor's silhouette looking at it, mysterious atmosphere", "아직 잠든 비밀"),
]

STORY = """{c01}

2019년 12월, 이탈리아의 한 미술관 바깥벽에서 사라졌던 명화가 나왔습니다. 담쟁이를 걷어 내던 정원사가 작은 철문을 열자, 검은 비닐 가방이 들어 있었습니다.

{c02}

가방 속에는 그림 한 점이 있었습니다. 22년 전에 사라진, 수백억 원짜리 클림트였습니다.

{c03}

그런데 이 그림의 비밀은 그게 끝이 아니었습니다. 물감 밑에는 또 다른 여인이 숨어 있었습니다.

{c04}

오늘은 과학이 밝혀낸 명화 속 숨은 비밀 다섯 가지를 다섯 번째부터 차례로 따라갑니다. 끝까지 보시면, 벽 속에서 나온 그림이 왜 두 번 사람들을 놀라게 했는지 알게 되실 겁니다.

## 1. 다섯 번째 비밀, AI가 찾아낸 낯선 얼굴

{c05}

스페인 마드리드의 프라도 미술관에는 라파엘로의 '장미의 성모'가 걸려 있습니다. 성모와 아기 예수, 어린 요한, 그리고 뒤편의 요셉이 함께 있는 그림입니다.

{c06}

이 그림을 두고 학자들은 오래 다퉜습니다. 정말 라파엘로가 혼자 다 그렸을까. 아니면 제자의 손이 섞였을까.

{c07}

2023년, 영국 브래드퍼드 대학 연구팀이 이 질문을 AI에게 맡겼습니다. 라파엘로의 진품 49점으로 붓질의 버릇을 가르쳤습니다. 진품을 알아맞히는 정확도는 98퍼센트였습니다.

{c08}

처음에 그림 전체를 넣었을 때는 답이 흐릿했습니다. 그래서 인물을 하나씩 잘라 다시 넣었습니다. 성모와 아기들은 라파엘로였습니다. 그런데 요셉의 얼굴만은 아니라는 답이 나왔습니다.

{c09}

라파엘로의 공방에는 제자가 많았습니다. 연구에 참여한 학자는 제자 줄리오 로마노를 후보로 꼽았습니다. 다만 아직 확실한 것은 아닙니다. 그리고 이어서 볼 그림에서는, 화가가 일부러 무언가를 감췄습니다.

## 2. 네 번째 비밀, 해부학 강의 속 사라진 손

{c10}

1632년, 스물여섯 살의 렘브란트가 그린 '튈프 박사의 해부학 강의'. 지금은 네덜란드 헤이그의 마우리츠하위스 미술관에 있습니다.

{c11}

그림 한가운데 누운 사람은 사형당한 죄수 아리스 킨트입니다. 그날 암스테르담에서는 실제로 공개 해부 강의가 열렸습니다.

{c12}

검은 옷의 의사들이 시신을 둘러싸고, 튈프 박사가 팔의 힘줄을 들어 보입니다. 겉으로는 아무 이상이 없어 보입니다.

{c13}

그런데 엑스선으로 그림 속을 들여다보자, 이상한 것이 드러났습니다.

{c14}

렘브란트는 처음에 시신의 오른손을 손이 아니라 잘린 팔목으로 그렸던 것입니다. 이 죄수가 예전에 벌로 손을 잃었을 수 있다는 뜻입니다. 렘브란트가 그 강의를 직접 보았다는 증거로도 여겨집니다.

{c14}

나중에 그 위에 손을 덧그렸습니다. 그래서 지금도 그 손만 팔과 색이 조금 다릅니다. 너무 눈에 띄는 잘린 팔목을 감추고 싶었던 걸까요? 이어서 세 번째 비밀입니다. 이번에는 그림이 통째로 사라졌습니다.

## 3. 세 번째 비밀, 잡지 사진과 바꿔치기된 그림

{c15}

피터르 브뤼헐 2세의 작은 그림, '불씨를 나르는 여인'. 한 손에는 불씨를, 다른 손에는 물통을 든 여인을 그렸습니다.

{c16}

이 그림은 폴란드 그단스크 국립박물관에 걸려 있었습니다.

{c17}

1974년 4월, 청소를 하던 직원이 실수로 액자를 떨어뜨렸습니다.

{c18}

그런데 액자 속에 든 것은 그림이 아니었습니다. 잡지에서 오려 낸 인쇄 사진이었습니다. 누군가 진짜를 빼 가고 사진을 대신 넣어 둔 것이었습니다. 반 다이크의 스케치도 같은 방법으로 바뀌어 있었습니다.

{c18}

사건을 증언할 수 있던 세관원은 증언을 앞두고 숨졌습니다. 수사는 멈췄고, 그림은 그렇게 반세기 동안 사라졌습니다.

{c19}

2025년, 네덜란드 미술 잡지의 편집자 존 브로지우스는 1974년 도난 사건을 다룬 폴란드 기사를 읽다가 한 그림을 떠올렸습니다.

{c20}

네덜란드 하우다의 박물관에, 개인 소장자가 빌려준 바로 그 그림이 걸려 있었던 것입니다.

{c21}

미술 탐정 아르튀르 브란트가 폴란드의 옛 기록과 대조했습니다. 결과는 백 퍼센트 같은 그림이었습니다. 폴란드는 지금 그림을 돌려받으려 하고 있습니다. 이어서 두 번째 비밀은, 300년 넘게 벽에 가려져 있었습니다.

## 4. 두 번째 비밀, 300년 동안 가려진 큐피드

{c22}

베르메르의 '창가에서 편지를 읽는 여인'. 열린 창가에서 한 여인이 조용히 편지를 읽습니다. 뒤쪽 벽은 텅 비어 있었습니다.

{c23}

1979년, 엑스선 사진에서 그 빈 벽에 커다란 그림이 숨어 있다는 것이 드러났습니다. 사랑의 신 큐피드였습니다. 사람들은 베르메르가 마음을 바꿔 스스로 지웠다고 여겼습니다.

{c24}

2017년, 독일 드레스덴 회화관이 누렇게 바랜 니스를 벗기는 복원을 시작했습니다. 그런데 복원가는 벽 부분의 물감이 다른 곳과 다르다는 것을 알아챘습니다.

{c24}

실험실 검사 결과는 놀라웠습니다. 큐피드를 덮은 물감은 베르메르가 그림을 끝내고 수십 년이 지난 뒤에 칠해진 것이었습니다. 누군가 남의 그림에 손을 댄 것입니다.

{c25}

복원팀은 메스로 덧칠을 한 겹씩 걷어 냈습니다. 2021년, 마침내 큐피드가 300여 년 만에 모습을 드러냈습니다.

{c26}

편지를 읽는 여인 뒤에 사랑의 신이 서 있습니다. 이제 이 편지는 사랑의 편지로 읽힙니다. 그림의 뜻 자체가 바뀐 것입니다. 이어서 마지막 첫 번째 비밀은, 22년 동안 바로 그 미술관 벽 속에 있었습니다.

## 5. 첫 번째 비밀, 벽 속에서 나온 클림트

{c27}

이탈리아 북부 피아첸차의 리치 오디 미술관. 이곳에는 구스타프 클림트의 '여인의 초상'이 있었습니다.

{c28}

1997년 2월 22일, 전시 준비로 어수선하던 때에 그림이 감쪽같이 사라졌습니다. 경찰은 도둑이 지붕 창으로 낚싯줄을 내려 그림을 낚아챘다고 보았습니다.

{c29}

빈 액자는 지붕 위에서 발견됐습니다. 그런데 이상했습니다. 그 지붕 창은 그림이 빠져나가기에는 너무 좁았습니다.

{c30}

수사는 22년 동안 제자리를 맴돌았습니다. 그리고 2019년 12월, 정원사가 미술관 바깥벽의 철문을 열었습니다.

{c31}

벽 속 작은 공간에서 나온 가방. 그 안에 클림트가 들어 있었습니다. 그림이 사라진 곳에서 불과 몇 걸음 떨어진 벽이었습니다.

{c32}

전문가들은 자외선과 적외선으로 그림을 살폈습니다. 1996년에 찍어 둔 사진과 비교한 끝에, 2020년 1월, 진품이라는 결론이 났습니다. 그런데 곧, 이 그림에 숨은 더 놀라운 비밀이 다시 주목받았습니다.

## 6. 그림 밑의 또 다른 여인

{c33}

그런데 사람들이 이 그림을 특별하게 여기는 이유는 또 있습니다. 도난 바로 한 해 전인 1996년, 한 젊은 미술 학도가 이 그림을 클림트의 옛 그림 사진과 나란히 놓아 보았습니다.

{c34}

1912년 이후 사라진 클림트의 '젊은 여인의 초상'. 두 그림의 얼굴 방향과 어깨가 겹쳐 보였습니다. 과학 조사 결과, 클림트는 그 옛 그림 위에 새 여인을 덧그린 것이었습니다.

{c34}

클림트의 그림 가운데 두 사람이 한 화폭에 겹친 것은 이 그림 하나뿐입니다. 사라진 그림 속에 사라진 그림이 숨어 있었던 셈입니다. 이어서, 과학이 지금 이런 비밀을 찾는 새로운 방법을 보겠습니다.

## 7. 아직 잠든 비밀

{c35}

엑스선 사진은 백 년 넘게 그림 속을 보여 주었습니다. 하지만 여러 겹의 물감이 한 장에 뭉쳐 찍힌다는 한계가 있었습니다.

{c35}

2026년, 미국 노스웨스턴 대학이 이 겹친 층을 AI로 한 장씩 떼어 보는 연구를 시작했습니다. 물리 법칙을 아는 AI가, 화가가 지운 밑그림을 층별로 되살리는 것입니다.

{c36}

어쩌면 미술관에 걸린 수많은 그림들 아래에도, 아직 아무도 본 적 없는 그림이 잠들어 있을지 모릅니다.

{c36}

여러분은 다섯 가지 비밀 가운데 무엇이 가장 놀라우셨나요? 댓글로 들려주세요. 보고 나면 가벼운 지식이 남는 이야기, 이 채널에서 계속 이어집니다."""

# 실제 사진을 보고 그리는 컷 (실제 그림·장소가 나오는 AI 장면) → 사진후보 이름들 (사진을 받은 뒤 채움)
REFS = {"c01": ["c27_4"], "c03": ["c02_1"], "c24": ["c22_8"], "c32": ["c02_1"], "c33": ["c02_1"], "c34": ["c02_1"]}
REF_NOTE = ("Any painting or building shown must look exactly like the reference photo of the real artwork or place "
            "(same composition, colors and figures), painted in the same oil style. ")

# 컷 → 고른 위키미디어 사진 후보 이름 (사진후보/후보.json 의 열쇠). 사진을 받은 뒤 채움
PHOTOS = {"c02": "c02_1", "c05": "c05_1", "c06": "c06_2", "c08": "c08_c", "c11": "c11_1", "c16": "c16_2", "c20": "c20_2",
          "c22": "c22_8", "c23": "c23_1", "c25": "c25_8", "c26": "c26_c", "c27": "c27_4", "c10": "c10_8", "c14": "c14_c"}


def main():
    cmd, folder = sys.argv[1], sys.argv[2]
    main_src = os.path.join(ROOT, "..", "shorts_novel_maker_supertonic.py")      # 작업 가지(메인 저장소)의 최신 화풍 목록이 우선
    src = open(main_src if os.path.exists(main_src) else os.path.join(ROOT, "shorts_novel_maker_supertonic.py"), encoding="utf-8").read()
    style = re.search('"' + re.escape(STYLE_NAME) + '": "([^"]+)"', src).group(1)
    only = sys.argv[3].split(",") if len(sys.argv) > 3 else None
    if cmd == "job":
        items = []
        for cid, desc, _ in CUTS:
            if (only and cid not in only) or cid in PHOTOS:
                continue
            refs = [os.path.join(HERE, "사진후보", k + ".jpg") for k in REFS.get(cid, [])]
            items.append({"id": cid, "width": 1024, "height": 576, "seed": 300 + int(cid[1:]), "refs": refs,
                          "prompt": f"{style}, historical documentary illustration, realistic proportions, museum-quality painting. "
                                    f"Scene: {desc}. {REF_NOTE if refs else ''}{'' if 'no people' in desc.lower() else 'Every person has exactly two arms, two hands with five fingers each and two legs, hands simple and relaxed (partly hidden is fine). '}"
                                    "Cinematic composition, full-bleed image, no border, no frame, no paper edges. No text, no letters, no captions."})
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
                credit = f"{m['artist'] or 'Wikimedia Commons'} / {m['license']} / Wikimedia Commons"
                story = story.replace("{" + cid + "}", f"[사진: {img} | {cap} | {credit} | {m['page']}]")
                continue
            img = next((os.path.join(folder, cid + e) for e in (".png", ".jpg") if os.path.exists(os.path.join(folder, cid + e))), os.path.join(folder, cid + ".png"))
            story = story.replace("{" + cid + "}", f"[사진: {img} | {cap} | AI 그림 (FLUX.2 klein, 수채화) | ]")
        proj = {"ver": 7, "category": "장문", "genre": "[다큐] 역사·미스터리", "topic": "명화 속 숨은 비밀", "title": TITLE,
                "story": story, "sources": ["https://www.mauritshuis.nl/"],
                "notes": "미술 미스터리 장문 다큐 (실제 명화·장소 사진 위주 + 사진이 없는 장면은 AI 그림)", "autophoto": False, "img_source": "그림: 유화",
                "settings": {"format": "롱폼 가로(1920×1080)", "narration": "on",
                             "layout": "자막형(큰 제목+사진+자막)", "img_fill": "전체 화면(글자가 사진 위에)",
                             "img_motion": "영상처럼(확대·이동·전환)",
                             "head_show": "안 보임(제목 카드만)", "sub_split": "한 줄씩(문장·쉼표로 나눠 차례로)", "img_label": "on",
                             "narr_voice": "Supertonic M2 (남성, 무료 로컬) [supertonic:M2]"}}
        out = os.path.join(HERE, "명화_숨은비밀.json")
        json.dump(proj, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(out, len(story), "chars")


if __name__ == "__main__":
    main()
