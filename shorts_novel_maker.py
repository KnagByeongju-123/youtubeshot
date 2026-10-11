# -*- coding: utf-8 -*-
"""
쇼츠 스크롤 영상 메이커 PRO (허구 소설 · 기이한 실화 · 과학 사실 · 자연현상)
AI: PC에 설치된 Claude Code(claude -p)를 Max 구독으로 사용 (API 키 불필요)
설치: pip install pillow numpy imageio-ffmpeg
기능: AI 대본(3안 심사·웹 조사), 근거 사진(복붙·AI 검색), 자체 합성 배경음, 연속 제작
실행: python shorts_novel_maker.py
"""
import os, re, io, json, time, queue, shutil, difflib, tempfile, threading, subprocess, math
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, colorchooser, simpledialog
from tkinter.scrolledtext import ScrolledText
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageTk, ImageFilter

W, H = 1080, 1920
BASE = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE, "shorts_novel_config.json")
PREVIEW_W, PREVIEW_H = 360, 640


def find_font(bold=False):
    cands = ([r"C:\Windows\Fonts\malgunbd.ttf", "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf",
              "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"] if bold else []) + [
        r"C:\Windows\Fonts\malgun.ttf", "/System/Library/Fonts/AppleSDGothicNeo.ttc",
        "/usr/share/fonts/truetype/nanum/NanumGothic.ttf", "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"]
    for p in cands:
        if os.path.exists(p):
            return p
    return ""


# 자체 합성 배경음 스타일 (아래 SOUND_STYLES 와 이름이 같아야 함)
SOUND_STYLE_NAMES = ["잔잔한 패드", "슬픈 패드", "감성 오르골", "밝은 오르골", "긴장 펄스", "어두운 드론",
                     "공포 심장박동", "비 오는 밤", "빗소리", "심해", "우주", "바람", "파도"]

# 소재별 자동 배경음
SOUND_BY_TOPIC = {
    "소름 반전": "어두운 드론", "사이다 참교육": "긴장 펄스", "감동 가족사연": "감성 오르골", "공포 괴담": "공포 심장박동",
    "설렘 로맨스": "밝은 오르골", "미스터리 추리": "긴장 펄스", "웃긴 일상썰": "밝은 오르골", "직장 썰": "긴장 펄스",
    "미제 사건": "어두운 드론", "기묘한 우연": "우주", "사라진 사람·배·비행기": "심해", "역사 속 기이한 일": "슬픈 패드",
    "생존 실화": "바람", "세계의 기이한 장소": "바람",
    "우주": "우주", "인체": "잔잔한 패드", "동물·생물": "밝은 오르골", "물리·화학": "잔잔한 패드", "심리·뇌": "긴장 펄스",
    "지구·환경": "바람",
    "기상 현상": "비 오는 밤", "지질·화산·지진": "어두운 드론", "바다": "심해", "하늘·빛": "우주", "동식물의 기이한 행동": "밝은 오르골",
}

# (탭, 키, 라벨, 타입, 기본값)
FIELDS = [
    ("글자", "font_path", "본문 글꼴", "font", find_font()),
    ("글자", "title_font_path", "제목 글꼴(굵게)", "font", find_font(True)),
    ("글자", "font_size", "본문 크기", "int", 56),
    ("글자", "title_size", "제목 크기", "int", 80),
    ("글자", "line_gap", "줄 간격(배)", "float", 1.65),
    ("글자", "para_gap", "문단 간격(배)", "float", 1.0),
    ("글자", "margin_x", "왼쪽 여백", "int", 90),
    ("글자", "margin_right", "오른쪽 여백(쇼츠 버튼 영역)", "int", 150),
    ("글자", "align", "정렬", "choice:left,center", "left"),
    ("글자", "text_color", "글자색", "color", "#F5F5F5"),
    ("글자", "title_color", "제목색", "color", "#FFD54F"),
    ("글자", "accent_color", "강조색(진행바·따옴표 대사)", "color", "#FF6B6B"),
    ("글자", "quote_color", "대사(따옴표) 색", "choice:on,off", "on"),
    ("글자", "shadow", "글자 그림자", "choice:on,off", "on"),
    ("글자", "stroke_width", "글자 테두리", "int", 0),
    ("배경", "bg_mode", "배경 종류", "choice:단색,그라데이션,이미지", "그라데이션"),
    ("배경", "bg_color", "배경색(위)", "color", "#0B0F1A"),
    ("배경", "bg_color2", "배경색(아래)", "color", "#1A1030"),
    ("배경", "bg_image", "배경 이미지", "image", ""),
    ("배경", "bg_dim", "이미지 어둡게(0~1)", "float", 0.55),
    ("배경", "bg_blur", "이미지 흐림(px)", "int", 6),
    ("배경", "ken_burns", "이미지 천천히 확대", "choice:on,off", "on"),
    ("배경", "vignette", "가장자리 어둡게", "float", 0.45),
    ("배경", "grain", "필름 노이즈(0~1)", "float", 0.06),
    ("효과", "fade", "위아래 흐림", "choice:on,off", "on"),
    ("효과", "focus", "읽는 줄 강조", "choice:on,off", "on"),
    ("효과", "focus_dim", "나머지 줄 밝기(0~1)", "float", 0.45),
    ("효과", "focus_y", "강조 위치(화면 비율)", "float", 0.42),
    ("효과", "progress_bar", "진행바", "choice:on,off", "on"),
    ("효과", "ease", "부드러운 시작/끝", "choice:on,off", "on"),
    ("효과", "intro_sec", "제목 카드(초, 0=없음)", "float", 1.8),
    ("효과", "outro_sec", "마무리 문구(초, 0=없음)", "float", 2.5),
    ("효과", "outro_text", "마무리 문구", "str", "구독하면 다음 이야기가 이어집니다"),
    ("효과", "safe_guide", "미리보기에 안전영역 표시", "choice:on,off", "off"),
    ("영상", "speed", "스크롤 속도(px/초)", "float", 70),
    ("영상", "target_sec", "목표 길이(초, 0=속도사용)", "float", 0),
    ("영상", "hold_start", "시작 정지(초)", "float", 1.5),
    ("영상", "hold_end", "끝 정지(초)", "float", 3.0),
    ("영상", "fps", "FPS(60=부드러움, 30=빠른 제작)", "int", 60),
    ("영상", "quality", "화질(crf, 낮을수록 좋음)", "int", 18),
    ("영상", "out_dir", "저장 폴더", "dir", os.path.join(BASE, "output")),
    ("소리", "bgm_mode", "배경음", "choice:자동생성,파일,없음", "자동생성"),
    ("소리", "bgm_style", "배경음 스타일", "choice:" + ",".join(["자동(소재별)"] + SOUND_STYLE_NAMES), "자동(소재별)"),
    ("소리", "bgm_volume", "배경음 볼륨(0~2)", "float", 0.5),
    ("소리", "reveal_hit", "반전 효과음(쿵)", "choice:on,off", "on"),
    ("소리", "hit_volume", "효과음 볼륨(0~2)", "float", 0.8),
    ("소리", "bgm_seed", "배경음 번호(0=만들 때마다 새로)", "int", 0),
    ("소리", "bgm_path", "음악 파일(파일 모드)", "audio", ""),
]
FTYPE = {k: t for _, k, _, t, _ in FIELDS}
LABEL = {k: l for _, k, l, _, _ in FIELDS}
DEFAULTS = {k: v for _, k, _, _, v in FIELDS}
FILE_KEYS = {"font_path", "title_font_path", "bg_image", "bgm_path", "out_dir", "safe_guide"}

# 테마 프리셋 (장르에 맞는 색·분위기)
THEMES = {
    "시네마 다크": dict(bg_mode="그라데이션", bg_color="#0B0F1A", bg_color2="#1A1030", text_color="#F5F5F5",
                    title_color="#FFD54F", accent_color="#FF6B6B", vignette=0.45, grain=0.06),
    "공포 레드": dict(bg_mode="그라데이션", bg_color="#000000", bg_color2="#2A0000", text_color="#E8E0E0",
                  title_color="#FF3B3B", accent_color="#FF3B3B", vignette=0.7, grain=0.12),
    "감동 웜톤": dict(bg_mode="그라데이션", bg_color="#2B1D14", bg_color2="#4A2E1C", text_color="#FFF3E0",
                  title_color="#FFB74D", accent_color="#FFAB91", vignette=0.4, grain=0.04),
    "종이 노트": dict(bg_mode="그라데이션", bg_color="#F6F1E7", bg_color2="#EDE3D1", text_color="#2B2B2B",
                  title_color="#8B2E2E", accent_color="#C0392B", vignette=0.25, grain=0.05, shadow="off"),
    "네온 시티": dict(bg_mode="그라데이션", bg_color="#05030F", bg_color2="#120A2E", text_color="#E0F7FF",
                  title_color="#00E5FF", accent_color="#FF2BD6", vignette=0.5, grain=0.08),
    "로맨스 핑크": dict(bg_mode="그라데이션", bg_color="#2A0F1E", bg_color2="#4A1A35", text_color="#FFF0F5",
                    title_color="#FF8FB1", accent_color="#FFB3C6", vignette=0.4, grain=0.04),
}

SAMPLE_TITLE = "마지막 버스"
SAMPLE_STORY = """밤 11시 58분, 정류장에는 나 혼자였다.

막차는 이미 끊겼다고 했다.
그런데 저 멀리, 불 켜진 버스 한 대가 다가왔다.

문이 열리자 기사님이 웃으며 말했다.
"오늘 하루 고생 많았죠? 타요, 집까지 데려다줄게요."

다음 날 알았다.
그 노선은 10년 전에 없어졌다는 걸."""

# 쇼츠에서 잘 되는 장르별 공식 + 어울리는 테마
GENRES = {
    "소름 반전": ("평범한 일상처럼 흘러가다 마지막 1~2줄에서 앞의 모든 장면이 다르게 보이는 반전. 복선은 앞에 자연스럽게 숨긴다.", "시네마 다크"),
    "사이다 참교육": ("무례한 사람(진상 손님, 갑질 상사, 얌체 친척 등)에게 당하다가 통쾌하게 되갚는 이야기. 답답함→역전→속 시원한 마무리.", "네온 시티"),
    "감동 가족사연": ("엄마, 아빠, 할머니, 자식 사이의 오해나 몰랐던 희생이 드러나 울컥하는 이야기. 마지막 한 줄에 감정을 터뜨린다.", "감동 웜톤"),
    "공포 괴담": ("실화처럼 1인칭으로, 장소·시간을 구체적으로. 조용히 이상한 점이 쌓이다가 마지막 줄에서 오싹하게 끝낸다. 잔인한 묘사는 하지 않는다.", "공포 레드"),
    "설렘 로맨스": ("짧은 순간의 설렘, 짝사랑, 오래된 인연. 대사 위주로 가볍게, 마지막에 심쿵 포인트.", "로맨스 핑크"),
    "미스터리 추리": ("작은 단서들을 앞에 흘리고, 마지막에 '그래서 그랬구나' 하고 맞춰지는 구조.", "시네마 다크"),
    "웃긴 일상썰": ("회사, 학교, 가족 사이의 황당한 실수나 오해. 짧은 문장으로 빠르게 치고 빠지는 웃음, 마지막에 한 번 더 빵 터뜨린다.", "종이 노트"),
    "직장 썰": ("회사 생활의 공감 가는 상황(신입, 팀장, 회식, 퇴사)에서 생긴 반전이나 사이다.", "네온 시티"),
}

# 콘텐츠 종류: 이름 -> (사실 기반 여부, 소재 목록{소재: (공식, 테마)})
KEEP_PHOTO_RULE = ("본문에 '[사진1]' 같은 자리표시 줄이 있으면 지우거나 고치지 말고 한 줄 그대로 둔다(위치는 알맞게 옮겨도 됨). "
                   "자리표시가 없으면 새로 만들지 않는다.")

CATEGORIES = {
    "허구 단편소설": (False, GENRES),
    "기이한 실화": (True, {
        "미제 사건": ("실제로 있었던 풀리지 않은 사건. 날짜·장소·관련자 수 등 확인된 사실만. 마지막에 '아직도 밝혀지지 않았다'로 여운.", "시네마 다크"),
        "기묘한 우연": ("통계적으로 믿기 힘든 실제 우연의 일치. 사건을 순서대로 쌓고 마지막에 가장 놀라운 우연을 터뜨린다.", "네온 시티"),
        "사라진 사람·배·비행기": ("실종 실화. 마지막으로 확인된 순간을 구체적으로, 남은 단서를 보여주고 끝.", "공포 레드"),
        "역사 속 기이한 일": ("교과서에 안 나오는 실제 역사 일화. 당시 상황→이상한 사건→기록으로 확인된 결말.", "감동 웜톤"),
        "생존 실화": ("극한 상황에서 살아남은 실제 사람. 숫자(일수, 온도, 거리)로 긴장감을 만들고 생환 순간으로 마무리.", "시네마 다크"),
        "세계의 기이한 장소": ("실제로 존재하는 이상한 장소. 위치, 특징, 과학적 설명 또는 미스터리를 순서대로.", "네온 시티"),
    }),
    "과학 사실": (True, {
        "우주": ("태양계·별·블랙홀 등 검증된 천문학 사실. 크기와 시간을 일상 비유로 바꿔 체감되게.", "네온 시티"),
        "인체": ("몸에 대한 놀라운 사실. '당신의 몸은 지금도…' 식으로 시청자 자신과 연결.", "감동 웜톤"),
        "동물·생물": ("동물의 놀라운 능력이나 습성. 하나의 동물에 집중해서 깊게.", "감동 웜톤"),
        "물리·화학": ("일상 속 현상의 과학 원리. '왜?'로 시작해서 원리를 쉬운 비유로 설명.", "시네마 다크"),
        "심리·뇌": ("실험으로 확인된 심리 효과. 실험 상황→결과→시청자에게 적용되는 한 줄.", "로맨스 핑크"),
        "지구·환경": ("지구 규모의 사실(판, 대기, 바다). 숫자를 비유로.", "시네마 다크"),
    }),
    "자연현상": (True, {
        "기상 현상": ("번개, 오로라, 토네이도 등. 목격한 사람 시점으로 장면을 보여주고 원리를 설명.", "네온 시티"),
        "지질·화산·지진": ("실제 사례(연도·장소)로 시작해 지구 내부 원리로 연결.", "공포 레드"),
        "바다": ("심해, 조류, 해양 생물 발광 등 바다의 기이한 현상.", "시네마 다크"),
        "하늘·빛": ("환일, 무지개, 녹색 섬광, 유성우 같은 빛의 현상과 그 원리.", "네온 시티"),
        "동식물의 기이한 행동": ("집단 이동, 대량 발생, 공생 등 실제 기록된 현상.", "감동 웜톤"),
    }),
}

FACT_RULES = """[사실 기반 콘텐츠 규칙 - 반드시 지킬 것]
- 널리 기록되고 검증된 사실만 쓴다. 확실하지 않은 숫자·이름·날짜는 쓰지 말고 '약', '수십' 처럼 범위로 쓴다.
- 지어내거나 과장하지 않는다. 논란이 있는 주장은 '~라는 설이 있다'로 구분한다.
- 연도, 장소, 사람 수, 크기 같은 구체적 정보가 신뢰감을 만든다. 단, 확신하는 것만.
- 괴담·도시전설을 실화처럼 쓰지 않는다. 실화와 전설이 섞이면 "전해지는 이야기로는"으로 구분.
- 구조: 첫 줄 훅(가장 놀라운 사실 or 장면) → 상황을 순서대로 → 중반에 '그런데 더 이상한 건' 반전 정보 → 마지막 줄은 여운(질문, 남은 미스터리, 소름 포인트)
- 마지막에 댓글을 부르는 짧은 질문 1줄 (예: "당신이라면 어떻게 했을까?")
- sources 에는 이 내용이 실린 대표 출처(기관, 논문, 유명 매체, 백과사전 항목명)를 2~4개 적는다. URL은 적지 않는다.
- confidence 는 전체 내용의 확신도(high/medium/low), notes 에는 확인이 필요한 부분을 적는다."""

FACT_SYSTEM = """너는 한국 유튜브 쇼츠에서 조회수 잘 나오는 '기이한 실화·과학·자연현상' 채널의 전문 작가다.
영상은 글이 위로 천천히 스크롤되는 형식이고, 시청자는 소리 없이 글만 읽는다.
문체는 1~2문장 짧은 문단, 쉬운 단어, 문단 사이 빈 줄. 한 줄 40자 이내. 제목은 15자 이내로 궁금하게.

{FACT_RULES}

반드시 JSON만 출력: {"title": "제목", "story": "본문", "sources": ["출처1", "출처2"], "confidence": "high", "notes": "확인 필요한 부분(없으면 빈 문자열)"}"""
FACT_SYSTEM = FACT_SYSTEM.replace("{FACT_RULES}", FACT_RULES)

FACT_MULTI_SYSTEM = FACT_SYSTEM.replace(
    "반드시 JSON만 출력:", "같은 소재로 서로 다른 접근(훅 방식, 강조하는 사실, 전개 순서)의 초안 3개를 쓴다. 각 초안마다 sources/confidence/notes 포함.\n반드시 JSON만 출력: {{\"drafts\": [초안1, 초안2, 초안3]}} 각 초안 형식:")

VERIFY_SYSTEM = """너는 과학·역사 팩트체커다. 아래 쇼츠 대본의 모든 사실 주장(숫자, 날짜, 이름, 장소, 인과관계)을 하나씩 점검한다.
기준: 널리 검증된 사실=ok, 과장되거나 틀림=wrong, 논란·불확실=unsure
틀리거나 불확실한 부분은 어떻게 고쳐야 안전한지 구체적으로 쓴다. 고친 전체 본문(corrected_story)은 원래 분량과 재미를 유지하되 틀린 부분만 바로잡는다.
""" + KEEP_PHOTO_RULE + """ 자리표시 줄은 점검 대상이 아니다.
반드시 JSON만 출력: {"verdict": "safe/needs_fix/risky", "issues": [{"claim": "원문 구절", "status": "wrong/unsure", "fix": "어떻게 고칠지"}], "corrected_story": "고친 전체 본문(문제 없으면 빈 문자열)", "summary": "한 줄 총평"}"""

