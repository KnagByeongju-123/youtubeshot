"""실화 9편(몬테베르데)·10편(술라웨시 손자국)의 지도·연표·도표 그림 만들기 (1920×1080, 인터넷 사진이 없어도 되는 설명 화면)
python 실화/조사/지도연표_만들기.py [저장폴더]      (기본: 실화/그림)
  - 필요: matplotlib, numpy, pyshp  (pip install matplotlib numpy pyshp)
  - 지도 자료는 처음 한 번 자동으로 받아 output/_geo 에 둠 (깃에 안 올림):
      해안선 = Natural Earth (퍼블릭 도메인), 빙하기 해안선 = NOAA ETOPO 해저 지형(퍼블릭 도메인)에서 해수면 -120m 선
  - 화면 아래 약 1/4 은 자막 자리라 중요한 글자를 두지 않음, 왼쪽 위는 프로그램 제목 자리라 비워 둠
  - 숫자는 실화/조사/*_사실확인.md 기준 (확인된 것만, 논쟁 중인 것은 '주장'·'보도'로 표시)"""
import csv
import io
import os
import sys
import urllib.request
import zipfile

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import FancyArrowPatch, Rectangle, FancyBboxPatch
import numpy as np
import shapefile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
GEO = os.path.join(ROOT, "output", "_geo")
OUT = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.path.join(ROOT, "실화", "그림")

BG, LAND, LAND_OLD, SEA, GRID = "#0B0F1A", "#3A4357", "#7A6A4F", "#0F1A2E", "#1E2A40"
CYAN, AMBER, RED, GREEN, WHITE, GREY = "#4FC3F7", "#FFB74D", "#EF5350", "#81C784", "#FFFFFF", "#9AA4B8"
W, H = 19.2, 10.8          # 인치 (dpi 100 → 1920×1080)
SAFE_BOTTOM = 0.27         # 아래 자막 자리 (그림 높이 비율)


def font():
    for p in ("/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf", r"C:\Windows\Fonts\malgunbd.ttf",
              "/System/Library/Fonts/AppleSDGothicNeo.ttc"):
        if os.path.exists(p):
            font_manager.fontManager.addfont(p)
            return font_manager.FontProperties(fname=p).get_name()
    return "sans-serif"


plt.rcParams["font.family"] = font()
plt.rcParams["axes.unicode_minus"] = False


def fetch(url, path):
    if not os.path.exists(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        print("받는 중:", url)
        data = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "youtubeshot-maps/1.0"}), timeout=300).read()
        open(path, "wb").write(data)
    return path


def land_shapes(res="50m"):
    z = fetch(f"https://naciscdn.org/naturalearth/{res}/physical/ne_{res}_land.zip", os.path.join(GEO, f"ne_{res}_land.zip"))
    zf = zipfile.ZipFile(z)
    names = {os.path.splitext(n)[1]: n for n in zf.namelist() if n.startswith(f"ne_{res}_land.")}
    r = shapefile.Reader(shp=io.BytesIO(zf.read(names[".shp"])), dbf=io.BytesIO(zf.read(names[".dbf"])), shx=io.BytesIO(zf.read(names[".shx"])))
    polys = []
    for s in r.shapes():
        pts, parts = s.points, list(s.parts) + [len(s.points)]
        for a, b in zip(parts[:-1], parts[1:]):
            polys.append(np.array(pts[a:b]))
    return polys


def etopo(name, lat0, lat1, lon0, lon1):
    url = ("https://coastwatch.pfeg.noaa.gov/erddap/griddap/etopo180.csv?altitude"
           f"%5B({lat0}):6:({lat1})%5D%5B({lon0}):6:({lon1})%5D")
    p = fetch(url, os.path.join(GEO, f"etopo_{name}.csv"))
    rows = list(csv.reader(open(p, encoding="utf-8")))[2:]
    a = np.array(rows, dtype=float)
    lats, lons = np.unique(a[:, 0]), np.unique(a[:, 1])
    z = a[:, 2].reshape(len(lats), len(lons))
    return lons, lats, z


