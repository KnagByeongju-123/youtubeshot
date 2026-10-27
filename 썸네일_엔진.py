"""GUI에 의존하지 않는 DreamArt 썸네일 합성/저장 엔진.
(출처: github.com/KnagByeongju-123/thumbnail 의 thumbnail_core.py, MIT - 썸네일_엔진_LICENSE.txt.
 이 프로그램에 맞춰 더한 것: AI 누끼(rembg) 연결, 프로그램 글꼴(검은고딕), 편집 상태 저장/불러오기, 자동 후보 auto_candidates)

구성 순서 (아래에서 위로 쌓임)
  1. 배경 (흐림·채도·밝기 보정)
  2. 사진 레이어들 (원하는 만큼, 위치/크기/회전/모양/테두리/그림자/투명도)
  3. 가독성 오버레이 (하단/좌측/우측 그라데이션, 비네팅, 전체 어둡게)
  4. 스티커 레이어 (빨간 원, 화살표, 물음표 배지 — 오버레이에 가려지지 않게 위쪽)
  5. 태그 배지 + 제목 (강조색 [단어] 문법, 외곽선/그림자/네온/박스 효과)
  6. 프레임 장식
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import math
import os
import random

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps

# ──────────────────────────────────────────────────────────────── 상수 / 선택지
PRESETS = {
    "YouTube HD 1280×720": (1280, 720),
    "YouTube FHD 1920×1080": (1920, 1080),
    "Shorts 세로 1080×1920": (1080, 1920),
    "정사각형 1080×1080": (1080, 1080),
}
# 테마 = (제목 기본색, 강조색)
THEMES = {
    "골드": ((255, 255, 255), (255, 205, 55)),
    "옐로 타이틀": ((255, 214, 10), (255, 255, 255)),
    "시안": ((245, 255, 255), (0, 225, 255)),
    "핑크": ((255, 250, 255), (255, 72, 155)),
    "레드": ((255, 255, 255), (255, 70, 60)),
    "오렌지": ((255, 255, 255), (255, 140, 30)),
    "라임": ((255, 255, 255), (170, 255, 60)),
    "블루": ((255, 255, 255), (70, 155, 255)),
    "퍼플": ((255, 255, 255), (175, 115, 255)),
    "화이트": ((255, 255, 255), (230, 230, 230)),
}
TITLE_STYLES = ["외곽선", "그림자", "네온 글로우", "박스 강조", "깔끔(효과 없음)"]
OVERLAYS = ["하단 그라데이션", "좌측 그라데이션", "우측 그라데이션", "비네팅", "전체 어둡게", "없음"]
FRAMES = ["테두리", "이중 테두리", "코너 장식", "없음"]
TAG_POSITIONS = ["제목 위", "좌측 상단", "우측 상단"]
SHAPES = ["원본", "둥근 모서리", "원형", "폴라로이드"]
ARRANGEMENTS = ["좌우 대칭", "중앙 겹치기", "비대칭 히어로", "콜라주 그리드", "배경 중심"]
STICKERS = ["빨간 원", "화살표", "물음표 배지", "느낌표 배지"]

# 한 번에 여러 옵션을 바꾸는 디자인 프리셋
DESIGN_PRESETS: dict[str, dict] = {
    "미스터리 다큐": dict(theme="골드", title_style="그림자", overlay="좌측 그라데이션", darkness=78,
                     align="left", tag_position="좌측 상단", frame="없음", text_y=66,
                     bg_saturation=80, bg_blur=0),
    "클래식 유튜브": dict(theme="옐로 타이틀", title_style="외곽선", overlay="하단 그라데이션", darkness=65,
                     align="center", tag_position="제목 위", frame="테두리", text_y=76,
                     bg_saturation=110, bg_blur=0),
    "속보 뉴스": dict(theme="레드", title_style="박스 강조", overlay="하단 그라데이션", darkness=45,
                  align="left", tag_position="좌측 상단", frame="테두리", text_y=74,
                  bg_saturation=100, bg_blur=0),
    "네온 SF": dict(theme="시안", title_style="네온 글로우", overlay="비네팅", darkness=80,
                  align="center", tag_position="제목 위", frame="코너 장식", text_y=72,
                  bg_saturation=120, bg_blur=0),
    "시네마틱": dict(theme="화이트", title_style="그림자", overlay="비네팅", darkness=70,
                 align="center", tag_position="우측 상단", frame="없음", text_y=78,
                 bg_saturation=70, bg_blur=2),
    "미니멀": dict(theme="화이트", title_style="깔끔(효과 없음)", overlay="전체 어둡게", darkness=45,
                align="center", tag_position="제목 위", frame="없음", text_y=55,
                bg_saturation=60, bg_blur=6),
}


# ──────────────────────────────────────────────────────────────── 데이터 구조
@dataclass(eq=False)
class PhotoLayer:
    """썸네일 위에 올리는 사진(또는 스티커) 한 장. 좌표는 0~1 비율."""
    image: Image.Image
    name: str = "사진"
    x: float = .5           # 중심 가로 위치 (0=왼쪽, 1=오른쪽)
    y: float = .45          # 중심 세로 위치 (0=위, 1=아래)
    height: float = .6      # 캔버스 높이 대비 크기
    rotation: float = 0.    # 도(°), 양수 = 반시계
    opacity: int = 100      # 10~100
    shape: str = "원본"
    outline: bool = False
    shadow: bool = True
    remove_bg: bool = False
    visible: bool = True
    kind: str = "photo"     # "photo" | "sticker"
    ai_cutout: bool = False  # AI 누끼(rembg, CUTOUT 연결 시) - 단색 배경 제거보다 정확
    src: str = ""           # 원본 파일 경로 (편집 상태 저장용)
    sticker: str = ""       # 스티커 종류 (편집 상태 저장용)
    _cache: dict = field(default_factory=dict, repr=False)

    def copy(self) -> "PhotoLayer":
        twin = PhotoLayer(**{k: getattr(self, k) for k in (
            "image", "name", "x", "y", "height", "rotation", "opacity", "shape",
            "outline", "shadow", "remove_bg", "visible", "kind", "ai_cutout", "src", "sticker")})
        twin._cache = self._cache  # 같은 원본 이미지이므로 배경 제거 결과 공유
        return twin


@dataclass
class RenderOptions:
    size: tuple[int, int] = (1280, 720)
    layout: str = "좌우 대칭"          # subject1/subject2 하위 호환용 배치
    title: str = "눈을 사로잡는\n[한 장]의 썸네일"
    subtitle: str = "DREAMART VIDEO HIGHLIGHT"
    theme: str = "골드"
    align: str = "center"
    font_size: int = 86               # 1280px 폭 기준, 다른 크기는 비례
    text_y: int = 76                  # 0-100: 제목 블록 세로 중심
    brightness: int = 85              # 20-150
    darkness: int = 62                # 0-100: 오버레이 강도
    remove_bg_1: bool = False
    remove_bg_2: bool = False
    subject_scale: int = 100          # 40-160 (하위 호환)
    title_style: str = "외곽선"
    overlay: str = "하단 그라데이션"
    frame: str = "테두리"
    tag_position: str = "제목 위"
    bg_blur: int = 0                  # 0-30
    bg_saturation: int = 100          # 0-200
    layers: list[PhotoLayer] = field(default_factory=list)


# ──────────────────────────────────────────────────────────────── 기본 도구
def load_image(path: str | Path) -> Image.Image:
    with Image.open(path) as loaded:
        return ImageOps.exif_transpose(loaded).convert("RGBA")


def face_center(image: Image.Image):
    """사진 속 주인공 얼굴(들)의 가운데 (0~1 비율) 또는 None — OpenCV YuNet (models/face_detection_yunet_2023mar.onnx)"""
    mp = Path(__file__).resolve().parent / "models" / "face_detection_yunet_2023mar.onnx"
    try:
        import cv2
        import numpy as np
        if not mp.exists():
            return None
        a = np.asarray(image.convert("RGB"))[:, :, ::-1]
        h, w = a.shape[:2]
        k = 640 / max(h, w)
        sm = cv2.resize(a, (max(1, int(w * k)), max(1, int(h * k))))
        det = cv2.FaceDetectorYN.create(str(mp), "", (sm.shape[1], sm.shape[0]), 0.6)
        _, f = det.detect(sm)
        if f is None or not len(f):
            return None
        big = max(r[2] * r[3] for r in f)
        f = [r for r in f if r[2] * r[3] >= 0.3 * big]
        cx = sum(r[0] + r[2] / 2 for r in f) / len(f) / sm.shape[1]
        cy = sum(r[1] + r[3] / 2 for r in f) / len(f) / sm.shape[0]
        return cx, cy
    except Exception:
        return None


def fit_cover(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    """이미지를 왜곡하지 않고 대상 크기에 가득 채움. 얼굴이 있으면 얼굴이 잘리지 않게 얼굴 쪽을 기준으로 자름
    (규칙: 세로로 긴 초상화를 가로 썸네일에 채울 때 가운데만 자르면 얼굴이 잘림)"""
    fc = face_center(image)
    centering = (min(max(fc[0], 0.0), 1.0), min(max(fc[1] - 0.08, 0.0), 1.0)) if fc else (0.5, 0.5)   # 얼굴을 살짝 위쪽에
    return ImageOps.fit(image.convert("RGB"), size, method=Image.Resampling.LANCZOS, centering=centering)


HERE = Path(__file__).resolve().parent
FONT_PATH = str(HERE / "fonts" / "BlackHanSans-Regular.ttf")   # 프로그램 썸네일 글꼴(검은고딕) - 없으면 아래 후보
CUTOUT = None   # 사진 → 배경 투명 RGBA (못 하면 None). 프로그램이 썸네일_합성.cutout(rembg)을 연결


def _font_candidates() -> list[str]:
    return [
        os.environ.get("DREAMART_FONT", ""),
        FONT_PATH,
        "C:/Windows/Fonts/malgunbd.ttf",
        "C:/Windows/Fonts/malgun.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
        "/System/Library/Fonts/AppleSDGothicNeo.ttc",
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc",
        "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]


_FONT_CACHE: dict[int, ImageFont.ImageFont] = {}


def font_for(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    size = max(10, int(size))
    if size in _FONT_CACHE:
        return _FONT_CACHE[size]
    font = None
    for p in _font_candidates():
        if p and Path(p).is_file():
            try:
                font = ImageFont.truetype(p, size)
                break
            except OSError:
                pass
    if font is None:
        try:
            font = ImageFont.truetype("DejaVuSans.ttf", size)
        except OSError:
            font = ImageFont.load_default(size=size)
    _FONT_CACHE[size] = font
    return font


def demo_background(size: tuple[int, int]) -> Image.Image:
    """사용자 파일이 없을 때 쓰는 내장 예시 배경."""
    w, h = size
    arr = np.zeros((h, w, 3), dtype=np.uint8)
    yy = np.linspace(0, 1, h, dtype=np.float32)
    for c, (a, b) in enumerate([(36, 15), (32, 8), (80, 50)]):
        arr[:, :, c] = (a * (1 - yy) + b * yy).astype(np.uint8)[:, None]
    im = Image.fromarray(arr, "RGB")
    layer = Image.new("RGBA", size)
    d = ImageDraw.Draw(layer)
    r = random.Random(2026)
    for _ in range(32):
        x = r.randint(0, w)
        y = r.randint(0, h)
        radius = r.randint(max(3, h // 120), max(12, h // 20))
        d.ellipse((x - radius, y - radius, x + radius, y + radius), fill=(80, 140, 255, r.randint(50, 125)))
    layer = layer.filter(ImageFilter.GaussianBlur(max(5, h // 28)))
    return Image.alpha_composite(im.convert("RGBA"), layer).convert("RGB")


def remove_corner_background(image: Image.Image, tolerance: int = 38) -> Image.Image:
    """네 모서리의 비슷한 단색 배경만 제거하는 간이 방식 (AI 누끼 아님)."""
    original = image.convert("RGBA")
    scale = min(1.0, 1500.0 / max(original.size))
    small = original if scale == 1.0 else original.resize(
        (max(1, round(original.width * scale)), max(1, round(original.height * scale))),
        Image.Resampling.BILINEAR,
    )
    pixels = np.asarray(small.convert("RGB"), dtype=np.int16)
    h, w = pixels.shape[:2]
    box = max(1, min(h, w) // 25)
    patches = [pixels[:box, :box], pixels[:box, -box:], pixels[-box:, :box], pixels[-box:, -box:]]
    corner = np.median(np.concatenate([p.reshape(-1, 3) for p in patches]), axis=0)
    delta = np.max(np.abs(pixels - corner), axis=2)
    candidate = (delta < tolerance).astype(np.uint8)
    count, labels = cv2.connectedComponents(candidate, connectivity=4)
    border_labels = np.unique(np.concatenate([labels[0, :], labels[-1, :], labels[:, 0], labels[:, -1]]))
    border_labels = border_labels[border_labels != 0]
    if count <= 1 or len(border_labels) == 0:
        return original
    mask = np.where(np.isin(labels, border_labels), 0, 255).astype(np.uint8)
    mask_im = Image.fromarray(mask, "L").filter(ImageFilter.GaussianBlur(1.2))
    if mask_im.size != original.size:
        mask_im = mask_im.resize(original.size, Image.Resampling.BILINEAR)
    a1 = np.asarray(original.getchannel("A"), dtype=np.uint16)
    a2 = np.asarray(mask_im, dtype=np.uint16)
    original.putalpha(Image.fromarray((a1 * a2 // 255).astype(np.uint8), "L"))
    return original


def _multiply_alpha(img: Image.Image, mask: Image.Image) -> Image.Image:
    a1 = np.asarray(img.getchannel("A"), dtype=np.uint16)
    a2 = np.asarray(mask, dtype=np.uint16)
    out = img.copy()
    out.putalpha(Image.fromarray((a1 * a2 // 255).astype(np.uint8), "L"))
    return out


# ──────────────────────────────────────────────────────────────── 스티커
def make_sticker(kind: str, color: tuple[int, int, int] = (235, 35, 35)) -> Image.Image:
    """강조용 도형을 투명 PNG로 생성 (원/화살표/물음표/느낌표)."""
    if kind == "빨간 원":
        s = 600
        im = Image.new("RGBA", (s, int(s * .78)), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        d.ellipse((24, 24, s - 24, im.height - 24), outline=color + (255,), width=34)
        return im
    if kind == "화살표":
        im = Image.new("RGBA", (720, 300), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        pts = [(20, 105), (450, 105), (450, 25), (700, 150), (450, 275), (450, 195), (20, 195)]
        d.polygon(pts, fill=color + (255,))
        d.line(pts + [pts[0]], fill=(255, 255, 255, 255), width=14, joint="curve")
        return im
    symbol = "?" if kind == "물음표 배지" else "!"
    s = 420
    im = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse((10, 10, s - 10, s - 10), fill=color + (255,), outline=(255, 255, 255, 255), width=18)
    f = font_for(290)
    bb = d.textbbox((0, 0), symbol, font=f)
    d.text(((s - (bb[2] - bb[0])) / 2 - bb[0], (s - (bb[3] - bb[1])) / 2 - bb[1]),
           symbol, font=f, fill=(255, 255, 255, 255))
    return im


# ──────────────────────────────────────────────────────────────── 레이어 렌더링
def _layer_source(layer: PhotoLayer) -> Image.Image:
    """배경 제거 결과를 레이어에 캐시해 미리보기/드래그를 빠르게 유지."""
    if layer.ai_cutout and CUTOUT is not None:
        key = ("ai", id(layer.image))
        if key not in layer._cache:
            try:
                obj = CUTOUT(layer.image.convert("RGB"))
            except Exception:
                obj = None
            if obj is not None:
                bbox = obj.getbbox()
                layer._cache[key] = obj.crop(bbox) if bbox else obj
            else:                       # AI 누끼 실패 → 단색 배경 제거로
                layer._cache[key] = remove_corner_background(layer.image)
        return layer._cache[key]
    if not layer.remove_bg:
        return layer.image.convert("RGBA") if layer.image.mode != "RGBA" else layer.image
    key = ("nobg", id(layer.image))
    if key not in layer._cache:
        obj = remove_corner_background(layer.image)
        bbox = obj.getbbox()
        layer._cache.clear()
        layer._cache[key] = obj.crop(bbox) if bbox else obj
    return layer._cache[key]


def _shape_image(obj: Image.Image, layer: PhotoLayer, accent, canvas_h: int) -> Image.Image:
    """모양(둥근/원형/폴라로이드)과 테두리 적용."""
    ow = max(3, canvas_h // 110)  # 테두리 두께
    if layer.shape == "원형":
        side = min(obj.size)
        obj = ImageOps.fit(obj, (side, side), method=Image.Resampling.LANCZOS)
        mask = Image.new("L", obj.size, 0)
        ImageDraw.Draw(mask).ellipse((0, 0, side - 1, side - 1), fill=255)
        obj = _multiply_alpha(obj, mask)
        if layer.outline:
            ImageDraw.Draw(obj).ellipse((ow // 2, ow // 2, side - 1 - ow // 2, side - 1 - ow // 2),
                                        outline=accent + (255,), width=ow)
        return obj
    if layer.shape == "둥근 모서리":
        radius = max(4, min(obj.size) // 12)
        mask = Image.new("L", obj.size, 0)
        ImageDraw.Draw(mask).rounded_rectangle((0, 0, obj.width - 1, obj.height - 1), radius=radius, fill=255)
        obj = _multiply_alpha(obj, mask)
        if layer.outline:
            ImageDraw.Draw(obj).rounded_rectangle(
                (ow // 2, ow // 2, obj.width - 1 - ow // 2, obj.height - 1 - ow // 2),
                radius=radius, outline=accent + (255,), width=ow)
        return obj
    if layer.shape == "폴라로이드":
        pad = max(6, min(obj.size) // 22)
        bottom = pad * 4
        card = Image.new("RGBA", (obj.width + pad * 2, obj.height + pad + bottom), (250, 248, 242, 255))
        card.alpha_composite(obj.convert("RGBA"), (pad, pad))
        if layer.outline:
            ImageDraw.Draw(card).rectangle((0, 0, card.width - 1, card.height - 1),
                                           outline=accent + (255,), width=ow)
        return card
    # 원본
    if layer.outline:
        alpha = obj.getchannel("A")
        if alpha.getextrema()[0] >= 250:  # 불투명한 사각형 사진
            obj = obj.copy()
            ImageDraw.Draw(obj).rectangle((0, 0, obj.width - 1, obj.height - 1),
                                          outline=accent + (255,), width=ow)
        else:  # 누끼 사진 → 윤곽선을 따라 테두리
            k = ow * 2 + 1
            padded = Image.new("RGBA", (obj.width + k, obj.height + k), (0, 0, 0, 0))
            padded.alpha_composite(obj, (k // 2, k // 2))
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k))
            grown = cv2.dilate(np.asarray(padded.getchannel("A")), kernel)
            ring = Image.new("RGBA", padded.size, accent + (255,))
            ring.putalpha(Image.fromarray(grown, "L"))
            ring.alpha_composite(padded)
            obj = ring
    return obj


def _prepare_layer(layer: PhotoLayer, size: tuple[int, int], accent) -> tuple[Image.Image, tuple[int, int]] | None:
    w, h = size
    obj = _layer_source(layer)
    if obj.getbbox() is None:
        return None
    target_h = max(4, int(h * max(.03, layer.height)))
    ratio = target_h / max(1, obj.height)
    target_w = max(4, int(obj.width * ratio))
    if target_w > w * 2:  # 지나치게 큰 레이어 방지
        ratio *= (w * 2) / target_w
        target_w, target_h = max(4, int(obj.width * ratio)), max(4, int(obj.height * ratio))
    obj = obj.resize((target_w, target_h), Image.Resampling.LANCZOS)
    obj = _shape_image(obj, layer, accent, h)
    if layer.rotation:
        obj = obj.rotate(layer.rotation, resample=Image.Resampling.BICUBIC, expand=True)
    if layer.opacity < 100:
        a = obj.getchannel("A").point(lambda v: round(v * max(.05, layer.opacity / 100)))
        obj.putalpha(a)
    left = int(w * layer.x - obj.width / 2)
    top = int(h * layer.y - obj.height / 2)
    return obj, (left, top)


def _composite_layer(canvas: Image.Image, layer: PhotoLayer, accent) -> tuple[int, int, int, int] | None:
    prepared = _prepare_layer(layer, canvas.size, accent)
    if prepared is None:
        return None
    obj, (x, y) = prepared
    h = canvas.height
    if layer.shadow:
        blur = max(4, h // 54)
        shadow_alpha = obj.getchannel("A").filter(ImageFilter.GaussianBlur(blur)).point(lambda v: round(v * .6))
        shadow = Image.new("RGBA", obj.size, (0, 0, 0, 0))
        shadow.putalpha(shadow_alpha)
        _paste_clipped(canvas, shadow, x + h // 90, y + h // 90)
    _paste_clipped(canvas, obj, x, y)
    return (x, y, x + obj.width, y + obj.height)


def _paste_clipped(canvas: Image.Image, obj: Image.Image, x: int, y: int) -> None:
    """캔버스 밖으로 일부가 나간 레이어도 보이는 부분만 잘라서 합성."""
    left, top = max(0, x), max(0, y)
    right, bottom = min(canvas.width, x + obj.width), min(canvas.height, y + obj.height)
    if right <= left or bottom <= top:
        return
    piece = obj.crop((left - x, top - y, right - x, bottom - y))
    canvas.alpha_composite(piece, (left, top))


# ──────────────────────────────────────────────────────────────── 자동 배치
def _fit_into_box(layer: PhotoLayer, box, size) -> None:
    cx, cy, bw, bh = box
    w, h = size
    img = layer.image
    aspect = img.width / max(1, img.height)
    if layer.shape == "원형":
        aspect = 1.0
    layer.x, layer.y = cx, cy
    layer.height = max(.05, min(bh, bw * w / max(1e-6, aspect * h)))


def _grid_boxes(n, region, gap=.02, cols=None):
    x0, y0, x1, y1 = region
    cols = cols or max(1, math.ceil(math.sqrt(n * 1.6)))
    rows = math.ceil(n / cols)
    cw, rh = (x1 - x0) / cols, (y1 - y0) / rows
    boxes = []
    for i in range(n):
        r, c = divmod(i, cols)
        in_row = min(cols, n - r * cols)
        shift = (cols - in_row) * cw / 2  # 마지막 줄 가운데 정렬
        boxes.append((x0 + shift + cw * (c + .5), y0 + rh * (r + .5), cw - gap, rh - gap))
    return boxes


def arrange_layers(layers: list[PhotoLayer], preset: str, size: tuple[int, int]) -> None:
    """사진 레이어(스티커 제외)를 프리셋 규칙으로 다시 배치. 회전도 초기화/설정."""
    photos = [l for l in layers if l.kind == "photo"]
    n = len(photos)
    if not n:
        return
    portrait = size[1] > size[0]
    if preset == "중앙 겹치기":
        spread = .10 if not portrait else .07
        for i, l in enumerate(photos):
            off = i - (n - 1) / 2
            l.rotation = -off * 7 if n > 1 else 0
            _fit_into_box(l, (.5 + off * spread, .42 + abs(off) * .02, .55, .66), size)
        return
    for l in photos:
        l.rotation = 0
    if preset == "비대칭 히어로":
        _fit_into_box(photos[0], (.70, .45, .58, .9), size)
        rest = photos[1:]
        for l, b in zip(rest, _grid_boxes(len(rest), (.02, .05, .40, .62), cols=1 if len(rest) <= 3 else 2)):
            _fit_into_box(l, b, size)
        return
    if preset == "콜라주 그리드":
        boxes = _grid_boxes(n, (.01, .01, .99, .99), gap=.015)
    elif preset == "배경 중심":
        boxes = _grid_boxes(n, (.55, .04, .97, .42), cols=min(n, 3))
    else:  # 좌우 대칭
        if portrait:
            boxes = _grid_boxes(n, (.04, .04, .96, .62), cols=1 if n <= 2 else 2)
        else:
            boxes = _grid_boxes(n, (.02, .08, .98, .80), cols=n if n <= 3 else None)
    for l, b in zip(photos, boxes):
        _fit_into_box(l, b, size)


def _legacy_layers(opts: RenderOptions, subject1, subject2) -> list[PhotoLayer]:
    """예전 버전(피사체 1·2) 호출을 레이어 방식으로 변환."""
    layouts = {
        "좌우 대칭": [(.23, .44, .67), (.77, .44, .67)],
        "중앙 집중": [(.39, .41, .73), (.66, .43, .64)],
        "비대칭 히어로": [(.73, .45, .93), (.20, .47, .48)],
        "배경 중심": [(.74, .40, .52), (.20, .40, .42)],
    }
    pos = layouts.get(opts.layout, layouts["좌우 대칭"])
    factor = max(.4, min(1.6, opts.subject_scale / 100))
    out = []
    for img, p, rm in [(subject1, pos[0], opts.remove_bg_1), (subject2, pos[1], opts.remove_bg_2)]:
        if img is not None:
            out.append(PhotoLayer(img, x=p[0], y=p[1], height=p[2] * factor, remove_bg=rm))
    return out


# ──────────────────────────────────────────────────────────────── 텍스트
def parse_markup(text: str) -> list[tuple[str, bool]]:
    """'[강조]' 표시를 (글자, 강조여부) 목록으로 변환. 대괄호는 지움."""
    out, accent = [], False
    for ch in text:
        if ch == "[":
            accent = True
        elif ch == "]":
            accent = False
        else:
            out.append((ch, accent))
    return out


def _wrap_text(draw: ImageDraw.ImageDraw, text: str, font, max_width: int) -> list[str]:
    """명시적 줄바꿈은 유지하고, 긴 줄은 단어(필요시 글자) 단위 자동 줄바꿈."""
    lines: list[str] = []
    for block in text.splitlines() or [""]:
        if not block:
            lines.append("")
            continue
        current = ""
        for word in block.split(" "):
            candidate = (current + " " + word).strip() if current else word
            if draw.textlength(candidate, font=font) <= max_width:
                current = candidate
            else:
                if current:
                    lines.append(current)
                    current = ""
                for char in word:
                    if current and draw.textlength(current + char, font=font) > max_width:
                        lines.append(current)
                        current = char
                    else:
                        current += char
        if current:
            lines.append(current)
    return lines[:10]


def _line_segments(lines: list[str], marked: list[tuple[str, bool]]) -> list[list[tuple[str, bool]]]:
    """줄바꿈된 각 줄에 원래 강조 정보를 되돌려 붙임 (공백/개행만 빠지므로 순서대로 대응)."""
    result, cur = [], 0
    for line in lines:
        segs: list[tuple[str, bool]] = []
        for ch in line:
            while cur < len(marked) and marked[cur][0] != ch:
                cur += 1
            flag = marked[cur][1] if cur < len(marked) else False
            cur += 1
            if segs and segs[-1][1] == flag:
                segs[-1] = (segs[-1][0] + ch, flag)
            else:
                segs.append((ch, flag))
        result.append(segs)
    return result


def _draw_tag(draw, text, font, x, y, pill_h, base_size, accent, align_box=None):
    bb = draw.textbbox((0, 0), text, font=font)
    lw, lh = bb[2] - bb[0], bb[3] - bb[1]
    pill_w = lw + round(base_size * .4)
    if align_box is not None:
        mode, left, right = align_box
        x = left if mode == "left" else (right - pill_w if mode == "right" else (left + right - pill_w) // 2)
    draw.rounded_rectangle((x, y, x + pill_w, y + pill_h), radius=max(4, pill_h // 5), fill=accent + (245,))
    dark = (15, 15, 20, 255) if sum(accent) > 300 else (255, 255, 255, 255)
    draw.text((x + (pill_w - lw) / 2 - bb[0], y + (pill_h - lh) / 2 - bb[1]), text, fill=dark, font=font)


def _draw_title_and_tag(canvas: Image.Image, opts: RenderOptions) -> Image.Image:
    w, h = canvas.size
    primary, accent = THEMES.get(opts.theme, THEMES["골드"])
    ratio = min(w, h * 16 / 9) / 1280  # 세로 캔버스에서도 과하게 작아지지 않게
    margin = round(min(w, h) * .055)
    maxwidth = w - 2 * margin
    base_size = max(18, round(opts.font_size * ratio))
    marked = parse_markup(opts.title.strip())
    plain = "".join(c for c, _ in marked)

    measure = ImageDraw.Draw(Image.new("L", (1, 1)))
    lines: list[str] = []
    line_height = total_main = 0
    for _ in range(40):
        font = font_for(base_size)
        lines = _wrap_text(measure, plain, font, maxwidth - (base_size // 3 if opts.title_style == "박스 강조" else 0))
        line_height = int(base_size * (1.32 if opts.title_style == "박스 강조" else 1.21))
        total_main = len(lines) * line_height
        if total_main <= h * .55 and len(lines) <= 5:
            break
        base_size = max(16, base_size - max(1, int(2 * ratio)))
    segments = _line_segments(lines, marked)

    label_text = opts.subtitle.strip()[:120]
    label_font = font_for(max(13, round(base_size * .37)))
    label_h = max(26, round(base_size * .58)) if label_text else 0
    if label_text:
        while measure.textlength(label_text, font=label_font) > maxwidth - 36 and len(label_text) > 2:
            label_text = label_text[:-2] + "…"
    tag_above = bool(label_text) and opts.tag_position == "제목 위"
    space = round(base_size * .17) if tag_above else 0
    block_h = total_main + (label_h + space if tag_above else 0)
    target_center = h * max(.12, min(.92, opts.text_y / 100))
    y0 = max(margin, min(h - margin - block_h, round(target_center - block_h / 2)))

    # 1) 효과 없는 '글자 모양' 레이어 → 그림자/글로우의 원본
    text_layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    tdraw = ImageDraw.Draw(text_layer)
    box_layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    bdraw = ImageDraw.Draw(box_layer)
    style = opts.title_style
    stroke = {"외곽선": max(2, int(base_size * .065)), "그림자": max(1, int(base_size * .03)),
              "네온 글로우": max(2, int(base_size * .05))}.get(style, 0)
    main_y = y0 + (label_h + space if tag_above else 0)
    for segs in segments:
        if not segs:
            main_y += line_height
            continue
        text_w = sum(tdraw.textlength(s, font=font) for s, _ in segs)
        tx = margin if opts.align == "left" else (w - margin - text_w if opts.align == "right" else (w - text_w) / 2)
        if style == "박스 강조":
            pad = base_size * .16
            asc, desc = font.getmetrics()
            if opts.align == "left":
                tx += pad
            elif opts.align == "right":
                tx -= pad
            bdraw.rectangle((tx - pad, main_y + base_size * .02, tx + text_w + pad, main_y + asc + desc * .55),
                            fill=(12, 12, 16, 228))
            bdraw.rectangle((tx - pad, main_y + base_size * .02, tx - pad + max(4, base_size * .07),
                             main_y + asc + desc * .55), fill=accent + (255,))
        x = tx
        for s, is_accent in segs:
            color = (accent if is_accent else primary) + (255,)
            tdraw.text((x, main_y), s, font=font, fill=color,
                       stroke_width=stroke, stroke_fill=(7, 7, 14, 255))
            x += tdraw.textlength(s, font=font)
        main_y += line_height

    out = canvas
    if style == "박스 강조":
        out = Image.alpha_composite(out, box_layer)
    alpha = text_layer.getchannel("A")
    if style == "그림자":
        off = max(3, base_size // 14)
        sh = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        sh.putalpha(alpha.filter(ImageFilter.GaussianBlur(max(2, base_size / 14))).point(lambda v: round(v * .9)))
        _paste_clipped(out, sh, off, off)
    elif style == "네온 글로우":
        for radius, strength in ((base_size / 3.5, .9), (base_size / 9, .55)):
            glow = Image.new("RGBA", (w, h), accent + (0,))
            glow.putalpha(alpha.filter(ImageFilter.GaussianBlur(radius)).point(lambda v, s=strength: min(255, round(v * 1.8 * s))))
            out = Image.alpha_composite(out, glow)
    out = Image.alpha_composite(out, text_layer)

    # 2) 태그 배지
    if label_text:
        tag = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        d = ImageDraw.Draw(tag)
        if tag_above:
            _draw_tag(d, label_text, label_font, 0, y0, label_h, base_size, accent,
                      (opts.align, margin + (base_size * .16 if style == "박스 강조" and opts.align == "left" else 0),
                       w - margin))
        else:
            mode = "left" if opts.tag_position == "좌측 상단" else "right"
            _draw_tag(d, label_text, label_font, 0, margin, label_h, base_size, accent, (mode, margin, w - margin))
        out = Image.alpha_composite(out, tag)
    return out


# ──────────────────────────────────────────────────────────────── 오버레이 / 프레임
def _overlay(size, kind: str, strength: float) -> Image.Image | None:
    w, h = size
    if kind == "없음" or strength <= 0:
        return None
    if kind == "전체 어둡게":
        a = np.full((h, w), 200 * strength, dtype=np.float32)
    elif kind in ("좌측 그라데이션", "우측 그라데이션"):
        ramp = np.linspace(1, 0, w, dtype=np.float32)
        if kind == "우측 그라데이션":
            ramp = ramp[::-1]
        line = np.clip(ramp * 1.35, 0, 1) ** 1.6 * 245 * strength
        a = np.repeat(line[None, :], h, axis=0)
    elif kind == "비네팅":
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        d = np.sqrt(((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2) / math.sqrt(2)
        a = np.clip(d * 1.25, 0, 1) ** 1.7 * 255 * strength
        a += (np.linspace(0, 1, h, dtype=np.float32) ** 2.2 * 120 * strength)[:, None]  # 아래쪽 글자용
    else:  # 하단 그라데이션
        ramp = np.linspace(0, 1, h, dtype=np.float32)
        a = np.repeat((255 * strength * (ramp ** 1.4))[:, None], w, axis=1)
    over = Image.new("RGBA", (w, h), (0, 0, 0, 255))
    over.putalpha(Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "L"))
    return over


def _draw_frame(canvas: Image.Image, kind: str, accent) -> None:
    w, h = canvas.size
    d = ImageDraw.Draw(canvas)
    lw = max(3, int(min(w, h * 16 / 9) * .007))
    col = accent + (255,)
    if kind == "테두리":
        d.rectangle((0, 0, w - 1, h - 1), outline=col, width=lw)
    elif kind == "이중 테두리":
        d.rectangle((0, 0, w - 1, h - 1), outline=col, width=lw)
        g = lw * 3
        d.rectangle((g, g, w - 1 - g, h - 1 - g), outline=(255, 255, 255, 200), width=max(2, lw // 2))
    elif kind == "코너 장식":
        m = lw * 4
        L = int(min(w, h) * .12)
        t = lw + 2
        for sx, sy in ((m, m), (w - 1 - m, m), (m, h - 1 - m), (w - 1 - m, h - 1 - m)):
            dx = 1 if sx < w / 2 else -1
            dy = 1 if sy < h / 2 else -1
            d.line([(sx, sy + dy * L), (sx, sy), (sx + dx * L, sy)], fill=col, width=t, joint="curve")


# ──────────────────────────────────────────────────────────────── 메인 렌더
def render_with_bounds(opts: RenderOptions, background: Image.Image | None = None,
                       subject1: Image.Image | None = None, subject2: Image.Image | None = None
                       ) -> tuple[Image.Image, list[tuple[int, int, int, int] | None]]:
    """썸네일과 각 레이어의 화면 위치(드래그 선택용)를 함께 반환."""
    w, h = opts.size
    if w < 200 or h < 200:
        raise ValueError("출력 크기는 최소 200×200이어야 합니다.")
    bg = demo_background(opts.size) if background is None else fit_cover(background, opts.size)
    if opts.bg_blur > 0:
        bg = bg.filter(ImageFilter.GaussianBlur(opts.bg_blur * min(w, h * 16 / 9) / 1280))
    if opts.bg_saturation != 100:
        bg = ImageEnhance.Color(bg).enhance(max(0., opts.bg_saturation / 100))
    bg = ImageEnhance.Brightness(bg).enhance(max(.1, opts.brightness / 100))
    canvas = bg.convert("RGBA")
    _, accent = THEMES.get(opts.theme, THEMES["골드"])

    layers = list(opts.layers) + _legacy_layers(opts, subject1, subject2)
    bounds: list[tuple[int, int, int, int] | None] = [None] * len(layers)
    for i, layer in enumerate(layers):
        if layer.visible and layer.kind != "sticker":
            bounds[i] = _composite_layer(canvas, layer, accent)
    over = _overlay(opts.size, opts.overlay, min(100, max(0, opts.darkness)) / 100)
    if over is not None:
        canvas = Image.alpha_composite(canvas, over)
    for i, layer in enumerate(layers):
        if layer.visible and layer.kind == "sticker":
            bounds[i] = _composite_layer(canvas, layer, accent)
    canvas = _draw_title_and_tag(canvas, opts)
    _draw_frame(canvas, opts.frame, accent)
    return canvas.convert("RGB"), bounds[:len(opts.layers)]


def render_thumbnail(opts: RenderOptions, background: Image.Image | None = None,
                     subject1: Image.Image | None = None,
                     subject2: Image.Image | None = None) -> Image.Image:
    """입력 이미지는 변경하지 않고 RGB 썸네일을 반환."""
    return render_with_bounds(opts, background, subject1, subject2)[0]


def save_thumbnail(image: Image.Image, path: str | Path, jpeg_max_bytes: int = 2 * 1024 * 1024) -> tuple[int, int]:
    """JPEG는 2MB 이하가 되도록 품질을 내려 시도하며 PNG는 무손실 저장."""
    path = Path(path)
    if path.suffix.lower() == ".png":
        image.save(path, format="PNG", optimize=True)
    elif path.suffix.lower() in (".jpg", ".jpeg"):
        for quality in (94, 90, 85, 80, 75, 68, 60, 50):
            image.convert("RGB").save(path, format="JPEG", quality=quality, optimize=True, subsampling=0)
            if path.stat().st_size <= jpeg_max_bytes:
                break
    else:
        raise ValueError(".jpg / .jpeg / .png 형식만 지원합니다.")
    return image.size


# ──────────────────────────────────────────────────────────────── 편집 상태 저장/불러오기 (프로그램 ↔ 썸네일 편집기)
_OPT_KEYS = ("size", "title", "subtitle", "theme", "align", "font_size", "text_y", "brightness", "darkness",
             "title_style", "overlay", "frame", "tag_position", "bg_blur", "bg_saturation")
_LAYER_KEYS = ("name", "x", "y", "height", "rotation", "opacity", "shape", "outline", "shadow", "remove_bg",
               "visible", "kind", "ai_cutout", "src", "sticker")


def state_dict(opts: RenderOptions, background: str = "", **meta) -> dict:
    """썸네일 한 장을 다시 열어 고칠 수 있게 하는 정보 (JSON 으로 저장 가능)"""
    d = {"ver": 1, "background": background, "options": {k: getattr(opts, k) for k in _OPT_KEYS},
         "layers": [{k: getattr(l, k) for k in _LAYER_KEYS} for l in opts.layers]}
    d["options"]["size"] = list(opts.size)
    d.update(meta)
    return d


def save_state(path: str | Path, opts: RenderOptions, background: str = "", image_dir: str | Path | None = None, **meta) -> dict:
    """파일 경로가 없는 레이어(영상 캡처·붙여넣기)는 image_dir 에 PNG 로 저장하고 그 경로를 적음"""
    for i, l in enumerate(opts.layers):
        if l.kind == "photo" and (not l.src or not Path(l.src).is_file()) and image_dir:
            Path(image_dir).mkdir(parents=True, exist_ok=True)
            p = Path(image_dir) / f"레이어_{i + 1:02d}.png"
            l.image.save(p)
            l.src = str(p)
    d = state_dict(opts, background, **meta)
    import json
    Path(path).write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    return d


def load_state(d: dict) -> tuple[RenderOptions, Image.Image | None]:
    """state_dict → (RenderOptions, 배경 이미지). 없는 사진 파일은 건너뜀"""
    o = dict(d.get("options") or {})
    o["size"] = tuple(o.get("size") or (1280, 720))
    opts = RenderOptions(**{k: v for k, v in o.items() if k in _OPT_KEYS})
    for ld in d.get("layers") or []:
        try:
            if ld.get("kind") == "sticker":
                img = make_sticker(ld.get("sticker") or ld.get("name") or "물음표 배지")
            else:
                img = load_image(ld["src"])
        except Exception:
            continue
        opts.layers.append(PhotoLayer(img, **{k: ld[k] for k in _LAYER_KEYS if k in ld}))
    bg = None
    if d.get("background") and Path(d["background"]).is_file():
        try:
            bg = load_image(d["background"])
        except Exception:
            bg = None
    return opts, bg


# ──────────────────────────────────────────────────────────────── 자동 후보 (프로그램의 썸네일 만들기에서 호출)
def _title_markup(v: dict) -> str:
    big, big2, emph = str(v.get("big") or "").strip(), str(v.get("big2") or "").strip(), str(v.get("emph") or "").strip()
    t = big + ("\n" + big2 if big2 else "")
    if emph and emph in t:
        t = t.replace(emph, f"[{emph}]", 1)
    return t


def _photo(path, name="사진", **kw):
    return PhotoLayer(load_image(path), name=name, src=str(path), **kw)


def _sticker(kind, **kw):
    return PhotoLayer(make_sticker(kind), name=kind, kind="sticker", sticker=kind, **kw)


def auto_candidates(items: list[dict], size: tuple[int, int], opening: str = "") -> list[tuple[str, Image.Image, dict]]:
    """디자인 프리셋 6종으로 썸네일 후보 → [(설명, 이미지, 편집 상태)].
    items: AI 문구 시안 [{big, big2, emph, small, mood, main: 대표 사진 경로, related: [관련 사진 경로]}]
    opening: 영상 첫 장면 사진 (규칙: 첫 5초 = 썸네일의 약속 → '미스터리 다큐' 후보의 배경)"""
    out = []
    if not items:
        return out
    portrait = size[1] > size[0]
    for n, (pname, preset) in enumerate(DESIGN_PRESETS.items()):
        k = n % len(items)
        v = items[k]
        main = v.get("main") or opening
        rel = [p for p in (v.get("related") or []) if p and p != main]
        if not main:
            continue
        o = dict(preset)
        layers: list[PhotoLayer] = []
        bg = main
        try:
            if pname == "미스터리 다큐":        # 첫 장면 배경 + 대표 사진을 오려 오른쪽에 크게 + 물음표
                bg = opening or main
                hero = main if main != bg else (rel[0] if rel else "")
                if hero:
                    layers.append(_photo(hero, "주인공(누끼)", ai_cutout=True, x=.5 if portrait else .74, y=.40 if portrait else .53,
                                         height=.55 if portrait else .92, shadow=True))
                if v.get("mood") in ("미스터리", "충격"):
                    layers.append(_sticker("물음표 배지", x=.86, y=.16, height=.11 if portrait else .2, rotation=-8))
            elif pname == "클래식 유튜브" and rel:
                layers.append(_photo(rel[0], "폴라로이드", shape="폴라로이드", x=.8 if not portrait else .7, y=.3, height=.42 if not portrait else .25,
                                     rotation=-6, shadow=True))
            elif pname == "속보 뉴스" and rel:
                layers.append(_photo(rel[0], "증거 사진", shape="둥근 모서리", outline=True, x=.79 if not portrait else .5,
                                     y=.32 if not portrait else .3, height=.5 if not portrait else .3, shadow=True))
            elif pname == "네온 SF" and rel:
                layers.append(_photo(rel[0], "원형 컷", shape="원형", outline=True, x=.5, y=.33 if not portrait else .3,
                                     height=.5 if not portrait else .3, shadow=True))
            elif pname == "미니멀":             # 흐린 배경 + 같은 사진의 주인공만 또렷하게
                layers.append(_photo(main, "주인공(누끼)", ai_cutout=True, x=.5, y=.38, height=.72 if not portrait else .45, shadow=True))
                o["text_y"] = 82
        except Exception:
            layers = []
        opts = RenderOptions(size=size, title=_title_markup(v), subtitle=str(v.get("small") or ""), layers=layers,
                             **{kk: vv for kk, vv in o.items() if kk in _OPT_KEYS})
        try:
            bgi = load_image(bg)
            im, _ = render_with_bounds(opts, bgi)
        except Exception:
            continue
        desc = f"{k + 1}안 '{v.get('big', '')} {v.get('big2', '')}' · 새 디자인: {pname}"
        out.append((desc, im, state_dict(opts, str(bg), design=pname, variant=k + 1)))
    return out
