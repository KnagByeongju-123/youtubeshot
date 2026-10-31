"""캐릭터 시트 모음 그리기 — 목록.json 의 인물·동물·귀신마다 시트(세 방향 전신, 흰 배경)를 klein 으로 그려 목록 폴더에 <name>.png
python 캐릭터시트_만들기.py <목록.json> [--스타일 "역사 수묵 담채"] [--이름 까치호랑이,도깨비] [--다시]
  - kind: person·spirit = 앞·옆·뒤 / animal = 옆·앞·뒤 (네 발 동물은 옆모습이 알아보기 쉬움)
  - 항목에 "refs": ["등장인물/조선/_기준/문관.png"] 를 넣으면 그 그림의 옷차림(관모·옷·흉배·띠·신)을 그대로, "color" 로 옷 색만 바꿈
  - 이미 있는 그림은 건너뜀 (--다시 면 새로). 한 장 약 2분 (AMX 서버)
  - 확인한 시트는 등장인물/등장인물.json 에 {name, look, look_ko, face} 로 등록하면 모든 편에서 같은 모습"""
import json
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
os.chdir(HERE)
import shorts_novel_maker_supertonic as m

a = sys.argv[1:]
lst = os.path.abspath(a[0])
style_name = a[a.index("--스타일") + 1] if "--스타일" in a else "역사 수묵 담채"
only = set(a[a.index("--이름") + 1].split(",")) if "--이름" in a else None
style = m.IMAGE_STYLES.get(style_name, style_name)
out_dir = os.path.dirname(lst)
VIEWS = {"animal": "side view, front view, back view, full body, standing on all its legs",
         "person": "front view, side view, back view, full body, standing",
         "spirit": "front view, side view, back view, full body, standing"}
# 그림 모델은 한국 옷 이름을 몰라 중국·일본 옷으로 그림 → 이름이 나오면 모양을 풀어 쓴 설명을 붙임 (2026-10-31 첫 시트에서 사모가 고깔, 단령이 여밈 옷으로 나옴)
KO_COSTUME = {
    "ikseongwan": "the king's ikseongwan cap = a black two-tiered cap (low front part, higher back part, no brim) with two cicada-wing shaped wings at the back standing UPRIGHT toward the sky",
    "samo": "samo = a black two-tiered gauze official cap (low front part, higher back part, no brim) with two thin flat oval wings attached at the back that stick straight out to the LEFT and RIGHT like ears, clearly visible in the front view and the back view",
    "gonryongpo": "gonryongpo = the king's deep crimson robe with a ROUND neckline, round gold badges of a five-clawed dragon on the chest, the back and both shoulders, a stiff jade belt hanging loosely around the waist, black boots",
    "dallyeong": "dallyeong = an official robe with a ROUND neckline (not a crossed collar), wide sleeves, a square embroidered rank badge (hyungbae) on the chest and back showing cranes for civil officials or a tiger for military officials, never letters, a stiff belt hanging loosely",
    "gat": "gat = a black wide flat-brimmed hat with a tall cylindrical crown, made of see-through horsehair, tied under the chin with strings",
    "dopo": "dopo = a long white overcoat with wide sleeves and a split back, tied at the chest with a thin sash",
    "jeogori": "jeogori = Korean jacket closed by a long ribbon bow (goreum) tied on the right chest, with gently curved sleeves",
    "dangui": "dangui = a Korean court lady's jacket reaching the thighs with curved side hems and gold patterns, closed by a ribbon bow on the chest",
    "wonsam": "wonsam = Korean ceremonial open robe for court ladies with very wide sleeves striped in many colors and white cuffs (red for the queen, purple or green for royal concubines)",
    "jeogui": "jeogui = the queen's deep red ceremonial robe covered in rows of small pheasant roundels, with round dragon badges",
    "eoyeomeori": "eoyeomeori = a huge wide braided wig worn on top of the head like a round black cushion, decorated with hairpins",
    "myeonryugwan": "myeonryugwan = a black crown with a flat rectangular board on top, strings of beads hanging in front of the face",
    "okdae": "okdae = the king's jade belt: a stiff red frame with white carved jade plaques, hanging loosely around the waist",
    "heukhwa": "heukhwa = black ankle-high boots with a thick white sole and a slightly upturned rounded toe",
    "jeollip": "jeollip = a black wide-brimmed felt hat with a red tassel and feathers on top, worn by soldiers",
    "cheopji": "cheopji = a small ornament (dragon or phoenix for the queen, frog for lower court ranks) placed at the hair parting on the forehead",
    "skirt": "the skirt (chima) is very full and tied high at the chest, falling to the floor",
    "straw sandals": "jipsin = woven straw shoes covering the toes and heels (not flip-flops)",
    "manggeon": "manggeon = a thin black horsehair headband around the forehead with the hair tied in a topknot on top",
    "paeraengi": "paeraengi = a small round woven bamboo hat",
    "jeongjagwan": "jeongjagwan = a tall black stepped horsehair cap shaped like the Chinese character for well (jeong)",
    "beongeoji": "beongeoji = a black felt hat with a wide round brim and a red tassel on top",
}
KO_REFS = {"samo": "등장인물/조선/_관모/samo.png", "ikseongwan": "등장인물/조선/_관모/ikseongwan.png"}   # 말로는 모양을 못 따라 해서(사모가 야구모자·갓처럼) 모양 기준 그림을 함께 넣음
OUTFIT_STYLE = ("traditional East Asian ink wash painting with light color washes: expressive black ink brush outlines, "
                "rich clear colors applied as transparent watercolor washes, rice paper texture")   # 조선 기본 시트 12명과 같은 그림체
