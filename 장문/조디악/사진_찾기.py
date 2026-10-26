"""조디악 컷마다 위키미디어 공용 사진 후보 받기 (../안티키테라/사진_찾기.py 를 검색어만 바꿔 씀)
  python 사진_찾기.py 사진후보 [컷들]"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "안티키테라"))
import 사진_찾기 as F
F.Q = {
    "c01": "Z340", "c09": "Z408", "c06": "Zodiac Killer", "c07": "Zodiac killer letter",
    "c03": "San Francisco 1960s", "c12": "San Francisco Chronicle building", "c17": "David Oranchak", "c25": "San Quentin State Prison",
    "c26": "J. Edgar Hoover Building", "c27": "FBI seal", "c29": "Mount Diablo State Park", "c32": "Presidio Heights", "c35": "Golden Gate Bridge fog",
    "c30": "Zodiac cipher",
}
if __name__ == "__main__":
    F.main()
