"""로미토 컷마다 사진 후보 받기 (../안티키테라/사진_찾기.py 를 검색어만 바꿔 씀, 여러 곳: ../사진_여러곳.py)
  python ../사진_여러곳.py 로미토/사진_찾기.py 로미토/사진후보 [컷들]"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "안티키테라"))
import 사진_찾기 as F
F.Q = {
    "c01": "Romito cave", "c03": "Pollino National Park", "c04": "Romito aurochs engraving", "c05": "Upper Paleolithic flint tools",
    "c06": "Red deer stag", "c07": "Papasidero", "c08": "Paleolithic grave", "c10": "Human skeleton",
    "c12": "Petrous part of the temporal bone", "c13": "Ancient DNA clean room", "c14": "DNA structure", "c16": "Epiphyseal plate",
    "c18": "Human chromosomes karyotype", "c21": "Shanidar Cave", "c22": "DNA sequencing laboratory", "c23": "Calabria mountains valley",
    "c24": "Shell beads prehistoric", "c25": "Papasidero landscape",
}
if __name__ == "__main__":
    F.main()
