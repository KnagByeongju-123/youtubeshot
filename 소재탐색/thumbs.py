"""
썸네일 문구 · 썸네일 이미지 · 해시태그 생성 (무료, 로컬)

- 문구: 해결 상태에 맞는 한국어 썸네일 문구 3안 (원문에 없는 숫자·기간·확정 결론을 만들지 않음)
- 이미지: 실사가 있으면 layouts.py 의 실사 편집 레이아웃 3안 (A 피사체 중심형 / C 증거 확대형 / B 좌우 비교형 또는 A').
  실사 출처: 사용자 사진(--bg, --bg-dir; 폴더 안 'NN_이름' 하위폴더는 N번 소재 전용) > --bg-commons 를 켰을 때만 위키미디어 공용.
  실사가 없으면 외부에서 가져오지 않고 기본 그래픽을 '임시' 로 표시.
- 메타데이터: 소재별 meta.json 에 사용 사진·출처·라이선스·편집 내역(크롭/확대 좌표)·레이아웃·사실 구분 메모를 기록.
- 해시태그: 용어 사전(glossary_ko.json)으로 옮긴 소재어 + 분야 태그 + 채널 공통 태그 5~8개.
- 저장: output/assets_날짜/NN_slug/ 에 thumb_A.jpg, thumb_B.jpg, thumb_C.jpg, copy.txt, hashtags.txt, source.txt
  (같은 폴더가 있으면 _2, _3 … 을 붙여 덮어쓰지 않음)

유튜브 썸네일 규격 (유튜브 고객센터 기준, 2026-10 확인): 1280×720 권장, 너비 640 이상, 16:9, 2MB 이하, JPG/GIF/PNG.
업로드 전에 현재 규격을 한 번 더 확인하세요.

선택 기능: pip install yake 가 되어 있으면 영어 키워드 후보를 추가로 뽑아 용어 사전으로 옮깁니다 (설치하지 않아도 동작).
"""

import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
GLOSSARY_FILE = os.path.join(HERE, "glossary_ko.json")
SIZE = (1280, 720)
FONT_CANDIDATES = [  # 한국어 굵은 글꼴 우선
    r"C:\Windows\Fonts\malgunbd.ttf", r"C:\Windows\Fonts\malgun.ttf", r"C:\Windows\Fonts\NotoSansKR-VF.ttf",
    r"C:\Windows\Fonts\NanumGothicBold.ttf", r"C:\Windows\Fonts\gulim.ttc",
    "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf", "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/System/Library/Fonts/AppleSDGothicNeo.ttc",
]
FIELD_TAGS = {
    "고고학/인류": ["고고학", "역사미스터리"], "우주/천문": ["우주", "천문학"], "생명/진화": ["진화", "고생물학"],
    "뇌/인체": ["뇌과학", "인체"], "지구/바다": ["지구과학", "자연"], "물리/화학/수학": ["물리학", "과학"],
    "기타 과학": ["과학"],
}
FIELD_COLORS = {  # 기본 그래픽 배경 (위, 아래)
    "고고학/인류": ((92, 58, 24), (20, 14, 8)), "우주/천문": ((18, 28, 80), (4, 6, 20)),
    "생명/진화": ((20, 72, 48), (6, 20, 14)), "뇌/인체": ((88, 28, 60), (24, 8, 18)),
    "지구/바다": ((16, 60, 92), (4, 16, 28)), "물리/화학/수학": ((60, 40, 96), (14, 10, 26)),
}
BASE_TAGS = ["과학다큐", "미스터리", "과학"]
STATUS_BADGE = {"해결 근거": ("해결된 미스터리", (46, 160, 90)), "가설 제안": ("새로운 가설", (222, 150, 30)),
                "미해결": ("미해결 미스터리", (120, 120, 130)), "확인 필요": ("확인 필요", (120, 120, 130))}
# 확정 표현 (미해결/가설 문구에 들어가면 안 됨) - 테스트에서도 사용
DEFINITIVE = re.compile(r"풀렸다|밝혀졌다|밝혔다|답이 나왔다|정체가 드러났다|해결됐다|해결되었다|확인됐다")


# ------------------------------------------------------------------ 용어 사전 · 한국어 소재어

def load_glossary(path=GLOSSARY_FILE):
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}
    return {k.lower(): v for k, v in data.items() if not k.startswith("_") and isinstance(v, str)}


def glossary_lookup(term, glossary):
    t = term.lower()
    if t in glossary:
        return glossary[t]
    # 어간 매칭은 '단어가 사전 키로 시작할 때'만 (archaeologists→archaeolog). 반대 방향(earth→earthquake)은 오역이라 허용 안 함
    for k, v in sorted(glossary.items(), key=lambda kv: -len(kv[0])):
        if len(k) >= 4 and t.startswith(k) and len(t) - len(k) <= 4:
            return v
    return ""


