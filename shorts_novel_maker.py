# -*- coding: utf-8 -*-
"""
쇼츠 스크롤 영상 메이커 PRO (허구 소설 · 기이한 실화 · 과학 사실 · 자연현상 · 올드 팝송 · 명화)
AI: PC에 설치된 Claude Code(claude -p)를 Max 구독으로 사용 (API 키 불필요)
설치: pip install pillow numpy imageio-ffmpeg  (빠진 패키지는 처음 실행 때 자동 설치됨)
기능: AI 대본(3안 심사·웹 조사), 근거 사진(복붙·AI 검색), 자체 합성 배경음, 연속 제작
실행: python shorts_novel_maker.py
"""
import os, re, io, sys, json, time, queue, shutil, difflib, tempfile, threading, subprocess, math
import importlib
import importlib.util


def pip_install(*pkgs):
    """지금 실행 중인 파이썬에 패키지 설치 (파이썬이 여러 개 깔려 있어도 맞는 곳에 설치됨)"""
    cmd = [sys.executable, "-m", "pip", "install", "--disable-pip-version-check", *pkgs]
    flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, errors="replace", creationflags=flags)
    if r.returncode != 0 and "externally-managed" in (r.stdout or ""):
        r = subprocess.run(cmd + ["--break-system-packages"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                           text=True, errors="replace", creationflags=flags)
    if r.returncode != 0 and "Permission" in (r.stdout or ""):
        r = subprocess.run(cmd + ["--user"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, errors="replace",
                           creationflags=flags)
    return r.returncode == 0, (r.stdout or "")[-600:]


def ensure_packages():
    """numpy, pillow 가 없으면 자동 설치 (imageio-ffmpeg 는 MP4 만들 때 확인)"""
    need = [pk for mod, pk in (("numpy", "numpy"), ("PIL", "pillow")) if importlib.util.find_spec(mod) is None]
    if need:
        print("필요한 패키지를 설치합니다:", " ".join(need), flush=True)
        ok, out = pip_install(*need)
        if not ok:
            print(out)
            print(f'\n자동 설치 실패. 아래 명령을 직접 실행하세요:\n"{sys.executable}" -m pip install {" ".join(need)}')
            input("엔터를 누르면 종료합니다...")
            sys.exit(1)
        importlib.invalidate_caches()


ensure_packages()
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, colorchooser, simpledialog
from tkinter.scrolledtext import ScrolledText
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageTk, ImageFilter

W, H = 1080, 1920            # 현재 화면 크기 (set_format 으로 바뀜)
FORMATS = {"쇼츠 세로(1080×1920)": (1080, 1920), "롱폼 가로(1920×1080)": (1920, 1080)}


def set_format(name):
    """화면 형식 바꾸기 (쇼츠 세로 / 롱폼 가로). 미리보기 크기도 같이 바뀜"""
    global W, H, PREVIEW_W, PREVIEW_H
    W, H = FORMATS.get(name, FORMATS["쇼츠 세로(1080×1920)"])
    if W > H:
        PREVIEW_W, PREVIEW_H = 640, 360
    else:
        PREVIEW_W, PREVIEW_H = 360, 640
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


TTS_VOICES = {
    "선히 (여성, 차분)": "ko-KR-SunHiNeural",
    "인준 (남성, 안정)": "ko-KR-InJoonNeural",
    "현수 (남성, 자연스러움)": "ko-KR-HyunsuMultilingualNeural",
    "윈도우 내장 음성": "sapi",
    "Aria (영어 여성)": "en-US-AriaNeural",
    "Guy (영어 남성)": "en-US-GuyNeural",
    "Nanami (일본어 여성)": "ja-JP-NanamiNeural",
    "Keita (일본어 남성)": "ja-JP-KeitaNeural",
}

LANGS = {   # 코드: (이름, 기본 목소리, 마무리 문구, 파일 꼬리표)
    "ko": ("한국어", "선히 (여성, 차분)", "구독하면 다음 이야기가 이어집니다", ""),
    "en": ("영어", "Aria (영어 여성)", "Subscribe for the next story", "_EN"),
    "ja": ("일본어", "Nanami (일본어 여성)", "次の話はチャンネル登録で", "_JA"),
}


def find_font_lang(lang, bold=False):
    """언어별 글꼴 (일본어는 가나·한자가 있는 글꼴 필요)"""
    if lang == "ja":
        for p_ in ([r"C:\Windows\Fonts\YuGothB.ttc", r"C:\Windows\Fonts\meiryob.ttc"] if bold else []) + [
                r"C:\Windows\Fonts\YuGothM.ttc", r"C:\Windows\Fonts\meiryo.ttc", r"C:\Windows\Fonts\msgothic.ttc",
                "/System/Library/Fonts/ヒラギノ角ゴシック W4.ttc", "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"]:
            if os.path.exists(p_):
                return p_
    if lang == "en":
        for p_ in ([r"C:\Windows\Fonts\segoeuib.ttf", r"C:\Windows\Fonts\arialbd.ttf"] if bold else []) + [
                r"C:\Windows\Fonts\segoeui.ttf", r"C:\Windows\Fonts\arial.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]:
            if os.path.exists(p_):
                return p_
    return ""

# 자체 합성 배경음 스타일 (아래 SOUND_STYLES 와 이름이 같아야 함)
SOUND_STYLE_NAMES = ["노래 멜로디(오르골)", "잔잔한 패드", "슬픈 패드", "감성 오르골", "밝은 오르골", "긴장 펄스", "어두운 드론",
                     "공포 심장박동", "비 오는 밤", "빗소리", "심해", "우주", "바람", "파도"]

# 소재별 자동 배경음
SOUND_BY_TOPIC = {
    "소름 반전": "어두운 드론", "사이다 참교육": "긴장 펄스", "감동 가족사연": "감성 오르골", "공포 괴담": "공포 심장박동",
    "설렘 로맨스": "밝은 오르골", "미스터리 추리": "긴장 펄스", "웃긴 일상썰": "밝은 오르골", "직장 썰": "긴장 펄스",
    "미제 사건": "어두운 드론", "기묘한 우연": "우주", "사라진 사람·배·비행기": "심해", "역사 속 기이한 일": "슬픈 패드",
    "생존 실화": "바람", "세계의 기이한 장소": "바람",
    "우주": "우주", "인체": "잔잔한 패드", "동물·생물": "밝은 오르골", "물리·화학": "잔잔한 패드", "심리·뇌": "긴장 펄스",
    "지구·환경": "바람",
    "명화 탄생 비화": "감성 오르골", "그림 속 숨은 비밀": "긴장 펄스", "화가의 실화": "슬픈 패드", "한국 명화": "감성 오르골",
    "도난·위작·사건": "긴장 펄스", "그림 속 인물의 실화": "감성 오르골",
    "가사 원문+해석": "노래 멜로디(오르골)", "가수·작곡가 실화": "노래 멜로디(오르골)", "노래 탄생 비화": "노래 멜로디(오르골)",
    "노래에 숨은 비밀": "노래 멜로디(오르골)", "크리스마스·캐럴 가사": "노래 멜로디(오르골)", "세계 각국의 옛 노래": "노래 멜로디(오르골)",
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
    ("글자", "photo_h", "사진 최대 높이(화면 비율)", "float", 0.36),
    ("배경", "bg_mode", "배경 종류", "choice:단색,그라데이션,이미지", "그라데이션"),
    ("배경", "bg_color", "배경색(위)", "color", "#0B0F1A"),
    ("배경", "bg_color2", "배경색(아래)", "color", "#1A1030"),
    ("배경", "bg_image", "배경 이미지", "image", ""),
    ("배경", "bg_dim", "이미지 어둡게(0~1)", "float", 0.55),
    ("배경", "bg_blur", "이미지 흐림(px)", "int", 6),
    ("배경", "ken_burns", "이미지 천천히 확대", "choice:on,off", "on"),
    ("배경", "vignette", "가장자리 어둡게", "float", 0.45),
    ("배경", "grain", "필름 노이즈(0~1, 켜면 용량 5~8배↑)", "float", 0),
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
    ("영상", "format", "화면 형식", "choice:" + ",".join(FORMATS), "쇼츠 세로(1080×1920)"),
    ("영상", "layout", "표현 방식", "choice:스크롤형(글이 흐름),자막형(큰 제목+사진+자막)", "스크롤형(글이 흐름)"),
    ("자막형", "head_style", "제목 색", "choice:노란색,흰색+하늘색,흰색,강조색", "흰색+하늘색"),
    ("자막형", "head_size", "제목 크기", "int", 96),
    ("자막형", "sub_size", "자막 크기", "int", 64),
    ("자막형", "sub_style", "자막 스타일", "choice:흰글자+검은테두리,노란글자+검은테두리,검은띠 위 흰글자", "흰글자+검은테두리"),
    ("자막형", "sub_max_chars", "자막 한 번에 글자 수", "int", 28),
    ("자막형", "img_zoom", "사진 천천히 확대", "choice:on,off", "on"),
    ("자막형", "img_radius", "사진 모서리 둥글기", "int", 28),
    ("자막형", "sec_per_char", "나레이션 없을 때 글자당 초", "float", 0.12),
    ("영상", "speed", "스크롤 속도(px/초)", "float", 70),
    ("영상", "target_sec", "목표 길이(초, 0=속도사용)", "float", 0),
    ("영상", "hold_start", "시작 정지(초)", "float", 1.5),
    ("영상", "hold_end", "끝 정지(초)", "float", 3.0),
    ("영상", "fps", "FPS(60=부드러움, 30=빠른 제작)", "int", 60),
    ("영상", "quality", "화질(crf 18=최고·23=권장·28=작게)", "int", 23),
    ("영상", "audio_out", "소리 저장 방식", "choice:MP4에 포함,MP4에 포함+MP3 따로,MP3만 따로(무음 MP4)", "MP4에 포함+MP3 따로"),
    ("영상", "out_dir", "저장 폴더", "dir", os.path.join(BASE, "output")),
    ("나레이션", "narration", "나레이션(음성 읽기)", "choice:on,off", "off"),
    ("나레이션", "narr_voice", "성우", "voice", "선히 (여성, 차분)"),
    ("나레이션", "narr_pitch", "음 높낮이(Hz, 엣지 음성만)", "float", 0),
    ("나레이션", "narr_style", "연기 지시(ChatGPT·Gemini 음성)", "str", "차분하고 또렷한 다큐멘터리 내레이터처럼. 반전 부분은 긴장감 있게."),
    ("나레이션", "openai_tts_model", "ChatGPT 음성 모델", "str", "gpt-4o-mini-tts"),
    ("나레이션", "gemini_tts_model", "Gemini 음성 모델", "str", "gemini-2.5-flash-preview-tts"),
    ("나레이션", "narr_rate", "말 속도(%, -30~+40)", "float", 5),
    ("나레이션", "narr_volume", "나레이션 볼륨(0~2)", "float", 1.0),
    ("나레이션", "narr_gap", "문단 사이 쉼(초)", "float", 0.5),
    ("나레이션", "narr_photo_pause", "사진 보는 시간(초)", "float", 1.5),
    ("나레이션", "narr_duck", "말할 때 음악 크기(0~1)", "float", 0.35),
    ("AI 엔진", "script_engine", "대본 작성 AI", "choice:Claude,ChatGPT,Gemini,자동(키 있으면 ChatGPT→Gemini→Claude)", "Claude"),
    ("AI 엔진", "trans_engine", "번역 AI", "choice:자동(키 있으면 ChatGPT→Gemini→Claude),Claude,ChatGPT,Gemini", "자동(키 있으면 ChatGPT→Gemini→Claude)"),
    ("AI 엔진", "auto_langs", "MP4 만들 때 다른 언어도", "choice:안 함,영어,일본어,영어+일본어", "안 함"),
    ("AI 엔진", "openai_key", "ChatGPT API 키", "secret", ""),
    ("AI 엔진", "openai_model", "ChatGPT 모델", "str", "gpt-4o-mini"),
    ("AI 엔진", "gemini_key", "Gemini API 키", "secret", ""),
    ("AI 엔진", "gemini_model", "Gemini 모델", "str", "gemini-2.5-flash"),
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
FILE_KEYS = {"font_path", "title_font_path", "bg_image", "bgm_path", "out_dir", "safe_guide", "openai_key", "gemini_key"}

# 테마 프리셋 (장르에 맞는 색·분위기)
THEMES = {
    "시네마 다크": dict(bg_mode="그라데이션", bg_color="#0B0F1A", bg_color2="#1A1030", text_color="#F5F5F5",
                    title_color="#FFD54F", accent_color="#FF6B6B", vignette=0.45, grain=0),
    "공포 레드": dict(bg_mode="그라데이션", bg_color="#000000", bg_color2="#2A0000", text_color="#E8E0E0",
                  title_color="#FF3B3B", accent_color="#FF3B3B", vignette=0.7, grain=0),
    "감동 웜톤": dict(bg_mode="그라데이션", bg_color="#2B1D14", bg_color2="#4A2E1C", text_color="#FFF3E0",
                  title_color="#FFB74D", accent_color="#FFAB91", vignette=0.4, grain=0),
    "종이 노트": dict(bg_mode="그라데이션", bg_color="#F6F1E7", bg_color2="#EDE3D1", text_color="#2B2B2B",
                  title_color="#8B2E2E", accent_color="#C0392B", vignette=0.25, grain=0, shadow="off"),
    "네온 시티": dict(bg_mode="그라데이션", bg_color="#05030F", bg_color2="#120A2E", text_color="#E0F7FF",
                  title_color="#00E5FF", accent_color="#FF2BD6", vignette=0.5, grain=0),
    "로맨스 핑크": dict(bg_mode="그라데이션", bg_color="#2A0F1E", bg_color2="#4A1A35", text_color="#FFF0F5",
                    title_color="#FF8FB1", accent_color="#FFB3C6", vignette=0.4, grain=0),
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
    "올드 팝송 이야기": (True, {
        "가사 원문+해석": ("1929년 이전 발표곡의 가사를 원문 한 줄 → 한국어 해석 한 줄로 번갈아 보여준다. 가장 유명한 부분(1절+후렴) 위주. 첫 줄은 노래를 한 문장으로 소개하는 훅, 마지막은 댓글 질문. 예: Danny Boy(1913), O Sole Mio(1898), Let Me Call You Sweetheart(1910)", "감동 웜톤"),
        "가수·작곡가 실화": ("노래를 부르거나 만든 사람의 실제 인생 이야기(시대 제한 없음). 가난, 전쟁, 사랑, 요절, 재기 같은 극적인 순간을 1인칭이 아닌 3인칭으로. 1930년 이후 곡이면 가사·멜로디는 쓰지 않고 이야기만.", "시네마 다크"),
        "노래 탄생 비화": ("곡이 태어난 순간(장소·사람·사건)과 당시 얼마나 유행했는지. '그런데 더 놀라운 건' 반전 비화. 1929년 이전 곡이면 가사 1~4줄 인용 가능.", "감동 웜톤"),
        "노래에 숨은 비밀": ("가사의 진짜 뜻, 사실은 다른 사람이 쓴 곡, 표절·소송·금지곡 등 반전 있는 비화.", "시네마 다크"),
        "크리스마스·캐럴 가사": ("오래된 캐럴(Silent Night 1818, Jingle Bells 1857, O Holy Night 1847 등)의 가사 원문+해석과 짧은 탄생 이야기.", "감동 웜톤"),
        "세계 각국의 옛 노래": ("일본·중남미·러시아·하와이·유럽 민요 등 1929년 이전 노래의 가사 원문+해석. 예: La Cumparsita(1916), Aloha ʻOe(1878), Greensleeves", "로맨스 핑크"),
    }),
}

CATEGORIES["명화 이야기"] = (True, {
    "명화 탄생 비화": ("그림이 그려진 순간의 실제 이야기(장소·사람·사건·돈). 첫 줄은 그 그림에 얽힌 가장 놀라운 사실. 예: 모나리자 도난(1911), 절규의 배경, 별이 빛나는 밤의 정신병원", "종이 노트"),
    "그림 속 숨은 비밀": ("그림 안에 숨은 상징·인물·오류·수수께끼를 하나씩 짚는다. '자세히 보면'으로 시작하는 문단이 좋다. 예: 아르놀피니 부부의 거울, 최후의 만찬의 손, 모내기 그림 속 양반", "시네마 다크"),
    "화가의 실화": ("화가의 인생(가난, 사랑, 병, 전쟁, 재기, 죽음)을 3인칭으로. 널리 알려진 사실만, 루머 금지. 예: 고흐의 귀, 신윤복의 정체, 프리다 칼로의 사고", "감동 웜톤"),
    "한국 명화": ("조선 회화와 근대 한국화(김홍도, 신윤복, 정선, 안견, 장승업, 나혜석 등)의 배경과 그림 읽는 법. 당시 생활상과 연결.", "종이 노트"),
    "도난·위작·사건": ("실제 미술 사건(도난, 위작, 파괴, 소송, 경매 기록). 범인·수법·결말을 순서대로.", "네온 시티"),
    "그림 속 인물의 실화": ("모델이 된 실존 인물의 삶. 그 사람에게 그림이 어떤 의미였는지. 예: 진주 귀걸이를 한 소녀, 올랭피아의 모델, 미인도", "로맨스 핑크"),
})

SONG_CATEGORY = "올드 팝송 이야기"
ART_CATEGORY = "명화 이야기"
ART_SAFE_DEATH_YEAR = 1955   # 작가가 이 해 이전에 사망 → 사후 70년 지나 그림 이미지 사용 가능 (한국·EU 기준)

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


SONG_RULES = """[올드 팝송 규칙 - 저작권 안전 기준, 반드시 지킬 것]
- 가사를 보여주거나 멜로디를 연주하려면 곡(악보·가사)이 1929년 12월 31일 이전에 발표(출판)된 노래여야 한다. 1930년 이후 곡은 가사·멜로디 금지 (예: Over the Rainbow 1939 ✗, You Are My Sunshine 1939 ✗, Happy Birthday 1893 ✓).
- '가수·작곡가 실화' 소재는 시대 제한이 없지만, 1930년 이후 곡이면 가사는 한 줄도 인용하지 않고 melody 는 빈 문자열로 둔다. 실존 인물은 널리 알려진 사실만 쓰고 추측·루머는 쓰지 않는다.
- 특정 가수의 '편곡'이나 '녹음(음원)'은 별개의 저작권이 있으므로 특정 음반을 쓰라고 하지 않는다. 멜로디는 프로그램이 직접 연주한다.
- [가사 모드] 소재 이름에 '가사'가 들어가면: 본문은 ①훅 1~2줄(노래 소개) ②가사 원문 한 줄 → 바로 아래 줄에 한국어 해석, 이 짝을 문단 하나로(문단 사이 빈 줄) ③마지막 댓글 질문 1줄. 원문 줄은 앞에 '♪ ' 를 붙인다. 해석은 직역이 아니라 노래처럼 자연스럽게. 가사가 길면 목표 길이에 맞게 가장 유명한 부분(1절+후렴)만.
- [이야기 모드] 그 외 소재: 첫 줄은 가장 놀라운 사실 → 장면 순서대로 → '그런데 더 놀라운 건' 반전 → 지금도 어디서 들리는지 → 댓글 질문. 1929년 이전 곡이면 가사 1~4줄(♪ 표시)과 해석을 넣어도 된다.
- song 정보를 꼭 채운다: title(원제), title_ko(한국어 제목), year(발표 연도), composer, lyricist, singer(대표 가수, 있으면), composer_death(사망 연도, 모르면 ""), pd_reason(가사·멜로디를 쓸 수 있는 이유 한 줄. 1930년 이후면 "저작권 유효 - 가사·멜로디 미사용")
- melody: 1929년 이전 곡일 때만, 가장 유명한 부분(후렴 또는 첫 소절) 8~24마디를 음표로. 형식: "C4:1 D4:1 E4:2 R:1" (음이름+옥타브:박자, R=쉼표, 박자 0.25~4). bpm 도 적는다. 멜로디가 확실하지 않으면 빈 문자열 (틀린 멜로디보다 없는 게 낫다)."""

SONG_SYSTEM = """너는 한국 유튜브 쇼츠 '옛날 팝송 이야기' 채널의 전문 작가다. 전 세계의 저작권이 끝난 옛 노래(1929년 이전)에 얽힌 실제 이야기를 들려준다.
영상은 글이 위로 천천히 스크롤되는 형식이고, 배경에는 프로그램이 직접 연주한 그 노래의 멜로디(오르골)가 깔린다.
문체는 1~2문장 짧은 문단, 쉬운 단어, 문단 사이 빈 줄. 한 줄 40자 이내. 제목은 15자 이내로 궁금하게.

""" + FACT_RULES + """

""" + SONG_RULES + """

반드시 JSON만 출력: {"title": "제목", "story": "본문", "sources": ["출처1", "출처2"], "confidence": "high", "notes": "확인 필요한 부분", "song": {"title": "", "title_ko": "", "year": 1910, "composer": "", "lyricist": "", "singer": "", "composer_death": "", "pd_reason": ""}, "melody": "C4:1 D4:1 ...", "bpm": 90}"""
SONG_MULTI_SYSTEM = SONG_SYSTEM.replace(
    "반드시 JSON만 출력:", "같은 노래로 서로 다른 접근(훅 방식, 강조하는 비화, 전개 순서)의 초안 3개를 쓴다. 각 초안마다 sources/notes/song/melody/bpm 포함.\n반드시 JSON만 출력: {\"drafts\": [초안1, 초안2, 초안3]} 각 초안 형식:")

ART_RULES = """[명화 규칙 - 저작권 안전 기준, 반드시 지킬 것]
- 그림 이미지를 보여주려면 화가가 """ + str(ART_SAFE_DEATH_YEAR) + """년 이전에 사망한 작품이어야 한다(사후 70년 경과). 그 이후 사망한 화가(예: 피카소 1973, 박수근 1965, 이중섭 1956, 달리 1989)는 이야기만 쓰고 photos 는 빈 배열, pd_reason 에 "저작권 유효 - 이미지 미사용"이라고 적는다.
- 화가 사후 70년이 지난 2차원 회화의 사진은 Wikimedia Commons 에서 퍼블릭 도메인(PD-Art)으로 제공된다. 그 파일을 쓴다. 미술관 공식 공개 이미지(국립중앙박물관 e뮤지엄 공공누리 1유형, Met Museum Open Access, Rijksmuseum 등)도 좋다.
- 실존 인물(화가·모델)은 널리 알려진 사실만. 질병·사생활은 기록으로 확인된 것만 간단히.
- artwork 정보를 꼭 채운다: title(원제), title_ko, artist, artist_death(사망 연도, 숫자), year(제작 연도), medium(재료·기법, 예: 캔버스에 유채 / 비단에 수묵담채), size(크기 cm), museum(소장처), movement(사조·시대), pd_reason(이미지 사용 가능 이유 또는 "저작권 유효 - 이미지 미사용")

[큐레이터 수준 해설 - 반드시 포함할 요소]
미술관 큐레이터가 관람객 앞에서 그 그림 하나를 10분 설명하듯, 아래 요소가 모두 들어가야 한다. 단, 쇼츠이므로 각 요소는 1~2문장, 쉬운 말로. 어려운 용어는 괄호 없이 풀어 쓴다(예: '키아로스쿠로' 대신 '빛과 어둠을 강하게 맞세우는 기법').
1. 훅: 그 그림에 얽힌 가장 놀라운 사실 한 줄 (연도·숫자·사건)
2. 기본 정보: 언제, 어디서, 무엇으로(재료), 얼마나 큰 그림인지 — 숫자는 확인된 것만
3. 시대 맥락: 그 시절 세상(전쟁·종교·돈·유행)이 이 그림에 어떻게 들어왔는지, 사조(인상주의, 진경산수 등)가 왜 생겼는지
4. 구도와 시선: 눈이 어디서 시작해 어디로 가게 그렸는지, 중심은 무엇인지, 왜 그 위치에 뒀는지
5. 빛과 색: 어디서 빛이 들어오는지, 어떤 색을 왜 썼는지(당시 그 물감이 귀했는지, 상징인지)
6. 붓질·기법: 붓 자국, 물감 두께, 선의 성격(한국화면 먹의 농담·여백·준법을 쉬운 말로)
7. 도상(숨은 뜻): 물건·동물·손짓·배경 하나하나가 무엇을 뜻하는지 — '자세히 보면'으로 시작하는 문단 2~3개, 각 문단은 그림의 어느 부분인지 명확히
8. 비교: 같은 화가의 다른 작품이나 다른 화가의 비슷한 그림과 무엇이 다른지 한 문장
9. 소장 이력: 누가 주문했고 어떻게 지금 미술관까지 왔는지(도난·경매·기증 등), 지금 어디서 볼 수 있는지
10. 마무리: 이 그림이 왜 지금도 중요한지 한 줄 + 댓글 질문
'자세히 보면' 문단에는 그 부분의 확대 사진이 붙는다. details 에 각 문단이 가리키는 부분을 그림 전체 기준 비율 상자로 적는다: {"after": "그 문단 앞부분 10~20자(원문 그대로)", "box": [왼쪽x, 위y, 너비w, 높이h] (0~1 비율), "caption": "15자 이내"}. 2~3개. 위치가 확실하지 않으면 넣지 않는다."""

ART_SYSTEM = """너는 국립 미술관의 수석 큐레이터이자 한국 유튜브 쇼츠 '명화 이야기' 채널의 작가다. 전 세계 명화와 한국 명화를 전문가 수준의 깊이로, 그러나 중학생도 알아듣는 말로 해설한다.
영상은 글이 위로 천천히 스크롤되는 형식이고, 그림 전체 사진이 크게 들어간 뒤 '자세히 보면' 문단마다 그 부분의 확대 사진이 붙는다. 시청자는 그림을 보면서 글을 읽는다.
문체는 1~2문장 짧은 문단, 문단 사이 빈 줄. 한 줄 40자 이내. 제목은 15자 이내로 궁금하게. 감탄사·과장 대신 구체적 관찰로 설득한다.

""" + FACT_RULES + """

""" + ART_RULES + """

반드시 JSON만 출력: {"title": "제목", "story": "본문", "sources": ["출처1", "출처2"], "confidence": "high", "notes": "확인 필요한 부분", "artwork": {"title": "", "title_ko": "", "artist": "", "artist_death": 1890, "year": "", "medium": "", "size": "", "museum": "", "movement": "", "pd_reason": ""}, "details": [{"after": "", "box": [0.1, 0.2, 0.3, 0.3], "caption": ""}]}"""
ART_MULTI_SYSTEM = ART_SYSTEM.replace(
    "반드시 JSON만 출력:", "같은 그림으로 서로 다른 접근(훅 방식, 강조하는 해설 요소, 전개 순서)의 초안 3개를 쓴다. 각 초안마다 sources/notes/artwork/details 포함.\n반드시 JSON만 출력: {\"drafts\": [초안1, 초안2, 초안3]} 각 초안 형식:")

FACT_MULTI_SYSTEM = FACT_SYSTEM.replace(
    "반드시 JSON만 출력:", "같은 소재로 서로 다른 접근(훅 방식, 강조하는 사실, 전개 순서)의 초안 3개를 쓴다. 각 초안마다 sources/confidence/notes 포함.\n반드시 JSON만 출력: {{\"drafts\": [초안1, 초안2, 초안3]}} 각 초안 형식:")

VERIFY_SYSTEM = """너는 과학·역사·음악사 팩트체커다. 명화 대본이면 화가 사망 연도, 제작 연도, 재료, 크기, 소장처, 사조, 도상 해석이 미술사 통설과 맞는지 확인한다. 통설이 아닌 개인 해석은 '~로 해석된다'로 고치게 한다.
올드 팝송 대본에 가사(♪ 줄)나 멜로디가 있으면 발표 연도가 1929년 이전인지 반드시 확인하고, 1930년 이후면 verdict 를 risky 로 하고 가사를 빼거나 다른 곡으로 바꾸라고 적는다. 가사 원문이 실제 가사와 맞는지도 확인한다. 아래 쇼츠 대본의 모든 사실 주장(숫자, 날짜, 이름, 장소, 인과관계)을 하나씩 점검한다.
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
- 명화 이야기면 그 그림 자체(Wikimedia Commons 의 PD-Art 파일, 화가 사후 70년 경과작만)를 첫 번째로, 그 다음 이야기에 나오는 부분의 확대 이미지나 화가 초상. 한국 그림은 국립중앙박물관·간송미술관 공개 이미지도 가능.
- 노래 이야기면 그 곡의 옛 악보 표지(sheet music cover, 1929년 이전 출판물은 퍼블릭 도메인), 작곡가·가수의 옛 사진, 당시 공연장 사진을 고른다.
- 그 사건·현상·장소를 실제로 보여주는 사진만 고른다. 비슷한 다른 사진 금지. 직접 열어서(WebFetch) 맞는지 확인한다
- after: 사진이 들어갈 위치 = 본문에서 사진 바로 앞에 올 문장의 일부(원문 그대로 10~20자). 본문이 아직 없으면 그 사진이 보여주는 사실의 핵심 단어
- caption: 15자 이내 한국어 설명 / credit: "작가 또는 기관 / 라이선스" / page: 출처 페이지 URL"""

RESEARCH_SYSTEM = """너는 유튜브 쇼츠 대본을 위한 자료조사원이다. WebSearch 로 주제를 검색하고, 중요한 내용은 WebFetch 로 원문을 열어 확인한다.
주제가 비어 있으면 해당 소재에서 쇼츠로 반응이 좋을 실제 주제를 하나 골라서 조사한다.

[명화일 때] 소장 미술관 공식 페이지와 백과사전 항목을 열어 제작 연도·재료·크기·소장 경로·기법 설명을 확인하고, 미술사학자의 해설(도상·구도·색)을 facts 에 넣는다. photos 첫 번째는 그림 전체(Wikimedia Commons PD-Art 원본, 가장 큰 해상도).

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
명화면 큐레이터 수준인지 본다: 기법·구도·빛과 색·도상·시대 맥락·소장 이력이 모두 구체적 관찰로 들어갔는지, 두루뭉술한 감탄("아름답다", "천재적")만 있으면 크게 감점. artwork/details 를 그대로 넘기고, 화가 사후 70년이 안 된 작품에 이미지가 있으면 감점.
올드 팝송이면: 가사나 멜로디를 쓴 초안은 1929년 이전 발표곡이어야 한다(아니면 0점). 가사 모드는 원문 줄(♪)과 해석 줄이 짝으로 되어 있는지, 해석이 노래처럼 자연스러운지 본다. polish 에는 song/melody/bpm 도 그대로 넘긴다.
사실 기반 콘텐츠(실화·과학·자연현상)이면 '정확성'을 최우선으로 본다: 의심스럽거나 과장된 주장이 있는 초안은 크게 감점하고, polish 에서 그 부분을 안전하게 고친다.
반드시 JSON만 출력: {"best": 가장 좋은 초안 번호(0부터), "scores": [{"total": 합계, "reason": "한 줄 이유"}, ...], "polish": {"title": "최고 초안을 다듬은 제목", "story": "최고 초안을 다듬은 전체 본문", "sources": ["사실 기반일 때 출처"], "notes": "확인 필요한 부분"}}
polish는 선택된 초안의 약점만 손봐서 완성본을 만든다. 길이는 원본과 비슷하게.
""" + KEEP_PHOTO_RULE

REVIEW_SYSTEM = """너는 유튜브 쇼츠 썰 채널의 베테랑 편집장이다. 아래 소설을 쇼츠 기준으로 냉정하게 평가한다.
항목(각 10점): hook(첫 줄), pacing(전개 속도), ending(반전/결말), readability(가독성), share(공유욕구)
명화 콘텐츠면 expertise(큐레이터 수준 전문성: 기법·구도·빛과 색·도상·시대 맥락·소장 이력이 구체적 관찰로 들어갔는지) 항목을 추가해 60점 만점으로 채점하고, fixes 에 빠진 해설 요소를 적는다.
반드시 JSON만 출력: {"scores": {"hook": 0, "pacing": 0, "ending": 0, "readability": 0, "share": 0}, "total": 0~50, "grade": "S/A/B/C", "strengths": ["..."], "fixes": ["구체적인 수정 제안 (어느 줄을 어떻게)", "..."]}"""

PACKAGE_SYSTEM = """너는 유튜브 쇼츠 채널 운영 전문가다. 소설을 읽고 업로드에 필요한 문구를 만든다.
- 제목 후보 5개: 결말을 밝히지 않고 궁금하게, 25자 이내, 이모지 0~1개
- 설명: 2~3줄, 마지막 줄에 "다음 이야기는 구독하고 받아보세요" 류 문구
- 해시태그 8~12개: 허구면 #쇼츠 #썰 #단편소설, 명화면 #명화 #미술 #그림이야기 #화가, 옛 노래면 #올드팝 #팝송 #노래비화 #명곡, 실화·과학이면 #쇼츠 #실화 #미스터리 #과학 #상식 등 종류와 소재 포함, 띄어쓰기로 구분
- 고정댓글: 시청자에게 결말에 대한 의견을 묻는 한 줄 질문
반드시 JSON만 출력: {"titles": ["..."], "description": "...", "hashtags": "#... #...", "pinned_comment": "..."}"""

IDEA_SYSTEM = """너는 한국 유튜브 쇼츠 채널 기획자다. (허구 썰, 기이한 실화, 과학 사실, 자연현상 모두 다룬다)
조회수가 잘 나오는 소재(공감, 궁금증, 반전, 감동, 소름, 놀라움)를 골라
첫 줄 훅이 강하게 나올 수 있는 주제를 만든다. 사실 기반 종류이면 실제로 존재하고 널리 알려진 사건·현상·사실만 고른다 (지어내지 않는다).
각 주제는 25자 이내 한 줄로, 결말은 밝히지 않는다.
명화면 '그림 제목 - 화가(제작 연도)' 형식, 이야기가 있는 유명 그림 위주(한국 명화 포함). 그림 이미지를 쓰려면 화가가 1955년 이전 사망이어야 하므로 그런 작품 위주.
올드 팝송이면 '노래 제목(발표 연도) - 가수/작곡가' 형식. 소재에 '가사'가 들어가면 1929년 이전 발표곡만, '실화'면 극적인 인생을 산 가수·작곡가 위주(시대 무관).
반드시 JSON만 출력: {"ideas": ["주제1", "주제2", ...]}"""


def _artist_recent(artwork):
    """화가 사후 70년 미만이면 True (그림 이미지 사용 불가)"""
    if not isinstance(artwork, dict):
        return False
    try:
        return int(str(artwork.get("artist_death", "")).strip()[:4]) >= ART_SAFE_DEATH_YEAR
    except ValueError:
        return False


def cat_info(category):
    factual, topics = CATEGORIES.get(category, CATEGORIES["허구 단편소설"])
    return factual, topics


def systems_for(category):
    factual, _ = cat_info(category)
    if category == SONG_CATEGORY:
        return SONG_SYSTEM, SONG_MULTI_SYSTEM
    if category == ART_CATEGORY:
        return ART_SYSTEM, ART_MULTI_SYSTEM
    return (FACT_SYSTEM, FACT_MULTI_SYSTEM) if factual else (STORY_SYSTEM, MULTI_SYSTEM)


LONGFORM_SYSTEM = """너는 유튜브 롱폼(8~15분) 채널의 구성작가다. 여러 개의 짧은 이야기(챕터)를 하나의 영상으로 묶는다.
아래 챕터 제목·본문을 읽고 전체 영상의 제목, 오프닝, 클로징, 다듬은 챕터 제목을 만든다.
- 전체 제목: 25자 이내, 궁금증 + 숫자 (예: "세계를 뒤흔든 미제사건 7가지")
- 오프닝: 2~4문장, 첫 문장은 가장 강한 훅, 마지막은 "끝까지 보면 ..." 식의 기대감. 문단 사이 빈 줄.
- 클로징: 2~3문장, 가장 인상적인 챕터를 다시 한 줄로 되짚고, 댓글 질문 + 구독 유도. 문단 사이 빈 줄.
- 챕터 제목: 각 12자 이내, 번호 없이 (프로그램이 번호를 붙임)
반드시 JSON만 출력: {"title": "전체 제목", "opening": "오프닝", "closing": "클로징", "chapter_titles": ["..."]}"""


TRANSLATE_SYSTEM = """You are a professional localizer for YouTube Shorts scripts. Translate the Korean script into {lang_name} so that it reads like a native-written viral short — natural, punchy, same emotional beats — not a literal translation.
Rules:
- Keep the exact paragraph structure: one paragraph per block, blank line between blocks. Same number of blocks, same order.
- Lines that start with "[사진:" (photo lines) must be copied EXACTLY as-is, unchanged.
- Lines that start with "## " are chapter titles: keep "## " and translate the title. Keep a leading number like "3. " if present.
- Lines that start with "♪ " are original song lyrics in their original language: copy them unchanged. Translate only the explanation line below each.
- Keep names, years and numbers accurate. Use the {lang_name} spelling for proper nouns.
- Keep each line short enough for a phone screen (about 45 characters in English, 25 characters in Japanese per line is ideal).
- The hook (first line) must stop a scroller; the last line should invite comments.
Output JSON only: {{"title": "translated title (max 40 chars)", "story": "translated script", "titles": ["5 alternative upload titles"], "description": "2-3 line upload description", "hashtags": "#tag1 #tag2 ... (8-12)", "pinned_comment": "one-line question for viewers"}}"""


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


def explain_api_error(code, body, who=""):
    """API 오류를 쉬운 한국어로"""
    msg = body
    try:
        j = json.loads(body)
        msg = (j.get("error") or {}).get("message") or body
    except Exception:
        pass
    low = (msg or "").lower()
    if "api key not valid" in low or "api_key_invalid" in low or "invalid api key" in low or "incorrect api key" in low:
        tip = f"{who} API 키가 올바르지 않습니다. 키를 다시 복사해서 붙여넣으세요 (앞뒤 공백·줄바꿈 없이)."
    elif "expired" in low:
        tip = f"{who} API 키가 만료됐습니다. 새 키를 만들어 넣으세요."
    elif code == 429 or "quota" in low or "rate limit" in low or "resource_exhausted" in low:
        tip = f"{who} 사용량 한도를 넘었습니다 (무료 한도 포함). 잠시 뒤 다시 하거나 다른 성우·엔진을 쓰세요."
    elif code == 404 or "not found" in low or "is not supported" in low:
        tip = f"{who} 모델 이름을 찾을 수 없습니다. AI 엔진/나레이션 탭의 모델 이름을 확인하세요."
    elif code in (401, 403) or "permission" in low or "billing" in low:
        tip = f"{who} 권한이 없습니다. 키 권한이나 결제 설정(유료 기능)을 확인하세요."
    elif "location" in low or "region" in low:
        tip = f"{who} 이 지역에서는 이 기능을 쓸 수 없습니다."
    else:
        tip = f"{who} 요청이 거절됐습니다 (HTTP {code})."
    return tip.strip() + "\n\n[상세] " + (msg or "")[:400]


class APIError(RuntimeError):
    def __init__(self, short, detail=""):
        super().__init__(short + ("\n\n" + detail if detail else ""))
        self.short = short


def _http_json(url, payload, headers, timeout=180, who=""):
    import urllib.request, urllib.error
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"),
                                 headers={"Content-Type": "application/json", **headers}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "ignore")[:1500]
        full = explain_api_error(e.code, body, who)
        raise APIError(full.split("\n\n")[0], full.split("\n\n", 1)[1] if "\n\n" in full else "")
    except urllib.error.URLError as e:
        raise APIError(f"{who} 서버에 연결하지 못했습니다 (인터넷 연결 확인)", str(e.reason)[:200])


def check_api_key(kind, key):
    """키 확인: 모델 목록을 불러와 본다 → (성공 여부, 메시지)"""
    import urllib.request, urllib.error
    key = (key or "").strip()
    if not key:
        return False, "키가 비어 있습니다."
    if kind == "gemini":
        req = urllib.request.Request("https://generativelanguage.googleapis.com/v1beta/models?pageSize=200", headers={"x-goog-api-key": key})
    else:
        req = urllib.request.Request("https://api.openai.com/v1/models", headers={"Authorization": "Bearer " + key})
    who = "Gemini" if kind == "gemini" else "ChatGPT"
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return False, explain_api_error(e.code, e.read().decode("utf-8", "ignore")[:1500], who)
    except urllib.error.URLError as e:
        return False, f"{who} 서버에 연결하지 못했습니다: {e.reason}"
    if kind == "gemini":
        names = [m_.get("name", "").split("/")[-1] for m_ in data.get("models", [])]
        tts = [n for n in names if "tts" in n]
        txt = [n for n in names if n.startswith("gemini-") and "tts" not in n and ("flash" in n or "pro" in n)]
        return True, (f"✅ Gemini 키 정상 (모델 {len(names)}개)\n음성 모델: {', '.join(tts[:4]) or '없음 - 이 키로는 Gemini 음성을 쓸 수 없음'}\n"
                      f"글 모델 예: {', '.join(txt[:4])}")
    names = [m_.get("id", "") for m_ in data.get("data", [])]
    tts = [n for n in names if "tts" in n]
    return True, f"✅ ChatGPT 키 정상 (모델 {len(names)}개)\n음성 모델: {', '.join(tts[:4]) or '없음'}"


def ask_openai(key, model, system, user):
    """ChatGPT API (채팅 기록에 남지 않음)"""
    out = _http_json("https://api.openai.com/v1/chat/completions",
                     {"model": model or "gpt-4o-mini", "temperature": 0.4,
                      "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]},
                     {"Authorization": "Bearer " + key}, who="ChatGPT")
    return out["choices"][0]["message"]["content"]


def ask_gemini(key, model, system, user):
    """Gemini API"""
    m = model or "gemini-2.5-flash"
    out = _http_json(f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent",
                     {"system_instruction": {"parts": [{"text": system}]},
                      "contents": [{"role": "user", "parts": [{"text": user}]}],
                      "generationConfig": {"temperature": 0.4}}, {"x-goog-api-key": key}, who="Gemini")
    return out["candidates"][0]["content"]["parts"][0]["text"]


def pick_engine(s, key="trans_engine"):
    """쓸 AI 고르기 → ('chatgpt'|'gemini'|'claude', 설명)"""
    want = s.get(key, "")
    ok_key = (s.get("openai_key") or os.environ.get("OPENAI_API_KEY", "")).strip()
    gk = (s.get("gemini_key") or os.environ.get("GEMINI_API_KEY", "")).strip()
    if want == "ChatGPT":
        if not ok_key:
            raise RuntimeError("ChatGPT API 키가 없습니다. 번역 탭에 키를 넣거나 OPENAI_API_KEY 환경변수를 설정하세요.")
        return "chatgpt", "ChatGPT " + (s.get("openai_model") or "gpt-4o-mini")
    if want == "Gemini":
        if not gk:
            raise RuntimeError("Gemini API 키가 없습니다. 번역 탭에 키를 넣거나 GEMINI_API_KEY 환경변수를 설정하세요.")
        return "gemini", "Gemini " + (s.get("gemini_model") or "gemini-2.5-flash")
    if want == "Claude":
        return "claude", "Claude"
    if ok_key:
        return "chatgpt", "ChatGPT " + (s.get("openai_model") or "gpt-4o-mini")
    if gk:
        return "gemini", "Gemini " + (s.get("gemini_model") or "gemini-2.5-flash")
    return "claude", "Claude"


def ask_engine_json(s, claude_model, system, user, key="trans_engine"):
    eng, _ = pick_engine(s, key)
    if eng == "chatgpt":
        key = (s.get("openai_key") or os.environ.get("OPENAI_API_KEY", "")).strip()
        return parse_json(ask_openai(key, s.get("openai_model"), system, user))
    if eng == "gemini":
        key = (s.get("gemini_key") or os.environ.get("GEMINI_API_KEY", "")).strip()
        return parse_json(ask_gemini(key, s.get("gemini_model"), system, user))
    return ask_json(claude_model, system, user)


SCRIPT_ENGINE = {"s": None}   # 대본 작성에 쓸 설정 (App 이 작업 전에 넣음)


def ask_script_json(model, system, user):
    """대본 작성·심사용: 'AI 엔진' 탭의 '대본 작성 AI' 설정을 따름 (웹 검색은 항상 Claude)"""
    s_ = SCRIPT_ENGINE.get("s")
    if s_ and s_.get("script_engine") and s_.get("script_engine") != "Claude":
        return ask_engine_json(s_, model, system, user, "script_engine")
    return ask_json(model, system, user)


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


# ---------------- ffmpeg (MP4 만들기) ----------------
_FFMPEG = None


def get_ffmpeg():
    """MP4 압축 프로그램(ffmpeg) 위치. 없으면 imageio-ffmpeg 를 자동 설치"""
    global _FFMPEG
    if _FFMPEG and os.path.exists(_FFMPEG):
        return _FFMPEG
    for attempt in (1, 2):
        try:
            import imageio_ffmpeg
            _FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
            return _FFMPEG
        except Exception:
            if attempt == 1:
                ok, _ = pip_install("imageio-ffmpeg")
                importlib.invalidate_caches()
                if not ok:
                    break
    sys_ff = shutil.which("ffmpeg")
    if sys_ff:
        _FFMPEG = sys_ff
        return _FFMPEG
    raise RuntimeError("MP4 압축 프로그램(ffmpeg)을 찾지 못했고 자동 설치도 실패했습니다.\n\n"
                       "명령 프롬프트(cmd)에서 아래 한 줄을 실행한 뒤 프로그램을 다시 켜세요:\n\n"
                       f'"{sys.executable}" -m pip install imageio-ffmpeg')


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
# 위키미디어는 프로그램 이름·연락처가 있는 User-Agent 를 요구함 (없으면 429/403으로 거부)
UA = "ShortsNovelMaker/1.0 (https://github.com/KnagByeongju-123/youtubeshot; personal YouTube Shorts tool) Python-urllib"
IMG_WIDTH = 1600   # 받을 사진 폭 (원본은 수십 MB라 축소본으로 받음)


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
    """위키미디어 주소를 '1600px 축소본' 주소로 통일 (원본·파일 페이지·썸네일 주소 모두 처리)"""
    from urllib.parse import quote, unquote
    url = url.strip()
    name = None
    m = re.match(r"https?://(?:commons\.wikimedia\.org|[\w-]+\.wikipedia\.org)/wiki/(?:File|파일|Datei|Fichier|Archivo|Fichier):([^?#]+)", url)
    if m:
        name = m.group(1)
    m = re.match(r"https?://upload\.wikimedia\.org/wikipedia/(?:commons|[a-z]{2,3})/thumb/[0-9a-f]/[0-9a-f]{2}/([^/?#]+)/\d+px-[^/?#]+", url)
    if m:
        name = m.group(1)
    m = re.match(r"https?://upload\.wikimedia\.org/wikipedia/(?:commons|[a-z]{2,3})/[0-9a-f]/[0-9a-f]{2}/([^/?#]+)$", url)
    if m:
        name = m.group(1)
    if name:
        return "https://commons.wikimedia.org/wiki/Special:FilePath/" + quote(unquote(name)) + f"?width={IMG_WIDTH}"
    return url


_last_dl = [0.0]


def download_image(url, media_dir, stem=None):
    """사진 내려받기. 위키미디어 429(너무 자주 요청)면 잠시 기다렸다 최대 3번 재시도"""
    import urllib.request, urllib.error
    target = fix_image_url(url)
    data = None
    for attempt in range(3):
        gap = time.time() - _last_dl[0]
        if gap < 1.0:                      # 요청 사이 최소 1초 간격
            time.sleep(1.0 - gap)
        _last_dl[0] = time.time()
        req = urllib.request.Request(target, headers={"User-Agent": UA, "Accept": "image/*,*/*;q=0.8"})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                data = r.read(25 * 1024 * 1024 + 1)
            break
        except urllib.error.HTTPError as e:
            if e.code in (429, 503) and attempt < 2:
                wait = 3.0 * (attempt + 1)
                try:
                    wait = max(wait, float(e.headers.get("Retry-After", 0)))
                except (TypeError, ValueError):
                    pass
                time.sleep(min(wait, 20))
                continue
            if e.code == 429:
                raise ValueError("위키미디어가 요청을 잠시 막음(429) - 1~2분 뒤 'AI 근거사진 찾기'를 다시 눌러보세요")
            raise
    if data is None:
        raise ValueError("내려받기 실패")
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


def crop_details(full_path, details, media_dir, log, limit=3):
    """그림 전체 사진에서 details 의 상자(비율)를 잘라 확대 사진으로 저장 → [{path, caption, credit, after}]"""
    im = load_media_image(full_path)
    if im is None:
        return []
    out = []
    for d in (details or [])[:limit]:
        try:
            x, y, w, h = [float(v) for v in d.get("box", [])]
        except (TypeError, ValueError):
            continue
        x, y = min(max(x, 0), 0.95), min(max(y, 0), 0.95)
        w, h = min(max(w, 0.05), 1 - x), min(max(h, 0.05), 1 - y)
        box = (int(x * im.width), int(y * im.height), int((x + w) * im.width), int((y + h) * im.height))
        c = im.crop(box)
        if c.width < 40 or c.height < 40:
            continue
        if c.width < 900:   # 너무 작으면 키워서 또렷하게
            k = 900 / c.width
            c = c.resize((int(c.width * k), int(c.height * k)), Image.LANCZOS)
        path = save_media_image(c, media_dir)
        cap = str(d.get("caption") or "부분 확대")
        out.append({"path": path, "caption": "확대: " + cap, "credit": "원작 부분 확대", "after": d.get("after", "")})
        log(f"  확대 사진: {cap}")
    return out


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
    """본문의 [사진N] 자리표시를 실제 사진 줄로 바꾸고, 자리표시가 없는 사진은 알맞은 곳에 끼움 (최대 5장)"""
    photos = list(photos or [])[:5]
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
                sc = min(maxw / im.width, H * min(0.7, max(0.15, s["photo_h"])) / im.height)
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
        if para.startswith("## "):          # 챕터 제목 (롱폼)
            head = para[3:].strip()
            y += int(s["font_size"] * 1.2)
            paras.append((y, "## " + head))
            fch = load_font(s["title_font_path"] or s["font_path"], int(s["title_size"] * 0.9))
            d_line_y = y + int(fch.size * 1.35) * len(wrap(head, fch, maxw))
            for ln in wrap(head, fch, maxw):
                items.append((y, ln, fch, s["title_color"], "center"))
                y += int(fch.size * 1.35)
            items.append((d_line_y, "─" * 12, fcap, tuple(hex_rgb(s["accent_color"])) + (200,), "center"))
            y = d_line_y + int(fcap.size * 1.6) + int(s["font_size"] * 0.6)
            continue
        paras.append((y, para))
        is_quote = s["quote_color"] == "on" and (para[:1] in "\"“'‘" or para.startswith("♪"))
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

    def __init__(self, title, story, s, narration=None):
        """narration: [(문단 인덱스, 소리 배열, 길이초)] - 있으면 스크롤이 읽는 속도에 맞춰 움직임"""
        self.s = s
        self.title = title
        self.narration = narration or []
        rgb, a, self.paras = build_text_layer(title, story, s)
        self.layer_h = rgb.shape[0]
        self.dist = self.layer_h - H
        pad = np.zeros((1, W), np.float32)
        self.a = np.concatenate([a, pad])                                   # 마지막에 투명 1줄 (보간용)
        self.prem = np.concatenate([rgb * a[..., None], pad[..., None].repeat(3, 2)])
        del rgb
        self.intro = s["intro_sec"] if title.strip() else 0
        self.hs, self.he = s["hold_start"], s["hold_end"]
        self.keys = None            # 나레이션 타임라인 [(t, y)]
        self.narr_at = []           # [(시작 시각, 소리 배열)]
        if self.narration and self.dist > 0:
            self._build_timeline()
        elif s["target_sec"] > 0 and self.dist > 0:
            self.scroll_t = max(1.0, s["target_sec"] - self.intro - self.hs - self.he)
        else:
            self.scroll_t = self.dist / max(1.0, s["speed"])
        self.duration = self.intro + self.hs + self.scroll_t + self.he
        # 가속/감속 구간 (스크롤 시간의 15%, 최대 1.2초)
        self.ramp = min(1.2, self.scroll_t * 0.15) if s["ease"] == "on" else 0.0
        self.vmax = self.dist / max(1e-6, self.scroll_t - self.ramp) if self.dist > 0 else 0.0
        self.speed = self.vmax if not self.keys else (self.dist / max(1.0, self.scroll_t))
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

    def focus_line(self):
        return H * (self.s["focus_y"] if self.s["focus"] == "on" else 0.55)

    def _build_timeline(self):
        """나레이션 길이에 맞춰 '문단 i는 T_i 초에 읽는 줄에 온다'는 지점들을 만든다"""
        s, line = self.s, self.focus_line()
        gap = max(0.0, float(s.get("narr_gap", 0.5)))
        photo_pause = max(0.0, float(s.get("narr_photo_pause", 1.5)))
        durs = {i: d for i, _, d in self.narration}
        keys, t = [], 0.0
        prev_y = None
        for i, (py, text) in enumerate(self.paras):
            y = max(0.0, min(float(self.dist), py - line))
            if prev_y is not None and y > prev_y:
                # 문단 사이에 사진이 끼어 있으면(간격이 크면) 보는 시간 추가
                if (y - prev_y) > H * 0.25:
                    t += photo_pause
            y = max(y, prev_y or 0.0)
            keys.append((t, y))
            d = durs.get(i, max(1.2, len(text) * 0.11))
            t += d + (1.2 if text.startswith("## ") else gap)
            prev_y = y
        # 마지막: 끝까지 스크롤
        if keys and keys[-1][1] < self.dist:
            keys.append((t, float(self.dist)))
        else:
            t = max(t, keys[-1][0] + 0.5) if keys else 1.0
        self.keys = keys
        self.scroll_t = max(1.0, t)
        base = self.intro + self.hs
        self.narr_at = [(base + keys[i][0] if i < len(keys) else base, clip) for i, clip, _ in self.narration]

    def _timeline_offset(self, t):
        """지점들 사이를 부드럽게(단조 3차) 이어서 위치 계산"""
        ks = self.keys
        if t <= ks[0][0]:
            return ks[0][1]
        if t >= ks[-1][0]:
            return ks[-1][1]
        if not hasattr(self, "_tl"):
            xs = np.array([k[0] for k in ks], float)
            ys = np.array([k[1] for k in ks], float)
            dx = np.diff(xs); dy = np.diff(ys)
            dx[dx <= 0] = 1e-6
            m = dy / dx
            d = np.zeros(len(xs))
            for i in range(1, len(xs) - 1):
                if m[i - 1] * m[i] > 0:
                    d[i] = 2 / (1 / m[i - 1] + 1 / m[i])   # Fritsch-Carlson (단조 유지)
            self._tl = (xs, ys, m, d)
        xs, ys, m, d = self._tl
        i = int(np.searchsorted(xs, t) - 1)
        i = max(0, min(i, len(xs) - 2))
        h = xs[i + 1] - xs[i]
        u = (t - xs[i]) / h
        h00 = 2 * u ** 3 - 3 * u ** 2 + 1; h10 = u ** 3 - 2 * u ** 2 + u
        h01 = -2 * u ** 3 + 3 * u ** 2; h11 = u ** 3 - u ** 2
        return float(h00 * ys[i] + h10 * h * d[i] + h01 * ys[i + 1] + h11 * h * d[i + 1])

    def para_time(self, idx):
        """문단 idx 가 읽는 줄에 오는 시각 (타임스탬프·효과음용)"""
        if self.keys and idx < len(self.keys):
            return self.intro + self.hs + self.keys[idx][0]
        py = self.paras[idx][0]
        line = self.focus_line()
        for i in range(int(self.duration * 20)):
            t = i / 20
            if t >= self.intro and py - self.offset(t) <= line + 2:
                return t
        return self.intro + self.hs + self.scroll_t

    def chapter_times(self):
        """[(시각, 챕터 제목)] - 롱폼 타임스탬프용"""
        return [(self.para_time(i), text[3:].strip()) for i, (_, text) in enumerate(self.paras) if text.startswith("## ")]

    def find_reveal(self):
        """반전 문단(마지막 문단, 마지막이 질문이면 그 앞)이 읽는 줄에 닿는 시각"""
        if not self.paras or self.dist <= 0:
            return None
        idx = -2 if len(self.paras) >= 2 and self.paras[-1][1].rstrip().endswith("?") else -1
        py = self.paras[idx][0]
        line = self.focus_line()
        if self.keys:
            t = self.para_time(len(self.paras) + idx)
            return t if t >= self.intro + 1.0 else None
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
        if self.keys:
            return self._timeline_offset(t)
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


class SubtitleRenderer:
    """자막형: 위 큰 제목 + 가운데 사진(천천히 확대) + 아래 자막. 문단마다 자막이 바뀌고 사진 줄에서 사진이 바뀜.
    Renderer 와 같은 인터페이스(duration, frame, frame_preview, thumbnail, reveal_t, narr_at, keys, chapter_times ...)"""

    def __init__(self, title, story, s, narration=None):
        self.s, self.title = s, title
        self.narration = narration or []
        self.keys = True if self.narration else None
        durs = {i: d for i, _, d in self.narration}
        clips = {i: c for i, c, _ in self.narration}
        gap = max(0.0, float(s.get("narr_gap", 0.5)))
        spc = max(0.04, float(s.get("sec_per_char", 0.12)))
        self.intro = s["intro_sec"] if title.strip() else 0
        self.hs, self.he = s["hold_start"], s["hold_end"]
        # 문단 → 구간
        self.images, segs, idx, cur_img = [], [], 0, -1
        paras_for_narr = narration_paras(story)
        for para in story.replace("\r", "").split("\n"):
            para = para.strip()
            if not para:
                continue
            med = parse_media(para)
            if med:
                im = load_media_image(med[0])
                if im is not None:
                    self.images.append((im, med[1]))
                    cur_img = len(self.images) - 1
                continue
            if PH_RE.match(para):
                continue
            para = PH_INLINE_RE.sub("", para).strip()
            if not para:
                continue
            kind = "chapter" if para.startswith("## ") else ("lyric" if para.startswith("♪") else "text")
            text = para[3:].strip() if kind == "chapter" else para
            d = durs.get(idx)
            if d is None:
                d = max(1.6, len(tts_clean(text)) * spc + 0.6)
            d = d + (1.0 if kind == "chapter" else gap)
            segs.append({"i": idx, "kind": kind, "text": text, "img": cur_img, "dur": d})
            idx += 1
        if self.images:   # 첫 사진이 나오기 전 문단들도 첫 사진을 보여줌 (빈 화면 방지)
            for sg in segs:
                if sg["img"] < 0:
                    sg["img"] = 0
        # 가사(♪) 바로 다음 문단(해석)은 같은 화면에: 가사는 사진 위, 해석은 자막
        self.segs = []
        k = 0
        while k < len(segs):
            sg = segs[k]
            if sg["kind"] == "lyric" and k + 1 < len(segs) and segs[k + 1]["kind"] == "text":
                nxt = segs[k + 1]
                sg = dict(sg, sub=nxt["text"], dur=sg["dur"] + nxt["dur"], i2=nxt["i"])
                k += 1
            self.segs.append(sg)
            k += 1
        t = self.intro + self.hs
        for sg in self.segs:
            sg["t0"] = t
            t += sg["dur"]
        self.scroll_t = max(1.0, t - self.intro - self.hs)
        self.duration = self.intro + self.hs + self.scroll_t + self.he
        self.dist, self.speed = 0, 0.0
        self.paras = [(0, (sg["text"] if sg["kind"] != "chapter" else "## " + sg["text"])) for sg in self.segs]
        self.narr_at = []
        for sg in self.segs:
            if sg["i"] in clips:
                self.narr_at.append((sg["t0"], clips[sg["i"]]))
            if "i2" in sg and sg["i2"] in clips:
                self.narr_at.append((sg["t0"] + durs.get(sg["i"], 0) + gap, clips[sg["i2"]]))
        # 레이아웃
        self.port = H > W
        m = int(W * 0.045)
        if self.port:
            self.head_box = (m, int(H * 0.06), W - m, int(H * 0.23))
            self.img_box = (m, int(H * 0.25), W - m, int(H * 0.74))
            self.sub_box = (m, int(H * 0.76), W - m, int(H * 0.93))
        else:
            self.head_box = (m, int(H * 0.04), W - m, int(H * 0.19))
            self.img_box = (int(W * 0.18), int(H * 0.21), int(W * 0.82), int(H * 0.80))
            self.sub_box = (m, int(H * 0.82), W - m, int(H * 0.97))
        self.bg = Background(s, self.duration)
        self.head_layer = self._make_head()
        self._sub_cache, self._img_cache = {}, {}
        self.accent = np.array(hex_rgb(s["accent_color"]), np.float32)
        self.card = None
        if self.intro > 0:
            ft = load_font(s["title_font_path"] or s["font_path"], int(s["title_size"] * 1.15))
            self.card = build_card([title.strip()], ft, s["title_color"], s, H * 0.46)
        self.outro = s["outro_sec"] if s["outro_text"].strip() else 0
        fo = load_font(s["font_path"], int(s["font_size"] * 0.85))
        self.outro_layer = build_card([s["outro_text"].strip()], fo, s["accent_color"], s, H * 0.72) if self.outro > 0 else None
        self.reveal_t = self.find_reveal()

    # --- 제목 ---
    def _make_head(self):
        s = self.s
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        if not self.title.strip():
            return layer
        d = ImageDraw.Draw(layer)
        x0, y0, x1, y1 = self.head_box
        size = int(s["head_size"])
        font = load_font(s["title_font_path"] or s["font_path"], size)
        lines = wrap(self.title.strip(), font, x1 - x0)
        while len(lines) > 2 and size > 40:
            size -= 6
            font = load_font(s["title_font_path"] or s["font_path"], size)
            lines = wrap(self.title.strip(), font, x1 - x0)
        lines = lines[:2]
        lh = int(size * 1.2)
        y = y0 + ((y1 - y0) - lh * len(lines)) // 2
        st = s["head_style"]
        for i, ln in enumerate(lines):
            if st == "노란색":
                col = "#FFE135"
            elif st == "흰색+하늘색":
                col = "#FFFFFF" if i == 0 else "#7FDBFF"
            elif st == "강조색":
                col = s["accent_color"]
            else:
                col = "#FFFFFF"
            x = x0 + ((x1 - x0) - font.getlength(ln)) / 2
            d.text((x, y), ln, font=font, fill=col, stroke_width=max(3, size // 14), stroke_fill="#000000")
            y += lh
        return layer

    # --- 자막 ---
    def _sub_layer(self, key, text, lyric=None):
        if key in self._sub_cache:
            return self._sub_cache[key]
        s = self.s
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        x0, y0, x1, y1 = self.sub_box
        size = int(s["sub_size"])
        font = load_font(s["title_font_path"] or s["font_path"], size)
        lines = wrap(text, font, x1 - x0)
        while len(lines) > 3 and size > 34:
            size -= 4
            font = load_font(s["title_font_path"] or s["font_path"], size)
            lines = wrap(text, font, x1 - x0)
        lh = int(size * 1.3)
        y = y1 - lh * len(lines)
        st = s["sub_style"]
        col = "#FFE135" if st.startswith("노란") else "#FFFFFF"
        if st.startswith("검은띠"):
            d.rectangle([x0 - 10, y - 14, x1 + 10, y1 + 6], fill=(0, 0, 0, 185))
        for ln in lines:
            x = x0 + ((x1 - x0) - font.getlength(ln)) / 2
            d.text((x, y), ln, font=font, fill=col, stroke_width=0 if st.startswith("검은띠") else max(3, size // 14), stroke_fill="#000000")
            y += lh
        if lyric:   # 가사 원문은 사진 위에 노란 글자로
            fl = load_font(s["title_font_path"] or s["font_path"], int(size * 0.95))
            ix0, iy0, ix1, iy1 = self.img_box
            ll = wrap(lyric.lstrip("♪").strip(), fl, ix1 - ix0 - 40)
            ly = iy1 - int(fl.size * 1.3) * len(ll) - 30
            for ln in ll:
                x = ix0 + ((ix1 - ix0) - fl.getlength(ln)) / 2
                d.text((x, ly), ln, font=fl, fill="#FFE135", stroke_width=max(3, fl.size // 12), stroke_fill="#000000")
                ly += int(fl.size * 1.3)
        self._sub_cache[key] = layer
        return layer

    # --- 사진 ---
    def _img_frame(self, idx, prog):
        """idx 사진을 사진 상자에 꽉 채워(가운데 잘라) 넣고 prog(0~1) 만큼 확대"""
        x0, y0, x1, y1 = self.img_box
        bw, bh = x1 - x0, y1 - y0
        if idx not in self._img_cache:
            im = self.images[idx][0]
            sc = max(bw / im.width, bh / im.height) * 1.12
            big = im.resize((int(im.width * sc) + 1, int(im.height * sc) + 1), Image.LANCZOS)
            mask = Image.new("L", (bw, bh), 0)
            ImageDraw.Draw(mask).rounded_rectangle([0, 0, bw - 1, bh - 1], radius=int(self.s["img_radius"]), fill=255)
            self._img_cache[idx] = (big, mask)
        big, mask = self._img_cache[idx]
        z = 1.0 + (0.12 * smoothstep(prog) if self.s["img_zoom"] == "on" else 0.06)
        cw, ch = bw * 1.12 / z, bh * 1.12 / z
        l, t = (big.width - cw) / 2, (big.height - ch) / 2
        crop = big.transform((bw, bh), Image.EXTENT, (l, t, l + cw, t + ch), Image.BILINEAR)
        return crop, mask

    def seg_at(self, t):
        for sg in self.segs:
            if t < sg["t0"] + sg["dur"]:
                return sg
        return self.segs[-1] if self.segs else None

    def _compose_pil(self, t):
        bg = Image.fromarray(np.clip(self.bg.frame(t), 0, 255).astype(np.uint8)).convert("RGBA")
        if self.card is not None and t < self.intro:
            k = smoothstep(t / 0.5) * smoothstep((self.intro - t) / 0.5)
            a = (self.card[1] * k)[..., None]
            arr = np.asarray(bg).astype(np.float32)[..., :3]
            out = arr + (self.card[0] - arr) * a
            return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))
        sg = self.seg_at(t)
        canvas = bg
        if sg is not None:
            if sg["img"] >= 0 and self.images:
                # 같은 사진이 보이는 전체 시간 기준으로 확대 진행
                same = [x for x in self.segs if x["img"] == sg["img"]]
                t_a, t_b = same[0]["t0"], same[-1]["t0"] + same[-1]["dur"]
                prog = (t - t_a) / max(0.1, t_b - t_a)
                crop, mask = self._img_frame(sg["img"], prog)
                canvas.paste(crop, (self.img_box[0], self.img_box[1]), mask)
            canvas.alpha_composite(self.head_layer)
            if sg["kind"] == "chapter":
                lay = self._sub_layer(("ch", sg["i"]), "— " + sg["text"] + " —")
            elif sg["kind"] == "lyric":
                lay = self._sub_layer(("ly", sg["i"]), sg.get("sub", ""), lyric=sg["text"])
            else:
                lay = self._sub_layer(("tx", sg["i"]), sg["text"])
            canvas.alpha_composite(lay)
        else:
            canvas.alpha_composite(self.head_layer)
        out = canvas.convert("RGB")
        if self.outro_layer is not None and t > self.duration - self.outro:
            k = smoothstep((t - (self.duration - self.outro)) / 0.6)
            arr = np.asarray(out).astype(np.float32)
            a = (self.outro_layer[1] * k)[..., None]
            out = Image.fromarray(np.clip(arr + (self.outro_layer[0] - arr) * a, 0, 255).astype(np.uint8))
        if self.s["progress_bar"] == "on":
            d = ImageDraw.Draw(out)
            d.rectangle([0, 0, int(W * min(1, t / self.duration)), 7], fill=tuple(int(v) for v in self.accent))
        return out

    def frame(self, t):
        return np.asarray(self._compose_pil(t)).copy()

    def frame_preview(self, t):
        return np.asarray(self._compose_pil(t).resize((PREVIEW_W, PREVIEW_H), Image.BILINEAR)).copy()

    def thumbnail(self):
        t = self.segs[0]["t0"] + 0.2 if self.segs else 0.1
        return self._compose_pil(t)

    def para_time(self, idx):
        return self.segs[idx]["t0"] if idx < len(self.segs) else self.duration

    def chapter_times(self):
        return [(sg["t0"], sg["text"]) for sg in self.segs if sg["kind"] == "chapter"]

    def find_reveal(self):
        texts = [sg for sg in self.segs if sg["kind"] != "chapter"]
        if len(texts) < 2:
            return None
        sg = texts[-2] if texts[-1]["text"].rstrip().endswith("?") else texts[-1]
        return sg["t0"] if sg["t0"] >= self.intro + 1.0 else None

    def offset(self, t):
        return 0.0


def make_renderer(title, story, s, narration=None):
    if s.get("layout", "").startswith("자막형"):
        return SubtitleRenderer(title, story, s, narration)
    return Renderer(title, story, s, narration)


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


def gen_pad(n, rng, mood="warm", chord_sec=8.0, bright=3400):
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


NOTE_RE = re.compile(r"^([A-Ga-g])([#b♯♭]?)(\d)$")
NOTE_BASE = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}


def parse_melody(text):
    """'C4:1 D#4:0.5 R:1' → [(midi 또는 None, 박자)]. 음표가 8개 미만이면 None"""
    notes = []
    for tok in re.split(r"[\s,]+", (text or "").strip()):
        if not tok:
            continue
        name, _, beat = tok.partition(":")
        try:
            b = float(beat) if beat else 1.0
        except ValueError:
            continue
        b = max(0.125, min(4.0, b))
        if name.upper() in ("R", "REST", "-"):
            notes.append((None, b))
            continue
        m = NOTE_RE.match(name.strip())
        if not m:
            continue
        acc = m.group(2)
        midi = 12 * (int(m.group(3)) + 1) + NOTE_BASE[m.group(1).upper()] + (1 if acc in ("#", "♯") else 0) - (1 if acc in ("b", "♭") else 0)
        if 36 <= midi <= 96:
            notes.append((midi, b))
    return notes if sum(1 for n in notes if n[0] is not None) >= 8 else None


def _melody_chords(notes):
    """멜로디 음들로 조성을 추정해 단순한 반주 화음(I-IV-V-I-vi-IV-V-I) 만들기"""
    pcs = [n[0] % 12 for n in notes if n[0] is not None]
    hist = np.bincount(pcs, minlength=12).astype(float)
    major = np.array([1, 0, 1, 0, 1, 1, 0, 1, 0, 1, 0, 1], float)
    key = int(max(range(12), key=lambda k: (np.roll(major, k) * hist).sum()))
    root = 48 + key
    I = [root, root + 7, root + 12, root + 16, root + 19]
    IV = [root + 5, root + 12, root + 17, root + 21, root + 24]
    V = [root + 7, root + 14, root + 19, root + 23, root + 26]
    vi = [root + 9, root + 16, root + 21, root + 24, root + 28]
    return [I, IV, V, I, vi, IV, V, I]


def gen_melody_box(n, rng, melody, bpm=90):
    """노래 멜로디를 오르골로 반복 연주 + 그 조성의 은은한 패드"""
    notes = parse_melody(melody)
    if not notes:
        return gen_musicbox(n, rng, "warm", 84)
    bpm = max(50, min(160, float(bpm or 90)))
    beat = 60.0 / bpm
    PROGS["_song"] = _melody_chords(notes)
    pad = gen_pad(n, rng, "_song", 8 * beat, 1500) * 0.3
    mel = np.zeros((n, 2), np.float32)
    shift = 12 if max(m_ for m_, _ in notes if m_ is not None) < 72 else 0   # 오르골답게 높은 음역으로
    cache, t = {}, 1.0
    while t < n / SR - 1.5:
        for midi, b in notes:
            if t >= n / SR - 1.5:
                break
            if midi is not None:
                m = midi + shift
                if m not in cache:
                    cache[m] = pluck(midi_hz(m), min(2.2, max(0.8, b * beat * 1.6)))
                vel = 1.0 if (t / beat) % 4 < 0.05 else rng.uniform(0.6, 0.85)
                place(mel, cache[m] * vel, t, 0.5 + 0.2 * np.sin(t))
            t += b * beat
        t += beat * 2   # 한 번 돌고 두 박 쉼
    return _norm(pad + _norm(reverb(mel, rng, 2.8, 0.35)) * 0.85)


SOUND_STYLES = {
    "노래 멜로디(오르골)": lambda n, r: gen_melody_box(n, r, CURRENT_MELODY.get("melody", ""), CURRENT_MELODY.get("bpm", 90)),
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
CURRENT_MELODY = {"melody": "", "bpm": 90}   # 현재 대본의 노래 멜로디 (올드 팝송일 때 채워짐)


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
    p = subprocess.run([get_ffmpeg(), "-v", "error", "-i", path, "-f", "f32le", "-ac", "2", "-ar", str(SR), "-"],
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                       creationflags=(subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0))
    x = np.frombuffer(p.stdout, np.float32).reshape(-1, 2) if p.returncode == 0 else np.zeros((0, 2), np.float32)
    if not len(x):
        raise RuntimeError("음악 파일을 읽지 못했습니다: " + p.stderr.decode("utf-8", "ignore")[:200])
    return np.tile(x, (int(np.ceil(n / len(x))), 1))[:n].copy()


def resolve_style(s, topic):
    st = s["bgm_style"]
    st = SOUND_BY_TOPIC.get(topic, "잔잔한 패드") if st not in SOUND_STYLES else st
    if st == "노래 멜로디(오르골)" and not parse_melody(CURRENT_MELODY.get("melody", "")):
        return "슬픈 패드" if "실화" in topic else "감성 오르골"   # 멜로디가 없으면 일반 소리로
    return st


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
    narr = getattr(r, "narr_at", []) if s.get("narration", "off") == "on" else []
    if music is None and hit_t is None and not narr:
        return None
    out = np.zeros((n, 2), np.float32)
    t = np.arange(n) / SR
    if music is not None:
        rms = float(np.sqrt((music ** 2).mean())) + 1e-9
        music = music * (0.24 / rms) * max(0, s["bgm_volume"])   # 볼륨 0.5 기준 약 -18dB (작은 스피커에서도 들리게)
        g = np.minimum(1, t / 1.5) * np.clip((r.duration - t) / 2.5, 0, 1)
        if hit_t:  # 반전 직전 음악을 줄였다가 다시 올림
            a = max(0.01, hit_t - 1.2)
            b = max(a + 0.01, hit_t - 0.1)
            g = g * np.interp(t, [0, a, b, hit_t + 1.5, hit_t + 4.5, 1e9], [1, 1, 0.25, 0.25, 1, 1])
        if narr:   # 말하는 동안 음악을 낮춤 (더킹)
            duck = float(s.get("narr_duck", 0.35))
            env = np.ones(n, np.float32)
            for st, clip in narr:
                i0, i1 = int(max(0, st - 0.3) * SR), int(min(r.duration, st + len(clip) / SR + 0.3) * SR)
                env[i0:i1] = duck
            k = int(0.4 * SR)
            env = np.convolve(env, np.ones(k, np.float32) / k, mode="same")
            g = g * env
        out += music * g[:, None].astype(np.float32)
    for st, clip in narr:
        vol = max(0, float(s.get("narr_volume", 1.0)))
        i0 = int(st * SR)
        seg = clip[: max(0, n - i0)]
        if len(seg):
            out[i0:i0 + len(seg)] += seg[:, None] * vol if seg.ndim == 1 else seg * vol
    if hit_t:
        out += reveal_fx(n, hit_t, rng) * 0.4 * max(0, s["hit_volume"])
    peak = float(np.abs(out).max())
    if peak > 0.95:
        out *= 0.95 / peak
    return out


# ---------------- 나레이션 (TTS) ----------------


def tts_clean(text):
    """읽기 좋게 정리: ♪, 따옴표, 챕터 표시 제거"""
    t = text.strip()
    if t.startswith("## "):
        t = t[3:]
    t = t.lstrip("♪").strip()
    t = re.sub(r"[\"“”'‘’]", "", t)
    t = re.sub(r"\s+", " ", t)
    return t


VOICE_CACHE_FILE = os.path.join(BASE, "voices_cache.json")
VOICE_LOCALES = {"ko-KR": "한국어", "en-US": "영어(미국)", "en-GB": "영어(영국)", "ja-JP": "일본어", "openai": "ChatGPT 음성", "gemini": "Gemini 음성"}
VOICE_KO_NAMES = {"SunHi": "선히", "InJoon": "인준", "Hyunsu": "현수", "BongJin": "봉진", "GookMin": "국민", "JiMin": "지민",
                  "SeoHyeon": "서현", "SoonBok": "순복", "YuJin": "유진", "Aria": "아리아", "Guy": "가이", "Jenny": "제니",
                  "Christopher": "크리스토퍼", "Ana": "아나", "Andrew": "앤드루", "Emma": "엠마", "Brian": "브라이언",
                  "Nanami": "나나미", "Keita": "케이타", "Sonia": "소니아", "Ryan": "라이언"}


OPENAI_VOICES = [("alloy", "중성, 차분"), ("ash", "남성, 또렷"), ("ballad", "남성, 부드러움"), ("coral", "여성, 밝음"),
                 ("echo", "남성, 낮음"), ("fable", "중성, 이야기꾼"), ("nova", "여성, 친근"), ("onyx", "남성, 깊음"),
                 ("sage", "여성, 차분"), ("shimmer", "여성, 맑음"), ("verse", "남성, 다정")]
GEMINI_VOICES = [("Zephyr", "밝음"), ("Puck", "경쾌"), ("Charon", "설명형"), ("Kore", "단단함"), ("Fenrir", "들뜸"), ("Leda", "젊음"),
                 ("Orus", "단호"), ("Aoede", "산뜻"), ("Callirrhoe", "편안"), ("Autonoe", "밝음"), ("Enceladus", "숨소리"),
                 ("Iapetus", "또렷"), ("Umbriel", "편안"), ("Algieba", "부드러움"), ("Despina", "부드러움"), ("Erinome", "또렷"),
                 ("Algenib", "거친 목소리"), ("Rasalgethi", "설명형"), ("Laomedeia", "경쾌"), ("Achernar", "부드러움"),
                 ("Alnilam", "단단함"), ("Schedar", "고름"), ("Gacrux", "성숙"), ("Pulcherrima", "적극적"), ("Achird", "친근"),
                 ("Zubenelgenubi", "캐주얼"), ("Vindemiatrix", "온화"), ("Sadachbia", "활기"), ("Sadaltager", "박식"), ("Sulafat", "따뜻")]


def ai_voice_list():
    return ([{"short": f"openai:{v}", "gender": d, "locale": "openai", "name": f"ChatGPT {v} ({d}) [openai:{v}]"} for v, d in OPENAI_VOICES]
            + [{"short": f"gemini:{v}", "gender": d, "locale": "gemini", "name": f"Gemini {v} ({d}) [gemini:{v}]"} for v, d in GEMINI_VOICES])


def voice_code(voice_name):
    """설정에 적힌 성우 이름 → 음성 코드. '[ko-KR-XxxNeural]' '[openai:nova]' '[gemini:Kore]' 형식이면 괄호 안을 씀"""
    if voice_name in TTS_VOICES:
        return TTS_VOICES[voice_name]
    m = re.search(r"\[((?:openai|gemini):[A-Za-z]+|[a-z]{2}-[A-Z]{2}-[A-Za-z0-9]+)\]", voice_name or "")
    if m:
        return m.group(1)
    if re.fullmatch(r"[a-z]{2}-[A-Z]{2}-[A-Za-z0-9]+", (voice_name or "").strip()):
        return voice_name.strip()
    return "ko-KR-SunHiNeural"


def voice_display(short, gender, locale):
    base = short.split("-")[-1].replace("Neural", "").replace("Multilingual", "")
    ko = VOICE_KO_NAMES.get(base, base)
    g = {"Female": "여성", "Male": "남성"}.get(gender, gender)
    multi = " · 다국어" if "Multilingual" in short else ""
    return f"{ko} ({g}, {VOICE_LOCALES.get(locale, locale)}{multi}) [{short}]"


def list_voices(refresh=False):
    """엣지 음성 서버에서 성우 목록 받기 (한국어·영어·일본어). 실패하면 캐시/기본 목록"""
    if not refresh and os.path.exists(VOICE_CACHE_FILE):
        try:
            with open(VOICE_CACHE_FILE, encoding="utf-8") as f:
                data = json.load(f)
            if data:
                return data
        except Exception:
            pass
    try:
        import edge_tts, asyncio
        loop = asyncio.new_event_loop()
        try:
            vs = loop.run_until_complete(edge_tts.list_voices())
        finally:
            loop.close()
        data = [{"short": v["ShortName"], "gender": v.get("Gender", ""), "locale": v.get("Locale", ""),
                 "name": voice_display(v["ShortName"], v.get("Gender", ""), v.get("Locale", ""))}
                for v in vs if v.get("Locale") in VOICE_LOCALES]
        data.sort(key=lambda d: (list(VOICE_LOCALES).index(d["locale"]), d["gender"], d["short"]))
        if data:
            with open(VOICE_CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=1)
            return data
    except Exception:
        pass
    return [{"short": c, "gender": "", "locale": c[:5], "name": n} for n, c in TTS_VOICES.items() if c != "sapi"]


def tts_edge(text, voice, rate_pct, out_mp3, pitch_hz=0):
    """마이크로소프트 엣지 음성 (인터넷 필요, 무료)"""
    try:
        import edge_tts
    except ImportError:
        ok, _ = pip_install("edge-tts")
        importlib.invalidate_caches()
        if not ok:
            raise RuntimeError("edge-tts 설치 실패")
        import edge_tts
    import asyncio
    rate = f"{'+' if rate_pct >= 0 else ''}{int(rate_pct)}%"
    pitch = f"{'+' if pitch_hz >= 0 else ''}{int(pitch_hz)}Hz"

    async def run():
        await edge_tts.Communicate(text, voice, rate=rate, pitch=pitch).save(out_mp3)
    try:
        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(run())
        finally:
            loop.close()
    except Exception as e:
        raise RuntimeError(f"엣지 음성 실패({type(e).__name__}): {str(e)[:120]}")


def tts_openai(text, voice, rate_pct, style, out_mp3, key, model):
    """ChatGPT 음성 API (gpt-4o-mini-tts: 연기 지시 가능)"""
    import urllib.request, urllib.error
    payload = {"model": model or "gpt-4o-mini-tts", "input": text, "voice": voice, "response_format": "mp3",
               "speed": max(0.5, min(2.0, 1 + rate_pct / 100))}
    if style and "4o" in (model or "gpt-4o-mini-tts"):
        payload["instructions"] = style
    req = urllib.request.Request("https://api.openai.com/v1/audio/speech", data=json.dumps(payload).encode("utf-8"),
                                 headers={"Content-Type": "application/json", "Authorization": "Bearer " + key}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            data = r.read()
    except urllib.error.HTTPError as e:
        full = explain_api_error(e.code, e.read().decode("utf-8", "ignore")[:1500], "ChatGPT 음성")
        raise APIError(full.split("\n\n")[0], full.split("\n\n", 1)[1] if "\n\n" in full else "")
    with open(out_mp3, "wb") as f:
        f.write(data)


GEMINI_TTS_DEFAULT = "gemini-2.5-flash-preview-tts"


def gemini_tts_model(model):
    """음성은 이름에 'tts'가 들어간 모델만 가능 → 글 모델 이름이 들어오면 음성 모델로 바꿈"""
    m = (model or "").strip()
    if not m:
        return GEMINI_TTS_DEFAULT
    if "tts" not in m.lower():
        return "gemini-2.5-pro-preview-tts" if "pro" in m.lower() else GEMINI_TTS_DEFAULT
    return m


def _gemini_audio_part(out):
    """응답의 모든 후보·parts 를 돌며 소리(inlineData) 찾기 → (pcm bytes, 샘플레이트) 또는 None"""
    import base64
    for cand in (out or {}).get("candidates") or []:
        for p_ in ((cand or {}).get("content") or {}).get("parts") or []:
            d = (p_ or {}).get("inlineData") or (p_ or {}).get("inline_data")
            if d and d.get("data"):
                mime = d.get("mimeType") or d.get("mime_type") or ""
                mr = re.search(r"rate=(\d+)", mime)
                return base64.b64decode(d["data"]), (int(mr.group(1)) if mr else 24000)
    return None


def tts_gemini(text, voice, rate_pct, style, out_wav, key, model):
    """Gemini 음성 API (연기 지시를 글로 줌). 결과는 24kHz 16bit PCM → WAV"""
    import wave
    hint = (style + " ") if style else ""
    if rate_pct >= 15:
        hint += "조금 빠르게 읽어줘. "
    elif rate_pct <= -15:
        hint += "조금 천천히 읽어줘. "
    prompt = (hint + "다음 문장을 읽어줘: " + text) if hint else text
    m = gemini_tts_model(model)
    body = {"contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"responseModalities": ["AUDIO"],
                                 "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": voice}}}}}
    got, out = None, None
    for attempt in range(2):   # 가끔 소리 없이 끝나는 응답이 와서 한 번 더 시도
        out = _http_json(f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent",
                         body, {"x-goog-api-key": key}, who="Gemini 음성")
        got = _gemini_audio_part(out)
        if got and len(got[0]) > 200:
            break
        if attempt == 0:
            time.sleep(1.0)
            body["contents"][0]["parts"][0]["text"] = "다음 문장을 그대로 소리 내어 읽어줘: " + text
    if not got or len(got[0]) <= 200:
        reason = ""
        try:
            c0 = (out.get("candidates") or [{}])[0]
            reason = c0.get("finishReason", "")
            if (out.get("promptFeedback") or {}).get("blockReason"):
                reason = "차단됨: " + out["promptFeedback"]["blockReason"]
        except Exception:
            pass
        raise APIError(f"Gemini 음성이 소리를 돌려주지 않았습니다{(' (' + reason + ')') if reason else ''}. 다른 성우를 고르거나 연기 지시를 짧게 해보세요.",
                       "응답 앞부분: " + str(out)[:300])
    pcm, rate = got
    with wave.open(out_wav, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(pcm)


def tts_sapi(text, rate_pct, out_wav):
    """윈도우 내장 음성 (오프라인). 한국어 음성(Heami)이 설치돼 있어야 함"""
    if os.name != "nt":
        raise RuntimeError("윈도우 내장 음성은 윈도우에서만 됩니다")
    rate = max(-10, min(10, int(round(rate_pct / 10))))
    safe = text.replace("'", "''")
    ps = (f"Add-Type -AssemblyName System.Speech; $s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
          f"$v = $s.GetInstalledVoices() | Where-Object {{ $_.VoiceInfo.Culture.Name -eq 'ko-KR' }} | Select-Object -First 1; "
          f"if ($v) {{ $s.SelectVoice($v.VoiceInfo.Name) }}; $s.Rate = {rate}; "
          f"$s.SetOutputToWaveFile('{out_wav}'); $s.Speak('{safe}'); $s.Dispose()")
    p = subprocess.run(["powershell", "-NoProfile", "-Command", ps], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                       text=True, errors="replace", creationflags=subprocess.CREATE_NO_WINDOW)
    if p.returncode != 0 or not os.path.exists(out_wav):
        raise RuntimeError("윈도우 음성 실패: " + (p.stderr or "")[-200:])


def tts_key(voice, rate_pct, pitch_hz, text):
    import hashlib
    return hashlib.md5(f"{voice}|{float(rate_pct)}|{float(pitch_hz)}|{text}".encode("utf-8")).hexdigest()[:16]


TTS_CFG = {"style": "", "openai_key": "", "gemini_key": "", "openai_tts_model": "", "gemini_tts_model": ""}


def set_tts_cfg(s):
    """App 설정에서 AI 음성에 필요한 값만 꺼내 둠 (백그라운드에서 위젯을 읽지 않기 위해)"""
    TTS_CFG.update(style=str(s.get("narr_style", "")).strip(),
                   openai_key=(s.get("openai_key") or os.environ.get("OPENAI_API_KEY", "")).strip(),
                   gemini_key=(s.get("gemini_key") or os.environ.get("GEMINI_API_KEY", "")).strip(),
                   openai_tts_model=str(s.get("openai_tts_model", "")).strip(),
                   gemini_tts_model=str(s.get("gemini_tts_model", "")).strip())


def tts_clip(text, voice_name, rate_pct, cache_dir, pitch_hz=0):
    """문장 하나 → (소리 배열 mono float32, 길이초). 같은 문장은 캐시에서 재사용"""
    text = tts_clean(text)
    if not text:
        return np.zeros(1, np.float32), 0.0
    voice = voice_code(voice_name)
    ai = voice.startswith(("openai:", "gemini:"))
    key = tts_key(voice, rate_pct, pitch_hz, (TTS_CFG["style"] + "|" if ai else "") + text)
    os.makedirs(cache_dir, exist_ok=True)
    npy = os.path.join(cache_dir, key + ".npy")
    if os.path.exists(npy):
        a = np.load(npy)
        return a, len(a) / SR
    src = os.path.join(cache_dir, key + (".wav" if voice == "sapi" or voice.startswith("gemini:") else ".mp3"))
    if voice == "sapi":
        tts_sapi(text, rate_pct, src)
    elif voice.startswith("openai:"):
        if not TTS_CFG["openai_key"]:
            raise RuntimeError("ChatGPT 음성에는 API 키가 필요합니다 (AI 엔진 탭에 입력)")
        tts_openai(text, voice.split(":", 1)[1], rate_pct, TTS_CFG["style"], src, TTS_CFG["openai_key"], TTS_CFG["openai_tts_model"])
    elif voice.startswith("gemini:"):
        if not TTS_CFG["gemini_key"]:
            raise RuntimeError("Gemini 음성에는 API 키가 필요합니다 (AI 엔진 탭에 입력)")
        tts_gemini(text, voice.split(":", 1)[1], rate_pct, TTS_CFG["style"], src, TTS_CFG["gemini_key"], TTS_CFG["gemini_tts_model"])
    else:
        try:
            tts_edge(text, voice, rate_pct, src, pitch_hz)
        except Exception as e:
            if os.name == "nt":
                tts_sapi(text, rate_pct, src := os.path.join(cache_dir, key + ".wav"))
            else:
                raise e
    a = _decode_full(src)
    # 앞뒤 무음 다듬기 + 크기 맞추기
    thr = 0.01
    nz = np.nonzero(np.abs(a) > thr)[0]
    if len(nz):
        a = a[max(0, nz[0] - int(0.05 * SR)): nz[-1] + int(0.15 * SR)]
    peak = float(np.abs(a).max()) if len(a) else 0
    if peak > 0:
        a = a * (0.7 / peak)
    a = a.astype(np.float32)
    np.save(npy, a)
    try:
        os.remove(src)
    except OSError:
        pass
    return a, len(a) / SR


def _decode_full(path):
    """오디오 파일 전체를 mono float32 로"""
    p = subprocess.run([get_ffmpeg(), "-v", "error", "-i", path, "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"],
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                       creationflags=(subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0))
    if p.returncode != 0 or not p.stdout:
        raise RuntimeError("음성 파일을 읽지 못했습니다: " + p.stderr.decode("utf-8", "ignore")[:200])
    return np.frombuffer(p.stdout, np.float32).copy()


def narration_paras(story):
    """나레이션으로 읽을 문단 목록 [(문단 인덱스, 글)] - build_text_layer 의 paras 순서와 같음"""
    out, idx = [], 0
    for para in (story or "").replace("\r", "").split("\n"):
        para = para.strip()
        if not para or parse_media(para) or PH_RE.match(para):
            continue
        para = PH_INLINE_RE.sub("", para).strip()
        if not para:
            continue
        out.append((idx, para))
        idx += 1
    return out


def build_narration(story, s, cache_dir, log=None, cancel=None):
    """본문 전체 나레이션 → [(문단 인덱스, 소리, 길이)]"""
    items = narration_paras(story)
    res = []
    for k, (i, text) in enumerate(items):
        if cancel and cancel.is_set():
            raise RuntimeError("취소됨")
        a, d = tts_clip(text, s["narr_voice"], float(s["narr_rate"]), cache_dir, float(s.get("narr_pitch", 0)))
        res.append((i, a, d))
        if log and (k % 5 == 0 or k == len(items) - 1):
            log(f"  🎙 나레이션 {k + 1}/{len(items)}")
    return res


def has_audio(path):
    """MP4에 소리가 들어 있는지 확인"""
    try:
        p = subprocess.run([get_ffmpeg(), "-i", path], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, errors="replace",
                           creationflags=(subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0))
        return "Audio:" in (p.stderr or "")
    except Exception:
        return False


def write_mp3(path, x):
    """소리 배열 → MP3 (192kbps)"""
    tmp = path + ".tmp.wav"
    write_wav(tmp, x)
    try:
        p = subprocess.run([get_ffmpeg(), "-y", "-v", "error", "-i", tmp, "-c:a", "libmp3lame", "-b:a", "192k", path],
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, errors="replace",
                           creationflags=(subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0))
        if p.returncode != 0:
            raise RuntimeError("MP3 저장 실패: " + (p.stderr or "")[-200:])
    finally:
        try:
            os.remove(tmp)
        except OSError:
            pass


def write_wav(path, x):
    import wave
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
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


def play_wav_from(path, start_sec):
    """start_sec 초 지점부터 재생 (앞부분을 잘라낸 임시 파일을 만들어 재생)"""
    if start_sec < 0.3:
        play_wav(path)
        return
    import wave
    try:
        with wave.open(path, "rb") as w:
            fr, ch, sw = w.getframerate(), w.getnchannels(), w.getsampwidth()
            skip = min(w.getnframes(), int(start_sec * fr))
            w.setpos(skip)
            data = w.readframes(w.getnframes() - skip)
        tmp = os.path.join(tempfile.gettempdir(), "shorts_play_from.wav")
        with wave.open(tmp, "wb") as o:
            o.setnchannels(ch)
            o.setsampwidth(sw)
            o.setframerate(fr)
            o.writeframes(data)
        play_wav(tmp)
    except Exception:
        play_wav(path)


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
    ff = get_ffmpeg()
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
    if pkg.get("chapters"):
        lines += ["", "[챕터 타임스탬프 (설명란에 그대로 붙여넣기)]", "00:00 오프닝"]
        lines += [f"{int(t // 60):02d}:{int(t % 60):02d} {n}" for t, n in pkg["chapters"]]
    art = pkg.get("artwork")
    if isinstance(art, dict):
        lines += ["", "[그림 정보 (설명란에 넣으면 좋음)]",
                  f"- 작품: {art.get('title', '')} ({art.get('title_ko', '')}) · {art.get('artist', '')} · {art.get('year', '')}",
                  f"- 재료/크기: {art.get('medium', '')} · {art.get('size', '')}" + (f" · 사조: {art.get('movement')}" if art.get("movement") else ""),
                  f"- 소장: {art.get('museum', '')}" + (f" · 화가 사망 {art.get('artist_death')}" if art.get("artist_death") else ""),
                  f"- 이미지 저작권: {art.get('pd_reason', '')}"]
    song = pkg.get("song")
    if isinstance(song, dict):
        lines += ["", "[노래 정보 (설명란에 넣으면 저작권 문의 예방)]",
                  f"- 곡: {song.get('title', '')} ({song.get('title_ko', '')}) · 발표 {song.get('year', '')}년",
                  f"- 작곡 {song.get('composer', '')} / 작사 {song.get('lyricist', '')}" + (f" / 노래 {song.get('singer')}" if song.get("singer") else "")
                  + (f" · 작곡가 사망 {song.get('composer_death')}" if song.get("composer_death") else ""),
                  f"- 저작권: {song.get('pd_reason', '')}",
                  "- 영상의 멜로디는 원곡 음원이 아니라 프로그램이 직접 연주(합성)한 것입니다." if pkg.get("melody_used") else "- 영상에 원곡 멜로디·음원은 사용하지 않았습니다."]
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
        self.after(800, self.prepare_ffmpeg)
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    # ---- 설정 저장/불러오기 ----
    def load_cfg(self):
        try:
            with open(CONFIG_PATH, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def project_dict(self):
        return {"ver": 4, "model": self.model_var.get(), "category": self.cat_var.get(), "topic": self.topic_var.get(), "genre": self.genre_var.get(),
                "sources": getattr(self, "sources", []), "notes": getattr(self, "notes", ""),
                "song": getattr(self, "song", None), "melody": getattr(self, "melody", ""), "bpm": getattr(self, "bpm", 90),
                "artwork": getattr(self, "artwork", None),
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
        self.song, self.melody, self.bpm = c.get("song"), c.get("melody", ""), c.get("bpm", 90)
        self.artwork = c.get("artwork")
        CURRENT_MELODY["melody"], CURRENT_MELODY["bpm"] = self.melody or "", self.bpm or 90
        self.len_var.set(c.get("length", "40"))
        self.judge_var.set(bool(c.get("judge", True)))
        self.theme_var.set(c.get("theme", "시네마 다크"))
        self.title_var.set(c.get("title", SAMPLE_TITLE))
        self.set_story(c.get("story", SAMPLE_STORY))
        s = dict(DEFAULTS)
        s.update(c.get("settings", {}))
        if c.get("settings") and c.get("ver", 1) < 2 and int(float(s.get("fps", 30))) == 30:
            s["fps"] = 60  # 부드러운 스크롤 기본값으로 올림
        if c.get("settings") and c.get("ver", 1) < 4 and str(s.get("gemini_model", "")).startswith("gemini-1."):
            s["gemini_model"] = "gemini-2.5-flash"   # 1.x 모델은 종료됨
        if c.get("settings") and c.get("ver", 1) < 3:
            s["grain"] = 0          # 노이즈는 용량을 크게 키움 → 끔
            if int(float(s.get("quality", 23))) < 23:
                s["quality"] = 23
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
        self.story = ScrolledText(s1, height=5, wrap="word", font=("맑은 고딕", 11), undo=True)   # 창이 크면 자동으로 늘어남
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
        ttk.Button(tr, text="🎙 나레이션 만들기", command=self.prepare_narration).pack(side="left", padx=(0, 6))
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
        ttk.Button(s4, text="📺 롱폼 만들기(챕터 묶음)", command=self.longform).pack(side="left", padx=(6, 0))
        ttk.Button(s4, text="🌐 영어·일본어 버전", command=self.lang_versions_dialog).pack(side="left", padx=(6, 0))
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
        self.sound_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(pr, text="소리", variable=self.sound_var).pack(side="left", padx=(4, 0))
        ttk.Button(pr, text="썸네일 PNG 저장", command=self.save_thumb).pack(side="left", padx=4)
        self.info = ttk.Label(right, text="", wraplength=PREVIEW_W, justify="left")
        self.info.pack(pady=4)

        # 하단 AI 명령어
        bot = ttk.LabelFrame(self, text="AI 명령어 (Claude로 수정)", padding=6)
        bot.pack(side="bottom", fill="x", padx=8, pady=(4, 8), before=main)   # 창이 작아도 항상 보이게
        r3 = ttk.Frame(bot)
        r3.pack(fill="x")
        self.cmd_var = tk.StringVar()
        e = ttk.Entry(r3, textvariable=self.cmd_var, font=("맑은 고딕", 11))
        e.pack(side="left", fill="x", expand=True)
        e.bind("<Return>", lambda _: self.ai_command())
        ttk.Button(r3, text="실행", command=self.ai_command).pack(side="left", padx=6)
        ttk.Label(bot, foreground="gray",
                  text='예) "글자 더 크게"  "공포 레드 테마로"  "결말을 더 소름돋게"  "45초에 맞춰줘"  "배경음 빗소리로"  "사진을 결말 앞으로 옮겨줘"').pack(anchor="w")
        sr = ttk.Frame(bot)
        sr.pack(fill="x", pady=(4, 0))
        self.now_var = tk.StringVar(value="준비")
        tk.Label(sr, textvariable=self.now_var, anchor="w", justify="left", font=("맑은 고딕", 11, "bold"),
                 fg="#1565C0", wraplength=1100).pack(side="left", fill="x", expand=True)
        ttk.Button(sr, text="📜 전체 기록", command=self.show_log).pack(side="right")
        self.log = ScrolledText(self, height=4, state="disabled", font=("맑은 고딕", 10))   # 화면에는 안 보임 (전체 기록 창에서 봄)
        self.busy_since, self.busy_label = 0.0, ""

    def make_field(self, parent, key, label, t, r, c):
        ttk.Label(parent, text=label).grid(row=r, column=c * 2, sticky="e", padx=(8, 2), pady=2)
        v = tk.StringVar()
        self.vars[key] = v
        cell = ttk.Frame(parent)
        cell.grid(row=r, column=c * 2 + 1, sticky="w", pady=2)
        if t.startswith("choice:"):
            cb = ttk.Combobox(cell, textvariable=v, values=t[7:].split(","), width=(22 if key in ("format", "narr_voice", "audio_out") else 10), state="readonly")
            cb.pack(side="left")
            if key == "format":
                cb.bind("<<ComboboxSelected>>", self.on_format_change)
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
        elif t == "secret":
            ttk.Entry(cell, textvariable=v, width=24, show="*").pack(side="left")
            kind = "gemini" if "gemini" in key else "openai"
            ttk.Button(cell, text="키 확인", command=lambda: self.check_key_ui(kind, v.get())).pack(side="left", padx=2)
        elif t == "voice":
            ttk.Entry(cell, textvariable=v, width=26, state="readonly").pack(side="left")
            ttk.Button(cell, text="🎤 성우 선택…", command=self.voice_picker).pack(side="left", padx=2)
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
        if "format" in d:
            self.apply_format(d["format"])

    def apply_format(self, name):
        """화면 형식(세로/가로) 적용: 렌더 크기·미리보기 크기·여백 기본값"""
        if name not in FORMATS:
            return
        prev = (W, H)
        set_format(name)
        self.canvas.config(width=PREVIEW_W, height=PREVIEW_H)
        self.tscale.config(length=PREVIEW_W)
        self.info.config(wraplength=PREVIEW_W)
        if (W, H) != prev:
            if W > H:   # 가로: 글이 너무 길게 퍼지지 않게 좌우 여백 넓힘
                self.vars["margin_x"].set("280")
                self.vars["margin_right"].set("280")
                self.vars["photo_h"].set("0.6")
                self.vars["fps"].set("30")
            else:
                self.vars["margin_x"].set("90")
                self.vars["margin_right"].set("150")
                self.vars["fps"].set("60")

    def on_format_change(self, *_):
        self.apply_format(self.vars["format"].get())
        self.refresh_preview()

    def narr_cache_dir(self):
        return os.path.join(self.get_settings()["out_dir"], "tts_cache")

    def narration_for(self, story, s, log=None, cancel=None):
        """설정이 켜져 있으면 나레이션 목록 반환 (캐시 활용). 백그라운드에서 호출 (화면 위젯을 읽지 않음)"""
        if s.get("narration") != "on":
            return None
        return build_narration(story, s, os.path.join(s["out_dir"], "tts_cache"), log, cancel)

    def narration_cached(self, story, s):
        """이미 만들어 둔 나레이션이 전부 있으면 바로 반환, 아니면 None (미리보기용, 느린 작업 안 함)"""
        if s.get("narration") != "on":
            return None
        import hashlib
        cache = os.path.join(s["out_dir"], "tts_cache")
        voice = voice_code(s["narr_voice"])
        res = []
        for i, text in narration_paras(story):
            t = tts_clean(text)
            if not t:
                res.append((i, np.zeros(1, np.float32), 0.0))
                continue
            ai = voice.startswith(("openai:", "gemini:"))
            key = tts_key(voice, s["narr_rate"], s.get("narr_pitch", 0), (str(s.get("narr_style", "")).strip() + "|" if ai else "") + t)
            npy = os.path.join(cache, key + ".npy")
            if not os.path.exists(npy):
                return None
            a = np.load(npy)
            res.append((i, a, len(a) / SR))
        return res

    def check_key_ui(self, kind, key):
        self.set_status("🔑 키 확인 중...")

        def worker():
            ok, msg = check_api_key(kind, key)
            self.q.put(lambda: (self.write_log(msg.splitlines()[0]), self.set_status(msg.splitlines()[0]),
                                (messagebox.showinfo if ok else messagebox.showerror)("키 확인", msg)))
        threading.Thread(target=worker, daemon=True).start()

    def voice_picker(self):
        """🎤 성우 선택: 목록에서 고르고 샘플 문장으로 미리듣기, 속도·높낮이 조절"""
        dlg = tk.Toplevel(self)
        dlg.title("성우 선택")
        dlg.transient(self)
        dlg.geometry("760x560")
        f = ttk.Frame(dlg, padding=10)
        f.pack(fill="both", expand=True)
        top = ttk.Frame(f)
        top.pack(fill="x")
        ttk.Label(top, text="언어").pack(side="left")
        lang_var = tk.StringVar(value="한국어")
        lb_lang = ttk.Combobox(top, textvariable=lang_var, values=["전체"] + list(VOICE_LOCALES.values()), width=10, state="readonly")
        lb_lang.pack(side="left", padx=4)
        status = ttk.Label(top, text="", foreground="gray")
        status.pack(side="right")
        ttk.Button(top, text="목록 새로고침(서버)", command=lambda: load(True)).pack(side="right", padx=4)
        mid = ttk.Frame(f)
        mid.pack(fill="both", expand=True, pady=6)
        lst = tk.Listbox(mid, font=("맑은 고딕", 11), activestyle="none")
        sb = ttk.Scrollbar(mid, orient="vertical", command=lst.yview)
        lst.config(yscrollcommand=sb.set)
        lst.pack(side="left", fill="both", expand=True)
        sb.pack(side="left", fill="y")
        ctl = ttk.LabelFrame(f, text="미리듣기 설정", padding=8)
        ctl.pack(fill="x")
        rate_var = tk.DoubleVar(value=float(self.vars["narr_rate"].get() or 0))
        pitch_var = tk.DoubleVar(value=float(self.vars["narr_pitch"].get() or 0))
        ttk.Label(ctl, text="말 속도(%)").grid(row=0, column=0, sticky="e")
        ttk.Scale(ctl, from_=-30, to=40, variable=rate_var, length=200).grid(row=0, column=1, padx=4)
        rl = ttk.Label(ctl, width=5)
        rl.grid(row=0, column=2)
        ttk.Label(ctl, text="음 높낮이(Hz)").grid(row=0, column=3, sticky="e", padx=(16, 0))
        ttk.Scale(ctl, from_=-40, to=40, variable=pitch_var, length=200).grid(row=0, column=4, padx=4)
        pl = ttk.Label(ctl, width=5)
        pl.grid(row=0, column=5)

        def upd(*_):
            rl.config(text=f"{rate_var.get():+.0f}%")
            pl.config(text=f"{pitch_var.get():+.0f}")
        rate_var.trace_add("write", upd)
        pitch_var.trace_add("write", upd)
        upd()
        ttk.Label(ctl, text="연기 지시").grid(row=2, column=0, sticky="e", pady=(6, 0))
        style_var = tk.StringVar(value=self.vars["narr_style"].get())
        ttk.Entry(ctl, textvariable=style_var, width=70).grid(row=2, column=1, columnspan=5, sticky="w", pady=(6, 0))
        ttk.Label(ctl, text="(ChatGPT·Gemini 음성만 적용. 예: 공포 라디오 DJ처럼 낮고 느리게 / 밝은 아나운서처럼)", foreground="gray").grid(row=3, column=1, columnspan=5, sticky="w")
        ttk.Label(ctl, text="샘플 문장").grid(row=1, column=0, sticky="e", pady=(6, 0))
        sample_var = tk.StringVar(value="안녕하세요. 오늘은 아무도 몰랐던 이야기를 들려드릴게요. 끝까지 보시면 소름이 돋을 겁니다.")
        ttk.Entry(ctl, textvariable=sample_var, width=70).grid(row=1, column=1, columnspan=5, sticky="w", pady=(6, 0))
        voices = []

        def load(refresh=False):
            status.config(text="목록 받는 중...")

            def worker():
                data = list_voices(refresh)
                self.q.put(lambda: fill(data))
            threading.Thread(target=worker, daemon=True).start()

        def fill(data):
            voices.clear()
            voices.extend(data + ai_voice_list())
            show()
            status.config(text=f"성우 {len(data)}명" + ("" if os.path.exists(VOICE_CACHE_FILE) else " (기본 목록 - 인터넷 연결 시 새로고침)"))

        def show(*_):
            lst.delete(0, "end")
            want = lang_var.get()
            cur = self.vars["narr_voice"].get()
            sel = None
            for v in voices:
                if want != "전체" and VOICE_LOCALES.get(v["locale"]) != want:
                    continue
                lst.insert("end", v["name"])
                if v["name"] == cur or v["short"] == voice_code(cur):
                    sel = lst.size() - 1
            lst.insert("end", "윈도우 내장 음성 (오프라인, 품질 낮음)")
            if sel is not None:
                lst.selection_set(sel)
                lst.see(sel)
        lb_lang.bind("<<ComboboxSelected>>", show)

        def chosen_name():
            i = lst.curselection()
            if not i:
                return None
            name = lst.get(i[0])
            return "윈도우 내장 음성" if name.startswith("윈도우") else name

        def preview():
            name = chosen_name()
            if not name:
                messagebox.showinfo("성우", "목록에서 성우를 고르세요.", parent=dlg)
                return
            text, rate, pitch = sample_var.get().strip(), rate_var.get(), pitch_var.get()
            if voice_code(name)[:3] in ("en-", "ja-") and re.search(r"[가-힣]", text):
                text = {"en": "Hello. Today I will tell you a story nobody knew. Stay until the end.",
                        "ja": "こんにちは。今日は誰も知らなかった話をお届けします。最後までご覧ください。"}[voice_code(name)[:2]]
            status.config(text="샘플 만드는 중...")
            s_now = self.get_settings()
            s_now["narr_style"] = style_var.get()
            set_tts_cfg(s_now)
            code = voice_code(name)
            if code.startswith("openai:") and not TTS_CFG["openai_key"]:
                status.config(text="ChatGPT API 키가 없습니다 (AI 엔진 탭)")
                return
            if code.startswith("gemini:") and not TTS_CFG["gemini_key"]:
                status.config(text="Gemini API 키가 없습니다 (AI 엔진 탭)")
                return
            cache = os.path.join(s_now["out_dir"], "tts_cache")

            def worker():
                try:
                    a, d = tts_clip(text, name, rate, cache, pitch)
                    p = os.path.join(tempfile.gettempdir(), "shorts_voice_sample.wav")
                    write_wav(p, np.stack([a, a], 1))
                    self.q.put(lambda: (status.config(text=f"재생 중 ({d:.1f}초)"), play_wav(p)))
                except Exception as e:
                    short = getattr(e, "short", str(e).splitlines()[0] if str(e) else "실패")
                    self.q.put(lambda e=e, short=short: (status.config(text="❌ " + short[:40] + ("…" if len(short) > 40 else "")),
                                                         messagebox.showerror("미리듣기 실패", str(e), parent=dlg)))
            threading.Thread(target=worker, daemon=True).start()

        def choose():
            name = chosen_name()
            if not name:
                return
            self.vars["narr_voice"].set(name)
            self.vars["narr_rate"].set(f"{rate_var.get():.0f}")
            self.vars["narr_pitch"].set(f"{pitch_var.get():.0f}")
            self.vars["narr_style"].set(style_var.get())
            self.vars["narration"].set("on")
            self.bgm_made = None
            self.write_log(f"🎤 성우 선택: {name} (속도 {rate_var.get():+.0f}%, 높낮이 {pitch_var.get():+.0f}Hz) → 나레이션을 다시 만들면 적용됩니다")
            self.save_cfg()
            stop_wav()
            dlg.destroy()
            self.refresh_preview()
        bf = ttk.Frame(f)
        bf.pack(fill="x", pady=(8, 0))
        ttk.Button(bf, text="▶ 들어보기", command=preview).pack(side="left")
        ttk.Button(bf, text="■ 정지", command=stop_wav).pack(side="left", padx=4)
        ttk.Button(bf, text="닫기", command=lambda: (stop_wav(), dlg.destroy())).pack(side="right")
        ttk.Button(bf, text="이 성우로 선택", command=choose).pack(side="right", padx=6)
        lst.bind("<Double-Button-1>", lambda _: preview())
        load(False)

    def prepare_narration(self):
        """🎙 나레이션 만들기: 모든 문단 음성 생성 → 미리보기가 읽는 속도에 맞춰짐"""
        s = self.get_settings()
        if s["narration"] != "on":
            self.vars["narration"].set("on")
            s["narration"] = "on"
        story = self.get_story()

        def job():
            return self.narration_for(story, s, self.log_bg, self.cancel)

        def done(narr):
            total = sum(d for _, _, d in narr)
            self.write_log(f"🎙 나레이션 완료: {len(narr)}문단, 말하는 시간 {total:.0f}초 ({s['narr_voice']}) → 스크롤이 읽는 속도에 맞춰집니다")
            self.bgm_made = None
            self.refresh_preview()
        self.write_log(f"🎙 나레이션 만드는 중... ({s['narr_voice']}, 문단마다 음성 생성)")
        self.run_bg("나레이션 만드는 중...", job, done)

    def get_story(self):
        return self.story.get("1.0", "end-1c")

    def set_story(self, txt):
        self.story.delete("1.0", "end")
        self.story.insert("1.0", txt)

    def write_log(self, msg):
        line = time.strftime("[%H:%M:%S] ") + msg + "\n"
        self.log.config(state="normal")
        self.log.insert("end", line)
        self.log.see("end")
        self.log.config(state="disabled")
        head = msg.strip().splitlines()[0] if msg.strip() else ""
        if head and not msg.startswith(" "):      # 들여쓴 줄(세부 내용)은 기록에만
            self.now_line = head
            self.set_status(head)
        lv = getattr(self, "_log_view", None)
        if lv is not None:
            try:
                lv.config(state="normal")
                lv.insert("end", line)
                lv.see("end")
                lv.config(state="disabled")
            except tk.TclError:
                self._log_view = None

    def set_status(self, text):
        """아래 진행 상황 한 줄 (작업 중이면 걸린 시간 표시)"""
        self._status_text = text
        if self.busy and self.busy_since:
            sec = int(time.time() - self.busy_since)
            text = f"⏳ {text}  ({sec // 60}분 {sec % 60:02d}초)" if sec >= 60 else f"⏳ {text}  ({sec}초)"
        self.now_var.set(text)

    def show_log(self):
        """📜 전체 기록 창"""
        win = tk.Toplevel(self)
        win.title("전체 기록")
        win.geometry("900x500")
        box = ScrolledText(win, font=("맑은 고딕", 10), wrap="word")
        box.pack(fill="both", expand=True)
        box.insert("1.0", self.log.get("1.0", "end"))
        box.see("end")
        box.config(state="disabled")
        bf = ttk.Frame(win, padding=4)
        bf.pack(fill="x")

        def copy():
            self.clipboard_clear()
            self.clipboard_append(self.log.get("1.0", "end"))

        def clear():
            for b in (self.log, box):
                b.config(state="normal")
                b.delete("1.0", "end")
                b.config(state="disabled")
        ttk.Button(bf, text="복사", command=copy).pack(side="left")
        ttk.Button(bf, text="지우기", command=clear).pack(side="left", padx=4)
        ttk.Button(bf, text="닫기", command=win.destroy).pack(side="right")
        self._log_view = box
        win.protocol("WM_DELETE_WINDOW", lambda: (setattr(self, "_log_view", None), win.destroy()))

    def apply_theme(self, name):
        if name in THEMES:
            self.set_settings(THEMES[name])
            self.theme_var.set(name)
            self.refresh_preview()

    def on_category(self, *_):
        topics = cat_info(self.cat_var.get())[1]
        self.vars["photo_h"].set("0.5" if self.cat_var.get() == ART_CATEGORY else "0.36")
        if self.cat_var.get() == ART_CATEGORY and self.len_var.get() in ("", "40"):
            self.len_var.set("60")   # 큐레이터 해설은 60초 정도 필요
        self.genre_box.config(values=list(topics))
        self.genre_var.set(list(topics)[0])
        self.topic_box.config(values=[])
        self.on_genre()

    def on_genre(self, *_):
        topics = cat_info(self.cat_var.get())[1]
        g = self.genre_var.get()
        if g in topics:
            self.apply_theme(topics[g][1])

    def set_song(self, song, melody="", bpm=90):
        self.song = song if isinstance(song, dict) else None
        self.melody, self.bpm = (melody or ""), (bpm or 90)
        CURRENT_MELODY["melody"], CURRENT_MELODY["bpm"] = self.melody, self.bpm
        self.bgm_made = None  # 멜로디가 바뀌면 배경음을 다시 만들어야 함
        if self.song:
            t = self.song.get("title_ko") or self.song.get("title", "")
            self.write_log(f"🎼 노래: {t} ({self.song.get('year', '?')}) 작곡 {self.song.get('composer', '?')}"
                           + (f" · 저작권: {self.song.get('pd_reason')}" if self.song.get("pd_reason") else "")
                           + (" · 멜로디 오르골 연주 준비됨" if parse_melody(self.melody) else ""))

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
        if self.busy and time.time() - getattr(self, "_last_tick", 0) >= 1:   # 작업 중 경과 시간 갱신
            self._last_tick = time.time()
            self.set_status(getattr(self, "_status_text", self.busy_label))
        self.after(100, self.poll)

    def run_bg(self, label, job, done):
        if self.busy:
            messagebox.showinfo("알림", "다른 작업이 진행 중입니다.")
            return
        self.busy = True
        self.busy_since, self.busy_label = time.time(), label
        self.cancel.clear()
        self.status.config(text=label)
        self.set_status(label)
        SCRIPT_ENGINE["s"] = self.get_settings()
        set_tts_cfg(SCRIPT_ENGINE["s"])

        def worker():
            try:
                res = job()
                self.q.put(lambda: (self.end_busy("완료"), done(res)))
            except Exception as e:
                self.q.put(lambda e=e: (self.end_busy("오류"), self.on_err(e)))
        threading.Thread(target=worker, daemon=True).start()

    def end_busy(self, txt):
        took = int(time.time() - self.busy_since) if self.busy_since else 0
        self.busy = False
        self.busy_since = 0.0
        self.status.config(text=txt)
        last = getattr(self, "_status_text", "")
        if txt == "완료":
            self.set_status(f"✅ {last}" + (f"  (걸린 시간 {took // 60}분 {took % 60:02d}초)" if took >= 60 else f"  ({took}초)" if took else ""))
        elif txt == "오류":
            self.set_status("❌ 오류 - 내용은 오류 창 또는 📜 전체 기록에서 확인")

    def on_err(self, e):
        msg = str(e)
        if isinstance(e, ModuleNotFoundError):
            msg += f'\n\n명령 프롬프트(cmd)에서 실행:\n"{sys.executable}" -m pip install pillow numpy imageio-ffmpeg'

        self.write_log("오류: " + (msg.splitlines()[0] if msg else ""))
        self.set_status("❌ " + (msg.splitlines()[0] if msg else "오류"))
        if msg != "취소됨":
            messagebox.showerror("오류", msg)

    def log_bg(self, msg):
        self.q.put(lambda: self.write_log(msg))

    # ---- AI ----
    def prepare_ffmpeg(self):
        """MP4 압축 프로그램을 미리 확인 (없으면 백그라운드에서 자동 설치)"""
        def worker():
            try:
                get_ffmpeg()
            except Exception as e:
                self.q.put(lambda e=e: self.write_log("⚠ " + str(e).splitlines()[0] + " → MP4 만들 때 다시 시도합니다"))
                return
            if not getattr(self, "_ff_logged", False):
                self._ff_logged = True
        threading.Thread(target=worker, daemon=True).start()

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
            d = ask_script_json(model, single_sys, user)
            title, story, notes = d.get("title", ""), d.get("story", ""), d.get("notes", "")
            sources = sources or d.get("sources", [])
            song, melody, bpm = d.get("song"), d.get("melody", ""), d.get("bpm", 90)
            artwork, details = d.get("artwork"), d.get("details")
        else:
            log("초안 3개 작성 중...")
            drafts = ask_script_json(model, multi_sys, user).get("drafts", [])
            drafts = [d for d in drafts if isinstance(d, dict) and d.get("story")]
            if not drafts:
                raise RuntimeError("초안을 만들지 못했습니다.")
            log("편집장 심사 중... (" + " / ".join(d.get("title", "") for d in drafts) + ")")
            j = ask_script_json(model, JUDGE_SYSTEM, f"콘텐츠 종류: {category}\n소재: {genre}\n\n[초안들]\n" + json.dumps(drafts, ensure_ascii=False))
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
            song = pol.get("song") or drafts[best].get("song")
            melody = pol.get("melody") or drafts[best].get("melody", "")
            bpm = pol.get("bpm") or drafts[best].get("bpm", 90)
            artwork = pol.get("artwork") or drafts[best].get("artwork")
            details = pol.get("details") or drafts[best].get("details")
        if photos:
            if category == ART_CATEGORY and details and not _artist_recent(artwork):
                photos = photos[:1] + crop_details(photos[0]["path"], details, media_dir, log) + photos[1:]
            story = place_photos(story, photos)
        elif factual and autophoto and not (category == ART_CATEGORY and _artist_recent(artwork)):
            log("🔎 근거 사진 찾는 중...")
            try:
                extra_info = ("\n[그림 정보] " + json.dumps(artwork, ensure_ascii=False)) if artwork else ""
                d = ask_json(model, PHOTO_SYSTEM, f"콘텐츠 종류: {category}{extra_info}\n[제목] {title}\n\n[본문]\n{story}", tools=WEB_TOOLS)
                photos = fetch_photos(d.get("photos"), media_dir, log)
                if photos and category == ART_CATEGORY and details:
                    photos = photos[:1] + crop_details(photos[0]["path"], details, media_dir, log) + photos[1:]
                if photos:
                    story = place_photos(story, photos)
            except Exception as e:
                log("  사진 찾기 실패: " + str(e)[:80])
            story = strip_placeholders(story)
        else:
            story = strip_placeholders(story)
        artwork = artwork if (category == ART_CATEGORY and isinstance(artwork, dict)) else None
        if artwork:
            recent = _artist_recent(artwork)
            if recent and photo_credits(story):
                story = story_text_only(story).strip()
                notes = f"⚠ 화가 사망 {artwork.get('artist_death')}년 → 사후 70년 미만이라 그림 이미지를 뺐습니다(이야기만 사용). " + str(notes or "")
            elif recent:
                notes = f"화가 사망 {artwork.get('artist_death')}년 → 그림 이미지 미사용(저작권). " + str(notes or "")
            log(f"  🖼 그림: {artwork.get('title_ko') or artwork.get('title')} - {artwork.get('artist')} ({artwork.get('year')})"
                + (" · 이미지 미사용(저작권)" if recent else f" · 이미지 사용 가능 ({artwork.get('pd_reason', '')})"))
        song = song if isinstance(song, dict) else None
        if category == SONG_CATEGORY and song:
            try:
                yr = int(str(song.get("year", "")).strip()[:4])
            except ValueError:
                yr = 0
            has_lyrics = any(l.lstrip().startswith("♪") for l in story.split("\n"))
            if yr >= 1930:
                if has_lyrics or "가사" in genre:
                    notes = f"⚠ 발표 연도 {yr}년 → 가사 저작권이 남아 있음. 1929년 이전 곡으로 바꾸거나 가사를 빼세요. " + str(notes or "")
                else:
                    notes = f"{yr}년 곡 → 가사·멜로디 없이 이야기만 사용. " + str(notes or "")
                melody = ""
            ok = bool(parse_melody(melody))
            log(f"  🎼 노래: {song.get('title_ko') or song.get('title')} ({song.get('year')}, {song.get('composer')})"
                + (" · 멜로디 확보 → 오르골로 연주" if ok else " · 멜로디 없음 → 일반 오르골"))
        else:
            song, melody, bpm = None, "", 90
        return {"title": title, "story": story, "note": note, "sources": sources, "notes": notes, "topic": topic,
                "song": song, "melody": melody if parse_melody(melody) else "", "bpm": bpm, "artwork": artwork}

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
            self.set_song(res.get("song"), res.get("melody", ""), res.get("bpm", 90))
            self.artwork = res.get("artwork")
            if self.artwork:
                a = self.artwork
                self.write_log(f"🖼 그림: {a.get('title_ko') or a.get('title')} - {a.get('artist')} ({a.get('year')}) · {a.get('museum', '')}"
                               + (f" · {a.get('pd_reason')}" if a.get("pd_reason") else ""))
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
        self.song, self.melody, self.bpm = None, "", 90
        self.artwork = None
        CURRENT_MELODY["melody"], CURRENT_MELODY["bpm"] = "", 90
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
            names = {"hook": "훅", "pacing": "전개", "ending": "결말", "readability": "가독성", "share": "공유욕구", "expertise": "전문성"}
            line = "  ".join(f"{names.get(k, k)} {sc.get(k, '?')}" for k in names if k in sc)
            mx = 60 if "expertise" in sc else 50
            self.write_log(f"평가 {d.get('grade', '')}등급 {d.get('total', '?')}/{mx}  |  {line}")
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
            pkg["song"] = getattr(self, "song", None)
            pkg["artwork"] = getattr(self, "artwork", None)
            pkg["chapters"] = self.renderer.chapter_times() if self.renderer else []
            pkg["melody_used"] = bool(parse_melody(getattr(self, "melody", "")))
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
            s = self.get_settings()
            narr = self.narration_cached(self.get_story(), s)
            self.renderer = make_renderer(self.title_var.get(), self.get_story(), s, narr)
            self.narr_missing = s.get("narration") == "on" and narr is None
        except Exception as e:
            self.on_err(e)
            return
        r = self.renderer
        self.tscale.config(to=max(0.1, r.duration))
        if self.tvar.get() > r.duration:
            self.tvar.set(0)
        if not self.playing and self.tvar.get() < 0.05:
            self.tvar.set(min(r.duration, r.intro + 0.3))  # 제목 카드가 사라지고 글이 보이는 시점
        warn = "\n⚠ 3분 넘음 (쇼츠 제한)" if r.duration > 180 and W < H else ""
        body = story_text_only(self.get_story())
        chars = len(body.replace(" ", "").replace("\n", ""))
        nph = len(photo_credits(self.get_story()))
        seed = self.vars["bgm_seed"].get()
        snd = ((self.cur_style() + (f" #{seed} (고정)" if seed not in ("", "0") else " (만들기 전)"))
               if self.vars["bgm_mode"].get() == "자동생성"
               else ("파일 " + os.path.basename(self.vars["bgm_path"].get()) if self.vars["bgm_mode"].get() == "파일" else "없음"))
        hit = f" | 반전 효과음 {r.reveal_t:.1f}초" if r.reveal_t and self.vars["reveal_hit"].get() == "on" else ""
        if self.vars["narration"].get() == "on":
            warn += ("\n🎙 나레이션: 준비됨 (읽는 속도에 맞춰 스크롤)" if r.keys else "\n🎙 나레이션: 아직 안 만듦 → '🎙 나레이션 만들기' 누르면 속도가 맞춰짐")
        ch = r.chapter_times()
        if ch:
            warn += f"\n📑 챕터 {len(ch)}개: " + " · ".join(f"{int(t // 60)}:{int(t % 60):02d} {n[:8]}" for t, n in ch[:6]) + (" …" if len(ch) > 6 else "")
        song = getattr(self, "song", None)
        if song and self.cat_var.get() == SONG_CATEGORY:
            warn += f"\n🎼 {song.get('title_ko') or song.get('title', '')} ({song.get('year', '?')})"
        art = getattr(self, "artwork", None)
        if art and self.cat_var.get() == ART_CATEGORY:
            warn += f"\n🖼 {art.get('title_ko') or art.get('title', '')} - {art.get('artist', '')}"
        mid = (f"자막 {len(r.segs)}장면 · 사진 {len(r.images)}장" if isinstance(r, SubtitleRenderer)
               else f"스크롤 {max(0, r.dist)}px | {r.speed:.0f}px/초")
        self.info.config(text=f"총 {r.duration:.1f}초 (제목카드 {r.intro:.1f} + 정지 {r.hs:.1f} + 본편 {r.scroll_t:.1f} + 끝 {r.he:.1f})\n"
                              f"본문 {chars}자 | {mid}{warn}\n"
                              f"배경음: {snd}{hit}" + (f" | 사진 {nph}장" if nph else ""))
        self.show_frame()

    def show_frame(self, *_):
        if not self.renderer:
            return
        im = Image.fromarray(self.renderer.frame_preview(float(self.tvar.get())))
        if self.vars["safe_guide"].get() == "on" and H > W:
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

    def bgm_ready(self):
        """지금 설정과 맞는 배경음 파일이 준비돼 있으면 경로, 소리가 없는 설정이면 "", 만들어야 하면 None"""
        s = self.get_settings()
        if s["bgm_mode"] == "없음" and s["reveal_hit"] != "on":
            return ""
        made = getattr(self, "bgm_made", None)
        if not made or not os.path.exists(made["path"]):
            return None
        if made["mode"] != s["bgm_mode"]:
            return None
        if s["bgm_mode"] == "파일" and made.get("src") != s["bgm_path"]:
            return None
        if s["bgm_mode"] == "자동생성" and str(made["seed"]) != str(s["bgm_seed"]):
            return None
        if self.renderer and abs(self.renderer.duration - made["dur"]) > 0.05:
            return None
        return made["path"]

    def replay_bgm(self):
        """만든 배경음을 화면과 같이 처음부터 재생"""
        self.playing = False
        stop_wav()
        self.tvar.set(0)
        self.sound_var.set(True)
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
        """▶ 재생: 화면과 배경음을 같이 재생 (배경음이 아직 없으면 먼저 만들고 자동 재생)"""
        if self.playing:
            self.playing = False
            stop_wav()
            return
        if not self.renderer:
            return
        if self.tvar.get() >= self.renderer.duration - 0.1 or self.tvar.get() <= self.renderer.intro + 0.35:
            self.tvar.set(0)
        if self.sound_var.get():
            path = self.bgm_ready()
            if path is None:
                if self.busy:
                    self.write_log("다른 작업이 끝나면 다시 ▶ 재생을 누르세요.")
                    return
                made = getattr(self, "bgm_made", None)
                s = self.get_settings()
                same = made and os.path.exists(made["path"]) and made["mode"] == s["bgm_mode"] and \
                    (s["bgm_mode"] != "자동생성" or str(made["seed"]) == str(s["bgm_seed"])) and \
                    (s["bgm_mode"] != "파일" or made.get("src") == s["bgm_path"])
                if same:
                    self.write_log("  영상 길이가 바뀌어서 배경음을 길이에 맞춰 다시 만든 뒤 재생합니다.")
                    self._remake_same()
                else:
                    self.write_log("  배경음을 먼저 만든 뒤 재생합니다...")
                    self.make_bgm()
                return   # 만들기가 끝나면 자동으로 재생됨
            if path:
                play_wav_from(path, float(self.tvar.get()))
        self.playing = True
        self.t0 = time.time() - float(self.tvar.get())
        self.tick()

    def tick(self):
        if not self.playing or not self.renderer:
            return
        t = time.time() - self.t0
        if t > self.renderer.duration:
            self.playing = False
            stop_wav()
            return
        t0 = time.time()
        self.tvar.set(t)
        self.show_frame()
        spent = int((time.time() - t0) * 1000)
        self.after(max(5, 16 - spent), self.tick)  # 가능하면 초당 60장, 최소 5ms 간격

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

    def ask_audio_choice(self, s):
        """MP4 만들기 전 배경음을 직접 고르는 창. 반환: 수정된 설정 또는 None(취소)"""
        dlg = tk.Toplevel(self)
        dlg.title("MP4 만들기 - 배경음 선택")
        dlg.transient(self)
        dlg.grab_set()
        made = getattr(self, "bgm_made", None)
        cur = (f"지금 설정 배경음: {self.cur_style()} #{s['bgm_seed']}" if s["bgm_mode"] == "자동생성" and s["bgm_seed"]
               else f"지금 설정 배경음: {self.cur_style()} (새로 만듦)" if s["bgm_mode"] == "자동생성"
               else f"지금 설정 배경음: 파일 {os.path.basename(s['bgm_path'])}" if s["bgm_mode"] == "파일" and s["bgm_path"]
               else "지금 설정 배경음: 없음")
        choice = tk.StringVar(value="current" if s["bgm_mode"] != "없음" else "none")
        file_var = tk.StringVar(value=s["bgm_path"] if s["bgm_mode"] == "파일" else "")
        out_var = tk.StringVar(value=s["audio_out"])
        hit_var = tk.BooleanVar(value=s["reveal_hit"] == "on")
        f = ttk.Frame(dlg, padding=12)
        f.pack(fill="both", expand=True)
        ttk.Label(f, text="영상에 넣을 배경음", font=("맑은 고딕", 10, "bold")).grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 6))
        ttk.Radiobutton(f, text=cur, variable=choice, value="current").grid(row=1, column=0, columnspan=3, sticky="w")
        ttk.Radiobutton(f, text="음악 파일 직접 선택:", variable=choice, value="file").grid(row=2, column=0, sticky="w")
        ttk.Entry(f, textvariable=file_var, width=38).grid(row=2, column=1, sticky="w", padx=4)

        def pick():
            p = filedialog.askopenfilename(parent=dlg, filetypes=[("오디오", "*.mp3 *.wav *.m4a *.ogg *.flac")])
            if p:
                file_var.set(p)
                choice.set("file")
        ttk.Button(f, text="…", width=3, command=pick).grid(row=2, column=2)
        ttk.Radiobutton(f, text="소리 없음", variable=choice, value="none").grid(row=3, column=0, columnspan=3, sticky="w")
        ttk.Checkbutton(f, text="반전 효과음(쿵) 넣기", variable=hit_var).grid(row=4, column=0, columnspan=3, sticky="w", pady=(6, 0))
        ttk.Label(f, text="소리 저장 방식", font=("맑은 고딕", 10, "bold")).grid(row=5, column=0, columnspan=3, sticky="w", pady=(10, 4))
        for i, (v, desc) in enumerate((("MP4에 포함", "MP4 안에 소리가 들어감 (그대로 업로드)"),
                                       ("MP4에 포함+MP3 따로", "MP4에도 넣고, 같은 이름의 MP3도 따로 저장 (편집 프로그램용)"),
                                       ("MP3만 따로(무음 MP4)", "MP4는 소리 없이 작게, 소리는 MP3로만 저장"))):
            ttk.Radiobutton(f, text=f"{v}  —  {desc}", variable=out_var, value=v).grid(row=6 + i, column=0, columnspan=3, sticky="w")
        ttk.Label(f, text="용량 참고: 1분 영상 ≈ 8MB (소리 포함 시 +1.4MB). '필름 노이즈'는 꺼 두세요 (용량 5~8배).",
                  foreground="gray").grid(row=9, column=0, columnspan=3, sticky="w", pady=(10, 0))
        res = {}
        bf = ttk.Frame(f)
        bf.grid(row=10, column=0, columnspan=3, sticky="e", pady=(10, 0))

        def ok():
            if choice.get() == "file" and not (file_var.get() and os.path.exists(file_var.get())):
                messagebox.showwarning("배경음", "음악 파일을 선택하세요.", parent=dlg)
                return
            res["v"] = (choice.get(), file_var.get(), out_var.get(), hit_var.get())
            dlg.destroy()
        ttk.Button(bf, text="취소", command=dlg.destroy).pack(side="right")
        ttk.Button(bf, text="MP4 만들기", command=ok).pack(side="right", padx=6)
        dlg.bind("<Return>", lambda _: ok())
        self.wait_window(dlg)
        if "v" not in res:
            return None
        ch, fp, outm, hit = res["v"]
        s = dict(s)
        if ch == "file":
            s["bgm_mode"], s["bgm_path"] = "파일", fp
            self.vars["bgm_mode"].set("파일")
            self.vars["bgm_path"].set(fp)
        elif ch == "none":
            s["bgm_mode"] = "없음"
        s["reveal_hit"] = "on" if hit else "off"
        s["audio_out"] = outm
        self.vars["audio_out"].set(outm)
        self.vars["reveal_hit"].set(s["reveal_hit"])
        return s

    def make_mp4(self):
        self.playing = False
        self.refresh_preview()
        if not self.renderer:
            return
        r = self.renderer
        s = self.ask_audio_choice(self.get_settings())
        if s is None:
            return
        style = resolve_style(s, self.genre_var.get())
        base = os.path.join(s["out_dir"], safe_name(self.title_var.get()))
        out = base + ".mp4"
        self.prog["value"] = 0
        prog = self.progress_cb()
        if s["bgm_mode"] == "자동생성" and s["bgm_seed"] == 0:
            seed = int(np.random.default_rng().integers(1, 100000))
            s["bgm_seed"] = seed
            self.vars["bgm_seed"].set(str(seed))
            self.write_log(f"  배경음 번호가 없어 새 번호 #{seed}로 만듭니다 (소리 탭에 저장됨)")

        story_now, title_now = self.get_story(), self.title_var.get()

        def job():
            nonlocal r
            if s.get("narration") == "on" and not r.keys:
                self.q.put(lambda: self.status.config(text="나레이션 만드는 중..."))
                narr = self.narration_for(story_now, s, self.log_bg, self.cancel)
                r = make_renderer(title_now, story_now, s, narr)
                self.q.put(lambda: setattr(self, "renderer", r))
            self.q.put(lambda: self.status.config(text="배경음 만드는 중..."))
            audio = build_audio(r, s, style)
            mp3 = ""
            if audio is not None and "MP3" in s["audio_out"]:
                mp3 = base + "_배경음.mp3"
                write_mp3(mp3, audio)
            in_video = audio if "MP4에 포함" in s["audio_out"] else None
            export_mp4(r, out, prog, self.cancel, in_video)
            r.thumbnail().save(base + "_썸네일.png")
            ch = r.chapter_times()
            if ch:
                with open(base + "_타임스탬프.txt", "w", encoding="utf-8") as f:
                    f.write("\n".join(f"{int(t // 60):02d}:{int(t % 60):02d} {n}" for t, n in [(0, "오프닝")] + ch))
            return out, mp3, in_video is not None and has_audio(out), os.path.getsize(out) / 1e6

        def done(res):
            p, mp3, snd, mb = res
            what = ((f"{style} #{s['bgm_seed']}") if s["bgm_mode"] == "자동생성"
                    else ("파일 " + os.path.basename(s["bgm_path"]) if s["bgm_mode"] == "파일"
                          else ("반전 효과음만" if s["reveal_hit"] == "on" else "없음")))
            self.write_log(f"MP4 저장 완료: {p}  ({mb:.1f}MB · 썸네일 PNG 같이 저장)")
            if "MP4에 포함" in s["audio_out"]:
                self.write_log("  MP4 소리: " + ("✅ 포함됨 (" + what + ")" if snd else "❌ 포함 안 됨 - 소리 탭 설정을 확인하세요"))
            else:
                self.write_log("  MP4 소리: 없음 (무음으로 저장)")
            if mp3:
                self.write_log(f"  🎵 배경음 MP3 따로 저장: {mp3}")
            if os.path.exists(base + "_타임스탬프.txt"):
                self.write_log("  📑 챕터 타임스탬프 저장: " + base + "_타임스탬프.txt (설명란에 붙여넣으면 챕터로 표시됨)")
            self.save_cfg()
            auto = s.get("auto_langs", "안 함")
            if auto != "안 함":
                langs = [c for c, nm in (("en", "영어"), ("ja", "일본어")) if nm in auto]
                self.after(300, lambda: self.make_lang_versions(langs, True))
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
                CURRENT_MELODY["melody"], CURRENT_MELODY["bpm"] = res.get("melody", ""), res.get("bpm", 90)
                narr = self.narration_for(story, s, log, self.cancel)
                r = make_renderer(title, story, s, narr)
                style = resolve_style(s, genre)
                audio = build_audio(r, s, style)
                if audio is not None and "MP3" in s["audio_out"]:
                    write_mp3(base + "_배경음.mp3", audio)
                export_mp4(r, base + ".mp4", self.progress_cb(f"[{i + 1}/{n}] "), self.cancel,
                           audio if "MP4에 포함" in s["audio_out"] else None)
                r.thumbnail().save(base + "_썸네일.png")
                try:
                    pkg = ask_json(model, PACKAGE_SYSTEM, f"콘텐츠 종류: {cat}\n소재: {genre}\n[제목] {title}\n\n[본문]\n{story_text_only(story)}")
                    pkg["sources"], pkg["notes"], pkg["song"], pkg["artwork"] = sources, notes, res.get("song"), res.get("artwork")
                    pkg["melody_used"] = bool(parse_melody(res.get("melody", "")))
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

    def lang_versions_dialog(self):
        if not story_text_only(self.get_story()).strip():
            messagebox.showinfo("다른 언어 버전", "먼저 대본을 만들거나 입력하세요.")
            return
        dlg = tk.Toplevel(self)
        dlg.title("다른 언어 버전 만들기")
        dlg.transient(self)
        dlg.grab_set()
        f = ttk.Frame(dlg, padding=12)
        f.pack(fill="both", expand=True)
        s = self.get_settings()
        try:
            _, eng_name = pick_engine(s)
        except RuntimeError as e:
            eng_name = "오류: " + str(e)[:40]
        ttk.Label(f, text=f"번역 AI: {eng_name}  (번역 탭에서 바꿀 수 있음 · API 방식이라 채팅 기록에 남지 않음)", foreground="gray").grid(row=0, column=0, columnspan=2, sticky="w")
        en, ja = tk.BooleanVar(value=True), tk.BooleanVar(value=True)
        ttk.Checkbutton(f, text="영어 (English) — 나레이션: Aria", variable=en).grid(row=1, column=0, sticky="w", pady=(8, 0))
        ttk.Checkbutton(f, text="일본어 (日本語) — 나레이션: Nanami", variable=ja).grid(row=2, column=0, sticky="w")
        mp4 = tk.BooleanVar(value=True)
        ttk.Checkbutton(f, text="번역 후 MP4까지 바로 만들기 (썸네일·업로드 문구 포함)", variable=mp4).grid(row=3, column=0, sticky="w", pady=(8, 0))
        ttk.Label(f, text="원본(한국어) 대본과 설정은 그대로 두고, 언어별 프로젝트(json)·MP4를 따로 저장합니다.", foreground="gray").grid(row=4, column=0, columnspan=2, sticky="w", pady=(8, 0))
        res = {}

        def ok():
            res["langs"] = [c for c, v in (("en", en.get()), ("ja", ja.get())) if v]
            res["mp4"] = mp4.get()
            dlg.destroy()
        bf = ttk.Frame(f)
        bf.grid(row=5, column=0, columnspan=2, sticky="e", pady=(10, 0))
        ttk.Button(bf, text="취소", command=dlg.destroy).pack(side="right")
        ttk.Button(bf, text="만들기", command=ok).pack(side="right", padx=6)
        self.wait_window(dlg)
        if res.get("langs"):
            self.make_lang_versions(res["langs"], res["mp4"])

    def make_lang_versions(self, langs, make_mp4=True, after=None):
        """영어·일본어 버전: 번역 → 언어별 프로젝트 저장 → (선택) MP4·썸네일·업로드 문구"""
        s = self.get_settings()
        try:
            pick_engine(s)
        except RuntimeError as e:
            self.on_err(e)
            return
        model, title, story = self.model_var.get().strip(), self.title_var.get(), self.get_story()
        cat, genre = self.cat_var.get(), self.genre_var.get()
        style = resolve_style(s, genre)
        if s["bgm_mode"] == "자동생성" and s["bgm_seed"] == 0:
            s["bgm_seed"] = int(np.random.default_rng().integers(1, 100000))
            self.vars["bgm_seed"].set(str(s["bgm_seed"]))
        proj = self.project_dict()
        log = self.log_bg
        melody = dict(CURRENT_MELODY)

        def job():
            done_files = []
            for code in langs:
                if self.cancel.is_set():
                    raise RuntimeError("취소됨")
                name, voice, outro, tag = LANGS[code]
                log(f"🌐 {name} 번역 중... ({pick_engine(s)[1]})")
                sysmsg = TRANSLATE_SYSTEM.format(lang_name={"en": "English", "ja": "Japanese"}[code])
                d = ask_engine_json(s, model, sysmsg, f"[Category] {cat} / {genre}\n[Title] {title}\n\n[Script]\n{story}")
                t_title, t_story = str(d.get("title") or title), str(d.get("story") or "")
                if not t_story.strip():
                    raise RuntimeError(f"{name} 번역 결과가 비어 있습니다")
                # 사진 줄은 원본 그대로 되살리기 (혹시 바뀌었을 때)
                orig_media = [l for l in story.split("\n") if parse_media(l)]
                got_media = [l for l in t_story.split("\n") if parse_media(l)]
                if len(got_media) == len(orig_media):
                    it = iter(orig_media)      # 번역 AI가 사진 줄을 조금 바꿨어도 원본으로 되돌림
                    t_story = "\n".join(next(it) if parse_media(l) else l for l in t_story.split("\n"))
                else:
                    t_story = "\n\n".join(p for p in split_paras(t_story) if not parse_media(p))
                    for mk in orig_media:
                        t_story = "\n\n".join(insert_photo_near(split_paras(t_story), mk, ""))
                ls = dict(s)
                ls["outro_text"] = outro
                ls["narr_voice"] = voice
                fp, fb = find_font_lang(code), find_font_lang(code, True)
                if fp:
                    ls["font_path"], ls["title_font_path"] = fp, (fb or fp)
                ls["auto_langs"] = "안 함"
                base = os.path.join(s["out_dir"], safe_name(title) + tag)
                os.makedirs(s["out_dir"], exist_ok=True)
                p2 = dict(proj, title=t_title, story=t_story, settings=ls, lang=code)
                with open(base + ".json", "w", encoding="utf-8") as fjs:
                    json.dump(p2, fjs, ensure_ascii=False, indent=2)
                pkg = {"titles": d.get("titles") or [t_title], "description": d.get("description", ""),
                       "hashtags": d.get("hashtags", ""), "pinned_comment": d.get("pinned_comment", ""),
                       "sources": proj.get("sources", []), "song": proj.get("song"), "artwork": proj.get("artwork"),
                       "melody_used": bool(parse_melody(proj.get("melody", "")))}
                log(f"  {name} 번역 완료: {t_title}")
                if make_mp4:
                    CURRENT_MELODY.update(melody)
                    narr = self.narration_for(t_story, ls, log, self.cancel)
                    r = make_renderer(t_title, t_story, ls, narr)
                    audio = build_audio(r, ls, style)
                    if audio is not None and "MP3" in ls["audio_out"]:
                        write_mp3(base + "_배경음.mp3", audio)
                    export_mp4(r, base + ".mp4", self.progress_cb(f"[{name}] "), self.cancel,
                               audio if "MP4에 포함" in ls["audio_out"] else None)
                    r.thumbnail().save(base + "_썸네일.png")
                    pkg["chapters"] = r.chapter_times()
                    log(f"  {name} MP4 저장: {base}.mp4 ({os.path.getsize(base + '.mp4') / 1e6:.1f}MB)")
                write_package(base, t_title, t_story, pkg)
                done_files.append(base)
            return done_files

        def done(files):
            self.write_log(f"🌐 다른 언어 버전 완료: {len(files)}개 → " + ", ".join(os.path.basename(f) for f in files))
            self.write_log("  열어보려면 '프로젝트 열기'에서 _EN.json / _JA.json 선택 (원본은 그대로 유지됨)")
            if after:
                after()
        self.write_log("🌐 다른 언어 버전 만들기: " + ", ".join(LANGS[c][0] for c in langs))
        self.run_bg("번역 중...", job, done)

    def longform(self):
        """📺 롱폼: 챕터 N개를 AI로 만들어 하나의 대본으로 묶음 (가로 화면·나레이션 권장)"""
        dlg = tk.Toplevel(self)
        dlg.title("롱폼 만들기 (챕터 묶음)")
        dlg.transient(self)
        dlg.grab_set()
        f = ttk.Frame(dlg, padding=12)
        f.pack(fill="both", expand=True)
        ttk.Label(f, text=f"종류 '{self.cat_var.get()}' · 소재 '{self.genre_var.get()}' 로 챕터를 만듭니다.", font=("맑은 고딕", 10, "bold")).grid(row=0, column=0, columnspan=2, sticky="w")
        ttk.Label(f, text="챕터 수").grid(row=1, column=0, sticky="e", pady=4)
        n_var = tk.StringVar(value="7")
        ttk.Spinbox(f, from_=2, to=20, textvariable=n_var, width=5).grid(row=1, column=1, sticky="w")
        ttk.Label(f, text="챕터당 길이(초)").grid(row=2, column=0, sticky="e", pady=4)
        sec_var = tk.StringVar(value="75")
        ttk.Spinbox(f, from_=30, to=240, increment=5, textvariable=sec_var, width=5).grid(row=2, column=1, sticky="w")
        ttk.Label(f, text="전체 주제(비우면 AI가 정함)").grid(row=3, column=0, sticky="e", pady=4)
        theme_var = tk.StringVar(value=self.topic_var.get())
        ttk.Entry(f, textvariable=theme_var, width=40).grid(row=3, column=1, sticky="w")
        ttk.Label(f, text="챕터 주제 직접 입력 (한 줄에 하나, 비우면 AI 추천)").grid(row=4, column=0, columnspan=2, sticky="w", pady=(8, 0))
        box = ScrolledText(f, height=6, width=60, font=("맑은 고딕", 10))
        box.grid(row=5, column=0, columnspan=2)
        land_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(f, text="가로 화면(1920×1080)으로 전환", variable=land_var).grid(row=6, column=0, columnspan=2, sticky="w", pady=(8, 0))
        narr_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(f, text="나레이션 켜기 (롱폼은 음성이 있어야 끝까지 봅니다)", variable=narr_var).grid(row=7, column=0, columnspan=2, sticky="w")
        ttk.Label(f, text="예상: 7챕터 × 75초 ≈ 9분 (8분 이상이면 중간 광고 가능). 챕터마다 AI 호출이 있어 20~40분 걸릴 수 있습니다.",
                  foreground="gray").grid(row=8, column=0, columnspan=2, sticky="w", pady=(8, 0))
        res = {}

        def ok():
            try:
                res["n"], res["sec"] = int(n_var.get()), float(sec_var.get())
            except ValueError:
                return
            res["theme"] = theme_var.get().strip()
            res["topics"] = [l.strip() for l in box.get("1.0", "end").split("\n") if l.strip()]
            res["land"], res["narr"] = land_var.get(), narr_var.get()
            dlg.destroy()
        bf = ttk.Frame(f)
        bf.grid(row=9, column=0, columnspan=2, sticky="e", pady=(10, 0))
        ttk.Button(bf, text="취소", command=dlg.destroy).pack(side="right")
        ttk.Button(bf, text="만들기 시작", command=ok).pack(side="right", padx=6)
        self.wait_window(dlg)
        if "n" not in res:
            return
        if res["land"]:
            self.vars["format"].set("롱폼 가로(1920×1080)")
            self.apply_format("롱폼 가로(1920×1080)")
        if res["narr"]:
            self.vars["narration"].set("on")
        self.vars["intro_sec"].set("2.5")
        self.vars["hold_end"].set("4")
        n, sec, theme, topics = res["n"], res["sec"], res["theme"], res["topics"]
        model, cat, genre, judge = self.model_var.get().strip(), self.cat_var.get(), self.genre_var.get(), self.judge_var.get()
        research, autophoto = self.research_var.get(), self.autophoto_var.get()
        factual, tmap = cat_info(cat)
        media_dir = self.media_dir()
        log = self.log_bg

        def job():
            ideas = list(topics)
            if len(ideas) < n:
                iu = (f"콘텐츠 종류: {cat}" + (" (실제 사건·사실만)" if factual else "") + f"\n소재: {genre}\n소재 공식: {tmap.get(genre, ('', ''))[0]}"
                      + (f"\n전체 영상 주제: {theme}" if theme else "") + f"\n이 소재로 롱폼 영상의 챕터 주제 {n - len(ideas)}개를 만들어줘. 서로 겹치지 않고 점점 더 놀라운 순서로.")
                if research:
                    iu += "\n[웹 검색 모드] WebSearch 로 실제 사건·발견·현상을 찾아 고른다."
                ideas += [str(x) for x in ask_json(model, IDEA_SYSTEM, iu, tools=WEB_TOOLS if research else None).get("ideas", [])]
            ideas = ideas[:n]
            chapters = []
            for i, topic in enumerate(ideas):
                if self.cancel.is_set():
                    raise RuntimeError("취소됨")
                log(f"📑 챕터 {i + 1}/{n}: {topic}")
                r_ = self.generate_story(model, cat, topic, genre, sec, judge, log, research, autophoto, "", media_dir)
                chapters.append(r_)
            log("전체 구성(제목·오프닝·클로징) 만드는 중...")
            summary = json.dumps([{"title": c["title"], "story": story_text_only(c["story"])[:600]} for c in chapters], ensure_ascii=False)
            plan = ask_json(model, LONGFORM_SYSTEM, f"콘텐츠 종류: {cat}\n소재: {genre}" + (f"\n전체 주제: {theme}" if theme else "") + f"\n\n[챕터들]\n{summary}")
            ctitles = plan.get("chapter_titles") or []
            parts = [strip_placeholders(str(plan.get("opening", "")).strip())]
            for i, c in enumerate(chapters):
                t = ctitles[i] if i < len(ctitles) and str(ctitles[i]).strip() else c["title"]
                parts.append(f"## {i + 1}. {t}\n\n" + c["story"].strip())
            parts.append(strip_placeholders(str(plan.get("closing", "")).strip()))
            story = "\n\n".join(p for p in parts if p)
            sources = [x for c in chapters for x in (c.get("sources") or [])]
            return plan.get("title") or (theme or chapters[0]["title"]), story, sources, chapters

        def done(resu):
            title, story, sources, chapters = resu
            self.title_var.set(title)
            self.set_story(story)
            self.set_sources(sources[:12], "")
            self.vars["target_sec"].set("0")
            self.bgm_made = None
            self.write_log(f"📺 롱폼 대본 완성: {title} · 챕터 {len(chapters)}개 · 본문 {len(story_text_only(story))}자")
            self.write_log("  → '🎙 나레이션 만들기'로 음성을 만든 뒤 MP4를 만드세요 (MP4 만들기를 바로 눌러도 자동으로 만듭니다)")
            self.refresh_preview()
            self.save_cfg()
        self.write_log(f"📺 롱폼 만들기 시작: {n}챕터 × {sec:.0f}초, {cat} · {genre}")
        self.run_bg("롱폼 만드는 중...", job, done)

    def open_folder(self):
        folder = self.get_settings()["out_dir"]
        os.makedirs(folder, exist_ok=True)
        if os.name == "nt":
            os.startfile(folder)
        else:
            subprocess.Popen(["open" if os.uname().sysname == "Darwin" else "xdg-open", folder])


if __name__ == "__main__":
    App().mainloop()
