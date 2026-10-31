"""권역별 전통악기 배경음의 공통 부품 — 악기 소리를 컴퓨터로 직접 합성 (녹음 음원을 쓰지 않아 저작권 걱정 없음)
진짜 역사 기록관(역사 채널)용. 권역 파일(한국.py·중동.py …)은 악기 소리와 음계만 정하고, 연주 방식은 여기 Region 이 맡음

  - pluck  : 뜯는 현 (가야금·고토·우드·시타르·류트) — Karplus-Strong, 누르는 음(bend)·떨기(농현 vib)·줄 떨림(buzz)
  - bowed  : 활로 켜는 현 (해금·마두금·얼후) — 톱니파 + 떨림 + 몸통 울림(띠 필터)
  - flute  : 부는 악기 (샤쿠하치·네이·반수리·리코더·대금·디즈) — 사인파 + 숨소리, membrane: 대금·디즈의 청 떨림
  - reed   : 겹서(리드) 악기 (피리·주르나·셰나이·숌) — 좁은 펄스파 + 콧소리 띠
  - drone  : 계속 울리는 바탕음 (탄푸라·후미·허디거디)
  - frame_drum : 손으로 치는 틀북 (다프 등), 아주 작게
REGION = 현악(뜯는 현이 주인공), WIND = 관악(피리가 주인공) — 권역 파일마다 둘 다
Region(...).interlude(rng, sec, mode) : 챕터 제목 동안 한 소절 (훑기 → 짧은 가락 → 으뜸음으로 끝)
Region(...).bed(n, rng, mode)        : 나레이션 아래 잔잔한 배경
음 간격은 반음 단위 소수도 됨 (중동 4분음 3.5 등)
"""
import numpy as np

SR = 44100


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def pluck(freq, dur=2.0, damp=0.995, bright=0.5, bend=0.0, vib=0.0, buzz=0.0, rng=None):
    """뜯는 현 한 음. damp: 클수록 오래 울림, bright: 0~1 첫소리 밝기, bend: 뜯고 살짝 눌러 올림,
    vib: 줄을 흔드는 떨림(가야금 농현) 깊이, buzz: 줄이 브릿지에 닿아 나는 지잉 소리(시타르)"""
    from scipy.signal import lfilter
    rng = rng or np.random.default_rng()
    n = int(dur * SR)
    N = max(2, int(SR / freq))
    exc = np.zeros(n, np.float32)
    burst = rng.uniform(-1, 1, N).astype(np.float32)
    k = max(1, int(round((1 - bright) * 6)))
    burst = np.convolve(burst, np.ones(k) / k, "same")
    exc[:N] = burst
    a = np.zeros(N + 2, np.float32)
    a[0], a[N], a[N + 1] = 1.0, -0.5 * damp, -0.5 * damp
    y = lfilter([1.0], a, exc).astype(np.float32)
    t = np.arange(n) / SR
    if bend or vib:
        ratio = 1 + bend * np.clip((t - 0.25) / 0.25, 0, 1) * np.clip((1.2 - t) / 0.4, 0, 1)
        ratio = ratio + vib * np.sin(2 * np.pi * 4.5 * t) * np.clip((t - 0.3) / 0.5, 0, 1)
        pos = np.cumsum(ratio)
        pos = pos / pos[-1] * (n - 1)
        y = np.interp(pos, np.arange(n), y).astype(np.float32)
    if buzz:
        y = y + buzz * np.tanh(4 * y) * np.exp(-t / 0.8)
    env = np.minimum(1, np.arange(n) / (0.002 * SR))
    return (y * env / (np.abs(y).max() + 1e-6)).astype(np.float32)