POPULAR_RULES = """[쇼츠 인기 공식 - 반드시 지킬 것]
1. 첫 줄(훅): 2초 안에 '어? 뭐지?' 하게 만든다. 아래 중 하나로 시작
   - 사건 한가운데서 시작 ("문을 열자, 엄마가 울고 있었다.")
   - 결과를 먼저 말하기 ("그날 이후 나는 그 엘리베이터를 타지 않는다.")
   - 궁금증 질문 ("10년 동안 우리 집 앞에 우유를 둔 사람은 누구였을까.")
   인사, 배경 설명, '안녕하세요'로 시작 금지.
2. 1인칭 썰체('~했다', '~였다'), 실제로 있었던 일처럼 구체적으로(시간, 장소, 물건).
3. 문장은 짧게, 문단은 1~2문장, 문단 사이 빈 줄. 한 줄이 너무 길면 화면에서 3줄 넘게 꺾이므로 40자 이내.
4. 2~3문단마다 새로운 사건이나 정보가 나와야 한다 (5~7초마다 전개).
5. 중반에 긴장감을 최고로 올리고, 마지막 1~2줄에서 반전/감동/사이다를 터뜨린다.
6. 마지막 줄은 첫 줄과 이어지게 해서 다시 처음부터 보고 싶게 만든다.
7. 쉬운 단어만. 설명보다 장면과 대사로 보여준다. 대사는 큰따옴표로.
8. 제목은 짧고 궁금하게(15자 이내), 결말은 제목에서 밝히지 않는다.
9. 실존 인물·기업 이름, 선정적이거나 잔인한 묘사 금지."""

STORY_SYSTEM = f"""너는 한국 유튜브 쇼츠에서 조회수 잘 나오는 '썰/단편소설' 전문 작가다.
영상은 글이 위로 천천히 스크롤되는 형식이고, 시청자는 소리 없이 글만 읽는다.

{POPULAR_RULES}

반드시 JSON만 출력: {{"title": "제목", "story": "본문"}}"""

MULTI_SYSTEM = f"""너는 한국 유튜브 쇼츠 '썰/단편소설' 전문 작가다. 글이 위로 스크롤되는 영상용이다.
같은 주제로 서로 다른 접근(훅 방식, 반전 방향, 분위기)의 초안 3개를 쓴다. 서로 비슷하면 안 된다.

{POPULAR_RULES}

반드시 JSON만 출력: {{"drafts": [{{"title": "제목", "story": "본문"}}, {{"title": "제목", "story": "본문"}}, {{"title": "제목", "story": "본문"}}]}}"""

PHOTO_RULES = """[사진 규칙]
- 우선순위: Wikimedia Commons(퍼블릭 도메인·CC 라이선스), NASA·NOAA·USGS·ESA 등 공공기관 공개 이미지
- url 은 이미지 파일 주소(.jpg/.jpeg/.png). 예: https://upload.wikimedia.org/... 또는 https://commons.wikimedia.org/wiki/File:파일이름.jpg
- 저작권이 불분명한 뉴스·블로그 사진, AI 생성 이미지, 워터마크 있는 사진은 쓰지 않는다
- 그 사건·현상·장소를 실제로 보여주는 사진만 고른다. 비슷한 다른 사진 금지. 직접 열어서(WebFetch) 맞는지 확인한다
- after: 사진이 들어갈 위치 = 본문에서 사진 바로 앞에 올 문장의 일부(원문 그대로 10~20자). 본문이 아직 없으면 그 사진이 보여주는 사실의 핵심 단어
- caption: 15자 이내 한국어 설명 / credit: "작가 또는 기관 / 라이선스" / page: 출처 페이지 URL"""

RESEARCH_SYSTEM = """너는 유튜브 쇼츠 대본을 위한 자료조사원이다. WebSearch 로 주제를 검색하고, 중요한 내용은 WebFetch 로 원문을 열어 확인한다.
주제가 비어 있으면 해당 소재에서 쇼츠로 반응이 좋을 실제 주제를 하나 골라서 조사한다.

[사실 기반(실화·과학·자연현상)일 때]
- 공식 기관·백과사전·주요 언론·논문 등 신뢰할 수 있는 자료를 우선한다. 여러 자료가 일치하는 내용만 facts 에 넣는다.
- facts: 대본에 쓸 핵심 사실 6~12개, 한 줄씩 (숫자·날짜·장소 포함, 확인된 것만)
- hook: 첫 줄로 쓸 가장 놀라운 포인트 / twist: 마지막에 터뜨릴 반전·여운 포인트
- sources: 실제로 확인한 자료 2~5개, "자료 이름 - URL" 형식
- photos: 아래 사진 규칙대로 1~3장 (못 찾으면 빈 배열)

[허구일 때]
- 요즘 사람들이 공감하거나 화제가 되는 상황·소재를 참고용으로 조사한다. 실제 사연을 그대로 베끼지 않는다. 실존 인물 금지.
- facts: 이야기 재료(상황, 공감 포인트, 생생한 디테일) 6~10개 / sources: 참고한 자료 / photos: 빈 배열

""" + PHOTO_RULES + """

반드시 JSON만 출력: {"topic": "조사한 주제", "facts": ["..."], "hook": "...", "twist": "...", "sources": ["이름 - URL"], "photos": [{"after": "...", "url": "...", "caption": "...", "credit": "...", "page": "..."}]}"""

PHOTO_SYSTEM = """너는 유튜브 쇼츠 사실 콘텐츠의 사진 자료조사원이다. WebSearch/WebFetch 로 아래 대본의 사실을 뒷받침하는 실제 사진을 1~3장 찾는다.
첫 문단(훅) 바로 뒤와 마지막 문단 뒤에는 넣지 않는다. 사진끼리 붙지 않게 떨어뜨린다.

""" + PHOTO_RULES + """

반드시 JSON만 출력: {"photos": [{"after": "...", "url": "...", "caption": "...", "credit": "...", "page": "..."}]}"""

WEB_VERIFY_BLOCK = """

[웹 검색 확인 모드] 의심스럽거나 중요한 숫자·날짜·이름은 WebSearch/WebFetch 로 직접 확인하고, issues 의 fix 에 확인한 자료(이름 - URL)를 적는다."""

JUDGE_SYSTEM = """너는 유튜브 쇼츠 썰 채널의 베테랑 편집장이다. 조회수와 끝까지 보는 비율(시청 지속률)을 기준으로 초안을 심사한다.
채점 항목(각 10점): 훅(첫 줄에서 멈추게 하는가), 전개(5~7초마다 새 정보가 있는가), 반전/결말(마지막 1~2줄의 충격·감동), 가독성(짧은 문장, 쉬운 단어), 공유욕구(댓글·공유하고 싶은가)
사실 기반 콘텐츠(실화·과학·자연현상)이면 '정확성'을 최우선으로 본다: 의심스럽거나 과장된 주장이 있는 초안은 크게 감점하고, polish 에서 그 부분을 안전하게 고친다.
반드시 JSON만 출력: {"best": 가장 좋은 초안 번호(0부터), "scores": [{"total": 합계, "reason": "한 줄 이유"}, ...], "polish": {"title": "최고 초안을 다듬은 제목", "story": "최고 초안을 다듬은 전체 본문", "sources": ["사실 기반일 때 출처"], "notes": "확인 필요한 부분"}}
polish는 선택된 초안의 약점만 손봐서 완성본을 만든다. 길이는 원본과 비슷하게.
""" + KEEP_PHOTO_RULE

REVIEW_SYSTEM = """너는 유튜브 쇼츠 썰 채널의 베테랑 편집장이다. 아래 소설을 쇼츠 기준으로 냉정하게 평가한다.
항목(각 10점): hook(첫 줄), pacing(전개 속도), ending(반전/결말), readability(가독성), share(공유욕구)
반드시 JSON만 출력: {"scores": {"hook": 0, "pacing": 0, "ending": 0, "readability": 0, "share": 0}, "total": 0~50, "grade": "S/A/B/C", "strengths": ["..."], "fixes": ["구체적인 수정 제안 (어느 줄을 어떻게)", "..."]}"""

PACKAGE_SYSTEM = """너는 유튜브 쇼츠 채널 운영 전문가다. 소설을 읽고 업로드에 필요한 문구를 만든다.
- 제목 후보 5개: 결말을 밝히지 않고 궁금하게, 25자 이내, 이모지 0~1개
- 설명: 2~3줄, 마지막 줄에 "다음 이야기는 구독하고 받아보세요" 류 문구
- 해시태그 8~12개: 허구면 #쇼츠 #썰 #단편소설, 실화·과학이면 #쇼츠 #실화 #미스터리 #과학 #상식 등 종류와 소재 포함, 띄어쓰기로 구분
- 고정댓글: 시청자에게 결말에 대한 의견을 묻는 한 줄 질문
반드시 JSON만 출력: {"titles": ["..."], "description": "...", "hashtags": "#... #...", "pinned_comment": "..."}"""

IDEA_SYSTEM = """너는 한국 유튜브 쇼츠 채널 기획자다. (허구 썰, 기이한 실화, 과학 사실, 자연현상 모두 다룬다)
조회수가 잘 나오는 소재(공감, 궁금증, 반전, 감동, 소름, 놀라움)를 골라
첫 줄 훅이 강하게 나올 수 있는 주제를 만든다. 사실 기반 종류이면 실제로 존재하고 널리 알려진 사건·현상·사실만 고른다 (지어내지 않는다).
각 주제는 25자 이내 한 줄로, 결말은 밝히지 않는다.
반드시 JSON만 출력: {"ideas": ["주제1", "주제2", ...]}"""


def cat_info(category):
    factual, topics = CATEGORIES.get(category, CATEGORIES["허구 단편소설"])
    return factual, topics


def systems_for(category):
    factual, _ = cat_info(category)
    return (FACT_SYSTEM, FACT_MULTI_SYSTEM) if factual else (STORY_SYSTEM, MULTI_SYSTEM)


def command_system():
    keys = "\n".join(f"- {k}: {LABEL[k]} ({FTYPE[k]})" for k in DEFAULTS if k not in FILE_KEYS)
    return f"""너는 유튜브 쇼츠 단편소설 스크롤 영상 편집 도우미다.
사용자 명령에 맞춰 제목, 본문, 화면/영상 설정을 고친다.
영상 크기는 1080x1920 세로 화면이다.
설정 키:
{keys}
테마 이름(theme 키로 지정 가능): {", ".join(THEMES)}
규칙:
- 색상은 #RRGGBB 형식
- 영상 길이를 맞추라는 명령은 target_sec 로 처리
- 본문을 고치면 story 에 '전체 본문'을 넣는다 (문단 사이 빈 줄)
- 본문을 고칠 때도 쇼츠 인기 공식을 지킨다: 첫 줄은 강한 훅, 짧은 문단, 2~3문단마다 새 전개, 마지막 1~2줄 반전/감동/사이다
- 사실 기반 콘텐츠(실화·과학·자연현상)이면 사실을 지어내거나 과장하지 않는다. 확실하지 않으면 범위 표현으로.
- {KEEP_PHOTO_RULE} 사용자가 사진 삭제를 요청한 경우에만 그 줄을 지운다.
- 바뀐 것만 넣는다
반드시 JSON만 출력:
{{"title": "바뀐 경우만", "story": "바뀐 경우만", "theme": "테마 바꿀 때만", "settings": {{"바뀐키": 값}}, "message": "무엇을 바꿨는지 한 줄"}}"""


def cast(key, v):
    t = FTYPE[key]
    try:
        if t == "int":
            return int(float(v))
        if t == "float":
            return float(v)
    except (TypeError, ValueError):
        return DEFAULTS[key]
    if t.startswith("choice:"):
        return v if v in t[7:].split(",") else DEFAULTS[key]
    if t == "color":
        v = str(v).strip()
        return v if re.fullmatch(r"#[0-9a-fA-F]{6}", v) else DEFAULTS[key]
    return str(v)


def hex_rgb(h):
    h = h.lstrip("#")
    return [int(h[i:i + 2], 16) for i in (0, 2, 4)]


def safe_name(s):
    s = re.sub(r'[\\/:*?"<>|\n\r\t]', "", s).strip()
    return s[:40] or "short_novel"


# ---------------- Claude (Claude Code CLI · Max 구독, API 키 사용 안 함) ----------------
CLAUDE_TIMEOUT = int(os.environ.get("CLAUDE_MAX_TIMEOUT", "300"))


def find_claude():
    explicit = os.environ.get("MES_CLAUDE_CLI", "").strip().strip('"')
    if explicit and os.path.exists(explicit):
        return explicit
    if os.name == "nt":
        for p in [os.path.expandvars(r"%USERPROFILE%\.local\bin\claude.exe"),
                  os.path.expandvars(r"%USERPROFILE%\.local\bin\claude.cmd"),
                  os.path.expandvars(r"%APPDATA%\npm\claude.cmd")]:
            if os.path.exists(p):
                return p
    return shutil.which("claude")


def safe_env():
    env = os.environ.copy()
    env.pop("ANTHROPIC_API_KEY", None)
    env.pop("CLAUDE_API_KEY", None)
    return env


def run_cli(args, input_text=None, timeout=CLAUDE_TIMEOUT):
    exe = find_claude()
    if not exe:
        raise RuntimeError("Claude Code가 설치되어 있지 않습니다.\n설치 후 터미널에서 claude 를 실행해 Max 계정으로 로그인하세요.")
    with tempfile.TemporaryDirectory(prefix="shorts_novel_") as work:
        try:
            return subprocess.run([exe] + args, input=input_text, cwd=work, env=safe_env(),
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                                  encoding="utf-8", errors="replace", timeout=timeout,
                                  creationflags=(subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0))
        except subprocess.TimeoutExpired:
            raise RuntimeError(f"Claude 응답 시간 초과({timeout}초). 다시 시도하세요.")
        except OSError as ex:
            raise RuntimeError(f"Claude Code 실행 불가: {ex}")


WEB_TOOLS = ["WebSearch", "WebFetch"]
WEB_TIMEOUT = int(os.environ.get("CLAUDE_WEB_TIMEOUT", "900"))


def ask_claude(model, system, user, tools=None, timeout=None):
    """tools=["WebSearch","WebFetch"] 이면 웹 검색 허용 (그 외 도구는 묻지 않고 거절)"""
    prompt = system + "\n\n" + user
    args = ["-p", "--output-format", "json"]
    if model:
        args += ["--model", model]
    if tools:
        args += ["--allowedTools"] + list(tools) + ["--permission-mode", "dontAsk"]
    p = run_cli(args, prompt, timeout or (WEB_TIMEOUT if tools else CLAUDE_TIMEOUT))
    raw = (p.stdout or "").strip()
    detail = (p.stderr or "").strip()
    text, rc = raw, p.returncode
    try:
        wrapper = json.loads(raw)
    except Exception:
        wrapper = None
    if isinstance(wrapper, dict) and "result" in wrapper:
        text = str(wrapper.get("result") or "")
        if wrapper.get("is_error"):
            detail = (text + " " + detail).strip()
            rc = rc or 1
    if rc != 0:
        detail = detail or raw
        low = detail.lower()
        if "limit" in low or "usage" in low:
            raise RuntimeError("Claude Max 사용량 한도에 도달했을 수 있습니다. 잠시 후 다시 시도하세요.\n" + detail[:300])
        if any(w in low for w in ("login", "auth", "oauth", "credential")):
            raise RuntimeError("Claude Code 로그인이 안 되어 있습니다. 터미널에서 claude 실행 후 로그인하세요.\n" + detail[:300])
        raise RuntimeError("Claude Code 오류: " + (detail[:1200] or f"exit code {rc}"))
    return text


def ask_json(model, system, user, tools=None, timeout=None):
    return parse_json(ask_claude(model, system, user, tools, timeout))


def check_claude():
    p = run_cli(["--version"], timeout=30)
    if p.returncode != 0:
        raise RuntimeError((p.stderr or p.stdout or "").strip()[:300])
    return (p.stdout or "").strip()


def parse_json(text):
    text = (text or "").strip()
    if not text:
        raise ValueError("Claude 응답이 비어 있습니다.")
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.I)
    text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text, strict=False)
    except Exception:
        pass
    dec = json.JSONDecoder(strict=False)
    found, i = [], text.find("{")
    while i >= 0:
        try:
            obj, end = dec.raw_decode(text, i)
            if isinstance(obj, dict):
                found.append((end - i, obj))
            i = text.find("{", end)
        except ValueError:
            i = text.find("{", i + 1)
    if found:
        return max(found, key=lambda f: f[0])[1]
    raise ValueError("AI 응답에서 JSON을 찾지 못했습니다:\n" + text[:300])


# ---------------- 근거 사진 ----------------
IMG_EXT = (".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif")
MEDIA_RE = re.compile(r"^\s*\[사진\s*:\s*(.+?)\]\s*$")
PH_RE = re.compile(r"^\s*[\[【(（]\s*(?:사진|이미지|그림|photo|image)\s*(\d+)\s*(?:[:：][^\]】)）]*)?[\]】)）]\s*$", re.I)
# 문장 속에 섞인 자리표시 (화면에는 절대 그리지 않음)
PH_INLINE_RE = re.compile(r"\s*(?:[\[【]\s*(?:사진|이미지|그림|photo|image)\s*\d*\s*(?:[:：][^\]】]*)?[\]】]"
                          r"|[(（]\s*(?:사진|이미지|그림|photo|image)\s*\d+\s*[)）])", re.I)


def strip_placeholders(text):
    """사진 줄([사진: 파일 | ...])은 그대로 두고, 남은 자리표시 글자만 지움"""
    out = []
    for line in (text or "").split("\n"):
        if parse_media(line):
            out.append(line)
            continue
        if PH_RE.match(line):
            continue
        out.append(PH_INLINE_RE.sub("", line).rstrip() if PH_INLINE_RE.search(line) else line)
    return re.sub(r"\n{3,}", "\n\n", "\n".join(out)).strip("\n")
UA = "ShortsNovelMaker/1.0 (personal YouTube Shorts tool)"


def parse_media(line):
    """'[사진: 경로 | 설명 | 출처 | 페이지]' → (경로, 설명, 출처, 페이지) 또는 None"""
    m = MEDIA_RE.match(line or "")
    if not m:
        return None
    parts = [x.strip() for x in m.group(1).split("|")] + ["", "", ""]
    return parts[0], parts[1], parts[2], parts[3]


def clean_field(x):
    return str(x or "").replace("|", "/").replace("]", ")").replace("\n", " ").strip()


