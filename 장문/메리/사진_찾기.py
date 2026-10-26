"""메리 스튜어트 컷마다 위키미디어 공용 사진 후보 받기 (../안티키테라/사진_찾기.py 를 검색어만 바꿔 씀)
  python 사진_찾기.py 사진후보 [컷들]"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "안티키테라"))
import 사진_찾기 as F
F.Q = {
    "c02": "Mary Queen of Scots portrait", "c04": "Linlithgow Palace", "c05": "Mary Stuart Clouet", "c06": "Francis II Mary Stuart",
    "c07": "Holyrood Palace", "c08": "Lochleven Castle", "c09": "Elizabeth I portrait", "c10": "Tutbury Castle",
    "c11": "Sheffield Manor Lodge", "c13": "Bibliotheque nationale Richelieu", "c17": "Francis Walsingham", "c18": "Michel de Castelnau",
    "c20": "James VI young", "c21": "National Archives Kew", "c22": "Chartley", "c24": "Babington postscript",
    "c26": "Fotheringhay", "c27": "execution of Mary Queen of Scots", "c28": "Westminster Abbey", "c24": "Mary Queen of Scots cipher",
}
if __name__ == "__main__":
    F.main()
