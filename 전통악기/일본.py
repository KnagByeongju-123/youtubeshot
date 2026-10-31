"""일본 전통 — 고토(뜯는 현) + 샤쿠하치(대나무 피리). 임진왜란·일본 관련 편 등"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import 공통 as K  # noqa: E402


REGION = K.Region(
    "일본", "고토·샤쿠하치",
    lead=lambda f, d, rng, last: K.pluck(f, d, damp=0.992, bright=0.75, bend=0.03 if last else 0.0, rng=rng),
    sustain=lambda f, d, rng: K.flute(f, d, breath=0.3, vib=0.006, slide=0.03, rng=rng),
    modes={"미야코부시": ([0, 1, 5, 7, 8], 52, "어둡고 쓸쓸 (전쟁·무사)"),
           "요음계": ([0, 2, 5, 7, 9], 52, "소박하고 밝음 (민속·마을)")},
    tempo=0.5)
