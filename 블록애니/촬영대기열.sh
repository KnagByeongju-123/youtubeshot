#!/bin/bash
# 촬영 대기열: 작업마다 샷을 3묶음으로 나눠 동시에 찍고, 끝나면 다음 작업.  사용: bash 촬영대기열.sh "<샷목록> <모형폴더> <프레임폴더>" ...
cd "$(dirname "$0")/.."
for job in "$@"; do
  set -- $job; SL=$1; MD=$2; FD=$3; mkdir -p "$FD"
  mapfile -t G < <(python3 -c "
import json,sys; s=[x['name'] for x in json.load(open('$SL',encoding='utf-8'))['shots']]; n=len(s); k=(n+2)//3
for i in range(3): print(','.join(s[i*k:(i+1)*k]))")
  echo "시작 $SL $(date +%T)"
  for g in "${G[@]}"; do [ -n "$g" ] && node 블록애니/blockbench_샷촬영.js "$SL" "$MD" "$FD" "$g" > "$FD.$RANDOM.log" 2>&1 & done
  wait; echo "끝 $SL $(date +%T)"
done
echo 대기열끝
