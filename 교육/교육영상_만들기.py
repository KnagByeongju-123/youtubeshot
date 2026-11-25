"""교육 영상 합성 (전체 화면 슬라이드 + 확대·축소 + 형광펜·밑줄 + O·X 도장 + 아나운서 + 한 줄 자막 + 나레이션·피아노)
   사용자 결정 2026-11-25 (사내 성희롱 예방교육): 아나운서는 자주 움직이고, 내용은 전체 화면을 써서 말하는 카드로 확대·축소,
   핵심 낱말은 형광펜 색칠 + 밑줄, 나레이션 립싱크(아나운서 장면은 애니3D/장면_교육아나운서.html 로 따로 찍음)
   사용: python 교육/교육영상_만들기.py <내용.json> <프로젝트_시간.json> <결과.mp4>
           [--아나운서 <투명 png 폴더>] [--나레이션 <나레이션만.mp3>] [--배경음 <피아노.wav>] [--배경음크기 0.2]
           [--그림 <장면 그림 폴더: s00.png, s01.png …>] [--크기 1280x720] [--시험 0,30,60 (그 초의 장면만 png 로)] [--동작 <결과 동작.json> (아나운서 동작표만 만들고 끝)]
   - 내용.json 의 문단 순서 = 시간.json 의 문단(kind 가 chapter 가 아닌 것) 순서
   - 그림(--그림): 장면이 시작될 때 2.6초 동안 그 장면 그림이 화면 가득(천천히 확대, 위에 장면 제목) → 0.7초 동안 제목 옆 작은 창으로 줄어듦
   - 장(챕터)이 바뀔 때마다 아나운서 자리가 오른쪽 ↔ 왼쪽 (왼쪽일 때는 좌우를 뒤집어 늘 내용 쪽을 가리킴)"""
import json
import os
import re
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps

a = sys.argv[1:]
spec = json.load(open(a[0], encoding="utf-8")); tim = json.load(open(a[1], encoding="utf-8")); out = a[2]
def opt(k, d=None): return a[a.index(k) + 1] if k in a else d
W, H = (int(v) for v in opt("--크기", "1280x720").split("x")); K = 2; WW, HH = W * K, H * K   # 2배로 그려 확대해도 또렷하게
FPS = 24
FB = "/usr/share/fonts/truetype/nanum/NanumBarunGothicBold.ttf"; FR = "/usr/share/fonts/truetype/nanum/NanumBarunGothic.ttf"
font = lambda p, s: ImageFont.truetype(p, int(s * K * H / 720))
S = lambda v: int(v * K * H / 720)
NAVY, NAVY2, INK, SUB = (22, 38, 74), (40, 64, 120), (30, 34, 46), (96, 104, 124)
ACC, MARK, LINE = (236, 120, 40), (255, 222, 70, 150), (226, 58, 74)

# ── 시간표: 문단마다 [시작, 끝, 장면 번호, 문단 번호] ──
segs = [s for s in tim["segs"]]
paras = [s for s in segs if s["kind"] != "chapter" and not s["text"].startswith("## ")]
chap_segs = [s for s in segs if s["kind"] == "chapter" or s["text"].startswith("## ")]
items = [(si, pi) for si, sc in enumerate(spec["장면"]) for pi in range(len(sc["문단"]))]
if len(items) != len(paras):
    sys.exit(f"문단 수가 다름: 내용 {len(items)} / 시간 {len(paras)}  (kind 들: {sorted(set(s['kind'] for s in segs))})")
P = []
for (si, pi), sg in zip(items, paras):
    P.append({"t0": sg["t0"], "t1": sg["t0"] + sg["dur"], "si": si, "pi": pi, "text": sg["text"]})
DUR = tim["duration"]
scene_t0 = {}
for p in P: scene_t0.setdefault(p["si"], p["t0"])
scene_t0[0] = 0.0          # 첫 장면은 영상 처음부터 (나레이션 전 제목 시간 포함)
side_of = {}; flip = False; prev_ch = None
for si, sc in enumerate(spec["장면"]):
    ch = sc.get("장", -1)
    if ch != prev_ch and prev_ch is not None: flip = not flip
    prev_ch = ch; side_of[si] = "R" if flip else "L"     # L = 내용 왼쪽·아나운서 오른쪽

