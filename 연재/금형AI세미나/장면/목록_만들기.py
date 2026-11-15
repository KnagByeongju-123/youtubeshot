"""시간표(_시간.json) → jobs.txt(촬영 묶음) · ../샷목록.json · ../숫자.json(화면 설명 상자, 문장 글자로 찾음)"""
import json, os
H=os.path.dirname(os.path.abspath(__file__))
d=json.load(open(os.path.join(H,'..','금형AI세미나_시간.json'),encoding='utf-8')); s=d['segs']
idx=[i for i,x in enumerate(s) if x['kind']=='chapter']
jobs=[]; shots=[]
for ch,a in enumerate(idx):
    t0=0.0 if ch==0 else s[a]['t0']; t1=s[idx[ch+1]]['t0'] if ch+1<len(idx) else d['duration']
    nf=int(round((t1-t0)*24))+1
    shots.append({'name':'ch%d'%ch,'t0':t0,'t1':t1,'fps':24})
    for f0 in range(1,nf+1,400): jobs.append('ch%d %d %d'%(ch,f0,min(nf,f0+399)))
open(os.path.join(H,'jobs.txt'),'w').write('\n'.join(jobs)+'\n')
json.dump({'shots':shots},open(os.path.join(H,'..','샷목록.json'),'w'),ensure_ascii=False,indent=1)
def find(word): return next(i for i,x in enumerate(s) if word in x['text'])
nums=[{'seg':find('부품이 백한 개'),'text':'부품 101개 · 서로 겹침 0','extra':0.5},
      {'seg':find('작은 부품 하나부터'),'text':'금형 안 · 리스트라이크 스테이션','extra':0.2}]
json.dump(nums,open(os.path.join(H,'..','숫자.json'),'w'),ensure_ascii=False,indent=1)
print(len(jobs),'묶음',round(d['duration'],1),'초',[round(x['t1']-x['t0'],1) for x in shots],nums)
