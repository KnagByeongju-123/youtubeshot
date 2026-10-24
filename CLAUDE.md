# 폰(클라우드 Claude Code)에서 쓸 때

- 세션이 시작되면 `.claude/hooks/session-start.sh` 가 준비를 자동으로 함:
  한글 글꼴(나눔·노토), 파이썬 3.12 화면 부품(tkinter), 가상 모니터(xvfb),
  실행 환경 `.supertonic_venv`, 목소리 모델 `supertonic_assets` (Supertonic 3),
  그림 모델 FLUX.2 klein 4B `.sd_venv` + `models/FLUX2_klein_4B` (Apache 2.0, 그래픽카드 없이)
- `python` = `.supertonic_venv/bin/python` (파이썬 3.12. 기본 python3.13 에는 tkinter 가 없음)
- 프로그램은 tkinter 창을 띄우므로 화면 없이 `xvfb-run -a python -X utf8 ...` 로 실행
- 성우는 남자 성우 2 (Supertonic M2) 만 씀
- 만화 그림: `klein_worker.py` (사용법은 파일 맨 위)
  - 인물마다 캐릭터 시트(앞·옆·뒤 전신, 흰 배경)를 먼저 그려 사용자 확인 → `등장인물/` 에 저장, `등장인물.json` 의 face 에 경로
  - 장면은 그 장면 인물의 시트를 refs 로 넣어 그림 (기준 그림은 작게: ref_max_area 기본값). 1024×576 기준 인물 장면 약 2분, 풍경 약 40초
  - 그린 뒤 직접 보고 검수 → 손가락·얼굴·옷이 틀리면 fixes 로 그 칸만 다시 그림 (약 1분 20초)
  - 한 장에 인물이 둘이어도 시트를 둘 다 넣으면 섞이지 않음
- `.bat` 는 윈도우용 → 같은 일을 하는 `.py` 를 직접 실행
- 만든 영상·소리는 서버가 지워지면 사라지므로 사용자에게 파일로 보내 줌 (깃에 올리지 않음)
- 사용자에게는 쉬운 말로 설명 (일반인이 알아들을 수준)
