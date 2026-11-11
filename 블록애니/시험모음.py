"""시험 사진(샷마다 4장)을 한 장으로 모음.  사용: python 시험모음.py <test폴더> <결과.jpg> [샷이름,...]"""
import sys,os,glob
from PIL import Image,ImageDraw,ImageFont
d,out=sys.argv[1:3]; want=sys.argv[3].split(',') if len(sys.argv)>3 else None
F=ImageFont.truetype(glob.glob('/usr/share/fonts/**/NanumGothicBold.ttf',recursive=True)[0],22)
shots=[s for s in sorted(os.listdir(d)) if os.path.isdir(os.path.join(d,s)) and (not want or s in want)]
fs0=sorted(glob.glob(os.path.join(d,shots[0],'f*.png'))); w0,h0=Image.open(fs0[0]).size
W=360 if h0>w0 else 480; H=int(W*h0/w0)
o=Image.new('RGB',(W*4,(H+30)*len(shots)),'white'); dr=ImageDraw.Draw(o)
for r,sh in enumerate(shots):
    for c,f in enumerate(sorted(glob.glob(os.path.join(d,sh,'f*.png')))[:4]):
        o.paste(Image.open(f).convert('RGB').resize((W,H)),(c*W,r*(H+30)+30))
    dr.text((5,r*(H+30)+3),sh,fill='black',font=F)
o.save(out,quality=85); print(out,o.size)
