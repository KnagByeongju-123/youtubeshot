"""몽골·중앙아시아 초원 — 마두금(말머리 현악기, 활) + 톱쇼르(뜯는 현) + 후미(목으로 내는 배음 바탕음). 흉노·몽골제국·실크로드 편 등"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import 공통 as K  # noqa: E402


REGION = K.Region(
    "몽골", "마두금·톱쇼르·후미",
    lead=lambda f, d, rng, last: K.pluck(f, d, damp=0.99, bright=0.3, rng=rng),
    sustain=lambda f, d, rng: K.bowed(f * 0.5, d + 1, band=(250, 2400), vib_rate=4.0, vib=0.01, attack=0.6, nasal=0.7),
    modes={"초원장조": ([0, 2, 4, 7, 9], 47, "넓고 웅장 (초원·기마·제국)"),
           "초원단조": ([0, 3, 5, 7, 10], 47, "쓸쓸하고 아득 (원정·이별)")},
    drone_kind="throat", gliss=False, tempo=0.55)


WIND = K.Region(   # 관악: 림베(가로피리, 긴 숨) + 마두금, 낮은 음은 톱쇼르, 후미 바탕음
    "몽골", "림베·마두금·후미",
    lead=lambda f, d, rng, last: K.flute(f, d, breath=0.25, vib=0.009, slide=0.02, rng=rng),
    sustain=REGION.sustain, bass=REGION.lead, modes=REGION.modes, drone_kind="throat", legato=True, gliss=False, tempo=0.7)