def canvas():
    fig = plt.figure(figsize=(W, H), dpi=100, facecolor=BG)
    return fig


def title(fig, t, sub=None):
    fig.text(0.5, 0.94, t, ha="center", va="center", color=WHITE, fontsize=40)
    if sub:
        fig.text(0.5, 0.885, sub, ha="center", va="center", color=GREY, fontsize=22)


def credit(fig, t):
    """출처 표시: 오른쪽 아래 구석에 작게 (위는 제목, 가운데 아래는 자막 자리)"""
    fig.text(0.992, 0.012, t, ha="right", va="bottom", color="#5E6880", fontsize=12)


def save(fig, name):
    os.makedirs(OUT, exist_ok=True)
    p = os.path.join(OUT, name + ".png")
    fig.savefig(p, dpi=100, facecolor=fig.get_facecolor())
    plt.close(fig)
    print("저장:", p)


def map_axes(fig, lon0, lon1, lat0, lat1, rect):
    ax = fig.add_axes(rect, facecolor=SEA)
    ax.set_xlim(lon0, lon1)
    ax.set_ylim(lat0, lat1)
    ax.set_aspect(1 / np.cos(np.radians((lat0 + lat1) / 2)))
    ax.set_xticks([])
    ax.set_yticks([])
    for s in ax.spines.values():
        s.set_color(GRID)
    return ax


def draw_land(ax, polys, color=LAND, z=2):
    x0, x1 = ax.get_xlim()
    y0, y1 = ax.get_ylim()
    for p in polys:
        if p[:, 0].max() < x0 - 5 or p[:, 0].min() > x1 + 5 or p[:, 1].max() < y0 - 5 or p[:, 1].min() > y1 + 5:
            continue
        ax.fill(p[:, 0], p[:, 1], color=color, lw=0.4, ec="#55607A", zorder=z)


def star(ax, x, y, label, color=AMBER, dx=1.0, dy=0.0, size=26, ha="left", fs=24):
    ax.plot(x, y, marker="*", ms=size, color=color, mec=BG, mew=1.5, zorder=10)
    ax.text(x + dx, y + dy, label, color=color, fontsize=fs, ha=ha, va="center", zorder=11,
            bbox=dict(boxstyle="round,pad=0.25", fc=BG, ec="none", alpha=0.75))


def dot(ax, x, y, label, color=CYAN, dx=1.0, dy=0.0, ha="left", fs=20):
    ax.plot(x, y, "o", ms=12, color=color, mec=BG, mew=1.5, zorder=10)
    ax.text(x + dx, y + dy, label, color=color, fontsize=fs, ha=ha, va="center", zorder=11,
            bbox=dict(boxstyle="round,pad=0.2", fc=BG, ec="none", alpha=0.7))


def arrow(ax, pts, color, lw=6, style="-|>"):
    pts = np.array(pts, dtype=float)
    ax.plot(pts[:-1, 0], pts[:-1, 1], color=color, lw=lw, solid_capstyle="round", zorder=8, alpha=0.95)
    ax.add_patch(FancyArrowPatch(pts[-2], pts[-1], arrowstyle=style, mutation_scale=40, color=color, lw=lw, zorder=8))


def iceage(ax, lons, lats, z, depth=-120):
    """오늘은 바다지만 빙하기(해수면 -120m)엔 땅이던 곳을 황토색으로"""
    ax.contourf(lons, lats, z, levels=[depth, 0.0001], colors=[LAND_OLD], zorder=1, alpha=0.95)


