"""조디악 340 암호 도표 (실제 암호 사진 위에 읽는 순서·세 부분·글자 카드를 그림) → 사진/<컷>.jpg
  python 도표_만들기.py   (사진후보/c13_1.jpg = 1969년 11월 8일 카드 속 340 암호, Public domain)
격자: 17칸 × 20줄, 첫 칸 중심 (30, 90), 칸 간격 28.4 × 28.5 (원본 530×799 기준)"""
import json, os
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 1920, 1080
FB = "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf"
FR = "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"
BG = (22, 20, 18)
src = Image.open(os.path.join(HERE, "사진후보", "c13_1.jpg")).convert("RGB")
X0, Y0, DX, DY = 30, 90, 28.4, 28.5


def cipher(scale):
    """암호 부분만 잘라 scale 배로 (위아래 여백 조금)"""
    c = src.crop((8, 66, 512, 656))
    return c.resize((int(c.width * scale), int(c.height * scale)), Image.LANCZOS), (8, 66)


def cell(r, k, scale, off, at):
    x = (X0 + k * DX - off[0]) * scale + at[0]
    y = (Y0 + r * DY - off[1]) * scale + at[1]
    return x, y


def canvas(title, sub=None):
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    return im, d


def text_block(d, x, y, lines, size, color, font=FB, gap=1.45):
    f = ImageFont.truetype(font, size)
    for ln in lines:
        d.text((x, y), ln, font=f, fill=color)
        y += int(size * gap)
    return y


def save(im, name):
    im.save(os.path.join(HERE, "사진", name + ".jpg"), quality=92)


os.makedirs(os.path.join(HERE, "사진"), exist_ok=True)
S = 1.45
cimg, off = cipher(S)
AT = (150, (H - cimg.height) // 2)

# c19 대각선으로 읽는 순서 (첫 부분: 한 줄 내려가며 두 칸씩 오른쪽, 끝에 닿으면 왼쪽으로 돌아옴)
im, d = canvas("")
im.paste(cimg, AT)
pts = []
r, k = 0, 0
for i in range(17):
    pts.append(cell(r, k, S, off, AT)); r += 1; k = (k + 2) % 17
for i, (x, y) in enumerate(pts):
    d.ellipse((x - 17, y - 17, x + 17, y + 17), outline=(255, 70, 60), width=4)
    if i:
        px, py = pts[i - 1]
        if abs(px - x) < 200:
            d.line((px, py, x, y), fill=(255, 70, 60), width=3)
    d.text((x + 16, y - 30), str(i + 1), font=ImageFont.truetype(FB, 22), fill=(255, 210, 90))
text_block(d, 1000, 300, ["읽는 순서의 비밀"], 64, (255, 230, 170))
text_block(d, 1000, 420, ["한 줄 내려갈 때마다", "두 칸씩 오른쪽으로 건너뜀", "", "끝에 닿으면 왼쪽으로 돌아와", "다시 대각선으로 이어 읽음"], 44, (235, 235, 235), FR)
save(im, "c19")

# c21 세 부분
im, d = canvas("")
im.paste(cimg, AT)
ov = Image.new("RGBA", im.size, (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
for (r0, r1, col, lab) in [(0, 8, (255, 90, 70, 70), "1부 · 9줄"), (9, 17, (80, 170, 255, 70), "2부 · 9줄"), (18, 19, (120, 220, 120, 80), "3부 · 2줄")]:
    x0, y0 = cell(r0, 0, S, off, AT); x1, y1 = cell(r1, 16, S, off, AT)
    od.rectangle((x0 - 20, y0 - 20, x1 + 20, y1 + 20), fill=col, outline=col[:3] + (255,), width=4)
    d2 = ImageDraw.Draw(ov); d2.text((x1 + 50, (y0 + y1) / 2 - 28), lab, font=ImageFont.truetype(FB, 50), fill=col[:3] + (255,))
im = Image.alpha_composite(im.convert("RGBA"), ov).convert("RGB")
d = ImageDraw.Draw(im)
text_block(d, 1250, 820, ["1·2부: 대각선 순서", "3부: 따로 읽음"], 40, (235, 235, 235), FR)
save(im, "c21")

# c04 확대 (왼쪽 위 부분)
z = src.crop((10, 70, 300, 300)); z = z.resize((int(z.width * 3.6), int(z.height * 3.6)), Image.LANCZOS)
im = Image.new("RGB", (W, H), BG); im.paste(z.crop((0, 0, min(W, z.width), min(H, z.height))), ((W - min(W, z.width)) // 2, (H - min(H, z.height)) // 2))
save(im, "c04")

# c15 기호 63가지 · 340개
im, d = canvas("")
im.paste(cimg, AT)
text_block(d, 1000, 330, ["340개의 기호"], 72, (255, 230, 170))
text_block(d, 1000, 450, ["가로 17칸 × 세로 20줄", "서로 다른 기호 63가지", "", "같은 방법으로는", "말이 되는 문장이 나오지 않았음"], 44, (235, 235, 235), FR)
save(im, "c15")

# c24 풀린 문장 (한국어 뜻 + 원문 일부)
im, d = canvas("")
small = cimg.resize((cimg.width * 2 // 3, cimg.height * 2 // 3)); im.paste(small, (110, (H - small.height) // 2))
y = text_block(d, 760, 170, ["340 암호에 적힌 말 (뜻)"], 56, (255, 230, 170))
y = text_block(d, 760, y + 30, ["“나를 잡으려고 무척 즐거운 시간을", "  보내고 있기를 바란다.", "  TV 프로그램에 나온 건 내가 아니었다.", "  나는 가스실이 두렵지 않다.", "  나를 더 빨리 천국으로 보내 줄 테니까.”"], 42, (240, 240, 240), FR)
text_block(d, 760, y + 40, ["I HOPE YOU ARE HAVING LOTS OF FUN IN TRYING TO CATCH ME", "THAT WASNT ME ON THE TV SHOW ...", "I AM NOT AFRAID OF THE GAS CHAMBER ..."], 26, (170, 170, 170), FR)
save(im, "c24")

meta_p = os.path.join(HERE, "사진후보", "후보.json"); meta = json.load(open(meta_p, encoding="utf-8"))
base = meta["c13_1"]
for k in ["c19", "c21", "c04", "c15", "c24"]:
    meta[k + "_도표"] = {"title": "도표: " + k, "artist": "340 암호 원본(Zodiac Killer, 1969) 위에 그린 설명 도표", "license": "Public domain", "page": base["page"]}
json.dump(meta, open(meta_p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("ok")
