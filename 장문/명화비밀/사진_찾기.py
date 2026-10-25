"""명화비밀 컷마다 위키미디어 공용 사진 후보 받기 (../안티키테라/사진_찾기.py 를 검색어만 바꿔 씀)
  python 사진_찾기.py 사진후보 [컷들]"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "안티키테라"))
import 사진_찾기 as F
F.Q = {
    "c03": "X-ray radiograph of painting", "c09": "Giulio Romano self-portrait", "c12": "anatomical theatre Leiden",
    "c13": "painting conservation X-ray museum", "c21": "Arthur Brand art detective", "c24": "painting restorer at work",
    "c30": "Galleria Ricci Oddi interno", "c36": "Mauritshuis interior gallery",
    "c02": "Klimt Portrait of a Lady Piacenza", "c05": "Raphael Madonna della Rosa", "c06": "Museo del Prado building",
    "c10": "Anatomy Lesson of Dr. Nicolaes Tulp", "c11": "Mauritshuis", "c15": "Brueghel woman embers",
    "c16": "Muzeum Narodowe Gdansk", "c20": "Museum Gouda", "c22": "Vermeer Brieflezend meisje",
    "c23": "Zwinger Dresden Gemaldegalerie", "c25": "Vermeer Girl Reading Letter restored Cupid", "c27": "Galleria Ricci Oddi Piacenza",
    "c34": "Klimt Portrait of a Young Lady", "c08": "Raphael Madonna della Rosa detail",
}
if __name__ == "__main__":
    F.main()
