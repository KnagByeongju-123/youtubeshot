[2026-10-12 installation fix - Korean CMD encoding issue]
Previous BAT file was UTF-8 Korean text. Windows CMD could misread it,
printing errors such as a broken Korean command or a lone 'o' command.
The new BAT file is ASCII-only with Windows CRLF line endings.

Fix steps (existing shorts_ directory):
1. Close the previous installer window.
2. Extract this new ZIP directly into C:\Users\user\Downloads\shorts_ .
3. When asked, choose Replace files in the destination.
4. Double-click setup_supertonic_windows.bat .
5. When SUCCESS appears, play voice_samples\M1_neutral.wav .
6. Double-click run_shorts_supertonic.bat .

If Python 3.11 not found:
In CMD run: py -0p
A 64-bit Python 3.11 installation is required for this package.

--- Original Korean instructions follow ---

쇼츠 스크롤 영상 메이커 PRO — Supertonic 3 감정형 무료 성우 통합판
================================================================
지원 환경: Windows 11 / 베이직북 14 N95, RAM 8GB (실제 속도 미측정)
작성 기준: 2026-10-12

[구성 파일]
 shorts_novel_maker_supertonic.py   기존 프로그램 기능 유지 + 로컬 무료 성우 선택 추가
 supertonic_local_worker.py        CPU 음성 합성 별도 프로세스
 supertonic_voice_test.py          남녀/감정 목소리 샘플 생성
 setup_supertonic_windows.bat      설치 및 기본 음성 테스트용
 run_shorts_supertonic.bat         통합 프로그램 실행용
 shorts_novel_maker.py            기존 원본은 백업으로 따로 보관 (제공 시 원본 유지)

[1] 폴더 준비
 위 5개 파일을 같은 폴더에 넣으세요.
 기존 shorts_novel_maker.py 및 shorts_novel_config.json이 있는 폴더에 넣으면 설정을 이어서 사용할 수 있습니다.
 설정이 담긴 원본 폴더를 별도로 복사해두면 더 안전합니다.
 이미지, 캐시 등 기존 리소스를 그대로 사용하되 새 코드가 들어간 파일로 실행합니다.

[2] Python 준비
 Windows Python 3.11 (64비트)을 설치해야 합니다.
 설치 확인: 시작 → cmd → py -3.11 --version
 'Python 3.11.x'가 나오면 다음 단계로 진행합니다.

[3] Supertonic 설치 (최초 1회, 인터넷 필요)
 setup_supertonic_windows.bat 더블클릭 → 자동으로 설치합니다.
 자동 설치 대상: .supertonic_venv / supertonic_assets (원본 프로그램과 분리)
 약 400MB 모델 파일 및 추가 Python 패키지 설치에 별도 디스크 용량이 필요합니다.
 사용 PC에 따라 설치 시간과 합성 시간이 다릅니다.
 완료 시 voice_samples\M1_neutral.wav 파일이 생성됩니다.

[4] 프로그램 실행
 run_shorts_supertonic.bat 더블클릭
 '나레이션' 탭 → 나레이션 on
 '🎤 성우 선택' → 한국어 → Supertonic M1~M5 또는 F1~F5 선택
 미리듣기에서 목소리 비교 가능
 '로컬 성우 감정' → 자동(문단별) 혹은 공포·긴장/슬픔·감동 선택
 '문단별 지정' 예: 2=슬픔,4=놀람,6=공포
 ※ 문단 번호는 사진/빈 줄 제외, 실제 나레이션 문단 1부터 시작
 '로컬 성우 품질(5~12)' 5=속도 우선, 8=품질 우선(느릴 수 있음)
 '로컬 성우 실패시 Edge 전환' on=실패시 Edge로 변환/경고, off=오류로 중단
 ★ 자막에는 감정 태그가 나오지 않으며 문단별 원본 글은 그대로 유지됩니다.

[5] 8GB RAM 권장
 영상 → FPS 30 (처음부터 60FPS 렌더링을 피하세요)
 먼저 대본 3~4문단 + 나레이션 만들기 → 미리듣기 → MP4 순서로 시험하세요.
 CPU 음성 생성은 한 번에 하나씩 처리하며 모델을 재활용합니다.
 8GB에서 메모리 부족이 생기면 다른 프로그램을 종료하세요.
 합성 중 '현재 작업 중지'를 누르면 음성 워커 프로세스가 종료됩니다.

[6] 음성이 생성되지 않을 때
 - 설치 단계 오류: 설치창 마지막 오류 메시지 확인
 - 오류 로그: supertonic_worker_error.log 확인
 - 무료 성우 준비되지 않았을 때: 설정에서 기존 Edge 성우를 선택하면 됩니다.
 - 설치 및 모델 파일이 없는 경우 Supertonic을 선택해도 자동으로 Edge 백업(설정이 on일 때)으로 넘어갑니다.
 - 저장 모델 폴더: supertonic_assets\onnx 및 supertonic_assets\voice_styles 필요
 - 별도 가상환경 설치는 원본 프로그램에 설치된 Python과 충돌하지 않도록 하기 위함입니다.

[감정 표현 한계]
 Supertonic 3 감정 태그는 확실한 연기 지시 모델이 아닙니다.
 <sad>, <surprise>, <laugh>, <breath>, <angry> 등의 태그는 일부 문장에서 무시되거나
 그대로 읽힐 수 있습니다. 공포 분위기는 <breath> + 속도 하향으로 구현합니다.
 원문 자막은 바뀌지 않으므로 최종 청취 후 선택하세요.
 '자동(문단별)'의 감정 분류는 단순 한국어 키워드 규칙이며 대본 의미를 이해하는 AI 분류가 아닙니다.
 정확한 표현은 '문단별 지정'에서 수동 설정하는 것이 좋습니다.

[라이선스/저작권]
 Supertonic Python 코드: MIT; 모델: OpenRAIL-M 사용 제한 적용
 영상 공개 시 합성 음성 고지/저작권/사용 제한을 확인하세요.
 기존 Supertonic GitHub는 2026-09-09 보관 처리되어 공식 유지보수 종료.
 코드: https://github.com/supertone-oss-archive/supertonic-py
 모델: https://huggingface.co/supertone-oss-archive/supertonic-3

[검증 범위]
 이 패키지는 Python 문법/기능 단위 검사 후 제공됩니다.
 모델 가중치 다운로드 및 실제 베이직북 PC에서의 음질·실행 속도는 확인하지 않았습니다.
