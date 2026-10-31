r"""장문(긴 나레이션 다큐) 자동 제작: 대본 → 나레이션 → MP4 → 썸네일·업로드 문구
- 설정은 '장문_설정.json' (처음 실행하면 기본값으로 만들어짐 - 주제·길이·배경음 크기를 고쳐서 쓰세요)
- 일시정지: 장문_일시정지.bat (출근 전) / 재개: 장문_재개.bat (만들기 창이 꺼져 있으면 새로 띄워서 이어서 함)
- 끄기 전: 장문_끄기전_정리.bat (지금 단계가 끝나면 멈추고 저장 → PC 끄기/절전 선택)
- 창을 닫거나 PC를 꺼도: 장문_만들기.bat(또는 장문_재개.bat)을 다시 실행하면 끝난 단계(조사·구성안·챕터·나레이션 문단·영상 구간)는 건너뛰고 이어서 함
- 주의: 웹 조사·챕터 집필처럼 AI가 답하는 동안(최대 15분)은 중간 저장이 없음 → 그 사이 끄면 그 단계 하나만 다시 함
- 연속 제작: 장문_연속제작.bat → 기획자 AI가 전체 라인업을 짜고 검토자 AI가 겹침·반응·사실 확인 가능성을 평가해 고친 뒤,
  그 순서대로 '연속_편수' 편을 만듦 (소재는 '연속_소재' 목록 안에서, 비우면 기본 목록). 기획 기록: output\장문\_연속제작_기획.txt
- 프로그램 설정 파일(shorts_novel_config.json)은 바꾸지 않음
"""
import importlib.util
import json
import os
import re
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
CFG = os.path.join(HERE, "장문_설정.json")
PAUSE = os.path.join(HERE, "장문_일시정지중.flag")
HISTORY = "--역사" in sys.argv or "--history" in sys.argv   # 역사 채널: 실록·정사 기록으로 보는 진짜 역사만 (역사_연속제작.bat)
SEED = os.path.join(HERE, "역사" if HISTORY else "실화", "주제목록.txt")   # --실화/--역사 때 AI 기획 대신 쓸 '정해진 주제' 목록 (있으면 순서대로)
STATE_NAME = "_연속제작_진행_역사.json" if HISTORY else "_연속제작_진행.json"   # 역사 채널은 진행 기록을 따로 (실화 연속 제작과 섞이지 않게)
_OLD_SEED = os.path.join(HERE, "실화_주제목록.txt")
if not HISTORY and os.path.exists(_OLD_SEED) and not os.path.exists(SEED):   # 예전 위치(프로그램 폴더 바로 아래)에 있으면 실화\ 폴더로 옮김
    os.makedirs(os.path.dirname(SEED), exist_ok=True)
    os.replace(_OLD_SEED, SEED)
DEFAULT = {
    "주제": "수심 1만 미터, 마리아나 해구 바닥에는 무엇이 살고 있을까?",
    "소재": "심해의 세계",
    "길이_분": 12,               # 규칙: 긴 영상은 10~15분
    "배경음": "심해",
    "배경음_크기": 0.03,      # 0~2 (0.03 = 거의 안 들림, 목소리가 또렷하게)
    "성우_프리셋": "",         # 🎤 성우 선택 창에서 ⭐ 새 성우로 저장한 이름 (비우면 기본: 남자 성우 2)
    "웹조사": True,
    "쇼츠_만들기": False,      # 규칙: 쇼츠는 기본적으로 안 만듦. true 로 하거나 명령에 --쇼츠 를 붙이면 롱폼마다 세로 쇼츠도 만듦
    "챕터별_사진": True,
    "사진_간격_초": 8,           # 규칙: 관련 사진 최대한 많이 (8초마다 한 장)
    "영상_구간_분": 2,
    "연속_편수": 5,
    "연속_소재": [],
    "제목_표시": "왼쪽 위 작게",      # 위 가운데 / 왼쪽 위 작게 / 숨김  (10분 다큐는 큰 제목이 화면을 가려 작게)
    "나레이션_먼저": True,          # 사용자 결정 2026-10-31: 대본 → 나레이션(문단마다 시간 기록) → 그 시간에 맞춰 그림 → 배경음·자막과 합치기 (그림 스타일일 때)
    "문단_최대_글자": 120,          # 나레이션 먼저일 때 이보다 긴 문단은 문장 끝에서 나눔 (약 15초) → 그림이 문단이 바뀔 때 바뀌어 박자가 맞음
    "그림_사용자점검": True,        # 사용자 결정 2026-10-31: 그림을 다 그리면 40장씩 모음(_그림점검_N.jpg)을 만들고 멈춤 → 점검 뒤 같은 명령에 --점검완료 를 붙여 이어서
    "자막": "보임",                 # 보임(기본, 사용자 결정 2026-10-31: 자막은 그대로) / 숨김(나레이션만)
    "자막_스타일": "자동",            # 자동(소재에 맞춰) 또는 프로그램의 '인기 롱폼 스타일' 이름 그대로
    "끝나면": "그대로",              # 연속 제작이 끝난 뒤: 그대로 / 절전 / 끄기  (시작할 때 물어봄)
    "claude_path": "",             # Claude Code 실행 파일 경로 (자동으로 못 찾을 때만 적음, 예: C:\\Users\\이름\\.local\\bin\\claude.exe)
    "채널_소개": "DreamArt - 보고 나면 가벼운 지식이 남는 10분 다큐, 잠들기 전 마음을 가라앉히는 명상·수면 음악, 가끔 웃음이 나는 이야기까지 여러 주제를 다루는 채널",
    # 연속 제작 구성: 순서대로 돌아가며 (지식 = 10분 지식 다큐, 명상 = 명상·수면 음악 영상, 재미 = 웃기거나 뭉클한 이야기 낭독)
    "연속_구성": ["지식", "지식", "명상", "지식", "재미"],
    "명상_분": 20,
    "명상_프리셋": [],      # 비우면 아래 MEDITATION_PRESETS 를 돌아가며
    "재미_소재": [],        # 비우면 아래 FUN_GENRES 를 돌아가며
    "그림_스타일": "자동(돌아가며)",   # 이야기 편 그림 스타일: 자동 또는 프로그램의 그림 스타일 이름(웹툰, 지브리풍 손그림 애니, 70~80년대 순정만화 …) 또는 직접 쓴 영어 지시
    "이미지": "근거 사진(웹)",   # 사실 주제 이미지: 근거 사진(웹) / 그림: 애니(웹툰) / 그림: 애니+수채화 / 그림: 파스텔 감성 / 그림: 애니 일러스트 / 그림: 애니 모델 그대로 (그림은 이 PC에서 그림)
    "역사_이미지": "그림: 역사 수묵 담채",   # 역사 채널(--역사) 이미지: 옛 인물·전투는 사진이 없어 이 PC에서 그림 (사용자 결정 2026-10-30: 샘플 4번째 그림의 수묵 담채). "근거 사진(웹)" 으로 바꾸면 웹 사진
    "그림_간격_초": 10,      # 그림(이미지가 '그림: …')일 때 간격. 대본 글자 수로 어림한 초라 실제 화면에서는 약 8초 (규칙: 그림 한 장 5~12초)
    "썸네일_선택": "프로그램",   # 유튜브 썸네일 최종본: 프로그램(AI가 고른 것 그대로) / 외부 자동(소재탐색 썸네일 중 점수로 고른 것) /
                               # 수동(창): 영상이 끝나면 프로그램 후보 + 소재탐색 후보를 한 화면에 띄워 클릭으로 고름 (연속 제작 중엔 창을 띄우지 않고 '외부 자동'처럼)
                               # 나중에 고르려면: 썸네일_고르기.bat 에 <제목>_썸네일_후보 폴더를 끌어다 놓기
}
MEDITATION_PRESETS = ["명상 · 싱잉볼", "싱잉볼 · 깊은 수면", "오르골 · 캐논", "싱잉볼 · 432Hz", "오르골 자장가 · 브람스", "싱잉볼 · 7 차크라",
                      "오르골 · 꿈속의 고향", "싱잉볼 · 528Hz", "오르골 · 어메이징 그레이스", "싱잉볼 · 노래하는 볼(문지르기)"]
FUN_GENRES = ["[이야기] 코믹 일상 장편 썰", "[이야기] 조선 야담·기담", "[이야기] 감동 휴먼 드라마", "[이야기] 사연 낭독(가족·시댁·이혼)", "[이야기] 시니어 인생 사연"]
MIN_PER_MUSIC = (0.6, 1.0)   # 명상 음악 영상 1분당 걸리는 시간(분): 20분 영상 → 12~20분
# 연속 제작 때 '연속_소재'가 비어 있으면 이 소재들을 돌아가며 씀 (10분 롱폼으로 반응 좋은 묶음)
BATCH_GENRES = ["세계의 축제", "신기한 풍속과 전통", "역사를 바꾼 결정적 순간", "세계의 외딴 마을과 작은 나라", "고고학 발굴 이야기",
                "세계의 음식 문화", "대형 사고에서 배운 교훈", "도시 하나 깊이 보기", "발명과 우연한 발견", "세계의 신화와 민담 여행",
                "심해의 세계", "세계의 신기한 법과 예절", "미라와 무덤의 비밀", "세계의 명절과 새해 풍습", "최신 고고학 발견"]
# --실화(또는 --true-story): 실화 소재만 돌아가며 10분 다큐 연속 제작 (모두 지식 다큐 · 명상/재미 섞지 않음)
TRUE_STORY_GENRES = ["[실화] 과학이 밝혀낸 미스터리", "[실화] 최근 밝혀진 과학 발견", "[실화] 극한 생존기", "[실화] 미제 사건의 기록", "[실화] 사라진 사람과 배·비행기",
                     "[실화] 믿기 힘든 우연", "[실화] 희대의 사기와 범죄", "[실화] 평범한 사람의 위대한 순간", "[실화] 재난에서 살아남은 날",
                     "[실화] 불가능에 도전한 사람들"]
