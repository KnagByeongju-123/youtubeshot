"""
실사 편집 레이아웃 (Pillow, 무료·로컬)

A. 피사체 중심형: 핵심 피사체를 크게 오른쪽에, 같은 사진을 흐리게·어둡게 처리한 배경 위에 배치
B. 좌우 비교형:   서로 다른 두 사진을 나란히 (실제 비교 대상이 두 장 있을 때만)
C. 증거 확대형:   사진 전체(맥락) + 핵심 부분을 원형 확대창으로, 원본 위치를 사각형과 연결선으로 표시

공통 편집: EXIF 회전 보정 → 자동 명암(autocontrast) → 색감·선명도 보정 → 초점 영역 검출(가장자리 밀도 기반, ML 없음)
→ 구도에 맞춘 크롭 → 글자 영역 어둡게 → 비네팅. 모든 크롭/확대 좌표를 원본 픽셀 기준으로 메타데이터에 남깁니다.

사진 속 증거(모양·숫자·문자)는 변형하지 않습니다. 보정은 전체 명암·색감·선명도뿐이고 내용은 그대로입니다.
선택: rembg(MIT) 가 설치되어 있으면 A 형에서 피사체 배경 제거를 시도합니다 (첫 실행 시 모델 다운로드, 미설치면 건너뜀).
"""

import os

SIZE = (1280, 720)
ACCENT = (255, 214, 0, 255)


def _pil():
    from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance, ImageOps
    return Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance, ImageOps


# ------------------------------------------------------------------ 사진 준비

def load_photo(path, max_side=2400):
    Image, _, _, _, _, ImageOps = _pil()
    img = ImageOps.exif_transpose(Image.open(path)).convert("RGB")
    w, h = img.size
    if max(w, h) > max_side:
        s = max_side / max(w, h)
        img = img.resize((int(w * s), int(h * s)), Image.LANCZOS)
    return img


def enhance(img):
    """전체 명암·색감·선명도 보정 (내용 변형 없음). 반환: (이미지, 적용 내역)"""
    _, _, _, _, ImageEnhance, ImageOps = _pil()
    out = ImageOps.autocontrast(img, cutoff=1)
    out = ImageEnhance.Color(out).enhance(1.12)
    out = ImageEnhance.Contrast(out).enhance(1.06)
    out = ImageEnhance.Sharpness(out).enhance(1.25)
    return out, ["autocontrast(cutoff=1)", "color×1.12", "contrast×1.06", "sharpness×1.25"]


def focal_box(img, frac_w=0.5, aspect=None, grid=48):
    """초점(피사체) 영역 추정: 가장자리 밀도 + 중앙 가중치가 가장 높은 창. ML 없이 동작.
    frac_w: 창 너비 비율, aspect: 창 가로/세로 비 (None 이면 사진 비율). 반환: 원본 좌표 (x0, y0, x1, y1)"""
    Image, _, _, ImageFilter, _, _ = _pil()
    w, h = img.size
    small = img.convert("L").resize((grid, max(8, int(grid * h / w))), Image.BILINEAR)
    edges = small.filter(ImageFilter.FIND_EDGES)
    gw, gh = edges.size
    px = edges.load()
    # 중앙 가중치 (가장자리로 갈수록 0.4 까지 감소)
    energy = [[px[x, y] * (1 - 0.6 * max(abs(x / (gw - 1) - 0.5), abs(y / (gh - 1) - 0.5)) * 2) for x in range(gw)] for y in range(gh)]
    # 적분 영상
    integ = [[0] * (gw + 1) for _ in range(gh + 1)]
    for y in range(gh):
        row = 0
        for x in range(gw):
            row += energy[y][x]
            integ[y + 1][x + 1] = integ[y][x + 1] + row
    aspect = aspect or (w / h)
    cw = max(2, min(gw, int(gw * frac_w)))
    # 창 높이(그리드 칸): 원본 픽셀 기준 너비 cw*(w/gw) 를 aspect 로 나눈 높이를 그리드 칸으로 환산
    ch = max(2, min(gh, int((cw * w / gw) / aspect * gh / h)))
    if ch >= gh:  # 세로가 꽉 차면 가로를 그에 맞게 줄임
        cw = max(2, min(gw, int((gh * h / gh) * aspect * gw / w)))
    best, bx, by = -1, 0, 0
    for y in range(0, gh - ch + 1):
        for x in range(0, gw - cw + 1):
            s = integ[y + ch][x + cw] - integ[y][x + cw] - integ[y + ch][x] + integ[y][x]
            if s > best:
                best, bx, by = s, x, y
    x0, y0 = int(bx * w / gw), int(by * h / gh)
    x1, y1 = int((bx + cw) * w / gw), int((by + ch) * h / gh)
    return (x0, y0, min(w, x1), min(h, y1))


