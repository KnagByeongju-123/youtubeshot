r"""유튜브 정책 지키기 - 규칙 4가지 (2026-10 기준, 최종 확인은 유튜브 고객센터에서)

  1) AI 이미지 표시: AI로 만든 그림이 들어가면 화면 설명에 'AI 상상도', 설명란에 '실제 사진 아님' 문구,
     업로드 체크리스트에 '변경되거나 합성된 콘텐츠 = 예' 를 적음 (유튜브 합성 콘텐츠 공개 의무, 2024-03~)
  2) 사실 콘텐츠의 AI 그림은 개념도·상상도로만: 실제 관측·실험·사건을 사진처럼 꾸미지 않음 (그림 기획 지시 + 프롬프트 꼬리)
  3) 영상마다 형식 바꾸기: 강조색·자막 등장 효과·배경음·오프닝 방식·챕터 수를 제목에 따라 다르게
     ('틀에 찍은 듯한 대량 생산 콘텐츠'는 수익 창출 제외 - 유튜브 '진정성 없는 콘텐츠' 정책)
  4) 건강 주제 경고: AI 목소리가 건강·의료를 다루면 2026-07 유튜브가 밝힌 '진정성 없는 콘텐츠' 범주와 겹침
     → 업로드 체크리스트에 경고 + 본인 목소리 도입부 권장
  결과: <영상>_업로드_체크.txt (publish_kit 이 만듦)
"""
import hashlib
import json
import os
import re

AI_MARK = "AI 생성 이미지"
AI_CAPTION = "AI 상상도"
AI_DESC_LINE = "※ 이 영상의 일부 이미지는 AI로 만든 상상도·개념도이며 실제 사진이 아닙니다."
FACT_IMAGE_RULE = ("\n[사실 콘텐츠 그림 규칙 - 유튜브 합성 콘텐츠 정책] 실제 관측·실험·사건·인물을 사진처럼 꾸며 그리지 않는다. "
                   "개념도·도식·누가 봐도 그림인 일러스트(수채화·평면 그래픽·3D 다이어그램)로만 그린다. "
                   "실제 사진이 있어야 할 장면(실제 망원경 사진, 실제 환자, 실제 실험 장비)은 그림 대상에서 뺀다.")
FACT_PROMPT_TAIL = ", clearly an illustration or diagram, not a photograph, no photorealistic rendering"
HEALTH_WORDS = r"(비만|체중|임상시험|신약|치료제|의약품|부작용|진단|환자|질환|당뇨|혈압|백신|복용|주사|처방|건강|의사|병원)"

# 3) 영상마다 바꿀 형식 (모두 다큐에 어울리는 값만)
ACCENTS = ["#FF6B6B", "#4FC3F7", "#FFD54F", "#81C784", "#BA68C8", "#FF8A65", "#4DD0E1", "#F06292"]
SUB_ANIMS = ["팝(튀어나옴)", "올라옴", "페이드"]
BGMS = ["잔잔한 패드", "어두운 드론", "우주", "긴장 펄스", "심해", "바람"]
OPENINGS = ["가장 놀라운 숫자 하나로 시작", "시청자에게 던지는 질문으로 시작", "한 장면을 눈앞에 그리듯 묘사하며 시작",
            "모두가 믿던 통념을 뒤집는 한 문장으로 시작", "연구자가 결과를 처음 본 순간으로 시작", "일상의 물건·경험에 빗대며 시작"]


DESC_STYLES = [   # 설명란 방식 (영상마다 다르게 - 같은 틀만 반복되면 '대량 생산'처럼 보임)
    "질문형: 영상이 던지는 큰 질문 한 문장으로 시작 → 무엇을 알게 되는지 2~3문장 → 연구가 나온 곳·시점 한 문장",
    "요약 목록형: 첫 줄에 핵심 한 문장 → '이 영상에서 다루는 것' 3~4줄 목록(•로 시작) → 마무리 한 문장",
    "장면형: 영상 속 가장 인상적인 장면이나 숫자를 묘사하며 시작 → 그 뒤의 이야기 2~3문장 → 시청 포인트 한 문장",
    "연구 소개형: '○년 ○월, ○○ 연구팀이…'처럼 연구 소개로 시작 → 왜 놀라운지 → 아직 남은 질문 한 문장",
    "대화형: 시청자에게 말을 거는 한 문장('혹시 ~ 생각해 보신 적 있나요?')으로 시작 → 영상 내용 2~3문장 → 댓글로 의견 묻기",
    "짧고 굵게: 3~4문장만. 핵심 사실 하나, 그것이 왜 중요한지, 영상에서 확인할 것",
]
DESC_BODY_MAX = 450      # 설명 본문 글자 수 상한 (한글 450자 ≈ 1,350바이트. 출처·사진 출처·해시태그까지 합쳐 5,000바이트 이내가 되게)
DESC_MAX_BYTES = 4900    # 유튜브 설명란 한도는 5,000 '바이트'(UTF-8). 한글 한 글자 = 3바이트 → 한글만이면 약 1,660자. 여유 100바이트


