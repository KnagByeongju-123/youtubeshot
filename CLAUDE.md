# 폰(클라우드 Claude Code)에서 쓸 때

- 세션이 시작되면 `.claude/hooks/session-start.sh` 가 준비를 자동으로 함:
  한글 글꼴(나눔·노토), 파이썬 3.12 화면 부품(tkinter), 가상 모니터(xvfb),
  실행 환경 `.supertonic_venv`, 목소리 모델 `supertonic_assets` (Supertonic 3),
  로컬 그림 모델 `.sd_venv` + `models/` (만화·그림 장면, 한 장 약 30초)
- `python` = `.supertonic_venv/bin/python` (파이썬 3.12. 기본 python3.13 에는 tkinter 가 없음)
- 프로그램은 tkinter 창을 띄우므로 화면 없이 `xvfb-run -a python -X utf8 ...` 로 실행
- 성우는 남자 성우 2 (Supertonic M2) 만 씀
- `.bat` 는 윈도우용 → 같은 일을 하는 `.py` 를 직접 실행
- 만든 영상·소리는 서버가 지워지면 사라지므로 사용자에게 파일로 보내 줌 (깃에 올리지 않음)
- 사용자에게는 쉬운 말로 설명 (일반인이 알아들을 수준)