def cover_params(src_size, dst_size, focus=None):
    """cover 크롭 파라미터 (scale, left, top). focus(원본 좌표 중심)가 있으면 그쪽으로 창을 옮김."""
    w, h = src_size
    s = max(dst_size[0] / w, dst_size[1] / h)
    sw, sh = w * s, h * s
    if focus:
        cx, cy = focus[0] * s, focus[1] * s
        left = min(max(0, cx - dst_size[0] / 2), sw - dst_size[0])
        top = min(max(0, cy - dst_size[1] / 2), sh - dst_size[1])
    else:
        left, top = (sw - dst_size[0]) / 2, (sh - dst_size[1]) / 2
    return s, left, top


def cover_crop(img, dst_size, focus=None):
    """원본을 dst 크기로 꽉 채워 크롭. 반환: (이미지, 원본 좌표 크롭 박스)"""
    Image = _pil()[0]
    s, left, top = cover_params(img.size, dst_size, focus)
    box = (int(left / s), int(top / s), int((left + dst_size[0]) / s), int((top + dst_size[1]) / s))
    return img.crop(box).resize(dst_size, Image.LANCZOS), box


def to_thumb_coords(box, crop_box, dst_size):
    """원본 좌표 box 를 cover_crop 결과(dst) 좌표로 변환."""
    cx0, cy0, cx1, cy1 = crop_box
    sx, sy = dst_size[0] / max(1, cx1 - cx0), dst_size[1] / max(1, cy1 - cy0)
    return (int((box[0] - cx0) * sx), int((box[1] - cy0) * sy), int((box[2] - cx0) * sx), int((box[3] - cy0) * sy))


def subject_cutout(img):
    """rembg 가 설치되어 있을 때만 배경 제거 (RGBA). 없거나 실패하면 None."""
    try:
        from rembg import remove  # noqa
    except Exception:
        return None
    try:
        return remove(img).convert("RGBA")
    except Exception:
        return None


# ------------------------------------------------------------------ 공통 그리기

def _font(path, size):
    return _pil()[2].truetype(path, size)


def darken_gradient(base, y_from_ratio=0.3, max_alpha=215, x_to=None):
    """아래쪽(또는 지정 영역) 어둡게 — 글자 대비용."""
    Image, ImageDraw = _pil()[0], _pil()[1]
    ov = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    H = base.size[1]
    y_start = int(H * y_from_ratio)
    span = max(1, H - y_start)
    for y in range(y_start, H):
        a = int(max_alpha * ((y - y_start) / span) ** 1.3)
        d.line([(0, y), (x_to or base.size[0], y)], fill=(0, 0, 0, min(255, a)))
    return Image.alpha_composite(base.convert("RGBA"), ov)


def vignette(base):
    Image, ImageDraw, _, ImageFilter, _, _ = _pil()
    m = Image.new("L", base.size, 0)
    ImageDraw.Draw(m).ellipse([-200, -160, base.size[0] + 200, base.size[1] + 220], fill=255)
    m = m.filter(ImageFilter.GaussianBlur(160))
    dark = Image.new("RGBA", base.size, (0, 0, 0, 0))
    dark.putalpha(Image.eval(m, lambda v: int((255 - v) * 0.55)))
    return Image.alpha_composite(base.convert("RGBA"), dark)


