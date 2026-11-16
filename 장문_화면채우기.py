"""장문 다큐: 사진이 오래 머무는 곳을 채움 — ① 정보 카드(숫자·연표·비교, 직접 그림) ② 앞 사진의 다른 부분 확대(변경 금지 ND 사진은 자르지 않음)
사용: python 장문_화면채우기.py <프로젝트.json> <카드규칙.json> [나레이션 길이(초)] [--간격 9]
  - 카드규칙.json: [{"re": "413", "title": "출토 유물", "big": "413건", "note": "…"}, {"re": "1997년", "timeline": [["1997","…"], …], "title": "…"},
                    {"re": "나트론", "compare": [["지중해(로마) 유리","나트론 · 소다가 많음"], ["중국 유리","납 · 바륨이 많음"]], "title": "…"},
                    {"re": "…", "list": ["…","…"], "title": "…"}]  — 대본 문단에 re 가 처음 나오는 곳에 한 번씩
  - 문단 시간은 나레이션 길이(영상 길이)를 글자 수로 나눠 어림. 화면이 '간격'초 넘게 그대로면 그 문단 앞에 카드나 확대 사진을 넣음
  - 처음 것은 <프로젝트>_화면채우기전.json 으로 남김.  (사용자 결정 2026-11-16: 흉노 편 사진이 한 장에 30초씩 머물러 지루함)"""
import json, os, re, sys, shutil
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
FONT_B = os.path.join(HERE, "fonts", "BlackHanSans-Regular.ttf")
FONT_G = os.path.join(HERE, "fonts", "NanumGothic-ExtraBold.ttf")
W, H = 1920, 1080
BG1, BG2, ACC, FG, SUB = (16, 22, 38), (34, 44, 70), (255, 196, 86), (245, 245, 240), (175, 185, 205)
MEDIA_RE = re.compile(r"^\[사진:\s*(.*)\]\s*$")


def F(p, s): return ImageFont.truetype(p, s)


def base_img():
    im = Image.new("RGB", (W, H), BG1); d = ImageDraw.Draw(im)
    for y in range(H):   # 위→아래 그라데이션
        t = y / H; d.line([(0, y), (W, y)], fill=tuple(int(BG1[i] * (1 - t) + BG2[i] * t) for i in range(3)))
    d.rectangle([120, 150, 132, 250], fill=ACC)   # 왼쪽 강조 막대
    return im, d


def center(d, y, text, font, fill):
    w = d.textlength(text, font=font); d.text(((W - w) / 2, y), text, font=font, fill=fill)


def card_big(c):
    im, d = base_img()
    d.text((160, 150), c["title"], font=F(FONT_G, 64), fill=SUB)
    big = c["big"]; s = 260
    while d.textlength(big, font=F(FONT_B, s)) > W - 300: s -= 10
    center(d, 380, big, F(FONT_B, s), ACC)
    if c.get("note"): center(d, 380 + s + 60, c["note"], F(FONT_G, 50), FG)
    return im


def card_timeline(c):
    im, d = base_img()
    d.text((160, 150), c["title"], font=F(FONT_G, 64), fill=SUB)
    items = c["timeline"]; n = len(items); x0, x1, y = 220, W - 220, 600
    d.line([(x0, y), (x1, y)], fill=SUB, width=6)
    for i, (yr, txt) in enumerate(items):
        x = x0 + (x1 - x0) * i / max(1, n - 1)
        d.ellipse([x - 22, y - 22, x + 22, y + 22], fill=ACC)
        fy = F(FONT_B, 64); w = d.textlength(yr, font=fy); d.text((x - w / 2, y - 130), yr, font=fy, fill=ACC)
        for k, part in enumerate(txt.split("\n")):
            ft = F(FONT_G, 40); w = d.textlength(part, font=ft); d.text((x - w / 2, y + 60 + k * 52), part, font=ft, fill=FG)
    return im


def card_compare(c):
    im, d = base_img()
    d.text((160, 150), c["title"], font=F(FONT_G, 64), fill=SUB)
    (a1, a2), (b1, b2) = c["compare"]
    for i, (h, t) in enumerate(((a1, a2), (b1, b2))):
        x = 200 + i * 800
        d.rounded_rectangle([x, 330, x + 720, 830], radius=30, fill=(28, 38, 62), outline=ACC if i == 0 else SUB, width=5)
        fh = F(FONT_B, 76); w = d.textlength(h, font=fh); d.text((x + 360 - w / 2, 420), h, font=fh, fill=ACC if i == 0 else FG)
        for k, part in enumerate(t.split("\n")):
            ft = F(FONT_G, 50); w = d.textlength(part, font=ft); d.text((x + 360 - w / 2, 580 + k * 70), part, font=ft, fill=FG)
    if c.get("note"): center(d, 900, c["note"], F(FONT_G, 42), SUB)
    return im


def card_list(c):
    im, d = base_img()
    d.text((160, 150), c["title"], font=F(FONT_G, 64), fill=SUB)
    for i, t in enumerate(c["list"]):
        y = 340 + i * 170
        d.ellipse([220, y, 320, y + 100], fill=ACC); fn = F(FONT_B, 64); n = str(i + 1)
        d.text((270 - d.textlength(n, font=fn) / 2, y + 10), n, font=fn, fill=BG1)
        d.text((380, y + 12), t, font=F(FONT_B, 72), fill=FG)
    return im


