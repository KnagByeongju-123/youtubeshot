"""일식709 컷마다 사진 후보 받기 (../안티키테라/사진_찾기.py 를 검색어만 바꿔 씀, 여러 곳: ../사진_여러곳.py)
  python ../사진_여러곳.py 일식709/사진_찾기.py 일식709/사진후보 [컷들]"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "안티키테라"))
import 사진_찾기 as F
F.Q = {
    "c01": "Total solar eclipse 2017", "c03": "Confucius portrait", "c04": "Chunqiu", "c05": "Temple of Confucius Qufu",
    "c06": "Geometry of a total solar eclipse", "c07": "Solar corona", "c09": "Qufu city wall", "c11": "Low tide", "c12": "Full moon photo",
    "c14": "Sundial Forbidden City", "c15": "Hanshu", "c16": "Sunspot", "c18": "Tree rings", "c19": "Ice core",
    "c20": "Total solar eclipse 2024", "c21": "Solar eclipse 2019 Chile", "c22": "Eclipse viewing glasses", "c23": "Ancient Observatory Beijing",
    "c24": "Earth from space", "c25": "Partial eclipse sun",
}
if __name__ == "__main__":
    F.main()
