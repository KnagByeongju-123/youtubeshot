import sys,glob,os
from PIL import Image
fs=sorted(glob.glob(os.path.join(sys.argv[1],'*.png'))); W=640
ims=[Image.open(f).convert('RGB').resize((W,360)) for f in fs]
cols=2; rows=(len(ims)+1)//2
m=Image.new('RGB',(W*cols,360*rows),'black')
for i,im in enumerate(ims): m.paste(im,((i%cols)*W,(i//cols)*360))
m.save(sys.argv[2]); print(len(ims))
