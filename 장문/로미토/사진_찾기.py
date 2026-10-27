"""로미토 컷마다 사진 후보 받기 (../안티키테라/사진_찾기.py 를 검색어만 바꿔 씀, 여러 곳: ../사진_여러곳.py)
  python ../사진_여러곳.py 로미토/사진_찾기.py 로미토/사진후보 [컷들]"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "안티키테라"))
import 사진_찾기 as F
F.Q = {
    "c01": "Grotta del Romito", "c03": "Pollino National Park", "c04": "Grotta del Romito Bos primigenius", "c05": "Upper Paleolithic flint tools",
    "c06": "Red deer stag", "c07": "Papasidero", "c08": "Paleolithic burial reconstruction", "c10": "Human skeleton arm bones",
    "c12": "Temporal bone petrous", "c13": "Ancient DNA laboratory", "c14": "DNA double helix", "c16": "Growth plate x-ray",
    "c18": "Human chromosomes karyotype", "c21": "Shanidar Cave", "c22": "Genetic counseling", "c23": "Calabria mountains valley",
    "c24": "Paleolithic shell necklace", "c25": "Lao river Calabria",
}
if __name__ == "__main__":
    F.main()
