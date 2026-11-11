"""블록 애니 쇼츠 조립 (나레이션 없음, 세로 1080×1920): 샷 프레임 → 24fps + 눈·밤 색감 + 화면 글자(대본.txt) + 배경음악
사용: python 블록쇼츠_조립.py <대본.txt> <샷목록.json> <프레임폴더> <음악.wav> <결과.mp4> [--효과 효과.json]
  대본.txt 한 줄 = '시작-끝 | 장면 설명 | 글자 / 글자'  (★ 로 시작하는 글자 = 위쪽 큰 글자, 나머지 = 아래 글자)
  효과.json = {"샷이름": {"snow": 0~1(눈 양), "night": 0~1(어둡고 푸르게)}, ...}"""
import json, os, re, subprocess, sys, glob, random
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter
script, shot_path, fdir, audio, out = sys.argv[1:6]
fx = json.load(open(sys.argv[sys.argv.index('--효과') + 1], encoding='utf-8')) if '--효과' in sys.argv else {}
shots = json.load(open(shot_path, encoding='utf-8'))['shots']
work = os.path.splitext(out)[0] + '_작업'; os.makedirs(work, exist_ok=True)
W, H = 1080, 1920

def snow_layer(i, amt, seed):
    """눈송이: 샷마다 같은 씨앗 → 프레임마다 아래로 떨어짐 (amt 1 = 눈보라)"""
    rnd = random.Random(seed); im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    for k in range(int(260 * amt)):
        x0 = rnd.uniform(0, W); y0 = rnd.uniform(0, H); sp = rnd.uniform(4, 14) * (1 + amt); r = rnd.uniform(2, 6)
        drift = rnd.uniform(-2, 2) + amt * 6
        x = (x0 + i * drift) % W; y = (y0 + i * sp) % H
        a = int(rnd.uniform(140, 235)); d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 255, 255, a))
    return im.filter(ImageFilter.GaussianBlur(1.2))

# 1) 샷 → 24fps 조각 (효과가 있으면 프레임을 먼저 고침)
parts = []
for si, sh in enumerate(shots):
    d = os.path.join(fdir, sh['name']); dur = sh['t1'] - sh['t0']; o = os.path.join(work, sh['name'] + '.mp4')
    e = fx.get(sh['name'], {})
    src = d
    if e:
        src = os.path.join(work, sh['name'] + '_fx'); os.makedirs(src, exist_ok=True)
        fs = sorted(glob.glob(os.path.join(d, 'f*.png')))
        for i, f in enumerate(fs):
            of = os.path.join(src, os.path.basename(f))
            if os.path.exists(of): continue
            im = Image.open(f).convert('RGB').resize((W, H), Image.LANCZOS)
            nt = e.get('night', 0)
            if nt:
                im = ImageEnhance.Brightness(im).enhance(1 - 0.62 * nt)
                blue = Image.new('RGB', (W, H), (20, 40, 90)); im = Image.blend(im, blue, 0.28 * nt)
            if e.get('snow'):
                im = im.convert('RGBA'); im.alpha_composite(snow_layer(i * 24 / sh['fps'] / 2, e['snow'], si * 97)); im = im.convert('RGB')
            im.save(of)
    if not os.path.exists(o):
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-framerate', str(sh['fps']), '-i', os.path.join(src, 'f%05d.png'),
                        '-vf', f'scale={W}:{H}:flags=lanczos,fps=24,tpad=stop_mode=clone:stop_duration=2,format=yuv420p', '-t', f'{dur:.3f}',
                        '-c:v', 'libx264', '-crf', '18', '-preset', 'medium', '-r', '24', o], check=True)
    parts.append(o)
lst = os.path.join(work, '목록.txt'); open(lst, 'w').write(''.join(f"file '{os.path.abspath(p)}'\n" for p in parts))
total = shots[-1]['t1']

# 2) 화면 글자 (ASS)
def ts(t): t = max(0, t); return f"{int(t // 3600)}:{int(t % 3600 // 60):02d}:{t % 60:05.2f}"
ev = []
for ln in open(script, encoding='utf-8'):
    ln = ln.strip()
    if not ln or ln.startswith('#'): continue
    tm, _, txt = [x.strip() for x in ln.split('|', 2)]
    a, b = [float(x) for x in tm.split('-')]
    for k, p in enumerate([x.strip() for x in txt.split(' / ') if x.strip()]):
        big = p.startswith('★'); p = p.lstrip('★').replace('{', '(').replace('}', ')')
        s0 = a + (0.25 if big else 0.6 + 0.2 * k); s1 = (b + 0.6) if b >= total - 0.01 else b - 0.05
        ev.append(f"Dialogue: 0,{ts(s0)},{ts(min(s1, total))},{'Big' if big else 'Sub'},,0,0,0,,{{\\fad(300,250)}}{p}")
F = 'NanumGothicExtraBold'
ass = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Big,{F},92,&H0060E8FF,&H00FFFFFF,&H00151515,&H90000000,1,0,0,0,100,100,0,0,1,7,3,8,70,70,300,1
Style: Sub,{F},62,&H00FFFFFF,&H00FFFFFF,&H00101010,&H80000000,1,0,0,0,100,100,0,0,1,5,2,2,80,80,430,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
""" + '\n'.join(ev) + '\n'
assp = os.path.join(work, '글자.ass'); open(assp, 'w', encoding='utf-8').write(ass)

# 3) 합치기 (처음 0.5초·끝 1초 검게)
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', lst, '-i', audio,
                '-vf', f"ass={assp},fade=t=in:st=0:d=0.5,fade=t=out:st={total - 1.0:.2f}:d=1.0", '-map', '0:v', '-map', '1:a',
                '-c:v', 'libx264', '-crf', '19', '-preset', 'medium', '-r', '24', '-c:a', 'aac', '-b:a', '192k',
                '-t', f'{total:.2f}', '-movflags', '+faststart', out], check=True)
print('OK', out)