def nbytes(t):
    return len(str(t).encode("utf-8"))


def fit_description(text, limit=DESC_MAX_BYTES):
    """완성된 설명란 글을 유튜브 한도(5,000바이트) 안으로. 줄이는 순서:
    1) 사진 출처의 주소(URL) 빼기 (작가·라이선스는 남김, 영상 속 사진 아래에도 표기됨)
    2) 출처 목록을 앞 3개만 (나머지는 '외 N건')  3) 사진 출처를 뒤에서부터 줄임 ('외 N장')
    4) 그래도 넘치면 설명 본문 끝을 문장 단위로 자름. 유튜브가 막는 '<' '>' 문자는 바꿈"""
    text = str(text).replace("<", "‹").replace(">", "›")
    if nbytes(text) <= limit:
        return text
    lines = text.rstrip("\n").split("\n")

    def sec(title):
        if title not in lines:
            return None, None
        i = lines.index(title)
        j = i + 1
        while j < len(lines) and lines[j].strip() and not lines[j].startswith(("📚", "🖼", "#")):
            j += 1
        return i, j
    tag_i = max((k for k, ln in enumerate(lines) if ln.startswith("#")), default=None)
    tags = lines[tag_i] if tag_i is not None else ""
    si, sj = sec("📚 출처")
    pi, pj = sec("🖼 사진 출처")
    first = min([x for x in (si, pi, tag_i) if x is not None] + [len(lines)])
    head = lines[:first]
    srcs = lines[si + 1:sj] if si is not None else []
    creds = lines[pi + 1:pj] if pi is not None else []

    def build(h, s_, more_s, c_, more_c):
        out = list(h)
        if s_:
            out += ["", "📚 출처"] + s_ + ([f"외 {more_s}건 (업로드문구 파일 참고)"] if more_s else [])
        if c_ or more_c:
            out += ["", "🖼 사진 출처"] + c_ + ([f"외 {more_c}장 (출처는 영상 속 사진 아래 표기)"] if more_c else [])
        if tags:
            out += ["", tags]
        return re.sub(r"\n{3,}", "\n\n", "\n".join(out)).strip() + "\n"
    creds = [re.sub(r"\s*\(https?://.*\)\s*$", "", c) for c in creds]             # 1) 사진 출처 주소 빼기 (파일 이름에 괄호가 있어도)
    out = build(head, srcs, 0, creds, 0)
    if nbytes(out) > limit and len(srcs) > 3:                                         # 2) 출처는 앞 3개
        out = build(head, srcs[:3], len(srcs) - 3, creds, 0)
        srcs, more_s = srcs[:3], len(srcs) - 3
    else:
        more_s = 0
    k = len(creds)
    while nbytes(out) > limit and k > 0:                                              # 3) 사진 출처 줄이기
        k -= 1
        out = build(head, srcs, more_s, creds[:k], len(creds) - k)
    while nbytes(out) > limit and head:                                               # 4) 본문 끝을 문장 단위로 자르기
        body = "\n".join(head).rstrip()
        cut = max(body.rfind(". ", 0, len(body) - 2), body.rfind("다.", 0, len(body) - 2), body.rfind("\n", 0, len(body) - 1))
        if cut <= 50:
            body = body[:max(50, len(body) - 200)]
        else:
            body = body[:cut + 1]
        head = (body.rstrip() + " …").split("\n")
        out = build(head, srcs, more_s, creds[:k], len(creds) - k)
    return out


