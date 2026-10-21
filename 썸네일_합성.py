r"""썸네일 합성 모듈 - 관련 사진을 오려 내고 잘라 붙여 문구와 합친 썸네일 디자인 4가지

  1) 오려 붙이기(누끼 + 큰 글자): 사진 속 주인공만 오려 내 흰 테두리 스티커처럼 붙이고, 진한 색 배경 + 큰 글자
  2) 콜라주 3장(사선 분할): 관련 사진 3장을 사선으로 나눠 붙이고 아래에 큰 글자
  3) 원형 컷 2장: 흐린 배경 사진 위에 둥글게 오린 사진 2장 + 큰 글자
  4) 폴라로이드 콜라주: 사진 3장을 기울어진 폴라로이드처럼 겹쳐 놓고 큰 글자

  주인공 오려 내기는 rembg(MIT 라이선스, 무료·이 PC에서 실행)를 씀:  py -3.11 -m pip install rembg
  모델(약 170MB)은 처음 쓸 때 models\rembg 에 받음. rembg 가 없거나 잘 안 오려지면 흰 테두리 사진 카드로 대신함.
  글자 그리기·사진 자르기는 프로그램(shorts_novel_maker_supertonic.py)의 도구를 H 로 넘겨받아 같은 글꼴·색을 씀.
"""
import math
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageOps

HERE = os.path.dirname(os.path.abspath(__file__))
REMBG_DIR = os.path.join(HERE, "models", "rembg")
REMBG_MODEL = "isnet-general-use"
STYLES = ["오려 붙이기(누끼 + 큰 글자)", "콜라주 3장(사선 분할)", "원형 컷 2장", "폴라로이드 콜라주"]
_R = {"session": None, "tried": False, "error": "", "cache": {}}


def cutout(im):
    """사진 → 주인공만 남긴 RGBA (배경 투명). 못 하면 None"""
    if im is None:
        return None
    key = id(im)
    if key in _R["cache"]:
        return _R["cache"][key]
    res = None
    try:
        if not _R["tried"]:
            _R["tried"] = True
            os.makedirs(REMBG_DIR, exist_ok=True)
            os.environ.setdefault("U2NET_HOME", REMBG_DIR)
            from rembg import new_session
            _R["session"] = new_session(REMBG_MODEL)
        if _R["session"] is not None:
            from rembg import remove
            src = im.convert("RGB")
            src.thumbnail((1024, 1024), Image.LANCZOS)
            out = remove(src, session=_R["session"]).convert("RGBA")
            a = np.asarray(out.getchannel("A")) > 128
            cover = float(a.mean())
            if 0.04 < cover < 0.9:                    # 거의 다 지웠거나 거의 안 지웠으면 실패로 봄
                bbox = out.getchannel("A").point(lambda x: 255 if x > 128 else 0).getbbox()
                res = out.crop(bbox) if bbox else None
    except Exception as e:
        _R["error"] = (str(e).splitlines() or [type(e).__name__])[0][:120]
    _R["cache"][key] = res
    return res