# ---------------------------------------------------------------- 9편 몬테베르데
def mv_01_sites(polys):
    fig = canvas()
    title(fig, "아메리카 최초 인류의 흔적들", "논쟁의 중심, 칠레 남부 몬테베르데")
    ax = map_axes(fig, -135, -30, -58, 66, [0.30, SAFE_BOTTOM - 0.02, 0.40, 0.84 - SAFE_BOTTOM + 0.02])
    draw_land(ax, polys)
    star(ax, -73.2, -41.5, "몬테베르데 (칠레)", AMBER, dx=3, fs=26, size=34)
    dot(ax, -106.3, 32.8, "화이트샌즈 발자국", CYAN, dx=-2.5, ha="right")
    dot(ax, -116.4, 45.8, "쿠퍼스 페리", CYAN, dx=-2.5, ha="right")
    dot(ax, -103.2, 34.4, "클로비스", GREEN, dx=2.5)
    credit(fig, "지도: Natural Earth (퍼블릭 도메인) · 위치는 대략")
    save(fig, "9_몬테베르데_01_유적위치")


def mv_02_beringia(polys):
    fig = canvas()
    title(fig, "빙하기, 아시아와 아메리카를 잇던 땅", "베링 육교 — 바닷물이 줄어 드러난 땅 (해수면 약 120m 낮을 때)")
    lw, latw, zw = etopo("bering_w", 48, 74, 140, 180)
    le, late, ze = etopo("bering_e", 48, 74, -180, -120)
    # 날짜변경선을 넘으므로 동경을 0~360 으로 이어 붙여 그림
    lons = np.concatenate([lw, le + 360])
    z = np.concatenate([zw, ze], axis=1)
    ax = map_axes(fig, 145, 235, 50, 74, [0.06, SAFE_BOTTOM, 0.88, 0.84 - SAFE_BOTTOM])
    iceage(ax, lons, latw, z)
    # Natural Earth 땅 조각은 날짜변경선에서 잘려 있으므로, 서경 조각을 통째로 +360 옮긴 사본을 함께 그림
    draw_land(ax, polys + [np.column_stack([p[:, 0] + 360, p[:, 1]]) for p in polys if p[:, 0].max() < 0])
    ax.text(160, 66, "아시아", color=WHITE, fontsize=34, ha="center", zorder=12)
    ax.text(213, 66, "북아메리카", color=WHITE, fontsize=34, ha="center", zorder=12)
    ax.text(190, 59.2, "베링 육교 (지금은 바다)", color=AMBER, fontsize=28, ha="center", zorder=12,
            bbox=dict(boxstyle="round,pad=0.3", fc=BG, ec=AMBER, alpha=0.8))
    ax.add_patch(Rectangle((0, 0), 0, 0, color=LAND_OLD, label="빙하기에만 드러난 땅"))
    ax.add_patch(Rectangle((0, 0), 0, 0, color=LAND, label="지금의 땅"))
    ax.legend(loc="lower right", fontsize=18, facecolor=BG, edgecolor=GRID, labelcolor=WHITE)
    credit(fig, "해안선: Natural Earth · 해저 지형: NOAA ETOPO (퍼블릭 도메인)")
    save(fig, "9_몬테베르데_02_베링육교")


def mv_03_routes(polys):
    fig = canvas()
    title(fig, "처음 온 사람들은 어느 길로 왔을까", "두 가지 가설: 태평양 해안 길 vs 내륙 '얼음 없는 통로'")
    ax = map_axes(fig, -175, -30, -58, 72, [0.27, SAFE_BOTTOM - 0.02, 0.46, 0.84 - SAFE_BOTTOM + 0.02])
    draw_land(ax, polys)
    arrow(ax, [(-168, 64), (-150, 59), (-135, 55), (-127, 47), (-121, 36), (-108, 22), (-90, 10), (-82, 0), (-80, -12),
               (-74, -26), (-74, -40)], CYAN)
    arrow(ax, [(-160, 66), (-140, 64), (-123, 58), (-114, 51), (-106, 42)], AMBER)
    ax.text(-140, 46, "해안 길", color=CYAN, fontsize=28, ha="right", zorder=12,
            bbox=dict(boxstyle="round,pad=0.25", fc=BG, ec="none", alpha=0.8))
    ax.text(-100, 55, "내륙 통로", color=AMBER, fontsize=28, ha="left", zorder=12,
            bbox=dict(boxstyle="round,pad=0.25", fc=BG, ec="none", alpha=0.8))
    star(ax, -73.2, -41.5, "몬테베르데", AMBER, dx=3, fs=24, size=30)
    fig.text(0.745, 0.66, "몬테베르데가\n1만 4,500년 전이라면\n→ 해안 길 가설에 힘", color=CYAN, fontsize=22, ha="left", va="center", linespacing=1.5)
    fig.text(0.745, 0.44, "8,200년보다 젊다면\n(수로벨 팀 주장)\n→ 내륙 이주 가능성", color=AMBER, fontsize=22, ha="left", va="center", linespacing=1.5)
    credit(fig, "지도: Natural Earth · 경로는 개념도 (실제 길은 모름)")
    save(fig, "9_몬테베르데_03_두가지길")