def bowed(freq, dur=3.0, band=(600, 3200), vib_rate=5.3, vib=0.006, attack=0.35, nasal=0.8):
    """활로 켜는 현 한 음 (해금·얼후·마두금). band: 몸통 울림 띠, nasal: 콧소리 정도"""
    from scipy.signal import butter, lfilter
    n = int(dur * SR)
    t = np.arange(n) / SR
    v = 1 + vib * np.sin(2 * np.pi * vib_rate * t) * np.clip(t / 0.6, 0, 1)
    ph = np.cumsum(2 * np.pi * freq * v / SR)
    saw = (2 * ((ph / (2 * np.pi)) % 1) - 1).astype(np.float32)
    b, a = butter(2, [band[0] / (SR / 2), band[1] / (SR / 2)], "band")
    y = lfilter(b, a, saw) * nasal + lfilter(*butter(1, 900 / (SR / 2)), saw) * 0.35
    env = np.clip(t / attack, 0, 1) * np.clip((dur - t) / 0.6, 0, 1)
    y = y * env
    return (y / (np.abs(y).max() + 1e-6)).astype(np.float32)


def flute(freq, dur=3.0, breath=0.12, vib=0.004, slide=0.0, rng=None, membrane=0.0, vib_rate=5.0):
    """부는 악기 한 음 (샤쿠하치·네이·반수리·리코더·대금·디즈). breath: 숨소리, slide: 아래에서 밀어 올리며 시작,
    membrane: 갈대청(대금·디즈)이 떨려 나는 지잉 소리"""
    from scipy.signal import butter, lfilter
    rng = rng or np.random.default_rng()
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = freq * (1 + vib * np.sin(2 * np.pi * vib_rate * t) * np.clip(t / 0.8, 0, 1)) * (1 - slide * np.exp(-t / 0.15))
    ph = np.cumsum(2 * np.pi * f / SR)
    y = np.sin(ph) + 0.25 * np.sin(2 * ph) + 0.08 * np.sin(3 * ph)
    if membrane:
        y = y + membrane * sum(np.sin(k * ph) / k for k in range(4, 12))
    noise = lfilter(*butter(2, [min(0.95, freq * 1.5 / (SR / 2)), min(0.98, freq * 4 / (SR / 2))], "band"), rng.standard_normal(n))
    y = y + breath * noise / (np.abs(noise).max() + 1e-6) * (1 + 2 * np.exp(-t / 0.12))
    env = np.clip(t / 0.18, 0, 1) * np.clip((dur - t) / 0.5, 0, 1)
    y = y * env
    return (y / (np.abs(y).max() + 1e-6)).astype(np.float32)


def reed(freq, dur=3.0, vib=0.006, vib_rate=5.5, band=(500, 3000), bright=0.25, slide=0.0, attack=0.12):
    """겹서 악기 한 음 (피리·주르나·셰나이·숌). bright: 펄스 폭(작을수록 날카롭고 콧소리)"""
    from scipy.signal import butter, lfilter
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = freq * (1 + vib * np.sin(2 * np.pi * vib_rate * t) * np.clip(t / 0.5, 0, 1)) * (1 - slide * np.exp(-t / 0.1))
    ph = np.cumsum(f / SR) % 1
    pulse = np.where(ph < bright, 1.0, -bright / (1 - bright)).astype(np.float32)
    b, a = butter(2, [band[0] / (SR / 2), band[1] / (SR / 2)], "band")
    y = lfilter(b, a, pulse) + 0.3 * lfilter(*butter(1, 1200 / (SR / 2)), pulse)
    env = np.clip(t / attack, 0, 1) * np.clip((dur - t) / 0.35, 0, 1)
    y = y * env
    return (y / (np.abs(y).max() + 1e-6)).astype(np.float32)