def _sticker(rgba, border, color=(255, 255, 255, 255), shadow=True):
    """오린 그림에 흰 테두리 + 그림자 (스티커처럼)"""
    pad = border * 3
    big = Image.new("RGBA", (rgba.width + pad * 2, rgba.height + pad * 2), (0, 0, 0, 0))
    big.alpha_composite(rgba, (pad, pad))
    a = big.getchannel("A").point(lambda x: 255 if x > 100 else 0)
    ring = a.filter(ImageFilter.MaxFilter(border * 2 + 1)) if border * 2 + 1 <= 61 else a
    if border * 2 + 1 > 61:                        # 큰 테두리는 여러 번 넓힘
        for _ in range(max(1, border // 15)):
            ring = ring.filter(ImageFilter.MaxFilter(31))
    ring = ring.filter(ImageFilter.GaussianBlur(1.2))
    out = Image.new("RGBA", big.size, (0, 0, 0, 0))
    if shadow:
        sh = Image.new("RGBA", big.size, (0, 0, 0, 150))
        sh.putalpha(ring.filter(ImageFilter.GaussianBlur(border * 1.2)).point(lambda x: int(x * 0.6)))
        out.alpha_composite(sh, (border // 2, border))
    edge = Image.new("RGBA", big.size, color)
    edge.putalpha(ring)
    out.alpha_composite(edge)
    out.alpha_composite(big)
    return out


def _cover(im, w, h, cx=0.5, cy=0.42):
    """사진을 (w,h)에 꽉 차게 (가운데 조금 위 기준)"""
    im = im.convert("RGB")
    k = max(w / im.width, h / im.height)
    im = im.resize((max(w, int(im.width * k) + 1), max(h, int(im.height * k) + 1)), Image.LANCZOS)
    l = int(min(max(im.width * cx - w / 2, 0), im.width - w))
    t = int(min(max(im.height * cy - h / 2, 0), im.height - h))
    return im.crop((l, t, l + w, t + h))


def _bg_color(H, v, s, w, h, photo):
    """진한 분위기 색 배경 + 흐린 사진 살짝 + 가장자리 어둡게"""
    mood = H.vparts(v)[3]
    base = H.hex_rgb(H.moods.get(mood, ("#FFFFFF", "#FFD54F", "#1E88E5", "#FFFFFF"))[2])
    yy, xx = np.mgrid[0:h, 0:w]
    r = np.sqrt(((xx - w * 0.72) / w) ** 2 + ((yy - h * 0.45) / h) ** 2)
    k = np.clip(1.15 - r * 1.1, 0.35, 1.15)[..., None]
    arr = np.clip(np.array(base, np.float32)[None, None, :] * k, 0, 255)
    out = Image.fromarray(arr.astype(np.uint8)).convert("RGBA")
    d = ImageDraw.Draw(out)
    for i in range(-h, w, max(18, w // 40)):       # 비스듬한 줄무늬 (아주 옅게)
        d.line([(i, h), (i + h, 0)], fill=(255, 255, 255, 14), width=max(3, w // 300))
    if photo is not None:
        ph = _cover(photo, w, h).filter(ImageFilter.GaussianBlur(max(6, w // 90))).convert("RGBA")
        ph.putalpha(46)
        out.alpha_composite(ph)
    return out


def _text_block(H, out, v, s, fp, x, y_bottom, avail, size_frac, align="left", c_big="#FFFFFF", c_emph="#FFE135", stroke_col="#000000"):
    lines, emph, small, mood = H.vparts(v)
    w, h = out.size
    f_ = H.fit_font(fp, lines, avail, h * size_frac)
    lh = int(f_.size * 1.12)
    y0 = int(y_bottom - lh * len(lines))
    d = ImageDraw.Draw(out)
    H.lines(d, lines, emph, f_, x, y0, avail, c_big, c_emph, align, True, True, stroke_col)
    return y0


def render(style, v, s, photos, size, fp, H):
    """style: STYLES 중 하나. photos: 관련 사진(PIL) 목록 (첫 장 = 이 시안의 대표 사진). H: 프로그램의 그리기 도구"""
    w, h = size
    port = h > w
    photos = [p for p in (photos or []) if p is not None]
    lines, emph, small, mood = H.vparts(v)
    m = int(w * 0.045)
    accent = H.moods.get(mood, ("#FFFFFF", "#FFE135", "#E53935", "#FFFFFF"))
    emc = accent[1] if str(accent[1]).upper() != "#FFFFFF" else "#FFE135"     # 강조 단어 색 (흰 글자와 다르게)
    main = photos[0] if photos else None

    if style.startswith("오려"):
        out = _bg_color(H, v, s, w, h, main)
        cut = cutout(main)
        if cut is not None:
            th = int(h * (0.62 if port else 0.94))
            k = min(th / cut.height, (w * (0.9 if port else 0.58)) / cut.width)
            cut = cut.resize((max(1, int(cut.width * k)), max(1, int(cut.height * k))), Image.LANCZOS)
            st = _sticker(cut, max(6, w // 110))
        else:                                          # 오려 내기 실패 → 흰 테두리 사진 카드
            cw, ch = (int(w * 0.8), int(h * 0.5)) if port else (int(w * 0.5), int(h * 0.74))
            card = _cover(main, cw, ch) if main is not None else Image.new("RGB", (cw, ch), "#333")
            card = ImageOps.expand(card, border=max(8, w // 120), fill="white").convert("RGBA")
            st = _sticker(card.rotate(-4, expand=True, resample=Image.BICUBIC), 2, shadow=True)
        if port:
            out.alpha_composite(st, ((w - st.width) // 2, max(0, int(h * 0.06))))
            _text_block(H, out, v, s, fp, m, h * 0.9, w - 2 * m, 0.1, "center", "#FFFFFF", emc)
        else:
            out.alpha_composite(st, (w - st.width + int(w * 0.02), h - st.height + int(h * 0.04)))
            _text_block(H, out, v, s, fp, m, h * 0.84, int(w * 0.5), 0.17, "left", "#FFFFFF", emc)
        H.tag(out, small, fp, h * (0.042 if port else 0.065), m, int(h * 0.06), "#111111", "#FFFFFF", -2)
        return out.convert("RGB")

    if style.startswith("콜라주"):
        ps = (photos * 3)[:3] if photos else [None] * 3
        out = Image.new("RGBA", (w, h), (255, 255, 255, 255))
        n = len(ps)
        gap = max(6, w // 140)
        skew = int(w * 0.07) if not port else 0
        for i, p in enumerate(ps):
            if port:
                ph = _cover(p, w, h // n) if p is not None else Image.new("RGB", (w, h // n), "#222")
                out.paste(ph, (0, i * (h // n) + (gap if i else 0)))
                continue
            x0 = int(i * w / n) - skew
            x1 = int((i + 1) * w / n) + skew
            ph = _cover(p, x1 - x0, h) if p is not None else Image.new("RGB", (x1 - x0, h), "#222")
            mask = Image.new("L", (x1 - x0, h), 0)
            md = ImageDraw.Draw(mask)
            lft = 0 if i == 0 else skew + gap // 2
            rgt = (x1 - x0) if i == n - 1 else (x1 - x0) - skew - gap // 2
            md.polygon([(lft + skew if i else 0, 0), (rgt + skew if i < n - 1 else x1 - x0, 0),
                        (rgt - skew if i < n - 1 else x1 - x0, h), (lft - skew if i else 0, h)], fill=255)
            out.paste(ph, (x0, 0), mask)
        grad = np.zeros((h, w, 4), np.uint8)
        grad[..., 3] = (np.clip((np.linspace(0, 1, h) - 0.45) / 0.55, 0, 1) ** 1.3 * 225).astype(np.uint8)[:, None]
        out.alpha_composite(Image.fromarray(grad))
        _text_block(H, out, v, s, fp, m, h * 0.93, w - 2 * m, 0.1 if port else 0.17, "center", "#FFFFFF", emc)
        H.tag(out, small, fp, h * (0.042 if port else 0.065), m, int(h * 0.05), accent[2], "#FFFFFF", 0)
        return out.convert("RGB")

    if style.startswith("원형"):
        bgp = main
        out = (_cover(bgp, w, h).filter(ImageFilter.GaussianBlur(max(8, w // 70))) if bgp is not None
               else Image.new("RGB", (w, h), "#1A1A2E")).convert("RGBA")
        dark = Image.new("RGBA", (w, h), (8, 10, 20, 150))
        out.alpha_composite(dark)
        circ = (photos[1:3] if len(photos) >= 3 else (photos * 2)[:2]) or [None, None]
        spots = ([(0.5, 0.25, 0.25), (0.78, 0.5, 0.15)] if port else [(0.68, 0.46, 0.33), (0.9, 0.78, 0.18)])
        for (fx, fy, fr), p in zip(spots, circ):
            r = int(min(w, h) * fr) if port else int(h * fr)
            ph = _cover(p, r * 2, r * 2) if p is not None else Image.new("RGB", (r * 2, r * 2), "#444")
            mask = Image.new("L", (r * 2, r * 2), 0)
            ImageDraw.Draw(mask).ellipse([0, 0, r * 2 - 1, r * 2 - 1], fill=255)
            ring = max(6, r // 14)
            cx, cy = int(w * fx), int(h * fy)
            sh = Image.new("RGBA", (r * 2 + ring * 6, r * 2 + ring * 6), (0, 0, 0, 0))
            ImageDraw.Draw(sh).ellipse([ring * 2, ring * 3, r * 2 + ring * 4, r * 2 + ring * 5], fill=(0, 0, 0, 140))
            out.alpha_composite(sh.filter(ImageFilter.GaussianBlur(ring)), (cx - r - ring * 3, cy - r - ring * 3))
            ImageDraw.Draw(out).ellipse([cx - r - ring, cy - r - ring, cx + r + ring, cy + r + ring], fill=(255, 255, 255, 255))
            out.paste(ph, (cx - r, cy - r), mask)
        if port:
            _text_block(H, out, v, s, fp, m, h * 0.92, w - 2 * m, 0.1, "center", "#FFFFFF", emc)
        else:
            _text_block(H, out, v, s, fp, m, h * 0.82, int(w * 0.46), 0.17, "left", "#FFFFFF", emc)
        H.tag(out, small, fp, h * (0.042 if port else 0.065), m, int(h * 0.07), accent[2], "#FFFFFF", 0)
        return out.convert("RGB")

    # 폴라로이드 콜라주
    out = (_cover(main, w, h).filter(ImageFilter.GaussianBlur(max(10, w // 60))) if main is not None
           else Image.new("RGB", (w, h), "#2B2B2B")).convert("RGBA")
    out.alpha_composite(Image.new("RGBA", (w, h), (20, 16, 12, 165)))
    ps = (photos * 3)[:3] if photos else [None] * 3
    pw = int(w * (0.56 if port else 0.3))
    ph_ = int(pw * 0.82)
    spots = ([(0.08, 0.06, -7), (0.38, 0.2, 6), (0.12, 0.38, -2)] if port else [(0.04, 0.08, -8), (0.36, 0.04, 5), (0.66, 0.1, -4)])
    for (fx, fy, rot), p in zip(spots, ps):
        img = _cover(p, pw, ph_) if p is not None else Image.new("RGB", (pw, ph_), "#555")
        fr = max(10, pw // 22)
        card = Image.new("RGBA", (pw + fr * 2, ph_ + fr * 2 + fr * 3), (250, 248, 240, 255))
        card.paste(img, (fr, fr))
        card = card.rotate(rot, expand=True, resample=Image.BICUBIC)
        sh = Image.new("RGBA", card.size, (0, 0, 0, 0))
        sh.putalpha(card.getchannel("A").point(lambda x: int(x * 0.55)))
        out.alpha_composite(sh.filter(ImageFilter.GaussianBlur(fr)), (int(w * fx) + fr // 2, int(h * fy) + fr))
        out.alpha_composite(card, (int(w * fx), int(h * fy)))
    band_h = int(h * (0.3 if port else 0.36))
    grad = np.zeros((band_h, w, 4), np.uint8)
    grad[..., 3] = (np.linspace(0, 1, band_h) ** 0.8 * 235).astype(np.uint8)[:, None]
    out.alpha_composite(Image.fromarray(grad), (0, h - band_h))
    _text_block(H, out, v, s, fp, m, h * 0.94, w - 2 * m, 0.1 if port else 0.165, "center", "#FFFFFF", "#FFE135")
    H.tag(out, small, fp, h * (0.042 if port else 0.06), w - m - int(w * 0.25), int(h * 0.04), accent[2], "#FFFFFF", 3)
    return out.convert("RGB")