# ── 아나운서 동작표 (--동작): 강조가 있는 문단 = 가리키기, '동작' 칸이 있으면 그것, 나머지는 손짓을 번갈아 → 자주 움직임 ──
if "--동작" in a:
    acts = []; cyc = ["open", "nod", "one", "open"]; c = 0
    for p in P:
        pa = spec["장면"][p["si"]]["문단"][p["pi"]]; d = p["t1"] - p["t0"]
        if pa.get("동작"):
            acts.append([p["t0"] + 0.1, p["t0"] + min(d, 3.2), pa["동작"]])
        elif "강조" in pa:
            acts.append([p["t0"] + 0.25, p["t0"] + min(d, 2.8), "point"])
            if d > 5.5: acts.append([p["t0"] + 3.6, p["t0"] + min(d - 0.3, 6.2), cyc[c % 4]]); c += 1
        else:
            acts.append([p["t0"] + 0.3, p["t0"] + min(d, 3.4), cyc[c % 4]]); c += 1
    json.dump({"acts": acts, "duration": DUR, "sides": [[scene_t0.get(si, 0), side_of[si]] for si in range(len(spec["장면"]))]},
              open(opt("--동작"), "w", encoding="utf-8"), ensure_ascii=False)
    print("동작표:", opt("--동작"), len(acts), "개"); sys.exit()


def wrap(text, f, maxw, d):
    if d.textlength(text, font=f) <= maxw: return [text]
    words = text.split(" "); lines, cur = [], ""
    for w_ in words:
        t = (cur + " " + w_).strip()
        if d.textlength(t, font=f) <= maxw or not cur: cur = t
        else: lines.append(cur); cur = w_
    lines.append(cur); return lines


def background(chx):
    im = Image.new("RGB", (WW, HH)); g = np.linspace(0, 1, HH)[:, None]
    c1, c2 = np.array([246, 248, 252]), np.array([226, 233, 245])
    arr = (c1 * (1 - g) + c2 * g)[:, None, :].repeat(WW, 1).astype(np.uint8)
    im = Image.fromarray(arr.reshape(HH, WW, 3)); d = ImageDraw.Draw(im, "RGBA")
    for k in range(5):        # 옅은 사선 띠 (밋밋하지 않게)
        x0 = int(WW * (0.55 + 0.11 * k)); d.polygon([(x0, 0), (x0 + S(60), 0), (x0 - S(260), HH), (x0 - S(320), HH)], fill=(255, 255, 255, 60))
    # 위 띠: 회사·교육 이름 + 장 단계
    d.rectangle([0, 0, WW, S(64)], fill=NAVY)
    d.text((S(28), S(18)), f"{spec.get('회사', '')}  |  {spec['제목']}", font=font(FB, 22), fill=(255, 255, 255))
    steps = spec["장"]; n = len(steps); x1 = WW - S(24); w_step = S(118)
    for i in range(n - 1, -1, -1):
        on = i == chx; done = chx >= 0 and i < chx
        bx = x1 - (n - i) * w_step
        col = ACC if on else ((92, 120, 180) if done else (58, 78, 128))
        d.rounded_rectangle([bx + S(4), S(14), bx + w_step - S(4), S(50)], radius=S(16), fill=col)
        f = font(FB if on else FR, 15); lab = f"{i + 1} {steps[i]}"; tw = d.textlength(lab, font=f)
        d.text((bx + (w_step - tw) / 2, S(22)), lab, font=f, fill=(255, 255, 255))
    return im


IMG_DIR = opt("--그림")
_imgs = {}
def scene_img(si):
    if not IMG_DIR: return None
    if si not in _imgs:
        f = os.path.join(IMG_DIR, f"s{si:02d}.png"); _imgs[si] = Image.open(f).convert("RGB") if os.path.exists(f) else None
    return _imgs[si]


