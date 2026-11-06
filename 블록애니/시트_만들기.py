"""캐릭터 시트(앞·옆·옆·뒤) 만들기
xvfb-run -a ../.blender_venv/bin/python 시트_만들기.py <저장폴더> <이름> [이름 ...]
이름: 서진 서진_젊은 하린 정우 보름이 어린고래 먹장어 상어 게 새우 오세닥스 조개 해파리 발광물고기 연구선 탐사장치 고래뼈"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import 블록
import 사람
try:
    import 바다생물
except ImportError:
    바다생물 = None

def models():
    d = {"서진": 사람.서진, "서진_젊은": lambda: 사람.서진(True), "하린": 사람.하린, "정우": 사람.정우}
    if 바다생물:
        d.update(바다생물.MODELS)
    return d

def main():
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    tmp = os.path.join(out, "_조각")
    os.makedirs(tmp, exist_ok=True)
    M = models()
    for n in sys.argv[2:]:
        fn = M[n]
        m = fn()
        lo, hi = m.bounds()
        size = max(hi[i] - lo[i] for i in range(3))
        files = 블록.render_views(fn, os.path.join(tmp, n), px_per_unit=820 / size)
        블록.compose_sheet(files, os.path.join(out, f"{n}_시트.png"), f"{n} — 블록 캐릭터 시트")
        print("시트", n)

main()