def make_card(c, path):
    im = (card_timeline if "timeline" in c else card_compare if "compare" in c else card_list if "list" in c else card_big)(c)
    im.save(path, quality=94); return path


def can_crop(credit):
    c = credit.upper()
    return not ("ND" in c.replace("UND", "") or "변경금지" in credit or "변경 금지" in credit)


def crops(src, out_base, k):
    """앞 사진의 다른 부분 2곳(왼쪽 위·오른쪽 아래)을 16:9 로 확대. 작은 사진은 안 함"""
    im = Image.open(src).convert("RGB")
    if im.width < 900: return []
    cw = int(im.width * 0.62); ch = int(cw * 9 / 16)
    if ch > im.height: ch = int(im.height * 0.9); cw = int(ch * 16 / 9)
    boxes = [(0, 0), (im.width - cw, im.height - ch), (im.width - cw, 0), (0, im.height - ch)]
    x, y = boxes[k % 4]
    p = f"{out_base}_부분{k + 1}.jpg"
    im.crop((x, y, x + cw, y + ch)).resize((W, int(W * ch / cw)), Image.LANCZOS).save(p, quality=92)
    return p


def main():
    a = sys.argv[1:]; gap = 9.0
    if "--간격" in a: i = a.index("--간격"); gap = float(a[i + 1]); del a[i:i + 2]
    proj, rules_p = a[0], a[1]
    pj = json.load(open(proj, encoding="utf-8")); rules = json.load(open(rules_p, encoding="utf-8"))
    bak = proj.replace("_프로젝트.json", "_화면채우기전.json")
    if not os.path.exists(bak): shutil.copy(proj, bak)
    story = pj["story"]; paras = [p for p in story.split("\n\n") if p.strip()]
    media_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(proj))), "media")
    os.makedirs(media_dir, exist_ok=True)
    text_chars = sum(len(re.sub(r"\s", "", p)) for p in paras if not p.startswith("[사진") and not p.startswith("## "))
    dur = float(a[2]) if len(a) > 2 else 0     # 나레이션 길이(초), 주면 더 정확
    cps = text_chars / (dur or text_chars / 7.0)       # 1초당 글자 (영상 길이를 주면 그것으로)
    out, used, t, last_t, crop_n, n_card, n_crop = [], set(), 0.0, 0.0, {}, 0, 0
    group, croppable = 1, []          # croppable: 잘라도 되는(ND 아님) 최근 사진들

    def pick(p):
        """이 문단에 넣을 것 하나: 문단에 맞는 정보 카드 → 잘라도 되는 가까운 사진의 다른 부분"""
        nonlocal n_card, n_crop
        for r_ in rules:
            if r_["re"] not in used and re.search(r_["re"], p):
                used.add(r_["re"]); n_card += 1
                path = make_card(r_, os.path.join(media_dir, f"card_{len(used):02d}.jpg"))
                return f"[사진: {path} | {r_['title']} | 직접 제작(정보 카드)]"
        for ph in reversed(croppable[-3:]):
            k = crop_n.get(ph[0], 0)
            if k >= 2:      # 한 사진은 최대 2곳만 (같은 사진 확대가 연달아 나오면 지루함)
                continue
            src = ph[0] if os.path.isabs(ph[0]) else os.path.join(HERE, ph[0])
            cp = crops(src, os.path.join(media_dir, os.path.splitext(os.path.basename(src))[0]), k) if os.path.exists(src) else []
            if cp:
                crop_n[ph[0]] = k + 1; n_crop += 1
                return f"[사진: {cp} | {ph[1]} (부분) | {ph[2]} | {ph[3]}]".replace(" | ]", "]")
        return None
    for p in paras:
        if MEDIA_RE.match(p):
            parts = [x.strip() for x in MEDIA_RE.match(p).group(1).split("|")] + ["", "", ""]
            group = group + 1 if out and MEDIA_RE.match(out[-1]) else 1
            if group == 1: last_t = t
            if can_crop(parts[2]) and "정보 카드" not in parts[2]: croppable.append(parts)
            out.append(p); continue
        if p.startswith("## "):
            out.append(p); continue
        dp = len(re.sub(r"\s", "", p)) / cps
        if (t + dp - last_t) / group > gap * 1.35:      # 이 문단이 끝날 때까지 화면 한 장이 너무 오래 → 문단 앞에 몇 장 (시간을 나눠 차례로 보임)
            need = max(1, int(dp // gap))
            ins = [x for x in (pick(p) for _ in range(need)) if x]
            if ins:
                out.extend(ins); last_t, group = t, len(ins)
        out.append(p); t += dp
    pj["story"] = "\n\n".join(out)
    json.dump(pj, open(proj, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"정보 카드 {n_card}장 · 부분 확대 {n_crop}장 넣음 (화면이 {gap:.0f}초 넘게 그대로인 곳) · 1초당 {cps:.1f}자 · 처음 것: {bak}")


if __name__ == "__main__":
    main()