def desc_style(title):
    return _pick(DESC_STYLES, title, "desc")


def desc_rule(title):
    """업로드 문구 AI에 붙일 '이번 설명란 방식' 지시"""
    return (f"\n\n[이번 설명란 방식 - 위 설명 구성 대신 이 방식을 따를 것] {desc_style(title)}"
            f"\n- 설명 본문은 {DESC_BODY_MAX}자 이내. '이 영상은 단순히 ~이 아닙니다', '~한 분께 추천합니다' 같은 정해진 문장은 쓰지 않는다.")


HUMAN_RULE = """
[공통 규칙 - 사람이 쓴 것처럼 (AI 틀 티 내지 않기)]
- 한 사람의 진행자 시점을 유지한다. 1인칭은 조사·읽기 과정에만 가끔, 정직하게 쓴다(예: '저는 처음에 이 제목을 과장인 줄 알았습니다', '논문을 끝까지 읽고서야 이해가 됐는데요', '솔직히 이 부분은 저도 아직 잘 모르겠습니다').
  실험을 직접 했다거나, 현장에 갔다거나, 연구자를 만났다는 식의 지어낸 경험은 절대 쓰지 않는다.
- 문장 길이를 섞는다(짧게 끊는 문장 + 가끔 긴 문장). 가끔 '여기서 잠깐', '재미있는 건 따로 있습니다' 같은 말 거는 표현. 끝부분에서 오프닝의 장면·숫자를 다시 불러온다.
- 모르는 것·아직 확인 안 된 것을 한 번은 솔직하게 말한다.
- 틀에 박힌 문장 금지: '오늘은 ~에 대해 알아보겠습니다', '~알게 되실 겁니다'로 딱딱하게 끝나는 예고, '구독과 좋아요 부탁드립니다'.
  마무리는 시청자에게 진짜 궁금한 질문 하나 + (원하면) 채널 이야기는 가볍게 한마디.
- 챕터 제목은 대화하듯(예: '그런데 숫자가 이상했습니다'). 챕터마다 길이를 똑같이 맞추지 않는다.
"""


# ---- 시청 유지 규칙 (1위 영상 분석, 2026-10-22): 첫 30초에 3분의 1이 나가고, 챕터 경계마다 조금씩 빠지고, 다른 영상으로 1.5%만 넘어감 ----
RETENTION_RULE = """
[공통 규칙 - 시청 유지 (인기 영상 분석에서 나온 규칙)]
- 첫 5초: 첫 문장은 제목·썸네일이 약속한 바로 그 대상·숫자·장면을 곧장 말한다(제목의 핵심 낱말이 첫 문장에 나오게). 배경 설명은 그 뒤에.
- 챕터 끝 예고: 마지막 챕터를 뺀 모든 챕터는 '진짜 예고' 한 문장으로 끝낸다. '잠시 뒤', '곧', '다음 장에서', '이어서' 같은 앞을 가리키는 말 + 다음 챕터의 가장 놀라운 것(뒤집히는 해석·의외의 숫자·반론)을 무엇인지는 숨기고 존재만 알림
  (예: '그런데 잠시 뒤 보실 숫자 하나가 이 설명을 통째로 흔들어 놓습니다.'). 그냥 다리 놓는 문장('이제 하나씩 살펴볼게요')은 예고가 아님. 다음 챕터에 실제로 있는 내용만, 과장 없이, 매번 다른 말로.
- 시리즈 한 줄: 마무리 부분에 이 채널이 어떤 이야기를 따라가는지 자연스러운 한 문장(예: '이 채널은 아직 풀리지 않은 수수께끼를 최신 연구로 따라가고 있습니다'). '구독과 좋아요 부탁드립니다' 같은 말은 여전히 쓰지 않는다.
"""
SERIES_LINES = [     # 마무리에 넣는 채널 정체성 한 줄 (영상마다 다른 말로 - 같은 문장 반복은 '틀' 티가 남)
    "이 채널은 아직 풀리지 않은 수수께끼를, 최신 연구가 나올 때마다 따라가 보고 있습니다.",
    "저는 이렇게 아직 답이 다 나오지 않은 이야기들을, 새 연구가 나올 때마다 하나씩 따라가 보고 있어요.",
    "이 채널에서는 오래된 수수께끼에 새 연구가 어떤 답을 내놓는지, 계속 이어서 살펴보고 있습니다.",
    "풀린 줄 알았던 것, 아직 안 풀린 것, 이런 이야기들을 최신 연구로 계속 따라가 보려고 합니다.",
    "아직 결론이 나지 않은 수수께끼를 연구가 한 걸음씩 풀어 가는 과정, 이 채널은 그걸 계속 따라갑니다.",
]
SERIES_PAT = r"(이 채널(은|에서는|에서)|따라가(고|보고|보려고|봅니다)|계속 (따라|살펴|이어))"
# 진짜 예고 = 앞으로 나올 것을 분명히 가리키는 말이 들어 있음 (그냥 질문·다리 놓는 문장은 예고로 안 침 - 사용자 확인 2026-10-22)
TEASER_PAT = r"(잠시 뒤|잠시 후|곧 |다음 장|다음 이야기|다음 챕터|이어서|바로 다음|뒤에서|조금 뒤|이따가)"


