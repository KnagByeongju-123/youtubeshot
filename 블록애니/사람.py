"""블록 사람 만들기 — 어른 비율(머리가 작고 다리가 긺, 키 약 27칸)

부위: hips(엉덩이, 뿌리) → leg_l, leg_r, torso → head, arm_l, arm_r
돌리는 중심: 다리 = 엉덩이 관절, 팔 = 어깨, 머리 = 목, 몸통 = 허리
캐릭터 오른쪽 = +x (앞에서 보면 화면 왼쪽)
"""
from 블록 import Model

# 어른 키: 신발 z0~1, 다리 z0~10, 몸통 z11~19, 머리 z20~25, 머리카락 z26  (블록 한 칸 0.062m → 약 1.7m)
LEG_TOP, TORSO_TOP, HEAD_TOP = 10, 19, 25


def person(name, pal, hair="short", glasses=False, vest=False, sleeve_full=True, collar=None, scale=0.062,
           apron=False, cardigan=False, shorts=False, skirt=False, brows=None):
    """pal 에 꼭 있어야 할 색: skin, hair, top, pants, shoes, eye, mouth (+ vest, glass, apron, inner, sock, brow)"""
    global LEG_TOP, TORSO_TOP, HEAD_TOP
    LEG_TOP, TORSO_TOP, HEAD_TOP = 10, 19, 25
    m = Model(name, pal, scale)
    hips = m.part("hips", (0, 0, LEG_TOP + 0.5))
    # 다리 (각 3칸 너비, 가운데 x=0 은 비움)
    for side, nm in ((-1, "leg_l"), (1, "leg_r")):
        x0, x1 = (1, 3) if side > 0 else (-3, -1)
        lg = m.part(nm, (side * 2, 0, LEG_TOP + 0.5), "hips")
        lg.box(x0, x1, -1, 1, 2, LEG_TOP, "pants")
        if shorts:
            lg.box(x0, x1, -1, 1, 2, LEG_TOP - 4, "skin")
        lg.box(x0, x1, -2, 1, 0, 1, "shoes")          # 신발은 앞으로 한 칸 더
        lg.box(x0, x1, -2, -2, 1, 1, "shoes")
        if apron:                                       # 작업 앞치마 아랫단(다리 앞을 덮어 걸을 때 같이 움직임)
            lg.box(x0 - (1 if side > 0 else 0), x1 + (1 if side < 0 else 0), -2, -2, LEG_TOP - 4, LEG_TOP, "apron")
    tor = m.part("torso", (0, 0, LEG_TOP + 0.5), "hips")
    tor.box(-3, 3, -1, 1, LEG_TOP + 1, TORSO_TOP, "top")
    tor.box(-3, 3, -1, 1, LEG_TOP + 1, LEG_TOP + 1, "pants" if not vest else "top")   # 허리띠 자리
    if "belt" in pal:
        tor.box(-3, 3, -1, 1, LEG_TOP + 1, LEG_TOP + 1, "belt")
    if vest:        # 구명조끼: 몸통 앞뒤를 한 겹 덮음(어깨 끈 포함)
        tor.box(-3, 3, -2, -2, LEG_TOP + 2, TORSO_TOP - 1, "vest")
        tor.box(-3, 3, 2, 2, LEG_TOP + 2, TORSO_TOP - 1, "vest")
        tor.box(-3, -2, -2, 2, TORSO_TOP, TORSO_TOP, "vest")
        tor.box(2, 3, -2, 2, TORSO_TOP, TORSO_TOP, "vest")
        tor.box(-1, 1, -2, -2, TORSO_TOP - 1, TORSO_TOP - 1, "top")     # 목 아래 트임
        tor.set(0, -2, LEG_TOP + 6, "glass")                             # 가운데 버클
        tor.set(0, -2, LEG_TOP + 4, "glass")
    if collar:
        tor.box(-1, 1, -1, 1, TORSO_TOP, TORSO_TOP, collar)
    if apron:                                           # 가슴까지 오는 앞치마 + 목끈 + 주머니
        tor.box(-2, 2, -2, -2, LEG_TOP + 1, TORSO_TOP - 2, "apron")
        tor.box(-3, 3, -2, -2, LEG_TOP + 1, LEG_TOP + 3, "apron")
        tor.set(-2, -2, TORSO_TOP - 1, "apron")
        tor.set(2, -2, TORSO_TOP - 1, "apron")
        tor.box(-1, 1, -3, -3, LEG_TOP + 4, LEG_TOP + 5, "apron2")       # 가슴 주머니(공구)
        tor.set(1, -3, LEG_TOP + 6, "glass")                             # 주머니에 꽂힌 드라이버
        tor.box(-3, 3, 2, 2, LEG_TOP + 3, LEG_TOP + 3, "apron2")         # 허리끈(뒤)
    if cardigan:                                        # 앞이 트인 카디건: 가운데 한 줄은 안쪽 블라우스 색
        tor.box(0, 0, -1, -1, LEG_TOP + 1, TORSO_TOP, "inner")
        tor.box(-1, 1, -1, -1, TORSO_TOP - 1, TORSO_TOP, "inner")
        tor.set(-1, -2, LEG_TOP + 4, "glass")
        tor.set(-1, -2, LEG_TOP + 6, "glass")
    # 팔 (2칸 너비, 어깨 z19 → 손 z10~11)
    for side, nm in ((-1, "arm_l"), (1, "arm_r")):
        xs = (4, 5) if side > 0 else (-5, -4)
        ar = m.part(nm, (side * 4.5, 0, TORSO_TOP), "torso")
        ar.box(xs[0], xs[1], -1, 0, 12 if sleeve_full else 16, TORSO_TOP, "top" if not vest else "sleeve")
        if not sleeve_full:
            ar.box(xs[0], xs[1], -1, 0, 12, 15, "skin")
        ar.box(xs[0], xs[1], -1, 0, 10, 11, "skin")
    # 머리 (5칸 너비·5칸 깊이·6칸 높이)
    hd = m.part("head", (0, 0, TORSO_TOP + 0.5), "torso")
    hd.box(-2, 2, -2, 2, TORSO_TOP + 1, HEAD_TOP, "skin")
    z_eye = HEAD_TOP - 2
    hd.set(-1, -2, z_eye, "eye")
    hd.set(1, -2, z_eye, "eye")
    hd.set(0, -3, z_eye - 1, "skin")                  # 코
    hd.set(0, -2, TORSO_TOP + 2, "mouth")
    if brows:                                           # 눈썹 (나이 든 사람은 흰 눈썹)
        hd.set(-1, -2, z_eye + 1, brows)
        hd.set(1, -2, z_eye + 1, brows)
    if glasses:
        for x in (-2, 0, 2):              # 얇은 안경테: 눈 양옆과 가운데만 (눈은 그대로 보임)
            hd.set(x, -3, z_eye, "glass")
    _hair(hd, hair)
    return m