HISTORY_GENRES = ["[실화] 기록으로 보는 진짜 역사"]
SAMGUK_WORDS = ["삼국", "정사", "연의", "관우", "조조", "유비", "제갈량", "주유", "여포", "손견", "손권", "화웅", "동탁", "초선", "조운", "조자룡", "맹획", "적벽", "진수", "배송지"]   # 삼국지 편 알아보는 말
HISTORY_CHANNEL_NOTE = ("기록으로 보는 진짜 역사 - 사극과 소설(삼국지연의)로 알려진 장면을 조선왕조실록·정사 『삼국지』의 실제 기록과 맞대어 보는 "
                        "10~30분 역사 다큐 채널. 시청자는 역사를 좋아하는 중장년층")
ONE = "--한편" in sys.argv or "--one" in sys.argv     # 버튼 하나로: AI가 새 인기 주제를 골라 긴 영상 '한 편'만 끝까지 (묻지 않음, 쇼츠 없음)
BATCH = ONE or HISTORY or "--batch" in sys.argv or "--실화" in sys.argv or "--true-story" in sys.argv
TRUE_STORY = ONE or HISTORY or "--실화" in sys.argv or "--true-story" in sys.argv
MORE_PHOTOS = "--more-photos" in sys.argv
SEG_SEC = 120

T0 = time.time()
LOG_FILE = os.path.join(HERE, "장문_진행기록.txt")