def short_path(path):
    """프로그램 폴더 안이면 짧은 상대 경로로"""
    try:
        rel = os.path.relpath(path, BASE)
        return path if rel.startswith("..") else rel.replace("\\", "/")
    except ValueError:
        return path


def make_marker(path, cap="", credit="", page=""):
    return f"[사진: {short_path(path)} | {clean_field(cap)} | {clean_field(credit)} | {clean_field(page)}]"


def resolve_media(path):
    if os.path.isabs(path) and os.path.exists(path):
        return path
    q = os.path.join(BASE, path)
    return q if os.path.exists(q) else None


def load_media_image(path):
    q = resolve_media(path)
    if not q:
        return None
    try:
        im = Image.open(q)
        im.load()
        return im.convert("RGB")
    except Exception:
        return None


def save_media_image(im, media_dir, stem=None):
    os.makedirs(media_dir, exist_ok=True)
    stem = stem or time.strftime("photo_%Y%m%d_%H%M%S") + f"_{int(time.time() * 1000) % 1000:03d}"
    im = im.convert("RGB")
    im.thumbnail((1600, 1600))
    path = os.path.join(media_dir, stem + ".jpg")
    im.save(path, quality=90)
    return path


def fix_image_url(url):
    """Commons/위키 파일 페이지 주소 → 실제 이미지 주소"""
    url = url.strip()
    m = re.match(r"https?://(?:commons\.wikimedia\.org|[\w-]+\.wikipedia\.org)/wiki/(?:File|파일|Datei|Fichier):([^?#]+)", url)
    if m:
        return "https://commons.wikimedia.org/wiki/Special:FilePath/" + m.group(1) + "?width=1600"
    return url


def download_image(url, media_dir, stem=None):
    import urllib.request
    req = urllib.request.Request(fix_image_url(url), headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=40) as r:
        data = r.read(25 * 1024 * 1024 + 1)
    if len(data) > 25 * 1024 * 1024:
        raise ValueError("파일이 너무 큼")
    im = Image.open(io.BytesIO(data))
    im.load()
    if im.width < 200 or im.height < 150:
        raise ValueError("사진이 너무 작음")
    return save_media_image(im, media_dir, stem)


def fetch_photos(items, media_dir, log, limit=3):
    """AI가 찾은 사진 목록을 내려받음 → [{path, caption, credit, page, after}]"""
    got = []
    for it in items or []:
        if len(got) >= limit:
            break
        if not isinstance(it, dict) or not it.get("url"):
            continue
        try:
            path = download_image(str(it["url"]), media_dir)
            got.append({"path": path, "caption": it.get("caption", ""), "credit": it.get("credit", ""),
                        "page": it.get("page", ""), "after": it.get("after", "")})
            log(f"  사진 받음: {it.get('caption', '')} ({it.get('credit', '')})")
        except Exception as e:
            log(f"  사진 받기 실패: {str(it.get('url'))[:60]} ({str(e)[:40]})")
    return got


def split_paras(story):
    return [x.strip() for x in re.split(r"\n\s*\n", (story or "").strip()) if x.strip()]


def _bigram_score(key, text):
    k = re.sub(r"\s+", "", key)
    t = re.sub(r"\s+", "", text)
    if len(k) < 2:
        return 0.0
    grams = {k[i:i + 2] for i in range(len(k) - 1)}
    return sum(g in t for g in grams) / len(grams)