def _hair(hd, style, top=None):
    top = HEAD_TOP if top is None else top
    if style == "bob":            # 턱까지 오는 짧은 단발 (서진)
        hd.box(-2, 2, -2, 2, top, top, "hair")
        hd.box(-3, 3, -2, 3, top + 1, top + 1, "hair")
        hd.box(-3, 3, -1, 3, top - 4, top, "hair")
        hd.box(-3, -3, -1, 3, top - 4, top, "hair")      # 옆머리는 얼굴 앞 한 줄을 비워 옆얼굴이 보이게
        hd.box(3, 3, -1, 3, top - 4, top, "hair")
        hd.box(-3, -3, -2, -2, top - 1, top, "hair")
        hd.box(3, 3, -2, -2, top - 1, top, "hair")
        hd.box(-2, 2, 3, 3, top - 4, top, "hair")
        hd.box(-2, 2, -3, -3, top, top, "hair")          # 앞머리
        hd.set(-2, -3, top - 1, "hair")
    elif style == "pony":         # 뒤로 묶은 긴 머리 (하린)
        hd.box(-2, 2, -2, 2, top, top, "hair")
        hd.box(-3, 3, -2, 3, top + 1, top + 1, "hair")
        hd.box(-3, -3, -2, 3, top - 3, top, "hair")
        hd.box(3, 3, -2, 3, top - 3, top, "hair")
        hd.box(-2, 2, 3, 3, top - 4, top, "hair")
        hd.box(-2, 2, -3, -3, top, top, "hair")
        hd.box(-1, 1, 4, 4, top - 1, top, "tie")         # 머리끈
        hd.box(-1, 1, 4, 5, top - 9, top - 2, "hair")    # 꽁지머리(등 쪽으로 내려옴)
        hd.box(0, 0, 5, 5, top - 11, top - 10, "hair")
    elif style == "medium":       # 어깨에 닿는 단발 (은비)
        hd.box(-2, 2, -2, 2, top, top, "hair")
        hd.box(-3, 3, -2, 3, top + 1, top + 1, "hair")
        hd.box(-3, -3, -1, 3, top - 6, top, "hair")
        hd.box(3, 3, -1, 3, top - 6, top, "hair")
        hd.box(-3, -3, -2, -2, top - 1, top, "hair")
        hd.box(3, 3, -2, -2, top - 1, top, "hair")
        hd.box(-2, 2, 3, 3, top - 6, top, "hair")
        hd.box(-2, 0, -3, -3, top, top, "hair")          # 옆으로 넘긴 앞머리
        hd.set(-2, -3, top - 1, "hair")
    elif style == "gray_short":   # 짧은 흰머리, 정수리가 조금 비침 (아버지)
        hd.box(-2, 2, -2, 2, top, top, "hair")
        hd.box(-1, 1, -1, 1, top + 1, top + 1, "skin")
        hd.box(-3, 3, 2, 3, top + 1, top + 1, "hair")
        hd.box(-3, -3, -2, 3, top + 1, top + 1, "hair")
        hd.box(3, 3, -2, 3, top + 1, top + 1, "hair")
        hd.box(-3, -3, -1, 3, top - 3, top, "hair")
        hd.box(3, 3, -1, 3, top - 3, top, "hair")
        hd.box(-2, 2, 3, 3, top - 3, top, "hair")
        hd.box(-2, 2, -3, -3, top + 1, top + 1, "hair")
    elif style == "pigtails":     # 양 갈래 머리 (어린 은비)
        hd.box(-2, 2, -2, 2, top, top, "hair")
        hd.box(-3, 3, -2, 3, top + 1, top + 1, "hair")
        hd.box(-3, -3, -1, 3, top - 2, top, "hair")
        hd.box(3, 3, -1, 3, top - 2, top, "hair")
        hd.box(-2, 2, 3, 3, top - 3, top, "hair")
        hd.box(-2, 2, -3, -3, top, top, "hair")
        for sx in (-1, 1):
            hd.set(sx * 4, 2, top - 1, "tie")
            hd.box(sx * 4, sx * 5, 2, 3, top - 4, top - 2, "hair")
            hd.set(sx * 5, 3, top - 5, "hair")
    else:                          # 짧은 머리 (정우)
        hd.box(-2, 2, -2, 2, top, top, "hair")
        hd.box(-3, 3, -2, 3, top + 1, top + 1, "hair")
        hd.box(-3, -3, -1, 3, top - 2, top, "hair")
        hd.box(3, 3, -1, 3, top - 2, top, "hair")
        hd.box(-2, 2, 3, 3, top - 3, top, "hair")
        hd.box(-2, 2, -3, -3, top + 1, top + 1, "hair")


