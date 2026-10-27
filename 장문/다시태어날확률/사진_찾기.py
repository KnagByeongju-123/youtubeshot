"""다시 태어날 확률 — 컷마다 사진 후보 받기 (../안티키테라/사진_찾기.py 를 검색어만 바꿔 씀, 여러 곳: ../사진_여러곳.py)
  python ../사진_여러곳.py 다시태어날확률/사진_찾기.py 다시태어날확률/사진후보 [컷들]"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "안티키테라"))
import 사진_찾기 as F
F.Q = {
    "c01": "Milky Way night sky", "c03": "Crab Nebula Hubble", "c04": "Pillars of Creation Webb", "c06": "forest soil", "c07": "Henri Poincaré",
    "c08": "Ludwig Boltzmann", "c10": "Hubble deep field galaxies", "c11": "human cells microscope", "c12": "nuclear test 1950s mushroom cloud",
    "c13": "cortical neurons Golgi stain", "c14": "ancient Greek ship painting", "c15": "human brain", "c17": "laboratory mouse",
    "c18": "hippocampus neurons", "c19": "Drosophila melanogaster", "c20": "FlyWire connectome", "c21": "electron microscope",
    "c22": "human cortex neurons H01", "c24": "data center servers", "c25": "Pale Blue Dot",
}
if __name__ == "__main__":
    F.main()