def timeline_axes(fig, x0, x1, rect, ticks, label="년 전"):
    ax = fig.add_axes(rect, facecolor=BG)
    ax.set_xlim(x0, x1)          # 왼쪽이 더 오래전
    ax.set_ylim(0, 1)
    ax.set_yticks([])
    ax.set_xticks([])
    for t in ticks:
        ax.text(t, -0.06, f"{t:,}", ha="center", va="top", color=GREY, fontsize=18)
    for k in ("top", "left", "right"):
        ax.spines[k].set_visible(False)
    ax.spines["bottom"].set_color(GREY)
    ax.text(1.0, -0.16, label, transform=ax.transAxes, ha="right", va="top", color=GREY, fontsize=18)
    for t in ticks:
        ax.axvline(t, color=GRID, lw=1, zorder=0)
    return ax


def mv_04_timeline():
    fig = canvas()
    title(fig, "아메리카 첫 인류 — 증거들의 나이", "숫자는 각 연구팀이 발표한 값 (몬테베르데는 두 주장이 맞섬)")
    ax = timeline_axes(fig, 25000, 0, [0.06, SAFE_BOTTOM + 0.04, 0.88, 0.52], list(range(25000, -1, -5000)))
    rows = [(0.88, 23000, 21000, "화이트샌즈 발자국 (미국)", CYAN),
            (0.70, 16600, 15300, "쿠퍼스 페리 (미국)", CYAN),
            (0.52, 14600, 14400, "몬테베르데 — 원래 연대 약 1만 4,500년", AMBER),
            (0.34, 8200, 4200, "몬테베르데 — 2026 수로벨 팀 주장 (8,200년보다 젊다)", RED),
            (0.16, 13100, 12900, "클로비스 문화 (약 1만 3,000년)", GREEN)]
    for y, a, b, lab, c in rows:
        ax.add_patch(Rectangle((b, y - 0.05), a - b, 0.1, fc=c, ec="none", zorder=3))
        right = b > 12000
        ax.text(b - 400 if right else a + 400, y, lab, color=c, fontsize=24, va="center", ha="left" if right else "right", zorder=4)
    credit(fig, "출처: Science 2021·2023(화이트샌즈), 2019(쿠퍼스 페리), 2026(수로벨 외) / 사실확인.md")
    save(fig, "9_몬테베르데_04_연표")