KO_HEAD = "Korean Joseon dynasty costume (hanbok) - NOT Chinese hanfu, NOT Japanese kimono. "


def explain(look):
    lo = look.lower()
    add = [v for k, v in KO_COSTUME.items() if re.search(r"\b" + re.escape(k) + r"\b", lo)]
    return (KO_HEAD if ("joseon" in lo or "korean" in lo) and add else "") + look + (" Details: " + "; ".join(add) + "." if add else "")


jobs = []
for c in json.load(open(lst, encoding="utf-8"))["chars"]:
    dst = os.path.join(out_dir, m.safe_name(c["name"])[:40] + ".png")
    if (only and c["name"] not in only) or (os.path.exists(dst) and "--다시" not in a):
        continue
    kind = c.get("kind", "person")
    outfit = [os.path.join(HERE, r_) for r_ in (c.get("refs") or []) if os.path.exists(os.path.join(HERE, r_))]   # 옷차림 기준 그림 (등장인물/조선/_기준/왕·왕비·문관·상궁·내관·무관)
    style_ = OUTFIT_STYLE if outfit else style    # 옷차림 기준이 있으면 기본 시트와 같은 선명한 색 (채널 기본 문구의 '차분한 색'은 옷 색을 회색으로 빼 버림)
    woman = re.search(r"\b(woman|queen|lady|girl|gisaeng|maid|female)\b", c["look"].lower())
    refs = outfit or [os.path.join(HERE, v) for k, v in KO_REFS.items() if re.search(r"\b" + k + r"\b", c["look"].lower())]
    jobs.append({"id": f"s{len(jobs)}", "name": c["name"], "dst": dst, "look": c["look"], "refs": refs, "width": 1024, "height": 576, "seed": int(c.get("seed", 7)),
                 "prompt": f"Character design sheet, {style_}. The same {'animal' if kind == 'animal' else 'character'} shown three times side by side "
                           f"on a plain white background: {VIEWS.get(kind, VIEWS['person'])}. {'Animal' if kind == 'animal' else 'Character'}: {explain(c['look'])}. "
                           + ("Exactly four legs and one tail. " if kind == "animal" and "nine" not in c["look"] and "fish" not in c["look"] and "bird" not in c["look"] and "crane" not in c["look"] and "rooster" not in c["look"] and "dragon" not in c["look"] else "")
                           + ("Exactly two arms and two legs. " if kind != "animal" else "")
                           + ("Dress the character in exactly the same costume as the person in the reference image: the same hat shape, robe cut, collar, badges, belt, shoes and colors"
                              + (f" (robe color: {c['color']})" if c.get("color") else "") + ", keep the colors as clear and strong as in the reference. Face, age, gender and body follow the description, not the reference. "
                              + ("She is a woman: no beard, no mustache, no facial hair, no hat. " if woman else "") if outfit else
                              "The black cap must have exactly the shape shown in the reference image (front, side, back), drawn in the same ink wash style. " if refs else "")
                           + "Consistent design in every view, no close-ups, no other people or animals, no text, no red seal stamp"})
print(f"그릴 시트 {len(jobs)}장: " + ", ".join(j["name"] for j in jobs), flush=True)
if jobs:
    if any(j.get("refs") for j in jobs):      # 옷차림 기준 그림은 크게 넣어야 흉배·무늬가 살아남 (klein 기본 115000 → 300000)
        os.environ["KLEIN_REF_MAX_AREA"] = "300000"
    got = m.sd_generate(jobs, os.path.join(out_dir, "_sd"), print, None)
    for j in jobs:
        if got.get(j["id"]):
            shutil.move(got[j["id"]], j["dst"])
            print("저장:", j["dst"], flush=True)
    shutil.rmtree(os.path.join(out_dir, "_sd"), ignore_errors=True)
