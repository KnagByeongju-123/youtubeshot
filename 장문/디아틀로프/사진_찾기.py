"""디아틀로프 고개 — 컷마다 사진 후보 받기 (../안티키테라/사진_찾기.py 를 검색어만 바꿔 씀, 여러 곳: ../사진_여러곳.py)
  python ../사진_여러곳.py 디아틀로프/사진_찾기.py 디아틀로프/사진후보 [컷들]"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "안티키테라"))
import 사진_찾기 as F
F.Q = {
    "c01": "Dyatlov tent 1959", "c02": "Northern Ural mountains winter", "c03": "Dyatlov group 1959", "c04": "Igor Dyatlov",
    "c05": "Dyatlov expedition skiing", "c06": "Yuri Yudin Dyatlov", "c07": "Dyatlov pass group photo", "c08": "Kholat Syakhl",
    "c09": "Dyatlov tent cut", "c10": "Dyatlov footprints", "c11": "Dyatlov cedar", "c12": "Dyatlov search party",
    "c13": "Dyatlov ravine", "c14": "Dyatlov pass memorial", "c16": "Ural Polytechnic Institute", "c18": "slab avalanche",
    "c19": "EPFL Lausanne", "c21": "snow cornice wind drift", "c22": "snowpack crack avalanche", "c24": "Ural mountains night",
    "c25": "Dyatlov Pass",
}
if __name__ == "__main__":
    F.main()