def mv_05_versus():
    fig = canvas()
    title(fig, "같은 유적, 두 개의 나이")
    for x, c, big, who, lines in [
        (0.27, AMBER, "1만 4,500년 전", "원래 발굴팀 (톰 딜레이 외)", ["50년 발굴 · 유물 수백 점", "나무 창, 엄니 도구, 해초를 직접 연대 측정", "1997년 전문가 현장 점검으로 인정"]),
        (0.73, RED, "8,200년보다 젊다", "2026 재조사팀 (토드 수로벨 외)", ["개울가 9곳 퇴적층 재측정", "유적 아래 1만 1천 년 전 화산재가 있다고 주장", "'오래된 나무가 쓸려 와 섞였다'"])]:
        fig.patches.append(FancyBboxPatch((x - 0.21, SAFE_BOTTOM + 0.02), 0.42, 0.56, boxstyle="round,pad=0.01,rounding_size=0.02",
                                          transform=fig.transFigure, fc="#121A2B", ec=c, lw=3))
        fig.text(x, 0.76, big, ha="center", color=c, fontsize=56)
        fig.text(x, 0.665, who, ha="center", color=WHITE, fontsize=24)
        for i, l in enumerate(lines):
            fig.text(x, 0.57 - i * 0.075, "· " + l, ha="center", color=GREY, fontsize=21)
    fig.text(0.5, 0.52, "VS", ha="center", va="center", color=WHITE, fontsize=48)
    credit(fig, "Science 391:1283 (2026) · Science eLetters (2026-05) · American Antiquity 62(4) (1997)")
    save(fig, "9_몬테베르데_05_두주장")


def column(fig, x, top, layers, heading, hc, note):
    fig.text(x, top + 0.035, heading, ha="center", color=hc, fontsize=26)
    y = top
    for h, color, label, lc in layers:
        fig.patches.append(Rectangle((x - 0.17, y - h), 0.34, h, transform=fig.transFigure, fc=color, ec=BG, lw=2))
        fig.text(x, y - h / 2, label, ha="center", va="center", color=lc, fontsize=20)
        y -= h
    fig.text(x, y - 0.035, note, ha="center", va="top", color=hc, fontsize=21)


def mv_06_layers():
    fig = canvas()
    title(fig, "화산재는 땅속 시계", "위에 쌓인 흙은 아래 화산재보다 젊다")
    SOIL, ASH, SITE = "#5D4A36", "#C9C4B8", "#B3743A"
    column(fig, 0.27, 0.80, [(0.08, SOIL, "흙", WHITE), (0.09, SITE, "유적 층", WHITE),
                              (0.06, ASH, "화산재 약 1만 1,000년 전", BG), (0.08, SOIL, "더 오래된 흙", WHITE)],
           "수로벨 팀의 주장", RED, "화산재가 유적 '아래'\n→ 유적은 1만 1천 년보다 젊다")
    column(fig, 0.73, 0.80, [(0.05, SOIL, "흙", WHITE), (0.05, ASH, "화산재 약 8,500년 전", BG),
                              (0.05, ASH, "화산재 약 1만 1,000년 전", BG), (0.09, SITE, "유적 층", WHITE), (0.07, SOIL, "더 오래된 흙", WHITE)],
           "반박 측 (2026년 10월 학회 보도)", AMBER, "화산재가 유적 '위'\n→ 유적은 그보다 오래됐다")
    credit(fig, "개념 그림 (두께는 실제와 다름) · 학회 발표 내용은 논문 심사 전")
    save(fig, "9_몬테베르데_06_화산재시계")


def mv_07_2026():
    fig = canvas()
    title(fig, "2026년, 몬테베르데 논쟁 일지")
    ev = [("3월 19일", "사이언스 논문", "'8,200년보다 오래될 수 없다'", RED),
          ("5월 4~5일", "반박 글 3편", "학자 30명이 이름을 올림", AMBER),
          ("8월 말", "학술지 PaleoAmerica", "추가 반론 실림 (로이터 보도)", AMBER),
          ("10월 15~17일", "미국 산타페 학회", "새 시험 구덩이 4개 공개 (보도)", CYAN)]
    y = 0.60
    fig.add_artist(plt.Line2D([0.1, 0.9], [y, y], transform=fig.transFigure, color=GREY, lw=3))
    for i, (d, a, b, c) in enumerate(ev):
        x = 0.16 + i * 0.226
        fig.add_artist(plt.Line2D([x], [y], transform=fig.transFigure, marker="o", ms=26, color=c, mec=BG, mew=3))
        fig.text(x, y + 0.085, d, ha="center", color=c, fontsize=28)
        fig.text(x, y - 0.08, a, ha="center", color=WHITE, fontsize=24)
        fig.text(x, y - 0.14, b, ha="center", color=GREY, fontsize=19)
    credit(fig, "AP · Live Science · Reuters · Science 뉴스 (2026)")
    save(fig, "9_몬테베르데_07_2026일지")


