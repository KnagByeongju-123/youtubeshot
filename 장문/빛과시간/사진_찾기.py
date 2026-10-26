"""빛과 시간 컷마다 사진 후보 받기 (../안티키테라/사진_찾기.py 를 검색어만 바꿔 씀, 여러 곳: ../사진_여러곳.py)
  python ../사진_여러곳.py 사진_찾기.py 사진후보 [컷들]"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "안티키테라"))
import 사진_찾기 as F
F.Q = {
    "c02": "Betelgeuse Orion constellation", "c03": "Hubble Ultra Deep Field", "c04": "Full Moon", "c05": "Sun Solar Dynamics Observatory",
    "c06": "Andromeda Galaxy", "c08": "JADES-GS-z14-0", "c09": "James Webb Space Telescope", "c11": "redshift galaxies Webb deep field",
    "c12": "Einstein ring gravitational lens Hubble", "c13": "gravitational lensing galaxy cluster Webb", "c14": "Albert Einstein 1921",
    "c18": "Planck cosmic microwave background", "c20": "cosmic web simulation", "c22": "Webb deep field galaxies", "c24": "Pale Blue Dot Voyager 1990", "c26": "Jupiter Io Juno", "c27": "Edwin Hubble", "c28": "1919 solar eclipse Eddington", "c29": "Supernova Refsdal", "c30": "GPS satellite", "c31": "M87 black hole Event Horizon Telescope", "c32": "Euclid space telescope", "c33": "Hubble Deep Field 1995", "c13b": "Abell 2744 gravitational lensing", "c18b": "cosmic microwave background WMAP Planck map",
}
if __name__ == "__main__":
    F.main()