SKIN = "#e8b894"
SKIN_OLD = "#dcae8c"


def 서진(young=False):
    pal = {"skin": SKIN if young else SKIN_OLD, "hair": "#262222" if young else "#b9b6b2", "top": "#2f4a5c",
           "sleeve": "#2f4a5c", "vest": "#e8742c", "pants": "#a8957a", "shoes": "#4a3326", "eye": "#1b1b1b",
           "mouth": "#a87462", "glass": "#7a6a58"}
    return person("서진_젊은" if young else "서진", pal, hair="bob", glasses=not young, vest=True)


def 하린():
    pal = {"skin": SKIN, "hair": "#1e1a1a", "top": "#efe4cf", "pants": "#3e5f8a", "shoes": "#f2f2f2",
           "eye": "#1b1b1b", "mouth": "#c27a6c", "tie": "#b0453d", "belt": "#3e5f8a"}
    return person("하린", pal, hair="pony")


def 정우():
    pal = {"skin": "#d9a47e", "hair": "#1e1a1a", "top": "#f0c53a", "pants": "#3b3f45", "shoes": "#1f1f22",
           "eye": "#1b1b1b", "mouth": "#a86a5a", "belt": "#3b3f45", "collar": "#d9ad25"}
    return person("정우", pal, hair="short", collar="collar")


