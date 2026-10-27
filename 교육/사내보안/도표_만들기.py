"""사내 보안교육 도표 (1920×1080, ESG Smart Factory 화면과 같은 어두운 남색 + 금색)
python 교육/사내보안/도표_만들기.py → 교육/사내보안/도표/c15.png ...
자막이 아래에 깔리므로 내용은 위 82% 안에 둠"""
import os
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "도표")
W, H = 1920, 1080
BG1, BG2 = (24, 27, 38), (14, 16, 23)
GOLD, TXT, SUB, CARD, LINE, RED, GREEN = (226, 176, 74), (236, 238, 244), (150, 158, 178), (34, 38, 54), (58, 64, 86), (239, 84, 84), (74, 196, 128)
BOLD = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
REG = "/usr/share/fonts/truetype/nanum/NanumBarunGothic.ttf"


def font(size, bold=False):
    return ImageFont.truetype(BOLD, size, index=1) if bold else ImageFont.truetype(REG, size)


def base(title, sub=None):
    im = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(im)
    for y in range(H):                                   # 위에서 아래로 살짝 어두워지는 바탕
        t = y / H
        d.line([(0, y), (W, y)], fill=tuple(int(a + (b - a) * t) for a, b in zip(BG1, BG2)))
    d.text((W // 2, 92), title, font=font(60, True), fill=GOLD, anchor="mm")
    if sub:
        d.text((W // 2, 158), sub, font=font(32), fill=SUB, anchor="mm")
    return im, d


def card(d, box, r=22, fill=CARD, outline=LINE, width=2):
    d.rounded_rectangle(box, r, fill=fill, outline=outline, width=width)


def c15():
    im, d = base("회사가 남기는 접속·조회·출력 기록", "사용자 · 일시 · IP · 한 일")
    cols = [("사용자", 300), ("일시", 420), ("접속 위치(IP)", 360), ("한 일", 560)]
    rows = [("홍길동", "2026-10-27 08:41", "192.168.0.24", "치수검사 조회"),
            ("김철수", "2026-10-27 09:15", "192.168.0.31", "도면 출력"),
            ("이영희", "2026-10-27 10:02", "192.168.0.17", "출하검사성적서 다운로드"),
            ("박민수", "2026-10-27 10:40", "192.168.0.45", "권한 밖 메뉴 접근 차단")]
    x0, y0, rh = (W - sum(c[1] for c in cols)) // 2, 240, 104
    card(d, (x0 - 20, y0 - 20, W - x0 + 20, y0 + rh * (len(rows) + 1) + 10))
    x = x0
    for name, w in cols:
        d.text((x + 24, y0 + rh // 2), name, font=font(36, True), fill=GOLD, anchor="lm")
        x += w
    for i, row in enumerate(rows):
        y = y0 + rh * (i + 1)
        d.line([(x0, y), (W - x0, y)], fill=LINE, width=2)
        x = x0
        for j, (v, (_, w)) in enumerate(zip(row, cols)):
            col = RED if (i == 3 and j == 3) else TXT
            d.text((x + 24, y + rh // 2), v, font=font(34), fill=col, anchor="lm")
            x += w
    d.text((W // 2, 830), "예시 화면 · 기록은 나를 지켜 주는 증거", font=font(34), fill=SUB, anchor="mm")
    return im


def steps(title, sub, items, colors=None):
    im, d = base(title, sub)
    n = len(items)
    bw, gap = 470, 90
    x0 = (W - (bw * n + gap * (n - 1))) // 2
    for i, (head, body) in enumerate(items):
        x = x0 + i * (bw + gap)
        c = (colors or [GOLD] * n)[i]
        card(d, (x, 280, x + bw, 760), outline=c, width=4)
        d.ellipse((x + bw // 2 - 50, 320, x + bw // 2 + 50, 420), fill=c)
        d.text((x + bw // 2, 370), str(i + 1), font=font(56, True), fill=BG2, anchor="mm")
        d.text((x + bw // 2, 490), head, font=font(48, True), fill=TXT, anchor="mm")
        for k, line in enumerate(body.split("\n")):
            d.text((x + bw // 2, 580 + k * 52), line, font=font(34), fill=SUB, anchor="mm")
        if i < n - 1:                                     # 다음 단계 화살표
            ax = x + bw + 14
            d.polygon([(ax, 500), (ax + gap - 28, 520), (ax, 540)], fill=GOLD)
    return im


def c18():
    return steps("보안사고 신고 순서", "피싱 메일 · 악성코드 감염 · 계정 도용 · 정보 유출이 의심될 때",
                 [("열지 않기", "첨부파일·링크를\n누르지 않음"), ("부서장에게", "바로 알림\n(혼자 해결 X)"), ("보안담당자에게", "상황을 그대로\n숨기지 않고 전달")],
                 [RED, GOLD, GREEN])


def listing(title, sub, items, cols=1, top=230, size=40):
    im, d = base(title, sub)
    per = (len(items) + cols - 1) // cols
    cw = (W - 240 - 60 * (cols - 1)) // cols
    rh = min(150, (860 - top) // per)
    for i, (num, head, body) in enumerate(items):
        c, r = divmod(i, per)
        x, y = 120 + c * (cw + 60), top + r * rh
        card(d, (x, y, x + cw, y + rh - 22))
        d.ellipse((x + 26, y + (rh - 22) // 2 - 32, x + 90, y + (rh - 22) // 2 + 32), fill=GOLD)
        d.text((x + 58, y + (rh - 22) // 2), num, font=font(34, True), fill=BG2, anchor="mm")
        if body:
            d.text((x + 120, y + (rh - 22) // 2 - 22), head, font=font(size, True), fill=TXT, anchor="lm")
            d.text((x + 120, y + (rh - 22) // 2 + 26), body, font=font(size - 10), fill=SUB, anchor="lm")
        else:
            d.text((x + 120, y + (rh - 22) // 2), head, font=font(size, True), fill=TXT, anchor="lm")
    return im


def c21():
    return listing("관리자 추가 서약 4가지", "권한 구분이 '관리자'인 경우",
                   [("1", "승인 기록이 있을 때만 권한 부여", "부서장 요청 + 업무에 필요한 최소한의 권한"),
                    ("2", "퇴직·전보자 계정은 즉시 회수", "접속·출력 기록을 정기적으로 점검하고 보고"),
                    ("3", "관리자 권한으로 본 정보는 관리 목적으로만", "열람·이용 금지"),
                    ("4", "전산 장애 대비", "대체 작업 방법과 자료 백업 상태 유지")])


def c23():
    im, d = base("서약을 어기면", None)
    items = [("회사 규정에 따른 징계", GOLD), ("부정경쟁방지 및 영업비밀보호에 관한 법률", RED), ("개인정보 보호법", RED), ("민사 · 형사 책임", RED)]
    for i, (t, c) in enumerate(items):
        y = 220 + i * 150
        card(d, (360, y, W - 360, y + 118), outline=c, width=4)
        d.text((W // 2, y + 59), t, font=font(48, True), fill=TXT, anchor="mm")
    return im


def c25():
    return listing("꼭 지켜야 할 8가지", "통합업무시스템(태진포탈) 및 회사 PC·네트워크",
                   [("1", "비밀유지", ""), ("2", "계정 관리", ""), ("3", "권한 내 사용", ""), ("4", "출력·반출 금지", ""),
                    ("5", "사용 이력 기록", ""), ("6", "보안사고 신고", ""), ("7", "PC 보안", ""), ("8", "퇴직·전보 시 반납", "")],
                   cols=2, top=220, size=46)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for f in (c15, c18, c21, c23, c25):
        f().save(os.path.join(OUT, f.__name__ + ".png"))
        print(f.__name__)