def drone(freqs, n, rng=None, kind="pluck"):
    """계속 울리는 바탕음. kind='pluck': 탄푸라처럼 줄을 차례로 뜯기를 되풀이, 'bowed': 허디거디처럼 길게, 'throat': 후미처럼 배음이 흐름"""
    rng = rng or np.random.default_rng()
    buf = np.zeros(n, np.float32)
    if kind == "pluck":
        t = 0.0
        while t < n / SR:
            for f in freqs:
                place_mono(buf, pluck(f, 3.5, damp=0.998, bright=0.35, buzz=0.35, rng=rng), t, 0.5)
                t += 0.9
    elif kind == "bowed":
        for f in freqs:
            seg = bowed(f, n / SR, band=(200, 1800), vib=0.0015, attack=1.5, nasal=0.5)
            buf[: len(seg)] += seg * 0.5
    else:   # throat: 낮은 기본음 + 천천히 움직이는 배음 띠
        from scipy.signal import butter, lfilter
        t = np.arange(n) / SR
        f0 = freqs[0]
        ph = 2 * np.pi * f0 * t
        y = sum(np.sin(k * ph) / k ** 0.6 for k in range(1, 18))
        y = y.astype(np.float32)
        out = lfilter(*butter(1, 500 / (SR / 2)), y) * 0.7
        for k0 in (6, 8, 9, 10, 12):          # 휘파람 같은 배음이 번갈아 떠오름
            g = np.clip(np.sin(2 * np.pi * (t / 9.0 + rng.random())) * 1.4 - 0.4, 0, 1)
            lo, hi = f0 * (k0 - 0.4), f0 * (k0 + 0.4)
            out += lfilter(*butter(2, [lo / (SR / 2), min(0.99, hi / (SR / 2))], "band"), y) * g * 2.5
        env = np.clip(t / 2.0, 0, 1) * np.clip((n / SR - t) / 2.0, 0, 1)
        buf += (out * env).astype(np.float32)
    return buf / (np.abs(buf).max() + 1e-6)


def frame_drum(dur=0.6, low=True, rng=None):
    """손으로 치는 틀북 한 번 (둥=low, 탁=high)"""
    from scipy.signal import butter, lfilter
    rng = rng or np.random.default_rng()
    n = int(dur * SR)
    t = np.arange(n) / SR
    if low:
        y = np.sin(2 * np.pi * (90 * np.exp(-t / 0.08) + 60) * t) * np.exp(-t / 0.18)
    else:
        y = lfilter(*butter(2, [900 / (SR / 2), 4000 / (SR / 2)], "band"), rng.standard_normal(n)) * np.exp(-t / 0.04)
    return (y / (np.abs(y).max() + 1e-6)).astype(np.float32)


def place_mono(buf, snd, t0, gain):
    i0 = int(t0 * SR)
    if i0 >= len(buf):
        return
    seg = snd[: len(buf) - i0] * gain
    buf[i0:i0 + len(seg)] += seg


def place(buf, snd, t0, gain, pan=0.0):
    i0 = int(t0 * SR)
    if i0 >= len(buf):
        return
    seg = snd[: len(buf) - i0] * gain
    buf[i0:i0 + len(seg), 0] += seg * (1 - max(0, pan))
    buf[i0:i0 + len(seg), 1] += seg * (1 + min(0, pan))


def reverb(x, rng, sec=2.2, wet=0.35):
    from scipy.signal import fftconvolve
    n = int(sec * SR)
    ir = rng.standard_normal((n, 2)).astype(np.float32) * np.exp(-np.arange(n) / (0.35 * SR))[:, None]
    ir[: int(0.02 * SR)] = 0
    out = np.stack([fftconvolve(x[:, c], ir[:, c])[: len(x)] for c in range(2)], 1)
    out /= np.abs(out).max() + 1e-6
    return (x * (1 - wet) + out * wet * np.abs(x).max()).astype(np.float32)