def series_line(title):
    return _pick(SERIES_LINES, title, "series")


def _narr_lines(block):
    return [ln for ln in block.split("\n") if ln.strip() and not ln.lstrip().startswith(("[사진:", "## ", "♪"))]


def chapters_of(story):
    """대본 → [오프닝, 챕터1, 챕터2 …] 블록 (챕터 블록은 '## ' 줄로 시작)"""
    parts = re.split(r"\n(?=## )", "\n" + story.strip())
    return [p.strip("\n") for p in parts if p.strip()]


def teaser_missing(story):
    """마지막 챕터를 뺀 챕터 중 끝 문장에 다음 챕터 예고가 없는 챕터 번호(1부터) 목록"""
    blocks = [b for b in chapters_of(story) if b.startswith("## ")]
    out = []
    for i, b in enumerate(blocks[:-1]):
        ln = _narr_lines(b)
        last = re.split(r"(?<=[.!?…])\s+", ln[-1].strip())[-1] if ln else ""
        if not re.search(TEASER_PAT, last):
            out.append(i + 1)
    return out


def has_series_line(story):
    blocks = chapters_of(story)
    tail = "\n".join(_narr_lines(blocks[-1])) if blocks else ""
    return bool(re.search(SERIES_PAT, tail))


def add_series_line(story, title):
    """시리즈 한 줄이 없으면 마지막 문단(시청자 질문) 바로 앞에 한 문단으로 넣음"""
    if has_series_line(story) or "\n## " not in "\n" + story:
        return story, False
    paras = story.rstrip().split("\n\n")
    idx = max(i for i, p in enumerate(paras) if _narr_lines(p))
    paras.insert(idx, series_line(title))
    return "\n\n".join(paras), True


# ---- 업로드 키트: 재생목록·고정 댓글·최종 화면 추천 (1위 영상에서 '다음 동영상'으로 넘어간 비율이 1.5%뿐) ----
PLAYLIST_FILE = "_재생목록.json"
CHANNEL_LIST = "_채널영상.txt"     # output\장문\_채널영상.txt : 채널에 실제로 올린 영상 제목 한 줄에 하나 (잘된 영상을 위에)
ENGAGE_SYSTEM = """너는 한국 유튜브 다큐 채널의 운영 담당이다. 새 영상 하나를 채널의 다른 영상과 이어 주는 방법을 정한다.
- playlist: 이 영상이 들어갈 재생목록 이름 하나. [지금 있는 재생목록] 중 맞는 게 있으면 그 이름을 그대로 쓰고, 없을 때만 새 이름(짧고 시청자가 이해하기 쉬운 주제명, 예: '고대 문자 해독', '고대 미스터리 최신 연구').
- related: [채널의 다른 영상] 중 이 영상을 본 사람이 이어서 볼 만한 영상 제목 1~3개 (목록에 있는 제목 그대로, 가장 관련 깊은 순). 없으면 빈 목록.
- pinned: 고정 댓글. 존댓말 2~4줄. 영상 내용에 대한 진짜 궁금한 질문 하나로 시작하고, related 첫 영상을 '이어서 보면 좋은 영상: 「제목」'처럼 한 줄로 소개. '구독과 좋아요 부탁' 금지, 낚시 금지, 이모지는 많아야 1개.
반드시 JSON만 출력: {"playlist": "...", "related": ["..."], "pinned": "..."}"""


