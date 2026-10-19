Supertonic 3 감정형 나레이션 - 다른 PC 설치용 통합 패키지
=======================================================

[중요]
이 패키지에는 정상 작동이 확인된 'UTF-8 한글 오류 수정 프로그램'이 포함되어 있습니다.
프로그램 원본도 함께 제공하며, 수정 프로그램은 별도 이름으로 실행합니다.

목차
  1. ZIP 파일로 다른 PC에 설치하기 (인터넷 연결 필요)
  2. 현재 잘되는 PC의 AI 모델까지 ZIP으로 만들기 (모델 재다운로드 방지)
  3. 폴더 구성 및 개인정보 보호
  4. 문제 해결

1. 일반 설치 - 다른 PC에서 최초 1회 인터넷 연결 필요
--------------------------------------------------
(1) Windows 10/11 64비트 PC에서 Python 3.11(64비트)을 설치합니다.
    Python 3.14가 이미 있어도 삭제할 필요가 없습니다.
    CMD에서 다음 명령으로 확인:
        py -3.11 --version
    공식 설치 파일(64비트):
        https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe

(2) 이 ZIP을 'C:\shorts_supertonic' 같은 폴더에 전부 압축 해제합니다.
    ZIP 내부에서 파일을 개별적으로 실행하지 마세요.
    경로에 특수문자를 넣지 않는 편이 안정적입니다.

(3) setup_supertonic_windows.bat 를 더블클릭합니다.
    새로운 PC 전용 .supertonic_venv 를 만들고 Python 패키지를 설치합니다.
    supertonic_assets 가 없으면 AI 모델 약 400MB를 내려받습니다.
    모델 폴더가 있으면 재다운로드 없이 건너뜁니다.
    마지막에 voice_samples\M1_neutral.wav 테스트 파일이 생성됩니다.
    인터넷은 최초 설치 및 필요 패키지를 받을 때 필요합니다.

(4) run_shorts_supertonic.bat 를 더블클릭해 프로그램을 실행합니다.
    '나레이션' → 나레이션 'on'
    '성우 선택' → Supertonic F1~F5 / M1~M5 를 선택합니다.
    미리듣기에서 정상 목소리가 나오는지 확인합니다.
    글이 깨지는 오류는 수정된 supertonic_local_worker.py 가 해결합니다.

2. 모델 다운로드 없이 전송할 ZIP 만들기 (현재 잘되는 PC에서 실행)
----------------------------------------------------------------
이 배포 ZIP에는 실제 AI 모델 파일(약 400MB)이 들어 있지 않습니다.
정상 작동하는 기존 PC에 이미 다운로드된 모델 파일을 사용하려면:

(1) 현재 잘되는 PC의 shorts_ 작업 폴더에 이 ZIP의 파일을 복사합니다.
    '기존 수정 프로그램 및 모델 폴더'는 절대 삭제하지 마세요.
    특히 supertonic_assets 폴더가 존재하는지 확인합니다.
    새로 받은 수정 프로그램 파일 2개를 덮어써도 기존과 같은 한글 수정본입니다.
(2) make_model_included_package.bat 를 더블클릭합니다.
(3) 같은 폴더에 Supertonic_model_included_transfer.zip 이 생성됩니다.
    이 ZIP은 현재 PC의 모델과 프로그램 코드를 모두 포함합니다.
    약 400MB 이상일 수 있으므로 생성에 시간이 걸립니다.
(4) 만들어진 ZIP을 USB나 외장 저장장치로 새 PC에 옮깁니다.
(5) 새 PC에서도 Python 3.11 설치 후 setup_supertonic_windows.bat 를 실행합니다.
    모델은 ZIP에 들어 있으므로 다운로드 단계를 건너뛰고,
    새 PC의 Python 패키지(가상환경)는 별도로 설치합니다.
    ★ 즉 '모델 포함 ZIP'도 최초 Python/패키지 설치에는 인터넷이 필요합니다.

