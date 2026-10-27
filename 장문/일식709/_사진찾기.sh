#!/bin/bash
cd /home/user/youtubeshot/.wt_longform/장문
/home/user/youtubeshot/.supertonic_venv/bin/python 사진_여러곳.py 일식709/사진_찾기.py 일식709/사진후보 --곳 commons >> 일식709/사진.log 2>&1
[ -f 로미토/사진_찾기.py ] && /home/user/youtubeshot/.supertonic_venv/bin/python 사진_여러곳.py 로미토/사진_찾기.py 로미토/사진후보 --곳 commons >> 로미토/사진.log 2>&1
exit 0