def engagement_kit(m, model, base, title, story, out_root, log=None):
    """<base>_재생목록_고정댓글.txt: 재생목록 이름(채널 전체에서 같은 이름 유지 → _재생목록.json) + 고정 댓글 + 최종 화면 추천"""
    log = log or (lambda x: None)
    cz = m._load_korean_reading("콘텐츠_정리")
    others = []
    try:
        for d in sorted(os.listdir(out_root)):
            if re.match(r"^\d{4}_", d) and os.path.isdir(os.path.join(out_root, d)):
                others.append(d[5:])
        cv = os.path.join(out_root, CHANNEL_LIST)           # 채널에 올라간 실제 제목 (사람이 적어 둔 것, 인기 영상 우선)
        if os.path.exists(cv):
            others = [ln.strip() for ln in open(cv, encoding="utf-8") if ln.strip() and not ln.startswith("#")] + others
        mf = os.path.join(out_root, getattr(cz, "MADE_FILE", "_만든주제.txt"))
        if os.path.exists(mf):      # 업로드 후 지운 영상 제목 (주제 설명 문장은 빼고 제목만: 40자 이내)
            others += [ln.strip() for ln in open(mf, encoding="utf-8") if 0 < len(ln.strip()) <= 40 and not ln.startswith("#")]
    except OSError:
        pass
    me = m.safe_name(title)
    others = [o for o in dict.fromkeys(others) if o and m.safe_name(o) != me and not o.endswith("_쇼츠")][-80:]
    pf = os.path.join(out_root, PLAYLIST_FILE)
    try:
        pls = json.load(open(pf, encoding="utf-8"))
    except Exception:
        pls = {}
    body = re.sub(r"\[사진:[^\]]*\]\n*", "", story)[:2500]
    d = m.ask_json(model, ENGAGE_SYSTEM, f"[이 영상 제목] {title}\n\n[대본 앞부분]\n{body}\n\n[지금 있는 재생목록]\n" +
                   ("\n".join(f"- {k}" for k in pls) or "(없음)") + "\n\n[채널의 다른 영상]\n" + ("\n".join(f"- {o}" for o in others) or "(없음)"))
    pl = str(d.get("playlist") or "").strip()[:60] or "고대 미스터리 최신 연구"
    rel = [str(x).strip() for x in (d.get("related") or []) if str(x).strip() in others][:3]
    pin = str(d.get("pinned") or "").strip()
    pls.setdefault(pl, [])
    if title not in pls[pl]:
        pls[pl].append(title)
    m.atomic_write_text(pf, json.dumps(pls, ensure_ascii=False, indent=1))
    same = [t for t in pls[pl] if t != title]
    end = rel[:1] or same[-1:]
    txt = (f"[재생목록]\n{pl}\n"
           f"  → 유튜브 스튜디오 → 콘텐츠 → 이 영상 → 세부정보 → '재생목록'에서 고르기 (없으면 '새 재생목록'으로 이 이름 그대로 만들기)\n"
           + (f"  같은 재생목록에 넣은 영상: " + ", ".join(f"「{t}」" for t in same) + "\n" if same else "") +
           f"\n[고정 댓글]  (영상 아래 댓글로 달고 ⋮ → '고정')\n{pin}\n"
           f"\n[최종 화면]  (편집기 → 최종 화면 → 끝 20초)\n"
           f"  - 동영상 1: " + (f"특정 동영상 「{end[0]}」" if end else "'시청자 맞춤' (아직 이어 줄 영상이 없음)") + "\n"
           f"  - 동영상 2: '시청자 맞춤' (유튜브가 그 사람에게 맞는 영상을 골라 줌)\n"
           f"  - 구독 버튼 요소 1개\n"
           + ("\n[이어서 보면 좋은 영상 (관련 순)]\n" + "\n".join(f"- {t}" for t in rel) + "\n" if rel else ""))
    m.atomic_write_text(base + "_재생목록_고정댓글.txt", txt)
    log(f"  🔗 재생목록 '{pl}' · 고정 댓글 · 최종 화면 추천 저장 ({os.path.basename(base)}_재생목록_고정댓글.txt)")
    return txt


