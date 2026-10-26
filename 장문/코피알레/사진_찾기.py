"""코피알레 컷마다 위키미디어 공용 사진 후보 받기 (../안티키테라/사진_찾기.py 를 검색어만 바꿔 씀)
  python 사진_찾기.py 사진후보 [컷들]"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "안티키테라"))
import 사진_찾기 as F
F.Q = {
    "c02": "Copiale cipher", "c03": "Copiale cipher page", "c04": "Berlin-Brandenburgische Akademie der Wissenschaften Jägerstraße",
    "c06": "USC Information Sciences Institute", "c07": "Uppsala University main building",
    "c15": "Wolfenbüttel Schloss", "c20": "surgeon performing an operation for cataract engraving", "c21": "Pope Clement XII portrait",
    "c22": "Freimaurer Initiation", "c24": "salon of Madame Geoffrin Lemonnier",
    "c25": "Staatsarchiv Wolfenbüttel", "c26": "Vatican Library manuscript", "c15b": "Wolfenbüttel Stadtansicht",
    "c13b": "18th century spectacles",
}
if __name__ == "__main__":
    F.main()
