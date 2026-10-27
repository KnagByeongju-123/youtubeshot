#!/bin/bash
# 사진 후보 받기 (위키미디어만, 차례로): 모아이 전체 → 구멍 띠 남은 컷
cd /home/user/youtubeshot/.wt_longform/장문
P=/home/user/youtubeshot/.supertonic_venv/bin/python
$P 사진_여러곳.py 모아이/사진_찾기.py 모아이/사진후보 --곳 commons >> 모아이/사진.log 2>&1
$P 사진_여러곳.py 구멍띠/사진_찾기.py 구멍띠/사진후보 c02,c14,c16,c24,c25 --곳 commons >> 구멍띠/사진3.log 2>&1
exit 0
