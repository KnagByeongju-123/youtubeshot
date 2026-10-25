"""데니소바 컷마다 위키미디어 공용 사진 후보 받기 (../안티키테라/사진_찾기.py 를 검색어만 바꿔 씀)
  python 사진_찾기.py 사진후보 [컷들]"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "안티키테라"))
import 사진_찾기 as F
F.Q = {
    "c02": "Denisova cave Altai", "c05": "Altai Republic mountains", "c07": "Svante Paabo", "c09": "Neanderthal skull",
    "c14": "Tibetan Plateau", "c16": "Xiahe mandible", "c19": "Penghu 1", "c21": "Harbin skull",
    "c26": "Laos limestone karst", "c28": "Papua New Guinea people", "c33": "Neanderthal modern human skull",
    "c35": "Denisova excavation", "c11": "Denisovan tooth", "c01": "Denisovan finger",
}
if __name__ == "__main__":
    F.main()