def insert_photo_near(paras, marker, after):
    """after 문장과 가장 비슷한 문단 뒤에 사진 줄 삽입 (훅 뒤·마지막 문단 뒤는 피함)"""
    text_idx = [i for i, p in enumerate(paras) if not parse_media(p) and not PH_RE.match(p)]
    best, best_i = 0.0, None
    for i in text_idx:
        sc = _bigram_score(after, paras[i]) if after else 0
        if sc > best:
            best, best_i = sc, i
    idx = best_i if best >= 0.35 else (text_idx[len(text_idx) // 2] if text_idx else len(paras) - 1)
    if len(paras) >= 3:
        idx = min(max(idx, 1), len(paras) - 2)
    while idx + 1 < len(paras) and parse_media(paras[idx + 1]):  # 사진끼리 붙지 않게
        idx += 1
    paras.insert(idx + 1, marker)
    return paras


def _split_inline_ph(text):
    """'문장 [사진1] 문장' → 자리표시를 별도 줄로 떼어냄"""
    pat = re.compile(r"([\[【(（]\s*(?:사진|이미지|그림|photo|image)\s*\d+\s*(?:[:：][^\]】)）]*)?[\]】)）])", re.I)
    out = []
    for line in (text or "").split("\n"):
        if parse_media(line) or PH_RE.match(line) or not pat.search(line):
            out.append(line)
            continue
        for part in pat.split(line):
            if part.strip():
                out += ["", part.strip(), ""] if PH_RE.match(part) else [part.strip()]
    return "\n".join(out)


def place_photos(story, photos):
    """본문의 [사진N] 자리표시를 실제 사진 줄로 바꾸고, 자리표시가 없는 사진은 알맞은 곳에 끼움"""
    paras = split_paras(_split_inline_ph(story))
    used = set()
    for i, p in enumerate(paras):
        m = PH_RE.match(p)
        if m:
            k = int(m.group(1)) - 1
            if 0 <= k < len(photos) and k not in used:
                ph = photos[k]
                paras[i] = make_marker(ph["path"], ph.get("caption"), ph.get("credit"), ph.get("page"))
                used.add(k)
            else:
                paras[i] = ""
    paras = [p for p in paras if p]
    for k, ph in enumerate(photos):
        if k not in used:
            paras = insert_photo_near(paras, make_marker(ph["path"], ph.get("caption"), ph.get("credit"), ph.get("page")), ph.get("after", ""))
    return strip_placeholders("\n\n".join(paras))


def to_placeholders(story):
    """AI에게 보낼 때 사진 줄을 [사진1] 자리표시로 바꿈 (경로 숨김)"""
    mapping, out = {}, []
    for line in (story or "").split("\n"):
        if parse_media(line):
            n = len(mapping) + 1
            mapping[n] = line.strip()
            out.append(f"[사진{n}]")
        else:
            out.append(line)
    return "\n".join(out), mapping


def from_placeholders(text, mapping):
    """AI 결과의 [사진N] 을 원래 사진 줄로 되돌림 (빠진 사진은 다시 끼움)"""
    used, out = set(), []
    for line in _split_inline_ph(text).split("\n"):
        m = PH_RE.match(line)
        if m:
            n = int(m.group(1))
            if n in mapping and n not in used:
                out.append(mapping[n])
                used.add(n)
            continue
        out.append(line)
    paras = split_paras("\n".join(out))
    for n, mk in mapping.items():
        if n not in used:
            paras = insert_photo_near(paras, mk, "")
    return strip_placeholders("\n\n".join(paras))


def story_text_only(story):
    return "\n".join(l for l in (story or "").split("\n") if not parse_media(l))


def photo_credits(story):
    res = []
    for l in (story or "").split("\n"):
        m = parse_media(l)
        if m:
            res.append(f"- {m[1] or os.path.basename(m[0])}: {m[2] or '출처 미기재'}" + (f" ({m[3]})" if m[3] else ""))
    return res


# ---------------- 렌더링 ----------------
def load_font(path, size):
    for p in (path, find_font()):
        try:
            return ImageFont.truetype(p, size)
        except Exception:
            continue
    return ImageFont.load_default(size)


def wrap(text, font, maxw):
    lines, cur = [], ""
    for ch in text:
        t = cur + ch
        if font.getlength(t) <= maxw or not cur:
            cur = t
            continue
        if ch == " ":
            lines.append(cur)
            cur = ""
            continue
        sp = cur.rfind(" ")
        if sp > 0:
            lines.append(cur[:sp])
            cur = cur[sp + 1:] + ch
        else:
            lines.append(cur)
            cur = ch
    if cur:
        lines.append(cur)
    return lines


def draw_text(d, xy, txt, font, fill, s, stroke=None):
    sw = max(0, s["stroke_width"]) if stroke is None else stroke
    if s["shadow"] == "on":
        off = max(2, font.size // 18)
        d.text((xy[0] + off, xy[1] + off), txt, font=font, fill=(0, 0, 0, 150), stroke_width=sw, stroke_fill=(0, 0, 0, 150))
    d.text(xy, txt, font=font, fill=fill, stroke_width=sw, stroke_fill="#000000")


def build_text_layer(title, story, s):
    fb = load_font(s["font_path"], s["font_size"])
    ft = load_font(s["title_font_path"] or s["font_path"], s["title_size"])
    maxw = W - s["margin_x"] - s["margin_right"]
    items = []
    y = int(H * 0.30)
    if title.strip():
        for ln in wrap(title.strip(), ft, maxw):
            items.append((y, ln, ft, s["title_color"], "center"))
            y += int(s["title_size"] * 1.35)
        y += int(s["title_size"] * 0.8)
    lh = int(s["font_size"] * s["line_gap"])
    paras, photos = [], []
    fcap = load_font(s["font_path"], max(18, int(s["font_size"] * 0.6)))
    fcred = load_font(s["font_path"], max(14, int(s["font_size"] * 0.44)))
    tc = hex_rgb(s["text_color"])
    for para in story.replace("\r", "").split("\n"):
        para = para.strip()
        if not para:
            continue
        med = parse_media(para)
        if med:
            path, cap, credit, _ = med
            y += int(s["font_size"] * 0.3)
            im = load_media_image(path)
            if im is None:
                ph_h = int(H * 0.18)
                photos.append((s["margin_x"], y, None, maxw, ph_h))
                items.append((y + ph_h // 2 - fcap.size // 2, "사진을 찾을 수 없음: " + os.path.basename(path)[:24], fcap, s["accent_color"], "center"))
                y += ph_h
            else:
                sc = min(maxw / im.width, H * 0.36 / im.height)
                iw, ih = max(1, int(im.width * sc)), max(1, int(im.height * sc))
                photos.append((s["margin_x"] + (maxw - iw) // 2, y, im.resize((iw, ih), Image.LANCZOS), iw, ih))
                y += ih
            y += int(fcap.size * 0.5)
            if cap:
                for ln in wrap(cap, fcap, maxw):
                    items.append((y, ln, fcap, tuple(tc) + (230,), "center"))
                    y += int(fcap.size * 1.35)
            if credit:
                for ln in wrap("출처: " + credit, fcred, maxw):
                    items.append((y, ln, fcred, tuple(tc) + (150,), "center"))
                    y += int(fcred.size * 1.35)
            y += int(s["font_size"] * s["para_gap"])
            continue
        if PH_RE.match(para):
            continue
        para = PH_INLINE_RE.sub("", para).strip()
        if not para:
            continue
        paras.append((y, para))
        is_quote = s["quote_color"] == "on" and para[:1] in "\"“'‘"
        col = s["accent_color"] if is_quote else s["text_color"]
        for ln in wrap(para, fb, maxw):
            items.append((y, ln, fb, col, s["align"]))
            y += lh
        y += int(s["font_size"] * s["para_gap"])
    # 마지막 문단이 '읽는 줄'에 멈추도록 아래 여백 계산
    if s["focus"] == "on":
        pad = int(H * (1 - s["focus_y"]) - lh / 2 - s["font_size"] * s["para_gap"])
    else:
        pad = int(H * 0.45)
    img_h = max(H, y + max(int(H * 0.2), pad))
    layer = Image.new("RGBA", (W, img_h), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    rad = 22
    for px, py, im, iw, ih in photos:
        if im is None:
            d.rounded_rectangle([px, py, px + iw, py + ih], radius=rad, outline=tuple(hex_rgb(s["accent_color"])) + (160,), width=3)
            continue
        mask = Image.new("L", (iw, ih), 0)
        ImageDraw.Draw(mask).rounded_rectangle([0, 0, iw - 1, ih - 1], radius=rad, fill=255)
        layer.paste(im.convert("RGBA"), (px, py), mask)
        d.rounded_rectangle([px, py, px + iw - 1, py + ih - 1], radius=rad, outline=(255, 255, 255, 70), width=2)
    for yy, ln, f, col, al in items:
        x = s["margin_x"] if al == "left" else s["margin_x"] + (maxw - f.getlength(ln)) / 2
        draw_text(d, (x, yy), ln, f, col, s)
    arr = np.array(layer)
    return arr[..., :3].astype(np.float32), arr[..., 3].astype(np.float32) / 255.0, paras


def build_card(lines, font, color, s, y_center):
    """제목 카드 / 마무리 문구용 작은 레이어 (화면 크기)"""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    maxw = W - s["margin_x"] - s["margin_right"]
    wrapped = [w for ln in lines for w in wrap(ln, font, maxw)]
    lh = int(font.size * 1.4)
    y = int(y_center - lh * len(wrapped) / 2)
    for ln in wrapped:
        x = (W - font.getlength(ln)) / 2
        draw_text(d, (x, y), ln, font, color, s)
        y += lh
    arr = np.array(layer)
    return arr[..., :3].astype(np.float32), arr[..., 3].astype(np.float32) / 255.0


class Background:
    def __init__(self, s, duration):
        self.s, self.duration = s, duration
        self.big = None
        mode = s["bg_mode"]
        p = s["bg_image"]
        if mode == "이미지" and p and os.path.exists(p):
            im = Image.open(p).convert("RGB")
            if s["bg_blur"] > 0:
                im = im.filter(ImageFilter.GaussianBlur(s["bg_blur"]))
            self.zoom = 1.12 if s["ken_burns"] == "on" else 1.0
            bw, bh = int(W * self.zoom), int(H * self.zoom)
            sc = max(bw / im.width, bh / im.height)
            im = im.resize((int(im.width * sc + 1), int(im.height * sc + 1)), Image.LANCZOS)
            l, t = (im.width - bw) // 2, (im.height - bh) // 2
            self.big = im.crop((l, t, l + bw, t + bh))
            self.dim = 1 - min(max(s["bg_dim"], 0), 1)
            self.static = None if self.zoom > 1 else np.asarray(self.big).astype(np.float32) * self.dim
        elif mode == "그라데이션":
            c1, c2 = np.array(hex_rgb(s["bg_color"]), np.float32), np.array(hex_rgb(s["bg_color2"]), np.float32)
            t = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
            self.static = np.broadcast_to(c1 + (c2 - c1) * t, (H, W, 3)).copy()
        else:
            self.static = np.full((H, W, 3), hex_rgb(s["bg_color"]), np.float32)
        # 비네트
        v = min(max(s["vignette"], 0), 1)
        if v > 0:
            yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
            r = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2) / 1.42
            self.vig = (1 - v * np.clip(r, 0, 1) ** 2)[..., None]
        else:
            self.vig = None
        self.grain = min(max(s["grain"], 0), 1)
        rng = np.random.default_rng(7)
        # 노이즈는 미리 전체 크기로 만들어 둠 (프레임마다 계산하지 않음)
        self.noise_bank = []
        if self.grain > 0:
            for _ in range(6):
                n = rng.normal(0, 1, (H // 4, W // 4)).astype(np.float32)
                self.noise_bank.append(np.repeat(np.repeat(n, 4, 0), 4, 1)[:H, :W, None] * (self.grain * 40))
        # 고정 배경이면 비네트까지 미리 곱해 둠
        if self.static is not None and self.vig is not None:
            self.static = self.static * self.vig
        self.static_cache = {}

    def frame(self, t):
        if self.static is not None:
            if self.noise_bank:
                k = int(t * 12) % len(self.noise_bank)
                if k not in self.static_cache:
                    self.static_cache[k] = self.static + self.noise_bank[k]
                return self.static_cache[k]
            return self.static
        bg = np.asarray(self._zoomed(t, W, H)).astype(np.float32) * self.dim
        if self.vig is not None:
            bg = bg * self.vig
        if self.noise_bank:
            bg = bg + self.noise_bank[int(t * 12) % len(self.noise_bank)]
        return bg

    def _zoomed(self, t, w, h):
        """천천히 확대 - 소수점 단위로 잘라서 확대가 끊기지 않게"""
        z = 1 + (self.zoom - 1) * smoothstep(t / max(0.1, self.duration))
        cw, ch = W * self.zoom / z, H * self.zoom / z
        l, tp = (self.big.width - cw) / 2, (self.big.height - ch) / 2
        return self.big.transform((w, h), Image.EXTENT, (l, tp, l + cw, tp + ch), Image.BILINEAR)

    def frame_small(self, t, w, h):
        """미리보기용 작은 배경 (빠름)"""
        if self.static is not None:
            if getattr(self, "_static_small", None) is None:
                self._static_small = np.asarray(Image.fromarray(np.clip(self.static, 0, 255).astype(np.uint8))
                                                .resize((w, h), Image.BILINEAR)).astype(np.float32)
            return self._static_small
        bg = np.asarray(self._zoomed(t, w, h)).astype(np.float32) * self.dim
        if self.vig is not None:
            if getattr(self, "_vig_small", None) is None:
                self._vig_small = np.asarray(Image.fromarray((self.vig[..., 0] * 255).astype(np.uint8))
                                             .resize((w, h), Image.BILINEAR)).astype(np.float32)[..., None] / 255
            bg = bg * self._vig_small
        return bg


def smoothstep(x):
    x = min(1, max(0, x))
    return x * x * (3 - 2 * x)


from concurrent.futures import ThreadPoolExecutor
N_WORKERS = max(1, min(8, (os.cpu_count() or 2)))
_POOL = ThreadPoolExecutor(max_workers=N_WORKERS) if N_WORKERS > 1 else None


def _ramp_area(u):
    """smoothstep 을 0~u 까지 적분한 값 (가속 구간 이동 거리 계산용)"""
    return u ** 3 - u ** 4 / 2


def _resize_f(arr, w, h):
    """float 배열(0~255 또는 0~1)을 작은 크기로 (미리보기용)"""
    if arr.ndim == 2:
        im = Image.fromarray(np.clip(arr * 255, 0, 255).astype(np.uint8))
        return np.asarray(im.resize((w, h), Image.BILINEAR)).astype(np.float32) / 255
    im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    return np.asarray(im.resize((w, h), Image.BILINEAR)).astype(np.float32)


class Renderer:
    """부드러운 스크롤:
    - 1픽셀보다 작은 단위로 위치를 계산해 두 줄 사이를 섞어 그림 (정수 픽셀로 끊기는 떨림 제거)
    - 속도가 0에서 서서히 올라갔다가 서서히 멈춤 (가속도가 끊기지 않는 곡선)
    - 글자는 '미리 곱한 알파'로 저장해서 섞을 때 가장자리가 번지지 않음"""

    def __init__(self, title, story, s):
        self.s = s
        self.title = title
        rgb, a, self.paras = build_text_layer(title, story, s)
        self.layer_h = rgb.shape[0]
        self.dist = self.layer_h - H
        pad = np.zeros((1, W), np.float32)
        self.a = np.concatenate([a, pad])                                   # 마지막에 투명 1줄 (보간용)
        self.prem = np.concatenate([rgb * a[..., None], pad[..., None].repeat(3, 2)])
        del rgb
        self.intro = s["intro_sec"] if title.strip() else 0
        self.hs, self.he = s["hold_start"], s["hold_end"]
        if s["target_sec"] > 0 and self.dist > 0:
            self.scroll_t = max(1.0, s["target_sec"] - self.intro - self.hs - self.he)
        else:
            self.scroll_t = self.dist / max(1.0, s["speed"])
        self.duration = self.intro + self.hs + self.scroll_t + self.he
        # 가속/감속 구간 (스크롤 시간의 15%, 최대 1.2초)
        self.ramp = min(1.2, self.scroll_t * 0.15) if s["ease"] == "on" else 0.0
        self.vmax = self.dist / max(1e-6, self.scroll_t - self.ramp) if self.dist > 0 else 0.0
        self.speed = self.vmax
        self.bg = Background(s, self.duration)
        # 화면 고정 마스크 (위아래 흐림 + 읽는 줄 강조)
        m = np.ones(H, np.float32)
        if s["fade"] == "on":
            n = 260
            r = np.linspace(0, 1, n, dtype=np.float32) ** 1.5
            m[:n] *= r
            m[-n:] *= r[::-1]
        if s["focus"] == "on":
            yy = np.arange(H, dtype=np.float32)
            fy, width = H * s["focus_y"], H * 0.16
            g = np.exp(-((yy - fy) / width) ** 2)
            dim = min(max(s["focus_dim"], 0), 1)
            m *= dim + (1 - dim) * g
        self.mask = m
        # 제목 카드 / 마무리 문구
        ft = load_font(s["title_font_path"] or s["font_path"], int(s["title_size"] * 1.15))
        self.card = build_card([title.strip()], ft, s["title_color"], s, H * 0.46) if self.intro > 0 else None
        self.outro = s["outro_sec"] if s["outro_text"].strip() else 0
        fo = load_font(s["font_path"], int(s["font_size"] * 0.85))
        self.outro_layer = build_card([s["outro_text"].strip()], fo, s["accent_color"], s, H * 0.72) if self.outro > 0 else None
        self.accent = np.array(hex_rgb(s["accent_color"]), np.float32)
        self.L = {"w": W, "h": H, "k": 1.0, "prem": self.prem, "a": self.a,
                  "m2": self.mask[:, None], "m3": self.mask[:, None, None],
                  "card": self.card, "outro": self.outro_layer, "bg": self.bg.frame}
        self._small = None
        self.reveal_t = self.find_reveal()

    def find_reveal(self):
        """반전 문단(마지막 문단, 마지막이 질문이면 그 앞)이 읽는 줄에 닿는 시각"""
        if not self.paras or self.dist <= 0:
            return None
        idx = -2 if len(self.paras) >= 2 and self.paras[-1][1].rstrip().endswith("?") else -1
        py = self.paras[idx][0]
        line = H * (self.s["focus_y"] if self.s["focus"] == "on" else 0.55)
        for i in range(int(self.duration * 20)):
            t = i / 20
            if t >= self.intro and py - self.offset(t) <= line + 2:
                return t if t >= self.intro + 1.0 else None
        end = self.intro + self.hs + self.scroll_t  # 끝까지 못 닿으면 스크롤이 멈추는 순간
        return end if py - self.dist < H * 0.85 and end >= self.intro + 1.0 else None

    def offset(self, t):
        """t초일 때 스크롤 위치(px, 소수점). 속도: 0 → 서서히 최고속 → 일정 → 서서히 0"""
        t -= self.intro + self.hs
        if self.dist <= 0 or t <= 0:
            return 0.0
        T, r = self.scroll_t, self.ramp
        if t >= T:
            return float(self.dist)
        if r <= 0:
            return self.dist * t / T
        if t < r:
            return self.vmax * r * _ramp_area(t / r)
        if t > T - r:
            return self.dist - self.vmax * r * _ramp_area((T - t) / r)
        return self.vmax * (r / 2 + t - r)

    @staticmethod
    def _sample(prem, a, y, h):
        """소수점 위치 y 에서 h 줄을 잘라옴 (위아래 두 줄을 비율대로 섞음)"""
        y = max(0.0, min(float(y), prem.shape[0] - h - 1))
        y0 = int(y)
        f = np.float32(y - y0)
        if f < 0.002:
            return prem[y0:y0 + h], a[y0:y0 + h]
        g = np.float32(1) - f
        return prem[y0:y0 + h] * g + prem[y0 + 1:y0 + h + 1] * f, a[y0:y0 + h] * g + a[y0 + 1:y0 + h + 1] * f

    def _make_small(self):
        k = PREVIEW_W / W
        hs = max(PREVIEW_H + 1, int(round(self.layer_h * k)))
        prem = _resize_f(self.prem[:-1], PREVIEW_W, hs)
        a = _resize_f(self.a[:-1], PREVIEW_W, hs)
        prem = np.concatenate([prem, np.zeros((1, PREVIEW_W, 3), np.float32)])
        a = np.concatenate([a, np.zeros((1, PREVIEW_W), np.float32)])
        m = np.interp(np.linspace(0, H - 1, PREVIEW_H), np.arange(H), self.mask).astype(np.float32)
        card = (_resize_f(self.card[0], PREVIEW_W, PREVIEW_H), _resize_f(self.card[1], PREVIEW_W, PREVIEW_H)) if self.card else None
        outro = (_resize_f(self.outro_layer[0], PREVIEW_W, PREVIEW_H), _resize_f(self.outro_layer[1], PREVIEW_W, PREVIEW_H)) if self.outro_layer else None
        return {"w": PREVIEW_W, "h": PREVIEW_H, "k": (hs - 1) / max(1, self.layer_h - 1) if hs > 1 else k,
                "prem": prem, "a": a, "m2": m[:, None], "m3": m[:, None, None], "card": card, "outro": outro,
                "bg": lambda t: self.bg.frame_small(t, PREVIEW_W, PREVIEW_H)}

    def _rows(self, r0, r1, bg, prem, a, y0, f, m2, m3, out):
        """r0~r1 줄만 계산 (여러 CPU가 나눠서 처리)"""
        if f < 0.002:
            al = a[y0 + r0:y0 + r1] * m2[r0:r1]
            pc = prem[y0 + r0:y0 + r1] * m3[r0:r1]
        else:
            g = np.float32(1) - f
            al = a[y0 + r0:y0 + r1] * g
            al += a[y0 + r0 + 1:y0 + r1 + 1] * f
            al *= m2[r0:r1]
            pc = prem[y0 + r0:y0 + r1] * g
            pc += prem[y0 + r0 + 1:y0 + r1 + 1] * f
            pc *= m3[r0:r1]
        np.subtract(1, al, out=al)
        pc += bg[r0:r1] * al[..., None]
        np.clip(pc, 0, 255, out=pc)
        out[r0:r1] = pc

    def _compose(self, t, L):
        w, h = L["w"], L["h"]
        bg = L["bg"](t)
        out = np.empty((h, w, 3), np.uint8)
        if L["card"] is not None and t < self.intro:
            k = smoothstep(t / 0.5) * smoothstep((self.intro - t) / 0.5)
            al = (L["card"][1] * k)[..., None]
            out[:] = np.clip(bg + (L["card"][0] - bg) * al, 0, 255)
        else:
            prem, a = L["prem"], L["a"]
            y = max(0.0, min(self.offset(t) * L["k"], prem.shape[0] - h - 1))
            y0 = int(y)
            f = np.float32(y - y0)
            if _POOL is not None and h > 400:
                step = -(-h // N_WORKERS)
                futs = [_POOL.submit(self._rows, r0, min(h, r0 + step), bg, prem, a, y0, f, L["m2"], L["m3"], out)
                        for r0 in range(0, h, step)]
                for fu in futs:
                    fu.result()
            else:
                self._rows(0, h, bg, prem, a, y0, f, L["m2"], L["m3"], out)
        if L["outro"] is not None and t > self.duration - self.outro:
            k = smoothstep((t - (self.duration - self.outro)) / 0.6)
            rows = L.get("outro_rows")
            if rows is None:
                nz = np.nonzero(L["outro"][1].max(1) > 0)[0]
                rows = L["outro_rows"] = (int(nz[0]), int(nz[-1]) + 1) if len(nz) else (0, 0)
            r0, r1 = rows
            if r1 > r0:
                al = (L["outro"][1][r0:r1] * k)[..., None]
                seg = out[r0:r1].astype(np.float32)
                out[r0:r1] = np.clip(seg + (L["outro"][0][r0:r1] - seg) * al, 0, 255)
        if self.s["progress_bar"] == "on":
            pw = min(1, t / self.duration) * w      # 진행바도 끝부분을 소수점까지 부드럽게
            full = int(pw)
            bh = max(2, int(round(8 * h / H)))
            out[0:bh, :full] = self.accent
            if full < w:
                fr = pw - full
                out[0:bh, full] = (out[0:bh, full] * (1 - fr) + self.accent * fr).astype(np.uint8)
        return out

    def frame(self, t):
        return self._compose(t, self.L)

    def frame_preview(self, t):
        """미리보기용 작은 화면 (360×640) - 빨라서 재생이 부드러움"""
        if self._small is None:
            self._small = self._make_small()
        return self._compose(t, self._small)

    def thumbnail(self):
        """제목 카드(있으면) 또는 첫 장면"""
        return Image.fromarray(self.frame(min(0.6, self.duration / 2) if self.card is not None else self.intro + 0.1))


# ---------------- 배경음 합성 (저작권 걱정 없는 자체 제작 소리) ----------------
SR = 44100


def _norm(x, peak=1.0):
    m = float(np.abs(x).max()) if x.size else 0
    return (x / m * peak).astype(np.float32) if m > 1e-9 else x.astype(np.float32)


def midi_hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def colored_noise(n, rng, power=1.0):
    """power 0=백색, 1=핑크(부드러운 쉬익), 2=브라운(낮은 웅웅)"""
    X = np.fft.rfft(rng.standard_normal(n))
    f = np.fft.rfftfreq(n, 1 / SR)
    low = f < 20
    f[0] = f[1] if n > 2 else 1
    X /= f ** (power / 2)
    if power >= 2:
        X[low] = 0
    return _norm(np.fft.irfft(X, n))


def band(x, lo=None, hi=None):
    """주파수 거르기 (lo 이하·hi 이상을 부드럽게 줄임)"""
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    m = np.ones_like(f)
    if hi:
        m /= 1 + (f / hi) ** 4
    if lo:
        m /= 1 + (lo / np.maximum(f, 1e-3)) ** 4
    return np.fft.irfft(X * m, len(x)).astype(np.float32)


def smooth_lfo(n, sec, rng, lo=0.0, hi=1.0):
    """sec 초 간격의 무작위 값을 부드럽게 이은 느린 변화 곡선"""
    k = int(n / (sec * SR)) + 3
    pts = rng.uniform(lo, hi, k)
    pos = np.arange(n) / (sec * SR)
    i = np.minimum(pos.astype(int), k - 2)
    w = (1 - np.cos(np.pi * (pos - i))) / 2
    return (pts[i] * (1 - w) + pts[i + 1] * w).astype(np.float32)


def ola_conv(x, h, block=1 << 16):
    nfft = 1 << int(np.ceil(np.log2(block + len(h) - 1)))
    Hf = np.fft.rfft(h, nfft)
    y = np.zeros(len(x) + len(h), np.float32)
    for i in range(0, len(x), block):
        seg = x[i:i + block]
        Y = np.fft.irfft(np.fft.rfft(seg, nfft) * Hf, nfft)[:len(seg) + len(h) - 1]
        y[i:i + len(Y)] += Y
    return y[:len(x)]


def reverb(st, rng, sec=2.5, mix=0.35):
    """공간 울림 (스테레오)"""
    n_ir = int(sec * SR)
    env = np.exp(-np.arange(n_ir) / SR * 6.9 / sec)
    out = np.empty_like(st)
    for c in range(2):
        ir = band((rng.standard_normal(n_ir) * env).astype(np.float32), lo=150, hi=6000)
        ir /= np.sqrt((ir ** 2).sum()) + 1e-9
        out[:, c] = st[:, c] * (1 - mix) + ola_conv(st[:, c], ir) * mix
    return out


def place(buf, sig, t_sec, pan=0.5):
    i = int(t_sec * SR)
    if i >= len(buf):
        return
    e = min(len(buf), i + len(sig))
    buf[i:e, 0] += sig[:e - i] * (1 - pan) * 2 * 0.5
    buf[i:e, 1] += sig[:e - i] * pan * 2 * 0.5


PROGS = {
    "warm": [[48, 55, 60, 64, 67], [45, 52, 57, 60, 64], [41, 48, 53, 57, 60], [43, 50, 55, 59, 62]],
    "sad": [[45, 52, 57, 60, 64], [41, 48, 53, 57, 60], [48, 55, 60, 64, 67], [43, 50, 55, 59, 62]],
    "dark": [[45, 52, 57, 60], [46, 53, 58, 62], [41, 48, 53, 56], [40, 47, 52, 56]],
    "space": [[50, 57, 62, 64, 69], [47, 54, 59, 62, 66], [43, 50, 55, 57, 62], [45, 52, 57, 59, 64]],
}


def gen_pad(n, rng, mood="warm", chord_sec=8.0, bright=2500):
    """화음이 천천히 바뀌는 부드러운 패드"""
    prog, fade = PROGS[mood], 3.0
    seg = int((chord_sec + fade) * SR)
    t = np.arange(seg) / SR
    env = np.minimum(1, t / fade) * np.minimum(1, (seg / SR - t) / fade)
    env = (np.sin(env * np.pi / 2) ** 2).astype(np.float32)
    out = np.zeros((n, 2), np.float32)
    start, ci = 0, 0
    while start < n:
        sig = np.zeros((seg, 2), np.float32)
        for m in prog[ci % len(prog)]:
            f = midi_hz(m)
            for c, det in enumerate((-1, 1)):
                for cents in (0, 5 * det, -7 * det):
                    ff = f * 2 ** (cents / 1200)
                    ph = rng.uniform(0, 2 * np.pi)
                    sig[:, c] += np.sin(2 * np.pi * ff * t + ph) + 0.18 * np.sin(4 * np.pi * ff * t + ph)
        sig *= env[:, None]
        e = min(n, start + seg)
        out[start:e] += sig[:e - start]
        start += int(chord_sec * SR)
        ci += 1
    for c in range(2):
        out[:, c] = band(out[:, c], hi=bright)
    return _norm(reverb(out, rng, 3.5, 0.45))


def gen_drone(n, rng):
    """낮게 깔리는 어두운 울림 + 가끔 불협화음"""
    t = np.arange(n) / SR
    st = np.zeros((n, 2), np.float32)
    for mul, amp in ((1, 1.0), (1.5, 0.5), (2.0, 0.35), (2.997, 0.15)):
        a = amp * smooth_lfo(n, 6, rng, 0.5, 1.0)
        st[:, 0] += a * np.sin(2 * np.pi * 55 * mul * t + rng.uniform(0, 6.28))
        st[:, 1] += a * np.sin(2 * np.pi * 55 * mul * 1.002 * t + rng.uniform(0, 6.28))
    for c in range(2):
        st[:, c] += band(colored_noise(n, rng, 2.0), lo=30, hi=250) * 0.35
    pos = rng.uniform(4, 9)
    while pos < n / SR - 5:
        d = rng.uniform(4, 6)
        tt = np.arange(int(d * SR)) / SR
        f = midi_hz(rng.integers(68, 80))
        sig = (np.sin(2 * np.pi * f * tt) + np.sin(2 * np.pi * f * 1.059 * tt)) * np.sin(np.pi * tt / d) ** 2 * 0.06
        place(st, sig.astype(np.float32), pos, rng.uniform(0.2, 0.8))
        pos += rng.uniform(9, 16)
    return _norm(reverb(st, rng, 4.0, 0.4))


def heartbeat(n, rng, bpm0=58, bpm1=92):
    """점점 빨라지는 심장박동"""
    out = np.zeros(n, np.float32)
    kl = int(0.35 * SR)
    tk = np.arange(kl) / SR

    def thump(freq, dec, amp):
        f = freq * (1 + 0.6 * np.exp(-tk * 30))
        return (amp * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tk / dec)).astype(np.float32)
    lub, dub = thump(55, 0.07, 1.0), thump(48, 0.06, 0.7)
    dur, t = n / SR, 0.5
    while t < dur - 0.4:
        for snd, off in ((lub, 0.0), (dub, 0.26)):
            i = int((t + off) * SR)
            e = min(n, i + kl)
            if i < n:
                out[i:e] += snd[:e - i]
        t += 60 / (bpm0 + (bpm1 - bpm0) * (t / dur) ** 1.5)
    out = _norm(band(out, hi=180))
    return np.stack([out, out], 1)


def gen_rain(n, rng):
    """빗소리: 쉬익 + 빗방울 톡톡 + 낮은 웅웅"""
    ch = []
    kl = int(0.006 * SR)
    for _ in range(2):
        hiss = band(colored_noise(n, rng, 1.0), lo=500, hi=9000) * (0.75 + 0.25 * smooth_lfo(n, 5, rng))
        imp = np.zeros(n, np.float32)
        k = int(n / SR * 40)
        imp[rng.integers(0, n, k)] = rng.uniform(0.2, 1, k) * rng.choice([-1, 1], k)
        kern = (rng.standard_normal(kl) * np.exp(-np.arange(kl) / (0.0012 * SR))).astype(np.float32)
        drops = band(ola_conv(imp, kern), lo=1500, hi=7000)
        rumble = band(colored_noise(n, rng, 2.0), hi=160)
        ch.append(_norm(hiss) * 0.6 + _norm(drops) * 0.35 + _norm(rumble) * 0.25)
    return _norm(np.stack(ch, 1))


def gen_sea(n, rng):
    """심해: 깊은 물 울림 + 고래 소리 + 수중 음파"""
    swell = 0.6 + 0.4 * smooth_lfo(n, 7, rng)
    st = np.stack([_norm(band(colored_noise(n, rng, 2.0), lo=25, hi=220)) * swell for _ in range(2)], 1) * 0.7
    fx = np.zeros((n, 2), np.float32)
    pos = rng.uniform(3, 10)
    while pos < n / SR - 5:
        d = rng.uniform(2.5, 4.5)
        tt = np.arange(int(d * SR)) / SR
        f = rng.uniform(140, 260) * (1 + 0.6 * np.sin(np.pi * tt / d)) * (1 + 0.01 * np.sin(2 * np.pi * 5 * tt))
        ph = 2 * np.pi * np.cumsum(f) / SR
        place(fx, ((np.sin(ph) + 0.3 * np.sin(2 * ph)) * np.sin(np.pi * tt / d) ** 2 * 0.35).astype(np.float32), pos, rng.uniform(0.3, 0.7))
        pos += rng.uniform(10, 18)
    tp = np.arange(int(0.25 * SR)) / SR
    ping = (np.sin(2 * np.pi * 1150 * tp) * np.exp(-tp / 0.05) * 0.25).astype(np.float32)
    pos = rng.uniform(5, 12)
    while pos < n / SR - 1:
        place(fx, ping, pos, rng.uniform(0.3, 0.7))
        pos += rng.uniform(12, 22)
    return _norm(st + reverb(fx, rng, 5.0, 0.7))


def bell(freq, dur=2.5):
    t = np.arange(int(dur * SR)) / SR
    sig = sum(a * np.sin(2 * np.pi * freq * r * t) * np.exp(-t / d) for r, a, d in ((1, 1, 1.2), (2.76, 0.5, 0.6), (5.4, 0.25, 0.3), (8.93, 0.12, 0.15)))
    return (sig * np.minimum(1, t / 0.005)).astype(np.float32)


def gen_space(n, rng):
    """우주: 넓은 패드 + 반짝이는 종소리"""
    pad = gen_pad(n, rng, "space", 10, 1800) * 0.7
    tw = np.zeros((n, 2), np.float32)
    pos = rng.uniform(1, 3)
    while pos < n / SR - 3:
        place(tw, bell(midi_hz(rng.choice([74, 76, 79, 81, 83, 86, 88]))) * rng.uniform(0.08, 0.18), pos, rng.uniform(0.2, 0.8))
        pos += rng.uniform(1.5, 4)
    return _norm(pad + reverb(tw, rng, 4, 0.6))


def pluck(freq, dur=1.6):
    t = np.arange(int(dur * SR)) / SR
    s = (np.sin(2 * np.pi * freq * t) + 0.35 * np.sin(4 * np.pi * freq * t) * np.exp(-t / 0.25)
         + 0.12 * np.sin(6 * np.pi * freq * t) * np.exp(-t / 0.12))
    return (s * np.exp(-t / 0.55) * np.minimum(1, t / 0.003)).astype(np.float32)


def gen_musicbox(n, rng, mood="warm", bpm=72):
    """오르골: 화음을 따라 톡톡 튀는 멜로디 + 은은한 패드"""
    prog, chord_sec = PROGS[mood], 8.0
    pad = gen_pad(n, rng, mood, chord_sec, 1600) * 0.35
    mel = np.zeros((n, 2), np.float32)
    cache, step, tpos, idx = {}, 60 / bpm / 2, 0.5, 0
    pattern = [0, 2, 4, 2, 3, 4, 2, 1]
    while tpos < n / SR - 1.5:
        tones = sorted(set(m + 12 for m in prog[int(tpos // chord_sec) % len(prog)][1:]))
        if rng.random() > 0.22:
            m = tones[pattern[idx % len(pattern)] % len(tones)]
            if m not in cache:
                cache[m] = pluck(midi_hz(m))
            place(mel, cache[m] * rng.uniform(0.5, 1.0), tpos, 0.5 + 0.25 * np.sin(idx * 0.7))
        tpos += step
        idx += 1
    return _norm(pad + _norm(reverb(mel, rng, 2.5, 0.35)) * 0.8)


def gen_pulse(n, rng, bpm=100):
    """긴장 펄스: 일정하게 뛰는 낮은 베이스 + 어두운 패드"""
    pad = gen_pad(n, rng, "dark", 8, 1400) * 0.4
    step = 60 / bpm / 2
    nl = int(step * SR * 0.95)
    tt = np.arange(nl) / SR
    env = np.exp(-tt / 0.12) * np.minimum(1, tt / 0.004)
    bass, cache, tpos, k = np.zeros(n, np.float32), {}, 0.0, 0
    while tpos < n / SR:
        m = PROGS["dark"][int(tpos // 8) % 4][0] - 12 + (12 if k % 4 == 3 else 0)
        if m not in cache:
            f = midi_hz(m)
            cache[m] = (sum(np.sin(2 * np.pi * f * h * tt) / h for h in range(1, 7)) * env).astype(np.float32)
        i = int(tpos * SR)
        e = min(n, i + nl)
        bass[i:e] += cache[m][:e - i] * (1.0 if k % 2 == 0 else 0.7)
        tpos += step
        k += 1
    bass = _norm(band(bass, hi=900))
    return _norm(pad + np.stack([bass, bass], 1) * 0.5)


def gen_wind(n, rng):
    """바람: 세기와 높낮이가 계속 바뀌는 바람"""
    gust = 0.35 + 0.65 * smooth_lfo(n, 4, rng) ** 2
    ch = []
    for _ in range(2):
        pn = colored_noise(n, rng, 1.0)
        mix = smooth_lfo(n, 5, rng)
        ch.append((_norm(band(pn, lo=150, hi=700)) * (1 - mix) + _norm(band(pn, lo=600, hi=2600)) * mix * 0.6) * gust
                  + _norm(band(colored_noise(n, rng, 2.0), hi=120)) * 0.25)
    return _norm(np.stack(ch, 1))


def gen_waves(n, rng):
    """파도: 밀려왔다 부서지는 파도"""
    env = np.zeros(n, np.float32)
    pos = 0.0
    while pos < n / SR:
        rise, fall, amp = rng.uniform(2, 3.5), rng.uniform(3, 5), rng.uniform(0.6, 1)
        tt = np.arange(int((rise + fall) * SR)) / SR
        e_ = (np.where(tt < rise, (tt / rise) ** 2, np.exp(-(tt - rise) / (fall / 3))) * amp).astype(np.float32)
        i = int(pos * SR)
        e = min(n, i + len(e_))
        env[i:e] = np.maximum(env[i:e], e_[:e - i])
        pos += rng.uniform(5.5, 9)
    ch = [_norm(band(colored_noise(n, rng, 1.0), lo=120, hi=6000)) * (0.15 + 0.85 * env)
          + _norm(band(colored_noise(n, rng, 2.0), lo=30, hi=400)) * 0.35 for _ in range(2)]
    return _norm(np.stack(ch, 1))


SOUND_STYLES = {
    "잔잔한 패드": lambda n, r: gen_pad(n, r, "warm"),
    "슬픈 패드": lambda n, r: gen_pad(n, r, "sad"),
    "감성 오르골": lambda n, r: gen_musicbox(n, r, "sad", 66),
    "밝은 오르골": lambda n, r: gen_musicbox(n, r, "warm", 96),
    "긴장 펄스": gen_pulse,
    "어두운 드론": gen_drone,
    "공포 심장박동": lambda n, r: _norm(gen_drone(n, r) * 0.6 + heartbeat(n, r) * 0.9),
    "비 오는 밤": lambda n, r: _norm(gen_rain(n, r) * 0.8 + gen_pad(n, r, "sad") * 0.35),
    "빗소리": gen_rain,
    "심해": gen_sea,
    "우주": gen_space,
    "바람": gen_wind,
    "파도": gen_waves,
}
assert list(SOUND_STYLES) == SOUND_STYLE_NAMES


def reveal_fx(n, t_hit, rng):
    """반전 순간: 1.6초 동안 차오르는 소리 → 쿵"""
    out = np.zeros((n, 2), np.float32)
    rl = int(1.6 * SR)
    i = int(t_hit * SR)
    if i - rl > 0:
        tt = np.arange(rl) / rl
        r_ = _norm(band(colored_noise(rl, rng, 1.0), lo=300, hi=5000)) * tt ** 3 * 0.45
        out[i - rl:i] += r_[:, None]
    bl = int(3.0 * SR)
    tt = np.arange(bl) / SR
    boom = np.sin(2 * np.pi * np.cumsum(38 + 70 * np.exp(-tt * 8)) / SR) * np.exp(-tt / 0.9)
    hit = _norm(band(colored_noise(bl, rng, 2.0), hi=900)) * np.exp(-tt / 0.25) * 0.5
    b_ = ((boom + hit) * np.minimum(1, tt / 0.002)).astype(np.float32)
    e = min(n, i + bl)
    if i < n:
        out[i:e] += b_[:e - i, None]
    return out


def decode_audio(path, n):
    """음악 파일을 읽어서 길이에 맞게 반복"""
    import imageio_ffmpeg
    p = subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-v", "error", "-i", path, "-f", "f32le", "-ac", "2", "-ar", str(SR), "-"],
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                       creationflags=(subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0))
    x = np.frombuffer(p.stdout, np.float32).reshape(-1, 2) if p.returncode == 0 else np.zeros((0, 2), np.float32)
    if not len(x):
        raise RuntimeError("음악 파일을 읽지 못했습니다: " + p.stderr.decode("utf-8", "ignore")[:200])
    return np.tile(x, (int(np.ceil(n / len(x))), 1))[:n].copy()


def resolve_style(s, topic):
    st = s["bgm_style"]
    return SOUND_BY_TOPIC.get(topic, "잔잔한 패드") if st not in SOUND_STYLES else st


def make_music(s, style, n):
    """배경음(음악)만 만들기 - 효과음·페이드 없음"""
    rng = np.random.default_rng(None if s["bgm_seed"] == 0 else s["bgm_seed"])
    if s["bgm_mode"] == "자동생성":
        return SOUND_STYLES.get(style, SOUND_STYLES["잔잔한 패드"])(n, rng)
    if s["bgm_mode"] == "파일" and s["bgm_path"] and os.path.exists(s["bgm_path"]):
        return decode_audio(s["bgm_path"], n)
    return None


def build_audio(r, s, style):
    """영상 길이에 맞춘 최종 소리 (배경음 + 반전 효과음). 없으면 None"""
    n = int(r.duration * SR)
    rng = np.random.default_rng(None if s["bgm_seed"] == 0 else s["bgm_seed"])
    music = make_music(s, style, n)
    hit_t = r.reveal_t if s["reveal_hit"] == "on" else None
    if music is None and hit_t is None:
        return None
    out = np.zeros((n, 2), np.float32)
    if music is not None:
        rms = float(np.sqrt((music ** 2).mean())) + 1e-9
        music = music * (0.12 / rms) * max(0, s["bgm_volume"])
        t = np.arange(n) / SR
        g = np.minimum(1, t / 1.5) * np.clip((r.duration - t) / 2.5, 0, 1)
        if hit_t:  # 반전 직전 음악을 줄였다가 다시 올림
            a = max(0.01, hit_t - 1.2)
            b = max(a + 0.01, hit_t - 0.1)
            g = g * np.interp(t, [0, a, b, hit_t + 1.5, hit_t + 4.5, 1e9], [1, 1, 0.25, 0.25, 1, 1])
        out += music * g[:, None].astype(np.float32)
    if hit_t:
        out += reveal_fx(n, hit_t, rng) * 0.5 * max(0, s["hit_volume"])
    peak = float(np.abs(out).max())
    if peak > 0.95:
        out *= 0.95 / peak
    return out


def write_wav(path, x):
    import wave
    d = (np.clip(x, -1, 1) * 32767).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(d.tobytes())


_player = None


def play_wav(path):
    global _player
    stop_wav()
    if os.name == "nt":
        import winsound
        winsound.PlaySound(path, winsound.SND_FILENAME | winsound.SND_ASYNC)
        return
    for cmd in (["afplay", path], ["paplay", path], ["aplay", "-q", path]):
        if shutil.which(cmd[0]):
            _player = subprocess.Popen(cmd)
            return


def stop_wav():
    global _player
    if os.name == "nt":
        try:
            import winsound
            winsound.PlaySound(None, 0)
        except Exception:
            pass
    if _player and _player.poll() is None:
        _player.kill()
    _player = None


def export_mp4(r, out, progress, cancel=None, audio=None):
    import imageio_ffmpeg
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    s = r.s
    fps = max(1, s["fps"])
    dur = r.duration
    n = int(round(dur * fps))
    tmpdir = tempfile.mkdtemp(prefix="shorts_audio_")
    wav = ""
    if audio is not None:
        wav = os.path.join(tmpdir, "audio.wav")
        write_wav(wav, audio)
    cmd = [ff, "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(fps), "-i", "-"]
    if wav:
        cmd += ["-i", wav]
    cmd += ["-c:v", "libx264", "-preset", "fast", "-threads", "0", "-crf", str(max(10, min(30, s["quality"]))), "-pix_fmt", "yuv420p",
            "-g", str(fps * 2), "-movflags", "+faststart"]
    if wav:
        cmd += ["-map", "0:v", "-map", "1:a", "-c:a", "aac", "-b:a", "192k", "-shortest"]
    cmd += ["-t", f"{dur:.2f}", out]
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    log_path = os.path.join(BASE, "ffmpeg_log.txt")
    flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    with open(log_path, "w", encoding="utf-8", errors="ignore") as log:
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=log, creationflags=flags)
        fq = queue.Queue(maxsize=4)          # 그리기와 인코딩을 동시에 (쓰기 스레드)
        werr = []

        def writer():
            try:
                while True:
                    b = fq.get()
                    if b is None:
                        break
                    p.stdin.write(b)
            except (BrokenPipeError, OSError) as e:
                werr.append(e)
            finally:
                try:
                    p.stdin.close()
                except Exception:
                    pass
        wt = threading.Thread(target=writer, daemon=True)
        wt.start()
        try:
            for i in range(n):
                if cancel and cancel.is_set():
                    p.kill()
                    raise RuntimeError("취소됨")
                if werr:
                    break
                fq.put(r.frame(i / fps).tobytes())
                if i % 15 == 0:
                    progress(i, n)
        finally:
            fq.put(None)
            wt.join()
        p.wait()
    shutil.rmtree(tmpdir, ignore_errors=True)
    if p.returncode != 0:
        with open(log_path, encoding="utf-8", errors="ignore") as f:
            raise RuntimeError("ffmpeg 오류:\n" + f.read()[-800:])
    progress(n, n)


def write_package(path_base, title, story, pkg):
    """업로드 문구 txt 저장"""
    lines = [f"[제목 후보]"] + [f"{i + 1}. {t}" for i, t in enumerate(pkg.get("titles", []))]
    lines += ["", "[설명]", pkg.get("description", ""), "", "[해시태그]", pkg.get("hashtags", ""),
              "", "[고정댓글]", pkg.get("pinned_comment", "")]
    if pkg.get("sources"):
        lines += ["", "[출처 (설명란에 넣으면 신뢰도 상승)]"] + [f"- {x}" for x in pkg["sources"]]
    credits = photo_credits(story)
    if credits:
        lines += ["", "[사진 출처 (CC 라이선스는 설명란 표기 필수)]"] + credits
    if pkg.get("notes"):
        lines += ["", "[확인 필요]", str(pkg["notes"])]
    lines += ["", "[본문]", title, "", story_text_only(story).strip()]
    with open(path_base + "_업로드문구.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


# ---------------- 화면(GUI) ----------------
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("쇼츠 스크롤 영상 메이커 PRO (Claude Max) — 소설 · 실화 · 과학 · 자연현상")
        self.geometry("1460x980")
        self.minsize(1200, 760)
        self.q = queue.Queue()
        self.renderer = None
        self.busy = False
        self.playing = False
        self.cancel = threading.Event()
        self.vars = {}
        self.cfg = self.load_cfg()
        self.build_ui()
        self.apply_cfg()
        self.after(100, self.poll)
        self.after(300, self.refresh_preview)
        self.after(500, self.check_claude_ui)
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    # ---- 설정 저장/불러오기 ----
    def load_cfg(self):
        try:
            with open(CONFIG_PATH, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def project_dict(self):
        return {"ver": 2, "model": self.model_var.get(), "category": self.cat_var.get(), "topic": self.topic_var.get(), "genre": self.genre_var.get(),
                "sources": getattr(self, "sources", []), "notes": getattr(self, "notes", ""),
                "length": self.len_var.get(), "judge": self.judge_var.get(), "theme": self.theme_var.get(),
                "research": self.research_var.get(), "autophoto": self.autophoto_var.get(),
                "reference": getattr(self, "reference", ""),
                "title": self.title_var.get(), "story": self.get_story(), "settings": self.get_settings()}

    def save_cfg(self):
        try:
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(self.project_dict(), f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def apply_cfg(self, c=None):
        c = self.cfg if c is None else c
        self.model_var.set(c.get("model", ""))
        self.topic_var.set(c.get("topic", ""))
        cat = c.get("category", "허구 단편소설")
        self.cat_var.set(cat if cat in CATEGORIES else "허구 단편소설")
        topics = cat_info(self.cat_var.get())[1]
        self.genre_box.config(values=list(topics))
        g = c.get("genre", "")
        self.genre_var.set(g or list(topics)[0])
        self.research_var.set(bool(c.get("research", True)))
        self.autophoto_var.set(bool(c.get("autophoto", True)))
        self.set_reference(c.get("reference", ""))
        self.set_sources(c.get("sources", []), c.get("notes", ""))
        self.len_var.set(c.get("length", "40"))
        self.judge_var.set(bool(c.get("judge", True)))
        self.theme_var.set(c.get("theme", "시네마 다크"))
        self.title_var.set(c.get("title", SAMPLE_TITLE))
        self.set_story(c.get("story", SAMPLE_STORY))
        s = dict(DEFAULTS)
        s.update(c.get("settings", {}))
        if c.get("settings") and c.get("ver", 1) < 2 and int(float(s.get("fps", 30))) == 30:
            s["fps"] = 60  # 부드러운 스크롤 기본값으로 올림
        if s.get("bgm_path") and "bgm_mode" not in c.get("settings", {}):
            s["bgm_mode"] = "파일"  # 예전 설정 호환
        self.set_settings(s)

    def on_close(self):
        try:
            self.save_cfg()
        finally:
            self.destroy()

    def open_project(self):
        p = filedialog.askopenfilename(filetypes=[("프로젝트", "*.json")])
        if p:
            with open(p, encoding="utf-8") as f:
                self.apply_cfg(json.load(f))
            self.refresh_preview()

    def save_project(self):
        p = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("프로젝트", "*.json")],
                                         initialfile=safe_name(self.title_var.get()) + ".json")
        if p:
            with open(p, "w", encoding="utf-8") as f:
                json.dump(self.project_dict(), f, ensure_ascii=False, indent=2)
            self.write_log("프로젝트 저장: " + p)

    # ---- UI ----
    def build_ui(self):
        top = ttk.Frame(self, padding=(8, 6))
        top.pack(fill="x")
        ttk.Button(top, text="🆕 새로 만들기", command=self.new_project).pack(side="left", padx=(0, 4))
        ttk.Button(top, text="프로젝트 열기", command=self.open_project).pack(side="left")
        ttk.Button(top, text="프로젝트 저장", command=self.save_project).pack(side="left", padx=4)
        ttk.Separator(top, orient="vertical").pack(side="left", fill="y", padx=8)
        ttk.Label(top, text="Claude 상태").pack(side="left")
        self.claude_lamp = tk.Label(top, text="●", fg="gray", font=("맑은 고딕", 14))
        self.claude_lamp.pack(side="left")
        self.claude_info = ttk.Label(top, text="확인 중...")
        self.claude_info.pack(side="left", padx=(2, 8))
        ttk.Button(top, text="연결 확인", command=self.check_claude_ui).pack(side="left")
        ttk.Label(top, text="모델").pack(side="left", padx=(14, 0))
        self.model_var = tk.StringVar()
        ttk.Combobox(top, textvariable=self.model_var, width=10, values=["", "sonnet", "opus", "haiku"]).pack(side="left", padx=4)
        ttk.Label(top, text="(빈칸 = Claude Code 기본 · API 키 없이 Max 구독 사용)", foreground="gray").pack(side="left")

        main = ttk.Frame(self, padding=(8, 0))
        main.pack(fill="both", expand=True)
        right = ttk.LabelFrame(main, text="미리보기 (1080×1920)", padding=6)
        right.pack(side="right", fill="y", padx=(8, 0))
        left = ttk.Frame(main)
        left.pack(side="left", fill="both", expand=True)

        # ① 소설
        s1 = ttk.LabelFrame(left, text="① 대본 만들기", padding=6)
        s1.pack(fill="both", expand=True)
        r = ttk.Frame(s1)
        r.pack(fill="x")
        ttk.Label(r, text="종류").pack(side="left")
        self.cat_var = tk.StringVar()
        cb = ttk.Combobox(r, textvariable=self.cat_var, width=11, state="readonly", values=list(CATEGORIES))
        cb.pack(side="left", padx=4)
        cb.bind("<<ComboboxSelected>>", self.on_category)
        ttk.Label(r, text="소재").pack(side="left")
        self.genre_var = tk.StringVar()
        self.genre_box = ttk.Combobox(r, textvariable=self.genre_var, width=16, values=list(GENRES))
        self.genre_box.pack(side="left", padx=4)
        self.genre_box.bind("<<ComboboxSelected>>", self.on_genre)
        ttk.Label(r, text="주제").pack(side="left")
        self.topic_var = tk.StringVar()
        self.topic_box = ttk.Combobox(r, textvariable=self.topic_var, width=34)
        self.topic_box.pack(side="left", padx=4, fill="x", expand=True)
        ttk.Button(r, text="인기 주제 추천", command=self.ai_ideas).pack(side="left", padx=(0, 4))
        ttk.Label(r, text="← 직접 입력 가능", foreground="gray").pack(side="left")
        r1 = ttk.Frame(s1)
        r1.pack(fill="x", pady=(4, 0))
        ttk.Label(r1, text="길이(초)").pack(side="left")
        self.len_var = tk.StringVar()
        ttk.Spinbox(r1, from_=15, to=180, increment=5, textvariable=self.len_var, width=5).pack(side="left", padx=4)
        self.judge_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(r1, text="3안 작성 후 AI 심사", variable=self.judge_var).pack(side="left", padx=4)
        self.research_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(r1, text="🔎 웹 검색으로 조사", variable=self.research_var).pack(side="left", padx=4)
        self.autophoto_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(r1, text="근거 사진 자동(사실일 때)", variable=self.autophoto_var).pack(side="left", padx=4)
        ttk.Button(r1, text="참고자료 붙여넣기", command=self.edit_reference).pack(side="left", padx=4)
        self.ref_label = ttk.Label(r1, text="", foreground="gray")
        self.ref_label.pack(side="left")
        ttk.Button(r1, text="✍ AI로 대본 쓰기", command=self.ai_write).pack(side="right", padx=4)
        r2 = ttk.Frame(s1)
        r2.pack(fill="x", pady=4)
        ttk.Label(r2, text="제목").pack(side="left")
        self.title_var = tk.StringVar()
        ttk.Entry(r2, textvariable=self.title_var, width=40).pack(side="left", padx=4)
        ttk.Button(r2, text="대본 평가", command=self.ai_review).pack(side="left", padx=(12, 4))
        ttk.Button(r2, text="사실 검증", command=self.ai_verify).pack(side="left", padx=4)
        ttk.Button(r2, text="업로드 문구 만들기", command=self.ai_package).pack(side="left", padx=4)
        self.src_label = ttk.Label(r2, text="", foreground="gray")
        self.src_label.pack(side="left", padx=8)
        r4 = ttk.Frame(s1)
        r4.pack(fill="x", pady=(0, 4))
        ttk.Label(r4, text="근거 사진").pack(side="left")
        ttk.Button(r4, text="파일에서 넣기", command=self.add_photo_file).pack(side="left", padx=4)
        ttk.Button(r4, text="붙여넣기 (Ctrl+V)", command=lambda: self.on_paste(from_button=True)).pack(side="left")
        ttk.Button(r4, text="🔎 AI 근거사진 찾기", command=self.ai_photos).pack(side="left", padx=4)
        ttk.Label(r4, text="사진·이미지 주소·파일을 복사해서 본문에 Ctrl+V → 커서 위치에 들어감",
                  foreground="gray").pack(side="left", padx=6)
        self.story = ScrolledText(s1, height=8, wrap="word", font=("맑은 고딕", 11), undo=True)
        self.story.pack(fill="both", expand=True)
        self.story.bind("<<Paste>>", self.on_paste)

        # ②③ 설정 (탭)
        s2 = ttk.LabelFrame(left, text="② 디자인 · 영상 설정", padding=6)
        s2.pack(fill="x", pady=(6, 0))
        tr = ttk.Frame(s2)
        tr.pack(fill="x")
        ttk.Label(tr, text="테마").pack(side="left")
        self.theme_var = tk.StringVar()
        tb = ttk.Combobox(tr, textvariable=self.theme_var, width=12, state="readonly", values=list(THEMES))
        tb.pack(side="left", padx=4)
        ttk.Button(tr, text="테마 적용", command=lambda: self.apply_theme(self.theme_var.get())).pack(side="left")
        ttk.Label(tr, text="  (소재를 고르면 테마·배경음 자동)", foreground="gray").pack(side="left")
        ttk.Separator(tr, orient="vertical").pack(side="left", fill="y", padx=8)
        ttk.Button(tr, text="🎵 배경음 만들기", command=self.make_bgm).pack(side="left")
        ttk.Button(tr, text="▶ 다시 듣기", command=self.replay_bgm).pack(side="left", padx=(4, 0))
        ttk.Button(tr, text="■ 소리 정지", command=stop_wav).pack(side="left", padx=4)
        ttk.Button(tr, text="💾 배경음 저장(이름 지정 → MP4에 사용)", command=self.save_bgm_named).pack(side="left")
        ttk.Button(tr, text="라이브용 긴 버전", command=self.save_bgm_wav).pack(side="left", padx=(4, 0))
        nb = ttk.Notebook(s2)
        nb.pack(fill="x", pady=(4, 0))
        tabs = {}
        for sec, k, lb, t, _ in FIELDS:
            if sec not in tabs:
                tabs[sec] = ttk.Frame(nb, padding=4)
                nb.add(tabs[sec], text=sec)
                tabs[sec].n = 0
            fr = tabs[sec]
            self.make_field(fr, k, lb, t, fr.n // 3, fr.n % 3)
            fr.n += 1

        # ④ 만들기
        s4 = ttk.LabelFrame(left, text="③ 만들기", padding=6)
        s4.pack(fill="x", pady=(6, 0))
        ttk.Button(s4, text="미리보기 새로고침", command=self.refresh_preview).pack(side="left")
        ttk.Button(s4, text="MP4 만들기", command=self.make_mp4).pack(side="left", padx=6)
        ttk.Button(s4, text="연속 제작(여러 편 자동)", command=self.batch).pack(side="left")
        ttk.Button(s4, text="취소", command=self.cancel.set).pack(side="left", padx=6)
        ttk.Button(s4, text="저장 폴더 열기", command=self.open_folder).pack(side="left")
        self.prog = ttk.Progressbar(s4, length=220)
        self.prog.pack(side="left", padx=10)
        self.status = ttk.Label(s4, text="준비")
        self.status.pack(side="left")

        # 미리보기
        self.canvas = tk.Canvas(right, width=PREVIEW_W, height=PREVIEW_H, bg="black", highlightthickness=0)
        self.canvas.pack()
        self.img_id = self.canvas.create_image(0, 0, anchor="nw")
        self.tvar = tk.DoubleVar(value=0)
        self.tscale = ttk.Scale(right, from_=0, to=10, variable=self.tvar, command=self.show_frame, length=PREVIEW_W)
        self.tscale.pack(pady=4)
        pr = ttk.Frame(right)
        pr.pack()
        ttk.Button(pr, text="▶ 재생 / ■ 정지", command=self.toggle_play).pack(side="left")
        ttk.Button(pr, text="썸네일 PNG 저장", command=self.save_thumb).pack(side="left", padx=4)
        self.info = ttk.Label(right, text="", wraplength=PREVIEW_W, justify="left")
        self.info.pack(pady=4)

        # 하단 AI 명령어
        bot = ttk.LabelFrame(self, text="AI 명령어 (Claude로 수정)", padding=6)
        bot.pack(fill="x", padx=8, pady=8)
        r3 = ttk.Frame(bot)
        r3.pack(fill="x")
        self.cmd_var = tk.StringVar()
        e = ttk.Entry(r3, textvariable=self.cmd_var, font=("맑은 고딕", 11))
        e.pack(side="left", fill="x", expand=True)
        e.bind("<Return>", lambda _: self.ai_command())
        ttk.Button(r3, text="실행", command=self.ai_command).pack(side="left", padx=6)
        ttk.Label(bot, foreground="gray",
                  text='예) "글자 더 크게"  "공포 레드 테마로"  "결말을 더 소름돋게"  "45초에 맞춰줘"  "배경음 빗소리로"  "사진을 결말 앞으로 옮겨줘"').pack(anchor="w")
        self.log = ScrolledText(bot, height=4, state="disabled", font=("맑은 고딕", 10))
        self.log.pack(fill="x")

    def make_field(self, parent, key, label, t, r, c):
        ttk.Label(parent, text=label).grid(row=r, column=c * 2, sticky="e", padx=(8, 2), pady=2)
        v = tk.StringVar()
        self.vars[key] = v
        cell = ttk.Frame(parent)
        cell.grid(row=r, column=c * 2 + 1, sticky="w", pady=2)
        if t.startswith("choice:"):
            ttk.Combobox(cell, textvariable=v, values=t[7:].split(","), width=10, state="readonly").pack(side="left")
        elif t == "color":
            ttk.Entry(cell, textvariable=v, width=9).pack(side="left")
            sw = tk.Label(cell, width=2, relief="solid")
            sw.pack(side="left", padx=2)

            def pick():
                col = colorchooser.askcolor(v.get())[1]
                if col:
                    v.set(col.upper())

            def upd(*_):
                try:
                    sw.config(bg=v.get())
                except tk.TclError:
                    pass
            v.trace_add("write", upd)
            ttk.Button(cell, text="선택", width=4, command=pick).pack(side="left")
        elif t in ("font", "image", "audio", "dir"):
            ttk.Entry(cell, textvariable=v, width=18).pack(side="left")
            ttk.Button(cell, text="…", width=3, command=lambda: self.browse(key, t)).pack(side="left")
            if t in ("image", "audio"):
                ttk.Button(cell, text="x", width=2, command=lambda: v.set("")).pack(side="left")
        elif t == "str":
            ttk.Entry(cell, textvariable=v, width=28).pack(side="left")
        else:
            ttk.Entry(cell, textvariable=v, width=8).pack(side="left")

    def browse(self, key, t):
        types = {"font": [("글꼴", "*.ttf *.otf *.ttc")],
                 "image": [("이미지", "*.png *.jpg *.jpeg *.webp")],
                 "audio": [("오디오", "*.mp3 *.wav *.m4a *.ogg")]}
        p = filedialog.askdirectory() if t == "dir" else filedialog.askopenfilename(filetypes=types[t])
        if p:
            self.vars[key].set(p)

    # ---- 값 읽기/쓰기 ----
    def get_settings(self):
        return {k: cast(k, self.vars[k].get()) for k in DEFAULTS}

    def set_settings(self, d):
        for k, v in d.items():
            if k in self.vars:
                self.vars[k].set(str(cast(k, v)))

    def get_story(self):
        return self.story.get("1.0", "end-1c")

    def set_story(self, txt):
        self.story.delete("1.0", "end")
        self.story.insert("1.0", txt)

    def write_log(self, msg):
        self.log.config(state="normal")
        self.log.insert("end", time.strftime("[%H:%M:%S] ") + msg + "\n")
        self.log.see("end")
        self.log.config(state="disabled")

    def apply_theme(self, name):
        if name in THEMES:
            self.set_settings(THEMES[name])
            self.theme_var.set(name)
            self.refresh_preview()

    def on_category(self, *_):
        topics = cat_info(self.cat_var.get())[1]
        self.genre_box.config(values=list(topics))
        self.genre_var.set(list(topics)[0])
        self.topic_box.config(values=[])
        self.on_genre()

    def on_genre(self, *_):
        topics = cat_info(self.cat_var.get())[1]
        g = self.genre_var.get()
        if g in topics:
            self.apply_theme(topics[g][1])

    def set_sources(self, sources, notes=""):
        self.sources = [str(x) for x in (sources or [])]
        self.notes = str(notes or "")
        txt = ("출처: " + " · ".join(self.sources)) if self.sources else ""
        if self.notes:
            txt += ("  |  " if txt else "") + "확인 필요: " + self.notes
        self.src_label.config(text=txt[:110])

    # ---- 백그라운드 작업 ----
    def poll(self):
        while not self.q.empty():
            self.q.get()()
        self.after(100, self.poll)

    def run_bg(self, label, job, done):
        if self.busy:
            messagebox.showinfo("알림", "다른 작업이 진행 중입니다.")
            return
        self.busy = True
        self.cancel.clear()
        self.status.config(text=label)

        def worker():
            try:
                res = job()
                self.q.put(lambda: (self.end_busy("완료"), done(res)))
            except Exception as e:
                self.q.put(lambda e=e: (self.end_busy("오류"), self.on_err(e)))
        threading.Thread(target=worker, daemon=True).start()

    def end_busy(self, txt):
        self.busy = False
        self.status.config(text=txt)

    def on_err(self, e):
        msg = str(e)
        if isinstance(e, ModuleNotFoundError):
            msg += "\n\npip install pillow numpy imageio-ffmpeg"
        self.write_log("오류: " + (msg.splitlines()[0] if msg else ""))
        if msg != "취소됨":
            messagebox.showerror("오류", msg)

    def log_bg(self, msg):
        self.q.put(lambda: self.write_log(msg))

    # ---- AI ----
    def check_claude_ui(self):
        self.claude_lamp.config(fg="orange")
        self.claude_info.config(text="확인 중...")

        def worker():
            try:
                v = check_claude()
                self.q.put(lambda: (self.claude_lamp.config(fg="green"), self.claude_info.config(text="준비됨 " + v)))
            except Exception as e:
                msg = str(e).splitlines()[0][:60]
                self.q.put(lambda: (self.claude_lamp.config(fg="red"), self.claude_info.config(text=msg)))
        threading.Thread(target=worker, daemon=True).start()

    def story_prompt(self, category, topic, genre, sec, research=None, reference="", photos=None):
        factual, topics = cat_info(category)
        g = topics.get(genre, ("(사용자가 직접 정한 소재)", ""))[0]
        txt = (f"콘텐츠 종류: {category}" + (" (사실 기반 - 지어내지 말 것)" if factual else " (허구)") + "\n"
               f"주제: {topic.strip() or '자유 (요즘 쇼츠에서 반응 좋을 소재로)'}\n"
               f"소재: {genre}\n소재 공식: {g}\n"
               f"목표 길이: 약 {sec:.0f}초 분량 (본문 공백 포함 약 {int(sec * 6)}자, 넘지 말 것)")
        if reference.strip():
            txt += "\n\n[사용자가 붙여넣은 참고자료 - 이 내용을 가장 우선해서 사용]\n" + reference.strip()[:12000]
        if research:
            txt += ("\n\n[웹 조사 자료 - " + ("사실은 이 안에서만 쓸 것" if factual else "이야기 재료로 참고") + "]\n"
                    + json.dumps({k: research.get(k) for k in ("topic", "facts", "hook", "twist", "sources")}, ensure_ascii=False))
        if photos:
            txt += ("\n\n[근거 사진] 아래 사진을 그 사실을 말한 문단 바로 뒤에 '[사진1]' 처럼 한 줄로 넣어라. "
                    "첫 문단 바로 뒤, 마지막 문단 뒤에는 넣지 말고 사진끼리 붙이지 않는다.\n"
                    + "\n".join(f"사진{i + 1}: {p.get('caption', '')} ({p.get('after', '')})" for i, p in enumerate(photos)))
        return txt

    def generate_story(self, model, category, topic, genre, sec, judge, log, research=False, autophoto=False,
                       reference="", media_dir=None):
        """대본 생성 파이프라인. 반환 dict: title, story, note, sources, notes, topic
        research=True : 웹 조사(+사진 수집) → 조사 자료로 집필
        autophoto=True: 사실 기반이면 완성된 대본에 맞춰 근거 사진을 찾아 끼움"""
        factual = cat_info(category)[0]
        media_dir = media_dir or os.path.join(DEFAULTS["out_dir"], "media")
        info, photos, sources = None, [], []
        if research:
            log("🔎 웹 검색으로 조사 중... (1~4분)")
            info = ask_json(model, RESEARCH_SYSTEM, self.story_prompt(category, topic, genre, sec, reference=reference), tools=WEB_TOOLS)
            topic = info.get("topic") or topic
            sources = [str(x) for x in info.get("sources") or []]
            log(f"  조사 완료: {topic}  (사실 {len(info.get('facts') or [])}개, 출처 {len(sources)}개)")
            if factual and autophoto and info.get("photos"):
                photos = fetch_photos(info.get("photos"), media_dir, log)
        user = self.story_prompt(category, topic, genre, sec, info, reference, photos)
        single_sys, multi_sys = systems_for(category)
        note = ""
        if not judge:
            log("대본 쓰는 중...")
            d = ask_json(model, single_sys, user)
            title, story, notes = d.get("title", ""), d.get("story", ""), d.get("notes", "")
            sources = sources or d.get("sources", [])
        else:
            log("초안 3개 작성 중...")
            drafts = ask_json(model, multi_sys, user).get("drafts", [])
            drafts = [d for d in drafts if isinstance(d, dict) and d.get("story")]
            if not drafts:
                raise RuntimeError("초안을 만들지 못했습니다.")
            log("편집장 심사 중... (" + " / ".join(d.get("title", "") for d in drafts) + ")")
            j = ask_json(model, JUDGE_SYSTEM, f"콘텐츠 종류: {category}\n소재: {genre}\n\n[초안들]\n" + json.dumps(drafts, ensure_ascii=False))
            try:
                best = int(j.get("best", 0))
            except (TypeError, ValueError):
                best = 0
            best = max(0, min(best, len(drafts) - 1))
            scores = j.get("scores") or []
            note = f"{best + 1}안 선택 → " + "  ".join(f"{i + 1}안 {sc.get('total', '?')}점({sc.get('reason', '')})"
                                                     for i, sc in enumerate(scores) if isinstance(sc, dict))
            pol = j.get("polish") or {}
            title = pol.get("title") or drafts[best].get("title", "")
            story = pol.get("story") or drafts[best].get("story", "")
            sources = sources or pol.get("sources") or drafts[best].get("sources", [])
            notes = pol.get("notes") or drafts[best].get("notes", "")
        if photos:
            story = place_photos(story, photos)
        elif factual and autophoto:
            log("🔎 근거 사진 찾는 중...")
            try:
                d = ask_json(model, PHOTO_SYSTEM, f"콘텐츠 종류: {category}\n[제목] {title}\n\n[본문]\n{story}", tools=WEB_TOOLS)
                photos = fetch_photos(d.get("photos"), media_dir, log)
                if photos:
                    story = place_photos(story, photos)
            except Exception as e:
                log("  사진 찾기 실패: " + str(e)[:80])
            story = strip_placeholders(story)
        else:
            story = strip_placeholders(story)
        return {"title": title, "story": story, "note": note, "sources": sources, "notes": notes, "topic": topic}

    def ai_write(self):
        try:
            sec = float(self.len_var.get())
        except ValueError:
            sec = 40
        model, cat, topic, genre, judge = self.model_var.get().strip(), self.cat_var.get(), self.topic_var.get(), self.genre_var.get(), self.judge_var.get()
        research, autophoto, ref = self.research_var.get(), self.autophoto_var.get(), getattr(self, "reference", "")
        media_dir = self.media_dir()

        def job():
            return self.generate_story(model, cat, topic, genre, sec, judge, self.log_bg, research, autophoto, ref, media_dir)

        def done(res):
            self.title_var.set(res["title"])
            self.set_story(res["story"])
            if res.get("topic") and not self.topic_var.get().strip():
                self.topic_var.set(res["topic"])
            self.set_sources(res["sources"], res["notes"])
            if res["sources"]:
                self.write_log("출처: " + " / ".join(self.sources))
            if res["notes"]:
                self.write_log("⚠ 확인 필요: " + str(res["notes"]) + '  → "사실 검증" 버튼으로 점검 권장')
            self.vars["target_sec"].set(str(sec))
            self.write_log(f"대본 완성: {res['title']}" + (f"  [{res['note']}]" if res["note"] else ""))
            self.refresh_preview()
            self.save_cfg()
        msg = "Claude가 대본을 쓰는 중..."
        if research:
            msg += " (웹 조사 포함, 3~6분 걸릴 수 있음)"
        elif judge:
            msg += " (3안 작성 + 심사, 1~2분)"
        self.write_log(msg)
        self.run_bg("대본 쓰는 중...", job, done)

    # ---- 새로 만들기 / 참고자료 / 사진 ----
    def new_project(self):
        if not messagebox.askyesno("새로 만들기", "제목·본문·주제·출처·참고자료를 모두 지우고 새로 시작할까요?\n(디자인·소리 설정과 종류·소재는 그대로 둡니다)"):
            return
        self.playing = False
        stop_wav()
        self.title_var.set("")
        self.set_story("")
        self.topic_var.set("")
        self.topic_box.config(values=[])
        self.set_sources([], "")
        self.set_reference("")
        self.cmd_var.set("")
        self.last_review = self.last_verify = None
        self.bgm_made = None
        self.vars["bgm_seed"].set("0")
        self.tvar.set(0)
        self.write_log("──────── 새로 만들기 ────────")
        self.refresh_preview()
        self.save_cfg()

    def set_reference(self, txt):
        self.reference = str(txt or "")
        n = len(self.reference.strip())
        self.ref_label.config(text=f"참고자료 {n:,}자" if n else "")

    def edit_reference(self):
        dlg = tk.Toplevel(self)
        dlg.title("참고자료 붙여넣기")
        dlg.geometry("720x520")
        dlg.transient(self)
        ttk.Label(dlg, text="기사·위키·논문 요약 등을 복사해서 붙여넣으세요. AI가 이 내용을 가장 우선해서 대본을 씁니다.",
                  padding=6).pack(anchor="w")
        box = ScrolledText(dlg, wrap="word", font=("맑은 고딕", 11))
        box.pack(fill="both", expand=True, padx=6)
        box.insert("1.0", getattr(self, "reference", ""))
        bf = ttk.Frame(dlg, padding=6)
        bf.pack(fill="x")

        def ok():
            self.set_reference(box.get("1.0", "end-1c"))
            self.save_cfg()
            dlg.destroy()
        ttk.Button(bf, text="지우기", command=lambda: box.delete("1.0", "end")).pack(side="left")
        ttk.Button(bf, text="저장", command=ok).pack(side="right")
        ttk.Button(bf, text="닫기", command=dlg.destroy).pack(side="right", padx=4)
        box.focus_set()

    def media_dir(self):
        return os.path.join(self.get_settings()["out_dir"], "media")

    def ask_caption(self, cap="", credit=""):
        dlg = tk.Toplevel(self)
        dlg.title("사진 정보")
        dlg.transient(self)
        dlg.grab_set()
        cv, sv = tk.StringVar(value=cap), tk.StringVar(value=credit)
        ttk.Label(dlg, text="사진 설명 (빈칸 가능)").grid(row=0, column=0, sticky="e", padx=6, pady=6)
        e1 = ttk.Entry(dlg, textvariable=cv, width=40)
        e1.grid(row=0, column=1, padx=6, pady=6)
        ttk.Label(dlg, text="출처 (예: NASA / 퍼블릭 도메인)").grid(row=1, column=0, sticky="e", padx=6, pady=6)
        ttk.Entry(dlg, textvariable=sv, width=40).grid(row=1, column=1, padx=6, pady=6)
        res = {}

        def ok(*_):
            res["v"] = (cv.get().strip(), sv.get().strip())
            dlg.destroy()
        ttk.Button(dlg, text="넣기", command=ok).grid(row=2, column=1, sticky="e", padx=6, pady=6)
        dlg.bind("<Return>", ok)
        e1.focus_set()
        self.wait_window(dlg)
        return res.get("v")

    def insert_marker(self, marker):
        """커서가 있는 줄 끝에 사진 줄을 별도 문단으로 삽입"""
        idx = self.story.index("insert lineend")
        self.story.insert(idx, "\n\n" + marker + "\n")
        self.story.mark_set("insert", f"{idx} + {len(marker) + 3}c")
        self.story.see("insert")
        self.refresh_preview()
        self.write_log("사진 넣음: " + marker[:80])

    def insert_photo_image(self, im, cap_hint=""):
        info = self.ask_caption(cap_hint)
        if info is None:
            return
        path = save_media_image(im, self.media_dir())
        self.insert_marker(make_marker(path, info[0], info[1]))

    def insert_photo_file(self, f):
        try:
            im = Image.open(f)
            im.load()
        except Exception as e:
            messagebox.showerror("사진", f"사진을 열 수 없습니다: {e}")
            return
        self.insert_photo_image(im, os.path.splitext(os.path.basename(f))[0][:15])

    def insert_photo_url(self, url):
        media = self.media_dir()

        def job():
            return download_image(url, media)

        def done(path):
            info = self.ask_caption("", re.sub(r"^https?://([^/]+).*$", r"\1", url))
            if info is not None:
                self.insert_marker(make_marker(path, info[0], info[1], url))
        self.write_log("이미지 주소에서 사진 받는 중...")
        self.run_bg("사진 받는 중...", job, done)

    def add_photo_file(self):
        files = filedialog.askopenfilenames(filetypes=[("이미지", "*.png *.jpg *.jpeg *.webp *.bmp *.gif")])
        for f in files:
            self.insert_photo_file(f)

    def on_paste(self, event=None, from_button=False):
        """Ctrl+V: 사진이면 사진 줄로, 이미지 주소면 내려받아 사진 줄로, 그 외는 일반 글 붙여넣기"""
        clip = None
        try:
            from PIL import ImageGrab
            clip = ImageGrab.grabclipboard()
        except Exception:
            clip = None
        if isinstance(clip, Image.Image):
            self.insert_photo_image(clip, "")
            return "break"
        if isinstance(clip, list):
            files = [f for f in clip if str(f).lower().endswith(IMG_EXT)]
            if files:
                for f in files:
                    self.insert_photo_file(f)
                return "break"
        try:
            txt = self.clipboard_get().strip()
        except tk.TclError:
            txt = ""
        if re.match(r"^https?://\S+$", txt) and (re.search(r"\.(jpe?g|png|webp|gif)(\?|$)", txt, re.I) or "wikimedia.org" in txt or "/wiki/File:" in txt):
            self.insert_photo_url(txt)
            return "break"
        if from_button:
            if txt:
                self.story.insert("insert", txt)
                self.refresh_preview()
            else:
                messagebox.showinfo("붙여넣기", "클립보드에 사진이나 글이 없습니다.")
            return "break"
        self.after(50, self.refresh_preview)
        return None

    def ai_photos(self):
        story = self.get_story()
        if not story_text_only(story).strip():
            messagebox.showinfo("근거 사진", "먼저 대본을 만들거나 입력하세요.")
            return
        model, title, cat = self.model_var.get().strip(), self.title_var.get(), self.cat_var.get()
        media = self.media_dir()
        text = story_text_only(story)

        def job():
            d = ask_json(model, PHOTO_SYSTEM, f"콘텐츠 종류: {cat}\n[제목] {title}\n\n[본문]\n{text}", tools=WEB_TOOLS)
            return fetch_photos(d.get("photos"), media, self.log_bg)

        def done(photos):
            if not photos:
                self.write_log("받을 수 있는 근거 사진을 찾지 못했습니다. 직접 복사해서 Ctrl+V 로 넣어보세요.")
                return
            self.set_story(place_photos(self.get_story(), photos))
            self.write_log(f"근거 사진 {len(photos)}장 배치 완료 (위치는 본문에서 [사진: ...] 줄을 옮겨 조정)")
            self.refresh_preview()
            self.save_cfg()
        self.write_log("🔎 AI가 근거 사진을 찾는 중... (1~3분)")
        self.run_bg("사진 찾는 중...", job, done)

    def ai_ideas(self):
        g, cat = self.genre_var.get(), self.cat_var.get()
        factual, topics = cat_info(cat)
        user = (f"콘텐츠 종류: {cat}" + (" (실제 사건·사실만)" if factual else "") +
                f"\n소재: {g}\n소재 공식: {topics.get(g, ('(사용자가 직접 정한 소재)', ''))[0]}\n이 소재로 쇼츠 주제 8개를 만들어줘.")
        model = self.model_var.get().strip()
        web = self.research_var.get()
        if web:
            user += "\n[웹 검색 모드] WebSearch 로 최근 화제가 된 사건·발견·현상·이야기를 찾아 그중에서 고른다. 실제로 존재하는 것만."

        def job():
            return ask_json(model, IDEA_SYSTEM, user, tools=WEB_TOOLS if web else None)

        def done(d):
            ideas = [str(x) for x in d.get("ideas", []) if str(x).strip()]
            if ideas:
                self.topic_box.config(values=ideas)
                self.topic_var.set(ideas[0])
                self.write_log("주제 추천 (주제 칸 ▼에서 선택): " + " / ".join(ideas))
        self.write_log(f"[{cat} · {g}] 인기 주제를 고르는 중...")
        self.run_bg("주제 추천 중...", job, done)

    def ai_review(self):
        model = self.model_var.get().strip()
        user = f"콘텐츠 종류: {self.cat_var.get()}\n[제목] {self.title_var.get()}\n\n[본문]\n{to_placeholders(self.get_story())[0]}"

        def job():
            return ask_json(model, REVIEW_SYSTEM, user)

        def done(d):
            sc = d.get("scores") or {}
            names = {"hook": "훅", "pacing": "전개", "ending": "결말", "readability": "가독성", "share": "공유욕구"}
            line = "  ".join(f"{names.get(k, k)} {sc.get(k, '?')}" for k in names)
            self.write_log(f"평가 {d.get('grade', '')}등급 {d.get('total', '?')}/50  |  {line}")
            for x in d.get("strengths", []):
                self.write_log("  + " + str(x))
            for x in d.get("fixes", []):
                self.write_log("  ! " + str(x))
            self.write_log('  → 고치려면 아래 AI 명령어에 "평가에서 지적한 대로 고쳐줘" 라고 입력')
            self.last_review = d
        self.write_log("편집장이 평가하는 중...")
        self.run_bg("평가 중...", job, done)

    def ai_verify(self):
        model = self.model_var.get().strip()
        text, mapping = to_placeholders(self.get_story())
        user = (f"콘텐츠 종류: {self.cat_var.get()}\n[제목] {self.title_var.get()}\n\n[본문]\n{text}\n\n[작성 시 출처]\n"
                + "\n".join(getattr(self, "sources", [])))
        web = self.research_var.get()

        def job():
            return ask_json(model, VERIFY_SYSTEM + (WEB_VERIFY_BLOCK if web else ""), user, tools=WEB_TOOLS if web else None)

        def done(d):
            v = d.get("verdict", "")
            mark = {"safe": "✅ 안전", "needs_fix": "⚠ 수정 필요", "risky": "❌ 위험"}.get(v, v)
            self.write_log(f"사실 검증 {mark}  |  {d.get('summary', '')}")
            for it in d.get("issues", []):
                if isinstance(it, dict):
                    self.write_log(f"  [{it.get('status', '')}] {it.get('claim', '')} → {it.get('fix', '')}")
            self.last_verify = d
            cs = d.get("corrected_story") or ""
            if cs.strip() and v != "safe":
                if messagebox.askyesno("사실 검증", "틀리거나 불확실한 부분을 고친 본문이 있습니다. 바로 적용할까요?"):
                    self.set_story(from_placeholders(cs, mapping))
                    self.write_log("  → 고친 본문 적용됨 (사진 유지)")
                    self.refresh_preview()
        self.write_log("팩트체커가 사실을 점검하는 중..." + (" (웹 검색 확인 포함)" if web else ""))
        self.run_bg("사실 검증 중...", job, done)

    def ai_package(self):
        model = self.model_var.get().strip()
        title, story = self.title_var.get(), self.get_story()
        user = f"콘텐츠 종류: {self.cat_var.get()}\n소재: {self.genre_var.get()}\n[제목] {title}\n\n[본문]\n{story_text_only(story)}"
        out_dir = self.get_settings()["out_dir"]
        sources = list(getattr(self, "sources", []))

        def job():
            pkg = ask_json(model, PACKAGE_SYSTEM, user)
            pkg["sources"] = sources
            os.makedirs(out_dir, exist_ok=True)
            base = os.path.join(out_dir, safe_name(title))
            write_package(base, title, story, pkg)
            return pkg, base

        def done(res):
            pkg, base = res
            self.write_log("업로드 문구 저장: " + base + "_업로드문구.txt")
            for i, t in enumerate(pkg.get("titles", [])):
                self.write_log(f"  제목{i + 1}: {t}")
            self.write_log("  해시태그: " + str(pkg.get("hashtags", "")))
            self.write_log("  고정댓글: " + str(pkg.get("pinned_comment", "")))
        self.write_log("업로드 문구 만드는 중...")
        self.run_bg("문구 작성 중...", job, done)

    def ai_command(self):
        cmd = self.cmd_var.get().strip()
        if not cmd:
            return
        s = {k: v for k, v in self.get_settings().items() if k not in FILE_KEYS}
        dur = f"{self.renderer.duration:.1f}초" if self.renderer else "알수없음"
        extra = ""
        if getattr(self, "last_review", None) and "평가" in cmd:
            extra = "\n\n[최근 평가]\n" + json.dumps(self.last_review, ensure_ascii=False)
        if getattr(self, "last_verify", None) and "검증" in cmd:
            extra += "\n\n[최근 사실 검증]\n" + json.dumps(self.last_verify, ensure_ascii=False)
        if cat_info(self.cat_var.get())[0]:
            extra = f"\n[콘텐츠 종류] {self.cat_var.get()} (사실 기반 - 지어내지 말 것)" + extra
        ph_text, ph_map = to_placeholders(self.get_story())
        user = (f"[현재 제목]\n{self.title_var.get()}\n\n[현재 본문]\n{ph_text}\n\n"
                f"[현재 설정]\n{json.dumps(s, ensure_ascii=False)}\n[현재 테마] {self.theme_var.get()}\n[현재 영상 길이] {dur}{extra}\n\n[명령]\n{cmd}")
        model = self.model_var.get().strip()

        def job():
            return ask_json(model, command_system(), user)

        def done(d):
            if d.get("theme") in THEMES:
                self.apply_theme(d["theme"])
            if d.get("title"):
                self.title_var.set(d["title"])
            if d.get("story"):
                self.set_story(from_placeholders(d["story"], ph_map) if ph_map else strip_placeholders(d["story"]))
            st = {k: v for k, v in (d.get("settings") or {}).items() if k in DEFAULTS and k not in FILE_KEYS}
            self.set_settings(st)
            self.write_log(f"▶ {cmd}\n   → {d.get('message', '수정 완료')}")
            self.cmd_var.set("")
            self.refresh_preview()
            self.save_cfg()
        self.write_log(f"명령 전송: {cmd}")
        self.run_bg("AI 수정 중...", job, done)

    # ---- 미리보기 ----
    def refresh_preview(self):
        try:
            self.renderer = Renderer(self.title_var.get(), self.get_story(), self.get_settings())
        except Exception as e:
            self.on_err(e)
            return
        r = self.renderer
        self.tscale.config(to=max(0.1, r.duration))
        if self.tvar.get() > r.duration:
            self.tvar.set(0)
        if not self.playing and self.tvar.get() < 0.05:
            self.tvar.set(min(r.duration, r.intro + 0.3))  # 제목 카드가 사라지고 글이 보이는 시점
        warn = "\n⚠ 3분 넘음 (쇼츠 제한)" if r.duration > 180 else ""
        body = story_text_only(self.get_story())
        chars = len(body.replace(" ", "").replace("\n", ""))
        nph = len(photo_credits(self.get_story()))
        seed = self.vars["bgm_seed"].get()
        snd = ((self.cur_style() + (f" #{seed} (고정)" if seed not in ("", "0") else " (만들기 전)"))
               if self.vars["bgm_mode"].get() == "자동생성"
               else ("파일 " + os.path.basename(self.vars["bgm_path"].get()) if self.vars["bgm_mode"].get() == "파일" else "없음"))
        hit = f" | 반전 효과음 {r.reveal_t:.1f}초" if r.reveal_t and self.vars["reveal_hit"].get() == "on" else ""
        self.info.config(text=f"총 {r.duration:.1f}초 (제목카드 {r.intro:.1f} + 정지 {r.hs:.1f} + 스크롤 {r.scroll_t:.1f} + 끝 {r.he:.1f})\n"
                              f"본문 {chars}자 | 스크롤 {max(0, r.dist)}px | {r.speed:.0f}px/초{warn}\n"
                              f"배경음: {snd}{hit}" + (f" | 사진 {nph}장" if nph else ""))
        self.show_frame()

    def show_frame(self, *_):
        if not self.renderer:
            return
        im = Image.fromarray(self.renderer.frame_preview(float(self.tvar.get())))
        if self.vars["safe_guide"].get() == "on":
            d = ImageDraw.Draw(im, "RGBA")
            # 쇼츠 UI가 가리는 영역: 오른쪽 버튼 열, 아래 제목/채널 영역
            d.rectangle([PREVIEW_W - 50, 0, PREVIEW_W, PREVIEW_H], fill=(255, 0, 0, 60))
            d.rectangle([0, int(PREVIEW_H * 0.80), PREVIEW_W, PREVIEW_H], fill=(255, 0, 0, 60))
        self.photo = ImageTk.PhotoImage(im)
        self.canvas.itemconfig(self.img_id, image=self.photo)

    def cur_style(self):
        return resolve_style(self.get_settings(), self.genre_var.get())

    def make_bgm(self):
        """배경음을 새로 만들어 고정 (같은 번호로 MP4에도 똑같이 들어감)"""
        self.refresh_preview()
        if not self.renderer:
            return
        s = self.get_settings()
        if s["bgm_mode"] == "자동생성":
            seed = int(np.random.default_rng().integers(1, 100000))
            self.vars["bgm_seed"].set(str(seed))
            s["bgm_seed"] = seed
        r, style = self.renderer, self.cur_style()
        media = self.media_dir()

        def job():
            a = build_audio(r, s, style)
            if a is None:
                raise RuntimeError("배경음이 '없음'이고 반전 효과음도 꺼져 있습니다.")
            os.makedirs(media, exist_ok=True)
            name = (f"배경음_{safe_name(style)}_{s['bgm_seed']}.wav" if s["bgm_mode"] == "자동생성"
                    else f"믹스_{os.path.splitext(os.path.basename(s['bgm_path']))[0]}.wav")
            path = os.path.join(media, name)
            write_wav(path, a)
            return path

        def done(p):
            self.bgm_made = {"path": p, "seed": s["bgm_seed"], "style": style, "dur": round(r.duration, 2),
                             "mode": s["bgm_mode"], "src": s["bgm_path"] if s["bgm_mode"] == "파일" else ""}
            what = f"{style} #{s['bgm_seed']}" if s["bgm_mode"] == "자동생성" else "파일 " + os.path.basename(s["bgm_path"])
            self.write_log(f"🎵 배경음 만들기 완료: {what}"
                           + (f" · 반전 효과음 {r.reveal_t:.1f}초" if r.reveal_t and s["reveal_hit"] == "on" else "")
                           + (" → 이 소리가 MP4에 그대로 들어갑니다 (마음에 안 들면 한 번 더 누르기)" if s["bgm_mode"] == "자동생성"
                              else " → 이 파일이 MP4에 그대로 들어갑니다"))
            self.write_log("  저장: " + p)
            self.refresh_preview()
            self.save_cfg()
            self.replay_bgm()
        self.write_log("🎵 배경음 만드는 중...")
        self.run_bg("배경음 만드는 중...", job, done)

    def replay_bgm(self):
        """만든 배경음을 화면과 같이 처음부터 재생"""
        made = getattr(self, "bgm_made", None)
        s = self.get_settings()
        changed = made and (made["mode"] != s["bgm_mode"] or (s["bgm_mode"] == "파일" and made.get("src") != s["bgm_path"])
                            or (s["bgm_mode"] == "자동생성" and str(made["seed"]) != str(s["bgm_seed"])))
        if not made or not os.path.exists(made["path"]) or changed:
            self.make_bgm()
            return
        if self.renderer and abs(self.renderer.duration - made["dur"]) > 0.05:
            self.write_log("  영상 길이가 바뀌어서 같은 번호로 다시 만듭니다.")
            s = self.get_settings()
            if s["bgm_mode"] == "자동생성":
                self.vars["bgm_seed"].set(str(made["seed"]))
            self._remake_same()
            return
        play_wav(made["path"])
        self.playing = False
        self.tvar.set(0)
        self.toggle_play()

    def _remake_same(self):
        """번호는 그대로 두고 지금 길이에 맞춰 다시 만들기"""
        r, s, style = self.renderer, self.get_settings(), self.cur_style()
        path = self.bgm_made["path"]

        def job():
            a = build_audio(r, s, style)
            if a is None:
                raise RuntimeError("배경음이 '없음'이고 반전 효과음도 꺼져 있습니다.")
            write_wav(path, a)
            return path

        def done(p):
            self.bgm_made.update(dur=round(r.duration, 2), style=style)
            self.replay_bgm()
        self.run_bg("배경음 맞추는 중...", job, done)

    def save_bgm_named(self):
        """지금 배경음을 원하는 이름으로 저장하고, 그 파일을 배경음으로 지정 (다시 듣기·MP4 모두 이 파일 사용)"""
        self.refresh_preview()
        if not self.renderer:
            return
        s, style = self.get_settings(), self.cur_style()
        if s["bgm_mode"] == "없음":
            messagebox.showinfo("배경음 저장", "소리 탭에서 배경음을 '자동생성' 또는 '파일'로 바꾼 뒤 저장하세요.")
            return
        if s["bgm_mode"] == "자동생성" and s["bgm_seed"] == 0:
            s["bgm_seed"] = int(np.random.default_rng().integers(1, 100000))
            self.vars["bgm_seed"].set(str(s["bgm_seed"]))
        music_dir = os.path.join(s["out_dir"], "music")
        os.makedirs(music_dir, exist_ok=True)
        default = f"{safe_name(self.title_var.get()) or '배경음'}_{safe_name(style)}.wav" if s["bgm_mode"] == "자동생성" \
            else f"{safe_name(self.title_var.get()) or '배경음'}_음악.wav"
        path = filedialog.asksaveasfilename(title="배경음 저장", defaultextension=".wav", initialdir=music_dir,
                                            initialfile=default, filetypes=[("WAV", "*.wav")])
        if not path:
            return
        r = self.renderer
        n = int((r.duration + 10) * SR)   # 대본이 조금 길어져도 모자라지 않게 10초 여유

        def job():
            m = make_music(s, style, n)
            if m is None:
                raise RuntimeError("배경음을 만들 수 없습니다 (파일 모드면 음악 파일을 먼저 고르세요).")
            write_wav(path, _norm(m, 0.9))
            return path

        def done(p):
            self.vars["bgm_mode"].set("파일")
            self.vars["bgm_path"].set(p)
            self.bgm_made = None
            self.write_log(f"💾 배경음 저장: {p}")
            self.write_log("  → 배경음이 '파일' 모드로 이 파일에 고정됐습니다. 다시 듣기와 MP4 모두 이 소리를 씁니다. "
                           "(반전 효과음은 대본에 맞춰 그때그때 얹힘)")
            self.save_cfg()
            self.make_bgm()
        self.write_log("배경음 저장 중...")
        self.run_bg("배경음 저장 중...", job, done)

    def save_bgm_wav(self):
        mins = simpledialog.askfloat("라이브용 긴 배경음", "길이(분, 최대 5분)\n라이브·ASMR 영상 배경으로 따로 쓰는 긴 버전입니다. (MP4에는 들어가지 않음)",
                                     minvalue=0.2, maxvalue=5, initialvalue=3)
        if not mins:
            return
        s, style = self.get_settings(), self.cur_style()
        out_dir = s["out_dir"]

        def job():
            n = int(mins * 60 * SR)
            a = SOUND_STYLES[style](n, np.random.default_rng(None if s["bgm_seed"] == 0 else s["bgm_seed"]))
            t = np.arange(n) / SR
            a = a * (np.minimum(1, t / 2) * np.clip((n / SR - t) / 3, 0, 1))[:, None].astype(np.float32) * 0.9
            os.makedirs(out_dir, exist_ok=True)
            p = os.path.join(out_dir, f"배경음_{safe_name(style)}_{time.strftime('%H%M%S')}.wav")
            write_wav(p, a)
            return p

        def done(p):
            self.write_log("라이브용 긴 배경음 저장: " + p)
        self.write_log(f"[{style}] {mins:g}분 라이브용 배경음 만드는 중...")
        self.run_bg("배경음 만드는 중...", job, done)

    def toggle_play(self):
        self.playing = not self.playing
        if not self.playing:
            stop_wav()
        if self.playing and self.renderer:
            if self.tvar.get() >= self.renderer.duration - 0.1 or self.tvar.get() <= self.renderer.intro + 0.35:
                self.tvar.set(0)
            self.t0 = time.time() - float(self.tvar.get())
            self.tick()

    def tick(self):
        if not self.playing or not self.renderer:
            return
        t = time.time() - self.t0
        if t > self.renderer.duration:
            self.playing = False
            return
        t0 = time.time()
        self.tvar.set(t)
        self.show_frame()
        spent = int((time.time() - t0) * 1000)
        self.after(max(1, 16 - spent), self.tick)  # 가능하면 초당 60장

    def save_thumb(self):
        if not self.renderer:
            return
        out_dir = self.get_settings()["out_dir"]
        os.makedirs(out_dir, exist_ok=True)
        p = os.path.join(out_dir, safe_name(self.title_var.get()) + "_썸네일.png")
        self.renderer.thumbnail().save(p)
        self.write_log("썸네일 저장: " + p)

    # ---- 내보내기 ----
    def progress_cb(self, prefix=""):
        def prog(i, n):
            self.q.put(lambda: (self.prog.config(value=i / max(1, n) * 100),
                                self.status.config(text=f"{prefix}만드는 중 {i}/{n}")))
        return prog

    def make_mp4(self):
        self.playing = False
        self.refresh_preview()
        if not self.renderer:
            return
        r = self.renderer
        s = self.get_settings()
        style = self.cur_style()
        base = os.path.join(s["out_dir"], safe_name(self.title_var.get()))
        out = base + ".mp4"
        self.prog["value"] = 0
        prog = self.progress_cb()

        if s["bgm_mode"] == "자동생성" and s["bgm_seed"] == 0:
            self.write_log("  (배경음 번호가 0이라 이번에 새 소리로 만듭니다. 먼저 '🎵 배경음 만들기'로 들어보고 고르면 그 소리가 그대로 들어갑니다)")

        def job():
            self.q.put(lambda: self.status.config(text="배경음 만드는 중..."))
            audio = build_audio(r, s, style)
            export_mp4(r, out, prog, self.cancel, audio)
            r.thumbnail().save(base + "_썸네일.png")
            return out

        def done(p):
            what = ((f"{style} #{s['bgm_seed']}" if s["bgm_seed"] else f"{style} (새로 만듦)") if s["bgm_mode"] == "자동생성"
                    else ("파일 " + os.path.basename(s["bgm_path"]) if s["bgm_mode"] == "파일" else "없음"))
            self.write_log(f"MP4 저장 완료: {p}  (썸네일 PNG 같이 저장 · 배경음 {what})")
            self.save_cfg()
        self.run_bg("영상 만드는 중...", job, done)

    def batch(self):
        n = simpledialog.askinteger("연속 제작", "몇 편을 만들까요? (장르·길이는 현재 설정 사용, 주제는 AI가 매번 새로 고름)", minvalue=1, maxvalue=30, initialvalue=3)
        if not n:
            return
        try:
            sec = float(self.len_var.get())
        except ValueError:
            sec = 40
        model, cat, genre, judge = self.model_var.get().strip(), self.cat_var.get(), self.genre_var.get(), self.judge_var.get()
        research, autophoto = self.research_var.get(), self.autophoto_var.get()
        factual, topics = cat_info(cat)
        s = self.get_settings()
        s["target_sec"] = sec
        s["bgm_seed"] = 0  # 연속 제작은 편마다 다른 배경음
        out_dir = os.path.join(s["out_dir"], time.strftime("batch_%Y%m%d_%H%M"))
        log = self.log_bg

        def job():
            os.makedirs(out_dir, exist_ok=True)
            iu = (f"콘텐츠 종류: {cat}" + (" (실제 사건·사실만)" if factual else "") +
                  f"\n소재: {genre}\n소재 공식: {topics.get(genre, ('(사용자가 직접 정한 소재)', ''))[0]}\n이 소재로 쇼츠 주제 {n}개를 만들어줘. 서로 겹치지 않게.")
            if research:
                iu += "\n[웹 검색 모드] WebSearch 로 최근 화제가 된 실제 사건·발견·현상을 찾아 고른다."
            ideas = ask_json(model, IDEA_SYSTEM, iu, tools=WEB_TOOLS if research else None).get("ideas", [])
            done_list = []
            for i in range(n):
                if self.cancel.is_set():
                    raise RuntimeError("취소됨")
                topic = str(ideas[i]) if i < len(ideas) else ""
                log(f"[{i + 1}/{n}] 주제: {topic or '(자유)'}")
                res = self.generate_story(model, cat, topic, genre, sec, judge, log, research, autophoto, "",
                                          os.path.join(out_dir, "media"))
                title, story, note, sources, notes = res["title"], res["story"], res["note"], res["sources"], res["notes"]
                if factual:
                    log("  사실 검증 중...")
                    try:
                        vt, vm = to_placeholders(story)
                        vr = ask_json(model, VERIFY_SYSTEM + (WEB_VERIFY_BLOCK if research else ""),
                                      f"콘텐츠 종류: {cat}\n[제목] {title}\n\n[본문]\n{vt}\n\n[출처]\n" + "\n".join(map(str, sources)),
                                      tools=WEB_TOOLS if research else None)
                        if vr.get("verdict") != "safe" and (vr.get("corrected_story") or "").strip():
                            story = from_placeholders(vr["corrected_story"], vm)
                            log(f"  ⚠ {len(vr.get('issues', []))}곳 수정 적용: {vr.get('summary', '')}")
                        else:
                            log("  ✅ " + str(vr.get("summary", "")))
                    except Exception as e:
                        log("  검증 실패: " + str(e)[:80])
                base = os.path.join(out_dir, f"{i + 1:02d}_{safe_name(title)}")
                r = Renderer(title, story, s)
                style = resolve_style(s, genre)
                audio = build_audio(r, s, style)
                export_mp4(r, base + ".mp4", self.progress_cb(f"[{i + 1}/{n}] "), self.cancel, audio)
                r.thumbnail().save(base + "_썸네일.png")
                try:
                    pkg = ask_json(model, PACKAGE_SYSTEM, f"콘텐츠 종류: {cat}\n소재: {genre}\n[제목] {title}\n\n[본문]\n{story_text_only(story)}")
                    pkg["sources"], pkg["notes"] = sources, notes
                    write_package(base, title, story, pkg)
                except Exception as e:
                    log("  업로드 문구 실패: " + str(e)[:80])
                log(f"  완료: {title} ({r.duration:.0f}초)" + (f"  [{note}]" if note else ""))
                done_list.append(title)
            return done_list

        def done(lst):
            self.write_log(f"연속 제작 완료 {len(lst)}편 → {out_dir}")
        self.write_log(f"연속 제작 시작: {n}편, {cat} · {genre}, {sec:.0f}초" + (" · 웹 조사" if research else "")
                       + (" · 근거 사진" if factual and autophoto else "") + (" · 사실 검증" if factual else ""))
        self.run_bg("연속 제작 중...", job, done)

    def open_folder(self):
        folder = self.get_settings()["out_dir"]
        os.makedirs(folder, exist_ok=True)
        if os.name == "nt":
            os.startfile(folder)
        else:
            subprocess.Popen(["open" if os.uname().sysname == "Darwin" else "xdg-open", folder])


if __name__ == "__main__":
    App().mainloop()
