"""촬영한 프레임에서 '지글거림(깜빡임)'을 찾음 — 면 겹침(z-fighting) 때문에 한 장 걸러 색이 바뀌는 점.
   연달은 세 장 f0·f1·f2 에서  f0 ≈ f2  인데  f1 만 크게 다른 점(가→나→가)을 셈. 카메라가 천천히 움직여도
   부드러운 움직임은 f1 이 f0·f2 사이에 오므로 잘 걸리지 않음.
   사용: python 지글검사.py <프레임폴더(샷 폴더들)> [샷이름,...] [--결과 <폴더>]   (12장 묶음마다 같은 점이 3번 넘게 깜빡이면 걸림)
   → 샷마다 지글 점이 많은 시간을 적고, 걸린 곳은 빨갛게 칠한 확인 그림(<결과>/<샷>_지글.jpg)을 저장"""
import sys, os, glob
import numpy as np
from PIL import Image
args=[a for a in sys.argv[1:]]
step=12; out=None
if '--간격' in args: i=args.index('--간격'); step=int(args[i+1]); del args[i:i+2]
if '--결과' in args: i=args.index('--결과'); out=args[i+1]; del args[i:i+2]
root=args[0]; only=set(args[1].split(',')) if len(args)>1 else None
out=out or os.path.join(os.path.dirname(os.path.abspath(root)),'_지글검사'); os.makedirs(out,exist_ok=True)
W=360   # 작게 줄여 비교 (빠르게, 작은 흔들림은 무시)
def load(p):
    im=Image.open(p).convert('RGB'); h=int(im.height*W/im.width)
    return np.asarray(im.resize((W,h),Image.BILINEAR)).astype(np.int16)
TH_FLIP=40; TH_SAME=14; MIN_PTS=12       # 색 차이 기준 (0~255), 걸렸다고 볼 최소 점 수
report=[]
for d in sorted(glob.glob(os.path.join(root,'*/'))):
    sh=os.path.basename(os.path.dirname(d))
    if only and sh not in only: continue
    fs=sorted(glob.glob(d+'f*.png'))
    if len(fs)<3: continue
    worst=(0,None,None)
    hits=[]
    # 같은 점이 짧은 구간(win 장) 안에서 3번 넘게 가→나→가 로 바뀌면 지글거림 (움직이는 팔·떨어지는 잎은 한 번 지나가고 끝남)
    win=12
    for w in range(0,len(fs)-2,win):
        cnt=None; fr=[load(f) for f in fs[w:w+win]]
        for k in range(len(fr)-2):
            a,b,c=fr[k],fr[k+1],fr[k+2]
            m=(np.abs(a-b).max(2)>TH_FLIP)&(np.abs(b-c).max(2)>TH_FLIP)&(np.abs(a-c).max(2)<TH_SAME)
            cnt=m.astype(np.int16) if cnt is None else cnt+m
        if cnt is None: continue
        m=cnt>=3; n=int(m.sum())
        if n>=MIN_PTS: hits.append((w,n))
        if n>worst[0]: worst=(n,w,m)
    if hits:
        n,k,m=worst
        im=Image.open(fs[k+1]).convert('RGB'); h=int(im.height*W/im.width); im=np.asarray(im.resize((W,h))).copy()
        im[m]=[255,0,0]; Image.fromarray(im).save(os.path.join(out,f'{sh}_지글.jpg'),quality=90)
        report.append(f'{sh}: 지글 {len(hits)}곳 (가장 심한 곳 {k+1}번째 장, 점 {n}개) → {sh}_지글.jpg')
    else:
        report.append(f'{sh}: 없음')
txt='\n'.join(report); print(txt)
open(os.path.join(out,'_지글검사.txt'),'w',encoding='utf-8').write(txt+'\n')
