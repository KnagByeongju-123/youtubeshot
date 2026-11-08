"""<이름>_v0..3.png 를 잘라 앞·옆·옆·뒤 한 장으로.  사용: python 시트_합치기.py <폴더>"""
import sys,glob,os
from PIL import Image,ImageDraw,ImageFont,ImageChops
d=sys.argv[1]
F=ImageFont.truetype(glob.glob('/usr/share/fonts/**/NanumGothicBold.ttf',recursive=True)[0],34)
for v0 in sorted(glob.glob(f'{d}/*_v0.png')):
    name=os.path.basename(v0)[:-7]; ims=[]
    for i in range(4):
        im=Image.open(f'{d}/{name}_v{i}.png').convert('RGB')
        bb=ImageChops.difference(im,Image.new('RGB',im.size,(255,255,255))).point(lambda v:255 if v>12 else 0).getbbox()
        ims.append(im.crop(bb) if bb else im)
    h=max(i.height for i in ims); pad=50
    ims=[i.resize((int(i.width*h/i.height*1.0),h)) if False else i for i in ims]
    W=sum(i.width for i in ims)+pad*5; Hh=h+pad*2+60
    o=Image.new('RGB',(W,Hh),'white'); dr=ImageDraw.Draw(o); x=pad
    for lab,i in zip(['앞','옆','옆','뒤'],ims):
        o.paste(i,(x,pad+(h-i.height))); dr.text((x+i.width//2-17,h+pad+10),lab,fill=(60,60,60),font=F); x+=i.width+pad
    dr.text((pad,10),name,fill=(30,30,30),font=F)
    o.save(f'{d}/{name}_시트.png'); print(name,o.size)
