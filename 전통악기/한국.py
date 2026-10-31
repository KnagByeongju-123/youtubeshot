"""한국 전통 — 가야금(뜯는 현, 농현으로 줄을 흔듦) + 해금(활로 켜는 현). 조선왕조실록 편 등"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import 공통 as K  # noqa: E402


REGION = K.Region(
    "한국", "가야금·해금",
    lead=lambda f, d, rng, last: K.pluck(f, d, damp=0.994, bright=0.35, bend=0.04 if last else 0.0, vib=0.012 if last else 0.004, rng=rng),
    sustain=lambda f, d, rng: K.bowed(f, d, band=(700, 3600), vib_rate=4.5, vib=0.012, nasal=1.0),
    modes={"평조": ([0, 2, 5, 7, 9], 52, "차분하고 너그러움 (궁중·평온)"),
           "계면조": ([0, 3, 5, 7, 10], 52, "슬프고 애절 (비극·이별)")},
    tempo=0.5)
