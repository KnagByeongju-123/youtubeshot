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
