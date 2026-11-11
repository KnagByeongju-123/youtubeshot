"""말없는 블록 애니 조립: 샷 프레임 → (쇼츠 세로 1080×1920 / 롱폼 가로 1920×1080) 24fps + 비 장면 빗줄기·눈 장면 눈송이 + 소리 + 끝 어두워짐 (글자 없음)
사용: python 밥그릇_조립.py <샷목록.json> <프레임폴더> <소리.wav> <결과.mp4>"""
import json, os, subprocess, sys, glob
import numpy as np
from PIL import Image, ImageDraw
shot_path, fdir, audio, out = sys.argv[1:5]
SJ=json.load(open(shot_path,encoding='utf-8')); shots=SJ['shots']
work=os.path.splitext(out)[0]+'_작업'; os.makedirs(work,exist_ok=True)
W,H=(1080,1920) if SJ.get('aspect')=='9:16' else (1920,1080)   # 쇼츠 세로 / 롱폼 가로
rng=np.random.default_rng(3)
drops=[[rng.uniform(0,W),rng.uniform(0,H),rng.uniform(55,95)*H/1920,rng.uniform(70,130)*H/1920] for _ in range(int(160*W/1080))]  # x,y,속도(px/장),길이

def rain_frame(im, k):
    """빗줄기(살짝 기운 흰 선) + 조금 어둡고 푸르게"""
    a=np.asarray(im).astype(np.float32); a=a*0.86+np.array([8,10,16])*1.0
    im=Image.fromarray(np.clip(a,0,255).astype(np.uint8))
    lay=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(lay)
    for x,y,v,l in drops:
        yy=(y+v*k)%(H+200)-100; xx=(x-0.18*v*k)%W
        d.line([(xx,yy),(xx-0.18*l,yy+l)],fill=(225,232,245,105),width=3)
    return Image.alpha_composite(im.convert('RGBA'),lay).convert('RGB')

flakes=[[rng.uniform(0,W),rng.uniform(0,H),rng.uniform(2.5,6)*H/1920,rng.uniform(4,10)*H/1920,rng.uniform(0,6.28)] for _ in range(int(220*W/1080))]
def snow_frame(im, k):
    """눈송이 (천천히 좌우로 흔들리며 내림) + 살짝 밝고 푸르게"""
    a=np.asarray(im).astype(np.float32); a=a*0.92+np.array([14,16,22])
    im=Image.fromarray(np.clip(a,0,255).astype(np.uint8))
    lay=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(lay)
    for x,y,v,r,ph in flakes:
        yy=(y+v*k)%(H+40)-20; xx=(x+18*np.sin(ph+k*0.05)*H/1920)%W
        d.ellipse([xx-r,yy-r,xx+r,yy+r],fill=(255,255,255,210))
    return Image.alpha_composite(im.convert('RGBA'),lay).convert('RGB')

parts=[]; k=0
for sh in shots:
    d=os.path.join(fdir,sh['name']); n=round((sh['t1']-sh['t0'])*sh['fps']); o=os.path.join(work,sh['name']+'.mp4')
    src=d
    fx=rain_frame if sh.get('rain') else snow_frame if sh.get('snow') else None
    if fx:   # 비·눈 장면: 사진마다 빗줄기·눈송이를 그려 넣음
        src=os.path.join(work,sh['name']+('_비' if sh.get('rain') else '_눈')); os.makedirs(src,exist_ok=True)
        for i in range(n):
            p=os.path.join(src,f'f{i:05d}.png')
            if not os.path.exists(p):
                im=Image.open(os.path.join(d,f'f{i:05d}.png')).convert('RGB').resize((W,H),Image.LANCZOS)
                fx(im,k+i).save(p)
        k+=n
    if not os.path.exists(o):
        subprocess.run(['ffmpeg','-v','error','-y','-framerate',str(sh['fps']),'-i',os.path.join(src,'f%05d.png'),
            '-vf',f'scale={W}:{H}:flags=lanczos,fps=24,format=yuv420p','-frames:v',str(n),
            '-c:v','libx264','-crf','17','-preset','medium','-r','24',o],check=True)
    parts.append(o)
lst=os.path.join(work,'목록.txt'); open(lst,'w').write(''.join(f"file '{os.path.abspath(p)}'\n" for p in parts))
total=shots[-1]['t1']
subprocess.run(['ffmpeg','-v','error','-y','-f','concat','-safe','0','-i',lst,'-i',audio,
  '-vf',f'fade=t=in:st=0:d=0.5,fade=t=out:st={total-1.6:.2f}:d=1.6','-map','0:v','-map','1:a',
  '-c:v','libx264','-crf','18','-preset','medium','-r','24','-pix_fmt','yuv420p',
  '-c:a','aac','-b:a','192k','-t',f'{total:.2f}','-movflags','+faststart',out],check=True)
print('OK',out)