class Region:
    """한 권역의 악기 짝과 음계들. lead(f, dur, rng, last) = 뜯는 주 악기, sustain(f, dur, rng) = 길게 끄는 악기,
    modes = {이름: (음 간격, 으뜸음 MIDI, 느낌)}, drone_kind = None/'pluck'/'bowed'/'throat', drum = 틀북을 아주 작게"""

    def __init__(self, name, instruments, lead, sustain, modes, drone_kind=None, drum=False, gliss=True, tempo=0.42, bass=None, legato=False):
        """bass: 낮은 음을 맡는 악기(없으면 lead), legato: 관악처럼 음을 길게 이어 붙여 노래하듯 (가락 음 길이 늘림)"""
        self.name, self.instruments, self.lead, self.sustain = name, instruments, lead, sustain
        self.modes, self.drone_kind, self.drum, self.gliss, self.tempo = modes, drone_kind, drum, gliss, tempo
        self.bass, self.legato = bass or lead, legato

    def mode_of(self, mode):
        pen, root, _ = self.modes.get(str(mode or "").strip(), next(iter(self.modes.values())))
        return pen, root

    @staticmethod
    def notes(pen, root, lo, hi):
        return [o * 12 + p + root for o in range(-3, 5) for p in pen if lo <= o * 12 + p + root <= hi]

    def interlude(self, rng, sec=4.0, mode=None):
        pen, root = self.mode_of(mode)
        buf = np.zeros((int((sec + 2.5) * SR), 2), np.float32)
        t = 0.0
        if self.gliss:                                           # 위에서 아래로 훑기
            for m in reversed(self.notes(pen, root, root + 12, root + 36)[-7:]):
                place(buf, self.lead(hz(m), 1.6, rng, False), t, 0.30, pan=0.3)
                t += 0.055
            t += 0.35
        mel = self.notes(pen, root, root + 7, root + 24)
        k = int(rng.integers(2, max(3, len(mel) - 2)))
        steps = int(rng.integers(3, 6))
        for j in range(steps):
            k = int(np.clip(k + rng.choice([-2, -1, 1, 2]), 0, len(mel) - 1))
            last = j == steps - 1
            if last:
                k = mel.index(root + 12)                         # 끝음은 으뜸음
            dur_ = (3.0 if last else self.tempo * 1.25) if self.legato else (2.6 if last else 1.8)
            place(buf, self.lead(hz(mel[k]), dur_, rng, last), t, 0.7 if last else 0.55)
            t += self.tempo if not last else 0
        if self.drum:
            for i, low in enumerate([True, False, False, True]):
                place(buf, frame_drum(0.5, low, rng), 0.2 + i * 0.5, 0.12, pan=-0.2)
        return reverb(buf, rng)

    def bed(self, n, rng, mode=None):
        pen, root = self.mode_of(mode)
        buf = np.zeros((n, 2), np.float32)
        if self.drone_kind:
            d = drone([hz(root - 12 + 7), hz(root), hz(root), hz(root - 12)] if self.drone_kind == "pluck" else
                      [hz(root - 12), hz(root - 5)] if self.drone_kind == "bowed" else [hz(root - 12)], n, rng, self.drone_kind)
            buf[:, 0] += d * 0.22
            buf[:, 1] += d * 0.22
        low = self.notes(pen, root, root - 12, root) + [root - 12, root]
        mid = self.notes(pen, root, root + 7, root + 26)
        t = 0.5
        while t < n / SR - 2:
            place(buf, self.bass(hz(rng.choice(low)), 3.0, rng, False), t, 0.33, pan=-0.2)
            if self.legato:                                      # 관악: 2~3음짜리 짧은 가락을 이어서 노래하듯
                k = int(rng.integers(0, len(mid)))
                t2 = t + rng.uniform(0.6, 1.5)
                for _ in range(int(rng.integers(2, 4))):
                    k = int(np.clip(k + rng.choice([-1, 1, 2, -2]), 0, len(mid) - 1))
                    d_ = rng.uniform(0.9, 1.6)
                    place(buf, self.lead(hz(mid[k]), d_ + 0.3, rng, False), t2, 0.22, pan=0.2)
                    t2 += d_
            else:
                for _ in range(int(rng.integers(1, 4))):
                    place(buf, self.lead(hz(rng.choice(mid)), 2.0, rng, False), t + rng.uniform(0.6, 3.2), 0.26, pan=0.25)
            if rng.random() < 0.45:
                place(buf, self.sustain(hz(rng.choice(mid)), rng.uniform(3, 5), rng), t + rng.uniform(0.5, 2), 0.16, pan=-0.1)
            if self.drum and rng.random() < 0.35:
                place(buf, frame_drum(0.6, True, rng), t + 0.2, 0.06)
            t += rng.uniform(3.5, 5.5)
        return reverb(buf, rng, wet=0.4)

    def sample(self, mode, sec=30, seed=11):
        rng = np.random.default_rng(seed)
        it = self.interlude(rng, mode=mode)
        return np.concatenate([it, self.bed(int(max(5, sec - len(it) / SR) * SR), rng, mode)])


def write_wav(path, x):
    import wave
    x = np.clip(x / (np.abs(x).max() + 1e-6) * 0.8, -1, 1)
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((x * 32767).astype(np.int16).tobytes())