# ---------------------------------------------------------------- 10편 술라웨시 손자국
def sw_01_location(polys):
    fig = canvas()
    title(fig, "무대는 인도네시아 술라웨시", "6만 7,800년 전 손자국이 나온 무나섬")
    ax = map_axes(fig, 112, 132, -10.5, 4.5, [0.10, SAFE_BOTTOM - 0.02, 0.80, 0.84 - SAFE_BOTTOM + 0.02])
    draw_land(ax, polys)
    star(ax, 122.6, -4.9, "무나섬 — 리앙 메탄두노 동굴", AMBER, dx=0.6, fs=26, size=34)
    dot(ax, 119.7, -4.95, "마로스-팡켑 (이전 기록들)", CYAN, dx=-0.5, ha="right")
    for x, y, t in [(114.5, 0.5, "보르네오"), (120.6, -1.4, "술라웨시"), (113.8, -7.0, "자바"), (128.6, -3.3, "말루쿠 제도")]:
        ax.text(x, y, t, color=WHITE, fontsize=26, ha="center", zorder=12)
    credit(fig, "지도: Natural Earth (퍼블릭 도메인) · 위치는 대략")
    save(fig, "10_술라웨시_01_위치")


def sw_02_sahul(polys):
    fig = canvas()
    title(fig, "빙하기의 순다와 사훌, 그리고 두 갈래 바닷길", "바닷물이 낮을 때 드러난 땅 (해수면 약 120m 낮을 때)")
    lons, lats, z = etopo("sunda", -16, 12, 90, 156)
    ax = map_axes(fig, 92, 154, -15, 10, [0.05, SAFE_BOTTOM - 0.02, 0.90, 0.84 - SAFE_BOTTOM + 0.02])
    iceage(ax, lons, lats, z)
    draw_land(ax, polys)
    ax.text(105, 2.5, "순다", color=WHITE, fontsize=40, ha="center", zorder=12)
    ax.text(140, -10.5, "사훌", color=WHITE, fontsize=40, ha="center", zorder=12)
    arrow(ax, [(112, -0.5), (117.5, -1.5), (121.5, -3.0), (127.5, -2.5), (132, -3.0), (135, -4.0)], CYAN)
    arrow(ax, [(110, -7.6), (116.5, -8.6), (121, -9.0), (125, -9.6), (128.5, -12.5)], AMBER)
    ax.text(126, 0.6, "북쪽 길", color=CYAN, fontsize=28, ha="center", zorder=12,
            bbox=dict(boxstyle="round,pad=0.25", fc=BG, ec="none", alpha=0.8))
    ax.text(118, -11.4, "남쪽 길", color=AMBER, fontsize=28, ha="center", zorder=12,
            bbox=dict(boxstyle="round,pad=0.25", fc=BG, ec="none", alpha=0.8))
    star(ax, 122.6, -4.9, "무나섬", RED, dx=0.6, dy=-0.9, fs=24, size=30)
    ax.add_patch(Rectangle((0, 0), 0, 0, color=LAND_OLD, label="빙하기에만 드러난 땅"))
    ax.add_patch(Rectangle((0, 0), 0, 0, color=LAND, label="지금의 땅"))
    ax.legend(loc="lower left", fontsize=18, facecolor=BG, edgecolor=GRID, labelcolor=WHITE)
    credit(fig, "해안선: Natural Earth · 해저 지형: NOAA ETOPO · 경로는 개념도")
    save(fig, "10_술라웨시_02_순다사훌")


