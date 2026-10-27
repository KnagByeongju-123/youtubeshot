"""구멍 띠 컷마다 사진 후보 받기 (../안티키테라/사진_찾기.py 를 검색어만 바꿔 씀, 여러 곳: ../사진_여러곳.py)
  python ../사진_여러곳.py 구멍띠/사진_찾기.py 구멍띠/사진후보 [컷들]"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "안티키테라"))
import 사진_찾기 as F
F.Q = {
    "c01": "Band of Holes Peru", "c02": "Pisco River", "c03": "Shippee Johnson aerial Peru", "c04": "Monte Sierpe holes",
    "c07": "Inca storehouses qollqa", "c08": "Paracas Candelabra", "c11": "Tambo Colorado", "c13": "Peruvian maize corn varieties",
    "c14": "Typha latifolia", "c15": "Peru woven basket", "c16": "Aji amarillo", "c18": "Chincha culture",
    "c19": "Ballestas Islands guano", "c20": "Quipu", "c21": "Quipu knots close", "c23": "Qhapaq Nan Inca road",
    "c24": "Quipucamayoc", "c25": "Ica desert Peru",
}
if __name__ == "__main__":
    F.main()
