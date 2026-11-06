"""막내 개그 만화 — 흑백 웹툰 컷이 움직이는 영상 (1화 '회식 메뉴' 기준, 대본·컷은 1화_회식메뉴.py)
python -X utf8 연재/막내개그/만화영상.py 녹음 <작업폴더>   → 줄마다 인물 목소리로 녹음 + 시간표.json + 목소리만.wav + 대본.txt(검사용)
python -X utf8 연재/막내개그/만화영상.py 영상 <작업폴더> <결과.mp4> [--배경음 <mp3>]
  - 해설 = 나레이션 성우(1화_회식메뉴.py 의 NARR), 따옴표 대사 = DIALOGUE 의 인물 목소리(VOICES)
  - 컷: Open Peeps(CC0) 인물을 흑백으로 + 코드로 그린 배경·소품·말풍선 (AI 그림 없음)
  - 움직임: 말하는 인물이 들썩, 말풍선이 그 대사 때 튀어나옴, 땀방울·반짝이·박수 효과, 컷마다 아주 느린 확대
  - 해설 글은 컷 왼쪽 위 네모 상자(웹툰 해설 칸), 대사는 말풍선"""
import importlib.util
import io
import json
import math
import os
import re
import subprocess
import sys
import urllib.parse
import urllib.request

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT)


def load(name, path):
    s = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(s)
    s.loader.exec_module(mod)
    return mod


EP = load("ep", os.path.join(HERE, "1화_회식메뉴.py"))
PEEP = load("peep", os.path.join(HERE, "오픈핍스_인물.py"))
LORE = load("lore", os.path.join(HERE, "로렐라이_인물.py"))     # 사용자 결정 2026-11-06: 인물은 Lorelei(CC0) 흑백 선화
STYLE = os.environ.get("MANHWA_STYLE", "lorelei")
NARR = {"code": "M2", "rate": 0, "semis": 0}
SR = 44100
W, H, FPS = 1920, 1080, 24
INK = 15
FONT = "/usr/share/fonts/truetype/nanum/NanumSquare_acEB.ttf"


# ── 대본 → 줄 목록 ──
def lines():
    who = {t: w for t, w in EP.DIALOGUE}
    out, panel = [], None
    for para in [p.strip() for p in EP.STORY.split("\n\n") if p.strip()]:
        m = re.fullmatch(r"\{(p\d+)\}", para)
        if m:
            panel = m.group(1)
            continue
        for part in re.findall(r'"[^"]+"|[^"]+', para):
            part = part.strip()
            if not part:
                continue
            if part.startswith('"'):
                t = part.strip('"')
                out.append({"panel": panel, "who": who.get(t, "해설"), "text": t})
            else:
                for s in re.split(r"(?<=[.?!])\s+", part):
                    if s.strip():
                        out.append({"panel": panel, "who": "해설", "text": s.strip()})
    return out


