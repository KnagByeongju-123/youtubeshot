"""크레타 파푸라 미궁 컷마다 사진 후보 받기 (../안티키테라/사진_찾기.py 를 검색어만 바꿔 씀, 여러 곳: ../사진_여러곳.py)
  python ../사진_여러곳.py 크레타미궁/사진_찾기.py 크레타미궁/사진후보 [컷들]"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "안티키테라"))
import 사진_찾기 as F
F.Q = {
    "c01": "Crete coast aerial", "c02": "Theseus Minotaur kylix", "c03": "Knossos palace", "c04": "Minotaur Watts",
    "c05": "Theseus Ariadne painting", "c06": "Knossos coin labyrinth", "c07": "Arthur Evans", "c08": "Knossos north entrance columns",
    "c09": "Knossos fresco dolphins", "c10": "Minoan double axe labrys", "c11": "Linear B tablet Knossos", "c12": "Heraklion aerial",
    "c13": "Kastelli Heraklion", "c17": "Minoan Kamares ware", "c19": "Bull-leaping fresco Knossos", "c20": "Minoan tholos tomb Mesara",
    "c21": "Tiryns walls", "c22": "Kastelli airport construction", "c23": "Knossos labyrinth fresco", "c24": "Psiloritis mountains Crete",
    "c25": "Labyrinth mosaic Roman",
}
if __name__ == "__main__":
    F.main()