def build_scene(si):
    """장면 바탕(2배 크기) + 카드 자리 + 강조 낱말 자리"""
    sc = spec["장면"][si]; side = side_of[si]; ch = sc.get("장", -1)
    im = background(ch); d = ImageDraw.Draw(im, "RGBA")
    cw = int(WW * 0.62); cx0 = S(70) if side == "L" else WW - cw - S(70)
    info = {"side": side, "cards": [], "words": {}, "content": (cx0, cx0 + cw), "thumb": None}
    img = scene_img(si)
    tw_ = cw
    if img is not None and ch >= 0:          # 제목 옆(내용 칸 오른쪽 위)에 16:9 작은 그림 창
        th_h = S(150); th_w = int(th_h * 16 / 9); info["thumb"] = (cx0 + cw - th_w, S(84), cx0 + cw, S(84) + th_h); tw_ = cw - th_w - S(24)
    if ch < 0:          # 시작·마무리: 가운데 큰 제목
        f = font(FB, 60 if img is None else 50); tl = wrap(sc["제목"], f, cw if img is None else cw - S(360), d); y = S(210)
        for ln in tl: d.text((cx0, y), ln, font=f, fill=NAVY); y += S(78)
        if sc.get("부제"): d.text((cx0, y + S(10)), sc["부제"], font=font(FR, 28), fill=SUB); y += S(60)
        d.rectangle([cx0, y + S(24), cx0 + S(120), y + S(32)], fill=ACC); y += S(70)
        top = y
        if img is not None:            # 시작·마무리: 제목 오른쪽 위에 그림 창
            th_h = S(190); th_w = int(th_h * 16 / 9); info["thumb"] = (cx0 + cw - th_w, S(100), cx0 + cw, S(100) + th_h)
    else:
        d.text((cx0, S(96)), f"{ch + 1}. {spec['장'][ch]}", font=font(FB, 22), fill=ACC)
        f = font(FB, 46 if tw_ == cw else 40); tl = wrap(sc["제목"], f, tw_, d); y = S(128)
        for ln in tl: d.text((cx0, y), ln, font=f, fill=NAVY); y += S(60)
        d.rectangle([cx0, y + S(8), cx0 + S(90), y + S(14)], fill=ACC); top = max(y + S(40), (info["thumb"][3] + S(22)) if info["thumb"] else 0)
    cards = sc["카드"]; n = len(cards)
    avail = HH - S(110) - top; gap = S(16)
    fs = 30 if n <= 3 else (27 if n == 4 else 24)
    ch_h = min(S(96), (avail - gap * (n - 1)) // n)
    for k, txt in enumerate(cards):
        f = font(FB, fs); lines = wrap(txt, f, cw - S(70), d)
        while len(lines) > 2 and fs > 18: fs -= 2; f = font(FB, fs); lines = wrap(txt, f, cw - S(70), d)
        y0 = top + k * (ch_h + gap); y1 = y0 + ch_h
        info["cards"].append((cx0, y0, cx0 + cw, y1, txt, lines, fs))
        # 단어 자리 (형광펜·밑줄용): 카드 글에서 강조 낱말을 찾아 줄·x 범위
        lh = int(f.size * 1.25); ty = y0 + (ch_h - lh * len(lines)) // 2
        for li, ln in enumerate(lines):
            for pa in sc["문단"]:
                if "강조" in pa and pa["강조"][0] == k and pa["강조"][1] in ln:
                    w_ = pa["강조"][1]; i0 = ln.index(w_)
                    x_a = cx0 + S(36) + d.textlength(ln[:i0], font=f); x_b = x_a + d.textlength(w_, font=f)
                    info["words"][(k, w_)] = (x_a, ty + li * lh, x_b, ty + li * lh + lh)
    info["font_sizes"] = fs
    return im, info


def draw_cards(im, info, t, ts, marks, active, stamps):
    """카드를 차례로 나타나게(장면 시작 뒤 0.15초씩), 확대 중인 카드는 주황 테두리, 형광펜·밑줄·O·X 도장"""
    lay = Image.new("RGBA", im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    for k, (x0, y0, x1, y1, txt, lines, fs) in enumerate(info["cards"]):
        ap = min(1, max(0, (t - ts - 0.35 - 0.18 * k) / 0.35))
        if ap <= 0: continue
        dy = int((1 - ap) * S(24)); al = int(255 * ap)
        d.rounded_rectangle([x0 + S(4), y0 + S(6) + dy, x1 + S(4), y1 + S(6) + dy], radius=S(16), fill=(20, 30, 60, int(28 * ap)))
        d.rounded_rectangle([x0, y0 + dy, x1, y1 + dy], radius=S(16), fill=(255, 255, 255, al),
                            outline=(ACC + (al,)) if k == active else None, width=S(4))
        d.rounded_rectangle([x0, y0 + dy, x0 + S(12), y1 + dy], radius=S(5), fill=((ACC if k == active else NAVY2) + (al,)))
        f = font(FB, fs); lh = int(f.size * 1.25); ty = y0 + (y1 - y0 - lh * len(lines)) // 2 + dy
        # 형광펜(글자 뒤에 먼저)
        for (kk, w_), prog in marks.items():
            if kk != k or (kk, w_) not in info["words"]: continue
            xa, ya, xb, yb = info["words"][(kk, w_)]
            xe = xa + (xb - xa + S(12)) * min(1, prog / 0.5)
            if xe > xa: d.rounded_rectangle([xa - S(6), ya + dy + S(4), xe - S(6), yb + dy - S(2)], radius=S(6), fill=MARK[:3] + (int(MARK[3] * ap),))
        for li, ln in enumerate(lines):
            d.text((x0 + S(36), ty + li * lh), ln, font=f, fill=INK + (al,))
        for (kk, w_), prog in marks.items():     # 밑줄(형광펜 뒤에 그어짐)
            if kk != k or (kk, w_) not in info["words"] or prog < 0.45: continue
            xa, ya, xb, yb = info["words"][(kk, w_)]
            xe = xa + (xb - xa) * min(1, (prog - 0.45) / 0.4)
            d.line([(xa, yb + dy - S(1)), (xe, yb + dy - S(1))], fill=LINE + (al,), width=S(5))
        if k in stamps:          # O·X 도장
            kind, prog = stamps[k]; sc_ = 1.6 - 0.6 * min(1, prog / 0.25); r = int(S(34) * sc_)
            cx, cy = x1 - S(70), (y0 + y1) // 2 + dy
            col = (40, 110, 220) if kind == "O" else (220, 50, 60)
            if kind == "O": d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=col + (230,), width=S(9))
            else:
                d.line([(cx - r, cy - r), (cx + r, cy + r)], fill=col + (230,), width=S(10)); d.line([(cx - r, cy + r), (cx + r, cy - r)], fill=col + (230,), width=S(10))
    im.alpha_composite(lay)


ease = lambda x: (lambda y: y * y * (3 - 2 * y))(min(1, max(0, x)))
SUBF = ImageFont.truetype(FB, int(30 * H / 720))
subs = []
for p in P:
    parts = [x.strip() for x in re.split(r"(?<=[.?!])\s+|(?<=,)\s+", p["text"]) if x.strip()]
    tot = sum(len(x) for x in parts); t = p["t0"]
    for x in parts:
        dd = (p["t1"] - p["t0"]) * len(x) / tot; subs.append((t, t + dd, x.rstrip(","))); t += dd

cache = {}
def frame(t):
    cur = max([p for p in P if p["t0"] <= t + 1e-6] or [P[0]], key=lambda p: p["t0"])
    si = cur["si"]; sc = spec["장면"][si]
    if si not in cache: cache.clear(); cache[si] = build_scene(si)
    base, info = cache[si]
    im = base.convert("RGBA"); ts = scene_t0[si]
    # 이 장면에서 지금까지 시작된 문단들의 형광펜 진행, 확대 카드, O·X
    marks, stamps, active, zoom = {}, {}, None, None
    for p in P:
        if p["si"] != si or p["t0"] > t: continue
        pa = sc["문단"][p["pi"]]
        if "강조" in pa: marks[tuple(pa["강조"])] = t - (p["t0"] + 0.35)
        if pa.get("확대") is not None and "확대" in pa: zoom = (pa["확대"], p["t0"])
        elif "확대" in pa: zoom = (None, p["t0"])
        m = re.search(r"답은 (오|엑스)", pa["말"])
        if m and "강조" in pa:
            ti = p["t0"] + (p["t1"] - p["t0"]) * m.end() / len(pa["말"])
            if t >= ti: stamps[pa["강조"][0]] = ("O" if m.group(1) == "오" else "X", t - ti)
        if zoom and zoom[0] is not None and p["t0"] == zoom[1]: active = zoom[0]
    if zoom and zoom[0] is not None and zoom[0] < len(info["cards"]): active = zoom[0]
    else: active = None
    img = scene_img(si); HERO, SHR = 2.6, 0.7
    if img is not None and info["thumb"] and t - ts >= HERO + SHR:      # 제목 옆 작은 그림 창 (그림자 + 둥근 모서리)
        x0, y0, x1, y1 = info["thumb"]; th = img.resize((x1 - x0, y1 - y0), Image.LANCZOS)
        mk = Image.new("L", th.size, 0); ImageDraw.Draw(mk).rounded_rectangle([0, 0, th.width - 1, th.height - 1], radius=S(14), fill=255)
        shl = Image.new("RGBA", im.size, (0, 0, 0, 0)); ImageDraw.Draw(shl).rounded_rectangle([x0 + S(5), y0 + S(7), x1 + S(5), y1 + S(7)], radius=S(14), fill=(20, 30, 60, 45))
        im.alpha_composite(shl)
        im.paste(th, (x0, y0), mk)
    draw_cards(im, info, t, ts, {k: v for k, v in marks.items() if v > 0}, active, stamps)
    # 확대·축소: 카드 확대 중이면 그 카드를 내용 칸 가운데로 1.35배
    def cam_for(z):
        if z is None or z >= len(info["cards"]): return (1.0, WW / 2, HH / 2)
        x0, y0, x1, y1 = info["cards"][z][:4]; s = 1.18
        cwid = WW / s; chei = HH / s
        # 카드 글이 잘리지 않게: 아나운서가 오른쪽이면 카드 왼쪽 끝을, 왼쪽이면 카드 오른쪽 끝을 화면 가장자리 조금 안쪽에 맞춤
        left = x0 - S(40) if info["side"] == "L" else x1 + S(40) - cwid
        top = (y0 + y1) / 2 - 0.52 * chei
        left = min(max(left, 0), WW - cwid); top = min(max(top, 0), HH - chei)
        return (s, left + cwid / 2, top + chei / 2)
    zs = [p for p in P if p["si"] == si and p["t0"] <= t and "확대" in sc["문단"][p["pi"]]]
    if zs:
        last = zs[-1]; prevz = zs[-2] if len(zs) > 1 else None
        A = cam_for(sc["문단"][prevz["pi"]].get("확대") if prevz else None); B = cam_for(sc["문단"][last["pi"]].get("확대"))
        k_ = ease((t - last["t0"]) / 0.8); cam = tuple(A[i] + (B[i] - A[i]) * k_ for i in range(3))
    else: cam = (1.0, WW / 2, HH / 2)
    s, cx, cy = cam; cw_, chh = WW / s, HH / s
    box = (int(cx - cw_ / 2), int(cy - chh / 2), int(cx + cw_ / 2), int(cy + chh / 2))
    fr = im.crop(box).resize((W, H), Image.LANCZOS if s > 1.01 else Image.BILINEAR)
    # 장면 시작: 그림이 화면 가득(천천히 확대) → 제목 옆 창으로 줄어듦. 위에 장 번호·장면 제목
    if img is not None and t - ts < HERO + SHR:
        u = t - ts; z = 1.0 + 0.06 * min(u, HERO) / HERO
        big = img.resize((int(W * z), int(H * z)), Image.BILINEAR).crop((int(W * (z - 1) / 2), int(H * (z - 1) / 2), int(W * (z - 1) / 2) + W, int(H * (z - 1) / 2) + H))
        if u < HERO:
            hero = big.convert("RGBA"); d2 = ImageDraw.Draw(hero, "RGBA")
            d2.rectangle([0, H - int(H * 0.30), W, H], fill=(10, 16, 34, 150))
            ch_ = sc.get("장", -1); y_ = H - int(H * 0.27)
            if ch_ >= 0: d2.text((int(W * 0.05), y_), f"{ch_ + 1}. {spec['장'][ch_]}", font=ImageFont.truetype(FB, int(24 * H / 720)), fill=(255, 190, 120)); y_ += int(36 * H / 720)
            d2.text((int(W * 0.05), y_), sc["제목"], font=ImageFont.truetype(FB, int(44 * H / 720)), fill=(255, 255, 255))
            fa = ease(u / 0.35)            # 처음 0.35초 부드럽게 나타남
            fr = Image.blend(fr.convert("RGBA"), hero, fa)
        else:                      # 줄어들기: 화면 가득 → 제목 옆 창 자리
            k2 = ease((u - HERO) / SHR)
            tb = info["thumb"] or (WW // 2 - S(200), S(200), WW // 2 + S(200), S(425))
            tx0, ty0, tx1, ty1 = [v / K for v in tb]
            x0_ = int(0 + (tx0 - 0) * k2); y0_ = int(0 + (ty0 - 0) * k2); x1_ = int(W + (tx1 - W) * k2); y1_ = int(H + (ty1 - H) * k2)
            if x1_ - x0_ > 4 and y1_ - y0_ > 4:
                fr.paste(big.resize((x1_ - x0_, y1_ - y0_), Image.BILINEAR), (x0_, y0_))
    # 위 띠는 확대해도 그대로 (장 단계가 늘 보이게)
    bar = im.crop((0, 0, WW, S(64))).resize((W, S(64) // K), Image.BILINEAR); fr.paste(bar, (0, 0))
    # 장면이 바뀔 때 0.4초 부드럽게 (앞 장면이 옅어짐)
    # 아나운서
    if opt("--아나운서"):
        fi = int(t * FPS); fi -= fi % 2
        fp = os.path.join(opt("--아나운서"), f"f{fi:04d}.png")
        if not os.path.exists(fp):
            c_ = sorted(f for f in os.listdir(opt("--아나운서")) if f.endswith(".png") and int(f[1:5]) <= fi)
            fp = os.path.join(opt("--아나운서"), c_[-1]) if c_ else None
        if fp:
            an = Image.open(fp).convert("RGBA"); sc_h = H / an.height * 0.98
            an = an.resize((int(an.width * sc_h), int(an.height * sc_h)), Image.BILINEAR)
            side = info["side"]
            # 자리 바꿈: 장면 시작 0.6초 동안 옆에서 미끄러져 들어옴
            xr = W - an.width + int(W * 0.02); xl = -int(W * 0.02)
            if side == "R": an = ImageOps.mirror(an)
            x = xr if side == "L" else xl
            k_ = ease((t - ts) / 0.6); prev_side = side_of.get(si - 1, side)
            if prev_side != side and si > 0:
                x = int((W if side == "L" else -an.width) + (x - (W if side == "L" else -an.width)) * k_)
            fr.paste(an, (x, H - an.height), an)
    # 자막 한 줄
    sub = next((x for x in subs if x[0] <= t < x[1]), None)
    if sub:
        d = ImageDraw.Draw(fr, "RGBA"); tw = d.textlength(sub[2], font=SUBF); y = H - int(70 * H / 720)
        d.rounded_rectangle([(W - tw) / 2 - 22, y - 10, (W + tw) / 2 + 22, y + SUBF.size + 14], radius=10, fill=(16, 20, 32, 190))
        d.text(((W - tw) / 2, y), sub[2], font=SUBF, fill=(255, 255, 255))
    return fr.convert("RGB")


if "--시험" in a:
    for ts_ in opt("--시험").split(","):
        frame(float(ts_)).save(out.replace(".mp4", f"_시험_{float(ts_):06.1f}.png")); print("시험", ts_)
    sys.exit()

nfr = int(DUR * FPS)
tmpv = out[:-4] + "_영상만.mp4"
pp = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                       "-c:v", "libx264", "-preset", "medium", "-crf", "21", "-pix_fmt", "yuv420p", tmpv], stdin=subprocess.PIPE)
for i in range(nfr):
    pp.stdin.write(frame(i / FPS).tobytes())
    if i % (FPS * 30) == 0: print(f"  {i / FPS:.0f}/{DUR:.0f}초", flush=True)
pp.stdin.close(); pp.wait()
# 소리: 나레이션 + 피아노(말할 때 살짝 낮춤)
cmd = ["ffmpeg", "-loglevel", "error", "-y", "-i", tmpv]
if opt("--나레이션"): cmd += ["-i", opt("--나레이션")]
if opt("--배경음"): cmd += ["-i", opt("--배경음")]
if opt("--나레이션") and opt("--배경음"):
    v = float(opt("--배경음크기", "0.2"))
    cmd += ["-filter_complex", f"[2:a]volume={v}[bg];[bg][1:a]sidechaincompress=threshold=0.03:ratio=3:attack=30:release=500[dk];[1:a][dk]amix=inputs=2:normalize=0:duration=first[aout]",
            "-map", "0:v", "-map", "[aout]"]
elif opt("--나레이션"): cmd += ["-map", "0:v", "-map", "1:a"]
cmd += ["-c:v", "libx264", "-preset", "medium", "-b:v", "2500k", "-maxrate", "3000k", "-bufsize", "5000k", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", "-shortest", out]
subprocess.run(cmd, check=True); os.remove(tmpv)
print("완성:", out)