def log(x):
    line = f"[{time.strftime('%H:%M')} · {(time.time() - T0) / 60:5.1f}분] {x}"
    print(line, flush=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


PLANNER_SYSTEM = """너는 한국 유튜브 지식 다큐 채널의 수석 기획자다. 10분짜리 사실 기반 롱폼 영상 여러 편의 라인업(편성표)을 짠다.
원칙: (1) 실제로 존재하는 사건·장소·풍습·발견만 (지어내지 않는다) (2) 각 편은 제목처럼 궁금증을 부르는 질문·반전형 주제 35자 이내
(3) 편 사이에 대상·지역·시대·감정(놀라움/감동/소름/유머)이 겹치지 않게 골고루 (4) 최근 1~2년 화제·새 발견과 이어진 편을 절반 이상
(5) 위키미디어 커먼즈 등에서 무료 사진을 구하기 쉬운 주제 우선 (6) 민감한 주제(참사 피해자 조롱, 특정 종교·민족 비하)는 피한다.
WebSearch 로 최근 화제와 유튜브에서 비슷한 긴 영상의 반응을 확인하고 고른다.
반드시 JSON만 출력: {"lineup": [{"genre": "소재(주어진 목록 중 하나 그대로)", "topic": "주제", "why": "왜 지금 반응이 좋을지 한 줄", "hook": "첫 문장 훅 한 줄"}], "note": "라인업 전체 의도 두 줄"}"""

REVIEWER_SYSTEM = """너는 유튜브 지식 다큐 채널의 까다로운 편성 검토자다. 기획자가 낸 라인업을 편마다 평가하고, 문제가 있으면 같은 소재 안에서 더 나은 주제로 바꾼다.
검토 항목: (a) 겹침 - 다른 편이나 이미 만든 주제와 똑같은 주제(같은 대상의 같은 발견·사건)인가 (같은 분야·비슷한 대상이라도 다른 연구·다른 각도면 괜찮음) (b) 반응 - 제목만 보고 누를 만큼 궁금한가, 너무 교과서적이진 않은가
(c) 사실 확인 가능성 - 10분을 채울 만큼 공개된 자료(기사·논문·백과)가 충분한가, 루머·음모론에 기대지 않는가 (d) 사진 - 무료 사진을 구할 수 있는 대상인가
(e) 안전 - 비하·선정·저작권 문제가 없는가. WebSearch 로 의심스러운 편은 실제로 자료가 있는지 확인한다.
각 편에 keep(그대로) 또는 replace(바꿈)를 정하고, replace 면 새 topic·why·hook 을 쓴다. 바꾸는 편은 전체의 절반을 넘기지 않는다.
반드시 JSON만 출력: {"review": [{"idx": 0, "verdict": "keep|replace", "score": 1~10, "reason": "한 줄", "topic": "유지면 원래 주제, 바꾸면 새 주제", "genre": "소재", "why": "...", "hook": "..."}], "note": "총평 두 줄"}"""


CHANNEL_NOTE = DEFAULT["채널_소개"]


def plan_lineup(m, app, genres, n, minutes, seen, log, out_root):
    """기획자 AI → 검토자 AI 두 단계로 n편 라인업을 정함. 기록은 _연속제작_기획.txt 에"""
    model = app.model_var.get().strip()
    topics = m.cat_info(m.DOC_CATEGORY)[1]
    glist = "\n".join(f"- {g_}: {topics.get(g_, ('', ''))[0][:120]}" for g_ in genres)
    seen_txt = ("\n\n[이미 만든 주제 - 똑같은 주제만 피한다. 같은 분야·비슷한 대상이라도 다른 연구·다른 사건·다른 각도면 괜찮다]\n- " + "\n- ".join(seen[-60:])) if seen else ""
    base = (f"채널: {CHANNEL_NOTE}\n영상: 각 {minutes}분 사실 기반 나레이션 다큐, 총 {n}편\n오늘: {time.strftime('%Y년 %m월 %d일')}\n"
            "라인업은 이 채널의 방향(여러 주제를 번갈아, 구독자가 '다음 편도 보고 싶게')에 맞춘다.\n"
            f"쓸 수 있는 소재 목록(각 편의 genre 는 이 중 하나, 가능하면 서로 다른 소재로):\n{glist}" + seen_txt)
    log(f"🧭 기획자 AI: {n}편 라인업 짜는 중... (웹 검색, 3~8분)")
    d1 = m.ask_json_alive(model, PLANNER_SYSTEM, base + f"\n\n{n}편 라인업을 짜라.", tools=m.WEB_TOOLS, log=log, label="기획자")
    lineup = [x for x in (d1.get("lineup") or []) if isinstance(x, dict) and str(x.get("topic", "")).strip()][:n]
    if not lineup:
        raise RuntimeError("기획자가 라인업을 만들지 못했습니다")
    for x in lineup:
        if x.get("genre") not in topics:
            x["genre"] = genres[0]
    for i, x in enumerate(lineup):
        log(f"   {i + 1}. [{x['genre']}] {x['topic']}  - {str(x.get('why', ''))[:60]}")
    log("🔍 검토자 AI: 겹침·반응·사실 확인 가능성 평가 중... (웹 검색, 3~8분)")
    plan_txt = "\n".join(f"{i}. [{x['genre']}] {x['topic']} / 이유: {x.get('why', '')} / 훅: {x.get('hook', '')}" for i, x in enumerate(lineup))
    d2 = m.ask_json_alive(model, REVIEWER_SYSTEM, base + f"\n\n[기획자 라인업]\n{plan_txt}\n\n편마다 평가하고 고쳐라.", tools=m.WEB_TOOLS, log=log, label="검토자")
    review = [x for x in (d2.get("review") or []) if isinstance(x, dict)]
    final, lines = [], []
    for i, x in enumerate(lineup):
        r = next((r_ for r_ in review if str(r_.get("idx")) == str(i)), None)
        item = dict(x)
        tag = "유지"
        if r and str(r.get("verdict", "")).lower().startswith("replace") and str(r.get("topic", "")).strip():
            item = {"genre": r.get("genre") if r.get("genre") in topics else x["genre"], "topic": str(r["topic"]).strip(),
                    "why": r.get("why") or x.get("why", ""), "hook": r.get("hook") or x.get("hook", "")}
            tag = f"교체(원래: {x['topic']})"
        if r and r.get("reason"):
            item["review"] = str(r.get("reason"))
        final.append(item)
        sc = f" {r.get('score')}점" if r and r.get("score") is not None else ""
        lines.append(f"{i + 1}. [{item['genre']}] {item['topic']}{sc} - {tag}" + (f" / 검토: {r.get('reason', '')}" if r else "")
                     + f"\n     왜: {item.get('why', '')}\n     훅: {item.get('hook', '')}")
        log(f"   {i + 1}. [{item['genre']}] {item['topic']}{sc} - {tag}")
    rec = (f"[{time.strftime('%Y-%m-%d %H:%M')}] 연속 제작 기획 ({n}편 · {minutes}분)\n기획 의도: {d1.get('note', '')}\n검토 총평: {d2.get('note', '')}\n"
           + "\n".join(lines) + "\n\n")
    try:
        with open(os.path.join(out_root, "_연속제작_기획.txt"), "a", encoding="utf-8") as f:
            f.write(rec)
    except OSError:
        pass
    return final


def load_seed_lineup(m):
    """실화\\주제목록.txt 를 읽어 [{genre, topic, memo, folder}] 라인업으로. 한 줄 = 한 편.
    형식: '소재 | 주제 | 기획메모' (소재 생략 시 '[실화] 과학이 밝혀낸 미스터리'). '#' 줄·빈 줄 무시.
    3번째 칸(선택): 실화_소재탐색.py 가 만든 기획메모 폴더(안의 기획메모.md 를 읽음) 또는 .md/.txt 파일 또는 그냥 메모 글
    → 대본 AI 의 '최우선 참고자료'로 들어가고, 폴더면 그 안의 thumb_*.jpg 가 영상 완성 뒤 썸네일 후보에 추가됨."""
    if not os.path.exists(SEED):
        return []
    topics_map = m.cat_info(m.DOC_CATEGORY)[1]
    default_genre = HISTORY_GENRES[0] if HISTORY else "[실화] 과학이 밝혀낸 미스터리"
    if default_genre not in topics_map:
        default_genre = next(iter(topics_map))
    out = []
    try:
        for raw in open(SEED, encoding="utf-8"):
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            parts = [x.strip() for x in line.split("|", 2)]
            if len(parts) == 1:
                g, t, memo_src = default_genre, parts[0], ""
            else:
                g, t = parts[0], parts[1]
                memo_src = parts[2] if len(parts) > 2 else ""
            if not t:
                continue
            if g not in topics_map:
                g = default_genre
            memo, folder = seed_memo(memo_src)
            out.append({"genre": g, "topic": t, "memo": memo, "folder": folder})
    except OSError:
        return []
    return out


def seed_memo(src):
    """주제 목록 3번째 칸 → (메모 글, 폴더). 폴더면 기획메모.md, 파일이면 내용, 아니면 글 그대로."""
    src = (src or "").strip()
    if not src:
        return "", ""
    try:
        if os.path.isdir(src):
            p = os.path.join(src, "기획메모.md")
            txt = open(p, encoding="utf-8").read() if os.path.exists(p) else ""
            return ("[소재탐색 기획메모 - 출처 링크는 대본 전에 웹에서 확인]\n" + txt) if txt else "", src
        if os.path.isfile(src) and src.lower().endswith((".md", ".txt")):
            return "[기획메모]\n" + open(src, encoding="utf-8").read(), os.path.dirname(src)
    except OSError:
        pass
    return "[기획메모]\n" + src, ""


def made_topics(m, out_root):
    """이미 만든(만들기 시작한) 장문 주제들 - 연속 제작 때 같은 주제를 피하려고"""
    if not os.path.isdir(out_root):
        return []
    return m._load_korean_reading("콘텐츠_정리").all_work_names(out_root)   # 바깥 + 콘텐츠 폴더 안


def pick_topic(m, app, genre, seen, log):
    """연속 제작: AI(웹 검색)가 이 소재로 지금 반응 좋을 10분 다큐 주제 하나를 고름"""
    topics = m.cat_info(m.DOC_CATEGORY)[1]
    formula = topics.get(genre, ("(사용자가 직접 정한 소재)", ""))[0]
    if m.doc_is_fiction(genre):   # 이야기 낭독: 창작 설정 (웹 검색 없이)
        user = (f"콘텐츠 종류: 장편 창작 이야기 낭독 (허구)\n소재: {genre}\n소재 공식: {formula}\n"
                "이 장르로 10분 낭독용 이야기 5개를 만들어줘. 각 주제는 '장르 표시 + 주인공의 상황과 갈등 한 줄'(35자 이내, 결말 금지, "
                "예: '[코믹] 엄마가 ChatGPT를 배우고 집안이 뒤집혔다'). 요즘 유튜브 장편 낭독에서 반응 좋은 설정으로, 실존 인물·기존 작품 금지.")
        if seen:
            user += "\n\n[이미 만든 주제 - 똑같은 이야기만 피한다. 비슷한 장르·설정이라도 인물·사건이 다르면 괜찮다]\n- " + "\n- ".join(seen[-60:])
        user += '\n출력: {"ideas": ["..."], "why": ["..."]} (반응이 좋을 순서대로)'
        d = m.ask_json_alive(app.model_var.get().strip(), m.IDEA_SYSTEM, user, log=log, label="이야기 주제 고르기")
        ideas = [str(x).strip() for x in (d.get("ideas") or []) if str(x).strip()]
        ideas = [x for x in ideas if x not in seen] or ideas
        if not ideas:
            raise RuntimeError("주제를 고르지 못했습니다")
        log(f"🎯 고른 이야기: {ideas[0]}")
        return ideas[0]
    user = (f"콘텐츠 종류: {m.DOC_CATEGORY} (실제 사건·사실만)\n소재: {genre}\n소재 공식: {formula}\n"
            f"이 소재로 10분 나레이션 다큐로 풀 수 있는, 지금 유튜브에서 반응 좋을 주제 5개를 만들어줘 (제목처럼 궁금증을 부르는 질문·반전형, 35자 이내). "
            + (f"오늘({time.strftime('%Y년 %m월 %d일')}) 기준 최근 3개월 안에 발표된 연구·발견만 고른다(발표 날짜·저널을 꼭 확인). 오래된 이야기는 제외.\n"
               if "최근 밝혀진" in genre else
               f"오늘({time.strftime('%Y년 %m월')}) 기준 최근 1~2년 화제·새 발견과 이어진 것을 먼저, 나머지는 꾸준히 인기 있는 것으로.\n")
            + "[웹 검색 모드] WebSearch 로 최근 화제가 된 사건·발견·현상을 찾아 그중에서 고른다. 실제로 존재하는 것만. "
            "유튜브에서 비슷한 주제의 긴 영상이 반응이 좋았는지, 아직 덜 다뤄진 틈새인지도 살핀다.")
    if seen:
        user += "\n\n[이미 만든 주제 - 똑같은 주제(같은 대상의 같은 발견·사건)만 피한다. 같은 분야·비슷한 대상이라도 다른 연구·다른 각도면 괜찮다]\n- " + "\n- ".join(seen[-60:])
    user += '\n출력: {"ideas": ["..."], "why": ["..."]} (반응이 좋을 순서대로)'
    d = m.ask_json_alive(app.model_var.get().strip(), m.IDEA_SYSTEM, user, tools=m.WEB_TOOLS, log=log, label="인기 주제 고르기")
    ideas = [str(x).strip() for x in (d.get("ideas") or []) if str(x).strip()]
    ideas = [x for x in ideas if x not in seen] or ideas
    if not ideas:
        raise RuntimeError("주제를 고르지 못했습니다")
    why = (d.get("why") or [""])[0] if isinstance(d.get("why"), list) else ""
    log(f"🎯 고른 주제: {ideas[0]}" + (f"  ({str(why)[:80]})" if why else ""))
    return ideas[0]


MIN_PER_EP = (4.0, 6.0)   # 10분 영상 한 편에 걸리는 시간(이 PC 실측): 영상 1분당 4~6분 → 10분이면 40~60분


def _fmt_hours(mins):
    h, mm = int(mins // 60), int(round(mins % 60))
    return ((f"{h}시간 " if h else "") + (f"{mm}분" if mm or not h else "")).strip()


def ask_batch_plan(c):
    """연속 제작 시작 전: 몇 편 만들지 묻고, 예상 시간을 보여 준 뒤 정말 할지 확인. 설정 파일의 연속_편수를 갱신"""
    out_root = os.path.join(HERE, "output", "장문")
    st = {}
    try:
        st = json.load(open(os.path.join(out_root, STATE_NAME), encoding="utf-8"))
    except Exception:
        pass
    done = len(st.get("done") or [])
    cur = st.get("current") or {}
    minutes = float(c.get("길이_분", 10))
    n0 = int(c.get("연속_편수") or 5)
    print("=" * 60)
    print(f"🔁 장문 연속 제작  (한 편 = 약 {minutes:.0f}분 영상 · 소재를 돌아가며 AI가 인기 주제를 고름)")
    if done or cur.get("주제"):
        print(f"   이미 끝난 편: {done}개" + (f" · 만들다 멈춘 편: {cur.get('주제')}" if cur.get("주제") else "") + "  → 끝난 편 다음부터 이어서 합니다")
    print("=" * 60)
    try:
        ans = input(f"모두 몇 편까지 만들까요? [Enter = {n0}편] : ").strip()
    except EOFError:
        ans = ""
    if ans:
        try:
            n0 = max(1, int(float(ans)))
        except ValueError:
            print("숫자가 아니어서 기본값을 씁니다.")
    if n0 <= done:
        print(f"이미 {done}편이 끝나 있어 더 만들 편이 없습니다. 더 만들려면 {done}보다 큰 숫자를 넣으세요.")
        return False
    todo = n0 - done
    comp = [str(x) for x in (c.get("연속_구성") or ["지식"]) if str(x) in ("지식", "명상", "재미")] or ["지식"]
    kinds = [comp[i % len(comp)] for i in range(done, n0)]
    med_min = float(c.get("명상_분", 20))
    n_med = kinds.count("명상")
    lo = minutes * MIN_PER_EP[0] * (todo - n_med) + med_min * MIN_PER_MUSIC[0] * n_med
    hi = minutes * MIN_PER_EP[1] * (todo - n_med) + med_min * MIN_PER_MUSIC[1] * n_med
    plan_extra = 0 if len(st.get("plan") or []) >= kinds.count("지식") else 10
    print()
    print(f"▶ 만들 편수: {todo}편" + (f" (끝난 {done}편 제외, 총 {n0}편)" if done else "")
          + f"  → 지식 다큐 {kinds.count('지식')}편 · 명상 음악 {n_med}편({med_min:.0f}분) · 재미 이야기 {kinds.count('재미')}편   (구성 순서: {' → '.join(comp)})")
    print(f"▶ 예상 소요: 약 {_fmt_hours(lo + plan_extra)} ~ {_fmt_hours(hi + plan_extra)}"
          + (f"  (기획·검토 {plan_extra}분 포함, " if plan_extra else "  (") + f"한 편 {_fmt_hours(minutes * MIN_PER_EP[0])}~{_fmt_hours(minutes * MIN_PER_EP[1])})")
    print(f"   끝나는 시각(예상): {time.strftime('%H:%M', time.localtime(time.time() + (lo + plan_extra) * 60))} ~ "
          f"{time.strftime('%m/%d %H:%M', time.localtime(time.time() + (hi + plan_extra) * 60))}")
    print("   중간에 멈추려면 장문_일시정지.bat, PC를 꺼야 하면 장문_끄기전_정리.bat (끝난 편은 남고 이어서 할 수 있음)")
    try:
        ok = input("이대로 시작할까요? (y = 시작 / 그 외 = 취소) : ").strip().lower()
    except EOFError:
        ok = ""
    if ok not in ("y", "yes", "ㅇ", "예", "네"):
        return False
    try:
        after = input("다 끝나면 PC를 어떻게 할까요? [Enter = 그대로 / 1 = 절전(최대 절전) / 2 = 끄기] : ").strip()
    except EOFError:
        after = ""
    c["끝나면"] = {"1": "절전", "2": "끄기"}.get(after, "그대로")
    if c["끝나면"] != "그대로":
        print(f"   → 모두 끝나면 1분 뒤 {c['끝나면']} (취소: 그 창에서 아무 키)")
    if n0 != int(c.get("연속_편수") or 5):
        c["연속_편수"] = n0
        try:
            saved = json.load(open(CFG, encoding="utf-8"))
            saved["연속_편수"] = n0
            json.dump(saved, open(CFG, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        except Exception:
            pass
    return True


def main():
    if not os.path.exists(CFG):
        json.dump(DEFAULT, open(CFG, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    c = dict(DEFAULT, **json.load(open(CFG, encoding="utf-8")))
    global CHANNEL_NOTE
    CHANNEL_NOTE = str(c.get("채널_소개") or DEFAULT["채널_소개"])
    if HISTORY:        # 역사 채널 모드: 기록으로 보는 진짜 역사만, 주제는 역사\주제목록.txt 부터
        c["연속_소재"] = list(HISTORY_GENRES)
        c["연속_구성"] = ["지식"]
        CHANNEL_NOTE = HISTORY_CHANNEL_NOTE
        c["이미지"] = str(c.get("역사_이미지") or DEFAULT["역사_이미지"])   # 실화 채널과 따로: 역사 편은 정해 둔 스타일로 그림
        print("📜 역사 연속 제작 모드: 실록·정사 기록으로 보는 진짜 역사 다큐를 만듭니다 (주제: 역사\\주제목록.txt)")
    elif TRUE_STORY:   # 실화 모드: 실화 소재만, 전부 지식 다큐로 (설정 파일의 연속_소재·연속_구성 무시)
        c["연속_소재"] = list(TRUE_STORY_GENRES)
        c["연속_구성"] = ["지식"]
        print("📖 실화 연속 제작 모드: 실화 소재만 돌아가며 10분 다큐를 만듭니다 (명상·재미 편 없음)")
    if ONE:
        c["끝나면"] = "그대로"
        print("▶ 한 편 만들기: AI가 아직 안 다룬 새 주제를 골라 긴 영상 한 편을 끝까지 만듭니다 (쇼츠 없음, 약 2~3시간).")
    elif BATCH and not ask_batch_plan(c):
        print("취소했습니다. (아무것도 만들지 않음)")
        return
    spec = importlib.util.spec_from_file_location("snm", os.path.join(HERE, "shorts_novel_maker_supertonic.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    exe = m.find_claude()
    if not exe:
        print(m.CLAUDE_INSTALL_HELP)
        log("❌ Claude Code를 찾지 못해 시작할 수 없습니다 (위 안내 참고)")
        return
    print(f"Claude Code: {exe}")
    try:
        ver = m.check_claude()
        print(f"  버전 {ver} · 연결 확인됨")
    except Exception as e:
        print("  ⚠ Claude Code 실행은 되지만 응답이 이상합니다 (로그인 안 됨?): " + str(e)[:200])
        print("  터미널에서 'claude' 를 한 번 실행해 로그인한 뒤 다시 시도하세요.")
        return
    global SEG_SEC
    m.DOC_PHOTO_SEC = max(6, float(c.get("사진_간격_초", 8)))   # 규칙: 관련 사진 최대한 많이 (8초마다 한 장)
    if str(c.get("이미지") or "").startswith("그림:"):    # 이 PC에서 그리는 그림: 한 장 5~12초 (그리는 효과로 볼거리, 사용자 결정 2026-10-30)
        m.DOC_PHOTO_SEC = float(c.get("그림_간격_초") or DEFAULT["그림_간격_초"])
    SEG_SEC = int(max(1, float(c.get("영상_구간_분", 2))) * 60)

    app = m.App()
    app.withdraw()
    app.update()
    gate = m.PauseGate(PAUSE, app.cancel, log)
    app.cancel = gate          # 대본 작성도 일시정지를 따르게
    if not BATCH:
        run_doc(m, app, c, gate)
        app.destroy()
        return
    # ---- 연속 제작: 소재를 돌아가며 AI가 주제를 고르고 한 편씩 끝까지 ----
    n = int(c.get("연속_편수") or 5)
    genres = [g_ for g_ in (c.get("연속_소재") or []) if g_ in m.cat_info(m.DOC_CATEGORY)[1]] or BATCH_GENRES
    out_root = os.path.join(app.get_settings()["out_dir"], "장문")
    os.makedirs(out_root, exist_ok=True)
    state_p = os.path.join(out_root, STATE_NAME)
    st = {}
    try:
        st = json.load(open(state_p, encoding="utf-8"))
    except Exception:
        pass
    done_list = list(st.get("done") or [])
    cur = st.get("current")      # 꺼졌다 켜면 만들던 편부터 이어서
    plan = list(st.get("plan") or [])
    if ONE:          # 한 편 모드: 만들다 멈춘 편이 있으면 그걸 끝내고, 없으면 새로 한 편만
        n = len(done_list) + 1

    def save_state():
        m.atomic_write_text(state_p, json.dumps({"done": done_list, "current": cur, "plan": plan, "offset": st.get("offset", 0)}, ensure_ascii=False, indent=1))
    comp = [str(x) for x in (c.get("연속_구성") or ["지식"]) if str(x) in ("지식", "명상", "재미")] or ["지식"]
    kinds = [comp[i % len(comp)] for i in range(n)]                      # 편마다 종류
    kn_slots = [i for i in range(n) if kinds[i] == "지식"]                # 지식 편만 기획자·검토자 라인업
    if TRUE_STORY and not plan and not (cur and cur.get("주제")):         # 정해둔 주제 목록이 있으면 AI 기획 대신 그걸 순서대로
        seed = load_seed_lineup(m)
        if seed:
            plan = seed[:len(kn_slots)]
            save_state()
            log(f"📑 정해둔 주제 {len(plan)}개를 순서대로 만듭니다 ({'역사' if HISTORY else '실화'}\\주제목록.txt). 편수가 더 많으면 나머지는 AI가 채웁니다.")
    med_presets = [p_ for p_ in (c.get("명상_프리셋") or []) if p_ in m.MUSIC_PRESETS] or MEDITATION_PRESETS
    fun_genres = [g_ for g_ in (c.get("재미_소재") or []) if g_ in m.cat_info(m.DOC_CATEGORY)[1]] or FUN_GENRES
    log(f"🔁 연속 제작 시작: {n}편 · 구성 {'/'.join(comp)} · 지식 {kinds.count('지식')}편(10분 다큐) · 명상 {kinds.count('명상')}편({c.get('명상_분', 20)}분 음악) · 재미 {kinds.count('재미')}편  (끝난 편 {len(done_list)}개)")
    k = len(done_list)
    if len(plan) < len(kn_slots) and not (cur and cur.get("주제")):   # 라인업이 없거나 편수를 늘렸으면: 기획자 → 검토자
        seen = made_topics(m, out_root) + [d_.get("주제", "") for d_ in done_list] + [p_.get("topic", "") for p_ in plan]
        try:
            plan += plan_lineup(m, app, genres, len(kn_slots) - len(plan), c["길이_분"], seen, log, out_root)
        except Exception as e:
            log("기획 단계 실패(편마다 주제를 따로 고릅니다): " + str(e)[:150])
        save_state()
    while k < n:
        kind = kinds[k]
        if kind == "명상":
            mi = sum(1 for i in range(k) if kinds[i] == "명상")
            preset = med_presets[mi % len(med_presets)]
            cur = {"주제": "", "종류": "명상", "프리셋": preset, "시작": time.strftime("%Y-%m-%d %H:%M")}
            save_state()
            log(f"🧘 {k + 1}/{n}편 (명상 음악): {preset}")
            res = run_music(m, app, c, gate, preset, float(c.get("명상_분", 20)))
            done_list.append({"종류": "명상", "주제": res.get("title", preset), "소재": preset, "제목": res.get("title", ""), "완료": time.strftime("%Y-%m-%d %H:%M")})
            cur = None
            k += 1
            save_state()
            log(f"✅ {k}/{n}편 완료")
            continue
        if cur and cur.get("주제"):
            ci = dict(c, 주제=cur["주제"], 소재=cur.get("소재") or c["소재"], 기획메모=cur.get("메모", ""), 소재탐색_폴더=cur.get("소재탐색_폴더", ""))
            log(f"▶ {k + 1}/{n}편 이어서: {ci['주제']} ({ci['소재']})")
        elif kind == "재미":
            fi = sum(1 for i in range(k) if kinds[i] == "재미")
            genre = fun_genres[fi % len(fun_genres)]
            log(f"😄 {k + 1}/{n}편 (재미 · 이야기 낭독) 주제 고르는 중... 소재: {genre}")
            seen = made_topics(m, out_root) + [d_.get("주제", "") for d_ in done_list]
            topic = pick_topic(m, app, genre, seen, log)
            cur = {"주제": topic, "소재": genre, "종류": "재미", "시작": time.strftime("%Y-%m-%d %H:%M"), "메모": ""}
            save_state()
            ci = dict(c, 주제=topic, 소재=genre, 기획메모="")
        else:
            pi = kn_slots.index(k) if k in kn_slots else len(plan)
            if pi < len(plan) and str(plan[pi].get("topic", "")).strip():
                genre, topic = (plan[pi].get("genre") if plan[pi].get("genre") in m.cat_info(m.DOC_CATEGORY)[1] else genres[0]), str(plan[pi]["topic"]).strip()
                log(f"🎯 {k + 1}/{n}편 (기획 라인업): {topic} ({genre})")
                memo = "\n".join(f"- {lab}: {plan[pi][key_]}" for lab, key_ in (("왜 지금 반응이 좋을지", "why"), ("첫 문장 훅(참고)", "hook"), ("검토자 주의사항(반드시 반영)", "review")) if plan[pi].get(key_))
                cur_memo = "[기획자·검토자 메모]\n" + memo if memo else ""
                if plan[pi].get("memo"):      # 실화\\주제목록.txt 3번째 칸(소재탐색 기획메모) → 대본 AI 최우선 참고자료
                    cur_memo = (str(plan[pi]["memo"]) + ("\n\n" + cur_memo if cur_memo else "")).strip()
                    log("   📎 소재탐색 기획메모를 대본 참고자료로 넘김" + (f" ({plan[pi].get('folder', '')})" if plan[pi].get("folder") else ""))
                cur_folder = str(plan[pi].get("folder") or "")
            else:
                cur_memo, cur_folder = "", ""
                genre = genres[(k + int(st.get("offset") or 0)) % len(genres)]
                log(f"🔎 {k + 1}/{n}편 주제 고르는 중... 소재: {genre}")
                seen = made_topics(m, out_root) + [d_.get("주제", "") for d_ in done_list]
                topic = pick_topic(m, app, genre, seen, log)
            cur = {"주제": topic, "소재": genre, "시작": time.strftime("%Y-%m-%d %H:%M"), "메모": cur_memo, "소재탐색_폴더": cur_folder}
            save_state()
            ci = dict(c, 주제=topic, 소재=genre, 기획메모=cur.get("메모", ""), 소재탐색_폴더=cur_folder)
        ci["배경음"] = m.SOUND_BY_TOPIC.get(ci["소재"], c.get("배경음") or "잔잔한 패드")
        res = run_doc(m, app, ci, gate)
        done_list.append({"종류": kind, "주제": ci["주제"], "소재": ci["소재"], "제목": res.get("title", ""), "완료": time.strftime("%Y-%m-%d %H:%M")})
        cur = None
        k += 1
        save_state()
        log(f"✅ {k}/{n}편 완료")
    log(f"🏁 연속 제작 {n}편 모두 완료 → {out_root}  (더 만들려면 '연속_편수'를 늘리거나 {os.path.basename(state_p)} 을 지우세요)")
    app.destroy()
    after_batch(c.get("끝나면", "그대로"))


def after_batch(mode):
    """연속 제작이 끝난 뒤 PC 절전/끄기 (1분 유예, 아무 키나 누르면 취소)"""
    import subprocess
    if mode not in ("절전", "끄기"):
        return
    print(f"⏻ 1분 뒤 PC를 {mode}합니다. 취소하려면 아무 키나 누르세요...", flush=True)
    try:
        import msvcrt
        for _ in range(600):
            if msvcrt.kbhit():
                msvcrt.getch()
                print("취소했습니다.")
                return
            time.sleep(0.1)
    except ImportError:
        time.sleep(60)
    if mode == "끄기":
        subprocess.run(["shutdown", "/s", "/t", "5"])
    else:
        subprocess.run(["shutdown", "/h"])


def split_long_paras(m, story, max_chars):
    """긴 나레이션 문단을 문장 끝에서 비슷한 길이로 나눔 (그림은 문단이 바뀔 때 바뀌므로 한 문단 = 한 박자, 그림 한 장 5~15초)"""
    out = []
    for p in story.split("\n"):
        s_ = p.strip()
        if len(s_) <= max_chars or s_.startswith(("[", "#", "♪")) or m.parse_media(s_):
            out.append(p)
            continue
        sents, cur, i = [], "", 0
        while i < len(s_):
            cur += s_[i]
            if s_[i] in ".?!…":
                while i + 1 < len(s_) and s_[i + 1] in "\"'”’」』)":
                    i += 1
                    cur += s_[i]
                if i + 1 >= len(s_) or s_[i + 1] == " ":
                    sents.append(cur.strip())
                    cur = ""
            i += 1
        if cur.strip():
            sents.append(cur.strip())
        if len(sents) < 2:
            out.append(p)
            continue
        n = -(-len(s_) // max_chars)
        goal = len(s_) / n
        grp = [""]
        for se in sents:
            if grp[-1] and len(grp[-1]) + len(se) / 2 > goal * len(grp) - sum(len(g_) for g_ in grp[:-1]) and len(grp) < n:
                grp.append("")
            grp[-1] = (grp[-1] + " " + se).strip()
        out += [g_ for g_ in grp if g_]
    return "\n\n".join(x for x in out if x.strip()) if any(len(x) > max_chars for x in story.split("\n")) else story


def run_music(m, app, c, gate, preset, minutes):
    """명상·수면 음악 영상 한 편: 프로그램이 음악을 작곡 → 분위기에 맞는 무료 사진(없으면 색 배경) 위에 2.5D 움직임·입자 효과·제목 → MP4·썸네일·업로드 문구"""
    if preset not in m.MUSIC_PRESETS:
        preset = MEDITATION_PRESETS[0]
    P = m.MUSIC_PRESETS[preset]
    title = P["title"]
    s = app.get_settings()
    out_dir = os.path.join(s["out_dir"], "music")
    os.makedirs(out_dir, exist_ok=True)
    base = os.path.join(out_dir, m.safe_name(title) + f"_{int(minutes)}분")
    if os.path.exists(base + ".mp4") and os.path.exists(base + ".json"):
        log(f"🎵 이미 만든 음악 영상 → 건너뜀: {os.path.basename(base)}.mp4")
        return {"title": title}
    log(f"🎵 명상 음악 영상 시작: {title} ({minutes}분 · {preset})")
    seed = int(time.time()) % 9000 + 1
    wav = base + "_tmp.wav"
    last = [0]

    def prog(i, n, lab="음악"):
        p_ = int(i * 100 / max(1, n))
        if p_ >= last[0] + 25:
            last[0] = p_
            log(f"  {lab} {p_}%")
    sec = m.render_music_track(preset, minutes, seed, wav, progress=prog, cancel=gate)
    # 배경 사진: AI가 분위기에 맞는 무료 사진을 찾음 (못 찾으면 프리셋 색 배경)
    bg_im, depth = None, None
    try:
        model = app.model_var.get().strip()
        pd_ = m.ask_json_alive(model, m.PHOTO_SYSTEM, f"콘텐츠 종류: 허구 단편소설 (분위기 사진)\n[제목] {title}\n\n[본문]\n{P.get('desc', '')}. "
                               f"장면: {P.get('prompt', '')}" + m.photo_note(3, "허구 단편소설")
                               + "\n(사람 얼굴·글자·워터마크 없는, 고요하고 넓은 풍경·공간 사진. 아래 3분의 1에 글자가 올라가도 되는 단순한 구도)",
                               tools=m.WEB_TOOLS, log=log, label="배경 사진 찾기")
        ph = m.fetch_photos(pd_.get("photos"), os.path.join(s["out_dir"], "media"), log, limit=3)
        for p_ in ph:
            try:
                im_ = m.Image.open(p_["path"]).convert("RGB")
                if im_.width >= 1200:
                    bg_im = im_
                    log(f"  🖼 배경 사진: {p_.get('caption', '')} ({p_.get('credit', '')})")
                    break
            except Exception:
                continue
        if bg_im is not None:
            depth = m.image_depth_map(m.trim_borders(bg_im), log)
    except Exception as e:
        log("  배경 사진 찾기 실패(색 배경 사용): " + str(e).splitlines()[0][:100])
    sk = dict(s, fps=min(30, int(s["fps"])))
    loop = m.MusicLoop(sk, bg_im, P.get("overlay", "먼지 빛"), title, "", P["colors"], True,
                       motion=m.MUSIC_MOTIONS[0] if depth is not None else "천천히 줌(기본)", depth=depth)
    loop.s = sk
    loop_mp4 = base + "_loop.mp4"
    last[0] = 0
    log("  🎬 화면 그리는 중 (32초 반복 조각)...")
    m.export_mp4(loop, loop_mp4, lambda i, n: prog(i, n, "화면"), gate, None)
    log("  🎞 음악과 화면 합치는 중...")
    m.mux_music_video(loop_mp4, wav, base + ".mp4", sec)
    for tmp_ in (loop_mp4, wav):
        try:
            os.remove(tmp_)
        except OSError:
            pass
    m.Image.fromarray(loop.frame(3.0)).save(base + "_썸네일.png")
    with open(base + ".json", "w", encoding="utf-8") as jf:
        json.dump({"title": title, "sec": sec, "preset": preset, "seed": seed, "audio_file": "", "nature": None}, jf, ensure_ascii=False)
    pkg = m.music_upload_text(title, [preset], minutes=minutes)
    m.write_package(base, title, "", pkg)
    log(f"🎵 음악 영상 완성: {os.path.basename(base)}.mp4 ({m.hms(sec)}) · 썸네일 · 업로드 문구")
    return {"title": title}


def run_doc(m, app, c, gate):
    """한 편 끝까지: 대본 → 사진 → 나레이션 → MP4 → 업로드 문구. 결과 res(dict) 돌려줌"""
    app.cat_var.set(m.DOC_CATEGORY)
    app.on_category()
    if c["소재"] in m.cat_info(m.DOC_CATEGORY)[1]:
        app.genre_var.set(c["소재"])
        app.on_genre()
    app.topic_var.set(c["주제"])
    prof = app.apply_genre_profile(c["소재"], quiet=True, sync=True)     # 소재별 기본 설정 (메인 프로그램의 표, 글꼴은 바로 받음)
    want_sub = str(c.get("자막_스타일", "자동")).strip()
    if want_sub != "자동" and want_sub in m.LONG_STYLES:     # 설정 파일에서 직접 고른 자막 스타일
        app.vars["style_preset"].set(want_sub)
        app.apply_style_preset()
        app.update()
        app.vars["head_pos"].set(prof["head_pos"])
        app.vars["sub_dialog"].set(prof["sub_dialog"])
    app.update()
    log(f"🎨 자막 스타일: {app.vars['style_preset'].get()}" + (" (소재에 맞춰 자동)" if want_sub == "자동" else ""))
    src_ = str(c.get("이미지") or m.IMG_SOURCE_WEB)
    if src_ == m.IMG_SOURCE_WEB and str(c["소재"]).startswith("[교육]"):     # 교육 소재는 기본이 그림 (실제 사람 사진 대신)
        src_ = m.genre_profile(c["소재"]).get("img_source", src_)
    m.IMG_SOURCE["mode"] = src_ if src_ in m.IMG_SOURCE_PRESET else m.IMG_SOURCE_WEB
    app.img_src_var.set(m.IMG_SOURCE["mode"])       # 프로젝트 파일에도 저장 (다시 만들기·그림 보강 때 같은 스타일로)
    if m.IMG_SOURCE["mode"] != m.IMG_SOURCE_WEB:
        log(f"🖌 이미지: {m.IMG_SOURCE['mode']} (사실 주제도 웹 사진 대신 이 PC에서 그림)")
    if m.doc_is_fiction(c["소재"]):
        want = str(c.get("그림_스타일") or "자동(돌아가며)")
        if want in m.IMAGE_STYLES:
            app.vars["image_style_preset"].set(want)
        elif not want.startswith("자동"):
            app.vars["image_style_preset"].set("직접 입력(아래 칸)")
            app.vars["image_style"].set(want)
        log(f"🎨 그림 스타일: {app.vars['image_style_preset'].get()} · "
            + ("이 PC에서 직접 그림" if str(app.vars['fiction_image'].get()).startswith("로컬") else "분위기 웹 사진"))
    if str(c.get("제목_표시", "")).strip() in ("위 가운데", "왼쪽 위 작게", "숨김"):
        app.vars["head_pos"].set(str(c["제목_표시"]).strip())
    app.vars["bgm_mode"].set("자동생성")
    app.vars["bgm_volume"].set(str(c["배경음_크기"]))
    if str(c.get("성우_프리셋") or "").strip():      # 저장한 성우(🎤 성우 선택 창의 ⭐ 새 성우로 저장). 비우면 기본 성우
        tmp = {}
        if m.apply_voice_preset(tmp, c["성우_프리셋"], log):
            for k_, v_ in tmp.items():
                if k_ in app.vars:
                    app.vars[k_].set(str(v_))
    LONG_FIX = {"narration": "on", "layout": "자막형(큰 제목+사진+자막)", "img_fill": "전체 화면(글자가 사진 위에)",   # 장문 화면 규칙 (CLAUDE.md):
                "img_motion": "영상처럼(확대·이동·전환)", "head_show": "안 보임(제목 카드만)", "head_pos": "숨김",   # 새 서버의 프로그램 기본값(쇼츠 세로 등)을 쓰지 않게
                "sub_split": "한 줄씩(문장·쉼표로 나눠 차례로)", "img_label": "off"}
    for k_, v_ in LONG_FIX.items():
        if k_ in app.vars:
            app.vars[k_].set(v_)
    app.vars["format"].set("롱폼 가로(1920×1080)")
    app.apply_format("롱폼 가로(1920×1080)")                # 장문은 항상 가로 16:9 (그림도 가로로 그려짐)
    s = app.get_settings()
    out_root = os.path.join(s["out_dir"], "장문")
    work = m._load_korean_reading("콘텐츠_정리").find_work(out_root, m.safe_name(c["주제"])[:40])   # 정리된 콘텐츠면 그 폴더 안의 작업 폴더
    os.makedirs(work, exist_ok=True)
    m.SCRIPT_ENGINE["s"] = s
    m.PHOTO_PLAN.update(sub=True, n=0)
    m.HIT_CTX["category"] = m.DOC_CATEGORY
    m.set_tts_cfg(s)
    model = app.model_var.get().strip()
    log(f"▶ 시작: {c['주제']} ({c['소재']}, {c['길이_분']}분) · 배경음 {c['배경음']} 크기 {c['배경음_크기']} · {s['fps']}fps")

    # 1) 대본 (조사·구성안·챕터마다 저장)
    script_json = os.path.join(work, "대본.json")
    res = None
    if os.path.exists(script_json):
        try:
            res = json.load(open(script_json, encoding="utf-8"))
            log("대본: 이미 완성됨 → " + res["title"])
        except Exception:
            log("대본 파일이 깨져 있어 진행 기록에서 다시 합칩니다")
    m.DEFER_DRAW["on"] = bool(c.get("나레이션_먼저", True)) and bool(m.draw_settings())   # 그림은 나레이션 시간에 맞춰 나중에
    if res is None:
        if m.DEFER_DRAW["on"]:
            log("🎙 나레이션 먼저: 대본 → 나레이션(문단 시간 기록) → 그 시간에 맞춰 그림 → 배경음·자막과 합치기")
        res = app.generate_longdoc(model, c["주제"], c["소재"], c["길이_분"], log, research=c["웹조사"], autophoto=c["챕터별_사진"],
                                   reference=str(c.get("기획메모") or ""), media_dir=os.path.join(out_root, "media"),
                                   state_path=os.path.join(work, "대본_진행.json"), gate=gate)
        m.atomic_write_text(script_json, json.dumps(res, ensure_ascii=False, indent=1))
        log(f"대본 완성: {res['title']} | {res['note']}")
    title, story = res["title"], res["story"]
    m.IMAGE_CAST["chars"] = list(res.get("cast") or [])     # 등장인물 외모 (다시 그릴 때도 같은 얼굴)
    # 사진 보강 (장문_사진보강.bat): 이미 만든 대본에 사진을 더 넣고 영상만 다시 만듦
    done_flag = os.path.join(work, "사진보강_완료.txt")
    req_flag = os.path.join(work, "사진보강_요청.txt")      # 보강 중에 꺼져도 장문_만들기.bat 으로 이어지게
    if MORE_PHOTOS and not BATCH and not os.path.exists(done_flag):
        m.atomic_write_text(req_flag, time.strftime("%Y-%m-%d %H:%M"))
    if os.path.exists(req_flag) and not os.path.exists(done_flag):
        bak = os.path.join(work, "대본_사진보강전.json")
        if not os.path.exists(bak):
            m.atomic_write_text(bak, json.dumps(res, ensure_ascii=False, indent=1))
        before = len(m.photo_credits(story))
        log(f"📷 사진 보강 시작: 지금 {before}장 → 나레이션 {m.DOC_PHOTO_SEC}초에 한 장 목표")
        story, n_add = m.doc_add_photos(model, title, story, os.path.join(out_root, "media"), log, gate,
                                        fiction=m.doc_is_fiction(c["소재"]), sources=res.get("sources") or [])
        res["story"] = story
        m.atomic_write_text(script_json, json.dumps(res, ensure_ascii=False, indent=1))
        m.atomic_write_text(done_flag, f"{before} -> {before + n_add}")
        log(f"📷 사진 보강 완료: {n_add}장 추가 (총 {len(m.photo_credits(story))}장)")
    # 전원이 꺼지며 깨진 사진이 있으면 그 사진 줄만 뺌
    from PIL import Image
    keep, dropped = [], 0
    for line in story.split("\n"):
        md = m.parse_media(line)
        if md:
            p_ = md[0] if os.path.isabs(md[0]) else os.path.join(m.BASE, md[0])
            try:
                with Image.open(p_) as im:
                    im.load()
            except Exception:
                dropped += 1
                continue
        keep.append(line)
    if dropped:
        story = "\n".join(keep)
        log(f"깨진 사진 {dropped}장을 빼고 진행합니다")
    if res.get("story_drawn"):              # 나레이션 먼저 흐름에서 이미 다듬고 그림까지 넣은 대본 → 그대로 (다듬기를 두 번 하지 않게)
        story = res["story_drawn"]
    else:
        story, _ = m.hook_fix(app.model_var.get().strip(), story, log, gate, title=title)   # 규칙: 30초 후크 + 첫 5초 = 제목·썸네일 약속
        story, _ = m.retention_fix(app.model_var.get().strip(), story, title, log, gate)    # 규칙: 챕터 끝 예고 + 시리즈 한 줄 (1위 영상 분석)
        story, _ = m.polite_fix(app.model_var.get().strip(), story, log, gate)   # 규칙: 모든 나레이션은 존댓말 (자막·성우 함께)
    defer = m.DEFER_DRAW["on"] and not any(m.parse_media(x) for x in story.split("\n"))   # 아직 그림 없는 대본 → 나레이션 뒤에 그림
    if defer:
        n0 = len([x for x in story.split("\n") if x.strip()])
        story = split_long_paras(m, story, int(c.get("문단_최대_글자") or 120))
        n1 = len([x for x in story.split("\n") if x.strip()])
        if n1 != n0:
            log(f"✂ 긴 문단을 문장 끝에서 나눔: {n0} → {n1}줄 (그림이 문단마다 바뀌어 박자가 맞게)")
    base = os.path.join(out_root, m.safe_name(title))
    app.title_var.set(title)
    app.set_story(story)
    app.set_sources(res.get("sources"), res.get("notes"))
    app.vars["target_sec"].set("0")
    m.atomic_write_text(base + "_프로젝트.json", json.dumps(app.project_dict(), ensure_ascii=False, indent=1))
    s = app.get_settings()
    ch_ = m._YP.vary_settings(s, title, log)     # 규칙: 영상마다 강조색·자막 효과·배경음을 다르게 (유튜브 '대량 생산 콘텐츠' 정책)
    if not str(c.get("배경음") or "").strip() or str(c.get("배경음")).startswith("자동"):
        c["배경음"] = ch_["bgm_style"]
    trad_ = m.trad_from_memo(c.get("기획메모", "")) if HISTORY else ""   # 주제목록 메모의 '배경음: 중동 히자즈' / '음계: 우조'
    samguk_ = HISTORY and any(w_ in (str(c.get("주제", "")) + str(c.get("기획메모", "")) + title) for w_ in SAMGUK_WORDS)
    if trad_ or samguk_:
        c["배경음"] = trad_ or m.CHINA_STRINGS   # 삼국지 편은 메모가 없으면 고쟁·얼후 궁조 (사용자 결정 2026-10-30, 실록 편은 메모가 있을 때만)
        log(f"🎵 배경음: {c['배경음']} · 챕터마다 전통악기 한 소절")
        try:                                   # 프로젝트에도 저장 (다시 만들 때 같은 배경음)
            pj_ = json.load(open(base + "_프로젝트.json", encoding="utf-8"))
            pj_.setdefault("settings", {})["bgm_style"] = c["배경음"]
            m.atomic_write_text(base + "_프로젝트.json", json.dumps(pj_, ensure_ascii=False, indent=1))
        except Exception:
            pass
    if m.is_trad(c["배경음"]):
        s["chapter_hold"] = 4.2               # 챕터 제목 동안 나레이션을 쉬고 고쟁 연주
        pc_ = re.search(r"타악\s*[:：]\s*(진군북|난타|연속북|징|북|없음)", str(c.get("기획메모", "")))   # 주제목록 메모의 '타악: 연속북' (없으면 권역 기본)
        if pc_:
            s["chapter_perc"] = "off" if pc_.group(1) == "없음" else pc_.group(1)
            log(f"🥁 챕터 시작 타악: {pc_.group(1)}")
            try:
                pj_ = json.load(open(base + "_프로젝트.json", encoding="utf-8"))
                pj_.setdefault("settings", {})["chapter_perc"] = s["chapter_perc"]
                m.atomic_write_text(base + "_프로젝트.json", json.dumps(pj_, ensure_ascii=False, indent=1))
            except Exception:
                pass
    if HISTORY:                                # 역사 편: 입체 움직임(2.5D) 끔 — 그리는 효과와 겹치고 없는 게 나음 (사용자 결정 2026-10-30)
        s["img_depth"] = "off"
        try:
            pj_ = json.load(open(base + "_프로젝트.json", encoding="utf-8"))
            pj_.setdefault("settings", {})["img_depth"] = "off"
            m.atomic_write_text(base + "_프로젝트.json", json.dumps(pj_, ensure_ascii=False, indent=1))
        except Exception:
            pass

    s["sub_hide"] = "on" if str(c.get("자막", "보임")).strip() == "숨김" else "off"   # 장문 자막: 기본 보임 (장문_설정.json 의 자막=숨김 이면 나레이션만)
    try:
        pj_ = json.load(open(base + "_프로젝트.json", encoding="utf-8"))
        pj_.setdefault("settings", {})["sub_hide"] = s["sub_hide"]
        m.atomic_write_text(base + "_프로젝트.json", json.dumps(pj_, ensure_ascii=False, indent=1))
    except Exception:
        pass

    # 2) 나레이션 (문단마다 저장 → 이어서)
    log("🎙 나레이션 만드는 중... (이미 만든 문단은 건너뜀)")
    if hasattr(m, "ensure_depth_maps") and str(s.get("img_depth", "off")) == "on":
        m.ensure_depth_maps(m.story_photo_paths(story), log)
    narr = app.narration_for(story, s, lambda x: None, gate)
    log(f"나레이션 완성: {len(narr)}문단 · {sum(d for _, _, d in narr) / 60:.1f}분")
    if defer and "--그림제외" in sys.argv:   # 대본·나레이션만 이 서버에서 (그림이 느린 서버) → 그림·영상은 다른 서버에서 같은 명령으로 이어서
        log("⏸ --그림제외: 대본·나레이션까지 끝. output/장문 을 그림이 빠른 서버로 옮겨 --그림제외 없이 같은 명령으로 이어서 하세요")
        raise SystemExit(0)
    if defer:   # 3) 그림: 나레이션 문단 시간에 맞춰 (한 장 5~15초, 문단이 바뀔 때 바뀜) → 인물 영역(그리는 효과)
        import subprocess
        pj_ = json.load(open(base + "_프로젝트.json", encoding="utf-8"))
        pj_["story"] = story
        pj_["settings"] = {k: v for k, v in dict(pj_.get("settings") or {}, **dict(s, bgm_style=c["배경음"])).items() if k not in m.SECRET_KEYS}   # 이 편 설정 그대로 (fps·제목·배경음 등)
        m.atomic_write_text(base + "_프로젝트.json", json.dumps(pj_, ensure_ascii=False, indent=1))
        for tool in ("그림_간격_보강.py", "인물영역_만들기.py"):
            log(f"🖌 {tool} 실행 중...")
            rc = subprocess.call([sys.executable, "-X", "utf8", "-u", os.path.join(HERE, tool), base + "_프로젝트.json"], cwd=HERE)
            if rc:
                raise SystemExit(f"{tool} 실패 (코드 {rc}) - 같은 명령으로 다시 실행하면 이어서 합니다")
        story = json.load(open(base + "_프로젝트.json", encoding="utf-8"))["story"]
        app.set_story(story)
        res["story_drawn"] = story                                    # 다시 실행하면 다듬기·그림 단계는 건너뜀
        m.atomic_write_text(script_json, json.dumps(res, ensure_ascii=False, indent=1))
        narr = app.narration_for(story, s, lambda x: None, gate)     # 문단은 그대로 → 녹음 캐시 그대로
        log(f"그림 완성: {len(m.photo_credits(story))}장 (나레이션 문단 시간에 맞춤)")
    review_ok = os.path.join(work, "그림점검_완료.txt")
    if "--점검완료" in sys.argv and not os.path.exists(review_ok):
        m.atomic_write_text(review_ok, time.strftime("%Y-%m-%d %H:%M"))
    if c.get("그림_사용자점검", True) and m.photo_credits(story) and not os.path.exists(review_ok):
        import subprocess
        subprocess.call([sys.executable, "-X", "utf8", os.path.join(HERE, "그림_모음.py"), base + "_프로젝트.json"], cwd=HERE)
        log("⏸ 그림 점검: 프로젝트 폴더의 _그림점검_N.jpg (40장씩) 를 사용자에게 보내 점검받은 뒤, 고칠 그림을 고치고 같은 명령에 --점검완료 를 붙여 이어서 (영상 합치기)")
        raise SystemExit(0)
    if "--영상제외" in sys.argv:            # 대본·나레이션·그림까지 이 서버에서 → 영상(합치기)은 다른 서버 (같은 명령을 --영상제외 없이 다시 실행하면 이어서)
        log("⏸ --영상제외: 대본·나레이션·그림까지 끝. output/장문 을 다른 서버로 옮겨 --영상제외 없이 같은 명령으로 이어서 하세요")
        raise SystemExit(0)

    # 3) 영상 (5분 구간마다 저장 → 이어서)
    r = m.make_renderer(title, story, s, narr)
    log(f"영상 길이 {m.hms(r.duration)} · 챕터 {len(r.chapter_times())}개 · 사진 {len(m.photo_credits(story))}장")
    audio = m.build_audio(r, s, c["배경음"])
    last = [0]

    def prog(i, n):
        p = int(i * 100 / max(1, n))
        if p >= last[0] + 5:
            last[0] = p
            log(f"  MP4 {p}%")
    import hashlib
    key = hashlib.md5((story + "|" + getattr(m, "RENDER_VER", "") + "|" + json.dumps({k: s.get(k) for k in ("fps", "format", "layout", "img_fill", "img_motion", "img_depth", "img_depth_amt", "head_style", "head_pos", "head_size", "head_show", "sub_style", "sub_size", "sub_layout", "sub_dialog", "sub_anim", "sub_split", "sub_hide", "style_preset", "text_color", "sub_box_alpha",
                                                                         "font_path", "title_font_path", "bgm_volume", "intro_sec", "outro_sec", "outro_text", "img_filter", "motion_count", "motion_chart", "motion_icon", "motion_lower", "motion_popup")}, ensure_ascii=False)
                       + "|" + title + "|" + ",".join(f"{d_:.3f}" for _, _, d_ in narr) + "|" + ",".join(f"{sg_['t0']:.2f}" for sg_ in getattr(r, "segs", [])) + f"|{r.duration:.2f}" + getattr(r, "fx_sig", "")).encode("utf-8")).hexdigest()   # 나레이션이 바뀌면(발음 수정 등) 영상 구간도 새로
    m.export_mp4_resumable(r, base + ".mp4", prog, gate, audio, work_dir=os.path.join(work, "영상구간"), seg_sec=SEG_SEC, log=log, key=key)
    del audio
    r.thumbnail().save(base + "_썸네일.png")
    ch = r.chapter_times()
    with open(base + "_타임스탬프.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(f"{m.hms(t)} {n}" for t, n in [(0, "오프닝")] + ch))
    log("MP4 완성: " + base + ".mp4")

    # 4) 업로드 문구 + 설명란 완성본 + 유튜브 썸네일
    log("📝 업로드 문구·설명란·유튜브 썸네일 만드는 중...")
    m.publish_kit(model, base, title, story, m.DOC_CATEGORY, c["소재"], s, ch, res.get("sources") or [], res.get("notes", ""), log)
    add_external_thumbs(c.get("소재탐색_폴더", ""), base, log, str(c.get("썸네일_선택") or "프로그램"))
    log("✅ 전부 완료 → " + out_root)
    make_sh = ("--쇼츠" in sys.argv or bool(c.get("쇼츠_만들기"))) and "--쇼츠없음" not in sys.argv
    if make_sh:     # 규칙: 쇼츠는 기본적으로 안 만듦. --쇼츠 옵션(또는 장문_설정.json 쇼츠_만들기=true)일 때만 (쇼츠_자동.py)
        try:
            m._load_korean_reading("쇼츠_자동").make_shorts(m, model, base + "_프로젝트.json", log)
        except Exception as e:
            log("⚠ 쇼츠 자동 만들기 실패(롱폼은 완성됨): " + (str(e).splitlines() or [type(e).__name__])[0][:120])
    try:                                    # 규칙: 다 만들면 롱폼 + 쇼츠를 output\장문\<제목>\ 폴더 하나로 정리 (콘텐츠_정리.py)
        m._load_korean_reading("콘텐츠_정리").organize(base + "_프로젝트.json", log, os.path.abspath(out_root))
    except Exception as e:
        log("⚠ 콘텐츠 폴더 정리 실패(파일은 그대로): " + (str(e).splitlines() or [type(e).__name__])[0][:120])
    return res


def add_external_thumbs(folder, base, log, choice="프로그램"):
    """소재탐색(실화_소재탐색.py)이 미리 만든 썸네일 3안을 _썸네일_후보 폴더에 '외부_' 이름으로 추가.
    출처·라이선스 메모(source.txt)도 함께 복사해 공용 사진 표기를 잊지 않게.
    choice='외부 자동' 이면 외부 후보 중 점수가 높은 것을 <제목>_썸네일_유튜브.jpg 로 (프로그램 것은 _썸네일_유튜브_프로그램.jpg 로 보관)."""
    if not folder or not os.path.isdir(folder):
        return
    import glob
    import shutil
    thumbs = sorted(glob.glob(os.path.join(folder, "thumb_*.jpg")))
    if not thumbs:
        return
    cdir = base + "_썸네일_후보"
    os.makedirs(cdir, exist_ok=True)
    for p in thumbs:
        shutil.copy(p, os.path.join(cdir, "외부_" + os.path.basename(p)))
    for name in ("source.txt", "meta.json", "hashtags.txt", "선택_기록.json"):
        src = os.path.join(folder, name)
        if os.path.exists(src):
            shutil.copy(src, os.path.join(cdir, "외부_" + name))
    log(f"  🖼 소재탐색 썸네일 {len(thumbs)}장을 후보 폴더에 추가: {os.path.basename(cdir)}\\외부_thumb_*.jpg (출처: 외부_source.txt)")
    if choice.startswith("수동"):
        if BATCH:   # 무인 연속 제작 중에는 창을 띄우지 않음 → 외부 자동처럼 처리하고 안내
            log("  🖼 '수동(창)'은 연속 제작 중엔 창을 띄우지 않습니다 → 자동으로 고르고, 나중에 썸네일_고르기.bat 로 바꾸세요")
            choice = "외부 자동"
        else:
            pick_thumb_window(cdir, base, log)
            return
    if choice.startswith("외부"):
        final = os.path.join(folder, "썸네일_최종.jpg")
        why = "소재탐색 단계에서 자동 선택된 것"
        if not os.path.exists(final):
            try:
                sys.path.insert(0, os.path.join(HERE, "소재탐색"))
                import thumb_pick
                final, why = thumb_pick.pick(folder, "자동")
            except Exception as e:
                log(f"  🖼 외부 썸네일 자동 선택 실패(프로그램 썸네일 유지): {str(e)[:80]}")
                return
        if final and os.path.exists(final):
            dest = base + "_썸네일_유튜브.jpg"
            if os.path.exists(dest):
                shutil.copy(dest, base + "_썸네일_유튜브_프로그램.jpg")
            shutil.copy(final, dest)
            log(f"  🖼 유튜브 썸네일을 소재탐색 후보로 교체: {os.path.basename(dest)} ({why}) · 프로그램 것은 _썸네일_유튜브_프로그램.jpg")
    else:
        log("     최종 썸네일은 프로그램이 고른 것 그대로 (바꾸려면 장문_설정.json '썸네일_선택': '외부 자동'/'수동(창)' 또는 썸네일_고르기.bat)")


def pick_thumb_window(cdir, base, log):
    """프로그램 후보(01.jpg …) + 외부 후보(외부_thumb_*.jpg)를 한 화면에 띄워 클릭으로 고름 → <제목>_썸네일_유튜브.jpg
    (프로그램이 고른 것은 _썸네일_유튜브_프로그램.jpg 로 보관). 창을 닫으면 그대로 둠."""
    try:
        sys.path.insert(0, os.path.join(HERE, "소재탐색"))
        import thumb_pick
        import shutil
        log("  🖼 썸네일 고르기 창을 띄웁니다 (클릭 한 번, 창을 닫으면 프로그램이 고른 것 유지)")
        final, msg = thumb_pick.pick(cdir, "수동", title=os.path.basename(base))
        if final:
            dest = base + "_썸네일_유튜브.jpg"
            if os.path.exists(dest):
                shutil.copy(dest, base + "_썸네일_유튜브_프로그램.jpg")
            shutil.copy(final, dest)
            log(f"  🖼 유튜브 썸네일 = {msg} → {os.path.basename(dest)}")
        else:
            log("  🖼 " + msg)
    except Exception as e:
        log(f"  🖼 썸네일 고르기 창 실패(프로그램 썸네일 유지): {str(e)[:80]}")


def _job_procs():
    """지금 돌고 있는 장문 만들기 작업(파이썬·그 창)의 프로세스 번호들"""
    import subprocess
    ps = ("Get-CimInstance Win32_Process | Where-Object { ($_.CommandLine -like '*make_longdoc.py*' -and $_.CommandLine -notlike '*--safe-stop*' "
          "-and $_.CommandLine -notlike '*--pause*' -and $_.CommandLine -notlike '*--resume*') } "
          "| ForEach-Object { $_.ProcessId }")
    out = subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, text=True).stdout
    return [int(x) for x in out.split() if x.strip().isdigit() and int(x) != os.getpid()]


def _paused_in_log(since=0):
    """진행 기록에서 since 바이트 이후(또는 마지막 시작 이후)에 '일시정지 중'이 찍히고 그 뒤 '재개'가 없으면 True"""
    try:
        with open(LOG_FILE, "rb") as f:
            f.seek(since)
            lines = f.read().decode("utf-8", "ignore").splitlines()
    except OSError:
        return False
    st = -1
    for i, ln in enumerate(lines):
        if "⏸ 일시정지 중" in ln:
            st = i
        elif "▶ 재개" in ln or "▶ 시작" in ln:
            st = -1
    return st >= 0


def safe_stop():
    """장문_끄기전_정리.bat: 일시정지 → 실제로 멈출 때까지 기다림 → 작업 종료 → (선택) PC 끄기"""
    import subprocess
    procs = _job_procs()
    if not procs:
        print("지금 돌고 있는 장문 작업이 없어요. 그냥 전원을 꺼도 됩니다.")
    else:
        size = os.path.getsize(LOG_FILE) if os.path.exists(LOG_FILE) else 0
        already = os.path.exists(PAUSE) and _paused_in_log(0)
        open(PAUSE, "w").close()
        if not already:
            print("⏸ 일시정지를 요청했어요. 지금 하던 작은 단계가 끝날 때까지 기다립니다...")
            print("   (AI가 조사·집필 중이면 그 답이 올 때까지 최대 15분 걸릴 수 있어요. 기다리기 싫으면 이 창을 닫고 그냥 꺼도 되고,")
            print("    그러면 그 단계 하나만 다시 하게 됩니다. 끝난 단계는 모두 저장되어 있습니다)")
            t0 = time.time()
            while not _paused_in_log(size):
                if not _job_procs():
                    break
                if time.time() - t0 > 20 * 60:
                    print("   20분이 지나도 멈추지 않아 지금 상태로 정리합니다 (하던 단계 하나만 다시 하게 돼요).")
                    break
                time.sleep(3)
                print(f"\r   기다리는 중... {int(time.time() - t0)}초", end="", flush=True)
            print()
        for pid in procs:
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)], capture_output=True)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{time.strftime('%H:%M')}] ⏹ 끄기 전 정리로 작업을 멈춤 - 다시 켠 뒤 장문_만들기.bat 을 실행하면 이어서 합니다\n")
        print("✅ 안전하게 멈췄어요. 이제 전원을 꺼도 됩니다.")
        print("   다시 켠 뒤 '장문_만들기.bat' 을 실행하면 멈춘 곳부터 이어서 만듭니다.")
    print()
    print("  1 = 지금 PC 끄기 (시스템 종료)")
    print("  2 = 최대 절전 모드 (열려 있던 창이 그대로 남음)")
    print("  그 외 = 아무것도 안 하고 닫기")
    try:
        ans = input("선택: ").strip()
    except EOFError:
        ans = ""
    if ans == "1":
        subprocess.run(["shutdown", "/s", "/t", "5"])
        print("5초 뒤에 꺼집니다. (취소: 명령 프롬프트에서 shutdown /a)")
    elif ans == "2":
        subprocess.run(["shutdown", "/h"])


if __name__ == "__main__":
    if "--safe-stop" in sys.argv:    # 장문_끄기전_정리.bat
        safe_stop()
        sys.exit(0)
    if "--pause" in sys.argv:        # 장문_일시정지.bat
        open(PAUSE, "w").close()
        print("⏸ 일시정지 요청함. 지금 하던 작은 단계(문단 하나·장면 하나·AI 답변 하나)가 끝나면 멈춥니다.")
        print("   다시 하려면 장문_재개.bat 을 누르세요. (PC를 꺼도 장문_만들기.bat 으로 이어서 할 수 있어요)")
        sys.exit(0)
    if "--resume" in sys.argv:       # 장문_재개.bat
        import subprocess
        was_paused = os.path.exists(PAUSE)
        if was_paused:
            os.remove(PAUSE)
        if _job_procs():
            print("▶ 재개했습니다. 만들기 창에서 이어서 진행됩니다." if was_paused else "이미 만들기가 돌아가고 있어요. (일시정지 상태 아님)")
        else:
            # 만들기 창이 없음(끄기 전 정리로 멈췄거나 PC를 껐다 켠 경우) → 만들기를 새 창으로 띄워 저장된 곳부터 이어서
            print("만들기 창이 꺼져 있어 새로 띄웁니다. 끝난 단계는 건너뛰고 멈춘 곳부터 이어서 합니다.")
            bat = os.path.join(HERE, "장문_만들기.bat")
            if os.path.exists(bat):
                subprocess.Popen(f'start "" "{bat}"', shell=True, cwd=HERE)
            else:
                subprocess.Popen([sys.executable, "-X", "utf8", os.path.abspath(__file__)], cwd=HERE,
                                 creationflags=getattr(subprocess, "CREATE_NEW_CONSOLE", 0))
        sys.exit(0)
    if os.path.exists(PAUSE):        # 일시정지된 채로 PC를 껐다 켠 경우: 다시 만들기를 누르면 바로 진행
        os.remove(PAUSE)
    try:
        main()
    except Exception as e:
        log("❌ 멈춤: " + str(e)[:300])
        log("   장문_만들기.bat 을 다시 실행하면 끝난 단계는 건너뛰고 이어서 합니다.")
        sys.exit(1)
