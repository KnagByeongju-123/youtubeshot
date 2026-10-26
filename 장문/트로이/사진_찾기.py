"""트로이 컷마다 사진 후보 받기 (../안티키테라/사진_찾기.py 를 검색어만 바꿔 씀, 여러 곳: ../사진_여러곳.py)
  python ../사진_여러곳.py 트로이/사진_찾기.py 트로이/사진후보 [컷들]"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "안티키테라"))
import 사진_찾기 as F
F.Q = {
    "c01": "Troy walls Hisarlik", "c02": "Homer bust British Museum", "c03": "Trojan War amphora", "c04": "Achilles Hector vase",
    "c05": "Trojan horse painting Tiepolo", "c06": "Hisarlik Troy aerial", "c07": "Heinrich Schliemann", "c08": "Schliemann trench Troy",
    "c09": "Sophia Schliemann Priam treasure", "c11": "Troy VI wall", "c12": "Troy gate ruins", "c13": "Hittite cuneiform tablet",
    "c14": "Hattusa Lion Gate", "c15": "Troy archaeological site", "c16": "Bronze Age sword spearhead", "c19": "sling bullet ancient",
    "c20": "Troy Museum Çanakkale", "c21": "Troad plain Scamander", "c22": "Troy VI sloping wall", "c23": "Dardanelles strait",
    "c24": "Trojan horse replica Troy", "c25": "Troy ruins ramp",
}
if __name__ == "__main__":
    F.main()
