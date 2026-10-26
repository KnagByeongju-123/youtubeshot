"""카라한 테페 컷마다 사진 후보 받기 (../안티키테라/사진_찾기.py 를 검색어만 바꿔 씀, 여러 곳: ../사진_여러곳.py)
  python ../사진_여러곳.py 카라한테페/사진_찾기.py 카라한테페/사진후보 [컷들]"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "안티키테라"))
import 사진_찾기 as F
F.Q = {
    "c01": "Karahan Tepe", "c02": "Göbekli Tepe", "c03": "Göbekli Tepe T-shaped pillar", "c04": "Göbekli Tepe pillar fox relief",
    "c05": "Şanlıurfa landscape", "c06": "Karahantepe excavation", "c08": "Karahantepe pillars head", "c09": "Karahan Tepe pillars",
    "c10": "Karahantepe snake", "c11": "Karahantepe statue", "c12": "Urfa Man statue", "c13": "Şanlıurfa Archaeology Museum",
    "c14": "Göbekli Tepe boar", "c15": "Göbekli Tepe vulture stone pillar 43", "c16": "Göbekli Tepe fox", "c19": "Göbekli Tepe pillar arms hands",
    "c20": "Göbekli Tepe pillar 18 arms belt", "c21": "Neolithic house Anatolia", "c22": "Mountain gazelle", "c23": "Lentil wild",
    "c24": "Einkorn wheat", "c25": "Göbekli Tepe roof", "c26": "Sayburç", "c27": "Göbekli Tepe panorama",
}
if __name__ == "__main__":
    F.main()
