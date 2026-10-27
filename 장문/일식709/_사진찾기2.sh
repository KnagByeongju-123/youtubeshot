#!/bin/bash
cd /home/user/youtubeshot/.wt_longform/장문
sleep 60
/home/user/youtubeshot/.supertonic_venv/bin/python 사진_여러곳.py 일식709/사진_찾기.py 일식709/사진후보 c04,c06,c07,c12,c14,c15,c16,c20,c21,c23,c25 --곳 commons >> 일식709/사진.log 2>&1
exit 0
