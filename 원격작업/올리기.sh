#!/bin/bash
# 그린 컷 PNG 를 5분마다 이 브랜치에 올림 (그림 프로그램이 끝나면 마지막으로 한 번 더 올리고 끝)
cd "$(dirname "$0")/.."
while true; do
  git add -f 원격작업/컷/*.png 2>/dev/null
  git commit -qm "원격 컷 그림 $(ls 원격작업/컷/*.png 2>/dev/null | wc -l)장" 2>/dev/null && \
    for i in 1 2 3 4; do git push -q origin HEAD:claude/saida-cuts-remote && break; sleep $((2**i)); done
  pgrep -f "klein_worker.py" >/dev/null || { [ -f 원격작업/끝 ] && break; touch 원격작업/끝; }
  sleep 300
done
