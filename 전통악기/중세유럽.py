"""중세 유럽 — 류트(뜯는 현) + 리코더 + 허디거디풍 바탕음. 로마 이후 유럽·십자군·수도원 편 등"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import 공통 as K  # noqa: E402


REGION = K.Region(
    "중세유럽", "류트·리코더·허디거디",
    lead=lambda f, d, rng, last: K.pluck(f, d, damp=0.993, bright=0.4, rng=rng),
    sustain=lambda f, d, rng: K.flute(f, d, breath=0.08, vib=0.003, rng=rng),
    modes={"도리안": ([0, 2, 3, 5, 7, 9, 10], 50, "엄숙하고 담담 (수도원·연대기)"),
           "믹솔리디안": ([0, 2, 4, 5, 7, 9, 10], 50, "밝고 소박 (장터·축제)"),
           "에올리안": ([0, 2, 3, 5, 7, 8, 10], 50, "어둡고 슬픔 (전쟁·흑사병)")},
    drone_kind="bowed", gliss=False, tempo=0.45)


WIND = K.Region(   # 관악: 리코더(맑은 세로피리) + 숌(겹서, 오보에 조상), 낮은 음은 류트, 허디거디풍 바탕음
    "중세유럽", "리코더·숌·허디거디",
    lead=lambda f, d, rng, last: K.flute(f, d, breath=0.06, vib=0.004 if last else 0.002, rng=rng),
    sustain=lambda f, d, rng: K.reed(f, d, band=(400, 2500), bright=0.3, vib=0.003),
    bass=REGION.lead, modes=REGION.modes, drone_kind="bowed", legato=True, gliss=False, tempo=0.5)