# ---------------------------------------------------------------- 아이 (키 약 18칸 ≈ 1.1~1.2m, 머리가 조금 큼)
def kid(name, pal, hair="short", shorts=False, dress=False, scale=0.062):
    """부위 이름은 어른과 같음(걷기 움직임을 같이 씀). 다리 z0~5, 몸통 z6~11, 머리 z12~16"""
    lt, tt, ht = 5, 11, 16
    m = Model(name, pal, scale)
    m.part("hips", (0, 0, lt + 0.5))
    for side, nm in ((-1, "leg_l"), (1, "leg_r")):
        x0, x1 = (1, 2) if side > 0 else (-2, -1)
        lg = m.part(nm, (side * 1.5, 0, lt + 0.5), "hips")
        lg.box(x0, x1, -1, 0, 1, lt, "pants")
        if shorts or dress:
            lg.box(x0, x1, -1, 0, 1, lt - 2, "skin")
        if "sock" in pal:
            lg.box(x0, x1, -1, 0, 1, 1, "sock")
        lg.box(x0, x1, -2, 0, 0, 0, "shoes")
    tor = m.part("torso", (0, 0, lt + 0.5), "hips")
    tor.box(-2, 2, -1, 0, lt + 1, tt, "top")
    if dress:                                            # 원피스 치마: 몸통 아래로 퍼짐
        tor.box(-3, 3, -2, 1, lt, lt + 1, "top")
        tor.box(-3, 3, -2, 1, lt, lt, "top2")
        tor.box(-2, 2, -2, -2, tt - 1, tt - 1, "top2")   # 가슴의 흰 깃
    for side, nm in ((-1, "arm_l"), (1, "arm_r")):
        xs = (3, 3) if side > 0 else (-3, -3)
        ar = m.part(nm, (side * 3, -0.5, tt), "torso")
        ar.box(xs[0], xs[1], -1, 0, tt - 2 if shorts or dress else lt + 2, tt, "top")
        ar.box(xs[0], xs[1], -1, 0, lt + 1, (tt - 3) if shorts or dress else lt + 1, "skin")
    hd = m.part("head", (0, 0, tt + 0.5), "torso")
    hd.box(-2, 2, -2, 2, tt + 1, ht, "skin")
    hd.set(-1, -2, ht - 2, "eye")
    hd.set(1, -2, ht - 2, "eye")
    hd.set(0, -2, tt + 2, "mouth")
    if "cheek" in pal:
        hd.set(-2, -2, tt + 2, "cheek")
        hd.set(2, -2, tt + 2, "cheek")
    _hair(hd, hair, top=ht)
    return m
