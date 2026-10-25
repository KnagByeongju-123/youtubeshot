#!/bin/bash
# 안티키테라 다큐: 프로젝트 → 장면별 영상(메인 저장소의 프로그램) → 발음·겹침 검사 (작업_이어하기 줄에서 씀)
W=/home/user/youtubeshot/.wt_longform/장문/안티키테라
cd /home/user/youtubeshot
.supertonic_venv/bin/python $W/안티키테라_기계.py project $W/그림 || exit 1
nice -n 5 xvfb-run -a .supertonic_venv/bin/python -X utf8 render_project.py $W/안티키테라_기계.json --대본그대로 --길이고정 --자막언어 영어,일본어 || exit 1
F=$(ls -t output/장문/*/"2천 년 전 바닷속 컴퓨터, 안티키테라 기계의 수수께끼.mp4" 2>/dev/null | head -1)
.sd_venv/bin/python 나레이션_발음검사.py "$F" $W/안티키테라_기계.py --기준 0.6 --결과 "${F%.mp4}_발음검사.txt"
.sd_venv/bin/python 나레이션_겹침검사.py "$F" $W/안티키테라_기계.py --결과 "${F%.mp4}_겹침검사.txt"
exit 0
