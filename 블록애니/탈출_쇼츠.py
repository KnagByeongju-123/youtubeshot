"""《13층 아래》 쇼츠(세로) 준비: 긴 영상의 샷 목록에서 구간을 골라 쇼츠용 샷 목록·글자·소리 시간표를 만듦
사용: python 탈출_쇼츠.py   → 연재/13층아래/쇼츠/<이름>_샷.json · _글자.json · _시간표.json
그다음: VERT=1 node blockbench_샷촬영.js <이름>_샷.json 장면 <프레임> all → 탈출_소리.py … --추격만 → 탈출_조립.py … --크기 1080x1920"""
import json, os
ROOT='/home/user/youtubeshot/연재/13층아래'; OUT=f'{ROOT}/쇼츠'; os.makedirs(OUT,exist_ok=True)
SH=json.load(open(f'{ROOT}/장면/샷목록.json',encoding='utf-8'))['shots']; TT=json.load(open(f'{ROOT}/시간표.json',encoding='utf-8'))
sm=lambda x:x*x*(3-2*x)
def at(cam,u):
    k=0
    while k<len(cam)-2 and u>cam[k+1]['u']: k+=1
    c0,c1=cam[k],cam[min(k+1,len(cam)-1)]; f=sm(min(1,max(0,(u-c0['u'])/(c1['u']-c0['u'])))) if c1['u']>c0['u'] else 0
    L=lambda a,b:[x+(y-x)*f for x,y in zip(a,b)]; d={'pos':L(c0['pos'],c1['pos']),'tgt':L(c0['tgt'],c1['tgt'])}
    for key,dv in (('fov',38),('roll',0),('shake',1)):
        if key in c0 or key in c1: d[key]=c0.get(key,dv)+(c1.get(key,dv)-c0.get(key,dv))*f
    return d
FLOOR=[(0,65,'B13'),(65,100,'B12 → B10'),(100,135,'B10'),(135,170,'B9'),(170,205,'B7'),(205,240,'B6 → B3'),(240,280,'B3'),(280,315,'B1'),(315,999,'지상')]
PARTS=[88.0,121.5,163.0,192.5,228.0,268.0,305.5]            # 부품을 잃는 때 → HUD 의 ■ 가 하나씩 줄어듦
def make(name,ranges,hook,end):
    shots=[]; caps=[]; cues=[]; t=0.0
    for a,b in ranges:
        for s in SH:
            x0,x1=max(a,s['t0']),min(b,s['t1'])
            if x1-x0<0.2: continue
            d=dict(s); u0=(x0-s['t0'])/(s['t1']-s['t0']); u1=(x1-s['t0'])/(s['t1']-s['t0']); n=7
            d['cam']=[dict(at(s['cam'],u0+(u1-u0)*i/(n-1)),u=i/(n-1)) for i in range(n)]
            d['name']=f"{len(shots):02d}_{s['name'].split('_',1)[1]}"; d['t0']=round(x0,3); d['t1']=round(x1,3); d['fps']=24; shots.append(d)
            # HUD: 층 + 남은 부품
            fl=[f for f in FLOOR if f[0]<=x0<f[1]][0][2]; marks=sorted([p for p in PARTS if x0<p<x1]+[x0,x1])
            for m0,m1 in zip(marks,marks[1:]):
                if x0>=315: break          # 지상(다시 맞춘 뒤)에는 부품 표시를 안 띄움
                left=7-sum(1 for p in PARTS if p<=m0); caps.append({'t0':t+m0-x0,'t1':t+m1-x0,'text':f"{fl}   부품 {'■'*left}{'□'*(7-left)}",'style':'Hud'})
            for c in TT['cues']:
                if x0<=c['t']<x1: cues.append({'t':round(t+c['t']-x0,2),'kind':c['kind'],'vol':c.get('vol',1)})
            t+=x1-x0
    for c in caps: c['text']=c['text']; 
    caps=[dict(c,text=c['text']) for c in caps]
    caps+= [{'t0':0.2,'t1':3.4,'text':hook,'style':'Hook'},{'t0':t-3.2,'t1':t-0.1,'text':end,'style':'End'}]
    json.dump({'shots':shots},open(f'{OUT}/{name}_샷.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
    json.dump(caps,open(f'{OUT}/{name}_글자.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
    json.dump({'duration':round(t,2),'cues':cues},open(f'{OUT}/{name}_시간표.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
    print(name,len(shots),'샷',round(t,1),'초',sum(round((s['t1']-s['t0'])*24) for s in shots),'장')
if __name__=='__main__':
    make('쇼츠1_레이저',[(100,132.6)],'레이저 복도를\\N통과하라','13층 아래\\N본편은 채널에서')
    make('쇼츠2_탈출',[(43.5,49),(84,91),(111.2,121.4),(153.6,163.2),(221,230),(300,306),(401.6,411.4)],'청소 로봇의\\N13층 탈출','13층 아래\\N본편은 채널에서')
