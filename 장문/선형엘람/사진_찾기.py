"""선형 엘람 문자 — 컷마다 사진 후보 받기 (../안티키테라/사진_찾기.py 를 검색어만 바꿔 씀, 여러 곳: ../사진_여러곳.py)
  python ../사진_여러곳.py 선형엘람/사진_찾기.py 선형엘람/사진후보 [컷들]"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "안티키테라"))
import 사진_찾기 as F
F.Q = {
    "c01": "Linear Elamite silver vase", "c02": "Linear Elamite inscription", "c03": "Khuzestan landscape", "c04": "Susa archaeological site",
    "c05": "Chogha Zanbil ziggurat", "c06": "Ashurbanipal Elam campaign relief", "c07": "Proto-Elamite tablet", "c08": "Elamite cuneiform tablet",
    "c09": "Linear Elamite Louvre", "c10": "Behistun inscription", "c11": "Rosetta Stone", "c12": "Jean-François Champollion",
    "c13": "Table au Lion Linear Elamite", "c14": "Puzur-Inshushinak", "c16": "ancient silver beaker Iran", "c18": "cuneiform inscription Elam",
    "c20": "Linear Elamite Susa", "c21": "Louvre pyramid", "c22": "Persepolis", "c23": "National Museum of Iran", "c24": "Susa Acropolis tell", "c25": "Code of Hammurabi stele Louvre",
}
if __name__ == "__main__":
    F.main()