def optional_yake_terms(text, n=5):
    """YAKE 가 설치되어 있을 때만 영어 키워드 후보 추가 (없으면 빈 목록)."""
    try:
        import yake  # noqa: F401
    except ImportError:
        return []
    try:
        kw = yake.KeywordExtractor(lan="en", n=1, top=n)
        return [k for k, _ in kw.extract_keywords(text)]
    except Exception:
        return []


# 대문자로 시작해도 고유명사가 아닌 흔한 영어 단어 (단어 하나만 기계번역하면 엉뚱해짐: Peak District→성수기)
MT_SKIP = set("""peak district valley river lake mountain island bay cave university college institute
museum society journal national state county city town park sea ocean north south east west new old
great little upper lower central age era period empire kingdom dynasty""".split())


def ko_terms(item, glossary, translate=None, max_terms=6):
    """소재어(한국어) 목록. 1) 용어 사전 2) 고유명사는 무료 번역(translate 함수, 선택) 3) 없으면 건너뜀.
    translate(text) -> (한국어, 상태) 형식. 반환: ([(용어, 출처)], 메모)  출처: 사전-식별어/사전-핵심어/기계번역/yake"""
    ids = [t for t in (item.get("yt_ids") or "").split(", ") if t]
    content = [t for t in (item.get("yt_query") or "").split() if t not in ids]
    extra = optional_yake_terms(item.get("title", "") + " " + item.get("summary", "")[:300])
    terms, notes, seen = [], [], set()

    def add(ko, src):
        if ko and ko not in seen:
            seen.add(ko)
            terms.append((ko, src))

    # 두 단어 이상인 사전 키("two faces", "black death", "dead sea scrolls")는 제목·요약 앞부분에서 먼저 찾음
    text = (item.get("title", "") + " " + item.get("summary", "")[:300]).lower()
    for k, v in sorted(glossary.items(), key=lambda kv: -len(kv[0])):
        if " " in k and k in text:
            add(v, "사전-핵심어")          # 핵심어 맨 앞에 놓임 (소재명에서 고유명사 다음으로 우선)
    for w in ids:
        add(glossary_lookup(w, glossary), "사전-식별어")
    for w in content:
        add(glossary_lookup(w, glossary), "사전-핵심어")
    for w in ids[:2]:  # 사전에 없는 고유명사만 기계번역 (최대 2개)
        if glossary_lookup(w, glossary) or w in MT_SKIP or not translate:
            continue
        ko, _ = translate(w.capitalize())
        if ko and re.search(r"[가-힣]", ko) and len(ko) <= 8 and not re.search(r"\s", ko.strip()):
            notes.append(f"{w}→{ko}(기계번역)")
            add(ko, "기계번역")
    for w in extra:
        add(glossary_lookup(w, glossary), "yake")
    return terms[:max_terms], notes


def short_name(item, terms):
    """썸네일/해시태그용 짧은 소재명 (3어 이내): 식별어(지명·고유명사) 1개 + 사전 핵심어 2개.
    사전 용어가 없으면 기계번역 고유명사 → 그것도 없으면 기계번역 제목 앞부분."""
    ids = [t for t, s in terms if s == "사전-식별어"]
    core = [t for t, s in terms if s in ("사전-핵심어", "yake")]
    mt = [t for t, s in terms if s == "기계번역"]
    picked, words = [], set()

    def take(t):
        ws = t.split()
        if any(w in words for w in ws) or len(words) + len(ws) > 3:   # 단어 겹침 금지 · 3단어 이내
            return
        picked.append(t)
        words.update(ws)

    for t in ids[:1]:
        take(t)
    for t in core:
        take(t)
    if len(words) < 2:
        for t in mt + ids[1:]:
            take(t)
    if picked:
        return " ".join(picked)
    ko = (item.get("title_ko") or "").strip()
    ko = re.split(r"[,.?!:·—-]", ko)[0]
    return ko[:14] if ko else item.get("title", "")[:20]


# ------------------------------------------------------------------ 썸네일 문구 (상태별)

def grounded_span(text):
    """원문에 있는 기간 표현만 사용 (없으면 빈 문자열)."""
    t = (text or "").lower()
    m = re.search(r"(\d[\d,]*)[- ]year[- ]old", t)
    if m:
        return f"{m.group(1)}년 전"
    m = re.search(r"for (?:nearly |almost |over |more than )?(\d[\d,]*) years", t)
    if m:
        return f"{m.group(1)}년간"
    m = re.search(r"(\d+)(?:st|nd|rd|th)[- ]century", t)
    if m:
        return f"{m.group(1)}세기"
    if re.search(r"\bcentur(?:y|ies)-old\b|\bcenturies\b", t):
        return "수백 년간"
    if re.search(r"\bdecades(?:-old)?\b", t):
        return "수십 년간"
    return ""


