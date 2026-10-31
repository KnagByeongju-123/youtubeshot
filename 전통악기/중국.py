"""중국 전통 — 현악: 고쟁(뜯는 현) + 얼후(활로 켜는 현), 실제 소리는 프로그램 폴더의 중국현악.py (삼국지 편에서 쓰던 그대로)
관악: 디즈(맑은 가로피리, 청 떨림) + 샤오(낮은 세로피리), 낮은 음은 고쟁"""
import importlib.util
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import 공통 as K  # noqa: E402

_spec = importlib.util.spec_from_file_location("china_strings", os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "중국현악.py"))
_cs = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_cs)


class _China:
    name, instruments = "중국", "고쟁·얼후"
    modes = _cs.MODES

    def interlude(self, rng, sec=4.0, mode=None):
        return _cs.interlude(rng, sec, mode or "궁조")

    def bed(self, n, rng, mode=None):
        return _cs.bed(n, rng, mode or "궁조")

    def sample(self, mode, sec=30, seed=11):
        return _cs.sample(mode, sec, seed)


REGION = _China()

WIND = K.Region(
    "중국", "디즈·샤오",
    lead=lambda f, d, rng, last: K.flute(f, d, breath=0.14, vib=0.01 if last else 0.006, slide=0.03, membrane=0.06, rng=rng),
    sustain=lambda f, d, rng: K.flute(f * 0.5, d, breath=0.3, vib=0.004, rng=rng),
    bass=lambda f, d, rng, last: _cs.guzheng(f, d, rng=rng),
    modes=_cs.MODES, legato=True, gliss=False, tempo=0.55)
