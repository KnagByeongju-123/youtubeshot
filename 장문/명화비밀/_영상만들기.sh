#!/bin/bash
# 명화비밀 다큐: 프로젝트 → 장면별 영상(메인 저장소의 프로그램) → 발음·겹침 검사 (작업_이어하기 줄에서 씀)
W=/home/user/youtubeshot/.wt_longform/장문/명화비밀
cd /home/user/youtubeshot
# 마지막에 다시 그린 컷(그림_새로 png)을 그림 폴더 jpg 로 (그림 폴더에 없는 것만)
.supertonic_venv/bin/python -c "
import os,sys
from PIL import Image
W=sys.argv[1]
for f in os.listdir(W+'/그림_새로'):
    c=f[:-4]
    if f.endswith('.png') and not os.path.exists(f'{W}/그림/{c}.jpg') and not os.path.exists(f'{W}/사진/{c}.jpg'):
        Image.open(f'{W}/그림_새로/{f}').convert('RGB').save(f'{W}/그림/{c}.jpg',quality=92); print('그림 추가',c)
" $W
.supertonic_venv/bin/python $W/명화_숨은비밀.py project $W/그림 || exit 1
nice -n 5 xvfb-run -a .supertonic_venv/bin/python -X utf8 render_project.py $W/명화_숨은비밀.json --대본그대로 --길이고정 --자막언어 영어,일본어 || exit 1
F=$(ls -t output/장문/*/"과학이 밝혀낸 명화 속 숨은 비밀 5가지.mp4" 2>/dev/null | head -1)
.sd_venv/bin/python 나레이션_발음검사.py "$F" $W/명화_숨은비밀.py --기준 0.6 --결과 "${F%.mp4}_발음검사.txt"
.sd_venv/bin/python 나레이션_겹침검사.py "$F" $W/명화_숨은비밀.py --결과 "${F%.mp4}_겹침검사.txt"
exit 0
