"""나스카 컷마다 사진 후보 받기 (../안티키테라/사진_찾기.py 를 검색어만 바꿔 씀, 여러 곳: ../사진_여러곳.py)
  python ../사진_여러곳.py 나스카/사진_찾기.py 나스카/사진후보 [컷들]"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "안티키테라"))
import 사진_찾기 as F
F.Q = {
    "c01": "Nazca hummingbird", "c02": "Nazca lines aerial", "c03": "Nazca monkey", "c04": "Nazca spider", "c05": "Nazca trapezoid lines",
    "c06": "Nazca desert surface stones", "c07": "Maria Reiche", "c08": "Nazca observation tower", "c09": "Nazca pottery", "c10": "Nazca hillside geoglyph",
    "c12": "Nazca plane flight", "c13": "Nazca astronaut owlman", "c14": "Nazca dog geoglyph", "c17": "Llama Peru", "c18": "Nazca trophy head pottery",
    "c19": "Cahuachi", "c21": "Nazca whale geoglyph", "c22": "Nazca condor", "c23": "Nazca river valley", "c24": "Palpa geoglyphs", "c25": "Nazca tree geoglyph",
    "c26": "Nazca pampa",
}
if __name__ == "__main__":
    F.main()
