"""모아이 컷마다 사진 후보 받기 (../안티키테라/사진_찾기.py 를 검색어만 바꿔 씀, 여러 곳: ../사진_여러곳.py)
  python ../사진_여러곳.py 모아이/사진_찾기.py 모아이/사진후보 [컷들]"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "안티키테라"))
import 사진_찾기 as F
F.Q = {
    "c01": "Ahu Tongariki", "c02": "Easter Island aerial", "c03": "Rano Raraku", "c04": "Rano Raraku unfinished moai El Gigante",
    "c05": "Ahu Nau Nau", "c06": "Roggeveen Easter Island", "c07": "Thor Heyerdahl", "c09": "Easter Island grassland landscape",
    "c10": "fallen moai road", "c12": "moai profile side view", "c15": "Rano Raraku moai road", "c17": "broken moai",
    "c19": "Ahu Akivi", "c20": "Pukao Puna Pau", "c21": "Rapa Nui manavai garden", "c22": "Tapati Rapa Nui festival",
    "c23": "Ahu Tongariki sunrise", "c24": "Rano Raraku moai heads slope", "c25": "Anakena moai",
}
if __name__ == "__main__":
    F.main()
