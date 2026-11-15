#!/bin/bash
# 사용: bash 촬영.sh  (jobs.txt 의 '장면 시작 끝' 을 3개씩 동시에)
cd "$(dirname "$0")"
B=/home/user/blender-4.2.3-linux-x64/blender
cat ${JOBS:-jobs.txt} | xargs -P ${PAR:-3} -L 1 bash -c 'B='"$B"'; $B -b -P $0.py -- --render $1 $2 > _log_$0_$1.txt 2>&1; echo done $0 $1'
echo ALL_DONE