3. 구성 파일
-----------
shorts_novel_maker_supertonic.py : 한글 UTF-8 오류 수정된 통합 제작 프로그램
supertonic_local_worker.py      : 로컬 TTS 워커(UTF-8 수정본)
supertonic_voice_test.py        : 무료 성우 테스트 프로그램
setup_supertonic_windows.bat    : 새 PC 최초 설치
run_shorts_supertonic.bat       : 프로그램 실행
make_model_included_package.bat : 현재 PC 모델 포함 ZIP 생성
make_model_included_package.py  : 모델 포함 ZIP 생성 처리
shorts_novel_maker.py           : 원본 프로그램 보관용
README_다른PC_설치방법.txt       : 이 안내서

모델 포함 ZIP에 추가되는 항목:
supertonic_assets\              : 현재 PC에 내려받은 AI 모델 전체(onnx, voice_styles 등)

포함하지 않는 항목:
.supertonic_venv\   : 다른 PC로 복사해서 쓰기 적합하지 않음. 새 PC에서 재생성.
shorts_novel_config.json : API 키와 사용자 설정이 있을 수 있어 개인정보 보호상 제외.
사용자 대본, 사진, 출력 영상, 생성 캐시 등: 설치에 필수는 아니므로 제외.

기존 작업도 이어가려면 대본/이미지/프로젝트 파일 등은 별도로 이동하세요.
특히 저장된 API 키와 비밀번호가 포함된 설정 파일을 타인에게 전달하지 마세요.

4. 오류 확인
-----------
- 'Python 3.11 not found': py -3.11 --version 확인, 64비트 Python 3.11 설치
- 'Found unsupported character': supertonic_local_worker.py 가 한글 수정본인지 확인
- 'Edge 403': Edge 서버 응답 문제. Supertonic 성우 선택 및 Edge 자동 전환 off
- 모델 없음: supertonic_assets\onnx 와 voice_styles 폴더를 확인
- 나레이션 오류: supertonic_worker_error.log 마지막 줄을 확인
- Windows 실행 차단: 파일 속성 > 차단 해제 및 신뢰할 수 있는 다운로드인지 확인
- 영상 만들기가 느림: FPS 30을 먼저 사용하고 다른 프로그램 종료

[저작권 안내]
오픈소스 엔진: https://github.com/supertone-oss-archive/supertonic-py
AI 모델: https://huggingface.co/supertone-oss-archive/supertonic-3
엔진 MIT / 모델 OpenRAIL-M 적용. 공개/상업 사용 시 모델 이용 조건 확인.

[검증 범위]
포함된 Python 파일 문법 검사 및 ZIP 내부파일 검사를 수행했습니다.
실제 사용 중인 Windows PC에서는 한글 수정본이 정상 작동한다고 사용자께서 확인했습니다.
다른 PC의 Windows/Python/네트워크 환경에서의 설치까지 보장할 수는 없습니다.

[사진 입체 움직임(2.5D) 모델]
- 장문·쇼츠 사진이 앞뒤로 입체감 있게 움직이는 기능은 깊이 추정 AI 모델이 필요합니다.
- 입체움직임_모델받기.bat 을 한 번 실행하면 models\depth_anything_v2_small_fp16.onnx (49.6MB, Apache-2.0) 를 받습니다.
- 모델이 없으면 기능이 자동으로 꺼지고 기존 평면 움직임만 씁니다. (설정 → 사진·장면 → 사진 입체 움직임)

[장문(10분 다큐) 자동 제작 .bat 모음]
장문_설정.json      : 주제·소재·길이(분)·배경음·연속_편수·연속_소재 (메모장으로 고쳐서 씀)
장문_만들기.bat     : 설정의 주제 한 편을 끝까지 (대본 → 사진 → 나레이션 → MP4 → 썸네일·업로드 문구)
장문_연속제작.bat   : AI가 인기 주제를 골라 '연속_편수' 편을 차례로 만듦. 소재는 '연속_소재' 목록을 돌아가며 쓰고,
                     비워 두면 기본 묶음(세계의 축제·풍속·역사·외딴 마을·고고학·음식·사고 교훈·도시…)을 돌아감.
                     진행 상황은 output\장문\_연속제작_진행.json 에 저장되어 꺼졌다 켜도 만들던 편부터 이어서 함.