def sw_03_oldest():
    fig = canvas()
    title(fig, "가장 오래된 그림들 — '적어도' 몇 년 전?", "막대 끝 = 측정된 최소 나이 (실제는 더 오래됐을 수 있음)")
    rows = [("블롬보스 (남아공) — 돌 조각의 빗금, 약", 73000, GREEN),
            ("무나섬 손자국 (인도네시아, 2026)", 67800, AMBER),
            ("말트라비에소 손 (스페인, 2018)", 66700, CYAN),
            ("아르달레스 붉은 종유석 (스페인)", 65500, CYAN),
            ("라 파시에가 붉은 선 (스페인)", 64800, CYAN),
            ("레앙 카람푸앙 이야기 그림 (술라웨시)", 51200, AMBER),
            ("레앙 테동게 혹멧돼지 (술라웨시)", 45500, AMBER),
            ("엘 카스티요 붉은 원반 (스페인)", 40800, CYAN),
            ("쇼베 동굴 (프랑스), 약", 37000, CYAN)]
    ax = fig.add_axes([0.40, SAFE_BOTTOM - 0.01, 0.55, 0.60], facecolor=BG)
    n = len(rows)
    for i, (lab, v, c) in enumerate(rows):
        y = n - 1 - i
        ax.barh(y, v, height=0.62, color=c, zorder=3)
        ax.text(v + 600, y, f"{v:,}년", va="center", color=WHITE, fontsize=19, zorder=4)
        ax.text(-1500, y, lab, va="center", ha="right", color=c, fontsize=19)
    ax.set_xlim(0, 82000)
    ax.set_ylim(-0.6, n - 0.4)
    ax.axis("off")
    for i, (t, c) in enumerate([("아시아", AMBER), ("유럽", CYAN), ("아프리카", GREEN)]):
        fig.text(0.80, 0.46 - i * 0.05, "■ " + t, color=c, fontsize=24, ha="left")
    credit(fig, "Nature 2026·2024·2018 · Science 2018·2012 · Sci. Adv. 2021 · PNAS 2016")
    save(fig, "10_술라웨시_03_오래된그림비교")


def sw_04_records():
    fig = canvas()
    title(fig, "술라웨시, 기록을 계속 갈아 치우다", "발표된 해에 따른 '가장 오래된 그림' 최소 나이")
    pts = [(2014, 39900, "손 그림\n3만 9,900년"), (2019, 43900, "사냥 장면\n4만 3,900년"), (2021, 45500, "혹멧돼지\n4만 5,500년"),
           (2024, 51200, "이야기 그림\n5만 1,200년"), (2026, 67800, "무나섬 손자국\n6만 7,800년")]
    ax = fig.add_axes([0.10, SAFE_BOTTOM + 0.03, 0.80, 0.52], facecolor=BG)
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    ax.plot(xs, ys, color=AMBER, lw=5, zorder=2)
    ax.scatter(xs, ys, s=500, color=AMBER, edgecolor=BG, linewidth=3, zorder=3)
    for x, y, t in pts:
        ax.text(x, y + 3500, t, ha="center", va="bottom", color=WHITE, fontsize=20)
    ax.set_xlim(2012.5, 2027.5)
    ax.set_ylim(30000, 82000)
    ax.set_xticks(xs)
    ax.set_xticklabels([f"{x}년" for x in xs], color=GREY, fontsize=20)
    ax.set_yticks([])
    for k in ("top", "left", "right"):
        ax.spines[k].set_visible(False)
    ax.spines["bottom"].set_color(GREY)
    credit(fig, "Nature 2014 · Nature 2019 · Science Advances 2021 · Nature 2024 · Nature 2026")
    save(fig, "10_술라웨시_04_기록경신")


