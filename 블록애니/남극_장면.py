"""《남극에 남겨진 타로와 지로》 장면 모형 (세트 하나, 움직임 시간 = 영상 시간 0~55초)
   → 연재/남극의타로지로/장면/A_기지.bbmodel + 세트정보.json
   사용: python 남극_장면.py [폴더]
   방향: 개·사람 앞 = -z. 위치 움직임 x 는 반대로 적용됨 → K() 가 부호를 뒤집음"""
import sys, os, json, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 남극인물 import *
OUT = sys.argv[1] if len(sys.argv) > 1 else '/home/user/youtubeshot/연재/남극의타로지로/장면'
os.makedirs(OUT, exist_ok=True)
L = 55.0
random.seed(7)

M = Model(256)
for k in DOGS: dog_palette(M, k)
explorer_palette(M)
M.swatch('snow', (238, 243, 250), 6); M.swatch('snow_d', (215, 225, 238), 6); M.swatch('snow_s', (200, 212, 230), 5)
M.swatch('ice', (175, 210, 235), 8); M.swatch('rock', (70, 66, 64), 10); M.swatch('rock_l', (100, 95, 90), 10)
M.swatch('wall', (150, 75, 40), 6); M.swatch('wall_d', (115, 55, 30), 5); M.swatch('roof', (245, 248, 252), 4)
M.swatch('win', (60, 80, 100), 4); M.swatch('win_l', (255, 220, 140), 4); M.swatch('metal', (90, 95, 100), 6)
M.swatch('chain', (55, 55, 60), 4); M.swatch('stake', (100, 70, 45), 5); M.swatch('print', (190, 203, 222), 3)
M.swatch('heli', (230, 120, 30), 6); M.swatch('heli_d', (190, 90, 25), 5); M.swatch('glass', (150, 200, 225), 4)
M.swatch('rotor', (40, 40, 42), 3)
A = Anim(L)
top = []

def K(g, ch, pts, interp='linear'):
    """position 은 x 부호를 뒤집어 넣음 (실제 이동 = 적은 값)"""
    if ch == 'position': pts = [(t, (-v[0], v[1], v[2])) for t, v in pts]
    A.add(g, ch, pts, interp)

def vis(g, spans):
    """spans=[(t0,t1),...] 동안만 보임 (그 밖은 크기 0)"""
    pts = []
    for a, b in spans:
        if a <= 0: pts.append((0, (1, 1, 1)))
        else: pts += [(a - 0.01, (0, 0, 0)), (a, (1, 1, 1))]
        if b < L: pts += [(b, (1, 1, 1)), (b + 0.01, (0, 0, 0))]
    if spans[0][0] > 0: pts.insert(0, (0, (0, 0, 0)))
    A.add(g, 'scale', pts)

def part(g, n): return find(g, g['name'].replace('root', n))

