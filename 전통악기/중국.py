"""중국 전통 — 고쟁(뜯는 현) + 얼후(활로 켜는 현). 실제 소리는 프로그램 폴더의 중국현악.py (삼국지 편에서 쓰던 그대로)"""
import importlib.util
import os

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
