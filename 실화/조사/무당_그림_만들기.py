"""실화 13편(무당의 역사)의 지도·연표·도표 그림 (1920×1080) — 지도연표_만들기.py 의 그리기 도구를 그대로 씀
python 실화/조사/무당_그림_만들기.py [저장폴더]      (기본: 실화/그림)
  - 숫자·사실은 실화/조사/무당_사실확인.md 기준 (해석인 것은 '해석'·'추정'으로 표시)
  - 아래 약 1/4 은 자막 자리, 오른쪽 위는 사진 설명 자리라 중요한 글자를 두지 않음"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

from 지도연표_만들기 import (AMBER, BG, CYAN, GREEN, GREY, RED, SAFE_BOTTOM, WHITE, canvas, credit, dot, draw_land,
                        land_shapes, map_axes, save, star, title)


def mu_01_map(polys):
    """무당의 흔적을 따라: 세 무덤 + 시베리아 + 신라·제주"""
    fig = canvas()
    title(fig, "무당의 흔적을 따라서", "고대 무덤의 '무당'은 무덤과 부장품을 보고 붙인 해석입니다")
    ax = map_axes(fig, -12, 145, 22, 66, [0.03, SAFE_BOTTOM - 0.02, 0.94, 0.62])
    draw_land(ax, polys)
    star(ax, 35.3, 32.9, "힐라존 타흐티트 · 1만 2,000년 전", AMBER, dx=0, dy=-3.2, ha="center", fs=20)
    star(ax, -0.4, 54.2, "스타 카 · 1만 1,000년 전", CYAN, dx=1.5, dy=3.0, fs=20)
    star(ax, 12.1, 51.3, "바트 뒤렌베르크 · 9,000년 전", GREEN, dx=1.5, dy=-2.6, fs=20)
    dot(ax, 105, 60, "에벤키족 · '샤먼'이란 말의 고향", GREY, dx=0, dy=2.6, ha="center", fs=20)
    dot(ax, 129.2, 35.8, "신라 · 차차웅", RED, dx=-1.5, dy=2.4, ha="right", fs=20)
    dot(ax, 126.5, 33.4, "제주 · 칠머리당 영등굿", RED, dx=-1.5, dy=-2.0, ha="right", fs=20)
    credit(fig, "지도 자료: Natural Earth (퍼블릭 도메인) · 무당_사실확인.md")
    save(fig, "13_무당_01_흔적지도")


def card(fig, x, y, w, h, head, body, color):
    fig.patches.append(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.006,rounding_size=0.015",
                                      transform=fig.transFigure, fc="#121A2B", ec=color, lw=2.5))
    fig.text(x + w / 2, y + h * 0.66, head, ha="center", va="center", color=color, fontsize=27)
    fig.text(x + w / 2, y + h * 0.28, body, ha="center", va="center", color=GREY, fontsize=19)


def mu_02_goods():
    """바트 뒤렌베르크 무덤 속 물건"""
    fig = canvas()
    title(fig, "9,000년 전 무덤에 함께 묻힌 것들", "독일 바트 뒤렌베르크 · 30~40세 여인과 생후 6~8개월 아기")
    items = [("노루뿔 머리장식", "머리 근처에서 거위 깃털 조각 (2025)", GREEN),
             ("짐승 이빨 약 50개", "오록스·들소·멧돼지·사슴 · 구멍 뚫음", AMBER),
             ("멧돼지 엄니", "쪼갠 엄니 · 일부는 구멍 뚫음", AMBER),
             ("작은 돌날 31개", "두루미 뼈로 만든 통에 담김", CYAN),
             ("붉은 흙 (오커)", "", RED),
             ("늪거북 등껍질 3개", "", CYAN)]
    w, h, gx, gy = 0.28, 0.17, 0.03, 0.035
    x0 = (1 - (3 * w + 2 * gx)) / 2
    top = 0.80
    for i, (a, b, c) in enumerate(items):
        r, k = divmod(i, 3)
        card(fig, x0 + k * (w + gx), top - (r + 1) * h - r * gy, w, h, a, b, c)
    credit(fig, "Orschiedt 외 2023 · Porr & Alt 2006 · 작센안할트 문화재청 2025 (위키 정리 기준)")
    save(fig, "13_무당_02_부장품")


def mu_03_bad_timeline():
    """한 여인의 9,000년"""
    fig = canvas()
    title(fig, "한 여인이 기억된 9,000년", "독일 바트 뒤렌베르크")
    ev = [("기원전 7000~6800년", "여인과 아기를 묻음", "앉은 자세 · 노루뿔 머리장식", GREEN),
          ("약 600년 뒤", "무덤 옆에 사슴뿔 머리장식 2개", "새 깃털·나무껍질 섬유 흔적", AMBER),
          ("1934년 5월 4일", "수도관 공사 중 발견", "하루 만에 발굴 · 사진 없음", GREY),
          ("2019년", "다시 발굴", "무덤 흙을 통째로 떠 옴", CYAN),
          ("2025~2026년", "깃털 · 꽃가루 · 특별전", "아기는 아들이 아닌 먼 친척", RED)]
    y = 0.60
    fig.add_artist(plt.Line2D([0.07, 0.93], [y, y], transform=fig.transFigure, color=GREY, lw=3))
    for i, (d, a, b, c) in enumerate(ev):
        x = 0.12 + i * 0.19
        fig.add_artist(plt.Line2D([x], [y], transform=fig.transFigure, marker="o", ms=24, color=c, mec=BG, mew=3))
        fig.text(x, y + 0.08, d, ha="center", color=c, fontsize=23)
        fig.text(x, y - 0.075, a, ha="center", color=WHITE, fontsize=20, wrap=True)
        fig.text(x, y - 0.13, b, ha="center", color=GREY, fontsize=16)
    credit(fig, "Orschiedt 외 2023 · 작센안할트 문화재청 보도 (2025-12) · HeritageDaily (2026-03)")
    save(fig, "13_무당_03_한여인의9000년")


def mu_04_history():
    """무당의 긴 역사 (간격은 실제 비율이 아님)"""
    fig = canvas()
    title(fig, "무당의 긴 역사", "간격은 실제 시간 비율이 아닙니다")
    ev = [("1만 2,000년 전", "이스라엘", "거북 등껍질 무덤", AMBER),
          ("1만 1,000년 전", "영국", "사슴 머리 쓰개 24점", CYAN),
          ("9,000년 전", "독일", "깃털 머리장식의 여인", GREEN),
          ("약 2,000년 전", "신라", "임금 칭호 '차차웅'", RED),
          ("고려", "이규보", "「노무편」 굿 묘사", RED),
          ("2009년", "제주", "영등굿 유네스코 등재", RED)]
    y = 0.60
    fig.add_artist(plt.Line2D([0.05, 0.95], [y, y], transform=fig.transFigure, color=GREY, lw=3))
    for i, (d, a, b, c) in enumerate(ev):
        x = 0.10 + i * 0.16
        fig.add_artist(plt.Line2D([x], [y], transform=fig.transFigure, marker="o", ms=24, color=c, mec=BG, mew=3))
        fig.text(x, y + 0.08, d, ha="center", color=c, fontsize=23)
        fig.text(x, y - 0.075, a, ha="center", color=WHITE, fontsize=22)
        fig.text(x, y - 0.13, b, ha="center", color=GREY, fontsize=17)
    credit(fig, "무당_사실확인.md (PNAS 2008 · PLoS ONE 2016 · 『삼국사기』 · 유네스코 2009)")
    save(fig, "13_무당_04_긴역사")


def main():
    polys = land_shapes("50m")
    mu_01_map(polys)
    mu_02_goods()
    mu_03_bad_timeline()
    mu_04_history()


if __name__ == "__main__":
    main()