def _pick(seq, key, salt):
    h = int(hashlib.md5(f"{salt}|{key}".encode("utf-8")).hexdigest(), 16)
    return seq[h % len(seq)]


def vary_settings(s, title, log=None):
    """제목에 따라 강조색·자막 등장 효과·배경음을 정해 settings dict 를 바꿈 (같은 제목이면 늘 같은 값 → 다시 만들어도 그대로)"""
    ch = {"accent_color": _pick(ACCENTS, title, "accent"), "sub_anim": _pick(SUB_ANIMS, title, "anim"),
          "bgm_style": _pick(BGMS, title, "bgm")}
    s.update(ch)
    if log:
        log(f"🎨 영상 형식 다양화: 강조색 {ch['accent_color']} · 자막 효과 {ch['sub_anim']} · 배경음 {ch['bgm_style']}")
    return ch


def opening_style(topic):
    """대본 오프닝 방식 (주제마다 다르게)"""
    return _pick(OPENINGS, topic, "opening")


def chapter_count(base_n, topic):
    """챕터 수를 주제마다 ±1 (3~12)"""
    return max(3, min(12, base_n + (-1, 0, 1)[int(hashlib.md5(topic.encode("utf-8")).hexdigest(), 16) % 3]))


def ai_images_in(story):
    return [ln for ln in (story or "").split("\n") if ln.lstrip().startswith("[사진:") and AI_MARK in ln]


def is_health(story, notes=""):
    return len(re.findall(HEALTH_WORDS, f"{story}\n{notes}")) >= 5


def checklist(title, story, notes="", portrait=False):
    """업로드 전에 확인할 것 (정책 관련)"""
    ai = ai_images_in(story)
    lines = [f"[업로드 체크리스트 - {title}]", ""]
    if ai:
        lines += [f"□ 이 영상에 AI로 만든 그림 {len(ai)}장이 있습니다.",
                  "   → 업로드 화면 '변경되거나 합성된 콘텐츠' 질문: 그림이 실제 장면·사람·장소로 착각될 만하면 '예'",
                  "     (화면 설명에 'AI 상상도'가 붙어 있고 누가 봐도 그림이면 '아니요'도 가능하지만, 헷갈리면 '예'가 안전)",
                  "   → 설명란에 '실제 사진이 아닙니다' 문구가 들어가 있는지 확인"]
    else:
        lines += ["□ AI로 만든 그림 없음 (실제 사진·공개 자료만) → '변경되거나 합성된 콘텐츠' 질문: 아니요"]
    lines += ["□ 대본·자막을 AI가 도왔고 목소리는 AI 성우(Supertonic)입니다 → 이것만으로는 합성 콘텐츠 표시 대상이 아닙니다"]
    if is_health(story, notes):
        lines += ["", "⚠ 건강·의료 주제입니다.",
                  "   유튜브는 2026-07 'AI 목소리가 건강·금융 같은 민감한 주제를 다루는 콘텐츠'를 수익 창출이 어려운 '진정성 없는 콘텐츠' 범주로 밝혔습니다.",
                  "   → 권장: 영상 앞 10~20초를 본인 목소리로 직접 녹음해 넣기 (프로그램의 '문단별 음성 파일' 기능)",
                  "   → 설명란의 '의학적 조언 아님' 문구와 연구비 출처가 있는지 확인"]
    lines += ["", "□ 채널 영상들이 서로 너무 비슷해 보이지 않는지 (같은 구성·같은 화면만 반복되면 '대량 생산' 판정 위험)",
              "   → 이 프로그램은 제목마다 강조색·자막 효과·배경음·오프닝 방식·챕터 수를 바꿉니다. 썸네일도 후보 중 다른 디자인을 골라 보세요",
              "□ 사진 출처(CC 라이선스) 표기가 설명란에 있는지"]
    if portrait:
        lines += ["□ 쇼츠: 고정 댓글이나 '관련 동영상'에 같은 주제 롱폼 연결"]
    lines += ["", "※ 정책은 바뀔 수 있습니다. 최종 확인은 유튜브 고객센터(수익 창출 정책, 합성 콘텐츠 공개)에서 하세요."]
    return "\n".join(lines) + "\n"
