"""프랭클린 원정대 컷마다 사진 후보 받기 (../안티키테라/사진_찾기.py 를 검색어만 바꿔 씀, 여러 곳: ../사진_여러곳.py)
  python ../사진_여러곳.py 사진_찾기.py 사진후보 [컷들]"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "안티키테라"))
import 사진_찾기 as F
F.Q = {
    "c02": "HMS Erebus and Terror", "c03": "John Franklin portrait", "c04": "Northwest Passage map",
    "c05": "Franklin expedition tins", "c07": "Beechey Island graves", "c08": "Beechey Island",
    "c09": "HMS Terror ice 1837", "c10": "Victory Point note Franklin", "c11": "Francis Crozier",
    "c12": "John Rae explorer portrait", "c13": "Jane Franklin portrait", "c14": "McClintock Fox ship",
    "c15": "They forced the last link with their lives", "c17": "Franklin expedition relics",
    "c20": "Erebus wreck Parks Canada", "c23": "James Fitzjames daguerreotype", "c24": "King William Island",
    "c25": "Erebus Bay King William Island", "c26": "Franklin memorial Waterloo Place", "c28": "Franklin expedition officers daguerreotype",
}
if __name__ == "__main__":
    F.main()
