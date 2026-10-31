"""인도 전통 — 시타르풍 뜯는 현(지잉 울림) + 반수리(대나무 피리) + 탄푸라 바탕음. 인도·불교 편 등"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import 공통 as K  # noqa: E402


REGION = K.Region(
    "인도", "시타르·반수리·탄푸라",
    lead=lambda f, d, rng, last: K.pluck(f, d, damp=0.996, bright=0.6, bend=0.05 if last else 0.02, buzz=0.45, rng=rng),
    sustain=lambda f, d, rng: K.flute(f, d, breath=0.2, vib=0.008, slide=0.04, rng=rng),
    modes={"야만": ([0, 2, 4, 6, 7, 9, 11], 50, "고요하고 경건 (밤·명상)"),
           "바이라비": ([0, 1, 4, 5, 7, 8, 11], 50, "엄숙하고 깊음 (새벽·종교)"),
           "카피": ([0, 2, 3, 5, 7, 9, 10], 50, "부드럽고 그리움 (사랑·민중)")},
    drone_kind="pluck", gliss=False, tempo=0.5)