장문_일시정지.bat / 장문_재개.bat : 잠시 멈췄다 이어서 (재개 때 만들기 창이 없으면 새로 띄움)
장문_끄기전_정리.bat : PC 끄기 전에 안전하게 멈춤 → 다시 켠 뒤 장문_만들기.bat(또는 연속제작.bat)으로 이어서
장문_사진보강.bat   : 이미 만든 대본에 사진을 더 넣고 영상만 다시
* 한 편(10분)에 이 PC 기준 약 40~60분 걸립니다 (조사·집필 10~15분, 사진 5~10분, 나레이션·영상 20~30분).

[실화 소재 탐색 → 실화 연속 제작]  (프로그램 창의 🔎 소재 탐색 버튼에서 모두 할 수 있음)
🔎 소재 탐색 버튼  : 무료로 주요 과학저널·과학 뉴스를 훑어 10분 다큐 소재를 고름. 종류 두 가지
                     · 🧩 풀린 수수께끼 찾기  = 실화_소재탐색.bat      (소재 '[실화] 과학이 밝혀낸 미스터리')
                     · 🆕 최근 밝혀진 발견 찾기 = 실화_최신발견탐색.bat (소재 '[실화] 최근 밝혀진 과학 발견', 최근 90일)
                     '📄 저널에서 찾기만'을 켜면 리포트·기획메모·썸네일만 만들고 주제 목록은 바꾸지 않음
                     탐색은 새 명령 창에서 돌아가고(몇 분), 결과는 output\장문\_소재탐색\날짜\ 에 소재별 폴더(기획메모.md·썸네일 3안·해시태그)
📑 주제 목록 열기   : 실화\주제목록.txt (한 줄 = 한 편, '소재 | 주제 | 기획메모 폴더'). 줄 앞에 # 를 붙이면 건너뜀
▶ 실화 연속 제작   : 실화_연속제작.bat 을 새 창으로 - 주제 목록을 순서대로 대본→사진→나레이션→MP4→업로드 문구까지
성우2로_다시만들기.bat : output\장문 의 영상을 모두 남자 성우 2(Supertonic M2)·배경음 거의 없음으로 다시 만듦

[폴더 구성]
소재탐색\            : 탐색 엔진 (topic_finder.py 저널·뉴스 검색, thumbs.py 썸네일, thumb_pick.py 썸네일 고르기 창, mp4_thumbs.py, tests\)
실화\주제목록.txt    : 실화 연속 제작이 순서대로 만들 주제 목록 (소재 탐색이 여기에 추가)
실화\챕터구성안.md   : 손으로 쓴 대본의 챕터 구성·출처·검증 주의
실화\대본\           : 완성 대본(프로젝트 .json) - render_project.py "실화\대본\1_별불가사리.json" --소재프로필 --kit 로 영상
실화\쇼츠\           : 롱폼에서 뽑은 세로 쇼츠 대본 - render_project.py "실화\쇼츠\1_별불가사리.json" --사진 8 --kit --suffix 쇼츠
output\장문\         : 완성 영상·썸네일·업로드 문구, _소재탐색\(탐색 결과), _연속제작_진행.json(이어 만들기 기록)

[Claude Code 를 인지하지 못할 때 (장문 연속 제작이 시작되지 않을 때)]
1) Claude Code 설치: PowerShell 에서  irm https://claude.ai/install.ps1 | iex   (또는  npm install -g @anthropic-ai/claude-code)
2) 설치 뒤 터미널에서  claude  를 한 번 실행해 Max 계정으로 로그인 (한 번만)
3) 그래도 "찾지 못했습니다"가 나오면 PowerShell 에서  Get-Command claude | Select-Object Source  로 경로를 확인한 뒤
   장문_설정.json 의  "claude_path"  에 그 경로를 적어 줍니다 (역슬래시는 두 번: C:\\Users\\이름\\.local\\bin\\claude.exe)
   프로그램이 찾는 위치: %USERPROFILE%\.local\bin, %APPDATA%\npm, npm 전역 폴더, scoop, PATH
* 장문_연속제작.bat 은 시작할 때 Claude Code 경로와 연결 상태를 먼저 출력합니다.
