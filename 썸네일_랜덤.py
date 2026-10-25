"""썸네일 글씨 얹기 — 규칙이 없는 영상용 무작위 디자인 (매번 글꼴·색·위치·효과가 달라 틀에 찍은 AI 썸네일처럼 보이지 않게)

  python 썸네일_랜덤.py <그림> <결과폴더> "<큰 문구>" [--작게 "<작은 글>"] [--개수 4] [--seed 숫자]

- 큰 문구: 줄바꿈은 \\n, 강조할 낱말은 [대괄호]  예) "2천 년 전\\n바닷속 [컴퓨터]"
- 글꼴(이 컴퓨터에 있는 굵은 한글 글꼴 중), 색 조합, 글씨 위치(위/아래 · 왼쪽/가운데/오른쪽), 크기, 글씨 효과,
  어둡게 깔기, 테두리 여부, 사진 밝기·채도를 무작위로 골라 후보를 만듦 → 결과폴더/랜덤_1.jpg … + 랜덤_기록.json(고른 값)
- 규칙(CLAUDE.md): 그 연재·주제에 정해진 썸네일 규칙(예: 연재/<연재>/썸네일_만들기.py, 기획.md 의 썸네일 항목)이 있으면 그것을 따르고,
  없을 때만 이 도구를 씀. 디자인 엔진은 썸네일_엔진.py (MIT)"""
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

FONTS = [    # 굵은 한글 글꼴 후보 (있는 것만 씀)
    os.path.join(HERE, "fonts", "BlackHanSans-Regular.ttf"),
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/opentype/noto/NotoSerifCJK-Black.ttc",
    "/usr/share/fonts/truetype/nanum/NanumGothicExtraBold.ttf",
    "/usr/share/fonts/truetype/nanum/NanumSquareEB.ttf",
    "/usr/share/fonts/truetype/nanum/NanumBarunGothicBold.ttf",
    "/usr/share/fonts/truetype/nanum/NanumMyeongjoExtraBold.ttf",
    "C:/Windows/Fonts/malgunbd.ttf",
]


def pick(rng, E):
    top = rng.random() < 0.35
    return {
        "font": rng.choice([f for f in FONTS if os.path.exists(f)] or [""]),
        "theme": rng.choice(list(E.THEMES)),
        "title_style": rng.choice(["외곽선", "그림자", "그림자", "박스 강조", "네온 글로우", "외곽선"]),
        "overlay": ("우측 그라데이션" if rng.random() < .2 else "좌측 그라데이션" if rng.random() < .3 else
                    rng.choice(["하단 그라데이션", "비네팅", "전체 어둡게"])) if not top else rng.choice(["비네팅", "전체 어둡게"]),
        "darkness": rng.randint(40, 80),
        "align": rng.choice(["left", "left", "center", "right"]),
        "text_y": rng.randint(16, 30) if top else rng.randint(64, 82),
        "font_size": rng.randint(74, 106),
        "frame": rng.choice(["없음", "없음", "없음", "테두리", "코너 장식"]),
        "tag_position": rng.choice(E.TAG_POSITIONS),
        "bg_saturation": rng.randint(85, 125),
        "brightness": rng.randint(82, 105),
    }


def main():
    a = sys.argv[1:]
    if len(a) < 3:
        sys.exit(__doc__)
    src, out_dir, title = a[0], a[1], a[2].replace("\\n", "\n")
    small = a[a.index("--작게") + 1] if "--작게" in a else ""
    n = int(a[a.index("--개수") + 1]) if "--개수" in a else 4
    seed = int(a[a.index("--seed") + 1]) if "--seed" in a else random.SystemRandom().randint(1, 10 ** 9)
    import 썸네일_엔진 as E
    rng = random.Random(seed)
    bg = E.load_image(src)
    os.makedirs(out_dir, exist_ok=True)
    log = []
    for k in range(n):
        c = pick(rng, E)
        os.environ["DREAMART_FONT"] = c["font"]
        E._FONT_CACHE.clear()
        opts = E.RenderOptions(size=(1280, 720), title=title, subtitle=small, layers=[],
                               **{kk: vv for kk, vv in c.items() if kk != "font"})
        im, _ = E.render_with_bounds(opts, bg)
        path = os.path.join(out_dir, f"랜덤_{k + 1}.jpg")
        E.save_thumbnail(im, path)
        log.append({"file": os.path.basename(path), **c})
        print(f"{path}  글꼴 {os.path.basename(c['font'])} · {c['theme']} · {c['title_style']} · {'위' if c['text_y'] < 50 else '아래'}-{c['align']}")
    json.dump({"seed": seed, "src": src, "title": title, "candidates": log},
              open(os.path.join(out_dir, "랜덤_기록.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
