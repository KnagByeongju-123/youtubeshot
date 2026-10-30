"""실화 14편(트로트의 유래)의 설명 그림 (1920×1080) — 지도연표_만들기.py 의 그리기 도구를 그대로 씀
python 실화/조사/트로트_그림_만들기.py [저장폴더]      (기본: 실화/그림)
  - 숫자·사실은 실화/조사/트로트_사실확인.md 기준. 엔카 영향설·독자 발전설은 같은 무게로
  - 아래 약 1/4 은 자막 자리, 오른쪽 위는 사진 설명 자리라 중요한 글자를 두지 않음"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle

from 지도연표_만들기 import AMBER, BG, CYAN, GREEN, GREY, RED, SAFE_BOTTOM, WHITE, canvas, credit, save, title

PINK = "#F48FB1"


def box(fig, x, y, w, h, color, fc="#121A2B", lw=3):
    fig.patches.append(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.008,rounding_size=0.02",
                                      transform=fig.transFigure, fc=fc, ec=color, lw=lw))


def tr_01_question():
    """오프닝: 큰 질문 + 두 숫자"""
    fig = canvas()
    fig.text(0.5, 0.80, "트로트는 일본 엔카에서 왔을까?", ha="center", va="center", color=WHITE, fontsize=62)
    for x, c, big, small in [(0.29, RED, "1965년", "'왜색'이라며 국민가요를 방송 금지"),
                             (0.71, PINK, "35.7%", "2020년 「미스터트롯」 결승 시청률")]:
        box(fig, x - 0.19, SAFE_BOTTOM + 0.08, 0.38, 0.30, c)
        fig.text(x, SAFE_BOTTOM + 0.29, big, ha="center", va="center", color=c, fontsize=64)
        fig.text(x, SAFE_BOTTOM + 0.15, small, ha="center", va="center", color=GREY, fontsize=24)
    credit(fig, "트로트_사실확인.md · 시청률: 닐슨코리아 전국")
    save(fig, "14_트로트_01_질문")


def tr_02_versus():
    """두 주장 (같은 무게)"""
    fig = canvas()
    title(fig, "트로트의 뿌리, 두 주장", "어느 쪽도 아직 결론이 나지 않았습니다")
    sides = [(0.27, AMBER, "엔카의 영향을 받았다", ["2박자 리듬 · 5음 음계가 같다", "기타 반주 · 꾸밈음도 엔카에서", "우리 전통 장단은 3박 · 9박이 많다", "— 작곡가 최창권 (1990)"]),
             (0.73, CYAN, "우리 뿌리가 있다", ["뿌리는 무가 · 민요 · 창가", "리듬이 굿거리장단을 닮았다", "그 음계가 일본만의 것은 아니다", "— 작곡가 박춘석 (1990), 민경찬 · 장유정"])]
    for x, c, head, lines in sides:
        box(fig, x - 0.21, SAFE_BOTTOM + 0.02, 0.42, 0.55, c)
        fig.text(x, 0.765, head, ha="center", color=c, fontsize=36)
        for i, l in enumerate(lines):
            fig.text(x, 0.67 - i * 0.075, l, ha="center", color=GREY if not l.startswith("—") else WHITE, fontsize=22)
    fig.text(0.5, 0.56, "VS", ha="center", va="center", color=WHITE, fontsize=44)
    credit(fig, "경향신문 1990-08-24 · 시사저널 · 문화일보 · 고바야시 다카유키 비교 논문")
    save(fig, "14_트로트_02_두주장")


def tr_03_ban():
    """금지곡 연표"""
    fig = canvas()
    title(fig, "금지된 국민가요", "이미자 「동백 아가씨」")
    ev = [("1950년대 말", "가요 정화 운동", "왜색 논쟁이 떠오름", GREY),
          ("1964년", "「동백 아가씨」 대히트", "전축 있는 집마다 음반을", PINK),
          ("1965년", "한일 국교 정상화", "같은 해, 왜색·비탄조로 방송 금지", RED),
          ("1987년", "해금", "20년 넘게 묶였던 노래", GREEN)]
    y = 0.60
    fig.add_artist(plt.Line2D([0.08, 0.92], [y, y], transform=fig.transFigure, color=GREY, lw=3))
    for i, (d, a, b, c) in enumerate(ev):
        x = 0.15 + i * 0.233
        fig.add_artist(plt.Line2D([x], [y], transform=fig.transFigure, marker="o", ms=26, color=c, mec=BG, mew=3))
        fig.text(x, y + 0.085, d, ha="center", color=c, fontsize=28)
        fig.text(x, y - 0.08, a, ha="center", color=WHITE, fontsize=24)
        fig.text(x, y - 0.14, b, ha="center", color=GREY, fontsize=18)
    credit(fig, "서울신문(이호섭·박성서) · 데일리안 · 경향신문 1990 — 금지 이유의 해석은 여러 가지")
    save(fig, "14_트로트_03_금지곡")


def tr_04_ratings():
    """시청률 막대"""
    fig = canvas()
    title(fig, "트로트의 귀환", "종합편성채널 시청률 (닐슨코리아 전국)")
    ax = fig.add_axes([0.18, SAFE_BOTTOM + 0.04, 0.64, 0.5], facecolor=BG)
    bars = [("JTBC 「SKY 캐슬」 최고 (2019)", 23.8, GREY), ("TV조선 「미스터트롯」 결승 (2020-03-12)", 35.7, PINK)]
    for i, (lab, v, c) in enumerate(bars):
        ax.barh(i, v, color=c, height=0.55)
        ax.text(v + 0.6, i, f"{v}%", va="center", color=c, fontsize=40)
        ax.text(0.4, i + 0.43, lab, va="bottom", color=WHITE, fontsize=22)
    ax.set_xlim(0, 42)
    ax.set_ylim(-0.6, 1.9)
    ax.axis("off")
    credit(fig, "뉴시스 · 데일리안 · 스포츠경향 (2020-03) — 결승 시청자 약 918만 명 (TNMS)")
    save(fig, "14_트로트_04_시청률")


def tr_05_history():
    """트로트 90년"""
    fig = canvas()
    title(fig, "트로트 90년", "간격은 실제 시간 비율이 아닙니다")
    ev = [("1932", "「황성옛터」", "유행가의 탄생", AMBER),
          ("1935", "「목포의 눈물」", "주류가 되다", AMBER),
          ("1960년대", "'트로트'라는 이름", "'뽕짝'이라 낮춰 불리기도", GREY),
          ("1965", "왜색 금지곡", "「동백 아가씨」", RED),
          ("1990", "뿌리 논쟁", "박춘석 vs 최창권", CYAN),
          ("2020", "「미스터트롯」", "시청률 35.7%", PINK),
          ("2022", "학술 논문", "음계 이름부터 뒤섞였다", GREEN)]
    y = 0.60
    fig.add_artist(plt.Line2D([0.04, 0.96], [y, y], transform=fig.transFigure, color=GREY, lw=3))
    for i, (d, a, b, c) in enumerate(ev):
        x = 0.085 + i * 0.138
        fig.add_artist(plt.Line2D([x], [y], transform=fig.transFigure, marker="o", ms=22, color=c, mec=BG, mew=3))
        fig.text(x, y + 0.08, d, ha="center", color=c, fontsize=24)
        fig.text(x, y - 0.075, a, ha="center", color=WHITE, fontsize=20)
        fig.text(x, y - 0.125, b, ha="center", color=GREY, fontsize=15)
    credit(fig, "트로트_사실확인.md (위키백과 · 경향신문 1990 · 한국음악연구 72집 2022)")
    save(fig, "14_트로트_05_90년")


def main():
    tr_01_question()
    tr_02_versus()
    tr_03_ban()
    tr_04_ratings()
    tr_05_history()


if __name__ == "__main__":
    main()