def thumb_copies(item, name):
    """썸네일 문구 3안 (각 2줄, '\\n' 구분). 해결 상태에 맞는 표현만 사용."""
    st = item.get("status", "확인 필요")
    span = grounded_span(item.get("title", "") + " " + item.get("summary", ""))
    pre = f"{span} " if span else ""
    if st == "해결 근거":
        c = [f"{name}\n마침내 풀렸다", f"{pre}풀리지 않던\n{name}의 답", f"{name}\n과학이 밝힌 정체"]
    elif st == "가설 제안":
        c = [f"{name}\n드디어 풀렸을까?", f"{name}\n유력한 답이 나왔을까?", f"{name}\n새로 찾은 단서"]
    elif st == "미해결":
        c = [f"{name}\n아직 아무도 모른다", f"{pre}풀리지 않은\n{name}의 수수께끼", f"{name}\n남은 질문들"]
    else:
        c = [f"{name}\n뜻밖의 단서", f"{name}\n무엇이 밝혀졌나?", f"{name}\n이상한 발견"]
    return c


# ------------------------------------------------------------------ 해시태그

def clean_tag(s):
    s = re.sub(r"[\s\-·/.,()'\"’“”]", "", s)
    s = re.sub(r"[^0-9A-Za-z가-힣_]", "", s)
    return s


def hashtags(item, terms, lo=5, hi=8):
    tags = []
    for t in terms:
        tags.append(clean_tag(t[0] if isinstance(t, tuple) else t))
    tags += [clean_tag(t) for t in FIELD_TAGS.get(item.get("field", ""), ["과학"])]
    tech = (item.get("tech") or "").split(", ")
    tags += [clean_tag(t) for t in tech if t]
    tags += BASE_TAGS
    out, seen = [], set()
    for t in tags:
        if t and len(t) >= 2 and t.lower() not in seen:
            seen.add(t.lower())
            out.append("#" + t)
        if len(out) >= hi:
            break
    return out[:hi] if len(out) >= lo else out


# ------------------------------------------------------------------ 이미지 합성 (Pillow)

def find_font(explicit=None):
    cands = ([explicit] if explicit else []) + FONT_CANDIDATES
    for p in cands:
        if p and os.path.exists(p):
            return p
    return ""


def _pil():
    try:
        from PIL import Image, ImageDraw, ImageFont, ImageFilter
        return Image, ImageDraw, ImageFont, ImageFilter
    except ImportError:
        return None


def _split_long_word(draw, word, font, max_w):
    parts, cur = [], ""
    for ch in word:
        if draw.textlength(cur + ch, font=font) <= max_w or not cur:
            cur += ch
        else:
            parts.append(cur)
            cur = ch
    return parts + [cur]


def wrap_lines(draw, text, font, max_w, max_lines):
    """단어(공백) 단위 자동 줄바꿈. 한 단어가 폭을 넘을 때만 글자 단위로 나눔.
    반환: (lines, overflow, wrapped) — wrapped 는 원래 줄('\\n')보다 줄이 늘었는지."""
    lines = []
    for para in text.split("\n"):
        cur = ""
        for word in para.split(" "):
            pieces = [word] if draw.textlength(word, font=font) <= max_w else _split_long_word(draw, word, font, max_w)
            for piece in pieces:
                trial = (cur + " " + piece) if cur else piece
                if draw.textlength(trial, font=font) <= max_w:
                    cur = trial
                else:
                    if cur:
                        lines.append(cur)
                    cur = piece
        lines.append(cur)
    wrapped = len(lines) > len(text.split("\n"))
    if len(lines) > max_lines:
        return lines[:max_lines], True, wrapped
    return lines, False, wrapped


def fit_text(draw, text, font_path, max_w, max_h, start=112, floor=56, max_lines=3, ImageFont=None):
    """1) 원래 줄 구성 그대로 들어가는 가장 큰 크기 → 2) 없으면 줄바꿈 허용 → 3) 최소 크기에서도 넘치면 말줄임.
    반환: (font, lines, overflow)"""
    best_wrapped = None
    for size in range(start, floor - 1, -6):
        font = ImageFont.truetype(font_path, size)
        lines, over, wrapped = wrap_lines(draw, text, font, max_w, max_lines)
        fits = not over and int(size * 1.22) * len(lines) <= max_h
        if fits and not wrapped:
            return font, lines, False
        if fits and best_wrapped is None and size >= floor + 18:
            best_wrapped = (font, lines)
    if best_wrapped:
        return best_wrapped[0], best_wrapped[1], False
    font = ImageFont.truetype(font_path, floor)
    lines, over, _ = wrap_lines(draw, text, font, max_w, max_lines)
    if over:
        last = lines[-1]
        lines[-1] = (last[:-2] if len(last) > 2 else last) + "…"
    return font, lines, over


