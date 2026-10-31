"""중동 전통 — 우드(뜯는 현) + 네이(갈대 피리) + 다프(틀북, 아주 작게). 페르시아·이슬람·고대 근동 편 등
라스트·바야티의 3.5·10.5·1.5 는 반음의 반(4분음)"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import 공통 as K  # noqa: E402


REGION = K.Region(
    "중동", "우드·네이·다프",
    lead=lambda f, d, rng, last: K.pluck(f, d, damp=0.993, bright=0.45, bend=0.025 if last else 0.0, buzz=0.1, rng=rng),
    sustain=lambda f, d, rng: K.flute(f, d, breath=0.35, vib=0.007, slide=0.02, rng=rng),
    modes={"히자즈": ([0, 1, 4, 5, 7, 8, 10], 50, "이국적이고 긴장 (사막·제국·음모)"),
           "라스트": ([0, 2, 3.5, 5, 7, 9, 10.5], 50, "당당하고 따뜻 (궁정·번영)"),
           "바야티": ([0, 1.5, 3, 5, 7, 8, 10], 50, "애잔하고 그윽 (몰락·순례)")},
    drum=True, gliss=False, tempo=0.36)