def sw_05_minage():
    fig = canvas()
    title(fig, "돌 껍질로 재는 '최소 나이'", "그림 위에 나중에 쌓인 껍질의 나이 = 그림의 가장 젊은 나이")
    ax = fig.add_axes([0.08, SAFE_BOTTOM + 0.02, 0.84, 0.56], facecolor=BG)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 50)
    ax.axis("off")
    ax.add_patch(Rectangle((5, 5), 22, 40, fc="#6B6F7A", ec="none"))
    ax.text(16, 25, "동굴\n벽", color=WHITE, fontsize=30, ha="center", va="center")
    ax.add_patch(Rectangle((27, 5), 3.5, 40, fc="#B5523B", ec="none"))
    ax.add_patch(Rectangle((30.5, 5), 7, 40, fc="#E8E1D0", ec="none", alpha=0.9))
    ax.annotate("① 붉은 물감 (손 그림)", xy=(28.7, 32), xytext=(45, 40), color="#F08A70", fontsize=26,
                arrowprops=dict(arrowstyle="-|>", color="#F08A70", lw=3))
    ax.annotate("② 그 위에 수만 년 동안 쌓인\n    탄산칼슘 껍질", xy=(34, 20), xytext=(45, 22), color=WHITE, fontsize=26,
                arrowprops=dict(arrowstyle="-|>", color=WHITE, lw=3))
    ax.text(45, 7, "③ 껍질 속 우라늄 → 토륨 비율로 껍질의 나이를 잼\n    → 그림은 적어도 그보다 오래됐다", color=AMBER, fontsize=24)
    credit(fig, "개념 그림 · 레이저 우라늄 계열 연대 측정 (Nature 2026)")
    save(fig, "10_술라웨시_05_최소나이원리")


def sw_06_errors():
    fig = canvas()
    title(fig, "1,100년 앞섰다? — 오차를 함께 보면", "최소 나이끼리 비교하면 사실상 비슷한 시기")
    ax = fig.add_axes([0.10, SAFE_BOTTOM + 0.06, 0.80, 0.46], facecolor=BG)
    ax.errorbar([71600], [1], xerr=[[3800], [3800]], fmt="o", ms=18, color=AMBER, elinewidth=6, capsize=14, capthick=4, zorder=3)
    ax.plot([67800], [1], marker="|", ms=60, mew=5, color=WHITE, zorder=4)
    ax.text(67800, 1.32, "발표된 최소 나이 6만 7,800년", ha="center", color=WHITE, fontsize=20)
    ax.text(71600, 0.68, "측정값 7만 1,600년 ± 3,800년", ha="center", color=AMBER, fontsize=20)
    ax.text(62000, 1, "무나섬 손자국", ha="right", va="center", color=AMBER, fontsize=24)
    ax.plot([66700], [0], marker="|", ms=60, mew=5, color=CYAN, zorder=4)
    ax.annotate("", xy=(78000, 0), xytext=(66700, 0), arrowprops=dict(arrowstyle="-|>", color=CYAN, lw=4, ls="--"))
    ax.text(62000, 0, "말트라비에소 손 (스페인)", ha="right", va="center", color=CYAN, fontsize=24)
    ax.text(72500, -0.32, "최소 6만 6,700년 (그보다 오래됐을 수 있음)", ha="center", color=CYAN, fontsize=20)
    ax.set_xlim(52000, 80000)
    ax.set_ylim(-0.7, 1.6)
    ax.set_yticks([])
    ax.set_xticks([60000, 65000, 70000, 75000, 80000])
    ax.set_xticklabels(["6만", "6만 5천", "7만", "7만 5천", "8만 년 전"], color=GREY, fontsize=18)
    for k in ("top", "left", "right"):
        ax.spines[k].set_visible(False)
    ax.spines["bottom"].set_color(GREY)
    credit(fig, "Nature 2026 (Oktaviana 외) · Science 2018 (Hoffmann 외)")
    save(fig, "10_술라웨시_06_오차비교")


def main():
    polys50 = land_shapes("50m")
    polys10 = land_shapes("10m")
    mv_01_sites(polys50)
    mv_02_beringia(polys50)
    mv_03_routes(polys50)
    mv_04_timeline()
    mv_05_versus()
    mv_06_layers()
    mv_07_2026()
    sw_01_location(polys10)
    sw_02_sahul(polys10)
    sw_03_oldest()
    sw_04_records()
    sw_05_minage()
    sw_06_errors()


if __name__ == "__main__":
    main()