def record(work):
    import shorts_novel_maker_supertonic as m
    os.makedirs(work, exist_ok=True)
    env = dict(os.environ, PYTHONUTF8="1")
    py = os.path.join(ROOT, ".supertonic_venv", "bin", "python")
    w = subprocess.Popen([py, "-X", "utf8", "-u", os.path.join(ROOT, "supertonic_local_worker.py"), "--model-dir", os.path.join(ROOT, "supertonic_assets")],
                         stdin=subprocess.PIPE, stdout=subprocess.PIPE, encoding="utf-8", bufsize=1, env=env)
    json.loads(w.stdout.readline())
    L = lines()
    t, prev_panel, chunks = 1.6, None, []
    for i, ln in enumerate(L):
        v = NARR if ln["who"] == "해설" else EP.VOICES[ln["who"]]
        raw = os.path.join(work, f"{i:02d}_raw.wav")
        say = m.tts_clean(ln["text"]) if hasattr(m, "tts_clean") else ln["text"]
        w.stdin.write(json.dumps({"text": say, "voice": v["code"], "speed": max(.7, min(2.0, 1 + v["rate"] / 100)), "steps": 5,
                                  "lang": "ko", "out": os.path.abspath(raw)}, ensure_ascii=False) + "\n")
        r = json.loads(w.stdout.readline())
        if not r.get("ok"):
            raise SystemExit(f"녹음 실패 {i}: {r}")
        wav = os.path.join(work, f"{i:02d}.wav")
        k = 2 ** (v["semis"] / 12)
        sr0 = int(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=sample_rate", "-of", "csv=p=0", raw], capture_output=True, text=True).stdout.strip() or SR)
        af = (f"asetrate={int(sr0 * k)},aresample={sr0},atempo={1 / k:.6f}," if v["semis"] else "") + f"aresample={SR}"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", raw, "-af", af, "-ac", "1", wav], check=True)
        os.remove(raw)
        x = np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-i", wav, "-f", "s16le", "-ac", "1", "-ar", str(SR), "-"], capture_output=True).stdout, np.int16)
        if prev_panel is not None and ln["panel"] != prev_panel:
            t += 0.9                                    # 컷이 바뀔 때 숨
        ln.update(t0=round(t, 3), t1=round(t + len(x) / SR, 3), wav=wav)
        chunks.append((t, x))
        t = ln["t1"] + (0.45 if ln["who"] == "해설" else 0.35)
        prev_panel = ln["panel"]
    w.stdin.close()
    total = t + 1.8
    mix = np.zeros(int(total * SR), np.float32)
    for t0, x in chunks:
        i0 = int(t0 * SR)
        mix[i0:i0 + len(x)] += x.astype(np.float32) / 32768
    mix /= max(1e-6, np.abs(mix).max()) / 0.9
    import wave
    with wave.open(os.path.join(work, "목소리만.wav"), "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(SR)
        f.writeframes((mix * 32767).astype(np.int16).tobytes())
    json.dump({"duration": round(total, 3), "lines": L}, open(os.path.join(work, "시간표.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    open(os.path.join(work, "대본.txt"), "w", encoding="utf-8").write("\n\n".join(l["text"] for l in L) + "\n")
    print("녹음", len(L), "줄 ·", round(total, 1), "초")


# ── 그림 ──
_PEEPS = {}


def peep(name, face, size, talk=False, blink=False):
    k = (name, face, size, talk, blink)
    if k not in _PEEPS:
        raw = LORE.get(name, face, 512, talk=talk, blink=blink) if STYLE == "lorelei" else PEEP.get(name, face, 512)
        im = Image.open(io.BytesIO(raw)).convert("RGBA")
        if STYLE == "lorelei":                          # 빈 여백을 잘라 얼굴·목을 꽉 차게 → 높이 size 로
            bb = im.split()[3].getbbox()
            im = im.crop(bb)
            im = im.resize((max(1, int(im.width * size / im.height)), size), Image.LANCZOS)
        else:
            im = im.resize((size, size), Image.LANCZOS)
        a = np.asarray(im).astype(np.float32)
        lum = a[..., :3] @ np.array([0.299, 0.587, 0.114])
        g = np.where(lum < 110, INK, 255).astype(np.uint8)
        _PEEPS[k] = (Image.fromarray(g, "L"), Image.fromarray(a[..., 3].astype(np.uint8), "L"))
    return _PEEPS[k]


def body(d, name, x, y, size):
    """Lorelei 는 얼굴만 → 어깨·옷을 선으로 (목 아래). 부장님은 넥타이, 팀장님은 재킷 깃, 이대리는 셔츠 깃"""
    cx, top = x + size * 0.5, y + size * 0.86
    sw = size * 0.45
    pts = [(cx - size * 0.13, top), (cx - sw, top + size * 0.28), (cx - sw - size * 0.06, H + 20), (cx + sw + size * 0.06, H + 20),
           (cx + sw, top + size * 0.28), (cx + size * 0.13, top)]
    d.polygon(pts, fill=255)
    d.line(pts[:3], fill=INK, width=6)
    d.line(pts[3:], fill=INK, width=6)
    d.line([(cx - size * 0.13, top), (cx, top + size * 0.16), (cx + size * 0.13, top)], fill=INK, width=5)    # 깃
    if name == "부장님":
        d.polygon([(cx - 14, top + size * 0.16), (cx + 14, top + size * 0.16), (cx + 26, top + size * 0.62), (cx, top + size * 0.72), (cx - 26, top + size * 0.62)], fill=INK)
    elif name == "팀장님":
        for sgn in (-1, 1):
            d.line([(cx + sgn * size * 0.13, top), (cx + sgn * size * 0.30, top + size * 0.55)], fill=INK, width=5)
    elif name in ("이대리", "막내"):
        for k in range(3):
            d.ellipse((cx - 6, top + size * (0.25 + k * 0.14) - 6, cx + 6, top + size * (0.25 + k * 0.14) + 6), fill=INK)


def tone(size, step=10, r=1.6):
    t = Image.new("L", size, 255)
    d = ImageDraw.Draw(t)
    for y in range(0, size[1], step):
        for x in range((y // step % 2) * step // 2, size[0], step):
            d.ellipse((x - r, y - r, x + r, y + r), fill=INK)
    return t


def bg_office():
    c = Image.new("L", (W, H), 255)
    d = ImageDraw.Draw(c)
    win = (1180, 90, 1820, 470)
    c.paste(tone((win[2] - win[0], win[3] - win[1]), 11, 1.4), win[:2])
    d.rectangle(win, outline=INK, width=6)
    d.line([((win[0] + win[2]) // 2, win[1]), ((win[0] + win[2]) // 2, win[3])], fill=INK, width=5)
    d.line([(win[0], (win[1] + win[3]) // 2), (win[2], (win[1] + win[3]) // 2)], fill=INK, width=5)
    d.line([(0, 640), (W, 640)], fill=INK, width=4)
    d.rectangle((120, 700, 1800, 760), fill=255, outline=INK, width=6)
    for x in (160, 1760):
        d.line([(x, 760), (x, 1080)], fill=INK, width=6)
    for mx in (330, 1450):
        d.rectangle((mx - 150, 470, mx + 150, 660), fill=255, outline=INK, width=6)
        d.rectangle((mx - 128, 492, mx + 128, 638), outline=INK, width=3)
        d.rectangle((mx - 20, 660, mx + 20, 700), fill=INK)
    for i in range(4):                                              # 서류 더미·화분
        d.rectangle((900 + i * 4, 660 - i * 14, 1060 - i * 4, 674 - i * 14), fill=255, outline=INK, width=3)
    d.rectangle((1640, 600, 1700, 700), fill=255, outline=INK, width=5)
    for a in (-0.9, -0.4, 0.1, 0.6):
        d.ellipse((1670 + 70 * math.sin(a) - 22, 540 - 40 * math.cos(a) - 34, 1670 + 70 * math.sin(a) + 22, 540 - 40 * math.cos(a) + 34), fill=255, outline=INK, width=4)
    return c


def bg_soup():
    c = Image.new("L", (W, H), 255)
    d = ImageDraw.Draw(c)
    c.paste(tone((W, 640), 12, 1.3), (0, 0))                         # 저녁 식당 (망점 벽)
    d.line([(0, 640), (W, 640)], fill=INK, width=5)
    for x in range(100, W, 360):                                     # 메뉴판
        d.rectangle((x, 90, x + 240, 200), fill=255, outline=INK, width=5)
        d.text((x + 120, 145), "순댓국", font=ImageFont.truetype(FONT, 46), fill=INK, anchor="mm")
    d.rectangle((60, 760, 1860, 820), fill=255, outline=INK, width=6)
    for bx in (760, 1160):                                           # 순댓국 두 그릇
        d.chord((bx - 150, 640, bx + 150, 800), 0, 180, fill=255, outline=INK, width=6)
        d.line([(bx - 150, 720), (bx + 150, 720)], fill=INK, width=6)
        for s in (-60, 0, 60):
            d.arc((bx + s - 20, 560, bx + s + 20, 700), 100, 260, fill=INK, width=4)
    return c


BG = {}


def food(d, kind, cx, cy, s=1.0):
    if kind == "초밥":
        d.rounded_rectangle((cx - 90 * s, cy, cx + 90 * s, cy + 60 * s), 30 * s, fill=255, outline=INK, width=6)
        d.polygon([(cx - 100 * s, cy + 10 * s), (cx - 70 * s, cy - 40 * s), (cx + 100 * s, cy - 30 * s), (cx + 90 * s, cy + 15 * s)], fill=200, outline=INK)
        for k in range(4):
            d.line([(cx - 50 * s + k * 35 * s, cy - 30 * s), (cx - 30 * s + k * 35 * s, cy + 10 * s)], fill=INK, width=4)
    elif kind == "파스타":
        d.ellipse((cx - 120 * s, cy - 30 * s, cx + 120 * s, cy + 60 * s), fill=255, outline=INK, width=6)
        for k in range(6):
            d.arc((cx - 80 * s + k * 18 * s, cy - 40 * s, cx + 20 * s + k * 18 * s, cy + 40 * s), 200, 340, fill=INK, width=4)
    elif kind == "고기":
        d.ellipse((cx - 110 * s, cy - 60 * s, cx + 80 * s, cy + 60 * s), fill=210, outline=INK, width=6)
        d.line([(cx + 60 * s, cy), (cx + 150 * s, cy)], fill=INK, width=int(18 * s))
        d.ellipse((cx + 140 * s, cy - 22 * s, cx + 180 * s, cy + 22 * s), fill=255, outline=INK, width=5)
    elif kind == "순댓국":
        d.chord((cx - 110 * s, cy - 50 * s, cx + 110 * s, cy + 70 * s), 0, 180, fill=255, outline=INK, width=6)
        d.line([(cx - 110 * s, cy + 10 * s), (cx + 110 * s, cy + 10 * s)], fill=INK, width=6)
        for k in (-40, 0, 40):
            d.arc((cx + k * s - 15 * s, cy - 110 * s, cx + k * s + 15 * s, cy - 10 * s), 100, 260, fill=INK, width=4)


def bubble(d, box, text, tail, font, pop=1.0):
    x0, y0, x1, y1 = box
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    hw, hh = (x1 - x0) / 2 * pop, (y1 - y0) / 2 * pop
    tx, ty = tail
    ang = math.atan2(ty - cy, tx - cx)
    bx, by = cx + hw * 0.85 * math.cos(ang), cy + hh * 0.85 * math.sin(ang)
    p = [(bx + 26 * math.cos(ang + 1.57), by + 26 * math.sin(ang + 1.57)), (cx + (tx - cx) * pop, cy + (ty - cy) * pop), (bx + 26 * math.cos(ang - 1.57), by + 26 * math.sin(ang - 1.57))]
    d.ellipse((cx - hw, cy - hh, cx + hw, cy + hh), fill=255, outline=INK, width=6)
    d.polygon(p, fill=255)
    d.line([p[0], p[1], p[2]], fill=INK, width=6)
    if pop > 0.85:
        rows = wrap(text, 11)
        lh = font.size * 1.25
        for i, ln in enumerate(rows):
            d.text((cx, cy + (i - (len(rows) - 1) / 2) * lh), ln, font=font, fill=INK, anchor="mm")


def wrap(text, n):
    words, rows, cur = text.split(), [], ""
    for wd in words:
        if cur and len(cur) + len(wd) + 1 > n:
            rows.append(cur)
            cur = wd
        else:
            cur = (cur + " " + wd).strip()
    rows.append(cur)
    return rows


SLOTS = {1: {"가운데": 640}, 2: {"왼": 230, "오른": 1100, "가운데": 640}, 3: {"왼": 60, "가운데": 680, "오른": 1300}}


def panel_frame(pid, tl, lines_here, t):
    pdef = {p[0]: p for p in EP.PANELS}[pid]
    _, bgname, who, prop, cap = pdef
    if bgname not in BG:
        BG[bgname] = bg_soup() if "순댓국" in bgname else bg_office()
    c = BG[bgname].copy()
    d = ImageDraw.Draw(c)
    n = len(who)
    size = 640 if n < 3 else 560
    speaking = [l for l in lines_here if l["t0"] <= t <= l["t1"]]
    cur_who = speaking[0]["who"] if speaking else None
    pos = {}
    CEN = {1: {"가운데": 960}, 2: {"왼": 560, "오른": 1360, "가운데": 960}, 3: {"왼": 380, "가운데": 960, "오른": 1540}}
    hgt = {1: 720, 2: 640, 3: 540}[n]
    for ni, (name, face, slot) in enumerate(who):
        talk = blink = False
        bounce = 0
        if name == cur_who:
            bounce = int(8 * abs(math.sin((t - speaking[0]["t0"]) * 9)))      # 말할 때 들썩
            talk = int((t - speaking[0]["t0"]) / 0.13) % 2 == 1                # 입 열고 닫기
        blink = (t + ni * 1.37) % 3.3 < 0.12                                    # 3초쯤마다 깜빡
        if STYLE == "lorelei":
            g, a = peep(name, face, hgt, talk=talk, blink=blink)
            x = CEN[n].get(slot, 960) - g.width // 2
            y = H - hgt + 10 - bounce                                           # 목이 화면 아래에 닿게 (몸은 그리지 않음)
        else:
            g, a = peep(name, face, size)
            x, y = SLOTS[n].get(slot, 640), H - size + 40 - bounce
        if slot == "오른":
            g, a = g.transpose(Image.FLIP_LEFT_RIGHT), a.transpose(Image.FLIP_LEFT_RIGHT)
        c.paste(g, (x, y), a)
        pos[name] = (x + g.width // 2, y + int(g.height * 0.05))
    # 소품·효과
    for kind in ("초밥", "파스타", "고기", "순댓국"):
        if kind in prop:
            food(d, kind, 960, 420 + 8 * math.sin(t * 3), 1.0)
    if "박수" in prop:
        for k in range(6):
            a_ = t * 6 + k
            if int(a_) % 2 == 0:
                x0, y0 = 300 + k * 260, 560 + 30 * (k % 2)
                for j in range(3):
                    r = math.radians(-60 + j * 60)
                    d.line([(x0 + 20 * math.cos(r), y0 - 20 * math.sin(r)), (x0 + 55 * math.cos(r), y0 - 55 * math.sin(r))], fill=INK, width=5)
    if "반짝이" in prop:
        for k in range(8):
            x0, y0 = 520 + (k * 173) % 900, 180 + (k * 97) % 360
            s = 18 + 14 * math.sin(t * 5 + k)
            d.line([(x0 - s, y0), (x0 + s, y0)], fill=INK, width=4)
            d.line([(x0, y0 - s), (x0, y0 + s)], fill=INK, width=4)
    if "땀방울" in prop:
        for k in range(3):
            yy = 300 + ((t * 120 + k * 70) % 260)
            xx = 1000 + k * 40
            d.ellipse((xx - 14, yy - 22, xx + 14, yy + 22), fill=255, outline=INK, width=5)
    if "생각 풍선" in prop:
        bubble(d, (520, 40, 1400, 300), "제가 언제 순댓국이라고 했죠?", (420, 520), ImageFont.truetype(FONT, 50))
        for k, (bx, by, r) in enumerate(((470, 380, 26), (440, 450, 18))):
            d.ellipse((bx - r, by - r, bx + r, by + r), fill=255, outline=INK, width=5)
    # 말풍선 (대사 때) · 해설 칸
    fnt = ImageFont.truetype(FONT, 52)
    for l in lines_here:
        if l["who"] != "해설" and l["t0"] - 0.15 <= t <= l["t1"] + 0.5 and l["who"] in pos:
            hx, hy = pos[l["who"]]
            left = hx < 960
            box = (60, 60, 840, 340) if left else (1080, 60, 1860, 340)
            pop = min(1.0, (t - l["t0"] + 0.15) / 0.18)
            bubble(d, box, l["text"], (hx, hy), fnt, pop=0.7 + 0.3 * pop)
    narr = [l for l in lines_here if l["who"] == "해설" and l["t0"] - 0.1 <= t <= l["t1"] + 0.3
            and not ("생각 풍선" in prop and "순댓국이라고" in l["text"])]      # 생각 풍선에 이미 쓴 말은 해설 칸에 또 쓰지 않음
    if narr:
        f2 = ImageFont.truetype(FONT, 46)
        rows = wrap(narr[0]["text"], 26)
        bw = max(d.textlength(r, font=f2) for r in rows) + 70
        bh = len(rows) * 62 + 40
        d.rectangle((40, 40, 40 + bw, 40 + bh), fill=255, outline=INK, width=6)
        for i, r in enumerate(rows):
            d.text((75, 60 + i * 62), r, font=f2, fill=INK)
    d.rectangle((0, 0, W - 1, H - 1), outline=INK, width=14)
    z = 1 + 0.03 * tl                                          # 컷 안에서 아주 느린 확대
    cw, ch = int(W / z), int(H / z)
    return c.crop(((W - cw) // 2, (H - ch) // 2, (W - cw) // 2 + cw, (H - ch) // 2 + ch)).resize((W, H), Image.BILINEAR)


def video(work, out, bgm=None):
    tt = json.load(open(os.path.join(work, "시간표.json"), encoding="utf-8"))
    L, total = tt["lines"], tt["duration"]
    order = []
    for l in L:
        if l["panel"] not in order:
            order.append(l["panel"])
    span = {}
    for i, pid in enumerate(order):
        here = [l for l in L if l["panel"] == pid]
        t0 = 0 if i == 0 else here[0]["t0"] - 0.45
        t1 = total if i == len(order) - 1 else [l for l in L if l["panel"] == order[i + 1]][0]["t0"] - 0.45
        span[pid] = (t0, t1, here)
    tmp = os.path.join(work, "_영상만.mp4")
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "gray", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p", tmp], stdin=subprocess.PIPE)
    title_font = ImageFont.truetype(FONT, 110)
    for fi in range(int(total * FPS)):
        t = fi / FPS
        pid = next(k for k in order if span[k][0] <= t < span[k][1] or k == order[-1])
        t0, t1, here = span[pid]
        im = panel_frame(pid, (t - t0) / max(0.1, t1 - t0), here, t)
        if t < 1.4:                                            # 제목 카드
            im = Image.new("L", (W, H), 255)
            d = ImageDraw.Draw(im)
            d.text((W / 2, H / 2 - 40), EP.TITLE.replace(" - ", "\n"), font=title_font, fill=INK, anchor="mm", align="center")
            d.rectangle((0, 0, W - 1, H - 1), outline=INK, width=14)
        p.stdin.write(im.tobytes())
    p.stdin.close()
    p.wait()
    voice = os.path.join(work, "목소리만.wav")
    if bgm:
        af = "[1:a]aresample=44100,volume=0.12,aloop=loop=-1:size=2e9[m];[2:a]aresample=44100[v];[v][m]amix=inputs=2:duration=first:normalize=0[a]"
        cmd = ["ffmpeg", "-v", "error", "-y", "-i", tmp, "-stream_loop", "-1", "-i", bgm, "-i", voice, "-filter_complex",
               "[1:a]aresample=44100,volume=0.12[m];[2:a]aresample=44100[v];[v][m]amix=inputs=2:duration=first:normalize=0[a]",
               "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out]
    else:
        cmd = ["ffmpeg", "-v", "error", "-y", "-i", tmp, "-i", voice, "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
               "-shortest", "-movflags", "+faststart", out]
    subprocess.run(cmd, check=True)
    print("OK", out, round(total, 1), "초")


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[0] == "녹음":
        record(a[1])
    else:
        video(a[1], a[2], a[a.index("--배경음") + 1] if "--배경음" in a else None)
