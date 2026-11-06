"""평면(2D) 애니메이션 시험: 한산도 대첩 학익진 — 위에서 본 바다 지도, 배는 납작한 도형 (약 15초, 소리 없음)
python -X utf8 평면애니/한산도_시험.py <결과.mp4>
흐름: 제목 → 일본 수군이 견내량(좁은 바닷길)을 빠져나와 조선 배 몇 척을 쫓음(유인) → 넓은 바다에서 조선 수군이 학 날개처럼 펼침
     → 감싼 채 포를 쏨 → 일본 배가 회색으로 가라앉음"""
import math
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont

OUT = sys.argv[1]
W, H, SS, FPS, SEC = 1920, 1080, 2, 24, 15.0
FONT = "/usr/share/fonts/truetype/nanum/NanumSquare_acEB.ttf"
SEA, SEA2, LAND, LAND2, EDGE = (88, 152, 196), (70, 132, 180), (214, 200, 150), (150, 176, 110), (60, 70, 60)
BLUE, BLUE2, RED, RED2, GRAY = (40, 90, 200), (20, 50, 140), (210, 60, 50), (130, 30, 25), (110, 110, 110)


def ease(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def lerp(a, b, u):
    return a + (b - a) * u


def font(sz):
    return ImageFont.truetype(FONT, sz * SS)


# 땅(아주 단순하게): 왼쪽 위 통영 쪽 반도, 오른쪽 거제도, 아래 한산도 — 위쪽 가운데 좁은 틈이 견내량
LANDS = [
    [(0, 0), (820, 0), (860, 120), (830, 260), (700, 330), (520, 360), (300, 420), (120, 470), (0, 480)],          # 통영 쪽
    [(980, 0), (1920, 0), (1920, 760), (1760, 700), (1600, 560), (1400, 430), (1180, 330), (1010, 230), (960, 110)],  # 거제도
    [(1280, 860), (1400, 800), (1540, 820), (1600, 900), (1560, 990), (1420, 1030), (1300, 990), (1240, 930)],         # 한산도
]


def ship(d, x, y, ang, col, dark, scale=1.0, alpha=255):
    """납작한 배: 뾰족한 뱃머리 + 네모 몸통 + 가운데 줄"""
    L, B = 46 * scale, 18 * scale
    pts = [(L * 0.62, 0), (L * 0.28, -B / 2), (-L * 0.45, -B / 2), (-L * 0.5, 0), (-L * 0.45, B / 2), (L * 0.28, B / 2)]
    c, s = math.cos(ang), math.sin(ang)
    P = [((x + px * c - py * s) * SS, (y + px * s + py * c) * SS) for px, py in pts]
    d.polygon(P, fill=col + (alpha,), outline=dark + (alpha,), width=2 * SS)
    d.line([((x - L * 0.3 * c) * SS, (y - L * 0.3 * s) * SS), ((x + L * 0.2 * c) * SS, (y + L * 0.2 * s) * SS)], fill=dark + (alpha,), width=3 * SS)


# 일본 수군 20척: 견내량에서 나와 남동쪽(한산도 앞바다)으로
JP = [(i % 5, i // 5) for i in range(20)]
# 조선 유인선 4척, 본대 18척(한산도 앞에 숨어 있다가 학익진)
CENTER = (1180, 700)     # 학익진 둥근 품의 가운데
R_WING = 330


def jp_pos(k, t):
    col, row = JP[k]
    sx, sy = 900 + (col - 2) * 34, 40 + row * 46                 # 견내량 안쪽 줄
    ex, ey = 1040 + (col - 2) * 60 + row * 18, 560 + row * 50 - abs(col - 2) * 8   # 학익진 품 안
    u = ease((t - 1.5) / 7.0)
    x, y = lerp(sx, ex, u), lerp(sy, ey, u)
    ang = math.atan2(ey - sy, ex - sx)
    return x, y, ang


def decoy_pos(k, t):
    sx, sy = 900 + (k - 1.5) * 50, 330
    ex, ey = 1240 + (k - 1.5) * 70, 860
    u = ease((t - 1.0) / 6.0)
    return lerp(sx, ex, u), lerp(sy, ey, u), math.atan2(ey - sy, ex - sx)


def kr_pos(k, t):
    n = 18
    sx, sy = 1500 + (k % 6) * 24, 760 + (k // 6) * 40               # 한산도 뒤쪽에 모여 있음
    a = math.radians(200 + 140 * k / (n - 1))                        # 반원(학 날개): 왼쪽 아래 ~ 오른쪽 위
    ex, ey = CENTER[0] + R_WING * math.cos(a) * 1.25, CENTER[1] + R_WING * math.sin(a) * 0.9 + 120
    u = ease((t - 4.0) / 3.5)
    x, y = lerp(sx, ex, u), lerp(sy, ey, u)
    face = math.atan2(CENTER[1] - y, CENTER[0] - x)                  # 펼친 뒤엔 가운데(적)를 봄
    move = math.atan2(ey - sy, ex - sx)
    return x, y, (move if u < 0.85 else face)


def text_box(d, xy, s, sz, fill=(255, 255, 255), bg=(20, 30, 50), a=230):
    f = font(sz)
    x, y = xy[0] * SS, xy[1] * SS
    bb = d.textbbox((x, y), s, font=f, anchor="mm")
    pad = 14 * SS
    d.rounded_rectangle((bb[0] - pad, bb[1] - pad * 0.6, bb[2] + pad, bb[3] + pad * 0.6), 12 * SS, fill=bg + (a,))
    d.text((x, y), s, font=f, fill=fill + (int(a * 255 / 230) if a < 230 else 255,), anchor="mm")


def frame(t):
    im = Image.new("RGBA", (W * SS, H * SS), SEA + (255,))
    d = ImageDraw.Draw(im, "RGBA")
    for i in range(0, H, 60):                                          # 잔물결 줄
        d.line([(0, (i + 20 * math.sin(t + i)) * SS), (W * SS, (i + 20 * math.sin(t + i + 1)) * SS)], fill=SEA2 + (60,), width=2 * SS)
    for poly in LANDS:
        d.polygon([(x * SS, y * SS) for x, y in poly], fill=LAND + (255,), outline=EDGE + (255,), width=3 * SS)
        cx, cy = sum(p[0] for p in poly) / len(poly), sum(p[1] for p in poly) / len(poly)
        d.ellipse(((cx - 90) * SS, (cy - 50) * SS, (cx + 90) * SS, (cy + 50) * SS), fill=LAND2 + (255,))
    for (x, y, s) in ((905, 175, "견내량"), (1420, 915, "한산도"), (1600, 220, "거제도"), (260, 230, "통영")):
        d.text((x * SS, y * SS), s, font=font(30), fill=(40, 50, 40, 255), anchor="mm")
    # 포 쏘기·가라앉기
    fire = 8.0 <= t < 12.5
    sink = ease((t - 10.0) / 3.0)
    for k in range(20):
        x, y, a = jp_pos(k, t)
        hit = sink * (1 if (k * 7) % 10 < 8 else 0.25)              # 대부분 가라앉고 몇 척은 남음
        col = tuple(int(lerp(c, g, hit)) for c, g in zip(RED, GRAY))
        ship(d, x, y, a, col, RED2, scale=1 - 0.35 * hit, alpha=int(255 * (1 - 0.7 * hit)))
    for k in range(4):
        x, y, a = decoy_pos(k, t)
        ship(d, x, y, a, BLUE, BLUE2)
    kr = [kr_pos(k, t) for k in range(18)]
    for k, (x, y, a) in enumerate(kr):
        ship(d, x, y, a, (30, 30, 40) if k == 8 else BLUE, BLUE2, scale=1.1 if k == 8 else 1.0)   # 가운데 한 척은 거북선(검게)
    if fire:
        for k, (x, y, a) in enumerate(kr):
            ph = (t * 3 + k * 0.37) % 1.0
            if ph < 0.35:
                tx, ty, _ = jp_pos((k * 3) % 20, t)
                u = ph / 0.35
                bx, by = lerp(x, tx, u), lerp(y, ty, u)
                d.ellipse(((bx - 5) * SS, (by - 5) * SS, (bx + 5) * SS, (by + 5) * SS), fill=(255, 220, 80, 255))
                if u < 0.25:
                    d.ellipse(((x - 16) * SS, (y - 16) * SS, (x + 16) * SS, (y + 16) * SS), fill=(255, 240, 200, 160))
    # 학익진 날개 선 (펼친 뒤 점선으로)
    wing = ease((t - 6.5) / 1.5) * (1 - ease((t - 12.5) / 1.0))
    if wing > 0:
        pts = [(x, y) for x, y, _ in kr]
        for i in range(len(pts) - 1):
            if i % 2 == 0:
                d.line([(pts[i][0] * SS, pts[i][1] * SS), (pts[i + 1][0] * SS, pts[i + 1][1] * SS)], fill=(255, 255, 255, int(200 * wing)), width=4 * SS)
        text_box(d, (CENTER[0], CENTER[1] - 250), "학익진 — 학이 날개를 펼친 모양", 40, a=int(230 * wing))
    # 자막·이름표
    if t < 3.0:
        a = int(255 * min(1, t / 0.5) * (1 - ease((t - 2.4) / 0.6)))
        text_box(d, (W / 2, H / 2), "한산도 대첩 · 1592년", 72, a=min(230, a))
    if 1.5 <= t < 6.5:
        text_box(d, (560, 620), "일본 수군 → 좁은 견내량을 빠져나와 추격", 34, bg=(120, 30, 25), a=210)
    if 3.5 <= t < 7.5:
        text_box(d, (1560, 640), "조선 수군 → 넓은 바다로 끌어냄", 34, bg=(20, 50, 140), a=210)
    if t >= 12.5:
        text_box(d, (W / 2, 120), "감싸서 한꺼번에 공격 → 조선 수군의 큰 승리", 46, a=int(230 * ease((t - 12.5) / 0.6)))
    return im.resize((W, H), Image.LANCZOS).convert("RGB")


p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                      "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", "-movflags", "+faststart", OUT], stdin=subprocess.PIPE)
for i in range(int(SEC * FPS)):
    p.stdin.write(frame(i / FPS).tobytes())
p.stdin.close()
p.wait()
print("OK", OUT)