def draw_copy(base, text, font_path, x0, x1, y_bottom, max_h, start=104):
    """문구 블록: 강조 바 + 그림자 + 외곽선. 마지막 줄 노란색. 반환: (base, overflow)"""
    import thumbs
    Image, ImageDraw, ImageFont, ImageFilter, _, _ = _pil()
    draw = ImageDraw.Draw(base)
    font, lines, over = thumbs.fit_text(draw, text, font_path, x1 - x0 - 36, max_h, start=start, ImageFont=ImageFont)
    lh = int(font.size * 1.18)
    y0 = y_bottom - lh * len(lines)
    sh = Image.new("RGBA", base.size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(sh)
    y = y0
    for line in lines:
        sd.text((x0 + 24 + 6, y + 8), line, font=font, fill=(0, 0, 0, 200), stroke_width=max(4, font.size // 10), stroke_fill=(0, 0, 0, 200))
        y += lh
    base = Image.alpha_composite(base, sh.filter(ImageFilter.GaussianBlur(10)))
    draw = ImageDraw.Draw(base)
    draw.rounded_rectangle([x0, y0 + 6, x0 + 12, y0 + lh * len(lines) - 10], radius=6, fill=ACCENT)
    stroke = max(4, font.size // 11)
    y = y0
    for i, line in enumerate(lines):
        fill = ACCENT if (i == len(lines) - 1 and len(lines) > 1) else (255, 255, 255, 255)
        draw.text((x0 + 24, y), line, font=font, fill=fill, stroke_width=stroke, stroke_fill=(10, 10, 10, 255))
        y += lh
    return base, over


def draw_badge(base, status, font_path):
    import thumbs
    ImageDraw = _pil()[1]
    label, color = thumbs.STATUS_BADGE.get(status, thumbs.STATUS_BADGE["확인 필요"])
    d = ImageDraw.Draw(base)
    f = _font(font_path, 34)
    bw = int(d.textlength(label, font=f)) + 44
    d.rounded_rectangle([52, 46, 52 + bw, 46 + 62], radius=16, fill=color + (240,), outline=(255, 255, 255, 90), width=2)
    d.text((74, 55), label, font=f, fill=(255, 255, 255, 255))
    return base


def draw_label(base, text, font_path, x, y, size=30):
    ImageDraw = _pil()[1]
    d = ImageDraw.Draw(base)
    f = _font(font_path, size)
    w = int(d.textlength(text, font=f)) + 28
    d.rounded_rectangle([x, y, x + w, y + size + 22], radius=10, fill=(0, 0, 0, 170))
    d.text((x + 14, y + 9), text, font=f, fill=(255, 255, 255, 255))
    return base


def rounded(img, radius):
    Image, ImageDraw = _pil()[0], _pil()[1]
    m = Image.new("L", img.size, 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, img.size[0] - 1, img.size[1] - 1], radius=radius, fill=255)
    out = img.convert("RGBA")
    out.putalpha(m)
    return out


def _save(base, out_path):
    rgb = base.convert("RGB")
    rgb.save(out_path, "JPEG", quality=92, subsampling=0)
    if os.path.getsize(out_path) > 2 * 1024 * 1024:
        rgb.save(out_path, "JPEG", quality=80)


# ------------------------------------------------------------------ 레이아웃 A: 피사체 중심형

def layout_subject(photo_path, text, font_path, status, out_path, side="right", frac=0.55):
    Image, _, _, ImageFilter, ImageEnhance, _ = _pil()
    photo = load_photo(photo_path)
    photo, edits = enhance(photo)
    meta = {"layout": "A 피사체 중심형", "source_image": photo_path, "source_size": photo.size, "edits": list(edits)}

    bg, bg_box = cover_crop(photo, SIZE)
    bg = ImageEnhance.Brightness(bg.filter(ImageFilter.GaussianBlur(16))).enhance(0.45)
    base = bg.convert("RGBA")
    meta["background"] = {"crop_box": bg_box, "blur": 16, "brightness": 0.45}

    panel = (600, 620)
    fb = focal_box(photo, frac_w=frac, aspect=panel[0] / panel[1])
    cut = subject_cutout(photo.crop(fb))
    if cut is not None:
        cut.thumbnail(panel, Image.LANCZOS)
        subj = cut
        meta["subject"] = {"crop_box": fb, "background_removed": "rembg", "size": subj.size}
    else:
        subj, sbox = cover_crop(photo, panel, focus=((fb[0] + fb[2]) // 2, (fb[1] + fb[3]) // 2))
        subj = rounded(subj, 28)
        meta["subject"] = {"crop_box": sbox, "background_removed": False, "focal_box": fb, "size": panel}
    sx = SIZE[0] - subj.size[0] - 40 if side == "right" else 40
    sy = (SIZE[1] - subj.size[1]) // 2
    shadow = Image.new("RGBA", SIZE, (0, 0, 0, 0))
    shadow.paste((0, 0, 0, 170), (sx + 14, sy + 18, sx + subj.size[0] + 14, sy + subj.size[1] + 18))
    base = Image.alpha_composite(base, shadow.filter(ImageFilter.GaussianBlur(22)))
    base.alpha_composite(subj, (sx, sy))
    meta["subject"]["placed_at"] = (sx, sy)

    base = vignette(base)
    if side == "right":
        base = darken_gradient(base, 0.25, 200, x_to=sx + 60)
        base, over = draw_copy(base, text, font_path, 72, sx - 20, SIZE[1] - 64, 420, start=96)
    else:
        base = darken_gradient(base, 0.25, 200)
        base, over = draw_copy(base, text, font_path, sx + subj.size[0] + 40, SIZE[0] - 60, SIZE[1] - 64, 420, start=96)
    base = draw_badge(base, status, font_path)
    _save(base, out_path)
    meta["text_overflow"] = over
    return meta


# ------------------------------------------------------------------ 레이아웃 B: 좌우 비교형

def layout_compare(left_path, right_path, text, font_path, status, out_path, labels=("", "")):
    Image, ImageDraw, _, _, _, _ = _pil()
    half = (SIZE[0] // 2 - 4, SIZE[1])
    meta = {"layout": "B 좌우 비교형", "panels": []}
    base = Image.new("RGBA", SIZE, (12, 12, 14, 255))
    for i, (p, label) in enumerate(((left_path, labels[0]), (right_path, labels[1]))):
        photo = load_photo(p)
        photo, edits = enhance(photo)
        fb = focal_box(photo, frac_w=0.7, aspect=half[0] / half[1])
        panel, box = cover_crop(photo, half, focus=((fb[0] + fb[2]) // 2, (fb[1] + fb[3]) // 2))
        x = 0 if i == 0 else SIZE[0] // 2 + 4
        base.paste(panel.convert("RGBA"), (x, 0))
        meta["panels"].append({"side": "left" if i == 0 else "right", "source_image": p, "source_size": photo.size,
                               "crop_box": box, "edits": edits, "label": label})
    d = ImageDraw.Draw(base)
    d.rectangle([SIZE[0] // 2 - 4, 0, SIZE[0] // 2 + 4, SIZE[1]], fill=(255, 214, 0, 255))
    base = vignette(base)
    base = darken_gradient(base, 0.42, 225)
    for i, label in enumerate(labels):
        if label:
            base = draw_label(base, label, font_path, 40 if i == 0 else SIZE[0] // 2 + 44, 130)
    base, over = draw_copy(base, text, font_path, 72, SIZE[0] - 72, SIZE[1] - 56, 300, start=92)
    base = draw_badge(base, status, font_path)
    _save(base, out_path)
    meta["text_overflow"] = over
    meta["note"] = "서로 다른 두 사진을 나란히 배치한 시각 자료입니다. 실제 비교 실험 장면이 아닙니다."
    return meta


# ------------------------------------------------------------------ 레이아웃 C: 증거 확대형

def layout_zoom(photo_path, text, font_path, status, out_path, zoom_frac=0.22, min_scale=2.2):
    Image, ImageDraw, _, ImageFilter, _, _ = _pil()
    photo = load_photo(photo_path)
    photo, edits = enhance(photo)
    # 확대창 지름 420px 기준으로 최소 min_scale 배가 되도록 확대 영역 크기를 제한
    R = 210
    frac = min(zoom_frac, (2 * R / min_scale) / photo.size[0])
    fb = focal_box(photo, frac_w=max(0.06, frac), aspect=1.0)
    # 맥락: 초점이 화면 안에 들어오도록 cover 크롭
    base_img, crop_box = cover_crop(photo, SIZE, focus=((fb[0] + fb[2]) // 2, (fb[1] + fb[3]) // 2))
    base = base_img.convert("RGBA")
    meta = {"layout": "C 증거 확대형", "source_image": photo_path, "source_size": photo.size, "edits": edits,
            "context_crop_box": crop_box, "zoom_box_original": fb}

    # 확대창 (원형, 흰 테두리) — 오른쪽 위
    inset = photo.crop(fb).resize((2 * R, 2 * R), Image.LANCZOS)
    mask = Image.new("L", (2 * R, 2 * R), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, 2 * R - 1, 2 * R - 1], fill=255)
    cx, cy = SIZE[0] - R - 60, R + 60
    base = vignette(base)
    base = darken_gradient(base, 0.3, 215, x_to=SIZE[0] - 2 * R - 90)
    # 원본 위치 표시 + 연결선
    tb = to_thumb_coords(fb, crop_box, SIZE)
    d = ImageDraw.Draw(base)
    d.rectangle(tb, outline=(255, 214, 0, 255), width=5)
    d.line([((tb[0] + tb[2]) // 2, (tb[1] + tb[3]) // 2), (cx - R, cy)], fill=(255, 214, 0, 230), width=4)
    shadow = Image.new("RGBA", SIZE, (0, 0, 0, 0))
    ImageDraw.Draw(shadow).ellipse([cx - R + 10, cy - R + 14, cx + R + 10, cy + R + 14], fill=(0, 0, 0, 180))
    base = Image.alpha_composite(base, shadow.filter(ImageFilter.GaussianBlur(18)))
    circ = inset.convert("RGBA")
    circ.putalpha(mask)
    base.alpha_composite(circ, (cx - R, cy - R))
    d = ImageDraw.Draw(base)
    d.ellipse([cx - R, cy - R, cx + R, cy + R], outline=(255, 255, 255, 255), width=8)
    d.ellipse([cx - R, cy - R, cx + R, cy + R], outline=(255, 214, 0, 255), width=3)
    scale = round((2 * R) / max(1, fb[2] - fb[0]), 2)
    base = draw_label(base, f"확대 ×{scale}", font_path, cx - R, cy + R + 12, 26)
    meta.update({"zoom_box_on_thumbnail": tb, "inset_center": (cx, cy), "inset_radius": R, "zoom_scale": scale})

    base, over = draw_copy(base, text, font_path, 72, SIZE[0] - 2 * R - 120, SIZE[1] - 64, 380, start=92)
    base = draw_badge(base, status, font_path)
    _save(base, out_path)
    meta["text_overflow"] = over
    return meta
