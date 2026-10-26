"""조세르 피라미드 물 승강기 — 컷마다 사진 후보 받기 (../안티키테라/사진_찾기.py 를 검색어만 바꿔 씀, 여러 곳: ../사진_여러곳.py)
  python ../사진_여러곳.py 사진_찾기.py 사진후보 [컷들]"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "안티키테라"))
import 사진_찾기 as F
F.Q = {
    "c02": "Pyramid of Djoser", "c03": "Saqqara necropolis panorama", "c04": "Step pyramid Djoser south side", "c05": "Imhotep statuette Louvre",
    "c06": "Djoser burial chamber granite", "c07": "Gisr el-Mudir", "c08": "Djoser complex enclosure wall", "c10": "Saqqara desert wadi",
    "c15": "Djoser pyramid sunset", "c16": "Djoser pyramid interior shaft", "c17": "Djoser complex south tomb",
    "c18": "Saqqara aerial view", "c19": "Nile felucca", "c20": "Diary of Merer papyrus", "c21": "Tura limestone casing stones Great Pyramid",
    "c22": "Hatnub quarry", "c24": "Dahshur pyramids Nile valley", "c25": "Giza workers tombs", "c26": "Giza pyramids",
    "c27": "Djoser pyramid restoration", "c28": "Meketre model boat",
}
if __name__ == "__main__":
    F.main()
