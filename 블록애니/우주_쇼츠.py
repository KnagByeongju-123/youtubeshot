"""《마지막 방어선》 쇼츠(세로) 준비: 긴 영상 샷 목록에서 구간을 골라 쇼츠용 샷 목록·글자·소리 시간표를 만듦
사용: python 우주_쇼츠.py → 연재/지구방위선/쇼츠/<이름>_샷.json·_글자.json·_시간표.json
그다음: VERT=1 node blockbench_샷촬영.js … → 우주_소리.py … --전투만 → 탈출_조립.py … --크기 1080x1920"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 탈출_쇼츠 import at
ROOT='/home/user/youtubeshot/연재/지구방위선'; OUT=f'{ROOT}/쇼츠'; os.makedirs(OUT,exist_ok=True)
SH=json.load(open(f'{ROOT}/장면/샷목록.json',encoding='utf-8'))['shots']; TT=json.load(open(f'{ROOT}/시간표.json',encoding='utf-8'))
def make(name,ranges,hook,end):
    shots=[]; cues=[]; t=0.0
    for a,b in ranges:
        for s in SH:
            x0,x1=max(a,s['t0']),min(b,s['t1'])
            if x1-x0<0.2: continue
            d=dict(s); u0=(x0-s['t0'])/(s['t1']-s['t0']); u1=(x1-s['t0'])/(s['t1']-s['t0']); n=7
            d['cam']=[dict(at(s['cam'],u0+(u1-u0)*i/(n-1)),u=i/(n-1)) for i in range(n)]
            d['name']=f"{len(shots):02d}_{s['name'].split('_',1)[1]}"; d['t0']=round(x0,3); d['t1']=round(x1,3); d['fps']=24; shots.append(d)
            for c in TT['cues']:
                if x0<=c['t']<x1: cues.append({'t':round(t+c['t']-x0,2),'kind':c['kind'],'vol':c.get('vol',1)})
            t+=x1-x0
    caps=[{'t0':0.2,'t1':3.4,'text':hook,'style':'Hook'},{'t0':t-3.2,'t1':t-0.1,'text':end,'style':'End'}]
    json.dump({'shots':shots},open(f'{OUT}/{name}_샷.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
    json.dump(caps,open(f'{OUT}/{name}_글자.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
    json.dump({'duration':round(t,2),'cues':cues},open(f'{OUT}/{name}_시간표.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
    print(name,len(shots),'샷',round(t,1),'초',sum(round((s['t1']-s['t0'])*24) for s in shots),'장')
if __name__=='__main__':
    make('쇼츠1_돌입',[(197,232)],'모함의 핵을\\N파괴하라','마지막 방어선\\N본편은 채널에서')
    make('쇼츠2_전투',[(92,99),(108,116),(159.6,166),(186,193),(229.4,232),(237,246)],'지구 방위대\\N최후의 전투','마지막 방어선\\N본편은 채널에서')