def cover(img, size, Image):
    w, h = img.size
    scale = max(size[0] / w, size[1] / h)
    img = img.resize((max(1, int(w * scale)), max(1, int(h * scale))), Image.LANCZOS)
    left, top = (img.width - size[0]) // 2, (img.height - size[1]) // 2
    return img.crop((left, top, left + size[0], top + size[1]))


def gradient_bg(field, Image):
    """기본 그래픽 배경: 세로 그라데이션 + 사선 광택 + 큰 물음표 워터마크 (사진이 없을 때)."""
    from PIL import ImageDraw, ImageFont
    top, bottom = FIELD_COLORS.get(field, ((40, 40, 48), (10, 10, 14)))
    # 세로 그라데이션: 선형 마스크(위 0 → 아래 255)로 두 색을 섞음 (픽셀 루프 없이)
    mask = Image.linear_gradient("L").rotate(0).resize(SIZE)
    img = Image.composite(Image.new("RGB", SIZE, bottom), Image.new("RGB", SIZE, top), mask)
    layer = Image.new("RGBA", SIZE, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.polygon([(760, 0), (1280, 0), (1280, 720), (980, 720)], fill=(255, 255, 255, 14))  # 사선 광택
    d.polygon([(900, 0), (1280, 0), (1280, 420)], fill=(255, 255, 255, 10))
    fp = find_font()
    if fp:
        qf = ImageFont.truetype(fp, 560)
        d.text((870, 40), "?", font=qf, fill=(255, 255, 255, 22))
    return Image.alpha_composite(img.convert("RGBA"), layer).convert("RGB")


def polish(base, Image, ImageFilter):
    """사진·그래픽 공통 마감: 가장자리 비네팅 + 미세한 질감(그레인)."""
    import random
    vign = Image.new("L", SIZE, 0)
    from PIL import ImageDraw
    vd = ImageDraw.Draw(vign)
    vd.ellipse([-200, -160, SIZE[0] + 200, SIZE[1] + 220], fill=255)
    vign = vign.filter(ImageFilter.GaussianBlur(160))
    dark = Image.new("RGBA", SIZE, (0, 0, 0, 150))
    dark.putalpha(Image.eval(vign, lambda v: int((255 - v) * 0.6)))
    base = Image.alpha_composite(base.convert("RGBA"), dark)
    rnd = random.Random(7)
    grain = Image.effect_noise(SIZE, 18).convert("L") if hasattr(Image, "effect_noise") else None
    if grain is not None:
        g = Image.merge("RGBA", (grain, grain, grain, Image.new("L", SIZE, 16)))
        base = Image.alpha_composite(base, g)
    return base


def compose_thumbnail(text, out_path, font_path, bg_path=None, field="", status="확인 필요"):
    """썸네일 1장 합성. 반환: {"ok": bool, "note": str}"""
    pil = _pil()
    if not pil:
        return {"ok": False, "note": "Pillow 미설치 (pip install pillow)"}
    Image, ImageDraw, ImageFont, ImageFilter = pil
    if not font_path:
        return {"ok": False, "note": "한국어 폰트를 찾지 못함 (--font 로 지정)"}
    note = ""
    if bg_path and os.path.exists(bg_path):
        try:
            base = cover(Image.open(bg_path).convert("RGB"), SIZE, Image)
        except Exception as e:
            base, note = gradient_bg(field, Image), f"배경 이미지 열기 실패({e}) → 기본 그래픽"
    else:
        base, note = gradient_bg(field, Image), "기본 그래픽 배경 (이미지 교체 필요)"
    base = polish(base, Image, ImageFilter)
    # 글자 대비용 어두운 그라데이션 (아래쪽 65%)
    overlay = Image.new("RGBA", SIZE, (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    for y in range(int(SIZE[1] * 0.30), SIZE[1]):
        a = int(215 * ((y - SIZE[1] * 0.30) / (SIZE[1] * 0.70)) ** 1.3)
        od.line([(0, y), (SIZE[0], y)], fill=(0, 0, 0, a))
    base = Image.alpha_composite(base, overlay)

    # 본문 크기 계산 (왼쪽 아래 정렬)
    margin, max_w, max_h = 72, SIZE[0] - 160, int(SIZE[1] * 0.60)
    draw = ImageDraw.Draw(base)
    font, lines, over = fit_text(draw, text, font_path, max_w, max_h, ImageFont=ImageFont)
    line_h = int(font.size * 1.18)
    y0 = SIZE[1] - margin - line_h * len(lines)

    # 글자 뒤 부드러운 그림자 (깊이감)
    shadow = Image.new("RGBA", SIZE, (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    y = y0
    for line in lines:
        sd.text((margin + 24 + 6, y + 8), line, font=font, fill=(0, 0, 0, 200),
                stroke_width=max(4, font.size // 10), stroke_fill=(0, 0, 0, 200))
        y += line_h
    base = Image.alpha_composite(base, shadow.filter(ImageFilter.GaussianBlur(10)))
    draw = ImageDraw.Draw(base)

    # 왼쪽 강조 바 + 본문 (흰색, 마지막 줄 노란색, 검은 외곽선)
    accent = (255, 214, 0, 255)
    draw.rounded_rectangle([margin, y0 + 6, margin + 12, y0 + line_h * len(lines) - 10], radius=6, fill=accent)
    stroke = max(4, font.size // 11)
    y = y0
    for i, line in enumerate(lines):
        fill = accent if (i == len(lines) - 1 and len(lines) > 1) else (255, 255, 255, 255)
        draw.text((margin + 24, y), line, font=font, fill=fill, stroke_width=stroke, stroke_fill=(10, 10, 10, 255))
        y += line_h

    # 상태 배지 (왼쪽 위) — 마지막에 올려 가려지지 않게
    label, color = STATUS_BADGE.get(status, STATUS_BADGE["확인 필요"])
    bfont = ImageFont.truetype(font_path, 34)
    bw = int(draw.textlength(label, font=bfont)) + 44
    draw.rounded_rectangle([52, 46, 52 + bw, 46 + 62], radius=16, fill=color + (240,), outline=(255, 255, 255, 90), width=2)
    draw.text((74, 55), label, font=bfont, fill=(255, 255, 255, 255))
    rgb = base.convert("RGB")
    if out_path.lower().endswith(".png"):
        rgb.save(out_path, "PNG")
    else:
        rgb.save(out_path, "JPEG", quality=92, subsampling=0)
        if os.path.getsize(out_path) > 2 * 1024 * 1024:  # 유튜브 2MB 제한
            rgb.save(out_path, "JPEG", quality=80)
            note = (note + " · " if note else "") + "2MB 초과로 JPG 품질 80 으로 저장"
    if over:
        note = (note + " · " if note else "") + "문구가 길어 잘림(…) — 문구를 줄이세요"
    return {"ok": True, "note": note}


# ------------------------------------------------------------------ 위키미디어 공용 배경 (옵션, --bg-commons 를 켰을 때만)

COMMONS_API = "https://commons.wikimedia.org/w/api.php"
COMMONS_UA = "ScienceMysteryTopicFinder/3.0 (personal YouTube research script; Python urllib)"
# 썸네일 배경으로 쓸 수 있는 자유 이용 라이선스만 허용 (그 밖의 라이선스/표기 불명은 건너뜀)
ALLOWED_LICENSE = re.compile(r"^(cc0|public domain|pd-?|cc[- ]by(?:[- ]sa)?(?:[- ]\d(\.\d)?)?|attribution|copyrighted free use)",
                             re.I)
STRIP_HTML = re.compile(r"<[^>]+>")


def _http_get(url, **kw):
    import urllib.request
    req = urllib.request.Request(url, headers={"User-Agent": COMMONS_UA})
    with urllib.request.urlopen(req, timeout=25) as r:
        return r.read()


def commons_search(query, http_get=None, min_width=960, limit=6):
    """위키미디어 공용에서 자유 이용 사진 후보를 찾는다. 반환: 후보 dict 목록 (라이선스 허용된 것만)."""
    import urllib.parse
    http_get = http_get or _http_get
    params = {"action": "query", "generator": "search", "gsrsearch": f"filetype:bitmap {query}",
              "gsrnamespace": "6", "gsrlimit": str(limit), "prop": "imageinfo",
              "iiprop": "url|extmetadata|size|mime", "iiurlwidth": "1600", "format": "json"}
    data = json.loads(http_get(COMMONS_API + "?" + urllib.parse.urlencode(params)))
    out = []
    qwords = [w for w in re.findall(r"[a-z0-9\-]+", query.lower()) if len(w) >= 3]

    def relevance_rank(p):  # 파일 제목에 검색어 단어가 많이 들어간 후보를 앞에 (그다음 검색 순위)
        title = p.get("title", "").lower()
        return (-sum(w in title for w in qwords), p.get("index", 99))

    for p in sorted(data.get("query", {}).get("pages", {}).values(), key=relevance_rank):
        ii = (p.get("imageinfo") or [{}])[0]
        em = ii.get("extmetadata", {})
        lic = STRIP_HTML.sub("", em.get("LicenseShortName", {}).get("value", "")).strip()
        if not ALLOWED_LICENSE.search(lic) or ii.get("width", 0) < min_width:
            continue
        if ii.get("mime") not in ("image/jpeg", "image/png"):
            continue
        out.append({
            "title": p.get("title", ""), "page": ii.get("descriptionurl", ""),
            "url": ii.get("thumburl") or ii.get("url", ""), "width": ii.get("width", 0),
            "license": lic, "license_url": em.get("LicenseUrl", {}).get("value", ""),
            "artist": STRIP_HTML.sub("", em.get("Artist", {}).get("value", "")).strip()[:120],
            "credit": STRIP_HTML.sub("", em.get("Credit", {}).get("value", "")).strip()[:120],
            "attribution_required": not re.search(r"cc0|public domain|^pd", lic, re.I),
        })
    return out


def commons_fetch_photos(item, dest_dir, http_get=None, n=3):
    """소재의 영어 식별어로 공용 사진을 최대 n장 내려받아 dest_dir/photo_1.jpg … 로 저장.
    반환: ([{"path", "title", "page", "license", ...}], 실패 사유 문자열 또는 '')"""
    ids = [t for t in (item.get("yt_ids") or "").split(", ") if t]
    content = [t for t in (item.get("yt_query") or "").split() if t not in ids]
    queries = [" ".join(ids[:2] + content[:2]), " ".join(content[:3]), " ".join(ids[:1] + content[:1]), " ".join(ids[:1])]
    got, seen, tried, err = [], set(), [], ""
    for q in [q for q in queries if q.strip()]:
        if q in tried or len(got) >= n:
            continue
        tried.append(q)
        try:
            cands = commons_search(q, http_get, limit=8)
        except Exception as e:
            err = f"공용 검색 실패({e})"
            continue
        for c in cands:
            if c["title"] in seen or len(got) >= n:
                continue
            try:
                raw = (http_get or _http_get)(c["url"])
            except Exception as e:
                err = f"공용 다운로드 실패({e})"
                continue
            ext = ".jpg" if c["url"].lower().endswith((".jpg", ".jpeg")) else ".png"
            path = os.path.join(dest_dir, f"photo_{len(got) + 1}{ext}")
            with open(path, "wb") as f:
                f.write(raw)
            seen.add(c["title"])
            got.append({**c, "path": path, "query": q})
    if not got:
        return [], err or f"검색어 {tried} 로 허용 라이선스 사진을 찾지 못함"
    return got, ""


def commons_fetch_bg(item, dest_dir, http_get=None):
    """(호환용) 공용 사진 1장. 반환: (경로 또는 '', 출처 dict 또는 사유)"""
    photos, err = commons_fetch_photos(item, dest_dir, http_get, n=1)
    return (photos[0]["path"], photos[0]) if photos else ("", err)


def commons_credit_lines(c, prefix="배경 이미지 출처"):
    by = c.get("artist") or c.get("credit") or "작자 미상"
    lines = [f"{prefix}: 위키미디어 공용 — {c['title']}",
             f"  파일: {os.path.basename(c.get('path', ''))}" if c.get("path") else "",
             f"  페이지: {c['page']}", f"  작가/크레딧: {by}",
             f"  라이선스: {c['license']}" + (f" ({c['license_url']})" if c.get("license_url") else ""),
             f"  검색어: {c.get('query', '')}"]
    lines = [l for l in lines if l]
    if c.get("attribution_required"):
        lines.append(f"  표기 문구(영상 설명란에 넣으세요): \"{c['title'].replace('File:', '')}\" by {by}, {c['license']}, via Wikimedia Commons")
        if re.search(r"sa", c["license"], re.I):
            lines.append("  주의: SA(동일조건변경허락) — 변형한 썸네일에도 같은 라이선스 표기가 필요합니다")
    else:
        lines.append("  표기 의무 없음 (출처 기재 권장)")
    return lines


# ------------------------------------------------------------------ 소재별 폴더 생성

def unique_dir(path):
    n, p = 1, path
    while os.path.exists(p):
        n += 1
        p = f"{path}_{n}"
    os.makedirs(p)
    return p


def slug(item, rank):
    ids = (item.get("yt_ids") or item.get("yt_query") or item.get("title", "")).replace(",", " ").split()
    s = "_".join(re.sub(r"[^a-z0-9]", "", w.lower()) for w in ids[:3])
    return f"{rank:02d}_{s or 'topic'}"


IMG_EXT = (".jpg", ".jpeg", ".png", ".webp")


def user_photos_for(rank, bg_dir, bg_paths):
    """사용자 사진: bg_dir 안에 'NN_' 로 시작하는 소재별 하위 폴더가 있으면 그 사진들, 없으면 순서대로 1장."""
    if bg_dir and os.path.isdir(bg_dir):
        for name in sorted(os.listdir(bg_dir)):
            sub = os.path.join(bg_dir, name)
            if os.path.isdir(sub) and name.startswith(f"{rank:02d}_"):
                return [os.path.join(sub, f) for f in sorted(os.listdir(sub)) if f.lower().endswith(IMG_EXT)]
    if bg_paths:
        return [bg_paths[(rank - 1) % len(bg_paths)]]
    return []


def compare_labels(item):
    """비교형 라벨: 제목에 '앞면/뒷면', 'before/after' 류가 있으면 그 쌍, 없으면 '사진 1/2'."""
    t = (item.get("title", "") + " " + item.get("title_ko", "")).lower()
    # 두 쌍 단어가 '모두' 있을 때만 그 라벨 (한쪽만 있으면 두 사진이 전후·앞뒤 관계처럼 오해될 수 있음)
    for a, b, la, lb in (("near side", "far side", "앞면", "뒷면"), ("nearside", "farside", "앞면", "뒷면"),
                         ("two faces", "moon", "앞면", "뒷면"), ("before", "after", "이전", "이후"), ("앞면", "뒷면", "앞면", "뒷면")):
        if a in t and b in t:
            return la, lb
    return "사진 1", "사진 2"


def build_variants(it, photos, copies, font_path, d, prefer_compare=None):
    """실사 3안: A 피사체 중심형 / C 증거 확대형 / B 좌우 비교형(사진 2장 이상) 또는 A' (왼쪽 배치·타이트 크롭).
    반환: (이미지 경로 목록, 메타 목록, 메모 목록)"""
    import layouts
    images, metas, notes = [], [], []
    p1 = photos[0]["path"]
    plan = [("A", lambda out: layouts.layout_subject(p1, copies[0], font_path, it.get("status", ""), out, side="right", frac=0.55)),
            ("C", lambda out: layouts.layout_zoom(p1, copies[1], font_path, it.get("status", ""), out))]
    if len(photos) >= 2 and prefer_compare is not False:
        la, lb = compare_labels(it)
        plan.append(("B", lambda out: layouts.layout_compare(p1, photos[1]["path"], copies[2], font_path,
                                                             it.get("status", ""), out, labels=(la, lb))))
    else:
        notes.append("비교형(B) 생략: 비교할 두 번째 사진이 없어 A' (왼쪽 배치·타이트 크롭)로 대체")
        plan.append(("A2", lambda out: layouts.layout_subject(p1, copies[2], font_path, it.get("status", ""), out, side="left", frac=0.42)))
    for label, fn in plan:
        out = os.path.join(d, f"thumb_{label}.jpg")
        try:
            meta = fn(out)
        except Exception as e:
            notes.append(f"{label}: 생성 실패({e})")
            continue
        meta["file"] = os.path.basename(out)
        meta["copy"] = copies[len(images) if len(images) < 3 else 2]
        if meta.get("text_overflow"):
            notes.append(f"{label}: 문구가 길어 잘림(…) — 문구를 줄이세요")
        images.append(out)
        metas.append(meta)
    return images, metas, notes


def make_assets(picks, out_root, font=None, bg_paths=None, bg_credit="", glossary=None, translate=None,
                commons=False, http_get=None, bg_dir=None):
    """선정 소재마다 문구 3안 · 썸네일 3안 · 해시태그 · 출처/편집 메타데이터를 폴더에 저장.
    실사(사용자 사진 또는 --bg-commons 공용 사진)가 있으면 실사 편집 레이아웃(A/B/C), 없으면 기본 그래픽을 '임시' 로 표시."""
    glossary = glossary if glossary is not None else load_glossary()
    font_path = find_font(font)
    bg_paths = [p for p in (bg_paths or []) if p and os.path.exists(p)]
    os.makedirs(out_root, exist_ok=True)
    summary = {"font": font_path or "없음", "pillow": bool(_pil()), "images": 0, "topics": 0, "commons_ok": 0,
               "photo_topics": 0, "graphic_topics": 0, "compare_topics": 0,
               "bg": (f"사용자 사진 ({bg_dir or len(bg_paths)})" if (bg_dir or bg_paths) else
                      ("위키미디어 공용 (옵션 켜짐)" if commons else "기본 그래픽 (임시, 실사 없음)")),
               "yake": bool(optional_yake_terms("test keyword extraction sample text")),
               "rembg": _has_rembg()}
    for rank, it in enumerate(picks, 1):
        terms, notes = ko_terms(it, glossary, translate)
        name = short_name(it, terms)
        copies = thumb_copies(it, name)
        tags = hashtags(it, terms)
        d = unique_dir(os.path.join(out_root, slug(it, rank)))

        # ---- 실사 확보: 사용자 사진 > 공용 사진(옵션) > 없음
        photos, photo_err = [], ""
        for p in user_photos_for(rank, bg_dir, bg_paths):
            photos.append({"path": p, "title": os.path.basename(p), "page": "", "license": bg_credit or "(직접 입력)",
                           "artist": "", "credit": bg_credit, "attribution_required": None, "source": "사용자 제공"})
        if not photos and commons:
            photos, photo_err = commons_fetch_photos(it, d, http_get, n=3)
            for p in photos:
                p["source"] = "위키미디어 공용"
            if photos:
                summary["commons_ok"] += 1

        images, metas, img_notes = [], [], []
        mode = "실사 편집"
        if photos and font_path and _pil():
            images, metas, img_notes = build_variants(it, photos, copies, font_path, d)
            if len(photos) >= 2:
                summary["compare_topics"] += 1
        if not images:  # 실사가 없거나 실패 → 기본 그래픽 (임시)
            mode = "기본 그래픽(임시)"
            for label, text in zip("ABC", copies):
                out = os.path.join(d, f"thumb_{label}.jpg")
                r = compose_thumbnail(text, out, font_path, None, it.get("field", ""), it.get("status", ""))
                if r["ok"]:
                    images.append(out)
                    metas.append({"layout": "기본 그래픽(임시)", "file": os.path.basename(out), "copy": text})
                if r["note"]:
                    img_notes.append(f"{label}: {r['note']}")
            if photo_err:
                img_notes.append(f"실사 없음: {photo_err}")
            summary["graphic_topics"] += 1
        else:
            summary["photo_topics"] += 1
        summary["images"] += len(images)

        # ---- 텍스트 파일
        with open(os.path.join(d, "copy.txt"), "w", encoding="utf-8") as f:
            f.write(f"소재: {name}\n해결 상태: {it.get('status')}\n원문: {it.get('title')}\n\n")
            for label, text in zip("ABC", copies):
                f.write(f"[{label}] {text.replace(chr(10), ' / ')}\n")
            if notes:
                f.write("\n용어 메모: " + ", ".join(notes) + "\n")
        with open(os.path.join(d, "hashtags.txt"), "w", encoding="utf-8") as f:
            f.write(" ".join(tags) + "\n")
        with open(os.path.join(d, "source.txt"), "w", encoding="utf-8") as f:
            f.write(f"썸네일 방식: {mode}\n")
            if not photos:
                f.write("배경 이미지: 없음 (기본 그래픽 — 실사로 교체 필요)\n")
                if photo_err:
                    f.write(f"위키미디어 공용: {photo_err}\n")
            for i, p in enumerate(photos, 1):
                if p.get("source") == "위키미디어 공용":
                    f.write("\n".join(commons_credit_lines(p, prefix=f"사진 {i} 출처")) + "\n")
                else:
                    f.write(f"사진 {i}: {p['path']}\n  출처: {bg_credit or '(직접 입력)'}\n  이용 조건/라이선스: {'(직접 입력)' if not bg_credit else '(확인 후 입력)'}\n")
            f.write(f"폰트: {font_path or '없음'}\n")
            f.write("규격: 1280×720 JPG (유튜브 권장 1280×720, 2MB 이하 — 업로드 전 현재 규격 재확인)\n")
            if img_notes:
                f.write("메모: " + " | ".join(img_notes) + "\n")
        # ---- 메타데이터 (사용 이미지 · 편집 · 레이아웃 · 출처 · 사실 구분)
        meta = {
            "topic": name, "status": it.get("status"), "title": it.get("title"), "mode": mode,
            "photos": [{k: p.get(k) for k in ("path", "title", "page", "license", "license_url", "artist", "credit", "source", "query")} for p in photos],
            "variants": metas, "hashtags": tags, "notes": img_notes,
            "honesty": ("사진은 소재와 관련된 참고 이미지이며 해당 연구의 실제 표본·발견 장면이 아닐 수 있습니다. "
                        "확대·크롭·명암 보정만 했고 사진 속 형태·숫자·문자는 변형하지 않았습니다." if photos else
                        "실사 없이 만든 임시 그래픽입니다."),
        }
        with open(os.path.join(d, "meta.json"), "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2, default=str)

        first = photos[0] if photos else None
        if first and first.get("source") == "위키미디어 공용":
            credit = (f"위키미디어 공용 '{first['title'].replace('File:', '')}' · {first['license']} · "
                      f"{first.get('artist') or first.get('credit') or '작자 미상'}" + (f" (+{len(photos) - 1}장)" if len(photos) > 1 else ""))
        elif first:
            credit = f"사용자 사진 {len(photos)}장"
        elif photo_err:
            credit = f"공용 사진 없음({photo_err[:60]}) → 기본 그래픽(임시)"
        else:
            credit = "기본 그래픽(임시, 실사 없음)"
        it.update({"asset_dir": d, "thumb_copies": copies, "hashtags": tags, "topic_name": name,
                   "thumb_images": images, "thumb_layouts": [m.get("layout", "") for m in metas],
                   "thumb_notes": " | ".join(img_notes), "term_notes": ", ".join(notes),
                   "bg_credit": credit, "bg_page": first.get("page", "") if first else "", "thumb_mode": mode})
        summary["topics"] += 1
    return summary


def _has_rembg():
    try:
        import rembg  # noqa: F401
        return True
    except Exception:
        return False


if __name__ == "__main__":
    # 간단 확인: python thumbs.py "문구\n두번째 줄" out.jpg [사진경로]
    txt = sys.argv[1] if len(sys.argv) > 1 else "오사카 모사사우루스 화석\n마침내 풀렸다"
    out = sys.argv[2] if len(sys.argv) > 2 else "thumb_test.jpg"
    print(compose_thumbnail(txt.replace("\\n", "\n"), out, find_font(), None, "고고학/인류", "해결 근거"), out)
