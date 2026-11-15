"""시간표 → jobs.txt(60장 묶음) · ../샷목록.json"""
import json, os, glob
H=os.path.dirname(os.path.abspath(__file__))
d=json.load(open(glob.glob(os.path.join(H,'..','*_시간.json'))[0],encoding='utf-8')); s=d['segs']
idx=[i for i,x in enumerate(s) if x['kind']=='chapter']
jobs=[]; shots=[]
for ch,a in enumerate(idx):
    t0=0.0 if ch==0 else s[a]['t0']; t1=s[idx[ch+1]]['t0'] if ch+1<len(idx) else d['duration']
    nf=int(round((t1-t0)*24))+1
    shots.append({'name':'ch%d'%ch,'t0':t0,'t1':t1,'fps':24})
    for f0 in range(1,nf+1,60): jobs.append('ch%d %d %d'%(ch,f0,min(nf,f0+59)))
open(os.path.join(H,'jobs.txt'),'w').write('\n'.join(jobs)+'\n')
json.dump({'shots':shots},open(os.path.join(H,'..','샷목록.json'),'w'),ensure_ascii=False,indent=1)
print(len(jobs),'묶음',round(d['duration'],1),'초',[round(x['t1']-x['t0'],1) for x in shots])