# ---------------- 땅 ----------------
top.append(M.cube('far_ground', [-4000, -30, -4000], [4000, -1, 4000], 'snow_d'))
for x in range(-320, 320, 64):
    for z in range(-560, 320, 64):
        top.append(M.cube('g', [x, -16, z], [x + 64, 0, z + 64], 'snow' if (x // 64 + z // 64) % 2 else 'snow_d'))
top.append(M.cube('sea_ice', [-4000, -1.5, -4000], [4000, -0.5, -560], 'ice'))
for i in range(26):   # 눈 더미·바위
    x = random.uniform(-300, 300); z = random.uniform(-520, 300)
    if abs(x) < 110 and -150 < z < 110: continue
    if abs(x) < 140 and z < -140: continue      # 달리는 길·해돋이 쪽 (카메라가 눈 더미를 뚫지 않게)
    w = random.uniform(10, 30); h = random.uniform(3, 12)
    top.append(M.cube('mound', [x - w, 0, z - w * 0.7], [x + w, h, z + w * 0.7], 'snow'))
    if i % 3 == 0: top.append(M.cube('rock', [x - w * 0.4, 0, z - w * 0.3], [x + w * 0.3, h + 5, z + w * 0.3], 'rock', up='snow'))
# 해돋이 언덕 (z -420)
top += [M.cube('hill1', [-60, 0, -460], [60, 10, -390], 'snow'), M.cube('hill2', [-35, 10, -445], [35, 16, -405], 'snow'),
        M.cube('hill_rock', [-12, 14, -432], [14, 18, -415], 'rock', up='snow')]

# ---------------- 기지 (뒤쪽 +z) ----------------
def hut(tag, x0, x1, z0, z1, h):
    k = [M.cube('wall', [x0, 0, z0], [x1, h, z1], 'wall', down='wall_d'), M.cube('roof', [x0 - 2, h, z0 - 2], [x1 + 2, h + 4, z1 + 2], 'roof'),
         M.cube('door', [(x0 + x1) / 2 - 5, 0, z0 - 0.6], [(x0 + x1) / 2 + 5, 16, z0], 'wall_d')]
    for wx in range(int(x0) + 8, int(x1) - 8, 18):
        if abs(wx + 4 - (x0 + x1) / 2) < 10: continue
        k.append(M.cube('win', [wx, h * 0.45, z0 - 0.6], [wx + 8, h * 0.45 + 7, z0], 'win'))
    k.append(M.cube('drift', [x0 - 4, 0, z0 - 6], [x1 + 4, 5, z0], 'snow'))
    return M.group(tag, [(x0 + x1) / 2, 0, (z0 + z1) / 2], k)
top += [hut('hut1', -150, -40, 70, 115, 30), hut('hut2', 20, 130, 85, 125, 26), hut('hut3', -230, -175, 40, 80, 22)]
top += [M.cube('mast', [150, 0, 90], [153, 90, 93], 'metal'), M.cube('mast_bar', [140, 86, 90.5], [163, 88, 92.5], 'metal')]
for i in range(4):
    top.append(M.cube('drum', [60 + i * 9, 0, 58], [67 + i * 9, 10, 65], 'metal', up='snow'))

# ---------------- 개 15마리 (목줄에 묶임, z=0, 앞 사슬 z=-20) ----------------
top.append(M.cube('chain_line', [-92, 0, -21], [92, 1.2, -19.8], 'chain'))
for x in (-92, 92): top.append(M.cube('stake', [x - 1, 0, -22], [x + 1, 6, -19], 'stake'))
order = ['grey', 'white', 'brown', 'grey', 'white', 'brown', 'taro', 'jiro', 'brown', 'grey', 'white', 'brown', 'grey', 'white', 'grey']
line = []
for i, kind in enumerate(order):
    x = -84 + 12 * i
    g = dog(M, f'L{i}_', kind)
    bod = part(g, 'body')
    # 목줄: 목걸이(y12.7,z-8.6)에서 사슬(y1,z-20)까지 계단 상자
    steps = [M.cube('leash', [-0.5, 12.2 - 2.4 * k, -9.4 - 2.2 * k], [0.5, 13.2 - 2.4 * k, -7.2 - 2.2 * k], 'chain') for k in range(5)]
    bod['children'] += steps
    move(M, g, x, 0, 0)
    top.append(g); line.append((g, kind, x))

# 빈 목줄 (19초부터): 눈 위에 놓인 목걸이 + 사슬 쪽으로 뻗은 줄
empty = []
for i, kind in enumerate(order):
    x = -84 + 12 * i
    col = kind + '_collar'
    k = [M.cube('ring', [x - 2.8, 0, -11.5], [x + 2.8, 1.3, -6.5], col), M.cube('ring_in', [x - 1.6, 0.2, -10.3], [x + 1.6, 1.5, -7.7], 'snow'),
         M.cube('leash', [x - 0.5, 0, -19.8], [x + 0.5, 0.8, -11.5], 'chain'),
         M.cube('drift', [x - 4, 0, -4], [x + 4, 3 + (i % 3), 6], 'snow')]
    e = M.group(f'E{i}', [x, 0, -9], k); top.append(e); empty.append(e)

# ---------------- 헬리콥터 ----------------
def heli(tag):
    k = [M.cube('cabin', [-8, 4, -14], [8, 20, 6], 'heli', north='glass'), M.cube('nose', [-6, 5, -18], [6, 16, -14], 'glass'),
         M.cube('boom', [-3, 12, 6], [3, 18, 38], 'heli'), M.cube('fin', [-1, 14, 34], [1, 26, 40], 'heli_d'),
         M.cube('stripe', [-8.2, 8, -10], [8.2, 10, 6], 'heli_d'),
         M.cube('skid_l', [5, 0, -14], [7, 1.5, 8], 'metal'), M.cube('skid_r', [-7, 0, -14], [-5, 1.5, 8], 'metal'),
         M.cube('strut_l', [5.5, 1.5, -6], [6.5, 4, -4], 'metal'), M.cube('strut_r', [-6.5, 1.5, -6], [-5.5, 4, -4], 'metal'),
         M.cube('mast', [-1, 20, -5], [1, 24, -3], 'metal')]
    rotor = M.group(tag + 'rotor', [0, 24, -4], [M.cube('blade1', [-34, 24, -5], [34, 25, -3], 'rotor'),
                                                M.cube('blade2', [-1, 24, -38], [1, 25, 30], 'rotor')])
    return M.group(tag + 'root', [0, 0, 0], k + [rotor])
H = heli('h_'); move(M, H, 150, 0, -130); top.append(H)
HX, HZ = 150, -130

# ---------------- 대원 ----------------
EX = explorer(M, 'e_'); top.append(EX)        # 원점에 두고 움직임 키로 자리·방향을 줌

# ---------------- 따로 움직이는 타로·지로 (23.5초~) ----------------
TR = dog(M, 'T_', 'taro'); JR = dog(M, 'J_', 'jiro'); top += [TR, JR]

# 발자국 두 줄 (해돋이 장면: z -300 → -400)
prints = []
for j, x0 in enumerate((-6, 6)):
    for k in range(14):
        z = -300 - k * 7.5 - j * 3
        prints.append(M.cube('print', [x0 + (1.5 if k % 2 else -1.5) - 1, 0, z - 1.2], [x0 + (1.5 if k % 2 else -1.5) + 1, 0.35, z + 1.2], 'print'))
PR = M.group('prints', [0, 0, -350], prints); top.append(PR)

# =====================================================================
#  움직임
# =====================================================================
def wag(g, t0, t1, amp=28, per=0.32):
    tl = part(g, 'tail'); pts = [(t0, (0, 0, 0))]; t = t0; s = 1
    while t < t1: t += per / 2; pts.append((min(t, t1), (0, s * amp, 0))); s = -s
    pts.append((t1 + 0.1, (0, 0, 0))); A.add(tl, 'rotation', pts, 'catmullrom')

def run_legs(g, t0, t1, amp=38, per=0.42):
    legs = [part(g, n) for n in ('leg_fl', 'leg_br', 'leg_fr', 'leg_bl')]
    for idx, lg in enumerate(legs):
        sg = 1 if idx < 2 else -1; pts = [(t0 - 0.05, (0, 0, 0))]; t = t0; s = sg
        while t < t1: pts.append((t, (s * amp, 0, 0))); t += per / 2; s = -s
        pts.append((t1 + 0.05, (0, 0, 0))); A.add(lg, 'rotation', pts, 'catmullrom')
    bod = part(g, 'body'); pts = []; t = t0; k = 0
    while t < t1: pts.append((t, (0, 1.2 if k % 2 else 0, 0))); t += per / 4; k += 1
    A.add(bod, 'position', [(t0 - 0.05, (0, 0, 0))] + pts + [(t1 + 0.05, (0, 0, 0))])

# --- 줄에 묶인 개들: 0~19초 ---
for i, (g, kind, x) in enumerate(line):
    vis(g, [(0, 19.0)])
    hd = part(g, 'head'); bod = part(g, 'body')
    ph = (i * 0.37) % 1.0
    # 머리: 가만히 둘러봄 → 9~14 헬기를 올려다봄(왼쪽 위) → 14~19 웅크려 고개 숙임
    A.add(hd, 'rotation', [(0, (0, 0, 0)), (2 + ph, (0, 12 * (1 if i % 2 else -1), 0)), (5 + ph, (0, -8 * (1 if i % 2 else -1), 0)),
                           (9.3 + ph * 0.6, (0, 0, 0)), (10.2 + ph * 0.5, (-25, 22, 0)), (13.6, (-30, 28, 0)),
                           (14.3, (0, 0, 0)), (15.0, (14, 0, 0)), (19, (14, 0, 0))], 'catmullrom')
    # 웅크림 14~19: 몸을 낮추고 다리를 접음
    K(bod, 'position', [(0, (0, 0, 0)), (14.0, (0, 0, 0)), (14.9, (0, -4.6, 0)), (19, (0, -4.6, 0))])
    for n in ('leg_fl', 'leg_fr', 'leg_bl', 'leg_br'):
        A.add(part(g, n), 'scale', [(0, (1, 1, 1)), (14.0, (1, 1, 1)), (14.9, (1, 0.15, 1)), (19, (1, 0.15, 1))])
    if kind in ('taro', 'jiro'): wag(g, 4.5, 8.8, amp=30)
    else: wag(g, 0.5 + ph, 3.5 + ph, amp=18, per=0.5)

for e in empty: vis(e, [(19.0, L)])

# --- 헬기: 0~14.5 (9초 이륙, 멀어짐), 33~55 (다시 옴) ---
vis(H, [(0, 14.6), (33.0, L)])
rot = []; t = 0; a = 0
while t <= L: rot.append((t, (0, a, 0))); t += 0.25; a += 150
A.add(part(H, 'rotor'), 'rotation', rot)
K(H, 'position', [(0, (0, 0, 0)), (9.0, (0, 0, 0)), (10.5, (0, 20, 0)), (14.5, (40, 150, 380)),
                  (33.0, (-60, 140, -260)), (36.0, (-15, 30, -60)), (37.2, (0, 0, 0)), (L, (0, 0, 0))], 'catmullrom')
A.add(H, 'rotation', [(0, (0, 0, 0)), (9.0, (0, 0, 0)), (11, (8, 0, 0)), (14.5, (8, 0, 0)), (33.0, (-6, 0, 0)), (36.5, (-6, 0, 0)), (37.3, (0, 0, 0))])

# --- 대원: 0~8.8 타로·지로 사이에서 쓰다듬음 / 37~55 헬기에서 내려 맞이함 ---
vis(EX, [(0, 9.0), (37.0, L)])
TXL, JXL = -84 + 12 * 6, -84 + 12 * 7     # 줄에 묶인 타로(-12)·지로(0)
MX, MZ = 60, -100                          # 만나는 곳
K(EX, 'position', [(0, ((TXL + JXL) / 2, 0, -27)), (8.8, ((TXL + JXL) / 2, 0, -27)),
                   (36.99, (HX - 14, 0, HZ + 2)), (37.0, (HX - 14, 0, HZ + 2)), (40.5, (MX, 0, MZ - 16)), (L, (MX, 0, MZ - 16))])
A.add(EX, 'rotation', [(0, (0, 180, 0)), (36.99, (0, 180, 0)), (37.0, (0, -110, 0)), (40.0, (0, -150, 0)), (40.6, (0, 180, 0)), (L, (0, 180, 0))])
# 무릎 꿇기: 0~8.8, 41.5~ (몸 낮춤 + 다리 접기)
kneel = [(0, 1), (8.8, 1), (40.6, 0), (41.4, 1), (L, 1)]
def kv(f, on, off):
    pts = []
    for t, k in kneel: pts.append((t, tuple(on[j] * k + off[j] * (1 - k) for j in range(3))))
    return pts
K(part(EX, 'body'), 'position', kv(None, (0, -7, 0), (0, 0, 0)))
A.add(part(EX, 'leg_left'), 'rotation', kv(None, (90, 0, 0), (0, 0, 0)))
A.add(part(EX, 'leg_right'), 'rotation', kv(None, (90, 0, 0), (0, 0, 0)))
K(part(EX, 'leg_left'), 'position', kv(None, (0, -7, 0), (0, 0, 0)))
K(part(EX, 'leg_right'), 'position', kv(None, (0, -7, 0), (0, 0, 0)))
# 팔: 쓰다듬기(0~8.8 양손 앞으로, 오르내림), 41.5~46 오른손을 지로에게 내밂, 46~50 두 팔 벌려 안음
arm_r = [(0, (-70, 0, 0)), (1.5, (-55, 0, 0)), (3, (-70, 0, 0)), (4.5, (-55, 0, 0)), (6, (-70, 0, 0)), (7.5, (-55, 0, 0)), (8.8, (-70, 0, 0)),
         (37, (0, 0, 0)), (40.5, (0, 0, 0)), (42.2, (-65, 0, 0)), (45.8, (-65, 0, 0)), (46.8, (-80, 0, -25)), (L, (-80, 0, -25))]
arm_l = [(0, (-55, 0, 0)), (1.5, (-70, 0, 0)), (3, (-55, 0, 0)), (4.5, (-70, 0, 0)), (6, (-55, 0, 0)), (7.5, (-70, 0, 0)), (8.8, (-55, 0, 0)),
         (37, (0, 0, 0)), (45.8, (0, 0, 0)), (46.8, (-80, 0, 25)), (L, (-80, 0, 25))]
A.add(part(EX, 'arm_right'), 'rotation', arm_r, 'catmullrom'); A.add(part(EX, 'arm_left'), 'rotation', arm_l, 'catmullrom')
walk_t = [(37.0, 40.5)]
for a, b in walk_t:
    pts = [(a, (0, 0, 0))]; t = a; s = 1
    while t < b: t += 0.35; pts.append((min(t, b), (s * 25, 0, 0))); s = -s
    A.add(part(EX, 'arm_left'), 'rotation', [(a + 0.01, (0, 0, 0))] + [(tt, (-v[0], 0, 0)) for tt, v in pts[1:]], 'catmullrom')
A.add(part(EX, 'head'), 'rotation', [(0, (25, 0, 0)), (8.8, (25, 0, 0)), (37, (0, 0, 0)), (41.5, (20, 0, 0)), (46, (20, 15, 0)), (50, (10, 0, 0)), (L, (10, 0, 0))], 'catmullrom')

# --- 따로 움직이는 타로·지로 ---
vis(TR, [(23.5, L)]); vis(JR, [(23.5, L)])
# 23.5~28.5 얼음 위를 달림 (z -150 → -330), 28.5~33 해돋이 언덕 위(뒷모습), 37~41.5 기지에서 달려 나옴, 41.5~ 대원 앞
K(JR, 'position', [(0, (8, 0, -150)), (23.5, (8, 0, -150)), (28.4, (8, 0, -300)), (28.5, (6, 16, -418)), (36.9, (6, 16, -418)),
                   (37.0, (40, 0, 40)), (41.0, (MX, 0, MZ + 12)), (L, (MX, 0, MZ + 12))])
K(TR, 'position', [(0, (-8, 0, -180)), (23.5, (-8, 0, -180)), (28.4, (-8, 0, -330)), (28.5, (-6, 16, -421)), (36.9, (-6, 16, -421)),
                   (37.0, (20, 0, 60)), (41.3, (MX - 26, 0, MZ + 22)), (45.8, (MX - 26, 0, MZ + 22)), (47.2, (MX - 13, 0, MZ + 6)), (L, (MX - 13, 0, MZ + 6))])
run_legs(JR, 23.5, 28.4); run_legs(TR, 23.5, 28.4, per=0.4)
run_legs(JR, 37.0, 41.0); run_legs(TR, 37.0, 41.3, per=0.4); run_legs(TR, 45.8, 47.2, per=0.4)
# 방향: 기지에서 나올 땐 만나는 곳 쪽, 그 밖은 -z
A.add(JR, 'rotation', [(0, (0, 0, 0)), (36.99, (0, 0, 0)), (37.0, (0, 10, 0)), (41.0, (0, 0, 0))])
A.add(TR, 'rotation', [(0, (0, 0, 0)), (36.99, (0, 0, 0)), (37.0, (0, 20, 0)), (41.3, (0, 0, 0)), (45.8, (0, 0, 0)), (46.3, (0, 40, 0)), (47.2, (0, 15, 0)), (L, (0, 15, 0))])
# 해돋이: 고개를 들어 해 쪽을 봄
for g in (TR, JR):
    A.add(part(g, 'head'), 'rotation', [(0, (0, 0, 0)), (28.5, (0, 0, 0)), (30, (-15, 0, 0)), (33, (-15, 0, 0)), (33.5, (0, 0, 0)),
                                        (41.5, (-28, 0, 0)), (L, (-28, 0, 0))], 'catmullrom')
# 지로: 이름 부르자 꼬리 (43.3~), 타로: 46.5~ 꼬리 + 뛰어오름(47.2~48.6)
wag(JR, 43.3, L - 0.2, amp=34, per=0.3); wag(TR, 46.4, L - 0.2, amp=34, per=0.28)
K(TR, 'position', [(47.2, (MX - 13, 0, MZ + 6)), (47.8, (MX - 10, 6, MZ + 3)), (48.8, (MX - 10, 6, MZ + 3)), (49.4, (MX - 13, 0, MZ + 6)), (L, (MX - 13, 0, MZ + 6))], 'catmullrom')
A.add(part(TR, 'body'), 'rotation', [(47.1, (0, 0, 0)), (47.8, (-35, 0, 0)), (48.8, (-35, 0, 0)), (49.4, (0, 0, 0))], 'catmullrom')

vis(PR, [(28.5, 33.0)])

A.bake(top)
M.save(f'{OUT}/A_기지.bbmodel', top, [A.json()], name='A')
json.dump({'A': {'ropes': []}}, open(f'{OUT}/세트정보.json', 'w', encoding='utf-8'))
print('ok', len(M.els), 'cubes')
